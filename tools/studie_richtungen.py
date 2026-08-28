#!/usr/bin/env python3
"""Hängt die Messbarkeit am Kamerastandpunkt? — acht Richtungen, dieselbe Szene.

**Wozu es diese Studie gibt** (28.08.2026): Beim Umstellen der Kamera auf `shift` wurde
ein Test rot, und die Vermutung lag nahe, **frontale** Ansichten trügen zu wenig
Tiefensignal für eine Rangkorrelation. Das ist eine Aussage über die Metrik und liess sich
hier billig prüfen, statt sie drüben messen zu lassen.

**Die Vermutung war falsch, und das Gegenteil ist der Befund.** ρ trennt auf **jeder** der
acht Richtungen. Die Richtung ``s`` sieht ihre Fassade mit einer Tiefenspanne von nur
0,42 m und liefert trotzdem die besten guten Werte der frontalen Gruppe — *rangbasiert
heisst massstabsfrei*, und das ist hier zum ersten Mal belegt statt behauptet.

**Was stattdessen dasteht, ist schärfer:** Die **guten** Fälle liegen auf frontalen
Richtungen systematisch tiefer als auf diagonalen. Bei ``PAAR_RHO_SCHWELLE = 0.80`` fallen
dort **5 von 20** guten Fällen durch und diagonal **keiner**. Die Schwelle ist
richtungsabhängig — und darum trägt `auf-20260827-61` seit heute die Auflage, die Richtung
je Fall mitzuführen.

Die Fallkonstruktion kommt aus :mod:`tools.studie_paarmasse` — dieselben elf Fälle,
dieselben von Hand vergebenen Etiketten. Nur die Kamera wandert.

    python tools/studie_richtungen.py build/frontal

Auswertung: `docs/RICHTUNGEN_2026-08-28.md`.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from studie_paarmasse import HERZSCHLAG_S, HINTERGRUND_M, faelle   # noqa: E402
from aiimaging import bildlesen, geometrie_qa, seams               # noqa: E402
from aiimaging import maske as maske_modul                         # noqa: E402

#: Die vier Richtungen, die eine Fassade **frontal** treffen.
FRONTAL = ("n", "e", "s", "w")

#: Vier diagonale zum Vergleich — je eine aus jedem Quadranten.
DIAGONAL = ("nNE", "eES", "sSE", "wWN")

AUFLOESUNG = 192
SAMPLES = 6
SAAT = 20260828


def _bericht(glb: Path, kamera: str, wurzel: Path) -> dict:
    aus = wurzel / kamera
    datei = aus / "blender-report.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))
    return seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=AUFLOESUNG,
                                  samples=SAMPLES, kamera=kamera,
                                  herzschlag_takt_s=HERZSCHLAG_S)


def gruppe(kamera: str) -> str:
    return "frontal" if kamera in FRONTAL else "diagonal"


def auswertung(zeilen: list[dict], schwelle: float) -> dict:
    """Wie viele **gute** Fälle je Gruppe unter der Schwelle liegen — und die Lücke.

    *Gezählt werden die guten Fälle und nicht die schlechten: Ein Tor, das gute Bilder
    sperrt, kostet Renderzeit und Vertrauen; und genau dieser Fehler hängt hier an der
    Richtung.*
    """
    aus: dict = {}
    for name in ("frontal", "diagonal"):
        unter, alle, luecken = 0, 0, []
        for z in zeilen:
            if z["gruppe"] != name:
                continue
            gute = [v for _, (g, v) in z["werte"].items() if g and v is not None]
            schlecht = [v for _, (g, v) in z["werte"].items() if not g and v is not None]
            if gute and schlecht:
                luecken.append(min(gute) - max(schlecht))
            for _, (g, v) in z["werte"].items():
                if not g or v is None:
                    continue
                alle += 1
                unter += v < schwelle
        aus[name] = {"gute_unter_schwelle": unter, "gute_gesamt": alle,
                     "kleinste_luecke": min(luecken) if luecken else None,
                     "groesste_luecke": max(luecken) if luecken else None}
    return aus


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0]) if argv else Path("build/frontal")
    wurzel.mkdir(parents=True, exist_ok=True)

    glb = Path("build/studie/hochbau.glb")
    if not glb.exists():
        print(f"FEHLER: {glb} fehlt. Erst `python tools/studie_paarmasse.py build/studie` "
              f"laufen lassen — die Szene entsteht dort.", file=sys.stderr)
        return 2

    zeilen: list[dict] = []
    for kamera in FRONTAL + DIAGONAL:
        bericht = _bericht(glb, kamera, wurzel)
        soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
        maske = maske_modul.maske_aus_bericht(bericht, gelaende_erwartet=False).get("maske")
        if maske is None:
            print(f"!! {kamera}: keine Maske")
            continue
        innen = [w for w, m in zip(soll, maske) if m and w < HINTERGRUND_M]
        spanne = (max(innen) - min(innen)) if innen else 0.0

        # DIE SAAT WIRD JE RICHTUNG ZURUECKGESETZT. Sonst bekaeme die zweite Kamera
        # anderes Rauschen als die erste, und ein Unterschied zwischen zwei Richtungen
        # waere nicht mehr von einem Unterschied zwischen zwei Wuerfen zu trennen.
        wuerfel = random.Random(SAAT)
        werte = {}
        for art, gut, ist in faelle(soll, maske, breite, hoehe, wuerfel):
            rho = geometrie_qa.rho_ueber_maske(
                soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_TIEFE)
            werte[art] = (gut, rho.get("gerichtet"))

        zeilen.append({"kamera": kamera, "gruppe": gruppe(kamera), "spanne_m": spanne,
                       "n_maske": len(innen), "verschiedene_tiefen": len(set(innen)),
                       "werte": werte})
        print(f"{kamera:<6} {gruppe(kamera):<9} Spanne {spanne:7.3f} m  "
              f"Maskenpunkte {len(innen):6d}  verschiedene Tiefen {len(set(innen)):6d}")

    (wurzel / "roh.json").write_text(json.dumps(zeilen, indent=1), encoding="utf-8")

    satz = auswertung(zeilen, geometrie_qa.PAAR_RHO_SCHWELLE)
    print()
    for name, w in satz.items():
        print(f"{name:<9} gute Faelle unter {geometrie_qa.PAAR_RHO_SCHWELLE}: "
              f"{w['gute_unter_schwelle']} von {w['gute_gesamt']}   "
              f"Luecken {w['kleinste_luecke']:+.3f} bis {w['groesste_luecke']:+.3f}")
    print(f"\n{len(zeilen)} Richtungen -> {wurzel}/roh.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
