import Foundation
import Security

/// Die Anmeldung für die HomeStation — **im Schlüsselbund, und nur dort.**
///
/// **Die Lehre aus dem früheren Mac-Client** (Codex-Repo, gelesen am 22.09.2026): Er legte
/// das Kennwort in `UserDefaults` ab — eine Klartextdatei im Ordner der App, die jede
/// Sicherung mitnimmt. Hier liegt es als Schlüsselbund-Eintrag, nur auf diesem Gerät und
/// erst nach dem ersten Entsperren lesbar (`AfterFirstUnlockThisDeviceOnly`: das
/// Nachsenden aus dem Parkfach soll auch bei gesperrtem Schirm gehen, eine Sicherung auf
/// ein anderes Gerät soll es nicht mitnehmen).
///
/// `AnfragenTests.testKeineDateiMitUserDefaultsNenntDasKennwort` prüft die Abwesenheit:
/// Keine Datei dieser Einheit, die `UserDefaults` benutzt, nennt das Kennwort.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
enum Schluesselbund {

    /// Was die Suche im Schlüsselbund ergab — **drei Fälle.** «Keiner» und «nicht lesbar»
    /// sind verschieden: Das erste heisst «noch nie gekoppelt», das zweite «es gab eine,
    /// und sie ist gerade nicht erreichbar».
    enum Fund {
        case gefunden(Anmeldung)
        case keiner
        case fehler(String)
    }

    /// Unter welchem Dienst der Eintrag liegt — aus der Marke, damit KosmoSketch ihn unter
    /// seinem eigenen Namen führt.
    private static var dienst: String { Marke.kennung + ".homestation" }
    /// Es gibt **eine** gekoppelte HomeStation zur Zeit.
    private static let konto = "homestation"

    private static var grundfrage: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: dienst,
         kSecAttrAccount as String: konto]
    }

    static func lies() -> Fund {
        var frage = grundfrage
        frage[kSecReturnData as String] = true
        frage[kSecMatchLimit as String] = kSecMatchLimitOne
        var ergebnis: CFTypeRef?
        let stand = SecItemCopyMatching(frage as CFDictionary, &ergebnis)
        if stand == errSecItemNotFound { return .keiner }
        guard stand == errSecSuccess, let daten = ergebnis as? Data else {
            return .fehler("Die Anmeldung liess sich nicht aus dem Schlüsselbund lesen "
                           + "(Code \(stand)).")
        }
        guard let a = try? JSONDecoder().decode(Anmeldung.self, from: daten) else {
            return .fehler("Die Anmeldung im Schlüsselbund ist unlesbar. Neu koppeln.")
        }
        return .gefunden(a)
    }

    /// Legt die Anmeldung ab. `nil` heisst: abgelegt; sonst der Satz, warum nicht.
    @discardableResult
    static func speichere(_ anmeldung: Anmeldung) -> String? {
        guard let daten = try? JSONEncoder().encode(anmeldung) else {
            return "Die Anmeldung liess sich nicht schreiben."
        }
        SecItemDelete(grundfrage as CFDictionary)
        var neu = grundfrage
        neu[kSecValueData as String] = daten
        neu[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        let stand = SecItemAdd(neu as CFDictionary, nil)
        return stand == errSecSuccess
            ? nil
            : "Die Anmeldung liess sich nicht im Schlüsselbund ablegen (Code \(stand))."
    }

    static func loesche() {
        SecItemDelete(grundfrage as CFDictionary)
    }
}
