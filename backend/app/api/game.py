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
