"""Composants graphiques : histogrammes, analyses croisées, détail d'activité."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_COLORS = px.colors.qualitative.Set2
_EMPTY_LAYOUT: dict = {
    "paper_bgcolor": "#f5f5f5",
    "plot_bgcolor": "#f5f5f5",
    "font": {"color": "#999"},
    "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
}


def _empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 13, "color": "#999"},
    )
    fig.update_layout(**_EMPTY_LAYOUT)
    return fig


# ─── Étape 13 : histogrammes ─────────────────────────────────────────────────


def make_activity_type_bar(activities: pd.DataFrame) -> go.Figure:
    """Nombre d'activités par type de sport (bar chart).

    Args:
        activities: DataFrame des activités enrichies.
    """
    if activities.empty:
        return _empty_fig("Aucune activité disponible")
    counts = activities["sport_type"].value_counts().reset_index()
    counts.columns = ["sport_type", "count"]
    fig = px.bar(
        counts,
        x="sport_type",
        y="count",
        color="sport_type",
        color_discrete_sequence=_COLORS,
        labels={"sport_type": "Sport", "count": "Nombre"},
        title="Activités par sport",
    )
    fig.update_layout(
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        xaxis={"showgrid": False},
        yaxis={"showgrid": True, "gridcolor": "#eee"},
    )
    return fig


def make_distance_histogram(activities: pd.DataFrame) -> go.Figure:
    """Distribution des distances en km.

    Args:
        activities: DataFrame des activités enrichies.
    """
    if activities.empty or "total_distance_m" not in activities.columns:
        return _empty_fig("Aucune donnée de distance")
    df = activities.copy()
    df["distance_km"] = df["total_distance_m"] / 1000
    fig = px.histogram(
        df,
        x="distance_km",
        nbins=20,
        color="sport_type",
        color_discrete_sequence=_COLORS,
        labels={"distance_km": "Distance (km)"},
        title="Distribution des distances",
    )
    fig.update_layout(
        barmode="overlay",
        bargap=0.05,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        yaxis={"showgrid": True, "gridcolor": "#eee"},
    )
    fig.update_traces(opacity=0.75)
    return fig


def make_duration_histogram(activities: pd.DataFrame) -> go.Figure:
    """Distribution des durées en minutes.

    Args:
        activities: DataFrame des activités enrichies.
    """
    if activities.empty or "duration_s" not in activities.columns:
        return _empty_fig("Aucune donnée de durée")
    df = activities.copy()
    df["duration_min"] = df["duration_s"] / 60
    fig = px.histogram(
        df,
        x="duration_min",
        nbins=20,
        color="sport_type",
        color_discrete_sequence=_COLORS,
        labels={"duration_min": "Durée (min)"},
        title="Distribution des durées",
    )
    fig.update_layout(
        barmode="overlay",
        bargap=0.05,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        yaxis={"showgrid": True, "gridcolor": "#eee"},
    )
    fig.update_traces(opacity=0.75)
    return fig


# ─── Étape 14 : scatter croisés ──────────────────────────────────────────────

SCATTER_OPTIONS: list[dict[str, str]] = [
    {"label": "Allure (min/km)", "value": "pace_min_per_km"},
    {"label": "Vitesse (km/h)", "value": "speed_kmh"},
    {"label": "Distance (km)", "value": "distance_km"},
    {"label": "Durée (min)", "value": "duration_min"},
    {"label": "FC moyenne (bpm)", "value": "avg_heart_rate"},
    {"label": "FC max (bpm)", "value": "max_heart_rate"},
    {"label": "Température (°C)", "value": "temperature_c"},
    {"label": "Vent (km/h)", "value": "wind_speed_kmh"},
    {"label": "Humidité (%)", "value": "humidity_pct"},
]

_LABEL_MAP: dict[str, str] = {o["value"]: o["label"] for o in SCATTER_OPTIONS}


def make_scatter_figure(
    activities: pd.DataFrame,
    x_col: str = "temperature_c",
    y_col: str = "pace_min_per_km",
) -> go.Figure:
    """Scatter plot croisé de deux métriques, coloré par sport.

    Args:
        activities: DataFrame des activités enrichies.
        x_col: Colonne pour l'axe X (valeur de SCATTER_OPTIONS).
        y_col: Colonne pour l'axe Y (valeur de SCATTER_OPTIONS).
    """
    if activities.empty:
        return _empty_fig("Aucune activité disponible")

    df = activities.copy()
    if "total_distance_m" in df.columns:
        df["distance_km"] = df["total_distance_m"] / 1000
    if "duration_s" in df.columns:
        df["duration_min"] = df["duration_s"] / 60

    if x_col not in df.columns or y_col not in df.columns:
        return _empty_fig(f"Colonnes manquantes : {x_col}, {y_col}")

    df = df.dropna(subset=[x_col, y_col])
    if df.empty:
        return _empty_fig("Pas de données pour cette combinaison")

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color="sport_type",
        hover_name="name" if "name" in df.columns else None,
        custom_data=["activity_id"],
        color_discrete_sequence=_COLORS,
        labels={
            x_col: _LABEL_MAP.get(x_col, x_col),
            y_col: _LABEL_MAP.get(y_col, y_col),
        },
        title=f"{_LABEL_MAP.get(x_col, x_col)} × {_LABEL_MAP.get(y_col, y_col)}",
    )
    fig.update_traces(marker={"size": 9, "opacity": 0.8})
    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        xaxis={"showgrid": True, "gridcolor": "#eee"},
        yaxis={"showgrid": True, "gridcolor": "#eee"},
        legend_title="Sport",
    )
    return fig


# ─── Étape 15 : détail seconde par seconde ────────────────────────────────────


def make_detail_figure(track: pd.DataFrame, activity_name: str = "") -> go.Figure:
    """Profils d'une activité : élévation, vitesse et FC dans le temps.

    Args:
        track: Points GPS complets d'une activité (depuis load_activity_track).
        activity_name: Nom de l'activité pour le titre du graphique.
    """
    if track.empty:
        return _empty_fig("Cliquez sur un point du graphique croisé pour voir le détail")

    from plotly.subplots import make_subplots

    has_elevation = "elevation" in track.columns and track["elevation"].notna().any()
    has_hr = "heart_rate" in track.columns and track["heart_rate"].notna().any()
    has_speed = "cumulative_distance_m" in track.columns

    row_titles: list[str] = []
    if has_elevation:
        row_titles.append("Élévation (m)")
    if has_speed:
        row_titles.append("Vitesse (km/h)")
    if has_hr:
        row_titles.append("Fréquence cardiaque (bpm)")

    n_rows = len(row_titles) or 1
    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=True,
        subplot_titles=row_titles if row_titles else ["Aucune donnée"],
        vertical_spacing=0.1,
    )

    x_axis: pd.Series = (
        pd.to_datetime(track["timestamp"])
        if "timestamp" in track.columns
        else pd.Series(track.index)
    )

    row = 1

    if has_elevation:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=track["elevation"],
                mode="lines",
                name="Élévation",
                line={"color": "#8bc34a", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(139,195,74,0.15)",
            ),
            row=row,
            col=1,
        )
        row += 1

    if has_speed:
        dist = track["cumulative_distance_m"].values
        if "timestamp" in track.columns:
            times = pd.to_datetime(track["timestamp"])
            dt = times.diff().dt.total_seconds().fillna(1).clip(lower=0.1)
        else:
            dt = pd.Series([1.0] * len(track))
        speed_kmh = (pd.Series(dist).diff().fillna(0) / dt * 3.6).clip(lower=0, upper=60)
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=speed_kmh,
                mode="lines",
                name="Vitesse",
                line={"color": "#1565c0", "width": 1.5},
            ),
            row=row,
            col=1,
        )
        row += 1

    if has_hr:
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=track["heart_rate"],
                mode="lines",
                name="FC",
                line={"color": "#e94560", "width": 1.5},
            ),
            row=row,
            col=1,
        )

    title = f"Détail : {activity_name}" if activity_name else "Détail de l'activité"
    fig.update_layout(
        title=title,
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
        height=max(300, n_rows * 200),
    )
    for i in range(1, n_rows + 1):
        fig.update_xaxes(showgrid=True, gridcolor="#eee", row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor="#eee", row=i, col=1)

    return fig
