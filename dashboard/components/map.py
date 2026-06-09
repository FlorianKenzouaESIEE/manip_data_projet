"""Composant carte géographique des tracés GPS."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_map_figure(tracks: pd.DataFrame, activities: pd.DataFrame) -> go.Figure:
    """Construit la carte des tracés GPS de toutes les activités.

    Args:
        tracks: Points GPS sous-échantillonnés (depuis dashsport_raw.db).
        activities: Activités enrichies (depuis dashsport_clean.db).

    Returns:
        Figure Plotly prête à afficher dans un dcc.Graph.
    """
    if tracks.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Aucun tracé disponible — lancez get_data.py puis clean_data.py",
            paper_bgcolor="#f5f5f5",
            font={"color": "#555"},
        )
        return fig

    merged = tracks.copy()
    if not activities.empty:
        meta = activities[["activity_id", "name", "sport_type"]].copy()
        merged = tracks.merge(meta, on="activity_id", how="left")
    else:
        merged["sport_type"] = "unknown"
        merged["name"] = "Activité " + merged["activity_id"].astype(str)

    merged["sport_type"] = merged["sport_type"].fillna("unknown")
    merged["name"] = merged["name"].fillna("Sans nom")

    center = {
        "lat": float(merged["lat"].mean()),
        "lon": float(merged["lon"].mean()),
    }

    fig = px.scatter_mapbox(
        merged,
        lat="lat",
        lon="lon",
        color="sport_type",
        hover_name="name",
        hover_data={"lat": False, "lon": False, "sport_type": False},
        center=center,
        zoom=11,
        mapbox_style="open-street-map",
        title="Tracés GPS de toutes les activités",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(marker={"size": 3, "opacity": 0.7})
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        legend_title="Sport",
        legend={"bgcolor": "rgba(255,255,255,0.85)", "bordercolor": "#ccc", "borderwidth": 1},
    )
    return fig
