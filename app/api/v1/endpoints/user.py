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
    return user.get_or_create_user(db, current_user.id, current_user.email)


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
