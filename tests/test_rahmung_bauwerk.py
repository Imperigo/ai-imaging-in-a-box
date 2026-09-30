"""Die Kamera rahmt das Bauwerk, nicht das Grundstück — Owner-Entscheid 30.09.2026.

Gemessen mit echtem Blender (Sitzung 73 §12): Testbau mit Geländeplatte, Kamera sSE —
nach der Szene gerahmt füllt das Gebäude 2,0 % des Bildes, nach dem Bauwerk 21,0 %. Der
Messweg (homeworker) rahmt seither nach dem Bauwerk; der Abholer erst nach dem Beweislauf
(``abholer.RAHMUNG_NACH_BAUWERK``).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, glbbox

WURZEL = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def glb_mit_gelaende(tmp_path_factory):
    from aiimaging import seams
    try:
        ifc_py = Path(seams.finde_ifc_python())
    except Exception:                                    # noqa: BLE001
        pytest.skip(".venv-ifc fehlt")
    if not ifc_py.exists():
        pytest.skip(".venv-ifc fehlt")
    d = tmp_path_factory.mktemp("rahmung")
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(d / "bau.ifc"), "--gelaende"],
                   check=True, capture_output=True, cwd=WURZEL)
    bericht = seams.ifc_zu_glb(d / "bau.ifc", d / "bau.glb")
    assert bericht["status"] == "ok", bericht.get("error")
    return bericht["glb_path"], bericht.get("up_axis", "Y")


def test_mit_gelaende_rahmt_sie_das_bauwerk(glb_mit_gelaende):
    glb, achse = glb_mit_gelaende
    aus = glbbox.rahmungsbox(glb, up_axis=achse)
    assert aus["nach"] == "bauwerk" and aus["box"] is not None
    (lo, hi) = aus["box"]
    assert hi[0] - lo[0] < 10, "das Bauwerk ist 8 m breit, nicht die 20-m-Szene"


def test_eine_unlesbare_datei_rahmt_nach_der_szene_ohne_pfad(tmp_path):
    aus = glbbox.rahmungsbox(tmp_path / "gibt-es-nicht.glb")
    assert aus["box"] is None and aus["nach"] == "szene"
    assert str(tmp_path) not in aus["grund"]


def test_der_abholer_rahmt_nach_dem_bauwerk_seit_dem_beweislauf():
    """auf-20260930-188: Form steht in 6 von 8 (Bauwerk) gegen 0 von 8 (Szene)."""
    assert abholer.RAHMUNG_NACH_BAUWERK is True
    # Eine unlesbare Datei rahmt weiter nach der Szene — kein Bild geht dadurch verloren.
    assert abholer._rahmung_fuer(None, "gibt-es-nicht.glb", "Y", "sSE") is None
    eigene = [[0, 0, 0], [1, 1, 1]]
    assert abholer._rahmung_fuer(eigene, "x.glb", "Y", "sSE") is eigene


def test_eingeschaltet_rahmt_der_abholer_das_bauwerk(monkeypatch, glb_mit_gelaende):
    glb, achse = glb_mit_gelaende
    monkeypatch.setattr(abholer, "RAHMUNG_NACH_BAUWERK", True)
    assert abholer._rahmung_fuer(None, glb, achse, "sSE") is not None
    assert abholer._rahmung_fuer(None, glb, achse, None) is None, "Standpunkt von Hand"
