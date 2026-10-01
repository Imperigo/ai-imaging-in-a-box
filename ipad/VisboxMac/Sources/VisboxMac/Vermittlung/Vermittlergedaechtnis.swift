import Foundation

/// Was sich die Vermittlung merkt — **nur, was kein Geheimnis ist:** ob schon einmal ein iPad
/// gekoppelt war (dann öffnet der Mac beim Start keine neue Zahl), und ob «iPad über diesen
/// Mac anbieten» an ist.
///
/// Eine eigene Datei, wie `Heimgedaechtnis`: Der Zugang des iPad liegt im Schlüsselbund
/// (`Vermittlerschluessel.swift`), und eine Datei, die `UserDefaults` benutzt, soll ihn nicht
/// einmal nennen (bewacht in `tests/test_ipad_geruest.py`).
enum Vermittlergedaechtnis {
    private static let gekoppeltSchluessel = "vermittlung.ipadGekoppelt"
    private static let angebotenSchluessel = "vermittlung.ipadAnbieten"

    /// **«iPad über diesen Mac anbieten» — Vorgabe aus** (Sicherheitsdurchsicht und
    /// Owner-Entscheid vom 01.10.2026). Unterwegs spricht das iPad über Tailscale direkt mit
    /// dem Heim-PC; der Mac bietet sich nur an, wer es einschaltet. Vorher bot er sich in
    /// jedem WLAN an, sobald der Heim-PC eingerichtet war, und zeigte beim ersten Start eine
    /// Zahl — fünf Versuche für jeden, der im Café mithörte.
    static var angeboten: Bool {
        get { UserDefaults.standard.bool(forKey: angebotenSchluessel) }
        set {
            if newValue {
                UserDefaults.standard.set(true, forKey: angebotenSchluessel)
            } else {
                UserDefaults.standard.removeObject(forKey: angebotenSchluessel)
            }
        }
    }

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
