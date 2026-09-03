#!/usr/bin/env python3
"""Trennt der Kantenanteil noch, wenn hinter dem Bauwerk ein Nachbar steht?

**Wozu es diese Studie gibt** (02.09.2026): Seit gestern trägt die Bauwerksmaske einen
Vorbehalt — steht ein `IfcCivilElement` in der Szene, sei der Kantenanteil an der
Maskengrenze nur eingeschränkt aussagekräftig. Die Zahlen dazu (+0.0016 gegen −0.0024)
stammen aus `auf-20260823-37`, also **von der HomeStation und nicht von hier**.

*Einen fremden Vorbehalt weiterzutragen ist bequem und wird mit jeder Weitergabe
unschärfer.* Diese Studie rechnet ihn nach — ohne GPU, ohne Bildmodell, mit gebauten
Karten.

**Der Mechanismus, den sie prüft:** Der Kantenanteil zählt, wie viel der Maskengrenze im
Bild wirklich als **Tiefensprung** dasteht. Hinter dem Bauwerk Himmel heisst: unendlicher
Sprung, jede Grenzstelle zählt. Hinter dem Bauwerk ein Nachbar in ähnlicher Tiefe heisst:
kleiner Sprung — und dann sieht ein perfektes Bild dort aus wie irgendeines.

    python tools/studie_nachbargebaeude.py

Ergebnis: `docs/NACHBARGEBAEUDE_2026-09-02.md`.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_test_glb import baue_glb                          # noqa: E402
from studie_paarmasse import HERZSCHLAG_S, HINTERGRUND_M    # noqa: E402
from aiimaging import bildlesen, geometrie_qa, seams        # noqa: E402
from aiimaging import maske as maske_modul                  # noqa: E402

AUFLOESUNG = 192
SAMPLES = 4
SAAT = 20260902

#: Das Zielbauwerk. Die Namen sind IFC-Klassen, damit die Maskenregel greift wie im Betrieb.
ZIEL = ("IfcWall_Zielbau", (-6.0, 0.0, -4.0), (6.0, 12.0, 4.0))

#: Der Nachbar — **hinter** dem Ziel, aus Sicht der Kamera. `IfcCivilElement` ist die
#: Klasse, unter der ein Nachbargebäude im gemessenen Bestand stand (01.09.2026); die
#: Maskenregel zählt sie seit gestern als Umfeld und nicht als Bauwerk.
def _nachbar(abstand_m: float):
    """Ein Nachbar, der den Hintergrund **wirklich füllt**.

    *Der erste Anlauf war zu klein* (28 × 16 m): Er deckte nur 9,8 % des Hintergrunds,
    und der Kantenanteil trennte weiter mühelos. Das war kein Gegenbeweis zum Vorbehalt,
    sondern eine Szene, die die Bedingung gar nicht herstellte — **die häufigste Art,
    eine Messung zu verfehlen.**

    Er misst darum 120 × 40 m. Wie viel er wirklich deckt, steht als
    ``anteil_hintergrund_endlich`` in jeder Zeile; ohne diese Zahl wäre «Nachbar ja/nein»
    nur ein Dateiname.
    """
    return ("IfcCivilElement_Nachbar",
            (-60.0, 0.0, -4.0 - abstand_m - 8.0), (60.0, 40.0, -4.0 - abstand_m))


#: Die Hüllbox des **Zielbauwerks im Weltsystem**, nach der Y-up→Z-up-Drehung des
#: Importers: glTF ``(x, y, z)`` wird zu ``(x, −z, y)``.
#:
#: **Sie muss ausdrücklich übergeben werden, und das ist der zweite verfehlte Anlauf
#: dieser Studie.** Ohne sie rahmt der Runner die ganze Szene — und die ist hier 120 m
#: breit, weil der Nachbar so gross sein muss. Das Ziel wurde damit winzig, über dem
#: Nachbarn stand viel Himmel, und **86 % des Hintergrunds waren wieder Himmel**: genau
#: die Bedingung, die nicht herrschen sollte.
#:
#: *Eine Szene, die die Bedingung nicht herstellt, widerlegt keinen Vorbehalt — sie misst
#: etwas anderes und sieht dabei aus wie eine Messung.*
ZIEL_HUELLBOX = [[-6.0, -4.0, 0.0], [6.0, 4.0, 12.0]]


def _multipass(glb: Path, aus: Path) -> dict:
    datei = aus / "blender-report.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))
    return seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=AUFLOESUNG,
                                  samples=SAMPLES, kamera="s",
                                  kamera_huellbox=ZIEL_HUELLBOX,
                                  herzschlag_takt_s=HERZSCHLAG_S)


def _geglaettet(karte, breite: int, hoehe: int):
    """3x3-Mittel — der grobe Ersatz fuer die Unschaerfe eines Tiefenschaetzers."""
    aus = list(karte)
    for y in range(1, hoehe - 1):
        for x in range(1, breite - 1):
            aus[y * breite + x] = sum(
                karte[(y + dy) * breite + x + dx]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    return aus


def messe(name: str, koerper, wurzel: Path) -> dict:
    """Kantenanteil für ein perfektes Bild und für weisses Rauschen — und ihr Abstand."""
    glb = wurzel / f"{name}.glb"
    if not glb.exists():
        glb.write_bytes(baue_glb(koerper, materialien=[k[0] for k in koerper]))
    bericht = _multipass(glb, wurzel / name)

    soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
    gebaut = maske_modul.maske_aus_bericht(bericht, gelaende_erwartet=False)
    maske = gebaut.get("maske")
    if maske is None:
        return {"szene": name, "fehler": gebaut.get("grund")}

    wuerfel = random.Random(SAAT)
    rauschen = [wuerfel.random() for _ in soll]

    perfekt = geometrie_qa.anteil_grenze_mit_kante(soll, maske, breite=breite)["anteil"]
    weiss = geometrie_qa.anteil_grenze_mit_kante(rauschen, maske, breite=breite)["anteil"]

    # UND DIE ENTSCHEIDENDE DRITTE SPALTE: eine GEGLAETTETE Karte.
    #
    # Die perfekte Karte trennt auch mit Nachbarn muehelos — der Sprung ist klein, aber
    # er ist da. Ein echter Tiefenschaetzer hat diese Schaerfe nicht: Bei 170 m Abstand
    # ist ein Nachbar 1 m dahinter ein relativer Unterschied von 0,6 %, und der
    # verschwindet im Rauschen des Schaetzers.
    #
    # Die Glaettung ist ein GROBER Ersatz dafuer und keine Nachbildung — sie sagt nur,
    # ob der Mechanismus ueberhaupt in diese Richtung zeigt.
    geglaettet = _geglaettet(soll, breite, hoehe)
    glatt = geometrie_qa.anteil_grenze_mit_kante(geglaettet, maske, breite=breite)["anteil"]

    # Der HINTERGRUND hinter der Maske: Steht dort Himmel (Hintergrundmarke) oder ein
    # Koerper? Das ist die Groesse, an der der Mechanismus haengt, und sie gehoert in den
    # Bericht — sonst ist «Nachbar ja/nein» nur ein Dateiname.
    hinter = [w for w, m in zip(soll, maske) if not m]
    endlich = [w for w in hinter if w < HINTERGRUND_M]
    return {
        "szene": name,
        "n_maske": sum(1 for m in maske if m),
        "anteil_hintergrund_endlich": round(len(endlich) / len(hinter), 4) if hinter else None,
        "kantenanteil_perfekt": round(perfekt, 4) if perfekt is not None else None,
        "kantenanteil_rauschen": round(weiss, 4) if weiss is not None else None,
        "kantenanteil_geglaettet": round(glatt, 4) if glatt is not None else None,
        "abstand": (round(perfekt - weiss, 4)
                    if perfekt is not None and weiss is not None else None),
        "abstand_geglaettet": (round(glatt - weiss, 4)
                               if glatt is not None and weiss is not None else None),
        "umfeld_namen": gebaut.get("umfeld_namen") or [],
        "warnung_nachbar": any("NACHBARGEBAEUDE" in w
                               for w in (gebaut.get("warnungen") or [])),
    }


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0]) if argv else Path("build/nachbar")
    wurzel.mkdir(parents=True, exist_ok=True)

    faelle = [
        ("himmel", (ZIEL,)),
        ("nachbar_1m", (ZIEL, _nachbar(1.0))),
        ("nachbar_5m", (ZIEL, _nachbar(5.0))),
        ("nachbar_20m", (ZIEL, _nachbar(20.0))),
    ]
    zeilen = [messe(name, koerper, wurzel) for name, koerper in faelle]

    print(f"{'Szene':<12} {'Hgr. endl.':>11} {'perfekt':>8} {'geglaettet':>11} "
          f"{'Rauschen':>9} {'Abst.perf':>10} {'Abst.glatt':>11}")
    for z in zeilen:
        if z.get("fehler"):
            print(f"{z['szene']:<12} FEHLER: {z['fehler']}")
            continue
        print(f"{z['szene']:<12} {z['anteil_hintergrund_endlich']:>11.4f} "
              f"{z['kantenanteil_perfekt']:>8.4f} {z['kantenanteil_geglaettet']:>11.4f} "
              f"{z['kantenanteil_rauschen']:>9.4f} {z['abstand']:>10.4f} "
              f"{z['abstand_geglaettet']:>11.4f}")

    (wurzel / "roh.json").write_text(json.dumps(zeilen, indent=1), encoding="utf-8")
    print(f"\n{len(zeilen)} Szenen -> {wurzel}/roh.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
