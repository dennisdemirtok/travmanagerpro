"""TravManager — Horse Hidden Properties Model"""
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class HorseHiddenProperties(Base):
    __tablename__ = "horse_hidden_properties"

    horse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Equipment preferences (-30 to +30, 0 = neutral)
    barefoot_affinity: Mapped[int] = mapped_column(Integer, default=0)
    american_sulky_affinity: Mapped[int] = mapped_column(Integer, default=0)
    racing_sulky_affinity: Mapped[int] = mapped_column(Integer, default=0)

    # Track preferences (-20 to +20)
    tight_curve_ability: Mapped[int] = mapped_column(Integer, default=0)
    long_homestretch_affinity: Mapped[int] = mapped_column(Integer, default=0)
    heavy_track_affinity: Mapped[int] = mapped_column(Integer, default=0)

    # Mental hidden
    confidence_sensitivity: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)
    crowd_response: Mapped[int] = mapped_column(Integer, default=0)
    recovery_rate: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)
    start_frequency_preference: Mapped[str] = mapped_column(String(20), default="normal")  # frequent/normal/sparse
    peak_age: Mapped[int] = mapped_column(Integer, default=6)
    late_bloomer: Mapped[bool] = mapped_column(Boolean, default=False)

    # Physical hidden
    natural_speed_ceiling: Mapped[int] = mapped_column(Integer, default=0)  # -5 to +15
    hidden_sprint_gear: Mapped[bool] = mapped_column(Boolean, default=False)  # 10% of horses
    wind_sensitivity: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=1.0)  # 0.5-1.5
    temperature_optimum: Mapped[int] = mapped_column(Integer, default=12)  # °C
    temperature_tolerance: Mapped[int] = mapped_column(Integer, default=15)  # degrees comfort zone

    horse = relationship("Horse", backref="hidden_properties_rel")
