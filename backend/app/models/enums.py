"""TravManager — Python enums mirroring PostgreSQL enum types"""
from enum import Enum


class HorseStatus(str, Enum):
    READY = "ready"
    FATIGUED = "fatigued"
    INJURED = "injured"
    RESTING = "resting"
    TRAINING = "training"       # At professional trainer
    PREGNANT = "pregnant"
    FOAL = "foal"
    YEARLING = "yearling"
    RETIRED = "retired"


class HorseGender(str, Enum):
    STALLION = "stallion"
    MARE = "mare"
    GELDING = "gelding"


class PersonalityType(str, Enum):
    CALM = "calm"
    HOT = "hot"
    STUBBORN = "stubborn"
    RESPONSIVE = "responsive"
    BRAVE = "brave"
    SENSITIVE = "sensitive"
    TRAINING_EAGER = "training_eager"
    WINNER = "winner"
    STRONG_WILLED = "strong_willed"
    MOODY = "moody"
    FOOD_LOVER = "food_lover"
    LAZY = "lazy"


class DrivingStyle(str, Enum):
    PATIENT = "patient"
    OFFENSIVE = "offensive"
    TACTICAL = "tactical"
    HARD = "hard"
    SOFT = "soft"


class ContractType(str, Enum):
    PERMANENT = "permanent"
    GUEST = "guest"
    APPRENTICE = "apprentice"


class RaceStartMethod(str, Enum):
    VOLT = "volt"
    AUTO = "auto"


class RaceClass(str, Enum):
    V75 = "v75"
    ELITE = "elite"
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    EVERYDAY = "everyday"
    YOUTH = "youth"
    AGE_2 = "age_2"
    AGE_3 = "age_3"
    AGE_4 = "age_4"
    MARE_RACE = "mare_race"
    AMATEUR = "amateur"
    QUALIFIER = "qualifier"


class SurfaceType(str, Enum):
    DIRT = "dirt"
    SYNTHETIC = "synthetic"
    WINTER = "winter"


class ShoeType(str, Enum):
    BAREFOOT = "barefoot"
    LIGHT_ALUMINUM = "light_aluminum"
    NORMAL_STEEL = "normal_steel"
    HEAVY_STEEL = "heavy_steel"
    STUDS = "studs"
    GRIP = "grip"
    BALANCE = "balance"


class TacticPositioning(str, Enum):
    LEAD = "lead"
    SECOND = "second"
    OUTSIDE = "outside"
    TRAILING = "trailing"
    BACK = "back"


class TacticTempo(str, Enum):
    OFFENSIVE = "offensive"
    BALANCED = "balanced"
    CAUTIOUS = "cautious"


class TacticSprint(str, Enum):
    EARLY_600M = "early_600m"
    NORMAL_400M = "normal_400m"
    LATE_250M = "late_250m"


class TacticGallopSafety(str, Enum):
    SAFE = "safe"
    NORMAL = "normal"
    RISKY = "risky"


class TacticCurve(str, Enum):
    INNER = "inner"
    MIDDLE = "middle"
    OUTER = "outer"


class TacticWhip(str, Enum):
    AGGRESSIVE = "aggressive"
    NORMAL = "normal"
    GENTLE = "gentle"


class FeedType(str, Enum):
    HAY_STANDARD = "hay_standard"
    HAY_PREMIUM = "hay_premium"
    HAY_ELITE = "hay_elite"
    OATS = "oats"
    CONCENTRATE_STANDARD = "concentrate_standard"
    CONCENTRATE_PREMIUM = "concentrate_premium"
    CARROTS = "carrots"
    APPLES = "apples"
    ELECTROLYTES = "electrolytes"
    JOINT_SUPPLEMENT = "joint_supplement"
    BIOTIN = "biotin"
    MINERAL_MIX = "mineral_mix"
    BREWERS_GRAIN = "brewers_grain"


class TrainingProgram(str, Enum):
    INTERVAL = "interval"
    LONG_DISTANCE = "long_distance"
    START_TRAINING = "start_training"
    SPRINT_TRAINING = "sprint_training"
    MENTAL_TRAINING = "mental_training"
    STRENGTH_TRAINING = "strength_training"
    BALANCE_TRAINING = "balance_training"
    SWIM_TRAINING = "swim_training"
    TRACK_TRAINING = "track_training"
    REST = "rest"


class TrainingIntensity(str, Enum):
    LIGHT = "light"
    NORMAL = "normal"
    HARD = "hard"
    MAXIMUM = "maximum"


class PressTone(str, Enum):
    HUMBLE = "humble"
    CONFIDENT = "confident"
    PROVOCATIVE = "provocative"


class FacilityType(str, Enum):
    STABLE_BOX = "stable_box"
    TRAINING_TRACK = "training_track"
    START_MACHINE = "start_machine"
    SWIM_POOL = "swim_pool"
    VET_CLINIC = "vet_clinic"
    SMITHY = "smithy"
    HORSE_TRANSPORT = "horse_transport"
    BREEDING_FACILITY = "breeding_facility"
    FAN_SHOP = "fan_shop"
    WALKER = "walker"


class StaffRole(str, Enum):
    TRAINER = "trainer"
    VETERINARIAN = "veterinarian"
    FARRIER = "farrier"
    STABLE_HAND = "stable_hand"


class EventType(str, Enum):
    INJURY = "injury"
    TRANSFER = "transfer"
    RACE = "race"
    SPONSOR = "sponsor"
    ACHIEVEMENT = "achievement"
    STABLE_MAINTENANCE = "stable_maintenance"
    STAFF = "staff"
    BREEDING = "breeding"
    WEATHER = "weather"
    SYSTEM = "system"


class AuctionStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SeasonPeriod(str, Enum):
    PRE_SEASON = "pre_season"
    REGULAR = "regular"
    QUALIFIERS = "qualifiers"
    FINALS = "finals"
    OFF_SEASON = "off_season"


class WeatherType(str, Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    COLD = "cold"
    HOT = "hot"
    WINDY = "windy"


class SpecialTrait(str, Enum):
    # Positive traits (20% chance when generated)
    IRON_HOOVES = "iron_hooves"          # Tappar aldrig skor
    SPRINT_KING = "sprint_king"          # +10% spurtbonus
    RAIN_LOVER = "rain_lover"            # Ingen väderpenalty i regn
    TRAVEL_HARDY = "travel_hardy"        # Ingen resetrötthet
    FAST_LEARNER = "fast_learner"        # Dubbel statsutveckling
    # Negative traits (80% chance when generated)
    GLASS_LEGS = "glass_legs"            # +30% skaderisk
    NERVOUS_STARTER = "nervous_starter"  # -15% startförmåga
    COLD_HATER = "cold_hater"            # Stor penalty i kyla/snö
    TRAVEL_SICK = "travel_sick"          # Dubbel resetrötthet
    SLOW_HEALER = "slow_healer"          # Återhämtning 50% långsammare
    GALLOP_PRONE = "gallop_prone"        # +40% galopprisk
    CROWD_SHY = "crowd_shy"             # Penalty på storbanor (prestige > 70)
    TEMPERAMENTAL = "temperamental"      # -10% kompatibilitet med alla kuskar


POSITIVE_TRAITS = [
    SpecialTrait.IRON_HOOVES,
    SpecialTrait.SPRINT_KING,
    SpecialTrait.RAIN_LOVER,
    SpecialTrait.TRAVEL_HARDY,
    SpecialTrait.FAST_LEARNER,
]

NEGATIVE_TRAITS = [
    SpecialTrait.GLASS_LEGS,
    SpecialTrait.NERVOUS_STARTER,
    SpecialTrait.COLD_HATER,
    SpecialTrait.TRAVEL_SICK,
    SpecialTrait.SLOW_HEALER,
    SpecialTrait.GALLOP_PRONE,
    SpecialTrait.CROWD_SHY,
    SpecialTrait.TEMPERAMENTAL,
]


class CaretakerSpecialty(str, Enum):
    SPEED = "speed"
    ENDURANCE = "endurance"
    MENTALITY = "mentality"
    START_ABILITY = "start_ability"
    SPRINT_STRENGTH = "sprint_strength"
    BALANCE = "balance"
    STRENGTH = "strength"


class CaretakerPersonality(str, Enum):
    METICULOUS = "meticulous"
    CALM = "calm"
    ENERGETIC = "energetic"
    EXPERIENCED = "experienced"
    STRICT = "strict"
    GENTLE = "gentle"


class SulkyType(str, Enum):
    EUROPEAN = "european"        # Standard, balanced
    AMERICAN = "american"        # Lighter, faster, less stable
    RACING = "racing"            # Ultra-light, high risk/reward

class WarmupIntensity(str, Enum):
    LIGHT = "light"              # Save energy, slower start
    NORMAL = "normal"            # Standard warm-up
    INTENSE = "intense"          # Sharp start, costs energy
