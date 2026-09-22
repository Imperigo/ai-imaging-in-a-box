import Foundation
import XCTest
import VisboxKern

/// Die eine Stelle fuer Name, Kennung und Dienst. Ob sie wirklich die EINE ist, prueft
/// `tests/test_ipad_geruest.py` (Abwesenheit in allen uebrigen Swift-Dateien); hier wird
/// geprueft, dass iOS mit den Werten etwas anfangen kann.
final class MarkeTests: XCTestCase {

    func testDerDienstHatDieFormDieIOSVerlangt() {
        // Bonjour: `_` + 1 bis 15 Zeichen aus Kleinbuchstaben, Ziffern, Strich + `._tcp`.
        // Ein Dienst in anderer Form wird von iOS still nicht gefunden — kein Fehler,
        // nur nichts.
        let muster = #"^_[a-z0-9-]{1,15}\._tcp$"#
        XCTAssertNotNil(Marke.dienst.range(of: muster, options: .regularExpression),
                        Marke.dienst)
    }

    func testDieKennungIstUmgekehrteDomainSchreibweise() {
        let teile = Marke.kennung.split(separator: ".", omittingEmptySubsequences: false)
        XCTAssertGreaterThanOrEqual(teile.count, 2, Marke.kennung)
        XCTAssertNotNil(Marke.kennung.range(of: #"^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$"#,
                                            options: .regularExpression), Marke.kennung)
    }

    func testDerNameIstNichtLeer() {
        XCTAssertFalse(Marke.name.trimmingCharacters(in: .whitespaces).isEmpty)
    }
}
