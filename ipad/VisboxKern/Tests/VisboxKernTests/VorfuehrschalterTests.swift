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
                                (404, #"{"fehler": "Unbekannter Weg"}"#)] {
            guard case .unbestaetigt(let grund) = Versuchsausgang.aus(status: status, daten: Data(rumpf.utf8)) else {
                XCTFail("\(status) \(rumpf) galt als bestätigt")
                continue
            }
            XCTAssertFalse(grund.isEmpty)
        }
        guard case .unbestaetigt(let grund) = Versuchsausgang.aus(
            status: 502, daten: Data(#"{"fehler": "Kein Server dahinter"}"#.utf8)) else { return XCTFail() }
        XCTAssertEqual(grund, "Kein Server dahinter", "der Satz des Servers, unverändert")
    }

    // ------------------------------------------- die Absage der Tür (Durchsicht, H2)

    /// 401 und 403 sind die Tür des Heim-PC — er antwortet. Der Grund sagt, was am Mac zu
    /// tun ist (derselbe Satz wie die Startzeile «Leitung»), und dahinter, was der Server sagt.
    func testDieAbsageDerTuerIstAbgewiesenMitDemSatzDerStartzeile() {
        let serversatz = "Nicht angemeldet. Benutzername und Kennwort stehen im Fenster, in dem "
            + "\(Marke.name) gestartet wurde."
        let rumpf = Data(#"{"fehler": "\#(serversatz)"}"#.utf8)
        guard case .abgewiesen(let grund) = Versuchsausgang.aus(status: 401, daten: rumpf) else {
            return XCTFail("401 galt nicht als Absage")
        }
        XCTAssertTrue(grund.hasPrefix("Kennwort stimmt nicht"), grund)
        XCTAssertTrue(grund.contains("«Einrichten»"), "der Satz sagt, was zu tun ist")
        XCTAssertTrue(grund.hasSuffix("Der Heim-PC sagt: «\(serversatz)»"), grund)
        // DERSELBE ANFANG WIE IN DER STARTZEILE: Band und Zeile widersprechen sich nicht.
        guard case .fehlt(let zeile) = Startzeilen.leitung(.antwort(status: 401, millisekunden: 40),
                                                           adresseDa: true, jetzt: t0) else {
            return XCTFail()
        }
        XCTAssertTrue(grund.hasPrefix(zeile))

        guard case .abgewiesen(let ohne) = Versuchsausgang.aus(status: 403, daten: Data("<html>".utf8))
        else { return XCTFail("403 galt nicht als Absage") }
        XCTAssertTrue(ohne.contains("Weiterleitung"), ohne)
        XCTAssertFalse(ohne.contains("Der Heim-PC sagt"), "ohne lesbaren Satz des Servers nur der eigene")
    }

    /// Der Ablauf aus der Durchsicht: falsches Kennwort beim Start. Früher nach zwei Versuchen
    /// Vorführmodus («antwortet nicht»), ohne Weg zu «Einrichten».
    func testEineAbsageLoestDenVorfuehrmodusNieAus() {
        var s = Vorfuehrschalter(start: t0)
        let absage = Versuchsausgang.abgewiesen(grund: "Kennwort stimmt nicht")
        for i in 0..<6 {
            s.melde(absage, jetzt: t(Double(i) * 5 + 0.2))
            s.ticke(jetzt: t(Double(i) * 5 + 4.9))
            XCTAssertEqual(s.lage, .abgewiesen)
        }
        s.ticke(jetzt: t(600))
        XCTAssertEqual(s.lage, .abgewiesen, "auch die Zeitschwelle schaltet nicht")
        XCTAssertFalse(s.imVorfuehrmodus)
        XCTAssertFalse(s.rechnenMoeglich, "abgewiesen wird nicht gerechnet")
        XCTAssertEqual(s.fehlschlaege, 0, "eine Absage ist keine Stille")
        XCTAssertEqual(s.seit, t(0.2), "abgewiesen seit der ersten Absage")
        XCTAssertEqual(s.letzterGrund, "Kennwort stimmt nicht")
        XCTAssertEqual(s.abstand, 60, "der Abstand wächst trotzdem — ändern tut erst das Einrichten")
    }

    /// Der Heim-PC war weg (Vorführmodus) und kommt mit neuem Kennwort zurück: Die Absage
    /// holt aus dem Vorführmodus heraus — in die Startansicht, nicht ins Rechnen.
    func testEineAbsageHoltAusDemVorfuehrmodusUndEinFehlschlagTrennt() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.melde(weg, jetzt: t(35))
        XCTAssertEqual(s.lage, .vorfuehrung)
        s.melde(.abgewiesen(grund: "Kennwort stimmt nicht"), jetzt: t(45))
        XCTAssertEqual(s.lage, .abgewiesen)
        XCTAssertEqual(s.seit, t(45))
        XCTAssertEqual(s.letzteAntwort, t0, "eine Absage ist keine bestätigte Antwort")
        XCTAssertEqual(s.naechsterVersuch, t(50), "von vorn: 5 s")
        // UND WIEDER STILL: getrennt seit dann, Vorführmodus erst nach der Schwelle.
        s.melde(weg, jetzt: t(50))
        XCTAssertEqual(s.lage, .getrennt)
        XCTAssertEqual(s.seit, t(50))
        XCTAssertEqual(s.fehlschlaege, 1)
        s.melde(weg, jetzt: t(55))
        XCTAssertEqual(s.lage, .vorfuehrung)
        // UND RICHTIG EINGERICHTET: verbunden.
        s.melde(.abgewiesen(grund: "x"), jetzt: t(60))
        s.melde(.antwort, jetzt: t(61))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertNil(s.letzterGrund)
    }

    func testDasFensterZeigtBeiAbsageDieStartansicht() {
        let s0 = Vorfuehrschalter(start: t0)
        XCTAssertEqual(s0.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
        XCTAssertEqual(s0.fensterinhalt(eingerichtet: true, arbeitet: true), .arbeit)

        var vorf = verbunden()
        vorf.melde(weg, jetzt: t(30))
        vorf.melde(weg, jetzt: t(35))
        XCTAssertEqual(vorf.fensterinhalt(eingerichtet: true, arbeitet: true), .vorfuehrung)
        XCTAssertEqual(vorf.fensterinhalt(eingerichtet: true, arbeitet: false), .vorfuehrung)
        XCTAssertEqual(vorf.fensterinhalt(eingerichtet: false, arbeitet: true), .start,
                       "ohne Adresse sagt der Vorführmodus nichts über den Heim-PC")

        var ab = Vorfuehrschalter(start: t0)
        ab.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        XCTAssertEqual(ab.fensterinhalt(eingerichtet: true, arbeitet: true), .start,
                       "auch mitten in der Arbeit: dort steht der Grund und «Einrichten»")
        XCTAssertEqual(ab.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
    }

    // --------------------------------------------- zwei Takte, ein Bild (Durchsicht, M1)

    /// Nach dem ersten Einrichten zeigte der Mac bis zu 60 s den Vorführmodus: Solange das
    /// Blatt offen war, scheiterte jeder Versuch (keine Adresse), und der Abstand wuchs.
    func testNeuEingerichtetBeginntVonVorn() {
        var s = Vorfuehrschalter(start: t0)
        for i in 0..<6 { s.melde(.keineAntwort(grund: "keine Adresse"), jetzt: t(Double(i) * 10)) }
        XCTAssertEqual(s.lage, .vorfuehrung)
        XCTAssertEqual(s.abstand, 60)
        s.neuEingerichtet(jetzt: t(100))
        XCTAssertEqual(s, Vorfuehrschalter(start: t(100)), "wie eben gestartet")
        XCTAssertTrue(s.faellig(jetzt: t(100)), "der erste Versuch sofort")
        XCTAssertFalse(s.imVorfuehrmodus)
        XCTAssertEqual(s.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
        s.melde(.antwort, jetzt: t(100.3))
        XCTAssertEqual(s.lage, .verbunden)
    }

    /// Steht die Leitung laut Heimleitung, versucht der Schalter sofort neu — er schaltet
    /// aber selbst nicht um: Entschieden wird an seiner eigenen Antwort.
    func testDieHeimleitungMachtDenNaechstenVersuchFaelligAberSchaltetNicht() {
        var s = verbunden()
        for i in 0..<5 { s.melde(weg, jetzt: t(30 + Double(i))) }
        XCTAssertEqual(s.lage, .vorfuehrung)
        XCTAssertFalse(s.faellig(jetzt: t(40)))

        s.heimleitungFand(.antwort(status: 200, millisekunden: 40), jetzt: t(40))
        XCTAssertTrue(s.faellig(jetzt: t(40)), "die Leitung steht: jetzt neu versuchen")
        XCTAssertEqual(s.lage, .vorfuehrung, "umgeschaltet wird erst an der eigenen Antwort")

        // EINE ABSAGE DORT holt ebenfalls zum Versuch — sie wird den Modus verlassen.
        var v = verbunden()
        for i in 0..<5 { v.melde(weg, jetzt: t(30 + Double(i))) }
        v.heimleitungFand(.antwort(status: 401, millisekunden: 40), jetzt: t(40))
        XCTAssertTrue(v.faellig(jetzt: t(40)))
        v.melde(.abgewiesen(grund: "Kennwort stimmt nicht"), jetzt: t(40.2))
        XCTAssertEqual(v.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
    }

    func testWasDieHeimleitungFindetUndNichtsAendert() {
        // VERBUNDEN UND 200: nichts zu tun, der Takt bleibt.
        var s = verbunden()
        let vorher = s
        s.heimleitungFand(.antwort(status: 200, millisekunden: 12), jetzt: t(3))
        XCTAssertEqual(s, vorher)
        // ABGEWIESEN UND 401: dasselbe Bild, kein Drängeln.
        var a = Vorfuehrschalter(start: t0)
        a.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        let abVorher = a
        a.heimleitungFand(.antwort(status: 401, millisekunden: 12), jetzt: t(2))
        a.heimleitungFand(.antwort(status: 403, millisekunden: 12), jetzt: t(2))
        XCTAssertEqual(a, abVorher)
        // KEINE ANTWORT DORT bringt den Vorführmodus nicht früher — die Schwelle entscheidet.
        var g = verbunden()
        g.melde(weg, jetzt: t(30))
        let gVorher = g
        g.heimleitungFand(.keineAntwort(.zeitUeberschritten), jetzt: t(31))
        g.heimleitungFand(.antwort(status: 502, millisekunden: 12), jetzt: t(31))
        XCTAssertEqual(g, gVorher)
        XCTAssertEqual(g.lage, .getrennt)
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
        XCTAssertEqual(Vorfuehrsaetze.einrichten, "Einrichten")
        XCTAssertEqual(Vorfuehrsaetze.grund("Tailscale am Mac an? Der Name des Heim-PC ist im Netz nicht zu finden."),
                       "Zuletzt: Tailscale am Mac an? Der Name des Heim-PC ist im Netz nicht zu finden.")
        XCTAssertNil(Vorfuehrsaetze.grund(nil), "ohne Grund kein Satz")
        XCTAssertNil(Vorfuehrsaetze.grund("  \n"), "ein leerer Grund ist keiner")
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
