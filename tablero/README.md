# Local CDT dashboard

A Dash/Plotly workspace for prioritizing potential term-deposit customers.
The only model used is `models/gradient_boosting_final.pkl` from notebook 02.
All new application code, labels, and documentation are in English.

## Run

From the repository root, with Python 3.13:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
dvc pull models/gradient_boosting_final.pkl.dvc
python -m tablero.app
```

On Windows, activate with `.venv\Scripts\activate` instead. Skip `dvc pull`
if the actual model artifact is already present. The DVC remote may require
Google Drive authentication. A Git LFS pointer is not a usable pickle.

Open **http://127.0.0.1:8050**. Stop the server with `Ctrl+C`. The app binds
to localhost and does not require MLflow, training CSVs, or a remote API.
Keep scikit-learn at **1.9.1**, the version recorded with the trained artifact.

## Workflows

- **Overview:** choose a workflow or download the sample CSV.
- **Manual prediction:** all eleven source predictors are visible in the form.
  Changes settle for 400 ms before scoring. Reset restores all eleven defaults.
  The probability card stays visible while scrolling, including on narrow screens.
  Invalid values clear the estimate and display the required correction.
  An inline spinner indicates updates while the previous estimate stays visible
  and the form remains editable.
- **CSV predictions:** upload up to 5 MB / 10,000 data rows, or load `sample_customers.csv`, a list of 120 fictional
  customers. An inline spinner indicates CSV processing. Search by name, filter yes/no/errors, sort column headings,
  and open any row or its View button for full details. Escape or the close button
  dismisses the modal. Stable source IDs keep details correct after sorting.

The decision is **yes when P(yes) >= 0.5**, otherwise **no**. P(no) is 1 − P(yes).
The table initially ranks customers by descending P(yes). Summary cards count
all uploaded rows, successfully processed rows, errors, yes, and no. The Plotly
histogram uses fixed 10-percentage-point bins and a 50% marker. The chart and
summary always describe the complete upload; the customer count beside the
table describes the current filter. Invalid rows never receive a prediction.

Uploads and predictions are held in process/browser memory, not written to
disk or sent to an external service. Navigation preserves current state;
refreshing the page clears it. A rejected replacement file clears prior results.
The app loads its scripts, styles, fonts, and model locally at runtime.

## CSV contract

Download the template from either the overview or CSV page. Use UTF-8 (with or
without BOM), commas, and these exact case-sensitive headers in this order:

```csv
name,age,job,marital,education,default,balance,housing,loan,pdays,previous,poutcome
```

All fields are required. Quoted names containing commas are supported. Unknown
categories must use the literal `unknown` where that category is available.
Blank values are errors. Duplicate names are allowed and kept as separate rows.
Extra/missing/reordered columns reject the file. Invalid values or incorrect
field counts are reported per row; valid rows continue to be scored.

| Column | Values | Manual default |
| --- | --- | --- |
| `name` | 1–200 characters; display only, never a predictor | CSV only |
| `age` | Whole years, 18–120 | 40 |
| `job` | admin., blue-collar, entrepreneur, housemaid, management, retired, self-employed, services, student, technician, unemployed, unknown | management |
| `marital` | divorced, married, single | married |
| `education` | primary, secondary, tertiary, unknown | secondary |
| `default` | no, yes | no |
| `balance` | Finite EUR amount, −1e12 to 1e12; negative balances allowed | 1000 |
| `housing` | no, yes | no |
| `loan` | no, yes | no |
| `pdays` | Whole days, −1 to 1,000,000; −1 means never contacted | −1 |
| `previous` | Whole contact count, 0 to 1,000,000 | 0 |
| `poutcome` | failure, other, success, unknown | unknown |

Numeric limits are application validation bounds, not evidence of model
reliability over those ranges. Enter a coherent campaign history: for someone
never contacted, normally use `pdays=-1`, `previous=0`, and `poutcome=unknown`.
Fields can be edited independently for scenario exploration. Category values
must match exactly; the app does not silently normalize or impute invalid input.

## Model and preprocessing provenance

The project uses UCI Bank Marketing, historical direct marketing campaigns at a
Portuguese bank. It estimates propensity to subscribe to a term deposit comparable
to a CDT, supporting contact prioritization under limited commercial capacity.
It does not guarantee a subscription or replace the team's judgment. Predictions
describe model associations; changing a field is not evidence of a causal effect.

Notebook 01, cell 33, engineers and encodes the data. Notebook 02 trains the final
Gradient Boosting classifier on the resulting 94 columns. Its saved pickle does
**not** contain the preprocessor. This dashboard reproduces the transformation
using eleven source predictors and the original one-hot feature order:

- `preprocessing.json` freezes the exact 94 names and training-only medians.
- The balance median is **451.0**, recovered from `X_train_final.csv`.
- Never-contacted recency is imputed as **195.0** days and its log as
  **5.278114659230517**, recovered from the training export. The corresponding
  category remains `missing` and contact flags remain false, as in notebook 01.
- The model's DVC MD5 at implementation is `5982cc4f662b01608838700d0d7f7553`.
- Duration, campaign, contact channel, and calendar variables were excluded by
  the notebook's availability controls and are not dashboard parameters.
- All derived flags, bands, logs, and one-hot columns are computed from source
  values; users edit the source fields instead of contradictory derived flags.

The loader checks model type, feature order, classes, and scikit-learn version.
Only this repository-owned pickle path is loaded; uploaded files are CSV only.
If the model is retrained, regenerate/revalidate the preprocessing contract and
fixtures before replacing it. No training or fitting happens at app startup.

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

The UI never opens the pickle or implements feature engineering. A future HTTP
API can call the functions in `api.py`; no API server is implemented in this delivery.

## Verification

```bash
python -m pytest tablero/tests -q
```

Tests include threshold boundaries, category/numeric validation, frozen missing
recency, CSV decoding and size limits, partial failures, filters, stable detail
selection, downloads, Dash callback requests, and histogram bin semantics.
Twelve public-data golden profiles check all 94 features against the notebook's
export. When `notebooks/data/processed/` is available, an additional test compares
all **9,043** held-out rows and probabilities to the original `X_test_final.csv`.
That full-partition check is skipped if optional notebook exports are absent.

Browser checks should cover template download/upload, a mixed valid/invalid CSV,
manual edits and reset, all eleven fields, sticky estimates, loading indicators, filters, sorting,
row details, and a rejected replacement upload. Recheck both wide and narrow
layouts after changing styles. The app uses Dash AG Grid's current theme API,
as described in its [migration documentation](https://dash.plotly.com/dash-ag-grid/migration-guide).
