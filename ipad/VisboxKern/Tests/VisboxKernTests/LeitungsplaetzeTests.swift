import Foundation
import XCTest
import VisboxKern

/// Die Plätze für Verbindungen am Mac (Sicherheitsdurchsicht vom 01.10.2026): **Wer stumm
/// Verbindungen öffnet, verdrängt das iPad nicht.** Bis dahin wurde bei 16 offenen jede neue
/// geschlossen — auch die des iPad.
final class LeitungsplaetzeTests: XCTestCase {

    func testBisZurGrenzeWirdAngenommen() {
        var p = Leitungsplaetze<Int>(hoechstens: 3, jeGegenstelle: 3)
        XCTAssertEqual(p.nimm(1, gegenstelle: "a"), .annehmen(schliesse: nil))
        XCTAssertEqual(p.nimm(2, gegenstelle: "b"), .annehmen(schliesse: nil))
        XCTAssertEqual(p.nimm(3, gegenstelle: "c"), .annehmen(schliesse: nil))
        XCTAssertEqual(p.anzahl, 3)
        p.entferne(2)
        XCTAssertEqual(p.anzahl, 2)
    }

    /// **Volles Haus: die älteste noch unangemeldete geht**, nicht die neue — und nie eine
    /// angemeldete.
    func testVollesHausSchliesstDieAeltesteUnangemeldete() {
        var p = Leitungsplaetze<Int>(hoechstens: 3, jeGegenstelle: 3)
        _ = p.nimm(1, gegenstelle: "ipad")
        _ = p.nimm(2, gegenstelle: "fremd")
        _ = p.nimm(3, gegenstelle: "andere")
        p.angemeldet(1)
        XCTAssertEqual(p.nimm(4, gegenstelle: "ipad"), .annehmen(schliesse: 2))
        XCTAssertEqual(p.anzahl, 3)
        XCTAssertEqual(p.nimm(5, gegenstelle: "x"), .annehmen(schliesse: 3))
        p.angemeldet(4)
        p.angemeldet(5)
        XCTAssertEqual(p.nimm(6, gegenstelle: "x"), .ablehnen,
                       "alle angemeldet: dann die neue nicht, statt einer, die arbeitet")
    }

    /// **Je Gegenstelle eine Obergrenze:** Wer von einer Adresse aus flutet, verdrängt seine
    /// eigenen Verbindungen, nicht die einer anderen — das iPad behält seine Plätze.
    func testEineGegenstelleVerdraengtNurSichSelbst() {
        var p = Leitungsplaetze<Int>(hoechstens: 4, jeGegenstelle: 2)
        _ = p.nimm(1, gegenstelle: "ipad")
        _ = p.nimm(2, gegenstelle: "fremd")
        _ = p.nimm(3, gegenstelle: "fremd")
        for neu in 4..<40 {
            guard case .annehmen(let weg?) = p.nimm(neu, gegenstelle: "fremd") else {
                return XCTFail("\(neu)")
            }
            XCTAssertNotEqual(weg, 1, "die Verbindung des iPad bleibt")
        }
        XCTAssertEqual(p.nimm(100, gegenstelle: "ipad"), .annehmen(schliesse: nil),
                       "für das iPad ist noch Platz")
        p.angemeldet(1)
        p.angemeldet(100)
        XCTAssertEqual(p.nimm(101, gegenstelle: "ipad"), .ablehnen,
                       "an seiner eigenen Grenze, und beide arbeiten")
    }

    func testDieGrenzenSindKlein() {
        XCTAssertEqual(Leitungsplaetze<Int>.hoechstens, 16)
        XCTAssertLessThan(Leitungsplaetze<Int>.jeGegenstelle, Leitungsplaetze<Int>.hoechstens)
        XCTAssertLessThanOrEqual(Leitungsplaetze<Int>.kopffrist, 5)
    }
}
