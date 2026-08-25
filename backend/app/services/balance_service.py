"""TravManager — Balansverktyg (sprint 8, DEL F3)

Kör N simuleringar av samma jämna lopp och redovisar fördelningen:
vinstprocent per taktikkombination, galoppfrekvens och snittid.

Målet enligt spec: ingen enskild position/tempo-kombination ska vinna
mer än 30 % i ett jämnt fält.
"""
import logging
import random
from collections import defaultdict

from app.engine.race_engine import (
    RaceEngine, RaceConditions, HorseStats, DriverStats, Tactics,
    RaceEntry as EngineRaceEntry,
    Positioning, Tempo, SprintOrder, GallopSafety, CurveStrategy, WhipUsage,
    StartMethod, ShoeType, Surface, Weather,
)

logger = logging.getLogger(__name__)

POSITIONS = list(Positioning)
TEMPOS = list(Tempo)
COMBOS = [(p, t) for p in POSITIONS for t in TEMPOS]
COMBO_KEYS = [(p.value, t.value) for p, t in COMBOS]

POSITION_LABELS = {
    "lead": "Ledning", "second": "Rygg", "outside": "Utvändigt",
    "trailing": "Bakom rygg", "back": "Bakifrån",
}
TEMPO_LABELS = {
    "offensive": "Offensivt", "balanced": "Balanserat", "cautious": "Avvaktande",
}

MAX_RUNS = 500


def _even_horse(idx: int, rng: random.Random) -> HorseStats:
    """En häst i ett medvetet jämnt fält — små skillnader, ingen favorit."""
    base = 60
    jitter = lambda: base + rng.randint(-2, 2)
    return HorseStats(
        id=f"bal_{idx}", name=f"Testhäst {idx + 1}",
        speed=jitter(), endurance=jitter(), mentality=jitter(),
        start_ability=jitter(), sprint_strength=jitter(),
        balance=jitter(), strength=jitter(),
        condition=80, energy_level=100, health=90, form=50, fatigue=0,
        current_weight=470.0, ideal_weight=470.0, mood=70,
        gallop_tendency=15, weather_sensitivity=50,
        distance_optimum=2140, racing_instinct=50,
        personality_primary="calm", personality_secondary="responsive",
        special_traits=[], is_npc=True, confidence=50,
    )


def _even_driver(idx: int) -> DriverStats:
    return DriverStats(
        id=f"bal_drv_{idx}", name=f"Kusk {idx + 1}", is_npc=True,
        skill=60, start_skill=60, tactical_ability=60, sprint_timing=60,
        gallop_handling=60, experience=60, composure=60,
        driving_style="tactical",
    )


def run_balance_test(
    runs: int = 100,
    field_size: int = 12,
    distance: int = 2140,
    stretch_class: str = "medium",
    seed: int = 20260101,
) -> dict:
    """Kör N lopp med ett jämnt fält och mät hur taktikvalen presterar."""
    runs = max(1, min(runs, MAX_RUNS))
    field_size = max(6, min(field_size, 12))

    rng = random.Random(seed)
    engine = RaceEngine()

    wins = defaultdict(int)
    starts = defaultdict(int)
    podiums = defaultdict(int)
    gallops = defaultdict(int)
    total_gallops = 0
    total_dq = 0
    finish_times = []

    stretch_len = {"short": 140, "medium": 200, "long": 320}[stretch_class]

    for run in range(runs):
        entries = []
        for i in range(field_size):
            # Rotera kombinationerna så alla får lika mycket speltid
            combo = COMBOS[(run * field_size + i) % len(COMBOS)]
            positioning, tempo = combo
            tactics = Tactics(
                positioning=positioning,
                tempo=tempo,
                sprint_order=SprintOrder.NORMAL_400M,
                gallop_safety=GallopSafety.NORMAL,
                curve_strategy=CurveStrategy.MIDDLE,
                whip_usage=WhipUsage.NORMAL,
            )
            entry = EngineRaceEntry(
                horse=_even_horse(i, rng),
                driver=_even_driver(i),
                tactics=tactics,
                shoe=ShoeType.NORMAL_STEEL,
                compatibility_score=60,
            )
            entry.post_position = i + 1
            entries.append(entry)
            starts[(positioning.value, tempo.value)] += 1

        conditions = RaceConditions(
            distance=distance,
            start_method=StartMethod.AUTO,
            surface=Surface.DIRT,
            weather=Weather.CLEAR,
            temperature=12,
            division_level=4,
            stretch_length=stretch_len,
            track_prestige=50,
            stretch_class=stretch_class,
        )
        conditions.prize_pool = 5_000_000

        result = engine.simulate(f"balance_{run}", entries, conditions, seed=seed + run)

        combo_by_id = {
            e.horse.id: (e.tactics.positioning.value, e.tactics.tempo.value)
            for e in entries
        }

        for f in result.finishers:
            combo = combo_by_id.get(f.horse_id)
            if not combo:
                continue
            if f.finish_position == 1:
                wins[combo] += 1
                finish_times.append(f.km_time_seconds)
            if f.finish_position and f.finish_position <= 3:
                podiums[combo] += 1
            if f.gallop_incidents:
                gallops[combo] += f.gallop_incidents
                total_gallops += f.gallop_incidents

        for d in result.disqualified:
            combo = combo_by_id.get(d.horse_id)
            if combo:
                gallops[combo] += d.gallop_incidents
            total_gallops += d.gallop_incidents
            total_dq += 1

    rows = []
    for combo in COMBO_KEYS:
        n = starts[combo]
        if not n:
            continue
        w = wins[combo]
        rows.append({
            "positioning": combo[0],
            "tempo": combo[1],
            "label": f"{POSITION_LABELS.get(combo[0], combo[0])} + {TEMPO_LABELS.get(combo[1], combo[1])}",
            "starts": n,
            "wins": w,
            "win_pct": round(w / n * 100, 1),
            "podiums": podiums[combo],
            "podium_pct": round(podiums[combo] / n * 100, 1),
            "gallops_per_start": round(gallops[combo] / n, 2),
        })

    rows.sort(key=lambda r: r["win_pct"], reverse=True)

    total_starts = sum(starts.values())
    expected_win_pct = round(100 / field_size, 1)
    dominant = [r for r in rows if r["win_pct"] > 30.0]

    return {
        "runs": runs,
        "field_size": field_size,
        "distance": distance,
        "stretch_class": stretch_class,
        "seed": seed,
        "total_starts": total_starts,
        "expected_win_pct": expected_win_pct,
        "gallop_rate": round(total_gallops / max(1, total_starts) * 100, 1),
        "dq_rate": round(total_dq / max(1, total_starts) * 100, 1),
        "avg_winning_km_time": round(sum(finish_times) / len(finish_times), 1) if finish_times else None,
        "spread": round(rows[0]["win_pct"] - rows[-1]["win_pct"], 1) if rows else 0,
        "combos": rows,
        "dominant_combos": dominant,
        "passes": len(dominant) == 0,
        "verdict": (
            "Balanserat — ingen taktikkombination vinner över 30 %."
            if not dominant else
            "OBALANS: " + ", ".join(
                f"{d['label']} vinner {d['win_pct']} %" for d in dominant
            )
        ),
    }
