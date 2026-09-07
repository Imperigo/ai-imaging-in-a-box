#!/usr/bin/env python3
"""BEWEIS 20 — Die ganze Kette als ein Bild: IFC → glb → Multipass → (Render) → QA, über
``kette.baue_kette`` und ``kette.fuehre_aus`` mit den ECHTEN Ausführern gefahren, je
Stufe ein Miniaturbild ihrer echten Ausgabe — und daneben dieselbe Kette mit den fünf
Riegeln, die VOR dem Bild greifen, jeder gefärbt danach, ob er in diesem Lauf gegriffen
hat, und jeder mit einer Gegenprobe, die zeigt, dass er greifen kann.

Was bewiesen wird
-----------------
1. **Die Kette läuft von Ende zu Ende durch dieselbe Ablaufsteuerung wie im Betrieb.**
   ``kette.baue_kette(ifc_path=…)`` liefert den Vier-Knoten-Graphen, ``kette.fuehre_aus``
   rechnet ihn — mit ``kette.AUSFUEHRER``, also den echten Stufen: ``ifc_zu_glb`` im
   ``.venv-ifc`` (Prozessgrenze, Regel 1), Räume aus der IFC, Torwächter,
   ``blender --background`` (Prozessgrenze, Regel 2), ``render.rendere``,
   ``tiefenschaetzer.qa_gegen_soll``. Kein Knoten ist eine Attrappe; Attrappen hat
   Beweis 05, und der beweist etwas anderes (den Zwischenspeicher).
2. **Jede Stufe hinterlässt eine echte Ausgabe, und die steht im Bild.** Kein Miniaturbild
   ist gemalt, um etwas zu illustrieren: Es ist die Datei der Stufe (Beauty, Tiefe,
   Material-ID) oder eine Zeichnung aus Zahlen, die die Stufe in DIESEM Lauf zurückgab
   (Raumpolygone aus der IFC, Knotenboxen aus der glb, Silhouette aus der EXR).
3. **Die Stufe, die das Gerät braucht, trägt eine Marke statt eines erfundenen Bildes.**
   ``render.rendere`` wird wirklich gerufen; ohne Gewichte lehnt es ab, BEVOR ``torch``
   geladen wird (siehe Beweis 03). Die Kachel zeigt dann das blaue Schraffurfeld — die
   Marke «braucht das Gerät». Das ist NICHT GEMESSEN, nicht DURCHGEFALLEN. Auf der
   HomeStation (Gewichte unter ``$AIIMAGING_MODELLE``, torch, GPU) rendert dieselbe
   Kachel das echte Bild, und die QA-Kachel bekommt ihr Urteil.
4. **Fünf Riegel greifen vor dem Bild, und man sieht je Riegel, ob er gegriffen hat.**
   Torwächter, Bildvollständigkeit, Massstab, Rahmung, Kamerahöhe über Dach — die
   Funktionen aus ``abholer.RIEGEL`` (dem Produktivweg) bzw. aus dem Geometrie-Knoten
   selbst, jede mit den Daten dieses Laufs gerufen. Und jede ein zweites Mal mit einer
   aus denselben Messwerten abgeleiteten, absichtlich kaputten Eingabe (Gegenprobe):
   Ein Riegel, der im gesunden Lauf offen steht, beweist nur, dass er offen war — dass
   er greifen KANN, zeigt erst die Gegenprobe. Greift eine Gegenprobe nicht, ist die
   Rückgabe 1: Das wäre ein Befund gegen den Riegel, kein «nicht gemessen».

Die Geometrie ist synthetisch und entsteht hier (Regel 3): ``make_test_ifc.erzeuge_ifc``
mit Geländeplatte und zwei Räumen — der Quader 8,0 × 5,0 × 3,25 m auf der 20 × 20 m
Platte, an dem jede bestehende Messreihe hängt. Die Kamera ist ``sSE`` (über Eck) und
rahmt die **Bauwerksbox** aus ``glbbox.bauwerksbox``, genau wie der Abholer seit dem
26.08.2026 die Box reicht, wenn er sie hat. Der Multipass-Ausführer der Standardkette
kennt keine Kamerarichtung (er lässt den Runner seinen Rückfall stellen); dieser Beweis
ersetzt darum EINEN Eintrag der Ausführertabelle — ``{**kette.AUSFUEHRER, multipass:
…}``, die dokumentierte Naht — durch denselben ``seams.glb_zu_multipass``-Aufruf mit
Richtung und Hüllbox, den auch ``abholer.verarbeiter`` macht. Die Prozessgrenze, der
Runner und alle Ausgaben sind dieselben.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Bedeutung liegt in Anordnung, Farbe und Dateiname;
jede Zahl im Dateinamen ist aus einem Rückgabewert dieses Laufs gelesen.

``01_kette_…png`` — die Übersichtstafel. Fünf Kacheln von links nach rechts, Pfeile
dazwischen in Rechenreihenfolge. Über jeder Kachel ein Kopfband in der Kennfarbe ihres
Knotens (dieselben Farben wie in Beweis 05):

    Sand         IFC — der Eingang des Geometrie-Knotens (helleres Band)
    Braun        glb — die Ausgabe des Geometrie-Knotens; IFC und glb stehen zusammen
                 in EINEM braunen Rahmen, denn sie sind EIN Knoten (``ART_GEOMETRIE``)
    Stahlblau    multipass
    Violett      render
    Grün         qa

Die Kacheln selbst:

    IFC          Grundriss (Nord oben, massstäblich) aus dem, was der Knoten aus der IFC
                 zurückgab: sandfarben die Grundfläche der gemeldeten Hüllbox, türkis
                 die Grundrisspolygone der Räume (``raeume``, über ``seams.ifc_raeume``
                 durch die Prozessgrenze gelesen — das L-förmige Polygon ist ein echtes
                 Polygon, keine Box). Der Rand des Bauwerks ist NICHT gezeichnet: Der
                 Knoten liefert von der IFC nur Hüllbox, Räume und Zahlen; Wände sieht
                 erst die glb.
    glb          Derselbe Grundriss, derselbe Massstab, aus den Knotenboxen der
                 erzeugten glb (``glbbox.knotenboxen`` → ``nach_welt``): Gelände braun,
                 Bauwerksknoten stahlblau, brauner Rahmen = Szenenbox, schwarzer Rahmen =
                 Bauwerksbox (``glbbox.bauwerksbox``). Man sieht die vier Wände als
                 Ring — und dass die Räume der IFC-Kachel INNERHALB dieses Rings liegen:
                 zwei Wege durch die Prozessgrenze, ein Bezugssystem.
    multipass    Der Beauty-Pass des Blender-Laufs, verkleinert; darunter zwei kleine
                 Kacheln: die normalisierte Tiefe (nah = hell) und die Material-ID
                 (Kennfarben). Alle drei tragen dieselbe Silhouette — eine Kamera, ein
                 Lauf.
    render       Das erzeugte Bild — oder das blaue Schraffurfeld: «braucht das Gerät».
    qa           Links die Soll-Silhouette, die der QA-Knoten aus der EXR des Multipass
                 liest (``bildlesen.tiefen_aus_report`` → ``geometrie_qa.silhouette``),
                 weiss auf schwarz. Rechts die Ist-Seite: grün oder rot nach
                 ``bestanden``, wenn die QA gerechnet hat — sonst Schraffur, weil das
                 Ist-Bild vom Render kommt und der das Gerät braucht. Der Bogen oberhalb
                 der Kacheln von multipass nach qa ist die zweite Kante des Graphen:
                 Die QA hat zwei Eingänge, Slot 0 Soll, Slot 1 Ist.

Unter jeder Kachel ein Statusband, aus ``fuehre_aus`` gelesen, nicht gedeutet:

    Orange       gerechnet — der Ausführer lief und meldete ``ok``
    Blau         Geräteschranke / nicht gefahren — nicht gemessen, nicht durchgefallen
    Grau         übersprungen, weil ein Vorgänger nicht ``ok`` war
    Rot          fehler oder abgelehnt (Torwächter, Lizenz) — käme es vor, stünde es hier

Darunter ein dünner dunkler Balken: die Dauer des Knotens (``dauer_s``), linear zur
längsten Dauer der Kette. Der Multipass ist die teuerste Stufe; die Zahlen stehen im
Dateinamen.

``02_riegel_…png`` — die Riegel-Tafel. Zwei Zeilen, links je Zeile so viele Quadrate
wie die Zeilennummer. Zeile 1 ist DIESER LAUF (Miniaturen der fünf Stufen auf der
Ablauflinie), Zeile 2 die GEGENPROBE (dieselbe Linie, leere Rahmen statt Miniaturen).
Auf der Linie stehen die Riegel als Balken, an der Stelle, an der sie im Ablauf greifen:

    nach glb, vor multipass:         1  Torwächter  (``torwaechter.torwaechter`` im
                                        Geometrie-Knoten — Massstab und Georeferenz)
    nach multipass, vor render:      2  Bildvollständigkeit  (``_bilder_vollstaendig``)
                                     3  Massstab  (``_massstab_gemeldet``)
                                     4  Rahmung  (``kameras.rahmungsverhaeltnis`` mit
                                        der Box, die die Kamera gerahmt hat)
                                     5  Kamerahöhe über Dach
                                        (``_komposition_vor_dem_render`` /
                                        ``_kamera_ueber_dach``)

    Grün, ANGEHOBEN über der Linie   offen — geprüft, nicht gegriffen; die Linie läuft
    Rot, AUF der Linie               gegriffen — Abbruch; die Linie dahinter wird blass
    Bernstein, auf der Linie         beanstandet, aber kein Abbruch — der Massstab
                                     MELDET nur (Begründung in ``_massstab_gemeldet``);
                                     die Linie läuft weiter
    Grau, angehoben, nur Umriss      nicht gemessen — die Eingabe fehlt (ohne
                                     Blender-Lauf gibt es keinen Bericht, also keine
                                     Bilder, keine Kamera, keine gemessene Rahmung)

Man sieht in Zeile 1, welche Riegel im gezeigten Lauf offen standen, und in Zeile 2,
dass jeder davon zufällt, sobald man ihm gibt, wofür er gebaut ist: die Hüllbox mal
1000 (Torwächter), die Hüllbox mal 0,001 (Massstab), die SZENENBOX als gerahmte Box
statt der Bauwerksbox (Rahmung — der Fall aus Beweis 13, hier an derselben Geometrie
nachgemessen), die Kamera einen Meter über die Dachkante gehoben (Dach), und eine auf
die Hälfte abgeschnittene Kopie einer echten PNG dieses Laufs (Bildvollständigkeit).
Die Gegenproben laufen auch ohne Blender, weil sie reine Arithmetik auf gemessenen
Zahlen sind; nur die Kamera für die Dach-Gegenprobe kommt dann aus
``kameras.kamerasatz`` diesseits statt aus dem Bericht — der Dateiname sagt, woher.

``03_…`` bis ``09_…png`` — die Miniaturen einzeln in voller Grösse: der IFC-Grundriss,
der glb-Grundriss, die drei Multipass-Ausgaben Byte für Byte kopiert, das Render (falls
gerechnet), die Soll-Silhouette der QA.

Was das Gerät braucht — und was nicht
-------------------------------------
* IFC → glb, Räume, Torwächter, Grundrisse, alle fünf Gegenproben: **hier**, ohne GPU,
  ohne Blender (``.venv-ifc`` genügt).
* Multipass: **Blender 4.2 auf der CPU genügt** (rund zwei Minuten bei 256 px, 8
  Samples). Mit ``--ohne-blender`` oder ohne Blender wird die Stufe als «nicht gefahren»
  geführt (Blau), render und qa werden übersprungen (Grau), und drei Riegel der ersten
  Zeile bleiben grau. Kein Fehlschlag: Rückgabe 0.
* Render und QA: **das Gerät** (Gewichte, torch, GPU). Hier: Blau mit Marke.

Aufruf:
    python3 tools/beweis/20_kette_von_ende_zu_ende.py [ziel_verzeichnis] [--ohne-blender]
        [--aufloesung 256] [--samples 8]

Ohne Argument schreibt es nach ``build/beweis/20_kette_von_ende_zu_ende/``. Rückgabe 1,
wenn der Torwächter die gesunde Geometrie ablehnt, der Geometrie-Knoten scheitert, oder
eine Gegenprobe nicht greift — Befunde gegen die Kette, nicht gegen die Umgebung.
"""
from __future__ import annotations

import argparse
import copy
import math
import shutil
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

import make_test_ifc  # noqa: E402
from aiimaging import (  # noqa: E402
    abholer, bildlesen, bildschreiben, geometrie_qa, glbbox, kameras, kette, render,
    seams, torwaechter,
)
from aiimaging.maske import ist_gelaende  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "20_kette_von_ende_zu_ende"

KAMERA = "sSE"
AUFLOESUNG = 256
SAMPLES = 8
PROMPT = "Wohnhaus am Hang, Morgenlicht, klare Sicht"

#: Wie in ``studie_paarmasse`` und Beweis 02: Auf der CPU verhungert der Herzschlagfaden
#: unter Cycles-Last, und die Wache meldete einen Stillstand, den es nicht gibt.
HERZSCHLAG_S = 12.0

#: Eigener Status des Multipass-Knotens, wenn Blender nicht gefahren wird. Kein
#: ``fehler``: Die Kette überspringt die Nachfolger in beiden Fällen, aber das Bild soll
#: «nicht gemessen» von «gescheitert» unterscheiden können — die Hausregel.
STATUS_NICHT_GEFAHREN = "nicht_gefahren"

# --------------------------------------------------------------------------------------
# Farbsprache — jede Farbe hat genau eine Bedeutung, siehe Docstring
# --------------------------------------------------------------------------------------
KENNFARBE = {
    "ifc": (205, 175, 115),                     # Sand — Eingang
    kette.KNOTEN_GEOMETRIE: (140, 100, 60),     # Braun
    kette.KNOTEN_MULTIPASS: (70, 100, 150),     # Stahlblau
    kette.KNOTEN_RENDER: (130, 80, 150),        # Violett
    kette.KNOTEN_QA: (60, 150, 70),             # Grün
}
FARBE_GERECHNET = (230, 120, 40)         # Orange
FARBE_GERAET = (80, 110, 175)            # Blau — Geräteschranke / nicht gefahren
FARBE_GERAET_HELL = (150, 175, 215)      # Schraffur darauf
FARBE_UEBERSPRUNGEN = (200, 200, 200)    # Grau
FARBE_FEHLER = (190, 60, 50)             # Rot
FARBE_BESTANDEN = (60, 150, 70)
FARBE_DURCHGEFALLEN = (190, 60, 50)
FARBE_OFFEN = (60, 150, 70)              # Riegel offen
FARBE_GEGRIFFEN = (190, 60, 50)          # Riegel zu
FARBE_GEMELDET = (200, 150, 40)          # Riegel meldet, bricht nicht ab
FARBE_UNGEMESSEN = (160, 160, 160)       # Riegel ohne Eingabe
FARBE_LINIE = (60, 60, 60)
FARBE_LINIE_BLASS = (200, 200, 200)
FARBE_LEINWAND = (245, 245, 245)
FARBE_RAHMEN = (110, 110, 110)
FARBE_DAUER = (40, 40, 40)

FARBE_GELAENDE = (139, 101, 60)
FARBE_BAUWERK = (70, 110, 160)
FARBE_RAUM = (60, 160, 160)
FARBE_PLAN_GRUND = (245, 245, 245)
FARBE_SAND = (222, 205, 165)
FARBE_SZENENBOX = (110, 75, 40)
FARBE_BAUWERKSBOX = (20, 20, 20)

KACHEL = 192
KOPF = 14
SUB = 84                                 # Nebenkachel unter dem Multipass
SUB_FUGE = KACHEL - 2 * SUB
FUGE_X = 56
RAND = 28
SCHLEIFE = 26                            # Bahn des Bogens multipass → qa
STATUS_H, DAUER_H = 10, 6
PLAN_RAND = 10

THUMB = 96                               # Miniatur auf der Riegel-Tafel
RIEGEL_B, RIEGEL_H = 14, 56
RIEGEL_ABSTAND = 34
ZAEHLER_KANTE, ZAEHLER_FUGE = 8, 4


# --------------------------------------------------------------------------------------
# Zeichenhilfen — achsparallel, damit der stdlib-Schreiber genügt
# --------------------------------------------------------------------------------------

def _neu(breite: int, hoehe: int, farbe=FARBE_LEINWAND) -> list:
    return [farbe] * (breite * hoehe)


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke=1) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _linie(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke=2) -> None:
    """Waagrechte oder senkrechte Strecke. Schräge braucht dieses Layout nicht."""
    h = dicke / 2
    if y0 == y1:
        _rechteck(px, breite, hoehe, min(x0, x1), y0 - h, max(x0, x1), y0 + h, farbe)
    elif x0 == x1:
        _rechteck(px, breite, hoehe, x0 - h, min(y0, y1), x0 + h, max(y0, y1), farbe)
    else:
        raise ValueError(f"nur achsparallele Strecken: ({x0},{y0})→({x1},{y1})")


def _pfeilspitze(px, breite, hoehe, x, y, richtung: str, farbe, groesse=7) -> None:
    for d in range(groesse + 1):
        halb = d * 0.6
        if richtung == "rechts":
            _rechteck(px, breite, hoehe, x - d, y - halb, x - d + 1, y + halb + 1, farbe)
        elif richtung == "unten":
            _rechteck(px, breite, hoehe, x - halb, y - d, x + halb + 1, y - d + 1, farbe)
        else:
            raise ValueError(richtung)


def _schraffur(px, breite, hoehe, x0, y0, x1, y1, farbe, abstand=12) -> None:
    """Diagonale Linien über einem Feld — die Marke «nicht gemessen» ohne Schrift."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x - x0 + y - y0) % abstand < 2:
                px[y * breite + x] = farbe


def _blit(px, breite, hoehe, quelle, qb, qh, x0, y0) -> None:
    for y in range(qh):
        zy = y0 + y
        if 0 <= zy < hoehe:
            px[zy * breite + x0:zy * breite + x0 + qb] = quelle[y * qb:(y + 1) * qb]


def _skaliere(quelle, qb, qh, nb, nh) -> list:
    """Nächster Nachbar — keine Interpolation, damit kein Wert entsteht, der nie
    gemessen wurde (dieselbe Linie wie in Beweis 04)."""
    aus = []
    for y in range(nh):
        qy = min(qh - 1, y * qh // nh)
        zeile = quelle[qy * qb:(qy + 1) * qb]
        aus.extend(zeile[min(qb - 1, x * qb // nb)] for x in range(nb))
    return aus


def _polygon(px, breite, hoehe, punkte, farbe) -> None:
    """Gefülltes Polygon, Zeilenabtastung mit Gerade/Ungerade-Regel — die Räume der
    Test-IFC sind L-förmig, ein Rechteckfüller genügt dort nicht."""
    if len(punkte) < 3:
        return
    ys = [p[1] for p in punkte]
    for y in range(max(0, int(math.floor(min(ys)))), min(hoehe, int(math.ceil(max(ys))))):
        ym = y + 0.5
        schnitte = []
        for i, (xa, ya) in enumerate(punkte):
            xb, yb = punkte[(i + 1) % len(punkte)]
            if (ya <= ym < yb) or (yb <= ym < ya):
                schnitte.append(xa + (ym - ya) * (xb - xa) / (yb - ya))
        schnitte.sort()
        for a, b in zip(schnitte[0::2], schnitte[1::2]):
            _rechteck(px, breite, hoehe, a, y, b, y + 1, farbe)


def _zaehler(px, breite, hoehe, x, y, n: int) -> None:
    for i in range(n):
        x0 = x + i * (ZAEHLER_KANTE + ZAEHLER_FUGE)
        _rechteck(px, breite, hoehe, x0, y, x0 + ZAEHLER_KANTE, y + ZAEHLER_KANTE, FARBE_DAUER)


def _fmt(x) -> str:
    if x is None:
        return "ungemessen"
    if isinstance(x, float):
        return f"{x:.3f}".rstrip("0").rstrip(".") or "0"
    return str(x)


# --------------------------------------------------------------------------------------
# Grundrisse — aus Zahlen dieses Laufs, in einem gemeinsamen Massstab
# --------------------------------------------------------------------------------------

class Plan:
    """Welt-XY → Kachelpixel, Nord oben. Ein Massstab für IFC- und glb-Kachel, damit
    die Räume der einen sichtbar im Wandring der anderen liegen."""

    def __init__(self, bbox, kante: int = KACHEL, rand: int = PLAN_RAND) -> None:
        (x0, y0, _), (x1, y1, _) = bbox
        self.x0, self.y0 = float(x0), float(y0)
        dx, dy = max(1e-9, float(x1) - self.x0), max(1e-9, float(y1) - self.y0)
        self.s = min((kante - 2 * rand) / dx, (kante - 2 * rand) / dy)
        self.kante, self.rand = kante, rand
        self.ox = rand + ((kante - 2 * rand) - dx * self.s) / 2
        self.oy = rand + ((kante - 2 * rand) - dy * self.s) / 2

    def p(self, x, y):
        return (self.ox + (float(x) - self.x0) * self.s,
                self.kante - self.oy - (float(y) - self.y0) * self.s)

    def rechteck(self, px, lo, hi, farbe, *, rahmen=None, dicke=1) -> None:
        xa, ya = self.p(lo[0], lo[1])
        xb, yb = self.p(hi[0], hi[1])
        if rahmen is None:
            _rechteck(px, self.kante, self.kante, xa, yb, xb, ya, farbe)
        else:
            _rahmen(px, self.kante, self.kante, xa, yb, xb, ya, rahmen, dicke)


def kachel_ifc(geometrie: dict) -> tuple[list, dict]:
    """Was der Geometrie-Knoten aus der IFC selbst zurückgab: Hüllbox und Räume."""
    plan = Plan(geometrie["bbox"])
    px = _neu(KACHEL, KACHEL, FARBE_PLAN_GRUND)
    lo, hi = geometrie["bbox"]
    plan.rechteck(px, lo, hi, FARBE_SAND)
    raeume = (geometrie.get("raeume") or {}).get("raeume") or []
    n_gezeichnet = 0
    for eintrag in raeume:
        ring = eintrag["raum"].get("grundriss_m")
        if not ring:
            continue
        _polygon(px, KACHEL, KACHEL, [plan.p(x, y) for x, y in ring], FARBE_RAUM)
        n_gezeichnet += 1
    return px, {"n_raeume": len(raeume), "n_gezeichnet": n_gezeichnet,
                "n_elements": geometrie.get("n_elements"),
                "n_triangles": geometrie.get("n_triangles")}


def kachel_glb(geometrie: dict, box: dict) -> tuple[list, dict]:
    """Die Knotenboxen der erzeugten glb, Gelände und Bauwerk nach derselben Regel wie
    ``glbbox.bauwerksbox``; darüber Szenen- und Bauwerksbox als Rahmen."""
    js = glbbox.lies_gltf_json(geometrie["glb_path"])
    knoten = glbbox.knotenboxen(js)["knoten"]
    welt = [(name, *glbbox.nach_welt(lo, hi, geometrie["up_axis"])) for name, lo, hi in knoten]
    plan = Plan(box["bbox_szene"])
    px = _neu(KACHEL, KACHEL, FARBE_PLAN_GRUND)
    # Gelände zuerst, dann Bauwerk nach Grundfläche absteigend — Kleines liegt oben.
    def flaeche(e):
        return (e[2][0] - e[1][0]) * (e[2][1] - e[1][1])
    for name, lo, hi in sorted(welt, key=lambda e: (not ist_gelaende(e[0]), -flaeche(e))):
        plan.rechteck(px, lo, hi, FARBE_GELAENDE if ist_gelaende(name) else FARBE_BAUWERK)
    plan.rechteck(px, *box["bbox_szene"], None, rahmen=FARBE_SZENENBOX, dicke=2)
    if box["bbox_bauwerk"] is not None:
        plan.rechteck(px, *box["bbox_bauwerk"], None, rahmen=FARBE_BAUWERKSBOX, dicke=2)
    return px, {"n_knoten": len(welt), "n_bauwerk": box["n_bauwerk"],
                "n_gelaende": box["n_gelaende"], "schrumpfung": box["schrumpfung"]}


def kachel_marke() -> list:
    """Das blaue Schraffurfeld — «braucht das Gerät»."""
    px = _neu(KACHEL, KACHEL, FARBE_GERAET)
    _schraffur(px, KACHEL, KACHEL, 0, 0, KACHEL, KACHEL, FARBE_GERAET_HELL)
    return px


def kachel_aus_png(pfad) -> list:
    farben, b, h = bildlesen.lies_png_farben(pfad)
    return _skaliere(farben, b, h, KACHEL, KACHEL)


def kachel_aus_grau_png(pfad, kante: int) -> list:
    grau, b, h = bildlesen.lies_png_graustufen(pfad)
    return _skaliere([(int(round(g * 255)),) * 3 for g in grau], b, h, kante, kante)


def kachel_qa(bericht: dict | None, qa: dict) -> tuple[list, dict]:
    """Links das Soll, wie der QA-Knoten es liest; rechts das Urteil oder die Marke."""
    px = _neu(KACHEL, KACHEL, (0, 0, 0))
    info = {"n_soll": None, "bestanden": None, "score": None}
    halb = KACHEL // 2
    if bericht is not None and bericht.get("depth_exr"):
        soll, b, h = bildlesen.tiefen_aus_report(bericht)
        silh = geometrie_qa.silhouette(soll)
        info["n_soll"] = sum(silh)
        bild = [(235, 235, 235) if s else (0, 0, 0) for s in silh]
        _blit(px, KACHEL, KACHEL, _skaliere(bild, b, h, halb, halb), halb, halb,
              0, (KACHEL - halb) // 2)
    else:
        _rechteck(px, KACHEL, KACHEL, 0, 0, halb, KACHEL, FARBE_UEBERSPRUNGEN)
    ausgaben = qa.get("ausgaben") or {}
    if qa["status"] == kette.STATUS_OK and "bestanden" in ausgaben:
        info["bestanden"] = bool(ausgaben["bestanden"])
        info["score"] = ausgaben.get("score")
        _rechteck(px, KACHEL, KACHEL, halb, 0, KACHEL, KACHEL,
                  FARBE_BESTANDEN if info["bestanden"] else FARBE_DURCHGEFALLEN)
    else:
        _rechteck(px, KACHEL, KACHEL, halb, 0, KACHEL, KACHEL, FARBE_GERAET)
        _schraffur(px, KACHEL, KACHEL, halb, 0, KACHEL, KACHEL, FARBE_GERAET_HELL)
    return px, info


# --------------------------------------------------------------------------------------
# Die Kette — echte Ausführer, eine Naht ersetzt
# --------------------------------------------------------------------------------------

def multipass_ausfuehrer(*, blender_fahren: bool, aufloesung: int, samples: int):
    """Der Multipass mit Kamerarichtung und Bauwerksbox — wie ``abholer.verarbeiter``.

    ``kette._fuehre_multipass`` reicht keine Richtung durch, der Runner stellte dann
    seinen Rückfall («diagonal von vorn-oben, nicht komponiert»), und die Riegel Rahmung
    und Dach hätten nichts zu beurteilen (``komposition.beurteile_bericht`` lehnt den
    Rückfallweg ausdrücklich ab). Derselbe Aufruf, dieselbe Prozessgrenze — nur mit
    ``kamera`` und ``kamera_huellbox``.
    """
    def fuehre(*, knoten, eingaben, out_dir):
        if not eingaben or not eingaben[0].get("glb_path"):
            return {"status": kette.STATUS_FEHLER, "error": "Multipass ohne glb."}
        geometrie = eingaben[0]
        box = glbbox.bauwerksbox(geometrie["glb_path"], up_axis=geometrie["up_axis"])
        gerahmt = box["bbox_bauwerk"] if box["bbox_bauwerk"] is not None else box["bbox_szene"]
        if not blender_fahren:
            return {"status": STATUS_NICHT_GEFAHREN,
                    "error": "Blender nicht gefahren (--ohne-blender oder kein Blender).",
                    "_gerahmte_box": gerahmt, "_glbbox": _glbbox_kurz(box)}
        bericht = seams.glb_zu_multipass(
            geometrie["glb_path"], out_dir, up_axis=geometrie["up_axis"],
            aufloesung=aufloesung, samples=samples,
            kamera=KAMERA, kamera_huellbox=gerahmt, herzschlag_takt_s=HERZSCHLAG_S)
        bericht.setdefault("status", kette.STATUS_OK)
        bericht["_gerahmte_box"] = gerahmt
        bericht["_glbbox"] = _glbbox_kurz(box)
        if not bericht.get("depth_png"):
            # Dieselbe Regel wie in ``kette._fuehre_multipass``: Ohne PNG keine
            # Konditionierung, und die Meldung gehört an diesen Knoten.
            return {**bericht, "status": kette.STATUS_FEHLER,
                    "error": f"keine normalisierte Tiefenkarte: "
                             f"{bericht.get('depth_png_fehler') or 'kein Grund genannt'}"}
        return bericht
    return fuehre


def _glbbox_kurz(box: dict) -> dict:
    return {k: box[k] for k in ("bbox_szene", "bbox_bauwerk", "schrumpfung", "n_bauwerk",
                                "n_gelaende", "entschieden_durch")}


def blender_verfuegbar() -> tuple[bool, str]:
    try:
        return True, seams.finde_blender()
    except seams.SeamError as fehler:
        return False, str(fehler)


def fahre_kette(ifc: Path, arbeit: Path, *, blender_fahren: bool, aufloesung: int,
                samples: int) -> dict:
    graph = kette.baue_kette(ifc_path=str(ifc), prompt=PROMPT, aufloesung=aufloesung,
                             samples=samples)
    ausfuehrer = {**kette.AUSFUEHRER,
                  kette.ART_MULTIPASS: multipass_ausfuehrer(
                      blender_fahren=blender_fahren, aufloesung=aufloesung, samples=samples)}
    # Ohne Zwischenspeicher: Jede Stufe rechnet. Den Cache beweist Beweis 05.
    return kette.fuehre_aus(graph, cache=None, ausfuehrer=ausfuehrer,
                            out_dir=arbeit / "out", pruefe_verdrahtung=True)


#: Wie ein Knotenergebnis auf die Farbsprache abgebildet wird.
LAGE_GERECHNET, LAGE_GERAET, LAGE_UEBERSPRUNGEN, LAGE_FEHLER = (
    "gerechnet", "geraet", "uebersprungen", "fehler")


def lage(kid: str, eintrag: dict, *, gewichte_da: bool) -> str:
    """Status → Lage. Blau ist nur, was NICHT GEMESSEN ist: Blender nicht gefahren, oder
    die Renderstufe scheitert an Ablage/torch/CUDA. Eine Ablehnung aus Lizenz oder
    Vertrag bleibt rot — das wäre ein Befund, keine Schranke."""
    status = eintrag["status"]
    if status == kette.STATUS_OK:
        return LAGE_GERECHNET
    if status == kette.STATUS_UEBERSPRUNGEN:
        return LAGE_UEBERSPRUNGEN
    if status == STATUS_NICHT_GEFAHREN:
        return LAGE_GERAET
    if kid == kette.KNOTEN_RENDER:
        text = (eintrag.get("error") or "").lower()
        if status == kette.STATUS_ABGELEHNT and not gewichte_da:
            return LAGE_GERAET
        if any(w in text for w in ("torch", "diffusers", "cuda", "gewichte")):
            return LAGE_GERAET
    return LAGE_FEHLER


LAGE_FARBE = {LAGE_GERECHNET: FARBE_GERECHNET, LAGE_GERAET: FARBE_GERAET,
              LAGE_UEBERSPRUNGEN: FARBE_UEBERSPRUNGEN, LAGE_FEHLER: FARBE_FEHLER}


# --------------------------------------------------------------------------------------
# Die Riegel — mit den Daten dieses Laufs, und je einmal mit kaputter Eingabe
# --------------------------------------------------------------------------------------

RIEGEL_OFFEN, RIEGEL_GEGRIFFEN, RIEGEL_GEMELDET, RIEGEL_UNGEMESSEN = (
    "offen", "gegriffen", "gemeldet", "ungemessen")
RIEGEL_FARBE = {RIEGEL_OFFEN: FARBE_OFFEN, RIEGEL_GEGRIFFEN: FARBE_GEGRIFFEN,
                RIEGEL_GEMELDET: FARBE_GEMELDET, RIEGEL_UNGEMESSEN: FARBE_UNGEMESSEN}
RIEGEL_NAMEN = ("torwaechter", "bilder", "massstab", "rahmung", "dach")


def _skaliert(bbox, faktor: float):
    return [[float(v) * faktor for v in ecke] for ecke in bbox]


def _kamera_diesseits(bbox_bauwerk) -> dict:
    """Der Kamerablock, wie der Runner ihn aus ``kameras.kamerasatz`` schreibt — für die
    Dach-Gegenprobe ohne Bericht. Dieselbe Funktion, dieselben Felder."""
    satz = kameras.kamerasatz(bbox_bauwerk, kuerzel=[KAMERA])
    k = satz["kameras"][0]
    return {"weg": "abgeleitet", "kuerzel": k["kuerzel"], "auge": list(k["auge"]),
            "gelaende_z": satz["gelaende_z"],
            "gebaeudehoehe_m": satz["mitte"][2] + satz["masse_m"][2] / 2.0 - satz["gelaende_z"]}


def riegel_dieser_lauf(geometrie: dict, bericht: dict | None) -> dict:
    """Je Riegel ``{lage, wert}`` aus dem, was in diesem Lauf vorlag."""
    urteil = geometrie.get("torwaechter") or {}
    aus = {"torwaechter": {
        "lage": (RIEGEL_OFFEN if urteil.get("entscheidung") == torwaechter.ENTSCHEIDUNG_ANNEHMEN
                 else RIEGEL_GEGRIFFEN if urteil else RIEGEL_UNGEMESSEN),
        "wert": urteil.get("entscheidung")}}

    # Der Massstab kennt seine Eingabe auch ohne Bericht: die Hüllbox der Konversion —
    # genau die, mit der ``_massstab_gemeldet`` rechnet, wenn der Bericht keine
    # Bauwerksbox trägt.
    m = abholer._massstab_gemeldet(bericht if bericht else {"bbox": geometrie.get("bbox")})
    aus["massstab"] = {
        "lage": (RIEGEL_UNGEMESSEN if not m["geprueft"]
                 else RIEGEL_GEMELDET if m["beanstandet"] else RIEGEL_OFFEN),
        "wert": m.get("groesste_kante_m")}

    if bericht is None:
        for name in ("bilder", "rahmung", "dach"):
            aus[name] = {"lage": RIEGEL_UNGEMESSEN, "wert": None}
        return aus

    b = abholer._bilder_vollstaendig(bericht)
    aus["bilder"] = {"lage": RIEGEL_OFFEN if b["vollstaendig"] else RIEGEL_GEGRIFFEN,
                     "wert": len(b["geprueft"])}

    # Rahmung: Die Frage ist «wieviel Bild füllt das Bauwerk, wenn die Kamera DIESE Box
    # rahmt». Gerahmt hat die Kamera hier die Bauwerksbox (``kamera_huellbox``); erste
    # Box ist darum die gerahmte, gemessener Füllgrad aus dem Bericht. Das Produktivurteil
    # ``_rahmung_vor_dem_render(bericht)`` nimmt stets ``bericht['bbox']`` — die Szene —
    # als gerahmte Box; es wird unten als Befund gedruckt, nicht ins Bild gedeutet.
    kamera = bericht.get("kamera") or {}
    r = kameras.rahmungsverhaeltnis(
        bericht.get("_gerahmte_box"), bericht.get("bbox_bauwerk"),
        deckungsgrad=float(bericht.get("deckungsgrad") or kameras.DECKUNGSGRAD),
        gemessener_fuellgrad=kamera.get("fuellgrad") if kamera.get("weg") == "abgeleitet" else None)
    aus["rahmung"] = {
        "lage": (RIEGEL_UNGEMESSEN if r["abbruch"] is None or kamera.get("weg") != "abgeleitet"
                 else RIEGEL_GEGRIFFEN if r["abbruch"] else RIEGEL_OFFEN),
        "wert": r.get("wirksame_bildbreite")}

    k = abholer._komposition_vor_dem_render(bericht)
    aus["dach"] = {
        "lage": (RIEGEL_GEGRIFFEN if k["abbruch"]
                 else RIEGEL_OFFEN if k.get("beurteilt") else RIEGEL_UNGEMESSEN),
        "wert": (float(kamera["auge"][2]) - float(kamera["gelaende_z"])
                 if kamera.get("auge") and kamera.get("gelaende_z") is not None else None)}
    return aus


def riegel_gegenprobe(geometrie: dict, box: dict, bericht: dict | None,
                      png_fuer_bilder: Path, arbeit: Path) -> dict:
    """Jeder Riegel mit einer Eingabe, für die er gebaut ist — abgeleitet aus den
    Messwerten dieses Laufs, nicht erfunden."""
    bbox = geometrie["bbox"]
    aus = {}

    t = torwaechter.torwaechter({"status": "ok", "bbox": _skaliert(bbox, 1000.0)})
    aus["torwaechter"] = {
        "lage": (RIEGEL_GEGRIFFEN if t["entscheidung"] != torwaechter.ENTSCHEIDUNG_ANNEHMEN
                 else RIEGEL_OFFEN),
        "wert": (t.get("massstab") or {}).get("groesste_kante_m")}

    m = abholer._massstab_gemeldet({"bbox": _skaliert(bbox, 0.001)})
    aus["massstab"] = {"lage": RIEGEL_GEMELDET if m["beanstandet"] else RIEGEL_OFFEN,
                       "wert": m.get("groesste_kante_m")}

    # Die Szenenbox als gerahmte Box — was ohne ``kamera_huellbox`` geschähe (Beweis 13).
    r = kameras.rahmungsverhaeltnis(box["bbox_szene"], box["bbox_bauwerk"],
                                    deckungsgrad=kameras.DECKUNGSGRAD)
    aus["rahmung"] = {"lage": (RIEGEL_UNGEMESSEN if r["abbruch"] is None
                               else RIEGEL_GEGRIFFEN if r["abbruch"] else RIEGEL_OFFEN),
                      "wert": r.get("wirksame_bildbreite")}

    # Die Kamera einen Meter über die Dachkante — am echten Kamerablock des Laufs, wenn
    # es ihn gibt, sonst am diesseits gerechneten.
    if bericht is not None and (bericht.get("kamera") or {}).get("weg") == "abgeleitet":
        kamera, quelle = copy.deepcopy(bericht["kamera"]), "bericht"
    else:
        kamera, quelle = _kamera_diesseits(box["bbox_bauwerk"]), "kamerasatz"
    kamera["auge"][2] = float(kamera["gelaende_z"]) + float(kamera["gebaeudehoehe_m"]) + 1.0
    d = abholer._kamera_ueber_dach(kamera)
    aus["dach"] = {"lage": RIEGEL_GEGRIFFEN if d["abbruch"] else RIEGEL_OFFEN,
                   "wert": float(kamera["auge"][2]) - float(kamera["gelaende_z"]),
                   "quelle": quelle}

    # Eine echte PNG dieses Laufs, auf die Hälfte abgeschnitten.
    daten = Path(png_fuer_bilder).read_bytes()
    halb = arbeit / "abgeschnitten.png"
    halb.write_bytes(daten[: len(daten) // 2])
    b = abholer._bilder_vollstaendig({"depth_png": str(halb)})
    aus["bilder"] = {"lage": RIEGEL_GEGRIFFEN if not b["vollstaendig"] else RIEGEL_OFFEN,
                     "wert": len(daten) // 2, "quelle": Path(png_fuer_bilder).name}
    return aus


# --------------------------------------------------------------------------------------
# Tafel 1 — die Kette
# --------------------------------------------------------------------------------------

REIHE = ("ifc", kette.KNOTEN_GEOMETRIE, kette.KNOTEN_MULTIPASS, kette.KNOTEN_RENDER,
         kette.KNOTEN_QA)


def zeichne_kette(kacheln: dict, neben: dict, lagen: dict, dauern: dict):
    """Fünf Kacheln, Kopfbänder, Pfeile, der Bogen, Statusbänder, Dauerbalken."""
    b = 2 * RAND + 5 * KACHEL + 4 * FUGE_X
    oben = RAND + SCHLEIFE
    y_kachel = oben + KOPF
    y_status = y_kachel + KACHEL + 6
    y_dauer = y_status + STATUS_H + 6
    y_neben = y_dauer + DAUER_H + 10
    h = y_neben + SUB + RAND
    px = _neu(b, h)
    xs = [RAND + i * (KACHEL + FUGE_X) for i in range(5)]

    # Knotenrahmen: IFC und glb sind EIN Knoten.
    _rahmen(px, b, h, xs[0] - 8, oben - 8, xs[1] + KACHEL + 8, y_dauer + DAUER_H + 8,
            KENNFARBE[kette.KNOTEN_GEOMETRIE], 2)
    for i in (2, 3, 4):
        _rahmen(px, b, h, xs[i] - 8, oben - 8, xs[i] + KACHEL + 8, y_dauer + DAUER_H + 8,
                KENNFARBE[REIHE[i]], 2)

    ym = y_kachel + KACHEL // 2
    for i in range(4):
        _linie(px, b, h, xs[i] + KACHEL + 8, ym, xs[i + 1] - 9, ym, FARBE_LINIE)
        _pfeilspitze(px, b, h, xs[i + 1] - 9, ym, "rechts", FARBE_LINIE)
    # Der Bogen: zweite Kante in die QA (Slot 0, das Soll).
    xa, xb = xs[2] + KACHEL // 2, xs[4] + KACHEL // 2
    _linie(px, b, h, xa, oben - 9, xa, RAND, FARBE_LINIE)
    _linie(px, b, h, xa, RAND, xb, RAND, FARBE_LINIE)
    _linie(px, b, h, xb, RAND, xb, oben - 9, FARBE_LINIE)
    _pfeilspitze(px, b, h, xb, oben - 9, "unten", FARBE_LINIE)

    dauer_max = max([d for d in dauern.values() if d] + [1e-9])
    for i, name in enumerate(REIHE):
        x = xs[i]
        _rechteck(px, b, h, x, oben, x + KACHEL, oben + KOPF, KENNFARBE[name])
        _blit(px, b, h, kacheln[name], KACHEL, KACHEL, x, y_kachel)
        _rahmen(px, b, h, x, oben, x + KACHEL, y_kachel + KACHEL, FARBE_RAHMEN)
        knoten = kette.KNOTEN_GEOMETRIE if name == "ifc" else name
        _rechteck(px, b, h, x, y_status, x + KACHEL, y_status + STATUS_H,
                  LAGE_FARBE[lagen[knoten]])
        d = dauern.get(knoten) or 0.0
        _rechteck(px, b, h, x, y_dauer, x + max(2.0, KACHEL * d / dauer_max),
                  y_dauer + DAUER_H, FARBE_DAUER)
        if name in neben:
            for j, kachel in enumerate(neben[name]):
                nx = x + j * (SUB + SUB_FUGE)
                _blit(px, b, h, kachel, SUB, SUB, nx, y_neben)
                _rahmen(px, b, h, nx, y_neben, nx + SUB, y_neben + SUB, FARBE_RAHMEN)
    return px, b, h


# --------------------------------------------------------------------------------------
# Tafel 2 — die Riegel
# --------------------------------------------------------------------------------------

def zeichne_riegel(thumbs: list, lauf: dict, gegenprobe: dict):
    """Zwei Zeilen: dieser Lauf mit Miniaturen, die Gegenprobe mit leeren Rahmen."""
    links = 40
    luecke_klein, luecke_tor, luecke_vier = 40, 70, 4 * RIEGEL_ABSTAND + 40
    xs = [links + RAND]
    xs.append(xs[0] + THUMB + luecke_klein)             # glb
    xs.append(xs[1] + THUMB + luecke_tor)               # multipass
    xs.append(xs[2] + THUMB + luecke_vier)              # render
    xs.append(xs[3] + THUMB + luecke_klein)             # qa
    b = xs[4] + THUMB + RAND
    zeile_h = THUMB + 2 * RAND
    h = 2 * zeile_h
    px = _neu(b, h)

    # Riegelpositionen: Torwächter mittig in der Lücke glb→multipass, die vier anderen
    # in der Lücke multipass→render — in der Reihenfolge des Verarbeiters.
    pos = {"torwaechter": xs[1] + THUMB + luecke_tor / 2}
    start = xs[2] + THUMB + 20 + RIEGEL_ABSTAND / 2
    for j, name in enumerate(("bilder", "massstab", "rahmung", "dach")):
        pos[name] = start + j * RIEGEL_ABSTAND

    for zeile, (riegel, mit_thumbs) in enumerate(((lauf, True), (gegenprobe, False))):
        y0 = zeile * zeile_h
        ym = y0 + RAND + THUMB // 2
        _zaehler(px, b, h, 12, ym - ZAEHLER_KANTE // 2, zeile + 1)
        # Die Linie, blass hinter dem ersten Riegel, der gegriffen hat.
        x_ende = xs[4]
        gegriffen = sorted(pos[n] for n in RIEGEL_NAMEN if riegel[n]["lage"] == RIEGEL_GEGRIFFEN)
        x_block = gegriffen[0] if gegriffen else None
        if x_block is None:
            _linie(px, b, h, xs[0], ym, x_ende, ym, FARBE_LINIE)
        else:
            _linie(px, b, h, xs[0], ym, x_block, ym, FARBE_LINIE)
            _linie(px, b, h, x_block, ym, x_ende, ym, FARBE_LINIE_BLASS)
        for i, x in enumerate(xs):
            if mit_thumbs:
                _blit(px, b, h, thumbs[i], THUMB, THUMB, x, y0 + RAND)
                _rahmen(px, b, h, x, y0 + RAND, x + THUMB, y0 + RAND + THUMB, FARBE_RAHMEN)
            else:
                _rechteck(px, b, h, x, y0 + RAND, x + THUMB, y0 + RAND + THUMB, FARBE_LEINWAND)
                _rahmen(px, b, h, x, y0 + RAND, x + THUMB, y0 + RAND + THUMB, FARBE_RAHMEN)
                _rechteck(px, b, h, x, y0 + RAND, x + THUMB, y0 + RAND + KOPF, KENNFARBE[REIHE[i]])
        for name in RIEGEL_NAMEN:
            x = pos[name]
            zustand = riegel[name]["lage"]
            farbe = RIEGEL_FARBE[zustand]
            if zustand in (RIEGEL_GEGRIFFEN, RIEGEL_GEMELDET):
                ya, yb = ym - RIEGEL_H / 2, ym + RIEGEL_H / 2
            else:
                ya, yb = ym - 8 - RIEGEL_H, ym - 8
            if zustand == RIEGEL_UNGEMESSEN:
                _rahmen(px, b, h, x - RIEGEL_B / 2, ya, x + RIEGEL_B / 2, yb, farbe, 2)
            else:
                _rechteck(px, b, h, x - RIEGEL_B / 2, ya, x + RIEGEL_B / 2, yb, farbe)
    return px, b, h


# --------------------------------------------------------------------------------------
# Der Lauf
# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("ziel", nargs="?", default=str(ZIEL_VORGABE))
    p.add_argument("--ohne-blender", action="store_true",
                   help="den Multipass nicht fahren (Stufe als nicht gemessen führen)")
    p.add_argument("--aufloesung", type=int, default=AUFLOESUNG)
    p.add_argument("--samples", type=int, default=SAMPLES)
    a = p.parse_args(argv)

    ziel = Path(a.ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = ziel / "_arbeit"
    if arbeit.exists():
        shutil.rmtree(arbeit)
    arbeit.mkdir()
    geschrieben: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, b, h) -> Path:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)
        return pfad

    def kopie(quelle, stamm: str) -> Path:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        shutil.copyfile(quelle, pfad)
        geschrieben.append(pfad)
        return pfad

    blender_da, blender_text = blender_verfuegbar()
    blender_fahren = blender_da and not a.ohne_blender
    if not blender_fahren:
        print("MULTIPASS NICHT GEFAHREN — " + ("--ohne-blender" if a.ohne_blender else blender_text))
    gewichte = render.modellwurzel_lage(render.VORGABE_BACKBONE)
    print(f"Gewichte für {render.VORGABE_BACKBONE!r}: "
          f"{'vorhanden' if gewichte['existiert'] else 'NICHT vorhanden'} ({gewichte['wurzel']})")

    ifc = arbeit / "bau.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True, mit_raeumen=True)

    ergebnis = fahre_kette(ifc, arbeit, blender_fahren=blender_fahren,
                           aufloesung=a.aufloesung, samples=a.samples)
    knoten = ergebnis["knoten"]
    for kid in ergebnis["reihenfolge"]:
        e = knoten[kid]
        print(f"  {kid:10s} {e['status']:15s} {e['dauer_s']:8.2f} s  "
              f"{(e['error'] or e['grund'] or '')[:90]}")
    print(f"torch geladen: {'torch' in sys.modules}")

    geo = knoten[kette.KNOTEN_GEOMETRIE]
    if geo["status"] != kette.STATUS_OK:
        print(f"Geometrie-Knoten nicht ok: {geo['error']}", file=sys.stderr)
        return 1
    geometrie = geo["ausgaben"]
    box = glbbox.bauwerksbox(geometrie["glb_path"], up_axis=geometrie["up_axis"])
    mp = knoten[kette.KNOTEN_MULTIPASS]
    bericht = mp["ausgaben"] if mp["status"] == kette.STATUS_OK else None
    lagen = {kid: lage(kid, knoten[kid], gewichte_da=gewichte["existiert"])
             for kid in ergebnis["reihenfolge"]}
    dauern = {kid: knoten[kid]["dauer_s"] for kid in ergebnis["reihenfolge"]}

    # --- Kacheln -------------------------------------------------------------------
    kacheln: dict = {}
    neben: dict = {}
    k_ifc, info_ifc = kachel_ifc(geometrie)
    k_glb, info_glb = kachel_glb(geometrie, box)
    kacheln["ifc"], kacheln[kette.KNOTEN_GEOMETRIE] = k_ifc, k_glb
    if bericht is not None:
        kacheln[kette.KNOTEN_MULTIPASS] = kachel_aus_png(bericht["beauty_png"])
        neben[kette.KNOTEN_MULTIPASS] = [kachel_aus_grau_png(bericht["depth_png"], SUB),
                                         _skaliere(*bildlesen.lies_png_farben(
                                             bericht["material_id_png"]), SUB, SUB)]
    else:
        kacheln[kette.KNOTEN_MULTIPASS] = kachel_marke()
    rd = knoten[kette.KNOTEN_RENDER]
    bild_png = (rd["ausgaben"] or {}).get("bild_png") if rd["status"] == kette.STATUS_OK else None
    kacheln[kette.KNOTEN_RENDER] = kachel_aus_png(bild_png) if bild_png else kachel_marke()
    kacheln[kette.KNOTEN_QA], info_qa = kachel_qa(bericht, knoten[kette.KNOTEN_QA])

    px, b, h = zeichne_kette(kacheln, neben, lagen, dauern)
    schreibe("kette_ifc-glb-multipass-render-qa_" + "_".join(
        f"{kid}-{lagen[kid]}-{_fmt(round(dauern[kid], 1))}s" for kid in ergebnis["reihenfolge"]),
        px, b, h)

    # --- Riegel --------------------------------------------------------------------
    lauf = riegel_dieser_lauf(geometrie, bericht)
    # Die Gegenprobe «Bildvollständigkeit» braucht eine echte PNG dieses Laufs: die
    # Tiefenkarte, wenn Blender lief — sonst die IFC-Kachel, hier in den Arbeitsordner
    # geschrieben, damit sie es gibt, bevor sie abgeschnitten wird.
    if bericht is not None:
        png_fuer_bilder = Path(bericht["depth_png"])
    else:
        png_fuer_bilder = bildschreiben.schreibe_farb_png(
            arbeit / "ifc_kachel.png", k_ifc, KACHEL, KACHEL)
    gegen = riegel_gegenprobe(geometrie, box, bericht, png_fuer_bilder, arbeit)
    thumbs = [_skaliere(kacheln[name], KACHEL, KACHEL, THUMB, THUMB) for name in REIHE]
    px, b, h = zeichne_riegel(thumbs, lauf, gegen)
    schreibe("riegel_lauf_" + "_".join(f"{n}-{lauf[n]['lage']}" for n in RIEGEL_NAMEN)
             + "__gegenprobe_" + "_".join(f"{n}-{gegen[n]['lage']}" for n in RIEGEL_NAMEN)
             + f"_dachkamera-aus-{gegen['dach']['quelle']}", px, b, h)

    # --- Einzelbilder --------------------------------------------------------------
    schreibe(f"stufe-ifc_grundriss_raeume-{info_ifc['n_gezeichnet']}-von-{info_ifc['n_raeume']}"
             f"_elemente-{info_ifc['n_elements']}_dreiecke-{info_ifc['n_triangles']}",
             k_ifc, KACHEL, KACHEL)
    schreibe(f"stufe-glb_grundriss_knoten-{info_glb['n_knoten']}_bauwerk-{info_glb['n_bauwerk']}"
             f"_gelaende-{info_glb['n_gelaende']}_schrumpfung-{_fmt(info_glb['schrumpfung'])}",
             k_glb, KACHEL, KACHEL)
    if bericht is not None:
        kam = bericht.get("kamera") or {}
        kopie(bericht["beauty_png"],
              f"stufe-multipass_beauty_{bericht.get('aufloesung')}px_{bericht.get('samples')}"
              f"samples_kamera-{kam.get('kuerzel')}_fuellgrad-{_fmt(kam.get('fuellgrad'))}")
        kopie(bericht["depth_png"], "stufe-multipass_tiefe-normalisiert_nah-hell")
        kopie(bericht["material_id_png"],
              f"stufe-multipass_material-id_{bericht.get('n_materialien')}-materialien")
    if bild_png:
        kopie(bild_png, f"stufe-render_{rd['ausgaben'].get('backbone')}_"
                        f"{_fmt(rd['ausgaben'].get('dauer_s'))}s")
    schreibe(f"stufe-qa_soll-silhouette_{_fmt(info_qa['n_soll'])}-geometriepixel"
             f"_bestanden-{_fmt(info_qa['bestanden'])}_score-{_fmt(info_qa['score'])}",
             kacheln[kette.KNOTEN_QA], KACHEL, KACHEL)

    # --- Befunde auf die Konsole ----------------------------------------------------
    print("RIEGEL dieser Lauf:  " + ", ".join(
        f"{n}={lauf[n]['lage']}({_fmt(lauf[n]['wert'])})" for n in RIEGEL_NAMEN))
    print("RIEGEL Gegenprobe:   " + ", ".join(
        f"{n}={gegen[n]['lage']}({_fmt(gegen[n]['wert'])})" for n in RIEGEL_NAMEN))
    if bericht is not None:
        prod = abholer._rahmung_vor_dem_render(bericht)
        print(f"BEFUND Produktivriegel _rahmung_vor_dem_render(bericht): abbruch={prod['abbruch']}, "
              f"wirksame_bildbreite={_fmt(prod['wirksame_bildbreite'])} — er nimmt "
              f"bericht['bbox'] (die Szene) als gerahmte Box, obwohl die Kamera die "
              f"Bauwerksbox rahmte (fuellgrad={_fmt((bericht.get('kamera') or {}).get('fuellgrad'))}).")

    for pfad in geschrieben:
        print(pfad)

    widersprueche = [f"Torwächter lehnt die gesunde Geometrie ab: {lauf['torwaechter']['wert']}"] \
        if lauf["torwaechter"]["lage"] != RIEGEL_OFFEN else []
    erwartet = {"torwaechter": RIEGEL_GEGRIFFEN, "massstab": RIEGEL_GEMELDET,
                "rahmung": RIEGEL_GEGRIFFEN, "dach": RIEGEL_GEGRIFFEN, "bilder": RIEGEL_GEGRIFFEN}
    widersprueche += [f"Gegenprobe {n}: {gegen[n]['lage']}, erwartet {soll}"
                      for n, soll in erwartet.items() if gegen[n]["lage"] != soll]
    if widersprueche:
        print("BEHAUPTUNG WIDERLEGT — Befund gegen einen Riegel, nicht gegen die Umgebung:\n  "
              + "\n  ".join(widersprueche), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
