from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.security import CurrentUser
from app.schemas.ai import (
    BudgetOptimizerRequest,
    BudgetOptimizerResponse,
    ChatRequest,
    ChatResponse,
    DestinationCompareRequest,
    DestinationCompareResponse,
    ItineraryRequest,
    ItineraryResponse,
    PackingListRequest,
    PackingListResponse,
)
from app.services.bedrock_client import TravelAIService

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = TravelAIService()


@router.post("/itinerary", response_model=ItineraryResponse)
async def itinerary(
    payload: ItineraryRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.generate_itinerary(payload)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.chat(payload)


@router.post("/budget-optimizer", response_model=BudgetOptimizerResponse)
async def budget_optimizer(
    payload: BudgetOptimizerRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.optimize_budget(payload)


@router.post("/compare", response_model=DestinationCompareResponse)
async def compare(
    payload: DestinationCompareRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.compare_destinations(payload)


@router.post("/packing-list", response_model=PackingListResponse)
async def packing_list(
    payload: PackingListRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.packing_list(payload)
