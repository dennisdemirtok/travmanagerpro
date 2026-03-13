"""TravManager — Game Initialization Service"""
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.game_state import GameState, Season, Division
from app.models.race import RaceTrack, RaceSession, Race
from app.models.enums import (
    RaceClass, RaceStartMethod, SurfaceType, WeatherType, SeasonPeriod,
)
from app.data.real_drivers import REAL_DRIVERS, map_real_driver_to_stats
from app.data.real_tracks import REAL_TRACKS
from app.data.real_horses import REAL_HORSES, map_real_to_game_stats, GENDER_MAP


# Season length in game weeks (1 season = 1 horse year)
SEASON_LENGTH_WEEKS = 10

# Weekly race template: (game_day, start_time_swedish, [(name, class, div_level, distance, start_method, prize_pool, entry_fee, min_start_points)])
# game_day 3 = Wednesday, game_day 6 = Saturday (real weekdays)
# Times are in Swedish time (CET/CEST), converted to UTC when scheduling
WEEKLY_RACE_TEMPLATE = [
    (3, "19:00", [  # Wednesday evening session (19:00 Swedish time)
        ("Vardagslopp", RaceClass.EVERYDAY, 6, 2140, RaceStartMethod.AUTO, 5_000_000, 100_000, 0),
        ("Ungdomslopp", RaceClass.AGE_3, None, 1640, RaceStartMethod.AUTO, 4_000_000, 80_000, 0),
        ("Bronsdivisionen", RaceClass.BRONZE, 5, 2140, RaceStartMethod.VOLT, 10_000_000, 200_000, 10),
        ("Vardagssprint", RaceClass.EVERYDAY, 6, 1640, RaceStartMethod.AUTO, 4_000_000, 100_000, 0),
    ]),
    (6, "14:00", [  # Saturday afternoon V75 session (14:00 Swedish time)
        ("Silverdivisionen", RaceClass.SILVER, 3, 2640, RaceStartMethod.VOLT, 20_000_000, 500_000, 30),
        ("V75-1", RaceClass.BRONZE, 4, 2140, RaceStartMethod.VOLT, 15_000_000, 300_000, 15),
        ("V75-2 Stayerlopp", RaceClass.BRONZE, 5, 2640, RaceStartMethod.VOLT, 8_000_000, 200_000, 10),
        ("Bronsdivisionen B", RaceClass.BRONZE, 4, 2140, RaceStartMethod.VOLT, 10_000_000, 200_000, 5),
        ("Gulddivisionen", RaceClass.GOLD, 2, 2140, RaceStartMethod.VOLT, 30_000_000, 800_000, 50),
        ("Ungsprint", RaceClass.AGE_2, None, 1640, RaceStartMethod.AUTO, 6_000_000, 100_000, 0),
        ("Kvällssprint", RaceClass.EVERYDAY, 6, 1640, RaceStartMethod.AUTO, 4_000_000, 100_000, 0),
    ]),
]


async def _seed_real_tracks(db: AsyncSession):
    """Seed all 33 real Swedish trotting tracks."""
    import logging
    logger = logging.getLogger(__name__)

    # Delete old non-real tracks (but keep if they have races)
    existing_result = await db.execute(select(RaceTrack))
    existing = existing_result.scalars().all()
    existing_names = {t.name for t in existing}

    count = 0
    for name, city, region, prestige, distances, has_auto, stretch, notes in REAL_TRACKS:
        if name in existing_names:
            # Update existing track with new fields
            for t in existing:
                if t.name == name:
                    t.region = region
                    t.stretch_length = stretch
                    t.notes = notes
                    break
            continue

        track = RaceTrack(
            name=name, city=city, region=region,
            prestige=prestige,
            available_distances=distances,
            has_auto_start=has_auto,
            stretch_length=stretch,
            notes=notes,
        )
        db.add(track)
        count += 1

    await db.flush()
    if count > 0:
        logger.info(f"Seeded {count} new real tracks")


async def _seed_stallion_registry(db: AsyncSession):
    """Seed the stallion registry with breeding stallions."""
    import logging
    from app.models.breeding import StallionRegistry

    logger = logging.getLogger(__name__)

    # Check if already seeded
    existing = await db.execute(select(StallionRegistry).limit(1))
    if existing.scalar_one_or_none():
        return

    # Swedish trotting stallions (fictional but realistic names and stats)
    STALLIONS = [
        # (name, country, stud_fee_öre, speed, endurance, mentality, sprint, balance, strength, start, prestige, desc)
        ("Nuncio", "IT", 15_000_000, 8, 6, 5, 7, 4, 5, 6, 90,
         "Italiensk elithingst med enastående fart och spurtförmåga."),
        ("Ready Cash", "FR", 20_000_000, 9, 7, 6, 8, 5, 6, 7, 95,
         "Legendarisk fransk hingst. Europas bästa avelsdjur."),
        ("Bold Eagle", "FR", 18_000_000, 8, 8, 7, 7, 6, 5, 5, 92,
         "Stark uthållighetstyp med bra mentalitet."),
        ("Maharajah", "SE", 12_000_000, 7, 6, 5, 8, 5, 4, 6, 85,
         "Svensk elithingst med explosiv spurt."),
        ("Love You", "FR", 10_000_000, 6, 7, 6, 5, 6, 6, 5, 80,
         "Beprövad avelshingst med starka avkommor."),
        ("Viking Kronos", "IT", 8_000_000, 6, 5, 5, 6, 5, 5, 7, 75,
         "Klassisk hingst med bra startförmåga."),
        ("Muscle Hill", "US", 14_000_000, 8, 6, 7, 7, 5, 7, 5, 88,
         "Amerikansk topphingst med rå styrka."),
        ("Readly Express", "SE", 11_000_000, 7, 7, 6, 6, 6, 5, 5, 82,
         "Snabb svensk hingst med bra uthållighet."),
        ("From Above", "SE", 6_000_000, 5, 5, 4, 5, 5, 4, 4, 60,
         "Prisvärd hingst för den som vill prova avel."),
        ("Global Trustworthy", "SE", 4_000_000, 4, 4, 5, 3, 4, 4, 3, 45,
         "Budgethingst med ok mentalitet."),
        ("Papagayo E", "IT", 9_000_000, 7, 5, 5, 7, 4, 5, 6, 78,
         "Italiensk spurtspecialist."),
        ("Propulsion", "SE", 16_000_000, 9, 7, 8, 6, 6, 7, 6, 93,
         "En av Sveriges bästa travhästar genom tiderna."),
    ]

    for name, country, fee, spd, end, men, spr, bal, stg, sta, prest, desc in STALLIONS:
        stallion = StallionRegistry(
            name=name,
            origin_country=country,
            stud_fee=fee,
            speed_bonus=spd,
            endurance_bonus=end,
            mentality_bonus=men,
            sprint_bonus=spr,
            balance_bonus=bal,
            strength_bonus=stg,
            start_bonus=sta,
            prestige=prest,
            description=desc,
            available=True,
        )
        db.add(stallion)

    await db.flush()
    logger.info(f"Seeded {len(STALLIONS)} stallions in breeding registry")


def _compute_scheduled_at(real_week_start: datetime, target_game_week: int, game_day: int, start_time: str) -> datetime:
    """Compute the real UTC datetime for a race session.
    real_week_start is Monday 00:00 UTC of game week 1.
    start_time is in Swedish time (CET = UTC+1).
    """
    # Base date: Monday of the target week
    race_date = real_week_start + timedelta(days=(target_game_week - 1) * 7 + (game_day - 1))
    hour, minute = map(int, start_time.split(":"))
    # Convert Swedish time to UTC (CET = UTC+1, approximate — ignores DST)
    utc_hour = max(0, hour - 1)
    return race_date.replace(hour=utc_hour, minute=minute, second=0, microsecond=0)


async def generate_races_for_week(db: AsyncSession, target_game_week: int):
    """Generate race sessions for a specific game week.
    Called when current week is target_game_week - 1 (races published 1 week ahead).
    Computes real scheduled_at datetime for each session.
    """
    existing = await db.execute(
        select(RaceSession).where(RaceSession.game_week == target_game_week)
    )
    if existing.scalars().first():
        return  # Already generated

    tracks_result = await db.execute(select(RaceTrack))
    tracks = tracks_result.scalars().all()
    if not tracks:
        return

    # Get real_week_start for scheduled_at computation
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    real_week_start = gs.real_week_start if gs else datetime.utcnow()
    # Strip timezone if present
    if real_week_start.tzinfo:
        real_week_start = real_week_start.replace(tzinfo=None)

    rng = random.Random(target_game_week * 1337)

    for game_day, start_time, race_configs in WEEKLY_RACE_TEMPLATE:
        track = rng.choice(tracks)
        weather = rng.choice([WeatherType.CLEAR, WeatherType.CLEAR, WeatherType.CLOUDY, WeatherType.RAIN])

        # Compute real scheduled datetime
        scheduled_at = _compute_scheduled_at(real_week_start, target_game_week, game_day, start_time)

        session = RaceSession(
            scheduled_at=scheduled_at,
            track_id=track.id,
            session_name=f"Omgång V{target_game_week} D{game_day}",
            game_week=target_game_week,
            game_day=game_day,
            start_time=start_time,
            weather=weather,
            temperature=rng.randint(5, 20),
        )
        db.add(session)
        await db.flush()

        for race_num, cfg in enumerate(race_configs, 1):
            name, rc, div, dist, sm, prize, fee, min_pts = cfg
            db.add(Race(
                session_id=session.id,
                race_number=race_num,
                race_name=f"{name} V{target_game_week}",
                race_class=rc,
                division_level=div,
                distance=dist,
                start_method=sm,
                surface=SurfaceType.DIRT,
                prize_pool=prize,
                entry_fee=fee,
                min_entries=6,
                max_entries=12,
                min_start_points=min_pts,
            ))

    await db.flush()


async def get_or_create_game_state(db: AsyncSession) -> GameState:
    result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = result.scalar_one_or_none()
    if gs:
        return gs

    # Bootstrap
    return await bootstrap_game(db)


async def bootstrap_game(db: AsyncSession) -> GameState:
    """Initialize game world: season, division, race schedule."""
    import logging
    logger = logging.getLogger(__name__)

    # Check if already exists
    result = await db.execute(select(GameState).where(GameState.id == 1))
    if result.scalar_one_or_none():
        return (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one()

    # Create season (10 weeks per season = 1 horse year)
    season = Season(
        season_number=1, start_game_week=1, end_game_week=SEASON_LENGTH_WEEKS,
        current_period=SeasonPeriod.REGULAR, is_active=True,
    )
    db.add(season)
    await db.flush()

    # Create divisions
    for level, name in [
        (6, "Vardagsserien"),
        (5, "Bronsdivisionen B"),
        (4, "Bronsdivisionen A"),
        (3, "Silverdivisionen B"),
        (2, "Silverdivisionen A"),
        (1, "Gulddivisionen"),
    ]:
        db.add(Division(level=level, name=name, group_number=1, season_id=season.id))
    await db.flush()

    # Anchor real_week_start to Monday 00:00 UTC of current week
    # so game_day 1=Mon, 3=Wed, 6=Sat matches real weekdays
    now = datetime.utcnow()
    days_since_monday = now.weekday()  # 0=Mon, 1=Tue, ..., 6=Sun
    monday = (now - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Create game state
    gs = GameState(
        id=1, current_game_week=1, current_game_day=1,
        current_season_id=season.id,
        real_week_start=monday,
    )
    db.add(gs)

    # === Seed all 33 real tracks ===
    await _seed_real_tracks(db)

    # === Seed stallion registry for breeding ===
    await _seed_stallion_registry(db)

    # Generate race schedule for weeks 1-2 (week 1 current, week 2 released ahead)
    for week in range(1, 3):
        await generate_races_for_week(db, week)

    rng = random.Random(42)

    # === Seed real drivers from travsport.se data ===
    from app.models.driver import Driver as DriverModel
    from app.models.enums import DrivingStyle

    for rd in REAL_DRIVERS:
        stats = map_real_driver_to_stats(rd["win_pct"], rd["earnings_msek"], rd["years_active"])
        # Set commission rate based on skill/earnings
        commission_rate = 0.10
        if rd["earnings_msek"] > 100:
            commission_rate = 0.22
        elif rd["earnings_msek"] > 50:
            commission_rate = 0.18
        elif rd["earnings_msek"] > 20:
            commission_rate = 0.15
        elif rd["earnings_msek"] > 10:
            commission_rate = 0.12

        real_driver = DriverModel(
            name=rd["name"],
            driving_style=DrivingStyle(rd["driving_style"]),
            popularity=rd["popularity"],
            commission_rate=commission_rate,
            is_npc=False,
            is_real_driver=True,
            **stats,
        )
        db.add(real_driver)
    await db.flush()

    # === Create 10 NPC stables with real horses ===
    from app.models.user import User
    from app.models.stable import Stable
    from app.models.horse import Horse, Bloodline
    from app.models.driver import Driver, DriverContract
    from app.models.breeding import HorsePedigree
    from app.models.enums import (
        HorseGender, HorseStatus, PersonalityType, DrivingStyle,
        ContractType, ShoeType, TrainingProgram, TrainingIntensity,
        SpecialTrait, POSITIVE_TRAITS, NEGATIVE_TRAITS,
    )
    from app.core.auth import hash_password
    from app.data.pedigree_names import generate_pedigree

    # Get all tracks for home track assignment
    tracks_result = await db.execute(select(RaceTrack))
    all_tracks = tracks_result.scalars().all()

    # 10 NPC stables with varied sizes and quality
    # (name, email, reputation, num_horses, driver_skill_lo, driver_skill_hi, commission)
    NPC_STABLES = [
        ("Stall Readly", "npc_readly@trav.se", 70, 15, 75, 88, 0.15),
        ("Team Solvalla", "npc_solvalla@trav.se", 65, 12, 70, 85, 0.14),
        ("Bergsåkers Travsällskap", "npc_bergsaker@trav.se", 55, 12, 65, 80, 0.12),
        ("Axevalla Racing", "npc_axevalla@trav.se", 50, 10, 60, 78, 0.11),
        ("Mantorps Stall", "npc_mantorp@trav.se", 45, 10, 58, 75, 0.10),
        ("Jägersro Travet", "npc_jagersro@trav.se", 50, 10, 60, 78, 0.11),
        ("Romme Stallklubb", "npc_romme@trav.se", 40, 8, 55, 72, 0.10),
        ("Bollnäs Travsällskap", "npc_bollnas@trav.se", 35, 8, 52, 68, 0.09),
        ("Hagmyrens Stall", "npc_hagmyren@trav.se", 30, 8, 50, 65, 0.08),
        ("Åby Stallförening", "npc_aby@trav.se", 45, 7, 55, 72, 0.10),
    ]

    PERSONALITIES = list(PersonalityType)

    # Get bloodlines
    bl_result = await db.execute(select(Bloodline))
    bloodlines = bl_result.scalars().all()
    bl_ids = [b.id for b in bloodlines] if bloodlines else []

    # Sort real horses by tier for distribution
    tier_horses = {"elite": [], "gold": [], "silver": [], "bronze": []}
    for h in REAL_HORSES:
        tier_horses[h[-1]].append(h)

    # Shuffle within tiers for variety
    for tier_list in tier_horses.values():
        rng.shuffle(tier_list)

    # Distribution: elite stables get elite+gold, mid stables get gold+silver, lower get silver+bronze
    # Build a pool for each stable range
    elite_pool = tier_horses["elite"] + tier_horses["gold"][:12]    # 15+12=27 for top 2 stables
    mid_pool = tier_horses["gold"][12:] + tier_horses["silver"]     # remaining gold + all silver
    lower_pool = tier_horses["bronze"]                               # all bronze

    horse_pool_idx = 0
    combined_pool = elite_pool + mid_pool + lower_pool  # Ordered by quality

    for stable_idx, (stable_name, email, reputation, num_horses, drv_lo, drv_hi, commission) in enumerate(NPC_STABLES):
        npc_user = User(
            username=stable_name.lower().replace(" ", "_").replace("å", "a").replace("ä", "a").replace("ö", "o"),
            email=email,
            password_hash=hash_password("npc_no_login_" + stable_name),
            is_npc=True,
        )
        db.add(npc_user)
        await db.flush()

        # Assign a home track
        home_track = all_tracks[stable_idx % len(all_tracks)] if all_tracks else None

        npc_stable = Stable(
            user_id=npc_user.id, name=stable_name,
            balance=100_000_000, reputation=reputation,
            fan_count=rng.randint(500, 3000), is_npc=True,
            home_track_id=home_track.id if home_track else None,
            max_horses=num_horses,
            box_upgrade_level=7,  # NPC stables are fully upgraded
        )
        db.add(npc_stable)
        await db.flush()

        # Assign horses from the pool
        horses_for_stable = combined_pool[horse_pool_idx:horse_pool_idx + num_horses]
        horse_pool_idx += num_horses

        for horse_data in horses_for_stable:
            name_h, gender_str, age, starts, wins, win_pct, place_pct, earnings_kr, tier = horse_data

            # Map real stats to game stats
            game_stats = map_real_to_game_stats(horse_data, rng)

            # Gender mapping
            gender = HorseGender[GENDER_MAP[gender_str]]

            # Generate special traits: 30% chance, elite tier gets more positive
            special_traits = []
            if rng.random() < 0.30:
                if tier in ("elite", "gold") and rng.random() < 0.50:
                    special_traits.append(rng.choice(POSITIVE_TRAITS).value)
                elif rng.random() < 0.20:
                    special_traits.append(rng.choice(POSITIVE_TRAITS).value)
                else:
                    special_traits.append(rng.choice(NEGATIVE_TRAITS).value)

            npc_horse = Horse(
                stable_id=npc_stable.id, name=name_h,
                gender=gender,
                birth_game_week=max(1, 1 - (age * SEASON_LENGTH_WEEKS)),
                age_game_weeks=age * SEASON_LENGTH_WEEKS,
                age_years=age,
                status=HorseStatus.READY, is_npc=True,
                speed=game_stats["speed"],
                endurance=game_stats["endurance"],
                mentality=game_stats["mentality"],
                start_ability=game_stats["start_ability"],
                sprint_strength=game_stats["sprint_strength"],
                balance=game_stats["balance"],
                strength=game_stats["strength"],
                potential_speed=game_stats["potential_speed"],
                potential_endurance=game_stats["potential_endurance"],
                potential_mentality=game_stats["potential_mentality"],
                potential_start=game_stats["potential_start"],
                potential_sprint=game_stats["potential_sprint"],
                potential_balance=game_stats["potential_balance"],
                potential_strength=game_stats["potential_strength"],
                condition=game_stats["condition"],
                energy=game_stats["energy"],
                health=game_stats["health"],
                current_weight=game_stats["current_weight"],
                ideal_weight=game_stats["ideal_weight"],
                form=game_stats["form"],
                mood=game_stats["mood"],
                gallop_tendency=game_stats["gallop_tendency"],
                distance_optimum=game_stats["distance_optimum"],
                racing_instinct=game_stats["racing_instinct"],
                personality_primary=rng.choice(PERSONALITIES),
                personality_secondary=rng.choice(PERSONALITIES),
                personality_revealed=False,
                special_traits=special_traits,
                traits_revealed=False,
                bloodline_id=rng.choice(bl_ids) if bl_ids else None,
                current_training=TrainingProgram.INTERVAL,
                training_intensity=TrainingIntensity.NORMAL,
                current_shoe=ShoeType.NORMAL_STEEL,
                shoe_durability=6,
                total_starts=0,
                total_wins=0,
                total_earnings=0,
            )
            db.add(npc_horse)
            await db.flush()

            # Generate pedigree for NPC horse
            pedigree_data = generate_pedigree("Okänd", "SE", rng=rng)
            pedigree = HorsePedigree(
                horse_id=npc_horse.id,
                sire_name=pedigree_data["sire_name"],
                sire_origin=pedigree_data["sire_origin"],
                dam_name=pedigree_data["dam_name"],
                dam_origin=pedigree_data["dam_origin"],
                sire_sire_name=pedigree_data.get("sire_sire_name"),
                sire_dam_name=pedigree_data.get("sire_dam_name"),
                dam_sire_name=pedigree_data.get("dam_sire_name"),
                dam_dam_name=pedigree_data.get("dam_dam_name"),
            )
            db.add(pedigree)

        # Create NPC driver with quality matching stable tier
        npc_driver = Driver(
            name=f"{stable_name}s Kusk",
            skill=rng.randint(drv_lo, drv_hi),
            start_skill=rng.randint(drv_lo - 5, drv_hi - 5),
            tactical_ability=rng.randint(drv_lo - 5, drv_hi),
            sprint_timing=rng.randint(drv_lo - 5, drv_hi - 5),
            gallop_handling=rng.randint(drv_lo - 5, drv_hi),
            experience=rng.randint(40, 70),
            composure=rng.randint(drv_lo - 10, drv_hi - 5),
            driving_style=rng.choice(list(DrivingStyle)),
            base_salary=300000, guest_fee=200000,
            popularity=rng.randint(30, 60),
            commission_rate=commission,
            is_npc=True,
        )
        db.add(npc_driver)
        await db.flush()

        npc_contract = DriverContract(
            stable_id=npc_stable.id, driver_id=npc_driver.id,
            contract_type=ContractType.PERMANENT,
            salary_per_week=300000,
            starts_game_week=1, ends_game_week=9999,  # Permanent NPC contracts
            is_active=True,
        )
        db.add(npc_contract)

        logger.info(f"NPC stable created: {stable_name} with {len(horses_for_stable)} horses")

    await db.flush()

    # === Simulate historical backlog (8 weeks of past races) ===
    await _simulate_historical_backlog(db, num_weeks=8)

    # === Seed initial NPC horse market listings ===
    from app.services.market_service import seed_npc_listings
    await seed_npc_listings(db, game_week=1, count=3)

    return gs


async def _simulate_historical_backlog(db: AsyncSession, num_weeks: int = 8):
    """Generate and simulate historical races for weeks -num_weeks through -1.
    NPC horses accumulate earnings, wins, and start points organically.
    """
    import logging
    from app.services.npc_entry_service import auto_enter_npc_horses
    from app.services.race_service import simulate_race_session
    from app.services.progression_service import apply_recovery

    logger = logging.getLogger(__name__)
    logger.info(f"Generating historical backlog: {num_weeks} weeks...")

    # Generate race sessions for historical weeks
    for week_offset in range(-num_weeks, 0):
        await generate_races_for_week(db, week_offset)

    await db.flush()

    # Simulate each historical session in chronological order
    sessions_result = await db.execute(
        select(RaceSession)
        .where(RaceSession.game_week < 1)
        .order_by(RaceSession.game_week, RaceSession.game_day)
    )
    sessions = sessions_result.scalars().all()

    for session in sessions:
        logger.info(
            f"Backlog: simulating W{session.game_week} D{session.game_day} "
            f"({session.session_name})"
        )

        # Auto-enter NPC horses
        await auto_enter_npc_horses(db, session.id, session.game_week)

        # Simulate the session
        try:
            await simulate_race_session(db, session.id)
        except Exception as e:
            logger.error(f"Backlog simulation error for {session.id}: {e}")
            continue

        # Apply inter-race recovery (3 game days between sessions)
        await apply_recovery(db, game_days_elapsed=3)

    await db.flush()
    logger.info(f"Historical backlog complete: {len(sessions)} sessions simulated")


def calculate_game_time(game_start: datetime) -> dict:
    """Calculate current game day/week from real time.
    1 real day = 1 game day (1:1 real time).
    real_week_start is anchored to Monday 00:00 UTC so
    game_day 1=Mon, 3=Wed, 6=Sat matches real weekdays.
    """
    now = datetime.utcnow()
    # Strip timezone if present (DB may return tz-aware)
    start = game_start.replace(tzinfo=None) if game_start.tzinfo else game_start
    elapsed_seconds = (now - start).total_seconds()
    elapsed_game_days = int(elapsed_seconds / (24 * 3600))  # 1 real day = 1 game day

    game_week = (elapsed_game_days // 7) + 1
    game_day = (elapsed_game_days % 7) + 1  # 1-7

    return {
        "game_week": game_week,
        "game_day": game_day,
        "total_game_days": elapsed_game_days + 1,
    }


async def get_game_state(db: AsyncSession):
    result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = result.scalar_one_or_none()
    if not gs:
        return None

    # Calculate real-time game clock
    game_time = calculate_game_time(gs.real_week_start)

    # Update stored values to keep them in sync
    gs.current_game_week = game_time["game_week"]
    gs.current_game_day = game_time["game_day"]
    await db.flush()

    season_number = None
    season_period = None
    season_start_week = 1
    if gs.current_season_id:
        sr = await db.execute(select(Season).where(Season.id == gs.current_season_id))
        season = sr.scalar_one_or_none()
        if season:
            season_number = season.season_number
            season_period = season.current_period.value
            season_start_week = season.start_game_week

    # Calculate season-relative week (1..SEASON_LENGTH_WEEKS)
    season_week = game_time["game_week"] - season_start_week + 1
    season_week = max(1, min(season_week, SEASON_LENGTH_WEEKS))

    return {
        "current_game_week": game_time["game_week"],
        "current_game_day": game_time["game_day"],
        "total_game_days": game_time["total_game_days"],
        "current_season": season_number,
        "season_period": season_period,
        "season_week": season_week,
        "season_total_weeks": SEASON_LENGTH_WEEKS,
        "next_race_at": gs.next_race_at.isoformat() if gs.next_race_at else None,
        "total_players": gs.total_active_players,
        "game_start": gs.real_week_start.isoformat(),
    }


async def dev_advance_time(db: AsyncSession, hours: int = 24):
    """DEV ONLY: Advance game time by shifting the start reference backward.
    Default 24h = 1 game day (1:1 real time).
    """
    result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = result.scalar_one_or_none()
    if not gs:
        return None

    # Shift start time backward to simulate time passing (strip tz for DB compat)
    start = gs.real_week_start.replace(tzinfo=None) if gs.real_week_start.tzinfo else gs.real_week_start
    gs.real_week_start = start - timedelta(hours=hours)
    await db.flush()

    game_time = calculate_game_time(gs.real_week_start)
    return {
        "advanced_hours": hours,
        "new_game_week": game_time["game_week"],
        "new_game_day": game_time["game_day"],
    }
