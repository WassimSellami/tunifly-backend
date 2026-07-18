from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    flightId = Column(Integer, ForeignKey("flights.id"), index=True, nullable=False)
    targetPrice = Column(Float, nullable=False)
    isActive = Column(Boolean, default=True, nullable=False)
    userId = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User")
