"""TravManager — Real Swedish Trotting Tracks

All active trotting tracks in Sweden with properties affecting gameplay.
Region determines travel costs between stables and tracks.
Stretch length affects sprint timing strategy.
"""

# (name, city, region, prestige, distances, has_auto_start, stretch_length_m, notes)
REAL_TRACKS = [
    # Elite / Major tracks
    ("Solvalla", "Stockholm", "östra", 95, [1640, 2140, 2640, 3140], True, 250, "Elitloppet, storlopp"),
    ("Åby", "Göteborg", "västra", 85, [1640, 2140, 2640], True, 200, "V75-bana"),
    ("Jägersro", "Malmö", "södra", 82, [1609, 1640, 2140, 2640], True, 230, "V75-bana, även galopp"),
    ("Bergsåker", "Sundsvall", "norra", 70, [1640, 2140, 2640], True, 300, "Långt upplopp"),
    ("Romme", "Borlänge", "mellersta", 68, [1640, 2140, 2640], True, 180, "V75-bana"),

    # Upper mid-tier
    ("Axevalla", "Skara", "västra", 60, [1640, 2140, 2640], True, 200, "Stayerlopp"),
    ("Eskilstuna", "Eskilstuna", "östra", 58, [1640, 2140, 2640], True, 200, ""),
    ("Gävle", "Gävle", "mellersta", 58, [1640, 2140, 2640], True, 190, ""),
    ("Färjestad", "Karlstad", "västra", 56, [1640, 2140, 2640], True, 200, ""),
    ("Örebro", "Örebro", "mellersta", 55, [1640, 2140, 2640], True, 185, ""),
    ("Halmstad", "Halmstad", "västra", 52, [1640, 2140, 2640], True, 190, ""),

    # Mid-tier
    ("Mantorp", "Mantorp", "östra", 48, [1640, 2140, 2640], True, 180, ""),
    ("Aby", "Norrköping", "östra", 46, [1640, 2140], True, 175, ""),
    ("Sundbyholm", "Eskilstuna", "östra", 44, [1640, 2140, 2640], True, 180, ""),
    ("Kalmar", "Kalmar", "södra", 42, [1640, 2140], True, 165, ""),
    ("Visby", "Visby", "södra", 42, [1640, 2140], True, 170, "Gotland"),
    ("Umåker", "Umeå", "norra", 48, [1640, 2140], True, 175, ""),
    ("Östersund", "Östersund", "norra", 46, [1640, 2140, 2640], True, 180, ""),

    # Smaller tracks
    ("Hagmyren", "Hudiksvall", "norra", 40, [1640, 2140], True, 155, ""),
    ("Boden", "Boden", "norra", 38, [1640, 2140], True, 150, ""),
    ("Bollnäs", "Bollnäs", "norra", 36, [1640, 2140], True, 150, ""),
    ("Lindesberg", "Lindesberg", "mellersta", 35, [1640, 2140], True, 150, ""),
    ("Rättvik", "Rättvik", "mellersta", 34, [1640, 2140], True, 155, ""),
    ("Vaggeryd", "Vaggeryd", "södra", 34, [1640, 2140], True, 150, ""),
    ("Arvika", "Arvika", "västra", 33, [1640, 2140], True, 150, ""),
    ("Åmål", "Åmål", "västra", 32, [1640, 2140], True, 145, ""),

    # Rural / small tracks
    ("Dannero", "Ånge", "norra", 30, [1640, 2140], True, 140, ""),
    ("Hoting", "Hoting", "norra", 25, [1640, 2140], True, 130, "Liten bana, kort upplopp"),
    ("Lycksele", "Lycksele", "norra", 28, [1640, 2140], True, 140, ""),
    ("Skellefteå", "Skellefteå", "norra", 35, [1640, 2140], True, 155, ""),
    ("Strömsholm", "Strömsholm", "östra", 36, [1640, 2140], True, 160, ""),
    ("Karlshamn", "Karlshamn", "södra", 30, [1640, 2140], True, 140, ""),
    ("Täby", "Stockholm", "östra", 38, [1640, 2140], True, 200, "Även galopp"),
]

# Region distance matrix for travel cost calculation
# 0 = same region, 1 = adjacent, 2 = far, 3 = very far
REGION_DISTANCES = {
    ("östra", "östra"): 0,
    ("östra", "västra"): 1,
    ("östra", "södra"): 1,
    ("östra", "norra"): 2,
    ("östra", "mellersta"): 1,
    ("västra", "västra"): 0,
    ("västra", "östra"): 1,
    ("västra", "södra"): 1,
    ("västra", "norra"): 2,
    ("västra", "mellersta"): 1,
    ("södra", "södra"): 0,
    ("södra", "östra"): 1,
    ("södra", "västra"): 1,
    ("södra", "norra"): 3,
    ("södra", "mellersta"): 2,
    ("norra", "norra"): 0,
    ("norra", "östra"): 2,
    ("norra", "västra"): 2,
    ("norra", "södra"): 3,
    ("norra", "mellersta"): 1,
    ("mellersta", "mellersta"): 0,
    ("mellersta", "östra"): 1,
    ("mellersta", "västra"): 1,
    ("mellersta", "södra"): 2,
    ("mellersta", "norra"): 1,
}

# Travel effects by region distance
TRAVEL_EFFECTS = {
    0: {"cost": 0, "energy_loss": 0, "form_impact": 2},        # Home region = small boost
    1: {"cost": 300_000, "energy_loss": 5, "form_impact": 0},   # Adjacent = 3,000 kr
    2: {"cost": 800_000, "energy_loss": 15, "form_impact": -3},  # Far = 8,000 kr
    3: {"cost": 1_500_000, "energy_loss": 25, "form_impact": -5}, # Very far = 15,000 kr
}
