# CDT prediction API

FastAPI serves the trained CDT model from the committed wheel. The service validates raw profiles, calls the wheel for feature engineering and inference, and formats the prediction response.

## Run locally

From the repository root with a Python 3.12 virtual environment active:

```bash
python -m pip install --only-binary=:all: -r api/requirements.txt api/model_pkg/cdt_model_pkg-0.1.0-py3-none-any.whl
python -m uvicorn api.app.main:app --host 127.0.0.1 --port 8001
```

On Ubuntu install `libgomp1`. On macOS install `libomp` with Homebrew. Open the interactive docs at <http://127.0.0.1:8001/docs>.

## Run in Docker

From the repository root:

```bash
docker build -f api/Dockerfile -t cdt-prediction-api api
docker run --rm -p 127.0.0.1:8001:8001 cdt-prediction-api
```

The image installs the model wheel and runs Uvicorn as an unprivileged user.

## HTTP contract

- `GET /api/v1/health` reports the API name, API version, and installed model version. The model loads on the first prediction.
- `POST /api/v1/predict` accepts an `inputs` array of 1 to 10,000 profiles and an optional `include_rank` boolean. Submit the 11 fields shown below for each profile. Numeric fields accept numbers or numeric strings.
- `GET /api/v1/openapi.json` returns the OpenAPI document.

Example prediction request:

```json
{
  "inputs": [
    {
      "age": 40,
      "job": "management",
      "marital": "married",
      "education": "secondary",
      "default": "no",
      "balance": 1000,
      "housing": "no",
      "loan": "no",
      "pdays": -1,
      "previous": 0,
      "poutcome": "unknown"
    }
  ],
  "include_rank": false
}
```

A successful response contains the model package `version` and a `predictions` array in input order. Each prediction contains `probability_yes`, `probability_no`, `prediction` (`"yes"` or `"no"`), and `rank`. Ranks start at 1 for the highest probability in the submitted batch. Ties retain input order. Set `include_rank` to `false` for an unranked response with `rank: null`.

Invalid requests receive HTTP 422. A failed model load or prediction receives HTTP 503.

## Run the tests

From the repository root with Python 3.12 available:

```bash
python -m pip install "tox>=4,<5"
python -m tox -c api/tox.ini
```

The tests install and exercise the committed wheel in an isolated environment.
