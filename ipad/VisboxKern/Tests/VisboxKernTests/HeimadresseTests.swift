import Foundation
import XCTest
import VisboxKern

/// Die Adresse des Heim-PC beim Einrichten der Mac-App: https, ein Anschluss, kein Pfad —
/// und nie ein Kennwort darin. Die Namen hier sind Platzhalter (Regel 3).
final class HeimadresseTests: XCTestCase {

    private func gut(_ eingabe: String, file: StaticString = #filePath,
                     line: UInt = #line) -> (URL, String?)? {
        guard case .gut(let url, let hinweis) = Heimadresse.pruefe(eingabe) else {
            XCTFail("abgewiesen: \(eingabe) — \(Heimadresse.pruefe(eingabe))", file: file,
                    line: line)
            return nil
        }
        return (url, hinweis)
    }

    private func schlecht(_ eingabe: String, file: StaticString = #filePath,
                          line: UInt = #line) -> String {
        guard case .schlecht(let satz) = Heimadresse.pruefe(eingabe) else {
            XCTFail("angenommen: \(eingabe)", file: file, line: line)
            return ""
        }
        XCTAssertFalse(satz.isEmpty, file: file, line: line)
        return satz
    }

    func testEineVollstaendigeAdresseGehtUnveraendert() {
        let r = gut("https://rechner.beispiel-netz.ts.net:8443")
        XCTAssertEqual(r?.0.absoluteString, "https://rechner.beispiel-netz.ts.net:8443")
        XCTAssertNil(r?.1)
    }

    func testRandUndSchraegstrichAmEndeWerdenAbgenommen() {
        let r = gut("  https://Rechner.Beispiel-Netz.ts.net:8443/ \n")
        XCTAssertEqual(r?.0.absoluteString, "https://rechner.beispiel-netz.ts.net:8443")
    }

    func testOhneSchemaIstHttpsGemeint() {
        XCTAssertEqual(gut("rechner.beispiel-netz.ts.net:8443")?.0.absoluteString,
                       "https://rechner.beispiel-netz.ts.net:8443")
    }

    /// Ohne Anschluss hiesse https: 443 — dort leitet am Heim-PC KosmoOrbit weiter, nicht
    /// Visbox. Darum 8443, und der Satz sagt es.
    func testOhneAnschlussWird8443GenommenUndGesagt() {
        let r = gut("https://rechner.beispiel-netz.ts.net")
        XCTAssertEqual(r?.0.absoluteString, "https://rechner.beispiel-netz.ts.net:8443")
        XCTAssertTrue(r?.1?.contains("8443") ?? false, "\(String(describing: r?.1))")
        XCTAssertEqual(Heimadresse.vorgabeAnschluss, 8443)
    }

    func testEinAndererAnschlussBleibt() {
        XCTAssertEqual(gut("https://rechner.beispiel-netz.ts.net:443")?.0.absoluteString,
                       "https://rechner.beispiel-netz.ts.net:443")
    }

    func testNurHttps() {
        XCTAssertTrue(schlecht("http://rechner.beispiel-netz.ts.net:8443").contains("https"))
        XCTAssertTrue(schlecht("ftp://rechner.beispiel-netz.ts.net:8443").contains("https"))
    }

    func testKeinPfad() {
        let satz = schlecht("https://rechner.beispiel-netz.ts.net:8443/unterpfad")
        XCTAssertTrue(satz.hasPrefix("Ohne Pfad"), satz)
        _ = schlecht("https://rechner.beispiel-netz.ts.net:8443/api/fortschritt")
    }

    func testKeineFrageUndKeinAnker() {
        _ = schlecht("https://rechner.beispiel-netz.ts.net:8443?a=b")
        _ = schlecht("https://rechner.beispiel-netz.ts.net:8443#oben")
    }

    /// **Das Kennwort gehört in den Schlüsselbund.** Die Adresse landet in den Einstellungen
    /// des Mac — mit Benutzer und Kennwort darin lägen beide dort im Klartext.
    func testKeinBenutzerUndKeinKennwortInDerAdresse() {
        let satz = schlecht("https://jemand:geheim@rechner.beispiel-netz.ts.net:8443")
        XCTAssertTrue(satz.contains("Schlüsselbund"), satz)
        _ = schlecht("https://jemand@rechner.beispiel-netz.ts.net:8443")
    }

    func testDiePlatzhalterDesBeispielsWerdenErkannt() {
        let satz = schlecht(Heimadresse.beispiel)
        XCTAssertTrue(satz.contains("Platzhalter"), satz)
    }

    func testLeerOderMitLeerzeichen() {
        XCTAssertTrue(schlecht("   ").contains(Heimadresse.beispiel))
        _ = schlecht("https://rechner beispiel.ts.net:8443")
    }

    func testEinAnschlussAusserhalbDesBereichs() {
        _ = schlecht("https://rechner.beispiel-netz.ts.net:0")
        _ = schlecht("https://rechner.beispiel-netz.ts.net:70000")
    }

    func testOhneNamen() {
        _ = schlecht("https://:8443")
    }

    /// Was gemerkt wird, trägt die Wege des Servers an der Wurzel — die Seite ruft `/api/…`.
    func testDieWegeLiegenAnDerWurzelDerGepruefenAdresse() throws {
        let basis = try XCTUnwrap(gut("rechner.beispiel-netz.ts.net")?.0)
        XCTAssertEqual(Wege.adresse(Wege.fortschritt, basis: basis)?.absoluteString,
                       "https://rechner.beispiel-netz.ts.net:8443/api/fortschritt")
        XCTAssertEqual(Wege.adresse(Wege.seite, basis: basis)?.absoluteString,
                       "https://rechner.beispiel-netz.ts.net:8443/")
    }

    /// Ein Vorschlag aus der Marke, kein fester Wert (Protokoll §2). Dass er dem Server
    /// entspricht, prüft `tests/test_ipad_geruest.py`.
    func testDerVorgeschlageneBenutzerKommtAusDerMarke() {
        XCTAssertEqual(Heimadresse.vorgabeBenutzer, Marke.name.lowercased())
        XCTAssertFalse(Heimadresse.vorgabeBenutzer.isEmpty)
    }
}
