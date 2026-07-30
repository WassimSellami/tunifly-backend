from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import flight, subscription
from app.db.session import SessionLocal
from app.core.auth import AuthenticatedUser, get_current_user
from app.crud import user

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_target_price(target_price: float, current_price: float) -> None:
    if target_price >= current_price:
        raise HTTPException(
            status_code=422,
            detail="Target price must be lower than the flight's current price.",
        )


@router.get("/", response_model=List[schemas.SubscriptionOut])
def read_subscriptions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return subscription.get_subscriptions_by_user_id(db, user_id=current_user.id)


@router.get("/flight/{flight_id}", response_model=schemas.SubscriptionOut)
def read_subscription_by_flight(
    flight_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_subscription = subscription.get_subscription_by_flight_and_user_id(
        db, flight_id, current_user.id
    )
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription


@router.post("/", response_model=schemas.SubscriptionOut)
def create_subscription(
    sub: schemas.SubscriptionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_flight = flight.get_flight(db, sub.flightId)
    if not db_flight or not db_flight.isAvailable:
        raise HTTPException(status_code=404, detail="Flight not found")
    _validate_target_price(sub.targetPrice, db_flight.priceEur)
    user.get_or_create_user(db, current_user.id, current_user.email)
    return subscription.create_subscription(db, sub, current_user.id)


@router.put("/{subscription_id}", response_model=schemas.SubscriptionOut)
def update_subscription(
    subscription_id: int,
    sub_update: schemas.SubscriptionUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_subscription = subscription.get_subscription_for_user(
        db, subscription_id, current_user.id
    )
    if not existing_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub_update.flightId is not None or sub_update.targetPrice is not None:
        flight_id = (
            sub_update.flightId
            if sub_update.flightId is not None
            else existing_subscription.flightId
        )
        db_flight = flight.get_flight(db, flight_id)
        if not db_flight or not db_flight.isAvailable:
            raise HTTPException(status_code=404, detail="Flight not found")
        target_price = (
            sub_update.targetPrice
            if sub_update.targetPrice is not None
            else existing_subscription.targetPrice
        )
        _validate_target_price(target_price, db_flight.priceEur)

    updated = subscription.update_subscription(db, subscription_id, current_user.id, sub_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return updated


@router.delete("/{subscription_id}", response_model=schemas.SubscriptionOut)
def delete_subscription(
    subscription_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = subscription.delete_subscription(db, subscription_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return deleted
