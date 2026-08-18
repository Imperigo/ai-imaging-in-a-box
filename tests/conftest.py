"""Gemeinsame Testvoraussetzung: das Paket liegt unter ``src/``, nicht im Wurzelverzeichnis.

Es gibt (noch) keine Installation des Pakets, darum legt diese Datei ``src/`` an den
Anfang von ``sys.path``. Damit laufen die Tests ohne ``pip install -e .``, ohne Netz,
ohne GPU und ohne Blender — genau das verlangt Regel 4: Der Kern ist eine Bibliothek,
die aus reinem Python heraus prüfbar ist.

Zweitens steht hier die **Sonde** :func:`nachgeladene_module`, mit der mehrere Testdateien
prüfen, dass ein Import keinen schweren Stack nachzieht. Warum sie einen eigenen Prozess
startet, steht in ihrem Docstring.
"""
from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

#: Wurzelverzeichnis des Repos (eine Ebene über ``tests/``).
REPO = Path(__file__).resolve().parents[1]

#: Der Produktcode. Alles darunter ausser ``runners/`` läuft im Produkt-Environment.
SRC = REPO / "src"

#: Der Kern selbst — Ziel des Quelltext-Scans in ``test_prozessgrenze.py``.
PAKET = SRC / "aiimaging"

#: Die Skripte jenseits der Prozessgrenze. Sie werden von FREMDEN Interpretern
#: ausgeführt (eigenes venv bzw. Blender) und im Test nie importiert.
RUNNER_DIR = PAKET / "runners"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# --------------------------------------------------------------------------------------
# Die Sonde: Was zieht ein Import nach?
# --------------------------------------------------------------------------------------

#: Kennzeichnung der Antwortzeile des Sondenprogramms. Ohne sie liesse sich „nichts
#: nachgeladen" (leere Zeile) nicht von „Ausgabe verloren gegangen" unterscheiden — und
#: eine Sonde, die im Zweifel schweigt, meldet fälschlich Erfolg.
_MARKE = "NACHGELADEN:"


def nachgeladene_module(modul: str, kandidaten: Sequence[str]) -> list[str]:
    """Welche aus ``kandidaten`` nach ``import <modul>`` in einem FRISCHEN Interpreter liegen.

    Args:
        modul: Vollständiger Modulname, etwa ``"aiimaging.render"``.
        kandidaten: Top-level-Modulnamen, deren Anwesenheit interessiert.

    Returns:
        Die Treffer in der Reihenfolge von ``kandidaten``; leere Liste heisst: keiner davon
        wurde geladen.

    Raises:
        AssertionError: Der Import scheiterte im frischen Prozess, oder die Sonde lieferte
            keine deutbare Antwort.

    Warum ein eigener Prozess und nicht ``sys.modules`` im laufenden Test
    ---------------------------------------------------------------------
    Die Zusicherung lautet: *Dieser Import zieht den GPU-Stack nicht nach.* Gegen
    ``sys.modules`` des Testprozesses geprüft, misst man aber nicht den Import, sondern
    den bisherigen Verlauf des Testlaufs — in einem Environment, in dem ``torch``
    installiert ist und irgendein früherer Test es geladen hat, ist die Prüfung rot,
    ohne dass am geprüften Modul etwas falsch wäre. Umgekehrt ist sie dort, wo der Stack
    gar nicht installiert ist, aus demselben Grund immer grün.

    Beides ist dieselbe Krankheit: **Ein Test, der nur in einer Umgebung gilt, misst die
    Umgebung und nicht den Code.** Und er ist genau dort blind, wo die Zusicherung etwas
    kostet — auf der HomeStation, wo der Stack liegt.

    Der frische Interpreter macht die Vorgeschichte gegenstandslos: Was danach in seinem
    ``sys.modules`` steht, hat dieser eine Import hineingebracht. Damit gilt dasselbe
    Testergebnis im Entwicklungscontainer wie auf der Maschine mit GPU-Stack.

    Die Umgebung des Kindprozesses ist bewusst kahl: ``sys.executable`` ist derselbe
    Interpreter (und damit dasselbe venv wie im Test), ``PYTHONPATH`` zeigt auf ``src/``,
    damit ``aiimaging`` auch ohne Installation gefunden wird, und sonst wird nichts
    durchgereicht.
    """
    kandidaten = tuple(kandidaten)
    programm = (
        "import sys\n"
        f"import {modul}\n"
        f"treffer = [m for m in {kandidaten!r} if m in sys.modules]\n"
        f"print({_MARKE!r} + ','.join(treffer))\n"
    )
    ergebnis = subprocess.run(
        [sys.executable, "-c", programm],
        capture_output=True, text=True, timeout=120,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert ergebnis.returncode == 0, (
        f"'import {modul}' scheiterte im frischen Interpreter:\n{ergebnis.stderr}"
    )
    zeilen = [z for z in ergebnis.stdout.splitlines() if z.startswith(_MARKE)]
    assert len(zeilen) == 1, (
        f"Die Sonde lieferte keine deutbare Antwort für {modul!r}.\n"
        f"stdout: {ergebnis.stdout!r}\nstderr: {ergebnis.stderr!r}"
    )
    return [m for m in zeilen[0][len(_MARKE):].split(",") if m]


# --------------------------------------------------------------------------------------
# Der Fall „kein GPU-Stack" — herstellbar, statt vorgefunden
# --------------------------------------------------------------------------------------

#: Was ``lade_modell`` in ``render.py`` und ``tiefenschaetzer.py`` verzögert importiert.
GPU_STACK = ("torch", "diffusers", "transformers")


@pytest.fixture
def ohne_gpu_stack(monkeypatch):
    """Lässt ``import torch``/``diffusers``/``transformers`` scheitern — auch wo sie liegen.

    Geprüft werden soll: Ist alles andere in Ordnung (Lizenz, Naht, Gewichte), bricht
    ``lade_modell`` am fehlenden GPU-Stack **erklärend** ab und nicht mit einem
    ``ImportError`` aus der Tiefe. Das ist eine Aussage über den Code, nicht über den
    Rechner — sie muss also auch dort prüfbar sein, wo der Stack installiert ist.

    Vorher hing derselbe Test daran, dass ``torch`` zufällig nicht in ``sys.modules``
    stand: Im Container war er immer wahr, auf der HomeStation übersprang er sich selbst
    oder lief in die echte ``diffusers``-Ladeprozedur. Beides ist keine Prüfung.

    ``sys.modules[name] = None`` ist der von CPython vorgesehene Riegel: Die
    Importmaschinerie wirft dann ``ModuleNotFoundError`` (eine ``ImportError``-Unterart),
    ohne die Platte anzufassen. ``monkeypatch`` stellt den Zustand nach dem Test wieder
    her — auch das ist wichtig, denn spätere Tests im selben Prozess dürfen davon nichts
    merken.
    """
    for name in GPU_STACK:
        monkeypatch.setitem(sys.modules, name, None)
