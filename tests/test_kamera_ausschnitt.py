"""Lange, flache Bauwerke: näher heran, als Ausschnitt (Entscheid 75, 08.10.2026).

**Der Anlass** (Splat-Demo der HomeStation, 08.10.2026): Eine Halle von 66 × 10 × 3,45 m füllte
bei der Rahmung «ganzes Bauwerk auf 70 % der Bildbreite» nur 3,8–4,5 % des Bildes und war
«nicht beurteilbar». Owner per Auswahl: Ist das Bauwerk viel breiter als hoch, rückt die Kamera
so nah, dass es mindestens rund ein Viertel des Bildes füllt; die Enden dürfen hinaus.
"""
from __future__ import annotations

import pytest

from aiimaging import kameras as k

HALLE = [[0.0, 0.0, 0.0], [66.0, 10.0, 3.45]]
TESTBAU = [[0.0, 0.0, 0.0], [8.0, 5.0, 3.25]]


def _satz(bbox, **kw):
    kw.setdefault("ausschnitt", True)
    return k.kamerasatz(bbox, kuerzel=["s", "sSE", "nNW"], gelaende_z=0.0,
                        seitenverhaeltnis=1.5, **kw)


def test_in_der_bibliothek_ist_der_ausschnitt_aus():
    """Vorgabe aus: Die Bibliothek rechnet ohne Aufforderung wie bisher. Eingeschaltet wird
    er vom Blender-Schritt, und nur bei Rahmung nach dem Bauwerk — auf einer Szenenbox mit
    grosser Gelaendeplatte hebelte er sonst den Rahmungsriegel aus."""
    for kamera in k.kamerasatz(HALLE, kuerzel=["s"], gelaende_z=0.0)["kameras"]:
        assert kamera["ausschnitt"] is False


def test_der_blender_schritt_schaltet_ihn_mit_bauwerksbox_oder_schalter_ein():
    """Seit ``auf-20261008-271`` auch mit ``--kamera-ausschnitt`` (Bauwerk = Szene)."""
    from pathlib import Path
    quelle = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
              / "blender_depth_stage.py").read_text(encoding="utf-8")
    assert 'ausschnitt=bool(getattr(a, "kamera_huellbox", None)' in quelle
    assert 'or getattr(a, "kamera_ausschnitt", False))' in quelle
    assert '"--kamera-ausschnitt", action="store_true"' in quelle


def test_ganz_im_bild_fuellt_die_halle_nur_einen_streifen():
    """Die Ausgangslage, nachgerechnet: ohne Ausschnitt unter 5 % sichtbar."""
    for kamera in _satz(HALLE, ausschnitt=False)["kameras"]:
        anteil = k.sichtbarer_flaechenanteil(
            kamera["auge"], kamera["blick_auf"], HALLE, seitenverhaeltnis=1.5,
            shift_mm=kamera["shift_mm"])
        assert anteil < 0.06


def test_die_halle_wird_als_ausschnitt_gezeigt():
    satz = _satz(HALLE)
    for kamera in satz["kameras"]:
        assert kamera["ausschnitt"] is True, kamera["kuerzel"]
        assert kamera["flaechenanteil_sichtbar"] >= k.AUSSCHNITT_SCHWELLE - 1e-9
        assert kamera["vollstaendig"] is False
        assert kamera["begruendung"].startswith("AUSSCHNITT (Entscheid 75)")
    # Gewollt, kein gescheiterter Eckentest:
    assert satz["unvollstaendig"] == []


def test_die_frontale_trifft_das_ziel():
    (s,) = _satz(HALLE)["kameras"][:1]
    assert s["flaechenanteil_sichtbar"] == pytest.approx(k.AUSSCHNITT_ZIEL, abs=0.01)


def test_der_testbau_bleibt_ganz_und_unveraendert():
    """Kein langes Bauwerk — alles wie vor dem Entscheid, bitgleich."""
    mit, ohne = _satz(TESTBAU), _satz(TESTBAU, ausschnitt=False)
    for a, b in zip(mit["kameras"], ohne["kameras"]):
        assert a["ausschnitt"] is False and a["flaechenanteil_sichtbar"] is None
        assert a["auge"] == b["auge"] and a["blick_auf"] == b["blick_auf"]
        assert a["vollstaendig"] is True


def test_eine_schmale_seite_bleibt_ganz():
    """Dieselbe Halle quer: Von Süden sieht man nur die 10 m breite Schmalseite —
    kein langes Bild, also die ganze Ansicht."""
    quer = [[0.0, 0.0, 0.0], [10.0, 66.0, 3.45]]
    (s,) = [c for c in _satz(quer)["kameras"] if c["kuerzel"] == "s"]
    assert s["ausschnitt"] is False


def test_ausschnitt_laesst_sich_abschalten():
    for kamera in _satz(HALLE, ausschnitt=False)["kameras"]:
        assert kamera["ausschnitt"] is False


def test_das_beschneiden_rechnet_richtig():
    streifen = [(-1.0, -0.1), (1.0, -0.1), (1.0, 0.1), (-1.0, 0.1)]
    assert k._polygonflaeche(k._beschnitten(streifen)) == pytest.approx(0.2)
    aussen = [(0.6, 0.6), (0.9, 0.6), (0.9, 0.9)]
    assert k._beschnitten(aussen) == []


# ======================================================================================
# Ohne Gelände (auf-20261008-271): das Bauwerk ist die Szene
# ======================================================================================

def _halle_glb(tmp_path, *, mit_gelaende=False):
    """Eine Halle 66 × 10 × 3,45 m als glb (``tools/make_test_glb.py``, glTF-Achsen: Y oben),
    wahlweise auf einer Geländeplatte 120 × 80 m."""
    import importlib.util
    from pathlib import Path
    werkzeug = Path(__file__).resolve().parents[1] / "tools" / "make_test_glb.py"
    spez = importlib.util.spec_from_file_location("make_test_glb_halle", werkzeug)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    koerper = [("Halle", (-33.0, 0.0, -5.0), (33.0, 3.45, 5.0))]
    if mit_gelaende:
        koerper.append(("Gelaende", (-60.0, -0.3, -40.0), (60.0, 0.0, 40.0)))
    tmp_path.mkdir(parents=True, exist_ok=True)
    pfad = tmp_path / "halle.glb"
    pfad.write_bytes(modul.baue_glb(koerper))
    return pfad


def test_ohne_gelaende_meldet_die_rahmung_bauwerk_gleich_szene(tmp_path):
    from aiimaging import glbbox
    urteil = glbbox.rahmungsbox(_halle_glb(tmp_path))
    assert urteil["box"] is None and urteil.get("szene_ist_bauwerk") is True


def test_der_abholer_schaltet_den_ausschnitt_ohne_box_nur_dann_ein(tmp_path):
    from aiimaging import abholer
    ohne = _halle_glb(tmp_path)
    assert abholer._ausschnitt_ohne_box(None, ohne, "Y", "s") is True
    # Von Hand gestellt (keine Richtung) oder eigene Box: nicht.
    assert abholer._ausschnitt_ohne_box(None, ohne, "Y", None) is False
    assert abholer._ausschnitt_ohne_box(((0, 0, 0), (1, 1, 1)), ohne, "Y", "s") is False
    mit = _halle_glb(tmp_path / "g", mit_gelaende=True)
    from aiimaging import glbbox
    assert glbbox.rahmungsbox(mit)["box"] is not None          # Gelände erkannt: Box
    assert abholer._ausschnitt_ohne_box(None, mit, "Y", "s") is False


def test_der_schalter_kommt_im_kommando_an(tmp_path):
    from aiimaging import seams
    ohne = seams.baue_kommando_multipass("m.glb", tmp_path, up_axis="Y")
    mit = seams.baue_kommando_multipass("m.glb", tmp_path, up_axis="Y", kamera_ausschnitt=True)
    assert "--kamera-ausschnitt" not in ohne
    assert mit[-1] == "--kamera-ausschnitt" or "--kamera-ausschnitt" in mit
    assert [x for x in mit if x != "--kamera-ausschnitt"] == ohne


def _blender_fehlt() -> bool:
    from pathlib import Path
    from aiimaging import seams
    try:
        return not Path(seams.finde_blender()).exists()
    except Exception:                                  # noqa: BLE001
        return True


@pytest.mark.skipif(_blender_fehlt(), reason="Blender fehlt")
def test_mit_blender_bekommt_die_halle_ohne_gelaende_den_ausschnitt(tmp_path):
    from aiimaging.seams import glb_zu_multipass
    glb = _halle_glb(tmp_path)
    bericht = glb_zu_multipass(glb, tmp_path / "mp", up_axis="Y", aufloesung=96, samples=2,
                               kamera="s", kamera_ausschnitt=True)
    assert bericht["kamera"]["ausschnitt"] is True
    vorher = glb_zu_multipass(glb, tmp_path / "mp0", up_axis="Y", aufloesung=96, samples=2,
                              kamera="s")
    assert vorher["kamera"]["ausschnitt"] is False


def test_die_angenommene_hochachse_der_bruecke_rahmt_nach_dem_bauwerk(tmp_path):
    """**Befund 08.10.2026:** Ohne Hochachse im Auftrag (jeder glb-Auftrag der Brücke) ging
    ``"Y_UP"`` an ``glbbox``, das nur ``"Y"`` kennt — die Rahmung nach dem Bauwerk kam auf
    diesem Weg nie an. Seither schreibt ``_glb_hochachse`` die Angabe um."""
    from aiimaging import abholer
    assert abholer.ANGENOMMENE_HOCHACHSE == "Y_UP"
    assert abholer._glb_hochachse("Y_UP") == "Y" and abholer._glb_hochachse(None) == "Y"
    mit = _halle_glb(tmp_path, mit_gelaende=True)
    box = abholer._rahmung_fuer(None, mit, abholer.ANGENOMMENE_HOCHACHSE, "s")
    assert box is not None                                    # vorher: None
    ohne = _halle_glb(tmp_path / "o")
    assert abholer._ausschnitt_ohne_box(None, ohne, abholer.ANGENOMMENE_HOCHACHSE, "s") is True
