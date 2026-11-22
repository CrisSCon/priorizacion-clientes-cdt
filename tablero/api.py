"""Dashboard adapter pending the switch to the HTTP prediction API."""

from collections.abc import Mapping, Sequence
from typing import Any

from api.app import service
from api.app.service import ModelUnavailableError as ModelUnavailableError
from api.app.service import Prediction as Prediction


def predict_many(profiles: Sequence[Mapping[str, Any]]) -> list[Prediction]:
    """Request ranked predictions in input order."""
    # TODO: POST non-empty batches to /api/v1/predict and return predictions.
    return service.predict_many(profiles)


def predict_one(profile: Mapping[str, Any]) -> Prediction:
    """Request an unranked prediction for one profile."""
    # TODO: POST one input to /api/v1/predict with include_rank=false.
    return service.predict_one(profile)
