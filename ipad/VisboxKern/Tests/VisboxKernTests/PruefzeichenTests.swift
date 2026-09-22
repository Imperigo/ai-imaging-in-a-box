import Foundation
import XCTest
import VisboxKern

/// Das Prüfzeichen am Bild — geprüft an dem, **was am Bild steht**: Farbe, Wort, Zahl und
/// Vorbehalt, für jede Kombination aus Urteil, Lesart, Zahl und Hinweisen.
final class PruefzeichenTests: XCTestCase {

    private let urteile: [Urteil] = [.bestanden, .durchgefallen, .nichtGemessen]
    private let zahlen: [Double?] = [nil, 0, 0.93, 0.36, -0.001, .nan, .infinity]
    private let hinweislisten: [[String]] = [
        [],
        ["SKIZZE NICHT ANGEKOMMEN: z-image-turbo nimmt gemessen kein Ausgangsbild an (x)."],
        ["Ein anderer Hinweis."],
    ]

    /// Jede Kombination, die ein Bild haben kann.
    private func alleZeichen() -> [(Urteil, Bildlesart, Double?, Pruefzeichen)] {
        var alle: [(Urteil, Bildlesart, Double?, Pruefzeichen)] = []
        for u in urteile {
            for l in Bildlesart.allCases {
                for z in zahlen {
                    for h in hinweislisten {
                        alle.append((u, l, z, Pruefzeichen(urteil: u, lesart: l, pruefzahl: z,
                                                           unterschied: z, hinweise: h)))
                    }
                }
            }
        }
        return alle
    }

    // ------------------------------------------------ nicht gemessen ist nie bestanden

    func testNichtGemessenSiehtNieAusWieBestanden() {
        let bestanden = Zeichenart.bestanden
        for (u, _, z, zeichen) in alleZeichen() where u == .nichtGemessen {
            XCTAssertNotEqual(zeichen.art, .bestanden, "nicht gemessen, Zahl \(String(describing: z))")
            XCTAssertNotEqual(zeichen.art.rand, bestanden.rand)
            XCTAssertNotEqual(zeichen.art.schrift, bestanden.schrift)
            XCTAssertFalse(zeichen.zeile.contains(bestanden.wort), zeichen.zeile)
            // UND NICHT WIE GAR NICHTS: ein Wort steht immer da.
            XCTAssertFalse(zeichen.zeile.isEmpty)
        }
    }

    func testNichtGemessenTraegtNieEineZahl() {
        // Auch wenn eine mitkommt: ohne Messung ist sie nicht die Zahl dieses Urteils.
        for (u, _, _, zeichen) in alleZeichen() where u == .nichtGemessen {
            XCTAssertEqual(zeichen.zahl, .keine, zeichen.zeile)
            XCTAssertFalse(zeichen.zeile.contains(where: { $0.isNumber }), zeichen.zeile)
        }
    }

    func testNichtGemessenBeimPruefenHatSeinEigenesZeichen() {
        let z = Pruefzeichen(urteil: .nichtGemessen, lesart: .pruefen, pruefzahl: 0.93)
        XCTAssertEqual(z.art, .nichtGemessen)
        XCTAssertEqual(z.zeile, "NICHT GEMESSEN")
        XCTAssertTrue(z.art.gestrichelt, "von weitem und ohne Farbensehen unterscheidbar")
        XCTAssertFalse(Zeichenart.bestanden.gestrichelt)
    }

    // ------------------------------------------------------ eine fehlende Zahl ist nie 0

    func testEineFehlendeZahlWirdNie000() {
        for (_, _, z, zeichen) in alleZeichen() where z == nil || !(z!.isFinite) {
            XCTAssertFalse(zeichen.zeile.contains("0.00"), zeichen.zeile)
            XCTAssertNotEqual(zeichen.zahl, .wert("0.00"))
        }
        let ohne = Pruefzeichen(urteil: .bestanden, lesart: .pruefen, pruefzahl: nil)
        XCTAssertEqual(ohne.zahl, .fehlt)
        XCTAssertEqual(ohne.zeile, "BESTANDEN · ohne Zahl",
                       "das Urteil verlangt eine Zahl, und dass sie fehlt, steht da")
        XCTAssertEqual(Pruefzeichen(urteil: .durchgefallen, lesart: .pruefen,
                                    pruefzahl: .nan).zeile, "DURCHGEFALLEN · ohne Zahl")
    }

    func testEineEchteNullBleibtNull() {
        // Die Gegenprobe: Eine gemessene 0 ist eine Zahl und wird geschrieben.
        XCTAssertEqual(Pruefzeichen(urteil: .durchgefallen, lesart: .pruefen,
                                    pruefzahl: 0).zeile, "DURCHGEFALLEN · 0.00")
        XCTAssertEqual(Pruefzeichen(urteil: .durchgefallen, lesart: .pruefen,
                                    pruefzahl: -0.001).zeile, "DURCHGEFALLEN · 0.00")
    }

    func testFarbeWortUndZahlWieImEntwurf() {
        XCTAssertEqual(Pruefzeichen(urteil: .bestanden, lesart: .pruefen,
                                    pruefzahl: 0.93).zeile, "BESTANDEN · 0.93")
        XCTAssertEqual(Pruefzeichen(urteil: .durchgefallen, lesart: .pruefen,
                                    pruefzahl: 0.364).zeile, "DURCHGEFALLEN · 0.36")
        XCTAssertEqual(Zeichenart.bestanden.rand.hex, "#4ea373")
        XCTAssertEqual(Zeichenart.bestanden.schrift.hex, "#8fd4ac")
        XCTAssertEqual(Zeichenart.durchgefallen.rand.hex, "#e2776f")
        XCTAssertEqual(Zeichenart.nichtGemessen.rand.hex, "#c8a53f")
        XCTAssertEqual(Zeichenart.entwurf.rand.hex, "#6fb3d2")
    }

    // ------------------------------------------------------------------- der Entwurf

    func testDerEntwurfSprichtKeinUrteil() {
        for (_, l, _, zeichen) in alleZeichen() where l == .entwerfen {
            XCTAssertEqual(zeichen.art, .entwurf)
            for wort in [Zeichenart.bestanden.wort, Zeichenart.durchgefallen.wort] {
                XCTAssertFalse(zeichen.zeile.contains(wort), zeichen.zeile)
            }
        }
        let z = Pruefzeichen(urteil: .bestanden, lesart: .entwerfen, pruefzahl: 0.93)
        XCTAssertEqual(z.zeile, "ENTWURF — NICHT GEPRÜFT",
                       "die Prüfzahl ist beim Entwerfen nicht die Zahl des Zeichens")
        XCTAssertEqual(Pruefzeichen(urteil: .bestanden, lesart: .entwerfen, pruefzahl: 0.93,
                                    unterschied: 0.31).zeile,
                       "ENTWURF — NICHT GEPRÜFT · Unterschied 0.31")
    }

    // ------------------------------------------------------- das Zeichen des Servers

    func testEinUnbekanntesZeichenWirdNichtGeraten() {
        for roh in ["ungeprueft", "", "BESTANDEN", "true"] {
            let z = Pruefzeichen(zeichen: roh, lesart: .pruefen, pruefzahl: 0.93)
            XCTAssertEqual(z.art, .unbekannt, roh)
            XCTAssertEqual(z.zahl, .keine, roh)
            XCTAssertFalse(z.zeile.isEmpty, "kein Zeichen sähe aus wie kein Problem")
        }
        XCTAssertEqual(Pruefzeichen(zeichen: "nicht-gemessen", lesart: .pruefen,
                                    pruefzahl: nil).art, .nichtGemessen)
        XCTAssertEqual(Pruefzeichen(zeichen: "bestanden", lesart: .pruefen,
                                    pruefzahl: 0.93).zeile, "BESTANDEN · 0.93")
    }

    // ------------------------------------------------- der Vorbehalt aus Entscheid E24

    func testSkizzeNichtAngekommenGibtEinenSichtbarenVorbehalt() {
        let satz = "SKIZZE NICHT ANGEKOMMEN: z-image-turbo nimmt gemessen kein Ausgangsbild an."
        for u in urteile {
            for l in Bildlesart.allCases {
                let z = Pruefzeichen(urteil: u, lesart: l, pruefzahl: 0.93,
                                     hinweise: ["Ein anderer Hinweis.", satz])
                XCTAssertEqual(z.vorbehalte.count, 1, "\(u) \(l)")
                XCTAssertEqual(z.vorbehalte.first?.satz, satz)
                // SICHTBAR heisst: im Streifen, und darum auch im geteilten Bild.
                // ERST ZAEHLEN, DANN LESEN: Ein `zeilen[1]` ohne zweite Zeile brach den
                // ganzen Lauf ab statt diese eine Probe (Mutationsprobe, 22.09.2026).
                guard z.zeilen.count == 2 else {
                    XCTFail("kein Vorbehalt im Streifen: \(z.zeilen) (\(u), \(l))")
                    continue
                }
                XCTAssertTrue(z.zeilen[1].hasPrefix("SKIZZE NICHT ANGEKOMMEN"), z.zeilen[1])
                XCTAssertTrue(z.vorlesetext.contains(satz))
            }
        }
        // Und auch bei einem Zeichen, das die App nicht kennt.
        XCTAssertEqual(Pruefzeichen(zeichen: "neu", lesart: .pruefen, pruefzahl: nil,
                                    hinweise: [satz]).vorbehalte.count, 1)
    }

    func testOhneDenSatzKeinVorbehalt() {
        for h in [[], ["Ein anderer Hinweis."], ["Die Skizze ist nicht angekommen."]] {
            let z = Pruefzeichen(urteil: .bestanden, lesart: .pruefen, pruefzahl: 0.93,
                                 hinweise: h)
            XCTAssertTrue(z.vorbehalte.isEmpty, "\(h)")
            XCTAssertEqual(z.zeilen, ["BESTANDEN · 0.93"])
        }
    }

    /// Die Abschrift des festen Anfangs, **bewacht gegen den Server.** Der Satz steht in
    /// `src/aiimaging/kette.py`; fängt er dort anders an, sähe die App ihn nie.
    func testDerAnfangIstDerDesServers() throws {
        let wurzel = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let kette = wurzel.appendingPathComponent("src/aiimaging/kette.py")
        let text = try String(contentsOf: kette, encoding: .utf8)
        let marke = "HINWEIS_SKIZZE_NICHT_ANGEKOMMEN = ("
        guard let stelle = text.range(of: marke) else {
            return XCTFail("kette.py hat keinen HINWEIS_SKIZZE_NICHT_ANGEKOMMEN mehr")
        }
        let danach = text[stelle.upperBound...].drop(while: { $0.isWhitespace })
        XCTAssertTrue(danach.hasPrefix("\"" + Pruefzeichen.anfangSkizzeNichtAngekommen),
                      String(danach.prefix(60)))
    }

    // -------------------------------------------------------------- die Farben selbst

    func testKeineFarbeHeisstZweiDinge() {
        let raender = Zeichenart.allCases.map { $0.rand }
        XCTAssertEqual(Set(raender).count, raender.count, "\(raender.map { $0.hex })")
        let schriften = Zeichenart.allCases.map { $0.schrift }
        XCTAssertEqual(Set(schriften).count, schriften.count)
        let woerter = Zeichenart.allCases.map { $0.wort }
        XCTAssertEqual(Set(woerter).count, woerter.count)
        XCTAssertFalse(Set(raender).contains(Pruefzeichen.vorbehaltSchrift),
                       "ein Vorbehalt ist kein weiteres Urteil")
    }

    /// Nachgerechnet, nicht behauptet: Jedes Wort ist auf dem Streifen lesbar (WCAG 4.5),
    /// ob der Streifen über einem weissen oder einem schwarzen Bild liegt.
    func testJedesWortIstAufDemStreifenLesbar() {
        let weiss = Farbton(hex: "ffffff"), schwarz = Farbton(hex: "000000")
        for grund in [weiss, schwarz] {
            let streifen = Pruefzeichen.streifen.ueber(grund, deckung: Pruefzeichen.streifenDeckung)
            for art in Zeichenart.allCases {
                let k = Farbton.kontrast(art.schrift, streifen)
                XCTAssertGreaterThanOrEqual(k, 4.5, "\(art) auf \(streifen.hex): \(k)")
            }
            XCTAssertGreaterThanOrEqual(
                Farbton.kontrast(Pruefzeichen.vorbehaltSchrift, streifen), 4.5)
        }
    }

    func testJedeFarbeIstLesbarGeschrieben() {
        // `Farbton(hex:)` fällt bei einem Schreibfehler still auf Schwarz — hier fiele es auf.
        for art in Zeichenart.allCases {
            XCTAssertNotEqual(art.rand, Farbton(hex: "000000"), "\(art)")
            XCTAssertEqual(Farbton(hex: art.rand.hex), art.rand)
        }
    }
}
