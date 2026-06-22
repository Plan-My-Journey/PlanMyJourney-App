"""Shared health check endpoints for Kubernetes probes."""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter(tags=["health"])


def create_health_router(service_name: str, db_session_factory=None):
    @router.get("/health")
    def health_legacy() -> dict[str, str]:
        return {"status": "healthy", "service": service_name}

    @router.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": service_name}

    @router.get("/ready")
    def ready() -> dict[str, str]:
        if db_session_factory is None:
            return {"status": "ready", "service": service_name}
        db: Session = db_session_factory()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ready", "service": service_name}
        except Exception:
            return {"status": "not_ready", "service": service_name}
        finally:
            db.close()

    return router
