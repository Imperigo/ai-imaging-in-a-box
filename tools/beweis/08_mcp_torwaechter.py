#!/usr/bin/env python3
"""BEWEIS 08 — Das MCP-Werkzeug ``aiimaging_check_geometry`` (``werkzeuge.check_geometry``,
gerufen über dieselbe SDK-freie Naht ``mcp_server.rufe_werkzeug`` wie in Beweis 06) zieht
die Schranken des Torwächters (``torwaechter.py``) tatsächlich dort, wo sein Modul-Docstring
sie behauptet — und zwar zweifach: einmal als durchgehende Fläche über zehn Grössenordnungen,
einmal an drei konkreten, benannten Einzelfällen.

Was bewiesen wird
------------------
1. **Die Fläche** (``01_torwaechter-flaeche_*.png``): Für ein Gitter aus
   Gebäudemasse × Positionsversatz (je 0.001 m bis 1e7 m, log-Skala, 40 000 Zellen) wird
   pro Zelle ein ECHTER Quader gebaut — Ecke ``(versatz, versatz, 0)`` bis
   ``(versatz+masse, versatz+masse, masse)`` — und über
   ``mcp_server.rufe_werkzeug("aiimaging_check_geometry", {"bbox": ...})`` ECHT geprüft.
   Kein Pixel ist geschätzt: 40 000 echte Werkzeugaufrufe, 40 000 echte Antworten.

   Die beiden Prüfungen im Torwächter sind unabhängig (Massstab prüft Kantenlängen,
   Georeferenz prüft Koordinatenbeträge) — durch die Eckpunktwahl oben hängen sie in
   diesem Gitter dennoch zusammen: Bei Versatz 0 bestimmt allein die Gebäudemasse beide
   Prüfungen, weil die Kante selbst dann auch der Koordinatenbetrag ist. Genau das macht
   die schmale Lücke zwischen den Schranken sichtbar (siehe unten).

   Genau drei Farben, genau die drei, die der Auftrag nennt — keine feinere Unter-
   scheidung der Ablehnungsgründe, denn ``check_geometry`` gibt die Innerei von
   ``pruefe_massstab`` (welche der drei Meldungen genau griff) gar nicht erst nach
   aussen; nur ``entscheidung`` und ``empfiehlt_neuzentrierung`` sind sichtbar, und nur
   diese beiden Felder steuern die Farbe hier.

   Waagrecht (Spalte = Gebäudemasse) zeigt sich die Massstabs-Schranke: Rot links (unter
   1 m), Grün in der Mitte (1–1000 m, plausibel), Rot rechts (über 1000 m). Senkrecht
   (Zeile = Positionsversatz) zeigt sich die Georeferenz-Schranke NUR innerhalb des
   grünen Mittelbands: unten (Versatz unter rund 1e5 m) bleibt es Grün, oben schlägt es
   nach Blau um (``annehmen``, aber ``empfiehlt_neuzentrierung=True``). Oben rechts, wo
   Gebäudemasse UND Versatz beide riesig sind, bleibt es Rot: Wächst der Quader von der
   Ecke bei ``(0,0,0)`` aus über rund 1e5 m hinaus, ist er laut Massstabsprüfung längst
   kein Gebäude mehr — Massstab schlägt hier immer zuerst zu, Blau erscheint einzig im
   grünen Band. Diese Lücke zu behaupten wäre eine Illustration gewesen; hier ist sie
   gemessen, in genau den Zellen, in denen der echte Werkzeugaufruf das auch ergibt.

2. **Die drei Einzelfälle** (``02_einzelfaelle_*.png``, drei Balken übereinander, jeder
   aus seinem eigenen echten Werkzeugaufruf):
   * 8×5×3 m — plausibles Gebäude, Ursprung: ``annehmen``, Grün.
   * 8000×5000×3000 m — dieselbe Form, Faktor 1000 zu gross (Millimeter versehentlich
     als Meter gelesen): ``ablehnen_massstab``, Rot.
   * 8×5×3 m an einer LV95-Koordinate (Ostwert 2 600 008 m): Massstab plausibel, aber
     ``empfiehlt_neuzentrierung=True``: ``annehmen``, Blau mit Empfehlungs-Feld.

Woran man es im Bild sieht
--------------------------
Fläche: reine Rasterfarbe pro Zelle, aus der echten Antwortfarbe gemischt (kein
Kantenglätten, kein Diagramm-Overlay) — Grenzen sind dort, wo die Farbe wirklich wechselt.
Einzelfälle: Balkenlänge = log10 der grössten Kante (dieselbe Konvention wie
``tools/beweis/01_knoten_geometrie.py``, dort geprüft), Balkenfarbe = echte Entscheidung,
blaues Feld rechts = echtes ``empfiehlt_neuzentrierung``. Die genauen Zahlen stehen im
Dateinamen (Regel 2: keine Bitmap-Schrift im Bild).

Läuft vollständig hier
-----------------------
``torwaechter.py`` ist laut eigenem Modul-Docstring reine stdlib, ohne Subprozess und
ohne Datei-I/O; ``werkzeuge.check_geometry`` ruft nichts an, was Blender oder eine GPU
bräuchte (das tut nur ``enqueue_render``, hier nicht verwendet). Dieser Beweis läuft
darum vollständig hier, ohne Gerät. 40 000 Gitterzellen sind reine Zahlenvergleiche —
in der Grössenordnung von Sekunden auf jeder CPU.

Aufruf:
    python3 tools/beweis/08_mcp_torwaechter.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/08_mcp_torwaechter/``.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, mcp_server, torwaechter  # noqa: E402
from aiimaging.mcp_schemas import WERKZEUG_PRUEFE  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "08_mcp_torwaechter"

# Dieselbe Wertespanne, die der Auftrag nennt: 0.001 m bis 1e7 m, zehn Grössenordnungen.
LOG_MIN = -3.0
LOG_MAX = 7.0

FARBE_HINTERGRUND = (238, 238, 235)
FARBE_ANNEHMEN = (60, 150, 70)              # annehmen, keine Georef-Empfehlung
FARBE_GEOREF = (50, 90, 190)                # annehmen, empfiehlt_neuzentrierung
FARBE_ABLEHNEN_MASSSTAB = (190, 60, 50)     # ablehnen_massstab, jeder Grund
FARBE_UNERWARTET = (120, 120, 120)          # sollte auf gültigen bbox-Werten nie auftreten


# ----------------------------------------------------------------------------------
# Echter Aufruf — dieselbe SDK-freie Naht wie in Beweis 06, nicht der Torwächter direkt.
# ----------------------------------------------------------------------------------

def rufe_pruefe_echt(bbox) -> dict:
    """``check_geometry`` ECHT über ``mcp_server.rufe_werkzeug`` — nicht ``torwaechter.
    torwaechter()`` direkt. Diese Naht ist genau das, was KosmoOrbit auch aufriefe."""
    antwort = mcp_server.rufe_werkzeug(WERKZEUG_PRUEFE, {"bbox": bbox})
    if antwort.get("error"):
        raise SystemExit(f"Echter Aufruf von {WERKZEUG_PRUEFE!r} schlug fehl: "
                          f"{antwort['error']}")
    return antwort


def einordnen(antwort: dict) -> tuple:
    """Echte Antwortfelder → (Farbe, Kategorie-Name fürs Zählen/den Dateinamen).

    Genau die drei Kategorien, die der Auftrag nennt — gesteuert einzig durch
    ``entscheidung`` und ``empfiehlt_neuzentrierung``, die beiden Felder, die
    ``check_geometry`` tatsächlich zurückgibt. ``pruefe_massstab`` unterscheidet intern
    zwischen mehreren Ablehnungsgründen (Faktor-1000-Verdacht, Kontextmodell, u.a.),
    aber diese Feinheit reicht das Werkzeug selbst nicht nach aussen (siehe
    ``werkzeuge.check_geometry`` — kein ``massstab``-Feld in der Antwort) — sie hier
    dennoch einzufärben würde etwas behaupten, das der echte Werkzeugaufruf gar nicht
    hergibt.
    """
    entscheidung = antwort["entscheidung"]
    if entscheidung == torwaechter.ENTSCHEIDUNG_ANNEHMEN:
        if antwort.get("empfiehlt_neuzentrierung"):
            return FARBE_GEOREF, "annehmen_georef-empfehlung"
        return FARBE_ANNEHMEN, "annehmen"
    if entscheidung == torwaechter.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB:
        return FARBE_ABLEHNEN_MASSSTAB, "ablehnen_massstab"
    return FARBE_UNERWARTET, f"unerwartet_{entscheidung}"


# ----------------------------------------------------------------------------------
# Minimaler Rasterizer (dasselbe Muster wie in den Nachbar-Beweisen 01/06) — im Projekt
# gibt es keinen, weil bildschreiben.py bewusst ohne Bibliothek auskommt.
# ----------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        zeile = y * breite
        for x in range(xa, xb):
            px[zeile + x] = farbe


def _dunkler(farbe, faktor: float = 0.6):
    return tuple(max(0, int(round(k * faktor))) for k in farbe)


def _rechteck_rahmen(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe,
                      *, rahmen=True) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe)
    if not rahmen:
        return
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    if xa >= xb or ya >= yb:
        return
    rand = _dunkler(farbe)
    for x in range(xa, xb):
        px[ya * breite + x] = rand
        px[(yb - 1) * breite + x] = rand
    for y in range(ya, yb):
        px[y * breite + xa] = rand
        px[y * breite + (xb - 1)] = rand


# ----------------------------------------------------------------------------------
# Teil 1 — die Fläche: 40 000 echte Werkzeugaufrufe, ein Pixelblock je Zelle.
# ----------------------------------------------------------------------------------

GITTER_N = 200     # Zellen je Achse -> GITTER_N**2 echte Aufrufe
ZELLE_PX = 4        # Bildpixel je Gitterzelle -> Bild GITTER_N*ZELLE_PX hoch/breit


def baue_flaeche() -> tuple:
    """Gitter Gebäudemasse (Spalte) × Positionsversatz (Zeile) füllen — je Zelle ein
    ECHTER Quader, ECHT über die MCP-Naht geprüft. Rückgabe: (pixel, breite, hoehe,
    zaehler) — ``zaehler`` ist die echte Verteilung der Kategorien über alle Zellen,
    für die Konsolenausgabe und den Dateinamen."""
    breite = hoehe = GITTER_N * ZELLE_PX
    px = _neues_bild(breite, hoehe)
    zaehler: dict = {}

    for zeile in range(GITTER_N):
        # Zeile 0 = oben = grösster Versatz (Konvention: y wächst nach oben, wie in
        # tools/beweis/01_knoten_geometrie.py).
        log_versatz = LOG_MAX - (zeile / (GITTER_N - 1)) * (LOG_MAX - LOG_MIN)
        versatz = 10.0 ** log_versatz
        for spalte in range(GITTER_N):
            log_masse = LOG_MIN + (spalte / (GITTER_N - 1)) * (LOG_MAX - LOG_MIN)
            masse = 10.0 ** log_masse
            bbox = [[versatz, versatz, 0.0],
                    [versatz + masse, versatz + masse, masse]]
            antwort = rufe_pruefe_echt(bbox)
            farbe, kategorie = einordnen(antwort)
            zaehler[kategorie] = zaehler.get(kategorie, 0) + 1
            x0 = spalte * ZELLE_PX
            y0 = zeile * ZELLE_PX
            _rechteck(px, breite, hoehe, x0, y0, x0 + ZELLE_PX, y0 + ZELLE_PX, farbe)

    return px, breite, hoehe, zaehler


# ----------------------------------------------------------------------------------
# Teil 2 — drei benannte Einzelfälle, je ein echter Aufruf, als Balken übereinander.
# ----------------------------------------------------------------------------------

EINZELFAELLE = [
    ("8x5x3m", [[0.0, 0.0, 0.0], [8.0, 5.0, 3.0]]),
    ("8000x5000x3000m", [[0.0, 0.0, 0.0], [8000.0, 5000.0, 3000.0]]),
    ("lv95-ostwert2600008m", [[2_600_000.0, 1_200_000.0, 450.0],
                              [2_600_008.0, 1_200_005.0, 453.0]]),
]

BALKEN_BREITE = 640
BALKEN_HOEHE_JE = 130
BALKEN_RAND = 30


def zeichne_balken(px, breite, hoehe, y0: int, farbe, log_kante: float,
                    empfiehlt: bool) -> None:
    balken_max = breite - 2 * BALKEN_RAND
    # Dieselbe log10-Konvention wie tools/beweis/01_knoten_geometrie.py:
    # zeichne_torwaechter — 0.02..1.0 über log10(Kante) von -1 bis 7, damit sowohl der
    # Faktor-1000-Fall als auch der LV95-Fall auf derselben Leinwand Platz haben.
    anteil = min(1.0, max(0.02, (log_kante + 1.0) / 8.0))
    laenge = BALKEN_RAND + anteil * balken_max
    y_bar0 = y0 + BALKEN_HOEHE_JE * 0.25
    y_bar1 = y0 + BALKEN_HOEHE_JE * 0.75
    _rechteck_rahmen(px, breite, hoehe, BALKEN_RAND, y_bar0, laenge, y_bar1, farbe)
    if empfiehlt:
        _rechteck_rahmen(px, breite, hoehe, breite - BALKEN_RAND - 30, y_bar0,
                          breite - BALKEN_RAND, y_bar1, FARBE_GEOREF)


def baue_einzelfaelle() -> tuple:
    hoehe = len(EINZELFAELLE) * BALKEN_HOEHE_JE
    px = _neues_bild(BALKEN_BREITE, hoehe)
    ergebnisse = []
    for i, (name, bbox) in enumerate(EINZELFAELLE):
        antwort = rufe_pruefe_echt(bbox)
        farbe, kategorie = einordnen(antwort)
        kante = max(torwaechter.masse_aus_bbox(bbox))  # nur zur Balkenlänge, echt gemessen
        log_kante = math.log10(kante) if kante > 0 else -3.0
        zeichne_balken(px, BALKEN_BREITE, hoehe, i * BALKEN_HOEHE_JE, farbe, log_kante,
                        bool(antwort.get("empfiehlt_neuzentrierung")))
        ergebnisse.append((name, kategorie, antwort))
        if i < len(EINZELFAELLE) - 1:
            fuge_y = (i + 1) * BALKEN_HOEHE_JE
            _rechteck(px, BALKEN_BREITE, hoehe, 0, fuge_y - 3, BALKEN_BREITE, fuge_y + 3,
                       (20, 20, 20))
    return px, BALKEN_BREITE, hoehe, ergebnisse


def _formatiere_zahl(x: float) -> str:
    if abs(x) >= 1000:
        return f"{x:.0f}"
    return f"{x:.4g}"


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    print(f"Echt aufgerufen (Fläche): mcp__aiimaging__{WERKZEUG_PRUEFE}, "
          f"{GITTER_N * GITTER_N} Zellen …")
    px, b, h, zaehler = baue_flaeche()
    verteilung = "_".join(f"{k}-{v}" for k, v in sorted(zaehler.items()))
    print("Echte Verteilung: " + ", ".join(f"{k}={v}" for k, v in sorted(zaehler.items())))
    name = (f"01_torwaechter-flaeche_gebaeudemasse-0.001m-bis-1e7m"
            f"_positionsversatz-0.001m-bis-1e7m_raster-{GITTER_N}x{GITTER_N}"
            f"_{verteilung}.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    print(f"Echt aufgerufen (Einzelfälle): mcp__aiimaging__{WERKZEUG_PRUEFE}, "
          f"{len(EINZELFAELLE)} Fälle …")
    px, b, h, ergebnisse = baue_einzelfaelle()
    for name_fall, kategorie, antwort in ergebnisse:
        print(f"  {name_fall}: {kategorie} "
              f"(empfiehlt_neuzentrierung={antwort.get('empfiehlt_neuzentrierung')})")
    teile = "_".join(f"{name_fall}-{kategorie}" for name_fall, kategorie, _ in ergebnisse)
    pfad = ziel / f"02_einzelfaelle_{teile}.png"
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
