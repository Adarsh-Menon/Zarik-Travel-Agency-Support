import json
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agent.state import AgentState, TravelPreferences
from agent.prompts import (
    SYSTEM_PROMPT, GREETING_PROMPT, COLLECTION_PROMPT,
    FOLLOWUP_PROMPT, EXTRACTION_PROMPT,
)
from memory.store import load_memory, save_memory, update_memory_from_trip
from leads.excel_manager import add_lead, update_lead, find_lead_by_telegram_id
from tools.itinerary_gen import generate_itinerary, modify_itinerary
from config import GROQ_API_KEY, GROQ_MODEL

llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.6,
    max_tokens=2048,
)

REQUIRED_FIELDS = ["destination", "travel_dates", "duration_days", "budget", "group_size", "interests"]


def _get_collected_and_missing(prefs: dict) -> tuple[dict, list]:
    collected = {k: v for k, v in prefs.items() if v and v != 0 and v != []}
    missing = [f for f in REQUIRED_FIELDS if f not in collected]
    return collected, missing


def _extract_preferences(message: str, existing: dict) -> dict:
    """Use LLM to extract structured preferences from free-text message."""
    import logging
    import re
    logger = logging.getLogger("zarik.extract")

    try:
        response = llm.invoke([
            SystemMessage(content=(
                "You are a JSON extraction bot. Extract travel preferences from the user message. "
                "Return ONLY a raw JSON object. No markdown, no backticks, no explanation. "
                "Example output: {\"destination\": \"Japan\", \"budget\": \"Rs 50000\", \"group_size\": 2}"
            )),
            HumanMessage(content=EXTRACTION_PROMPT.format(message=message)),
        ])

        raw = response.content.strip()
        logger.info(f"Raw extraction: {raw}")

        # Strip markdown code fences aggressively
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        raw = raw.strip()

        # Find JSON object in response (Llama sometimes adds text around it)
        json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(0)

        extracted = json.loads(raw)
        logger.info(f"Extracted fields: {extracted}")

        merged = {**existing}
        for k, v in extracted.items():
            if v is not None and v != "" and v != [] and v != 0:
                merged[k] = v

        logger.info(f"Merged preferences: {merged}")
        return merged

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed: {e} | Raw: {raw[:200]}")
        return existing
    except Exception as e:
        logger.warning(f"Extraction error: {e}")
        return existing


# ── Node Functions ──────────────────────────────────────────


def greet_node(state: AgentState) -> dict:
    """Welcome the user. Check memory for returning users."""
    memory = load_memory(state["telegram_id"])
    is_returning = len(memory.get("past_itineraries", [])) > 0

    prompt = GREETING_PROMPT.format(memory=json.dumps(memory, indent=2) if is_returning else "New user")

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT.format(phase="greeting")),
        HumanMessage(content=prompt),
    ])

    if state.get("user_name") and memory.get("name") != state["user_name"]:
        memory["name"] = state["user_name"]
        save_memory(state["telegram_id"], memory)

    return {
        "messages": [AIMessage(content=response.content)],
        "phase": "collect",
        "memory_loaded": True,
        "user_memory": memory,
        "collection_step": 0,
    }


def collect_node(state: AgentState) -> dict:
    """Collect travel preferences through conversation."""
    import logging
    logger = logging.getLogger("zarik.collect")

    last_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break

    # Extract preferences from latest message
    current_prefs = dict(state.get("preferences", {}))
    updated_prefs = _extract_preferences(last_msg, current_prefs)
    collected, missing = _get_collected_and_missing(updated_prefs)

    logger.info(f"Collected: {list(collected.keys())} | Missing: {missing} | Step: {state['collection_step']}")

    if not missing:
        # All preferences collected — move to generation
        return {
            "preferences": updated_prefs,
            "phase": "generate",
            "collection_step": state["collection_step"] + 1,
        }

    # Safety valve: if stuck for 8+ steps, generate with what we have
    if state["collection_step"] >= 8 and collected:
        logger.warning(f"Collection stuck at step {state['collection_step']}, proceeding with partial: {collected}")
        # Fill missing with defaults
        defaults = {
            "destination": "Not specified",
            "travel_dates": "Flexible",
            "duration_days": 5,
            "budget": "Mid-range",
            "group_size": 2,
            "interests": ["general sightseeing"],
        }
        for field in missing:
            updated_prefs.setdefault(field, defaults.get(field, ""))
        return {
            "preferences": updated_prefs,
            "phase": "generate",
            "collection_step": state["collection_step"] + 1,
        }

    # Ask for next missing field — include what user actually said
    prompt = COLLECTION_PROMPT.format(
        user_message=last_msg,
        collected=json.dumps(collected, indent=2) if collected else "Nothing yet",
        missing=", ".join(missing),
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT.format(phase="collecting preferences")),
        *state["messages"][-6:],  # last 3 turns for context
        HumanMessage(content=prompt),
    ])

    return {
        "messages": [AIMessage(content=response.content)],
        "preferences": updated_prefs,
        "collection_step": state["collection_step"] + 1,
    }


def generate_node(state: AgentState) -> dict:
    """Generate the itinerary and capture the lead."""
    prefs = dict(state["preferences"])
    itinerary = generate_itinerary(prefs)

    # Capture lead in Excel
    interests_str = ", ".join(prefs.get("interests", []))
    summary = f"{prefs.get('duration_days', '?')}d {prefs.get('destination', '?')} - {interests_str}"

    existing_lead = find_lead_by_telegram_id(state["telegram_id"])
    if existing_lead:
        lead_id = existing_lead["lead_id"]
        update_lead(
            lead_id,
            destination=prefs.get("destination", ""),
            travel_dates=prefs.get("travel_dates", ""),
            budget=str(prefs.get("budget", "")),
            group_size=prefs.get("group_size", 0),
            interests=interests_str,
            itinerary_summary=summary,
            status="Contacted",
        )
    else:
        lead_id = add_lead(
            name=state.get("user_name", "Unknown"),
            telegram_handle=state.get("telegram_handle", ""),
            telegram_id=state["telegram_id"],
            destination=prefs.get("destination", ""),
            travel_dates=prefs.get("travel_dates", ""),
            budget=str(prefs.get("budget", "")),
            group_size=prefs.get("group_size", 0),
            interests=interests_str,
            itinerary_summary=summary,
        )

    # Update user memory
    update_memory_from_trip(state["telegram_id"], prefs, summary)

    return {
        "messages": [AIMessage(content=itinerary)],
        "itinerary": itinerary,
        "lead_id": lead_id,
        "phase": "followup",
    }


def followup_node(state: AgentState) -> dict:
    """Handle post-itinerary conversation."""
    last_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_msg = m.content
            break

    # Check if user wants modifications
    modification_keywords = ["change", "modify", "adjust", "more", "less", "add", "remove", "swap", "replace", "different"]
    wants_modification = any(kw in last_msg.lower() for kw in modification_keywords)

    if wants_modification:
        modified = modify_itinerary(state["itinerary"], last_msg, dict(state["preferences"]))
        if state.get("lead_id"):
            update_lead(state["lead_id"], notes=f"Modified: {last_msg[:100]}")
        return {
            "messages": [AIMessage(content=modified)],
            "itinerary": modified,
        }

    # General followup
    prompt = FOLLOWUP_PROMPT.format(
        itinerary_summary=state.get("itinerary", "")[:500],
    )
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT.format(phase="followup")),
        *state["messages"][-4:],
        HumanMessage(content=prompt),
    ])

    return {
        "messages": [AIMessage(content=response.content)],
    }


# ── Router ──────────────────────────────────────────────────


def route_phase(state: AgentState) -> str:
    phase = state.get("phase", "greet")
    if phase == "greet":
        return "greet"
    elif phase == "collect":
        return "collect"
    elif phase == "generate":
        return "generate"
    elif phase in ("followup", "modify"):
        return "followup"
    return "greet"


# ── Build Graph ─────────────────────────────────────────────


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("greet", greet_node)
    graph.add_node("collect", collect_node)
    graph.add_node("generate", generate_node)
    graph.add_node("followup", followup_node)

    # Entry point routes based on phase
    graph.set_conditional_entry_point(route_phase, {
        "greet": "greet",
        "collect": "collect",
        "generate": "generate",
        "followup": "followup",
    })

    # Greet always goes to END (response sent, next message goes to collect)
    graph.add_edge("greet", END)

    # Collect either loops or goes to generate
    graph.add_conditional_edges(
        "collect",
        lambda s: "generate" if s["phase"] == "generate" else END,
        {"generate": "generate", END: END},
    )

    # Generate goes to END (response sent, next message goes to followup)
    graph.add_edge("generate", END)

    # Followup always goes to END
    graph.add_edge("followup", END)

    return graph.compile()


# Compiled graph instance
zarik_graph = build_graph()
