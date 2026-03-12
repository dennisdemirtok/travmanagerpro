"""TravManager — Breeding Service

Handles stallion registry, breeding requests, pregnancy tracking,
foal births, and pedigree generation.
"""
import random
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.stable import Stable
from app.models.breeding import StallionRegistry, HorsePedigree, ProfessionalTraining
from app.models.enums import HorseGender, HorseStatus, PersonalityType, SpecialTrait, POSITIVE_TRAITS, NEGATIVE_TRAITS
from app.data.pedigree_names import generate_pedigree, DAM_NAMES
from app.services import finance_service

logger = logging.getLogger(__name__)

PREGNANCY_DURATION_WEEKS = 4
FOAL_NAMES = [
    "Lilla Stjärnan", "Unga Blixten", "Nya Hoppet", "Framtidens Dröm",
    "Vårens Bud", "Lilla Prinsen", "Lilla Prinsessan", "Unga Kransen",
    "Morgondagens", "Spirande Eld", "Nya Kraften", "Solens Unge",
    "Drömmens Barn", "Ljusets Arv", "Framtids Gull", "Nya Stjernan",
]


async def get_available_stallions(db: AsyncSession) -> list[dict]:
    """Return all available stallions for breeding."""
    result = await db.execute(
        select(StallionRegistry)
        .where(StallionRegistry.available == True)
        .order_by(StallionRegistry.prestige.desc())
    )
    stallions = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "origin_country": s.origin_country,
            "stud_fee": s.stud_fee,
            "bonuses": {
                "speed": s.speed_bonus,
                "endurance": s.endurance_bonus,
                "mentality": s.mentality_bonus,
                "sprint": s.sprint_bonus,
                "balance": s.balance_bonus,
                "strength": s.strength_bonus,
                "start": s.start_bonus,
            },
            "prestige": s.prestige,
            "description": s.description,
        }
        for s in stallions
    ]


async def breed_horse(
    db: AsyncSession, stable_id, mare_id, stallion_id, game_week: int
) -> dict:
    """Start a breeding process: mare + stallion → pregnancy."""
    # Verify stable
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    # Verify mare
    mare_result = await db.execute(
        select(Horse).where(Horse.id == mare_id, Horse.stable_id == stable_id)
    )
    mare = mare_result.scalar_one_or_none()
    if not mare:
        return {"error": "Hästen tillhör inte ditt stall"}
    if mare.gender != HorseGender.MARE:
        return {"error": "Endast ston kan avlas"}
    if mare.pregnancy_week is not None:
        return {"error": "Stoet är redan dräktigt"}
    if mare.status != HorseStatus.READY:
        return {"error": f"Stoet är inte redo (status: {mare.status.value})"}

    # Verify stallion
    stallion_result = await db.execute(
        select(StallionRegistry).where(StallionRegistry.id == stallion_id)
    )
    stallion = stallion_result.scalar_one_or_none()
    if not stallion:
        return {"error": "Hingsten hittades inte"}
    if not stallion.available:
        return {"error": "Hingsten är inte tillgänglig"}

    # Check balance
    if stable.balance < stallion.stud_fee:
        return {"error": f"Inte tillräckligt med pengar (behöver {stallion.stud_fee:,} öre)"}

    # Deduct stud fee
    await finance_service.record_transaction(
        db, stable_id, -stallion.stud_fee, "breeding",
        f"Betäckningsavgift: {stallion.name}", game_week,
    )

    # Set pregnancy
    mare.pregnancy_week = game_week
    mare.expected_foal_week = game_week + PREGNANCY_DURATION_WEEKS
    mare.status = HorseStatus.RESTING

    await db.flush()

    return {
        "success": True,
        "mare_name": mare.name,
        "stallion_name": stallion.name,
        "stud_fee": stallion.stud_fee,
        "expected_foal_week": mare.expected_foal_week,
        "pregnancy_weeks": PREGNANCY_DURATION_WEEKS,
    }


async def check_births(db: AsyncSession, game_week: int) -> int:
    """Process all due pregnancies and create foals. Returns count of births."""
    pregnant_result = await db.execute(
        select(Horse).where(
            Horse.expected_foal_week <= game_week,
            Horse.pregnancy_week.isnot(None),
        )
    )
    mares = pregnant_result.scalars().all()
    births = 0

    for mare in mares:
        try:
            # Check stable capacity before birth
            from sqlalchemy import func as sqlfunc
            horse_count_result = await db.execute(
                select(sqlfunc.count(Horse.id)).where(Horse.stable_id == mare.stable_id)
            )
            horse_count = horse_count_result.scalar() or 0

            stable_result = await db.execute(
                select(Stable).where(Stable.id == mare.stable_id)
            )
            stable = stable_result.scalar_one_or_none()
            max_horses = (stable.max_horses if stable else 3) or 3

            if horse_count >= max_horses:
                # Delay birth — keep pregnancy for another week
                logger.warning(
                    f"Foal birth delayed for mare {mare.name}: stable full "
                    f"({horse_count}/{max_horses}). Pregnancy extends 1 week."
                )
                mare.expected_foal_week = game_week + 1
                continue

            await _create_foal(db, mare, game_week)
            # Reset mare
            mare.pregnancy_week = None
            mare.expected_foal_week = None
            mare.status = HorseStatus.READY
            births += 1
        except Exception as e:
            logger.error(f"Error creating foal for mare {mare.id}: {e}")

    if births > 0:
        await db.flush()
        logger.info(f"Breeding: {births} foals born in week {game_week}")

    return births


async def _create_foal(db: AsyncSession, mare: Horse, game_week: int):
    """Create a foal from a mare (breeding pregnancy result)."""
    rng = random.Random(int(str(mare.id).replace("-", "")[:8], 16) + game_week)

    # Look up the stallion used (from the pedigree if exists, or generate random)
    # For now, generate foal stats based on mare stats + random variation
    # Get mare's pedigree to find the stallion info
    pedigree_result = await db.execute(
        select(HorsePedigree).where(HorsePedigree.horse_id == mare.id)
    )
    mare_pedigree = pedigree_result.scalar_one_or_none()

    # Generate foal name
    foal_name = rng.choice(FOAL_NAMES)
    # Add uniqueness
    foal_name = f"{foal_name} {rng.randint(1, 99)}"

    # Gender
    gender = rng.choice([HorseGender.STALLION, HorseGender.MARE, HorseGender.GELDING])

    # Stats: based on mare stats with random variation
    def foal_stat(mare_val: int) -> int:
        """Generate foal stat: ~30% of mare stat + random factor."""
        base = int(mare_val * 0.3) + rng.randint(5, 25)
        return max(10, min(60, base))

    def foal_potential(stat: int) -> int:
        """Generate potential ceiling for foal."""
        return min(99, stat + rng.randint(15, 35))

    speed = foal_stat(mare.speed)
    endurance = foal_stat(mare.endurance)
    mentality = foal_stat(mare.mentality)
    start_ability = foal_stat(mare.start_ability)
    sprint_strength = foal_stat(mare.sprint_strength)
    balance = foal_stat(mare.balance)
    strength = foal_stat(mare.strength)

    # Personality
    personalities = list(PersonalityType)
    primary = rng.choice(personalities)
    secondary = rng.choice(personalities)

    # Special traits: 20% positive, 80% negative
    traits = []
    if rng.random() < 0.30:  # 30% chance of having a trait
        if rng.random() < 0.20:
            traits.append(rng.choice(POSITIVE_TRAITS).value)
        else:
            traits.append(rng.choice(NEGATIVE_TRAITS).value)

    foal = Horse(
        stable_id=mare.stable_id,
        name=foal_name,
        gender=gender,
        birth_game_week=game_week,
        age_game_weeks=0,
        age_years=0,
        status=HorseStatus.RESTING,  # Foals can't race yet
        is_npc=mare.is_npc,
        speed=speed, endurance=endurance, mentality=mentality,
        start_ability=start_ability, sprint_strength=sprint_strength,
        balance=balance, strength=strength,
        potential_speed=foal_potential(speed),
        potential_endurance=foal_potential(endurance),
        potential_mentality=foal_potential(mentality),
        potential_start=foal_potential(start_ability),
        potential_sprint=foal_potential(sprint_strength),
        potential_balance=foal_potential(balance),
        potential_strength=foal_potential(strength),
        condition=70, energy=100, health=95,
        current_weight=round(rng.uniform(350, 400), 1),
        ideal_weight=round(rng.uniform(440, 480), 1),
        form=40, mood=80, fatigue=0,
        gallop_tendency=rng.randint(10, 25),
        distance_optimum=rng.choice([1640, 2140, 2140, 2640]),
        racing_instinct=rng.randint(30, 60),
        personality_primary=primary,
        personality_secondary=secondary,
        personality_revealed=False,
        special_traits=traits,
        traits_revealed=False,
        generation=(mare.generation or 1) + 1,
    )
    db.add(foal)
    await db.flush()

    # Create pedigree for foal
    pedigree_data = generate_pedigree(
        stallion_name="Okänd Hingst",  # Will be replaced with actual stallion if available
        stallion_origin="SE",
        rng=rng,
    )
    # Override dam info with actual mare
    pedigree_data["dam_name"] = mare.name
    pedigree_data["dam_origin"] = "SE"

    # If mare has a pedigree, use her parents as grandparents
    if mare_pedigree:
        pedigree_data["dam_sire_name"] = mare_pedigree.sire_name
        pedigree_data["dam_dam_name"] = mare_pedigree.dam_name

    foal_pedigree = HorsePedigree(
        horse_id=foal.id,
        sire_name=pedigree_data["sire_name"],
        sire_origin=pedigree_data["sire_origin"],
        dam_name=pedigree_data["dam_name"],
        dam_origin=pedigree_data["dam_origin"],
        sire_sire_name=pedigree_data.get("sire_sire_name"),
        sire_dam_name=pedigree_data.get("sire_dam_name"),
        dam_sire_name=pedigree_data.get("dam_sire_name"),
        dam_dam_name=pedigree_data.get("dam_dam_name"),
    )
    db.add(foal_pedigree)

    logger.info(f"Foal born: {foal_name} (stable {mare.stable_id})")


async def get_breeding_status(db: AsyncSession, stable_id) -> list[dict]:
    """Get pregnancy/breeding status for all mares in stable."""
    mares_result = await db.execute(
        select(Horse).where(
            Horse.stable_id == stable_id,
            Horse.gender == HorseGender.MARE,
        )
    )
    mares = mares_result.scalars().all()

    return [
        {
            "id": str(m.id),
            "name": m.name,
            "is_pregnant": m.pregnancy_week is not None,
            "pregnancy_week": m.pregnancy_week,
            "expected_foal_week": m.expected_foal_week,
            "age_years": m.age_years,
            "status": m.status.value,
        }
        for m in mares
    ]


async def get_horse_pedigree(db: AsyncSession, horse_id) -> dict | None:
    """Get 3-generation pedigree for a horse."""
    result = await db.execute(
        select(HorsePedigree).where(HorsePedigree.horse_id == horse_id)
    )
    pedigree = result.scalar_one_or_none()
    if not pedigree:
        return None

    return {
        "sire": {
            "name": pedigree.sire_name,
            "origin": pedigree.sire_origin,
            "sire": {"name": pedigree.sire_sire_name},
            "dam": {"name": pedigree.sire_dam_name},
        },
        "dam": {
            "name": pedigree.dam_name,
            "origin": pedigree.dam_origin,
            "sire": {"name": pedigree.dam_sire_name},
            "dam": {"name": pedigree.dam_dam_name},
        },
    }
