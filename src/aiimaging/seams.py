"""Die Prozessgrenzen: Aufrufe an IfcOpenShell und Blender.

Dieses Modul ist die einzige Stelle, an der das Produkt fremde Programme startet — und
es startet sie **immer** als eigenständige Prozesse, nie als Import.

Warum das so gebaut ist
-----------------------
* **Blender** (GPL-2.0-or-later) → `blender --background --python <runner>` (Regel 2)
* **IfcOpenShell** (LGPL-3.0-or-later, Wheel enthält GPL-lizenziertes CGAL) → eigenes
  venv, eigener Prozess (LGPL-Präzisierung zu Regel 1)

Beides ist GPL-rechtlich eine Aggregation: Die fremden Programme bleiben unter ihrer
Lizenz, der Code hier bleibt Apache-2.0. Die Verständigung läuft ausschliesslich über
Dateien und Prozess-Rückgabewerte.

Dieses Modul importiert weder `bpy` noch `ifcopenshell` — und darf es nie.

Test-Naht
---------
Jede Funktion nimmt ein optionales `_starte`, mit dem der Subprozessaufruf ersetzt
werden kann. Ohne das wären die Nahtstellen nur auf Rechnern prüfbar, auf denen Blender
installiert ist; mit ihm lässt sich die Aufrufkonstruktion überall testen.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from aiimaging.contracts import ContractError, needs_rotation

_RUNNER_DIR = Path(__file__).resolve().parent / "runners"

IFC_RUNNER = _RUNNER_DIR / "ifc_to_glb_runner.py"
BLENDER_RUNNER = _RUNNER_DIR / "blender_depth_stage.py"


class SeamError(RuntimeError):
    """Ein Subprozess ist fehlgeschlagen oder seine Voraussetzung fehlt."""


def _default_starte(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def finde_ifc_python() -> str:
    """Pfad zum Python des `.venv-ifc`.

    Reihenfolge: Umgebungsvariable, dann das venv im Projektwurzelverzeichnis. Bewusst
    **kein** Rückfall auf `sys.executable` — das wäre genau der Fehlgriff, den die
    Prozessgrenze verhindern soll: ifcopenshell (und damit GPL-CGAL) liefe dann im
    Produkt-Environment.
    """
    if (env := os.environ.get("AIIMAGING_IFC_PYTHON")):
        return env
    kandidat = Path(__file__).resolve().parents[2] / ".venv-ifc" / "bin" / "python"
    if kandidat.exists():
        return str(kandidat)
    raise SeamError(
        ".venv-ifc nicht gefunden. Anlegen mit:\n"
        "    python3 -m venv .venv-ifc && .venv-ifc/bin/pip install ifcopenshell trimesh numpy\n"
        "Oder AIIMAGING_IFC_PYTHON setzen. Ein Rückfall auf das Produkt-Python findet "
        "bewusst nicht statt — er würde GPL-Code in diesen Prozess holen."
    )


def finde_blender() -> str:
    """Pfad zum Blender-Binary (Umgebungsvariable, dann PATH, dann /opt/blender)."""
    if (env := os.environ.get("AIIMAGING_BLENDER")):
        return env
    if (gefunden := shutil.which("blender")):
        return gefunden
    if (opt := Path("/opt/blender/blender")).exists():
        return str(opt)
    raise SeamError(
        "Blender nicht gefunden. AIIMAGING_BLENDER setzen oder blender in den PATH legen."
    )


def ifc_zu_glb(ifc_path, glb_path, *, timeout: int = 300, _starte=None) -> dict:
    """IFC4 → glb (Y-up) über den Subprozess im `.venv-ifc`.

    Returns:
        Report des Runners mit `glb_path`, `up_axis`, `bbox`, `n_elements`, `n_triangles`.

    Raises:
        SeamError: venv fehlt, Subprozess scheitert oder liefert keinen lesbaren Report.
    """
    starte = _starte or _default_starte
    cmd = [finde_ifc_python(), str(IFC_RUNNER), str(ifc_path), str(glb_path)]

    ergebnis = starte(cmd, timeout)
    if ergebnis.returncode != 0:
        raise SeamError(
            f"IFC→glb fehlgeschlagen (Code {ergebnis.returncode}):\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[:800]}"
        )
    try:
        return json.loads(ergebnis.stdout)
    except json.JSONDecodeError as e:
        raise SeamError(f"Runner lieferte kein JSON: {e}\n{ergebnis.stdout[:400]}") from e


def glb_zu_tiefenkarte(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                       samples: int = 16, timeout: int = 900, _starte=None) -> dict:
    """glb → Cycles-Tiefenkarte über `blender --background`.

    `up_axis` ist **Pflicht**, kein Vorgabewert. Der Grund ist der Phase-0-Befund: Zwei
    Erzeuger im Ökosystem liefern beide ein Feld `glb_path`, aber mit unterschiedlicher
    Orientierung (KosmoDraw Z-up, KosmoVis Y-up). Ein Default wäre eine stille
    Verdrehung von Tiefenkarte, Kamera und späterer Geometrie-QA.

    Raises:
        ContractError: `up_axis` fehlt oder ist nicht deutbar.
        SeamError: Blender fehlt oder der Lauf scheitert.
    """
    starte = _starte or _default_starte
    drehen = needs_rotation(up_axis)          # wirft ContractError, wenn up_axis fehlt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        finde_blender(), "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        "--glb", str(glb_path), "--out", str(out_dir),
        "--aufloesung", str(aufloesung), "--samples", str(samples),
    ]
    if drehen:
        cmd.append("--rotiere-z-up")

    ergebnis = starte(cmd, timeout)
    bericht = out_dir / "blender-report.json"
    if not bericht.exists():
        raise SeamError(
            f"Blender schrieb keinen Report (Code {ergebnis.returncode}):\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1500:]}"
        )
    return json.loads(bericht.read_text(encoding="utf-8"))


def baue_kommando_tiefenkarte(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                              samples: int = 16) -> list[str]:
    """Nur das Blender-Kommando bauen, ohne es auszuführen.

    Für Tests und zur Fehlersuche: zeigt, ob die Prozessgrenze richtig konstruiert ist —
    insbesondere, ob `--rotiere-z-up` bei Z-up-Quellen gesetzt wird.
    """
    cmd = [
        "blender", "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        "--glb", str(glb_path), "--out", str(out_dir),
        "--aufloesung", str(aufloesung), "--samples", str(samples),
    ]
    if needs_rotation(up_axis):
        cmd.append("--rotiere-z-up")
    return cmd


__all__ = [
    "ContractError", "SeamError",
    "baue_kommando_tiefenkarte", "finde_blender", "finde_ifc_python",
    "glb_zu_tiefenkarte", "ifc_zu_glb",
]
