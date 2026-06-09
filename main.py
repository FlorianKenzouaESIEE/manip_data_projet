"""Point d'entrée principal de DashSport.

Lance automatiquement les étapes d'ingestion et de nettoyage si les bases
de données n'existent pas encore, puis démarre le serveur Dash.

Usage :
    python main.py
"""

from __future__ import annotations

from pathlib import Path

_RAW_DB = Path("data") / "dashsport_raw.db"
_CLEAN_DB = Path("data") / "dashsport_clean.db"
_ACTIVITIES_DIR = Path("activities")


def _bootstrap() -> None:
    """Construit les bases de données si elles sont absentes."""
    if not _RAW_DB.exists() and _ACTIVITIES_DIR.exists():
        print("[bootstrap] Ingestion des activités...")
        import get_data
        get_data.main()

    if not _CLEAN_DB.exists() and _RAW_DB.exists():
        print("[bootstrap] Nettoyage et enrichissement...")
        import clean_data
        clean_data.main()


if __name__ == "__main__":
    _bootstrap()

    from dashboard.app import create_app

    app = create_app()
    print("\nDashSport — http://127.0.0.1:8050")
    app.run(debug=False, host="127.0.0.1", port=8050)
