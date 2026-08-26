"""Der Wächter über ``docs/SCHWELLENSTUDIE_ECHT_2026-08-26.md``.

Ein Auswertungsdokument veraltet lautlos. Die Zahlen darin sind an einem Tag gemessen
worden; ändert sich danach die Metrik, bleibt das Dokument stehen und behauptet weiter,
was einmal galt. Wer es dann liest, liest eine Messung, die es nicht mehr gibt.

**Was dieser Wächter kann und was nicht** — und der Unterschied ist der Grund, warum es
ihn überhaupt gibt statt eines Vertrauens:

* Die **synthetische Kontrollzeile** (Kapitel 5) läuft ohne Blender, ohne GPU und ohne
  Netz. Sie wird hier **nachgerechnet** und gegen das Dokument gehalten. Fällt die
  Rangbasiertheit, verschiebt sich die beste Schwelle oder ändert sich die Zählung der
  Fehlerarten, wird dieses Dokument rot.
* Die **drei echten Szenen** brauchen einen Renderlauf und lassen sich hier nicht
  nachrechnen. Für sie prüft der Wächter nur, dass ihre Zahlen im Dokument überhaupt
  stehen und untereinander stimmig sind — und das Dokument sagt selbst, dass sie nicht
  laufend geprüft werden.

Ein Wächter, der so tut, als prüfe er mehr als er prüft, wäre schlimmer als keiner.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging.schwellenstudie import (
    HERKUNFT_KARTE,
    VORBEHALT_NICHT_DIE_KETTE,
    baue_testszene,
    studienlauf,
    trennschaerfe_kurve,
)

DOKUMENT = Path(__file__).resolve().parents[1] / "docs" / "SCHWELLENSTUDIE_ECHT_2026-08-26.md"

#: Die Szenen, um die es geht. Der Wächter zählt sie von der anderen Seite: Steht eine
#: im Dokument, die hier fehlt (oder umgekehrt), fällt der Test.
SZENEN = ("Quader", "Hochbau", "Hochbau mit Gelände")


@pytest.fixture(scope="module")
def text() -> str:
    return DOKUMENT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def synthetisch() -> dict:
    """Die Kontrollzeile aus Kapitel 5, hier neu gerechnet — 64 × 64, ohne alles."""
    ergebnis = studienlauf(baue_testszene(64, 64), breite=64, hoehe=64,
                           szene="synthetisch-64")
    ergebnis["kurve"] = trennschaerfe_kurve(ergebnis)
    return ergebnis


def punkt(kurve: dict, schwelle: float) -> dict:
    for p in kurve["punkte"]:
        if abs(p["schwelle"] - schwelle) < 1e-9:
            return p
    raise AssertionError(f"Schwelle {schwelle} steht nicht in der Kurve")


def test_das_dokument_ist_da(text):
    assert len(text) > 4000, "ein Auswertungsdokument mit vier Zeilen ist keines"


def test_die_synthetische_kontrollzeile_stimmt_noch(synthetisch, text):
    """Der eigentliche Wächter: Kapitel 5 wird nachgerechnet.

    Das Dokument nennt für die synthetische Szene bei 64 × 64 die beste Schwelle 0,90 bei
    einer Trefferquote von 0,844, und bei 0,65 achtzehn zu Unrecht freigegebene Fälle bei
    keinem zu Unrecht gesperrten. Diese Zahlen stammen aus derselben Rechnung, die hier
    läuft — sie sind damit keine Behauptung, sondern eine Zusicherung.
    """
    kurve = synthetisch["kurve"]

    assert kurve["beste"]["schwelle"] == pytest.approx(0.90)
    assert kurve["beste"]["treffer"] == pytest.approx(0.844, abs=0.001)
    assert punkt(kurve, 0.65)["falsch_frei"] == 18
    assert punkt(kurve, 0.65)["falsch_gesperrt"] == 0
    assert punkt(kurve, 0.85)["falsch_gesperrt"] == 0, (
        "genau der Satz, der auf echter Geometrie kippt — hier muss er noch gelten"
    )
    assert kurve["n_ausgewertet"] == 32
    assert len(kurve["entdoppelt"]) == 4

    for zahl in ("0,844", "0,438", "0,90"):
        assert zahl in text, f"{zahl} steht nicht mehr im Dokument"


def test_die_beiden_kontrollen_der_metrik_stehen_unveraendert(synthetisch):
    """Rangbasiertheit und Polaritätsblindheit — Befund 1 des Dokuments.

    Sie sind Eigenschaften der Metrik. Fällt eine, ist nicht das Dokument veraltet,
    sondern die Metrik kaputt — und dann wäre alles darin wertlos, nicht nur Kapitel 3.
    """
    kontrollen = synthetisch["kontrollen"]

    assert kontrollen["rangerhaltung"]["bestanden"] is True
    assert kontrollen["rangerhaltung"]["kleinster_score"] == pytest.approx(1.0, abs=1e-9)
    assert kontrollen["polaritaet_unsichtbar"]["wie_erwartet_blind"] is True


def test_jede_szene_des_dokuments_traegt_ihren_geometrieanteil(text):
    """Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde.

    Der Geometrieanteil **ist** hier die Bedingung: An ihm hängt `geom_iou`, und er ist
    der Grund, warum diese zweite Studie überhaupt gefahren wurde. Eine Szene ohne ihn
    wäre eine Kurve ohne Aussage.
    """
    for szene in SZENEN:
        assert szene in text, f"Szene {szene} fehlt im Dokument"
    for anteil in ("0,1111", "0,1730", "0,0822", "0,4727"):
        assert anteil in text, f"Geometrieanteil {anteil} fehlt im Dokument"


def test_der_vorbehalt_steht_im_dokument_und_im_code(text):
    """Was die Studie nicht abdeckt, steht an beiden Orten — und sagt dasselbe."""
    assert "Metrik, nicht die Kette" in text
    assert "Metrik, nicht die Kette" in VORBEHALT_NICHT_DIE_KETTE
    assert "DECKELSTUDIE_2026-08-26" in text
    assert "DECKELSTUDIE_2026-08-26" in VORBEHALT_NICHT_DIE_KETTE


def test_das_dokument_sagt_selbst_was_es_nicht_prueft(text):
    """Die ehrliche Grenze dieses Wächters gehört ins Dokument, nicht nur hierher.

    Die drei echten Szenen brauchen einen Renderlauf; ihre Zahlen sind mit dem Datum des
    Dokuments gemessen und stehen unter keinem Wächter. Wer das Dokument liest, muss das
    wissen, ohne diese Testdatei zu öffnen.
    """
    # Der Zeilenumbruch des Dokuments darf hier nicht mitprüfen — er ist Satz, nicht
    # Inhalt. Ein Wächter, der an einer umbrochenen Zeile scheitert, meldet einen Fehler,
    # den es nicht gibt, und wird darum als Erster abgeschaltet.
    assert re.search(r"nicht\s+laufend\s+geprüft", text)
    assert "tests/test_schwellenstudie_echt.py" in text


def test_die_schwelle_ist_nicht_heimlich_verschoben_worden(text):
    """Kapitel 9 sagt, die Schwelle bleibe bei 0,65. Wenn sie es nicht mehr tut, ist das
    Dokument falsch — und zwar an der Stelle, die am meisten zählt."""
    from aiimaging import geometrie_qa

    assert geometrie_qa.SCHWELLE_GEOMETRIE == pytest.approx(0.65)
    assert "bleibt bei 0,65" in text
    assert "nicht verteidigt, sondern beibehalten" in text


#: Der Ausdruck, mit dem nach absoluten Pfaden gesucht wird. Er steht als Konstante da,
#: weil ihn zwei Tests brauchen: der eigentliche Wächter und seine Gegenprobe.
PFADMUSTER = r"(?<![\w`/])/(?:home|Users|tmp|root)/\S+"


def test_kein_absoluter_pfad_im_dokument(text):
    """Regel 3: Ein Pfad aus dieser Umgebung trüge einen Benutzernamen ins Repo."""
    verdaechtig = re.findall(PFADMUSTER, text)
    assert not verdaechtig, f"absolute Pfade im Dokument: {verdaechtig}"


def test_der_pfadwaechter_findet_ueberhaupt_etwas():
    """Gegenprobe — ohne sie wäre der Test darüber eine leere Zusicherung.

    Ein „nichts gefunden" sagt nur dann etwas, wenn gesucht wurde. Wäre der Ausdruck
    kaputt (ein Tippfehler in der Zeichenklasse genügt), fände er nie etwas, und der
    Wächter darüber bliebe für immer grün — auch über einem Dokument voller Pfade.
    """
    beispiel = "gemessen unter /home/jemand/repo/aus.json und /tmp/reprobe/hb_a400"

    assert re.findall(PFADMUSTER, beispiel) == ["/home/jemand/repo/aus.json",
                                                "/tmp/reprobe/hb_a400"]


def test_die_herkunft_ist_im_ergebnis_und_nicht_nur_im_titel(synthetisch):
    """Der Titel sagt «auf echter Geometrie». Die Kontrollzeile ist es nicht — und ihr
    Ergebnis sagt das selbst, statt es dem Leser zu überlassen."""
    assert synthetisch["herkunft"] == HERKUNFT_KARTE
    assert synthetisch["geometrieanteil"] > 0.4
