import XCTest
@testable import VisboxKern

/// Fassungswache des stdio-Wegs (Mac-Probe 0.3.67): alte Claude-Verbindung, neue App → eine Warnzeile.
final class McpfassungswacheTests: XCTestCase {
    func testGleicheOderUnbekannteFassungWarntNicht() {
        XCTAssertNil(Mcpfassungswache.warnung(bruecke: "0.3.68", app: "0.3.68"))
        XCTAssertNil(Mcpfassungswache.warnung(bruecke: "0.3.68", app: nil))
        XCTAssertEqual(Mcpfassungswache.warnung(bruecke: "0.3.67", app: "0.3.68"),
                       "Claude-Verbindung läuft mit 0.3.67, App ist 0.3.68 — Claude neu starten.")
    }

    func testDieAppNenntIhreFassungImKopf() {
        let antwort = Mcpfassungswache.mitFassung(.json(.objekt(["jsonrpc": .text("2.0")])), "0.3.68")
        XCTAssertEqual(Mcpfassungswache.appFassung(ausAntwort: antwort.bytes()), "0.3.68")
    }

    func testOhneKopfAusDerStatuszeile() {
        let rumpf = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            + #"{"result":{"content":[{"type":"text","text":"bereit.\n"# + Mcpkern.fassungsSatz("0.3.66") + #""}]}}"#
        XCTAssertEqual(Mcpfassungswache.appFassung(ausAntwort: Data(rumpf.utf8)), "0.3.66")
    }

    func testDieWarnungStehtVorDemErstenText() throws {
        let zeile = #"{"jsonrpc":"2.0","id":4,"result":{"content":[{"type":"text","text":"App ist bereit."}]}}"#
        let mit = Mcpfassungswache.zeile(zeile, warnung: "Claude neu starten.")
        let wert = try JSONWert.lies(Data(mit.utf8))
        XCTAssertEqual(wert["result"]?["content"]?.alsListe?.first?["text"]?.alsText,
                       "⚠ Claude neu starten.\nApp ist bereit.")
        XCTAssertEqual(Mcpfassungswache.zeile(zeile, warnung: nil), zeile)
        let liste = #"{"jsonrpc":"2.0","id":1,"result":{"tools":[]}}"#
        XCTAssertEqual(Mcpfassungswache.zeile(liste, warnung: "x"), liste)
    }
}
