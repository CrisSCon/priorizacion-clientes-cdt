# Customer prioritization for term-deposit campaigns

Academic project using the [UCI Bank Marketing dataset](https://archive.ics.uci.edu/dataset/222/bank+marketing) to estimate subscription propensity and prioritize customer contact.

## Repository structure

| Path | Purpose |
| --- | --- |
| `notebooks/` | Exploration, feature engineering, model comparison, and MLflow experiments |
| `data/` | Source dataset tracked with DVC |
| `models/` | Trained models, inference artifacts, and experiment metadata |
| [`model_pkg/`](model_pkg/README.md) | XGBoost inference package and trained artifacts |
| `api/model_pkg/` | Built inference wheel |
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

The dashboard uses the installed `cdt-model-pkg` package for local XGBoost inference.

From the repository root, with Python 3.12. On macOS, install OpenMP first with `brew install libomp`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install api/model_pkg/cdt_model_pkg-0.1.0-py3-none-any.whl -r tablero/requirements.txt
python -m tablero.app
```

Use a separate virtual environment from notebook development. Open http://127.0.0.1:8050.

For the dashboard container, run from the repository root:

```bash
docker build -f tablero/Dockerfile -t cdt-dashboard .
docker run --rm -p 127.0.0.1:8050:8050 cdt-dashboard
```

See the [dashboard guide](tablero/README.md) for CSV input, model artifacts, and runtime details.
