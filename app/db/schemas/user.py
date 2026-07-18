from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    enableNotificationsSetting: bool = True

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    enableNotificationsSetting: Optional[bool] = None


class UserOut(UserBase):
    id: str
