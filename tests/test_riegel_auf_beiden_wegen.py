"""Läuft jeder Riegel auf **beiden** Wegen — oder sagt er, warum nicht?

Der Anlass
----------
Bis zum 26.08.2026 gab es zwei Nähte, die dasselbe versprachen, und **nur eine hatte
einen Ausführer**: Ein über den MCP-Einlass bestellter Render ging auf ``queued`` und
blieb dort für immer liegen. Seither bedient derselbe Abholer beide Ablagen, und alle
Riegel laufen für beide — weil beide durch dasselbe ``verarbeiter`` gehen.

**Genau das soll nicht unbemerkt aufhören.** Wer einen Riegel in ``bruecke.lies_auftrag``
verschiebt, hat ihn für den MCP-Weg gelöscht, ohne dass ein Test rot wird — es sei denn,
dieser hier.

Was hier NICHT geprüft wird
---------------------------
Ob ein Riegel richtig urteilt. Das tun seine eigenen Tests. Hier geht es allein um die
Frage, **wo** er läuft — dieselbe Trennung wie bei ``test_naht_durchreichung.py``.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from aiimaging import abholer, bruecke, eigene_quelle

#: Die acht Namen, die eine Quelle führen muss, damit der Abholer sie bedienen kann.
#: Sie stehen hier und nicht im Abholer, weil ein Vertrag von der Seite geprüft gehört,
#: die ihn braucht — der Abholer selbst könnte ihn nur gegen sich selbst halten.
QUELLEN_VERTRAG = ("QUELLEN_FEHLER", "STATUS_RUNNING", "STATUS_ERROR",
                   "offene_auftraege", "laufzettel_pfad", "lies_auftrag",
                   "setze_status", "schreibe_ergebnis")

QUELLEN = {"bruecke": bruecke, "eigene_quelle": eigene_quelle}


def _funktionen_mit_abbruch() -> set[str]:
    """Jede Funktion in ``abholer``, die ein ``abbruch``-Feld anfasst.

    **Von der anderen Seite gezählt.** Die Tabelle kann keinen Riegel vermissen, den es
    nicht gibt; also wird nicht die Tabelle abgefragt, sondern der Quelltext — und die
    Tabelle muss ihm standhalten. Dasselbe Verfahren hat am 26.08.2026 drei
    Läuferschalter gefunden, die in keiner Durchreichungstabelle standen.
    """
    quelle = Path(inspect.getsourcefile(abholer)).read_text(encoding="utf-8")
    gefunden = set()
    for knoten in ast.parse(quelle).body:
        if not isinstance(knoten, ast.FunctionDef):
            continue
        for unter in ast.walk(knoten):
            if isinstance(unter, ast.Constant) and unter.value == "abbruch":
                gefunden.add(knoten.name)
                break
    return gefunden


# ── Der Quellenvertrag ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(QUELLEN))
def test_jede_quelle_fuehrt_alle_acht_namen(name):
    """Eine Quelle, der ein Name fehlt, bricht erst im Betrieb — und dann mitten im Lauf."""
    modul = QUELLEN[name]
    fehlend = [n for n in QUELLEN_VERTRAG if not hasattr(modul, n)]
    assert not fehlend, (
        f"Quelle {name!r} fehlen: {', '.join(fehlend)}. Der Abholer ruft sie ohne "
        f"Rückfrage; was fehlt, fällt erst auf, wenn ein Auftrag schon auf 'running' "
        f"steht."
    )


def test_beide_quellen_sind_verschiedene_module():
    """Sonst prüfte der Vertrag nur eine Sache zweimal."""
    assert bruecke is not eigene_quelle


def test_der_abholer_nimmt_die_bruecke_als_vorgabe():
    """Die Vorgabe ist der ältere Weg — jeder bestehende Aufruf muss ohne Änderung tragen."""
    for funktion in (abholer.hole_einen, abholer.durchgang, abholer.waisen):
        vorgabe = inspect.signature(funktion).parameters["quelle"].default
        assert vorgabe is bruecke, (
            f"{funktion.__name__} hat nicht mehr die Brücke als Vorgabe. Jeder Aufruf "
            f"ohne `quelle=` würde damit still die Ablage wechseln."
        )


# ── Die Riegeltabelle ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(abholer.RIEGEL))
def test_jeder_riegel_laeuft_auf_beiden_wegen_oder_nennt_den_grund(name):
    """Die dritte Möglichkeit — «steht nirgends» — gibt es hier nicht."""
    eintrag = abholer.RIEGEL[name]
    wege = tuple(eintrag["wege"])
    assert set(wege) <= set(abholer.WEGE), f"{name}: unbekannter Weg in {wege}"
    assert wege, f"{name}: kein Weg genannt — ein Riegel, der nirgends läuft, ist keiner."
    if set(wege) != set(abholer.WEGE):
        assert eintrag.get("begruendung"), (
            f"{name} läuft nur auf {', '.join(wege)} und nennt keinen Grund. Ein "
            f"einseitiger Riegel ohne Begründung ist eine Lücke mit gutem Gewissen — "
            f"genau die Sorte, die dieses Projekt am 26.08.2026 an fünf Stellen fand."
        )
    assert eintrag.get("was"), f"{name}: kein `was` — wogegen riegelt er?"


@pytest.mark.parametrize("name", sorted(abholer.RIEGEL))
def test_jeder_riegel_wird_an_seinem_genannten_ort_auch_gerufen(name):
    """Ein Eintrag, der auf einen Aufruf zeigt, den es nicht gibt, ist schlimmer als keiner."""
    eintrag = abholer.RIEGEL[name]
    ort = eintrag["ort"]
    modulname, _, funktionsname = ort.rpartition(".")
    if modulname:
        modul = __import__(f"aiimaging.{modulname}", fromlist=["x"])
    else:
        modul = abholer
    funktion = getattr(modul, funktionsname)
    text = inspect.getsource(funktion)
    gesucht = name.rpartition(".")[2]
    assert f"{gesucht}(" in text, (
        f"{name} soll in {ort} gerufen werden, kommt dort aber nicht vor. Entweder ist "
        f"der Riegel abgehängt, oder die Tabelle zeigt ins Leere."
    )


def test_jede_funktion_mit_abbruch_steht_in_der_tabelle():
    """Von der anderen Seite gezählt — sonst kann die Tabelle nichts vermissen."""
    bekannt = {n.rpartition(".")[2] for n in abholer.RIEGEL} | set(abholer.KEINE_RIEGEL)
    unbekannt = sorted(_funktionen_mit_abbruch() - bekannt)
    assert not unbekannt, (
        f"Diese Funktionen führen ein `abbruch`-Feld und stehen weder in RIEGEL noch in "
        f"KEINE_RIEGEL: {', '.join(unbekannt)}. Entweder ist es ein Riegel — dann gehört "
        f"er mit seinen Wegen in die Tabelle —, oder es ist keiner, dann gehört der "
        f"Grund nach KEINE_RIEGEL."
    )


def test_keine_riegel_nennt_nur_funktionen_die_es_gibt():
    """Eine Ausnahme für etwas Gelöschtes verdeckt beim nächsten Mal einen echten Fund."""
    for name, grund in abholer.KEINE_RIEGEL.items():
        assert hasattr(abholer, name), f"KEINE_RIEGEL nennt {name!r} — gibt es nicht mehr."
        assert grund.strip(), f"KEINE_RIEGEL[{name!r}] hat keinen Grund."


def test_riegel_und_keine_riegel_ueberschneiden_sich_nicht():
    """Sonst stünde derselbe Name als Riegel UND als Nichtriegel da."""
    doppelt = {n.rpartition(".")[2] for n in abholer.RIEGEL} & set(abholer.KEINE_RIEGEL)
    assert not doppelt, f"Steht in beiden Listen: {', '.join(sorted(doppelt))}"
