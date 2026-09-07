"""Die Studie zur Innenansicht — ihre Arithmetik und ihre Schalter.

Was hier geprüft wird und was nicht
------------------------------------
**Geprüft wird die Rechnung**, nicht der Blender-Lauf: ``_kennzahlen`` bekommt einen
Bericht und gibt vier Zahlen zurück. Das ist reine Arithmetik über die Soll-Karte, und
genau darum ist die Studie hier überhaupt fahrbar — ohne GPU und ohne Schätzer.

**Nicht geprüft wird, ob die gemessenen Zahlen stimmen.** Das kann keine Probe sagen; es
sagt der Lauf, und der steht mit seinen Zahlen in ``docs/INNENANSICHT_2026-09-09.md``.

Die vier Schalter sind mitgeprüft — *ein Bedienelement ohne Wirkung ist schlimmer als
keines: Es sagt, etwas sei geschehen.* Gefahren wird dabei gegen einen abgefangenen
``messe``, denn ein echter Lauf kostet acht Blender-Starts.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]


def _lade():
    """Lädt das Werkzeug als Modul — es ist ein Skript, kein Paket."""
    pfad = WURZEL / "tools" / "studie_innenansicht.py"
    spec = importlib.util.spec_from_file_location("studie_innenansicht", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["studie_innenansicht"] = modul
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def studie():
    return _lade()


def _bericht(werte: list[float | None], breite: int, hoehe: int):
    """Ein Bericht, wie ``bildlesen.tiefen_aus_report`` ihn auflösen würde."""
    return {"_werte": werte, "_breite": breite, "_hoehe": hoehe}


@pytest.fixture
def ohne_blender(studie, monkeypatch):
    """Ersetzt den Leser: Die Studie soll ihre Rechnung zeigen, nicht Blender."""
    def lies(bericht):
        return bericht["_werte"], bericht["_breite"], bericht["_hoehe"]
    monkeypatch.setattr(studie.bildlesen, "tiefen_aus_report", lies)
    return studie


# --------------------------------------------------------------- die Rechnung

def test_eine_einzige_ebene_wird_als_ganzes_bild_gemeldet(ohne_blender):
    """Der Fall, um den es geht: 50 mm frontal, gemessen eine einzige Tiefe.

    Spanne 0, eine Stufe, das ganze Bild auf einer Ebene. *Eine Tiefenkarte aus einem
    Wert kann keine Rangordnung tragen* — und genau das soll die Zahl sagen.
    """
    k = ohne_blender._kennzahlen(_bericht([4.1] * 16, 4, 4))
    assert k["geometrieanteil"] == 1.0
    assert k["spanne_m"] == pytest.approx(0.0)
    assert k["stufen"] == 1
    assert k["groesste_ebene_anteil"] == pytest.approx(1.0)


def test_der_himmel_zaehlt_nicht_als_geometrie_und_nicht_gegen_die_ebene(ohne_blender):
    """Zwei Dinge zugleich, und das zweite ist die Entscheidung.

    Der Himmel (``1e10`` in der EXR) ist keine Geometrie. Der Anteil der grössten Ebene
    wird trotzdem am **ganzen Bild** gemessen und nicht an der Geometrie: *Ein Blick, der
    halb aus Himmel besteht, ist nicht dadurch besser, dass die andere Hälfte eine
    einzige Wand ist.*
    """
    k = ohne_blender._kennzahlen(_bericht([4.1] * 8 + [1e10] * 8, 4, 4))
    assert k["geometrieanteil"] == pytest.approx(0.5)
    assert k["stufen"] == 1
    assert k["groesste_ebene_anteil"] == pytest.approx(0.5), (
        "Am ganzen Bild gemessen wären es 50 %, an der Geometrie 100 % — und 100 % "
        "hiesse hier 'von einer Fläche beherrscht', wo das halbe Bild Himmel ist.")


def test_gestaffelte_tiefen_ergeben_eine_kleine_groesste_ebene(ohne_blender):
    """Der Gegenfall: über Eck, gemessen 0,5 bis 0,6 % auf der grössten Ebene."""
    k = ohne_blender._kennzahlen(_bericht([4.0 + i * 0.05 for i in range(100)], 10, 10))
    assert k["stufen"] == 100
    assert k["groesste_ebene_anteil"] == pytest.approx(0.01)
    assert k["spanne_m"] == pytest.approx(4.95)


def test_eine_karte_ohne_geometrie_behauptet_keine_zahlen(ohne_blender):
    """Kein Geometriepunkt heisst **nicht gemessen** und nicht «Spanne null».

    Eine Null wäre hier die gefährliche Richtung: Sie sähe aus wie das Ergebnis vom
    50-mm-Fall — eine flache Wand — und wäre in Wahrheit ein leeres Bild.
    """
    k = ohne_blender._kennzahlen(_bericht([1e10] * 16, 4, 4))
    assert k["geometrieanteil"] == 0.0
    assert k["spanne_m"] is None
    assert k["groesste_ebene_anteil"] is None


def test_die_stufen_werden_auf_einen_zentimeter_gerundet(ohne_blender):
    """Ohne Rundung zählte jeder Gleitkommaschimmer als eigene Tiefenstufe.

    Vier Werte innerhalb eines Zentimeters sind **eine** Fläche und nicht vier.
    """
    k = ohne_blender._kennzahlen(_bericht([4.100, 4.1001, 4.1002, 4.1003], 2, 2))
    assert k["stufen"] == 1
    assert k["groesste_ebene_anteil"] == pytest.approx(1.0)


# ---------------------------------------------------------------- die Schalter

@pytest.fixture
def abgefangen(studie, monkeypatch):
    """Fängt ``messe`` ab — acht Blender-Starts gehören nicht in eine Probe."""
    gesehen: dict = {}

    def messe(*, breite, hoehe, samples, arbeit):
        gesehen.update(breite=breite, hoehe=hoehe, samples=samples)
        return [{"raum": "Raum-Nord", "blick": "frontal", "brennweite_mm": 24.0,
                 "quelle": "raumkamera", "status": "ok", "geometrieanteil": 0.933,
                 "spanne_m": 1.191, "stufen": 73, "groesste_ebene": 4.1,
                 "groesste_ebene_anteil": 0.788, "breite": breite, "hoehe": hoehe}]

    monkeypatch.setattr(studie, "messe", messe)
    return studie, gesehen


def test_breite_hoehe_und_samples_kommen_an(abgefangen, capsys):
    studie, gesehen = abgefangen
    assert studie.main(["--breite", "1600", "--hoehe", "992", "--samples", "4"]) == 0
    assert gesehen == {"breite": 1600, "hoehe": 992, "samples": 4}
    assert "1600×992" in capsys.readouterr().out


def test_json_gibt_die_zeilen_roh_aus(abgefangen, capsys):
    """Für ein Blatt, das die Zahlen weiterrechnet — nicht die gesetzte Tabelle."""
    import json

    studie, _ = abgefangen
    assert studie.main(["--json"]) == 0
    zeilen = json.loads(capsys.readouterr().out)
    assert zeilen[0]["groesste_ebene_anteil"] == pytest.approx(0.788)


def test_die_tabelle_nennt_die_flaechenbeherrschten_faelle(abgefangen, capsys):
    """Die Zeile, die jemanden hinsehen lässt — und sie steht nur, wenn es sie gibt."""
    studie, _ = abgefangen
    studie.main([])
    aus = capsys.readouterr().out
    assert "VON EINER FLAECHE BEHERRSCHT" in aus
    assert "78.8 %" in aus
    assert "VORPRUEFUNG" in aus, (
        "Ohne den Vorbehalt liest jemand die Tabelle als Aussage über erzeugte Bilder.")
