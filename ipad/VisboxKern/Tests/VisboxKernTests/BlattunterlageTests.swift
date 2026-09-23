import Foundation
import XCTest
import VisboxKern

/// Die Unterlage des Blattes (`Kern/Blattunterlage.swift`, 23.09.2026): keine Ebene, `ueber`
/// nur sichtbar und aus derselben Mappe, gestreckt wie beim Server — und der Weg durch das
/// Parkfach bis in die Anfrage, **auch über einen Neustart der App.**
final class BlattunterlageTests: XCTestCase {

    private let png = Data(Ebenenausgabe.pngKennung + [5, 5, 5])

    private func unterlage(_ bild: String = "lauf-07.png", ordner: String? = "/mappe",
                           breite: Int? = 1536, hoehe: Int? = 1024) -> Blattunterlage {
        Blattunterlage(bild: bild, titel: "Lauf 07", ordner: ordner, breite: breite,
                       hoehe: hoehe)!
    }

    /// Ein Stapel mit `anzahl` bezeichneten, sichtbaren Ebenen.
    private func stapel(bezeichnet anzahl: Int) -> Ebenenstapel {
        var s = Ebenenstapel()
        for i in 0..<anzahl {
            if i > 0 { s.legeAn() }
            s.setzeStriche(s.aktiv, 3)
        }
        return s
    }

    private func rumpf(_ a: Anfrage) throws -> [String: JSONWert] {
        try XCTUnwrap(JSONWert.lies(try XCTUnwrap(a.rumpf)).alsObjekt)
    }

    // --------------------------------------------------------- 1 · keine Ebene

    func testDieUnterlageIstKeineEbene() {
        var s = Ebenenstapel()
        let vorher = s.ebenen
        let aktiv = s.aktiv
        s.legeUnterlage(unterlage())

        XCTAssertEqual(s.ebenen, vorher, "die Unterlage steht nicht in den Ebenen")
        XCTAssertEqual(s.vonObenGesehen.count, 1)
        XCTAssertEqual(s.aktiv, aktiv, "und sie wird nicht die gewählte Ebene")
        XCTAssertEqual(s.unterlage?.bild, "lauf-07.png")

        // ZUR HOECHSTZAHL ZAEHLT SIE NICHT: acht Ebenen gehen auch mit Unterlage.
        for _ in 1..<Ebenenstapel.hoechstensEbenen { XCTAssertNotNil(s.legeAn()) }
        XCTAssertEqual(s.ebenen.count, Ebenenstapel.hoechstensEbenen)
        XCTAssertFalse(s.kannAnlegen)
    }

    func testDieUnterlageZaehltNichtZurLeerPruefungUndIstKeineVariante() {
        var leer = Ebenenstapel()
        leer.legeUnterlage(unterlage())
        XCTAssertEqual(leer.plan(.eineSkizze), .nichtsGezeichnet(ausgeblendetGezeichnet: 0),
                       "eine sichtbare Unterlage macht das Blatt nicht bezeichnet")
        XCTAssertEqual(leer.plan(.ebenenAlsVarianten), .nichtsGezeichnet(ausgeblendetGezeichnet: 0))

        var drei = stapel(bezeichnet: 3)
        drei.legeUnterlage(unterlage())
        guard case .teile(let teile) = drei.plan(.ebenenAlsVarianten) else {
            return XCTFail("drei Ebenen und eine Unterlage sind drei Varianten, nicht vier")
        }
        XCTAssertEqual(teile.count, 3)
        guard case .teile(let eine) = drei.plan(.eineSkizze) else { return XCTFail() }
        XCTAssertEqual(eine.first?.ebenen.count, 3, "«Geht mit» zählt nur Ebenen")
    }

    func testNurDieUnterlageGehtNichtHinausUndDerSatzSagtEs() {
        let u = unterlage()
        let plan = Ablageplan.aus(Skizzenpaket(ausgabe: .nichtsGezeichnet(ausgeblendetGezeichnet: 0),
                                               unterlage: u), ordner: "/mappe")
        guard case .nicht(let satz) = plan else { return XCTFail("\(plan)") }
        XCTAssertTrue(satz.contains("Unterlage allein"), satz)
        XCTAssertTrue(satz.contains("«Lauf 07»"), satz)

        // Ohne sichtbare Unterlage der gewohnte Satz vom leeren Blatt.
        var s = Ebenenstapel()
        s.legeUnterlage(u)
        s.setzeUnterlageSichtbar(false)
        guard case .nicht(let leer) = Ablageplan.aus(
            Skizzenpaket(ausgabe: .nichtsGezeichnet(ausgeblendetGezeichnet: 0),
                         unterlage: s.unterlage),
            ordner: "/mappe") else { return XCTFail() }
        XCTAssertTrue(leer.hasPrefix("Nichts gezeichnet"), leer)
    }

    // --------------------------------------------------------- 2 · wann `ueber` mitgeht

    func testUeberGehtGenauMitWennDieUnterlageLiegtUndSichtbarIst() {
        var s = Ebenenstapel()
        XCTAssertEqual(Unterlagenangabe.aus(s.unterlage, ordner: "/mappe"), .ohne)

        s.legeUnterlage(unterlage())
        XCTAssertEqual(Unterlagenangabe.aus(s.unterlage, ordner: "/mappe"), .ueber("lauf-07.png"))

        // ENTSCHEID 7: gerechnet wird, was sichtbar ist — auch bei der Unterlage.
        s.setzeUnterlageSichtbar(false)
        let aus = Unterlagenangabe.aus(s.unterlage, ordner: "/mappe")
        XCTAssertEqual(aus, .ausgeblendet(bild: "lauf-07.png"))
        XCTAssertNil(aus.ueber)

        s.setzeUnterlageSichtbar(true)
        XCTAssertEqual(Unterlagenangabe.aus(s.unterlage, ordner: "/mappe").ueber, "lauf-07.png")

        s.entferneUnterlage()
        XCTAssertNil(s.unterlage)
        XCTAssertEqual(Unterlagenangabe.aus(s.unterlage, ordner: "/mappe"), .ohne)
    }

    func testEineNeuGelegteUnterlageIstSichtbarAuchWennDieAlteAusgeblendetWar() throws {
        var s = Ebenenstapel()
        s.legeUnterlage(unterlage("lauf-06.png"))
        s.setzeUnterlageSichtbar(false)
        s.legeUnterlage(unterlage("lauf-07.png"))
        XCTAssertEqual(s.unterlage?.sichtbar, true)
        XCTAssertEqual(s.unterlage?.bild, "lauf-07.png", "höchstens eine: die neue ersetzt die alte")

        // AUCH EIN AUSGEBLENDETER WERT WIRD SICHTBAR GELEGT: Wer darauf skizzieren will,
        // will das Bild sehen — und nur ein sichtbares geht als `ueber` mit.
        s.setzeUnterlageSichtbar(false)
        let versteckt = try XCTUnwrap(s.unterlage)
        XCTAssertFalse(versteckt.sichtbar)
        var neu = Ebenenstapel()
        neu.legeUnterlage(versteckt)
        XCTAssertEqual(neu.unterlage?.sichtbar, true)
        XCTAssertEqual(Unterlagenangabe.aus(neu.unterlage, ordner: "/mappe"), .ueber("lauf-07.png"))
    }

    func testEineUnterlageAusEinerAnderenMappeWirdAbgelehntNichtGrauGerechnet() {
        let u = unterlage(ordner: "/mappe-a")
        XCTAssertEqual(Unterlagenangabe.aus(u, ordner: "/mappe-b"),
                       .andereMappe(unterlage: "/mappe-a", jetzt: "/mappe-b"))
        let plan = Ablageplan.aus(Skizzenpaket(ausgabe: .bilder([]), unterlage: u),
                                  ordner: "/mappe-b")
        guard case .nicht(let satz) = plan else { return XCTFail("\(plan)") }
        XCTAssertTrue(satz.contains("«/mappe-a»") && satz.contains("«/mappe-b»"), satz)

        // LEER UND NIL SIND DIESELBE MAPPE — die des Starts.
        let start = unterlage(ordner: "")
        XCTAssertNil(start.ordner)
        XCTAssertEqual(Unterlagenangabe.aus(start, ordner: nil), .ueber("lauf-07.png"))
        XCTAssertEqual(Unterlagenangabe.aus(unterlage(ordner: nil), ordner: ""), .ueber("lauf-07.png"))
        XCTAssertEqual(Unterlagenangabe.aus(start, ordner: "/mappe"),
                       .andereMappe(unterlage: nil, jetzt: "/mappe"))
    }

    func testEineAusgeblendeteUnterlageAusEinerAnderenMappeHaeltNichtsAuf() {
        var s = Ebenenstapel()
        s.legeUnterlage(unterlage(ordner: "/mappe-a"))
        s.setzeUnterlageSichtbar(false)
        XCTAssertEqual(Unterlagenangabe.aus(s.unterlage, ordner: "/mappe-b"),
                       .ausgeblendet(bild: "lauf-07.png"))
    }

    func testOhneNamenGibtEsKeineUnterlage() {
        XCTAssertNil(Blattunterlage(bild: ""))
        XCTAssertNil(Blattunterlage(bild: "  \n"))
        XCTAssertEqual(Blattunterlage(bild: "lauf-07.png", titel: " ")?.titel, "lauf-07.png",
                       "ohne Titel der Dateiname, nie eine leere Zeile")
    }

    // --------------------------------------------------------- 3 · gestreckt wie drüben

    /// Die Grenzen sind mit der Regel des Servers nachgerechnet (`arbeitsgang.py`,
    /// `setze_auf_unterlage`, 23.09.2026, Blatt 1536 × 1024): 1520 und 1552 Bildpunkte
    /// breit bei 1024 hoch sind gestreckt, 1521 und 1551 nicht.
    func testGestrecktFaelltWieBeimServer() {
        let faelle: [(Int, Int, Bool)] = [
            (1536, 1024, false), (768, 512, false), (3072, 2048, false),
            (1521, 1024, false), (1520, 1024, true),
            (1551, 1024, false), (1552, 1024, true),
            (1024, 1024, true), (1920, 1080, true), (1, 1, true),
        ]
        for (b, h, soll) in faelle {
            XCTAssertEqual(unterlage(breite: b, hoehe: h).gestreckt, soll, "\(b) × \(h)")
        }
    }

    func testOhneGelesenGroesseIstGestrecktNichtGemessen() {
        XCTAssertNil(unterlage(breite: nil, hoehe: nil).gestreckt)
        XCTAssertNil(unterlage(breite: 1536, hoehe: nil).gestreckt)
        XCTAssertNil(unterlage(breite: 0, hoehe: 1024).gestreckt, "0 ist keine Grösse, nicht «nein»")
        XCTAssertNil(unterlage(breite: 0, hoehe: 1024).breite)
    }

    func testDieTafelSagtJedeLageMitEigenemSatz() {
        XCTAssertTrue(Blattunterlage.tafelsatz(nil, ordner: "/mappe").contains("Grau"))
        XCTAssertTrue(Blattunterlage.tafelsatz(unterlage(breite: 1024, hoehe: 1024),
                                               ordner: "/mappe").contains("gestreckt"))
        XCTAssertTrue(Blattunterlage.tafelsatz(unterlage(), ordner: "/mappe")
            .contains("Blatt auf Bild"))
        XCTAssertTrue(Blattunterlage.tafelsatz(unterlage(breite: nil, hoehe: nil),
                                               ordner: "/mappe").contains("nicht bekannt"))
        var s = Ebenenstapel()
        s.legeUnterlage(unterlage())
        s.setzeUnterlageSichtbar(false)
        XCTAssertTrue(Blattunterlage.tafelsatz(s.unterlage, ordner: "/mappe")
            .contains("ausgeblendet"))
        let fremd = Blattunterlage.tafelsatz(unterlage(ordner: "/mappe-a"), ordner: "/mappe-b")
        XCTAssertTrue(fremd.contains("«/mappe-a»") && fremd.contains("«/mappe-b»"), fremd)
        XCTAssertTrue(fremd.contains("nicht hinaus"), fremd)
    }

    /// **Tafel, Titel und Ablegen lesen eine Regel** (Befund Durchsicht der Welle 2b,
    /// 23.09.2026): Nach einem Mappenwechsel versprach die Tafel «wird auf X gerechnet» und
    /// der Titel «Skizze über X», während das Ablegen die Skizze abwies. Geprüft an der
    /// Wirkung, für jede Lage: Was der Ablageplan mit `ueber` X parken würde, kündigen Tafel
    /// und Titel als X an — und nur das.
    func testTafelUndTitelSagenDasselbeWieDerAblageplan() {
        let ausgabe = Ebenenausgabe.aus(stapel(bezeichnet: 1).plan(.eineSkizze)) { _ in self.png }
        var lagen: [(String, Blattunterlage?, String?)] = [("keine Unterlage", nil, "/mappe")]
        for (mappeDerUnterlage, jetzt) in [("/mappe", "/mappe"), ("/mappe-a", "/mappe-b"),
                                           ("", ""), ("", "/mappe"), ("/mappe", "")] {
            for (breite, hoehe) in [(1536, 1024), (1024, 1024)] as [(Int?, Int?)]
                + [(nil, nil)] {
                for sichtbar in [true, false] {
                    var s = Ebenenstapel()
                    s.legeUnterlage(unterlage(ordner: mappeDerUnterlage, breite: breite,
                                              hoehe: hoehe))
                    s.setzeUnterlageSichtbar(sichtbar)
                    lagen.append(("aus «\(mappeDerUnterlage)», jetzt «\(jetzt)», "
                                  + "\(String(describing: breite)), sichtbar \(sichtbar)",
                                  s.unterlage, jetzt))
                }
            }
        }
        var gesehen: Set<String> = []
        for (name, u, jetzt) in lagen {
            let plan = Ablageplan.aus(Skizzenpaket(ausgabe: ausgabe, unterlage: u),
                                      ordner: jetzt)
            let satz = Blattunterlage.tafelsatz(u, ordner: jetzt)
            let titel = Blattunterlage.blatttitel(ebene: "Variante A", unterlage: u,
                                                  ordner: jetzt)
            let versprochen = satz.contains("auf «Lauf 07» gerechnet")
            switch plan {
            case .parke(_, let ueber?):
                gesehen.insert("mit")
                XCTAssertEqual(ueber, "lauf-07.png", name)
                XCTAssertTrue(versprochen, "\(name): \(satz)")
                XCTAssertEqual(titel, "Skizze über Lauf 07 · Variante A", name)
            case .parke(_, nil):
                gesehen.insert("ohne")
                XCTAssertFalse(versprochen, "\(name): \(satz)")
                XCTAssertTrue(satz.contains("Grau"), "\(name): \(satz)")
                XCTAssertEqual(titel, "Skizze · Variante A", name)
            case .nicht(let grund):
                gesehen.insert("abgelehnt")
                XCTAssertFalse(versprochen, "\(name): \(satz)")
                XCTAssertTrue(satz.contains("nicht hinaus"), "\(name): \(satz)")
                XCTAssertTrue(grund.contains("Dort gibt es das Bild nicht"), grund)
                XCTAssertEqual(titel, "Skizze · Variante A", name)
            }
        }
        // DIE PROBE MUSS JEDEN AUSGANG GESEHEN HABEN, sonst prüft sie einen nicht.
        XCTAssertEqual(gesehen, ["mit", "ohne", "abgelehnt"])
    }

    // --------------------------------------------------------- 4 · durch das Parkfach

    /// Der Weg der App: Stapel → Ausgabe → Ablageplan → Parkfach → **Neustart** → Anfrage.
    func testDieUnterlageGehtDurchFachUndNeustartBisInDieAnfrage() throws {
        let ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("unterlage-probe-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: ordner) }

        var s = stapel(bezeichnet: 1)
        s.legeUnterlage(unterlage())
        let ausgabe = Ebenenausgabe.aus(s.plan(.eineSkizze)) { _ in self.png }
        let plan = Ablageplan.aus(Skizzenpaket(ausgabe: ausgabe, unterlage: s.unterlage),
                                  ordner: "/mappe")
        guard case .parke(let bilder, let ueber) = plan else { return XCTFail("\(plan)") }
        XCTAssertEqual(ueber, "lauf-07.png")
        try Parkfach(ordner: ordner).parke(bilder, ueber: ueber, ordner: "/mappe")

        let wieder = try Parkfach(ordner: ordner)
        let e = try XCTUnwrap(wieder.naechster)
        XCTAssertEqual(e.ueber, "lauf-07.png", "die Unterlage überlebt den Neustart")
        let r = try rumpf(try Anfragen.skizze(e, png: try XCTUnwrap(wieder.png(e.schluessel)),
                                              anmeldung: nil))
        XCTAssertEqual(r["ueber"], .text("lauf-07.png"))
        XCTAssertEqual(r["ordner"], .text("/mappe"))
    }

    func testAusgeblendetGehtOhneUeberHinaus() throws {
        let ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("unterlage-probe-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: ordner) }

        var s = stapel(bezeichnet: 1)
        s.legeUnterlage(unterlage())
        s.setzeUnterlageSichtbar(false)
        let ausgabe = Ebenenausgabe.aus(s.plan(.eineSkizze)) { _ in self.png }
        guard case .parke(let bilder, let ueber) =
                Ablageplan.aus(Skizzenpaket(ausgabe: ausgabe, unterlage: s.unterlage),
                               ordner: "/mappe") else { return XCTFail() }
        XCTAssertNil(ueber)
        try Parkfach(ordner: ordner).parke(bilder, ueber: ueber, ordner: "/mappe")
        let e = try XCTUnwrap(try Parkfach(ordner: ordner).naechster)
        XCTAssertNil(e.ueber)
        XCTAssertNil(try rumpf(try Anfragen.skizze(e, png: png, anmeldung: nil))["ueber"],
                     "ohne Unterlage fehlt das Feld")
    }

    func testJedeVarianteTraegtDieUnterlage() throws {
        let ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("unterlage-probe-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: ordner) }

        var s = stapel(bezeichnet: 2)
        s.legeUnterlage(unterlage())
        let ausgabe = Ebenenausgabe.aus(s.plan(.ebenenAlsVarianten)) { _ in self.png }
        guard case .parke(let bilder, let ueber) =
                Ablageplan.aus(Skizzenpaket(ausgabe: ausgabe, unterlage: s.unterlage),
                               ordner: "/mappe") else { return XCTFail() }
        let gelegt = try Parkfach(ordner: ordner).parke(bilder, ueber: ueber, ordner: "/mappe")
        XCTAssertEqual(gelegt.count, 2)
        let wieder = try Parkfach(ordner: ordner)
        XCTAssertEqual(wieder.eintraege.map { $0.ueber }, ["lauf-07.png", "lauf-07.png"])
        XCTAssertEqual(Set(wieder.eintraege.compactMap { $0.name }), ["Variante A", "Variante B"])
    }
}
