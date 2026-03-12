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


async def seed_npc_listings(db: AsyncSession, game_week: int, count: int = 3):
    """Create NPC horse listings to populate the market.
    Called during game init or periodically to keep the market active.
    """
    import random

    # Find NPC horses not already listed
    listed_result = await db.execute(
        select(AuctionListing.horse_id).where(AuctionListing.status == "active")
    )
    listed_ids = {row[0] for row in listed_result.all()}

    npc_horses_result = await db.execute(
        select(Horse)
        .where(
            Horse.is_npc == True,
            Horse.status == "ready",
            Horse.id.notin_(listed_ids) if listed_ids else True,
        )
        .order_by(Horse.total_earnings.desc())
        .limit(count * 2)  # get extra to select from
    )
    npc_horses = npc_horses_result.scalars().all()

    if not npc_horses:
        return 0

    rng = random.Random(game_week * 777)
    selected = rng.sample(npc_horses, min(count, len(npc_horses)))
    created = 0

    for horse in selected:
        # Price based on stats and career
        avg_stat = (horse.speed + horse.endurance + horse.mentality +
                    horse.start_ability + horse.sprint_strength +
                    horse.balance + horse.strength) / 7
        base_price = int(avg_stat * 50_000)
        career_bonus = horse.total_wins * 200_000 + horse.total_starts * 30_000
        starting_price = base_price + career_bonus + rng.randint(-500_000, 500_000)
        starting_price = max(500_000, starting_price)  # Minimum 500k
        buyout_price = int(starting_price * rng.uniform(1.5, 2.5))

        listing = AuctionListing(
            horse_id=horse.id,
            seller_stable_id=horse.stable_id,
            starting_price=starting_price,
            buyout_price=buyout_price,
            status="active",
            listed_game_week=game_week,
            expires_game_week=game_week + 1,  # ~5 days
        )
        db.add(listing)
        created += 1

    await db.flush()
    return created
