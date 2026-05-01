# 🌍 Zarik — AI Travel Itinerary Assistant

> An AI-powered Telegram bot that captures travel preferences through natural conversation, generates personalized day-by-day itineraries, remembers returning users, and manages leads in Excel — all orchestrated by a LangGraph stateful agent.

![Zarik Demo](resources/Zarik.gif)

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_Agent-purple)
![Groq](https://img.shields.io/badge/LLM-Groq_Llama_3.3-orange?logo=meta)
![Telegram](https://img.shields.io/badge/Client-Telegram_Bot-26A5E4?logo=telegram&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is Zarik?

Zarik is a complete travel agency assistant that lives inside Telegram. A user starts a conversation, tells the bot where they want to go, and Zarik handles the rest — asking the right questions naturally, generating a full itinerary with costs and tips, and capturing the lead automatically in a formatted Excel sheet.

Built for travel agencies that want to automate the initial customer interaction without losing the personal touch.

### Demo Conversation

```
User: /start
Zarik: 👋 Welcome to Zarik! I'm your AI travel assistant.
       Where would you love to travel?

User: Japan, 7 days, budget around Rs 50000, me and my wife
Zarik: 🇯🇵 Japan for 7 days with your wife — great choice!
       What interests you most — food, culture, adventure, nature?

User: Street food and temples
Zarik: Perfect! Let me craft your itinerary...

Zarik: 📅 Day 1: Tokyo Arrival
       🌅 Morning: Tsukiji Outer Market — fresh sushi breakfast
       ☀️ Afternoon: Senso-ji Temple, Asakusa
       🌙 Evening: Shibuya street food crawl
       💰 Est. Cost: ₹6,500
       ...

User: Add more ramen spots
Zarik: ✨ Updated! Added ramen experiences on Day 2 and Day 5...
```

---

## Architecture

```
Telegram → FastAPI Gateway → LangGraph Agent → Groq LLM (Llama 3.3 70B)
                                    │
                          ┌─────────┼─────────┐
                          ▼         ▼         ▼
                     Excel Leads  Memory   Itinerary
                     (.xlsx)      (JSON)   Generator
```

The LangGraph agent runs a 4-node state machine:

| Node | What it does |
|------|-------------|
| **Greet** | Welcomes user, checks memory for returning visitors |
| **Collect** | Multi-turn conversation to extract preferences (destination, dates, budget, group size, interests) |
| **Generate** | Produces day-by-day itinerary via Groq, captures lead in Excel |
| **Followup** | Handles modifications, feedback, and new trip requests |

---

## Features

- **Natural conversation flow** — not a form, not a survey. Zarik extracts preferences from free-text messages and asks follow-up questions naturally
- **Multi-currency support** — understands Rs, ₹, INR, AED, $, €, and shorthand like "50k" or "2 lakh"
- **Per-user memory** — remembers returning users, their past trips, preferences, and travel style (JSON file store, ClawdBot pattern)
- **Auto lead capture** — every interaction creates/updates a formatted Excel lead with status tracking (New → Contacted → Converted → Lost)
- **Itinerary modification** — users can request changes ("add more food spots", "make it more adventurous") and get updated itineraries
- **Safety valve** — if preference collection gets stuck, auto-fills defaults and generates after 8 steps
- **REST API** — FastAPI endpoints for lead management (`GET /api/leads`, `PATCH /api/leads/{id}`)
- **Groq-powered** — uses Llama 3.3 70B via Groq for fast inference (~1-2s responses)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | LangGraph + LangChain |
| LLM | Groq API — Llama 3.3 70B Versatile |
| API | FastAPI + Uvicorn |
| Client | Telegram (python-telegram-bot) |
| Lead Storage | Excel (.xlsx) via openpyxl |
| Memory | Per-user JSON file store |
| Language | Python 3.11+ |

---

## Project Structure

```
zarik/
├── main.py                 # Entry point — FastAPI + Telegram bot
├── config.py               # Environment variables
├── Procfile                # Railway deployment
├── Dockerfile              # Docker deployment
├── requirements.txt
├── agent/
│   ├── graph.py            # LangGraph state machine
│   ├── state.py            # AgentState TypedDict
│   └── prompts.py          # System prompts for each node
├── api/
│   ├── routes.py           # FastAPI routes (leads CRUD)
│   └── schemas.py          # Pydantic models
├── bot/
│   ├── telegram_bot.py     # Telegram handlers + session management
│   └── formatters.py       # Message formatting for Telegram
├── leads/
│   └── excel_manager.py    # Excel CRUD with formatting
├── memory/
│   └── store.py            # Per-user JSON memory
├── tools/
│   └── itinerary_gen.py    # LLM itinerary generation
└── data/
    ├── leads.xlsx          # Auto-generated lead tracker
    └── memory/             # Per-user memory files
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- [Groq API key](https://console.groq.com/keys) (free)
- [Telegram Bot Token](https://t.me/BotFather) (free)

### Setup

```bash
# Clone
git clone https://github.com/Adarsh-Menon/Zarik-Travel-Agency-Support.git
cd Zarik-Travel-Agency-Support

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys (no quotes around values)

# Run
python main.py
```

### Environment Variables

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
TELEGRAM_BOT_TOKEN=your_bot_token_here
LEADS_EXCEL_PATH=data/leads.xlsx
MEMORY_DIR=data/memory
```

---

## Deployment

### Docker

```bash
docker build -t zarik .
docker run -d --restart=always --name zarik --env-file .env -p 8000:8000 -v $(pwd)/data:/app/data zarik
```

### Railway

1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Add environment variables in Railway dashboard
4. Deploy — Railway auto-detects Python and runs via `Procfile`

> **Important:** Only run one instance at a time. Running both Docker and Railway with the same bot token causes Telegram polling conflicts.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/leads` | List all leads (optional `?status=New` filter) |
| `GET` | `/api/leads/stats` | Lead count by status |
| `GET` | `/api/leads/{id}` | Get lead details |
| `PATCH` | `/api/leads/{id}` | Update lead (status, notes, phone) |

---

## Lead Excel Format

Auto-generated with color-coded status, frozen headers, and auto-filter:

| Lead ID | Name | Destination | Budget | Status | Created |
|---------|------|-------------|--------|--------|---------|
| ZRK-001 | Adarsh | Japan | Rs 50000 | 🔵 New | 2026-05-01 |
| ZRK-002 | Sarah | Bali | $2000 | 🟢 Converted | 2026-05-01 |

---

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Start a new trip planning session |
| `/mytrips` | View your past itineraries |
| `/help` | Show available commands |

---

## Skills & Frameworks Demonstrated

### AI / ML Skills

| Skill | How it's used in Zarik |
|-------|----------------------|
| **Agentic AI** | LangGraph stateful agent with conditional routing, multi-node orchestration, and tool-calling — not a simple prompt-response chain |
| **LLM Engineering** | Prompt design for structured extraction (JSON output from free-text), system prompt chaining across conversation phases, temperature tuning per task |
| **Conversational AI** | Multi-turn dialogue management with context carryover, intent detection, and natural preference extraction |
| **Structured Output Extraction** | LLM-powered JSON extraction from unstructured user messages with regex fallback and validation |
| **Memory & Personalization** | Per-user persistent memory store enabling cross-session personalization (ClawdBot pattern) |
| **Lead Automation / CRM** | Auto-capture and lifecycle management of leads in structured Excel format with status tracking |

### Frameworks & Technologies

| Category | Technologies |
|----------|-------------|
| **Agent Orchestration** | LangGraph (stateful graph), LangChain (LLM abstraction) |
| **LLM Inference** | Groq API, Llama 3.3 70B Versatile, langchain-groq |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Bot Framework** | python-telegram-bot (async, polling mode) |
| **Data Layer** | openpyxl (Excel CRUD), JSON file store (memory) |
| **DevOps** | Docker, Railway PaaS, systemd (Linux), GitHub CI/CD |
| **Language** | Python 3.11+ (async/await, type hints, TypedDict) |

### Architecture Patterns

| Pattern | Implementation |
|---------|---------------|
| **State Machine** | LangGraph graph with conditional edges routing between conversation phases |
| **Lazy Initialization** | LLM clients initialized on first use, not import time — enables cloud PaaS compatibility |
| **Tool-augmented Agent** | Dedicated tool nodes (itinerary generator, lead manager, memory store) invoked by the orchestrator |
| **Session Management** | In-memory session dict keyed by Telegram user ID, persisted to JSON between sessions |
| **Structured Logging** | Per-module loggers (zarik.extract, zarik.collect) for debugging agent decisions in production |
| **Safety Valve** | Auto-fallback to defaults after N collection steps to prevent infinite conversation loops |

---

## Roadmap

- [ ] RAG layer for destination knowledge (hotels, visa requirements, local tips)
- [ ] PDF itinerary export with agency branding
- [ ] Admin dashboard (React frontend)
- [ ] Multi-language support (Arabic for UAE market)
- [ ] Webhook mode for production Telegram integration
- [ ] Group trip coordination

---

## Built With

Built by [Adarsh Menon](https://github.com/Adarsh-Menon) as part of an AI automation agency initiative. Zarik demonstrates practical agentic AI — stateful conversation management, structured data extraction, and automated CRM — applied to the travel industry.

---

## License

MIT License — see [LICENSE](LICENSE) for details.