from fastapi import APIRouter
from ..core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@router.get("/api/status")
def status():
    return {"status": "up", "version": settings.VERSION, "phase": settings.ENVIRONMENT}
