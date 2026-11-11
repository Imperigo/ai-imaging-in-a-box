"""Messung von A0322 über den echten Aufrufweg, Kopf gegen Basis in getrennten Prozessen (von Hand, kein Prüflauf).

Schreibt die gezielte Reihe (:func:`fluegel_satz.zufallsfall_geschosse`) als glb in einen Ordner, lässt jede Fassung
(``--src`` zeigt auf ihr ``src``) ``lies_glb_umfeld`` und ihre Gruppierung rechnen (wie ``plane`` im Situationsmodell:
``grundriss_cluster`` der Bauwerk-Boxen, mit den Grundrissen, wo die Fassung sie kennt) und vergleicht mit der Wahrheit.

    python tests/grundriss_geschosse_messung.py schreibe ORDNER --anzahl 2000 --seed 32210
    python tests/grundriss_geschosse_messung.py gruppen ORDNER --src PFAD/src --name kopf
    python tests/grundriss_geschosse_messung.py vergleiche ORDNER --kopf kopf --basis basis

Regel 3: die Dateien sind frei erfunden und gehören nicht ins Repo.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent


def schreibe(ordner: Path, anzahl: int, seed: int) -> None:
    sys.path[:0] = [str(HIER), str(HIER.parent / "src")]
    from fluegel_glb import schreibe as glb
    from fluegel_satz import zufallsfall_geschosse
    rnd = random.Random(seed)
    ordner.mkdir(parents=True, exist_ok=True)
    wahr = []
    for n in range(anzahl):
        fall = zufallsfall_geschosse(rnd)
        glb(ordner / f"s{n:05d}.glb", fall["glb"])
        art = fall["glb"][0]
        wahr.append({"haus": fall["haus"], "name": fall["name"], "geschosse": (art[6] if len(art) > 6 else 1) or 1,
                     "auskragung": bool(len(art) > 7 and art[7]), "gedreht": bool(art[4]),
                     "verschachtelt": bool(len(art) > 8 and art[8]), "platte": fall["haus"][-1] is None})
    (ordner / "wahrheit.json").write_text(json.dumps(wahr))


def gruppen(ordner: Path, src: str, name: str) -> None:
    import time
    sys.path.insert(0, src)
    from aiimaging import umfeld
    wahr = json.loads((ordner / "wahrheit.json").read_text())
    aus = []
    for n in range(len(wahr)):
        gelesen = umfeld.lies_glb_umfeld(ordner / f"s{n:05d}.glb")
        g = gelesen.get("bauwerk_grundrisse")
        start = time.perf_counter()
        cl = umfeld.grundriss_cluster(gelesen["bauwerk_boxen"], grundrisse=g) if g is not None else \
            umfeld.grundriss_cluster(gelesen["bauwerk_boxen"])
        aus.append({"gruppen": sorted(sorted(c["teile"]) for c in cl),
                    "mehrdeutig": sum(bool(c.get("mehrdeutig")) for c in cl),
                    "bau": [bool(c["bau"]) for c in sorted(cl, key=lambda c: sorted(c["teile"]))],
                    "ohne_grundriss": None if g is None else sum(x is None for x in g),
                    "zeit": time.perf_counter() - start})
    (ordner / f"{name}.json").write_text(json.dumps(aus))


def _urteil(haus, gruppen, bau) -> dict:
    sys.path[:0] = [str(HIER)]
    from fluegel_satz import beurteile
    return beurteile({"haus": haus}, [{"teile": g, "bau": b, "art": "bau" if b else "anderes"} for g, b in zip(gruppen, bau)])


def vergleiche(ordner: Path, kopf: str, basis: str) -> None:
    sys.path[:0] = [str(HIER)]
    from fluegel_satz import schlechter
    wahr = json.loads((ordner / "wahrheit.json").read_text())
    k = json.loads((ordner / f"{kopf}.json").read_text())
    b = json.loads((ordner / f"{basis}.json").read_text())
    z = {"szenen": len(wahr), "kopf_richtig": 0, "basis_richtig": 0, "rueckschritte": 0, "rueckschritte_ohne_vermerk": 0,
         "verbesserungen": 0, "kopf_mit_vermerk": 0, "teile_ohne_grundriss": 0, "falsch_ohne_vermerk": 0}
    beispiele = []
    for n, (w, a, c) in enumerate(zip(wahr, k, b)):
        uk, ub = _urteil(w["haus"], a["gruppen"], a["bau"]), _urteil(w["haus"], c["gruppen"], c["bau"])
        z["kopf_richtig"] += uk["richtig"]
        z["basis_richtig"] += ub["richtig"]
        z["kopf_mit_vermerk"] += a["mehrdeutig"] > 0
        z["teile_ohne_grundriss"] += a["ohne_grundriss"] or 0
        if not uk["richtig"] and not a["mehrdeutig"]:
            z["falsch_ohne_vermerk"] += 1
        if schlechter(uk, ub):
            z["rueckschritte"] += 1
            z["rueckschritte_ohne_vermerk"] += a["mehrdeutig"] == 0
            if len(beispiele) < 5:
                beispiele.append((n, w["name"], uk["grund"]))
        elif uk["richtig"] and not ub["richtig"]:
            z["verbesserungen"] += 1
    for schl in ("geschosse", "auskragung", "gedreht", "verschachtelt", "platte"):
        z[f"mit_{schl}"] = sum(1 for w in wahr if (w[schl] > 1 if schl == "geschosse" else w[schl]))
    zeiten = sorted(x["zeit"] for x in k)
    z["zeit_median_s"] = round(zeiten[len(zeiten) // 2], 5)
    print(json.dumps(z, ensure_ascii=False))
    for bsp in beispiele:
        print("RUECKSCHRITT", bsp)


if __name__ == "__main__":                                     # pragma: no cover: Messung von Hand
    p = argparse.ArgumentParser()
    p.add_argument("was", choices=("schreibe", "gruppen", "vergleiche"))
    p.add_argument("ordner", type=Path)
    p.add_argument("--anzahl", type=int, default=2000)
    p.add_argument("--seed", type=int, default=32210)
    p.add_argument("--src")
    p.add_argument("--name")
    p.add_argument("--kopf", default="kopf")
    p.add_argument("--basis", default="basis")
    a = p.parse_args()
    if a.was == "schreibe":
        schreibe(a.ordner, a.anzahl, a.seed)
    elif a.was == "gruppen":
        gruppen(a.ordner, a.src, a.name)
    else:
        vergleiche(a.ordner, a.kopf, a.basis)
