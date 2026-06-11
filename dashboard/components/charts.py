"""Composants graphiques : histogramme FC, courbes de performance, stats sport."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

_BG_MAIN = "#0D0D14"
_BG_CARD = "#141420"
_GRID = "rgba(238,238,245,0.07)"
_FONT = dict(family="Barlow Condensed", color="#EEEEF5")
_HOVER_LABEL = dict(bgcolor=_BG_CARD, bordercolor="#7B2FBE", font=dict(color="#EEEEF5", family="Barlow Condensed"))


def _empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font={"size": 13, "color": "rgba(238,238,245,0.4)", "family": "Barlow Condensed"},
    )
    fig.update_layout(
        paper_bgcolor=_BG_CARD,
        plot_bgcolor=_BG_CARD,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


# ── Histogramme FC global ─────────────────────────────────────────────────────

def _zone_color(bpm: float) -> str:
    if bpm < 115:
        return "#00B4D8"
    if bpm < 135:
        return "#39D353"
    if bpm < 155:
        return "#EF9F27"
    if bpm < 170:
        return "#E040FB"
    return "#F72585"


def make_global_hr_histogram(hr_series: list[float]) -> go.Figure:
    """Histogramme FC global de toutes les activités avec zones colorées."""
    if not hr_series:
        return _empty_fig("Aucune donnée de fréquence cardiaque disponible")

    bins = list(range(80, 210, 5))
    counts, edges = np.histogram(hr_series, bins=bins)
    x_labels = [f"{int(edges[i])}–{int(edges[i + 1])}" for i in range(len(counts))]
    colors = [_zone_color((edges[i] + edges[i + 1]) / 2) for i in range(len(counts))]

    fig = go.Figure(
        go.Bar(
            x=x_labels,
            y=counts / 60,
            marker_color=colors,
            marker_line_width=0,
            hovertemplate="%{x} bpm<br>%{y:.1f} min<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        bargap=0.04,
        xaxis=dict(title="Fréquence cardiaque (bpm)", gridcolor=_GRID, tickfont=dict(size=11)),
        yaxis=dict(title="Temps (min)", gridcolor=_GRID, tickfont=dict(size=11)),
        margin=dict(l=48, r=16, t=32, b=48),
        height=260,
        hoverlabel=_HOVER_LABEL,
    )
    return fig


# ── Courbes de performance ────────────────────────────────────────────────────

def make_performance_curves(track: pd.DataFrame, x_mode: str = "time") -> go.Figure:
    """Courbes superposées : vitesse (axe gauche) + altitude (axe droit) + FC optionnelle."""
    if track.empty:
        return _empty_fig("Sélectionnez une activité pour voir les courbes")

    has_elevation = "elevation" in track.columns and track["elevation"].notna().any()
    has_hr = "heart_rate" in track.columns and track["heart_rate"].notna().any()
    has_dist = "cumulative_distance_m" in track.columns

    # X-axis
    if x_mode == "distance" and has_dist:
        x_vals = track["cumulative_distance_m"] / 1000
        x_title = "Distance (km)"
    elif "timestamp" in track.columns:
        ts = pd.to_datetime(track["timestamp"])
        x_vals = (ts - ts.iloc[0]).dt.total_seconds() / 60
        x_title = "Temps (min)"
    else:
        x_vals = pd.Series(range(len(track)), dtype=float)
        x_title = "Points"

    # Speed
    speed_kmh = pd.Series([0.0] * len(track))
    if has_dist:
        dist_m = track["cumulative_distance_m"].values
        if "timestamp" in track.columns:
            ts2 = pd.to_datetime(track["timestamp"])
            dt = ts2.diff().dt.total_seconds().fillna(1).clip(lower=0.1)
        else:
            dt = pd.Series([1.0] * len(track))
        speed_kmh = (pd.Series(dist_m).diff().fillna(0) / dt * 3.6).clip(lower=0, upper=80)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Speed → primary y
    fig.add_trace(
        go.Scatter(
            x=x_vals, y=speed_kmh,
            mode="lines", name="Vitesse",
            line=dict(color="#F72585", width=2),
            hovertemplate="%{y:.1f} km/h<extra>Vitesse</extra>",
        ),
        secondary_y=False,
    )

    # Altitude → secondary y, area fill
    if has_elevation:
        fig.add_trace(
            go.Scatter(
                x=x_vals, y=track["elevation"],
                mode="lines", name="Altitude",
                line=dict(color="#7B2FBE", width=1.5),
                fill="tozeroy", fillcolor="rgba(123,47,190,0.18)",
                hovertemplate="%{y:.0f} m<extra>Altitude</extra>",
            ),
            secondary_y=True,
        )

    # FC → primary y (thin line)
    if has_hr:
        fig.add_trace(
            go.Scatter(
                x=x_vals, y=track["heart_rate"],
                mode="lines", name="FC",
                line=dict(color="#00B4D8", width=1.5),
                hovertemplate="%{y:.0f} bpm<extra>FC</extra>",
            ),
            secondary_y=False,
        )

    fig.update_layout(
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        legend=dict(bgcolor="rgba(20,20,32,0.85)", bordercolor="#7B2FBE", font=dict(color="#EEEEF5")),
        margin=dict(l=48, r=56, t=16, b=48),
        height=280,
        hovermode="x unified",
        hoverlabel=_HOVER_LABEL,
        xaxis=dict(title=x_title, gridcolor=_GRID, tickfont=dict(size=11)),
    )
    fig.update_yaxes(
        title_text="Vitesse (km/h)" + (" / FC (bpm)" if has_hr else ""),
        gridcolor=_GRID,
        secondary_y=False,
        title_font=dict(color="#F72585"),
    )
    if has_elevation:
        fig.update_yaxes(
            title_text="Altitude (m)",
            gridcolor="rgba(0,0,0,0)",
            secondary_y=True,
            title_font=dict(color="#7B2FBE"),
        )
    return fig


# ── Stats par sport ───────────────────────────────────────────────────────────

_SPORT_PIE_COLORS: dict[str, str] = {
    "running": "#F72585",
    "cycling": "#00B4D8",
    "hiking": "#39D353",
    "walking": "#E040FB",
    "swimming": "#7B2FBE",
    "skiing": "#EEEEF5",
    "trail running": "#EF9F27",
}


def make_sport_stats_table(activities: pd.DataFrame) -> go.Figure:
    """Tableau des métriques agrégées par sport."""
    if activities.empty:
        return _empty_fig("Aucune activité")

    df = activities.copy()
    df["distance_km"] = df["total_distance_m"] / 1000 if "total_distance_m" in df.columns else 0
    df["duration_h"] = df["duration_s"] / 3600 if "duration_s" in df.columns else 0

    grp = (
        df.groupby("sport_type", sort=False)
        .agg(nb=("activity_id", "count"), dist=("distance_km", "sum"), dur=("duration_h", "sum"))
        .reset_index()
        .sort_values("dur", ascending=False)
    )
    row_colors = [
        ["rgba(247,37,133,0.08)" if i % 2 == 0 else _BG_CARD for i in range(len(grp))]
        for _ in range(4)
    ]

    fig = go.Figure(
        go.Table(
            columnwidth=[2.2, 1, 1.6, 1.6],
            header=dict(
                values=["Sport", "Activités", "Distance", "Durée"],
                fill_color="#1A1A2E",
                font=dict(color="#EEEEF5", family="Barlow Condensed", size=11),
                align=["left", "center", "center", "center"],
                line_color="rgba(123,47,190,0.5)",
                height=30,
            ),
            cells=dict(
                values=[
                    [s.capitalize() for s in grp["sport_type"]],
                    grp["nb"].tolist(),
                    [f"{d:.0f} km" for d in grp["dist"]],
                    [f"{h:.1f} h" for h in grp["dur"]],
                ],
                fill_color=row_colors,
                font=dict(color="#EEEEF5", family="Barlow Condensed", size=12),
                align=["left", "center", "center", "center"],
                line_color="rgba(123,47,190,0.2)",
                height=28,
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor=_BG_CARD,
        margin=dict(l=0, r=0, t=0, b=0),
        height=240,
    )
    return fig


def make_sport_duration_pie(activities: pd.DataFrame) -> go.Figure:
    """Donut chart de la durée totale par sport."""
    if activities.empty:
        return _empty_fig("Aucune activité")

    df = activities.copy()
    df["duration_h"] = df["duration_s"] / 3600 if "duration_s" in df.columns else 0

    grp = (
        df.groupby("sport_type")["duration_h"]
        .sum()
        .reset_index()
        .sort_values("duration_h", ascending=False)
    )

    colors = [_SPORT_PIE_COLORS.get(s.lower(), "#7B2FBE") for s in grp["sport_type"]]
    total_h = grp["duration_h"].sum()

    fig = go.Figure(
        go.Pie(
            labels=[s.capitalize() for s in grp["sport_type"]],
            values=grp["duration_h"],
            hole=0.62,
            marker=dict(
                colors=colors,
                line=dict(color=_BG_MAIN, width=3),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value:.1f} h — %{percent}<extra></extra>",
            direction="clockwise",
            sort=False,
        )
    )
    fig.add_annotation(
        text=f"<b>{total_h:.0f}h</b>",
        x=0.5, y=0.5,
        font=dict(size=22, color="#EEEEF5", family="Barlow Condensed"),
        showarrow=False,
    )
    fig.update_layout(
        paper_bgcolor=_BG_CARD,
        font=_FONT,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#EEEEF5", family="Barlow Condensed", size=11),
            orientation="v",
            x=1.0,
            y=0.5,
            xanchor="left",
        ),
        margin=dict(l=0, r=100, t=20, b=20),
        height=240,
        hoverlabel=_HOVER_LABEL,
    )
    return fig


# ── Scatter croisé ────────────────────────────────────────────────────────────

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

_SPORT_COLORS_SCATTER = [
    "#F72585", "#E040FB", "#7B2FBE", "#00B4D8", "#39D353", "#EF9F27",
]


def make_scatter_figure(
    activities: pd.DataFrame,
    x_col: str = "temperature_c",
    y_col: str = "pace_min_per_km",
) -> go.Figure:
    """Scatter plot croisé de deux métriques, coloré par sport — thème sombre."""
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

    sports = df["sport_type"].unique()
    fig = go.Figure()
    for i, sport in enumerate(sports):
        sub = df[df["sport_type"] == sport]
        color = _SPORT_COLORS_SCATTER[i % len(_SPORT_COLORS_SCATTER)]
        hover_name = sub["name"].tolist() if "name" in sub.columns else None
        fig.add_trace(
            go.Scatter(
                x=sub[x_col],
                y=sub[y_col],
                mode="markers",
                name=str(sport).capitalize(),
                customdata=sub[["activity_id"]].values if "activity_id" in sub.columns else None,
                text=hover_name,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    + _LABEL_MAP.get(x_col, x_col) + ": %{x}<br>"
                    + _LABEL_MAP.get(y_col, y_col) + ": %{y}<extra></extra>"
                ),
                marker=dict(size=9, color=color, opacity=0.85, line=dict(width=0)),
            )
        )

    fig.update_layout(
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        xaxis=dict(
            title=_LABEL_MAP.get(x_col, x_col),
            gridcolor=_GRID,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title=_LABEL_MAP.get(y_col, y_col),
            gridcolor=_GRID,
            tickfont=dict(size=11),
        ),
        legend=dict(bgcolor="rgba(20,20,32,0.85)", bordercolor="#7B2FBE", font=dict(color="#EEEEF5")),
        margin=dict(l=48, r=20, t=16, b=48),
        height=380,
        hoverlabel=_HOVER_LABEL,
    )
    return fig


# ── KPI hebdomadaires ─────────────────────────────────────────────────────────

_BAR_COLORS = ["#F72585", "#00B4D8", "#39D353", "#E040FB", "#EF9F27", "#7B2FBE"]


def make_weekly_distance_chart(weekly: pd.DataFrame) -> go.Figure:
    """Histogramme empilé de la distance hebdomadaire par sport."""
    if weekly.empty:
        return _empty_fig("Aucun KPI hebdomadaire — lancez clean_data.py")

    df = weekly.copy()
    df["label"] = df["year"].astype(str) + "-S" + df["week"].astype(str).str.zfill(2)
    df["distance_km"] = df["total_distance_m"] / 1000

    fig = go.Figure()
    for i, sport in enumerate(sorted(df["sport_type"].unique())):
        sub = df[df["sport_type"] == sport].sort_values(["year", "week"])
        fig.add_trace(go.Bar(
            x=sub["label"],
            y=sub["distance_km"],
            name=sport.capitalize(),
            marker_color=_BAR_COLORS[i % len(_BAR_COLORS)],
            hovertemplate="%{x}<br>%{y:.1f} km<extra>" + sport.capitalize() + "</extra>",
        ))

    fig.update_layout(
        barmode="stack",
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        xaxis=dict(title="Semaine", gridcolor=_GRID, tickfont=dict(size=10), tickangle=-45),
        yaxis=dict(title="Distance (km)", gridcolor=_GRID, tickfont=dict(size=11)),
        legend=dict(bgcolor="rgba(20,20,32,0.85)", bordercolor="#7B2FBE", font=dict(color="#EEEEF5")),
        margin=dict(l=48, r=20, t=16, b=80),
        height=300,
        hoverlabel=_HOVER_LABEL,
    )
    return fig


# ── TRIMP — charge d'entraînement ─────────────────────────────────────────────

_ZONE_WEIGHTS: dict[int, float] = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 4.5}


def make_trimp_chart(activities: pd.DataFrame) -> go.Figure:
    """Charge d'entraînement hebdomadaire — TRIMP simplifié (durée × facteur zone FC)."""
    if activities.empty:
        return _empty_fig("Aucune activité disponible")

    df = activities.copy()
    df["start_time"] = pd.to_datetime(df["start_time"])
    df = df.dropna(subset=["start_time", "duration_s"])
    df["duration_min"] = df["duration_s"] / 60
    df["trimp"] = df.apply(
        lambda r: r["duration_min"] * _ZONE_WEIGHTS.get(
            int(r["hr_zone"]) if pd.notna(r.get("hr_zone")) else 0, 1.0
        ),
        axis=1,
    )

    iso = df["start_time"].dt.isocalendar()
    df["label"] = iso.year.astype(int).astype(str) + "-S" + iso.week.astype(int).astype(str).str.zfill(2)
    weekly = df.groupby("label")["trimp"].sum().reset_index().sort_values("label")

    max_t = weekly["trimp"].max() or 1
    colors = [
        "#39D353" if v < max_t * 0.4 else "#EF9F27" if v < max_t * 0.7 else "#F72585"
        for v in weekly["trimp"]
    ]

    fig = go.Figure(go.Bar(
        x=weekly["label"],
        y=weekly["trimp"],
        marker_color=colors,
        marker_line_width=0,
        hovertemplate="%{x}<br>TRIMP : %{y:.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        xaxis=dict(title="Semaine", gridcolor=_GRID, tickfont=dict(size=10), tickangle=-45),
        yaxis=dict(title="Score TRIMP", gridcolor=_GRID, tickfont=dict(size=11)),
        margin=dict(l=48, r=20, t=16, b=80),
        height=260,
        hoverlabel=_HOVER_LABEL,
    )
    return fig


# ── Records personnels ─────────────────────────────────────────────────────────

def _best_for_distance(
    df: pd.DataFrame, min_m: float, max_m: float
) -> pd.Series | None:
    mask = (
        (df["total_distance_m"] >= min_m)
        & (df["total_distance_m"] <= max_m)
        & (df["sport_type"].str.lower().isin(["running", "trail running"]))
        & df["pace_min_per_km"].notna()
    )
    candidates = df[mask]
    if candidates.empty:
        return None
    return candidates.loc[candidates["pace_min_per_km"].idxmin()]


def _fmt_pace_rec(pace: float) -> str:
    mins = int(pace)
    secs = int((pace % 1) * 60)
    return f"{mins}'{secs:02d}\"/km"


def make_personal_records_table(activities: pd.DataFrame) -> go.Figure:
    """Tableau des records personnels sur les distances clés (course à pied)."""
    if activities.empty:
        return _empty_fig("Aucune activité disponible")

    records = [
        ("5 km",        4500,  5500),
        ("10 km",       9000, 11000),
        ("Semi-marathon", 19000, 22500),
        ("Marathon",    40000, 44000),
    ]

    labels, paces, dist_reelles, dates = [], [], [], []
    for label, mn, mx in records:
        best = _best_for_distance(activities, mn, mx)
        labels.append(label)
        if best is not None:
            paces.append(_fmt_pace_rec(float(best["pace_min_per_km"])))
            dist_reelles.append(f"{best['total_distance_m'] / 1000:.1f} km")
            try:
                dates.append(pd.to_datetime(best["start_time"]).strftime("%d/%m/%Y"))
            except Exception:
                dates.append("—")
        else:
            paces.append("—")
            dist_reelles.append("—")
            dates.append("—")

    if all(p == "—" for p in paces):
        return _empty_fig("Aucune activité de course à pied éligible")

    row_colors = [
        ["rgba(247,37,133,0.08)" if i % 2 == 0 else _BG_CARD for i in range(len(labels))]
        for _ in range(4)
    ]
    fig = go.Figure(go.Table(
        columnwidth=[1.8, 1.5, 1.5, 1.8],
        header=dict(
            values=["Distance", "Meilleure allure", "Dist. réelle", "Date"],
            fill_color="#1A1A2E",
            font=dict(color="#EEEEF5", family="Barlow Condensed", size=11),
            align=["left", "center", "center", "center"],
            line_color="rgba(123,47,190,0.5)",
            height=30,
        ),
        cells=dict(
            values=[labels, paces, dist_reelles, dates],
            fill_color=row_colors,
            font=dict(color="#EEEEF5", family="Barlow Condensed", size=12),
            align=["left", "center", "center", "center"],
            line_color="rgba(123,47,190,0.2)",
            height=28,
        ),
    ))
    fig.update_layout(
        paper_bgcolor=_BG_CARD,
        margin=dict(l=0, r=0, t=0, b=0),
        height=190,
    )
    return fig


# ── Comparaison de deux activités ─────────────────────────────────────────────

def make_comparison_chart(
    track1: pd.DataFrame,
    track2: pd.DataFrame,
    label1: str = "Activité 1",
    label2: str = "Activité 2",
) -> go.Figure:
    """Courbes de vitesse et FC superposées pour comparer deux activités."""
    if track1.empty and track2.empty:
        return _empty_fig("Sélectionnez deux activités ci-dessus pour les comparer")

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=False,
        subplot_titles=["Vitesse (km/h)", "Fréquence cardiaque (bpm)"],
        vertical_spacing=0.14,
    )

    palette = ["#F72585", "#00B4D8"]

    for idx, (track, label, color) in enumerate(
        [(track1, label1, palette[0]), (track2, label2, palette[1])]
    ):
        if track.empty:
            continue

        has_dist = "cumulative_distance_m" in track.columns
        if has_dist:
            x_vals = track["cumulative_distance_m"] / 1000
        elif "timestamp" in track.columns:
            ts = pd.to_datetime(track["timestamp"])
            x_vals = (ts - ts.iloc[0]).dt.total_seconds() / 60
        else:
            x_vals = pd.Series(range(len(track)), dtype=float)

        speed_kmh = pd.Series([0.0] * len(track))
        if has_dist and "timestamp" in track.columns:
            ts2 = pd.to_datetime(track["timestamp"])
            dt = ts2.diff().dt.total_seconds().fillna(1).clip(lower=0.1)
            speed_kmh = (track["cumulative_distance_m"].diff().fillna(0) / dt * 3.6).clip(lower=0, upper=80)

        fig.add_trace(go.Scatter(
            x=x_vals, y=speed_kmh, mode="lines", name=label,
            line=dict(color=color, width=2),
            hovertemplate=f"{label}: %{{y:.1f}} km/h<extra></extra>",
            legendgroup=label,
        ), row=1, col=1)

        if "heart_rate" in track.columns and track["heart_rate"].notna().any():
            fig.add_trace(go.Scatter(
                x=x_vals, y=track["heart_rate"], mode="lines", name=label,
                line=dict(color=color, width=2),
                hovertemplate=f"{label}: %{{y:.0f}} bpm<extra></extra>",
                showlegend=False,
                legendgroup=label,
            ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor=_BG_MAIN,
        plot_bgcolor=_BG_CARD,
        font=_FONT,
        legend=dict(bgcolor="rgba(20,20,32,0.85)", bordercolor="#7B2FBE", font=dict(color="#EEEEF5")),
        margin=dict(l=48, r=20, t=40, b=48),
        height=480,
        hovermode="x unified",
        hoverlabel=_HOVER_LABEL,
    )
    fig.update_xaxes(gridcolor=_GRID, tickfont=dict(size=11))
    fig.update_yaxes(gridcolor=_GRID, tickfont=dict(size=11))
    return fig
