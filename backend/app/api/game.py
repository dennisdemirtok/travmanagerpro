"""TravManager — Game State API Routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db
from app.services import game_init_service, race_service, race_ticker_service
from app.models.race import RaceSession

router = APIRouter()


@router.get("/state")
async def game_state(db: AsyncSession = Depends(get_db)):
    state = await game_init_service.get_game_state(db)
    if not state:
        raise HTTPException(status_code=404, detail="Speldata inte initierad. Kör POST /game/init")
    return state


@router.post("/init")
async def init_game(db: AsyncSession = Depends(get_db)):
    gs = await game_init_service.bootstrap_game(db)
    return {"status": "ok", "game_week": gs.current_game_week}


@router.post("/dev/advance")
async def dev_advance(
    hours: int = Query(default=12, description="Hours to advance (12 = 1 game day)"),
    db: AsyncSession = Depends(get_db),
):
    """DEV ONLY: Advance game time for testing."""
    result = await game_init_service.dev_advance_time(db, hours)
    if not result:
        raise HTTPException(status_code=404, detail="Speldata inte initierad")
    return result


@router.post("/dev/simulate-next")
async def dev_simulate_next(db: AsyncSession = Depends(get_db)):
    """DEV ONLY: Simulate the next unsimulated race session immediately."""
    # Find next unsimulated session
    result = await db.execute(
        select(RaceSession)
        .options(selectinload(RaceSession.races), selectinload(RaceSession.track))
        .where(RaceSession.is_simulated == False)
        .order_by(RaceSession.game_week, RaceSession.game_day)
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Inga osimulerade sessioner hittades")

    # Run the full simulation pipeline
    await race_service.simulate_race_session(db, session)
    await db.commit()

    return {
        "status": "ok",
        "simulated_session": str(session.id),
        "track": session.track.name if session.track else "",
        "game_week": session.game_week,
        "game_day": session.game_day,
        "races_count": len(session.races),
    }


@router.post("/dev/tick")
async def dev_tick(db: AsyncSession = Depends(get_db)):
    """DEV ONLY: Force a game tick (recovery, weekly processing, race simulation)."""
    await race_ticker_service.tick_races(db)
    return {"status": "ok"}


@router.post("/dev/reset-time")
async def dev_reset_time(db: AsyncSession = Depends(get_db)):
    """DEV ONLY: Reset real_week_start to Monday of current week and fix season to 10 weeks.
    Use this after upgrading from 2x speed to 1:1 time system.
    """
    from datetime import datetime, timedelta
    from app.models.game_state import GameState, Season
    from app.services.game_init_service import SEASON_LENGTH_WEEKS

    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    if not gs:
        raise HTTPException(status_code=404, detail="Speldata inte initierad")

    # Anchor real_week_start to Monday 00:00 UTC of current week
    now = datetime.utcnow()
    days_since_monday = now.weekday()
    monday = (now - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    gs.real_week_start = monday
    gs.current_game_week = 1
    gs.current_game_day = days_since_monday + 1
    gs.last_weekly_processing_week = None
    gs.last_recovery_game_day = None

    # Fix active season to 10 weeks
    if gs.current_season_id:
        sr = await db.execute(select(Season).where(Season.id == gs.current_season_id))
        season = sr.scalar_one_or_none()
        if season:
            season.start_game_week = 1
            season.end_game_week = SEASON_LENGTH_WEEKS

    await db.flush()

    return {
        "status": "ok",
        "real_week_start": monday.isoformat(),
        "current_day": days_since_monday + 1,
        "message": f"Tid nollställd till måndag {monday.strftime('%Y-%m-%d')}. Dag {days_since_monday + 1} (1=Mån).",
    }


@router.post("/dev/run-migrations")
async def dev_run_migrations(db: AsyncSession = Depends(get_db)):
    """DEV ONLY: Run all pending migrations manually."""
    from sqlalchemy import text

    migrations = [
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS form_history JSONB NOT NULL DEFAULT '[]'",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS age_years INTEGER NOT NULL DEFAULT 3",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS special_traits JSONB DEFAULT '[]'",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS traits_revealed BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS is_breeding_available BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS stud_fee BIGINT",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS pregnancy_week INTEGER",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS expected_foal_week INTEGER",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS training_locked_until INTEGER",
        "ALTER TABLE horses ADD COLUMN IF NOT EXISTS training_last_result JSONB",
    ]

    applied = []
    for sql in migrations:
        try:
            await db.execute(text(sql))
            applied.append(sql.split("IF NOT EXISTS ")[1].split(" ")[0] if "IF NOT EXISTS" in sql else "ok")
        except Exception as e:
            applied.append(f"skip: {str(e)[:80]}")

    await db.commit()
    return {"status": "ok", "applied": applied}
