import Foundation
import XCTest
import VisboxKern

/// Die Startzeilen der Mac-App (Blatt 13): jede Zeile kennt «steht / lädt / wartet / fehlt,
/// weil …», und die Kopfzeile ist gezählt. Der Ersatz-Server ist hier eine Reihe von
/// Antworten (Code, Rumpf, Fehlercode) — genau das, was die Mac-App misst und hereingibt.
final class StartzeilenTests: XCTestCase {

    private let t0 = Date(timeIntervalSince1970: 1_790_000_000)

    private func heim(_ json: String, status: Int = 200) -> Heimbefund {
        .antwort(status: status, daten: Data(json.utf8))
    }

    /// Die Antwort von `/api/heim` wie auf Blatt 13: Blender da, Karte frei, Assistent lädt.
    private let berichtWieBlatt13 = """
        {"blender": {"da": true, "satz": "Blender da"},
         "grafikkarte": {"frei_gb": 30.2, "satz": ""},
         "assistent": {"stand": "laedt", "modell": "qwen3:30b",
                       "satz": "Sprachmodell am Heim-PC wird geladen"},
         "satz": "Der Heim-PC ist da."}
        """

    // ------------------------------------------------------------------ die Leitung

    func testOhneAdresseWartetDieLeitungUndSagtWasZuTunIst() {
        let s = Startzeilen.leitung(nil, adresseDa: false, jetzt: t0)
        XCTAssertEqual(s.wort, "wartet")
        XCTAssertTrue(s.satz.contains("Einrichten"), s.satz)
    }

    func testVorDerErstenAntwortLaedtDieLeitung() {
        XCTAssertEqual(Startzeilen.leitung(nil, adresseDa: true, jetzt: t0),
                       .laedt(seit: t0, satz: "Leitung zum Heim-PC wird aufgebaut"))
    }

    func testMit200StehtSieMitDerGemessenenAntwortzeit() {
        let s = Startzeilen.leitung(.antwort(status: 200, millisekunden: 38), adresseDa: true,
                                    jetzt: t0)
        XCTAssertTrue(s.steht)
        XCTAssertTrue(s.satz.contains("38 ms"), s.satz)
    }

    func test401HeisstKennwortStimmtNicht() {
        let s = Startzeilen.leitung(.antwort(status: 401, millisekunden: 20), adresseDa: true,
                                    jetzt: t0)
        XCTAssertTrue(s.fehlt)
        XCTAssertTrue(s.satz.hasPrefix("Kennwort stimmt nicht"), s.satz)
    }

    func test403HeisstUeberDieWeiterleitungOhneKennwort() {
        let s = Startzeilen.leitung(.antwort(status: 403, millisekunden: 20), adresseDa: true,
                                    jetzt: t0)
        XCTAssertTrue(s.fehlt)
        XCTAssertTrue(s.satz.contains("Weiterleitung ohne Kennwort"), s.satz)
    }

    /// Tailscale Serve antwortet selbst mit 502, wenn hinter ihm kein Server läuft — das ist
    /// eine Antwort, aber nicht die des Heim-PC.
    func test502SagtDassTailscaleAntwortetAberKeinServer() {
        let s = Startzeilen.leitung(.antwort(status: 502, millisekunden: 20), adresseDa: true,
                                    jetzt: t0)
        XCTAssertTrue(s.fehlt)
        XCTAssertTrue(s.satz.contains("kein Server"), s.satz)
    }

    func testJederAndereCodeFehltMitSeinerZahl() {
        let s = Startzeilen.leitung(.antwort(status: 500, millisekunden: 20), adresseDa: true,
                                    jetzt: t0)
        XCTAssertTrue(s.fehlt)
        XCTAssertTrue(s.satz.contains("500"), s.satz)
    }

    func testKeineAntwortHeisstHeimPCAntwortetNicht() {
        for code in [-1001, -1004, -1005] {
            let s = Startzeilen.leitung(.keineAntwort(Leitungsfehler(urlFehlercode: code)),
                                        adresseDa: true, jetzt: t0)
            XCTAssertTrue(s.fehlt, "\(code)")
            XCTAssertTrue(s.satz.hasPrefix("Heim-PC antwortet nicht"), "\(code): \(s.satz)")
        }
    }

    func testZertifikatsUndNamensfehlerFragenNachTailscale() {
        for code in [-1003, -1006, -1200, -1202, -1203, -1206] {
            let s = Startzeilen.leitung(.keineAntwort(Leitungsfehler(urlFehlercode: code)),
                                        adresseDa: true, jetzt: t0)
            XCTAssertTrue(s.fehlt, "\(code)")
            XCTAssertTrue(s.satz.hasPrefix("Tailscale am Mac an?"), "\(code): \(s.satz)")
        }
    }

    func testDieFehlercodesWerdenZugeordnet() {
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1001), .zeitUeberschritten)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1004), .keineVerbindung)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1005), .abgerissen)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1009), .keinNetz)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1003), .nameUnbekannt)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1006), .nameUnbekannt)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1201), .zertifikat)
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -999), .abgebrochen)
        // AM RAND DES ZERTIFIKATSBEREICHS: -1207 ist keiner mehr.
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1207), .sonstig(code: -1207))
        XCTAssertEqual(Leitungsfehler(urlFehlercode: -1199), .sonstig(code: -1199))
    }

    /// Eine Abfrage, die die App selbst zurückzieht, ist kein Befund über den Heim-PC.
    func testEineZurueckgezogeneAbfrageIstKeinFehlen() {
        let s = Startzeilen.leitung(.keineAntwort(.abgebrochen), adresseDa: true, jetzt: t0)
        XCTAssertFalse(s.fehlt)
        XCTAssertTrue(s.laedt)
    }

    // -------------------------------------------------------- Rechner und Assistent

    func testOhneLeitungWartenRechnerUndAssistent() {
        let leitung = Zeilenstand.fehlt(grund: "Heim-PC antwortet nicht.")
        let h = Startzeilen.heim(leitung: leitung, heim(berichtWieBlatt13), jetzt: t0)
        XCTAssertEqual(h.rechner.wort, "wartet")
        XCTAssertEqual(h.assistent.wort, "wartet")
    }

    /// **Der wichtigste Fall dieser Datei:** Ein Server ohne `/api/heim` hat nichts gesagt —
    /// und was nicht gesagt ist, steht nicht.
    func testOhneDenWegHeisstEsWartetNieSteht() {
        let h = Startzeilen.heim(leitung: .steht(satz: "da"),
                                 heim(#"{"fehler": "Unbekannter Weg: /api/heim"}"#, status: 404),
                                 jetzt: t0)
        for s in [h.rechner, h.assistent] {
            XCTAssertEqual(s.wort, "wartet")
            XCTAssertTrue(s.satz.contains("kennt diese Frage noch nicht"), s.satz)
        }
    }

    func testDerBerichtWieAufBlatt13() {
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(berichtWieBlatt13), jetzt: t0)
        XCTAssertEqual(h.rechner, .steht(satz: "Blender da · Grafikkarte frei (30.2 GB)"))
        XCTAssertEqual(h.assistent,
                       .laedt(seit: t0, satz: "Sprachmodell am Heim-PC wird geladen"))
    }

    func testDerAssistentStehtMitSeinemModell() {
        let json = #"{"blender": {"da": true, "satz": "x"}, "grafikkarte": {"frei_gb": null, "satz": "y"}, "assistent": {"stand": "bereit", "modell": "qwen3:30b", "satz": ""}, "satz": "z"}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertEqual(h.assistent, .steht(satz: "Sprachmodell geladen · qwen3:30b"))
    }

    func testFehltBlenderFehltDerRechnerMitDemSatzDesServers() {
        let json = #"{"blender": {"da": false, "satz": "Blender ist am Heim-PC nicht zu finden."}, "grafikkarte": {"frei_gb": 30, "satz": "frei"}, "assistent": {"stand": "fehlt", "modell": null, "satz": ""}, "satz": ""}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertEqual(h.rechner, .fehlt(grund: "Blender ist am Heim-PC nicht zu finden."))
        XCTAssertTrue(h.assistent.fehlt)
        XCTAssertFalse(h.assistent.satz.isEmpty)
    }

    /// «aus» heisst: vor einem Bild entladen — es kommt wieder. Das ist ein Warten.
    func testAusHeisstWartet() {
        let json = #"{"blender": {"da": true, "satz": "x"}, "grafikkarte": {"frei_gb": 1, "satz": "y"}, "assistent": {"stand": "aus", "modell": "qwen3:30b", "satz": "Entladen, solange ein Bild rechnet."}, "satz": ""}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertEqual(h.assistent, .wartet(satz: "Entladen, solange ein Bild rechnet."))
    }

    func testEinUnbekannterAssistentenstandWirdGezeigtNichtGeraten() {
        let json = #"{"blender": {"da": true}, "grafikkarte": {"frei_gb": 1}, "assistent": {"stand": "schlaeft"}, "satz": ""}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertTrue(h.assistent.fehlt)
        XCTAssertTrue(h.assistent.satz.contains("«schlaeft»"), h.assistent.satz)
    }

    /// Eine `1` ist kein Ja — wie überall im Kern.
    func testDaMussEinWahrheitswertSein() {
        let json = #"{"blender": {"da": 1, "satz": "Blender da"}, "grafikkarte": {"frei_gb": 1}, "assistent": {"stand": "bereit"}, "satz": ""}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertTrue(h.rechner.fehlt, "\(h.rechner)")
        // DER ASSISTENT IST TROTZDEM GELESEN: ein kaputter Teil verschweigt nicht die anderen.
        XCTAssertTrue(h.assistent.steht, "\(h.assistent)")
    }

    func testEinUnlesbarerBerichtFehltBeideMitSatz() {
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim("<html>"), jetzt: t0)
        XCTAssertTrue(h.rechner.fehlt)
        XCTAssertTrue(h.assistent.fehlt)
        XCTAssertTrue(h.rechner.satz.contains("nicht lesbar"), h.rechner.satz)
    }

    func testEineFehlendeGrafikkartenzahlIstNichtNull() {
        let json = #"{"blender": {"da": true}, "grafikkarte": {"frei_gb": null}, "assistent": {"stand": "bereit"}}"#
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), heim(json), jetzt: t0)
        XCTAssertTrue(h.rechner.satz.contains("nicht gemeldet"), h.rechner.satz)
        XCTAssertFalse(h.rechner.satz.contains("0.0"), h.rechner.satz)
    }

    func testHeimOhneAntwortFehltMitDemSatzDerLeitung() {
        let h = Startzeilen.heim(leitung: .steht(satz: "da"), .keineAntwort(.zeitUeberschritten),
                                 jetzt: t0)
        XCTAssertEqual(h.rechner, .fehlt(grund: Leitungsfehler.zeitUeberschritten.satz))
    }

    // ------------------------------------------------------------- nie ein leerer Satz

    /// **Leere Sätze gibt es nie.** Über ein Raster von Befunden — auch einem Server, der
    /// jeden `satz` leer schickt — hat jede der vier Zeilen einen Satz mit Inhalt.
    func testKeineZeileHatJeEinenLeerenSatz() {
        let leer = #"{"blender": {"da": true, "satz": " "}, "grafikkarte": {"frei_gb": 2.5, "satz": ""}, "assistent": {"stand": "%@", "modell": null, "satz": ""}, "satz": ""}"#
        var heimBefunde: [Heimbefund?] = [nil, .keineAntwort(.keinNetz), .keineAntwort(.abgebrochen),
                                         heim("{}"), heim("[]"), heim("", status: 404),
                                         heim("", status: 401), heim("", status: 418)]
        for stand in ["bereit", "laedt", "fehlt", "aus", "anders"] {
            heimBefunde.append(heim(leer.replacingOccurrences(of: "%@", with: stand)))
        }
        var leitungen: [Leitungsbefund?] = [nil, .antwort(status: 200, millisekunden: -3)]
        for status in [401, 403, 404, 500, 502] {
            leitungen.append(.antwort(status: status, millisekunden: 1))
        }
        for code in [-999, -1001, -1003, -1004, -1005, -1009, -1200, -1, 0] {
            leitungen.append(.keineAntwort(Leitungsfehler(urlFehlercode: code)))
        }
        var gesehen = 0
        for adresseDa in [true, false] {
            for l in leitungen {
                for h in heimBefunde {
                    let bild = Startbild.aus(leitung: l, heim: h, adresseDa: adresseDa, ipad: nil,
                                             vorher: nil, jetzt: t0)
                    for (zeile, stand) in bild.zeilen {
                        gesehen += 1
                        XCTAssertFalse(stand.satz.trimmingCharacters(in: .whitespaces).isEmpty,
                                       "\(zeile) leer bei \(String(describing: l)) / "
                                       + "\(String(describing: h))")
                    }
                }
            }
        }
        XCTAssertGreaterThan(gesehen, 500)
    }

    func testAuchEinVonHandLeerGesetzterStandHatEinenSatz() {
        for s in [Zeilenstand.steht(satz: ""), .laedt(seit: t0, satz: "  "), .wartet(satz: "\n"),
                  .fehlt(grund: "")] {
            XCTAssertFalse(s.satz.isEmpty, "\(s)")
        }
    }

    // ---------------------------------------------------------------- das Ganze

    /// Blatt 13 wörtlich: Leitung steht, Rechner steht, Assistent lädt, iPad wartet —
    /// «baut auf · 2 von 4». Gezählt, nicht geschätzt.
    func testDieKopfzeileIstGezaehlt() {
        let bild = Startbild.aus(leitung: .antwort(status: 200, millisekunden: 38),
                                 heim: heim(berichtWieBlatt13), adresseDa: true, ipad: nil,
                                 vorher: nil, jetzt: t0)
        XCTAssertEqual(bild.zeilen.map(\.stand.wort), ["steht", "steht", "lädt", "wartet"])
        XCTAssertEqual(bild.stehend, 2)
        XCTAssertEqual(bild.kopfzeile, "baut auf · 2 von 4")
    }

    func testAlleStehenHeisstBereitUndEinFehlenUnvollstaendig() {
        var bild = Startbild(leitung: .steht(satz: "a"), rechner: .steht(satz: "b"),
                             assistent: .steht(satz: "c"), ipad: .steht(satz: "d"))
        XCTAssertEqual(bild.kopfzeile, "bereit · 4 von 4")
        bild.rechner = .fehlt(grund: "Blender fehlt.")
        XCTAssertEqual(bild.kopfzeile, "unvollständig · 3 von 4")
    }

    /// Lädt nichts mehr und fehlt nichts, baut auch nichts auf — dann wartet es.
    func testOhneLadendeZeileHeisstEsWartetNichtBautAuf() {
        let nurIpad = Startbild(leitung: .steht(satz: "a"), rechner: .steht(satz: "b"),
                                assistent: .steht(satz: "c"))
        XCTAssertEqual(nurIpad.kopfzeile, "wartet · 3 von 4")
        let ohneAdresse = Startbild.aus(leitung: nil, heim: nil, adresseDa: false, ipad: nil,
                                        vorher: nil, jetzt: t0)
        XCTAssertEqual(ohneAdresse.kopfzeile, "wartet · 0 von 4")
    }

    func testDieIpadZeileWartetOhneMeldungUndNenntDieApp() {
        let bild = Startbild(leitung: .steht(satz: "a"), rechner: .steht(satz: "b"),
                             assistent: .steht(satz: "c"))
        XCTAssertEqual(bild.ipad.wort, "wartet")
        XCTAssertTrue(bild.ipad.satz.hasPrefix(Marke.name + " auf dem iPad öffnen"), bild.ipad.satz)
        XCTAssertTrue(bild.ipad.satz.contains("Tailscale"), bild.ipad.satz)
        XCTAssertTrue(bild.ipad.satz.contains("iPad koppeln"), bild.ipad.satz)
        // VON AUSSEN GEMELDET, gilt das Gemeldete.
        let gemeldet = Startbild.aus(leitung: nil, heim: nil, adresseDa: true,
                                     ipad: .steht(satz: "verbunden"), vorher: nil, jetzt: t0)
        XCTAssertEqual(gemeldet.ipad, .steht(satz: "verbunden"))
    }

    /// Entscheid 39: Anfangen, bevor der Assistent geladen ist.
    func testSchonAnfangenGehtSobaldDieLeitungStehtAuchWennDerAssistentLaedt() {
        let bild = Startbild.aus(leitung: .antwort(status: 200, millisekunden: 38),
                                 heim: heim(berichtWieBlatt13), adresseDa: true, ipad: nil,
                                 vorher: nil, jetzt: t0)
        XCTAssertTrue(bild.assistent.laedt)
        XCTAssertTrue(bild.schonAnfangen)
        XCTAssertTrue(bild.anfangenSatz.contains("Assistent kommt dazu"), bild.anfangenSatz)
    }

    func testSchonAnfangenGehtNichtOhneLeitung() {
        for l: Leitungsbefund? in [nil, .antwort(status: 401, millisekunden: 1),
                                   .keineAntwort(.zeitUeberschritten)] {
            let bild = Startbild.aus(leitung: l, heim: nil, adresseDa: true, ipad: nil,
                                     vorher: nil, jetzt: t0)
            XCTAssertFalse(bild.schonAnfangen, "\(String(describing: l))")
            XCTAssertTrue(bild.anfangenSatz.contains("sobald die Leitung"), bild.anfangenSatz)
        }
    }

    /// «lädt seit 12 s» zählt ab dem ersten Mal — nicht ab der letzten Abfrage.
    func testLaedtBehaeltSeinenBeginnUeberMehrereAbfragen() {
        let erst = Startbild.aus(leitung: .antwort(status: 200, millisekunden: 38),
                                 heim: heim(berichtWieBlatt13), adresseDa: true, ipad: nil,
                                 vorher: nil, jetzt: t0)
        let spaeter = t0.addingTimeInterval(12)
        let dann = Startbild.aus(leitung: .antwort(status: 200, millisekunden: 40),
                                 heim: heim(berichtWieBlatt13), adresseDa: true, ipad: nil,
                                 vorher: erst, jetzt: spaeter)
        guard case .laedt(let seit, _) = dann.assistent else {
            return XCTFail("\(dann.assistent)")
        }
        XCTAssertEqual(seit, t0)
        XCTAssertEqual(Startzeilen.seitText(seit, jetzt: spaeter), "seit 12 s")
        XCTAssertEqual(Startzeilen.seitText(seit, jetzt: t0.addingTimeInterval(185)), "seit 3 min")
    }

    // ------------------------------------------------------------ Takt und Signal

    func testDerTaktWaechstVon5Bis60UndFaelltBeiAenderungZurueck() {
        var abstand: TimeInterval? = nil
        var folge: [TimeInterval] = []
        for _ in 0..<7 {
            let n = Leitungstakt.naechster(nach: abstand, geaendert: false, laedt: false)
            folge.append(n)
            abstand = n
        }
        XCTAssertEqual(folge, [5, 10, 20, 40, 60, 60, 60])
        XCTAssertEqual(Leitungstakt.naechster(nach: 60, geaendert: true, laedt: false), 5)
        XCTAssertEqual(Leitungstakt.naechster(nach: 60, geaendert: false, laedt: true), 5)
    }

    func testDieErreichbarkeitBehaeltIhrSeitUndWechseltNurBeimWechsel() {
        let t1 = t0.addingTimeInterval(10)
        let t2 = t0.addingTimeInterval(20)
        var e = Heimerreichbarkeit.unbekannt
        e = e.nach(.laedt(seit: t0, satz: "x"), jetzt: t0)
        XCTAssertEqual(e, .unbekannt)
        e = e.nach(.steht(satz: "x"), jetzt: t0)
        XCTAssertEqual(e, .erreichbar(seit: t0))
        e = e.nach(.steht(satz: "y"), jetzt: t1)
        XCTAssertEqual(e, .erreichbar(seit: t0))
        // NEU AUFBAUEN IST KEIN WECHSEL.
        e = e.nach(.laedt(seit: t1, satz: "x"), jetzt: t1)
        XCTAssertEqual(e, .erreichbar(seit: t0))
        e = e.nach(.fehlt(grund: "weg"), jetzt: t1)
        XCTAssertEqual(e, .nichtErreichbar(seit: t1))
        e = e.nach(.wartet(satz: "keine Adresse"), jetzt: t2)
        XCTAssertEqual(e, .nichtErreichbar(seit: t1))
        XCTAssertFalse(e.erreichbar)
    }

    // ------------------------------------------------- die Zahl fürs iPad (Entscheid 63)

    private let heimAdresse = URL(string: "https://rechner.netz.ts.net:8443")!

    func testDieZahlFuersIPadStehtMitDerAdresseInDerZeile() {
        let daten = Data(#"{"zahl": "123456", "gilt_noch_s": 600, "satz": "x"}"#.utf8)
        let zeile = Koppelzahl.zeile(status: 200, daten: daten, adresse: heimAdresse)
        XCTAssertEqual(zeile.wort, "wartet")
        XCTAssertTrue(zeile.satz.contains("123 456"), zeile.satz)
        XCTAssertTrue(zeile.satz.contains("10 min"), zeile.satz)
        XCTAssertTrue(zeile.satz.contains(heimAdresse.absoluteString),
                      "ohne die Adresse kann das iPad mit der Zahl nichts anfangen")
    }

    func testOhneZahlOderMitFehlerSagtDieZeileWarum() {
        let ohne = Koppelzahl.zeile(status: 200, daten: Data(#"{"satz": "x"}"#.utf8),
                                    adresse: heimAdresse)
        XCTAssertEqual(ohne.wort, "fehlt")
        let falsch = Koppelzahl.zeile(status: 200, daten: Data(#"{"zahl": "12a456"}"#.utf8),
                                      adresse: heimAdresse)
        XCTAssertEqual(falsch.wort, "fehlt")
        let abgelehnt = Koppelzahl.zeile(
            status: 400, daten: Data(#"{"fehler": "Ohne Kennwort gibt es nichts zu koppeln."}"#.utf8),
            adresse: heimAdresse)
        XCTAssertEqual(abgelehnt.wort, "fehlt")
        XCTAssertTrue(abgelehnt.satz.contains("Ohne Kennwort"), abgelehnt.satz)
    }
}
