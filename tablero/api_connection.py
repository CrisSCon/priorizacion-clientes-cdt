"""HTTP client for dashboard predictions."""

from collections.abc import Mapping, Sequence
from os import getenv
from typing import Any

import requests
from pydantic import BaseModel
from pydantic import ValidationError as ResponseValidationError

from common.predictions import API_PREFIX, PREDICT_ROUTE, Prediction
from common.profiles import ValidationError


class ModelUnavailableError(RuntimeError):
    """The prediction API could not return usable results."""


class _PredictionResponse(BaseModel):
    """The prediction records in the API response."""

    predictions: list[Prediction]


def _validation_message(response: requests.Response) -> str:
    """Read the API's input validation message."""
    try:
        issues = response.json()["detail"]
        message = " ".join(issue["msg"] for issue in issues)
    except (KeyError, TypeError, ValueError):
        message = ""
    return message or "The prediction API rejected the supplied profiles."


def _request_predictions(
    profiles: Sequence[Mapping[str, Any]], *, include_rank: bool
) -> list[Prediction]:
    """Send profiles and decode the returned predictions."""
    if not profiles:
        return []

    host = getenv("API_URL", "localhost")
    port = getenv("API_PORT", "8001")
    url = f"http://{host}:{port}{API_PREFIX}{PREDICT_ROUTE}"
    try:
        response = requests.post(
            url,
            json={
                "inputs": [dict(profile) for profile in profiles],
                "include_rank": include_rank,
            },
            timeout=(3, 90),
            allow_redirects=False,
        )
    except requests.exceptions.Timeout as exc:
        raise ModelUnavailableError("The prediction API timed out.") from exc
    except requests.exceptions.RequestException as exc:
        raise ModelUnavailableError("Could not reach the prediction API.") from exc

    if response.status_code == 422:
        raise ValidationError(_validation_message(response))
    if response.status_code != 200:
        raise ModelUnavailableError(f"The prediction API returned HTTP {response.status_code}.")

    try:
        predictions = _PredictionResponse.model_validate_json(
            response.content, strict=True
        ).predictions
    except ResponseValidationError as exc:
        raise ModelUnavailableError("The prediction API returned an invalid response.") from exc
    if len(predictions) != len(profiles):
        raise ModelUnavailableError("The prediction API returned the wrong number of results.")
    return predictions


def predict_many(profiles: Sequence[Mapping[str, Any]]) -> list[Prediction]:
    """Request ranked predictions in input order."""
    return _request_predictions(profiles, include_rank=True)


def predict_one(profile: Mapping[str, Any]) -> Prediction:
    """Request an unranked prediction for one profile."""
    return _request_predictions([profile], include_rank=False)[0]
