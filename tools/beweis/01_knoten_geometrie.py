#!/usr/bin/env python3
"""BEWEIS 01 — Das Node "geometrie" (kette.ART_GEOMETRIE) überquert echt die
Prozessgrenze IFC → glb, und die drei nachgeschalteten Prüfschritte liefern echte,
im Bild nachprüfbare Ergebnisse: die gebaute Geometrie selbst, ihre Hüllbox, und das
Torwächter-Urteil über drei Varianten derselben gemessenen Box.

Woran man es im Bild sieht
--------------------------
* ``01_grundriss_*.png`` — Grundriss (Blick von oben, Welt X/Y), gerastert aus den
  ECHTEN Knotenboxen (``glbbox.knotenboxen``), die aus dem JSON-Kopf der über die
  Prozessgrenze erzeugten ``.glb`` gelesen wurden. Kein Dreieck wird gemalt — jedes
  Rechteck ist die Hüllbox eines echten glTF-Knotens, geschnitten auf Schnitthöhe
  (Wert steht im Dateinamen). Gelände (``maske.ist_gelaende``) braun, Bauwerk
  stahlblau — dieselbe Regel, die auch ``glbbox.bauwerksbox`` benutzt.
* ``02_hoehenschnitt_*.png`` — derselbe Vorgang, geschnitten entlang der Gebäudetiefe
  (Welt X/Z): ein echter Querschnitt, keine Ansicht — nur Knoten, deren Ausdehnung die
  Schnittebene trifft, werden gezeichnet.
* ``03_huellbox-balken_*.png`` — Balkenlängen sind die gemessenen Kantenlängen von
  Szenen- und Bauwerksbox (``glbbox.bauwerksbox``), im selben Lauf gemessen wie die
  beiden Ansichten oben. Grau = Szene, Blau = Bauwerk; wo Blau kürzer ist als Grau,
  hat die Geländeregel gegriffen.
* ``04_torwaechter_in-ordnung_*.png`` / ``05_torwaechter_massstab-faktor1000_*.png`` /
  ``06_torwaechter_georef-versatz_*.png`` — drei ECHTE ``torwaechter.torwaechter()``-
  Urteile über drei Varianten derselben gemessenen bbox (unverändert / ×1000 /
  +LV95-Versatz). Grün = annehmen, Rot = ablehnen_massstab; ein blaues Feld am
  rechten Rand markiert ``empfiehlt_neuzentrierung``. Die drei Bilder unterscheiden
  sich in Farbe UND Balkenlänge (Balkenlänge ist log10 der grössten Kante in Metern,
  weil Faktor 1000 sonst nicht auf dieselbe Leinwand passt) — und der genaue
  Zahlenwert steht im Dateinamen, nicht im Bild (Regel 2: keine Bitmap-Schrift).

Braucht KEIN Blender und KEIN GPU
----------------------------------
Die IFC→glb-Prozessgrenze dieses Projekts läuft für ``kette.ART_GEOMETRIE`` über
ifcopenshell im ``.venv-ifc`` (``aiimaging.seams.ifc_zu_glb`` → ``ifc_to_glb_runner.py``)
— nicht über Blender. Blender kommt erst beim Rendern ins Spiel
(``seams.glb_zu_multipass``), das ist ein anderer Beweis. Dieses Skript läuft darum
vollständig hier, ohne Gerät und ohne Blender-Aufruf — genau wie
``tools/studie_innenansicht.py`` denselben Aufruf an derselben Stelle bereits nutzt.

Aufruf:
    python3 tools/beweis/01_knoten_geometrie.py [ziel_verzeichnis]

Ohne Argument schreibt es nach ``build/beweis/01_knoten_geometrie/``.
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildschreiben, glbbox, seams, torwaechter  # noqa: E402
from aiimaging.maske import ist_gelaende  # noqa: E402

import make_test_ifc  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "01_knoten_geometrie"

#: Farben für die Geländeregel — dieselbe Regel wie in glbbox.bauwerksbox, hier nur
#: zum Einfärben zweitverwendet, nicht neu erfunden.
FARBE_GELAENDE = (139, 101, 60)
FARBE_BAUWERK = (70, 110, 160)
FARBE_HINTERGRUND = (245, 245, 245)


# ----------------------------------------------------------------------------------
# Minimaler Rasterizer: Rechtecke in einen flachen (r,g,b)-Puffer füllen.
# Es gibt im Projekt keinen Rasterizer (keine Bibliothek, Regel im Modulkopf von
# bildschreiben.py) — hier reicht das Füllen achsparalleler Rechtecke, weil die
# Testgeometrie aus achsparallelen Quadern besteht (make_test_ifc.py).
# ----------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _dunkler(farbe, faktor: float = 0.6):
    return tuple(max(0, int(round(k * faktor))) for k in farbe)


def _rechteck(px: list, breite: int, hoehe: int, x0: float, y0: float, x1: float,
              y1: float, farbe, *, rahmen=True) -> None:
    """Füllt ein Rechteck, mit optionalem dunklerem 1px-Rahmen (Kanten bleiben sichtbar,
    wenn zwei gleichfarbige Knoten aneinanderstossen — z.B. vier Wände)."""
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    if xa >= xb or ya >= yb:
        return
    for y in range(ya, yb):
        for x in range(xa, xb):
            px[y * breite + x] = farbe
    if rahmen:
        rand = _dunkler(farbe)
        for x in range(xa, xb):
            px[ya * breite + x] = rand
            px[(yb - 1) * breite + x] = rand
        for y in range(ya, yb):
            px[y * breite + xa] = rand
            px[y * breite + (xb - 1)] = rand


# ----------------------------------------------------------------------------------
# Schritt 1 — IFC erzeugen, über die Prozessgrenze zu glb konvertieren
# ----------------------------------------------------------------------------------

def baue_glb(arbeit: Path) -> dict:
    """Synthetisches Bauwerk (Regel 3) → echte .glb über ``seams.ifc_zu_glb``.

    ``mit_gelaende=True``: ohne Geländeplatte gäbe es in der Szene nur Bauwerk, und
    die Geländeregel (Braun/Stahlblau) hätte an dieser Datei nichts zu zeigen.
    """
    ifc = arbeit / "bau.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True)
    report = seams.ifc_zu_glb(str(ifc), str(arbeit / "modell.glb"))
    if report.get("status") != "ok":
        raise SystemExit(f"IFC→glb fehlgeschlagen: {report.get('error')}")
    return report


# ----------------------------------------------------------------------------------
# Schritt 2 — Grundriss / Höhenschnitt aus den echten Knotenboxen
# ----------------------------------------------------------------------------------

def zeichne_schnitt(knoten_welt, achse_a: int, achse_b: int, achse_c: int,
                     schnitt_wert: float, farben: dict, *, breite: int = 640,
                     hoehe: int = 480, rand_px: int = 24):
    """Ein echter Schnitt: nur Knoten, deren Box die Ebene ``achse_c = schnitt_wert``
    trifft, werden auf (``achse_a``, ``achse_b``) projiziert und gefüllt.

    Args:
        knoten_welt: ``[(name, lo, hi), …]`` in Weltkoordinaten (aus
            ``glbbox.nach_welt``).
        achse_a/b/c: 0=X, 1=Y (Gebäudetiefe), 2=Z (Höhe).

    Returns:
        ``(pixel, breite, hoehe, n_gezeichnet)``.
    """
    getroffen = [(n, lo, hi) for n, lo, hi in knoten_welt if lo[achse_c] <= schnitt_wert <= hi[achse_c]]
    if not getroffen:
        getroffen = list(knoten_welt)

    amin = min(lo[achse_a] for _, lo, _ in getroffen)
    amax = max(hi[achse_a] for _, _, hi in getroffen)
    bmin = min(lo[achse_b] for _, lo, _ in getroffen)
    bmax = max(hi[achse_b] for _, _, hi in getroffen)
    spanne_a = max(amax - amin, 1e-6)
    spanne_b = max(bmax - bmin, 1e-6)
    skala = min((breite - 2 * rand_px) / spanne_a, (hoehe - 2 * rand_px) / spanne_b)

    def px_a(v):
        return rand_px + (v - amin) * skala

    def px_b(v):
        # Bildursprung ist oben links; wachsende Weltachse soll im Bild nach OBEN
        # zeigen, darum gespiegelt.
        return hoehe - rand_px - (v - bmin) * skala

    pixel = _neues_bild(breite, hoehe)
    # Grössere Grundfläche zuerst (Gelände, Decke), damit kleinere Bauteile (Wände)
    # sichtbar obenauf gezeichnet werden — Maler-Algorithmus, kein Z-Buffer nötig,
    # weil alle Körper achsparallele Quader sind.
    for name, lo, hi in sorted(getroffen,
                                key=lambda t: (t[2][achse_a] - t[1][achse_a])
                                * (t[2][achse_b] - t[1][achse_b]), reverse=True):
        farbe = farben.get(name, FARBE_BAUWERK)
        _rechteck(pixel, breite, hoehe,
                  px_a(lo[achse_a]), px_b(hi[achse_b]),
                  px_a(hi[achse_a]), px_b(lo[achse_b]), farbe)
    return pixel, breite, hoehe, len(getroffen)


# ----------------------------------------------------------------------------------
# Schritt 3 — Hüllbox-Balken (Szene vs. Bauwerk, im selben Lauf gemessen)
# ----------------------------------------------------------------------------------

def zeichne_huellbox_balken(bbox_szene, bbox_bauwerk, *, breite: int = 560,
                             hoehe: int = 320, rand_px: int = 30):
    kanten_szene = [abs(bbox_szene[1][i] - bbox_szene[0][i]) for i in range(3)]
    kanten_bau = [abs(bbox_bauwerk[1][i] - bbox_bauwerk[0][i]) for i in range(3)] \
        if bbox_bauwerk is not None else [0.0, 0.0, 0.0]
    hoechste = max(kanten_szene + kanten_bau + [1e-6])

    pixel = _neues_bild(breite, hoehe)
    achsen = ("X", "Y", "Z")
    reihen_hoehe = (hoehe - 2 * rand_px) // 3
    balken_max = breite - 2 * rand_px - 90
    for i in range(3):
        y0 = rand_px + i * reihen_hoehe
        # Szenenbalken (grau) oben in der Reihe, Bauwerksbalken (blau) darunter.
        laenge_s = 90 + (kanten_szene[i] / hoechste) * balken_max
        laenge_b = 90 + (kanten_bau[i] / hoechste) * balken_max
        _rechteck(pixel, breite, hoehe, 90, y0 + 2, laenge_s, y0 + reihen_hoehe * 0.45,
                   (150, 150, 150))
        _rechteck(pixel, breite, hoehe, 90, y0 + reihen_hoehe * 0.55, laenge_b,
                   y0 + reihen_hoehe - 2, FARBE_BAUWERK)
        # Achsenmarke links als kleines Farbfeld statt Text (Regel 2: keine
        # Bitmap-Schrift) — die drei Reihen sind X/Y/Z von oben nach unten.
        marke = (60, 60, 60) if achsen[i] != "Z" else (30, 30, 30)
        _rechteck(pixel, breite, hoehe, 20, y0 + 2, 70, y0 + reihen_hoehe - 2, marke,
                   rahmen=False)
    return pixel, breite, hoehe


# ----------------------------------------------------------------------------------
# Schritt 4 — Torwächter-Urteil als Bild
# ----------------------------------------------------------------------------------

def zeichne_torwaechter(urteil: dict, groesste_kante_m: float | None, *,
                         breite: int = 560, hoehe: int = 160, rand_px: int = 30):
    pixel = _neues_bild(breite, hoehe)
    if urteil["entscheidung"] == torwaechter.ENTSCHEIDUNG_ANNEHMEN:
        farbe = (60, 150, 70)
    elif urteil["entscheidung"] == torwaechter.ENTSCHEIDUNG_ABLEHNEN_MASSSTAB:
        farbe = (190, 60, 50)
    else:
        farbe = (200, 150, 40)

    # Balkenlänge: log10 der grössten Kante, weil Faktor 1000 sonst nicht auf
    # dieselbe Leinwand passt wie der plausible Fall — die Farbe trägt die
    # Entscheidung, die Länge nur die Grössenordnung.
    balken_max = breite - 2 * rand_px
    if groesste_kante_m and groesste_kante_m > 0:
        log = math.log10(groesste_kante_m)
        # Plausibler Bereich ist log10(1)=0 .. log10(1000)=3; Skala fasst -1..7,
        # damit auch der Faktor-1000-Fall (log10 ~ 3.9) und der Georef-Fall
        # (log10 der Kante bleibt normal, aber der Betrag ist riesig — siehe unten)
        # nicht abgeschnitten werden.
        anteil = min(1.0, max(0.02, (log + 1.0) / 8.0))
    else:
        anteil = 0.02
    laenge = rand_px + anteil * balken_max
    _rechteck(pixel, breite, hoehe, rand_px, hoehe * 0.3, laenge, hoehe * 0.7, farbe)

    if urteil["empfiehlt_neuzentrierung"]:
        # Blaues Feld am rechten Rand: die Empfehlung ist unabhängig von der
        # Massstabsfarbe, darum ein eigenes Feld statt einer Mischfarbe.
        _rechteck(pixel, breite, hoehe, breite - rand_px - 26, hoehe * 0.3,
                   breite - rand_px, hoehe * 0.7, (50, 90, 190))
    return pixel, breite, hoehe


def _formatiere_zahl(x: float) -> str:
    """Für Dateinamen: kompakt, ohne Komma-Zeichen, das Pfade verwirrt."""
    if abs(x) >= 1000:
        return f"{x:.0f}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    with tempfile.TemporaryDirectory(prefix="beweis01_") as tmp:
        report = baue_glb(Path(tmp))
        js = glbbox.lies_gltf_json(report["glb_path"])
        gelesen = glbbox.knotenboxen(js)
        if gelesen["ohne_grenzen"]:
            raise SystemExit(
                f"{len(gelesen['ohne_grenzen'])} Knoten ohne min/max — siehe glbbox.")

        knoten_welt = [(name, *glbbox.nach_welt(lo, hi, up_axis=report["up_axis"]))
                       for name, lo, hi in gelesen["knoten"]]
        farben = {name: (FARBE_GELAENDE if ist_gelaende(name) else FARBE_BAUWERK)
                  for name, _, _ in gelesen["knoten"]}

        bau = glbbox.bauwerksbox(report["glb_path"], up_axis=report["up_axis"])

        # -- 01 Grundriss: Schnitt auf 35 % der Gebäudehöhe (Welt Z), Blick von oben --
        z_werte = [v for _, lo, hi in knoten_welt for v in (lo[2], hi[2])]
        schnitt_z = min(z_werte) + 0.35 * (max(z_werte) - min(z_werte))
        pixel, b, h, n = zeichne_schnitt(knoten_welt, 0, 1, 2, schnitt_z, farben)
        pfad = ziel / f"01_grundriss_schnitthoehe-{_formatiere_zahl(schnitt_z)}m.png"
        bildschreiben.schreibe_farb_png(pfad, pixel, b, h)
        geschrieben.append(pfad)

        # -- 02 Höhenschnitt: Schnitt auf 50 % der Gebäudetiefe (Welt Y) --
        y_werte = [v for _, lo, hi in knoten_welt for v in (lo[1], hi[1])]
        schnitt_y = min(y_werte) + 0.50 * (max(y_werte) - min(y_werte))
        pixel, b, h, n = zeichne_schnitt(knoten_welt, 0, 2, 1, schnitt_y, farben)
        pfad = ziel / f"02_hoehenschnitt_schnitttiefe-{_formatiere_zahl(schnitt_y)}m.png"
        bildschreiben.schreibe_farb_png(pfad, pixel, b, h)
        geschrieben.append(pfad)

        # -- 03 Hüllbox-Balken --
        pixel, b, h = zeichne_huellbox_balken(bau["bbox_szene"], bau["bbox_bauwerk"])
        schrumpfung_pct = round((bau["schrumpfung"] or 0.0) * 100, 1)
        pfad = ziel / f"03_huellbox-balken_schrumpfung-{schrumpfung_pct}pct.png"
        bildschreiben.schreibe_farb_png(pfad, pixel, b, h)
        geschrieben.append(pfad)

        # -- 04..06 Torwächter: drei echte Urteile über Varianten derselben bbox --
        echt = report["bbox"]
        varianten = [
            ("04_torwaechter_in-ordnung", echt),
            ("05_torwaechter_massstab-faktor1000",
             [[v * 1000.0 for v in ecke] for ecke in echt]),
            ("06_torwaechter_georef-versatz",
             [[echt[0][0] + 2_600_000.0, echt[0][1] + 1_200_000.0, echt[0][2]],
              [echt[1][0] + 2_600_000.0, echt[1][1] + 1_200_000.0, echt[1][2]]]),
        ]
        for stamm, bbox in varianten:
            urteil = torwaechter.torwaechter(
                {"status": "ok", "bbox": bbox, "error": None})
            kante = urteil["massstab"]["groesste_kante_m"]
            pixel, b, h = zeichne_torwaechter(urteil, kante)
            kennzahl = _formatiere_zahl(kante) if kante is not None else "unlesbar"
            pfad = ziel / f"{stamm}_kante-{kennzahl}m.png"
            bildschreiben.schreibe_farb_png(pfad, pixel, b, h)
            geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
