"""Strict CSV ingestion, row-level validation, scoring, and result queries."""

import base64
import binascii
import csv
import io
from dataclasses import asdict
from typing import Any, Sequence

from tablero import api
from tablero.schema import (
    CSV_COLUMNS,
    DEFAULT_PROFILE,
    FEATURE_KEYS,
    ValidationError,
    validate_profile,
)

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10000


def template_csv() -> str:
    """Return a UTF-8 CSV template with three explicitly fictional profiles."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(
        [
            {"name": "Sample customer 1", **DEFAULT_PROFILE},
            {
                "name": "Sample customer 2",
                **DEFAULT_PROFILE,
                "age": 65,
                "job": "retired",
                "balance": 5000,
                "previous": 2,
                "pdays": 60,
                "poutcome": "success",
            },
            {
                "name": "Sample customer 3",
                **DEFAULT_PROFILE,
                "age": 28,
                "job": "technician",
                "housing": "yes",
            },
        ]
    )
    return stream.getvalue()


def decode_upload(contents: str, filename: str | None) -> str:
    """Decode a Dash CSV upload, enforcing file type, size, and UTF-8 encoding."""
    if not filename or not filename.lower().endswith(".csv"):
        raise ValidationError("Choose a .csv file using the downloaded template.")
    if len(contents) > MAX_BYTES * 4 // 3 + 1024:
        raise ValidationError("The CSV exceeds the 5 MB upload limit.")
    try:
        header, payload = contents.split(",", 1)
        if not header.endswith(";base64"):
            raise ValueError("Invalid upload encoding")
        raw = base64.b64decode(payload, validate=True)
        if len(raw) > MAX_BYTES:
            raise ValidationError("The CSV exceeds the 5 MB upload limit.")
        return raw.decode("utf-8-sig")
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        if isinstance(exc, ValidationError):
            raise
        raise ValidationError("Upload a valid UTF-8, comma-separated CSV.") from exc


def process_csv(text: str) -> list[dict[str, Any]]:
    """Score valid CSV rows and retain invalid rows with actionable errors.

    The header must match the template, including order and case. File-level
    structural errors reject the file. Value errors reject only their row.
    A stable source-row ID preserves detail selection after sorting/filtering.
    """
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff"), newline=""), strict=True)
    try:
        header = next(reader, [])
        if header != list(CSV_COLUMNS):
            raise ValidationError(
                "Column names and order must exactly match the template: "
                + ", ".join(CSV_COLUMNS)
            )
        results = []
        valid_profiles = []
        valid_indices = []
        for index, values in enumerate(reader):
            if index >= MAX_ROWS:
                raise ValidationError("Upload no more than 10,000 data rows.")
            original = dict(zip(CSV_COLUMNS, values))
            row = {
                "id": str(index + 1),
                "row": index + 2,
                "name": original.get("name", ""),
                "age": None,
                "job": original.get("job", ""),
                "balance": None,
                "prediction": "error",
                "probability_yes": None,
                "probability_no": None,
                "error": "",
                "original": original,
                "raw_values": values,
            }
            try:
                if len(values) != len(CSV_COLUMNS):
                    raise ValidationError(
                        f"Expected {len(CSV_COLUMNS)} values; found {len(values)}."
                    )
                if not row["name"].strip() or len(row["name"]) > 200:
                    raise ValidationError("Name must contain 1–200 characters.")
                profile = validate_profile({key: original[key] for key in FEATURE_KEYS})
                row.update({key: profile[key] for key in ("age", "job", "balance")})
                valid_profiles.append(profile)
                valid_indices.append(index)
            except ValidationError as exc:
                row["error"] = str(exc)
            results.append(row)
    except csv.Error as exc:
        raise ValidationError(
            "Malformed CSV quoting. Export the template as CSV again."
        ) from exc
    if not results:
        raise ValidationError("The CSV has a header but no customer rows.")
    for index, prediction in zip(valid_indices, api.predict_many(valid_profiles)):
        results[index].update(asdict(prediction))
    return results


def summarize(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count all uploaded rows, successful predictions, and row errors."""
    yes = sum(row["prediction"] == "yes" for row in rows)
    no = sum(row["prediction"] == "no" for row in rows)
    return {
        "total": len(rows),
        "processed": yes + no,
        "errors": len(rows) - yes - no,
        "yes": yes,
        "no": no,
    }


def filter_rows(
    rows: Sequence[dict[str, Any]],
    name: str | None,
    prediction: str,
) -> list[dict[str, Any]]:
    """Filter names case-insensitively and match the chosen prediction status."""
    query = (name or "").strip().casefold()
    return [
        row
        for row in rows
        if query in row["name"].casefold()
        and (prediction == "all" or row["prediction"] == prediction)
    ]


def find_row(rows: Sequence[dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    """Find a source row by stable ID independently of visible table order."""
    return next((row for row in rows if row["id"] == row_id), None)
