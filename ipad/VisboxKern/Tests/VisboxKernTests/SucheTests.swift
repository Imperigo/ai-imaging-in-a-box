import Foundation
import XCTest
import VisboxKern

/// Das Finden der HomeStation: was gefunden wurde, und welche genommen wird.
final class SucheTests: XCTestCase {

    private func dienst(_ name: String, _ rechner: String? = "192.0.2.10",
                        _ anschluss: Int? = 8731) -> GefundenerDienst {
        GefundenerDienst(name: name, rechner: rechner, anschluss: anschluss)
    }

    // ------------------------------------------------------------------ die Wahl

    func testKeinerIstKeiner() {
        XCTAssertEqual(Suche.waehle([]), .keiner)
    }

    func testGenauEinerWirdGenommen() {
        XCTAssertEqual(Suche.waehle([dienst("Arbeitsrechner")]), .einer(dienst("Arbeitsrechner")))
    }

    func testMehrereWerdenAngebotenUndNichtGeraten() {
        let ergebnis = Suche.waehle([dienst("zweiter", "192.0.2.20"), dienst("Erster")])
        XCTAssertEqual(ergebnis, .mehrere([dienst("Erster"), dienst("zweiter", "192.0.2.20")]),
                       "nach Namen geordnet, keiner vorgezogen")
    }

    func testDieselbeHomeStationUeberZweiWegeIstEine() {
        // Ueber WLAN und Kabel gemeldet: derselbe Name, einmal noch nicht aufgeloest.
        let unaufgeloest = dienst("Arbeitsrechner", nil, nil)
        let aufgeloest = dienst("Arbeitsrechner", "192.0.2.10", 8731)
        XCTAssertEqual(Suche.waehle([unaufgeloest, aufgeloest]), .einer(aufgeloest))
        XCTAssertEqual(Suche.waehle([aufgeloest, unaufgeloest]), .einer(aufgeloest))
    }

    // ------------------------------------------------------------ der Dienst selbst

    func testDieAdresseEntstehtErstMitRechnerUndAnschluss() {
        XCTAssertEqual(dienst("a").adresse?.absoluteString, "http://192.0.2.10:8731")
        XCTAssertNil(dienst("a", nil, 8731).adresse)
        XCTAssertNil(dienst("a", "192.0.2.10", nil).adresse)
        XCTAssertNil(dienst("a", "192.0.2.10", 0).adresse)
        XCTAssertFalse(dienst("a", nil, nil).aufgeloest)
    }

    func testEineIpv6AdresseStehtInKlammernMitKodiertemBereich() throws {
        let url = try XCTUnwrap(dienst("a", "fe80::1%en0", 8731).adresse)
        XCTAssertEqual(url.absoluteString, "http://[fe80::1%25en0]:8731")
    }

    func testTxtEintraegeInLeitungsform() {
        // RFC 6763: Laengenbyte + «schluessel=wert»; der erste gleiche Schluessel gilt.
        var roh = Data()
        for teil in ["Fassung=1", "ohnewert", "fassung=2", "=leer", "name=Ä b"] {
            let b = Array(teil.utf8)
            roh.append(UInt8(b.count))
            roh.append(contentsOf: b)
        }
        roh.append(0)
        let e = GefundenerDienst.txtEintraege(roh)
        XCTAssertEqual(e, ["fassung": "1", "ohnewert": "", "name": "Ä b"])
        XCTAssertEqual(GefundenerDienst(name: "x", rechner: nil, anschluss: nil, eintraege: e).fassung, "1")
    }

    func testEinAbgeschnittenerTxtEintragWirdNichtErfunden() {
        let roh = Data([5] + Array("ab=c".utf8))   // fuenf angesagt, vier da
        XCTAssertEqual(GefundenerDienst.txtEintraege(roh), [:])
    }

    func testOhneFassungIstDieFassungUnbekannt() {
        XCTAssertNil(dienst("a").fassung)
    }

    // -------------------------------------------------------- die eingetippte Adresse

    func testEineEingetippteAdresseWirdZurAdresse() {
        XCTAssertEqual(Suche.adresse(ausEingabe: " 192.0.2.10 ")?.absoluteString,
                       "http://192.0.2.10:\(Suche.vorgabeAnschluss)")
        XCTAssertEqual(Suche.adresse(ausEingabe: "192.0.2.10:9000")?.absoluteString,
                       "http://192.0.2.10:9000")
        XCTAssertEqual(Suche.adresse(ausEingabe: "http://homestation.local:8731/")?.absoluteString,
                       "http://homestation.local:8731")
    }

    func testWasDerServerNichtSprichtWirdAbgelehnt() {
        for falsch in ["", "   ", "https://192.0.2.10", "192.0.2.10/api/projekt",
                       "http://a:b@192.0.2.10", "192.0.2.10?x=1", "192.0.2.10:99999",
                       "ftp://192.0.2.10", "192.0 .2.10"] {
            XCTAssertNil(Suche.adresse(ausEingabe: falsch), falsch)
        }
    }

    // ------------------------------------------------------------- der Zustand

    func testGekoppeltStehtErstDaWennDieHomeStationGeantwortetHat() {
        XCTAssertEqual(Verbindungszustand.bestimme(gekoppelt: true, sucht: false,
                                                   erreichbar: nil, grund: nil), .suche,
                       "eine gemerkte Anmeldung ist noch keine Verbindung")
        XCTAssertEqual(Verbindungszustand.bestimme(gekoppelt: true, sucht: true,
                                                   erreichbar: true, grund: nil), .gekoppelt)
        XCTAssertEqual(Verbindungszustand.bestimme(gekoppelt: true, sucht: false,
                                                   erreichbar: false, grund: "weg"),
                       .getrennt(grund: "weg"))
        XCTAssertEqual(Verbindungszustand.bestimme(gekoppelt: false, sucht: false,
                                                   erreichbar: true, grund: nil), .aus)
        XCTAssertEqual(Verbindungszustand.bestimme(gekoppelt: false, sucht: true,
                                                   erreichbar: nil, grund: nil), .suche)
    }

    func testGesendetWirdNurGekoppelt() {
        XCTAssertTrue(Verbindungszustand.gekoppelt.darfSenden)
        for z in [Verbindungszustand.aus, .suche, .getrennt(grund: "x")] {
            XCTAssertFalse(z.darfSenden, "\(z)")
        }
        XCTAssertEqual([Verbindungszustand.aus, .suche, .gekoppelt, .getrennt(grund: "x")].map(\.wort),
                       ["Aus", "Suche", "Gekoppelt", "Getrennt"])
    }
}
