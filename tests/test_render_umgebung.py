"""Die Probe sagt, ob dieser Python rechnen kann — bevor ein Auftrag daran scheitert.

Befund der HomeStation (`auftraege/ergebnisse/auf-20260924-164.json`, B4): Der Abholer lief
von Hand mit dem System-Python. ``--probe`` meldete den Auftrag «frei», der Lauf scheiterte
erst beim Rendern mit «torch/diffusers nicht verfügbar». ``render.umgebung_da`` fragt das
vorher, ohne ``torch`` zu laden.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from aiimaging import render

REPO = Path(__file__).resolve().parents[1]


def _abholen():
    spec = importlib.util.spec_from_file_location("abholen_umgebung", REPO / "tools" / "abholen.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_fehlt_ein_paket_sagt_es_die_umgebung_mit_namen():
    antwort = render.umgebung_da(finde=lambda name: None if name == "torch" else object())
    assert antwort["da"] is False
    assert antwort["fehlend"] == ("torch",)
    assert antwort["satz"].startswith("FEHLT — torch")


def test_sind_beide_da_ist_die_umgebung_da():
    antwort = render.umgebung_da(finde=lambda name: object())
    assert antwort == {"da": True, "fehlend": (), "satz": "da (torch, diffusers)"}


def test_ein_kaputter_fund_zaehlt_als_fehlend():
    def wirft(name):
        raise ValueError("kaputter Eintrag")
    assert render.umgebung_da(finde=wirft)["fehlend"] == render.RENDER_PAKETE


def test_die_frage_laedt_torch_nicht():
    """Die Probe soll billig sein: ``torch`` bleibt ungeladen, wenn es nicht schon war."""
    vorher = "torch" in sys.modules
    render.umgebung_da()
    assert ("torch" in sys.modules) == vorher


def test_die_probe_nennt_die_render_umgebung(monkeypatch, tmp_path, capsys):
    modul = _abholen()
    monkeypatch.setattr(modul, "karte_auskunft", lambda: (True, "Attrappe"))
    monkeypatch.setattr(render, "umgebung_da", lambda: {"da": False, "fehlend": ("torch",),
                                                         "satz": "FEHLT — torch …"})
    monkeypatch.setattr(sys, "argv", ["abholen.py", "--store", str(tmp_path), "--probe"])
    assert modul.main() == 0
    assert "Render-Umgebung: FEHLT — torch" in capsys.readouterr().out
