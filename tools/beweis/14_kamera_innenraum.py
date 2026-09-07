#!/usr/bin/env python3
"""BEWEIS 14 — Die automatische Kamerasetzung, Teil 6: **innen**. ``raumkamera.standpunkte``
rechnet aus einem ``IfcSpace`` **beide** Blickarten — frontal und über Eck —, und die
frontale ist von einer Fläche beherrscht (56,9 % / 78,8 % des Bildes auf EINER
Tiefenebene), die über Eck nicht (0,5 % / 0,6 %).

Was bewiesen wird
-----------------
1. **Aus dem Raum werden Standpunkte, nicht aus der Hüllbox.** Die Geometrie entsteht
   hier (``tools/make_test_ifc.py --raeume``, Regel 3), die Räume werden über die
   Prozessgrenze gelesen (``seams.ifc_raeume``, ifcopenshell im ``.venv-ifc``), und
   ``raumkamera.standpunkte`` rechnet je Raum beide Blickarten. Kein Punkt in den
   Grundrissbildern ist gesetzt: Polygon, Auge, Blickziel, Öffnungswinkel und die am
   Zielwandende sichtbare Breite kommen alle aus dem Aufruf.
2. **Beide Blickarten liegen verschieden** — der Owner-Entscheid vom 22.08.2026 (es
   wird beides gerechnet, gewählt wird anderswo) in einem Bild je Raum.
3. **Die frontale Ansicht fasst die Zielwand nicht immer.** Im L-förmigen Raum steht
   die Kamera 4,10 m vor einer 7,40 m breiten Wand und sieht bei 24 mm davon 6,15 m;
   der ungedeckte Rest der Wand ist im Bild markiert, die nötige Brennweite steht im
   Dateinamen. Das ist ``raumkamera._sichtfeld`` — gezeichnet, nicht behauptet.
4. **Frontal ist von einer Fläche beherrscht, über Eck nicht** — die Messung vom
   09.09.2026 (``docs/INNENANSICHT_2026-09-09.md``) als Balkenbild. Sie wird in diesem
   Lauf **neu gemessen**, wenn Blender und das ``.venv-ifc`` da sind (über
   ``tools/studie_innenansicht.messe``, dieselbe Funktion, die die belegten Zahlen
   erzeugt hat); sonst werden die belegten Zahlen aus dem Dokument gelesen und **als
   belegt gekennzeichnet** — schraffiert im Bild, ``belegt`` im Dateinamen.

Woran man es im Bild sieht
--------------------------
Farben, in allen Bildern dieselben: **rot** frontal, **blau** über Eck; dunkelgrau
die Wände, ein 1-m-Balken links unten als Massstab (der Massstab steht auch im Dateinamen,
``m-je-px``).

``01_uebersicht_…png`` — beide Räume im selben Massstab, alle vier Standpunkte. Auge als
volle Scheibe, Blickziel als Ring, Blickachse als Linie, Sichtfeld als gefüllter Kegel
(auf den Raum beschnitten — was hinter einer Wand liegt, sieht die Kamera nicht).
Man sieht: Der frontale Standpunkt steht auf der **Mittelachse** der längsten Wand, an der
gegenüberliegenden Wand mit 0,30 m Abstand; der Über-Eck-Standpunkt sitzt **in einer
vorspringenden Ecke** und blickt diagonal. Beide Kegel sind gleich weit geöffnet (24 mm),
liegen aber verschieden.

``02_raum-…png`` / ``03_raum-…png`` — je Raum allein, grösser. Die **Zielwand** der
frontalen Aufnahme trägt zwei Farben: rot der Teil, den der Kegel bei 24 mm fasst, orange
der Rest, den er **nicht** fasst. Ist die Wand ganz rot, sagt der Dateiname
``passt-ja``; sonst ``passt-nein`` und die nötige Brennweite.

``04_tiefenebenen_…png`` — je Raum vier Balken: frontal 24 mm, frontal 50 mm (Rückfall
des Runners), über Eck 24 mm, über Eck 50 mm. Balkenlänge ist der Anteil des **ganzen**
Bildes, der auf *einer* Tiefenebene (1 cm) liegt. Marker links: Blickart in ihrer
Farbe, hohl bei der Rückfall-Brennweite. Balkenfarbe: **rotbraun** ab
``studie_innenansicht.BEHERRSCHT_AB`` (0,50, die rote Senkrechte), sonst **grün**.
**Vollflächig** heisst in diesem Lauf gemessen; **schraffiert** heisst belegt aus dem
Dokument. Wurde gemessen, liegt unter jedem vollen Balken der belegte als schmaler
schraffierter Balken — sind beide gleich lang, stimmt die Messung mit dem Dokument
überein. Feine Striche oben: 0,1-Schritte.
Man sieht: Die beiden frontalen 24-mm-Balken laufen weit über die rote Senkrechte, die
beiden Über-Eck-Balken sind kaum sichtbar — Faktor über hundert, in beiden Räumen.
Die 50-mm-Balken der frontalen Aufnahme reichen fast oder ganz bis zum Rand: Das ist
Befund 2 des Dokuments, der Rückfall macht die Aufnahme unmessbar.

Was hier NICHT gemessen wird
----------------------------
ρ — die Rangkorrelation gegen den Tiefenschätzer — braucht ``torch`` und ein Gewicht
und ist die Frage von ``auf-20260909-89`` am Gerät. Hier steht nur die **Vorprüfung**:
ob die Soll-Karte überhaupt eine Ordnung trägt. Und die Testräume haben keine Decke
(siehe das Dokument): Was eine Decke zur Tiefenordnung beiträgt, bleibt ungeprüft.

Was das Gerät braucht: **nichts**. Blender läuft auf der CPU (acht Läufe zu 800 × 496,
8 Samples, je wenige Sekunden). Ohne Blender wird Bild 04 aus den belegten Zahlen
gezeichnet und sagt es; ohne ``.venv-ifc`` gibt es keine Räume und damit keine Bilder
01–03 — dann steht NICHT GEMESSEN, nicht durchgefallen.

    python tools/beweis/14_kamera_innenraum.py [zielordner] [--ohne-blender]
"""
from __future__ import annotations

import argparse
import math
import re
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, raumkamera, seams  # noqa: E402

import make_test_ifc  # noqa: E402
import studie_innenansicht  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "14_kamera_innenraum"
BELEGT_DOKUMENT = WURZEL / "docs" / "INNENANSICHT_2026-09-09.md"

# Dieselben Bildmasse wie die Studie vom 09.09.2026. Das Seitenverhältnis geht in den
# Standpunkt ein (`seitenverhaeltnis`) und in den Anteil auf der grössten Ebene — bei
# 4:3 gemessen kämen andere Zahlen heraus, und die wären keine Wiederholung der Messung.
BREITE = 800
HOEHE = 496
SAMPLES = 8

#: Sensorbreite, mit der der Öffnungswinkel gerechnet wird — dieselbe wie in `raumkamera`.
SENSOR_BREITE_MM = raumkamera.SENSOR_BREITE_MM

# Leinwand der Grundrisse.
PLAN_B, PLAN_H, RAND = 800, 600, 48

GRUND = (243, 243, 241)
WAND = (60, 66, 74)
FRONTAL = (200, 60, 48)
ECK = (60, 110, 200)
FEHLT = (232, 150, 40)        # der Teil der Zielwand, den der Kegel nicht fasst
MASSSTAB = (110, 114, 120)
BEHERRSCHT = (170, 70, 50)
ORDNET = (70, 130, 90)
SCHWELLE = (200, 40, 40)
TICK = (170, 172, 176)
FARBE_JE_ART = {raumkamera.ART_FRONTAL: FRONTAL, raumkamera.ART_UEBER_ECK: ECK}


# ── Zeichnen, reine Listen ────────────────────────────────────────────────────────────

def _leinwand(breite, hoehe, farbe=GRUND):
    return [list(farbe) for _ in range(breite * hoehe)]


def _setze(bild, breite, hoehe, x, y, farbe, alpha=1.0):
    if 0 <= x < breite and 0 <= y < hoehe:
        if alpha >= 1.0:
            bild[y * breite + x] = list(farbe)
        else:
            alt = bild[y * breite + x]
            bild[y * breite + x] = [round(a * (1 - alpha) + f * alpha)
                                    for a, f in zip(alt, farbe)]


def _scheibe(bild, breite, hoehe, x, y, r, farbe, *, hohl=False):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d2 = dx * dx + dy * dy
            if d2 <= r * r and (not hohl or d2 >= (r - 2) * (r - 2)):
                _setze(bild, breite, hoehe, x + dx, y + dy, farbe)


def _linie(bild, breite, hoehe, a, b, farbe, dicke=1):
    x0, y0 = a
    x1, y1 = b
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = dicke // 2
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                _setze(bild, breite, hoehe, x + dx, y + dy, farbe)


def _abbildung(polygone, breite, hoehe, rand=RAND):
    """Weltkoordinaten ↔ Bildkoordinaten. **Massstabstreu** in beiden Achsen, y nach oben.

    Returns ``(ab, zurueck, m_je_px)``. Der Massstab steht im Dateinamen: Ein Grundriss,
    dessen Massstab niemand kennt, ist eine Skizze.
    """
    xs = [p[0] for poly in polygone for p in poly]
    ys = [p[1] for poly in polygone for p in poly]
    dx = (max(xs) - min(xs)) or 1.0
    dy = (max(ys) - min(ys)) or 1.0
    px_je_m = min((breite - 2 * rand) / dx, (hoehe - 2 * rand) / dy)
    x0 = min(xs) - ((breite - 2 * rand) / px_je_m - dx) / 2
    y0 = min(ys) - ((hoehe - 2 * rand) / px_je_m - dy) / 2

    def ab(p):
        return (round(rand + (p[0] - x0) * px_je_m),
                round(hoehe - rand - (p[1] - y0) * px_je_m))

    def zurueck(x, y):
        return ((x - rand) / px_je_m + x0, (hoehe - rand - y) / px_je_m + y0)

    return ab, zurueck, 1.0 / px_je_m


def _massstab(bild, breite, hoehe, ab, zurueck):
    """Ein 1-m-Balken links unten, aus derselben Abbildung wie der Grundriss."""
    x_welt, y_welt = zurueck(RAND // 2, hoehe - RAND // 2)
    a = ab((x_welt, y_welt))
    b = ab((x_welt + 1.0, y_welt))
    _linie(bild, breite, hoehe, a, b, MASSSTAB, 3)
    for p in (a, b):
        _linie(bild, breite, hoehe, (p[0], p[1] - 5), (p[0], p[1] + 5), MASSSTAB, 1)


def _halbwinkel(stand: dict) -> tuple[float, float]:
    """Halber Öffnungswinkel aus der Brennweite, die im Standpunkt steht — nicht gesetzt."""
    f = (stand.get("sichtfeld") or {}).get("brennweite_mm") or raumkamera.BRENNWEITE_INNEN_MM
    return math.atan(SENSOR_BREITE_MM / (2.0 * f)), f


def _kreuzt(a, b, c, d) -> bool:
    """Schneiden sich die Strecken a–b und c–d im Inneren? Berührung zählt nicht."""
    def dreh(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = dreh(c, d, a), dreh(c, d, b)
    d3, d4 = dreh(a, b, c), dreh(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) \
        and d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0


def _sieht(auge, punkt, polygon) -> bool:
    """Liegt zwischen Auge und Punkt keine Wand? Das Auge steht im Raum (Wandabstand
    ≥ 0,30 m, von `raumkamera` gesichert); ein Punkt, den die Strecke ohne Wandkreuzung
    erreicht, liegt dann ebenfalls im Raum — und ist von dort zu sehen."""
    n = len(polygon)
    for i in range(n):
        if _kreuzt(auge, punkt, polygon[i], polygon[(i + 1) % n]):
            return False
    return True


def _kegel(bild, breite, hoehe, ab, zurueck, polygon, stand, farbe, m_je_px):
    """Sichtfeld als gefüllter Kegel, **an den Wänden beschnitten**.

    Je Bildpunkt: liegt er innerhalb des halben Öffnungswinkels um die Blickachse, und
    kreuzt die Strecke vom Auge dorthin keine Wand (`_sieht`)? Dann wird er eingefärbt.
    Das ist das Sichtbarkeitspolygon des Grundrisses im Kegel — was hinter der
    einspringenden Ecke des L-Raums liegt, bleibt weiss. Was die Kamera in der Höhe
    sieht (Boden, Decke), steht nicht im Grundriss; das ist die Messung in Bild 04.
    """
    auge, blick = stand["auge"], stand["blick_auf"]
    halb, _f = _halbwinkel(stand)
    achse = math.atan2(blick[1] - auge[1], blick[0] - auge[0])
    a2 = auge[:2]
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    x_min, y_min = ab((min(xs), max(ys)))
    x_max, y_max = ab((max(xs), min(ys)))
    for y in range(max(0, y_min), min(hoehe, y_max + 1)):
        for x in range(max(0, x_min), min(breite, x_max + 1)):
            wx, wy = zurueck(x, y)
            dx, dy = wx - auge[0], wy - auge[1]
            if math.hypot(dx, dy) < 1e-9:
                continue
            w = (math.atan2(dy, dx) - achse + math.pi) % (2 * math.pi) - math.pi
            if abs(w) <= halb and _sieht(a2, (wx, wy), polygon):
                _setze(bild, breite, hoehe, x, y, farbe, alpha=0.22)
    # Die Kegelkanten, abgeschritten bis zur ersten Wand.
    laengste = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    for seite in (-1, 1):
        w = achse + seite * halb
        richtung = (math.cos(w), math.sin(w))
        t, ende = 0.0, a2
        while t <= laengste:
            p = (a2[0] + richtung[0] * t, a2[1] + richtung[1] * t)
            if not _sieht(a2, p, polygon):
                break
            ende, t = p, t + m_je_px
        _linie(bild, breite, hoehe, ab(a2), ab(ende), farbe, 1)


def _zielwand(bild, breite, hoehe, ab, stand):
    """Die Zielwand der frontalen Aufnahme: gefasst in Rot, ungefasst in Orange."""
    zw = stand.get("zielwand")
    if not zw:
        return
    a, b = zw["von"], zw["bis"]
    laenge = zw["laenge_m"]
    sichtbar = (stand.get("sichtfeld") or {}).get("sichtbare_breite_m") or 0.0
    mitte = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    u = ((b[0] - a[0]) / laenge, (b[1] - a[1]) / laenge)
    halb = min(sichtbar, laenge) / 2
    _linie(bild, breite, hoehe, ab(a), ab(b), FEHLT, 7)
    _linie(bild, breite, hoehe,
           ab((mitte[0] - u[0] * halb, mitte[1] - u[1] * halb)),
           ab((mitte[0] + u[0] * halb, mitte[1] + u[1] * halb)), FRONTAL, 7)


def _standpunkt(bild, breite, hoehe, ab, zurueck, polygon, stand, m_je_px):
    farbe = FARBE_JE_ART[stand["art"]]
    _kegel(bild, breite, hoehe, ab, zurueck, polygon, stand, farbe, m_je_px)
    if stand["art"] == raumkamera.ART_FRONTAL:
        _zielwand(bild, breite, hoehe, ab, stand)
    auge, blick = stand["auge"], stand["blick_auf"]
    _linie(bild, breite, hoehe, ab(auge[:2]), ab(blick[:2]), farbe, 2)
    _scheibe(bild, breite, hoehe, *ab(blick[:2]), 6, farbe, hohl=True)
    _scheibe(bild, breite, hoehe, *ab(auge[:2]), 7, farbe)


def _waende(bild, breite, hoehe, ab, polygon):
    for i in range(len(polygon)):
        _linie(bild, breite, hoehe, ab(polygon[i]), ab(polygon[(i + 1) % len(polygon)]),
               WAND, 3)


def _rein(text) -> str:
    return "".join(c if c.isalnum() else "-" for c in str(text or "ohne-name"))


# ── Die Bilder ────────────────────────────────────────────────────────────────────────

def zeichne_uebersicht(ziel: Path, eintraege: list[tuple[dict, dict]]) -> Path:
    """Beide Räume, alle brauchbaren Standpunkte, ein Massstab."""
    polygone = [raumkamera._als_polygon(r["grundriss_m"]) for r, _ in eintraege]
    ab, zurueck, m_je_px = _abbildung(polygone, PLAN_B, PLAN_H)
    bild = _leinwand(PLAN_B, PLAN_H)
    for polygon, (raum, punkte) in zip(polygone, eintraege):
        for stand in punkte["standpunkte"]:
            if stand["auge"] is not None:
                _standpunkt(bild, PLAN_B, PLAN_H, ab, zurueck, polygon, stand, m_je_px)
    for polygon in polygone:
        _waende(bild, PLAN_B, PLAN_H, ab, polygon)
    _massstab(bild, PLAN_B, PLAN_H, ab, zurueck)
    teile = []
    for raum, punkte in eintraege:
        for s in punkte["standpunkte"]:
            if s["auge"] is not None:
                teile.append(f"{_rein(raum['name'])}-{_rein(s['art'])}-auge-"
                             f"{s['auge'][0]:.2f}-{s['auge'][1]:.2f}-{s['auge'][2]:.3f}")
    pfad = ziel / (f"01_uebersicht_{len(eintraege)}-raeume_"
                   f"{sum(p['n_brauchbar'] for _, p in eintraege)}-standpunkte_"
                   f"{'_'.join(teile)}_massstab-{m_je_px:.4f}m-je-px.png")
    bildschreiben.schreibe_farb_png(pfad, bild, PLAN_B, PLAN_H)
    return pfad


def zeichne_raum(ziel: Path, nr: int, raum: dict, punkte: dict) -> Path:
    polygon = raumkamera._als_polygon(raum["grundriss_m"])
    ab, zurueck, m_je_px = _abbildung([polygon], PLAN_B, PLAN_H)
    bild = _leinwand(PLAN_B, PLAN_H)
    stand = {s["art"]: s for s in punkte["standpunkte"]}
    for s in punkte["standpunkte"]:
        if s["auge"] is not None:
            _standpunkt(bild, PLAN_B, PLAN_H, ab, zurueck, polygon, s, m_je_px)
    _waende(bild, PLAN_B, PLAN_H, ab, polygon)
    _massstab(bild, PLAN_B, PLAN_H, ab, zurueck)

    teile = [f"{nr:02d}_raum-{_rein(raum['name'])}_{raum['flaeche_m2']:.2f}m2_"
             f"hoehe-{raum['hoehe_m']:.2f}m"]
    f = stand[raumkamera.ART_FRONTAL]
    if f["auge"] is not None:
        sf = f["sichtfeld"]
        teile.append(f"frontal-auge-{f['auge'][0]:.2f}-{f['auge'][1]:.2f}-{f['auge'][2]:.3f}_"
                     f"abstand-{f['abstand_m']:.2f}m_zielwand-{f['zielwand']['laenge_m']:.2f}m_"
                     f"sichtbar-{sf['sichtbare_breite_m']:.2f}m_"
                     f"passt-{'ja' if sf['passt'] else 'nein'}"
                     + (f"_noetig-{sf['noetige_brennweite_mm']:.0f}mm"
                        if sf["noetige_brennweite_mm"] else ""))
    else:
        teile.append("frontal-KEIN-STANDPUNKT")
    e = stand[raumkamera.ART_UEBER_ECK]
    if e["auge"] is not None:
        teile.append(f"eck-auge-{e['auge'][0]:.2f}-{e['auge'][1]:.2f}-{e['auge'][2]:.3f}_"
                     f"sichtweite-{e['sichtweite_m']:.2f}m")
    else:
        teile.append("eck-KEIN-STANDPUNKT")
    teile.append(f"brennweite-{raumkamera.BRENNWEITE_INNEN_MM:.0f}mm_"
                 f"massstab-{m_je_px:.4f}m-je-px")
    pfad = ziel / ("_".join(teile) + ".png")
    bildschreiben.schreibe_farb_png(pfad, bild, PLAN_B, PLAN_H)
    return pfad


# ── Tiefenebenen: neu messen oder belegt lesen ────────────────────────────────────────

_ZEILE = re.compile(
    r"^(Raum-\S+)\s+(\S+)\s+(\d+) mm \((\w+)\)\s+([\d.]+)%\s+([\d.]+)\s+(\d+)\s+([\d.]+)%")


def lies_belegt(dokument: Path = BELEGT_DOKUMENT) -> list[dict]:
    """Die Tabelle aus dem Dokument vom 09.09.2026 — gelesen, nicht abgeschrieben.

    Stünden die Zahlen als Konstante hier, könnten Dokument und Beweis auseinanderlaufen,
    ohne dass es jemand merkt. Fehlt das Dokument, gibt es keine belegten Zahlen — und
    kein Bild aus geratenen.
    """
    if not dokument.is_file():
        return []
    zeilen = []
    for zeile in dokument.read_text(encoding="utf-8").splitlines():
        m = _ZEILE.match(zeile.strip())
        if m:
            zeilen.append({"raum": m.group(1), "blick": m.group(2),
                           "brennweite_mm": float(m.group(3)), "quelle": m.group(4),
                           "geometrieanteil": float(m.group(5)) / 100,
                           "spanne_m": float(m.group(6)), "stufen": int(m.group(7)),
                           "groesste_ebene_anteil": float(m.group(8)) / 100,
                           "status": "ok"})
    return zeilen


def messe_neu(arbeit: Path) -> list[dict] | None:
    """Dieselbe Messung wie am 09.09.2026 — dieselbe Funktion, dieselben Masse.

    ``None`` heisst NICHT GEMESSEN: Blender oder das ``.venv-ifc`` fehlen. Das ist kein
    Fehlschlag, und es steht im Bild als Schraffur.
    """
    try:
        seams.finde_blender()
        seams.finde_ifc_python()
    except seams.SeamError as e:
        print(f"NICHT GEMESSEN — {e}")
        return None
    return studie_innenansicht.messe(breite=BREITE, hoehe=HOEHE, samples=SAMPLES,
                                     arbeit=arbeit)


def _schluessel(z: dict) -> tuple:
    return (z["raum"], z["blick"], z["quelle"])


def _schraffiert(bild, breite, hoehe, x0, y0, x1, y1, farbe):
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x + y) % 6 < 2:
                _setze(bild, breite, hoehe, x, y, farbe)


def _voll(bild, breite, hoehe, x0, y0, x1, y1, farbe, alpha=1.0):
    for y in range(y0, y1):
        for x in range(x0, x1):
            _setze(bild, breite, hoehe, x, y, farbe, alpha)


def zeichne_tiefenebenen(ziel: Path, raeume: list[str], gemessen: list[dict] | None,
                         belegt: list[dict]) -> Path | None:
    """Je Raum vier Balken. Voll = in diesem Lauf gemessen, schraffiert = belegt."""
    if gemessen is None and not belegt:
        print("04 übersprungen: weder Messung noch Dokument — Tiefenebenen NICHT GEMESSEN.",
              file=sys.stderr)
        return None
    reihen = [(r, b, q) for r in raeume
              for b in (raumkamera.ART_FRONTAL, raumkamera.ART_UEBER_ECK)
              for q in ("raumkamera", "Rueckfall")]
    neu = {_schluessel(z): z for z in (gemessen or []) if z.get("status") == "ok"}
    alt = {_schluessel(z): z for z in belegt}

    links, rechts, oben, zeile, luecke = 70, 30, 34, 44, 16
    b = BREITE
    h = oben + len(reihen) * zeile + (len(raeume) - 1) * luecke + 20
    bild = _leinwand(b, h)
    spur = b - links - rechts

    def x_von(anteil):
        return links + round(spur * anteil)

    for zehntel in range(11):
        x = x_von(zehntel / 10)
        _linie(bild, b, h, (x, oben - 14), (x, oben - 6), TICK, 1)
    _voll(bild, b, h, links, oben - 2, b - rechts, h - 18, (250, 250, 249))
    xs = x_von(studie_innenansicht.BEHERRSCHT_AB)
    _linie(bild, b, h, (xs, oben - 14), (xs, h - 18), SCHWELLE, 3)

    werte_im_namen = []
    y = oben
    for i, (raum, blick, quelle) in enumerate(reihen):
        if i and reihen[i - 1][0] != raum:
            y += luecke
        farbe_art = FARBE_JE_ART[blick]
        _scheibe(bild, b, h, links - 28, y + zeile // 2, 8, farbe_art,
                 hohl=(quelle == "Rueckfall"))
        n = neu.get((raum, blick, quelle))
        a = alt.get((raum, blick, quelle))
        wert = n["groesste_ebene_anteil"] if n else (a["groesste_ebene_anteil"] if a else None)
        if wert is None:
            # Weder gemessen noch belegt: ein hohler Ring auf der Nulllinie, wie in
            # Beweis 10 — nicht «0 %», sondern «keine Zahl».
            _scheibe(bild, b, h, x_von(0) + 8, y + zeile // 2, 8, MASSSTAB, hohl=True)
            werte_im_namen.append("nicht-gemessen")
            y += zeile
            continue
        farbe = BEHERRSCHT if wert >= studie_innenansicht.BEHERRSCHT_AB else ORDNET
        if n is not None:
            x1 = max(x_von(0) + 2, x_von(n["groesste_ebene_anteil"]))
            if quelle == "Rueckfall":
                _voll(bild, b, h, x_von(0), y + 6, x1, y + zeile - 14, farbe, alpha=0.45)
            else:
                _voll(bild, b, h, x_von(0), y + 6, x1, y + zeile - 14, farbe)
            if a is not None:
                # Der belegte Wert als schmaler schraffierter Balken darunter.
                xa = max(x_von(0) + 2, x_von(a["groesste_ebene_anteil"]))
                _schraffiert(bild, b, h, x_von(0), y + zeile - 12, xa, y + zeile - 4, WAND)
            werte_im_namen.append(f"{100 * n['groesste_ebene_anteil']:.1f}pct")
        else:
            x1 = max(x_von(0) + 2, x_von(a["groesste_ebene_anteil"]))
            _schraffiert(bild, b, h, x_von(0), y + 6, x1, y + zeile - 6, farbe)
            werte_im_namen.append(f"{100 * a['groesste_ebene_anteil']:.1f}pct")
        y += zeile

    quelle = ("gemessen-in-diesem-lauf" if gemessen is not None
              else "belegt-INNENANSICHT-2026-09-09_nicht-neu-gemessen")
    name = (f"04_tiefenebenen_groesste-ebene-anteil_{quelle}_"
            f"reihen-je-raum-frontal24-frontal50-eck24-eck50_"
            + "_".join(f"{_rein(r)}-" + "-".join(werte_im_namen[4 * k:4 * k + 4])
                       for k, r in enumerate(raeume))
            + f"_schwelle-{studie_innenansicht.BEHERRSCHT_AB:.2f}.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, bild, b, h)
    return pfad


# ── Ablauf ────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("ziel", nargs="?", default=str(ZIEL_VORGABE))
    p.add_argument("--ohne-blender", action="store_true",
                   help="Tiefenebenen nicht neu messen, sondern die belegten Zahlen "
                        "aus dem Dokument nehmen (schraffiert gekennzeichnet)")
    a = p.parse_args(argv)
    ziel = Path(a.ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis14_") as tmp:
        arbeit = Path(tmp)

        # 1 — Geometrie mit Räumen, synthetisch, hier erzeugt (Regel 3).
        ifc = make_test_ifc.erzeuge_ifc(arbeit / "raeume.ifc", mit_raeumen=True)

        # 2 — Die Räume über die Prozessgrenze (ifcopenshell nur im .venv-ifc, Regel 1).
        eintraege: list[tuple[dict, dict]] = []
        try:
            bericht = seams.ifc_raeume(ifc)
        except seams.SeamError as e:
            print(f"NICHT GEMESSEN — Räume nicht lesbar: {e}")
            bericht = {"status": "fehlt", "raeume": []}
        if bericht.get("status") != "ok":
            print(f"Bilder 01–03 übersprungen: ifc_raeume meldet {bericht.get('status')!r}.")
        for raum in bericht.get("raeume") or []:
            if raum.get("grundriss_m") is None:
                print(f"  {raum.get('name')}: kein Grundriss — {raum.get('befund')}")
                continue
            # 3 — DIE ABLEITUNG: beide Blickarten, gerechnet, nicht gewählt.
            punkte = raumkamera.standpunkte(raum, seitenverhaeltnis=BREITE / HOEHE)
            eintraege.append((raum, punkte))
            print(f"  {raum['name']}: {raum['flaeche_m2']:.2f} m², Höhe {raum['hoehe_m']:.2f} m, "
                  f"{punkte['n_brauchbar']} von 2 Blickarten brauchbar")
            for s in punkte["standpunkte"]:
                if s["auge"] is None:
                    print(f"    {s['art']}: KEIN STANDPUNKT — {s['befund']}")
                    continue
                sf = s["sichtfeld"]
                print(f"    {s['art']}: Auge ({s['auge'][0]:.2f}, {s['auge'][1]:.2f}, "
                      f"{s['auge'][2]:.3f}), Blick auf ({s['blick_auf'][0]:.2f}, "
                      f"{s['blick_auf'][1]:.2f}), {sf['brennweite_mm']:.0f} mm, sichtbar "
                      f"{sf['sichtbare_breite_m']:.2f} m, passt={sf['passt']}")

        # 4 — Grundrisse.
        if eintraege:
            geschrieben.append(zeichne_uebersicht(ziel, eintraege))
            for nr, (raum, punkte) in enumerate(eintraege, start=2):
                geschrieben.append(zeichne_raum(ziel, nr, raum, punkte))

        # 5 — Tiefenebenen: neu messen (Blender, CPU) oder belegt lesen.
        belegt = lies_belegt()
        gemessen = None if a.ohne_blender else messe_neu(arbeit / "messung")
        if a.ohne_blender:
            print("Tiefenebenen NICHT NEU GEMESSEN (--ohne-blender) — belegte Zahlen "
                  f"aus {BELEGT_DOKUMENT.name}.")
        if gemessen is not None:
            for z in gemessen:
                if z.get("status") == "ok":
                    print(f"  gemessen: {z['raum']} {z['blick']} {z['brennweite_mm']:g} mm "
                          f"({z['quelle']}): {100 * z['groesste_ebene_anteil']:.1f} % auf "
                          f"einer Ebene, {z['stufen']} Stufen")
                else:
                    print(f"  FEHLER: {z['raum']} {z['blick']} — {z.get('error')}")
        raeume_namen = ([r["name"] for r, _ in eintraege]
                        or sorted({z["raum"] for z in belegt}))
        if raeume_namen:
            pfad = zeichne_tiefenebenen(ziel, raeume_namen, gemessen, belegt)
            if pfad:
                geschrieben.append(pfad)

    print(f"\n{len(geschrieben)} Bilder in {ziel}")
    for pfad in geschrieben:
        print(f"  {pfad.name}")
    return 0 if geschrieben else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
