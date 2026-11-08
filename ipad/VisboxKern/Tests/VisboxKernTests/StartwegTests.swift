import Foundation
import XCTest
import VisboxKern

/// A0255 Runde 2: der GANZE Startweg der Mac-App liest den Schlüsselbund nie auf dem Hauptfaden,
/// und ein Testbau berührt weder Ausweis noch Kopplung der installierten App (E144).
///
/// Die Mac-App lässt sich unter Linux nicht übersetzen; darum prüfen diese Proben ihre Quellen
/// (wie `StartwartenTests` den Ablauf und die Anleitung): wo eine Lesung oder Schreibung des
/// Schlüsselbunds stehen darf und wo nicht.
final class StartwegTests: XCTestCase {

    private var wurzel: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    }

    private var macQuellen: URL {
        wurzel.appendingPathComponent("ipad/\(Marke.name)Mac/Sources/\(Marke.name)Mac")
    }

    /// Alle Quelldateien der Mac-App, ohne Kommentare: Dateiname (relativ) -> Text.
    private func quellen() throws -> [String: String] {
        var alle: [String: String] = [:]
        let sucher = try XCTUnwrap(FileManager.default.enumerator(at: macQuellen, includingPropertiesForKeys: nil))
        for fall in sucher {
            guard let datei = fall as? URL, datei.pathExtension == "swift" else { continue }
            let roh = try String(contentsOf: datei, encoding: .utf8)
            let ohne = roh.split(separator: "\n", omittingEmptySubsequences: false).map { zeile -> String in
                if let k = zeile.range(of: "//") , !zeile[..<k.lowerBound].contains("\"") {
                    return String(zeile[..<k.lowerBound])
                }
                return String(zeile)
            }.joined(separator: "\n")
            alle[String(datei.path.dropFirst(macQuellen.path.count + 1))] = ohne
        }
        XCTAssertGreaterThan(alle.count, 20)
        return alle
    }

    private func lies(_ teil: String) throws -> String {
        try String(contentsOf: wurzel.appendingPathComponent(teil), encoding: .utf8)
    }

    /// Der Text einer Funktion: ab ihrer Kopfzeile bis zur schliessenden Klammer.
    private func rumpf(_ text: String, ab kopf: String) throws -> String {
        let k = try XCTUnwrap(text.range(of: kopf), "«\(kopf)» fehlt")
        var tiefe = 0
        var begonnen = false
        var ende = text.endIndex
        for i in text[k.lowerBound...].indices {
            if text[i] == "{" { tiefe += 1; begonnen = true }
            if text[i] == "}" { tiefe -= 1; if begonnen && tiefe == 0 { ende = text.index(after: i); break } }
        }
        return String(text[k.lowerBound..<ende])
    }

    // ------------------------------------------------------------- M1: der ganze Startweg

    private static let lesungen = ["Heimschluesselbund.lies(", "Vermittlerschluessel.liesOderErzeuge(",
                                   "Macidentitaet.liesOderErzeuge("]

    func testKeineSchluesselbundLesungStehtAusserhalbDesHintergrunds() throws {
        let alle = try quellen()
        // Aufgerufen werden die drei Lesungen nur von der Hintergrundarbeit des Starts
        // (`Heimleitung.leseSchluesselbund`) und der Lesung des Vermittlers, die dort läuft.
        for (datei, text) in alle {
            for lesung in Self.lesungen where text.contains(lesung) {
                XCTAssertTrue(["Start/Heimleitung.swift", "Vermittlung/Vermittlerlesung.swift"].contains(datei),
                              "\(datei) ruft \(lesung) auf, ausserhalb der Hintergrundarbeit des Starts")
            }
        }
        // Und in Heimleitung steht der Aufruf im Hintergrundlauf (`Startwarten.starte`), vor `fertig:`.
        let leitung = try XCTUnwrap(alle["Start/Heimleitung.swift"])
        let hintergrund = try rumpf(leitung, ab: "func leseSchluesselbund()")
        let lauf = try XCTUnwrap(hintergrund.range(of: "Startwarten.starte("))
        let fertig = try XCTUnwrap(hintergrund.range(of: "fertig:"))
        let arbeit = String(hintergrund[lauf.upperBound..<fertig.lowerBound])
        XCTAssertTrue(arbeit.contains("Heimschluesselbund.lies("), "die Heim-Anmeldung liest nicht im Hintergrund")
        XCTAssertTrue(arbeit.contains("Vermittlerlesung.lies("), "die Lesung des Vermittlers liest nicht im Hintergrund")
        // Die Lesung des Vermittlers hält beide Lesungen in einer Arbeit.
        let lesung = try XCTUnwrap(alle["Vermittlung/Vermittlerlesung.swift"])
        XCTAssertTrue(lesung.contains("Vermittlerschluessel.liesOderErzeuge("))
        XCTAssertTrue(lesung.contains("Macidentitaet.liesOderErzeuge("))
    }

    func testDerVermittlungsdienstLiestBeimAnlegenNichts() throws {
        let alle = try quellen()
        let dienst = try XCTUnwrap(alle["Vermittlung/Vermittlungsdienst.swift"])
        let anlegen = try rumpf(dienst, ab: "init(heim:")
        XCTAssertTrue(anlegen.contains("lesung: Vermittlerlesung"), "der Dienst bekommt die Lesung mit")
        for lesung in Self.lesungen {
            XCTAssertFalse(anlegen.contains(lesung), "Vermittlungsdienst.init liest selbst: \(lesung)")
        }
        // Der Dienst entsteht an einer einzigen Stelle, und erst, wenn die Lesung da ist.
        let anlegerstellen = alle.filter { $0.value.contains("Vermittlungsdienst(heim:") }
        XCTAssertEqual(Array(anlegerstellen.keys), ["Start/Vermittlungsanschluss.swift"])
        let anschluss = try XCTUnwrap(alle["Start/Vermittlungsanschluss.swift"])
        let richte = try rumpf(anschluss, ab: "func richteAus(")
        let wache = try XCTUnwrap(richte.range(of: "guard let lesung"), "richteAus wartet nicht auf die Lesung")
        let neu = try XCTUnwrap(richte.range(of: "Vermittlungsdienst(heim:"))
        XCTAssertLessThan(wache.lowerBound, neu.lowerBound)
    }

    func testDasFensterStehtVorAllenLesungenUndDerHinweisGiltFuerAlle() throws {
        let alle = try quellen()
        let fenster = try XCTUnwrap(alle["Start/Hauptfenster.swift"])
        let beimStart = try rumpf(fenster, ab: ".onAppear {")
        // Beim Erscheinen wird kein Vermittlungsdienst angelegt: das geschieht nach der Antwort.
        XCTAssertFalse(beimStart.contains("vermittlung.richteAus("), "der Dienst entsteht schon beim Erscheinen")
        XCTAssertTrue(beimStart.contains("leitung.leseSchluesselbund()"))
        // Der Hinweis hängt an EINEM Zustand, und der endet erst, wenn alle Lesungen fertig sind.
        let leitung = try XCTUnwrap(alle["Start/Heimleitung.swift"])
        let uebernahme = try rumpf(leitung, ab: "func uebernimmFund(")
        XCTAssertTrue(uebernahme.contains("vermittlerLesung"), "die Vermittlerlesung wird nicht mit übernommen")
        let liest = try XCTUnwrap(uebernahme.range(of: "schluesselbundLiest = false"))
        let vermittler = try XCTUnwrap(uebernahme.range(of: "vermittlerLesung"))
        XCTAssertLessThan(vermittler.lowerBound, liest.lowerBound)
        // Nach der Antwort richtet das Fenster den Dienst aus (mit der Lesung), einmal.
        let nach = try rumpf(fenster, ab: ".onChange(of: leitung.schluesselbundLiest)")
        XCTAssertTrue(nach.contains("vermittlung.uebernimm("))
    }

    // ------------------------------------------------------------- M2: der Testbau berührt nichts

    func testDerTestbauSchreibtNieInDenSchluesselbund() throws {
        let alle = try quellen()
        // Schreibende Schlüsselbund-Aufrufe gibt es nur in diesen drei Dateien, und jede
        // schreibende Funktion fragt zuerst nach dem Testbau.
        let schreibend = ["SecItemAdd(", "SecItemDelete(", "SecItemUpdate(", "SecKeyCreateRandomKey("]
        let erlaubt: Set<String> = ["Start/Heimschluesselbund.swift", "Vermittlung/Vermittlerschluessel.swift",
                                    "Start/Macidentitaet.swift"]
        for (datei, text) in alle where schreibend.contains(where: { text.contains($0) }) {
            XCTAssertTrue(erlaubt.contains(datei), "\(datei) schreibt in den Schlüsselbund")
        }
        let heim = try XCTUnwrap(alle["Start/Heimschluesselbund.swift"])
        for kopf in ["static func speichere(", "static func loesche("] {
            let f = try rumpf(heim, ab: kopf)
            let wache = try XCTUnwrap(f.range(of: "Testbau.aktiv"), "\(kopf) fragt nicht nach dem Testbau")
            XCTAssertLessThan(wache.lowerBound, try XCTUnwrap(f.range(of: "SecItem")).lowerBound)
        }
        let vermittler = try XCTUnwrap(alle["Vermittlung/Vermittlerschluessel.swift"])
        for kopf in ["static func speichere(", "static func liesOderErzeuge("] {
            let f = try rumpf(vermittler, ab: kopf)
            let wache = try XCTUnwrap(f.range(of: "Testbau.aktiv"), "\(kopf) fragt nicht nach dem Testbau")
            let erzeugt = try XCTUnwrap(f.range(of: "speichere(neu)") ?? f.range(of: "SecItemDelete"))
            XCTAssertLessThan(wache.lowerBound, erzeugt.lowerBound)
        }
        let identitaet = try XCTUnwrap(alle["Start/Macidentitaet.swift"])
        for kopf in ["static func liesOderErzeuge(", "private static func erzeuge(", "private static func loesche("] {
            let f = try rumpf(identitaet, ab: kopf)
            let wache = try XCTUnwrap(f.range(of: "Testbau.aktiv"), "\(kopf) fragt nicht nach dem Testbau")
            XCTAssertEqual(wache.lowerBound, f.range(of: "Testbau.aktiv")!.lowerBound)
            for schreiben in schreibend + ["Macidentitaetsregel.schritt("] {
                if let s = f.range(of: schreiben) { XCTAssertLessThan(wache.lowerBound, s.lowerBound, "\(kopf): \(schreiben)") }
            }
        }
    }

    func testDerTestbauLiestAdresseUndFingerabdruckNurAusDerAblageDerInstallierten() throws {
        let alle = try quellen()
        let gedaechtnis = try XCTUnwrap(alle["Start/Heimgedaechtnis.swift"])
        XCTAssertTrue(gedaechtnis.contains("Testbau.ablageDerInstallierten"), "Testbau liest nicht aus der Ablage der installierten")
        let lage = try XCTUnwrap(alle["Start/Testbaulage.swift"])
        XCTAssertTrue(lage.contains("UserDefaults(suiteName:"))
        XCTAssertTrue(lage.contains("installierteKennung(testkennung:"))
        // Geschrieben wird im Testbau nicht: jeder Setzer fragt zuerst.
        let setzer = gedaechtnis.components(separatedBy: "set {").dropFirst()
        XCTAssertEqual(setzer.count, 2)
        for s in setzer {
            XCTAssertTrue(s.prefix(120).contains("Testbau.aktiv"), "ein Setzer schreibt auch im Testbau: \(s.prefix(120))")
        }
    }

    func testKoppelnUndVonHandEintragenSagenImTestbauEinenSatz() throws {
        let alle = try quellen()
        let leitung = try XCTUnwrap(alle["Start/Heimleitung.swift"])
        for kopf in ["func richteEin(adresse", "func richteEin(zugang"] {
            let f = try rumpf(leitung, ab: kopf)
            let wache = try XCTUnwrap(f.range(of: "Testbau.aktiv"), "\(kopf) sagt im Testbau nichts")
            XCTAssertTrue(f.contains("Testbau.satzKoppeln"))
            XCTAssertLessThan(wache.lowerBound, try XCTUnwrap(f.range(of: "Heimschluesselbund.speichere(")).lowerBound)
        }
        // Die Blätter fordern im Testbau nicht erst eine Zahl am Heim-PC an.
        let koppeln = try XCTUnwrap(alle["Start/Koppeln.swift"])
        XCTAssertTrue(koppeln.contains("Testbau.aktiv"))
        XCTAssertTrue(koppeln.contains("Testbau.satzKoppeln"))
        let ipad = try XCTUnwrap(alle["Start/IpadKoppelfenster.swift"])
        XCTAssertTrue(ipad.contains("Testbau.satzKoppeln"), "«iPad koppeln» geht im Testbau an der installierten App vorbei")
    }

    // ------------------------------------------------------------- die Regel im Kern

    func testDieTestbauKennungUndDieInstallierte() {
        let installiert = "\(Marke.kennung).mac"
        XCTAssertTrue(Testbau.istTestbau(kennung: installiert + ".test"))
        XCTAssertFalse(Testbau.istTestbau(kennung: installiert))
        XCTAssertFalse(Testbau.istTestbau(kennung: nil))
        XCTAssertEqual(Testbau.installierteKennung(testkennung: installiert + ".test"), installiert)
        XCTAssertNil(Testbau.installierteKennung(testkennung: installiert))
        XCTAssertNil(Testbau.installierteKennung(testkennung: ".test"), "nichts übrig, also keine Kennung")
    }

    func testDieSaetzeSindEinSatzUndNennenDenGrund() {
        for satz in [Testbau.satzKoppeln, Testbau.satzKeinZugang, Testbau.satzKeinZertifikat] {
            XCTAssertEqual(satz.filter { ".!?".contains($0) }.count, 1, "mehr oder weniger als ein Satz: \(satz)")
            XCTAssertTrue(satz.contains("Testbau"), satz)
        }
        XCTAssertTrue(Testbau.satzKoppeln.contains("installierten"))
    }

    func testDieAnleitungSagtGenauWasDerTestbauLiestUndNichtSchreibt() throws {
        let text = try lies("ipad/\(Marke.name)Mac/LIESMICH.md")
        let k = try XCTUnwrap(text.range(of: "## Testbau"))
        let rest = text[k.lowerBound...].dropFirst(3)
        let abschnitt = String(rest.prefix(upTo: rest.range(of: "\n## ")?.lowerBound ?? rest.endIndex))
        XCTAssertFalse(abschnitt.contains("bleibt derselbe"), "der alte Satz führte in den Eingriff")
        for wort in ["nur lesend", "schreibt nichts in den Schlüsselbund", "Koppeln", "Von Hand eintragen",
                     "Adresse", "Fingerabdruck", "erzeugt nie"] {
            XCTAssertTrue(abschnitt.contains(wort), "Anleitung nennt «\(wort)» nicht")
        }
    }
}
