"""`komposition.beurteilt` war auf dem Produktivweg IMMER false.

**Der Befund kommt von der HomeStation** (24.08.2026, Nachtrag zu `auf-13`): *«`komposition
.beurteilt` ist bei ausdrücklichen Kameras immer false.»*

Und das ist der schlechteste denkbare Ort dafür. Kommt der Kamerastandort als Zahlen herein
— und **so schickt ihn die Oberfläche** —, rechnet `kamerasatz` gar nicht, und der Bericht
trägt `abstand_m`, `gelaende_z`, `gelaende_bezug` und `gebaeudehoehe_m` nicht.
`beurteile_bericht` antwortet dann völlig richtig «nicht beurteilbar» — bei **jedem**
Auftrag, der über die Oberfläche kommt.

Die **vierte** tote Kante dieser Woche, und die folgenreichste: Das Regelwerk lief genau
dort nicht, wo Bilder für Menschen entstehen. Am 23.08. hatten wir `komposition.py`
angeschlossen und gemeint, es sei erledigt.

**Die Zahlen fehlten nicht, sie wurden nur nie ausgerechnet.**
"""
from __future__ import annotations

import math

import pytest

from aiimaging import kameras, komposition

BBOX = [[-8.0, -5.0, 0.0], [8.0, 5.0, 15.0]]


# --------------------------------------------------------------------------------------
# 1 · Die Ableitung
# --------------------------------------------------------------------------------------

def test_aus_standort_blickziel_und_huellbox_entstehen_alle_vier_felder():
    e = kameras.berichtsfelder_aus_stellung((0.0, -35.0, 1.7), (0.0, 0.0, 7.5), BBOX)

    assert e["abstand_m"] == pytest.approx(35.0)
    assert e["gelaende_z"] == pytest.approx(0.0)
    assert e["gelaende_bezug"] == "huellbox_unterkante"
    assert e["gebaeudehoehe_m"] == pytest.approx(15.0)


def test_ein_gesetzter_gelaendestand_schlaegt_die_huellbox_und_sagt_es():
    """Bei einem Bauwerk mit Untergeschoss ist die Unterkante der Keller.

    Welche der beiden Zahlen gilt, muss am Bericht ablesbar sein — sonst rechnet die
    Kompositionsprüfung die Gebäudehöhe vom Kellerboden aus und urteilt zu mild.
    """
    mit_keller = [[-8.0, -5.0, -3.0], [8.0, 5.0, 15.0]]

    ohne = kameras.berichtsfelder_aus_stellung((0, -35, 1.7), (0, 0, 7.5), mit_keller)
    mit = kameras.berichtsfelder_aus_stellung((0, -35, 1.7), (0, 0, 7.5), mit_keller,
                                              gelaende_z=0.0)

    assert ohne["gebaeudehoehe_m"] == pytest.approx(18.0)
    assert ohne["gelaende_bezug"] == "huellbox_unterkante"
    assert mit["gebaeudehoehe_m"] == pytest.approx(15.0)
    assert mit["gelaende_bezug"] == "gesetzt"


def test_der_abstand_ist_waagrecht_und_nicht_die_luftlinie():
    """Die Aufnahmeentfernung ist eine Grundrissgrösse.

    Die Luftlinie wäre bei einer erhöhten Kamera länger und hinge an der Augenhöhe — dann
    stünde in `abstand_m` teilweise die Kamerahöhe.
    """
    tief = kameras.berichtsfelder_aus_stellung((0, -35, 1.7), (0, 0, 7.5), BBOX)
    hoch = kameras.berichtsfelder_aus_stellung((0, -35, 40.0), (0, 0, 7.5), BBOX)

    assert tief["abstand_m"] == hoch["abstand_m"] == pytest.approx(35.0)
    assert math.dist((0, -35, 40.0), (0, 0, 7.5)) > 35.0, (
        "die Luftlinie ist hier deutlich laenger — genau darum wird sie nicht genommen")


@pytest.mark.parametrize("kaputt", [
    {"auge": (0, 0)}, {"blick_auf": "hier"}, {"bbox": [[0, 0, 0]]},
])
def test_unlesbare_eingaben_werden_abgewiesen(kaputt):
    args = {"auge": (0, -35, 1.7), "blick_auf": (0, 0, 7.5), "bbox": BBOX, **kaputt}
    with pytest.raises(ValueError):
        kameras.berichtsfelder_aus_stellung(args["auge"], args["blick_auf"], args["bbox"])


# --------------------------------------------------------------------------------------
# 2 · Und damit urteilt die Kompositionsprüfung endlich
# --------------------------------------------------------------------------------------

def _bericht_vorgegeben(mit_ableitung: bool) -> dict:
    """Ein Kamerablock, wie ihn der Runner auf dem **vorgegebenen** Weg schreibt."""
    block = {
        "weg": "vorgegeben",
        "auge": [0.0, -35.0, 1.7],
        "blick_auf": [0.0, 0.0, 7.5],
        "brennweite_mm": 35.0,
        "shift_y": 0.0,
        "modus": kameras.MODUS_SHIFT,
    }
    if mit_ableitung:
        block.update(kameras.berichtsfelder_aus_stellung(
            block["auge"], block["blick_auf"], BBOX,
            brennweite_mm=block["brennweite_mm"]))
    return block


def test_ohne_die_ableitung_urteilt_sie_NICHT():
    """Der Zustand bis zum 24.08.2026 — hier festgehalten, damit er nicht zurückkehrt."""
    urteil = komposition.beurteile_bericht(_bericht_vorgegeben(False))

    assert urteil["beurteilt"] is False
    assert "trägt" in urteil["grund"]


def test_mit_der_ableitung_urteilt_sie():
    """**Der eigentliche Test.** Dieselbe Kamera, dieselben Zahlen — nur ausgerechnet."""
    urteil = komposition.beurteile_bericht(_bericht_vorgegeben(True))

    assert urteil["beurteilt"] is True, urteil.get("grund")


def test_das_urteil_haengt_an_den_zahlen_und_nicht_an_der_ableitung():
    """Gegenprobe: Eine offensichtlich schlechte Aufstellung fällt auch jetzt auf.

    Sonst hiesse «beurteilt: true» nur, dass die Felder da sind.
    """
    nah = _bericht_vorgegeben(False)
    nah["auge"] = [0.0, -4.0, 1.7]
    nah.update(kameras.berichtsfelder_aus_stellung(
        nah["auge"], nah["blick_auf"], BBOX, brennweite_mm=35.0))

    urteil = komposition.beurteile_bericht(nah)

    assert urteil["beurteilt"] is True
    assert urteil.get("warnungen"), (
        "vier Meter vor einem 15-m-Bau ist keine Architekturaufnahme — dazu muss das "
        "Regelwerk etwas zu sagen haben, sonst prueft es nichts")


def test_der_runner_ruft_die_ableitung_auch_wirklich_auf():
    """Ein Mass, das nie gerufen wird, ist von einem fehlenden nicht zu unterscheiden.

    Dieses Projekt hat die Fehlerart in dieser Woche viermal gefunden; der Nachweis der
    Verdrahtung steht darum im selben Zug wie die Rechnung.
    """
    from pathlib import Path

    quelle = (Path(kameras.__file__).resolve().parents[0]
              / "runners" / "blender_depth_stage.py").read_text(encoding="utf-8")

    assert "berichtsfelder_aus_stellung" in quelle
    assert "setdefault" in quelle, (
        "vorhandene Felder duerfen nicht ueberschrieben werden — auf dem gerechneten Weg "
        "stehen dort die genaueren Zahlen"
    )
