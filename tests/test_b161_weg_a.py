"""B161/B3: Ein Demohaus über Weg A wird angenommen — die Abnahme, die KosmoOrbit verlangt.

Ihre Behauptung vom 23.09.2026 (Auftrag B161): *«`interior` und weitere Felder fehlen in
deiner strengen Feldkarte. Jedes Demohaus, das ueber Zonen (Weg A) kommt, wuerde
abgewiesen.»* Nachgemessen am 24.09.2026: **überholt** für ``interior`` (in der Karte
seit dem 22.09.2026). **Zutreffend** in einer engeren Form: Sobald drüben eine
Render-Voreinstellung gewählt ist, reisen Felder mit, die wir abweisen — und zwei fielen
bis heute wortlos weg (``cameras[].referenzpunkt``, und die Sonnendetails).

Die Bestellungen sind Zeichen für Zeichen nach ihrem Erzeuger gebaut
(``kosmo-orbit/apps/kosmo-orbit/src/modules/vis/vis-jobs.ts``, ``postRenderJob``,
gelesen am 24.09.2026 auf ihrem Zweig ``claude/kosmo-orbit-v1-build-pzxkbj``): Weg A heisst
``interior: {rooms: 'auto'}`` zusammen mit ``geometry.format: 'ifc'``, gesendet genau dann,
wenn das Dokument Zonen hat — das Demohaus hat sechzehn.
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, kosmo_szene

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_abholer import _kette  # noqa: E402

WURZEL = Path(__file__).resolve().parents[1]

#: Ihre `deriveAutoKameras` für einen 8 × 5 × 3 m Bau, glTF-Koordinaten (y oben).
KAMERAS = [
    {"name": "Eingang", "position": [4.0, 1.6, 6.4], "target": [4.0, 1.2, -2.5],
     "fov": 55, "up_axis": "y", "referenzpunkt": "okff"},
    {"name": "Übersicht", "position": [16.8, 9.0, 8.8], "target": [4.0, 1.5, -2.5],
     "fov": 45, "up_axis": "y"},
    {"name": "Innenraum", "position": [1.913, 1.6, -1.18], "target": [4.333, 1.6, -2.5],
     "fov": 65, "up_axis": "y", "referenzpunkt": "okff"},
]


def szene_weg_a(*, kameras=None, preset=None):
    """Die Objektform von ``postRenderJob`` bei einem Dokument mit Zonen."""
    render = {"resolution": [1600, 1000], "samples": 128, "faithful": 0.8}
    extra = {}
    if preset == "praesentation":
        render.update(resolution=[1920, 1200], samples=256,
                      sun={"azimuth": 200, "elevation": 32})
        extra["komposition"] = {"seitenverhaeltnis": 1.6, "brennweiteMm": 50,
                                "horizontlinie": 0.42}
    return {
        "schema": kosmo_szene.SCHEMA_SZENE,
        "cameras": copy.deepcopy(kameras) if kameras else "auto",
        "render": render,
        "style": {"mode": "none", "prompt": "verputztes Mauerwerk, Holzfenster, Flachdach"},
        "vis": {"skip": False, "backbone": "z-image-turbo", "upscale": False},
        **extra,
        "interior": {"rooms": "auto"},
        "out": "",
        "geometry": {"path": "model.ifc", "format": "ifc"},
    }


@pytest.mark.parametrize("kameras", [None, KAMERAS], ids=["auto", "autokamera-knoten"])
def test_das_demohaus_ueber_weg_a_hat_keinen_mangel(kameras):
    gelesen = kosmo_szene.lies_szene(szene_weg_a(kameras=kameras))
    assert gelesen["maengel"] == (), gelesen["maengel"]
    assert kosmo_szene.unbekannte_felder(szene_weg_a(kameras=kameras)) == ()


def test_der_referenzpunkt_wird_gelesen_und_nicht_verschluckt():
    gelesen = kosmo_szene.lies_szene(szene_weg_a(kameras=KAMERAS))
    bezuege = [k.get("referenzpunkt") for k in gelesen["kameras"]]
    assert bezuege == ["okff", None, "okff"]


def test_ein_fremder_kameraschluessel_faellt_auf():
    """Bis zum 24.09.2026 wurde eine Kameraliste nicht auf fremde Schlüssel geprüft."""
    kameras = copy.deepcopy(KAMERAS)
    kameras[1]["belichtungszeit"] = 0.5
    assert kosmo_szene.unbekannte_felder(szene_weg_a(kameras=kameras)) == (
        "cameras[1].belichtungszeit",)
    gelesen = kosmo_szene.lies_szene(szene_weg_a(kameras=kameras))
    assert any("belichtungszeit" in m for m in gelesen["maengel"])


def test_ein_unbekannter_referenzpunkt_wird_nicht_geraten():
    """Wie ein unbekanntes ``up_axis``: Die Kamera ist dann nicht lesbar."""
    kameras = copy.deepcopy(KAMERAS)
    kameras[0]["referenzpunkt"] = "dachkante"
    with pytest.raises(kosmo_szene.SzenenError, match="referenzpunkt"):
        kosmo_szene.lies_szene(szene_weg_a(kameras=kameras))


# ---------------------------------------------------------------------------------------
# Die Sonne: ihre Konvention, und das Licht
# ---------------------------------------------------------------------------------------

def _mit_sonne(sonne):
    szene = szene_weg_a()
    szene["render"]["sun"] = sonne
    return kosmo_szene.lies_szene(szene)


def test_ihre_sonne_zaehlt_von_norden():
    """180 heisst bei ihnen Süden — bis zum 24.09.2026 stand sie bei uns im Norden."""
    from aiimaging import sonne as sonne_modul
    gelesen = _mit_sonne({"azimuth": 180, "elevation": 30})
    assert gelesen["sonne"]["konvention"] == sonne_modul.AZIMUT_VON_NORDEN
    befund = sonne_modul.aus_bestellung(gelesen["sonne"])
    # Dieselbe Richtung wie 0 Grad in der Süd-Konvention: die Sonne steht im Süden.
    sued = sonne_modul.blender_euler(30, 0, konvention=sonne_modul.AZIMUT_VON_SUEDEN)
    assert befund["euler"] == pytest.approx(sued)
    assert any("ab Nord" in w for w in gelesen["warnungen"])


def test_das_licht_der_sonne_wird_gelesen_und_der_vorbehalt_gesagt():
    gelesen = _mit_sonne({"azimuth": 200, "elevation": 32, "staerke": 6.0,
                          "kelvin": 4900, "winkelGrad": 0.62})
    assert gelesen["maengel"] == ()
    satz = next(w for w in gelesen["warnungen"] if w.startswith("Sonnenstand bedient"))
    assert "staerke, kelvin, winkelGrad" in satz and "Vorbehalt" in satz


@pytest.mark.parametrize("sonne,wort", [
    ({"azimuth": 200, "elevation": 32, "kelvin": 99999}, "kelvin"),
    ({"azimuth": 200, "elevation": 32, "staerke": -1}, "staerke"),
    ({"azimuth": 200, "elevation": 32, "winkelGrad": 180}, "winkelGrad"),
    ({"azimut": 200, "elevation": 32}, "render.sun.azimut"),
])
def test_ein_unbrauchbares_sonnenfeld_ist_ein_mangel(sonne, wort):
    gelesen = _mit_sonne(sonne)
    assert any(wort in m for m in gelesen["maengel"]), gelesen["maengel"]


def test_die_lichtangaben_reisen_bis_zu_den_blender_argumenten():
    from aiimaging import seams
    argumente = seams._multipass_argumente(
        "m.glb", "aus", aufloesung=64, samples=1, drehen=False, beauty=True,
        material_id=True,
        sonne={"azimuth": 200, "elevation": 32, "konvention": "von_norden",
               "staerke": 6.0, "kelvin": 4900, "winkelGrad": 0.62})
    for erwartet in ("--sonne-azimut=200.0", "--sonne-konvention=von_norden",
                     "--sonne-staerke=6.0", "--sonne-kelvin=4900.0", "--sonne-winkel=0.62"):
        assert erwartet in argumente, argumente


def test_mit_voreinstellung_wird_komposition_abgewiesen_und_das_sagt_es():
    """Die engere Form ihrer Behauptung, die zutrifft — mit ihrem eigenen Satz."""
    gelesen = kosmo_szene.lies_szene(szene_weg_a(kameras=KAMERAS, preset="praesentation"))
    assert any(m.startswith("Feld 'komposition'") for m in gelesen["maengel"])


# ---------------------------------------------------------------------------------------
# Durch den Abholer, mit echter IFC-Naht (Multipass und Render als Attrappen)
# ---------------------------------------------------------------------------------------

def _ifc_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_ifc_python()).exists()
    except Exception:                                  # noqa: BLE001
        return True


@pytest.mark.skipif(_ifc_fehlt(), reason=".venv-ifc fehlt")
@pytest.mark.parametrize("kameras,bilder", [(None, 1), (KAMERAS, 3)],
                         ids=["auto", "autokamera-knoten"])
def test_das_demohaus_laeuft_durch_den_abholer(tmp_path, kameras, bilder):
    """Das Job-Paket so, wie ihre Brücke es ablegt (``main.py`` create_job)."""
    job = tmp_path / "store" / "vis-1788000001-000001"
    job.mkdir(parents=True)
    subprocess.run([sys.executable, "tools/make_test_ifc.py", str(job / "model.ifc"),
                    "IFC4", "--raeume"], check=True, capture_output=True, cwd=WURZEL)
    szene = szene_weg_a(kameras=kameras)
    szene["geometry"]["path"] = str(job / "model.ifc")
    szene["out"] = str(job / "out")
    (job / bruecke.DATEI_SZENE).write_text(json.dumps(szene), encoding="utf-8")
    (job / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": job.name, "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "1a2b3c4d",
        "idle_window_only": True, "requested_engine": "ki"}), encoding="utf-8")

    protokoll, attrappen = _kette()
    antwort = abholer.hole_einen(
        job, fremde_freigabe_gilt=True, darf_rechnen=lambda: (True, "frei"),
        verarbeite=abholer.verarbeiter(out_wurzel=tmp_path / "aus", nullprobe=False,
                                       **attrappen))
    assert antwort["tat"] == abholer.TAT_VERARBEITET, antwort["grund"]
    assert len(protokoll["multipass"]) == bilder
    ergebnis = json.loads((job / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
    assert len(ergebnis["images"]) == bilder
    shutil.rmtree(tmp_path / "aus", ignore_errors=True)


def _blender_fehlt() -> bool:
    return not shutil.which("blender") and not Path("/opt/blender/blender").exists()


@pytest.mark.skipif(_blender_fehlt(), reason="Blender fehlt")
def test_das_licht_steht_im_bericht_des_echten_laufs(tmp_path):
    """Nicht die Argumente, sondern die Lampe: Was Blender gesetzt hat, sagt sein Bericht."""
    from aiimaging import seams
    from test_multipass import schreibe_test_glb
    glb = schreibe_test_glb(tmp_path / "zwei_quader.glb")
    bericht = seams.glb_zu_multipass(
        glb, tmp_path / "aus", up_axis="Y", aufloesung=64, samples=1, material_id=False,
        sonne={"azimuth": 200, "elevation": 32, "konvention": "von_norden",
               "staerke": 6.0, "kelvin": 4900, "winkelGrad": 0.62}, timeout=600)
    assert bericht["status"] == "ok", bericht.get("error")
    sonne = bericht["sonne"]
    assert sonne["konvention"] == "von_norden"
    assert sonne["staerke"] == pytest.approx(6.0)
    assert sonne["winkel_grad"] == pytest.approx(0.62, abs=1e-4)
    assert sonne["kelvin"] == pytest.approx(4900.0)
    assert sonne["farbe_linear"][0] == pytest.approx(1.0)
    assert sonne["licht_bestellt"] == ["staerke", "kelvin", "winkelGrad"]


@pytest.mark.skipif(_blender_fehlt(), reason="Blender fehlt")
def test_ohne_lichtangaben_bleibt_die_feste_sonne(tmp_path):
    """Gegenprobe: Nicht bestellt heisst die festen 2.0 und 3 Grad — und das steht da."""
    from aiimaging import seams
    from test_multipass import schreibe_test_glb
    glb = schreibe_test_glb(tmp_path / "zwei_quader.glb")
    bericht = seams.glb_zu_multipass(glb, tmp_path / "aus", up_axis="Y", aufloesung=64,
                                     samples=1, material_id=False, timeout=600)
    assert bericht["status"] == "ok", bericht.get("error")
    assert bericht["sonne"]["staerke"] == pytest.approx(2.0)
    assert bericht["sonne"]["winkel_grad"] == pytest.approx(3.0, abs=1e-4)
    assert bericht["sonne"]["licht_bestellt"] == []
