#!/usr/bin/env python3
"""BEWEIS 16 — Ohne Nullprobe gibt es keine Einordnung: Auf einer synthetischen
Bodenszene erreichen weisses Rauschen, eine leere Graufläche und ein strukturloser
Verlauf reale, hier gemessene ``geometrie_qa``-Scores gegen dieselbe Soll-Karte, und
die Schwelle 0.65 steht als Linie daneben.

Der belegte Befund, um den es geht (``geometrie_qa.NULLANKER['platte_endlich']``,
gemessen `auf-20260820-21` MIT ``tiefenschaetzer.qa_gegen_soll`` auf der HomeStation):
Auf einer Blender-Szene mit 59,8 % Bodenanteil erreichte **weisses Rauschen 0.7217**
und bestand damit das Gate von 0.65 — mehr als jeder der fünf echten Läufe derselben
Messung. Der Grund liegt nicht am Rauschen, sondern am Schätzer: Ein monokularer
Tiefenschätzer legt in JEDES Bild eine zum Horizont laufende Bodenebene, und eine Szene
mit viel Boden IST im Wesentlichen so eine Rampe — die Rangkorrelation vergleicht dann
zwei Bodenrampen, nicht das Bauwerk.

Was hier neu gemessen wird, und was dabei am Gerät hängt
----------------------------------------------------------
Dieses Skript baut eine EIGENE synthetische Bodenszene (60,2 % Geometrieanteil, Boden
plus ein aufsitzendes Gebäude — Konstruktion unten, keine Blender-Datei, keine echten
Projektdaten) und versucht DENSELBEN Weg wie am 20.08.2026: Kontrollbild schreiben,
``tiefenschaetzer.qa_gegen_soll`` darüberlaufen lassen, ``geometrie_gate`` urteilen
lassen. Dieser Versuch braucht ``torch`` und Gewichte (``depth-anything-v2-small``) —
hier nicht vorhanden — und schlägt sauber mit ``status='fehler'`` fehl
(``tiefenschaetzer.schaetze_tiefe`` fängt genau diesen Fall ab und wirft nicht). Das
Skript meldet das im Dateinamen und im Text, statt die Zahl von 0.7217 abzuschreiben
oder zu erfinden.

Was OHNE Gerät läuft, und was es beweist
------------------------------------------
Parallel dazu — und das ist die Messung, die tatsächlich in diesem Lauf entsteht — wird
derselbe Gate-Aufruf mit den KONTROLLBILD-Grauwerten (``bildschreiben.kontrollwerte``,
0..1) DIREKT als Ist-Tiefenkarte gemessen, ohne Schätzer dazwischen. Das ist eine andere
Messung als die vom 20.08.2026, keine Wiederholung — und der Unterschied trägt die
eigentliche Aussage:

* ``geom_iou`` hängt an dieser Stelle NUR am Bodenanteil der Szene: Ein Kontrollbild hat
  keine eigene Hintergrundmarke (alle Werte liegen weit unter der 1e6-Schranke), seine
  Silhouette ist also das GANZE Bild. Damit ist ``geom_iou = n_soll / n_bild`` — hier
  gemessen, nicht angenommen — unabhängig vom Bildinhalt. Das ist derselbe Mechanismus,
  den ``geometrie_qa`` als «Der Geometrieanteil sagt den Deckel fast allein» dokumentiert
  (Zeile ~1035), hier ohne Schätzer reproduziert.
* Die Rangkorrelation dagegen braucht eine echte Ordnung im Ist. Ohne Schätzer trägt kein
  Kontrollbild eine Bodenrampe — weisses Rauschen bleibt Rauschen, der Verlauf bleibt
  quer zur Tiefe (``bildschreiben.kontrollwerte``: «Der Verlauf soll gerade NICHT wie
  eine Bodenebene aussehen»), und die Graufläche ist konstant und damit gar nicht
  korrelierbar (``geometrie_qa.spearman`` verweigert eine Rangkorrelation über einer
  konstanten Folge — das Ergebnis ist ``score=None``, NICHT MESSBAR, nicht 0).

Die Trennung dieser beiden Anteile ist die eigentliche Aussage dieses Beweises: Der
Bodenanteil allein bringt hier keinen Score über die Schwelle — dafür fehlt die
gerichtete Ordnung, die erst der Schätzer einträgt. Auf der synthetischen Bodenszene
fällt darum jedes der drei Kontrollbilder unter 0.65, während dieselbe Szene mit dem
echten Schätzer (Gerät) am 20.08.2026 weisses Rauschen bestehen liess. Das Gerät ist
also nicht Beiwerk dieser Messung, sondern ihr Unterschied.

Woran man es im Bild sieht
---------------------------
``01``…``04`` — die vier Karten nebeneinander, je 256×256, ``nah = hell`` (Konvention
``bildschreiben.KONVENTION``): das perfekte Bild (Soll = Ist, Score 1.000), weisses
Rauschen, die Graufläche, der Verlauf. Unter jeder Karte ein Streifen mit dem
Gate-Urteil: Grün = bestanden, Rot = durchgefallen, Dunkelblaugrau = nicht messbar.
``geometrie_gate`` selbst kennt nur ein BOOL'sches ``bestanden`` (fail-closed: auch
``score=None`` ergibt dort schon ``False``) — die dritte Farbe wertet darum ``score``
direkt aus, nicht ``bestanden``. Sie trifft hier genau die Graufläche: keinen Fehlschlag,
sondern eine Rangkorrelation, die es für eine konstante Folge nicht gibt
(``geometrie_qa.spearman`` verweigert sie ausdrücklich).

``05_balken_…png`` — vier Gruppen (perfekt / rauschen / grau / verlauf), je drei Balken:
``|spearman|`` (Blau), ``geom_iou`` (Orange), ``score`` (Dunkelgrau) — alle in diesem
Lauf gemessen. Die rote Linie ist ``SCHWELLE_GEOMETRIE`` (0.65), die Konstante des
Gates und keine Messung. Unter jeder Gruppe dasselbe Urteilsquadrat wie oben. Bei
``grau`` fehlen die Balken für ``spearman`` und ``score`` — das Feld ist ``None``,
nicht 0, und ein leerer Balken behauptet keinen Wert, den es nicht gibt.

Regel 3 (keine echten Projektdaten): Boden und Gebäude sind reine Arithmetik dieses
Skripts, reproduzierbar, ohne Blender und ohne IFC.

Aufruf:
    python3 tools/beweis/16_qa_nullanker.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/16_qa_nullanker/``. Rückgabe 1, wenn die
Nullprobe «perfekt» hier nicht 1.000 ergibt — das wäre ein Bug in der Szene dieses
Skripts, kein Befund über die Metrik.
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, geometrie_qa, tiefenschaetzer  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "16_qa_nullanker"

# ── Die synthetische Bodenszene ─────────────────────────────────────────────────────
#
# 256×256 — dieselbe Kantenlänge, die ``bildschreiben`` in seinem eigenen Docstring als
# Referenzgrösse nennt (65 536 Bildpunkte). Kein Bezug zu einer echten Aufnahme.
BREITE = 256
HOEHE = 256

#: Horizontzeile: darüber Himmel (Hintergrund), darunter Boden. 40 % der Höhe ergibt
#: 60,2 % Bodenanteil — in derselben Grössenordnung wie die 59,8 % der historischen
#: Messung, aber eine EIGENE Zahl dieser Szene, kein Nachbau jener.
HORIZONT_ZEILE = round(HOEHE * 0.40)

NAH_M = 4.0            # Bodentiefe an der Unterkante (am nächsten zur Kamera)
FERN_M = 60.0           # Bodentiefe am Horizont (am weitesten)

#: Ein Gebäude auf dem Boden — sonst wäre die Szene nur eine Rampe, und «Bodenszene»
#: hiesse dann streng genommen «leere Bodenplatte». Lage und Grösse sind willkürlich
#: gewählt, aber fest: ein Baukörper in der Bildmitte, deutlich näher als der Boden
#: hinter ihm an derselben Zeile.
GEBAEUDE_X0, GEBAEUDE_X1 = 90, 166
GEBAEUDE_Y0, GEBAEUDE_Y1 = 118, 196
GEBAEUDE_FAKTOR = 0.45  # Gebäudetiefe = Faktor × Bodentiefe derselben Zeile

#: Himmelsmarke — derselbe Wert, den Cycles als "kein Treffer" schreibt
#: (``bildschreiben.HINTERGRUND_AB_M`` ist 1e7, ``geometrie_qa.HINTERGRUND_SCHWELLE_M``
#: 1e6; 1e10 liegt über beiden, die Klassifikation ist darum in beiden Modulen gleich).
HIMMEL_M = 1.0e10

FARBE_BESTANDEN = (60, 150, 70)
FARBE_DURCHGEFALLEN = (190, 60, 50)
FARBE_NICHT_MESSBAR = (70, 90, 120)
FARBE_LEINWAND = (245, 245, 245)
FARBE_ACHSE = (120, 120, 120)
FARBE_SPEARMAN = (50, 110, 210)   # Blau
FARBE_IOU = (230, 120, 40)        # Orange
FARBE_SCORE = (60, 60, 60)        # Dunkelgrau
FARBE_SCHWELLE = (190, 60, 50)

FUGE = 10
STREIFEN = 14


def floor_tiefe_m(y: int) -> float:
    """Bodentiefe in Zeile ``y`` — linear von ``FERN_M`` am Horizont zu ``NAH_M`` unten."""
    t = (y - HORIZONT_ZEILE) / (HOEHE - 1 - HORIZONT_ZEILE)
    return FERN_M - t * (FERN_M - NAH_M)


def baue_bodenszene() -> list[float]:
    """Soll-Tiefenkarte in Metern: Himmel, eine Bodenplatte bis zum Horizont, ein
    aufsitzendes Gebäude. Zeilenweise von oben, wie jede Karte in diesem Projekt."""
    karte = [HIMMEL_M] * (BREITE * HOEHE)
    for y in range(HORIZONT_ZEILE, HOEHE):
        boden = floor_tiefe_m(y)
        im_gebaeude_zeile = GEBAEUDE_Y0 <= y < GEBAEUDE_Y1
        for x in range(BREITE):
            if im_gebaeude_zeile and GEBAEUDE_X0 <= x < GEBAEUDE_X1:
                karte[y * BREITE + x] = boden * GEBAEUDE_FAKTOR
            else:
                karte[y * BREITE + x] = boden
    return karte


# ── Kacheln: Tiefenkarte → Grauwerte, nah = hell ────────────────────────────────────

def kachel_perfekt(karte: list[float]) -> list[tuple[int, int, int]]:
    grau, _ = bildschreiben.normalisiere_tiefe(karte)
    return [(int(round(g * 255)),) * 3 for g in grau]


def kachel_kontrolle(werte: list[float]) -> list[tuple[int, int, int]]:
    """Rohe Kontrollwerte (0..1) direkt als Grauwert — dasselbe Bild, das der Schätzer
    bekäme, keine erneute Normalisierung."""
    return [(int(round(max(0.0, min(1.0, v)) * 255)),) * 3 for v in werte]


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe


def urteil_farbe(urteil: dict) -> tuple[int, int, int]:
    """``geometrie_gate`` liefert ``bestanden`` fail-closed als BOOL — ``score=None``
    ergibt dort bereits ``bestanden=False`` (anders als im Doppel-Gate ``aiimaging.gate``,
    das ein drittes ``None`` für «nicht beurteilbar» kennt). Der Unterschied zwischen
    «durchgefallen» und «gar nicht gemessen» steht hier also am ``score``, nicht am
    ``bestanden``-Feld: Nur ``score is None`` bekommt die eigene Farbe."""
    if urteil["score"] is None:
        return FARBE_NICHT_MESSBAR
    return FARBE_BESTANDEN if urteil["bestanden"] else FARBE_DURCHGEFALLEN


def tafel_mit_streifen(kachel, urteil: dict) -> tuple[list, int, int]:
    hoehe = HOEHE + FUGE + STREIFEN
    px = [FARBE_LEINWAND] * (BREITE * hoehe)
    for y in range(HOEHE):
        px[y * BREITE:(y + 1) * BREITE] = kachel[y * BREITE:(y + 1) * BREITE]
    farbe = urteil_farbe(urteil)
    for y in range(HOEHE + FUGE, hoehe):
        px[y * BREITE:(y + 1) * BREITE] = [farbe] * BREITE
    return px, BREITE, hoehe


# ── Balkenbild ───────────────────────────────────────────────────────────────────────

def zeichne_balken(ergebnisse: list[dict], *, breite: int = 760, hoehe: int = 360,
                   rand: int = 44, schwelle: float = geometrie_qa.SCHWELLE_GEOMETRIE):
    """Drei Balken je Gruppe (``|spearman|``, ``geom_iou``, ``score``), fehlende Werte
    (``None``) bleiben aus — ein leerer Balken behauptet nichts."""
    px = [FARBE_LEINWAND] * (breite * hoehe)
    plot_oben, plot_unten = rand, hoehe - rand - 26

    def y_von(v: float) -> float:
        return plot_unten - v * (plot_unten - plot_oben)

    _rechteck(px, breite, hoehe, rand, y_von(0.0), breite - rand, y_von(0.0) + 1, FARBE_ACHSE)
    _rechteck(px, breite, hoehe, rand, y_von(1.0), breite - rand, y_von(1.0) + 1, FARBE_ACHSE)
    _rechteck(px, breite, hoehe, rand, y_von(schwelle), breite - rand, y_von(schwelle) + 1,
              FARBE_SCHWELLE)

    n = len(ergebnisse)
    gruppen_breite = (breite - 2 * rand) / n
    masse = (("spearman_abs", FARBE_SPEARMAN), ("geom_iou", FARBE_IOU), ("score", FARBE_SCORE))
    balken_breite = gruppen_breite / (len(masse) + 1.5)

    for g, e in enumerate(ergebnisse):
        x_start = rand + g * gruppen_breite + balken_breite * 0.75
        for m, (feld, farbe) in enumerate(masse):
            v = e.get(feld)
            if v is None:
                continue
            x0 = x_start + m * balken_breite
            _rechteck(px, breite, hoehe, x0 + 2, y_von(v), x0 + balken_breite - 2,
                      y_von(0.0), farbe)
        mitte = rand + (g + 0.5) * gruppen_breite
        _rechteck(px, breite, hoehe, mitte - 9, plot_unten + 8, mitte + 9, plot_unten + 26,
                  urteil_farbe(e))
    return px, breite, hoehe


def _z(x) -> str:
    return "None" if x is None else f"{x:.4f}"


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, breite, hoehe) -> None:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
        geschrieben.append(pfad)

    soll = baue_bodenszene()
    n_boden = sum(1 for w in soll if w < geometrie_qa.HINTERGRUND_SCHWELLE_M)
    bodenanteil = n_boden / len(soll)

    # ── Der Versuch am Gerät — DAS ist der Teil, der ``torch`` und Gewichte braucht ──
    kontroll_pngs: dict[str, Path] = {}
    for art in bildschreiben.KONTROLLARTEN:
        pfad = ziel / f"_kontrollbild_{art}.png"
        bildschreiben.schreibe_kontrollbild(pfad, art, BREITE, HOEHE)
        kontroll_pngs[art] = pfad

    geraet_status: dict[str, str] = {}
    for art, pfad in kontroll_pngs.items():
        antwort = tiefenschaetzer.qa_gegen_soll(pfad, soll)
        geraet_status[art] = (
            f"{antwort['status']}"
            + (f" ({antwort.get('error')})" if antwort.get("error") else "")
        )

    # ── Der Weg ohne Schätzer — DAS läuft hier, reine stdlib, real gemessen ─────────
    ergebnisse: list[dict] = []
    namen = ("perfekt",) + bildschreiben.KONTROLLARTEN
    for name in namen:
        if name == "perfekt":
            ist = list(soll)
            kachel = kachel_perfekt(soll)
        else:
            werte = bildschreiben.kontrollwerte(name, BREITE, HOEHE)
            ist = werte
            kachel = kachel_kontrolle(werte)
        urteil = geometrie_qa.geometrie_gate(soll, ist)
        urteil["name"] = name
        urteil["spearman_abs"] = None if urteil["spearman"] is None else abs(urteil["spearman"])
        ergebnisse.append(urteil)

        px, b, h = tafel_mit_streifen(kachel, urteil)
        urteilswort = ("nicht-messbar" if urteil["score"] is None
                        else "bestanden" if urteil["bestanden"] else "durchgefallen")
        schreibe(f"{name}_score-{_z(urteil['score'])}_iou-{_z(urteil['geom_iou'])}"
                 f"_rho-{_z(urteil['spearman'])}_{urteilswort}", px, b, h)

    px, b, h = zeichne_balken(ergebnisse)
    stamm = "balken_" + "_".join(
        f"{e['name']}-{_z(e['score'])}" for e in ergebnisse
    ) + f"_schwelle-{geometrie_qa.SCHWELLE_GEOMETRIE:.2f}"
    schreibe(stamm, px, b, h)

    print(f"Bodenszene: {BREITE}x{HOEHE}, Bodenanteil {bodenanteil:.1%} "
          f"({n_boden} von {len(soll)} Punkten), hier neu gebaut, keine Blender-Datei.")
    print("Versuch am Geraet (tiefenschaetzer.qa_gegen_soll, braucht torch + Gewichte):")
    for art, status in geraet_status.items():
        print(f"  {art}: {status}")
    print("Gemessen hier, ohne Schaetzer (Kontrollwerte direkt als Ist-Tiefenkarte):")
    for e in ergebnisse:
        print(f"  {e['name']:9s} score={_z(e['score'])} geom_iou={_z(e['geom_iou'])} "
              f"spearman={_z(e['spearman'])} bestanden={e['bestanden']}")

    for p in geschrieben:
        print(p)
    # Die drei Kontrollbild-PNGs selbst gehören nicht zur Bildserie des Beweises (sie
    # sind Eingabe, nicht Befund) — trotzdem geschrieben, weil qa_gegen_soll eine echte
    # Datei braucht und Regel 4 verlangt, den reinen Python-Teil wirklich auszufuehren.
    for pfad in kontroll_pngs.values():
        print(pfad)

    perfekt = ergebnisse[0]
    if perfekt["name"] != "perfekt" or perfekt["score"] is None \
            or abs(perfekt["score"] - 1.0) > 1e-9:
        print(f"NULLPROBE VERFEHLT: perfekt gibt {perfekt.get('score')!r} statt 1.000 — "
              f"Fehler in der Szene dieses Skripts, nicht in der Metrik.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
