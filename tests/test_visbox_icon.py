"""Das Visbox-Icon (Owner-Entscheid 88, 14.10.2026, Blatt 20 Vorschlag A «Box mit Bild»).

Bewacht wird, dass die erzeugten Dateien da sind und taugen — und dass Mac-App und iPad-App sie
wirklich einbinden. Ein Icon, das im Repo liegt, aber nicht im Bündel, sieht niemand.
"""
from __future__ import annotations

import importlib.util
import plistlib
import struct
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
ICNS = WURZEL / "ipad" / "VisboxMac" / "App" / "Visbox.icns"
SATZ = WURZEL / "ipad" / "Visbox.swiftpm" / "Assets.xcassets" / "AppIcon.appiconset"


def _werkzeug():
    spec = importlib.util.spec_from_file_location("make_icon_probe", WURZEL / "tools" / "make_icon.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _png_kante(daten: bytes) -> tuple[int, int, int]:
    assert daten[:8] == b"\x89PNG\r\n\x1a\n"
    breite, hoehe = struct.unpack(">II", daten[16:24])
    return breite, hoehe, daten[25]                             # Farbtyp: 2 RGB, 6 RGBA


def test_das_icns_traegt_alle_stufen_als_png():
    roh = ICNS.read_bytes()
    assert roh[:4] == b"icns" and struct.unpack(">I", roh[4:8])[0] == len(roh)
    gefunden, pos = {}, 8
    while pos < len(roh):
        art, laenge = roh[pos:pos + 4].decode("ascii"), struct.unpack(">I", roh[pos + 4:pos + 8])[0]
        gefunden[art] = _png_kante(roh[pos + 8:pos + laenge])[:2]
        pos += laenge
    assert pos == len(roh)
    erwartet = {art: (kante, kante) for art, kante in _werkzeug().ICNS_BLOECKE}
    assert gefunden == erwartet


def test_das_ipad_icon_ist_1024_und_ohne_durchsicht():
    breite, hoehe, farbtyp = _png_kante((SATZ / "AppIcon-1024.png").read_bytes())
    assert (breite, hoehe) == (1024, 1024) and farbtyp == 2       # RGB: Xcode verlangt das
    import json
    inhalt = json.loads((SATZ / "Contents.json").read_text(encoding="utf-8"))
    assert inhalt["images"][0]["filename"] == "AppIcon-1024.png"
    assert inhalt["images"][0]["size"] == "1024x1024"


def test_beide_apps_binden_das_icon_ein():
    plist = plistlib.loads((WURZEL / "ipad" / "VisboxMac" / "App" / "Info.plist").read_bytes())
    assert plist["CFBundleIconFile"] == ICNS.stem
    ablauf = (WURZEL / ".github" / "workflows" / "ipad.yml").read_text(encoding="utf-8")
    assert f'cp App/{ICNS.name} "$BUENDEL/Contents/Resources/{ICNS.name}"' in ablauf
    paket = (WURZEL / "ipad" / "Visbox.swiftpm" / "Package.swift").read_text(encoding="utf-8")
    assert 'appIcon: .asset("AppIcon")' in paket and ".placeholder(" not in paket


def test_die_vorlage_ist_die_gewaehlte_zeichnung():
    m = _werkzeug()
    svg = (WURZEL / "ipad" / "Marke" / "visbox-icon.svg").read_text(encoding="utf-8")
    assert svg == m.svg_randlos()
    assert (WURZEL / "ipad" / "Marke" / "visbox-icon-mac.svg").read_text(encoding="utf-8") == m.svg_mac()
    assert m.BILD in svg and "<text" not in svg                  # ohne Schrift


def _chromium_fehlt() -> bool:
    try:
        _werkzeug()._chromium()
    except SystemExit:
        return True
    return False


@pytest.mark.skipif(_chromium_fehlt(), reason="Chromium fehlt")
def test_das_werkzeug_erzeugt_dieselben_dateien_neu(tmp_path):
    """``--png`` in einen leeren Ordner: Es entstehen dieselben Dateien wie im Repo, mit denselben
    Stufen — das Icon ist aus der Vorlage wieder herstellbar."""
    assert _werkzeug().main(["--png"], wurzel=tmp_path) == 0
    neu = tmp_path / "ipad"
    for teil in ("Marke/visbox-icon.svg", "Marke/visbox-icon-mac.svg",
                 "Visbox.swiftpm/Assets.xcassets/AppIcon.appiconset/Contents.json"):
        assert (neu / teil).read_bytes() == (WURZEL / "ipad" / teil).read_bytes(), teil
    roh = (neu / "VisboxMac" / "App" / "Visbox.icns").read_bytes()
    assert roh[:4] == b"icns" and len(roh) > 50_000
    breite, hoehe, farbtyp = _png_kante(
        (neu / "Visbox.swiftpm/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png").read_bytes())
    assert (breite, hoehe, farbtyp) == (1024, 1024, 2)
