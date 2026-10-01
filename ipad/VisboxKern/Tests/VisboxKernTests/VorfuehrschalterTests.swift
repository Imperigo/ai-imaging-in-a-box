import Foundation
import XCTest
import VisboxKern

/// Der Vorführschalter — **jeder Übergang einzeln**, mit einer Uhr, die die Probe selbst
/// vorrückt.
final class VorfuehrschalterTests: XCTestCase {

    private let t0 = Date(timeIntervalSinceReferenceDate: 812_000_000)
    private let weg = Versuchsausgang.keineAntwort(grund: "Frist abgelaufen")

    private func t(_ s: TimeInterval) -> Date { t0.addingTimeInterval(s) }

    /// Ein Schalter, der einmal verbunden war (bei t0).
    private func verbunden() -> Vorfuehrschalter {
        var s = Vorfuehrschalter(start: t0)
        s.melde(.antwort, jetzt: t0)
        return s
    }

    // ------------------------------------------------------------------ der Start

    func testBeimStartIstDerErsteVersuchSofortFaellig() {
        let s = Vorfuehrschalter(start: t0)
        XCTAssertEqual(s.lage, .startet)
        XCTAssertTrue(s.faellig(jetzt: t0))
        XCTAssertFalse(s.imVorfuehrmodus)
        XCTAssertFalse(s.rechnenMoeglich, "ohne Antwort wird nicht gerechnet")
        XCTAssertNil(s.letzterVersuch)
    }

    /// Beim Start ohne Leitung: **nie sofort** — erst nach der Schwelle.
    func testBeimStartOhneLeitungNichtSofortSondernNachDerSchwelle() {
        var s = Vorfuehrschalter(start: t0)
        s.melde(weg, jetzt: t(0.2))
        XCTAssertEqual(s.lage, .startet, "ein Fehlschlag ist ein Ruckler")
        XCTAssertEqual(s.seit, t0, "beim Start zählt die Stille ab dem Start")
        s.ticke(jetzt: t(4))
        XCTAssertEqual(s.lage, .startet)
        s.melde(weg, jetzt: t(5.2))
        XCTAssertEqual(s.lage, .vorfuehrung, "zwei Fehlschläge in Folge")
        XCTAssertEqual(s.seit, t0)
        XCTAssertTrue(s.imVorfuehrmodus)
    }

    func testBeimStartMitHaengendemVersuchNachZehnSekunden() {
        var s = Vorfuehrschalter(start: t0)
        s.ticke(jetzt: t(9.9))
        XCTAssertEqual(s.lage, .startet)
        s.ticke(jetzt: t(10))
        XCTAssertEqual(s.lage, .vorfuehrung)
    }

    func testBeimStartMitAntwortVerbunden() {
        var s = Vorfuehrschalter(start: t0)
        s.melde(weg, jetzt: t(0.1))
        s.melde(.antwort, jetzt: t(5))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertEqual(s.seit, t(5))
        XCTAssertEqual(s.fehlschlaege, 0)
        XCTAssertTrue(s.rechnenMoeglich)
        XCTAssertEqual(s.naechsterVersuch, t(5 + Vorfuehrschalter.lebenszeichenAbstand))
    }

    // ------------------------------------------------------- verbunden → getrennt

    func testDerErsteFehlschlagNachEinerAntwortIstGetrenntSeit() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        XCTAssertEqual(s.lage, .getrennt)
        XCTAssertEqual(s.seit, t(30), "«getrennt seit» beginnt beim ersten Fehlschlag")
        XCTAssertEqual(s.fehlschlaege, 1)
        XCTAssertEqual(s.letzterGrund, "Frist abgelaufen")
        XCTAssertFalse(s.rechnenMoeglich, "schon getrennt wird nicht mehr gerechnet")
        XCTAssertFalse(s.imVorfuehrmodus)
        XCTAssertEqual(s.naechsterVersuch, t(35))
    }

    func testGetrenntWirdNachZweiFehlschlaegenVorfuehrung() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.melde(weg, jetzt: t(35))
        XCTAssertEqual(s.lage, .vorfuehrung)
        XCTAssertEqual(s.seit, t(30), "seit dem ersten Fehlschlag, nicht seit dem Umschalten")
    }

    func testGetrenntWirdNachZehnSekundenVorfuehrung() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.ticke(jetzt: t(39.9))
        XCTAssertEqual(s.lage, .getrennt)
        s.ticke(jetzt: t(40))
        XCTAssertEqual(s.lage, .vorfuehrung)
    }

    func testGetrenntUndWiederDaOhneVorfuehrung() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.melde(.antwort, jetzt: t(35))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertEqual(s.seit, t(35))
        XCTAssertEqual(s.fehlschlaege, 0)
        // UND EIN NEUER FEHLSCHLAG BEGINNT VON VORN, nicht beim alten Zähler.
        s.melde(weg, jetzt: t(45))
        XCTAssertEqual(s.lage, .getrennt)
        XCTAssertEqual(s.naechsterVersuch, t(50))
    }

    // ------------------------------------------------- zurück nur mit Bestätigung

    func testAusDerVorfuehrungZurueckErstNachEinerBestaetigtenAntwort() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.melde(weg, jetzt: t(35))
        XCTAssertEqual(s.lage, .vorfuehrung)
        s.melde(.unbestaetigt(grund: "Fehlerseite der Weiterleitung"), jetzt: t(45))
        XCTAssertEqual(s.lage, .vorfuehrung, "eine unbestätigte Antwort holt nicht zurück")
        XCTAssertEqual(s.letzterGrund, "Fehlerseite der Weiterleitung")
        s.ticke(jetzt: t(300))
        XCTAssertEqual(s.lage, .vorfuehrung, "die Zeit allein holt nicht zurück")
        s.melde(.antwort, jetzt: t(301))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertTrue(s.rechnenMoeglich)
        XCTAssertEqual(s.letzteAntwort, t(301))
        XCTAssertNil(s.letzterGrund)
    }

    func testUnbestaetigtZaehltWieEinFehlschlag() {
        var s = verbunden()
        s.melde(.unbestaetigt(grund: "unlesbar"), jetzt: t(30))
        XCTAssertEqual(s.lage, .getrennt)
        s.melde(.unbestaetigt(grund: "unlesbar"), jetzt: t(35))
        XCTAssertEqual(s.lage, .vorfuehrung)
    }

    /// Bestätigt ist nur der Laufstand des Visbox-Servers — nicht jede 200.
    func testBestaetigtIstNurDerLaufstandDesServers() {
        XCTAssertEqual(Versuchsausgang.aus(status: 200, daten: Data(#"{"laeuft": false, "ordner": null}"#.utf8)),
                       .antwort)
        XCTAssertEqual(Versuchsausgang.aus(status: 200, daten: Data(#"{"laeuft": true}"#.utf8)), .antwort)
        for (status, rumpf) in [(200, #"{"ok": true}"#), (200, #"{"laeuft": 1}"#), (200, "<html>"),
                                (200, "[]"), (502, "Bad Gateway"),
                                (401, #"{"fehler": "Anmeldung fehlt"}"#)] {
            guard case .unbestaetigt(let grund) = Versuchsausgang.aus(status: status, daten: Data(rumpf.utf8)) else {
                XCTFail("\(status) \(rumpf) galt als bestätigt")
                continue
            }
            XCTAssertFalse(grund.isEmpty)
        }
        guard case .unbestaetigt(let grund) = Versuchsausgang.aus(
            status: 401, daten: Data(#"{"fehler": "Anmeldung fehlt"}"#.utf8)) else { return XCTFail() }
        XCTAssertEqual(grund, "Anmeldung fehlt", "der Satz des Servers, unverändert")
    }

    // ----------------------------------------------------- der wachsende Abstand

    func testDerAbstandWaechstVonFuenfBisSechzig() {
        XCTAssertEqual((0..<8).map { Vorfuehrschalter.abstand(stufe: $0) },
                       [5, 10, 20, 40, 60, 60, 60, 60])
        XCTAssertEqual(Vorfuehrschalter.abstand(stufe: 10_000), 60, "kein Überlauf")
        var s = verbunden()
        var jetzt: TimeInterval = 30
        var abstaende: [TimeInterval] = []
        for _ in 0..<6 {
            s.melde(weg, jetzt: t(jetzt))
            abstaende.append(s.naechsterVersuch.timeIntervalSince(t(jetzt)))
            XCTAssertEqual(s.letzterVersuch, t(jetzt))
            XCTAssertFalse(s.faellig(jetzt: t(jetzt + abstaende.last! - 0.1)))
            XCTAssertTrue(s.faellig(jetzt: t(jetzt + abstaende.last!)))
            jetzt += abstaende.last!
        }
        XCTAssertEqual(abstaende, [5, 10, 20, 40, 60, 60])
    }

    func testErneutVerbindenSetztDenAbstandZurueckUndBleibtImVorfuehrmodus() {
        var s = verbunden()
        for i in 0..<5 { s.melde(weg, jetzt: t(30 + Double(i))) }
        XCTAssertEqual(s.abstand, 60)
        s.erneutVerbinden(jetzt: t(100))
        XCTAssertTrue(s.faellig(jetzt: t(100)), "der nächste Versuch sofort")
        XCTAssertEqual(s.lage, .vorfuehrung, "verlangt ist nicht verbunden")
        s.melde(weg, jetzt: t(100.5))
        XCTAssertEqual(s.naechsterVersuch, t(105.5), "wieder ab 5 s")
        s.melde(weg, jetzt: t(105.5))
        XCTAssertEqual(s.naechsterVersuch, t(115.5), "dann 10 s")
        s.erneutVerbinden(jetzt: t(110))
        s.melde(.antwort, jetzt: t(110.3))
        XCTAssertEqual(s.lage, .verbunden)
    }

    func testDieFristEinesVersuchsLiegtUnterDerZeitschwelle() {
        XCTAssertLessThan(Vorfuehrschalter.versuchsfrist, Vorfuehrschalter.schwelleSekunden)
        XCTAssertGreaterThanOrEqual(Vorfuehrschalter.schwelleFehlschlaege, 2, "nie sofort")
    }

    // ------------------------------------------------------------ Sätze und Farben

    func testDieSaetzeStehenSoAufDemBlatt() {
        let zone = TimeZone(secondsFromGMT: 2 * 3600)!
        // 14:02 Ortszeit (UTC+2) — t0 liegt auf einer vollen Minute.
        var k = Calendar(identifier: .gregorian)
        k.timeZone = zone
        let seit = k.date(from: DateComponents(year: 2026, month: 10, day: 28, hour: 14, minute: 2))!
        XCTAssertEqual(Vorfuehrsaetze.band(seit: seit, zone: zone),
                       "Der Heim-PC antwortet nicht (seit 14:02). Gezeigt werden Bilder, die "
                       + "vorher gerechnet wurden — neue Läufe sind nicht möglich.")
        XCTAssertEqual(Vorfuehrsaetze.leitung(seit: seit, letzterVersuch: seit.addingTimeInterval(100),
                                              jetzt: seit.addingTimeInterval(120), zone: zone),
                       "Leitung zum Heim-PC: keine Antwort seit 14:02. Letzter Versuch vor 20 s.")
        XCTAssertEqual(Vorfuehrsaetze.leitung(seit: seit, letzterVersuch: nil, jetzt: seit, zone: zone),
                       "Leitung zum Heim-PC: keine Antwort seit 14:02. Noch kein Versuch zurück.")
        XCTAssertEqual(Vorfuehrsaetze.vorWieLange(seit, jetzt: seit.addingTimeInterval(200), zone: zone), "vor 3 min")
        XCTAssertEqual(Vorfuehrsaetze.vorWieLange(seit, jetzt: seit.addingTimeInterval(7200), zone: zone), "um 14:02")
        XCTAssertEqual(Vorfuehrsaetze.vorWieLange(seit, jetzt: seit.addingTimeInterval(-5), zone: zone), "vor 0 s",
                       "eine Uhr, die zurückspringt, macht keine negative Zeit")
        XCTAssertEqual(Vorfuehrsaetze.assistent, "Assistent: läuft am Heim-PC, darum ebenfalls nicht da.")
        XCTAssertEqual(Vorfuehrsaetze.ipadVerbunden, "iPad: verbunden mit diesem Mac — zeichnen und zeigen geht.")
        XCTAssertTrue(Vorfuehrsaetze.kasten.hasPrefix("Violett heisst hier: nichts auf diesem Schirm ist gerade gerechnet."))
        XCTAssertFalse((Vorfuehrsaetze.kasten + Vorfuehrsaetze.rechnenSatz).contains("ß"), "Schweizer Schreibung")
    }

    func testVioletHeisstNurVorfuehrung() {
        XCTAssertEqual(Vorfuehrfarbe.violett.hex, "#a996e0")
        XCTAssertEqual(Vorfuehrfarbe.rand.hex, "#5b4f7a")
        XCTAssertEqual(Vorfuehrfarbe.grund.hex, "#1d1a26")
        XCTAssertEqual(Vorfuehrfarbe.geht.hex, "#4ea373")
        XCTAssertEqual(Vorfuehrfarbe.gehtNicht.hex, "#e2776f")
        // DIESELBE FARBE DARF NIE ZWEI DINGE HEISSEN: Violett ist kein Urteil und kein Grund.
        let belegt = Set(Zeichenart.allCases.flatMap { [$0.rand, $0.schrift] } + Blattfarbe.grundfarben)
        for ton in [Vorfuehrfarbe.violett, Vorfuehrfarbe.rand, Vorfuehrfarbe.grund] {
            XCTAssertFalse(belegt.contains(ton), ton.hex)
        }
        // LESBAR: die violette Schrift auf dem Band, die helle Schrift auch.
        XCTAssertGreaterThanOrEqual(Farbton.kontrast(Vorfuehrfarbe.violett, Vorfuehrfarbe.grund), 4.5)
        XCTAssertGreaterThanOrEqual(Farbton.kontrast(Blattfarbe.schrift, Vorfuehrfarbe.grund), 4.5)
        XCTAssertGreaterThanOrEqual(Farbton.kontrast(Vorfuehrfarbe.violett, Blattfarbe.grund), 4.5)
    }
}
