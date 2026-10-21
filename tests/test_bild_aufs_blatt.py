"""Bild aufs Blatt (Video-Befunde L4-16, L3-A4, L3-A5; 21.10.2026): in Visbox zählt «Exportieren».

Die Knotenansicht gibt das Bild eines Laufs in der grossen Ansicht im Original heraus («Exportieren», ein
gewöhnliches Herunterladen). Visbox hat kein Blatt und kein Projekt, das Bilder behält — der Wirt schaltet das
Sichern ins Projekt und «Aufs Blatt» in der grossen Ansicht darum ab (``setzeBlattDa(false)``), die Ausnahme steht
in ``kosmovis/UI_AUSNAHMEN.json``. Die Mac-App macht aus dem Herunterladen einen Sichern-Dialog: ohne
``WKDownloadDelegate`` täte eine ``WKWebView`` mit ``a[download]`` nichts, und «Exportieren» wäre ein Knopf ohne
Wirkung. Hier wird geprüft, dass diese Teile beieinander sind.
"""
from __future__ import annotations

import json
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
KOPIE = WURZEL / "kosmovis"
VIS = KOPIE / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"
WIRT = KOPIE / "apps" / "visbox-knoten" / "src" / "main.tsx"
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start" / "Arbeitsansicht.swift"
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Sichername.swift"


def test_die_kopie_traegt_ablage_und_export():
    zeile = (VIS / "BildAblageZeile.tsx").read_text(encoding="utf-8")
    assert "-exportieren" in zeile and "-aufs-blatt" in zeile
    assert "istBlattDa()" in zeile, "«Aufs Blatt» muss in Visbox wegfallen koennen"
    ablage = (VIS / "bild-ablage.ts").read_text(encoding="utf-8")
    assert "a.download = name" in ablage, "Exportieren ist ein gewoehnliches Herunterladen"
    verlauf = (VIS / "RenderVerlauf.tsx").read_text(encoding="utf-8")
    assert "<BildAblageZeile" in verlauf


def test_der_wirt_schaltet_blatt_und_sichern_ab():
    wirt = WIRT.read_text(encoding="utf-8")
    assert "setzeBlattDa(false)" in wirt


def test_die_ausnahme_ist_benannt():
    daten = json.loads((KOPIE / "UI_AUSNAHMEN.json").read_text(encoding="utf-8"))
    eintraege = [e for e in daten.get("werkzeug_ausnahmen", []) if e.get("testid") == "render-verlauf-gross-aufs-blatt"]
    assert len(eintraege) == 1
    assert eintraege[0]["grund"] and eintraege[0]["entscheid"]


def test_die_mac_app_zeigt_den_sichern_dialog():
    mac = MAC.read_text(encoding="utf-8")
    assert "WKDownloadDelegate" in mac
    assert "shouldPerformDownload ? .download : .allow" in mac
    assert "download.delegate = self" in mac
    assert "NSSavePanel()" in mac and "Sichername.vorschlag(suggestedFilename)" in mac
    kern = KERN.read_text(encoding="utf-8")
    assert "import Foundation" in kern and "AppKit" not in kern and "WebKit" not in kern
