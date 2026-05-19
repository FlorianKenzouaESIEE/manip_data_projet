"""Orchestrateur de nettoyage et d'enrichissement des données sportives.

Workflow :
1. Lit les activités depuis dashsport_raw.db.
2. Calcule les métriques métier (allure, vitesse, zones FC).
3. Enrichit chaque activité avec les données météo du cache local.
4. Persiste les résultats dans dashsport_clean.db (table activities_clean).
5. Calcule les agrégats KPI hebdomadaires et mensuels.

Usage :
    python clean_data.py

Pré-requis :
    python get_data.py  (construit dashsport_raw.db)
"""

from __future__ import annotations

import sys
from pathlib import Path

from src.models import Activity, TrackPoint, get_session
from src.models_clean import (
    ActivityClean,
    MonthlyKPI,
    WeeklyKPI,
    create_clean_database,
    get_clean_session,
)
from src.transform.aggregations import compute_monthly_kpis, compute_weekly_kpis
from src.transform.metrics import (
    compute_avg_hr,
    compute_hr_zone,
    compute_max_hr,
    compute_pace,
    compute_speed,
)
from src.weather.cache import get_weather

_PROJECT_ROOT = Path(__file__).parent
_RAW_DB = _PROJECT_ROOT / "data" / "dashsport_raw.db"


# ─── Vérifications préalables ─────────────────────────────────────────────────


def _check_raw_db() -> None:
    """Vérifie que la base brute existe et interrompt le script sinon."""
    if not _RAW_DB.exists():
        print("Erreur : data/dashsport_raw.db introuvable.")
        print("Lancez d'abord : python get_data.py")
        sys.exit(1)


# ─── Construction des enregistrements clean ───────────────────────────────────


def _build_activity_clean(
    activity: Activity, track_points: list[TrackPoint]
) -> ActivityClean:
    """Construit un enregistrement ActivityClean à partir des données brutes.

    Args:
        activity: Activité lue depuis dashsport_raw.db.
        track_points: Points de trace associés à cette activité.

    Returns:
        Instance ActivityClean prête à être insérée dans dashsport_clean.db.
    """
    dist = activity.total_distance_m
    dur = activity.duration_s

    pace = compute_pace(dist, dur) if dist and dur else None
    speed = compute_speed(dist, dur) if dist and dur else None
    avg_hr = compute_avg_hr(track_points)
    max_hr = compute_max_hr(track_points)
    hr_zone = compute_hr_zone(avg_hr) if avg_hr is not None else None

    weather = None
    if (
        activity.start_lat is not None
        and activity.start_lon is not None
        and activity.start_time is not None
    ):
        weather = get_weather(activity.start_lat, activity.start_lon, activity.start_time)

    return ActivityClean(
        activity_id=activity.id,
        source_file=activity.source_file,
        name=activity.name,
        sport_type=activity.sport_type,
        start_time=activity.start_time,
        duration_s=dur,
        total_distance_m=dist,
        start_lat=activity.start_lat,
        start_lon=activity.start_lon,
        pace_min_per_km=pace,
        speed_kmh=speed,
        avg_heart_rate=avg_hr,
        max_heart_rate=max_hr,
        hr_zone=hr_zone,
        temperature_c=weather.temperature_c if weather else None,
        wind_speed_kmh=weather.wind_speed_kmh if weather else None,
        precipitation_mm=weather.precipitation_mm if weather else None,
        humidity_pct=weather.humidity_pct if weather else None,
        weather_code=weather.weather_code if weather else None,
    )


# ─── Étapes d'exécution ───────────────────────────────────────────────────────


def run_enrichment() -> None:
    """Lit la base brute, calcule les métriques, et peuple activities_clean."""
    raw_session = get_session(str(_RAW_DB))
    clean_session = get_clean_session()

    activities: list[Activity] = raw_session.query(Activity).all()
    existing_ids: set[int] = {
        row[0] for row in clean_session.query(ActivityClean.activity_id).all()
    }

    new_count = 0
    skip_count = 0

    for act in activities:
        if act.id in existing_ids:
            skip_count += 1
            continue

        track_points: list[TrackPoint] = (
            raw_session.query(TrackPoint)
            .filter(TrackPoint.activity_id == act.id)
            .all()
        )
        clean_row = _build_activity_clean(act, track_points)
        clean_session.add(clean_row)
        new_count += 1

        weather_flag = "☁" if clean_row.temperature_c is not None else "—"
        print(
            f"  ✓ {act.name} | {act.sport_type} | "
            f"{clean_row.speed_kmh:.1f} km/h | "
            f"allure {clean_row.pace_min_per_km:.2f} min/km | "
            f"météo {weather_flag}"
            if clean_row.speed_kmh and clean_row.pace_min_per_km
            else f"  ✓ {act.name} | {act.sport_type}"
        )

    clean_session.commit()
    raw_session.close()
    clean_session.close()

    print(f"\n  → {new_count} activité(s) enrichie(s), {skip_count} déjà présente(s).")


def run_aggregations() -> None:
    """Calcule et persiste les KPI hebdomadaires et mensuels."""
    clean_session = get_clean_session()
    activities: list[ActivityClean] = clean_session.query(ActivityClean).all()

    rows = [
        {
            "start_time": a.start_time,
            "sport_type": a.sport_type,
            "total_distance_m": a.total_distance_m,
            "duration_s": a.duration_s,
            "pace_min_per_km": a.pace_min_per_km,
            "speed_kmh": a.speed_kmh,
            "temperature_c": a.temperature_c,
        }
        for a in activities
    ]

    # Recalcul complet à chaque exécution (idempotent)
    clean_session.query(WeeklyKPI).delete()
    for kpi in compute_weekly_kpis(rows):
        clean_session.add(WeeklyKPI(**kpi))

    clean_session.query(MonthlyKPI).delete()
    for kpi in compute_monthly_kpis(rows):
        clean_session.add(MonthlyKPI(**kpi))

    clean_session.commit()

    weekly_count = clean_session.query(WeeklyKPI).count()
    monthly_count = clean_session.query(MonthlyKPI).count()
    clean_session.close()

    print(f"  → {weekly_count} semaine(s) et {monthly_count} mois agrégés.")


# ─── Point d'entrée ───────────────────────────────────────────────────────────


def main() -> None:
    """Point d'entrée principal de clean_data.py."""
    print("=" * 70)
    print("DASHSPORT — Nettoyage et enrichissement des données")
    print("=" * 70)

    _check_raw_db()
    create_clean_database()

    print("\n[1/2] Enrichissement des activités...")
    run_enrichment()

    print("\n[2/2] Calcul des agrégats KPI...")
    run_aggregations()

    print("\n" + "=" * 70)
    print("✓ Base dashsport_clean.db mise à jour.")
    print("=" * 70)


if __name__ == "__main__":
    main()
