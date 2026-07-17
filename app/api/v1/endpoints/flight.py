from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db import schemas, models
from app.crud import flight
from app.db.session import SessionLocal
from app.services import booking_url_service


router = APIRouter(prefix="/flights", tags=["flights"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def to_flight_out(
    db_flight: models.Flight,
    min_price: float | None = None,
    max_price: float | None = None,
) -> schemas.FlightOut:
    flight_out = schemas.FlightOut.model_validate(db_flight)
    return flight_out.model_copy(
        update={
            "minPrice": min_price,
            "maxPrice": max_price,
            "bookingUrl": booking_url_service.generate_booking_url(db_flight),
        }
    )


@router.get("/", response_model=List[schemas.FlightOut])
def read_flights(
    db: Session = Depends(get_db),
    departureAirportCodes: Optional[List[str]] = Query(None),
    arrivalAirportCodes: Optional[List[str]] = Query(None),
    startDate: date = Query(default_factory=date.today),
    endDate: Optional[date] = Query(None),
    airlineCodes: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    db_flights = flight.get_flights_with_min_max(
        db,
        departure_airport_codes=departureAirportCodes,
        arrival_airport_codes=arrivalAirportCodes,
        start_date=startDate,
        end_date=endDate,
        airline_codes=airlineCodes,
        limit=limit,
        offset=offset,
    )

    return [
        to_flight_out(db_flight, min_price, max_price)
        for db_flight, min_price, max_price in db_flights
    ]


@router.get("/{flight_id}", response_model=schemas.FlightOut)
def read_flight(flight_id: int, db: Session = Depends(get_db)):
    db_flight = flight.get_flight(db, flight_id)
    if not db_flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return to_flight_out(db_flight)
