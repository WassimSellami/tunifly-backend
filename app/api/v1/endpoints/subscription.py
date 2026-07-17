from fastapi import APIRouter, Depends, HTTPException, Query  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import subscription
from app.db.session import SessionLocal

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[schemas.SubscriptionOut])
def read_subscriptions(
    email: str = Query(..., description="User email to filter subscriptions"),
    db: Session = Depends(get_db),
):
    return subscription.get_subscriptions_by_email(db, email=email)


@router.get("/flight/{flight_id}", response_model=schemas.SubscriptionOut)
def read_subscription_by_flight_and_email(
    flight_id: int,
    email: str = Query(..., description="User email to filter subscription"),
    db: Session = Depends(get_db),
):
    db_subscription = subscription.get_subscription_by_flight_and_email(
        db, flight_id, email
    )
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription


@router.post("/", response_model=schemas.SubscriptionOut)
def create_subscription(sub: schemas.SubscriptionCreate, db: Session = Depends(get_db)):
    return subscription.create_subscription(db, sub)


@router.put("/{subscription_id}", response_model=schemas.SubscriptionOut)
def update_subscription(
    subscription_id: int,
    sub_update: schemas.SubscriptionUpdate,
    db: Session = Depends(get_db),
):
    updated = subscription.update_subscription(db, subscription_id, sub_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return updated


@router.delete("/{subscription_id}", response_model=schemas.SubscriptionOut)
def delete_subscription(subscription_id: int, db: Session = Depends(get_db)):
    deleted = subscription.delete_subscription(db, subscription_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return deleted
