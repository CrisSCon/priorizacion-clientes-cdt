"""JSON contracts for the prediction API."""

from pydantic import BaseModel, ConfigDict, Field

from common.predictions import MAX_BATCH_SIZE, Prediction
from common.profiles import DEFAULT_PROFILE


type NumericInput = int | float | str


class ProfileInput(BaseModel):
    """The raw model inputs for one customer."""

    model_config = ConfigDict(extra="forbid", strict=True)

    age: NumericInput
    job: str
    marital: str
    education: str
    default: str
    balance: NumericInput
    housing: str
    loan: str
    pdays: NumericInput
    previous: NumericInput
    poutcome: str


class PredictionRequest(BaseModel):
    """Customer profiles to score together."""

    model_config = ConfigDict(extra="forbid", strict=True)

    inputs: list[ProfileInput] = Field(
        min_length=1,
        max_length=MAX_BATCH_SIZE,
        examples=[[DEFAULT_PROFILE]],
    )
    include_rank: bool = Field(default=True, description="Return ranks within this batch.")


class PredictionResponse(BaseModel):
    """Model version and one prediction per input profile, in input order."""

    version: str
    predictions: list[Prediction]


class HealthResponse(BaseModel):
    """API identity and installed model package version."""

    name: str
    api_version: str
    model_version: str
