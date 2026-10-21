import Foundation
import XCTest
import VisboxKern

/// Stufen 5 und 6 der KI-Bedienung (Plan `docs/PLAN_KI_BEDIENUNG_2026-10-20.md`, 21.10.2026): der
/// Assistent mit derselben Werkzeugliste wie Claude, und Blick und Maus fuer beide.
final class KibedienenTests: XCTestCase {

    private func json(_ text: String) throws -> JSONWert {
        try JSONWert.lies(Data(text.utf8))
    }

    private let anmeldung = Anmeldung(benutzer: "probe", kennwort: "geheim-32-zeichen")

    private let liste = [
        Mcpwerkzeug(name: "graph_lesen", beschreibung: "liest", art: .lesen),
        Mcpwerkzeug(name: Kibedienen.mausName, beschreibung: "Maus", art: .bedienen),
    ]

    // ------------------------------------------------------------- Blick und Maus

    func testDieMausIstNieSelbstEineKarte() {
        for modus in Selbstaendigkeit.allCases {
            XCTAssertFalse(Mcpfreigabe.brauchtKarte(.bedienen, modus: modus), modus.rawValue)
            // Was sie ausloest, bleibt nach der Regel: Loeschen und Rendern immer Karte.
            XCTAssertTrue(Mcpfreigabe.brauchtKarte(.loeschen, modus: modus))
            XCTAssertTrue(Mcpfreigabe.brauchtKarte(.rendern, modus: modus))
        }
        let w = Mcpwerkzeug(name: Kibedienen.mausName, beschreibung: "x", art: .bedienen).alsJSON
        XCTAssertEqual(w["annotations"]?["readOnlyHint"], .wahrheit(false))
        XCTAssertEqual(w["annotations"]?["destructiveHint"], .wahrheit(false))
    }

    func testDieListeDerSeiteTraegtBlickUndMaus() throws {
        let text = #"[{"name":"\#(Kibedienen.blickName)","description":"b","inputSchema":{"type":"object"},"art":"lesen"},"# +
            #"{"name":"\#(Kibedienen.mausName)","description":"m","inputSchema":{"type":"object","required":["aktion"]},"art":"bedienen"}]"#
        let w = Kibruecke.werkzeuge(aus: try json(text))
        XCTAssertEqual(w.map(\.art), [.lesen, .bedienen])
        XCTAssertEqual(Kibedienen.blickName, Mcp.servername + "_blick")
        XCTAssertTrue(Kibedienen.ist(Kibedienen.mausName))
        XCTAssertFalse(Kibedienen.ist("vis_render"))
    }

    func testDerRumpfWartetAufDieSeite() {
        XCTAssertEqual(Kibedienen.rumpf(Kibedienen.blickName),
                       "return \(Kibruecke.name).alsText(await \(Kibruecke.name).blick(urheber, JSON.parse(argumente)));")
        XCTAssertNotNil(Kibedienen.rumpf(Kibedienen.mausName))
        XCTAssertNil(Kibedienen.rumpf("vis_render"))
    }

    func testDieAntwortMitUndOhneBild() throws {
        let ohne = Kibedienen.ergebnis(aus: try json(#"{"ok":false,"text":"VERWEIGERT: Rechenfreigaben …"}"#))
        XCTAssertTrue(ohne.fehler)
        XCTAssertNil(ohne.bild)
        let mit = Kibedienen.ergebnis(aus: try json(#"{"ok":true,"text":"BEREICH: Knotenansicht","bild":{"data":"QUJD","mimeType":"image/jpeg"}}"#))
        XCTAssertEqual(mit.bild?.art, "image/jpeg")
        XCTAssertFalse(mit.fehler)
        let fremd = Kibedienen.ergebnis(aus: try json(#"{"ok":true,"text":"t","bild":{"data":"QUJD","mimeType":"image/svg+xml"}}"#))
        XCTAssertNil(fremd.bild)
        XCTAssertTrue(fremd.text.contains("nicht mitgeschickt"))
        let gross = String(repeating: "A", count: (Macwerkzeuge.bildHoechstens / 3 + 10) * 4)
        let zuGross = Kibedienen.ergebnis(aus: .objekt(["ok": .wahrheit(true), "text": .text("t"),
                                                        "bild": .objekt(["data": .text(gross), "mimeType": .text("image/png")])]))
        XCTAssertNil(zuGross.bild)
        XCTAssertEqual(Kibedienen.ergebnis(aus: .null), Mcpergebnis(text: Kibruecke.unlesbar, fehler: true))
    }

    func testDerRufNenntDenUrheber() throws {
        let a = Mcpaufruf(kennung: "A-3", werkzeug: "vis_nodeSetzen", argumente: ["typ": .text("stimmung")])
        let ruf = try json(XCTUnwrap(Kibruecke.ruf(a, urheber: .assistent)))
        XCTAssertEqual(ruf["urheber"], .text("assistent"))
        XCTAssertEqual(ruf["kennung"], .text("A-3"))
        XCTAssertEqual(try json(XCTUnwrap(Kibruecke.ruf(a, urheber: .claude)))["urheber"], .text("claude"))
    }

    func testDieWorteImStrom() {
        XCTAssertEqual(Kiworte.tut(Kibedienen.blickName), "schaut in die Knotenansicht")
        XCTAssertEqual(Kiworte.tut(Kibedienen.mausName), "bedient die Knotenansicht")
    }

    // ------------------------------------------------------------- der Assistent mit Werkzeugen

    func testEineKarteHeisstFuerDasModellVorschlag() {
        let karte = Assistentenschrittergebnis.text(.karte("Knoten «Abend» löschen"), kennung: "A-4")
        XCTAssertTrue(karte.ok)
        XCTAssertTrue(karte.text.hasPrefix("VORSCHLAG A-4 liegt als Karte beim Architekten: Knoten «Abend» löschen."))
        let bild = Assistentenschrittergebnis.text(.ergebnis(Mcpergebnis(text: "Bild:", bild: (daten: "x", art: "image/png"))), kennung: "A-5")
        XCTAssertTrue(bild.text.contains("sieht nur Claude"))
        let fehler = Assistentenschrittergebnis.text(.ergebnis(Mcpergebnis(text: "FEHLER: x", fehler: true)), kennung: "A-6")
        XCTAssertFalse(fehler.ok)
    }

    func testDieAntwortMitOffenenSchritten() throws {
        let a = try Assistentenantwort.lies(status: 200, daten: Data(
            #"{"antwort":"Ich lese den Graph.","schritte_offen":[{"werkzeug":"graph_lesen","argumente":{}},{"werkzeug":"vis_nodeSetzen"}]}"#.utf8))
        XCTAssertEqual(a.schritte.map(\.werkzeug), ["graph_lesen", "vis_nodeSetzen"])
        XCTAssertEqual(a.schritte[1].argumente, [:])
        let alt = try Assistentenantwort.lies(status: 200, daten: Data(#"{"antwort":"Hallo"}"#.utf8))
        XCTAssertTrue(alt.schritte.isEmpty)
    }

    func testDasGespraechMitWerkzeugschritten() throws {
        var g = Assistentengespraech()
        let bitte = try XCTUnwrap(g.sende("Leg eine Abendstimmung an.", werkzeuge: liste))
        XCTAssertEqual(bitte.werkzeuge, liste)
        XCTAssertTrue(bitte.schritte.isEmpty)
        // Der Heim-PC nennt zwei Schritte: die Frage bleibt unterwegs, nichts im Verlauf.
        g.empfange(Assistentenantwort(antwort: "Ich sehe zuerst nach.", vorschlag: nil, schritte: [
            Assistentenaufruf(werkzeug: "graph_lesen", argumente: [:]),
            Assistentenaufruf(werkzeug: Kibedienen.mausName, argumente: ["aktion": .text("klick")]),
        ]))
        XCTAssertTrue(g.wartet)
        XCTAssertTrue(g.beitraege.isEmpty)
        XCTAssertEqual(g.hinweis, "Ich sehe zuerst nach.")
        XCTAssertNil(g.sende("noch eine Frage"), "solange er arbeitet, geht keine zweite hinaus")
        let erster = try XCTUnwrap(g.naechsterSchritt())
        XCTAssertEqual(erster.kennung, "A-1")
        XCTAssertNil(g.schrittErledigt("{\"graphen\":[]}"), "erst wenn alle erledigt sind")
        let zweiter = try XCTUnwrap(g.naechsterSchritt())
        XCTAssertEqual(zweiter.kennung, "A-2")
        XCTAssertEqual(zweiter.aufruf.werkzeug, Kibedienen.mausName)
        let weiter = try XCTUnwrap(g.schrittErledigt("OK: geklickt"))
        XCTAssertEqual(weiter.nachricht, "Leg eine Abendstimmung an.")
        XCTAssertEqual(weiter.schritte.map(\.ergebnis), ["{\"graphen\":[]}", "OK: geklickt"])
        XCTAssertNil(g.naechsterSchritt())
        // Fertig: jetzt erst kommen Frage und Antwort in den Verlauf.
        g.empfange(Assistentenantwort(antwort: "Die Stimmung liegt als Karte A-2 bei dir.", vorschlag: nil))
        XCTAssertFalse(g.wartet)
        XCTAssertNil(g.lauf)
        XCTAssertEqual(g.beitraege.map(\.von), [.mensch, .assistent])
        // Die Kennungen zaehlen ueber das Gespraech weiter.
        _ = g.sende("Und noch eine.", werkzeuge: liste)
        g.empfange(Assistentenantwort(antwort: "", vorschlag: nil, schritte: [Assistentenaufruf(werkzeug: "graph_lesen", argumente: [:])]))
        XCTAssertEqual(g.naechsterSchritt()?.kennung, "A-3")
        XCTAssertNil(g.hinweis, "ein leerer Zwischensatz steht nicht da")
    }

    func testScheitertEinSchrittWegIstDieFrageNichtVerloren() throws {
        var g = Assistentengespraech()
        _ = g.sende("Frage", werkzeuge: liste)
        g.empfange(Assistentenantwort(antwort: "", vorschlag: nil, schritte: [Assistentenaufruf(werkzeug: "graph_lesen", argumente: [:])]))
        XCTAssertEqual(g.scheitert("Der Heim-PC antwortet nicht."), "Frage")
        XCTAssertNil(g.lauf)
        XCTAssertFalse(g.wartet)
        XCTAssertTrue(g.beitraege.isEmpty)
    }

    func testOhneListeBleibtAllesWieBisher() throws {
        var g = Assistentengespraech()
        _ = g.sende("Frage")
        XCTAssertNil(g.lauf)
        // Ein Server, der trotzdem Schritte nennt, wird ohne Lauf nicht ausgefuehrt.
        g.empfange(Assistentenantwort(antwort: "Antwort", vorschlag: nil, schritte: [Assistentenaufruf(werkzeug: "x", argumente: [:])]))
        XCTAssertNil(g.naechsterSchritt())
        XCTAssertEqual(g.beitraege.count, 2)
    }

    func testDieAnfrageTraegtListeUndSchritteOhneArt() throws {
        let schritt = Assistentenschritt(aufruf: Assistentenaufruf(werkzeug: "graph_lesen", argumente: [:]), ergebnis: "{}")
        let a = try Anfragen.assistent(Assistentenbitte(nachricht: "x", verlauf: [], werkzeuge: liste, schritte: [schritt]),
                                       anmeldung: anmeldung)
        let rumpf = try XCTUnwrap(JSONWert.lies(XCTUnwrap(a.rumpf)).alsObjekt)
        let werkzeuge = try XCTUnwrap(rumpf["werkzeuge"]?.alsListe)
        XCTAssertEqual(werkzeuge.map { $0["name"]?.alsText }, ["graph_lesen", Kibedienen.mausName])
        XCTAssertNil(werkzeuge[0]["art"], "ob eine Karte noetig ist, entscheidet die App — nicht das Modell")
        XCTAssertNotNil(werkzeuge[0]["inputSchema"])
        XCTAssertEqual(rumpf["schritte"]?.alsListe?.first?["ergebnis"], .text("{}"))
        let ohne = try Anfragen.assistent(Assistentenbitte(nachricht: "x", verlauf: []), anmeldung: anmeldung)
        let o = try XCTUnwrap(JSONWert.lies(XCTUnwrap(ohne.rumpf)).alsObjekt)
        XCTAssertNil(o["werkzeuge"])
        XCTAssertNil(o["schritte"])
    }
}
