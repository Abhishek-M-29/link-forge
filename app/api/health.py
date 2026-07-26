from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.cache.redis_client import redis_client

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok"}

import logging
logger = logging.getLogger(__name__)

@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    checks = {"database": False, "redis": False}
    errors = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error("Database readiness check failed: %s", e)
        errors["database"] = str(e)

    try:
        redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error("Redis readiness check failed: %s", e)
        errors["redis"] = str(e)

    all_ready = all(checks.values())
    content = {"ready": all_ready, "checks": checks}
    if errors:
        content["errors"] = errors
        
    return JSONResponse(
        status_code=200 if all_ready else 503,
        content=content
    )
