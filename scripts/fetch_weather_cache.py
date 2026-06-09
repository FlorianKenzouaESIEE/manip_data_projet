"""Script développeur : pré-télécharge les données météo Open-Meteo pour toutes les activités.

À exécuter une seule fois (ou après ajout de nouvelles activités) puis commiter
data/weather_cache.json pour que le projet fonctionne hors-ligne.

Pré-requis : python get_data.py doit avoir été exécuté.
API utilisée : Open-Meteo Archive (https://archive-api.open-meteo.com) — gratuite, sans clé.

Usage :
    python scripts/fetch_weather_cache.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import timezone
from pathlib import Path

# Permet d'importer src.* depuis la racine du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import Activity, get_session  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
CACHE_PATH = _PROJECT_ROOT / "data" / "weather_cache.json"
_RAW_DB = _PROJECT_ROOT / "data" / "dashsport_raw.db"

_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
_HOURLY_VARS = (
    "temperature_2m,windspeed_10m,weathercode,precipitation,relativehumidity_2m"
)


def _fetch_daily_hourly(lat: float, lon: float, date: str) -> dict[str, list]:
    """Récupère les données horaires Open-Meteo Archive pour une journée entière.

    Args:
        lat: Latitude arrondie à 2 décimales.
        lon: Longitude arrondie à 2 décimales.
        date: Date au format YYYY-MM-DD.

    Returns:
        Dictionnaire des séries horaires retournées par l'API.

    Raises:
        urllib.error.URLError: Si la requête réseau échoue.
        KeyError: Si la réponse JSON ne contient pas la clé attendue.
    """
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "start_date": date,
            "end_date": date,
            "hourly": _HOURLY_VARS,
            "timezone": "UTC",
            "wind_speed_unit": "kmh",
        }
    )
    url = f"{_BASE_URL}?{params}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data: dict = json.loads(resp.read().decode("utf-8"))
    return data["hourly"]  # type: ignore[return-value]


def _build_entries(lat: float, lon: float, hourly: dict[str, list]) -> dict[str, dict]:
    """Construit les entrées du cache à partir des séries horaires brutes.

    Args:
        lat: Latitude arrondie à 2 décimales (partie de la clé de cache).
        lon: Longitude arrondie à 2 décimales (partie de la clé de cache).
        hourly: Données horaires retournées par _fetch_daily_hourly.

    Returns:
        Dict {clé_cache: snapshot_dict} pour les 24 heures de la journée.
        Clé au format "{lat}_{lon}_{YYYY-MM-DDTHH}".
    """
    entries: dict[str, dict] = {}
    times: list[str] = hourly.get("time", [])

    def _safe(series: list, i: int) -> float | None:
        return series[i] if series and i < len(series) else None

    temps = hourly.get("temperature_2m", [])
    winds = hourly.get("windspeed_10m", [])
    codes = hourly.get("weathercode", [])
    precip = hourly.get("precipitation", [])
    humid = hourly.get("relativehumidity_2m", [])

    for i, t in enumerate(times):
        key = f"{lat}_{lon}_{t}"
        raw_code = _safe(codes, i)
        entries[key] = {
            "temperature_c": _safe(temps, i),
            "wind_speed_kmh": _safe(winds, i),
            "precipitation_mm": _safe(precip, i),
            "humidity_pct": _safe(humid, i),
            "weather_code": int(raw_code) if raw_code is not None else None,
        }
    return entries


def main() -> None:
    """Orchestre le téléchargement météo et la mise à jour du cache JSON."""
    if not _RAW_DB.exists():
        print("Erreur : data/dashsport_raw.db introuvable.")
        print("Lancez d'abord : python get_data.py")
        return

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Chargement du cache existant (mise à jour incrémentale)
    cache: dict[str, dict] = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            cache = json.load(f)
        print(f"Cache existant chargé : {len(cache)} entrées.\n")

    session = get_session(str(_RAW_DB))
    activities: list[Activity] = (
        session.query(Activity)
        .filter(
            Activity.start_lat.isnot(None),
            Activity.start_lon.isnot(None),
            Activity.start_time.isnot(None),
        )
        .all()
    )
    session.close()

    if not activities:
        print("Aucune activité avec coordonnées GPS dans la base brute.")
        return

    seen: set[tuple[float, float, str]] = set()
    new_entries = 0

    for act in activities:
        lat = round(act.start_lat, 2)  # type: ignore[arg-type]
        lon = round(act.start_lon, 2)  # type: ignore[arg-type]
        dt = act.start_time
        if dt is None:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")

        key_tuple = (lat, lon, date_str)
        if key_tuple in seen:
            continue
        seen.add(key_tuple)

        # Vérifie si la journée est déjà en cache
        sample_key = f"{lat}_{lon}_{date_str}T00:00"
        if sample_key in cache:
            print(f"  Déjà en cache : {act.name} ({date_str})")
            continue

        print(
            f"  Téléchargement : {act.name} — {date_str} @ ({lat}, {lon}) ...",
            end=" ",
            flush=True,
        )
        try:
            hourly = _fetch_daily_hourly(lat, lon, date_str)
            entries = _build_entries(lat, lon, hourly)
            cache.update(entries)
            new_entries += len(entries)
            print(f"OK ({len(entries)} heures)")
            time.sleep(0.5)  # courtoisie envers l'API
        except Exception as exc:
            print(f"ERREUR : {exc}")

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(
        f"\nCache météo sauvegardé : {len(cache)} entrées totales "
        f"(+{new_entries} nouvelles)."
    )
    print(f"Fichier : {CACHE_PATH}")


if __name__ == "__main__":
    main()
