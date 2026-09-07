"""Der serielle Fahrer der Beweisskripte — und warum er seriell ist.

Der Anlass ist gemessen und nicht vorsichtig
---------------------------------------------
Am 26.08.2026 wurden an einem Tag **drei** Läufe rot — zweimal ``test_bauwerksbox``,
einmal ``test_kette`` —, und alle drei hatten dieselbe Ursache: nebenher lief ein zweiter
Blender. Allein gefahren war dieselbe Sammlung **fünf von fünf** grün. Der Herzschlagfaden
verhungert unter Last länger als seine Frist, und die Wache tötet dann einen gesunden
Lauf.

Die zwanzig Beweisskripte entstehen parallel; **gefahren werden sie einzeln.** Das ist
die Regel, die dieses Werkzeug ausführbar macht.

Was hier geprüft wird
---------------------
Die **Buchführung**, nicht die Bilder. Ob ein Beweis trägt, entscheidet, wer ihn ansieht.
Was eine Probe entscheiden kann: dass die Reihenfolge stimmt, dass ein Fehlschlag die
Reihe nicht anhält, und — der wichtigste Fall — dass ein Skript mit Rückgabe 0 **und
keinem Bild** nicht als Erfolg durchgeht.

*Ein Skript, das gelingt und nichts schreibt, ist kein Beweis* — dieselbe Fehlerart wie
der liegengebliebene Blender-Report aus Sitzung 03 und die Dateigrösse als vermeintlicher
Beleg aus Sitzung 05. Beide Male sah es nach Erfolg aus.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]


def _lade():
    pfad = WURZEL / "tools" / "beweise_fahren.py"
    spec = importlib.util.spec_from_file_location("beweise_fahren", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["beweise_fahren"] = modul
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def fahrer():
    return _lade()


@pytest.fixture
def ablage(fahrer, tmp_path, monkeypatch):
    """Ein eigener Beweisordner — die echten Skripte fahren hier nicht mit."""
    beweise = tmp_path / "tools" / "beweis"
    beweise.mkdir(parents=True)
    monkeypatch.setattr(fahrer, "WURZEL", tmp_path)
    monkeypatch.setattr(fahrer, "BEWEISE", beweise)
    monkeypatch.setattr(fahrer, "AUSGABE", tmp_path / "build" / "beweis")
    return beweise


def _skript(ablage: Path, name: str, rumpf: str) -> Path:
    p = ablage / name
    p.write_text(rumpf, encoding="utf-8")
    return p


# ------------------------------------------------------------- die Reihenfolge

def test_die_reihenfolge_ist_die_nummer_und_nicht_die_platte(fahrer, ablage):
    """Die Nummer steht im Dateinamen und ist die Ordnung.

    Eine Reihenfolge, die vom Änderungsdatum abhängt, ist beim nächsten Klon eine
    andere — und ein Beweisgang, der sich je Klon anders ordnet, ist nicht nachbaubar.
    """
    for name in ("20_letzter.py", "02_zweiter.py", "01_erster.py"):
        _skript(ablage, name, "pass\n")
    assert [p.name for p in fahrer.skripte()] == [
        "01_erster.py", "02_zweiter.py", "20_letzter.py"]


def test_nur_waehlt_nach_nummer(fahrer, ablage):
    """``--nur 02 09`` — für den Fall, dass ein einzelner Beweis nachgezogen wird."""
    for name in ("01_a.py", "02_b.py", "09_c.py", "14_d.py"):
        _skript(ablage, name, "pass\n")
    assert [p.name for p in fahrer.skripte(["02", "09"])] == ["02_b.py", "09_c.py"]


def test_unterstrich_dateien_sind_kein_beweis(fahrer, ablage):
    """``__init__.py`` und Helfer mit führendem Unterstrich werden nicht gefahren."""
    _skript(ablage, "01_echt.py", "pass\n")
    _skript(ablage, "_helfer.py", "pass\n")
    assert [p.name for p in fahrer.skripte()] == ["01_echt.py"]


# ------------------------------------------------------------ die Buchführung

def test_gemessen_wird_was_auf_der_platte_liegt(fahrer, ablage, tmp_path):
    """Nicht, was das Skript behauptet.

    Ein Skript, das «geschrieben» meldet und nichts schreibt, ist in diesem Projekt
    zweimal vorgekommen — der liegengebliebene Report und die Dateigrösse als Beleg.
    """
    _skript(ablage, "01_schreibt.py", (
        "import pathlib, sys\n"
        f"z = pathlib.Path({str(tmp_path / 'build' / 'beweis' / '01_schreibt')!r})\n"
        "z.mkdir(parents=True, exist_ok=True)\n"
        "(z / 'a.png').write_bytes(b'x')\n"
        "(z / 'b.png').write_bytes(b'x')\n"
        "print('zwei Bilder geschrieben')\n"))
    bericht = fahrer.fahre(ablage / "01_schreibt.py")
    assert bericht["code"] == 0
    assert bericht["bilder"] == ["a.png", "b.png"]


def test_ein_bild_aus_einem_frueheren_lauf_ueberlebt_nicht(fahrer, ablage, tmp_path):
    """**Die dritte Fehlerart, und sie ist die stillste.**

    Ein Skript wird geändert und schreibt nur noch ein Bild statt zwei. Ohne Räumung
    liegt das zweite weiter da, der Fahrer zählt zwei, und **eines davon beweist eine
    Fassung, die es nicht mehr gibt.** Dieselbe Gestalt wie der liegengebliebene
    Blender-Report aus Sitzung 03: Es sah nach Erfolg aus.
    """
    ziel = tmp_path / "build" / "beweis" / "01_schreibt"
    ziel.mkdir(parents=True)
    (ziel / "alt.png").write_bytes(b"x")          # aus einem frueheren Lauf
    _skript(ablage, "01_schreibt.py", (
        "import pathlib\n"
        f"z = pathlib.Path({str(ziel)!r})\n"
        "z.mkdir(parents=True, exist_ok=True)\n"
        "(z / 'neu.png').write_bytes(b'x')\n"))
    bericht = fahrer.fahre(ablage / "01_schreibt.py")
    assert bericht["bilder"] == ["neu.png"], "das alte Bild hat den Lauf ueberlebt"
    assert bericht["geraeumt"] == ["alt.png"]
    assert bericht["verschwunden"] == ["alt.png"], (
        "der Fahrer muss sagen, dass eine fruehere Datei nicht mehr entsteht")


def test_geraeumt_wird_nur_der_eigene_ordner(fahrer, ablage, tmp_path):
    """Ein Beweis raeumt nie die Ergebnisse eines anderen weg.

    Sonst haette `--nur 09` den Nebeneffekt, die uebrigen neunzehn Beweisreihen zu
    loeschen — und das faellt erst auf, wenn man sie ausliefern will.
    """
    fremd = tmp_path / "build" / "beweis" / "02_anderer"
    fremd.mkdir(parents=True)
    (fremd / "fremd.png").write_bytes(b"x")
    _skript(ablage, "01_meiner.py", (
        "import pathlib\n"
        f"z = pathlib.Path({str(tmp_path / 'build' / 'beweis' / '01_meiner')!r})\n"
        "z.mkdir(parents=True, exist_ok=True)\n"
        "(z / 'a.png').write_bytes(b'x')\n"))
    fahrer.fahre(ablage / "01_meiner.py")
    assert (fremd / "fremd.png").exists(), "ein fremder Beweisordner wurde geraeumt"


def test_ein_skript_das_gelingt_und_nichts_schreibt_faellt_auf(fahrer, ablage, capsys):
    """**Der gefährlichere der beiden Fehlschläge.**

    Rückgabe 0 und nichts auf der Platte sieht in jeder Zusammenfassung wie ein Erfolg
    aus. Der Fahrer meldet es getrennt und gibt einen Fehlercode zurück.
    """
    _skript(ablage, "01_leer.py", "print('fertig')\n")
    code = fahrer.main([])
    aus = capsys.readouterr().out
    assert "OHNE BILD" in aus
    assert "kein Beweis" in aus
    assert code == 1, "ein Beweis ohne Bild darf den Gang nicht als gelungen melden"


def test_ein_fehlschlag_haelt_die_reihe_nicht_an(fahrer, ablage, tmp_path, capsys):
    """Sonst entschiede das erste kaputte Skript, wie viele Beweise es gibt."""
    _skript(ablage, "01_kaputt.py", "raise SystemExit(3)\n")
    _skript(ablage, "02_gut.py", (
        "import pathlib\n"
        f"z = pathlib.Path({str(tmp_path / 'build' / 'beweis' / '02_gut')!r})\n"
        "z.mkdir(parents=True, exist_ok=True)\n"
        "(z / 'a.png').write_bytes(b'x')\n"))
    code = fahrer.main([])
    aus = capsys.readouterr().out
    assert "GESCHEITERT: 01_kaputt" in aus
    assert "1 Bilder" in aus or "BILDER:   1" in aus, (
        "der zweite Beweis muss trotzdem gefahren worden sein")
    assert code == 1


def test_die_frist_bricht_ab_und_meldet_es(fahrer, ablage):
    """``--frist-s``. Ein hängender Beweis darf den Gang nicht auf Dauer blockieren.

    Gemeldet wird der Abbruch als solcher — nicht als Fehler des Skripts, denn *nicht
    fertig geworden* ist etwas anderes als *fehlgeschlagen*.
    """
    _skript(ablage, "01_haengt.py", "import time\ntime.sleep(30)\n")
    bericht = fahrer.fahre(ablage / "01_haengt.py", frist_s=1)
    assert bericht["code"] == -1
    assert "Frist" in bericht["fehler"]


def test_das_skript_findet_aiimaging_auch_ohne_eigenen_pfadeintrag(fahrer, ablage,
                                                                   tmp_path):
    """``PYTHONPATH`` wird gesetzt, damit ein vergessener ``sys.path``-Eintrag nicht
    wie ein fehlendes Modul aussieht.

    Der Fehler wäre sonst eine Falschmeldung: «aiimaging nicht gefunden» in einem Repo,
    in dem es liegt.
    """
    _skript(ablage, "01_pfad.py", (
        "import os, pathlib\n"
        f"z = pathlib.Path({str(tmp_path / 'build' / 'beweis' / '01_pfad')!r})\n"
        "z.mkdir(parents=True, exist_ok=True)\n"
        "(z / 'pfad.png').write_bytes(b'x')\n"
        "assert 'src' in os.environ.get('PYTHONPATH', ''), os.environ.get('PYTHONPATH')\n"))
    bericht = fahrer.fahre(ablage / "01_pfad.py")
    assert bericht["code"] == 0, bericht["fehler"]


def test_liste_faehrt_nichts(fahrer, ablage, capsys):
    """``--liste`` sagt, was gefahren würde — und fährt es nicht.

    Bei zwanzig Beweisen mit Blender-Läufen ist der Unterschied eine halbe Stunde.
    """
    _skript(ablage, "01_darf_nicht_laufen.py", "raise SystemExit(9)\n")
    assert fahrer.main(["--liste"]) == 0
    assert "01_darf_nicht_laufen.py" in capsys.readouterr().out


def test_die_schalter_kommen_ueber_die_kommandozeile_an(fahrer, ablage, tmp_path,
                                                        capsys):
    """``--nur`` und ``--frist-s`` werden hier wirklich **gedrückt**.

    Die Proben oben rufen ``skripte()`` und ``fahre()`` direkt — das prüft die Rechnung
    und nicht die Naht. *Ein Wächter, der den Aufruf selbst nachbaut, bewacht seine
    eigene Nachbildung*, und dass ``argparse`` ``--frist-s`` in ``a.frist_s`` legt, ist
    keine Auskunft darüber, ob der Wert ankommt.
    """
    _skript(ablage, "01_uebergangen.py", "raise SystemExit(9)\n")
    _skript(ablage, "02_haengt.py", "import time\ntime.sleep(30)\n")

    assert fahrer.main(["--nur", "02", "--frist-s", "1"]) == 1
    aus = capsys.readouterr().out
    assert "01_uebergangen" not in aus, "--nur hat nicht gewählt"
    assert "02_haengt" in aus and "FEHL" in aus, "--frist-s hat nicht abgebrochen"


def test_ohne_beweise_ist_das_ein_befund_und_kein_erfolg(fahrer, ablage, capsys):
    """Ein leerer Ordner darf nicht als «alles gelaufen» durchgehen."""
    assert fahrer.main([]) == 1
    assert "Keine Beweisskripte" in capsys.readouterr().out
