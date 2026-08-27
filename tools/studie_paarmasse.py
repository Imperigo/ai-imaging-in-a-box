#!/usr/bin/env python3
"""OBERGRENZE der Paarmasse — können sie überhaupt trennen, mit perfekten Karten?

**Wozu es diese Studie gibt** (27.08.2026, vor `auf-20260827-61`): Die Kalibrierung der
beiden Paarschwellen kostet drüben GPU-Zeit. Vorher ist eine billigere Frage zu klären —
*trennen die beiden Masse im Prinzip?* Denn was mit **perfekten** Karten nicht trennt,
trennt mit einem echten Tiefenschätzer erst recht nicht.

**Die Ist-Karten sind hier gebaut, nicht geschätzt.** Der Fehler des Schätzers kommt gar
nicht vor. Das Ergebnis ist damit eine **Obergrenze**: Was hier trennt, ist noch nicht
bestätigt; was hier nicht trennt, ist erledigt.

**Die Etiketten sind von Hand vergeben** und nicht aus einer Störungsstärke abgeleitet —
darin unterscheidet sich diese Studie von `schwellenstudie`, und darum wird sie mit
:func:`aiimaging.paarschwellen.trennkurve` ausgewertet und nicht mit
`trennschaerfe_kurve`.

    python tools/studie_paarmasse.py build/studie
    python tools/paarschwellen.py build/studie/f_rho.json
    python tools/paarschwellen.py build/studie/f_kante.json --groesse kantenanteil

Ergebnis und Auswertung: `docs/PAARSCHWELLEN_OBERGRENZE_2026-08-27.md`.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_test_ifc import erzeuge_ifc                        # noqa: E402
from aiimaging import bildlesen, geometrie_qa, seams         # noqa: E402
from aiimaging import maske as maske_modul                   # noqa: E402

#: Hintergrundmarke der Soll-Karten aus der EXR. Sie ist **kein Messwert** — Punkte
#: darauf sind «nichts dahinter» und dürfen in keine Mittelung eingehen.
HINTERGRUND_M = 1.0e10

AUFLOESUNG = 256
SAMPLES = 8

#: Der Herzschlagtakt ist hier **grösser als die Vorgabe** (2 s), und das ist eine
#: Eigenschaft DIESER Umgebung und keine Empfehlung: Läuft die Sammlung neben einem
#: Blender-Lauf, verhungert der Herzschlagfaden und die Wache meldet einen Stillstand,
#: den es nicht gibt. Auf der HomeStation ist die längste gemessene Lücke 2,10 s.
HERZSCHLAG_S = 12.0

SZENEN = (
    ("quader", {}, False),
    ("hochbau", {"hochbau": True}, False),
    ("gelaende4x", {"mit_gelaende": True, "gelaende_vielfaches": 4.0}, True),
)
KAMERAS = ("sSE", "nNW")

SAAT = 20260827


# ======================================================================================
# Die Szenen
# ======================================================================================

def _bericht(name: str, kw: dict, mit_gelaende: bool, kamera: str, wurzel: Path) -> dict:
    """Multipass für eine Szene und eine Kamera — mit Zwischenspeicher über den Pfad."""
    ifc = wurzel / f"{name}.ifc"
    glb = wurzel / f"{name}.glb"
    if not glb.exists():
        erzeuge_ifc(ifc, schema="IFC4", **kw)
        seams.ifc_zu_glb(ifc, glb)

    aus = wurzel / f"{name}_{kamera}"
    datei = aus / "blender-report.json"
    if datei.exists():
        return json.loads(datei.read_text(encoding="utf-8"))

    zusatz = {}
    if mit_gelaende:
        # OHNE die Bauwerksbox schrumpft der Bau zum Fleck und der Boden wird ein
        # Horizontstreifen. Am 26.08.2026 dreimal falsch gemacht, bevor es stimmte —
        # darum steht hier ein Vorlauf in 64 Punkten statt einer Faustregel.
        vor = seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=64, samples=1,
                                     kamera=kamera, herzschlag_takt_s=HERZSCHLAG_S)
        if vor.get("bbox_bauwerk"):
            zusatz["kamera_huellbox"] = vor["bbox_bauwerk"]
    return seams.glb_zu_multipass(glb, aus, up_axis="Y", aufloesung=AUFLOESUNG,
                                  samples=SAMPLES, kamera=kamera,
                                  herzschlag_takt_s=HERZSCHLAG_S, **zusatz)


# ======================================================================================
# Die Fälle — `gut` ist VON HAND vergeben
# ======================================================================================

def _boden_statt_bauwerk(soll, maske, breite, hoehe):
    """Was an der Stelle des Bauwerks stünde, wenn es nicht da wäre.

    Zeilenweise das Mittel des **endlichen** Hintergrunds. Steht in einer Zeile gar kein
    endlicher Hintergrund — eine Szene ohne Gelände —, bleibt die Hintergrundmarke stehen.
    Dann hat die Maske hinterher keine Rangfolge mehr, und ρ ist `None`: **nicht messbar**,
    nicht null. Genau dieser Befund ist Kapitel 3 der Auswertung.
    """
    aus = list(soll)
    for y in range(hoehe):
        zeile = [soll[y * breite + x] for x in range(breite)
                 if not maske[y * breite + x] and soll[y * breite + x] < HINTERGRUND_M]
        ersatz = sum(zeile) / len(zeile) if zeile else HINTERGRUND_M
        for x in range(breite):
            if maske[y * breite + x]:
                aus[y * breite + x] = ersatz
    return aus


def _versetzt(soll, breite, hoehe, dx):
    aus = [HINTERGRUND_M] * (breite * hoehe)
    for y in range(hoehe):
        for x in range(breite):
            quelle = x - dx
            if 0 <= quelle < breite:
                aus[y * breite + x] = soll[y * breite + quelle]
    return aus


def _gedreht(soll, breite, hoehe):
    """Um 90 Grad gedreht, auf dieselbe Grösse beschnitten."""
    aus = [HINTERGRUND_M] * (breite * hoehe)
    for y in range(hoehe):
        for x in range(breite):
            if x < hoehe and y < breite:
                aus[y * breite + x] = soll[x * breite + y]
    return aus


def _geglaettet(karte, breite, hoehe):
    aus = list(karte)
    for y in range(1, hoehe - 1):
        for x in range(1, breite - 1):
            summe = 0.0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    summe += karte[(y + dy) * breite + x + dx]
            aus[y * breite + x] = summe / 9.0
    return aus


def faelle(soll, maske, breite, hoehe, wuerfel):
    """Elf Fälle, fünf gute und sechs schlechte. Die Etiketten sind eine Setzung."""
    endlich = [w for w in soll if w < HINTERGRUND_M]
    spanne = (max(endlich) - min(endlich)) if endlich else 1.0
    sigma = 0.01 * (spanne or 1.0)
    mitte = sum(endlich) / len(endlich) if endlich else 0.0
    return [
        # ---- GUT: das würde jeder durchgehen lassen ---------------------------------
        ("treu", True, list(soll)),
        ("skala", True, [3.0 * w + 7.0 if w < HINTERGRUND_M else w for w in soll]),
        ("rausch_leicht", True,
         [w + wuerfel.gauss(0, sigma) if w < HINTERGRUND_M else w for w in soll]),
        ("glatt_leicht", True, _geglaettet(soll, breite, hoehe)),
        ("versatz_1px", True, _versetzt(soll, breite, hoehe, 1)),
        # ---- SCHLECHT: das würde niemand durchgehen lassen --------------------------
        ("bauwerk_weg", False, _boden_statt_bauwerk(soll, maske, breite, hoehe)),
        ("versatz_20px", False, _versetzt(soll, breite, hoehe, 20)),
        ("gedreht_90", False, _gedreht(soll, breite, hoehe)),
        ("rauschen", False, [wuerfel.random() for _ in soll]),
        ("flach", False, [1.0] * len(soll)),
        # Der Umriss bleibt vollkommen, die Tiefen INNEN sind gespiegelt. Der Fall, an
        # dem der Kantenanteil scheitert: Anteil 1,0000 bei ρ −1,0000.
        ("innen_vertauscht", False,
         [(2 * mitte - w) if (m and w < HINTERGRUND_M) else w
          for w, m in zip(soll, maske)]),
    ]


# ======================================================================================
# Der Lauf
# ======================================================================================

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    wurzel = Path(argv[0]) if argv else Path("build/studie")
    wurzel.mkdir(parents=True, exist_ok=True)
    wuerfel = random.Random(SAAT)

    zeilen: list[dict] = []
    for name, kw, mit_gelaende in SZENEN:
        for kamera in KAMERAS:
            bericht = _bericht(name, kw, mit_gelaende, kamera, wurzel)
            soll, breite, hoehe = bildlesen.tiefen_aus_report(bericht)
            gebaut = maske_modul.maske_aus_bericht(bericht,
                                                   gelaende_erwartet=mit_gelaende)
            maske = gebaut.get("maske")
            if maske is None:
                print(f"!! {name}/{kamera}: keine Maske — {gebaut.get('grund')}")
                continue
            n_maske = sum(1 for x in maske if x)
            n_boden = sum(1 for w, m in zip(soll, maske)
                          if (not m) and w < HINTERGRUND_M)
            print(f"{name}/{kamera}: {breite}x{hoehe}  "
                  f"Geometrieanteil {n_maske / len(maske):.4f}  "
                  f"Bodenanteil {n_boden / len(maske):.4f}")

            for art, gut, ist in faelle(soll, maske, breite, hoehe, wuerfel):
                rho = geometrie_qa.rho_ueber_maske(
                    soll, ist, maske, polaritaet=geometrie_qa.POLARITAET_TIEFE)
                anteil = geometrie_qa.anteil_grenze_mit_kante(ist, maske, breite=breite)
                zeilen.append({
                    "fall_id": f"{name}-{kamera}-{art}", "gut": gut,
                    "szene": name, "kamera": kamera, "art": art,
                    "rho": rho.get("gerichtet"),
                    "kantenanteil": anteil.get("anteil"),
                    "bodenanteil": round(n_boden / len(maske), 4),
                    "geometrieanteil": round(n_maske / len(maske), 4),
                })

    (wurzel / "roh.json").write_text(json.dumps(zeilen, indent=1), encoding="utf-8")
    for kurz, schluessel in (("rho", "rho"), ("kante", "kantenanteil")):
        satz = [{"fall_id": z["fall_id"], "gut": z["gut"], "wert": z[schluessel],
                 "szene": z["szene"], "kamera": z["kamera"]} for z in zeilen]
        (wurzel / f"f_{kurz}.json").write_text(json.dumps(satz, indent=1),
                                               encoding="utf-8")
    print(f"\n{len(zeilen)} Zeilen -> {wurzel}/roh.json, f_rho.json, f_kante.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
