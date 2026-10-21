import Foundation
import XCTest
import VisboxKern

/// Ein Traeger, der fuer jedes Werkzeug eine Karte legt — die Entscheide kommen von aussen.
private struct Kartentraeger: Werkzeugtraeger {
    func werkzeuge() async -> [Mcpwerkzeug] {
        [Mcpwerkzeug(name: "vis_nodeParametrieren", beschreibung: "stellt ein", art: .aendern)]
    }

    func lage() async -> Mcplage { Mcplage(bereit: true, mappe: "Probe") }

    func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort {
        .karte("Node-Parameter (stimmung)")
    }
}

/// Strang Karten (21.10.2026): Offene Karten ueberleben einen Wechsel der Ansicht. Sie gelten pro
/// Mappe und Graph; verworfen wird nur mit «Ablehnen» oder nach Ablauf — und Claude hoert einen
/// Satz mit Grund.
final class KartenablageTests: XCTestCase {
    private let a = Kartenmappe(schluessel: "/m/Haus", name: "Haus")
    private let b = Kartenmappe(schluessel: "/m/Hof", name: "Hof")
    private let t0 = Date(timeIntervalSince1970: 1_800_000_000)

    private func json(_ text: String) throws -> JSONWert {
        try JSONWert.lies(Data(text.utf8))
    }

    /// Die Karte K-3 aus dem Demolauf: Stimmung morgen → abend.
    private func karte(_ kennung: String = "K-3", urheber: String = "claude") throws -> Kikarte {
        let roh = try json(#"""
            {"kennung":"\#(kennung)","werkzeug":"vis_nodeParametrieren","art":"aendern","urheber":"\#(urheber)",
             "zusammenfassung":"Node-Parameter (stimmung)",
             "schritte":[{"commandId":"vis.nodeParametrieren","params":{"graphId":"g1","nodeId":"n1","params":{"stimmung":"abend"}},"zusammenfassung":"Node-Parameter (stimmung)"}]}
            """#)
        return try XCTUnwrap(Kikarte(roh))
    }

    // ------------------------------------------------------------- ueberleben

    func testKarteUeberlebtEntladenUndNeuladenDerKnotenansicht() throws {
        var ablage = Kartenablage()
        var stand = Kileistenstand()
        let k = try karte()
        stand.nimm(.karte(k))
        ablage.lege(k, mappe: a, jetzt: t0)
        // ENTLADEN (Wechsel zur Visbox-Seite): Die Karte bleibt — in der Leiste und in der Ablage.
        stand.nimm(.weg(grund: "Die Knotenansicht wurde für die Seite geschlossen"))
        ablage.seiteWeg()
        XCTAssertEqual(stand.karten.map(\.kennung), ["K-3"], "die Leiste zeigt sie weiter")
        XCTAssertEqual(ablage.kennungen, ["K-3"])
        XCTAssertFalse(stand.knotenBereit)
        // NEU GELADEN: Die App gibt sie zurueck — der Vorschlag so, wie die Seite ihn schickte.
        let text = try XCTUnwrap(ablage.uebergabeText(a))
        let liste = try XCTUnwrap(try json(text).alsListe)
        XCTAssertEqual(liste.first?["kennung"]?.alsText, "K-3")
        XCTAssertEqual(liste.first?["schritte"]?.alsListe?.first?["params"]?["params"]?["stimmung"]?.alsText, "abend")
        ablage.nimmWiedergabe(try json(#"[{"kennung":"K-3","liegt":true,"text":"Node-Parameter (stimmung)"}]"#))
        stand.nimm(.karte(k))
        ablage.lege(k, mappe: a, jetzt: t0.addingTimeInterval(600))
        XCTAssertEqual(stand.karten.map(\.kennung), ["K-3"], "noch da, nicht doppelt")
        XCTAssertEqual(ablage.eintrag("K-3")?.seit, t0, "die Wiedergabe setzt die Zeit nicht neu")
        XCTAssertNil(ablage.uebergabeText(a), "liegt wieder in der Seite — nichts mehr zurueckzugeben")
        // ANWENDEN geht an die Seite (dort laeuft es wie jedes Anwenden).
        XCTAssertEqual(ablage.entscheide("K-3", ja: true, mappe: a, seiteOffen: true), .anDieSeite)
    }

    func testZurueckgegebeneKarteBehaeltIhrenPlatz() throws {
        var stand = Kileistenstand()
        stand.nimm(.karte(try karte("K-1")))
        stand.nimm(.karte(try karte("K-2")))
        stand.nimm(.weg(grund: "neu"))
        stand.nimm(.karte(try karte("K-1")))
        XCTAssertEqual(stand.karten.map(\.kennung), ["K-1", "K-2"])
    }

    func testAnwendenBeiGeschlossenerKnotenansichtWartet() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        ablage.seiteWeg()
        XCTAssertEqual(ablage.entscheide("K-3", ja: true, mappe: a, seiteOffen: false),
                       .wartet(meldung: Kartenablage.wartetSatz))
        XCTAssertEqual(ablage.kennungen, ["K-3"], "nichts verworfen")
        XCTAssertEqual(ablage.entscheide("K-3", ja: true, mappe: a, seiteOffen: true),
                       .wartet(meldung: Kartenablage.wirdZurueckgegebenSatz))
    }

    // ------------------------------------------------------------- Ablehnen und Ablauf: ein Satz an Claude

    func testAblehnenGibtClaudeEinenSatzAuchOhneKnotenansicht() async throws {
        let kern = Mcpkern(traeger: Kartentraeger(), fassung: "9.9.9", wartefrist: 5)
        let aufruf = Task {
            await kern.verarbeite(try self.json(
                #"{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"vis_nodeParametrieren","arguments":{}}}"#))
        }
        for _ in 0..<100 {
            if await kern.offeneVorschlaege().first?.karte != nil { break }
            try await Task.sleep(nanoseconds: 10_000_000)
        }
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        ablage.seiteWeg()
        guard case .hier(let antwort, _) = ablage.entscheide("K-1", ja: false, mappe: a, seiteOffen: false) else {
            return XCTFail("Ablehnen entscheidet hier, auch ohne Seite")
        }
        await kern.entscheide("K-1", antwort)
        let a = try await aufruf.value
        let satz = a?["result"]?["content"]?.alsListe?.first?["text"]?.alsText ?? ""
        XCTAssertTrue(satz.hasPrefix("ABGELEHNT: Der Architekt hat den Vorschlag abgelehnt"), satz)
        XCTAssertEqual(a?["result"]?["isError"], .wahrheit(true))
        XCTAssertTrue(ablage.kennungen.isEmpty)
    }

    func testBeiAblaufHoertClaudeDenGrundUeberVorschlagStatus() async throws {
        let kern = Mcpkern(traeger: Kartentraeger(), fassung: "9.9.9", wartefrist: 0.05)
        _ = await kern.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"vis_nodeParametrieren","arguments":{}}}"#))
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        XCTAssertTrue(ablage.abgelaufene(jetzt: t0.addingTimeInterval(Kartenablage.frist - 1)).isEmpty)
        let weg = ablage.abgelaufene(jetzt: t0.addingTimeInterval(Kartenablage.frist))
        XCTAssertEqual(weg.map(\.karte.kennung), ["K-1"])
        XCTAssertTrue(ablage.kennungen.isEmpty)
        for e in weg { await kern.entscheide(e.karte.kennung, Kartenablage.abgelaufen(e)) }
        let r = await kern.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"\#(Mcpkern.nachfrageName)","arguments":{"kennung":"K-1"}}}"#))
        let satz = r?["result"]?["content"]?.alsListe?.first?["text"]?.alsText ?? ""
        XCTAssertTrue(satz.hasPrefix("VERWORFEN: Der Vorschlag «Node-Parameter (stimmung)» lag 4 Stunden"), satz)
        XCTAssertTrue(satz.contains("abgelaufen"), satz)
        XCTAssertTrue(satz.contains("nichts wurde geändert"), satz)
        XCTAssertTrue(Kartenablage.abgelaufenMeldung(weg[0]).contains("Claude hat es gehört"))
    }

    // ------------------------------------------------------------- passt nicht mehr: beim Anwenden mit Satz

    func testAndereMappeGibtNichtsZurueckUndAnwendenWeistMitSatzAb() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        ablage.seiteWeg()
        XCTAssertNil(ablage.uebergabeText(b), "eine Karte gilt pro Mappe")
        XCTAssertNotNil(ablage.uebergabeText(a))
        guard case .hier(let antwort, let meldung) = ablage.entscheide("K-3", ja: true, mappe: b, seiteOffen: true) else {
            return XCTFail("andere Mappe: hier mit Satz abweisen")
        }
        XCTAssertTrue(antwort.fehler)
        XCTAssertTrue(antwort.text.contains("gehört zur Mappe «Haus», offen ist «Hof»"), antwort.text)
        XCTAssertTrue(antwort.text.contains("nichts wurde geändert"))
        XCTAssertTrue(meldung?.contains("anderen Mappe") == true)
        XCTAssertTrue(ablage.kennungen.isEmpty)
    }

    func testGraphGeaendertAnwendenWeistMitDemSatzDesProbelaufsAb() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        ablage.seiteWeg()
        let unpassend = ablage.nimmWiedergabe(try json(
            #"[{"kennung":"K-3","liegt":false,"text":"FEHLER: Node «n1» existiert nicht — nichts wurde vorgeschlagen."}]"#))
        XCTAssertEqual(unpassend, ["K-3"])
        XCTAssertEqual(ablage.eintrag("K-3")?.passtNicht, "Node «n1» existiert nicht")
        XCTAssertNil(ablage.uebergabeText(a), "nicht noch einmal zurueckgeben")
        guard case .hier(let antwort, _) = ablage.entscheide("K-3", ja: true, mappe: a, seiteOffen: true) else {
            return XCTFail("passt nicht mehr: hier mit Satz abweisen")
        }
        XCTAssertEqual(antwort, Kibruecke.verworfen("Der Vorschlag passt nicht mehr zum Graph (Node «n1» existiert nicht)"))
    }

    func testUnpassendeKarteLaesstSichAblehnen() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        ablage.seiteWeg()
        ablage.nimmWiedergabe(try json(#"[{"kennung":"K-3","liegt":false,"text":"FEHLER: x"}]"#))
        XCTAssertEqual(ablage.entscheide("K-3", ja: false, mappe: a, seiteOffen: true),
                       .hier(antwort: Kartenablage.abgelehnt, meldung: nil))
    }

    func testDieSeiteEntscheidetWasSieKennt() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        XCTAssertEqual(ablage.entscheide("K-3", ja: false, mappe: a, seiteOffen: true), .anDieSeite)
        XCTAssertEqual(ablage.entscheide("K-9", ja: true, mappe: a, seiteOffen: true), .unbekannt)
        XCTAssertNotNil(ablage.entferne("K-3"))
        XCTAssertNil(ablage.entferne("K-3"))
    }

    func testDieMappeKommtAusDemOrdner() {
        XCTAssertEqual(Kartenmappe.aus(ordner: nil), .amHeimPC)
        let m = Kartenmappe.aus(ordner: URL(fileURLWithPath: "/tmp/Probe.mappe", isDirectory: true))
        XCTAssertEqual(m.name, "Probe")
        XCTAssertNotEqual(m, .amHeimPC)
        XCTAssertEqual(m, Kartenmappe.aus(ordner: URL(fileURLWithPath: "/tmp/./Probe.mappe", isDirectory: true)))
    }
}
