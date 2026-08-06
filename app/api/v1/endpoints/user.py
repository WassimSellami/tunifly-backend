from fastapi import (  # type: ignore
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.db import schemas
from app.crud import user
from app.db.session import (
    SessionLocal,
)
from app.core.auth import AuthenticatedUser, get_current_user
from app.services import email_alerts

router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me", response_model=schemas.UserOut)
def read_current_user_endpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user, was_created = user.get_or_create_user_with_status(
        db, current_user.id, current_user.email
    )
    if was_created:
        email_alerts.send_welcome_email(db_user.email)
    return db_user


@router.put("/me", response_model=schemas.UserOut)
def update_current_user_endpoint(
    user_update: schemas.UserUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated_user = user.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user
