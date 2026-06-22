import asyncio
import json
import logging

import boto3

from app.core.config import settings
from app.schemas.ai import (
    BudgetOptimizerRequest,
    DestinationCompareRequest,
    ItineraryRequest,
    PackingListRequest,
)
from app.services.bedrock_client import TravelAIService
from app.services.job_services import JobStoreService

logger = logging.getLogger(__name__)


class JobProcessor:
    def __init__(self) -> None:
        self._sqs = boto3.client("sqs", region_name=settings.aws_region)
        self._store = JobStoreService()
        self._ai = TravelAIService()

    async def run_forever(self) -> None:
        logger.info("AI worker started for queue %s", settings.sqs_queue_url)
        while True:
            processed = await asyncio.to_thread(self._poll_once)
            if not processed:
                await asyncio.sleep(2)

    def _poll_once(self) -> bool:
        response = self._sqs.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=300,
        )
        messages = response.get("Messages", [])
        if not messages:
            return False

        message = messages[0]
        receipt_handle = message["ReceiptHandle"]
        body = json.loads(message["Body"])
        job_id = body["job_id"]
        job_type = body["job_type"]
        payload = body["payload"]

        self._store.mark_processing(job_id)
        try:
            result = asyncio.run(self._dispatch(job_type, payload))
            self._store.mark_completed(job_id, result)
        except Exception as exc:  # noqa: BLE001 - worker boundary
            logger.exception("Job %s failed", job_id)
            self._store.mark_failed(job_id, str(exc))
        finally:
            self._sqs.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle)
        return True

    async def _dispatch(self, job_type: str, payload: dict) -> dict:
        if job_type == "itinerary":
            return (await self._ai.generate_itinerary(ItineraryRequest.model_validate(payload))).model_dump()
        if job_type == "budget_optimizer":
            return (await self._ai.optimize_budget(BudgetOptimizerRequest.model_validate(payload))).model_dump()
        if job_type == "compare":
            return (await self._ai.compare_destinations(DestinationCompareRequest.model_validate(payload))).model_dump()
        if job_type == "packing_list":
            return (await self._ai.packing_list(PackingListRequest.model_validate(payload))).model_dump()
        raise ValueError(f"Unsupported job type: {job_type}")
