"""Layout principal du dashboard DashSport."""

from __future__ import annotations

from dash import dcc, html

from .components.charts import (
    make_activity_type_bar,
    make_distance_histogram,
    make_duration_histogram,
)
from .components.header import header_component
from .components.map import make_map_figure
from .data import load_activities, load_track_points

_SECTION_STYLE = {"padding": "1.5rem 2rem"}
_TITLE_STYLE: dict = {
    "margin": "0 0 0.75rem",
    "fontSize": "1.1rem",
    "color": "#333",
    "fontWeight": "600",
}
_HR_STYLE: dict = {"border": "none", "borderTop": "1px solid #ddd", "margin": "0"}


def create_layout() -> html.Div:
    """Construit et retourne le layout complet de l'application."""
    activities = load_activities()
    tracks = load_track_points()

    return html.Div(
        [
            header_component(activities),
            html.Main(
                [
                    # ── Section 1 : Carte GPS ─────────────────────────────────
                    html.Section(
                        [
                            html.H2("Carte des tracés GPS", style=_TITLE_STYLE),
                            dcc.Graph(
                                id="map-activities",
                                figure=make_map_figure(tracks, activities),
                                style={"height": "600px"},
                                config={"scrollZoom": True},
                            ),
                        ],
                        style=_SECTION_STYLE,
                    ),
                    html.Hr(style=_HR_STYLE),
                    # ── Section 2 : Histogrammes ──────────────────────────────
                    html.Section(
                        [
                            html.H2("Distribution des activités", style=_TITLE_STYLE),
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="bar-sport-type",
                                        figure=make_activity_type_bar(activities),
                                        style={"flex": "1", "minWidth": "280px"},
                                        config={"displayModeBar": False},
                                    ),
                                    dcc.Graph(
                                        id="hist-distance",
                                        figure=make_distance_histogram(activities),
                                        style={"flex": "1", "minWidth": "280px"},
                                        config={"displayModeBar": False},
                                    ),
                                    dcc.Graph(
                                        id="hist-duration",
                                        figure=make_duration_histogram(activities),
                                        style={"flex": "1", "minWidth": "280px"},
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "1rem",
                                    "flexWrap": "wrap",
                                },
                            ),
                        ],
                        style=_SECTION_STYLE,
                    ),
                ],
                style={"background": "#f5f5f5", "minHeight": "calc(100vh - 80px)"},
            ),
        ],
        style={"fontFamily": "Arial, sans-serif", "margin": "0"},
    )
