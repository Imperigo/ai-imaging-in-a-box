#!/usr/bin/env python3
"""BEWEIS 10 — Die automatische Kamerasetzung, Teil 2: Der Deckungsgrad stellt die Kamera,
und 0,70 (Owner-Entscheid 25.08.2026) steht dort, wo die Messung ein Bild noch trägt —
gezeichnet aus dem, was ``kameras.kamerasatz`` bei fünf Deckungsgraden zurückgibt, und aus
den sieben Stützstellen der Kniemessung, ohne eine Linie dazwischen zu erfinden.

Was bewiesen wird
-----------------
1. **Was der Deckungsgrad tut.** ``kamerasatz(bbox, deckungsgrad=d)`` setzt den Abstand
   so, dass die Silhouette des Bauwerks ``d`` der Bildbreite füllt. Dieselbe Geometrie,
   dieselbe Richtung (Süd), fünf Werte — 0,30 / 0,45 / 0,55 / 0,70 / 0,85 — und je ein
   projizierter Rahmen. Der Abstand sinkt, das Bauwerk wächst im Bild, die Umgebung
   verschwindet; die gemessene Bildbreite steht als Balken unter jedem Rahmen und im
   Dateinamen. Die Vorgabe ``DECKUNGSGRAD`` liegt in der Reihe — das Skript bricht ab,
   wenn sie es nicht tut.
2. **Die Rampe mit Knie.** Das Geometrie-Tor besteht nicht ab einer Stufe, sondern auf
   einer Rampe: Ein Score entsteht ab rund 0,50 Bildbreite, die Schwelle 0,65 wird
   zwischen 0,5991 und 0,6488 überschritten. ``BILDBREITE_KNIE`` (0,5991) ist die untere
   Kante des Knies, ``BILDBREITE_ABBRUCH`` (0,65) die Stelle, unter der nicht gerendert
   wird. Beide werden hier **gegen die Messdatei geprüft**, aus der sie stammen.
3. **Zwischen den Stützstellen wird nicht interpoliert** (Hausregel, siehe
   ``geometrie_qa.torchance``). Das Kurvenbild zeigt darum Punkte, keine Linie: Eine
   Gerade durch sieben Punkte einer einzigen Szene wäre keine Schätzung, sondern eine
   Erfindung.

Die Geometrie ist synthetisch und wird hier erzeugt (Regel 3): ein Quader
15,36 × 10,36 × 6,0 m auf einer Platte mit zehnfacher Grundfläche, über
``make_test_glb.baue_glb`` direkt als glb — **dieselbe Szene, die die HomeStation am
24.08.2026 gemessen hat** (``auftraege/ergebnisse/auf-20260824-37.json``). Die Hüllbox
wird mit ``glbbox.bauwerksbox`` aus der glb gelesen und gegen die dort protokollierte
Box geprüft; stimmt sie nicht, ist es nicht dieselbe Szene, und das Skript bricht ab.
Kamera-Vorgaben: 35 mm Kleinbild, 16:9, Shift-Modus, Richtung ``s`` (frontal Süd, mit
``FRONTAL_VERSATZ`` 10 % seitlich). Kein Blender, keine GPU.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Bedeutung liegt in Anordnung, Farbe und Dateiname; jede
Zahl im Dateinamen ist aus dem Rückgabewert einer Funktion gelesen, nicht abgeschrieben.

``01_grundriss_…png`` — Draufsicht, massstäblich, Nord oben, 10-m-Balken unten links.

    Sandfarben     die Geländeplatte
    Stahlblau      das Bauwerk; dunkler Rahmen: seine Hüllbox (``bauwerksbox``)
    Fünf Kreise    die fünf Standorte der Südkamera, von hell (0,30, am weitesten weg)
                   bis dunkel (0,85, am nächsten); der Kreis mit orangem Ring ist die
                   Vorgabe 0,70. Der blasse Keil ist der horizontale Bildwinkel (54°),
                   auf ein Drittel des Abstands gekürzt, im Öffnungswinkel echt.

Man sieht: Alle fünf Standorte liegen auf einer Linie südlich des Bauwerks, und ihr
Abstand fällt mit steigendem Deckungsgrad — der Deckungsgrad ist ein Abstand, nichts
anderes. Die Abstände in Metern stehen im Dateinamen.

``02_…`` bis ``06_…png`` — je Deckungsgrad der Rahmen, Kamera Süd, in die Bildebene
projiziert (dieselbe Projektion wie ``kameras.flaechenanteil``).

    Weisses Feld      der Bildrahmen 16:9
    Hellgrauer Rahmen der Sicherheitsrand 92 % (Eckentest)
    Dünne graue Linie der Horizont
    Sandfarbene Fläche  die Oberfläche der Geländeplatte, projiziert. Aus 1,7 m
                      Augenhöhe ist sie ein flaches Band unter dem Horizont; bei 0,30
                      liegt sie mit beiden Seitenkanten im Bild, bei 0,85 läuft sie
                      links und rechts aus dem Rahmen — die Umgebung ist weg
    Hellblaue Fläche  die konvexe Hülle der acht Bauwerksecken; ihr Anteil am Feld IST
                      ``flaechenanteil`` im Dateinamen
    Grüne Punkte      Ecken innerhalb des Sicherheitsrands (rot: ausserhalb)
    Balken darunter   die **gemessene** Bildbreite des Bauwerks (``fuellgrad_breite``),
                      vom linken Rahmenrand aus, als Anteil der Rahmenbreite — so lang,
                      wie die blaue Hülle breit ist. Drei Marken an festen Stellen, in
                      jedem Bild dieselben: grau das Knie 0,5991, rot die Abbruchgrenze
                      0,65, orange die Vorgabe 0,70.
    Rahmenfarbe       das Urteil von ``kameras.rahmungsverhaeltnis`` mit dieser Breite:
                      grün — rendern (≥ 0,65); bernstein — über dem Knie, aber unter der
                      Abbruchgrenze (das Band, in dem sich die zwei Messungen
                      widersprechen); rot — Abbruch (unter dem Knie).

Man sieht: Der Balken ist so lang wie die blaue Hülle breit — Balken und Hülle sind zwei
Rechenwege für dieselbe Breite (``kamerasatz`` gegen die Projektion hier), und das
Skript prüft, dass sie sich um weniger als 0,5 % unterscheiden. Bei 0,30, 0,45 und 0,55
ist der Rahmen rot (alle unter dem Knie), bei 0,70 und 0,85 grün. Das Bauwerk wird nicht
angeschnitten: alle acht Ecken bleiben grün, auch bei 0,85.

``07_tafel_…png`` — die fünf Rahmen untereinander, dieselben Pixel. Von oben nach unten
wächst der Balken an den drei Marken vorbei, die Hülle füllt den Rahmen, und die Platte
läuft seitlich aus dem Bild.

``08_rampe-mit-knie_…png`` — das Kurvenbild, zwei Felder übereinander, gemeinsame
waagrechte Achse: Bildbreite 0 … 1, feine Striche je 0,1, langer Strich bei 0,5.

    Oberes Feld     ``geom_iou`` je Stützstelle (0 … 1)
    Unteres Feld    ``geometrie_score`` je Stützstelle (0 … 1); die waagrechte rote
                    Linie ist ``SCHWELLE_GEOMETRIE`` 0,65
    Gefüllte Punkte grün: Tor bestanden; rot: nicht bestanden
    Hohle Ringe     auf der Nulllinie: dort gibt es **keinen** Score (zu wenige gemeinsame
                    Punkte, unter ``MIN_GEMEINSAME_PUNKTE``) — nicht «Score 0», sondern
                    «nicht messbar»; die dritte Antwort dieses Projekts
    Senkrechte      grau: ``BILDBREITE_KNIE`` 0,5991; rot: ``BILDBREITE_ABBRUCH`` 0,65;
                    orange: ``DECKUNGSGRAD`` 0,70. Das blasse Band zwischen Knie und
                    Abbruch ist der Bereich, in dem die Kniemessung «trägt» sagt und die
                    Kettenmessung «nicht rendern»
    Dreiecke unten  die fünf **hier** gemessenen Bildbreiten der Bilder 02–06, in
                    deren Farben — das Bindeglied zwischen den Rahmen und der Rampe
    Keine Linie     zwischen den Punkten. Absichtlich.

Man sieht: links vier Punkte praktisch bei null (drei davon ohne Score), dann der Sprung
zwischen 0,50 und 0,55 (das Knie), darüber ein stetiger Anstieg; die Schwelle wird
zwischen dem grauen und dem roten Strich überschritten; der orange Strich steht rechts
davon mit sichtbarem Abstand zur Schwelle. Genau das ist der Grund für 0,70.

Was hier NICHT gemessen wird — und das gehört ins Bild
-----------------------------------------------------
Die sieben Stützstellen in Bild 08 stammen **nicht aus diesem Lauf**. Sie wurden am
24.08.2026 auf der HomeStation gemessen (GPU, z-image-turbo, Depth-Anything-V2-Small,
Blender) und werden hier aus ``auftraege/ergebnisse/auf-20260824-37.json`` gelesen —
das ist die Messdatei, aus der die Konstanten ``BILDBREITE_KNIE`` und
``BILDBREITE_ABBRUCH`` abgelesen wurden. Das Skript prüft, dass die Konstanten und die
Datei einander nicht widersprechen; es misst die Rampe nicht neu. Fehlt die Datei, wird
Bild 08 übersprungen und gesagt, warum — nicht gemessen ist etwas anderes als
durchgefallen. Bilder 01–07 sind vollständig in diesem Lauf gerechnet.

    python tools/beweis/10_kamera_rahmung.py [zielordner]
"""
from __future__ import annotations

import json
import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, geometrie_qa, glbbox, kameras  # noqa: E402
from aiimaging.maske import ist_gelaende  # noqa: E402

import make_test_glb  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "10_kamera_rahmung"

#: Die Messdatei der Kniemessung — Stützstellen für Bild 08 und Referenz für die Szene.
MESSDATEI = WURZEL / "auftraege" / "ergebnisse" / "auf-20260824-37.json"

#: Die Reihe. ``DECKUNGSGRAD`` muss darin liegen, sonst zeigt die Serie die Vorgabe nicht.
DECKUNGSGRADE = (0.30, 0.45, 0.55, 0.70, 0.85)

#: Die Szene der Kniemessung: Bauwerk 15,36 × 10,36 × 6,0 m, Platte mit zehnfacher
#: Grundfläche. Namen so, dass ``maske.ist_gelaende`` die Platte erkennt (am Gerät
#: gegengeprüft, auf-36) und das Bauwerk nicht.
BAUWERK_M = (15.36, 10.36, 6.0)
PLATTENVERHAELTNIS = 10.0
PLATTENDICKE_M = 0.5
NAME_BAUWERK = "Bauwerk"
NAME_PLATTE = "Boden_Platte"

# Farben — dieselbe Geländeregel wie in Beweis 01 und 09.
FARBE_LEINWAND = (245, 245, 245)
FARBE_GELAENDE = (222, 206, 170)
FARBE_BAUTEIL = (70, 110, 160)
FARBE_HUELLBOX = (40, 40, 40)
FARBE_MASSSTAB = (60, 60, 60)
FARBE_VORGABE = (230, 120, 40)          # DECKUNGSGRAD — orange, in jedem Bild dieselbe
FARBE_KNIE = (120, 120, 120)            # BILDBREITE_KNIE
FARBE_ABBRUCH = (200, 50, 40)           # BILDBREITE_ABBRUCH und SCHWELLE_GEOMETRIE
FARBE_BAND = (250, 232, 200)            # das Band, in dem sich die Messungen widersprechen

FARBE_RAHMEN = (255, 255, 255)
FARBE_SICHERHEITSRAND = (205, 205, 205)
FARBE_HORIZONT = (170, 170, 170)
FARBE_HUELLE = (200, 220, 240)
FARBE_KANTE = (50, 60, 80)
FARBE_ECKE_DRIN = (50, 160, 70)
FARBE_ECKE_DRAUSSEN = (200, 50, 40)
FARBE_BALKEN = (90, 90, 90)

FARBE_URTEIL = {"rendern": (50, 160, 70), "band": (220, 160, 40), "abbruch": (200, 50, 40)}

#: Fünf Stufen von hell nach dunkel — der Deckungsgrad als Helligkeit.
FARBE_STUFEN = ((160, 190, 220), (120, 160, 200), (85, 130, 180), (55, 100, 155),
                (30, 65, 115))

GRUNDRISS_PX = 900
GRUNDRISS_RAND_PX = 40
RAHMEN_B, RAHMEN_H = 640, 360
RAHMEN_RAND_PX = 20
BALKEN_H = 26                            # Platz unter dem Rahmen für den Breitenbalken
KURVE_B, KURVE_H = 900, 640


# --------------------------------------------------------------------------------------
# Rasterizer — wie in Beweis 09: Scheiben, Strecken, konvexe Polygone. Reine stdlib.
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
    laenge = math.hypot(x1 - x0, y1 - y0)
    schritte = max(1, int(laenge / max(0.5, dicke * 0.5)))
    for i in range(schritte + 1):
        t = i / schritte
        _scheibe(px, breite, hoehe, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                 dicke / 2.0, farbe)


def _gestrichelt(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: float = 1.5,
                 strich: float = 6.0, luecke: float = 5.0) -> None:
    laenge = math.hypot(x1 - x0, y1 - y0)
    if laenge <= 0:
        return
    ex, ey = (x1 - x0) / laenge, (y1 - y0) / laenge
    s = 0.0
    while s < laenge:
        e = min(laenge, s + strich)
        _strecke(px, breite, hoehe, x0 + ex * s, y0 + ey * s, x0 + ex * e, y0 + ey * e,
                 farbe, dicke)
        s = e + luecke


def _pfeil(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: float = 2.0,
           spitze: float = 9.0) -> None:
    _strecke(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke)
    w = math.atan2(y1 - y0, x1 - x0)
    for seite in (+1, -1):
        a = w + math.pi + seite * math.radians(28)
        _strecke(px, breite, hoehe, x1, y1, x1 + spitze * math.cos(a),
                 y1 + spitze * math.sin(a), farbe, dicke)


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    # Beide Kanten in [0, breite] klemmen. Nur eine zu klemmen (wie in Beweis 09) lässt ein
    # Rechteck, das ganz rechts aus dem Bild fällt, in die NÄCHSTE Zeile schreiben —
    # gefunden an einer orangen Marke, die links auftauchte, obwohl sie rechts lag.
    xa, xb = sorted((min(breite, max(0, int(round(x0)))), min(breite, max(0, int(round(x1))))))
    ya, yb = sorted((min(hoehe, max(0, int(round(y0)))), min(hoehe, max(0, int(round(y1))))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: int = 1) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _dreieck(px, breite, hoehe, x, y, groesse: float, farbe) -> None:
    """Spitze nach oben auf (x, y) — die Marke auf einer Achse."""
    _polygon_fuellen(px, breite, hoehe,
                     [(x, y), (x - groesse, y + 1.7 * groesse), (x + groesse, y + 1.7 * groesse)],
                     farbe)


def _konvexe_huelle(punkte) -> list:
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


def _einblenden(px, breite, hoehe, x0, y0, x1, y1, farbe, anteil: float) -> None:
    """Rechteck mit dem Untergrund mischen — für das blasse Band im Kurvenbild."""
    _polygon_fuellen(px, breite, hoehe, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], farbe,
                     anteil=anteil)


# --------------------------------------------------------------------------------------
# Schritt 1 — die Szene der Kniemessung, hier nachgebaut und gegen die Messdatei geprüft
# --------------------------------------------------------------------------------------

def lies_messdatei() -> dict | None:
    """Die Ergebnisdatei der Kniemessung, oder ``None`` mit Begründung auf stderr.

    Fehlt sie, fehlt Bild 08 — und die Szenenprüfung. Beides ist dann *nicht geprüft*,
    nicht *falsch*; das Skript sagt es und rechnet weiter.
    """
    if not MESSDATEI.is_file():
        print(f"NICHT GEPRUEFT: {MESSDATEI.relative_to(WURZEL)} fehlt — Bild 08 (Rampe) "
              f"entfaellt, die Szene wird nicht gegen die Messung geprueft.",
              file=sys.stderr)
        return None
    with MESSDATEI.open(encoding="utf-8") as f:
        d = json.load(f)
    if d.get("status") != "ok" or "frage_b" not in d:
        print(f"NICHT GEPRUEFT: {MESSDATEI.name} traegt keine Frage B mit Status ok.",
              file=sys.stderr)
        return None
    return d


def baue_geometrie(arbeit: Path, messung: dict | None) -> dict:
    """Quader auf Platte → glb → Hüllboxen, Knotenboxen, Geländestand.

    In glTF-Koordinaten (Y oben); ``glbbox.nach_welt`` dreht nach Z oben. Die Platte
    liegt mit ihrer Oberkante auf z = 0, das Bauwerk steht darauf — wie in auf-36/37,
    wo ``gelaende_z`` 0.0 war.
    """
    dx, dy, dz = BAUWERK_M
    seite = math.sqrt(PLATTENVERHAELTNIS * dx * dy)
    koerper = (
        (NAME_PLATTE, (-seite / 2, -PLATTENDICKE_M, -seite / 2), (seite / 2, 0.0, seite / 2)),
        (NAME_BAUWERK, (-dx / 2, 0.0, -dy / 2), (dx / 2, dz, dy / 2)),
    )
    if ist_gelaende(NAME_BAUWERK) or not ist_gelaende(NAME_PLATTE):
        raise SystemExit("Die Geländeregel erkennt die Namen nicht wie am Gerät — "
                         "die Bauwerksbox wäre eine andere.")
    glb = arbeit / "kniemessung.glb"
    glb.write_bytes(make_test_glb.baue_glb(koerper))

    js = glbbox.lies_gltf_json(glb)
    gelesen = glbbox.knotenboxen(js)
    knoten_welt = [(name, *glbbox.nach_welt(lo, hi)) for name, lo, hi in gelesen["knoten"]]
    bau = glbbox.bauwerksbox(glb)
    if bau["bbox_bauwerk"] is None:
        raise SystemExit(f"Keine Bauwerks-Hüllbox: {bau['note']}")
    gelaende = [hi[2] for name, lo, hi in knoten_welt if ist_gelaende(name)]

    # Ist es DIESELBE Szene wie in der Messung? Die Hüllbox aus der glb gegen die Box aus
    # der Messdatei, Zahl für Zahl. Sonst hiesse der Vergleich in Bild 08 nichts.
    if messung is not None:
        soll = messung["frage_b"]["gerechnete_kameras"]["bauwerk_bbox"]
        for a, b in zip(sum(bau["bbox_bauwerk"], []), sum(soll, [])):
            if abs(a - b) > 1e-6:
                raise SystemExit(f"Hüllbox {bau['bbox_bauwerk']} ist nicht die der Messung "
                                 f"{soll} — nicht dieselbe Szene, kein Vergleich.")
        seite_soll = messung["aufbau"]["geometrie_wiederverwendet"]["plattenseite_m"]
        if abs(seite - seite_soll) > 1e-6:
            raise SystemExit(f"Plattenseite {seite} statt {seite_soll}.")

    return {"bbox_bauwerk": bau["bbox_bauwerk"], "bbox_szene": bau["bbox_szene"],
            "knoten_welt": knoten_welt, "gelaende_z": max(gelaende), "plattenseite_m": seite}


# --------------------------------------------------------------------------------------
# Schritt 2 — die Südkamera bei fünf Deckungsgraden
# --------------------------------------------------------------------------------------

def rechne_reihe(geometrie: dict) -> list:
    """Je Deckungsgrad die Südkamera aus ``kamerasatz`` und das Urteil der Rahmung."""
    if not any(abs(d - kameras.DECKUNGSGRAD) < 1e-9 for d in DECKUNGSGRADE):
        raise SystemExit(f"DECKUNGSGRAD ist {kameras.DECKUNGSGRAD}, die Reihe "
                         f"{DECKUNGSGRADE} enthält ihn nicht — die Vorgabe fehlte im Beweis.")
    bbox = geometrie["bbox_bauwerk"]
    reihe = []
    for d in DECKUNGSGRADE:
        satz = kameras.kamerasatz(bbox, gelaende_z=geometrie["gelaende_z"],
                                  deckungsgrad=d, kuerzel=("s",))
        (kam,) = satz["kameras"]
        # Das Urteil mit der GEMESSENEN Breite, Bauwerk = Szene (Anteil 1): So fragt
        # `rahmungsverhaeltnis` genau, ob DIESE Bildbreite über Knie und Abbruch liegt.
        urteil = kameras.rahmungsverhaeltnis(bbox, bbox, deckungsgrad=d,
                                             gemessener_fuellgrad=kam["fuellgrad_breite"])
        if urteil["grundlage"] != "gemessener_fuellgrad":
            raise SystemExit("rahmungsverhaeltnis hat die gemessene Breite nicht genommen.")
        if not urteil["traegt"]:
            wort = "abbruch"
        elif urteil["abbruch"]:
            wort = "band"
        else:
            wort = "rendern"
        reihe.append({"deckungsgrad": d, "kamera": kam, "urteil": urteil, "wort": wort,
                      "vollstaendig": not satz["unvollstaendig"]})
    return reihe


def projiziere_ecken(kam: dict, bbox) -> tuple[list, float]:
    """Acht Ecken einer Box in Rahmenkoordinaten (-0.5 … +0.5 sichtbar), wie in
    ``kameras.flaechenanteil``. Hinter der Kamera: ``None``."""
    basis = kameras._kamerabasis(kam["auge"], kam["blick_auf"])
    if basis is None:
        raise SystemExit("Kamerabasis entartet.")
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
    return ecken, -versatz / grenze_v / 2.0


KANTEN = tuple((a, b) for a in range(8) for b in range(a + 1, 8)
               if bin(a ^ b).count("1") == 1)


def zeichne_rahmen(eintrag: dict, geometrie: dict, *, breite: int = RAHMEN_B,
                   hoehe: int = RAHMEN_H, rand_px: int = RAHMEN_RAND_PX,
                   bildrand: float = kameras.BILDRAND):
    """Rahmen, Platte, Bauwerkshülle, Ecken — und darunter der Balken der Bildbreite."""
    kam = eintrag["kamera"]
    bbox = geometrie["bbox_bauwerk"]
    gesamt_b, gesamt_h = breite + 2 * rand_px, hoehe + 2 * rand_px + BALKEN_H
    px = _neues_bild(gesamt_b, gesamt_h)

    def nach_px(u, w):
        return (rand_px + (u + 0.5) * breite, rand_px + (0.5 - w) * hoehe)

    _rechteck(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
              FARBE_RAHMEN)

    # Die Platte zuerst — was von der Umgebung im Bild bleibt. Nur ihre OBERFLÄCHE: Die
    # Box hat 0,5 m Dicke, und aus 1,7 m Augenhöhe erscheint die Stirnseite als zweites
    # Band unter dem Boden, das nichts über die Rahmung sagt. Die nahen Ecken liegen
    # weit ausserhalb des Rahmens; die Füllung schneidet am Bildrand ab.
    for name, lo, hi in geometrie["knoten_welt"]:
        if ist_gelaende(name):
            platte, _ = projiziere_ecken(kam, ((lo[0], lo[1], hi[2]), hi))
            sichtbar = [nach_px(*e) for e in platte if e is not None]
            _polygon_fuellen(px, gesamt_b, gesamt_h, _konvexe_huelle(sichtbar), FARBE_GELAENDE)
    # Der Rand ausserhalb des Rahmens bleibt Leinwand, auch wenn die Platte darüber ragt.
    _rechteck(px, gesamt_b, gesamt_h, 0, 0, gesamt_b, rand_px, FARBE_LEINWAND)
    _rechteck(px, gesamt_b, gesamt_h, 0, rand_px + hoehe, gesamt_b, gesamt_h, FARBE_LEINWAND)
    _rechteck(px, gesamt_b, gesamt_h, 0, 0, rand_px, gesamt_h, FARBE_LEINWAND)
    _rechteck(px, gesamt_b, gesamt_h, rand_px + breite, 0, gesamt_b, gesamt_h, FARBE_LEINWAND)

    sx0, sy0 = nach_px(-0.5 * bildrand, 0.5 * bildrand)
    sx1, sy1 = nach_px(0.5 * bildrand, -0.5 * bildrand)
    _rahmen(px, gesamt_b, gesamt_h, sx0, sy0, sx1, sy1, FARBE_SICHERHEITSRAND, 1)

    ecken, horizont = projiziere_ecken(kam, bbox)
    if -0.5 <= horizont <= 0.5:
        hx0, hy = nach_px(-0.5, horizont)
        hx1, _ = nach_px(0.5, horizont)
        _strecke(px, gesamt_b, gesamt_h, hx0, hy, hx1, hy, FARBE_HORIZONT, 1.0)

    sichtbar = [nach_px(*e) for e in ecken if e is not None]
    _polygon_fuellen(px, gesamt_b, gesamt_h, _konvexe_huelle(sichtbar), FARBE_HUELLE)
    for a, b in KANTEN:
        if ecken[a] is None or ecken[b] is None:
            continue
        _strecke(px, gesamt_b, gesamt_h, *nach_px(*ecken[a]), *nach_px(*ecken[b]),
                 FARBE_KANTE, 2.0 if (a ^ b) == 1 else 1.4)
    drin = 0
    for e in ecken:
        if e is None:
            continue
        im_rand = abs(e[0]) <= 0.5 * bildrand and abs(e[1]) <= 0.5 * bildrand
        drin += im_rand
        _scheibe(px, gesamt_b, gesamt_h, *nach_px(*e), 4.0,
                 FARBE_ECKE_DRIN if im_rand else FARBE_ECKE_DRAUSSEN)

    # Die Silhouettenbreite aus DIESER Projektion gegen `fuellgrad_breite` aus
    # `kamerasatz`: zwei Rechenwege, eine Zahl. Weichen sie ab, ist eines der beiden
    # Bilder falsch — und dann wird keines geschrieben.
    us = [e[0] for e in ecken if e is not None]
    silhouette = max(us) - min(us)
    if abs(silhouette - kam["fuellgrad_breite"]) > 0.005:
        raise SystemExit(f"Deckungsgrad {eintrag['deckungsgrad']}: projizierte Breite "
                         f"{silhouette:.4f} gegen fuellgrad_breite "
                         f"{kam['fuellgrad_breite']:.4f} — die Zeichnung widerspricht der "
                         f"Rechnung.")

    # Der Balken: die gemessene Bildbreite als Anteil der Rahmenbreite, vom linken
    # Rahmenrand aus. Die drei Marken stehen darum in JEDEM Bild an derselben Stelle —
    # in der Tafel sieht man den Balken von oben nach unten an ihnen vorbeiwachsen.
    y0 = rand_px + hoehe + 8
    _rechteck(px, gesamt_b, gesamt_h, rand_px, y0, rand_px + silhouette * breite, y0 + 10,
              FARBE_BALKEN)
    for wert, farbe in ((kameras.BILDBREITE_KNIE, FARBE_KNIE),
                        (kameras.BILDBREITE_ABBRUCH, FARBE_ABBRUCH),
                        (kameras.DECKUNGSGRAD, FARBE_VORGABE)):
        xm = rand_px + wert * breite
        _rechteck(px, gesamt_b, gesamt_h, xm - 1, y0 - 6, xm + 1, y0 + 16, farbe)

    _rahmen(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
            FARBE_URTEIL[eintrag["wort"]], 3)
    return px, gesamt_b, gesamt_h, drin, silhouette


# --------------------------------------------------------------------------------------
# Schritt 3 — Grundriss mit den fünf Standorten
# --------------------------------------------------------------------------------------

def zeichne_grundriss(geometrie: dict, reihe: list, *, kante_px: int = GRUNDRISS_PX,
                      rand_px: int = GRUNDRISS_RAND_PX):
    bbox = geometrie["bbox_bauwerk"]
    kam0 = reihe[0]["kamera"]
    hfov, _ = kameras.bildwinkel(kam0["brennweite_mm"],
                                 seitenverhaeltnis=kam0["seitenverhaeltnis"])
    xs, ys = [], []
    for ecke in geometrie["bbox_szene"]:
        xs.append(ecke[0]); ys.append(ecke[1])
    for e in reihe:
        ax, ay, _ = e["kamera"]["auge"]
        xs.append(ax); ys.append(ay)
    spanne = max(max(xs) - min(xs), max(ys) - min(ys))
    m_je_px = spanne / (kante_px - 2 * rand_px)
    mx, my = (max(xs) + min(xs)) / 2.0, (max(ys) + min(ys)) / 2.0
    breite = hoehe = kante_px

    def nach_px(x, y):
        return (breite / 2.0 + (x - mx) / m_je_px, hoehe / 2.0 - (y - my) / m_je_px)

    px = _neues_bild(breite, hoehe)
    for name, lo, hi in geometrie["knoten_welt"]:
        if ist_gelaende(name):
            x0, y0 = nach_px(lo[0], hi[1]); x1, y1 = nach_px(hi[0], lo[1])
            _rechteck(px, breite, hoehe, x0, y0, x1, y1, FARBE_GELAENDE)
    for name, lo, hi in geometrie["knoten_welt"]:
        if not ist_gelaende(name):
            x0, y0 = nach_px(lo[0], hi[1]); x1, y1 = nach_px(hi[0], lo[1])
            _rechteck(px, breite, hoehe, x0, y0, x1, y1, FARBE_BAUTEIL)
    x0, y0 = nach_px(bbox[0][0], bbox[1][1]); x1, y1 = nach_px(bbox[1][0], bbox[0][1])
    _rahmen(px, breite, hoehe, x0, y0, x1, y1, FARBE_HUELLBOX, 2)

    # Keile von weit nach nah, damit der nächste Standort obenauf liegt.
    for i, e in enumerate(reihe):
        kam = e["kamera"]
        ax, ay, _ = kam["auge"]; bx, by, _ = kam["blick_auf"]
        w = math.atan2(by - ay, bx - ax)
        laenge = kam["abstand_m"] * 0.33
        keil = [nach_px(ax, ay)] + [nach_px(ax + laenge * math.cos(w + s * hfov / 2.0),
                                            ay + laenge * math.sin(w + s * hfov / 2.0))
                                    for s in (+1, -1)]
        _polygon_fuellen(px, breite, hoehe, keil, FARBE_STUFEN[i], anteil=0.15)
    for i, e in enumerate(reihe):
        kam = e["kamera"]
        ax, ay = nach_px(kam["auge"][0], kam["auge"][1])
        bx, by = nach_px(kam["blick_auf"][0], kam["blick_auf"][1])
        _pfeil(px, breite, hoehe, ax, ay, bx, by, FARBE_STUFEN[i], 1.6)
    for i, e in enumerate(reihe):
        kam = e["kamera"]
        ax, ay = nach_px(kam["auge"][0], kam["auge"][1])
        _scheibe(px, breite, hoehe, ax, ay, 8.0, FARBE_STUFEN[i])
        _ring(px, breite, hoehe, ax, ay, 8.0, FARBE_HUELLBOX, 1.2)
        if abs(e["deckungsgrad"] - kameras.DECKUNGSGRAD) < 1e-9:
            _ring(px, breite, hoehe, ax, ay, 13.0, FARBE_VORGABE, 3.0)

    bx0, by0 = rand_px, hoehe - rand_px
    _rechteck(px, breite, hoehe, bx0, by0 - 4, bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0, by0 - 10, bx0 + 2, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0 + 10.0 / m_je_px - 2, by0 - 10,
              bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _pfeil(px, breite, hoehe, rand_px, rand_px + 34, rand_px, rand_px, FARBE_MASSSTAB, 2.0)
    return px, breite, hoehe, m_je_px


def zeichne_tafel(tafeln: list, *, fuge: int = 8):
    tb, th = tafeln[0][1], tafeln[0][2]
    breite = tb + 2 * fuge
    hoehe = len(tafeln) * th + (len(tafeln) + 1) * fuge
    px = _neues_bild(breite, hoehe, (225, 225, 225))
    for i, (tp, _, _) in enumerate(tafeln):
        y0 = fuge + i * (th + fuge)
        for y in range(th):
            px[(y0 + y) * breite + fuge:(y0 + y) * breite + fuge + tb] = tp[y * tb:(y + 1) * tb]
    return px, breite, hoehe


# --------------------------------------------------------------------------------------
# Schritt 4 — die Rampe mit Knie aus den Stützstellen der Messdatei
# --------------------------------------------------------------------------------------

def stuetzstellen(messung: dict) -> list:
    """Die sieben Stufen aus ``frage_b.je_stufe``, nach Bildbreite sortiert — und die
    Konstanten gegen sie geprüft.

    ``BILDBREITE_KNIE`` **ist** die Bildbreite der Stufe s60, und die Schwelle fällt
    zwischen s60 und s65. Steht das anders in der Datei, sind die Konstanten
    abgeschrieben und nicht abgelesen — dann wird kein Bild daraus.
    """
    stufen = messung["frage_b"]["je_stufe"]
    punkte = sorted(({"stufe": k, "bildbreite": float(v["fuellgrad_breite"]),
                      "geom_iou": float(v["geom_iou"]),
                      "score": (None if v["geometrie_score"] is None
                                else float(v["geometrie_score"])),
                      "bestanden": bool(v["bestanden"]),
                      "n_gemeinsam": int(v["n_gemeinsam"]),
                      "anteil_maske": float(v["anteil_maske"])}
                     for k, v in stufen.items()), key=lambda p: p["bildbreite"])

    def stufe(name):
        return next(p for p in punkte if p["stufe"] == name)

    if abs(stufe("s60")["bildbreite"] - kameras.BILDBREITE_KNIE) > 5e-5:
        raise SystemExit(f"BILDBREITE_KNIE {kameras.BILDBREITE_KNIE} ist nicht die Bildbreite "
                         f"von s60 ({stufe('s60')['bildbreite']}).")
    if not (stufe("s60")["score"] < geometrie_qa.SCHWELLE_GEOMETRIE <= stufe("s65")["score"]):
        raise SystemExit("Die Schwelle fällt in der Messdatei nicht zwischen s60 und s65.")
    if stufe("s60")["bestanden"] or not stufe("s65")["bestanden"]:
        raise SystemExit("bestanden-Flaggen von s60/s65 widersprechen dem Knie.")
    for p in punkte:
        if (p["score"] is None) != (p["n_gemeinsam"] < geometrie_qa.MIN_GEMEINSAME_PUNKTE):
            raise SystemExit(f"{p['stufe']}: Score fehlt nicht genau dann, wenn "
                             f"n_gemeinsam unter {geometrie_qa.MIN_GEMEINSAME_PUNKTE} liegt.")
    # Die grobe Tabelle in geometrie_qa.RAHMUNG_GEMESSEN ist dieselbe Messung in
    # Maskenanteil — jeder ihrer Punkte muss hier wiederzufinden sein.
    for anteil, iou in geometrie_qa.RAHMUNG_GEMESSEN:
        if not any(abs(p["anteil_maske"] - anteil) < 5e-5 and abs(p["geom_iou"] - iou) < 5e-4
                   for p in punkte):
            raise SystemExit(f"RAHMUNG_GEMESSEN-Punkt ({anteil}, {iou}) steht nicht in der "
                             f"Messdatei.")
    return punkte


def zeichne_rampe(punkte: list, reihe: list, *, breite: int = KURVE_B, hoehe: int = KURVE_H):
    """Zwei Felder, gemeinsame x-Achse, Punkte ohne Verbindungslinie."""
    px = _neues_bild(breite, hoehe, FARBE_RAHMEN)
    links, rechts = 70, breite - 40
    feld_h = (hoehe - 140) // 2
    felder = [(50, 50 + feld_h), (50 + feld_h + 40, 50 + 2 * feld_h + 40)]

    def x_von(b):
        return links + b * (rechts - links)

    for oben, unten in felder:
        def y_von(w, oben=oben, unten=unten):
            return unten - w * (unten - oben)

        # Das Band Knie–Abbruch, blass, unter allem anderen.
        _einblenden(px, breite, hoehe, x_von(kameras.BILDBREITE_KNIE), oben,
                    x_von(kameras.BILDBREITE_ABBRUCH), unten, FARBE_BAND, 0.7)
        _rahmen(px, breite, hoehe, links, oben, rechts, unten, FARBE_KNIE, 1)
        for i in range(11):
            t = i / 10
            lang = 12 if i in (0, 5, 10) else 6
            _rechteck(px, breite, hoehe, x_von(t) - 0.5, unten, x_von(t) + 0.5, unten + lang,
                      FARBE_KNIE)
            _rechteck(px, breite, hoehe, links - lang, y_von(t) - 0.5, links, y_von(t) + 0.5,
                      FARBE_KNIE)
        for wert, farbe in ((kameras.BILDBREITE_KNIE, FARBE_KNIE),
                            (kameras.BILDBREITE_ABBRUCH, FARBE_ABBRUCH),
                            (kameras.DECKUNGSGRAD, FARBE_VORGABE)):
            _gestrichelt(px, breite, hoehe, x_von(wert), oben, x_von(wert), unten, farbe, 2.0)

    # Oberes Feld: geom_iou. Unteres Feld: Score mit Schwelle.
    (o1, u1), (o2, u2) = felder
    y_s = u2 - geometrie_qa.SCHWELLE_GEOMETRIE * (u2 - o2)
    _strecke(px, breite, hoehe, links, y_s, rechts, y_s, FARBE_ABBRUCH, 2.0)
    for p in punkte:
        x = x_von(p["bildbreite"])
        farbe = FARBE_ECKE_DRIN if p["bestanden"] else FARBE_ECKE_DRAUSSEN
        _scheibe(px, breite, hoehe, x, u1 - p["geom_iou"] * (u1 - o1), 6.0, farbe)
        if p["score"] is None:
            _ring(px, breite, hoehe, x, u2, 6.0, FARBE_KNIE, 2.0)
        else:
            _scheibe(px, breite, hoehe, x, u2 - p["score"] * (u2 - o2), 6.0, farbe)

    # Die fünf hier gemessenen Bildbreiten der Rahmenbilder, als Dreiecke auf der Achse.
    for i, e in enumerate(reihe):
        _dreieck(px, breite, hoehe, x_von(e["kamera"]["fuellgrad_breite"]), u2 + 16, 7.0,
                 FARBE_STUFEN[i])
    return px, breite, hoehe


# --------------------------------------------------------------------------------------

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    messung = lies_messdatei()
    with tempfile.TemporaryDirectory(prefix="beweis10_") as tmp:
        geometrie = baue_geometrie(Path(tmp), messung)
    reihe = rechne_reihe(geometrie)

    # -- 01 Grundriss --
    px, b, h, m_je_px = zeichne_grundriss(geometrie, reihe)
    abstaende = "_".join(f"{e['kamera']['abstand_m']:.1f}m" for e in reihe)
    pfad = ziel / (f"01_grundriss_suedkamera-bei-deckungsgrad-"
                   f"{'-'.join(f'{d:.2f}' for d in DECKUNGSGRADE)}_abstand-{abstaende}_"
                   f"vorgabe-{kameras.DECKUNGSGRAD:.2f}_massstab-{m_je_px:.3f}m-je-px.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 02..06 je Deckungsgrad --
    tafeln = []
    for i, e in enumerate(reihe):
        kam = e["kamera"]
        px, b, h, drin, silhouette = zeichne_rahmen(e, geometrie)
        vorgabe = "_VORGABE" if abs(e["deckungsgrad"] - kameras.DECKUNGSGRAD) < 1e-9 else ""
        pfad = ziel / (f"{i + 2:02d}_rahmen_deckungsgrad-{e['deckungsgrad']:.2f}{vorgabe}_"
                       f"bildbreite-gemessen-{kam['fuellgrad_breite']:.3f}_"
                       f"flaeche-{kam['flaechenanteil']:.3f}_abstand-{kam['abstand_m']:.1f}m_"
                       f"massgebend-{kam['massgebend']}_ecken-{drin}von8_"
                       f"urteil-{e['wort']}.png")
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)
        tafeln.append((px, b, h))

    # -- 07 Tafel --
    px, b, h = zeichne_tafel(tafeln)
    pfad = ziel / (f"07_tafel_fuenf-deckungsgrade_knie-{kameras.BILDBREITE_KNIE:.4f}_"
                   f"abbruch-{kameras.BILDBREITE_ABBRUCH:.2f}_"
                   f"urteile-{'-'.join(e['wort'] for e in reihe)}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 08 Rampe mit Knie -- nur mit der Messdatei; ohne sie: nicht gemessen, nicht falsch.
    if messung is not None:
        punkte = stuetzstellen(messung)
        px, b, h = zeichne_rampe(punkte, reihe)
        pfad = ziel / (f"08_rampe-mit-knie_stuetzstellen-{len(punkte)}_"
                       f"gemessen-homestation-{messung['beendet'][:10]}_{messung['auftrag_id']}_"
                       f"knie-{kameras.BILDBREITE_KNIE:.4f}_abbruch-{kameras.BILDBREITE_ABBRUCH:.2f}_"
                       f"vorgabe-{kameras.DECKUNGSGRAD:.2f}_"
                       f"schwelle-{geometrie_qa.SCHWELLE_GEOMETRIE:.2f}_nicht-interpoliert.png")
        bildschreiben.schreibe_farb_png(pfad, px, b, h)
        geschrieben.append(pfad)
    else:
        print("08 übersprungen: keine Messdatei — Rampe NICHT GEMESSEN.", file=sys.stderr)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
