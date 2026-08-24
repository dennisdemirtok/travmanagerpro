"""TravManager — Hästvärdering (Ekonomi 2.0, del B4)

Beräknar ett marknadsvärde i öre för en häst utifrån:
stats, ålder, form, intjänat, traits, hälsa och avelspotential.

Skalan är kalibrerad mot befintliga NPC-listningar i market_service
(snittstat 50 ≈ 30 000 kr) så att spelaren inte upplever prischock.
"""
import logging

from app.models.enums import HorseGender, HorseStatus, POSITIVE_TRAITS, NEGATIVE_TRAITS

logger = logging.getLogger(__name__)

# Vikter per stat — fart och uthållighet driver värdet mest
STAT_WEIGHTS = {
    "speed": 1.25,
    "endurance": 1.15,
    "sprint_strength": 1.05,
    "start_ability": 0.85,
    "mentality": 0.75,
    "balance": 0.55,
    "strength": 0.55,
}

# Ålderskurva: multiplikator på grundvärdet
AGE_MULTIPLIER = {
    2: 1.05, 3: 1.15, 4: 1.12, 5: 1.05, 6: 1.00, 7: 0.92,
    8: 0.78, 9: 0.60, 10: 0.44, 11: 0.30, 12: 0.20,
}
AGE_MULTIPLIER_OLD = 0.12  # 13+

# Superlinjär grundkurva: en elithäst ska kosta mångdubbelt mer än en medelmåtta.
# power 50 → 30 000 kr, power 70 → 60 000 kr, power 95 → ~123 000 kr
BASE_AT_AVERAGE = 3_000_000    # öre vid power 50
POWER_EXPONENT = 2.2
MIN_VALUE = 300_000            # 3 000 kr — ingen häst är värdelös
TRAIT_STEP = 0.08              # ±8 % per trait

_POSITIVE = {t.value for t in POSITIVE_TRAITS}
_NEGATIVE = {t.value for t in NEGATIVE_TRAITS}


def _weighted_power(horse) -> float:
    """Viktat statsnitt 1-100."""
    total = 0.0
    weight_sum = 0.0
    for stat, weight in STAT_WEIGHTS.items():
        total += (getattr(horse, stat, 40) or 40) * weight
        weight_sum += weight
    return total / weight_sum


def _potential_power(horse) -> float:
    pots = [
        horse.potential_speed, horse.potential_endurance, horse.potential_sprint,
        horse.potential_start, horse.potential_mentality,
        horse.potential_balance, horse.potential_strength,
    ]
    valid = [p for p in pots if p]
    return sum(valid) / len(valid) if valid else 70.0


def calculate_horse_value(horse) -> int:
    """Returnerar marknadsvärde i öre."""
    power = _weighted_power(horse)
    value = BASE_AT_AVERAGE * ((max(1.0, power) / 50.0) ** POWER_EXPONENT)

    age = horse.age_years or 3
    value *= AGE_MULTIPLIER.get(age, AGE_MULTIPLIER_OLD)

    # Outnyttjad potential är värd pengar på unga hästar
    if age <= 5:
        headroom = max(0.0, _potential_power(horse) - power)
        value += headroom * 38_000 * (1.0 if age <= 3 else 0.6)

    # Form: 50 = neutral
    form = horse.form if horse.form is not None else 50
    value *= 0.85 + (form / 100.0) * 0.30

    # Meriter — 25 % av intjänat kapitaliseras
    value += (horse.total_earnings or 0) * 0.25

    # Segerprocent premieras
    starts = horse.total_starts or 0
    if starts >= 5:
        win_pct = (horse.total_wins or 0) / starts
        value *= 1.0 + min(0.35, win_pct * 0.9)

    # Traits
    traits = horse.special_traits or []
    trait_mod = 1.0
    for t in traits:
        key = t.value if hasattr(t, "value") else str(t)
        if key in _POSITIVE:
            trait_mod += TRAIT_STEP
        elif key in _NEGATIVE:
            trait_mod -= TRAIT_STEP
    value *= max(0.5, trait_mod)

    # Avelsvärde — bra ston/hingstar i rätt ålder
    if age >= 4 and power >= 60:
        gender = horse.gender.value if hasattr(horse.gender, "value") else str(horse.gender)
        if gender in ("mare", "stallion"):
            value *= 1.18

    # Hälsa & skada
    health = horse.health if horse.health is not None else 90
    value *= 0.70 + (health / 100.0) * 0.30
    status = horse.status.value if hasattr(horse.status, "value") else str(horse.status)
    if status == HorseStatus.INJURED.value:
        value *= 0.60
    elif status == HorseStatus.RETIRED.value:
        value *= 0.35

    return max(MIN_VALUE, int(value))


def value_breakdown(horse) -> dict:
    """Detaljerad uppdelning för UI (Marknad / Hästkort)."""
    power = _weighted_power(horse)
    age = horse.age_years or 3
    return {
        "value": calculate_horse_value(horse),
        "power": round(power, 1),
        "age": age,
        "age_multiplier": AGE_MULTIPLIER.get(age, AGE_MULTIPLIER_OLD),
        "potential_headroom": round(max(0.0, _potential_power(horse) - power), 1),
        "form": horse.form,
        "earnings": horse.total_earnings or 0,
        "traits": horse.special_traits or [],
    }
