"""Composant d'en-tête du dashboard."""

from __future__ import annotations

import pandas as pd
from dash import html

_GRAD_STYLE: dict = {
    "background": "linear-gradient(135deg, #F72585, #7B2FBE)",
    "WebkitBackgroundClip": "text",
    "WebkitTextFillColor": "transparent",
    "backgroundClip": "text",
    "display": "inline-block",
    "fontFamily": "'Barlow Condensed', sans-serif",
    "fontWeight": "900",
    "lineHeight": "1",
}


def _fmt_duration(total_s: float) -> str:
    h = int(total_s // 3600)
    m = int((total_s % 3600) // 60)
    return f"{h}h{m:02d}"


def _kpi_block(value: str, label: str) -> html.Div:
    return html.Div(
        [
            html.Span(value, style={**_GRAD_STYLE, "fontSize": "2rem"}),
            html.Div(
                label,
                style={
                    "fontSize": "0.65rem",
                    "fontFamily": "'Barlow', sans-serif",
                    "fontWeight": "600",
                    "letterSpacing": "0.12em",
                    "color": "#EEEEF5",
                    "opacity": "0.5",
                    "textTransform": "uppercase",
                    "marginTop": "3px",
                },
            ),
        ],
        style={"textAlign": "center"},
    )


def header_component(activities: pd.DataFrame) -> html.Header:
    """Construit l'en-tête fixe avec les KPI globaux."""
    if activities.empty:
        total_km, total_acts, total_dur = 0.0, 0, 0.0
    else:
        total_km = activities["total_distance_m"].sum() / 1000
        total_acts = len(activities)
        total_dur = float(activities["duration_s"].sum())

    divider = html.Div(
        style={
            "width": "1px",
            "alignSelf": "stretch",
            "background": "rgba(123,47,190,0.35)",
            "margin": "0 0.25rem",
        }
    )

    return html.Header(
        [
            html.Div(
                [
                    html.Span(
                        "Dash",
                        style={
                            "fontFamily": "'Barlow Condensed', sans-serif",
                            "fontWeight": "900",
                            "fontSize": "1.75rem",
                            "color": "#EEEEF5",
                        },
                    ),
                    html.Span(
                        "Sport",
                        style={
                            **_GRAD_STYLE,
                            "fontSize": "1.75rem",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "1px"},
            ),
            html.Div(
                [
                    _kpi_block(f"{total_km:,.0f} km", "Distance"),
                    divider,
                    _kpi_block(str(total_acts), "Activités"),
                    divider,
                    _kpi_block(_fmt_duration(total_dur), "Durée"),
                ],
                style={
                    "display": "flex",
                    "gap": "1.5rem",
                    "alignItems": "center",
                },
            ),
        ],
        style={
            "background": "#0D0D14",
            "borderBottom": "1px solid rgba(123,47,190,0.6)",
            "padding": "0.75rem 2rem",
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "position": "sticky",
            "top": "0",
            "zIndex": "100",
        },
    )
