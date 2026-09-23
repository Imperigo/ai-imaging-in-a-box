import Foundation

// DIE FARBTOENE DER ZEICHENFLAECHE — abgeschrieben an einer Stelle, im Kern, damit sie
// hier gegen das Blatt geprueft werden (Durchsicht der Verdrahtung, 22.09.2026).
//
// Befund: Bis dahin standen der Grund des Blattes und die vier Stiftfarben als Zahlen in
// `Zeichnen/` (`UIColor(red: 0x19 / 255.0 …)`, `ton(0xe0, 0x8b, 0x52)`) — dort, wo sie
// keine Probe sah: Der Waechter der Farbtoene suchte nur nach «Farbton(hex:», und
// SwiftUI uebersetzt unter Linux nicht. Jetzt macht `Zeichnen/` aus diesen Werten nur noch
// Farben. `FarbtonTests.testJederStifttonStehtSoAufDemBlatt` haelt jeden Ton gegen die
// Abschrift der Blaetter, `testAusserhalbDesKernsStehtKeinFarbwertAlsZahl` haelt fest,
// dass ausserhalb von `Kern/` keiner mehr als Zahl steht.

/// Eine vorgegebene Stiftfarbe: ihr Name, wie ihn die Bedienhilfe vorliest, und ihr Ton.
///
/// Die Farben **bedeuten nichts** (Entscheid Nr. 8) — sie sind nur schneller erreicht als
/// die freie Wahl daneben.
public struct Stiftton: Equatable, Sendable {
    public let name: String
    public let ton: Farbton

    public init(name: String, ton: Farbton) {
        self.name = name
        self.ton = ton
    }
}

/// Die Töne, die die Zeichenfläche selbst mitbringt.
public enum Stiftfarben {
    /// Der Grund des Zeichenblatts, auf dem gezeichnet wird — Blatt «Main» (und
    /// «MainHoch»): die Fläche des Blattes, `#191d23`.
    ///
    /// Er geht **nicht** mit hinaus: Das PNG hat einen durchsichtigen Grund
    /// (`Zeichenstand.pngAusgabe`), und der Server setzt die Skizze auf ihre Unterlage.
    public static let papier = Farbton(hex: "191d23")

    /// Die vier Stiftfarben in der Reihenfolge des Blatts «Main», Feld «Stift»
    /// (`#e08b52`, `#e6e8ec`, `#6fb3d2`, `#8fd4ac`). Die erste ist die Vorgabe; sie steht
    /// auch auf dem Blatt «Die Zeichen» als «Tinte».
    public static let vorgaben: [Stiftton] = [
        Stiftton(name: "Orange", ton: Farbton(hex: "e08b52")),
        Stiftton(name: "Hell", ton: Farbton(hex: "e6e8ec")),
        Stiftton(name: "Blau", ton: Farbton(hex: "6fb3d2")),
        Stiftton(name: "Grün", ton: Farbton(hex: "8fd4ac")),
    ]
}
