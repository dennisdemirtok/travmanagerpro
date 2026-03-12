"""TravManager — Races API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.schemas import RaceEntryRequest, UpdateTacticsRequest
from app.core.deps import get_db, get_current_stable
from app.services import race_service

router = APIRouter()


@router.get("/schedule")
async def race_schedule(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    schedule = await race_service.get_race_schedule(db, stable_id=stable.id)
    return {"sessions": schedule}


@router.post("/{race_id}/enter")
async def enter_race(
    race_id: UUID,
    req: RaceEntryRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await race_service.enter_race(
            db, race_id, req.horse_id, req.driver_id, stable.id,
            req.shoe, req.tactics.model_dump(),
        )
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Hasten ar redan anmald till detta lopp")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{race_id}/result")
async def get_race_result(
    race_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await race_service.get_race_result(db, race_id)
    if not result:
        raise HTTPException(status_code=404, detail="Loppet hittades inte eller ar inte avslutat")
    return result


@router.put("/entries/{entry_id}/tactics")
async def update_tactics(
    entry_id: UUID,
    req: UpdateTacticsRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await race_service.update_entry_tactics(db, entry_id, stable.id, req.model_dump(exclude_none=True))
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/entries/{entry_id}")
async def withdraw_entry(
    entry_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await race_service.withdraw_entry(db, entry_id, stable.id)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
