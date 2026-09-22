import Foundation

/// Was sich die App über die gekoppelte HomeStation merkt — **nur, was kein Geheimnis ist:**
/// ihre Adresse, ihren Namen im Heimnetz und den Projektordner auf ihr.
///
/// Das Geheimnis für die Tür liegt **nicht** hier, sondern in `Schluesselbund.swift`. Eine
/// Probe (`AnfragenTests`) fällt, sobald eine Datei dieser Einheit, die `UserDefaults`
/// benutzt, es beim Namen nennt — die Lehre aus dem früheren Mac-Client (22.09.2026).
enum Verbindungsgedaechtnis {
    private static let adresseSchluessel = "verbindung.adresse"
    private static let nameSchluessel = "verbindung.name"
    private static let ordnerSchluessel = "verbindung.ordner"

    /// Wo die HomeStation zuletzt antwortete.
    static var adresse: URL? {
        get { UserDefaults.standard.string(forKey: adresseSchluessel).flatMap(URL.init(string:)) }
        set { UserDefaults.standard.set(newValue?.absoluteString, forKey: adresseSchluessel) }
    }

    /// Ihr Name im Heimnetz (Bonjour) — `nil`, wenn die Adresse eingetippt wurde.
    static var name: String? {
        get { UserDefaults.standard.string(forKey: nameSchluessel) }
        set { UserDefaults.standard.set(newValue, forKey: nameSchluessel) }
    }

    /// Der Projektordner **auf der HomeStation**; leer heisst: der, mit dem sie gestartet
    /// wurde (Protokoll §3).
    static var ordner: String {
        get { UserDefaults.standard.string(forKey: ordnerSchluessel) ?? "" }
        set { UserDefaults.standard.set(newValue, forKey: ordnerSchluessel) }
    }

    /// Vergisst Adresse und Namen. Der Ordner bleibt — er gehört zur Arbeit, nicht zur
    /// Kopplung.
    static func vergiss() {
        UserDefaults.standard.removeObject(forKey: adresseSchluessel)
        UserDefaults.standard.removeObject(forKey: nameSchluessel)
    }
}
