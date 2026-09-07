#!/usr/bin/env python3
"""BEWEIS 12 — Die automatische Kamerasetzung, Teil 4: die Auswahl. ``kameras.standpunkte``
wählt aus den tauglichen Richtungen ``anzahl`` Standpunkte über ALLE Kombinationen, nicht
über die Einzelränge — und seit dem 07.09.2026 gibt sie den echten Gleichstand aus, statt
eine Rangfolge vorzutäuschen, die nicht gemessen ist (siehe der lange Kommentar bei
``standpunkte()``, Owner-Entscheid «Entscheidung A»).

Was bewiesen wird
-----------------
1. **Der Gleichstand ist echt, nicht geschätzt.** Von den zwölf Richtungen bestehen die
   vier Frontalen die Tauglichkeitsprüfung nicht — ``zweite_fassade`` ist bei ihnen exakt
   0 (siehe ``kameras.MIN_ZWEITE_FASSADE``), eine Aufrissaufnahme ist kein Körperbild.
   Bleiben acht Diagonalen; bei drei Plätzen sind das ``C(8,3) = 56`` Kombinationen, und
   dieses Skript rechnet **alle 56** nach — mit derselben Formel, die im Docstring von
   ``standpunkte()`` steht (geometrisches Mittel der Güte, mal die kleinste Streuung
   geteilt durch die ideale). Das Bild ``01_…`` zeigt sie als Rangbild, absteigend
   sortiert: eine flache Kante oben beweist den Gleichstand, weil mehrere Balken exakt
   dieselbe Höhe erreichen — kein gemaltes Argument, sondern echte Balkenhöhen aus 56
   echten Werten.
2. **Die gewählte Kombination ist eine von mehreren, nicht die einzige.** Unter den
   gleichwertigen gewinnt die erste in ``RICHTUNGSFOLGE`` (Owner-Entscheid 07.09.2026,
   Berichtigung des Rundungsfehlers, der vorher den zweiten Platz auswählte). Bild
   ``01_…`` markiert die gesamte Gleichstandsgruppe UND, in einer zweiten Farbe, welcher
   Balken davon tatsächlich zurückkommt.
3. **Die drei gewählten Richtungen treffen zusammen alle vier Fassaden.** Jede Diagonale
   steht zwischen zwei Fassaden (``nNE`` = Nord führt, Ost begleitet — siehe
   ``kameras.RICHTUNGEN``); welche zwei, folgt hier direkt aus derselben Tabelle, nicht
   aus einer zweiten Zuordnung. Bild ``02_…`` zeichnet den Grundriss mit den drei
   gewählten Kameras und färbt jede der vier Fassadenkanten ein — sie werden alle vier
   erreicht, aus einer Auswahl, die nur drei von acht Richtungen benutzt.

Geometrie: ``make_test_ifc`` mit ``hochbau=True`` und Geländeplatte (Regel 3, keine
Projektdaten) → ``seams.ifc_zu_glb`` (IfcOpenShell im ``.venv-ifc``, **kein Blender**,
Regel 3/6 dieses Auftrags) → ``glbbox.bauwerksbox``. Dasselbe Bauwerk wie in Beweis 09.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Bedeutung liegt in Anordnung, Farbe und Dateiname.

``01_kombinationen_…png`` — 56 Balken, absteigend nach Güte sortiert, Grundlinie unten.

    Blaugrau      eine gewöhnliche Kombination (nicht am Bestwert)
    Teal          eine von mehreren gleichwertigen Kombinationen (exakter Bestwert)
    Orange        die Kombination, die ``standpunkte()`` tatsächlich zurückgibt —
                  IMMER die erste Teal-farbene von links, weil sortiert wurde und
                  Python stabil sortiert: Bei gleicher Höhe bleibt die
                  ``RICHTUNGSFOLGE``-Reihenfolge erhalten, dieselbe Regel, nach der
                  ``standpunkte()`` den Gleichstand auflöst.
    Dünne graue Linie   der Bestwert als Referenzhöhe

``02_grundrissabdeckung_…png`` — Draufsicht, Nord oben (wie Beweis 09).

    Sandfarben    die Geländeplatte
    Stahlblau     die Bauteile (glb-Knotenboxen, auf den Boden projiziert)
    Dunkler Rahmen  die Hüllbox des Bauwerks
    Vier farbige Kanten der Hüllbox  je eine Fassade (N/E/S/W); GRÜN = von
                  mindestens einer der drei gewählten Kameras getroffen, ROT = von
                  keiner. Der Beweis behauptet: alle vier sind grün.
    Drei Kreise mit Pfeil  die gewählten Kameras (Standort, Blickziel), je eine
                  eigene Farbe
    Dünne Linien in Kamerafarbe  vom Standort zur Mitte jeder Fassadenkante, die
                  diese Kamera trägt (zwei je Kamera) — macht sichtbar, WELCHE
                  Kamera WELCHE Fassade deckt, nicht nur dass sie gedeckt ist

Was hier NICHT bewiesen wird
----------------------------
Dass Blender an genau diesen drei Standorten rendert — das ist Beweis 09/10/11. Dieses
Skript ruft kein Blender auf (Regel 3 dieses Auftrags) und braucht keine GPU; es läuft
vollständig hier, reine Python-Rechnung auf synthetischer Geometrie.

    python tools/beweis/12_kamera_auswahl.py [zielordner]
"""
from __future__ import annotations

import itertools
import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, glbbox, kameras  # noqa: E402
from aiimaging import seams  # noqa: E402
from aiimaging.maske import ist_gelaende  # noqa: E402

import make_test_ifc  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "12_kamera_auswahl"

# Farben — dieselbe Sprache wie in Beweis 09/10/11.
FARBE_LEINWAND = (245, 245, 245)
FARBE_GELAENDE = (222, 206, 170)
FARBE_BAUTEIL = (70, 110, 160)
FARBE_HUELLBOX = (40, 40, 40)
FARBE_MASSSTAB = (60, 60, 60)

FARBE_BAR_NORMAL = (150, 170, 190)
FARBE_BAR_GLEICHSTAND = (40, 150, 150)
FARBE_BAR_GEWAEHLT = (230, 120, 40)
FARBE_REFERENZLINIE = (120, 120, 120)

FARBE_ABGEDECKT = (40, 150, 70)
FARBE_NICHT_ABGEDECKT = (200, 50, 40)

# Drei feste Kamerafarben — reine Kennfarben, keine Bewertung.
FARBEN_KAMERAS = ((190, 70, 150), (60, 130, 200), (210, 150, 30))

BALKEN_B, BALKEN_H = 960, 460
BALKEN_RAND_PX = 30

GRUNDRISS_PX = 900
GRUNDRISS_RAND_PX = 40


# ----------------------------------------------------------------------------------------
# Rasterizer — dieselben drei Grundformen wie in Beweis 09 (Regel 1: keine Bibliothek).
# ----------------------------------------------------------------------------------------

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


def _formatiere_zahl(x: float, stellen: int = 2) -> str:
    return f"{x:.{stellen}f}"


# ----------------------------------------------------------------------------------------
# Schritt 1 — Geometrie (identisch zu Beweis 09, damit beide Beweise vergleichbar sind)
# ----------------------------------------------------------------------------------------

def baue_geometrie(arbeit: Path) -> dict:
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
    return {
        "bbox_bauwerk": bau["bbox_bauwerk"],
        "bbox_szene": bau["bbox_szene"],
        "knoten_welt": knoten_welt,
        "gelaende_z": max(gelaende) if gelaende else None,
    }


# ----------------------------------------------------------------------------------------
# Schritt 2 — alle Kombinationen nachrechnen (dieselbe Formel wie standpunkte(), aus
# dessen Docstring: mittel(güte) [geometrisch] · min(kleinster Winkelabstand / ideal, 1))
# ----------------------------------------------------------------------------------------

def _winkelabstand(a: float, b: float) -> float:
    d = abs(float(a) - float(b)) % 360.0
    return min(d, 360.0 - d)


def rechne_alle_kombinationen(befund: dict) -> list:
    """``[(kuerzel_tuple, wert), ...]`` für JEDE Kombination der tauglichen Richtungen,
    in der Enumerationsreihenfolge von ``itertools.combinations`` über die tauglichen
    Kürzel in ``RICHTUNGSFOLGE``-Reihenfolge — genau die Reihenfolge, in der
    ``kameras.standpunkte`` selbst aufzählt (dort als privater Code, hier nachgebaut aus
    dem, was der Docstring als Formel nennt, damit sie unabhängig geprüft werden kann).
    """
    satz = befund["satz"]
    guete_je_kuerzel = {b["kuerzel"]: b["guete"] for b in befund["kandidaten"]}
    azimut_je_kuerzel = {k["kuerzel"]: k["azimut_grad"] for k in satz["kameras"]}
    tauglich = [k["kuerzel"] for k in satz["kameras"]
                if guete_je_kuerzel.get(k["kuerzel"], 0.0) > 0.0
                and any(b["kuerzel"] == k["kuerzel"] and b["taugt"]
                        for b in befund["kandidaten"])]

    ziel = min(3, len(tauglich))
    ideal = 360.0 / max(ziel, 1)

    ergebnisse = []
    for gruppe in itertools.combinations(tauglich, ziel):
        guete = [guete_je_kuerzel[k] for k in gruppe]
        mittel = math.prod(guete) ** (1.0 / len(guete))
        if len(gruppe) < 2:
            wert = mittel
        else:
            eng = min(_winkelabstand(azimut_je_kuerzel[a], azimut_je_kuerzel[b])
                      for a, b in itertools.combinations(gruppe, 2))
            wert = mittel * min(eng / ideal, 1.0)
        ergebnisse.append((gruppe, wert))
    return ergebnisse


# ----------------------------------------------------------------------------------------
# Schritt 3 — Bild 1: Rangbild der Kombinationen
# ----------------------------------------------------------------------------------------

def zeichne_rangbild(kombinationen: list, gewaehlte_kuerzel: tuple, *,
                     stellen: int = 12, breite: int = BALKEN_B, hoehe: int = BALKEN_H,
                     rand_px: int = BALKEN_RAND_PX):
    """Absteigend sortiert nach gerundetem Wert; Python sortiert stabil, darum bleibt bei
    gleicher Höhe die Enumerationsreihenfolge (= ``RICHTUNGSFOLGE``) erhalten — dieselbe
    Regel, nach der ``standpunkte()`` den Gleichstand auflöst. Der erste Balken der
    Gleichstandsgruppe IST darum die tatsächlich gewählte Kombination."""
    gerundet = [(round(wert, stellen), gruppe, wert) for gruppe, wert in kombinationen]
    gerundet.sort(key=lambda t: t[0], reverse=True)
    spitze = gerundet[0][0]

    px = _neues_bild(breite, hoehe)
    n = len(gerundet)
    innen_b = breite - 2 * rand_px
    innen_h = hoehe - 2 * rand_px
    breite_je_balken = innen_b / n
    hoechster_rohwert = max(w for _, _, w in gerundet) or 1.0

    referenz_y = rand_px + innen_h * (1.0 - spitze / hoechster_rohwert)
    _strecke(px, breite, hoehe, rand_px, referenz_y, breite - rand_px, referenz_y,
             FARBE_REFERENZLINIE, 1.0)

    for i, (g, gruppe, wert) in enumerate(gerundet):
        x0 = rand_px + i * breite_je_balken
        x1 = x0 + max(1.0, breite_je_balken - 1.0)
        y1 = rand_px + innen_h
        y0 = rand_px + innen_h * (1.0 - wert / hoechster_rohwert)
        if gruppe == gewaehlte_kuerzel:
            farbe = FARBE_BAR_GEWAEHLT
        elif g == spitze:
            farbe = FARBE_BAR_GLEICHSTAND
        else:
            farbe = FARBE_BAR_NORMAL
        _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe)

    return px, breite, hoehe, spitze, sum(1 for g, _, _ in gerundet if g == spitze)


# ----------------------------------------------------------------------------------------
# Schritt 4 — welche zwei Fassaden eine Diagonale trägt, direkt aus RICHTUNGEN gelesen
# ----------------------------------------------------------------------------------------

def fassaden_je_richtung() -> dict:
    """``{kuerzel: (primaer, sekundaer)}`` für jede der acht Diagonalen — ohne eine zweite
    Zuordnungstabelle zu erfinden: ``primaer`` ist die Frontale mit demselben Grundazimut,
    ``sekundaer`` die Frontale um 90° in Richtung des Bias-Vorzeichens. ``nNE`` (Grund 0°,
    Faktor +1) ergibt so ``("n", "e")`` — genau das, was der Modul-Docstring in Worten
    sagt: «die Nordfassade führt, die Ostfassade begleitet»."""
    frontal_je_grund = {grund: kuerzel for kuerzel, (grund, faktor)
                        in kameras.RICHTUNGEN.items() if faktor == 0}
    ergebnis = {}
    for kuerzel, (grund, faktor) in kameras.RICHTUNGEN.items():
        if faktor == 0:
            continue
        vorzeichen = 1 if faktor > 0 else -1
        ergebnis[kuerzel] = (frontal_je_grund[grund % 360.0],
                             frontal_je_grund[(grund + 90.0 * vorzeichen) % 360.0])
    return ergebnis


# ----------------------------------------------------------------------------------------
# Schritt 5 — Bild 2: Grundriss mit den drei gewählten Kameras und der Fassadenabdeckung
# ----------------------------------------------------------------------------------------

def zeichne_abdeckung(geometrie: dict, satz: dict, gewaehlt: list, *,
                      kante_px: int = GRUNDRISS_PX, rand_px: int = GRUNDRISS_RAND_PX):
    bbox = geometrie["bbox_bauwerk"]
    (ux, uy, _), (ox, oy, _) = bbox
    fassaden = fassaden_je_richtung()
    getroffen = set()
    for kam in gewaehlt:
        getroffen.update(fassaden[kam["kuerzel"]])

    xs = [ecke[0] for ecke in geometrie["bbox_szene"]] + [k["auge"][0] for k in gewaehlt]
    ys = [ecke[1] for ecke in geometrie["bbox_szene"]] + [k["auge"][1] for k in gewaehlt]
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
            _rechteck(px, breite, hoehe, x0, y0, max(x1, x0 + 1), max(y1, y0 + 1),
                      FARBE_BAUTEIL)

    x0, y0 = nach_px(ux, oy); x1, y1 = nach_px(ox, uy)
    _rahmen(px, breite, hoehe, x0, y0, x1, y1, FARBE_HUELLBOX, 2)

    # Vier Fassadenkanten, dick nachgezogen: gruen = getroffen, rot = nicht.
    mxp, myp = (ux + ox) / 2.0, (uy + oy) / 2.0
    kanten = {
        "n": ((ux, oy), (ox, oy)),
        "s": ((ux, uy), (ox, uy)),
        "e": ((ox, uy), (ox, oy)),
        "w": ((ux, uy), (ux, oy)),
    }
    mitten_welt = {}
    for name, (p0, p1) in kanten.items():
        farbe = FARBE_ABGEDECKT if name in getroffen else FARBE_NICHT_ABGEDECKT
        a = nach_px(*p0); b = nach_px(*p1)
        _strecke(px, breite, hoehe, *a, *b, farbe, 6.0)
        mitten_welt[name] = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)

    # Kameras: Standort, Blickpfeil, und je eine duenne Linie zu den Mitten der beiden
    # Fassadenkanten, die diese Kamera nach `fassaden_je_richtung` traegt.
    for i, kam in enumerate(gewaehlt):
        farbe = FARBEN_KAMERAS[i % len(FARBEN_KAMERAS)]
        ax, ay = nach_px(kam["auge"][0], kam["auge"][1])
        for fname in fassaden[kam["kuerzel"]]:
            fx, fy = nach_px(*mitten_welt[fname])
            _strecke(px, breite, hoehe, ax, ay, fx, fy, farbe, 1.2)
        bx, by = nach_px(kam["blick_auf"][0], kam["blick_auf"][1])
        _pfeil(px, breite, hoehe, ax, ay, bx, by, farbe, 2.2)
        _scheibe(px, breite, hoehe, ax, ay, 7.0, farbe)

    bx0, by0 = rand_px, hoehe - rand_px
    _rechteck(px, breite, hoehe, bx0, by0 - 4, bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0, by0 - 10, bx0 + 2, by0, FARBE_MASSSTAB)
    _rechteck(px, breite, hoehe, bx0 + 10.0 / m_je_px - 2, by0 - 10,
              bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    _pfeil(px, breite, hoehe, rand_px, rand_px + 34, rand_px, rand_px, FARBE_MASSSTAB, 2.0)

    return px, breite, hoehe, m_je_px, getroffen


# ----------------------------------------------------------------------------------------

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis12_") as tmp:
        geometrie = baue_geometrie(Path(tmp))

    bbox = geometrie["bbox_bauwerk"]
    befund = kameras.standpunkte(bbox, gelaende_z=geometrie["gelaende_z"])
    if not befund["standpunkte"]:
        raise SystemExit("standpunkte() liefert keinen Vorschlag — kein Beweis moeglich "
                          "(siehe 'warnungen').")
    gewaehlte_kuerzel = tuple(k["kuerzel"] for k in befund["standpunkte"])

    # -- Kontrolle VOR dem Zeichnen: die eigene Nachrechnung muss den Befund treffen. --
    kombinationen = rechne_alle_kombinationen(befund)
    if len(kombinationen) != befund["n_kombinationen"]:
        raise SystemExit(
            f"{len(kombinationen)} nachgerechnete Kombinationen, "
            f"standpunkte() nennt {befund['n_kombinationen']} — kein Beweis, sondern "
            f"ein Widerspruch.")
    bester_nachgerechnet = max(wert for _, wert in kombinationen)
    if not math.isclose(bester_nachgerechnet, befund["wert"], rel_tol=1e-9, abs_tol=1e-9):
        raise SystemExit(
            f"Nachgerechneter Bestwert {bester_nachgerechnet!r} != "
            f"befund['wert'] {befund['wert']!r} — die Formel im Docstring stimmt nicht "
            f"mit dem Code ueberein.")
    n_gleichstand_nachgerechnet = sum(
        1 for _, wert in kombinationen
        if round(wert, 12) == round(bester_nachgerechnet, 12))
    if n_gleichstand_nachgerechnet != befund["n_gleichstand"]:
        raise SystemExit(
            f"{n_gleichstand_nachgerechnet} gleichwertige nachgerechnet, "
            f"standpunkte() nennt {befund['n_gleichstand']} — kein Beweis.")

    # -- 01 Rangbild --
    px, b, h, spitze, n_gleichstand = zeichne_rangbild(kombinationen, gewaehlte_kuerzel)
    pfad = ziel / (
        f"01_kombinationen_rang_n-{len(kombinationen)}_gleichstand-{n_gleichstand}_"
        f"gewaehlt-{'+'.join(gewaehlte_kuerzel)}_guete-{spitze:.4f}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 02 Grundrissabdeckung --
    px, b, h, m_je_px, getroffen = zeichne_abdeckung(
        geometrie, befund["satz"], befund["standpunkte"])
    if getroffen != {"n", "e", "s", "w"}:
        raise SystemExit(
            f"Nur {sorted(getroffen)} getroffen statt aller vier Fassaden — die "
            f"Behauptung dieses Beweises stimmt fuer diesen Lauf NICHT, das Bild darf "
            f"das nicht verschweigen.")
    pfad = ziel / (
        f"02_grundrissabdeckung_kameras-{'+'.join(gewaehlte_kuerzel)}_"
        f"fassaden-{len(getroffen)}von4_massstab-{m_je_px:.3f}m-je-px.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
