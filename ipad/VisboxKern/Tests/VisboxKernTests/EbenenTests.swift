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

    /// Die unterste Ebene hat keine darunter — die Wahl fällt auf die darüber, nicht ins
    /// Leere (Wächterlücke aus Durchsicht A, 22.09.2026).
    func testEntfernenDerUnterstenAktivenWaehltDieDarueber() {
        var (s, a, b, c) = dreiBezeichnete()
        s.waehle(a)
        XCTAssertTrue(s.entferne(a))
        XCTAssertEqual(s.aktiv, b)
        XCTAssertEqual(s.ebenen.map { $0.id }, [b, c])
        // Und was hinausginge, sind genau die beiden, die bleiben.
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [b, c])
    }

    func testVerschiebenAmRandTutNichts() {
        var (s, a, b, c) = dreiBezeichnete()
        XCTAssertFalse(s.verschiebe(c, nachOben: true), "die oberste kann nicht höher")
        XCTAssertFalse(s.verschiebe(a, nachOben: false), "die unterste kann nicht tiefer")
        XCTAssertFalse(s.verschiebe(UUID(), nachOben: true), "eine fremde Ebene gibt es nicht")
        XCTAssertEqual(s.ebenen.map { $0.id }, [a, b, c])
        XCTAssertEqual(teile(s.plan(.ebenenAlsVarianten)).map { $0.name },
                       ["Variante A", "Variante B", "Variante C"])
    }

    func testAufEineAusgeblendeteEbeneWirdNichtGezeichnet() {
        var s = Ebenenstapel()
        XCTAssertTrue(s.aktiveIstZeichenbar)
        s.setzeSichtbar(s.aktiv, false)
        XCTAssertFalse(s.aktiveIstZeichenbar)
    }

    /// Entscheid Nr. 4 und die Hand (Durchsicht der Welle 2b, 23.09.2026): Auf einer
    /// ausgeblendeten Ebene schiebt der Stift nicht — **ausser mit der Hand**, die genau dafür
    /// da ist. Auf einer sichtbaren zeichnet er, und die Regel mischt sich nicht ein.
    func testMitDerHandSchiebtAuchDerStiftSonstNurDerFinger() {
        var s = Ebenenstapel()
        for w in Zeichenwerkzeug.allCases {
            XCTAssertFalse(s.stiftSchiebtNicht(mit: w), "sichtbar, \(w)")
        }
        s.setzeSichtbar(s.aktiv, false)
        XCTAssertFalse(s.stiftSchiebtNicht(mit: .hand), "ausgeblendet, mit der Hand schiebt er")
        for w in [Zeichenwerkzeug.stift, .radiererStriche, .radiererFlaeche] {
            XCTAssertTrue(s.stiftSchiebtNicht(mit: w), "ausgeblendet, \(w): nur der Finger")
        }
    }

    // ----------------------------------------- leer heisst: im Bild deckt nichts

    /// Flächig ganz weggewischt: PencilKit führt die Striche noch, im Bild deckt nichts.
    /// Dann geht die Ebene nicht als leeres PNG hinaus (Befund Durchsicht A, 22.09.2026).
    func testGanzWeggewischtIstLeerTrotzStrichen() {
        var s = Ebenenstapel()
        let a = s.aktiv
        s.setzeStriche(a, 5, alpha: Data(repeating: 0, count: 64))
        XCTAssertTrue(s.aktiveEbene.istLeer)
        for art in Ebenenstapel.Ausgabeart.allCases {
            XCTAssertEqual(s.plan(art), .nichtsGezeichnet(ausgeblendetGezeichnet: 0), "\(art)")
        }
        // Ein leerer Puffer ist kein gemaltes Bild — auch nichts, das deckt.
        s.setzeStriche(a, 5, alpha: Data())
        XCTAssertTrue(s.aktiveEbene.istLeer)
    }

    func testEinEinzigerDeckenderBildpunktZaehlt() {
        var s = Ebenenstapel()
        let a = s.aktiv
        var alpha = Data(repeating: 0, count: 64)
        alpha[63] = 1
        s.setzeStriche(a, 5, alpha: alpha)
        XCTAssertEqual(s.aktiveEbene.striche, 5)
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [a])
        // Wieder weggewischt: wieder leer — die Zahl folgt dem Bild, nicht der Vorgeschichte.
        s.setzeStriche(a, 5, alpha: Data(repeating: 0, count: 64))
        XCTAssertTrue(s.aktiveEbene.istLeer)
    }

    // ------------------------------------- das Bild, wie es im Speicher liegt

    /// Ein Bild mit vier Bytes je Bildpunkt, Deckung an `alphaStelle`, dazu `fuell`
    /// Füllbytes am Ende jeder Zeile. Farb- und Füllbytes tragen 255 — sie dürfen nie zählen.
    private func bild(breite: Int, hoehe: Int, fuell: Int, alphaStelle: Int,
                      deckt: [(Int, Int)] = []) -> Deckungsbild? {
        let zeilenlaenge = breite * 4 + fuell
        var daten = Data(repeating: 255, count: zeilenlaenge * hoehe)
        for y in 0..<hoehe {
            for x in 0..<breite { daten[y * zeilenlaenge + x * 4 + alphaStelle] = 0 }
        }
        for (x, y) in deckt { daten[y * zeilenlaenge + x * 4 + alphaStelle] = 1 }
        return Deckungsbild(daten: daten, breite: breite, hoehe: hoehe,
                            zeilenlaenge: zeilenlaenge, punktlaenge: 4,
                            alphaStelle: alphaStelle)
    }

    /// Gelesen wird **nur** die Deckung: Farbbytes und Füllbytes am Zeilenende tragen 255
    /// und machen ein durchsichtiges Bild nicht zu einem bezeichneten.
    func testDasBildZeigtNurWasDecktNichtFarbeOderFuellung() throws {
        for stelle in [0, 3] {
            let leer = try XCTUnwrap(bild(breite: 5, hoehe: 3, fuell: 8, alphaStelle: stelle))
            XCTAssertFalse(leer.zeigtEtwas, "Deckung an Stelle \(stelle)")
            // Der letzte Bildpunkt der letzten Zeile — dort, wo ein Abbruch zu früh ihn verpasste.
            let ecke = try XCTUnwrap(bild(breite: 5, hoehe: 3, fuell: 8, alphaStelle: stelle,
                                          deckt: [(4, 2)]))
            XCTAssertTrue(ecke.zeigtEtwas, "Deckung an Stelle \(stelle)")
        }
    }

    /// Ganz weggewischt heisst leer, auch am Bild aus dem Speicher — und ein Bildpunkt reicht.
    func testDasGeleseneBildEntscheidetUeberLeer() throws {
        var s = Ebenenstapel()
        let a = s.aktiv
        s.setzeStriche(a, 5, deckung: bild(breite: 6, hoehe: 4, fuell: 4, alphaStelle: 3))
        XCTAssertTrue(s.aktiveEbene.istLeer)
        XCTAssertFalse(s.aktiveEbene.deckungUngewiss)
        s.setzeStriche(a, 5, deckung: bild(breite: 6, hoehe: 4, fuell: 4, alphaStelle: 3,
                                           deckt: [(2, 1)]))
        XCTAssertEqual(s.aktiveEbene.striche, 5)
        XCTAssertFalse(s.aktiveEbene.deckungUngewiss)
    }

    /// **Nicht lesbar heisst nicht geprüft**, nicht still «bezeichnet» (Befund Durchsicht,
    /// 22.09.2026): Die Strichzahl gilt, und die Ebene trägt den Vorbehalt — bis ein Bild
    /// gelesen ist oder keine Abdeckung mehr im Spiel ist.
    func testEinNichtLesbaresBildLaesstDieDeckungUngewiss() throws {
        var s = Ebenenstapel()
        let a = s.aktiv
        s.setzeStriche(a, 5, deckung: nil)
        XCTAssertEqual(s.aktiveEbene.striche, 5, "die Zahl gilt, nichts wird verschwiegen")
        XCTAssertTrue(s.aktiveEbene.deckungUngewiss)
        XCTAssertEqual(teile(s.plan(.eineSkizze)).first?.ebenen.map { $0.id }, [a])
        s.setzeStriche(a, 5, deckung: bild(breite: 2, hoehe: 2, fuell: 0, alphaStelle: 0,
                                           deckt: [(0, 0)]))
        XCTAssertFalse(s.aktiveEbene.deckungUngewiss, "gelesen: nicht mehr ungewiss")
        s.setzeStriche(a, 5, deckung: nil)
        XCTAssertTrue(s.aktiveEbene.deckungUngewiss)
        s.setzeStriche(a, 3)
        XCTAssertFalse(s.aktiveEbene.deckungUngewiss, "ohne Abdeckung zählt die Zahl")
        s.setzeStriche(a, 0, deckung: nil)
        XCTAssertFalse(s.aktiveEbene.deckungUngewiss, "ohne Striche ist nichts ungewiss")
        XCTAssertTrue(s.aktiveEbene.istLeer)
    }

    /// Masse, die nicht zum Puffer passen, ergeben kein Bild — geraten wird nicht.
    func testWidersinnigeMasseErgebenKeinBild() {
        let d = Data(repeating: 0, count: 64)
        XCTAssertNotNil(Deckungsbild(daten: d, breite: 4, hoehe: 4, zeilenlaenge: 16,
                                     punktlaenge: 4, alphaStelle: 3))
        XCTAssertNil(Deckungsbild(daten: d, breite: 4, hoehe: 4, zeilenlaenge: 12,
                                  punktlaenge: 4, alphaStelle: 3), "Zeile kürzer als ihre Punkte")
        XCTAssertNil(Deckungsbild(daten: d, breite: 4, hoehe: 5, zeilenlaenge: 16,
                                  punktlaenge: 4, alphaStelle: 3), "Puffer zu kurz")
        XCTAssertNil(Deckungsbild(daten: d, breite: 4, hoehe: 4, zeilenlaenge: 16,
                                  punktlaenge: 4, alphaStelle: 4), "Deckung ausserhalb")
        XCTAssertNil(Deckungsbild(daten: d, breite: 0, hoehe: 4, zeilenlaenge: 16,
                                  punktlaenge: 4, alphaStelle: 3), "kein Bildpunkt")
        XCTAssertNil(Deckungsbild(daten: d, breite: Int.max, hoehe: 1, zeilenlaenge: 16,
                                  punktlaenge: 4, alphaStelle: 3), "Überlauf")
        // Die letzte Zeile braucht keine Füllbytes: genau so lang wie nötig reicht.
        XCTAssertNotNil(Deckungsbild(daten: Data(count: 16 + 12), breite: 3, hoehe: 2,
                                     zeilenlaenge: 16, punktlaenge: 4, alphaStelle: 0))
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

    /// Der Vor-Zweig des Abgleichs (Wächterlücke aus Durchsicht A, 22.09.2026).
    func testAbgleichenSagtBeiVerpasstemVorNichtGezaehlt() {
        var z = Schrittzaehler()
        for _ in 0..<3 { z.neuerSchritt() }
        // Der UndoManager kann vor, der Zähler hat kein Zurück mitbekommen.
        z.abgleichen(kannZurueck: true, kannVor: true)
        XCTAssertNil(z.vor)
        XCTAssertEqual(z.zurueck, 3)
        // Ein gezähltes Vor bleibt stehen, solange es geht …
        var y = Schrittzaehler()
        for _ in 0..<3 { y.neuerSchritt() }
        y.zurueckGegangen()
        y.zurueckGegangen()
        y.abgleichen(kannZurueck: true, kannVor: true)
        XCTAssertEqual(y.vor, 2)
        // … und wird 0, sobald der UndoManager nicht mehr vor kann.
        y.abgleichen(kannZurueck: true, kannVor: false)
        XCTAssertEqual(y.vor, 0)
    }

    /// Nach dem Neuaufbau der Flächen (Drehen) gilt keine alte Zahl mehr: Was noch geht,
    /// ist nicht gezählt; was nicht geht, ist sicher 0 (Befund Durchsicht A, 22.09.2026).
    func testNachFlaechenNeuGiltKeineAlteZahl() {
        var z = Schrittzaehler()
        for _ in 0..<7 { z.neuerSchritt() }
        z.zurueckGegangen()
        z.flaechenNeu(kannZurueck: true, kannVor: true)
        XCTAssertNil(z.zurueck, "die 6 zählte Schritte der abgebauten Flächen")
        XCTAssertNil(z.vor)
        XCTAssertEqual(z.anzeige, "?/20")
        // Die offene Lücke (`Zeichenstand.stapelAbgebaut`): Bleiben Schritte der abgebauten
        // Flächen stehen, macht weder ein neuer Strich noch der Abgleich daraus eine Zahl.
        z.neuerSchritt()
        z.abgleichen(kannZurueck: true, kannVor: false)
        XCTAssertEqual(z.anzeige, "?/20")

        var y = Schrittzaehler()
        for _ in 0..<7 { y.neuerSchritt() }
        y.zurueckGegangen()
        y.flaechenNeu(kannZurueck: false, kannVor: false)
        XCTAssertEqual(y.zurueck, 0)
        XCTAssertEqual(y.vor, 0)
        XCTAssertEqual(y.anzeige, "0/20")
        // Danach wird wieder gezählt.
        y.neuerSchritt()
        XCTAssertEqual(y.anzeige, "1/20")
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

    // ------------------------------------------------------------------ der Zug

    /// Befund Durchsicht der Welle 2b (23.09.2026): Kam das Ende eines Zugs nie, blieb er
    /// offen, und «Zurück» über den Knopf galt als «im Zug». Ein Weg ohne Stift schliesst ihn.
    func testEinWegOhneStiftSchliesstEinenAbgebrochenenZug() {
        let a = UUID()
        var z = Zugstand()
        XCTAssertFalse(z.imZug(a))
        z.beginnt(a)
        XCTAssertTrue(z.imZug(a))
        // Das Ende kommt nie. Dann tippt jemand auf «Zurück»:
        XCTAssertEqual(z.ohneStift(), a, "der offene Zug wird genannt, sein Bild steht aus")
        XCTAssertFalse(z.imZug(a), "danach ist die Änderung durch «Zurück» keine im Zug")
        XCTAssertNil(z.ohneStift(), "kein offener Zug, nichts zu nennen")
    }

    func testDasEndeEinesZugsSchliesstNurSeinenEigenen() {
        let a = UUID(), b = UUID()
        var z = Zugstand()
        z.beginnt(a)
        z.endet(a)
        XCTAssertFalse(z.imZug(a), "gewöhnliches Ende")

        z.beginnt(a)
        z.beginnt(b)  // das Ende auf A kam nie
        XCTAssertFalse(z.imZug(a))
        XCTAssertTrue(z.imZug(b))
        z.endet(a)    // kommt verspätet
        XCTAssertTrue(z.imZug(b), "ein spätes Ende auf A schliesst den Zug auf B nicht")
        z.endet(b)
        XCTAssertNil(z.auf)
    }
}
