"""Exercise the prediction API with the packaged model."""

import json
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from api.app import service
from api.app.main import app
from api.app.profiles import DEFAULT_PROFILE


client = TestClient(app)


def test_health_and_docs() -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {
        "name": "CDT Prediction API",
        "api_version": "1.0.0",
        "model_version": version("cdt-model-pkg"),
    }
    assert client.get("/docs").status_code == 200
    openapi = client.get("/api/v1/openapi.json").json()
    assert "/api/v1/predict" in openapi["paths"]


def test_batch_uses_input_order_and_stable_ranks() -> None:
    low = DEFAULT_PROFILE
    high = {**DEFAULT_PROFILE, "previous": 5, "pdays": 15, "poutcome": "success"}
    response = client.post("/api/v1/predict", json={"inputs": [low, high, low]})

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == version("cdt-model-pkg")
    first, second, third = body["predictions"]
    assert [first["rank"], second["rank"], third["rank"]] == [2, 1, 3]
    assert first["probability_yes"] == third["probability_yes"]
    assert second["probability_yes"] > first["probability_yes"]
    for prediction in body["predictions"]:
        assert prediction["prediction"] in ("yes", "no")
        assert 0 <= prediction["probability_yes"] <= 1
        assert prediction["probability_no"] == pytest.approx(1 - prediction["probability_yes"])


def test_unranked_prediction_accepts_numeric_strings() -> None:
    response = client.post(
        "/api/v1/predict",
        json={"inputs": [{**DEFAULT_PROFILE, "age": "40"}], "include_rank": False},
    )
    assert response.status_code == 200
    assert response.json()["predictions"][0]["rank"] is None


@pytest.mark.parametrize(
    "inputs",
    [
        [],
        [{}],
        [{**DEFAULT_PROFILE, "age": True}],
        [{**DEFAULT_PROFILE, "job": "invalid"}],
        [{**DEFAULT_PROFILE, "pdays": -2}],
        [{**DEFAULT_PROFILE, "name": "unexpected"}],
    ],
)
def test_invalid_inputs_are_rejected(inputs: list[dict[str, object]]) -> None:
    response = client.post("/api/v1/predict", json={"inputs": inputs})
    assert response.status_code == 422
    assert response.json()["detail"]


def test_invalid_nonfinite_value_returns_422() -> None:
    content = json.dumps({"inputs": [{**DEFAULT_PROFILE, "balance": [float("inf")]}]})
    response = client.post(
        "/api/v1/predict",
        content=content,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]


def test_unavailable_model_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError("internal artifact path")

    monkeypatch.setattr(service, "predict_dataframe", unavailable)
    response = client.post("/api/v1/predict", json={"inputs": [DEFAULT_PROFILE]})
    assert response.status_code == 503
    assert response.json() == {"detail": "The prediction model is unavailable."}
