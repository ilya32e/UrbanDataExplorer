from fastapi import APIRouter, HTTPException

from common.database import ping_sql_database
from common.document_store import ping_document_store

from ..auth import auth_status
from ..security import metrics_snapshot, security_status


router = APIRouter(tags=["health"])


@router.get("/metrics")
def metrics() -> dict[str, object]:
    return metrics_snapshot()


@router.get("/health")
def healthcheck() -> dict[str, object]:
    try:
        ping_sql_database()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MySQL indisponible: {exc}") from exc

    try:
        ping_document_store()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB indisponible: {exc}") from exc

    return {
        "status": "ok",
        "sql": "mysql",
        "nosql": "mongodb",
        "mysql": "ok",
        "mongodb": "ok",
        "security": security_status(),
        "auth": auth_status(),
    }
