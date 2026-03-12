"""TravManager — Leaderboard API Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.stable import Stable
from app.models.horse import Horse

router = APIRouter()


@router.get("/stables")
async def get_stable_leaderboard(
    db: AsyncSession = Depends(get_db),
    _stable=Depends(get_current_stable),
):
    """Top stables by total earnings."""
    result = await db.execute(
        select(Stable)
        .order_by(Stable.total_earnings.desc())
        .limit(20)
    )
    stables = result.scalars().all()

    # Count horses per stable
    horse_counts = {}
    for s in stables:
        count_result = await db.execute(
            select(sqlfunc.count(Horse.id)).where(Horse.stable_id == s.id)
        )
        horse_counts[s.id] = count_result.scalar() or 0

    return {
        "stables": [
            {
                "rank": i + 1,
                "name": s.name,
                "is_npc": s.is_npc,
                "total_earnings": s.total_earnings,
                "reputation": s.reputation,
                "fan_count": s.fan_count,
                "horse_count": horse_counts.get(s.id, 0),
            }
            for i, s in enumerate(stables)
        ]
    }


@router.get("/horses")
async def get_horse_leaderboard(
    db: AsyncSession = Depends(get_db),
    _stable=Depends(get_current_stable),
):
    """Top horses by total earnings."""
    result = await db.execute(
        select(Horse, Stable.name.label("stable_name"))
        .join(Stable, Horse.stable_id == Stable.id)
        .order_by(Horse.total_earnings.desc())
        .limit(30)
    )
    rows = result.all()

    return {
        "horses": [
            {
                "rank": i + 1,
                "name": h.name,
                "gender": h.gender.value if hasattr(h.gender, 'value') else str(h.gender),
                "age_years": h.age_years,
                "stable_name": stable_name,
                "is_npc": h.is_npc,
                "total_earnings": h.total_earnings,
                "total_starts": h.total_starts,
                "total_wins": h.total_wins,
                "total_seconds": h.total_seconds,
                "total_thirds": h.total_thirds,
                "best_km_time": h.best_km_time,
            }
            for i, (h, stable_name) in enumerate(rows)
        ]
    }
