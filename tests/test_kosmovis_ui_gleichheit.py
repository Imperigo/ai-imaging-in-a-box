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
   keine KI-Leiste, seit S3 keine Assistent-Leiste — und die zweite Brücke trägt kein Kennwort.
4. **Seit S3/S4** (Kugel und Gesprächsfeld, Einstellungs-Insel): jeder Abschnitt der Einstellungen
   von KosmoOrbit und jeder Schalter von «Bewegung & Klang» ist eingesetzt, ersetzt oder Ausnahme
   mit Grund; der Name «Assistent» und die Liste dessen, was die Seite behält, stehen in Seite und
   Kern gleich; die Lizenzzeilen der Insel stehen im ``NOTICE``.

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
        # EIN STELLVERTRETER MIT DER ANATOMIE VON DORT (S3, Gesprächsfeld): wortgleich ist dann das
        # CSS (`datei`), die Komponente kommt aus dem Stellvertreter, und der steht in HERKUNFT.json.
        if sv := t.get("stellvertreter"):
            assert sv in h["stellvertreter"], f"{t['teil']}: {sv} ist kein verbuchter Stellvertreter"
            quelle += (KOPIE / sv).read_text(encoding="utf-8")
        if komp := t.get("komponente"):
            modul = (t.get("stellvertreter") or datei).removeprefix("apps/kosmo-orbit/src/").rsplit(".", 1)[0]
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
    for komp in ("AnsichtsInfo", "InselOnboarding", "StarterGuide", "StartSequenz", "CursorEbene",
                 "CommandPalette"):
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


# ============================================================== S3/S4 (20.10.2026)

def test_s3_s4_sind_nicht_mehr_offen():
    offen = {t["teil"]: t["stufe"] for t in _ausnahmen()["kopfteile"] if t["stand"] == "offen"}
    assert "S3" not in offen.values() and "S4" not in offen.values(), offen


def test_nach_s5_ist_kein_kopfteil_mehr_offen():
    offen = [t["teil"] for t in _ausnahmen()["kopfteile"] if t["stand"] == "offen"]
    assert not offen, offen


def _meldet_vis_befehle_an(vis: Path) -> list[str]:
    return sorted(str(p.relative_to(vis)) for p in vis.rglob("*.ts*")
                  if re.search(r"\bregisterActions\s*\(", p.read_text(encoding="utf-8")))


def test_befehlspalette_ist_ausnahme_weil_das_vis_werkzeug_keine_befehle_anmeldet():
    """S5, ⌘K: Die Ausnahme steht nur, solange ihr Grund wahr ist — das Vis-Werkzeug meldet bei der
    Befehlspalette nichts an. Tut es das in einem Nachzug, wird diese Probe rot, und die Palette
    kommt wortgleich herüber."""
    eintrag = next(t for t in _ausnahmen()["kopfteile"] if t["teil"] == "Befehlspalette (⌘K)")
    assert eintrag["stand"] == "ausnahme"
    vis = KOPIE / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"
    assert vis.is_dir()
    assert _meldet_vis_befehle_an(vis) == []
    assert "CommandPalette" not in _wirt_text()


@pytest.mark.skipif(not os.environ.get("KOSMO_ORBIT"), reason="KosmoOrbit liegt nicht daneben (KOSMO_ORBIT)")
def test_kosmoorbit_vis_werkzeug_meldet_keine_befehle_an():
    vis = Path(os.environ["KOSMO_ORBIT"]) / "apps" / "kosmo-orbit" / "src" / "modules" / "vis"
    assert _meldet_vis_befehle_an(vis) == [], "Das Vis-Werkzeug meldet drueben Befehle an — ⌘K uebernehmen"


def test_jeder_abschnitt_der_einstellungen_ist_benannt():
    h = _ausnahmen()
    for liste in ("einstellungen_abschnitte", "bewegung_klang_schalter"):
        kennungen = [a["testid"] for a in h[liste]]
        assert len(kennungen) == len(set(kennungen)), liste
        for a in h[liste]:
            assert a["stand"] in {"eingesetzt", "ersetzt", "ausnahme"}, a
            if a["stand"] != "eingesetzt":
                assert a.get("grund") and a.get("entscheid"), a
            if a["stand"] == "eingesetzt":
                assert a["datei"] in _herkunft()["woertlich"], a
    for a in h["gespraechsfeld_ausnahmen"]:
        assert a.get("grund"), a
    # Was eingesetzt oder ersetzt ist, steht in der Insel — was Ausnahme ist, nicht.
    insel = (WIRT / "einstellungen.tsx").read_text(encoding="utf-8")
    teile = (KOPIE / "apps/kosmo-orbit/src/shell/einstellungen-teile.tsx").read_text(encoding="utf-8")
    for a in h["einstellungen_abschnitte"] + h["bewegung_klang_schalter"]:
        ziel = [x.strip() for x in a.get("durch", a["testid"]).split(",")]
        da = all(f'"{z}"' in insel + teile for z in ziel)
        if a["stand"] == "ausnahme":
            assert f'data-testid="{a["testid"]}"' not in insel, a["testid"]
        else:
            assert da, f"{a['testid']}: {ziel} steht nicht in der Insel"
    for name in ("<EinstellungenSchale", "<AbschnittDarstellung", "<AbschnittAnzeige", "<AbschnittBewegungKlang", "<SchalterTouchUndo"):
        assert name in insel, name


def test_kreis_und_chip_oeffnen_die_insel():
    kopf = (WIRT / "kopf.tsx").read_text(encoding="utf-8")
    assert "onClick={() => oeffneEinstellungen()}" in kopf
    assert "onSyncToggle={() => oeffneEinstellungen('rechner')}" in kopf
    main = (WIRT / "main.tsx").read_text(encoding="utf-8")
    assert "<VisboxEinstellungen />" in main and "<VisboxAssistent />" in main
    assert "<VisWorkspace onKosmoOeffnen={wechsleGespraech} />" in main
    assert main.index("meldeAssistentAn();") < main.index("createRoot(")


def test_name_und_merkliste_wie_im_kern():
    kern = (WURZEL / "ipad" / "Visbox.swiftpm" / "Kern" / "Knotenwirtinseln.swift").read_text(encoding="utf-8")
    kopf = (WIRT / "kopf.tsx").read_text(encoding="utf-8")
    name = re.search(r'assistentName = "([^"]+)"', kern).group(1)
    assert f"ASSISTENT_NAME = '{name}'" in kopf
    assert name == "Assistent"  # Entscheid 116 (2)
    swift = re.findall(r'"([\w.-]+)"', re.search(r"merkbar: \[String\] = \[([^\]]+)\]", kern).group(1))
    bruecke = (WIRT / "wirt-bruecke.ts").read_text(encoding="utf-8")
    ts = re.findall(r"'([\w.-]+)'", re.search(r"MERKBAR: readonly string\[\] = \[([^\]]+)\]", bruecke).group(1))
    assert swift == ts, (swift, ts)


def test_die_lizenzzeilen_stehen_im_notice():
    notice = (WURZEL / "NOTICE").read_text(encoding="utf-8")
    insel = (WIRT / "einstellungen.tsx").read_text(encoding="utf-8")
    for wort in ("Blender", "IfcOpenShell", "Z-Image-Turbo", "Qwen-Image-2.1", "qwen3:14b", "IBM Plex", "Instrument Serif", "Lato", "PT Sans Narrow", "CC0"):
        assert wort in insel, wort
        assert wort.lower() in notice.lower(), f"{wort} fehlt im NOTICE"


def test_das_gespraech_fuehrt_die_app_und_die_seite_kennt_kein_kennwort():
    gespraech = (KOPIE / "apps/kosmo-orbit/src/shell/kosmo-gespraech.ts").read_text(encoding="utf-8")
    panel = (KOPIE / "apps/kosmo-orbit/src/shell/KosmoPanel.tsx").read_text(encoding="utf-8")
    for code in (gespraech, panel, (WIRT / "einstellungen.tsx").read_text(encoding="utf-8")):
        ohne = re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)
        assert "fetch(" not in ohne, "die Seite fragt den Heim-PC selbst"
        assert not re.search(r"type=.password|passwort|password|token", ohne, re.I)
    # Die Regeln stehen im Kern: die Seite zählt keine Längen und keinen Verlauf nach.
    assert "2000" not in panel and "verlaufHoechstens" not in panel
    ansicht = (MAC / "Start" / "Arbeitsansicht.swift").read_text(encoding="utf-8")
    # Die Assistent-Leiste steht nur auf der Visbox-Seite; das Modell hält die Arbeitsansicht.
    assert re.search(r"if wahl != \.knoten \{\s*Rectangle\(\)[^\n]*\n\s*assistentenPlatz", ansicht)
    assert "Assistentenhalter" in ansicht and "frageVonSeite" in ansicht


@pytest.mark.skipif(not os.environ.get("KOSMO_ORBIT"), reason="KosmoOrbit liegt nicht daneben (KOSMO_ORBIT)")
def test_kosmoorbit_hat_keinen_abschnitt_der_hier_fehlt():
    app = Path(os.environ["KOSMO_ORBIT"]) / "apps" / "kosmo-orbit" / "src" / "shell"
    einst = (app / "Einstellungen.tsx").read_text(encoding="utf-8") + (app / "einstellungen-teile.tsx").read_text(encoding="utf-8")
    abschnitte = set(re.findall(r'<section[^>]*data-testid="(einstellungen-[\w-]+)"', einst))
    h = _ausnahmen()
    benannt = {a["testid"] for a in h["einstellungen_abschnitte"]}
    assert abschnitte - benannt == set(), f"KosmoOrbit hat neue Abschnitte: {sorted(abschnitte - benannt)}"
    einstellungen = (app / "Einstellungen.tsx").read_text(encoding="utf-8")
    block = einstellungen[einstellungen.index("<AbschnittBewegungKlang>"):einstellungen.index("</AbschnittBewegungKlang>")]
    schalter = set(re.findall(r'data-testid="(einstellung-[\w-]+)"', block)) | {"einstellung-touch-undo-geste"}
    assert schalter == {a["testid"] for a in h["bewegung_klang_schalter"]}, schalter
    panel = (app / "KosmoPanel.tsx").read_text(encoding="utf-8") + (app / "kosmo-feldkopf.tsx").read_text(encoding="utf-8")
    for a in h["gespraechsfeld_ausnahmen"]:
        assert f'"{a["testid"]}"' in panel, a["testid"]


def test_die_zwei_zeichen_von_visbox_stehen_im_wirt_nicht_in_der_kopie():
    """Entscheide 132/133 (22.10.2026, Blätter 47/48): Visbox-Logo oben links, Lot unten rechts.

    Beide sind benannte Ausnahmen von 115, und beide stehen allein im Wirt — die Kopie bleibt wortgleich
    (KosmoEckOrb.tsx und kosmo-eck-orb.css nicht unter ``geaendert``)."""
    zeichen = {a["testid"]: a for a in _ausnahmen()["zeichen_ausnahmen"]}
    assert set(zeichen) == {"visbox-logo", "kosmo-eck-orb"}
    for a in zeichen.values():
        assert a["stand"] == "ausnahme" and a["grund"] and a["entscheid"], a
    assert zeichen["visbox-logo"]["entscheid"].startswith("132")
    assert zeichen["kosmo-eck-orb"]["entscheid"].startswith("133")
    kopf = (WIRT / "kopf.tsx").read_text(encoding="utf-8")
    assert re.search(r"logo=\{<VisboxLogo\b", kopf), "die Palette trägt nicht das Visbox-Logo"
    assert "StationLogo" not in kopf, "die Kosmo-Spirale steht noch im Kopf"
    css = (WIRT / "visbox.css").read_text(encoding="utf-8")
    assert re.search(r"\.app-wurzel svg\[data-logo='kosmo'\] > \* \{\s*display: none;", css)
    assert "--visbox-lot:" in css and "@media (prefers-reduced-motion: reduce)" in css
    geaendert = _herkunft().get("geaendert", {})
    for datei in ("apps/kosmo-orbit/src/shell/kosmo-eck-orb/KosmoEckOrb.tsx",
                  "apps/kosmo-orbit/src/shell/kosmo-eck-orb/kosmo-eck-orb.css"):
        assert datei in _herkunft()["woertlich"] and datei not in geaendert, datei
