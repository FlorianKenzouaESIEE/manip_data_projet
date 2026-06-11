"""Layout principal du dashboard DashSport — design system sombre."""

from __future__ import annotations

import pandas as pd
from dash import dcc, html

from .components.charts import (
    make_comparison_chart,
    make_global_hr_histogram,
    make_personal_records_table,
    make_sport_duration_pie,
    make_sport_stats_table,
    make_trimp_chart,
    make_weekly_distance_chart,
)
from .components.header import header_component
from .data import load_activities, load_hr_series_all, load_weekly_kpis

# ── Design tokens ─────────────────────────────────────────────────────────────
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
    "border": f"1px solid rgba(123,47,190,0.3)",
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

# ── Couleurs et icônes par sport ──────────────────────────────────────────────
_SPORT_COLORS: dict[str, str] = {
    "running": _PINK,
    "cycling": _CYAN,
    "hiking": "#39D353",
    "walking": _VIOLET,
    "swimming": _PURPLE,
    "skiing": _TEXT,
    "trail running": _PINK,
}
_SPORT_ICONS: dict[str, str] = {
    "running": "🏃",
    "cycling": "🚴",
    "hiking": "🥾",
    "walking": "🚶",
    "swimming": "🏊",
    "skiing": "⛷",
    "trail running": "🏔",
}


def _fmt_pace(pace: float) -> str:
    mins = int(pace)
    secs = int((pace % 1) * 60)
    return f"{mins}'{secs:02d}\"/km"


def _fmt_duration_short(dur_s: float) -> str:
    h = int(dur_s // 3600)
    m = int((dur_s % 3600) // 60)
    return f"{h}h{m:02d}" if h > 0 else f"{m}min"


def build_activity_card(row: pd.Series) -> html.Div:
    """Construit une card cliquable pour une activité."""
    sport = str(row.get("sport_type", "unknown")).lower()
    border_color = _SPORT_COLORS.get(sport, _PURPLE)
    icon = _SPORT_ICONS.get(sport, "🏅")
    activity_id = int(row["activity_id"])

    km = row.get("total_distance_m", 0) / 1000
    dur_str = _fmt_duration_short(float(row.get("duration_s", 0)))

    pace = row.get("pace_min_per_km")
    pace_str = _fmt_pace(float(pace)) if (pace is not None and not pd.isna(pace)) else "—"

    hr = row.get("avg_heart_rate")
    hr_ok = hr is not None and not pd.isna(hr)

    try:
        date = pd.to_datetime(row["start_time"]).strftime("%d/%m/%Y")
    except Exception:
        date = str(row.get("start_time", ""))

    metrics: list = [
        html.Span(f"{km:.1f} km", style={"color": _TEXT, "fontFamily": "'Barlow Condensed', sans-serif", "fontWeight": "600"}),
        html.Span(" · ", style={"color": _PURPLE, "opacity": "0.6"}),
        html.Span(dur_str, style={"color": _TEXT, "fontFamily": "'Barlow Condensed', sans-serif", "fontWeight": "600"}),
        html.Span(" · ", style={"color": _PURPLE, "opacity": "0.6"}),
        html.Span(pace_str, style={"color": _CYAN, "fontFamily": "'Barlow Condensed', sans-serif", "fontWeight": "600"}),
    ]
    if hr_ok:
        metrics += [
            html.Span(" · ", style={"color": _PURPLE, "opacity": "0.6"}),
            html.Span(f"♥ {int(hr)} bpm", style={"color": _PINK, "fontFamily": "'Barlow Condensed', sans-serif", "fontWeight": "600"}),
        ]

    return html.Div(
        id={"type": "activity-card", "index": activity_id},
        n_clicks=0,
        children=[
            html.Div(
                [
                    html.Span(icon, style={"fontSize": "1.5rem", "lineHeight": "1"}),
                    html.Div(
                        [
                            html.Div(
                                str(row.get("name", f"Activité {activity_id}")),
                                style={
                                    "fontFamily": "'Barlow Condensed', sans-serif",
                                    "fontWeight": "700",
                                    "fontSize": "1rem",
                                    "color": _TEXT,
                                    "whiteSpace": "nowrap",
                                    "overflow": "hidden",
                                    "textOverflow": "ellipsis",
                                },
                            ),
                            html.Div(
                                f"{sport.capitalize()} · {date}",
                                style={
                                    "fontSize": "0.72rem",
                                    "color": _TEXT,
                                    "opacity": "0.45",
                                    "fontFamily": "'Barlow', sans-serif",
                                    "marginTop": "1px",
                                },
                            ),
                        ],
                        style={"flex": "1", "minWidth": "0"},
                    ),
                    html.Div(
                        "›",
                        style={
                            "color": _PURPLE,
                            "fontSize": "1.3rem",
                            "opacity": "0.6",
                            "fontFamily": "'Barlow Condensed', sans-serif",
                        },
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "0.75rem", "marginBottom": "0.5rem"},
            ),
            html.Div(metrics, style={"display": "flex", "alignItems": "center", "fontSize": "0.83rem", "flexWrap": "wrap"}),
        ],
        style={
            "background": _BG_CARD,
            "borderLeft": f"3px solid {border_color}",
            "borderRadius": "12px",
            "padding": "0.875rem 1rem",
            "marginBottom": "0.625rem",
            "cursor": "pointer",
        },
    )


def create_layout() -> html.Div:
    """Construit et retourne le layout complet de l'application."""
    activities = load_activities()
    hr_series = load_hr_series_all()
    weekly_kpis = load_weekly_kpis()

    if activities.empty:
        cards: list = [
            html.P(
                "Aucune activité — lancez get_data.py puis clean_data.py",
                style={"color": "rgba(238,238,245,0.4)", "fontFamily": "'Barlow', sans-serif", "padding": "2rem 0", "textAlign": "center"},
            )
        ]
        compare_options: list = []
    else:
        sorted_acts = activities.sort_values("start_time", ascending=False)
        cards = [build_activity_card(row) for _, row in sorted_acts.iterrows()]
        compare_options = [
            {
                "label": f"{row['name']} — {pd.to_datetime(row['start_time']).strftime('%d/%m/%Y')}",
                "value": int(row["activity_id"]),
            }
            for _, row in sorted_acts.iterrows()
        ]

    _dropdown_style = {
        "flex": "1",
        "minWidth": "200px",
        "color": "#0D0D14",
        "fontFamily": "'Barlow Condensed', sans-serif",
    }

    return html.Div(
        [
            dcc.Store(id="app-state", data={"view": "dashboard", "activity_id": None}),

            # ══════════════════════════════════════════════════════════════════
            # VUE 1 — Dashboard principal
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                id="view-dashboard",
                children=[
                    header_component(activities),

                    html.Div(
                        [
                            # ── Filtre par période ────────────────────────────
                            html.Div(
                                [
                                    html.Div("Filtrer par période", style=_SECTION_TITLE),
                                    html.Div(
                                        [
                                            dcc.DatePickerRange(
                                                id="date-filter",
                                                display_format="DD/MM/YYYY",
                                                clearable=True,
                                                start_date_placeholder_text="Début",
                                                end_date_placeholder_text="Fin",
                                            ),
                                            html.Div(
                                                id="filter-summary",
                                                style={
                                                    "color": _CYAN,
                                                    "fontFamily": "'Barlow Condensed', sans-serif",
                                                    "fontSize": "0.85rem",
                                                    "alignSelf": "center",
                                                },
                                            ),
                                        ],
                                        style={"display": "flex", "alignItems": "center", "gap": "1.5rem", "flexWrap": "wrap"},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Stats par sport + donut ───────────────────────
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div("Stats par sport", style=_SECTION_TITLE),
                                            dcc.Graph(
                                                id="sport-stats-table",
                                                figure=make_sport_stats_table(activities),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        style={**_CARD_STYLE, "flex": "1.3", "minWidth": "280px", "marginBottom": "0"},
                                    ),
                                    html.Div(
                                        [
                                            html.Div("Durée par sport", style=_SECTION_TITLE),
                                            dcc.Graph(
                                                id="sport-duration-pie",
                                                figure=make_sport_duration_pie(activities),
                                                config={"displayModeBar": False},
                                            ),
                                        ],
                                        style={**_CARD_STYLE, "flex": "1", "minWidth": "240px", "marginBottom": "0"},
                                    ),
                                ],
                                style={"display": "flex", "gap": "1rem", "flexWrap": "wrap", "marginBottom": "1rem"},
                            ),

                            # ── KPI hebdomadaires ─────────────────────────────
                            html.Div(
                                [
                                    html.Div("Distance hebdomadaire par sport", style=_SECTION_TITLE),
                                    dcc.Graph(
                                        id="weekly-distance-chart",
                                        figure=make_weekly_distance_chart(weekly_kpis),
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Histogramme FC global ─────────────────────────
                            html.Div(
                                [
                                    html.Div("Distribution FC globale", style=_SECTION_TITLE),
                                    html.Div(
                                        [
                                            html.Span("■ Z1 Récup", style={"color": "#00B4D8", "marginRight": "1rem", "fontSize": "0.7rem"}),
                                            html.Span("■ Z2 Endurance", style={"color": "#39D353", "marginRight": "1rem", "fontSize": "0.7rem"}),
                                            html.Span("■ Z3 Tempo", style={"color": "#EF9F27", "marginRight": "1rem", "fontSize": "0.7rem"}),
                                            html.Span("■ Z4 Seuil", style={"color": "#E040FB", "marginRight": "1rem", "fontSize": "0.7rem"}),
                                            html.Span("■ Z5 VO₂max", style={"color": "#F72585", "fontSize": "0.7rem"}),
                                        ],
                                        style={"display": "flex", "flexWrap": "wrap", "marginBottom": "0.5rem", "fontFamily": "'Barlow', sans-serif"},
                                    ),
                                    dcc.Graph(
                                        id="hr-histogram",
                                        figure=make_global_hr_histogram(hr_series),
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Charge d'entraînement (TRIMP) ─────────────────
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div("Charge d'entraînement hebdomadaire", style={**_SECTION_TITLE, "marginBottom": "0"}),
                                            html.Span(
                                                "TRIMP = durée × facteur zone FC  (vert < 40 % · orange < 70 % · rouge = charge élevée)",
                                                style={"fontSize": "0.7rem", "opacity": "0.45", "fontFamily": "'Barlow', sans-serif"},
                                            ),
                                        ],
                                        style={"marginBottom": "0.75rem"},
                                    ),
                                    dcc.Graph(
                                        id="trimp-chart",
                                        figure=make_trimp_chart(activities),
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Records personnels ────────────────────────────
                            html.Div(
                                [
                                    html.Div("Records personnels — course à pied", style=_SECTION_TITLE),
                                    dcc.Graph(
                                        id="personal-records",
                                        figure=make_personal_records_table(activities),
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Comparaison de deux activités ─────────────────
                            html.Div(
                                [
                                    html.Div("Comparer deux activités", style=_SECTION_TITLE),
                                    html.Div(
                                        [
                                            dcc.Dropdown(
                                                id="compare-activity-1",
                                                options=compare_options,
                                                placeholder="Activité 1...",
                                                style=_dropdown_style,
                                                clearable=True,
                                            ),
                                            dcc.Dropdown(
                                                id="compare-activity-2",
                                                options=compare_options,
                                                placeholder="Activité 2...",
                                                style=_dropdown_style,
                                                clearable=True,
                                            ),
                                        ],
                                        style={"display": "flex", "gap": "1rem", "marginBottom": "1rem", "flexWrap": "wrap"},
                                    ),
                                    dcc.Graph(
                                        id="compare-chart",
                                        figure=make_comparison_chart(pd.DataFrame(), pd.DataFrame()),
                                        config={"displayModeBar": False},
                                    ),
                                ],
                                style=_CARD_STYLE,
                            ),

                            # ── Activités récentes ────────────────────────────
                            html.Div(
                                [
                                    html.Div("Activités récentes", style=_SECTION_TITLE),
                                    html.Div(cards),
                                ],
                                style=_CARD_STYLE,
                            ),
                        ],
                        style={"maxWidth": "860px", "margin": "0 auto", "padding": "1.25rem 1rem 5rem"},
                    ),

                    # FAB centré fixe
                    html.Div(
                        html.Div(
                            "+",
                            style={
                                "background": f"linear-gradient(135deg, {_PINK}, {_VIOLET})",
                                "borderRadius": "28px",
                                "padding": "0.7rem 2.25rem",
                                "fontSize": "1.6rem",
                                "color": "white",
                                "fontWeight": "900",
                                "fontFamily": "'Barlow Condensed', sans-serif",
                                "cursor": "pointer",
                                "boxShadow": f"0 4px 24px rgba(247,37,133,0.4)",
                                "lineHeight": "1",
                            },
                        ),
                        style={
                            "position": "fixed",
                            "bottom": "1.5rem",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": "200",
                        },
                    ),
                ],
            ),

            # ══════════════════════════════════════════════════════════════════
            # VUE 2 — Détail d'une séance
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                id="view-detail",
                style={"display": "none"},
                children=[
                    html.Div(
                        [
                            html.Button("← Retour", id="btn-retour", n_clicks=0),
                        ],
                        style={
                            "padding": "0.875rem 1.5rem",
                            "background": _BG_MAIN,
                            "borderBottom": f"1px solid rgba(123,47,190,0.25)",
                            "position": "sticky",
                            "top": "0",
                            "zIndex": "90",
                        },
                    ),

                    html.Div(
                        [
                            html.Div(id="detail-header"),
                            html.Div(id="detail-hero-metrics"),

                            html.Div(
                                [
                                    html.Div("Tracé GPS", style=_SECTION_TITLE),
                                    dcc.Graph(
                                        id="detail-map",
                                        config={"scrollZoom": True, "displayModeBar": False},
                                        style={"borderRadius": "8px", "overflow": "hidden"},
                                    ),
                                ],
                                style={**_CARD_STYLE, "border": f"1px solid {_PURPLE}"},
                            ),

                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div("Courbes de performance", style={**_SECTION_TITLE, "marginBottom": "0"}),
                                            dcc.RadioItems(
                                                id="curves-x-mode",
                                                options=[
                                                    {"label": " Temps", "value": "time"},
                                                    {"label": " Distance", "value": "distance"},
                                                ],
                                                value="time",
                                                inline=True,
                                                style={"gap": "1rem"},
                                                inputStyle={"marginRight": "4px", "accentColor": _PINK},
                                                labelStyle={
                                                    "color": _TEXT,
                                                    "fontSize": "0.8rem",
                                                    "fontFamily": "'Barlow', sans-serif",
                                                    "cursor": "pointer",
                                                },
                                            ),
                                        ],
                                        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "0.75rem"},
                                    ),
                                    dcc.Graph(id="detail-curves", config={"displayModeBar": False}),
                                ],
                                style=_CARD_STYLE,
                            ),

                            html.Div(id="detail-weather"),
                        ],
                        style={"maxWidth": "860px", "margin": "0 auto", "padding": "1rem 1rem 2rem"},
                    ),
                ],
            ),
        ],
        style={"background": _BG_MAIN, "minHeight": "100vh", "color": _TEXT},
    )
