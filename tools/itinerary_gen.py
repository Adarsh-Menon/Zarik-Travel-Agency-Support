import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from agent.prompts import ITINERARY_PROMPT, MODIFICATION_PROMPT

_llm = None

def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.7,
            max_tokens=4096,
        )
    return _llm


def generate_itinerary(preferences: dict) -> str:
    prompt = ITINERARY_PROMPT.format(
        destination=preferences.get("destination", "Not specified"),
        travel_dates=preferences.get("travel_dates", "Flexible"),
        duration_days=preferences.get("duration_days", 5),
        budget=preferences.get("budget", "Mid-range"),
        group_size=preferences.get("group_size", 2),
        interests=", ".join(preferences.get("interests", ["general sightseeing"])),
        dietary=preferences.get("dietary", "None"),
        special_requests=preferences.get("special_requests", "None"),
    )

    response = _get_llm().invoke([
        SystemMessage(content="You are a world-class travel planner. Create detailed, practical itineraries."),
        HumanMessage(content=prompt),
    ])
    return response.content


def modify_itinerary(current_itinerary: str, modification: str, preferences: dict) -> str:
    prompt = MODIFICATION_PROMPT.format(
        current_itinerary=current_itinerary,
        modification=modification,
        preferences=str(preferences),
    )

    response = _get_llm().invoke([
        SystemMessage(content="You are a world-class travel planner. Modify itineraries based on feedback."),
        HumanMessage(content=prompt),
    ])
    return response.content
