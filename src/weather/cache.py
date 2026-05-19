"""Lecture des données météo historiques depuis le cache JSON local.

Le cache est pré-téléchargé par scripts/fetch_weather_cache.py (exécuté une
fois en développement) et versionné dans data/weather_cache.json.
Aucune connexion réseau n'est requise à l'exécution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Chemin absolu depuis la position du module
CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "weather_cache.json"


@dataclass
class WeatherSnapshot:
    """Données météo horaires pour un lieu et une heure donnés."""

    temperature_c: float | None
    wind_speed_kmh: float | None
    precipitation_mm: float | None
    humidity_pct: float | None
    weather_code: int | None


def _cache_key(lat: float, lon: float, dt: datetime) -> str:
    """Retourne la clé du cache au format {lat_r2}_{lon_r2}_{YYYY-MM-DDTHH}."""
    return f"{round(lat, 2)}_{round(lon, 2)}_{dt.strftime('%Y-%m-%dT%H')}"


def get_weather(lat: float, lon: float, dt: datetime) -> WeatherSnapshot | None:
    """Retourne le snapshot météo depuis le cache local pour un point GPS et une heure.

    La résolution spatiale est de 0,01° (~1 km). L'heure est celle de l'activité
    (minutes et secondes ignorées — on utilise l'heure pleine).

    Args:
        lat: Latitude du point de départ de l'activité.
        lon: Longitude du point de départ de l'activité.
        dt: Horodatage de début d'activité.

    Returns:
        WeatherSnapshot si l'entrée est présente dans le cache, None sinon.
    """
    if not CACHE_PATH.exists():
        return None

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache: dict[str, dict[str, float | int | None]] = json.load(f)

    key = _cache_key(lat, lon, dt)
    entry = cache.get(key)
    if entry is None:
        return None

    return WeatherSnapshot(
        temperature_c=entry.get("temperature_c"),
        wind_speed_kmh=entry.get("wind_speed_kmh"),
        precipitation_mm=entry.get("precipitation_mm"),
        humidity_pct=entry.get("humidity_pct"),
        weather_code=entry.get("weather_code"),
    )
