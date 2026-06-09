"""Tests unitaires pour src/ingestion/parse_gpx.py."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.ingestion.parse_gpx import ParsedGPXActivity, parse_gpx

# ─── Fixture GPX minimal ──────────────────────────────────────────────────────

_MINIMAL_GPX = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <gpx version="1.1" creator="Strava"
        xmlns="http://www.topografix.com/GPX/1/1"
        xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
      <metadata><name>Test Run</name></metadata>
      <trk>
        <name>Test Run</name>
        <type>running</type>
        <trkseg>
          <trkpt lat="48.8566" lon="2.3522">
            <ele>35.0</ele>
            <time>2024-06-01T07:00:00Z</time>
            <extensions>
              <gpxtpx:TrackPointExtension>
                <gpxtpx:hr>150</gpxtpx:hr>
                <gpxtpx:cad>85</gpxtpx:cad>
              </gpxtpx:TrackPointExtension>
            </extensions>
          </trkpt>
          <trkpt lat="48.8570" lon="2.3530">
            <ele>36.0</ele>
            <time>2024-06-01T07:01:00Z</time>
          </trkpt>
          <trkpt lat="48.8580" lon="2.3540">
            <ele>37.0</ele>
            <time>2024-06-01T07:02:00Z</time>
          </trkpt>
        </trkseg>
      </trk>
    </gpx>
""")


@pytest.fixture
def gpx_file(tmp_path: Path) -> Path:
    """Fichier GPX minimal valide écrit dans un répertoire temporaire."""
    p = tmp_path / "test_run.gpx"
    p.write_text(_MINIMAL_GPX, encoding="utf-8")
    return p


# ─── Tests structurels ────────────────────────────────────────────────────────


def test_parse_gpx_returns_correct_type(gpx_file: Path) -> None:
    assert isinstance(parse_gpx(gpx_file), ParsedGPXActivity)


def test_parse_gpx_name(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).name == "Test Run"


def test_parse_gpx_sport_type(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).sport_type == "running"


def test_parse_gpx_point_count(gpx_file: Path) -> None:
    assert len(parse_gpx(gpx_file).points) == 3


# ─── Tests des valeurs des points ─────────────────────────────────────────────


def test_parse_gpx_first_point_lat_lon(gpx_file: Path) -> None:
    p0 = parse_gpx(gpx_file).points[0]
    assert p0.lat == pytest.approx(48.8566)
    assert p0.lon == pytest.approx(2.3522)


def test_parse_gpx_heart_rate_extracted(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).points[0].heart_rate == 150


def test_parse_gpx_cadence_extracted(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).points[0].cadence == 85


def test_parse_gpx_first_point_cumulative_distance_zero(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).points[0].cumulative_distance_m == pytest.approx(0.0)


def test_parse_gpx_cumulative_distance_increases(gpx_file: Path) -> None:
    dists = [p.cumulative_distance_m for p in parse_gpx(gpx_file).points]
    assert dists[1] > dists[0]
    assert dists[2] > dists[1]


# ─── Tests des propriétés calculées ──────────────────────────────────────────


def test_parse_gpx_duration_two_minutes(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).duration_s == pytest.approx(120.0)


def test_parse_gpx_start_lat_lon(gpx_file: Path) -> None:
    activity = parse_gpx(gpx_file)
    assert activity.start_lat == pytest.approx(48.8566)
    assert activity.start_lon == pytest.approx(2.3522)


def test_parse_gpx_total_distance_positive(gpx_file: Path) -> None:
    assert parse_gpx(gpx_file).total_distance_m > 0.0


# ─── Tests des cas d'erreur ───────────────────────────────────────────────────


def test_parse_gpx_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        parse_gpx("/nonexistent/path/activity.gpx")


def test_parse_gpx_empty_gpx_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty.gpx"
    empty.write_text(
        '<?xml version="1.0"?><gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1"></gpx>',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Aucun point GPS"):
        parse_gpx(empty)
