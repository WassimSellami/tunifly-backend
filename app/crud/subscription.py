from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.db import models, schemas
from typing import List, Optional


class DuplicateSubscriptionError(Exception):
    """Raised when a user already has a subscription for a flight."""


def get_subscriptions_by_user_id(db: Session, user_id: str) -> List[models.Subscription]:
    return (
        db.query(models.Subscription)
        .join(models.Flight, models.Subscription.flightId == models.Flight.id)
        .filter(models.Subscription.userId == user_id)
        .filter(models.Flight.isAvailable.is_(True))
        .filter(models.Flight.departureDate >= func.current_date())
        .all()
    )


def get_subscription_by_flight_and_user_id(
    db: Session, flight_id: int, user_id: str
) -> Optional[models.Subscription]:
    return (
        db.query(models.Subscription)
        .join(models.Flight, models.Subscription.flightId == models.Flight.id)
        .filter(models.Subscription.flightId == flight_id)
        .filter(models.Subscription.userId == user_id)
        .filter(models.Flight.isAvailable.is_(True))
        .filter(models.Flight.departureDate >= func.current_date())
        .first()
    )


def get_subscription(
    db: Session, subscription_id: int
) -> Optional[models.Subscription]:
    return (
        db.query(models.Subscription)
        .filter(models.Subscription.id == subscription_id)
        .first()
    )


def get_subscription_for_user(
    db: Session, subscription_id: int, user_id: str
) -> Optional[models.Subscription]:
    return (
        db.query(models.Subscription)
        .filter(models.Subscription.id == subscription_id)
        .filter(models.Subscription.userId == user_id)
        .first()
    )


def get_subscriptions(db: Session) -> List[models.Subscription]:
    return (
        db.query(models.Subscription)
        .join(models.Flight, models.Subscription.flightId == models.Flight.id)
        .filter(models.Subscription.isActive == True)
        .filter(models.Flight.departureDate >= func.current_date())
        .all()
    )


def get_active_subscriptions_for_flight_with_notifications_enabled(
    db: Session, flight_id: int
) -> List[models.Subscription]:
    """
    Retrieves active subscriptions for a given flight where the associated user
    has email notifications enabled.
    """
    return (
        db.query(models.Subscription)
        .join(models.User, models.Subscription.userId == models.User.id)
        .join(models.Flight, models.Subscription.flightId == models.Flight.id)
        .filter(models.Subscription.flightId == flight_id)
        .filter(models.Subscription.isActive == True)
        .filter(models.Flight.isAvailable.is_(True))
        .filter(models.Flight.departureDate >= func.current_date())
        .filter(models.User.enableNotificationsSetting == True)
        .all()
    )


def create_subscription(
    db: Session, subscription: schemas.SubscriptionCreate, user_id: str
) -> models.Subscription:
    db_subscription = models.Subscription(**subscription.model_dump(), userId=user_id)
    db_subscription.isActive = True  # type: ignore
    db.add(db_subscription)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateSubscriptionError from error
    db.refresh(db_subscription)
    return db_subscription


def update_subscription(
    db: Session,
    subscription_id: int,
    user_id: str,
    subscription_update: schemas.SubscriptionUpdate,
) -> Optional[models.Subscription]:
    db_subscription = get_subscription_for_user(db, subscription_id, user_id)
    if not db_subscription:
        return None
    
    update_data = subscription_update.model_dump(exclude_unset=True)

    if (
        "targetPrice" in update_data
        and update_data["targetPrice"] != db_subscription.targetPrice
    ):
        db_subscription.isActive = True  # type: ignore
    if "isActive" in update_data:
        db_subscription.isActive = update_data["isActive"]

    for key, value in update_data.items():
        if key != "isActive":
            setattr(db_subscription, key, value)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise DuplicateSubscriptionError from error
    db.refresh(db_subscription)
    return db_subscription


def delete_subscription(
    db: Session, subscription_id: int, user_id: str
) -> Optional[models.Subscription]:
    db_subscription = get_subscription_for_user(db, subscription_id, user_id)
    if not db_subscription:
        return None
    db.delete(db_subscription)
    db.commit()
    return db_subscription
