import Foundation
import XCTest
import VisboxKern

/// Das Zertifikat des Mac für die Leitung zum iPad (Entscheid 118, 21.10.2026): DER-Bausteine
/// und das Zertifikat selbst — **eingefroren** gegen ein Ergebnis, das `openssl x509 -text` las
/// und `openssl verify` mit einer echten Unterschrift annahm (Protokoll 74, Strang iPad).
final class MaczertifikatTests: XCTestCase {

    private func hex(_ s: String) -> [UInt8] {
        var aus: [UInt8] = []
        var i = s.startIndex
        while i < s.endIndex {
            let j = s.index(i, offsetBy: 2)
            aus.append(UInt8(s[i..<j], radix: 16)!)
            i = j
        }
        return aus
    }

    private func alsHex(_ b: [UInt8]) -> String { Fingerabdruck.hex(b) }

    /// Der öffentliche Schlüssel der Prüfung vom 21.10.2026 (P-256, unkomprimiert).
    private let schluessel = "04e57924d8e5230e23b64c2595681ca7254e0598454e1aae5e67a41fc60c3796cc"
        + "f804b95cc8d0b3bca9706c58fa8bb3bc259a8c3b102cb9e2490f323f32c7f694"

    /// Was `openssl` als gültig las — die Bytes des unterschriebenen Teils.
    private let tbsErwartet = "30820107a00302010202087102030405060708300a06082a8648ce3d040302301b311930170603550403"
        + "0c1050726f6265204d616320616231326364301e170d3236313031343136343634305a170d3239303131"
        + "363137343634305a301b3119301706035504030c1050726f6265204d6163206162313263643059301306"
        + "072a8648ce3d020106082a8648ce3d03010703420004e57924d8e5230e23b64c2595681ca7254e059845"
        + "4e1aae5e67a41fc60c3796ccf804b95cc8d0b3bca9706c58fa8bb3bc259a8c3b102cb9e2490f323f32c7"
        + "f694a3353033300c0603551d130101ff04023000300e0603551d0f0101ff04040302078030130603551d"
        + "25040c300a06082b06010505070301"

    // ------------------------------------------------------------- DER

    func testLaengen() {
        XCTAssertEqual(Der.laenge(0), [0])
        XCTAssertEqual(Der.laenge(127), [0x7f])
        XCTAssertEqual(Der.laenge(128), [0x81, 0x80])
        XCTAssertEqual(Der.laenge(265), [0x82, 0x01, 0x09])
    }

    func testGanzeZahlenSindPositiv() {
        XCTAssertEqual(Der.ganz(2), [0x02, 0x01, 0x02])
        XCTAssertEqual(Der.ganz(0), [0x02, 0x01, 0x00])
        XCTAssertEqual(Der.ganz([0x80]), [0x02, 0x02, 0x00, 0x80], "oberstes Bit: eine Null davor")
        XCTAssertEqual(Der.ganz([0x00, 0x00, 0x05]), [0x02, 0x01, 0x05], "führende Nullen weg")
    }

    func testKennzeichen() {
        // ecdsa-with-SHA256 und der lange Teil (840 = 0x86 0x48).
        XCTAssertEqual(alsHex(Der.kennzeichen([1, 2, 840, 10045, 4, 3, 2])), "06082a8648ce3d040302")
        XCTAssertEqual(alsHex(Der.kennzeichen([2, 5, 4, 3])), "0603550403")
    }

    func testZeitBis2049KurzDanachLang() {
        let d2026 = Date(timeIntervalSince1970: 1_792_000_000)
        XCTAssertEqual(Der.zeit(d2026).first, 0x17)
        XCTAssertEqual(String(decoding: Der.zeit(d2026).dropFirst(2), as: UTF8.self), "261014174640Z")
        let d2050 = Date(timeIntervalSince1970: 2_524_608_000)
        XCTAssertEqual(Der.zeit(d2050).first, 0x18)
        XCTAssertEqual(String(decoding: Der.zeit(d2050).dropFirst(2), as: UTF8.self), "20500101000000Z")
    }

    // ------------------------------------------------------------- das Zertifikat

    func testDerUnterschriebeneTeilIstDerGepruefte() throws {
        let (von, bis) = Maczertifikat.frist(jetzt: Date(timeIntervalSince1970: 1_792_000_000))
        let tbs = try Maczertifikat.tbs(schluessel: hex(schluessel), name: "Probe Mac ab12cd",
                                        seriennummer: [0xf1, 2, 3, 4, 5, 6, 7, 8], von: von, bis: bis)
        XCTAssertEqual(alsHex(tbs), tbsErwartet)
    }

    func testDasGanzeZertifikatTraegtTeilVerfahrenUndUnterschrift() throws {
        let tbs = hex(tbsErwartet)
        let unterschrift: [UInt8] = [0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x02]
        let z = Maczertifikat.zertifikat(tbs: tbs, unterschrift: unterschrift)
        XCTAssertEqual(Array(z.prefix(4)), [0x30, 0x82, 0x01, 0x22])
        XCTAssertEqual(Array(z[4..<(4 + tbs.count)]), tbs)
        XCTAssertEqual(alsHex(Array(z.suffix(unterschrift.count + 3 + 12))),
                       "300a06082a8648ce3d04030203090030060201010201" + "02")
    }

    func testNurEinGueltigerSchluesselUndEineKurzeSeriennummer() {
        let jetzt = Date(timeIntervalSince1970: 1_792_000_000)
        XCTAssertThrowsError(try Maczertifikat.tbs(schluessel: [0x04] + [UInt8](repeating: 1, count: 63),
                                                   name: "x", seriennummer: [1], von: jetzt, bis: jetzt))
        XCTAssertThrowsError(try Maczertifikat.tbs(schluessel: hex(schluessel), name: "x",
                                                   seriennummer: [], von: jetzt, bis: jetzt))
        XCTAssertThrowsError(try Maczertifikat.tbs(schluessel: hex(schluessel), name: "x",
                                                   seriennummer: [UInt8](repeating: 1, count: 21),
                                                   von: jetzt, bis: jetzt))
        XCTAssertThrowsError(try Maczertifikat.tbs(schluessel: hex(schluessel), name: "",
                                                   seriennummer: [1], von: jetzt, bis: jetzt))
    }

    func testDerNameNenntKeinGeraet() {
        XCTAssertEqual(Maczertifikat.name(zusatz: "ab12cd"), Marke.name + " Mac ab12cd")
    }

    func testFristUndErneuern() {
        let jetzt = Date(timeIntervalSince1970: 1_792_000_000)
        let (von, bis) = Maczertifikat.frist(jetzt: jetzt)
        XCTAssertEqual(jetzt.timeIntervalSince(von), Maczertifikat.rueckdatiert)
        XCTAssertEqual(bis.timeIntervalSince(jetzt), 825 * 86_400)
        XCTAssertFalse(Maczertifikat.erneuern(bis: bis, jetzt: jetzt))
        XCTAssertTrue(Maczertifikat.erneuern(bis: jetzt.addingTimeInterval(29 * 86_400), jetzt: jetzt))
        XCTAssertTrue(Maczertifikat.erneuern(bis: nil, jetzt: jetzt), "unbekannt: neu ausstellen")
    }
}
