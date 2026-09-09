#!/usr/bin/env python3
"""BEWEIS 27 — Der Prompt verrät sich selbst: Wer Bauteile bestellt, lädt das Modell ein,
Geometrie zu erfinden — und der Wächter meldet es **vor** dem Renderlauf.

Warum das zur Kernfrage der Arbeit gehört
-----------------------------------------
Die Arbeit prüft, ob ein erzeugtes Bild zu der Geometrie passt, aus der es entstand. Der
häufigste Weg, dieses Passen zu zerstören, kostet keine Sekunde Rechenzeit: **Man
schreibt ein Bauteil in den Prompt, das im Modell nicht steht.** Das Bildmodell tut dann
genau, worum es gebeten wurde — und das Ergebnis ist ein plausibles Haus, nur nicht
*dieses*.

*Der Fehler ist danach unsichtbar:* Ein erfundenes Dach sieht aus wie ein Dach. Der Lauf
schlägt nicht fehl, die Geometrie-QA meldet nur eine schlechte Zahl, und niemand käme auf
den Prompt.

Was hier gemessen wird
----------------------
Sechs Prompts durch `prompts.bauteilwaechter` und `prompts.komponiere` — echte Aufrufe,
kein Nachbau. Drei sind harmlos, drei nennen Bauteile. Dazu der **deutsche** Fall: Der
Wächter prüft beide Fassungen, das Original und die Übersetzung, weil ein deutsches
«Dach» erst als «roof» sicher gefunden wird — *und weil sonst genau die Wörter
durchrutschten, die die Übersetzung selbst erzeugt hat.*

Woran man es im Bild sieht
--------------------------
* ``01_ampel_...png`` — je Prompt ein Feld: **grün** kein Bauteilwort, **rot** mit. Die
  Länge des Balkens daneben ist die Zahl der Fundstellen.
* ``02_fundstellen_...png`` — je Prompt die gefundenen Wörter als Blöcke, in der
  Reihenfolge des Textes.
* ``03_deutsch_...png`` — der deutsche Prompt: links, was im **Original** gefunden wird,
  rechts, was erst nach der **Übersetzung** auffällt. Wo rechts mehr steht als links,
  hätte eine Prüfung nur am Original das Wort verfehlt.

Der Selbstcheck
---------------
Er hält an, wenn ein harmloser Prompt anschlägt **oder** ein Bauteil-Prompt nicht. Beides
wäre ein Wächter, der nicht das misst, was draufsteht.

Was hier NICHT behauptet wird
-----------------------------
Dass der Wächter Bedeutung versteht. Er kennt **Wörter**. «a wall of fog» schlägt an,
obwohl keine Wand gemeint ist. *Ein Fehlalarm kostet einen Blick, ein übersehener Fund ein
Bild* — die Richtung ist gewollt und steht so im Modul.

Aufruf:
    python3 tools/beweis/27_der_prompt_verrat_sich.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, prompts, sprache  # noqa: E402

#: Drei harmlose, drei mit Bauteilen. Die Erwartung steht **vor** der Messung.
FAELLE = (
    ("harmlos-1", "a calm architectural photograph, overcast light", False),
    ("harmlos-2", "morning atmosphere, quiet, no people", False),
    ("harmlos-3", "eine ruhige Aufnahme bei bedecktem Himmel", False),
    ("bauteil-1", "a house with a large roof and many windows", True),
    ("bauteil-2", "add a balcony and a staircase to the entrance", True),
    ("bauteil-3", "ein Gebaeude mit Dach, Fenstern und einem Balkon", True),
)
#: Der deutsche Fall, an dem die zweite Prüfung hängt.
DEUTSCH = "ein Gebaeude mit Dach, Fenstern und einem Balkon"

GRUND = (243, 243, 241)
OK = (62, 140, 78)
FUND = (200, 60, 48)
LINKS = (62, 106, 160)
RECHTS = (216, 122, 40)


def _leinwand(b, h, farbe=GRUND):
    return [list(farbe) for _ in range(b * h)]


def _rechteck(bild, b, h, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(b, x1)):
            bild[y * b + x] = list(farbe)


def _ampel(ziel: Path, zeilen: list[tuple[str, bool, int]], name: str) -> Path:
    zeile, b = 34, 520
    h = 20 + zeile * len(zeilen)
    bild = _leinwand(b, h)
    hoechst = max(n for _, _, n in zeilen) or 1
    for i, (_, gefunden, n) in enumerate(zeilen):
        y0 = 10 + i * zeile
        farbe = FUND if gefunden else OK
        _rechteck(bild, b, h, 20, y0, 20 + 26, y0 + 26, farbe)      # das Feld
        if n:
            _rechteck(bild, b, h, 56, y0 + 6, 56 + round((b - 90) * n / hoechst),
                      y0 + 20, farbe)                                # der Balken
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _bloecke(ziel: Path, zeilen: list[tuple[str, list]], name: str) -> Path:
    """Je Prompt die Fundstellen als Blöcke — Breite nach Wortlänge."""
    zeile, b = 30, 560
    h = 20 + zeile * len(zeilen)
    bild = _leinwand(b, h)
    for i, (_, woerter) in enumerate(zeilen):
        x = 20
        y0 = 12 + i * zeile
        for wort in woerter:
            breite = 8 + 7 * len(wort)
            _rechteck(bild, b, h, x, y0, min(b - 10, x + breite), y0 + 18, FUND)
            x += breite + 6
            if x > b - 40:
                break
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def _zwei_seiten(ziel: Path, links: list, rechts: list, name: str) -> Path:
    """Original gegen Übersetzung — wo rechts mehr steht, hätte eine Seite gereicht."""
    b, h = 560, 130
    bild = _leinwand(b, h)
    for spalte, (woerter, farbe) in enumerate(((links, LINKS), (rechts, RECHTS))):
        x0 = 20 + spalte * 275
        for i, wort in enumerate(woerter):
            y0 = 20 + i * 26
            _rechteck(bild, b, h, x0, y0, x0 + min(250, 8 + 9 * len(wort)), y0 + 18,
                      farbe)
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)

    ampel: list[tuple[str, bool, int]] = []
    bloecke: list[tuple[str, list]] = []
    for name, text, erwartet in FAELLE:
        befund = prompts.bauteilwaechter(text)
        woerter = list(befund["woerter"])
        ampel.append((name, befund["gefunden"], len(woerter)))
        bloecke.append((name, woerter))
        print(f"  {name:10s} gefunden={str(befund['gefunden']):5s} "
              f"({len(woerter)}) {woerter}")
        if befund["gefunden"] != erwartet:
            print(f"\nDER WAECHTER MISST NICHT, WAS DRAUFSTEHT: {name} ergab "
                  f"{befund['gefunden']}, erwartet war {erwartet}. Prompt: {text!r}")
            return 1

    print("  Ampel:     ", _ampel(
        ziel, ampel,
        "01_ampel_" + "_".join(
            f"{n}-{'fund' if g else 'frei'}" for n, g, _ in ampel) + ".png").name)
    print("  Fundstellen:", _bloecke(
        ziel, bloecke,
        "02_fundstellen_" + "_".join(f"{n}-{len(w)}" for n, w in bloecke) + ".png").name)

    # ── Der deutsche Fall: beide Fassungen werden geprüft ──
    sprachbefund = sprache.uebersetze(DEUTSCH)
    im_original = list(prompts.bauteilwaechter(sprachbefund["original"])["woerter"])
    im_uebersetzten = list(prompts.bauteilwaechter(sprachbefund["uebersetzt"])["woerter"])
    nur_nach_uebersetzung = [w for w in im_uebersetzten
                             if w.lower() not in {x.lower() for x in im_original}]
    print(f"\n  deutsch, Original:    {im_original}")
    print(f"  deutsch, uebersetzt:  {im_uebersetzten}")
    print(f"  erst nach Uebersetzung gefunden: {nur_nach_uebersetzung or 'keines'}")

    p = _zwei_seiten(
        ziel, im_original, im_uebersetzten,
        f"03_deutsch_original-{len(im_original)}_uebersetzt-{len(im_uebersetzten)}"
        f"_nur-nach-uebersetzung-{len(nur_nach_uebersetzung)}"
        f"_verfahren-{sprachbefund['verfahren']}.png")
    print("  Zwei Seiten:", p.name)

    # Und die Gegenprobe an der Naht: `komponiere` reicht den Hinweis heraus.
    fertig = prompts.komponiere(freitext=DEUTSCH)
    traegt = [h for h in fertig["hinweise"] if "auteil" in h or "Bauteil" in h]
    print(f"\n  komponiere() meldet den Bauteilfund: {bool(traegt)}")
    if not traegt:
        print("DER HINWEIS ERREICHT DEN FERTIGEN PROMPT NICHT — er stuende nur im "
              "Waechter, und niemand liest den Waechter.")
        return 1
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
