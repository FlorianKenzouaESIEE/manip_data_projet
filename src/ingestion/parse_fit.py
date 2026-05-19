"""Parsing des fichiers .fit et .fit.gz issus de l'export Strava.

Entrée  : chemin vers un fichier .fit ou .fit.gz
Sortie  : ParsedFITActivity — dataclass typée contenant les points GPS
          et les métadonnées de l'activité.
"""

from __future__ import annotations

import gzip
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from fitparse import FitFile


# ─── Structures de données ────────────────────────────────────────────────────


@dataclass
class TrackPoint:
    """Un point GPS horodaté avec métriques optionnelles."""

    lat: float
    lon: float
    elevation: Optional[float]
    timestamp: datetime
    heart_rate: Optional[int]
    cadence: Optional[int]
    cumulative_distance_m: float  # distance cumulée depuis le départ


@dataclass
class ParsedFITActivity:
    """Résultat structuré du parsing d'un fichier .fit/.fit.gz."""

    source_file: str
    name: str
    sport_type: str
    start_time: datetime
    points: list[TrackPoint] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        """Durée totale en secondes (premier → dernier point horodaté)."""
        if len(self.points) < 2:
            return 0.0
        return (self.points[-1].timestamp - self.points[0].timestamp).total_seconds()

    @property
    def total_distance_m(self) -> float:
        """Distance totale en mètres (valeur du dernier point)."""
        return self.points[-1].cumulative_distance_m if self.points else 0.0

    @property
    def start_lat(self) -> Optional[float]:
        """Latitude du point de départ."""
        return self.points[0].lat if self.points else None

    @property
    def start_lon(self) -> Optional[float]:
        """Longitude du point de départ."""
        return self.points[0].lon if self.points else None


# ─── Helpers privés ───────────────────────────────────────────────────────────


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance orthodromique en mètres entre deux points GPS."""
    R = 6_371_000  # rayon terrestre moyen
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _semicircles_to_degrees(semicircles: Optional[int]) -> Optional[float]:
    """Convertit les semicircles FIT (2^31 = 180°) en degrés décimaux."""
    if semicircles is None:
        return None
    return semicircles * (180.0 / 2**31)


def _get_sport_type(fit_file: FitFile) -> str:
    """Extrait le type de sport depuis les messages 'sport' ou 'session'."""
    for record in fit_file.get_messages("sport"):
        sport = record.get_value("sport")
        if sport:
            return str(sport)

    for record in fit_file.get_messages("session"):
        sport = record.get_value("sport")
        if sport:
            return str(sport)

    return "Unknown"


def _get_activity_name(fit_file: FitFile, file_stem: str) -> str:
    """Extrait le nom de l'activité depuis les messages 'file_id' ou 'session'."""
    for record in fit_file.get_messages("file_id"):
        name = record.get_value("time_created")
        if name:
            return str(name)

    for record in fit_file.get_messages("session"):
        name = record.get_value("start_time")
        if name:
            return str(name)

    return file_stem


# ─── Fonction publique ────────────────────────────────────────────────────────


def parse_fit(file_path: str | Path) -> ParsedFITActivity:
    """Parse un fichier .fit ou .fit.gz Strava et retourne une ParsedFITActivity.

    Args:
        file_path: Chemin absolu ou relatif vers le fichier .fit ou .fit.gz.

    Returns:
        ParsedFITActivity avec tous les points et métadonnées.

    Raises:
        FileNotFoundError: Le fichier n'existe pas.
        ValueError: Le fichier est invalide ou ne contient aucun point GPS.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    # Gestion des fichiers .fit.gz
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as gz_file:
            fit_file = FitFile(gz_file)
    else:
        fit_file = FitFile(str(path))

    # Extraction des métadonnées
    sport_type = _get_sport_type(fit_file)
    name = _get_activity_name(fit_file, path.stem)

    # Collecte des points GPS depuis les messages 'record'
    points: list[TrackPoint] = []
    cumulative = 0.0
    first_timestamp: Optional[datetime] = None

    for record in fit_file.get_messages("record"):
        # Extraction des valeurs brutes
        lat_raw = record.get_value("position_lat")
        lon_raw = record.get_value("position_long")
        timestamp = record.get_value("timestamp")
        elevation = record.get_value("altitude")
        heart_rate = record.get_value("heart_rate")
        cadence = record.get_value("cadence")

        # Validation des données essentielles
        if lat_raw is None or lon_raw is None or timestamp is None:
            continue

        lat = _semicircles_to_degrees(lat_raw)
        lon = _semicircles_to_degrees(lon_raw)

        if lat is None or lon is None:
            continue

        # Premier timestamp valide
        if first_timestamp is None:
            first_timestamp = timestamp

        # Calcul de la distance cumulée
        if points:
            prev = points[-1]
            cumulative += _haversine_m(prev.lat, prev.lon, lat, lon)

        points.append(
            TrackPoint(
                lat=lat,
                lon=lon,
                elevation=elevation,
                timestamp=timestamp,
                heart_rate=heart_rate,
                cadence=cadence,
                cumulative_distance_m=cumulative,
            )
        )

    if not points:
        raise ValueError(f"Aucun point GPS valide dans {path.name}")

    if first_timestamp is None:
        raise ValueError(f"Aucun timestamp valide dans {path.name}")

    return ParsedFITActivity(
        source_file=str(path),
        name=name,
        sport_type=sport_type,
        start_time=first_timestamp,
        points=points,
    )

# Made with Bob
