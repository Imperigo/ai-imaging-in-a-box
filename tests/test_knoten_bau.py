"""Der eingecheckte Bau der Knotenansicht passt zur Quelle (14.10.2026).

Bis dahin war der Bau vom Repo ausgeschlossen, und die HomeStation lieferte drei Wochen lang
den Bau vom 24.09. aus. Jetzt ist er eingecheckt — und diese Probe fällt, wenn jemand die
Kopie nachzieht und vergisst, `python3 tools/knoten_bau.py` laufen zu lassen.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _bau():
    spec = importlib.util.spec_from_file_location("knoten_bau_probe", WURZEL / "tools" / "knoten_bau.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_der_bau_ist_auf_dem_stand_der_quelle():
    m = _bau()
    stempel = json.loads(m.STEMPEL.read_text(encoding="utf-8"))
    assert stempel["quelle"] == m.fingerabdruck(), (
        "Die Quelle der Knotenansicht hat sich geaendert, der Bau nicht — "
        "`python3 tools/knoten_bau.py` laufen lassen und dist/ einchecken.")


def test_die_seite_findet_alle_ihre_teile():
    m = _bau()
    seite = (m.BAU / "index.html").read_text(encoding="utf-8")
    teile = re.findall(r'(?:src|href)="\./([^"]+)"', seite)
    assert teile, "index.html verweist auf nichts"
    for teil in teile:
        assert (m.BAU / teil).is_file(), teil


def test_der_bau_ist_eingecheckt_und_nicht_mehr_ausgeschlossen():
    regeln = (WURZEL / ".gitignore").read_text(encoding="utf-8")
    assert "!kosmovis/apps/visbox-knoten/dist/" in regeln


def test_nur_stempeln_baut_nicht_und_aendert_einen_frischen_stempel_nicht(monkeypatch):
    m = _bau()
    vorher = m.STEMPEL.read_bytes()
    monkeypatch.setattr(m.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("--stempel darf nicht bauen")))
    assert m.main(["--stempel"]) == 0
    assert m.STEMPEL.read_bytes() == vorher


def test_npm_ci_auch_wenn_das_lockfile_neuer_ist(tmp_path):
    """auf-20261015-286: Ein Nachzug brachte ein neues Paket, node_modules war alt, der Bau
    scheiterte. Jetzt: ci, wenn node_modules fehlt oder das Lockfile neuer ist."""
    import os
    import importlib.util
    spec = importlib.util.spec_from_file_location("kb", WURZEL / "tools" / "knoten_bau.py")
    kb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kb)
    assert kb.braucht_npm_ci(tmp_path) is True                       # kein node_modules
    (tmp_path / "node_modules").mkdir()
    stand = tmp_path / "node_modules" / ".package-lock.json"
    stand.write_text("{}", encoding="utf-8")
    lock = tmp_path / "package-lock.json"
    lock.write_text("{}", encoding="utf-8")
    os.utime(stand, (1000, 1000)); os.utime(lock, (2000, 2000))
    assert kb.braucht_npm_ci(tmp_path) is True                       # Lockfile neuer
    os.utime(lock, (500, 500))
    assert kb.braucht_npm_ci(tmp_path) is False                      # Einrichtung aktuell
