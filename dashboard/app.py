"""Instance Dash et configuration de l'application."""

from __future__ import annotations

import dash

from .layout import create_layout


def create_app() -> dash.Dash:
    """Crée et configure l'application Dash."""
    app = dash.Dash(__name__, title="DashSport")
    app.layout = create_layout()
    return app
