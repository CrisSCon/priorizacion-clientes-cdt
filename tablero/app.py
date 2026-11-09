"""Run the dashboard with ``python -m tablero.app``."""

from pathlib import Path

from dash import Dash
from flask import Response

from tablero.batch import template_csv
from tablero.callbacks import register_callbacks
from tablero.ui import layout


def create_app() -> Dash:
    """Create the dashboard and CSV download route."""
    app = Dash(
        __name__,
        title="CDT · Customer prioritization",
        assets_folder=str(Path(__file__).with_name("assets")),
        update_title="Updating…",
    )
    app.server.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024
    app.layout = layout()
    register_callbacks(app)

    @app.server.get("/download/template.csv")
    def download_template() -> Response:
        """Download the CSV template."""
        return Response(
            template_csv(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="cdt_template.csv"'},
        )

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8050, debug=False)
