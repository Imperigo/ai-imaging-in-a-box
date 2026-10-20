import Foundation

/// Was die Mac-App nach «Schon anfangen» vom Heim-PC zeigt (Owner-Entscheid 85, 14.10.2026;
/// Blatt 19 der Entwurfsfläche).
///
/// **Zuerst die Knoten.** Bis dahin öffnete die App die Visbox-Seite, und der Knotenbaum lag
/// hinter deren Knopf «Knotenansicht». Owner: *«die Macversion ist vollständig KosmoVis-Werkzeug»*.
/// Am Mac wird nichts nachgebaut; der Knotenbaum ist die Kopie aus KosmoOrbit (E26) und wird
/// dort weiterentwickelt. **Seit Schritt 1 von «Visbox eigenständig» (20.10.2026)** kommt er
/// aus dem App-Bündel, nicht mehr vom Heim-PC (`ausDemBuendel`, `Knotenwege`); die
/// Visbox-Seite kommt vorerst weiter vom Heim-PC.
///
/// * **A** — ein Schalter «Knoten | Visbox-Seite» oben in der Kopfleiste. **Ersetzt durch
///   Entscheid 94** (14.10.2026): Die Knoten sind DIE Arbeitsfläche zum Rendern; die Seite
///   öffnet nur noch das Menü «Darstellung», zurück führt «Zurück zu den Knoten».
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

    /// Ob die Fläche **aus dem App-Bündel** kommt («Visbox eigenständig», Schritt 1,
    /// 20.10.2026): die Knoten ja (eigenes Adressschema, `Knotenwege`), die Visbox-Seite
    /// vorerst nicht — ob sie überhaupt bleibt, entscheidet Schritt 5.
    public var ausDemBuendel: Bool {
        switch self {
        case .knoten: return true
        case .seite: return false
        }
    }

    /// Die Adresse, die das Webfenster lädt — die Knoten aus dem Bündel
    /// (`visbox://app/knoten/`, **auch ohne Heim-PC**), die Seite vom eingerichteten Heim-PC.
    /// `nil`, wenn die Seite gefragt ist und kein Heim-PC eingerichtet ist (oder sich aus seiner
    /// Adresse keine bauen lässt).
    ///
    /// `pfad` bleibt der Pfad **am Heim-PC**: Dort bedient der Server die Knoten weiter für den
    /// Browser, und die Datenwege der Knoten liegen unter ihm (`Knotenwege.datenwege`).
    public func adresse(basis: URL?) -> URL? {
        if ausDemBuendel { return Knotenwege.einstieg }
        guard let basis else { return nil }
        return Wege.adresse(Weg(pfad: pfad, methode: .get), basis: basis)
    }
}
