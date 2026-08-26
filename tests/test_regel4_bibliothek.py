"""Regel 4, maschinell: Der Kern ist eine Bibliothek und braucht keine Oberfläche.

Warum es diese Datei gibt
-------------------------
Am 26.08.2026 haben nacheinander vier Hausregeln einen Wächter bekommen — und beim
Nachzählen fiel auf, dass **Regel 4 nur zur Hälfte einen hatte.**

`tests/test_prozessgrenze.py` bewacht Regel 2 gründlich: kein ``import bpy``, kein
``import ifcopenshell``, kein Add-on-Gerüst. Regel 4 verlangt aber zwei Dinge, und das
zweite stand nirgends:

    *Kein `import bpy` und **kein UI-Framework-Import** im Kern.*
    *Die Oberfläche ist eine dünne Schicht über der Bibliothek, nie deren Voraussetzung.*

**Gemessen am 26.08.2026 hält die Regel** — ein Import von ``aiimaging`` lädt weder das
MCP-SDK noch ein Oberflächen-Werkzeug noch ``torch``. Sie hält aber aus **Disziplin** und
nicht durch eine Prüfung, und genau dieser Zustand ist an diesem Tag achtmal schiefgegangen:
Was nur im Text steht, veraltet, sobald jemand eine Zeile schreibt, ohne den Text zu lesen.

Die Faustregel der Regel selbst
-------------------------------
    **Was nur über einen Klick erreichbar ist, existiert nicht.**

Ein Test dazu kann nicht prüfen, ob eine Fähigkeit *sinnvoll* ohne Oberfläche nutzbar ist.
Er kann aber prüfen, dass der Kern nichts lädt, was eine Oberfläche voraussetzt — und das
ist die Bedingung, ohne die der Rest gar nicht erst zur Frage steht.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from conftest import SRC
from test_prozessgrenze import importierte_module, kern_dateien

#: Oberflächen-Werkzeuge, die im Kern nichts zu suchen haben.
#:
#: Die Liste nennt, was heute üblich ist — Fenster-Werkzeugkästen, Web-Oberflächen und
#: die beiden Baukästen, mit denen man einer Bibliothek in zehn Zeilen eine Oberfläche
#: verpasst. *Genau diese zehn Zeilen sind die Gefahr:* Sie sind schnell geschrieben, und
#: danach ist die Oberfläche keine dünne Schicht mehr, sondern eine Voraussetzung.
#:
#: ``fastapi`` und ``flask`` stehen mit dabei, obwohl ein Webdienst keine GUI ist. Der
#: Grund ist derselbe: Was einen laufenden Server braucht, ist aus Python heraus nicht
#: einfach aufrufbar — und darum geht es in Regel 4.
UI_WERKZEUGE = (
    "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "kivy",
    "gradio", "streamlit", "flask", "fastapi", "dash", "nicegui", "textual",
)

#: Der optionale Zusatz. Er darf **nicht** vom Kern aus erreichbar sein.
#:
#: ``mcp_server`` ist die einzige Datei des Pakets, die das MCP-SDK braucht — und sie steht
#: als einzige **nicht** in der Sammelzeile von ``aiimaging/__init__.py``. Das ist eine
#: Entscheidung und kein Zufall; hier wird sie festgehalten.
OPTIONALER_ZUSATZ = "mcp_server"


def test_kein_ui_werkzeug_im_kern():
    """Kein Modul des Kerns importiert eine Oberfläche — auch nicht in einer Funktion."""
    funde = []
    for datei in kern_dateien():
        importe = importierte_module(datei.read_text(encoding="utf-8"))
        for werkzeug in UI_WERKZEUGE:
            if werkzeug in importe:
                funde.append(f"{datei.name}: import {werkzeug}")
    assert not funde, (
        "Oberflächen-Importe im Kern (Regel 4):\n  " + "\n  ".join(funde) +
        "\n\nDie Oberfläche ist eine dünne Schicht über der Bibliothek, nie deren "
        "Voraussetzung. Was hier gebraucht wird, gehört in ein eigenes Modul, das den "
        "Kern benutzt — nicht umgekehrt.")


def test_der_scanner_wuerde_ein_ui_werkzeug_auch_finden():
    """Selbstprobe. **Ein Test, der nichts findet, bewacht nichts.**

    Ohne sie wäre die Zusicherung oben nicht von einer unterscheidbar, die den falschen
    Namen sucht oder gar keinen — sie wäre grün, weil sie blind ist, und niemand wüsste es.
    """
    quelle = "def zeichne():\n    import tkinter\n    return tkinter\n"
    assert "tkinter" in importierte_module(quelle)
    quelle_from = "from gradio import Blocks\n"
    assert "gradio" in importierte_module(quelle_from)


def test_die_liste_der_ui_werkzeuge_ist_nicht_leer():
    """Sonst liefe die Schleife oben über nichts und wäre vakuumwahr.

    Dieselbe Gestalt, die `tools/vakuumprobe.py` in dieser Suite sucht: eine Zusicherung
    über **alle** Elemente einer Sammlung, die auch bei leerer Sammlung hält.
    """
    assert len(UI_WERKZEUGE) >= 10


@pytest.mark.parametrize("datei", kern_dateien(), ids=lambda p: p.name)
def test_kein_kernmodul_zieht_den_optionalen_zusatz_herein(datei):
    """``mcp_server`` darf von keinem anderen Modul importiert werden.

    *Er ist die dünne Schicht.* Zöge ihn ein Kernmodul herein, wäre das MCP-SDK eine
    Voraussetzung der Bibliothek — und die Richtung der Abhängigkeit stünde auf dem Kopf,
    ohne dass irgendetwas rot würde.
    """
    if datei.stem == OPTIONALER_ZUSATZ:
        pytest.skip("die Schicht selbst")
    quelle = datei.read_text(encoding="utf-8")
    treffer = [z for z in quelle.splitlines()
               if z.lstrip().startswith(("import ", "from "))
               and OPTIONALER_ZUSATZ in z]
    assert not treffer, (
        f"{datei.name} importiert {OPTIONALER_ZUSATZ!r}:\n  " + "\n  ".join(treffer))


def test_der_import_des_kerns_laedt_keine_oberflaeche_und_kein_sdk():
    """Die Probe am laufenden Interpreter — was der Quelltext sagt, ist die halbe Auskunft.

    Ein Modul kann eine Oberfläche auch über eine dritte Bibliothek hereinziehen, und das
    sähe im eigenen Quelltext nach nichts aus. Gefragt ist darum, was nach dem Import
    **wirklich geladen** ist.

    ``torch`` steht mit in der Liste, obwohl es keine Oberfläche ist: Das `NOTICE` sagt
    zu, dass die Bildmodell-Stufe erst dort lädt, wo wirklich gerendert wird. Ein Import
    von ``aiimaging``, der ``torch`` mitbrächte, wäre dieselbe Art von stiller
    Vertragsverletzung.
    """
    programm = (
        "import sys\n"
        f"sys.path.insert(0, {str(SRC)!r})\n"
        "import aiimaging\n"
        "verboten = {'mcp', 'torch', 'diffusers', 'transformers', 'bpy', 'ifcopenshell'}\n"
        + f"verboten |= set({list(UI_WERKZEUGE)!r})\n"
        "geladen = sorted(m for m in sys.modules if m.split('.')[0] in verboten)\n"
        "print(','.join(geladen))\n"
    )
    lauf = subprocess.run([sys.executable, "-c", programm],
                          capture_output=True, text=True, check=False)
    assert lauf.returncode == 0, f"Der Kern liess sich nicht importieren:\n{lauf.stderr}"
    geladen = [m for m in lauf.stdout.strip().split(",") if m]
    assert not geladen, (
        f"Der blosse Import von `aiimaging` hat {geladen} geladen. Regel 4: Die "
        f"Bibliothek muss ohne Oberfläche und ohne schwere Fremdstufe nutzbar sein — "
        f"und das `NOTICE` sagt für torch/diffusers ausdrücklich zu, dass sie erst dort "
        f"laden, wo wirklich gerendert wird.")


def test_die_selbstprobe_dieser_datei_haelt():
    """Gegenprobe zur Zusicherung oben: Ein frischer Interpreter **kann** so etwas melden.

    Ohne sie wäre der Unterprozess-Test nicht von einem zu unterscheiden, dessen Programm
    schlicht nichts ausgibt — er wäre grün, weil er stumm ist.
    """
    programm = ("import sys, json\n"
                "geladen = sorted(m for m in sys.modules if m.split('.')[0] in {'json'})\n"
                "print(','.join(geladen))\n")
    lauf = subprocess.run([sys.executable, "-c", programm],
                          capture_output=True, text=True, check=False)
    # `json` UND seine Untermodule (`json.decoder` …) teilen sich denselben Kopf — die
    # Gegenprobe fragt darum nach dem Vorkommen und nicht nach Gleichheit. *Die erste
    # Fassung verglich auf Gleichheit und war prompt rot; eine Gegenprobe, die selbst
    # falsch gebaut ist, widerlegt nichts.*
    gemeldet = [m for m in lauf.stdout.strip().split(",") if m]
    assert "json" in gemeldet, (
        f"Die Gegenprobe liefert {gemeldet!r} und nennt `json` nicht — dann sagt der "
        f"Test darüber ebenfalls nichts aus.")
