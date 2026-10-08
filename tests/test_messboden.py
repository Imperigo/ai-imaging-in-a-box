"""Der Messboden: eine gedachte Bodenfläche, nur in der Soll-Karte der Prüfung (Entscheid 78).

**Anlass ``auf-20261008-272``:** Ohne Umgebung sagte die Prüfung an der Halle «nicht messbar» —
0 gemeinsame Punkte bei ρ 0,99 auf dem Haus. Das Modell hat keinen Boden, das Bild schon.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

from aiimaging import abholer, messboden
from aiimaging import tiefenschaetzer as ts
from test_tiefenschaetzer import attrappe

WURZEL = Path(__file__).resolve().parents[1]
KAMERA = {"auge": [0.0, -20.0, 1.7], "blick_auf": [0.0, 0.0, 1.7], "brennweite_mm": 35.0,
          "sensor_breite_mm": 36.0, "shift_y": 0.0, "gelaende_z": 0.0}


def test_ueber_dem_horizont_bleibt_hintergrund_darunter_wird_boden():
    b, h = 8, 8
    neu, befund = messboden.mit_messboden([math.inf] * (b * h), b, h, KAMERA)
    assert all(not math.isfinite(w) for w in neu[: b * h // 2])         # obere Hälfte: Himmel
    assert all(math.isfinite(w) for w in neu[b * h // 2:])              # untere: Boden
    assert befund["n_boden"] == b * h // 2


def test_der_boden_wird_nach_unten_naeher():
    b, h = 4, 16
    neu, _ = messboden.mit_messboden([math.inf] * (b * h), b, h, KAMERA)
    spalte = [neu[y * b + 1] for y in range(h // 2, h)]
    assert spalte == sorted(spalte, reverse=True)


def test_geometrie_wird_nicht_angefasst():
    b, h = 4, 4
    soll = [math.inf] * 8 + [12.0] * 8
    neu, befund = messboden.mit_messboden(soll, b, h, KAMERA)
    assert neu[8:] == [12.0] * 8 and befund["n_boden"] == 0


def test_cycles_leere_zaehlt_als_hintergrund():
    neu, befund = messboden.mit_messboden([1.0e10] * 16, 4, 4, KAMERA)
    assert befund["n_boden"] == 8


def test_eine_unvollstaendige_kamera_ist_kein_boden():
    with pytest.raises(messboden.MessbodenError):
        messboden.mit_messboden([math.inf] * 4, 2, 2, {"auge": [0, 0, 1]})


@pytest.fixture()
def bild(tmp_path) -> Path:
    pfad = tmp_path / "bild.png"
    pfad.write_bytes(b"\x89PNG\r\n\x1a\n")
    return pfad


def test_der_befund_aus_272_wird_messbar(bild):
    """Nachgestellt: Halle quer im Bild, darunter Boden im Bild, nicht im Modell. Ohne Messboden
    kein gemeinsamer Punkt; mit ihm misst die Prüfung."""
    b, h = 40, 40
    kamera = dict(KAMERA, auge=[0.0, -30.0, 1.7], blick_auf=[0.0, 0.0, 1.7])
    soll = []
    for y in range(h):
        for x in range(b):
            soll.append(30.0 + 0.05 * x if 14 <= y < 20 else math.inf)
    maske = [math.isfinite(w) for w in soll]
    mit, befund = messboden.mit_messboden(soll, b, h, kamera)
    ist_bild = [1.0 / w if math.isfinite(w) else 0.001 for w in mit]   # das Bild hat Boden
    ohne = ts.qa_gegen_soll(bild, soll, modell=attrappe(ist_bild), breite=b, hoehe=h, maske=maske)
    assert ohne["score"] is None and ohne["n_gemeinsam"] == 0
    gemessen = ts.qa_gegen_soll(bild, mit, modell=attrappe(ist_bild), breite=b, hoehe=h,
                                maske=maske)
    assert gemessen["score"] is not None and gemessen["n_gemeinsam"] > 0
    assert befund["n_boden"] > 0


def test_der_abholer_legt_ihn_nur_ohne_gemessenes_gelaende_an():
    soll = [math.inf] * 16
    bericht = {"kamera": KAMERA}
    neu, befund = abholer._mit_messboden(soll, 4, 4, bericht, {"gelaende_erkannt": False})
    assert befund["angewandt"] is True and sum(map(math.isfinite, neu)) == 8
    for maske in ({"gelaende_erkannt": True}, {}, None):          # Gelände da / ungemessen
        assert abholer._mit_messboden(soll, 4, 4, bericht, maske) == (soll, None)
    kaputt = abholer._mit_messboden(soll, 4, 4, {"kamera": {}}, {"gelaende_erkannt": False})
    assert kaputt[0] == soll and kaputt[1]["angewandt"] is False


def _blender_fehlt() -> bool:
    from aiimaging import seams
    try:
        return not Path(seams.finde_blender()).exists()
    except Exception:                                  # noqa: BLE001
        return True


@pytest.mark.skipif(_blender_fehlt(), reason="Blender fehlt")
def test_der_messboden_trifft_eine_echte_bodenplatte(tmp_path):
    """**Der Beleg für die Kameraformel.** Dasselbe Haus einmal ohne, einmal mit Bodenplatte
    auf 0, dieselbe Kamera: Der Messboden aus dem Lauf ohne trifft die Tiefe der Platte
    (gemessen 08.10.2026: Mittel 1,3 mm, grösster Fehler 3,8 cm an Pixelkanten). Und die
    Tiefe ist der Abstand zur Bildebene, nicht die Strahllänge (die läge um Meter daneben)."""
    from aiimaging import bildlesen, seams
    spez = importlib.util.spec_from_file_location("glb_mb", WURZEL / "tools" / "make_test_glb.py")
    erz = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(erz)
    haus = [("Haus", (-5.0, 0.0, -4.0), (5.0, 6.0, 4.0))]
    (tmp_path / "o.glb").write_bytes(erz.baue_glb(haus))
    (tmp_path / "w.glb").write_bytes(erz.baue_glb(
        haus + [("Gelaende", (-200.0, -0.2, -200.0), (200.0, 0.0, 200.0))]))
    kw = dict(up_axis="Y", aufloesung=96, hoehe=64, samples=2)
    o = seams.glb_zu_multipass(tmp_path / "o.glb", tmp_path / "o", kamera="s", **kw)
    k = o["kamera"]
    w = seams.glb_zu_multipass(tmp_path / "w.glb", tmp_path / "w", auge=k["auge"],
                               blick_auf=k["blick_auf"], brennweite=k["brennweite_mm"], **kw)
    so, b, h = bildlesen.tiefen_aus_report(o, quelle="exr")
    sw, _, _ = bildlesen.tiefen_aus_report(w, quelle="exr")
    kamera_w = dict(k, shift_y=w["kamera"]["shift_y"])
    for art, grenze in (("achse", 0.01), ("strahl", None)):
        neu, befund = messboden.mit_messboden(so, b, h, kamera_w, ebene_z=0.0, tiefe=art)
        d = [abs(a - c) for a, c, s in zip(neu, sw, so) if s >= 1e7 and a < 1e7 and c < 1e7]
        assert len(d) > 0.9 * befund["n_boden"]
        mittel = sum(d) / len(d)
        if grenze is not None:
            assert mittel < grenze, mittel
        else:
            assert mittel > 0.1, mittel                       # Strahllänge ist falsch
