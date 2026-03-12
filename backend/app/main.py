"""
TravManager — Main FastAPI Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import auth, stable, horses, races, drivers, finances, events, game, sponsors, market, breeding, training, leaderboard
from app.core.database import init_db, close_db, async_session
from app.services import race_ticker_service

logger = logging.getLogger(__name__)


async def race_poller():
    """Background task that checks for races to simulate every 60 seconds."""
    while True:
        try:
            async with async_session() as db:
                simulated = await race_ticker_service.tick_races(db)
                await db.commit()
                if simulated:
                    logger.info(f"Race poller: simulated {len(simulated)} sessions")
        except Exception as e:
            logger.error(f"Race poller error: {e}")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("TravManager starting up...")
    await init_db()
    poller_task = asyncio.create_task(race_poller())
    yield
    # Shutdown
    poller_task.cancel()
    print("TravManager shutting down...")
    await close_db()


app = FastAPI(
    title="TravManager API",
    description="Online harness racing manager game — API backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "game": "TravManager", "version": "0.1.0"}


# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(stable.router, prefix="/api/v1/stable", tags=["stable"])
app.include_router(horses.router, prefix="/api/v1/horses", tags=["horses"])
app.include_router(races.router, prefix="/api/v1/races", tags=["races"])
app.include_router(drivers.router, prefix="/api/v1/drivers", tags=["drivers"])
app.include_router(finances.router, prefix="/api/v1/finances", tags=["finances"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(game.router, prefix="/api/v1/game", tags=["game"])
app.include_router(sponsors.router, prefix="/api/v1/sponsors", tags=["sponsors"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(breeding.router, prefix="/api/v1/breeding", tags=["breeding"])
app.include_router(training.router, prefix="/api/v1/training", tags=["training"])
app.include_router(leaderboard.router, prefix="/api/v1/leaderboard", tags=["leaderboard"])


# Temporary: Test race engine directly
@app.get("/api/v1/test-race")
async def test_race():
    """Run a test race simulation and return results."""
    import random
    from app.engine.race_engine import (
        RaceEngine, NPCGenerator, RaceEntry, RaceConditions,
        HorseStats, DriverStats, Tactics, StartMethod, Surface,
        Weather, ShoeType, Positioning, Tempo, SprintOrder,
        GallopSafety, calculate_compatibility, generate_race_seed,
    )
    
    engine = RaceEngine()
    npc_gen = NPCGenerator(random.Random(42))

    player_horse = HorseStats(
        id="test_h1", name="Bliansen",
        speed=78, endurance=82, mentality=71, start_ability=85,
        sprint_strength=74, balance=65, strength=70,
        gallop_tendency=12, condition=92, form=65, mood=80,
        personality_primary="brave", personality_secondary="responsive",
    )
    player_driver = DriverStats(
        id="test_d1", name="Erik Lindblom",
        skill=82, start_skill=78, tactical_ability=78,
        sprint_timing=85, gallop_handling=80, experience=74, composure=72,
        driving_style="tactical",
    )
    
    compat = calculate_compatibility(player_horse, player_driver, 8)
    
    player_entry = RaceEntry(
        horse=player_horse, driver=player_driver,
        tactics=Tactics(positioning=Positioning.SECOND, tempo=Tempo.BALANCED,
                       sprint_order=SprintOrder.NORMAL_400M, gallop_safety=GallopSafety.NORMAL),
        shoe=ShoeType.LIGHT_ALUMINUM,
        compatibility_score=compat,
    )

    conditions = RaceConditions(
        distance=2140, start_method=StartMethod.AUTO,
        surface=Surface.DIRT, weather=Weather.CLEAR,
        temperature=14, division_level=3,
    )
    conditions.prize_pool = 15000000

    field = npc_gen.fill_race_field([player_entry], division_level=3)
    seed = generate_race_seed("test_001", "2024-01-15T19:30:00")
    result = engine.simulate("test_001", field, conditions, seed)

    return {
        "race_id": result.race_id,
        "distance": result.distance,
        "field_size": len(field),
        "seed": result.seed,
        "finishers": [
            {
                "position": f.finish_position,
                "horse": f.horse_name,
                "km_time": f.km_time_display,
                "prize": f.prize_money,
                "energy_at_finish": f.energy_at_finish,
                "gallop_incidents": f.gallop_incidents,
                "driver_rating": f.driver_rating,
                "compatibility": f.compatibility_score,
            }
            for f in result.finishers
        ],
        "disqualified": [
            {"horse": d.horse_name, "reason": d.dq_reason}
            for d in result.disqualified
        ],
        "events": [
            {"type": e.event_type, "horse": e.horse_name, "text": e.text}
            for e in result.events if e.event_type != "start"
        ],
        "total_snapshots": len(result.snapshots),
        "player_compatibility": compat,
    }
