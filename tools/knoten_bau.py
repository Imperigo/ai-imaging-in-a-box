"""Den Bau der Knotenansicht erneuern und stempeln (14.10.2026).

**Anlass:** Der Bau (`kosmovis/apps/visbox-knoten/dist/`) war bis zum 14.10.2026 vom Repo
ausgeschlossen. Die HomeStation lieferte darum den Bau vom 24.09.2026 aus, während die Quelle
längst weiter war — der Owner sah am Mac noch die alten Knoten. Seither ist der Bau
**eingecheckt**: Ein `git pull` am Heim-PC bringt ihn mit, ohne dass dort jemand baut.

Damit Bau und Quelle nicht wieder auseinanderlaufen, schreibt dieses Werkzeug nach dem Bau
``dist/BAUSTAND.json`` mit dem Fingerabdruck der Quelle (``kosmovis/HERKUNFT.json`` und der
Visbox-eigenen Wirtsdateien). ``tests/test_knoten_bau.py`` fällt, sobald die Quelle sich ändert
und der Bau nicht neu gestempelt ist.

**Vor dem Bau wird geprüft** (Plan UI-Gleichheit S5, 21.10.2026): zuerst die Kopie gegen ihren
Abdruck (``kosmovis_uebernahme.pruefe``, dasselbe wie ``--pruefen``) — ein Befund bricht ab. Ist
``KOSMO_ORBIT`` gesetzt (Pfad zu ``kosmo-orbit/`` in einem Klon), dann auch gegen den aktuellen
Integrator-Stand (``--abgleich``); eine Abweichung bricht ebenfalls ab. Wer bewusst gegen den
festgehaltenen Stand der Kopie bauen will (etwa, weil drüben gerade etwas Halbes liegt), gibt
``--fester-stand`` — der Stempel vermerkt dann, gegen welchen Stand gebaut wurde und wie viele
Abweichungen offen waren. *Ein Bau, der still auf einem alten Stand entsteht, sieht am Mac genauso
aus wie ein aktueller.*

Gebrauch::

    python3 tools/knoten_bau.py                 # prüfen, npm ci (falls nötig), bauen, stempeln
    python3 tools/knoten_bau.py --fester-stand  # trotz Abweichung zum Integrator bauen (vermerkt)
    python3 tools/knoten_bau.py --stempel       # nur stempeln (nach einem Bau von Hand)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import importlib.util
import subprocess
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KOSMOVIS = WURZEL / "kosmovis"
APP = KOSMOVIS / "apps" / "visbox-knoten"
BAU = APP / "dist"
STEMPEL = BAU / "BAUSTAND.json"

#: Was den Bau bestimmt und nicht schon in HERKUNFT.json steht.
QUELLEN = ("kosmovis/HERKUNFT.json", "kosmovis/package-lock.json",
           "kosmovis/apps/visbox-knoten/src/main.tsx", "kosmovis/apps/visbox-knoten/src/mappe.ts",
           "kosmovis/apps/visbox-knoten/src/ki-wirt.ts",
           # Kopfteile (Plan UI-Gleichheit S1/S2, 20.10.2026) — und die beiden Wirtsdateien, die
           # bis dahin fehlten, obwohl sie mitgebaut werden.
           "kosmovis/apps/visbox-knoten/src/kopf.tsx", "kosmovis/apps/visbox-knoten/src/wirt-bruecke.ts",
           "kosmovis/apps/visbox-knoten/src/thema.ts", "kosmovis/apps/visbox-knoten/src/graph-sichern.ts",
           "kosmovis/apps/visbox-knoten/src/kurztasten.ts",
           # S3/S4 (20.10.2026): die Einstellungs-Insel des Wirts.
           "kosmovis/apps/visbox-knoten/src/einstellungen.tsx",
           "kosmovis/apps/visbox-knoten/src/visbox.css", "kosmovis/apps/visbox-knoten/index.html",
           "kosmovis/apps/visbox-knoten/vite.config.ts")


def _stellvertreter(wurzel: Path) -> list[str]:
    """Die Stellvertreter der Kopie (``HERKUNFT.json``) — sie werden mitgebaut, stehen in
    ``HERKUNFT.json`` aber nur mit ihrem Grund, nicht mit einem Abdruck. Ohne sie bliebe eine
    Aenderung an einem Stellvertreter (S3: das Gespraechsfeld) vom Stempel unbemerkt."""
    herkunft = json.loads((wurzel / "kosmovis" / "HERKUNFT.json").read_text(encoding="utf-8"))
    return sorted(f"kosmovis/{p}" for p in herkunft.get("stellvertreter", {}))


def fingerabdruck(wurzel: Path = WURZEL) -> dict[str, str]:
    return {q: hashlib.sha256((wurzel / q).read_bytes()).hexdigest()
            for q in (*QUELLEN, *_stellvertreter(wurzel))}


def stempele(abgleich: dict | None = None) -> None:
    """Schreibt den Stempel. Ohne ``abgleich`` (``--stempel``) bleibt der Vermerk des letzten
    Baus stehen — gestempelt wird dann nur die Quelle neu."""
    if abgleich is None and STEMPEL.is_file():
        abgleich = json.loads(STEMPEL.read_text(encoding="utf-8")).get("abgleich")
    inhalt = {"quelle": fingerabdruck()}
    if abgleich is not None:
        inhalt["abgleich"] = abgleich
    STEMPEL.write_text(json.dumps(inhalt, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                       encoding="utf-8")


def _uebernahme():
    spec = importlib.util.spec_from_file_location(
        "kosmovis_uebernahme_bau", WURZEL / "tools" / "kosmovis_uebernahme.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


class BauAbbruch(SystemExit):
    """Der Bau beginnt nicht — mit dem Grund als Text."""


def vor_dem_bau(fester_stand: bool = False, kosmo_orbit: str | None = None) -> dict:
    """Prüft die Kopie, bevor gebaut wird, und gibt den Vermerk für den Stempel zurück.

    1. ``pruefe()``: Jede wörtliche Kopie stimmt mit ihrem Abdruck, keine Datei ohne Herkunft.
       Ein Befund bricht immer ab — dagegen hilft kein Schalter, sondern ``geaendert`` mit Grund.
    2. Ist ``kosmo_orbit`` gegeben (Vorgabe: Umgebung ``KOSMO_ORBIT``): der Abgleich gegen den
       Integrator-Stand. Eine Abweichung bricht ab, ausser mit ``fester_stand``."""
    ue = _uebernahme()
    befunde = ue.pruefe()
    if befunde:
        raise BauAbbruch("Bau abgebrochen — die Kopie stimmt nicht mit ihrem Abdruck:\n  "
                         + "\n  ".join(befunde))
    fest = json.loads(ue.HERKUNFT.read_text(encoding="utf-8"))["quelle"]["commit"]
    pfad = os.environ.get("KOSMO_ORBIT") if kosmo_orbit is None else kosmo_orbit
    if not pfad:
        return {"ergebnis": "nicht abgeglichen (KOSMO_ORBIT nicht gesetzt)", "fester_stand": fest}
    bericht = ue.abgleich(Path(pfad))
    n = ue.abgleich_befunde(bericht)
    vermerk = {"ref": bericht["ref"], "commit": bericht["commit"], "fester_stand": fest,
               "abweichungen": n, "eigener_zweig": len(bericht["eigen"])}
    if not n:
        return {**vermerk, "ergebnis": "gleich"}
    ue.drucke_abgleich(bericht)
    if not fester_stand:
        raise BauAbbruch(f"Bau abgebrochen — {n} Abweichungen gegen {bericht['ref']}. Kopie "
                         "nachziehen (tools/kosmovis_uebernahme.py) oder bewusst mit "
                         "--fester-stand bauen.")
    return {**vermerk, "ergebnis": "abweichend, bewusst gegen den festen Stand gebaut"}


def braucht_npm_ci(kosmovis: Path | None = None) -> bool:
    """Ob ``npm ci`` vor dem Bau nötig ist: ohne ``node_modules`` — oder wenn das Lockfile
    neuer ist als ``node_modules`` (HomeStation, auf-20261015-286: nach einem Nachzug, der ein
    neues Paket wie ``@kosmo/data`` brachte, scheiterte der Bau an der alten Einrichtung)."""
    wurzel = KOSMOVIS if kosmovis is None else Path(kosmovis)
    module = wurzel / "node_modules"
    lock = wurzel / "package-lock.json"
    if not module.is_dir():
        return True
    if not lock.is_file():
        return False
    # npm schreibt bei jedem ci/install diese Datei neu; sie ist der Stand der Einrichtung.
    stand = module / ".package-lock.json"
    bezug = stand if stand.is_file() else module
    return lock.stat().st_mtime > bezug.stat().st_mtime


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--stempel", action="store_true", help="nur stempeln, nicht bauen")
    a.add_argument("--fester-stand", action="store_true",
                   help="trotz Abweichung zum Integrator-Stand bauen (im Stempel vermerkt)")
    args = a.parse_args(argv)
    vermerk = None
    if not args.stempel:
        vermerk = vor_dem_bau(args.fester_stand)
        if braucht_npm_ci():
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=KOSMOVIS, check=True)
        subprocess.run(["npm", "run", "build"], cwd=APP, check=True)
        # KI-BEDIENUNG STUFE 3: die Werkzeugliste der Knotenansicht in den Bau, damit die
        # Mac-App sie Claude nennen kann, bevor die Knotenansicht offen ist. `vite build` leert
        # dist/ — darum danach, geschrieben von der Probe, die sie sonst gegen die Quelle prueft.
        subprocess.run(["npx", "vitest", "run", "test/ki-werkzeugliste.test.ts"], cwd=APP,
                       check=True, env={**os.environ, "VISBOX_KI_LISTE_SCHREIBEN": "1"})
    stempele(vermerk)
    print(f"Bau gestempelt: {STEMPEL.relative_to(WURZEL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
