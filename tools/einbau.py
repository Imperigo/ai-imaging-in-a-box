#!/usr/bin/env python3
"""EINBAU-STAND — was fehlt noch, und bei wem liegt es?

Die dünne Schicht über :mod:`aiimaging.einbau`. Sie rechnet nichts; sie zeigt.

**Wozu es sie gibt** (Owner-Auftrag 26.08.2026): Der Einbau in KosmoOrbit ist das Ziel,
nicht der Bau. Verantwortung für etwas, das anderswo geschieht, lässt sich nur führen,
wenn der Rückstand zählbar ist — und was von Hand gezählt wird, wird irgendwann nicht mehr
gezählt.

    python tools/einbau.py              # der Stand in einem Blick
    python tools/einbau.py --json       # dasselbe für ein Werkzeug
    python tools/einbau.py --worker ui  # nur ein Adressat

Rückgabewert **1** in zwei Fällen — beides Zustände, für die ich hafte, und beide sollen
ein Skript scheitern lassen können:

1. **Ein offener Posten hat keinen Adressaten.** Er wird nie eingebaut, und es fällt
   niemandem auf.
2. **Eine erledigte Zeile sagt nicht, worauf ihr Beleg ruht** — im Repo oder am Gerät.
   Seit dem 27.08.2026, nachdem `B8` sechs Tage als erledigt geführt worden war, während
   auf dem Gerät eine Fassung vom 20.08. lief. *Eine Datei im Repo belegt, was jemand
   geschrieben hat, nicht was auf dem Gerät läuft.*

Ein blosser Rückstand ist **kein** Fehler: Ein Auftrag, der bei einem Worker liegt, ist
verteilt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aiimaging import einbau  # noqa: E402


def _zeilen(bericht: dict, nur: str | None) -> list[str]:
    aus: list[str] = []
    r = bericht["rueckstand"]
    aus.append(f"RUECKSTAND: {r['n']} Auftraege ohne Antwort"
               + (f", aeltester {r['aelteste_tage']} Tage" if r["aelteste_tage"] is not None
                  else ""))
    for worker, anzahl in r["je_worker"].items():
        if nur and worker != nur:
            continue
        aus.append(f"  {worker:<6} {anzahl}")
        for e in r["eintraege"]:
            if e["worker"] != worker:
                continue
            alter = "?" if e["tage"] is None else f"{e['tage']}d"
            aus.append(f"      {e['auftrag_id']:<22} {alter:>4}  {e['beschreibung'][:70]}")
    aus.append("")
    offen = bericht["offene_posten"]
    aus.append(f"EINBAU-STAND: {len(offen)} von {bericht['n_posten']} Posten noch nicht "
               f"in der Software")
    for p in offen:
        aus.append(f"  {p['kennung']:<4} {p['zustand']:<30} {p['posten'][:60]}")
    aus.append("")
    if bericht["ohne_adressat"]:
        aus.append("OHNE ADRESSATEN — diese Posten treibt niemand:")
        for p in bericht["ohne_adressat"]:
            aus.append(f"  {p['kennung']:<4} {p['posten'][:70]}")
    else:
        aus.append("ADRESSATEN: vollstaendig — jeder offene Posten hat einen.")

    if bericht["ohne_geraetebeweis"]:
        aus.append("")
        aus.append("ERLEDIGT, ABER OHNE ANGABE, WORAUF DER BELEG RUHT:")
        for p in bericht["ohne_geraetebeweis"]:
            aus.append(f"  {p['kennung']:<4} {p['mangel']:<24} {p['posten'][:44]}")
            aus.append(f"       {p['grund'][:100]}")
    else:
        aus.append("BELEGE: jede erledigte Zeile sagt, ob sie im Repo oder am Geraet ruht.")
    return aus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=".", help="Wurzel des Repos (Vorgabe: hier)")
    ap.add_argument("--json", action="store_true", help="maschinenlesbar ausgeben")
    ap.add_argument("--worker", choices=("local", "cloud", "ui"),
                    help="nur den Rueckstand eines Adressaten zeigen")
    a = ap.parse_args(argv)

    bericht = einbau.bericht(a.repo)
    if a.json:
        print(json.dumps(bericht, ensure_ascii=False, indent=1))
    else:
        print("\n".join(_zeilen(bericht, a.worker)))
    return 0 if bericht["bereit"] else 1


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
