# CDT dashboard

A Dash/Plotly workspace for prioritizing potential term-deposit customers.
The dashboard uses the final XGBoost model through the shared inference pipeline in `src/inference.py`.

## Run

From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-deploy.txt
python -m tablero.app
```


Open **http://127.0.0.1:8050**. Stop the server with `Ctrl+C`.

## Structure

| Module | Responsibility |
| --- | --- |
| `app.py` | Dash factory, local CSV download route, localhost entry point |
| `ui.py`, `assets/` | Page layouts, presentation, responsive styles, modal behavior |
| `callbacks.py` | Dash event wiring and 400 ms debounce |
| `schema.py` | Source fields, defaults, shared validation |
|  `src/inference.py`, `models/` | Shared feature engineering and model inference |
| `api.py` | In-process `predict_one` / `predict_many`; no HTTP prediction API |
| `batch.py` | Strict upload parsing, row errors, summaries, filtering, stable lookup |
| `figures.py` | Probability histogram |
| `sample_customers.csv` | 120 fictional customers for the sample-data button |
