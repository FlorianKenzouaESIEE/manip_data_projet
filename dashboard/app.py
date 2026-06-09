"""Instance Dash et configuration de l'application."""

from __future__ import annotations

import dash

from .callbacks import register_callbacks
from .layout import create_layout

_GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700;900"
    "&family=Barlow:wght@400;600&display=swap"
)


def create_app() -> dash.Dash:
    """Crée et configure l'application Dash."""
    app = dash.Dash(
        __name__,
        title="DashSport",
        external_stylesheets=[_GOOGLE_FONTS],
        suppress_callback_exceptions=True,
    )
    app.layout = create_layout()
    register_callbacks(app)
    return app
