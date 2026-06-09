"""Tests unitaires pour src/transform/aggregations.py."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from src.transform.aggregations import compute_monthly_kpis, compute_weekly_kpis


# ─── Helper ───────────────────────────────────────────────────────────────────


def _row(
    date: str,
    sport: str = "running",
    distance_m: float = 10_000,
    duration_s: float = 3_600,
    pace: float | None = 6.0,
    speed: float | None = 10.0,
    temp: float | None = 15.0,
) -> dict[str, Any]:
    return {
        "start_time": datetime.fromisoformat(date),
        "sport_type": sport,
        "total_distance_m": distance_m,
        "duration_s": duration_s,
        "pace_min_per_km": pace,
        "speed_kmh": speed,
        "temperature_c": temp,
    }


# ─── compute_weekly_kpis ──────────────────────────────────────────────────────


def test_weekly_empty_input() -> None:
    assert compute_weekly_kpis([]) == []


def test_weekly_none_date_ignored() -> None:
    rows: list[dict[str, Any]] = [{"start_time": None, "sport_type": "running"}]
    assert compute_weekly_kpis(rows) == []


def test_weekly_single_activity() -> None:
    result = compute_weekly_kpis([_row("2024-01-08")])
    assert len(result) == 1
    assert result[0]["activity_count"] == 1
    assert result[0]["total_distance_m"] == pytest.approx(10_000)


def test_weekly_two_same_week_same_sport() -> None:
    rows = [_row("2024-01-08"), _row("2024-01-10")]
    result = compute_weekly_kpis(rows)
    assert len(result) == 1
    assert result[0]["activity_count"] == 2
    assert result[0]["total_distance_m"] == pytest.approx(20_000)
    assert result[0]["total_duration_s"] == pytest.approx(7_200)


def test_weekly_two_different_weeks() -> None:
    rows = [_row("2024-01-08"), _row("2024-01-15")]
    result = compute_weekly_kpis(rows)
    assert len(result) == 2


def test_weekly_different_sports_same_week() -> None:
    rows = [_row("2024-01-08", sport="running"), _row("2024-01-08", sport="cycling")]
    result = compute_weekly_kpis(rows)
    assert len(result) == 2
    sports = {r["sport_type"] for r in result}
    assert sports == {"running", "cycling"}


def test_weekly_avg_pace_computed() -> None:
    rows = [_row("2024-01-08", pace=5.0), _row("2024-01-10", pace=7.0)]
    result = compute_weekly_kpis(rows)
    assert result[0]["avg_pace_min_per_km"] == pytest.approx(6.0)


def test_weekly_avg_pace_none_when_missing() -> None:
    rows = [_row("2024-01-08", pace=None), _row("2024-01-10", pace=None)]
    result = compute_weekly_kpis(rows)
    assert result[0]["avg_pace_min_per_km"] is None


def test_weekly_sorted_by_year_week_sport() -> None:
    rows = [_row("2024-01-22"), _row("2024-01-08")]
    result = compute_weekly_kpis(rows)
    assert result[0]["week"] < result[1]["week"]


# ─── compute_monthly_kpis ─────────────────────────────────────────────────────


def test_monthly_empty_input() -> None:
    assert compute_monthly_kpis([]) == []


def test_monthly_single_activity() -> None:
    result = compute_monthly_kpis([_row("2024-01-08")])
    assert len(result) == 1
    assert result[0]["year"] == 2024
    assert result[0]["month"] == 1


def test_monthly_two_same_month() -> None:
    rows = [_row("2024-01-08"), _row("2024-01-20")]
    result = compute_monthly_kpis(rows)
    assert len(result) == 1
    assert result[0]["activity_count"] == 2


def test_monthly_two_different_months() -> None:
    rows = [_row("2024-01-08"), _row("2024-02-05")]
    result = compute_monthly_kpis(rows)
    assert len(result) == 2


def test_monthly_cross_year() -> None:
    rows = [_row("2023-12-28"), _row("2024-01-02")]
    result = compute_monthly_kpis(rows)
    assert len(result) == 2
    assert result[0]["year"] == 2023
    assert result[1]["year"] == 2024


def test_monthly_avg_temperature() -> None:
    rows = [_row("2024-06-01", temp=20.0), _row("2024-06-15", temp=30.0)]
    result = compute_monthly_kpis(rows)
    assert result[0]["avg_temperature_c"] == pytest.approx(25.0)
