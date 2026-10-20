import Foundation
import XCTest
import VisboxKern

/// Stufe 3 und 4 der KI-Bedienung (Entscheide 105–106f, 108, 114): was die Antworten der
/// Knotenansicht heissen, was die Assistent-Leiste zeigt, die Werkzeuge der Mac-App und der
/// Eintrag fuer Claude Desktop.
final class KibedienungTests: XCTestCase {

    private func json(_ text: String) throws -> JSONWert {
        try JSONWert.lies(Data(text.utf8))
    }

    // ------------------------------------------------------------- die Bruecke

    func testDieWerkzeugeKommenAusDerListeOderDerDatei() throws {
        let eintrag = #"{"name":"vis_nodeSetzen","description":"setzt","inputSchema":{"type":"object","properties":{}},"art":"aendern"}"#
        let kaputt = #"{"name":"kein name!","description":"x","inputSchema":{"type":"object"},"art":"aendern"}"#
        let fremdeArt = #"{"name":"x_y","description":"x","inputSchema":{"type":"object"},"art":"freigeben"}"#
        let ohneSchema = #"{"name":"x_z","description":"x","inputSchema":{"type":"array"},"art":"lesen"}"#
        let liste = Kibruecke.werkzeuge(aus: try json("[\(eintrag),\(kaputt),\(fremdeArt),\(ohneSchema)]"))
        XCTAssertEqual(liste.map(\.name), ["vis_nodeSetzen"], "nur gültige Namen, Schemas und Arten")
        XCTAssertEqual(liste.first?.art, .aendern)
        let datei = Kibruecke.werkzeuge(aus: try json(#"{"format":"\#(Kibruecke.listenformat)","werkzeuge":[\#(eintrag)]}"#))
        XCTAssertEqual(datei.map(\.name), ["vis_nodeSetzen"])
        XCTAssertTrue(Kibruecke.werkzeuge(aus: try json(#"{"format":"anders/v9","werkzeuge":[\#(eintrag)]}"#)).isEmpty,
                      "ein unbekanntes Format wird nicht geraten")
    }

    func testDieAntwortSagtObEsEineKarteIst() throws {
        let sofort = Kibruecke.traegerantwort(aus: try json(#"{"sofort":{"kennung":"K-1","ok":true,"text":"ANGEWENDET"}}"#))
        XCTAssertEqual(sofort, .ergebnis(Mcpergebnis(text: "ANGEWENDET")))
        let fehler = Kibruecke.traegerantwort(aus: try json(#"{"sofort":{"kennung":"K-1","ok":false,"text":"FEHLER: x"}}"#))
        XCTAssertEqual(fehler, .ergebnis(Mcpergebnis(text: "FEHLER: x", fehler: true)))
        // EIN PAKET IST «aendern», MIT LOESCHEN DARIN ABER EINE KARTE — die Antwort entscheidet.
        let karte = Kibruecke.traegerantwort(aus: try json(#"{"karte":{"kennung":"K-2","werkzeug":"vis_paket","art":"loeschen","urheber":"claude","zusammenfassung":"Paket: 2 Schritte","schritte":[]}}"#))
        XCTAssertEqual(karte, .karte("Paket: 2 Schritte"))
        XCTAssertEqual(Kibruecke.traegerantwort(aus: .null), .ergebnis(Mcpergebnis(text: Kibruecke.unlesbar, fehler: true)))
        XCTAssertTrue(Kibruecke.nichtOffen.contains("nicht offen"))
        XCTAssertEqual(Kibruecke.name, Mcp.servername + "Ki")
        XCTAssertEqual(Kibruecke.rumpf("werkzeuge()"),
                       "return \(Kibruecke.name).alsText(\(Kibruecke.name).werkzeuge());")
        XCTAssertTrue(Kibruecke.verworfen("neu geladen").text.hasPrefix("VERWORFEN: neu geladen"))
    }

    // ------------------------------------------------------------- Ereignisse und Leiste

    func testDieEreignisseDerSeite() throws {
        XCTAssertEqual(Kiereignis(try json(#"{"art":"taetigkeit","phase":"beginn","kennung":"K-1","werkzeug":"graph_lesen","urheber":"claude","zeit":1}"#)),
                       .beginn(kennung: "K-1", werkzeug: "graph_lesen", urheber: .claude))
        XCTAssertEqual(Kiereignis(try json(#"{"art":"taetigkeit","phase":"ende","kennung":"K-1","werkzeug":"graph_lesen","urheber":"assistent","zeit":1,"ok":true,"text":"{}"}"#)),
                       .ende(kennung: "K-1", werkzeug: "graph_lesen", urheber: .assistent, ok: true, text: "{}"))
        XCTAssertEqual(Kiereignis(try json(#"{"art":"entschieden","kennung":"K-2","angewendet":false,"ergebnis":{"kennung":"K-2","ok":false,"text":"ABGELEHNT: x"}}"#)),
                       .entschieden(kennung: "K-2", angewendet: false, ergebnis: Mcpergebnis(text: "ABGELEHNT: x", fehler: true)))
        XCTAssertEqual(Kiereignis(try json(#"{"art":"kiverlauf","anzahl":1,"letzter":{"claude":{"kennung":"K-3","urheber":"claude","zusammenfassung":"verschoben"},"assistent":null}}"#)),
                       .kiverlauf(claude: Kischritt(kennung: "K-3", urheber: .claude, zusammenfassung: "verschoben"), assistent: nil))
        XCTAssertEqual(Kiereignis(try json(#"{"art":"bereit","werkzeuge":13}"#)), .bereit(werkzeuge: 13))
        XCTAssertEqual(Kiereignis(try json(#"{"art":"weg","grund":"neu"}"#)), .weg(grund: "neu"))
        XCTAssertNil(Kiereignis(try json(#"{"art":"unbekannt"}"#)))
        XCTAssertNil(Kiereignis(try json(#"{"art":"karte","vorschlag":{"kennung":"K-9"}}"#)), "eine halbe Karte ist keine")
    }

    private func karte(_ kennung: String, art: String = "aendern", urheber: String = "claude") throws -> Kiereignis {
        try XCTUnwrap(Kiereignis(try json(#"{"art":"karte","vorschlag":{"kennung":"\#(kennung)","werkzeug":"vis_paket","art":"\#(art)","urheber":"\#(urheber)","zusammenfassung":"3 Knoten anlegen","schritte":[{"commandId":"vis.nodeSetzen","params":{},"zusammenfassung":"+ Stimmung"},{"commandId":"vis.nodeSetzen","params":{},"zusammenfassung":"+ Varianten"}]}}"#)))
    }

    func testDieKarteNachDemBlatt() throws {
        guard case .karte(let k) = try karte("K-12", art: "rendern") else { return XCTFail() }
        XCTAssertEqual(k.kopf, "Vorschlag von Claude · K-12")
        XCTAssertEqual(k.freigabeSatz, "Rendern braucht danach deine Freigabe am Knoten.")
        XCTAssertEqual(k.zeilen, ["+ Stimmung", "+ Varianten"])
        guard case .karte(let a) = try karte("K-13", art: "loeschen", urheber: "assistent") else { return XCTFail() }
        XCTAssertEqual(a.kopf, "Vorschlag des Assistenten · K-13")
        XCTAssertNil(a.freigabeSatz, "nur Render-Karten tragen den Satz")
    }

    func testDieLeisteFolgtDenEreignissen() throws {
        var stand = Kileistenstand()
        let t0 = Date(timeIntervalSince1970: 1000)
        XCTAssertTrue(stand.strom(jetzt: t0).isEmpty, "108 C: ohne Arbeit kein Strom")
        stand.nimm(.beginn(kennung: "K-1", werkzeug: "vis_nodeSetzen", urheber: .claude), jetzt: t0)
        XCTAssertEqual(stand.strom(jetzt: t0), ["Claude legt einen Knoten an …"])
        stand.nimm(.ende(kennung: "K-1", werkzeug: "vis_nodeSetzen", urheber: .claude, ok: true, text: ""), jetzt: t0)
        XCTAssertEqual(stand.strom(jetzt: t0.addingTimeInterval(1)).count, 1, "kurzer Nachlauf")
        XCTAssertTrue(stand.strom(jetzt: t0.addingTimeInterval(Kileistenstand.nachlauf + 0.1)).isEmpty)
        // Eine Karte steht als Karte da, nicht im Strom.
        stand.nimm(.beginn(kennung: "K-12", werkzeug: "vis_paket", urheber: .claude), jetzt: t0)
        stand.nimm(try karte("K-12"), jetzt: t0)
        XCTAssertEqual(stand.karten.map(\.kennung), ["K-12"])
        XCTAssertTrue(stand.strom(jetzt: t0.addingTimeInterval(10)).isEmpty)
        stand.nimm(try karte("K-13", urheber: "assistent"), jetzt: t0)
        stand.nimm(.entschieden(kennung: "K-12", angewendet: true, ergebnis: Mcpergebnis(text: "ok")), jetzt: t0)
        XCTAssertEqual(stand.karten.map(\.kennung), ["K-13"])
        // 114: der Knopf nur, wenn es einen Schritt von Claude gibt.
        XCTAssertNil(stand.claudeZuruecknehmen)
        stand.nimm(.kiverlauf(claude: Kischritt(kennung: "K-20", urheber: .claude, zusammenfassung: "x"), assistent: nil))
        XCTAssertEqual(stand.claudeZuruecknehmen?.kennung, "K-20")
        stand.nimm(.bereit(werkzeuge: 13))
        XCTAssertTrue(stand.knotenBereit)
        stand.nimm(.weg(grund: "neu"))
        XCTAssertFalse(stand.knotenBereit)
        XCTAssertTrue(stand.karten.isEmpty)
        XCTAssertNil(stand.claudeZuruecknehmen)
        XCTAssertEqual(Kileistenstand.zuruecknehmenKnopf, "Claudes letzten Schritt zurücknehmen")
    }

    func testDerStromHatEinfacheWorte() {
        XCTAssertEqual(Kiworte.tut("vis_verbinden"), "verbindet zwei Knoten")
        XCTAssertEqual(Kiworte.tut("bild_ansehen"), "sieht ein Bild an")
        XCTAssertEqual(Kiworte.tut("unbekannt"), "arbeitet")
    }

    // ------------------------------------------------------------- die Zeilen oben

    func testClaudeGiltNurAlsVerbundenWennEsKuerzlichSprach() {
        let jetzt = Date(timeIntervalSince1970: 10_000)
        XCTAssertEqual(Claudezeile.zeile(lage: .bereit, letzterKontakt: jetzt.addingTimeInterval(-5), jetzt: jetzt).titel,
                       "Claude verbunden")
        XCTAssertEqual(Claudezeile.zeile(lage: .bereit, letzterKontakt: jetzt.addingTimeInterval(-5), jetzt: jetzt).zusatz,
                       "· über MCP, nur dieser Mac")
        XCTAssertEqual(Claudezeile.zeile(lage: .bereit, letzterKontakt: nil, jetzt: jetzt).titel, "Claude: bereit")
        XCTAssertEqual(Claudezeile.zeile(lage: .bereit, letzterKontakt: jetzt.addingTimeInterval(-Claudezeile.frische - 1),
                                         jetzt: jetzt).titel, "Claude: bereit", "zu lange still")
        XCTAssertEqual(Claudezeile.zeile(lage: .aus, letzterKontakt: jetzt, jetzt: jetzt).titel, "Claude: aus")
        XCTAssertEqual(Claudezeile.zeile(lage: .gestoert("belegt"), letzterKontakt: nil, jetzt: jetzt).titel,
                       "Claude: nicht bereit")
    }

    func testDieZeileDesAssistenten() {
        XCTAssertEqual(Assistentenkopf.satz(Assistentenzeile(stand: .bereit, modell: "qwen3:14b", satz: ""),
                                            heimEingerichtet: true),
                       "Assistent: qwen3:14b am Heim-PC · bereit")
        XCTAssertEqual(Assistentenkopf.satz(nil, heimEingerichtet: false), "Assistent: braucht den Heim-PC")
    }

    func testDieSelbstaendigkeitWirdGemerkt() {
        XCTAssertEqual(Selbstaendigkeit(gemerkt: "coop"), .coop)
        XCTAssertEqual(Selbstaendigkeit(gemerkt: nil), .karte, "106b: Karte ist die Vorgabe")
        XCTAssertEqual(Selbstaendigkeit(gemerkt: "freigeben"), .karte)
        XCTAssertEqual(Selbstaendigkeit.einstellung, "ki.selbstaendigkeit")
    }

    // ------------------------------------------------------------- die Werkzeuge der Mac-App

    func testDieWerkzeugeDerMacApp() {
        XCTAssertEqual(Macwerkzeuge.alle.map(\.name), ["mappe_lesen", "skizzen_lesen", "lauf_abbrechen", "bild_ansehen"])
        for w in Macwerkzeuge.alle {
            XCTAssertTrue(Mcpwerkzeug.nameIstGueltig(w.name))
            XCTAssertEqual(w.eingabe["type"]?.alsText, "object")
            XCTAssertFalse(Mcpfreigabe.brauchtKarte(w.art, modus: .karte), "\(w.name): keines braucht eine Karte")
            XCTAssertNotEqual(w.art, .rendern, "keines startet die Grafikkarte")
        }
        XCTAssertEqual(Macwerkzeuge.laufAbbrechen.art, .anhalten)
        XCTAssertFalse(Macwerkzeuge.alle.contains { $0.name.contains("freig") || $0.name.contains("approve") })
    }

    func testKennungenBleibenImWegDerBruecke() {
        XCTAssertTrue(Macwerkzeuge.gueltigeKennung("job-20261020-abc_1"))
        XCTAssertTrue(Macwerkzeuge.gueltigeKennung("bild.png"))
        for boese in ["", "../etc", "a/b", ".versteckt", "a..b", "a b", "a%2Fb", String(repeating: "x", count: 129)] {
            XCTAssertFalse(Macwerkzeuge.gueltigeKennung(boese), boese)
        }
        XCTAssertEqual(Macwerkzeuge.abbrechenWeg("j1"), .init(methode: "POST", pfad: "/bruecke/jobs/j1/cancel", frage: nil))
        XCTAssertEqual(Macwerkzeuge.artefaktWeg("j1", "bild.png")?.pfad, "/bruecke/jobs/j1/artifacts/bild.png")
        XCTAssertNil(Macwerkzeuge.artefaktWeg("j1", "../x"))
        XCTAssertEqual(Macwerkzeuge.skizzeWeg("skizze 3.png").frage, "name=skizze%203.png")
        XCTAssertEqual(Macwerkzeuge.mappeWeg.pfad, "/knoten/mappe")
    }

    func testDieAntwortenDerMacWerkzeuge() throws {
        let mappe = Data(#"{"name":"Hofhaus","glb":true,"bauteile":12,"grund":"","skizzen":[{"name":"s1.png"}]}"#.utf8)
        let m = Macwerkzeuge.mappeErgebnis(status: 200, daten: mappe)
        XCTAssertTrue(m.text.hasPrefix("Mappe «Hofhaus»: Modell geladen (12 Bauteile), 1 Skizze(n)."), m.text)
        XCTAssertFalse(m.fehler)
        let fehlt = Macwerkzeuge.mappeErgebnis(status: 404, daten: Data(#"{"fehler":"Kein Projektordner"}"#.utf8))
        XCTAssertEqual(fehlt, Mcpergebnis(text: "Kein Projektordner", fehler: true))
        XCTAssertEqual(Macwerkzeuge.skizzenErgebnis(status: 200, daten: Data(#"{"skizzen":[]}"#.utf8)).text,
                       "Die Mappe hat keine Skizzen vom iPad.")
        XCTAssertEqual(Macwerkzeuge.abbrechenErgebnis(status: 200, daten: Data(#"{"status":"cancelled"}"#.utf8), jobId: "j1").text,
                       "Lauf j1 abgebrochen — die Grafikkarte ist frei.")
        XCTAssertEqual(Macwerkzeuge.abbrechenErgebnis(status: 200, daten: Data(#"{"status":"done"}"#.utf8), jobId: "j1").text,
                       "Lauf j1 war schon beendet (done); nichts geändert.")
        let zettel = Data(#"{"status":"done","result":{"images":["a.png","b.png"]}}"#.utf8)
        XCTAssertEqual(Macwerkzeuge.bildname(laufzettel: zettel, status: 200, jobId: "j1", nummer: 1), .name("b.png"))
        guard case .keines(let e) = Macwerkzeuge.bildname(laufzettel: zettel, status: 200, jobId: "j1", nummer: 5) else {
            return XCTFail()
        }
        XCTAssertTrue(e.text.contains("bild ist 0 bis 1"), e.text)
        guard case .keines(let leer) = Macwerkzeuge.bildname(laufzettel: Data(#"{"status":"running"}"#.utf8),
                                                             status: 200, jobId: "j1", nummer: 0) else { return XCTFail() }
        XCTAssertTrue(leer.text.contains("Stand: running"), leer.text)
    }

    func testEinBildGehtAlsBildAnClaude() {
        let png = Data([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0, 0, 0, 0])
        let e = Macwerkzeuge.bildErgebnis(status: 200, daten: png, typ: nil, was: "Bild 0 von j1")
        XCTAssertEqual(e.bild?.art, "image/png")
        XCTAssertEqual(e.bild?.daten, png.base64EncodedString())
        XCTAssertEqual(e.alsJSON["content"]?.alsListe?.last?["type"]?.alsText, "image")
        let gross = Data(count: Macwerkzeuge.bildHoechstens + 1)
        XCTAssertTrue(Macwerkzeuge.bildErgebnis(status: 200, daten: gross, typ: "image/png", was: "x").fehler)
        XCTAssertTrue(Macwerkzeuge.bildErgebnis(status: 200, daten: Data("text".utf8), typ: "text/plain", was: "x").fehler)
        XCTAssertEqual(Macwerkzeuge.bildart(typ: "image/jpeg; charset=binary", daten: Data()), "image/jpeg")
    }

    // ------------------------------------------------------------- Claude Desktop und Einrichten

    func testDerEintragFuerClaudeDesktopLaesstAllesAndereStehen() throws {
        let alt = Data(#"{"mcpServers":{"andere":{"command":"x"}},"theme":"dark"}"#.utf8)
        let neu = try Claudedesktop.mische(vorhanden: alt, programm: "/Programme/App.app/Contents/MacOS/App")
        let w = try JSONWert.lies(neu)
        XCTAssertEqual(w["theme"]?.alsText, "dark")
        XCTAssertEqual(w["mcpServers"]?["andere"]?["command"]?.alsText, "x")
        XCTAssertEqual(w["mcpServers"]?[Mcp.servername]?["args"], .liste([.text("--mcp-stdio")]))
        XCTAssertTrue(Claudedesktop.traegt(neu, programm: "/Programme/App.app/Contents/MacOS/App"))
        XCTAssertFalse(Claudedesktop.traegt(alt, programm: "/x"))
        let frisch = try Claudedesktop.mische(vorhanden: nil, programm: "/p")
        XCTAssertEqual(try JSONWert.lies(frisch)["mcpServers"]?[Mcp.servername]?["command"]?.alsText, "/p")
        XCTAssertThrowsError(try Claudedesktop.mische(vorhanden: Data("[1]".utf8), programm: "/p"),
                             "eine fremde Datei wird nicht überschrieben")
    }

    func testDieSaetzeImEinrichtenStehenWieAufDemBlatt() {
        XCTAssertEqual(Claudeeinrichtung.befehl, "claude mcp add --transport http \(Mcp.servername) " + Mcp.adresse)
        XCTAssertEqual(Mcp.adresse.count, "http://127.0.0.1:8631/mcp".count)
        XCTAssertEqual(Claudeeinrichtung.daten,
                       "Mappennamen, Prompts, den Knotengraph und Bilder, die Claude ansehen will. Das geht an Anthropic.")
        XCTAssertEqual(Claudeeinrichtung.nurHier, "Nur auf diesem Mac. Kein Weg aus dem Internet.")
        for satz in [Claudeeinrichtung.daten, Claudeeinrichtung.werkzeuge, Kibruecke.nichtOffen,
                     Kikarte.rendernSatz, Claudedesktop.satz(programm: "/p")] {
            XCTAssertFalse(satz.contains("ß"), satz)
        }
    }
}
