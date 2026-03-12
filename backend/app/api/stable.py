"""TravManager — Stable API Routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_stable
from app.models.race import RaceTrack
from app.services import stable_service
from app.services import travel_service
from app.services import finance_service
from app.api.schemas import PressReleaseRequest


class SetHomeTrackRequest(BaseModel):
    track_id: UUID

router = APIRouter()


@router.get("")
async def get_stable(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await stable_service.get_stable_summary(db, stable)


@router.get("/tracks")
async def get_all_tracks(
    db: AsyncSession = Depends(get_db),
    _stable=Depends(get_current_stable),
):
    """Return all available race tracks, sorted by prestige."""
    result = await db.execute(
        select(RaceTrack).order_by(RaceTrack.prestige.desc(), RaceTrack.name)
    )
    tracks = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "city": t.city,
            "region": t.region,
            "prestige": t.prestige,
        }
        for t in tracks
    ]


@router.get("/morning-report")
async def morning_report(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await stable_service.get_morning_report(db, stable)


@router.post("/daily-checkup")
async def daily_checkup(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    return await stable_service.daily_checkup(db, stable)


@router.post("/press-release")
async def create_press_release(
    req: PressReleaseRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    result = await stable_service.create_press_release(db, stable, req.tone, req.content)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/home-track")
async def set_home_track(
    req: SetHomeTrackRequest,
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Set the home track for this stable."""
    result = await travel_service.set_home_track(db, stable.id, req.track_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    await db.commit()
    return result


@router.get("/weekly-costs")
async def get_weekly_costs(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get estimated weekly costs for the stable."""
    return await finance_service.calculate_weekly_cost_estimate(db, stable.id)


# Box upgrade costs (escalating): level 0→1 = 50k kr, 1→2 = 100k kr, etc.
BOX_UPGRADE_COSTS = [
    5_000_000,    # 0→1: 50,000 kr → 4 boxes
    10_000_000,   # 1→2: 100,000 kr → 5 boxes
    15_000_000,   # 2→3: 150,000 kr → 6 boxes
    20_000_000,   # 3→4: 200,000 kr → 7 boxes
    30_000_000,   # 4→5: 300,000 kr → 8 boxes
    40_000_000,   # 5→6: 400,000 kr → 9 boxes
    50_000_000,   # 6→7: 500,000 kr → 10 boxes (MAX)
]


@router.post("/upgrade-boxes")
async def upgrade_boxes(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade stable capacity by adding a new box."""
    from app.models.game_state import GameState

    current_level = stable.box_upgrade_level or 0

    if current_level >= len(BOX_UPGRADE_COSTS):
        raise HTTPException(status_code=400, detail="Stallet är redan fullt uppgraderat (max 10 boxar)")

    cost = BOX_UPGRADE_COSTS[current_level]

    if stable.balance < cost:
        raise HTTPException(
            status_code=400,
            detail=f"Inte tillräckligt med pengar. Kostnad: {cost} öre, Saldo: {stable.balance} öre"
        )

    # Get current game week for transaction
    gs_result = await db.execute(
        select(GameState).where(GameState.id == 1)
    )
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    # Deduct cost
    stable.balance -= cost
    stable.box_upgrade_level = current_level + 1
    stable.max_horses = 3 + stable.box_upgrade_level  # 3 base + upgrades

    # Record transaction
    await finance_service.record_transaction(
        db, stable.id, -cost, "stable_costs",
        f"Boxuppgradering: {stable.max_horses - 1} → {stable.max_horses} boxar",
        game_week,
    )

    await db.commit()

    next_cost = BOX_UPGRADE_COSTS[stable.box_upgrade_level] if stable.box_upgrade_level < len(BOX_UPGRADE_COSTS) else None

    return {
        "success": True,
        "new_max_horses": stable.max_horses,
        "upgrade_level": stable.box_upgrade_level,
        "cost_paid": cost,
        "next_upgrade_cost": next_cost,
    }


@router.get("/box-info")
async def get_box_info(
    stable=Depends(get_current_stable),
    db: AsyncSession = Depends(get_db),
):
    """Get current box capacity info."""
    from app.models.horse import Horse

    # Count current horses
    horse_count_result = await db.execute(
        select(sqlfunc.count(Horse.id)).where(Horse.stable_id == stable.id)
    )
    horse_count = horse_count_result.scalar() or 0

    current_level = stable.box_upgrade_level or 0
    max_horses = stable.max_horses or 3
    next_cost = BOX_UPGRADE_COSTS[current_level] if current_level < len(BOX_UPGRADE_COSTS) else None

    return {
        "current_horses": horse_count,
        "max_horses": max_horses,
        "upgrade_level": current_level,
        "max_upgrade_level": len(BOX_UPGRADE_COSTS),
        "next_upgrade_cost": next_cost,
        "can_upgrade": current_level < len(BOX_UPGRADE_COSTS),
    }
