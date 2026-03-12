"""TravManager — Finance Service

Handles transaction recording and weekly stable costs.
Weekly costs:
- Stall rent: 300,000 öre/horse/week (3,000 kr)
- Base feed: 150,000 öre/horse/week (1,500 kr)
- Staff: 500,000 öre/week (5,000 kr)
"""
import logging
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import Transaction
from app.models.stable import Stable
from app.models.horse import Horse
from app.models.driver import DriverContract

logger = logging.getLogger(__name__)

# Weekly cost constants (in öre)
STALL_RENT_PER_HORSE = 300_000    # 3,000 kr per horse per week
FEED_COST_PER_HORSE = 150_000     # 1,500 kr per horse per week
STAFF_COST_BASE = 500_000          # 5,000 kr flat per week


async def record_transaction(
    db: AsyncSession, stable_id, amount: int, category: str,
    description: str, game_week: int, reference_type: str = None,
    reference_id=None,
):
    """Insert a transaction. DB trigger auto-updates stable.balance."""
    txn = Transaction(
        stable_id=stable_id, amount=amount, category=category,
        description=description, game_week=game_week,
        reference_type=reference_type, reference_id=reference_id,
    )
    db.add(txn)
    await db.flush()
    return txn


async def deduct_weekly_stable_costs(db: AsyncSession, game_week: int) -> int:
    """Deduct weekly fixed costs for ALL stables.
    Called once per game week by the ticker.
    Returns total costs deducted across all stables.
    """
    stables_result = await db.execute(select(Stable))
    stables = stables_result.scalars().all()
    total_deducted = 0

    for stable in stables:
        # Count horses in this stable
        horse_count_result = await db.execute(
            select(sa_func.count(Horse.id)).where(Horse.stable_id == stable.id)
        )
        horse_count = horse_count_result.scalar() or 0

        if horse_count == 0 and not stable.is_npc:
            continue  # No costs if no horses (skip empty player stables)

        # Calculate costs
        stall_cost = STALL_RENT_PER_HORSE * horse_count
        feed_cost = FEED_COST_PER_HORSE * horse_count
        staff_cost = STAFF_COST_BASE

        # Driver salaries from active contracts
        contracts_result = await db.execute(
            select(DriverContract).where(
                DriverContract.stable_id == stable.id,
                DriverContract.is_active == True,
            )
        )
        driver_costs = sum(c.salary_per_week for c in contracts_result.scalars().all())

        total_cost = stall_cost + feed_cost + staff_cost + driver_costs

        if total_cost > 0:
            # Single summary transaction per stable
            description_parts = []
            if stall_cost > 0:
                description_parts.append(f"Stallhyra {horse_count} hästar: {stall_cost:,}")
            if feed_cost > 0:
                description_parts.append(f"Foder: {feed_cost:,}")
            description_parts.append(f"Personal: {staff_cost:,}")
            if driver_costs > 0:
                description_parts.append(f"Kusklöner: {driver_costs:,}")

            await record_transaction(
                db, stable.id, -total_cost, "weekly_costs",
                f"Veckokostnader V{game_week}: " + ", ".join(description_parts),
                game_week,
            )
            total_deducted += total_cost

    await db.flush()
    if total_deducted > 0:
        logger.info(f"Weekly costs deducted for week {game_week}: {total_deducted:,} öre total")

    return total_deducted


async def calculate_weekly_cost_estimate(db: AsyncSession, stable_id) -> dict:
    """Calculate estimated weekly costs for a stable (for display)."""
    # Count horses
    horse_count_result = await db.execute(
        select(sa_func.count(Horse.id)).where(Horse.stable_id == stable_id)
    )
    horse_count = horse_count_result.scalar() or 0

    stall_cost = STALL_RENT_PER_HORSE * horse_count
    feed_cost = FEED_COST_PER_HORSE * horse_count
    staff_cost = STAFF_COST_BASE

    # Driver salaries
    contracts_result = await db.execute(
        select(DriverContract).where(
            DriverContract.stable_id == stable_id,
            DriverContract.is_active == True,
        )
    )
    driver_costs = sum(c.salary_per_week for c in contracts_result.scalars().all())

    total = stall_cost + feed_cost + staff_cost + driver_costs

    return {
        "stall_rent": stall_cost,
        "feed": feed_cost,
        "staff": staff_cost,
        "driver_salaries": driver_costs,
        "total": total,
        "horse_count": horse_count,
    }


async def get_financial_overview(db: AsyncSession, stable_id):
    result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = result.scalar_one()

    # Weekly cost estimate
    weekly_costs = await calculate_weekly_cost_estimate(db, stable_id)

    # Get recent transactions
    txns = await db.execute(
        select(Transaction)
        .where(Transaction.stable_id == stable_id)
        .order_by(Transaction.created_at.desc())
        .limit(100)
    )
    transactions = txns.scalars().all()

    income = sum(t.amount for t in transactions if t.amount > 0)
    expenses = sum(t.amount for t in transactions if t.amount < 0)

    return {
        "balance": stable.balance,
        "weekly_summary": {
            "income": {"total": income},
            "expenses": {"total": abs(expenses)},
            "net": income + expenses,
        },
        "weekly_costs": weekly_costs,
        "trend_8_weeks": [],
        "sponsors": [],
    }


async def get_transactions(db: AsyncSession, stable_id, category=None, game_week=None, limit=50):
    q = select(Transaction).where(Transaction.stable_id == stable_id)
    if category:
        q = q.where(Transaction.category == category)
    if game_week:
        q = q.where(Transaction.game_week == game_week)
    q = q.order_by(Transaction.created_at.desc()).limit(limit)
    result = await db.execute(q)
    txns = result.scalars().all()
    return [
        {
            "id": str(t.id), "amount": t.amount, "category": t.category,
            "description": t.description, "game_week": t.game_week,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txns
    ]
