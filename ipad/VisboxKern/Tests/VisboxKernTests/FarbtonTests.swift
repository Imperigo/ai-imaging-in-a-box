import Foundation
import XCTest
import VisboxKern

/// Die Farbtöne der Zeichenfläche — **sie stehen so auf dem Blatt, und nirgends sonst als
/// Zahl** (Durchsicht der Verdrahtung, 22.09.2026).
///
/// Befund: Der Grund des Blattes und die vier Stiftfarben standen als Zahlen in `Zeichnen/`
/// (`UIColor(red: 0x19 / 255.0 …)`, `ton(0xe0, 0x8b, 0x52)`), und die Probe
/// `PruefzeichenTests.testDieAppSchreibtKeineFarbtoeneAusserhalbDesKerns` sah sie nicht —
/// sie suchte nur nach `Farbton(hex:`. Jetzt stehen die Töne in `Kern/Stiftfarben.swift`
/// und hier gegen die Abschrift der Blätter; ausserhalb des Kerns steht kein Farbwert mehr
/// als Zahl, in keiner Schreibweise, die diese Probe kennt.
final class FarbtonTests: XCTestCase {

    // ------------------------------------------------------ die Abschrift der Blätter

    /// Die Stiftfarben, wie sie auf dem Blatt «Main» im Feld «Stift» stehen, in dieser
    /// Reihenfolge (abgeschrieben am 22.09.2026). Die erste steht auch auf dem Blatt
    /// «Die Zeichen» («Nur für den Stift»: Tinte).
    private let stiftfarbenAufDemBlatt: [(blatt: String, name: String, hex: String)] = [
        ("Main, Feld «Stift» · Die Zeichen, «Tinte»", "Orange", "#e08b52"),
        ("Main, Feld «Stift»", "Hell", "#e6e8ec"),
        ("Main, Feld «Stift»", "Blau", "#6fb3d2"),
        ("Main, Feld «Stift»", "Grün", "#8fd4ac"),
    ]

    /// Der Grund des Zeichenblatts — Blätter «Main» und «MainHoch», die Fläche der Skizze.
    private let papierAufDemBlatt = (blatt: "Main · MainHoch, Fläche der Skizze", hex: "#191d23")

    /// Jeder Ton aus `Stiftfarben` steht **so** auf dem Blatt — und jeder Ton des Blatts
    /// steht in `Stiftfarben`, in derselben Reihenfolge. Verglichen wird die Hex-Schreibweise:
    /// `Farbton(hex:)` fällt bei einem Schreibfehler still auf Schwarz, `#000000` stünde
    /// dann hier gegen den Ton des Blatts.
    func testJederStifttonStehtSoAufDemBlatt() {
        XCTAssertEqual(Stiftfarben.vorgaben.count, stiftfarbenAufDemBlatt.count,
                       "so viele Stiftfarben, wie das Blatt zeigt")
        for (ton, blatt) in zip(Stiftfarben.vorgaben, stiftfarbenAufDemBlatt) {
            XCTAssertEqual(ton.name, blatt.name, blatt.blatt)
            XCTAssertEqual(ton.ton.hex, blatt.hex, "\(blatt.name) — Blatt \(blatt.blatt)")
        }
        XCTAssertEqual(Stiftfarben.papier.hex, papierAufDemBlatt.hex,
                       "Papier — Blatt \(papierAufDemBlatt.blatt)")
    }

    /// Die App führt eine Stiftfarbe über ihren Namen (`Stiftfarbe.id`, gewählt ist sie
    /// über `farbvorgabe`). Zwei gleiche Namen wären zwei Knöpfe, die als einer gewählt sind.
    func testJedeStiftfarbeHatIhrenEigenenNamen() {
        let namen = Stiftfarben.vorgaben.map { $0.name }
        XCTAssertEqual(Set(namen).count, namen.count, "\(namen)")
    }

    // --------------------------------------------- die Abwesenheit ausserhalb des Kerns

    /// Die Schreibweisen, in denen ein Farbwert als Zahl im Quelltext stehen kann — **im
    /// Code, nicht im Kommentar** (ein Kommentar färbt nichts). Jede ist unten an einem
    /// Beispiel geprüft (`testDieProbeErkenntJedeSchreibweise`).
    private static let farbzahlen: [(name: String, muster: String)] = [
        // `srgbRed:` und `displayP3Red:` (CGColor, UIColor) seit der Durchsicht der Welle 2b
        // (23.09.2026): Stand der erste Kanal allein in einer Zeile, sah die Probe ihn nicht.
        ("Kanal als Zahl (red:/green:/blue:/white:/srgbRed:/displayP3Red: …)",
         #"\b(red|green|blue|white|hue|saturation|brightness|srgbRed|displayP3Red)\s*:\s*[-+]?(0x[0-9a-fA-F]+|[0-9]*\.?[0-9]+)"#),
        ("Zahl durch 255", #"(0x[0-9a-fA-F]+|\b[0-9]+(\.[0-9]+)?)\s*/\s*255"#),
        ("Hex-Text #rrggbb", #"#[0-9a-fA-F]{6}\b"#),
        ("Farbton aus Ziffern", #"Farbton\s*\(\s*(hex\s*:|rot\s*:\s*[0-9])"#),
        // Drei Hex-Bytes als Aufruf, `(0xe0, 0x8b, 0x52)`: ein Ton, gleich wie die Hilfe
        // heisst. Eine Byte-Liste in eckigen Klammern (die PNG-Kennung) ist keiner.
        ("drei Hex-Bytes als Aufruf",
         #"\(\s*0x[0-9a-fA-F]{2}\s*,\s*0x[0-9a-fA-F]{2}\s*,\s*0x[0-9a-fA-F]{2}"#),
        ("Hex-Zahl neben einer Farbe",
         #"(?=.*(Color|UIColor|CGColor|[Ff]arb|\bton\b|rgb|RGB)).*0x[0-9a-fA-F]{2}"#),
    ]

    /// Was in einer Zeile Code ist — ohne `//`-Kommentar und ohne `/* … */`. Zeichenketten
    /// bleiben stehen: Ein `"#191d23"` im Code ist ein Farbwert.
    private static func code(_ text: String) -> [String] {
        var zeilen: [String] = []
        var imBlock = false
        for zeile in text.components(separatedBy: "\n") {
            var aus = ""
            var inKette = false
            var i = zeile.startIndex
            while i < zeile.endIndex {
                let rest = zeile[i...]
                if imBlock {
                    if rest.hasPrefix("*/") { imBlock = false; i = zeile.index(i, offsetBy: 2) }
                    else { i = zeile.index(after: i) }
                    continue
                }
                if !inKette && rest.hasPrefix("//") { break }
                if !inKette && rest.hasPrefix("/*") { imBlock = true; i = zeile.index(i, offsetBy: 2); continue }
                let c = zeile[i]
                if c == "\\" && inKette {
                    aus.append(c)
                    i = zeile.index(after: i)
                    if i < zeile.endIndex { aus.append(zeile[i]); i = zeile.index(after: i) }
                    continue
                }
                if c == "\"" { inKette.toggle() }
                aus.append(c)
                i = zeile.index(after: i)
            }
            zeilen.append(aus)
        }
        return zeilen
    }

    /// Die Funde in einem Quelltext: `(Zeilennummer, Schreibweise, Zeile)`.
    private static func funde(in text: String) -> [(Int, String, String)] {
        var gefunden: [(Int, String, String)] = []
        for (nummer, zeile) in code(text).enumerated() {
            let ganz = NSRange(zeile.startIndex..., in: zeile)
            for (name, muster) in farbzahlen {
                // Ein Muster, das nicht übersetzt, ist ein Fehler dieser Probe — laut, nicht still.
                let ausdruck = try! NSRegularExpression(pattern: muster)
                if ausdruck.firstMatch(in: zeile, range: ganz) != nil {
                    gefunden.append((nummer + 1, name, zeile.trimmingCharacters(in: .whitespaces)))
                }
            }
        }
        return gefunden
    }

    /// **Die Probe selbst**, an den Zeilen, die vor der Durchsicht in `Zeichnen/` standen —
    /// und an denen, die bleiben dürfen.
    func testDieProbeErkenntJedeSchreibweise() {
        let verboten = [
            "backgroundColor = UIColor(red: 0x19 / 255.0, green: 0x1d / 255.0,",
            "Stiftfarbe(name: \"Orange\", farbe: ton(0xe0, 0x8b, 0x52)),",
            "Color(red: 0.1, green: 0.11, blue: 0.14)",
            "let papier = \"#191d23\"",
            "let tinte = Farbton(hex: \"e08b52\")",
            "let tinte = Farbton(rot: 224, gruen: 139, blau: 82)",
            "let grund = UIColor(white: 0.1, alpha: 1)",
            "let wert = 0x191d23; let farbe = UIColor(rgb: wert)",
            "static let orange = mach(0xe0, 0x8b, 0x52)",
            "Color(uiColor: UIColor(red: 25/255, green: 29/255, blue: 35/255, alpha: 1))",
            // Der erste Kanal allein in seiner Zeile, die anderen darunter.
            "let grund = CGColor(srgbRed: 0.098,",
            "let grund = UIColor(displayP3Red: 0.1,",
        ]
        for zeile in verboten {
            XCTAssertFalse(FarbtonTests.funde(in: zeile).isEmpty, "übersehen: \(zeile)")
        }
        let erlaubt = [
            "self.init(.sRGB, red: Double(ton.rot) / 255, green: Double(ton.gruen) / 255,",
            "backgroundColor = UIColor(Color(Stiftfarben.papier))",
            "// Der Grund des Blattes (Blatt «Main»: #191d23).",
            "let x = 1 /* red: 0x19 / 255 */ + 2",
            "let url = \"http://beispiel/#abc\" // #191d23",
            "static let pngKennung: [UInt8] = [0x89, 0x50, 0x4E, 0x47]",
            ".opacity(0.35 + 0.65 * welle)",
            ".foregroundStyle(Color(zeichen.art.schrift))",
            "let srgbRedAnteil = ton.rot",
        ]
        for zeile in erlaubt {
            XCTAssertEqual(FarbtonTests.funde(in: zeile).map { $0.1 }, [], "fälschlich: \(zeile)")
        }
    }

    /// **Eine Abwesenheit:** In keiner Swift-Datei des App-Pakets ausserhalb von `Kern/`
    /// steht ein Farbwert als Zahl. Sonst gäbe es einen Ton, den keine Probe gegen das Blatt
    /// hält — wie den Grund des Blattes und die Stiftfarben bis zum 22.09.2026. **Nur in den
    /// Schreibweisen von `farbzahlen`**; die bekannten Lücken (Hex-Bytes in eckigen Klammern
    /// ohne Farbwort, ein berechneter Kanal, ein Asset-Katalog) stehen in
    /// `Kern/Stiftfarben.swift`.
    func testAusserhalbDesKernsStehtKeinFarbwertAlsZahl() throws {
        // DAS APP-PAKET UEBER DEN VERWEIS DES KERNS GEFUNDEN, wie in
        // `PruefzeichenTests.testDieAppSchreibtKeineFarbtoeneAusserhalbDesKerns` — nicht
        // über seinen Namen, der nur in `Marke.swift` stehen darf. `Sources/` dieses
        // Prüfpakets enthält genau einen Eintrag: den Verweis.
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
        guard let gang = FileManager.default.enumerator(at: app,
                                                        includingPropertiesForKeys: nil) else {
            return XCTFail("App-Paket nicht gefunden: \(app.path)")
        }
        var gelesen: [String] = []
        var funde: [String] = []
        for case let datei as URL in gang where datei.pathExtension == "swift" {
            let echt = datei.resolvingSymlinksInPath().path
            if echt.hasPrefix(kern.path + "/") { continue }
            let text = try String(contentsOf: datei, encoding: .utf8)
            let name = String(echt.dropFirst(app.path.count + 1))
            gelesen.append(name)
            for (zeile, schreibweise, inhalt) in FarbtonTests.funde(in: text) {
                funde.append("\(name):\(zeile) — \(schreibweise): \(inhalt)")
            }
        }
        XCTAssertEqual(funde, [], "Farbwerte als Zahl ausserhalb von Kern/ — in "
                       + "Kern/Stiftfarben.swift oder Blattfarbe ablegen und gegen das Blatt halten")
        // DIE PROBE MUSS DIE DATEIEN GESEHEN HABEN, um die es ging.
        XCTAssertTrue(gelesen.contains("Zeichnen/Zeichenleinwand.swift"), "\(gelesen)")
        XCTAssertTrue(gelesen.contains("Zeichnen/Zeichenstand.swift"), "\(gelesen)")
        XCTAssertGreaterThan(gelesen.count, 5, "\(gelesen)")
    }
}
