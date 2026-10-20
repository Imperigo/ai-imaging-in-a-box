"""Visbox-Ansichten = KosmoVis — die Kopfteile, geprüft (Entscheide 115/116, 20.10.2026).

Owner, stehend (Entscheid 115): *«ansichten ui und ux sollte zu kosmovis identisch sein immer».*
Die Knotenfläche war schon gleich; was fehlte, waren die Kopfteile, die KosmoOrbit am Programm-Wirt
über der Vis-Station zeigt (`App.tsx` unter `bodenDockAusgeblendet`, `main.tsx`). Plan:
``docs/PLAN_UI_GLEICHHEIT_2026-10-20.md`` §4.

Diese Proben halten drei Dinge zusammen:

1. **Jeder Kopfteil von KosmoOrbit ist benannt** — in ``kosmovis/UI_AUSNAHMEN.json`` genau einmal:
   eingesetzt, Ausnahme (Grund und Entscheid) oder offen (mit Stufe).
2. **Was eingesetzt heisst, ist wahr:** Die Datei kommt wortgleich herüber (``HERKUNFT.json``,
   nicht unter ``geaendert``), der Wirt zeichnet die Komponente aus genau dieser Datei, und die
   Kennung (``data-testid``) steht dort.
3. **Die Mac-App zeigt in der Knotenansicht keine eigenen Kopfteile mehr** — keine Kopfleiste,
   keine KI-Leiste — und die zweite Brücke trägt kein Kennwort.

Liegt KosmoOrbit daneben (Umgebungsvariable ``KOSMO_ORBIT`` = Pfad zu ``kosmo-orbit/``), prüft die
letzte Probe zusätzlich, dass ``App.tsx`` und ``main.tsx`` dort keinen Kopfteil zeigen, der hier
fehlt. Ohne den Pfad wird sie übersprungen; die Liste unten ist dann der Stand der Kopie.

Die Proben brauchen weder Node noch ``npm install`` — sie lesen nur Dateien.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
KOPIE = WURZEL / "kosmovis"
WIRT = KOPIE / "apps" / "visbox-knoten" / "src"
MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac"

#: Was KosmoOrbit über der Vis-Station zeigt, je mit einem Merkmal aus `App.tsx`/`main.tsx`
#: (Stand der Kopie). Jedes Merkmal muss im Feld «ko» eines Eintrags von UI_AUSNAHMEN.json stehen.
KOPF_IN_KO = (
    "app-schmal-hinweis",
    "WerkzeugPalette",
    "isl-einstellungen-kreis",
    "SpeichernKreis",
    "InselZweitgruppe",
    "sync-toggle",
    "starter-guide-start",
    "AnsichtsInfo",
    "InselOnboarding",
    "StarterGuide",
    "StartSequenz",
    "app-sync-leiste",
    "CursorEbene",
    "ClaudeAnschluss",
    "ClaudeFensterRahmen",
    "ErzaehlZeile",
    "KosmoMausEbene",
    "KosmoEckOrb",
    "KosmoPanel",
    "Einstellungen",
    "CommandPalette",
    "dataset.theme",
)

STAENDE = {"eingesetzt", "ausnahme", "offen"}


def _ausnahmen() -> dict:
    return json.loads((KOPIE / "UI_AUSNAHMEN.json").read_text(encoding="utf-8"))


def _herkunft() -> dict:
    return json.loads((KOPIE / "HERKUNFT.json").read_text(encoding="utf-8"))


def _wirt_text() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(WIRT.glob("*.ts*")))


def test_jeder_eintrag_hat_stand_und_begruendung():
    teile = _ausnahmen()["kopfteile"]
    namen = [t["teil"] for t in teile]
    assert len(namen) == len(set(namen)), "ein Teil steht doppelt"
    for t in teile:
        assert t["stand"] in STAENDE, t
        assert t["ko"].strip(), t
        if t["stand"] == "ausnahme":
            assert t.get("grund") and t.get("entscheid"), f"Ausnahme ohne Grund oder Entscheid: {t['teil']}"
        if t["stand"] == "offen":
            assert re.fullmatch(r"S[1-9]", t.get("stufe", "")) and t.get("grund"), t["teil"]
        if t["stand"] == "eingesetzt":
            assert t.get("datei") and t.get("testid"), t["teil"]


def test_jeder_kopfteil_von_kosmoorbit_ist_eingesetzt_oder_benannt():
    ko = " ".join(t["ko"] for t in _ausnahmen()["kopfteile"])
    fehlend = [m for m in KOPF_IN_KO if m not in ko]
    assert not fehlend, f"in UI_AUSNAHMEN.json nicht benannt: {fehlend}"


def test_eingesetzt_heisst_wortgleich_und_vom_wirt_gezeichnet():
    h = _herkunft()
    wirt = _wirt_text()
    for t in _ausnahmen()["kopfteile"]:
        if t["stand"] != "eingesetzt":
            continue
        datei = t["datei"]
        assert datei in h["woertlich"], f"{t['teil']}: {datei} kommt nicht wortgleich herüber"
        assert datei not in h.get("geaendert", {}), f"{t['teil']}: {datei} ist geändert, nicht wortgleich"
        quelle = (KOPIE / datei).read_text(encoding="utf-8")
        if komp := t.get("komponente"):
            modul = datei.removeprefix("apps/kosmo-orbit/src/").rsplit(".", 1)[0]
            assert re.search(rf"import \{{[^}}]*\b{komp}\b[^}}]*\}} from '[./]+kosmo-orbit/src/{re.escape(modul)}'", wirt), \
                f"{t['teil']}: der Wirt holt {komp} nicht aus {datei}"
            assert re.search(rf"<{komp}\b", wirt), f"{t['teil']}: der Wirt zeichnet <{komp}> nicht"
        tid = t["testid"]
        if tid.startswith("html["):
            continue
        assert f'"{tid}"' in wirt or f'"{tid}"' in quelle or f"'{tid}'" in wirt, \
            f"{t['teil']}: Kennung {tid} steht weder im Wirt noch in {datei}"


def test_ausnahmen_stehen_nicht_im_wirt():
    """Was Ausnahme ist, zeichnet der Wirt nicht — sonst wäre die Ausnahme eine Behauptung."""
    wirt = _wirt_text()
    for komp in ("AnsichtsInfo", "InselOnboarding", "StarterGuide", "StartSequenz", "KosmoMausEbene", "CursorEbene"):
        assert not re.search(rf"<{komp}\b", wirt), komp
    kopf = (WIRT / "kopf.tsx").read_text(encoding="utf-8")
    # Ohne Rundgang kein «?», ohne .kosmo-Datei keine Handgriffe am Speichern-Kreis.
    assert "onRundgang" not in kopf
    assert not re.search(r"<SpeichernKreis[^>]*on(Sichern|Weitergeben|Oeffnen)", kopf)


def test_der_wirt_setzt_das_thema_vor_dem_ersten_bild_und_die_kopfteile_in_die_wurzel():
    main = (WIRT / "main.tsx").read_text(encoding="utf-8")
    assert main.index("legeThema();") < main.index("createRoot(")
    assert re.search(r'<div className="app-wurzel" data-station="vis">\s*<VisboxKopf />', main)
    assert "<VisboxClaude />" in main
    thema = (WIRT / "thema.ts").read_text(encoding="utf-8")
    assert "THEMA_VORGABE: ThemeName = 'orbit'" in thema
    assert "'kosmo.thema'" in thema


def test_die_zweite_bruecke_liest_kein_kennwort():
    bruecke = (WIRT / "wirt-bruecke.ts").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", bruecke, flags=re.S)
    assert not re.search(r"kennwort|passwort|password|token|anmeldung", code, re.I), \
        "die Seite liest ein Kennwort-Feld"
    swift = (MAC / "Start" / "Knotenki.swift").read_text(encoding="utf-8")
    wirtteil = swift[swift.index("final class Knotenwirtbote"):]
    assert "anmeldung" not in wirtteil.lower() and "kennwort" not in wirtteil.lower()


def test_die_knotenansicht_der_mac_app_hat_keine_eigenen_kopfteile():
    ansicht = (MAC / "Start" / "Arbeitsansicht.swift").read_text(encoding="utf-8")
    # Die Kopfleiste steht nur noch auf der Visbox-Seite.
    assert re.search(r"if wahl == \.seite \{\s*Seitenkopf\(", ansicht), "die Mac-Kopfleiste steht noch über den Knoten"
    # Die KI-Leiste fällt in der Knotenansicht weg (Kizentrale bleibt Zustand und MCP-Sperre).
    assert "mitKi: wahl != .knoten" in ansicht
    leiste = (MAC / "Assistent" / "Assistentenleiste.swift").read_text(encoding="utf-8")
    assert re.search(r"if mitKi \{\s*Kileiste\(", leiste)
    assert re.search(r"if mitKi \{\s*Kileiste\(", ansicht)
    # Die zweite Brücke hängt neben der ersten, mit derselben Wache.
    ki = (MAC / "Start" / "Knotenki.swift").read_text(encoding="utf-8")
    assert "Knotenwirtbote.haengeAn(einstellung" in ansicht
    wirt = ki[ki.index("final class Knotenwirtbote"):]
    assert "isMainFrame" in wirt and "Knotenwege.istEigen" in wirt


@pytest.mark.skipif(not os.environ.get("KOSMO_ORBIT"), reason="KosmoOrbit liegt nicht daneben (KOSMO_ORBIT)")
def test_kosmoorbit_zeigt_keinen_kopfteil_der_hier_fehlt():
    app = Path(os.environ["KOSMO_ORBIT"]) / "apps" / "kosmo-orbit" / "src"
    quelle = (app / "App.tsx").read_text(encoding="utf-8")
    teile: set[str] = set()
    kennungen: set[str] = set()
    # Jeder Block unter dem Guard der Insel-Stationen, bis zu seiner schliessenden Klammer.
    for m in re.finditer(r"\{bodenDockAusgeblendet && ", quelle):
        ende = quelle.find("\n      )}", m.end())
        zeile = quelle.find("\n", m.end())
        block = quelle[m.end():ende if quelle[m.end()] == "(" and ende > 0 else zeile]
        teile |= set(re.findall(r"<([A-Z]\w+)", block))
        kennungen |= set(re.findall(r'data-testid="([\w-]+)"', block))
    main = (app / "main.tsx").read_text(encoding="utf-8")
    zweig = main[main.index("<App />"):main.index("</>", main.index("<App />"))]
    teile |= set(re.findall(r"<([A-Z]\w+)", zweig)) - {"App"}
    # Bausteine im Guard, die nur Zeichen oder Logo sind (keine eigenen Kopfteile).
    teile -= {"OrbitMark", "KIcon"}
    eintraege = _ausnahmen()["kopfteile"]
    benannt = " ".join(t["ko"] + " " + t.get("testid", "") for t in eintraege)
    fehlend = sorted(t for t in teile | kennungen if t not in benannt)
    assert {"WerkzeugPalette", "SpeichernKreis", "InselZweitgruppe", "ClaudeAnschluss"} <= teile, teile
    assert not fehlend, f"KosmoOrbit zeigt neu: {fehlend} — eintragen (eingesetzt, Ausnahme oder offen)"
