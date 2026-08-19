"""``tools/abholen.py`` — der Betriebs-Einstieg, geprüft an seiner Verdrahtung.

Warum diese Datei existiert
---------------------------
``tools/abholen.py`` ist am 19.08.2026 entstanden, weil :mod:`aiimaging.abholer` alles
konnte und **niemand es rief**. Ein Modul, das nie läuft, ist von einem fehlenden Modul
nicht zu unterscheiden.

Genau dieselbe Fehlerart kann sich im Einstieg wiederholen, eine Ebene tiefer: ein
Schalter, den ``argparse`` kennt und den niemand weiterreicht. ``--stillstand-frist-s``
stünde dann in der Hilfe, und die Wache liefe trotzdem mit der Vorgabe — oder gar nicht.
Diese Datei prüft darum nicht, was der Abholer tut (das steht in ``test_abholer.py``),
sondern **dass die Angaben des Betriebs bei ihm ankommen**.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _abholen():
    """``tools/`` ist kein Paket — wie in ``test_testgeometrie.py``."""
    pfad = REPO / "tools" / "abholen.py"
    spez = importlib.util.spec_from_file_location("abholen_pruefling", pfad)
    modul = importlib.util.module_from_spec(spez)
    spez.loader.exec_module(modul)
    return modul


def _lauf(monkeypatch, tmp_path, argv, ausgabe):
    """Den Einstieg fahren und festhalten, womit er ``durchgang`` gerufen hat."""
    modul = _abholen()
    gesehen: dict = {}

    def falscher_durchgang(store, **kw):
        gesehen.update(kw)
        gesehen["store"] = store
        return {"gesehen": 0, "verarbeitet": 0, "fehler": 0, "liegengelassen": 0,
                "gestanden": 0, "waisen": [], "ergebnisse": []}

    monkeypatch.setattr(modul.abholer, "durchgang", falscher_durchgang)
    monkeypatch.setattr(modul.abholer, "verarbeiter", lambda **kw: (lambda a: {}))
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path), *argv])

    assert modul.main() == 0
    return gesehen


def test_die_frist_des_betriebs_kommt_bei_der_wache_an(monkeypatch, tmp_path):
    """Der Schalter darf nicht bloss in der Hilfe stehen.

    Geprüft an der **gebauten Wache**, nicht am gemerkten Argument: Ein Wert, der
    entgegengenommen und dann verworfen wird, sähe an einem Argument-Test gleich aus.
    """
    ausgabe = tmp_path / "job" / "out"
    gesehen = _lauf(monkeypatch, tmp_path, ["--stillstand-frist-s", "42"], ausgabe)

    wache = gesehen["wache_bauen"]({"ausgabe": ausgabe, "job_id": "vis-1-abcdef"})
    assert wache.frist_s == 42.0


def test_ohne_wache_wird_keine_gebaut(monkeypatch, tmp_path):
    """`None` heisst im Abholer „nicht beobachtet" — und genau das soll ankommen."""
    gesehen = _lauf(monkeypatch, tmp_path, ["--ohne-wache"], tmp_path / "out")

    assert gesehen["wache_bauen"] is None


def test_die_wache_haengt_am_ausgabeordner_und_legt_ihn_an(monkeypatch, tmp_path):
    """Sonst fände der erste Blick nichts vor.

    Die Uhr liefe dann ab Beginn statt ab dem ersten Zeichen, und ein Auftrag, dessen
    erstes Bild spät kommt, sähe aus wie einer, der steht.
    """
    ausgabe = tmp_path / "job" / "out"
    gesehen = _lauf(monkeypatch, tmp_path, [], ausgabe)
    assert not ausgabe.exists()

    wache = gesehen["wache_bauen"]({"ausgabe": ausgabe, "job_id": "vis-1-abcdef"})

    assert ausgabe.is_dir()
    assert wache.blick()["befund"] is None       # der Ordner ist da, also gibt es ein Zeichen


def test_die_wache_ist_belegt_und_nicht_behauptet(monkeypatch, tmp_path):
    """Eine neue Datei taucht auf, weil etwas fertig wurde — nicht, weil jemand es sagt.

    Der Unterschied entscheidet über `warn` gegen `error`: Nur bei belegtem Zeichen heisst
    Stillstand wirklich Stillstand.
    """
    from aiimaging import fortschritt

    gesehen = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    wache = gesehen["wache_bauen"]({"ausgabe": tmp_path / "out", "job_id": "vis-1-abcdef"})

    assert wache.art == fortschritt.BELEGT


def test_die_voreingestellte_frist_ist_die_uebernommene_und_keine_eigene(monkeypatch, tmp_path):
    """Sie ist aus dem Altbestand und **nicht gemessen** — das steht so in der Hilfe.

    Der Test hält sie an die Modulkonstante gebunden, damit sie nicht still zu einer
    zweiten, abweichenden Zahl auseinanderläuft.
    """
    from aiimaging import fortschritt

    gesehen = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    wache = gesehen["wache_bauen"]({"ausgabe": tmp_path / "out", "job_id": "vis-1-abcdef"})

    assert wache.frist_s == fortschritt.FRIST_S


def test_der_betreiber_entscheid_zur_fremden_freigabe_bleibt_voreingestellt_aus(
        monkeypatch, tmp_path):
    """Die Regel, wegen der es diesen Einstieg überhaupt gibt — hier gegen ein Versehen."""
    ohne = _lauf(monkeypatch, tmp_path, [], tmp_path / "out")
    mit = _lauf(monkeypatch, tmp_path, ["--fremde-freigabe"], tmp_path / "out")

    assert ohne["fremde_freigabe_gilt"] is False
    assert mit["fremde_freigabe_gilt"] is True
