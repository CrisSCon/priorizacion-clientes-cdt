"""Connect Dash interactions to the independent local inference services."""

from typing import Any

from dash import ALL, Dash, Input, Output, State, ctx, no_update
from dash.exceptions import PreventUpdate

from tablero import api, batch, ui
from tablero.figures import probability_distribution
from tablero.schema import DEFAULT_PROFILE, ValidationError


def register_callbacks(app: Dash) -> None:
    """Register navigation, debounced scoring, uploads, filters, and row details."""

    @app.callback(
        Output("home-page", "style"),
        Output("manual-page", "style"),
        Output("csv-page", "style"),
        Output("nav-home", "className"),
        Output("nav-manual", "className"),
        Output("nav-csv", "className"),
        Input("location", "pathname"),
    )
    def navigate(path: str | None) -> tuple[Any, ...]:
        """Show one route, keeping other page inputs mounted and intact."""
        route = path if path in ("/manual", "/csv") else "/"
        routes = ("/", "/manual", "/csv")
        return tuple(
            {} if route == item else {"display": "none"} for item in routes
        ) + tuple("active" if route == item else "" for item in routes)

    app.clientside_callback(
        """function(values, ids) {
            const state = window.cdtDebounce || (window.cdtDebounce = {});
            clearTimeout(state.timer);
            if (state.resolve) state.resolve(window.dash_clientside.no_update);
            return new Promise(resolve => {
                state.resolve = resolve;
                state.timer = setTimeout(() => {
                    const profile = {};
                    ids.forEach((id, index) => profile[id.key] = values[index]);
                    state.resolve = null;
                    resolve(profile);
                }, 400);
            });
        }""",
        Output("profile-values", "data"),
        Input({"type": "profile-field", "key": ALL}, "value"),
        State({"type": "profile-field", "key": ALL}, "id"),
    )

    @app.callback(Output("manual-result", "children"), Input("profile-values", "data"))
    def score_profile(profile: dict[str, Any] | None) -> list[Any]:
        """Replace the estimate on each settled edit, clearing it on invalid input."""
        try:
            return ui.prediction_card(api.predict_one(profile or DEFAULT_PROFILE))
        except (ValidationError, api.ModelUnavailableError) as exc:
            return ui.prediction_card(None, str(exc))

    @app.callback(
        Output({"type": "profile-field", "key": ALL}, "value"),
        Input("reset-profile", "n_clicks"),
        State({"type": "profile-field", "key": ALL}, "id"),
        prevent_initial_call=True,
    )
    def reset_profile(clicks: int, ids: list[dict[str, str]]) -> list[Any]:
        """Restore every visible and advanced predictor to its documented default."""
        return [DEFAULT_PROFILE[identifier["key"]] for identifier in ids]

    @app.callback(
        Output("batch-data", "data"),
        Output("upload-message", "children"),
        Output("upload-message", "className"),
        Input("csv-upload", "contents"),
        Input("sample-data", "n_clicks"),
        State("csv-upload", "filename"),
        prevent_initial_call=True,
    )
    def upload_csv(
        contents: str | None, clicks: int | None, filename: str | None
    ) -> tuple[Any, ...]:
        """Process a complete upload atomically and remove stale data on failure."""
        try:
            if ctx.triggered_id == "sample-data":
                text, label = batch.template_csv(), "Sample data"
            elif contents:
                text, label = batch.decode_upload(contents, filename), filename
            else:
                raise PreventUpdate
            rows = batch.process_csv(text)
            summary = batch.summarize(rows)
            message = (
                f"{label} · {summary['processed']:,} of {summary['total']:,} rows processed"
                f" · rows with errors: {summary['errors']:,}"
            )
            return (
                rows,
                message,
                "upload-message "
                + ("warning-message" if summary["errors"] else "success-message"),
            )
        except (ValidationError, api.ModelUnavailableError) as exc:
            return [], str(exc), "upload-message error-message"

    @app.callback(
        Output("batch-summary", "children"),
        Output("distribution", "figure"),
        Output("batch-results", "style"),
        Output("batch-empty", "style"),
        Input("batch-data", "data"),
    )
    def summarize_batch(rows: list[dict[str, Any]]) -> tuple[Any, ...]:
        """Keep summary statistics and the chart tied to the full uploaded list."""
        return (
            ui.summary_cards(batch.summarize(rows)),
            probability_distribution(rows),
            {} if rows else {"display": "none"},
            {"display": "none"} if rows else {},
        )

    @app.callback(
        Output("results-grid", "rowData"),
        Output("visible-count", "children"),
        Input("batch-data", "data"),
        Input("name-filter", "value"),
        Input("prediction-filter", "value"),
    )
    def filter_customers(
        rows: list[dict[str, Any]], name: str | None, prediction: str
    ) -> tuple[Any, str]:
        """Apply user-facing filters; AG Grid handles sorting and pagination."""
        filtered = batch.filter_rows(rows, name, prediction)
        return filtered, f"{len(filtered):,} of {len(rows):,} customers"

    @app.callback(
        Output("detail-content", "children"),
        Output("modal-event", "data"),
        Input("results-grid", "cellClicked"),
        Input("results-grid", "cellRendererData"),
        Input("batch-data", "data"),
        prevent_initial_call=True,
    )
    def show_customer(
        cell: dict[str, Any] | None,
        button: dict[str, Any] | None,
        rows: list[dict[str, Any]],
    ) -> tuple[Any, Any]:
        """Resolve the selected source ID even after table sorting or filtering."""
        if ctx.triggered_id == "batch-data":
            return [], {"open": False}
        event = (
            button if ctx.triggered[0]["prop_id"].endswith("cellRendererData") else cell
        )
        row = batch.find_row(rows, str((event or {}).get("rowId", "")))
        if row is None:
            return no_update, no_update
        return ui.row_details(row), {"open": True, "event": event}

    app.clientside_callback(
        """function(event) {
            const dialog = document.getElementById('details-dialog');
            if (!dialog || !event) return '';
            if (event.open) {
                if (!dialog.open) dialog.showModal();
                document.getElementById('close-details').focus();
            } else if (dialog.open) dialog.close();
            return '';
        }""",
        Output("modal-sync", "children"),
        Input("modal-event", "data"),
    )
