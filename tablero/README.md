# Local CDT dashboard

A Dash/Plotly workspace for prioritizing potential term-deposit customers.
The only model used is `models/gradient_boosting_final.pkl` from notebook 02.

## Run

From the repository root, with Python 3.13:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
dvc pull models/gradient_boosting_final.pkl.dvc
python -m tablero.app
```

Skip `dvc pull` if the actual model artifact is already present. The DVC remote may require
Google Drive authentication.

Open **http://127.0.0.1:8050**. Stop the server with `Ctrl+C`.

## Structure

| Module | Responsibility |
| --- | --- |
| `app.py` | Dash factory, local CSV download route, localhost entry point |
| `ui.py`, `assets/` | Page layouts, presentation, responsive styles, modal behavior |
| `callbacks.py` | Dash event wiring and 400 ms debounce |
| `schema.py` | Source fields, defaults, shared validation |
| `preprocessing.py`, `preprocessing.json` | Frozen notebook feature transformations |
| `api.py` | In-process `predict_one` / `predict_many`; no HTTP prediction API |
| `batch.py` | Strict upload parsing, row errors, summaries, filtering, stable lookup |
| `figures.py` | Probability histogram |
| `sample_customers.csv` | 120 fictional customers for the sample-data button |
| `tests/` | Parameterized validation, inference parity, CSV and callback tests |

## Verification

```bash
python -m pytest tablero/tests -q
```
