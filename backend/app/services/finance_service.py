"""TravManager — Finance Service (Ekonomi 2.0)

Allt räknas i öre (1 kr = 100 öre).

Kostnader per vecka:
- Stallhyra: progressiv — 1 500 kr för häst 1-3, 3 000 kr för 4-6, 5 000 kr för 7+
- Foder: 500 kr/häst
- Personal: 5 000 kr fast
- Kusklöner: endast kontrakterade kuskar (frilanskusk betalas per lopp)

Skuld:
- Övertrasseringsränta 2 %/vecka på negativt saldo
- Låneränta 3 %/vecka på utestående lån (max 200 000 kr)
- Under −100 000 kr: krav på hästförsäljning inom 2 veckor, annars tvångsförsäljning
- Konkursgolv vid −300 000 kr → Nystart erbjuds
"""
import logging

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import Transaction
from app.models.stable import Stable
from app.models.horse import Horse
from app.models.driver import DriverContract
from app.models.enums import HorseStatus

logger = logging.getLogger(__name__)

# ── Kostnadskonstanter (öre) ────────────────────────────────────────────
STALL_RENT_TIER_1 = 150_000   # 1 500 kr — häst 1-3
STALL_RENT_TIER_2 = 300_000   # 3 000 kr — häst 4-6
STALL_RENT_TIER_3 = 500_000   # 5 000 kr — häst 7+
FEED_COST_PER_HORSE = 50_000  # 500 kr
STAFF_COST_BASE = 500_000     # 5 000 kr

# Kusk
FREELANCE_DRIVER_FEE = 80_000  # 800 kr per lopp

# ── Intäktskonstanter ───────────────────────────────────────────────────
START_FEE_PCT = 0.01          # 1 % av prispotten
START_FEE_MIN = 50_000        # 500 kr golv
BREEDER_PREMIUM_PCT = 0.05    # 5 % uppfödarpremie

# ── Skuldkonstanter ─────────────────────────────────────────────────────
OVERDRAFT_INTEREST_RATE = 0.02   # 2 %/vecka på negativt saldo
LOAN_INTEREST_RATE = 0.03        # 3 %/vecka på lån
MAX_LOAN = 20_000_000            # 200 000 kr
FORCED_SALE_THRESHOLD = -10_000_000   # −100 000 kr
FORCED_SALE_GRACE_WEEKS = 2
BANKRUPTCY_FLOOR = -30_000_000        # −300 000 kr
FORCED_SALE_VALUE_PCT = 0.50
RESTART_REPUTATION_PENALTY = 20


def format_kr(ore: int) -> str:
    """Formatera öre som svensk kronsträng: 26 500 kr."""
    kr = round(ore / 100)
    return f"{kr:,}".replace(",", " ") + " kr"


def calculate_stall_rent(horse_count: int) -> int:
    """Progressiv stallhyra i öre. Häst 1-3 billig, 7+ dyr."""
    rent = 0
    for i in range(1, horse_count + 1):
        if i <= 3:
            rent += STALL_RENT_TIER_1
        elif i <= 6:
            rent += STALL_RENT_TIER_2
        else:
            rent += STALL_RENT_TIER_3
    return rent


def calculate_start_fee(prize_pool: int) -> int:
    """Garanterad startpeng: 1 % av potten, minst 500 kr."""
    return max(START_FEE_MIN, int(prize_pool * START_FEE_PCT))


# ── Transaktioner ───────────────────────────────────────────────────────
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


async def _current_balance(db: AsyncSession, stable_id) -> int:
    """Läs saldot färskt från DB (triggern uppdaterar utanför sessionen)."""
    result = await db.execute(select(Stable.balance).where(Stable.id == stable_id))
    return result.scalar_one_or_none() or 0


# ── Veckokostnader ──────────────────────────────────────────────────────
async def deduct_weekly_stable_costs(db: AsyncSession, game_week: int) -> int:
    """Dra veckokostnader för ALLA stall. Anropas en gång per speldag-vecka.
    Returnerar totalt avdraget belopp i öre.
    """
    stables_result = await db.execute(select(Stable))
    stables = stables_result.scalars().all()
    total_deducted = 0

    for stable in stables:
        horse_count_result = await db.execute(
            select(sa_func.count(Horse.id)).where(Horse.stable_id == stable.id)
        )
        horse_count = horse_count_result.scalar() or 0

        if horse_count == 0 and not stable.is_npc:
            continue

        stall_cost = calculate_stall_rent(horse_count)
        feed_cost = FEED_COST_PER_HORSE * horse_count
        staff_cost = STAFF_COST_BASE

        contracts_result = await db.execute(
            select(DriverContract).where(
                DriverContract.stable_id == stable.id,
                DriverContract.is_active == True,
            )
        )
        driver_costs = sum(c.salary_per_week for c in contracts_result.scalars().all())

        total_cost = stall_cost + feed_cost + staff_cost + driver_costs
        if total_cost <= 0:
            continue

        parts = [
            f"stallhyra {horse_count} hästar {format_kr(stall_cost)}",
            f"foder {format_kr(feed_cost)}",
            f"personal {format_kr(staff_cost)}",
        ]
        if driver_costs > 0:
            parts.append(f"kusklöner {format_kr(driver_costs)}")

        await record_transaction(
            db, stable.id, -total_cost, "weekly_costs",
            f"Veckokostnader V{game_week} ({', '.join(parts)})",
            game_week,
        )
        total_deducted += total_cost

    await db.flush()
    if total_deducted > 0:
        logger.info(f"Weekly costs deducted for week {game_week}: {format_kr(total_deducted)} total")

    return total_deducted


async def calculate_weekly_cost_estimate(db: AsyncSession, stable_id) -> dict:
    """Uppskattade veckokostnader för ett stall (visning)."""
    horse_count_result = await db.execute(
        select(sa_func.count(Horse.id)).where(Horse.stable_id == stable_id)
    )
    horse_count = horse_count_result.scalar() or 0

    stall_cost = calculate_stall_rent(horse_count)
    feed_cost = FEED_COST_PER_HORSE * horse_count
    staff_cost = STAFF_COST_BASE

    contracts_result = await db.execute(
        select(DriverContract).where(
            DriverContract.stable_id == stable_id,
            DriverContract.is_active == True,
        )
    )
    driver_costs = sum(c.salary_per_week for c in contracts_result.scalars().all())

    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()

    interest = 0
    if stable:
        if stable.balance < 0:
            interest += int(abs(stable.balance) * OVERDRAFT_INTEREST_RATE)
        if (stable.loan_principal or 0) > 0:
            interest += int(stable.loan_principal * LOAN_INTEREST_RATE)

    total = stall_cost + feed_cost + staff_cost + driver_costs + interest

    return {
        "stall_rent": stall_cost,
        "feed": feed_cost,
        "staff": staff_cost,
        "driver_salaries": driver_costs,
        "interest": interest,
        "total": total,
        "horse_count": horse_count,
        "next_horse_rent": calculate_stall_rent(horse_count + 1) - stall_cost,
    }


# ── Startpeng & uppfödarpremie ──────────────────────────────────────────
async def pay_start_fee(
    db: AsyncSession, stable_id, prize_pool: int, race_name: str,
    game_week: int, race_id=None,
) -> int:
    """Garanterad startpeng till alla startande. Returnerar utbetalt belopp."""
    fee = calculate_start_fee(prize_pool)
    await record_transaction(
        db, stable_id, fee, "start_fee",
        f"Startpeng — {race_name}",
        game_week, reference_type="race", reference_id=race_id,
    )
    return fee


async def pay_breeder_premium(
    db: AsyncSession, horse, prize_money: int, race_name: str,
    game_week: int, race_id=None,
) -> int:
    """5 % uppfödarpremie till den som fött upp hästen — även efter försäljning."""
    breeder_id = getattr(horse, "breeder_stable_id", None)
    if not breeder_id or prize_money <= 0:
        return 0
    if breeder_id == horse.stable_id:
        return 0  # äger den redan, prispengen räcker

    breeder = await db.get(Stable, breeder_id)
    if not breeder or breeder.is_npc:
        return 0

    premium = int(prize_money * BREEDER_PREMIUM_PCT)
    if premium <= 0:
        return 0

    await record_transaction(
        db, breeder_id, premium, "breeder_premium",
        f"Uppfödarpremie — {horse.name} i {race_name}",
        game_week, reference_type="race", reference_id=race_id,
    )
    return premium


# ── Lån ─────────────────────────────────────────────────────────────────
async def take_loan(db: AsyncSession, stable_id, amount: int, game_week: int) -> dict:
    """Ta lån. Max 200 000 kr utestående, 3 %/vecka."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}
    if amount <= 0:
        return {"error": "Beloppet måste vara större än noll"}

    current = stable.loan_principal or 0
    headroom = MAX_LOAN - current
    if headroom <= 0:
        return {"error": f"Du har redan maximalt lån ({format_kr(MAX_LOAN)})"}
    if amount > headroom:
        return {"error": f"Du kan låna högst {format_kr(headroom)} till"}

    await record_transaction(
        db, stable_id, amount, "loan",
        f"Lån upptaget: {format_kr(amount)} (3 % ränta/vecka)",
        game_week,
    )
    stable.loan_principal = current + amount
    stable.loan_taken_week = game_week
    await db.flush()

    return {
        "success": True,
        "borrowed": amount,
        "loan_principal": stable.loan_principal,
        "weekly_interest": int(stable.loan_principal * LOAN_INTEREST_RATE),
        "balance": await _current_balance(db, stable_id),
    }


async def repay_loan(db: AsyncSession, stable_id, amount: int, game_week: int) -> dict:
    """Amortera på lånet."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    principal = stable.loan_principal or 0
    if principal <= 0:
        return {"error": "Du har inget lån att amortera"}
    if amount <= 0:
        return {"error": "Beloppet måste vara större än noll"}

    amount = min(amount, principal)
    balance = await _current_balance(db, stable_id)
    if balance < amount:
        return {"error": f"Otillräckligt saldo. Du har {format_kr(max(0, balance))}"}

    await record_transaction(
        db, stable_id, -amount, "loan_repayment",
        f"Amortering: {format_kr(amount)}",
        game_week,
    )
    stable.loan_principal = principal - amount
    if stable.loan_principal == 0:
        stable.loan_taken_week = None
    await db.flush()

    return {
        "success": True,
        "repaid": amount,
        "loan_principal": stable.loan_principal,
        "balance": await _current_balance(db, stable_id),
    }


# ── Veckovis skuldhantering ─────────────────────────────────────────────
async def process_weekly_debt(db: AsyncSession, game_week: int) -> dict:
    """Ränta, bankbrev, tvångsförsäljning och konkursgolv. En gång per vecka."""
    from app.services import event_service

    result = await db.execute(select(Stable).where(Stable.is_npc == False))
    stables = result.scalars().all()

    summary = {"interest_charged": 0, "warnings": 0, "forced_sales": 0, "restart_offers": 0}

    for stable in stables:
        balance = await _current_balance(db, stable.id)

        # 1. Låneränta
        principal = stable.loan_principal or 0
        if principal > 0:
            interest = int(principal * LOAN_INTEREST_RATE)
            if interest > 0:
                await record_transaction(
                    db, stable.id, -interest, "loan_interest",
                    f"Låneränta V{game_week}: 3 % av {format_kr(principal)}",
                    game_week,
                )
                summary["interest_charged"] += interest
                balance -= interest

        # 2. Övertrasseringsränta
        if balance < 0:
            overdraft = int(abs(balance) * OVERDRAFT_INTEREST_RATE)
            if overdraft > 0:
                await record_transaction(
                    db, stable.id, -overdraft, "debt_interest",
                    f"Övertrasseringsränta V{game_week}: 2 % av {format_kr(abs(balance))}",
                    game_week,
                )
                summary["interest_charged"] += overdraft
                balance -= overdraft

        # 3. Eskalering
        if balance >= 0:
            if stable.debt_warning_week or stable.forced_sale_deadline_week:
                stable.debt_warning_week = None
                stable.forced_sale_deadline_week = None
                await event_service.create_event(
                    db, stable.id, "finance", "Skulden är reglerad",
                    "Banken har avskrivit kravet. Ditt saldo är åter på plus.",
                    game_week,
                )
            continue

        # Bankbrev första gången saldot går minus
        if stable.debt_warning_week is None:
            stable.debt_warning_week = game_week
            summary["warnings"] += 1
            await event_service.create_event(
                db, stable.id, "finance", "Brev från banken",
                f"Ditt saldo är {format_kr(balance)}. Från och med nu debiteras "
                f"2 % ränta per vecka på skulden. Kontakta oss för lån om du "
                f"behöver överbrygga.",
                game_week,
            )

        # Krav på försäljning
        if balance <= FORCED_SALE_THRESHOLD and stable.forced_sale_deadline_week is None:
            stable.forced_sale_deadline_week = game_week + FORCED_SALE_GRACE_WEEKS
            await event_service.create_event(
                db, stable.id, "finance", "Krav: sälj en häst",
                f"Skulden överstiger {format_kr(abs(FORCED_SALE_THRESHOLD))}. "
                f"Sälj minst en häst före vecka {stable.forced_sale_deadline_week}, "
                f"annars tvångssäljer banken din sämsta häst för halva värdet.",
                game_week,
            )

        # Tvångsförsäljning
        if (
            stable.forced_sale_deadline_week is not None
            and game_week > stable.forced_sale_deadline_week
            and balance <= FORCED_SALE_THRESHOLD
        ):
            sold = await _forced_sale(db, stable, game_week)
            if sold:
                summary["forced_sales"] += 1
                balance = await _current_balance(db, stable.id)
                stable.forced_sale_deadline_week = (
                    game_week + FORCED_SALE_GRACE_WEEKS if balance <= FORCED_SALE_THRESHOLD else None
                )

        # Konkursgolv
        if balance <= BANKRUPTCY_FLOOR:
            topup = BANKRUPTCY_FLOOR - balance
            if topup > 0:
                await record_transaction(
                    db, stable.id, topup, "bankruptcy_protection",
                    "Konkursskydd: saldot kan inte gå under −300 000 kr",
                    game_week,
                )
            summary["restart_offers"] += 1
            await event_service.create_event(
                db, stable.id, "finance", "Nystart erbjuds",
                "Du har nått skuldgolvet. Under Ekonomi kan du göra en nystart: "
                "behåll en häst, skulden nollställs, du tappar 20 i rykte.",
                game_week,
            )

    await db.flush()
    return summary


async def _forced_sale(db: AsyncSession, stable: Stable, game_week: int) -> bool:
    """Banken säljer stallets sämsta häst för 50 % av värdet."""
    from app.services import event_service
    from app.services.valuation_service import calculate_horse_value

    result = await db.execute(
        select(Horse).where(
            Horse.stable_id == stable.id,
            Horse.status != HorseStatus.RETIRED,
        )
    )
    horses = result.scalars().all()
    if len(horses) <= 1:
        return False  # Aldrig ta sista hästen

    worst = min(horses, key=calculate_horse_value)
    payout = int(calculate_horse_value(worst) * FORCED_SALE_VALUE_PCT)

    await record_transaction(
        db, stable.id, payout, "forced_sale",
        f"Tvångsförsäljning: {worst.name} såld för {format_kr(payout)} (50 % av värdet)",
        game_week,
    )
    await event_service.create_event(
        db, stable.id, "finance", f"{worst.name} tvångssåld",
        f"Banken har sålt {worst.name} för {format_kr(payout)} — halva marknadsvärdet. "
        f"Sälj själv nästa gång, då får du fullt pris.",
        game_week,
    )
    await db.delete(worst)
    await db.flush()
    logger.info(f"Forced sale: {worst.name} from stable {stable.id} for {format_kr(payout)}")
    return True


async def restart_stable(db: AsyncSession, stable_id, game_week: int, keep_horse_id=None) -> dict:
    """Nystart: behåll en häst, nollställ skuld och lån, −20 rykte."""
    from app.services import event_service
    from app.services.valuation_service import calculate_horse_value

    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    balance = await _current_balance(db, stable_id)
    if balance > BANKRUPTCY_FLOOR:
        return {"error": "Nystart kan bara göras när du nått skuldgolvet (−300 000 kr)"}

    result = await db.execute(select(Horse).where(Horse.stable_id == stable_id))
    horses = result.scalars().all()

    keeper = None
    if keep_horse_id:
        keeper = next((h for h in horses if str(h.id) == str(keep_horse_id)), None)
    if keeper is None and horses:
        keeper = max(horses, key=calculate_horse_value)

    for horse in horses:
        if keeper is None or horse.id != keeper.id:
            await db.delete(horse)

    # Nollställ ekonomin
    if balance != 0:
        await record_transaction(
            db, stable_id, -balance, "restart",
            "Nystart: skulden avskriven, saldot nollställt",
            game_week,
        )
    stable.loan_principal = 0
    stable.loan_taken_week = None
    stable.forced_sale_deadline_week = None
    stable.debt_warning_week = None
    stable.reputation = max(0, (stable.reputation or 0) - RESTART_REPUTATION_PENALTY)
    stable.restarts_count = (stable.restarts_count or 0) + 1
    await db.flush()

    await event_service.create_event(
        db, stable_id, "finance", "Nystart genomförd",
        f"Skulden är avskriven och du börjar om med {keeper.name if keeper else 'ett tomt stall'}. "
        f"Ryktet sjönk med {RESTART_REPUTATION_PENALTY}.",
        game_week,
    )

    return {
        "success": True,
        "kept_horse": keeper.name if keeper else None,
        "reputation": stable.reputation,
        "balance": await _current_balance(db, stable_id),
    }


# ── Översikt ────────────────────────────────────────────────────────────
async def get_debt_status(db: AsyncSession, stable_id) -> dict:
    """Skuldläge för UI-varningar."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {}

    # Läs saldot färskt — DB-triggern uppdaterar utanför ORM-sessionen,
    # så stable.balance kan vara inaktuellt efter en transaktion i samma request.
    balance = await _current_balance(db, stable_id)
    principal = stable.loan_principal or 0

    if balance <= BANKRUPTCY_FLOOR:
        level, label = "critical", "Skuldgolv nått — nystart krävs"
    elif balance <= FORCED_SALE_THRESHOLD:
        level, label = "severe", "Tvångsförsäljning hotar"
    elif balance < 0:
        level, label = "warning", "Övertrasserat konto"
    elif principal > 0:
        level, label = "loan", "Lån löper"
    else:
        level, label = "ok", "Ekonomin är i balans"

    return {
        "level": level,
        "label": label,
        "balance": balance,
        "loan_principal": principal,
        "loan_headroom": max(0, MAX_LOAN - principal),
        "max_loan": MAX_LOAN,
        "weekly_loan_interest": int(principal * LOAN_INTEREST_RATE),
        "weekly_overdraft_interest": int(abs(balance) * OVERDRAFT_INTEREST_RATE) if balance < 0 else 0,
        "forced_sale_deadline_week": stable.forced_sale_deadline_week,
        "bankruptcy_floor": BANKRUPTCY_FLOOR,
        "forced_sale_threshold": FORCED_SALE_THRESHOLD,
        "can_restart": balance <= BANKRUPTCY_FLOOR,
    }


async def get_financial_overview(db: AsyncSession, stable_id):
    result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = result.scalar_one()

    weekly_costs = await calculate_weekly_cost_estimate(db, stable_id)

    txns = await db.execute(
        select(Transaction)
        .where(Transaction.stable_id == stable_id)
        .order_by(Transaction.created_at.desc())
        .limit(100)
    )
    transactions = txns.scalars().all()

    income = sum(t.amount for t in transactions if t.amount > 0)
    expenses = sum(t.amount for t in transactions if t.amount < 0)

    # Intäkter/kostnader per kategori (senaste 100 transaktionerna)
    by_category: dict[str, int] = {}
    for t in transactions:
        by_category[t.category] = by_category.get(t.category, 0) + t.amount

    return {
        "balance": stable.balance,
        "weekly_summary": {
            "income": {"total": income},
            "expenses": {"total": abs(expenses)},
            "net": income + expenses,
        },
        "weekly_costs": weekly_costs,
        "by_category": by_category,
        "debt": await get_debt_status(db, stable_id),
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
