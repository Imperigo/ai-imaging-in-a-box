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


def _multipass_argumente(glb_path, out_dir, *, drehen: bool, aufloesung: int, samples: int,
                         beauty: bool, material_id: bool) -> list[str]:
    """Die Argumente hinter dem `--`-Trenner — eine Stelle für Lauf und Trockenlauf.

    Wären sie zweimal geschrieben, könnten `glb_zu_multipass` und
    `baue_kommando_multipass` auseinanderlaufen — und dann prüfte der Test ein Kommando,
    das so nie gestartet wird.
    """
    argumente = [
        "--glb", str(glb_path), "--out", str(out_dir),
        "--aufloesung", str(aufloesung), "--samples", str(samples),
    ]
    if drehen:
        argumente.append("--rotiere-z-up")
    if not beauty:
        argumente.append("--ohne-beauty")
    if not material_id:
        argumente.append("--ohne-material-id")
    return argumente


def glb_zu_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                     samples: int = 16, beauty: bool = True, material_id: bool = True,
                     timeout: int = 900, _starte=None) -> dict:
    """glb → Cycles-Multipass über `blender --background`.

    Vier Ausgaben, in zwei Renderdurchgängen: Beauty und Tiefe (EXR in Metern plus
    normalisiertes 16-Bit-PNG, nah = hell) entstehen gemeinsam, die Material-ID braucht
    einen eigenen Durchgang — ihr Emissions-Override würde sonst das Beauty-Bild in eine
    flache Farbfläche verwandeln.

    `up_axis` ist **Pflicht**, kein Vorgabewert. Der Grund ist der Phase-0-Befund: Zwei
    Erzeuger im Ökosystem liefern beide ein Feld `glb_path`, aber mit unterschiedlicher
    Orientierung (KosmoDraw Z-up, KosmoVis Y-up). Ein Default wäre eine stille
    Verdrehung von Tiefenkarte, Kamera und späterer Geometrie-QA.

    Args:
        beauty: `False` unterdrückt nur das Schreiben des Beauty-PNG. Gerendert wird der
            Durchgang trotzdem — die Tiefe ist ein Pass desselben Renders und hinge sonst
            in der Luft. Spart Plattenplatz, keine Rechenzeit.
        material_id: `False` lässt den zweiten Durchgang ganz aus und spart damit
            tatsächlich Rechenzeit.

    Returns:
        Report des Runners mit `beauty_png`, `material_id_png`, `depth_exr`, `depth_png`,
        `n_materialien` und `depth_normalisierung` (min/max in Metern, für die Rückrechnung
        des PNG in echte Tiefen).

    Raises:
        ContractError: `up_axis` fehlt oder ist nicht deutbar.
        SeamError: Blender fehlt oder der Lauf scheitert.
    """
    starte = _starte or _default_starte
    drehen = needs_rotation(up_axis)          # wirft ContractError, wenn up_axis fehlt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Einen Report aus einem frueheren Lauf VOR dem Start entfernen. Ohne das wuerde ein
    # abgestuerzter Blender-Lauf still gelingen, weil der Erfolg unten an der blossen
    # Existenz der Datei haengt — und out_dir wird ueblicherweise wiederverwendet. Genau
    # die Sorte stiller Falschmeldung, gegen die dieses Projekt sonst antritt.
    bericht = out_dir / "blender-report.json"
    bericht.unlink(missing_ok=True)

    cmd = [
        finde_blender(), "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=drehen, aufloesung=aufloesung,
                              samples=samples, beauty=beauty, material_id=material_id),
    ]

    ergebnis = starte(cmd, timeout)

    # Zwei unabhaengige Bedingungen, beide notwendig: Der Prozess muss sauber geendet
    # haben UND einen Report hinterlassen haben. Nur die Datei zu pruefen genuegt nicht
    # (siehe oben), nur den Rueckgabewert auch nicht — Blender kann 0 melden und am
    # Compositor gescheitert sein.
    if ergebnis.returncode != 0:
        raise SeamError(
            f"Blender endete mit Code {ergebnis.returncode}:\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1500:]}"
        )
    if not bericht.exists():
        raise SeamError(
            f"Blender schrieb keinen Report (Code {ergebnis.returncode}):\n"
            f"{(ergebnis.stderr or ergebnis.stdout or '').strip()[-1500:]}"
        )
    return json.loads(bericht.read_text(encoding="utf-8"))


def baue_kommando_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                            samples: int = 16, beauty: bool = True,
                            material_id: bool = True) -> list[str]:
    """Nur das Blender-Kommando bauen, ohne es auszuführen.

    Für Tests und zur Fehlersuche: zeigt, ob die Prozessgrenze richtig konstruiert ist —
    insbesondere, ob `--rotiere-z-up` bei Z-up-Quellen gesetzt wird.
    """
    return [
        "blender", "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=needs_rotation(up_axis),
                              aufloesung=aufloesung, samples=samples,
                              beauty=beauty, material_id=material_id),
    ]


# ── Alte Namen ───────────────────────────────────────────────────────────────────────
# Der Lauf liefert seit dem Multipass nicht mehr nur eine Tiefenkarte, sondern vier
# Ausgaben; `…_tiefenkarte` benennt also nur noch einen Teil dessen, was passiert. Die
# alten Namen bleiben als Alias stehen, weil sie in `docs/`, in bestehenden Tests und in
# der MCP-Anbindung vorkommen: Ein blosses Umbenennen wäre ein stiller Bruch für jeden
# Aufrufer ausserhalb dieses Repos — und die Prozessgrenze ist genau die Stelle, an der
# dieses Projekt keine stillen Brüche will. Neuer Code nimmt die `…_multipass`-Namen.
glb_zu_tiefenkarte = glb_zu_multipass
baue_kommando_tiefenkarte = baue_kommando_multipass


__all__ = [
    "ContractError", "SeamError",
    "baue_kommando_multipass", "baue_kommando_tiefenkarte",
    "finde_blender", "finde_ifc_python",
    "glb_zu_multipass", "glb_zu_tiefenkarte", "ifc_zu_glb",
]
