"""Calcul des métriques sportives : allure, vitesse, zones de fréquence cardiaque.

Toutes les fonctions sont pures (sans effet de bord) et peuvent être testées
unitairement sans base de données.
"""

from __future__ import annotations

from typing import Protocol


class HasHeartRate(Protocol):
    """Protocol satisfait par tout objet exposant un attribut heart_rate."""

    heart_rate: int | None


# Fréquence cardiaque maximale de référence quand elle est inconnue
_DEFAULT_MAX_HR: float = 190.0

# Seuils des zones FC exprimés en fraction de la FC max (zones Coggan/Karvonen)
_HR_ZONE_THRESHOLDS: list[float] = [0.60, 0.70, 0.80, 0.90]


def compute_pace(distance_m: float, duration_s: float) -> float | None:
    """Calcule l'allure en min/km.

    Args:
        distance_m: Distance totale en mètres.
        duration_s: Durée totale en secondes.

    Returns:
        Allure en min/km, ou None si les données sont invalides (zéro ou négatives).
    """
    if distance_m <= 0 or duration_s <= 0:
        return None
    return (duration_s / 60.0) / (distance_m / 1000.0)


def compute_speed(distance_m: float, duration_s: float) -> float | None:
    """Calcule la vitesse moyenne en km/h.

    Args:
        distance_m: Distance totale en mètres.
        duration_s: Durée totale en secondes.

    Returns:
        Vitesse en km/h, ou None si les données sont invalides.
    """
    if distance_m <= 0 or duration_s <= 0:
        return None
    return (distance_m / 1000.0) / (duration_s / 3600.0)


def compute_hr_zone(avg_hr: float, max_hr: float = _DEFAULT_MAX_HR) -> int:
    """Calcule la zone de fréquence cardiaque (1-5) selon les seuils % FC max.

    Zones :
        1 : < 60 % FC max  — récupération active
        2 : 60–70 % FC max — endurance de base
        3 : 70–80 % FC max — aérobie
        4 : 80–90 % FC max — seuil anaérobie
        5 : > 90 % FC max  — VO2 max / effort maximal

    Args:
        avg_hr: Fréquence cardiaque moyenne observée (bpm).
        max_hr: Fréquence cardiaque maximale de référence (bpm).

    Returns:
        Numéro de zone de 1 à 5.
    """
    ratio = avg_hr / max_hr
    for zone, threshold in enumerate(_HR_ZONE_THRESHOLDS, start=1):
        if ratio < threshold:
            return zone
    return 5


def compute_avg_hr(track_points: list[HasHeartRate]) -> float | None:
    """Calcule la fréquence cardiaque moyenne à partir d'une liste de points de trace.

    Args:
        track_points: Liste de TrackPoint (ORM ou dataclass) avec attribut heart_rate.

    Returns:
        FC moyenne en bpm, ou None si aucune donnée FC n'est disponible.
    """
    values = [tp.heart_rate for tp in track_points if tp.heart_rate is not None]
    if not values:
        return None
    return sum(values) / len(values)


def compute_max_hr(track_points: list[HasHeartRate]) -> float | None:
    """Calcule la fréquence cardiaque maximale à partir d'une liste de points de trace.

    Args:
        track_points: Liste de TrackPoint avec attribut heart_rate.

    Returns:
        FC max en bpm, ou None si aucune donnée FC n'est disponible.
    """
    values = [tp.heart_rate for tp in track_points if tp.heart_rate is not None]
    if not values:
        return None
    return float(max(values))
