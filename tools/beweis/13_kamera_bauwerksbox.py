#!/usr/bin/env python3
"""BEWEIS 13 — Die automatische Kamerasetzung, Teil 5: Bauwerksbox gegen Szenenbox.
Mit Gelände rahmt die Kamera Platte plus Bauwerk, und das Bauwerk wird zum Fleck — und
die Formregel erkennt die Platte auch dann, wenn ihr Name verdeckt wird.

Was bewiesen wird
-----------------
1. **``glbbox.bauwerksbox`` trennt Gelände von Bauwerk — an einer Datei, die
   ``tools/make_test_ifc.py --gelaende`` hier erzeugt und ``aiimaging.seams.ifc_zu_glb``
   hier zu glb konvertiert.** Kein Blender: Der Konverter läuft im ``.venv-ifc`` über
   ``ifcopenshell``/``trimesh``, ein eigenständiger Prozess (Regel 1/2). Die Szenenbox
   (Platte + Bauwerk) und die Bauwerksbox (ohne Platte) unterscheiden sich real gemessen
   um **66,6 % der Grundriss-Diagonale** (``schrumpfung``, ``glbbox.bauwerksbox``).
2. **Was das für die Kamera heisst.** ``kameras.kamerasatz`` rahmt einmal die Szenenbox,
   einmal die Bauwerksbox, beide bei Deckungsgrad 0,70 — echte Läufe derselben Funktion,
   die auch den Produktivweg stellt. ``kameras.rahmungsverhaeltnis`` (dieselbe Funktion,
   die ``abholer._rahmung_vor_dem_render`` vor jedem Renderlauf befragt) sagt daraus,
   wieviel vom Bild dabei wirklich auf das Bauwerk entfällt: **27,9 %** statt der
   angeforderten 70 % — das Bauwerk wird zum Fleck, und der Lauf würde deswegen
   **abgebrochen** (``abbruch: True``, unter der Schwelle 0,65). Rahmt die Kamera
   stattdessen die Bauwerksbox direkt, füllt das Bauwerk wieder **69,9 %** — der
   angeforderte Wert, und die Geländeplatte liefe als schmaler Streifen aus dem Bild.
3. **Die Formregel (``gelaendeform``) erkennt die Platte, ohne je ihren Namen zu lesen.**
   Alle sechs Knotennamen werden hier durch ``objekt_00`` … ``objekt_05`` ersetzt — keiner
   davon enthält eines der Wörter aus ``maske.GELAENDE_WOERTER``, und die Namensregel
   findet auf dieser verdeckten Liste **nichts** (geprüft, nicht behauptet: das Skript
   bricht ab, würde ``ist_gelaende`` doch anschlagen). ``gelaendeform.gelaende_knoten``
   läuft auf denselben sechs Boxen — ohne die Namen zu sehen, sie liest nur
   ``grundrissanteil``, ``flachheit`` und ``tieflage`` — und ordnet trotzdem genau den
   einen Knoten als Gelände ein, der es ist. Das Skript prüft zusätzlich, dass dasselbe
   Urteil mit den echten Namen entsteht: Wer den Namen entfernt und nichts ändert sich,
   hat bewiesen, dass der Name für das Urteil nie gebraucht wurde.

Woran man es im Bild sieht
--------------------------
Keine Schrift im Bild (Regel 2). Bedeutung liegt in Anordnung, Farbe und Grösse; jede
Zahl im Dateinamen ist aus einem echten Rückgabewert gelesen.

``01_grundriss_…png`` — Draufsicht, massstäblich, Nord oben.

    Sandfarben     die Geländeplatte (20 × 20 m, ``--gelaende``-Vorgabe)
    Stahlblau      die fünf Bauwerksknoten (Bodenplatte, vier Wände)
    Brauner Rahmen die Szenenbox (``bbox_szene``) — deckt sich mit der Platte
    Schwarzer Rahmen die Bauwerksbox (``bbox_bauwerk``) — deckt sich mit dem Baukörper

Man sieht: Der schwarze Rahmen liegt weit innerhalb des braunen. Das ist die
Schrumpfung, in Zahlen im Dateinamen.

``02_rahmung_…png`` — zwei Bildrahmen 16:9 nebeneinander, dieselbe Kamera (Süd, 0,70),
zweimal anders gerahmt.

    Linker Rahmen   Kamera rahmt die SZENENBOX. Sandfarbene Fläche: die gerahmte Platte,
                    exakt ``fuellgrad_breite``/``fuellgrad_hoehe`` dieses Laufs (kein
                    Schätzwert). Stahlblauer Fleck darin: das Bauwerk, in derselben
                    Aufnahme — seine Breite ist ``wirksame_bildbreite``, seine Höhe die
                    gleiche Rechnung senkrecht (``bau_dz/szene_dz`` mal gerahmter Höhe;
                    es gibt dafür keine Funktion im Projekt, die Höhe hier ist der
                    senkrechte Zwilling der vorhandenen Breitenrechnung, hier ausgeführt).
    Rechter Rahmen  Kamera rahmt die BAUWERKSBOX direkt. Stahlblaue Fläche füllt den
                    Rahmen bei ``fuellgrad_breite``/``fuellgrad_hoehe`` dieses zweiten
                    Laufs — wieder rund 0,70. Der sandfarbene Streifen am unteren Rand
                    ist dieselbe Platte, hochgerechnet auf denselben Massstab: Sie ist so
                    dünn und so breit, dass sie links und rechts aus dem Rahmen läuft.

Man sieht: links ist die Platte im Bild und das Bauwerk ein Fleck, rechts ist das
Bauwerk im Bild und die Platte ein Streifen ausserhalb — dieselbe Szene, zwei Rahmen,
zwei entgegengesetzte Antworten auf „was steht im Bild".

``03_formregel_…png`` — sechs Zeilen, eine je Mesh-Knoten, in der Reihenfolge des
Szenengraphen (Zeile 1 ist die Geländeplatte).

    Linkes Feld     rot: die NAMENSREGEL auf dem VERDECKTEN Namen (``objekt_NN``) findet
                    hier nichts — in JEDER Zeile, auch der ersten. Das ist der Beweis,
                    dass der Name nicht mehr trägt.
    Drei Balken     ``grundrissanteil`` (0 … 1 der Bildbreite), ``flachheit`` (0 … 2,
                    oben gekappt — echte Werte über 2 reichen bis 10) und ``tieflage``
                    (0 = Szenenboden, 1 = Szenendach) — alle drei aus
                    ``gelaendeform.merkmale``, gerechnet auf denselben verdeckten Boxen.
    Balkenfarbe     sandfarben, wenn die FORMREGEL (ohne Namen!) diese Zeile als Gelände
                    einordnet, stahlblau bei Bauwerk, grau bei „nicht entscheidbar".

Man sieht: Zeile 1 hat den grössten ersten Balken (Grundrissanteil ≈ 1,0), den
kürzesten zweiten (Flachheit ≈ 0,003) und einen kurzen dritten (Tieflage ≈ 0,02) — und
ist die einzige sandfarbene Zeile, obwohl links überall Rot steht. Die Form allein hat
getroffen, was der Name nicht mehr sagen durfte.

Was hier NICHT gemessen wird
-----------------------------
Kein Blender, keine GPU, kein Renderbild. ``kameras.rahmungsverhaeltnis`` und
``kamerasatz`` sind Arithmetik auf Hüllboxen — die *Rechnung*, die vor jedem Renderlauf
entscheidet, ob er sich lohnt, nicht die *Messung* am fertigen Bild. Der pixelgezählte
``geometrie_qa.anteil_maske`` braucht einen echten Material-ID-Renderdurchgang (Blender,
GPU) und wird hier nicht erzeugt — dafür ist ein Messauftrag an die HomeStation nötig,
kein Skript hier. Bild 02 zeigt darum die geometrische VORHERSAGE (``wirksame_bildbreite``
und ``fuellgrad_breite``/``fuellgrad_hoehe`` aus ``kamerasatz``), nicht die gerenderte
Maske — der Unterschied steht auch im Docstring von ``rahmungsverhaeltnis`` selbst.

    python tools/beweis/13_kamera_bauwerksbox.py [zielordner]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, gelaendeform, glbbox, kameras, seams  # noqa: E402
from aiimaging.maske import ist_gelaende  # noqa: E402

import make_test_ifc  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "13_kamera_bauwerksbox"

# --------------------------------------------------------------------------------------
# Farben — dieselbe Geländeregel wie in den übrigen Kamerabeweisen (09/10/11).
# --------------------------------------------------------------------------------------
FARBE_LEINWAND = (245, 245, 245)
FARBE_GELAENDE = (222, 206, 170)
FARBE_BAUTEIL = (70, 110, 160)
FARBE_UNKLAR = (150, 150, 150)
FARBE_HUELLBOX_SZENE = (150, 108, 40)
FARBE_HUELLBOX_BAU = (30, 30, 30)
FARBE_RAHMEN = (255, 255, 255)
FARBE_NAMENSREGEL_BLIND = (190, 60, 50)   # rot — findet auf verdecktem Namen nichts
FARBE_MASSSTAB = (60, 60, 60)

GRUNDRISS_PX = 760
GRUNDRISS_RAND_PX = 40
RAHMEN_B, RAHMEN_H = 640, 360
RAHMEN_RAND_PX = 20
RAHMEN_FUGE_PX = 30
BALKEN_B = 780
BALKEN_RAND_PX = 30
BALKEN_ZEILE_H = 58
BALKEN_HOEHE_PX = 15
BALKEN_LUECKE_PX = 3
NAMENSFELD_PX = 26          # Breite des roten/grünen Namensregel-Feldes links je Zeile

#: Anzeige-Deckel für die Flachheit — echte Werte reichen bis ~10 (schmale Wände). Über
#: dem Deckel wird der Balken voll gezeichnet, nicht abgeschnitten unsichtbar.
FLACHHEIT_ANZEIGE_MAX = 2.0

DECKUNGSGRAD = kameras.DECKUNGSGRAD


# --------------------------------------------------------------------------------------
# Rasterizer — Rechtecke und Rahmen, reine stdlib. Kleinstmögliche Teilmenge von
# tools/beweis/10_kamera_rahmung.py, eigenständig geschrieben (Regel 7: keine bestehende
# Datei wird verändert oder importiert).
# --------------------------------------------------------------------------------------
def _neues_bild(breite: int, hoehe: int, hg=FARBE_LEINWAND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((min(breite, max(0, int(round(x0)))), min(breite, max(0, int(round(x1))))))
    ya, yb = sorted((min(hoehe, max(0, int(round(y0)))), min(hoehe, max(0, int(round(y1))))))
    for y in range(ya, yb):
        px[y * breite + xa:y * breite + xb] = [farbe] * (xb - xa)


def _rahmen(px, breite, hoehe, x0, y0, x1, y1, farbe, dicke: int = 1) -> None:
    _rechteck(px, breite, hoehe, x0, y0, x1, y0 + dicke, farbe)
    _rechteck(px, breite, hoehe, x0, y1 - dicke, x1, y1, farbe)
    _rechteck(px, breite, hoehe, x0, y0, x0 + dicke, y1, farbe)
    _rechteck(px, breite, hoehe, x1 - dicke, y0, x1, y1, farbe)


def _nebeneinander(tafeln: list, *, fuge: int = RAHMEN_FUGE_PX):
    """Mehrere gleich hohe Bilder waagrecht aneinanderreihen, mit Fuge dazwischen."""
    hoehe = tafeln[0][2]
    breite = sum(t[1] for t in tafeln) + fuge * (len(tafeln) - 1)
    px = _neues_bild(breite, hoehe)
    x = 0
    for tp, tb, th in tafeln:
        for y in range(th):
            px[y * breite + x:y * breite + x + tb] = tp[y * tb:(y + 1) * tb]
        x += tb + fuge
    return px, breite, hoehe


# --------------------------------------------------------------------------------------
# Schritt 1 — echte Geometrie: make_test_ifc --gelaende → glb über aiimaging.seams
# (ifcopenshell im .venv-ifc, KEIN Blender).
# --------------------------------------------------------------------------------------
def erzeuge_glb(arbeit: Path) -> Path:
    ifc = arbeit / "testbau_gelaende.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True)
    glb = arbeit / "testbau_gelaende.glb"
    report = seams.ifc_zu_glb(ifc, glb)
    if report.get("status") != "ok":
        raise SystemExit(f"IFC→glb (seams.ifc_zu_glb, .venv-ifc) fehlgeschlagen: {report}")
    return glb


def lese_geometrie(glb: Path) -> dict:
    """Knotenboxen (glTF-Koordinaten) und die beiden Hüllboxen (Welt) — Weg (b), ohne
    Blender: :func:`glbbox.bauwerksbox` liest nur den JSON-Kopf der glb."""
    js = glbbox.lies_gltf_json(glb)
    alle = glbbox.knotenboxen(js)["knoten"]
    if not alle:
        raise SystemExit("Keine Mesh-Knoten in der glb — Testgeometrie kaputt.")

    bau = glbbox.bauwerksbox(glb)
    if bau["bbox_bauwerk"] is None:
        raise SystemExit(f"Keine Bauwerksbox: {bau['note']}")
    # Diese Testszene muss auf dem NAMENSWEG entschieden werden ('Gelaende' ist ein Wort
    # aus maske.GELAENDE_WOERTER) — sonst zeigt das Skript eine andere Lage, als es
    # behauptet, und der Formregel-Beweis in Schritt 3 verlöre seinen Kontrast.
    if bau["entschieden_durch"] != "name" or bau["n_gelaende"] != 1:
        raise SystemExit(
            f"Erwartet: genau 1 Knoten von der Namensregel als Gelände erkannt; "
            f"gemessen: entschieden_durch={bau['entschieden_durch']!r}, "
            f"n_gelaende={bau['n_gelaende']}. Die Testgeometrie hat sich geändert."
        )

    knoten_welt = [(name, *glbbox.nach_welt(lo, hi)) for name, lo, hi in alle]
    return {"alle_gltf": alle, "knoten_welt": knoten_welt, "bau": bau}


# --------------------------------------------------------------------------------------
# Schritt 2 — die Kamera: einmal Szene, einmal Bauwerk gerahmt (kameras.kamerasatz, echt
# gerechnet), und das Rahmungsverhältnis dazwischen (kameras.rahmungsverhaeltnis, dieselbe
# Funktion, die abholer._rahmung_vor_dem_render vor jedem Renderlauf befragt).
# --------------------------------------------------------------------------------------
def rechne_rahmung(bau: dict) -> dict:
    bbox_szene, bbox_bau = bau["bbox_szene"], bau["bbox_bauwerk"]

    satz_szene = kameras.kamerasatz(bbox_szene, deckungsgrad=DECKUNGSGRAD, kuerzel=("s",))
    kam_szene = satz_szene["kameras"][0]
    satz_bau = kameras.kamerasatz(bbox_bau, deckungsgrad=DECKUNGSGRAD, kuerzel=("s",))
    kam_bau = satz_bau["kameras"][0]

    lage = kameras.rahmungsverhaeltnis(bbox_szene, bbox_bau, deckungsgrad=DECKUNGSGRAD,
                                       gemessener_fuellgrad=kam_szene["fuellgrad_breite"])
    if lage["grundlage"] != "gemessener_fuellgrad":
        raise SystemExit("rahmungsverhaeltnis hat die gemessene Breite nicht übernommen.")

    # Das SENKRECHTE Gegenstück zu 'breitenanteil'/'wirksame_bildbreite' — es gibt dafür
    # keine Funktion in kameras.py (rahmungsverhaeltnis misst nur die waagrechte
    # Ausdehnung, siehe ihr Docstring), darum wird es hier, einmalig und mit derselben
    # Formel, direkt ausgerechnet: dieselbe Idee, eine Achse tiefer.
    dz_szene = bbox_szene[1][2] - bbox_szene[0][2]
    dz_bau = bbox_bau[1][2] - bbox_bau[0][2]
    hoehenanteil = dz_bau / dz_szene if dz_szene > 0 else 0.0
    wirksame_bildhoehe = kam_szene["fuellgrad_hoehe"] * hoehenanteil

    return {"kam_szene": kam_szene, "kam_bau": kam_bau, "lage": lage,
            "hoehenanteil": hoehenanteil, "wirksame_bildhoehe": wirksame_bildhoehe}


# --------------------------------------------------------------------------------------
# Schritt 3 — die Formregel OHNE Namen: Namen durch 'objekt_NN' ersetzen, prüfen dass die
# Namensregel darauf blind ist, prüfen dass die Formregel dasselbe Urteil trifft wie mit
# den echten Namen.
# --------------------------------------------------------------------------------------
def formregel_ohne_namen(alle_gltf: list) -> dict:
    real = gelaendeform.gelaende_knoten(alle_gltf, hoch=1)

    verdeckt_knoten = [(f"objekt_{i:02d}", lo, hi) for i, (_, lo, hi) in enumerate(alle_gltf)]
    namensregel_verdeckt = [ist_gelaende(n) for n, _, _ in verdeckt_knoten]
    if any(namensregel_verdeckt):
        raise SystemExit(
            "Die verdeckten Namen ('objekt_NN') matchen zufällig die Namensregel — kein "
            "sauberer Beweis, dass die Formregel ohne Namen auskommt."
        )

    verdeckt = gelaendeform.gelaende_knoten(verdeckt_knoten, hoch=1)
    urteile_real = [u["urteil"] for u in real["urteile"]]
    urteile_verdeckt = [u["urteil"] for u in verdeckt["urteile"]]
    if urteile_real != urteile_verdeckt:
        raise SystemExit(
            f"Das Urteil ändert sich, wenn der Name verdeckt wird: {urteile_real} gegen "
            f"{urteile_verdeckt} — dann läse gelaendeform doch irgendwo den Namen."
        )
    # Zweite Probe auf demselben Befund, an der POSITION statt am Namen: Welcher Index
    # als Gelände gilt, muss in beiden Läufen derselbe sein. Ein Vergleich der NAMEN wäre
    # hier sinnlos — die verdeckten Namen sind ja gerade andere.
    idx_real = {i for i, u in enumerate(urteile_real) if u == gelaendeform.GELAENDE}
    idx_verdeckt = {i for i, u in enumerate(urteile_verdeckt) if u == gelaendeform.GELAENDE}
    if idx_real != idx_verdeckt:
        raise SystemExit(f"Gelände-Indizes weichen ab: {idx_real} gegen {idx_verdeckt}.")

    return {"urteile": urteile_verdeckt, "merkmale": [u["merkmale"] for u in real["urteile"]],
            "namensregel_verdeckt": namensregel_verdeckt,
            "n_gelaende": len(verdeckt["gelaende"]), "n_bauwerk": len(verdeckt["bauwerk"]),
            "n_unklar": len(verdeckt["unklar"])}


# --------------------------------------------------------------------------------------
# Bild 1 — Grundriss: Szenenbox gegen Bauwerksbox
# --------------------------------------------------------------------------------------
def zeichne_grundriss(geometrie: dict, *, kante_px: int = GRUNDRISS_PX,
                      rand_px: int = GRUNDRISS_RAND_PX):
    bau = geometrie["bau"]
    bbox_szene, bbox_bau = bau["bbox_szene"], bau["bbox_bauwerk"]
    xs = [bbox_szene[0][0], bbox_szene[1][0]]
    ys = [bbox_szene[0][1], bbox_szene[1][1]]
    spanne = max(max(xs) - min(xs), max(ys) - min(ys))
    m_je_px = spanne / (kante_px - 2 * rand_px)
    mx = (max(xs) + min(xs)) / 2.0
    my = (max(ys) + min(ys)) / 2.0
    breite = hoehe = kante_px

    def nach_px(x, y):
        return (breite / 2.0 + (x - mx) / m_je_px, hoehe / 2.0 - (y - my) / m_je_px)

    px = _neues_bild(breite, hoehe)
    for name, lo, hi in geometrie["knoten_welt"]:
        x0, y0 = nach_px(lo[0], hi[1])
        x1, y1 = nach_px(hi[0], lo[1])
        _rechteck(px, breite, hoehe, x0, y0, x1, y1,
                  FARBE_GELAENDE if ist_gelaende(name) else FARBE_BAUTEIL)

    x0, y0 = nach_px(bbox_szene[0][0], bbox_szene[1][1])
    x1, y1 = nach_px(bbox_szene[1][0], bbox_szene[0][1])
    _rahmen(px, breite, hoehe, x0, y0, x1, y1, FARBE_HUELLBOX_SZENE, 3)

    x0, y0 = nach_px(bbox_bau[0][0], bbox_bau[1][1])
    x1, y1 = nach_px(bbox_bau[1][0], bbox_bau[0][1])
    _rahmen(px, breite, hoehe, x0, y0, x1, y1, FARBE_HUELLBOX_BAU, 3)

    bx0, by0 = rand_px, hoehe - rand_px
    _rechteck(px, breite, hoehe, bx0, by0 - 4, bx0 + 10.0 / m_je_px, by0, FARBE_MASSSTAB)
    return px, breite, hoehe, m_je_px


# --------------------------------------------------------------------------------------
# Bild 2 — zwei Rahmungen derselben Szene: Kamera an der Szenenbox gegen Kamera an der
# Bauwerksbox.
# --------------------------------------------------------------------------------------
def _rahmen_bild(*, breite_feld_frac: float, hoehe_feld_frac: float, farbe_feld,
                 breite_zusatz_frac: float | None = None, hoehe_zusatz_frac: float | None = None,
                 zusatz_unten: bool = False,
                 breite: int = RAHMEN_B, hoehe: int = RAHMEN_H, rand_px: int = RAHMEN_RAND_PX):
    """Ein Bildrahmen mit einer zentrierten Fläche (dem gerahmten Körper) und wahlweise
    einer zweiten, sandfarbenen Fläche (der jeweils anderen Box, zum Vergleich)."""
    gesamt_b, gesamt_h = breite + 2 * rand_px, hoehe + 2 * rand_px
    px = _neues_bild(gesamt_b, gesamt_h)
    _rechteck(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
              FARBE_RAHMEN)

    if breite_zusatz_frac is not None:
        zb = breite_zusatz_frac * breite
        zh = (hoehe_zusatz_frac or 0.0) * hoehe
        zx0 = rand_px + (breite - zb) / 2.0
        zy1 = rand_px + hoehe if zusatz_unten else rand_px + (hoehe + zh) / 2.0
        zy0 = zy1 - zh
        _rechteck(px, gesamt_b, gesamt_h, zx0, zy0, zx0 + zb, zy1, FARBE_GELAENDE)

    fb, fh = breite_feld_frac * breite, hoehe_feld_frac * hoehe
    fx0 = rand_px + (breite - fb) / 2.0
    fy0 = rand_px + (hoehe - fh) / 2.0
    _rechteck(px, gesamt_b, gesamt_h, fx0, fy0, fx0 + fb, fy0 + fh, farbe_feld)

    _rahmen(px, gesamt_b, gesamt_h, rand_px, rand_px, rand_px + breite, rand_px + hoehe,
            (120, 120, 120), 2)
    return px, gesamt_b, gesamt_h


def zeichne_rahmungen(rahmung: dict):
    kam_s, kam_b, lage = rahmung["kam_szene"], rahmung["kam_bau"], rahmung["lage"]

    links, lb, lh = _rahmen_bild(
        breite_feld_frac=kam_s["fuellgrad_breite"], hoehe_feld_frac=kam_s["fuellgrad_hoehe"],
        farbe_feld=FARBE_GELAENDE)
    # Das Bauwerk als zweite Fläche INNERHALB des linken Rahmens: seine Breite ist
    # `wirksame_bildbreite`, seine Höhe die senkrechte Entsprechung — beide bezogen auf
    # den GANZEN Rahmen, nicht auf die sandfarbene Fläche, darum eigene Zeichnung statt
    # Wiederverwendung von `_rahmen_bild`.
    bx = lage["wirksame_bildbreite"] * RAHMEN_B
    bh = rahmung["wirksame_bildhoehe"] * RAHMEN_H
    x0 = RAHMEN_RAND_PX + (RAHMEN_B - bx) / 2.0
    y0 = RAHMEN_RAND_PX + (RAHMEN_H - bh) / 2.0
    _rechteck(links, lb, lh, x0, y0, x0 + bx, y0 + bh, FARBE_BAUTEIL)
    _rahmen(links, lb, lh, RAHMEN_RAND_PX, RAHMEN_RAND_PX,
            RAHMEN_RAND_PX + RAHMEN_B, RAHMEN_RAND_PX + RAHMEN_H, (120, 120, 120), 2)

    # Rechts: Kamera rahmt die BAUWERKSBOX direkt. Die Platte wäre bei diesem Massstab
    # `1/breitenanteil` mal so breit wie das Bauwerk und (in der Höhe) so dünn wie ihr
    # gemessenes Verhältnis zur Bauwerkshöhe — beides aus real gemessenen Boxen, keine
    # Schätzung.
    platte_breite_frac = kam_b["fuellgrad_breite"] / lage["breitenanteil"]
    platte_hoehe_frac = kam_b["fuellgrad_hoehe"] * rahmung["_platte_dz_verhaeltnis"]
    rechts, rb, rh = _rahmen_bild(
        breite_feld_frac=kam_b["fuellgrad_breite"], hoehe_feld_frac=kam_b["fuellgrad_hoehe"],
        farbe_feld=FARBE_BAUTEIL,
        breite_zusatz_frac=platte_breite_frac, hoehe_zusatz_frac=platte_hoehe_frac,
        zusatz_unten=True)

    return _nebeneinander([(links, lb, lh), (rechts, rb, rh)])


# --------------------------------------------------------------------------------------
# Bild 3 — Formregel je Knoten, ohne Namen
# --------------------------------------------------------------------------------------
def zeichne_formregel(alle_gltf: list, formregel: dict, *, breite: int = BALKEN_B,
                      rand_px: int = BALKEN_RAND_PX):
    n = len(alle_gltf)
    hoehe = n * BALKEN_ZEILE_H + 2 * rand_px
    px = _neues_bild(breite, hoehe)

    balken_x0 = rand_px + NAMENSFELD_PX + 12
    balken_b = breite - balken_x0 - rand_px
    farbe_urteil = {gelaendeform.GELAENDE: FARBE_GELAENDE, gelaendeform.BAUWERK: FARBE_BAUTEIL,
                    gelaendeform.NICHT_ENTSCHEIDBAR: FARBE_UNKLAR}

    for i in range(n):
        y0 = rand_px + i * BALKEN_ZEILE_H
        # Links: die Namensregel auf dem VERDECKTEN Namen — in jeder Zeile "findet
        # nichts", denn 'objekt_NN' enthält kein Wort aus GELAENDE_WOERTER (geprüft in
        # formregel_ohne_namen, nicht nur behauptet).
        namensfeld_farbe = (FARBE_NAMENSREGEL_BLIND if not formregel["namensregel_verdeckt"][i]
                            else (60, 150, 90))
        _rechteck(px, breite, hoehe, rand_px, y0 + 6, rand_px + NAMENSFELD_PX, y0 + BALKEN_ZEILE_H - 6,
                  namensfeld_farbe)

        farbe = farbe_urteil[formregel["urteile"][i]]
        m = formregel["merkmale"][i]
        werte = (min(1.0, m["grundrissanteil"]),
                min(1.0, m["flachheit"] / FLACHHEIT_ANZEIGE_MAX),
                min(1.0, m["tieflage"]))
        for j, w in enumerate(werte):
            by0 = y0 + 4 + j * (BALKEN_HOEHE_PX + BALKEN_LUECKE_PX)
            _rechteck(px, breite, hoehe, balken_x0, by0, balken_x0 + balken_b * w,
                      by0 + BALKEN_HOEHE_PX, farbe)
        _rahmen(px, breite, hoehe, balken_x0, y0 + 2, balken_x0 + balken_b, y0 + BALKEN_ZEILE_H - 4,
                (210, 210, 210), 1)

    return px, breite, hoehe


# --------------------------------------------------------------------------------------

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis13_") as tmp:
        glb = erzeuge_glb(Path(tmp))
        geometrie = lese_geometrie(glb)

    bau = geometrie["bau"]
    rahmung = rechne_rahmung(bau)
    # Realer Höhenanteil der Platte (Dicke ÷ Bauwerkshöhe), für den sandfarbenen Streifen
    # in Bild 2 rechts — aus der tatsächlich gemessenen Gelände-Knotenbox, nicht der
    # Konstante GELAENDE_DICKE aus make_test_ifc: Wäre die Konstante falsch abgeschrieben,
    # zeigte das Bild trotzdem den WIRKLICHEN Wert.
    gelaende_dz = next(hi[2] - lo[2] for name, lo, hi in geometrie["knoten_welt"]
                       if ist_gelaende(name))
    bau_dz = bau["bbox_bauwerk"][1][2] - bau["bbox_bauwerk"][0][2]
    rahmung["_platte_dz_verhaeltnis"] = gelaende_dz / bau_dz

    formregel = formregel_ohne_namen(geometrie["alle_gltf"])

    # -- 01 Grundriss --
    px, b, h, m_je_px = zeichne_grundriss(geometrie)
    pfad = ziel / (f"01_grundriss_szenenbox-vs-bauwerksbox_"
                   f"schrumpfung-{bau['schrumpfung']:.4f}_"
                   f"entschieden-durch-{bau['entschieden_durch']}_"
                   f"n-bauwerk-{bau['n_bauwerk']}_n-gelaende-{bau['n_gelaende']}_"
                   f"massstab-{m_je_px:.3f}m-je-px.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 02 Rahmungen --
    px, b, h = zeichne_rahmungen(rahmung)
    lage = rahmung["lage"]
    pfad = ziel / (f"02_rahmung_kamera-szene-vs-kamera-bauwerk_deckungsgrad-{DECKUNGSGRAD:.2f}_"
                   f"fuellgrad-szene-{rahmung['kam_szene']['fuellgrad_breite']:.4f}_"
                   f"bauwerk-wird-fleck-{lage['wirksame_bildbreite']:.4f}_"
                   f"abbruch-{lage['abbruch']}_"
                   f"fuellgrad-bauwerk-direkt-{rahmung['kam_bau']['fuellgrad_breite']:.4f}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    # -- 03 Formregel ohne Namen --
    px, b, h = zeichne_formregel(geometrie["alle_gltf"], formregel)
    pfad = ziel / (f"03_formregel_ohne_namen_n-{len(geometrie['alle_gltf'])}-knoten_"
                   f"gelaende-{formregel['n_gelaende']}_bauwerk-{formregel['n_bauwerk']}_"
                   f"unklar-{formregel['n_unklar']}_"
                   f"namensregel-auf-verdecktem-namen-blind-"
                   f"{not any(formregel['namensregel_verdeckt'])}.png")
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
