"""TravManager — Horse & Bloodline Models"""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import (
    HorseGender, HorseStatus, PersonalityType, ShoeType,
    SurfaceType, TrainingIntensity, TrainingProgram,
)


class Bloodline(Base):
    __tablename__ = "bloodlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    origin_country: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Horse(Base):
    __tablename__ = "horses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[HorseGender] = mapped_column(PgEnum(HorseGender, "horse_gender"), nullable=False)
    birth_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    age_game_weeks: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[HorseStatus] = mapped_column(PgEnum(HorseStatus, "horse_status"), default=HorseStatus.READY, server_default="ready")
    is_npc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Core stats (1-100)
    speed: Mapped[int] = mapped_column(Integer, default=40)
    endurance: Mapped[int] = mapped_column(Integer, default=40)
    mentality: Mapped[int] = mapped_column(Integer, default=40)
    start_ability: Mapped[int] = mapped_column(Integer, default=40)
    sprint_strength: Mapped[int] = mapped_column(Integer, default=40)
    balance: Mapped[int] = mapped_column(Integer, default=40)
    strength: Mapped[int] = mapped_column(Integer, default=40)

    # Genetic potential
    potential_speed: Mapped[int] = mapped_column(Integer, default=70)
    potential_endurance: Mapped[int] = mapped_column(Integer, default=70)
    potential_mentality: Mapped[int] = mapped_column(Integer, default=70)
    potential_start: Mapped[int] = mapped_column(Integer, default=70)
    potential_sprint: Mapped[int] = mapped_column(Integer, default=70)
    potential_balance: Mapped[int] = mapped_column(Integer, default=70)
    potential_strength: Mapped[int] = mapped_column(Integer, default=70)

    # Physical status
    condition: Mapped[int] = mapped_column(Integer, default=80)
    energy: Mapped[int] = mapped_column(Integer, default=100)
    health: Mapped[int] = mapped_column(Integer, default=90)
    current_weight: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=470.0)
    ideal_weight: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=470.0)
    form: Mapped[int] = mapped_column(Integer, default=50)
    fatigue: Mapped[int] = mapped_column(Integer, default=0)
    mood: Mapped[int] = mapped_column(Integer, default=70)
    confidence: Mapped[int] = mapped_column(Integer, default=50, server_default="50")

    # Hidden/genetic traits
    gallop_tendency: Mapped[int] = mapped_column(Integer, default=15)
    track_preference: Mapped[str | None] = mapped_column(String(10), nullable=True)
    surface_preference: Mapped[SurfaceType | None] = mapped_column(PgEnum(SurfaceType, "surface_type"), nullable=True)
    weather_sensitivity: Mapped[int] = mapped_column(Integer, default=50)
    distance_optimum: Mapped[int] = mapped_column(Integer, default=2140)
    maturation_speed: Mapped[int] = mapped_column(Integer, default=50)
    racing_instinct: Mapped[int] = mapped_column(Integer, default=50)
    days_since_last_race: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    races_last_30_days: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    transport_tolerance: Mapped[int] = mapped_column(Integer, default=70)

    # Personality
    personality_primary: Mapped[PersonalityType] = mapped_column(PgEnum(PersonalityType, "personality_type"), default=PersonalityType.CALM)
    personality_secondary: Mapped[PersonalityType] = mapped_column(PgEnum(PersonalityType, "personality_type"), default=PersonalityType.RESPONSIVE)
    personality_revealed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Pedigree
    sire_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="SET NULL"), nullable=True)
    dam_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="SET NULL"), nullable=True)
    bloodline_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("bloodlines.id"), nullable=True)
    generation: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    # Training
    current_training: Mapped[TrainingProgram | None] = mapped_column(PgEnum(TrainingProgram, "training_program"), default=TrainingProgram.REST)
    training_intensity: Mapped[TrainingIntensity | None] = mapped_column(PgEnum(TrainingIntensity, "training_intensity"), default=TrainingIntensity.NORMAL)

    # Training lock (total game days when training unlocks)
    training_locked_until: Mapped[int | None] = mapped_column(Integer, nullable=True)
    training_last_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Shoeing
    current_shoe: Mapped[ShoeType] = mapped_column(PgEnum(ShoeType, "shoe_type"), default=ShoeType.NORMAL_STEEL)
    shoe_durability: Mapped[int] = mapped_column(Integer, default=6)
    last_shoeing_week: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Career stats
    total_starts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_wins: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_thirds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_dq: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_earnings: Mapped[int] = mapped_column(default=0, server_default="0", type_=__import__("sqlalchemy").BigInteger)
    best_km_time: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    best_km_time_display: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Special traits & age
    special_traits: Mapped[dict | None] = mapped_column(JSONB, default=list, server_default="'[]'")
    traits_revealed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    age_years: Mapped[int] = mapped_column(Integer, default=3, server_default="3")

    # Form history (list of recent form values for sparklines)
    form_history: Mapped[list] = mapped_column(JSONB, default=list, server_default="'[]'")

    # Injury
    injury_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    injury_recovery_weeks: Mapped[int | None] = mapped_column(Integer, default=0)

    # Breeding
    is_breeding_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    stud_fee: Mapped[int | None] = mapped_column(__import__("sqlalchemy").BigInteger, nullable=True)
    pregnancy_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_foal_week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relationships
    stable = relationship("Stable", back_populates="horses")
    bloodline = relationship("Bloodline")
    sire = relationship("Horse", remote_side="Horse.id", foreign_keys=[sire_id])
    dam = relationship("Horse", remote_side="Horse.id", foreign_keys=[dam_id])
    feed_plans = relationship("FeedPlan", back_populates="horse")
