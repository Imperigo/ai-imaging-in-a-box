import Foundation
import XCTest
import VisboxKern

/// Das Zertifikat des Mac nach einem Update (Befund Demolauf 0.3.54, 24.10.2026): **nie still
/// ein neues, und nach einem Verlust nur einmal je Fassung.**
final class MacidentitaetsregelTests: XCTestCase {

    private typealias R = Macidentitaetsregel

    func testLesbarBleibt() {
        XCTAssertEqual(R.schritt(fund: .lesbar, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .behalten)
    }

    func testLesbarMitAblaufendFristWirdErneuert() {
        XCTAssertEqual(R.schritt(fund: .lesbar, fristLaeuftAb: true, gemerkt: true,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .erneuern)
    }

    func testNochNieEinesIstDasErsteOhneMeldung() {
        XCTAssertEqual(R.schritt(fund: .keines, fristLaeuftAb: false, gemerkt: false,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .erstesMal)
    }

    func testGemerktAberKeinesMehrDaIstEinVerlust() {
        XCTAssertEqual(R.schritt(fund: .keines, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .ersetzenNachVerlust)
        // VON HAND AUFGERAEUMT in derselben Fassung: anlegen, kein Anhalten (kein Rest liegt).
        XCTAssertEqual(R.schritt(fund: .keines, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: "0.3.55 (1)", fassung: "0.3.55 (1)"), .ersetzenNachVerlust)
    }

    func testNichtLesbarErsetztEinmal() {
        // DER BEFUND: nach dem Update nicht lesbar — einmal ersetzen, mit Meldung.
        XCTAssertEqual(R.schritt(fund: .nichtLesbar, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .ersetzenNachVerlust)
        // AUCH OHNE GEMERKTEN FINGERABDRUCK (erster Start mit dieser Regel): Es gab eines.
        XCTAssertEqual(R.schritt(fund: .nichtLesbar, fristLaeuftAb: false, gemerkt: false,
                                 ersetztIn: nil, fassung: "0.3.55 (1)"), .ersetzenNachVerlust)
        // DAS NAECHSTE UPDATE ist eine neue Fassung — dort darf es wieder einmal.
        XCTAssertEqual(R.schritt(fund: .nichtLesbar, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: "0.3.55 (1)", fassung: "0.3.56 (1)"), .ersetzenNachVerlust)
    }

    func testNichtBeiJedemStartErneut() {
        XCTAssertEqual(R.schritt(fund: .nichtLesbar, fristLaeuftAb: false, gemerkt: true,
                                 ersetztIn: "0.3.55 (1)", fassung: "0.3.55 (1)"), .anhalten)
        XCTAssertEqual(R.schritt(fund: .nichtLesbar, fristLaeuftAb: true, gemerkt: true,
                                 ersetztIn: "0.3.55 (1)", fassung: "0.3.55 (1)"), .anhalten)
    }

    func testDieZeileSagtEsBisNeuGekoppeltIst() {
        XCTAssertEqual(R.zeilenhinweis(neuKoppeln: true, zahlOffen: false), R.satzNeuKoppeln)
        XCTAssertNil(R.zeilenhinweis(neuKoppeln: true, zahlOffen: true), "die Zahl geht vor")
        XCTAssertNil(R.zeilenhinweis(neuKoppeln: false, zahlOffen: false))
        XCTAssertTrue(R.satzNeuKoppeln.contains("neu koppeln"))
        XCTAssertTrue(R.satzAngehalten.contains("nicht still"))
    }
}
