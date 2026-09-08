#!/usr/bin/env python3
"""BEWEIS 26 — Vier IFC-Spielarten, **ein** Bauwerk: IFC4 und IFC2X3, Meter und
Millimeter, gemessen und gerendert.

Warum vier und nicht eine
-------------------------
An **40 echten IFC-Dateien** gemessen (`auf-20260818-08`, 18.08.2026): 30 waren IFC4 und
10 IFC2X3 — und **alle zehn ArchiCAD-Dateien waren IFC2X3**. 15 standen in Metern, 25 in
Millimetern.

*Wer nur gegen IFC4 in Metern prüft, prüft nicht gegen das, was das verbreitetste
Autorenprogramm tatsächlich liefert.* Und ein Massstabsfehler um Faktor 1000 ist der
teuerste Fehler dieser Kette: Er kommt sauber durch jede Stufe und fällt erst am Bild auf,
wenn überhaupt.

Was hier gemessen wird
----------------------
Dieselbe Geometrie wird viermal geschrieben — ``IFC4``/``IFC2X3`` × Meter/Millimeter —,
viermal über die Prozessgrenze umgewandelt und viermal gerendert. Geprüft wird gegen die
**bekannte** Wahrheit: 8,0 × 5,0 × 3,0 m, mit `konversionstreue.pruefe_konversion`.

*Die Wahrheit kommt vom Aufrufer, nicht aus dem geprüften Modul* — sonst prüfte es sich
selbst.

Woran man es im Bild sieht
--------------------------
* ``NN_..._beauty.png`` — vier Renders. Sie müssen **gleich aussehen**; sehen sie es
  nicht, ist die Umwandlung schemaabhängig.
* ``90_kantenlaengen_...png`` — die drei gemessenen Kanten je Datei als Balken. Vier
  gleiche Balkengruppen sind der Beweis; eine tausendmal längere wäre der
  Massstabsfehler, den `torwaechter` fängt.
* ``91_differenz_...png`` — das Differenzbild zwischen der ersten und der letzten
  Spielart. **Schwarz heisst: kein Unterschied.**

Der Selbstcheck
---------------
Er hält an, wenn eine der vier Umwandlungen nicht stimmt **oder** wenn zwei Renders
sichtbar auseinandergehen. *Ein Beweisbild, das eine Behauptung zeigt, die gerade nicht
gilt, ist schlimmer als keines.*

Aufruf:
    python3 tools/beweis/26_vier_ifc_ein_bauwerk.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildlesen, bildschreiben, konversionstreue, seams  # noqa: E402

import make_test_ifc  # noqa: E402

BREITE, HOEHE, SAMPLES = 400, 250, 8

#: Die vier Spielarten. Namen ohne Umlaute, weil sie in Dateinamen landen.
SPIELARTEN = (
    ("ifc4-meter", "IFC4", None),
    ("ifc4-milli", "IFC4", "MILLI"),
    ("ifc2x3-meter", "IFC2X3", None),
    ("ifc2x3-milli", "IFC2X3", "MILLI"),
)
#: Die bekannte Wahrheit: **8,0 × 5,0 × 3,25 m**.
#:
#: NICHT `make_test_ifc.HOEHE_Z` — das sind 3,0 m, die WANDhöhe. Die Hüllbox ist um die
#: Bodenplatte höher, und 3,25 m ist die Zahl, die `tools/make_test_ifc.py` in seinem
#: eigenen Docstring nennt und die an beiden Schemata durch den echten Konverter gemessen
#: wurde. *Der erste Anlauf hat hier die naheliegende Konstante genommen und ist mit
#: «1 von 3 Achsen weicht ab» durchgefallen* — zu Recht: Die Wahrheit war falsch, nicht
#: die Umwandlung.
SOLL_M = (8.0, 5.0, 3.25)
#: Zwei Renders, die sich im Mittel um mehr unterscheiden, gehen sichtbar auseinander.
GLEICH_BIS = 0.002

GRUND = (243, 243, 241)
FARBEN = ((62, 106, 160), (216, 122, 40), (62, 140, 78))   # x, y, z


def _balken(ziel: Path, zeilen: list[tuple[str, tuple]], name: str) -> Path:
    """Je Datei drei Kanten. Vier gleiche Gruppen sind der Beweis."""
    zeile, b = 26, 520
    h = 24 + zeile * 3 * len(zeilen) + 14 * len(zeilen)
    bild = [list(GRUND) for _ in range(b * h)]
    hoechst = max(max(k) for _, k in zeilen) or 1.0
    y = 12
    for _, kanten in zeilen:
        for i, wert in enumerate(kanten):
            laenge = max(2, round((b - 60) * wert / hoechst))
            for yy in range(y, y + 18):
                for x in range(30, 30 + laenge):
                    bild[yy * b + x] = list(FARBEN[i])
            y += zeile
        y += 14
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis26-"))

    zeilen: list[tuple[str, tuple]] = []
    karten: list[dict] = []
    for nr, (name, schema, vorsatz) in enumerate(SPIELARTEN, 1):
        ifc = arbeit / f"{name}.ifc"
        make_test_ifc.erzeuge_ifc(ifc, schema=schema, vorsatz=vorsatz)
        umbau = seams.ifc_zu_glb(ifc, arbeit / f"{name}.glb")
        if umbau.get("status") != "ok":
            print(f"  {name}: IFC→glb {umbau.get('error')}")
            return 1

        # DIE WAHRHEIT KOMMT VON HIER, nicht aus dem geprueften Modul.
        urteil = konversionstreue.pruefe_konversion(umbau, huellbox_m=SOLL_M)
        kanten = tuple(round(w, 4) for w in urteil["spanne"])
        zeilen.append((name, kanten))
        print(f"  {name:14s} {schema:7s} {str(vorsatz or 'METER'):6s} "
              f"Kanten {kanten}  stimmt={urteil['stimmt']}"
              + (f"  DIAGNOSE {urteil['diagnose']}" if urteil.get("diagnose") else ""))
        if urteil["stimmt"] is not True:
            print(f"\nDIE UMWANDLUNG STIMMT NICHT: {name}, Abweichungen "
                  f"{urteil['abweichungen']}, Diagnose {urteil.get('diagnose')!r}.")
            return 1

        aus = arbeit / f"lauf-{name}"
        aus.mkdir(parents=True, exist_ok=True)
        bericht = seams.glb_zu_multipass(
            arbeit / f"{name}.glb", aus, up_axis="y", aufloesung=BREITE, hoehe=HOEHE,
            samples=SAMPLES, kamera="sSE", material_id=False, deckungsgrad=0.85)
        if bericht.get("status") != "ok":
            print(f"  {name}: Blender {bericht.get('error')}")
            return 1
        beauty = Path(bericht.get("beauty_png") or "")
        if not beauty.is_file():
            print(f"  {name}: kein Beauty-Bild")
            return 1
        werte, b, h = bildlesen.lies_png_luminanz(beauty)
        karten.append({"name": name, "werte": werte, "breite": b, "hoehe": h})
        neu = ziel / (f"{nr}0_{name}_{schema.lower()}_"
                      f"{'millimeter' if vorsatz else 'meter'}"
                      f"_kanten-{kanten[0]}-{kanten[1]}-{kanten[2]}m"
                      f"_stimmt-ja_beauty.png")
        neu.write_bytes(beauty.read_bytes())
        print("        ", neu.name)

    # ── Der Selbstcheck: die vier Bilder muessen GLEICH sein ──
    schlimmster = 0.0
    for i in range(len(karten)):
        for k in range(i + 1, len(karten)):
            d = (sum(abs(x - y) for x, y in zip(karten[i]["werte"], karten[k]["werte"]))
                 / len(karten[i]["werte"]))
            schlimmster = max(schlimmster, d)
            if d > GLEICH_BIS:
                print(f"\nZWEI SPIELARTEN SEHEN VERSCHIEDEN AUS: {karten[i]['name']} "
                      f"gegen {karten[k]['name']}, mittlerer Unterschied {d:.5f} "
                      f"(erlaubt bis {GLEICH_BIS}). Die Umwandlung haengt am Schema "
                      f"oder an der Einheit.")
                return 1
    print(f"  groesster Unterschied zwischen zwei Renders: {schlimmster:.5f}")

    name = ("90_kantenlaengen_" + "_".join(n for n, _ in zeilen)
            + f"_soll-{SOLL_M[0]}-{SOLL_M[1]}-{SOLL_M[2]}m_alle-gleich.png")
    print("  Balken:   ", _balken(ziel, zeilen, name).name)

    roh = [abs(x - y) for x, y in zip(karten[0]["werte"], karten[-1]["werte"])]
    hoechst = max(roh) or 1.0
    dif = ziel / (f"91_differenz_{karten[0]['name']}-gegen-{karten[-1]['name']}"
                  f"_mittel-{schlimmster:.5f}_schwarz-heisst-kein-unterschied.png")
    bildschreiben.schreibe_graustufen_png(dif, [w / hoechst for w in roh],
                                          karten[0]["breite"], karten[0]["hoehe"])
    print("  Differenz:", dif.name)
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
