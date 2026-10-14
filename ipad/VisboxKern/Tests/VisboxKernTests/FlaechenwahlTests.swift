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

    func testAdressenAufDemHeimPC() throws {
        let basis = try XCTUnwrap(URL(string: "https://heim.example:8731"))
        XCTAssertEqual(Flaechenwahl.knoten.adresse(basis: basis)?.absoluteString,
                       "https://heim.example:8731/knoten/")
        XCTAssertEqual(Flaechenwahl.seite.adresse(basis: basis)?.absoluteString,
                       "https://heim.example:8731/")
    }
}
