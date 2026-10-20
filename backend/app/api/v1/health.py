from fastapi import APIRouter, Response

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """API liveness only; does not report database or AI readiness."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse()
