"""Das Werkzeug, das tote Kanten sucht — und selbst geprüft wird.

**Der Anlass ist eine Zählung, die den gefährlichen Fall übersehen hat.** Am 25.08.2026
wurde von Hand gezählt: 256 öffentliche Funktionen, 67 vom Produktpfad nicht gerufen,
davon **vier** ohne jeden Ruf. Das Kriterium war *«null Produktrufe UND null Testrufe»* —
und genau dieses Kriterium übergeht die schlimmste Sorte.

Denn eine Funktion **mit** gründlichen Tests und **ohne** Aufrufer sieht nicht verdächtig
aus, sondern **fertig**. Sie ist grün, sie hat einen ausführlichen Docstring, sie
beantwortet eine Frage, die jemand gestellt hat — und sie beantwortet sie nie. *Die
Testsuite ist dann das einzige Programm, das sie benutzt.*

Beide toten Kanten des 26.08.2026 waren von dieser Art: `bbox_bauwerk` samt
`rahmungsverhaeltnis` und `geometrie_qa.erreichbarkeit`. Beide sind von **aussen** gemeldet
worden, weil hier niemand danach gesucht hat.

**Warum ein Test für ein Werkzeug, das nur meldet.** Weil es sonst selbst die Fehlerart
bekäme, gegen die es gebaut ist: Ein Suchwerkzeug, das nichts mehr findet, weil seine
Erhebung stillschweigend kaputtgegangen ist, sieht aus wie ein sauberes Repo.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WERKZEUG = Path(__file__).resolve().parents[1] / "tools" / "tote_kanten.py"


def _werkzeug():
    spez = importlib.util.spec_from_file_location("tote_kanten_pruefling", WERKZEUG)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def erhebung():
    return _werkzeug().erhebung()


def test_die_erhebung_findet_ueberhaupt_funktionen(erhebung):
    """Die Voraussetzung für alles Übrige. Eine Erhebung, die null Funktionen kennt,
    meldet null tote Kanten und sieht dabei beruhigend aus."""
    assert erhebung["n_definitionen"] > 200
    assert erhebung["n_erreicht"] > 200


def test_die_kette_selbst_gilt_als_erreichbar(erhebung):
    """Die Gegenprobe zur Erreichbarkeit: Was `tools/abholen.py` startet, MUSS als
    erreichbar gelten. Sonst wäre die Wurzelmenge kaputt und jede Meldung wertlos."""
    tot = {e["name"] for e in erhebung["nur_tests"] + erhebung["nirgends"]}

    for lebendig in ("verarbeiter", "hole_einen", "durchgang", "befund_kurz",
                     "lies_szene", "rendere", "kamerasatz", "qa_gegen_soll"):
        assert lebendig not in tot, f"{lebendig} liegt auf dem Produktpfad"


def test_die_beiden_funde_vom_26_august_gelten_jetzt_als_angeschlossen(erhebung):
    """**Der Rückblick, der das Werkzeug rechtfertigt.** Beide waren am Morgen tot und
    sind es am Abend nicht mehr. Meldete das Werkzeug sie weiter, wäre seine Erhebung
    falsch; meldete es sie nie, hätte es sie auch am Morgen nicht gefunden."""
    tot = {e["name"] for e in erhebung["nur_tests"] + erhebung["nirgends"]}

    assert "rahmungsverhaeltnis" not in tot
    assert "erreichbarkeit" not in tot
    assert "aus_bestellung" not in tot


def test_ein_studienmodul_darf_ungerufen_sein_und_wird_trotzdem_genannt(erhebung):
    """`stilstudie` und `schwellenstudie` sind Analysemodule; kein Renderlauf erreicht
    sie. Das Werkzeug **verschweigt sie nicht** — es gruppiert sie nach Modul, damit ein
    Mensch in einem Blick sieht, dass es ein ganzes Modul ist und keine Einzelfälle."""
    module = {e["orte"][0][0] for e in erhebung["nur_tests"]}

    assert any("stilstudie" in m for m in module)


def test_jede_meldung_traegt_ihren_fundort(erhebung):
    """Eine Meldung ohne Datei und Zeile ist der Anfang einer Suche und nicht einer
    Untersuchung."""
    for eintrag in erhebung["nur_tests"] + erhebung["nirgends"]:
        datei, zeile = eintrag["orte"][0]
        assert datei.startswith("src/aiimaging/")
        assert zeile > 0


def test_private_funktionen_werden_nicht_gemeldet(erhebung):
    """Ein Helfer mit Unterstrich ist keine tote Kante, sondern ein Helfer. Ihn zu melden
    wäre die Sorte Fehlalarm, an der ein Suchwerkzeug stirbt."""
    for eintrag in erhebung["nur_tests"] + erhebung["nirgends"]:
        assert not eintrag["name"].startswith("_"), eintrag["name"]


def test_die_ausnahmeliste_ist_kurz_und_begruendet():
    """Jeder Eintrag ist ein Versprechen, dass jemand nachgesehen hat. *Eine wachsende
    Liste ist ein Zeichen dafür, dass weggesehen statt geprüft wird* — darum steht die
    Schranke hier und nicht nur im Docstring."""
    ausnahmen = _werkzeug().ABSICHTLICH

    assert len(ausnahmen) <= 10, "eine lange Ausnahmeliste ist kein Werkzeug mehr"
    for name, grund in ausnahmen.items():
        assert len(grund) > 15, f"{name} hat keine Begruendung, nur ein Wort"


def test_die_beiden_gruppen_ueberschneiden_sich_nicht(erhebung):
    """«Nur über Tests erreichbar» und «gar nicht genannt» verlangen verschiedene
    Handgriffe — anschliessen gegen prüfen-oder-löschen. Wäre eine Funktion in beiden,
    wüsste niemand welchen."""
    a = {e["name"] for e in erhebung["nur_tests"]}
    b = {e["name"] for e in erhebung["nirgends"]}

    assert a & b == set()


def test_das_werkzeug_laeuft_durch_und_meldet_nichts_als_fehler():
    """Es **meldet**, es prüft nicht. Ein Rückgabewert ungleich null machte es zu einem
    Test — und ein Test mit dutzenden Fehlalarmen wird abgeschaltet."""
    assert _werkzeug().main([]) == 0
