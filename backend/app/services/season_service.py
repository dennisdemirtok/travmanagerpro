"""TravManager — Säsongsloopen (sprint 6, DEL A3)

Fyra mål per säsong, anpassade till stallets nivå. Belöning betalas ut
direkt när målet nås. Efter tio veckor sammanfattas säsongen.
"""
import logging

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stable import Stable
from app.models.horse import Horse
from app.models.race import RaceResultSummary
from app.models.season_goal import SeasonGoal
from app.models.game_state import GameState, Season
from app.models.observation import HorseObservation
from app.services import finance_service, event_service

logger = logging.getLogger(__name__)


# ── Måldefinitioner per nivå ────────────────────────────────────────
# (nyckel, titel, beskrivning, mål, pengar i öre, rykte, belöningstext)
BEGINNER_GOALS = [
    ("wins", "Vinn {target} lopp", "Ta hem segern i {target} lopp under säsongen.",
     2, 2_500_000, 0, "25 000 kr"),
    ("earnings", "Tjäna {target_kr}", "Nå {target_kr} i intjänade prispengar.",
     50_000, 0, 5, "+5 rykte"),
    ("starts", "Genomför {target} starter", "Starta i {target} lopp under säsongen.",
     8, 1_000_000, 0, "10 000 kr"),
    ("discoveries", "Upptäck {target} dolda egenskaper",
     "Samla {target} observationer i hästdagboken.",
     3, 600_000, 0, "3 gratis snabbjobb (6 000 kr)"),
]

INTERMEDIATE_GOALS = [
    ("wins", "Vinn {target} lopp", "Ta hem segern i {target} lopp under säsongen.",
     4, 5_000_000, 2, "50 000 kr"),
    ("earnings", "Tjäna {target_kr}", "Nå {target_kr} i intjänade prispengar.",
     200_000, 0, 8, "+8 rykte"),
    ("podiums", "Ta {target} pallplatser", "Sluta topp tre i {target} lopp.",
     10, 3_000_000, 0, "30 000 kr"),
    ("v75", "Starta i {target} V75-lopp", "Kvala in och starta i {target} V75-lopp.",
     3, 4_000_000, 3, "40 000 kr"),
]

ADVANCED_GOALS = [
    ("wins", "Vinn {target} lopp", "Ta hem segern i {target} lopp under säsongen.",
     8, 12_000_000, 5, "120 000 kr"),
    ("earnings", "Tjäna {target_kr}", "Nå {target_kr} i intjänade prispengar.",
     600_000, 0, 12, "+12 rykte"),
    ("silver", "Nå Silverdivisionen", "Starta i minst {target} silverlopp.",
     3, 8_000_000, 5, "80 000 kr"),
    ("breeding", "Föd upp {target} föl", "Få {target} föl fött under säsongen.",
     1, 6_000_000, 4, "60 000 kr"),
]


def _tier_for(stable: Stable) -> tuple[str, list]:
    rep = stable.reputation or 0
    earned = stable.total_earnings or 0
    if rep >= 45 or earned >= 60_000_000:
        return "advanced", ADVANCED_GOALS
    if rep >= 22 or earned >= 15_000_000:
        return "intermediate", INTERMEDIATE_GOALS
    return "beginner", BEGINNER_GOALS


def _kr(ore: int) -> str:
    return finance_service.format_kr(ore)


async def ensure_season_goals(db: AsyncSession, stable_id, season_number: int) -> list:
    """Skapa säsongens fyra mål om de inte finns. Idempotent."""
    stable = await db.get(Stable, stable_id)
    if not stable:
        return []

    existing = (await db.execute(
        select(SeasonGoal).where(
            SeasonGoal.stable_id == stable_id,
            SeasonGoal.season_number == season_number,
        )
    )).scalars().all()
    if existing:
        return existing

    tier, defs = _tier_for(stable)
    created = []
    for key, title, desc, target, money, rep, reward_text in defs:
        target_kr = _kr(target * 100) if key == "earnings" else ""
        goal = SeasonGoal(
            stable_id=stable_id,
            season_number=season_number,
            goal_key=key,
            title=title.format(target=target, target_kr=target_kr),
            description=desc.format(target=target, target_kr=target_kr),
            target=target,
            reward_money=money,
            reward_reputation=rep,
            reward_text=reward_text,
        )
        db.add(goal)
        created.append(goal)

    stable.season_goals_generated = season_number
    await db.flush()
    logger.info(f"Skapade {len(created)} säsongsmål ({tier}) för stall {stable_id}")
    return created


async def _measure(db: AsyncSession, stable_id, key: str, season) -> int:
    """Mät nuvarande progress för ett mål inom säsongens veckospann."""
    lo, hi = season.start_game_week, season.end_game_week

    if key in ("wins", "starts", "podiums", "v75", "silver"):
        rows = (await db.execute(
            select(RaceResultSummary).where(
                RaceResultSummary.stable_id == stable_id,
                RaceResultSummary.game_week >= lo,
                RaceResultSummary.game_week <= hi,
            )
        )).scalars().all()
        if key == "wins":
            return sum(1 for r in rows if r.finish_position == 1)
        if key == "starts":
            return len(rows)
        if key == "podiums":
            return sum(1 for r in rows if r.finish_position and r.finish_position <= 3)
        if key == "v75":
            return sum(1 for r in rows
                       if (r.race_class.value if hasattr(r.race_class, "value") else str(r.race_class)) == "v75")
        if key == "silver":
            return sum(1 for r in rows
                       if (r.race_class.value if hasattr(r.race_class, "value") else str(r.race_class)) == "silver")

    if key == "earnings":
        total = (await db.execute(
            select(sa_func.coalesce(sa_func.sum(RaceResultSummary.prize_money), 0)).where(
                RaceResultSummary.stable_id == stable_id,
                RaceResultSummary.game_week >= lo,
                RaceResultSummary.game_week <= hi,
            )
        )).scalar() or 0
        return int(total // 100)  # målet anges i kronor

    if key == "discoveries":
        return (await db.execute(
            select(sa_func.count(HorseObservation.id)).where(
                HorseObservation.stable_id == stable_id,
                HorseObservation.game_week >= lo,
                HorseObservation.game_week <= hi,
            )
        )).scalar() or 0

    if key == "breeding":
        return (await db.execute(
            select(sa_func.count(Horse.id)).where(
                Horse.breeder_stable_id == stable_id,
                Horse.birth_game_week >= lo,
                Horse.birth_game_week <= hi,
            )
        )).scalar() or 0

    return 0


async def refresh_goals(db: AsyncSession, stable_id, game_week: int) -> list[dict]:
    """Uppdatera progress och betala ut belöningar för uppnådda mål."""
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()
    if not gs or not gs.current_season_id:
        return []
    season = await db.get(Season, gs.current_season_id)
    if not season:
        return []

    await ensure_season_goals(db, stable_id, season.season_number)

    goals = (await db.execute(
        select(SeasonGoal).where(
            SeasonGoal.stable_id == stable_id,
            SeasonGoal.season_number == season.season_number,
        ).order_by(SeasonGoal.created_at)
    )).scalars().all()

    out = []
    for goal in goals:
        if not goal.is_completed:
            goal.progress = await _measure(db, stable_id, goal.goal_key, season)
            if goal.progress >= goal.target:
                goal.is_completed = True
                goal.completed_week = game_week
                await _pay_reward(db, stable_id, goal, game_week)

        out.append({
            "id": str(goal.id),
            "key": goal.goal_key,
            "title": goal.title,
            "description": goal.description,
            "target": goal.target,
            "progress": min(goal.progress, goal.target),
            "raw_progress": goal.progress,
            "percent": min(100, round(goal.progress / max(1, goal.target) * 100)),
            "reward_text": goal.reward_text,
            "is_completed": goal.is_completed,
            "completed_week": goal.completed_week,
        })

    await db.flush()
    return out


async def _pay_reward(db: AsyncSession, stable_id, goal: SeasonGoal, game_week: int):
    stable = await db.get(Stable, stable_id)
    if goal.reward_money:
        await finance_service.record_transaction(
            db, stable_id, goal.reward_money, "season_goal",
            f"Säsongsmål uppnått: {goal.title}", game_week,
        )
    if goal.reward_reputation and stable:
        stable.reputation = (stable.reputation or 0) + goal.reward_reputation
    await event_service.create_event(
        db, stable_id, "goal", f"Säsongsmål klart: {goal.title}",
        f"Du nådde målet och fick {goal.reward_text}.", game_week,
    )
    logger.info(f"Säsongsmål utbetalt: {goal.goal_key} för stall {stable_id}")


# ══════════════════════════════════════════════════════════════════
# SÄSONGSSAMMANFATTNING — "Din säsong"
# ══════════════════════════════════════════════════════════════════

async def build_season_summary(db: AsyncSession, stable_id, season_number: int = None) -> dict:
    """Sammanfatta en säsong: starter, segrar, intjänat, bästa lopp,
    största skräll, formkurva och nya upptäckter."""
    gs = (await db.execute(select(GameState).where(GameState.id == 1))).scalar_one_or_none()

    if season_number is None:
        season = await db.get(Season, gs.current_season_id) if gs and gs.current_season_id else None
    else:
        season = (await db.execute(
            select(Season).where(Season.season_number == season_number)
        )).scalar_one_or_none()
    if not season:
        return {"error": "Ingen säsong hittades"}

    lo, hi = season.start_game_week, season.end_game_week

    rows = (await db.execute(
        select(RaceResultSummary).where(
            RaceResultSummary.stable_id == stable_id,
            RaceResultSummary.game_week >= lo,
            RaceResultSummary.game_week <= hi,
        ).order_by(RaceResultSummary.game_week)
    )).scalars().all()

    starts = len(rows)
    wins = sum(1 for r in rows if r.finish_position == 1)
    seconds = sum(1 for r in rows if r.finish_position == 2)
    thirds = sum(1 for r in rows if r.finish_position == 3)
    earned = sum(r.prize_money or 0 for r in rows)

    best = max(rows, key=lambda r: r.prize_money or 0, default=None)

    # Största skräll: seger i det lopp med högst prispott
    upsets = [r for r in rows if r.finish_position == 1]
    biggest_upset = max(upsets, key=lambda r: r.prize_money or 0, default=None)

    # Formkurva: snittform per vecka ur hästarnas formhistorik
    horses = (await db.execute(
        select(Horse).where(Horse.stable_id == stable_id)
    )).scalars().all()
    form_curve = []
    if horses:
        histories = [h.form_history or [] for h in horses]
        max_len = max((len(h) for h in histories), default=0)
        for i in range(max_len):
            vals = [h[i] for h in histories if len(h) > i and isinstance(h[i], (int, float))]
            if vals:
                form_curve.append(round(sum(vals) / len(vals)))

    discoveries = (await db.execute(
        select(sa_func.count(HorseObservation.id)).where(
            HorseObservation.stable_id == stable_id,
            HorseObservation.game_week >= lo,
            HorseObservation.game_week <= hi,
        )
    )).scalar() or 0

    goals = (await db.execute(
        select(SeasonGoal).where(
            SeasonGoal.stable_id == stable_id,
            SeasonGoal.season_number == season.season_number,
        )
    )).scalars().all()

    stable = await db.get(Stable, stable_id)

    return {
        "season_number": season.season_number,
        "weeks": [lo, hi],
        "is_finished": bool(gs and gs.current_game_week > hi),
        "starts": starts,
        "wins": wins,
        "seconds": seconds,
        "thirds": thirds,
        "win_rate": round(wins / starts * 100) if starts else 0,
        "podium_rate": round((wins + seconds + thirds) / starts * 100) if starts else 0,
        "earned": earned,
        "discoveries": discoveries,
        "reputation": stable.reputation if stable else 0,
        "balance": stable.balance if stable else 0,
        "best_race": {
            "race_id": str(best.race_id),
            "position": best.finish_position,
            "prize": best.prize_money,
            "km_time": best.km_time_display,
            "game_week": best.game_week,
        } if best else None,
        "biggest_win": {
            "race_id": str(biggest_upset.race_id),
            "prize": biggest_upset.prize_money,
            "game_week": biggest_upset.game_week,
        } if biggest_upset else None,
        "form_curve": form_curve[-20:],
        "goals": [
            {
                "title": g.title,
                "is_completed": g.is_completed,
                "progress": min(g.progress, g.target),
                "target": g.target,
                "reward_text": g.reward_text,
            }
            for g in goals
        ],
        "goals_completed": sum(1 for g in goals if g.is_completed),
        "goals_total": len(goals),
    }


async def apply_division_movement(db: AsyncSession, season_number: int) -> dict:
    """Upp- och nedflyttning efter säsongen, baserat på säsongspoäng."""
    stables = (await db.execute(
        select(Stable).where(Stable.is_npc == False)
    )).scalars().all()
    if not stables:
        return {"promoted": 0, "relegated": 0}

    promoted = relegated = 0
    for stable in stables:
        points = stable.season_points or 0
        rank = stable.division_rank or 6

        if points >= 120 and rank > 1:
            stable.division_rank = rank - 1
            promoted += 1
            await event_service.create_event(
                db, stable.id, "achievement", "Uppflyttad!",
                f"Med {points} säsongspoäng flyttas du upp till division {rank - 1}.",
                season_number,
            )
        elif points < 25 and rank < 6:
            stable.division_rank = rank + 1
            relegated += 1
            await event_service.create_event(
                db, stable.id, "system", "Nedflyttad",
                f"Med bara {points} säsongspoäng flyttas du ner till division {rank + 1}. "
                f"Nästa säsong blir en nystart.",
                season_number,
            )
        stable.season_points = 0

    await db.flush()
    return {"promoted": promoted, "relegated": relegated}
