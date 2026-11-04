from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.education import router as education_router
from app.api.v1.health import router as health_router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="AfyaHer private prototype API",
        version="0.1.0",
        description=(
            "Private reproductive-health education engineering prototype for adults "
            "18+. Use synthetic inputs only. This API does not diagnose, assess "
            "symptoms, provide treatment, or perform emergency screening.\n\n"
            "The education endpoint is an unavailable stub: valid requests return "
            "HTTP 200 with application status `service_unavailable`, no medical "
            "answer, and no sources. Retrieval, safety screening, evidence "
            "assessment, and model generation are not connected to this route. "
            "Other answer-status enum values are reserved for future reviewed "
            "behavior. Health reports liveness only.\n\n"
            "These docs do not establish clinical validation or approval for "
            "public use. Do not enter real health information or secrets."
        ),
        openapi_tags=[
            {"name": "health", "description": "API liveness, not clinical readiness."},
            {
                "name": "education",
                "description": "Validated educational requests; currently unavailable.",
            },
        ],
        swagger_ui_parameters={"displayRequestDuration": True},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health_router)
    app.include_router(education_router)
    return app


app = create_app()
