#!/usr/bin/env python3
"""BEWEIS 06 — Das MCP-Werkzeug ``aiimaging_capabilities`` (Selbstauskunft der Lane,
Modul ``aiimaging.werkzeuge.capabilities``) wird ECHT aufgerufen — über dieselbe
SDK-freie Naht, die auch der Server benutzt (``aiimaging.mcp_server.rufe_werkzeug``) —
und seine Antwort wird als Bild dargestellt: welche Werkzeuge zugesagt sind, welche
Schwelle mit welchem Kalibrierungsstand, und daneben die Lizenzlage des Repos
(``NOTICE``, echt eingelesen, nicht behauptet).

Zum Namen im Auftrag: Der Owner nennt das Werkzeug "kosmovis_capabilities" — so, wie es
im Cockpit als Naht der Lane "KosmoVis" erscheinen würde. Der tatsächliche MCP-Name
(``mcp_schemas.LANE = "aiimaging"``) lautet ``aiimaging_capabilities``; das ist keine
Ungenauigkeit dieses Beweises, sondern der Name, der beim echten Aufruf tatsächlich
zurückkommt (siehe Bildunterschrift im Dateinamen und die erste Zeile der Konsolen-
ausgabe unten).

Was bewiesen wird
-----------------
Drei Zusagen aus einem einzigen echten Aufruf, plus eine vierte Messung daneben:

1. **Werkzeuge.** ``antwort["werkzeuge"]`` — die vier Namen, unter denen KosmoOrbit
   diese Lane ansprechen kann.
2. **Schwelle mit Kalibrierungsstand.** ``antwort["geometrie_schwelle"]`` (0.65) UND,
   aus ``antwort["vorbehalte"]`` herausgelesen, ob sie kalibriert ist. Das ist der
   Befund U3 aus ``docs/UI_BEFUNDE.md``: *"Die Vorbehalte gehören an die Zahl, nicht
   in eine Fussnote"* — hier wörtlich umgesetzt, indem der Vorbehalt die FARBE der
   Zahl selbst bestimmt, statt daneben zu stehen.
3. **Prompt-Sprache.** ``antwort["prompt_sprache"]`` — zwei echte Wahrheitswerte
   (wird deutsch übersetzt? warnt die Lane bei nicht-englischem Prompt?) als gefüllte
   bzw. leere Quadrate.
4. **Lizenzlage.** Kein Feld der MCP-Antwort — echt aus ``NOTICE`` ausgezählt (jede
   Zeile ``AUFLOESUNG: <Wert>``, siehe dessen Kopf). Drei Werte sind möglich:
   Prozessgrenze (grün), Lizenzausnahme (blau), KEINE — ein offener Punkt (rot).
   Diese Auszählung steht neben der Werkzeug-Antwort, weil Regel 1 verlangt, dass ein
   GPL/AGPL-Fund AUSDRÜCKLICH gemeldet wird, und "ausdrücklich" hier heisst: im selben
   Bild wie die Fähigkeiten, nicht in einem separaten Lizenzbericht, den niemand neben
   das Cockpit legt.

Woran man es im Bild sieht
--------------------------
Drei Felder übereinander, durch schwarze Fugen getrennt, Hintergrund helles Grau:

  Oben     Vier Balken, einer je zugesagtem Werkzeug (Reihenfolge = sortierte Namen,
           steht im Dateinamen). Balkenhöhe = Anzahl Ausgabefelder seines
           ``outputSchema`` (echt gezählt, kein Schätzwert — 6/6/9/8). Goldener Rahmen
           um den Balken des Werkzeugs, das diesen Beweis gerade beantwortet hat
           (``aiimaging_capabilities`` selbst). Grüner Streifen darunter über die
           volle Breite: alle vier sind laut Vertrag ``readonly``.
  Mitte    Ein Balken auf einer Skala von 0 bis zum Bildrand (die Skala selbst als
           grauer Rahmen, 0..1 der Geometrie-Schwelle): Füllstand 0.65. Die Farbe der
           Füllung ist ROT, weil ``vorbehalte`` diese Schwelle wörtlich als "NICHT
           kalibriert" führt — wäre sie kalibriert, stünde hier Grün. Rechts daneben
           zwei kleine Quadrate für die beiden echten Sprach-Wahrheitswerte: gefüllt
           = wahr. Beide sind hier gefüllt.
  Unten    Ein durchgehender Balken, echt aus ``NOTICE`` ausgezählt und proportional
           unterteilt: Grün = Prozessgrenze, Blau = Lizenzausnahme, Rot = KEINE
           (offener Punkt). Darunter so viele rote Striche, wie ``vorbehalte`` lang
           ist (vier) — die Vorbehalte als sichtbare Menge, nicht als Fussnotenzahl.

Kein Diagramm hier illustriert eine Behauptung — jede Balkenlänge, jede Farbe und jede
Strichzahl ist im selben Lauf gemessen, der auch die Konsolenausgabe erzeugt.

Läuft vollständig hier
----------------------
Reines Python: ein direkter Funktionsaufruf plus das Einlesen einer Textdatei (NOTICE).
Kein Blender, keine GPU, kein Modellgewicht. Das gilt für den GESAMTEN Beweis — anders
als bei den Nachbar-Skripten 01-04 gibt es hier keinen abgetrennten Geräte-Teil.

Aufruf:
    python3 tools/beweis/06_mcp_faehigkeiten.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/06_mcp_faehigkeiten/``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, mcp_server  # noqa: E402
from aiimaging.mcp_schemas import WERKZEUG_FAEHIGKEITEN, WERKZEUGE  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "06_mcp_faehigkeiten"

FARBE_HINTERGRUND = (238, 238, 235)
FARBE_WERKZEUG = (70, 140, 135)
FARBE_RAHMEN_AKTIV = (210, 165, 40)     # gold — das Werkzeug, das gerade geantwortet hat
FARBE_READONLY = (70, 150, 70)
FARBE_KALIBRIERT = (70, 150, 70)
FARBE_NICHT_KALIBRIERT = (190, 60, 50)
FARBE_SKALA_RAHMEN = (140, 140, 140)
FARBE_WAHR = (60, 120, 190)
FARBE_PROZESSGRENZE = (70, 150, 70)
FARBE_LIZENZAUSNAHME = (60, 110, 190)
FARBE_OFFEN = (190, 60, 50)
FARBE_FUGE = (20, 20, 20)


# ----------------------------------------------------------------------------------
# Minimaler Rasterizer (dasselbe Muster wie tools/beweis/01_knoten_geometrie.py) —
# es gibt im Projekt keinen, weil bildschreiben.py bewusst ohne Bibliothek auskommt.
# ----------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe


def _rahmen(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe, dicke: int = 4) -> None:
    """Ein NICHT gefüllter Rahmen — markiert, ohne die Fläche selbst zu übermalen."""
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    _rechteck(px, breite, hoehe, xa, ya, xb, ya + dicke, farbe)
    _rechteck(px, breite, hoehe, xa, yb - dicke, xb, yb, farbe)
    _rechteck(px, breite, hoehe, xa, ya, xa + dicke, yb, farbe)
    _rechteck(px, breite, hoehe, xb - dicke, ya, xb, yb, farbe)


# ----------------------------------------------------------------------------------
# Echter Aufruf — dieselbe Naht, die auch KosmoOrbit über MCP benutzen würde.
# ----------------------------------------------------------------------------------

def rufe_capabilities_echt() -> dict:
    """``mcp_server.rufe_werkzeug`` ist SDK-frei (Modul-Docstring dort) — genau darum
    hier statt eines direkten ``werkzeuge.capabilities({})``: Diese Funktion ist die
    Naht, die auch ein laufender MCP-Server benutzt, nicht bloss die Bibliothek
    dahinter."""
    antwort = mcp_server.rufe_werkzeug(WERKZEUG_FAEHIGKEITEN, {})
    if antwort.get("error"):
        raise SystemExit(f"Echter Aufruf von {WERKZEUG_FAEHIGKEITEN!r} schlug fehl: "
                          f"{antwort['error']}")
    return antwort


def zaehle_lizenzlage(notice_pfad: Path) -> dict:
    """``NOTICE`` ECHT einlesen und die drei möglichen ``AUFLOESUNG:``-Werte zählen
    (siehe NOTICE-Kopf, Zeilen 17-24). Keine Annahme, keine Schätzung — Textzählung."""
    text = notice_pfad.read_text(encoding="utf-8")
    treffer = re.findall(r"^AUFLOESUNG:\s*(\S+)", text, flags=re.MULTILINE)
    return {
        "prozessgrenze": treffer.count("Prozessgrenze"),
        "lizenzausnahme": treffer.count("Lizenzausnahme"),
        "offen": treffer.count("KEINE"),
        "gesamt": len(treffer),
    }


def ist_schwelle_kalibriert(vorbehalte: list) -> bool:
    """Kein eigenes Feld im Schema — der Kalibrierungsstand steht als Fliesstext in
    ``vorbehalte``. Ein 'NICHT kalibriert' zur Geometrie-Schwelle heisst: nein."""
    return not any("Geometrie-Schwelle" in v and "NICHT kalibriert" in v
                   for v in vorbehalte)


# ----------------------------------------------------------------------------------
# Zeichnen
# ----------------------------------------------------------------------------------

BREITE = 900
FUGENDICKE = 14
PANEL_HOEHE = 260
RAND = 40


def zeichne(antwort: dict, feldzahlen: dict, aktives_werkzeug: str,
            lizenz: dict) -> tuple[list, int, int]:
    hoehe = 3 * PANEL_HOEHE + 2 * FUGENDICKE
    px = _neues_bild(BREITE, hoehe)

    # ---- Panel oben: zugesagte Werkzeuge, Balkenhöhe = echte Feldzahl ----------
    werkzeuge = sorted(antwort["werkzeuge"])
    hoechste_feldzahl = max(feldzahlen[w] for w in werkzeuge)
    n = len(werkzeuge)
    spalte = (BREITE - 2 * RAND) / n
    balken_max = PANEL_HOEHE - 2 * RAND
    y_boden = RAND + balken_max
    for i, w in enumerate(werkzeuge):
        x0 = RAND + i * spalte + spalte * 0.15
        x1 = RAND + (i + 1) * spalte - spalte * 0.15
        anteil = feldzahlen[w] / hoechste_feldzahl
        y0 = y_boden - anteil * balken_max
        _rechteck(px, BREITE, hoehe, x0, y0, x1, y_boden, FARBE_WERKZEUG)
        if w == aktives_werkzeug:
            _rahmen(px, BREITE, hoehe, x0 - 4, y0 - 4, x1 + 4, y_boden + 4,
                    FARBE_RAHMEN_AKTIV)
    # Grüner Streifen: alle vier Verträge sind laut Schema readonly.
    alle_readonly = all(WERKZEUGE[w].get("readonly") for w in werkzeuge)
    if alle_readonly:
        _rechteck(px, BREITE, hoehe, RAND, y_boden + 8, BREITE - RAND, y_boden + 18,
                   FARBE_READONLY)

    fuge1_y0 = PANEL_HOEHE
    _rechteck(px, BREITE, hoehe, 0, fuge1_y0, BREITE, fuge1_y0 + FUGENDICKE, FARBE_FUGE)

    # ---- Panel Mitte: Schwelle auf 0..1-Skala, Farbe = Kalibrierungsstand ------
    panel2_y0 = fuge1_y0 + FUGENDICKE
    skala_x0, skala_x1 = RAND, BREITE - RAND - 140       # rechts Platz für die 2 Booleans
    skala_y0 = panel2_y0 + PANEL_HOEHE * 0.35
    skala_y1 = panel2_y0 + PANEL_HOEHE * 0.65
    _rahmen(px, BREITE, hoehe, skala_x0, skala_y0, skala_x1, skala_y1,
            FARBE_SKALA_RAHMEN, dicke=3)
    schwelle = antwort["geometrie_schwelle"]
    kalibriert = ist_schwelle_kalibriert(antwort["vorbehalte"])
    farbe_schwelle = FARBE_KALIBRIERT if kalibriert else FARBE_NICHT_KALIBRIERT
    fuellung_x1 = skala_x0 + schwelle * (skala_x1 - skala_x0)
    _rechteck(px, BREITE, hoehe, skala_x0 + 3, skala_y0 + 3, fuellung_x1, skala_y1 - 3,
              farbe_schwelle)

    # Zwei echte Wahrheitswerte aus prompt_sprache — gefüllt = wahr.
    ps = antwort["prompt_sprache"]
    booleans = [ps.get("uebersetzt_deutsch"), ps.get("warnt_bei_nicht_englisch")]
    bx = BREITE - RAND - 110
    for j, wert in enumerate(booleans):
        by0 = panel2_y0 + PANEL_HOEHE * 0.30 + j * 60
        by1 = by0 + 40
        if wert:
            _rechteck(px, BREITE, hoehe, bx, by0, bx + 40, by1, FARBE_WAHR)
        else:
            _rahmen(px, BREITE, hoehe, bx, by0, bx + 40, by1, FARBE_SKALA_RAHMEN, dicke=3)

    fuge2_y0 = panel2_y0 + PANEL_HOEHE
    _rechteck(px, BREITE, hoehe, 0, fuge2_y0, BREITE, fuge2_y0 + FUGENDICKE, FARBE_FUGE)

    # ---- Panel unten: Lizenzlage aus NOTICE, echt ausgezählt -------------------
    panel3_y0 = fuge2_y0 + FUGENDICKE
    balken_x0, balken_x1 = RAND, BREITE - RAND
    balken_y0 = panel3_y0 + PANEL_HOEHE * 0.30
    balken_y1 = panel3_y0 + PANEL_HOEHE * 0.55
    gesamt = lizenz["gesamt"] or 1
    x = balken_x0
    for anzahl, farbe in (
        (lizenz["prozessgrenze"], FARBE_PROZESSGRENZE),
        (lizenzausnahme := lizenz["lizenzausnahme"], FARBE_LIZENZAUSNAHME),
        (lizenz["offen"], FARBE_OFFEN),
    ):
        breite_segment = (balken_x1 - balken_x0) * (anzahl / gesamt)
        if breite_segment > 0:
            _rechteck(px, BREITE, hoehe, x, balken_y0, x + breite_segment, balken_y1, farbe)
        x += breite_segment

    # Vorbehalte als sichtbare Striche — die Menge, nicht nur ihre Zahl im Text.
    n_vorbehalte = len(antwort["vorbehalte"])
    strich_y0 = panel3_y0 + PANEL_HOEHE * 0.70
    strich_y1 = strich_y0 + 22
    strich_breite = 28
    luecke = 14
    for k in range(n_vorbehalte):
        sx0 = balken_x0 + k * (strich_breite + luecke)
        _rechteck(px, BREITE, hoehe, sx0, strich_y0, sx0 + strich_breite, strich_y1,
                   FARBE_OFFEN)

    return px, BREITE, hoehe


def _formatiere_zahl(x: float) -> str:
    if abs(x) >= 1000:
        return f"{x:.0f}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    antwort = rufe_capabilities_echt()
    print(f"Echt aufgerufen: mcp__aiimaging__{WERKZEUG_FAEHIGKEITEN} -> "
          f"{len(antwort['werkzeuge'])} Werkzeuge, "
          f"Schwelle {antwort['geometrie_schwelle']}, "
          f"{len(antwort['vorbehalte'])} Vorbehalte")

    feldzahlen = {name: len(WERKZEUGE[name].get("outputSchema", {}).get("properties", {}))
                  for name in antwort["werkzeuge"]}
    lizenz = zaehle_lizenzlage(WURZEL / "NOTICE")
    kalibriert = ist_schwelle_kalibriert(antwort["vorbehalte"])

    px, b, h = zeichne(antwort, feldzahlen, WERKZEUG_FAEHIGKEITEN, lizenz)

    name = (
        f"06_mcp_faehigkeiten_werkzeuge-{len(antwort['werkzeuge'])}"
        f"_schwelle-{_formatiere_zahl(antwort['geometrie_schwelle'])}"
        f"-{'kalibriert' if kalibriert else 'NICHTkalibriert'}"
        f"_lizenz-prozessgrenze{lizenz['prozessgrenze']}"
        f"-ausnahme{lizenz['lizenzausnahme']}-offen{lizenz['offen']}"
        f"_vorbehalte-{len(antwort['vorbehalte'])}.png"
    )
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
