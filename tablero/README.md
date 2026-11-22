# CDT dashboard

Dash/Plotly dashboard for manual customer predictions and CSV batch prioritization.

## Run locally

From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install ./model_pkg -r tablero/requirements.txt
python -m tablero.app
```

On macOS, install the XGBoost OpenMP prerequisite with `brew install libomp`. The Docker image installs the Linux equivalent.

Open http://127.0.0.1:8050. Stop the server with `Ctrl+C`. No environment variables or external services are required by the application.

The dashboard calls the installed [`model_pkg.inference`](../model_pkg/src/model_pkg/inference.py) module in the same Python process.

## Model

The XGBoost inference package bundles these files:

- `xgboost_final.ubj`
- `preprocessor_final.joblib`
- `inference_metadata.json`

Classification uses the metadata threshold, currently 20%. The chart also displays a 20% threshold marker; update it if the model threshold changes.

## Features and CSV format

- Manual form with all input fields, defaults, debounced updates, and probability indicators.
- Downloadable CSV template and a sample containing 120 fictional profiles.
- CSV upload with per-row validation errors, totals, yes/no counts, and a probability histogram.
- Name and prediction filters, sortable results, priority ranks, and a row-details modal.

Use the downloaded template without changing its headers:

```text
name,age,job,marital,education,default,balance,housing,loan,pdays,previous,poutcome
```

Uploads must be UTF-8 CSV (an optional BOM is accepted), no larger than 5 MiB and no more than 10,000 data rows. Header names and column order must match the template exactly. `schema.py` defines allowed categories and numeric ranges. Invalid rows are shown with errors; valid rows are scored together. `name` is used for display, not as a model feature.

## Docker

Build from the repository root so Docker can access the inference package and dashboard:

```bash
docker build -f tablero/Dockerfile -t cdt-dashboard .
docker run --rm -p 127.0.0.1:8050:8050 cdt-dashboard
```

`Dockerfile.dockerignore` is the Dockerfile-specific ignore file for this build. The image installs the inference package and dashboard dependencies. It runs `tablero.wsgi:server` with Gunicorn on port 8050, one worker, four threads, and a 120-second timeout.

## Modules

| Module | Responsibility |
| --- | --- |
| `app.py` | Dash factory, CSV download route, localhost entry point |
| `wsgi.py` | Gunicorn entry point |
| `ui.py`, `assets/` | Layout, styles, and browser interactions |
| `callbacks.py` | Event wiring and 400 ms debounce |
| `schema.py` | Fields, defaults, and validation |
| `api.py` | Dashboard adapter for local inference; preserves input order |
| `model_pkg.inference` | Feature engineering and XGBoost predictions |
| `batch.py` | Upload parsing, row errors, summaries, and filtering |
| `figures.py` | Probability histogram |
| `sample_customers.csv` | Fictional sample profiles |
