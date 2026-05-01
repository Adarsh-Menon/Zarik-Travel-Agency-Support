from fastapi import APIRouter, HTTPException, Query
from api.schemas import LeadUpdate, StatsResponse
from leads.excel_manager import get_all_leads, get_lead, update_lead, get_lead_stats

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "zarik"}


# ── Lead Management API ────────────────────────────────────


@router.get("/api/leads")
async def list_leads(status: str = Query(None, description="Filter by status")):
    leads = get_all_leads(status_filter=status)
    return {"leads": leads, "count": len(leads)}


@router.get("/api/leads/stats")
async def lead_stats():
    return get_lead_stats()


@router.get("/api/leads/{lead_id}")
async def get_lead_detail(lead_id: str):
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/api/leads/{lead_id}")
async def update_lead_endpoint(lead_id: str, update: LeadUpdate):
    fields = {k: v for k, v in update.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = update_lead(lead_id, **fields)
    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "updated", "lead_id": lead_id}
