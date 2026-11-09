"""Reproduce notebook 01's features using frozen training-only statistics.

The final pickle contains only a classifier. These transformations reproduce
the notebook's numeric features and one-hot encoding without fitting anything
at inference time. See preprocessing.json for training statistics and feature order.
"""

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from tablero.schema import validate_profile

METADATA = json.loads(
    Path(__file__).with_name("preprocessing.json").read_text(encoding="utf-8")
)


def engineer_profile(profile: Mapping[str, Any]) -> dict[str, float]:
    """Expand a validated customer profile into the 94 trained predictors.

    For a never-contacted customer, recency flags remain false, the category
    is ``missing``, and numeric recency uses the frozen training median.
    Derived inputs are computed together to avoid inconsistent manual flags.
    """
    p = validate_profile(profile)
    age, balance = float(p["age"]), float(p["balance"])
    previous, pdays = float(p["previous"]), float(p["pdays"])
    housing, loan = p["housing"] == "yes", p["loan"] == "yes"
    days = pdays if pdays >= 0 else METADATA["recency_median"]
    numeric = {
        "age": age,
        "balance": balance,
        "previous": previous,
        "age_squared": age**2,
        "age_group_18_29": 18 <= age <= 29,
        "age_30_plus": age >= 30,
        "age_60_plus": age >= 60,
        "balance_negative": balance < 0,
        "balance_zero": balance == 0,
        "balance_positive": balance > 0,
        "balance_abs": abs(balance),
        "had_previous_contact": pdays >= 0,
        "days_since_previous_contact": days,
        "had_previous_campaign_contact": previous > 0,
        "previous_contact_recent": 0 <= pdays <= 30,
        "previous_contact_old": pdays > 180,
        "previous_success": p["poutcome"] == "success" and previous > 0,
        "previous_failure": p["poutcome"] == "failure" and previous > 0,
        "has_housing_loan": housing,
        "has_personal_loan": loan,
        "has_default": p["default"] == "yes",
        "active_loan_products_count": int(housing) + int(loan),
        "has_any_loan": housing or loan,
        "housing_without_personal_loan": housing and not loan,
        "both_loans": housing and loan,
        "is_retired": p["job"] == "retired",
        "is_student": p["job"] == "student",
        "is_unemployed": p["job"] == "unemployed",
        "job_unknown": p["job"] == "unknown",
        "education_unknown": p["education"] == "unknown",
        "is_married": p["marital"] == "married",
        "is_single": p["marital"] == "single",
        "balance_signed_log": np.sign(balance) * np.log1p(abs(balance)),
        "balance_above_median": balance > METADATA["balance_median"],
    }
    for key in (
        "age",
        "previous",
        "days_since_previous_contact",
        "balance_abs",
        "age_squared",
    ):
        numeric[f"{key}_log"] = np.log1p(numeric[key])
    if pdays < 0:
        numeric["days_since_previous_contact_log"] = METADATA["recency_log_median"]
    categories = {
        key: p[key]
        for key in (
            "job",
            "marital",
            "education",
            "default",
            "housing",
            "loan",
            "poutcome",
        )
    }
    categories["age_bucket"] = (
        "18-29"
        if age < 30
        else f"{int(age // 10) * 10}-{int(age // 10) * 10 + 9}"
        if age < 80
        else "80_plus"
    )
    categories["balance_band"] = band(
        balance,
        (-1, 0, 500, 2000, 5000, 10000),
        ("negative", "zero", "low_positive", "medium", "high", "very_high", "extreme"),
    )
    categories["previous_contact_band"] = band(
        previous,
        (0, 1, 3, 5),
        ("none", "one", "two_to_three", "four_to_five", "more_than_five"),
    )
    categories["previous_contact_recency_band"] = (
        "missing"
        if pdays < 0
        else band(
            pdays,
            (7, 30, 90, 180, 365),
            (
                "within_week",
                "within_month",
                "within_quarter",
                "within_half_year",
                "within_year",
                "over_year",
            ),
        )
    )
    features = {f"num__{key}": float(value) for key, value in numeric.items()}
    selected = {f"cat__{key}_{value}" for key, value in categories.items()}
    features.update(
        {
            name: float(name in selected)
            for name in METADATA["feature_names"]
            if name.startswith("cat__")
        }
    )
    return features


def band(value: float, bounds: Sequence[float], labels: Sequence[str]) -> str:
    """Return a right-inclusive band, matching pandas.cut in the notebook."""
    return labels[int(np.searchsorted(bounds, value, side="left"))]


def prepare_features(profiles: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    """Return finite predictors in the exact order expected by the classifier."""
    return pd.DataFrame(
        [engineer_profile(profile) for profile in profiles],
        columns=METADATA["feature_names"],
        dtype=float,
    )
