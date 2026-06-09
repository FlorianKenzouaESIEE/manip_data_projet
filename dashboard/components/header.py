"""Composant d'en-tête du dashboard."""

from __future__ import annotations

import pandas as pd
from dash import html


def header_component(activities: pd.DataFrame) -> html.Header:
    """Construit l'en-tête avec les KPI globaux.

    Args:
        activities: DataFrame des activités enrichies (peut être vide).
    """
    if activities.empty:
        subtitle = "Aucune activité — lancez d'abord get_data.py puis clean_data.py"
    else:
        n = len(activities)
        km = activities["total_distance_m"].sum() / 1000
        subtitle = f"{n} activité(s)  ·  {km:.0f} km au total"

    return html.Header(
        [
            html.H1("DashSport", style={"margin": "0", "fontSize": "1.8rem", "fontWeight": "700"}),
            html.P(subtitle, style={"margin": "0.25rem 0 0", "opacity": "0.85", "fontSize": "0.95rem"}),
        ],
        style={
            "background": "#1a1a2e",
            "color": "white",
            "padding": "1rem 2rem",
            "borderBottom": "3px solid #e94560",
        },
    )
