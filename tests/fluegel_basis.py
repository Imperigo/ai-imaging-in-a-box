"""Die Gruppierung der Grundrisse, wie sie VOR A0301 war (Stand ``fab/visbox/int-0376``, 1781a25a8).

**Wozu:** Runde 2 von A0301 verlangt, dass kein Fall schlechter wird als an der Basis. Das lässt sich nur
messen, wenn die Basis neben der neuen Regel läuft. Diese Datei ist die wörtliche Abschrift der alten
Funktion; sie ruft dieselben Schwellen und Helfer aus ``aiimaging.umfeld`` (die A0301 nicht ändert).
Sie ist Messmittel der Proben, kein Teil des Produkts.
"""
from __future__ import annotations

from aiimaging.umfeld import (BAU_MAX_FLAECHE_M2, BAU_MIN_HOEHE_M, CLUSTER_LUECKE_M, _art_des_clusters,
                              _ueberlappt)


def basis_cluster(boxen, *, luecke_m: float = CLUSTER_LUECKE_M,
                  bau_min_hoehe_m: float = BAU_MIN_HOEHE_M) -> list[dict]:
    """``grundriss_cluster`` vor A0301: Überlappung bindet; ein Cluster aus mehreren Teilen über
    ``BAU_MAX_FLAECHE_M2`` wird ganz in seine Stapel (gleicher Grundriss) zerlegt."""
    b3 = []
    for b in boxen:
        lo, hi = b
        z0 = float(lo[2]) if len(lo) > 2 else 0.0
        z1 = float(hi[2]) if len(hi) > 2 else z0 + bau_min_hoehe_m
        b3.append(((float(lo[0]), float(lo[1]), z0), (float(hi[0]), float(hi[1]), z1)))
    eltern = list(range(len(b3)))

    def wurzel(i):
        while eltern[i] != i:
            eltern[i] = eltern[eltern[i]]
            i = eltern[i]
        return i
    reihen = sorted(range(len(b3)), key=lambda i: b3[i][0][0])
    for k, i in enumerate(reihen):                         # Sweep über x
        for j in reihen[k + 1:]:
            if b3[j][0][0] > b3[i][1][0] + luecke_m:
                break
            if _ueberlappt(((b3[i][0][0], b3[i][0][1]), (b3[i][1][0], b3[i][1][1])),
                           ((b3[j][0][0], b3[j][0][1]), (b3[j][1][0], b3[j][1][1])), rand=luecke_m):
                eltern[wurzel(i)] = wurzel(j)
    gruppen: dict = {}
    for i in range(len(b3)):
        gruppen.setdefault(wurzel(i), []).append(i)

    def eintrag(teile):
        lo = [min(b3[i][0][a] for i in teile) for a in range(3)]
        hi = [max(b3[i][1][a] for i in teile) for a in range(3)]
        hoehe = hi[2] - lo[2]
        flaeche = (hi[0] - lo[0]) * (hi[1] - lo[1])
        art = _art_des_clusters(hoehe, flaeche, bau_min_hoehe_m)
        return {"box": ((lo[0], lo[1]), (hi[0], hi[1])), "hoehe_m": round(hoehe, 2),
                "flaeche_m2": round(flaeche, 1), "art": art, "bau": art == "bau",
                "teile": sorted(teile)}
    aus = []
    for teile in gruppen.values():
        ganz = eintrag(teile)
        if len(teile) > 1 and ganz["flaeche_m2"] > BAU_MAX_FLAECHE_M2:
            stapel: dict = {}
            for i in teile:
                stapel.setdefault(tuple(round(b3[i][k][a] * 2) / 2 for k in (0, 1) for a in (0, 1)),
                                  []).append(i)
            aus.extend(eintrag(t) for t in stapel.values())
        else:
            aus.append(ganz)
    aus.sort(key=lambda c: (not c["bau"], -c["flaeche_m2"], c["box"]))
    return aus
