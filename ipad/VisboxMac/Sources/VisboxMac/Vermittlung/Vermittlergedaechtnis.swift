import Foundation

/// Was sich die Vermittlung merkt — **nur, was kein Geheimnis ist:** ob schon einmal ein iPad
/// gekoppelt war (dann öffnet der Mac beim Start keine neue Zahl).
///
/// Eine eigene Datei, wie `Heimgedaechtnis`: Der Zugang des iPad liegt im Schlüsselbund
/// (`Vermittlerschluessel.swift`), und eine Datei, die `UserDefaults` benutzt, soll ihn nicht
/// einmal nennen (bewacht in `tests/test_ipad_geruest.py`).
enum Vermittlergedaechtnis {
    private static let gekoppeltSchluessel = "vermittlung.ipadGekoppelt"

    static var gekoppelt: Bool {
        get { UserDefaults.standard.bool(forKey: gekoppeltSchluessel) }
        set {
            if newValue {
                UserDefaults.standard.set(true, forKey: gekoppeltSchluessel)
            } else {
                UserDefaults.standard.removeObject(forKey: gekoppeltSchluessel)
            }
        }
    }
}
