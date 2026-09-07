#!/usr/bin/env python3
"""BEWEIS 02 — Das Node «multipass» liefert aus einem Blender-Lauf drei Ausgaben, die zur
selben Kamera gehören: Beauty, Tiefe (EXR in Metern + normalisiertes PNG), Material-ID.

Was bewiesen wird
-----------------
``kette.ART_MULTIPASS`` ist die teuerste Stufe der Standardkette (geometrie → multipass
→ render → qa). Sie ruft ``seams.glb_zu_multipass``; der startet ``blender --background``
hinter der Prozessgrenze (Regel 2) und hinterlässt

    beauty_.png       das gerenderte Bild (Cycles, Sonne, Schatten)
    tiefe_0001.exr    die Tiefe in echten Metern, 32 Bit
    tiefe_norm.png    dieselbe Tiefe, normalisiert, 16 Bit, nah = hell — gerechnet auf
                      der Produktseite (``bildschreiben.tiefe_exr_zu_png``), nicht in Blender
    material_id.png   je Material eine Kennfarbe, ein Sample, harte Kanten, 8 Bit

Woran man es im Bild sieht
--------------------------
``05_multipass_nebeneinander_…png`` — vier Kacheln gleicher Grösse, dieselbe Kamera:

    1  Beauty: Licht und Schatten, Gelände hell, Wände schattiert.
    2  Tiefe normalisiert: vorne hell, hinten dunkel, Hintergrund schwarz. Das
       entfernteste Geometriepixel ist ebenfalls schwarz — die dokumentierte Falle
       (``bildschreiben.KONVENTION``); wer die Silhouette exakt braucht, nimmt die EXR.
    3  Material-ID: flache Farbflächen ohne jede Schattierung, eine je Material,
       Hintergrund schwarz.
    4  Falschfarben **aus der EXR** (``bildlesen.lies_exr_tiefe``), nah = hell:
       weiss → gelb → rot → dunkelblau = fern, Hintergrund schwarz. Darunter die Rampe,
       fern links, nah rechts. Hier ist die Silhouette vollständig — auch das
       entfernteste Geometriepixel ist vom Hintergrund getrennt, anders als in Kachel 2.

Dass Kachel 2, 3 und 4 dieselbe Silhouette tragen, belegt: alle Ausgaben stammen aus
derselben Kamera desselben Laufs. Die Zahlen in den Dateinamen (Auflösung, Samples,
Zahl der Kennfarben, min/max in Metern) sind in diesem Lauf gemessen, nicht gesetzt.

Bild 01 bis 03 sind **Byte für Byte** die Dateien des Blender-Laufs, nur umbenannt.
Bild 04 und 05 sind aus ihnen gerechnet — reine stdlib, kein numpy, kein Pillow.

Was das Gerät braucht
---------------------
Nichts. Blender 4.2 auf der CPU genügt; keine GPU, kein torch, keine Gewichte. Fehlt
Blender, wird der Lauf übersprungen und «NICHT GEMESSEN» gemeldet — kein Bild, aber auch
kein Fehlschlag (Rückgabe 0). Liegt ein vollständiger Lauf schon unter ``lauf/``, wird er
wiederverwendet; ``--neu`` verwirft ihn.

Die Szene ist synthetisch und entsteht hier (Regel 3): eine Geländeplatte und drei
Baukörper mit vier Materialien, über ``tools/make_test_glb.py``.

    python tools/beweis/02_knoten_multipass.py
    python tools/beweis/02_knoten_multipass.py --neu --aufloesung 256 --samples 8
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildlesen, bildschreiben, glbbox, seams        # noqa: E402
from make_test_glb import baue_glb                                   # noqa: E402

ZIEL = WURZEL / "build" / "beweis" / "02_knoten_multipass"

#: Eine Platte und drei Baukörper, in glTF-Koordinaten (Y oben). Bewusst asymmetrisch
#: und mit einem Turm: Eine Tiefenkarte mit einem einzigen Wert trüge keinen Beweis.
#: Die Namen tragen die IFC-Klasse, weil die Geländeregel (``maske.ist_gelaende``) an
#: Namen entscheidet — und ohne erkanntes Gelände rahmte die Kamera die ganze Platte.
SZENE = (
    ("IfcSite_Gelaende_0aBcDeFgHiJkLmNoPqRsTu", (-14.0, -0.5, -12.0), (26.0, 0.0, 18.0)),
    ("IfcWall_Hauptbau_1aBcDeFgHiJkLmNoPqRsT", (0.0, 0.0, 0.0), (12.0, 15.0, 9.0)),
    ("IfcWall_Anbau_2aBcDeFgHiJkLmNoPqRsTuV", (12.0, 0.0, 2.0), (18.0, 5.0, 7.0)),
    ("IfcWall_Turm_3aBcDeFgHiJkLmNoPqRsTuVw", (-4.0, 0.0, 3.0), (0.0, 21.0, 6.0)),
)
#: Ein Material je Körper, reihum vergeben — vier Kennfarben im Material-ID-Pass.
MATERIALIEN = ("Gelaende", "Mauerwerk", "Beton", "Sichtbeton")

KAMERA = "sSE"                      # diagonal: zwei Fassaden, Tiefenspanne über 20 m
AUFLOESUNG = 384
SAMPLES = 16

#: Grösser als die Vorgabe (2 s), aus demselben Grund wie in ``studie_paarmasse``: Auf
#: der CPU verhungert der Herzschlagfaden unter Cycles-Last, und die Wache meldete einen
#: Stillstand, den es nicht gibt.
HERZSCHLAG_S = 12.0

#: Falschfarben-Rampe, fern → nah. Die Helligkeit steigt monoton: dunkelblau, rot, gelb,
#: weiss — «nah = hell» gilt also auch in der Luminanz, nicht nur in der Farbe.
RAMPE = ((20, 30, 120), (200, 40, 40), (255, 220, 60), (255, 255, 255))
HINTERGRUND = (0, 0, 0)

FUGE = 12                           # Abstand der Kacheln in der Tafel
RAND = 12
GRUND = (48, 48, 48)                # neutrales Grau, damit Schwarz im Bild als Bild zählt
LEGENDE_H = 14


def _luma(f) -> float:
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]


# Ein Beweis, dessen Rampe «nah = hell» nur behauptet, wäre keiner: geprüft beim Import.
assert all(_luma(RAMPE[i]) < _luma(RAMPE[i + 1]) for i in range(len(RAMPE) - 1)), \
    "RAMPE muss von fern nach nah heller werden"


def falschfarbe(t: float) -> tuple[int, int, int]:
    """Grauwert 0..1 (1 = nah) → Farbe auf der Rampe, linear zwischen den Stützen."""
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    pos = t * (len(RAMPE) - 1)
    i = min(int(pos), len(RAMPE) - 2)
    f = pos - i
    a, b = RAMPE[i], RAMPE[i + 1]
    return tuple(int(round(a[k] + (b[k] - a[k]) * f)) for k in range(3))


def tiefe_falschfarben(meter, *, hintergrund_ab_m=bildschreiben.HINTERGRUND_AB_M):
    """Meter → Falschfarben. Die Silhouette kommt aus den **Metern**, nicht aus dem Grau.

    ``normalisiere_tiefe`` setzt das entfernteste Geometriepixel und den Hintergrund
    beide auf 0 — im PNG ununterscheidbar. Hier entscheidet der Meterwert, und darum
    bleibt das entfernteste Pixel dunkelblau statt schwarz.
    """
    grau, norm = bildschreiben.normalisiere_tiefe(meter, hintergrund_ab_m=hintergrund_ab_m)
    farben = [HINTERGRUND] * len(meter)
    for i, (m, g) in enumerate(zip(meter, grau)):
        if m == m and 0.0 < m < hintergrund_ab_m:
            farben[i] = falschfarbe(g)
    return farben, norm


def tafel(kacheln, breite, hoehe, *, legende_unter=None):
    """Kacheln gleicher Grösse nebeneinander auf grauem Grund; wahlweise eine Rampe unter
    einer davon. Kein Text — was die Kacheln sind, sagt der Dateiname."""
    n = len(kacheln)
    b = 2 * RAND + n * breite + (n - 1) * FUGE
    h = 2 * RAND + hoehe + (FUGE + LEGENDE_H if legende_unter is not None else 0)
    aus = [GRUND] * (b * h)
    for k, kachel in enumerate(kacheln):
        x0 = RAND + k * (breite + FUGE)
        for y in range(hoehe):
            zeile = (RAND + y) * b + x0
            aus[zeile:zeile + breite] = kachel[y * breite:(y + 1) * breite]
    if legende_unter is not None:
        x0 = RAND + legende_unter * (breite + FUGE)
        y0 = RAND + hoehe + FUGE
        for y in range(LEGENDE_H):
            zeile = (y0 + y) * b + x0
            aus[zeile:zeile + breite] = [falschfarbe(x / (breite - 1)) for x in range(breite)]
    return aus, b, h


def _vollstaendig(bericht: dict) -> bool:
    """Ein Bericht zählt nur, wenn jede genannte Datei daliegt und nicht leer ist —
    die Existenz eines Reports ist kein Beleg für seinen Inhalt (seams, Sitzung 03/05)."""
    if bericht.get("status") != "ok":
        return False
    for feld in ("beauty_png", "depth_png", "material_id_png", "depth_exr"):
        pfad = bericht.get(feld)
        if not pfad or not Path(pfad).is_file() or Path(pfad).stat().st_size == 0:
            return False
    return True


def lauf(glb: Path, aus: Path, huellbox, *, neu: bool, aufloesung: int, samples: int):
    """Der Blender-Lauf — oder sein wiederverwendetes Ergebnis, oder ``None`` ohne Blender."""
    datei = aus / "blender-report.json"
    if not neu and datei.exists():
        alt = json.loads(datei.read_text(encoding="utf-8"))
        if _vollstaendig(alt) and alt.get("aufloesung") == aufloesung \
                and alt.get("samples") == samples:
            print(f"VORHANDENER LAUF wiederverwendet: {datei} (--neu verwirft ihn)")
            return alt
    try:
        seams.finde_blender()
    except seams.SeamError as e:
        print(f"NICHT GEMESSEN — {e}")
        print("Der Beweis braucht einen Blender-Lauf; ohne Blender gibt es kein Bild "
              "und keinen Fehlschlag.")
        return None
    beginn = time.monotonic()
    bericht = seams.glb_zu_multipass(
        glb, aus, up_axis="Y", aufloesung=aufloesung, samples=samples,
        kamera=KAMERA, kamera_huellbox=huellbox, herzschlag_takt_s=HERZSCHLAG_S)
    bericht["_dauer_s"] = round(time.monotonic() - beginn, 1)
    print(f"Blender {bericht.get('blender')}: {bericht['_dauer_s']} s, "
          f"{bericht.get('n_meshes')} Meshes, Kamera {bericht.get('kamera')}")
    return bericht


def bilder_aus_bericht(bericht: dict, ziel: Path) -> list[Path]:
    """Alles nach Blender: lesen, umbenennen, rechnen, nebeneinanderstellen."""
    if not bericht.get("depth_png"):
        raise SystemExit(f"Der Lauf hat kein normalisiertes PNG: "
                         f"{bericht.get('depth_png_fehler')}")

    beauty, b1, h1 = bildlesen.lies_png_farben(bericht["beauty_png"])
    grau, b2, h2 = bildlesen.lies_png_graustufen(bericht["depth_png"])
    matid, b3, h3 = bildlesen.lies_png_farben(bericht["material_id_png"])
    meter, b4, h4 = bildlesen.lies_exr_tiefe(bericht["depth_exr"])
    masse = {(b1, h1), (b2, h2), (b3, h3), (b4, h4)}
    if len(masse) != 1:
        raise SystemExit(f"Die vier Ausgaben haben nicht dieselbe Grösse: {sorted(masse)}")
    breite, hoehe = b1, h1

    farben, norm = tiefe_falschfarben(meter)
    kennfarben = sorted(set(matid) - {HINTERGRUND})
    quelle = "+".join(bericht.get("material_id_quelle") or ["unbekannt"])
    aufl = bericht.get("aufloesung", breite)
    samples = bericht.get("samples", "?")

    geschrieben: list[Path] = []

    def kopie(quelle_pfad, name: str) -> None:
        # Byte für Byte, nicht neu kodiert: Bild 01–03 SIND die Ausgaben des Laufs.
        z = ziel / name
        shutil.copyfile(quelle_pfad, z)
        geschrieben.append(z)

    kopie(bericht["beauty_png"],
          f"01_beauty_cycles_{aufl}px_{samples}samples_kamera-{KAMERA}.png")
    kopie(bericht["depth_png"],
          "02_tiefe-normalisiert_16bit_nah-hell_hintergrund-schwarz.png")
    kopie(bericht["material_id_png"],
          f"03_material-id_{len(kennfarben)}-kennfarben_quelle-{quelle}.png")

    z4 = ziel / (f"04_tiefe-falschfarben_aus-exr_nah-hell_"
                 f"min-{norm['min_m']:.1f}m_max-{norm['max_m']:.1f}m.png")
    bildschreiben.schreibe_farb_png(z4, farben, breite, hoehe)
    geschrieben.append(z4)

    # Für die Tafel: 16-Bit-Grau auf 8 Bit, Beauty ohne Alpha. Beides nur zur Ansicht;
    # die Originale liegen unverändert als 01–03 daneben.
    grau8 = [(int(round(g * 255)),) * 3 for g in grau]
    kacheln, tb, th = tafel([beauty, grau8, matid, farben], breite, hoehe, legende_unter=3)
    z5 = ziel / "05_multipass_nebeneinander_beauty_tiefe_material-id_falschfarben.png"
    bildschreiben.schreibe_farb_png(z5, kacheln, tb, th)
    geschrieben.append(z5)

    print(f"Tiefe aus EXR: {norm['n_geometriepixel']} Geometriepixel von {breite * hoehe}, "
          f"{norm['min_m']:.2f} m bis {norm['max_m']:.2f} m")
    print(f"Material-ID: {len(kennfarben)} Kennfarben im Bild, "
          f"{len(bericht.get('material_id_tabelle') or [])} Einträge in der Tabelle "
          f"(Quelle: {quelle})")
    return geschrieben


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--neu", action="store_true", help="vorhandenen Blender-Lauf verwerfen")
    p.add_argument("--aufloesung", type=int, default=AUFLOESUNG)
    p.add_argument("--samples", type=int, default=SAMPLES)
    a = p.parse_args(argv)

    ZIEL.mkdir(parents=True, exist_ok=True)
    glb = ZIEL / "szene.glb"
    glb.write_bytes(baue_glb(SZENE, materialien=MATERIALIEN))

    # Die Kamera rahmt das Bauwerk, nicht die Platte — die Bauwerksbox kommt aus der glb,
    # ohne Blender-Vorlauf (glbbox, Weg b). Dieselbe Regel wie im Runner.
    box = glbbox.bauwerksbox(glb, up_axis="Y")
    huellbox = box["bbox_bauwerk"]
    print(f"Bauwerksbox {huellbox} ({box['n_bauwerk']} Bauwerk, {box['n_gelaende']} "
          f"Gelände, entschieden durch: {box['entschieden_durch']})")

    bericht = lauf(glb, ZIEL / "lauf", huellbox, neu=a.neu,
                   aufloesung=a.aufloesung, samples=a.samples)
    if bericht is None:
        return 0

    geschrieben = bilder_aus_bericht(bericht, ZIEL)
    print("\nGESCHRIEBEN:")
    for pfad in geschrieben:
        print(f"  {pfad.relative_to(WURZEL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
