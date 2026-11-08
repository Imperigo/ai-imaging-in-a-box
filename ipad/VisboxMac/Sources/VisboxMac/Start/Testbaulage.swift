import Foundation
import VisboxKern

/// Ob diese laufende App ein Testbau ist (A0255, E144): ihre Bündelkennung trägt die Endung `.test`
/// (`Testbau.endung`, vom Kern). Die Regeln dazu stehen im Kern (`Testbau`); hier nur die Messung.
extension Testbau {
    static var aktiv: Bool { istTestbau(kennung: Bundle.main.bundleIdentifier) }

    /// Die Ablage der installierten App (ihre Einstellungen, **nur zum Lesen**) — `nil` ausserhalb
    /// eines Testbaus.
    static var ablageDerInstallierten: UserDefaults? {
        guard let kennung = Bundle.main.bundleIdentifier,
              let installiert = installierteKennung(testkennung: kennung) else { return nil }
        return UserDefaults(suiteName: installiert)
    }
}
