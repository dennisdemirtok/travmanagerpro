"""TravManager — Premium, kosmetik och säsongspass (sprint 9, DEL G)

Grundregel från spec: ALDRIG fart eller stats för pengar.
Allt som säljs är utrymme, historik, analys och utseende.
Gratisspelare har full spelmekanik.

VIKTIGT: ingen betalleverantör är inkopplad. `grant_*`-funktionerna är
rättighetstilldelning och måste anropas från ett verifierat köpflöde
(Stripe eller motsvarande) innan lansering.
"""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stable import Stable
from app.models.cosmetic import CosmeticUnlock
from app.models.race import RaceResultSummary
from app.services import event_service

logger = logging.getLogger(__name__)

FREE_BOXES = 3
PREMIUM_EXTRA_BOXES = 6
PREMIUM_WEEKS = 4          # en månad ≈ fyra spelveckor
SEASON_PASS_LENGTH = 10    # en säsong

PREMIUM_PRICE_SEK = 79
SEASON_PASS_PRICE_SEK = 49

PREMIUM_FEATURES = [
    ("boxes", "6 extra boxar", f"{FREE_BOXES} → {FREE_BOXES + PREMIUM_EXTRA_BOXES} hästar"),
    ("diary_full", "Full hästdagbok", "All historik plus export"),
    ("advanced_stats", "Avancerad statistik", "Motståndaranalys och taktikhistorik"),
    ("second_stable", "Andra stall", "Driv två stall parallellt"),
    ("season_archive", "Säsongsarkiv", "Alla tidigare säsonger sparade"),
    ("named_contracts", "Namngivna kuskavtal", "Bind kuskar över hela säsongen"),
]

# Kosmetik — engångsköp, påverkar bara utseende
COSMETICS = [
    # (nyckel, typ, namn, beskrivning, pris i kr, värde)
    ("color_gold", "color", "Guld & svart", "Klassisk stallfärg", 0, "#D4A853"),
    ("color_royal", "color", "Kungsblå", "Syns tydligt i banan", 19, "#4C6FE7"),
    ("color_crimson", "color", "Karmosin", "Djupröd stalldress", 19, "#E63946"),
    ("color_forest", "color", "Skogsgrön", "Lugn och distinkt", 19, "#2A9D8F"),
    ("color_violet", "color", "Violett", "Sticker ut i fältet", 29, "#9C6ADE"),
    ("color_copper", "color", "Koppar", "Varm metallton", 29, "#BC6C25"),
    ("sulky_classic", "sulky", "Klassisk sulky", "Standardmodell", 0, "classic"),
    ("sulky_carbon", "sulky", "Kolfibersulky", "Matt svart finish", 39, "carbon"),
    ("sulky_retro", "sulky", "Retrosulky", "Träpaneler och mässing", 29, "retro"),
    ("banner_default", "banner", "Standardbanderoll", "Enkel och ren", 0, "default"),
    ("banner_champion", "banner", "Mästarbanderoll", "Lagerkrans i guld", 49, "champion"),
    ("banner_stable", "banner", "Stallbanderoll", "Din stallfärg i stor skala", 29, "stable"),
]

COSMETIC_BY_KEY = {c[0]: c for c in COSMETICS}
FREE_COSMETICS = {c[0] for c in COSMETICS if c[4] == 0}

# Säsongspassets belöningsstege. Gratisspåret finns alltid.
SEASON_PASS_LADDER = [
    # (poäng, gratisbelöning, premiumbelöning)
    (10, {"type": "money", "amount": 500_000, "label": "5 000 kr"},
         {"type": "cosmetic", "item": "color_royal", "label": "Stallfärg Kungsblå"}),
    (25, None,
         {"type": "money", "amount": 1_500_000, "label": "15 000 kr"}),
    (45, {"type": "scout", "amount": 1, "label": "1 scoutrapport"},
         {"type": "cosmetic", "item": "sulky_retro", "label": "Retrosulky"}),
    (70, None,
         {"type": "money", "amount": 3_000_000, "label": "30 000 kr"}),
    (100, {"type": "money", "amount": 1_000_000, "label": "10 000 kr"},
          {"type": "cosmetic", "item": "banner_champion", "label": "Mästarbanderoll"}),
    (140, None,
          {"type": "cosmetic", "item": "color_violet", "label": "Stallfärg Violett"}),
]


def is_premium(stable: Stable, current_week: int) -> bool:
    until = stable.premium_until_week
    return bool(until and until >= current_week)


def max_boxes(stable: Stable, current_week: int) -> int:
    """Fria boxar plus ev. uppgraderingar plus premiumbonus."""
    base = stable.max_horses or FREE_BOXES
    if is_premium(stable, current_week):
        return base + PREMIUM_EXTRA_BOXES
    return base


async def get_status(db: AsyncSession, stable_id, current_week: int) -> dict:
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    unlocked = {
        row.item_key for row in (await db.execute(
            select(CosmeticUnlock).where(CosmeticUnlock.stable_id == stable_id)
        )).scalars().all()
    } | FREE_COSMETICS

    premium = is_premium(stable, current_week)
    return {
        "is_premium": premium,
        "premium_until_week": stable.premium_until_week,
        "weeks_remaining": max(0, (stable.premium_until_week or 0) - current_week),
        "price_sek": PREMIUM_PRICE_SEK,
        "features": [
            {"key": k, "title": t, "detail": d} for k, t, d in PREMIUM_FEATURES
        ],
        "boxes": {
            "base": stable.max_horses or FREE_BOXES,
            "effective": max_boxes(stable, current_week),
            "premium_bonus": PREMIUM_EXTRA_BOXES if premium else 0,
        },
        "equipped": {
            "color": stable.stable_color,
            "color_secondary": stable.stable_color_secondary,
            "sulky": stable.sulky_design,
            "banner": stable.banner,
        },
        "cosmetics": [
            {
                "key": k, "type": t, "name": n, "detail": d,
                "price_sek": p, "value": v,
                "unlocked": k in unlocked,
            }
            for k, t, n, d, p, v in COSMETICS
        ],
        "payment_configured": False,
        "note": (
            "Ingen betalleverantör är inkopplad ännu. Rättigheterna fungerar, "
            "men köpflödet måste kopplas till en riktig betaltjänst före lansering."
        ),
    }


async def equip_cosmetic(db: AsyncSession, stable_id, item_key: str, current_week: int) -> dict:
    item = COSMETIC_BY_KEY.get(item_key)
    if not item:
        return {"error": f"Okänt kosmetiskt föremål: {item_key}"}

    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    if item[4] > 0:
        owned = (await db.execute(
            select(CosmeticUnlock).where(
                CosmeticUnlock.stable_id == stable_id,
                CosmeticUnlock.item_key == item_key,
            )
        )).scalar_one_or_none()
        if not owned:
            return {"error": f"{item[2]} är inte upplåst än."}

    kind, value = item[1], item[5]
    if kind == "color":
        stable.stable_color = value
    elif kind == "sulky":
        stable.sulky_design = value
    elif kind == "banner":
        stable.banner = value
    await db.flush()

    return {"success": True, "equipped": item_key, "type": kind, "value": value}


async def grant_premium(db: AsyncSession, stable_id, current_week: int,
                        weeks: int = PREMIUM_WEEKS) -> dict:
    """Tilldela premium. Anropas EFTER verifierad betalning."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}
    start = max(current_week, stable.premium_until_week or 0)
    stable.premium_until_week = start + weeks
    await db.flush()
    await event_service.create_event(
        db, stable_id, "system", "Premium aktiverat",
        f"Du har premium i {weeks} veckor. {PREMIUM_EXTRA_BOXES} extra boxar, "
        f"full hästdagbok och avancerad statistik är upplåsta.",
        current_week,
    )
    return {"success": True, "premium_until_week": stable.premium_until_week}


async def grant_cosmetic(db: AsyncSession, stable_id, item_key: str,
                         source: str = "purchase") -> dict:
    """Lås upp kosmetik. Anropas EFTER verifierad betalning eller från passet."""
    item = COSMETIC_BY_KEY.get(item_key)
    if not item:
        return {"error": f"Okänt kosmetiskt föremål: {item_key}"}
    existing = (await db.execute(
        select(CosmeticUnlock).where(
            CosmeticUnlock.stable_id == stable_id,
            CosmeticUnlock.item_key == item_key,
        )
    )).scalar_one_or_none()
    if existing:
        return {"success": True, "already_owned": True}
    db.add(CosmeticUnlock(stable_id=stable_id, item_key=item_key, source=source))
    await db.flush()
    return {"success": True, "item": item_key}


# ── Säsongspass ─────────────────────────────────────────────────────
async def get_season_pass(db: AsyncSession, stable_id, season_number: int,
                          current_week: int) -> dict:
    """Säsongspassets belöningsstege. Gratisspåret finns alltid."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    has_pass = stable.season_pass_season == season_number
    points = stable.season_pass_points or 0

    tiers = []
    for threshold, free_reward, premium_reward in SEASON_PASS_LADDER:
        tiers.append({
            "points": threshold,
            "reached": points >= threshold,
            "free": free_reward,
            "premium": premium_reward,
            "premium_locked": not has_pass,
        })

    return {
        "season_number": season_number,
        "has_pass": has_pass,
        "price_sek": SEASON_PASS_PRICE_SEK,
        "points": points,
        "max_points": SEASON_PASS_LADDER[-1][0],
        "tiers": tiers,
        "how_to_earn": (
            "Poäng samlas av starter, pallplatser och upptäckter i hästdagboken. "
            "Gratisspåret ger belöningar oavsett om du köpt passet."
        ),
        "payment_configured": False,
    }


async def award_pass_points(db: AsyncSession, stable_id, season_number: int,
                            points: int) -> int:
    """Lägg till säsongspasspoäng. Nollställs vid ny säsong."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return 0
    if stable.season_pass_season != season_number:
        # Behåll ev. köpt pass men nollställ poängen vid säsongsbyte
        if stable.season_pass_season is not None:
            stable.season_pass_points = 0
    stable.season_pass_points = (stable.season_pass_points or 0) + points
    await db.flush()
    return stable.season_pass_points


async def sync_pass_points(db: AsyncSession, stable_id, season) -> int:
    """Räkna om passpoängen ur säsongens faktiska resultat."""
    from app.models.observation import HorseObservation
    from sqlalchemy import func as sa_func

    rows = (await db.execute(
        select(RaceResultSummary).where(
            RaceResultSummary.stable_id == stable_id,
            RaceResultSummary.game_week >= season.start_game_week,
            RaceResultSummary.game_week <= season.end_game_week,
        )
    )).scalars().all()

    discoveries = (await db.execute(
        select(sa_func.count(HorseObservation.id)).where(
            HorseObservation.stable_id == stable_id,
            HorseObservation.game_week >= season.start_game_week,
            HorseObservation.game_week <= season.end_game_week,
        )
    )).scalar() or 0

    points = (
        len(rows) * 2
        + sum(3 for r in rows if r.finish_position and r.finish_position <= 3)
        + sum(5 for r in rows if r.finish_position == 1)
        + discoveries
    )

    stable = await db.get(Stable, stable_id)
    if stable:
        stable.season_pass_points = points
        await db.flush()
    return points


async def grant_season_pass(db: AsyncSession, stable_id, season_number: int) -> dict:
    """Aktivera säsongspass. Anropas EFTER verifierad betalning."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}
    stable.season_pass_season = season_number
    await db.flush()
    return {"success": True, "season_number": season_number}
