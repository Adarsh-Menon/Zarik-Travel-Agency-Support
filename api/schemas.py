from pydantic import BaseModel
from typing import Optional


class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    phone: Optional[str] = None
    destination: Optional[str] = None


class LeadResponse(BaseModel):
    lead_id: str
    name: str
    telegram_handle: str
    destination: str
    status: str
    budget: str
    created_at: str


class StatsResponse(BaseModel):
    total: int
    by_status: dict[str, int]
