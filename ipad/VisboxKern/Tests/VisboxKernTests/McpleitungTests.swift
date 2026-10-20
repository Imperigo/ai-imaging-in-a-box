import Foundation
import XCTest
import VisboxKern

/// Die Leitung des MCP-Kerns: wer hinein darf, `POST /mcp`, und der Weg ueber stdio.
final class McpleitungTests: XCTestCase {

    private let kern = Mcpkern(traeger: Mcpplatzhalter(), fassung: "1.0.0", wartefrist: 0.05)

    private func anfrage(_ methode: String = "POST", pfad: String = "/mcp",
                         koepfe: [Kopfzeile] = [Kopfzeile("Host", "127.0.0.1:8631")],
                         rumpf: String = #"{"jsonrpc":"2.0","id":1,"method":"ping"}"#) -> RoheAnfrage {
        let d = Data(rumpf.utf8)
        return RoheAnfrage(kopf: Anfragekopf(methode: methode, ziel: pfad,
                                             koepfe: koepfe + [Kopfzeile("Content-Length", "\(d.count)")]),
                           rumpf: d)
    }

    private func antwort(_ a: RoheAnfrage) async -> Leitungsantwort {
        await Mcpleitung.antworte(auf: a, kern: kern)
    }

    // ------------------------------------------------------------- Zugang

    func testNurLokaleNamenMitDemRichtigenAnschluss() {
        XCTAssertTrue(Mcpzugang.hostErlaubt("127.0.0.1:8631"))
        XCTAssertTrue(Mcpzugang.hostErlaubt("localhost:8631"))
        XCTAssertTrue(Mcpzugang.hostErlaubt("LOCALHOST:8631"))
        XCTAssertFalse(Mcpzugang.hostErlaubt(nil))
        XCTAssertFalse(Mcpzugang.hostErlaubt("127.0.0.1"), "ohne Anschluss nicht")
        XCTAssertFalse(Mcpzugang.hostErlaubt("127.0.0.1:8630"), "der Anschluss von KosmoOrbit nicht")
        XCTAssertFalse(Mcpzugang.hostErlaubt("boese.example:8631"), "DNS-Rebinding")
        XCTAssertFalse(Mcpzugang.hostErlaubt("192.168.1.5:8631"))
        XCTAssertFalse(Mcpzugang.hostErlaubt("localhost.boese.example:8631"))
    }

    func testNurLokaleUrspruenge() {
        XCTAssertTrue(Mcpzugang.ursprungErlaubt(nil), "kein Browser")
        XCTAssertTrue(Mcpzugang.ursprungErlaubt(""))
        XCTAssertTrue(Mcpzugang.ursprungErlaubt("http://localhost"))
        XCTAssertTrue(Mcpzugang.ursprungErlaubt("http://localhost:6274"))
        XCTAssertTrue(Mcpzugang.ursprungErlaubt("http://127.0.0.1:5173"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("null"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("https://boese.example"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("http://localhost.boese.example"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("http://localhost:"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("http://localhost:80a"))
        XCTAssertFalse(Mcpzugang.ursprungErlaubt("http://127.0.0.1@boese.example"))
    }

    func testVermittlerspurenUndGegenstellen() {
        XCTAssertTrue(Mcpzugang.kamUeberVermittler([Kopfzeile("X-Forwarded-For", "203.0.113.4")]))
        XCTAssertTrue(Mcpzugang.kamUeberVermittler([Kopfzeile("Cf-Connecting-Ip", "x")]))
        XCTAssertTrue(Mcpzugang.kamUeberVermittler([Kopfzeile("Forwarded", "for=x")]))
        XCTAssertFalse(Mcpzugang.kamUeberVermittler([Kopfzeile("Host", "127.0.0.1:8631")]))
        for lokal in ["127.0.0.1", "127.1.2.3", "::1", "::ffff:127.0.0.1", "::1%lo0"] {
            XCTAssertTrue(Mcpzugang.gegenstelleIstLokal(lokal), lokal)
        }
        for fremd in ["192.168.1.2", "10.0.0.1", "fe80::1", "127.0.0", "127.0.0.256", "128.0.0.1"] {
            XCTAssertFalse(Mcpzugang.gegenstelleIstLokal(fremd), fremd)
        }
    }

    // ------------------------------------------------------------- POST /mcp

    func testEinPingGehtAlsJsonZurueck() async throws {
        let a = await antwort(anfrage())
        XCTAssertEqual(a.status, 200)
        XCTAssertEqual(a.koepfe.wert("Content-Type"), "application/json; charset=utf-8")
        XCTAssertEqual(try JSONWert.lies(a.rumpf)["result"], .objekt([:]))
        XCTAssertNil(a.koepfe.wert("Access-Control-Allow-Origin"), "ohne Origin kein CORS")
    }

    func testFremderHostOderUrsprungWirdAbgewiesen() async {
        let fremd = await antwort(anfrage(koepfe: [Kopfzeile("Host", "boese.example:8631")]))
        XCTAssertEqual(fremd.status, 403)
        XCTAssertEqual(String(data: fremd.rumpf, encoding: .utf8), "verweigert", "ohne Grund nach aussen")
        let ohne = await antwort(anfrage(koepfe: []))
        XCTAssertEqual(ohne.status, 403)
        let doppelt = await antwort(anfrage(koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                     Kopfzeile("Host", "boese.example:8631")]))
        XCTAssertEqual(doppelt.status, 403)
        let browser = await antwort(anfrage(koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                     Kopfzeile("Origin", "https://boese.example")]))
        XCTAssertEqual(browser.status, 403)
        let tunnel = await antwort(anfrage(koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                    Kopfzeile("X-Forwarded-For", "203.0.113.4")]))
        XCTAssertEqual(tunnel.status, 403, "106e: vorerst nur lokal")
    }

    func testEinLokalerBrowserBekommtCors() async {
        let koepfe = [Kopfzeile("Host", "localhost:8631"), Kopfzeile("Origin", "http://localhost:6274")]
        let vorab = await antwort(anfrage("OPTIONS", koepfe: koepfe, rumpf: ""))
        XCTAssertEqual(vorab.status, 204)
        XCTAssertEqual(vorab.koepfe.wert("Access-Control-Allow-Origin"), "http://localhost:6274")
        XCTAssertEqual(vorab.koepfe.wert("Access-Control-Allow-Methods"), "POST, OPTIONS")
        let post = await antwort(anfrage(koepfe: koepfe))
        XCTAssertEqual(post.status, 200)
        XCTAssertEqual(post.koepfe.wert("Vary"), "Origin")
    }

    func testGetUndDeleteSind405UndAnderePfade404() async {
        let get = await antwort(anfrage("GET", koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                       Kopfzeile("Accept", "text/event-stream")], rumpf: ""))
        XCTAssertEqual(get.status, 405, "kein Ereignisstrom: die Norm verlangt dann 405")
        XCTAssertEqual(get.koepfe.wert("Allow"), "POST, OPTIONS")
        let weg = await antwort(anfrage("DELETE", rumpf: ""))
        XCTAssertEqual(weg.status, 405)
        let anders = await antwort(anfrage(pfad: "/api/heim"))
        XCTAssertEqual(anders.status, 404)
        let mitFrage = await antwort(anfrage(pfad: "/mcp?x=1"))
        XCTAssertEqual(mitFrage.status, 200, "die Frage gehört nicht zum Pfad")
    }

    func testUnbekannteFassungImKopfUndKaputtesJson() async throws {
        let fassung = await antwort(anfrage(koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                     Kopfzeile("MCP-Protocol-Version", "2099-01-01")]))
        XCTAssertEqual(fassung.status, 400)
        XCTAssertEqual(try JSONWert.lies(fassung.rumpf)["error"]?["code"], .ganz(-32600))
        let bekannt = await antwort(anfrage(koepfe: [Kopfzeile("Host", "127.0.0.1:8631"),
                                                     Kopfzeile("MCP-Protocol-Version", "2025-06-18")]))
        XCTAssertEqual(bekannt.status, 200)
        let kaputt = await antwort(anfrage(rumpf: "{nicht json"))
        XCTAssertEqual(kaputt.status, 400)
        XCTAssertEqual(try JSONWert.lies(kaputt.rumpf)["error"]?["code"], .ganz(-32700))
    }

    func testEineMeldungBekommt202OhneRumpf() async {
        let a = await antwort(anfrage(rumpf: #"{"jsonrpc":"2.0","method":"notifications/initialized"}"#))
        XCTAssertEqual(a.status, 202)
        XCTAssertTrue(a.rumpf.isEmpty)
    }

    // ------------------------------------------------------------- der ganze Weg in Bytes

    func testDerGanzeWegVonDerZeileZurZeile() async throws {
        let zeile = #"{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"\#(Mcpkern.statusName)","arguments":{}}}"#
        var leser = Anfrageleser()
        guard case .fertig(let roh) = leser.nimm(Mcpweiterleitung.anfrage(zeile)) else {
            return XCTFail("der Anfrageleser liest, was die Weiterleitung schreibt")
        }
        XCTAssertEqual(roh.kopf.koepfe.wert("Host"), "127.0.0.1:8631")
        let a = await Mcpleitung.antworte(auf: roh, kern: kern)
        let zeilen = Mcpweiterleitung.zeilen(ausAntwort: a.bytes(), nachricht: zeile)
        XCTAssertEqual(zeilen.count, 1)
        XCTAssertFalse(zeilen[0].contains("\n"), "eine Nachricht, eine Zeile")
        let wert = try JSONWert.lies(Data(zeilen[0].utf8))
        XCTAssertEqual(wert["id"], .ganz(11))
        let text = wert["result"]?["content"]?.alsListe?.first?["text"]?.alsText ?? ""
        XCTAssertTrue(text.contains("Stufe 3"), text)
    }

    func testEine202WirdKeineZeile() {
        let a = Leitungsantwort(status: 202)
        XCTAssertEqual(Mcpweiterleitung.zeilen(ausAntwort: a.bytes(), nachricht: "{}"), [])
    }

    func testEineAbweisungWirdEinFehlerFuerDieAnfrage() throws {
        let zeile = #"{"jsonrpc":"2.0","id":"x","method":"ping"}"#
        let z = Mcpweiterleitung.zeilen(ausAntwort: Mcpleitung.verweigert.bytes(), nachricht: zeile)
        XCTAssertEqual(z.count, 1)
        let w = try JSONWert.lies(Data(z[0].utf8))
        XCTAssertEqual(w["id"], .text("x"))
        XCTAssertEqual(w["error"]?["code"], .ganz(-32603))
        XCTAssertTrue(w["error"]?["message"]?.alsText?.contains("HTTP 403") == true)
        let meldung = #"{"jsonrpc":"2.0","method":"notifications/initialized"}"#
        XCTAssertEqual(Mcpweiterleitung.fehlerzeilen(meldung, "weg"), [], "eine Meldung bekommt nie eine Antwort")
        let buendel = #"[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","id":2,"method":"ping"}]"#
        let b = try JSONWert.lies(Data(Mcpweiterleitung.fehlerzeilen(buendel, "weg")[0].utf8))
        XCTAssertEqual(b.alsListe?.map { $0["id"] }, [.ganz(1), .ganz(2)])
        let kaputt = try JSONWert.lies(Data(Mcpweiterleitung.fehlerzeilen("{nicht", "weg")[0].utf8))
        XCTAssertEqual(kaputt["error"]?["code"], .ganz(-32700))
    }

    func testEineUnlesbareOderAbgeschnitteneAntwort() {
        XCTAssertNil(Mcpweiterleitung.lies(Data("kein http".utf8)))
        XCTAssertNil(Mcpweiterleitung.lies(Data("HTTP/1.1 200 OK\r\nContent-Length: 10\r\n\r\nkurz".utf8)),
                     "abgeschnitten ist nicht gelesen")
        let ganz = Mcpweiterleitung.lies(Data("HTTP/1.1 200 OK\r\ncontent-length: 2\r\n\r\n{}zu viel".utf8))
        XCTAssertEqual(ganz?.status, 200)
        XCTAssertEqual(ganz?.rumpf, Data("{}".utf8))
        let z = Mcpweiterleitung.zeilen(ausAntwort: Data("Müll".utf8), nachricht: #"{"jsonrpc":"2.0","id":3,"method":"ping"}"#)
        XCTAssertTrue(z.first?.contains("nicht lesbar") == true)
    }

    // ------------------------------------------------------------- Zeilen von stdin

    func testZeilenUeberStueckgrenzen() {
        var z = Mcpzeilen()
        XCTAssertEqual(z.nimm(Data(#"{"a":"#.utf8)), [])
        XCTAssertEqual(z.nimm(Data("1}\r\n\n{\"b\"".utf8)), [#"{"a":1}"#], "\\r weg, leere Zeile weg")
        XCTAssertEqual(z.nimm(Data(":2}\n".utf8)), [#"{"b":2}"#])
        // UMLAUTE ÜBER DIE STÜCKGRENZE: ein Zeichen aus zwei Bytes, in zwei Stücken.
        let ae = Array("\"ä\"\n".utf8)
        XCTAssertEqual(z.nimm(Data(ae[0..<2])), [])
        XCTAssertEqual(z.nimm(Data(ae[2...])), ["\"ä\""])
    }

    func testEineZuLangeZeileWirdGanzVerworfen() {
        var z = Mcpzeilen()
        let lang = Data(repeating: 65, count: Mcpzeilen.grenze + 10)
        XCTAssertEqual(z.nimm(lang), [])
        XCTAssertEqual(z.nimm(Data("Rest\nok\n".utf8)), ["ok"], "der Rest der langen Zeile fällt mit")
        XCTAssertEqual(z.verworfen, 1)
    }
}
