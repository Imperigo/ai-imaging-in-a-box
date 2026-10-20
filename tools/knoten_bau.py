"""Den Bau der Knotenansicht erneuern und stempeln (14.10.2026).

**Anlass:** Der Bau (`kosmovis/apps/visbox-knoten/dist/`) war bis zum 14.10.2026 vom Repo
ausgeschlossen. Die HomeStation lieferte darum den Bau vom 24.09.2026 aus, während die Quelle
längst weiter war — der Owner sah am Mac noch die alten Knoten. Seither ist der Bau
**eingecheckt**: Ein `git pull` am Heim-PC bringt ihn mit, ohne dass dort jemand baut.

Damit Bau und Quelle nicht wieder auseinanderlaufen, schreibt dieses Werkzeug nach dem Bau
``dist/BAUSTAND.json`` mit dem Fingerabdruck der Quelle (``kosmovis/HERKUNFT.json`` und der
Visbox-eigenen Wirtsdateien). ``tests/test_knoten_bau.py`` fällt, sobald die Quelle sich ändert
und der Bau nicht neu gestempelt ist.

Gebrauch::

    python3 tools/knoten_bau.py            # npm ci (falls nötig), npm run build, stempeln
    python3 tools/knoten_bau.py --stempel  # nur stempeln (nach einem Bau von Hand)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
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
           "kosmovis/apps/visbox-knoten/src/visbox.css", "kosmovis/apps/visbox-knoten/index.html",
           "kosmovis/apps/visbox-knoten/vite.config.ts")


def fingerabdruck(wurzel: Path = WURZEL) -> dict[str, str]:
    return {q: hashlib.sha256((wurzel / q).read_bytes()).hexdigest() for q in QUELLEN}


def stempele() -> None:
    STEMPEL.write_text(json.dumps({"quelle": fingerabdruck()}, indent=1, sort_keys=True) + "\n",
                       encoding="utf-8")


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
    args = a.parse_args(argv)
    if not args.stempel:
        if braucht_npm_ci():
            subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=KOSMOVIS, check=True)
        subprocess.run(["npm", "run", "build"], cwd=APP, check=True)
        # KI-BEDIENUNG STUFE 3: die Werkzeugliste der Knotenansicht in den Bau, damit die
        # Mac-App sie Claude nennen kann, bevor die Knotenansicht offen ist. `vite build` leert
        # dist/ — darum danach, geschrieben von der Probe, die sie sonst gegen die Quelle prueft.
        subprocess.run(["npx", "vitest", "run", "test/ki-werkzeugliste.test.ts"], cwd=APP,
                       check=True, env={**os.environ, "VISBOX_KI_LISTE_SCHREIBEN": "1"})
    stempele()
    print(f"Bau gestempelt: {STEMPEL.relative_to(WURZEL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
