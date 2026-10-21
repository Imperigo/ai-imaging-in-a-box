"""Claude bedient Visbox am Mac — die Brücke zwischen MCP-Kern, Knotenansicht und Leiste.

Plan KI-Bedienung (``docs/PLAN_KI_BEDIENUNG_2026-10-20.md``), Stufe 3 und der Visbox-Teil von
Stufe 4; Entscheide 105–106f, 108 und 114; gezeichnet auf Blatt 30 («KI bedient Visbox»).

Die Logik prüfen ``swift test`` (``KibedienungTests``, ``McpkernTests``) und ``vitest``
(``kv-ki-werkzeuge``, ``ki-wirt``, ``ki-werkzeugliste``). Die Mac-App übersetzt nur die
Prüfstrecke am Mac; bewacht wird hier die **Verdrahtung**: dass die Seite den Werkzeugsatz
anhängt und nur sie die App erreicht, dass die Karte aus der Antwort der Knotenansicht kommt,
dass die Liste im Bau liegt, dass die Leiste und das Einrichten zu sehen sind — und dass kein
Weg die Grafikkarte freigibt.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IPAD = WURZEL / "ipad"
KERN = IPAD / "Visbox.swiftpm" / "Kern"
QUELLEN = IPAD / "VisboxMac" / "Sources" / "VisboxMac"
CLAUDE = QUELLEN / "Claude"
START = QUELLEN / "Start"
ASSISTENT = QUELLEN / "Assistent"
PROBEN = IPAD / "VisboxKern" / "Tests" / "VisboxKernTests"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten"
KOPIE = WURZEL / "kosmovis" / "apps" / "kosmo-orbit"


def _code(pfad: Path) -> str:
    """Der Quelltext ohne Zeilenkommentare — bewacht wird, was übersetzt wird."""
    return "\n".join(z for z in pfad.read_text(encoding="utf-8").splitlines()
                     if not z.lstrip().startswith(("//", "*", "/**")))


# ------------------------------------------------------------------- die Seite

def test_die_seite_haengt_den_werkzeugsatz_an_und_meldet_an_die_app():
    wirt = _code(WIRT / "src" / "ki-wirt.ts")
    assert "visboxKi = schnitt" in wirt
    assert "webkit?.messageHandlers?.visboxKi" in wirt
    assert "setzeVerlaufWache(kiVerlaufWache)" in wirt, "114: Strg+Z nur die eigenen Schritte"
    assert "verwirfVorschlaege(MAPPE_GEWECHSELT)" in wirt
    assert "'pagehide'" in wirt
    haupt = _code(WIRT / "src" / "main.tsx")
    assert haupt.index("await ladeGesichertenGraph();") < haupt.index("haengeKiAn(window);"), (
        "erst der Graph der Mappe, dann die Schnittstelle — sonst läse Claude den leeren Anfang")


def test_kein_weg_der_seite_gibt_die_grafikkarte_frei():
    for datei in (WIRT / "src" / "ki-wirt.ts", KOPIE / "src" / "modules" / "vis" / "ki-werkzeuge.ts"):
        code = _code(datei)
        assert not re.search(r"approve|freigeben\(|render-freigeben|approval", code, re.I), datei.name


def test_die_werkzeugliste_liegt_im_bau():
    liste = json.loads((WIRT / "dist" / "ki-werkzeugliste.json").read_text(encoding="utf-8"))
    assert liste["format"] == "visbox.ki-werkzeugliste/v1"
    namen = [w["name"] for w in liste["werkzeuge"]]
    # Seit Stufe 6 (21.10.2026) stehen Blick und Maus hinter den Werkzeugen der Knotenansicht.
    assert namen[0] == "graph_lesen" and namen[-3:] == ["vis_paket", "visbox_blick", "visbox_maus"]
    assert {"vis_nodeSetzen", "vis_verbinden", "vis_nodeLoeschen", "vis_render"} <= set(namen)
    arten = {w["name"]: w["art"] for w in liste["werkzeuge"]}
    assert arten["vis_nodeLoeschen"] == "loeschen" and arten["vis_render"] == "rendern"
    assert arten["visbox_blick"] == "lesen" and arten["visbox_maus"] == "bedienen"
    assert not [n for n in namen if re.search(r"freig|approv|gpu", n, re.I)]
    for w in liste["werkzeuge"]:
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", w["name"]) and w["inputSchema"]["type"] == "object"
    # DER BAU SCHREIBT SIE, DIE PROBE PRUEFT SIE (vite leert dist/).
    bau = (WURZEL / "tools" / "knoten_bau.py").read_text(encoding="utf-8")
    assert '"VISBOX_KI_LISTE_SCHREIBEN": "1"' in bau
    assert "kosmovis/apps/visbox-knoten/src/ki-wirt.ts" in bau


def test_die_kopie_traegt_den_werkzeugsatz_und_seine_probe():
    werkzeug = (WURZEL / "tools" / "kosmovis_uebernahme.py").read_text(encoding="utf-8")
    assert '"apps/kosmo-orbit/test/kv-ki-werkzeuge.test.ts",' in werkzeug
    assert '"apps/kosmo-orbit/test/kv-ki-werkzeuge-schema.test.ts":' in werkzeug
    herkunft = json.loads((WURZEL / "kosmovis" / "HERKUNFT.json").read_text(encoding="utf-8"))
    assert "apps/kosmo-orbit/src/modules/vis/ki-werkzeuge.ts" in herkunft["woertlich"]
    assert "apps/kosmo-orbit/src/modules/vis/ki-werkzeuge.ts" not in herkunft["geaendert"]


# ------------------------------------------------------------------- die Brücke in der App

def test_der_bote_haengt_vor_dem_bau_der_ansicht_und_hoert_nur_die_eigene_seite():
    flaeche = _code(START / "Arbeitsansicht.swift")
    anhaengen = flaeche.index("Knotenki.haengeAn(einstellung, bote: context.coordinator.kibote)")
    assert anhaengen < flaeche.index("let ansicht = WKWebView(frame: .zero, configuration: einstellung)")
    assert "static func dismantleNSView" in flaeche and 'Knotenki.seiteGeht("Die Knotenansicht wurde geschlossen")' in flaeche
    bote = _code(START / "Knotenki.swift")
    assert "static let name = Kibruecke.name" in bote
    assert 'public static let name = Mcp.servername + "Ki"' in _code(KERN / "Kibedienung.swift"), (
        "der Name, den ki-wirt.ts schreibt (visboxKi)")
    assert "nachricht.frameInfo.isMainFrame" in bote
    assert "Knotenwege.istEigen(adresse)" in bote, "die Visbox-Seite des Heim-PC legt keine Karte"
    assert "callAsyncJavaScript(rumpf, arguments: argumente" in bote
    assert "Schwacherbote" in bote, "die Konfiguration hält den Boten nur schwach"


def test_die_karte_kommt_aus_der_antwort_der_knotenansicht():
    zentrale = _code(CLAUDE / "Kizentrale.swift")
    assert "Kibruecke.traegerantwort(aus: antwort)" in zentrale
    assert "brauchtKarte" not in zentrale, "nicht allein aus der Art des Werkzeugs"
    # NUR DIE WEGE VON window.visboxKi, keiner gibt frei.
    aufrufe = set(re.findall(r'Kibruecke\.rumpf\("(\w+)\(', zentrale))
    assert aufrufe == {"rufe", "entscheide", "werkzeuge", "rueckgaengigKi", "stelleWieder"}, aufrufe
    assert "rufe(JSON.parse(ruf), modus)" in zentrale, "der Modus kommt bei jedem Aufruf mit"
    assert "Kibruecke.nichtOffen" in zentrale, "ohne offene Knotenansicht ein klarer Satz"
    assert "Knotenwege.ordnerImBuendel" in zentrale and "Kibruecke.listendatei" in zentrale
    assert "sendeAnClaude(kennung, ergebnis)" in zentrale and "await kern.entscheide(kennung, antwort)" in zentrale
    # STRANG KARTEN (21.10.2026): Geht die Seite, bleiben die Karten — niemand verwirft sie still.
    weg = zentrale[zentrale.index("func knotenWeg"):zentrale.index("func empfange")]
    assert "beantworteOffene" not in weg and "ablage.seiteWeg()" in weg, weg


def test_offene_karten_ueberleben_den_wechsel_der_ansicht():
    """Strang Karten: Die App haelt die Karten und gibt sie der neu geladenen Seite zurueck."""
    zentrale = _code(CLAUDE / "Kizentrale.swift")
    assert "Task { await gibKartenZurueck() }" in zentrale, "nach «bereit» zurueckgeben"
    assert 'Kibruecke.rumpf("stelleWieder(JSON.parse(karten))")' in zentrale
    assert "ablage.lege(karte, mappe: kartenmappe)" in zentrale
    assert "ablage.entscheide(kennung, ja: ja, mappe: kartenmappe, seiteOffen: knoten != nil)" in zentrale
    # FOLGEAUFTRAG (Regel wie KosmoOrbit v0.1.10): keine Frist; echtes Beenden und Leitungsverlust.
    assert "pruefeAblauf" not in zentrale and "Timer" not in zentrale, "keine Frist mehr"
    assert "NSApplicationWillTerminateNotification" in zentrale and "beende(.appZu)" in zentrale
    assert "await kern.meldeNeu(neu)" in zentrale, "beim Wiederverbinden zuerst neu anmelden"
    anschluss = _code(CLAUDE / "Claudeanschluss.swift")
    halte = anschluss[anschluss.index("func halte()"):anschluss.index("private func hoererZustand")]
    assert halte.index("beende(.anschlussAus)") < halte.index("hoerer?.cancel()"), "Satz vor dem Abschalten"
    assert "Kizentrale.gemeinsam.leitungWeg()" in anschluss and "Kizentrale.gemeinsam.leitungWieder()" in anschluss
    flaeche = _code(START / "Arbeitsansicht.swift")
    assert "Kizentrale.gemeinsam.setzeKartenmappe(mappe)" in flaeche
    wirt = _code(WIRT / "src" / "ki-wirt.ts")
    verlassen = wirt[wirt.index("const beimVerlassen"):wirt.index("fenster.addEventListener('pagehide'")]
    assert "verwirf" not in verlassen, "beim Neuladen wird in der Seite nichts verworfen"
    assert "behandle(alsAufruf(v), 'karte')" in wirt, "zurueckgegeben wird nie still angewendet"
    kern = (KERN / "Kartenablage.swift").read_text(encoding="utf-8")
    assert "frist" not in kern.lower().replace("wartefrist", ""), "keine Ablauf-Frist an Karten"
    assert 'leitungUnterbrochen = "Leitung unterbrochen"' in kern


def test_die_mac_werkzeuge_lesen_ueber_die_bestehenden_wege_und_geben_nichts_frei():
    kern = _code(KERN / "Kibedienung.swift")
    for weg in ('"/knoten/mappe"', '"/knoten/skizze"', '"/bruecke/jobs/\\(jobId)/cancel"'):
        assert weg in kern, weg
    assert "approve" not in kern.lower()
    lesen = _code(START / "Heimlesen.swift")
    assert "delegate: Heimvertrauenslotse.gemeinsam" in lesen
    assert "Knotenwege.koepfeFuerHeim(seite: [], anmeldung: anmeldung)" in lesen
    assert "approve" not in lesen.lower()
    fenster = _code(START / "Hauptfenster.swift")
    assert fenster.count("Heimlesen.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)") == 3


def test_der_claude_teil_traegt_kein_geheimnis_und_keinen_fremden_import():
    for datei in sorted(CLAUDE.glob("*.swift")):
        importe = set(re.findall(r"^[ \t]*import[ \t]+(\w+)", datei.read_text(encoding="utf-8"), re.M))
        assert importe <= {"Foundation", "Network", "VisboxKern"}, (datei.name, importe)
    zentrale = _code(CLAUDE / "Kizentrale.swift")
    assert not re.search(r"authorization|token|kennwort|schluesselbund", zentrale, re.I)


# ------------------------------------------------------------------- Leiste und Einrichten

def test_die_leiste_zeigt_den_ki_teil_mit_und_ohne_heim_pc():
    leiste = _code(ASSISTENT / "Assistentenleiste.swift")
    assert "Kileiste(assistentSatz: Assistentenkopf.satz(modell.zeile, heimEingerichtet: true)" in leiste
    platz = _code(START / "Arbeitsansicht.swift")
    assert 'Kileiste(assistentSatz: "Assistent: " + stand.wort' in platz
    ki = _code(ASSISTENT / "Kileiste.swift")
    for teil in ("Claudezeile.zeile(lage: lage, letzterKontakt: kontakt",
                 "Picker(\"Selbständigkeit\"", "zentrale.setzeModus($0)",
                 "stand.strom(jetzt: zeit.date)", "karte.freigabeSatz",
                 "Kileistenstand.zuruecknehmenKnopf", "zentrale.stand.claudeZuruecknehmen",
                 "zentrale.entscheide(karte.kennung, ja: true)",
                 "zentrale.entscheide(karte.kennung, ja: false)"):
        assert teil in ki, teil


def test_das_einrichten_hat_den_abschnitt_claude_ueber_mcp():
    koppeln = _code(START / "Koppeln.swift")
    assert "Claudeeinrichten(anschluss: .gemeinsam" in koppeln
    assert koppeln.count('Button(Claudeeinrichtung.titel + " …")') == 2
    einrichten = _code(START / "Claudeeinrichten.swift")
    for teil in ("Claudeeinrichtung.befehl", "Claudeeinrichtung.daten", "Claudeeinrichtung.nurHier",
                 "anschluss.schalte($0)", "anschluss.lage.satz", "Claudedesktop.mische(",
                 "NSPasteboard.general.setString(Claudeeinrichtung.befehl"):
        assert teil in einrichten, teil
    kern = (KERN / "Kibedienung.swift").read_text(encoding="utf-8")
    # 106f WOERTLICH WIE AUF DEM BLATT.
    assert '"Mappennamen, Prompts, den Knotengraph und Bilder, die Claude ansehen "' in kern
    assert '+ "will. Das geht an Anthropic."' in kern
    assert '"Nur auf diesem Mac. Kein Weg aus dem Internet."' in kern


def test_der_kern_hat_seine_proben():
    proben = (PROBEN / "KibedienungTests.swift").read_text(encoding="utf-8")
    for name in ("testDieAntwortSagtObEsEineKarteIst", "testDieLeisteFolgtDenEreignissen",
                 "testClaudeGiltNurAlsVerbundenWennEsKuerzlichSprach",
                 "testKennungenBleibenImWegDerBruecke",
                 "testDerEintragFuerClaudeDesktopLaesstAllesAndereStehen"):
        assert f"func {name}(" in proben, name
    for datei in ("ki-wirt.test.ts", "ki-werkzeugliste.test.ts"):
        assert (WIRT / "test" / datei).is_file(), datei
