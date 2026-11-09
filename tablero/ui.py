"""Dashboard layouts and components."""

import json
from typing import Any

import dash_ag_grid as dag
from dash import dcc, html

from tablero.api import Prediction
from tablero.figures import probability_distribution
from tablero.schema import FIELDS, Field


def loading_status(label: str) -> html.Div:
    """Show a nonblocking loading indicator."""
    return html.Div(
        [html.Span(className="status-spinner", **{"aria-hidden": "true"}), label],
        className="loading-status",
        role="status",
        **{"aria-live": "polite"},
    )


def field_control(field: Field) -> html.Div:
    """Render a field with its default value and help text."""
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
    """Show prediction probabilities or an input error."""
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
    ]


def home_page() -> html.Section:
    """Build the workflow selection page."""
    return html.Section(
        [
            html.H1("Customer prioritization"),
            html.P(
                "Upload a CSV or enter a customer profile.",
                className="page-intro",
            ),
            html.Div(
                [
                    dcc.Link(
                        [
                            html.Div("01 / CUSTOMER LIST", className="eyebrow"),
                            html.Div("↥", className="option-icon"),
                            html.H2("Upload a CSV"),
                            html.P("View predictions for multiple customers."),
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
                            html.H2("Manual prediction"),
                            html.P("Enter customer values and view the probability."),
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
                            html.Strong("CSV template"),
                            html.P("Required columns and example rows."),
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
        ],
        id="home-page",
    )


def manual_page() -> html.Section:
    """Show all profile fields and the prediction."""
    primary_order = (
        "poutcome",
        "previous",
        "pdays",
        "age",
        "balance",
        "housing",
        "loan",
        "job",
        "marital",
        "education",
        "default",
    )
    by_key = {field.key: field for field in FIELDS}
    return html.Section(
        [
            html.Div("SINGLE PROFILE", className="eyebrow"),
            html.H1("Manual prediction"),
            html.P(
                "Enter customer values. The prediction updates automatically.",
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
                        ],
                        className="panel profile-panel",
                    ),
                    html.Aside(
                        [
                            dcc.Loading(
                                [
                                    html.Div(className="loading-space"),
                                    dcc.Store(id="profile-values"),
                                    html.Div(
                                        id="manual-result", **{"aria-live": "polite"}
                                    ),
                                ],
                                id="manual-loading",
                                custom_spinner=loading_status("Updating…"),
                                delay_show=0,
                                delay_hide=150,
                                target_components={
                                    "profile-values": "data",
                                    "manual-result": "children",
                                },
                                parent_className="prediction-loading",
                                overlay_style={"visibility": "visible"},
                                show_initially=False,
                            ),
                        ],
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
    """Build the sortable customer table."""
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
    """Build the CSV upload and results page."""
    return html.Section(
        [
            html.Div("CUSTOMER LIST", className="eyebrow"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H1("CSV predictions"),
                            html.P(
                                "Upload a CSV to view customer predictions.",
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
                [
                    html.Div(className="loading-space"),
                    dcc.Store(id="batch-data", data=[]),
                ],
                id="batch-loading",
                custom_spinner=loading_status("Processing CSV…"),
                target_components={"batch-data": "data"},
                delay_show=0,
                delay_hide=150,
                parent_className="batch-progress",
                show_initially=False,
            ),
            html.Div(id="upload-message", role="status", className="upload-message"),
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
    """Show row, prediction, and error counts."""
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
    """Show a row, its prediction, and any errors."""
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
    """Build the dashboard while preserving state between pages."""
    return html.Div(
        [
            dcc.Location(id="location", refresh=False),
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
                    ],
                    className="header-inner",
                )
            ),
            html.Main([home_page(), manual_page(), csv_page()], id="main-content"),
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
