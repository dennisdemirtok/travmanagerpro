"""TravManager — Sponsor Service

Handles sponsor discovery, contract signing, and weekly income collection.
"""
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.finance import Sponsor, SponsorContract
from app.models.stable import Stable
from app.services import finance_service

logger = logging.getLogger(__name__)


async def get_available_sponsors(db: AsyncSession, stable_id) -> list[dict]:
    """Return all sponsors with contract status for this stable."""
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return []

    sponsors_result = await db.execute(select(Sponsor).order_by(Sponsor.min_reputation))
    sponsors = sponsors_result.scalars().all()

    # Get active contracts for this stable
    contracts_result = await db.execute(
        select(SponsorContract).where(
            SponsorContract.stable_id == stable_id,
            SponsorContract.is_active == True,
        )
    )
    active_contracts = {c.sponsor_id: c for c in contracts_result.scalars().all()}

    result = []
    for s in sponsors:
        contract = active_contracts.get(s.id)
        meets_rep = stable.reputation >= s.min_reputation
        # Calculate weekly payment based on sponsor tier
        weekly_payment = _calculate_weekly_payment(s)
        win_bonus = _calculate_win_bonus(s)

        result.append({
            "id": str(s.id),
            "name": s.name,
            "min_reputation": s.min_reputation,
            "min_division": s.min_division,
            "weekly_payment": weekly_payment,
            "win_bonus": win_bonus,
            "eligible": meets_rep,
            "has_contract": contract is not None,
            "contract": {
                "id": str(contract.id),
                "weekly_payment": contract.weekly_payment,
                "win_bonus": contract.win_bonus,
                "starts_week": contract.starts_week,
                "ends_week": contract.ends_week,
                "is_active": contract.is_active,
            } if contract else None,
        })
    return result


def _calculate_weekly_payment(sponsor: Sponsor) -> int:
    """Calculate weekly payment based on sponsor tier (min_reputation).
    Rebalanced: 500k öre (5,000 kr) at rep 0 → 5,260k öre (52,600 kr) at rep 70.
    """
    base = 500_000 + (sponsor.min_reputation * 68_000)
    return base


def _calculate_win_bonus(sponsor: Sponsor) -> int:
    """Calculate win bonus for a sponsor.
    Rebalanced: 500k öre (5,000 kr) at rep 0 → 7,500k öre (75,000 kr) at rep 70.
    """
    return 500_000 + (sponsor.min_reputation * 100_000)


async def sign_sponsor_contract(
    db: AsyncSession, stable_id, sponsor_id, game_week: int
) -> dict:
    """Sign a contract with a sponsor."""
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    sponsor_result = await db.execute(select(Sponsor).where(Sponsor.id == sponsor_id))
    sponsor = sponsor_result.scalar_one_or_none()
    if not sponsor:
        return {"error": "Sponsor hittades inte"}

    # Check reputation requirement
    if stable.reputation < sponsor.min_reputation:
        return {"error": f"Kräver minst {sponsor.min_reputation} rykte (du har {stable.reputation})"}

    # Check if already has contract with this sponsor
    existing = await db.execute(
        select(SponsorContract).where(
            SponsorContract.stable_id == stable_id,
            SponsorContract.sponsor_id == sponsor_id,
            SponsorContract.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        return {"error": "Du har redan ett avtal med denna sponsor"}

    # Max 3 active sponsors
    active_count_result = await db.execute(
        select(SponsorContract).where(
            SponsorContract.stable_id == stable_id,
            SponsorContract.is_active == True,
        )
    )
    active_count = len(active_count_result.scalars().all())
    if active_count >= 3:
        return {"error": "Max 3 aktiva sponsoravtal tillåtna"}

    weekly_payment = _calculate_weekly_payment(sponsor)
    win_bonus = _calculate_win_bonus(sponsor)
    contract_weeks = 8  # 8-week contract

    contract = SponsorContract(
        stable_id=stable_id,
        sponsor_id=sponsor_id,
        weekly_payment=weekly_payment,
        win_bonus=win_bonus,
        starts_week=game_week,
        ends_week=game_week + contract_weeks,
        is_active=True,
    )
    db.add(contract)
    await db.flush()

    return {
        "success": True,
        "sponsor_name": sponsor.name,
        "weekly_payment": weekly_payment,
        "win_bonus": win_bonus,
        "contract_weeks": contract_weeks,
        "contract_id": str(contract.id),
    }


async def terminate_sponsor_contract(db: AsyncSession, stable_id, contract_id) -> dict:
    """Terminate a sponsor contract early."""
    contract_result = await db.execute(
        select(SponsorContract).where(
            SponsorContract.id == contract_id,
            SponsorContract.stable_id == stable_id,
            SponsorContract.is_active == True,
        )
    )
    contract = contract_result.scalar_one_or_none()
    if not contract:
        return {"error": "Avtal hittades inte"}

    contract.is_active = False
    await db.flush()
    return {"success": True, "message": "Sponsoravtal avslutat"}


async def collect_weekly_sponsor_income(db: AsyncSession, game_week: int) -> int:
    """Collect sponsor income for NPC stables only (auto-collected by ticker).
    Player stables must collect manually via collect_player_sponsor_income().
    Returns total income distributed.
    """
    contracts_result = await db.execute(
        select(SponsorContract).where(
            SponsorContract.is_active == True,
            SponsorContract.starts_week <= game_week,
            SponsorContract.ends_week >= game_week,
        )
    )
    contracts = contracts_result.scalars().all()
    total_paid = 0

    for contract in contracts:
        # Check if this stable is NPC — only auto-collect for NPCs
        stable_result = await db.execute(
            select(Stable).where(Stable.id == contract.stable_id)
        )
        stable = stable_result.scalar_one_or_none()

        if stable and stable.is_npc:
            await finance_service.record_transaction(
                db, contract.stable_id, contract.weekly_payment,
                "sponsor_income",
                f"Sponsorinkomst vecka {game_week}",
                game_week,
            )
            total_paid += contract.weekly_payment

        # Check if contract expires this week
        if game_week >= contract.ends_week:
            contract.is_active = False

    await db.flush()
    return total_paid


async def collect_player_sponsor_income(
    db: AsyncSession, stable_id, game_week: int, game_day: int
) -> dict:
    """Manually collect sponsor income for a player stable.
    Only available on Saturdays (game_day == 6), once per week.
    """
    # Check it's Saturday
    if game_day != 6:
        return {"error": "Sponsorpengar kan bara hämtas på lördagar"}

    # Get stable and check if already collected this week
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable:
        return {"error": "Stall hittades inte"}

    if stable.last_sponsor_collection_week >= game_week:
        return {"error": "Du har redan hämtat sponsorpengar denna vecka"}

    # Get active contracts
    contracts_result = await db.execute(
        select(SponsorContract).where(
            SponsorContract.stable_id == stable_id,
            SponsorContract.is_active == True,
            SponsorContract.starts_week <= game_week,
            SponsorContract.ends_week >= game_week,
        )
    )
    contracts = contracts_result.scalars().all()

    if not contracts:
        return {"error": "Inga aktiva sponsoravtal att hämta inkomst från"}

    total_income = 0
    sponsor_details = []

    for contract in contracts:
        await finance_service.record_transaction(
            db, stable_id, contract.weekly_payment,
            "sponsor_income",
            f"Sponsorinkomst vecka {game_week}",
            game_week,
        )
        total_income += contract.weekly_payment
        sponsor_details.append({
            "contract_id": str(contract.id),
            "amount": contract.weekly_payment,
        })

        # Check if contract expires this week
        if game_week >= contract.ends_week:
            contract.is_active = False

    # Mark as collected this week
    stable.last_sponsor_collection_week = game_week
    await db.flush()

    return {
        "success": True,
        "total_income": total_income,
        "contracts_paid": len(sponsor_details),
        "details": sponsor_details,
    }


async def get_active_contracts(db: AsyncSession, stable_id) -> list[dict]:
    """Get all active sponsor contracts for a stable."""
    contracts_result = await db.execute(
        select(SponsorContract, Sponsor)
        .join(Sponsor, SponsorContract.sponsor_id == Sponsor.id)
        .where(
            SponsorContract.stable_id == stable_id,
            SponsorContract.is_active == True,
        )
    )
    results = contracts_result.all()

    return [
        {
            "id": str(c.id),
            "sponsor_name": s.name,
            "weekly_payment": c.weekly_payment,
            "win_bonus": c.win_bonus,
            "starts_week": c.starts_week,
            "ends_week": c.ends_week,
            "weeks_remaining": max(0, c.ends_week - c.starts_week),
        }
        for c, s in results
    ]
