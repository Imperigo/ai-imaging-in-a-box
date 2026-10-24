"""Knoten «Umfeld»: Der Katalog am Knoten (Vis-Werkzeug, ``derive/umfeld.ts``) ist der des Heim-PC.

Der Knoten zeigt, was geladen würde — mit Quelle, Lizenz und Grösse. Gewählt und geladen wird am
Heim-PC (:mod:`aiimaging.umfeld`). Zwei Listen derselben Sache laufen auseinander, wenn niemand sie
vergleicht: Diese Probe liest die TypeScript-Kopie in ``kosmovis/`` und hält sie Feld für Feld gleich.
"""
from __future__ import annotations

import re
from pathlib import Path

from aiimaging import umfeld

TS = Path(__file__).resolve().parents[1] / "kosmovis" / "packages" / "kosmo-kernel" / "src" / \
    "derive" / "umfeld.ts"

_EINTRAG = re.compile(r"\{ id: '([^']+)', kategorie: '([^']+)', label: '([^']+)', quelle: '([^']+)', "
                      r"lizenz: '([^']+)', seite: '([^']+)', mb: ([0-9.]+), vorgabe: (true|false) \}")


def _ts_katalog():
    text = TS.read_text(encoding="utf-8")
    block = text.split("VIS_UMFELD_KATALOG", 1)[1].split("];", 1)[0]
    return [{"id": m[0], "kategorie": m[1], "label": m[2], "quelle": m[3], "lizenz": m[4],
             "seite": m[5], "mb": float(m[6]), "vorgabe": m[7] == "true"}
            for m in _EINTRAG.findall(block)]


def test_katalog_am_knoten_ist_der_des_heim_pc():
    assert _ts_katalog() == umfeld.katalog_fuer_anzeige()


def test_kategorien_dichten_und_schalter_satz_gleich():
    text = TS.read_text(encoding="utf-8")
    for kat, label in umfeld.KATEGORIE_LABEL.items():
        assert f"{{ id: '{kat}', label: '{label}' }}" in text
    assert "['wenig', 'mittel', 'viel']" in text and umfeld.DICHTEN == ("wenig", "mittel", "viel")
    assert f"UMFELD_ANZAHL_HOECHSTENS = {umfeld.ANZAHL_HOECHSTENS};" in text
