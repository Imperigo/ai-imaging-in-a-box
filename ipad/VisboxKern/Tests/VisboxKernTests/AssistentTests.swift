import Foundation
import XCTest
import VisboxKern

/// Der Assistent im Kern (Plan v0.1.7, Strom D3): Antworten lesen, die Karte ableiten, den
/// Zustand der Seitenleiste führen, die Anfragen bauen.
///
/// Die Antworten unten sind **dem Server nachgebildet** (`aiimaging.assistent.frage` und
/// `aiimaging.heimstand.heimstand`, Stand 01.10.2026), Blatt 14 durchgespielt.
final class AssistentTests: XCTestCase {

    private let anmeldung = Anmeldung(benutzer: "probe", kennwort: "geheim-32-zeichen")

    private let blatt14 = """
    {"antwort": "Hier ist mein Vorschlag: von Süd-Ost, Abendlicht, drei Varianten.",
     "vorschlag": {
       "einstellungen": {"kamera": "sSE", "augenhoehe": 1.6, "auge": null,
                         "blick_auf": null, "innenraum": null,
                         "prompt": "evening light, street view, residential building",
                         "seed": 0},
       "varianten": 3,
       "saetze": ["Standpunkt von Süden, zur Südost-Ecke gedreht (sSE) · 1.6 m Augenhöhe",
                  "Bildauftrag: «evening light, street view, residential building»",
                  "3 Varianten, Startwerte 0–2"],
       "rechenzeit": {"sekunden": null, "satz": "Rechenzeit am Heim-PC: noch nicht gemessen."}}}
    """

    private func lies(_ text: String, status: Int = 200) throws -> Assistentenantwort {
        try Assistentenantwort.lies(status: status, daten: Data(text.utf8))
    }

    private func rumpf(_ a: Anfrage) throws -> [String: JSONWert] {
        try XCTUnwrap(JSONWert.lies(XCTUnwrap(a.rumpf)).alsObjekt)
    }

    // ------------------------------------------------------------------ die Antwort

    func testBlatt14WirdGelesenUndDieKarteZeigtDieSaetzeDesServers() throws {
        let a = try lies(blatt14)
        let v = try XCTUnwrap(a.vorschlag)
        XCTAssertEqual(v.varianten, 3)
        XCTAssertEqual(v.einstellungen["augenhoehe"], .zahl(1.6))
        XCTAssertEqual(v.einstellungen["seed"], .ganz(0))
        XCTAssertEqual(v.einstellungen["auge"], .null, "null bleibt null — es leert drüben")
        let karte = Assistentenkarte(v)
        XCTAssertEqual(karte.zeilen.count, 3)
        XCTAssertEqual(karte.zeilen[2], "3 Varianten, Startwerte 0–2")
        XCTAssertEqual(karte.rechenzeit, "Rechenzeit am Heim-PC: noch nicht gemessen.")
        XCTAssertEqual(karte.standpunkt, .richtung("sSE"))
    }

    func testEineAntwortOhneVorschlagHatKeineKarte() throws {
        let a = try lies(#"{"antwort": "Dazu habe ich keinen Vorschlag."}"#)
        XCTAssertNil(a.vorschlag)
    }

    func testEinFehlerDesServersKommtAlsSatz() {
        XCTAssertThrowsError(try lies(#"{"fehler": "Gerade rechnet ein Bild."}"#, status: 400)) {
            let f = $0 as? Serverfehler
            XCTAssertEqual(f?.satz, "Gerade rechnet ein Bild.")
            XCTAssertEqual(f?.art, .abgelehnt)
        }
        XCTAssertThrowsError(try lies(#"{"fehler": "Ollama antwortet nicht."}"#, status: 503)) {
            XCTAssertEqual(($0 as? Serverfehler)?.satz, "Ollama antwortet nicht.")
        }
    }

    func testEineAntwortOhneAntwortfeldIstUnlesbarUndKeinErfolg() {
        XCTAssertThrowsError(try lies(#"{"vorschlag": null}"#)) {
            XCTAssertEqual(($0 as? Serverfehler)?.art, .unlesbar)
        }
    }

    // ------------------------------------------------------------------- der Standpunkt

    func testEinStandpunktVonHandWirdFuerDenPlanGelesen() {
        let s = VorgeschlagenerStandpunkt(["auge": .liste([.ganz(10), .zahl(-2.5), .zahl(1.6)]),
                                            "blick_auf": .liste([.ganz(0), .ganz(0), .ganz(3)]),
                                            "kamera": .null])
        XCTAssertEqual(s, .vonHand(auge: [10, -2.5, 1.6], blickAuf: [0, 0, 3]))
    }

    func testOhneStandpunktZeichnetDerPlanNichts() {
        XCTAssertNil(VorgeschlagenerStandpunkt(["prompt": .text("x"), "auge": .null]))
        XCTAssertNil(VorgeschlagenerStandpunkt(["auge": .liste([.ganz(1), .ganz(2)]),
                                                 "blick_auf": .liste([.ganz(0), .ganz(0), .ganz(0)])]))
    }

    func testEineKarteOhneSaetzeSagtWasSieEnthaelt() {
        let v = Assistentenvorschlag(einstellungen: ["prompt": .text("x"), "auge": .null],
                                     varianten: 4, saetze: ["  "], rechenzeit: nil)
        let karte = Assistentenkarte(v)
        XCTAssertEqual(karte.zeilen, ["Vorschlag ohne Beschreibung: prompt, 4 Varianten"])
        XCTAssertNil(karte.rechenzeit)
    }

    // --------------------------------------------------------------- der Zustand der Leiste

    func testEinGespraechDurchBlatt14() throws {
        var g = Assistentengespraech()
        let bitte = try XCTUnwrap(g.sende("  Zeig das Haus mehr von der Strasse her.  "))
        XCTAssertEqual(bitte.nachricht, "Zeig das Haus mehr von der Strasse her.")
        XCTAssertEqual(bitte.verlauf, [], "der Verlauf ist, was VOR der Nachricht stand")
        XCTAssertTrue(g.wartet)
        XCTAssertNil(g.sende("noch eine"), "solange eine Anfrage unterwegs ist, keine zweite")

        g.empfange(try lies(blatt14))
        XCTAssertFalse(g.wartet)
        XCTAssertNotNil(g.karte)
        XCTAssertEqual(g.beitraege.map(\.von), [.mensch, .assistent])

        let zweite = try XCTUnwrap(g.sende("Und etwas mehr Grün."))
        XCTAssertEqual(zweite.verlauf.count, 2)
        XCTAssertNil(g.karte, "eine neue Bitte ersetzt die alte Karte")
    }

    func testAblehnenVerwirftUndAendernLegtDenTextInsFeld() throws {
        var g = Assistentengespraech()
        _ = g.sende("x")
        g.empfange(try lies(blatt14))
        let text = try XCTUnwrap(g.aendere())
        XCTAssertTrue(text.hasPrefix("Bitte ändern: Standpunkt von Süden"), text)
        XCTAssertNil(g.karte)
        XCTAssertNil(g.aendere(), "ohne Karte nichts zu ändern")

        _ = g.sende("y")
        g.empfange(try lies(blatt14))
        g.lehneAb()
        XCTAssertNil(g.karte)
        XCTAssertNil(g.beginneAnwenden(), "eine abgelehnte Karte lässt sich nicht anwenden")
    }

    func testAnwendenGehtEinmalHinaus() throws {
        var g = Assistentengespraech()
        _ = g.sende("x")
        g.empfange(try lies(blatt14))
        let v = try XCTUnwrap(g.beginneAnwenden())
        XCTAssertEqual(v.varianten, 3)
        XCTAssertNil(g.beginneAnwenden(), "zweimal «Anwenden» hiesse zwei Läufe")
        XCTAssertNil(g.aendere())
        let start = try Rechenstart.lies(status: 200, daten: Data(
            #"{"gestartet": true, "schritte_gesamt": 8, "entwurf": false, "varianten": 3}"#.utf8))
        g.angewendet(start)
        XCTAssertNil(g.karte)
        XCTAssertFalse(g.wartet)
        XCTAssertNotNil(g.hinweis)
    }

    func testEinGescheitertesAnwendenLaesstDieKarteLiegen() throws {
        var g = Assistentengespraech()
        _ = g.sende("x")
        g.empfange(try lies(blatt14))
        _ = g.beginneAnwenden()
        g.scheitert("Es läuft schon einer.")
        XCTAssertNotNil(g.karte)
        XCTAssertEqual(g.hinweis, "Es läuft schon einer.")
        XCTAssertNotNil(g.beginneAnwenden(), "nach dem Satz darf es noch einmal versucht werden")
    }

    func testDerVerlaufWirdAufVierzigBeschnitten() throws {
        var g = Assistentengespraech()
        for i in 0..<30 {
            _ = g.sende("Frage \(i)")
            g.empfange(Assistentenantwort(antwort: "Antwort \(i)", vorschlag: nil))
        }
        let bitte = try XCTUnwrap(g.sende("letzte"))
        XCTAssertEqual(bitte.verlauf.count, Assistentengespraech.verlaufHoechstens)
        XCTAssertEqual(bitte.verlauf.last?.text, "Antwort 29")
    }

    // ------------------------------------------------------------------ der Stand

    func testNurBereitNimmtEingabe() {
        for stand in Assistentenstand.allCases {
            let z = Assistentenzeile(stand: stand, modell: "qwen3:30b", satz: "x")
            XCTAssertEqual(z.nimmtEingabe, stand == .bereit, stand.rawValue)
        }
        XCTAssertFalse(Assistentenzeile(stand: nil, modell: nil, satz: "x").nimmtEingabe)
    }

    func testDieZeileWirdAusHeimGelesenUndEinUnbekannterStandNichtGeraten() throws {
        let heim = """
        {"blender": {"da": true, "satz": "Blender ist da."},
         "grafikkarte": {"frei_gb": null, "satz": "nicht gemessen"},
         "assistent": {"stand": "laedt", "modell": "qwen3:30b", "satz": "Gerade rechnet ein Bild."},
         "satz": "Heim-PC antwortet."}
        """
        let z = try Assistentenzeile.ausHeim(status: 200, daten: Data(heim.utf8))
        XCTAssertEqual(z.stand, .laedt)
        XCTAssertEqual(z.satz, "Gerade rechnet ein Bild.")
        let fremd = heim.replacingOccurrences(of: "\"laedt\"", with: "\"schlaeft\"")
        let f = try Assistentenzeile.ausHeim(status: 200, daten: Data(fremd.utf8))
        XCTAssertNil(f.stand)
        XCTAssertFalse(f.nimmtEingabe)
        XCTAssertThrowsError(try Assistentenzeile.ausHeim(status: 200, daten: Data("{}".utf8)))
    }

    // ------------------------------------------------------------------ die Anfragen

    func testDieBitteGehtMitVerlaufAlsMenschUndAssistent() throws {
        let bitte = Assistentenbitte(nachricht: "Und jetzt?", verlauf: [
            Gespraechsbeitrag(von: .mensch, text: "Hallo"),
            Gespraechsbeitrag(von: .assistent, text: "Grüezi")])
        let a = try Anfragen.assistent(bitte, anmeldung: anmeldung)
        XCTAssertEqual(a.weg, Wege.assistent)
        let r = try rumpf(a)
        XCTAssertEqual(r["nachricht"], .text("Und jetzt?"))
        XCTAssertEqual(r["verlauf"], .liste([
            .objekt(["von": .text("mensch"), "text": .text("Hallo")]),
            .objekt(["von": .text("assistent"), "text": .text("Grüezi")])]))
        XCTAssertNil(try rumpf(Anfragen.assistent(
            Assistentenbitte(nachricht: "x", verlauf: []), anmeldung: anmeldung))["verlauf"])
    }

    func testAnwendenSchicktDenVorschlagMitSeinenLeerungenZurueck() throws {
        let v = try XCTUnwrap(try lies(blatt14).vorschlag)
        let a = try Anfragen.assistentAnwenden(v, ordner: "/p", anmeldung: anmeldung)
        XCTAssertEqual(a.weg, Wege.assistentAnwenden)
        let r = try rumpf(a)
        XCTAssertEqual(r["ordner"], .text("/p"))
        let zurueck = try XCTUnwrap(r["vorschlag"]?["einstellungen"]?.alsObjekt)
        XCTAssertEqual(zurueck["auge"], .null)
        XCTAssertEqual(zurueck["kamera"], .text("sSE"))
        XCTAssertEqual(r["vorschlag"]?["varianten"], .ganz(3))
    }

    func testHeimIstEinLesenderWegMitAnmeldung() {
        let a = Anfragen.heim(anmeldung: anmeldung)
        XCTAssertEqual(a.weg, Wege.heim)
        XCTAssertEqual(a.methode, .get)
        XCTAssertNil(a.rumpf)
        XCTAssertEqual(a.kopfzeilen["Authorization"], anmeldung.kopfzeile)
    }

    func testDieGrenzenStehenWieAufBlatt14() {
        XCTAssertEqual(Assistentengrenzen.titel, "Was der Assistent nicht tut")
        XCTAssertTrue(Assistentengrenzen.satz.contains("ohne «Anwenden» rechnen"))
    }
}
