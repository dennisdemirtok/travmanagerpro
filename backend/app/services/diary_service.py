"""TravManager — Hästdagboken och motståndsanalysen (sprint 4, DEL D)

Dagboken är kärnan i skill-spelet: den som för bok slår den som gissar.
Motståndsanalysen gör smart anmälning till en egen spelmekanik.
"""
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.horse import Horse
from app.models.race import Race, RaceEntry
from app.models.observation import HorseObservation, HorseNote, HorseTag

logger = logging.getLogger(__name__)

# Förslagstaggar spelaren kan sätta med ett klick
SUGGESTED_TAGS = [
    "Barfota ✓", "Barfota ✗", "Amerikansk sulky ✓", "Trivs i regn",
    "Ogillar kyla", "Tåligt underlag", "Ej täta starter", "Tål täta starter",
    "Stark spurt", "Behöver ledning", "Trivs i rygg", "Tåligt långt upplopp",
]

VERDICTS = [
    # (min_ratio, key, label, color)
    (1.12, "superior", "ÖVERLÄGSEN", "#4ADE80"),
    (1.04, "favourite", "FAVORIT", "#A3E635"),
    (0.96, "matched", "MATCHAT", "#E9C46A"),
    (0.88, "tough", "TUFFT", "#FB923C"),
    (0.00, "too_tough", "FÖR TUFFT", "#EF4444"),
]


def horse_rating(h) -> float:
    """Samma viktning som motorn använder för att matcha NPC-fält."""
    rating = (
        (h.speed or 40) * 0.35
        + (h.endurance or 40) * 0.25
        + (h.sprint_strength or 40) * 0.20
        + (h.start_ability or 40) * 0.10
        + (h.balance or 40) * 0.05
        + (h.mentality or 40) * 0.05
    )
    rating *= 0.9 + (h.form if h.form is not None else 50) / 500
    rating *= 0.9 + (h.condition if h.condition is not None else 80) / 500
    return rating


def _verdict(ratio: float):
    for threshold, key, label, color in VERDICTS:
        if ratio >= threshold:
            return key, label, color
    return "too_tough", "FÖR TUFFT", "#EF4444"


async def analyze_opposition(db: AsyncSession, race_id, horse_id) -> dict:
    """Motståndsanalys inför anmälan: din häst mot fältet."""
    horse = await db.get(Horse, horse_id)
    if not horse:
        return {"error": "Hästen hittades inte"}

    race = (await db.execute(
        select(Race).where(Race.id == race_id)
    )).scalar_one_or_none()
    if not race:
        return {"error": "Loppet finns inte"}

    entries = (await db.execute(
        select(RaceEntry).where(
            RaceEntry.race_id == race_id,
            RaceEntry.is_scratched == False,
        )
    )).scalars().all()

    rival_ids = [e.horse_id for e in entries if e.horse_id != horse_id]
    rivals = []
    if rival_ids:
        rivals = (await db.execute(
            select(Horse).where(Horse.id.in_(rival_ids))
        )).scalars().all()

    mine = horse_rating(horse)
    rival_ratings = [horse_rating(r) for r in rivals]

    # Motorn genererar NPC-fältet relativt snittet av de anmälda hästarna,
    # men NPC-stallens hästar anmäls först och filtreras av divisionsnivån.
    # Divisionen är därför ett golv för hur hårt motståndet faktiskt blir:
    # division 1 = elit (~82), division 6 = nybörjare (~42).
    all_entered = rival_ratings + [mine]
    entered_mean = sum(all_entered) / len(all_entered)
    division_level = race.division_level or 6
    division_baseline = (90 - division_level * 8) * 0.92
    field_reference = max(entered_mean, division_baseline)

    # Rollfördelning i motorn: contender +2..+8, midfield ±5, backmarker -12..-3
    expected_contender = field_reference + 5.0
    expected_average = field_reference - 1.5

    ratio_avg = mine / expected_average if expected_average > 0 else 1.0
    ratio_top = mine / expected_contender if expected_contender > 0 else 1.0
    key, label, color = _verdict((ratio_avg * 0.45) + (ratio_top * 0.55))

    # Startpoäng
    from app.services.race_service import calculate_start_points
    sp = await calculate_start_points(db, horse_id)
    qualifies = sp["total"] >= (race.min_start_points or 0)

    warnings = []
    confidence = getattr(horse, "confidence", 50) or 50
    if confidence < 30:
        warnings.append(
            f"Självförtroendet är lågt ({confidence}). Hästen tappar fart och "
            f"galopprisken stiger — en förlust här förstärker nedgången."
        )
    elif confidence > 70:
        warnings.append(
            f"Självförtroendet är högt ({confidence}). Hästen kan mer än statsen visar."
        )
    if key == "too_tough":
        warnings.append(
            "Motståndet är för hårt. En sistaplats mot överlägset motstånd kostar "
            "lite självförtroende — men en sistaplats i ett lopp hästen borde klarat "
            "kostar mycket."
        )
    if not qualifies:
        warnings.append(
            f"Hästen har {sp['total']} startpoäng men loppet kräver {race.min_start_points}."
        )
    if (horse.energy or 100) < 45:
        warnings.append(f"Energin är nere på {horse.energy}. Överväg vila först.")
    if (horse.races_last_30_days or 0) >= 3:
        warnings.append(
            f"{horse.races_last_30_days} starter senaste 30 dagarna — "
            f"kolla dagboken om hästen tål täta starter."
        )

    return {
        "horse_id": str(horse_id),
        "horse_name": horse.name,
        "your_rating": round(mine, 1),
        "field_average": round(expected_average, 1),
        "field_top": round(expected_contender, 1),
        "entered_rivals": len(rivals),
        "division_level": division_level,
        "division_baseline": round(division_baseline, 1),
        "entered_mean": round(entered_mean, 1),
        "verdict": key,
        "verdict_label": label,
        "verdict_color": color,
        "confidence": confidence,
        "start_points": sp["total"],
        "min_start_points": race.min_start_points or 0,
        "qualifies": qualifies,
        "warnings": warnings,
        "note": (
            f"Division {division_level} sätter grundnivån på motståndet. Fältet fylls "
            f"sedan med AI-hästar som matchas mot de anmälda hästarna — anmäler du en "
            f"svag häst bland starka blir motståndet hårdare."
        ),
    }


# ── Dagbok ──────────────────────────────────────────────────────────
async def get_diary(db: AsyncSession, stable_id, horse_id) -> dict:
    horse = await db.get(Horse, horse_id)
    if not horse:
        return {"error": "Hästen hittades inte"}

    obs = (await db.execute(
        select(HorseObservation)
        .where(HorseObservation.horse_id == horse_id)
        .order_by(HorseObservation.created_at.desc())
        .limit(60)
    )).scalars().all()

    notes = (await db.execute(
        select(HorseNote)
        .where(HorseNote.horse_id == horse_id, HorseNote.stable_id == stable_id)
        .order_by(HorseNote.created_at.desc())
        .limit(60)
    )).scalars().all()

    tags = (await db.execute(
        select(HorseTag)
        .where(HorseTag.horse_id == horse_id, HorseTag.stable_id == stable_id)
        .order_by(HorseTag.created_at)
    )).scalars().all()

    return {
        "horse_id": str(horse_id),
        "horse_name": horse.name,
        "confidence": getattr(horse, "confidence", 50) or 50,
        "days_since_last_race": horse.days_since_last_race or 0,
        "races_last_30_days": horse.races_last_30_days or 0,
        "observations": [
            {
                "id": str(o.id),
                "type": o.observation_type,
                "text": o.text,
                "game_week": o.game_week,
                "confidence_level": float(o.confidence_level or 0.5),
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in obs
        ],
        "notes": [
            {
                "id": str(n.id),
                "text": n.text,
                "game_week": n.game_week,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notes
        ],
        "tags": [{"id": str(t.id), "tag": t.tag} for t in tags],
        "suggested_tags": SUGGESTED_TAGS,
    }


async def add_note(db: AsyncSession, stable_id, horse_id, text: str, game_week: int) -> dict:
    text = (text or "").strip()
    if not text:
        return {"error": "Anteckningen kan inte vara tom"}
    if len(text) > 2000:
        return {"error": "Anteckningen är för lång (max 2000 tecken)"}

    horse = await db.get(Horse, horse_id)
    if not horse or horse.stable_id != stable_id:
        return {"error": "Hästen hittades inte i ditt stall"}

    note = HorseNote(
        horse_id=horse_id, stable_id=stable_id, text=text, game_week=game_week
    )
    db.add(note)
    await db.flush()
    return {"success": True, "id": str(note.id), "text": text}


async def delete_note(db: AsyncSession, stable_id, note_id) -> dict:
    note = await db.get(HorseNote, note_id)
    if not note or note.stable_id != stable_id:
        return {"error": "Anteckningen hittades inte"}
    await db.delete(note)
    await db.flush()
    return {"success": True}


async def add_tag(db: AsyncSession, stable_id, horse_id, tag: str) -> dict:
    tag = (tag or "").strip()[:40]
    if not tag:
        return {"error": "Taggen kan inte vara tom"}

    horse = await db.get(Horse, horse_id)
    if not horse or horse.stable_id != stable_id:
        return {"error": "Hästen hittades inte i ditt stall"}

    existing = (await db.execute(
        select(HorseTag).where(HorseTag.horse_id == horse_id, HorseTag.tag == tag)
    )).scalar_one_or_none()
    if existing:
        return {"success": True, "id": str(existing.id), "tag": tag}

    row = HorseTag(horse_id=horse_id, stable_id=stable_id, tag=tag)
    db.add(row)
    await db.flush()
    return {"success": True, "id": str(row.id), "tag": tag}


async def delete_tag(db: AsyncSession, stable_id, tag_id) -> dict:
    row = await db.get(HorseTag, tag_id)
    if not row or row.stable_id != stable_id:
        return {"error": "Taggen hittades inte"}
    await db.delete(row)
    await db.flush()
    return {"success": True}
