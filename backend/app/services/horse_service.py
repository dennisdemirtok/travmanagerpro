"""TravManager — Horse Service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.horse import Horse
from app.models.enums import ShoeType
from app.models.driver import DriverContract, Driver
from app.models.facility import FeedPlan
from app.models.race import RaceEntry
from app.engine.race_engine import calculate_compatibility, HorseStats, DriverStats


async def list_horses(db: AsyncSession, stable_id, status_filter=None, sort_by="name"):
    q = select(Horse).where(Horse.stable_id == stable_id)
    if status_filter and status_filter != "all":
        q = q.where(Horse.status == status_filter)
    result = await db.execute(q)
    horses = result.scalars().all()
    return [_horse_to_dict(h) for h in horses]


async def get_horse_detail(db: AsyncSession, horse_id, stable_id):
    result = await db.execute(
        select(Horse)
        .options(selectinload(Horse.bloodline), selectinload(Horse.feed_plans))
        .where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = result.scalar_one_or_none()
    if not horse:
        return None

    detail = _horse_to_dict(horse)

    # Add detail-only fields
    detail["ideal_weight"] = float(horse.ideal_weight)
    detail["gallop_tendency"] = horse.gallop_tendency
    detail["personality_primary"] = horse.personality_primary.value if horse.personality_revealed else None
    detail["personality_secondary"] = horse.personality_secondary.value if horse.personality_revealed else None
    detail["distance_optimum"] = horse.distance_optimum
    detail["surface_preference"] = horse.surface_preference.value if horse.surface_preference else None
    detail["training_intensity"] = horse.training_intensity.value if horse.training_intensity else None
    detail["training_locked_until"] = horse.training_locked_until
    detail["training_last_result"] = horse.training_last_result
    detail["shoe_durability"] = horse.shoe_durability
    detail["total_seconds"] = horse.total_seconds
    detail["total_thirds"] = horse.total_thirds
    detail["total_dq"] = horse.total_dq
    detail["bloodline_name"] = horse.bloodline.name if horse.bloodline else None
    detail["sire_name"] = None
    detail["dam_name"] = None
    detail["form_last_5"] = list(horse.form_history or [])[-5:]

    # Injury info
    detail["injury_type"] = horse.injury_type
    detail["injury_recovery_weeks"] = horse.injury_recovery_weeks or 0

    # Feed plan
    detail["feed_plan"] = [
        {"feed_type": fp.feed_type.value, "percentage": fp.percentage, "cost_per_week": fp.cost_per_week}
        for fp in (horse.feed_plans or [])
    ]

    # Compatibility with contracted drivers
    contracts_result = await db.execute(
        select(DriverContract)
        .options(selectinload(DriverContract.driver))
        .where(DriverContract.stable_id == stable_id, DriverContract.is_active == True)
    )
    contracts = contracts_result.scalars().all()

    from app.models.game_state import CompatibilityCache
    compat_list = []
    for c in contracts:
        d = c.driver
        # Check if paid compatibility exists in cache
        cache_result = await db.execute(
            select(CompatibilityCache).where(
                CompatibilityCache.horse_id == horse.id,
                CompatibilityCache.driver_id == d.id,
                CompatibilityCache.is_paid == True,
            )
        )
        cached = cache_result.scalar_one_or_none()

        if cached:
            compat_list.append({
                "driver_id": str(d.id), "driver_name": d.name,
                "score": cached.total_score, "label": _compat_label(cached.total_score),
                "is_checked": True,
            })
        else:
            compat_list.append({
                "driver_id": str(d.id), "driver_name": d.name,
                "score": None, "label": "?",
                "is_checked": False,
                "check_cost": 50_000,
            })
    detail["compatibility_with_drivers"] = compat_list

    return detail


def _horse_to_dict(h: Horse) -> dict:
    from app.services.game_init_service import SEASON_LENGTH_WEEKS
    age_years = (h.age_game_weeks or 0) // SEASON_LENGTH_WEEKS

    # Determine trend based on form history (actual direction, not just level)
    form_hist = list(h.form_history) if h.form_history else []
    if len(form_hist) >= 2:
        recent_avg = sum(form_hist[-3:]) / len(form_hist[-3:])
        older_avg = sum(form_hist[:-3] or form_hist[:1]) / len(form_hist[:-3] or form_hist[:1])
        diff = recent_avg - older_avg
        if diff > 3:
            trend = "up"
        elif diff < -3:
            trend = "down"
        else:
            trend = "stable"
    else:
        # Fallback: base on current form level
        if h.form > 60:
            trend = "up"
        elif h.form < 40:
            trend = "down"
        else:
            trend = "stable"

    # Total skill rating (1-20 scale, like Xpert Eleven)
    avg_stat = (h.speed + h.endurance + h.mentality + h.start_ability +
                h.sprint_strength + h.balance + h.strength) / 7
    total_skill = max(1, min(20, round(avg_stat / 5)))

    return {
        "id": str(h.id),
        "name": h.name,
        "gender": h.gender.value,
        "age_years": age_years,
        "status": h.status.value,
        "total_skill": total_skill,
        "speed": h.speed,
        "endurance": h.endurance,
        "mentality": h.mentality,
        "start_ability": h.start_ability,
        "sprint_strength": h.sprint_strength,
        "balance": h.balance,
        "strength": h.strength,
        "condition": h.condition,
        "energy": h.energy,
        "health": h.health,
        "form": h.form,
        "fatigue": h.fatigue,
        "mood": h.mood,
        "current_weight": float(h.current_weight),
        "total_starts": h.total_starts,
        "total_wins": h.total_wins,
        "total_earnings": h.total_earnings,
        "best_km_time_display": h.best_km_time_display,
        "current_training": h.current_training.value if h.current_training else None,
        "current_shoe": h.current_shoe.value if h.current_shoe else "normal_steel",
        "trend": trend,
        "form_history": form_hist[-10:],  # Last 10 for sparklines
        "injury_type": h.injury_type,
        "injury_recovery_weeks": h.injury_recovery_weeks or 0,
    }


def _horse_to_engine_stats(h: Horse) -> HorseStats:
    return HorseStats(
        id=str(h.id), name=h.name,
        speed=h.speed, endurance=h.endurance, mentality=h.mentality,
        start_ability=h.start_ability, sprint_strength=h.sprint_strength,
        balance=h.balance, strength=h.strength,
        condition=h.condition, energy_level=h.energy,
        health=h.health, form=h.form, fatigue=h.fatigue,
        current_weight=float(h.current_weight),
        ideal_weight=float(h.ideal_weight),
        mood=h.mood, gallop_tendency=h.gallop_tendency,
        surface_preference=h.surface_preference.value if h.surface_preference else None,
        weather_sensitivity=h.weather_sensitivity,
        distance_optimum=h.distance_optimum,
        racing_instinct=h.racing_instinct,
        personality_primary=h.personality_primary.value,
        personality_secondary=h.personality_secondary.value,
        special_traits=h.special_traits if hasattr(h, 'special_traits') and h.special_traits else [],
        is_npc=h.is_npc,
    )


def _driver_to_engine_stats(d: Driver) -> DriverStats:
    return DriverStats(
        id=str(d.id), name=d.name,
        skill=d.skill, start_skill=d.start_skill,
        tactical_ability=d.tactical_ability,
        sprint_timing=d.sprint_timing,
        gallop_handling=d.gallop_handling,
        experience=d.experience, composure=d.composure,
        driving_style=d.driving_style.value,
    )


def _compat_label(score: int) -> str:
    if score >= 86:
        return "Perfekt"
    elif score >= 71:
        return "Utmarkt"
    elif score >= 51:
        return "Bra"
    elif score >= 31:
        return "Okej"
    else:
        return "Dalig"


async def change_shoe(db: AsyncSession, horse_id, stable_id, shoe_type: str):
    """Change horse's shoe type. Costs money based on shoe quality."""
    from app.services import finance_service
    result = await db.execute(select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id))
    horse = result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte"}

    SHOE_COSTS = {
        "barefoot": 0, "light_aluminum": 50000, "normal_steel": 30000,
        "heavy_steel": 40000, "studs": 60000, "grip": 55000, "balance": 70000,
    }
    cost = SHOE_COSTS.get(shoe_type, 30000)

    try:
        shoe_enum = ShoeType(shoe_type)
    except ValueError:
        return {"error": f"Ogiltig skotyp: {shoe_type}"}

    horse.current_shoe = shoe_enum
    horse.shoe_durability = 6

    if cost > 0:
        await finance_service.record_transaction(
            db, stable_id, -cost, "shoeing",
            f"Skoning: {shoe_type} for {horse.name}", 1,
        )

    await db.flush()
    return {"success": True, "shoe": shoe_type, "cost": cost}


async def change_training(db: AsyncSession, horse_id, stable_id, program: str, intensity: str = "normal"):
    """Change horse's training program and intensity.
    Locks training for 2 game days so results can be observed.
    """
    from app.models.enums import TrainingProgram, TrainingIntensity
    from app.models.game_state import GameState
    from app.services.game_init_service import calculate_game_time

    result = await db.execute(select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id))
    horse = result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte"}

    try:
        prog_enum = TrainingProgram(program)
        int_enum = TrainingIntensity(intensity)
    except ValueError:
        return {"error": "Ogiltigt träningsprogram eller intensitet"}

    # Check if training is locked
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    current_total_day = 1
    if gs:
        gt = calculate_game_time(gs.real_week_start)
        current_total_day = gt["total_game_days"]

    if horse.training_locked_until and horse.training_locked_until > current_total_day:
        days_left = horse.training_locked_until - current_total_day
        return {"error": f"Hästen tränar fortfarande. {days_left} dag(ar) kvar."}

    # Set training and lock for 2 days (unless switching to REST)
    horse.current_training = prog_enum
    horse.training_intensity = int_enum
    horse.training_last_result = None  # Clear old result

    if prog_enum.value != "rest":
        horse.training_locked_until = current_total_day + 2
    else:
        horse.training_locked_until = None

    await db.flush()
    return {
        "success": True,
        "training": program,
        "intensity": intensity,
        "locked_until": horse.training_locked_until,
    }


async def update_feed_plan(db: AsyncSession, horse_id, stable_id, feeds: list[dict]):
    """Update horse's feed plan. feeds = [{"feed_type": str, "percentage": int}]"""
    from app.models.enums import FeedType
    result = await db.execute(select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id))
    horse = result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte"}

    total_pct = sum(f["percentage"] for f in feeds)
    if total_pct != 100:
        return {"error": f"Foderprocent måste vara 100%, är {total_pct}%"}

    # Remove old feed plans
    old_feeds = await db.execute(select(FeedPlan).where(FeedPlan.horse_id == horse_id))
    for fp in old_feeds.scalars().all():
        await db.delete(fp)

    FEED_COSTS_PER_PCT = {
        "hay_standard": 300, "hay_premium": 450, "hay_elite": 700,
        "oats": 300, "concentrate_standard": 400, "concentrate_premium": 600,
        "carrots": 100, "apples": 120, "electrolytes": 800,
        "joint_supplement": 1200, "biotin": 900, "mineral_mix": 300, "brewers_grain": 200,
    }

    new_plans = []
    for f in feeds:
        try:
            ft = FeedType(f["feed_type"])
        except ValueError:
            return {"error": f"Ogiltig fodertyp: {f['feed_type']}"}
        cost = FEED_COSTS_PER_PCT.get(f["feed_type"], 300) * f["percentage"]
        plan = FeedPlan(horse_id=horse_id, feed_type=ft, percentage=f["percentage"], cost_per_week=cost)
        db.add(plan)
        new_plans.append({"feed_type": f["feed_type"], "percentage": f["percentage"], "cost_per_week": cost})

    await db.flush()
    return {"success": True, "feed_plan": new_plans}
