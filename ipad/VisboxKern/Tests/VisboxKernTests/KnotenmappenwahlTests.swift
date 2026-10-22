import Foundation
import XCTest
import VisboxKern

/// Owner-Entscheid 129 (22.10.2026): Der Mac merkt sich seine zuletzt offene Mappe selbst und öffnet
/// die Knotenansicht mit ihr; andere Geräte verstellen sie nicht mehr (Protokoll 74 §231).
final class KnotenmappenwahlTests: XCTestCase {
    private func daten(_ text: String) -> Data { Data(text.utf8) }

    func testDerNameKommtAusDerAntwortDesGraphen() {
        XCTAssertEqual(Knotenmappenwahl.mappe(ausGraphAntwort: daten(#"{"graphen":[],"mappe":"Demohaus Test","stand":"leer"}"#)),
                       "Demohaus Test")
        XCTAssertNil(Knotenmappenwahl.mappe(ausGraphAntwort: daten(#"{"graphen":[]}"#)))
        XCTAssertNil(Knotenmappenwahl.mappe(ausGraphAntwort: daten("kein json")))
    }

    func testNurBlosseOrdnernamen() {
        XCTAssertTrue(Knotenmappenwahl.gueltig("probe330"))
        for falsch in ["", " ", "../weg", "a/b", ".versteckt", "a\\b", String(repeating: "x", count: 201)] {
            XCTAssertFalse(Knotenmappenwahl.gueltig(falsch), falsch)
            XCTAssertNil(Knotenmappenwahl.mappe(ausGraphAntwort: daten(#"{"mappe":"\#(falsch.replacingOccurrences(of: "\\", with: "\\\\"))"}"#)))
        }
    }

    func testMerkenUndVergessen() {
        let mit = daten(#"{"mappe":"Demohaus"}"#)
        XCTAssertEqual(Knotenmappenwahl.folge(status: 200, daten: mit, verlangt: nil), .merke("Demohaus"))
        XCTAssertEqual(Knotenmappenwahl.folge(status: 404, daten: daten("{}"), verlangt: "Weg"), .vergiss)
        XCTAssertEqual(Knotenmappenwahl.folge(status: 404, daten: daten("{}"), verlangt: nil), .nichts)
        XCTAssertEqual(Knotenmappenwahl.folge(status: 502, daten: mit, verlangt: "Demohaus"), .nichts)
    }

    func testBeimLadenNurOhneMacMappeUndNichtVonDerSeite() {
        XCTAssertEqual(Knotenmappenwahl.beimLaden(gemerkt: "Demohaus", macMappeOffen: false, vonDerSeite: false), "Demohaus")
        XCTAssertNil(Knotenmappenwahl.beimLaden(gemerkt: "Demohaus", macMappeOffen: true, vonDerSeite: false))
        XCTAssertNil(Knotenmappenwahl.beimLaden(gemerkt: "Demohaus", macMappeOffen: false, vonDerSeite: true))
        XCTAssertNil(Knotenmappenwahl.beimLaden(gemerkt: nil, macMappeOffen: false, vonDerSeite: false))
        XCTAssertNil(Knotenmappenwahl.beimLaden(gemerkt: "../x", macMappeOffen: false, vonDerSeite: false))
    }

    func testDerEinstiegTraegtDieMappe() {
        XCTAssertEqual(Knotenmappenwahl.einstieg(mappe: nil), Knotenwege.einstieg)
        let mit = Knotenmappenwahl.einstieg(mappe: "Demohaus Test")
        XCTAssertTrue(Knotenwege.istEigen(mit))
        XCTAssertEqual(Knotenmappenwahl.verlangt(in: mit), "Demohaus Test")
        XCTAssertEqual(URLComponents(url: mit, resolvingAgainstBaseURL: false)?.path,
                       URLComponents(url: Knotenwege.einstieg, resolvingAgainstBaseURL: false)?.path)
        XCTAssertNil(Knotenmappenwahl.verlangt(in: Knotenwege.einstieg))
    }
}
