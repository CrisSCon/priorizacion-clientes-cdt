"""In-process inference boundary; no HTTP API or remote calls are implemented.

The UI calls these functions without accessing the model directly. Only the
repository's trusted gradient_boosting_final.pkl artifact is ever loaded.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pickle
from typing import Any, Mapping, Sequence
import warnings

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.exceptions import InconsistentVersionWarning

from tablero.preprocessing import METADATA, prepare_features

MODEL_PATH = Path(__file__).resolve().parents[1] / "models/gradient_boosting_final.pkl"
THRESHOLD = 0.5


class ModelUnavailableError(RuntimeError):
    """Indicate that the selected artifact cannot safely serve predictions."""


@dataclass(frozen=True)
class Prediction:
    """Represent complementary class probabilities and the 50% decision."""

    probability_yes: float
    probability_no: float
    prediction: str


def classify_probability(probability_yes: float) -> Prediction:
    """Classify a finite probability, treating exactly 50% as yes."""
    if not np.isfinite(probability_yes) or not 0 <= probability_yes <= 1:
        raise ValueError("Probability must be finite and between zero and one.")
    return Prediction(
        float(probability_yes),
        float(1 - probability_yes),
        "yes" if probability_yes >= THRESHOLD else "no",
    )


@lru_cache(maxsize=1)
def load_model() -> GradientBoostingClassifier:
    """Load and check the single supported artifact once per process.

    Missing DVC artifacts and incompatible scikit-learn versions produce an
    actionable message. A different feature contract is never guessed.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", InconsistentVersionWarning)
            with MODEL_PATH.open("rb") as artifact:
                model = pickle.load(artifact)
    except FileNotFoundError as exc:
        raise ModelUnavailableError(
            "The final model is missing. Run dvc pull "
            "models/gradient_boosting_final.pkl.dvc from the repository root."
        ) from exc
    except Exception as exc:
        raise ModelUnavailableError(
            "The final model could not be loaded. Install requirements.txt "
            "and restore models/gradient_boosting_final.pkl with DVC."
        ) from exc
    if (
        not isinstance(model, GradientBoostingClassifier)
        or list(model.feature_names_in_) != METADATA["feature_names"]
        or list(model.classes_) != [0, 1]
    ):
        raise ModelUnavailableError("The final model has an incompatible input schema.")
    return model


def predict_many(profiles: Sequence[Mapping[str, Any]]) -> list[Prediction]:
    """Validate and score profiles in one local model call, preserving order."""
    if not profiles:
        return []
    features = prepare_features(profiles)
    probabilities = load_model().predict_proba(features)[:, 1]
    return [classify_probability(float(value)) for value in probabilities]


def predict_one(profile: Mapping[str, Any]) -> Prediction:
    """Score one complete source profile using the same path as CSV scoring."""
    return predict_many([profile])[0]
