from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.crud import subscription
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
    user.get_or_create_user(db, current_user.id, current_user.email)
    return subscription.create_subscription(db, sub, current_user.id)


@router.put("/{subscription_id}", response_model=schemas.SubscriptionOut)
def update_subscription(
    subscription_id: int,
    sub_update: schemas.SubscriptionUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
