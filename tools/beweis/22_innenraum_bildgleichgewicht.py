#!/usr/bin/env python3
"""BEWEIS 22 — Die Innenraum-Bildbewertung (`komposition.bildanteile`) **gegen den
gerenderten Bildinhalt**: Drei Kamerahöhen im selben Raum, jede gerendert, und der
Bodenanteil aus dem Material-ID-Pass **gezählt** statt geglaubt.

Die Behauptung, die hier fallen kann
------------------------------------
`komposition.bildanteile` rechnet Boden-, Decken- und Wandanteil aus Kamerahöhe,
Abstand, Brennweite und Sensorhöhe. Dazu sagt der Modulkopf zwei Dinge, die man an
einem Bild nachprüfen kann und nicht nur behaupten muss:

1. Der **Bodenanteil** ist ``f · h / (D · s) − v/s``. Er wächst mit der Kamerahöhe.
2. Der **Wandanteil hängt nicht von der Kamerahöhe ab** — die Höhe verteilt nur
   zwischen Boden und Decke um.

Und `hoehe_fuer_bild_gleichgewicht` nennt die Höhe, bei der Boden und Decke gleich viel
bekommen: ohne Shift schlicht ``Raumhöhe / 2``.

Dieser Beweis rendert denselben Raum aus **derselben** Blickrichtung bei drei Höhen und
zählt im Material-ID-Pass, wieviel Bildfläche der Bodenkörper wirklich einnimmt. Neben
jeder gezählten Zahl steht die gerechnete. **Weichen sie ab, ist das der Befund** — dieser
Beweis ist so gebaut, dass er die Behauptung widerlegen kann.

Was er NICHT kann, und es steht mit im Bild
-------------------------------------------
Unsere Testgeometrie hat **keine Decke** (`tools/make_test_ifc.py --raeume` legt zwei
``IfcSpace`` ins Wandinnere; ein Deckenkörper ist nicht dabei). Im Material-ID-Pass ist
darum oben ein **schwarzes Band** — Hintergrund, wo eine Decke wäre. Der
``deckenanteil`` ist damit **nicht messbar**, und er wird hier auch nicht gemessen:
Die gerechnete Zahl steht da, die gezählte fehlt, und das schwarze Band ist der Grund.
*Nicht messbar ist weder bestanden noch durchgefallen.*

Woran man es im Bild sieht
--------------------------
* ``NN_hoehe-*_beauty.png`` / ``NN_hoehe-*_material-id.png`` — je Höhe der echte
  Cycles-Lauf und der Pass, in dem gezählt wird. Von unten nach oben: Boden (eine
  Farbe), Wand (eine andere), schwarzes Band = fehlende Decke.
* ``NN_hoehe-*_bodenanteil_gerechnet-*_gezaehlt-*.png`` — zwei Balken übereinander,
  gerechnet und gezählt, in denselben Bildmassen. Gleich lang heisst: die Rechnung
  stimmt an diesem Bild.
* ``90_gleichgewicht_*.png`` — die drei Höhen nebeneinander gegen die von
  `hoehe_fuer_bild_gleichgewicht` genannte Höhe.

Aufruf:
    python3 tools/beweis/22_innenraum_bildgleichgewicht.py [ziel_verzeichnis]
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildlesen, bildschreiben, komposition, raumkamera, seams  # noqa: E402

import make_test_ifc  # noqa: E402

BREITE = 800
HOEHE = 496
SAMPLES = 8
BRENNWEITE_MM = 24.0
#: Der Runner rahmt HORIZONTAL auf 36 mm Sensorbreite (steht so im Blender-Bericht).
#: Die Sensorhöhe folgt daraus über das Seitenverhältnis — sie ist NICHT die Vorgabe
#: `komposition.SENSOR_HOEHE_QUER_MM` (24,0 für 3:2). Bei 800×496 sind es 22,32 mm, und
#: mit 24 gerechnet läge der Bodenanteil um 7 % daneben, ohne dass es auffiele.
SENSOR_BREITE_MM = 36.0

GRUND = (243, 243, 241)
GERECHNET = (70, 110, 190)
GEZAEHLT = (225, 140, 45)
FEHLT = (90, 90, 95)


def _leinwand(breite, hoehe, farbe=GRUND):
    return [list(farbe) for _ in range(breite * hoehe)]


def _rechteck(bild, breite, hoehe, x0, y0, x1, y1, farbe):
    for y in range(max(0, y0), min(hoehe, y1)):
        for x in range(max(0, x0), min(breite, x1)):
            bild[y * breite + x] = list(farbe)


def _balkenpaar(ziel: Path, name: str, gerechnet: float, gezaehlt: float | None) -> Path:
    """Zwei Balken in denselben Bildmassen — gleich lang heisst: die Rechnung stimmt."""
    breite, hoehe = 640, 170
    bild = _leinwand(breite, hoehe)
    nutz = breite - 60
    _rechteck(bild, breite, hoehe, 30, 25, 30 + max(2, round(nutz * gerechnet)), 70,
              GERECHNET)
    if gezaehlt is None:
        _rechteck(bild, breite, hoehe, 30, 100, 30 + nutz, 145, FEHLT)
    else:
        _rechteck(bild, breite, hoehe, 30, 100, 30 + max(2, round(nutz * gezaehlt)), 145,
                  GEZAEHLT)
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, bild, breite, hoehe)
    return pfad


def _anteile_aus_material_id(pfad: Path, bodenfarbe=None) -> dict:
    """Die Farbanteile des Material-ID-Passes — gezählt, nicht geschätzt.

    Schwarz ist Hintergrund. Der Boden wird an seiner **Kennfarbe** erkannt, und die
    Farbe wird **einmal** bestimmt: an der untersten Bildzeile der tiefsten Kamerahöhe,
    wo Boden garantiert im Bild ist. Danach zählt jede Höhe dieselbe Farbe.

    **Der erste Anlauf fragte je Höhe neu, welche Farbe unten steht** — und lieferte für
    die höchste Kamera 0,756 statt 0,000. Dort ist gar kein Boden mehr im Bild (die
    Boden-Wand-Kante ist unter den Bildrand gewandert, `boden_kante_im_bild` sagt das
    voraus), und die Frage «welche Farbe steht unten» beantwortete brav die Wand. *Ein
    Messverfahren, das seine eigene Bezugsgrösse aus dem Messobjekt zieht, misst bei
    Abwesenheit des Gesuchten etwas anderes und meldet es als Fund.*
    """
    farben, breite, hoehe = bildlesen.lies_png_farben(pfad)
    n = breite * hoehe
    if bodenfarbe is None:
        bodenfarbe = farben[(hoehe - 1) * breite + breite // 2]
        if bodenfarbe == (0, 0, 0):
            return {"bodenanteil": None, "bodenfarbe": None,
                    "grund": "unten steht Hintergrund — keine Bodenfarbe zu holen"}
    boden = sum(1 for f in farben if f == bodenfarbe)
    schwarz = sum(1 for f in farben if f == (0, 0, 0))
    return {"bodenanteil": boden / n, "hintergrundanteil": schwarz / n,
            "bodenfarbe": bodenfarbe, "grund": ""}


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis22-"))

    ifc = arbeit / "raeume.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_raeumen=True)
    umbau = seams.ifc_zu_glb(ifc, arbeit / "szene.glb")
    if umbau.get("status") != "ok":
        print(f"IFC→glb: {umbau.get('error')}")
        return 1

    raeume = seams.ifc_raeume(ifc)
    raum = (raeume.get("raeume") or [None])[0]
    if raum is None:
        print("kein Raum")
        return 1
    raumhoehe = float(raum["hoehe_m"])
    frontal = raumkamera.frontaler_standpunkt(raum, brennweite_mm=BRENNWEITE_MM,
                                              seitenverhaeltnis=BREITE / HOEHE)
    if frontal.get("auge") is None:
        print(f"kein frontaler Standpunkt: {frontal.get('befund')}")
        return 1

    sensor_hoehe = SENSOR_BREITE_MM * HOEHE / BREITE
    gleichgewicht = komposition.hoehe_fuer_bild_gleichgewicht(raumhoehe)
    print(f"Raumhöhe {raumhoehe:.2f} m, Gleichgewicht bei {gleichgewicht:.3f} m, "
          f"Sensorhöhe {sensor_hoehe:.2f} mm")

    auge, blick = list(frontal["auge"]), list(frontal["blick_auf"])
    z_unten = float(raum.get("z_unten_m") or 0.0)
    hoehen = [round(z_unten + a * raumhoehe, 3) for a in (0.25, 0.5, 0.75)]

    zeilen = []
    # DIE BODENFARBE WIRD EINMAL BESTIMMT, an der tiefsten Höhe — siehe
    # `_anteile_aus_material_id`. `hoehen` ist aufsteigend sortiert, und das ist hier
    # keine Kosmetik, sondern die Voraussetzung des Verfahrens.
    bodenfarbe = None
    for nr, h in enumerate(hoehen, 1):
        out = arbeit / f"h{nr}"
        out.mkdir(parents=True, exist_ok=True)
        bericht = seams.glb_zu_multipass(
            arbeit / "szene.glb", out, up_axis="y", aufloesung=BREITE, hoehe=HOEHE,
            samples=SAMPLES, auge=[auge[0], auge[1], h], blick_auf=[blick[0], blick[1], h],
            brennweite=BRENNWEITE_MM, material_id=True)
        if bericht.get("status") != "ok":
            print(f"  Blender bei {h} m: {bericht.get('error')}")
            continue
        abstand = float((bericht.get("kamera") or {}).get("abstand_m") or 0.0)
        # ÜBER DEM BODEN, nicht über dem Projektnullpunkt: `bodenanteil` rechnet mit dem
        # Abstand der Kamera zur Bodenfläche, und die liegt bei `z_unten_m`.
        anteile = komposition.bildanteile(
            kamerahoehe_m=h - z_unten, abstand_m=abstand, brennweite_mm=BRENNWEITE_MM,
            sensor_hoehe_mm=sensor_hoehe, raumhoehe_m=raumhoehe)
        gemessen = {"bodenanteil": None}
        mid = Path(bericht.get("material_id_png") or "")
        if mid.is_file():
            gemessen = _anteile_aus_material_id(mid, bodenfarbe)
            bodenfarbe = bodenfarbe or gemessen.get("bodenfarbe")
            neu = ziel / f"{nr}0_hoehe-{h:.2f}m_material-id.png"
            neu.write_bytes(mid.read_bytes())
            print("  ", neu.name)
        beauty = Path(bericht.get("beauty_png") or "")
        if beauty.is_file():
            neu = ziel / f"{nr}1_hoehe-{h:.2f}m_beauty_abstand-{abstand:.2f}m.png"
            neu.write_bytes(beauty.read_bytes())
            print("  ", neu.name)

        g, m = anteile["bodenanteil"], gemessen["bodenanteil"]
        kante = "kante-im-bild" if anteile.get("boden_kante_im_bild") else "kante-draussen"
        name = (f"{nr}2_hoehe-{h:.2f}m_{kante}_bodenanteil_gerechnet-{g:.3f}"
                + (f"_gezaehlt-{m:.3f}" if m is not None else "_gezaehlt-fehlt")
                + (f"_abweichung-{abs(g - m):.3f}" if m is not None else "") + ".png")
        print("  ", _balkenpaar(ziel, name, g, m).name)
        zeilen.append((h, g, m, anteile.get("wandanteil"),
                       bool(anteile.get("boden_kante_im_bild"))
                       and bool(anteile.get("decken_kante_im_bild"))))

    if not zeilen:
        return 1

    # DER WANDANTEIL, DREIMAL — UND DIE BEDINGUNG, UNTER DER DIE BEHAUPTUNG GILT.
    #
    # Das Modul sagt, der Wandanteil hänge nicht von der Kamerahöhe ab. Gemessen stimmt
    # das **solange beide Kanten im Bild sind**: bei 1,35 m 0,708, bei 0,68 m und 2,02 m
    # dagegen 0,677 — dort ist eine der beiden Kanten aus dem Bild gewandert, der
    # zugehörige Anteil wird auf 0 begrenzt, und `1 − Boden − Decke` beschreibt das Bild
    # nicht mehr. Die Balken der Höhen mit beiden Kanten im Bild sind blau, die anderen
    # grau: **Die Behauptung fällt nicht, sie hat eine Bedingung** — und die steht mit
    # `boden_kante_im_bild` / `decken_kante_im_bild` schon im Rückgabewert.
    breite, hoehe = 640, 60 * len(zeilen) + 40
    bild = _leinwand(breite, hoehe)
    for i, (h, g, m, wand, beide) in enumerate(zeilen):
        y0 = 20 + i * 60
        _rechteck(bild, breite, hoehe, 30, y0, 30 + max(2, round((breite - 60) * (wand or 0))),
                  y0 + 40, GERECHNET if beide else FEHLT)
    name = ("90_wandanteil_"
            + "_".join(f"{h:.2f}m-{(w or 0):.3f}-{'beide-kanten' if b else 'kante-draussen'}"
                       for h, _, _, w, b in zeilen) + ".png")
    bildschreiben.schreibe_farb_png(ziel / name, bild, breite, hoehe)
    print("  ", name)

    abw = [abs(g - m) for _, g, m, _, _ in zeilen if m is not None]
    if abw:
        print(f"\nGRÖSSTE ABWEICHUNG gerechnet gegen gezählt: {max(abw):.4f}")
    print(f"{len(sorted(ziel.glob('*.png')))} Bilder in {ziel}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
