"""Tests unitaires pour src/ingestion/parse_fit.py.

Les fonctions pures (_haversine_m, _semicircles_to_degrees) sont testées
directement. Le parsing complet nécessiterait un fichier .fit binaire,
donc seul le cas FileNotFoundError est vérifié pour parse_fit().
"""

from __future__ import annotations

import pytest

from src.ingestion.parse_fit import _haversine_m, _semicircles_to_degrees, parse_fit


# ─── _haversine_m ─────────────────────────────────────────────────────────────


def test_haversine_same_point() -> None:
    assert _haversine_m(48.86, 2.35, 48.86, 2.35) == pytest.approx(0.0)


def test_haversine_known_distance_paris_north() -> None:
    # ~0.1° de latitude ≈ ~11 km
    dist = _haversine_m(48.85, 2.35, 48.95, 2.35)
    assert 10_000 < dist < 12_000


def test_haversine_symmetry() -> None:
    d1 = _haversine_m(48.85, 2.35, 48.95, 2.40)
    d2 = _haversine_m(48.95, 2.40, 48.85, 2.35)
    assert d1 == pytest.approx(d2)


def test_haversine_positive() -> None:
    assert _haversine_m(0.0, 0.0, 1.0, 1.0) > 0.0


# ─── _semicircles_to_degrees ──────────────────────────────────────────────────


def test_semicircles_none_returns_none() -> None:
    assert _semicircles_to_degrees(None) is None


def test_semicircles_full_circle() -> None:
    # 2^31 semicircles = 180°
    assert _semicircles_to_degrees(2**31) == pytest.approx(180.0)


def test_semicircles_zero() -> None:
    assert _semicircles_to_degrees(0) == pytest.approx(0.0)


def test_semicircles_negative() -> None:
    # -2^31 = -180°
    assert _semicircles_to_degrees(-(2**31)) == pytest.approx(-180.0)


# ─── parse_fit — cas d'erreur ─────────────────────────────────────────────────


def test_parse_fit_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        parse_fit("/nonexistent/activity.fit")
