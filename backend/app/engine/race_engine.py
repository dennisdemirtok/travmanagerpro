"""
TravManager Race Engine
=======================
Deterministic, step-based harness racing simulation.
Each step = 100 meters. Seeded RNG for replay/verification.
"""

import hashlib
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ============================================================
# ENUMS
# ============================================================

class Positioning(Enum):
    LEAD = "lead"
    SECOND = "second"
    OUTSIDE = "outside"
    TRAILING = "trailing"
    BACK = "back"

class Tempo(Enum):
    OFFENSIVE = "offensive"
    BALANCED = "balanced"
    CAUTIOUS = "cautious"

class SprintOrder(Enum):
    EARLY_600M = "early_600m"
    NORMAL_400M = "normal_400m"
    LATE_250M = "late_250m"

class GallopSafety(Enum):
    SAFE = "safe"
    NORMAL = "normal"
    RISKY = "risky"

class CurveStrategy(Enum):
    INNER = "inner"
    MIDDLE = "middle"
    OUTER = "outer"

class WhipUsage(Enum):
    AGGRESSIVE = "aggressive"
    NORMAL = "normal"
    GENTLE = "gentle"

class StartMethod(Enum):
    VOLT = "volt"
    AUTO = "auto"

class ShoeType(Enum):
    BAREFOOT = "barefoot"
    LIGHT_ALUMINUM = "light_aluminum"
    NORMAL_STEEL = "normal_steel"
    HEAVY_STEEL = "heavy_steel"
    STUDS = "studs"
    GRIP = "grip"
    BALANCE = "balance"

class Weather(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    COLD = "cold"
    HOT = "hot"
    WINDY = "windy"

class Surface(Enum):
    DIRT = "dirt"
    SYNTHETIC = "synthetic"
    WINTER = "winter"


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class HorseStats:
    id: str
    name: str
    is_npc: bool = False

    # Core stats (1-100)
    speed: int = 50
    endurance: int = 50
    mentality: int = 50
    start_ability: int = 50
    sprint_strength: int = 50
    balance: int = 50
    strength: int = 50

    # Physical status
    condition: int = 80
    energy_level: int = 100  # Pre-race energy (fatigue affects this)
    health: int = 90
    form: int = 50
    fatigue: int = 0
    current_weight: float = 475.0
    ideal_weight: float = 475.0
    mood: int = 70

    # Hidden traits
    gallop_tendency: int = 15  # 0-50
    surface_preference: Optional[str] = None
    weather_sensitivity: int = 50
    distance_optimum: int = 2140
    racing_instinct: int = 50

    # Personality
    personality_primary: str = "calm"
    personality_secondary: str = "responsive"

    # Special traits (list of trait value strings)
    special_traits: list = field(default_factory=list)


@dataclass
class DriverStats:
    id: str
    name: str
    is_npc: bool = False

    skill: int = 50
    start_skill: int = 50
    tactical_ability: int = 50
    sprint_timing: int = 50
    gallop_handling: int = 50
    experience: int = 30
    composure: int = 50

    driving_style: str = "tactical"


@dataclass
class Tactics:
    positioning: Positioning = Positioning.SECOND
    tempo: Tempo = Tempo.BALANCED
    sprint_order: SprintOrder = SprintOrder.NORMAL_400M
    gallop_safety: GallopSafety = GallopSafety.NORMAL
    curve_strategy: CurveStrategy = CurveStrategy.MIDDLE
    whip_usage: WhipUsage = WhipUsage.NORMAL
    sulky: str = "european"
    warmup: str = "normal"


@dataclass
class RaceConditions:
    distance: int = 2140
    start_method: StartMethod = StartMethod.AUTO
    surface: Surface = Surface.DIRT
    weather: Weather = Weather.CLEAR
    temperature: int = 12
    wind_speed: int = 5
    track_direction: str = "left"
    division_level: int = 4
    stretch_length: int = 200  # meters — affects sprint timing strategy
    track_prestige: int = 50   # affects crowd_shy trait


@dataclass
class RaceEntry:
    horse: HorseStats
    driver: DriverStats
    tactics: Tactics
    shoe: ShoeType = ShoeType.NORMAL_STEEL
    post_position: int = 1
    handicap_meters: int = 0
    compatibility_score: int = 50
    shared_races: int = 0

    # Runtime state
    position_meters: float = 0.0
    current_speed: float = 0.0
    energy: float = 100.0
    mental_state: float = 1.0
    is_galloping: bool = False
    is_disqualified: bool = False
    gallop_count: int = 0
    energy_drain_modifier: float = 1.0
    sprint_bonus: float = 1.0


@dataclass
class RaceEvent:
    step: int
    distance: int
    event_type: str  # 'start', 'gallop_minor', 'gallop_major', 'gallop_dq', 'sprint', 'overtake', 'finish'
    horse_name: str
    horse_id: str
    text: str
    data: dict = field(default_factory=dict)


@dataclass
class PositionSnapshot:
    horse_id: str
    horse_name: str
    position_meters: float
    energy: float
    speed: float
    is_galloping: bool
    is_disqualified: bool
    rank: int = 0


@dataclass
class StepSnapshot:
    distance: int
    positions: list  # List of PositionSnapshot


@dataclass
class FinishResult:
    horse_id: str
    horse_name: str
    stable_id: str
    driver_name: str
    finish_position: int
    finish_time_seconds: float
    km_time_seconds: float
    km_time_display: str
    prize_money: int
    energy_at_finish: int
    top_speed: float
    gallop_incidents: int
    driver_rating: int
    compatibility_score: int
    sector_times: list
    is_disqualified: bool = False
    dq_reason: str = ""


@dataclass
class RaceResult:
    race_id: str
    distance: int
    start_method: str
    seed: int
    finishers: list  # List of FinishResult
    disqualified: list  # List of FinishResult
    events: list  # List of RaceEvent
    snapshots: list  # List of StepSnapshot


# ============================================================
# SHOE EFFECTS
# ============================================================

SHOE_EFFECTS = {
    ShoeType.BAREFOOT: {
        "speed_mod": 1.02, "gallop_risk_mod": 1.15, "weight_grams": 0,
        "grip_normal": 0.92, "grip_wet": 0.80, "grip_winter": 0.75,
    },
    ShoeType.LIGHT_ALUMINUM: {
        "speed_mod": 1.01, "gallop_risk_mod": 1.05, "weight_grams": 120,
        "grip_normal": 0.97, "grip_wet": 0.90, "grip_winter": 0.85,
    },
    ShoeType.NORMAL_STEEL: {
        "speed_mod": 1.00, "gallop_risk_mod": 1.00, "weight_grams": 350,
        "grip_normal": 1.00, "grip_wet": 0.95, "grip_winter": 0.90,
    },
    ShoeType.HEAVY_STEEL: {
        "speed_mod": 0.98, "gallop_risk_mod": 0.90, "weight_grams": 500,
        "grip_normal": 1.05, "grip_wet": 1.00, "grip_winter": 0.95,
    },
    ShoeType.STUDS: {
        "speed_mod": 0.99, "gallop_risk_mod": 0.95, "weight_grams": 400,
        "grip_normal": 1.00, "grip_wet": 1.02, "grip_winter": 1.10,
    },
    ShoeType.GRIP: {
        "speed_mod": 0.99, "gallop_risk_mod": 0.92, "weight_grams": 380,
        "grip_normal": 1.00, "grip_wet": 1.08, "grip_winter": 1.00,
    },
    ShoeType.BALANCE: {
        "speed_mod": 1.00, "gallop_risk_mod": 0.88, "weight_grams": 250,
        "grip_normal": 1.02, "grip_wet": 0.98, "grip_winter": 0.92,
    },
}

SULKY_EFFECTS = {
    "european": {"speed": 1.00, "gallop_risk": 1.00, "energy_drain": 1.00, "stability": 1.00},
    "american": {"speed": 1.015, "gallop_risk": 1.10, "energy_drain": 0.97, "stability": 0.92},
    "racing": {"speed": 1.025, "gallop_risk": 1.25, "energy_drain": 0.94, "stability": 0.85},
}

WARMUP_EFFECTS = {
    "light": {"start_energy_mod": 1.05, "start_ability_mod": 0.92, "gallop_start_mod": 0.85},
    "normal": {"start_energy_mod": 1.00, "start_ability_mod": 1.00, "gallop_start_mod": 1.00},
    "intense": {"start_energy_mod": 0.93, "start_ability_mod": 1.08, "gallop_start_mod": 1.15},
}


# ============================================================
# COMPATIBILITY ENGINE
# ============================================================

COMPAT_MATRIX = {
    ("patient", "calm"): 65, ("patient", "hot"): 85, ("patient", "stubborn"): 30,
    ("patient", "responsive"): 70, ("patient", "brave"): 55, ("patient", "sensitive"): 80,
    ("offensive", "calm"): 45, ("offensive", "hot"): 50, ("offensive", "stubborn"): 75,
    ("offensive", "responsive"): 60, ("offensive", "brave"): 90, ("offensive", "sensitive"): 25,
    ("tactical", "calm"): 75, ("tactical", "hot"): 65, ("tactical", "stubborn"): 55,
    ("tactical", "responsive"): 85, ("tactical", "brave"): 70, ("tactical", "sensitive"): 60,
    ("hard", "calm"): 50, ("hard", "hot"): 35, ("hard", "stubborn"): 80,
    ("hard", "responsive"): 30, ("hard", "brave"): 85, ("hard", "sensitive"): 20,
    ("soft", "calm"): 70, ("soft", "hot"): 60, ("soft", "stubborn"): 25,
    ("soft", "responsive"): 90, ("soft", "brave"): 55, ("soft", "sensitive"): 95,
}


def calculate_compatibility(horse: HorseStats, driver: DriverStats, shared_races: int = 0) -> int:
    primary = COMPAT_MATRIX.get((driver.driving_style, horse.personality_primary), 50)
    secondary = COMPAT_MATRIX.get((driver.driving_style, horse.personality_secondary), 50)
    base = primary * 0.7 + secondary * 0.3
    exp_bonus = min(15, shared_races * 2)
    if driver.experience > 80:
        base = base * 0.7 + 50 * 0.3
    return int(clamp(base + exp_bonus, 0, 100))


# ============================================================
# TIME CONVERTER
# ============================================================

# Km time in seconds per division level
KM_TIME_TABLE = {
    1: (68.5, 71.0, 74.0),
    2: (70.0, 72.5, 76.0),
    3: (71.5, 74.0, 78.0),
    4: (73.0, 76.0, 80.0),
    5: (75.0, 78.0, 82.0),
    6: (77.0, 80.0, 85.0),
}

PRIZE_DISTRIBUTION = {
    1: 0.50, 2: 0.25, 3: 0.125, 4: 0.0625, 5: 0.035, 6: 0.0275,
    7: 0.00, 8: 0.00, 9: 0.00, 10: 0.00, 11: 0.00, 12: 0.00,
}


def format_km_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining = seconds % 60
    whole_secs = int(remaining)
    tenths = int((remaining - whole_secs) * 10)
    return f"{minutes}.{whole_secs:02d},{tenths}"


# ============================================================
# UTILITY
# ============================================================

def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def generate_race_seed(race_id: str, scheduled_time: str) -> int:
    raw = f"{race_id}:{scheduled_time}:TravManager_v1"
    hash_bytes = hashlib.sha256(raw.encode()).digest()
    return int.from_bytes(hash_bytes[:8], "big")


# ============================================================
# RACE ENGINE
# ============================================================

class RaceEngine:
    STEP_DISTANCE = 100  # meters per step

    def __init__(self):
        self.rng: random.Random = random.Random()
        self.events: list[RaceEvent] = []
        self.snapshots: list[StepSnapshot] = []
        self.sector_tracker: dict[str, list] = {}

    def simulate(
        self,
        race_id: str,
        entries: list[RaceEntry],
        conditions: RaceConditions,
        seed: int,
    ) -> RaceResult:
        self.rng = random.Random(seed)
        self.events = []
        self.snapshots = []
        self.sector_tracker = {e.horse.id: [] for e in entries}
        self.conditions = conditions
        self.distance = conditions.distance
        self.total_steps = self.distance // self.STEP_DISTANCE
        self.entries = entries

        # Pre-race: apply shoe effects, weight, weather, compatibility
        self._apply_pre_race_modifiers(entries, conditions)

        # Pre-race: tactical interactions
        self._calculate_tactical_interactions(entries)

        # Step 0: Start
        self._simulate_start(entries, conditions)
        self.snapshots.append(self._take_snapshot(entries, 0))

        # Narrative checkpoints (meters where we generate commentary)
        narrative_points = set()
        if self.distance >= 1600:
            narrative_points = {500, 1000, self.distance - 600, self.distance - 200}
        elif self.distance >= 1000:
            narrative_points = {400, 800, self.distance - 200}
        else:
            narrative_points = {300, self.distance - 200}
        # Add halfway
        narrative_points.add(self.distance // 2)
        last_narrative_distance = 0

        # Steps 1..N
        for step in range(1, self.total_steps + 1):
            meters = step * self.STEP_DISTANCE
            remaining = self.distance - meters

            for entry in entries:
                if entry.is_disqualified:
                    continue

                target_speed = self._calc_target_speed(entry, remaining, entries)
                actual_speed = self._apply_physics(entry, target_speed, step)
                self._check_gallop(entry, actual_speed, remaining, step)

                if not entry.is_disqualified:
                    actual_speed = self._apply_driver_skill(entry, actual_speed, remaining)
                    entry.position_meters += actual_speed
                    entry.current_speed = actual_speed

                # Track sector times
                self._track_sector(entry, meters)

            self.snapshots.append(self._take_snapshot(entries, meters))

            # Generate narrative at checkpoint distances
            for np in sorted(narrative_points):
                if last_narrative_distance < np <= meters:
                    self._generate_narrative(entries, step, np, remaining)
                    last_narrative_distance = np

        # Compile results
        return self._compile_result(race_id, entries, conditions, seed)

    # ----------------------------------------------------------
    # NARRATIVE GENERATION
    # ----------------------------------------------------------

    def _generate_narrative(self, entries: list[RaceEntry], step: int, distance: int, remaining: int):
        """Generate a narrative event at a specific distance checkpoint."""
        active = [e for e in entries if not e.is_disqualified]
        if not active:
            return

        # Sort by position (leader first)
        ranked = sorted(active, key=lambda e: e.position_meters, reverse=True)
        leader = ranked[0]
        leader_pos = leader.position_meters

        # Determine phase
        if distance <= 500:
            phase = "opening"
            phase_label = "Öppning"
        elif distance <= self.distance // 2:
            phase = "middle"
            phase_label = "Mittfasen"
        elif remaining > 300:
            phase = "backstretch"
            phase_label = "Sista kurvan"
        else:
            phase = "sprint"
            phase_label = "Spurtfas"

        # Build position descriptions
        parts = []
        positions_data = []

        # Leader
        spd_label = f"1.{int(15 + self.rng.uniform(-2, 3))}"
        parts.append(f"{leader.horse.name} ({leader.post_position}) leder i {spd_label}-fart")
        positions_data.append({"horse": leader.horse.name, "pos": 1, "gap": 0})

        # 2nd horse (in rygg / i dödens)
        if len(ranked) >= 2:
            second = ranked[1]
            gap2 = round(leader_pos - second.position_meters, 1)
            if gap2 < 5:
                pos_desc = "sitter i rygg"
            elif gap2 < 15:
                pos_desc = "kör i dödens"
            else:
                pos_desc = f"ligger {gap2:.0f}m efter"
            parts.append(f"{second.horse.name} ({second.post_position}) {pos_desc}")
            positions_data.append({"horse": second.horse.name, "pos": 2, "gap": gap2})

        # 3rd horse
        if len(ranked) >= 3:
            third = ranked[2]
            gap3 = round(leader_pos - third.position_meters, 1)
            positions_data.append({"horse": third.horse.name, "pos": 3, "gap": gap3})

        # Last horse (if many runners)
        if len(ranked) >= 5:
            last = ranked[-1]
            gap_last = round(leader_pos - last.position_meters, 1)
            if gap_last > 30:
                parts.append(f"{last.horse.name} ({last.post_position}) sist med stor lucka")

        # Sprint phase special narrative
        if phase == "sprint" and len(ranked) >= 2:
            second = ranked[1]
            gap = round(leader_pos - second.position_meters, 1)
            if gap < 5:
                parts = [f"Tät uppgörelse! {leader.horse.name} och {second.horse.name} sida vid sida"]
                if len(ranked) >= 3:
                    third = ranked[2]
                    gap3 = round(leader_pos - third.position_meters, 1)
                    if gap3 < 10:
                        parts.append(f"{third.horse.name} kör starkt utifrån")

        text = f"{distance}m — {'. '.join(parts)}."

        self.events.append(RaceEvent(
            step=step, distance=distance, event_type="narrative",
            horse_name=leader.horse.name, horse_id=leader.horse.id,
            text=text,
            data={
                "phase": phase,
                "phase_label": phase_label,
                "leader": leader.horse.name,
                "positions": positions_data[:5],
            }
        ))

    # ----------------------------------------------------------
    # PRE-RACE MODIFIERS
    # ----------------------------------------------------------

    def _apply_pre_race_modifiers(self, entries: list[RaceEntry], cond: RaceConditions):
        for entry in entries:
            horse = entry.horse

            # Starting energy = base - fatigue
            entry.energy = clamp(100 - horse.fatigue * 0.5, 40, 100)

            # Shoe effects
            shoe_fx = SHOE_EFFECTS[entry.shoe]
            entry._shoe_speed_mod = shoe_fx["speed_mod"]
            entry._shoe_gallop_mod = shoe_fx["gallop_risk_mod"]

            # Sulky effects
            sulky_type = entry.tactics.sulky if hasattr(entry.tactics, 'sulky') else "european"
            sulky_fx = SULKY_EFFECTS.get(sulky_type, SULKY_EFFECTS["european"])
            entry._shoe_speed_mod *= sulky_fx["speed"]
            entry._shoe_gallop_mod *= sulky_fx["gallop_risk"]
            entry.sulky_energy_mod = sulky_fx["energy_drain"]
            entry.sulky_stability = sulky_fx["stability"]

            # Grip based on weather
            if cond.weather in (Weather.RAIN, Weather.HEAVY_RAIN):
                entry._grip = shoe_fx["grip_wet"]
            elif cond.weather == Weather.SNOW or cond.surface == Surface.WINTER:
                entry._grip = shoe_fx["grip_winter"]
            else:
                entry._grip = shoe_fx["grip_normal"]

            # Weight effect
            weight_dev = abs(horse.current_weight - horse.ideal_weight) / horse.ideal_weight
            if weight_dev < 0.02:
                entry._weight_mod = 1.0
            elif weight_dev < 0.05:
                entry._weight_mod = 0.97
            elif weight_dev < 0.10:
                entry._weight_mod = 0.92
            else:
                entry._weight_mod = 0.85

            # Weather sensitivity
            bad_weather = cond.weather in (Weather.RAIN, Weather.HEAVY_RAIN, Weather.SNOW, Weather.HOT, Weather.WINDY)
            if bad_weather:
                sensitivity = horse.weather_sensitivity / 100
                entry._weather_mod = 1.0 - sensitivity * 0.08
            else:
                entry._weather_mod = 1.0

            # Surface preference
            if horse.surface_preference and horse.surface_preference == cond.surface.value:
                entry._surface_mod = 1.03
            else:
                entry._surface_mod = 1.0

            # Distance optimum (closer to optimal = better)
            dist_diff = abs(cond.distance - horse.distance_optimum) / 1000
            entry._distance_mod = 1.0 - dist_diff * 0.04

            # Form effect (recent form affects performance ±5%)
            entry._form_mod = 1.0 + (horse.form - 50) / 1000

            # Mood effect
            if horse.mood < 30:
                entry._mood_mod = 0.95
            elif horse.mood > 80:
                entry._mood_mod = 1.02
            else:
                entry._mood_mod = 1.0

            # Compatibility
            compat = entry.compatibility_score
            if compat >= 86:
                entry._compat_mod = 1.08
                entry._compat_gallop_mod = 0.90
            elif compat >= 71:
                entry._compat_mod = 1.05
                entry._compat_gallop_mod = 0.95
            elif compat >= 51:
                entry._compat_mod = 1.03
                entry._compat_gallop_mod = 1.0
            elif compat >= 31:
                entry._compat_mod = 1.0
                entry._compat_gallop_mod = 1.0
            else:
                entry._compat_mod = 0.95
                entry._compat_gallop_mod = 1.10

            # Special traits effects
            entry._trait_sprint_mod = 1.0
            entry._trait_gallop_mod = 1.0
            entry._trait_start_mod = 1.0
            traits = getattr(horse, 'special_traits', None) or []
            for trait in traits:
                if trait == "sprint_king":
                    entry._trait_sprint_mod = 1.10
                elif trait == "rain_lover":
                    if cond.weather in (Weather.RAIN, Weather.HEAVY_RAIN):
                        entry._weather_mod = 1.02  # Override weather penalty
                elif trait == "iron_hooves":
                    entry._shoe_gallop_mod *= 0.85
                elif trait == "fast_learner":
                    pass  # Handled in progression_service
                elif trait == "travel_hardy":
                    pass  # Handled in travel_service
                elif trait == "nervous_starter":
                    entry._trait_start_mod = 0.85
                elif trait == "gallop_prone":
                    entry._trait_gallop_mod = 1.20
                elif trait == "cold_hater":
                    if cond.weather in (Weather.COLD, Weather.SNOW):
                        entry._weather_mod *= 0.90
                elif trait == "crowd_shy":
                    if cond.track_prestige > 70:
                        entry._mood_mod *= 0.93
                elif trait == "temperamental":
                    # Random boost or penalty
                    if self.rng.random() < 0.3:
                        entry._form_mod *= 1.05
                    else:
                        entry._form_mod *= 0.95
                elif trait == "glass_legs":
                    entry.energy_drain_modifier *= 1.15
                elif trait == "slow_healer":
                    pass  # Handled in recovery
                elif trait == "travel_sick":
                    pass  # Handled in travel_service

    def _calculate_tactical_interactions(self, entries: list[RaceEntry]):
        leaders = [e for e in entries if e.tactics.positioning == Positioning.LEAD]
        closers = [e for e in entries if e.tactics.positioning == Positioning.BACK]

        if len(leaders) >= 3:
            for e in leaders:
                e.energy_drain_modifier *= 1.25
            for e in closers:
                e.sprint_bonus *= 1.10
        elif len(leaders) == 0:
            for e in entries:
                e.energy_drain_modifier *= 0.85
            for e in closers:
                e.sprint_bonus *= 0.95

    # ----------------------------------------------------------
    # START PHASE
    # ----------------------------------------------------------

    def _simulate_start(self, entries: list[RaceEntry], cond: RaceConditions):
        for entry in entries:
            h = entry.horse
            d = entry.driver

            # Warmup effects
            warmup = entry.tactics.warmup if hasattr(entry.tactics, 'warmup') else "normal"
            warmup_fx = WARMUP_EFFECTS.get(warmup, WARMUP_EFFECTS["normal"])
            entry.energy *= warmup_fx["start_energy_mod"]
            warmup_start_mod = warmup_fx["start_ability_mod"]

            if cond.start_method == StartMethod.AUTO:
                start_power = (
                    h.start_ability * warmup_start_mod * 0.55
                    + d.start_skill * 0.25
                    + self.rng.gauss(0, 5) * 0.15
                    + entry._compat_mod * 2
                )
                entry.position_meters = (start_power / 100) * 15 - entry.handicap_meters

            else:  # VOLT
                volt_bonus = max(0, (8 - entry.post_position)) * 1.5
                start_power = (
                    h.start_ability * warmup_start_mod * 0.45
                    + h.mentality * 0.20
                    + d.start_skill * 0.20
                    + self.rng.gauss(0, 4) * 0.15
                )
                entry.position_meters = (start_power / 100) * 12 + volt_bonus - entry.handicap_meters

                # Volt gallop risk
                gallop_chance = (
                    h.gallop_tendency * 0.4
                    + (100 - h.mentality) * 0.2
                    + (100 - d.gallop_handling) * 0.1
                ) / 100

                if entry.tactics.positioning == Positioning.LEAD:
                    gallop_chance *= 1.4

                gallop_chance *= entry._shoe_gallop_mod
                gallop_chance *= entry._compat_gallop_mod
                gallop_chance *= warmup_fx["gallop_start_mod"]

                if self.rng.random() < gallop_chance * 0.12:
                    self._trigger_gallop(entry, 0, "start")

            self.events.append(RaceEvent(
                step=0, distance=0, event_type="start",
                horse_name=h.name, horse_id=h.id,
                text=f"{h.name} ({entry.post_position}) startade — position {entry.position_meters:.1f}m",
                data={"position": round(entry.position_meters, 1)}
            ))

    # ----------------------------------------------------------
    # SPEED CALCULATION
    # ----------------------------------------------------------

    def _calc_target_speed(self, entry: RaceEntry, remaining: int, all_entries: list[RaceEntry]) -> float:
        h = entry.horse

        # Base speed
        base = (h.speed * 0.6 + h.endurance * 0.4) / 10

        # Apply all pre-race mods
        base *= entry._shoe_speed_mod
        base *= entry._weight_mod
        base *= entry._weather_mod
        base *= entry._surface_mod
        base *= entry._distance_mod
        base *= entry._form_mod
        base *= entry._mood_mod
        base *= entry._compat_mod
        base *= entry._grip

        # Race phase
        phase_pct = remaining / self.distance
        if phase_pct > 0.70:
            phase = "opening"
        elif phase_pct > 0.25:
            phase = "middle"
        else:
            phase = "sprint"

        # Tempo modifier
        tempo_mods = {
            "opening":  {Tempo.OFFENSIVE: 1.08, Tempo.BALANCED: 1.00, Tempo.CAUTIOUS: 0.92},
            "middle":   {Tempo.OFFENSIVE: 1.04, Tempo.BALANCED: 1.00, Tempo.CAUTIOUS: 0.97},
            "sprint":   {Tempo.OFFENSIVE: 1.02, Tempo.BALANCED: 1.05, Tempo.CAUTIOUS: 1.10},
        }
        target = base * tempo_mods[phase][entry.tactics.tempo]

        # Positioning
        my_rank = self._get_rank(entry, all_entries)
        active = [e for e in all_entries if not e.is_disqualified]
        leader = max(active, key=lambda e: e.position_meters, default=None)

        if entry.tactics.positioning == Positioning.LEAD:
            if my_rank > 1:
                target *= 1.06
            else:
                target *= 1.01
        elif entry.tactics.positioning == Positioning.SECOND:
            if leader and leader != entry:
                target = min(target, leader.current_speed * 0.99)
        elif entry.tactics.positioning == Positioning.OUTSIDE:
            target *= 1.02
            entry.energy_drain_modifier = max(entry.energy_drain_modifier, 1.12)
        elif entry.tactics.positioning == Positioning.TRAILING:
            if leader and leader != entry:
                target = min(target, leader.current_speed * 1.01)
                entry.energy_drain_modifier = max(entry.energy_drain_modifier, 1.15)
        elif entry.tactics.positioning == Positioning.BACK:
            if phase != "sprint":
                target *= 0.94
            else:
                target *= 1.12

        # Sprint zone
        sprint_distances = {
            SprintOrder.EARLY_600M: 600,
            SprintOrder.NORMAL_400M: 400,
            SprintOrder.LATE_250M: 250,
        }
        sprint_dist = sprint_distances[entry.tactics.sprint_order]
        if remaining <= sprint_dist:
            sprint_power = (h.sprint_strength * 0.7 + h.speed * 0.3) / 100
            # Stretch length modifier: long stretch favors early sprint, short favors late
            stretch_factor = self.conditions.stretch_length / 200.0
            if entry.tactics.sprint_order == SprintOrder.EARLY_600M:
                sprint_power *= (1.0 + (stretch_factor - 1) * 0.4)
            elif entry.tactics.sprint_order == SprintOrder.LATE_250M:
                sprint_power *= (1.0 + (1 - stretch_factor) * 0.3)
            target *= (1.0 + sprint_power * 0.2) * entry.sprint_bonus * getattr(entry, '_trait_sprint_mod', 1.0)

            # Racing instinct in tight finishes
            if remaining < 200:
                closest = self._closest_competitor_distance(entry, all_entries)
                if closest < 5:  # Very tight
                    instinct_bonus = h.racing_instinct / 100 * 0.03
                    target *= (1.0 + instinct_bonus)

        # Whip usage
        if phase == "sprint":
            whip_mods = {
                WhipUsage.AGGRESSIVE: 1.02,
                WhipUsage.NORMAL: 1.00,
                WhipUsage.GENTLE: 0.99,
            }
            target *= whip_mods[entry.tactics.whip_usage]

        # Energy limitation
        if entry.energy < 20:
            target *= (entry.energy / 20) * 0.7 + 0.3
        elif entry.energy < 40:
            target *= 0.93
        elif entry.energy < 60:
            target *= 0.97

        return target

    # ----------------------------------------------------------
    # PHYSICS
    # ----------------------------------------------------------

    def _apply_physics(self, entry: RaceEntry, target_speed: float, step: int) -> float:
        h = entry.horse

        # Acceleration limit
        max_accel = 0.3 + (h.speed / 200)
        speed_diff = target_speed - entry.current_speed
        actual_speed = entry.current_speed + clamp(speed_diff, -max_accel, max_accel)

        # Energy drain
        base_speed = (h.speed * 0.6 + h.endurance * 0.4) / 10
        speed_ratio = actual_speed / base_speed if base_speed > 0 else 1.0

        energy_cost = (
            1.0
            + max(0, speed_ratio - 1.0) * 4.0
            + (1.0 - h.endurance / 100) * 0.5
        )

        # Curve energy cost (every ~500m is a curve on a standard track)
        if step % 5 == 0:  # Curve every 500m
            curve_mods = {
                CurveStrategy.INNER: 0.95,   # Shortest path, saves energy
                CurveStrategy.MIDDLE: 1.00,
                CurveStrategy.OUTER: 1.08,   # Longer path, more energy
            }
            curve_energy_cost_mod = curve_mods[entry.tactics.curve_strategy]
            # Sulky stability in curves
            sulky_stab = getattr(entry, 'sulky_stability', 1.0)
            if sulky_stab < 1.0:
                curve_energy_cost_mod *= (2.0 - sulky_stab)  # e.g., 0.85 stability -> 1.15x curve energy
            energy_cost *= curve_energy_cost_mod
            # Balance stat helps in curves
            actual_speed *= (1.0 + (h.balance - 50) / 2000)

        # Strength matters when running outside or against wind
        if entry.tactics.positioning in (Positioning.OUTSIDE, Positioning.TRAILING):
            strength_help = h.strength / 100 * 0.03
            energy_cost *= (1.0 - strength_help)

        # Drain modifier from tactical interactions
        energy_cost *= entry.energy_drain_modifier

        # Sulky energy drain modifier
        sulky_e_mod = getattr(entry, 'sulky_energy_mod', 1.0)
        energy_cost *= sulky_e_mod

        # Mental state
        if entry.mental_state < 0.8:
            energy_cost *= 1.2

        entry.energy = max(0, entry.energy - energy_cost)

        # Small random variation
        actual_speed *= (1.0 + self.rng.gauss(0, 0.008))

        return max(0, actual_speed)

    # ----------------------------------------------------------
    # GALLOP CHECK
    # ----------------------------------------------------------

    def _check_gallop(self, entry: RaceEntry, speed: float, remaining: int, step: int):
        if entry.is_disqualified:
            return

        h = entry.horse
        d = entry.driver

        base_risk = h.gallop_tendency / 100

        # Speed pressure
        base_speed = (h.speed * 0.6 + h.endurance * 0.4) / 10
        speed_ratio = speed / base_speed if base_speed > 0 else 1.0
        if speed_ratio > 1.05:
            base_risk *= (1 + (speed_ratio - 1.05) * 3)

        # Mentality
        base_risk += (100 - h.mentality) / 100 * 0.02

        # Energy depletion
        if entry.energy < 15:
            base_risk *= 2.5
        elif entry.energy < 30:
            base_risk *= 1.5
        elif entry.energy < 50:
            base_risk *= 1.1

        # Balance stat reduces gallop risk
        base_risk *= (1.0 - h.balance / 200)

        # Shoe effect
        base_risk *= entry._shoe_gallop_mod

        # Compatibility effect
        base_risk *= entry._compat_gallop_mod

        # Grip on surface
        if entry._grip < 0.95:
            base_risk *= (1.0 + (1.0 - entry._grip) * 2)

        # Driver safety setting
        safety_mods = {
            GallopSafety.SAFE: 0.6,
            GallopSafety.NORMAL: 1.0,
            GallopSafety.RISKY: 1.5,
        }
        base_risk *= safety_mods[entry.tactics.gallop_safety]

        # Driver handling skill
        base_risk *= (1.0 - d.gallop_handling / 100 * 0.4)

        # Previous gallops in this race increase risk
        base_risk *= (1.0 + entry.gallop_count * 0.3)

        # Random check per step
        if self.rng.random() < base_risk * 0.06:
            self._trigger_gallop(entry, step, f"{self.distance - remaining}m")

    def _trigger_gallop(self, entry: RaceEntry, step: int, location: str):
        d = entry.driver
        h = entry.horse

        recovery_skill = (d.gallop_handling * 0.6 + d.experience * 0.4) / 100
        roll = self.rng.random()

        entry.gallop_count += 1

        if roll < recovery_skill * 0.7:
            # Minor: lose 1-2 lengths
            loss = self.rng.uniform(3, 8)
            entry.position_meters -= loss
            entry.mental_state *= 0.85
            entry.is_galloping = False
            self.events.append(RaceEvent(
                step=step, distance=self.distance - (self.total_steps - step) * self.STEP_DISTANCE,
                event_type="gallop_minor", horse_name=h.name, horse_id=h.id,
                text=f"{h.name} galopperade kortvarigt vid {location} — {d.name} rättade snabbt till.",
                data={"loss_meters": round(loss, 1), "severity": "minor"}
            ))

        elif roll < recovery_skill * 0.9 + 0.3:
            # Major: lose 3-5 lengths
            loss = self.rng.uniform(10, 25)
            entry.position_meters -= loss
            entry.energy -= 10
            entry.mental_state *= 0.6
            entry.is_galloping = False
            self.events.append(RaceEvent(
                step=step, distance=self.distance - (self.total_steps - step) * self.STEP_DISTANCE,
                event_type="gallop_major", horse_name=h.name, horse_id=h.id,
                text=f"{h.name} i kraftig galopp vid {location}! Tappar flera längder.",
                data={"loss_meters": round(loss, 1), "severity": "major"}
            ))

        else:
            # Disqualification
            entry.is_disqualified = True
            entry.is_galloping = True
            self.events.append(RaceEvent(
                step=step, distance=self.distance - (self.total_steps - step) * self.STEP_DISTANCE,
                event_type="gallop_dq", horse_name=h.name, horse_id=h.id,
                text=f"{h.name} DISKVALIFICERAD efter galopp vid {location}.",
                data={"severity": "dq"}
            ))

    # ----------------------------------------------------------
    # DRIVER SKILL
    # ----------------------------------------------------------

    def _apply_driver_skill(self, entry: RaceEntry, speed: float, remaining: int) -> float:
        d = entry.driver

        # General skill bonus (0-5%)
        bonus = 1.0 + (d.skill / 100) * 0.05

        # Tactical bonus in middle phase
        if remaining > 300 and remaining < self.distance * 0.7:
            bonus *= 1.0 + (d.tactical_ability / 100) * 0.02

        # Sprint timing bonus
        if remaining <= 400:
            bonus *= 1.0 + (d.sprint_timing / 100) * 0.04

        # Composure under pressure (tight race)
        active = [e for e in self.entries if not e.is_disqualified]
        if len(active) > 1 and remaining < 300:
            closest = self._closest_competitor_distance(entry, active)
            if closest < 3:
                bonus *= 1.0 + (d.composure / 100) * 0.02

        return speed * bonus

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------

    def _get_rank(self, entry: RaceEntry, all_entries: list[RaceEntry]) -> int:
        active = sorted(
            [e for e in all_entries if not e.is_disqualified],
            key=lambda e: e.position_meters, reverse=True,
        )
        for i, e in enumerate(active):
            if e is entry:
                return i + 1
        return len(active)

    def _closest_competitor_distance(self, entry: RaceEntry, all_entries: list[RaceEntry]) -> float:
        min_dist = float("inf")
        for e in all_entries:
            if e is entry or e.is_disqualified:
                continue
            d = abs(e.position_meters - entry.position_meters)
            if d < min_dist:
                min_dist = d
        return min_dist

    def _track_sector(self, entry: RaceEntry, meters: int):
        # Track every 500m sector
        sector_num = meters // 500
        sectors = self.sector_tracker[entry.horse.id]
        if len(sectors) < sector_num:
            sectors.append({"sector": sector_num, "distance": meters, "speed": entry.current_speed, "energy": entry.energy})

    def _take_snapshot(self, entries: list[RaceEntry], meters: int) -> StepSnapshot:
        active = sorted(entries, key=lambda e: e.position_meters, reverse=True)
        positions = []
        for rank, e in enumerate(active):
            positions.append(PositionSnapshot(
                horse_id=e.horse.id,
                horse_name=e.horse.name,
                position_meters=round(e.position_meters, 1),
                energy=round(e.energy, 1),
                speed=round(e.current_speed, 2),
                is_galloping=e.is_galloping,
                is_disqualified=e.is_disqualified,
                rank=rank + 1,
            ))
        return StepSnapshot(distance=meters, positions=positions)

    # ----------------------------------------------------------
    # RESULTS COMPILATION
    # ----------------------------------------------------------

    def _compile_result(self, race_id: str, entries: list[RaceEntry], cond: RaceConditions, seed: int) -> RaceResult:
        active = sorted(
            [e for e in entries if not e.is_disqualified],
            key=lambda e: e.position_meters, reverse=True,
        )
        dq_entries = [e for e in entries if e.is_disqualified]

        # Calculate times
        div_level = cond.division_level
        fastest, avg, slowest = KM_TIME_TABLE.get(div_level, KM_TIME_TABLE[4])

        finishers = []
        if active:
            winner = active[0]
            winner_power = (winner.horse.speed + winner.horse.endurance) / 2
            power_pct = clamp((winner_power - 40) / 50, 0, 1)
            winner_km_time = avg - (avg - fastest) * power_pct

            if cond.start_method == StartMethod.AUTO:
                winner_km_time -= 0.8

            winner_total = winner_km_time * (cond.distance / 1000)
            winner_pos = winner.position_meters

            for pos_idx, entry in enumerate(active):
                position = pos_idx + 1
                dist_behind = winner_pos - entry.position_meters
                time_behind = dist_behind * 0.35
                total_time = winner_total + time_behind
                km_time = total_time / (cond.distance / 1000)

                # Prize money
                prize_pct = PRIZE_DISTRIBUTION.get(position, 0)
                prize = int(cond.prize_pool * prize_pct) if hasattr(cond, "prize_pool") else 0

                # Driver rating (1-10)
                driver_rating = self._calculate_driver_rating(entry, position, len(active))

                finishers.append(FinishResult(
                    horse_id=entry.horse.id,
                    horse_name=entry.horse.name,
                    stable_id="",  # Set by caller
                    driver_name=entry.driver.name,
                    finish_position=position,
                    finish_time_seconds=round(total_time, 1),
                    km_time_seconds=round(km_time, 1),
                    km_time_display=format_km_time(km_time),
                    prize_money=prize,
                    energy_at_finish=int(entry.energy),
                    top_speed=round(max(s.speed for snap in self.snapshots for s in snap.positions if s.horse_id == entry.horse.id), 2),
                    gallop_incidents=entry.gallop_count,
                    driver_rating=driver_rating,
                    compatibility_score=entry.compatibility_score,
                    sector_times=self.sector_tracker.get(entry.horse.id, []),
                ))

        # DQ entries
        dq_results = []
        for entry in dq_entries:
            dq_results.append(FinishResult(
                horse_id=entry.horse.id,
                horse_name=entry.horse.name,
                stable_id="",
                driver_name=entry.driver.name,
                finish_position=0,
                finish_time_seconds=0,
                km_time_seconds=0,
                km_time_display="galp.",
                prize_money=0,
                energy_at_finish=int(entry.energy),
                top_speed=0,
                gallop_incidents=entry.gallop_count,
                driver_rating=1,
                compatibility_score=entry.compatibility_score,
                sector_times=[],
                is_disqualified=True,
                dq_reason=f"Galopp ({entry.gallop_count} gånger)",
            ))

        return RaceResult(
            race_id=race_id,
            distance=cond.distance,
            start_method=cond.start_method.value,
            seed=seed,
            finishers=finishers,
            disqualified=dq_results,
            events=self.events,
            snapshots=self.snapshots,
        )

    def _calculate_driver_rating(self, entry: RaceEntry, position: int, field_size: int) -> int:
        # Base rating from position relative to expected
        horse_power = (entry.horse.speed + entry.horse.endurance + entry.horse.sprint_strength) / 3
        expected_rank = max(1, int((100 - horse_power) / 100 * field_size))
        outperformance = expected_rank - position

        base = 5  # Average
        base += clamp(outperformance, -4, 4)

        # Bonus for gallop-free race
        if entry.gallop_count == 0:
            base += 1

        # Energy management
        if entry.energy > 10:
            base += 0.5

        return int(clamp(base, 1, 10))


# ============================================================
# NPC HORSE GENERATOR
# ============================================================

HORSE_NAME_PREFIXES = [
    "Storm", "Guld", "Silver", "Blixt", "Natt", "Sol", "Vinter", "Järn",
    "Kung", "Dröm", "Stjärn", "Eld", "Is", "Nord", "Snabb", "Stark",
    "Mörk", "Ljus", "Vind", "Åsk", "Kraft", "Ädel", "Fri", "Blå",
    "Röd", "Svart", "Vit", "Höst", "Vår", "Sommar", "Polar", "Berg",
]

HORSE_NAME_SUFFIXES = [
    "pilen", "svansen", "faxen", "stegen", "prinsen", "dansen",
    "blansen", "kransen", "anden", "lansen", "bollen", "draken",
    "falken", "jansen", "ansen", "mannen", "stenen", "glansen",
    "tansen", "ransen", "vikingen", "baronen", "hjälten", "kungen",
]

NPC_STABLE_NAMES = [
    "Datatraven", "Systemstallet", "AI Trav AB", "Digitalt Stall",
    "Björklunds Stall", "Sjöbergs Trav", "Lundströms Hästar",
    "Nordströms Stall", "Ekbergs Trav", "Holms Racing",
]


class NPCGenerator:
    def __init__(self, rng: random.Random = None):
        self.rng = rng or random.Random()

    def generate_horse_name(self) -> str:
        prefix = self.rng.choice(HORSE_NAME_PREFIXES)
        suffix = self.rng.choice(HORSE_NAME_SUFFIXES)
        return prefix + suffix

    def generate_horse(self, division_level: int, role: str = "STEADY") -> HorseStats:
        base_power = 35 + (division_level * 8)
        nerf = self.rng.uniform(0.85, 0.95)

        stats = {
            "speed": int(clamp(base_power * nerf + self.rng.gauss(0, 8), 20, 95)),
            "endurance": int(clamp(base_power * nerf + self.rng.gauss(0, 8), 20, 95)),
            "mentality": int(clamp(base_power * nerf + self.rng.gauss(0, 10), 20, 95)),
            "start_ability": int(clamp(base_power * nerf + self.rng.gauss(0, 8), 20, 95)),
            "sprint_strength": int(clamp(base_power * nerf + self.rng.gauss(0, 8), 20, 95)),
            "balance": int(clamp(base_power * nerf + self.rng.gauss(0, 7), 20, 95)),
            "strength": int(clamp(base_power * nerf + self.rng.gauss(0, 7), 20, 95)),
        }

        gallop = int(clamp(15 + self.rng.gauss(0, 5), 5, 35))

        if role == "PACEMAKER":
            stats["speed"] += 10
            stats["endurance"] -= 15
        elif role == "CLOSER":
            stats["speed"] -= 8
            stats["sprint_strength"] += 12
        elif role == "WILDCARD":
            gallop = self.rng.randint(20, 40)
            stats["speed"] += self.rng.randint(-5, 15)
        # STEADY = no modifications

        personality_opts = ["calm", "hot", "stubborn", "responsive", "brave", "sensitive"]

        return HorseStats(
            id=f"npc_{self.rng.randint(100000, 999999)}",
            name=self.generate_horse_name(),
            is_npc=True,
            gallop_tendency=gallop,
            personality_primary=self.rng.choice(personality_opts),
            personality_secondary=self.rng.choice(personality_opts),
            **stats,
        )

    def generate_driver(self, division_level: int) -> DriverStats:
        base = 30 + division_level * 7
        return DriverStats(
            id=f"npc_driver_{self.rng.randint(1000, 9999)}",
            name="Systemkusk",
            is_npc=True,
            skill=int(base + self.rng.gauss(0, 5)),
            start_skill=int(base + self.rng.gauss(0, 5)),
            tactical_ability=int(base + self.rng.gauss(0, 5)),
            sprint_timing=int(base + self.rng.gauss(0, 5)),
            gallop_handling=int(base + self.rng.gauss(0, 5)),
            experience=int(base * 0.8),
            composure=int(base + self.rng.gauss(0, 5)),
            driving_style=self.rng.choice(["patient", "offensive", "tactical"]),
        )

    def fill_race_field(
        self,
        player_entries: list[RaceEntry],
        division_level: int,
        min_field: int = 8,
        max_field: int = 12,
    ) -> list[RaceEntry]:
        field = list(player_entries)
        npc_needed = max(0, min_field - len(field))
        npc_needed = max(npc_needed, 2)  # Always at least 2 NPC for variety
        npc_needed = min(npc_needed, max_field - len(field))

        if npc_needed <= 0:
            return field

        # Role distribution
        roles = []
        if npc_needed >= 2:
            roles.extend(["PACEMAKER", "CLOSER"])
            npc_needed -= 2
        for _ in range(npc_needed):
            roles.append(self.rng.choices(
                ["STEADY", "STEADY", "STEADY", "WILDCARD"],
                weights=[3, 3, 3, 1],
            )[0])

        npc_driver = self.generate_driver(division_level)

        for role in roles:
            horse = self.generate_horse(division_level, role)
            tactics = self._npc_tactics(horse, role)
            shoe = self.rng.choice([ShoeType.NORMAL_STEEL, ShoeType.LIGHT_ALUMINUM])

            field.append(RaceEntry(
                horse=horse,
                driver=npc_driver,
                tactics=tactics,
                shoe=shoe,
                compatibility_score=50,
            ))

        # Assign post positions
        self.rng.shuffle(field)
        for i, entry in enumerate(field):
            entry.post_position = i + 1

        return field

    def _npc_tactics(self, horse: HorseStats, role: str) -> Tactics:
        if role == "PACEMAKER":
            return Tactics(
                positioning=Positioning.LEAD,
                tempo=Tempo.OFFENSIVE,
                sprint_order=SprintOrder.NORMAL_400M,
                gallop_safety=GallopSafety.NORMAL,
                sulky="american",
                warmup="intense",
            )
        elif role == "CLOSER":
            return Tactics(
                positioning=Positioning.BACK,
                tempo=Tempo.CAUTIOUS,
                sprint_order=SprintOrder.EARLY_600M,
                gallop_safety=GallopSafety.SAFE,
                sulky="european",
                warmup="light",
            )
        elif role == "WILDCARD":
            return Tactics(
                positioning=self.rng.choice([Positioning.LEAD, Positioning.OUTSIDE]),
                tempo=Tempo.OFFENSIVE,
                sprint_order=SprintOrder.EARLY_600M,
                gallop_safety=GallopSafety.RISKY,
                sulky="racing",
                warmup="intense",
            )
        else:  # STEADY
            return Tactics(
                positioning=Positioning.SECOND,
                tempo=Tempo.BALANCED,
                sprint_order=SprintOrder.NORMAL_400M,
                gallop_safety=GallopSafety.NORMAL,
                sulky="european",
                warmup="normal",
            )


# ============================================================
# QUICK TEST
# ============================================================

if __name__ == "__main__":
    import json

    engine = RaceEngine()
    npc_gen = NPCGenerator(random.Random(42))

    # Create some test entries
    player_horse = HorseStats(
        id="player_h1", name="Bliansen",
        speed=78, endurance=82, mentality=71, start_ability=85,
        sprint_strength=74, balance=65, strength=70,
        gallop_tendency=12, condition=92, form=65, mood=80,
        personality_primary="brave", personality_secondary="responsive",
    )
    player_driver = DriverStats(
        id="player_d1", name="Erik Lindblom",
        skill=82, start_skill=78, tactical_ability=78,
        sprint_timing=85, gallop_handling=80, experience=74, composure=72,
        driving_style="tactical",
    )
    player_entry = RaceEntry(
        horse=player_horse,
        driver=player_driver,
        tactics=Tactics(
            positioning=Positioning.SECOND,
            tempo=Tempo.BALANCED,
            sprint_order=SprintOrder.NORMAL_400M,
            gallop_safety=GallopSafety.NORMAL,
        ),
        shoe=ShoeType.LIGHT_ALUMINUM,
        compatibility_score=calculate_compatibility(player_horse, player_driver, 8),
    )

    # Fill with NPC
    conditions = RaceConditions(
        distance=2140,
        start_method=StartMethod.AUTO,
        surface=Surface.DIRT,
        weather=Weather.CLEAR,
        temperature=14,
        division_level=3,
    )
    conditions.prize_pool = 15000000  # 150,000 kr in öre

    field = npc_gen.fill_race_field([player_entry], division_level=3)
    seed = generate_race_seed("test_001", "2024-01-15T19:30:00")

    result = engine.simulate("test_001", field, conditions, seed)

    print(f"\n{'='*60}")
    print(f"LOPP: 2140m Auto — Division 3")
    print(f"Fält: {len(field)} hästar, Seed: {seed}")
    print(f"{'='*60}\n")

    for f in result.finishers:
        marker = "🏆 " if f.finish_position == 1 else "   "
        npc = " (AI)" if any(e.horse.id == f.horse_id and e.horse.is_npc for e in field) else ""
        print(f"{marker}{f.finish_position}. {f.horse_name:<20}{npc:<6} {f.km_time_display:>8}  "
              f"Energi: {f.energy_at_finish:>3}%  Galopp: {f.gallop_incidents}  "
              f"Kusk: {f.driver_rating}/10")

    for d in result.disqualified:
        print(f"   DQ {d.horse_name:<20} — {d.dq_reason}")

    print(f"\nEvents ({len(result.events)}):")
    for e in result.events:
        if e.event_type != "start":
            print(f"  [{e.event_type}] {e.text}")

    print(f"\nSnapshots: {len(result.snapshots)} steps recorded")
    print(f"Compatibility (Bliansen + Erik): {player_entry.compatibility_score}/100")
