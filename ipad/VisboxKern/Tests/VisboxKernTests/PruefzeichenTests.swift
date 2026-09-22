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

    // ------------------------------------------- was kein Urteil trägt (Durchsicht B)

    func testNichtGemessenUndUnbekanntSindGestrichelt() {
        // Die Durchsicht B (22.09.2026) fand `.unbekannt` gestrichelt, aber unbewacht.
        XCTAssertTrue(Zeichenart.nichtGemessen.gestrichelt)
        XCTAssertTrue(Zeichenart.unbekannt.gestrichelt,
                      "ein Zeichen, das die App nicht lesen kann, ist für sie kein Urteil")
        for art in [Zeichenart.bestanden, .durchgefallen] {
            XCTAssertFalse(art.gestrichelt, "\(art)")
        }
        // Und am Bild aus der Mappe, nicht nur an der Art:
        for roh in [#"{"zeichen": "neu"}"#, #"{"zeichen": null}"#, #"{}"#] {
            XCTAssertTrue(bild(roh).pruefzeichen(.pruefen).art.gestrichelt, roh)
        }
    }

    // --------------------------------------------------- die Mappe, wie sie Bild für Bild kommt

    /// Ein Bildeintrag aus `GET /api/projekt`, **aus Bytes gelesen** — derselbe Weg wie in
    /// der App (`Mappenlage.lies`).
    private func bild(_ json: String) -> Mappenbild {
        let text = #"{"bilder": ["# + json + "]}"
        guard let lage = try? Mappenlage.lies(status: 200, daten: Data(text.utf8)),
              let erstes = lage.bilder?.first else {
            XCTFail("nicht lesbar: \(json)")
            return Mappenbild([:])
        }
        return erstes
    }

    func testEinFehlendesZeichenHeisstNichtGeliefertUndNieLeer() {
        for roh in [#"{"bild": "a.png", "score": 0.93}"#,
                    #"{"bild": "a.png", "zeichen": null, "score": 0.93}"#] {
            let b = bild(roh)
            XCTAssertNil(b.zeichen, roh)
            let z = b.pruefzeichen(.pruefen)
            XCTAssertEqual(z.art, .unbekannt, roh)
            XCTAssertEqual(z.zeile, "ZEICHEN NICHT GELIEFERT", roh)
            XCTAssertEqual(z.zahl, .keine, "ohne Zeichen keine Zahl: \(roh)")
            XCTAssertNil(z.schwelle, roh)
        }
        // GELIEFERT, ABER UNBEKANNT ist etwas anderes als nicht geliefert.
        XCTAssertEqual(bild(#"{"zeichen": ""}"#).zeichen, "")
        XCTAssertEqual(bild(#"{"zeichen": ""}"#).pruefzeichen(.pruefen).zeile, "ZEICHEN UNBEKANNT")
        XCTAssertEqual(bild(#"{"zeichen": true}"#).zeichen, "true")
        XCTAssertEqual(bild(#"{"zeichen": true}"#).pruefzeichen(.pruefen).zeile, "ZEICHEN UNBEKANNT")
    }

    func testDieZahlUndDieSchwelleKommenAusDerMappe() {
        let b = bild(#"{"bild": "a.png", "zeichen": "bestanden", "score": 0.934, "schwelle": 0.8}"#)
        XCTAssertEqual(b.pruefzeichen(.pruefen).zeile, "BESTANDEN · 0.93")
        XCTAssertEqual(b.pruefzeichen(.pruefen).schwelle, "0.80")
        let d = bild(#"{"zeichen": "durchgefallen", "score": 0, "schwelle": 0.8}"#)
        XCTAssertEqual(d.pruefzeichen(.pruefen).zeile, "DURCHGEFALLEN · 0.00",
                       "eine gemessene Null ist eine Zahl")
        // OHNE ZAHL KEINE SCHWELLE — auch wenn der Server eine schickt.
        let ohne = bild(#"{"zeichen": "bestanden", "score": null, "schwelle": 0.8}"#)
        XCTAssertEqual(ohne.pruefzeichen(.pruefen).zeile, "BESTANDEN · ohne Zahl")
        XCTAssertNil(ohne.pruefzeichen(.pruefen).schwelle)
        // Ein Wahrheitswert ist keine Zahl.
        XCTAssertNil(bild(#"{"zeichen": "bestanden", "score": true}"#).score)
    }

    /// **Die dritte Antwort:** Ohne Urteil zeigt das Prüfzeichen keine Zahl — auch wenn der
    /// Server eine liefert. Durch den ganzen Weg: Bytes → Mappe → Zeichen.
    func testOhneUrteilKeineZahlAuchWennDerServerEineSchickt() {
        let b = bild(#"{"zeichen": "nicht-gemessen", "score": 0.93, "schwelle": 0.8}"#)
        XCTAssertEqual(b.score, 0.93, "gelesen wird sie — gezeigt nicht")
        for l in Bildlesart.allCases {
            let z = b.pruefzeichen(l)
            XCTAssertEqual(z.zahl, .keine, "\(l)")
            XCTAssertNil(z.schwelle, "\(l)")
            XCTAssertFalse(z.zeilen.joined().contains(where: { $0.isNumber }), "\(z.zeilen)")
            XCTAssertFalse(z.vorlesetext.contains("0.93"), z.vorlesetext)
        }
    }

    func testEinEntwurfWirdAlsEntwurfGelesen() {
        let e = bild(#"{"zeichen": "nicht-gemessen", "entwurf": true, "score": 0.9, "satz": "Entwurf — nicht geprüft"}"#)
        XCTAssertEqual(e.vorgabeLesart, .entwerfen)
        XCTAssertEqual(e.pruefzeichen(e.vorgabeLesart).art, .entwurf)
        XCTAssertEqual(e.pruefzeichen(e.vorgabeLesart).zeile, "ENTWURF — NICHT GEPRÜFT")
        // Umgelegt auf Prüfen: nicht gemessen — und kein Blau, das der Server nie setzte.
        XCTAssertEqual(e.pruefzeichen(.pruefen).art, .nichtGemessen)
        for roh in [#"{"zeichen": "bestanden", "entwurf": false}"#,
                    #"{"zeichen": "nicht-gemessen"}"#,
                    #"{"zeichen": "nicht-gemessen", "entwurf": null}"#,
                    #"{"zeichen": "nicht-gemessen", "entwurf": 1}"#] {
            XCTAssertEqual(bild(roh).vorgabeLesart, .pruefen, roh)
        }
    }

    func testSkizzeNichtAngekommenKommtAusDemFeldDesServers() {
        let satz = "SKIZZE NICHT ANGEKOMMEN: z-image-turbo nimmt gemessen kein Ausgangsbild an (x). "
            + "Das Bild ist aus Tiefenkarte und Text gerechnet."
        let feld = #""skizze_nicht_angekommen": true, "skizze_hinweis": "\#(satz)""#
        for rest in [#""hinweise": ["\#(satz)"]"#, #""hinweise": null"#, #""hinweise": []"#] {
            let b = bild(#"{"zeichen": "durchgefallen", "score": 0.41, "#
                         + feld + ", " + rest + "}")
            let z = b.pruefzeichen(.pruefen)
            XCTAssertEqual(z.vorbehalte.count, 1, rest)
            XCTAssertEqual(z.vorbehalte.first?.satz, satz, rest)
            XCTAssertEqual(z.zeilen.count, 2, "\(z.zeilen)")
            XCTAssertEqual(z.zeile, "DURCHGEFALLEN · 0.41", "die Zahl steht trotzdem da")
        }
        // Gemeldet, aber ohne Satz: der Vorbehalt bleibt.
        let ohneSatz = bild(#"{"zeichen": "bestanden", "score": 0.9, "skizze_nicht_angekommen": true}"#)
        XCTAssertEqual(ohneSatz.pruefzeichen(.pruefen).vorbehalte.count, 1)
        // Angekommen, oder kein Skizzenbild: keiner.
        for roh in [#"{"zeichen": "bestanden", "skizze_nicht_angekommen": false, "hinweise": []}"#,
                    #"{"zeichen": "bestanden", "skizze_nicht_angekommen": null, "hinweise": null}"#] {
            XCTAssertTrue(bild(roh).pruefzeichen(.pruefen).vorbehalte.isEmpty, roh)
        }
    }

    /// Der Kopf des Vorbehalts ist das, was in der zugeklappten Kachel steht — er muss der
    /// feste Anfang sein und im kurzen Wort vorne stehen, sonst sagt die zugeklappte
    /// Kachel etwas anderes als die aufgeklappte.
    func testDerKopfDesVorbehaltsIstDerFesteAnfang() {
        let z = Pruefzeichen(urteil: .bestanden, lesart: .pruefen, pruefzahl: 0.9,
                             hinweise: ["SKIZZE NICHT ANGEKOMMEN: x"])
        guard let v = z.vorbehalte.first else { return XCTFail("kein Vorbehalt") }
        XCTAssertEqual(v.kopf, Pruefzeichen.anfangSkizzeNichtAngekommen)
        XCTAssertTrue(v.kurz.hasPrefix(v.kopf), v.kurz)
    }

    func testDieMappeTraegtStandnummerSkizzenUndReihe() throws {
        let antwort = #"""
        {"name": "Testkörper", "stand_nr": 12,
         "bilder": [
           {"bild": "a.png", "zeichen": "bestanden", "titel": "  ",
            "variantengruppe": {"id": "g1", "art": "startwerte", "nummer": 2, "von": 3, "seed": 43}},
           {"bild": "b.png", "zeichen": "nicht-gemessen", "titel": "Attika",
            "variantengruppe": {"id": "g2", "art": "ebenen", "nummer": 1, "von": 2, "skizze": "s1.png"}},
           "kein Objekt"],
         "skizzen": [
           {"skizze": "s1.png", "stand": "offen", "titel": null, "bemerkung": "Ebene 1"},
           {"skizze": "s2.png", "stand": "gerechnet", "ergebnis": "b.png", "titel": "Zwei"},
           {"skizze": "s3.png", "stand": "schwebend"}]}
        """#
        let lage = try Mappenlage.lies(status: 200, daten: Data(antwort.utf8))
        XCTAssertEqual(lage.standNr, 12)
        XCTAssertEqual(lage.name, "Testkörper")
        XCTAssertEqual(lage.bilder?.count, 2, "was kein Objekt ist, ist kein Bild")
        XCTAssertNil(lage.bilder?[0].titel, "ein leerer Name ist kein Name")
        XCTAssertEqual(lage.bilder?[1].titel, "Attika")
        let g = lage.bilder?[0].variantengruppe
        XCTAssertEqual(g?.id, "g1")
        XCTAssertEqual(g?.art, "startwerte")
        XCTAssertEqual(g?.nummer, 2)
        XCTAssertEqual(g?.von, 3)
        XCTAssertEqual(g?.seed, 43)
        XCTAssertEqual(lage.bilder?[1].variantengruppe?.skizze, "s1.png")
        XCTAssertEqual(lage.skizzen?.map { $0.stand }, [.offen, .gerechnet, nil],
                       "ein unbekannter Stand wird nicht zu «offen»")
        XCTAssertEqual(lage.skizzen?[1].ergebnis, "b.png")
        XCTAssertEqual(lage.skizzen?[1].titel, "Zwei")

        // NICHT GELIEFERT IST NICHT LEER.
        let ohne = try Mappenlage.lies(status: 200, daten: Data(#"{"name": "x"}"#.utf8))
        XCTAssertNil(ohne.bilder)
        XCTAssertNil(ohne.skizzen)
        XCTAssertNil(ohne.standNr)
        XCTAssertThrowsError(try Mappenlage.lies(
            status: 404, daten: Data(#"{"fehler": "Kein Projekt."}"#.utf8))) { f in
            XCTAssertEqual((f as? Serverfehler)?.satz, "Kein Projekt.")
        }
    }

    // ------------------------------------------------------- Rechnen lassen, Namen geben

    private func rumpf(_ a: Anfrage) -> [String: JSONWert] {
        guard let d = a.rumpf, let o = (try? JSONWert.lies(d))?.alsObjekt else {
            XCTFail("kein Rumpf")
            return [:]
        }
        return o
    }

    func testDieBestellungTraegtDieLesart() throws {
        for l in Bildlesart.allCases {
            let a = try Rechenbestellung.skizze("s1.png", anweisung: "höher")
                .anfrage(lesart: l, ordner: "/m", anmeldung: nil)
            XCTAssertEqual(a.weg, Wege.rechneSkizze)
            XCTAssertEqual(rumpf(a)["skizze"], .text("s1.png"))
            XCTAssertEqual(rumpf(a)["anweisung"], .text("höher"))
            XCTAssertEqual(rumpf(a)["entwurf"], .wahrheit(l == .entwerfen))
            XCTAssertEqual(rumpf(a)["ordner"], .text("/m"))
        }
    }

    func testDieEbenenReiheGehtAlsListe() throws {
        let a = try Rechenbestellung.ebenenreihe(["s1.png", "s2.png"], anweisung: nil)
            .anfrage(lesart: .entwerfen, ordner: nil, anmeldung: nil)
        XCTAssertEqual(a.weg, Wege.rechneSkizze)
        XCTAssertEqual(rumpf(a)["skizze"], .liste([.text("s1.png"), .text("s2.png")]))
        XCTAssertNil(rumpf(a)["anweisung"], "ohne Anweisung gilt drüben die Bemerkung")
        XCTAssertNil(rumpf(a)["varianten"], "Startwert-Reihen gibt es nur für das Modell")
    }

    func testDreiStartwerteGehenAnRechneMitVarianten() throws {
        for l in Bildlesart.allCases {
            let a = try Rechenbestellung.startwerte
                .anfrage(lesart: l, ordner: nil, anmeldung: Anmeldung(benutzer: "u", kennwort: "k"))
            XCTAssertEqual(a.weg, Wege.rechne)
            XCTAssertEqual(rumpf(a)["varianten"], .ganz(3),
                           "drei Varianten, so viele wie die Mappe nebeneinander zeigt")
            XCTAssertEqual(rumpf(a)["entwurf"], .wahrheit(l == .entwerfen))
            XCTAssertNil(rumpf(a)["ordner"])
            XCTAssertNotNil(a.kopfzeilen["Authorization"])
        }
        XCTAssertEqual(Rechenbestellung.reihenlaenge, Ebenenstapel.hoechstensVarianten)
    }

    private func quittung(_ status: Int, _ json: String,
                          _ art: (Int, Data) -> Handlungsquittung) -> Handlungsquittung {
        art(status, Data(json.utf8))
    }

    func testEineQuittungHatVierAusgaengeUndEinerIstUngewiss() {
        let rechnen = Handlungsquittung.rechnen(status:daten:)
        XCTAssertEqual(quittung(200, #"{"gestartet": true, "entwurf": false}"#, rechnen).ausgang,
                       .angenommen)
        XCTAssertTrue(quittung(200, #"{"gestartet": true, "entwurf": true}"#, rechnen).satz
                        .contains("ohne Geometrieprüfung"))
        // ERFOLG NUR, WENN ER DASTEHT.
        XCTAssertEqual(quittung(200, #"{}"#, rechnen).ausgang, .ungewiss)
        XCTAssertEqual(quittung(200, #"{"gestartet": 1}"#, rechnen).ausgang, .ungewiss)
        XCTAssertEqual(quittung(200, "kaputt", rechnen).ausgang, .ungewiss)
        let schon = quittung(400, #"{"fehler": "Es läuft schon einer."}"#, rechnen)
        XCTAssertEqual(schon.ausgang, .abgelehnt)
        XCTAssertEqual(schon.satz, "Es läuft schon einer.", "der Satz des Servers, unverändert")

        let ab = quittung(200, #"{"abbruch_verlangt": true, "satz": "Abbruch verlangt. X."}"#,
                          Handlungsquittung.abbrechen(status:daten:))
        XCTAssertEqual(ab, Handlungsquittung(ausgang: .angenommen, satz: "Abbruch verlangt. X."))
        XCTAssertEqual(quittung(400, #"{"fehler": "Es läuft gerade kein Lauf."}"#,
                                Handlungsquittung.abbrechen(status:daten:)).ausgang, .abgelehnt)

        let name = Handlungsquittung.benennen(status:daten:)
        XCTAssertEqual(quittung(200, #"{"benannt": true, "stand_nr": 13}"#, name).ausgang, .angenommen)
        XCTAssertEqual(quittung(400, #"{"fehler": "Kollision. Die Seite neu laden zeigt den neuen Stand."}"#,
                                name).ausgang, .abgelehnt)

        let still = Handlungsquittung.ohneAntwort(grund: "Die Verbindung ist abgerissen.")
        XCTAssertEqual(still.ausgang, .ungewiss, "keine Antwort ist kein Nein")
        XCTAssertTrue(still.satz.hasPrefix("Die Verbindung ist abgerissen."))
    }

    // ------------------------------------------------- die Farbtöne gegen das Blatt

    /// **Die Abschrift des Blatts «Die Zeichen» (und «Main»), Stand 22.09.2026.** Ändert
    /// jemand einen Ton im Kern, fällt diese Probe; ändert sich das Blatt, wird diese Liste
    /// nachgezogen — in derselben Sitzung.
    func testJederFarbtonStehtSoAufDemBlatt() {
        let blatt: [(String, Farbton, String)] = [
            ("Grund", Blattfarbe.grund, "#14161a"),
            ("Feld", Blattfarbe.feld, "#1c1f26"),
            ("Leiste", Blattfarbe.leiste, "#16191e"),
            ("Bühne", Blattfarbe.buehne, "#101317"),
            ("Linie", Blattfarbe.linie, "#2b3038"),
            ("Schrift", Blattfarbe.schrift, "#e6e8ec"),
            ("Leise", Blattfarbe.leise, "#9aa2ae"),
            ("gewählt Rand", Blattfarbe.gewaehltRand, "#4ea373"),
            ("gewählt Grund", Blattfarbe.gewaehltGrund, "#223028"),
            ("gewählt Schrift", Blattfarbe.gewaehltSchrift, "#a7dec0"),
            ("Kachel", Blattfarbe.kachel, "#14181b"),
            ("Lücke", Blattfarbe.luecke, "#0e1013"),
            ("bestanden", Zeichenart.bestanden.rand, "#4ea373"),
            ("bestanden, Schrift", Zeichenart.bestanden.schrift, "#8fd4ac"),
            ("durchgefallen", Zeichenart.durchgefallen.rand, "#e2776f"),
            ("nicht gemessen", Zeichenart.nichtGemessen.rand, "#c8a53f"),
            ("Entwurf", Zeichenart.entwurf.rand, "#6fb3d2"),
            // rgba(8,10,13,0.94) auf dem Blatt
            ("Streifen", Pruefzeichen.streifen, "#080a0d"),
            ("Vorbehalt", Pruefzeichen.vorbehaltSchrift, "#e6e8ec"),
        ]
        for (name, ton, hex) in blatt {
            XCTAssertEqual(ton.hex, hex, name)
        }
        XCTAssertEqual(Pruefzeichen.streifen, Farbton(rot: 8, gruen: 10, blau: 13))
        XCTAssertEqual(Pruefzeichen.streifenDeckung, 0.94)
    }

    /// Die Töne, die auch die Webseite führt, **gelesen aus `oberflaeche/seite.html`** —
    /// eine Bedeutung, eine Farbe, auf beiden Flächen (Blatt «Die Zeichen»).
    func testDieGemeinsamenToeneSindDieDerWebseite() throws {
        let seite = try String(contentsOf: wurzel().appendingPathComponent("oberflaeche/seite.html"),
                               encoding: .utf8)
        guard let anfang = seite.range(of: ":root {"),
              let ende = seite[anfang.upperBound...].range(of: "}") else {
            return XCTFail("seite.html hat keinen :root-Block mehr")
        }
        let block = String(seite[anfang.upperBound..<ende.lowerBound])
        func ton(_ name: String) -> String? {
            guard let r = block.range(of: "--\(name):") else { return nil }
            return String(block[r.upperBound...].drop(while: { $0 == " " }).prefix(7))
        }
        let paare: [(String, Farbton)] = [
            ("grund", Blattfarbe.grund), ("feld", Blattfarbe.feld), ("rand", Blattfarbe.linie),
            ("schrift", Blattfarbe.schrift), ("leise", Blattfarbe.leise),
            ("bestanden", Zeichenart.bestanden.rand),
            ("durchgefallen", Zeichenart.durchgefallen.rand),
            ("ungemessen", Zeichenart.nichtGemessen.rand), ("entwurf", Zeichenart.entwurf.rand),
        ]
        for (name, farbe) in paare {
            XCTAssertEqual(ton(name), farbe.hex, "--\(name)")
        }
    }

    /// Keine Urteilsfarbe ist eine Grundfarbe — **ein Rand am Bild sieht nie aus wie eine
    /// Beschriftung.** Befund der Durchsicht B: `.unbekannt` trug das Leise der Schrift.
    func testKeineUrteilsfarbeIstEineGrundfarbe() {
        for art in Zeichenart.allCases {
            XCTAssertFalse(Blattfarbe.grundfarben.contains(art.rand), "\(art): \(art.rand.hex)")
        }
        XCTAssertNotEqual(Zeichenart.unbekannt.rand, Blattfarbe.leise)
    }

    /// **Eine Abwesenheit:** Ausserhalb des Kerns schreibt keine Datei der App einen
    /// Farbton als Hex-Ziffern. Sonst gäbe es einen Ton, den keine Probe sieht.
    func testDieAppSchreibtKeineFarbtoeneAusserhalbDesKerns() throws {
        // DAS APP-PAKET UEBER DEN VERWEIS DES KERNS GEFUNDEN, nicht über seinen Namen: Der
        // Name steht nur in `Marke.swift` (`test_name_kennung_und_dienst_stehen_nur_in_der_marke`).
        // `Sources/` dieses Prüfpakets enthält genau einen Eintrag — den Verweis.
        let quellen = URL(fileURLWithPath: #filePath).deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
            .appendingPathComponent("Sources")
        let eintraege = try FileManager.default.contentsOfDirectory(
            at: quellen, includingPropertiesForKeys: nil)
        guard eintraege.count == 1, let verweis = eintraege.first else {
            return XCTFail("Sources/ hat nicht genau einen Eintrag: \(eintraege)")
        }
        let kern = verweis.resolvingSymlinksInPath()
        let app = kern.deletingLastPathComponent()
        guard let gang = FileManager.default.enumerator(at: app, includingPropertiesForKeys: nil) else {
            return XCTFail("App-Paket nicht gefunden: \(app.path)")
        }
        var gelesen = 0
        for case let datei as URL in gang where datei.pathExtension == "swift" {
            if datei.resolvingSymlinksInPath().path.hasPrefix(kern.path + "/") { continue }
            let text = try String(contentsOf: datei, encoding: .utf8)
            gelesen += 1
            XCTAssertFalse(text.contains("Farbton(hex:"), datei.lastPathComponent)
        }
        XCTAssertGreaterThan(gelesen, 5, "die Probe muss Dateien gesehen haben")
    }

    private func wurzel() -> URL {
        URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    }
}
