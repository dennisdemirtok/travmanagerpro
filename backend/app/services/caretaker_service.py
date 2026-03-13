"""TravManager — Caretaker (Skötare) Service"""
import random
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.caretaker import Caretaker, CaretakerAssignment, CaretakerScoutReport
from app.models.horse import Horse
from app.models.stable import Stable
from app.models.game_state import GameState
from app.models.enums import CaretakerSpecialty, CaretakerPersonality
from app.services import finance_service
from app.data.caretaker_names import CARETAKER_NAMES

logger = logging.getLogger(__name__)

SCOUT_COST = 75_000  # öre (750 kr)

# Personality compatibility matrix
# CaretakerPersonality -> HorsePersonality -> modifier
PERSONALITY_MATRIX = {
    CaretakerPersonality.CALM: {
        "hot": 20, "nervous": 18, "brave": 5, "calm": 10,
        "responsive": 8, "stubborn": -5, "lazy": -8, "sensitive": 12,
        "training_eager": 5, "moody": 10,
    },
    CaretakerPersonality.STRICT: {
        "stubborn": 18, "lazy": 15, "hot": -8, "brave": 10,
        "responsive": 5, "calm": 5, "nervous": -10, "sensitive": -12,
        "training_eager": 8, "moody": -5,
    },
    CaretakerPersonality.GENTLE: {
        "sensitive": 22, "nervous": 15, "moody": 18, "calm": 12,
        "responsive": 10, "hot": 5, "stubborn": -8, "lazy": 5,
        "training_eager": 8, "brave": 5,
    },
    CaretakerPersonality.ENERGETIC: {
        "lazy": 20, "calm": 5, "responsive": 15, "training_eager": 18,
        "brave": 12, "hot": -5, "stubborn": 8, "nervous": -8,
        "sensitive": -5, "moody": 0,
    },
    CaretakerPersonality.METICULOUS: {
        "training_eager": 18, "responsive": 15, "calm": 12, "brave": 10,
        "sensitive": 8, "stubborn": 0, "lazy": 5, "hot": -5,
        "nervous": 5, "moody": 5,
    },
    CaretakerPersonality.EXPERIENCED: {
        # Experienced is decent with everything, no big bonuses or penalties
        "hot": 10, "nervous": 8, "brave": 10, "calm": 10,
        "responsive": 10, "stubborn": 8, "lazy": 8, "sensitive": 8,
        "training_eager": 10, "moody": 8,
    },
}


def calculate_compatibility(caretaker: Caretaker, horse: Horse) -> int:
    """Calculate compatibility score (1-100) between caretaker and horse."""
    score = 50  # base

    # Personality match (biggest factor)
    personality_modifiers = PERSONALITY_MATRIX.get(caretaker.personality, {})
    primary_mod = personality_modifiers.get(horse.personality_primary, 0) if horse.personality_primary else 0
    score += primary_mod

    # Secondary personality modifier (half effect)
    if horse.personality_secondary:
        secondary_mod = personality_modifiers.get(horse.personality_secondary, 0)
        score += secondary_mod // 2

    # Skill base bonus
    score += (caretaker.skill - 50) // 10

    # Horse mood modifier
    if hasattr(horse, 'mood') and horse.mood:
        score += (horse.mood - 50) // 10

    return max(5, min(100, score))


def get_compatibility_label(score: int) -> str:
    """Convert score to Swedish label."""
    if score >= 85:
        return "Utmärkt"
    if score >= 70:
        return "Bra"
    if score >= 50:
        return "OK"
    if score >= 30:
        return "Dålig"
    return "Mycket dålig"


def calculate_stat_boost(caretaker: Caretaker, compatibility: int) -> dict:
    """Calculate stat boosts from caretaker.
    Returns {stat_name: boost_points} (raw 1-100 scale).
    Boost range: 0-15 points (maps to ~0-3 bars on 1-20 display scale).
    """
    if compatibility < 30:
        return {}

    # Compatibility multiplier
    if compatibility >= 85:
        compat_mult = 1.0
    elif compatibility >= 70:
        compat_mult = 0.85
    elif compatibility >= 50:
        compat_mult = 0.6
    else:
        compat_mult = 0.3

    # Skill determines max boost
    max_primary = int((caretaker.skill / 100) * 15)
    primary_boost = max(1, int(max_primary * compat_mult))

    boosts = {caretaker.primary_specialty.value: primary_boost}

    if caretaker.secondary_specialty:
        max_secondary = max_primary // 2
        secondary_boost = int(max_secondary * compat_mult)
        if secondary_boost > 0:
            boosts[caretaker.secondary_specialty.value] = secondary_boost

    return boosts


async def get_available_caretakers(db: AsyncSession) -> list[dict]:
    """Get all available caretakers on the market."""
    result = await db.execute(
        select(Caretaker).where(Caretaker.is_available == True).order_by(Caretaker.skill.desc())
    )
    caretakers = result.scalars().all()
    return [_caretaker_to_dict(c) for c in caretakers]


async def get_stable_assignments(db: AsyncSession, stable_id) -> list[dict]:
    """Get all active caretaker assignments for a stable."""
    result = await db.execute(
        select(CaretakerAssignment)
        .options(
            selectinload(CaretakerAssignment.caretaker),
            selectinload(CaretakerAssignment.horse),
        )
        .where(
            CaretakerAssignment.stable_id == stable_id,
            CaretakerAssignment.is_active == True,
        )
    )
    assignments = result.scalars().all()

    items = []
    for a in assignments:
        compat = await _get_scout_report(db, a.caretaker_id, a.horse_id)
        boost = {}
        if compat:
            boost = calculate_stat_boost(a.caretaker, compat.compatibility_score)

        items.append({
            "assignment_id": str(a.id),
            "caretaker": _caretaker_to_dict(a.caretaker),
            "horse_id": str(a.horse_id),
            "horse_name": a.horse.name if a.horse else "",
            "salary_per_week": a.salary_per_week,
            "compatibility_score": compat.compatibility_score if compat else None,
            "compatibility_label": compat.compatibility_label if compat else None,
            "stat_boosts": boost,
        })
    return items


async def scout_caretaker(db: AsyncSession, caretaker_id, horse_id, stable_id) -> dict:
    """Scout a caretaker for compatibility with a specific horse. Costs money."""
    # Check existing report
    existing = await _get_scout_report(db, caretaker_id, horse_id)
    if existing:
        c = await db.get(Caretaker, caretaker_id)
        boost = calculate_stat_boost(c, existing.compatibility_score) if c else {}
        return {
            "already_scouted": True,
            "compatibility_score": existing.compatibility_score,
            "compatibility_label": existing.compatibility_label,
            "primary_boost": existing.primary_boost,
            "secondary_boost": existing.secondary_boost,
            "stat_boosts": boost,
        }

    # Load caretaker and horse
    caretaker = await db.get(Caretaker, caretaker_id)
    if not caretaker:
        return {"error": "Skötaren finns inte"}

    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen tillhör inte ditt stall"}

    # Get game week
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    # Charge scout fee
    stable = await db.get(Stable, stable_id)
    if not stable or stable.balance < SCOUT_COST:
        return {"error": f"Inte tillräckligt med pengar. Granskning kostar {SCOUT_COST // 100} kr."}

    await finance_service.record_transaction(
        db, stable_id, -SCOUT_COST, "caretaker_scout",
        f"Granskning av skötare {caretaker.name} för {horse.name}",
        game_week,
    )

    # Calculate compatibility
    score = calculate_compatibility(caretaker, horse)
    label = get_compatibility_label(score)
    boost = calculate_stat_boost(caretaker, score)

    primary_boost_val = boost.get(caretaker.primary_specialty.value, 0)
    secondary_boost_val = boost.get(caretaker.secondary_specialty.value, 0) if caretaker.secondary_specialty else 0

    # Save report
    report = CaretakerScoutReport(
        caretaker_id=caretaker_id,
        horse_id=horse_id,
        stable_id=stable_id,
        compatibility_score=score,
        compatibility_label=label,
        primary_boost=primary_boost_val,
        secondary_boost=secondary_boost_val,
        game_week=game_week,
    )
    db.add(report)
    await db.flush()

    return {
        "already_scouted": False,
        "compatibility_score": score,
        "compatibility_label": label,
        "primary_boost": primary_boost_val,
        "secondary_boost": secondary_boost_val,
        "stat_boosts": boost,
        "cost": SCOUT_COST,
    }


async def hire_caretaker(db: AsyncSession, caretaker_id, horse_id, stable_id, offered_salary: int) -> dict:
    """Make a salary offer to hire a caretaker for a specific horse."""
    caretaker = await db.get(Caretaker, caretaker_id)
    if not caretaker:
        return {"error": "Skötaren finns inte"}
    if not caretaker.is_available:
        return {"error": "Skötaren är inte tillgänglig"}

    # Verify horse belongs to stable
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen tillhör inte ditt stall"}

    # Check horse doesn't already have a caretaker
    existing = await db.execute(
        select(CaretakerAssignment).where(
            CaretakerAssignment.horse_id == horse_id,
            CaretakerAssignment.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        return {"error": "Hästen har redan en skötare. Avskeda den nuvarande först."}

    # Accept/reject based on offer vs demand
    ratio = offered_salary / caretaker.salary_demand if caretaker.salary_demand > 0 else 1.0

    if ratio >= 1.0:
        accepted = True
    elif ratio >= 0.85:
        accepted = random.random() < 0.70
    elif ratio >= 0.70:
        accepted = random.random() < 0.30
    else:
        accepted = False

    if not accepted:
        return {
            "accepted": False,
            "message": "Skötaren tackade nej till erbjudandet. Prova en högre lön.",
        }

    # Get game week
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    # Charge signing fee (2x weekly salary)
    signing_fee = offered_salary * 2
    stable = await db.get(Stable, stable_id)
    if not stable or stable.balance < signing_fee:
        return {"error": f"Inte tillräckligt med pengar. Signeringsavgift: {signing_fee // 100} kr."}

    await finance_service.record_transaction(
        db, stable_id, -signing_fee, "caretaker_signing",
        f"Signeringsavgift skötare {caretaker.name} för {horse.name}",
        game_week,
    )

    # Create assignment
    assignment = CaretakerAssignment(
        caretaker_id=caretaker_id,
        horse_id=horse_id,
        stable_id=stable_id,
        salary_per_week=offered_salary,
        starts_game_week=game_week,
    )
    db.add(assignment)

    # Mark caretaker as unavailable
    caretaker.is_available = False
    await db.flush()

    return {
        "accepted": True,
        "assignment_id": str(assignment.id),
        "signing_fee": signing_fee,
        "salary_per_week": offered_salary,
        "message": f"{caretaker.name} accepterade erbjudandet!",
    }


async def fire_caretaker(db: AsyncSession, assignment_id, stable_id) -> dict:
    """Fire a caretaker (release from horse)."""
    result = await db.execute(
        select(CaretakerAssignment)
        .options(selectinload(CaretakerAssignment.caretaker))
        .where(
            CaretakerAssignment.id == assignment_id,
            CaretakerAssignment.stable_id == stable_id,
            CaretakerAssignment.is_active == True,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        return {"error": "Anställningen hittades inte"}

    assignment.is_active = False
    assignment.caretaker.is_available = True
    await db.flush()

    return {"status": "ok", "message": f"{assignment.caretaker.name} har avskedats."}


async def get_horse_caretaker(db: AsyncSession, horse_id) -> dict | None:
    """Get the active caretaker for a horse, including stat boosts."""
    result = await db.execute(
        select(CaretakerAssignment)
        .options(selectinload(CaretakerAssignment.caretaker))
        .where(
            CaretakerAssignment.horse_id == horse_id,
            CaretakerAssignment.is_active == True,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        return None

    report = await _get_scout_report(db, assignment.caretaker_id, horse_id)
    boost = {}
    if report:
        boost = calculate_stat_boost(assignment.caretaker, report.compatibility_score)

    return {
        "assignment_id": str(assignment.id),
        "caretaker": _caretaker_to_dict(assignment.caretaker),
        "salary_per_week": assignment.salary_per_week,
        "compatibility_score": report.compatibility_score if report else None,
        "compatibility_label": report.compatibility_label if report else None,
        "stat_boosts": boost,
    }


async def get_scout_reports_for_stable(db: AsyncSession, stable_id, caretaker_id=None) -> list[dict]:
    """Get all scout reports for a stable, optionally filtered by caretaker."""
    q = select(CaretakerScoutReport).where(CaretakerScoutReport.stable_id == stable_id)
    if caretaker_id:
        q = q.where(CaretakerScoutReport.caretaker_id == caretaker_id)
    result = await db.execute(q)
    reports = result.scalars().all()
    return [
        {
            "caretaker_id": str(r.caretaker_id),
            "horse_id": str(r.horse_id),
            "compatibility_score": r.compatibility_score,
            "compatibility_label": r.compatibility_label,
            "primary_boost": r.primary_boost,
            "secondary_boost": r.secondary_boost,
        }
        for r in reports
    ]


async def seed_npc_caretakers(db: AsyncSession, count: int = 25):
    """Seed NPC caretakers at bootstrap or for market refresh."""
    existing = await db.execute(select(Caretaker))
    existing_names = {c.name for c in existing.scalars().all()}

    rng = random.Random(42)
    specialties = list(CaretakerSpecialty)
    personalities = list(CaretakerPersonality)
    available_names = [n for n in CARETAKER_NAMES if n not in existing_names]

    created = 0
    for name in available_names[:count]:
        skill = int(rng.gauss(55, 15))
        skill = max(25, min(95, skill))

        primary = rng.choice(specialties)
        secondary = None
        if rng.random() < 0.6:
            secondary = rng.choice([s for s in specialties if s != primary])

        personality = rng.choice(personalities)
        salary = int(skill * 5_000 * (0.8 + rng.random() * 0.4))

        db.add(Caretaker(
            name=name,
            skill=skill,
            primary_specialty=primary,
            secondary_specialty=secondary,
            personality=personality,
            salary_demand=salary,
        ))
        created += 1

    await db.flush()
    logger.info(f"Seeded {created} NPC caretakers")
    return created


# --- Internal helpers ---

async def _get_scout_report(db: AsyncSession, caretaker_id, horse_id) -> CaretakerScoutReport | None:
    result = await db.execute(
        select(CaretakerScoutReport).where(
            CaretakerScoutReport.caretaker_id == caretaker_id,
            CaretakerScoutReport.horse_id == horse_id,
        )
    )
    return result.scalar_one_or_none()


def _caretaker_to_dict(c: Caretaker) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "skill": c.skill,
        "primary_specialty": c.primary_specialty.value,
        "secondary_specialty": c.secondary_specialty.value if c.secondary_specialty else None,
        "personality": c.personality.value,
        "salary_demand": c.salary_demand,
        "is_available": c.is_available,
    }
