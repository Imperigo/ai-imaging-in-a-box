#!/usr/bin/env python3
"""STUDIE GELÄNDEFORM — was die Formregel trennt, und was sie kostet.

Wozu
----
`aiimaging.gelaendeform` erkennt Gelände an der Gestalt statt am Namen. Ihre drei
Schwellen wären ohne diese Studie **abgelesen** — genau das, wogegen dieses Projekt seit
drei Wochen antritt. Hier werden sie gemessen.

Gemessen wird an **synthetischen Beständen mit bekannter Wahrheit**: Für jeden Körper
steht vorher fest, ob er Gelände ist. Die Namen sind nach echtem Bestand nachgebaut
(`IfcCovering_Sub-Division:1`, `IfcCovering_Toposolid_1`, `Decke-025`) — **keine
Projektdaten, nur Namensmuster**, und alle im Repo erzeugbar (Regel 3).

Die beiden Fehlerrichtungen werden **getrennt** gezählt, weil sie nicht gleich teuer sind:

* **Gelände in der Maske** (falsch als Bauwerk gezählt) macht die Maske stumpf — auf einer
  Bodenszene erreichte weisses Rauschen dort den Score 0,72.
* **Bauwerk fälschlich ausgeschlossen** macht die Box zu klein; die Kamera steht zu nah,
  und das Bauwerk wird angeschnitten.

Der erste ist der teurere. Die Schwellen sind darum streng — im Zweifel Bauwerk.

    python tools/studie_gelaendeform.py
    python tools/studie_gelaendeform.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import gelaendeform as gf  # noqa: E402

#: Die Bestände. Je Körper ``(name, lo, hi, ist_wirklich_gelaende)`` in **glTF-Koordinaten**
#: (Y oben) — dieselbe Form, die ``tools/make_test_glb.py::baue_glb`` nimmt und die
#: ``glbbox.knotenboxen`` liefert.
BESTAENDE: dict[str, list[tuple]] = {
    # Der Normalfall: Quader auf Platte. Der Name der Platte verrät nichts.
    "quader_auf_platte": [
        ("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50), True),
        ("Wand-01", (-10, 0, -10), (10, 30, 10), False),
    ],
    # DER PRUEFSTEIN. Nachgebaut nach der echten Bestandsmessung vom 06.09.2026: zwanzig
    # `IfcCovering_Sub-Division`-Knoten bilden zusammen 47 % der Szenenspannweite und
    # blieben nach der Namensregel der groesste «Bauwerks»-Knoten.
    "sub_division": [
        ("IfcCovering_Sub-Division:1", (-47, -0.5, -47), (47, 0, 47), True),
        ("Stuetze-01", (-8, 0, -8), (8, 36, 8), False),
        ("IfcCivilElement_Nachbar_1", (60, 0, 60), (80, 20, 80), False),
    ],
    # Riegel: langes Bauwerk, Gelaende nur wenig groesser.
    "riegel": [
        ("Gelaende-Platte", (-60, -1, -20), (60, 0, 20), True),
        ("Riegel", (-50, 0, -8), (50, 22, 8), False),
    ],
    # DER TEURE GEGENFALL: eine grosse flache Geschossdecke IM Bauwerk. Nach Form sieht
    # sie aus wie Gelaende — daran faellt eine zu grosszuegige Schwelle auf.
    "decke_im_bauwerk": [
        ("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50), True),
        ("Decke-025", (-30, 14, -30), (30, 14.4, 30), False),
        ("Wand-01", (-30, 0, -30), (30, 30, 30), False),
    ],
    # Gelaende auf zwei Ebenen: Platte unten, Terrasse darueber.
    "zwei_ebenen": [
        ("IfcCovering_Toposolid_1", (-50, -1, -50), (50, 0, 50), True),
        ("Terrasse", (-40, 3, 10), (40, 3.4, 45), True),
        ("Wand-01", (-20, 0, -20), (20, 26, 20), False),
    ],
    # Gar kein Gelaende. Hier darf die Form NICHTS finden.
    "ohne_gelaende": [
        ("Wand-01", (-20, 0, -20), (20, 30, 20), False),
        ("Dach", (-22, 30, -22), (22, 31, 22), False),
    ],
}


def _messe(bestand: list[tuple]) -> dict:
    alle = [(n, lo, hi) for n, lo, hi, _ in bestand]
    wahrheit = {n: g for n, _lo, _hi, g in bestand}
    befund = gf.gelaende_knoten(alle)

    treffer = fehlend = falsch = unklar = 0
    zeilen = []
    for u in befund["urteile"]:
        soll = wahrheit[u["name"]]
        ist = u["urteil"]
        if ist == gf.NICHT_ENTSCHEIDBAR:
            lage, unklar = "nicht entscheidbar", unklar + 1
        elif soll and ist == gf.GELAENDE:
            lage, treffer = "richtig", treffer + 1
        elif soll:
            lage, fehlend = "GELAENDE UEBERSEHEN", fehlend + 1
        elif ist == gf.GELAENDE:
            lage, falsch = "BAUWERK AUSGESCHLOSSEN", falsch + 1
        else:
            lage = "richtig"
        zeilen.append({"name": u["name"], "soll": "gelaende" if soll else "bauwerk",
                       "ist": ist, "lage": lage, **u["merkmale"]})
    return {"zeilen": zeilen, "treffer": treffer, "gelaende_uebersehen": fehlend,
            "bauwerk_ausgeschlossen": falsch, "unklar": unklar}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="maschinenlesbar ausgeben")
    a = ap.parse_args(argv)

    ergebnis = {name: _messe(b) for name, b in BESTAENDE.items()}
    if a.json:
        print(json.dumps(ergebnis, ensure_ascii=False, indent=1))
        return 0

    print(f"SCHWELLEN: Grundrissanteil >= {gf.GRUNDRISSANTEIL_MIN:.0%}, "
          f"Flachheit <= {gf.FLACHHEIT_MAX}, Tieflage <= {gf.TIEFLAGE_MAX:.0%} "
          f"(unklar bis {gf.TIEFLAGE_UNKLAR_MAX:.0%})\n")
    print(f"{'Bestand':<20} {'Knoten':<28} {'soll':<9} {'ist':<19} "
          f"{'Anteil':>7} {'Flach':>7} {'Tief':>6}  Lage")
    summe = {"gelaende_uebersehen": 0, "bauwerk_ausgeschlossen": 0, "unklar": 0}
    for name, aus in ergebnis.items():
        for z in aus["zeilen"]:
            print(f"{name:<20} {z['name'][:27]:<28} {z['soll']:<9} {z['ist']:<19} "
                  f"{z['grundrissanteil']:>6.1%} {z['flachheit']:>7.2f} "
                  f"{z['tieflage']:>5.0%}  "
                  f"{'' if z['lage'] == 'richtig' else z['lage']}")
        for k in summe:
            summe[k] += aus[k]

    print()
    print(f"BAUWERK FAELSCHLICH AUSGESCHLOSSEN: {summe['bauwerk_ausgeschlossen']}  "
          f"(die TEURE Richtung — Gelaende in der Maske macht sie stumpf)")
    print(f"GELAENDE UEBERSEHEN:                {summe['gelaende_uebersehen']}  "
          f"(die billigere — die Box bleibt zu gross, das faellt auf)")
    print(f"NICHT ENTSCHEIDBAR:                 {summe['unklar']}  "
          f"(kein Fehler, sondern die dritte Antwort)")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
