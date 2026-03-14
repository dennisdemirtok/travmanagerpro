"""TravManager — Hidden Properties Generation & Observation Service"""
import math
import random
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hidden_properties import HorseHiddenProperties
from app.models.observation import HorseObservation


def _normal_random(rng: random.Random, stddev: float = 10.0) -> float:
    """Box-Muller normal distribution."""
    u1 = max(1e-10, rng.random())
    u2 = rng.random()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2) * stddev


def _clamp(val, min_val, max_val):
    return max(min_val, min(max_val, round(val)))


async def generate_hidden_properties(db: AsyncSession, horse_id, seed: int = None) -> HorseHiddenProperties:
    """Generate hidden properties for a horse. Called at horse creation."""
    # Check if already exists
    existing = await db.execute(
        select(HorseHiddenProperties).where(HorseHiddenProperties.horse_id == horse_id)
    )
    if existing.scalar_one_or_none():
        return existing.scalar_one_or_none()

    rng = random.Random(seed or hash(str(horse_id)))

    props = HorseHiddenProperties(
        horse_id=horse_id,
        # Equipment preferences (-30 to +30)
        barefoot_affinity=_clamp(_normal_random(rng), -30, 30),
        american_sulky_affinity=_clamp(_normal_random(rng), -30, 30),
        racing_sulky_affinity=_clamp(_normal_random(rng), -30, 30),
        # Track preferences (-20 to +20)
        tight_curve_ability=_clamp(_normal_random(rng, 7), -20, 20),
        long_homestretch_affinity=_clamp(_normal_random(rng, 7), -20, 20),
        heavy_track_affinity=_clamp(_normal_random(rng, 7), -20, 20),
        # Mental hidden
        confidence_sensitivity=Decimal(str(round(max(0.3, min(2.0, 0.5 + rng.random())), 2))),
        crowd_response=_clamp(_normal_random(rng, 7), -20, 20),
        recovery_rate=Decimal(str(round(max(0.4, min(1.8, 0.5 + rng.random())), 2))),
        start_frequency_preference=rng.choices(
            ["frequent", "normal", "sparse"], weights=[30, 40, 30]
        )[0],
        peak_age=_clamp(5 + _normal_random(rng, 2), 3, 10),
        late_bloomer=rng.random() < 0.15,
        # Physical hidden
        natural_speed_ceiling=_clamp(_normal_random(rng, 5), -5, 15),
        hidden_sprint_gear=rng.random() < 0.10,
        wind_sensitivity=Decimal(str(round(max(0.5, min(1.5, 0.7 + rng.random() * 0.6)), 2))),
        temperature_optimum=_clamp(8 + rng.random() * 12, 2, 25),
        temperature_tolerance=_clamp(8 + rng.random() * 14, 5, 25),
    )
    db.add(props)
    await db.flush()
    return props


async def get_hidden_properties(db: AsyncSession, horse_id) -> HorseHiddenProperties | None:
    """Get hidden properties for a horse."""
    result = await db.execute(
        select(HorseHiddenProperties).where(HorseHiddenProperties.horse_id == horse_id)
    )
    return result.scalar_one_or_none()


async def ensure_hidden_properties(db: AsyncSession, horse_id) -> HorseHiddenProperties:
    """Get or generate hidden properties."""
    props = await get_hidden_properties(db, horse_id)
    if not props:
        props = await generate_hidden_properties(db, horse_id)
    return props


async def generate_observations(
    db: AsyncSession,
    horse_id,
    stable_id,
    hidden: HorseHiddenProperties,
    equipment: dict,
    race_result: dict,
    game_week: int,
    race_id=None,
) -> list[dict]:
    """Generate post-race observation notes based on hidden properties.
    Returns list of observation dicts.
    """
    rng = random.Random(hash(str(horse_id)) + game_week)
    observations = []

    # Barefoot observation
    shoe = equipment.get("shoe", "normal_steel")
    if shoe == "barefoot" and abs(hidden.barefoot_affinity) > 12:
        if hidden.barefoot_affinity > 12:
            observations.append({
                "type": "equipment_positive",
                "text": "Hästen verkade trivas utan skor — lättare steg och bättre balans.",
                "confidence": min(0.9, abs(hidden.barefoot_affinity) / 35),
            })
        else:
            observations.append({
                "type": "equipment_negative",
                "text": "Hästen verkade osäker utan skor — trevade lite i underlaget.",
                "confidence": min(0.9, abs(hidden.barefoot_affinity) / 35),
            })

    # Sulky observation
    sulky = equipment.get("sulky", "european")
    if sulky == "american" and abs(hidden.american_sulky_affinity) > 12:
        if hidden.american_sulky_affinity > 12:
            observations.append({
                "type": "equipment_positive",
                "text": "Hästen gick fint med den amerikanska sulkyn — verkade avslappnad.",
                "confidence": min(0.9, abs(hidden.american_sulky_affinity) / 35),
            })
        else:
            observations.append({
                "type": "equipment_negative",
                "text": "Hästen verkade obekväm i den amerikanska sulkyn — lite ryckig.",
                "confidence": min(0.9, abs(hidden.american_sulky_affinity) / 35),
            })

    if sulky == "racing" and abs(hidden.racing_sulky_affinity) > 12:
        if hidden.racing_sulky_affinity > 12:
            observations.append({
                "type": "equipment_positive",
                "text": "Hästen verkade älska racing-sulkyn — flög fram!",
                "confidence": min(0.9, abs(hidden.racing_sulky_affinity) / 35),
            })
        else:
            observations.append({
                "type": "equipment_negative",
                "text": "Hästen var instabil i racing-sulkyn — darrade i kurvorna.",
                "confidence": min(0.9, abs(hidden.racing_sulky_affinity) / 35),
            })

    # Temperature observation
    temp = race_result.get("temperature", 12)
    if temp is not None:
        temp_diff = abs(temp - int(hidden.temperature_optimum))
        if temp_diff > int(hidden.temperature_tolerance) + 5:
            if temp > int(hidden.temperature_optimum):
                observations.append({
                    "type": "condition_negative",
                    "text": "Hästen verkade besvärad av värmen — svettades ovanligt mycket.",
                    "confidence": min(0.8, temp_diff / 25),
                })
            else:
                observations.append({
                    "type": "condition_negative",
                    "text": "Hästen verkade frysig och stel i det kalla vädret.",
                    "confidence": min(0.8, temp_diff / 25),
                })

    # Crowd observation
    track_prestige = race_result.get("track_prestige", 50)
    if hidden.crowd_response < -12 and track_prestige > 70:
        observations.append({
            "type": "mental_negative",
            "text": "Hästen blev stressig i paddocken — verkar inte trivas med stor publik.",
            "confidence": min(0.8, abs(hidden.crowd_response) / 20),
        })
    elif hidden.crowd_response > 12 and track_prestige > 70:
        observations.append({
            "type": "mental_positive",
            "text": "Hästen verkade peppad av publiken — spelade med öronen och steppade upp.",
            "confidence": min(0.8, abs(hidden.crowd_response) / 20),
        })

    # Heavy track observation
    surface = race_result.get("surface", "dirt")
    weather = race_result.get("weather", "clear")
    is_heavy = surface == "winter" or weather in ("heavy_rain", "rain")
    if is_heavy and abs(hidden.heavy_track_affinity) > 10:
        if hidden.heavy_track_affinity > 10:
            observations.append({
                "type": "condition_positive",
                "text": "Hästen verkade trivas på det tunga underlaget — stabila steg.",
                "confidence": min(0.8, abs(hidden.heavy_track_affinity) / 20),
            })
        else:
            observations.append({
                "type": "condition_negative",
                "text": "Hästen kämpade på det tunga underlaget — tappade fart i kurvorna.",
                "confidence": min(0.8, abs(hidden.heavy_track_affinity) / 20),
            })

    # Start frequency observation
    days_since = race_result.get("days_since_last_race", 14)
    pref = hidden.start_frequency_preference
    if pref == "frequent" and days_since > 21:
        observations.append({
            "type": "mental_negative",
            "text": "Hästen verkar rastlös — kanske behöver den starta oftare?",
            "confidence": 0.6,
        })
    elif pref == "sparse" and race_result.get("races_last_30_days", 0) >= 3:
        observations.append({
            "type": "mental_negative",
            "text": "Hästen verkar sliten — kanske har den startat för tätt?",
            "confidence": 0.6,
        })

    # Sort by confidence and limit to 3
    observations.sort(key=lambda x: x.get("confidence", 0.5), reverse=True)
    observations = observations[:3]

    # Save to DB
    saved = []
    for obs in observations:
        db_obs = HorseObservation(
            horse_id=horse_id,
            stable_id=stable_id,
            game_week=game_week,
            observation_type=obs["type"],
            text=obs["text"],
            confidence_level=Decimal(str(round(obs.get("confidence", 0.5), 2))),
            race_id=race_id,
        )
        db.add(db_obs)
        saved.append(obs)

    if saved:
        await db.flush()

    return saved


async def get_horse_diary(db: AsyncSession, horse_id, stable_id, limit: int = 20) -> list[dict]:
    """Get observation diary for a horse."""
    result = await db.execute(
        select(HorseObservation)
        .where(
            HorseObservation.horse_id == horse_id,
            HorseObservation.stable_id == stable_id,
        )
        .order_by(HorseObservation.created_at.desc())
        .limit(limit)
    )
    observations = result.scalars().all()
    return [
        {
            "id": str(o.id),
            "game_week": o.game_week,
            "type": o.observation_type,
            "text": o.text,
            "confidence": float(o.confidence_level) if o.confidence_level else 0.5,
            "race_id": str(o.race_id) if o.race_id else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in observations
    ]
