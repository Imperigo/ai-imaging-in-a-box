import Foundation

/// Welche Mappe am Mac offen ist — der Ordnername, gemerkt in den App-Einstellungen («Visbox
/// eigenständig», Schritt 3, 21.10.2026). Eigene Datei, weil hier nur dieser eine Name liegt und
/// nie etwas zur Leitung (die Probe `tests/test_ipad_geruest.py` hält das fest).
enum Mappengedaechtnis {
    static let schluessel = "mappe.offen"

    static var offen: String? {
        get { UserDefaults.standard.string(forKey: schluessel) }
        set { UserDefaults.standard.set(newValue, forKey: schluessel) }
    }
}
