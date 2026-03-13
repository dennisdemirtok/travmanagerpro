"""TravManager — Horses API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.horse import Horse
from app.models.stable import Stable
from app.services import horse_service
from app.services.race_service import calculate_start_points
from app.services.game_init_service import SEASON_LENGTH_WEEKS
from app.api.schemas import ChangeShoeRequest, ChangeTrainingRequest, UpdateFeedRequest

router = APIRouter()


@router.get("/database")
async def horse_database(
    sort: str = Query(default="earnings"),
    search: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
    _stable=Depends(get_current_stable),
):
    """Public database of all horses in the game."""
    q = (
        select(Horse, Stable.name.label("stable_name"))
        .join(Stable, Horse.stable_id == Stable.id)
    )
    if search:
        q = q.where(Horse.name.ilike(f"%{search}%"))

    sort_map = {
        "earnings": Horse.total_earnings.desc(),
        "name": Horse.name.asc(),
        "age": Horse.age_years.desc(),
        "speed": Horse.speed.desc(),
        "starts": Horse.total_starts.desc(),
    }
    q = q.order_by(sort_map.get(sort, Horse.total_earnings.desc()))

    result = await db.execute(q)
    rows = result.all()

    def _calc_total_skill(h):
        avg = (h.speed + h.endurance + h.mentality + h.start_ability +
               h.sprint_strength + h.balance + h.strength) / 7
        return max(1, min(20, round(avg / 5)))

    return {
        "horses": [
            {
                "id": str(h.id),
                "name": h.name,
                "gender": h.gender.value,
                "age_years": h.age_years,
                "stable_name": stable_name,
                "is_npc": h.is_npc,
                "status": h.status.value,
                "total_skill": _calc_total_skill(h),
                "speed": h.speed,
                "endurance": h.endurance,
                "sprint_strength": h.sprint_strength,
                "mentality": h.mentality,
                "total_starts": h.total_starts,
                "total_wins": h.total_wins,
                "total_seconds": h.total_seconds,
                "total_thirds": h.total_thirds,
                "total_earnings": h.total_earnings,
                "best_km_time_display": h.best_km_time_display,
                "distance_optimum": h.distance_optimum,
            }
            for h, stable_name in rows
        ],
        "total": len(rows),
    }


@router.get("")
async def list_horses(
    status: str = Query(default="all"),
    sort: str = Query(default="name"),
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    import logging
    logger = logging.getLogger(__name__)
    try:
        horses = await horse_service.list_horses(db, stable.id, status_filter=status, sort_by=sort)
        return {"horses": horses, "total": len(horses)}
    except Exception as e:
        logger.exception(f"Error listing horses for stable {stable.id}")
        raise HTTPException(status_code=500, detail=str(e))


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
