import Foundation
import XCTest
@testable import VisboxKern

/// «Exportieren» in der Mac-App (Video-Befund L3-A4): der Name, den der Sichern-Dialog vorschlägt.
final class SichernameTests: XCTestCase {

    func testDerVorschlagDerSeiteBleibt() {
        XCTAssertEqual(Sichername.vorschlag("Projekt-Lauf-3-K1.png"), "Projekt-Lauf-3-K1.png")
        XCTAssertEqual(Sichername.vorschlag("Ansicht Süd.jpg"), "Ansicht Süd.jpg")
    }

    func testNurDerLetzteTeilEinesPfads() {
        XCTAssertEqual(Sichername.vorschlag("../../etc/K1.png"), "K1.png")
        XCTAssertEqual(Sichername.vorschlag("ordner\\K2.png"), "K2.png")
    }

    func testKeinVersteckterNameKeinDoppelpunktKeineSteuerzeichen() {
        XCTAssertEqual(Sichername.vorschlag(".versteckt.png"), "versteckt.png")
        XCTAssertEqual(Sichername.vorschlag("Lauf 3: Abend.png"), "Lauf 3- Abend.png")
        XCTAssertEqual(Sichername.vorschlag("K1\u{0007}.png"), "K1.png")
    }

    func testOhneBrauchbarenNamenDieVorgabe() {
        XCTAssertEqual(Sichername.vorschlag(nil), Sichername.vorgabe)
        XCTAssertEqual(Sichername.vorschlag(""), Sichername.vorgabe)
        XCTAssertEqual(Sichername.vorschlag("   "), Sichername.vorgabe)
        XCTAssertEqual(Sichername.vorschlag("..."), Sichername.vorgabe)
    }

    func testOhneEndungPngUndHoechstensHundertzwanzigZeichen() {
        XCTAssertEqual(Sichername.vorschlag("Bild"), "Bild.png")
        let lang = Sichername.vorschlag(String(repeating: "a", count: 300) + ".png")
        XCTAssertEqual(lang.count, Sichername.hoechstens)
        XCTAssertTrue(lang.hasSuffix(".png"))
    }
}
