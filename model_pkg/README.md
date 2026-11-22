# Model inference package

`cdt-model-pkg` provides local Python inference for CDT customer prioritization. It bundles the trained XGBoost classifier, fitted scikit-learn preprocessor, and inference metadata in `src/model_pkg/trained/`. The original inference artifacts live in `models/`. When updating the package, copy all three files from the same model export into `src/model_pkg/trained/`. The current classification threshold is 0.20.

## Build the wheel

From the repository root, in a Python 3.12 virtual environment:

```bash
python -m pip wheel --no-deps --wheel-dir api/model_pkg ./model_pkg
```

Update the package version in `pyproject.toml` when releasing changes to the inference code or trained artifacts. Update the wheel reference in `tablero/Dockerfile` and the install commands when publishing a new version.

## Install the wheel

```bash
python -m pip install --only-binary=:all: api/model_pkg/cdt_model_pkg-0.1.0-py3-none-any.whl
```

For development, use `python -m pip install -e ./model_pkg`.

On Ubuntu 24.04, install `python3.12-venv` and `libgomp1` before creating the virtual environment. For Docker, use a glibc-based image such as `python:3.12-slim` and install `libgomp1` with apt. XGBoost 3.2.0 publishes Linux wheels for x86-64 and ARM64 that require glibc 2.28 or newer ([PyPI release files](https://pypi.org/project/xgboost/3.2.0/#files)). On macOS, install the OpenMP runtime with `brew install libomp`.

## Use the installed package

```python
import pandas as pd

from model_pkg.inference import predict_dataframe

profiles = pd.read_csv("tablero/sample_customers.csv")
predictions = predict_dataframe(profiles)
```

Supply `age`, `job`, `marital`, `education`, `default`, `balance`, `housing`, `loan`, `pdays`, `previous`, and `poutcome`. An optional `name` column supplies identifiers. Otherwise, inference uses the input index.

`predict_dataframe` returns `name`, `probability`, `prediction` (0 or 1), and `rank`, sorted by descending probability. Ties retain input order. The dashboard additionally validates input and restores CSV row order through `tablero/api.py`.
