# CDT dashboard

Dash/Plotly dashboard for manual customer predictions and CSV batch prioritization.

## Run locally

Start the [prediction API](../api/README.md) in a separate terminal. From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r tablero/requirements.txt
python -m tablero.app
```

Open http://127.0.0.1:8050. The dashboard uses `POST /api/v1/predict` for single and batch scoring.

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_URL` | `localhost` | API hostname |
| `API_PORT` | `8001` | API HTTP port |

The API applies the model's classification threshold, currently 20%. Update the dashboard chart marker if that threshold changes.

## Features and CSV format

- Manual form with all input fields, defaults, debounced updates, and probability indicators.
- Downloadable CSV template and a sample containing 120 fictional profiles.
- CSV upload with per-row validation errors, totals, yes/no counts, and a probability histogram.
- Name and prediction filters, sortable results, priority ranks, and a row-details modal.

Use the downloaded template without changing its headers:

```text
name,age,job,marital,education,default,balance,housing,loan,pdays,previous,poutcome
```

Uploads must be UTF-8 CSV (an optional BOM is accepted), no larger than 5 MiB and no more than 10,000 data rows. Header names and column order must match the template exactly. `common/profiles.py` defines allowed categories and numeric ranges. Invalid rows are shown with errors; valid rows are scored together. `name` is used for display, not as a model feature.

## Docker

Build the images with BuildKit and run the two containers on a local Docker network from the repository root:

```bash
docker build --build-context common=./common -f api/Dockerfile -t cdt-prediction-api api
docker build --build-context common=./common -f tablero/Dockerfile -t cdt-dashboard tablero
docker network create cdt-local
docker run --rm -d --name cdt-prediction-api --network cdt-local -p 127.0.0.1:8001:8001 cdt-prediction-api
docker run --rm -d --name cdt-dashboard --network cdt-local -e API_URL=cdt-prediction-api -e API_PORT=8001 -p 127.0.0.1:8050:8050 cdt-dashboard
```

Open the dashboard at <http://127.0.0.1:8050> and the API docs at <http://127.0.0.1:8001/docs>. Stop the containers with `docker stop cdt-dashboard cdt-prediction-api`.

In AWS, set the dashboard's `API_URL` to the API service hostname reachable from the dashboard, without a scheme or port, and set `API_PORT=8001` for a direct connection. The `localhost` default refers to the dashboard container itself.

The dashboard image builds from `tablero/` and `common/` and runs Gunicorn on port 8050 with one worker, four threads, and a 120-second timeout. It connects to the API over HTTP using `API_URL` and `API_PORT`.

The dashboard and API use `common/` for profile validation and the prediction result format.

## Tests

From the repository root with the dashboard dependencies installed:

```bash
python -B -m unittest discover -s tablero/tests
```

## Modules

| Module | Responsibility |
| --- | --- |
| `app.py` | Dash factory, CSV download route, localhost entry point |
| `wsgi.py` | Gunicorn entry point |
| `ui.py`, `assets/` | Layout, styles, and browser interactions |
| `callbacks.py` | Event wiring and 400 ms debounce |
| `common/profiles.py` | Profile fields and validation for the form and CSV |
| `api_connection.py` | HTTP client for the prediction API |
| `batch.py` | Upload parsing, row errors, summaries, and filtering |
| `figures.py` | Probability histogram |
| `sample_customers.csv` | Fictional sample profiles |
