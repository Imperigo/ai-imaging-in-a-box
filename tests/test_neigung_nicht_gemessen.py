"""Eine fehlende Neigung wurde zu einer gerechneten 0° — und 0° heisst «Norm erfüllt».

**Der Befund (22.09.2026).** In `komposition.beurteile_kamera` stand::

    neigung_grad=float(kamera.get("neigung_grad") or 0.0),
    shift_mm=float(kamera.get("shift_mm") or 0.0),

Ein Kamerablock, der die Neigung gar nicht meldet, bekam damit den Wert 0.0 — und 0.0
ist in diesem Modul keine beliebige Zahl, sondern die **Aussage**: Sensorebene lotrecht,
HABS/NPS eingehalten. Aus «nicht gemessen» wurde «bestanden», und zwar lautlos.

**Der Weg dorthin ist der Hauptweg, nicht ein Sonderfall.**
`runners/blender_depth_stage.py` schreibt `neigung_grad` und `shift_mm` nur im Zweig
`weg: "abgeleitet"`. Auf dem Zweig `vorgegeben` — genau dem, den die Bedienoberfläche
nimmt, wenn jemand Auge und Blickziel im Grundriss anklickt — entstehen sie nie. Seit
`berichtsfelder_aus_stellung` (24.08.2026) urteilt die Kompositionsprüfung dort; sie
urteilte nur eben über eine Neigung, die niemand gemessen hatte.

**Was diese Wächter prüfen, ist die Wirkung am Ergebnis**, nicht der Wortlaut einer
Zeile: ob aus einem fehlenden Feld ein `True`, eine Zahl oder ein Schweigen wird.
"""
from __future__ import annotations

import pytest

from aiimaging import abholer, kameras, komposition

BBOX = [[-8.0, -5.0, 0.0], [8.0, 5.0, 15.0]]


def _block(**kw) -> dict:
    """Ein Kamerablock, wie ihn der Runner auf dem **vorgegebenen** Weg schreibt.

    Also: Standort, Blickziel, Brennweite — und die vier Felder, die
    `berichtsfelder_aus_stellung` daraus ableitet. Weder `neigung_grad` noch `shift_mm`,
    denn die entstehen auf diesem Zweig nicht.
    """
    block = {
        "weg": "vorgegeben",
        "kuerzel": "sSE",
        "auge": [0.0, -35.0, 1.7],
        "blick_auf": [0.0, 0.0, 7.5],
        "brennweite_mm": 35.0,
        "seitenverhaeltnis": 1.0,
    }
    block.update(kameras.berichtsfelder_aus_stellung(
        block["auge"], block["blick_auf"], BBOX, brennweite_mm=35.0))
    block.update(kw)
    return block


def _satz(kamerablock: dict) -> dict:
    """Ein Kamerasatz mit genau dieser einen Kamera, sonst wie aus `kamerasatz`."""
    return {
        "kameras": [kamerablock],
        "gelaende_z": 0.0,
        "gelaende_bezug": "huellbox_unterkante",
        "mitte": [0.0, 0.0, 7.5],
        "masse_m": [16.0, 10.0, 15.0],
    }


# ======================================================================================
# 1 · Der Wächter: ohne Neigungsangabe keine Aussage über die Lotrechte
# ======================================================================================

def test_ohne_neigungsangabe_gilt_die_sensorebene_nicht_als_lotrecht():
    """**Der eigentliche Wächter.** Gemessen wird am Urteil, nicht am Quelltext."""
    urteil = komposition.beurteile_bericht(_block())

    assert urteil["beurteilt"] is True, (
        "Kamerahöhe, Bezugspunkt und Horizontlage stehen da — hier ist sehr wohl etwas "
        "zu beurteilen, nur eben nicht die Neigung")
    assert urteil["neigung_grad"] is None, (
        "eine nicht gemeldete Neigung darf nicht als gemessene 0° dastehen — 0° ist in "
        "diesem Modul die Aussage «HABS/NPS eingehalten»")
    assert urteil["konvergenz"] is None, (
        "die Konvergenz hängt an der Neigung; eine 0.0 hier hiesse «Vertikalen "
        "nachweislich parallel»")
    assert "neigung_grad" in urteil["nicht_gemessen"]


def test_die_fehlende_angabe_wird_gemeldet_und_nicht_als_abweichung_ausgegeben():
    """Die dritte Antwort hat ihren eigenen Wortlaut — sonst ist sie eine der zwei."""
    warnungen = komposition.beurteile_bericht(_block())["warnungen"]
    text = " ".join(warnungen)

    assert "NICHT GEMESSEN" in text, (
        "was nicht gemessen wurde, muss jemand erfahren; ein leeres Feld allein liest "
        "sich als «hier war nichts zu melden»")
    assert "statt 0°" not in text, (
        "es ist keine Abweichung festgestellt worden — «nicht gemessen» ist weder "
        "bestanden noch durchgefallen")


def test_der_kamerasatz_gibt_drei_verschiedene_antworten_auf_dieselbe_frage():
    """Die Wahrheitstafel. Wären es zwei Antworten, wäre eine davon erfunden."""
    gemessen_lotrecht = komposition.beurteile_kamerasatz(
        _satz(_block(neigung_grad=0.0, shift_mm=0.0)))
    gemessen_gekippt = komposition.beurteile_kamerasatz(
        _satz(_block(neigung_grad=9.46, shift_mm=0.0)))
    nicht_gemessen = komposition.beurteile_kamerasatz(_satz(_block()))

    assert gemessen_lotrecht["alle_waagrecht"] is True
    assert gemessen_gekippt["alle_waagrecht"] is False
    assert nicht_gemessen["alle_waagrecht"] is None, (
        "genau hier lief der Befund durch: ohne Angabe meldete der Satz «alle "
        "waagrecht» — eine Normerfüllung, die niemand geprüft hat")


def test_eine_einzige_ungemessene_kamera_macht_den_ganzen_satz_ungemessen():
    """`all()` über eine Liste mit einer Lücke urteilt über die anderen mit."""
    satz = _satz(_block(neigung_grad=0.0, shift_mm=0.0))
    satz["kameras"].append(_block(kuerzel="nNW"))

    assert komposition.beurteile_kamerasatz(satz)["alle_waagrecht"] is None


def test_eine_gemeldete_null_bleibt_eine_messung():
    """Die Gegenprobe zum `or`: 0.0 ist falsch als Ersatzwert und richtig als Messung.

    Ohne diesen Test liesse sich der Befund auch dadurch «beheben», dass gar nichts mehr
    beurteilt wird — und ein Wächter, der nur noch `None` sieht, prüft nichts.
    """
    urteil = komposition.beurteile_bericht(_block(neigung_grad=0.0, shift_mm=0.0))

    assert urteil["neigung_grad"] == 0.0
    assert urteil["konvergenz"] == 0.0
    assert urteil["nicht_gemessen"] == ()
    assert "NICHT GEMESSEN" not in " ".join(urteil["warnungen"])


# ======================================================================================
# 2 · Derselbe Fehler am Shift — Mindestabstand und Bodenanteil hängen daran
# ======================================================================================

def test_ohne_shiftangabe_entsteht_kein_mindestabstand_und_kein_bodenanteil():
    urteil = komposition.beurteile_bericht(_block())

    assert urteil["mindestabstand"] is None
    assert urteil["bodenanteil"] is None
    assert urteil["abstand_genuegt"] is None, (
        "ein `False` hiesse «zu nah» und ein `True` «weit genug» — beides ist eine "
        "Aussage über eine Rechnung, die nicht stattgefunden hat")
    assert "shift_mm" in urteil["nicht_gemessen"]


def test_mit_shiftangabe_wird_wieder_gerechnet():
    """Gegenprobe: Der Weg ist nicht verstopft, es fehlte nur eine Zahl."""
    urteil = komposition.beurteile_bericht(_block(shift_mm=0.0))

    assert urteil["mindestabstand"]["abstand_m"] > 0.0
    assert urteil["bodenanteil"] == pytest.approx(0.5)
    assert urteil["abstand_genuegt"] is True


# ======================================================================================
# 3 · Der Produktweg — dieselbe Frage dort, wo der Auftrag wirklich durchläuft
# ======================================================================================

def test_auf_dem_produktweg_steht_am_bild_keine_erfundene_lotrechte():
    """Die Naht, nicht der Baustein.

    `_komposition_vor_dem_render` ist die Stelle, an der ein Auftrag der Oberfläche die
    Kompositionsprüfung erreicht. Eine Naht, die nur der direkte Aufrufer erreicht, gibt
    es für den Weg nicht, den das Produkt wirklich geht.
    """
    urteil = abholer._komposition_vor_dem_render({"kamera": _block()})

    assert urteil["beurteilt"] is True
    assert urteil["abbruch"] is False, "eine ungemessene Neigung ist kein Abbruchgrund"
    assert urteil["neigung_grad"] is None
    assert any("NICHT GEMESSEN" in w for w in urteil["warnungen"])
