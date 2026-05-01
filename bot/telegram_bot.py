import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters,
)
from langchain_core.messages import HumanMessage

from agent.graph import zarik_graph
from agent.state import AgentState
from bot.formatters import format_for_telegram, chunk_message
from memory.store import load_memory
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

# In-memory session store: telegram_id -> AgentState
sessions: dict[int, dict] = {}


def _get_or_create_session(user_id: int, user_name: str, handle: str) -> dict:
    if user_id not in sessions:
        sessions[user_id] = {
            "messages": [],
            "telegram_id": user_id,
            "telegram_handle": handle,
            "user_name": user_name,
            "phase": "greet",
            "preferences": {},
            "itinerary": "",
            "lead_id": "",
            "memory_loaded": False,
            "user_memory": {},
            "collection_step": 0,
        }
    return sessions[user_id]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Traveler"
    handle = f"@{user.username}" if user.username else ""

    # Reset session for /start
    sessions.pop(user_id, None)
    session = _get_or_create_session(user_id, user_name, handle)

    result = zarik_graph.invoke(session)

    # Update session
    sessions[user_id] = result

    # Send response
    last_ai_msg = result["messages"][-1].content
    for chunk in chunk_message(format_for_telegram(last_ai_msg)):
        await update.message.reply_text(chunk, parse_mode="HTML")


async def mytrips_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    memory = load_memory(user_id)
    trips = memory.get("past_itineraries", [])

    if not trips:
        await update.message.reply_text("You haven't planned any trips with me yet! Send /start to begin. ✈️")
        return

    text = "🗺️ <b>Your Past Trips:</b>\n\n"
    for i, trip in enumerate(trips, 1):
        text += f"{i}. <b>{trip.get('destination', '?')}</b> — {trip.get('days', '?')} days ({trip.get('dates', 'N/A')})\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌍 <b>Zarik — AI Travel Assistant</b>\n\n"
        "/start — Plan a new trip\n"
        "/mytrips — View your past trips\n"
        "/help — Show this message\n\n"
        "Just tell me where you want to go and I'll handle the rest!"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Traveler"
    handle = f"@{user.username}" if user.username else ""
    text = update.message.text

    session = _get_or_create_session(user_id, user_name, handle)

    # Add user message to session
    session["messages"].append(HumanMessage(content=text))

    # Run graph
    try:
        result = zarik_graph.invoke(session)
        sessions[user_id] = result

        last_ai_msg = result["messages"][-1].content
        for chunk in chunk_message(format_for_telegram(last_ai_msg)):
            await update.message.reply_text(chunk, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Agent error for user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(
            "Oops, something went wrong on my end. Please try again or /start fresh! 🙏"
        )


def create_bot_app() -> Application:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("mytrips", mytrips_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
