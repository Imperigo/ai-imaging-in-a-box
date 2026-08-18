"""Die Wache an der Prozessgrenze — Regel 1 (LGPL-Präzisierung) und Regel 2.

Blender steht unter GPL-2.0-or-later, das ifcopenshell-Wheel bindet GPL-lizenziertes
CGAL statisch ein. Beide dürfen nur als **eigenständige Programme** aufgerufen werden,
nie als Import im Produkt-Environment: Ein ``import bpy`` oder ``import ifcopenshell``
in ``src/aiimaging/`` machte das ausgelieferte Produkt GPL.

Die Grenze ist eine Zusage, die man nicht sieht — ein einziger Import in einem späteren
Commit hebt sie stillschweigend auf. Darum die vier Wachen dieser Datei:

1. Quelltext-Scan über den Kern (per ``ast``, damit Docstrings und Kommentare, die den
   verbotenen Import *besprechen*, nicht fälschlich anschlagen).
2. Laufzeitprobe in einem frischen Interpreter: nach ``import aiimaging`` liegt keines
   der beiden Module in ``sys.modules``.
3. Die Runner existieren, nutzen die verbotenen Module — und werden hier **nicht**
   importiert, denn sie leben jenseits der Grenze.
4. ``finde_ifc_python`` fällt nie auf ``sys.executable`` zurück; genau dieser Fehlgriff
   holte GPL-Code in den Produktprozess zurück.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import PAKET, RUNNER_DIR, SRC

#: Module, die im Produkt-Environment nichts zu suchen haben. Ihre Lizenzen sind der
#: Grund für die Prozessgrenze — nicht Geschmack.
VERBOTEN = ("bpy", "ifcopenshell")


def importierte_module(quelle: str) -> set[str]:
    """Alle top-level Modulnamen, die eine Quelldatei tatsächlich importiert.

    Bewusst über ``ast`` statt Textsuche: Die Modul-Docstrings von ``contracts.py`` und
    ``seams.py`` erklären, warum ``import bpy`` verboten ist — eine Textsuche würde an
    genau dieser Erklärung scheitern und den Test wertlos machen (er wäre immer rot).
    Erfasst werden auch Importe innerhalb von Funktionen, denn die Grenze gilt dort
    genauso.
    """
    gefunden: set[str] = set()
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.Import):
            gefunden.update(alias.name.split(".")[0] for alias in knoten.names)
        elif isinstance(knoten, ast.ImportFrom):
            if knoten.level == 0 and knoten.module:
                gefunden.add(knoten.module.split(".")[0])
    return gefunden


def kern_dateien() -> list[Path]:
    """Alle Python-Dateien des Produkts — ohne ``runners/``, das jenseits der Grenze liegt."""
    return sorted(p for p in PAKET.rglob("*.py") if RUNNER_DIR not in p.parents)


# --------------------------------------------------------------------------------------
# 0 · Der Scanner selbst — ein Test, der nichts findet, bewacht nichts
# --------------------------------------------------------------------------------------

def test_scanner_findet_import_auch_in_funktionen():
    """Selbstprobe: Der Scanner erkennt verbotene Importe auch tief im Code, nicht nur oben."""
    quelle = "def f():\n    import bpy\n    from ifcopenshell import geom\n    return bpy, geom\n"
    assert importierte_module(quelle) >= {"bpy", "ifcopenshell"}


def test_scanner_ignoriert_erwaehnungen_in_text():
    """Selbstprobe: Über einen verbotenen Import zu *schreiben* ist kein Vertragsbruch."""
    quelle = '"""Ein import bpy waere hier verboten."""\n# import ifcopenshell ebenso\nimport json\n'
    assert importierte_module(quelle) == {"json"}


def test_kern_bespricht_die_grenze_im_text():
    """Beleg, dass der ast-Ansatz nötig ist: Eine reine Textsuche schlüge im Kern an."""
    treffer = [p.name for p in kern_dateien()
               if any(f"import {m}" in p.read_text(encoding="utf-8") for m in VERBOTEN)]
    assert treffer, "Erwartet: die Docstrings erklären das Importverbot im Wortlaut"


# --------------------------------------------------------------------------------------
# 1 · Quelltext-Scan über den Kern
# --------------------------------------------------------------------------------------

def test_kern_dateien_werden_ueberhaupt_gefunden():
    """Vorbedingung: Der Scan läuft über echte Dateien, nicht über eine leere Liste."""
    namen = {p.name for p in kern_dateien()}
    assert {"__init__.py", "contracts.py", "seams.py"} <= namen


@pytest.mark.parametrize("datei", kern_dateien(), ids=lambda p: p.name)
def test_kein_verbotener_import_im_kern(datei):
    """Regel 1 und 2: Keine Produktdatei importiert ``bpy`` oder ``ifcopenshell``."""
    module = importierte_module(datei.read_text(encoding="utf-8"))
    verstoss = sorted(module.intersection(VERBOTEN))
    assert not verstoss, (
        f"{datei} importiert {verstoss} — das holt GPL-Code ins Produkt-Environment. "
        "Der Aufruf gehört als Subprozess in aiimaging/runners/."
    )


def test_kein_add_on_gerüst_im_kern():
    """Regel 2: Keine Blender-Add-on-Verpackung (``bl_info``) im Produktcode."""
    for datei in kern_dateien():
        assert "bl_info" not in datei.read_text(encoding="utf-8"), f"{datei} riecht nach Add-on"


# --------------------------------------------------------------------------------------
# 2 · Laufzeitprobe
# --------------------------------------------------------------------------------------

def test_import_des_kerns_laedt_keine_verbotenen_module():
    """Regel 2 zur Laufzeit: ``import aiimaging`` zieht ``bpy``/``ifcopenshell`` nicht nach."""
    import aiimaging  # noqa: F401
    import aiimaging.seams  # noqa: F401

    geladen = sorted(m for m in VERBOTEN if m in sys.modules)
    assert not geladen, f"{geladen} liegt nach dem Import des Kerns in sys.modules"


def test_frischer_interpreter_bleibt_frei_von_bpy_und_ifcopenshell():
    """Gegenprobe in einem sauberen Prozess — unabhängig davon, was pytest sonst geladen hat."""
    programm = (
        "import sys\n"
        "import aiimaging, aiimaging.seams, aiimaging.contracts\n"
        f"treffer = [m for m in {VERBOTEN!r} if m in sys.modules]\n"
        "print(','.join(treffer))\n"
    )
    ergebnis = subprocess.run(
        [sys.executable, "-c", programm],
        capture_output=True, text=True, timeout=120,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(SRC), "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert ergebnis.returncode == 0, ergebnis.stderr
    assert ergebnis.stdout.strip() == "", f"nachgeladen: {ergebnis.stdout.strip()}"


# --------------------------------------------------------------------------------------
# 3 · Die Runner leben jenseits der Grenze — hier wird nur hingeschaut, nie importiert
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("dateiname, erwartet", [
    ("blender_depth_stage.py", "bpy"),
    ("ifc_to_glb_runner.py", "ifcopenshell"),
])
def test_runner_existiert_und_nutzt_sein_fremdmodul(dateiname, erwartet):
    """Die Grenze hat zwei Seiten: Was drüben liegt, DARF das Fremdmodul nutzen — dafür ist es da.

    Der Test importiert die Datei bewusst nicht (``bpy`` gibt es hier gar nicht, und ein
    Import wäre genau der verbotene Schritt); er liest sie nur mit ``ast``.
    """
    datei = RUNNER_DIR / dateiname
    assert datei.exists(), f"{datei} fehlt — ohne Runner gibt es keinen Subprozess aufzurufen"
    assert erwartet in importierte_module(datei.read_text(encoding="utf-8"))


def test_runner_werden_vom_produkt_nicht_importiert():
    """Kein Kernmodul importiert ``aiimaging.runners`` — sie werden aufgerufen, nicht geladen."""
    for datei in kern_dateien():
        for knoten in ast.walk(ast.parse(datei.read_text(encoding="utf-8"))):
            if isinstance(knoten, ast.Import):
                namen = [a.name for a in knoten.names]
            elif isinstance(knoten, ast.ImportFrom):
                namen = [knoten.module or ""]
            else:
                continue
            for name in namen:
                assert not name.startswith("aiimaging.runners"), f"{datei} importiert {name}"


def test_runner_sind_nach_dem_import_des_kerns_nicht_geladen():
    """Auch als Python-Module bleiben die Runner draussen — sonst wäre die Grenze nur Prosa."""
    import aiimaging  # noqa: F401

    geladen = [m for m in sys.modules if m.startswith("aiimaging.runners")]
    assert not geladen, f"{geladen} wurde in den Produktprozess geladen"


def test_seams_kennt_die_runner_nur_als_pfade():
    """Die Naht verweist auf die Runner als Dateipfade — die einzige erlaubte Bezugnahme."""
    from aiimaging import seams

    assert seams.BLENDER_RUNNER == RUNNER_DIR / "blender_depth_stage.py"
    assert seams.IFC_RUNNER == RUNNER_DIR / "ifc_to_glb_runner.py"
    assert isinstance(seams.BLENDER_RUNNER, Path)


# --------------------------------------------------------------------------------------
# 4 · Kein Rückfall auf sys.executable
# --------------------------------------------------------------------------------------

def test_ifc_python_faellt_nie_auf_das_produkt_python_zurueck(monkeypatch):
    """Der Fehlgriff, den die Grenze verhindern soll: ifcopenshell im Produkt-Environment.

    Ohne Umgebungsvariable und ohne ``.venv-ifc`` muss ``SeamError`` fliegen — ein
    stiller Rückfall auf ``sys.executable`` liesse GPL-CGAL in diesem Prozess laufen.
    """
    from aiimaging import seams

    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: False)   # venv gilt als nicht vorhanden

    with pytest.raises(seams.SeamError) as fehler:
        seams.finde_ifc_python()

    assert ".venv-ifc" in str(fehler.value)
    assert sys.executable not in str(fehler.value)


def test_ifc_python_nimmt_das_venv_und_nicht_den_eigenen_interpreter(monkeypatch):
    """Ist das venv da, zeigt der Pfad dorthin — und gerade nicht auf das laufende Python."""
    from aiimaging import seams

    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: True)

    gefunden = seams.finde_ifc_python()

    assert gefunden.endswith(str(Path(".venv-ifc") / "bin" / "python"))
    assert gefunden != sys.executable


def test_umgebungsvariable_hat_vorrang(monkeypatch):
    """Ein gesetztes ``AIIMAGING_IFC_PYTHON`` gewinnt — so bleibt das venv austauschbar (Regel 1)."""
    from aiimaging import seams

    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/anderswo/venv/bin/python")
    assert seams.finde_ifc_python() == "/anderswo/venv/bin/python"


def test_fehlendes_blender_wird_gemeldet_statt_ersetzt(monkeypatch):
    """Regel 2: Fehlt das Blender-Binary, wird das gesagt — es gibt keinen Ersatz im Prozess."""
    from aiimaging import seams

    monkeypatch.delenv("AIIMAGING_BLENDER", raising=False)
    monkeypatch.setattr(seams.shutil, "which", lambda _name: None)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(seams.SeamError, match="Blender nicht gefunden"):
        seams.finde_blender()
