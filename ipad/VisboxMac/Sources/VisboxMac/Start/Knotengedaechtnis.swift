import Foundation
import VisboxKern

/// Was die Knotenansicht ueber das Neuladen hinaus behaelt (Plan UI-Gleichheit S4, 20.10.2026) — in
/// den App-Einstellungen, nur die Schluessel von `Knotenwirt.merkbar` (Thema, Akzent, Anzeige,
/// Rueckgaengig-Schalter). Das Webfenster hat keinen bleibenden Speicher; die `Heimflaeche` legt die
/// Werte vor dem ersten Bild zurueck (`Knotenwirt.merkSkript`).
///
/// Das Thema geht an seine eigene Einstellung (`Knotenwirt.Thema.einstellung`), die das
/// `Hauptfenster` liest und das Menue «Darstellung» schaltet — eine Wahrheit fuer beide Wege.
///
/// Eigene Datei, weil die `Arbeitsansicht` sich nichts merkt (Entscheid 85 C).
enum Knotengedaechtnis {
    static var werte: [String: String] {
        (UserDefaults.standard.dictionary(forKey: Knotenwirt.merkEinstellung) as? [String: String]) ?? [:]
    }

    static func merke(_ schluessel: String, _ wert: String) {
        guard Knotenwirt.merkbar.contains(schluessel) else { return }
        if schluessel == "kosmo.thema" {
            UserDefaults.standard.set(Knotenwirt.Thema(gemerkt: wert).rawValue,
                                      forKey: Knotenwirt.Thema.einstellung)
            return
        }
        var alle = werte
        guard alle[schluessel] != wert else { return }
        alle[schluessel] = wert
        UserDefaults.standard.set(alle, forKey: Knotenwirt.merkEinstellung)
    }
}
