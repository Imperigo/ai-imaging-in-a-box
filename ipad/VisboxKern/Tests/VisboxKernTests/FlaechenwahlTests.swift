import XCTest
import VisboxKern

/// Entscheid 85 (14.10.2026, Blatt 19): Die Mac-App zeigt zuerst die Knoten.
final class FlaechenwahlTests: XCTestCase {
    func testZuerstDieKnoten() {
        XCTAssertEqual(Flaechenwahl.beimOeffnen, .knoten)
        XCTAssertEqual(Flaechenwahl.allCases, [.knoten, .seite])     // Reihenfolge im Schalter
    }

    func testBeschriftung() {
        XCTAssertEqual(Flaechenwahl.knoten.titel, "Knoten")
        XCTAssertEqual(Flaechenwahl.seite.titel, "\(Marke.name)-Seite")
    }

    /// «Visbox eigenständig», Schritt 1: Die Knoten kommen aus dem Bündel — mit und ohne
    /// Heim-PC dieselbe Adresse; die Seite weiter vom Heim-PC.
    func testDieKnotenAusDemBuendelDieSeiteVomHeimPC() throws {
        let basis = try XCTUnwrap(URL(string: "https://heim.example:8731"))
        XCTAssertEqual(Flaechenwahl.knoten.adresse(basis: basis)?.absoluteString,
                       "\(Knotenwege.schema)://app/knoten/")
        XCTAssertEqual(Flaechenwahl.knoten.adresse(basis: nil)?.absoluteString,
                       "\(Knotenwege.schema)://app/knoten/")
        XCTAssertEqual(Flaechenwahl.seite.adresse(basis: basis)?.absoluteString,
                       "https://heim.example:8731/")
        XCTAssertNil(Flaechenwahl.seite.adresse(basis: nil))
        XCTAssertTrue(Flaechenwahl.knoten.ausDemBuendel)
        XCTAssertFalse(Flaechenwahl.seite.ausDemBuendel)
    }

    /// Der Pfad am Heim-PC bleibt: Dort bedient der Server die Knoten weiter für den Browser.
    func testDerPfadAmHeimPCBleibt() {
        XCTAssertEqual(Flaechenwahl.knoten.pfad, "/knoten/")
        XCTAssertEqual(Flaechenwahl.seite.pfad, "/")
    }
}
