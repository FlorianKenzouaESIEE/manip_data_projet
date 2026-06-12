> Vidéo de démonstration : https://youtu.be/_Ofig6UfDtg

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

> `main.py` orchestre automatiquement l'ingestion, l'enrichissement météo et le nettoyage avant de lancer le dashboard. Aucune clé d'API n'est requise, toutes les données météo sont servies depuis un cache pré-téléchargé.

---

## Architecture générale

Le projet suit un pipeline **ETL → SQLite → Dash** en trois étapes distinctes :

```
activities/             ← fichiers bruts Strava (.gpx)
      │
      ▼
get_data.py             ← parsing + insertion SQLAlchemy
      │
      ▼
data/dashsport_raw.db   ← tables : activities + track_points
      │
      ▼
clean_data.py           ← métriques métier + enrichissement météo + agrégats
      │
      ▼
data/dashsport_clean.db ← tables : activities_clean + weekly_kpis + monthly_kpis
      │
      ▼
dashboard/              ← Dash / Plotly (lecture seule)
```

`main.py` exécute ces trois étapes en séquence au démarrage, de façon **incrémentale** : seules les nouvelles activités sont parsées et ajoutées, les activités déjà présentes en base sont ignorées.

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
│   └── weather_cache.json         # Cache météo Open-Meteo (versionné)
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
│   ├── app.py                     # Instance Dash + montage des callbacks
│   ├── layout.py                  # Layout principal (vues dashboard + détail)
│   ├── callbacks.py               # Callbacks Dash : navigation et graphiques
│   ├── data.py                    # Couche d'accès aux données (SQLite → Pandas)
│   ├── assets/style.css           # Styles globaux
│   └── components/
│       ├── header.py              # En-tête + KPI globaux
│       ├── map.py                 # Carte des tracés GPS (Plotly Scattermapbox)
│       └── charts.py              # Histogramme FC, courbes de performance, stats
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

## Détail des modules

### `main.py` — Point d'entrée

Lance le bootstrap complet avant de démarrer le serveur Dash :

1. Si le dossier `activities/` existe → appelle `get_data.main()` (ingestion incrémentale)
2. Si `dashsport_raw.db` existe → appelle `fetch_weather_cache.main()` (mise à jour optionnelle du cache météo)
3. Appelle `clean_data.main()` (métriques + enrichissement)
4. Démarre Dash sur `127.0.0.1:8050`

### `get_data.py` — Ingestion

Parcourt récursivement le dossier `activities/` et dispatche chaque fichier vers le parser adéquat :

- `.gpx` → `src/ingestion/parse_gpx.py`
- `.fit` ou `.fit.gz` → `src/ingestion/parse_fit.py`

Chaque activité parsée est insérée dans `dashsport_raw.db` via SQLAlchemy. Les fichiers déjà présents (clé `source_file` unique) sont ignorés.

### `src/ingestion/parse_gpx.py` — Parser GPX

Lit les fichiers `.gpx` Strava via `gpxpy`. Pour chaque point GPS :

- Extrait latitude, longitude, altitude, timestamp
- Extrait FC et cadence depuis les **extensions Garmin/Strava** (`gpxtpx:TrackPointExtension`)
- Calcule la **distance cumulée** point à point via la formule haversine (rayon terrestre = 6 371 000 m)

Retourne une `ParsedGPXActivity` (dataclass) contenant la liste typée des `TrackPoint`.

### `src/ingestion/parse_fit.py` — Parser FIT/FIT.GZ

Lit les fichiers `.fit` (format binaire Garmin) et `.fit.gz` (variante compressée) via `fitparse`. Particularités :

- Les coordonnées GPS sont stockées en **semicircles** → conversion en degrés décimaux (`× 180 / 2³¹`)
- Le type de sport est extrait des messages `sport` puis `session`
- La distance cumulée est calculée par haversine, comme pour le GPX

### `src/transform/metrics.py` — Métriques sportives

Fonctions pures (sans effet de bord, testables unitairement) :

| Fonction | Calcul | Unité |
|---|---|---|
| `compute_pace` | `(durée_s / 60) / (distance_m / 1000)` | min/km |
| `compute_speed` | `(distance_m / 1000) / (durée_s / 3600)` | km/h |
| `compute_avg_hr` | moyenne des FC non nulles | bpm |
| `compute_max_hr` | max des FC non nulles | bpm |
| `compute_hr_zone` | % FC max → zone 1-5 (seuils Coggan) | — |

Zones de fréquence cardiaque (FC max de référence : 190 bpm par défaut) :

| Zone | Seuil | Description |
|---|---|---|
| Z1 | < 60 % FC max | Récupération active |
| Z2 | 60–70 % FC max | Endurance de base |
| Z3 | 70–80 % FC max | Aérobie / tempo |
| Z4 | 80–90 % FC max | Seuil anaérobie |
| Z5 | > 90 % FC max | VO₂ max / effort maximal |

### `src/transform/aggregations.py` — Agrégats KPI

Calcule les KPI agrégés **par semaine ISO** (`compute_weekly_kpis`) et **par mois calendaire** (`compute_monthly_kpis`), segmentés par type de sport. Pour chaque bucket :

- Nombre d'activités, distance totale, durée totale
- Allure moyenne, vitesse moyenne
- Température moyenne (depuis les données météo enrichies)

### `src/weather/` — Cache météo

Le fichier `data/weather_cache.json` contient les relevés historiques **Open-Meteo** (température, vent, précipitations, humidité, code WMO) pour chaque heure de chaque journée couverte par les activités. `scripts/fetch_weather_cache.py` télécharge ce cache une seule fois. La lecture en runtime est purement locale, **aucune connexion réseau n'est nécessaire**.

### `src/models.py` — Schéma de la base brute

Deux tables SQLAlchemy :

- **`activities`** : métadonnées d'une activité (nom, type de sport, date de début, durée, distance, coordonnées GPS de départ)
- **`track_points`** : points GPS horodatés (lat, lon, altitude, FC, cadence, distance cumulée) — relation 1-N avec `activities`

### `src/models_clean.py` — Schéma de la base enrichie

Trois tables SQLAlchemy :

- **`activities_clean`** : copie enrichie de chaque activité avec allure, vitesse, FC moy/max, zone FC, et données météo (température, vent, précipitations, humidité, code WMO)
- **`weekly_kpis`** : agrégats hebdomadaires par sport (contrainte d'unicité sur `year × week × sport_type`)
- **`monthly_kpis`** : agrégats mensuels par sport (contrainte d'unicité sur `year × month × sport_type`)

---

## Dashboard

L'application Dash est organisée en **deux vues** gérées par un `dcc.Store` central (`app-state`).

### Vue 1 — Dashboard principal

- **En-tête** (`header.py`) : nombre total d'activités, distance totale, durée totale, sport(s) pratiqué(s)
- **Stats par sport** : tableau récapitulatif (activités, distance, durée, allure moy.) + donut "Durée par sport"
- **Distribution FC globale** : histogramme coloré par zones (Z1 cyan → Z5 rose), axe Y en minutes
- **Liste des activités** : cards cliquables triées par date décroissante — chaque card affiche distance, durée, allure et FC moyenne

### Vue 2 — Détail d'une activité (au clic sur une card)

- **Hero métriques** : 4 tuiles (distance, durée, allure, dénivelé positif)
- **Tracé GPS** : carte Plotly Scattermapbox sur fond OpenStreetMap avec le tracé de l'activité
- **Courbes de performance** : graphique multi-pistes seconde par seconde (allure, vitesse, FC, altitude), axe X commutable entre **temps** et **distance** via RadioItems
- **Conditions météo** : température, vent, humidité, altitude moyenne + analyse automatique (conditions difficiles / favorables / optimales)

### `dashboard/data.py` — Couche données

| Fonction | Source | Détail |
|---|---|---|
| `load_activities()` | `dashsport_clean.db` | Toutes les activités enrichies |
| `load_track_points()` | `dashsport_raw.db` | Points GPS sous-échantillonnés (1 sur 5) pour la carte globale |
| `load_activity_track(id)` | `dashsport_raw.db` | Tous les points d'une activité (sans sous-échantillonnage) pour le détail |
| `load_hr_series_all()` | `dashsport_raw.db` | Toutes les valeurs FC pour l'histogramme global |

### `dashboard/callbacks.py` — Callbacks Dash

Deux callbacks principaux :

1. **`update_app_state`** : écoute les clics sur les cards et le bouton "Retour", met à jour le store `app-state`
2. **`render_view`** : réagit au store et au mode d'axe X des courbes, rend la vue active (dashboard ou détail) en construisant dynamiquement l'en-tête, les métriques héros, la carte, les courbes et la section météo

---

## Pipeline de données — récapitulatif

| Étape | Script | Entrée | Sortie |
|---|---|---|---|
| Parsing GPX | `get_data.py` → `parse_gpx.py` | `.gpx` | `activities` + `track_points` |
| Parsing FIT | `get_data.py` → `parse_fit.py` | `.fit` / `.fit.gz` | `activities` + `track_points` |
| Métriques | `clean_data.py` | `dashsport_raw.db` | allure, vitesse, FC moy/max, zone FC |
| Météo | `clean_data.py` + cache JSON | `weather_cache.json` | temp., vent, précip., humidité |
| Agrégats | `clean_data.py` | activités enrichies | `weekly_kpis`, `monthly_kpis` |

---

## Technologies

| Catégorie | Bibliothèques | Version minimale |
|---|---|---|
| Parsing | `gpxpy`, `fitparse` | 1.6.0, 1.2.0 |
| Base de données | `SQLAlchemy`, SQLite | 2.0.0 |
| Transformation | `pandas`, `numpy` | 2.1.0, 1.26.0 |
| Dashboard | `Dash`, `Plotly` | 2.14.0, 5.18.0 |
| Météo | Open-Meteo (cache local JSON) | — |
| Qualité | `mypy`, `pytest` | 1.8.0, 8.0.0 |

---

## Tests

```bash
pytest tests/
```

Les tests couvrent les parsers GPX et FIT, les fonctions de métriques (allure, vitesse, zones FC), les agrégations KPI hebdomadaires et mensuels, et la lecture du cache météo. Toutes les fonctions de `src/transform/` sont pures et testées sans base de données.

## Vérification du typage statique

```bash
mypy src/
```

L'ensemble de `src/` est annoté avec des types Python 3.11 et vérifié par mypy en mode strict.
