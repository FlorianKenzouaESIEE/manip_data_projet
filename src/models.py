"""Modèles SQLAlchemy pour la base de données brute (dashsport_raw.db).

Tables :
- Activity : métadonnées d'une activité sportive (1 ligne = 1 fichier .gpx/.fit)
- TrackPoint : points GPS horodatés (N lignes par activité)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship


# ─── Base déclarative ─────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""

    pass


# ─── Modèles ──────────────────────────────────────────────────────────────────


class Activity(Base):
    """Métadonnées d'une activité sportive (course, vélo, natation…)."""

    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_file = Column(String, nullable=False, unique=True)  # chemin du fichier source
    name = Column(String, nullable=False)
    sport_type = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    duration_s = Column(Float, nullable=False)  # durée en secondes
    total_distance_m = Column(Float, nullable=False)  # distance totale en mètres
    start_lat = Column(Float, nullable=True)  # latitude de départ
    start_lon = Column(Float, nullable=True)  # longitude de départ

    # Relation 1-N vers les points GPS
    track_points = relationship("TrackPoint", back_populates="activity", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, name='{self.name}', sport='{self.sport_type}', date={self.start_time})>"


class TrackPoint(Base):
    """Point GPS horodaté avec métriques optionnelles (FC, cadence, altitude…)."""

    __tablename__ = "track_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    elevation = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False)
    heart_rate = Column(Integer, nullable=True)
    cadence = Column(Integer, nullable=True)
    cumulative_distance_m = Column(Float, nullable=False)

    # Relation N-1 vers l'activité parente
    activity = relationship("Activity", back_populates="track_points")

    def __repr__(self) -> str:
        return f"<TrackPoint(id={self.id}, activity_id={self.activity_id}, lat={self.lat:.4f}, lon={self.lon:.4f})>"


# ─── Fonctions utilitaires ────────────────────────────────────────────────────


def create_raw_database(db_path: str = "data/dashsport_raw.db") -> None:
    """Crée la base de données brute avec toutes les tables.

    Args:
        db_path: Chemin vers le fichier SQLite (créé s'il n'existe pas).
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    print(f"✓ Base de données créée : {db_path}")


def get_session(db_path: str = "data/dashsport_raw.db") -> Session:
    """Retourne une session SQLAlchemy connectée à la base brute.

    Args:
        db_path: Chemin vers le fichier SQLite.

    Returns:
        Session SQLAlchemy prête à l'emploi.
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return Session(engine)


if __name__ == "__main__":
    # Test : création de la base de données
    create_raw_database()

# Made with Bob
