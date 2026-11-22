"""Validate profiles and format predictions from the installed model."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any, Literal

import pandas as pd

from api.app.profiles import ValidationError, validate_profile
from model_pkg.inference import predict_dataframe


class ModelUnavailableError(RuntimeError):
    """The trained model could not return predictions."""


@dataclass(frozen=True)
class Prediction:
    """Subscription probabilities, predicted class, and optional batch rank."""

    probability_yes: float
    probability_no: float
    prediction: Literal["yes", "no"]
    rank: int | None = None


def _format_prediction(probability: float, prediction: int, rank: int | None) -> Prediction:
    """Convert a model row to the API result format."""
    if not isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probability must be finite and between zero and one.")
    return Prediction(
        probability_yes=probability,
        probability_no=1 - probability,
        prediction="yes" if prediction == 1 else "no",
        rank=rank,
    )


def predict_many(
    profiles: Sequence[Mapping[str, Any]], *, include_rank: bool = True
) -> list[Prediction]:
    """Score profiles and preserve their input order."""
    if not profiles:
        return []

    validated = []
    for index, profile in enumerate(profiles, start=1):
        try:
            validated.append(validate_profile(profile))
        except ValidationError as exc:
            raise ValidationError(f"Profile {index}: {exc}") from exc

    frame = pd.DataFrame(validated)
    # The wheel uses stringified row indices as identifiers when name is absent.
    identifiers = frame.index.astype(str)
    try:
        results = predict_dataframe(frame).set_index("name").loc[identifiers]
        return [
            _format_prediction(
                float(row.probability),
                int(row.prediction),
                int(row.rank) if include_rank else None,
            )
            for row in results.itertuples()
        ]
    except Exception as exc:
        raise ModelUnavailableError("The prediction model is unavailable.") from exc


def predict_one(profile: Mapping[str, Any]) -> Prediction:
    """Score a single profile without a batch rank."""
    return predict_many([profile], include_rank=False)[0]
