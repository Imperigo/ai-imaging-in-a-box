import Foundation
import XCTest
import VisboxKern

/// Die Regeln der Zeichenfläche — geprüft an der **Wirkung**: was hinausginge, was der
/// Zähler zeigt, was der Doppeltipp wählt.
final class EbenenTests: XCTestCase {

    // ------------------------------------------------------------------ Hilfen

    /// Ein Stapel mit drei bezeichneten Ebenen A (unten), B, C (oben).
    private func dreiBezeichnete() -> (Ebenenstapel, UUID, UUID, UUID) {
        var s = Ebenenstapel()
        let a = s.aktiv
        s.setzeStriche(a, 3)
        let b = s.legeAn()!.id
        s.setzeStriche(b, 1)
        let c = s.legeAn()!.id
        s.setzeStriche(c, 7)
        return (s, a, b, c)
    }

    private func teile(_ plan: Ebenenstapel.Plan, datei: StaticString = #filePath,
                       zeile: UInt = #line) -> [Ebenenstapel.Teil] {
        guard case .teile(let t) = plan else {
            XCTFail("keine Teile, sondern \(plan)", file: datei, line: zeile)
            return []
        }
        return t
    }

    private let einPNG = Data(Ebenenausgabe.pngKennung + [0, 0, 0, 13])

    // ---------------------------------------------- gerechnet wird, was sichtbar ist

    func testEineAusgeblendeteEbeneGehtInKeinerAusgabeartMit() {
        var (s, a, b, c) = dreiBezeichnete()
        s.setzeSichtbar(b, false)
        for art in Ebenenstapel.Ausgabeart.allCases {
            let ids = teile(s.plan(art)).flatMap { $0.ebenen.map { $0.id } }
            XCTAssertFalse(ids.contains(b), "\(art): die ausgeblendete Ebene ging mit")
            XCTAssertEqual(Set(ids), [a, c], "\(art)")
        }
    }

    func testDieReihenfolgeIstDieStapelfolgeVonUntenNachOben() {
        var (s, a, b, c) = dreiBezeichnete()
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [a, b, c])
        XCTAssertEqual(teile(s.plan(.ebenenAlsVarianten)).map { $0.ebenen[0].id }, [a, b, c])
        // Umgestapelt ist umgeordnet — die Ausgabe folgt dem Stapel, nicht dem Anlegen.
        XCTAssertTrue(s.verschiebe(a, nachOben: true))
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [b, a, c])
        XCTAssertEqual(s.vonObenGesehen.map { $0.id }, [c, a, b])
    }

    func testEineSkizzeIstEinBildAusAllenSichtbaren() {
        let (s, _, _, _) = dreiBezeichnete()
        let t = teile(s.plan(.eineSkizze))
        XCTAssertEqual(t.count, 1)
        XCTAssertEqual(t.first?.name, "Variante A + Variante B + Variante C")
    }

    func testEineLeereSichtbareEbeneErzeugtKeineVariante() {
        var (s, a, b, c) = dreiBezeichnete()
        s.setzeStriche(b, 0)
        XCTAssertEqual(teile(s.plan(.ebenenAlsVarianten)).map { $0.ebenen[0].id }, [a, c])
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [a, c])
    }

    func testNichtsGezeichnetIstKeinLeeresBild() {
        var s = Ebenenstapel()
        for art in Ebenenstapel.Ausgabeart.allCases {
            XCTAssertEqual(s.plan(art), .nichtsGezeichnet(ausgeblendetGezeichnet: 0))
        }
        // Striche auf einer AUSGEBLENDETEN Ebene: immer noch nichts, das mitgeht — aber
        // gesagt wird, dass da etwas liegt.
        s.setzeStriche(s.aktiv, 4)
        s.setzeSichtbar(s.aktiv, false)
        XCTAssertEqual(s.plan(.eineSkizze), .nichtsGezeichnet(ausgeblendetGezeichnet: 1))
        // Und der Maler wird dann gar nicht erst gefragt.
        var gefragt = 0
        let aus = Ebenenausgabe.aus(s.plan(.eineSkizze)) { _ in gefragt += 1; return self.einPNG }
        XCTAssertEqual(aus, .nichtsGezeichnet(ausgeblendetGezeichnet: 1))
        XCTAssertEqual(gefragt, 0)
    }

    func testZuVieleVariantenWerdenAbgelehntUndNichtGekuerzt() {
        var (s, _, _, _) = dreiBezeichnete()
        let d = s.legeAn()!.id
        s.setzeStriche(d, 2)
        XCTAssertEqual(s.plan(.ebenenAlsVarianten),
                       .zuVieleVarianten(sichtbar: 4, hoechstens: Ebenenstapel.hoechstensVarianten))
        // Als eine Skizze geht dasselbe: ein Bild, vier Ebenen.
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.count, 4)
        // Eine ausblenden, und es sind wieder drei.
        s.setzeSichtbar(d, false)
        XCTAssertEqual(teile(s.plan(.ebenenAlsVarianten)).count, 3)
    }

    // ------------------------------------------------------------------ die Ausgabe

    func testDieAusgabeTraegtJeTeilEinPNGInStapelfolge() {
        let (s, _, _, _) = dreiBezeichnete()
        let aus = Ebenenausgabe.aus(s.plan(.ebenenAlsVarianten)) { teil in
            self.einPNG + Data(teil.name.utf8)
        }
        guard case .bilder(let bilder) = aus else { return XCTFail("\(aus)") }
        XCTAssertEqual(bilder.map { $0.name }, ["Variante A", "Variante B", "Variante C"])
        XCTAssertEqual(bilder.map { $0.ebenen }, [["Variante A"], ["Variante B"], ["Variante C"]])
        XCTAssertEqual(bilder[1].png, einPNG + Data("Variante B".utf8))
    }

    func testEinFehlendesBildMachtDieGanzeAusgabeUngueltig() {
        let (s, _, _, _) = dreiBezeichnete()
        let aus = Ebenenausgabe.aus(s.plan(.ebenenAlsVarianten)) { teil in
            teil.name == "Variante B" ? nil : self.einPNG
        }
        guard case .nichtErzeugt(let grund) = aus else {
            return XCTFail("ein halbes Paket ging durch: \(aus)")
        }
        XCTAssertTrue(grund.contains("Variante B"), grund)
    }

    func testWasKeinPNGIstGehtNichtAlsPNGHinaus() {
        let (s, _, _, _) = dreiBezeichnete()
        for falsch in [Data(), Data("kein Bild".utf8), Data(Ebenenausgabe.pngKennung.dropLast())] {
            let aus = Ebenenausgabe.aus(s.plan(.eineSkizze)) { _ in falsch }
            guard case .nichtErzeugt = aus else { return XCTFail("\(falsch) ging als PNG durch") }
        }
    }

    // ------------------------------------------------------------------ die Grenzen

    func testMehrAlsDieHoechstzahlWirdNichtAngelegt() {
        var s = Ebenenstapel()
        while s.kannAnlegen { XCTAssertNotNil(s.legeAn()) }
        XCTAssertEqual(s.ebenen.count, Ebenenstapel.hoechstensEbenen)
        XCTAssertNil(s.legeAn())
        XCTAssertEqual(s.ebenen.count, Ebenenstapel.hoechstensEbenen)
    }

    func testDieLetzteEbeneBleibtStehen() {
        var s = Ebenenstapel()
        XCTAssertFalse(s.entferne(s.aktiv))
        XCTAssertEqual(s.ebenen.count, 1)
    }

    func testEntfernenDerAktivenWaehltEineVorhandene() {
        var (s, _, b, c) = dreiBezeichnete()
        XCTAssertEqual(s.aktiv, c)
        XCTAssertTrue(s.entferne(c))
        XCTAssertEqual(s.aktiv, b)
        XCTAssertEqual(s.aktiveEbene.id, b)
    }

    func testDeckkraftBleibtZwischenMindestwertUndEins() {
        var s = Ebenenstapel()
        let a = s.aktiv
        s.setzeDeckkraft(a, 0)
        XCTAssertEqual(s.aktiveEbene.deckkraft, Ebenenstapel.mindestDeckkraft)
        s.setzeDeckkraft(a, 3)
        XCTAssertEqual(s.aktiveEbene.deckkraft, 1)
        s.setzeDeckkraft(a, .nan)
        XCTAssertEqual(s.aktiveEbene.deckkraft, 1)
        s.setzeDeckkraft(a, 0.55)
        XCTAssertEqual(s.aktiveEbene.deckkraft, 0.55)
    }

    func testEinLeererNameWirdAbgelehnt() {
        var s = Ebenenstapel()
        let a = s.aktiv
        XCTAssertFalse(s.benenne(a, "   \n"))
        XCTAssertEqual(s.aktiveEbene.name, "Variante A")
        XCTAssertTrue(s.benenne(a, "  Attika zurück  "))
        XCTAssertEqual(s.aktiveEbene.name, "Attika zurück")
        XCTAssertTrue(s.benenne(a, String(repeating: "x", count: 100)))
        XCTAssertEqual(s.aktiveEbene.name.count, Ebenenstapel.hoechstensNamenslaenge)
    }

    func testVorgabenamenWiederholenSichNicht() {
        var s = Ebenenstapel()
        let b = s.legeAn()!.id
        _ = s.legeAn()
        XCTAssertTrue(s.entferne(b))
        // A und C stehen noch; die neue heisst B, nicht zum zweiten Mal C.
        XCTAssertEqual(s.legeAn()?.name, "Variante B")
        XCTAssertEqual(Set(s.ebenen.map { $0.name }).count, s.ebenen.count)
    }

    func testAufEineAusgeblendeteEbeneWirdNichtGezeichnet() {
        var s = Ebenenstapel()
        XCTAssertTrue(s.aktiveIstZeichenbar)
        s.setzeSichtbar(s.aktiv, false)
        XCTAssertFalse(s.aktiveIstZeichenbar)
    }

    // ------------------------------------------------------------------ Zurück und Vor

    func testDerZaehlerHoertBeiZwanzigAuf() {
        var z = Schrittzaehler()
        XCTAssertEqual(z.anzeige, "0/20")
        for _ in 0..<25 { z.neuerSchritt() }
        XCTAssertEqual(z.zurueck, Schrittzaehler.tiefe)
        XCTAssertEqual(z.anzeige, "20/20")
    }

    func testZurueckUndVorZaehlenGegeneinander() {
        var z = Schrittzaehler()
        for _ in 0..<7 { z.neuerSchritt() }
        z.zurueckGegangen()
        z.zurueckGegangen()
        XCTAssertEqual(z.zurueck, 5)
        XCTAssertEqual(z.vor, 2)
        z.vorGegangen()
        XCTAssertEqual(z.zurueck, 6)
        XCTAssertEqual(z.vor, 1)
        // Ein neuer Strich nimmt die Vor-Schritte weg.
        z.neuerSchritt()
        XCTAssertEqual(z.zurueck, 7)
        XCTAssertEqual(z.vor, 0)
    }

    func testEinVerpassterSchrittIstNichtGezaehltUndNichtNull() {
        var z = Schrittzaehler()
        // Der UndoManager kann zurück, der Zähler hat nichts mitbekommen.
        z.abgleichen(kannZurueck: true, kannVor: false)
        XCTAssertNil(z.zurueck)
        XCTAssertEqual(z.anzeige, "?/20")
        // Weitere Schritte machen daraus keine erfundene Zahl.
        z.neuerSchritt()
        XCTAssertNil(z.zurueck)
        // Erst wenn der UndoManager nichts mehr kann, ist es wieder sicher 0.
        z.abgleichen(kannZurueck: false, kannVor: false)
        XCTAssertEqual(z.anzeige, "0/20")
    }

    func testAbgleichenSetztAufNullWasNichtMehrGeht() {
        var z = Schrittzaehler()
        for _ in 0..<3 { z.neuerSchritt() }
        z.zurueckGegangen()
        z.abgleichen(kannZurueck: true, kannVor: false)
        XCTAssertEqual(z.zurueck, 2)
        XCTAssertEqual(z.vor, 0)
    }

    // ------------------------------------------------------------------ der Doppeltipp

    func testDoppeltippSchaltetStiftUndRadierer() {
        var w = Werkzeugwahl()
        XCTAssertEqual(w.werkzeug, .stift)
        w.doppeltipp()
        XCTAssertEqual(w.werkzeug, .radiererStriche)
        w.doppeltipp()
        XCTAssertEqual(w.werkzeug, .stift)
    }

    func testDoppeltippNimmtDenZuletztBenutztenRadierer() {
        var w = Werkzeugwahl()
        w.waehle(.radiererFlaeche)
        w.waehle(.stift)
        w.doppeltipp()
        XCTAssertEqual(w.werkzeug, .radiererFlaeche)
    }

    func testDerZweiteDoppeltippFuehrtZumWerkzeugDavorZurueck() {
        var w = Werkzeugwahl()
        w.waehle(.hand)
        w.doppeltipp()
        XCTAssertEqual(w.werkzeug, .radiererStriche)
        w.doppeltipp()
        XCTAssertEqual(w.werkzeug, .hand, "zurück zur Hand, nicht still zum Stift")
    }

    func testDieHandIstKeinRadierer() {
        XCTAssertEqual(Zeichenwerkzeug.allCases.filter { $0.istRadierer },
                       [.radiererStriche, .radiererFlaeche])
    }
}
