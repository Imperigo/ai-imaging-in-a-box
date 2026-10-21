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
/// Mappe und Graph; sie bleiben, bis sie abgelehnt, angewendet oder beim echten Beenden (App zu,
/// «Claude über MCP» aus) mit Satz verworfen werden. Bei Leitungsverlust bleiben sie mit Vermerk.
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

    private func ruf(_ k: Mcpkern, id: Int = 1) async throws -> JSONWert? {
        await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":\#(id),"method":"tools/call","params":{"name":"vis_nodeParametrieren","arguments":{}}}"#))
    }

    private func nachfrage(_ k: Mcpkern, _ kennung: String) async throws -> String {
        let r = await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"\#(Mcpkern.nachfrageName)","arguments":{"kennung":"\#(kennung)"}}}"#))
        return r?["result"]?["content"]?.alsListe?.first?["text"]?.alsText ?? ""
    }

    func testKeineFrist() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte(), mappe: a, jetzt: t0)
        // Eine Woche spaeter liegt sie noch: Es gibt keinen Ablauf mehr (Regel wie KosmoOrbit v0.1.10).
        ablage.seiteWeg()
        XCTAssertEqual(ablage.kennungen, ["K-3"])
        XCTAssertNotNil(ablage.uebergabeText(a))
    }

    func testAnschlussAusVerwirftClaudesKartenMitSatz() async throws {
        let kern = Mcpkern(traeger: Kartentraeger(), fassung: "9.9.9", wartefrist: 5)
        let aufruf = Task { try await self.ruf(kern) }
        for _ in 0..<100 {
            if await kern.offeneVorschlaege().first?.karte != nil { break }
            try await Task.sleep(nanoseconds: 10_000_000)
        }
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        ablage.lege(try karte("A-1", urheber: "assistent"), mappe: a, jetzt: t0)
        let antworten = ablage.beende(.anschlussAus)
        XCTAssertEqual(antworten.map(\.kennung), ["K-1"], "nur Claudes Karten")
        XCTAssertEqual(ablage.kennungen, ["A-1"], "die des Assistenten bleiben")
        XCTAssertTrue(antworten[0].inDerSeite, "die App raeumt sie auch in der Seite ab")
        for x in antworten { await kern.entscheide(x.kennung, x.antwort) }
        let wert = try await aufruf.value
        let satz = wert?["result"]?["content"]?.alsListe?.first?["text"]?.alsText ?? ""
        XCTAssertTrue(satz.hasPrefix("VERWORFEN: Der Architekt hat «Claude über MCP» ausgeschaltet"), satz)
        XCTAssertTrue(satz.contains("nichts wurde geändert"), satz)
        let meldung = try XCTUnwrap(Kartenablage.beendetMeldung(antworten, .anschlussAus))
        XCTAssertTrue(meldung.contains("K-1 verworfen"), meldung)
    }

    func testAppZuVerwirftAlleKarten() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        ablage.lege(try karte("A-1", urheber: "assistent"), mappe: a, jetzt: t0)
        let antworten = ablage.beende(.appZu)
        XCTAssertEqual(antworten.map(\.kennung), ["K-1", "A-1"])
        XCTAssertTrue(antworten[0].antwort.text.contains("\(Marke.name) wurde beendet"))
        XCTAssertTrue(ablage.kennungen.isEmpty)
        XCTAssertNil(Kartenablage.beendetMeldung([], .appZu))
    }

    func testLeitungWegKarteBleibtMitVermerkUndEntscheidWirdZurueckgehalten() throws {
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        ablage.lege(try karte("A-1", urheber: "assistent"), mappe: a, jetzt: t0)
        XCTAssertNil(ablage.vermerk("K-1"))
        ablage.leitungWeg()
        XCTAssertEqual(ablage.kennungen, ["K-1", "A-1"], "Leitungsverlust ist kein Beenden")
        XCTAssertEqual(ablage.vermerk("K-1"), Kartenablage.leitungUnterbrochen)
        XCTAssertNil(ablage.vermerk("A-1"), "der Assistent geht nicht ueber MCP")
        guard case .hier(let antwort, _) = ablage.entscheide("K-1", ja: false, mappe: a, seiteOffen: false) else {
            return XCTFail("Ablehnen geht auch ohne Leitung")
        }
        XCTAssertFalse(ablage.anClaude("K-1", antwort), "zurueckgehalten bis zur Leitung")
        XCTAssertEqual(ablage.zurueckgehalten.map(\.kennung), ["K-1"])
    }

    func testWiederverbindenMeldetNeuUndErstDanachDenEntscheid() async throws {
        let kern = Mcpkern(traeger: Kartentraeger(), fassung: "9.9.9", wartefrist: 0.05)
        _ = try await ruf(kern, id: 1)
        _ = try await ruf(kern, id: 2)
        var ablage = Kartenablage()
        ablage.lege(try karte("K-1"), mappe: a, jetzt: t0)
        ablage.lege(try karte("K-2"), mappe: a, jetzt: t0)
        ablage.leitungWeg()
        _ = ablage.entscheide("K-1", ja: false, mappe: a, seiteOffen: false)
        XCTAssertFalse(ablage.anClaude("K-1", Kartenablage.abgelehnt))
        // Noch nichts bei Claude: K-1 wartet.
        let vorher = try await nachfrage(kern, "K-1")
        XCTAssertTrue(vorher.hasPrefix("Wartet noch"), vorher)
        let (neu, antworten) = ablage.leitungWieder()
        XCTAssertTrue(ablage.leitungSteht)
        XCTAssertEqual(neu.map(\.kennung), ["K-2"], "die offene Karte wird neu angemeldet")
        XCTAssertEqual(antworten.map(\.kennung), ["K-1"])
        await kern.meldeNeu(neu)
        let offen = await kern.offeneVorschlaege()
        XCTAssertEqual(offen.first { $0.kennung == "K-2" }?.karte, "Node-Parameter (stimmung)")
        for x in antworten { await kern.entscheide(x.kennung, x.antwort) }
        let eins = try await nachfrage(kern, "K-1")
        let zwei = try await nachfrage(kern, "K-2")
        XCTAssertTrue(eins.hasPrefix("ABGELEHNT"), eins)
        XCTAssertTrue(zwei.hasPrefix("Wartet noch"), "K-2 bleibt offen")
        XCTAssertNil(ablage.vermerk("K-2"))
        // Eine schon erledigte Kennung wird durch das Neuanmelden nicht wieder offen.
        await kern.meldeNeu([(kennung: "K-1", zusammenfassung: "x")])
        let danach = await kern.offeneVorschlaege()
        XCTAssertNil(danach.first { $0.kennung == "K-1" })
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
