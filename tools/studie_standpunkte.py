#!/usr/bin/env python3
"""Was `guete_standpunkt` an einer Hüllbox wirklich unterscheidet — und was nicht.

**Wozu es diese Studie gibt** (01.09.2026): Die HomeStation hat den Kameraabstand
berichtigt — er war 24 bis 25 % zu gross, weil ``+ tiefe/2`` die seitlichen
Silhouettenkanten auf die Vorderkante setzte. In ihrer Meldung steht ein Folgeposten,
und er hatte keinen Adressaten:

    «Die Streuung von `flaechenanteil` über die zwölf Richtungen fällt am gedrungenen Bau
    von 2.3 auf 1.17 — ein grosser Teil der alten Spanne WAR der Abstandsfehler. Das
    schwächt `guete_standpunkt` bei kompakten Bauten, und das ist ein Folgeposten.»

Diese Studie misst nach, und sie braucht **weder GPU noch Blender**: `kamerasatz` rechnet
aus einer Hüllbox, sonst nichts. Die Formen sind erfundene Kantenlängen — keine echten
Bauten, kein Projekt, kein Ort (Regel 3).

    python tools/studie_standpunkte.py

Ergebnis und Auswertung: `docs/STANDPUNKTE_2026-09-01.md`.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import kameras                                    # noqa: E402

#: Sechs Formen, von würfelig bis langgestreckt. Die Zahlen sind gesetzt und beschreiben
#: **Verhältnisse**, nicht Gebäude: Was hier gemessen wird, hängt am Grundriss-Verhältnis
#: und nicht am Massstab.
FORMEN: tuple[tuple[str, tuple[float, float, float]], ...] = (
    ("wuerfel", (20.0, 20.0, 20.0)),
    ("gedrungen", (30.0, 25.0, 18.0)),
    ("turm", (20.0, 18.0, 45.0)),
    ("flachbau", (40.0, 30.0, 6.0)),
    ("riegel", (60.0, 12.0, 15.0)),
    ("langriegel", (103.84, 57.15, 27.10)),
)


def _bewertet(masse):
    """Je Richtung der Güteblock — dieselbe Rechnung wie in :func:`kameras.standpunkte`."""
    dx, dy, dz = masse
    satz = kameras.kamerasatz([[0.0, 0.0, 0.0], [dx, dy, dz]])
    kams = satz["kameras"]
    bester = max(k.get("flaechenanteil") or 0.0 for k in kams)
    return kams, {k["kuerzel"]: kameras.guete_standpunkt(
        k, masse, bester_flaechenanteil=bester) for k in kams}


def messe(name: str, masse) -> dict:
    """Eine Form: Spanne des Flächenanteils, Zahl der Güteklassen, Gleichstand."""
    dx, dy, dz = masse
    kams, guete = _bewertet(masse)
    anteile = [k.get("flaechenanteil") or 0.0 for k in kams]
    tauglich = [k for k in kams if guete[k["kuerzel"]]["taugt"]]

    # WIE VIELE VERSCHIEDENE GUETEWERTE ES UEBERHAUPT GIBT. Das ist die Zahl, die zaehlt:
    # Eine Rangfolge ueber acht Standpunkte, die nur zwei Werte kennt, ordnet nicht acht
    # Dinge, sondern teilt sie in zwei Haufen.
    klassen = sorted({round(guete[k["kuerzel"]]["guete"], kameras.GLEICHSTAND_STELLEN)
                      for k in tauglich}, reverse=True)

    aus = kameras.standpunkte([[0.0, 0.0, 0.0], [dx, dy, dz]])

    # DIE ENTSCHEIDENDE GEGENPROBE: Waehlt dieselbe Rechnung dasselbe, wenn der
    # Flaechenanteil ueberall gleich ist? Dann traegt er die Auswahl nicht.
    flach = [dict(k, flaechenanteil=0.2) for k in kams]
    flach_guete = {k["kuerzel"]: kameras.guete_standpunkt(
        k, masse, bester_flaechenanteil=0.2) for k in flach}
    besser = max((g["guete"], kz) for kz, g in flach_guete.items() if g["taugt"])
    echt = max((guete[k["kuerzel"]]["guete"], k["kuerzel"]) for k in tauglich)

    return {
        "form": name, "masse": list(masse),
        "grundriss_verhaeltnis": round(max(dx, dy) / min(dx, dy), 3),
        "anteil_min": round(min(anteile), 4), "anteil_max": round(max(anteile), 4),
        "spanne": round(max(anteile) / min(anteile), 3) if min(anteile) > 0 else None,
        "n_tauglich": len(tauglich),
        "n_gueteklassen": len(klassen),
        "gueteklassen": [round(w, 4) for w in klassen],
        "n_gleichstand": aus["n_gleichstand"],
        "n_kombinationen": aus["n_kombinationen"],
        "gewaehlt": [k["kuerzel"] for k in aus["standpunkte"]],
        "bester_echt": echt[1],
        "bester_ohne_flaechenanteil": besser[1],
        "flaechenanteil_entscheidet": echt[1] != besser[1],
    }


def main(argv=None) -> int:
    zeilen = [messe(name, masse) for name, masse in FORMEN]

    print(f"{'Form':<12} {'GR-Verh':>8} {'Spanne':>7} {'taugl':>6} {'Klassen':>8} "
          f"{'Gleichstand':>12}  bester   ohne Flaeche")
    for z in zeilen:
        print(f"{z['form']:<12} {z['grundriss_verhaeltnis']:>8.2f} {z['spanne']:>6.2f}x "
              f"{z['n_tauglich']:>6} {z['n_gueteklassen']:>8} "
              f"{z['n_gleichstand']:>4}/{z['n_kombinationen']:<7} "
              f"{z['bester_echt']:<8} {z['bester_ohne_flaechenanteil']}")

    entscheidet = sum(1 for z in zeilen if z["flaechenanteil_entscheidet"])
    print(f"\nDer Flaechenanteil entscheidet den besten Standpunkt in {entscheidet} von "
          f"{len(zeilen)} Formen.")
    print(f"Groesste Zahl von Gueteklassen ueber alle Formen: "
          f"{max(z['n_gueteklassen'] for z in zeilen)} — bei je "
          f"{zeilen[0]['n_tauglich']} tauglichen Standpunkten.")

    ziel = Path("build/standpunkte.json")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(zeilen, indent=1), encoding="utf-8")
    print(f"\n{len(zeilen)} Formen -> {ziel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
