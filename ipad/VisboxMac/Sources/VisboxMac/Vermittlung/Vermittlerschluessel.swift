import Foundation
import Security
import VisboxKern

/// Die Zugangsdaten, die der Mac dem iPad gibt — **im Schlüsselbund des Mac, und nur dort.**
///
/// Sie überleben einen Neustart der App, damit das iPad nicht jedes Mal neu koppeln muss.
/// Sie sind **nicht** das Kennwort des Heim-PC (das legt die Mac-App unter einem eigenen
/// Eintrag ab) — getrennt, damit «das iPad vergessen» (`Vermittlungsdienst.vergissIPad`)
/// nur diese ersetzt und am Heim-PC nichts ändert.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).* Offen ist, ob macOS bei einer App mit
/// Behelfs-Unterschrift nach jedem neuen Bau beim Lesen fragt («… möchte auf den
/// Schlüsselbund zugreifen») — dann steht das einmal am Bildschirm, mehr nicht.
enum Vermittlerschluessel {
    /// Unter welchem Dienst der Eintrag liegt — aus der Marke, damit er beim Umbenennen
    /// mitgeht.
    private static var dienst: String { Marke.kennung + ".vermittler" }
    private static let konto = "ipad"

    private static var grundfrage: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: dienst,
         kSecAttrAccount as String: konto]
    }

    /// Liest die Zugangsdaten — oder erzeugt neue und legt sie ab. Der Satz ist `nil`, wenn
    /// alles ging; sonst sagt er, warum das iPad nach einem Neustart neu koppeln muss.
    static func liesOderErzeuge() -> (Vermittlerzugang, String?) {
        var frage = grundfrage
        frage[kSecReturnData as String] = true
        frage[kSecMatchLimit as String] = kSecMatchLimitOne
        var ergebnis: CFTypeRef?
        let stand = SecItemCopyMatching(frage as CFDictionary, &ergebnis)
        if stand == errSecSuccess, let daten = ergebnis as? Data,
           let zugang = try? JSONDecoder().decode(Vermittlerzugang.self, from: daten),
           zugang.anmeldung.benutzer == Vermittlerzugang.benutzer {
            return (zugang, nil)
        }
        // KEINER, UNLESBAR ODER AUS EINER FRUEHEREN FASSUNG: neu. Ein gekoppeltes iPad muss
        // dann neu koppeln — das ist ehrlicher als ein Zugang, den niemand mehr pruefen kann.
        let neu = Vermittlerzugang.erzeuge()
        return (neu, speichere(neu))
    }

    /// Legt die Zugangsdaten ab. `nil` heisst: abgelegt; sonst der Satz, warum nicht.
    @discardableResult
    static func speichere(_ zugang: Vermittlerzugang) -> String? {
        guard let daten = try? JSONEncoder().encode(zugang) else {
            return "Der Zugang für das iPad liess sich nicht schreiben — nach einem Neustart "
                + "muss das iPad neu koppeln."
        }
        SecItemDelete(grundfrage as CFDictionary)
        var neu = grundfrage
        neu[kSecValueData as String] = daten
        let stand = SecItemAdd(neu as CFDictionary, nil)
        return stand == errSecSuccess
            ? nil
            : "Der Zugang für das iPad liess sich nicht im Schlüsselbund ablegen (Code \(stand)) "
                + "— nach einem Neustart muss das iPad neu koppeln."
    }
}
