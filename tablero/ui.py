"""Dash layouts and presentational components, independent of inference."""

import json
from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from tablero.api import Prediction
from tablero.figures import probability_distribution
from tablero.schema import FIELDS, Field

DISCLAIMER = (
    "Estimated propensity to subscribe to a term deposit comparable to a CDT. "
    "A prediction does not guarantee a subscription or replace commercial judgment."
)


def field_control(field: Field) -> html.Div:
    """Render a labeled source predictor with an explicit default and help text."""
    identifier = {"type": "profile-field", "key": field.key}
    if field.choices:
        control = dcc.Dropdown(
            id=identifier,
            options=[
                {"label": option.replace("_", " ").capitalize(), "value": option}
                for option in field.choices
            ],
            value=field.default,
            clearable=False,
            searchable=False,
        )
    else:
        control = dcc.Input(
            id=identifier,
            value=field.default,
            type="number",
            debounce=False,
            min=field.minimum,
            max=field.maximum,
            step=1 if field.integer else "any",
            className="number-input",
        )
    return html.Div(
        [
            html.Div(field.label, id=f"label-{field.key}", className="field-label")
            if field.choices
            else html.Label(
                field.label,
                id=f"label-{field.key}",
                htmlFor=json.dumps(identifier, sort_keys=True, separators=(",", ":")),
            ),
            control,
            html.Small(field.help, className="field-help"),
        ],
        className="field",
        role="group",
        **{"aria-labelledby": f"label-{field.key}"},
    )


def prediction_card(result: Prediction | None, error: str = "") -> list[Any]:
    """Render a complementary probability display or clear invalid-input state."""
    if result is None:
        return [
            html.Div("PREDICTION", className="eyebrow"),
            html.H2("Check the profile"),
            html.P(error, className="error-text"),
        ]
    yes = result.probability_yes * 100
    no = result.probability_no * 100
    return [
        html.Div("SUBSCRIPTION ESTIMATE", className="eyebrow"),
        html.Div(
            [
                html.Span(f"{yes:.1f}", className="probability-number"),
                html.Span("%", className="percent-sign"),
            ],
            className="big-probability",
        ),
        html.P("Probability of yes", className="muted"),
        html.Span(
            f"Predicted {result.prediction}", className=f"decision {result.prediction}"
        ),
        html.Div(
            [
                html.Div(style={"width": f"{yes}%"}, className="bar-yes"),
                html.Div(style={"width": f"{no}%"}, className="bar-no"),
                html.Div(className="cutoff-marker"),
            ],
            className="probability-track",
        ),
        html.Div(
            [
                html.Span(f"Yes {yes:.1f}%", className="yes-text"),
                html.Span(f"No {no:.1f}%", className="no-text"),
            ],
            className="probability-labels",
        ),
        html.Div("Yes at 50% or above", className="cutoff-note"),
        html.Hr(),
        html.P("Updates as you change the profile.", className="small"),
        html.P(DISCLAIMER, className="small muted"),
    ]


def home_page() -> html.Section:
    """Build the landing page with two equal-access prediction workflows."""
    return html.Section(
        [
            html.Div("CONTACT PLANNING", className="eyebrow"),
            html.H1("Customer prioritization"),
            html.P(
                "Estimate subscription propensity and review who to contact next.",
                className="page-intro",
            ),
            html.Div(
                [
                    dcc.Link(
                        [
                            html.Div("01 / CUSTOMER LIST", className="eyebrow"),
                            html.Div("↥", className="option-icon"),
                            html.H2("Upload a CSV"),
                            html.P(
                                "Score a list, compare probabilities, and inspect each customer."
                            ),
                            html.Div(
                                ["Open batch predictions", html.Span("↗")],
                                className="card-action",
                            ),
                        ],
                        href="/csv",
                        className="option-card primary-option",
                    ),
                    dcc.Link(
                        [
                            html.Div("02 / SINGLE PROFILE", className="eyebrow"),
                            html.Div("⇄", className="option-icon"),
                            html.H2("Explore one customer"),
                            html.P(
                                "Start with a sample profile and see how changes affect its estimate."
                            ),
                            html.Div(
                                ["Open manual prediction", html.Span("↗")],
                                className="card-action",
                            ),
                        ],
                        href="/manual",
                        className="option-card secondary-option",
                    ),
                ],
                className="workflow-grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Strong("Start with the right format"),
                            html.P(
                                "A CSV template with three fictional profiles and all required columns."
                            ),
                        ]
                    ),
                    html.A(
                        "↓ Download template",
                        href="/download/template.csv",
                        className="button secondary",
                    ),
                ],
                className="template-strip",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div("MODEL", className="eyebrow"),
                            html.Strong("Gradient Boosting · Final"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("DATA SOURCE", className="eyebrow"),
                            html.Strong("UCI Bank Marketing"),
                        ]
                    ),
                    html.Div(
                        [
                            html.Div("DECISION THRESHOLD", className="eyebrow"),
                            html.Strong("50% subscription probability"),
                        ]
                    ),
                ],
                className="model-facts",
            ),
            html.P(
                "Based on historical direct marketing campaigns at a Portuguese bank. "
                + DISCLAIMER,
                className="context-note",
            ),
        ],
        id="home-page",
    )


def manual_page() -> html.Section:
    """Build the editable form with advanced inputs and a persistent estimate."""
    primary_order = (
        "poutcome",
        "previous",
        "pdays",
        "age",
        "balance",
        "housing",
        "loan",
    )
    by_key = {field.key: field for field in FIELDS}
    return html.Section(
        [
            html.Div("SINGLE PROFILE", className="eyebrow"),
            html.H1("Manual prediction"),
            html.P(
                "Adjust the customer profile to explore the subscription estimate.",
                className="page-intro",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H2("Customer profile"),
                                            html.P(
                                                "Most influential inputs are shown first.",
                                                className="muted small",
                                            ),
                                        ]
                                    ),
                                    html.Button(
                                        "Reset defaults",
                                        id="reset-profile",
                                        className="button secondary",
                                    ),
                                ],
                                className="section-heading",
                            ),
                            html.Div(
                                [field_control(by_key[key]) for key in primary_order],
                                className="form-grid",
                            ),
                            html.Details(
                                [
                                    html.Summary(
                                        "Additional profile details · 4 fields"
                                    ),
                                    html.Div(
                                        [
                                            field_control(field)
                                            for field in FIELDS
                                            if not field.primary
                                        ],
                                        className="form-grid advanced-fields",
                                    ),
                                ],
                                className="advanced",
                            ),
                        ],
                        className="panel profile-panel",
                    ),
                    html.Aside(
                        dcc.Loading(
                            html.Div(id="manual-result", **{"aria-live": "polite"}),
                            type="circle",
                            color="#103e38",
                            delay_show=250,
                        ),
                        className="panel prediction-panel",
                    ),
                ],
                className="manual-grid",
            ),
        ],
        id="manual-page",
        style={"display": "none"},
    )


def results_grid() -> dag.AgGrid:
    """Build a sortable, paginated customer table with accessible detail buttons."""
    return dag.AgGrid(
        id="results-grid",
        rowData=[],
        getRowId="params.data.id",
        columnDefs=[
            {"field": "name", "headerName": "Customer", "minWidth": 190, "flex": 1.5},
            {
                "field": "age",
                "headerName": "Age",
                "width": 85,
                "flex": 0,
                "cellDataType": "number",
                "valueFormatter": {
                    "function": "params.value == null ? '—' : params.value"
                },
            },
            {"field": "job", "headerName": "Occupation", "minWidth": 140},
            {
                "field": "balance",
                "headerName": "Balance · EUR",
                "minWidth": 145,
                "cellDataType": "number",
                "valueFormatter": {
                    "function": "params.value == null ? '—' : params.value"
                },
            },
            {
                "field": "prediction",
                "headerName": "Prediction",
                "minWidth": 125,
                "cellClassRules": {
                    "cell-yes": {"function": "params.value === 'yes'"},
                    "cell-no": {"function": "params.value === 'no'"},
                    "cell-error": {"function": "params.value === 'error'"},
                },
            },
            {
                "field": "probability_yes",
                "headerName": "P(yes)",
                "minWidth": 130,
                "cellDataType": "number",
                "sort": "desc",
                "valueFormatter": {
                    "function": "params.value == null ? '—' : (params.value * 100).toFixed(1) + '%'"
                },
            },
            {
                "headerName": "Details",
                "field": "id",
                "width": 100,
                "flex": 0,
                "sortable": False,
                "cellRenderer": "DetailsButton",
            },
        ],
        defaultColDef={"sortable": True, "resizable": True, "flex": 1},
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 10,
            "paginationPageSizeSelector": [10, 25, 50],
            "rowHeight": 54,
            "headerHeight": 46,
            "localeText": {"noRowsToShow": "No customers match these filters."},
            "rowSelection": {"mode": "singleRow", "checkboxes": False},
            "theme": {
                "function": "themeQuartz.withParams({accentColor: '#103e38', "
                "headerBackgroundColor: '#f4f7f2', foregroundColor: '#294239', "
                "borderColor: '#e1e7e0', fontFamily: 'Arial, sans-serif', fontSize: 12})"
            },
        },
        className="customer-grid",
        style={"height": "440px"},
    )


def csv_page() -> html.Section:
    """Build the upload, summary, chart, and searchable customer results view."""
    return html.Section(
        [
            html.Div("CUSTOMER LIST", className="eyebrow"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("CSV predictions"),
                            html.P(
                                "Upload a customer list to compare subscription estimates.",
                                className="page-intro",
                            ),
                        ]
                    ),
                    html.A(
                        "↓ Download template",
                        href="/download/template.csv",
                        className="button secondary",
                    ),
                ],
                className="page-heading",
            ),
            html.Div(
                [
                    dcc.Upload(
                        id="csv-upload",
                        accept=".csv",
                        multiple=False,
                        children=html.Div(
                            [
                                html.Span("↥", className="upload-icon"),
                                html.Div(
                                    [
                                        html.Strong("Drop your CSV here"),
                                        html.P(
                                            "or click to choose a file · UTF-8 · up to 5 MB / 10,000 rows"
                                        ),
                                    ]
                                ),
                                html.Button(
                                    "Choose file",
                                    className="button primary",
                                ),
                            ],
                            className="upload-content",
                        ),
                        className="upload-zone",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Use the template’s exact column names and order."
                            ),
                            html.Button(
                                "Try sample data",
                                id="sample-data",
                                className="text-button",
                            ),
                        ],
                        className="upload-help",
                    ),
                    html.Details(
                        [
                            html.Summary("CSV format and accepted values"),
                            html.P(
                                "Include name (1–200 characters) followed by the fields below. "
                                "All values are required; categories are lowercase. Name is only a label and is not used by the model. "
                                "Duration, campaign, channel, and contact date are excluded from this model."
                            ),
                            html.Table(
                                [
                                    html.Thead(
                                        html.Tr(
                                            [
                                                html.Th("Column"),
                                                html.Th("Accepted values"),
                                            ]
                                        )
                                    ),
                                    html.Tbody(
                                        [
                                            html.Tr(
                                                [
                                                    html.Td(html.Code(field.key)),
                                                    html.Td(
                                                        ", ".join(field.choices)
                                                        if field.choices
                                                        else f"{field.minimum:g} to {field.maximum:g}"
                                                        + (
                                                            " · whole number"
                                                            if field.integer
                                                            else ""
                                                        )
                                                        + " · "
                                                        + field.help
                                                    ),
                                                ]
                                            )
                                            for field in FIELDS
                                        ]
                                    ),
                                ],
                                className="schema-table",
                            ),
                        ],
                        className="format-help",
                    ),
                ],
                className="panel upload-panel",
            ),
            dcc.Loading(
                html.Div(
                    id="upload-message", role="status", className="upload-message"
                ),
                type="circle",
                color="#103e38",
            ),
            html.Div(
                [
                    html.Div(id="batch-summary", className="stats-grid"),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H2("Probability distribution"),
                                    html.P(
                                        "All valid rows · errors excluded",
                                        className="muted small",
                                    ),
                                ],
                                className="chart-heading",
                            ),
                            dcc.Graph(
                                id="distribution",
                                figure=probability_distribution([]),
                                style={"height": "250px"},
                                config={"displayModeBar": False, "responsive": True},
                            ),
                        ],
                        className="panel chart-panel",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H2("Customers"),
                                            html.P(
                                                "Select a row to inspect its full profile. Click a column heading to sort.",
                                                className="muted small",
                                            ),
                                        ]
                                    ),
                                    html.Span(
                                        id="visible-count", className="muted small"
                                    ),
                                ],
                                className="section-heading",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Label(
                                                "Search by name", htmlFor="name-filter"
                                            ),
                                            dcc.Input(
                                                id="name-filter",
                                                type="search",
                                                placeholder="Search customers…",
                                                debounce=0.3,
                                            ),
                                        ],
                                        className="search-field",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                "Prediction",
                                                id="prediction-filter-label",
                                                className="field-label",
                                            ),
                                            dcc.Dropdown(
                                                id="prediction-filter",
                                                value="all",
                                                clearable=False,
                                                searchable=False,
                                                options=[
                                                    {
                                                        "label": "All predictions",
                                                        "value": "all",
                                                    },
                                                    {
                                                        "label": "Yes · 50% or above",
                                                        "value": "yes",
                                                    },
                                                    {
                                                        "label": "No · below 50%",
                                                        "value": "no",
                                                    },
                                                    {
                                                        "label": "Rows with errors",
                                                        "value": "error",
                                                    },
                                                ],
                                            ),
                                        ],
                                        className="decision-filter",
                                        role="group",
                                        **{
                                            "aria-labelledby": "prediction-filter-label"
                                        },
                                    ),
                                ],
                                className="table-filters",
                            ),
                            results_grid(),
                        ],
                        className="panel table-panel",
                    ),
                ],
                id="batch-results",
                style={"display": "none"},
            ),
            html.Div(
                [
                    html.Div("No list uploaded yet", className="empty-title"),
                    html.P(
                        "Choose a CSV or try the sample data to see predictions here."
                    ),
                ],
                id="batch-empty",
                className="empty-state",
            ),
        ],
        id="csv-page",
        style={"display": "none"},
    )


def summary_cards(summary: dict[str, int]) -> list[html.Div]:
    """Present processed and rejected row counts separately from decisions."""
    return [
        html.Div(
            [
                html.Span(label, className="stat-label"),
                html.Strong(f"{summary[key]:,}", className=f"stat-value {tone}"),
            ],
            className="panel stat-card",
        )
        for key, label, tone in [
            ("total", "Total rows", ""),
            ("processed", "Processed", ""),
            ("errors", "Rows with errors", "error-text"),
            ("yes", "Predicted yes", "yes-text"),
            ("no", "Predicted no", "no-text"),
        ]
    ]


def row_details(row: dict[str, Any]) -> list[Any]:
    """Display every original CSV value plus the result and any validation error."""
    probability = row["probability_yes"]
    return [
        html.Div("CUSTOMER DETAILS", className="eyebrow"),
        html.H2(row["name"] or "Unnamed customer", id="detail-title"),
        html.P(f"CSV row {row['row']}", className="muted small"),
        html.Div(
            [
                html.Span(
                    f"Predicted {row['prediction']}"
                    if not row["error"]
                    else "Row error",
                    className=f"decision {row['prediction']}",
                ),
                html.Strong(
                    f"{probability:.1%} probability of yes"
                    if probability is not None
                    else "No prediction"
                ),
            ],
            className="detail-result",
        ),
        html.P(row["error"], className="error-text", role="alert")
        if row["error"]
        else None,
        html.Dl(
            [
                html.Div([html.Dt(key), html.Dd(str(value) or "(empty)")])
                for key, value in row["original"].items()
            ],
            className="detail-list",
        ),
        html.Details([html.Summary("Raw CSV values"), html.Pre(str(row["raw_values"]))])
        if row["error"]
        else None,
    ]


def layout() -> html.Div:
    """Compose persistent pages so navigation preserves profile and upload state."""
    return html.Div(
        [
            dcc.Location(id="location", refresh=False),
            dcc.Store(id="profile-values"),
            dcc.Store(id="batch-data", data=[]),
            dcc.Store(id="modal-event"),
            html.Div(id="modal-sync", hidden=True),
            html.A("Skip to content", href="#main-content", className="skip-link"),
            html.Header(
                html.Div(
                    [
                        dcc.Link(
                            [
                                html.Span("C", className="brand-mark"),
                                html.Span(
                                    [html.Strong("CDT"), html.Small("Contact planning")]
                                ),
                            ],
                            href="/",
                            className="brand",
                        ),
                        html.Nav(
                            [
                                dcc.Link("Overview", href="/", id="nav-home"),
                                dcc.Link("CSV predictions", href="/csv", id="nav-csv"),
                                dcc.Link(
                                    "Manual prediction", href="/manual", id="nav-manual"
                                ),
                            ],
                            **{"aria-label": "Main navigation"},
                        ),
                        html.Span(
                            [html.Span(className="status-dot"), "Local workspace"],
                            className="local-badge",
                        ),
                    ],
                    className="header-inner",
                )
            ),
            html.Main([home_page(), manual_page(), csv_page()], id="main-content"),
            html.Footer(
                [
                    html.Span("CDT / Customer prioritization"),
                    html.Span("Gradient Boosting · 50% decision threshold"),
                ]
            ),
            html.Dialog(
                [
                    html.Button(
                        "×",
                        id="close-details",
                        className="close-button",
                        **{"aria-label": "Close customer details"},
                    ),
                    html.Div(id="detail-content"),
                ],
                id="details-dialog",
                **{"aria-labelledby": "detail-title"},
            ),
        ]
    )
