import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class JobQueueService:
    def __init__(self) -> None:
        self._sqs = boto3.client("sqs", region_name=settings.aws_region)

    @property
    def enabled(self) -> bool:
        return settings.async_jobs_enabled and bool(settings.sqs_queue_url)

    def enqueue(self, job_type: str, payload: dict[str, Any], user_id: str) -> str:
        if not self.enabled:
            raise RuntimeError("Async job queue is not configured")

        job_id = str(uuid.uuid4())
        body = {
            "job_id": job_id,
            "job_type": job_type,
            "user_id": user_id,
            "payload": payload,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._sqs.send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps(body),
            MessageAttributes={
                "job_type": {"DataType": "String", "StringValue": job_type},
            },
        )
        return job_id


class JobStoreService:
    def __init__(self) -> None:
        self._table = boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.jobs_table_name)

    @property
    def enabled(self) -> bool:
        return bool(settings.jobs_table_name)

    def create(self, job_id: str, job_type: str, user_id: str) -> None:
        if not self.enabled:
            return
        expires_at = int((datetime.now(UTC) + timedelta(days=7)).timestamp())
        self._table.put_item(
            Item={
                "job_id": job_id,
                "job_type": job_type,
                "user_id": user_id,
                "status": "queued",
                "created_at": datetime.now(UTC).isoformat(),
                "expires_at": expires_at,
            }
        )

    def mark_processing(self, job_id: str) -> None:
        self._update_status(job_id, "processing")

    def mark_completed(self, job_id: str, result: dict[str, Any]) -> None:
        self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, #result = :result, completed_at = :completed_at",
            ExpressionAttributeNames={"#status": "status", "#result": "result"},
            ExpressionAttributeValues={
                ":status": "completed",
                ":result": result,
                ":completed_at": datetime.now(UTC).isoformat(),
            },
        )

    def mark_failed(self, job_id: str, error: str) -> None:
        self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status, #error = :error, completed_at = :completed_at",
            ExpressionAttributeNames={"#status": "status", "#error": "error"},
            ExpressionAttributeValues={
                ":status": "failed",
                ":error": error[:500],
                ":completed_at": datetime.now(UTC).isoformat(),
            },
        )

    def get(self, job_id: str, user_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            response = self._table.get_item(Key={"job_id": job_id})
        except (ClientError, BotoCoreError):
            logger.exception("Failed to read job")
            return None
        item = response.get("Item")
        if not item or item.get("user_id") != user_id:
            return None
        return item

    def _update_status(self, job_id: str, status: str) -> None:
        if not self.enabled:
            return
        self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": status},
        )
