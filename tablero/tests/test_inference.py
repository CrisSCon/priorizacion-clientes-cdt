"""Verify the local prediction contract and notebook preprocessing parity."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from tablero import api
from tablero.preprocessing import engineer_profile, prepare_features
from tablero.schema import DEFAULT_PROFILE, FEATURE_KEYS, ValidationError


@pytest.mark.parametrize(
    "probability,label", [(0, "no"), (0.4999, "no"), (0.5, "yes"), (1, "yes")]
)
def test_decision_uses_fifty_percent(probability: float, label: str) -> None:
    """A customer at the cutoff receives a yes decision with complementary odds."""
    result = api.classify_probability(probability)
    assert result.prediction == label
    assert result.probability_yes + result.probability_no == pytest.approx(1)


@pytest.mark.parametrize("probability", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_probability_is_rejected(probability: float) -> None:
    """Invalid model output must not be presented as a customer prediction."""
    with pytest.raises(ValueError):
        api.classify_probability(probability)


@pytest.mark.parametrize(
    "key,value",
    [
        ("age", 17),
        ("age", 40.5),
        ("age", None),
        ("balance", "nan"),
        ("previous", -1),
        ("pdays", -2),
        ("job", "doctor"),
        ("housing", "YES"),
        ("loan", True),
    ],
)
def test_invalid_manual_profile_is_rejected(key: str, value: object) -> None:
    """Users receive validation errors instead of misleading scores."""
    with pytest.raises(ValidationError):
        api.predict_one({**DEFAULT_PROFILE, key: value})


@pytest.mark.parametrize(
    "days,category",
    [
        (-1, "missing"),
        (0, "within_week"),
        (7, "within_week"),
        (8, "within_month"),
        (30, "within_month"),
        (31, "within_quarter"),
        (365, "within_year"),
        (366, "over_year"),
    ],
)
def test_contact_recency_boundaries(days: int, category: str) -> None:
    """Contact ages on a boundary use the same inclusive bands as training."""
    features = engineer_profile({**DEFAULT_PROFILE, "pdays": days})
    assert features[f"cat__previous_contact_recency_band_{category}"] == 1


@pytest.mark.parametrize(
    "balance,category",
    [
        (-1, "negative"),
        (-0.5, "zero"),
        (0, "zero"),
        (500, "low_positive"),
        (2000, "medium"),
        (5000, "high"),
        (10000, "very_high"),
        (10001, "extreme"),
    ],
)
def test_balance_boundaries_match_training(balance: float, category: str) -> None:
    """Financial bands preserve the notebook's exact pandas.cut semantics."""
    features = engineer_profile({**DEFAULT_PROFILE, "balance": balance})
    assert features[f"cat__balance_band_{category}"] == 1


def test_never_contacted_profile_uses_frozen_training_statistics() -> None:
    """Missing recency uses training medians without setting contact flags."""
    features = engineer_profile(DEFAULT_PROFILE)
    assert features["num__days_since_previous_contact"] == 195
    assert features["num__days_since_previous_contact_log"] == pytest.approx(
        5.278114659
    )
    assert features["num__had_previous_contact"] == 0
    assert features["num__previous_contact_recent"] == 0


def test_single_and_batch_predictions_agree() -> None:
    """The manual form and CSV workflow score identical customers identically."""
    assert api.predict_one(DEFAULT_PROFILE) == api.predict_many([DEFAULT_PROFILE])[0]


def test_model_missing_has_actionable_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing artifact tells the user which DVC file to retrieve."""
    monkeypatch.setattr(api, "MODEL_PATH", tmp_path / "missing.pkl")
    with pytest.raises(api.ModelUnavailableError, match="dvc pull"):
        api.load_model.__wrapped__()


def test_model_corrupt_has_actionable_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An unreadable artifact does not silently fall back to another model."""
    artifact = tmp_path / "corrupt.pkl"
    artifact.write_bytes(b"not a pickle")
    monkeypatch.setattr(api, "MODEL_PATH", artifact)
    with pytest.raises(api.ModelUnavailableError, match="could not be loaded"):
        api.load_model.__wrapped__()


def test_golden_profiles_match_notebook_export() -> None:
    """Public dataset examples reproduce the original exported feature vectors."""
    examples = json.loads(Path(__file__).with_name("golden_profiles.json").read_text())
    actual = prepare_features(examples["profiles"])
    np.testing.assert_allclose(actual, examples["features"], rtol=1e-12, atol=1e-12)


def test_full_test_partition_matches_notebook() -> None:
    """When local exports exist, verify every held-out row and predicted score."""
    folder = Path(__file__).resolve().parents[2] / "notebooks/data/processed"
    if not (folder / "bank_marketing_feature_engineered.csv").exists():
        pytest.skip("Optional notebook exports are not available locally")
    source = pd.read_csv(
        folder / "bank_marketing_feature_engineered.csv", low_memory=False
    )
    _, indices = train_test_split(
        source.index, test_size=0.2, random_state=42, stratify=source.y
    )
    expected = pd.read_csv(folder / "X_test_final.csv")
    actual = prepare_features(
        source.loc[indices, list(FEATURE_KEYS)].to_dict("records")
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(
        api.load_model().predict_proba(actual),
        api.load_model().predict_proba(expected),
        atol=1e-12,
    )
