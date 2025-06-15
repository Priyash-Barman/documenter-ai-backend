# schemas/subscription_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"

class SubscriptionBase(BaseModel):
    user_id: str
    app_id: str
    package_id: str
    stripe_subscription_id: str
    start_date: datetime
    end_date: datetime
    cancel_at_period_end: Optional[datetime] = None
    status: SubscriptionStatus

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    status: Optional[SubscriptionStatus] = None
    cancel_at_period_end: Optional[datetime] = None

class SubscriptionInDB(SubscriptionBase):
    id: str = Field(..., alias="_id")