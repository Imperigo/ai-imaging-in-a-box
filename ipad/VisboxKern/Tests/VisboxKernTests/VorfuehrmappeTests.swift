import Foundation
import XCTest
import VisboxKern

/// Die Vorführmappe — gelesen wie die Mac-App sie liest, und **an der Mappe, die
/// `tools/vorfuehrmappe.py --beispiel` erzeugt** (abgelegt unter `ipad/VisboxMac/Beispielmappe/`;
/// dass sie genau die Ausgabe des Werkzeugs ist, hält `tests/test_vorfuehrmappe.py`).
final class VorfuehrmappeTests: XCTestCase {

    private var ordner: URL!

    override func setUpWithError() throws {
        ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("vorfuehrmappe-probe-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
    }

    override func tearDownWithError() throws {
        try? FileManager.default.removeItem(at: ordner)
    }

    /// Der Ordner der Beispielmappe im Repo: `ipad/<Mac-App>/Beispielmappe/`.
    ///
    /// **Gesucht, nicht beim Namen genannt:** Der Ordner der Mac-App trägt den Namen der
    /// App, und der steht nur in `Marke.swift` (`tests/test_ipad_geruest.py`). Es muss genau
    /// einen geben — zwei Beispielmappen wären zwei Stände.
    private var beispielordner: URL {
        get throws {
            let ipad = URL(fileURLWithPath: #filePath)
                .deletingLastPathComponent().deletingLastPathComponent()
                .deletingLastPathComponent().deletingLastPathComponent()
            let treffer = try FileManager.default
                .contentsOfDirectory(at: ipad, includingPropertiesForKeys: nil)
                .map { $0.appendingPathComponent("Beispielmappe") }
                .filter {
                    FileManager.default.fileExists(
                        atPath: $0.appendingPathComponent(Vorfuehrmappe.dateiname).path)
                }
            XCTAssertEqual(treffer.count, 1, "\(treffer)")
            return try XCTUnwrap(treffer.first)
        }
    }

    private func mappe(_ bilder: String, kopf: String = #""schema": "visbox.vorfuehrmappe/v1", "titel": "Testbau""#,
                       vorhanden: Set<String>? = nil) throws -> Vorfuehrmappe {
        let json = "{\(kopf), \"bilder\": [\(bilder)]}"
        return try Vorfuehrmappe.lies(Data(json.utf8)) { vorhanden?.contains($0) ?? true }
    }

    private func bild(_ datei: String, tag: String? = nil, flaeche: String = #"{"zeichen": "bestanden", "score": 0.84, "schwelle": 0.65}"#) -> String {
        let t = tag.map { "\"\($0)\"" } ?? "null"
        return #"{"datei": "\#(datei)", "blick": "Blick \#(datei)", "gerechnet_am": \#(t), "flaeche": \#(flaeche)}"#
    }

    private func fehler(_ arbeit: () throws -> Vorfuehrmappe) -> Vorfuehrmappenfehler? {
        do {
            _ = try arbeit()
            return nil
        } catch let f as Vorfuehrmappenfehler {
            return f
        } catch {
            XCTFail("fremder Fehler \(error)")
            return nil
        }
    }

    // ------------------------------------------------------ die Mappe aus dem Werkzeug

    func testDieBeispielmappeAusDemWerkzeugIstLesbar() throws {
        let m = try Vorfuehrmappe.lies(ordner: try beispielordner)
        XCTAssertEqual(m.titel, "Testbau")
        XCTAssertEqual(m.art, "Beispielmappe")
        XCTAssertTrue(m.platzhalter, "die Beispielmappe hält Platzhalter und sagt es")
        XCTAssertNil(m.gerechnetAm, "ein Platzhalter ist an keinem Tag gerechnet")
        XCTAssertEqual(m.bilder.count, 6)
        XCTAssertTrue(m.bilder.allSatisfy { $0.vorhanden }, "\(m.bilder.filter { !$0.vorhanden }.map { $0.datei })")
        XCTAssertEqual(m.kopfzeile, "Beispielmappe · 6 Bilder · Platzhalter, nicht gerechnet")
        // JEDE DATEI IST EIN PNG — die App lädt sie, ohne nachzusehen.
        for b in m.bilder {
            let url = try XCTUnwrap(Vorfuehrmappe.adresse(b, in: try beispielordner))
            let kopf = try Data(contentsOf: url).prefix(8)
            XCTAssertEqual(Array(kopf), Ebenenausgabe.pngKennung, b.datei)
        }
    }

    func testDieBeispielmappeZeigtJedeArtVonZeichen() throws {
        let m = try Vorfuehrmappe.lies(ordner: try beispielordner)
        let nachDatei = Dictionary(uniqueKeysWithValues: m.bilder.map { ($0.datei, $0) })
        let so = try XCTUnwrap(nachDatei["blick-sued-ost.png"])
        XCTAssertEqual(so.zeichen.art, .bestanden)
        XCTAssertEqual(so.fussband, "BESTANDEN · 0.84 gegen 0.65")
        XCTAssertEqual(so.unterzeile, "Blick Süd-Ost · Platzhalter, nicht gerechnet")
        let nw = try XCTUnwrap(nachDatei["blick-nord-west.png"])
        XCTAssertEqual(nw.fussband, "DURCHGEFALLEN · 0.52 gegen 0.65")
        let hof = try XCTUnwrap(nachDatei["skizze-ueber-den-hof.png"])
        XCTAssertEqual(hof.zeichen.art, .nichtGemessen)
        XCTAssertTrue(hof.zeichen.art.gestrichelt)
        XCTAssertEqual(hof.fussband, "NICHT GEMESSEN · Vorbehalt")
        XCTAssertEqual(hof.zeichen.vorbehalte.first?.kopf, Pruefzeichen.anfangSkizzeNichtAngekommen)
        let strasse = try XCTUnwrap(nachDatei["blick-von-der-strasse.png"])
        XCTAssertEqual(strasse.zeichen.art, .entwurf, "ein Entwurf liest sich als Entwurf")
        XCTAssertEqual(strasse.fussband, "ENTWURF — NICHT GEPRÜFT")
        let ost = try XCTUnwrap(nachDatei["blick-ost.png"])
        XCTAssertEqual(ost.fussband, "NICHT GEMESSEN", "ohne Messung keine Zahl und kein Vorbehalt")
    }

    /// **Dasselbe Zeichen wie live**: Die Felder unter `flaeche` sind die eines Bildes aus
    /// `GET /api/projekt`, und das Zeichen ist `Mappenbild.pruefzeichen` — nicht nachgebaut.
    func testDasZeichenIstDasDerFlaeche() throws {
        let daten = try Data(contentsOf: try beispielordner.appendingPathComponent(Vorfuehrmappe.dateiname))
        let roh = try XCTUnwrap(JSONWert.lies(daten)["bilder"]?.alsListe)
        let m = try Vorfuehrmappe.lies(ordner: try beispielordner)
        for eintrag in roh {
            let datei = try XCTUnwrap(eintrag["datei"]?.alsText)
            let live = Mappenbild(try XCTUnwrap(eintrag["flaeche"]?.alsObjekt))
            let hier = try XCTUnwrap(m.bilder.first { $0.datei == datei })
            XCTAssertEqual(hier.angaben, live, datei)
            XCTAssertEqual(hier.zeichen, live.pruefzeichen(live.vorgabeLesart), datei)
        }
    }

    // ------------------------------------------------------------- Zusage 1: Schema

    func testEinUnbekanntesSchemaWirdNichtGelesen() {
        XCTAssertEqual(fehler { try mappe(bild("a.png"), kopf: #""schema": "visbox.vorfuehrmappe/v2", "titel": "T""#) },
                       .schemaUnbekannt("visbox.vorfuehrmappe/v2"))
        XCTAssertEqual(fehler { try mappe(bild("a.png"), kopf: #""titel": "T""#) },
                       .schemaUnbekannt(nil))
        XCTAssertTrue(Vorfuehrmappenfehler.schemaUnbekannt("x/v9").satz.contains("x/v9"))
        XCTAssertTrue(Vorfuehrmappenfehler.schemaUnbekannt(nil).satz.contains(Vorfuehrmappe.schema))
    }

    func testOhneTitelOderBilderlisteKeineMappe() {
        XCTAssertEqual(fehler { try mappe(bild("a.png"), kopf: #""schema": "visbox.vorfuehrmappe/v1""#) },
                       .feldFehlt("titel"))
        XCTAssertEqual(fehler { try mappe(bild("a.png"), kopf: #""schema": "visbox.vorfuehrmappe/v1", "titel": "  ""#) },
                       .feldFehlt("titel"))
        let ohneListe = Data(#"{"schema": "visbox.vorfuehrmappe/v1", "titel": "T", "bilder": "a.png"}"#.utf8)
        XCTAssertEqual(fehler { try Vorfuehrmappe.lies(ohneListe) { _ in true } }, .feldFehlt("bilder"))
        XCTAssertEqual(fehler { try Vorfuehrmappe.lies(Data("[1]".utf8)) { _ in true } }, .nichtLesbar)
        XCTAssertEqual(fehler { try Vorfuehrmappe.lies(Data("kein json".utf8)) { _ in true } }, .nichtLesbar)
    }

    func testOhneDateiImOrdnerEinBenannterFehler() {
        XCTAssertEqual(fehler { try Vorfuehrmappe.lies(ordner: ordner) }, .dateiFehlt)
        XCTAssertTrue(Vorfuehrmappenfehler.dateiFehlt.satz.contains(Vorfuehrmappe.dateiname))
    }

    // ------------------------------------------------------ Zusage 2: fehlende Datei

    func testEineFehlendeBilddateiBringtNichtsZuFall() throws {
        let json = #"{"schema": "visbox.vorfuehrmappe/v1", "titel": "T", "platzhalter": false, "bilder": [\#(bild("da.png", tag: "2026-10-28")), \#(bild("weg.png", tag: "2026-10-28"))]}"#
        try Data(json.utf8).write(to: ordner.appendingPathComponent(Vorfuehrmappe.dateiname))
        try Data(Ebenenausgabe.pngKennung).write(to: ordner.appendingPathComponent("da.png"))
        let m = try Vorfuehrmappe.lies(ordner: ordner)
        XCTAssertEqual(m.bilder.map { $0.datei }, ["da.png", "weg.png"])
        XCTAssertEqual(m.bilder.map { $0.vorhanden }, [true, false])
        let weg = m.bilder[1]
        XCTAssertNil(Vorfuehrmappe.adresse(weg, in: ordner))
        XCTAssertEqual(weg.unterzeile, "Blick weg.png · Bilddatei fehlt")
        XCTAssertTrue(weg.fehltSatz.contains("fehlt"))
        XCTAssertTrue(weg.fehltSatz.contains("weg.png"))
        XCTAssertEqual(weg.zeichen.art, .bestanden, "das Zeichen bleibt, auch ohne Datei")
    }

    func testEinOrdnerMitDemNamenEinesBildesIstKeinBild() throws {
        let json = #"{"schema": "visbox.vorfuehrmappe/v1", "titel": "T", "bilder": [\#(bild("a.png"))]}"#
        try Data(json.utf8).write(to: ordner.appendingPathComponent(Vorfuehrmappe.dateiname))
        try FileManager.default.createDirectory(at: ordner.appendingPathComponent("a.png"),
                                                withIntermediateDirectories: true)
        XCTAssertEqual(try Vorfuehrmappe.lies(ordner: ordner).bilder.map { $0.vorhanden }, [false])
    }

    // ------------------------------------------------- Zusage 3: ein Name, kein Weg

    func testEinDateinameMitWegWirdAbgewiesen() {
        for name in ["../a.png", "/etc/a.png", "unter/a.png", #"c:\\a.png"#, ".versteckt.png", "", " a.png"] {
            let f = fehler { try mappe(bild(name)) }
            guard case .bildUnlesbar(let stelle, _) = f else {
                XCTFail("\(name.debugDescription) wurde angenommen: \(String(describing: f))")
                continue
            }
            XCTAssertEqual(stelle, 1)
        }
    }

    func testEinBildOhneFlaecheOderDoppeltWirdAbgewiesen() {
        guard case .bildUnlesbar(2, let grund) = fehler({ try mappe(bild("a.png") + #", {"datei": "b.png"}"#) }) else {
            return XCTFail("ein Bild ohne flaeche wurde angenommen")
        }
        XCTAssertTrue(grund.contains("flaeche"))
        guard case .bildUnlesbar(2, _) = fehler({ try mappe(bild("a.png") + ", " + bild("a.png")) }) else {
            return XCTFail("ein doppeltes Bild wurde angenommen")
        }
        guard case .bildUnlesbar(1, _) = fehler({ try mappe("7") }) else {
            return XCTFail("ein Eintrag, der kein Objekt ist, wurde angenommen")
        }
    }

    // ---------------------------------------------------------------- Sortieren

    func testSortiertDasZuletztGerechneteZuerstSonstNachDatei() throws {
        let m = try mappe([bild("ohne.png"), bild("alt.png", tag: "2026-10-27"),
                           bild("neu-b.png", tag: "2026-10-28T09:00:00Z"),
                           bild("neu-a.png", tag: "2026-10-28")].joined(separator: ", "),
                          kopf: #""schema": "visbox.vorfuehrmappe/v1", "titel": "T", "platzhalter": false"#)
        XCTAssertEqual(m.bilder.map { $0.datei }, ["neu-b.png", "neu-a.png", "alt.png", "ohne.png"])
        XCTAssertEqual(m.kopfzeile, "4 Bilder · gerechnet vom 27.10. bis 28.10.")
    }

    // ---------------------------------------------------------- Datum und Zeilen

    func testDasDatumStehtAnJedemGerechnetenBild() throws {
        let m = try mappe(bild("a.png", tag: "2026-10-28"),
                          kopf: #""schema": "visbox.vorfuehrmappe/v1", "titel": "T", "art": "Beispielmappe", "platzhalter": false, "gerechnet_am": "2026-10-28""#)
        XCTAssertFalse(m.platzhalter)
        XCTAssertEqual(m.gerechnetAm, Kalendertag("2026-10-28"))
        XCTAssertEqual(m.bilder[0].unterzeile, "Blick a.png · vorher gerechnet am 28.10.2026")
        XCTAssertEqual(m.kopfzeile, "Beispielmappe · 1 Bild · gerechnet am 28.10.")
        let ohneTag = try mappe(bild("b.png"), kopf: #""schema": "visbox.vorfuehrmappe/v1", "titel": "T", "platzhalter": false"#)
        XCTAssertEqual(ohneTag.bilder[0].unterzeile, "Blick b.png · vorher gerechnet, Tag nicht bekannt")
        XCTAssertEqual(ohneTag.kopfzeile, "1 Bild · Tag des Rechnens nicht bekannt")
    }

    /// Eine Mappe, die nicht sagt, ob sie gerechnet ist, gilt als Platzhalter — nie umgekehrt.
    func testOhneAngabeGiltDieMappeAlsPlatzhalter() throws {
        let m = try mappe(bild("a.png", tag: "2026-10-28"))
        XCTAssertTrue(m.platzhalter)
        XCTAssertEqual(m.bilder[0].unterzeile, "Blick a.png · Platzhalter, nicht gerechnet")
    }

    func testDerKalendertagRaetNicht() {
        XCTAssertEqual(Kalendertag("2026-10-28")?.kurz, "28.10.")
        XCTAssertEqual(Kalendertag("2026-01-05T23:59:00Z")?.lang, "05.01.2026")
        for roh in ["", "28.10.2026", "2026-13-01", "2026-10-00", "2026-10-28 09:00", "2026/10/28", "abcd-ef-gh"] {
            XCTAssertNil(Kalendertag(roh), roh)
        }
        XCTAssertNil(Kalendertag(nil))
        XCTAssertLessThan(Kalendertag("2026-10-27")!, Kalendertag("2026-10-28")!)
        XCTAssertLessThan(Kalendertag("2025-12-31")!, Kalendertag("2026-01-01")!)
    }

    func testDieUnterschriftFaelltAufDenEigenenNamenUndDieDateiZurueck() throws {
        let m = try mappe(#"{"datei": "a.png", "flaeche": {"zeichen": "bestanden", "titel": "Eigener Name"}}, {"datei": "b.png", "blick": " ", "flaeche": {}}"#)
        XCTAssertEqual(m.bilder[0].unterzeile, "Eigener Name · Platzhalter, nicht gerechnet")
        XCTAssertEqual(m.bilder[1].unterzeile, "b.png · Platzhalter, nicht gerechnet")
        // OHNE ZEICHEN: wie live «nicht geliefert», nicht «bestanden» und nicht nichts.
        XCTAssertEqual(m.bilder[1].fussband, Pruefzeichen.wortNichtGeliefert)
        XCTAssertTrue(m.bilder[0].vorlesetext.contains("Prüfzeichen"))
    }
}
