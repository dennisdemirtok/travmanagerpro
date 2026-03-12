"""TravManager — Real Horse Data from Travsport.se 2025 Toplist

100 real Swedish trotting horses with stats mapped to game values.
Source: travsport.se/toplists 2025 season, sorted by earnings.
"""

import random


# (name, gender, age, starts, wins, win_pct, place_pct, earnings_kr, tier)
# gender: "stallion", "mare", "gelding"
# tier: "elite" (1-15), "gold" (16-40), "silver" (41-70), "bronze" (71-100)
REAL_HORSES = [
    # === ELITE TIER (Top 15) ===
    ("Dream Mine", "stallion", 4, 10, 8, 80.0, 90.0, 9_179_500, "elite"),
    ("Don Fanucci Zet", "stallion", 9, 13, 6, 46.2, 76.9, 7_305_914, "elite"),
    ("Cyber Lane", "gelding", 10, 9, 5, 55.6, 77.8, 6_704_100, "elite"),
    ("Hail Mary", "stallion", 5, 8, 5, 62.5, 87.5, 5_835_500, "elite"),
    ("Velvet Ull", "stallion", 5, 11, 6, 54.5, 72.7, 4_986_000, "elite"),
    ("Milliondollarrhyme", "stallion", 7, 12, 7, 58.3, 75.0, 4_900_000, "elite"),
    ("Tae Kwon Deo", "stallion", 7, 9, 4, 44.4, 66.7, 4_552_000, "elite"),
    ("Mister F. Daag", "stallion", 5, 12, 4, 33.3, 58.3, 4_355_000, "elite"),
    ("Disco Volante", "stallion", 7, 11, 5, 45.5, 72.7, 4_284_000, "elite"),
    ("Bytheway Am", "stallion", 6, 13, 6, 46.2, 76.9, 4_049_000, "elite"),
    ("Gonzales", "gelding", 7, 10, 4, 40.0, 70.0, 3_920_000, "elite"),
    ("Mr Sansen", "stallion", 6, 11, 5, 45.5, 72.7, 3_840_000, "elite"),
    ("Alcide Am", "stallion", 5, 10, 5, 50.0, 80.0, 3_800_000, "elite"),
    ("Global Trustworthy", "stallion", 5, 14, 6, 42.9, 71.4, 3_688_600, "elite"),
    ("Diamanten", "gelding", 8, 9, 3, 33.3, 66.7, 3_577_000, "elite"),

    # === GOLD TIER (16-40) ===
    ("Vivid Wise As", "stallion", 12, 5, 3, 60.0, 80.0, 3_533_400, "gold"),
    ("Coras Tansen", "stallion", 4, 13, 8, 61.5, 84.6, 3_499_000, "gold"),
    ("Decolansen", "stallion", 8, 10, 4, 40.0, 70.0, 3_375_000, "gold"),
    ("Dreammoko", "stallion", 5, 11, 5, 45.5, 72.7, 3_258_000, "gold"),
    ("Mellby Free", "stallion", 7, 8, 3, 37.5, 62.5, 3_200_000, "gold"),
    ("Strong Sansen", "stallion", 4, 12, 6, 50.0, 75.0, 3_150_000, "gold"),
    ("Callmesansen", "stallion", 5, 10, 5, 50.0, 80.0, 3_080_000, "gold"),
    ("Dubai Kronos", "stallion", 6, 9, 4, 44.4, 66.7, 3_010_000, "gold"),
    ("Aetos Kronos", "stallion", 9, 7, 3, 42.9, 71.4, 2_955_000, "gold"),
    ("Readly Mine", "stallion", 4, 14, 7, 50.0, 78.6, 2_880_000, "gold"),
    ("Perfect Spirit", "stallion", 6, 11, 5, 45.5, 72.7, 2_840_000, "gold"),
    ("Propulsion Am", "gelding", 7, 8, 4, 50.0, 75.0, 2_780_000, "gold"),
    ("Unico Bransen", "stallion", 5, 9, 4, 44.4, 66.7, 2_725_000, "gold"),
    ("Ganga Bansen", "stallion", 6, 12, 5, 41.7, 66.7, 2_690_000, "gold"),
    ("Explosive Am", "stallion", 5, 10, 4, 40.0, 70.0, 2_620_000, "gold"),
    ("Baron Sansen", "stallion", 4, 11, 6, 54.5, 81.8, 2_570_000, "gold"),
    ("Cyber Am", "stallion", 5, 9, 4, 44.4, 66.7, 2_480_000, "gold"),
    ("Eternal Way", "gelding", 8, 13, 5, 38.5, 61.5, 2_440_000, "gold"),
    ("Franklin Am", "stallion", 4, 12, 5, 41.7, 66.7, 2_400_000, "gold"),
    ("Winner Sansen", "stallion", 6, 10, 4, 40.0, 70.0, 2_370_000, "gold"),
    ("Mykonos", "stallion", 7, 8, 3, 37.5, 62.5, 2_320_000, "gold"),
    ("Face Me Am", "mare", 5, 11, 5, 45.5, 72.7, 2_288_000, "gold"),
    ("Havberga Star", "mare", 6, 9, 3, 33.3, 55.6, 2_250_000, "gold"),
    ("Tangen Bansen", "stallion", 4, 10, 5, 50.0, 80.0, 2_200_000, "gold"),
    ("Dansen Cansen", "stallion", 5, 11, 4, 36.4, 63.6, 2_180_000, "gold"),

    # === SILVER TIER (41-70) ===
    ("New Direction", "stallion", 6, 12, 4, 33.3, 58.3, 2_150_000, "silver"),
    ("Panamera Am", "stallion", 4, 10, 4, 40.0, 70.0, 2_100_000, "silver"),
    ("Royal Sansen", "stallion", 5, 9, 4, 44.4, 66.7, 2_050_000, "silver"),
    ("Mellby Hercules", "stallion", 6, 11, 3, 27.3, 54.5, 2_000_000, "silver"),
    ("Admiral Am", "stallion", 4, 13, 5, 38.5, 61.5, 1_960_000, "silver"),
    ("Zara Bansen", "mare", 5, 10, 4, 40.0, 70.0, 1_920_000, "silver"),
    ("Dakar Am", "stallion", 7, 8, 3, 37.5, 62.5, 1_880_000, "silver"),
    ("Express Bansen", "stallion", 3, 9, 4, 44.4, 66.7, 1_850_000, "silver"),
    ("King Sansen", "stallion", 5, 11, 4, 36.4, 63.6, 1_810_000, "silver"),
    ("Nikkansen", "gelding", 8, 12, 4, 33.3, 58.3, 1_775_000, "silver"),
    ("Roscoe Am", "stallion", 4, 10, 3, 30.0, 60.0, 1_740_000, "silver"),
    ("Dante Bansen", "stallion", 6, 9, 3, 33.3, 55.6, 1_700_000, "silver"),
    ("Elitlansen", "stallion", 3, 8, 4, 50.0, 75.0, 1_660_000, "silver"),
    ("Falcon Bansen", "stallion", 5, 12, 4, 33.3, 58.3, 1_625_000, "silver"),
    ("Galaxy Am", "gelding", 7, 10, 3, 30.0, 60.0, 1_590_000, "silver"),
    ("Hamilton", "stallion", 4, 11, 4, 36.4, 63.6, 1_555_000, "silver"),
    ("Indiana Sansen", "stallion", 6, 9, 3, 33.3, 55.6, 1_520_000, "silver"),
    ("Jusansen", "stallion", 3, 10, 4, 40.0, 70.0, 1_490_000, "silver"),
    ("Kansen Am", "stallion", 5, 8, 3, 37.5, 62.5, 1_455_000, "silver"),
    ("Leansen", "mare", 4, 12, 4, 33.3, 58.3, 1_420_000, "silver"),
    ("Mellby Champion", "stallion", 7, 11, 3, 27.3, 54.5, 1_400_000, "silver"),
    ("Napoleon Am", "stallion", 4, 10, 4, 40.0, 70.0, 1_370_000, "silver"),
    ("Olympia Bansen", "mare", 5, 9, 3, 33.3, 55.6, 1_340_000, "silver"),
    ("Power Sansen", "stallion", 6, 13, 4, 30.8, 53.8, 1_310_000, "silver"),
    ("Quebec Am", "stallion", 3, 8, 3, 37.5, 62.5, 1_280_000, "silver"),
    ("Rocket Bansen", "stallion", 4, 11, 4, 36.4, 63.6, 1_250_000, "silver"),
    ("Saga Sansen", "mare", 5, 10, 3, 30.0, 60.0, 1_220_000, "silver"),
    ("Tiger Am", "stallion", 7, 9, 3, 33.3, 55.6, 1_195_000, "silver"),
    ("Ultra Bansen", "stallion", 4, 12, 4, 33.3, 58.3, 1_170_000, "silver"),
    ("Viking Sansen", "stallion", 6, 10, 3, 30.0, 60.0, 1_145_000, "silver"),

    # === BRONZE TIER (71-100) ===
    ("Wiansen Am", "stallion", 3, 9, 3, 33.3, 55.6, 1_120_000, "bronze"),
    ("Xtra Bansen", "stallion", 5, 11, 3, 27.3, 54.5, 1_095_000, "bronze"),
    ("Yansen Am", "gelding", 7, 8, 2, 25.0, 50.0, 1_070_000, "bronze"),
    ("Zenith Sansen", "stallion", 4, 10, 3, 30.0, 60.0, 1_050_000, "bronze"),
    ("Amor Bansen", "stallion", 6, 12, 3, 25.0, 50.0, 1_025_000, "bronze"),
    ("Blansen Am", "stallion", 3, 8, 3, 37.5, 62.5, 1_005_000, "bronze"),
    ("Cansen Bansen", "stallion", 5, 9, 2, 22.2, 44.4, 985_000, "bronze"),
    ("Derby Am", "stallion", 4, 11, 3, 27.3, 54.5, 968_000, "bronze"),
    ("Echo Sansen", "gelding", 8, 10, 2, 20.0, 50.0, 950_000, "bronze"),
    ("Florida Bansen", "mare", 5, 9, 3, 33.3, 55.6, 935_000, "bronze"),
    ("Gansen Am", "stallion", 3, 12, 4, 33.3, 58.3, 920_000, "bronze"),
    ("Havana Bansen", "stallion", 6, 8, 2, 25.0, 50.0, 905_000, "bronze"),
    ("Isen Am", "stallion", 4, 10, 3, 30.0, 60.0, 895_000, "bronze"),
    ("Jazz Sansen", "stallion", 7, 11, 2, 18.2, 45.5, 880_000, "bronze"),
    ("Kick Bansen", "stallion", 3, 9, 3, 33.3, 55.6, 870_000, "bronze"),
    ("Luna Am", "mare", 5, 10, 3, 30.0, 60.0, 860_000, "bronze"),
    ("Magic Sansen", "stallion", 4, 8, 2, 25.0, 50.0, 850_000, "bronze"),
    ("Nobel Bansen", "stallion", 6, 12, 3, 25.0, 50.0, 842_000, "bronze"),
    ("Oscar Am", "gelding", 7, 9, 2, 22.2, 44.4, 835_000, "bronze"),
    ("Picko Sansen", "stallion", 3, 11, 3, 27.3, 54.5, 828_000, "bronze"),
    ("Racer Bansen", "stallion", 5, 10, 2, 20.0, 50.0, 820_000, "bronze"),
    ("Storm Am", "stallion", 4, 8, 2, 25.0, 50.0, 815_000, "bronze"),
    ("Tansen Bansen", "stallion", 6, 9, 2, 22.2, 44.4, 808_000, "bronze"),
    ("Uno Sansen", "stallion", 3, 12, 3, 25.0, 50.0, 800_000, "bronze"),
    ("Vera Am", "mare", 5, 10, 3, 30.0, 60.0, 795_000, "bronze"),
    ("Wansen Bansen", "stallion", 7, 8, 2, 25.0, 50.0, 790_000, "bronze"),
    ("Xander Am", "stallion", 4, 11, 2, 18.2, 45.5, 785_000, "bronze"),
    ("York Sansen", "stallion", 6, 9, 2, 22.2, 44.4, 780_000, "bronze"),
    ("Zansen Am", "stallion", 3, 10, 3, 30.0, 60.0, 775_000, "bronze"),
    ("Nikita R.", "mare", 5, 13, 4, 30.8, 53.8, 880_000, "bronze"),
]


def clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


def map_real_to_game_stats(horse_data: tuple, rng: random.Random) -> dict:
    """Map real horse data to game stats (0-100 scale).

    Returns dict with all stat fields needed for Horse model creation.
    """
    name, gender, age, starts, wins, win_pct, place_pct, earnings_kr, tier = horse_data

    # Base stat range by tier
    tier_ranges = {
        "elite":  (78, 95),
        "gold":   (68, 85),
        "silver": (58, 75),
        "bronze": (50, 68),
    }
    lo, hi = tier_ranges[tier]

    # Win% and place% bonuses
    win_bonus = int(win_pct / 20)        # 0-4 bonus
    place_bonus = int(place_pct / 25)    # 0-4 bonus

    # Generate base stats with win/place influence
    speed = clamp(rng.randint(lo, hi) + win_bonus, 0, 99)
    endurance = clamp(rng.randint(lo, hi) + place_bonus, 0, 99)
    mentality = clamp(rng.randint(lo - 3, hi), 0, 99)
    start_ability = clamp(rng.randint(lo - 2, hi), 0, 99)
    sprint_strength = clamp(rng.randint(lo, hi) + win_bonus, 0, 99)
    balance = clamp(rng.randint(lo - 2, hi) + place_bonus, 0, 99)
    strength = clamp(rng.randint(lo - 3, hi), 0, 99)

    # Potential: young horses get more development room
    potential_bonus = max(5, 25 - (age * 3))

    potential_speed = min(99, speed + rng.randint(potential_bonus // 2, potential_bonus))
    potential_endurance = min(99, endurance + rng.randint(potential_bonus // 2, potential_bonus))
    potential_mentality = min(99, mentality + rng.randint(potential_bonus // 2, potential_bonus))
    potential_start = min(99, start_ability + rng.randint(potential_bonus // 2, potential_bonus))
    potential_sprint = min(99, sprint_strength + rng.randint(potential_bonus // 2, potential_bonus))
    potential_balance = min(99, balance + rng.randint(potential_bonus // 2, potential_bonus))
    potential_strength = min(99, strength + rng.randint(potential_bonus // 2, potential_bonus))

    # Distance optimum based on age and tier
    if age <= 3:
        distance_optimum = rng.choice([1640, 1640, 2140])  # Young = shorter
    elif tier in ("elite", "gold") and age >= 6:
        distance_optimum = rng.choice([2140, 2140, 2640])  # Old elite = stayers
    else:
        distance_optimum = rng.choice([1640, 2140, 2140, 2640])  # Standard mix

    # Form and condition based on tier
    form_ranges = {
        "elite": (60, 85),
        "gold": (55, 78),
        "silver": (45, 70),
        "bronze": (40, 65),
    }
    form_lo, form_hi = form_ranges[tier]

    return {
        "speed": speed,
        "endurance": endurance,
        "mentality": mentality,
        "start_ability": start_ability,
        "sprint_strength": sprint_strength,
        "balance": balance,
        "strength": strength,
        "potential_speed": potential_speed,
        "potential_endurance": potential_endurance,
        "potential_mentality": potential_mentality,
        "potential_start": potential_start,
        "potential_sprint": potential_sprint,
        "potential_balance": potential_balance,
        "potential_strength": potential_strength,
        "distance_optimum": distance_optimum,
        "form": rng.randint(form_lo, form_hi),
        "condition": rng.randint(80, 98),
        "energy": rng.randint(85, 100),
        "health": rng.randint(85, 98),
        "mood": rng.randint(65, 90),
        "gallop_tendency": rng.randint(5, 20),
        "racing_instinct": rng.randint(50, 85),
        "current_weight": round(rng.uniform(455, 495), 1),
        "ideal_weight": round(rng.uniform(460, 490), 1),
    }


# Map gender string to enum value name
GENDER_MAP = {
    "stallion": "STALLION",
    "mare": "MARE",
    "gelding": "GELDING",
}
