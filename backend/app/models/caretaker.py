"""TravManager — Caretaker (Skötare) Models"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import CaretakerSpecialty, CaretakerPersonality


class Caretaker(Base):
    __tablename__ = "caretakers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_npc: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    skill: Mapped[int] = mapped_column(Integer, default=50)
    primary_specialty: Mapped[CaretakerSpecialty] = mapped_column(PgEnum(CaretakerSpecialty, "caretaker_specialty"), nullable=False)
    secondary_specialty: Mapped[CaretakerSpecialty | None] = mapped_column(PgEnum(CaretakerSpecialty, "caretaker_specialty"), nullable=True)
    personality: Mapped[CaretakerPersonality] = mapped_column(PgEnum(CaretakerPersonality, "caretaker_personality"), nullable=False)
    salary_demand: Mapped[int] = mapped_column(BigInteger, default=200_000)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    assignments = relationship("CaretakerAssignment", back_populates="caretaker")


class CaretakerAssignment(Base):
    __tablename__ = "caretaker_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    caretaker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("caretakers.id", ondelete="CASCADE"), nullable=False)
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    salary_per_week: Mapped[int] = mapped_column(BigInteger, nullable=False)
    starts_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    caretaker = relationship("Caretaker", back_populates="assignments")
    horse = relationship("Horse")
    stable = relationship("Stable")

    __table_args__ = (
        Index("idx_caretaker_active_horse", "horse_id", unique=True, postgresql_where="is_active = true"),
    )


class CaretakerScoutReport(Base):
    __tablename__ = "caretaker_scout_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    caretaker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("caretakers.id", ondelete="CASCADE"), nullable=False)
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    compatibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    compatibility_label: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_boost: Mapped[int] = mapped_column(Integer, default=0)
    secondary_boost: Mapped[int] = mapped_column(Integer, default=0)
    scouted_at: Mapped[datetime] = mapped_column(server_default=func.now())
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)

    caretaker = relationship("Caretaker")
    horse = relationship("Horse")

    __table_args__ = (
        UniqueConstraint("caretaker_id", "horse_id", name="uq_caretaker_horse_scout"),
    )
