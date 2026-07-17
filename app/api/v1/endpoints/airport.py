from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import airport
from app.db.session import SessionLocal

router = APIRouter(prefix="/airports", tags=["airports"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.AirportOut])
def read_airports(db: Session = Depends(get_db)):
    return airport.get_airports(db)
