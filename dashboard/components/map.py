"""Composant carte géographique — tracé GPS d'une activité (CartoDB Positron)."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def make_activity_map(track: pd.DataFrame) -> go.Figure:
    """Construit la carte d'une activité avec tuiles CartoDB Positron.

    Args:
        track: Points GPS complets de l'activité (depuis load_activity_track).
    """
    if track.empty or "lat" not in track.columns or "lon" not in track.columns:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#141420",
            plot_bgcolor="#141420",
            margin=dict(l=0, r=0, t=0, b=0),
            height=350,
        )
        fig.add_annotation(
            text="Aucun tracé GPS disponible",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="rgba(238,238,245,0.4)", size=13, family="Barlow Condensed"),
        )
        return fig

    center_lat = float(track["lat"].mean())
    center_lon = float(track["lon"].mean())

    fig = go.Figure()

    # Tracé GPS — Deep Purple
    fig.add_trace(
        go.Scattermapbox(
            lat=track["lat"].tolist(),
            lon=track["lon"].tolist(),
            mode="lines",
            line=dict(width=5, color="#7B2FBE"),
            hoverinfo="none",
            name="Tracé",
        )
    )

    # Marqueur départ — Electric Cyan
    fig.add_trace(
        go.Scattermapbox(
            lat=[float(track["lat"].iloc[0])],
            lon=[float(track["lon"].iloc[0])],
            mode="markers",
            marker=dict(size=12, color="#00B4D8"),
            hovertemplate="Départ<extra></extra>",
            name="Départ",
        )
    )

    # Marqueur arrivée — Hot Pink
    fig.add_trace(
        go.Scattermapbox(
            lat=[float(track["lat"].iloc[-1])],
            lon=[float(track["lon"].iloc[-1])],
            mode="markers",
            marker=dict(size=12, color="#F72585"),
            hovertemplate="Arrivée<extra></extra>",
            name="Arrivée",
        )
    )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=13,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=350,
        paper_bgcolor="#141420",
        showlegend=False,
    )
    return fig
