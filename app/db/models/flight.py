from sqlalchemy import (
    Column,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from app.db.base import Base


class Flight(Base):
    __tablename__ = "flights"
    __table_args__ = (
        UniqueConstraint(
            "departureDate",
            "departureAirportCode",
            "arrivalAirportCode",
            "airlineCode",
            name="uq_flights_identity",
        ),
        Index(
            "ix_flights_search",
            "departureAirportCode",
            "arrivalAirportCode",
            "airlineCode",
            "departureDate",
        ),
        CheckConstraint(
            '"consecutiveMisses" >= 0',
            name="ck_flights_consecutive_misses_nonnegative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    departureDate = Column(DateTime, index=True, nullable=False)
    price = Column(Float, nullable=False)
    priceEur = Column(Float, nullable=False)
    departureAirportCode = Column(
        String(10), ForeignKey("airports.code"), nullable=False
    )
    arrivalAirportCode = Column(String(10), ForeignKey("airports.code"), nullable=False)
    airlineCode = Column(String(10), ForeignKey("airlines.code"), nullable=False)
    isAvailable = Column(Boolean, nullable=False, default=True, server_default="true")
    consecutiveMisses = Column(Integer, nullable=False, default=0, server_default="0")
