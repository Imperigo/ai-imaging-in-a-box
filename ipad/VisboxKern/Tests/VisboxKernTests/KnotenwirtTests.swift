import XCTest
import VisboxKern

/// Die zweite Brücke «visboxWirt» (Plan UI-Gleichheit S1/S2, Entscheide 115/116, 20.10.2026).
final class KnotenwirtTests: XCTestCase {
    private func lies(_ text: String) throws -> JSONWert {
        try JSONWert.lies(Data(text.utf8))
    }

    func testDerNameIstDerDerSeite() {
        XCTAssertEqual(Knotenwirt.name, Mcp.servername + "Wirt")
        XCTAssertEqual(Kibruecke.name, Mcp.servername + "Ki")
        XCTAssertEqual(Knotenwirt.Ziel.visboxSeite.wort, Mcp.servername + "-seite")
    }

    func testDieWuenscheDerSeite() throws {
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"bereit"}"#)), .bereit)
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"modus","modus":"coop"}"#)), .modus(.coop))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"rechner"}"#)), .rechner)
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"claude","an":false}"#)), .claude(an: false))
        let seite = Knotenwirt.Ziel.visboxSeite.wort
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies("{\"art\":\"oeffne\",\"ziel\":\"\(seite)\"}")),
                       .oeffne(.visboxSeite))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"oeffne","ziel":"startansicht"}"#)),
                       .oeffne(.startansicht))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"einstellung"}"#)),
                       .einstellung(abschnitt: nil))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"einstellung","abschnitt":"claude"}"#)),
                       .einstellung(abschnitt: "claude"))
    }

    /// Unvollständig oder unbekannt: nichts — die App raet nicht.
    func testUnbekanntesFaelltWeg() throws {
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"modus","modus":"frei"}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"claude","an":1}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"oeffne","ziel":"irgendwo"}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"freigeben"}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"[1,2]"#)))
    }

    func testDerHeimPcChipSprichtWieDerSyncChip() {
        XCTAssertEqual(Knotenwirt.rechnerchip(eingerichtet: false, lage: .verbunden),
                       Knotenwirt.Rechnerchip(text: "Heim-PC · nicht gekoppelt", ton: "aus"))
        XCTAssertEqual(Knotenwirt.rechnerchip(eingerichtet: true, lage: .verbunden).ton, "gut")
        for lage in [Leitungslage.startet, .getrennt, .ohneRechner, .abgewiesen] {
            let chip = Knotenwirt.rechnerchip(eingerichtet: true, lage: lage)
            XCTAssertEqual(chip.ton, "warnung", "\(lage)")
            XCTAssertTrue(chip.text.hasPrefix("Heim-PC · "), chip.text)
        }
    }

    func testThemaVorgabeDunkelUndUmschaltbar() {
        XCTAssertEqual(Knotenwirt.Thema.vorgabe, .orbit)
        XCTAssertEqual(Knotenwirt.Thema(gemerkt: nil), .orbit)
        XCTAssertEqual(Knotenwirt.Thema(gemerkt: "paper"), .paper)
        XCTAssertEqual(Knotenwirt.Thema(gemerkt: "ink"), .orbit)
        XCTAssertEqual(Knotenwirt.Thema.orbit.anderes, .paper)
        XCTAssertEqual(Knotenwirt.Thema.paper.anderes, .orbit)
    }

    func testVersion() {
        XCTAssertEqual(Knotenwirt.version("0.4.0"), "v0.4.0")
        XCTAssertEqual(Knotenwirt.version("v0.4.0"), "v0.4.0")
        XCTAssertEqual(Knotenwirt.version(nil), "")
    }

    func testClaudeVerbundenNurNachKontakt() {
        let jetzt = Date(timeIntervalSince1970: 1_000_000)
        XCTAssertFalse(Knotenwirt.claudeVerbunden(lage: .bereit, letzterKontakt: nil, jetzt: jetzt))
        XCTAssertTrue(Knotenwirt.claudeVerbunden(lage: .bereit, letzterKontakt: jetzt.addingTimeInterval(-60),
                                                 jetzt: jetzt))
        XCTAssertFalse(Knotenwirt.claudeVerbunden(lage: .aus, letzterKontakt: jetzt, jetzt: jetzt))
    }

    /// Der Rumpf legt genau die Felder in die Seite, die sie liest — und **kein Kennwort**.
    func testDieLageTraegtKeinKennwort() throws {
        let lage = Knotenwirt.Lage(leitung: nil, sperre: "Rechnen gesperrt",
                                   rechner: Knotenwirt.rechnerchip(eingerichtet: true, lage: .verbunden),
                                   claudeVerbunden: true, version: "v0.4.0", modus: .voll, thema: .orbit)
        let rumpf = try XCTUnwrap(Knotenwirt.rumpf(lage))
        let kopf = "window.\(Knotenwirt.name) && window.\(Knotenwirt.name).lage("
        XCTAssertTrue(rumpf.hasPrefix(kopf + "{"), rumpf)
        let json = String(rumpf.dropFirst(kopf.count).dropLast(2))
        let wert = try lies(json)
        guard case .objekt(let felder) = wert else { return XCTFail("kein Objekt") }
        XCTAssertEqual(Set(felder.keys), ["leitung", "sperre", "rechner", "claude", "version", "modus", "thema"])
        XCTAssertEqual(wert["modus"]?.alsText, "voll")
        XCTAssertEqual(wert["claude"]?["verbunden"]?.alsWahrheit, true)
        XCTAssertEqual(wert["rechner"]?["text"]?.alsText, "Heim-PC · bereit")
        for verboten in ["kennwort", "passwort", "anmeldung", "benutzer", "token"] {
            XCTAssertFalse(rumpf.lowercased().contains(verboten), verboten)
        }
    }

    // ================================================================ S3/S4 (20.10.2026)

    func testDieNeuenWuensche() throws {
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"rechner","arbeit":"bildmodell","ort":"heimPC"}"#)),
                       .rechnerWaehlen(.bildmodell, .heimPC))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"rechner","arbeit":"bildmodell"}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"rechner","arbeit":"kaffee","ort":"heimPC"}"#)))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"assistent","tat":"frage","text":"Abend"}"#)),
                       .assistent(.frage("Abend")))
        for tat in ["anwenden", "ablehnen", "aendern"] {
            XCTAssertNotNil(Knotenwirt.wunsch(aus: try lies("{\"art\":\"assistent\",\"tat\":\"\(tat)\"}")), tat)
        }
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"assistent","tat":"frage"}"#)))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"assistent","tat":"rechnen"}"#)))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"oeffne","ziel":"einrichten"}"#)), .oeffne(.einrichten))
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"oeffne","ziel":"aktualisieren"}"#)), .oeffne(.aktualisieren))
    }

    /// Gemerkt wird nur, was auf der Liste steht — kein Weg, der App beliebige Werte unterzuschieben.
    func testMerkenNurVonDerListe() throws {
        XCTAssertEqual(Knotenwirt.wunsch(aus: try lies(#"{"art":"merke","schluessel":"kosmo.thema","wert":"paper"}"#)),
                       .merke(schluessel: "kosmo.thema", wert: "paper"))
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies(#"{"art":"merke","schluessel":"kosmo.bridge","wert":"x"}"#)))
        let lang = String(repeating: "x", count: Knotenwirt.merkWertHoechstens + 1)
        XCTAssertNil(Knotenwirt.wunsch(aus: try lies("{\"art\":\"merke\",\"schluessel\":\"kosmo.anzeige\",\"wert\":\"\(lang)\"}")))
        let skript = Knotenwirt.merkSkript(["kosmo.anzeige": #"{"schrift":"gross"}"#, "kosmo.bridge": "boese",
                                            "kosmo.akzent": "'); alert(1); ('"])
        XCTAssertTrue(skript.contains(#"localStorage.setItem("kosmo.anzeige", "{\"schrift\":\"gross\"}");"#), skript)
        XCTAssertFalse(skript.contains("kosmo.bridge"))
        XCTAssertTrue(skript.contains(#""'); alert(1); ('""#), skript)
    }

    func testDasGespraechSagtWannStattDesFeldsEinSatzSteht() throws {
        var g = Assistentengespraech()
        let bereit = Assistentenzeile(stand: .bereit, modell: "qwen3:14b", satz: "Assistent bereit.")
        XCTAssertNil(Assistentenlage(gespraech: g, zeile: bereit, gesperrt: nil).feldSatz)
        XCTAssertEqual(Assistentenlage(gespraech: g, zeile: bereit, gesperrt: "Ohne Heim-PC gesperrt.").feldSatz,
                       "Ohne Heim-PC gesperrt.")
        let laedt = Assistentenzeile(stand: .laedt, modell: "qwen3:14b", satz: "Ein Bild rechnet.")
        XCTAssertEqual(Assistentenlage(gespraech: g, zeile: laedt, gesperrt: nil).feldSatz, "Ein Bild rechnet.")
        XCTAssertEqual(Assistentenlage(gespraech: g, zeile: nil, gesperrt: nil).feldSatz, Assistentenlage.nachgesehen)

        _ = g.sende("Abendstimmung")
        let wartend = Assistentenlage(gespraech: g, zeile: bereit, gesperrt: nil,
                                      feld: .init(nummer: 3, text: "")).wert
        XCTAssertEqual(wartend["wartet"]?.alsWahrheit, true)
        XCTAssertEqual(wartend["beitraege"]?.alsListe?.first?["von"]?.alsText, "mensch")
        XCTAssertEqual(wartend["feld"]?["nummer"]?.alsGanz, 3)
        XCTAssertEqual(wartend["grenzen"]?["titel"]?.alsText, Assistentengrenzen.titel)
        XCTAssertEqual(wartend["karte"], .null)
        let vorschlag = Assistentenvorschlag(einstellungen: ["stimmung": .text("abend")], varianten: nil,
                                             saetze: ["Stimmung: Abend"], rechenzeit: nil)
        g.empfange(Assistentenantwort(antwort: "Gern.", vorschlag: vorschlag))
        let fertig = Assistentenlage(gespraech: g, zeile: bereit, gesperrt: nil).wert
        XCTAssertEqual(fertig["beitraege"]?.alsListe?.count, 2)
        XCTAssertEqual(fertig["karte"]?["zeilen"]?.alsListe?.first?.alsText, "Stimmung: Abend")
        XCTAssertEqual(fertig["modell"]?.alsText, "qwen3:14b")
        XCTAssertEqual(fertig["stand"]?.alsText, "bereit")
    }

    func testWerRechnetWieDieAnsichtDerApp() {
        let befund = Rechnerbefund(blenderGefunden: false, arbeitsspeicher: 16 * 1024 * 1024 * 1024)
        let lage = Rechnerwahllage(wahl: .vorgabe, befund: befund, lage: .verbunden, eingerichtet: true)
        let w = lage.wert
        XCTAssertEqual(w["titel"]?.alsText, Rechnerwahl.titel)
        let arbeiten = w["arbeiten"]?.alsListe ?? []
        XCTAssertEqual(arbeiten.compactMap { $0["arbeit"]?.alsText }, Rechenarbeit.allCases.map(\.rawValue))
        let blender = arbeiten[0]["felder"]?.alsListe ?? []
        XCTAssertEqual(blender[0]["gewaehlt"]?.alsWahrheit, true)
        XCTAssertEqual(blender[0]["zeile"]?.alsText, "· verbunden")
        XCTAssertEqual(blender[1]["waehlbar"]?.alsWahrheit, false)
        XCTAssertEqual(blender[1]["zeile"]?.alsText, "nicht verfügbar — kein Blender gefunden")
    }

    func testClaudeUndNeuigkeitenTragenDieSaetzeDesKerns() throws {
        let c = Claudemcplage(an: true, satz: "Hört.").wert
        XCTAssertEqual(c["befehl"]?.alsText, Claudeeinrichtung.befehl)
        XCTAssertEqual(c["an"]?.alsWahrheit, true)
        let n = Neuigkeitenlage(fassung: "v0.3.8", angebot: nil).wert
        XCTAssertEqual(n["fassung"]?.alsText, "v0.3.8")
        XCTAssertEqual(n["angebot"], .null)
    }

    /// Auch mit Gespraech, «Wer rechnet?» und «Claude über MCP» trägt die Lage **kein Kennwort**.
    func testDieVolleLageTraegtKeinKennwort() throws {
        var g = Assistentengespraech()
        _ = g.sende("Hallo")
        let lage = Knotenwirt.Lage(
            leitung: nil, sperre: nil, rechner: Knotenwirt.rechnerchip(eingerichtet: true, lage: .verbunden),
            claudeVerbunden: true, version: "v0.4.0", modus: .karte, thema: .orbit,
            assistent: Assistentenlage(gespraech: g, zeile: nil, gesperrt: nil),
            rechnerwahl: Rechnerwahllage(wahl: .vorgabe, befund: Rechnerbefund(blenderGefunden: true, arbeitsspeicher: 0),
                                         lage: .verbunden, eingerichtet: true),
            claudeMcp: Claudemcplage(an: false, satz: "aus"),
            neuigkeiten: Neuigkeitenlage(fassung: "v0.4.0", angebot: nil))
        let rumpf = try XCTUnwrap(Knotenwirt.rumpf(lage))
        for verboten in ["kennwort", "passwort", "anmeldung", "benutzer", "token", "authorization"] {
            XCTAssertFalse(rumpf.lowercased().contains(verboten), verboten)
        }
        XCTAssertEqual(Knotenwirt.assistentName, "Assistent")
    }
}
