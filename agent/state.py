from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class TravelPreferences(TypedDict, total=False):
    destination: str
    travel_dates: str
    duration_days: int
    budget: str
    group_size: int
    interests: list[str]
    dietary: str
    special_requests: str


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    telegram_id: int
    telegram_handle: str
    user_name: str
    phase: Literal["greet", "collect", "generate", "followup", "modify", "end"]
    preferences: TravelPreferences
    itinerary: str
    lead_id: str
    memory_loaded: bool
    user_memory: dict
    collection_step: int  # tracks which preference we're collecting
