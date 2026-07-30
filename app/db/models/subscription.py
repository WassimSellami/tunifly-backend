from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "userId", "flightId", name="uq_subscriptions_user_id_flight_id"
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    flightId = Column(Integer, ForeignKey("flights.id"), index=True, nullable=False)
    targetPrice = Column(Float, nullable=False)
    isActive = Column(Boolean, default=True, nullable=False)
    userId = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User")
