import Foundation
import XCTest
import VisboxKern

/// Unterwegs direkt über Tailscale zum Heim-PC (Entscheid 63, 01.10.2026): die eingetippte
/// https-Adresse, was davon gemerkt wird, dass jede Anfrage ihr Schema behält, und welcher
/// Satz kommt, wenn keine Antwort kommt. Die Namen sind Platzhalter (Regel 3).
final class StreckeTests: XCTestCase {

    private let tailscale = "https://rechner.beispiel-netz.ts.net:8443"

    private func gut(_ eingabe: String, file: StaticString = #filePath,
                     line: UInt = #line) -> (URL, String?)? {
        guard case .gut(let url, let hinweis) = Suche.pruefe(eingabe: eingabe) else {
            XCTFail("abgewiesen: \(eingabe) — \(Suche.pruefe(eingabe: eingabe))", file: file,
                    line: line)
            return nil
        }
        return (url, hinweis)
    }

    private func schlecht(_ eingabe: String, file: StaticString = #filePath,
                          line: UInt = #line) -> String {
        guard case .schlecht(let satz) = Suche.pruefe(eingabe: eingabe) else {
            XCTFail("angenommen: \(eingabe)", file: file, line: line)
            return ""
        }
        XCTAssertFalse(satz.isEmpty, file: file, line: line)
        return satz
    }

    // ------------------------------------------------------- die eingetippte Adresse

    func testDieTailscaleAdresseGehtUnveraendert() {
        let r = gut(tailscale)
        XCTAssertEqual(r?.0.absoluteString, tailscale)
        XCTAssertNil(r?.1, "nichts ergänzt, also kein Hinweis")
        XCTAssertEqual(r.map { Strecke(basis: $0.0) }, .tailscale)
    }

    func testEingefuegtMitRandUndSchraegstrichGehtAuch() {
        XCTAssertEqual(gut("  \(tailscale)/ \n")?.0.absoluteString, tailscale)
        XCTAssertEqual(gut("HTTPS://Rechner.Beispiel-Netz.ts.net:8443")?.0.absoluteString,
                       tailscale)
    }

    func testOhneAnschlussGilt8443MitHinweis() {
        let r = gut("https://rechner.beispiel-netz.ts.net")
        XCTAssertEqual(r?.0.absoluteString, tailscale)
        XCTAssertEqual(r?.0.port, Heimadresse.vorgabeAnschluss)
        XCTAssertTrue(r?.1?.contains("8443") ?? false, "der Hinweis nennt den Anschluss")
    }

    func testEinTailscaleNameOhneSchemaIstHttps() {
        // TAILSCALE SERVE SPRICHT NUR HTTPS — ein `.ts.net`-Name ohne Schema meint es.
        XCTAssertEqual(gut("rechner.beispiel-netz.ts.net:8443")?.0.absoluteString, tailscale)
        XCTAssertEqual(gut("rechner.beispiel-netz.ts.net")?.0.absoluteString, tailscale)
    }

    func testEinTailscaleNameMitHttpWirdMitSatzAbgelehnt() {
        let satz = schlecht("http://rechner.beispiel-netz.ts.net:8443")
        XCTAssertTrue(satz.contains("https"), satz)
    }

    func testKennwortInDerAdresseWirdAbgelehntUndDerSatzPasstAufsIPad() {
        for eingabe in ["https://jemand:geheim@rechner.beispiel-netz.ts.net:8443",
                        "https://jemand@rechner.beispiel-netz.ts.net:8443",
                        "http://jemand:geheim@192.0.2.10:8731"] {
            let satz = schlecht(eingabe)
            XCTAssertTrue(satz.contains("Schlüsselbund"), satz)
            // DER SATZ DER MAC-APP sagt «Einstellungen des Mac» — am iPad gibt es die nicht.
            XCTAssertFalse(satz.contains("Mac"), satz)
            XCTAssertFalse(satz.contains("geheim"), "das Kennwort steht nicht im Satz")
        }
    }

    func testPfadFrageUndPlatzhalterWerdenAbgelehnt() {
        _ = schlecht("\(tailscale)/api/fortschritt")
        _ = schlecht("\(tailscale)?a=b")
        _ = schlecht("\(tailscale)#oben")
        _ = schlecht("https://rechner.beispiel-netz.ts.net:70000")
        XCTAssertTrue(schlecht(Heimadresse.beispiel).contains("Platzhalter"))
        XCTAssertTrue(schlecht("ftp://rechner.beispiel-netz.ts.net").contains("https"))
    }

    /// EINE PRUEFUNG FUER DIESELBE ADRESSE: Was die Mac-App für den Heim-PC nimmt, nimmt das
    /// iPad genauso (bis auf den Satz zu Benutzer und Kennwort, der am iPad anders lautet).
    func testHttpsLiestDasIPadWieDieMacApp() {
        for eingabe in [tailscale, "https://rechner.beispiel-netz.ts.net",
                        "https://rechner.beispiel-netz.ts.net:443",
                        "https://rechner.beispiel-netz.ts.net:8443/",
                        "https://rechner.beispiel-netz.ts.net:8443/unterpfad",
                        "https://rechner.beispiel-netz.ts.net:0", "https://:8443"] {
            XCTAssertEqual(Suche.pruefe(eingabe: eingabe), Heimadresse.pruefe(eingabe), eingabe)
        }
    }

    func testImHeimnetzBleibtAllesWieEsWar() {
        let r = gut("192.0.2.10")
        XCTAssertEqual(r?.0.absoluteString, "http://192.0.2.10:\(Suche.vorgabeAnschluss)")
        XCTAssertNil(r?.1)
        XCTAssertEqual(r.map { Strecke(basis: $0.0) }, .heimnetz)
        XCTAssertEqual(gut("homestation.local:8731")?.0.absoluteString,
                       "http://homestation.local:8731")
    }

    // ---------------------------------------------- was im Feld steht, und in der Zeile

    func testDerFeldtextLiestSichZurSelbenAdresse() throws {
        for text in [tailscale, "http://192.0.2.10:8731", "http://homestation.local:9000"] {
            let url = try XCTUnwrap(URL(string: text))
            let feld = Suche.eingabetext(url)
            XCTAssertEqual(Suche.adresse(ausEingabe: feld), url, feld)
        }
        // IM HEIMNETZ OHNE SCHEMA (wie ein Mensch tippt), UEBER TAILSCALE MIT — dort zählt es.
        XCTAssertEqual(Suche.eingabetext(try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))),
                       "192.0.2.10:8731")
        XCTAssertEqual(Suche.eingabetext(try XCTUnwrap(URL(string: tailscale))), tailscale)
    }

    func testDieZeileNenntUeberTailscaleNurDenRechner() throws {
        let ts = try XCTUnwrap(URL(string: tailscale))
        XCTAssertEqual(Suche.anzeigename(ts), "rechner")
        XCTAssertEqual(Strecke(basis: ts).zusatz, " · über Tailscale")
        let heim = try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))
        XCTAssertEqual(Suche.anzeigename(heim), "192.0.2.10:8731")
        XCTAssertEqual(Strecke(basis: heim).zusatz, "")
    }

    // ------------------------------------------------------------ was gemerkt wird

    func testGemerktWirdDieAdresseSamtSchema() throws {
        for text in [tailscale, "http://192.0.2.10:8731", "http://homestation.local:9000",
                     "http://[fe80::1%25en0]:8731"] {
            // SO SCHREIBT `Verbindungsgedaechtnis` (absoluteString) — und so liest es zurück.
            let url = try XCTUnwrap(URL(string: text))
            let zurueck = try XCTUnwrap(Suche.gemerkt(url.absoluteString), text)
            XCTAssertEqual(zurueck, url, text)
            XCTAssertEqual(zurueck.scheme, url.scheme, text)
            XCTAssertEqual(zurueck.port, url.port, text)
        }
        // EINE GEPRUEFTE EINGABE UEBERSTEHT DAS MERKEN — https bleibt https, mit 8443.
        let eingetippt = try XCTUnwrap(Suche.adresse(ausEingabe: "rechner.beispiel-netz.ts.net"))
        XCTAssertEqual(Suche.gemerkt(eingetippt.absoluteString)?.absoluteString, tailscale)
    }

    func testVerdorbenGemerktHeisstNichtGekoppelt() {
        for text in [nil, "", "kein text", "ftp://192.0.2.10:21", "https://rechner.ts.net",
                     "http://jemand:geheim@192.0.2.10:8731", "\(tailscale)/api/projekt",
                     "\(tailscale)?a=b"] as [String?] {
            XCTAssertNil(Suche.gemerkt(text), text ?? "nil")
        }
    }

    // ----------------------------------------------- jede Anfrage behält das Schema

    func testJederWegGehtAnDieGemerkteBasisMitIhremSchema() throws {
        let basis = try XCTUnwrap(URL(string: tailscale))
        for weg in Wege.alle {
            let url = try XCTUnwrap(try Anfragen.baue(weg, anmeldung: nil).adresse(basis: basis),
                                    weg.pfad)
            XCTAssertEqual(url.scheme, "https", weg.pfad)
            XCTAssertEqual(url.host, "rechner.beispiel-netz.ts.net", weg.pfad)
            XCTAssertEqual(url.port, 8443, weg.pfad)
            XCTAssertEqual(url.path, weg.pfad.isEmpty ? "/" : weg.pfad, weg.pfad)
        }
        // MIT FRAGE: kodiert wie im Heimnetz, nur über https.
        let bild = Anfragen.bild(name: "a+b c.png", ordner: nil, anmeldung: nil)
        XCTAssertEqual(bild.adresse(basis: basis)?.absoluteString,
                       "\(tailscale)/bild?name=a%2Bb%20c.png")
    }

    /// DIE WACHE GEGEN FESTE `http://`-BAUSTEINE: Keine Datei des App-Pakets setzt ein
    /// `"http://` in Code — ausser `Kern/Suche.swift` (das Heimnetz: Bonjour und eingetippt)
    /// und `Kern/Anfragen.swift` (das Gerüst, aus dem nur der Pfad gelesen wird). Bis zum
    /// 01.10.2026 strich der Koppelbildschirm selbst ein `http://` ab.
    func testKeinFestesHttpAusserhalbDerHeimnetzregeln() throws {
        let ipad = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
        let paket = try XCTUnwrap(FileManager.default.contentsOfDirectory(
            at: ipad, includingPropertiesForKeys: nil).first { $0.pathExtension == "swiftpm" })
        let erlaubt: Set<String> = ["Suche.swift", "Anfragen.swift"]
        var gelesen = 0
        let liste = FileManager.default.enumerator(at: paket, includingPropertiesForKeys: nil)
        while let datei = liste?.nextObject() as? URL {
            guard datei.pathExtension == "swift" else { continue }
            gelesen += 1
            let code = try String(contentsOf: datei, encoding: .utf8)
                .split(separator: "\n", omittingEmptySubsequences: false)
                .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
            for zeile in code where zeile.contains("\"http://") {
                XCTAssertTrue(erlaubt.contains(datei.lastPathComponent),
                              "\(datei.lastPathComponent): \(zeile.trimmingCharacters(in: .whitespaces))")
            }
        }
        XCTAssertGreaterThan(gelesen, 20, "die Wache sieht das App-Paket nicht mehr")
    }

    // ------------------------------------------------------------- die Sätze

    func testDieStreckeStehtInDerAdresse() throws {
        XCTAssertEqual(Strecke(basis: try XCTUnwrap(URL(string: tailscale))), .tailscale)
        XCTAssertEqual(Strecke(basis: try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))),
                       .heimnetz)
        XCTAssertEqual(Strecke(basis: try XCTUnwrap(URL(string: "http://homestation.local:8731"))),
                       .heimnetz)
        // EINE AELTERE GEMERKTE `.ts.net`-ADRESSE MIT http bekommt trotzdem den Tailscale-Satz.
        XCTAssertEqual(Strecke(basis: try XCTUnwrap(URL(string: "http://rechner.netz.ts.net:8731"))),
                       .tailscale)
        XCTAssertFalse(Strecke.istTailscaleName("ts.net.beispiel"))
        XCTAssertTrue(Strecke.istTailscaleName("Rechner.Netz.TS.NET."))
    }

    /// TAILSCALE AM IPAD AUS: Name unbekannt (fast immer), keine Verbindung, keine Antwort in
    /// der Frist, Zertifikat — jeder beginnt mit dem ersten Handgriff.
    func testUeberTailscaleFragtDerSatzZuerstNachTailscale() {
        for code in [-1003, -1006, -1004, -1001, -1200, -1202, -1206] {
            let satz = Leitungsfehler(urlFehlercode: code).satzAmIPad(.tailscale)
            XCTAssertTrue(satz.hasPrefix("Tailscale am iPad an?"), "\(code): \(satz)")
        }
        XCTAssertTrue(Leitungsfehler.nameUnbekannt.satzAmIPad(.tailscale).contains("Heim-PC"))
        XCTAssertTrue(Leitungsfehler.zertifikat.satzAmIPad(.tailscale).contains(".ts.net"))
    }

    func testKeinSatzAmIPadSprichtVomMac() {
        // DIE EINTEILUNG IST DIE DER MAC-APP, DIE SAETZE NICHT: «Tailscale am Mac an?» oder
        // «Dieser Mac» wären am iPad falsch.
        for code in [-1001, -1003, -1004, -1005, -1006, -1009, -1018, -1201, -999, -1, -1022] {
            for strecke in [Strecke.heimnetz, .tailscale] {
                let satz = Leitungsfehler(urlFehlercode: code).satzAmIPad(strecke)
                XCTAssertFalse(satz.contains("Mac"), "\(code) \(strecke): \(satz)")
                XCTAssertTrue(satz.hasSuffix(".") || satz.hasSuffix("?") || satz.hasSuffix(")."),
                              satz)
            }
        }
    }

    /// ZUHAUSE AENDERT SICH NICHTS: die Sätze, die `Sender.swift` bis zum 01.10.2026 selbst
    /// schrieb, wortgleich — und keiner nennt Tailscale.
    func testImHeimnetzSindDieSaetzeDieAlten() {
        let alt: [(Int, String)] = [
            (-1004, "Die HomeStation nimmt keine Verbindung an — läuft der Server dort?"),
            (-1003, "Die Adresse der HomeStation ist im Netz nicht zu finden."),
            (-1006, "Die Adresse der HomeStation ist im Netz nicht zu finden."),
            (-1001, "Die HomeStation hat nicht rechtzeitig geantwortet."),
            (-1009, "Das iPad ist mit keinem Netz verbunden."),
            (-1005, "Die Verbindung ist unterwegs abgerissen."),
            (-999, "Das Senden wurde abgebrochen."),
        ]
        for (code, satz) in alt {
            XCTAssertEqual(Leitungsfehler(urlFehlercode: code).satzAmIPad(.heimnetz), satz)
        }
        for code in [-1001, -1003, -1004, -1005, -1006, -1009, -1201, -1] {
            XCTAssertFalse(Leitungsfehler(urlFehlercode: code).satzAmIPad(.heimnetz)
                .contains("Tailscale"), "\(code)")
        }
    }

    func testDerUnbekannteFallNenntDieMeldungDesSystemsOderDenCode() {
        let f = Leitungsfehler(urlFehlercode: -1022)
        XCTAssertTrue(f.satzAmIPad(.tailscale, beschreibung: "Eine Meldung des Systems")
            .contains("Eine Meldung des Systems"))
        XCTAssertTrue(f.satzAmIPad(.heimnetz).contains("Fehler -1022"))
        XCTAssertTrue(f.satzAmIPad(.tailscale, beschreibung: "  ").contains("Fehler -1022"))
    }
}
