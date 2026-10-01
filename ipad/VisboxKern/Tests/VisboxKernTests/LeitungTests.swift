import Foundation
import XCTest
import VisboxKern

/// Die Leitung in Bytes: eine Anfrage lesen, eine Antwort schreiben (für den Mac als
/// Vermittler, Protokoll §8b).
final class LeitungTests: XCTestCase {

    private func lies(_ text: String, rumpf: Data = Data()) -> Lesestand {
        var leser = Anfrageleser()
        var d = Data(text.utf8)
        d.append(rumpf)
        return leser.nimm(d)
    }

    private func code(_ stand: Lesestand) -> Int? {
        if case .kaputt(let a) = stand { return a.status }
        return nil
    }

    // ------------------------------------------------------------------ lesen

    func testEineGetAnfrageInEinemStueck() throws {
        let stand = lies("GET /bild?name=a%2Bb.png HTTP/1.1\r\nHost: mac.invalid:8731\r\n"
                         + "Accept: application/json\r\nX-Leer:\r\n\r\n")
        guard case .fertig(let a) = stand else { return XCTFail("\(stand)") }
        XCTAssertEqual(a.kopf.methode, "GET")
        XCTAssertEqual(a.kopf.ziel, "/bild?name=a%2Bb.png")
        XCTAssertEqual(a.kopf.pfad, "/bild")
        XCTAssertEqual(a.kopf.fassung, "HTTP/1.1")
        XCTAssertEqual(a.kopf.koepfe.wert("accept"), "application/json", "Name ohne Gross/klein")
        XCTAssertEqual(a.kopf.koepfe.wert("X-Leer"), "")
        XCTAssertTrue(a.rumpf.isEmpty)
    }

    func testStueckFuerStueckIstDasselbeWieAufEinmal() {
        let rumpf = Data(#"{"pin":"042917"}"#.utf8)
        let roh = Data("POST /api/verbinden HTTP/1.1\r\nContent-Length: \(rumpf.count)\r\n\r\n".utf8)
            + rumpf
        var leser = Anfrageleser()
        var stand = Lesestand.mehr
        for (i, byte) in roh.enumerated() {
            stand = leser.nimm(Data([byte]))
            if i < roh.count - 1 { XCTAssertEqual(stand, .mehr, "bei Byte \(i)") }
        }
        guard case .fertig(let a) = stand else { return XCTFail("\(stand)") }
        XCTAssertEqual(a.rumpf, rumpf)
        XCTAssertEqual(a.kopf.methode, "POST")
    }

    func testUnvollstaendigHeisstMehrLesen() {
        XCTAssertEqual(lies("GET /api/fortschritt HTTP/1.1\r\nAccept: x\r\n"), .mehr)
        XCTAssertEqual(lies("POST /api/skizze HTTP/1.1\r\nContent-Length: 10\r\n\r\n",
                            rumpf: Data("12345".utf8)), .mehr, "Rumpf noch nicht ganz")
    }

    func testWasNachDemRumpfKommtWirdNichtGelesen() {
        let stand = lies("POST /api/rechne HTTP/1.1\r\nContent-Length: 2\r\n\r\n",
                         rumpf: Data("{}GET / HTTP/1.1\r\n\r\n".utf8))
        guard case .fertig(let a) = stand else { return XCTFail("\(stand)") }
        XCTAssertEqual(a.rumpf, Data("{}".utf8))
    }

    func testNachDemEndeAendertKeinStueckMehrEtwas() {
        var leser = Anfrageleser()
        let erst = leser.nimm(Data("GET / HTTP/1.1\r\n\r\n".utf8))
        XCTAssertEqual(leser.nimm(Data("Unfug\r\n\r\n".utf8)), erst)
        var kaputt = Anfrageleser()
        let k = kaputt.nimm(Data("Unfug\r\n\r\n".utf8))
        XCTAssertEqual(kaputt.nimm(Data("GET / HTTP/1.1\r\n\r\n".utf8)), k)
    }

    // ------------------------------------------------------------- kaputt → 400

    func testKaputteAnfragenWerdenAbgewiesen() {
        let faelle: [(String, Int)] = [
            ("GET /\r\n\r\n", 400),                                    // keine Fassung
            ("GET  / HTTP/1.1\r\n\r\n", 400),                          // doppelter Abstand
            ("get / HTTP/1.1\r\n\r\n", 400),                           // Art klein
            ("GET / HTTP/2.0\r\n\r\n", 505),
            ("GET http://anders.invalid/ HTTP/1.1\r\n\r\n", 400),      // ganze Adresse
            ("GET //anders.invalid/x HTTP/1.1\r\n\r\n", 400),          // anderer Rechner
            ("GET /a#b HTTP/1.1\r\n\r\n", 400),
            ("GET * HTTP/1.1\r\n\r\n", 400),
            ("GET / HTTP/1.1\r\nKeinDoppelpunkt\r\n\r\n", 400),
            ("GET / HTTP/1.1\r\nA: b\r\n fortgesetzt\r\n\r\n", 400),
            ("GET / HTTP/1.1\r\nName mit Leer: b\r\n\r\n", 400),
            ("POST / HTTP/1.1\r\nContent-Length: abc\r\n\r\n", 400),
            ("POST / HTTP/1.1\r\nContent-Length: -1\r\n\r\n", 400),
            ("POST / HTTP/1.1\r\nContent-Length: 2\r\nContent-Length: 3\r\n\r\n", 400),
            ("POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n", 411),
            ("POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\nContent-Length: 2\r\n\r\n", 400),
        ]
        for (text, erwartet) in faelle {
            XCTAssertEqual(code(lies(text)), erwartet, text.debugDescription)
        }
    }

    func testDieAbweisungIstEinSatzInDerFormDesServers() throws {
        guard case .kaputt(let a) = lies("GET / HTTP/2.0\r\n\r\n") else { return XCTFail() }
        let wert = try JSONWert.lies(a.rumpf)
        XCTAssertNotNil(wert["fehler"]?.alsText)
        XCTAssertEqual(a.koepfe.wert("Content-Type"), "application/json; charset=utf-8")
    }

    func testZweimalDieselbeLaengeIstEineLaenge() {
        let stand = lies("POST / HTTP/1.1\r\nContent-Length: 2\r\nContent-Length: 2\r\n\r\n{}")
        guard case .fertig = stand else { return XCTFail("\(stand)") }
    }

    // --------------------------------------------------------------- die Grenzen

    /// **Die Grenze trägt die grösste Anfrage der App:** eine Skizze von 2 MiB (der Riegel
    /// des Servers) als Base64 im JSON, samt den übrigen Feldern — gebaut von derselben
    /// Bauform, die die App benutzt.
    func testDieGrenzeFasstDieGroessteSkizzeDieDerServerNimmt() throws {
        var png = Data([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        png.append(Data(count: 2 * 1024 * 1024 - png.count))
        let anfrage = try Anfragen.skizze(
            png: png, ueber: String(repeating: "u", count: 200),
            bemerkung: String(repeating: "b", count: 2000), name: "n",
            ordner: String(repeating: "o", count: 500), schluessel: UUID().uuidString,
            anmeldung: Anmeldung(benutzer: "b", kennwort: "k"))
        let rumpf = try XCTUnwrap(anfrage.rumpf)
        XCTAssertGreaterThan(rumpf.count, 2 * 1024 * 1024 * 4 / 3, "Base64 macht sie grösser")
        XCTAssertLessThanOrEqual(rumpf.count, Anfrageleser.rumpfGrenze)
        let stand = lies("POST /api/skizze HTTP/1.1\r\nContent-Length: \(rumpf.count)\r\n\r\n",
                         rumpf: rumpf)
        guard case .fertig(let a) = stand else { return XCTFail("\(code(stand) ?? 0)") }
        XCTAssertEqual(a.rumpf.count, rumpf.count)
    }

    /// **Abgewiesen, bevor er ganz gelesen ist:** Schon der Kopf sagt, dass es zu viel wird
    /// — vom Rumpf ist noch kein Byte da.
    func testEinRumpfUeberDerGrenzeWirdAmKopfAbgewiesen() throws {
        var leser = Anfrageleser()
        let stand = leser.nimm(Data(("POST /api/skizze HTTP/1.1\r\nContent-Length: "
                                     + "\(Anfrageleser.rumpfGrenze + 1)\r\n\r\n").utf8))
        XCTAssertEqual(code(stand), 413)
        XCTAssertNil(leser.zwischenantwort(), "kein «weiter», wenn schon abgewiesen ist")
        XCTAssertEqual(code(lies("POST / HTTP/1.1\r\nContent-Length: "
                                 + "\(Anfrageleser.rumpfGrenze)\r\n\r\n")), nil,
                       "genau die Grenze ist erlaubt (dann: mehr lesen)")
    }

    func testEinKopfOhneEndeWirdNichtEndlosGesammelt() {
        var leser = Anfrageleser()
        var stand = leser.nimm(Data("GET / HTTP/1.1\r\n".utf8))
        let zeile = Data(("X-Lang: " + String(repeating: "a", count: 1000) + "\r\n").utf8)
        var runden = 0
        while stand == .mehr && runden < 100 {
            stand = leser.nimm(zeile)
            runden += 1
        }
        XCTAssertEqual(code(stand), 431)
        XCTAssertLessThan(runden, 40, "abgewiesen kurz nach der Grenze, nicht am Ende")
    }

    // ---------------------------------------------------------- 100 Continue

    func testWerFragtBevorErSchicktBekommtEinmalWeiter() {
        var leser = Anfrageleser()
        XCTAssertNil(leser.zwischenantwort(), "vor dem Kopf nicht")
        XCTAssertEqual(leser.nimm(Data(("POST /api/skizze HTTP/1.1\r\nExpect: 100-continue\r\n"
                                        + "Content-Length: 2\r\n\r\n").utf8)), .mehr)
        XCTAssertEqual(leser.zwischenantwort(), Data("HTTP/1.1 100 Continue\r\n\r\n".utf8))
        XCTAssertNil(leser.zwischenantwort(), "nur einmal")
        guard case .fertig = leser.nimm(Data("{}".utf8)) else { return XCTFail() }

        var ohne = Anfrageleser()
        _ = ohne.nimm(Data("POST / HTTP/1.1\r\nContent-Length: 2\r\n\r\n".utf8))
        XCTAssertNil(ohne.zwischenantwort(), "ungefragt nicht")
    }

    // ------------------------------------------------------------ schreiben

    func testDieAntwortSchliesstUndNenntIhreLaenge() {
        let a = Leitungsantwort(status: 200,
                                koepfe: [Kopfzeile("Content-Type", "image/png"),
                                         Kopfzeile("Content-Length", "999"),
                                         Kopfzeile("Connection", "keep-alive")],
                                rumpf: Data([1, 2, 3]))
        let text = String(decoding: a.bytes(), as: UTF8.self)
        XCTAssertTrue(text.hasPrefix("HTTP/1.1 200 OK\r\n"))
        XCTAssertTrue(text.contains("Content-Type: image/png\r\n"))
        XCTAssertTrue(text.contains("Content-Length: 3\r\n"), "die echte Länge, nicht die gegebene")
        XCTAssertFalse(text.contains("999"))
        XCTAssertFalse(text.contains("keep-alive"))
        XCTAssertTrue(text.contains("Connection: close\r\n\r\n"))
        XCTAssertEqual(Array(a.bytes().suffix(3)), [1, 2, 3])
    }

    func testDieGeschriebeneAntwortLiestDieAppWieDieDesServers() throws {
        let a = Leitungsantwort.fehler("Ein Satz.", status: 404)
        XCTAssertEqual(try Serverfehler.ausAntwort(a).satz, "Ein Satz.")
    }
}

private extension Serverfehler {
    /// Liest eine Leitungsantwort so, wie die App eine Antwort des Servers liest.
    static func ausAntwort(_ a: Leitungsantwort) throws -> Serverfehler {
        do {
            _ = try liesAntwort(status: a.status, daten: a.rumpf)
        } catch let f as Serverfehler {
            return f
        }
        throw NSError(domain: "kein Fehler", code: 0)
    }
}
