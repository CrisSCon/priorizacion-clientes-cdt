"""Verify dashboard endpoints, callback workflows, and chart meaning."""

import base64
import json
from typing import Any

import pytest
from dash import Dash

from tablero.app import create_app
from tablero.batch import process_csv, template_csv
from tablero.figures import probability_distribution
from tablero.schema import DEFAULT_PROFILE


@pytest.fixture(scope="module")
def app() -> Dash:
    """Create one local app for exercising user-facing Dash endpoints."""
    return create_app()


def callback_request(
    app: Dash,
    output_prefix: str,
    inputs: list[dict[str, Any]],
    state: list[dict[str, Any]] | None = None,
    changed: str | None = None,
) -> dict[str, Any]:
    """Submit a Dash callback request without browser-specific implementation code."""
    key = next(key for key in app.callback_map if key.startswith(output_prefix))
    output = app.callback_map[key]["output"]
    outputs = (
        [item.to_dict() for item in output]
        if isinstance(output, list)
        else output.to_dict()
    )
    response = app.server.test_client().post(
        "/_dash-update-component",
        json={
            "output": key,
            "outputs": outputs,
            "inputs": inputs,
            "state": state or [],
            "changedPropIds": [changed or f"{inputs[0]['id']}.{inputs[0]['property']}"],
        },
    )
    assert response.status_code == 200, response.data.decode()
    return response.json["response"]


@pytest.mark.parametrize(
    "route", ["/", "/manual", "/csv", "/_dash-layout", "/_dash-dependencies"]
)
def test_pages_are_available(app: Dash, route: str) -> None:
    """Each public page and its Dash configuration can be loaded locally."""
    assert app.server.test_client().get(route).status_code == 200


def test_download_is_a_valid_csv_attachment(app: Dash) -> None:
    """The main-page download produces a file that the scoring service accepts."""
    response = app.server.test_client().get("/download/template.csv")
    assert response.status_code == 200
    assert 'filename="cdt_template.csv"' in response.headers["Content-Disposition"]
    assert len(process_csv(response.data.decode())) == 3


@pytest.mark.parametrize(
    "route,page", [("/", "home-page"), ("/manual", "manual-page"), ("/csv", "csv-page")]
)
def test_navigation_shows_requested_workflow(app: Dash, route: str, page: str) -> None:
    """Only the requested workflow is visible while its siblings retain state."""
    result = callback_request(
        app,
        "..home-page",
        [
            {"id": "location", "property": "pathname", "value": route},
        ],
    )
    assert result[page]["style"] == {}
    assert sum(value.get("style") == {} for value in result.values()) == 1


@pytest.mark.parametrize(
    "age,expected", [(40, "10.1"), (65, "31.4"), (None, "Age is required")]
)
def test_manual_edits_update_or_clear_prediction(
    app: Dash, age: int | None, expected: str
) -> None:
    """A settled edit updates the estimate; blank inputs remove stale probabilities."""
    result = callback_request(
        app,
        "manual-result",
        [
            {
                "id": "profile-values",
                "property": "data",
                "value": {**DEFAULT_PROFILE, "age": age},
            },
        ],
    )
    serialized = json.dumps(result)
    assert expected in serialized
    if age is None:
        assert "probability-number" not in serialized


@pytest.mark.parametrize("valid", [True, False])
def test_upload_callback_reports_success_or_clears_stale_results(
    app: Dash, valid: bool
) -> None:
    """Uploading a malformed replacement cannot leave the previous list visible."""
    text = template_csv() if valid else "wrong,header\ninvalid,row"
    contents = "data:text/csv;base64," + base64.b64encode(text.encode()).decode()
    result = callback_request(
        app,
        "..batch-data",
        [
            {"id": "csv-upload", "property": "contents", "value": contents},
            {"id": "sample-data", "property": "n_clicks", "value": None},
        ],
        [{"id": "csv-upload", "property": "filename", "value": "customers.csv"}],
    )
    assert len(result["batch-data"]["data"]) == (3 if valid else 0)
    assert ("success-message" if valid else "error-message") in result[
        "upload-message"
    ]["className"]


def test_filtered_table_shows_matching_customer(app: Dash) -> None:
    """Name and prediction controls together return the intended contact."""
    result = callback_request(
        app,
        "..results-grid.rowData",
        [
            {
                "id": "batch-data",
                "property": "data",
                "value": process_csv(template_csv()),
            },
            {"id": "name-filter", "property": "value", "value": "customer 2"},
            {"id": "prediction-filter", "property": "value", "value": "yes"},
        ],
    )
    assert result["visible-count"]["children"] == "1 of 3 customers"
    assert result["results-grid"]["rowData"][0]["name"] == "Sample customer 2"


def test_detail_callback_uses_source_id_after_sorting(app: Dash) -> None:
    """The first displayed row may be source row two; details must follow its ID."""
    result = callback_request(
        app,
        "..detail-content",
        [
            {
                "id": "results-grid",
                "property": "cellClicked",
                "value": {"rowId": "2", "rowIndex": 0},
            },
            {"id": "results-grid", "property": "cellRendererData", "value": None},
            {
                "id": "batch-data",
                "property": "data",
                "value": process_csv(template_csv()),
            },
        ],
    )
    assert result["modal-event"]["data"]["open"] is True
    assert "Sample customer 2" in json.dumps(result["detail-content"])
    assert "Sample customer 1" not in json.dumps(result["detail-content"])


@pytest.mark.parametrize(
    "probabilities,expected",
    [([], [0] * 10), ([0, 0.4999, 0.5, 1, None], [1, 0, 0, 0, 1, 1, 0, 0, 0, 1])],
)
def test_distribution_counts_and_threshold(
    probabilities: list[float | None], expected: list[int]
) -> None:
    """The plot includes valid extremes, excludes errors, and marks the cutoff."""
    figure = probability_distribution(
        [{"probability_yes": value} for value in probabilities]
    )
    assert list(figure.data[0].y) == expected
    assert figure.layout.shapes[0].x0 == 50
