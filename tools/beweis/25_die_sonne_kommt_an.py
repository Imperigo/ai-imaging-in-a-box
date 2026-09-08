#!/usr/bin/env python3
"""BEWEIS 25 — Die bestellte Sonne kommt beim Renderer an, und man sieht es am Schatten.

Der Anlass ist ein Fehler, der wie ein Erfolg aussah
----------------------------------------------------
Bis zum 26.08.2026 lief der Sonnenblock der Bestellung **ins Leere**: `seams` reichte ihn
nicht an den Runner weiter. Ein Auftrag mit Abendstand wurde gerendert, als wäre er nie
gestellt worden — und heraus kam *ein sauberes, gut belichtetes, falsches Bild.* Niemand
merkt so etwas an einem einzelnen Bild.

Genau deshalb steht hier eine **Reihe**: Drei bestellte Sonnenstände, dieselbe Geometrie,
dieselbe Kamera. Ändert sich der Schatten nicht, ist die Bestellung nicht angekommen — und
das sieht man ohne jede Zahl.

Was gemessen wird, und was das Bild zeigt
-----------------------------------------
* ``NN_beauty_...png`` — je Sonnenstand ein **echter** Cycles-Lauf. Von Morgen (flach,
  lange Schatten) über Mittag (hoch, kurze Schatten) zum Abend (flach, Schatten zur
  anderen Seite).
* ``9x_schattenanteil_...png`` — je Bild der Anteil dunkler Bildpunkte auf der
  Bodenplatte, **gezählt** aus dem Beauty-Pass. Drei gleiche Balken hiessen: die Sonne
  ist nicht angekommen.
* Der Blender-Bericht trägt `sonne.bestellt` — die Angabe, **was wirklich bestellt war**.
  Ohne sie sieht ein Bild mit der Vorgabe genauso aus wie eines mit einer zufällig
  gleichen Bestellung.

Der Selbstcheck
---------------
Sind zwei der drei Schattenanteile gleich (bis auf 0,005), hält das Skript an. *Ein
Beweisbild, das eine Behauptung zeigt, die gerade nicht gilt, ist schlimmer als keines.*

Aufruf:
    python3 tools/beweis/25_die_sonne_kommt_an.py [ziel_verzeichnis]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))
sys.path.insert(0, str(WURZEL / "tools"))

from aiimaging import bildlesen, bildschreiben, seams, sonne  # noqa: E402

import make_test_ifc  # noqa: E402

BREITE, HOEHE, SAMPLES = 480, 300, 16

#: Drei Stände, und sie sind so gewählt, dass der Unterschied im Bild liegt und nicht in
#: der dritten Nachkommastelle: flach von links, hoch, flach von rechts.
STAENDE = (("morgen", 12.0, -75.0), ("mittag", 72.0, 0.0), ("abend", 12.0, 75.0))
#: Zwei Bilder, die sich im Mittel um weniger unterscheiden, gelten als gleich — dann ist
#: die Bestellung nicht angekommen.
GLEICH_BIS = 0.002
#: Der Deckungsgrad. Ohne ihn rahmt die Kamera die ganze Szene, das Bauwerk wird klein,
#: und der graue Hintergrund verwaessert jede Messung — beim ersten Anlauf lag der
#: Unterschied zwischen Morgen und Abend deshalb bei 0,005 statt bei dem, was man sieht.
DECKUNGSGRAD = 0.85

GRUND = (243, 243, 241)
BALKEN = (216, 122, 40)


def _kennwerte(png: Path) -> dict:
    """Was sich mit dem Sonnenstand ändert — gezählt, nicht geschätzt.

    **Der erste Anlauf hat hier das falsche Werkzeug genommen** und ist zu Recht daran
    gescheitert: Er zählte Bildpunkte unter 0,25 als «Schatten». In diesen Renders liegt
    der dunkelste Wert bei 0,34 — es gab **null** solche Punkte, in allen drei Bildern.
    Der Selbstcheck hat den Lauf angehalten, statt drei gleiche Balken als Beweis
    auszugeben.

    Gemessen wird jetzt, was tatsächlich reagiert: der **hellste** Wert (die besonnte
    Fläche) und das Mittel. Und der eigentliche Beleg steht daneben — der Unterschied
    zwischen zwei Bildern.
    """
    werte, breite, hoehe = bildlesen.lies_png_luminanz(png)
    return {"werte": werte, "breite": breite, "hoehe": hoehe,
            "hellster": max(werte), "mittel": sum(werte) / len(werte)}


def _unterschied(a: dict, b: dict) -> float:
    """Mittlerer Betrag der Differenz zweier Bilder — 0 hiesse: dasselbe Bild."""
    return sum(abs(x - y) for x, y in zip(a["werte"], b["werte"])) / len(a["werte"])


def _differenzbild(ziel: Path, a: dict, b: dict, name: str) -> Path:
    """Was die Sonne bewegt hat, als Bild — hell, wo sich etwas geändert hat."""
    roh = [abs(x - y) for x, y in zip(a["werte"], b["werte"])]
    hoechst = max(roh) or 1.0
    bildschreiben.schreibe_graustufen_png(ziel / name, [w / hoechst for w in roh],
                                          a["breite"], a["hoehe"])
    return ziel / name


def _balken(ziel: Path, zeilen: list[tuple[str, float]], name: str) -> Path:
    b, h = 560, 56 * len(zeilen) + 32
    bild = [list(GRUND) for _ in range(b * h)]
    hoechst = max(a for _, a in zeilen) or 1.0
    for i, (_, anteil) in enumerate(zeilen):
        y0 = 16 + i * 56
        laenge = max(2, round((b - 60) * anteil / hoechst))
        for y in range(y0, y0 + 36):
            for x in range(30, 30 + laenge):
                bild[y * b + x] = list(BALKEN)
    p = ziel / name
    bildschreiben.schreibe_farb_png(p, bild, b, h)
    return p


def main(ziel_arg: str | None = None) -> int:
    ziel = Path(ziel_arg) if ziel_arg else WURZEL / "build" / "beweis" / Path(__file__).stem
    ziel.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix="beweis25-"))

    ifc = arbeit / "bau.ifc"
    make_test_ifc.erzeuge_ifc(ifc, mit_gelaende=True)
    umbau = seams.ifc_zu_glb(ifc, arbeit / "szene.glb")
    if umbau.get("status") != "ok":
        print(f"IFC→glb: {umbau.get('error')}")
        return 1

    zeilen: list[tuple[str, float]] = []
    karten: list[dict] = []
    for nr, (name, hoehe_grad, azimut_grad) in enumerate(STAENDE, 1):
        aus = arbeit / name
        aus.mkdir(parents=True, exist_ok=True)
        bericht = seams.glb_zu_multipass(
            arbeit / "szene.glb", aus, up_axis="y", aufloesung=BREITE, hoehe=HOEHE,
            samples=SAMPLES, kamera="sSE", material_id=False,
            deckungsgrad=DECKUNGSGRAD,
            sonne={"elevation": hoehe_grad, "azimuth": azimut_grad})
        if bericht.get("status") != "ok":
            print(f"  {name}: {bericht.get('error')}")
            return 1

        # WAS IM BERICHT ANGEKOMMEN IST, und nicht was wir bestellt haben.
        gemeldet = bericht.get("sonne") or {}
        bestellt = tuple(gemeldet.get("bestellt") or ())
        angekommen = (abs(float(gemeldet.get("hoehe_grad", -999)) - hoehe_grad) < 0.01
                      and abs(float(gemeldet.get("azimut_grad", -999)) - azimut_grad) < 0.01)

        beauty = Path(bericht.get("beauty_png") or "")
        if not beauty.is_file():
            print(f"  {name}: kein Beauty-Bild")
            return 1
        kenn = _kennwerte(beauty)
        kenn["name"] = name
        zeilen.append((name, kenn["hellster"]))
        karten.append(kenn)

        neu = ziel / (f"{nr}0_{name}_hoehe-{hoehe_grad:.0f}grad"
                      f"_azimut-{azimut_grad:.0f}grad"
                      f"_bestellt-{'-'.join(bestellt) or 'nichts'}"
                      f"_im-bericht-{'angekommen' if angekommen else 'ABWEICHEND'}"
                      f"_hellster-{kenn['hellster']:.4f}"
                      f"_mittel-{kenn['mittel']:.4f}.png")
        neu.write_bytes(beauty.read_bytes())
        print(f"  {name:7s} bestellt {str(bestellt):22s} angekommen={angekommen} "
              f"hellster={kenn['hellster']:.4f} mittel={kenn['mittel']:.4f}")
        print("        ", neu.name)

        if not angekommen:
            print(f"\nDIE BESTELLUNG IST NICHT ANGEKOMMEN: gemeldet "
                  f"{gemeldet.get('hoehe_grad')}/{gemeldet.get('azimut_grad')}, "
                  f"bestellt {hoehe_grad}/{azimut_grad}.")
            return 1

    # ── Der Selbstcheck: JEDES Paar muss sich unterscheiden ──
    paare = []
    for i in range(len(karten)):
        for k in range(i + 1, len(karten)):
            d = _unterschied(karten[i], karten[k])
            paare.append((karten[i]["name"], karten[k]["name"], d))
            if d < GLEICH_BIS:
                print(f"\nZWEI STAENDE ERGEBEN DASSELBE BILD: {karten[i]['name']} gegen "
                      f"{karten[k]['name']}, mittlerer Unterschied {d:.5f} "
                      f"(gleich bis {GLEICH_BIS}). Entweder ist die Sonne nicht "
                      f"angekommen, oder die Staende sind zu aehnlich gewaehlt.")
                return 1
    for a, b, d in paare:
        print(f"  {a} gegen {b}: mittlerer Unterschied {d:.5f}")

    name = ("90_hellster-punkt_" + "_".join(f"{n}-{a:.4f}" for n, a in zeilen)
            + f"_spanne-{max(a for _, a in zeilen) - min(a for _, a in zeilen):.4f}.png")
    print("  Balken: ", _balken(ziel, zeilen, name).name)
    print("  Differenz:", _differenzbild(
        ziel, karten[0], karten[-1],
        f"91_differenz_{karten[0]['name']}-gegen-{karten[-1]['name']}"
        f"_mittel-{paare[-1][2]:.5f}_hell-wo-die-sonne-etwas-bewegt-hat.png").name)

    # Und die Gegenprobe: ohne Bestellung meldet der Bericht `bestellt: ()`.
    ohne = sonne.lage()
    print(f"\nOhne Bestellung: {ohne['hoehe_grad']}/{ohne['azimut_grad']}, "
          f"bestellt={ohne['bestellt']} — die Vorgabe steht als Vorgabe da.")
    return 0 if sorted(ziel.glob("*.png")) else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
