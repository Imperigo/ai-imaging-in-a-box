#!/usr/bin/env python3
"""Die Beispiel-JSONs für KosmoOrbit — aus unserem Code erzeugt, nicht von Hand geschrieben.

**Anlass (29.09.2026):** KosmoOrbit schreibt ihre Schemas nach einem Beispiel, nicht nach
einer Feldliste (Antworten auf auf-142 und auf-171). Ein von Hand geschriebenes Beispiel
wäre eine Behauptung über unseren Code; dieses hier ist seine Ausgabe.

Was echt ist, und was nicht
---------------------------
==========================  ================================================================
IFC → glb → Multipass       **echt** (IfcOpenShell, Blender/Cycles) — synthetischer Bau aus
                            ``tools/make_test_ifc.py`` (Regel 3)
Ebenen (``ebenen``)         **echt**: Dateien und ``bedeutung`` kommen aus dem Blender-Bericht
Puls und ``/health``        **echt**: dieselben Funktionen wie im Betrieb, Uhr eingespritzt
Diffusion                   **Attrappe** — das Bild ist das Blender-Schönbild; ``engine_*``
                            nennt das Vorgabemodell aus dem Register, gerechnet hat es nicht
Geometrie-QA                **Attrappe** (Wert 0,9) — ``qa``, ``qa_je_kamera``,
                            ``geometry_gates`` zeigen die FORM, nicht eine Messung
==========================  ================================================================

Aufruf::

    python3 tools/vertragsbeispiele.py <zielordner> [--echt]

Braucht Blender und ``.venv-ifc`` (wie ``tests/test_kettenlauf_echt.py``). ``--echt`` (nur
an der HomeStation, GPU): Diffusion, Tiefenschätzer und Nullprobe laufen wirklich — dann
ist auch ``qa``/``geometry_gates`` gemessen und nicht bloss geformt (``auf-20260929-176``).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import abholer, backbone, bruecke, knotenweg  # noqa: E402
from aiimaging.seams import ifc_zu_glb  # noqa: E402

JOB = "vis-1790000000-e124a1"
#: Ein fester Zeitpunkt, damit zwei Läufe dasselbe Beispiel ergeben (29.09.2026 12:00 UTC).
UHR = 1790683200.0


def _auftrag(basis: Path, glb: Path) -> Path:
    ordner = basis / JOB
    ordner.mkdir(parents=True)
    (ordner / bruecke.DATEI_LAUFZETTEL).write_text(json.dumps({
        "job_id": JOB, "status": "queued",
        "approval_token": bruecke.TOKEN_VORSATZ + "deadbeef"}), encoding="utf-8")
    szene = {"schema": bruecke.kosmo_szene.SCHEMA_SZENE,
             "geometry": {"path": bruecke.DATEI_MODELL, "format": "glb"},
             "cameras": [
                 {"name": "Suedost", "position": [18, -12, 1.6], "target": [4, 2.5, 1.5],
                  "fov": 50, "up_axis": "z"},
                 {"name": "Suedwest", "position": [-11, -9, 1.6], "target": [4, 2.5, 1.5],
                  "fov": 50, "up_axis": "z"}],
             "render": {"samples": 8, "faithful": 0.8, "resolution": [384, 256],
                        "passes": "alle"},
             "style": {"prompt": "overcast sky, no people"}}
    (ordner / bruecke.DATEI_SZENE).write_text(json.dumps(szene, indent=2), encoding="utf-8")
    shutil.copy(glb, ordner / bruecke.DATEI_MODELL)
    return ordner


def _verarbeite(aus: Path, echt: bool = False):
    if echt:
        return abholer.verarbeiter(out_wurzel=aus)
    bb = backbone.BACKBONES["z-image-turbo"]

    def rendere(auftrag, **_):
        # ATTRAPPE: Das «KI-Bild» ist das Schönbild aus Blender.
        ziel = Path(auftrag.ausgabe_png)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(auftrag.beauty_png, ziel)
        return {"status": "ok", "bild_png": str(ziel), "hinweise": (),
                "backbone": bb.name, "lizenz": {"lizenz": bb.lizenz}, "parameter": {}}

    def qa(*_a, **_k):
        return {"status": "ok", "score": 0.9, "bestanden": True}   # ATTRAPPE

    return abholer.verarbeiter(out_wurzel=aus, nullprobe=False, _rendere=rendere, _qa=qa,
                               _tiefen_modell=object())


def _schreibe(ziel: Path, name: str, inhalt) -> None:
    (ziel / name).write_text(json.dumps(inhalt, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")


def main(ziel: Path, echt: bool = False) -> int:
    ziel.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ifc, glb = tmp / "bau.ifc", tmp / "model.glb"
        subprocess.run([sys.executable, "tools/make_test_ifc.py", str(ifc), "--gelaende"],
                       check=True, capture_output=True, cwd=WURZEL)
        bericht = ifc_zu_glb(ifc, glb)
        if bericht["status"] != "ok":
            raise SystemExit(f"IFC → glb gescheitert: {bericht.get('error')}")

        # 1 · Der nie gesehene Abholer: eine Ablage ohne Pulsdatei.
        ablage = tmp / "ablage"
        ablage.mkdir()
        gesund = {"nie_gesehen": knotenweg.gesundheit(ablage, _uhr=lambda: UHR)}

        # 2 · Ein echter Durchgang mit einem Auftrag, der alle Ebenen bestellt.
        ordner = _auftrag(ablage, glb)
        durchgang = abholer.durchgang(ablage, verarbeite=_verarbeite(tmp / "aus", echt),
                                      fremde_freigabe_gilt=True, _uhr=lambda: UHR)
        if durchgang["verarbeitet"] != 1:
            raise SystemExit(f"Der Durchgang hat nichts verarbeitet: "
                             f"{durchgang['ergebnisse']}")
        ergebnis = json.loads((ordner / bruecke.DATEI_ERGEBNIS).read_text(encoding="utf-8"))
        _schreibe(ziel, "render-result.json", ergebnis)
        _schreibe(ziel, "render-scene.json",
                  json.loads((ordner / bruecke.DATEI_SZENE).read_text(encoding="utf-8")))
        # Die Bilder UND die Ebenen: `images` nennt Dateien, und ein Beispiel, das auf
        # fehlende Dateien zeigt, ist keines (Befund der HomeStation, auf-176, 30.09.2026).
        namen = list(ergebnis.get("images") or ()) + [
            e["datei"] for e in ergebnis.get("ebenen") or () if e.get("datei")]
        for name in namen:
            shutil.copy(ordner / name, ziel / name)
        _schreibe(ziel, "abholer-puls.json",
                  json.loads((ablage / abholer.DATEI_PULS).read_text(encoding="utf-8")))

        # 3 · /health in den übrigen Zuständen — dieselbe Pulsdatei, verschiedene Uhren.
        gesund["laeuft_leer"] = knotenweg.gesundheit(ablage, _uhr=lambda: UHR + 31)
        gesund["steht"] = knotenweg.gesundheit(
            ablage, _uhr=lambda: UHR + knotenweg.PULS_FRIST_S + 45)
        puls = json.loads((ablage / abholer.DATEI_PULS).read_text(encoding="utf-8"))
        (ablage / abholer.DATEI_PULS).write_text(
            json.dumps(dict(puls, liegengelassen=1)), encoding="utf-8")
        gesund["wartet"] = knotenweg.gesundheit(ablage, _uhr=lambda: UHR + 31)
        bruecke.setze_status(ordner, bruecke.STATUS_RUNNING)
        gesund["arbeitet"] = knotenweg.gesundheit(ablage, _uhr=lambda: UHR + 31)
        _schreibe(ziel, "health-abholer-je-zustand.json", gesund)
    print(f"geschrieben nach {ziel}")
    return 0


if __name__ == "__main__":
    argumente = [a for a in sys.argv[1:] if a != "--echt"]
    if len(argumente) != 1:
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(argumente[0]), echt="--echt" in sys.argv[1:]))
