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


def test_der_blender_schritt_schaltet_ihn_nur_mit_bauwerksbox_ein():
    from pathlib import Path
    quelle = (Path(__file__).resolve().parents[1] / "src" / "aiimaging" / "runners"
              / "blender_depth_stage.py").read_text(encoding="utf-8")
    assert 'ausschnitt=bool(getattr(a, "kamera_huellbox", None))' in quelle


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
