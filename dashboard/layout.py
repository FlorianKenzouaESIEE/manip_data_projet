"""Layout principal du dashboard DashSport."""

from __future__ import annotations

from dash import dcc, html

from .components.header import header_component
from .components.map import make_map_figure
from .data import load_activities, load_track_points


def create_layout() -> html.Div:
    """Construit et retourne le layout complet de l'application."""
    activities = load_activities()
    tracks = load_track_points()

    return html.Div(
        [
            header_component(activities),
            html.Main(
                [
                    html.Section(
                        [
                            html.H2(
                                "Carte des tracés GPS",
                                style={
                                    "margin": "0 0 0.75rem",
                                    "fontSize": "1.1rem",
                                    "color": "#333",
                                    "fontWeight": "600",
                                },
                            ),
                            dcc.Graph(
                                id="map-activities",
                                figure=make_map_figure(tracks, activities),
                                style={"height": "600px"},
                                config={"scrollZoom": True},
                            ),
                        ],
                        style={"padding": "1.5rem 2rem"},
                    ),
                ],
                style={"background": "#f5f5f5", "minHeight": "calc(100vh - 80px)"},
            ),
        ],
        style={"fontFamily": "Arial, sans-serif", "margin": "0"},
    )
