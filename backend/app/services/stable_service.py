"""TravManager — Stable Service"""
import random
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.auth import hash_password
from app.core.config import settings
from app.models.user import User
from app.models.stable import Stable
from app.models.horse import Horse, Bloodline
from app.models.driver import Driver, DriverContract
from app.models.facility import Facility, FeedPlan
from app.models.enums import (
    HorseGender, HorseStatus, PersonalityType, DrivingStyle,
    ContractType, FacilityType, ShoeType, TrainingProgram,
    TrainingIntensity, FeedType,
)

from app.data.starter_horses import STARTER_HORSES

GENDER_MAP_STARTER = {
    "stallion": HorseGender.STALLION,
    "mare": HorseGender.MARE,
    "gelding": HorseGender.GELDING,
}
PERSONALITIES = list(PersonalityType)
GENDERS = [HorseGender.STALLION, HorseGender.MARE, HorseGender.GELDING]


async def create_new_player(db: AsyncSession, username: str, email: str, password: str, stable_name: str):
    """Create user + stable + 3 starter horses + 1 driver + basic facilities."""
    # Create user
    user = User(
        username=username, email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    await db.flush()

    # Create stable
    stable = Stable(
        user_id=user.id, name=stable_name,
        balance=settings.STARTING_BALANCE,
    )
    db.add(stable)
    await db.flush()

    # Get bloodlines from DB
    bl_result = await db.execute(select(Bloodline))
    bloodlines = bl_result.scalars().all()
    bl_ids = [b.id for b in bloodlines] if bloodlines else []

    # Create 3 starter horses from real horse bank
    rng = random.Random(str(user.id))
    chosen = rng.sample(STARTER_HORSES, 3)
    for name, gender_str, age_years in chosen:
        # Randomize stats 40-65
        base = lambda: rng.randint(40, 65)
        pot = lambda curr: min(99, curr + rng.randint(15, 35))

        spd, end, ment = base(), base(), base()
        sta, spr, bal, stg = base(), base(), base(), base()

        age_weeks = age_years * 16  # 1 year = 16 game weeks

        horse = Horse(
            stable_id=stable.id, name=name,
            gender=GENDER_MAP_STARTER.get(gender_str, HorseGender.GELDING),
            birth_game_week=max(1, 1 - age_weeks),
            age_game_weeks=age_weeks,
            status=HorseStatus.READY,
            speed=spd, endurance=end, mentality=ment,
            start_ability=sta, sprint_strength=spr, balance=bal, strength=stg,
            potential_speed=pot(spd), potential_endurance=pot(end),
            potential_mentality=pot(ment), potential_start=pot(sta),
            potential_sprint=pot(spr), potential_balance=pot(bal),
            potential_strength=pot(stg),
            condition=rng.randint(75, 95),
            energy=rng.randint(85, 100),
            health=rng.randint(80, 95),
            current_weight=round(rng.uniform(450, 500), 1),
            ideal_weight=round(rng.uniform(460, 490), 1),
            form=rng.randint(40, 65),
            mood=rng.randint(60, 85),
            gallop_tendency=rng.randint(8, 25),
            distance_optimum=rng.choice([1640, 2140, 2140, 2140, 2640]),
            racing_instinct=rng.randint(30, 70),
            personality_primary=rng.choice(PERSONALITIES),
            personality_secondary=rng.choice(PERSONALITIES),
            personality_revealed=True,  # Own horses are revealed
            bloodline_id=rng.choice(bl_ids) if bl_ids else None,
            current_training=TrainingProgram.REST,
            training_intensity=TrainingIntensity.NORMAL,
            current_shoe=ShoeType.NORMAL_STEEL,
            shoe_durability=6,
        )
        db.add(horse)

        # Default feed plan for each horse
        await db.flush()
        feeds = [
            FeedPlan(horse_id=horse.id, feed_type=FeedType.HAY_PREMIUM, percentage=55, cost_per_week=24750),
            FeedPlan(horse_id=horse.id, feed_type=FeedType.OATS, percentage=20, cost_per_week=6000),
            FeedPlan(horse_id=horse.id, feed_type=FeedType.CONCENTRATE_STANDARD, percentage=15, cost_per_week=6000),
            FeedPlan(horse_id=horse.id, feed_type=FeedType.CARROTS, percentage=5, cost_per_week=500),
            FeedPlan(horse_id=horse.id, feed_type=FeedType.MINERAL_MIX, percentage=5, cost_per_week=1500),
        ]
        for f in feeds:
            db.add(f)

    # Create 1 starter driver (apprentice)
    driver = Driver(
        name=f"{stable_name}s Kusk",
        skill=rng.randint(40, 55),
        start_skill=rng.randint(38, 52),
        tactical_ability=rng.randint(40, 55),
        sprint_timing=rng.randint(35, 50),
        gallop_handling=rng.randint(40, 55),
        experience=rng.randint(20, 35),
        composure=rng.randint(40, 55),
        driving_style=rng.choice(list(DrivingStyle)),
        base_salary=150000,
        guest_fee=100000,
        popularity=rng.randint(20, 40),
    )
    db.add(driver)
    await db.flush()

    contract = DriverContract(
        stable_id=stable.id, driver_id=driver.id,
        contract_type=ContractType.APPRENTICE,
        salary_per_week=150000,
        starts_game_week=1, ends_game_week=32,
        is_active=True,
    )
    db.add(contract)

    # Basic facility
    facility = Facility(
        stable_id=stable.id,
        facility_type=FacilityType.STABLE_BOX,
        level=1, build_cost=0,
        maintenance_cost_per_week=25000,
    )
    db.add(facility)

    await db.flush()

    return {
        "user_id": str(user.id),
        "stable_id": str(stable.id),
        "stable_name": stable.name,
    }


async def get_stable_summary(db: AsyncSession, stable):
    """Return stable summary for dashboard."""
    from app.models.horse import Horse
    from app.models.race import RaceSession, Race, RaceTrack

    # Count horses
    horse_result = await db.execute(
        select(sa_func.count(Horse.id)).where(Horse.stable_id == stable.id)
    )
    horse_count = horse_result.scalar() or 0

    ready_result = await db.execute(
        select(sa_func.count(Horse.id)).where(
            Horse.stable_id == stable.id,
            Horse.status == HorseStatus.READY,
        )
    )
    horses_ready = ready_result.scalar() or 0

    # Get home track name
    home_track_name = None
    if stable.home_track_id:
        track_result = await db.execute(
            select(RaceTrack).where(RaceTrack.id == stable.home_track_id)
        )
        track = track_result.scalar_one_or_none()
        if track:
            home_track_name = track.name

    return {
        "id": str(stable.id),
        "name": stable.name,
        "reputation": stable.reputation,
        "fan_count": stable.fan_count,
        "balance": stable.balance,
        "division": None,
        "horse_count": horse_count,
        "horses_ready": horses_ready,
        "max_horses": stable.max_horses or 3,
        "box_upgrade_level": stable.box_upgrade_level or 0,
        "last_sponsor_collection_week": stable.last_sponsor_collection_week or 0,
        "home_track_name": home_track_name,
        "next_race": None,
        "weekly_income": 0,
        "weekly_expenses": 0,
    }


async def get_morning_report(db: AsyncSession, stable):
    """Generate morning report."""
    from app.models.horse import Horse

    horses_result = await db.execute(
        select(Horse).where(Horse.stable_id == stable.id)
    )
    horses = horses_result.scalars().all()

    statuses = []
    for h in horses:
        alerts = []
        if h.fatigue > 60:
            alerts.append("Hog trotthet")
        if h.health < 70:
            alerts.append("Lag halsa")
        if h.mood < 40:
            alerts.append("Daligt humor")
        if float(h.current_weight) > float(h.ideal_weight) * 1.05:
            alerts.append(f"Overvikt +{float(h.current_weight) - float(h.ideal_weight):.0f} kg")

        statuses.append({
            "id": str(h.id), "name": h.name,
            "status": h.status.value,
            "alerts": alerts, "mood": h.mood,
        })

    return {
        "game_week": 1,
        "game_day": 1,
        "horse_statuses": statuses,
        "todos": [],
        "balance": stable.balance,
        "balance_change_24h": 0,
        "events": [],
    }


    # Training program → stat effect mapping
TRAINING_EFFECTS = {
    "interval": {"speed": (1, 3), "endurance": (1, 2)},
    "long_distance": {"endurance": (2, 4), "strength": (0, 2)},
    "start_training": {"start_ability": (2, 4)},
    "sprint_training": {"sprint_strength": (2, 4), "speed": (0, 2)},
    "mental_training": {"mentality": (2, 4)},
    "strength_training": {"strength": (2, 4), "endurance": (0, 2)},
    "balance_training": {"balance": (2, 4)},
    "swim_training": {"endurance": (1, 3), "strength": (1, 2), "balance": (0, 2)},
    "track_training": {"speed": (1, 3), "mentality": (0, 2), "start_ability": (0, 1)},
}


async def daily_checkup(db: AsyncSession, stable):
    """Process daily checkup: update horse status, generate events, apply training results."""
    from app.models.horse import Horse
    from app.models.game_state import GameState
    from app.services.game_init_service import calculate_game_time
    from app.services import event_service
    import random

    # Get current total game day
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    current_total_day = 1
    if gs:
        gt = calculate_game_time(gs.real_week_start)
        current_total_day = gt["total_game_days"]

    horses_result = await db.execute(select(Horse).where(Horse.stable_id == stable.id))
    horses = horses_result.scalars().all()

    rng = random.Random()
    events = []

    for h in horses:
        # ── Training completion check ──
        if (
            h.training_locked_until
            and h.training_locked_until <= current_total_day
            and h.current_training
            and h.current_training.value != "rest"
        ):
            program = h.current_training.value
            intensity = h.training_intensity.value if h.training_intensity else "normal"
            effects = TRAINING_EFFECTS.get(program, {})

            intensity_mult = {"light": 0.6, "normal": 1.0, "hard": 1.4}.get(intensity, 1.0)
            stat_changes = {}

            for stat, (lo, hi) in effects.items():
                current_val = getattr(h, stat, 0)
                potential_key = f"potential_{stat}" if stat != "sprint_strength" else "potential_sprint"
                if stat == "start_ability":
                    potential_key = "potential_start"
                potential_val = getattr(h, potential_key, 99)

                # Gain scales with gap to potential and intensity
                gap = max(0, potential_val - current_val)
                if gap <= 0:
                    stat_changes[stat] = 0
                    continue

                base_gain = rng.randint(lo, hi)
                adjusted = round(base_gain * intensity_mult * min(1.0, gap / 30))
                adjusted = max(0, min(adjusted, gap))  # Can't exceed potential
                if adjusted > 0:
                    setattr(h, stat, current_val + adjusted)
                    stat_changes[stat] = adjusted

            # Unlock training and store result
            h.training_locked_until = None
            h.training_last_result = stat_changes

            if any(v > 0 for v in stat_changes.values()):
                detail_parts = [f"{_stat_label(k)} +{v}" for k, v in stat_changes.items() if v > 0]
                events.append({
                    "type": "training_complete",
                    "horse": h.name,
                    "detail": ", ".join(detail_parts),
                    "stat_changes": stat_changes,
                })
            else:
                events.append({
                    "type": "training_complete",
                    "horse": h.name,
                    "detail": "Ingen förbättring",
                    "stat_changes": {},
                })

        # ── Energy recovery based on training ──
        if h.current_training and h.current_training.value == "rest":
            h.energy = min(100, h.energy + rng.randint(5, 12))
            h.fatigue = max(0, h.fatigue - rng.randint(5, 10))
        else:
            h.energy = max(0, h.energy - rng.randint(2, 8))
            h.fatigue = min(100, h.fatigue + rng.randint(1, 5))

        # Mood changes
        mood_delta = rng.randint(-3, 5)
        h.mood = max(0, min(100, h.mood + mood_delta))

        # Condition shift
        if h.current_training and h.current_training.value != "rest":
            h.condition = min(100, h.condition + rng.randint(0, 2))

        # Random injury chance (1%)
        if rng.random() < 0.01 and h.status.value == "ready":
            h.status = HorseStatus.INJURED
            h.injury_type = rng.choice(["Senskada", "Halthet", "Muskelspänning"])
            h.injury_recovery_weeks = rng.randint(2, 6)
            evt = await event_service.create_event(
                db, stable.id, "injury", f"{h.name} skadad",
                f"{h.name} har drabbats av {h.injury_type}. Beräknad återhämtning: {h.injury_recovery_weeks} veckor.",
                1, requires_action=True,
            )
            events.append({"type": "injury", "horse": h.name, "detail": h.injury_type})

        # Check fatigue -> fatigued status
        if h.fatigue > 70 and h.status.value == "ready":
            h.status = HorseStatus.FATIGUED
            events.append({"type": "fatigue", "horse": h.name, "detail": f"Trötthet: {h.fatigue}. Behöver vila."})
        elif h.fatigue < 30 and h.status.value == "fatigued":
            h.status = HorseStatus.READY
            events.append({"type": "recovered", "horse": h.name, "detail": "Återhämtad och redo att tävla igen!"})

        # Energy warning
        if h.energy < 30 and h.status.value == "ready":
            events.append({
                "type": "energy_warning", "horse": h.name,
                "detail": f"Låg energi ({h.energy}%). Överväg att byta till vila."
            })

        # Mood warning/celebration
        if h.mood >= 90:
            events.append({"type": "mood_high", "horse": h.name, "detail": f"Strålande humör ({h.mood})! Presterar troligen bättre."})
        elif h.mood <= 25:
            events.append({"type": "mood_low", "horse": h.name, "detail": f"Dåligt humör ({h.mood}). Kan påverka prestationen negativt."})

    await db.flush()
    return {"processed": len(horses), "events": events}


def _stat_label(stat: str) -> str:
    """Swedish label for a stat name."""
    labels = {
        "speed": "Fart",
        "endurance": "Uthållighet",
        "mentality": "Mentalitet",
        "start_ability": "Startförmåga",
        "sprint_strength": "Spurt",
        "balance": "Balans",
        "strength": "Styrka",
    }
    return labels.get(stat, stat)


async def create_press_release(db: AsyncSession, stable, tone: str, content: str):
    """Create a press release to boost reputation. Max 1 per game week."""
    from app.models.enums import PressTone
    from app.models.event import PressRelease
    from app.models.game_state import GameState
    from app.services import finance_service
    import random

    # Get current game week
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    current_week = gs.current_game_week if gs else 1

    # Check if already published this week
    if stable.last_press_release_week >= current_week:
        return {"error": "Du kan bara publicera ett pressmeddelande per vecka"}

    try:
        tone_enum = PressTone(tone)
    except ValueError:
        return {"error": "Ogiltig ton. Välj humble, confident eller provocative."}

    rng = random.Random()

    # PR points based on tone and randomness
    base_points = {"humble": 3, "confident": 5, "provocative": 8}
    risk = {"humble": 0, "confident": 0.1, "provocative": 0.3}

    points = base_points[tone]

    # Provocative can backfire
    if rng.random() < risk[tone]:
        points = -points
        reputation_change = -rng.randint(1, 3)
    else:
        reputation_change = rng.randint(1, points)

    # Income from PR
    income = max(0, points * 10000)

    pr = PressRelease(
        stable_id=stable.id, tone=tone_enum, content=content,
        pr_points=points, income_generated=income,
        game_week=current_week, game_day=1,
    )
    db.add(pr)

    # Update reputation and track last PR week
    stable.reputation = max(0, min(100, stable.reputation + reputation_change))
    stable.fan_count = max(0, stable.fan_count + points * 10)
    stable.last_press_release_week = current_week

    if income > 0:
        await finance_service.record_transaction(
            db, stable.id, income, "sponsor_income",
            f"Pressmeddelande ({tone})", current_week,
        )

    await db.flush()

    return {
        "success": True,
        "pr_points": points,
        "reputation_change": reputation_change,
        "new_reputation": stable.reputation,
        "income": income,
        "backfired": points < 0,
    }
