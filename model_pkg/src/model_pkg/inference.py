from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb


TRAINED_DIR = Path(__file__).resolve().parent / "trained"
MODEL_PATH = TRAINED_DIR / "xgboost_final.ubj"
PREPROCESSOR_PATH = TRAINED_DIR / "preprocessor_final.joblib"
METADATA_PATH = TRAINED_DIR / "inference_metadata.json"

REQUIRED_COLUMNS = [
    "age", "job", "marital", "education", "default",
    "balance", "housing", "loan", "pdays", "previous", "poutcome"
]


def load_artifacts():
    with open(METADATA_PATH, encoding="utf-8") as file:
        metadata = json.load(file)

    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)

    return model, preprocessor, metadata


def build_features(raw, balance_median=451.0):
    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")

    df = raw.copy()

    # Normalización de variables categóricas.
    categorical = [
        "job", "marital", "education", "default",
        "housing", "loan", "poutcome"
    ]
    for col in categorical:
        df[col] = df[col].astype("string").str.strip().str.lower()

    # Conversión numérica.
    for col in ["age", "balance", "pdays", "previous"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    age = df["age"]
    balance = df["balance"]
    previous = df["previous"]
    pdays = df["pdays"]

    # Edad.
    df["age_squared"] = age ** 2
    df["age_group_18_29"] = age.between(18, 29).astype(int)
    df["age_30_plus"] = (age >= 30).astype(int)
    df["age_60_plus"] = (age >= 60).astype(int)

    df["age_bucket"] = pd.cut(
        age,
        bins=[18, 30, 40, 50, 60, 70, 80, np.inf],
        labels=["18-29", "30-39", "40-49", "50-59",
                "60-69", "70-79", "80_plus"],
        right=False
    )

    # Saldo.
    df["balance_negative"] = (balance < 0).astype(int)
    df["balance_zero"] = (balance == 0).astype(int)
    df["balance_positive"] = (balance > 0).astype(int)
    df["balance_abs"] = balance.abs()

    df["balance_band"] = pd.cut(
        balance,
        bins=[-np.inf, -1, 0, 500, 2000, 5000, 10000, np.inf],
        labels=["negative", "zero", "low_positive", "medium",
                "high", "very_high", "extreme"]
    )

    # Historial de contactos anteriores.
    df["had_previous_contact"] = (pdays >= 0).astype(int)
    df["days_since_previous_contact"] = pdays.where(pdays >= 0, np.nan)
    df["had_previous_campaign_contact"] = (previous > 0).astype(int)

    df["previous_contact_band"] = pd.cut(
        previous,
        bins=[-1, 0, 1, 3, 5, np.inf],
        labels=["none", "one", "two_to_three",
                "four_to_five", "more_than_five"]
    )

    df["previous_contact_recency_band"] = pd.cut(
        df["days_since_previous_contact"],
        bins=[-0.1, 7, 30, 90, 180, 365, np.inf],
        labels=["within_week", "within_month", "within_quarter",
                "within_half_year", "within_year", "over_year"]
    )

    df["previous_contact_recent"] = (
        df["days_since_previous_contact"] <= 30
    ).fillna(False).astype(int)

    df["previous_contact_old"] = (
        df["days_since_previous_contact"] > 180
    ).fillna(False).astype(int)

    df["previous_success"] = (
        (df["poutcome"] == "success") & (previous > 0)
    ).astype(int)

    df["previous_failure"] = (
        (df["poutcome"] == "failure") & (previous > 0)
    ).astype(int)

    # Productos y características del cliente.
    df["has_housing_loan"] = (df["housing"] == "yes").astype(int)
    df["has_personal_loan"] = (df["loan"] == "yes").astype(int)
    df["has_default"] = (df["default"] == "yes").astype(int)

    df["active_loan_products_count"] = (
        df["has_housing_loan"] + df["has_personal_loan"]
    )
    df["has_any_loan"] = (
        df["active_loan_products_count"] > 0
    ).astype(int)
    df["housing_without_personal_loan"] = (
        (df["housing"] == "yes") & (df["loan"] == "no")
    ).astype(int)
    df["both_loans"] = (
        (df["housing"] == "yes") & (df["loan"] == "yes")
    ).astype(int)

    df["is_retired"] = (df["job"] == "retired").astype(int)
    df["is_student"] = (df["job"] == "student").astype(int)
    df["is_unemployed"] = (df["job"] == "unemployed").astype(int)
    df["job_unknown"] = (df["job"] == "unknown").astype(int)
    df["education_unknown"] = (df["education"] == "unknown").astype(int)
    df["is_married"] = (df["marital"] == "married").astype(int)
    df["is_single"] = (df["marital"] == "single").astype(int)

    # Transformaciones logarítmicas.
    df["age_log"] = np.log1p(age)
    df["previous_log"] = np.log1p(previous)
    df["days_since_previous_contact_log"] = np.log1p(
        df["days_since_previous_contact"]
    )
    df["balance_abs_log"] = np.log1p(balance.abs())
    df["age_squared_log"] = np.log1p(df["age_squared"])
    df["balance_signed_log"] = (
        np.sign(balance) * np.log1p(balance.abs())
    )

    # Umbral calculado exclusivamente con el conjunto de entrenamiento.
    df["balance_above_median"] = (
        balance > balance_median
    ).astype(int)

    return df


def predict_dataframe(raw):
    model, preprocessor, metadata = load_artifacts()

    identifiers = (
        raw["name"].reset_index(drop=True)
        if "name" in raw.columns
        else pd.Series(raw.index.astype(str), name="name")
    )

    features = build_features(raw, metadata['balance_median_train'])

    numeric = metadata["numeric_features"]
    categorical = metadata["categorical_features"]
    model_input = features[numeric + categorical]

    transformed = preprocessor.transform(model_input)

    expected = len(metadata["feature_names"])
    if transformed.shape[1] != expected:
        raise ValueError(
            f"Se generaron {transformed.shape[1]} variables; "
            f"el modelo espera {expected}."
        )

    probabilities = model.predict_proba(transformed)[:, 1]
    threshold = float(metadata["threshold"])

    result = pd.DataFrame({
        "name": identifiers,
        "probability": probabilities,
        "prediction": (probabilities >= threshold).astype(int)
    })

    result["rank"] = (
        result["probability"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    return result.sort_values("rank").reset_index(drop=True)
