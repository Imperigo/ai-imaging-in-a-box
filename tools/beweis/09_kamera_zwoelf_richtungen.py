#!/usr/bin/env python3
"""BEWEIS 09 — Die automatische Kamerasetzung, Teil 1: ``kameras.kamerasatz`` rechnet aus
einer Hüllbox zwölf Standpunkte um das Bauwerk, und an jedem davon liegen alle acht
Ecken der Hüllbox im Bild — gezeichnet aus den Zahlen, die die Funktion zurückgibt,
nicht aus einer Vorstellung davon.

Was bewiesen wird
-----------------
1. **Zwölf Richtungen.** ``kameras.richtungen`` liefert vier frontale und acht
   diagonale Azimute (Bias 35°); ``kamerasatz`` setzt je Richtung einen Standort auf
   Augenhöhe, ein Blickziel und einen Abstand aus dem Bildwinkel. Die Frontalen stehen
   um 10 % der Gebäudebreite seitlich versetzt (``FRONTAL_VERSATZ``) — eine exakt
   mittige Frontale ist symmetrisch und bildlich tot.
2. **Der Eckentest.** ``kameras.ecken_im_bild`` prüft je Kamera alle acht Ecken einzeln
   gegen den Bildrahmen (mit 8 % Sicherheitsrand, ``BILDRAND = 0.92``) und schiebt die
   Kamera zurück, bis sie hineinpassen (``schiebe_bis_im_bild``). Das Ergebnis steht in
   ``kamerasatz(...)["unvollstaendig"]`` — eine leere Liste heisst: alle zwölf sitzen.
3. **Der Füllgrad.** Je Kamera meldet ``kamerasatz`` ``fuellgrad`` (Anteil der
   führenden Bildlänge) und ``flaechenanteil`` (Anteil der Bildfläche, konvexe Hülle der
   acht projizierten Ecken). Beide stehen im Dateinamen des jeweiligen Bildes.

Die Geometrie ist synthetisch und wird hier erzeugt (Regel 3): ``make_test_ifc``
mit ``hochbau=True`` und Geländeplatte, über ``seams.ifc_zu_glb`` (Subprozess im
``.venv-ifc``, **kein Blender**) zur glb, und ``glbbox.bauwerksbox`` trennt die Hüllbox
des Bauwerks vom Gelände. Die Oberkante der Geländeplatte geht als ``gelaende_z`` in
``kamerasatz`` — der Parameter, ohne den die Kamera bei einem Untergeschoss im Keller
stünde. Kamera-Vorgaben: 35 mm Kleinbild, 16:9, Deckungsgrad 0.70, Shift-Modus.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Die Bedeutung liegt in Anordnung, Farbe und
Dateiname; jede Zahl im Dateinamen ist aus dem Rückgabewert von ``kamerasatz`` bzw.
``ecken_im_bild`` gelesen, nicht abgeschrieben.

``01_grundriss_…png`` — Draufsicht, massstäblich (Nord ist oben, der Massstab
steht im Dateinamen als Meter je Bildpunkt, unten links liegt ein 10-m-Balken).

    Sandfarben   die Geländeplatte
    Stahlblau    die Bauteile des Bauwerks (jede glb-Knotenbox, auf den Boden projiziert)
    Dunkler Rahmen  die Hüllbox des Bauwerks, wie ``bauwerksbox`` sie gefunden hat
    Orange       die vier frontalen Kameras (n, e, s, w)
    Teal         die acht diagonalen Kameras
    Kreis        der Standort (``auge``); die Linie mit Pfeil zeigt zum Blickziel
                 (``blick_auf``); der blasse Keil ist der horizontale Bildwinkel
                 (54° bei 35 mm Kleinbild), in der Länge auf ein Drittel des Abstands
                 gekürzt, im Öffnungswinkel echt.

Man sieht: zwölf Kreise auf einem Ring um das Bauwerk, alle Pfeile zeigen auf dessen
Mitte, die frontalen sind seitlich leicht versetzt, und die diagonalen sitzen nicht auf
45°, sondern um 35° aus der Frontalen gedreht — je zwei nahe beieinander, wie es der
Bias vorgibt. Die Abstände sind nicht gleich: Aus der Schmalseite steht die Kamera
näher als von der Breitseite, weil der Bildwinkel und nicht ein fester Radius den
Abstand setzt.

``02_kamera-n_…`` bis ``13_kamera-nNW_…png`` — je Richtung die Hüllbox, mit der
Kamera dieser Richtung in die Bildebene projiziert (dieselbe Projektion wie in
``kameras.flaechenanteil``: perspektivische Division, Shift als Rahmenversatz).

    Weisses Feld       der Bildrahmen 16:9 — was Blender rendern würde
    Hellgrauer Rahmen  der Sicherheitsrand (92 %), gegen den der Eckentest prüft
    Dünne graue Linie  der Horizont — im Shift-Modus liegt er unterhalb der Bildmitte,
                       weil der Rahmen nach oben verschoben ist
    Hellblaue Fläche   die konvexe Hülle der acht Ecken — ihr Anteil am Feld IST der
                       ``flaechenanteil`` im Dateinamen
    Dunkle Linien      die zwölf Kanten der Hüllbox; senkrechte Kanten bleiben
                       senkrecht (Shift-Modus, Neigung 0°)
    Grüne Punkte       Ecken innerhalb des Sicherheitsrands
    Rote Punkte        Ecken ausserhalb (kommen hier nicht vor — kämen sie vor, stünden
                       sie im Bild und ``faellt`` im Dateinamen)

Im Dateinamen: Kürzel, ``eckentest-passt``/``faellt``, ``fuellgrad`` (führende
Länge), ``flaeche`` (Bildfläche), ``abstand`` in Metern, ``shift`` in Millimetern.

**Ein Vorbehalt, der ins Bild gehört:** Der Füllgrad 0,70 ist erreicht, und trotzdem
nimmt das Bauwerk nur rund die halbe Bildhöhe ein. Das ist kein Widerspruch der
Zeichnung, sondern die Definition in ``abstand_aus_bildwinkel``: Der vertikale Bedarf
wird **vom Blickziel aus asymmetrisch** gemessen — die grössere der beiden Halbhöhen
(hier: vom Ziel 4,75 m über dem Fuss bis zur Traufe auf 15,25 m, also 10,5 m) wird
verdoppelt und gegen den Deckungsgrad gesetzt; ``massgebend`` ist bei allen zwölf
Kameras ``"hoehe"``. Die kleinere Hälfte unter dem Ziel bleibt leer. Damit sind
15,25 / 21,0 · 0,70 ≈ 0,51 der Bildhöhe belegt; genau das zeigt das Bild. Wer die Höhe füllen will, muss den Deckungsgrad anders definieren, nicht die
Kamera näher stellen — und diese Frage stellt der Beweis, er beantwortet sie nicht.

``14_uebersicht_…png`` — die zwölf Rahmen als Tafel 4 × 3 in der Ausgabereihenfolge
von ``RICHTUNGSFOLGE`` (erste Zeile n, e, s, w; dann die Diagonalen im Uhrzeigersinn ab
Nord). Die Zahl der Kameras mit unvollständigem Eckentest steht im Dateinamen —
``unvollstaendig-0`` ist die Aussage dieses Beweises.

Was hier NICHT bewiesen wird
----------------------------
Dass Blender die Kamera auch so setzt, wie ``kamerasatz`` sie rechnet, und dass im
gerenderten Tiefenbild das Bauwerk wirklich dort steht — das ist Teil 2 und braucht
einen Blender-Lauf. Dieses Skript ruft **kein** Blender auf und braucht keine GPU.

    python tools/beweis/09_kamera_zwoelf_richtungen.py [zielordner]
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

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "09_kamera_zwoelf_richtungen"

# Farben — dieselbe Geländeregel wie in Beweis 01, damit ein Leser beide Bilder ohne
# Umdenken nebeneinanderlegen kann.
FARBE_LEINWAND = (245, 245, 245)
FARBE_GELAENDE = (222, 206, 170)
FARBE_BAUTEIL = (70, 110, 160)
FARBE_HUELLBOX = (40, 40, 40)
FARBE_FRONTAL = (230, 120, 40)
FARBE_DIAGONAL = (40, 150, 150)
FARBE_MASSSTAB = (60, 60, 60)

FARBE_RAHMEN = (255, 255, 255)
FARBE_RAHMENRAND = (120, 120, 120)
FARBE_SICHERHEITSRAND = (205, 205, 205)
FARBE_HORIZONT = (170, 170, 170)
FARBE_HUELLE = (200, 220, 240)
FARBE_KANTE = (50, 60, 80)
FARBE_ECKE_DRIN = (50, 160, 70)
FARBE_ECKE_DRAUSSEN = (200, 50, 40)

GRUNDRISS_PX = 900
GRUNDRISS_RAND_PX = 40
RAHMEN_B, RAHMEN_H = 640, 360
RAHMEN_RAND_PX = 20


# --------------------------------------------------------------------------------------
# Rasterizer — Punkte, Strecken in beliebiger Richtung, konvexe Polygone. Das Projekt hat
# keinen (Regel 1: jede Bibliothek ist eine Lizenzentscheidung), und für diese Bilder
# genügen drei Grundformen.
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


def _ring(px, breite, hoehe, x, y, radius: float, farbe, dicke: float = 2.0) -> None:
    aussen, innen = radius * radius, (radius - dicke) ** 2
    for yi in range(int(y - radius) - 1, int(y + radius) + 2):
        for xi in range(int(x - radius) - 1, int(x + radius) + 2):
            d = (xi - x) ** 2 + (yi - y) ** 2
            if innen <= d <= aussen:
                _punkt(px, breite, hoehe, xi, yi, farbe)


def _strecke(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: float = 1.5) -> None:
    """Strecke in beliebiger Richtung: Scheiben in halber Dicke entlang der Strecke."""
    laenge = math.hypot(x1 - x0, y1 - y0)
    schritte = max(1, int(laenge / max(0.5, dicke * 0.5)))
    for i in range(schritte + 1):
        t = i / schritte
        _scheibe(px, breite, hoehe, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                 dicke / 2.0, farbe)


def _pfeil(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: float = 2.0,
           spitze: float = 9.0) -> None:
    _strecke(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke)
    w = math.atan2(y1 - y0, x1 - x0)
    for seite in (+1, -1):
        a = w + math.pi + seite * math.radians(28)
        _strecke(px, breite, hoehe, x1, y1, x1 + spitze * math.cos(a),
                 y1 + spitze * math.sin(a), farbe, dicke)


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
    """Scanline-Füllung eines einfachen Polygons. ``anteil`` < 1 mischt die Farbe mit
    dem, was schon dasteht — der Ersatz für einen Alphakanal, den das PNG hier nicht hat."""
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


def _formatiere_zahl(x: float, stellen: int = 2) -> str:
    return f"{x:.{stellen}f}"


# --------------------------------------------------------------------------------------
# Schritt 1 — Geometrie im Repo erzeugen, Hüllbox und Geländestand messen
# --------------------------------------------------------------------------------------

def baue_geometrie(arbeit: Path) -> dict:
    """Hochbau mit Geländeplatte → glb → Bauwerks-Hüllbox, Knotenboxen, Geländestand.

    ``hochbau=True``, weil der Quader (8 × 5 × 3,25 m) unter dem Mindestabstand von 10 m
    liegt — dort setzte die ``untergrenze`` den Standort und nicht der Bildwinkel, und
    der Beweis zeigte die falsche Regel. Der Hochbau ist rund 15 m hoch mit Auskragung;
    an ihm arbeitet die Bildwinkelrechnung wirklich.
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

    # Der Geländestand ist die OBERKANTE der Geländeplatte — gemessen an der glb, nicht
    # angenommen. Das ist der Wert, den `kamerasatz(gelaende_z=…)` verlangt.
    gelaende = [hi[2] for name, lo, hi in knoten_welt if ist_gelaende(name)]
    return {
        "bbox_bauwerk": bau["bbox_bauwerk"],
        "bbox_szene": bau["bbox_szene"],
        "knoten_welt": knoten_welt,
        "gelaende_z": max(gelaende) if gelaende else None,
    }


# --------------------------------------------------------------------------------------
# Schritt 2 — Grundriss mit zwölf Kameras
# --------------------------------------------------------------------------------------

def zeichne_grundriss(geometrie: dict, satz: dict, *, kante_px: int = GRUNDRISS_PX,
                      rand_px: int = GRUNDRISS_RAND_PX):
    """Draufsicht: Welt-XY → Bild, Nord (+Y) oben, ein Massstab für beide Achsen."""
    bbox = geometrie["bbox_bauwerk"]
    kams = satz["kameras"]
    hfov, _ = kameras.bildwinkel(kams[0]["brennweite_mm"],
                                 seitenverhaeltnis=kams[0]["seitenverhaeltnis"])

    # Alles, was ins Bild muss: Szene, Kamerastandorte und die Enden der Bildwinkelstrahlen.
    xs, ys = [], []
    for ecke in geometrie["bbox_szene"]:
        xs.append(ecke[0]); ys.append(ecke[1])
    strahlen = {}
    for kam in kams:
        ax, ay, _ = kam["auge"]
        bx, by, _ = kam["blick_auf"]
        xs.append(ax); ys.append(ay)
        w = math.atan2(by - ay, bx - ax)
        # Der Keil ist VERKÜRZT gezeichnet (ein Drittel des Abstands): Bei 54° Bildwinkel
        # und 59 m Abstand ist das Sichtfeld am Bauwerk 60 m breit; zwölf solche Keile in
        # voller Länge kreuzten sich zu einem Stern, der nichts mehr zeigt. Der
        # Öffnungswinkel ist der echte.
        laenge = kam["abstand_m"] * 0.33
        enden = [(ax + laenge * math.cos(w + s * hfov / 2.0),
                  ay + laenge * math.sin(w + s * hfov / 2.0)) for s in (+1, -1)]
        strahlen[kam["kuerzel"]] = enden
        for ex, ey in enden:
            xs.append(ex); ys.append(ey)
    spanne = max(max(xs) - min(xs), max(ys) - min(ys))
    m_je_px = spanne / (kante_px - 2 * rand_px)
    mx, my = (max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0
    breite = hoehe = kante_px

    def nach_px(x, y):
        return (breite / 2.0 + (x - mx) / m_je_px, hoehe / 2.0 - (y - my) / m_je_px)

    px = _neues_bild(breite, hoehe)

    # Gelände zuerst, dann die Bauteile, dann die Hüllbox — von unten nach oben.
    for name, lo, hi in geometrie["knoten_welt"]:
        if ist_gelaende(name):
            x0, y0 = nach_px(lo[0], hi[1]); x1, y1 = nach_px(hi[0], lo[1])
            _rechteck(px, breite, hoehe, x0, y0, x1, y1, FARBE_GELAENDE)
    for name, lo, hi in geometrie["knoten_welt"]:
        if not ist_gelaende(name):
            x0, y0 = nach_px(lo[0], hi[1]); x1, y1 = nach_px(hi[0], lo[1])
            _rechteck(px, breite, hoehe, x0, y0, max(x1, x0 + 1), max(y1, y0 + 1),
                      FARBE_BAUTEIL)
    x0, y0 = nach_px(bbox[0][0], bbox[1][1]); x1, y1 = nach_px(bbox[1][0], bbox[0][1])
    _rahmen(px, breite, hoehe, x0, y0, x1, y1, FARBE_HUELLBOX, 2)

    # Keile des Bildwinkels unter die Kameras, damit die Pfeile obenauf liegen.
    for kam in kams:
        frontal = kameras.RICHTUNGEN[kam["kuerzel"]][1] == 0
        ax, ay = nach_px(kam["auge"][0], kam["auge"][1])
        keil = [(ax, ay)] + [nach_px(ex, ey) for ex, ey in strahlen[kam["kuerzel"]]]
        _polygon_fuellen(px, breite, hoehe, keil,
                         FARBE_FRONTAL if frontal else FARBE_DIAGONAL, anteil=0.18)
    for kam in kams:
        frontal = kameras.RICHTUNGEN[kam["kuerzel"]][1] == 0
        farbe = FARBE_FRONTAL if frontal else FARBE_DIAGONAL
        ax, ay = nach_px(kam["auge"][0], kam["auge"][1])
        bx, by = nach_px(kam["blick_auf"][0], kam["blick_auf"][1])
        _pfeil(px, breite, hoehe, ax, ay, bx, by, farbe, 2.0)
        _scheibe(px, breite, hoehe, ax, ay, 8.0 if frontal else 6.5, farbe)
        _ring(px, breite, hoehe, ax, ay, 8.0 if frontal else 6.5, FARBE_HUELLBOX, 1.2)

    # 10-m-Balken unten links und Nordpfeil oben links — beides aus dem Massstab
    # gerechnet, nicht dazugemalt.
    bx0, by0 = rand_px, hoehe - rand_px
    _rechteck(px, breite, hoehe, bx0, by0 - 4, bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0, by0 - 10, bx0 + 2, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0 + 10.0 / m_je_px - 2, by0 - 10,
              bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _pfeil(px, breite, hoehe, rand_px, rand_px + 34, rand_px, rand_px, FARBE_MASSSTAB, 2.0)

    return px, breite, hoehe, m_je_px


# --------------------------------------------------------------------------------------
# Schritt 3 — je Richtung die Hüllbox in der Bildebene
# --------------------------------------------------------------------------------------

def projiziere_ecken(kam: dict, bbox) -> list:
    """Die acht Hüllbox-Ecken in Rahmenkoordinaten (-0.5 … +0.5 = sichtbar).

    Zeile für Zeile die Projektion aus ``kameras.flaechenanteil``: Tiefe entlang der
    Blickachse, seitliche Anteile durch die Tiefe, Shift als Rahmenversatz. Eine Ecke
    hinter der Kamera bekommt ``None`` — sie hat keinen Ort im Bild.
    """
    basis = kameras._kamerabasis(kam["auge"], kam["blick_auf"])
    if basis is None:
        raise SystemExit(f"Kamerabasis entartet bei {kam['kuerzel']}")
    vorwaerts, rechts, oben = basis
    hfov, vfov = kameras.bildwinkel(kam["brennweite_mm"],
                                    seitenverhaeltnis=kam["seitenverhaeltnis"])
    grenze_h, grenze_v = math.tan(hfov / 2.0), math.tan(vfov / 2.0)
    versatz = kam["shift_mm"] / kam["brennweite_mm"]
    (ux, uy, uz), (ox, oy, oz) = bbox
    ecken = []
    for x in (ux, ox):
        for y in (uy, oy):
            for z in (uz, oz):
                v = (x - kam["auge"][0], y - kam["auge"][1], z - kam["auge"][2])
                tiefe = kameras._punkt(v, vorwaerts)
                if tiefe < kameras.MIN_TIEFE_M:
                    ecken.append(None)
                    continue
                ecken.append((kameras._punkt(v, rechts) / tiefe / grenze_h / 2.0,
                              (kameras._punkt(v, oben) / tiefe - versatz) / grenze_v / 2.0))
    horizont = -versatz / grenze_v / 2.0
    return ecken, horizont


#: Die zwölf Kanten des Quaders als Paare von Eckenindizes (Index = x·4 + y·2 + z).
KANTEN = tuple((a, b) for a in range(8) for b in range(a + 1, 8)
               if bin(a ^ b).count("1") == 1)


def zeichne_rahmen(kam: dict, bbox, *, breite: int = RAHMEN_B, hoehe: int = RAHMEN_H,
                   rand_px: int = RAHMEN_RAND_PX, bildrand: float = kameras.BILDRAND):
    """Ein Bild je Kamera: der 16:9-Rahmen, der Sicherheitsrand, die projizierte Box."""
    ecken, horizont = projiziere_ecken(kam, bbox)
    gesamt_b, gesamt_h = breite + 2 * rand_px, hoehe + 2 * rand_px
    px = _neues_bild(gesamt_b, gesamt_h)

    def nach_px(u, w):
        return (rand_px + (u + 0.5) * breite, rand_px + (0.5 - w) * hoehe)

    _rechteck(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
              FARBE_RAHMEN)
    # Der Sicherheitsrand: 92 % des Rahmens, um die Bildmitte. Genau gegen diese Grenze
    # rechnet `ecken_im_bild`.
    sx0, sy0 = nach_px(-0.5 * bildrand, 0.5 * bildrand)
    sx1, sy1 = nach_px(0.5 * bildrand, -0.5 * bildrand)
    _rahmen(px, gesamt_b, gesamt_h, sx0, sy0, sx1, sy1, FARBE_SICHERHEITSRAND, 1)
    if -0.5 <= horizont <= 0.5:
        hx0, hy = nach_px(-0.5, horizont)
        hx1, _ = nach_px(0.5, horizont)
        _strecke(px, gesamt_b, gesamt_h, hx0, hy, hx1, hy, FARBE_HORIZONT, 1.0)

    sichtbar = [nach_px(*e) for e in ecken if e is not None]
    _polygon_fuellen(px, gesamt_b, gesamt_h, _konvexe_huelle(sichtbar), FARBE_HUELLE)
    for a, b in KANTEN:
        if ecken[a] is None or ecken[b] is None:
            continue
        senkrecht = (a ^ b) == 1          # nur z verschieden
        _strecke(px, gesamt_b, gesamt_h, *nach_px(*ecken[a]), *nach_px(*ecken[b]),
                 FARBE_KANTE, 2.0 if senkrecht else 1.4)
    drin = 0
    for e in ecken:
        if e is None:
            continue
        im_rand = abs(e[0]) <= 0.5 * bildrand and abs(e[1]) <= 0.5 * bildrand
        drin += im_rand
        _scheibe(px, gesamt_b, gesamt_h, *nach_px(*e), 4.0,
                 FARBE_ECKE_DRIN if im_rand else FARBE_ECKE_DRAUSSEN)
    _rahmen(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
            FARBE_RAHMENRAND, 1)
    return px, gesamt_b, gesamt_h, drin


def zeichne_uebersicht(tafeln: list, *, spalten: int = 4, fuge: int = 8):
    """Die zwölf Rahmenbilder als Tafel — dieselben Pixel, nur nebeneinandergelegt."""
    tb, th = tafeln[0][1], tafeln[0][2]
    zeilen = math.ceil(len(tafeln) / spalten)
    breite = spalten * tb + (spalten + 1) * fuge
    hoehe = zeilen * th + (zeilen + 1) * fuge
    px = _neues_bild(breite, hoehe, (225, 225, 225))
    for i, (tp, _, _) in enumerate(tafeln):
        x0 = fuge + (i % spalten) * (tb + fuge)
        y0 = fuge + (i // spalten) * (th + fuge)
        for y in range(th):
            px[(y0 + y) * breite + x0:(y0 + y) * breite + x0 + tb] = tp[y * tb:(y + 1) * tb]
    return px, breite, hoehe


# --------------------------------------------------------------------------------------

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis09_") as tmp:
        geometrie = baue_geometrie(Path(tmp))

    bbox = geometrie["bbox_bauwerk"]
    satz = kameras.kamerasatz(bbox, gelaende_z=geometrie["gelaende_z"])
    if len(satz["kameras"]) != 12:
        raise SystemExit(f"{len(satz['kameras'])} Kameras statt 12 — kein Beweis.")
    masse = satz["masse_m"]

    # -- 01 Grundriss --
    px, b, h, m_je_px = zeichne_grundriss(geometrie, satz)
    pfad = ziel / (f"01_grundriss_zwoelf-kameras_bauwerk-{_formatiere_zahl(masse[0], 1)}x"
                   f"{_formatiere_zahl(masse[1], 1)}x{_formatiere_zahl(masse[2], 1)}m_"
                   f"bias-{satz['bias_grad']:.0f}grad_massstab-{m_je_px:.3f}m-je-px.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 02..13 je Richtung --
    tafeln = []
    for i, kam in enumerate(satz["kameras"]):
        # Der Eckentest NOCH EINMAL an der endgültigen Stellung — die Zahl im Dateinamen
        # stammt aus `ecken_im_bild`, nicht aus dem Bild.
        test = kameras.ecken_im_bild(kam["auge"], kam["blick_auf"], bbox,
                                     brennweite_mm=kam["brennweite_mm"],
                                     seitenverhaeltnis=kam["seitenverhaeltnis"],
                                     shift_mm=kam["shift_mm"])
        px, b, h, drin = zeichne_rahmen(kam, bbox)
        if test["passt"] != (drin == 8):
            raise SystemExit(
                f"{kam['kuerzel']}: ecken_im_bild sagt passt={test['passt']}, im Bild "
                f"liegen {drin} von 8 Ecken im Sicherheitsrand — die Zeichnung widerspricht "
                f"der Rechnung.")
        pfad = ziel / (f"{i + 2:02d}_kamera-{kam['kuerzel']}_azimut-{kam['azimut_grad']:.0f}_"
                       f"eckentest-{'passt' if test['passt'] else 'faellt'}_ecken-{drin}von8_"
                       f"ueberstehen-{test['max_ueberstehen']:.3f}_"
                       f"fuellgrad-{kam['fuellgrad']:.2f}_flaeche-{kam['flaechenanteil']:.2f}_"
                       f"abstand-{kam['abstand_m']:.1f}m_shift-{kam['shift_mm']:.1f}mm.png")
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)
        tafeln.append((px, b, h))

    # -- 14 Übersicht --
    px, b, h = zeichne_uebersicht(tafeln)
    pfad = ziel / (f"14_uebersicht_zwoelf-rahmen_unvollstaendig-{len(satz['unvollstaendig'])}_"
                   f"fuellgrad-{min(k['fuellgrad'] for k in satz['kameras']):.2f}-bis-"
                   f"{max(k['fuellgrad'] for k in satz['kameras']):.2f}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
