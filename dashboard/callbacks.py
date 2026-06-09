"""Callbacks Dash : interactivité entre les composants du dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import dash
from dash import Input, Output

from .components.charts import make_detail_figure, make_scatter_figure
from .data import load_activities, load_activity_track


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

    # ── Étape 15 : détail seconde par seconde au clic sur un point ────────────

    @app.callback(
        Output("detail-graph", "figure"),
        Output("detail-section", "style"),
        Input("scatter-cross", "clickData"),
        prevent_initial_call=True,
    )
    def show_activity_detail(
        click_data: dict[str, Any] | None,
    ) -> tuple[Any, dict[str, str]]:
        """Affiche le détail d'une activité quand l'utilisateur clique sur un point."""
        hidden: dict[str, str] = {"display": "none"}
        visible: dict[str, str] = {"display": "block", "padding": "1.5rem 2rem"}

        if not click_data:
            return make_detail_figure(pd.DataFrame()), hidden

        point = click_data["points"][0]
        custom = point.get("customdata")
        if not custom:
            return make_detail_figure(pd.DataFrame()), hidden

        activity_id = int(custom[0])

        activities = load_activities()
        name = ""
        if not activities.empty:
            match = activities[activities["activity_id"] == activity_id]
            if not match.empty:
                name = str(match["name"].iloc[0])

        track = load_activity_track(activity_id)
        return make_detail_figure(track, name), visible
