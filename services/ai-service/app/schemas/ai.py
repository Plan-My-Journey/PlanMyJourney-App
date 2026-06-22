from decimal import Decimal

from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=160)
    budget: Decimal = Field(ge=0)
    days: int = Field(ge=1, le=60)
    interests: list[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str


class ItineraryResponse(BaseModel):
    trip_summary: str
    day_wise_plan: list[DayPlan]
    estimated_budget_breakdown: dict[str, str]
    travel_tips: list[str]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1200)


class ChatResponse(BaseModel):
    answer: str


class BudgetOptimizerRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=160)
    budget: Decimal = Field(ge=0)
    days: int = Field(ge=1, le=60)


class BudgetOptimizerResponse(BaseModel):
    budget_saving_suggestions: list[str]


class DestinationCompareRequest(BaseModel):
    destination_a: str = Field(min_length=2, max_length=160)
    destination_b: str = Field(min_length=2, max_length=160)


class DestinationCompareResponse(BaseModel):
    cost_comparison: dict[str, str]
    weather_comparison: dict[str, str]
    activity_comparison: dict[str, str]
    best_choice: str


class PackingListRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=160)
    travel_month: str = Field(min_length=3, max_length=20)


class PackingCategory(BaseModel):
    category: str
    items: list[str]


class PackingListResponse(BaseModel):
    packing_list: list[PackingCategory]


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    job_type: str | None = None
    result: dict | None = None
    error: str | None = None
