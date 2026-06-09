"""Callbacks Dash : interactivité entre les composants du dashboard."""

from __future__ import annotations

from typing import Any

import dash
from dash import Input, Output

from .components.charts import make_scatter_figure
from .data import load_activities


def register_callbacks(app: dash.Dash) -> None:
    """Enregistre tous les callbacks de l'application.

    Args:
        app: Instance Dash configurée avec le layout.
    """

    # ── Étape 14 : mise à jour du scatter croisé via les dropdowns ────────────

    @app.callback(
        Output("scatter-cross", "figure"),
        [Input("scatter-x", "value"), Input("scatter-y", "value")],
    )
    def update_scatter(x_col: str, y_col: str) -> Any:
        """Régénère le scatter plot quand l'utilisateur change un axe."""
        return make_scatter_figure(load_activities(), x_col=x_col, y_col=y_col)
