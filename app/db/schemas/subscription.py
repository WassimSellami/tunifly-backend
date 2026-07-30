from pydantic import BaseModel, Field
from typing import Optional


class SubscriptionBase(BaseModel):
    flightId: int
    targetPrice: float = Field(ge=1, allow_inf_nan=False)

    class Config:
        from_attributes = True


class SubscriptionCreate(SubscriptionBase):
    isActive: Optional[bool] = True


class SubscriptionUpdate(BaseModel):
    flightId: Optional[int] = None
    targetPrice: Optional[float] = Field(default=None, ge=1, allow_inf_nan=False)
    isActive: Optional[bool] = None
    enableEmailNotifications: Optional[bool] = None


class SubscriptionOut(SubscriptionBase):
    id: int
    isActive: bool
