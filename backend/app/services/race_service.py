"""TravManager — Race Service"""
import random
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.race import Race, RaceEntry, RaceSession, RaceTrack, RaceResultSummary
from app.models.horse import Horse
from app.models.driver import Driver, DriverContract, DriverHorseHistory
from app.models.stable import Stable
from app.models.game_state import GameState
from app.engine.race_engine import (
    RaceEngine, NPCGenerator, RaceConditions,
    HorseStats, DriverStats, Tactics,
    RaceEntry as EngineRaceEntry,
    Positioning, Tempo, SprintOrder, GallopSafety,
    CurveStrategy, WhipUsage,
    StartMethod, ShoeType as EngineShoeType,
    Surface, Weather,
    calculate_compatibility, generate_race_seed, format_km_time,
)
from app.models.enums import (
    TacticPositioning, TacticTempo, TacticSprint,
    TacticGallopSafety, TacticCurve, TacticWhip,
)
from app.services.horse_service import _horse_to_engine_stats, _driver_to_engine_stats
from app.services import finance_service, event_service
from app.services.game_init_service import calculate_game_time


PLACEMENT_POINTS = {1: 40, 2: 25, 3: 15, 4: 5}

DAY_NAMES = {
    1: "Måndag", 2: "Tisdag", 3: "Onsdag", 4: "Torsdag",
    5: "Fredag", 6: "Lördag", 7: "Söndag",
}


async def calculate_start_points(db: AsyncSession, horse_id) -> dict:
    """Calculate start points based on last 5 race results.

    Points = placement_points + earnings_points
    Placement: 1st=40, 2nd=25, 3rd=15, 4th=5
    Earnings: sum(prize_money from last 5) / 100_000
    """
    results = await db.execute(
        select(RaceResultSummary)
        .where(RaceResultSummary.horse_id == horse_id)
        .order_by(RaceResultSummary.game_week.desc())
        .limit(5)
    )
    summaries = results.scalars().all()

    placement_pts = sum(PLACEMENT_POINTS.get(s.finish_position, 0) for s in summaries)
    total_earnings = sum(s.prize_money for s in summaries)
    earnings_pts = total_earnings // 100_000

    last_5 = [
        {
            "position": s.finish_position,
            "prize_money": s.prize_money,
            "race_class": s.race_class.value if hasattr(s.race_class, 'value') else str(s.race_class),
            "game_week": s.game_week,
        }
        for s in summaries
    ]

    return {
        "total": placement_pts + earnings_pts,
        "placement_points": placement_pts,
        "earnings_points": earnings_pts,
        "last_5_results": last_5,
    }


def _check_entry_deadline(game_time: dict, session) -> bool:
    """Return True if the entry deadline has passed (can no longer enter).
    Deadline is 1 game day before the race session.
    """
    deadline_week = session.game_week
    deadline_day = session.game_day - 1
    if deadline_day < 1:
        deadline_week -= 1
        deadline_day = 7

    current_total = (game_time["game_week"] - 1) * 7 + game_time["game_day"]
    deadline_total = (deadline_week - 1) * 7 + deadline_day

    return current_total >= deadline_total


async def get_race_schedule(db: AsyncSession, stable_id=None):
    """Get all race sessions with races (simulated shown last)."""
    sessions_result = await db.execute(
        select(RaceSession)
        .options(
            selectinload(RaceSession.track),
            selectinload(RaceSession.races).selectinload(Race.entries),
        )
        .order_by(RaceSession.is_simulated, RaceSession.scheduled_at)
        .limit(20)
    )
    sessions = sessions_result.scalars().unique().all()

    result = []
    for s in sessions:
        races = []
        for r in s.races:
            entries_count = len([e for e in r.entries if not e.is_scratched])
            your_entries = []
            if stable_id:
                your_entries = [
                    {"horse_id": str(e.horse_id), "driver_id": str(e.driver_id)}
                    for e in r.entries if e.stable_id == stable_id and not e.is_scratched
                ]
            races.append({
                "id": str(r.id),
                "race_name": r.race_name,
                "race_class": r.race_class.value,
                "distance": r.distance,
                "start_method": r.start_method.value,
                "prize_pool": r.prize_pool,
                "entry_fee": r.entry_fee,
                "current_entries": entries_count,
                "max_entries": r.max_entries,
                "your_entries": your_entries,
                "division_level": r.division_level,
                "surface": r.surface.value if r.surface else "dirt",
                "min_start_points": r.min_start_points,
            })

        # Calculate entry deadline
        deadline_week = s.game_week
        deadline_day = (s.game_day if hasattr(s, 'game_day') and s.game_day else 1) - 1
        if deadline_day < 1:
            deadline_week -= 1
            deadline_day = 7

        game_day = s.game_day if hasattr(s, 'game_day') and s.game_day else 1
        day_name = DAY_NAMES.get(game_day, "Okänd")

        # Collect all driver IDs already booked in this session (for your stable)
        booked_driver_ids = set()
        if stable_id:
            for r in s.races:
                for e in r.entries:
                    if e.stable_id == stable_id and not e.is_scratched:
                        booked_driver_ids.add(str(e.driver_id))

        result.append({
            "id": str(s.id),
            "scheduled_at": s.scheduled_at.isoformat(),
            "track_name": s.track.name if s.track else "",
            "track_city": s.track.city if s.track else "",
            "track_region": s.track.region if s.track else "",
            "weather": s.weather.value if s.weather else "clear",
            "temperature": s.temperature,
            "start_time": s.start_time or "",
            "races": races,
            "is_simulated": s.is_simulated,
            "game_week": s.game_week,
            "game_day": game_day,
            "day_name": day_name,
            "entry_deadline_week": deadline_week,
            "entry_deadline_day": deadline_day,
            "is_v75": game_day == 6,
            "track_id": str(s.track_id) if s.track_id else None,
            "booked_driver_ids": list(booked_driver_ids),
        })
    return result


async def enter_race(db: AsyncSession, race_id, horse_id, driver_id, stable_id, shoe: str, tactics: dict):
    """Enter a horse in a race."""
    # Load race
    race_result = await db.execute(
        select(Race).options(selectinload(Race.entries)).where(Race.id == race_id)
    )
    race = race_result.scalar_one_or_none()
    if not race:
        return {"error": "Loppet finns inte"}
    if race.is_finished:
        return {"error": "Loppet är redan avklarat"}

    # Check entry deadline
    session_result = await db.execute(
        select(RaceSession).where(RaceSession.id == race.session_id)
    )
    session = session_result.scalar_one()
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    if gs:
        game_time = calculate_game_time(gs.real_week_start)
        if _check_entry_deadline(game_time, session):
            return {"error": "Anmälningsdeadline har passerat (1 dag före loppdagen)"}

    active_entries = [e for e in race.entries if not e.is_scratched]
    if len(active_entries) >= race.max_entries:
        return {"error": "Loppet är fullt"}

    # Check horse belongs to stable and is ready
    horse_result = await db.execute(select(Horse).where(Horse.id == horse_id, Horse.stable_id == stable_id))
    horse = horse_result.scalar_one_or_none()
    if not horse:
        return {"error": "Hästen tillhör inte ditt stall"}
    if horse.status.value != "ready":
        return {"error": f"Hästen är inte redo (status: {horse.status.value})"}

    # Check minimum start points
    if race.min_start_points > 0:
        sp = await calculate_start_points(db, horse_id)
        if sp["total"] < race.min_start_points:
            return {"error": f"Hästen har för få startpoäng ({sp['total']}/{race.min_start_points})"}

    # Check horse not already entered in this race
    existing = [e for e in race.entries if e.horse_id == horse_id and not e.is_scratched]
    if existing:
        return {"error": "Hästen är redan anmäld till detta lopp"}

    # Check driver is contracted
    contract_result = await db.execute(
        select(DriverContract).where(
            DriverContract.driver_id == driver_id,
            DriverContract.stable_id == stable_id,
            DriverContract.is_active == True,
        )
    )
    if not contract_result.scalar_one_or_none():
        return {"error": "Kusken har inget aktivt kontrakt med ditt stall"}

    # Check driver is not already booked in another race in the same session
    session_result2 = await db.execute(
        select(RaceSession)
        .options(selectinload(RaceSession.races).selectinload(Race.entries))
        .where(RaceSession.id == session.id)
    )
    session_full = session_result2.scalars().unique().first()
    if session_full:
        for other_race in session_full.races:
            for entry in other_race.entries:
                if entry.driver_id == driver_id and not entry.is_scratched and other_race.id != race_id:
                    return {"error": "Kusken kör redan i ett annat lopp i denna session"}

    # Calculate compatibility
    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    driver = driver_result.scalar_one()
    hs = _horse_to_engine_stats(horse)
    ds = _driver_to_engine_stats(driver)
    compat = calculate_compatibility(hs, ds, 0)

    # Check for a previously scratched entry for this horse+race — reactivate it
    # instead of inserting a new row (DB has a unique constraint on race_id+horse_id)
    scratched_entry = next(
        (e for e in race.entries if e.horse_id == horse_id and e.is_scratched), None
    )
    if scratched_entry:
        scratched_entry.is_scratched = False
        scratched_entry.scratch_reason = None
        scratched_entry.driver_id = driver_id
        scratched_entry.shoe = shoe
        scratched_entry.positioning = tactics.get("positioning", "second")
        scratched_entry.tempo = tactics.get("tempo", "balanced")
        scratched_entry.sprint_order = tactics.get("sprint_order", "normal_400m")
        scratched_entry.gallop_safety = tactics.get("gallop_safety", "normal")
        scratched_entry.curve_strategy = tactics.get("curve_strategy", "middle")
        scratched_entry.whip_usage = tactics.get("whip_usage", "normal")
        scratched_entry.entry_fee_paid = race.entry_fee
        scratched_entry.compatibility_score = compat
        entry = scratched_entry
    else:
        # Create new entry
        entry = RaceEntry(
            race_id=race_id, horse_id=horse_id, stable_id=stable_id,
            driver_id=driver_id,
            positioning=tactics.get("positioning", "second"),
            tempo=tactics.get("tempo", "balanced"),
            sprint_order=tactics.get("sprint_order", "normal_400m"),
            gallop_safety=tactics.get("gallop_safety", "normal"),
            curve_strategy=tactics.get("curve_strategy", "middle"),
            whip_usage=tactics.get("whip_usage", "normal"),
            shoe=shoe,
            entry_fee_paid=race.entry_fee,
            compatibility_score=compat,
        )
        db.add(entry)

    # Deduct entry fee
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    await finance_service.record_transaction(
        db, stable_id, -race.entry_fee, "entry_fee",
        f"Anmalningsavgift: {race.race_name}", game_week,
        reference_type="race", reference_id=race_id,
    )

    await db.flush()

    warnings = []
    if horse.fatigue > 50:
        warnings.append(f"Hasten har hog trotthet ({horse.fatigue}%) — risk for samre prestation")
    if horse.shoe_durability <= 1:
        warnings.append("Skor ar nastan utslitna — overvag omskoning")

    return {
        "entry_id": str(entry.id),
        "compatibility_score": compat,
        "warnings": warnings,
    }


async def simulate_race_session(db: AsyncSession, session_id):
    """Simulate all races in a session."""
    session_result = await db.execute(
        select(RaceSession)
        .options(selectinload(RaceSession.track))
        .where(RaceSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return {"error": "Session finns inte"}
    if session.is_simulated:
        return {"error": "Sessionen ar redan simulerad"}

    # Load races
    races_result = await db.execute(
        select(Race)
        .options(
            selectinload(Race.entries).selectinload(RaceEntry.horse),
            selectinload(Race.entries).selectinload(RaceEntry.driver),
        )
        .where(Race.session_id == session_id)
        .order_by(Race.race_number)
    )
    races = races_result.scalars().unique().all()

    engine = RaceEngine()
    npc_gen = NPCGenerator(random.Random(42))
    results_all = []

    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    for race in races:
        active_entries = [e for e in race.entries if not e.is_scratched]

        # Convert DB entries to engine entries
        engine_entries = []
        entry_map = {}  # engine_horse_id -> db_entry

        for e in active_entries:
            h = e.horse
            d = e.driver

            hs = _horse_to_engine_stats(h)
            ds = _driver_to_engine_stats(d)

            tactics = Tactics(
                positioning=Positioning(e.positioning.value if hasattr(e.positioning, 'value') else e.positioning),
                tempo=Tempo(e.tempo.value if hasattr(e.tempo, 'value') else e.tempo),
                sprint_order=SprintOrder(e.sprint_order.value if hasattr(e.sprint_order, 'value') else e.sprint_order),
                gallop_safety=GallopSafety(e.gallop_safety.value if hasattr(e.gallop_safety, 'value') else e.gallop_safety),
            )

            shoe_val = e.shoe.value if hasattr(e.shoe, 'value') else e.shoe
            compat = e.compatibility_score or calculate_compatibility(hs, ds, 0)

            engine_entry = EngineRaceEntry(
                horse=hs, driver=ds, tactics=tactics,
                shoe=EngineShoeType(shoe_val),
                compatibility_score=compat,
            )
            engine_entries.append(engine_entry)
            entry_map[str(h.id)] = e

        # Determine division level
        div_level = race.division_level or 6

        # Fill with NPCs
        field = npc_gen.fill_race_field(engine_entries, division_level=div_level)

        # Setup conditions
        weather_map = {
            "clear": Weather.CLEAR, "cloudy": Weather.CLOUDY,
            "rain": Weather.RAIN, "heavy_rain": Weather.HEAVY_RAIN,
            "snow": Weather.SNOW, "cold": Weather.COLD,
            "hot": Weather.HOT, "windy": Weather.WINDY,
        }
        surface_map = {
            "dirt": Surface.DIRT, "synthetic": Surface.SYNTHETIC,
            "winter": Surface.WINTER,
        }
        start_map = {
            "volt": StartMethod.VOLT, "auto": StartMethod.AUTO,
        }

        w_val = session.weather.value if hasattr(session.weather, 'value') else session.weather
        s_val = race.surface.value if hasattr(race.surface, 'value') else race.surface
        sm_val = race.start_method.value if hasattr(race.start_method, 'value') else race.start_method

        # Get track stretch length and prestige
        track_stretch = session.track.stretch_length if session.track and hasattr(session.track, 'stretch_length') and session.track.stretch_length else 200
        track_prestige = session.track.prestige if session.track and hasattr(session.track, 'prestige') else 50

        conditions = RaceConditions(
            distance=race.distance,
            start_method=start_map.get(sm_val, StartMethod.AUTO),
            surface=surface_map.get(s_val, Surface.DIRT),
            weather=weather_map.get(w_val, Weather.CLEAR),
            temperature=session.temperature,
            division_level=div_level,
            stretch_length=track_stretch,
            track_prestige=track_prestige,
        )
        conditions.prize_pool = race.prize_pool

        # Generate seed and simulate
        seed = generate_race_seed(str(race.id), session.scheduled_at.isoformat())
        sim_result = engine.simulate(str(race.id), field, conditions, seed)

        # Write results back to DB
        race.is_finished = True
        race.seed = seed & 0x7FFFFFFFFFFFFFFF  # Fit in signed int64

        # Store simulation data (events + NPC results for get_race_result)
        npc_finishers = []
        for f in sim_result.finishers:
            if f.horse_id not in entry_map and not f.horse_id.startswith("npc_"):
                continue
            if f.horse_id not in entry_map:
                npc_finishers.append({
                    "position": f.finish_position,
                    "horse_name": f.horse_name,
                    "horse_id": f.horse_id,
                    "driver_name": f.driver_name if hasattr(f, 'driver_name') else "Systemkusk",
                    "km_time": f.km_time_display,
                    "prize_money": f.prize_money,
                    "energy_at_finish": f.energy_at_finish,
                    "gallop_incidents": f.gallop_incidents,
                    "driver_rating": f.driver_rating,
                    "compatibility": f.compatibility_score if hasattr(f, 'compatibility_score') else 50,
                    "is_npc": True,
                })

        # Build snapshot data for race replay (use short keys to save space)
        snapshot_data = [
            {
                "d": snap.distance,
                "p": [
                    {
                        "id": p.horse_id,
                        "n": p.horse_name,
                        "pos": round(p.position_meters, 1),
                        "e": round(p.energy),
                        "spd": round(p.speed, 2),
                        "g": p.is_galloping,
                        "dq": p.is_disqualified,
                        "r": p.rank,
                    }
                    for p in snap.positions
                ],
            }
            for snap in sim_result.snapshots
        ] if game_week >= 1 else []  # Skip snapshots for historical backlog

        race.simulation_data = {
            "events": [
                {
                    "type": ev.event_type,
                    "horse": ev.horse_name,
                    "text": ev.text,
                    "distance": ev.distance,
                    **({"data": ev.data} if ev.data else {}),
                }
                for ev in sim_result.events
            ],
            "npc_results": npc_finishers,
            "snapshots": snapshot_data,
        }

        # Process finishers
        for f in sim_result.finishers:
            db_entry = entry_map.get(f.horse_id)
            if db_entry:
                db_entry.finish_position = f.finish_position
                db_entry.km_time_display = f.km_time_display
                db_entry.km_time_seconds = Decimal(str(f.km_time_seconds)) if f.km_time_seconds else None
                db_entry.finish_time_seconds = Decimal(str(f.finish_time_seconds)) if f.finish_time_seconds else None
                db_entry.prize_money = f.prize_money
                db_entry.energy_at_finish = f.energy_at_finish
                db_entry.gallop_incidents = f.gallop_incidents
                db_entry.driver_rating = f.driver_rating
                db_entry.top_speed = Decimal(str(f.top_speed)) if f.top_speed else None

                # Update horse career stats
                horse = db_entry.horse
                horse.total_starts += 1
                horse.total_earnings += f.prize_money
                if f.finish_position == 1:
                    horse.total_wins += 1
                elif f.finish_position == 2:
                    horse.total_seconds += 1
                elif f.finish_position == 3:
                    horse.total_thirds += 1

                if f.km_time_seconds and (horse.best_km_time is None or Decimal(str(f.km_time_seconds)) < horse.best_km_time):
                    horse.best_km_time = Decimal(str(f.km_time_seconds))
                    horse.best_km_time_display = f.km_time_display

                # Add fatigue
                horse.fatigue = min(100, horse.fatigue + 30)
                horse.energy = max(0, horse.energy - 40)

                # Apply stat progression
                from app.services.progression_service import apply_post_race_progression
                active_count = len([e for e in race.entries if not e.is_scratched])
                await apply_post_race_progression(
                    db, db_entry.horse_id, f.finish_position, active_count
                )

                # Record prize money transaction (minus driver commission)
                if f.prize_money > 0:
                    driver = db_entry.driver
                    commission_rate = float(getattr(driver, 'commission_rate', 0.10) or 0.10)
                    commission = int(f.prize_money * commission_rate)
                    net_prize = f.prize_money - commission

                    await finance_service.record_transaction(
                        db, db_entry.stable_id, net_prize, "prize_money",
                        f"Prispeng {f.finish_position}:a plats - {race.race_name} (efter {int(commission_rate*100)}% provision)",
                        game_week, reference_type="race", reference_id=race.id,
                    )
                    if commission > 0:
                        await finance_service.record_transaction(
                            db, db_entry.stable_id, -commission, "driver_commission",
                            f"Kuskprovision {driver.name}: {int(commission_rate*100)}% av {f.prize_money:,}",
                            game_week, reference_type="race", reference_id=race.id,
                        )

                # Update driver-horse history
                hist_result = await db.execute(
                    select(DriverHorseHistory).where(
                        DriverHorseHistory.driver_id == db_entry.driver_id,
                        DriverHorseHistory.horse_id == db_entry.horse_id,
                    )
                )
                hist = hist_result.scalar_one_or_none()
                if hist:
                    hist.races_together += 1
                    if f.finish_position == 1:
                        hist.wins_together += 1
                    hist.last_race_week = game_week
                else:
                    db.add(DriverHorseHistory(
                        driver_id=db_entry.driver_id, horse_id=db_entry.horse_id,
                        races_together=1,
                        wins_together=1 if f.finish_position == 1 else 0,
                        last_race_week=game_week,
                    ))

                # Create result summary
                db.add(RaceResultSummary(
                    race_id=race.id, horse_id=db_entry.horse_id,
                    stable_id=db_entry.stable_id, driver_id=db_entry.driver_id,
                    finish_position=f.finish_position,
                    km_time_display=f.km_time_display,
                    km_time_seconds=Decimal(str(f.km_time_seconds)) if f.km_time_seconds else None,
                    prize_money=f.prize_money, distance=race.distance,
                    start_method=race.start_method, race_class=race.race_class,
                    race_date=session.scheduled_at.replace(tzinfo=None) if hasattr(session.scheduled_at, 'replace') else session.scheduled_at,
                    game_week=game_week,
                ))

        # Process DQs
        for d in sim_result.disqualified:
            db_entry = entry_map.get(d.horse_id)
            if db_entry:
                db_entry.is_disqualified = True
                db_entry.disqualification_reason = d.dq_reason
                db_entry.finish_position = None
                db_entry.horse.total_starts += 1
                db_entry.horse.total_dq += 1
                db_entry.horse.fatigue = min(100, db_entry.horse.fatigue + 40)

        # Build result response
        finishers_out = []
        for f in sim_result.finishers:
            db_entry = entry_map.get(f.horse_id)
            finishers_out.append({
                "position": f.finish_position,
                "horse_name": f.horse_name,
                "horse_id": f.horse_id,
                "driver_name": f.driver_name if hasattr(f, 'driver_name') else "",
                "km_time": f.km_time_display,
                "prize_money": f.prize_money,
                "energy_at_finish": f.energy_at_finish,
                "gallop_incidents": f.gallop_incidents,
                "driver_rating": f.driver_rating,
                "compatibility": f.compatibility_score if hasattr(f, 'compatibility_score') else 50,
                "is_npc": db_entry is None,
            })

        results_all.append({
            "race_id": str(race.id),
            "race_name": race.race_name,
            "distance": race.distance,
            "start_method": sm_val,
            "track": session.track.name if session.track else "",
            "weather": w_val,
            "finishers": finishers_out,
            "disqualified": [
                {"horse": d.horse_name, "reason": d.dq_reason}
                for d in sim_result.disqualified
            ],
            "events": [
                {"type": ev.event_type, "horse": ev.horse_name, "text": ev.text}
                for ev in sim_result.events if ev.event_type != "start"
            ],
        })

    # Mark session as simulated
    session.is_simulated = True
    session.simulated_at = datetime.utcnow()

    await db.flush()
    return results_all


async def get_race_result(db: AsyncSession, race_id):
    """Get results for a finished race."""
    race_result = await db.execute(
        select(Race)
        .options(
            selectinload(Race.entries).selectinload(RaceEntry.horse),
            selectinload(Race.entries).selectinload(RaceEntry.driver),
            selectinload(Race.session).selectinload(RaceSession.track),
        )
        .where(Race.id == race_id)
    )
    race = race_result.scalar_one_or_none()
    if not race or not race.is_finished:
        return None

    finishers = []
    disqualified = []
    for e in sorted(race.entries, key=lambda x: x.finish_position or 999):
        if e.is_scratched:
            continue
        if e.is_disqualified:
            disqualified.append({
                "horse": e.horse.name, "reason": e.disqualification_reason,
            })
        elif e.finish_position is not None:
            finishers.append({
                "position": e.finish_position,
                "horse_name": e.horse.name,
                "horse_id": str(e.horse_id),
                "driver_name": e.driver.name if e.driver else "",
                "km_time": e.km_time_display or "",
                "prize_money": e.prize_money or 0,
                "energy_at_finish": e.energy_at_finish or 0,
                "gallop_incidents": e.gallop_incidents,
                "driver_rating": e.driver_rating or 5,
                "compatibility": e.compatibility_score or 50,
                "is_npc": False,
                "sector_times": e.sector_times or [],
            })

    # Merge NPC results from simulation_data
    if race.simulation_data and "npc_results" in race.simulation_data:
        for npc in race.simulation_data["npc_results"]:
            finishers.append(npc)

    # Sort all finishers by position
    finishers.sort(key=lambda x: x.get("position", 999))

    w_val = race.session.weather.value if hasattr(race.session.weather, 'value') else str(race.session.weather)
    sm_val = race.start_method.value if hasattr(race.start_method, 'value') else str(race.start_method)

    # Session info
    session = race.session
    track = session.track if session else None
    surface_val = session.surface.value if session and hasattr(session, 'surface') and session.surface and hasattr(session.surface, 'value') else ""
    temp_val = session.temperature if session and hasattr(session, 'temperature') else None
    game_week = session.game_week if session else None
    game_day = session.game_day if session and hasattr(session, 'game_day') else None
    day_name = DAY_NAMES.get(game_day, "") if game_day else ""

    return {
        "race_id": str(race.id),
        "race_name": race.race_name,
        "distance": race.distance,
        "start_method": sm_val,
        "track": track.name if track else "",
        "track_city": track.city if track and hasattr(track, 'city') else "",
        "weather": w_val,
        "surface": surface_val,
        "temperature": temp_val,
        "game_week": game_week,
        "day_name": day_name,
        "finishers": finishers,
        "disqualified": disqualified,
        "events": race.simulation_data.get("events", []) if race.simulation_data else [],
        "snapshots": race.simulation_data.get("snapshots", []) if race.simulation_data else [],
    }


async def update_entry_tactics(db: AsyncSession, entry_id, stable_id, tactics: dict):
    """Update tactics for an existing race entry."""
    result = await db.execute(
        select(RaceEntry).where(RaceEntry.id == entry_id, RaceEntry.stable_id == stable_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return {"error": "Anmälan hittades inte"}

    # Check race not already simulated
    race_result = await db.execute(select(Race).where(Race.id == entry.race_id))
    race = race_result.scalar_one_or_none()
    if race and race.is_finished:
        return {"error": "Loppet är redan avslutat"}

    TACTIC_ENUMS = {
        "positioning": TacticPositioning, "tempo": TacticTempo,
        "sprint_order": TacticSprint, "gallop_safety": TacticGallopSafety,
        "curve_strategy": TacticCurve, "whip_usage": TacticWhip,
    }

    for key, value in tactics.items():
        if key in TACTIC_ENUMS:
            try:
                setattr(entry, key, TACTIC_ENUMS[key](value))
            except ValueError:
                return {"error": f"Ogiltigt varde for {key}: {value}"}

    await db.flush()
    return {"success": True, "entry_id": str(entry.id)}


async def withdraw_entry(db: AsyncSession, entry_id, stable_id):
    """Withdraw a horse from a race. Refund entry fee (minus 20% admin fee)."""
    from app.services import finance_service
    result = await db.execute(
        select(RaceEntry).where(RaceEntry.id == entry_id, RaceEntry.stable_id == stable_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return {"error": "Anmälan hittades inte"}

    race_result = await db.execute(select(Race).where(Race.id == entry.race_id))
    race = race_result.scalar_one_or_none()
    if race and race.is_finished:
        return {"error": "Loppet är redan avslutat"}

    if entry.is_scratched:
        return {"error": "Hasten ar redan avanmald"}

    entry.is_scratched = True
    entry.scratch_reason = "Avanmald av stallägare"

    # Refund 80% of entry fee
    refund = int(entry.entry_fee_paid * 0.8)
    if refund > 0:
        await finance_service.record_transaction(
            db, stable_id, refund, "entry_fee_refund",
            f"Avanmalan aterbetalning (80%): {race.race_name if race else 'lopp'}", 1,
        )

    await db.flush()
    return {"success": True, "refund": refund}
