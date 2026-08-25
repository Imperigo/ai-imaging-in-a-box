"""Die Kamera soll die Hüllbox des BAUWERKS rahmen, nicht die der ganzen Szene.

**Der grösste gemessene Fehler dieser Woche** (HomeStation, `auf-13`/`auf-35`, 24.08.2026):
Ein Quader auf einer Platte mit zehnfacher Grundfläche füllt bei `cameras: auto` **1,9 %**
des Bildes, und das Geometrie-Tor kann rechnerisch nicht bestehen. Bei 70 % Bildbreite
entsteht dagegen ein Score von 0,9599.

*Die Kamera rahmt die Szene, gemessen wird das Bauwerk — das ist der Bruch.*

**Ohne eine zweite Hüllbox ist er nicht einmal feststellbar.** Der Runner kennt die
IFC-Klasse jedes Bauteils — er schreibt sie in den Knotennamen —, führte aber nur *eine*
Box. Diese Datei prüft die zweite: die der gebauten Substanz, ohne Gelände.

**Regel 2:** Der Runner wird über den **Dateipfad** geladen, nicht als `aiimaging`-Modul —
derselbe Weg wie in `test_ifc_glb_filter.py`. Ein `import aiimaging.runners…` wäre der
Anfang genau des Weges, den `test_prozessgrenze.py` verbietet.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from aiimaging import maske

RUNNER = (Path(__file__).resolve().parents[1]
          / "src" / "aiimaging" / "runners" / "ifc_to_glb_runner.py")


def _runner():
    spez = importlib.util.spec_from_file_location("ifc_bauwerksbox_pruefling", RUNNER)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


# --------------------------------------------------------------------------------------
# 1 · Die Geländeregel — an zwei Stellen, und darum geprüft
# --------------------------------------------------------------------------------------

def test_der_runner_kennt_ifcsite_als_gelaende():
    modul = _runner()

    assert modul.ist_gelaende_typ("IfcSite") is True
    assert modul.ist_gelaende_typ("IfcWall") is False
    assert modul.ist_gelaende_typ("IfcSlab") is False, (
        "eine Bodenplatte ist gebaute Substanz und kein Gelaende — der Unterschied ist "
        "genau der, um den es hier geht")


def test_die_beiden_gelaenderegeln_passen_zusammen():
    """**Der Test ersetzt den Import, den es nicht geben darf.**

    Der Runner läuft im `.venv-ifc` und darf sich nicht darauf verlassen, das Produkt-Paket
    zu erreichen (Regel 2). Also steht die Liste an zwei Stellen — und eine Zahl an zwei
    Stellen ist an einer davon bereits falsch, sobald sie auseinanderlaufen.

    Geprüft wird nicht Gleichheit, sondern **Verträglichkeit**: Was der Runner als Gelände
    aussortiert, muss die Maskenregel ebenfalls als Gelände erkennen. Die Maskenregel darf
    mehr kennen — sie sieht Materialnamen, nicht IFC-Klassen.
    """
    modul = _runner()

    for typ in modul.GELAENDE_TYPEN:
        knotenname = f"{typ}_1a2b3c"
        assert maske.ist_gelaende(knotenname, maske.GELAENDE_MUSTER), (
            f"{typ!r} sortiert der Runner als Gelaende aus, die Maskenregel erkennt es "
            f"aber nicht — dann steckt es spaeter doch im Bauwerk")


def test_ein_bauteil_ist_nicht_zugleich_gelaende_und_uebersprungen():
    """Die beiden Listen des Runners beantworten verschiedene Fragen und dürfen sich
    nicht überschneiden.

    `NICHT_GEBAUTE_SUBSTANZ` fliegt ganz raus (Luft, Ausschnitte). `GELAENDE_TYPEN` bleibt
    in der glb — es soll gerendert werden, nur nicht gerahmt.
    """
    modul = _runner()

    assert not set(modul.GELAENDE_TYPEN) & set(modul.NICHT_GEBAUTE_SUBSTANZ)
    for typ in modul.GELAENDE_TYPEN:
        assert modul.ist_gebaute_substanz(typ) is True, (
            "Gelaende bleibt in der glb — es wird gerendert, nur nicht gerahmt")


# --------------------------------------------------------------------------------------
# 2 · Die zweite Box wird berichtet — und nicht durch die erste ersetzt
# --------------------------------------------------------------------------------------

def test_der_bericht_fuehrt_beide_boxen_getrennt():
    """`bbox_bauwerk` darf **nie** stillschweigend die Szenenbox sein.

    Das wäre genau die Verwechslung, gegen die das Feld gebaut ist — und sie fiele
    niemandem auf, weil beide Felder dann plausible Zahlen trügen.
    """
    quelle = RUNNER.read_text(encoding="utf-8")

    assert '"bbox_bauwerk"' in quelle
    assert "None if bau_min is None" in quelle, (
        "ohne gebaute Substanz gehoert dort None — kein Rueckfall auf die Szenenbox")
    assert "bbox_bauwerk_note" in quelle, (
        "das Feld braucht seinen Bezugsrahmen dabei; 'bbox' hat seinen auch")


def test_die_zweite_box_haengt_an_der_gelaenderegel_und_nicht_am_zufall():
    quelle = RUNNER.read_text(encoding="utf-8")

    assert "if not ist_gelaende_typ(produkt.is_a()):" in quelle


def test_der_runner_laedt_weiterhin_ohne_ifcopenshell():
    """Die Ergänzung darf die Ladbarkeit nicht kosten.

    Dieses Environment hat kein `.venv-ifc`; eine Regel, die sich nur dort prüfen lässt,
    wo die Bibliothek liegt, wird nie geprüft.
    """
    modul = _runner()

    assert callable(modul.ist_gelaende_typ)
    assert callable(modul.ist_gebaute_substanz)
