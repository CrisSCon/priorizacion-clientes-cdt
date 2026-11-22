# Customer prioritization for term-deposit campaigns

Academic project using the [UCI Bank Marketing dataset](https://archive.ics.uci.edu/dataset/222/bank+marketing) to estimate subscription propensity and prioritize customer contact.

## Repository structure

| Path | Purpose |
| --- | --- |
| `notebooks/` | Exploration, feature engineering, model comparison, and MLflow experiments |
| `data/` | Source dataset tracked with DVC |
| `models/` | Trained models, inference artifacts, and experiment metadata |
| [`model_pkg/`](model_pkg/README.md) | XGBoost inference package and trained artifacts |
| [`api/`](api/README.md) | FastAPI prediction service and Docker configuration |
| `api/model_pkg/` | Built inference wheel |
| [`tablero/`](tablero/README.md) | Dash dashboard, assets, and dashboard Docker configuration |
| `common/` | Customer profile validation and prediction contract used by both services |
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

## Prediction API

The FastAPI service exposes health and batch prediction endpoints on port 8001. See the [API guide](api/README.md) for local and Docker commands, the request format, and tests.

## Dashboard environment

The dashboard sends predictions to the FastAPI service at `http://localhost:8001` by default.

Start the [prediction API](api/README.md) in a separate terminal. From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r tablero/requirements.txt
python -m tablero.app
```

Use a separate virtual environment from notebook development. Open http://127.0.0.1:8050.

## Deployment to AWS

Each image uses its service directory and `common/` as build contexts. Run these commands from the repository root with BuildKit enabled:

```bash
docker build --build-context common=./common -f api/Dockerfile -t cdt-prediction-api api
docker build --build-context common=./common -f tablero/Dockerfile -t cdt-dashboard tablero
```

Deploy the API and dashboard as separate services on ports `8001` and `8050`. Set `API_URL` on the dashboard service to the API's reachable hostname, without `http://` or a port. Set `API_PORT=8001` for a direct connection to the API. Allow the dashboard service to reach the API over the network.

See the [dashboard guide](tablero/README.md) for CSV input and a local Docker example.
