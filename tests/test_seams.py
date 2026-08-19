"""Die Aufrufkonstruktion an der Prozessgrenze — geprüft ohne Blender und ohne venv.

``seams.py`` startet fremde Programme. Ohne Testnaht wäre es nur dort prüfbar, wo
Blender installiert ist; damit bliebe die wichtigste Stelle des Projekts ungeprüft.
Jede Funktion nimmt darum ein ``_starte``, das den Subprozessaufruf ersetzt. Die Tests
hier reichen einen Doppelgänger hinein und schauen sich an, **was** aufgerufen worden
wäre — insbesondere, ob ``--rotiere-z-up`` genau dann gesetzt wird, wenn die Quelle
Z-up ist (Phase-0-Befund).

Es wird kein echter Prozess gestartet: kein Blender, keine GPU, kein Netz.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from aiimaging import seams
from aiimaging.contracts import ContractError
from aiimaging.seams import (
    SeamError,
    baue_kommando_multipass,
    baue_kommando_tiefenkarte,
    glb_zu_tiefenkarte,
    ifc_zu_glb,
)

#: Die beiden realen Schreibweisen aus dem Ökosystem (siehe ``test_contracts.py``).
KOSMODRAW_UP = "Z"
KOSMOVIS_UP = "Y (glTF-2.0-Standard; Blender-Import → Z-up/aufrecht)"

#: Die Flagge, an der alles hängt: gesetzt, dreht der Runner die Geometrie vor dem Rendern.
FLAGGE = "--rotiere-z-up"


class Ergebnis:
    """Doppelgänger eines ``subprocess.CompletedProcess`` — nur, was die Naht ausliest."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Aufrufer:
    """Ersatz für ``_starte``: merkt sich die Kommandos, statt Prozesse zu starten."""

    def __init__(self, ergebnis=None, nebenwirkung=None):
        self.ergebnis = ergebnis or Ergebnis()
        self.nebenwirkung = nebenwirkung
        self.kommandos: list[list[str]] = []
        self.timeouts: list[int] = []

    def __call__(self, cmd, timeout):
        self.kommandos.append(list(cmd))
        self.timeouts.append(timeout)
        if self.nebenwirkung is not None:
            self.nebenwirkung(cmd)
        return self.ergebnis

    @property
    def kommando(self) -> list[str]:
        assert len(self.kommandos) == 1, f"erwartet: genau ein Aufruf, war {len(self.kommandos)}"
        return self.kommandos[0]


def verweigerer(cmd, timeout):
    """``_starte``, das nie aufgerufen werden darf — belegt, dass vorher abgebrochen wurde."""
    raise AssertionError(f"Es wurde ein Prozess gestartet, obwohl der Vertrag brach: {cmd}")


@pytest.fixture
def blender_attrappe(monkeypatch):
    """Ein Pfad, der so tut, als wäre Blender installiert — gestartet wird er nie."""
    monkeypatch.setenv("AIIMAGING_BLENDER", "/attrappe/blender")
    return "/attrappe/blender"


@pytest.fixture
def ifc_python_attrappe(monkeypatch):
    """Ein Pfad, der das ``.venv-ifc``-Python vertritt — ausgeführt wird er nie."""
    monkeypatch.setenv("AIIMAGING_IFC_PYTHON", "/attrappe/venv-ifc/bin/python")
    return "/attrappe/venv-ifc/bin/python"


# --------------------------------------------------------------------------------------
# baue_kommando_tiefenkarte — die Flagge sitzt genau dann, wenn die Quelle Z-up ist
# --------------------------------------------------------------------------------------

def test_kommando_dreht_bei_z_up_quelle():
    """Phase-0-Befund: Eine Z-up-glb (KosmoDraw) bekommt die Drehflagge, sonst liegt sie."""
    cmd = baue_kommando_tiefenkarte("bau.glb", "out", up_axis=KOSMODRAW_UP)
    assert FLAGGE in cmd


def test_kommando_dreht_nicht_bei_y_up_quelle():
    """Gegenprobe: Die Y-up-glb (KosmoVis) darf die Flagge nicht bekommen — sie kippte sonst."""
    cmd = baue_kommando_tiefenkarte("bau.glb", "out", up_axis=KOSMOVIS_UP)
    assert FLAGGE not in cmd


@pytest.mark.parametrize("up_axis, erwartet_flagge", [
    ("Z", True),
    ("z", True),
    ("Z-up (rohe IFC-Koordinaten)", True),
    ("Y", False),
    ("y", False),
    (KOSMOVIS_UP, False),
])
def test_flagge_folgt_der_up_achse(up_axis, erwartet_flagge):
    """Die Flagge hängt allein an der Up-Achse — über alle bekannten Schreibweisen hinweg."""
    cmd = baue_kommando_tiefenkarte("bau.glb", "out", up_axis=up_axis)
    assert (FLAGGE in cmd) is erwartet_flagge


def test_kommando_ruft_blender_ohne_oberflaeche_und_ohne_benutzerprofil():
    """Regel 2 und 4: Blender läuft als Subprozess im Hintergrund, ohne UI und ohne Add-ons."""
    cmd = baue_kommando_tiefenkarte("bau.glb", "out", up_axis="Y")
    assert cmd[0] == "blender"
    assert "--background" in cmd
    assert "--factory-startup" in cmd
    assert cmd[cmd.index("--python") + 1] == str(seams.BLENDER_RUNNER)
    assert "--" in cmd and cmd.index("--") > cmd.index("--python")


def test_kommando_reicht_aufloesung_und_samples_durch():
    """Renderparameter gehören ins Kommando, nicht in eine Voreinstellung des Runners."""
    cmd = baue_kommando_tiefenkarte("bau.glb", "out", up_axis="Y", aufloesung=256, samples=4)
    assert cmd[cmd.index("--aufloesung") + 1] == "256"
    assert cmd[cmd.index("--samples") + 1] == "4"


def test_kommando_ohne_up_achse_wird_nicht_gebaut():
    """Ohne ``up_axis`` entsteht gar kein Kommando — lieber kein Lauf als ein verdrehter."""
    with pytest.raises(ContractError):
        baue_kommando_tiefenkarte("bau.glb", "out", up_axis=None)


# --------------------------------------------------------------------------------------
# glb_zu_tiefenkarte — Vertragsprüfung VOR dem Prozessstart
# --------------------------------------------------------------------------------------

def test_tiefenkarte_bricht_vor_dem_prozessstart_ab_wenn_up_achse_fehlt(tmp_path):
    """Der teuerste Fehler wäre ein Cycles-Lauf auf verdrehter Geometrie — abgebrochen wird vorher."""
    ziel = tmp_path / "depth"
    with pytest.raises(ContractError, match="up_axis"):
        glb_zu_tiefenkarte("bau.glb", ziel, up_axis=None, _starte=verweigerer)
    assert not ziel.exists(), "Das Ausgabeverzeichnis wurde angelegt, obwohl nichts lief"


@pytest.mark.parametrize("kaputt", ["", "   ", "X"])
def test_tiefenkarte_bricht_bei_undeutbarer_up_achse_ab(tmp_path, kaputt):
    """Leer oder undeutbar zählt wie fehlend — kein Lauf auf geratener Orientierung."""
    with pytest.raises(ContractError):
        glb_zu_tiefenkarte("bau.glb", tmp_path / "depth", up_axis=kaputt, _starte=verweigerer)


def test_tiefenkarte_startet_blender_mit_drehflagge(tmp_path, blender_attrappe):
    """Der Befund im Vollzug: Aus einer Z-up-Quelle wird ein Blender-Aufruf mit Drehung."""
    ziel = tmp_path / "depth"

    def report_schreiben(cmd):
        Path(cmd[cmd.index("--out") + 1], "blender-report.json").write_text(
            json.dumps({"status": "ok", "depth_png": "depth.png"}), encoding="utf-8")

    aufrufer = Aufrufer(nebenwirkung=report_schreiben)
    bericht = glb_zu_tiefenkarte("bau.glb", ziel, up_axis=KOSMODRAW_UP, _starte=aufrufer)

    assert aufrufer.kommando[0] == blender_attrappe
    assert FLAGGE in aufrufer.kommando
    # `depth_png` wird seit dem 18.08.2026 von der Naht selbst gesetzt, nicht vom
    # Runner — hier auf None, weil der Attrappen-Report keine EXR nennt.
    assert bericht["status"] == "ok"
    assert bericht["depth_png"] is None
    assert ziel.is_dir(), "Das Ausgabeverzeichnis muss vor dem Lauf existieren"


def test_tiefenkarte_startet_blender_ohne_drehflagge_bei_y_up(tmp_path, blender_attrappe):
    """Gegenprobe am echten Aufruf: KosmoVis-Geometrie wird unverändert gerendert."""
    ziel = tmp_path / "depth"
    aufrufer = Aufrufer(nebenwirkung=lambda cmd: Path(
        cmd[cmd.index("--out") + 1], "blender-report.json").write_text("{}", encoding="utf-8"))

    glb_zu_tiefenkarte("bau.glb", ziel, up_axis=KOSMOVIS_UP, _starte=aufrufer)

    assert FLAGGE not in aufrufer.kommando


def test_tiefenkarte_meldet_abbruch_des_prozesses(tmp_path, blender_attrappe):
    """Endet Blender mit Fehlercode, wird das gemeldet — nicht verschwiegen."""
    aufrufer = Aufrufer(Ergebnis(returncode=1, stderr="Cycles: out of memory"))

    with pytest.raises(SeamError, match="Code 1"):
        glb_zu_tiefenkarte("bau.glb", tmp_path / "depth", up_axis="Y", _starte=aufrufer)


def test_tiefenkarte_meldet_fehlenden_report_als_seamerror(tmp_path, blender_attrappe):
    """Sauberes Ende ohne Report heisst trotzdem gescheitert — Blender kann 0 melden und
    am Compositor scheitern. Beide Bedingungen sind notwendig, keine genuegt allein."""
    aufrufer = Aufrufer(Ergebnis(returncode=0))

    with pytest.raises(SeamError, match="Report"):
        glb_zu_tiefenkarte("bau.glb", tmp_path / "depth", up_axis="Y", _starte=aufrufer)


def test_tiefenkarte_gilt_nicht_wegen_eines_alten_reports_als_gelungen(tmp_path, blender_attrappe):
    """Regression: ein abgestuerzter Lauf darf sich nicht am Report eines Vorlaufs gesundmelden.

    Gefunden beim Testschreiben (Sitzung 03). Weil `out_dir` ueblicherweise
    wiederverwendet wird, htte ein Absturz mit liegengebliebenem Report still
    `status: ok` zurueckgegeben — die Sorte stiller Falschmeldung, gegen die dieses
    Projekt sonst antritt. Der Report wird darum vor dem Start geloescht.
    """
    ziel = tmp_path / "depth"
    ziel.mkdir()
    (ziel / "blender-report.json").write_text(
        '{"status": "ok", "aus": "ALTER LAUF"}', encoding="utf-8")

    aufrufer = Aufrufer(Ergebnis(returncode=137, stderr="Killed"))

    with pytest.raises(SeamError):
        glb_zu_tiefenkarte("bau.glb", ziel, up_axis="Y", _starte=aufrufer)

    assert not (ziel / "blender-report.json").exists(), \
        "Der alte Report muss vor dem Lauf entfernt worden sein"


def test_tiefenkarte_reicht_timeout_durch(tmp_path, blender_attrappe):
    """Ein Render darf hängen — der Zeitausschnitt des Aufrufers muss beim Subprozess ankommen."""
    aufrufer = Aufrufer(nebenwirkung=lambda cmd: Path(
        cmd[cmd.index("--out") + 1], "blender-report.json").write_text("{}", encoding="utf-8"))

    glb_zu_tiefenkarte("bau.glb", tmp_path / "d", up_axis="Y", timeout=42, _starte=aufrufer)

    assert aufrufer.timeouts == [42]


# --------------------------------------------------------------------------------------
# ifc_zu_glb — Prozess im fremden venv, Verständigung über JSON
# --------------------------------------------------------------------------------------

def test_ifc_lauf_ruft_das_fremde_venv_mit_dem_runner_auf(ifc_python_attrappe, tmp_path):
    """LGPL-Auflage 1: Der Runner läuft im eigenen venv, nicht im Produkt-Interpreter."""
    aufrufer = Aufrufer(Ergebnis(stdout=json.dumps({"glb_path": "b.glb", "up_axis": "Y"})))

    bericht = ifc_zu_glb(tmp_path / "b.ifc", tmp_path / "b.glb", _starte=aufrufer)

    assert aufrufer.kommando[0] == ifc_python_attrappe
    assert aufrufer.kommando[1] == str(seams.IFC_RUNNER)
    assert bericht["up_axis"] == "Y", "Der eigene Pfad liefert glTF-konformes Y-up"


def test_ifc_lauf_meldet_rueckgabewert_ungleich_null(ifc_python_attrappe, tmp_path):
    """Ein gescheiterter Subprozess wird zum ``SeamError`` — kein stilles Weiterlaufen."""
    aufrufer = Aufrufer(Ergebnis(returncode=2, stderr="ifcopenshell: Datei nicht lesbar"))

    with pytest.raises(SeamError) as fehler:
        ifc_zu_glb(tmp_path / "b.ifc", tmp_path / "b.glb", _starte=aufrufer)

    assert "Code 2" in str(fehler.value)
    assert "nicht lesbar" in str(fehler.value), "Die Meldung des Runners muss durchgereicht werden"


def test_ifc_lauf_meldet_nicht_json_ausgabe(ifc_python_attrappe, tmp_path):
    """Die Verständigung läuft über JSON — was das nicht ist, wird als Nahtfehler gemeldet."""
    aufrufer = Aufrufer(Ergebnis(stdout="Segmentation fault (core dumped)"))

    with pytest.raises(SeamError, match="kein JSON"):
        ifc_zu_glb(tmp_path / "b.ifc", tmp_path / "b.glb", _starte=aufrufer)


def test_ifc_lauf_meldet_leere_ausgabe(ifc_python_attrappe, tmp_path):
    """Auch ein stiller Runner ist ein Fehler: Ohne Report weiss der Aufrufer nichts."""
    with pytest.raises(SeamError, match="kein JSON"):
        ifc_zu_glb(tmp_path / "b.ifc", tmp_path / "b.glb", _starte=Aufrufer(Ergebnis(stdout="")))


def test_ifc_lauf_startet_nichts_ohne_venv(monkeypatch, tmp_path):
    """Fehlt das ``.venv-ifc``, wird gar kein Prozess versucht — und schon gar nicht der eigene."""
    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(SeamError, match=".venv-ifc"):
        ifc_zu_glb(tmp_path / "b.ifc", tmp_path / "b.glb", _starte=verweigerer)


# ==========================================================================================
# Die Kamera über die Prozessgrenze
#
# Bis zum 18.08.2026 stellte der Runner immer dieselbe Notkamera ("diagonal von vorn-oben")
# und sein eigener Kommentar sagte, die zwölf Automatikkameras kämen später. Sie sind jetzt
# da (`aiimaging.kameras`) — und die Frage ist, WIE sie über die Grenze kommen.
#
# Zwei Wege, und der Unterschied ist kein Geschmack:
#   * `kamera="n"` — der Runner leitet aus der DORT gemessenen Hüllbox ab. Sicher, weil
#     keine Annahme über Bezugssysteme nötig ist.
#   * `auge`/`blick_auf` — fertige Zahlen. Wer sie schickt, trägt das Bezugssystem selbst.
# ==========================================================================================

def test_ohne_angabe_bleibt_das_kommando_wie_bisher():
    """Kein Kameraargument heisst: Der Runner stellt seinen Rückfall — wie immer.

    Wichtig als Rückwärtssicherung: Jede bisher gemessene Tiefenkarte hängt an genau
    dieser Notkamera. Ein stillschweigend geändertes Vorgabekommando verschöbe sie alle.
    """
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y")
    assert "--kamera" not in kommando
    assert "--auge" not in kommando
    assert "--brennweite" not in kommando


def test_richtungskuerzel_wird_durchgereicht():
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="nNE")
    assert kommando[kommando.index("--kamera") + 1] == "nNE"


def test_fertige_koordinaten_schlagen_das_kuerzel():
    """Wer selbst gerechnet hat, hat den Vortritt — sonst rechnete der Runner nochmal."""
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                       kamera="n", auge=(1.0, -2.0, 1.7),
                                       blick_auf=(0.0, 0.0, 5.0))
    assert "--kamera" not in kommando
    assert kommando[kommando.index("--auge") + 1] == "1.0,-2.0,1.7"
    assert kommando[kommando.index("--blick-auf") + 1] == "0.0,0.0,5.0"


def test_standort_ohne_blickziel_wird_vor_dem_blender_start_abgewiesen():
    """Der Fehler ist an drei Zahlen erkennbar — der Lauf dahinter kostet Minuten.

    Ihn erst im Runner auffallen zu lassen hiesse, einen Blender-Start für nichts zu
    verbrennen und den Owner auf eine Meldung warten zu lassen, die hier sofort da ist.
    """
    for kw in ({"auge": (1.0, 2.0, 3.0)}, {"blick_auf": (1.0, 2.0, 3.0)}):
        with pytest.raises(SeamError, match="gehören zusammen"):
            baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", **kw)


@pytest.mark.parametrize("kaputt", [
    (1.0, 2.0), (1.0, 2.0, 3.0, 4.0), "1,2,3", (1.0, 2.0, float("nan")),
    (1.0, 2.0, float("inf")), (1.0, 2.0, None), None,
])
def test_unbrauchbare_koordinaten_werden_abgewiesen(kaputt):
    """Eine halb gelesene Kameraposition ist schlimmer als gar keine.

    Das Bild entstünde und zeigte etwas anderes als gemeint, ohne dass irgendwo ein
    Fehler stünde.
    """
    with pytest.raises(SeamError):
        baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                auge=kaputt, blick_auf=(0.0, 0.0, 0.0))


def test_brennweite_nur_wenn_gesetzt():
    """`None` heisst: Blenders eigene Brennweite bleibt stehen.

    Der Rückfall ist die Bezugsgrösse aller bisher gemessenen Tiefenkarten. Wer seine
    Optik ändert, verschiebt rückwirkend jede Zahl, die daran kalibriert wurde.
    """
    ohne = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="n")
    assert "--brennweite" not in ohne
    mit = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="n",
                                  brennweite=35.0)
    assert mit[mit.index("--brennweite") + 1] == "35.0"


def test_die_kameraargumente_stehen_hinter_dem_trenner():
    """Alles vor `--` gehört Blender. Ein Kameraargument davor wäre ein Blender-Flag."""
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="s")
    assert kommando.index("--") < kommando.index("--kamera")


def test_kamera_und_z_up_drehung_vertragen_sich():
    """Beides zusammen ist der Regelfall bei KosmoDraw-Geometrie."""
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Z", kamera="eEN")
    assert "--rotiere-z-up" in kommando
    assert kommando[kommando.index("--kamera") + 1] == "eEN"


def test_gelaendestand_wird_durchgereicht():
    """Bei einem Untergeschoss ist die Hüllbox-Unterkante nicht das Gelände.

    Ohne Angabe stünde die Kamera im Keller. Die Bibliothek rät nicht — sie nimmt die
    Angabe entgegen, wenn es eine gibt.
    """
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                       kamera="n", gelaende_z=412.5)
    assert kommando[kommando.index("--gelaende-z") + 1] == "412.5"
    ohne = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="n")
    assert "--gelaende-z" not in ohne


def test_die_hoehe_wird_durchgereicht():
    """Ohne sie rendert die Kette zwingend quadratisch — und ein Stil-Seitenverhältnis
    wäre eine tote Kante.

    Genau das war es vom 18. bis zum 19.08.2026: `prompts.Stil.seitenverhaeltnis` wurde
    geschrieben, der Runner setzte `resolution_x = resolution_y` und rechnete die Kamera
    fest mit 1.0. Ein Feld, das aussieht als wirke es, und nichts tut.
    """
    kommando = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                       aufloesung=320, hoehe=180)
    assert kommando[kommando.index("--hoehe") + 1] == "180"


def test_ohne_hoehe_bleibt_es_quadratisch():
    """Rückwärtssicherung: Jede bisher gemessene Zahl hängt am quadratischen Rahmen."""
    assert "--hoehe" not in baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y")
