"""Test CSV workflows through the same functions called by the dashboard."""

import base64
import csv
import io
from typing import Any

import pytest

from tablero import api, batch
from tablero.schema import CSV_COLUMNS, DEFAULT_PROFILE, ValidationError


def make_csv(rows: list[dict[str, Any]]) -> str:
    """Serialize test customer records with the public upload contract."""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def test_template_can_be_uploaded_and_scored() -> None:
    """The downloaded sample works without editing and includes both decisions."""
    rows = batch.process_csv(batch.template_csv())
    assert batch.summarize(rows) == {
        "total": 3,
        "processed": 3,
        "errors": 0,
        "yes": 1,
        "no": 2,
    }
    assert (
        rows[0]["probability_yes"] == api.predict_one(DEFAULT_PROFILE).probability_yes
    )


@pytest.mark.parametrize(
    "source,count", [(batch.template_csv, 3), (batch.sample_csv, 120)]
)
def test_example_files_contain_valid_varied_customers(source: Any, count: int) -> None:
    """Templates and sample lists score every row and contain both decisions."""
    rows = batch.process_csv(source())
    summary = batch.summarize(rows)
    assert summary["processed"] == count
    assert summary["errors"] == 0
    assert summary["yes"] > 0
    assert summary["no"] > 0
    assert len({row["name"] for row in rows}) == count


def test_invalid_rows_do_not_prevent_other_predictions() -> None:
    """A mixed file keeps errors visible while scoring its valid customers."""
    text = make_csv(
        [
            {"name": "Valid", **DEFAULT_PROFILE},
            {"name": "Invalid", **DEFAULT_PROFILE, "age": "bad"},
        ]
    )
    rows = batch.process_csv(text)
    assert batch.summarize(rows)["processed"] == 1
    assert batch.summarize(rows)["errors"] == 1
    assert rows[1]["probability_yes"] is None
    assert rows[1]["age"] is None
    assert "Age must be a number" in rows[1]["error"]
    assert rows[1]["original"]["age"] == "bad"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "name,age\nA,40",
        ",".join(CSV_COLUMNS),
        batch.template_csv().replace(",", ";"),
        batch.template_csv().replace("name,", "Name,", 1),
        batch.template_csv() + '"unclosed',
    ],
)
def test_invalid_file_structure_is_rejected(text: str) -> None:
    """Empty, malformed, and mismatched files receive a file-level error."""
    with pytest.raises(ValidationError):
        batch.process_csv(text)


@pytest.mark.parametrize("suffix", ["\n", "Wrong,40\n", '"",40\n'])
def test_incomplete_data_rows_are_reported(suffix: str) -> None:
    """Blank or short rows are retained and counted as errors."""
    rows = batch.process_csv(batch.template_csv() + suffix)
    assert batch.summarize(rows)["errors"] == 1
    assert rows[-1]["prediction"] == "error"


def test_all_invalid_file_never_calls_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """An entirely invalid upload still produces a useful error report."""
    monkeypatch.setattr(api, "MODEL_PATH", None)
    rows = batch.process_csv(
        make_csv([{"name": "Invalid", **DEFAULT_PROFILE, "age": -1}])
    )
    assert batch.summarize(rows)["errors"] == 1


@pytest.mark.parametrize(
    "name,prediction,count",
    [
        ("CUSTOMER 2", "all", 1),
        ("", "yes", 1),
        ("sample", "no", 2),
        ("absent", "all", 0),
    ],
)
def test_customer_filters(name: str, prediction: str, count: int) -> None:
    """Search and decision filters combine without changing source row IDs."""
    rows = batch.process_csv(batch.template_csv())
    assert len(batch.filter_rows(rows, name, prediction)) == count


def test_details_follow_customer_after_sorting() -> None:
    """Opening a sorted result returns the original profile, not its row offset."""
    rows = batch.process_csv(batch.template_csv())
    ranked = sorted(rows, key=lambda row: row["probability_yes"], reverse=True)
    detail = batch.find_row(rows, ranked[0]["id"])
    assert detail["name"] == "Sample customer 2"
    assert detail["original"]["poutcome"] == "success"
    assert batch.find_row(rows, "missing") is None


def test_utf8_upload_accepts_bom_and_unicode_names() -> None:
    """UTF-8 spreadsheet exports retain international customer names."""
    text = make_csv([{"name": "José", **DEFAULT_PROFILE}])
    contents = (
        "data:text/csv;base64," + base64.b64encode(text.encode("utf-8-sig")).decode()
    )
    decoded = batch.decode_upload(contents, "customers.CSV")
    assert batch.process_csv(decoded)[0]["name"] == "José"


@pytest.mark.parametrize(
    "contents,filename",
    [
        ("invalid", "file.csv"),
        ("data:text/csv;base64,??", "file.csv"),
        ("data:text/csv;base64,/w==", "file.csv"),
        ("", "file.xlsx"),
        ("", None),
    ],
)
def test_invalid_upload_has_readable_error(contents: str, filename: str | None) -> None:
    """Unsupported uploads are rejected before parsing or model execution."""
    with pytest.raises(ValidationError):
        batch.decode_upload(contents, filename)


def test_upload_size_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Oversized uploads fail explicitly rather than hanging the dashboard."""
    monkeypatch.setattr(batch, "MAX_BYTES", 1)
    with pytest.raises(ValidationError, match="5 MB"):
        batch.decode_upload("data:text/csv;base64,YWJj", "file.csv")


def test_row_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exceeding the row budget rejects the entire file instead of truncating it."""
    monkeypatch.setattr(batch, "MAX_ROWS", 1)
    with pytest.raises(ValidationError, match="10,000"):
        batch.process_csv(batch.template_csv())
