"""WSGI entry point for the CDT dashboard."""

from tablero.app import create_app

dash_app = create_app()
server = dash_app.server
