import Foundation
import Security

/// Was sich die App über die gekoppelte HomeStation merkt — **nur, was kein Geheimnis ist:**
/// ihre Adresse (samt Schema), ihren Namen im Heimnetz, ob der Mac vermittelt, und den Projektordner auf ihr.
///
/// Das Geheimnis für die Tür liegt **nicht** hier, sondern in `Schluesselbund.swift`. Eine
/// Probe (`AnfragenTests`) fällt, sobald eine Datei dieser Einheit, die `UserDefaults`
/// benutzt, es beim Namen nennt — die Lehre aus dem früheren Mac-Client (22.09.2026).
///
/// **SEIT 0.2.12 IM SCHLÜSSELBUND, nicht mehr in den App-Einstellungen** (Owner, 20.10.2026:
/// «Kopplung einmal machen, danach nie wieder»). Die App-Einstellungen gehen mit, wenn die App
/// aktualisiert wird — aber nicht, wenn sie über Xcode gelöscht und neu aufgespielt wird; dann
/// musste neu gekoppelt werden, obwohl das Kennwort im Schlüsselbund noch lag. Der
/// Schlüsselbund bleibt auf dem Gerät. Gespeichert wird hier weiter **kein Geheimnis**, nur
/// unter einem eigenen Dienst neben der Anmeldung. Was noch in den App-Einstellungen steht
/// (alte Fassung), wird beim ersten Lesen übernommen.
enum Verbindungsgedaechtnis {
    private static let adresseSchluessel = "verbindung.adresse"
    private static let nameSchluessel = "verbindung.name"
    private static let ordnerSchluessel = "verbindung.ordner"
    private static let macSchluessel = "verbindung.ueberDenMac"

    /// Wo die HomeStation zuletzt antwortete — **samt Schema**: `http://…:8731` im Heimnetz,
    /// `https://<rechner>.<netz>.ts.net:8443` unterwegs über Tailscale (Entscheid 63). Jede
    /// Anfrage baut ihre Adresse aus genau dieser Basis (`Wege.adresse` übernimmt Schema,
    /// Rechner und Anschluss); ein festes `http://` gibt es dazwischen nicht.
    ///
    /// Zurückgelesen wird über `Suche.gemerkt` (Kern, mit Proben): unverändert, aber nur, was
    /// eine Adresse der App sein kann. Eine verdorbene Angabe heisst «nicht gekoppelt», nicht
    /// eine Anfrage an einen Ort, den niemand gewählt hat.
    static var adresse: URL? {
        get { Suche.gemerkt(lies(adresseSchluessel)) }
        set { schreibe(adresseSchluessel, newValue?.absoluteString) }
    }

    /// Ihr Name im Heimnetz (Bonjour) — `nil`, wenn die Adresse eingetippt wurde.
    static var name: String? {
        get { lies(nameSchluessel) }
        set { schreibe(nameSchluessel, newValue) }
    }

    /// Ob unterwegs der Mac vermittelt (TXT `vermittler=mac`, Protokoll §8b) — nur für die
    /// Anzeige «über den Mac».
    static var ueberDenMac: Bool {
        get { lies(macSchluessel) == "1" }
        set { schreibe(macSchluessel, newValue ? "1" : nil) }
    }

    /// Der Projektordner **auf der HomeStation**; leer heisst: der, mit dem sie gestartet
    /// wurde (Protokoll §3).
    static var ordner: String {
        get { lies(ordnerSchluessel) ?? "" }
        set { schreibe(ordnerSchluessel, newValue.isEmpty ? nil : newValue) }
    }

    /// Vergisst Adresse und Namen. Der Ordner bleibt — er gehört zur Arbeit, nicht zur
    /// Kopplung.
    static func vergiss() {
        for schluessel in [adresseSchluessel, nameSchluessel, macSchluessel] {
            schreibe(schluessel, nil)
        }
    }

    // ------------------------------------------------------------ Ablage (seit 0.2.12)

    /// Der Dienst im Schlüsselbund — neben dem der Anmeldung (`Schluesselbund`), nicht in ihm:
    /// Kein Geheimnis soll mit dem Gedächtnis zusammen gelesen oder gelöscht werden.
    private static var dienst: String { Marke.kennung + ".verbindung" }

    private static func frage(_ schluessel: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: dienst,
         kSecAttrAccount as String: schluessel]
    }

    /// Liest einen Wert — aus dem Schlüsselbund, sonst (einmalig) aus den App-Einstellungen
    /// der alten Fassung, und übernimmt ihn dabei.
    private static func lies(_ schluessel: String) -> String? {
        var f = frage(schluessel)
        f[kSecReturnData as String] = true
        f[kSecMatchLimit as String] = kSecMatchLimitOne
        var ergebnis: CFTypeRef?
        if SecItemCopyMatching(f as CFDictionary, &ergebnis) == errSecSuccess,
           let daten = ergebnis as? Data, let text = String(data: daten, encoding: .utf8) {
            return text
        }
        // DIE ÜBERNAHME aus 0.2.11 und älter: Steht der Wert noch in den App-Einstellungen,
        // wandert er in den Schlüsselbund und verschwindet dort, wo er herkam.
        let alt: String?
        if schluessel == macSchluessel {
            alt = UserDefaults.standard.object(forKey: schluessel) == nil
                ? nil : (UserDefaults.standard.bool(forKey: schluessel) ? "1" : nil)
        } else {
            alt = UserDefaults.standard.string(forKey: schluessel)
        }
        guard let alt else { return nil }
        schreibe(schluessel, alt)
        UserDefaults.standard.removeObject(forKey: schluessel)
        return alt
    }

    /// Schreibt einen Wert; `nil` löscht ihn. Fehler bleiben still: Ein Gedächtnis, das
    /// nicht geschrieben werden kann, heisst nur «beim nächsten Mal neu koppeln».
    private static func schreibe(_ schluessel: String, _ wert: String?) {
        SecItemDelete(frage(schluessel) as CFDictionary)
        UserDefaults.standard.removeObject(forKey: schluessel)
        guard let wert, let daten = wert.data(using: .utf8) else { return }
        var neu = frage(schluessel)
        neu[kSecValueData as String] = daten
        neu[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        SecItemAdd(neu as CFDictionary, nil)
    }
}
