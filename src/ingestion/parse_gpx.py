"""Parsing des fichiers .gpx issus de l'export Strava.

Entrée  : chemin vers un fichier .gpx (UTF-8)
Sortie  : ParsedGPXActivity — dataclass typée contenant les points GPS
          et les métadonnées de l'activité.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import Element

import gpxpy
import gpxpy.gpx


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
class ParsedGPXActivity:
    """Résultat structuré du parsing d'un fichier .gpx."""

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


def _extract_hr_cadence(
    point: gpxpy.gpx.GPXTrackPoint,
) -> tuple[Optional[int], Optional[int]]:
    """Extrait FC et cadence depuis les extensions Garmin/Strava d'un point GPX.

    Strava génère des extensions sous la forme :
        <gpxtpx:TrackPointExtension>
            <gpxtpx:hr>150</gpxtpx:hr>
            <gpxtpx:cad>85</gpxtpx:cad>
        </gpxtpx:TrackPointExtension>
    """
    hr: Optional[int] = None
    cad: Optional[int] = None

    if not point.extensions:
        return hr, cad

    for ext in point.extensions:
        if not isinstance(ext, Element):
            continue

        # L'extension est soit le conteneur TrackPointExtension, soit un tag direct
        tag = ext.tag.split("}")[-1] if "}" in ext.tag else ext.tag

        # Cas 1 : conteneur TrackPointExtension → on descend d'un niveau
        children = list(ext) if "TrackPointExtension" in tag else [ext]

        for child in children:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_tag in ("hr", "heartrate") and child.text:
                try:
                    hr = int(child.text)
                except ValueError:
                    pass
            elif child_tag in ("cad", "cadence") and child.text:
                try:
                    cad = int(child.text)
                except ValueError:
                    pass

    return hr, cad


# ─── Fonction publique ────────────────────────────────────────────────────────


def parse_gpx(file_path: str | Path) -> ParsedGPXActivity:
    """Parse un fichier .gpx Strava et retourne une ParsedGPXActivity.

    Args:
        file_path: Chemin absolu ou relatif vers le fichier .gpx.

    Returns:
        ParsedGPXActivity avec tous les points et métadonnées.

    Raises:
        FileNotFoundError: Le fichier n'existe pas.
        ValueError: Le fichier est invalide ou ne contient aucun point GPS.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with path.open("r", encoding="utf-8") as fh:
        gpx = gpxpy.parse(fh)

    name = gpx.name or path.stem

    sport_type = "Unknown"
    if gpx.tracks and gpx.tracks[0].type:
        sport_type = gpx.tracks[0].type

    # Collecte tous les points de tous les segments du premier track
    raw_points: list[gpxpy.gpx.GPXTrackPoint] = []
    for track in gpx.tracks:
        for segment in track.segments:
            raw_points.extend(segment.points)

    if not raw_points:
        raise ValueError(f"Aucun point GPS dans {path.name}")

    first_ts = raw_points[0].time
    if first_ts is None:
        raise ValueError(f"Premier point sans timestamp dans {path.name}")

    # Construction des TrackPoints typés avec distance cumulée
    points: list[TrackPoint] = []
    cumulative = 0.0

    for raw in raw_points:
        if raw.time is None or raw.latitude is None or raw.longitude is None:
            continue  # point incomplet → ignoré

        if points:
            prev = points[-1]
            cumulative += _haversine_m(prev.lat, prev.lon, raw.latitude, raw.longitude)

        hr, cad = _extract_hr_cadence(raw)

        points.append(
            TrackPoint(
                lat=raw.latitude,
                lon=raw.longitude,
                elevation=raw.elevation,
                timestamp=raw.time,
                heart_rate=hr,
                cadence=cad,
                cumulative_distance_m=cumulative,
            )
        )

    if not points:
        raise ValueError(f"Aucun point valide (lat/lon/time) dans {path.name}")

    return ParsedGPXActivity(
        source_file=str(path),
        name=name,
        sport_type=sport_type,
        start_time=first_ts,
        points=points,
    )
