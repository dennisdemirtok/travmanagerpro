"""TravManager — Post-Race Progression & Recovery Service

Handles:
- Energy/fatigue recovery between race days
- Stat growth after racing (bounded by potential)
- Age-based development (Xperteleven-style: younger = faster growth)
- Weekly form volatility (personality-driven form dips)
- Form/mood adjustments
- Post-race injuries & "känningar" (niggles)
- Dynamic fatigue/energy based on race conditions
"""
import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.enums import PersonalityType, TrainingProgram

logger = logging.getLogger(__name__)

MAX_FORM_HISTORY = 20  # Keep last 20 form snapshots

# ============================================================
# INJURY DEFINITIONS
# ============================================================

INJURY_TYPES = {
    # name: (min_recovery_weeks, max_recovery_weeks, severity_label)
    "senskada": (3, 8, "allvarlig"),          # Tendon injury
    "hovböld": (1, 3, "lindrig"),              # Hoof abscess
    "muskelknut": (1, 2, "lindrig"),           # Muscle knot / niggle
    "hälta": (2, 5, "måttlig"),                # Lameness
    "ryggproblem": (2, 6, "måttlig"),          # Back issue
    "ledproblem": (3, 7, "allvarlig"),         # Joint issue
    "muskelbristning": (4, 10, "allvarlig"),   # Muscle tear
    "stressfraktur": (6, 12, "kritisk"),       # Stress fracture
}

# "Känningar" = minor niggles that don't sideline but affect performance
KANNINGAR_TYPES = [
    "öm hovled",
    "stel nacke",
    "trött muskulatur",
    "liten ömhet i bakben",
    "spänning i ryggen",
    "lätt hälta efter lopp",
]


def _record_form(horse: Horse):
    """Append current form to the horse's form_history (max 20 entries)."""
    history = list(horse.form_history) if horse.form_history else []
    history.append(horse.form)
    if len(history) > MAX_FORM_HISTORY:
        history = history[-MAX_FORM_HISTORY:]
    horse.form_history = history


def _get_age_growth_multiplier(age_years: int) -> float:
    """Xperteleven-style age development: younger horses develop faster."""
    if age_years <= 2:
        return 3.0   # Huge jumps possible
    elif age_years <= 3:
        return 2.5
    elif age_years <= 4:
        return 2.0
    elif age_years <= 5:
        return 1.5
    elif age_years <= 7:
        return 1.0   # Standard
    elif age_years <= 10:
        return 0.5   # Slowing down
    else:
        return 0.1   # Near retirement


def _get_personality_modifier(personality: PersonalityType, finish_position: int = 99) -> float:
    """Personality affects growth rate."""
    if personality == PersonalityType.TRAINING_EAGER:
        return 1.5
    elif personality == PersonalityType.LAZY:
        return 0.6
    elif personality == PersonalityType.WINNER and finish_position <= 3:
        return 1.3
    elif personality == PersonalityType.STRONG_WILLED:
        return 1.1
    elif personality == PersonalityType.MOODY:
        return 0.8  # Inconsistent
    else:
        return 1.0


async def apply_recovery(db: AsyncSession, game_days_elapsed: int = 1):
    """Recover energy and reduce fatigue for all horses over elapsed game days.
    Called by the race ticker when game day advances, and during backlog seeding.
    """
    if game_days_elapsed <= 0:
        return

    # Cap to prevent huge jumps
    days = min(game_days_elapsed, 7)

    horses_result = await db.execute(select(Horse))
    horses = horses_result.scalars().all()

    for horse in horses:
        # Energy recovery: ~15 per game day
        base_recovery = 15 * days
        if horse.current_training == TrainingProgram.REST:
            base_recovery = int(base_recovery * 1.5)
        elif horse.current_training in (
            TrainingProgram.INTERVAL,
            TrainingProgram.SPRINT_TRAINING,
        ):
            base_recovery = int(base_recovery * 0.7)

        horse.energy = min(100, horse.energy + base_recovery)

        # Fatigue reduction: ~10 per game day
        fatigue_recovery = 10 * days
        if horse.current_training == TrainingProgram.REST:
            fatigue_recovery = int(fatigue_recovery * 1.5)

        horse.fatigue = max(0, horse.fatigue - fatigue_recovery)

        # Mood drifts toward 70 (neutral)
        for _ in range(days):
            if horse.mood < 70:
                horse.mood = min(70, horse.mood + 2)
            elif horse.mood > 70:
                horse.mood = max(70, horse.mood - 1)

    await db.flush()


async def apply_weekly_form_changes(db: AsyncSession, game_week: int):
    """Apply random weekly form volatility to all horses.
    Personality affects frequency and severity of form dips.
    Called once per game week by the ticker.
    """
    horses_result = await db.execute(select(Horse))
    horses = horses_result.scalars().all()

    rng = random.Random(game_week * 7919)  # Seeded for determinism
    form_changes = 0

    for horse in horses:
        # Base dip chance
        dip_chance = 0.15

        # Personality modifiers
        p = horse.personality_primary
        if p == PersonalityType.MOODY:
            dip_chance = 0.30
        elif p == PersonalityType.TRAINING_EAGER:
            dip_chance = 0.08
        elif p == PersonalityType.LAZY:
            dip_chance = 0.25
        elif p == PersonalityType.FOOD_LOVER:
            dip_chance = 0.20

        # Energy-based modifier
        if horse.energy < 40:
            dip_chance = min(0.50, dip_chance + 0.25)

        if rng.random() < dip_chance:
            if p == PersonalityType.MOODY:
                # Moody horses can swing either way
                if rng.random() < 0.3:
                    form_change = rng.randint(5, 10)  # Surprise boost
                else:
                    form_change = rng.randint(-20, -8)  # Bigger dips
            else:
                form_change = rng.randint(-15, -5)

            old_form = horse.form
            horse.form = max(0, min(100, horse.form + form_change))
            if horse.form != old_form:
                form_changes += 1
                _record_form(horse)

    await db.flush()
    if form_changes > 0:
        logger.info(f"Weekly form changes: {form_changes} horses affected in week {game_week}")


async def apply_post_race_effects(
    db: AsyncSession,
    horse_id,
    finish_position: int,
    field_size: int,
    race_data: dict = None,
):
    """Apply ALL post-race effects: fatigue, energy, form, injuries, stat growth.

    race_data contains details from the simulation:
    - distance: int (race distance in meters)
    - energy_at_finish: int (0-100)
    - gallop_incidents: int
    - sulky_type: str
    - warmup_intensity: str
    - weather: str
    - surface: str
    - tempo: str
    - positioning: str
    - was_disqualified: bool
    - driver_rating: int
    - km_time_seconds: float
    """
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {}

    rd = race_data or {}
    events = []  # Post-race event messages for the player

    # Seeded RNG for deterministic outcomes
    seed_val = int(str(horse_id).replace("-", "")[:8], 16) + horse.total_starts
    rng = random.Random(seed_val)

    age_years = horse.age_years or 4

    # ============================================================
    # 1. DYNAMIC FATIGUE — based on race effort, not flat
    # ============================================================
    distance = rd.get("distance", 2140)
    energy_at_finish = rd.get("energy_at_finish", 50)
    gallop_incidents = rd.get("gallop_incidents", 0)
    sulky_type = rd.get("sulky_type", "european")
    warmup = rd.get("warmup_intensity", "normal")
    tempo = rd.get("tempo", "balanced")
    positioning = rd.get("positioning", "second")

    # Base fatigue from distance (longer = more tiring)
    base_fatigue = 20 + (distance / 1000) * 8  # 20-37 for 1600-2140m

    # Effort modifiers
    if tempo == "offensive":
        base_fatigue *= 1.25
    elif tempo == "cautious":
        base_fatigue *= 0.85

    if positioning in ("lead", "outside", "trailing"):
        base_fatigue *= 1.15
    elif positioning == "back":
        base_fatigue *= 0.90

    if sulky_type == "racing":
        base_fatigue *= 1.20
    elif sulky_type == "american":
        base_fatigue *= 1.08

    if warmup == "intense":
        base_fatigue *= 1.10
    elif warmup == "light":
        base_fatigue *= 0.92

    # Gallop incidents add fatigue
    base_fatigue += gallop_incidents * 8

    # Energy depletion adds fatigue (ran on empty = exhausting)
    if energy_at_finish < 10:
        base_fatigue *= 1.40
    elif energy_at_finish < 25:
        base_fatigue *= 1.20
    elif energy_at_finish < 40:
        base_fatigue *= 1.10

    # Age modifier (older horses tire more)
    if age_years >= 10:
        base_fatigue *= 1.25
    elif age_years >= 8:
        base_fatigue *= 1.10

    # Endurance stat reduces fatigue
    endurance_factor = 1.0 - (horse.endurance / 100) * 0.20  # Top endurance = 20% less fatigue
    base_fatigue *= endurance_factor

    fatigue_added = int(min(60, max(15, base_fatigue)))
    horse.fatigue = min(100, horse.fatigue + fatigue_added)

    # ============================================================
    # 2. DYNAMIC ENERGY LOSS
    # ============================================================
    base_energy_loss = 25 + (distance / 1000) * 10

    if tempo == "offensive":
        base_energy_loss *= 1.20
    elif tempo == "cautious":
        base_energy_loss *= 0.85

    if energy_at_finish < 15:
        base_energy_loss *= 1.30  # Ran completely empty

    energy_lost = int(min(70, max(20, base_energy_loss)))
    horse.energy = max(0, horse.energy - energy_lost)

    # ============================================================
    # 3. FORM CHANGES — based on HOW the race went
    # ============================================================
    form_change = 0

    # Position-based (base)
    if finish_position == 1:
        form_change += rng.randint(5, 12)
    elif finish_position == 2:
        form_change += rng.randint(3, 7)
    elif finish_position == 3:
        form_change += rng.randint(1, 5)
    elif finish_position <= field_size // 2:
        form_change += rng.randint(-2, 2)
    elif finish_position > max(1, field_size - 2):
        form_change -= rng.randint(3, 10)

    # Effort-based adjustments
    if energy_at_finish < 10:
        # Horse was pushed to the limit — form can swing either way
        if finish_position <= 3:
            form_change += rng.randint(2, 5)  # Gutsy performance = form boost
            events.append("Hästen gav allt och vann på vilja — formen stiger!")
        else:
            form_change -= rng.randint(2, 5)  # Pushed too hard for nothing
            events.append("Hästen kördes slut utan resultat — formen sjunker")

    # Gallop incidents hurt form
    if gallop_incidents >= 2:
        form_change -= rng.randint(3, 8)
        events.append("Flera galoppincidenter påverkar formen negativt")
    elif gallop_incidents == 1:
        form_change -= rng.randint(1, 3)

    # DQ is devastating for form
    was_dq = rd.get("was_disqualified", False)
    if was_dq:
        form_change = -rng.randint(8, 15)
        events.append("Diskvalificering — formen sjunker kraftigt")

    # Personality affects form recovery
    p = horse.personality_primary
    if p == PersonalityType.WINNER and finish_position > field_size // 2:
        form_change -= rng.randint(2, 5)  # Winner personality hates losing
    elif p == PersonalityType.WINNER and finish_position == 1:
        form_change += rng.randint(2, 4)  # Thrives on winning
    elif p == PersonalityType.MOODY:
        form_change += rng.randint(-4, 4)  # Unpredictable

    old_form = horse.form
    horse.form = max(0, min(100, horse.form + form_change))
    _record_form(horse)

    if horse.form > old_form + 3:
        events.append(f"Formen steg till {horse.form} (+{horse.form - old_form})")
    elif horse.form < old_form - 3:
        events.append(f"Formen sjönk till {horse.form} ({horse.form - old_form})")

    # ============================================================
    # 4. MOOD CHANGES
    # ============================================================
    if finish_position == 1:
        horse.mood = min(100, horse.mood + rng.randint(5, 10))
    elif finish_position <= 3:
        horse.mood = min(100, horse.mood + rng.randint(1, 5))
    elif finish_position > max(1, field_size - 2):
        horse.mood = max(20, horse.mood - rng.randint(2, 8))

    if was_dq:
        horse.mood = max(20, horse.mood - rng.randint(5, 12))

    # Whip usage affects mood
    whip = rd.get("whip_usage", "normal")
    if whip == "aggressive":
        horse.mood = max(20, horse.mood - rng.randint(3, 7))
        if horse.personality_primary == PersonalityType.SENSITIVE:
            horse.mood = max(20, horse.mood - rng.randint(3, 6))
            events.append("Hästen reagerade negativt på aggressiv piskföring")
    elif whip == "gentle":
        if horse.personality_primary == PersonalityType.SENSITIVE:
            horse.mood = min(100, horse.mood + rng.randint(1, 3))

    # ============================================================
    # 5. POST-RACE INJURY CHECK
    # ============================================================
    injury_result = _check_post_race_injury(horse, rd, rng)
    if injury_result:
        events.append(injury_result)

    # ============================================================
    # 6. SHOE WEAR
    # ============================================================
    horse.shoe_durability = max(0, horse.shoe_durability - 1)
    if horse.shoe_durability <= 1:
        events.append("Skorna börjar bli utslitna — överväg omskoning")

    # ============================================================
    # 7. STAT GROWTH (kept from original)
    # ============================================================
    _apply_stat_growth(horse, finish_position, field_size, age_years, rng)

    await db.flush()

    return {
        "fatigue_added": fatigue_added,
        "energy_lost": energy_lost,
        "form_change": horse.form - old_form,
        "new_form": horse.form,
        "events": events,
        "injury": injury_result if injury_result else None,
    }


def _check_post_race_injury(horse: Horse, race_data: dict, rng: random.Random) -> str | None:
    """Check for post-race injuries based on race events.
    Returns event description string or None.
    """
    # Don't double-injure
    if horse.injury_type:
        return None

    gallop_incidents = race_data.get("gallop_incidents", 0)
    energy_at_finish = race_data.get("energy_at_finish", 50)
    sulky_type = race_data.get("sulky_type", "european")
    distance = race_data.get("distance", 2140)
    was_dq = race_data.get("was_disqualified", False)
    age = horse.age_years or 4

    # Base injury chance
    base_chance = 0.02  # 2% base

    # Gallop incidents are the #1 cause
    base_chance += gallop_incidents * 0.06  # Each gallop = +6%

    # Energy depletion = pushed too hard
    if energy_at_finish < 5:
        base_chance += 0.08
    elif energy_at_finish < 15:
        base_chance += 0.04
    elif energy_at_finish < 25:
        base_chance += 0.02

    # Racing sulky = higher injury risk
    if sulky_type == "racing":
        base_chance += 0.04
    elif sulky_type == "american":
        base_chance += 0.01

    # Longer distances = more wear
    if distance >= 2600:
        base_chance += 0.03
    elif distance >= 2140:
        base_chance += 0.01

    # Age increases injury risk
    if age >= 10:
        base_chance += 0.06
    elif age >= 8:
        base_chance += 0.03
    elif age >= 6:
        base_chance += 0.01

    # DQ from gallop = high injury risk
    if was_dq:
        base_chance += 0.10

    # "glass_legs" trait
    traits = horse.special_traits or []
    if "glass_legs" in traits:
        base_chance *= 1.5

    # Health stat reduces risk
    health_factor = 1.0 - (horse.health / 100) * 0.4
    base_chance *= health_factor

    # Fatigue going in increases risk
    if horse.fatigue > 70:
        base_chance *= 1.3
    elif horse.fatigue > 50:
        base_chance *= 1.1

    # Cap at 35%
    base_chance = min(0.35, base_chance)

    if rng.random() < base_chance:
        # Determine severity based on contributing factors
        severity_score = gallop_incidents * 2 + (1 if energy_at_finish < 15 else 0) + (2 if was_dq else 0) + (1 if age >= 8 else 0)

        if severity_score >= 4:
            # Severe injury
            injury_pool = ["senskada", "ledproblem", "muskelbristning"]
            if rng.random() < 0.1:
                injury_pool.append("stressfraktur")
        elif severity_score >= 2:
            # Medium injury
            injury_pool = ["hälta", "ryggproblem", "senskada"]
        else:
            # Minor injury / niggle
            injury_pool = ["hovböld", "muskelknut"]

        injury = rng.choice(injury_pool)
        min_weeks, max_weeks, severity = INJURY_TYPES[injury]
        recovery = rng.randint(min_weeks, max_weeks)

        horse.injury_type = injury
        horse.injury_recovery_weeks = recovery
        horse.status = __import__("app.models.enums", fromlist=["HorseStatus"]).HorseStatus.INJURED

        return f"SKADA: {injury} ({severity}) — {recovery} veckors vila krävs"

    # Check for "känningar" (niggles) — more common, less severe
    kanningar_chance = base_chance * 2  # Twice as likely as real injury
    if rng.random() < kanningar_chance:
        niggle = rng.choice(KANNINGAR_TYPES)
        # Känningar reduce form and energy but don't sideline
        horse.form = max(0, horse.form - rng.randint(2, 5))
        horse.energy = max(0, horse.energy - rng.randint(5, 10))
        return f"Känning: {niggle} — hästen behöver extra omsorg"

    return None


def _apply_stat_growth(horse: Horse, finish_position: int, field_size: int, age_years: int, rng: random.Random):
    """Apply stat growth based on racing experience."""
    age_multiplier = _get_age_growth_multiplier(age_years)
    personality_mod = _get_personality_modifier(horse.personality_primary, finish_position)

    # Base growth chance based on placement
    if finish_position <= 3:
        base_chance = 0.40
    elif finish_position <= 6:
        base_chance = 0.25
    else:
        base_chance = 0.10

    growth_chance = base_chance * age_multiplier * personality_mod

    stat_pairs = [
        ("speed", "potential_speed"),
        ("endurance", "potential_endurance"),
        ("mentality", "potential_mentality"),
        ("start_ability", "potential_start"),
        ("sprint_strength", "potential_sprint"),
        ("balance", "potential_balance"),
        ("strength", "potential_strength"),
    ]

    max_gain = 3 if age_years <= 4 else 2 if age_years <= 7 else 1

    for stat, potential in stat_pairs:
        current = getattr(horse, stat)
        cap = getattr(horse, potential)
        if current < cap and rng.random() < growth_chance * 0.3:
            gain = rng.randint(1, max_gain)
            gain = min(gain, cap - current)
            if gain > 0:
                setattr(horse, stat, current + gain)

    # Racing instinct grows with experience
    if rng.random() < 0.15 * age_multiplier:
        horse.racing_instinct = min(100, horse.racing_instinct + 1)

    # Gallop tendency decreases with experience
    if horse.total_starts > 10 and rng.random() < 0.10:
        horse.gallop_tendency = max(3, horse.gallop_tendency - 1)


# Legacy alias for backward compatibility
async def apply_post_race_progression(
    db: AsyncSession,
    horse_id,
    finish_position: int,
    field_size: int,
):
    """Legacy wrapper — calls apply_post_race_effects with defaults."""
    return await apply_post_race_effects(db, horse_id, finish_position, field_size)
