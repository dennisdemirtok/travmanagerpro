"""TravManager — Driver Service"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.driver import Driver, DriverContract, DriverHorseHistory
from app.models.horse import Horse
from app.models.game_state import GameState, CompatibilityCache
from app.engine.race_engine import calculate_compatibility
from app.services.horse_service import _horse_to_engine_stats, _driver_to_engine_stats, _compat_label
from app.services import finance_service

COMPAT_CHECK_COST = 50_000  # 500 SEK in ore


async def list_drivers(db: AsyncSession, stable_id):
    # Get contracted drivers
    contracts_result = await db.execute(
        select(DriverContract)
        .options(selectinload(DriverContract.driver))
        .where(DriverContract.stable_id == stable_id, DriverContract.is_active == True)
    )
    contracts = contracts_result.scalars().all()

    contracted = []
    for c in contracts:
        d = c.driver
        contracted.append({
            "id": str(d.id), "name": d.name,
            "skill": d.skill, "start_skill": d.start_skill,
            "tactical_ability": d.tactical_ability,
            "sprint_timing": d.sprint_timing,
            "gallop_handling": d.gallop_handling,
            "experience": d.experience, "composure": d.composure,
            "driving_style": d.driving_style.value,
            "contract_type": c.contract_type.value,
            "salary_per_week": c.salary_per_week,
            "is_active": c.is_active,
        })

    # Get real drivers available on the market (not contracted by this stable)
    contracted_ids = {c.driver_id for c in contracts}
    market_result = await db.execute(
        select(Driver).where(Driver.is_real_driver == True)
    )
    market_drivers = market_result.scalars().all()

    market = []
    for d in market_drivers:
        if d.id in contracted_ids:
            continue
        market.append({
            "id": str(d.id), "name": d.name,
            "skill": d.skill, "start_skill": d.start_skill,
            "tactical_ability": d.tactical_ability,
            "sprint_timing": d.sprint_timing,
            "gallop_handling": d.gallop_handling,
            "experience": d.experience, "composure": d.composure,
            "driving_style": d.driving_style.value,
            "base_salary": d.base_salary,
            "guest_fee": d.guest_fee,
            "popularity": d.popularity,
            "is_real_driver": True,
        })

    return {"contracted": contracted, "market": market}


def _build_compat_result(score, shared_races):
    """Build the compatibility result dict from a score."""
    label = _compat_label(score)
    perf_mod = "+0%"
    gallop_mod = "+0%"
    if score >= 86:
        perf_mod, gallop_mod = "+8%", "-10%"
    elif score >= 71:
        perf_mod, gallop_mod = "+5%", "-5%"
    elif score >= 51:
        perf_mod, gallop_mod = "+3%", "+0%"
    elif score <= 30:
        perf_mod = "-5%"

    return {
        "score": score, "label": label,
        "performance_mod": perf_mod, "gallop_risk_mod": gallop_mod,
        "breakdown": {
            "style_match": score - min(15, shared_races * 2),
            "experience_bonus": min(15, shared_races * 2),
            "shared_races": shared_races,
        },
    }


async def check_compatibility_paid(db: AsyncSession, driver_id, horse_id, stable_id):
    """Paid compatibility check. Charges COMPAT_CHECK_COST ore.
    Returns cached result if already paid, otherwise calculates and caches.
    """
    # Check cache first
    cache_result = await db.execute(
        select(CompatibilityCache).where(
            CompatibilityCache.horse_id == horse_id,
            CompatibilityCache.driver_id == driver_id,
            CompatibilityCache.is_paid == True,
        )
    )
    cached = cache_result.scalar_one_or_none()
    if cached:
        # Already paid — return free
        hist_result = await db.execute(
            select(DriverHorseHistory).where(
                DriverHorseHistory.driver_id == driver_id,
                DriverHorseHistory.horse_id == horse_id,
            )
        )
        hist = hist_result.scalar_one_or_none()
        shared = hist.races_together if hist else 0
        result = _build_compat_result(cached.total_score, shared)
        result["is_cached"] = True
        result["cost"] = 0
        return result

    # Validate driver and horse exist
    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return {"error": "Kusken hittades inte"}

    horse_result = await db.execute(select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id))
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte"}

    # Charge the stable
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    await finance_service.record_transaction(
        db, stable_id, -COMPAT_CHECK_COST, "compatibility_check",
        f"Kompatibilitetskoll: {driver.name} + {horse.name}",
        game_week,
    )

    # Calculate
    hist_result = await db.execute(
        select(DriverHorseHistory).where(
            DriverHorseHistory.driver_id == driver_id,
            DriverHorseHistory.horse_id == horse_id,
        )
    )
    hist = hist_result.scalar_one_or_none()
    shared_races = hist.races_together if hist else 0

    hs = _horse_to_engine_stats(horse)
    ds = _driver_to_engine_stats(driver)
    score = calculate_compatibility(hs, ds, shared_races)

    # Store in cache (upsert)
    existing_cache = await db.execute(
        select(CompatibilityCache).where(
            CompatibilityCache.horse_id == horse_id,
            CompatibilityCache.driver_id == driver_id,
        )
    )
    existing = existing_cache.scalar_one_or_none()
    if existing:
        existing.total_score = score
        existing.base_score = score - min(15, shared_races * 2)
        existing.experience_bonus = min(15, shared_races * 2)
        existing.is_paid = True
    else:
        db.add(CompatibilityCache(
            horse_id=horse_id, driver_id=driver_id,
            base_score=score - min(15, shared_races * 2),
            experience_bonus=min(15, shared_races * 2),
            total_score=score, is_paid=True,
        ))

    await db.flush()

    result = _build_compat_result(score, shared_races)
    result["is_cached"] = False
    result["cost"] = COMPAT_CHECK_COST
    return result


async def get_compatibility(db: AsyncSession, driver_id, horse_id, stable_id):
    """Check if paid compatibility exists. Returns score if paid, otherwise locked status."""
    # Check if already paid
    cache_result = await db.execute(
        select(CompatibilityCache).where(
            CompatibilityCache.horse_id == horse_id,
            CompatibilityCache.driver_id == driver_id,
            CompatibilityCache.is_paid == True,
        )
    )
    cached = cache_result.scalar_one_or_none()

    if cached:
        hist_result = await db.execute(
            select(DriverHorseHistory).where(
                DriverHorseHistory.driver_id == driver_id,
                DriverHorseHistory.horse_id == horse_id,
            )
        )
        hist = hist_result.scalar_one_or_none()
        shared = hist.races_together if hist else 0
        result = _build_compat_result(cached.total_score, shared)
        result["is_checked"] = True
        return result

    # Not paid yet — return locked
    return {
        "score": None,
        "label": "?",
        "is_checked": False,
        "check_cost": COMPAT_CHECK_COST,
    }


async def renew_contract(db: AsyncSession, driver_id, stable_id, contract_type: str, weeks: int):
    """Renew or create contract with a driver."""
    from app.models.enums import ContractType
    from app.services import finance_service

    contract_result = await db.execute(
        select(DriverContract).where(
            DriverContract.driver_id == driver_id,
            DriverContract.stable_id == stable_id,
            DriverContract.is_active == True,
        )
    )
    contract = contract_result.scalar_one_or_none()

    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return {"error": "Kusken hittades inte"}

    try:
        ct = ContractType(contract_type)
    except ValueError:
        return {"error": "Ogiltig kontraktstyp"}

    salary = driver.base_salary
    if ct == ContractType.GUEST:
        salary = driver.guest_fee
    elif ct == ContractType.APPRENTICE:
        salary = int(driver.base_salary * 0.6)

    signing_fee = salary * 2

    if contract:
        contract.contract_type = ct
        contract.salary_per_week = salary
        contract.ends_game_week = contract.ends_game_week + weeks
    else:
        contract = DriverContract(
            stable_id=stable_id, driver_id=driver_id,
            contract_type=ct, salary_per_week=salary,
            starts_game_week=1, ends_game_week=1 + weeks,
            is_active=True,
        )
        db.add(contract)

    await finance_service.record_transaction(
        db, stable_id, -signing_fee, "driver_contract",
        f"Kontraktskostnad: {driver.name} ({ct.value})", 1,
    )

    await db.flush()
    return {"success": True, "salary_per_week": salary, "signing_fee": signing_fee}


async def terminate_contract(db: AsyncSession, driver_id, stable_id):
    """Terminate an active driver contract."""
    contract_result = await db.execute(
        select(DriverContract).where(
            DriverContract.driver_id == driver_id,
            DriverContract.stable_id == stable_id,
            DriverContract.is_active == True,
        )
    )
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return {"error": "Inget aktivt kontrakt hittades"}

    contract.is_active = False
    await db.flush()
    return {"success": True}
