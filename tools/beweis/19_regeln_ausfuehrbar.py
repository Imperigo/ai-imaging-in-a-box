#!/usr/bin/env python3
"""BEWEIS 19 — Die vier nicht verhandelbaren Regeln aus ``CLAUDE.md`` sind nicht nur
Prosa, sondern **ausführbarer Code**: Vier echte Läufe, vier Tafeln, je eine Regel.

Was bewiesen wird — und wie, echt statt behauptet
--------------------------------------------------
1. **Regel 1 (Lizenz).** ``backbone.waehle(kommerziell=True)`` wird ECHT aufgerufen und
   das Ergebnis gegen die ECHTE Registry (``backbone.BACKBONES``) geprüft: FLUX.1-dev und
   FLUX.2-dev — die beiden Non-Commercial-Einträge — dürfen darin nicht vorkommen. Jeder
   Registry-Eintrag bekommt zusätzlich sein echtes ``backbone.pruefe_lizenz(...)``-Urteil
   (``01_regel1_lizenz-ampel_*.png``).
2. **Regel 2 (Prozessgrenze).** Aus einer synthetischen IFC (``tools/make_test_ifc.py``,
   Regel 3 in Aktion) wird ECHT über ``seams.ifc_zu_glb`` (Subprozess im ``.venv-ifc``)
   eine glb gebaut, und ``sys.modules`` dieses Prozesses wird DANACH durchsucht:
   ``ifcopenshell`` darf nicht darin stehen. Optional (siehe unten) folgt derselbe Schnitt
   nach einem echten ``seams.glb_zu_multipass``-Lauf für ``bpy``
   (``02_regel2_prozessgrenze_*.png``).
3. **Regel 3 (keine echten Projektdaten / keine Namen in Pfaden).** Der bestehende
   Regel-3-Wächter aus ``tests/test_regel3_kennungen.py`` wird **unverändert** geladen
   (``importlib``, keine Kopie der Suchmuster) und über das ECHTE ``git ls-files`` dieses
   Repos laufen gelassen. Gezählt werden geprüfte Dateien und Treffer — beides echte
   Zahlen aus diesem Lauf, nicht aus dem letzten ``pytest``-Protokoll
   (``03_regel3_waechter_*.png``).
4. **Regel 4 (Bibliothek ohne Oberfläche).** Ein FRISCHER Interpreter (eigener
   Subprozess, nicht dieser hier) führt genau ``import aiimaging`` aus und meldet seinen
   kompletten ``sys.modules``-Bestand zurück. Geprüft wird auf 13 benannte Marker: das
   MCP-SDK (``mcp``), ``torch``, ``bpy``, ``ifcopenshell`` und neun UI-Bibliotheken
   (``tkinter``, ``PyQt5/6``, ``PySide2/6``, ``gradio``, ``streamlit``, ``kivy``, ``wx``)
   (``04_regel4_bibliothek_*.png``).

Woran man es im Bild sieht (Regel 2 dieses Auftrags: keine Bitmap-Schrift)
---------------------------------------------------------------------------
Jede Tafel ist eine Reihe farbiger Balken/Felder, keine einzige Ziffer steht im Pixel.
Grün = gemessen und in Ordnung, Rot = gemessen und ein Verstoss (kommt in keinem echten
Lauf dieses Skripts vor — träte er auf, wäre GENAU DAS der Beweis, dass eine Regel
gebrochen ist, nicht ein Darstellungsfehler), Grau = nicht gemessen (nur beim optionalen
Blender-Teil von Regel 2, siehe unten). Alle Zahlen — Registrygrösse, Dateizahl, Treffer,
Modulzahl — stehen ausschliesslich im Dateinamen und in der Konsolenausgabe.

Braucht dieser Beweis ein Gerät?
---------------------------------
Nein — GPU und Modellgewichte kommen nirgends vor. Regel 2 hat aber einen Blender-Teil,
und genau dieses Skript darf Blender laufen lassen, während es GEBAUT wird nicht laufen
darf (mehrere gleichzeitige Blender-Läufe haben in diesem Projekt schon Testläufe
zerstört — Kollisionsschutz, nicht Gerätemangel: Blender rechnet auch auf der CPU, siehe
``seams.BLENDER_TAKT_S``). Deshalb ist der Blender-Teil hinter der Umgebungsvariable
``AIIMAGING_BEWEIS19_MIT_BLENDER=1`` verriegelt:

* Ohne die Variable (Vorgabe) läuft **nur** die ``.venv-ifc``-Hälfte von Regel 2 echt;
  die ``bpy``-Zeile der Tafel wird grau und als "übersprungen" markiert — nicht gemessen
  ist etwas anderes als durchgefallen.
* Mit der Variable läuft zusätzlich ein echter, winziger ``blender --background``-Lauf
  (64×64, 4 Samples, ohne Beauty/Material-ID) und die ``bpy``-Zeile wird grün oder rot,
  je nach echtem Befund.

Aufruf:
    python3 tools/beweis/19_regeln_ausfuehrbar.py [ziel_verzeichnis]
    AIIMAGING_BEWEIS19_MIT_BLENDER=1 python3 tools/beweis/19_regeln_ausfuehrbar.py [ziel]

Ohne Argument schreibt es nach ``build/beweis/19_regeln_ausfuehrbar/``.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WURZEL / "src"))

from aiimaging import backbone, bildschreiben, seams  # noqa: E402

ZIEL_VORGABE = WURZEL / "build" / "beweis" / "19_regeln_ausfuehrbar"

#: Der Kollisionsschutz aus dem Modulkopf — siehe dort.
ENV_BLENDER = "AIIMAGING_BEWEIS19_MIT_BLENDER"

FARBE_HINTERGRUND = (238, 238, 235)
FARBE_GRUEN = (60, 150, 70)      # gemessen, in Ordnung
FARBE_GELB = (215, 165, 40)      # zulässig, aber mit Auflagen
FARBE_ROT = (190, 60, 50)        # gemessen, Verstoss
FARBE_GRAU = (150, 150, 150)     # nicht gemessen (Kollisionsschutz)
FARBE_MARKE = (30, 30, 30)       # neutrale Markierung (z.B. "das ist ein FLUX-dev-Eintrag")


# ----------------------------------------------------------------------------------
# Minimaler Rasterizer — dasselbe Muster wie in den Nachbar-Beweisen (z.B. 08), im
# Projekt gibt es keinen gemeinsamen, weil bildschreiben.py bewusst ohne Bibliothek
# auskommt (Regel 4).
# ----------------------------------------------------------------------------------

def _neues_bild(breite: int, hoehe: int, hg=FARBE_HINTERGRUND) -> list:
    return [hg] * (breite * hoehe)


def _rechteck(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    for y in range(ya, yb):
        zeile = y * breite
        for x in range(xa, xb):
            px[zeile + x] = farbe


def _dunkler(farbe, faktor: float = 0.6):
    return tuple(max(0, int(round(k * faktor))) for k in farbe)


def _rahmen(px: list, breite: int, hoehe: int, x0, y0, x1, y1, farbe) -> None:
    """Gefülltes Rechteck mit einem um ``faktor`` dunkleren Rand — Kanten bleiben
    lesbar, auch wenn zwei Felder direkt aneinanderstossen."""
    _rechteck(px, breite, hoehe, x0, y0, x1, y1, farbe)
    xa, xb = sorted((max(0, int(round(x0))), min(breite, int(round(x1)))))
    ya, yb = sorted((max(0, int(round(y0))), min(hoehe, int(round(y1)))))
    if xa >= xb or ya >= yb:
        return
    rand = _dunkler(farbe)
    for x in range(xa, xb):
        px[ya * breite + x] = rand
        px[(yb - 1) * breite + x] = rand
    for y in range(ya, yb):
        px[y * breite + xa] = rand
        px[y * breite + (xb - 1)] = rand


# ====================================================================================
# Regel 1 — Lizenz: backbone.waehle(kommerziell=True) gibt FLUX-dev nie zurück
# ====================================================================================

def pruefe_regel1() -> dict:
    """Echte Registry, echte Auswahl, echtes Urteil je Eintrag — nichts davon abgeschrieben."""
    namen = list(backbone.BACKBONES.keys())          # Registry-Reihenfolge, wie sie ist
    gewaehlt = {b.name for b in backbone.waehle(kommerziell=True)}

    zeilen = []
    for name in namen:
        eintrag = backbone.BACKBONES[name]
        urteil = backbone.pruefe_lizenz(name)
        zeilen.append({
            "name": name,
            "kommerziell_nutzbar": eintrag.kommerziell_nutzbar,
            "zulaessig": urteil["zulaessig"],
            "n_auflagen": len(urteil["auflagen"]),
            "in_waehle": name in gewaehlt,
        })

    flux_namen = [n for n in namen if "flux1-dev" in n or "flux2-dev" in n]
    flux_in_waehle = [n for n in flux_namen if n in gewaehlt]
    if flux_in_waehle:
        # Das wäre kein Darstellungsfehler, sondern ein echter Regel-1-Verstoss dieses
        # Laufs — er gehört laut abgebrochen, nicht schön eingefärbt.
        raise RuntimeError(
            f"REGEL-1-VERSTOSS: waehle(kommerziell=True) enthält {flux_in_waehle} — "
            f"Non-Commercial-Gewichte in einer als kommerziell nutzbar deklarierten Auswahl."
        )

    return {
        "n_registry": len(namen),
        "n_gewaehlt": len(gewaehlt),
        "n_ausgeschlossen": len(namen) - len(gewaehlt),
        "flux_namen": flux_namen,
        "zeilen": zeilen,
    }


def zeichne_regel1(befund: dict) -> tuple:
    zeilen = befund["zeilen"]
    n = len(zeilen)
    row_h, gap = 56, 8
    breite = 900
    hoehe = gap + n * (row_h + gap)
    px = _neues_bild(breite, hoehe)

    for i, z in enumerate(zeilen):
        y0 = gap + i * (row_h + gap)
        y1 = y0 + row_h

        # Spalte 0: neutrale Marke — ist dieser Eintrag einer der beiden FLUX-dev-Fälle,
        # auf die sich die Behauptung des Auftrags ausdrücklich bezieht?
        ist_flux_dev = z["name"] in befund["flux_namen"]
        _rahmen(px, breite, hoehe, 0, y0, 40, y1,
               FARBE_MARKE if ist_flux_dev else FARBE_HINTERGRUND)

        # Spalte 1 (breit): die Lizenz-Ampel aus dem echten pruefe_lizenz()-Urteil.
        if not z["kommerziell_nutzbar"] or not z["zulaessig"]:
            ampel = FARBE_ROT
        elif z["n_auflagen"] > 0:
            ampel = FARBE_GELB
        else:
            ampel = FARBE_GRUEN
        _rahmen(px, breite, hoehe, 55, y0, breite * 0.68, y1, ampel)

        # Spalte 2 (schmal): steht dieser Name echt in waehle(kommerziell=True)?
        marker = FARBE_GRUEN if z["in_waehle"] else FARBE_ROT
        _rahmen(px, breite, hoehe, breite * 0.72, y0, breite - 10, y1, marker)

    return px, breite, hoehe


# ====================================================================================
# Regel 2 — Prozessgrenze: nach einem Kettenlauf ist weder bpy noch ifcopenshell
# in sys.modules
# ====================================================================================

def pruefe_regel2() -> dict:
    """IFC -> glb ECHT über .venv-ifc; glb -> Multipass ECHT über Blender, sofern
    :data:`ENV_BLENDER` gesetzt ist (Kollisionsschutz, siehe Modulkopf)."""
    arbeits_dir = Path(tempfile.mkdtemp(prefix="aiimaging-beweis19-regel2-"))
    ifc_path = arbeits_dir / "testbau.ifc"
    glb_path = arbeits_dir / "testbau.glb"

    erzeuger = subprocess.run(
        [sys.executable, str(WURZEL / "tools" / "make_test_ifc.py"), str(ifc_path)],
        capture_output=True, text=True, timeout=60)
    if erzeuger.returncode != 0:
        raise RuntimeError(
            f"make_test_ifc.py fehlgeschlagen (Regel 3 liefert die Testgeometrie): "
            f"{(erzeuger.stderr or erzeuger.stdout)[-500:]}"
        )

    bericht_geometrie = seams.ifc_zu_glb(str(ifc_path), str(glb_path))
    ifcopenshell_geladen = "ifcopenshell" in sys.modules
    if bericht_geometrie.get("status") != "ok":
        raise RuntimeError(
            f"seams.ifc_zu_glb meldete {bericht_geometrie.get('status')!r}: "
            f"{bericht_geometrie.get('error')}"
        )

    mit_blender = os.environ.get(ENV_BLENDER) == "1"
    bpy_status = "uebersprungen"
    bpy_geladen = None
    multipass_fehler = None
    if mit_blender:
        multipass_dir = arbeits_dir / "multipass"
        try:
            bericht_multipass = seams.glb_zu_multipass(
                str(glb_path), multipass_dir,
                up_axis=bericht_geometrie.get("up_axis", "Y"),
                aufloesung=64, samples=4, beauty=False, material_id=False,
                herzschlag_takt_s=None,
            )
            if bericht_multipass.get("status") not in (None, "ok"):
                multipass_fehler = (
                    f"Multipass meldete {bericht_multipass.get('status')!r}: "
                    f"{bericht_multipass.get('error')}"
                )
        finally:
            bpy_geladen = "bpy" in sys.modules
            bpy_status = "gemessen"

    return {
        "arbeits_dir": str(arbeits_dir),
        "bbox": bericht_geometrie.get("bbox"),
        "n_elements": bericht_geometrie.get("n_elements"),
        "ifcopenshell_geladen": ifcopenshell_geladen,
        "bpy_status": bpy_status,
        "bpy_geladen": bpy_geladen,
        "multipass_fehler": multipass_fehler,
    }


def zeichne_regel2(befund: dict) -> tuple:
    breite, row_h, gap = 700, 90, 14
    hoehe = gap + 2 * (row_h + gap)
    px = _neues_bild(breite, hoehe)

    # Zeile 1: ifcopenshell — IMMER echt gemessen.
    y0 = gap
    farbe = FARBE_ROT if befund["ifcopenshell_geladen"] else FARBE_GRUEN
    _rahmen(px, breite, hoehe, gap, y0, breite - gap, y0 + row_h, farbe)

    # Zeile 2: bpy — gemessen nur mit gesetztem Kollisionsschutz-Flag, sonst grau.
    y0 = gap + (row_h + gap)
    if befund["bpy_status"] == "uebersprungen":
        farbe = FARBE_GRAU
    else:
        farbe = FARBE_ROT if befund["bpy_geladen"] else FARBE_GRUEN
    _rahmen(px, breite, hoehe, gap, y0, breite - gap, y0 + row_h, farbe)

    return px, breite, hoehe


# ====================================================================================
# Regel 3 — keine echten Projektdaten / keine Namen in Pfaden: der bestehende
# Regel-3-Wächter über git ls-files, unverändert nachgeladen.
# ====================================================================================

def _lade_regel3_waechter():
    """``tests/test_regel3_kennungen.py`` als Modul laden — OHNE die Datei zu ändern
    und ohne ihre Suchmuster zu kopieren. Der Wächter, den dieser Beweis benutzt, ist
    also wortwörtlich derselbe, den ``pytest`` auch prüft."""
    pfad = WURZEL / "tests" / "test_regel3_kennungen.py"
    spec = importlib.util.spec_from_file_location("beweis19_regel3_geladen", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def pruefe_regel3() -> dict:
    """Dieselbe Suche wie
    ``test_im_ganzen_repo_steht_kein_benutzername_in_einem_pfad`` — hier nur gezählt
    statt mit ``assert`` quittiert, weil dieser Beweis eine Zahl braucht, kein
    Testergebnis."""
    modul = _lade_regel3_waechter()
    dateien = modul._versionierte_textdateien()

    funde: list[str] = []
    for pfad in dateien:
        rel = str(pfad.relative_to(WURZEL))
        if rel in modul.AUSGENOMMEN:
            continue
        try:
            text = pfad.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for treffer in modul.SUCHE.finditer(text):
            name = treffer.group(1) or treffer.group(2)
            if name not in modul.ERLAUBT:
                funde.append(f"{rel}: {treffer.group(0)}")
        for treffer in modul.SUCHE_VOR_DEM_REPO.finditer(text):
            name = modul._vor_dem_repo(treffer.group(1))
            if name not in modul.ERLAUBT and name not in modul.ERLAUBT_VOR_DEM_REPO:
                funde.append(f"{rel}: {treffer.group(0)}")

    return {"n_dateien": len(dateien), "funde": funde}


def zeichne_regel3(befund: dict) -> tuple:
    breite, hoehe = 900, 220
    px = _neues_bild(breite, hoehe)

    rand = 30
    balken_breite_max = breite - 2 * rand

    # Balken 1: geprüfte Dateien — 1 Bildpunkt je Datei, gedeckelt auf die Leinwand.
    n_dateien_px = min(befund["n_dateien"], balken_breite_max)
    _rahmen(px, breite, hoehe, rand, 40, rand + n_dateien_px, 100, (70, 100, 150))

    # Balken 2: Treffer — 40 Bildpunkte je Treffer, damit auch ein einziger Treffer
    # unübersehbar würde. Null Treffer bleiben ein schmaler Rahmen ohne Füllung.
    n_funde = len(befund["funde"])
    if n_funde == 0:
        _rahmen(px, breite, hoehe, rand, 140, rand + 6, 200, FARBE_GRUEN)
    else:
        treffer_px = min(n_funde * 40, balken_breite_max)
        _rahmen(px, breite, hoehe, rand, 140, rand + treffer_px, 200, FARBE_ROT)

    return px, breite, hoehe


# ====================================================================================
# Regel 4 — Bibliothek ohne Oberfläche: ein frischer Interpreter importiert
# aiimaging, ohne MCP-SDK, torch oder ein UI-Framework zu laden.
# ====================================================================================

#: Was in ``sys.modules`` eines frischen ``import aiimaging`` NICHT stehen darf.
#: ``mcp`` ist das MCP-SDK (``aiimaging.mcp_server`` importiert es NUR innerhalb einer
#: Funktion, siehe dessen Modul-Docstring); die übrigen sind GUI-Bibliotheken.
VERBOTENE_MARKER = (
    "bpy", "ifcopenshell", "torch", "mcp",
    "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6",
    "gradio", "streamlit", "kivy", "wx",
)


def pruefe_regel4() -> dict:
    """Ein zweiter, frischer Prozess importiert ``aiimaging`` — dieser Prozess hier
    (der schon lange läuft und selbst ``aiimaging`` importiert hat, siehe Modulkopf)
    wäre keine ehrliche Probe."""
    code = (
        "import sys, json\n"
        f"sys.path.insert(0, {str(WURZEL / 'src')!r})\n"
        "import aiimaging\n"
        "print(json.dumps(sorted(sys.modules)))\n"
    )
    lauf = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          timeout=60)
    if lauf.returncode != 0:
        raise RuntimeError(f"'import aiimaging' im frischen Interpreter scheiterte:\n"
                           f"{lauf.stderr[-1000:]}")
    module = json.loads(lauf.stdout)

    gefunden = {}
    for marker in VERBOTENE_MARKER:
        treffer = [m for m in module if m == marker or m.startswith(marker + ".")]
        gefunden[marker] = treffer

    return {"n_module": len(module), "gefunden": gefunden}


def zeichne_regel4(befund: dict) -> tuple:
    marker = list(VERBOTENE_MARKER)
    n = len(marker)
    breite, hoehe = 900, 220
    px = _neues_bild(breite, hoehe)

    # Reihe kleiner Felder, eines je verbotenem Marker — grün wenn abwesend (Vorgabe
    # und einziger Fall in einem intakten Lauf), rot wenn tatsächlich geladen.
    feld_breite = (breite - 2 * 20) / n
    for i, name in enumerate(marker):
        x0 = 20 + i * feld_breite
        x1 = x0 + feld_breite * 0.85
        farbe = FARBE_ROT if befund["gefunden"][name] else FARBE_GRUEN
        _rahmen(px, breite, hoehe, x0, 30, x1, 110, farbe)

    # Balken darunter: Grösse des geladenen Modul-Bestands — 2 Bildpunkte je Modul,
    # gedeckelt, damit ein sehr grosser Bestand die Leinwand nicht sprengt. Zeigt,
    # dass "kein verbotener Marker" nicht durch einen leeren Import erschlichen ist.
    balken_max = breite - 2 * 20
    modul_px = min(befund["n_module"] * 2, balken_max)
    _rahmen(px, breite, hoehe, 20, 150, 20 + modul_px, 190, (90, 90, 90))

    return px, breite, hoehe


# ====================================================================================
# Ablauf
# ====================================================================================

def main() -> int:
    ziel = Path(sys.argv[1]) if len(sys.argv) > 1 else ZIEL_VORGABE
    ziel.mkdir(parents=True, exist_ok=True)
    geschrieben: list[Path] = []

    print("Regel 1 — echte Registry, echte Auswahl …")
    befund1 = pruefe_regel1()
    print(f"  Registry: {befund1['n_registry']} Einträge, "
          f"{befund1['n_gewaehlt']} in waehle(kommerziell=True), "
          f"{befund1['n_ausgeschlossen']} ausgeschlossen "
          f"(darunter: {', '.join(befund1['flux_namen'])}).")
    px, b, h = zeichne_regel1(befund1)
    name = (f"01_regel1_lizenz-ampel_registry-{befund1['n_registry']}"
            f"_gewaehlt-{befund1['n_gewaehlt']}"
            f"_ausgeschlossen-{befund1['n_ausgeschlossen']}"
            f"_flux-dev-in-waehle-False.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    print("Regel 2 — echter Kettenlauf über .venv-ifc"
          + (" und Blender" if os.environ.get(ENV_BLENDER) == "1" else " (bpy-Teil "
             "übersprungen — Kollisionsschutz, siehe Modulkopf)") + " …")
    befund2 = pruefe_regel2()
    print(f"  bbox={befund2['bbox']}, n_elements={befund2['n_elements']}, "
          f"ifcopenshell_geladen={befund2['ifcopenshell_geladen']}, "
          f"bpy_status={befund2['bpy_status']}, bpy_geladen={befund2['bpy_geladen']}")
    if befund2["multipass_fehler"]:
        print(f"  HINWEIS Multipass: {befund2['multipass_fehler']}")
    px, b, h = zeichne_regel2(befund2)
    bpy_teil = ("uebersprungen" if befund2["bpy_status"] == "uebersprungen"
                else f"abwesend-{not befund2['bpy_geladen']}")
    name = (f"02_regel2_prozessgrenze"
            f"_ifcopenshell-abwesend-{not befund2['ifcopenshell_geladen']}"
            f"_bpy-{bpy_teil}.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    print("Regel 3 — der bestehende Regel-3-Wächter über git ls-files …")
    befund3 = pruefe_regel3()
    print(f"  {befund3['n_dateien']} versionierte Textdateien geprüft, "
          f"{len(befund3['funde'])} Treffer.")
    for f in befund3["funde"][:10]:
        print(f"    FUND: {f}")
    px, b, h = zeichne_regel3(befund3)
    name = (f"03_regel3_waechter_dateien-{befund3['n_dateien']}"
            f"_treffer-{len(befund3['funde'])}.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    print("Regel 4 — frischer Interpreter, 'import aiimaging' …")
    befund4 = pruefe_regel4()
    n_verboten_gefunden = sum(1 for t in befund4["gefunden"].values() if t)
    print(f"  {befund4['n_module']} Module geladen, "
          f"{n_verboten_gefunden} von {len(VERBOTENE_MARKER)} verbotenen Markern gefunden.")
    for marker, treffer in befund4["gefunden"].items():
        if treffer:
            print(f"    VERSTOSS: {marker} -> {treffer}")
    px, b, h = zeichne_regel4(befund4)
    name = (f"04_regel4_bibliothek_module-{befund4['n_module']}"
            f"_verboten-{n_verboten_gefunden}.png")
    pfad = ziel / name
    bildschreiben.schreibe_farb_png(pfad, px, b, h)
    geschrieben.append(pfad)

    for p in geschrieben:
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
