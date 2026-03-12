"""TravManager — Training Service

Handles quick form training (instant boost) and professional training
(send horse away 1-2 weeks for targeted stat improvement).
"""
import random
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.stable import Stable
from app.models.breeding import ProfessionalTraining
from app.models.enums import HorseStatus
from app.services import finance_service

logger = logging.getLogger(__name__)

# Quick train costs 500,000 öre (5,000 kr)
QUICK_TRAIN_COST = 500_000

# Professional training costs per week
TRAINER_COSTS = {
    "standard": 300_000,   # 3,000 kr/week
    "advanced": 600_000,   # 6,000 kr/week
    "elite": 1_000_000,    # 10,000 kr/week
}

# Stat gains per trainer level (min, max)
TRAINER_GAINS = {
    "standard": (1, 3),
    "advanced": (2, 5),
    "elite": (3, 7),
}

# Training duration in weeks per level
TRAINER_DURATION = {
    "standard": 1,
    "advanced": 1,
    "elite": 2,
}

TRAINABLE_STATS = [
    "speed", "endurance", "mentality", "start_ability",
    "sprint_strength", "balance", "strength",
]


async def quick_train(
    db: AsyncSession, stable_id, horse_id, game_week: int
) -> dict:
    """Instant form training — costs 5,000 kr, boosts form by 8-20 points."""
    # Verify stable
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    # Verify horse
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen tillhör inte ditt stall"}
    if horse.status != HorseStatus.READY:
        return {"error": f"Hästen är inte redo (status: {horse.status.value})"}

    # Check balance
    if stable.balance < QUICK_TRAIN_COST:
        return {"error": f"Inte tillräckligt med pengar (behöver {QUICK_TRAIN_COST:,} öre)"}

    # Deduct cost
    await finance_service.record_transaction(
        db, stable_id, -QUICK_TRAIN_COST, "training",
        f"Formträning: {horse.name}", game_week,
    )

    # Apply form boost
    rng = random.Random(int(str(horse_id).replace("-", "")[:8], 16) + game_week)
    boost = rng.randint(8, 20)

    old_form = horse.form
    horse.form = min(100, horse.form + boost)
    actual_boost = horse.form - old_form

    # Small mood improvement
    horse.mood = min(100, horse.mood + rng.randint(2, 5))

    await db.flush()

    return {
        "success": True,
        "horse_name": horse.name,
        "form_boost": actual_boost,
        "new_form": horse.form,
        "cost": QUICK_TRAIN_COST,
    }


async def send_to_professional(
    db: AsyncSession, stable_id, horse_id, target_stat: str,
    trainer_level: str, game_week: int
) -> dict:
    """Send a horse to a professional trainer for 1-2 weeks."""
    # Validate target stat
    if target_stat not in TRAINABLE_STATS:
        return {"error": f"Ogiltigt mål: {target_stat}. Välj bland: {', '.join(TRAINABLE_STATS)}"}

    # Validate trainer level
    if trainer_level not in TRAINER_COSTS:
        return {"error": f"Ogiltig tränarnivå: {trainer_level}"}

    # Verify stable
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    # Verify horse
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen tillhör inte ditt stall"}
    if horse.status != HorseStatus.READY:
        return {"error": f"Hästen är inte redo (status: {horse.status.value})"}

    duration = TRAINER_DURATION[trainer_level]
    cost_per_week = TRAINER_COSTS[trainer_level]
    total_cost = cost_per_week * duration

    # Check balance
    if stable.balance < total_cost:
        return {"error": f"Inte tillräckligt med pengar (behöver {total_cost:,} öre)"}

    # Deduct cost upfront
    await finance_service.record_transaction(
        db, stable_id, -total_cost, "training",
        f"Proffstränare ({trainer_level}): {horse.name} - {target_stat}",
        game_week,
    )

    # Set horse status to training
    horse.status = HorseStatus.TRAINING

    # Create training log
    training = ProfessionalTraining(
        horse_id=horse_id,
        stable_id=stable_id,
        target_stat=target_stat,
        trainer_level=trainer_level,
        cost_per_week=cost_per_week,
        start_week=game_week,
        end_week=game_week + duration,
        completed=False,
    )
    db.add(training)
    await db.flush()

    return {
        "success": True,
        "horse_name": horse.name,
        "target_stat": target_stat,
        "trainer_level": trainer_level,
        "duration_weeks": duration,
        "total_cost": total_cost,
        "return_week": game_week + duration,
        "training_id": str(training.id),
    }


async def process_professional_training(db: AsyncSession, game_week: int) -> int:
    """Process completed professional trainings. Returns count completed."""
    trainings_result = await db.execute(
        select(ProfessionalTraining).where(
            ProfessionalTraining.completed == False,
            ProfessionalTraining.end_week <= game_week,
        )
    )
    trainings = trainings_result.scalars().all()
    completed_count = 0

    for training in trainings:
        horse_result = await db.execute(
            select(Horse).where(Horse.id == training.horse_id)
        )
        horse = horse_result.scalar_one_or_none()
        if not horse:
            training.completed = True
            continue

        # Calculate stat gain
        rng = random.Random(
            int(str(training.id).replace("-", "")[:8], 16) + game_week
        )
        min_gain, max_gain = TRAINER_GAINS[training.trainer_level]
        gain = rng.randint(min_gain, max_gain)

        # Check potential cap
        potential_map = {
            "speed": "potential_speed",
            "endurance": "potential_endurance",
            "mentality": "potential_mentality",
            "start_ability": "potential_start",
            "sprint_strength": "potential_sprint",
            "balance": "potential_balance",
            "strength": "potential_strength",
        }
        potential_field = potential_map.get(training.target_stat)
        if potential_field:
            current = getattr(horse, training.target_stat)
            cap = getattr(horse, potential_field)
            gain = min(gain, cap - current)
            gain = max(0, gain)

        # Apply gain
        if gain > 0:
            old_val = getattr(horse, training.target_stat)
            setattr(horse, training.target_stat, old_val + gain)

        # Complete training
        training.completed = True
        training.stat_gain = gain

        # Return horse to ready status
        horse.status = HorseStatus.READY
        horse.form = min(100, horse.form + rng.randint(5, 15))
        horse.energy = min(100, horse.energy + 20)

        completed_count += 1
        logger.info(
            f"Training complete: {horse.name} gained +{gain} {training.target_stat} "
            f"(trainer: {training.trainer_level})"
        )

    if completed_count > 0:
        await db.flush()

    return completed_count


async def get_active_trainings(db: AsyncSession, stable_id) -> list[dict]:
    """Get all active professional trainings for a stable."""
    result = await db.execute(
        select(ProfessionalTraining, Horse)
        .join(Horse, ProfessionalTraining.horse_id == Horse.id)
        .where(
            ProfessionalTraining.stable_id == stable_id,
            ProfessionalTraining.completed == False,
        )
    )
    trainings = result.all()

    return [
        {
            "id": str(t.id),
            "horse_name": h.name,
            "horse_id": str(h.id),
            "target_stat": t.target_stat,
            "trainer_level": t.trainer_level,
            "start_week": t.start_week,
            "end_week": t.end_week,
            "cost_per_week": t.cost_per_week,
        }
        for t, h in trainings
    ]
