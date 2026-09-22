import Foundation

/// Wie ein Weg angefragt wird.
public enum Methode: String, Sendable {
    case get = "GET"
    case post = "POST"
}

/// Ein Weg des Servers auf der HomeStation — Pfad und Methode gehören zusammen.
///
/// **Warum nicht bloss der Pfad.** `GET /api/verbinden` gibt es nicht, `POST` schon; ein
/// Pfad ohne seine Methode ist die halbe Auskunft, und die fehlende Hälfte fällt erst
/// als 404 am Gerät auf.
public struct Weg: Hashable, Sendable {
    public let pfad: String
    public let methode: Methode
    /// Ob der Weg **ohne Anmeldung** erreichbar ist. Zwei sind es — das Verbinden und die
    /// Koppelseite für den Browser —, und beide nur, solange an der HomeStation eine
    /// Kopplung offen ist.
    public let ohneAnmeldung: Bool

    public init(pfad: String, methode: Methode, ohneAnmeldung: Bool = false) {
        self.pfad = pfad
        self.methode = methode
        self.ohneAnmeldung = ohneAnmeldung
    }
}

/// Die Wege von `oberflaeche/server.py`, **abgeschrieben und bewacht.**
///
/// Abgeschrieben, weil die App den Python-Server nicht lesen kann. Bewacht, weil eine
/// Abschrift veraltet, ohne dass es jemand merkt: `tests/test_ipad_geruest.py` vergleicht
/// diese Liste mit den Wegtafeln, die der Server **wirklich** bedient (`WEGTAFEL`,
/// `WEGTAFEL_LESEN`), und fällt, sobald eine Seite einen Weg hat, den die andere nicht
/// kennt.
///
/// Was hinter jedem Weg an Feldern hin- und zurückgeht, steht in
/// `docs/VISBOX_PROTOKOLL.md`.
public enum Wege {
    // ------------------------------------------------------------------ lesen (GET)

    /// Die Webseite der HomeStation. Die App braucht sie nicht; sie steht hier, weil der
    /// Server sie bedient und die Liste vollständig sein soll.
    public static let seite = Weg(pfad: "/", methode: .get)
    /// Dieselbe Seite unter ihrem zweiten Namen.
    public static let seiteLang = Weg(pfad: "/index.html", methode: .get)
    /// Alles über ein Projekt in einem Stück. Frage: `ordner` (freiwillig).
    public static let projekt = Weg(pfad: "/api/projekt", methode: .get)
    /// Der Stand des laufenden Auftrags.
    public static let fortschritt = Weg(pfad: "/api/fortschritt", methode: .get)
    /// Ein Bild aus dem Projektordner. Frage: `ordner` (freiwillig), `name`.
    public static let bild = Weg(pfad: "/bild", methode: .get)
    /// Die Koppelseite für einen **Browser** (Entscheid 26): ein Zahlenfeld, das
    /// `verbinden` ruft. Die App braucht sie nicht — sie ruft `verbinden` selbst. Ohne
    /// Anmeldung erreichbar, und nur, solange drüben eine Zahl gilt.
    public static let koppeln = Weg(pfad: "/koppeln", methode: .get, ohneAnmeldung: true)

    // ---------------------------------------------------------------- handeln (POST)

    public static let anlegen = Weg(pfad: "/api/anlegen", methode: .post)
    public static let einstellungen = Weg(pfad: "/api/einstellungen", methode: .post)
    public static let skizze = Weg(pfad: "/api/skizze", methode: .post)
    public static let rechne = Weg(pfad: "/api/rechne", methode: .post)
    /// Das erste Verbinden: sechsstellige Zahl gegen Kennwort.
    public static let verbinden = Weg(pfad: "/api/verbinden", methode: .post,
                                      ohneAnmeldung: true)
    /// Einen eigenen Namen geben (Entscheid 19): `bild` oder `skizze`, `titel` (Pflicht;
    /// `null` nimmt ihn zurück), `von_stand` (freiwillig).
    public static let benennen = Weg(pfad: "/api/benennen", methode: .post)
    /// Den laufenden Lauf anhalten (Entscheid 31) — zwischen zwei Knoten.
    public static let abbrechen = Weg(pfad: "/api/abbrechen", methode: .post)
    /// Eine abgelegte Skizze rechnen lassen: `skizze` (Name oder Liste für Ebenen),
    /// `anweisung`, `entwurf` (freiwillig).
    public static let rechneSkizze = Weg(pfad: "/api/rechne-skizze", methode: .post)

    /// Alle Wege, die der Server heute bedient.
    public static let alle: [Weg] = [
        seite, seiteLang, projekt, fortschritt, bild, koppeln,
        anlegen, einstellungen, skizze, rechne, verbinden,
        benennen, abbrechen, rechneSkizze,
    ]

    /// Die Adresse für einen Weg auf einer HomeStation — oder `nil`, wenn sich aus
    /// `basis` keine bauen lässt.
    ///
    /// Die Frage wird **kodiert**, nicht angehängt: Ein Bildname mit Leerzeichen oder `&`
    /// gäbe sonst eine Adresse, die auf ein anderes Bild zeigt oder auf keines.
    public static func adresse(_ weg: Weg, basis: URL,
                               frage: [(String, String)] = []) -> URL? {
        guard var teile = URLComponents(url: basis, resolvingAgainstBaseURL: false) else {
            return nil
        }
        teile.path = weg.pfad
        teile.queryItems = frage.isEmpty ? nil : frage.map { URLQueryItem(name: $0.0, value: $0.1) }
        // `+` STEHT IN EINER FRAGE FUER EIN LEERZEICHEN (so liest `parse_qs` des Servers
        // sie). `URLComponents` laesst es stehen — ein Bild namens «a+b.png» kaeme
        // drueben als «a b.png» an. Darum wird es hier ausdruecklich kodiert.
        teile.percentEncodedQuery = teile.percentEncodedQuery?
            .replacingOccurrences(of: "+", with: "%2B")
        return teile.url
    }
}
