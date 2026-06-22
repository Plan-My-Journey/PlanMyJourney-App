from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

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
    JobAcceptedResponse,
    JobStatusResponse,
    PackingListRequest,
    PackingListResponse,
)
from app.services.bedrock_client import TravelAIService
from app.services.job_services import JobQueueService, JobStoreService

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = TravelAIService()
job_queue = JobQueueService()
job_store = JobStoreService()


async def _enqueue_or_run(
    job_type: str,
    payload: dict[str, Any],
    current_user: CurrentUser,
    runner,
):
    if job_queue.enabled:
        job_id = job_queue.enqueue(job_type, payload, current_user.id)
        job_store.create(job_id, job_type, current_user.id)
        return JobAcceptedResponse(job_id=job_id)
    return await runner()


@router.post("/itinerary", response_model=ItineraryResponse | JobAcceptedResponse)
async def itinerary(
    payload: ItineraryRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    response: Response,
):
    result = await _enqueue_or_run(
        "itinerary",
        payload.model_dump(mode="json"),
        current_user,
        lambda: ai_service.generate_itinerary(payload),
    )
    if isinstance(result, JobAcceptedResponse):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    return await ai_service.chat(payload)


@router.post("/budget-optimizer", response_model=BudgetOptimizerResponse | JobAcceptedResponse)
async def budget_optimizer(
    payload: BudgetOptimizerRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    response: Response,
):
    result = await _enqueue_or_run(
        "budget_optimizer",
        payload.model_dump(mode="json"),
        current_user,
        lambda: ai_service.optimize_budget(payload),
    )
    if isinstance(result, JobAcceptedResponse):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.post("/compare", response_model=DestinationCompareResponse | JobAcceptedResponse)
async def compare(
    payload: DestinationCompareRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    response: Response,
):
    result = await _enqueue_or_run(
        "compare",
        payload.model_dump(mode="json"),
        current_user,
        lambda: ai_service.compare_destinations(payload),
    )
    if isinstance(result, JobAcceptedResponse):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.post("/packing-list", response_model=PackingListResponse | JobAcceptedResponse)
async def packing_list(
    payload: PackingListRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    response: Response,
):
    result = await _enqueue_or_run(
        "packing_list",
        payload.model_dump(mode="json"),
        current_user,
        lambda: ai_service.packing_list(payload),
    )
    if isinstance(result, JobAcceptedResponse):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def job_status(
    job_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    item = job_store.get(job_id, current_user.id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobStatusResponse(
        job_id=job_id,
        status=item.get("status", "unknown"),
        job_type=item.get("job_type"),
        result=item.get("result"),
        error=item.get("error"),
    )
