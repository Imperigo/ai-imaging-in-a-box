import Foundation

/// Was sich die Mac-App über den Heim-PC merkt — **nur, was kein Geheimnis ist:** seine
/// Adresse.
///
/// Das Geheimnis für die Tür liegt in `Heimschluesselbund.swift`. Die Adresse ist vor dem
/// Merken geprüft (`Heimadresse.pruefe` im Kern) — und dort auch darauf, dass kein Kennwort
/// in ihr steckt, denn was hier liegt, liegt in einer Datei.
enum Heimgedaechtnis {
    private static let adresseSchluessel = "heim.adresse"

    /// Wo der Heim-PC zu erreichen ist (`https://<rechner>.<netz>.ts.net:8443`).
    static var adresse: URL? {
        get { UserDefaults.standard.string(forKey: adresseSchluessel).flatMap(URL.init(string:)) }
        set { UserDefaults.standard.set(newValue?.absoluteString, forKey: adresseSchluessel) }
    }
}
