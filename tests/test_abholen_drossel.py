"""Eine fehlende Ablage steht nicht im Takt im Journal (A0203, B0052, 05.11.2026).

Der Abholer laeuft als Zeitgeber mit je einem Durchgang je Prozess. Fehlte ihm die eigene
Ablage, stand «fehlt — uebersprungen» rund 5400-mal am Tag im Journal, und die Zeilen, die
zaehlen, gingen darin unter. Weil jeder Durchgang ein frischer Prozess ist, kann die Drossel
nicht im Speicher liegen: Diese Probe laedt den Einstieg darum je Durchgang neu.
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ZEILE = "fehlt — uebersprungen"
UHR = 1_790_000_000.0


@pytest.fixture
def lauf(monkeypatch, capsys, tmp_path):
    """Ein Durchgang als frischer Aufruf; gibt Rueckgabewert und Zahl der Warnzeilen."""
    (tmp_path / "bruecke").mkdir()

    def fahren(*zusatz, uhr=None, erwartet=0):
        if uhr is not None:
            monkeypatch.setattr(time, "time", lambda: uhr)
        spez = importlib.util.spec_from_file_location(
            "abholen_pruefling", REPO / "tools" / "abholen.py")
        modul = importlib.util.module_from_spec(spez)
        spez.loader.exec_module(modul)
        monkeypatch.setattr(modul.abholer, "durchgang", lambda ablage, **kw: {
            "gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
            "gestanden": 0, "waisen": [], "ergebnisse": []})
        monkeypatch.setattr(modul.abholer, "verarbeiter", lambda **kw: (lambda a: {}))
        monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
        monkeypatch.setattr(modul.bruecke, "offene_auftraege", lambda p, **kw: [])
        monkeypatch.setattr(modul.eigene_quelle, "offene_auftraege", lambda p, **kw: [])
        monkeypatch.setattr(sys, "argv", [
            "abholen.py", "--store", str(tmp_path / "bruecke"),
            "--eigener-store", str(tmp_path / "eigen"), *zusatz])
        assert modul.main() == erwartet
        return capsys.readouterr().out.count(ZEILE)

    return fahren


def _zustand(ablage: Path) -> list[Path]:
    return [p for p in ablage.iterdir() if "drossel" in p.name]


def test_zwanzig_durchgaenge_ergeben_eine_zeile(lauf):
    assert sum(lauf() for _ in range(20)) == 1


def test_die_zeile_kommt_je_wechsel_genau_einmal_wieder(lauf, tmp_path):
    eigen = tmp_path / "eigen"
    assert [lauf(), lauf()] == [1, 0]

    eigen.mkdir()
    assert lauf() == 0

    eigen.rmdir()
    assert [lauf(), lauf()] == [1, 0]

    eigen.mkdir()
    lauf()
    eigen.rmdir()
    assert [lauf(), lauf()] == [1, 0]


def test_nach_einer_stunde_kommt_sie_wieder_einmal(lauf):
    assert lauf(uhr=UHR) == 1
    assert lauf(uhr=UHR + 3599) == 0
    assert lauf(uhr=UHR + 3600) == 1
    assert lauf(uhr=UHR + 3601) == 0
    assert lauf(uhr=UHR + 7199) == 0
    assert lauf(uhr=UHR + 7200) == 1


def test_eine_zurueckgestellte_uhr_verschweigt_nichts(lauf):
    assert lauf(uhr=UHR) == 1
    assert lauf(uhr=UHR - 10) == 1


def test_die_probe_zeigt_die_zeile_immer_und_verbraucht_nichts(lauf, tmp_path):
    """`--probe` ist die Frage des Menschen; ihm verschweigt die Drossel nichts."""
    assert [lauf("--probe"), lauf("--probe")] == [1, 1]
    assert _zustand(tmp_path / "bruecke") == []
    assert lauf() == 1


@pytest.mark.parametrize("kaputt", ["text", "liste", "fremde_werte", "ordner"])
def test_ein_kaputter_zustand_verschweigt_nichts(lauf, tmp_path, kaputt):
    """Weder eine unlesbare noch eine unschreibbare Datei wirft den Durchgang um."""
    assert lauf() == 1
    datei, = _zustand(tmp_path / "bruecke")
    datei.unlink()
    if kaputt == "ordner":
        datei.mkdir()
    else:
        datei.write_text({"text": "{halb", "liste": "[1]",
                          "fremde_werte": '{"gemeldet": {"eigene Ablage (MCP-Einlass)": "x"}}'
                          }[kaputt], encoding="utf-8")
    assert lauf() == 1


def test_der_zustand_nennt_keinen_pfad(lauf, tmp_path):
    """Regel 3: Er liegt neben dem Puls und traegt wie dieser nur Name und Zeitpunkt."""
    lauf()
    datei, = _zustand(tmp_path / "bruecke")
    assert str(tmp_path) not in datei.read_text(encoding="utf-8")


def test_ohne_fehlende_ablage_entsteht_keine_datei(lauf, tmp_path):
    """Wer nichts vermisst, bekommt nichts in die Bruecken-Ablage."""
    (tmp_path / "eigen").mkdir()
    assert lauf() == 0
    assert _zustand(tmp_path / "bruecke") == []
    assert _zustand(tmp_path / "eigen") == []


def test_fehlt_die_bruecke_wird_auch_sie_gedrosselt(lauf, tmp_path):
    """Der Zustand wandert in die vorhandene Ablage, und ein alter Stand dort veraltet nicht."""
    bruecke, eigen = tmp_path / "bruecke", tmp_path / "eigen"
    eigen.mkdir()
    bruecke.rmdir()
    assert [lauf(), lauf()] == [1, 0]

    bruecke.mkdir()
    assert lauf() == 0

    bruecke.rmdir()
    assert [lauf(), lauf()] == [1, 0]


def test_fehlen_alle_bleibt_es_ein_abbruch_ohne_datei(lauf, tmp_path):
    (tmp_path / "bruecke").rmdir()
    assert lauf(erwartet=2) == 0
    assert list(tmp_path.iterdir()) == []
