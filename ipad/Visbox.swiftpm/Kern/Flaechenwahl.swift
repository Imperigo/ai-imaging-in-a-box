import Foundation

/// Was die Mac-App nach «Schon anfangen» vom Heim-PC zeigt (Owner-Entscheid 85, 14.10.2026;
/// Blatt 19 der Entwurfsfläche).
///
/// **Zuerst die Knoten.** Bis dahin öffnete die App die Visbox-Seite, und der Knotenbaum lag
/// hinter deren Knopf «Knotenansicht». Owner: *«die Macversion ist vollständig KosmoVis-Werkzeug»*.
/// Beides kommt weiter vom Heim-PC — am Mac wird nichts nachgebaut; der Knotenbaum ist die
/// Kopie aus KosmoOrbit (E26) und wird dort weiterentwickelt.
///
/// * **A** — ein Schalter «Knoten | Visbox-Seite» oben in der Kopfleiste.
/// * **B** — welche Mappe die Knoten zeigen, entscheidet der Heim-PC: die zuletzt auf der
///   Visbox-Seite geöffnete, sonst die vom Start (`oberflaeche/server.py`).
/// * **C** — beim Öffnen **immer** zuerst die Knoten (`beimOeffnen`), nichts gemerkt.
public enum Flaechenwahl: String, CaseIterable, Sendable {
    case knoten
    case seite

    /// Entscheid 85 C: immer zuerst die Knoten.
    public static let beimOeffnen: Flaechenwahl = .knoten

    /// Die Beschriftung im Schalter.
    public var titel: String {
        switch self {
        case .knoten: return "Knoten"
        case .seite: return "\(Marke.name)-Seite"
        }
    }

    /// Der Pfad auf dem Heim-PC. Die Knotenansicht braucht den **Schrägstrich am Ende**: Sie
    /// lädt ihre Teile relativ (`./assets/…`), ohne ihn antwortet der Server mit einer
    /// Weiterleitung. Kein `Weg` aus `Wege`: Die Knotenansicht steht nicht in den Wegtafeln
    /// des Servers, sondern ist ein eigener Bereich (`WEG_KNOTEN`), bewacht von
    /// `tests/test_mac_knoten_zuerst.py`.
    public var pfad: String {
        switch self {
        case .knoten: return "/knoten/"
        case .seite: return Wege.seite.pfad
        }
    }

    /// Die Adresse auf dem eingerichteten Heim-PC, oder `nil`, wenn sich keine bauen lässt.
    public func adresse(basis: URL) -> URL? {
        Wege.adresse(Weg(pfad: pfad, methode: .get), basis: basis)
    }
}
