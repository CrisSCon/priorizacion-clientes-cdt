# Model inference

This package provides local Python inference. It does not expose HTTP endpoints and has no Docker configuration yet.

## Environment

From the repository root, with Python 3.12 and an active virtual environment:

```bash
python -m pip install -r api/requirements.txt
```

The requirements list is independent of the dashboard and notebook environments. XGBoost also requires an OpenMP runtime: `brew install libomp` on macOS, or `libgomp1` on Debian Linux.

## Artifacts

`inference.py` resolves these paths relative to the repository root:

- `models/xgboost_final.ubj`: final XGBoost classifier.
- `models/preprocessor_final.joblib`: fitted preprocessing pipeline.
- `models/inference_metadata.json`: input features, feature order, training balance median, and classification threshold.

Keep these three artifacts from the same training export. The current threshold is 0.20. No MLflow server is needed to run inference.

## Usage

```python
import pandas as pd

from api.inference import predict_dataframe

profiles = pd.read_csv("tablero/sample_customers.csv")
predictions = predict_dataframe(profiles)
```

Required columns: `age`, `job`, `marital`, `education`, `default`, `balance`, `housing`, `loan`, `pdays`, `previous`, and `poutcome`. An optional `name` column supplies identifiers; otherwise the input index is used.

`build_features` derives the model inputs. `load_artifacts` loads the classifier, fitted preprocessor, and metadata. `predict_dataframe` applies them and returns `name`, `probability`, `prediction` (0 or 1), and `rank`, sorted by descending probability. Ties retain input order.

The dashboard adds strict input validation and restores CSV input order through `tablero/api.py`. Callers using this package directly are responsible for input validation.
