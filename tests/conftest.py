"""Gemeinsame Testvoraussetzung: das Paket liegt unter ``src/``, nicht im Wurzelverzeichnis.

Es gibt (noch) keine Installation des Pakets, darum legt diese Datei ``src/`` an den
Anfang von ``sys.path``. Damit laufen die Tests ohne ``pip install -e .``, ohne Netz,
ohne GPU und ohne Blender — genau das verlangt Regel 4: Der Kern ist eine Bibliothek,
die aus reinem Python heraus prüfbar ist.
"""
from __future__ import annotations

import sys
from pathlib import Path

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
