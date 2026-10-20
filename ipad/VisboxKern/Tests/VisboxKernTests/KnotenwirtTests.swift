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
}
