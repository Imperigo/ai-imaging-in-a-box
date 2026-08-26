"""Das README ist die Eingangstür der Vertiefungsarbeit — also wird es geprüft wie Code.

Anlass, und er ist gemessen und nicht vermutet
---------------------------------------------
Am 26.08.2026 stand im README **in Fettschrift**, ein echter Render habe *nie*
stattgefunden. Er hatte am 18.08. stattgefunden, und das Ergebnis lag als Datei im Repo
(``auftraege/ergebnisse/auf-20260818-09.json``). Die Testzahl stand bei **1509**, während
die Sammlung **3587** ergab. Vier weitere Zeilen waren in dieselbe Richtung veraltet, zwei
in die andere.

Das ist dieselbe Fehlerart wie eine tote Kante und wie ein Docstring, der eine Prüfung
behauptet: **Es sieht gepflegt aus und trägt nicht.** Ein Dokument, das niemand mitführt,
untertreibt oder übertreibt — die Richtung ist nicht das Problem, dass es niemand merkt,
ist es.

Was hier ausdrücklich **nicht** bewacht wird
--------------------------------------------
**Prosa.** Am selben Vormittag lief eine einmalige Sondierung über Docstrings, die
veraltete Konstanten zitieren: sieben Verdachtsfälle, **ein** echter Treffer. Fünf
Fehlalarme auf einen Treffer ist der Punkt, an dem ein Suchwerkzeug stirbt — man schaltet
es ab, und danach bewacht es nichts mehr.

Bewacht wird darum nur, was **maschinell entscheidbar** ist: eine Zahl, die Existenz einer
Datei, die Existenz einer Funktion. Ob ein Satz noch stimmt, entscheidet weiterhin ein
Mensch — aber er entscheidet es nicht mehr über die drei Dinge, bei denen eine Maschine
es besser kann.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
README = WURZEL / "README.md"

#: Ziele, die absichtlich nicht im Repo liegen. Jeder Eintrag ist eine Entscheidung:
#: ``auftraege/README.md`` liegt sehr wohl da — hier stehen nur Orte, die **zur Laufzeit**
#: entstehen oder jenseits der Prozessgrenze liegen.
NICHT_IM_REPO: tuple[str, ...] = ()


def _text() -> str:
    return README.read_text(encoding="utf-8")


# ---------------------------------------------------------------- die Testzahl

def _gemeldete_testzahl(text: str) -> int:
    treffer = re.findall(r"Tests:\s*\*\*([\d’'  ]+)\*\*", text)
    assert len(treffer) == 1, (
        f"Die Testzahl steht {len(treffer)}× im README. Sie gehört genau einmal dorthin — "
        f"zwei Stellen veralten unabhängig voneinander, und wer die falsche liest, liest "
        f"die alte.")
    return int(re.sub(r"[^\d]", "", treffer[0]))


def _gesammelte_testzahl() -> int:
    """Was ``pytest --collect-only -q`` wirklich zählt.

    Im Unterprozess und nicht über die laufende Sitzung: Ein Test, der die eigene Sammlung
    von innen ausliest, misst den Ausschnitt, den der Aufrufer gerade gewählt hat — ein
    ``pytest tests/test_readme.py`` ergäbe dann eine Handvoll statt der ganzen Sammlung,
    und der Wächter meldete einen Fehler, den es nicht gibt.
    """
    lauf = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=WURZEL, capture_output=True, text=True, timeout=300)
    letzte = [z for z in lauf.stdout.splitlines() if z.strip()]
    assert letzte, f"Die Sammlung hat nichts ausgegeben. rc={lauf.returncode}\n{lauf.stderr[-2000:]}"
    treffer = re.search(r"(\d+)\s+tests?\s+collected", "\n".join(letzte[-5:]))
    assert treffer, (
        f"Aus der Sammlung liess sich keine Zahl lesen. rc={lauf.returncode}\n"
        f"{chr(10).join(letzte[-5:])}")
    return int(treffer.group(1))


def test_die_testzahl_im_readme_stimmt():
    """Genau die Zahl, kein Toleranzband.

    Ein Toleranzband wäre eine Einladung zum Driften: Es hielte still, solange sich wenig
    ändert, und schwiege genau dann, wenn sich über Wochen viel geändert hat — also im
    einzigen Fall, der zählt.
    """
    gemeldet = _gemeldete_testzahl(_text())
    gesammelt = _gesammelte_testzahl()
    assert gemeldet == gesammelt, (
        f"Das README nennt {gemeldet} Tests, gesammelt werden {gesammelt}. Die Zahl im "
        f"README anpassen — sie ist eine Messung und keine Schätzung.")


# ------------------------------------------------------------------ die Links

def _link_ziele(text: str) -> list[tuple[str, str]]:
    """``[Text](ziel)`` → ``(text, ziel)``, ohne externe Adressen und ohne Sprungmarken."""
    roh = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)
    ziele = []
    for beschriftung, ziel in roh:
        if ziel.startswith(("http://", "https://", "mailto:", "#")):
            continue
        ziele.append((beschriftung, ziel.split("#", 1)[0]))
    return ziele


def test_jede_verlinkte_datei_existiert():
    ziele = _link_ziele(_text())
    assert len(ziele) >= 10, (
        f"Nur {len(ziele)} repo-interne Links gefunden. Wenn die Dokumententabelle "
        f"verschwunden ist, bewacht dieser Test nichts mehr.")
    fehlend = [(b, z) for b, z in ziele
               if z not in NICHT_IM_REPO and not (WURZEL / z).exists()]
    assert not fehlend, (
        f"Verlinkt, aber nicht vorhanden: {fehlend}. Ein toter Link im README ist "
        f"schlimmer als ein fehlender Absatz — er behauptet, es gäbe da etwas.")


def test_die_aufgerufenen_werkzeuge_existieren():
    """Was das README als Befehl hinschreibt, muss man auch tippen können."""
    pfade = set(re.findall(r"python3?\s+(tools/\S+\.py)", _text()))
    assert pfade, "Kein Werkzeugaufruf im README gefunden — dann bewacht dieser Test nichts."
    fehlend = sorted(p for p in pfade if not (WURZEL / p).exists())
    assert not fehlend, f"Im README aufgerufen, aber nicht vorhanden: {fehlend}"


# ------------------------------------------------------- die Belege der Regeln

#: Was das README als **ausführbaren** Beleg der vier Regeln nennt. Ein Beleg, der auf
#: eine gelöschte Funktion zeigt, ist schlimmer als keiner: Er lädt dazu ein, die Regel
#: für bewacht zu halten.
#:
#: Geprüft wird die **Existenz**, nicht das Verhalten — dafür gibt es die Tests der
#: jeweiligen Module (`test_backbone.py`, `test_lora.py`, `test_auftrag.py`). Diese
#: Prüfung hier beantwortet eine andere Frage: ob das README noch auf etwas zeigt,
#: das es gibt.
REGEL_BELEGE = (
    ("aiimaging.backbone", "waehle"),
    ("aiimaging.lora", "pruefe_auftrag"),
    ("aiimaging.auftrag", "baue_ergebnis"),
)


@pytest.mark.parametrize("modul, name", REGEL_BELEGE)
def test_der_beleg_einer_regel_existiert(modul, name):
    import importlib
    gegenstand = getattr(importlib.import_module(modul), name, None)
    assert callable(gegenstand), (
        f"{modul}.{name} wird im README als Beleg einer der vier Regeln genannt, ist aber "
        f"nicht aufrufbar. Entweder ist die Funktion umbenannt — dann gehört das README "
        f"nachgezogen — oder die Regel hat ihren ausführbaren Beleg verloren.")


def test_das_readme_nennt_die_belege_auch_wirklich():
    """Die Liste oben darf nicht von der Prosa abkoppeln.

    Sonst wäre sie ein Selbstgespräch: Sie prüfte drei Funktionen, die im README längst
    nicht mehr vorkommen, und schwiege zu den drei, die dort stehen.
    """
    text = _text()
    fehlend = [f"{m}.{n}" for m, n in REGEL_BELEGE if n not in text]
    assert not fehlend, (
        f"Diese Liste nennt Belege, die im README nicht mehr vorkommen: {fehlend}. "
        f"Entweder ins README zurück, oder hier heraus.")


# ------------------------------------------------------------------ das Datum

def test_die_standtabelle_traegt_ein_datum():
    """Ein Stand ohne Datum ist keine Aussage, sondern eine Stimmung.

    Bis zum 26.08.2026 stand die Tabelle sechs Tage lang undatiert da, und niemand konnte
    ihr ansehen, worauf sie sich bezog.
    """
    treffer = re.search(r"\*\*Stand (\d{4})-(\d{2})-(\d{2})\.?\*\*", _text())
    assert treffer, (
        "Im README steht kein Datum der Form **Stand JJJJ-MM-TT**. Wer die Tabelle "
        "anfasst, setzt das Datum mit — sonst weiss der nächste Leser nicht, ob er eine "
        "Momentaufnahme von gestern oder von letztem Monat vor sich hat.")
    jahr = int(treffer.group(1))
    assert 2026 <= jahr <= 2030, f"Das Standdatum {treffer.group(0)!r} ist unplausibel."
