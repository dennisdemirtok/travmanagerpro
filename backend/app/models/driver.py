"""TravManager — Driver Models"""
import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base, PgEnum
from app.models.enums import ContractType, DrivingStyle


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_npc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    is_real_driver: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    skill: Mapped[int] = mapped_column(Integer, default=50)
    start_skill: Mapped[int] = mapped_column(Integer, default=50)
    tactical_ability: Mapped[int] = mapped_column(Integer, default=50)
    sprint_timing: Mapped[int] = mapped_column(Integer, default=50)
    gallop_handling: Mapped[int] = mapped_column(Integer, default=50)
    experience: Mapped[int] = mapped_column(Integer, default=30)
    composure: Mapped[int] = mapped_column(Integer, default=50)

    driving_style: Mapped[DrivingStyle] = mapped_column(PgEnum(DrivingStyle, "driving_style"), default=DrivingStyle.TACTICAL)

    base_salary: Mapped[int] = mapped_column(BigInteger, default=500000)
    guest_fee: Mapped[int] = mapped_column(BigInteger, default=300000)
    popularity: Mapped[int] = mapped_column(Integer, default=50)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(4, 3), default=0.10, server_default="0.10")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    contracts = relationship("DriverContract", back_populates="driver")


class DriverContract(Base):
    __tablename__ = "driver_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id", ondelete="CASCADE"), nullable=False)
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False)
    contract_type: Mapped[ContractType] = mapped_column(PgEnum(ContractType, "contract_type"), nullable=False)
    salary_per_week: Mapped[int] = mapped_column(BigInteger, nullable=False)
    guest_fee_per_race: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    starts_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    ends_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    stable = relationship("Stable", back_populates="driver_contracts")
    driver = relationship("Driver", back_populates="contracts")


class DriverHorseHistory(Base):
    __tablename__ = "driver_horse_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    driver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id"), nullable=False)
    races_together: Mapped[int] = mapped_column(Integer, default=0)
    wins_together: Mapped[int] = mapped_column(Integer, default=0)
    last_race_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
