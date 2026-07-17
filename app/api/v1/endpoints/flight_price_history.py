from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import flight_price_history
from app.db.session import SessionLocal

router = APIRouter(prefix="/price-history", tags=["flight price history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/flight/{flight_id}", response_model=List[schemas.FlightPriceHistoryOut])
def read_price_history(flight_id: int, db: Session = Depends(get_db)):
    return flight_price_history.get_price_history(db, flight_id)
