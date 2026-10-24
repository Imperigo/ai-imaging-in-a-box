"""Vogelschau und Draufsicht für ein Situationsmodell — Kameras für die Brücke, Raster fürs Bild.

**Anlass (Ergebnis auf-20261024-354, Auftrag 356):** Eine Anlage von rund 500 m zeigt sich in
Augenhöhe als Strich am Horizont. Dieses Werkzeug rechnet für eine glb die erhöhten Kameras
und gibt sie als ``CameraSpec``-Liste aus — so, wie sie in ``scene.cameras`` an
``POST /bruecke/jobs`` gehen (Z oben, ``perspektive: frei``). Gerechnet wird in
:mod:`aiimaging.kameras` (Regel 4); hier wird nur gelesen, gerufen und geschrieben.

Die Box ist dieselbe wie bei den Auto-Kameras: nach den Bauteilen
(:func:`aiimaging.glbbox.rahmungsbox`), sonst die ganze Szene.

Aufruf::

    python3 tools/vogelschau.py kameras MODELL.glb [--hoehe 45 --hoehe 30] [--richtung sSE]
                                [--draufsicht] [--zelle B3] [--aufloesung 960x600]
                                [--brennweite 35] [--achse Y]
    python3 tools/vogelschau.py raster PLAN.png PLAN_RASTER.png

``--draufsicht`` gibt die Draufsicht (89 Grad von Süden, Norden oben) dazu. ``--zelle B3``
rechnet dieselbe Draufsicht und stellt danach eine Vogelschau auf die Zelle B3 ihres Rasters;
``--zelle B2:C3`` nimmt das Gebiet von B2 bis C3 (der Kreuzpunkt der vier Zellen)
(Spalten A–D von links, Zeilen 1–4 von oben). ``raster`` zeichnet dieses Raster über ein Bild
(Pillow, nur dort gebraucht).

Ausgabe von ``kameras``: JSON ``{situation, box, cameras}`` auf stdout. Keine Pfade.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import glbbox, kameras, kosmo_szene  # noqa: E402


def box_der_bauteile(glb, achse: str = "Y") -> list:
    """Die Box, nach der die Auto-Kameras rahmen: Bauteile, sonst die ganze Szene."""
    box = glbbox.rahmungsbox(glb, up_axis=achse).get("box")
    if box is None:
        box = glbbox.bauwerksbox(glb, up_axis=achse).get("bbox_szene")
    if box is None:
        raise SystemExit("Keine lesbare Huellbox in der glb.")
    return [list(map(float, box[0])), list(map(float, box[1]))]


def _spec(kamera: dict) -> dict:
    spec = kosmo_szene.kamera_zu_spec({"kuerzel": kamera["kuerzel"], "auge": kamera["auge"],
                                       "blick_auf": kamera["blick_auf"],
                                       "brennweite_mm": kamera["brennweite_mm"]})
    spec["perspektive"] = kosmo_szene.PERSPEKTIVE_FREI
    return spec


def kameras_fuer(glb, *, hoehen=(), richtung: str = "sSE", draufsicht: bool = False,
                 zelle: str | None = None, seitenverhaeltnis: float = 1.6,
                 brennweite_mm: float = kameras.BRENNWEITE_MM, achse: str = "Y") -> dict:
    """``{situation, box, cameras, erklaerung}`` — die Kameras als ``CameraSpec``."""
    box = box_der_bauteile(glb, achse)
    gestellt, erklaerung = [], []

    def stelle(b, kuerzel, hoehe, name=None):
        k = kameras.vogelschau(b, kuerzel=kuerzel, hoehe_grad=hoehe,
                               brennweite_mm=brennweite_mm, seitenverhaeltnis=seitenverhaeltnis)
        if name:
            k["kuerzel"] = name
        gestellt.append(_spec(k))
        erklaerung.append({"name": k["kuerzel"], "abstand_m": k["abstand_m"],
                           "kamerahoehe_m": k["kamerahoehe_m"], "fuellgrad": k["fuellgrad"]})
        return k

    plan = None
    if draufsicht or zelle:
        plan = kameras.vogelschau(box, kuerzel="s", hoehe_grad=kameras.DRAUFSICHT_GRAD,
                                  brennweite_mm=brennweite_mm,
                                  seitenverhaeltnis=seitenverhaeltnis)
    if draufsicht:
        stelle(box, "s", kameras.DRAUFSICHT_GRAD)
    for hoehe in hoehen:
        stelle(box, richtung, float(hoehe), f"vogelschau-{richtung}-{float(hoehe):g}")
    if zelle:
        bereich = kameras.rasterzelle_bereich(
            zelle, plan["auge"], plan["blick_auf"], boden_z=box[0][2],
            hoehe_m=box[1][2] - box[0][2], brennweite_mm=brennweite_mm,
            seitenverhaeltnis=seitenverhaeltnis)
        hoehe = float(hoehen[0]) if hoehen else kameras.VOGELSCHAU_GRAD
        stelle(bereich, richtung, hoehe, f"zelle-{zelle.upper().replace(':', '')}-{richtung}")
    return {"situation": kameras.ist_situationsmodell(box), "box": box,
            "cameras": gestellt, "erklaerung": erklaerung}


def raster_zeichnen(quelle, ziel) -> None:
    """Das Raster A–D × 1–4 über ein Bild — dünne Linien, Beschriftung je Zelle oben links."""
    from PIL import Image, ImageDraw  # noqa: PLC0415 — nur hier gebraucht

    bild = Image.open(quelle).convert("RGB")
    breite, hoehe = bild.size
    zeichnung = ImageDraw.Draw(bild)
    n_s, n_z = len(kameras.RASTER_SPALTEN), kameras.RASTER_ZEILEN
    for i in range(1, n_s):
        x = round(i * breite / n_s)
        zeichnung.line([(x, 0), (x, hoehe)], fill=(255, 40, 40), width=2)
    for j in range(1, n_z):
        y = round(j * hoehe / n_z)
        zeichnung.line([(0, y), (breite, y)], fill=(255, 40, 40), width=2)
    for i, spalte in enumerate(kameras.RASTER_SPALTEN):
        for j in range(n_z):
            x, y = round(i * breite / n_s) + 6, round(j * hoehe / n_z) + 4
            text = f"{spalte}{j + 1}"
            zeichnung.rectangle([x - 2, y - 1, x + 7 * len(text) + 2, y + 12], fill=(255, 255, 255))
            zeichnung.text((x, y), text, fill=(200, 0, 0))
    Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    bild.save(ziel)


def _aufloesung(text: str) -> float:
    try:
        b, h = (int(t) for t in str(text).lower().split("x"))
        return b / h
    except (ValueError, ZeroDivisionError) as fehler:
        raise SystemExit(f"--aufloesung braucht BREITExHOEHE, war {text!r}.") from fehler


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    unter = ap.add_subparsers(dest="was", required=True)
    k = unter.add_parser("kameras")
    k.add_argument("glb")
    k.add_argument("--hoehe", type=float, action="append", default=[])
    k.add_argument("--richtung", default="sSE")
    k.add_argument("--draufsicht", action="store_true")
    k.add_argument("--zelle", default=None)
    k.add_argument("--aufloesung", default="960x600")
    k.add_argument("--brennweite", type=float, default=kameras.BRENNWEITE_MM)
    k.add_argument("--achse", default="Y")
    r = unter.add_parser("raster")
    r.add_argument("bild")
    r.add_argument("ziel")
    a = ap.parse_args(argv)
    if a.was == "raster":
        raster_zeichnen(a.bild, a.ziel)
        print(f"Raster {kameras.RASTER_SPALTEN[0]}1–{kameras.RASTER_SPALTEN[-1]}"
              f"{kameras.RASTER_ZEILEN} gezeichnet.")
        return 0
    try:
        aus = kameras_fuer(a.glb, hoehen=a.hoehe, richtung=a.richtung, draufsicht=a.draufsicht,
                           zelle=a.zelle, seitenverhaeltnis=_aufloesung(a.aufloesung),
                           brennweite_mm=a.brennweite, achse=a.achse)
    except ValueError as fehler:
        print(str(fehler), file=sys.stderr)
        return 2
    print(json.dumps(aus, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
