import Foundation
import Security

/// Die Ablage des Verbindungsgedächtnisses im Schlüsselbund (seit 0.2.12) — **ohne** die
/// App-Einstellungen, und darum eine eigene Datei: `AnfragenTests` bewacht, dass keine Datei,
/// die `UserDefaults` benutzt, vom Geheimnis spricht; diese spricht nur vom Schlüsselbund.
///
/// Ein eigener Dienst `<kennung>.verbindung`, getrennt von der Anmeldung (`Schluesselbund`):
/// Nichts Geheimes wird mit dem Gedächtnis zusammen gelesen oder gelöscht. Gespeichert werden
/// kurze Texte (Adresse, Name, Ordner), nur auf diesem Gerät, nach dem ersten Entsperren.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
enum Gedaechtnisablage {
    private static var dienst: String { Marke.kennung + ".verbindung" }

    private static func frage(_ schluessel: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: dienst,
         kSecAttrAccount as String: schluessel]
    }

    static func lies(_ schluessel: String) -> String? {
        var f = frage(schluessel)
        f[kSecReturnData as String] = true
        f[kSecMatchLimit as String] = kSecMatchLimitOne
        var ergebnis: CFTypeRef?
        guard SecItemCopyMatching(f as CFDictionary, &ergebnis) == errSecSuccess,
              let daten = ergebnis as? Data else { return nil }
        return String(data: daten, encoding: .utf8)
    }

    /// `nil` löscht. Fehler bleiben still: Ein Gedächtnis, das nicht geschrieben werden kann,
    /// heisst nur «beim nächsten Mal neu koppeln».
    static func schreibe(_ schluessel: String, _ wert: String?) {
        SecItemDelete(frage(schluessel) as CFDictionary)
        guard let wert, let daten = wert.data(using: .utf8) else { return }
        var neu = frage(schluessel)
        neu[kSecValueData as String] = daten
        neu[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        SecItemAdd(neu as CFDictionary, nil)
    }
}
