"""``docs/UI_BEFUNDE.md`` — jeder Befund kommt an oder sagt, dass er es nicht tut.

Der Anlass
----------
Seit dem 26.08.2026 baut der **`ui`-Worker** die ganze Oberfläche von KosmoOrbit
(Owner-Hinweis). Was uns bei der eigenen Arbeit an der Oberfläche auffällt, gehört ihm
weitergegeben — *als Auftrag*, nicht im Vorbeigehen.

**Und genau das ist die Stelle, an der so etwas sonst verlorengeht:** Ein Befund über die
Anzeige entsteht immer beim Bauen von etwas anderem. U7 und U8 sind an einem einzigen
Abend entstanden — einer beim Anschluss eines Zwischenspeichers, einer beim Beantworten
einer Rückfrage der HomeStation. Keiner hatte mit Oberfläche zu tun, bis er es hatte.

Dieser Wächter erzwingt genau eine Sache: **Ein Befund ist weitergegeben — mit einem
Auftrag, den es gibt — oder ausdrücklich als «noch nicht» geführt.** Die dritte
Möglichkeit, «steht da und ist nie irgendwo angekommen», ist die bequemste, und gegen sie
ist das Blatt gebaut. Dieselbe Bauform wie ``tests/test_einbau_stand.py``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from aiimaging import auftrag

REPO = Path(__file__).resolve().parents[1]
BLATT = REPO / "docs" / "UI_BEFUNDE.md"
OFFEN = REPO / "auftraege" / "offen"

#: Eine Tabellenzeile ``| U1 | Befund | Woher | Stand |``
ZEILE = re.compile(r"^\|\s*(U\d+)\s*\|(.+)\|\s*$")

#: Ein Auftragsname, wie er im Stand steht.
AUFTRAG = re.compile(r"`(auf-\d{8}-\d+)`")

#: Die beiden zulässigen Stände. Ein dritter wäre eine neue Kategorie und gehört
#: benannt, nicht nebenbei eingeführt.
WEITERGEGEBEN = "weitergegeben"
NOCH_NICHT = "noch nicht"


def _zeilen() -> list[tuple[str, list[str]]]:
    ergebnis = []
    for roh in BLATT.read_text(encoding="utf-8").splitlines():
        treffer = ZEILE.match(roh)
        if treffer:
            ergebnis.append((treffer.group(1),
                             [s.strip() for s in treffer.group(2).split("|")]))
    return ergebnis


ZEILEN = _zeilen()


def test_das_blatt_gibt_es_und_hat_befunde():
    assert BLATT.is_file(), f"{BLATT.name} fehlt — dann sammelt niemand mehr."
    assert ZEILEN, "Keine Befunde. Ein leeres Blatt sammelt nichts."


def test_die_nummerierung_hat_keine_luecken():
    """Ein gestrichener Befund ist von einem weitergegebenen nicht zu unterscheiden."""
    nummern = sorted(int(k[1:]) for k, _ in ZEILEN)
    assert nummern == list(range(1, len(nummern) + 1)), (
        f"Lückenhaft: {nummern}. Abgehakt wird, nicht gelöscht.")


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_befund_nennt_woher_er_kommt(kennung, spalten):
    """Ein Befund ohne Herkunft lässt sich später nicht nachprüfen."""
    assert spalten[1].strip(), (
        f"{kennung} sagt nicht, wo er entstanden ist. Ein Befund über die Anzeige "
        f"entsteht immer beim Bauen von etwas anderem — ohne die Stelle ist er in einer "
        f"Woche nicht mehr nachvollziehbar."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_befund_ist_weitergegeben_oder_ausdruecklich_nicht(kennung, spalten):
    """Die dritte Möglichkeit gibt es nicht."""
    stand = spalten[-1].lower()
    assert WEITERGEGEBEN in stand or NOCH_NICHT in stand, (
        f"{kennung} trägt den Stand {spalten[-1]!r}. Erlaubt sind "
        f"{WEITERGEGEBEN!r} (mit Auftrag) oder {NOCH_NICHT!r}. Alles andere heisst: "
        f"steht da und ist nie irgendwo angekommen."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_jeder_weitergegebene_befund_nennt_einen_auftrag_den_es_gibt(kennung, spalten):
    """Ein Verweis auf einen Auftrag, den es nicht gibt, ist schlimmer als keiner."""
    stand = spalten[-1]
    if WEITERGEGEBEN not in stand.lower():
        return
    namen = AUFTRAG.findall(stand)
    assert namen, f"{kennung} gilt als weitergegeben und nennt keinen Auftrag."
    fehlend = [n for n in namen if not (OFFEN / f"{n}.json").is_file()
               and not (REPO / "auftraege" / "ergebnisse" / f"{n}.json").is_file()]
    assert not fehlend, (
        f"{kennung} beruft sich auf {', '.join(fehlend)} — den Auftrag gibt es weder "
        f"offen noch beantwortet."
    )


@pytest.mark.parametrize("kennung,spalten", ZEILEN, ids=[k for k, _ in ZEILEN])
def test_ein_ui_befund_geht_an_den_ui_worker(kennung, spalten):
    """**Der Punkt, an dem das Feld `worker` überhaupt hängt.**

    Ein Oberflächenauftrag beim Cloud-Worker oder bei der HomeStation bliebe liegen —
    nicht, weil ihn jemand ablehnt, sondern weil er nicht zu ihrem Gegenstand gehört.
    Genau dieser Fall ist am 26.08.2026 eingetreten: `auf-52` lag beim Cloud-Worker, bis
    der Owner mitteilte, dass die Oberfläche seit heute jemand anderem gehört.
    """
    import json

    stand = spalten[-1]
    if WEITERGEGEBEN not in stand.lower():
        return
    for name in AUFTRAG.findall(stand):
        for ordner in ("offen", "ergebnisse"):
            pfad = REPO / "auftraege" / ordner / f"{name}.json"
            if not pfad.is_file():
                continue
            satz = json.loads(pfad.read_text(encoding="utf-8"))
            assert satz.get("worker") == auftrag.WORKER_UI, (
                f"{kennung} ist an {name} weitergegeben, und der geht an "
                f"{satz.get('worker')!r} statt an {auftrag.WORKER_UI!r}. Dort bleibt er "
                f"liegen — nicht aus Ablehnung, sondern weil er nicht zum Gegenstand "
                f"des Lesers gehört."
            )


def test_der_ui_worker_ist_ueberhaupt_ein_bekannter_worker():
    """Sonst weist `auftrag.baue_auftrag` jeden Oberflächenauftrag ab."""
    assert auftrag.WORKER_UI in auftrag.WORKER


def test_die_drei_worker_sind_verschieden():
    assert len(set(auftrag.WORKER)) == 3


def test_das_blatt_wird_vom_readme_erwaehnt():
    """Eine Sammelstelle, die niemand findet, sammelt nichts."""
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "UI_BEFUNDE" in readme
