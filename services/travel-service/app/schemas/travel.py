from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TripCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=160)
    budget: Decimal = Field(ge=0)
    days: int = Field(ge=1, le=365)
    interests: list[str] = Field(default_factory=list)
    status: str = Field(default="planned", min_length=2, max_length=40)


class TripUpdate(BaseModel):
    destination: str | None = Field(default=None, min_length=2, max_length=160)
    budget: Decimal | None = Field(default=None, ge=0)
    days: int | None = Field(default=None, ge=1, le=365)
    interests: list[str] | None = None
    status: str | None = Field(default=None, min_length=2, max_length=40)


class TripRead(BaseModel):
    id: str
    user_id: str
    destination: str
    budget: Decimal
    days: int
    interests: list[str]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(BaseModel):
    trip_id: str
    category: str = Field(min_length=2, max_length=80)
    amount: Decimal = Field(gt=0)
    description: str = Field(default="", max_length=500)


class ExpenseRead(BaseModel):
    id: str
    trip_id: str
    category: str
    amount: Decimal
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    total_budget: Decimal
    total_spent: Decimal
    remaining_budget: Decimal
