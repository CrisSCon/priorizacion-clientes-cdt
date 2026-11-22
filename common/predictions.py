"""Prediction fields and limits shared by both services."""

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field


API_PREFIX = "/api/v1"
PREDICT_ROUTE = "/predict"
MAX_BATCH_SIZE = 10_000


@dataclass(frozen=True)
class Prediction:
    """Subscription probabilities, predicted class, and optional batch rank."""

    probability_yes: Annotated[float, Field(ge=0, le=1)]
    probability_no: Annotated[float, Field(ge=0, le=1)]
    prediction: Literal["yes", "no"]
    rank: Annotated[int, Field(gt=0)] | None
