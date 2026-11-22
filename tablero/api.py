"""Connect dashboard predictions to the final XGBoost inference engine."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from model_pkg import inference
from tablero.schema import validate_profile


class ModelUnavailableError(RuntimeError):
    """The final model or its preprocessing artifacts are unavailable."""


@dataclass(frozen=True)
class Prediction:
    """Probability, classification, and ranking for one customer."""

    probability_yes: float
    probability_no: float
    prediction: str
    rank: int | None = None


def _format_prediction(
    probability_yes: float,
    prediction: int,
    rank: int,
) -> Prediction:
    """Convert a model result into the dashboard format."""
    if not np.isfinite(probability_yes) or not 0 <= probability_yes <= 1:
        raise ValueError("Probability must be finite and between zero and one.")

    return Prediction(
        probability_yes=float(probability_yes),
        probability_no=float(1 - probability_yes),
        prediction="yes" if prediction == 1 else "no",
        rank=rank,
    )


def predict_many(
    profiles: Sequence[Mapping[str, Any]],
) -> list[Prediction]:
    """Validate and score profiles, preserving their original input order."""
    if not profiles:
        return []

    validated = [validate_profile(profile) for profile in profiles]

    # Temporary unique identifiers allow restoring the original CSV order
    # after the inference engine sorts customers by descending probability.
    frame = pd.DataFrame(validated)
    identifiers = [f"__customer_{i}__" for i in range(len(frame))]
    frame["name"] = identifiers

    try:
        results = inference.predict_dataframe(frame)
    except Exception as exc:
        raise ModelUnavailableError(
            f"XGBoost inference failed: {exc}"
        ) from exc

    by_identifier = results.set_index("name").to_dict("index")

    predictions = []
    for identifier in identifiers:
        result = by_identifier[identifier]
        predictions.append(
            _format_prediction(
                float(result["probability"]),
                int(result["prediction"]),
                int(result["rank"]),
            )
        )

    return predictions


def predict_one(profile: Mapping[str, Any]) -> Prediction:
    """Score one customer profile without implying a portfolio rank."""
    result = predict_many([profile])[0]
    return Prediction(
        probability_yes=result.probability_yes,
        probability_no=result.probability_no,
        prediction=result.prediction,
        rank=None,
    )
