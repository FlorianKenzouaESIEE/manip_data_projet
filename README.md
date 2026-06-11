# DashSport — Analyse de données sportives Strava

Dashboard interactif d'analyse de données sportives personnelles issues d'une archive Strava locale.
Projet scolaire de Data Engineering — ESIEE Paris.

---

## Prérequis

- Python 3.11+
- Les fichiers d'activités Strava (`.gpx`, `.fit`, `.fit.gz`) placés dans le dossier `activities/`

---

## Installation et lancement

```bash
git clone https://github.com/FlorianKenzouaESIEE/manip_data_projet.git
cd manip_data_projet

pip install -r requirements.txt

python main.py
```

Ouvrir ensuite **http://127.0.0.1:8050** dans un navigateur.

> `main.py` orchestre automatiquement l'ingestion, l'enrichissement météo et le nettoyage avant de lancer le dashboard. Aucune clé d'API requise.

---

## Architecture des données

```
activities/             ← fichiers bruts Strava (.gpx / .fit / .fit.gz)
      │
      ▼
get_data.py             ← parsing + insertion
      │
      ▼
data/dashsport_raw.db   ← activités + points GPS (SQLite)
      │
      ▼
clean_data.py           ← métriques métier + enrichissement météo
      │
      ▼
data/dashsport_clean.db ← activités enrichies + KPI hebdo/mensuels (SQLite)
      │
      ▼
dashboard/              ← Dash / Plotly
```

Les données météo historiques sont récupérées depuis un **cache local JSON** (`data/weather_cache.json`) pré-téléchargé via l'API Open-Meteo — aucune connexion réseau n'est nécessaire pour les données.

---

## Arborescence du projet

```
manip_data_projet/
├── main.py                        # Point d'entrée : bootstrap + lancement Dash
├── get_data.py                    # Orchestrateur d'ingestion
├── clean_data.py                  # Nettoyage, métriques, enrichissement météo
├── requirements.txt
├── mypy.ini
│
├── activities/                    # Fichiers Strava bruts (non versionnés)
├── data/
│   ├── dashsport_raw.db           # Base brute (non versionnée)
│   ├── dashsport_clean.db         # Base enrichie (non versionnée)
│   └── weather_cache.json         # Cache météo Open-Meteo
│
├── src/
│   ├── ingestion/
│   │   ├── parse_gpx.py           # Parser GPX (gpxpy)
│   │   └── parse_fit.py           # Parser FIT / FIT.GZ (fitparse)
│   ├── transform/
│   │   ├── metrics.py             # Allure, vitesse, zones FC
│   │   └── aggregations.py        # KPI hebdomadaires et mensuels
│   ├── weather/
│   │   └── cache.py               # Lecture du cache météo local
│   ├── models.py                  # Modèles SQLAlchemy — base brute
│   └── models_clean.py            # Modèles SQLAlchemy — base enrichie
│
├── dashboard/
│   ├── app.py                     # Instance Dash
│   ├── layout.py                  # Layout principal
│   ├── callbacks.py               # Callbacks interactifs
│   ├── data.py                    # Chargement des données vers Pandas
│   ├── assets/style.css           # Styles globaux
│   └── components/
│       ├── header.py              # En-tête + KPI globaux
│       ├── map.py                 # Carte des tracés GPS
│       └── charts.py              # Courbes de performance, histogrammes, stats
│
├── scripts/
│   └── fetch_weather_cache.py     # Téléchargement du cache météo (usage unique)
│
└── tests/
    ├── test_parse_gpx.py
    ├── test_parse_fit.py
    ├── test_metrics.py
    ├── test_aggregations.py
    └── test_weather_cache.py
```

---

## Fonctionnalités du dashboard

- **En-tête** : nombre d'activités, distance totale, synthèse globale
- **Carte GPS** : tracés de toutes les activités sur fond OpenStreetMap, colorés par sport
- **Liste des activités** : cards cliquables avec allure, distance, durée, météo au départ
- **Détail d'une activité** : courbes seconde par seconde (allure, vitesse, FC, altitude)
- **Stats par sport** : histogrammes de distance, durée, répartition des types d'activité
- **Graphiques croisés** : axes X/Y configurables (allure, vitesse, FC, température, distance…)

---

## Pipeline de données détaillé

| Étape | Script | Sortie |
|-------|--------|--------|
| Parsing | `get_data.py` | `dashsport_raw.db` — tables `activities` + `track_points` |
| Métriques | `clean_data.py` | allure (min/km), vitesse (km/h), zones FC (1-5) |
| Météo | `clean_data.py` + cache JSON | température, vent, précipitations, humidité |
| Agrégats | `clean_data.py` | KPI hebdomadaires et mensuels par sport |

---

## Technologies

| Catégorie | Bibliothèques |
|-----------|--------------|
| Parsing | `gpxpy`, `fitparse` |
| Base de données | `SQLAlchemy`, SQLite |
| Transformation | `pandas`, `numpy` |
| Dashboard | `Dash`, `Plotly` |
| Météo | Open-Meteo (cache local JSON) |
| Qualité | `mypy`, `pytest` |

---

## Lancer les tests

```bash
pytest tests/
```

## Vérification du typage

```bash
mypy src/
```
