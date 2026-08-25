"""TravManager — Dagsloop API (träning, stallrunda, beslut)"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState
from app.services import daily_service
from app.services.game_init_service import calculate_game_time

router = APIRouter()


class TrainingRequest(BaseModel):
    horse_id: UUID
    program: str


class ResolveRequest(BaseModel):
    choice: str


async def _time(db: AsyncSession) -> dict:
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    if not gs:
        return {"game_week": 1, "game_day": 1, "total_game_days": 1}
    return calculate_game_time(gs.real_week_start)


@router.get("/training-options")
async def training_options():
    return {"options": daily_service.training_options()}


@router.post("/training")
async def set_training(
    req: TrainingRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await daily_service.set_training(db, stable.id, req.horse_id, req.program)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.post("/stable-round")
async def stable_round(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    t = await _time(db)
    result = await daily_service.run_stable_round(
        db, stable.id, t["game_week"], t["game_day"], t["total_game_days"],
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.get("/events")
async def pending_events(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return {"events": await daily_service.get_pending_events(db, stable.id)}


@router.post("/events/{event_id}/resolve")
async def resolve_event(
    event_id: UUID,
    req: ResolveRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    t = await _time(db)
    result = await daily_service.resolve_event(
        db, stable.id, event_id, req.choice, t["game_week"], t["total_game_days"],
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result
