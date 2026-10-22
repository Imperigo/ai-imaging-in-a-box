import Foundation

// WELCHE MAPPE DIE KNOTENANSICHT AM MAC ÖFFNET (Owner-Entscheid 129, 22.10.2026).
//
// Anlass (Mac-Befund 0.3.33, Protokoll 74 §231): Ohne Mappe am Mac las die Knotenansicht beim
// Öffnen die Mappe, die am Heim-PC **irgendein** Gerät zuletzt geöffnet hatte (Entscheid 85 B).
// Ein Probelauf am Heim-PC verstellte damit, was der Owner nach «Schon anfangen» sah.
//
// Seither gilt für den Mac (Heim-PC-Browser und iPad behalten 85 B):
//
//  * Die App **merkt sich** den Namen der Mappe, deren Graph die Knotenansicht zuletzt gelesen hat
//    (`mappe` in der Antwort von `GET /knoten/graph`, gelesen beim Weiterreichen).
//  * Beim Öffnen der Knotenansicht geht dieser Name als `?mappe=` mit; die Seite liest Mappe,
//    Modell, Graph, Skizzen und Standpunkte dann aus genau dieser.
//  * **Nicht** beim Zurückwechseln von der Visbox-Seite: Wer dort eine Mappe öffnet, will sie in den
//    Knoten sehen — dann gilt die zuletzt geöffnete, und die App merkt sich danach diese.
//  * **Nicht** mit offener Mappe am Mac: Die liest und sichert die App selbst.
//  * Gibt es die gemerkte Mappe am Heim-PC nicht mehr (404), vergisst die App sie — beim nächsten
//    Öffnen wieder wie 85 B.
//
// Hier steht nur die Regel, ohne WebKit und ohne `UserDefaults` — darum unter Linux mit Proben
// (`KnotenmappenwahlTests`).
public enum Knotenmappenwahl {
    /// Der Schlüssel in den App-Einstellungen.
    public static let einstellung = "knoten.heimMappe"
    /// Der Weg, dessen Antwort den Namen trägt.
    public static let graphWeg = "/knoten/graph"
    /// Höchstens so lang (wie `mappenpaket.KENNUNG_HOECHSTENS` am Heim-PC).
    public static let hoechstens = 200

    /// Ein blosser Ordnername: nicht leer, kein Pfad, kein Punkt am Anfang.
    public static func gueltig(_ name: String) -> Bool {
        let n = name.trimmingCharacters(in: .whitespaces)
        return !n.isEmpty && n == name && n.count <= hoechstens && !n.hasPrefix(".")
            && !n.contains("/") && !n.contains("\\") && !n.contains("\0")
    }

    /// Der Name aus der Antwort von `GET /knoten/graph` — `nil`, wenn keiner (oder kein gültiger).
    public static func mappe(ausGraphAntwort daten: Data) -> String? {
        guard let wert = try? JSONWert.lies(daten), let name = wert["mappe"]?.alsText,
              gueltig(name) else { return nil }
        return name
    }

    /// Was die App mit einer Antwort auf `GET /knoten/graph` tut.
    public enum Folge: Equatable, Sendable {
        case merke(String)
        case vergiss
        case nichts
    }

    /// 200 mit Namen: merken. 404 auf eine verlangte Mappe: vergessen. Sonst nichts.
    public static func folge(status: Int, daten: Data, verlangt: String?) -> Folge {
        if status == 200, let name = mappe(ausGraphAntwort: daten) { return .merke(name) }
        if status == 404, verlangt != nil { return .vergiss }
        return .nichts
    }

    /// Welche Mappe beim Laden der Knotenansicht verlangt wird — `nil`: keine (85 B).
    public static func beimLaden(gemerkt: String?, macMappeOffen: Bool, vonDerSeite: Bool) -> String? {
        guard !macMappeOffen, !vonDerSeite, let gemerkt, gueltig(gemerkt) else { return nil }
        return gemerkt
    }

    /// Der Einstieg der Knotenansicht, mit `?mappe=` wenn eine verlangt wird.
    public static func einstieg(mappe: String?) -> URL {
        let basis = Knotenwege.einstieg
        guard let mappe, gueltig(mappe),
              var teile = URLComponents(url: basis, resolvingAgainstBaseURL: false) else { return basis }
        teile.queryItems = [URLQueryItem(name: "mappe", value: mappe)]
        return teile.url ?? basis
    }

    /// Die verlangte Mappe aus einer Adresse der Seite (`?mappe=`) — `nil`: keine.
    public static func verlangt(in adresse: URL) -> String? {
        URLComponents(url: adresse, resolvingAgainstBaseURL: true)?
            .queryItems?.first { $0.name == "mappe" }?.value
    }
}
