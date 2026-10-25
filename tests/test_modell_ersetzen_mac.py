"""Befund «Andere Datei» (Mac-Probe Visbox 0.3.67, Mappe «haus-am-hang», 25.10.2026) — die Rückkehr von N1.

«Andere Datei …» am Modell-Knoten einer **bestehenden** Mappe am Mac ersetzte das Modell nicht: Am
Heim-PC kam die neue Fassung an (38 Bauteile), am Mac blieben ``modell.glb`` (vom 22.10.) und
``mappe.json`` (30 Bauteile, alte Hüllbox, ``heimMappe`` unverändert). Am Knoten stand «38» — die Zahl
aus dem Stand des **Heim-PC**, nicht aus der Mappe am Mac.

Die Kette hat drei Glieder; dieser Probensatz hält jedes fest:

1. **Heim-PC** (hier gerechnet): Laden mit ``X-Mappe-Am-Mac``/``X-Mappe-Heim`` → neue Fassung im
   Zwilling (oder ein neuer Zwilling, wenn der genannte hier gerade offen ist), Stand mit ``am_mac``;
   ``/knoten/mappe-paket`` und ``/knoten/mappe-datei`` liefern danach **das neue** Modell mit 38
   Bauteilen. Dieses Glied war richtig und bleibt es.
2. **Seite** (vitest ``kosmovis/apps/visbox-knoten/test/modell-ersetzen-mac.test.ts``): Kam das Laden aus
   einer Mappe am Mac, ist ein 404 der App kein «nichts zu tun» mehr, und der Knoten zeigt, was **in der
   Mappe am Mac** liegt — weicht es vom Heim-PC ab, steht ein Satz da. Beim Öffnen holt die Seite ein
   fertiges Laden dieser Mappe nach, das nicht ankam.
3. **Mac-App** (Swift, hier als Text; XCTest ``MacmappeTests``): altes Modell als ``modell.vorher.glb``,
   neues erst nach Grössenprobe gültig, ``mappe.json`` nennt den Zwilling (``heim_mappe``) für die Seite.

Regel 3: alles synthetisch (``tools/make_test_glb.py``).
"""
from __future__ import annotations

import re

from aiimaging import projekt

from test_modell_laden import MK_GLB, WURZEL, _Server, server, start  # noqa: F401 — Fixtures
from test_mappe_am_mac_laden import _lade

MAC = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Start"
KERN = WURZEL / "ipad" / "Visbox.swiftpm" / "Kern"
WIRT = WURZEL / "kosmovis" / "apps" / "visbox-knoten" / "src"
KOPF = {"X-Mappe-Am-Mac": "haus-am-hang"}


def _haus(teile: int) -> bytes:
    """Ein synthetisches Haus aus ``teile`` Scheiben — 30 vorher, 38 nachher wie im Befund."""
    return MK_GLB.baue_glb([(f"Teil_{i:02d}", (i * 0.5, 0, 0), (i * 0.5 + 0.4, 3, 6)) for i in range(teile)])


def _lies(p):
    return p.read_text(encoding="utf-8")


# ======================================================================== 1 · der Heim-PC

def test_die_neue_fassung_kommt_im_zwilling_an_und_das_paket_liefert_sie(server, start):
    s = _Server(server, start)
    erste = _lade(s, "haus-am-hang.glb", _haus(30), KOPF)
    assert erste["mappe"] == "haus-am-hang" and erste["bauteile"] == 30
    neu = _haus(38)
    zweite = _lade(s, "haus-am-hang.glb", neu, {**KOPF, "X-Mappe-Heim": "haus-am-hang"})
    # DER ZWILLING BEKOMMT DIE NEUE FASSUNG — und der Stand sagt, aus welcher Mappe am Mac.
    assert zweite["stand"] == "geladen" and zweite["mappe"] == "haus-am-hang"
    assert zweite["ersetzt"] is True and zweite["fassung"] == 2 and zweite["bauteile"] == 38
    assert zweite["am_mac"] == "haus-am-hang"
    # WAS DIE MAC-APP DANACH HOLT, ist das neue Modell: Paket und Datei, beide mit 38.
    code, paket = s.get("/knoten/mappe-paket?mappe=haus-am-hang")
    assert code == 200
    assert paket["knoten"]["bauteile"] == 38 and paket["knoten"]["fassung"] == 2
    modell = [d for d in paket["dateien"] if d["art"] == "modell"]
    assert modell == [{"weg": "modell.glb", "art": "modell", "bytes": len(neu)}]
    code, roh = s.get("/knoten/mappe-datei?mappe=haus-am-hang&weg=modell.glb")
    assert code == 200 and roh == neu


def test_ist_der_zwilling_am_heim_pc_offen_entsteht_ein_neuer_und_der_stand_nennt_ihn(server, start):
    """Die Mappe, mit der am Heim-PC gearbeitet wird, bekommt nie eine Fassung vom Mac (304 B1).
    Dann ist der Zwilling ein anderer — die Mappe am Mac muss danach DIESEN nennen (``heim_mappe``)."""
    s = _Server(server, start)
    _lade(s, "haus-am-hang.glb", _haus(30), KOPF)
    s.klasse.zuletzt_geoeffnet = str(start.parent / "haus-am-hang")
    zweite = _lade(s, "haus-am-hang.glb", _haus(38), {**KOPF, "X-Mappe-Heim": "haus-am-hang"})
    assert zweite["mappe"] == "haus-am-hang-2" and zweite["ersetzt"] is False
    assert zweite["bauteile"] == 38 and zweite["am_mac"] == "haus-am-hang"
    assert projekt.modellfassung(projekt.oeffne(start.parent / "haus-am-hang")["projekt"]) == 1


# ======================================================================== 2 · die Seite

def test_ein_404_nach_dem_laden_aus_der_mappe_am_mac_ist_ein_fehler():
    seite = _lies(WIRT / "mappe.ts")
    start_ = seite.index("export async function holeInDieMappeAmMac")
    teil = seite[start_:start_ + 1400]
    assert "mussAmMac = false" in teil
    assert "if (antwort.status === 404 && !mussAmMac) return null;" in teil
    # Bis 0.3.67 war JEDE 404 still — auch die einer Mappe am Mac.
    assert "if (antwort.ok || antwort.status === 404) return null;" not in seite
    verfolge = seite[seite.index("export async function verfolge"):seite.index("export const WEG_MODELL_HOLEN")]
    assert "const amMac = Boolean(jetzt.am_mac) && imEigenenSchema();" in verfolge
    assert "holeInDieMappeAmMac(jetzt.mappe, undefined, undefined, amMac)" in verfolge
    assert "if (amMac) return zustandNachDemHolen(jetzt, offeneAntwort);" in verfolge


def test_beim_oeffnen_holt_die_seite_ein_fertiges_laden_nach():
    haupt = _lies(WIRT / "main.tsx")
    assert re.search(r"const nachgeholt = await nimmFertigesLadenAn\(sicht\.laden\);", haupt)


# ======================================================================== 3 · die Mac-App

def test_die_mac_app_sichert_das_alte_modell_und_prueft_das_neue():
    ablage = _lies(MAC / "Mappenablage.swift")
    start_ = ablage.index("func holeModell(von kennung: String, in ordner: URL")
    rumpf = ablage[start_:ablage.index("private func holePaket", start_)]
    assert 'nonisolated static let modellVorher = "modell.vorher.glb"' in ablage
    assert "try fm.copyItem(at: glb, to: vorherGlb)" in rumpf
    assert "guard let schritt = plan.first else" in rumpf
    assert "guard groesse == schritt.bytes else" in rumpf
    # Die Reihenfolge: sichern, holen, prüfen, erst dann mappe.json.
    assert (rumpf.index("copyItem") < rumpf.index("try await holeDateien(plan")
            < rumpf.index("guard groesse == schritt.bytes") < rumpf.index("Mappenablage.schreibe(mappe"))
    # N1 bleibt: in genau die Mappe der Anfrage, frisch gelesen, Zwilling und Auswertung gesetzt.
    assert "mappe.heimMappe = kennung" in rumpf and "mappe.knoten = paket.knotenFuerMappe" in rumpf


def test_die_mappe_am_mac_nennt_ihren_zwilling():
    kern = _lies(KERN / "Macmappe.swift")
    assert 'felder["heim_mappe"] = mappe.heimMappe.map(JSONWert.text) ?? .null' in kern


# ======================================================================== Zusatz: Fassungswache (0.3.68)

STDIO = WURZEL / "ipad" / "VisboxMac" / "Sources" / "VisboxMac" / "Claude"


def test_die_app_nennt_ihre_fassung_in_jeder_mcp_antwort():
    """Mac-Probe 0.3.67: Die Claude-Verbindung (``--mcp-stdio``) lief nach der Aktualisierung mit dem alten
    Code weiter — alter Werkzeugkatalog. Die App nennt ihre Fassung jetzt im Kopf jeder Antwort."""
    leitung = _lies(STDIO / "Claudeleitung.swift")
    assert "Mcpfassungswache.mitFassung(roh, Claudeleitung.fassung)" in leitung
    wache = _lies(KERN / "Mcpfassungswache.swift")
    assert 'public static let kopf = "X-App-Fassung"' in wache


def test_der_stdio_weg_warnt_bei_anderer_fassung_ohne_zu_scheitern():
    stdio = _lies(STDIO / "Claudestdio.swift")
    assert "bearbeite(zeile, ersatz: ersatz, fassung: fassung)" in stdio
    assert "Mcpfassungswache.appFassung(ausAntwort: daten)" in stdio
    assert ".map { Mcpfassungswache.zeile($0, warnung: warnung) }" in stdio
    wache = _lies(KERN / "Mcpfassungswache.swift")
    # Der Wortlaut der Warnung — eine Zeile vor dem Text, kein Fehler.
    assert '"Claude-Verbindung läuft mit \\(b), App ist \\(a) — Claude neu starten."' in wache
    assert 'erstes["text"] = .text("⚠ " + warnung + "\\n" + text)' in wache
    assert "-32603" not in wache and "fehler(" not in wache
