"""TravManager — Horse Market / Auction Models"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AuctionListing(Base):
    __tablename__ = "auction_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    horse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("horses.id", ondelete="CASCADE"), nullable=False)
    seller_stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    starting_price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    buyout_price: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    current_bid: Mapped[int] = mapped_column(BigInteger, default=0)
    current_bidder_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    listed_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    horse = relationship("Horse")
    seller_stable = relationship("Stable", foreign_keys=[seller_stable_id])
    current_bidder = relationship("Stable", foreign_keys=[current_bidder_id])


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    listing_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auction_listings.id", ondelete="CASCADE"), nullable=False)
    bidder_stable_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("stables.id"), nullable=False)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    game_week: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    listing = relationship("AuctionListing")
    bidder_stable = relationship("Stable")
