"""TravManager — Post-Race Progression & Recovery Service

Handles:
- Energy/fatigue recovery between race days
- Stat growth after racing (bounded by potential)
- Age-based development (Xperteleven-style: younger = faster growth)
- Weekly form volatility (personality-driven form dips)
- Form/mood adjustments
"""
import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.enums import PersonalityType, TrainingProgram

logger = logging.getLogger(__name__)

MAX_FORM_HISTORY = 20  # Keep last 20 form snapshots


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


async def apply_post_race_progression(
    db: AsyncSession,
    horse_id,
    finish_position: int,
    field_size: int,
):
    """Apply stat growth based on racing experience.
    Uses Xperteleven-style age-based development:
    - Young horses (2-3yo) develop faster with bigger stat jumps
    - Older horses (8+) barely improve
    Personality also affects growth rate.
    """
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return

    # Seeded RNG for deterministic growth
    seed_val = int(str(horse_id).replace("-", "")[:8], 16) + horse.total_starts
    rng = random.Random(seed_val)

    # Age-based growth multiplier (Xperteleven style)
    age_years = horse.age_years or 4
    age_multiplier = _get_age_growth_multiplier(age_years)

    # Personality modifier
    personality_mod = _get_personality_modifier(
        horse.personality_primary, finish_position
    )

    # Base growth chance based on placement
    if finish_position <= 3:
        base_chance = 0.40
    elif finish_position <= 6:
        base_chance = 0.25
    else:
        base_chance = 0.10

    # Combined growth chance
    growth_chance = base_chance * age_multiplier * personality_mod

    # Form update
    if finish_position == 1:
        horse.form = min(100, horse.form + rng.randint(5, 12))
    elif finish_position <= 3:
        horse.form = min(100, horse.form + rng.randint(2, 6))
    elif finish_position > max(1, field_size - 2):
        horse.form = max(0, horse.form - rng.randint(2, 8))

    # Record form snapshot after race
    _record_form(horse)

    # Stat growth with age-based jumps
    stat_pairs = [
        ("speed", "potential_speed"),
        ("endurance", "potential_endurance"),
        ("mentality", "potential_mentality"),
        ("start_ability", "potential_start"),
        ("sprint_strength", "potential_sprint"),
        ("balance", "potential_balance"),
        ("strength", "potential_strength"),
    ]

    # Bigger stat jumps for young horses
    max_gain = 3 if age_years <= 4 else 2 if age_years <= 7 else 1

    for stat, potential in stat_pairs:
        current = getattr(horse, stat)
        cap = getattr(horse, potential)
        if current < cap and rng.random() < growth_chance * 0.3:
            gain = rng.randint(1, max_gain)
            gain = min(gain, cap - current)
            if gain > 0:
                setattr(horse, stat, current + gain)

    # Racing instinct grows with experience (hidden stat)
    if rng.random() < 0.15 * age_multiplier:
        horse.racing_instinct = min(100, horse.racing_instinct + 1)

    # Gallop tendency decreases with experience (horse learns)
    if horse.total_starts > 10 and rng.random() < 0.10:
        horse.gallop_tendency = max(3, horse.gallop_tendency - 1)

    await db.flush()
