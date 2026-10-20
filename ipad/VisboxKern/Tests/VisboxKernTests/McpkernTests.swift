import Foundation
import XCTest
import VisboxKern

/// Ein Traeger fuer die Proben: ein Werkzeug, das sofort liest, eines, das eine Karte legt,
/// und eines, das laenger braucht als die Frist.
private struct Probetraeger: Werkzeugtraeger {
    var modus: Selbstaendigkeit = .karte
    var zusaetzlich: [Mcpwerkzeug] = []

    func werkzeuge() async -> [Mcpwerkzeug] {
        [Mcpwerkzeug(name: "graph_lesen", beschreibung: "liest", art: .lesen),
         Mcpwerkzeug(name: "knoten_setzen", beschreibung: "setzt", art: .aendern),
         Mcpwerkzeug(name: "langsam", beschreibung: "braucht lange", art: .lesen)]
            + zusaetzlich
    }

    func lage() async -> Mcplage {
        Mcplage(bereit: true, mappe: "Probe", modus: modus)
    }

    func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort {
        switch aufruf.werkzeug {
        case "graph_lesen":
            let wert = aufruf.argumente["tiefe"]?.alsGanz.map(String.init) ?? "-"
            return .ergebnis(Mcpergebnis(text: "Graph \(aufruf.kennung) tiefe=\(wert)"))
        case "knoten_setzen":
            return .karte("Knoten «Render» setzen")
        default:
            try? await Task.sleep(nanoseconds: 400_000_000)
            return .ergebnis(Mcpergebnis(text: "spät"))
        }
    }
}

final class McpkernTests: XCTestCase {

    private func kern(_ t: Werkzeugtraeger = Probetraeger(), frist: TimeInterval = 0.3) -> Mcpkern {
        Mcpkern(traeger: t, fassung: "9.9.9", wartefrist: frist)
    }

    private func json(_ text: String) throws -> JSONWert {
        try JSONWert.lies(Data(text.utf8))
    }

    private func rufe(_ k: Mcpkern, _ name: String, _ argumente: String = "{}",
                      id: Int = 7) async throws -> JSONWert {
        let a = await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":\#(id),"method":"tools/call","params":{"name":"\#(name)","arguments":\#(argumente)}}"#))
        let antwort = try XCTUnwrap(a)
        XCTAssertEqual(antwort["id"], .ganz(id))
        return try XCTUnwrap(antwort["result"])
    }

    private func text(_ ergebnis: JSONWert) -> String {
        ergebnis["content"]?.alsListe?.first?["text"]?.alsText ?? ""
    }

    // ------------------------------------------------------------- Handschlag

    func testInitializeNimmtDieGewuenschteFassung() async throws {
        let k = kern()
        for fassung in Mcp.protokolle {
            let a = await k.verarbeite(try json(
                #"{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"\#(fassung)","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}"#))
            XCTAssertEqual(a?["result"]?["protocolVersion"]?.alsText, fassung)
        }
    }

    func testInitializeSchlaegtBeiUnbekannterFassungDieNeuesteVor() async throws {
        let a = await kern().verarbeite(try json(
            #"{"jsonrpc":"2.0","id":"a","method":"initialize","params":{"protocolVersion":"1999-01-01"}}"#))
        let r = try XCTUnwrap(a?["result"])
        XCTAssertEqual(a?["id"], .text("a"), "eine Text-Kennung kommt als Text zurück")
        XCTAssertEqual(r["protocolVersion"]?.alsText, "2025-06-18")
        XCTAssertEqual(r["serverInfo"]?["name"]?.alsText, Marke.name.lowercased())
        XCTAssertEqual(r["serverInfo"]?["version"]?.alsText, "9.9.9")
        XCTAssertEqual(r["capabilities"]?["tools"]?["listChanged"], .wahrheit(false),
                       "ohne Ereignisstrom keine Meldung «Liste geändert»")
        XCTAssertEqual(Mcpkern.fassungFuer(nil), "2025-06-18")
    }

    func testDieAnleitungTraegtDieSpielregel() async throws {
        let a = await kern().verarbeite(try json(#"{"jsonrpc":"2.0","id":1,"method":"initialize"}"#))
        let anleitung = try XCTUnwrap(a?["result"]?["instructions"]?.alsText)
        XCTAssertEqual(anleitung, Mcp.anleitung)
        XCTAssertTrue(anleitung.contains(Mcpkern.statusName))
        XCTAssertTrue(anleitung.contains("Karte in der Assistent-Leiste"), "alles Ändernde wird Karte")
        XCTAssertTrue(anleitung.contains("Rendern gibt immer ein Mensch frei"))
        XCTAssertTrue(anleitung.contains("Löschen geht nur über eine Karte"))
        XCTAssertTrue(anleitung.contains("wiederhole den Aufruf nicht"))
    }

    func testPingUndMeldungen() async throws {
        let k = kern()
        let ping = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":3,"method":"ping"}"#))
        XCTAssertEqual(ping, .objekt(["jsonrpc": .text("2.0"), "id": .ganz(3), "result": .objekt([:])]))
        let initialisiert = await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","method":"notifications/initialized"}"#))
        XCTAssertNil(initialisiert, "eine Meldung bekommt keine Antwort")
        let abgebrochen = await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":3}}"#))
        XCTAssertNil(abgebrochen)
        let antwortDesProgramms = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":9,"result":{}}"#))
        XCTAssertNil(antwortDesProgramms, "eine Antwort des Programms bekommt keine Antwort")
    }

    func testUnbekannteMethodeUndUngueltigeAnfragen() async throws {
        let k = kern()
        let unbekannt = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":4,"method":"resources/list"}"#))
        XCTAssertEqual(unbekannt?["error"]?["code"], .ganz(-32601))
        XCTAssertEqual(unbekannt?["id"], .ganz(4))
        let keinObjekt = await k.verarbeite(.text("hallo"))
        XCTAssertEqual(keinObjekt?["error"]?["code"], .ganz(-32600))
        XCTAssertEqual(keinObjekt?["id"], .null)
        let wahrheitAlsId = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":true,"method":"ping"}"#))
        XCTAssertEqual(wahrheitAlsId?["error"]?["code"], .ganz(-32600))
        let ohneMethode = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":5}"#))
        XCTAssertEqual(ohneMethode?["error"]?["code"], .ganz(-32600))
        let unbekannteMeldung = await k.verarbeite(try json(#"{"jsonrpc":"2.0","method":"etwas"}"#))
        XCTAssertNil(unbekannteMeldung)
    }

    func testEinBuendelBekommtEinBuendelOhneDieMeldungen() async throws {
        let a = await kern().verarbeite(try json(
            #"[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","method":"notifications/initialized"},{"jsonrpc":"2.0","id":2,"method":"ping"}]"#))
        XCTAssertEqual(a?.alsListe?.map { $0["id"] }, [.ganz(1), .ganz(2)])
        let leer = await kern().verarbeite(.liste([]))
        XCTAssertEqual(leer?["error"]?["code"], .ganz(-32600))
        let nurMeldungen = await kern().verarbeite(try json(
            #"[{"jsonrpc":"2.0","method":"notifications/initialized"}]"#))
        XCTAssertNil(nurMeldungen)
    }

    // ------------------------------------------------------------- die Liste

    func testDieListeBeginntMitDenZweiDesKerns() async throws {
        let doppelt = Mcpwerkzeug(name: Mcpkern.statusName, beschreibung: "falsch", art: .aendern)
        let ungueltig = Mcpwerkzeug(name: "mit leerzeichen", beschreibung: "", art: .lesen)
        let k = kern(Probetraeger(zusaetzlich: [doppelt, ungueltig,
                                                Mcpwerkzeug(name: "graph_lesen", beschreibung: "2", art: .lesen),
                                                Mcpwerkzeug(name: "knoten_loeschen", beschreibung: "weg", art: .loeschen)]))
        let a = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":1,"method":"tools/list"}"#))
        let werkzeuge = try XCTUnwrap(a?["result"]?["tools"]?.alsListe)
        XCTAssertEqual(werkzeuge.compactMap { $0["name"]?.alsText },
                       [Mcpkern.statusName, Mcpkern.nachfrageName, "graph_lesen", "knoten_setzen",
                        "langsam", "knoten_loeschen"],
                       "ohne Doppel, ohne ungültigen Namen, die zwei des Kerns vorn")
        XCTAssertEqual(werkzeuge[0]["description"]?.alsText, Mcpkern.statusWerkzeug.beschreibung)
        XCTAssertEqual(werkzeuge[0]["inputSchema"]?["type"], .text("object"))
        XCTAssertEqual(werkzeuge[1]["inputSchema"]?["required"], .liste([.text("kennung")]))
        XCTAssertEqual(werkzeuge[0]["annotations"]?["readOnlyHint"], .wahrheit(true))
        XCTAssertEqual(werkzeuge[3]["annotations"]?["readOnlyHint"], .wahrheit(false))
        XCTAssertEqual(werkzeuge[5]["annotations"]?["destructiveHint"], .wahrheit(true))
    }

    func testGueltigeNamen() {
        XCTAssertTrue(Mcpwerkzeug.nameIstGueltig("vis_node-Setzen2"))
        XCTAssertFalse(Mcpwerkzeug.nameIstGueltig(""))
        XCTAssertFalse(Mcpwerkzeug.nameIstGueltig("a.b"))
        XCTAssertFalse(Mcpwerkzeug.nameIstGueltig("ä"))
        XCTAssertFalse(Mcpwerkzeug.nameIstGueltig(String(repeating: "a", count: 65)))
    }

    // ------------------------------------------------------------- Aufrufe

    func testEinLesendesWerkzeugAntwortetSofortMitDenArgumenten() async throws {
        let r = try await rufe(kern(), "graph_lesen", #"{"tiefe":2}"#)
        XCTAssertEqual(text(r), "Graph K-1 tiefe=2")
        XCTAssertNil(r["isError"])
    }

    func testFehlendeArgumenteWerdenEinLeeresObjekt() async throws {
        let a = await kern().verarbeite(try json(
            #"{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"graph_lesen"}}"#))
        XCTAssertEqual(text(try XCTUnwrap(a?["result"])), "Graph K-1 tiefe=-")
    }

    func testFalscheParameterSindEinProtokollfehler() async throws {
        let k = kern()
        let ohneName = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{}}"#))
        XCTAssertEqual(ohneName?["error"]?["code"], .ganz(-32602))
        let liste = await k.verarbeite(try json(
            #"{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"graph_lesen","arguments":[1]}}"#))
        XCTAssertEqual(liste?["error"]?["code"], .ganz(-32602))
    }

    func testEineKarteWartetUndSagtWoSieLiegt() async throws {
        let k = kern()
        let r = try await rufe(k, "knoten_setzen")
        let t = text(r)
        XCTAssertTrue(t.hasPrefix("Wartet noch — Vorschlag K-1 liegt in der Assistent-Leiste"), t)
        XCTAssertTrue(t.contains("Knoten «Render» setzen"))
        XCTAssertTrue(t.contains(Mcpkern.nachfrageName))
        XCTAssertNil(r["isError"], "warten ist kein Fehlschlag")
        let offen = await k.offeneVorschlaege()
        XCTAssertEqual(offen.map(\.kennung), ["K-1"])
        XCTAssertEqual(offen.first?.karte, "Knoten «Render» setzen")

        // DER STATUS NENNT DIE KARTE …
        let status = text(try await rufe(k, Mcpkern.statusName))
        XCTAssertTrue(status.contains("Offene Vorschläge: 1"), status)
        XCTAssertTrue(status.contains("K-1 «Knoten «Render» setzen»"), status)

        // … UND NACH «ANWENDEN» HOLT CLAUDE DAS ERGEBNIS.
        await k.entscheide("K-1", Mcpergebnis(text: "angewendet"))
        let nachher = try await rufe(k, Mcpkern.nachfrageName, #"{"kennung":"K-1"}"#)
        XCTAssertEqual(text(nachher), "angewendet")
        let leer = await k.offeneVorschlaege()
        XCTAssertTrue(leer.isEmpty)
    }

    func testEinEntscheidInnerhalbDerFristKommtDirektZurueck() async throws {
        let k = kern(frist: 5)
        async let antwort = rufe(k, "knoten_setzen")
        // WARTEN, BIS DIE KARTE LIEGT — dann «Anwenden».
        for _ in 0..<200 {
            if await k.offeneVorschlaege().first?.karte != nil { break }
            try await Task.sleep(nanoseconds: 5_000_000)
        }
        await k.entscheide("K-1", Mcpergebnis(text: "abgelehnt vom Architekten", fehler: true))
        let r = try await antwort
        XCTAssertEqual(text(r), "abgelehnt vom Architekten")
        XCTAssertEqual(r["isError"], .wahrheit(true))
    }

    func testDieNachfrageWartetAufDenEntscheid() async throws {
        let k = kern(frist: 0.3)
        _ = try await rufe(k, "knoten_setzen")
        // OHNE ENTSCHEID: nach der Frist wieder «wartet noch» …
        let ohne = try await rufe(k, Mcpkern.nachfrageName, #"{"kennung":"K-1"}"#)
        XCTAssertTrue(text(ohne).hasPrefix("Wartet noch — Vorschlag K-1"), text(ohne))
        // … MIT ENTSCHEID WAEHREND DES WARTENS: das Ergebnis, ohne die Frist abzuwarten.
        async let nachfrage = rufe(k, Mcpkern.nachfrageName, #"{"kennung":"K-1"}"#)
        try await Task.sleep(nanoseconds: 50_000_000)
        await k.entscheide("K-1", Mcpergebnis(text: "angewendet"))
        let r = try await nachfrage
        XCTAssertEqual(text(r), "angewendet")
    }

    func testEinLangsamerTraegerBekommtWartetNochUndDasErgebnisSpaeter() async throws {
        let k = kern(frist: 0.05)
        let r = try await rufe(k, "langsam")
        XCTAssertEqual(text(r), Mcpkern.wartetNoch("K-1", karte: nil))
        XCTAssertTrue(text(r).contains("noch nicht beantwortet"))
        try await Task.sleep(nanoseconds: 600_000_000)
        let spaeter = try await rufe(k, Mcpkern.nachfrageName, #"{"kennung":"K-1"}"#)
        XCTAssertEqual(text(spaeter), "spät")
    }

    func testEineUnbekannteKennung() async throws {
        let r = try await rufe(kern(), Mcpkern.nachfrageName, #"{"kennung":"K-99"}"#)
        XCTAssertEqual(r["isError"], .wahrheit(true))
        XCTAssertTrue(text(r).contains("K-99"))
    }

    func testEinEntscheidZaehltNurEinmal() async throws {
        let k = kern(frist: 0.05)
        _ = try await rufe(k, "knoten_setzen")
        await k.entscheide("K-1", Mcpergebnis(text: "erst"))
        await k.entscheide("K-1", Mcpergebnis(text: "zweit"))
        await k.entscheide("K-7", Mcpergebnis(text: "niemand"))
        let r = try await rufe(k, Mcpkern.nachfrageName, #"{"kennung":"K-1"}"#)
        XCTAssertEqual(text(r), "erst")
    }

    func testDieKennungenZaehlenHoch() async throws {
        let k = kern()
        let eins = text(try await rufe(k, "graph_lesen"))
        let zwei = text(try await rufe(k, "graph_lesen"))
        XCTAssertEqual(eins, "Graph K-1 tiefe=-")
        XCTAssertEqual(zwei, "Graph K-2 tiefe=-")
    }

    func testEinBildGehtAlsZweiterInhalt() {
        let e = Mcpergebnis(text: "Blick", bild: (daten: "iVBO", art: "image/png"))
        let inhalt = e.alsJSON["content"]?.alsListe
        XCTAssertEqual(inhalt?.count, 2)
        XCTAssertEqual(inhalt?[1]["type"], .text("image"))
        XCTAssertEqual(inhalt?[1]["mimeType"], .text("image/png"))
        XCTAssertNil(e.alsJSON["isError"])
    }

    // ------------------------------------------------------------- der Platzhalter

    func testDerPlatzhalterBeantwortetNurDenStatus() async throws {
        let k = kern(Mcpplatzhalter())
        let liste = await k.verarbeite(try json(#"{"jsonrpc":"2.0","id":1,"method":"tools/list"}"#))
        XCTAssertEqual(liste?["result"]?["tools"]?.alsListe?.compactMap { $0["name"]?.alsText },
                       [Mcpkern.statusName, Mcpkern.nachfrageName])
        let status = text(try await rufe(k, Mcpkern.statusName))
        XCTAssertTrue(status.contains("Stufe 3"), status)
        XCTAssertTrue(status.contains("Modus: Karte"), status)
        let anderes = try await rufe(k, "vis_render")
        XCTAssertEqual(anderes["isError"], .wahrheit(true))
        XCTAssertTrue(text(anderes).contains("«vis_render» kommt mit Stufe 3"), text(anderes))
        XCTAssertTrue(text(anderes).contains("nichts wurde ausgeführt"))
        let offen = await k.offeneVorschlaege()
        XCTAssertTrue(offen.isEmpty, "ein unbekanntes Werkzeug wird kein Vorschlag")
    }

    func testDerPlatzhalterOhneAppSagtWasZuTunIst() async throws {
        let k = kern(Mcpplatzhalter(ort: .ohneApp))
        let status = text(try await rufe(k, Mcpkern.statusName))
        let etwas = text(try await rufe(k, "etwas"))
        XCTAssertTrue(status.contains("\(Marke.name)-App öffnen"), status)
        XCTAssertTrue(etwas.hasPrefix("Nichts wurde ausgeführt."), etwas)
    }

    // ------------------------------------------------------------- die Regel

    func testDieFreigaberegel() {
        for modus in Selbstaendigkeit.allCases {
            XCTAssertFalse(Mcpfreigabe.brauchtKarte(.lesen, modus: modus), "Lesen nie")
            XCTAssertTrue(Mcpfreigabe.brauchtKarte(.loeschen, modus: modus), "106c: Löschen nur über Karte")
            XCTAssertTrue(Mcpfreigabe.brauchtKarte(.rendern, modus: modus), "106b: GPU immer ein Mensch")
        }
        XCTAssertTrue(Mcpfreigabe.brauchtKarte(.aendern, modus: .karte))
        XCTAssertFalse(Mcpfreigabe.brauchtKarte(.aendern, modus: .coop))
        XCTAssertFalse(Mcpfreigabe.brauchtKarte(.aendern, modus: .voll))
        XCTAssertEqual(Selbstaendigkeit.vorgabe, .karte, "106b: Karte ist die Vorgabe")
        XCTAssertTrue(Mcpfreigabe.satz(.voll).contains("Grafikkarte gibt immer ein Mensch frei"))
    }

    func testDerStatusNenntDenModus() async throws {
        let k = kern(Probetraeger(modus: .coop))
        let t = text(try await rufe(k, Mcpkern.statusName))
        XCTAssertTrue(t.hasPrefix("\(Marke.name) ist bereit. Mappe: «Probe». Werkzeuge: 5. Offene Vorschläge: 0."), t)
        XCTAssertTrue(t.contains("Modus: Coop"), t)
    }
}
