"""TravManager — Travel Service

Calculates travel costs, energy/form impact based on stable's home track
vs. the race track location (region-based distances).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.race import RaceTrack
from app.models.stable import Stable
from app.data.real_tracks import REGION_DISTANCES, TRAVEL_EFFECTS


def get_region_distance(region_a: str | None, region_b: str | None) -> int:
    """Get the number of hops between two regions (0-3)."""
    if not region_a or not region_b:
        return 1  # Default if missing
    if region_a == region_b:
        return 0
    pair = tuple(sorted([region_a, region_b]))
    return REGION_DISTANCES.get(pair, 2)


def calculate_travel_effects(distance_hops: int) -> dict:
    """Get travel cost and physical effects for a given distance."""
    return TRAVEL_EFFECTS.get(distance_hops, TRAVEL_EFFECTS[2])


async def calculate_travel(
    db: AsyncSession, stable_id, race_track_id
) -> dict:
    """Calculate full travel info for a stable going to a race track.

    Returns:
        dict with cost, energy_loss, form_impact, distance_hops, home_region, race_region
    """
    # Get stable with home track
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    # Get race track
    race_track_result = await db.execute(
        select(RaceTrack).where(RaceTrack.id == race_track_id)
    )
    race_track = race_track_result.scalar_one_or_none()
    if not race_track:
        return {"error": "Bana hittades inte"}

    # Get home track region
    home_region = None
    if stable.home_track_id:
        home_track_result = await db.execute(
            select(RaceTrack).where(RaceTrack.id == stable.home_track_id)
        )
        home_track = home_track_result.scalar_one_or_none()
        if home_track:
            home_region = home_track.region

    race_region = race_track.region
    distance_hops = get_region_distance(home_region, race_region)
    effects = calculate_travel_effects(distance_hops)

    return {
        "distance_hops": distance_hops,
        "cost": effects["cost"],
        "energy_loss": effects["energy_loss"],
        "form_impact": effects["form_impact"],
        "home_region": home_region or "okänd",
        "race_region": race_region or "okänd",
        "home_bonus": distance_hops == 0,
    }


async def apply_travel_effects(
    db: AsyncSession, horse, distance_hops: int
):
    """Apply travel fatigue/form effects to a horse before race."""
    effects = calculate_travel_effects(distance_hops)
    horse.energy = max(0, horse.energy - effects["energy_loss"])
    horse.form = max(0, horse.form + effects["form_impact"])  # form_impact is negative

    # Home track bonus
    if distance_hops == 0:
        horse.form = min(100, horse.form + 3)
        horse.mood = min(100, horse.mood + 2)


async def set_home_track(db: AsyncSession, stable_id, track_id) -> dict:
    """Set the home track for a stable."""
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    track_result = await db.execute(select(RaceTrack).where(RaceTrack.id == track_id))
    track = track_result.scalar_one_or_none()
    if not track:
        return {"error": "Bana hittades inte"}

    stable.home_track_id = track_id
    await db.flush()

    return {
        "success": True,
        "home_track": track.name,
        "region": track.region,
    }
