from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from app.db import models, schemas


def get_flight(db: Session, flight_id: int):
    return db.query(models.Flight).filter(models.Flight.id == flight_id).first()

def get_flights_with_min_max(
    db: Session,
    departure_airport_codes=None,
    arrival_airport_codes=None,
    start_date=None,
    end_date=None,
    airline_codes=None,
    limit=100,
    offset=0,
):
    q = (
        db.query(
            models.Flight,
            func.min(models.FlightPriceHistory.priceEur).label("min_price"),
            func.max(models.FlightPriceHistory.priceEur).label("max_price"),
        )
        .outerjoin(
            models.FlightPriceHistory,
            models.Flight.id == models.FlightPriceHistory.flightId,
        )
        .filter(models.Flight.isAvailable.is_(True))
    )

    if departure_airport_codes:
        q = q.filter(models.Flight.departureAirportCode.in_(departure_airport_codes))
    if arrival_airport_codes:
        q = q.filter(models.Flight.arrivalAirportCode.in_(arrival_airport_codes))
    if start_date:
        start_datetime = (
            datetime.combine(start_date, time.min)
            if isinstance(start_date, date) and not isinstance(start_date, datetime)
            else start_date
        )
        q = q.filter(models.Flight.departureDate >= start_datetime)
    if end_date:
        end_datetime = (
            datetime.combine(end_date + timedelta(days=1), time.min)
            if isinstance(end_date, date) and not isinstance(end_date, datetime)
            else end_date
        )
        q = q.filter(models.Flight.departureDate < end_datetime)
    if airline_codes:
        q = q.filter(models.Flight.airlineCode.in_(airline_codes))

    return (
        q.group_by(models.Flight.id)
        .order_by(models.Flight.departureDate, models.Flight.priceEur, models.Flight.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_flight(db: Session, flight: schemas.FlightCreate) -> models.Flight:
    db_flight: models.Flight = models.Flight(**flight.model_dump())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight


def update_flight(db: Session, flight_id: int, flight_update: schemas.FlightUpdate):
    db_flight = get_flight(db, flight_id)
    if not db_flight:
        return None
    update_data = flight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_flight, key, value)
    db.commit()
    db.refresh(db_flight)
    return db_flight


def delete_flight(db: Session, flight_id: int):
    db_flight = get_flight(db, flight_id)
    if not db_flight:
        return None
    db.delete(db_flight)
    db.commit()
    return db_flight
