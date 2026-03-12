"""TravManager — Game State Models"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import SeasonPeriod


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    season_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    start_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    end_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    current_period: Mapped[SeasonPeriod] = mapped_column(PgEnum(SeasonPeriod, "season_period"), default=SeasonPeriod.PRE_SEASON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Division(Base):
    __tablename__ = "divisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    group_number: Mapped[int] = mapped_column(Integer, default=1)
    season_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    max_stables: Mapped[int] = mapped_column(Integer, default=12)


class DivisionStanding(Base):
    __tablename__ = "division_standings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    division_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("divisions.id"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    races_run: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    prize_money_earned: Mapped[int] = mapped_column(BigInteger, default=0)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)


class GameState(Base):
    __tablename__ = "game_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    current_game_week: Mapped[int] = mapped_column(Integer, default=1)
    current_game_day: Mapped[int] = mapped_column(Integer, default=1)
    current_season_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True)
    real_week_start: Mapped[datetime] = mapped_column(server_default=func.now())
    next_race_session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("race_sessions.id"), nullable=True)
    next_race_at: Mapped[datetime | None] = mapped_column(nullable=True)
    total_active_players: Mapped[int] = mapped_column(Integer, default=0)
    npc_scaling_factor: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0.70)
    last_recovery_game_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_weekly_processing_week: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DailyHorseLog(Base):
    __tablename__ = "daily_horse_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id"), nullable=False)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    game_day: Mapped[int] = mapped_column(Integer, nullable=False)
    condition: Mapped[int] = mapped_column(Integer, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, nullable=False)
    health: Mapped[int] = mapped_column(Integer, nullable=False)
    fatigue: Mapped[int] = mapped_column(Integer, nullable=False)
    mood: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 1), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CompatibilityCache(Base):
    __tablename__ = "compatibility_cache"

    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), primary_key=True)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), primary_key=True)
    base_score: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_bonus: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_calculated: Mapped[datetime] = mapped_column(server_default=func.now())
