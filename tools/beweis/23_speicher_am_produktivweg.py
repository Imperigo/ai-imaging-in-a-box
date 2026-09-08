#!/usr/bin/env python3
"""BEWEIS 23 — Der Zwischenspeicher **am Produktivweg**, mit echtem Blender.

Die Behauptung, die hier fallen kann
------------------------------------
`docs/PLAN.md` führt seit Wochen den Posten «die Kette als Graph läuft **nicht** am
Produktivweg — der Abholer fährt die Stufen als gerade Abfolge». Das stimmt und ist
zugleich missverständlich, denn es legt nahe, der **Nutzen** des Graphen fehle dort auch.

Beweis 05 zeigt den Nutzen am Graphen: Ändert man nur den Prompt, kommen `geometrie` und
`multipass` aus dem Speicher. Dieses Skript stellt **dieselbe** Frage an `abholer.
verarbeiter` — also an den Weg, den ein Auftrag aus KosmoOrbit wirklich nimmt — und zählt
dabei die **echten Blender-Läufe**.

Vier Läufe, dieselbe Frage wie in Beweis 05:

    1  Prompt A, Geometrie A      muss rechnen
    2  nur der Prompt geändert    darf NICHT rechnen
    3  unverändert                darf NICHT rechnen
    4  Geometrie geändert         muss rechnen

**Der Selbstcheck hält den Lauf an, wenn eine dieser vier Erwartungen bricht.** Ein
Beweisbild, das eine Behauptung zeigt, die gerade nicht gilt, ist schlimmer als keines.

Was hier NICHT bewiesen wird
----------------------------
Dass der Abholer den **Graphen** benutzt. Er tut es nicht, und dieses Skript ändert daran
nichts. Bewiesen wird nur, dass die teure Stufe am Produktivweg denselben Speicher hat —
*was «gebaut, aber nicht im Betrieb» von «der Nutzen fehlt» trennt.*

`render` und `qa` sind ersetzt: Sie brauchen torch und Gewichte, die hier nicht liegen.
Gezählt wird die Stufe, um die es geht, und die läuft echt.

Aufruf:
    python3 tools/beweis/23_speicher_am_produktivweg.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import abholer, bildschreiben, graph, seams  # noqa: E402

import make_test_ifc  # noqa: E402

BREITE, HOEHE, SAMPLES = 320, 200, 4

GRUND = (243, 243, 241)
GERECHNET = (216, 122, 40)     # dieselbe Rolle und Farbe wie in Beweis 05
SPEICHER = (62, 106, 160)
LINIE = (60, 66, 74)

#: Was jeder der vier Läufe tun MUSS. Der Selbstcheck prüft genau das.
ERWARTET = (True, False, False, True)


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _matrix(ziel: Path, laeufe: list[dict]) -> Path:
    """Läufe (Zeilen) gegen Blender-Aufrufe — orange gerechnet, blau aus dem Speicher."""
    zelle, rand = 96, 30
    b, h = rand * 2 + zelle, rand * 2 + zelle * len(laeufe)
    bild = _leinwand(b, h)
    for i, lauf in enumerate(laeufe):
        y0 = rand + i * zelle
        farbe = GERECHNET if lauf["gerechnet"] else SPEICHER
        _rechteck(bild, b, h, rand + 6, y0 + 6, rand + zelle - 6, y0 + zelle - 6, farbe)
        # Die Laufnummer als Punktreihe links — dieselbe Handschrift wie Beweis 05.
        for k in range(i + 1):
            _rechteck(bild, b, h, 8 + k * 6, y0 + zelle // 2 - 2,
                      12 + k * 6, y0 + zelle // 2 + 2, LINIE)
    p = ziel / ("03_matrix_laeufe-gegen-blender_"
                + "-".join("gerechnet" if l["gerechnet"] else "speicher" for l in laeufe)
                + ".png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _zeitbalken(ziel: Path, laeufe: list[dict]) -> Path:
    """Was der Speicher an Wanduhrzeit spart — gemessen, nicht geschätzt."""
    b, h = 560, 56 * len(laeufe) + 32
    bild = _leinwand(b, h)
    hoechst = max(l["dauer_s"] for l in laeufe) or 1.0
    for i, lauf in enumerate(laeufe):
        y0 = 16 + i * 56
        laenge = max(2, round((b - 60) * lauf["dauer_s"] / hoechst))
        farbe = GERECHNET if lauf["gerechnet"] else SPEICHER
        _rechteck(bild, b, h, 30, y0, 30 + laenge, y0 + 36, farbe)
    p = ziel / ("04_dauer-je-lauf_" + "_".join(f"{l['dauer_s']:.2f}s" for l in laeufe)
                + ".png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis23-"))

    # Zwei Geometrien: A ohne Gelände, B mit — derselbe Bau, andere glb, anderer Inhalt.
    glb = {}
    for name, gelaende in (("A", False), ("B", True)):
        ifc = arbeit / f"bau_{name}.ifc"
        make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=gelaende)
        bericht = seams.ifc_zu_glb(ifc, arbeit / f"szene_{name}.glb")
        if bericht.get("status") != "ok":
            print(f"IFC→glb {name}: {bericht.get('error')}")
            return 1
        glb[name] = arbeit / f"szene_{name}.glb"

    zaehler: list = []
    echt = seams.glb_zu_multipass

    def gezaehlter_multipass(glb_pfad, aus, **kw):
        zaehler.append(str(glb_pfad))
        return echt(glb_pfad, aus, **kw)

    cache = graph.ArtefaktCache(arbeit / "speicher")
    verarbeite = abholer.verarbeiter(
        out_wurzel=arbeit / "aus", auto_richtungen=("sSE",), up_axis="y",
        nullprobe=False, rahmung_pruefen=False, seeds=(0,), zwischenspeicher=cache,
        _multipass=gezaehlter_multipass,
        _rendere=_attrappe, _soll=lambda b: ([0.0, 1.0, 2.0, 3.0], 2, 2),
        _qa=lambda bild, soll, **kw: {"score": None, "bestanden": None,
                                      "grund": "kein Schaetzer in dieser Umgebung"})

    bestellungen = [
        ("A", "ein Wohnhaus am Hang"),
        ("A", "ein Buerobau bei Abendlicht"),   # NUR der Prompt
        ("A", "ein Buerobau bei Abendlicht"),   # gar nichts
        ("B", "ein Buerobau bei Abendlicht"),   # NUR die Geometrie
    ]
    laeufe = []
    for nr, (welche, prompt) in enumerate(bestellungen, 1):
        vorher = len(zaehler)
        beginn = time.monotonic()
        verarbeite({
            "modell": glb[welche], "job_id": f"vis-{nr}-aaaaaa",
            "verzeichnis": arbeit / f"lauf{nr}", "hochachse": "y",
            "szene": {"kameras": "auto", "aufloesung": BREITE, "hoehe": HOEHE,
                      "samples": SAMPLES, "prompt": prompt},
        })
        dauer = time.monotonic() - beginn
        gerechnet = len(zaehler) > vorher
        laeufe.append({"nr": nr, "gerechnet": gerechnet, "dauer_s": round(dauer, 2),
                       "geometrie": welche, "prompt": prompt})
        print(f"  Lauf {nr}  Geometrie {welche}  "
              f"{'GERECHNET' if gerechnet else 'aus dem Speicher':17s} {dauer:6.2f} s")

    # ── Der Selbstcheck. Er haelt an, statt ein irrefuehrendes Bild zu schreiben. ──
    ist = tuple(l["gerechnet"] for l in laeufe)
    if ist != ERWARTET:
        print(f"\nERWARTUNG GEBROCHEN: gerechnet {ist}, erwartet {ERWARTET}.")
        print("  Lauf 2 und 3 duerfen NICHT rechnen (nur der Prompt aendert sich),")
        print("  Lauf 1 und 4 muessen rechnen (erste Geometrie, dann eine andere).")
        return 1

    # ── Die Bilder ──
    for i, welche in ((1, "A"), (4, "B")):
        quelle = next((arbeit / "aus").rglob("beauty_.png"), None)
        ordner = sorted((arbeit / "aus").glob(f"*{i}*/sSE/beauty_.png"))
        pfad = ordner[0] if ordner else quelle
        if pfad and pfad.is_file():
            neu = ziel / (f"0{1 if i == 1 else 2}_lauf{i}_geometrie-{welche}"
                          f"_{'ohne' if welche == 'A' else 'mit'}-gelaende_beauty.png")
            neu.write_bytes(pfad.read_bytes())
            print("  Blender:", neu.name)

    print("  Matrix: ", _matrix(ziel, laeufe).name)
    print("  Dauer:  ", _zeitbalken(ziel, laeufe).name)

    gespart = sum(l["dauer_s"] for l in laeufe if not l["gerechnet"])
    gerechnet_s = sum(l["dauer_s"] for l in laeufe if l["gerechnet"])
    print(f"\nGERECHNET {gerechnet_s:.2f} s in 2 Laeufen, "
          f"AUS DEM SPEICHER {gespart:.2f} s in 2 Laeufen.")
    return 0 if sorted(ziel.glob("*.png")) else 1


def _attrappe(a, **kw):
    """Ersatz für `render.rendere` — er behauptet nichts, er streift.

    Ein Ersatz, der wie ein Ergebnis aussieht, ist in diesem Projekt schon zweimal als
    eines gelesen worden.
    """
    p = Path(a.ausgabe_png)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 64
    bildschreiben.schreibe_graustufen_png(
        p, [1.0 if ((x // 4) + (y // 4)) % 2 else 0.0
            for y in range(n) for x in range(n)], n, n)
    return {"status": "ok", "bild_png": str(p)}


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
