import Foundation
import XCTest
import VisboxKern

/// Die Wege des Servers. Ob sie mit `oberflaeche/server.py` uebereinstimmen, prueft
/// `tests/test_ipad_geruest.py` auf der Python-Seite; hier wird geprueft, was die App
/// mit ihnen TUT.
final class WegeTests: XCTestCase {

    func testKeinWegStehtZweimal() {
        let schluessel = Wege.alle.map { "\($0.methode.rawValue) \($0.pfad)" }
        XCTAssertEqual(Set(schluessel).count, schluessel.count, "\(schluessel)")
    }

    func testGenauEinWegOhneAnmeldungUndDasIstVerbinden() {
        let offen = Wege.alle.filter(\.ohneAnmeldung)
        XCTAssertEqual(offen, [Wege.verbinden])
        XCTAssertEqual(Wege.verbinden.methode, .post,
                       "der Server laesst ohne Anmeldung nur POST durch")
    }

    func testDieAdresseTraegtPfadUndAnschluss() throws {
        let basis = try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))
        let url = try XCTUnwrap(Wege.adresse(Wege.fortschritt, basis: basis))
        XCTAssertEqual(url.absoluteString, "http://192.0.2.10:8731/api/fortschritt")
    }

    func testEinBildnameMitSonderzeichenKommtUnverfaelschtAn() throws {
        // `parse_qs` des Servers liest `+` als Leerzeichen und `&` als Trenner. Beides
        // muss kodiert sein, sonst zeigt die Adresse auf ein anderes Bild.
        let basis = try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))
        let url = try XCTUnwrap(Wege.adresse(Wege.bild, basis: basis,
                                             frage: [("name", "a+b & c.png")]))
        let frage = try XCTUnwrap(url.query)
        XCTAssertFalse(frage.contains("+"), frage)
        XCTAssertFalse(frage.dropFirst("name=".count).contains("&"), frage)
        let zurueck = URLComponents(url: url, resolvingAgainstBaseURL: false)?
            .queryItems?.first { $0.name == "name" }?.value
        XCTAssertEqual(zurueck, "a+b & c.png")
    }
}
