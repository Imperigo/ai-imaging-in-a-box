import Foundation
import XCTest
import VisboxKern

/// Das dreiwertige Urteil — geprüft an der **Wirkung**: was aus dem JSON des Servers wird.
final class UrteilTests: XCTestCase {

    /// Ein Eintrag, wie er in `projekt.json` steht — das Urteil als Pflichtfeld.
    private struct Eintrag: Decodable {
        let geometrie_bestanden: Urteil
    }

    /// Dasselbe, aber so gelesen, wie die App es tun soll: fehlt das Feld, ist es nicht
    /// gemessen.
    private struct EintragOhnePflicht: Decodable {
        let urteil: Urteil
        enum CodingKeys: String, CodingKey { case geometrie_bestanden }
        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            urteil = try c.decodeIfPresent(Urteil.self, forKey: .geometrie_bestanden)
                ?? .nichtGemessen
        }
    }

    private func lies<T: Decodable>(_ text: String, als typ: T.Type) throws -> T {
        try JSONDecoder().decode(typ, from: Data(text.utf8))
    }

    func testNullWirdNichtGemessenUndNichtFalse() throws {
        let e = try lies(#"{"geometrie_bestanden": null}"#, als: Eintrag.self)
        XCTAssertEqual(e.geometrie_bestanden, .nichtGemessen)
        XCTAssertNotEqual(e.geometrie_bestanden, .durchgefallen,
                          "null ist nicht gemessen — nie «nicht bestanden»")
        XCTAssertNil(e.geometrie_bestanden.bestanden,
                     "zurueck in die Form des Projekts bleibt es null, nicht false")
    }

    func testTrueUndFalseBleibenWasSieSind() throws {
        XCTAssertEqual(try lies(#"{"geometrie_bestanden": true}"#, als: Eintrag.self)
            .geometrie_bestanden, .bestanden)
        XCTAssertEqual(try lies(#"{"geometrie_bestanden": false}"#, als: Eintrag.self)
            .geometrie_bestanden, .durchgefallen)
    }

    func testEinFehlendesFeldIstNichtGemessen() throws {
        XCTAssertEqual(try lies(#"{}"#, als: EintragOhnePflicht.self).urteil, .nichtGemessen)
        XCTAssertEqual(try lies(#"{"geometrie_bestanden": null}"#,
                                als: EintragOhnePflicht.self).urteil, .nichtGemessen)
    }

    func testEineZahlIstKeinUrteil() {
        // Dieselbe Falle wie in Python (`1 == True`): Eine 1 darf nicht als «bestanden»
        // durchgehen und eine 0 nicht als «durchgefallen».
        for roh in ["1", "0", "\"true\"", "\"nicht-gemessen\""] {
            XCTAssertThrowsError(
                try lies(#"{"geometrie_bestanden": "# + roh + "}", als: Eintrag.self),
                "\(roh) wurde als Urteil gelesen")
        }
    }

    func testDasZeichenDesServers() {
        XCTAssertEqual(Urteil(zeichen: "bestanden"), .bestanden)
        XCTAssertEqual(Urteil(zeichen: "durchgefallen"), .durchgefallen)
        XCTAssertEqual(Urteil(zeichen: "nicht-gemessen"), .nichtGemessen)
        // UNBEKANNT IST NICHT «NICHT GEMESSEN». Ein Zeichen von einem neueren Server wird
        // nicht geraten.
        XCTAssertNil(Urteil(zeichen: "ungeprueft"))
        XCTAssertNil(Urteil(zeichen: ""))
    }

    func testHinUndZurueckVerliertDenDrittenFallNicht() throws {
        for urteil in [Urteil.bestanden, .durchgefallen, .nichtGemessen] {
            let roh = try JSONEncoder().encode([urteil])
            XCTAssertEqual(try JSONDecoder().decode([Urteil].self, from: roh), [urteil])
            XCTAssertEqual(Urteil(zeichen: urteil.zeichen), urteil)
        }
        XCTAssertEqual(String(decoding: try JSONEncoder().encode([Urteil.nichtGemessen]),
                              as: UTF8.self), "[null]")
    }
}
