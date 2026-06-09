"""Tests unitaires pour src/weather/cache.py."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.weather.cache import WeatherSnapshot, _cache_key, get_weather

# ─── _cache_key ───────────────────────────────────────────────────────────────


def test_cache_key_format() -> None:
    key = _cache_key(48.8566, 2.3522, datetime(2024, 6, 1, 7, 30, 0))
    assert key == "48.86_2.35_2024-06-01T07:00"


def test_cache_key_truncates_minutes_seconds() -> None:
    k1 = _cache_key(48.86, 2.35, datetime(2024, 6, 1, 7, 0, 0))
    k2 = _cache_key(48.86, 2.35, datetime(2024, 6, 1, 7, 59, 59))
    assert k1 == k2


def test_cache_key_rounds_coordinates() -> None:
    # 48.856 arrondi à 2 décimales → 48.86
    key = _cache_key(48.856, 2.352, datetime(2024, 1, 1, 0, 0, 0))
    assert key.startswith("48.86_2.35_")


# ─── get_weather ──────────────────────────────────────────────────────────────

_SAMPLE_CACHE = {
    "48.86_2.35_2024-06-01T07:00": {
        "temperature_c": 18.5,
        "wind_speed_kmh": 12.0,
        "precipitation_mm": 0.0,
        "humidity_pct": 65.0,
        "weather_code": 1,
    }
}


@pytest.fixture
def cache_file(tmp_path: Path) -> Path:
    p = tmp_path / "weather_cache.json"
    p.write_text(json.dumps(_SAMPLE_CACHE), encoding="utf-8")
    return p


def test_get_weather_returns_snapshot(cache_file: Path) -> None:
    with patch("src.weather.cache.CACHE_PATH", cache_file):
        result = get_weather(48.8566, 2.3522, datetime(2024, 6, 1, 7, 0, 0))
    assert isinstance(result, WeatherSnapshot)
    assert result.temperature_c == pytest.approx(18.5)
    assert result.wind_speed_kmh == pytest.approx(12.0)
    assert result.weather_code == 1


def test_get_weather_missing_key_returns_none(cache_file: Path) -> None:
    with patch("src.weather.cache.CACHE_PATH", cache_file):
        result = get_weather(0.0, 0.0, datetime(2024, 1, 1, 0, 0, 0))
    assert result is None


def test_get_weather_no_cache_file_returns_none() -> None:
    with patch("src.weather.cache.CACHE_PATH", Path("/nonexistent/weather_cache.json")):
        result = get_weather(48.86, 2.35, datetime(2024, 6, 1, 7, 0, 0))
    assert result is None


def test_get_weather_weather_code_is_int(cache_file: Path) -> None:
    with patch("src.weather.cache.CACHE_PATH", cache_file):
        result = get_weather(48.8566, 2.3522, datetime(2024, 6, 1, 7, 0, 0))
    assert result is not None
    assert isinstance(result.weather_code, int)
