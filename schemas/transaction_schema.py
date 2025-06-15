# schemas/transaction_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class TransactionBase(BaseModel):
    subscription_id: str
    stripe_payment_intent_id: str
    stripe_invoice_id: str
    amount: float
    currency: str
    status: TransactionStatus
    is_active: bool = True

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    is_active: Optional[bool] = None

class TransactionInDB(TransactionBase):
    id: str = Field(..., alias="_id")
    timestamp: datetime