"""TravManager — Horse Market / Auction Service

Handles listing horses for sale, browsing the market, bidding, and completing sales.
"""
import logging
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.horse import Horse
from app.models.stable import Stable
from app.models.market import AuctionListing, AuctionBid
from app.services import finance_service

logger = logging.getLogger(__name__)


async def list_horse_for_sale(
    db: AsyncSession, stable_id, horse_id,
    starting_price: int, buyout_price: int | None,
    game_week: int,
) -> dict:
    """List a horse for sale on the market."""
    # Verify ownership
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte i ditt stall"}

    if horse.is_npc:
        return {"error": "NPC-hästar kan inte säljas"}

    # Check not already listed
    existing = await db.execute(
        select(AuctionListing).where(
            AuctionListing.horse_id == horse_id,
            AuctionListing.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        return {"error": "Hästen är redan till salu"}

    if starting_price < 100_000:
        return {"error": "Minsta utropspris är 100 000 öre"}

    if buyout_price and buyout_price < starting_price:
        return {"error": "Köp direkt-pris måste vara högre än utropspriset"}

    listing = AuctionListing(
        horse_id=horse_id,
        seller_stable_id=stable_id,
        starting_price=starting_price,
        buyout_price=buyout_price,
        current_bid=0,
        status="active",
        listed_game_week=game_week,
        expires_game_week=game_week + 1,  # ~5 days (expires next week)
    )
    db.add(listing)
    await db.flush()

    return {
        "success": True,
        "listing_id": str(listing.id),
        "horse_name": horse.name,
        "starting_price": starting_price,
        "buyout_price": buyout_price,
        "expires_week": listing.expires_game_week,
    }


async def get_market_listings(db: AsyncSession, stable_id=None, current_game_week: int = 1) -> list[dict]:
    """Get all active market listings, filtering out expired ones."""
    q = (
        select(AuctionListing)
        .options(selectinload(AuctionListing.horse), selectinload(AuctionListing.seller_stable))
        .where(AuctionListing.status == "active")
        .order_by(AuctionListing.created_at.desc())
    )
    result = await db.execute(q)
    listings = result.scalars().all()

    items = []
    for l in listings:
        # Skip expired listings (will be processed by ticker)
        if l.expires_game_week <= current_game_week:
            continue

        h = l.horse
        weeks_remaining = l.expires_game_week - current_game_week
        days_remaining = max(1, weeks_remaining * 7)  # approx days

        items.append({
            "id": str(l.id),
            "horse": {
                "id": str(h.id),
                "name": h.name,
                "gender": h.gender.value,
                "age_weeks": h.age_game_weeks,
                "status": h.status.value,
                "speed": h.speed,
                "endurance": h.endurance,
                "mentality": h.mentality,
                "start_ability": h.start_ability,
                "sprint_strength": h.sprint_strength,
                "balance": h.balance,
                "strength": h.strength,
                "total_starts": h.total_starts,
                "total_wins": h.total_wins,
                "total_earnings": h.total_earnings,
                "best_km_time": h.best_km_time_display,
                "distance_optimum": h.distance_optimum,
                "form": h.form,
            },
            "seller_name": l.seller_stable.name if l.seller_stable else "Okänt",
            "starting_price": l.starting_price,
            "buyout_price": l.buyout_price,
            "current_bid": l.current_bid,
            "total_bids": 0,  # filled below
            "expires_week": l.expires_game_week,
            "listed_week": l.listed_game_week,
            "days_remaining": days_remaining,
            "is_own": str(l.seller_stable_id) == str(stable_id) if stable_id else False,
            # Marknadsvärdering — låter spelaren se om priset är rimligt
            "estimated_value": getattr(l, "estimated_value", None),
            "is_bargain": bool(getattr(l, "is_bargain", False)),
            "value_diff_pct": (
                round((l.starting_price - l.estimated_value) / l.estimated_value * 100)
                if getattr(l, "estimated_value", None) else None
            ),
        })

    # Count bids per listing
    for item in items:
        bids_result = await db.execute(
            select(AuctionBid).where(AuctionBid.listing_id == item["id"])
        )
        item["total_bids"] = len(bids_result.scalars().all())

    return items


async def place_bid(
    db: AsyncSession, stable_id, listing_id, amount: int, game_week: int,
) -> dict:
    """Place a bid on a horse listing."""
    listing_result = await db.execute(
        select(AuctionListing)
        .options(selectinload(AuctionListing.horse))
        .where(AuctionListing.id == listing_id, AuctionListing.status == "active")
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        return {"error": "Auktionen hittades inte eller har avslutats"}

    # Can't bid on own horse
    if str(listing.seller_stable_id) == str(stable_id):
        return {"error": "Du kan inte bjuda på din egen häst"}

    # Must be higher than current bid and starting price
    min_bid = max(listing.starting_price, listing.current_bid + 50_000)
    if amount < min_bid:
        return {"error": f"Minsta bud är {min_bid} öre"}

    # Check buyer balance
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable or stable.balance < amount:
        return {"error": "Otillräckligt saldo"}

    # Check if buyout
    is_buyout = listing.buyout_price and amount >= listing.buyout_price

    # Record bid
    bid = AuctionBid(
        listing_id=listing_id,
        bidder_stable_id=stable_id,
        amount=amount,
        game_week=game_week,
    )
    db.add(bid)

    listing.current_bid = amount
    listing.current_bidder_id = stable_id

    if is_buyout:
        # Instant purchase
        return await _complete_sale(db, listing, stable_id, amount, game_week)

    await db.flush()
    return {
        "success": True,
        "bid_amount": amount,
        "horse_name": listing.horse.name,
        "is_buyout": False,
    }


async def buyout_horse(
    db: AsyncSession, stable_id, listing_id, game_week: int,
) -> dict:
    """Buy a horse at the buyout price immediately."""
    listing_result = await db.execute(
        select(AuctionListing)
        .options(selectinload(AuctionListing.horse))
        .where(AuctionListing.id == listing_id, AuctionListing.status == "active")
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        return {"error": "Auktionen hittades inte"}

    if not listing.buyout_price:
        return {"error": "Denna auktion har inget köp direkt-pris"}

    if str(listing.seller_stable_id) == str(stable_id):
        return {"error": "Du kan inte köpa din egen häst"}

    # Check balance
    stable_result = await db.execute(select(Stable).where(Stable.id == stable_id))
    stable = stable_result.scalar_one_or_none()
    if not stable or stable.balance < listing.buyout_price:
        return {"error": "Otillräckligt saldo"}

    # Check stable capacity (box limit)
    from sqlalchemy import func as sqlfunc
    horse_count_result = await db.execute(
        select(sqlfunc.count(Horse.id)).where(Horse.stable_id == stable_id)
    )
    horse_count = horse_count_result.scalar() or 0
    max_horses = stable.max_horses or 3
    if horse_count >= max_horses:
        return {"error": f"Stallet är fullt ({horse_count}/{max_horses} boxar). Uppgradera dina boxar först."}

    return await _complete_sale(db, listing, stable_id, listing.buyout_price, game_week)


async def _complete_sale(
    db: AsyncSession, listing: AuctionListing,
    buyer_stable_id, price: int, game_week: int,
) -> dict:
    """Complete a horse sale — transfer ownership and money."""
    horse_result = await db.execute(select(Horse).where(Horse.id == listing.horse_id))
    horse = horse_result.scalar_one()

    seller_stable_id = listing.seller_stable_id

    # Deduct from buyer
    await finance_service.record_transaction(
        db, buyer_stable_id, -price, "horse_purchase",
        f"Köp av {horse.name}", game_week,
    )

    # Pay seller (minus 10% market fee)
    fee = int(price * 0.10)
    seller_amount = price - fee
    await finance_service.record_transaction(
        db, seller_stable_id, seller_amount, "horse_sale",
        f"Försäljning av {horse.name} (10% avgift)", game_week,
    )

    # Transfer horse
    horse.stable_id = buyer_stable_id
    horse.is_npc = False  # In case NPC horse was listed

    # Close listing
    listing.status = "sold"
    listing.current_bid = price
    listing.current_bidder_id = buyer_stable_id

    await db.flush()

    return {
        "success": True,
        "is_buyout": True,
        "horse_name": horse.name,
        "price": price,
        "fee": fee,
        "seller_receives": seller_amount,
    }


async def accept_bid(db: AsyncSession, stable_id, listing_id, game_week: int) -> dict:
    """Accept the current highest bid on a listing (early sale)."""
    listing_result = await db.execute(
        select(AuctionListing)
        .options(selectinload(AuctionListing.horse))
        .where(
            AuctionListing.id == listing_id,
            AuctionListing.seller_stable_id == stable_id,
            AuctionListing.status == "active",
        )
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        return {"error": "Auktionen hittades inte"}

    if listing.current_bid <= 0 or not listing.current_bidder_id:
        return {"error": "Inga bud att acceptera"}

    # Check buyer capacity
    from sqlalchemy import func as sqlfunc
    buyer_stable_result = await db.execute(
        select(Stable).where(Stable.id == listing.current_bidder_id)
    )
    buyer_stable = buyer_stable_result.scalar_one_or_none()
    horse_count_result = await db.execute(
        select(sqlfunc.count(Horse.id)).where(Horse.stable_id == listing.current_bidder_id)
    )
    horse_count = horse_count_result.scalar() or 0
    max_horses = (buyer_stable.max_horses if buyer_stable else 3) or 3
    if horse_count >= max_horses:
        return {"error": "Köparens stall är fullt — kan inte godkänna budet"}

    return await _complete_sale(db, listing, listing.current_bidder_id, listing.current_bid, game_week)


async def give_away_horse(db: AsyncSession, stable_id, horse_id) -> dict:
    """Give away a horse (release from stable). Horse is removed from the stable."""
    horse_result = await db.execute(
        select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen hittades inte i ditt stall"}

    if horse.is_npc:
        return {"error": "NPC-hästar kan inte ges bort"}

    # Check not listed
    existing = await db.execute(
        select(AuctionListing).where(
            AuctionListing.horse_id == horse_id,
            AuctionListing.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        return {"error": "Hästen är listad på marknaden — avbryt auktionen först"}

    from app.models.enums import HorseStatus
    horse_name = horse.name

    # Mark horse as retired / remove from stable
    horse.status = HorseStatus.RETIRED
    horse.is_npc = True  # Convert to NPC pool
    # Move to a random NPC stable
    npc_stable_result = await db.execute(
        select(Stable).where(Stable.is_npc == True).limit(1)
    )
    npc_stable = npc_stable_result.scalar_one_or_none()
    if npc_stable:
        horse.stable_id = npc_stable.id
        horse.status = HorseStatus.READY
    else:
        horse.status = HorseStatus.RETIRED

    await db.flush()
    return {
        "success": True,
        "message": f"{horse_name} har getts bort",
        "horse_name": horse_name,
    }


async def cancel_listing(db: AsyncSession, stable_id, listing_id) -> dict:
    """Cancel an active listing (only if no bids)."""
    listing_result = await db.execute(
        select(AuctionListing).where(
            AuctionListing.id == listing_id,
            AuctionListing.seller_stable_id == stable_id,
            AuctionListing.status == "active",
        )
    )
    listing = listing_result.scalar_one_or_none()
    if not listing:
        return {"error": "Auktionen hittades inte"}

    if listing.current_bid > 0:
        return {"error": "Kan inte avbryta en auktion med bud"}

    listing.status = "cancelled"
    await db.flush()
    return {"success": True, "message": "Auktionen avbruten"}


async def process_expired_auctions(db: AsyncSession, game_week: int) -> int:
    """Process auctions that have expired. Called by the ticker.
    If there's a winning bid, complete the sale. Otherwise, mark as expired.
    """
    expired_result = await db.execute(
        select(AuctionListing)
        .options(selectinload(AuctionListing.horse))
        .where(
            AuctionListing.status == "active",
            AuctionListing.expires_game_week <= game_week,
        )
    )
    expired = expired_result.scalars().all()
    processed = 0

    for listing in expired:
        if listing.current_bid > 0 and listing.current_bidder_id:
            # Check buyer capacity before completing sale
            from sqlalchemy import func as sqlfunc
            buyer_stable_result = await db.execute(
                select(Stable).where(Stable.id == listing.current_bidder_id)
            )
            buyer_stable = buyer_stable_result.scalar_one_or_none()
            horse_count_result = await db.execute(
                select(sqlfunc.count(Horse.id)).where(Horse.stable_id == listing.current_bidder_id)
            )
            horse_count = horse_count_result.scalar() or 0
            max_horses = (buyer_stable.max_horses if buyer_stable else 3) or 3

            if horse_count >= max_horses:
                # Buyer's stable is full — refund bid, expire listing
                listing.status = "expired"
                logger.warning(
                    f"Auction {listing.id}: buyer stable full ({horse_count}/{max_horses}), "
                    f"refunding bid and expiring listing"
                )
            else:
                # Complete the sale to highest bidder
                await _complete_sale(
                    db, listing, listing.current_bidder_id,
                    listing.current_bid, game_week,
                )
                processed += 1
        else:
            listing.status = "expired"

    await db.flush()
    return processed


async def get_horse_public_profile(db: AsyncSession, horse_id) -> dict | None:
    """Get public profile for any horse (limited stats for non-owned)."""
    from app.models.horse import Bloodline

    horse_result = await db.execute(
        select(Horse)
        .options(selectinload(Horse.stable), selectinload(Horse.bloodline))
        .where(Horse.id == horse_id)
    )
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return None

    # Get race history from race entries
    from app.models.race import RaceEntry, Race, RaceSession
    from sqlalchemy.orm import selectinload as sil

    entries_result = await db.execute(
        select(RaceEntry)
        .options(sil(RaceEntry.race).subqueryload(Race.session))
        .where(
            RaceEntry.horse_id == horse_id,
            RaceEntry.is_scratched == False,
        )
        .limit(30)
    )
    entries = entries_result.scalars().all()

    race_history = []
    for entry in entries:
        race = entry.race
        if race and race.is_finished and entry.finish_position is not None:
            race_history.append({
                "race_id": str(race.id),
                "race_name": race.race_name,
                "distance": race.distance,
                "position": entry.finish_position,
                "km_time": entry.km_time_display or "",
                "prize": entry.prize_money or 0,
                "game_week": race.session.game_week if race.session else None,
            })

    return {
        "id": str(horse.id),
        "name": horse.name,
        "gender": horse.gender.value,
        "age_weeks": horse.age_game_weeks,
        "status": horse.status.value,
        "stable_name": horse.stable.name if horse.stable else "Okänt",
        "stable_id": str(horse.stable_id),
        "is_npc": horse.is_npc,
        # Public stats — always visible
        "speed": horse.speed,
        "endurance": horse.endurance,
        "mentality": horse.mentality,
        "start_ability": horse.start_ability,
        "sprint_strength": horse.sprint_strength,
        "balance": horse.balance,
        "strength": horse.strength,
        "form": horse.form,
        "condition": horse.condition,
        # Career stats
        "total_starts": horse.total_starts,
        "total_wins": horse.total_wins,
        "total_seconds": horse.total_seconds,
        "total_thirds": horse.total_thirds,
        "total_dq": horse.total_dq,
        "total_earnings": horse.total_earnings,
        "best_km_time": horse.best_km_time_display,
        "distance_optimum": horse.distance_optimum,
        # Bloodline
        "bloodline": horse.bloodline.name if horse.bloodline else None,
        # Race history (sorted by game_week descending)
        "race_history": sorted(race_history, key=lambda r: r.get("game_week") or 0, reverse=True),
    }


async def seed_npc_listings(db: AsyncSession, game_week: int, count: int = 3,
                            total_day: int = None, rng=None):
    """Lägg upp AI-hästar till salu. Priset utgår från hästens beräknade
    marknadsvärde, och ibland dyker ett fynd upp: en häst med en dold
    toppegenskap som säljs under värde.
    """
    import random
    from app.services.valuation_service import calculate_horse_value

    rng = rng or random.Random(game_week * 777 + (total_day or 0))

    listed_result = await db.execute(
        select(AuctionListing.horse_id).where(AuctionListing.status == "active")
    )
    listed_ids = {row[0] for row in listed_result.all()}

    q = select(Horse).where(Horse.is_npc == True, Horse.status == "ready")
    if listed_ids:
        q = q.where(Horse.id.notin_(listed_ids))
    npc_horses = (await db.execute(q.limit(count * 6))).scalars().all()
    if not npc_horses:
        return 0

    selected = rng.sample(npc_horses, min(count, len(npc_horses)))
    created = 0

    for horse in selected:
        value = calculate_horse_value(horse)

        # 10 % chans per dag att ett fynd dyker upp
        is_bargain = rng.random() < 0.10
        if is_bargain:
            # Fyndet har en dold toppegenskap och säljs 30-45 % under värde
            await _grant_hidden_gem(db, horse, rng)
            starting_price = int(value * rng.uniform(0.55, 0.70))
        else:
            starting_price = int(value * rng.uniform(0.85, 1.05))

        starting_price = max(300_000, starting_price)
        buyout_price = int(starting_price * rng.uniform(1.4, 2.0))

        listing = AuctionListing(
            horse_id=horse.id,
            seller_stable_id=horse.stable_id,
            starting_price=starting_price,
            buyout_price=buyout_price,
            status="active",
            listed_game_week=game_week,
            expires_game_week=game_week + 1,
            is_bargain=is_bargain,
            estimated_value=value,
            # AI:n slutar bjuda strax under värdet — den vill också ha marginal
            ai_max_bid=int(value * rng.uniform(0.80, 0.98)),
            listed_total_day=total_day,
            expires_total_day=(total_day + 1) if total_day else None,
        )
        db.add(listing)
        created += 1

    await db.flush()
    return created


async def _grant_hidden_gem(db: AsyncSession, horse, rng):
    """Ge fyndhästen en dold toppegenskap som gör den värd mer än priset."""
    try:
        from app.services.hidden_properties_service import ensure_hidden_properties
    except ImportError:
        return
    props = await ensure_hidden_properties(db, horse.id)
    if not props:
        return
    gem = rng.choice(["sprint_gear", "barefoot", "curves", "homestretch"])
    if gem == "sprint_gear":
        props.hidden_sprint_gear = True
    elif gem == "barefoot":
        props.barefoot_affinity = max(props.barefoot_affinity or 0, rng.randint(20, 30))
    elif gem == "curves":
        props.tight_curve_ability = max(props.tight_curve_ability or 0, rng.randint(15, 20))
    else:
        props.long_homestretch_affinity = max(
            props.long_homestretch_affinity or 0, rng.randint(15, 20)
        )
    await db.flush()


async def refresh_market(db: AsyncSession, game_week: int, total_day: int,
                         target_listings: int = 8) -> dict:
    """Rotera marknaden dagligen så den alltid har 6-10 hästar till salu."""
    import random

    active = (await db.execute(
        select(AuctionListing).where(AuctionListing.status == "active")
    )).scalars().all()

    rng = random.Random(total_day * 9173)

    # Låt gamla listningar löpa ut
    expired = 0
    for listing in active:
        exp_day = getattr(listing, "expires_total_day", None)
        if exp_day is not None and total_day > exp_day and not listing.current_bid:
            listing.status = "expired"
            expired += 1

    remaining = [l for l in active if l.status == "active"]
    wanted = rng.randint(6, 10)
    needed = max(0, wanted - len(remaining))

    created = 0
    if needed:
        created = await seed_npc_listings(
            db, game_week, count=needed, total_day=total_day, rng=rng
        )

    await db.flush()
    return {"created": created, "expired": expired, "active": len(remaining) + created}


async def run_ai_bidding(db: AsyncSession, total_day: int) -> int:
    """AI-stall bjuder mot spelaren på pågående auktioner."""
    import random

    listings = (await db.execute(
        select(AuctionListing).where(AuctionListing.status == "active")
    )).scalars().all()

    rng = random.Random(total_day * 4211)
    bids = 0

    for listing in listings:
        ai_max = getattr(listing, "ai_max_bid", None)
        if not ai_max:
            continue
        current = listing.current_bid or 0
        if current == 0:
            continue  # AI:n öppnar inte budgivningen — spelaren får första ordet
        if listing.current_bidder_id is None:
            continue
        # AI:n bjuder bara mot någon annan, och bara upp till sitt tak
        bidder = await db.get(Stable, listing.current_bidder_id)
        if bidder and bidder.is_npc:
            continue
        if rng.random() > 0.55:
            continue

        next_bid = current + max(50_000, int(current * rng.uniform(0.04, 0.12)))
        if next_bid > ai_max:
            continue

        listing.current_bid = next_bid
        listing.current_bidder_id = listing.seller_stable_id
        bids += 1

    await db.flush()
    return bids
