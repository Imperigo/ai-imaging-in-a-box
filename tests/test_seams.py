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

import ast
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


@pytest.fixture
def ifc_datei(tmp_path):
    """Eine winzige, **gueltige** IFC auf der Platte.

    **Gebraucht seit dem 19.09.2026**, und der Grund ist selbst ein Befund: `ifc_zu_glb`
    sieht die Datei jetzt an, bevor es den Subprozess startet. Die Proben hier reichten
    bis dahin einen Pfad durch, den es gar nicht gab — mit einem Aufrufer, der so tat,
    als haette ein Prozess ihn gelesen. *Eine Attrappe, die eine Lage nachbaut, die es
    nicht geben kann, prueft die falsche Sache.*

    Regel 3: synthetisch und hier erzeugt, nichts aus einem echten Projekt.
    """
    pfad = tmp_path / "b.ifc"
    pfad.write_text(
        "ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION((''),'');\n"
        "FILE_NAME('b.ifc','2026-09-19T00:00:00',(''),(''),'','Testfixture','');\n"
        "FILE_SCHEMA(('IFC4'));\nENDSEC;\nDATA;\n"
        "#1=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\nENDSEC;\nEND-ISO-10303-21;\n",
        encoding="utf-8")
    return pfad


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


@pytest.fixture(autouse=True)
def ohne_zeitfaktor(monkeypatch):
    """Diese Proben messen den Code, nicht die Maschine, auf der sie laufen.

    GEMESSEN AM 18.09.2026: Mit ``AIIMAGING_ZEITFAKTOR=3`` in der Umgebung — also mit
    genau der Angabe, die eine langsamere Maschine laut :func:`seams.zeitfaktor` machen
    SOLL — fielen drei Proben der Gesamtsuite um, zwei davon hier
    (``test_tiefenkarte_reicht_timeout_durch``,
    ``test_ohne_gesamtfrist_hat_die_nachbearbeitung_trotzdem_eine``). Die Studierende auf
    dem MacBook haette die Variable gesetzt, die Suite gefahren und rote Proben gesehen —
    und den Fehler dort gesucht, wo keiner ist. Das ist derselbe Schaden, gegen den die
    Variable gebaut wurde.

    Wer den Faktor pruefen WILL, setzt ihn danach selbst: ``monkeypatch.setenv`` in der
    Probe wirkt nach dieser Vorbereitung.
    """
    monkeypatch.delenv(seams.ZEITFAKTOR_ENV, raising=False)


def test_die_proben_hier_laufen_auf_faktor_eins():
    """Die Gegenprobe zur Vorbereitung oben — ohne sie faellt diese Zeile um.

    Sie faellt nur dort, wo es darauf ankommt: auf einer Maschine, die den Faktor
    wirklich gesetzt hat. Genau deshalb steht sie hier und nicht als Kommentar.
    """
    assert seams.zeitfaktor() == seams.ZEITFAKTOR_VORGABE, (
        "Die Umgebung dieser Maschine faerbt auf die Proben ab. Die Vorbereitung "
        "`ohne_zeitfaktor` raeumt sie darum weg.")


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


def test_die_diagnose_der_ifc_steht_vor_dem_rauschen_der_fremden_bibliothek(ifc_datei):
    """BEFUND 19.09.2026: `ifc_zu_glb` hat die einzige brauchbare Meldung verworfen.

    Gemessen an einer umbenannten JPG mit der Endung `.ifc`::

        stdout   {"status":"error","error":"Error: Unable to parse IFC SPF header"}
        stderr   Exception ignored in: <function file.__del__ …>
                 KeyError: 404872384

    Die Naht baute ihre Meldung als `(stderr or stdout)`. Bei ifcopenshell 0.8.5 ist
    `stderr` **nie leer** — die Bibliothek hinterlaesst beim Herunterfahren eine
    Destruktor-Meldung, die mit der Ursache nichts zu tun hat. Also gewann immer das
    Rauschen. Wer eine beschaedigte IFC, eine umbenannte Datei oder eine `.skp`
    hineinlegte, sah **immer denselben KeyError aus einer fremden Bibliothek.**

    Die Zielgruppe sind Architektinnen und Studierende. Ein Stacktrace aus einem
    Destruktor ist fuer sie keine Antwort, sondern das Ende des Versuchs.

    **Die Reparatur lag seit dem 22.08.2026 zwanzig Zeilen tiefer:** `_fehlertext` ist
    genau dafuer gebaut, und `ifc_raeume` benutzt sie. `ifc_zu_glb` ist beim Nachziehen
    uebersehen worden, und weil der Fehlerweg nur im Fehlerfall laeuft, fiel es dreissig
    Tage lang niemandem auf. *Eine Reparatur, die nur an einer von zwei gleichen Stellen
    sitzt, ist eine halbe.*
    """
    aufrufer = Aufrufer(Ergebnis(
        returncode=1,
        stdout=json.dumps({"status": "error",
                           "error": "Error: Unable to parse IFC SPF header",
                           "glb_path": None}),
        stderr="Exception ignored in: <function file.__del__ at 0x7f6a>\nKeyError: 404872384\n"))

    with pytest.raises(SeamError) as fehler:
        seams.ifc_zu_glb(ifc_datei, "raus.glb", _starte=aufrufer)

    text = str(fehler.value)
    assert "Unable to parse IFC SPF header" in text, \
        "die einzige brauchbare Diagnose fehlt — genau das war der Befund"
    assert text.index("Unable to parse") < text.index("KeyError"), \
        "sie muss VOR dem Rauschen stehen; wer den ersten Satz liest, hat genug gelesen"
    assert "KeyError" in text, \
        "das Rauschen bleibt trotzdem drin — bei einem Absturz ist es die einzige Spur"


def test_die_ifc_naht_kommt_auch_ohne_lesbaren_report_zurecht(ifc_datei):
    """Die Gegenprobe: Ohne JSON auf stdout bleibt stderr die beste Quelle.

    Ohne sie waere «lies immer den Report» auch dann gruen, wenn es gar keinen gibt — und
    die Meldung waere leer statt roh.
    """
    aufrufer = Aufrufer(Ergebnis(returncode=1, stdout="", stderr="Segmentation fault"))

    with pytest.raises(SeamError, match="Segmentation fault"):
        seams.ifc_zu_glb(ifc_datei, "raus.glb", _starte=aufrufer)


def test_blender_zeigt_seinen_eigenen_report_statt_nur_sein_rauschen(tmp_path, blender_attrappe):
    """Derselbe Befund eine Ebene hoeher, nachgetragen am 19.09.2026.

    `blender_depth_stage` schreibt `blender-report.json` mit dem Feld `error` **auch wenn
    es scheitert**, und meldet den Fehlschlag danach ueber den Rueckgabewert 1. Die Naht
    zeigte bis hierher nur die letzten 1500 Zeichen Blender-Ausgabe — und der eine Satz,
    der die Ursache nennt, lag ungelesen in der Datei daneben.

    Blender laeuft in dieser Umgebung nicht; nachgestellt wird darum die Lage, nicht der
    Lauf: ein Aufrufer, der den Report schreibt und dann 1 zurueckgibt.
    """
    ziel = tmp_path / "raus"

    def schreibt_report(cmd):
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / "blender-report.json").write_text(
            json.dumps({"status": "error",
                        "error": "Kamera ausserhalb der Szene — kein Bauwerk im Bild"}),
            encoding="utf-8")

    aufrufer = Aufrufer(Ergebnis(returncode=1, stderr="Blender quit\n" * 200),
                        nebenwirkung=schreibt_report)

    with pytest.raises(SeamError) as fehler:
        glb_zu_tiefenkarte("bau.glb", ziel, up_axis="Y", _starte=aufrufer)

    assert "Kamera ausserhalb der Szene" in str(fehler.value), \
        "der Report lag daneben und wurde nicht gelesen — genau das war der Befund"


def test_ein_fehlender_report_wird_nicht_zur_leeren_meldung(tmp_path, blender_attrappe):
    """Die Gegenprobe dazu: Gibt es keinen Report, bleibt die rohe Ausgabe uebrig.

    Ohne sie koennte `_fehlertext` still eine leere Zeichenkette liefern, und die Meldung
    saehe aus wie «gescheitert, Grund unbekannt» — obwohl der Grund auf stderr steht.
    """
    aufrufer = Aufrufer(Ergebnis(returncode=1, stderr="Cycles: out of memory"))

    with pytest.raises(SeamError, match="out of memory"):
        glb_zu_tiefenkarte("bau.glb", tmp_path / "raus", up_axis="Y", _starte=aufrufer)


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

def test_ifc_lauf_ruft_das_fremde_venv_mit_dem_runner_auf(ifc_python_attrappe, tmp_path, ifc_datei):
    """LGPL-Auflage 1: Der Runner läuft im eigenen venv, nicht im Produkt-Interpreter."""
    aufrufer = Aufrufer(Ergebnis(stdout=json.dumps({"glb_path": "b.glb", "up_axis": "Y"})))

    bericht = ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=aufrufer)

    assert aufrufer.kommando[0] == ifc_python_attrappe
    assert aufrufer.kommando[1] == str(seams.IFC_RUNNER)
    assert bericht["up_axis"] == "Y", "Der eigene Pfad liefert glTF-konformes Y-up"


def test_ifc_lauf_meldet_rueckgabewert_ungleich_null(ifc_python_attrappe, tmp_path, ifc_datei):
    """Ein gescheiterter Subprozess wird zum ``SeamError`` — kein stilles Weiterlaufen."""
    aufrufer = Aufrufer(Ergebnis(returncode=2, stderr="ifcopenshell: Datei nicht lesbar"))

    with pytest.raises(SeamError) as fehler:
        ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=aufrufer)

    assert "Code 2" in str(fehler.value)
    assert "nicht lesbar" in str(fehler.value), "Die Meldung des Runners muss durchgereicht werden"


def test_ifc_lauf_meldet_nicht_json_ausgabe(ifc_python_attrappe, tmp_path, ifc_datei):
    """Die Verständigung läuft über JSON — was das nicht ist, wird als Nahtfehler gemeldet."""
    aufrufer = Aufrufer(Ergebnis(stdout="Segmentation fault (core dumped)"))

    with pytest.raises(SeamError, match="kein JSON"):
        ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=aufrufer)


def test_ifc_lauf_meldet_leere_ausgabe(ifc_python_attrappe, tmp_path, ifc_datei):
    """Auch ein stiller Runner ist ein Fehler: Ohne Report weiss der Aufrufer nichts."""
    with pytest.raises(SeamError, match="kein JSON"):
        ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=Aufrufer(Ergebnis(stdout="")))


def test_eine_skp_erreicht_den_subprozess_gar_nicht_mehr(ifc_python_attrappe, tmp_path):
    """DER SICHTGANG, VERDRAHTET — bis zum 19.09.2026 prueft diese Naht **gar nichts**.

    Nicht die Existenz, nicht die Endung, nicht den Inhalt. Eine `.skp` lief als kaputte
    IFC in den Subprozess und kam als Fehler einer fremden Bibliothek zurueck. Jetzt
    kostet die Abweisung einen Dateikopf und spart einen ganzen Prozessstart.

    Geprueft wird beides: **dass der Satz stimmt** und **dass nichts gestartet wurde.**
    Nur das erste zu pruefen liesse offen, ob die Ersparnis ueberhaupt eintritt.
    """
    (skp := tmp_path / "haus.skp").write_bytes(b"SketchUp Model\x00" + b"\x00" * 64)

    with pytest.raises(SeamError) as fehler:
        ifc_zu_glb(skp, tmp_path / "b.glb", _starte=verweigerer)

    text = str(fehler.value)
    assert "SketchUp" in text, "das Format muss beim Namen genannt werden"
    assert "IFC" in text, "und die Absage muss den Ausweg nennen"


def test_ein_NICHT_ERKANNTES_format_geht_weiterhin_durch(ifc_python_attrappe, tmp_path):
    """**Hier kehrt sich fail-closed um, und das ist der Entscheid dieser Stelle.**

    Abgewiesen wird nur, was der Sichtgang **sicher** ablehnt. Ein «nicht erkannt» geht
    durch zu ifcopenshell — und das ist Absicht, kein Nachlassen:

    Dies ist ein Tor, das **nachtraeglich** in einen laufenden Weg eingezogen wird. Ein
    neues Tor, das etwas sperrt, was gestern funktioniert hat, ist ein Rueckschritt und
    keine Verbesserung. Und «nicht erkannt» ist eine Aussage ueber **unsere Kennungen**,
    nicht ueber die Datei: ifcopenshell kennt mehr IFC-Formen als unser Dateikopf-Blick.
    Wer sie abwiese, ersetzte einen unverstaendlichen Fehlschlag durch einen unnoetigen.

    *Ohne diese Probe waere «weise alles ab, was du nicht kennst» ebenso gruen — und
    niemand saehe, dass damit brauchbare Dateien verloren gehen.*
    """
    (fremd := tmp_path / "eigenartig.ifc").write_bytes(b"etwas, das wir nicht kennen" * 4)
    aufrufer = Aufrufer(Ergebnis(stdout=json.dumps({"glb_path": "x.glb"})))

    ifc_zu_glb(fremd, tmp_path / "b.glb", _starte=aufrufer)

    assert aufrufer.kommandos, "der Subprozess muss gelaufen sein"


def test_die_installation_wird_vor_der_datei_geprueft(monkeypatch, tmp_path):
    """Fehlt das `.venv-ifc`, hilft kein Urteil ueber die Datei.

    Wer dann «deine Datei gibt es nicht» zu hoeren bekaeme, suchte den Fehler bei sich,
    waehrend er bei der Einrichtung liegt. *Eine Frage nach dem Gegenstand setzt voraus,
    dass das Werkzeug ihn ueberhaupt anfassen koennte.*
    """
    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(SeamError, match=".venv-ifc"):
        ifc_zu_glb(tmp_path / "gibtsnicht.ifc", tmp_path / "b.glb", _starte=verweigerer)


def test_ifc_lauf_startet_nichts_ohne_venv(monkeypatch, tmp_path, ifc_datei):
    """Fehlt das ``.venv-ifc``, wird gar kein Prozess versucht — und schon gar nicht der eigene."""
    monkeypatch.delenv("AIIMAGING_IFC_PYTHON", raising=False)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with pytest.raises(SeamError, match=".venv-ifc"):
        ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=verweigerer)


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
    assert "--auge=1.0,-2.0,1.7" in kommando
    assert "--blick-auf=0.0,0.0,5.0" in kommando


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
    assert not any(str(a).startswith("--brennweite") for a in ohne)
    mit = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y", kamera="n",
                                  brennweite=35.0)
    assert "--brennweite=35.0" in mit


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
    assert "--gelaende-z=412.5" in kommando
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


# ---------------------------------------------------------------------------------------
# Negative Koordinaten — am Gerät gefunden, 19.08.2026
# ---------------------------------------------------------------------------------------
#
# Der erste echte Auftrag der fremden Brücke trug drei Kameras. Zwei liefen; die dritte
# stand INNEN, mit `auge` [-6.854, 1.6, 6.854], und brach ab mit
#
#     blender: error: argument --auge: expected one argument
#
# `argparse` liest jedes Wort mit führendem Minus als Option. Der Fehler war nicht selten,
# er war unerreichbar: Jede bis dahin gemessene Kamera stand VOR dem Bauwerk, also im
# positiven Bereich. Erst eine Innenraumkamera hat mindestens eine negative Koordinate.

def test_negative_koordinaten_bleiben_am_flag_haengen():
    """`--auge=-6.854,…` statt `--auge -6.854,…` — sonst frisst argparse den Wert."""
    cmd = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                  auge=(-6.854, 1.6, 6.854), blick_auf=(0.0, 1.6, 0.0))
    assert "--auge=-6.854,1.6,6.854" in cmd
    assert "--blick-auf=0.0,1.6,0.0" in cmd
    # Und das Minus steht NIE allein als eigenes Argument da:
    assert not any(str(a).startswith("-6.854") for a in cmd)


def test_auch_das_gelaende_traegt_das_minus():
    """Nicht nur die Kamera: Ein Gelände unter dem Nullpunkt ist negativ."""
    cmd = baue_kommando_multipass("/tmp/a.glb", "/tmp/aus", up_axis="Y",
                                  kamera="n", gelaende_z=-1.5)
    assert "--gelaende-z=-1.5" in cmd


def test_auch_die_huellbox_traegt_das_minus():
    """Eine Hüllbox mit Ursprung in der Mitte hat drei negative Ecken.

    `baue_kommando_multipass` reicht sie nicht durch, `glb_zu_multipass` schon —
    geprüft wird darum die gemeinsame Quelle beider.
    """
    from aiimaging.seams import _multipass_argumente
    args = _multipass_argumente("/tmp/a.glb", "/tmp/aus", drehen=False, aufloesung=512,
                                samples=16, beauty=True, material_id=True,
                                kamera_huellbox=((-3.0, -4.0, -0.5), (3.0, 4.0, 9.0)))
    assert "--kamera-huellbox=-3.0,-4.0,-0.5,3.0,4.0,9.0" in args


# ======================================================================================
# Der Trockenlauf muss dasselbe Kommando zeigen wie der echte Lauf
# ======================================================================================
#
# Nachgetragen am 26.08.2026, nachdem genau das auseinandergelaufen war.

def test_trockenlauf_und_echter_lauf_kennen_dieselben_einstellungen():
    """Die beiden Signaturen dürfen sich nur in dem unterscheiden, was ein Lauf braucht.

    **Der Anlass ist ein Auseinanderlaufen, das der gemeinsame Helfer verhindern sollte.**
    `_multipass_argumente` ist genau dafür gebaut — sein Docstring sagt: *«Wären sie
    zweimal geschrieben, könnten `glb_zu_multipass` und `baue_kommando_multipass`
    auseinanderlaufen — und dann prüfte der Test ein Kommando, das so nie gestartet
    wird.»*

    Am 26.08.2026 war genau das eingetreten: **Der Helfer war geteilt, die Aufrufe waren
    es nicht.** `baue_kommando_multipass` kannte `kamera_huellbox` gar nicht — der
    Trockenlauf zeigte ein Kommando ohne die Hüllbox, der echte Lauf startete eines mit
    ihr. *Ein gemeinsamer Helfer schützt nicht davor, ihn verschieden aufzurufen.*
    """
    import inspect
    echt = set(inspect.signature(seams.glb_zu_multipass).parameters)
    trocken = set(inspect.signature(seams.baue_kommando_multipass).parameters)

    # Was nur der echte Lauf hat, und **jeder Eintrag mit Grund** — eine Ausnahmeliste
    # ohne Begruendung ist eine Einladung, den naechsten Unterschied hineinzuschreiben:
    #
    #   timeout, starte, _starte  — betreffen das AUSFUEHREN. Ein Trockenlauf fuehrt
    #                               nichts aus; `_starte` ist die Naht fuer Attrappen.
    #   stillstand_frist_s        — wird von `glb_zu_multipass` IMMER abgewiesen und
    #                               steht nur da, damit ein Aufrufer eine klare Fehler-
    #                               meldung bekommt statt stillen Wirkungslosigkeit.
    #                               Er erzeugt kein Argument und kann darum keines
    #                               auseinanderlaufen lassen.
    nur_lauf = {"timeout", "starte", "_starte", "stillstand_frist_s"}
    fehlt_im_trockenlauf = echt - trocken - nur_lauf
    assert not fehlt_im_trockenlauf, (
        f"`baue_kommando_multipass` kennt diese Einstellungen nicht: "
        f"{sorted(fehlt_im_trockenlauf)}. Der Trockenlauf zeigt dann ein Kommando, das "
        f"der echte Lauf so nie startet — und ein Test darauf prüft eine Erfindung.")

    zuviel = trocken - echt
    assert not zuviel, (
        f"`baue_kommando_multipass` nimmt {sorted(zuviel)} entgegen, der echte Lauf "
        f"nicht. Dann lässt sich etwas trocken zeigen, was nie laufen kann.")


def test_beide_erzeugen_bei_gleichen_angaben_dasselbe_kommando():
    """Die Gegenprobe zur Signaturprüfung — gleiche Namen genügen nicht.

    Zwei Funktionen können dieselben Parameter führen und trotzdem verschiedene Kommandos
    bauen, wenn eine davon einen Wert nicht weiterreicht. *Genau das war der Fehler: Der
    Parameter fehlte in der Signatur, aber sichtbar wurde es erst am Kommando.*
    """
    angaben = dict(up_axis="Y_UP", aufloesung=256, samples=4, kamera="sSE",
                   brennweite=35.0, kamera_modus="shift", gelaende_z=-1.5,
                   hoehe=192, kamera_huellbox=((0.0, 0.0, 0.0), (5.0, 5.0, 5.0)),
                   sonne={"elevation": 25.0, "azimuth": -40.0},
                   deckungsgrad=0.55, augenhoehe=1.7, bias_grad=35.0)

    # OHNE BLENDER GIBT ES HIER NICHTS ZU VERGLEICHEN — und das ist ein SKIP, kein Fehler.
    #
    # `glb_zu_multipass` sucht das Binary, BEVOR es das Kommando baut. Fehlt es, fliegt
    # ein `SeamError` aus `finde_blender`, und der sah bis zum 16.09.2026 genauso aus wie
    # der Sentinel unten: Der Test meldete «Der echte Lauf hat kein Kommando gebaut» und
    # klang nach einem Defekt in der Naht. *Ein Test, der ein fehlendes Werkzeug als
    # Fehler des Programms meldet, schickt den Leser in die falsche Datei.*
    #
    # Aufgefallen an einem frischen Container ohne Blender — dieselbe Lage, in der die
    # uebrigen 144 Proben sauber uebersprungen werden.
    try:
        seams.finde_blender()
    except seams.SeamError as fehlt:
        pytest.skip(f"Blender ist auf diesem Geraet nicht da: {fehlt}")

    gesehen = {}
    SENTINEL = "nur das Kommando einsammeln"

    def _falscher_start(cmd, timeout):
        gesehen["cmd"] = list(cmd)
        raise seams.SeamError(SENTINEL)

    # NUR DEN SENTINEL VERSCHLUCKEN, nicht jeden SeamError. Ein echter Fehler weiter
    # innen kaeme sonst als «kein Kommando gebaut» heraus — dieselbe Verwechslung eine
    # Ebene tiefer.
    try:
        seams.glb_zu_multipass("x.glb", "/tmp/aus", _starte=_falscher_start, **angaben)
    except seams.SeamError as fehler:
        if SENTINEL not in str(fehler):
            raise

    trocken = seams.baue_kommando_multipass("x.glb", "/tmp/aus", **angaben)
    assert gesehen.get("cmd"), "Der echte Lauf hat kein Kommando gebaut."

    def _nur_argumente(cmd):
        return [a for a in cmd if a.startswith("--")]

    assert _nur_argumente(gesehen["cmd"]) == _nur_argumente(trocken), (
        f"Die beiden Kommandos gehen auseinander.\n"
        f"  echt:    {_nur_argumente(gesehen['cmd'])}\n"
        f"  trocken: {_nur_argumente(trocken)}")


def test_die_drei_kameraparameter_erreichen_den_runner():
    """`--deckungsgrad`, `--augenhoehe` und `--bias` — bis zum 26.08.2026 nie gesetzt.

    Der Runner kennt alle drei seit jeher; **diese Naht setzte keinen einzigen davon.**
    Auf dem Produktivweg galten also immer seine Vorgaben, und wer etwas anderes wollte,
    musste den Runner selbst aufrufen.

    Das ist mehr als unbequem: `auf-20260825-41` vergleicht Bildpaare bei Deckungsgrad
    **0,55 gegen 0,70** — und diese Messung war über diesen Weg gar nicht durchführbar.
    Die Augenhöhe wiederum ist genau die Grösse, über die Frage 7 des Übergabeblatts mit
    KosmoOrbit verhandelt wird. *Über einen Wert zu verhandeln, den man nicht einstellen
    kann, ist müssig.*
    """
    cmd = seams.baue_kommando_multipass("x.glb", "/tmp/aus", up_axis="Y_UP",
                                        deckungsgrad=0.55, augenhoehe=1.3,
                                        bias_grad=20.0)
    assert "--deckungsgrad=0.55" in cmd
    assert "--augenhoehe=1.3" in cmd
    assert "--bias=20.0" in cmd


def test_ohne_angabe_wird_keiner_der_drei_gesetzt():
    """**Nicht angefasst ist etwas anderes als null.**

    Ein mitgeschickter Vorgabewert wäre im Bericht des Runners von einer Bestellung nicht
    mehr zu unterscheiden — dieselbe Regel wie beim Sonnenstand.
    """
    cmd = seams.baue_kommando_multipass("x.glb", "/tmp/aus", up_axis="Y_UP")
    for schalter in ("--deckungsgrad", "--augenhoehe", "--bias"):
        assert not any(a.startswith(schalter) for a in cmd), (
            f"{schalter} steht im Kommando, obwohl nichts bestellt war.")


# ======================================================================================
# DIE ZEITGRENZEN — nachgesehen am 18.09.2026, als die Zielmaschine gewechselt hat
# ======================================================================================
#
# Nicht mehr die HomeStation (Ryzen 9 9950X, 16 Kerne), sondern der Laptop einer
# Studierenden. Eine Frist, die auf dem langsamen Gerät zuschlägt, ohne dass etwas kaputt
# ist, ist schlimmer als keine: Sie macht aus einem langsamen Lauf einen Fehlschlag, und
# die Nutzerin sucht den Fehler an der falschen Stelle.
#
# Die Proben hier trennen zwei Sorten Frist, und die Trennung ist der ganze Punkt:
#
#   * MASCHINENFEST sind die Fristen auf unser eigenes Lebenszeichen (Herzschlag,
#     Anlauf). Sie messen nicht die Rechenzeit, sondern einen Faden, den wir selbst
#     starten — sie dürfen auf einem langsamen Gerät bleiben, wie sie sind.
#   * MASCHINENGEBUNDEN sind die Gesamtfristen. Sie decken die Rechenzeit und sind damit
#     eine Aussage über EINE Maschine.


def _report_schreiber():
    """Ein ``_starte``, das tut, was Blender täte: den Report hinterlassen."""
    return Aufrufer(nebenwirkung=lambda cmd: Path(
        cmd[cmd.index("--out") + 1], "blender-report.json").write_text(
            "{}", encoding="utf-8"))


class Uhr:
    """Eine Uhr, die nur vorrückt, wenn man sie schiebt.

    Ohne sie liesse sich ein kalter Start von 13 Sekunden nur prüfen, indem man dreizehn
    Sekunden wartet — und ein Test, der so teuer ist, läuft nicht.
    """

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def weiter(self, s):
        self.t += float(s)


# --------------------------------------------------------------------------------------
# 1 · Jede Zahl sagt, worauf sie ruht
# --------------------------------------------------------------------------------------

#: Die Zeitgrenzen dieses Moduls. Wer eine neue hinzufügt, trägt sie hier nach — und
#: merkt dabei, dass er ihre Herkunft aufschreiben muss.
ZEITGRENZEN = (
    "TAKT_S", "BLENDER_TAKT_S", "BLENDER_GPU_STILLE_S", "HERZSCHLAG_TAKT_S",
    "ANLAUF_S", "HERZSCHLAG_AUSFAELLE", "BLENDER_FRIST_MIN_S",
    "GESAMTFRIST_IFC_S", "ZEITDECKEL_HOMESTATION_S", "GESAMTFRIST_NACHBEARBEITUNG_S",
)

#: Woran man erkennt, dass die Herkunft dasteht.
HERKUNFTSWOERTER = ("gemessen", "gesetzt", "setzung", "messung")


def _herkunftstext(name: str) -> str:
    """Der Kommentarblock über einer Zuweisung — das, was ihre Herkunft tragen muss."""
    zeilen = Path(seams.__file__).read_text(encoding="utf-8").splitlines()
    treffer = [i for i, z in enumerate(zeilen) if z.startswith(f"{name} = ")]
    assert len(treffer) == 1, f"{name} ist nicht genau einmal zugewiesen: {len(treffer)}×"
    i = treffer[0] - 1
    block = []
    while i >= 0 and zeilen[i].lstrip().startswith("#"):
        block.append(zeilen[i])
        i -= 1
    return "\n".join(reversed(block))


@pytest.mark.parametrize("name", ZEITGRENZEN)
def test_jede_zeitgrenze_sagt_ob_sie_gemessen_oder_gesetzt_ist(name):
    """Hausregel: Wo eine Zahl steht, steht daneben, ob sie GEMESSEN oder GESETZT ist.

    Der Anlass ist der Maschinenwechsel: Erst an der Herkunft lässt sich entscheiden, ob
    eine Zahl auf ein anderes Gerät mitgenommen werden darf. Eine Frist ohne Herkunft
    wandert stillschweigend mit — und schlägt drüben zu, ohne dass jemand weiss, warum sie
    je so hoch stand.
    """
    text = _herkunftstext(name).lower()
    assert any(w in text for w in HERKUNFTSWOERTER), (
        f"Über {name} steht nicht, worauf die Zahl ruht. Erwartet wird eines dieser "
        f"Wörter: {HERKUNFTSWOERTER}. Ohne das ist auf einem anderen Gerät nicht "
        f"entscheidbar, ob die Zahl mitgenommen werden darf.")


def test_die_gesamtfrist_des_blender_laufs_nennt_ihre_maschine_im_namen():
    """900 s sind keine Eigenschaft eines Laufs, sondern eine Auskunft über einen Rechner.

    Der Name trägt sie mit, damit niemand sie auf einem Laptop für ein Naturgesetz hält.
    Die Zahl selbst bleibt, wo sie ist: `abholer.ZEITDECKEL_S` hängt daran, und
    `tests/test_durchreichung_verarbeiter.py` hält beide aneinander.
    """
    import inspect
    assert seams.ZEITDECKEL_HOMESTATION_S == 900
    vorgabe = inspect.signature(seams.glb_zu_multipass).parameters["timeout"].default
    assert vorgabe == seams.ZEITDECKEL_HOMESTATION_S


# --------------------------------------------------------------------------------------
# 2 · Der Anlauf der Herzschlagwache — die Frist, die auf dem Laptop als erste zuschlug
# --------------------------------------------------------------------------------------
#
# GEMESSEN am 10.09.2026 in dieser Umgebung: Der erste `blender --background --version`
# braucht 12,63 s, die drei danach 0,66 / 0,26 / 0,15 s. Die Herzschlagwache hatte eine
# Frist von 10 s und KEINEN Anlauf — vor dem ersten Schlag gibt es die Datei nicht, die
# Wache zählt keinen Schritt, und die kurze Frist gilt vom ersten Blick an.

def _gebaute_wache(monkeypatch, tmp_path, **kw):
    """Die Wache abfangen, die `glb_zu_multipass` für den Herzschlag baut."""
    gebaut = {}

    def merke(wache=None, **_kw):
        gebaut["wache"] = wache
        raise SeamError("Wache gebaut")

    monkeypatch.setattr(seams, "starter_mit_wache", merke)
    glb = tmp_path / "m.glb"
    glb.write_bytes(b"glTF")
    with pytest.raises(SeamError, match="Wache gebaut"):
        seams.glb_zu_multipass(glb, tmp_path / "aus", up_axis="Y_UP",
                               herzschlag_takt_s=2.0, **kw)
    return gebaut["wache"]


def test_der_anlauf_wird_vom_zeitfaktor_gestreckt(monkeypatch):
    """BEFUND 18.09.2026: ``ANLAUF_S`` stand unter MASCHINENFEST und misst Maschinenzeit.

    Die anderen drei Zahlen dieser Gruppe messen einen Faden, den wir selbst starten — der
    schlaegt auf jedem Geraet gleich schnell. Der Anlauf deckt die Spanne DAVOR: Blender
    kalt starten und Python laden, also Rechenzeit. Der Kommentar an der Konstante
    begruendet die 60 s selbst mit einer Kaltstartmessung von 12,63 s *in dieser
    Umgebung*.

    Solange ``zeitfaktor()`` nicht darauf wirkte, war das auf dem langsamen Zielgeraet die
    Frist, die als erste zuschlaegt — **und die einzige, die sich nicht strecken laesst.**
    Wer ``AIIMAGING_ZEITFAKTOR`` setzt, dehnte jede Gesamtfrist und stand trotzdem vor
    einem Lauf, der beim kalten Start abbricht.

    Die Gegenprobe steckt mit drin: Bei Faktor 1.0 kommt die Zahl UNVERAENDERT zurueck.
    Die HomeStation sieht nach einem ``git pull`` genau dieselbe Frist wie vorher — eine
    Verhaltensaenderung waere dort meldepflichtig, und hier gibt es keine.
    """
    assert seams.anlauf_frist_s() == seams.ANLAUF_S, \
        "ohne Angabe darf sich nichts aendern — sonst ist es eine stille Umstellung"

    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "3")
    assert seams.anlauf_frist_s() == pytest.approx(3 * seams.ANLAUF_S), \
        "der Anlauf muss mitwachsen, sonst bricht der kalte Start trotz gesetztem Faktor"

    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "0.5")
    assert seams.anlauf_frist_s() == pytest.approx(0.5 * seams.ANLAUF_S), \
        "und in die andere Richtung ebenso — ein Faktor, der nur streckt, ist keiner"


def test_die_wachen_holen_den_anlauf_ueber_die_frist_und_nicht_ueber_die_konstante():
    """Der Wert allein genuegt nicht — er muss auch dort ankommen, wo gewacht wird.

    Ohne diese Probe bliebe die obige gruen, waehrend die Wache weiterhin die rohe
    Konstante bekaeme: eine Funktion, die richtig rechnet und die niemand ruft.
    """
    quelle = (Path(seams.__file__)).read_text(encoding="utf-8")
    baum = ast.parse(quelle)
    roh = [k.lineno for k in ast.walk(baum)
           if isinstance(k, ast.keyword) and k.arg == "anlauf_s"
           and isinstance(k.value, ast.Name) and k.value.id == "ANLAUF_S"]
    assert not roh, (
        f"seams.py reicht ANLAUF_S roh an eine Wache durch (Zeile(n) {roh}) — dort "
        f"gehoert anlauf_frist_s() hin, sonst wirkt der Zeitfaktor nicht."
    )


def test_die_herzschlagwache_bekommt_einen_anlauf(tmp_path, monkeypatch, blender_attrappe):
    """Ohne Anlauf reisst der kalte Blender-Start die Frist, bevor der erste Schlag kommt."""
    wache = _gebaute_wache(monkeypatch, tmp_path)

    assert wache.anlauf_s == seams.ANLAUF_S, (
        "Die Herzschlagwache läuft ohne Anlauf. Vor dem ersten Schlag gibt es die Datei "
        "nicht — dann gilt vom ersten Blick an die kurze Frist, und der Blender-Start "
        "passt nicht hinein.")
    assert wache.anlauf_s > 12.63, (
        "Der Anlauf muss über dem gemessenen kalten Start von 12,63 s liegen.")
    assert wache.frist_s == seams.HERZSCHLAG_AUSFAELLE * 2.0, (
        "Nach dem ersten Schlag gilt wieder die kurze Frist — der Anlauf ist keine "
        "Lockerung der Wache.")


def test_ein_kalter_start_ueberlebt_die_herzschlagwache(tmp_path, monkeypatch,
                                                        blender_attrappe):
    """Die Gegenprobe am Verhalten, nicht am Feld: 30 s ohne Herzschlag sind kein Stillstand.

    Geprüft werden die Werte, die `glb_zu_multipass` der Wache wirklich mitgibt — nachgebaut
    mit einer stellbaren Uhr, weil ein Test, der dreissig Sekunden wartet, nicht läuft.
    """
    from aiimaging import fortschritt

    echte = _gebaute_wache(monkeypatch, tmp_path)
    uhr = Uhr()
    schlag = tmp_path / "leer" / seams.HERZSCHLAG_DATEI          # gibt es noch nicht
    wache = fortschritt.wache_fuer_datei(
        schlag, frist_s=echte.frist_s, anlauf_s=echte.anlauf_s, _uhr=uhr)

    uhr.weiter(30.0)                      # kalter Start: Blender lädt, nichts schlägt
    befund = wache.blick()
    assert befund["schwere"] != fortschritt.SCHWERE_FEHLER, (
        "Ein Lauf, der noch nicht angefangen hat, ist nicht stehengeblieben — und ein "
        "kalter Blender-Start dauert gemessen über 12 s.")
    assert befund["im_anlauf"] is True

    schlag.parent.mkdir(parents=True, exist_ok=True)
    schlag.write_text("1 30.0\n", encoding="utf-8")
    wache.blick()                         # der erste Schlag ist da
    uhr.weiter(30.0)
    assert wache.blick()["schwere"] == fortschritt.SCHWERE_FEHLER, (
        "Nach dem ersten Schlag muss wieder die kurze Frist gelten. Sonst wäre der "
        "Anlauf eine stille Entschärfung der Wache.")


# --------------------------------------------------------------------------------------
# 3 · Der Herzschlag des Vorlaufs — eine Datei, die den neuen Lauf umbringt
# --------------------------------------------------------------------------------------

def test_der_herzschlag_des_vorlaufs_wird_vor_dem_start_entfernt(tmp_path, blender_attrappe):
    """`out_dir` wird wiederverwendet — die alte Datei sähe aus wie ein Schlag dieses Laufs.

    Und sie wäre teuer: Die Wache zählte beim ersten Blick einen Schritt, der Anlauf wäre
    damit verbraucht, und es gälte vom Start weg die kurze Frist, die der kalte
    Blender-Start reisst. Die Datei von gestern brächte den Lauf von heute um.
    """
    aus = tmp_path / "aus"
    aus.mkdir()
    alt = aus / seams.HERZSCHLAG_DATEI
    alt.write_text("88 176.6\n", encoding="utf-8")

    glb_zu_tiefenkarte("bau.glb", aus, up_axis="Y", _starte=_report_schreiber())

    assert not alt.exists(), (
        "Der Herzschlag des Vorlaufs liegt noch da. Die Wache dieses Laufs liest ihn als "
        "eigenes Zeichen — dieselbe Lehre wie beim Report: Die Existenz einer Datei ist "
        "kein Beleg für ihren Lauf.")


def test_ein_liegengebliebener_herzschlag_verbraucht_den_anlauf(tmp_path):
    """Warum die Zeile oben nötig ist — am Mechanismus gezeigt, nicht behauptet."""
    from aiimaging import fortschritt

    uhr = Uhr()
    schlag = tmp_path / seams.HERZSCHLAG_DATEI
    schlag.write_text("88 176.6\n", encoding="utf-8")          # der Lauf von gestern
    wache = fortschritt.wache_fuer_datei(schlag, frist_s=10.0, anlauf_s=60.0, _uhr=uhr)

    wache.blick()                          # die alte Datei zählt als Zeichen
    uhr.weiter(30.0)
    assert wache.blick()["schwere"] == fortschritt.SCHWERE_FEHLER, (
        "Mit einer liegengebliebenen Datei gilt sofort die kurze Frist — genau darum "
        "wird sie vor dem Lauf entfernt.")


# --------------------------------------------------------------------------------------
# 4 · Die Gesamtfrist ist ein Budget, kein Hängerwächter
# --------------------------------------------------------------------------------------

def test_ohne_gesamtfrist_laeuft_der_blender_lauf_weiter(tmp_path, blender_attrappe):
    """`timeout=None` heisst: Die Stillstandswache urteilt, nicht die Uhr.

    Das ist die Bauform für ein langsames Gerät. Der Hänger fällt weiter nach zehn
    Sekunden auf (Herzschlag); was entfällt, ist allein das Budget — und ein Budget ist
    eine Aussage über die Maschine, nicht über den Lauf.
    """
    aufrufer = _report_schreiber()

    glb_zu_tiefenkarte("bau.glb", tmp_path / "aus", up_axis="Y", timeout=None,
                       _starte=aufrufer)

    assert aufrufer.timeouts == [None], "None muss als None ankommen, nicht als Zahl"


def test_ohne_frist_und_ohne_wache_wird_abgewiesen(tmp_path, blender_attrappe):
    """Beides zugleich abzuschalten hiesse, einen unbegrenzten Prozess zu starten.

    Fail-closed: Genau eines von beidem muss stehen. Und die Meldung nennt den Ausweg,
    statt ihn raten zu lassen.
    """
    with pytest.raises(SeamError) as fehler:
        seams.glb_zu_multipass("bau.glb", tmp_path / "aus", up_axis="Y",
                               timeout=None, herzschlag_takt_s=None)

    assert "herzschlag_takt_s" in str(fehler.value)


def test_die_ifc_laeufe_lassen_sich_die_frist_nicht_nehmen(ifc_python_attrappe, tmp_path, ifc_datei):
    """Hinter ihnen wacht nichts — der Runner meldet sich erst am Ende.

    Darum ist `None` hier kein zulässiger Wert, und es wird auch kein Prozess gestartet:
    `verweigerer` belegt, dass vorher abgebrochen wurde.
    """
    for lauf in (lambda: ifc_zu_glb(ifc_datei, tmp_path / "b.glb",
                                    timeout=None, _starte=verweigerer),
                 lambda: seams.ifc_raeume(tmp_path / "b.ifc", timeout=None,
                                          _starte=verweigerer)):
        with pytest.raises(SeamError) as fehler:
            lauf()
        assert seams.ZEITFAKTOR_ENV in str(fehler.value), (
            "Die Meldung muss den Weg für eine langsame Maschine NENNEN.")


# --------------------------------------------------------------------------------------
# 5 · Der Zeitfaktor — die Maschine gibt über sich selbst Auskunft
# --------------------------------------------------------------------------------------
#
# Keine erfundene Laptop-Zahl: In diesem Repo ist für kein MacBook etwas gemessen. Was es
# gibt, ist eine Stelle, an der eine langsamere Maschine sagen kann, WIEVIEL langsamer sie
# ist — und ohne Angabe ändert sich nirgends etwas.

def test_ohne_angabe_bleibt_jede_frist_auf_die_zahl_genau_wie_bisher(tmp_path,
                                                                     blender_attrappe,
                                                                     monkeypatch):
    """Die HomeStation fährt diesen Code — sie muss dieselbe Zahl sehen wie gestern."""
    monkeypatch.delenv(seams.ZEITFAKTOR_ENV, raising=False)
    aufrufer = _report_schreiber()

    glb_zu_tiefenkarte("bau.glb", tmp_path / "aus", up_axis="Y", _starte=aufrufer)

    assert aufrufer.timeouts == [seams.ZEITDECKEL_HOMESTATION_S]
    assert isinstance(aufrufer.timeouts[0], int), (
        "Ohne Faktor wird nicht einmal der Typ angefasst — sonst stünde in Berichten "
        "plötzlich 900.0, wo bisher 900 stand.")


def test_der_faktor_streckt_die_gesamtfrist_des_blender_laufs(tmp_path, blender_attrappe,
                                                              monkeypatch):
    """Drei heisst: Diese Maschine braucht für dasselbe dreimal so lange."""
    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "3")
    aufrufer = _report_schreiber()

    glb_zu_tiefenkarte("bau.glb", tmp_path / "aus", up_axis="Y", _starte=aufrufer)

    assert aufrufer.timeouts == [3 * seams.ZEITDECKEL_HOMESTATION_S]


def test_der_faktor_streckt_auch_die_ifc_laeufe(ifc_python_attrappe, tmp_path, monkeypatch, ifc_datei):
    """Sonst bliebe die Frist ohne Wache ausgerechnet die, die niemand strecken kann."""
    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "2.5")
    aufrufer = Aufrufer(Ergebnis(stdout=json.dumps({"glb_path": "b.glb", "up_axis": "Y"})))

    ifc_zu_glb(ifc_datei, tmp_path / "b.glb", _starte=aufrufer)

    assert aufrufer.timeouts == [2.5 * seams.GESAMTFRIST_IFC_S]


def test_eine_bestellte_frist_wird_mitgestreckt(tmp_path, blender_attrappe, monkeypatch):
    """Auch die Zahl des Aufrufers ist auf der schnellen Maschine gesetzt worden.

    `abholer.ZEITDECKEL_S` reicht sie IMMER durch — hier ankommend als 900. Wirkte der
    Faktor nur auf den Vorgabewert, bliebe der Produktivweg auf dem Laptop ungedeckt.
    """
    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "4")
    aufrufer = _report_schreiber()

    glb_zu_tiefenkarte("bau.glb", tmp_path / "aus", up_axis="Y", timeout=900,
                       _starte=aufrufer)

    assert aufrufer.timeouts == [3600.0]


@pytest.mark.parametrize("roh", ["viel", "3,5", "0", "-2", "inf", "nan"])
def test_ein_unlesbarer_faktor_wird_abgewiesen_statt_verworfen(roh, tmp_path,
                                                               blender_attrappe,
                                                               monkeypatch):
    """Ein Tippfehler darf nicht stillschweigend die alte Frist gelten lassen.

    Das wäre genau der Schaden, gegen den die Variable gebaut ist: Der Lauf bräche auf dem
    langsamen Gerät ab, und die Angabe, die ihn retten sollte, sähe aus, als wirkte sie.
    """
    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, roh)

    with pytest.raises(SeamError) as fehler:
        seams.glb_zu_multipass("bau.glb", tmp_path / "aus", up_axis="Y",
                               _starte=verweigerer)

    assert seams.ZEITFAKTOR_ENV in str(fehler.value)


def test_eine_leere_angabe_ist_keine_angabe(monkeypatch):
    """Eine leergeräumte Umgebungsvariable heisst «nicht gesetzt», nicht «kaputt»."""
    monkeypatch.setenv(seams.ZEITFAKTOR_ENV, "  ")
    assert seams.zeitfaktor() == seams.ZEITFAKTOR_VORGABE


# --------------------------------------------------------------------------------------
# 6 · Die Nachbearbeitung erbt die Wache des Renderlaufs nicht
# --------------------------------------------------------------------------------------

def _lauf_mit_attrappenstarter(monkeypatch, tmp_path, **kw):
    """Ein Lauf mit Herzschlagzweig, aber ohne echten Prozess — gibt zurück, was die
    Nachbearbeitung bekommen hat."""
    gesehen = {}

    def merke(report, out_dir, **kwargs):
        gesehen.update(kwargs)
        return report

    def starter(wache=None, **_kw):
        def starte(cmd, timeout):
            Path(cmd[cmd.index("--out") + 1], "blender-report.json").write_text(
                "{}", encoding="utf-8")
            return Ergebnis()
        return starte

    monkeypatch.setattr(seams, "_tiefe_nachbearbeiten", merke)
    monkeypatch.setattr(seams, "starter_mit_wache", starter)
    seams.glb_zu_multipass("bau.glb", tmp_path / "aus", up_axis="Y", **kw)
    return gesehen


def test_die_nachbearbeitung_bekommt_nicht_den_wachstarter(tmp_path, monkeypatch,
                                                           blender_attrappe):
    """Sonst liefe sie unter einer Wache auf eine Datei, die niemand mehr schreibt.

    Blender ist zu diesem Zeitpunkt beendet, `herzschlag.txt` rührt sich nicht mehr, und
    die Stillstandsuhr der wiederverwendeten Wache läuft seit dem letzten Schlag. Der
    Rückfall auf einen zweiten Blender-Prozess wäre fast sofort als «Stillstand»
    abgeräumt worden — und im Report stünde ein irreführendes `depth_png_fehler` statt
    einer Tiefenkarte.
    """
    gesehen = _lauf_mit_attrappenstarter(monkeypatch, tmp_path, herzschlag_takt_s=2.0)

    assert gesehen["_starte"] is None, (
        "Die Nachbearbeitung hat den überwachten Starter des Renderlaufs geerbt.")


def test_die_naht_des_aufrufers_erreicht_die_nachbearbeitung_weiterhin(tmp_path,
                                                                       monkeypatch,
                                                                       blender_attrappe):
    """Die Gegenprobe: Was der Aufrufer schickt, muss ankommen — sonst wäre die
    EXR-Nachbearbeitung ohne Blender nicht mehr prüfbar."""
    gesehen = {}

    def merke(report, out_dir, **kwargs):
        gesehen.update(kwargs)
        return report

    monkeypatch.setattr(seams, "_tiefe_nachbearbeiten", merke)
    aufrufer = _report_schreiber()

    glb_zu_tiefenkarte("bau.glb", tmp_path / "aus", up_axis="Y", _starte=aufrufer)

    assert gesehen["_starte"] is aufrufer


def test_ohne_gesamtfrist_hat_die_nachbearbeitung_trotzdem_eine(tmp_path, monkeypatch,
                                                                blender_attrappe):
    """Hinter ihr wacht nichts — wie bei den IFC-Läufen. `None` dürfte hier nicht ankommen."""
    gesehen = _lauf_mit_attrappenstarter(monkeypatch, tmp_path, herzschlag_takt_s=2.0,
                                         timeout=None)

    assert gesehen["timeout"] == seams.GESAMTFRIST_NACHBEARBEITUNG_S


# --------------------------------------------------------------------------------------
# 7 · Die Stelle, an der `timeout=None` wirklich ankommt — der ueberwachte Starter
# --------------------------------------------------------------------------------------
#
# NACHGETRAGEN AM 18.09.2026 BEI DER GEGENPRUEFUNG, und der Anlass ist ein Waechter ohne
# Probe: `starter_mit_wache` hat beim Erlauben von `timeout=None` zwei neue Zweige
# bekommen — die Abfrage `timeout is not None` in der Warteschleife und die
# Stillstandsmeldung, die ohne Gesamtfrist anders lautet. Beide waren durch NICHTS
# gedeckt.
#
# GEMESSEN (18.09.2026): Setzt man beide Zweige auf den Stand von vorher zurueck, bleiben
# `tests/test_seams.py` und `tests/test_fortschritt.py` zusammen bei 168 von 168 gruen —
# waehrend der echte Aufruf `glb_zu_multipass(..., timeout=None)` mit voreingestelltem
# Herzschlag beim ersten Blick stirbt:
#
#     TypeError: '>' not supported between instances of 'float' and 'NoneType'
#
# Also ausgerechnet auf dem Weg, fuer den `timeout=None` gebaut wurde: dem langsamen
# Laptop. Die Proben weiter oben fassen das nicht, weil sie alle ein eigenes `_starte`
# hineinreichen und den ueberwachten Starter damit gar nicht betreten.


class Strom:
    """Ein Ausgabestrom, der eine feste Bytefolge liefert und dann endet.

    Gebaut wie der in ``tests/test_fortschritt.py``: Seit dem 20.08.2026 laufen die
    Stroeme ueber ``PIPE`` und einen Faden, der sie laufend in eine Datei giesst.
    """

    def __init__(self, inhalt: bytes = b""):
        self._rest = bytearray(inhalt)

    def read(self, n: int = 1) -> bytes:
        if not self._rest:
            return b""
        heraus = bytes(self._rest[:n])
        del self._rest[:n]
        return heraus

    def close(self):
        pass


class Prozessattrappe:
    """Ein Popen-Doppelgaenger: ``laeuft_blicke`` Blicke lang am Leben, dann fertig.

    ``None`` heisst **wird nie fertig** — der haengende Lauf, um den es geht.
    """

    def __init__(self, laeuft_blicke=0, ausgabe: bytes = b"blender sagt etwas\n"):
        self.laeuft_blicke = laeuft_blicke
        self.ausgabe = ausgabe
        self.returncode = None
        self.getoetet = False

    def __call__(self, cmd, stdout=None, stderr=None):
        self.stdout = Strom(self.ausgabe)
        self.stderr = Strom(b"")
        return self

    def poll(self):
        if self.laeuft_blicke is None:
            return None
        if self.laeuft_blicke <= 0:
            self.returncode = 0
            return 0
        self.laeuft_blicke -= 1
        return None

    def kill(self):
        self.getoetet = True
        self.returncode = -9

    def wait(self):
        return self.returncode


def test_ohne_gesamtfrist_laeuft_der_ueberwachte_starter_wirklich_durch():
    """`timeout=None` muss den Starter erreichen, nicht nur die Signatur.

    Ohne die Abfrage `timeout is not None` in der Warteschleife vergleicht die zweite
    Runde `float` mit `None` und der Lauf stirbt mit einem `TypeError` — beim ERSTEN
    Blick, also lange vor jedem Rendern.
    """
    uhr = Uhr()
    prozess = Prozessattrappe(laeuft_blicke=3)
    starte = seams.starter_mit_wache(frist_s=100, takt_s=1,
                                     _schlaf=lambda s: uhr.weiter(s),
                                     _popen=prozess, _uhr=uhr)

    ergebnis = starte(["blender"], None)

    assert ergebnis.returncode == 0
    assert "blender sagt etwas" in ergebnis.stdout
    assert not prozess.getoetet, "ohne Gesamtfrist darf die Uhr niemanden beenden"


def test_ohne_gesamtfrist_greift_die_wache_trotzdem():
    """Was entfaellt, ist das Budget — nicht die Wache.

    Sonst waere `timeout=None` das ungepruefte Durchlassen, gegen das die Abweisung in
    `glb_zu_multipass` gebaut ist.
    """
    uhr = Uhr()
    prozess = Prozessattrappe(laeuft_blicke=None, ausgabe=b"")   # schreibt nie etwas
    starte = seams.starter_mit_wache(frist_s=100, takt_s=30,
                                     _schlaf=lambda s: uhr.weiter(s),
                                     _popen=prozess, _uhr=uhr)

    with pytest.raises(SeamError) as fehler:
        starte(["blender"], None)

    assert prozess.getoetet, "ein haengender Prozess muss auch wirklich beendet werden"
    meldung = str(fehler.value)
    assert "Gesamtfrist gibt es bei diesem Lauf nicht" in meldung, (
        "Die Meldung muss sagen, dass es hier keine Gesamtfrist gibt. Die alte Fassung "
        "rechnete stattdessen aus, wann der Gesamt-Timeout gegriffen haette — mit None "
        "ist das ein TypeError mitten in der Fehlermeldung.")
    assert "wäre erst in" not in meldung, (
        "Ohne Gesamtfrist darf die Meldung keine ausrechnen.")


def test_der_produktivweg_ohne_gesamtfrist_kommt_bis_zum_report(tmp_path, monkeypatch,
                                                                blender_attrappe):
    """Die Gegenprobe am ganzen Weg: kein eigenes `_starte`, also der echte Wachstarter.

    Genau diese Kombination — `timeout=None` und voreingestellter Herzschlag — ist die,
    die auf dem Laptop gefahren werden soll. Alle uebrigen Proben zu `timeout=None`
    reichen ein `_starte` hinein und betreten den Wachstarter darum nie.
    """
    aus = tmp_path / "aus"
    prozess = Prozessattrappe(laeuft_blicke=1)

    def oeffne(cmd, stdout=None, stderr=None):
        # Tut, was Blender taete: den Report hinterlassen.
        Path(cmd[cmd.index("--out") + 1], "blender-report.json").write_text(
            "{}", encoding="utf-8")
        return prozess(cmd, stdout, stderr)

    monkeypatch.setattr(seams.subprocess, "Popen", oeffne)
    monkeypatch.setattr(seams.time, "sleep", lambda s: None)     # ein Blick, kein Warten

    report = seams.glb_zu_multipass("bau.glb", aus, up_axis="Y", timeout=None)

    assert report["depth_png"] is None, "ohne EXR bleibt das PNG NICHT GEMESSEN"
    assert report["depth_png_fehler"], "und der Grund steht als Feld da"


# --------------------------------------------------------------------------------------
# 8 · Eine Frist, die keine Zahl ist — die zweite Abweisung ohne Probe
# --------------------------------------------------------------------------------------
#
# Auch am 18.09.2026 nachgetragen. `_gesamtfrist` weist seit heute nicht-positive,
# nicht-endliche und nicht-numerische Fristen ab. GEMESSEN: Nimmt man beide Abweisungen
# heraus, bleiben `tests/test_seams.py`, `tests/test_fortschritt.py` und
# `tests/test_durchreichung_verarbeiter.py` zusammen bei 204 von 204 gruen. Eine
# Verhaltensaenderung, die der HomeStation angesagt werden muss, darf nicht die einzige
# ihrer Art ohne fallende Probe sein.

@pytest.mark.parametrize("frist", [0, -5, float("inf"), float("nan"), "900", True])
def test_eine_frist_die_keine_ist_wird_abgewiesen(frist, tmp_path, blender_attrappe):
    """Null Sekunden sind keine Frist, und `True` ist keine Zahl.

    Wer keine Gesamtfrist will, sagt ``None`` — das ist etwas anderes als null. Und es
    wird KEIN Prozess gestartet: `verweigerer` belegt, dass vorher abgebrochen wurde.
    """
    with pytest.raises(SeamError) as fehler:
        seams.glb_zu_multipass("bau.glb", tmp_path / "aus", up_axis="Y",
                               timeout=frist, _starte=verweigerer)

    assert "timeout" in str(fehler.value)


@pytest.mark.parametrize("frist", [0, -5, float("nan"), "300"])
def test_auch_die_ifc_laeufe_nehmen_keine_frist_die_keine_ist(frist, ifc_python_attrappe,
                                                              tmp_path):
    """Dieselbe Pruefung hinter `_ifc_frist` — dort ist die Frist der einzige Riegel."""
    with pytest.raises(SeamError):
        ifc_zu_glb(ifc_datei, tmp_path / "b.glb", timeout=frist,
                   _starte=verweigerer)
