# ZARIK — AI Itinerary Assistant for Travel Agencies

## System Overview

Zarik is an AI-powered travel itinerary assistant that operates via Telegram, captures user travel preferences through conversational flow, generates detailed itineraries using LLM intelligence, and manages leads in Excel — all orchestrated by a LangGraph stateful agent.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      TELEGRAM CLIENT                        │
│  User ↔ Bot (python-telegram-bot)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Webhook / Polling
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI GATEWAY                           │
│  /webhook    — Telegram webhook receiver                    │
│  /api/leads  — Lead CRUD (for admin dashboard)              │
│  /api/itinerary — Manual itinerary generation               │
│  /health     — Health check                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               LANGGRAPH AGENT (State Machine)               │
│                                                             │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐ │
│  │ GREET   │→ │ COLLECT  │→ │ GENERATE   │→ │ FOLLOWUP  │ │
│  │         │  │ PREFS    │  │ ITINERARY  │  │ & CLOSE   │ │
│  └─────────┘  └──────────┘  └────────────┘  └───────────┘ │
│       │            │              │               │         │
│       └────────────┴──────────────┴───────────────┘         │
│                        │                                    │
│              ┌─────────┴──────────┐                         │
│              │   TOOL NODES       │                         │
│              │ • itinerary_gen    │                         │
│              │ • lead_manager     │                         │
│              │ • memory_store     │                         │
│              │ • price_estimator  │                         │
│              └────────────────────┘                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌────────────┐ ┌─────────┐ ┌──────────┐
   │ LLM (Claude│ │ EXCEL   │ │ MEMORY   │
   │ / OpenAI)  │ │ LEADS   │ │ STORE    │
   │            │ │ (.xlsx) │ │ (JSON)   │
   └────────────┘ └─────────┘ └──────────┘
```

---

## Core Modules

### 1. Telegram Bot Layer (`bot/`)
- Receives messages via webhook or polling
- Routes to FastAPI, which invokes the LangGraph agent
- Sends formatted itineraries, confirmations, follow-ups
- Handles /start, /mytrips, /help commands

### 2. FastAPI Gateway (`api/`)
- Webhook endpoint for Telegram
- REST endpoints for lead management (admin use)
- Serves as the HTTP backbone

### 3. LangGraph Agent (`agent/`)
The brain — a stateful graph with these nodes:

| Node | Purpose |
|------|---------|
| `greet` | Welcome message, detect returning user via memory |
| `collect_preferences` | Multi-turn conversation to capture: destination, dates, budget, group size, interests, dietary needs |
| `generate_itinerary` | LLM call to produce day-by-day itinerary |
| `capture_lead` | Save/update lead in Excel with all collected data |
| `followup` | Ask for feedback, offer modifications, upsell |
| `modify_itinerary` | Re-generate based on user feedback |

### 4. Lead Manager (`leads/`)
- Reads/writes Excel (.xlsx) using openpyxl
- Columns: Lead ID, Name, Telegram Handle, Phone, Destination, Dates, Budget, Group Size, Interests, Status, Itinerary Summary, Created At, Last Updated, Agent Notes
- AI agent can query, filter, update status (New → Contacted → Converted → Lost)
- Auto-generates lead ID, timestamps

### 5. Memory Store (`memory/`)
- Per-user JSON files (like ClawdBot pattern)
- Stores: user profile, past trips, preferences, conversation history summary
- Loaded at conversation start, updated at end
- Enables personalization ("Welcome back! Last time you loved Bali...")

### 6. Itinerary Generator (`tools/`)
- LLM-powered with structured output
- Generates: day-by-day plan, activities, estimated costs, tips
- Supports modification ("make it more adventurous", "add beach day")

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangGraph + LangChain |
| API | FastAPI |
| Client | Telegram (python-telegram-bot) |
| LLM | Groq API — Llama 3.3 70B (via langchain-groq) |
| Lead Storage | Excel (.xlsx) via openpyxl |
| Memory | JSON file store (per-user) |
| Language | Python 3.11+ |

---

## Project Structure

```
zarik/
├── main.py                    # Entry point — starts FastAPI + Telegram
├── config.py                  # Environment variables, settings
├── requirements.txt
│
├── api/
│   ├── __init__.py
│   ├── routes.py              # FastAPI routes (webhook, leads API)
│   └── schemas.py             # Pydantic models
│
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py        # Telegram bot setup, handlers
│   └── formatters.py          # Format itineraries for Telegram
│
├── agent/
│   ├── __init__.py
│   ├── graph.py               # LangGraph state machine definition
│   ├── state.py               # AgentState TypedDict
│   ├── nodes.py               # Node functions (greet, collect, generate, etc.)
│   └── prompts.py             # System prompts for each node
│
├── leads/
│   ├── __init__.py
│   └── excel_manager.py       # Excel CRUD operations
│
├── memory/
│   ├── __init__.py
│   └── store.py               # Per-user memory read/write
│
├── tools/
│   ├── __init__.py
│   ├── itinerary_gen.py       # Itinerary generation tool
│   └── price_estimator.py     # Basic price estimation
│
├── data/
│   ├── leads.xlsx             # Lead tracking spreadsheet
│   └── memory/                # Per-user memory JSONs
│       └── {telegram_id}.json
│
└── .env                       # API keys, bot token
```

---

## Conversation Flow

```
User: /start
Bot: "👋 Welcome to Zarik! I'm your AI travel assistant.
      Where would you love to travel?"

User: "I want to visit Japan"
Bot: "🇯🇵 Great choice! When are you planning to go?
      And how many days are you thinking?"

User: "October, about 7 days"
Bot: "Perfect! A few more questions:
      💰 What's your approximate budget per person?
      👥 How many travelers?
      🎯 What interests you most — culture, food, adventure, relaxation?"

User: "Budget $2000, 2 people, we love food and culture"
Bot: "Got it! Let me craft your perfect Japan itinerary..."

Bot: [Generates and sends detailed 7-day itinerary]
     "Want me to adjust anything? More food spots?
      Different pace? Just tell me!"

User: "Add more street food experiences"
Bot: [Modifies and resends updated itinerary]
```

---

## Lead Excel Structure

| Column | Type | Description |
|--------|------|-------------|
| lead_id | str | Auto UUID (ZRK-001, ZRK-002...) |
| name | str | User's name (from Telegram) |
| telegram_handle | str | @username |
| telegram_id | int | Numeric Telegram ID |
| phone | str | If provided |
| destination | str | Target destination |
| travel_dates | str | Preferred dates |
| budget | str | Budget range |
| group_size | int | Number of travelers |
| interests | str | Comma-separated interests |
| status | str | New / Contacted / Converted / Lost |
| itinerary_summary | str | Brief itinerary description |
| created_at | datetime | First interaction |
| last_updated | datetime | Last modification |
| notes | str | Agent/admin notes |

---

## Memory Structure (per user)

```json
{
  "telegram_id": 123456789,
  "name": "Adarsh",
  "first_seen": "2026-05-01",
  "last_seen": "2026-05-01",
  "preferences": {
    "preferred_destinations": ["Japan", "Bali"],
    "travel_style": "adventure + culture",
    "budget_range": "mid-range",
    "dietary": "none",
    "group_size_typical": 2
  },
  "past_itineraries": [
    {
      "destination": "Japan",
      "dates": "Oct 2026",
      "days": 7,
      "generated_at": "2026-05-01"
    }
  ],
  "conversation_summary": "Loves Japanese street food, prefers cultural experiences..."
}
```

---

## Environment Variables (.env)

```
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
TELEGRAM_BOT_TOKEN=123456:ABC...
LEADS_EXCEL_PATH=data/leads.xlsx
MEMORY_DIR=data/memory
LOG_LEVEL=INFO
```
