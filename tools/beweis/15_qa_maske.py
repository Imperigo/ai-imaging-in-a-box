#!/usr/bin/env python3
"""BEWEIS 15 — ``maske.bauwerksmaske`` trennt das Bauwerk vom Gelände über den
Material-ID-Pass, und diese Trennung macht aus einer stumpfen Geometrie-QA eine scharfe:
Dieselbe Rangkorrelation, die über das ganze Bild ein verkehrt herum stehendes Bauwerk
durchwinkt, meldet über der Maske «genau umgekehrt».

Was bewiesen wird
-----------------
Drei Dinge, an einer synthetischen Szene mit bekannter Wahrheit:

1. **Die Maske entsteht aus dem Material-ID-Pass**, ohne zweite Aufnahme: Ein PNG mit
   Kennfarben plus die ``material_id_tabelle`` des Reports → ``maske.bauwerksmaske``.
   Die Geländeregel (``GELAENDE_MUSTER``, hier greift ``ifcsite*``) sortiert die
   Tabelleneinträge; das Ergebnis nennt, was sie wohin sortiert hat.
2. **Die Soll-Karte ohne Boden ist eine andere Karte.** Rund 52 % der Bildpunkte sind
   hier Gelände — eine Rampe von unten nach oben. Was nach der Maske übrig bleibt, ist
   das Bauwerk allein: rund 16 % des Bildes, ohne Rampe (die genauen Zahlen stehen im
   Dateinamen von Bild 03 und werden im Lauf gezählt).
3. **Der Kern:** ``geom_iou`` und ρ, je einmal über das ganze Bild
   (``geometrie_qa.geometrie_gate``) und einmal über die Maske
   (``geometrie_qa.rho_ueber_maske``), an DERSELBEN Szene und DENSELBEN Ist-Karten.
   Vier Fälle, die Wahrheit steht vor der Messung fest:

       treu       Ist = Soll. Nullprobe: beide Wege müssen 1.000 geben.
       umgekehrt  Der Boden stimmt, das Bauwerk steht in der Tiefe verkehrt herum
                  (innerhalb der Maske: nah ↔ fern gespiegelt). Über das ganze Bild
                  trägt die Bodenrampe die Korrelation — das Tor lässt es DURCH. Über
                  der Maske ist ρ exakt −1: genau umgekehrt. Das ist der Fall, für den
                  die Maske gebaut wurde.
       rampe      Ist = eine reine Rampe von unten (nah) nach oben (fern), über die
                  ganze Silhouette — das, was ein monokularer Schätzer in eine
                  strukturlose Fläche legt (``maske``-Modulkopf). Über das ganze Bild
                  korreliert Rampe mit Rampe; über der Maske steht eine Fassade, deren
                  Tiefe von links nach rechts läuft, und die Rampe weiss davon nichts.
                  Ihr kleiner y-Anteil läuft sogar gegen die Rampe (unten ferner statt
                  näher) — ρ über der Maske fällt darum leicht unter Null.
       versatz    Reihe: das Bauwerk in der Ist-Karte um 0, 2, 4, 8, 16 Bildpunkte nach
                  rechts versetzt, der Boden unverändert. Die Frage aus
                  ``docs/MASKE_2026-08-21.md``: Ist ρ über der Maske MONOTON im Versatz?
                  (Über das ganze Bild war es dort nicht: 4 m stand besser da als 2 m.)

Woran man es im Bild sieht
--------------------------
Alle Karten sind 96×96, viermal vergrössert (nächster Nachbar, nichts interpoliert).

    01  Material-ID-Pass — das PNG, aus dem die Maske gelesen wird. Kennfarben aus der
        Palette des Runners (``hsv(i·0.618, 0.85, 1.0)``), Himmel schwarz.
    02  Die Sortierung der Regel: Orange = Einträge, die die Geländeregel als Gelände
        eingeordnet hat; Blau = Bauwerkseinträge; Schwarz = Hintergrund. Die Farben
        stammen aus ``gelaende_namen``/``bauwerk_namen`` des Ergebnisses, nicht aus der
        Szenenbeschreibung — sie zeigen, was die Regel getan hat.
    03  Die fertige Maske: Weiss = Bauwerk, Schwarz = alles andere. ``n_bauwerk`` und
        ``anteil_bauwerk`` im Dateinamen.
    04  Soll-Karte MIT Boden — Tiefe, nah = hell (``bildschreiben.normalisiere_tiefe``).
        Die helle Rampe unten ist der Boden.
    05  Soll-Karte OHNE Boden — dieselbe Karte, maskiert: Nur das Bauwerk, über sich
        selbst normalisiert. Die Rampe ist weg; übrig bleibt die Fassade von links (nah)
        nach rechts (fern) mit dem vorspringenden Flügel.
    je Fall  ``NN_<fall>_ist_…png`` (Ist-Karte mit Boden), ``NN_<fall>_ist_nur-maske_…png``
        (dieselbe Ist-Karte, maskiert), und ``NN_<fall>_nebeneinander_…png``: drei Kacheln
        Soll-mit-Boden | Ist | Ist-nur-Maske, darunter ZWEI Streifen:
            oberer Streifen  = Urteil über das GANZE Bild (``geometrie_gate``,
                               Schwelle 0.65): Grün bestanden, Rot durchgefallen.
            unterer Streifen = ρ über der MASKE gegen ``PAAR_RHO_SCHWELLE`` (0.80):
                               Grün darüber, Rot darunter, Grau nicht gemessen.
        Im Fall «umgekehrt» ist der obere Streifen grün und der untere rot — das ist der
        Beweis in zwei Farben. Die Zahlen stehen im Dateinamen
        (``rho-ganz``, ``iou-ganz``, ``rho-maske``, ``iou-maske``).
    Balken  ``NN_balken_…png`` — je Fall eine Vierergruppe: Blau = ρ über das ganze
        Bild, Dunkelblau = ρ über der Maske, Orange = ``geom_iou`` über das ganze Bild,
        Hellorange = ``geom_iou`` über der Maske. Graue Linien bei 0 und 1, rote Linie
        bei 0.80 (``PAAR_RHO_SCHWELLE``, Konstante des Moduls — die einzige nicht in
        diesem Lauf gemessene Zahl im Bild). Negative Balken hängen unter die Nulllinie.
    Reihe   ``NN_reihe_versatz_…png`` — fünf Gruppen von links nach rechts, Versatz
        0/2/4/8/16 px; je Gruppe Blau = ρ ganz, Dunkelblau = ρ Maske, Grau = Score ganz,
        Hellorange = ``geom_iou`` über der Maske. Die Reihe über der Maske fällt mit
        jedem Schritt, von 1 bis unter Null; ob die über das ganze Bild das auch tut,
        steht im Dateinamen (``monoton-ja``/``monoton-nein``) und ist gemessen. Sichtbar
        ist so oder so: Über das ganze Bild bewegt sich ρ kaum vom Balkenrand weg — der
        Boden trägt es, gleichgültig, wo das Bauwerk steht. Die Hellorange-Säule zeigt,
        was der Abschnitt oben behauptet und die anderen drei Fälle nicht zeigen können,
        weil dort konstruktionsbedingt immer 1.000 steht: Erst hier, wo das Bauwerk aus
        seiner Maske herauswandert, fällt ``geom_iou`` über der Maske mit — von 1.000 auf
        0.630 bei 16 px (die genauen Werte stehen im Dateinamen). Negative Zahlen stehen
        in Dateinamen als ``minus0.607``, weil ein zweiter Bindestrich nicht lesbar wäre.

Was ``geom_iou`` über der Maske bedeutet — und was nicht
--------------------------------------------------------
``geometrie_qa`` sagt im Maskenabschnitt: Über der Maske ist ``geom_iou``
konstruktionsbedingt 1, weil innerhalb der Maske die Soll-Karte überall Geometrie trägt.
Es wird hier trotzdem gerechnet und gezeigt, weil der Auftrag es verlangt und weil man
es sehen soll: In den Fällen treu/umgekehrt/rampe steht es auf 1.000 — es misst dort
nichts. Erst im Versatz fällt es, weil die Ist-Karte an der alten Bauwerksstelle
Himmel trägt; dort misst es, wie viel der Maske die Ist-Karte überhaupt füllt.

Was dieser Beweis NICHT zeigt — und was das Gerät braucht
---------------------------------------------------------
Im Betrieb kommt die Ist-Karte aus einem monokularen Tiefenschätzer (Gewichte, GPU).
Die Zahlen des Modulkopfs von ``maske`` — Rauschen erreicht über das ganze Bild 0.72,
über der Maske ρ = −0.52 — sind Zahlen über den SCHÄTZER und hier nicht reproduzierbar:
Ohne Schätzer gibt es keinen Grund, warum aus Rauschen eine Rampe würde. Der Fall
«rampe» zeigt darum das ERGEBNIS jener Beobachtung (der Schätzer liefert eine Rampe) als
gebaute Karte, nicht ihre Entstehung. Alles hier läuft ohne Gerät, ohne Blender, ohne
numpy — reine stdlib (Regel 4). Die Szene ist synthetisch (Regel 3) und entsteht in
``baue_szene`` unten: Boden als Lochkamera-Rampe (Kamerahöhe 1,6 m), Fassade schräg,
ein Flügel springt vor.

Aufruf:
    python3 tools/beweis/15_qa_maske.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/15_qa_maske/``. Rückgabe 1, wenn die
Nullprobe (treu) auf einem der beiden Wege nicht 1.000 liefert oder die Maske nicht
entsteht — das wäre ein Befund gegen Metrik oder Maske, nicht gegen die Szene.
"""
from __future__ import annotations

import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildschreiben, geometrie_qa, maske  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "15_qa_maske"

#: Kantenlänge der Karten. 96: gross genug für einen Boden mit echter Perspektive und
#: ein Bauwerk mit über 1000 Punkten, klein genug für reine Python-Rasterung.
KANTE = 96
VERGROESSERUNG = 4
KACHEL = KANTE * VERGROESSERUNG
FUGE = 8

#: Die Szene. Horizont bei Zeile 42; die Kamera steht waagrecht 1,6 m über dem Boden,
#: Brennweite = Bildhöhe in Bildpunkten. Damit liegt die Bodentiefe in Zeile 50 bei
#: rund 18 m — dort steht der Fuss des Bauwerks, und die Fassade beginnt bei 18 m.
HORIZONT = 42
KAMERAHOEHE_M = 1.6
BRENNWEITE_PX = float(KANTE)
BAU_X0, BAU_X1 = 30, 66
BAU_DACH, BAU_FUSS = 8, 50
NAH_M, FERN_M = 18.0, 27.0
HINTERGRUND_M = 1.0e10

#: Versatz-Reihe in Bildpunkten. 16 px sind fast die halbe Bauwerksbreite (36 px).
VERSAETZE = (0, 2, 4, 8, 16)

# Kennfarben der Runner-Palette für die Indizes 0..3 — dieselben Werte, die in
# docs/MASKE_2026-08-21.md in der gemessenen Tabelle stehen und in tests/test_maske.py
# als Konstanten liegen. Nicht nachgerechnet: Die Tabelle ist der Schlüssel, nicht die
# Formel (maske.tabelle_aus_report).
FARBE_GELAENDE = (255, 38, 38)
FARBE_SOCKEL = (38, 101, 255)
FARBE_FASSADE = (165, 255, 38)
FARBE_FLUEGEL = (255, 38, 228)

# Namen, wie der glb-Export sie liefert: IFC-Klasse, Name, angehängte Kennung. Die
# Kennungen sind erfunden (Regel 3).
NAME_GELAENDE = "IfcSite_Gelaende_0synth0000000000001"
NAME_SOCKEL = "IfcSlab_Sockel_0synth0000000000002"
NAME_FASSADE = "IfcWall_Fassade_0synth0000000000003"
NAME_FLUEGEL = "IfcWall_Fluegel_0synth0000000000004"

FARBE_HINTERGRUND = (0, 0, 0)
FARBE_ALS_GELAENDE = (230, 120, 40)     # Orange: von der Regel als Gelände eingeordnet
FARBE_ALS_BAUWERK = (50, 110, 210)      # Blau: Bauwerk
FARBE_MASKE_AN = (235, 235, 235)
FARBE_RHO_GANZ = (50, 110, 210)
FARBE_RHO_MASKE = (20, 45, 110)
FARBE_IOU_GANZ = (230, 120, 40)
FARBE_IOU_MASKE = (245, 190, 130)
FARBE_SCORE = (110, 110, 110)
FARBE_BESTANDEN = (60, 150, 70)
FARBE_DURCHGEFALLEN = (190, 60, 50)
FARBE_NICHT_GEMESSEN = (150, 150, 150)
FARBE_SCHWELLE = (190, 60, 50)
FARBE_LEINWAND = (245, 245, 245)
FARBE_ACHSE = (120, 120, 120)


# ----------------------------------------------------------------------------------
# Die Szene — Boden, Bauwerk, Himmel; Tiefe und Material-ID aus derselben Rasterung
# ----------------------------------------------------------------------------------

def _bodentiefe(y: int) -> float:
    """Lochkamera: Ein Bodenpunkt in Zeile ``y`` unter dem Horizont liegt
    ``h · f / (y − Horizont)`` Meter entfernt. Nah unten, fern am Horizont."""
    return KAMERAHOEHE_M * BRENNWEITE_PX / (y + 0.5 - HORIZONT)


def _fassadentiefe(x: int, y: int) -> float:
    """Schräg stehende Fassade: Tiefe läuft von links (nah) nach rechts (fern).

    Ein kleiner, inkommensurabler Anteil in y (√2 · 0.15) verhindert Bindungen —
    ohne ihn trüge jede Spalte einen einzigen Wert, und die Rangkorrelation rechnete
    über Bindungsgruppen (Befund der Schwellenstudie vom 18.08.2026). Der Flügel
    springt um ein Drittel der Bautiefe vor.
    """
    wurzel_zwei = 1.41421356237309504880
    ax = (x - BAU_X0) / (BAU_X1 - BAU_X0 - 1)
    ay = (y - BAU_DACH) / (BAU_FUSS - BAU_DACH - 1)
    gewicht_y = 0.15 * wurzel_zwei
    anteil = (ax + gewicht_y * ay) / (1.0 + gewicht_y)
    tiefe = NAH_M + anteil * (FERN_M - NAH_M)
    if _ist_fluegel(x, y):
        tiefe -= (FERN_M - NAH_M) / 3.0
    return tiefe


def _ist_fluegel(x: int, y: int) -> bool:
    mitte = BAU_X0 + (BAU_X1 - BAU_X0) // 2
    oben = BAU_DACH + (BAU_FUSS - BAU_DACH) // 4
    unten = BAU_FUSS - (BAU_FUSS - BAU_DACH) // 4
    return x < mitte and oben <= y < unten


def _ist_sockel(y: int) -> bool:
    return y >= BAU_FUSS - 3


def baue_szene(versatz_px: int = 0) -> tuple[list[float], list[tuple[int, int, int]]]:
    """Soll-Tiefenkarte und Material-ID-Pass aus einer Rasterung.

    ``versatz_px`` verschiebt nur das Bauwerk; Boden und Horizont bleiben, wo sie sind.
    Wo das Bauwerk hinrückt, verdeckt es Boden oder Himmel; wo es wegrückt, kommt
    wieder Boden (unter dem Horizont) oder Himmel (darüber) zum Vorschein — wie bei
    einer echten Kamera.
    """
    tiefe = [HINTERGRUND_M] * (KANTE * KANTE)
    farben = [FARBE_HINTERGRUND] * (KANTE * KANTE)
    for y in range(KANTE):
        for x in range(KANTE):
            i = y * KANTE + x
            if y > HORIZONT:
                tiefe[i] = _bodentiefe(y)
                farben[i] = FARBE_GELAENDE
            xb = x - versatz_px
            if BAU_X0 <= xb < BAU_X1 and BAU_DACH <= y < BAU_FUSS:
                tiefe[i] = _fassadentiefe(xb, y)
                if _ist_sockel(y):
                    farben[i] = FARBE_SOCKEL
                elif _ist_fluegel(xb, y):
                    farben[i] = FARBE_FLUEGEL
                else:
                    farben[i] = FARBE_FASSADE
    return tiefe, farben


def _eintrag(index: int, name: str, farbe) -> dict:
    """Ein Eintrag der ``material_id_tabelle``, in der Form, die der Runner schreibt."""
    return {"index": index, "name": name, "quelle": "objekt",
            "farbe_srgb": [k / 255.0 for k in farbe], "farbe_srgb_8bit": list(farbe)}


TABELLE = [
    _eintrag(0, NAME_GELAENDE, FARBE_GELAENDE),
    _eintrag(1, NAME_SOCKEL, FARBE_SOCKEL),
    _eintrag(2, NAME_FASSADE, FARBE_FASSADE),
    _eintrag(3, NAME_FLUEGEL, FARBE_FLUEGEL),
]


# ----------------------------------------------------------------------------------
# Die Ist-Karten — jede eine bekannte Abweichung vom Soll
# ----------------------------------------------------------------------------------

def ist_treu(soll, m):
    return list(soll)


def ist_umgekehrt(soll, m):
    """Innerhalb der Maske nah ↔ fern gespiegelt; Boden und Himmel unverändert."""
    werte = [soll[k] for k in range(len(soll)) if m[k]]
    lo, hi = min(werte), max(werte)
    return [lo + hi - soll[k] if m[k] else soll[k] for k in range(len(soll))]


def ist_rampe(soll, m):
    """Eine Rampe von unten (nah) nach oben (fern) über die ganze Silhouette — die
    Karte, die ein Schätzer in eine strukturlose Fläche legt. Ein winziger x-Anteil
    bricht die Bindungen innerhalb einer Zeile; die Ordnung bleibt eine reine Rampe."""
    sil = geometrie_qa.silhouette(soll)
    aus = []
    for i, an in enumerate(sil):
        y, x = divmod(i, KANTE)
        aus.append(float(KANTE - y) + x * 1e-4 if an else HINTERGRUND_M)
    return aus


FAELLE = (
    ("treu", "ist-gleich-soll", ist_treu),
    ("umgekehrt", "bauwerk-nah-fern-gespiegelt-boden-stimmt", ist_umgekehrt),
    ("rampe", "reine-rampe-unten-nah-oben-fern", ist_rampe),
)


# ----------------------------------------------------------------------------------
# Messen — beide Wege, dieselben Karten
# ----------------------------------------------------------------------------------

def iou_ueber_maske(soll, ist, m) -> float | None:
    """``geom_iou``, eingeschränkt auf die Maskenpunkte. Innerhalb der Maske trägt das
    Soll überall Geometrie — der Wert sagt darum nur, wie viel der Maske die Ist-Karte
    füllt (siehe Docstring oben)."""
    sil_soll = geometrie_qa.silhouette(soll)
    sil_ist = geometrie_qa.silhouette(ist)
    a = [sil_soll[k] for k in range(len(m)) if m[k]]
    b = [sil_ist[k] for k in range(len(m)) if m[k]]
    try:
        return geometrie_qa.iou(a, b)
    except geometrie_qa.QaError:
        return None


def messe(soll, ist, m) -> dict:
    ganz = geometrie_qa.geometrie_gate(soll, ist, polaritaet=geometrie_qa.POLARITAET_TIEFE)
    ueber_maske = geometrie_qa.rho_ueber_maske(soll, ist, m,
                                               polaritaet=geometrie_qa.POLARITAET_TIEFE)
    gerichtet = ueber_maske["gerichtet"]
    return {
        "rho_ganz": ganz["spearman"],
        "iou_ganz": ganz["geom_iou"],
        "score_ganz": ganz["score"],
        "bestanden_ganz": ganz["bestanden"],
        "rho_maske": ueber_maske["rho"],
        "gerichtet_maske": gerichtet,
        "iou_maske": iou_ueber_maske(soll, ist, m),
        "bestanden_maske": (None if gerichtet is None
                            else gerichtet >= geometrie_qa.PAAR_RHO_SCHWELLE),
        "n_maske": ueber_maske["n_maske"],
    }


# ----------------------------------------------------------------------------------
# Kacheln
# ----------------------------------------------------------------------------------

def kachel_tiefe(karte, m=None) -> list[tuple[int, int, int]]:
    """Tiefe → Grau, nah = hell, Hintergrund schwarz — mit
    ``bildschreiben.normalisiere_tiefe``, der Referenz des Projekts. Mit ``m`` wird
    alles ausserhalb der Maske zu Hintergrund, und normalisiert wird über den Rest."""
    if m is not None:
        karte = [karte[k] if m[k] else HINTERGRUND_M for k in range(len(karte))]
    grau, _ = bildschreiben.normalisiere_tiefe(karte)
    return [(int(round(g * 255)),) * 3 for g in grau]


def kachel_sortierung(farben, ergebnis) -> list[tuple[int, int, int]]:
    """Was die Regel wohin sortiert hat — aus dem Ergebnis, nicht aus der Szene."""
    nach_farbe = {tuple(e["farbe_srgb_8bit"]): e["name"] for e in TABELLE}
    gelaende = set(ergebnis["gelaende_namen"]) | set(ergebnis["umfeld_namen"])
    aus = []
    for f in farben:
        name = nach_farbe.get(tuple(f))
        if name is None:
            aus.append(FARBE_HINTERGRUND)
        elif name in gelaende:
            aus.append(FARBE_ALS_GELAENDE)
        else:
            aus.append(FARBE_ALS_BAUWERK)
    return aus


def kachel_maske(m) -> list[tuple[int, int, int]]:
    return [FARBE_MASKE_AN if an else FARBE_HINTERGRUND for an in m]


def vergroessere(kachel, kante: int = KANTE, faktor: int = VERGROESSERUNG):
    aus = []
    for y in range(kante * faktor):
        zeile = kachel[(y // faktor) * kante:(y // faktor + 1) * kante]
        for x in range(kante * faktor):
            aus.append(zeile[x // faktor])
    return aus


def _urteilsfarbe(bestanden) -> tuple[int, int, int]:
    if bestanden is None:
        return FARBE_NICHT_GEMESSEN
    return FARBE_BESTANDEN if bestanden else FARBE_DURCHGEFALLEN


def nebeneinander(kacheln, urteile, *, streifen: int = 14):
    """Kacheln mit Fuge, darunter je Urteil ein Streifen — oben ganzes Bild, unten Maske."""
    n = len(kacheln)
    breite = n * KACHEL + (n - 1) * FUGE
    hoehe = KACHEL + FUGE + len(urteile) * (streifen + 2)
    px = [FARBE_LEINWAND] * (breite * hoehe)
    for k, kachel in enumerate(kacheln):
        x0 = k * (KACHEL + FUGE)
        for y in range(KACHEL):
            px[y * breite + x0:y * breite + x0 + KACHEL] = kachel[y * KACHEL:(y + 1) * KACHEL]
    y = KACHEL + FUGE
    for urteil in urteile:
        farbe = _urteilsfarbe(urteil)
        for yy in range(y, y + streifen):
            px[yy * breite:(yy + 1) * breite] = [farbe] * breite
        y += streifen + 2
    return px, breite, hoehe


# ----------------------------------------------------------------------------------
# Balken — nur Zahlen aus diesem Lauf, eine Achse von −1 bis 1
# ----------------------------------------------------------------------------------

def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe


def zeichne_gruppen(gruppen: list[list[tuple[float | None, tuple[int, int, int]]]],
                    urteile: list[list] | None = None, *,
                    breite: int = 760, hoehe: int = 400, rand: int = 40,
                    schwelle: float | None = geometrie_qa.PAAR_RHO_SCHWELLE):
    """Gruppen von Balken. Jede Gruppe: Liste von (Wert, Farbe); ``None`` lässt eine
    Lücke. Achse von −1 bis 1, damit negative ρ unter der Nulllinie hängen. Unter jeder
    Gruppe optional Urteilsquadrate (oben ganz, unten Maske)."""
    px = [FARBE_LEINWAND] * (breite * hoehe)
    unten, oben = -1.0, 1.0
    fuss = 40 if urteile else 0
    plot_oben, plot_unten = rand, hoehe - rand - fuss

    def y_von(v: float) -> float:
        return plot_unten - (v - unten) / (oben - unten) * (plot_unten - plot_oben)

    for linie, farbe in ((0.0, FARBE_ACHSE), (1.0, FARBE_ACHSE), (-1.0, FARBE_ACHSE)):
        _rechteck(px, breite, hoehe, rand, y_von(linie), breite - rand, y_von(linie) + 1, farbe)
    if schwelle is not None:
        _rechteck(px, breite, hoehe, rand, y_von(schwelle), breite - rand,
                  y_von(schwelle) + 1, FARBE_SCHWELLE)

    n = len(gruppen)
    gruppen_breite = (breite - 2 * rand) / n
    for g, gruppe in enumerate(gruppen):
        balken_breite = gruppen_breite / (len(gruppe) + 1.5)
        x_start = rand + g * gruppen_breite + balken_breite * 0.75
        for k, (v, farbe) in enumerate(gruppe):
            if v is None:
                continue
            x0 = x_start + k * balken_breite
            _rechteck(px, breite, hoehe, x0 + 2, y_von(v), x0 + balken_breite - 2,
                      y_von(0.0), farbe)
        if urteile:
            mitte = rand + (g + 0.5) * gruppen_breite
            for r, urteil in enumerate(urteile[g]):
                y0 = plot_unten + 8 + r * 18
                _rechteck(px, breite, hoehe, mitte - 8, y0, mitte + 8, y0 + 14,
                          _urteilsfarbe(urteil))
    return px, breite, hoehe


def _z(x) -> str:
    """Zahl für den Dateinamen. Negative als ``minus…``: ``rho-maske--1.000`` liest
    niemand richtig."""
    return "None" if x is None else f"{x:.3f}".replace("-", "minus")


def _monoton_fallend(werte) -> bool:
    return all(a > b for a, b in zip(werte, werte[1:]))


# ----------------------------------------------------------------------------------

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

    soll, farben = baue_szene()

    # ── 1. Der Material-ID-Pass als Datei, und die Maske daraus über den Dateiweg ──
    # Geschrieben, gelesen, sortiert — derselbe Weg wie im Betrieb
    # (maske.bauwerksmaske_aus_lauf liest das PNG und die Tabelle des Reports).
    material_png = schreibe("material-id-pass_4-eintraege_himmel-schwarz",
                            vergroessere(farben), KACHEL, KACHEL)
    # Für die Maske zählt die Karte in Originalgrösse — indexgleich zur Tiefe.
    klein_png = ziel / "_material_id_96px.png"
    bildschreiben.schreibe_farb_png(klein_png, farben, KANTE, KANTE)
    report = {"material_id_tabelle": TABELLE, "material_id_quelle": ["objekt"]}
    ergebnis = maske.bauwerksmaske_aus_lauf(klein_png, report)
    klein_png.unlink()
    m = ergebnis["maske"]
    if m is None:
        print("KEINE MASKE: " + " ".join(ergebnis["warnungen"]), file=sys.stderr)
        return 1
    assert material_png.exists()

    gelaende_kurz = "+".join(n.split("_")[1] for n in ergebnis["gelaende_namen"]) or "keines"
    schreibe(f"regel_gelaende-orange-{gelaende_kurz}_bauwerk-blau-"
             f"{len(ergebnis['bauwerk_namen'])}-eintraege",
             vergroessere(kachel_sortierung(farben, ergebnis)), KACHEL, KACHEL)
    schreibe(f"maske_bauwerk-weiss_n-{ergebnis['n_bauwerk']}_anteil-"
             f"{ergebnis['anteil_bauwerk']:.3f}_gelaende-{ergebnis['n_gelaende']}",
             vergroessere(kachel_maske(m)), KACHEL, KACHEL)

    # ── 2. Soll mit und ohne Boden ──
    sil_soll = geometrie_qa.silhouette(soll)
    n_geometrie = sum(sil_soll)
    kachel_soll_mit = vergroessere(kachel_tiefe(soll))
    schreibe(f"soll_mit-boden_nah-hell_geometrie-{n_geometrie}_boden-{ergebnis['n_gelaende']}",
             kachel_soll_mit, KACHEL, KACHEL)
    schreibe(f"soll_ohne-boden_nur-maske_n-{ergebnis['n_bauwerk']}",
             vergroessere(kachel_tiefe(soll, m)), KACHEL, KACHEL)

    # ── 3. Die Fälle: beide Wege, dieselben Karten ──
    messungen: list[dict] = []
    for name, beschreibung, baue in FAELLE:
        ist = baue(soll, m)
        e = messe(soll, ist, m)
        messungen.append(e)
        k_ist = vergroessere(kachel_tiefe(ist))
        k_ist_maske = vergroessere(kachel_tiefe(ist, m))
        schreibe(f"{name}_ist_{beschreibung}", k_ist, KACHEL, KACHEL)
        schreibe(f"{name}_ist_nur-maske", k_ist_maske, KACHEL, KACHEL)
        px, b, h = nebeneinander([kachel_soll_mit, k_ist, k_ist_maske],
                                 [e["bestanden_ganz"], e["bestanden_maske"]])
        schreibe(f"{name}_nebeneinander_rho-ganz-{_z(e['rho_ganz'])}_iou-ganz-"
                 f"{_z(e['iou_ganz'])}_rho-maske-{_z(e['rho_maske'])}_iou-maske-"
                 f"{_z(e['iou_maske'])}", px, b, h)

    gruppen = [[(e["rho_ganz"], FARBE_RHO_GANZ), (e["rho_maske"], FARBE_RHO_MASKE),
                (e["iou_ganz"], FARBE_IOU_GANZ), (e["iou_maske"], FARBE_IOU_MASKE)]
               for e in messungen]
    urteile = [[e["bestanden_ganz"], e["bestanden_maske"]] for e in messungen]
    px, b, h = zeichne_gruppen(gruppen, urteile)
    schreibe("balken_rho-ganz-blau_rho-maske-dunkelblau_iou-ganz-orange_iou-maske-hell_"
             + "_".join(f"{n}-{_z(e['rho_ganz'])}-vs-{_z(e['rho_maske'])}"
                        for (n, _, _), e in zip(FAELLE, messungen))
             + f"_schwelle-{geometrie_qa.PAAR_RHO_SCHWELLE:.2f}", px, b, h)

    # ── 4. Die Versatz-Reihe ──
    reihe: list[dict] = []
    for v in VERSAETZE:
        ist, _ = baue_szene(v)
        reihe.append(messe(soll, ist, m))
    gruppen = [[(e["rho_ganz"], FARBE_RHO_GANZ), (e["rho_maske"], FARBE_RHO_MASKE),
                (e["score_ganz"], FARBE_SCORE), (e["iou_maske"], FARBE_IOU_MASKE)]
               for e in reihe]
    px, b, h = zeichne_gruppen(gruppen, schwelle=None)
    mono_maske = _monoton_fallend([e["rho_maske"] for e in reihe])
    mono_ganz = _monoton_fallend([e["rho_ganz"] for e in reihe])
    schreibe("reihe_versatz-" + "-".join(str(v) for v in VERSAETZE) + "px_rho-maske-"
             + "-".join(_z(e["rho_maske"]) for e in reihe)
             + f"_monoton-{'ja' if mono_maske else 'nein'}_rho-ganz-"
             + "-".join(_z(e["rho_ganz"]) for e in reihe)
             + f"_monoton-{'ja' if mono_ganz else 'nein'}_iou-maske-"
             + "-".join(_z(e["iou_maske"]) for e in reihe), px, b, h)

    for p in geschrieben:
        print(p)

    treu = messungen[0]
    for feld in ("score_ganz", "rho_maske"):
        wert = treu[feld]
        if wert is None or abs(wert - 1.0) > 1e-9:
            print(f"NULLPROBE VERFEHLT: treu gibt {feld}={wert!r} statt 1.000 — Befund "
                  f"gegen die Metrik, nicht gegen die Szene.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
