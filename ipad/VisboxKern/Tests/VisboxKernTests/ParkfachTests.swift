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
        guard let e = fach.naechster, let frei = try fach.beginneSenden(e.schluessel, abgebrochen: false) else {
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
        XCTAssertNil(try fach.beginneSenden(e.schluessel, abgebrochen: false), "das Tor bleibt zu")
        XCTAssertFalse(try fach.nochEinmal(e.schluessel), "auch nicht auf Wunsch")
        XCTAssertNil(fach.png(e.schluessel), "die Zeichnung liegt drüben, nicht mehr hier")

        let wieder = try Parkfach(ordner: ordner)
        XCTAssertNil(wieder.naechster)
        XCTAssertNil(try wieder.beginneSenden(e.schluessel, abgebrochen: false))
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.zustand.wort, "angekommen",
                       "die Quittung bleibt stehen")
    }

    func testUnterwegsGehtNichtEinZweitesMalDurchDasTor() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        XCTAssertNotNil(try fach.beginneSenden(e.schluessel, abgebrochen: false))
        XCTAssertNil(try fach.beginneSenden(e.schluessel, abgebrochen: false), "zwei Schleifen, eine Sendung")
        XCTAssertNil(fach.naechster)
        XCTAssertEqual(fach.eintrag(e.schluessel)?.versuche, 1)
    }

    func testEineZweiteMeldungFuerDieselbeSendungAendertNichts() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        _ = try fach.beginneSenden(e.schluessel, abgebrochen: false)
        XCTAssertTrue(try fach.melde(e.schluessel, .aus(status: 200, daten: quittung())))
        XCTAssertFalse(try fach.melde(e.schluessel, .nichtErreicht(grund: "spät")))
        XCTAssertEqual(fach.eintrag(e.schluessel)?.zustand.wort, "angekommen")
    }

    /// Seit dem 22.09.2026 geht eine ungewisse Skizze **mit Schlüssel** von selbst noch
    /// einmal: Der Server erkennt den Schlüssel und legt keine zweite Datei an
    /// (Protokoll §3). Bis dahin wartete sie auf einen Menschen.
    func testWasBeimSchliessenUnterwegsWarIstUngewissUndGehtMitSchluesselVonSelbst() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        _ = try fach.beginneSenden(e.schluessel, abgebrochen: false)
        // Die App wird hier beendet — keine Meldung mehr.

        let wieder = try Parkfach(ordner: ordner)
        let nach = try XCTUnwrap(wieder.eintrag(e.schluessel))
        guard case .ungewiss(let grund) = nach.zustand else {
            return XCTFail("\(nach.zustand)")
        }
        XCTAssertTrue(grund.contains("nicht bekannt"), grund)
        XCTAssertEqual(nach.schluesselGesendet, true, "am Tor festgehalten, vor dem Senden")
        XCTAssertEqual(wieder.png(e.schluessel), zeichnung, "und die Zeichnung ist noch da")
        XCTAssertEqual(wieder.naechster?.schluessel, e.schluessel, "mit Schlüssel: von selbst")
        XCTAssertEqual(wieder.wartend, 1)
        XCTAssertEqual(wieder.brauchenEntscheid, 0)

        // Die Wiederholung geht durch das Tor, und die Antwort macht ein Wissen daraus.
        let frei = try XCTUnwrap(try wieder.beginneSenden(e.schluessel, abgebrochen: false))
        XCTAssertEqual(frei.versuche, 2)
        try wieder.melde(e.schluessel, .aus(status: 200, daten: quittung()))
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.zustand.wort, "angekommen")
    }

    /// Ein Eintrag aus der Fassung vor dem 22.09.2026 kennt das Feld nicht: **Ob** der
    /// Schlüssel mitging, ist nicht bekannt — dann entscheidet weiter ein Mensch.
    func testUngewissOhneBekanntenSchluesselWartetAufEinenMenschen() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        try sende(fach, .ohneVerbindung(grund: "abgerissen", gesendeteBytes: 4096))

        // DIE ALTE FORM: dasselbe JSON ohne «schluesselGesendet».
        let datei = ordner.appendingPathComponent(e.schluessel + ".json")
        var roh = try XCTUnwrap(try JSONSerialization.jsonObject(
            with: Data(contentsOf: datei)) as? [String: Any])
        XCTAssertNotNil(roh.removeValue(forKey: "schluesselGesendet"), "das Feld steht auf der Platte")
        try JSONSerialization.data(withJSONObject: roh).write(to: datei)

        let wieder = try Parkfach(ordner: ordner)
        let alt = try XCTUnwrap(wieder.eintrag(e.schluessel))
        XCTAssertNil(alt.schluesselGesendet, "nicht bekannt — und nicht still «nein»")
        XCTAssertEqual(alt.zustand, .ungewiss(grund: "abgerissen"))
        XCTAssertNil(wieder.naechster, "nicht von selbst — sie könnte drüben liegen")
        XCTAssertNil(try wieder.beginneSenden(e.schluessel, abgebrochen: false), "auch nicht am Tor vorbei")
        XCTAssertEqual(wieder.brauchenEntscheid, 1)

        XCTAssertTrue(try wieder.nochEinmal(e.schluessel), "ein Mensch darf sie schicken")
        XCTAssertEqual(wieder.naechster?.schluessel, e.schluessel)
    }

    func testUngewissGehtNurBegrenztOftVonSelbstDannEntscheidetEinMensch() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung)
        var gesendet = 0
        while try sende(fach, .ohneAntwort(grund: "unlesbar")) != nil {
            gesendet += 1
            XCTAssertLessThanOrEqual(gesendet, Parkfach.selbstHoechstens, "endlos")
            if gesendet > Parkfach.selbstHoechstens { break }
        }
        XCTAssertEqual(gesendet, Parkfach.selbstHoechstens)
        let nach = try XCTUnwrap(fach.eintrag(e.schluessel))
        XCTAssertFalse(nach.gehtVonSelbst)
        XCTAssertTrue(nach.brauchtEntscheid)
        XCTAssertTrue(try fach.nochEinmal(e.schluessel), "ein Mensch darf weiter")
        XCTAssertNotNil(try fach.beginneSenden(e.schluessel, abgebrochen: false))
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
        XCTAssertEqual(fach.naechster?.schluessel, e.schluessel,
                       "ungewiss, aber mit Schlüssel — geht von selbst noch einmal")
    }

    // --------------------------------------------- 4 · das Fach wächst nicht ohne Ende

    private func angekommen(_ fach: Parkfach, am zeit: Date) throws -> Parkeintrag {
        let e = try fach.parke(png: zeichnung, jetzt: zeit)
        _ = try XCTUnwrap(try fach.beginneSenden(e.schluessel, abgebrochen: false, jetzt: zeit))
        try fach.melde(e.schluessel, .aus(status: 200, daten: quittung()), jetzt: zeit)
        return e
    }

    func testAngekommeneGehenNachSiebenTagenWartendeNie() throws {
        let tag: TimeInterval = 24 * 3600
        let fach = try Parkfach(ordner: ordner)
        let a = try angekommen(fach, am: t0)
        let wartet = try fach.parke(png: zeichnung, jetzt: t0)
        try sende(fach, .aus(status: 400, daten: Data(#"{"fehler": "zu gross"}"#.utf8)))
        let abgewiesen = try XCTUnwrap(fach.eintraege.first { $0.brauchtEntscheid })
        let nochDa = try fach.parke(png: zeichnung, jetzt: t0)
        XCTAssertNotEqual(wartet.schluessel, nochDa.schluessel)

        let nachSechs = try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(6 * tag))
        XCTAssertNotNil(nachSechs.eintrag(a.schluessel), "eine Woche steht die Quittung")

        let nachAcht = try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(8 * tag))
        XCTAssertNil(nachAcht.eintrag(a.schluessel))
        XCTAssertFalse(FileManager.default.fileExists(
            atPath: ordner.appendingPathComponent(a.schluessel + ".json").path),
                       "auch von der Platte")
        XCTAssertNotNil(nachAcht.eintrag(abgewiesen.schluessel), "abgewiesen wartet auf einen Menschen")
        XCTAssertNotNil(nachAcht.eintrag(nochDa.schluessel), "geparkt wartet auf das Senden")
        XCTAssertEqual(nachAcht.eintraege.count, 2)
    }

    func testHoechstensFuenfzigAngekommeneBleibenDieAeltestenGehen() throws {
        let fach = try Parkfach(ordner: ordner)
        let zahl = Parkfach.angekommenHoechstens + 3
        var alle: [Parkeintrag] = []
        for i in 0..<zahl {
            alle.append(try angekommen(fach, am: t0.addingTimeInterval(Double(i))))
        }
        XCTAssertEqual(fach.eintraege.count, Parkfach.angekommenHoechstens)
        for alt in alle.prefix(3) {
            XCTAssertNil(fach.eintrag(alt.schluessel), "die ältesten gehen zuerst")
        }
        XCTAssertNotNil(fach.eintrag(alle[3].schluessel))
        XCTAssertEqual(try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(Double(zahl)))
            .eintraege.count, Parkfach.angekommenHoechstens, "auch nach dem Neustart")
    }

    // ------------------------ 4b · das Aufräumen bringt nichts zu Fall (22.09.2026)

    /// Ein Löschen, das für genau eine Datei scheitert. Unter Linux als Verwalter gibt es
    /// keine Datei, die sich nicht löschen lässt (Schreibschutz wirkt nicht, und ein nicht
    /// leerer Ordner an ihrer Stelle wird mitgelöscht) — darum hier gesetzt.
    private func klemmt(_ name: String) -> (URL) throws -> Void {
        { url in
            if url.lastPathComponent == name { throw CocoaError(.fileWriteNoPermission) }
            try FileManager.default.removeItem(at: url)
        }
    }

    func testEinNichtLoeschbarerAlterEintragHaeltDasOeffnenNichtAuf() throws {
        let tag: TimeInterval = 24 * 3600
        let fach = try Parkfach(ordner: ordner)
        let alt = try angekommen(fach, am: t0)
        let wartet = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(1))
        let datei = ordner.appendingPathComponent(alt.schluessel + ".json")

        // Acht Tage spaeter: Die Quittung soll gehen, laesst sich aber nicht loeschen.
        let wieder = try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(8 * tag),
                                  loesche: klemmt(alt.schluessel + ".json"))
        XCTAssertEqual(wieder.naechster?.schluessel, wartet.schluessel,
                       "das Fach ist offen, und die geparkte Skizze wartet")
        XCTAssertEqual(wieder.png(wartet.schluessel), zeichnung)
        XCTAssertNotNil(wieder.eintrag(alt.schluessel), "die Quittung bleibt stehen, wie auf der Platte")
        XCTAssertTrue(FileManager.default.fileExists(atPath: datei.path))
        let fehler = try XCTUnwrap(wieder.aufraeumFehler, "der Fehler steht im Feld")
        XCTAssertTrue(fehler.contains(alt.schluessel), fehler)

        // Und sie geht hinaus.
        try sende(wieder, .aus(status: 200, daten: quittung()))
        XCTAssertEqual(wieder.eintrag(wartet.schluessel)?.zustand.wort, "angekommen")

        // Laesst sich die Datei wieder loeschen, geht sie beim naechsten Oeffnen — und das
        // Feld ist leer.
        let danach = try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(8 * tag))
        XCTAssertNil(danach.eintrag(alt.schluessel))
        XCTAssertNil(danach.aufraeumFehler)
    }

    func testEineAnkunftGiltAuchWennDasAufraeumenDanachScheitert() throws {
        let tag: TimeInterval = 24 * 3600
        let alt = UUID().uuidString
        let fach = try Parkfach(ordner: ordner, loesche: klemmt(alt + ".json"))
        // Eine alte Quittung unter dem Namen, dessen Loeschen scheitert.
        let a = try fach.parke(png: zeichnung, jetzt: t0)
        _ = try XCTUnwrap(try fach.beginneSenden(a.schluessel, abgebrochen: false, jetzt: t0))
        try fach.melde(a.schluessel, .aus(status: 200, daten: quittung()), jetzt: t0)
        let quelle = ordner.appendingPathComponent(a.schluessel + ".json")
        var roh = try XCTUnwrap(try JSONSerialization.jsonObject(
            with: Data(contentsOf: quelle)) as? [String: Any])
        roh["schluessel"] = alt
        try JSONSerialization.data(withJSONObject: roh)
            .write(to: ordner.appendingPathComponent(alt + ".json"))
        try FileManager.default.removeItem(at: quelle)

        let offen = try Parkfach(ordner: ordner, jetzt: t0, loesche: klemmt(alt + ".json"))
        XCTAssertNotNil(offen.eintrag(alt))
        let neu = try offen.parke(png: zeichnung, jetzt: t0.addingTimeInterval(8 * tag))
        _ = try XCTUnwrap(try offen.beginneSenden(neu.schluessel, abgebrochen: false,
                                                   jetzt: t0.addingTimeInterval(8 * tag)))
        XCTAssertTrue(try offen.melde(neu.schluessel, .aus(status: 200, daten: quittung()),
                                      jetzt: t0.addingTimeInterval(8 * tag)),
                      "die Meldung gilt — sie wirft nicht wegen des Aufraeumens")
        XCTAssertNotNil(offen.aufraeumFehler)
        XCTAssertEqual(try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(8 * tag),
                                    loesche: klemmt(alt + ".json"))
            .eintrag(neu.schluessel)?.zustand.wort, "angekommen", "auf der Platte")
    }

    /// Ohne gesetztes Scheitern, an der Platte: Hat jemand eine alte Quittung schon
    /// entfernt, ist erreicht, was das Aufräumen wollte — kein Fehler, kein Wurf.
    func testEineSchonEntfernteQuittungGiltAlsAufgeraeumt() throws {
        let tag: TimeInterval = 24 * 3600
        let fach = try Parkfach(ordner: ordner)
        let alt = try angekommen(fach, am: t0)
        try FileManager.default.removeItem(
            at: ordner.appendingPathComponent(alt.schluessel + ".json"))

        let neu = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(8 * tag))
        _ = try XCTUnwrap(try fach.beginneSenden(neu.schluessel, abgebrochen: false,
                                                  jetzt: t0.addingTimeInterval(8 * tag)))
        XCTAssertTrue(try fach.melde(neu.schluessel, .aus(status: 200, daten: quittung()),
                                     jetzt: t0.addingTimeInterval(8 * tag)))
        XCTAssertNil(fach.eintrag(alt.schluessel))
        XCTAssertNil(fach.aufraeumFehler)
    }

    // --------------------------------------- das Tor nach dem Vorspiel (22.09.2026)

    func testEinAbbruchVorDemTorLaesstDenEintragUnberuehrt() throws {
        let fach = try Parkfach(ordner: ordner)
        let e = try fach.parke(png: zeichnung, jetzt: t0)
        XCTAssertNil(try fach.beginneSenden(e.schluessel, abgebrochen: true,
                                            jetzt: t0.addingTimeInterval(1)))

        // Auf der Platte, nach einem Neustart: nicht unterwegs gewesen, also nicht ungewiss.
        let wieder = try Parkfach(ordner: ordner, jetzt: t0.addingTimeInterval(2))
        let nach = try XCTUnwrap(wieder.eintrag(e.schluessel))
        XCTAssertEqual(nach.zustand, .geparkt)
        XCTAssertEqual(nach.versuche, 0, "kein Versuch gezaehlt")
        XCTAssertNil(nach.schluesselGesendet, "nichts ging hinaus, also auch kein Schluessel")
        XCTAssertEqual(nach.geaendert, t0)
        XCTAssertEqual(wieder.naechster?.schluessel, e.schluessel, "sie wartet weiter")

        // Eine ungewisse behaelt ihre Versuche.
        try sende(wieder, .ohneAntwort(grund: "abgerissen"))
        XCTAssertNil(try wieder.beginneSenden(e.schluessel, abgebrochen: true))
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.versuche, 1)
        XCTAssertEqual(wieder.eintrag(e.schluessel)?.zustand, .ungewiss(grund: "abgerissen"))

        // Ohne Abbruch geht sie gleich danach durch das Tor.
        XCTAssertEqual(try wieder.beginneSenden(e.schluessel, abgebrochen: false)?.versuche, 2)
    }

    // ------------------------------------------------ der Knopf zählt getrennt

    func testDerKnopfZaehltUngewisseNichtAlsGeparkt() throws {
        let fach = try Parkfach(ordner: ordner)
        let ungewiss = try fach.parke(png: zeichnung, jetzt: t0)
        let abgewiesen = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(1))
        let unterwegs = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(2))
        let angekommen = try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(3))
        try fach.parke(png: zeichnung, jetzt: t0.addingTimeInterval(4))

        _ = try fach.beginneSenden(ungewiss.schluessel, abgebrochen: false)
        try fach.melde(ungewiss.schluessel, .ohneAntwort(grund: "abgerissen"))
        _ = try fach.beginneSenden(abgewiesen.schluessel, abgebrochen: false)
        try fach.melde(abgewiesen.schluessel, .abgewiesen(grund: "zu gross", code: 400))
        _ = try fach.beginneSenden(angekommen.schluessel, abgebrochen: false)
        try fach.melde(angekommen.schluessel, .aus(status: 200, daten: quittung()))
        _ = try fach.beginneSenden(unterwegs.schluessel, abgebrochen: false)

        XCTAssertEqual(fach.wartend, 2, "von selbst gehen zwei — aber nur eine ist geparkt")
        let z = Fachzaehlung(fach.eintraege)
        XCTAssertEqual(z.geparkt, 1)
        XCTAssertEqual(z.ungewiss, 1)
        XCTAssertEqual(z.unterwegs, 1)
        XCTAssertEqual(z.offen, 1)
        XCTAssertEqual(z.teile.map(\.wort), ["geparkt", "ungewiss", "unterwegs", "offen"])
        XCTAssertEqual(z.teile.map(\.zahl), [1, 1, 1, 1])
        XCTAssertEqual(z.teile.map(\.zahl).reduce(0, +), fach.eintraege.count - 1,
                       "jede ausser der Quittung in genau einem Fach")

        // Nur Quittungen: keine Zahl, keine Null.
        XCTAssertEqual(Fachzaehlung(fach.eintraege.filter { $0.zustand.wort == "angekommen" }).teile, [])
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
        _ = try fach.beginneSenden(a.schluessel, abgebrochen: false)
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

    func testBeimAbhebenWandertDieMarkeAnDenRandZumZiel() {
        // Blatt «Verbindung», Augenblick 2: «Die Marke wandert an den Rand, an dem der
        // Rechner sitzt. Die Richtung ist die Richtung.»
        XCTAssertGreaterThan(Flugbahn.ort(.abheben), Flugbahn.ort(.ablegen), "sie bewegt sich zum Ziel")
        XCTAssertEqual(Flugbahn.ort(.abheben), Flugbahn.rand)
        XCTAssertLessThan(Flugbahn.ort(.abheben), Flugbahn.haltepunkt)
        // Der Flug beginnt am Rand und faellt nicht hinter ihn zurueck.
        XCTAssertEqual(Flugbahn.ort(.flug(gesendet: 0, gesamt: 100)), Flugbahn.rand)
        XCTAssertEqual(Flugbahn.ort(.flug(gesendet: 100, gesamt: 100)), Flugbahn.haltepunkt,
                       accuracy: 1e-12)
    }

    func testImAbbruchFaelltDieMarkeZurueckAufsIpad() {
        XCTAssertEqual(Flugbahn.ort(.zurueck), 0)
        XCTAssertFalse(Flugbahn.atmet(.zurueck), "nach dem Abbruch bewegt sich nichts mehr")
    }

    func testVorDemErstenByteLegtDieMarkeAbUndHebtAb() {
        // Die fünf Augenblicke des Blatts: 1 Ablegen (220 ms), 2 Abheben (180 ms), dann Flug.
        XCTAssertEqual(Flugbahn.vorspiel.map(\.phase), [.ablegen, .abheben])
        XCTAssertEqual(Flugbahn.vorspiel.map(\.dauer), [0.22, 0.18])
    }

    func testDerFlugBeginntUngezaehltUndAtmet() {
        // Kommt kein einziger Zählerstand (ein kleines PNG in einem Stück), muss die Marke
        // trotzdem atmen (Regel 2) — und darf nicht vorankommen (Regel 1).
        XCTAssertTrue(Flugbahn.atmet(Flugbahn.flugbeginn))
        XCTAssertNil(Flugbahn.anteil(Flugbahn.flugbeginn))
        XCTAssertEqual(Flugbahn.ort(Flugbahn.flugbeginn), Flugbahn.ort(.abheben))
        for (phase, _) in Flugbahn.vorspiel {
            XCTAssertFalse(Flugbahn.atmet(phase), "vor dem Senden ist nichts unterwegs")
        }
    }

    func testEinZaehlerstandWirktNurImFlugUndRastetNieEin() {
        // Vor dem Flug und nach ihm ändert ein (später) Zählerstand nichts.
        for p: Flugbahn.Phase in [.ablegen, .abheben, .warten, .eingerastet, .zurueck] {
            XCTAssertNil(Flugbahn.gezaehlt(p, gesendet: 10, gesamt: 100), "\(p)")
        }
        XCTAssertEqual(Flugbahn.gezaehlt(Flugbahn.flugbeginn, gesendet: 40, gesamt: 100),
                       .flug(gesendet: 40, gesamt: 100))
        XCTAssertEqual(Flugbahn.gezaehlt(Flugbahn.flugbeginn, gesendet: 40, gesamt: nil),
                       .flug(gesendet: 40, gesamt: nil))
        // Alles hinaus heisst warten, nicht angekommen (Regel 3).
        XCTAssertEqual(Flugbahn.gezaehlt(.flug(gesendet: 40, gesamt: 100), gesendet: 100,
                                         gesamt: 100), .warten)
    }

    func testOhneBewegungErscheintDieMarkeErstAmZiel() {
        // Blatt: «Die Marke erscheint am Ziel, der Balken bleibt.»
        let unterwegs: [Flugbahn.Phase] = [.ablegen, .abheben, Flugbahn.flugbeginn,
                                           .flug(gesendet: 50, gesamt: 100), .warten]
        for p in unterwegs {
            XCTAssertNil(Flugbahn.ortOhneBewegung(p), "\(p): unterwegs steht sie nirgends")
        }
        XCTAssertEqual(Flugbahn.ortOhneBewegung(.eingerastet), 1)
        XCTAssertEqual(Flugbahn.ortOhneBewegung(.zurueck), 0)
        // Der Balken bleibt: der Anteil hängt nicht an der Bewegung.
        XCTAssertEqual(Flugbahn.anteil(.flug(gesendet: 50, gesamt: 100)), 0.5)
    }
}
