"""A0270 Satz 1: Der Varianten-Knoten nennt bei einer nachgezogenen Mappe den Weg zu Standpunkten.

Geräteprobe 0.3.75, Befund A0261: aus einer nachgezogenen Mappe (Standpunkte null,
``auskunft_nachgezogen`` wahr) las man «Keine Standpunkte — erst ein Modell laden …» und kam nicht
weiter. Gesperrt sind die Standpunkte mit gutem Grund (der Zwilling am Heim-PC trägt ein anderes
Modell); der Knoten muss aber den Rückweg nennen: «Andere Datei …» am Modell-Knoten.

Die TypeScript-Probe (``varianten-nachgezogen-a0270.test.tsx``) rendert den Knoten; diese Probe
liest die Quelltexte und läuft in jeder Umgebung (auch dort, wo kein Node installiert ist).
"""
from __future__ import annotations

import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
VIS = WURZEL / "kosmovis" / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"
SWIFT_KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Modelltausch.swift"


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8")


def test_der_knoten_hat_einen_satz_fuer_die_nachgezogene_mappe():
    quelle = _lies(VIS / "VariantenKnoten.tsx")
    m = re.search(r"VARIANTEN_NACHGEZOGEN_SATZ\s*=\s*\n?\s*'([^']+)'", quelle)
    assert m, "der Satz für die nachgezogene Mappe fehlt"
    satz = m.group(1)
    assert "«Andere Datei …»" in satz and "Modell-Knoten" in satz and "Standpunkte" in satz
    # Der Zweig «keine Standpunkte» wählt den Satz nach dem Zustand, nicht mehr fest.
    assert "nachgezogen ? VARIANTEN_NACHGEZOGEN_SATZ" in quelle
    assert "standpunkteNachgezogen()" in quelle
    assert "useSyncExternalStore(abonniereHeimStandpunkte" in quelle, "der Knoten muss mitwechseln"


def test_der_alte_satz_bleibt_fuer_alle_anderen_faelle():
    quelle = _lies(VIS / "VariantenKnoten.tsx")
    assert "Keine Standpunkte — erst ein Modell laden oder einen Blick sichern." in quelle


def test_der_wirt_setzt_das_zeichen_aus_der_mappenantwort_vor_den_hoerern():
    mappe = _lies(WIRT / "mappe.ts")
    assert "auskunft_nachgezogen?: boolean" in mappe
    zeichen = mappe.index("registriereStandpunkteNachgezogen(mappe.glb && mappe.auskunft_nachgezogen === true)")
    hoerer = mappe.index("registriereHeimStandpunkte(mappe.glb && mappe.standpunkte")
    assert zeichen < hoerer, "erst das Zeichen, dann die Hörer rufen"


def test_der_speicher_kennt_das_zeichen_und_meldet_nur_bei_aenderung():
    speicher = _lies(VIS / "heim-standpunkte.ts")
    assert "export function registriereStandpunkteNachgezogen(ja: boolean)" in speicher
    assert "export function standpunkteNachgezogen(): boolean" in speicher
    assert "if (nachgezogen === ja) return;" in speicher


def test_das_zeichen_kommt_vom_mac_so_wie_die_probe_es_liest():
    swift = _lies(SWIFT_KERN)
    assert 'felder["auskunft_nachgezogen"] = .wahrheit(true)' in swift


def test_die_aenderung_unter_kosmovis_ist_in_herkunft_begruendet():
    import json
    herkunft = json.loads(_lies(WURZEL / "kosmovis" / "HERKUNFT.json"))
    for pfad in ("apps/kosmo-orbit/src/modules/vis/VariantenKnoten.tsx",
                 "apps/kosmo-orbit/src/modules/vis/heim-standpunkte.ts"):
        assert "A0270" in herkunft["geaendert"].get(pfad, ""), pfad
