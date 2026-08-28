"""Der Ausführende auf der HomeStation — Hardware-Schranke, Render-Pfad, Ablauf.

``tools/homeworker.py`` ist das einzige Stück dieses Projekts, das **unbeaufsichtigt**
läuft, und es läuft an einer Hardwareschranke: Die RTX 5090 löst unter ungebremster
Volllast die Netzteil-Schutzschaltung aus. Niemand sitzt daneben, der eine falsche
Freigabe abfangen könnte. Genau deshalb steht hier der Schwerpunkt auf der Zusage
*fail-closed*: Lässt sich der Zustand der Karte nicht feststellen, wird **abgelehnt**,
nicht geraten (``auftraege/README.md``, Abschnitt „Die Hardware-Schranke").

Geprüft wird ohne GPU, ohne Blender, ohne ``torch`` und ohne ein einziges Gewicht —
alles über die Nähte, die das Skript dafür mitbringt:

* ``nvidia-smi`` wird über ``shutil.which``/``subprocess.run`` ersetzt. Ein Test, der
  eine echte Karte bräuchte, liefe nie und belegte darum nichts.
* ``fuehre_aus(..., _render_modell=…, _tiefen_modell=…)`` reicht fertige Modelle durch.
  Der Render-Pfad ``_render_und_qa`` wird direkt mit einem selbst gebauten
  Blender-Bericht gerufen; damit braucht kein Test Blender.
* ``seams.ifc_zu_glb`` und ``seams.glb_zu_tiefenkarte`` werden nur dort ersetzt, wo der
  **ganze** Weg durch ``fuehre_aus`` gemeint ist.

Alle Bilddaten sind synthetisch und hier erzeugt (Regel 3). Es wird kein echter Prozess
gestartet und nichts ins Repo geschrieben.

Was hier **nicht** belegt ist: dass die Karte auf der HomeStation tatsächlich unter
120 W leerläuft, dass ein echter Render geometrietreu ist, oder dass die Schwelle 0.65
auf dieser Naht trägt. Das kann nur die HomeStation (``docs/PLAN.md``, Phase 4).
"""
from __future__ import annotations

import json
import importlib.util
import math
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import REPO

from aiimaging import bildlesen, bildschreiben, geometrie_qa, render, seams, tiefenschaetzer


def _lade_homeworker():
    """``tools/`` ist kein Paket — das Skript wird über seinen Pfad geladen.

    Ein ``sys.path``-Eintrag auf ``tools/`` täte es auch, würde aber jedem anderen Test
    das Verzeichnis unterschieben. Der Ladevorgang über die Datei bleibt lokal.
    """
    pfad = REPO / "tools" / "homeworker.py"
    spec = importlib.util.spec_from_file_location("homeworker", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("homeworker", modul)
    spec.loader.exec_module(modul)
    return modul


hw = _lade_homeworker()

#: Ein paar Bytes mit PNG-Signatur. Wo nur die Existenz einer Datei geprüft wird, ist
#: mehr nicht nötig — und ein echtes Bild belegte nichts zusätzlich.
PNG_PLATZHALTER = b"\x89PNG\r\n\x1a\n"

#: Die Auflagen, wie ``auftrag.baue_auftrag`` sie jedem Auftrag mitgibt.
AUFLAGEN = {
    "leistungsgrenze_w": 400,
    "nur_bei_leerlauf": True,
    "leerlauf_schwelle_w": 120,
    "leerlauf_schwelle_mem_gb": 8,
}


# ══ Doppelgänger ═════════════════════════════════════════════════════════════════════

class Prozess:
    """Doppelgänger eines ``subprocess.CompletedProcess`` — nur, was ausgelesen wird."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def smi_zeile(*, name="NVIDIA GeForce RTX 5090", leistung_w=25.0, speicher_mb=512.0,
              gesamt_mb=32768.0, grenze_w=400.0) -> str:
    """Eine Zeile im Format ``--format=csv,noheader,nounits``, wie die Karte sie liefert."""
    return f"{name}, {leistung_w}, {speicher_mb}, {gesamt_mb}, {grenze_w}\n"


@pytest.fixture
def smi(monkeypatch):
    """Ersetzt den Aufruf von ``nvidia-smi``. Ohne diese Naht wäre die Schranke nur dort
    prüfbar, wo eine RTX 5090 steckt — also praktisch nirgends."""

    def stelle_ein(*, vorhanden=True, returncode=0, stdout=None, wirft=None):
        monkeypatch.setattr(hw.shutil, "which",
                            lambda n: f"/usr/bin/{n}" if vorhanden else None)

        def gefaelscht(cmd, **kw):
            if wirft is not None:
                raise wirft
            return Prozess(returncode, smi_zeile() if stdout is None else stdout)

        monkeypatch.setattr(hw.subprocess, "run", gefaelscht)

    return stelle_ein


@pytest.fixture(autouse=True)
def keine_fremden_prozesse(monkeypatch):
    """Vorgabe für jeden Test: keine GPU, kein Blender, kein Subprozess.

    ``_umgebung()`` ruft in fast jedem Pfad ``gpu_zustand()``. Ohne diese Vorgabe hinge
    das Ergebnis eines Tests davon ab, ob auf dem Rechner zufällig ein ``nvidia-smi``
    liegt — der Test bewiese dann auf zwei Rechnern Verschiedenes.
    """
    monkeypatch.setattr(hw.shutil, "which", lambda n: None)

    def verboten(cmd, **kw):
        raise AssertionError(f"Kein Test darf einen Prozess starten: {cmd!r}")

    monkeypatch.setattr(hw.subprocess, "run", verboten)


# ══ A · Die Hardware-Schranke ════════════════════════════════════════════════════════
#
# Der sicherheitskritische Teil. Ein übersprungener Auftrag kostet Wartezeit, ein
# abgestürzter Rechner mehr — jede Unsicherheit muss darum zur Ablehnung führen.

def test_gpu_zustand_liest_die_werte_der_karte(smi):
    """Die Gegenprobe zu allen Ablehnungen: Im Normalfall wird wirklich etwas gelesen.

    Ohne sie prüften die Tests unten nur, dass diese Funktion immer ``verfuegbar=False``
    meldet — und wären vakuös.
    """
    smi()

    z = hw.gpu_zustand()

    assert z["verfuegbar"] is True
    assert z["name"] == "NVIDIA GeForce RTX 5090"
    assert z["leistung_w"] == 25.0
    assert z["speicher_belegt_gb"] == pytest.approx(0.5)      # 512 MB
    assert z["speicher_gesamt_gb"] == pytest.approx(32.0)
    assert z["leistungsgrenze_w"] == 400.0


#: Jede Art, auf die die Auskunft über die Karte ausbleiben kann. Alle müssen zu
#: „Zustand unbekannt" führen — nicht zu einem Absturz und nicht zu einem stillen True.
FEHLBILDER = {
    "nvidia-smi fehlt": {"vorhanden": False},
    "Rückgabewert ungleich 0": {"returncode": 9},
    "unverständliche Ausgabe": {"stdout": "Failed to initialize NVML\n"},
    "zu wenige Felder": {"stdout": "RTX 5090, 25.0\n"},
    "Zahl ist keine Zahl": {"stdout": "RTX 5090, k.A., 512, 32768, 400\n"},
    "Timeout": {"wirft": subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=30)},
    "nicht ausführbar": {"wirft": OSError("Exec format error")},
    "Subprozessfehler": {"wirft": subprocess.SubprocessError("kaputt")},
}


@pytest.mark.parametrize("fall", list(FEHLBILDER), ids=list(FEHLBILDER))
def test_unauskunftsfaehige_karte_gilt_als_unbekannt(smi, fall):
    """Kein Fehlbild darf als Ausnahme aus ``gpu_zustand`` herausfallen.

    Ein Traceback hier bräche den ganzen Stapellauf ab; das Skript soll aber den
    einzelnen Auftrag ablehnen und weiterlaufen.
    """
    smi(**FEHLBILDER[fall])

    z = hw.gpu_zustand()

    assert z["verfuegbar"] is False
    assert z["grund"], "Eine Ablehnung ohne Grund ist auf der HomeStation nicht zu lesen"


@pytest.mark.parametrize("fall", list(FEHLBILDER), ids=list(FEHLBILDER))
def test_unbekannter_zustand_startet_nichts(smi, fall):
    """Das Herzstück der Zusage: unbekannt → nicht starten. Für **jedes** Fehlbild.

    Der Weg geht bewusst über ``gpu_zustand()`` statt über ein von Hand gebautes
    Wörterbuch: Geprüft werden soll die Kette, nicht eine Annahme über sie.
    """
    smi(**FEHLBILDER[fall])

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is False
    assert "unbekannt" in grund


def test_leere_ausgabe_von_nvidia_smi_gilt_als_unbekannt(smi):
    """``nvidia-smi`` mit Code 0 und leerer Ausgabe — der Fall „Treiber lädt noch".

    Er gehört zu denselben Fehlbildern wie die oben und muss zur Ablehnung führen.
    Tatsächlich fliegt ein ``IndexError`` bis in ``main()`` und reisst über
    ``_umgebung()`` auch jeden anderen Pfad mit.
    """
    smi(stdout="")

    assert hw.gpu_zustand()["verfuegbar"] is False


# ── Die Grenzwerte selbst ────────────────────────────────────────────────────────────
#
# Genau auf der Schwelle, knapp darüber, knapp darunter. Dort wohnen die Fehler.

@pytest.mark.parametrize("leistung_w, erwartet_frei", [
    (119.9, True),      # knapp darunter — die Karte ist frei
    (120.0, False),     # genau auf der Schwelle — '>=' schliesst sie ein
    (120.1, False),     # knapp darüber
])
def test_leistungsschwelle_an_ihrer_kante(smi, leistung_w, erwartet_frei):
    """Die Schwelle ist einschliessend gemeint: 120 W gelten schon als belegt."""
    smi(stdout=smi_zeile(leistung_w=leistung_w))

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is erwartet_frei
    if not frei:
        assert "nicht frei" in grund


@pytest.mark.parametrize("speicher_mb, erwartet_frei", [
    (8 * 1024 - 1, True),
    (8 * 1024, False),
    (8 * 1024 + 1, False),
])
def test_speicherschwelle_an_ihrer_kante(smi, speicher_mb, erwartet_frei):
    """8 GB belegt heisst: da liegt ein fremdes Modell. Auch exakt 8 GB."""
    smi(stdout=smi_zeile(speicher_mb=float(speicher_mb)))

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is erwartet_frei
    if not frei:
        assert "fremdes Modell" in grund


@pytest.mark.parametrize("grenze_w, erwartet_frei", [
    (400.0, True),      # gesetzt wie gefordert
    (401.0, True),      # die eine Watt Toleranz gegen Rundung im Treiber
    (402.0, False),     # darüber ist die Schranke offen
    (600.0, False),     # Werkseinstellung der 5090 — der gefährliche Fall
])
def test_leistungsgrenze_an_ihrer_kante(smi, grenze_w, erwartet_frei):
    """Eine zu hohe Leistungsgrenze ist der Fall, für den es die Schranke gibt."""
    smi(stdout=smi_zeile(grenze_w=grenze_w))

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is erwartet_frei
    if not frei:
        # Die Ablehnung muss sagen, was zu tun wäre — sonst steht der Betrieb ratlos da.
        assert f"sudo nvidia-smi -pl {AUFLAGEN['leistungsgrenze_w']}" in grund


def test_freie_karte_wird_freigegeben_und_die_begruendung_sagt_warum(smi):
    """Auch das Ja braucht seinen Grund: Im Protokoll steht sonst nur „gestartet"."""
    smi()

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is True
    assert "frei" in grund and "Leistungsgrenze" in grund


def test_ohne_auflagen_gelten_die_belegten_werte_des_projekts(smi):
    """Ein Auftrag ohne Auflagen darf nicht milder behandelt werden als einer mit.

    Die Vorgaben kommen aus ``auftrag.py`` (KosmoVis-Bericht 2026-06-30) und nicht aus
    einer zweiten, hier getippten Zahl.
    """
    smi(stdout=smi_zeile(leistung_w=float(hw.auf.GPU_LEERLAUF_W)))

    assert hw.darf_starten(hw.gpu_zustand(), {})[0] is False


def test_belegte_karte_wird_abgelehnt_obwohl_die_leistungsgrenze_stimmt(smi):
    """Gegenprobe: Die Ablehnung hängt an der Belegung, nicht an der Grenze."""
    smi(stdout=smi_zeile(leistung_w=310.0, speicher_mb=20000.0, grenze_w=400.0))

    frei, grund = hw.darf_starten(hw.gpu_zustand(), AUFLAGEN)

    assert frei is False
    assert "310 W" in grund


# ── Die Zweige, in denen die Zusage nicht hält ───────────────────────────────────────

def test_abgeschaltetes_leerlauf_gate_prueft_die_leistungsgrenze_weiterhin(smi):
    """Die beiden Auflagen sind zwei — und die gefährlichere ist die Leistungsgrenze.

    ``nur_bei_leerlauf: false`` heisst „ich weiss, dass da noch etwas läuft", nicht
    „renn ohne Schranke". Genau ungebremste Volllast löst die Schutzschaltung aus.
    """
    smi(stdout=smi_zeile(grenze_w=600.0))

    frei, _ = hw.darf_starten(hw.gpu_zustand(), {**AUFLAGEN, "nur_bei_leerlauf": False})

    assert frei is False


def test_abgeschaltetes_leerlauf_gate_startet_nicht_bei_unbekanntem_zustand(smi):
    """Fail-closed heisst: ohne Auskunft kein Start. Auch mit abgeschaltetem Gate.

    Reproduktion: ``darf_starten({'verfuegbar': False, 'grund': '…'},
    {'nur_bei_leerlauf': False})`` → ``(True, 'Leerlauf-Gate im Auftrag abgeschaltet')``.
    Die Prüfung ``if not zustand.get('verfuegbar')`` steht eine Zeile zu spät.
    """
    smi(vorhanden=False)

    frei, _ = hw.darf_starten(hw.gpu_zustand(), {**AUFLAGEN, "nur_bei_leerlauf": False})

    assert frei is False


def test_unbekannte_leistungsgrenze_wird_abgelehnt():
    """Ein Zustand ohne Leistungsgrenze ist ein unvollständiger Zustand.

    ``zustand.get('leistungsgrenze_w', 0) > soll + 1`` liest die fehlende Angabe als
    0 W — also als die denkbar bravste Karte. Fail-closed wäre die Ablehnung.
    """
    zustand = {"verfuegbar": True, "name": "RTX 5090",
               "leistung_w": 20.0, "speicher_belegt_gb": 0.4}

    assert hw.darf_starten(zustand, AUFLAGEN)[0] is False


# ══ B · Der Render-Pfad `_render_und_qa` ═════════════════════════════════════════════
#
# Er wurde am 18.08.2026 gebaut und ist noch nie gelaufen. Hier läuft er zum ersten Mal
# — ohne GPU und ohne ein einziges Gewicht, über die beiden Modell-Nähte.

#: Masse der synthetischen Szene. 16×16 reicht: geometrie_qa verlangt mindestens 32
#: gemeinsame Punkte (MIN_GEMEINSAME_PUNKTE), und das Bild bleibt trotzdem lesbar klein.
BREITE = HOEHE = 16

#: Ein quaderförmiger „Bau" vor unendlich fernem Hintergrund.
BLOCK_ZEILEN = range(2, 14)
BLOCK_SPALTEN = range(4, 12)


#: Farben des Material-ID-Passes. Dieselbe Gestalt wie in ``tests/test_maske.py``:
#: ein Geländeeintrag, der nach der Regel herausfällt, und ein Bauteil, das bleibt.
MI_HINTERGRUND = (0, 0, 0)
MI_BODEN = (255, 38, 38)
MI_WAND = (165, 255, 38)


def _material_id_bild() -> list[tuple[int, int, int]]:
    """Der Material-ID-Pass zur Soll-Karte: derselbe Block, als Bauteil eingefärbt.

    Die unterste Zeile des Blocks ist **Gelände** — sonst prüfte die Geländeregel hier
    nichts, und die Maske wäre nur eine zweite Silhouette unter anderem Namen.
    """
    farben = [MI_HINTERGRUND] * (BREITE * HOEHE)
    for zeile in BLOCK_ZEILEN:
        for spalte in BLOCK_SPALTEN:
            farben[zeile * BREITE + spalte] = (
                MI_BODEN if zeile == BLOCK_ZEILEN.stop - 1 else MI_WAND)
    return farben


def _soll_meter() -> list[float]:
    """Die Soll-Tiefenkarte in Metern, zeilenweise von oben — Hintergrund als ``inf``.

    Die Tiefe steigt nur mit der **Spalte**. Damit gibt es eine eindeutige Tiefenordnung
    und trotzdem viele Bindungen, also genau die Lage, für die ``spearman`` bindungs-
    korrekt gerechnet wird.
    """
    werte = [float("inf")] * (BREITE * HOEHE)
    for zeile in BLOCK_ZEILEN:
        for spalte in BLOCK_SPALTEN:
            werte[zeile * BREITE + spalte] = 3.0 + 0.25 * (spalte - BLOCK_SPALTEN.start)
    return werte


class Renderattrappe:
    """Ein Bildmodell aus vier Zeilen — dieselbe Naht wie ``modell`` in ``render.rendere``."""

    def __init__(self):
        self.aufrufe: list[dict] = []

    def __call__(self, parameter: dict):
        self.aufrufe.append(parameter)
        Path(parameter["ausgabe_png"]).write_bytes(PNG_PLATZHALTER)
        return parameter["ausgabe_png"]


class Tiefenattrappe:
    """Ein Tiefenschätzer, der eine vorgegebene Karte zurückgibt."""

    def __init__(self, werte):
        self.werte = list(werte)
        self.aufrufe: list[dict] = []

    def __call__(self, parameter: dict):
        self.aufrufe.append(parameter)
        return self.werte


class Verboten:
    """Ein Modell, das nicht gerufen werden darf. Es meldet sich, wenn doch."""

    def __init__(self, wofuer: str):
        self.wofuer = wofuer

    def __call__(self, parameter: dict):
        raise AssertionError(f"{self.wofuer} hätte hier nicht gerufen werden dürfen")


@pytest.fixture
def aus(tmp_path) -> Path:
    """Das Arbeitsverzeichnis auf der HomeStation. Es bleibt dort — Regel 3."""
    verzeichnis = tmp_path / "build" / "auf-20260818-99"
    verzeichnis.mkdir(parents=True)
    return verzeichnis


@pytest.fixture
def bericht(aus) -> dict:
    """Ein Blender-Bericht, wie ``seams.glb_zu_tiefenkarte`` ihn zurückgibt.

    Das Tiefen-PNG ist ein echtes 16-Bit-Graustufenbild aus ``bildschreiben`` — so
    läuft ``bildlesen.tiefen_aus_report`` im Test wirklich und nicht als Attrappe. Die
    EXR fehlt bewusst: Ihr Weg führte über Blender, und den gibt es hier nicht.
    """
    grau, normalisierung = bildschreiben.normalisiere_tiefe(_soll_meter())
    bildschreiben.schreibe_graustufen_png(aus / "tiefe_norm.png", grau, BREITE, HOEHE)
    (aus / "beauty.png").write_bytes(PNG_PLATZHALTER)
    # DER MATERIAL-ID-PASS GEHOERT DAZU — bis zum 26.08.2026 fehlte er hier.
    #
    # Der echte Lauf liefert ihn (er steht in `homeworker._PFADFELDER`), diese Attrappe
    # nicht. Damit lief jeder Test dieses Moduls in einer Welt, in der sich gar keine
    # Bauwerksmaske bauen laesst — und die Luecke im Maskenweg konnte hier nicht auffallen.
    # Dieselbe Sorte Fehler wie eine Attrappe, die eine Datei VORTAEUSCHT: Sie prueft die
    # Kette gegen eine Welt, in der sie nicht laeuft.
    bildschreiben.schreibe_farb_png(aus / "material_id.png", _material_id_bild(),
                                    BREITE, HOEHE)
    return {
        "depth_exr": None,
        "depth_png": str(aus / "tiefe_norm.png"),
        "depth_normalisierung": normalisierung,
        "depth_png_fehler": None,
        "depth_exr_kanaele": ["tiefe_.V"],
        "depth_exr_format": "MULTILAYER",
        "beauty_png": str(aus / "beauty.png"),
        "material_id_png": str(aus / "material_id.png"),
        "material_id_tabelle": [
            {"index": 0, "name": "Boden_Platte", "farbe_srgb_8bit": list(MI_BODEN),
             "quelle": "material"},
            {"index": 1, "name": "IfcWall_0QOeb014", "farbe_srgb_8bit": list(MI_WAND),
             "quelle": "material"},
        ],
        "bbox_size_m": [8.0, 5.0, 3.0],
        "n_meshes": 7,
    }


GLB_BERICHT = {"status": "ok", "glb_path": "/ai/bau.glb", "up_axis": "Y",
               "n_elements": 7, "n_triangles": 4242}


def satz(art: str = "render") -> dict:
    """Der Auftragssatz. ``_render_und_qa`` liest daraus nur die Kennung."""
    return {"auftrag_id": "auf-20260818-99", "art": art,
            "geometrie": {"synthetisch": True}, "params": {}}


def rufe_render_und_qa(bericht, aus, params, *, render_modell=None, tiefen_modell=None):
    """``_render_und_qa`` direkt rufen — ohne Blender, ohne IFC, ohne glb."""
    return hw._render_und_qa(
        satz(), bericht, GLB_BERICHT, aus, params, time.monotonic(),
        _render_modell=render_modell, _tiefen_modell=tiefen_modell)


def treue_ist_karte(bericht) -> list[float]:
    """Eine Ist-Karte, die dem Soll exakt folgt — als Disparität (nah = grosser Wert).

    Sie wird aus der **zurückgelesenen** Soll-Karte gebaut, nicht aus den Metern von
    oben: Das PNG ist verlustbehaftet, und eine Ist-Karte, die genauer wäre als das,
    was der Massstab hergibt, prüfte einen Fall, den es nicht gibt.
    """
    soll, _, _ = bildlesen.tiefen_aus_report(bericht)
    return [1.0 / t if math.isfinite(t) else 0.0 for t in soll]


def verschobene_ist_karte(bericht, versatz: int = 4) -> list[float]:
    """Dieselbe Kubatur, aber um vier Spalten versetzt — das Muster „erfundene Kubatur".

    Die Tiefenordnung stimmt, die Silhouette liegt woanders. Genau dafür ist das
    geometrische Mittel aus Rangkorrelation und Überdeckung gebaut.
    """
    soll, _, _ = bildlesen.tiefen_aus_report(bericht)
    ist = [0.0] * len(soll)
    for zeile in range(HOEHE):
        for spalte in range(BREITE):
            if math.isfinite(soll[zeile * BREITE + spalte]):
                ist[zeile * BREITE + spalte + versatz] = 1.0 + 0.1 * spalte
    return ist


# ── Der Abbruch vor dem Render ───────────────────────────────────────────────────────

def test_ohne_tiefenkarte_wird_gar_nicht_gerendert(bericht, aus):
    """Ohne Konditionierung wäre der Render genau die erfundene Kubatur, gegen die das
    Projekt antritt. Also: kein Versuch, sondern ein Fehler mit Begründung."""
    bericht["depth_png"] = None
    bericht["depth_png_fehler"] = "EXRVarianteError: Kanal V nicht gefunden"

    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Verboten("Das Bildmodell"), tiefen_modell=Verboten("Der Schätzer"))

    assert ergebnis["status"] == "fehler"
    assert "depth_png" in ergebnis["fehler"]
    assert "render" not in ergebnis["messwerte"]
    # Der Grund des Ausfalls reist mit — sonst ist der Lauf auf der Entwicklungsseite
    # nicht zu deuten.
    assert ergebnis["messwerte"]["depth_png_fehler"].startswith("EXRVarianteError")


def test_messwerte_der_ersten_haelfte_bleiben_beim_abbruch_erhalten(bericht, aus):
    """Ein Bruch in der Mitte darf die Erkenntnis der ersten Hälfte nicht mitnehmen."""
    bericht["depth_png"] = None

    messwerte = rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus"})["messwerte"]

    assert messwerte["bbox_size_m"] == [8.0, 5.0, 3.0]
    assert messwerte["n_meshes"] == 7
    assert messwerte["n_triangles"] == 4242
    assert messwerte["depth_exr_kanaele"] == ["tiefe_.V"]


# ── Die Ablehnung des Renders ────────────────────────────────────────────────────────

def test_gegenprobe_flux_dev_steht_in_der_registry():
    """Ohne diese Probe hinge der Test unten an einem unbekannten Namen statt an Regel 1."""
    assert render.backbone.hole("flux1-dev").kommerziell_nutzbar is False


def test_unzulaessiges_backbone_erreicht_die_qa_stufe_nicht(bericht, aus):
    """Regel 1 entscheidet vor der Messung — und die Mängel gehören ins Ergebnis.

    Stünde dort nur „fehler", müsste jemand auf der HomeStation nachsehen, warum. Der
    Sinn des Übergabeprotokolls ist gerade, dass er das nicht muss.
    """
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus", "backbone": "flux1-dev"},
        tiefen_modell=Verboten("Der Tiefenschätzer"))

    assert ergebnis["status"] == "fehler"
    assert ergebnis["messwerte"]["render"]["status"] == "abgelehnt"
    assert any("kommerzielle Nutzung" in m for m in ergebnis["messwerte"]["render"]["maengel"])
    assert "geometrie_qa" not in ergebnis["messwerte"]
    assert ergebnis["urteil"]["render"] == "abgelehnt"


def test_leerer_prompt_wird_zur_ablehnung(bericht, aus):
    """Die Vorgabe für ``prompt`` ist der leere Text — und ein leerer Prompt ist ein
    Mangel. Ein Auftrag ohne ``params.prompt`` rendert also nichts."""
    ergebnis = rufe_render_und_qa(bericht, aus, {})

    assert ergebnis["status"] == "fehler"
    assert any("Prompt ist leer" in m for m in ergebnis["messwerte"]["render"]["maengel"])


def test_gescheitertes_bildmodell_wird_zum_fehler_nicht_zum_absturz(bericht, aus):
    """Ein Stapellauf über Nacht darf nicht an einem CUDA-OOM im dritten Auftrag enden."""

    def modell(parameter):
        raise RuntimeError("CUDA out of memory")

    ergebnis = rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus"},
                                  render_modell=modell,
                                  tiefen_modell=Verboten("Der Tiefenschätzer"))

    assert ergebnis["status"] == "fehler"
    assert "CUDA out of memory" in ergebnis["fehler"]


# ── Der glückliche Fall ──────────────────────────────────────────────────────────────

def test_glueckliche_kette_liefert_messwerte_und_urteil(bericht, aus):
    """Der Weg, für den es diesen Rechner gibt — hier zum ersten Mal ganz durchlaufen."""
    bildmodell = Renderattrappe()
    schaetzer = Tiefenattrappe(treue_ist_karte(bericht))

    ergebnis = rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus, Beton und Holz"},
                                  render_modell=bildmodell, tiefen_modell=schaetzer)

    assert ergebnis["status"] == "ok"
    assert ergebnis["messwerte"]["render"]["status"] == "ok"
    assert ergebnis["messwerte"]["geometrie_qa"]["status"] == "ok"
    assert ergebnis["urteil"]["score"] == pytest.approx(1.0)
    assert ergebnis["urteil"]["bestanden"] is True
    assert ergebnis["urteil"]["gemessen"] is True
    assert ergebnis["urteil"]["begruendung"]
    assert len(bildmodell.aufrufe) == 1 and len(schaetzer.aufrufe) == 1


def test_der_schaetzer_sieht_das_erzeugte_bild(bericht, aus):
    """Gemessen wird am Render, nicht an der Eingabe — sonst misst die QA sich selbst."""
    schaetzer = Tiefenattrappe(treue_ist_karte(bericht))

    rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus"},
                       render_modell=Renderattrappe(), tiefen_modell=schaetzer)

    (gesehen,) = schaetzer.aufrufe
    assert gesehen["bild_png"] == str(aus / "render.png")


def test_der_beauty_pass_geht_als_anker_in_den_render(bericht, aus):
    """Mit Ausgangsbild ist es Image-Edit, ohne wäre es txt2img — das ist der Unterschied
    zwischen „nach dem Bau" und „nach Beschreibung"."""
    bildmodell = Renderattrappe()

    rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus"},
                       render_modell=bildmodell, tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    (parameter,) = bildmodell.aufrufe
    assert parameter["beauty_png"] == str(aus / "beauty.png")
    assert parameter["modus"] == render.MODUS_IMAGE_EDIT


def test_ohne_beauty_pass_bleibt_txt2img(bericht, aus):
    """Gegenprobe: ``mit_beauty: false`` ist wirksam — sonst wäre der Schalter Zierde."""
    bildmodell = Renderattrappe()

    rufe_render_und_qa(bericht, aus, {"prompt": "Wohnhaus", "mit_beauty": False},
                       render_modell=bildmodell, tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    (parameter,) = bildmodell.aufrufe
    assert parameter["beauty_png"] is None
    assert parameter["modus"] == render.MODUS_TXT2IMG


def test_parameter_des_auftrags_erreichen_das_bildmodell(bericht, aus):
    """Ohne die vollständige Wiederholvorschrift ist ein Messwert später nicht zuzuordnen."""
    bildmodell = Renderattrappe()

    rufe_render_und_qa(
        bericht, aus,
        {"prompt": "Wohnhaus", "negativ_prompt": "Menschen", "seed": 4711,
         "schritte": 12, "controlnet_staerke": 0.55, "denoise": 0.4},
        render_modell=bildmodell, tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    (parameter,) = bildmodell.aufrufe
    assert parameter["seed"] == 4711
    assert parameter["schritte"] == 12
    assert parameter["controlnet_staerke"] == 0.55
    assert parameter["denoise"] == 0.4
    assert parameter["negativ_prompt"] == "Menschen"
    assert parameter["depth_png"] == bericht["depth_png"]


# ── Ein gerissener Schwellenwert ist ein Befund, kein Fehler ─────────────────────────

def test_gerissene_schwelle_bleibt_ein_gelungener_auftrag(bericht, aus):
    """Bewusste Entscheidung, und die leicht zu verwechselnde: ``status`` bildet ab, ob
    **gemessen** wurde — nicht, ob das Bild besteht.

    Ein durchgefallener Render als ``fehler`` machte die Auftragsliste unlesbar: Man
    sähe nicht mehr, welche Läufe kaputt und welche bloss schlecht waren.
    """
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(),
        tiefen_modell=Tiefenattrappe(verschobene_ist_karte(bericht)))

    assert ergebnis["status"] == "ok"
    assert ergebnis["urteil"]["gemessen"] is True
    assert ergebnis["urteil"]["bestanden"] is False
    assert ergebnis["urteil"]["score"] < geometrie_qa.SCHWELLE_GEOMETRIE
    assert ergebnis["fehler"] is None


def test_erfundene_kubatur_wird_im_klartext_benannt(bericht, aus):
    """Die versetzte Kubatur ist der Fall, für den die Metrik gebaut wurde — sie soll
    ihn auch benennen, nicht nur eine Zahl senken."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(),
        tiefen_modell=Tiefenattrappe(verschobene_ist_karte(bericht)))

    qa = ergebnis["messwerte"]["geometrie_qa"]
    assert qa["geom_iou"] < 1.0
    assert abs(qa["spearman"]) > 0.9
    assert any("erfundene" in w for w in qa["warnungen"])


def test_nicht_messbarer_fall_gilt_als_nicht_bestanden(bericht, aus):
    """Fail-closed auch hier: Was nicht gemessen wurde, ist nicht freigesprochen."""
    leer = [0.0] * (BREITE * HOEHE)
    leer[0] = 1.0                       # eine einzige Geometriemarke — messbar ist das nicht

    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(leer))

    assert ergebnis["urteil"]["bestanden"] is False
    assert ergebnis["urteil"]["score"] is None


def test_unpassend_lange_ist_karte_wird_nicht_stillschweigend_beschnitten(bericht, aus):
    """Abschneiden wäre eine stille Reparatur mit falschem Ergebnis.

    Die Metrik setzt Indexgleichheit voraus: derselbe Ausschnitt, dieselbe Kamera,
    dieselbe Punktreihenfolge. Eine um einen Punkt kürzere Karte verschöbe alles danach.
    """
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(),
        tiefen_modell=Tiefenattrappe([1.0] * (BREITE * HOEHE - 1)))

    assert ergebnis["status"] == "fehler"
    assert ergebnis["messwerte"]["geometrie_qa"]["status"] == "fehler"
    assert "255" in ergebnis["messwerte"]["geometrie_qa"]["error"]
    assert ergebnis["urteil"]["gemessen"] is False
    assert ergebnis["urteil"]["bestanden"] is False


# ── Die Schwelle kommt aus dem Kern ──────────────────────────────────────────────────

def test_geometrie_schwelle_stammt_aus_dem_kern():
    """Keine zweite getippte Zahl: Wer die Schwelle in Phase 4 verschiebt, verschiebt sie
    hier mit. Der Beweis ist, dass eine Änderung im Kern hier ankommt — Gleichheit
    allein bewiese nur, dass jemand denselben Wert getippt hat."""
    assert hw.geometrie_schwelle() == geometrie_qa.SCHWELLE_GEOMETRIE


def test_geaenderte_schwelle_im_kern_kommt_hier_an(monkeypatch):
    monkeypatch.setattr(geometrie_qa, "SCHWELLE_GEOMETRIE", 0.9)
    assert hw.geometrie_schwelle() == 0.9


def test_die_gemessene_schwelle_ist_die_des_kerns(bericht, aus):
    """Nicht nur die Funktion, auch der Lauf muss die Schwelle des Kerns benutzen."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    assert ergebnis["messwerte"]["geometrie_qa"]["schwelle"] == geometrie_qa.SCHWELLE_GEOMETRIE


def test_auftrag_darf_eine_eigene_schwelle_setzen(bericht, aus):
    """Für die Schwellenstudie: Der Auftrag darf die Grenze verschieben, ohne den
    Rechenweg anzufassen."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus", "schwelle": 0.999},
        render_modell=Renderattrappe(),
        tiefen_modell=Tiefenattrappe(verschobene_ist_karte(bericht)))

    assert ergebnis["messwerte"]["geometrie_qa"]["schwelle"] == 0.999
    assert ergebnis["urteil"]["bestanden"] is False


# ── Regel 1 gilt auch für die zweite Stufe ───────────────────────────────────────────

def test_gemessen_wird_mit_dem_zulaessigen_schaetzer(bericht, aus):
    """Von Depth-Anything-V2 ist nur das kleinste Modell permissiv lizenziert; die
    grösseren stehen unter CC-BY-NC-4.0 und sind damit ausgeschlossen (Regel 1)."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    benutzt = ergebnis["messwerte"]["geometrie_qa"]["schaetzer"]
    assert benutzt == tiefenschaetzer.VORGABE_TIEFENSCHAETZER
    assert tiefenschaetzer.pruefe_lizenz(benutzt)["zulaessig"] is True


def test_gegenprobe_die_groesseren_schaetzer_stehen_in_der_registry():
    """Ohne diese Probe hinge der Test unten an einem unbekannten Namen statt an der
    Lizenz — und prüfte nur, dass ein Tippfehler auffällt."""
    assert tiefenschaetzer.pruefe_lizenz("depth-anything-v2-large")["zulaessig"] is False


def test_gesperrter_schaetzer_wird_vor_dem_render_abgewiesen(bericht, aus):
    """``params.schaetzer: "depth-anything-v2-large"`` ist der wahrscheinlichste
    Fehlgriff — das grössere Modell misst besser und ist genau deshalb verlockend.
    Es ist CC-BY-NC-4.0 und unter Regel 1 ausgeschlossen.

    **Der Befund, aus dem dieser Test entstand** (18.08.2026): Die Lizenzprüfung fiel
    ursprünglich erst in der QA-Stufe — als ungefangene Ausnahme, hinter der GPU-Stunde,
    und sie nahm die Messwerte der ersten Hälfte mit.

    Die Korrektur ging weiter als der Befund verlangte. Statt die Ausnahme zu fangen und
    die erste Hälfte zu retten, entscheidet Regel 1 jetzt **vor** dem Render — dieselbe
    Reihenfolge, die ``render.rendere`` schon hat („Regel 1 entscheidet, bevor 20 GB
    Gewichte auf die GPU wandern"). Der Test prüft darum die schärfere Zusage: Es wird
    nicht nur nichts verloren, es wird gar nichts erst gerechnet.

    Regel 1 ist keine Zusatzprüfung am Ende, sondern die erste Frage.
    """
    render_attrappe = Renderattrappe()
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus", "schaetzer": "depth-anything-v2-large"},
        render_modell=render_attrappe, tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    assert ergebnis["status"] == "fehler"
    assert "Regel 1" in ergebnis["fehler"]
    assert ergebnis["urteil"]["regel_1"] == "abgelehnt"
    assert ergebnis["urteil"]["stufe"] == "vor dem Render"

    # Der eigentliche Punkt: keine GPU-Sekunde ausgegeben. Ein Ergebnis mit
    # `render.status == "ok"` wäre die schwächere Zusage und hier ausdrücklich falsch.
    assert render_attrappe.aufrufe == [], "Regel 1 fiel erst hinter der GPU-Stunde"
    assert "render" not in ergebnis["messwerte"]


# ── Regel 3: was zurück ins Repo reist ───────────────────────────────────────────────

def test_das_bild_reist_als_dateiname_nicht_als_pfad(bericht, aus):
    """Der wichtigste Test dieser Gruppe. ``bild_png`` wäre ein Pfad auf der
    HomeStation; als Name ist er genug, und nur der Name gehört ins öffentliche Repo."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    bild = ergebnis["messwerte"]["render"]["bild"]
    assert bild == "render.png"
    assert "/" not in bild and Path(bild).name == bild


def test_ergebnis_traegt_keine_bilddaten(bericht, aus):
    """``auftrag.baue_ergebnis`` wehrt Bilddaten ab — der Render-Pfad muss diese Abwehr
    überstehen, ohne dass jemand sie umgeht."""
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    # Der Beleg ist, dass baue_ergebnis nicht geworfen hat; hier die Gegenprobe, dass
    # die Abwehr überhaupt greift.
    with pytest.raises(hw.auf.AuftragError):
        hw.auf.baue_ergebnis(auftrag_id="auf-20260818-99", status="ok",
                             messwerte={"bild": "iVBORw0KGgo" + "A" * 40})
    assert ergebnis["schema"] == hw.auf.SCHEMA_ERGEBNIS


def _felder_mit(wert, verzeichnis: str, pfad: str = "messwerte") -> list[tuple[str, str]]:
    """Jedes Feld sammeln, dessen Text das Arbeitsverzeichnis nennt.

    Gesucht wird nach dem **Verzeichnis**, nicht nach jedem Schrägstrich: Ein Modellname
    wie ``Qwen/Qwen-Image-Edit-2511`` trägt auch einen, verrät aber nichts über den
    Rechner. Regel 3 richtet sich gegen das Zweite, nicht gegen das Erste.
    """
    gefunden: list[tuple[str, str]] = []
    if isinstance(wert, str):
        if verzeichnis in wert:
            gefunden.append((pfad, wert))
    elif isinstance(wert, dict):
        for k, v in wert.items():
            gefunden += _felder_mit(v, verzeichnis, f"{pfad}.{k}")
    elif isinstance(wert, (list, tuple)):
        for i, v in enumerate(wert):
            gefunden += _felder_mit(v, verzeichnis, f"{pfad}[{i}]")
    return gefunden


def test_kein_arbeitsverzeichnis_verlaesst_die_homestation(bericht, aus):
    """Was im öffentlichen Repo landet, soll nichts über den Rechner verraten, auf dem
    es entstand — weder Benutzernamen noch Projektordner (Regel 3).

    Reproduktion: ``ergebnis['messwerte']['geometrie_qa']['bild_png']`` und die drei
    Pfadfelder unter ``messwerte['render']['parameter']`` sind komplette Pfade der Form
    ``…/build/auf-20260818-99/render.png``. Der Kommentar im Skript hält an der Stelle
    daneben fest, ein solcher Pfad sei „als Name genug" — für ``bild`` wird er darum
    gekürzt, für die anderen vier nicht. In den bereits eingecheckten Ergebnissen steht
    aus derselben Ursache (dort über Fehlertexte) der Heimatordner der HomeStation.
    """
    ergebnis = rufe_render_und_qa(
        bericht, aus, {"prompt": "Wohnhaus"},
        render_modell=Renderattrappe(), tiefen_modell=Tiefenattrappe(treue_ist_karte(bericht)))

    assert _felder_mit(ergebnis["messwerte"], str(aus)) == []


# ══ C · Der Ablauf drumherum ═════════════════════════════════════════════════════════

def test_synthetische_geometrie_wird_vor_ort_erzeugt(tmp_path, monkeypatch):
    """Bei ``synthetisch`` reist nichts über das Repo — die IFC entsteht auf der
    HomeStation, aus einem Skript, das im Repo liegt (Regel 3)."""
    gerufen = []
    monkeypatch.setattr(hw.subprocess, "run",
                        lambda cmd, **kw: gerufen.append(cmd) or Prozess())

    pfad = hw._geometrie_bereitstellen({"geometrie": {"synthetisch": True}}, tmp_path)

    (kommando,) = gerufen
    assert kommando[0] == sys.executable
    assert kommando[1].endswith("make_test_ifc.py")
    assert pfad == str(tmp_path / "build" / "testbau.ifc") == kommando[2]


def test_vorhandene_geometrie_wird_nur_verwiesen(tmp_path):
    """Ein Pfad auf der HomeStation wird durchgereicht — nichts wird erzeugt.

    Der Doppelgänger für ``subprocess.run`` aus der autouse-Vorgabe schlägt Alarm, wenn
    hier doch ein Prozess startete.
    """
    ifc = tmp_path / "bau.ifc"
    ifc.write_text("ISO-10303-21;\n", encoding="utf-8")

    assert hw._geometrie_bereitstellen(
        {"geometrie": {"synthetisch": False, "pfad": str(ifc)}}, tmp_path) == str(ifc)


def test_fehlende_geometrie_meldet_sich_sofort(tmp_path):
    """Vor dem Lauf feststellbar — nach dem Lauf eine verlorene Stunde Cycles."""
    with pytest.raises(FileNotFoundError, match="Geometrie nicht gefunden"):
        hw._geometrie_bereitstellen(
            {"geometrie": {"synthetisch": False, "pfad": str(tmp_path / "weg.ifc")}},
            tmp_path)


def test_umgebung_kommt_auch_ohne_gpu_zurueck():
    """``_umgebung`` läuft in jedem Ergebnispfad. Stürzte sie ohne Karte ab, wäre der
    Entwicklungscontainer für diesen Code unbenutzbar — und die Ablehnung eines
    GPU-Auftrags könnte nicht einmal protokolliert werden."""
    umgebung = hw._umgebung()

    assert umgebung["gpu"] == "keine"
    assert umgebung["leistungsgrenze_w"] is None
    assert umgebung["python"] == sys.version.split()[0]
    assert umgebung["blender"]


def test_umgebung_nennt_die_karte_wenn_es_eine_gibt(smi):
    """Gegenprobe: „keine" ist wirklich eine Auskunft und nicht die einzige Antwort."""
    smi()

    umgebung = hw._umgebung()

    assert umgebung["gpu"] == "NVIDIA GeForce RTX 5090"
    assert umgebung["leistungsgrenze_w"] == 400.0


def _lege_auftrag_ab(repo: Path, auftrag_id: str, art: str = "multipass") -> dict:
    auftrag = hw.auf.baue_auftrag(
        auftrag_id=auftrag_id, art=art,
        beschreibung="Synthetischer Testauftrag, im Repo erzeugbar.")
    hw.auf.schreibe_auftrag(auftrag, repo)
    return auftrag


def test_ein_auftrag_ist_unerledigt_bis_ein_gleichnamiges_ergebnis_liegt(tmp_path):
    """Die Übergabe hat kein Protokoll ausser den Dateinamen — genau darin liegt ihre
    Verlässlichkeit: kein Dienst, kein Port, kein Zustand, den jemand verlieren kann."""
    _lege_auftrag_ab(tmp_path, "auf-20260818-99")
    assert [s["auftrag_id"] for s in hw.auf.unerledigt(tmp_path)] == ["auf-20260818-99"]

    hw.auf.schreibe_ergebnis(
        hw.auf.baue_ergebnis(auftrag_id="auf-20260818-99", status="ok"), tmp_path)

    assert hw.auf.unerledigt(tmp_path) == []


def test_ein_fremdes_ergebnis_erledigt_den_auftrag_nicht(tmp_path):
    """Gegenprobe: „gleichnamig" heisst wirklich gleichnamig."""
    _lege_auftrag_ab(tmp_path, "auf-20260818-99")
    hw.auf.schreibe_ergebnis(
        hw.auf.baue_ergebnis(auftrag_id="auf-20260818-98", status="ok"), tmp_path)

    assert len(hw.auf.unerledigt(tmp_path)) == 1


# ── Der ganze Weg durch `fuehre_aus` ─────────────────────────────────────────────────

@pytest.fixture
def blender_naht(monkeypatch, bericht):
    """``seams`` ersetzen — sonst bräuchte dieser Weg Blender und das ``.venv-ifc``."""
    monkeypatch.setattr(seams, "ifc_zu_glb", lambda ifc, glb, **kw: dict(GLB_BERICHT))
    monkeypatch.setattr(seams, "glb_zu_tiefenkarte", lambda glb, aus, **kw: bericht)
    return bericht


def _multipass_satz(art: str, ifc: Path, aus: Path) -> dict:
    return {"auftrag_id": "auf-20260818-99", "art": art,
            "geometrie": {"synthetisch": False, "pfad": str(ifc)},
            "params": {"out_dir": str(aus), "prompt": "Wohnhaus"}}


@pytest.fixture
def ifc(tmp_path) -> Path:
    pfad = tmp_path / "bau.ifc"
    pfad.write_text("ISO-10303-21;\n", encoding="utf-8")
    return pfad


def test_multipass_meldet_nur_zahlen_und_dateinamen(blender_naht, ifc, aus, tmp_path):
    """Der Regelfall ohne GPU: Was zurückreist, sind Zahlen und Dateinamen."""
    ergebnis = hw.fuehre_aus(_multipass_satz("multipass", ifc, aus), tmp_path)

    assert ergebnis["status"] == "ok"
    assert ergebnis["messwerte"]["n_elements"] == 7
    assert ergebnis["messwerte"]["n_triangles"] == 4242
    assert ergebnis["urteil"] == {"multipass": "ok"}
    assert sorted(ergebnis["messwerte"]["dateien"]) == [
        "beauty.png", "material_id.png", "tiefe_norm.png"], (
        "der Material-ID-Pass gehört dazu — er ist die Grundlage der Bauwerksmaske, und "
        "die Attrappe liess ihn bis zum 26.08.2026 weg"
    )
    assert all("/" not in name for name in ergebnis["messwerte"]["dateien"])


def test_multipass_ohne_tiefenkarte_gilt_nicht_als_erledigt(blender_naht, ifc, aus, tmp_path):
    """Für ``seams`` ist eine gescheiterte Normalisierung nicht tödlich — die EXR bleibt
    das massgebliche Artefakt. Für einen **Auftrag** gilt das nicht.

    Käme ein solcher Lauf als ``ok`` zurück, wäre die einzige Spur ein fehlender
    Dateiname in einer Liste: als erledigt abgehakt und damit unauffindbar. Genau an
    diesen Rückmeldungen wurde die Blender-5.2-Sperre gefunden.
    """
    blender_naht["depth_png"] = None
    blender_naht["depth_png_fehler"] = "EXRVarianteError: Kanal V nicht gefunden"

    ergebnis = hw.fuehre_aus(_multipass_satz("multipass", ifc, aus), tmp_path)

    assert ergebnis["status"] == "fehler"
    assert ergebnis["urteil"]["multipass"] == "unvollstaendig"
    assert "EXRVarianteError" in ergebnis["fehler"]
    # Was der Lauf trotzdem herausgefunden hat, bleibt im Ergebnis.
    assert ergebnis["messwerte"]["n_meshes"] == 7
    assert ergebnis["messwerte"]["depth_exr_kanaele"] == ["tiefe_.V"]


def test_gescheiterte_ifc_konversion_startet_blender_nicht(monkeypatch, ifc, aus, tmp_path):
    """Eine kaputte glb weiterzurendern kostete eine Stunde Cycles für nichts."""
    monkeypatch.setattr(seams, "ifc_zu_glb",
                        lambda i, g, **kw: {"status": "error", "error": "keine Geometrie im IFC"})
    monkeypatch.setattr(seams, "glb_zu_tiefenkarte", Verboten("Blender"))

    ergebnis = hw.fuehre_aus(_multipass_satz("multipass", ifc, aus), tmp_path)

    assert ergebnis["status"] == "fehler"
    assert "keine Geometrie im IFC" in ergebnis["fehler"]


def test_fuehre_aus_reicht_beide_modelle_bis_in_den_render_pfad(blender_naht, ifc, aus, tmp_path):
    """Die beiden Nähte sind der Grund, warum dieser Pfad überhaupt prüfbar ist —
    ohne sie bliebe ausgerechnet der unbeaufsichtigte Teil ungeprüft."""
    bildmodell = Renderattrappe()
    schaetzer = Tiefenattrappe(treue_ist_karte(blender_naht))

    ergebnis = hw.fuehre_aus(_multipass_satz("render", ifc, aus), tmp_path,
                             _render_modell=bildmodell, _tiefen_modell=schaetzer)

    assert ergebnis["status"] == "ok"
    assert ergebnis["urteil"]["bestanden"] is True
    assert len(bildmodell.aufrufe) == 1 and len(schaetzer.aufrufe) == 1


def test_der_maskenweg_wird_auf_der_homestation_wirklich_gefahren(
        blender_naht, ifc, aus, tmp_path):
    """**Die Lücke, die am 26.08.2026 hier sass — und zwar dort, wo gemessen wird.**

    ``qa_gegen_soll`` hat drei Aufrufstellen. Bis zu diesem Tag reichte nur der Abholer
    eine Maske herein; dieses Skript nicht, obwohl es der Weg ist, auf dem die HomeStation
    ihre Render-Aufträge abarbeitet. Ohne Maske bleiben ``rho_maske``, Kante und
    Paarurteil ungemessen — genau die Masse, die die **Abwesenheit** eines Bauwerks
    fangen. Der Score über das ganze Bild fängt sie nicht: Ein leeres Grundstück erreichte
    dort 0.9530 und bestand das Tor (`auf-20260821-26`).

    Gefunden wurde die Lücke durch Zählen von der anderen Seite, nicht durch einen Test —
    und darum steht hier jetzt einer.
    """
    ergebnis = hw.fuehre_aus(_multipass_satz("render", ifc, aus), tmp_path,
                             _render_modell=Renderattrappe(),
                             _tiefen_modell=Tiefenattrappe(treue_ist_karte(blender_naht)))
    qa = ergebnis["messwerte"]["geometrie_qa"]

    assert "maskenbefund" in ergebnis["messwerte"], (
        "der Befund reist mit, auch wenn die Maske nicht baubar war — sonst sähe ein Lauf "
        "ohne Maske hinterher aus wie einer mit Maske und ohne Auffälligkeit"
    )
    assert not [w for w in qa["warnungen"] if "OHNE MASKENWEG" in w], (
        "die selbstlöschende Zeile aus `qa_gegen_soll` darf hier nicht mehr auflaufen"
    )
    assert qa["paarurteil"] is not None, "der Maskenweg ist gefahren, also gibt es ein Urteil"


# ── Die Kommandozeile ────────────────────────────────────────────────────────────────

def test_liste_zeigt_unerledigtes_ohne_etwas_zu_starten(tmp_path, capsys):
    """``--liste`` ist der erste Griff auf der HomeStation. Er darf nichts rechnen."""
    _lege_auftrag_ab(tmp_path, "auf-20260818-99")

    assert hw.main(["--repo", str(tmp_path), "--liste"]) == 0
    assert "auf-20260818-99" in capsys.readouterr().out


def test_hoechstens_deckelt_den_durchgang(tmp_path, monkeypatch, capsys):
    """**Der Schalter, ohne den es keinen Takt geben konnte.**

    ``--alle`` kann zwölf Aufträge bedeuten, und ein Renderlauf dauert Minuten. Ein Takt,
    der erst nach Stunden zurückkommt, ist keiner: Die Karte bliebe belegt, ein dringender
    Auftrag wartete hinter elf alten, und ein hängender Lauf hielte die Reihe auf.

    Der Abholer löst dasselbe seit dem 22.08.2026 mit ``--hoechstens 1``. Der Homeworker
    hatte es nicht — und lief darum **nur von Hand**. Genau das ist der Unterschied
    zwischen «beauftragt» und «wird auch gemacht».
    """
    for nummer in (97, 98, 99):
        _lege_auftrag_ab(tmp_path, f"auf-20260818-{nummer}")
    gelaufen: list[str] = []
    monkeypatch.setattr(hw, "fuehre_aus", lambda satz, repo, **kw: (
        gelaufen.append(satz["auftrag_id"]) or hw.auf.baue_ergebnis(
            auftrag_id=satz["auftrag_id"], status="ok")))

    assert hw.main(["--repo", str(tmp_path), "--alle", "--hoechstens", "2"]) == 0

    assert len(gelaufen) == 2, "der Deckel gilt, auch wenn mehr offen liegt"
    assert len(hw.auf.unerledigt(tmp_path)) == 1, "der dritte bleibt für den nächsten Takt"


def test_ohne_hoechstens_laeuft_weiterhin_alles(tmp_path, monkeypatch):
    """Die Gegenprobe. Ohne sie prüfte der Test darüber nur, dass irgendwann Schluss ist.

    Der Deckel ist eine **Betriebsangabe**, keine neue Voreinstellung: Wer ``--alle`` ohne
    Zahl sagt, meint alles, und das bleibt so.
    """
    for nummer in (97, 98, 99):
        _lege_auftrag_ab(tmp_path, f"auf-20260818-{nummer}")
    monkeypatch.setattr(hw, "fuehre_aus", lambda satz, repo, **kw: hw.auf.baue_ergebnis(
        auftrag_id=satz["auftrag_id"], status="ok"))

    assert hw.main(["--repo", str(tmp_path), "--alle"]) == 0
    assert hw.auf.unerledigt(tmp_path) == []


def test_ein_deckel_unter_eins_wird_abgewiesen_statt_still_nichts_zu_tun(tmp_path, capsys):
    """``--hoechstens 0`` sähe aus wie ein ruhiger Durchgang und wäre ein stummer.

    Ein Dienst, der jede fünf Minuten fehlerfrei nichts tut, ist die geduldigste Art,
    einen Rückstand zu verstecken.
    """
    _lege_auftrag_ab(tmp_path, "auf-20260818-99")

    assert hw.main(["--repo", str(tmp_path), "--alle", "--hoechstens", "0"]) == 1
    assert "mindestens 1" in capsys.readouterr().out
    assert len(hw.auf.unerledigt(tmp_path)) == 1


def test_gpu_schalter_meldet_den_zustand_als_json(smi, capsys):
    """``--gpu`` beantwortet die Frage „ist die Karte frei?" ohne Auftrag."""
    smi()

    assert hw.main(["--gpu"]) == 0
    assert "NVIDIA GeForce RTX 5090" in capsys.readouterr().out


def test_render_auftrag_wird_bei_unbekannter_gpu_abgelehnt_statt_gestartet(
        tmp_path, monkeypatch, capsys):
    """Die Zusage im Ganzen: unbekannter Zustand → ``abgelehnt`` als Ergebnis im Repo,
    und ``fuehre_aus`` wird gar nicht erst gerufen."""
    _lege_auftrag_ab(tmp_path, "auf-20260818-99", art="render")
    monkeypatch.setattr(hw, "fuehre_aus", Verboten("Der Auftrag"))

    assert hw.main(["--repo", str(tmp_path), "--alle"]) == 0

    ergebnis = hw.auf.lies_ergebnis("auf-20260818-99", tmp_path)
    assert ergebnis["status"] == "abgelehnt"
    assert "unbekannt" in ergebnis["fehler"]


def test_ein_gescheiterter_auftrag_reisst_den_lauf_nicht_ab(tmp_path, monkeypatch):
    """Über Nacht laufen mehrere Aufträge. Ein Absturz im ersten kostete alle."""
    _lege_auftrag_ab(tmp_path, "auf-20260818-98")

    def bricht(satz, repo, **kw):
        raise RuntimeError("Blender endete mit Code 1")

    monkeypatch.setattr(hw, "fuehre_aus", bricht)

    assert hw.main(["--repo", str(tmp_path), "--alle"]) == 0

    ergebnis = hw.auf.lies_ergebnis("auf-20260818-98", tmp_path)
    assert ergebnis["status"] == "fehler"
    assert "RuntimeError: Blender endete mit Code 1" == ergebnis["fehler"]


def test_unbekannter_auftrag_meldet_sich_statt_still_nichts_zu_tun(tmp_path, capsys):
    """Ein Tippfehler in der Kennung darf nicht wie „nichts zu tun" aussehen."""
    assert hw.main(["--repo", str(tmp_path), "--auftrag", "auf-gibt-es-nicht"]) == 1
    assert "auf-gibt-es-nicht" in capsys.readouterr().out


# ======================================================================================
# Der Demolauf soll ein Bild auf Augenhöhe zeigen (Owner-Auftrag 28.08.2026)
# ======================================================================================

@pytest.fixture
def mitgeschrieben(monkeypatch, bericht):
    """Wie ``blender_naht``, aber sie **merkt sich die Argumente**."""
    gesehen: dict = {}

    def merken(glb, aus, **kw):
        gesehen.clear()
        gesehen.update(kw)
        return bericht

    monkeypatch.setattr(seams, "ifc_zu_glb", lambda ifc, glb, **kw: dict(GLB_BERICHT))
    monkeypatch.setattr(seams, "glb_zu_tiefenkarte", merken)
    return gesehen


def test_der_homeworker_fordert_eine_kamera_an(mitgeschrieben, ifc, aus, tmp_path):
    """**Der Befund des Owners, als Test** (28.08.2026):

    *«wenn der local worker nun einen demolauf macht ist die kamera vom endbild … nicht
    auf augenhöhe mensch … wieso?»*

    Weil hier bis dahin **gar keine** Kamera stand. `glb_zu_tiefenkarte` wurde nur mit
    Auflösung und Samples gerufen, und der Runner stellte dann seine **Notkamera** —
    Blenders eigene 50-mm-Optik an einem Ort, der mit Augenhöhe nichts zu tun hat. Der
    Bericht sagte es sogar (`weg: rueckfall`); niemand las es.

    *Ein Rückfall, der sich meldet, ist besser als einer, der schweigt — aber er bleibt
    ein Rückfall. Gemeldet zu werden ersetzt nicht, richtig zu sein.*
    """
    hw.fuehre_aus(_multipass_satz("multipass", ifc, aus), tmp_path)
    assert mitgeschrieben.get("kamera") == hw.VORGABE_KAMERA


def test_ein_auftrag_darf_die_richtung_selbst_waehlen(mitgeschrieben, ifc, aus, tmp_path):
    satz = _multipass_satz("multipass", ifc, aus)
    satz["params"]["kamera"] = "nNW"
    hw.fuehre_aus(satz, tmp_path)
    assert mitgeschrieben.get("kamera") == "nNW"


def test_die_vorgabe_ist_eine_diagonale_richtung():
    """**Gemessen, nicht gewählt** (28.08.2026, acht Richtungen einer Szene):

    Auf den vier frontalen Richtungen fallen **5 von 20** guten Fällen unter
    `PAAR_RHO_SCHWELLE`, auf den vier diagonalen **keiner**. Frontale Ansichten sind nicht
    unmessbar — sie sind die schlechtere Vorgabe.
    """
    from aiimaging import kameras
    assert hw.VORGABE_KAMERA in kameras.RICHTUNGSFOLGE
    assert hw.VORGABE_KAMERA not in ("n", "e", "s", "w"), (
        "eine frontale Richtung als Vorgabe kostet gute Faelle")


@pytest.mark.parametrize("name,wert", [
    ("augenhoehe", 1.55), ("gelaende_z", 412.5), ("kamera_modus", "gekippt"),
    ("brennweite", 28.0), ("deckungsgrad", 0.6), ("bias_grad", 20.0),
])
def test_kameraangaben_aus_dem_auftrag_werden_durchgereicht(mitgeschrieben, ifc, aus,
                                                            tmp_path, name, wert):
    """`gelaende_z` ist die wichtigste davon: Ohne sie ist der Bezugspunkt die
    **Hüllbox-Unterkante**, und die liegt bei einem Untergeschoss im Erdreich."""
    satz = _multipass_satz("multipass", ifc, aus)
    satz["params"][name] = wert
    hw.fuehre_aus(satz, tmp_path)
    assert mitgeschrieben.get(name) == wert


def test_eine_nicht_gesetzte_kameraangabe_wird_NICHT_durchgereicht(mitgeschrieben, ifc,
                                                                   aus, tmp_path):
    """Ein durchgereichtes ``None`` überschriebe die gerechnete Vorgabe mit nichts."""
    hw.fuehre_aus(_multipass_satz("multipass", ifc, aus), tmp_path)
    for name in hw._KAMERA_PARAMS:
        assert name not in mitgeschrieben, name


def test_kameraangaben_gelten_als_verbraucht_und_werden_nicht_bemaengelt(ifc, aus):
    """Sonst meldete der Auftrag sie als unverstanden — und das wäre eine Falschmeldung."""
    params = {n: 1.0 for n in hw._KAMERA_PARAMS}
    params["kamera"] = "sSE"
    assert hw._unverstandene_params("multipass", params) == []


# ======================================================================================
# Der Empfängerfilter — der Befund kam vom Gerät (auf-20260828-64, 28.08.2026)
# ======================================================================================

def _fremder_satz(kennung: str, worker: str) -> dict:
    return {"schema": hw.auf.SCHEMA_AUFTRAG, "worker": worker, "auftrag_id": kennung,
            "art": "qa", "beschreibung": "Eine Frage an eine andere Lane.",
            "anweisung": "Nicht fuer die HomeStation.",
            "erstellt": "2026-08-28T00:00:00Z",
            "geometrie": {"synthetisch": True, "pfad": None,
                          "erzeugen_mit": "python3 tools/make_test_ifc.py build/t.ifc"},
            "params": {}, "auflagen": ["keine"], "rueckgabe": ["V1 nichts"]}


def _ablage(tmp_path, *saetze):
    ordner = tmp_path / "auftraege" / "offen"
    ordner.mkdir(parents=True, exist_ok=True)
    (tmp_path / "auftraege" / "ergebnisse").mkdir(parents=True, exist_ok=True)
    for satz in saetze:
        (ordner / f"{satz['auftrag_id']}.json").write_text(
            json.dumps(satz), encoding="utf-8")
    return tmp_path


def test_ein_fremder_auftrag_wird_nicht_ausgefuehrt_und_nicht_geschlossen(tmp_path,
                                                                          capsys):
    """**Der blockierende Fund vom Gerät.**

    `homeworker` las das `worker`-Feld nirgends. Von 23 offenen Aufträgen wären **fünf
    beim falschen Empfänger** durchgelaufen — alle `art: qa`, alle im Multipass-Zweig,
    alle mit `status: ok, urteil: {"multipass": "ok"}`. Grün und leer.

    **Und das Ergebnis wäre nicht folgenlos:** Ein geschriebenes Ergebnis heisst in diesem
    Projekt *beantwortet*. Die HomeStation hätte Vertragsfragen an einen fremden Worker
    geschlossen, ohne dass jemand sie je gelesen hätte.

    *`auftrag.py` verlangt das Feld seit dem 22.08.2026 als Pflicht — es wurde nur nie
    gelesen. Eine Pflichtangabe, die niemand liest, ist eine Zeile Text.*
    """
    repo = _ablage(tmp_path, _fremder_satz("auf-20260828-90", "cloud"))
    assert hw.main(["--repo", str(repo), "--alle"]) == 0

    ausgabe = capsys.readouterr().out
    assert "auf-20260828-90" in ausgabe and "'cloud'" in ausgabe
    assert not list((repo / "auftraege" / "ergebnisse").iterdir()), (
        "eine Ablehnung waere hier schlimmer als Schweigen — sie zaehlte als Antwort")


@pytest.mark.parametrize("worker", ["cloud", "ui"])
def test_kein_fremder_worker_wird_ausgefuehrt(tmp_path, worker):
    repo = _ablage(tmp_path, _fremder_satz("auf-20260828-91", worker))
    hw.main(["--repo", str(repo), "--alle"])
    assert not list((repo / "auftraege" / "ergebnisse").iterdir())


def test_ein_fremder_auftrag_wird_auch_bei_ausdruecklicher_nennung_abgelehnt(tmp_path,
                                                                             capsys):
    """`--auftrag` ist kein Freibrief. Wer ihn nennt, weiss oft nicht, wem er gehört."""
    repo = _ablage(tmp_path, _fremder_satz("auf-20260828-92", "ui"))
    assert hw.main(["--repo", str(repo), "--auftrag", "auf-20260828-92"]) == 1
    assert "nicht fuer 'local'" in capsys.readouterr().out
    assert not list((repo / "auftraege" / "ergebnisse").iterdir())


def test_die_liste_zeigt_beide_seiten(tmp_path, capsys):
    """Fremde Aufträge werden **gezählt und genannt** — sonst hielte sie jemand für
    erledigt, weil sie nirgends mehr auftauchen."""
    eigener = _fremder_satz("auf-20260828-93", "local")
    repo = _ablage(tmp_path, eigener, _fremder_satz("auf-20260828-94", "cloud"))
    hw.main(["--repo", str(repo), "--liste"])

    ausgabe = capsys.readouterr().out
    assert "1 Auftraege sind nicht fuer 'local'" in ausgabe
    assert "1 unerledigt fuer 'local'" in ausgabe
    assert "auf-20260828-93" in ausgabe and "auf-20260828-94" in ausgabe


def test_ein_auftrag_ohne_worker_feld_gilt_als_fremd(tmp_path):
    """**Nicht als eigener.** Ein fehlendes Feld ist keine Zusage, und der teure Fehler
    liegt auf der Seite «doch ausgeführt»."""
    satz = _fremder_satz("auf-20260828-95", "local")
    del satz["worker"]
    repo = _ablage(tmp_path, satz)
    hw.main(["--repo", str(repo), "--alle"])
    assert not list((repo / "auftraege" / "ergebnisse").iterdir())


def test_der_eigene_worker_heisst_local():
    """Er steht in `auftrag.WORKER` — sonst liefe der Filter gegen einen erfundenen Namen
    und liesse alles liegen."""
    assert hw.EIGENER_WORKER in hw.auf.WORKER
