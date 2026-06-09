"""Tests unitaires pour src/transform/metrics.py."""

from __future__ import annotations

import pytest

from src.transform.metrics import (
    compute_avg_hr,
    compute_hr_zone,
    compute_max_hr,
    compute_pace,
    compute_speed,
)


# ─── Helpers de test ──────────────────────────────────────────────────────────


class _Point:
    """Implémente HasHeartRate pour les tests."""

    def __init__(self, hr: int | None) -> None:
        self.heart_rate = hr


# ─── compute_pace ─────────────────────────────────────────────────────────────


def test_compute_pace_valid() -> None:
    # 10 km en 50 min → allure 5 min/km
    result = compute_pace(10_000, 3_000)
    assert result == pytest.approx(5.0)


def test_compute_pace_half_marathon() -> None:
    # 21 095 m en 1h45 → ~4:58 min/km
    result = compute_pace(21_095, 6_300)
    assert result is not None
    assert result == pytest.approx(6_300 / 60 / (21_095 / 1000))


def test_compute_pace_zero_distance() -> None:
    assert compute_pace(0, 3_000) is None


def test_compute_pace_zero_duration() -> None:
    assert compute_pace(10_000, 0) is None


def test_compute_pace_negative_distance() -> None:
    assert compute_pace(-500, 3_000) is None


def test_compute_pace_negative_duration() -> None:
    assert compute_pace(10_000, -1) is None


# ─── compute_speed ────────────────────────────────────────────────────────────


def test_compute_speed_valid() -> None:
    # 10 km en 1 h → 10 km/h
    result = compute_speed(10_000, 3_600)
    assert result == pytest.approx(10.0)


def test_compute_speed_fast() -> None:
    # 100 m en 10 s → 36 km/h
    result = compute_speed(100, 10)
    assert result == pytest.approx(36.0)


def test_compute_speed_zero_distance() -> None:
    assert compute_speed(0, 3_600) is None


def test_compute_speed_zero_duration() -> None:
    assert compute_speed(10_000, 0) is None


# ─── compute_hr_zone ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("avg_hr", "max_hr", "expected_zone"),
    [
        (100, 190, 1),   # 52 % → zone 1 (< 60 %)
        (113, 190, 1),   # 59.5 % → zone 1 (strictement < 60 %)
        (120, 190, 2),   # 63 % → zone 2 (60–70 %)
        (132, 190, 2),   # 69.5 % → zone 2 (strictement < 70 %)
        (140, 190, 3),   # 73 % → zone 3 (70–80 %)
        (151, 190, 3),   # 79.5 % → zone 3 (strictement < 80 %)
        (160, 190, 4),   # 84 % → zone 4 (80–90 %)
        (170, 190, 4),   # 89 % → zone 4
        (180, 190, 5),   # 94 % → zone 5 (> 90 %)
        (190, 190, 5),   # 100 % → zone 5
    ],
)
def test_compute_hr_zone(avg_hr: float, max_hr: float, expected_zone: int) -> None:
    assert compute_hr_zone(avg_hr, max_hr) == expected_zone


def test_compute_hr_zone_default_max_hr() -> None:
    # FC max par défaut = 190 → 100/190 ≈ 52 % → zone 1
    assert compute_hr_zone(100) == 1


# ─── compute_avg_hr ───────────────────────────────────────────────────────────


def test_compute_avg_hr_valid() -> None:
    points = [_Point(100), _Point(120), _Point(140)]
    assert compute_avg_hr(points) == pytest.approx(120.0)


def test_compute_avg_hr_with_none_values() -> None:
    points = [_Point(100), _Point(None), _Point(140)]
    assert compute_avg_hr(points) == pytest.approx(120.0)


def test_compute_avg_hr_all_none() -> None:
    assert compute_avg_hr([_Point(None), _Point(None)]) is None


def test_compute_avg_hr_empty_list() -> None:
    assert compute_avg_hr([]) is None


def test_compute_avg_hr_single_value() -> None:
    assert compute_avg_hr([_Point(155)]) == pytest.approx(155.0)


# ─── compute_max_hr ───────────────────────────────────────────────────────────


def test_compute_max_hr_valid() -> None:
    points = [_Point(100), _Point(170), _Point(130)]
    assert compute_max_hr(points) == pytest.approx(170.0)


def test_compute_max_hr_with_none() -> None:
    points = [_Point(None), _Point(160), _Point(None)]
    assert compute_max_hr(points) == pytest.approx(160.0)


def test_compute_max_hr_empty_list() -> None:
    assert compute_max_hr([]) is None


def test_compute_max_hr_all_none() -> None:
    assert compute_max_hr([_Point(None)]) is None
