import Foundation
import XCTest
import VisboxKern

/// Die Rechner-Wahl («Visbox eigenständig», Schritt 6; Blatt 28, Feld 2) — sichtbar und
/// gespeichert, aber heute ohne Wirkung auf den Weg.
final class RechnerwahlTests: XCTestCase {

    private let ohneBlender = Rechnerbefund(blenderGefunden: false, arbeitsspeicher: 16 << 30)
    private let mitBlenderUndViel = Rechnerbefund(blenderGefunden: true, arbeitsspeicher: 64 << 30)

    func testDieVorgabeIstUeberallDerHeimPC() {
        let w = Rechnerwahl.vorgabe
        for arbeit in Rechenarbeit.allCases {
            XCTAssertEqual(w.ort(fuer: arbeit), .heimPC, arbeit.rawValue)
            XCTAssertEqual(w.wirksam(fuer: arbeit, befund: mitBlenderUndViel), .heimPC)
        }
        XCTAssertEqual(Rechenarbeit.allCases.map(\.titel), ["Blender-Render", "Bildmodell", "Bedien-KI"])
        XCTAssertEqual(Rechnerort.allCases.map(\.titel), ["Heim-PC", "Dieses Gerät"])
    }

    func testDiesesGeraetIstNichtVerfuegbarMitDemGrundAusDemBlatt() {
        XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .blenderRender, befund: ohneBlender).zeile,
                       "nicht verfügbar — kein Blender gefunden")
        XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bildmodell, befund: ohneBlender).zeile,
                       "nicht verfügbar — zu wenig Grafikspeicher")
        XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bedienKI, befund: ohneBlender).zeile,
                       "nicht verfügbar")
        for arbeit in Rechenarbeit.allCases {
            XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.heimPC, fuer: arbeit, befund: ohneBlender), .verfuegbar)
            XCTAssertNil(Rechnerwahl.verfuegbarkeit(.heimPC, fuer: arbeit, befund: ohneBlender).zeile)
        }
    }

    func testAuchMitBlenderUndVielSpeicherHeuteNicht() {
        // GEFUNDEN HEISST NUR: ein anderer Grund. Der lokale Abholer ist nicht gebaut.
        let blender = Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .blenderRender, befund: mitBlenderUndViel)
        XCTAssertFalse(blender.waehlbar)
        XCTAssertEqual(blender.zeile, "nicht verfügbar — lokales Rechnen kommt in einer späteren Fassung")
        let bild = Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bildmodell, befund: mitBlenderUndViel)
        XCTAssertFalse(bild.waehlbar)
        XCTAssertEqual(bild.zeile, "nicht verfügbar — kommt in einer späteren Fassung")
        XCTAssertFalse(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bedienKI,
                                                  befund: mitBlenderUndViel).waehlbar)
    }

    func testDieSpeichergrenzeIstGesetztUndScharf() {
        let knapp = Rechnerbefund(blenderGefunden: false, arbeitsspeicher: Rechnerwahl.bildmodellSpeicher - 1)
        let genug = Rechnerbefund(blenderGefunden: false, arbeitsspeicher: Rechnerwahl.bildmodellSpeicher)
        XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bildmodell, befund: knapp),
                       .nichtVerfuegbar(grund: Rechnerwahl.zuWenigGrafikspeicher))
        XCTAssertEqual(Rechnerwahl.verfuegbarkeit(.diesesGeraet, fuer: .bildmodell, befund: genug),
                       .nichtVerfuegbar(grund: Rechnerwahl.bildmodellSpaeter))
        XCTAssertEqual(Rechnerwahl.bildmodellSpeicher, 32 << 30)
    }

    func testEinGesperrterOrtLaesstSichNichtWaehlen() {
        var w = Rechnerwahl.vorgabe
        XCTAssertFalse(w.waehle(.diesesGeraet, fuer: .blenderRender, befund: mitBlenderUndViel))
        XCTAssertEqual(w, .vorgabe, "eine gesperrte Wahl ändert nichts")
        XCTAssertTrue(w.waehle(.heimPC, fuer: .bedienKI, befund: ohneBlender))
        XCTAssertEqual(w, .vorgabe, "der Heim-PC ist die Vorgabe und wird nicht eigens gespeichert")
    }

    func testSpeichernUndLesen() {
        let leer = Rechnerwahl.vorgabe.alsDaten()
        XCTAssertEqual(String(data: leer, encoding: .utf8), "{}")
        XCTAssertEqual(Rechnerwahl.aus(daten: leer), .vorgabe)
        XCTAssertEqual(Rechnerwahl.aus(daten: nil), .vorgabe, "noch nie gespeichert")
        XCTAssertEqual(Rechnerwahl.aus(daten: Data("kaputt".utf8)), .vorgabe, "Unlesbares hält nichts auf")
        XCTAssertEqual(Rechnerwahl.aus(daten: Data("[1,2]".utf8)), .vorgabe)

        // EINE SPAETERE FASSUNG hat «dieses Gerät» gespeichert: Gelesen wird es, gerechnet wird
        // trotzdem am Heim-PC, solange es hier nicht verfügbar ist.
        let spaeter = Rechnerwahl.aus(daten: Data(#"{"blenderRender":"diesesGeraet","bedienKI":"heimPC","fremd":"x","bildmodell":"mond"}"#.utf8))
        XCTAssertEqual(spaeter.ort(fuer: .blenderRender), .diesesGeraet)
        XCTAssertEqual(spaeter.ort(fuer: .bildmodell), .heimPC, "ein unbekannter Ort wird übergangen")
        XCTAssertEqual(spaeter.wirksam(fuer: .blenderRender, befund: mitBlenderUndViel), .heimPC)
        XCTAssertEqual(String(data: spaeter.alsDaten(), encoding: .utf8), #"{"blenderRender":"diesesGeraet"}"#)
        XCTAssertEqual(Rechnerwahl.aus(daten: spaeter.alsDaten()), spaeter)
        XCTAssertEqual(Rechnerwahl.schluessel, "rechnerwahl.v1")
    }

    func testDerZusatzAmHeimPCFolgtDerLeitung() {
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .blenderRender, lage: .verbunden, eingerichtet: true), "verbunden")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .bedienKI, lage: .verbunden, eingerichtet: true), "Sprachmodell")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .bildmodell, lage: .ohneRechner, eingerichtet: true),
                       "nicht erreichbar")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .bedienKI, lage: .ohneRechner, eingerichtet: true),
                       "Sprachmodell · nicht erreichbar")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .blenderRender, lage: .abgewiesen, eingerichtet: true), "weist ab")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .blenderRender, lage: .startet, eingerichtet: true), "wird gefragt")
        XCTAssertEqual(Rechnerwahl.zusatzHeim(fuer: .blenderRender, lage: .verbunden, eingerichtet: false),
                       "nicht eingerichtet")
    }

    func testDieSaetzeStehenSoAufDemBlatt() {
        XCTAssertEqual(Rechnerwahl.titel, "Wer rechnet?")
        XCTAssertEqual(Rechnerwahl.untertitel, "Je Arbeit wählbar. Vorgabe: Heim-PC.")
        // Entscheide 105/106 (20.10.2026): wahr formuliert — seit Stufe 3 ist Claude angeschlossen.
        XCTAssertEqual(Rechnerwahl.mcpSatz,
                       "Claude über MCP: eingerichtet — Claude bedient \(Marke.name) auf diesem "
                       + "Mac über die Knotenansicht, unabhängig von dieser Wahl (Einrichten › "
                       + "Claude über MCP). Die Wahl gilt für die Assistent-Leiste in der App.")
        XCTAssertFalse(Rechnerwahl.mcpSatz.contains("steuert"))
        XCTAssertEqual(Rechnerwahl.blenderOrt, "/Applications/Blender.app")
        for satz in [Rechnerwahl.mcpSatz, Rechnerwahl.heuteSatz, Rechnerwahl.blenderSpaeter] {
            XCTAssertFalse(satz.contains("ß"), satz)
        }
    }
}
