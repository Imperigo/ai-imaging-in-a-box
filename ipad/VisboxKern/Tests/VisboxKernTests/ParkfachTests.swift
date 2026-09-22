import Foundation
import XCTest
import VisboxKern

/// Das Parkfach — geprüft **an der Wirkung auf der Platte**: Jede Probe öffnet das Fach am
/// Ende ein zweites Mal aus demselben Ordner, wie die App nach einem Neustart.
final class ParkfachTests: XCTestCase {

    private var ordner: URL!

    override func setUpWithError() throws {
        ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("parkfach-probe-\(UUID().uuidString)", isDirectory: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: ordner)
    }

    private let zeichnung = Data(Ebenenausgabe.pngKennung + [7, 7, 7])
    private let t0 = Date(timeIntervalSinceReferenceDate: 800_000_000)

    private func quittung(_ name: String = "skizze-20260922-081207.png") -> Data {
        Data(#"{"abgelegt": true, "skizze": "\#(name)", "hinweis": "Abgelegt, aber NICHT gerechnet"}"#.utf8)
    }

    /// Ein Sendeversuch, wie die App ihn fährt: Tor, dann Meldung.
    @discardableResult
    private func sende(_ fach: Parkfach, _ ergebnis: Sendeergebnis) throws -> Parkeintrag? {
        guard let e = fach.naechster, let frei = try fach.beginneSenden(e.schluessel) else {
            return nil
        }
        try fach.melde(frei.schluessel, ergebnis)
        return frei
    }

    // ------------------------------------------------------------ 1 · nach Neustart da

    func testNachEinemNeustartIstDasFachNochDa() throws {
        let fach = try Parkfach(ordner: ordner)
        let a = try fach.parke(png: zeichnung, ueber: "lauf-07.png", name: "Variante A",
                               ordner: "/mappe", jetzt: t0)
        try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(5))

        let wieder = try Parkfach(ordner: ordner)
        XCTAssertEqual(wieder.eintraege.count, 2)
        XCTAssertEqual(wieder.eintraege, fach.eintraege)
        XCTAssertEqual(wieder.naechster?.schluessel, a.schluessel, "die älteste zuerst")
        XCTAssertEqual(wieder.naechster?.ueber, "lauf-07.png")
        XCTAssertEqual(wieder.png(a.schluessel), zeichnung)
        XCTAssertEqual(wieder.wartend, 2)
        XCTAssertEqual(wieder.unlesbar, [])
    }

    func testJedeSkizzeHatIhrenEigenenSchluessel() throws {
        let fach = try Parkfach(ordner: ordner)
        let schluessel = try (0..<20).map { _ in try fach.parke(png: zeichnung).schluessel }
        XCTAssertEqual(Set(schluessel).count, 20)
    }

    // ----------------------------------------------- 2 · angekommen geht nie wieder

    func testEineAngekommeneSkizzeGehtNieEinZweitesMalHinaus() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        try sende(fach, .aus(status: 200, daten: quittung()))

        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand,
                       .angekommen(skizze: "skizze-20260922-081207.png",
                                   hinweis: "Abgelegt, aber NICHT gerechnet"))
        XCTAssertNil(fach.naechster)
        XCTAssertNil(try fach.beginneSenden(e.schluessel), "das Tor bleibt zu")
        XCTAssertFalse(try fach.nochEinmal(e.schluessel), "auch nicht auf Wunsch")
        XCTAssertNil(fach.png(e.schluessel), "die Zeichnung liegt drüben, nicht mehr hier")

        let wieder = try Parkfach(ordner: ordner)
        XCTAssertNil(wieder.naechster)
        XCTAssertNil(try wieder.beginneSenden(e.schluessel))
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.zustand.wort, "angekommen",
                       "die Quittung bleibt stehen")
    }

    func testUnterwegsGehtNichtEinZweitesMalDurchDasTor() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        XCTAssertNotNil(try fach.beginneSenden(e.schluessel))
        XCTAssertNil(try fach.beginneSenden(e.schluessel), "zwei Schleifen, eine Sendung")
        XCTAssertNil(fach.naechster)
        XCTAssertEqual(fach.eintrag(e.schluessel)?.versuche, 1)
    }

    func testEineZweiteMeldungFuerDieselbeSendungAendertNichts() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        _ = try fach.beginneSenden(e.schluessel)
        XCTAssertTrue(try fach.melde(e.schluessel, .aus(status: 200, daten: quittung())))
        XCTAssertFalse(try fach.melde(e.schluessel, .nichtErreicht(grund: "spät")))
        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand.wort, "angekommen")
    }

    func testWasBeimSchliessenUnterwegsWarIstUngewissUndGehtNichtVonSelbst() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        _ = try fach.beginneSenden(e.schluessel)
        // Die App wird hier beendet — keine Meldung mehr.

        let wieder = try Parkfach(ordner: ordner)
        guard case .ungewiss(let grund)? = wieder.eintrag(e.schluessel)?.zustand else {
            return XCTFail("\(String(describing: wieder.eintrag(e.schluessel)?.zustand))")
        }
        XCTAssertTrue(grund.contains("nicht bekannt"), grund)
        XCTAssertNil(wieder.naechster, "nicht von selbst — sie könnte drüben liegen")
        XCTAssertEqual(wieder.png(e.schluessel), zeichnung, "und die Zeichnung ist noch da")

        XCTAssertTrue(try wieder.nochEinmal(e.schluessel), "ein Mensch darf sie schicken")
        XCTAssertEqual(wieder.naechster?.schluessel, e.schluessel)
    }

    // --------------------------------------------- 3 · abgewiesen bleibt mit Grund

    func testEineAbgewieseneBleibtMitGrundLiegen() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        let satz = "Was ankam, ist kein PNG. Die Fläche legt nur ab, was sie auch erkennt."
        try sende(fach, .aus(status: 400, daten: Data(#"{"fehler": "\#(satz)"}"#.utf8)))

        let wieder = try Parkfach(ordner: ordner)
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.zustand, .abgewiesen(grund: satz, code: 400))
        XCTAssertEqual(wieder.png(e.schluessel), zeichnung, "nicht still verworfen")
        XCTAssertNil(wieder.naechster, "und nicht endlos wieder hinaus")
        XCTAssertEqual(wieder.eintraege.count, 1)
    }

    func testNichtErreichtFaelltZurueckInsFachUndGehtWiederHinaus() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        try sende(fach, .ohneVerbindung(grund: "Die HomeStation nimmt keine Verbindung an.",
                                        gesendeteBytes: 0))
        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand, .geparkt)
        XCTAssertEqual(fach.eintrag(e.schluessel)?.letzterGrund,
                       "Die HomeStation nimmt keine Verbindung an.")
        XCTAssertEqual(fach.naechster?.schluessel, e.schluessel)

        try sende(fach, .aus(status: 200, daten: quittung()))
        XCTAssertEqual(fach.eintrag(e.schluessel)?.versuche, 2)
        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand.wort, "angekommen")
    }

    func testMitGesendetenBytesUndOhneAntwortIstEsUngewiss() throws {
        XCTAssertEqual(Sendeergebnis.ohneVerbindung(grund: "abgerissen", gesendeteBytes: 4096),
                       .ohneAntwort(grund: "abgerissen"))
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        try sende(fach, .ohneVerbindung(grund: "abgerissen", gesendeteBytes: 4096))
        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand, .ungewiss(grund: "abgerissen"))
        XCTAssertNil(fach.naechster)
    }

    func testDieAntwortEntscheidetWasAusDerSkizzeWird() {
        XCTAssertEqual(Sendeergebnis.aus(status: 401, daten: Data(#"{"fehler": "Nicht angemeldet."}"#.utf8)),
                       .nichtAngemeldet(grund: "Nicht angemeldet."))
        XCTAssertEqual(Sendeergebnis.aus(status: 404, daten: Data(#"{"fehler": "Unbekannter Weg: /api/skizze"}"#.utf8)),
                       .abgewiesen(grund: "Unbekannter Weg: /api/skizze", code: 404))
        // EIN ERFOLG, DER SICH NICHT LESEN LAESST, IST NICHT «ANGEKOMMEN».
        guard case .ohneAntwort = Sendeergebnis.aus(status: 200, daten: Data("ok".utf8)) else {
            return XCTFail("eine unlesbare 200 darf nicht als angekommen gelten")
        }
    }

    func testVerwerfenNurAufWunschUndNieUnterwegs() throws {
        let fach = try Parkfach(ordner: ordner)
        let a = try fach.parke(png: zeichnung, jetzt: t0)
        let b = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(1))
        _ = try fach.beginneSenden(a.schluessel)
        XCTAssertFalse(try fach.verwirf(a.schluessel), "unterwegs wird nicht verworfen")
        XCTAssertTrue(try fach.verwirf(b.schluessel))

        let wieder = try Parkfach(ordner: ordner)
        XCTAssertNil(wieder.eintrag(b.schluessel), "verworfen bleibt verworfen")
        XCTAssertNotNil(wieder.eintrag(a.schluessel))
    }

    // ---------------------------------------------------------- Abbrüche auf der Platte

    func testEineZeichnungOhneEintragWirdAufgenommenNichtUebergangen() throws {
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
        let stamm = UUID().uuidString
        try zeichnung.write(to: ordner.appendingPathComponent(stamm + ".png"))

        let fach = try Parkfach(ordner: ordner)
        XCTAssertEqual(fach.naechster?.schluessel, stamm)
        XCTAssertEqual(fach.png(stamm), zeichnung)
        XCTAssertEqual(try Parkfach(ordner: ordner).eintraege.count, 1, "nur einmal aufgenommen")
    }

    func testEinUnlesbarerEintragWirdGemeldetUndNichtGeloescht() throws {
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
        let stamm = UUID().uuidString
        let datei = ordner.appendingPathComponent(stamm + ".json")
        try Data("{kaputt".utf8).write(to: datei)
        try zeichnung.write(to: ordner.appendingPathComponent(stamm + ".png"))

        let fach = try Parkfach(ordner: ordner)
        XCTAssertEqual(fach.unlesbar, [stamm + ".json"])
        XCTAssertTrue(fach.eintraege.isEmpty, "die Zeichnung wird nicht als verwaist neu erfunden")
        XCTAssertTrue(FileManager.default.fileExists(atPath: datei.path))
    }

    // ------------------------------------------------------------ die Flugbahn

    func testDieMarkeErreichtDasZielErstMitDerBestaetigung() {
        // Regel 3: Keine Phase vor der Antwort bringt die Marke ans Ziel.
        let vorher: [Flugbahn.Phase] = [.ablegen, .abheben, .warten, .zurueck,
                                        .flug(gesendet: 0, gesamt: 100),
                                        .flug(gesendet: 100, gesamt: 100),
                                        .flug(gesendet: 500, gesamt: 100),
                                        .flug(gesendet: 50, gesamt: nil)]
        for p in vorher {
            XCTAssertLessThanOrEqual(Flugbahn.ort(p), Flugbahn.haltepunkt, "\(p)")
            XCTAssertLessThan(Flugbahn.ort(p), 1, "\(p)")
        }
        XCTAssertEqual(Flugbahn.ort(.eingerastet), 1)
    }

    func testOhneZaehlungBewegtSichNichtsSondernAtmet() {
        // Regeln 1 und 2: Der Ort folgt den gezählten Bytes, und nur ihnen.
        let a = Flugbahn.ort(.flug(gesendet: 10, gesamt: nil))
        let b = Flugbahn.ort(.flug(gesendet: 90_000, gesamt: nil))
        XCTAssertEqual(a, b)
        XCTAssertEqual(a, Flugbahn.ort(.abheben))
        XCTAssertTrue(Flugbahn.atmet(.flug(gesendet: 10, gesamt: nil)))
        XCTAssertTrue(Flugbahn.atmet(.flug(gesendet: 10, gesamt: 0)))
        XCTAssertNil(Flugbahn.anteil(.flug(gesendet: 10, gesamt: 0)))

        XCTAssertFalse(Flugbahn.atmet(.flug(gesendet: 10, gesamt: 100)))
        XCTAssertLessThan(Flugbahn.ort(.flug(gesendet: 10, gesamt: 100)),
                          Flugbahn.ort(.flug(gesendet: 60, gesamt: 100)))
        XCTAssertEqual(Flugbahn.anteil(.flug(gesendet: 25, gesamt: 100)), 0.25)
        XCTAssertTrue(Flugbahn.atmet(.warten))
    }

    func testImAbbruchFaelltDieMarkeZurueckAufsIpad() {
        XCTAssertEqual(Flugbahn.ort(.zurueck), 0)
        XCTAssertFalse(Flugbahn.atmet(.zurueck), "nach dem Abbruch bewegt sich nichts mehr")
    }
}
