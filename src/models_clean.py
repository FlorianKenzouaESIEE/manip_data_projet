"""Modèles SQLAlchemy pour la base de données enrichie dashsport_clean.db.

Tables :
- ActivityClean   : une activité par ligne, avec métriques et météo calculées.
- WeeklyKPI       : agrégats par semaine ISO et type de sport.
- MonthlyKPI      : agrégats par mois calendaire et type de sport.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session

_DB_PATH = Path(__file__).parent.parent / "data" / "dashsport_clean.db"
_engine = None


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles de la base clean."""

    pass


class ActivityClean(Base):
    """Activité enrichie : métriques calculées (allure, vitesse, FC) + météo."""

    __tablename__ = "activities_clean"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, nullable=False, unique=True)  # FK logique vers raw
    source_file = Column(String, nullable=False)
    name = Column(String)
    sport_type = Column(String)
    start_time = Column(DateTime)
    duration_s = Column(Float)
    total_distance_m = Column(Float)
    start_lat = Column(Float)
    start_lon = Column(Float)

    # ── Métriques calculées ──────────────────────────────────────────────────
    pace_min_per_km = Column(Float)   # pertinent pour course/marche
    speed_kmh = Column(Float)
    avg_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    hr_zone = Column(Integer)         # zone 1-5 basée sur % FC max

    # ── Données météo (depuis cache local) ──────────────────────────────────
    temperature_c = Column(Float)
    wind_speed_kmh = Column(Float)
    precipitation_mm = Column(Float)
    humidity_pct = Column(Float)
    weather_code = Column(Integer)    # code WMO Open-Meteo

    def __repr__(self) -> str:
        return (
            f"<ActivityClean(id={self.id}, name='{self.name}', "
            f"sport='{self.sport_type}', pace={self.pace_min_per_km:.2f} min/km)>"
        )


class WeeklyKPI(Base):
    """Agrégats de performance par semaine ISO et type de sport."""

    __tablename__ = "weekly_kpis"
    __table_args__ = (UniqueConstraint("year", "week", "sport_type"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    sport_type = Column(String, nullable=False)
    activity_count = Column(Integer)
    total_distance_m = Column(Float)
    total_duration_s = Column(Float)
    avg_pace_min_per_km = Column(Float)
    avg_speed_kmh = Column(Float)
    avg_temperature_c = Column(Float)


class MonthlyKPI(Base):
    """Agrégats de performance par mois calendaire et type de sport."""

    __tablename__ = "monthly_kpis"
    __table_args__ = (UniqueConstraint("year", "month", "sport_type"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    sport_type = Column(String, nullable=False)
    activity_count = Column(Integer)
    total_distance_m = Column(Float)
    total_duration_s = Column(Float)
    avg_pace_min_per_km = Column(Float)
    avg_speed_kmh = Column(Float)
    avg_temperature_c = Column(Float)


def create_clean_database() -> None:
    """Crée (ou met à jour) dashsport_clean.db avec toutes les tables clean."""
    global _engine
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{_DB_PATH}", echo=False)
    Base.metadata.create_all(_engine)


def get_clean_session() -> Session:
    """Retourne une session SQLAlchemy connectée à dashsport_clean.db.

    Appelle create_clean_database() si le moteur n'est pas encore initialisé.
    """
    global _engine
    if _engine is None:
        create_clean_database()
    return Session(_engine)
