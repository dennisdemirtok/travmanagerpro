"""TravManager — NPC Auto-Entry Service

Automatically enters NPC stable horses into appropriate races
before each session is simulated.
"""
import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import (
    HorseStatus, PersonalityType,
    TacticPositioning, TacticTempo, TacticSprint,
    TacticGallopSafety, TacticCurve, TacticWhip,
    ShoeType,
)
from app.models.horse import Horse
from app.models.race import Race, RaceEntry, RaceSession
from app.models.stable import Stable
from app.models.driver import DriverContract
from app.services.race_service import calculate_start_points

logger = logging.getLogger(__name__)


# Map personality to preferred tactics
PERSONALITY_TACTICS = {
    PersonalityType.BRAVE: {
        "positioning": TacticPositioning.LEAD,
        "tempo": TacticTempo.OFFENSIVE,
        "sprint_order": TacticSprint.NORMAL_400M,
        "gallop_safety": TacticGallopSafety.NORMAL,
    },
    PersonalityType.CALM: {
        "positioning": TacticPositioning.SECOND,
        "tempo": TacticTempo.BALANCED,
        "sprint_order": TacticSprint.NORMAL_400M,
        "gallop_safety": TacticGallopSafety.SAFE,
    },
    PersonalityType.HOT: {
        "positioning": TacticPositioning.LEAD,
        "tempo": TacticTempo.OFFENSIVE,
        "sprint_order": TacticSprint.EARLY_600M,
        "gallop_safety": TacticGallopSafety.RISKY,
    },
    PersonalityType.STUBBORN: {
        "positioning": TacticPositioning.LEAD,
        "tempo": TacticTempo.CAUTIOUS,
        "sprint_order": TacticSprint.LATE_250M,
        "gallop_safety": TacticGallopSafety.NORMAL,
    },
    PersonalityType.RESPONSIVE: {
        "positioning": TacticPositioning.SECOND,
        "tempo": TacticTempo.BALANCED,
        "sprint_order": TacticSprint.NORMAL_400M,
        "gallop_safety": TacticGallopSafety.NORMAL,
    },
    PersonalityType.SENSITIVE: {
        "positioning": TacticPositioning.BACK,
        "tempo": TacticTempo.CAUTIOUS,
        "sprint_order": TacticSprint.LATE_250M,
        "gallop_safety": TacticGallopSafety.SAFE,
    },
}


async def auto_enter_npc_horses(
    db: AsyncSession, session_id, game_week: int
):
    """Auto-enter NPC stable horses into appropriate races in a session.

    Each NPC stable enters 1-3 horses depending on availability.
    Horses are matched to races by division level and distance preference.
    """
    # Load NPC stables with horses
    stables_result = await db.execute(
        select(Stable)
        .where(Stable.is_npc == True)
        .options(selectinload(Stable.horses))
    )
    npc_stables = stables_result.scalars().all()

    if not npc_stables:
        return

    # Sessionen behövs för bana och väder när AI:n väljer taktik och skor
    session = (await db.execute(
        select(RaceSession)
        .options(selectinload(RaceSession.track))
        .where(RaceSession.id == session_id)
    )).scalar_one_or_none()

    # Load races in this session with current entries
    races_result = await db.execute(
        select(Race)
        .options(selectinload(Race.entries))
        .where(Race.session_id == session_id, Race.is_finished == False)
    )
    races = races_result.scalars().all()

    if not races:
        return

    # Load active driver contracts for NPC stables
    stable_ids = [s.id for s in npc_stables]
    contracts_result = await db.execute(
        select(DriverContract)
        .where(
            DriverContract.stable_id.in_(stable_ids),
            DriverContract.is_active == True,
        )
    )
    contracts = {c.stable_id: c for c in contracts_result.scalars().all()}

    # Track which horses are already entered in this session
    all_entries = []
    for race in races:
        for entry in race.entries:
            if not entry.is_scratched:
                all_entries.append(entry.horse_id)
    entered_horse_ids = set(all_entries)

    rng = random.Random(abs(game_week) * 7 + hash(str(session_id)) % 10000)

    for stable in npc_stables:
        contract = contracts.get(stable.id)
        if not contract:
            continue

        # Skip if stable is too broke
        if stable.balance < 200_000:
            continue

        # Get eligible horses
        eligible = []
        for horse in stable.horses:
            if horse.id in entered_horse_ids:
                continue
            if horse.status != HorseStatus.READY:
                continue
            if horse.energy < 50:
                continue
            if horse.fatigue > 60:
                continue
            eligible.append(horse)

        if not eligible:
            continue

        # Shuffle and pick 1-3 horses
        rng.shuffle(eligible)
        num_to_enter = min(len(eligible), rng.randint(1, 3))
        horses_to_enter = eligible[:num_to_enter]

        for horse in horses_to_enter:
            # Calculate start points for this horse
            sp = await calculate_start_points(db, horse.id)
            horse_points = sp["total"]

            # Find the best matching race
            best_race = _pick_race_for_horse(
                horse, horse_points, races, entered_horse_ids, rng
            )

            if not best_race:
                continue

            # Check if race is full
            active_entries = [
                e for e in best_race.entries if not e.is_scratched
            ]
            if len(active_entries) >= best_race.max_entries:
                continue

            # Check balance
            if stable.balance < best_race.entry_fee * 2:
                continue

            # Stallets personlighet styr upplägget, hästens temperament finjusterar
            tactics = _choose_tactics(stable, horse, best_race, session, rng)

            entry = RaceEntry(
                race_id=best_race.id,
                horse_id=horse.id,
                stable_id=stable.id,
                driver_id=contract.driver_id,
                positioning=tactics["positioning"],
                tempo=tactics["tempo"],
                sprint_order=tactics["sprint_order"],
                gallop_safety=tactics["gallop_safety"],
                curve_strategy=tactics["curve_strategy"],
                whip_usage=tactics["whip_usage"],
                shoe=tactics["shoe"],
                entry_fee_paid=best_race.entry_fee,
                compatibility_score=50,  # NPC default
            )
            db.add(entry)

            # Deduct entry fee
            stable.balance -= best_race.entry_fee

            entered_horse_ids.add(horse.id)

            logger.info(
                f"NPC entry: {horse.name} ({stable.name}) → "
                f"{best_race.race_name} (pts: {horse_points})"
            )

    await db.flush()


def _pick_race_for_horse(
    horse: Horse,
    horse_points: int,
    races: list[Race],
    entered_ids: set,
    rng: random.Random,
) -> Race | None:
    """Pick the best-fitting race for an NPC horse."""
    candidates = []

    for race in races:
        # Loppstegen gäller AI-hästar också — annars fylls nybörjarlopp
        # av meriterade hästar och skyddet blir meningslöst.
        if race.min_start_points > 0 and horse_points < race.min_start_points:
            continue
        max_pts = getattr(race, "max_start_points", None)
        if max_pts is not None and horse_points > max_pts:
            continue
        max_earn = getattr(race, "max_earnings", None)
        if max_earn is not None and (horse.total_earnings or 0) > max_earn:
            continue
        race_class = race.race_class.value if hasattr(race.race_class, "value") else str(race.race_class)
        if race_class == "maiden" and (horse.total_wins or 0) > 0:
            continue

        # Check capacity
        active = [e for e in race.entries if not e.is_scratched]
        if len(active) >= race.max_entries:
            continue

        # Score the match
        score = 0.0

        # Prefer races matching division level (horse power ~ division)
        horse_power = (horse.speed + horse.endurance + horse.sprint_strength) / 3
        if race.division_level:
            # Division 6 = weakest (power ~55-70), division 1 = strongest (power ~85+)
            expected_power = 40 + race.division_level * 8
            power_diff = abs(horse_power - expected_power)
            score += max(0, 30 - power_diff)  # Max 30 points for match
        else:
            score += 15  # Neutral for youth/unclassified races

        # Prefer matching distance
        dist_diff = abs(race.distance - horse.distance_optimum) / 100
        score += max(0, 10 - dist_diff)  # Max 10 points for distance

        # Prefer races with fewer entries (fill undersubscribed races)
        entry_count = len([e for e in race.entries if not e.is_scratched])
        score += max(0, 10 - entry_count)

        # Small random factor
        score += rng.random() * 5

        candidates.append((race, score))

    if not candidates:
        return None

    # Pick best scoring race
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


# ── AI-stallens personlighet (DEL E punkt 4-5) ──────────────────────
STABLE_PERSONALITIES = ["aggressive", "balanced", "defensive", "unpredictable"]

# Fel i 15 % av fallen — AI:n ska inte vara felfri
MISTAKE_RATE = 0.15


def _choose_tactics(stable, horse, race, session, rng) -> dict:
    """Semi-intelligent taktik: stallets personlighet + bana + underlag,
    med en felmarginal så AI-stall ibland gör samma misstag som spelare."""
    personality = getattr(stable, "ai_personality", None) or "balanced"

    # Position och tempo efter stallets läggning
    if personality == "aggressive":
        positioning = rng.choice([TacticPositioning.LEAD, TacticPositioning.LEAD,
                                  TacticPositioning.OUTSIDE])
        tempo = TacticTempo.OFFENSIVE
        safety = TacticGallopSafety.RISKY
    elif personality == "defensive":
        positioning = rng.choice([TacticPositioning.SECOND, TacticPositioning.TRAILING,
                                  TacticPositioning.BACK])
        tempo = TacticTempo.CAUTIOUS
        safety = TacticGallopSafety.SAFE
    elif personality == "unpredictable":
        positioning = rng.choice(list(TacticPositioning))
        tempo = rng.choice(list(TacticTempo))
        safety = rng.choice(list(TacticGallopSafety))
    else:  # balanced
        positioning = rng.choice([TacticPositioning.SECOND, TacticPositioning.SECOND,
                                  TacticPositioning.LEAD, TacticPositioning.TRAILING])
        tempo = TacticTempo.BALANCED
        safety = TacticGallopSafety.NORMAL

    # Hästens egen läggning drar åt sitt håll
    if horse.personality_primary == PersonalityType.HOT and personality != "unpredictable":
        positioning = TacticPositioning.LEAD
    elif horse.personality_primary == PersonalityType.CALM and personality == "aggressive":
        tempo = TacticTempo.BALANCED

    # Spurttiming efter upploppets längd
    stretch = getattr(session.track, "stretch_length", 200) if session and session.track else 200
    if stretch >= 300:
        sprint = TacticSprint.LATE_250M
    elif stretch <= 150:
        sprint = TacticSprint.EARLY_600M
    else:
        sprint = TacticSprint.NORMAL_400M

    # Kurvstrategi: starka hästar vågar innerspår
    power = (horse.speed + horse.endurance + horse.sprint_strength) / 3
    curve = TacticCurve.INNER if power >= 65 else rng.choice(
        [TacticCurve.MIDDLE, TacticCurve.MIDDLE, TacticCurve.OUTER]
    )

    # Skoval efter underlag och väder
    surface = race.surface.value if hasattr(race.surface, "value") else str(race.surface or "dirt")
    weather = session.weather.value if session and hasattr(session.weather, "value") else "clear"
    if surface == "winter" or weather == "snow":
        shoe = ShoeType.STUDS
    elif weather in ("rain", "heavy_rain"):
        shoe = ShoeType.GRIP
    else:
        shoe = rng.choice([ShoeType.NORMAL_STEEL, ShoeType.NORMAL_STEEL,
                           ShoeType.LIGHT_ALUMINUM])

    # Felmarginal: ibland glöms rätt sko på vinterbana
    if rng.random() < MISTAKE_RATE:
        shoe = rng.choice([ShoeType.NORMAL_STEEL, ShoeType.BAREFOOT,
                           ShoeType.LIGHT_ALUMINUM])

    whip = TacticWhip.AGGRESSIVE if personality == "aggressive" else TacticWhip.NORMAL

    return {
        "positioning": positioning,
        "tempo": tempo,
        "sprint_order": sprint,
        "gallop_safety": safety,
        "curve_strategy": curve,
        "whip_usage": whip,
        "shoe": shoe,
    }


# ── AI-stallens personligheter ──────────────────────────────────────
async def ensure_stable_personalities(db: AsyncSession) -> int:
    """Ge varje AI-stall en personlighet. Idempotent — körs varje vecka.

    Personligheten avgör hur stallet kör: aggressive tar ledningen,
    defensive sitter i rygg, unpredictable gör vad som helst.
    """
    result = await db.execute(
        select(Stable).where(Stable.is_npc == True, Stable.ai_personality == None)
    )
    stables = result.scalars().all()
    assigned = 0
    for stable in stables:
        # Deterministiskt ur stall-id så samma stall alltid kör likadant
        idx = int(str(stable.id).replace("-", "")[:8], 16) % len(STABLE_PERSONALITIES)
        stable.ai_personality = STABLE_PERSONALITIES[idx]
        assigned += 1
    if assigned:
        await db.flush()
        logger.info(f"Tilldelade personlighet till {assigned} AI-stall")
    return assigned
