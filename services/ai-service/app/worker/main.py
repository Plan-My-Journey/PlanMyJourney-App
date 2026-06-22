import asyncio
import logging

from app.core.config import settings
from app.worker.processor import JobProcessor

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.sqs_queue_url or not settings.jobs_table_name:
        raise SystemExit("SQS_QUEUE_URL and JOBS_TABLE_NAME are required for the worker")
    processor = JobProcessor()
    asyncio.run(processor.run_forever())


if __name__ == "__main__":
    main()
