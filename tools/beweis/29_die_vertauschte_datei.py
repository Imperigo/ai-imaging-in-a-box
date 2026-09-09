#!/usr/bin/env python3
"""BEWEIS 29 — Dieselbe Datei, ein anderes Bauwerk: merkt es die Kette?

Die Behauptung, die hier fallen kann
------------------------------------
Der Zwischenspeicher ist der einzige Teil dieser Kette, der ein Bild **ausliefert, ohne
es gerechnet zu haben**. Damit hängt an ihm eine Frage, die kein Renderlauf beantwortet:
*Woran erkennt er, dass zwei Aufträge dieselben sind?*

Der bequeme Weg wäre der Dateipfad — er steht im Auftrag, kostet nichts und ist fast
immer richtig. **Fast immer.** Genau dann nicht, wenn jemand ein Modell austauscht und
den Dateinamen behält: `szene.glb` wird neu exportiert, der Pfad bleibt, der Inhalt ist
ein anderes Haus. Ein Speicher, der auf den Pfad hört, liefert dann in aller Ruhe das
**alte** Bild — und niemand sieht es dem Ergebnis an.

Das ist die fünfte Regel dieses Projekts in Reinform: *Ein Fehlschlag, der wie ein Erfolg
aussieht, wird nicht gefunden — er wird geglaubt.*

Vier Läufe, **immer derselbe Pfad und derselbe Dateiname**:

    1  Inhalt A (der Quader)            muss rechnen
    2  Inhalt B (das zweite Bauwerk)    muss rechnen  ← hier fiele ein Pfad-Speicher um
    3  Inhalt B, unverändert            darf NICHT rechnen
    4  Inhalt A, byteweise zurück       darf NICHT rechnen  ← und zwar der Eintrag von 1

Lauf 4 ist die Gegenrichtung und der eigentliche Beleg: Erkannt wird nicht «die Datei hat
sich geändert», sondern **welcher Inhalt dasteht**. Eine neu geschriebene Datei mit altem
Inhalt rechnet nicht neu.

Zwei Zeugen, und sie müssen sich einig sein
-------------------------------------------
Gezählt wird doppelt: was die Kette in ihrem eigenen Bericht **sagt**
(``urteil["zwischenspeicher"]["treffer"]``) und wie oft `seams.glb_zu_multipass`
**wirklich** gelaufen ist. Widersprechen sie sich, hält der Lauf an.
*Wer nur den Bericht liest, glaubt dem Erzähler.*

Was hier NICHT bewiesen wird
----------------------------
Dass ein Modelltausch **inhaltlich** auffällt — dass also jemand merkt, das Bild zeige
das falsche Haus. Bewiesen wird nur, dass die Kette **neu rechnet** statt ein altes Bild
durchzureichen. Das ist die Voraussetzung dafür und nicht dasselbe.

`render` und `qa` sind ersetzt: Sie brauchen torch und Gewichte, die hier nicht liegen.
Die Stufe, um die es geht, läuft echt — mit Blender.

Aufruf:
    python3 tools/beweis/29_die_vertauschte_datei.py [ziel_verzeichnis]
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import abholer, bildlesen, bildschreiben, graph, seams  # noqa: E402

import make_test_ifc  # noqa: E402

BREITE, HOEHE, SAMPLES = 320, 200, 4

GRUND = (243, 243, 241)
GERECHNET = (216, 122, 40)     # dieselbe Rolle und Farbe wie in Beweis 05 und 23
SPEICHER = (62, 106, 160)
LINIE = (60, 66, 74)
PFADFARBE = (150, 150, 150)    # was der blosse Pfad unterscheidet: nichts

#: Was jeder der vier Laeufe tun MUSS. Der Selbstcheck prueft genau das.
ERWARTET = (True, True, False, False)

#: Ab hier gilt der Tausch als im Bild angekommen (mittlerer Helligkeitsabstand).
TAUSCH_SICHTBAR_AB = 0.01


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _hashfarbe(hexwert: str) -> tuple[int, int, int]:
    """Die ersten drei Bytes eines Hashes als Farbe — nicht mehr und nicht weniger.

    Sie ist keine Messung, sondern eine Lesehilfe: Gleiche Farbe heisst gleicher Hash.
    Der Hash selbst steht im Dateinamen.
    """
    roh = bytes.fromhex(hexwert[:6])
    # aufgehellt, damit die Bloecke auf dem hellen Grund nicht als Loecher wirken
    return tuple(80 + (w * 140) // 255 for w in roh)


def _zwei_reihen(ziel: Path, laeufe: list[dict]) -> Path:
    """Oben, was der Pfad unterscheidet. Unten, was der Inhalt unterscheidet."""
    zelle, rand, luft = 96, 30, 46
    b = rand * 2 + zelle * len(laeufe)
    h = rand * 2 + zelle * 2 + luft
    bild = _leinwand(b, h)
    for i, lauf in enumerate(laeufe):
        x0 = rand + i * zelle
        _rechteck(bild, b, h, x0 + 6, rand + 6, x0 + zelle - 6, rand + zelle - 6,
                  PFADFARBE)
        y0 = rand + zelle + luft
        _rechteck(bild, b, h, x0 + 6, y0 + 6, x0 + zelle - 6, y0 + zelle - 6,
                  _hashfarbe(lauf["inhalt_sha"]))
        for k in range(i + 1):
            _rechteck(bild, b, h, x0 + 8 + k * 8, h - rand + 6,
                      x0 + 13 + k * 8, h - rand + 11, LINIE)
    p = ziel / ("04_pfad-sagt-viermal-dasselbe_inhalt-sagt-"
                + "-".join(l["marke"] for l in laeufe)
                + "_farbe-ist-der-inhalts-hash.png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _zeugen(ziel: Path, laeufe: list[dict]) -> Path:
    """Je Lauf zwei Blöcke: was der Bericht sagt, was der Blenderzähler sah."""
    zelle, rand, luft = 96, 30, 20
    b = rand * 2 + zelle * len(laeufe)
    h = rand * 2 + zelle * 2 + luft
    bild = _leinwand(b, h)
    for i, lauf in enumerate(laeufe):
        x0 = rand + i * zelle
        for reihe, wert in enumerate((lauf["bericht_gerechnet"], lauf["gezaehlt"])):
            y0 = rand + reihe * (zelle + luft)
            _rechteck(bild, b, h, x0 + 6, y0 + 6, x0 + zelle - 6, y0 + zelle - 6,
                      GERECHNET if wert else SPEICHER)
    p = ziel / ("05_zwei-zeugen_bericht-und-blenderzaehler_"
                + "-".join("rechnet" if l["gezaehlt"] else "speicher" for l in laeufe)
                + "_einig-ja.png")
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _attrappe(a, **kw):
    """Ersatz für `render.rendere` — er behauptet nichts, er streift."""
    p = Path(a.ausgabe_png)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 64
    bildschreiben.schreibe_graustufen_png(
        p, [1.0 if ((x // 4) + (y // 4)) % 2 else 0.0
            for y in range(n) for x in range(n)], n, n)
    return {"status": "ok", "bild_png": str(p)}


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis29-"))

    # Zwei WIRKLICH verschiedene Bauwerke: der Quader und der Hochbau (Stuetzenraster,
    # Kern, gegliederte Huelle). Nicht zwei Spielarten derselben Datei — es soll ein
    # anderes Haus sein, nicht eine andere Schreibweise desselben.
    bytes_von = {}
    for marke, hochbau in (("A", False), ("B", True)):
        ifc = arbeit / f"bau_{marke}.ifc"
        make_test_ifc.erzeuge_ifc(ifc, hochbau=hochbau)
        bericht = seams.ifc_zu_glb(ifc, arbeit / f"szene_{marke}.glb")
        if bericht.get("status") != "ok":
            print(f"IFC->glb {marke}: {bericht.get('error')}")
            return 1
        bytes_von[marke] = (arbeit / f"szene_{marke}.glb").read_bytes()
        print(f"  Bauwerk {marke}: {len(bytes_von[marke])} Byte, "
              f"sha256 {hashlib.sha256(bytes_von[marke]).hexdigest()[:12]}")

    # DER EINE PFAD, ueber alle vier Laeufe. Er ist der ganze Punkt dieses Beweises.
    modell = arbeit / "modell" / "szene.glb"
    modell.parent.mkdir(parents=True, exist_ok=True)

    gezaehlt: list[str] = []
    echt = seams.glb_zu_multipass

    def gezaehlter_multipass(glb_pfad, aus, **kw):
        gezaehlt.append(str(glb_pfad))
        return echt(glb_pfad, aus, **kw)

    cache = graph.ArtefaktCache(arbeit / "speicher")
    verarbeite = abholer.verarbeiter(
        out_wurzel=arbeit / "aus", auto_richtungen=("sSE",), up_axis="y",
        nullprobe=False, rahmung_pruefen=False, seeds=(0,), zwischenspeicher=cache,
        _multipass=gezaehlter_multipass,
        _rendere=_attrappe, _soll=lambda b: ([0.0, 1.0, 2.0, 3.0], 2, 2),
        _qa=lambda bild, soll, **kw: {"score": None, "bestanden": None,
                                      "grund": "kein Schaetzer in dieser Umgebung"})

    laeufe = []
    for nr, marke in enumerate(("A", "B", "B", "A"), 1):
        # Immer schreiben, auch wenn sich nichts aendert: Ein Speicher, der auf mtime
        # hoert, faellt genau hier — und er soll fallen, wenn er so gebaut waere.
        modell.write_bytes(bytes_von[marke])
        inhalt_sha = hashlib.sha256(modell.read_bytes()).hexdigest()
        vorher = len(gezaehlt)
        ergebnis = verarbeite({
            "modell": modell, "job_id": f"vis-{nr}-aaaaaa",
            "verzeichnis": arbeit / f"lauf{nr}", "hochachse": "y",
            "szene": {"kameras": "auto", "aufloesung": BREITE, "hoehe": HOEHE,
                      "samples": SAMPLES, "prompt": "ein Bauwerk am Hang"},
        })
        kameras = ergebnis.get("kameras") or []
        speicher = (kameras[0].get("zwischenspeicher") or {}) if kameras else {}
        laeufe.append({
            "nr": nr, "marke": marke, "inhalt_sha": inhalt_sha,
            "gezaehlt": len(gezaehlt) > vorher,
            "bericht_gerechnet": not speicher.get("treffer"),
            "schluessel": str(speicher.get("schluessel")),
            "bilder": ergebnis.get("bilder") or [],
        })
        print(f"  Lauf {nr}  Inhalt {marke}  sha {inhalt_sha[:12]}  "
              f"Bericht: {'gerechnet' if laeufe[-1]['bericht_gerechnet'] else 'Speicher':9s}  "
              f"Blenderzaehler: {'gerechnet' if laeufe[-1]['gezaehlt'] else 'Speicher'}")

    # ── Selbstcheck 1: die zwei Zeugen muessen sich einig sein ──
    for lauf in laeufe:
        if lauf["bericht_gerechnet"] != lauf["gezaehlt"]:
            print(f"\nDIE ZEUGEN WIDERSPRECHEN SICH in Lauf {lauf['nr']}: Der Bericht "
                  f"sagt {'gerechnet' if lauf['bericht_gerechnet'] else 'Speicher'}, "
                  f"gelaufen ist {'gerechnet' if lauf['gezaehlt'] else 'Speicher'}. "
                  f"Ein Bericht, der etwas anderes sagt als der Zaehler, ist die "
                  f"gefaehrlichere Haelfte — er wird gelesen.")
            return 1

    # ── Selbstcheck 2: die vier Erwartungen ──
    ist = tuple(l["gezaehlt"] for l in laeufe)
    if ist != ERWARTET:
        print(f"\nERWARTUNG GEBROCHEN: gerechnet {ist}, erwartet {ERWARTET}.")
        print("  Lauf 2 MUSS rechnen — der Dateiname blieb, der Inhalt wurde getauscht.")
        print("  Lauf 4 darf NICHT rechnen — der alte Inhalt steht wieder da.")
        return 1

    # ── Selbstcheck 3: der Schluessel haengt am Inhalt, nicht am Pfad ──
    s = [l["schluessel"] for l in laeufe]
    if not (s[0] == s[3] and s[1] == s[2] and s[0] != s[1]):
        print(f"\nDIE SCHLUESSEL PASSEN NICHT ZUM INHALT: {[k[:10] for k in s]}. "
              f"Erwartet: 1 und 4 gleich (Inhalt A), 2 und 3 gleich (Inhalt B), "
              f"1 gegen 2 verschieden.")
        return 1
    print(f"  Schluessel: 1={s[0][:10]}  2={s[1][:10]}  3={s[2][:10]}  4={s[3][:10]}")

    # ── Die Bilder der beiden gerechneten Laeufe ──
    karten = []
    for lauf in laeufe[:2]:
        ordner = sorted((arbeit / "aus").glob(f"*{lauf['nr']}*/sSE/beauty_.png"))
        beauty = ordner[0] if ordner else None
        if beauty is None or not beauty.is_file():
            print(f"\nKEIN BEAUTY-BILD fuer Lauf {lauf['nr']}.")
            return 1
        werte, b, h = bildlesen.lies_png_luminanz(beauty)
        karten.append({"werte": werte, "breite": b, "hoehe": h})
        neu = ziel / (f"0{lauf['nr']}_lauf{lauf['nr']}_szene.glb_inhalt-{lauf['marke']}"
                      f"_sha-{lauf['inhalt_sha'][:8]}_gerechnet_beauty.png")
        neu.write_bytes(beauty.read_bytes())
        print("  Blender: ", neu.name)

    if karten[0]["breite"] != karten[1]["breite"] or karten[0]["hoehe"] != karten[1]["hoehe"]:
        print("\nDIE BEIDEN RENDERS HABEN VERSCHIEDENE GROESSEN — nicht vergleichbar.")
        return 1

    roh = [abs(x - y) for x, y in zip(karten[0]["werte"], karten[1]["werte"])]
    mittel = sum(roh) / len(roh)
    if mittel < TAUSCH_SICHTBAR_AB:
        print(f"\nDER TAUSCH IST IM BILD NICHT ZU SEHEN: mittlerer Unterschied "
              f"{mittel:.5f}, verlangt sind {TAUSCH_SICHTBAR_AB}. Dann belegt dieser "
              f"Beweis nur, dass neu gerechnet wurde — nicht, dass es noetig war.")
        return 1
    hoechst = max(roh) or 1.0
    dif = ziel / (f"03_differenzbild_lauf1-gegen-lauf2_mittel-{mittel:.5f}"
                  f"_schwelle-{TAUSCH_SICHTBAR_AB}_der-tausch-kommt-im-bild-an.png")
    bildschreiben.schreibe_graustufen_png(dif, [w / hoechst for w in roh],
                                          karten[0]["breite"], karten[0]["hoehe"])
    print("  Differenz:", dif.name)
    print("  Reihen:   ", _zwei_reihen(ziel, laeufe).name)
    print("  Zeugen:   ", _zeugen(ziel, laeufe).name)

    print(f"\nVIERMAL DERSELBE PFAD {modell.name}, zweimal gerechnet, zweimal aus dem "
          f"Speicher — und die Zuordnung folgt dem INHALT: A B B A.")
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
