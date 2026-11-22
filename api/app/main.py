"""Versioned FastAPI routes for CDT predictions."""

import logging
from importlib.metadata import version

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from api.app import service
from api.app.profiles import ValidationError
from api.app.schemas import HealthResponse, PredictionRequest, PredictionResponse


app = FastAPI(
    title="CDT Prediction API",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
)
router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)
MODEL_VERSION = version("cdt-model-pkg")


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return serializable validation details."""
    detail = [
        {"loc": issue["loc"], "msg": issue["msg"], "type": issue["type"]}
        for issue in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    """Open the interactive API documentation."""
    return RedirectResponse(url="/docs")


@router.get("/health")
def health() -> HealthResponse:
    """Report that the API is running and identify the installed model."""
    return HealthResponse(name=app.title, api_version=app.version, model_version=MODEL_VERSION)


@router.post("/predict", responses={503: {"description": "Model unavailable"}})
def predict(request: PredictionRequest) -> PredictionResponse:
    """Score customer profiles and return one prediction per input."""
    try:
        predictions = service.predict_many(
            [profile.model_dump() for profile in request.inputs],
            include_rank=request.include_rank,
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "inputs"], "msg": str(exc), "type": "value_error"}],
        ) from exc
    except service.ModelUnavailableError as exc:
        logger.exception("CDT prediction failed")
        raise HTTPException(status_code=503, detail="The prediction model is unavailable.") from exc

    return PredictionResponse(version=MODEL_VERSION, predictions=predictions)


app.include_router(router)
