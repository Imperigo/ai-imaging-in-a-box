"""Die Wahrheitstafel des Doppel-Gates — UND, nicht ODER.

Der belegte Anlass steht im Modul-Docstring von ``gate.py``: Ein reines Stil-Gate meldete
einmal ``bestanden`` (Stil-Score 0.42) auf einen Render mit **halluzinierter** Kubatur.
Der wichtigste Test dieser Datei ist darum
``test_stil_bestanden_geometrie_nicht_faellt_durch``: genau jener Fall, an dem die
Methode einmal versagt hat, als ausführbare Zusage.

Die zweite Hälfte der Datei prüft nicht das Urteil, sondern seine **Lesbarkeit**: Fehlt
ein Teilurteil, fällt das Gate zu (fail-closed) und benennt den Mangel — statt ein
fehlendes Messergebnis mit einem verfehlten zu verwechseln.

``gate.py`` importiert keines der beiden QA-Module; diese Datei entsprechend auch nicht.
Die Teilurteile sind hier von Hand geschriebene Wörterbücher. Damit läuft der Test auch
dann, wenn ``geometrie_qa.py`` noch gar nicht existiert.
"""
from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from aiimaging.gate import gesamturteil


def geometrie(bestanden: bool, score: float = 0.71) -> dict:
    """Ein Teilurteil in der Form, die ``geometrie_qa.geometrie_gate`` liefert."""
    return {"bestanden": bestanden, "score": score, "schwelle": 0.65}


def stil(bestanden: bool, score: float = 0.42) -> dict:
    """Ein Teilurteil in der Form, die ``stil_qa.stil_gate`` liefert.

    Der Vorgabewert 0.42 ist nicht beliebig: Das ist der Score, mit dem das reine
    Stil-Gate seinerzeit eine halluzinierte Kubatur durchgelassen hat.
    """
    return {"bestanden": bestanden, "score": score, "schwelle": 0.30}


# --------------------------------------------------------------------------------------
# 1 · Die Wahrheitstafel
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("geo, sti, erwartet", [
    (True, True, True),
    (True, False, False),
    (False, True, False),
    (False, False, False),
])
def test_wahrheitstafel_ist_ein_und(geo, sti, erwartet):
    """Vollständig: nur True/True besteht. Ein ODER liesse drei von vier Zeilen durch."""
    urteil = gesamturteil(geometrie(geo), stil(sti))
    assert urteil["bestanden"] is erwartet


def test_stil_bestanden_geometrie_nicht_faellt_durch():
    """Der belegte Fall: Stil-Score 0.42 auf eine halluzinierte Kubatur.

    Ein reines Stil-Gate meldete hier ``bestanden``. Das Doppel-Gate darf das nicht —
    und der hohe Stil-Score ist dabei kein Trost, sondern das Warnzeichen: Je
    überzeugender die Halluzination, desto besser ihr Stil-Score.
    """
    urteil = gesamturteil(geometrie(False, score=0.31), stil(True, score=0.42))

    assert urteil["bestanden"] is False
    assert "halluzinierte Kubatur" in urteil["begruendung"]
    assert urteil["maengel"] == ()


def test_geometrie_bestanden_stil_nicht_faellt_durch():
    """Das richtige Gebäude im falschen Bild — neu rendern, Geometrie kann bleiben."""
    urteil = gesamturteil(geometrie(True), stil(False, score=0.09))
    assert urteil["bestanden"] is False
    assert "Geometrie ja, Stil nein" in urteil["begruendung"]


def test_beide_bestanden():
    urteil = gesamturteil(geometrie(True), stil(True, score=0.55))
    assert urteil["bestanden"] is True
    assert "Geometrie UND Stil" in urteil["begruendung"]


def test_beide_durchgefallen_deutet_auf_einen_kettenfehler():
    """Zwei gleichzeitig verfehlte Gates sind selten ein misslungener Render."""
    urteil = gesamturteil(geometrie(False), stil(False))
    assert urteil["bestanden"] is False
    assert "Kettenfehler" in urteil["begruendung"]


def test_bestanden_ist_ein_echter_bool():
    """Kein truthy-Ersatz: Aufrufer prüfen mit ``is True``."""
    assert isinstance(gesamturteil(geometrie(True), stil(True))["bestanden"], bool)


# --------------------------------------------------------------------------------------
# 2 · Fail-closed — ein fehlendes Urteil ist kein bestandenes
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("kaputt", [
    {},                                # gar kein Urteil
    {"score": 0.9},                    # gemessen, aber nicht geurteilt
    {"bestanden": None},
    {"bestanden": "ja"},               # truthy — würde ein Wahrheitswert-Test durchlassen
    {"bestanden": 1},                  # dito
    None,
    "bestanden",
    [True],
])
def test_unlesbares_geometrie_urteil_faellt_zu(kaputt):
    """Ohne lesbares Teilurteil wird nicht durchgelassen — auch wenn der Stil besteht."""
    urteil = gesamturteil(kaputt, stil(True))
    assert urteil["bestanden"] is False
    assert urteil["maengel"], "der Mangel muss benannt sein, nicht nur das False"
    assert "Geometrie" in urteil["maengel"][0]


@pytest.mark.parametrize("kaputt", [{}, {"bestanden": "ja"}, None])
def test_unlesbares_stil_urteil_faellt_zu(kaputt):
    urteil = gesamturteil(geometrie(True), kaputt)
    assert urteil["bestanden"] is False
    assert "Stil" in urteil["maengel"][0]


def test_truthy_text_kommt_nicht_durch():
    """``{"bestanden": "nein"}`` ist truthy. Genau so entstehen stille Fehlurteile."""
    urteil = gesamturteil({"bestanden": "nein"}, stil(True))
    assert urteil["bestanden"] is False
    assert "bool" in urteil["maengel"][0]


def test_beide_unlesbar_ergibt_zwei_maengel():
    urteil = gesamturteil({}, {})
    assert urteil["bestanden"] is False
    assert len(urteil["maengel"]) == 2


def test_ein_mangel_wird_vom_verfehlten_urteil_unterschieden():
    """„Nicht gemessen" und „gemessen und verfehlt" sind zwei verschiedene Befunde.

    Beide führen zu ``bestanden: False``. Wer ein Protokoll liest, muss unterscheiden
    können, ob nachzubessern oder die Kette zu reparieren ist.
    """
    verfehlt = gesamturteil(geometrie(False), stil(True))
    fehlend = gesamturteil({}, stil(True))

    assert verfehlt["bestanden"] is fehlend["bestanden"] is False
    assert verfehlt["maengel"] == ()
    assert fehlend["maengel"] != ()
    assert "nicht lesbar" in fehlend["begruendung"]


def test_gate_wirft_nicht():
    """Fail-closed statt Ausnahme: Ein ``False`` kann niemand mit einem Durchlass verwechseln.

    Eine Ausnahme dagegen lässt sich fangen und übergehen — und genau das passiert in
    einer Schleife über viele Renders.
    """
    assert gesamturteil(object(), 3.14)["bestanden"] is False


# --------------------------------------------------------------------------------------
# 3 · Das Protokoll
# --------------------------------------------------------------------------------------

def test_teilurteile_werden_unveraendert_durchgereicht():
    """Ein Wörterbuch trägt das vollständige Protokoll: Score und Schwelle beider Seiten."""
    geo, sti = geometrie(True, score=0.88), stil(True, score=0.61)
    urteil = gesamturteil(geo, sti)

    assert urteil["geometrie"] is geo
    assert urteil["stil"] is sti
    assert urteil["geometrie"]["score"] == 0.88
    assert urteil["stil"]["schwelle"] == 0.30


def test_eingaben_werden_nicht_veraendert():
    """Nur gelesen, nie geschrieben — sonst wäre das Gate eine Nebenwirkung."""
    geo, sti = geometrie(True), stil(False)
    vorher = (copy.deepcopy(geo), copy.deepcopy(sti))

    gesamturteil(geo, sti)

    assert (geo, sti) == vorher


def test_antwort_traegt_immer_dieselben_felder():
    """Kein Rückgabepfad darf ein Feld vergessen — auch der Mangelpfad nicht."""
    felder = {"bestanden", "geometrie", "stil", "maengel", "begruendung"}
    assert set(gesamturteil(geometrie(True), stil(True))) == felder
    assert set(gesamturteil(None, None)) == felder


# --------------------------------------------------------------------------------------
# 4 · Unabhängigkeit der Module
# --------------------------------------------------------------------------------------

def test_gate_importiert_keine_der_beiden_qa():
    """Das Doppel-Gate kennt nur zwei Wörterbücher — nicht die Messmethoden dahinter.

    So bleiben Geometrie-QA und Stil-QA einzeln austauschbar, und dieses Modul ist
    prüfbar, ohne dass eine von beiden existiert. Der Test hält die Zusage fest, weil ein
    bequemer Import sie in einem späteren Commit lautlos aufhebt.
    """
    import aiimaging.gate as modul

    quelle = Path(modul.__file__).read_text(encoding="utf-8")
    module = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            module.update(a.name for a in knoten.names)
        elif isinstance(knoten, ast.ImportFrom) and knoten.level == 0 and knoten.module:
            module.add(knoten.module)

    assert not any(m.startswith("aiimaging") for m in module), module
    assert module <= {"__future__"}
