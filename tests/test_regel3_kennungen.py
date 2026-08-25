"""Regel 3, dritter Absatz: keine Namen in Pfaden — jetzt als Prüfung statt als Satz.

**Der Anlass ist ein Fund im eigenen Repo** (24.08.2026): In fünf Ergebnisdateien und zwei
Dokumenten stand seit dem **18.08.** der Klarname des Owners. Hereingekommen ist er nicht
durch Nachlässigkeit beim Schreiben, sondern durch **Blender-Fehlertexte** — ein Traceback
bringt den vollen Pfad des Skripts mit, und darin steht der Benutzername. *Hingeschrieben
hat ihn niemand; er ist mitgereist.*

`_wehre_bilddaten_ab` sah genau diese Felder an — aber nur auf Binärdaten und Länge. Ein
Name in einem Pfad ist beides nicht. Und ein **Auftrag** wurde überhaupt nicht geprüft.

Am selben Tag hat die HomeStation denselben Fehler auf ihrer Seite gefunden und von Hand
behoben: *«Die Anleitung zur Regel verletzte die Regel.»* Von Hand heisst: beim nächsten
Mal wieder.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from aiimaging import auftrag
from aiimaging.auftrag import NUTZER_ERSATZ, AuftragError

WURZEL = Path(__file__).resolve().parents[1]

#: Platzhalter, die ausdrücklich **kein** Name sind und darum stehenbleiben dürfen.
#:
#: Die Liste ist kurz gehalten und wird gelesen, nicht gepflegt — dasselbe Prinzip wie
#: `GEWOLLTE_TRENNUNGEN` in `test_lexikon.py`. Wer hier etwas einträgt, erklärt damit, dass
#: es der Name **keines Menschen** ist. Eine Liste, die mitwächst, ist keine Prüfung mehr.
ERLAUBT = {NUTZER_ERSATZ, "nutzer", "user", "vorname-nachname", "jemand", "USER", "HOME"}

SUCHE = re.compile(r"/home/([^/\s\"'<>)\]]+)|/Users/([^/\s\"'<>)\]]+)")


# --------------------------------------------------------------------------------------
# 1 · Das Ersetzen selbst
# --------------------------------------------------------------------------------------

def test_der_name_faellt_weg_und_der_pfad_bleibt():
    """**Der Rest des Pfades ist die Auskunft** — er sagt, welches Skript gestolpert ist.

    Den ganzen Pfad zu tilgen machte aus einem brauchbaren Fehlertext einen unbrauchbaren.
    """
    text, n = auftrag.ohne_kennungen(
        "/home/vorname-nachname/repo/src/x.py:210: DeprecationWarning")

    assert n == 1
    assert text == f"/home/{NUTZER_ERSATZ}/repo/src/x.py:210: DeprecationWarning"


@pytest.mark.parametrize("roh,erwartet", [
    ("/Users/Jemand/projekt", f"/Users/{NUTZER_ERSATZ}/projekt"),
    ("C:\\Users\\Wer\\projekt", f"C:\\Users\\{NUTZER_ERSATZ}\\projekt"),
])
def test_auch_die_fremden_schreibweisen(roh, erwartet):
    """Nicht jede Messung läuft auf Linux, und ein Muster, das nur eine Form kennt, ist
    an den übrigen blind."""
    assert auftrag.ohne_kennungen(roh)[0] == erwartet


def test_mehrere_treffer_werden_gezaehlt_und_nicht_bloss_gemeldet():
    text = ("/home/a/x und /home/b/y und /Users/c/z")

    sauber, n = auftrag.ohne_kennungen(text)

    assert n == 3
    assert "/home/a" not in sauber and "/Users/c" not in sauber


def test_ein_satz_ohne_namen_bleibt_unveraendert():
    """Gegenprobe: Das Muster darf nicht überall zuschlagen."""
    satz = {"beschreibung": "Lauf unter /ai/geometrie/testbau.ifc pruefen.",
            "params": {"pfad": "build/testbau.ifc"}}

    sauber, n = auftrag.regel3_saeubern(satz)

    assert n == 0
    assert sauber == satz
    assert "regel3_ersetzt" not in sauber


def test_auch_schluessel_werden_gesaeubert():
    """Ein Name kann auch links vom Doppelpunkt stehen — etwa als Dateipfad-Schlüssel."""
    sauber, n = auftrag.regel3_saeubern({"/home/jemand/x.png": 3})

    assert n == 1
    assert f"/home/{NUTZER_ERSATZ}/x.png" in sauber


def test_der_satz_wird_nicht_an_ort_und_stelle_geaendert():
    """Eine Funktion, die ihr Argument umschreibt, macht aus einer Prüfung eine Nebenwirkung."""
    satz = {"urteil": "/home/jemand/x"}
    vorher = dict(satz)

    auftrag.regel3_saeubern(satz)

    assert satz == vorher


def test_kein_woerterbuch_wird_abgewiesen():
    with pytest.raises(AuftragError, match="kein Wörterbuch"):
        auftrag.regel3_saeubern(["/home/jemand/x"])


# --------------------------------------------------------------------------------------
# 2 · Es greift dort, wo geschrieben wird — und ist nicht zu umgehen
# --------------------------------------------------------------------------------------

def test_ein_auftrag_wird_beim_schreiben_gesaeubert(tmp_path):
    """**Bis zum 24.08.2026 wurde ein Auftrag darauf überhaupt nicht geprüft.**"""
    satz = auftrag.baue_auftrag(
        auftrag_id="auf-20260824-99", art="qa", synthetisch=True,
        beschreibung="Lauf unter /home/vorname-nachname/repo pruefen.")

    ziel = auftrag.schreibe_auftrag(satz, tmp_path)
    inhalt = json.loads(ziel.read_text(encoding="utf-8"))

    assert "vorname-nachname" not in ziel.read_text(encoding="utf-8")
    assert inhalt["regel3_ersetzt"] == 1, (
        "die Zahl gehoert in die Datei — sonst waere es eine stille Reparatur")


def test_ein_ergebnis_ebenfalls(tmp_path):
    """Hier kommen die Fehlertexte an, hier ist der Weg, auf dem es passiert ist."""
    satz = auftrag.baue_ergebnis(
        auftrag_id="auf-20260824-99", status="fehler",
        urteil={"grund": "SeamError: /home/vorname-nachname/repo/x.py:210"})

    ziel = auftrag.schreibe_ergebnis(satz, tmp_path)

    assert "vorname-nachname" not in ziel.read_text(encoding="utf-8")
    assert f"/home/{NUTZER_ERSATZ}/repo/x.py:210" in ziel.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------
# 3 · Und das ganze Repo bleibt sauber
# --------------------------------------------------------------------------------------

#: Die einzige Datei, die Beispielpfade tragen **muss** — diese hier.
#:
#: Die Ausnahme steht auf **einer** Datei und nicht in :data:`ERLAUBT`. Der Unterschied
#: ist wesentlich: Eine wachsende Erlaubnisliste höhlt die Prüfung überall aus, eine
#: benannte Datei nur hier. Und hier stehen ausschliesslich Beispiele — wer in dieser
#: Datei einen echten Namen unterbringt, tut es mit Absicht.
AUSGENOMMEN = {"tests/test_regel3_kennungen.py"}


def _versionierte_textdateien() -> list[Path]:
    """Nur, was wirklich im Repo steht — nicht das Arbeitsverzeichnis mit Bauresten."""
    roh = subprocess.run(["git", "ls-files"], cwd=WURZEL, capture_output=True,
                         text=True, check=True).stdout.split("\n")
    endungen = {".md", ".json", ".py", ".txt", ".toml", ".yml", ".yaml", ".cfg"}
    return [WURZEL / n for n in roh
            if n and (WURZEL / n).suffix in endungen and (WURZEL / n).is_file()]


def test_im_ganzen_repo_steht_kein_benutzername_in_einem_pfad():
    """**Die Prüfung, die es seit dem 18.08. hätte geben müssen.**

    Sie sieht das an, was wirklich eingecheckt ist. Ein Fund hier ist kein Stilfehler: Es
    ist ein Name in einem öffentlichen Repo.
    """
    funde: list[str] = []
    for pfad in _versionierte_textdateien():
        if str(pfad.relative_to(WURZEL)) in AUSGENOMMEN:
            continue
        try:
            text = pfad.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for treffer in SUCHE.finditer(text):
            name = treffer.group(1) or treffer.group(2)
            if name not in ERLAUBT:
                funde.append(f"{pfad.relative_to(WURZEL)}: {treffer.group(0)}")

    assert not funde, (
        "Benutzernamen in Pfaden (Regel 3):\n  " + "\n  ".join(sorted(set(funde))[:20]))


def test_gegenprobe_die_pruefung_findet_ueberhaupt_etwas():
    """Ohne sie wäre der Test darüber vakuumwahr, sobald das Suchmuster kaputtginge.

    Zweiter Teil: Der **Platzhalter** wird gar nicht erst erfasst — er trägt spitze
    Klammern, und die stehen in keinem Benutzernamen. Er hängt damit nicht an der
    Erlaubnisliste, sondern fällt schon aus dem Muster. Das ist die stabilere von beiden
    Möglichkeiten.
    """
    assert SUCHE.search("/home/echter-name/x") is not None
    assert SUCHE.search(f"/home/{NUTZER_ERSATZ}/x") is None


def test_die_ausnahme_ist_genau_eine_datei_und_zwar_diese():
    """Eine Ausnahmeliste, die wächst, ist keine Prüfung mehr.

    Sie steht auf **einer** Datei — dieser —, weil eine Prüfung auf Beispielpfade
    notwendig Beispielpfade enthält. Jede weitere Datei hier wäre ein Loch.
    """
    assert AUSGENOMMEN == {"tests/test_regel3_kennungen.py"}
    assert (WURZEL / "tests/test_regel3_kennungen.py").resolve() == Path(__file__).resolve()


def test_jeder_erlaubte_platzhalter_ist_auch_wirklich_einer():
    """Wer die Liste erweitert, muss Farbe bekennen.

    Sonst wäre sie ein Freibrief: Man trägt einen echten Namen ein, und die Prüfung
    schweigt für immer. Ein Platzhalter besteht aus einem Wort ohne Bindestrich-Vornamen
    und ist im Repo als Beispiel erkennbar.
    """
    for name in ERLAUBT:
        assert name.islower() or name.isupper() or name == NUTZER_ERSATZ, (
            f"{name!r} sieht nach einem Eigennamen aus — Eigennamen gehoeren nicht in "
            f"diese Liste, sondern aus dem Repo")
