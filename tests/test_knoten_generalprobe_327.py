"""Folgen der Generalprobe 327 in der Knotenansicht (22.10.2026, Protokoll 74 §226).

Die Logik prüft ``vitest`` (``kosmovis/apps/visbox-knoten/test/graph-sichern.test.ts``,
``…/varianten.test.tsx``, drüben ``kv-varianten.test.tsx``). Bewacht wird hier die **Verdrahtung**
und die Antwort auf die Frage aus S3:

* S2 — nach «Datei laden …» in eine andere Mappe legt die Seite deren Graph (oder den fertigen
  Anfang), ohne Neuladen.
* S3 — der Varianten-Knoten nennt die Richtungen des Knotens «Kamera», nicht die drei der Vorgabe.
* S3 — «Himmel: keiner» am Render-Knoten ist ``render.himmel``, das nie gesendet wird; die
  Knotenansicht setzt ``vis.himmel_sichtbar`` und die zwei anderen Schalter nicht, darum gilt am
  Heim-PC dieselbe Vorgabe (Entscheid 126) wie bei einem Auftrag über die Brücke ohne Schalter.
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KV = WURZEL / "kosmovis"
WIRT = KV / "apps" / "visbox-knoten"
VIS = KV / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8")


def test_s2_die_seite_meldet_den_mappenwechsel_an():
    main = _lies(WIRT / "src" / "main.tsx")
    assert "registriereMappenWechsel(() => graphDerNeuenMappe())" in main


def test_s2_verfolge_ruft_den_wechsel_nur_bei_einer_anderen_mappe():
    mappe = _lies(WIRT / "src" / "mappe.ts")
    rumpf = mappe[mappe.index("export async function verfolge("):]
    rumpf = rumpf[:rumpf.index("\n}\n")]
    assert "const vorher = offeneMappe;" in rumpf
    assert re.search(r"await ladeMappe\(\);\s*\n(?:\s*//.*\n)*\s*if \(offeneMappe !== vorher && beiAndererMappe\) await beiAndererMappe\(\);",
                     rumpf), "der Wechsel gehört direkt hinter das Laden der neuen Mappe"


def test_s2_der_neue_graph_ersetzt_den_alten_oder_der_anfang_kommt():
    sichern = _lies(WIRT / "src" / "graph-sichern.ts")
    rumpf = sichern[sichern.index("export async function graphDerNeuenMappe("):]
    rumpf = rumpf[:rumpf.index("\n}\n")]
    # Erst holen, dann in einem Schritt tauschen — sonst könnte das Sichern einen leeren Stand schicken.
    assert rumpf.index("holen('./graph')") < rumpf.index("doc.apply(alt.map(")
    assert "startGraphAnlegen()" in rumpf


def test_s3_varianten_lesen_die_auto_kamera():
    varianten = _lies(VIS / "varianten.ts")
    assert ".kamerasAuto" in varianten
    assert "heimRichtungen(doc, graph, render)" in varianten


def test_s3_himmel_am_render_knoten_wird_nicht_gesendet_und_die_schalter_setzt_die_knotenansicht_nicht():
    jobs = _lies(VIS / "vis-jobs.ts")
    block = jobs[jobs.index("export const NICHT_GESENDET = {"):]
    block = block[:block.index("} as const;")]
    assert "'himmel'" in block
    for schalter in ("himmel_sichtbar", "material_vorne", "umriss_halten"):
        treffer = [p.name for p in VIS.rglob("*.ts*") if schalter in _lies(p)]
        assert not treffer, f"{schalter} steht jetzt in {treffer} — dann gilt am Heim-PC nicht mehr die Vorgabe"


def test_die_vitest_proben_liegen():
    assert "Generalprobe 327" in _lies(WIRT / "test" / "graph-sichern.test.ts")
    assert "Generalprobe 327" in _lies(WIRT / "test" / "varianten.test.tsx")
