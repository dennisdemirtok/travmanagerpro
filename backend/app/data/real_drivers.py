"""
Real Swedish trotting drivers seed data.

Stats are approximations based on publicly available career data from travsport.se.
Win percentages and earnings are used to derive in-game skill stats.
"""


def map_real_driver_to_stats(
    win_pct: float,
    earnings_msek: float,
    years_active: int,
) -> dict:
    """Map real-world performance to in-game driver stats.

    Higher win% and earnings = higher stats and cost.
    """
    # Normalize: 20% win is top-tier
    power = min(1.0, win_pct / 0.20)
    # Earnings factor (normalized to ~500M SEK career max)
    earn_factor = min(1.0, earnings_msek / 500)
    # Combined factor (win% weighted more)
    combined = power * 0.7 + earn_factor * 0.3

    skill = int(35 + combined * 60)
    start_skill = int(30 + combined * 55)
    tactical_ability = int(30 + combined * 60)
    sprint_timing = int(30 + combined * 60)
    gallop_handling = int(35 + combined * 55)
    experience = min(95, 20 + years_active * 3)
    composure = int(40 + combined * 50)

    base_salary = 200_000 + skill * 5_000  # ore/week
    guest_fee = 100_000 + skill * 3_000    # ore/race

    return {
        "skill": min(95, skill),
        "start_skill": min(90, start_skill),
        "tactical_ability": min(95, tactical_ability),
        "sprint_timing": min(95, sprint_timing),
        "gallop_handling": min(90, gallop_handling),
        "experience": experience,
        "composure": min(90, composure),
        "base_salary": base_salary,
        "guest_fee": guest_fee,
    }


# ~25 real Swedish trotting drivers across all tiers
REAL_DRIVERS = [
    # === ELITE TIER (win% 15-20%) ===
    {
        "name": "Örjan Kihlström",
        "driving_style": "tactical",
        "win_pct": 0.18,
        "earnings_msek": 480,
        "years_active": 25,
        "popularity": 95,
    },
    {
        "name": "Björn Goop",
        "driving_style": "offensive",
        "win_pct": 0.17,
        "earnings_msek": 450,
        "years_active": 25,
        "popularity": 92,
    },
    {
        "name": "Erik Adielsson",
        "driving_style": "tactical",
        "win_pct": 0.15,
        "earnings_msek": 350,
        "years_active": 22,
        "popularity": 88,
    },
    # === TOP TIER (win% 12-15%) ===
    {
        "name": "Ulf Ohlsson",
        "driving_style": "hard",
        "win_pct": 0.14,
        "earnings_msek": 320,
        "years_active": 25,
        "popularity": 82,
    },
    {
        "name": "Magnus A Djuse",
        "driving_style": "offensive",
        "win_pct": 0.15,
        "earnings_msek": 150,
        "years_active": 12,
        "popularity": 80,
    },
    {
        "name": "Johan Untersteiner",
        "driving_style": "tactical",
        "win_pct": 0.13,
        "earnings_msek": 180,
        "years_active": 20,
        "popularity": 75,
    },
    {
        "name": "Jorma Kontio",
        "driving_style": "patient",
        "win_pct": 0.13,
        "earnings_msek": 280,
        "years_active": 30,
        "popularity": 70,
    },
    # === GOOD TIER (win% 9-12%) ===
    {
        "name": "Adrian Kolgjini",
        "driving_style": "offensive",
        "win_pct": 0.12,
        "earnings_msek": 120,
        "years_active": 15,
        "popularity": 72,
    },
    {
        "name": "Peter Untersteiner",
        "driving_style": "tactical",
        "win_pct": 0.11,
        "earnings_msek": 200,
        "years_active": 22,
        "popularity": 68,
    },
    {
        "name": "Christoffer Eriksson",
        "driving_style": "tactical",
        "win_pct": 0.11,
        "earnings_msek": 100,
        "years_active": 15,
        "popularity": 65,
    },
    {
        "name": "Stefan Persson",
        "driving_style": "patient",
        "win_pct": 0.10,
        "earnings_msek": 90,
        "years_active": 18,
        "popularity": 60,
    },
    {
        "name": "Daniel Redén",
        "driving_style": "tactical",
        "win_pct": 0.12,
        "earnings_msek": 250,
        "years_active": 20,
        "popularity": 78,
    },
    {
        "name": "Joakim Lövgren",
        "driving_style": "patient",
        "win_pct": 0.10,
        "earnings_msek": 110,
        "years_active": 25,
        "popularity": 55,
    },
    # === MID TIER (win% 6-9%) ===
    {
        "name": "Roger Walmann",
        "driving_style": "patient",
        "win_pct": 0.08,
        "earnings_msek": 80,
        "years_active": 20,
        "popularity": 48,
    },
    {
        "name": "Robert Bergh",
        "driving_style": "tactical",
        "win_pct": 0.09,
        "earnings_msek": 160,
        "years_active": 22,
        "popularity": 62,
    },
    {
        "name": "Svante Båth",
        "driving_style": "tactical",
        "win_pct": 0.08,
        "earnings_msek": 130,
        "years_active": 25,
        "popularity": 55,
    },
    {
        "name": "Jörgen Westholm",
        "driving_style": "soft",
        "win_pct": 0.07,
        "earnings_msek": 60,
        "years_active": 20,
        "popularity": 42,
    },
    {
        "name": "Stefan Melander",
        "driving_style": "tactical",
        "win_pct": 0.08,
        "earnings_msek": 100,
        "years_active": 28,
        "popularity": 50,
    },
    {
        "name": "Lutfi Kolgjini",
        "driving_style": "offensive",
        "win_pct": 0.09,
        "earnings_msek": 90,
        "years_active": 20,
        "popularity": 55,
    },
    # === BUDGET TIER (win% 3-6%) ===
    {
        "name": "Jennifer Tillman",
        "driving_style": "tactical",
        "win_pct": 0.06,
        "earnings_msek": 30,
        "years_active": 12,
        "popularity": 45,
    },
    {
        "name": "Carl Johan Jepson",
        "driving_style": "soft",
        "win_pct": 0.05,
        "earnings_msek": 25,
        "years_active": 15,
        "popularity": 35,
    },
    {
        "name": "Kevin Oscarsson",
        "driving_style": "offensive",
        "win_pct": 0.05,
        "earnings_msek": 20,
        "years_active": 8,
        "popularity": 30,
    },
    {
        "name": "André Eklundh",
        "driving_style": "patient",
        "win_pct": 0.04,
        "earnings_msek": 15,
        "years_active": 10,
        "popularity": 25,
    },
    {
        "name": "Kim Eriksson",
        "driving_style": "soft",
        "win_pct": 0.04,
        "earnings_msek": 12,
        "years_active": 8,
        "popularity": 22,
    },
    {
        "name": "Emilia Leo",
        "driving_style": "tactical",
        "win_pct": 0.03,
        "earnings_msek": 8,
        "years_active": 5,
        "popularity": 28,
    },
]
