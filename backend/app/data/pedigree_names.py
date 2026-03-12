"""TravManager — Pedigree Name Pools

Random horse names for generating pedigree ancestors.
Mix of Swedish, French, American and Italian trotting names.
"""

import random

SIRE_NAMES = [
    # Swedish
    "Doneransen", "Vikingen", "Stormblansen", "Nordstjärnan", "Guldpilen",
    "Iskungen", "Silverprinsen", "Blixten", "Eldfaxen", "Stormvargen",
    "Vikingablodet", "Norrlandskungen", "Dalmansen", "Fjällräven", "Havsbisen",
    "Kraftfull", "Snabbjansen", "Torvansen", "Gångaren", "Tempansen",
    "Stallansen", "Blåbärsansen", "Åskmolnet", "Ragnarök", "Frostbiten",

    # American
    "American Winner", "Credit Winner", "Conway Hall", "Andover Hall",
    "Victory Dream", "Pine Chip", "Speed Force", "Valley Victor",
    "Mach Three", "Super Bowl", "Western Ideal", "Western Terror",
    "Hambletonian", "Speedy Crown", "Lindy Champion",

    # French
    "Ouragan de Celland", "Love You", "Coktail Jet", "Jag de Bellouet",
    "Royal Dream", "Timoko", "Bilibili", "Bellino II", "Ténor de Baune",
    "Jasmin de Flore", "Kepi Vert", "Look de Star", "Mon Tourbillon",

    # Italian
    "Varenne", "Zenit", "Moni Maker", "Vivid Wise As", "Ringostarr Tansen",
]

DAM_NAMES = [
    # Swedish
    "Drottningen", "Stjärnglansen", "Månskensflickan", "Solrosetten", "Vindflöjten",
    "Fjällrosen", "Blomsterdansen", "Midnattssolen", "Polstjärnan", "Ljusglimt",
    "Vårblomman", "Isdrömmen", "Silvernymfen", "Snödrottningen", "Midsommardröm",
    "Norrskensflickan", "Skogsfrun", "Daggdroppen", "Sagostjärnan", "Regnbågen",
    "Guldstjärnan", "Diamantflickan", "Kristallflickan", "Änglavingen", "Dimmornas",

    # International
    "Lawn Tennis", "Muscle Beauty", "Dream Along", "Star Sensation",
    "Indy de Vive", "Kidea", "Kissy Suzuki", "Tiba Lavec",
    "Another Gill", "Donerail", "Paris Killean", "Volo Queen",
    "Panne de Moteur", "Aung San Suu Kyi", "Miss Versatility",
    "Dancing Diamonds", "Flirting Around", "Lucky Lady",
    "Speedy Princess", "Royal Maiden", "Crystal Dream",
    "Midnight Rose", "Silver Belle", "Golden Girl",
    "Winter Queen", "Spring Melody", "Autumn Star",
]

# For great-grandparents (shorter pool, less detail needed)
ANCESTOR_NAMES = SIRE_NAMES + DAM_NAMES + [
    "Viking Express", "Nordic Star", "Baltic Prince", "Scandinavian Dream",
    "Northern Dancer", "Southern Star", "Eastern Promise", "Western Legend",
    "Royal Command", "Noble Warrior", "Star Command", "Thunder Road",
    "Lightning Bolt", "Gentle Breeze", "Storm Warning", "Arctic Fox",
    "Snow Leopard", "Wild Mustang", "Golden Eagle", "Silver Hawk",
    "Diamond Creek", "Crystal Lake", "Pine Forest", "Meadow Brook",
]


def generate_pedigree(stallion_name: str, stallion_origin: str, rng: random.Random = None) -> dict:
    """Generate a random 3-generation pedigree for a horse.

    Returns dict compatible with HorsePedigree model.
    """
    if rng is None:
        rng = random.Random()

    dam_name = rng.choice(DAM_NAMES)
    dam_origin = rng.choice(["SE", "SE", "SE", "FR", "US", "IT"])

    # Grandparents (sire's parents)
    sire_sire = rng.choice(SIRE_NAMES)
    sire_dam = rng.choice(DAM_NAMES)

    # Grandparents (dam's parents)
    dam_sire = rng.choice(SIRE_NAMES)
    dam_dam = rng.choice(DAM_NAMES)

    return {
        "sire_name": stallion_name,
        "sire_origin": stallion_origin,
        "dam_name": dam_name,
        "dam_origin": dam_origin,
        "sire_sire_name": sire_sire,
        "sire_dam_name": sire_dam,
        "dam_sire_name": dam_sire,
        "dam_dam_name": dam_dam,
    }
