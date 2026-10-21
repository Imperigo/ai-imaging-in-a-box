"""Grossansicht und Vergleich (Video-Befunde L4-14/L4-15/L4-5/L4-1, 21.10.2026): trägt der Bau der Knotenansicht sie?

Die Proben der Bedienung laufen in der Kopie (`kv-grossansicht.test.tsx`, e2e `kv-grossansicht.spec.ts`). Hier wird
nur gewacht, dass der ausgelieferte Bau sie enthält und ihre Stilregeln auf oberster Ebene stehen — dieselbe Wache
wie für die Varianten-Daumen (eine verlorene Klammer legte am 21.10.2026 alle späteren Regeln still).
"""
from __future__ import annotations

import re

from test_varianten_daumen import DIST, QUELLE, _tiefe_vor


def _bau():
    seite = (DIST / "index.html").read_text(encoding="utf-8")
    css = (DIST / "assets" / re.findall(r'assets/(index-[^"]+\.css)', seite)[0]).read_text(encoding="utf-8")
    js = (DIST / "assets" / re.findall(r'assets/(index-[^"]+\.js)', seite)[0]).read_text(encoding="utf-8")
    return css, js


def test_der_bau_traegt_grossansicht_vergleich_und_schalter():
    _css, js = _bau()
    for kennung in ("render-verlauf-gross-pruefung", "render-verlauf-gross-nebeneinander", "render-gross-bei-fertig",
                    "render-verlauf-gross-deckung", "grossBeiFertig"):
        assert kennung in js, kennung


def test_die_regeln_der_grossansicht_greifen():
    css, _js = _bau()
    for regel in (".vis-gross-reihe{", ".vis-gross-deckung{", ".vis-gross-schalter{"):
        stelle = css.find(regel)
        assert stelle >= 0, regel
        assert _tiefe_vor(css, stelle) == 0, f"{regel} steht verschachtelt und greift nicht"


def test_die_quellen_liegen_in_der_kopie():
    for datei in ("grossansicht.ts", "kontext-hinweis.ts", "vis-grossansicht.css"):
        assert (QUELLE / datei).is_file(), datei
