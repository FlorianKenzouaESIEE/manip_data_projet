"""Callbacks Dash : navigation entre vues et mise à jour des graphiques."""

from __future__ import annotations

from typing import Any

import pandas as pd
import dash
from dash import ALL, Input, Output, State, callback_context, html, dcc

from .components.charts import (
    make_comparison_chart,
    make_performance_curves,
    make_sport_duration_pie,
    make_sport_stats_table,
)
from .components.map import make_activity_map
from .data import load_activities, load_activity_track
from .layout import build_activity_card

# ── Design tokens (dupliqués ici pour rester autonome) ───────────────────────
_BG_MAIN = "#0D0D14"
_BG_CARD = "#141420"
_PINK = "#F72585"
_VIOLET = "#E040FB"
_PURPLE = "#7B2FBE"
_CYAN = "#00B4D8"
_TEXT = "#EEEEF5"
_CARD_STYLE: dict = {
    "background": _BG_CARD,
    "borderRadius": "12px",
    "border": "1px solid rgba(123,47,190,0.3)",
    "padding": "1.25rem",
    "marginBottom": "1rem",
}
_SECTION_TITLE: dict = {
    "fontFamily": "'Barlow Condensed', sans-serif",
    "fontWeight": "700",
    "fontSize": "0.85rem",
    "color": _TEXT,
    "letterSpacing": "0.12em",
    "textTransform": "uppercase",
    "opacity": "0.55",
    "marginBottom": "0.75rem",
}
_SPORT_ICONS: dict[str, str] = {
    "running": "🏃", "cycling": "🚴", "hiking": "🥾",
    "walking": "🚶", "swimming": "🏊", "skiing": "⛷", "trail running": "🏔",
}


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _fmt_pace(pace: float) -> str:
    mins = int(pace)
    secs = int((pace % 1) * 60)
    return f"{mins}'{secs:02d}\"/km"


def _fmt_duration(dur_s: float) -> str:
    h = int(dur_s // 3600)
    m = int((dur_s % 3600) // 60)
    return f"{h}h{m:02d}" if h > 0 else f"{m}min"


def _compute_elevation_gain(track: pd.DataFrame) -> float | None:
    if "elevation" not in track.columns or track["elevation"].isna().all():
        return None
    elev = track["elevation"].dropna()
    if len(elev) < 2:
        return None
    gain = float(elev.diff().clip(lower=0).sum())
    return gain if gain > 1 else None


def _grad_text(value: str, size: str = "2rem") -> html.Span:
    return html.Span(
        value,
        style={
            "background": f"linear-gradient(135deg, {_PINK}, {_PURPLE})",
            "WebkitBackgroundClip": "text",
            "WebkitTextFillColor": "transparent",
            "backgroundClip": "text",
            "display": "inline-block",
            "fontFamily": "'Barlow Condensed', sans-serif",
            "fontWeight": "900",
            "fontSize": size,
            "lineHeight": "1",
        },
    )


def _build_detail_header(row: pd.Series) -> html.Div:
    sport = str(row.get("sport_type", "")).lower()
    icon = _SPORT_ICONS.get(sport, "🏅")
    try:
        date = pd.to_datetime(row["start_time"]).strftime("%d %B %Y")
    except Exception:
        date = str(row.get("start_time", ""))

    return html.Div(
        [
            html.Span(icon, style={"fontSize": "2rem"}),
            html.Div(
                [
                    html.Div(
                        str(row.get("name", "Activité")),
                        style={
                            "fontFamily": "'Barlow Condensed', sans-serif",
                            "fontWeight": "700",
                            "fontSize": "1.6rem",
                            "color": _TEXT,
                        },
                    ),
                    html.Div(
                        f"{sport.capitalize()} · {date}",
                        style={
                            "fontSize": "0.8rem",
                            "color": _TEXT,
                            "opacity": "0.5",
                            "fontFamily": "'Barlow', sans-serif",
                            "marginTop": "2px",
                        },
                    ),
                ],
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "0.875rem",
            "padding": "1rem 0 0.75rem",
        },
    )


def _build_hero_metrics(row: pd.Series, track: pd.DataFrame) -> html.Div:
    km = row.get("total_distance_m", 0) / 1000
    dur_str = _fmt_duration(float(row.get("duration_s", 0)))
    pace = row.get("pace_min_per_km")
    pace_str = _fmt_pace(float(pace)) if (pace is not None and not pd.isna(pace)) else "—"
    gain = _compute_elevation_gain(track)
    gain_str = f"+{gain:.0f} m" if gain else "—"

    def hero_card(label: str, value: str) -> html.Div:
        return html.Div(
            [
                _grad_text(value, "2rem"),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.65rem",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.12em",
                        "opacity": "0.5",
                        "fontFamily": "'Barlow', sans-serif",
                        "fontWeight": "600",
                        "marginTop": "4px",
                    },
                ),
            ],
            style={
                "textAlign": "center",
                "background": _BG_CARD,
                "borderRadius": "12px",
                "padding": "0.875rem 0.5rem",
                "border": "1px solid rgba(123,47,190,0.25)",
            },
        )

    return html.Div(
        [
            hero_card("Distance", f"{km:.1f} km"),
            hero_card("Durée", dur_str),
            hero_card("Allure moy.", pace_str),
            hero_card("Dénivelé", gain_str),
        ],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "0.75rem",
            "marginBottom": "1rem",
        },
    )


def _build_weather_section(row: pd.Series, track: pd.DataFrame) -> html.Div:
    temp = row.get("temperature_c")
    wind = row.get("wind_speed_kmh")
    hum = row.get("humidity_pct")
    avg_elev: float | None = (
        float(track["elevation"].mean())
        if "elevation" in track.columns and track["elevation"].notna().any()
        else None
    )

    def _color(metric: str, val: Any) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return _TEXT
        if metric == "wind" and float(val) > 30:
            return _PINK
        if metric == "temp" and float(val) > 30:
            return _VIOLET
        if metric == "humidity" and float(val) > 80:
            return _CYAN
        return _TEXT

    def w_card(icon: str, label: str, val_str: str, color: str) -> html.Div:
        return html.Div(
            [
                html.Div(icon, style={"fontSize": "1.3rem", "marginBottom": "0.3rem"}),
                html.Div(
                    val_str,
                    style={
                        "fontFamily": "'Barlow Condensed', sans-serif",
                        "fontWeight": "900",
                        "fontSize": "1.4rem",
                        "color": color,
                        "lineHeight": "1",
                    },
                ),
                html.Div(
                    label,
                    style={
                        "fontSize": "0.65rem",
                        "opacity": "0.5",
                        "fontFamily": "'Barlow', sans-serif",
                        "fontWeight": "600",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.08em",
                        "marginTop": "4px",
                    },
                ),
            ],
            style={
                "background": _BG_MAIN,
                "borderRadius": "8px",
                "padding": "0.75rem 0.5rem",
                "textAlign": "center",
                "border": "1px solid rgba(123,47,190,0.2)",
            },
        )

    def _safe_str(val: Any, fmt: str, suffix: str) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        return f"{float(val):{fmt}}{suffix}"

    cards = [
        w_card("🌡", "Température", _safe_str(temp, ".0f", "°C"), _color("temp", temp)),
        w_card("💨", "Vent", _safe_str(wind, ".0f", " km/h"), _color("wind", wind)),
        w_card("💧", "Humidité", _safe_str(hum, ".0f", "%"), _color("humidity", hum)),
        w_card("⛰", "Altitude moy.", _safe_str(avg_elev, ".0f", " m"), _TEXT),
    ]

    # Analyse conditions
    cond_text = ""
    cond_color = _TEXT
    try:
        has_all = all(v is not None and not pd.isna(v) for v in [temp, wind, hum])
        if has_all:
            t, w, h = float(temp), float(wind), float(hum)
            if w > 30 or t > 32 or h > 85:
                cond_text = "⚠ Conditions difficiles"
                cond_color = _PINK
            elif t > 20 and w < 15 and h < 70:
                cond_text = "✓ Conditions optimales"
                cond_color = "#39D353"
            else:
                cond_text = "✓ Conditions favorables"
                cond_color = _CYAN
    except (TypeError, ValueError):
        pass

    children: list = [
        html.Div("Conditions de la séance", style=_SECTION_TITLE),
        html.Div(
            cards,
            style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "0.625rem"},
        ),
    ]
    if cond_text:
        children.append(
            html.Div(
                cond_text,
                style={
                    "marginTop": "0.75rem",
                    "fontSize": "0.8rem",
                    "color": cond_color,
                    "fontFamily": "'Barlow', sans-serif",
                    "fontWeight": "600",
                },
            )
        )

    return html.Div(children, style=_CARD_STYLE)


# ── Enregistrement des callbacks ──────────────────────────────────────────────

def register_callbacks(app: dash.Dash) -> None:
    """Enregistre tous les callbacks de l'application."""

    # ── Callback 1 : navigation entre vues ────────────────────────────────────

    @app.callback(
        Output("app-state", "data"),
        [
            Input({"type": "activity-card", "index": ALL}, "n_clicks"),
            Input("btn-retour", "n_clicks"),
        ],
        State("app-state", "data"),
        prevent_initial_call=True,
    )
    def update_app_state(
        card_clicks: list[int | None],
        retour_clicks: int | None,
        current_state: dict,
    ) -> dict:
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered_id = ctx.triggered_id

        if triggered_id == "btn-retour":
            return {"view": "dashboard", "activity_id": None}

        if isinstance(triggered_id, dict) and triggered_id.get("type") == "activity-card":
            val = ctx.triggered[0].get("value")
            if val and int(val) > 0:
                return {"view": "detail", "activity_id": triggered_id["index"]}

        raise dash.exceptions.PreventUpdate

    # ── Callback 2 : rendu des vues ────────────────────────────────────────────

    @app.callback(
        [
            Output("view-dashboard", "style"),
            Output("view-detail", "style"),
            Output("detail-header", "children"),
            Output("detail-hero-metrics", "children"),
            Output("detail-map", "figure"),
            Output("detail-curves", "figure"),
            Output("detail-weather", "children"),
        ],
        [
            Input("app-state", "data"),
            Input("curves-x-mode", "value"),
        ],
    )
    def render_view(
        state: dict | None,
        x_mode: str,
    ) -> tuple:
        dash_visible = {"display": "block"}
        dash_hidden = {"display": "none"}
        detail_hidden = {"display": "none"}
        detail_visible = {"display": "block"}

        empty_map = make_activity_map(pd.DataFrame())
        empty_curves = make_performance_curves(pd.DataFrame())

        if not state or state.get("view") != "detail":
            return dash_visible, detail_hidden, [], [], empty_map, empty_curves, []

        activity_id = state.get("activity_id")
        if activity_id is None:
            return dash_visible, detail_hidden, [], [], empty_map, empty_curves, []

        activities = load_activities()
        if activities.empty:
            return dash_visible, detail_hidden, [], [], empty_map, empty_curves, []

        match = activities[activities["activity_id"] == activity_id]
        if match.empty:
            return dash_visible, detail_hidden, [], [], empty_map, empty_curves, []

        row = match.iloc[0]
        track = load_activity_track(int(activity_id))

        return (
            dash_hidden,
            detail_visible,
            _build_detail_header(row),
            _build_hero_metrics(row, track),
            make_activity_map(track),
            make_performance_curves(track, x_mode=x_mode or "time"),
            _build_weather_section(row, track),
        )

    # ── Callback 3 : filtre par période ───────────────────────────────────────

    @app.callback(
        [
            Output("sport-stats-table", "figure"),
            Output("sport-duration-pie", "figure"),
            Output("filter-summary", "children"),
        ],
        [
            Input("date-filter", "start_date"),
            Input("date-filter", "end_date"),
        ],
    )
    def filter_by_date(
        start_date: str | None,
        end_date: str | None,
    ) -> tuple:
        acts = load_activities()

        if not acts.empty and (start_date or end_date):
            acts = acts.copy()
            acts["start_time"] = pd.to_datetime(acts["start_time"])
            if start_date:
                acts = acts[acts["start_time"] >= pd.to_datetime(start_date)]
            if end_date:
                acts = acts[acts["start_time"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]

        if start_date or end_date:
            summary: str | None = f"{len(acts)} activité(s) sur la période sélectionnée"
        else:
            summary = None

        return (
            make_sport_stats_table(acts),
            make_sport_duration_pie(acts),
            summary,
        )

    # ── Callback 4 : comparaison de deux activités ────────────────────────────

    @app.callback(
        Output("compare-chart", "figure"),
        [
            Input("compare-activity-1", "value"),
            Input("compare-activity-2", "value"),
        ],
    )
    def update_comparison(
        act1_id: int | None,
        act2_id: int | None,
    ) -> object:
        if act1_id is None and act2_id is None:
            return make_comparison_chart(pd.DataFrame(), pd.DataFrame())

        activities = load_activities()

        track1 = load_activity_track(int(act1_id)) if act1_id is not None else pd.DataFrame()
        track2 = load_activity_track(int(act2_id)) if act2_id is not None else pd.DataFrame()

        def _label(aid: int | None) -> str:
            if aid is None or activities.empty:
                return "—"
            m = activities[activities["activity_id"] == aid]
            return str(m.iloc[0]["name"]) if not m.empty else f"Activité {aid}"

        return make_comparison_chart(track1, track2, _label(act1_id), _label(act2_id))
