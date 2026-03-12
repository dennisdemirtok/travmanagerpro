"""TravManager — Horses API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.services import horse_service
from app.services.race_service import calculate_start_points
from app.api.schemas import ChangeShoeRequest, ChangeTrainingRequest, UpdateFeedRequest

router = APIRouter()


@router.get("")
async def list_horses(
    status: str = Query(default="all"),
    sort: str = Query(default="name"),
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    horses = await horse_service.list_horses(db, stable.id, status_filter=status, sort_by=sort)
    return {"horses": horses, "total": len(horses)}


@router.get("/{horse_id}")
async def get_horse(
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    detail = await horse_service.get_horse_detail(db, horse_id, stable.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Hästen hittades inte")
    return detail


@router.get("/{horse_id}/start-points")
async def get_start_points(
    horse_id: UUID,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    sp = await calculate_start_points(db, horse_id)
    return sp


@router.put("/{horse_id}/shoe")
async def change_shoe(
    horse_id: UUID,
    req: ChangeShoeRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await horse_service.change_shoe(db, horse_id, stable.id, req.shoe_type)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/{horse_id}/training")
async def change_training(
    horse_id: UUID,
    req: ChangeTrainingRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await horse_service.change_training(db, horse_id, stable.id, req.program, req.intensity)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/{horse_id}/feed")
async def update_feed(
    horse_id: UUID,
    req: UpdateFeedRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await horse_service.update_feed_plan(db, horse_id, stable.id, [f.model_dump() for f in req.feeds])
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
