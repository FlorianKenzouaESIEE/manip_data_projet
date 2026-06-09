"""Couche d'accès aux données : lecture des bases SQLite vers Pandas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

_RAW_DB = Path("data") / "dashsport_raw.db"
_CLEAN_DB = Path("data") / "dashsport_clean.db"

_TRACK_SAMPLE_STEP = 5  # 1 point sur 5 pour alléger la carte


def load_activities() -> pd.DataFrame:
    """Charge toutes les activités enrichies depuis dashsport_clean.db."""
    if not _CLEAN_DB.exists():
        return pd.DataFrame()
    engine = create_engine(f"sqlite:///{_CLEAN_DB}", echo=False)
    return pd.read_sql_table("activities_clean", engine)


def load_track_points() -> pd.DataFrame:
    """Charge les points GPS depuis dashsport_raw.db (sous-échantillonnés)."""
    if not _RAW_DB.exists():
        return pd.DataFrame()
    engine = create_engine(f"sqlite:///{_RAW_DB}", echo=False)
    df = pd.read_sql_table("track_points", engine)
    return df.iloc[::_TRACK_SAMPLE_STEP].reset_index(drop=True)
