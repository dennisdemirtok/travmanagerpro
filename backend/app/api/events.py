"""TravManager — Events API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.services import event_service

router = APIRouter()


@router.get("")
async def list_events(
    unread: bool = Query(default=False),
    limit: int = Query(default=20),
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    events = await event_service.get_events(db, stable.id, unread_only=unread, limit=limit)
    return {"events": events}


@router.post("/{event_id}/action")
async def handle_event_action(
    event_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await event_service.handle_action(db, event_id, stable.id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
