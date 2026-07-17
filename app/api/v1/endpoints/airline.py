from fastapi import APIRouter, Depends  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import airline
from app.db.session import SessionLocal

router = APIRouter(prefix="/airlines", tags=["airlines"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.AirlineOut])
def read_airlines(db: Session = Depends(get_db)):
    return airline.get_airlines(db)
