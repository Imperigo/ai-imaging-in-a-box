#!/usr/bin/env python3
"""BEWEIS 11 — Die automatische Kamerasetzung, Teil 3: ``MODUS_SHIFT`` hält senkrechte
Gebäudekanten senkrecht, ``MODUS_GEKIPPT`` lässt sie zusammenlaufen — und der Shift,
den der normgerechte Modus dafür braucht, bleibt über alle Gebäudehöhen weit unter dem,
was ein wirkliches Shift-Objektiv leistet (``MAX_SHIFT_MM``).

Was bewiesen wird
-----------------
1. **Zwei Modi, dieselbe Fassade.** ``kameras.kamerasatz`` wird zweimal auf dieselbe
   Hüllbox gerechnet, einmal mit ``modus=MODUS_GEKIPPT`` und einmal mit
   ``modus=MODUS_SHIFT``. Standort und Abstand sind in beiden Fällen gleich; der
   Unterschied liegt allein darin, WIE gerahmt wird: Gekippt zeigt die Achse zum
   angehobenen Blickziel (``neigung_grad`` ≈ 3°), geshiftet bleibt die Achse waagrecht
   (``neigung_grad`` = 0) und der Rahmen wird um ``shift_mm`` nach oben verschoben.
2. **Die Projektion ist gerechnet, nicht gemalt.** Jede Hüllbox-Ecke wird mit der
   Kamerabasis aus ``kameras._kamerabasis`` und dem Bildwinkel aus
   ``kameras.bildwinkel`` in die Bildebene projiziert — Zeile für Zeile dieselbe
   Rechnung wie in ``kameras.flaechenanteil`` (perspektivische Division, Shift als
   Rahmenversatz). Die Abweichung jeder senkrechten Kante von der Bildsenkrechten wird
   aus den projizierten Endpunkten gemessen und steht im Dateinamen.
3. **Der Shift bleibt innerhalb des Machbaren.** Für acht Gebäudehöhen von 3 bis 100 m
   (gleicher Grundriss) rechnet ``kamerasatz`` im Shift-Modus alle zwölf Richtungen;
   der nötige ``shift_mm`` wird gegen ``MAX_SHIFT_MM`` (12 mm, Bildkreis eines
   Kleinbild-Shift-Objektivs) gezeichnet. Er wächst NICHT mit der Höhe, weil der
   Deckungsgrad die Kamera bei hohen Bauten proportional weiter wegstellt — Shift ist
   ``brennweite · Δh / Abstand``, und beide Grössen wachsen mit der Höhe.

Die Geometrie ist synthetisch und wird hier erzeugt (Regel 3): ``make_test_ifc`` mit
``hochbau=True`` und Geländeplatte, über ``seams.ifc_zu_glb`` (Subprozess im
``.venv-ifc``, **kein Blender**) zur glb; ``glbbox.bauwerksbox`` liefert die Hüllbox,
die Geländeplatte den ``gelaende_z``. Für die Höhenreihe wird derselbe Grundriss mit
gesetzter Höhe als Hüllbox gerechnet. Kamera-Vorgaben: 35 mm Kleinbild, 16:9,
Deckungsgrad 0.70.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Die Bedeutung liegt in Anordnung, Farbe und
Dateiname; jede Zahl im Dateinamen stammt aus dem Rückgabewert von ``kamerasatz``
oder aus der Projektion, nicht aus einer Vorstellung.

``01_paar-n_…`` bis ``12_paar-nNW_…png`` — je Richtung ein Bildpaar, LINKS gekippt,
RECHTS geshiftet, dieselbe Hüllbox, derselbe Standort.

    Farbband oben     rot = MODUS_GEKIPPT, grün = MODUS_SHIFT
    Weisses Feld      der Bildrahmen 16:9 — was Blender rendern würde
    Hellblaue Fläche  die konvexe Hülle der acht projizierten Ecken
    Dunkle Linien     die zwölf Kanten der Hüllbox; die vier senkrechten dicker
    Graue Senkrechte  das LOT: vom Fuss jeder senkrechten Kante gerade nach oben bis zum
                      Rahmenrand — die Bildsenkrechte, an der die Kante gemessen wird
    Rote Verlängerung die senkrechte Kante über ihre Oberkante hinaus bis zum Rahmenrand
                      verlängert; der rot gefüllte Keil zwischen Lot und Verlängerung
                      IST die Abweichung. Links laufen die Verlängerungen aufeinander
                      zu (sie treffen sich weit über dem Bild im Fluchtpunkt der
                      Senkrechten); rechts decken sie das Lot — kein Keil.
    Dünne graue Linie der Horizont: gekippt liegt er unter der Bildmitte, weil die
                      Achse nach oben zeigt; geshiftet liegt er ebenfalls unter der
                      Mitte, aber weil der RAHMEN verschoben wurde — die Achse selbst
                      trifft ihn
    Zwei Lupen unten  je Rahmen die Oberkanten der äussersten linken und rechten
                      senkrechten Kante, sechsfach vergrössert, aus derselben Projektion
                      gezeichnet (kein Bildausschnitt, dieselbe Rechnung bei anderem
                      Massstab). Der kleine Rahmen im Hauptbild zeigt, wo die Lupe
                      sitzt. Links klafft zwischen Lot und Kante ein Spalt, rechts nicht.

Im Dateinamen: Kürzel, ``neigung`` in Grad (gekippt), ``shift`` in Millimetern
(geshiftet), ``lot-gekippt`` und ``lot-shift`` — die grösste Abweichung einer
senkrechten Kante von der Bildsenkrechten in Grad, je Modus, aus der Projektion
gemessen. ``lot-shift-0.000`` ist die Aussage dieses Beweises.

``13_uebersicht_…png`` — die zwölf Paare als Tafel (3 Spalten, 4 Zeilen, in der
Reihenfolge von ``RICHTUNGSFOLGE``), ohne Lupen. Der Dateiname trägt die Spanne der
Lot-Abweichung über alle zwölf Richtungen je Modus.

``14_shift-je-hoehe_…png`` — Höhenreihe. Waagrecht die Gebäudehöhe (0 bis 105 m,
Markierung alle 10 m), senkrecht der nötige Shift in Millimetern (−2 bis 14, Linie
alle 2 mm; die dunkle Waagrechte ist die Nulllinie). Die ROTE waagrechte Linie ist
``MAX_SHIFT_MM``. Beim 3-m-Bau ist der Shift NEGATIV (Rahmen nach unten): Dort holt
``ZIEL_HOECHSTANTEIL`` das Blickziel unter die Augenhöhe, und die Kamera sähe gekippt
leicht nach unten. Je Höhe ein grüner
Balken von der kleinsten zur grössten der zwölf Richtungen, die zwölf Werte als
Punkte. Alle Balken liegen unten am Boden des Diagramms, weit unter der roten Linie;
sie werden mit der Höhe nicht länger und nicht höher. Im Dateinamen: Spanne der
Höhen, Spanne des Shifts (``minus`` steht für das Vorzeichen), die Grenze, und wie viele der 96 Kameras die Grenze
überschreiten (``ueber-grenze-0``).

``15_abstand-und-neigung-je-hoehe_…png`` — dieselbe Höhenreihe, zwei Felder.
LINKS: Abstand der Kamera in Metern (0 bis zum Maximum, Linie alle 50 m) — er wächst
linear mit der Höhe; das ist der Grund, warum der Shift es nicht tut. RECHTS: Neigung
im gekippten Modus in Grad (−1 bis 6, Linie je Grad, Nulllinie dunkel) — die Achse, die der Shift-Modus
waagrecht hält. Auch sie bleibt über alle Höhen nahezu konstant: dieselbe Geometrie,
einmal als Winkel, einmal als Verschiebung.

Was hier NICHT bewiesen wird
----------------------------
Dass Blender die Kamera so setzt, wie ``kamerasatz`` sie rechnet, und dass die
gerenderten Kanten wirklich senkrecht stehen. Das hat ``auf-33`` am Gerät gemessen
(0,47°–0,98° gekippt gegen 0,004°–0,016° geshiftet); dieses Skript ruft **kein**
Blender auf und braucht keine GPU. Es zeigt die Rechnung, die Blender nachbildet.

    python tools/beweis/11_kamera_shift_gegen_kippen.py [zielordner]
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, glbbox, kameras, seams  # noqa: E402
from aiimaging.maske import ist_gelaende  # noqa: E402

import make_test_ifc  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "11_kamera_shift_gegen_kippen"

#: Die Höhen der Höhenreihe in Metern. Von der Gartenmauer bis zum Hochhaus; der
#: Grundriss bleibt der des Hochbaus aus ``make_test_ifc``.
HOEHEN_M = (3.0, 6.0, 10.0, 15.0, 25.0, 40.0, 60.0, 100.0)

# Farben — Leinwand und Rahmen wie in Beweis 09, damit die Bilder nebeneinander lesbar
# bleiben. Neu sind die beiden Modusfarben und das Lot.
FARBE_LEINWAND = (245, 245, 245)
FARBE_RAHMEN = (255, 255, 255)
FARBE_RAHMENRAND = (120, 120, 120)
FARBE_HORIZONT = (170, 170, 170)
FARBE_HUELLE = (200, 220, 240)
FARBE_KANTE = (50, 60, 80)
FARBE_LOT = (150, 150, 150)
FARBE_ABWEICHUNG = (220, 60, 40)
FARBE_GEKIPPT = (200, 60, 40)
FARBE_SHIFT = (50, 150, 80)
FARBE_LUPE = (90, 90, 200)
FARBE_GITTER = (215, 215, 215)
FARBE_ACHSE = (60, 60, 60)
FARBE_GRENZE = (220, 40, 40)
FARBE_BALKEN = (50, 150, 80)
FARBE_PUNKT = (20, 90, 40)
FARBE_ABSTAND = (70, 110, 160)

RAHMEN_B, RAHMEN_H = 720, 405
LUPE_PX = 220
LUPE_FAKTOR = 6.0
BAND_PX = 10
FUGE_PX = 20
KLEIN_B, KLEIN_H = 320, 180


# --------------------------------------------------------------------------------------
# Rasterizer — dieselben drei Grundformen wie in Beweis 09. Das Projekt hat keinen
# (Regel 1: jede Bibliothek ist eine Lizenzentscheidung).
# --------------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_LEINWAND) -> list:
    return [hg] * (breite * hoehe)


def _punkt(px, breite, hoehe, x, y, farbe) -> None:
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < breite and 0 <= yi < hoehe:
        px[yi * breite + xi] = farbe


def _scheibe(px, breite, hoehe, x, y, radius: float, farbe) -> None:
    r2 = radius * radius
    for yi in range(int(y - radius) - 1, int(y + radius) + 2):
        for xi in range(int(x - radius) - 1, int(x + radius) + 2):
            if (xi - x) ** 2 + (yi - y) ** 2 <= r2:
                _punkt(px, breite, hoehe, xi, yi, farbe)


def _strecke(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: float = 1.5) -> None:
    """Strecke in beliebiger Richtung: Scheiben in halber Dicke entlang der Strecke."""
    laenge = math.hypot(x1 - x0, y1 - y0)
    schritte = max(1, int(laenge / max(0.5, dicke * 0.5)))
    for i in range(schritte + 1):
        t = i / schritte
        _scheibe(px, breite, hoehe, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                 dicke / 2.0, farbe)


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: int = 1) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _konvexe_huelle(punkte) -> list:
    """Andrews Monotone Chain — dieselbe Hülle, die ``kameras.flaechenanteil`` misst."""
    p = sorted(set(punkte))
    if len(p) < 3:
        return p

    def halb(pp):
        stapel = []
        for q in pp:
            while len(stapel) >= 2:
                (ax, ay), (bx, by) = stapel[-2], stapel[-1]
                if (bx - ax) * (q[1] - ay) - (by - ay) * (q[0] - ax) > 0:
                    break
                stapel.pop()
            stapel.append(q)
        return stapel[:-1]

    return halb(p) + halb(list(reversed(p)))


def _polygon_fuellen(px, breite, hoehe, ecken, farbe, anteil: float = 1.0) -> None:
    """Scanline-Füllung eines einfachen Polygons; ``anteil`` < 1 mischt mit dem Grund."""
    if len(ecken) < 3:
        return
    y_min = max(0, int(min(y for _, y in ecken)))
    y_max = min(hoehe - 1, int(max(y for _, y in ecken)) + 1)
    n = len(ecken)
    for y in range(y_min, y_max + 1):
        ys = y + 0.5
        schnitte = []
        for i in range(n):
            (x0, y0), (x1, y1) = ecken[i], ecken[(i + 1) % n]
            if (y0 <= ys < y1) or (y1 <= ys < y0):
                schnitte.append(x0 + (ys - y0) * (x1 - x0) / (y1 - y0))
        schnitte.sort()
        for a, b in zip(schnitte[0::2], schnitte[1::2]):
            if anteil >= 1.0:
                _rechteck(px, breite, hoehe, a, y, b, y + 1, farbe)
                continue
            for x in range(max(0, int(round(a))), min(breite, int(round(b)))):
                alt = px[y * breite + x]
                px[y * breite + x] = tuple(int(round(alt[i] + (farbe[i] - alt[i]) * anteil))
                                           for i in range(3))


def _einfuegen(px, breite, quelle, qb, qh, x0: int, y0: int) -> None:
    """Ein fertiges Bild an eine Stelle eines grösseren kopieren — Pixel für Pixel."""
    for y in range(qh):
        px[(y0 + y) * breite + x0:(y0 + y) * breite + x0 + qb] = quelle[y * qb:(y + 1) * qb]


# --------------------------------------------------------------------------------------
# Schritt 1 — Geometrie im Repo erzeugen
# --------------------------------------------------------------------------------------

def baue_geometrie(arbeit: Path) -> dict:
    """Hochbau mit Geländeplatte → glb → Bauwerks-Hüllbox und Geländestand.

    Derselbe Weg wie in Beweis 09: ``hochbau=True``, weil an einem 15-m-Bau die
    Bildwinkelrechnung wirklich arbeitet und nicht der Mindestabstand.
    """
    ifc = arbeit / "hochbau.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True, hochbau=True)
    report = seams.ifc_zu_glb(str(ifc), str(arbeit / "hochbau.glb"))
    if report.get("status") != "ok":
        raise SystemExit(f"IFC→glb fehlgeschlagen: {report.get('error')}")

    js = glbbox.lies_gltf_json(report["glb_path"])
    gelesen = glbbox.knotenboxen(js)
    if gelesen["ohne_grenzen"]:
        raise SystemExit(f"{len(gelesen['ohne_grenzen'])} Knoten ohne min/max — siehe glbbox.")
    knoten_welt = [(name, *glbbox.nach_welt(lo, hi, up_axis=report["up_axis"]))
                   for name, lo, hi in gelesen["knoten"]]

    bau = glbbox.bauwerksbox(report["glb_path"], up_axis=report["up_axis"])
    if bau["bbox_bauwerk"] is None:
        raise SystemExit(f"Keine Bauwerks-Hüllbox feststellbar: {bau['note']}")
    gelaende = [hi[2] for name, lo, hi in knoten_welt if ist_gelaende(name)]
    if not gelaende:
        raise SystemExit("Keine Geländeplatte in der glb — gelaende_z nicht messbar.")
    return {"bbox_bauwerk": bau["bbox_bauwerk"], "gelaende_z": max(gelaende)}


# --------------------------------------------------------------------------------------
# Schritt 2 — die Projektion, gerechnet wie in kameras.flaechenanteil
# --------------------------------------------------------------------------------------

#: Die zwölf Kanten des Quaders als Paare von Eckenindizes (Index = x·4 + y·2 + z).
KANTEN = tuple((a, b) for a in range(8) for b in range(a + 1, 8)
               if bin(a ^ b).count("1") == 1)


def projiziere(kam: dict, bbox) -> dict:
    """Acht Ecken und der Horizont in Rahmenkoordinaten (-0.5 … +0.5 = sichtbar).

    Tiefe entlang der Blickachse, seitliche Anteile durch die Tiefe, Shift als
    Rahmenversatz — Zeile für Zeile ``kameras.flaechenanteil``. Der Horizont ist die
    Projektion eines sehr fernen Punkts in waagrechter Blickrichtung; so gilt dieselbe
    Rechnung für beide Modi, und die Zeichnung nimmt nicht vorweg, wo er liegt.
    """
    basis = kameras._kamerabasis(kam["auge"], kam["blick_auf"])
    if basis is None:
        raise SystemExit(f"Kamerabasis entartet bei {kam['kuerzel']}")
    vorwaerts, rechts, oben = basis
    hfov, vfov = kameras.bildwinkel(kam["brennweite_mm"],
                                    seitenverhaeltnis=kam["seitenverhaeltnis"])
    grenze_h, grenze_v = math.tan(hfov / 2.0), math.tan(vfov / 2.0)
    versatz = kam["shift_mm"] / kam["brennweite_mm"]

    def bildpunkt(p):
        v = (p[0] - kam["auge"][0], p[1] - kam["auge"][1], p[2] - kam["auge"][2])
        tiefe = kameras._punkt(v, vorwaerts)
        if tiefe < kameras.MIN_TIEFE_M:
            return None
        return (kameras._punkt(v, rechts) / tiefe / grenze_h / 2.0,
                (kameras._punkt(v, oben) / tiefe - versatz) / grenze_v / 2.0)

    (ux, uy, uz), (ox, oy, oz) = bbox
    ecken = [bildpunkt((x, y, z)) for x in (ux, ox) for y in (uy, oy) for z in (uz, oz)]

    waag = kameras._normiert((vorwaerts[0], vorwaerts[1], 0.0))
    fern = bildpunkt((kam["auge"][0] + waag[0] * 1e6, kam["auge"][1] + waag[1] * 1e6,
                      kam["auge"][2]))
    return {"ecken": ecken, "horizont": fern[1] if fern else None}


def lot_abweichungen(ecken, seitenverhaeltnis: float) -> list:
    """Je senkrechter Kante: ``(fuss, kopf, abweichung_grad)``.

    Die Rahmenkoordinaten sind auf Breite und Höhe getrennt normiert; für den Winkel
    im BILD muss die Breite mit dem Seitenverhältnis zurückgewichtet werden — sonst
    misst man den Winkel in einem quadratisch verzerrten Rahmen.
    """
    kanten = []
    for a, b in KANTEN:
        if (a ^ b) != 1 or ecken[a] is None or ecken[b] is None:
            continue
        fuss, kopf = (ecken[a], ecken[b]) if ecken[a][1] <= ecken[b][1] else (ecken[b], ecken[a])
        du = (kopf[0] - fuss[0]) * seitenverhaeltnis
        dw = kopf[1] - fuss[1]
        grad = math.degrees(math.atan2(abs(du), abs(dw))) if abs(dw) > 1e-12 else 90.0
        kanten.append((fuss, kopf, grad))
    return kanten


# --------------------------------------------------------------------------------------
# Schritt 3 — ein Rahmen je Modus, mit Lot, Keil und Lupen
# --------------------------------------------------------------------------------------

def _zeichne_szene(px, breite, hoehe, nach_px, proj: dict, kanten: list, *,
                   mit_huelle: bool, kanten_dicke: float) -> None:
    """Alles, was in Hauptbild und Lupe gleich ist — nur der Massstab ist ein anderer."""
    ecken = proj["ecken"]
    if proj["horizont"] is not None:
        hx0, hy = nach_px(-0.5, proj["horizont"])
        hx1, _ = nach_px(0.5, proj["horizont"])
        _strecke(px, breite, hoehe, hx0, hy, hx1, hy, FARBE_HORIZONT, 1.0)
    if mit_huelle:
        sichtbar = [nach_px(*e) for e in ecken if e is not None]
        _polygon_fuellen(px, breite, hoehe, _konvexe_huelle(sichtbar), FARBE_HUELLE)

    # Lot und Verlängerung ZUERST, damit die Kanten obenauf liegen. Beide enden am
    # oberen Rahmenrand (w = 0.5); die Verlängerung folgt der Kantenrichtung.
    for fuss, kopf, _ in kanten:
        dw = kopf[1] - fuss[1]
        if dw <= 1e-12:
            continue
        t = (0.5 - fuss[1]) / dw
        ende = (fuss[0] + (kopf[0] - fuss[0]) * t, 0.5)
        _polygon_fuellen(px, breite, hoehe,
                         [nach_px(*fuss), nach_px(fuss[0], 0.5), nach_px(*ende)],
                         FARBE_ABWEICHUNG, anteil=0.45)
        _strecke(px, breite, hoehe, *nach_px(*fuss), *nach_px(fuss[0], 0.5),
                 FARBE_LOT, 1.2)
        _strecke(px, breite, hoehe, *nach_px(*kopf), *nach_px(*ende),
                 FARBE_ABWEICHUNG, 1.2)

    for a, b in KANTEN:
        if ecken[a] is None or ecken[b] is None:
            continue
        senkrecht = (a ^ b) == 1
        _strecke(px, breite, hoehe, *nach_px(*ecken[a]), *nach_px(*ecken[b]),
                 FARBE_KANTE, kanten_dicke * (1.5 if senkrecht else 1.0))


def zeichne_rahmen(kam: dict, bbox, *, breite: int = RAHMEN_B, hoehe: int = RAHMEN_H,
                   mit_lupen: bool = True) -> dict:
    """Ein Rahmen mit Modusband, darunter zwei Lupen — und die gemessenen Abweichungen."""
    proj = projiziere(kam, bbox)
    kanten = lot_abweichungen(proj["ecken"], kam["seitenverhaeltnis"])
    if not kanten:
        raise SystemExit(f"{kam['kuerzel']}: keine senkrechte Kante sichtbar — kein Beweis.")
    abweichung = max(grad for _, _, grad in kanten)

    gesamt_h = BAND_PX + hoehe + (FUGE_PX // 2 + LUPE_PX if mit_lupen else 0)
    px = _neues_bild(breite, gesamt_h)
    _rechteck(px, breite, gesamt_h, 0, 0, breite, BAND_PX,
              FARBE_SHIFT if kam["modus"] == kameras.MODUS_SHIFT else FARBE_GEKIPPT)
    oben_px = BAND_PX

    def nach_px(u, w):
        return ((u + 0.5) * breite, oben_px + (0.5 - w) * hoehe)

    _rechteck(px, breite, gesamt_h, 0, oben_px, breite, oben_px + hoehe, FARBE_RAHMEN)
    _zeichne_szene(px, breite, gesamt_h, nach_px, proj, kanten,
                   mit_huelle=True, kanten_dicke=1.4)
    _rahmen(px, breite, gesamt_h, 0, oben_px, breite, oben_px + hoehe, FARBE_RAHMENRAND, 1)

    if mit_lupen:
        # Die äusserste linke und rechte Kante — dort ist die Abweichung am grössten,
        # weil der Fluchtpunkt über der Bildmitte liegt. Vergrössert wird um den KOPF
        # der Kante: Am Fuss decken sich Lot und Kante per Konstruktion.
        links = min(kanten, key=lambda k: k[1][0])
        rechts = max(kanten, key=lambda k: k[1][0])
        for i, (fuss, kopf, _) in enumerate((links, rechts)):
            lx0 = (breite - 2 * LUPE_PX - FUGE_PX) // 2 + i * (LUPE_PX + FUGE_PX)
            ly0 = oben_px + hoehe + FUGE_PX // 2
            spanne_u = LUPE_PX / (breite * LUPE_FAKTOR)
            spanne_w = LUPE_PX / (hoehe * LUPE_FAKTOR)

            def lupe_px(u, w, u0=kopf[0], w0=kopf[1], x0=lx0, y0=ly0):
                return (x0 + LUPE_PX / 2.0 + (u - u0) * breite * LUPE_FAKTOR,
                        y0 + LUPE_PX / 2.0 - (w - w0) * hoehe * LUPE_FAKTOR)

            # Die Lupe zeichnet nur in ihr eigenes Fenster: ein eigenes Bild, das
            # danach eingefügt wird. So bleibt nichts über den Rand hinaus stehen.
            lp = _neues_bild(LUPE_PX, LUPE_PX, FARBE_RAHMEN)

            def lupe_lokal(u, w, f=lupe_px, x0=lx0, y0=ly0):
                x, y = f(u, w)
                return (x - x0, y - y0)

            _zeichne_szene(lp, LUPE_PX, LUPE_PX, lupe_lokal, proj, kanten,
                           mit_huelle=False, kanten_dicke=2.0)
            _rahmen(lp, LUPE_PX, LUPE_PX, 0, 0, LUPE_PX, LUPE_PX, FARBE_LUPE, 2)
            _einfuegen(px, breite, lp, LUPE_PX, LUPE_PX, lx0, ly0)
            # Wo die Lupe im Hauptbild sitzt.
            mx0, my0 = nach_px(kopf[0] - spanne_u / 2.0, kopf[1] + spanne_w / 2.0)
            mx1, my1 = nach_px(kopf[0] + spanne_u / 2.0, kopf[1] - spanne_w / 2.0)
            _rahmen(px, breite, gesamt_h, mx0, my0, mx1, my1, FARBE_LUPE, 1)

    return {"px": px, "breite": breite, "hoehe": gesamt_h, "abweichung_grad": abweichung,
            "kanten": kanten}


def zeichne_paar(links: dict, rechts: dict):
    """Zwei Rahmen nebeneinander: gekippt links, geshiftet rechts."""
    breite = links["breite"] + rechts["breite"] + 3 * FUGE_PX
    hoehe = max(links["hoehe"], rechts["hoehe"]) + 2 * FUGE_PX
    px = _neues_bild(breite, hoehe)
    _einfuegen(px, breite, links["px"], links["breite"], links["hoehe"], FUGE_PX, FUGE_PX)
    _einfuegen(px, breite, rechts["px"], rechts["breite"], rechts["hoehe"],
               2 * FUGE_PX + links["breite"], FUGE_PX)
    return px, breite, hoehe


def zeichne_uebersicht(paare: list, *, spalten: int = 3, fuge: int = 10):
    """Zwölf kleine Paare als Tafel."""
    pb = 2 * KLEIN_B + fuge // 2
    ph = BAND_PX + KLEIN_H
    zeilen = math.ceil(len(paare) / spalten)
    breite = spalten * pb + (spalten + 1) * fuge
    hoehe = zeilen * ph + (zeilen + 1) * fuge
    px = _neues_bild(breite, hoehe, (225, 225, 225))
    for i, (l, r) in enumerate(paare):
        x0 = fuge + (i % spalten) * (pb + fuge)
        y0 = fuge + (i // spalten) * (ph + fuge)
        _einfuegen(px, breite, l["px"], l["breite"], l["hoehe"], x0, y0)
        _einfuegen(px, breite, r["px"], r["breite"], r["hoehe"], x0 + KLEIN_B + fuge // 2, y0)
    return px, breite, hoehe


# --------------------------------------------------------------------------------------
# Schritt 4 — die Höhenreihe als Diagramm; jede Zahl aus kamerasatz im selben Lauf
# --------------------------------------------------------------------------------------

def zeichne_reihe(reihe: list, *, y_min: float, y_max: float, y_schritt: float,
                  grenze: float | None, farbe, breite: int = 1000, hoehe: int = 520,
                  rand: int = 60):
    """Balken je Höhe von min bis max über die zwölf Richtungen, dazu die zwölf Punkte.

    ``reihe`` ist eine Liste ``(hoehe_m, [werte je Richtung])``. Die x-Achse ist linear
    in der Gebäudehöhe, damit die Abstände zwischen den Balken selbst eine Aussage sind.
    ``y_min`` liegt unter null, wo Werte negativ werden können: Bei niedrigen Bauten holt
    ``ZIEL_HOECHSTANTEIL`` das Blickziel unter die Augenhöhe, die Kamera sieht leicht
    nach unten, und Shift wie Neigung wechseln das Vorzeichen. Das gehört ins Bild und
    nicht unter die Achse.
    """
    px = _neues_bild(breite, hoehe, FARBE_RAHMEN)
    x_max = max(h for h, _ in reihe) * 1.05
    plot_b, plot_h = breite - 2 * rand, hoehe - 2 * rand

    def nach_px(h, y):
        return (rand + h / x_max * plot_b,
                rand + plot_h - (y - y_min) / (y_max - y_min) * plot_h)

    # Gitter: waagrecht alle y_schritt, senkrecht alle 10 m — ohne Zahlen, aber mit
    # festem Raster, damit der Dateiname die Skala vollständig beschreibt.
    y = y_min
    while y <= y_max + 1e-9:
        x0, yy = nach_px(0, y)
        x1, _ = nach_px(x_max, y)
        _strecke(px, breite, hoehe, x0, yy, x1, yy, FARBE_GITTER, 1.0)
        y += y_schritt
    h = 0.0
    while h <= x_max:
        xx, y0 = nach_px(h, 0)
        _rechteck(px, breite, hoehe, xx - 0.5, y0, xx + 0.5, y0 + 8, FARBE_ACHSE)
        h += 10.0
    if grenze is not None:
        x0, yg = nach_px(0, grenze)
        x1, _ = nach_px(x_max, grenze)
        _strecke(px, breite, hoehe, x0, yg, x1, yg, FARBE_GRENZE, 3.0)

    for h, werte in reihe:
        lo, hi = min(werte), max(werte)
        xx, y_lo = nach_px(h, lo)
        _, y_hi = nach_px(h, hi)
        _rechteck(px, breite, hoehe, xx - 7, y_hi - 1, xx + 7, y_lo + 1, farbe)
        for w in werte:
            _, yw = nach_px(h, w)
            _scheibe(px, breite, hoehe, xx, yw, 2.2, FARBE_PUNKT)

    # Die Nulllinie ist die Achse — nicht der untere Rand, der liegt bei y_min.
    _strecke(px, breite, hoehe, *nach_px(0, 0), *nach_px(x_max, 0), FARBE_ACHSE, 2.0)
    _strecke(px, breite, hoehe, *nach_px(0, y_min), *nach_px(0, y_max), FARBE_ACHSE, 2.0)
    return px, breite, hoehe


def _zahl(x: float, stellen: int = 2) -> str:
    """Zahl für den Dateinamen: ``-0.36`` würde nach ``shift-`` zu ``--0.36``."""
    return f"{x:.{stellen}f}".replace("-", "minus")


def zeichne_nebeneinander(a, b, fuge: int = FUGE_PX):
    (pa, ba, ha), (pb, bb, hb) = a, b
    breite, hoehe = ba + bb + 3 * fuge, max(ha, hb) + 2 * fuge
    px = _neues_bild(breite, hoehe)
    _einfuegen(px, breite, pa, ba, ha, fuge, fuge)
    _einfuegen(px, breite, pb, bb, hb, 2 * fuge + ba, fuge)
    return px, breite, hoehe


# --------------------------------------------------------------------------------------

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis11_") as tmp:
        geometrie = baue_geometrie(Path(tmp))
    bbox = geometrie["bbox_bauwerk"]
    gz = geometrie["gelaende_z"]

    saetze = {m: kameras.kamerasatz(bbox, gelaende_z=gz, modus=m) for m in kameras.MODI}
    for m, s in saetze.items():
        if len(s["kameras"]) != 12:
            raise SystemExit(f"{m}: {len(s['kameras'])} Kameras statt 12 — kein Beweis.")

    # -- 01..12 die Paare --
    paare_klein = []
    spanne = {m: [] for m in kameras.MODI}
    for i, (kg, ks) in enumerate(zip(saetze[kameras.MODUS_GEKIPPT]["kameras"],
                                     saetze[kameras.MODUS_SHIFT]["kameras"])):
        if kg["kuerzel"] != ks["kuerzel"] or kg["auge"] != ks["auge"]:
            raise SystemExit(f"{kg['kuerzel']}: Standort in beiden Modi verschieden — die "
                             f"Paare wären nicht vergleichbar.")
        links = zeichne_rahmen(kg, bbox)
        rechts = zeichne_rahmen(ks, bbox)
        # Die Aussage des Modus, geprüft an der Projektion und nicht nur behauptet: Mit
        # waagrechter Achse hat eine senkrechte Weltkante keinen seitlichen Anteil.
        if rechts["abweichung_grad"] > 1e-6:
            raise SystemExit(f"{ks['kuerzel']}: Shift-Modus weicht um "
                             f"{rechts['abweichung_grad']:.4f}° vom Lot ab — Widerspruch.")
        if links["abweichung_grad"] <= rechts["abweichung_grad"]:
            raise SystemExit(f"{kg['kuerzel']}: gekippt weicht nicht stärker ab als "
                             f"geshiftet — kein Beweis.")
        spanne[kameras.MODUS_GEKIPPT].append(links["abweichung_grad"])
        spanne[kameras.MODUS_SHIFT].append(rechts["abweichung_grad"])
        px, b, h = zeichne_paar(links, rechts)
        pfad = ziel / (f"{i + 1:02d}_paar-{kg['kuerzel']}_azimut-{kg['azimut_grad']:.0f}_"
                       f"abstand-{kg['abstand_m']:.1f}m_"
                       f"neigung-{kg['neigung_grad']:.2f}grad_shift-{ks['shift_mm']:.2f}mm_"
                       f"lot-gekippt-{links['abweichung_grad']:.3f}grad_"
                       f"lot-shift-{rechts['abweichung_grad']:.3f}grad.png")
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)
        paare_klein.append((zeichne_rahmen(kg, bbox, breite=KLEIN_B, hoehe=KLEIN_H,
                                           mit_lupen=False),
                            zeichne_rahmen(ks, bbox, breite=KLEIN_B, hoehe=KLEIN_H,
                                           mit_lupen=False)))

    # -- 13 Übersicht --
    px, b, h = zeichne_uebersicht(paare_klein)
    g, s = spanne[kameras.MODUS_GEKIPPT], spanne[kameras.MODUS_SHIFT]
    pfad = ziel / (f"13_uebersicht_zwoelf-paare_links-gekippt-rechts-shift_"
                   f"lot-gekippt-{min(g):.3f}-bis-{max(g):.3f}grad_"
                   f"lot-shift-{min(s):.3f}-bis-{max(s):.3f}grad.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 14, 15 die Höhenreihe --
    (ux, uy, _), (ox, oy, _) = bbox
    reihe_shift, reihe_abstand, reihe_neigung = [], [], []
    ueber_grenze = 0
    for hm in HOEHEN_M:
        box = [[ux, uy, 0.0], [ox, oy, hm]]
        satz_s = kameras.kamerasatz(box, gelaende_z=0.0, modus=kameras.MODUS_SHIFT)
        satz_g = kameras.kamerasatz(box, gelaende_z=0.0, modus=kameras.MODUS_GEKIPPT)
        reihe_shift.append((hm, [k["shift_mm"] for k in satz_s["kameras"]]))
        reihe_abstand.append((hm, [k["abstand_m"] for k in satz_s["kameras"]]))
        reihe_neigung.append((hm, [k["neigung_grad"] for k in satz_g["kameras"]]))
        ueber_grenze += sum(k["shift_ueber_grenze"] for k in satz_s["kameras"])

    alle_shift = [w for _, werte in reihe_shift for w in werte]
    px, b, h = zeichne_reihe(reihe_shift, y_min=-2.0, y_max=14.0, y_schritt=2.0,
                             grenze=kameras.MAX_SHIFT_MM, farbe=FARBE_BALKEN)
    pfad = ziel / (f"14_shift-je-hoehe_{HOEHEN_M[0]:.0f}-bis-{HOEHEN_M[-1]:.0f}m_"
                   f"shift-{_zahl(min(alle_shift))}-bis-{_zahl(max(alle_shift))}mm_"
                   f"grenze-{kameras.MAX_SHIFT_MM:.0f}mm_"
                   f"ueber-grenze-{ueber_grenze}von{len(alle_shift)}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    alle_abstand = [w for _, werte in reihe_abstand for w in werte]
    alle_neigung = [w for _, werte in reihe_neigung for w in werte]
    y_abstand = math.ceil(max(alle_abstand) / 50.0) * 50.0
    px, b, h = zeichne_nebeneinander(
        zeichne_reihe(reihe_abstand, y_min=0.0, y_max=y_abstand, y_schritt=50.0,
                      grenze=None, farbe=FARBE_ABSTAND, breite=700),
        zeichne_reihe(reihe_neigung, y_min=-1.0, y_max=6.0, y_schritt=1.0,
                      grenze=None, farbe=FARBE_GEKIPPT, breite=700))
    pfad = ziel / (f"15_abstand-und-neigung-je-hoehe_{HOEHEN_M[0]:.0f}-bis-{HOEHEN_M[-1]:.0f}m_"
                   f"abstand-{min(alle_abstand):.0f}-bis-{max(alle_abstand):.0f}m_"
                   f"neigung-gekippt-{_zahl(min(alle_neigung))}-bis-{_zahl(max(alle_neigung))}grad.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
