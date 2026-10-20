import Foundation
import XCTest
import VisboxKern

/// Der Leitungsschalter (bis 0.3.0 «Vorführschalter») — **jeder Übergang einzeln**, mit einer
/// Uhr, die die Probe selbst vorrückt. Seit Entscheid 103b ersetzt keine Lage mehr das Fenster;
/// geprüft wird dazu, was gesperrt ist und welches Band steht.
final class LeitungsschalterTests: XCTestCase {

    private let t0 = Date(timeIntervalSinceReferenceDate: 812_000_000)
    private let weg = Versuchsausgang.keineAntwort(grund: "Frist abgelaufen")

    private func t(_ s: TimeInterval) -> Date { t0.addingTimeInterval(s) }

    /// Drei Fehlschläge ab `ab`, der letzte 30 s danach — die Schwelle seit dem 20.10.2026.
    private func dreiFehlschlaege(_ s: inout Leitungsschalter, ab: TimeInterval) {
        s.melde(weg, jetzt: t(ab))
        s.melde(weg, jetzt: t(ab + 10))
        s.melde(weg, jetzt: t(ab + 30))
    }

    /// Ein Schalter, der einmal verbunden war (bei t0).
    private func verbunden() -> Leitungsschalter {
        var s = Leitungsschalter(start: t0)
        s.melde(.antwort, jetzt: t0)
        return s
    }

    // ------------------------------------------------------------------ der Start

    func testBeimStartIstDerErsteVersuchSofortFaellig() {
        let s = Leitungsschalter(start: t0)
        XCTAssertEqual(s.lage, .startet)
        XCTAssertTrue(s.faellig(jetzt: t0))
        XCTAssertFalse(s.ohneRechner)
        XCTAssertFalse(s.rechnenMoeglich, "ohne Antwort wird nicht gerechnet")
        XCTAssertNil(s.letzterVersuch)
    }

    /// Beim Start ohne Leitung: **nie sofort** — erst nach der Schwelle.
    func testBeimStartOhneLeitungNichtSofortSondernNachDerSchwelle() {
        var s = Leitungsschalter(start: t0)
        s.melde(weg, jetzt: t(0.2))
        XCTAssertEqual(s.lage, .startet, "ein Fehlschlag ist ein Ruckler")
        XCTAssertEqual(s.seit, t0, "beim Start zählt die Stille ab dem Start")
        s.ticke(jetzt: t(4))
        XCTAssertEqual(s.lage, .startet)
        s.melde(weg, jetzt: t(5.2))
        XCTAssertEqual(s.lage, .startet, "zwei Fehlschläge sind seit 20.10.2026 noch ein Aussetzer")
        s.melde(weg, jetzt: t(15.2))
        XCTAssertEqual(s.lage, .startet, "drei, aber noch keine 30 s")
        s.ticke(jetzt: t(29.9))
        XCTAssertEqual(s.lage, .startet)
        s.ticke(jetzt: t(30))
        XCTAssertEqual(s.lage, .ohneRechner, "drei Fehlschläge und 30 s")
        XCTAssertEqual(s.seit, t0)
        XCTAssertTrue(s.ohneRechner)
    }

    func testBeimStartMitHaengendemVersuchNachNeunzigSekunden() {
        var s = Leitungsschalter(start: t0)
        s.ticke(jetzt: t(30))
        XCTAssertEqual(s.lage, .startet, "Zeit allein, ohne drei Fehlschläge: noch nicht")
        s.ticke(jetzt: t(89.9))
        XCTAssertEqual(s.lage, .startet)
        s.ticke(jetzt: t(90))
        XCTAssertEqual(s.lage, .ohneRechner, "90 s ohne jede Antwort")
    }

    func testBeimStartMitAntwortVerbunden() {
        var s = Leitungsschalter(start: t0)
        s.melde(weg, jetzt: t(0.1))
        s.melde(.antwort, jetzt: t(5))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertEqual(s.seit, t(5))
        XCTAssertEqual(s.fehlschlaege, 0)
        XCTAssertTrue(s.rechnenMoeglich)
        XCTAssertEqual(s.naechsterVersuch, t(5 + Leitungsschalter.lebenszeichenAbstand))
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
        XCTAssertFalse(s.ohneRechner)
        XCTAssertEqual(s.naechsterVersuch, t(35))
    }

    func testGetrenntWirdNachDreiFehlschlaegenUndDreissigSekundenOhneRechner() {
        var s = verbunden()
        s.melde(weg, jetzt: t(30))
        s.melde(weg, jetzt: t(35))
        XCTAssertEqual(s.lage, .getrennt, "zwei Fehlschläge: noch ein Aussetzer")
        XCTAssertTrue(s.kurzNichtErreichbar, "das weiche Band steht")
        s.melde(weg, jetzt: t(45))
        XCTAssertEqual(s.lage, .getrennt, "drei, aber erst 15 s")
        s.ticke(jetzt: t(59.9))
        XCTAssertEqual(s.lage, .getrennt)
        s.ticke(jetzt: t(60))
        XCTAssertEqual(s.lage, .ohneRechner)
        XCTAssertFalse(s.kurzNichtErreichbar, "ohne Rechner kein weiches Band mehr")
        XCTAssertEqual(s.seit, t(30), "seit dem ersten Fehlschlag, nicht seit dem Umschalten")
    }

    /// Der Owner-Befund vom 20.10.2026: Mobilfunk, ein Aussetzer über die Frist eines Versuchs
    /// (8 s) — und «antwortet nicht» stand da, obwohl der Heim-PC gesund war.
    func testEinAussetzerImMobilfunkSperrtNichts() {
        var s = verbunden()
        // ZWEI VERSUCHE SCHEITERN (je 8 s Frist), DER DRITTE KOMMT DURCH.
        s.melde(weg, jetzt: t(18))
        XCTAssertTrue(s.kurzNichtErreichbar)
        s.melde(weg, jetzt: t(31))
        XCTAssertFalse(s.ohneRechner)
        s.ticke(jetzt: t(45))
        XCTAssertFalse(s.ohneRechner, "still weiter verbinden")
        s.melde(.antwort, jetzt: t(51))
        XCTAssertEqual(s.lage, .verbunden, "von selbst zurück")
        XCTAssertFalse(s.kurzNichtErreichbar)
        XCTAssertEqual(Leitungssaetze.kurzWeg, "Heim-PC kurz nicht erreichbar — verbinde neu …")
    }

    func testDieSchwelleIstDreiUndDreissigOderNeunzig() {
        XCTAssertFalse(Leitungsschalter.schwelleErreicht(fehlschlaege: 2, stille: 89))
        XCTAssertFalse(Leitungsschalter.schwelleErreicht(fehlschlaege: 9, stille: 29.9))
        XCTAssertTrue(Leitungsschalter.schwelleErreicht(fehlschlaege: 3, stille: 30))
        XCTAssertTrue(Leitungsschalter.schwelleErreicht(fehlschlaege: 0, stille: 90))
    }

    func testGetrenntUndWiederDaOhneSchwelle() {
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

    func testAusOhneRechnerZurueckErstNachEinerBestaetigtenAntwort() {
        var s = verbunden()
        dreiFehlschlaege(&s, ab: 30)
        XCTAssertEqual(s.lage, .ohneRechner)
        s.melde(.unbestaetigt(grund: "Fehlerseite der Weiterleitung"), jetzt: t(45))
        XCTAssertEqual(s.lage, .ohneRechner, "eine unbestätigte Antwort holt nicht zurück")
        XCTAssertEqual(s.letzterGrund, "Fehlerseite der Weiterleitung")
        s.ticke(jetzt: t(300))
        XCTAssertEqual(s.lage, .ohneRechner, "die Zeit allein holt nicht zurück")
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
        s.melde(.unbestaetigt(grund: "unlesbar"), jetzt: t(60))
        XCTAssertEqual(s.lage, .ohneRechner)
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
    /// Band «antwortet nicht», ohne Weg zu «Einrichten».
    func testEineAbsageFuehrtNieZuOhneRechner() {
        var s = Leitungsschalter(start: t0)
        let absage = Versuchsausgang.abgewiesen(grund: "Kennwort stimmt nicht")
        for i in 0..<6 {
            s.melde(absage, jetzt: t(Double(i) * 5 + 0.2))
            s.ticke(jetzt: t(Double(i) * 5 + 4.9))
            XCTAssertEqual(s.lage, .abgewiesen)
        }
        s.ticke(jetzt: t(600))
        XCTAssertEqual(s.lage, .abgewiesen, "auch die Zeitschwelle schaltet nicht")
        XCTAssertFalse(s.ohneRechner)
        XCTAssertFalse(s.rechnenMoeglich, "abgewiesen wird nicht gerechnet")
        XCTAssertEqual(s.fehlschlaege, 0, "eine Absage ist keine Stille")
        XCTAssertEqual(s.seit, t(0.2), "abgewiesen seit der ersten Absage")
        XCTAssertEqual(s.letzterGrund, "Kennwort stimmt nicht")
        XCTAssertEqual(s.abstand, 60, "der Abstand wächst trotzdem — ändern tut erst das Einrichten")
    }

    /// Der Heim-PC war weg (ohne Rechner) und kommt mit neuem Kennwort zurück: Die Absage
    /// holt aus «ohne Rechner» heraus — gesperrt bleibt das Rechnen trotzdem.
    func testEineAbsageHoltAusOhneRechnerUndEinFehlschlagTrennt() {
        var s = verbunden()
        dreiFehlschlaege(&s, ab: 30)
        XCTAssertEqual(s.lage, .ohneRechner)
        s.melde(.abgewiesen(grund: "Kennwort stimmt nicht"), jetzt: t(70))
        XCTAssertEqual(s.lage, .abgewiesen)
        XCTAssertEqual(s.seit, t(70))
        XCTAssertEqual(s.letzteAntwort, t0, "eine Absage ist keine bestätigte Antwort")
        XCTAssertEqual(s.naechsterVersuch, t(75), "von vorn: 5 s")
        // UND WIEDER STILL: getrennt seit dann, «ohne Rechner» erst nach der Schwelle.
        s.melde(weg, jetzt: t(75))
        XCTAssertEqual(s.lage, .getrennt)
        XCTAssertEqual(s.seit, t(75))
        XCTAssertEqual(s.fehlschlaege, 1)
        s.melde(weg, jetzt: t(85))
        s.melde(weg, jetzt: t(105))
        XCTAssertEqual(s.lage, .ohneRechner)
        // UND RICHTIG EINGERICHTET: verbunden.
        s.melde(.abgewiesen(grund: "x"), jetzt: t(110))
        s.melde(.antwort, jetzt: t(111))
        XCTAssertEqual(s.lage, .verbunden)
        XCTAssertNil(s.letzterGrund)
    }

    func testKeineLageErsetztMehrDasFenster() {
        // ENTSCHEID 103b: Bis 0.3.0 kam hier der Vorführmodus, und eine Absage holte aus der
        // Arbeit zurück zum Start. Jetzt entscheidet allein «Schon anfangen».
        let s0 = Leitungsschalter(start: t0)
        XCTAssertEqual(s0.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
        XCTAssertEqual(s0.fensterinhalt(eingerichtet: true, arbeitet: true), .arbeit)

        var ohne = verbunden()
        dreiFehlschlaege(&ohne, ab: 30)
        XCTAssertEqual(ohne.lage, .ohneRechner)
        XCTAssertEqual(ohne.fensterinhalt(eingerichtet: true, arbeitet: true), .arbeit)
        XCTAssertEqual(ohne.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
        XCTAssertEqual(ohne.fensterinhalt(eingerichtet: false, arbeitet: true), .start,
                       "ohne Adresse liegt das Blatt «Einrichten» über dem Start")

        var ab = Leitungsschalter(start: t0)
        ab.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        XCTAssertEqual(ab.fensterinhalt(eingerichtet: true, arbeitet: true), .arbeit,
                       "die Absage sperrt Rechnen und Assistent, nicht die Arbeit")
        XCTAssertEqual(ab.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
    }

    func testOhneRechnerOeffnetDieArbeitVonSelbstUndSchonAnfangenGeht() {
        var s = Leitungsschalter(start: t0)
        XCTAssertFalse(s.oeffnetDieArbeit(eingerichtet: true))
        XCTAssertFalse(s.anfangenMoeglich(leitungSteht: false), "vor der Schwelle wird gewartet")
        XCTAssertTrue(s.anfangenMoeglich(leitungSteht: true))
        dreiFehlschlaege(&s, ab: 0)
        XCTAssertEqual(s.lage, .ohneRechner)
        XCTAssertTrue(s.oeffnetDieArbeit(eingerichtet: true),
                      "an der Stelle des Vorführmodus kommt die gewöhnliche Arbeit")
        XCTAssertFalse(s.oeffnetDieArbeit(eingerichtet: false),
                       "solange eingerichtet wird, beginnt die App mit den Startzeilen")
        XCTAssertTrue(s.anfangenMoeglich(leitungSteht: false), "ohne Rechner geht es trotzdem")
        XCTAssertEqual(s.anfangenSatz(startzeilen: "S", leitungSteht: false),
                       Leitungssaetze.anfangenOhneRechner)
        XCTAssertEqual(s.anfangenSatz(startzeilen: "S", leitungSteht: true), "S")
        XCTAssertEqual(verbunden().anfangenSatz(startzeilen: "S", leitungSteht: true), "S")

        var ab = Leitungsschalter(start: t0)
        ab.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        XCTAssertFalse(ab.oeffnetDieArbeit(eingerichtet: true), "die Absage zeigt der Start")
        XCTAssertFalse(ab.anfangenMoeglich(leitungSteht: false))
    }

    // ------------------------------------------------ was gesperrt ist, und das Band

    func testGesperrtSindRechnenUndAssistentNurNachDerSchwelleOderBeiAbsage() {
        let start = Leitungsschalter(start: t0)
        XCTAssertEqual(start.sperre(eingerichtet: true), .offen, "beim Start kein falscher Alarm")
        XCTAssertEqual(verbunden().sperre(eingerichtet: true), .offen)

        var getrennt = verbunden()
        getrennt.melde(weg, jetzt: t(20))
        XCTAssertEqual(getrennt.lage, .getrennt)
        XCTAssertEqual(getrennt.sperre(eingerichtet: true), .offen, "ein Aussetzer sperrt nichts")

        var ohne = verbunden()
        dreiFehlschlaege(&ohne, ab: 30)
        XCTAssertEqual(ohne.sperre(eingerichtet: true).satz,
                       "Braucht einen Rechner — Heim-PC nicht erreichbar.")
        XCTAssertTrue(ohne.sperre(eingerichtet: true).gesperrt)
        XCTAssertFalse(ohne.rechnenMoeglich)

        var ab = Leitungsschalter(start: t0)
        ab.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        XCTAssertEqual(ab.sperre(eingerichtet: true).satz, Leitungssaetze.sperreAbgewiesen)
        XCTAssertTrue(Leitungssaetze.sperreAbgewiesen.contains("«Einrichten»"))

        for s in [start, verbunden(), ohne, ab] {
            XCTAssertEqual(s.sperre(eingerichtet: false).satz, Leitungssaetze.sperreOhneHeim,
                           "ohne eingerichteten Heim-PC gibt es keinen Rechner")
        }
    }

    func testDasBandStehtWieImBlatt() {
        XCTAssertNil(Leitungsschalter(start: t0).band(eingerichtet: true))
        XCTAssertNil(verbunden().band(eingerichtet: true))

        var getrennt = verbunden()
        getrennt.melde(weg, jetzt: t(20))
        let weich = getrennt.band(eingerichtet: true)
        XCTAssertEqual(weich, .kurzWeg)
        XCTAssertEqual(weich?.weich, true)
        XCTAssertNil(weich?.knopf, "das weiche Band verbindet ohnehin still neu")
        XCTAssertEqual(weich?.titel, "Heim-PC kurz nicht erreichbar — verbinde neu …")

        var ohne = verbunden()
        dreiFehlschlaege(&ohne, ab: 30)
        let hart = ohne.band(eingerichtet: true)
        // BLATT 28, FELD 1 — wörtlich.
        XCTAssertEqual(hart?.titel, "Heim-PC nicht erreichbar")
        XCTAssertEqual(hart?.satz, "Rechnen und Assistent gesperrt — alles andere geht.")
        XCTAssertEqual(hart?.knopf, .erneutVerbinden)
        XCTAssertEqual(hart?.knopf?.wort, "Erneut verbinden")
        XCTAssertEqual(hart?.weich, false)
        XCTAssertEqual(hart?.vorgelesen,
                       "Heim-PC nicht erreichbar. Rechnen und Assistent gesperrt — alles andere geht.")

        var ab = Leitungsschalter(start: t0)
        ab.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        let absage = ab.band(eingerichtet: true)
        XCTAssertEqual(absage, .abgewiesen)
        XCTAssertEqual(absage?.knopf, .einrichten, "bei einer Absage hilft kein neuer Versuch")
        XCTAssertEqual(absage?.knopf?.wort, "Einrichten")
        XCTAssertNotEqual(absage?.titel, hart?.titel, "eine Absage ist nicht «nicht erreichbar»")

        XCTAssertNil(ohne.band(eingerichtet: false), "beim Einrichten liegt das Blatt darüber")
    }

    func testDieFarbenDesBandsSindDieDesBlattsUndLesbar() {
        XCTAssertEqual(Rechnerband.grund.hex, "#2a2416")
        XCTAssertEqual(Rechnerband.rand.hex, "#5a4a22")
        XCTAssertEqual(Rechnerband.schrift.hex, "#e8d9b0")
        XCTAssertGreaterThanOrEqual(Farbton.kontrast(Rechnerband.schrift, Rechnerband.grund), 4.5)
    }

    func testDieSaetzeSindSchweizerSchreibung() {
        let alle = [Leitungssaetze.kurzWeg, Leitungssaetze.bandNichtErreichbar,
                    Leitungssaetze.bandGesperrt, Leitungssaetze.bandAbgewiesen,
                    Leitungssaetze.bandAbgewiesenSatz, Leitungssaetze.erneutVerbinden,
                    Leitungssaetze.einrichten, Leitungssaetze.sperreNichtErreichbar,
                    Leitungssaetze.sperreAbgewiesen, Leitungssaetze.sperreOhneHeim,
                    Leitungssaetze.anfangenOhneRechner]
        for satz in alle {
            XCTAssertFalse(satz.contains("ß"), satz)
            XCTAssertFalse(satz.lowercased().contains("vorführ"), "der Vorführmodus entfällt: \(satz)")
        }
        XCTAssertEqual(Leitungssaetze.einrichten, "Einrichten")
    }

    // --------------------------------------------- zwei Takte, ein Bild (Durchsicht, M1)

    /// Nach dem ersten Einrichten zeigte der Mac bis zu 60 s den Vorführmodus: Solange das
    /// Blatt offen war, scheiterte jeder Versuch (keine Adresse), und der Abstand wuchs.
    func testNeuEingerichtetBeginntVonVorn() {
        var s = Leitungsschalter(start: t0)
        for i in 0..<6 { s.melde(.keineAntwort(grund: "keine Adresse"), jetzt: t(Double(i) * 10)) }
        XCTAssertEqual(s.lage, .ohneRechner)
        XCTAssertEqual(s.abstand, 60)
        s.neuEingerichtet(jetzt: t(100))
        XCTAssertEqual(s, Leitungsschalter(start: t(100)), "wie eben gestartet")
        XCTAssertTrue(s.faellig(jetzt: t(100)), "der erste Versuch sofort")
        XCTAssertFalse(s.ohneRechner)
        XCTAssertFalse(s.oeffnetDieArbeit(eingerichtet: true))
        s.melde(.antwort, jetzt: t(100.3))
        XCTAssertEqual(s.lage, .verbunden)
    }

    /// Steht die Leitung laut Heimleitung, versucht der Schalter sofort neu — er schaltet
    /// aber selbst nicht um: Entschieden wird an seiner eigenen Antwort.
    func testDieHeimleitungMachtDenNaechstenVersuchFaelligAberSchaltetNicht() {
        var s = verbunden()
        for i in 0..<5 { s.melde(weg, jetzt: t(30 + Double(i) * 10)) }
        XCTAssertEqual(s.lage, .ohneRechner)
        XCTAssertFalse(s.faellig(jetzt: t(80)))

        s.heimleitungFand(.antwort(status: 200, millisekunden: 40), jetzt: t(80))
        XCTAssertTrue(s.faellig(jetzt: t(80)), "die Leitung steht: jetzt neu versuchen")
        XCTAssertEqual(s.lage, .ohneRechner, "umgeschaltet wird erst an der eigenen Antwort")

        // EINE ABSAGE DORT holt ebenfalls zum Versuch — sie wird den Modus verlassen.
        var v = verbunden()
        for i in 0..<5 { v.melde(weg, jetzt: t(30 + Double(i) * 10)) }
        v.heimleitungFand(.antwort(status: 401, millisekunden: 40), jetzt: t(80))
        XCTAssertTrue(v.faellig(jetzt: t(80)))
        v.melde(.abgewiesen(grund: "Kennwort stimmt nicht"), jetzt: t(80.2))
        XCTAssertEqual(v.fensterinhalt(eingerichtet: true, arbeitet: false), .start)
    }

    func testWasDieHeimleitungFindetUndNichtsAendert() {
        // VERBUNDEN UND 200: nichts zu tun, der Takt bleibt.
        var s = verbunden()
        let vorher = s
        s.heimleitungFand(.antwort(status: 200, millisekunden: 12), jetzt: t(3))
        XCTAssertEqual(s, vorher)
        // ABGEWIESEN UND 401: dasselbe Bild, kein Drängeln.
        var a = Leitungsschalter(start: t0)
        a.melde(.abgewiesen(grund: "x"), jetzt: t(1))
        let abVorher = a
        a.heimleitungFand(.antwort(status: 401, millisekunden: 12), jetzt: t(2))
        a.heimleitungFand(.antwort(status: 403, millisekunden: 12), jetzt: t(2))
        XCTAssertEqual(a, abVorher)
        // KEINE ANTWORT DORT bringt «ohne Rechner» nicht früher — die Schwelle entscheidet.
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
        XCTAssertEqual((0..<8).map { Leitungsschalter.abstand(stufe: $0) },
                       [5, 10, 20, 40, 60, 60, 60, 60])
        XCTAssertEqual(Leitungsschalter.abstand(stufe: 10_000), 60, "kein Überlauf")
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

    func testErneutVerbindenSetztDenAbstandZurueckUndBleibtOhneRechner() {
        var s = verbunden()
        for i in 0..<5 { s.melde(weg, jetzt: t(30 + Double(i) * 10)) }
        XCTAssertEqual(s.abstand, 60)
        s.erneutVerbinden(jetzt: t(100))
        XCTAssertTrue(s.faellig(jetzt: t(100)), "der nächste Versuch sofort")
        XCTAssertEqual(s.lage, .ohneRechner, "verlangt ist nicht verbunden")
        s.melde(weg, jetzt: t(100.5))
        XCTAssertEqual(s.naechsterVersuch, t(105.5), "wieder ab 5 s")
        s.melde(weg, jetzt: t(105.5))
        XCTAssertEqual(s.naechsterVersuch, t(115.5), "dann 10 s")
        s.erneutVerbinden(jetzt: t(110))
        s.melde(.antwort, jetzt: t(110.3))
        XCTAssertEqual(s.lage, .verbunden)
    }

    func testDieFristEinesVersuchsLiegtUnterDerZeitschwelle() {
        XCTAssertLessThan(Leitungsschalter.versuchsfrist, Leitungsschalter.schwelleSekunden)
        XCTAssertGreaterThanOrEqual(Leitungsschalter.schwelleFehlschlaege, 3, "nie sofort")
        XCTAssertLessThan(Leitungsschalter.schwelleSekunden, Leitungsschalter.schwelleSekundenAllein)
    }
}
