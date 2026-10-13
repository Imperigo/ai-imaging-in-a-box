import Foundation

/// Was sich die Mac-App über den Heim-PC merkt — **nur, was kein Geheimnis ist:** seine
/// Adresse und, im Heim-WLAN, den Fingerabdruck seines Zertifikats.
///
/// Das Geheimnis für die Tür liegt in `Heimschluesselbund.swift`. Die Adresse ist vor dem
/// Merken geprüft (`Heimadresse.pruefe` im Kern) — und dort auch darauf, dass kein Kennwort
/// in ihr steckt, denn was hier liegt, liegt in einer Datei.
///
/// **Der Fingerabdruck ist öffentlich** (Entscheid 83, 13.10.2026): Er steht in jedem
/// Handschlag des Heim-PC. Gemerkt wird er, damit der Mac im WLAN nur noch **dieses**
/// Zertifikat annimmt (`Heimvertrauen`) — er ist die Erinnerung, nicht der Schlüssel.
enum Heimgedaechtnis {
    private static let adresseSchluessel = "heim.adresse"
    private static let abdruckSchluessel = "heim.fingerabdruck"

    /// Wo der Heim-PC zu erreichen ist (`https://<rechner>.<netz>.ts.net:8443`, oder im
    /// Heim-WLAN `https://<adresse>:8732`).
    static var adresse: URL? {
        get { UserDefaults.standard.string(forKey: adresseSchluessel).flatMap(URL.init(string:)) }
        set { UserDefaults.standard.set(newValue?.absoluteString, forKey: adresseSchluessel) }
    }

    /// Der angeheftete Fingerabdruck — `nil` über Tailscale (dort prüft das System).
    static var fingerabdruck: String? {
        get { UserDefaults.standard.string(forKey: abdruckSchluessel) }
        set { UserDefaults.standard.set(newValue, forKey: abdruckSchluessel) }
    }
}
