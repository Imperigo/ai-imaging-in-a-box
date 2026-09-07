#!/usr/bin/env python3
"""BEWEIS 17 — Die vier Halluzinationsfälle H1–H4 mit bekannter Wahrheit: ρ über der
Maske und die Tiefenkante an der Maskengrenze fragen zwei verschiedene Dinge, und keines
der beiden Masse beantwortet allein, ob das gezeigte Bauwerk das entworfene ist.

Was bewiesen wird
-----------------
Die Halluzinationsfälle aus ``docs/HALLUZINATION_2026-08-21.md`` und
``docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`` — dort am Gerät mit Blender und dem
Tiefenschätzer gemessen — werden hier als Soll/Ist-Paare mit **bekannter Wahrheit**
nachgebaut. Soll-Karte und Maske stammen in ALLEN Fällen vom unverstellten Bauwerk;
geändert wird ausschliesslich, was im Bild steht (so hat es ``auf-20260821-25``
verlangt):

    perfekt   das entworfene Bauwerk, unverstellt — die Nullprobe (ρ muss 1.000 geben)
    H1        Bauwerk ganz weg, nur Gelände: das leere Grundstück
    H2        Bauwerk 20 m versetzt — ausserhalb der Maske, im Bild noch sichtbar
    H3        andere Kubatur am richtigen Ort (doppelte Höhe, halber Grundriss)
    H4        dasselbe Bauwerk, um 90° gedreht, am richtigen Ort
    rauschen  weisses Rauschen als Ist-Karte (``bildschreiben.kontrollwerte``), drei
              Startwerte — der Rauschboden, gegen den alles gehalten wird

Je Fall werden DREI Masse aus ``aiimaging.geometrie_qa`` gerechnet, auf denselben Karten:

    ρ         ``rho_ueber_maske``: Rangkorrelation Soll↔Ist, nur über die Maskenpunkte.
              Fragt: sind die Tiefen INNERHALB des Umrisses richtig gestaffelt?
    Kante     ``kante_an_maskengrenze``: Median innen minus Median aussen am Randband,
              geteilt durch die Spanne der Ist-Karte. Fragt: steht AN der Maskengrenze
              ein Tiefensprung — steht dort überhaupt etwas?
    Anteil    ``anteil_grenze_mit_kante``: wieviel der Grenze eine der stärksten 5 %
              Kanten trägt. Das zweite Bein des Paartests seit dem 22.08.2026; hier
              mitgeführt, in der Kreuztabelle stehen nur die beiden ersten.

**Die Regel, wann ein Mass einen Fall «fängt», steht fest, BEVOR gemessen wird**
(``GEFANGEN_REST``): Der Restsignalanteil eines Falls ist
``(wert − rauschen) / (perfekt − rauschen)`` — 1 heisst «wie das perfekte Bild», 0 heisst
«wie Rauschen». Beide Anker werden IN DIESEM LAUF gemessen. Ein Mass fängt einen Fall,
wenn ihm höchstens ein Zehntel des Signals bleibt: Der Fall liegt dann praktisch auf dem
Rauschboden, und genau so haben die Gerätemessungen «gefangen» gelesen (H1 bei ρ lag
ÜBER dem Rauschboden → nicht gefangen; H1 bei der Kante lag AUF ihm → gefangen).

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild. Alle Karten sind 192×108 (16:9, wie die Kamera), dreifach
vergrössert, nächster Nachbar. Tiefe: nah = hell (``bildschreiben.normalisiere_tiefe``),
Hintergrund schwarz. Jede Zahl im Dateinamen ist ein Rückgabewert dieses Laufs;
negative Zahlen stehen als ``minus0.123``.

    01  Material-ID-Pass des unverstellten Bauwerks: Rot Gelände, Blau Wände, Grün Dach,
        Himmel schwarz — Kennfarben der Runner-Palette, daraus liest ``maske`` die Maske.
    02  Die Maske: Weiss = Bauwerk. ``n`` und ``anteil`` im Dateinamen.
    03  Die Soll-Karte (mit Gelände). Man sieht den Eckblick: die nahe Gebäudekante hell,
        beide Fassaden laufen nach aussen dunkler; das Gelände ist die Rampe darunter.
    je Fall  ``NN_<fall>_ist_….png`` — die Ist-Karte des Falls, ganzes Bild. Bei H1 ist
        an der Stelle des Bauwerks Gelände und Himmel; bei H2 steht rechts ein kleineres
        Bauwerk; bei H3 ein schmaler, hoher Turm; bei H4 der Baukörper quer.
        ``NN_<fall>_nebeneinander_….png`` — vier Kacheln: Soll | Ist | Ist-nur-Maske |
        Randband. Die Randband-Kachel ist die Kante, Punkt für Punkt: Die Maske grau,
        das innere Randband (``geometrie_qa._randpunkte``) eingefärbt nach dem Sprung zum
        nächsten Nachbarn ausserhalb — Orange = Sprung wie im perfekten Bild, dunkles
        Rot = kein Sprung. Bei H1/H2 ist das ganze Band rot: Nichts steht an der Grenze.
        Bei H3/H4 ist es rot, wo die falsche Kubatur den Umriss nicht ausfüllt, und
        orange, wo sie ihn zufällig trifft. Darunter zwei Streifen — oben ρ, unten
        Kante: Grün = das Mass lässt den Fall DURCH (Restsignal über einem Zehntel), Rot
        = das Mass fängt ihn. Beim perfekten Bild sind beide grün, beim Rauschen beide
        rot — das sind die Anker.
    Balken  ``NN_balken_….png`` — drei Tafeln übereinander (ρ, Kante, Anteil), je sechs
        Gruppen von links: perfekt, H1, H2, H3, H4, Rauschen. Blau = ρ (Achse −1…1, rote
        Linie bei ``PAAR_RHO_SCHWELLE`` 0.80 — die einzige nicht hier gemessene Zahl im
        Bild), Orange = Kante, Grün = Anteil (graue Linie: der Zufallswert des Masses).
        Der graue Balken je Gruppe ist der Rauschanker derselben Tafel. Man sieht die
        Kreuztabelle schon hier: H1/H2 haben bei ρ noch einen Balken, bei der Kante
        keinen; H3/H4 umgekehrt oder beides — was davon zutrifft, hat dieser Lauf
        gemessen, nicht dieses Skript entschieden.
    Kreuz   ``NN_kreuztabelle_….png`` — DAS Ergebnis. Vier Zeilen (H1–H4, von oben),
        Zeilenkopf ist die Ist-Karte des Falls (nur Maske). Zwei Spalten: links ρ
        (Spaltenkopf: die Maske gefüllt, blau — ρ misst das Innere), rechts Kante
        (Spaltenkopf: nur das Randband, orange — die Kante misst die Grenze). Jede Zelle
        trägt einen Balken mit dem Restsignal von 0 (Rauschen, links) bis 1 (perfekt,
        rechts), die Zehntel-Marke als dünne Linie. Zelle DUNKEL AUSGEFÜLLT = das Mass
        fängt den Fall; Zelle HELL MIT ROTEM RAHMEN = das Mass verfehlt ihn. Die
        Behauptung «jedes Mass fängt genau die Fälle, die das andere verfehlt» ist dann
        wahr, wenn kein Paar von Zellen in einer Zeile beide hell ist — und das Muster
        über Kreuz liegt. Der Dateiname sagt für jedes Mass, welche Fälle es fängt.

Was «idealer Schätzer» heisst — und was das Gerät anders sieht
---------------------------------------------------------------
Im Betrieb kommt die Ist-Karte aus einem monokularen Tiefenschätzer (Gewichte, GPU); der
läuft hier nicht. Die Ist-Karte ist darum die **Wahrheit des gezeigten Bildes**: dieselbe
Lochkamera, dieselbe Tiefe in Metern, nur die Szene ist die halluzinierte. Der Himmel
bekommt eine endliche Zahl jenseits des fernsten Bodenpunkts (``HIMMEL_FAKTOR``), weil ein
Schätzer dort keine Marke schreibt, sondern eine Zahl — und weil ``kante_an_maskengrenze``
eine Hintergrundmarke ausdrücklich zurückweist (sie sättigt das Mass bei ±1).

Was der ideale Schätzer NICHT hat, ist die Eigenheit des echten: Der legt über Boden und
Himmel eine glatte Rampe, und die korrelierte in der Gerätemessung mit der Fassade des
fehlenden Bauwerks (H1 bei ρ: −0.686 gegen Rauschboden −0.521, ``auf-25``). Diese Zahl
ist eine Aussage über den Schätzer und hier nicht reproduzierbar — ob ρ das leere
Grundstück durchlässt, entscheidet hier allein die Geometrie: das Gelände unter dem Umriss
ist eine Rampe von unten nach oben, und die Fassaden des Eckblicks staffeln sich von der
nahen Kante nach beiden Seiten. Was daraus wird, misst der Lauf. Die Gerätezahlen stehen
in den beiden Dokumenten oben und werden hier nicht abgeschrieben.

Die Kamera ist die des Produkts: ``kameras.kamerasatz`` stellt sie (Eckblick ``sSE``,
Augenhöhe 1,70 m, Shift-Modus, 35 mm) und dieses Skript bildet sie als Lochkamera nach —
Sensorbreite 36 mm, Shift in Millimetern auf dem Sensor, Tiefe längs der Achse. Der
Deckungsgrad steht auf 0.45 statt 0.70, damit neben der Maske Platz für ein um 20 m
versetztes Bauwerk bleibt (H2 muss ausserhalb der Maske und im Bild sein — beides wird
gezählt und steht im Dateinamen). Die Szene ist synthetisch (Regel 3): eine Geländeplatte
und ein Quader 12 × 8 × 6 m. Alles läuft ohne Gerät, ohne Blender, ohne numpy (Regel 4).

Aufruf:
    python3 tools/beweis/17_qa_halluzination.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/17_qa_halluzination/``. Rückgabe 1, wenn
die Nullprobe (perfekt) nicht ρ = 1.000 liefert, die Maske nicht entsteht oder H2 die
Maske berührt — jeweils ein Befund gegen Metrik, Maske oder Szenenaufbau, nicht gegen
den Beweis.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, geometrie_qa, kameras, maske  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "17_qa_halluzination"

#: Bildmasse 16:9 — das Seitenverhältnis, mit dem ``kamerasatz`` rechnet. 192×108 ist
#: gross genug für ein Randband mit einigen hundert Punkten und klein genug, dass die
#: reine Python-Strahlrechnung je Szene unter einer Sekunde bleibt.
BREITE, HOEHE = 192, 108
VERGROESSERUNG = 3
KACHEL_B, KACHEL_H = BREITE * VERGROESSERUNG, HOEHE * VERGROESSERUNG
FUGE = 8
SEITENVERHAELTNIS = BREITE / HOEHE

#: Der Baukörper: Länge, Breite, Höhe in Metern. Bewusst nicht quadratisch — sonst wäre
#: eine Drehung um 90° (H4) keine andere Kubatur.
BAU_MASSE = (12.0, 8.0, 6.0)
#: Geländeplatte, Kantenlänge in Metern, mittig unter dem Bauwerk. Sie ist endlich, damit
#: der fernste Bodenpunkt endlich ist — daraus wird die Himmelszahl des Schätzers.
PLATTE_M = 120.0
#: Himmel = dieser Faktor mal der fernste Bodenpunkt im Bild. Eine Zahl, keine Marke.
HIMMEL_FAKTOR = 1.1
HINTERGRUND_M = 1.0e10

#: Kamera: Eckblick von Süd-Südost, Deckungsgrad 0.45 (Begründung im Docstring).
KUERZEL = "sSE"
DECKUNGSGRAD = 0.45
SENSOR_BREITE_MM = kameras.SENSOR_BREITE_MM

#: H2: Versatz 20 m. Richtung in der Bildebene: ``H2_QUER`` nach rechts (Kameraachse ×
#: Aufwärts), ``H2_LAENGS`` von der Kamera weg — zusammen 20 m. Der Anteil quer ist so
#: gewählt, dass das Bauwerk neben der Maske und noch im Bild steht; ob das gelungen
#: ist, ZÄHLT das Skript und bricht ab, wenn nicht.
# 24,0 m und nicht 20,0: Bei 20 m lagen noch 54 Bauwerkspunkte INNERHALB der Maske, und
# der Selbstcheck weiter unten hat den Lauf dafuer angehalten — richtig so, denn H2 soll
# den Fall «ausserhalb der Maske, im Bild noch sichtbar» stellen. 24 m ist der kleinste
# der geprueften Werte, der ihn wirklich stellt; ab 36 m faellt das Bauwerk ganz aus dem
# Bild und der Fall waere ein anderer.
H2_VERSATZ_M = 24.0
H2_QUER = 0.90

#: Die Regel, bevor gemessen wird: Ein Mass fängt einen Fall, wenn dem Fall höchstens
#: dieser Anteil des Signals zwischen Rauschen (0) und perfektem Bild (1) bleibt.
GEFANGEN_REST = 0.10

RAUSCH_SEEDS = (11, 23, 47)

# Kennfarben der Runner-Palette für die Indizes 0..2 (hsv(i·0.618, 0.85, 1.0)), wie in
# tools/beweis/15_qa_maske.py und tests/test_maske.py — die Tabelle ist der Schlüssel.
FARBE_GELAENDE = (255, 38, 38)
FARBE_WAND = (38, 101, 255)
FARBE_DACH = (165, 255, 38)
FARBE_HINTERGRUND = (0, 0, 0)
NAME_GELAENDE = "IfcSite_Gelaende_0synth0000000000001"
NAME_WAND = "IfcWall_Aussenwand_0synth0000000000002"
NAME_DACH = "IfcSlab_Dach_0synth0000000000003"

FARBE_LEINWAND = (245, 245, 245)
FARBE_ACHSE = (120, 120, 120)
FARBE_MASKE_AN = (235, 235, 235)
FARBE_MASKE_GRAU = (90, 90, 90)
FARBE_RHO = (50, 110, 210)
FARBE_KANTE = (230, 120, 40)
FARBE_ANTEIL = (60, 150, 70)
FARBE_RAUSCHEN = (170, 170, 170)
FARBE_SCHWELLE = (190, 60, 50)
FARBE_DURCH = (60, 150, 70)          # Streifen: das Mass lässt den Fall durch
FARBE_GEFANGEN = (190, 60, 50)       # Streifen: das Mass fängt den Fall
FARBE_ZELLE_GEFANGEN = (35, 55, 95)
FARBE_ZELLE_VERFEHLT = (252, 240, 236)
FARBE_ZELLE_RAHMEN = (190, 60, 50)
FARBE_KEIN_SPRUNG = (120, 30, 20)
FARBE_SPRUNG = (255, 170, 60)


# ----------------------------------------------------------------------------------
# Vektoren, klein
# ----------------------------------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _kreuz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    n = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
    return (a[0] / n, a[1] / n, a[2] / n)


# ----------------------------------------------------------------------------------
# Die Kamera — aus kamerasatz, als Lochkamera nachgebildet
# ----------------------------------------------------------------------------------

class Lochkamera:
    """Die Kamera aus ``kameras.kamerasatz`` als Strahlerzeuger.

    Bildpunkt → Richtung im Weltsystem. Die Achse ist waagrecht (Shift-Modus); der Shift
    verschiebt das Bildfenster auf dem Sensor nach oben, in Millimetern wie ``shift_mm``.
    Die Tiefe eines Treffers ist der Abstand längs der Achse (``t · brennweite``), nicht
    die Strahllänge — eine Fläche parallel zum Sensor hat dann überall dieselbe Tiefe.
    """

    def __init__(self, kamera: dict):
        self.auge = tuple(float(v) for v in kamera["auge"])
        self.f = _norm(_sub(kamera["blick_auf"], self.auge))
        self.r = _norm(_kreuz(self.f, (0.0, 0.0, 1.0)))
        self.u = _kreuz(self.r, self.f)
        self.brennweite = float(kamera["brennweite_mm"])
        self.shift = float(kamera["shift_mm"])
        self.sensor_h = SENSOR_BREITE_MM / SEITENVERHAELTNIS

    def strahl(self, px: int, py: int) -> tuple[float, float, float]:
        xs = (px + 0.5) / BREITE * SENSOR_BREITE_MM - SENSOR_BREITE_MM / 2.0
        ys = self.sensor_h / 2.0 - (py + 0.5) / HOEHE * self.sensor_h + self.shift
        f, r, u = self.f, self.r, self.u
        return tuple(f[k] * self.brennweite + r[k] * xs + u[k] * ys for k in range(3))


# ----------------------------------------------------------------------------------
# Die Szene — Platte und Quader, Strahl für Strahl
# ----------------------------------------------------------------------------------

def quader(mitte_xy, masse, drehung_grad: float = 0.0) -> dict:
    """Ein Quader auf dem Gelände: Mitte im Grundriss, (Länge, Breite, Höhe), Drehung um
    die Hochachse. Er steht auf z = 0."""
    return {"mitte": (float(mitte_xy[0]), float(mitte_xy[1])),
            "masse": tuple(float(m) for m in masse),
            "drehung": math.radians(drehung_grad)}


def _treffer_platte(auge, d) -> float | None:
    if d[2] >= 0.0:
        return None
    t = -auge[2] / d[2]
    x = auge[0] + t * d[0]
    y = auge[1] + t * d[1]
    if abs(x) <= PLATTE_M / 2.0 and abs(y) <= PLATTE_M / 2.0:
        return t
    return None


def _treffer_quader(auge, d, q: dict) -> tuple[float, bool] | None:
    """Plattentest im gedrehten Körpersystem. Gibt ``(t, ist_dach)``."""
    c, s = math.cos(-q["drehung"]), math.sin(-q["drehung"])
    ox, oy = auge[0] - q["mitte"][0], auge[1] - q["mitte"][1]
    o = (c * ox - s * oy, s * ox + c * oy, auge[2])
    dd = (c * d[0] - s * d[1], s * d[0] + c * d[1], d[2])
    lx, ly, lz = q["masse"]
    grenzen = ((-lx / 2.0, lx / 2.0), (-ly / 2.0, ly / 2.0), (0.0, lz))
    t_ein, t_aus, achse = -math.inf, math.inf, -1
    for k in range(3):
        lo, hi = grenzen[k]
        if abs(dd[k]) < 1e-12:
            if o[k] < lo or o[k] > hi:
                return None
            continue
        t1, t2 = (lo - o[k]) / dd[k], (hi - o[k]) / dd[k]
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > t_ein:
            t_ein, achse = t1, k
        t_aus = min(t_aus, t2)
    if t_aus < max(t_ein, 0.0) or t_ein <= 0.0:
        return None
    return t_ein, achse == 2


def raster(kamera: Lochkamera, koerper: list[dict]):
    """Tiefe (Meter längs der Achse, Hintergrund = Marke), Materialfarbe je Bildpunkt,
    und die Menge der Punkte, an denen ein Körper getroffen wurde."""
    tiefe = [HINTERGRUND_M] * (BREITE * HOEHE)
    farben = [FARBE_HINTERGRUND] * (BREITE * HOEHE)
    koerper_punkte: set[int] = set()
    for py in range(HOEHE):
        for px in range(BREITE):
            d = kamera.strahl(px, py)
            i = py * BREITE + px
            t_best, farbe = None, FARBE_HINTERGRUND
            t = _treffer_platte(kamera.auge, d)
            if t is not None:
                t_best, farbe = t, FARBE_GELAENDE
            for q in koerper:
                tr = _treffer_quader(kamera.auge, d, q)
                if tr is not None and (t_best is None or tr[0] < t_best):
                    t_best = tr[0]
                    farbe = FARBE_DACH if tr[1] else FARBE_WAND
                    koerper_punkte.add(i)
            if t_best is not None:
                tiefe[i] = t_best * kamera.brennweite
                farben[i] = farbe
    return tiefe, farben, koerper_punkte


def als_schaetzung(tiefe, himmel_m: float) -> list[float]:
    """Die Wahrheit des gezeigten Bildes als Schätzkarte: Himmel wird zur Zahl."""
    return [himmel_m if t >= geometrie_qa.HINTERGRUND_SCHWELLE_M else t for t in tiefe]


# ----------------------------------------------------------------------------------
# Messen — dieselben drei Funktionen für jeden Fall
# ----------------------------------------------------------------------------------

def messe(soll, ist, m) -> dict:
    rho = geometrie_qa.rho_ueber_maske(soll, ist, m, polaritaet=geometrie_qa.POLARITAET_TIEFE)
    kante = geometrie_qa.kante_an_maskengrenze(ist, m, breite=BREITE,
                                               polaritaet=geometrie_qa.POLARITAET_TIEFE)
    anteil = geometrie_qa.anteil_grenze_mit_kante(ist, m, breite=BREITE)
    return {"rho": rho["gerichtet"], "kante": kante["gerichtet"],
            "anteil": anteil["anteil"], "anteil_zufall": anteil["zufall"],
            "n_maske": rho["n_maske"], "n_rand": kante["n_innen"],
            "warnungen": rho["warnungen"] + kante["warnungen"] + anteil["warnungen"]}


def restsignal(wert, perfekt, rauschen) -> float | None:
    if wert is None or perfekt is None or rauschen is None:
        return None
    spanne = perfekt - rauschen
    if abs(spanne) < 1e-12:
        return None
    return (wert - rauschen) / spanne


def gefangen(rest) -> bool | None:
    return None if rest is None else rest <= GEFANGEN_REST


# ----------------------------------------------------------------------------------
# Kacheln
# ----------------------------------------------------------------------------------

def kachel_tiefe(karte, m=None):
    """Tiefe → Grau, nah = hell. Mit ``m`` nur die Maskenpunkte, über sich normalisiert.
    Der Himmel des Schätzers ist eine endliche Zahl und wird darum wie ferner Boden grau
    — genau so sähe ihn auch die Kette."""
    if m is not None:
        karte = [karte[k] if m[k] else HINTERGRUND_M for k in range(len(karte))]
    grau, _ = bildschreiben.normalisiere_tiefe(karte)
    return [(int(round(g * 255)),) * 3 for g in grau]


def kachel_randband(ist, m, bezug: float):
    """Die Kante, Punkt für Punkt: Sprung von jedem inneren Randpunkt zu seinem fernsten
    äusseren Nachbarn, geteilt durch die Spanne der Ist-Karte, gegen den Bezug (die
    Kante des perfekten Bildes) eingefärbt. Dieselbe Nachbarschaft wie
    ``geometrie_qa._randpunkte``."""
    innen, _ = geometrie_qa._randpunkte(list(m), BREITE, HOEHE)
    spanne = max(ist) - min(ist)
    aus = [FARBE_MASKE_GRAU if an else FARBE_HINTERGRUND for an in m]
    for i in innen:
        nachbarn = [i - 1, i + 1, i - BREITE, i + BREITE]
        sprung = max((ist[n] - ist[i]) / spanne for n in nachbarn if not m[n])
        w = max(0.0, min(1.0, sprung / bezug)) if bezug > 0 else 0.0
        aus[i] = tuple(int(round(FARBE_KEIN_SPRUNG[k] + w * (FARBE_SPRUNG[k] - FARBE_KEIN_SPRUNG[k])))
                       for k in range(3))
    return aus


def kachel_pikto_maske(m, nur_rand: bool):
    """Spaltenköpfe der Kreuztabelle: die Maske gefüllt (ρ) oder nur ihr Randband (Kante)."""
    if not nur_rand:
        return [FARBE_RHO if an else FARBE_HINTERGRUND for an in m]
    innen, _ = geometrie_qa._randpunkte(list(m), BREITE, HOEHE)
    aus = [FARBE_HINTERGRUND] * len(m)
    for i in innen:
        aus[i] = FARBE_KANTE
    return aus


def vergroessere(kachel, faktor: int = VERGROESSERUNG):
    aus = []
    for y in range(HOEHE * faktor):
        zeile = kachel[(y // faktor) * BREITE:(y // faktor + 1) * BREITE]
        for x in range(BREITE * faktor):
            aus.append(zeile[x // faktor])
    return aus


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe


def _einblenden(px, breite, kachel, kb, kh, x0, y0) -> None:
    for y in range(kh):
        px[(y0 + y) * breite + x0:(y0 + y) * breite + x0 + kb] = kachel[y * kb:(y + 1) * kb]


def nebeneinander(kacheln, gefangen_liste, *, streifen: int = 14):
    n = len(kacheln)
    breite = n * KACHEL_B + (n - 1) * FUGE
    hoehe = KACHEL_H + FUGE + len(gefangen_liste) * (streifen + 2)
    px = [FARBE_LEINWAND] * (breite * hoehe)
    for k, kachel in enumerate(kacheln):
        _einblenden(px, breite, kachel, KACHEL_B, KACHEL_H, k * (KACHEL_B + FUGE), 0)
    y = KACHEL_H + FUGE
    for g in gefangen_liste:
        farbe = FARBE_RAUSCHEN if g is None else (FARBE_GEFANGEN if g else FARBE_DURCH)
        _rechteck(px, breite, hoehe, 0, y, breite, y + streifen, farbe)
        y += streifen + 2
    return px, breite, hoehe


# ----------------------------------------------------------------------------------
# Balken — drei Tafeln, nur Zahlen aus diesem Lauf
# ----------------------------------------------------------------------------------

def tafel(px, breite, hoehe, y_oben, y_unten, werte, farbe, *, unten, oben,
          linien, anker=None, rand: int = 40) -> None:
    def y_von(v):
        return y_unten - (v - unten) / (oben - unten) * (y_unten - y_oben)

    for wert, lf in linien:
        _rechteck(px, breite, hoehe, rand, y_von(wert), breite - rand, y_von(wert) + 1, lf)
    n = len(werte)
    gb = (breite - 2 * rand) / n
    for g, v in enumerate(werte):
        x0 = rand + g * gb + gb * 0.2
        x1 = rand + g * gb + gb * 0.55
        if anker is not None:
            _rechteck(px, breite, hoehe, x1 + 2, y_von(anker), x1 + gb * 0.25, y_von(0.0),
                      FARBE_RAUSCHEN)
        if v is not None:
            _rechteck(px, breite, hoehe, x0, y_von(v), x1, y_von(0.0), farbe)


def balken(messungen: list[dict], rausch_mittel: dict, *, breite: int = 900, hoehe: int = 720):
    px = [FARBE_LEINWAND] * (breite * hoehe)
    tafeln = (
        ("rho", FARBE_RHO, -1.0, 1.0,
         [(0.0, FARBE_ACHSE), (1.0, FARBE_ACHSE), (-1.0, FARBE_ACHSE),
          (geometrie_qa.PAAR_RHO_SCHWELLE, FARBE_SCHWELLE)]),
        ("kante", FARBE_KANTE, None, None, [(0.0, FARBE_ACHSE)]),
        ("anteil", FARBE_ANTEIL, 0.0, 1.0,
         [(0.0, FARBE_ACHSE), (1.0, FARBE_ACHSE),
          (messungen[0]["anteil_zufall"] or 0.0, FARBE_ACHSE)]),
    )
    h_tafel = (hoehe - 40) / len(tafeln)
    for k, (feld, farbe, unten, oben, linien) in enumerate(tafeln):
        werte = [e[feld] for e in messungen]
        if unten is None:
            spitze = max(abs(v) for v in werte if v is not None) or 1.0
            unten, oben = -0.25 * spitze * 1.1, spitze * 1.1
        y0 = 20 + k * h_tafel + 10
        y1 = 20 + (k + 1) * h_tafel - 10
        tafel(px, breite, hoehe, y0, y1, werte, farbe, unten=unten, oben=oben,
              linien=linien, anker=rausch_mittel[feld])
    return px, breite, hoehe


# ----------------------------------------------------------------------------------
# Die Kreuztabelle
# ----------------------------------------------------------------------------------

def kreuztabelle(zeilen: list[tuple[list, dict]], m, *, zelle_b: int = 300):
    """``zeilen``: je Fall (Ist-Kachel nur Maske in Originalgrösse, Restsignal je Mass).
    Kopfzeile: links leer, dann die beiden Piktogramme; jede Zeile: Ist-Kachel, dann
    zwei Zellen. Zellen tragen den Restsignalbalken von 0 (links) bis 1 (rechts)."""
    kopf_b, kopf_h = BREITE, HOEHE
    zelle_h = HOEHE
    n = len(zeilen)
    breite = kopf_b + FUGE + 2 * (zelle_b + FUGE)
    hoehe = kopf_h + FUGE + n * (zelle_h + FUGE)
    px = [FARBE_LEINWAND] * (breite * hoehe)
    _einblenden(px, breite, kachel_pikto_maske(m, False), BREITE, HOEHE, kopf_b + FUGE, 0)
    _einblenden(px, breite, kachel_pikto_maske(m, True), BREITE, HOEHE,
                kopf_b + FUGE + zelle_b + FUGE, 0)
    for z, (kachel, reste) in enumerate(zeilen):
        y0 = kopf_h + FUGE + z * (zelle_h + FUGE)
        _einblenden(px, breite, kachel, BREITE, HOEHE, 0, y0)
        for s, feld in enumerate(("rho", "kante")):
            x0 = kopf_b + FUGE + s * (zelle_b + FUGE)
            rest = reste[feld]
            g = gefangen(rest)
            if g is None:
                _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y0 + zelle_h, FARBE_RAUSCHEN)
                continue
            if g:
                _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y0 + zelle_h,
                          FARBE_ZELLE_GEFANGEN)
                balkenfarbe, achse = FARBE_LEINWAND, (200, 200, 200)
            else:
                _rechteck(px, breite, hoehe, x0, y0, x0 + zelle_b, y0 + zelle_h,
                          FARBE_ZELLE_RAHMEN)
                _rechteck(px, breite, hoehe, x0 + 4, y0 + 4, x0 + zelle_b - 4,
                          y0 + zelle_h - 4, FARBE_ZELLE_VERFEHLT)
                balkenfarbe, achse = FARBE_RHO if feld == "rho" else FARBE_KANTE, FARBE_ACHSE
            # Skala: 0 bei einem Achtel der Zelle, 1 bei sieben Achteln; darunter wird
            # abgeschnitten, damit ein negatives Restsignal nicht aus der Zelle läuft.
            xa, xb = x0 + zelle_b / 8.0, x0 + zelle_b * 7.0 / 8.0
            ym = y0 + zelle_h / 2.0
            _rechteck(px, breite, hoehe, xa, ym - 1, xb, ym + 1, achse)
            for marke in (0.0, GEFANGEN_REST, 1.0):
                xm = xa + marke * (xb - xa)
                _rechteck(px, breite, hoehe, xm, ym - 14, xm + 2, ym + 14, achse)
            r = max(-0.125, min(1.125, rest))
            xr = xa + r * (xb - xa)
            _rechteck(px, breite, hoehe, min(xa, xr), ym - 9, max(xa, xr), ym + 9, balkenfarbe)
    return px, breite, hoehe


# ----------------------------------------------------------------------------------

def _z(x) -> str:
    return "None" if x is None else f"{x:.3f}".replace("-", "minus")


def _eintrag(index: int, name: str, farbe) -> dict:
    return {"index": index, "name": name, "quelle": "objekt",
            "farbe_srgb": [k / 255.0 for k in farbe], "farbe_srgb_8bit": list(farbe)}


TABELLE = [_eintrag(0, NAME_GELAENDE, FARBE_GELAENDE),
           _eintrag(1, NAME_WAND, FARBE_WAND),
           _eintrag(2, NAME_DACH, FARBE_DACH)]


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []
    nr = 0

    def schreibe(stamm: str, px, breite, hoehe) -> Path:
        nonlocal nr
        nr += 1
        pfad = ziel / f"{nr:02d}_{stamm}.png"
        bildschreiben.schreibe_farb_png(pfad, px, breite, hoehe)
        geschrieben.append(pfad)
        return pfad

    # ── Kamera aus dem Produktivweg ──
    lx, ly, lz = BAU_MASSE
    bbox = [[-lx / 2, -ly / 2, 0.0], [lx / 2, ly / 2, lz]]
    satz = kameras.kamerasatz(bbox, gelaende_z=0.0, deckungsgrad=DECKUNGSGRAD,
                              seitenverhaeltnis=SEITENVERHAELTNIS, kuerzel=(KUERZEL,))
    k = satz["kameras"][0]
    kamera = Lochkamera(k)

    # ── Die Wahrheit: Soll-Karte, Material-ID-Pass, Maske ──
    bau = quader((0.0, 0.0), BAU_MASSE)
    soll, farben, _ = raster(kamera, [bau])
    klein_png = ziel / "_material_id_192px.png"
    bildschreiben.schreibe_farb_png(klein_png, farben, BREITE, HOEHE)
    ergebnis = maske.bauwerksmaske_aus_lauf(
        klein_png, {"material_id_tabelle": TABELLE, "material_id_quelle": ["objekt"]})
    klein_png.unlink()
    m = ergebnis["maske"]
    if m is None:
        print("KEINE MASKE: " + " ".join(ergebnis["warnungen"]), file=sys.stderr)
        return 1
    m = list(m)

    boden = [t for t, f in zip(soll, farben) if f == FARBE_GELAENDE]
    himmel_m = HIMMEL_FAKTOR * max(boden)

    schreibe(f"material-id-pass_gelaende-rot_wand-blau_dach-gruen_kamera-{KUERZEL}_"
             f"abstand-{k['abstand_m']:.1f}m_shift-{k['shift_mm']:.2f}mm_"
             f"fuellgrad-{k['fuellgrad']:.2f}", vergroessere(farben), KACHEL_B, KACHEL_H)
    schreibe(f"maske_bauwerk-weiss_n-{ergebnis['n_bauwerk']}_anteil-"
             f"{ergebnis['anteil_bauwerk']:.3f}_gelaende-{ergebnis['n_gelaende']}",
             vergroessere([FARBE_MASKE_AN if an else FARBE_HINTERGRUND for an in m]),
             KACHEL_B, KACHEL_H)
    kachel_soll = vergroessere(kachel_tiefe(soll))
    schreibe(f"soll_nah-hell_eckblick_himmel-des-schaetzers-{himmel_m:.1f}m",
             kachel_soll, KACHEL_B, KACHEL_H)

    # ── Die Fälle: nur das Bild ändert sich ──
    # H2: 20 m in der Bildebene, Anteil quer und längs (Docstring).
    quer, laengs = kamera.r, kamera.f
    a_q = H2_QUER * H2_VERSATZ_M
    a_l = math.sqrt(H2_VERSATZ_M ** 2 - a_q ** 2)
    h2_mitte = (quer[0] * a_q + laengs[0] * a_l, quer[1] * a_q + laengs[1] * a_l)
    faelle = [
        ("perfekt", "unverstellt", [bau]),
        ("H1", "bauwerk-ganz-weg", []),
        ("H2", f"bauwerk-{H2_VERSATZ_M:.0f}m-versetzt", [quader(h2_mitte, BAU_MASSE)]),
        ("H3", "andere-kubatur_doppelte-hoehe-halber-grundriss",
         [quader((0.0, 0.0), (lx / 2, ly / 2, lz * 2))]),
        ("H4", "um-90-grad-gedreht", [quader((0.0, 0.0), BAU_MASSE, 90.0)]),
    ]

    messungen: list[dict] = []
    ist_karten: list[list[float]] = []
    for name, beschreibung, koerper in faelle:
        tiefe, _, punkte = raster(kamera, koerper)
        ist = als_schaetzung(tiefe, himmel_m)
        e = messe(soll, ist, m)
        e["name"], e["beschreibung"] = name, beschreibung
        e["n_koerper"] = len(punkte)
        e["n_koerper_in_maske"] = sum(1 for i in punkte if m[i])
        messungen.append(e)
        ist_karten.append(ist)

    rauschen: list[dict] = []
    for seed in RAUSCH_SEEDS:
        ist = bildschreiben.kontrollwerte("rauschen", BREITE, HOEHE, seed=seed)
        e = messe(soll, ist, m)
        rauschen.append(e)
        if seed == RAUSCH_SEEDS[0]:
            ist_rauschen = ist
    rausch_mittel = {feld: sum(e[feld] for e in rauschen) / len(rauschen)
                     for feld in ("rho", "kante", "anteil")}
    perfekt = messungen[0]

    # Nullprobe und Aufbauprüfung, bevor irgendein Bild diese Zahlen trägt.
    if perfekt["rho"] is None or abs(perfekt["rho"] - 1.0) > 1e-9:
        print(f"NULLPROBE VERFEHLT: perfekt gibt rho={perfekt['rho']!r} statt 1.000 — "
              f"Befund gegen die Metrik, nicht gegen die Szene.", file=sys.stderr)
        return 1
    h2 = messungen[2]
    if h2["n_koerper_in_maske"] != 0 or h2["n_koerper"] == 0:
        print(f"H2 FALSCH AUFGEBAUT: {h2['n_koerper_in_maske']} Bauwerkspunkte in der "
              f"Maske, {h2['n_koerper']} im Bild — verlangt sind 0 und > 0.",
              file=sys.stderr)
        return 1
    for e in messungen + rauschen:
        for w in e["warnungen"]:
            print(f"WARNUNG {e.get('name', 'rauschen')}: {w}", file=sys.stderr)

    # ── Bilder je Fall ──
    for e, ist in zip(messungen, ist_karten):
        e["rest"] = {f: restsignal(e[f], perfekt[f], rausch_mittel[f])
                     for f in ("rho", "kante", "anteil")}
    for e in rauschen:
        e["rest"] = {f: restsignal(e[f], perfekt[f], rausch_mittel[f])
                     for f in ("rho", "kante", "anteil")}

    def bilder_fuer(name, beschreibung, e, ist, zusatz=""):
        k_ist = vergroessere(kachel_tiefe(ist))
        k_ist_m = vergroessere(kachel_tiefe(ist, m))
        k_rand = vergroessere(kachel_randband(ist, m, perfekt["kante"]))
        schreibe(f"{name}_ist_{beschreibung}{zusatz}", k_ist, KACHEL_B, KACHEL_H)
        px, b, h = nebeneinander([kachel_soll, k_ist, k_ist_m, k_rand],
                                 [gefangen(e["rest"]["rho"]), gefangen(e["rest"]["kante"])])
        schreibe(f"{name}_nebeneinander_soll-ist-istmaske-randband_rho-{_z(e['rho'])}_"
                 f"kante-{_z(e['kante'])}_anteil-{_z(e['anteil'])}_rest-rho-"
                 f"{_z(e['rest']['rho'])}_rest-kante-{_z(e['rest']['kante'])}", px, b, h)

    for e, ist in zip(messungen, ist_karten):
        zusatz = ""
        if e["name"] == "H2":
            zusatz = f"_in-maske-{e['n_koerper_in_maske']}px_im-bild-{e['n_koerper']}px"
        bilder_fuer(e["name"], e["beschreibung"], e, ist, zusatz)
    bilder_fuer("rauschen", f"weisses-rauschen_seed-{RAUSCH_SEEDS[0]}", rauschen[0],
                ist_rauschen)

    # ── Balken ──
    px, b, h = balken(messungen + [rauschen[0]], rausch_mittel)
    # DER NAME BLEIBT UNTER 255 BYTE. Der erste Anlauf haengte rho UND Kantenanteil je
    # Fall an und kam auf rund 290 Zeichen — das Dateisystem lehnt das ab, und der Beweis
    # scheiterte an seinem eigenen Dateinamen. Hier stehen die rho-Werte; der
    # Kantenanteil ist in der Kreuztabelle darunter ohnehin die zweite Spalte.
    schreibe("balken_rho-blau_kante-orange_gruppen-perfekt-H1-H2-H3-H4-rauschen_"
             + "_".join(f"{e['name']}-rho-{_z(e['rho'])}" for e in messungen)
             + f"_rauschboden-rho-{_z(rausch_mittel['rho'])}"
             f"_schwelle-{geometrie_qa.PAAR_RHO_SCHWELLE:.2f}",
             px, b, h)

    # ── Kreuztabelle ──
    zeilen = [(kachel_tiefe(ist, m), e["rest"]) for e, ist in zip(messungen[1:], ist_karten[1:])]
    px, b, h = kreuztabelle(zeilen, m)
    faengt = {}
    for feld in ("rho", "kante"):
        faengt[feld] = [e["name"] for e in messungen[1:] if gefangen(e["rest"][feld])]
    verfehlt_beide = [e["name"] for e in messungen[1:]
                      if not gefangen(e["rest"]["rho"]) and not gefangen(e["rest"]["kante"])]
    schreibe(f"kreuztabelle_zeilen-H1-H2-H3-H4_spalten-rho-kante_dunkel-gefangen_"
             f"rho-faengt-{'-'.join(faengt['rho']) or 'keinen'}_"
             f"kante-faengt-{'-'.join(faengt['kante']) or 'keinen'}_"
             f"beide-verfehlen-{'-'.join(verfehlt_beide) or 'keinen'}_"
             f"regel-rest-bis-{GEFANGEN_REST:.2f}", px, b, h)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
