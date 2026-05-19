"""Script orchestrateur d'ingestion des données sportives.

Workflow :
1. Scan du dossier `activities/` (fichiers .gpx, .fit, .fit.gz)
2. Routage vers le parser approprié (parse_gpx ou parse_fit)
3. Insertion des activités et points GPS dans `data/dashsport_raw.db`

Usage :
    python get_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Union

from sqlalchemy.orm import Session

from src.ingestion.parse_fit import ParsedFITActivity, parse_fit
from src.ingestion.parse_gpx import ParsedGPXActivity, parse_gpx
from src.models import Activity, TrackPoint, create_raw_database, get_session


# ─── Configuration ────────────────────────────────────────────────────────────

ACTIVITIES_DIR = Path("activities")
DB_PATH = "data/dashsport_raw.db"


# ─── Fonctions utilitaires ────────────────────────────────────────────────────


def scan_activity_files(directory: Path) -> list[Path]:
    """Scanne le dossier d'activités et retourne tous les fichiers supportés.

    Args:
        directory: Chemin vers le dossier contenant les fichiers d'activités.

    Returns:
        Liste des chemins de fichiers .gpx, .fit, .fit.gz trouvés.
    """
    if not directory.exists():
        print(f"⚠️  Dossier introuvable : {directory}")
        return []

    supported_extensions = {".gpx", ".fit", ".gz"}
    files: list[Path] = []

    for file_path in directory.iterdir():
        if file_path.is_file():
            # Gestion des .fit.gz (double extension)
            if file_path.suffix == ".gz" and file_path.stem.endswith(".fit"):
                files.append(file_path)
            elif file_path.suffix in supported_extensions:
                files.append(file_path)

    return sorted(files)


def parse_activity_file(file_path: Path) -> Union[ParsedGPXActivity, ParsedFITActivity, None]:
    """Route le fichier vers le parser approprié selon son extension.

    Args:
        file_path: Chemin vers le fichier d'activité.

    Returns:
        ParsedGPXActivity ou ParsedFITActivity, ou None en cas d'erreur.
    """
    try:
        # Fichiers .gpx
        if file_path.suffix == ".gpx":
            return parse_gpx(file_path)

        # Fichiers .fit ou .fit.gz
        elif file_path.suffix == ".fit" or (file_path.suffix == ".gz" and file_path.stem.endswith(".fit")):
            return parse_fit(file_path)

        else:
            print(f"⚠️  Extension non supportée : {file_path.name}")
            return None

    except Exception as e:
        print(f"❌ Erreur lors du parsing de {file_path.name} : {e}")
        return None


def insert_activity_to_db(
    parsed_activity: Union[ParsedGPXActivity, ParsedFITActivity],
    session: Session,
) -> None:
    """Insère une activité parsée et ses points GPS dans la base de données.

    Args:
        parsed_activity: Activité parsée (GPX ou FIT).
        session: Session SQLAlchemy active.
    """
    # Vérification si l'activité existe déjà (évite les doublons)
    existing = session.query(Activity).filter_by(source_file=parsed_activity.source_file).first()
    if existing:
        print(f"⏭️  Activité déjà en base : {Path(parsed_activity.source_file).name}")
        return

    # Création de l'objet Activity
    activity = Activity(
        source_file=parsed_activity.source_file,
        name=parsed_activity.name,
        sport_type=parsed_activity.sport_type,
        start_time=parsed_activity.start_time,
        duration_s=parsed_activity.duration_s,
        total_distance_m=parsed_activity.total_distance_m,
        start_lat=parsed_activity.start_lat,
        start_lon=parsed_activity.start_lon,
    )

    session.add(activity)
    session.flush()  # Récupère l'ID auto-généré

    # Création des TrackPoints associés
    track_points = [
        TrackPoint(
            activity_id=activity.id,
            lat=point.lat,
            lon=point.lon,
            elevation=point.elevation,
            timestamp=point.timestamp,
            heart_rate=point.heart_rate,
            cadence=point.cadence,
            cumulative_distance_m=point.cumulative_distance_m,
        )
        for point in parsed_activity.points
    ]

    session.add_all(track_points)
    session.commit()

    print(f"✓ Activité insérée : {Path(parsed_activity.source_file).name} ({len(track_points)} points)")


# ─── Fonction principale ──────────────────────────────────────────────────────


def main() -> None:
    """Point d'entrée principal du script d'ingestion."""
    print("=" * 70)
    print("DASHSPORT — Ingestion des données sportives")
    print("=" * 70)

    # Étape 1 : Création de la base de données (si elle n'existe pas)
    print("\n[1/3] Initialisation de la base de données...")
    Path("data").mkdir(exist_ok=True)
    create_raw_database(DB_PATH)

    # Étape 2 : Scan des fichiers d'activités
    print(f"\n[2/3] Scan du dossier '{ACTIVITIES_DIR}'...")
    activity_files = scan_activity_files(ACTIVITIES_DIR)

    if not activity_files:
        print("⚠️  Aucun fichier d'activité trouvé.")
        sys.exit(0)

    print(f"✓ {len(activity_files)} fichier(s) trouvé(s)")

    # Étape 3 : Parsing et insertion en base
    print("\n[3/3] Parsing et insertion en base de données...")
    session = get_session(DB_PATH)

    success_count = 0
    error_count = 0

    for file_path in activity_files:
        parsed = parse_activity_file(file_path)
        if parsed:
            insert_activity_to_db(parsed, session)
            success_count += 1
        else:
            error_count += 1

    session.close()

    # Résumé
    print("\n" + "=" * 70)
    print(f"✓ Ingestion terminée : {success_count} activité(s) insérée(s)")
    if error_count > 0:
        print(f"⚠️  {error_count} erreur(s) rencontrée(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
