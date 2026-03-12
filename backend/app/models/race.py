"""TravManager — Race Models"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import (
    RaceClass, RaceStartMethod, ShoeType, SurfaceType, WeatherType,
    TacticPositioning, TacticTempo, TacticSprint, TacticGallopSafety,
    TacticCurve, TacticWhip,
)


class RaceTrack(Base):
    __tablename__ = "race_tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(50), default="Sweden")
    surface: Mapped[SurfaceType] = mapped_column(PgEnum(SurfaceType, "surface_type"), default=SurfaceType.DIRT)
    track_direction: Mapped[str] = mapped_column(String(10), default="left")
    available_distances = mapped_column(ARRAY(Integer), default=[1640, 2140, 2640])
    has_auto_start: Mapped[bool] = mapped_column(Boolean, default=True)
    prestige: Mapped[int] = mapped_column(Integer, default=50)
    region: Mapped[str | None] = mapped_column(String(20), nullable=True)
    stretch_length: Mapped[int] = mapped_column(Integer, default=200)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)


class RaceSession(Base):
    __tablename__ = "race_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    scheduled_at: Mapped[datetime] = mapped_column(nullable=False)
    track_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("race_tracks.id"), nullable=False)
    session_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    game_day: Mapped[int] = mapped_column(Integer, default=1)
    weather: Mapped[WeatherType] = mapped_column(PgEnum(WeatherType, "weather_type"), default=WeatherType.CLEAR)
    temperature: Mapped[int] = mapped_column(Integer, default=12)
    wind_speed: Mapped[int] = mapped_column(Integer, default=5)
    start_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    simulated_at: Mapped[datetime | None] = mapped_column(nullable=True)

    track = relationship("RaceTrack")
    races = relationship("Race", back_populates="session")


class Race(Base):
    __tablename__ = "races"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("race_sessions.id"), nullable=False)
    race_number: Mapped[int] = mapped_column(Integer, nullable=False)
    race_name: Mapped[str] = mapped_column(String(200), nullable=False)
    race_class: Mapped[RaceClass] = mapped_column(PgEnum(RaceClass, "race_class"), nullable=False)
    division_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    start_method: Mapped[RaceStartMethod] = mapped_column(PgEnum(RaceStartMethod, "race_start_method"), nullable=False)
    surface: Mapped[SurfaceType] = mapped_column(PgEnum(SurfaceType, "surface_type"), default=SurfaceType.DIRT)
    prize_pool: Mapped[int] = mapped_column(BigInteger, nullable=False)
    entry_fee: Mapped[int] = mapped_column(BigInteger, default=100000)
    min_entries: Mapped[int] = mapped_column(Integer, default=6)
    max_entries: Mapped[int] = mapped_column(Integer, default=12)
    handicap_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_start_points: Mapped[int] = mapped_column(Integer, default=0)

    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)
    seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    simulation_data = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session = relationship("RaceSession", back_populates="races")
    entries = relationship("RaceEntry", back_populates="race")


class RaceEntry(Base):
    __tablename__ = "race_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    race_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("races.id", ondelete="CASCADE"), nullable=False)
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)

    # Tactics
    positioning: Mapped[TacticPositioning] = mapped_column(PgEnum(TacticPositioning, "tactic_positioning"), default=TacticPositioning.SECOND)
    tempo: Mapped[TacticTempo] = mapped_column(PgEnum(TacticTempo, "tactic_tempo"), default=TacticTempo.BALANCED)
    sprint_order: Mapped[TacticSprint] = mapped_column(PgEnum(TacticSprint, "tactic_sprint"), default=TacticSprint.NORMAL_400M)
    gallop_safety: Mapped[TacticGallopSafety] = mapped_column(PgEnum(TacticGallopSafety, "tactic_gallop_safety"), default=TacticGallopSafety.NORMAL)
    curve_strategy: Mapped[TacticCurve] = mapped_column(PgEnum(TacticCurve, "tactic_curve"), default=TacticCurve.MIDDLE)
    whip_usage: Mapped[TacticWhip] = mapped_column(PgEnum(TacticWhip, "tactic_whip"), default=TacticWhip.NORMAL)

    # Equipment
    shoe: Mapped[ShoeType] = mapped_column(PgEnum(ShoeType, "shoe_type"), default=ShoeType.NORMAL_STEEL)

    # Post position
    post_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handicap_meters: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    finish_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_disqualified: Mapped[bool] = mapped_column(Boolean, default=False)
    disqualification_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    finish_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    km_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    km_time_display: Mapped[str | None] = mapped_column(String(10), nullable=True)
    prize_money: Mapped[int] = mapped_column(BigInteger, default=0)

    # Detailed stats
    energy_at_finish: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_speed: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    gallop_incidents: Mapped[int] = mapped_column(Integer, default=0)
    driver_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compatibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sector_times = mapped_column(JSONB, nullable=True)

    # Entry meta
    entry_fee_paid: Mapped[int] = mapped_column(BigInteger, default=0)
    is_scratched: Mapped[bool] = mapped_column(Boolean, default=False)
    scratch_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    entered_at: Mapped[datetime] = mapped_column(server_default=func.now())

    race = relationship("Race", back_populates="entries")
    horse = relationship("Horse")
    driver = relationship("Driver")
    stable = relationship("Stable")


class RaceResultSummary(Base):
    __tablename__ = "race_results_summary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    race_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("races.id"), nullable=False)
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)

    finish_position: Mapped[int] = mapped_column(Integer, nullable=False)
    km_time_display: Mapped[str | None] = mapped_column(String(10), nullable=True)
    km_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    prize_money: Mapped[int] = mapped_column(BigInteger, default=0)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    start_method: Mapped[RaceStartMethod] = mapped_column(PgEnum(RaceStartMethod, "race_start_method"), nullable=False)
    race_class: Mapped[RaceClass] = mapped_column(PgEnum(RaceClass, "race_class"), nullable=False)
    race_date: Mapped[datetime] = mapped_column(nullable=False)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
