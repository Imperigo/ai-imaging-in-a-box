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
    """IFC → glb (Y-up) über den Subprozess im `.venv-ifc`.

    **IFC4 *und* IFC2X3.** Hier stand bis zum 18.08.2026 „IFC4". Das war eine Behauptung
    über eine Datei, die niemand gesehen hatte: An 40 echten Dateien (`auf-20260818-08`)
    waren 30 IFC4 und **10 IFC2X3 — und alle zehn davon kamen aus ArchiCAD**. Wer nur
    gegen IFC4 prüft, prüft nicht gegen das, was das verbreitetste Autorenprogramm
    tatsächlich liefert.

    Beide Schemata sind hier durch den echten Konverter gemessen, in Metern und in
    Millimetern, jeweils mit demselben Ergebnis (8,0 × 5,0 × 3,25 m).

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
                         beauty: bool, material_id: bool, kamera=None,
                         auge=None, blick_auf=None, brennweite=None,
                         gelaende_z=None) -> list[str]:
    """Die Argumente hinter dem `--`-Trenner — eine Stelle für Lauf und Trockenlauf.

    Wären sie zweimal geschrieben, könnten `glb_zu_multipass` und
    `baue_kommando_multipass` auseinanderlaufen — und dann prüfte der Test ein Kommando,
    das so nie gestartet wird.

    Zur Kamera gibt es zwei Wege, und ohne Angabe bleibt es beim Rückfall des Runners:

    * ``kamera`` — ein Richtungskürzel aus :mod:`aiimaging.kameras`. Der Standort wird
      dann **im Runner** aus der dort gemessenen Hüllbox abgeleitet. Das ist der sichere
      Weg, weil er keine Annahme über Bezugssysteme macht: Ob die Hüllbox aus dem IFC nach
      Export, Import und einer möglichen Z-up-Drehung noch dieselbe ist, gehört gemessen
      und nicht angenommen.
    * ``auge`` und ``blick_auf`` — fertige Koordinaten. Wer sie schickt, hat selbst
      gerechnet und trägt die Verantwortung für das Bezugssystem.

    Raises:
        SeamError: ``auge`` ohne ``blick_auf`` (oder umgekehrt). Ein Standort ohne
            Blickziel beschreibt keine Kamera, und der Runner würde erst nach dem
            Blender-Start abbrechen — Minuten später, für nichts.
    """
    argumente = [
        "--glb", str(glb_path), "--out", str(out_dir),
        "--aufloesung", str(aufloesung), "--samples", str(samples),
    ]
    if (auge is None) != (blick_auf is None):
        raise SeamError(
            "auge und blick_auf gehören zusammen: "
            f"auge={auge!r}, blick_auf={blick_auf!r}. Ein Standort ohne Blickziel "
            "beschreibt keine Kamera."
        )
    if auge is not None:
        argumente += ["--auge", _punkt(auge, "auge"),
                      "--blick-auf", _punkt(blick_auf, "blick_auf")]
    elif kamera is not None:
        argumente += ["--kamera", str(kamera)]
    if brennweite is not None:
        argumente += ["--brennweite", str(float(brennweite))]
    if gelaende_z is not None:
        argumente += ["--gelaende-z", str(float(gelaende_z))]
    if drehen:
        argumente.append("--rotiere-z-up")
    if not beauty:
        argumente.append("--ohne-beauty")
    if not material_id:
        argumente.append("--ohne-material-id")
    return argumente


def _punkt(wert, name: str) -> str:
    """``(1, 2, 3)`` → ``"1.0,2.0,3.0"`` — die Form, die der Runner liest.

    Raises:
        SeamError: nicht drei endliche Zahlen. Hier abzufangen statt im Runner spart
            einen Blender-Start: Der Fehler ist an drei Zahlen erkennbar, und der Lauf
            dahinter kostet Minuten.
    """
    try:
        werte = [float(w) for w in wert]
    except (TypeError, ValueError) as e:
        raise SeamError(f"{name} muss drei Zahlen sein, war: {wert!r}") from e
    if len(werte) != 3 or any(w != w or w in (float("inf"), float("-inf")) for w in werte):
        raise SeamError(f"{name} muss drei endliche Zahlen sein, war: {wert!r}")
    return ",".join(repr(w) for w in werte)


def glb_zu_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                     samples: int = 16, beauty: bool = True, material_id: bool = True,
                     kamera=None, auge=None, blick_auf=None, brennweite=None,
                     gelaende_z=None, timeout: int = 900, _starte=None) -> dict:
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

        `depth_png` und `depth_normalisierung` kommen **nicht** aus Blender, sondern
        werden hier nachgerechnet — siehe :func:`_tiefe_nachbearbeiten`. Scheitert das,
        steht der Grund in `depth_png_fehler` und der Lauf gilt trotzdem als gelungen:
        Die EXR mit den echten Metern ist das massgebliche Artefakt.

    Raises:
        ContractError: `up_axis` fehlt oder ist nicht deutbar.
        SeamError: Blender fehlt oder der Lauf scheitert.
    """
    starte = _starte or _default_starte
    drehen = needs_rotation(up_axis)          # wirft ContractError, wenn up_axis fehlt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ausgaben eines frueheren Laufs VOR dem Start entfernen — nicht nur den Report.
    #
    # Vorgeschichte: In Sitzung 03 wurde der Report geloescht, weil ein abgestuerzter Lauf
    # sich sonst am liegengebliebenen Report gesundmeldete. In Sitzung 05 stellte sich
    # heraus, dass dasselbe eine Datei weiter noch galt: Der Runner erklaerte den Lauf fuer
    # gelungen, sobald eine `tiefe_*.exr` im Verzeichnis lag — auch die des Vorlaufs. Weil
    # `out_dir` ueblicherweise wiederverwendet wird, verwies ein gescheiterter Lauf dann auf
    # das Bild von gestern.
    #
    # Die Lehre, die dieses Projekt mehrfach gelernt hat: Die Existenz einer Datei ist kein
    # Beleg fuer ihren Inhalt. Darum wird hier abgeraeumt statt geprueft.
    bericht = out_dir / "blender-report.json"
    bericht.unlink(missing_ok=True)
    for muster in ("tiefe_*.exr", "tiefe_norm.png", "material_id.png", "beauty_*.png"):
        for alt_datei in out_dir.glob(muster):
            alt_datei.unlink(missing_ok=True)

    cmd = [
        finde_blender(), "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=drehen, aufloesung=aufloesung,
                              samples=samples, beauty=beauty, material_id=material_id,
                              kamera=kamera, auge=auge, blick_auf=blick_auf,
                              brennweite=brennweite, gelaende_z=gelaende_z),
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
    report = json.loads(bericht.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise SeamError(
            f"blender-report.json enthält kein Objekt, sondern "
            f"{type(report).__name__}. Eine abgeschnittene oder fremde Datei — der Lauf "
            f"ist damit nicht deutbar."
        )
    return _tiefe_nachbearbeiten(report, out_dir, timeout=timeout, _starte=starte)


def _tiefe_nachbearbeiten(report: dict, out_dir: Path, *, timeout: int = 300,
                          _starte=None) -> dict:
    """Aus der EXR das normalisierte PNG rechnen — auf dieser Seite der Prozessgrenze.

    Bis zum 18.08.2026 tat das der Runner selbst. Der Schritt ist hierher gewandert,
    weil Blender 5.2 die Multilayer-EXR, die es dort schreiben **muss**, selbst nicht
    wieder einlesen kann (`bpy.data.images.load` liefert 0×0 mit 0 Kanälen). Die volle
    Begründung samt Messwerten steht in :mod:`aiimaging.bildschreiben`.

    Warum das die bessere Naht ist, unabhängig vom Fehler: Eine Normalisierung ist
    Arithmetik auf einem Zahlenfeld. Sie hier zu rechnen heisst, sie **ohne Blender,
    ohne GPU und ohne Prozessgrenze** testen zu können — Regel 4 in ihrer schärfsten
    Lesart. Und es gibt nur noch **einen** Weg zum PNG statt eines je Blender-Fassung;
    zwei Wege wären eine stille Abweichung, die niemand bemerkt.

    Der Schritt ist bewusst **nicht** tödlich: Scheitert er, bleibt der Blender-Lauf
    gültig. Die EXR ist das massgebliche Artefakt — sie trägt echte Meter, das PNG ist
    ihre verlustbehaftete Ableitung für das Bildmodell. Was schiefging, steht in
    `depth_png_fehler`, nicht in einem Traceback.
    """
    from aiimaging import bildschreiben               # spät, damit `seams` leicht bleibt

    # Überschreiben, nicht ergänzen. Diese Naht ist ab jetzt der einzige Erzeuger von
    # `depth_png`; ein Wert, der schon im Report stand, stammt aus einem Runner, der
    # nicht mehr normalisiert — also aus einem früheren Lauf oder einer fremden Fassung.
    # Ihn stehen zu lassen hiesse, auf eine Datei zu zeigen, die niemand geschrieben hat.
    # Das ist dieselbe Lehre wie beim Abräumen der Altdateien weiter oben: Ein Feld im
    # Report ist kein Beleg für eine Datei auf der Platte.
    report["depth_png"] = None
    report["depth_normalisierung"] = None
    report["depth_png_fehler"] = None

    exr = report.get("depth_exr")
    if not exr:
        report["depth_png_fehler"] = "Report nennt keine `depth_exr` — nichts zu normalisieren."
        return report
    if not Path(exr).exists():
        report["depth_png_fehler"] = f"`depth_exr` zeigt auf {exr}, dort liegt nichts."
        return report

    ziel = Path(out_dir) / "tiefe_norm.png"
    try:
        # `timeout` und `_starte` weiterreichen: Der stdlib-Leser kann nicht jede
        # EXR-Spielart, und sein Rückfall ist ein zweiter Blender-Prozess. Ohne diese
        # beiden Argumente liefe er ohne Naht und mit einem Zeitlimit, das der Aufrufer
        # nie gesetzt hat.
        normalisierung = bildschreiben.tiefe_exr_zu_png(
            exr, ziel, timeout=timeout, _starte=_starte)
    except Exception as e:                              # Befund als Feld, nicht als Absturz
        report["depth_png_fehler"] = f"{type(e).__name__}: {e}"
        return report

    # Nachsehen statt behaupten — dieselbe Prüfung, die `render.rendere` am Ende macht.
    # Ein Schreiber, der einen Pfad zurückgibt, ohne etwas zu hinterlassen, ist ein
    # Fehlschlag und kein Erfolg mit fehlender Datei.
    if not ziel.is_file() or ziel.stat().st_size == 0:
        report["depth_png_fehler"] = (
            f"Die Normalisierung meldete Erfolg, aber {ziel.name} fehlt oder ist leer."
        )
        return report

    report["depth_normalisierung"] = normalisierung
    report["depth_png"] = str(ziel)
    return report


def baue_kommando_multipass(glb_path, out_dir, *, up_axis, aufloesung: int = 512,
                            samples: int = 16, beauty: bool = True,
                            material_id: bool = True, kamera=None, auge=None,
                            blick_auf=None, brennweite=None,
                            gelaende_z=None) -> list[str]:
    """Nur das Blender-Kommando bauen, ohne es auszuführen.

    Für Tests und zur Fehlersuche: zeigt, ob die Prozessgrenze richtig konstruiert ist —
    insbesondere, ob `--rotiere-z-up` bei Z-up-Quellen gesetzt wird.
    """
    return [
        "blender", "--background", "--factory-startup",
        "--python", str(BLENDER_RUNNER), "--",
        *_multipass_argumente(glb_path, out_dir, drehen=needs_rotation(up_axis),
                              aufloesung=aufloesung, samples=samples,
                              beauty=beauty, material_id=material_id,
                              kamera=kamera, auge=auge, blick_auf=blick_auf,
                              brennweite=brennweite, gelaende_z=gelaende_z),
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
