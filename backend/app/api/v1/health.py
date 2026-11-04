from fastapi import APIRouter, Response

from app.schemas.health import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API liveness",
    response_description="The API process can respond; no database or AI checks occur.",
    responses={
        200: {
            "headers": {
                "Cache-Control": {
                    "description": "Prevent caching of liveness results.",
                    "schema": {"type": "string", "const": "no-store"},
                }
            },
            "content": {
                "application/json": {
                    "example": {"status": "ok", "service": "afyaher-api"}
                }
            },
        }
    },
)
def health(response: Response) -> HealthResponse:
    """API liveness only; does not report database or AI readiness."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse()
