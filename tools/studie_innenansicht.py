#!/usr/bin/env python3
"""STUDIE INNENANSICHT — trägt eine frontale Innenaufnahme überhaupt Tiefe?

Wozu
----
`docs/PLAN.md` führt seit dem 22.08.2026 einen Verdacht und ein Gegenargument, und
**beides war ungemessen**:

    «Verdacht gegen die frontale INNENANSICHT — ungemessen, und deshalb nicht
    abgeschaltet. `auf-29` fand: Für ρ über der Maske muss der Blick MEHR ALS EINE
    FLÄCHE zeigen, sonst misst man den Schätzer statt der Geometrie. […] Aber innen ist
    die Lage nicht dieselbe — Boden, Decke und die anschneidenden Seitenwände liegen
    schräg im Bild und tragen Tiefe.»

ρ selbst braucht den Tiefenschätzer und damit `torch`. Die **Vorprüfung** braucht ihn
nicht: Ob der Blick mehr als eine Fläche zeigt, steht in der **Soll-Karte**, und die
kommt aus Blender. Diese Studie misst genau das — und nicht mehr.

Was sie kann und was nicht
--------------------------
Sie ist eine **Vorprüfung**, und die Hausregel dazu ist vom 24.08.2026: *Renders und
Nullanker können ein Mass widerlegen, aber nicht tragen.* Zeigt eine Aufnahme keine
Tiefenordnung, kann ρ dort nichts messen — das ist ein Ausschluss und gilt. Zeigt sie
Tiefe, ist über das erzeugte Bild **nichts** gezeigt.

Gemessen wird je Fall:

* **Geometrieanteil** — wieviel des Bildes überhaupt Geometrie trägt.
* **Spanne** — grösste minus kleinste Tiefe in Metern.
* **Tiefenstufen** — verschiedene Werte auf 1 cm gerundet.
* **Grösste Ebene** — der Anteil des Bildes, der auf *einem* Wert liegt. **Das ist die
  Zahl, um die es geht:** Ein Bild, das zu vier Fünfteln auf einer Ebene liegt, trägt
  kaum Rangordnung, gleichgültig wie gross seine Spanne ist.

Die Brennweite wird **zweimal** gefahren: mit der, die `raumkamera` rechnet, und mit dem
Rückfall des Runners (50 mm). Der Unterschied war der eigentliche Fund.

Gebrauch
--------
    python tools/studie_innenansicht.py                  # kleine Auflösung, schnell
    python tools/studie_innenansicht.py --breite 1600 --hoehe 992
    python tools/studie_innenansicht.py --json

Braucht Blender und das `.venv-ifc` — **keine GPU**, kein Modellgewicht.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import bildlesen, raumkamera, seams  # noqa: E402

#: Der Rückfall, den der Blender-Runner stellt, wenn ihm niemand eine Brennweite nennt.
#: Nicht aus unserem Code — aus Blenders Vorgabe, am Bericht abgelesen
#: (``kamera.brennweite_mm`` bei ``weg: vorgegeben``).
RUECKFALL_MM = 50.0

#: Ab welchem Anteil auf **einer** Ebene die Aufnahme als flächenbeherrscht gilt. Eine
#: **Setzung**, keine Ablesung: Zwischen den gemessenen 0,6 % (über Eck) und 78,8 %
#: (frontal) liegt nichts, und wer die Lücke füllt, ändert die Zahl.
BEHERRSCHT_AB = 0.50


def _bauwerk(ziel: Path) -> Path:
    """Erzeugt die Testgeometrie mit Räumen — im Repo erzeugbar (Regel 3)."""
    sys.path.insert(0, str(WURZEL / "tools"))
    import make_test_ifc                                   # noqa: PLC0415

    return make_test_ifc.erzeuge_ifc(ziel / "bau.ifc", mit_raeumen=True)


def _kennzahlen(bericht: dict) -> dict:
    """Soll-Karte → die vier Zahlen. Reine Arithmetik, kein Schätzer."""
    tiefen, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    echt = [w for w in tiefen if w is not None and w < 1e6]
    if not echt:
        return {"geometrieanteil": 0.0, "spanne_m": None, "stufen": 0,
                "groesste_ebene": None, "groesste_ebene_anteil": None,
                "breite": breite, "hoehe": hoehe}
    haeufig = collections.Counter(round(w, 2) for w in echt)
    tiefe, n = haeufig.most_common(1)[0]
    return {"geometrieanteil": len(echt) / len(tiefen),
            "spanne_m": max(echt) - min(echt),
            "stufen": len(haeufig),
            "groesste_ebene": tiefe,
            # Anteil am **ganzen Bild**, nicht an der Geometrie: Ein Blick, der halb aus
            # Himmel besteht, ist nicht dadurch besser, dass die andere Hälfte eine
            # einzige Wand ist.
            "groesste_ebene_anteil": n / len(tiefen),
            "breite": breite, "hoehe": hoehe}


def messe(*, breite: int, hoehe: int, samples: int, arbeit: Path) -> list[dict]:
    ifc = _bauwerk(arbeit)
    glb = seams.ifc_zu_glb(str(ifc), str(arbeit / "modell.glb"))
    if glb.get("status") != "ok":
        raise SystemExit(f"IFC→glb scheiterte: {glb.get('error')}")

    raeume = seams.ifc_raeume(str(ifc))
    if raeume.get("status") != "ok":
        raise SystemExit(f"Raumleser scheiterte: {raeume.get('error')}")

    zeilen: list[dict] = []
    for raum in raeume.get("raeume") or []:
        punkte = raumkamera.standpunkte(raum)
        for stand in punkte["standpunkte"]:
            if stand.get("auge") is None:
                continue
            gerechnet = (stand.get("sichtfeld") or {}).get("brennweite_mm")
            for brennweite, quelle in ((gerechnet, "raumkamera"),
                                       (RUECKFALL_MM, "Rueckfall")):
                out = arbeit / f"{raum['name']}_{stand['art']}_{quelle}"
                out.mkdir(parents=True, exist_ok=True)
                bericht = seams.glb_zu_multipass(
                    str(arbeit / "modell.glb"), out, up_axis="Y",
                    aufloesung=breite, hoehe=hoehe, samples=samples,
                    auge=list(stand["auge"]), blick_auf=list(stand["blick_auf"]),
                    brennweite=brennweite)
                zeile = {"raum": raum["name"], "blick": stand["art"],
                         "brennweite_mm": brennweite, "quelle": quelle,
                         "status": bericht.get("status")}
                if bericht.get("status") == "ok":
                    zeile.update(_kennzahlen(bericht))
                else:
                    zeile["error"] = str(bericht.get("error"))[:300]
                zeilen.append(zeile)
    return zeilen


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--breite", type=int, default=800)
    p.add_argument("--hoehe", type=int, default=496,
                   help="Vorgabe 800×496 — dasselbe Seitenverhältnis wie 1600×992 "
                        "in der Produktion, bei einem Viertel der Rechenzeit")
    p.add_argument("--samples", type=int, default=8,
                   help="Für eine Tiefenkarte genügen wenige; sie ist nicht verrauscht")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="innenansicht-") as tmp:
        zeilen = messe(breite=a.breite, hoehe=a.hoehe, samples=a.samples,
                       arbeit=Path(tmp))

    if a.json:
        print(json.dumps(zeilen, ensure_ascii=False, indent=1))
        return 0

    print(f"Aufloesung {a.breite}×{a.hoehe}, {a.samples} Samples. "
          f"Gemessen wird die SOLL-Karte — kein Schaetzer, keine GPU.\n")
    print(f"{'Raum':<12} {'Blick':<10} {'Brennweite':<18} {'Geometrie':>9} "
          f"{'Spanne m':>9} {'Stufen':>7} {'groesste Ebene':>15}")
    for z in zeilen:
        if z["status"] != "ok":
            print(f"{z['raum']:<12} {z['blick']:<10} FEHLER: {z.get('error','')[:60]}")
            continue
        etikett = f"{z['brennweite_mm']:g} mm ({z['quelle']})"
        print(f"{z['raum']:<12} {z['blick']:<10} {etikett:<18} "
              f"{100*z['geometrieanteil']:8.1f}% {z['spanne_m']:9.3f} "
              f"{z['stufen']:7d} {100*z['groesste_ebene_anteil']:14.1f}%")

    beherrscht = [z for z in zeilen if z["status"] == "ok"
                  and z["groesste_ebene_anteil"] is not None
                  and z["groesste_ebene_anteil"] >= BEHERRSCHT_AB]
    print(f"\nVON EINER FLAECHE BEHERRSCHT (>= {BEHERRSCHT_AB:.0%} auf einer Ebene): "
          f"{len(beherrscht)} von {len(zeilen)}")
    for z in beherrscht:
        print(f"   {z['raum']} {z['blick']} bei {z['brennweite_mm']:g} mm "
              f"({z['quelle']}) — {100*z['groesste_ebene_anteil']:.1f} %")
    print("\nDas ist eine VORPRUEFUNG: Wo keine Tiefenordnung steht, kann rho nichts "
          "messen.\nWo eine steht, ist ueber das ERZEUGTE Bild nichts gezeigt.")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
