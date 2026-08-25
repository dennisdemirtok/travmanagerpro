"""TravManager — Dagsloopen (sprint 3)

Två meningsfulla beslut varje speldag:
1. Träningspass per häst
2. Stallrundan, som genererar 0-2 händelser som kräver ett val

Träningsregler enligt spec:
- Hästar under 6 år utvecklar grundstats långsamt (max +1/vecka per stat,
  tak vid genetisk potential)
- Hästar från 8 år underhåller bara — träning motverkar förfall
- Överträning (3+ hårda pass i rad) ger trötthet, skaderisk och formtapp
"""
import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.stable import Stable
from app.models.event import StableEvent
from app.models.enums import HorseStatus
from app.services import event_service, finance_service

logger = logging.getLogger(__name__)

# ── Träningspass ────────────────────────────────────────────────────
REST = "rest"
LIGHT = "light"
INTERVAL = "interval"
DISTANCE = "distance"
HILL = "hill"
SPEED_TEST = "speed_test"

SPEED_TEST_COST = 200_000  # 2 000 kr

TRAINING_DEFS = {
    REST: {
        "label": "Vila",
        "description": "Snabbare återhämtning och bättre humör.",
        "energy": 0, "hard": False, "cost": 0,
        "stats": {},
    },
    LIGHT: {
        "label": "Lätt jobb",
        "description": "Håller formen uppe utan att kosta energi.",
        "energy": -3, "hard": False, "cost": 0,
        "stats": {},
    },
    INTERVAL: {
        "label": "Intervall",
        "description": "Utvecklar spurt hos unga hästar. Kostar energi, liten skaderisk.",
        "energy": -14, "hard": True, "cost": 0,
        "stats": {"sprint_strength": 1.0, "speed": 0.5},
        "injury_risk": 0.03,
    },
    DISTANCE: {
        "label": "Distans",
        "description": "Bygger uthållighet. Kostar energi.",
        "energy": -12, "hard": True, "cost": 0,
        "stats": {"endurance": 1.0, "mentality": 0.3},
        "injury_risk": 0.015,
    },
    HILL: {
        "label": "Backträning",
        "description": "Bygger styrka och uthållighet. Kostar mycket energi.",
        "energy": -20, "hard": True, "cost": 0,
        "stats": {"strength": 1.0, "endurance": 0.6},
        "injury_risk": 0.035,
        "requires_hill": True,
    },
    SPEED_TEST: {
        "label": "Snabbjobb (bantest)",
        "description": "Ger en observation om hästens dolda egenskaper.",
        "energy": -10, "hard": True, "cost": SPEED_TEST_COST,
        "stats": {"speed": 0.4},
        "injury_risk": 0.02,
        "observation": True,
    },
}

YOUNG_AGE = 6          # under 6 år: utveckling
VETERAN_AGE = 8        # från 8 år: bara underhåll
MAX_STAT_GAINS_PER_WEEK = 1
OVERTRAINING_STREAK = 3


def training_options() -> list[dict]:
    return [
        {
            "key": key,
            "label": d["label"],
            "description": d["description"],
            "cost": d["cost"],
            "hard": d["hard"],
            "requires_hill": d.get("requires_hill", False),
        }
        for key, d in TRAINING_DEFS.items()
    ]


def _potential_key(stat: str) -> str:
    return {
        "sprint_strength": "potential_sprint",
        "start_ability": "potential_start",
    }.get(stat, f"potential_{stat}")


async def set_training(db: AsyncSession, stable_id, horse_id, program: str) -> dict:
    if program not in TRAINING_DEFS:
        allowed = ", ".join(TRAINING_DEFS)
        return {"error": f"Okänt träningspass: {program}. Tillåtna: {allowed}"}

    horse = await db.get(Horse, horse_id)
    if not horse or horse.stable_id != stable_id:
        return {"error": "Hästen hittades inte i ditt stall"}
    if horse.status == HorseStatus.INJURED and program not in (REST, LIGHT):
        return {"error": f"{horse.name} är skadad och kan bara vila eller gå lätt jobb"}

    horse.daily_training = program
    await db.flush()
    return {
        "success": True,
        "horse_id": str(horse_id),
        "training": program,
        "label": TRAINING_DEFS[program]["label"],
    }


async def apply_daily_training(
    db: AsyncSession, stable_id, game_week: int, total_day: int, rng=None
) -> list[dict]:
    """Kör dagens träningspass för stallets hästar. Returnerar en rapport per häst."""
    rng = rng or random.Random()

    result = await db.execute(select(Horse).where(Horse.stable_id == stable_id))
    horses = result.scalars().all()
    report = []

    for horse in horses:
        if horse.last_training_day == total_day:
            continue  # redan tränad i dag
        if horse.status in (HorseStatus.RETIRED, HorseStatus.FOAL, HorseStatus.YEARLING):
            continue

        program = horse.daily_training or LIGHT
        if horse.status == HorseStatus.INJURED and program not in (REST, LIGHT):
            program = REST
        spec = TRAINING_DEFS.get(program, TRAINING_DEFS[LIGHT])

        notes: list[str] = []
        stat_changes: dict[str, int] = {}

        # Kostnad
        if spec["cost"] > 0:
            stable = await db.get(Stable, stable_id)
            balance = stable.balance if stable else 0
            if balance < spec["cost"]:
                notes.append("Otillräckligt saldo — passet byttes mot lätt jobb.")
                program, spec = LIGHT, TRAINING_DEFS[LIGHT]
            else:
                await finance_service.record_transaction(
                    db, stable_id, -spec["cost"], "training",
                    f"{spec['label']} — {horse.name}", game_week,
                )

        # Hård-pass-streak
        if spec["hard"]:
            horse.hard_training_streak = (horse.hard_training_streak or 0) + 1
        else:
            horse.hard_training_streak = 0

        overtrained = horse.hard_training_streak >= OVERTRAINING_STREAK

        # Energi och humör
        energy_delta = spec["energy"]
        if program == REST:
            horse.mood = min(100, (horse.mood or 70) + rng.randint(2, 5))
            horse.fatigue = max(0, (horse.fatigue or 0) - rng.randint(8, 14))
        if overtrained:
            energy_delta -= 8
            horse.fatigue = min(100, (horse.fatigue or 0) + rng.randint(6, 12))
            horse.form = max(1, (horse.form or 50) - rng.randint(2, 5))
            horse.mood = max(0, (horse.mood or 70) - rng.randint(3, 7))
            notes.append(
                f"Överträning: {horse.hard_training_streak} hårda pass i rad. "
                f"Trötthet och formtapp."
            )

        horse.energy = max(0, min(100, (horse.energy or 100) + energy_delta))

        # Formdrift av lätt jobb
        if program == LIGHT and not overtrained:
            horse.form = min(100, (horse.form or 50) + 1)

        # Statsutveckling
        age = horse.age_years or 3
        if spec["stats"] and not overtrained:
            if horse.stat_gain_week != game_week:
                horse.stat_gain_week = game_week
                horse.stat_gain_count = 0

            if age >= VETERAN_AGE:
                # Underhåll: träningen motverkar förfall, ingen ökning
                notes.append("Veteran — passet håller formen uppe men bygger inte nytt.")
            elif horse.stat_gain_count >= MAX_STAT_GAINS_PER_WEEK:
                notes.append("Har redan utvecklats så mycket den kan denna vecka.")
            else:
                for stat, weight in spec["stats"].items():
                    current = getattr(horse, stat, 40) or 40
                    cap = getattr(horse, _potential_key(stat), 70) or 70
                    if current >= cap:
                        continue
                    # Unga hästar utvecklas långsamt: chansdriven +1
                    chance = weight * (0.55 if age < YOUNG_AGE else 0.3)
                    if rng.random() < chance:
                        setattr(horse, stat, current + 1)
                        stat_changes[stat] = 1
                        horse.stat_gain_count += 1
                        break

        # Skaderisk
        risk = spec.get("injury_risk", 0.0)
        if overtrained:
            risk *= 2.5
        if risk > 0 and rng.random() < risk:
            horse.status = HorseStatus.INJURED
            horse.injury_type = "träningsskada"
            horse.injury_recovery_weeks = rng.randint(1, 2)
            notes.append("Hästen kände av något under passet och är skadad.")
            await event_service.create_event(
                db, stable_id, "injury", f"{horse.name} skadad i träning",
                f"{horse.name} kände av något under {spec['label'].lower()}. "
                f"Beräknad frånvaro: {horse.injury_recovery_weeks} vecka/veckor.",
                game_week,
            )

        # Observation av dold egenskap
        if spec.get("observation"):
            obs = await _speed_test_observation(db, horse, stable_id, game_week)
            if obs:
                notes.append(obs)

        horse.last_training_day = total_day

        report.append({
            "horse_id": str(horse.id),
            "horse_name": horse.name,
            "training": program,
            "label": spec["label"],
            "energy": horse.energy,
            "form": horse.form,
            "stat_changes": stat_changes,
            "overtrained": overtrained,
            "notes": notes,
        })

    await db.flush()
    return report


async def _speed_test_observation(db: AsyncSession, horse, stable_id, game_week: int):
    """Snabbjobb ger en riktad ledtråd om hästens dolda egenskaper."""
    try:
        from app.services.hidden_properties_service import ensure_hidden_properties
    except ImportError:
        return None

    props = await ensure_hidden_properties(db, horse.id)
    if not props:
        return None

    clues = []
    if abs(getattr(props, "barefoot_affinity", 0) or 0) >= 15:
        clues.append(
            "Kusken tyckte hästen rörde sig ovanligt lätt barfota."
            if props.barefoot_affinity > 0
            else "Hästen verkade obekväm utan skor."
        )
    if abs(getattr(props, "tight_curve_ability", 0) or 0) >= 15:
        clues.append(
            "Den tog kurvorna påfallande smidigt."
            if props.tight_curve_ability > 0
            else "Den tappade balans i de tvära kurvorna."
        )
    if abs(getattr(props, "long_homestretch_affinity", 0) or 0) >= 15:
        clues.append(
            "Den fortsatte accelerera långt in på upploppet."
            if props.long_homestretch_affinity > 0
            else "Den planade ut tidigt på upploppet."
        )
    if getattr(props, "hidden_sprint_gear", False):
        clues.append("Det fanns en extra växel där i slutet av jobbet.")
    if (getattr(props, "start_frequency_preference", "normal") or "normal") != "normal":
        clues.append(
            "Hästen verkar må bra av täta starter."
            if props.start_frequency_preference == "frequent"
            else "Hästen verkar behöva gott om vila mellan starterna."
        )

    if not clues:
        clues = ["Inget särskilt att rapportera — hästen kändes helt normal."]

    text = random.choice(clues)
    try:
        from app.models.observation import HorseObservation
        db.add(HorseObservation(
            horse_id=horse.id, stable_id=stable_id, game_week=game_week,
            observation_type="speed_test", text=text, confidence_level=0.7,
        ))
        await db.flush()
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Kunde inte spara observation: {exc}")
    return text


# ══════════════════════════════════════════════════════════════════
# STALLRUNDAN — händelsegenerator
# ══════════════════════════════════════════════════════════════════

VET_COST = 500_000        # 5 000 kr
REPAIR_COST = 300_000     # 3 000 kr
EXPRESS_FEED_COST = 150_000  # 1 500 kr
RELIEF_DRIVER_COST = 120_000  # 1 200 kr

# Allvarliga händelser: max en per vecka
SERIOUS = {"health_scare", "equipment_wear", "driver_conflict"}


async def run_stable_round(
    db: AsyncSession, stable_id, game_week: int, game_day: int, total_day: int
) -> dict:
    """Kör stallrundan: träningsresultat + 0-2 händelser som kräver beslut."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return {"error": "Stall hittades inte"}

    already_done = stable.last_stable_round_day == total_day
    rng = random.Random(f"{stable_id}-{total_day}")

    training_report = await apply_daily_training(
        db, stable_id, game_week, total_day, rng=rng
    )

    pending = await get_pending_events(db, stable_id)
    new_events = []

    if not already_done:
        horses = (await db.execute(
            select(Horse).where(Horse.stable_id == stable_id)
        )).scalars().all()

        count = rng.choices([0, 1, 2], weights=[25, 55, 20])[0]
        allow_serious = stable.last_serious_event_week != game_week

        for _ in range(count):
            ev = await _generate_event(
                db, stable, horses, game_week, total_day, rng, allow_serious
            )
            if ev is None:
                continue
            if ev["kind"] in SERIOUS:
                allow_serious = False
                stable.last_serious_event_week = game_week
            new_events.append(ev)

        stable.last_stable_round_day = total_day
        await db.flush()

    return {
        "already_done": already_done,
        "game_week": game_week,
        "game_day": game_day,
        "training": training_report,
        "new_events": new_events,
        "pending_events": await get_pending_events(db, stable_id),
    }


async def _generate_event(db, stable, horses, game_week, total_day, rng, allow_serious):
    """Slumpa fram en händelse ur poolen och spara den som ett beslut."""
    active = [h for h in horses if h.status not in (HorseStatus.RETIRED,)]
    if not active:
        return None

    pool = [
        ("health_scare", 18),
        ("form_peak", 16),
        ("caretaker_note", 14),
        ("equipment_wear", 12),
        ("purchase_offer", 10),
        ("driver_conflict", 10),
        ("feed_delay", 12),
        ("youngster_breakthrough", 8),
    ]
    if not allow_serious:
        pool = [(k, w) for k, w in pool if k not in SERIOUS]

    kinds = [k for k, _ in pool]
    weights = [w for _, w in pool]
    kind = rng.choices(kinds, weights=weights)[0]

    horse = rng.choice(active)
    builder = _EVENT_BUILDERS[kind]
    built = builder(horse, active, rng)
    if built is None:
        return None

    title, description, choices = built
    event = await event_service.create_event(
        db, stable.id, "stable_round", title, description, game_week,
        requires_action=True,
        action_data={
            "kind": kind,
            "horse_id": str(horse.id),
            "horse_name": horse.name,
            "choices": choices,
            "total_day": total_day,
        },
    )
    return {
        "id": str(event.id),
        "kind": kind,
        "title": title,
        "description": description,
        "horse_id": str(horse.id),
        "horse_name": horse.name,
        "choices": choices,
    }


def _b_health_scare(horse, active, rng):
    limb = rng.choice(["vänster fram", "höger fram", "vänster bak", "höger bak"])
    return (
        f"Hälsokänning: {horse.name}",
        f"{horse.name} kändes stel i {limb}ben under morgonjobbet.",
        [
            {"key": "vet", "label": "Veterinär", "detail": "5 000 kr — säkert besked"},
            {"key": "rest", "label": "Vila 2 dagar", "detail": "Gratis, men två dagar utan träning"},
            {"key": "ignore", "label": "Ignorera", "detail": "30 % risk att det blir en skada"},
        ],
    )


def _b_form_peak(horse, active, rng):
    return (
        f"Formtopp: {horse.name}",
        f"{horse.name} verkar sprudlande idag — skötaren har aldrig sett den så pigg.",
        [
            {"key": "use", "label": "Utnyttja formen", "detail": "+10 form i 5 dagar"},
            {"key": "save", "label": "Spara energin", "detail": "+8 energi istället"},
        ],
    )


def _b_caretaker_note(horse, active, rng):
    return (
        f"Skötaren rapporterar om {horse.name}",
        f"Skötaren har lagt märke till något hos {horse.name} och vill berätta.",
        [
            {"key": "listen", "label": "Lyssna", "detail": "Ger en observation till hästdagboken"},
            {"key": "ignore", "label": "Inte nu", "detail": "Ingen effekt"},
        ],
    )


def _b_equipment_wear(horse, active, rng):
    return (
        "Utrustningsslitage",
        f"Sulkyn som {horse.name} kör med har en spricka i ramen.",
        [
            {"key": "repair", "label": "Laga", "detail": "3 000 kr"},
            {"key": "ignore", "label": "Kör ändå", "detail": "Risk för haveri i nästa lopp"},
        ],
    )


def _b_purchase_offer(horse, active, rng):
    from app.services.valuation_service import calculate_horse_value
    value = calculate_horse_value(horse)
    offer = int(value * rng.uniform(0.85, 1.25))
    buyer = rng.choice([
        "Stall Nordstjärnan", "Team Vinterbro", "Stall Gyllene Sulky",
        "Kviberg Racing", "Stall Havsbris",
    ])
    return (
        f"Bud på {horse.name}",
        f"{buyer} vill köpa {horse.name} för {finance_service.format_kr(offer)}.",
        [
            {"key": "sell", "label": f"Sälj för {finance_service.format_kr(offer)}",
             "detail": "Hästen lämnar stallet", "amount": offer},
            {"key": "decline", "label": "Tacka nej", "detail": "Behåll hästen"},
        ],
    )


def _b_driver_conflict(horse, active, rng):
    other = rng.choice([h for h in active if h.id != horse.id] or [horse])
    return (
        "Kusken är dubbelbokad",
        f"Din kusk är bokad på både {horse.name} och {other.name} till lördagen.",
        [
            {"key": "keep_first", "label": f"Kör {horse.name}", "detail": "Den andra får stå över"},
            {"key": "keep_second", "label": f"Kör {other.name}", "detail": "Den första får stå över",
             "horse_id": str(other.id)},
            {"key": "relief", "label": "Hyr ersättare", "detail": "1 200 kr — båda kan starta"},
        ],
    )


def _b_feed_delay(horse, active, rng):
    return (
        "Foderleveransen är försenad",
        "Foderbilen har fastnat. Utan expressleverans tappar alla hästar form i morgon.",
        [
            {"key": "express", "label": "Beställ express", "detail": "1 500 kr"},
            {"key": "wait", "label": "Vänta ut det", "detail": "−2 form på alla hästar"},
        ],
    )


def _b_youngster_breakthrough(horse, active, rng):
    young = [h for h in active if (h.age_years or 3) < YOUNG_AGE]
    if not young:
        return None
    horse = rng.choice(young)
    return (
        f"Genombrott: {horse.name}",
        f"{horse.name} visade något extra i morgonjobbet — tränaren log hela vägen hem.",
        [
            {"key": "celebrate", "label": "Bygg vidare på det", "detail": "+2 permanent på en stat"},
        ],
    )


_EVENT_BUILDERS = {
    "health_scare": _b_health_scare,
    "form_peak": _b_form_peak,
    "caretaker_note": _b_caretaker_note,
    "equipment_wear": _b_equipment_wear,
    "purchase_offer": _b_purchase_offer,
    "driver_conflict": _b_driver_conflict,
    "feed_delay": _b_feed_delay,
    "youngster_breakthrough": _b_youngster_breakthrough,
}


async def get_pending_events(db: AsyncSession, stable_id) -> list[dict]:
    result = await db.execute(
        select(StableEvent).where(
            StableEvent.stable_id == stable_id,
            StableEvent.requires_action == True,
        ).order_by(StableEvent.created_at.desc()).limit(10)
    )
    out = []
    for e in result.scalars().all():
        data = e.action_data or {}
        out.append({
            "id": str(e.id),
            "kind": data.get("kind"),
            "title": e.title,
            "description": e.description,
            "horse_id": data.get("horse_id"),
            "horse_name": data.get("horse_name"),
            "choices": data.get("choices", []),
            "game_week": e.game_week,
        })
    return out


# ══════════════════════════════════════════════════════════════════
# BESLUT — utfall av spelarens val
# ══════════════════════════════════════════════════════════════════

async def resolve_event(
    db: AsyncSession, stable_id, event_id, choice_key: str,
    game_week: int, total_day: int,
) -> dict:
    """Applicera utfallet av spelarens val och stäng händelsen."""
    event = await db.get(StableEvent, event_id)
    if not event or event.stable_id != stable_id:
        return {"error": "Händelsen hittades inte"}
    if not event.requires_action:
        return {"error": "Händelsen är redan hanterad"}

    data = event.action_data or {}
    kind = data.get("kind")
    valid = {c["key"] for c in data.get("choices", [])}
    if choice_key not in valid:
        return {"error": f"Ogiltigt val. Tillåtna: {', '.join(sorted(valid))}"}

    horse = None
    if data.get("horse_id"):
        horse = await db.get(Horse, data["horse_id"])

    rng = random.Random(f"{event_id}-{choice_key}")
    handler = _RESOLVERS.get(kind)
    outcome = await handler(
        db, stable_id, horse, data, choice_key, game_week, total_day, rng
    ) if handler else "Inget hände."

    event.requires_action = False
    event.is_read = True
    event.action_data = {**data, "resolved_with": choice_key, "outcome": outcome}
    await db.flush()

    return {"success": True, "outcome": outcome, "kind": kind, "choice": choice_key}


async def _r_health_scare(db, stable_id, horse, data, choice, week, day, rng):
    if horse is None:
        return "Hästen finns inte kvar i stallet."
    if choice == "vet":
        await finance_service.record_transaction(
            db, stable_id, -VET_COST, "vet",
            f"Veterinärbesök — {horse.name}", week,
        )
        if rng.random() < 0.45:
            horse.health = min(100, (horse.health or 90) + 6)
            return (f"Veterinären hittade inget allvarligt. {horse.name} är frisk "
                    f"och hälsan förbättrades något.")
        horse.daily_training = REST
        return (f"Veterinären hittade en begynnande inflammation. {horse.name} sattes "
                f"på vila och slipper en riktig skada.")
    if choice == "rest":
        horse.daily_training = REST
        horse.energy = min(100, (horse.energy or 100) + 10)
        horse.fatigue = max(0, (horse.fatigue or 0) - 10)
        return f"{horse.name} vilar två dagar. Stelheten släppte."
    # ignore
    if rng.random() < 0.30:
        horse.status = HorseStatus.INJURED
        horse.injury_type = "sena i framben"
        horse.injury_recovery_weeks = rng.randint(1, 3)
        await event_service.create_event(
            db, stable_id, "injury", f"{horse.name} skadad",
            f"Stelheten du valde att ignorera utvecklades till en skada. "
            f"{horse.injury_recovery_weeks} vecka/veckor borta.",
            week,
        )
        return (f"Det gick illa. {horse.name} är skadad i "
                f"{horse.injury_recovery_weeks} vecka/veckor.")
    return f"Det löste sig — {horse.name} gick av sig stelheten."


async def _r_form_peak(db, stable_id, horse, data, choice, week, day, rng):
    if horse is None:
        return "Hästen finns inte kvar i stallet."
    if choice == "use":
        horse.form_window_until_day = day + 5
        horse.form_window_bonus = 10
        return (f"{horse.name} har ett formfönster på +10 i fem dagar. "
                f"Anmäl den medan det varar.")
    horse.energy = min(100, (horse.energy or 100) + 8)
    return f"{horse.name} fick gå lugnt och sparade krafterna (+8 energi)."


async def _r_caretaker_note(db, stable_id, horse, data, choice, week, day, rng):
    if choice != "listen" or horse is None:
        return "Du hade inte tid att lyssna den här gången."
    text = await _speed_test_observation(db, horse, stable_id, week)
    return text or "Skötaren hade inget konkret att tillägga."


async def _r_equipment_wear(db, stable_id, horse, data, choice, week, day, rng):
    if choice == "repair":
        await finance_service.record_transaction(
            db, stable_id, -REPAIR_COST, "equipment",
            "Sulkyreparation", week,
        )
        if horse is not None:
            horse.equipment_damaged = False
        return "Sulkyn är lagad och redo för nästa start."
    if horse is not None:
        horse.equipment_damaged = True
    return "Du kör vidare på den spruckna sulkyn. Risk för haveri i nästa lopp."


async def _r_purchase_offer(db, stable_id, horse, data, choice, week, day, rng):
    if choice != "sell" or horse is None:
        return "Du tackade nej till budet."

    horses_left = (await db.execute(
        select(Horse).where(Horse.stable_id == stable_id)
    )).scalars().all()
    if len(horses_left) <= 1:
        return "Du kan inte sälja din sista häst."

    amount = next(
        (c.get("amount") for c in data.get("choices", []) if c["key"] == "sell"), 0
    )
    await finance_service.record_transaction(
        db, stable_id, amount, "horse_sale",
        f"Sålde {horse.name}", week,
    )
    name = horse.name
    await db.delete(horse)
    await db.flush()
    return f"{name} är såld för {finance_service.format_kr(amount)}."


async def _r_driver_conflict(db, stable_id, horse, data, choice, week, day, rng):
    if choice == "relief":
        await finance_service.record_transaction(
            db, stable_id, -RELIEF_DRIVER_COST, "freelance_driver",
            "Ersättarkusk vid dubbelbokning", week,
        )
        return "Du hyrde in en ersättare — båda hästarna kan starta."
    return "Du valde vilken häst kusken kör. Den andra får stå över."


async def _r_feed_delay(db, stable_id, horse, data, choice, week, day, rng):
    horses = (await db.execute(
        select(Horse).where(Horse.stable_id == stable_id)
    )).scalars().all()
    if choice == "express":
        await finance_service.record_transaction(
            db, stable_id, -EXPRESS_FEED_COST, "feed",
            "Expressleverans foder", week,
        )
        return "Fodret kom fram i tid. Inga hästar påverkas."
    for h in horses:
        h.form = max(1, (h.form or 50) - 2)
    return f"Fodret dröjde. {len(horses)} hästar tappade 2 i form."


async def _r_youngster_breakthrough(db, stable_id, horse, data, choice, week, day, rng):
    if horse is None:
        return "Hästen finns inte kvar i stallet."
    trainable = ["speed", "endurance", "mentality", "start_ability",
                 "sprint_strength", "balance", "strength"]
    rng.shuffle(trainable)
    for stat in trainable:
        current = getattr(horse, stat, 40) or 40
        cap = getattr(horse, _potential_key(stat), 70) or 70
        if current + 2 <= cap:
            setattr(horse, stat, current + 2)
            label = {
                "speed": "Fart", "endurance": "Uthållighet", "mentality": "Mentalitet",
                "start_ability": "Startförmåga", "sprint_strength": "Spurt",
                "balance": "Balans", "strength": "Styrka",
            }[stat]
            return f"{horse.name} utvecklades permanent: {label} +2."
    return f"{horse.name} har redan nått sin potential i alla grenar."


_RESOLVERS = {
    "health_scare": _r_health_scare,
    "form_peak": _r_form_peak,
    "caretaker_note": _r_caretaker_note,
    "equipment_wear": _r_equipment_wear,
    "purchase_offer": _r_purchase_offer,
    "driver_conflict": _r_driver_conflict,
    "feed_delay": _r_feed_delay,
    "youngster_breakthrough": _r_youngster_breakthrough,
}
