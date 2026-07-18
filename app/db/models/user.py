from sqlalchemy import Column, String, Boolean
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    # Supabase auth.users.id. It must only be obtained from a verified JWT.
    id = Column(String(36), primary_key=True, index=True, nullable=False)
    email = Column(String(320), unique=True, index=True, nullable=False)
    enableNotificationsSetting = Column(Boolean, default=True, nullable=False)
