"""TravManager — Race Ticker Service

Automatically simulates races when their scheduled real time has passed,
and generates upcoming race schedules.
Handles season transitions (horse aging every SEASON_LENGTH_WEEKS).
"""
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game_state import GameState, Season
from app.models.race import RaceSession
from app.services.game_init_service import (
    calculate_game_time, generate_races_for_week, SEASON_LENGTH_WEEKS,
)
from app.services.race_service import simulate_race_session, calculate_start_points
from app.services.npc_entry_service import auto_enter_npc_horses
from app.services.progression_service import apply_recovery, apply_weekly_form_changes
from app.services import finance_service
from app.services import sponsor_service
from app.services import market_service
from app.services import training_service
from app.services import breeding_service

logger = logging.getLogger(__name__)


async def run_qualification_for_session(db: AsyncSession, session_id):
    """For each race in a session, if entries > max_entries,
    keep only the top entries by start points. Scratch the rest with full refund.
    """
    from app.models.race import Race, RaceEntry
    from sqlalchemy.orm import selectinload

    races_result = await db.execute(
        select(Race)
        .options(selectinload(Race.entries))
        .where(Race.session_id == session_id, Race.is_finished == False)
    )

    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    game_week = gs.current_game_week if gs else 1

    for race in races_result.scalars().all():
        active_entries = [e for e in race.entries if not e.is_scratched]

        if len(active_entries) <= race.max_entries:
            continue

        # Calculate start points for each entry
        entries_with_points = []
        for entry in active_entries:
            sp = await calculate_start_points(db, entry.horse_id)
            entries_with_points.append((entry, sp["total"]))

        # Sort by points descending
        entries_with_points.sort(key=lambda x: x[1], reverse=True)

        # Scratch overflow entries (lowest points)
        for entry, points in entries_with_points[race.max_entries:]:
            entry.is_scratched = True
            entry.scratch_reason = f"Ej kvalificerad (startpoäng: {points})"

            # Full refund for qualification scratches
            if entry.entry_fee_paid > 0:
                await finance_service.record_transaction(
                    db, entry.stable_id, entry.entry_fee_paid, "entry_fee_refund",
                    f"Ej kvalificerad - full återbetalning: {race.race_name}",
                    game_week,
                )

            logger.info(
                f"Qualification scratch: horse {entry.horse_id} from {race.race_name} "
                f"(points: {points})"
            )


async def tick_races(db: AsyncSession) -> list[dict]:
    """Check for race sessions whose scheduled game time has passed,
    run qualification and simulate them.

    Also generates next week's race schedule if needed.

    Returns list of session IDs that were simulated.
    """
    gs_result = await db.execute(select(GameState).where(GameState.id == 1))
    gs = gs_result.scalar_one_or_none()
    if not gs:
        return []

    game_time = calculate_game_time(gs.real_week_start)
    current_week = game_time["game_week"]
    current_day = game_time["game_day"]

    # Apply daily recovery if game day has advanced
    current_total_day = game_time["total_game_days"]
    if gs.last_recovery_game_day is None or current_total_day > gs.last_recovery_game_day:
        days_elapsed = current_total_day - (gs.last_recovery_game_day or 0)
        if days_elapsed > 0:
            await apply_recovery(db, min(days_elapsed, 7))
            gs.last_recovery_game_day = current_total_day
            await db.flush()

    # Weekly processing: sponsor income, expired auctions, NPC listings
    # Uses dedicated tracker to avoid race with get_game_state() which pre-updates current_game_week
    if gs.last_weekly_processing_week is None or current_week > gs.last_weekly_processing_week:
        logger.info(f"Running weekly processing for week {current_week} (last processed: {gs.last_weekly_processing_week})")

        # 1. Sponsor income
        income = await sponsor_service.collect_weekly_sponsor_income(db, current_week)
        if income > 0:
            logger.info(f"Sponsor income collected for week {current_week}: {income} öre")

        # 2. Deduct weekly stable costs (rent, feed, staff, driver salaries)
        costs = await finance_service.deduct_weekly_stable_costs(db, current_week)
        if costs > 0:
            logger.info(f"Weekly costs deducted for week {current_week}: {costs} öre")

        # 3. Apply weekly form changes (personality-driven form volatility)
        await apply_weekly_form_changes(db, current_week)

        # 4. Process completed professional training
        completed = await training_service.process_professional_training(db, current_week)
        if completed > 0:
            logger.info(f"Professional training completed: {completed} horses in week {current_week}")

        # 5. Check for breeding births
        births = await breeding_service.check_births(db, current_week)
        if births > 0:
            logger.info(f"Foals born: {births} in week {current_week}")

        # 6. Process injury recovery
        recovered = await _process_injury_recovery(db, current_week)
        if recovered > 0:
            logger.info(f"Injury recovery: {recovered} horses healed in week {current_week}")

        # 7. Season transition: age horses at end of each season
        aged = await _check_season_transition(db, current_week, gs)
        if aged > 0:
            logger.info(f"Season transition: {aged} horses aged (week {current_week})")

        # 8. Process expired auctions
        processed = await market_service.process_expired_auctions(db, current_week)
        if processed > 0:
            logger.info(f"Processed {processed} expired auctions")

        # 9. Seed new NPC listings periodically (every 2 weeks)
        if current_week % 2 == 0:
            seeded = await market_service.seed_npc_listings(db, current_week, count=2)
            if seeded > 0:
                logger.info(f"Seeded {seeded} NPC market listings")

        gs.last_weekly_processing_week = current_week
        await db.flush()

    # Update stored game week
    gs.current_game_week = current_week
    gs.current_game_day = current_day
    await db.flush()

    # Generate races for next week if not already generated
    await generate_races_for_week(db, current_week + 1)

    # Find unsimulated sessions whose scheduled real time has passed
    now = datetime.utcnow()
    sessions_result = await db.execute(
        select(RaceSession)
        .where(RaceSession.is_simulated == False)
        .order_by(RaceSession.game_week, RaceSession.game_day)
    )
    sessions = sessions_result.scalars().all()

    simulated = []
    for session in sessions:
        session_day = session.game_day if hasattr(session, 'game_day') and session.game_day else 1

        # Use scheduled_at (real datetime) if available, otherwise fallback to game day
        should_simulate = False
        if session.scheduled_at:
            sched = session.scheduled_at.replace(tzinfo=None) if session.scheduled_at.tzinfo else session.scheduled_at
            should_simulate = now >= sched
        else:
            # Fallback for legacy sessions without proper scheduled_at
            session_total = (session.game_week - 1) * 7 + session_day
            current_total = (current_week - 1) * 7 + current_day
            should_simulate = current_total >= session_total

        if should_simulate:
            logger.info(
                f"Auto-simulating session {session.id} "
                f"(week {session.game_week}, day {session_day}, "
                f"scheduled_at={session.scheduled_at})"
            )

            # Auto-enter NPC horses into races
            await auto_enter_npc_horses(db, session.id, current_week)

            # Run qualification first (trim overflowing entries)
            await run_qualification_for_session(db, session.id)

            # Simulate
            try:
                result = await simulate_race_session(db, session.id)
                simulated.append({
                    "session_id": str(session.id),
                    "game_week": session.game_week,
                    "game_day": session_day,
                })
            except Exception as e:
                logger.error(f"Failed to simulate session {session.id}: {e}")

    return simulated


async def _check_season_transition(db: AsyncSession, current_week: int, gs: GameState) -> int:
    """Check if the current season has ended and transition to a new one.
    Each season = SEASON_LENGTH_WEEKS game weeks = 1 horse year.
    Returns number of horses aged (0 if no transition).
    """
    from app.models.enums import SeasonPeriod

    if not gs.current_season_id:
        return 0

    sr = await db.execute(select(Season).where(Season.id == gs.current_season_id))
    season = sr.scalar_one_or_none()
    if not season:
        return 0

    # Check if current week exceeds the season's end week
    if current_week <= season.end_game_week:
        return 0

    # === Season transition ===
    logger.info(
        f"Season {season.season_number} ended (weeks {season.start_game_week}-{season.end_game_week}). "
        f"Current week: {current_week}"
    )

    # 1. Age all horses
    aged = await _age_horses(db)

    # 2. Mark old season as finished
    season.is_active = False
    season.current_period = SeasonPeriod.OFF_SEASON

    # 3. Create new season
    new_start = season.end_game_week + 1
    new_season = Season(
        season_number=season.season_number + 1,
        start_game_week=new_start,
        end_game_week=new_start + SEASON_LENGTH_WEEKS - 1,
        current_period=SeasonPeriod.REGULAR,
        is_active=True,
    )
    db.add(new_season)
    await db.flush()

    # 4. Update game state to point to new season
    gs.current_season_id = new_season.id
    await db.flush()

    logger.info(
        f"Season {new_season.season_number} started "
        f"(weeks {new_season.start_game_week}-{new_season.end_game_week})"
    )

    return aged


async def _age_horses(db: AsyncSession) -> int:
    """Age all non-retired horses by 1 year (called at season transition).
    Auto-retire horses aged 13+.
    1 season = SEASON_LENGTH_WEEKS game weeks = 1 horse year.
    """
    from app.models.horse import Horse
    from app.models.enums import HorseStatus

    result = await db.execute(
        select(Horse).where(Horse.status != HorseStatus.RETIRED)
    )
    horses = result.scalars().all()

    aged_count = 0
    retired_count = 0
    for horse in horses:
        horse.age_years = (horse.age_years or 0) + 1
        horse.age_game_weeks = (horse.age_game_weeks or 0) + SEASON_LENGTH_WEEKS
        aged_count += 1

        # Auto-retire very old horses (13+ years)
        if horse.age_years >= 13:
            horse.status = HorseStatus.RETIRED
            retired_count += 1
            logger.info(f"Horse retired due to age: {horse.name} (age {horse.age_years})")

    await db.flush()

    if retired_count > 0:
        logger.info(f"Auto-retired {retired_count} horses at age 13+")

    return aged_count


async def _process_injury_recovery(db: AsyncSession, current_week: int) -> int:
    """Process weekly injury recovery for all injured horses.
    Each week, injury_recovery_weeks decrements by 1.
    When it reaches 0, the horse is healed and set back to READY.
    """
    from app.models.horse import Horse
    from app.models.enums import HorseStatus
    from app.services import event_service

    result = await db.execute(
        select(Horse).where(
            Horse.status == HorseStatus.INJURED,
            Horse.injury_recovery_weeks != None,
            Horse.injury_recovery_weeks > 0,
        )
    )
    injured_horses = result.scalars().all()

    recovered_count = 0
    for horse in injured_horses:
        # "slow_healer" trait = recovery takes longer
        recovery_rate = 1
        traits = horse.special_traits or []
        if "slow_healer" in traits:
            # 30% chance recovery doesn't progress this week
            import random
            if random.random() < 0.30:
                recovery_rate = 0

        horse.injury_recovery_weeks = max(0, horse.injury_recovery_weeks - recovery_rate)

        if horse.injury_recovery_weeks <= 0:
            # Healed!
            injury_name = horse.injury_type or "skada"
            horse.injury_type = None
            horse.injury_recovery_weeks = 0
            horse.status = HorseStatus.READY

            # Notify stable
            await event_service.create_event(
                db, horse.stable_id, "injury",
                f"{horse.name} är frisk igen",
                f"{horse.name} har återhämtat sig från {injury_name} och är redo för tävling igen.",
                current_week,
            )
            recovered_count += 1
            logger.info(f"Horse recovered from injury: {horse.name} ({injury_name})")

    await db.flush()
    return recovered_count
