"""TravManager — Säsongsmål och säsongssammanfattning API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.game_state import GameState, Season
from app.services import season_service

router = APIRouter()


@router.get("/goals")
async def season_goals(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    week = gs.current_game_week if gs else 1
    goals = await season_service.refresh_goals(db, stable.id, week)
    await db.commit()

    season = await db.get(Season, gs.current_season_id) if gs and gs.current_season_id else None
    return {
        "season_number": season.season_number if season else 1,
        "week_in_season": (week - season.start_game_week + 1) if season else week,
        "season_length": (season.end_game_week - season.start_game_week + 1) if season else 10,
        "goals": goals,
        "completed": sum(1 for g in goals if g["is_completed"]),
    }


@router.get("/summary")
async def season_summary(
    season_number: int = Query(default=None),
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await season_service.build_season_summary(db, stable.id, season_number)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
