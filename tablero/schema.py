"""Profile fields, defaults, and validation."""

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping


@dataclass(frozen=True)
class Field:
    """A profile field with defaults and validation limits."""

    key: str
    label: str
    default: str | int | float
    help: str
    choices: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    integer: bool = False
    primary: bool = False


FIELDS = (
    Field(
        "age",
        "Age",
        40,
        "Years · 18–120",
        minimum=18,
        maximum=120,
        integer=True,
        primary=True,
    ),
    Field(
        "job",
        "Occupation",
        "management",
        "Current occupation",
        (
            "admin.",
            "blue-collar",
            "entrepreneur",
            "housemaid",
            "management",
            "retired",
            "self-employed",
            "services",
            "student",
            "technician",
            "unemployed",
            "unknown",
        ),
    ),
    Field(
        "marital",
        "Marital status",
        "married",
        "Recorded marital status",
        ("divorced", "married", "single"),
    ),
    Field(
        "education",
        "Education",
        "secondary",
        "Highest recorded level",
        ("primary", "secondary", "tertiary", "unknown"),
    ),
    Field(
        "default", "Credit in default", "no", "Existing credit default", ("no", "yes")
    ),
    Field(
        "balance",
        "Average annual balance",
        1000,
        "EUR · use the original dataset currency",
        minimum=-1e12,
        maximum=1e12,
        primary=True,
    ),
    Field(
        "housing",
        "Housing loan",
        "no",
        "Has a housing loan",
        ("no", "yes"),
        primary=True,
    ),
    Field(
        "loan",
        "Personal loan",
        "no",
        "Has a personal loan",
        ("no", "yes"),
        primary=True,
    ),
    Field(
        "pdays",
        "Days since previous contact",
        -1,
        "Use −1 if never contacted",
        minimum=-1,
        maximum=1e6,
        integer=True,
        primary=True,
    ),
    Field(
        "previous",
        "Previous contacts",
        0,
        "Contacts before this campaign",
        minimum=0,
        maximum=1e6,
        integer=True,
        primary=True,
    ),
    Field(
        "poutcome",
        "Previous campaign outcome",
        "unknown",
        "Use unknown if no previous campaign",
        ("failure", "other", "success", "unknown"),
        primary=True,
    ),
)
FEATURE_KEYS = tuple(field.key for field in FIELDS)
CSV_COLUMNS = ("name", *FEATURE_KEYS)
DEFAULT_PROFILE = {field.key: field.default for field in FIELDS}


class ValidationError(ValueError):
    """Invalid profile or CSV input."""


def validate_profile(profile: Mapping[str, Any]) -> dict[str, str | float]:
    """Validate profile fields and convert numeric strings to numbers."""
    errors = []
    extra = set(profile) - set(FEATURE_KEYS)
    if extra:
        errors.append(f"Unexpected fields: {', '.join(sorted(extra))}")
    result: dict[str, str | float] = {}
    for field in FIELDS:
        value = profile.get(field.key)
        if value is None or isinstance(value, bool) or str(value).strip() == "":
            errors.append(f"{field.label} is required")
            continue
        if field.choices:
            if value not in field.choices:
                errors.append(f"{field.label}: use {', '.join(field.choices)}")
            else:
                result[field.key] = str(value)
            continue
        try:
            number = float(value)
        except (ValueError, TypeError, OverflowError):
            errors.append(f"{field.label} must be a number")
            continue
        if not isfinite(number):
            errors.append(f"{field.label} must be a finite number")
        elif field.integer and not number.is_integer():
            errors.append(f"{field.label} must be a whole number")
        elif (field.minimum is not None and number < field.minimum) or (
            field.maximum is not None and number > field.maximum
        ):
            errors.append(
                f"{field.label} must be between {field.minimum:g} and {field.maximum:g}"
            )
        else:
            result[field.key] = number
    if errors:
        raise ValidationError("; ".join(errors))
    return result
