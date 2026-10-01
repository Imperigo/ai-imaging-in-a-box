import Foundation
import Security
import VisboxKern

/// Benutzer und Kennwort für den Heim-PC — **im Schlüsselbund des Mac, und nur dort.**
///
/// Dieselbe Lehre wie bei der iPad-App (`Verbindung/Schluesselbund.swift`): Der frühere
/// Mac-Client legte das Kennwort in `UserDefaults` ab, eine Klartextdatei, die jede Sicherung
/// mitnimmt. Hier liegt es als Schlüsselbund-Eintrag. Die Adresse des Heim-PC ist kein
/// Geheimnis und liegt in `Heimgedaechtnis`; `tests/test_ipad_geruest.py` fällt, sobald eine
/// Datei der Mac-App, die `UserDefaults` benutzt, das Kennwort nennt.
///
/// **Der Schlüsselbund des Anmeldens, nicht der geschützte** (`kSecUseDataProtectionKeychain`
/// bleibt aus): Der geschützte verlangt eine Berechtigung, die nur eine von Apple unterschriebene
/// App trägt — mit der Behelfs-Unterschrift der Prüfstrecke gäbe `SecItemAdd` dort
/// `errSecMissingEntitlement` zurück. Die Folge, und sie steht im LIESMICH: Nach jedem neuen
/// Herunterladen ist die Unterschrift eine andere, und macOS fragt einmal, ob die App an den
/// Eintrag darf.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
enum Heimschluesselbund {

    /// Was die Suche ergab — «keiner» (noch nie eingerichtet) und «nicht lesbar» (es gab
    /// einen, und er ist gerade nicht erreichbar) sind verschieden.
    enum Fund {
        case gefunden(Anmeldung)
        case keiner
        case fehler(String)
    }

    /// Aus der Marke, mit eigener Endung: Der Eintrag der Mac-App ist nicht der des iPad.
    private static var dienst: String { Marke.kennung + ".mac.heim-pc" }
    /// Es gibt **einen** Heim-PC zur Zeit.
    private static let konto = "heim-pc"

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
                           + "(Code \(stand)). Unter «Einrichten» neu eingeben.")
        }
        guard let a = try? JSONDecoder().decode(Anmeldung.self, from: daten) else {
            return .fehler("Der Eintrag im Schlüsselbund ist unlesbar. Unter «Einrichten» neu "
                           + "eingeben.")
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
        // DER NAME IN DER SCHLUESSELBUNDVERWALTUNG — damit ein Mensch den Eintrag findet.
        neu[kSecAttrLabel as String] = "\(Marke.name) · Heim-PC"
        let stand = SecItemAdd(neu as CFDictionary, nil)
        return stand == errSecSuccess
            ? nil
            : "Die Anmeldung liess sich nicht im Schlüsselbund ablegen (Code \(stand))."
    }

    static func loesche() {
        SecItemDelete(grundfrage as CFDictionary)
    }
}
