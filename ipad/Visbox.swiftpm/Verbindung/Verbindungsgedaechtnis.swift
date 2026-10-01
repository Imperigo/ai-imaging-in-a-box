import Foundation

/// Was sich die App über die gekoppelte HomeStation merkt — **nur, was kein Geheimnis ist:**
/// ihre Adresse (samt Schema), ihren Namen im Heimnetz, ob der Mac vermittelt, und den Projektordner auf ihr.
///
/// Das Geheimnis für die Tür liegt **nicht** hier, sondern in `Schluesselbund.swift`. Eine
/// Probe (`AnfragenTests`) fällt, sobald eine Datei dieser Einheit, die `UserDefaults`
/// benutzt, es beim Namen nennt — die Lehre aus dem früheren Mac-Client (22.09.2026).
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
        get { Suche.gemerkt(UserDefaults.standard.string(forKey: adresseSchluessel)) }
        set { UserDefaults.standard.set(newValue?.absoluteString, forKey: adresseSchluessel) }
    }

    /// Ihr Name im Heimnetz (Bonjour) — `nil`, wenn die Adresse eingetippt wurde.
    static var name: String? {
        get { UserDefaults.standard.string(forKey: nameSchluessel) }
        set { UserDefaults.standard.set(newValue, forKey: nameSchluessel) }
    }

    /// Ob unterwegs der Mac vermittelt (TXT `vermittler=mac`, Protokoll §8b) — nur für die
    /// Anzeige «über den Mac».
    static var ueberDenMac: Bool {
        get { UserDefaults.standard.bool(forKey: macSchluessel) }
        set { UserDefaults.standard.set(newValue, forKey: macSchluessel) }
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
        UserDefaults.standard.removeObject(forKey: macSchluessel)
    }
}
