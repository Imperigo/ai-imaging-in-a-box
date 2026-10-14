"""Strg+Z / ⌘Z in der Visbox-Knotenansicht (auf-20261014-284 D5, 14.10.2026).

In KosmoOrbit hängt das Kürzel am Hauptprogramm (`App.tsx`), das nicht kopiert ist; in Visbox
wirkte Strg+Z darum nicht. Der Wirt hängt es jetzt selbst an (`visbox-knoten/src/kurztasten.ts`).
Die Logik läuft hier unter Node (Typen werden nur abgestreift), die Verdrahtung wird am Text geprüft.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"

PROBE = """
const m = await import(process.argv[1]);
const t = (o) => m.verlaufsschritt({ key: 'z', ctrlKey: false, metaKey: false, altKey: false,
  shiftKey: false, target: { tagName: 'DIV' }, ...o });
console.log(JSON.stringify({
  strgZ: t({ ctrlKey: true }), cmdZ: t({ metaKey: true }),
  cmdShiftZ: t({ metaKey: true, shiftKey: true }), strgY: t({ ctrlKey: true, key: 'y' }),
  ohne: t({}), alt: t({ ctrlKey: true, altKey: true }),
  text: t({ ctrlKey: true, target: { tagName: 'INPUT', type: 'text' } }),
  feld: t({ ctrlKey: true, target: { tagName: 'TEXTAREA' } }),
  haekchen: t({ ctrlKey: true, target: { tagName: 'INPUT', type: 'checkbox' } }),
}));
"""


def test_der_wirt_haengt_rueckgaengig_und_wiederholen_an():
    haupt = (WIRT / "main.tsx").read_text(encoding="utf-8")
    assert "haengeVerlaufKurztastenAn(window, {" in haupt
    assert "undo: () => useProject.getState().undo()" in haupt
    assert "redo: () => useProject.getState().redo()" in haupt


@pytest.mark.skipif(shutil.which("node") is None, reason="ohne Node keine Logikprobe")
def test_welche_taste_was_tut(tmp_path):
    lauf = subprocess.run(
        ["node", "--experimental-strip-types", "--input-type=module", "-e", PROBE,
         (WIRT / "kurztasten.ts").as_uri()],
        capture_output=True, text=True, timeout=60)
    if lauf.returncode != 0 and "strip-types" in lauf.stderr:
        pytest.skip("Diese Node-Fassung streift keine Typen ab")
    assert lauf.returncode == 0, lauf.stderr
    erg = json.loads(lauf.stdout.strip().splitlines()[-1])
    assert erg == {"strgZ": "rueckgaengig", "cmdZ": "rueckgaengig", "cmdShiftZ": "wiederholen",
                   "strgY": "wiederholen", "ohne": None, "alt": None, "text": None,
                   "feld": None, "haekchen": "rueckgaengig"}
