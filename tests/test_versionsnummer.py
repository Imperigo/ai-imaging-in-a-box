"""Eine Versionsnummer für Visbox — an allen vier Stellen dieselbe (Owner-Entscheid 66, 01.10.2026).

Bis dahin trug Visbox drei verschiedene: Bibliothek 0.0.1 (pyproject) und 0.0.2 (Modul), iPad-App
0.1, Mac-App 0.1.7 (die Nummer von KosmoOrbit). Seit dem 01.10.2026 zählt Visbox selbst, ab
**0.1.0** — die erste vorführbare Fassung. Welche KosmoOrbit-Fassung dazu passt, steht im
Lieferblatt, nicht in der Nummer.
"""
from __future__ import annotations

import plistlib
import re
import tomllib
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _stellen() -> dict[str, str]:
    import aiimaging
    pyproject = tomllib.loads((WURZEL / "pyproject.toml").read_text(encoding="utf-8"))
    ipad = (WURZEL / "ipad" / "Visbox.swiftpm" / "Package.swift").read_text(encoding="utf-8")
    with (WURZEL / "ipad" / "VisboxMac" / "App" / "Info.plist").open("rb") as f:
        mac = plistlib.load(f)
    return {
        "pyproject.toml": pyproject["project"]["version"],
        "aiimaging.__version__": aiimaging.__version__,
        "iPad displayVersion": re.search(r'displayVersion:\s*"([^"]+)"', ipad).group(1),
        "Mac CFBundleShortVersionString": mac["CFBundleShortVersionString"],
    }


def test_visbox_traegt_ueberall_dieselbe_nummer():
    stellen = _stellen()
    assert len(set(stellen.values())) == 1, stellen


def test_die_nummer_hat_drei_teile():
    """«0.1» und «0.1.0» sind für einen Menschen dasselbe, für einen Vergleich nicht."""
    nummer = next(iter(_stellen().values()))
    assert re.fullmatch(r"\d+\.\d+\.\d+", nummer), nummer
