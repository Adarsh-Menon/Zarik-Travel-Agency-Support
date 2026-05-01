import json
import os
from datetime import datetime, date
from config import MEMORY_DIR


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def _path(telegram_id: int) -> str:
    os.makedirs(MEMORY_DIR, exist_ok=True)
    return os.path.join(MEMORY_DIR, f"{telegram_id}.json")


def load_memory(telegram_id: int) -> dict:
    path = _path(telegram_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {
        "telegram_id": telegram_id,
        "name": "",
        "first_seen": datetime.now().isoformat(),
        "last_seen": datetime.now().isoformat(),
        "preferences": {
            "preferred_destinations": [],
            "travel_style": "",
            "budget_range": "",
            "dietary": "",
            "group_size_typical": 0,
        },
        "past_itineraries": [],
        "conversation_summary": "",
    }


def save_memory(telegram_id: int, memory: dict):
    memory["last_seen"] = datetime.now().isoformat()
    path = _path(telegram_id)
    with open(path, "w") as f:
        json.dump(memory, f, indent=2, cls=DateEncoder)


def update_memory_from_trip(telegram_id: int, preferences: dict, itinerary_summary: str):
    memory = load_memory(telegram_id)

    dest = preferences.get("destination", "")
    if dest and dest not in memory["preferences"]["preferred_destinations"]:
        memory["preferences"]["preferred_destinations"].append(dest)

    if preferences.get("budget"):
        memory["preferences"]["budget_range"] = preferences["budget"]
    if preferences.get("group_size"):
        memory["preferences"]["group_size_typical"] = preferences["group_size"]
    if preferences.get("dietary"):
        memory["preferences"]["dietary"] = preferences["dietary"]

    interests = preferences.get("interests", [])
    if interests:
        memory["preferences"]["travel_style"] = ", ".join(interests)

    memory["past_itineraries"].append({
        "destination": dest,
        "dates": preferences.get("travel_dates", ""),
        "days": preferences.get("duration_days", 0),
        "generated_at": datetime.now().isoformat(),
    })

    # Keep only last 10 itineraries
    memory["past_itineraries"] = memory["past_itineraries"][-10:]

    save_memory(telegram_id, memory)
    return memory
