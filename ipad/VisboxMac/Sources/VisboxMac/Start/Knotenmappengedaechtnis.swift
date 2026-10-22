import Foundation
import VisboxKern

/// Welche Mappe des Heim-PC die Knotenansicht am Mac zuletzt gelesen hat (Owner-Entscheid 129,
/// 22.10.2026) — der Ordnername, gemerkt in den App-Einstellungen. Die Regel steht im Kern
/// (`Knotenmappenwahl`, mit Proben); hier nur das Merken. Eigene Datei, weil hier nur dieser eine
/// Name liegt und nie etwas zur Leitung.
enum Knotenmappengedaechtnis {
    static var gemerkt: String? {
        UserDefaults.standard.string(forKey: Knotenmappenwahl.einstellung)
    }

    /// Was die Antwort auf `GET /knoten/graph` sagt: merken, vergessen oder nichts.
    static func nimm(_ folge: Knotenmappenwahl.Folge) {
        switch folge {
        case .merke(let name):
            UserDefaults.standard.set(name, forKey: Knotenmappenwahl.einstellung)
        case .vergiss:
            UserDefaults.standard.removeObject(forKey: Knotenmappenwahl.einstellung)
        case .nichts:
            break
        }
    }
}
