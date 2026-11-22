# Customer prioritization for term-deposit campaigns

Academic project using the [UCI Bank Marketing dataset](https://archive.ics.uci.edu/dataset/222/bank+marketing) to estimate subscription propensity and prioritize customer contact.

## Repository structure

| Path | Purpose |
| --- | --- |
| `notebooks/` | Exploration, feature engineering, model comparison, and MLflow experiments |
| `data/` | Source dataset tracked with DVC |
| `models/` | Trained models and inference artifacts |
| [`api/`](api/README.md) | Local XGBoost inference and feature engineering |
| [`tablero/`](tablero/README.md) | Dash dashboard, assets, and dashboard Docker configuration |
| `docs/`, `evidencias/` | Report figures and experiment evidence |
| `requirements.txt` | Notebook and model-development dependencies only |

## Notebook environment

From the repository root, with Python 3.13:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
dvc pull
jupyter notebook
```

Run `notebooks/01_eda_bank_marketing.ipynb` before `notebooks/02_modelado_baseline_reglog.ipynb`. Review notebook paths and MLflow configuration before running all cells.

The DVC remote uses Google Drive and may require access and authentication. If the source CSV is unavailable, notebook 01 can download UCI data and validate its size and MD5 against `data/bank-full.csv.dvc`. Exploration figures are exported to `docs/figuras/`. Call duration is not an input to the dashboard's pre-contact predictions.

## Dashboard environment

The dashboard uses `models/xgboost_final.ubj`, `models/preprocessor_final.joblib`, and `models/inference_metadata.json`. Earlier model files remain available for the modeling work but are not used by the dashboard.

From the repository root, with Python 3.12. On macOS, install OpenMP first with `brew install libomp`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r api/requirements.txt -r tablero/requirements.txt
python -m tablero.app
```

Use a separate virtual environment from notebook development. Open http://127.0.0.1:8050.

The two application requirements files are independent lists. The current dashboard calls `api` in the same Python process, so running it still requires both lists. A separate HTTP API and API Docker image are not implemented.

For the dashboard container, run from the repository root:

```bash
docker build -f tablero/Dockerfile -t cdt-dashboard .
docker run --rm -p 127.0.0.1:8050:8050 cdt-dashboard
```

See the [dashboard guide](tablero/README.md) for CSV input, model artifacts, and runtime details.
