import Foundation
import XCTest
import VisboxKern

/// A0255: Der Start wartet nicht auf den Schlüsselbund; ein Testbau trägt eine eigene Kennung.
final class StartwartenTests: XCTestCase {

    // ----------------------------------------------------- Satz 1: kein Warten, ein Hinweis

    func testDerStartWartetNichtAufDenLangsamenSchluessel() {
        let tor = DispatchSemaphore(value: 0)
        let fertig = expectation(description: "Schlüssel gelesen")
        var erhalten: String?
        let antwort = DispatchQueue(label: "probe.antwort")
        let t0 = Date()
        Startwarten.starte({ () -> String in
            _ = tor.wait(timeout: .now() + 10)   // der Schlüsselbund fragt noch
            return "Zugang"
        }, fertig: { wert in erhalten = wert; fertig.fulfill() }, antwort: antwort)
        // `starte` ist zurueck, obwohl das Lesen noch haengt.
        XCTAssertLessThan(Date().timeIntervalSince(t0), 2.0, "der Start hat auf den Schlüssel gewartet")
        XCTAssertNil(erhalten)
        tor.signal()
        wait(for: [fertig], timeout: 10)
        XCTAssertEqual(erhalten, "Zugang")
    }

    func testSolangeGelesenWirdStehtDerHinweisImFenster() {
        let satz = Startwarten.hinweis(liest: true)
        XCTAssertNotNil(satz)
        XCTAssertTrue(satz!.contains("Schlüsselbund"), satz!)
        XCTAssertTrue(satz!.contains("hinter"), satz!)
        XCTAssertNil(Startwarten.hinweis(liest: false))
    }

    func testEinrichtenGehtNichtAufSolangeDerSchluesselbundLiest() {
        XCTAssertFalse(Startwarten.brauchtEinrichten(liest: true, adresseDa: false, anmeldungDa: false))
        XCTAssertTrue(Startwarten.brauchtEinrichten(liest: false, adresseDa: true, anmeldungDa: false))
        XCTAssertTrue(Startwarten.brauchtEinrichten(liest: false, adresseDa: false, anmeldungDa: true))
        XCTAssertFalse(Startwarten.brauchtEinrichten(liest: false, adresseDa: true, anmeldungDa: true))
    }

    // ----------------------------------------------------- Satz 3: die zweite Instanz sagt es

    func testDieZweiteInstanzSagtEsMitNamen() {
        let satz = Startwarten.zweiteInstanz(name: Marke.name)
        XCTAssertTrue(satz.contains(Marke.name), satz)
        XCTAssertTrue(satz.contains("läuft schon"), satz)
        XCTAssertTrue(satz.contains("nach vorn"), satz)
    }

    // ----------------------------------------------------- Satz 2: Kennung des Testbaus

    private var wurzel: URL {
        // .../ipad/VisboxKern/Tests/VisboxKernTests/Datei.swift -> Repo-Wurzel
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    }

    private func lies(_ teil: String) throws -> String {
        try String(contentsOf: wurzel.appendingPathComponent(teil), encoding: .utf8)
    }

    func testDieInstallierteAppBleibtUnterDerFestenKennung() throws {
        let plist = try lies("ipad/\(Marke.name)Mac/App/Info.plist")
        XCTAssertTrue(plist.contains("<string>\(Marke.kennung).mac</string>"),
                      "die eingecheckte Plist ist die der installierten App und bleibt es")
        XCTAssertFalse(plist.contains(".test</string>"))
    }

    func testDerTestbauBekommtEigeneKennungUndNamenNurAusserhalbVonMain() throws {
        let ablauf = try lies(".github/workflows/ipad.yml")
        // Eigene Kennung (Endung .test) und eigener Name im gebauten Buendel.
        XCTAssertTrue(ablauf.contains("Set :CFBundleIdentifier"), "keine eigene Kennung im Testbau")
        XCTAssertTrue(ablauf.contains("Set :CFBundleName"), "kein eigener Name im Testbau")
        XCTAssertTrue(ablauf.contains("Set :CFBundleDisplayName"), "kein eigener Anzeigename im Testbau")
        XCTAssertTrue(ablauf.contains(".test\""), "Endung .test fehlt")
        // Nur ausserhalb von main: die Bedingung steht an derselben Stelle wie die Kennung.
        let k = try XCTUnwrap(ablauf.range(of: "Set :CFBundleIdentifier"))
        let davor = String(ablauf[ablauf.startIndex..<k.lowerBound])
        let bedingung = try XCTUnwrap(davor.range(of: "refs/heads/main", options: .backwards))
        XCTAssertLessThan(davor.distance(from: bedingung.upperBound, to: davor.endIndex), 600,
                          "die Main-Bedingung steht nicht bei der Testbau-Kennung")
        // Die Freigabe auf main bleibt, wie sie war.
        XCTAssertTrue(ablauf.contains("if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'"))
    }

    // ----------------------------------------------------- Satz 4: die Anleitung

    func testDieAnleitungFuerTestbautenNenntStartUndRueckweg() throws {
        let text = try lies("ipad/\(Marke.name)Mac/LIESMICH.md")
        let k = try XCTUnwrap(text.range(of: "## Testbau"), "kein Abschnitt «Testbau»")
        let rest = text[k.lowerBound...].dropFirst(3)
        let abschnitt = String(rest.prefix(upTo: rest.range(of: "\n## ")?.lowerBound ?? rest.endIndex))
        for wort in ["\(Marke.name) Test.app", "\(Marke.kennung).mac.test", "ersetzt die installierte", "Rückweg",
                     "Papierkorb", "Programme"] {
            XCTAssertTrue(abschnitt.contains(wort), "Anleitung nennt «\(wort)» nicht")
        }
    }
}
