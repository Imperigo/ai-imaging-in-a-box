import Foundation
import XCTest
@testable import VisboxKern

/// A0264: Die Startseite am Mac ist ab der kleinsten Fensterbreite ganz sichtbar, und die Liste
/// «Noch am Heim-PC» springt beim Fuellen nicht.
final class StartmassTests: XCTestCase {

    func testKleinstesFensterZeigtBeideSeitenGanz() {
        XCTAssertTrue(Startmass.passt(fensterbreite: Startmass.kleinsteFensterbreite))
    }

    func testJedeBreiteAbDerKleinstenPasst() {
        var breite = Startmass.kleinsteFensterbreite
        while breite <= 3000 {
            XCTAssertTrue(Startmass.passt(fensterbreite: breite), "bei \(breite) px")
            breite += 10
        }
    }

    func testBilderbreiten1100_1280_1440() {
        for breite in [1100.0, 1280.0, 1440.0] {
            let links = Startmass.zeilenseite(fuer: breite)
            XCTAssertLessThanOrEqual(links + Startmass.trennlinie + Startmass.rechteSeiteKleinste, breite,
                                     "bei \(breite) px nichts abgeschnitten")
            XCTAssertGreaterThanOrEqual(links, Startmass.zeilenseiteKleinste)
            XCTAssertLessThanOrEqual(links, Startmass.zeilenseiteWunsch)
        }
    }

    func testBreitesFensterBehaeltDenWunsch() {
        XCTAssertEqual(Startmass.zeilenseite(fuer: 2200), Startmass.zeilenseiteWunsch)
    }

    func testKleinsteFensterhoeheBleibtSiebenhundert() {
        XCTAssertEqual(Startmass.kleinsteFensterhoehe, 700)
        XCTAssertEqual(Startmass.kleinsteFensterbreite, 1100)
    }

    // -------------------------------------------------------- die Liste springt nicht

    func testListenhoeheIstLadenderUndFertigGleich() {
        for zeilen in [0, 1, 2, 5, 12] {
            XCTAssertEqual(Mappenfenster.listenhoehe(heimLaedt: true, zeilen: 0),
                           Mappenfenster.listenhoehe(heimLaedt: false, zeilen: zeilen),
                           "mit \(zeilen) Mappen springt die Liste")
        }
    }

    func testListenhoeheLiegtFest() {
        XCTAssertEqual(Mappenfenster.listenhoehe(heimLaedt: true, zeilen: 0), Mappenfenster.hoechstens)
        XCTAssertGreaterThan(Mappenfenster.hoechstens, 0)
    }
}
