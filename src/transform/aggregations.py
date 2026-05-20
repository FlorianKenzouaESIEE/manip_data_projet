"""Calcul des agrégats KPI hebdomadaires et mensuels.

Toutes les fonctions sont pures : elles prennent des listes de dicts et
retournent des listes de dicts, sans accès à la base de données.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any


def _iso_week(dt: datetime) -> tuple[int, int]:
    """Retourne (année ISO, numéro de semaine ISO) pour une datetime.

    Utilise isocalendar() : la semaine 1 est celle qui contient le premier
    jeudi de janvier (norme ISO 8601).
    """
    iso = dt.isocalendar()
    return int(iso.year), int(iso.week)


def _safe_avg(values: list[float]) -> float | None:
    """Calcule la moyenne d'une liste non vide, ou None si la liste est vide."""
    return sum(values) / len(values) if values else None


def compute_weekly_kpis(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calcule les KPI agrégés par semaine ISO et type de sport.

    Args:
        rows: Liste de dicts avec les clés start_time (datetime), sport_type,
              total_distance_m, duration_s, pace_min_per_km, speed_kmh,
              temperature_c. Les valeurs manquantes (None) sont tolérées.

    Returns:
        Liste de dicts triés par (year, week, sport_type), prêts à insérer
        dans la table weekly_kpis.
    """
    buckets: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        dt: datetime | None = row.get("start_time")
        if dt is None:
            continue
        year, week = _iso_week(dt)
        sport = row.get("sport_type") or "unknown"
        buckets[(year, week, sport)].append(row)

    results: list[dict[str, Any]] = []
    for (year, week, sport), group in sorted(buckets.items()):
        paces = [r["pace_min_per_km"] for r in group if r.get("pace_min_per_km") is not None]
        speeds = [r["speed_kmh"] for r in group if r.get("speed_kmh") is not None]
        temps = [r["temperature_c"] for r in group if r.get("temperature_c") is not None]

        results.append(
            {
                "year": year,
                "week": week,
                "sport_type": sport,
                "activity_count": len(group),
                "total_distance_m": sum(r.get("total_distance_m") or 0.0 for r in group),
                "total_duration_s": sum(r.get("duration_s") or 0.0 for r in group),
                "avg_pace_min_per_km": _safe_avg(paces),
                "avg_speed_kmh": _safe_avg(speeds),
                "avg_temperature_c": _safe_avg(temps),
            }
        )

    return results


def compute_monthly_kpis(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calcule les KPI agrégés par mois calendaire et type de sport.

    Args:
        rows: Même structure que pour compute_weekly_kpis.

    Returns:
        Liste de dicts triés par (year, month, sport_type), prêts à insérer
        dans la table monthly_kpis.
    """
    buckets: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        dt: datetime | None = row.get("start_time")
        if dt is None:
            continue
        sport = row.get("sport_type") or "unknown"
        buckets[(dt.year, dt.month, sport)].append(row)

    results: list[dict[str, Any]] = []
    for (year, month, sport), group in sorted(buckets.items()):
        paces = [r["pace_min_per_km"] for r in group if r.get("pace_min_per_km") is not None]
        speeds = [r["speed_kmh"] for r in group if r.get("speed_kmh") is not None]
        temps = [r["temperature_c"] for r in group if r.get("temperature_c") is not None]

        results.append(
            {
                "year": year,
                "month": month,
                "sport_type": sport,
                "activity_count": len(group),
                "total_distance_m": sum(r.get("total_distance_m") or 0.0 for r in group),
                "total_duration_s": sum(r.get("duration_s") or 0.0 for r in group),
                "avg_pace_min_per_km": _safe_avg(paces),
                "avg_speed_kmh": _safe_avg(speeds),
                "avg_temperature_c": _safe_avg(temps),
            }
        )

    return results
