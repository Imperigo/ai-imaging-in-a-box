import Foundation

// ============================================================================ Knotenwege
//
// DIE KNOTENANSICHT AUS DEM APP-BUENDEL («Visbox eigenstaendig», Schritt 1, 20.10.2026).
//
// Bis dahin lud die Mac-App die Knotenansicht vom Heim-PC (`https://…/knoten/`). Seither liegt
// ihr Bau im Buendel (`Contents/Resources/Knoten/`), und die App bedient das Webfenster ueber
// ein EIGENES ADRESSSCHEMA: `visbox://app/knoten/…`. Die Seite merkt davon nichts — sie spricht
// weiter relativ (`./mappe`, `./graph`, `./modell.glb`, `./skizze`, `./modell-laden`) und die
// Bruecke unter `/bruecke`. Die App entscheidet je Anfrage, wohin sie geht:
//
// * **Datei** — ein Teil des Baus (`index.html`, `assets/…`, `fonts/…`): aus dem Buendel.
// * **Heim** — ein Datenweg: wird per `URLSession` an den Heim-PC weitergereicht, mit der
//   Anmeldung der App; die Antwort kommt unveraendert zurueck (Status, Typ, Rumpf).
// * **Umleitung** — `/knoten` ohne Schraegstrich, wie am Server.
// * **Unbekannt** — alles andere: 404 mit Satz, nie still an den Heim-PC.
//
// WARUM `visbox://app/knoten/` UND NICHT `visbox://knoten/`: Mit dem Pfad `/knoten/` sieht
// die Seite dieselbe Adresse wie am Heim-PC (`aufDemVisboxServer` in `mappe.ts`), und jeder
// relative Datenweg landet auf DEMSELBEN Pfad wie drueben (`/knoten/mappe`). Die Weiterleitung
// ist damit eine reine Abbildung «gleicher Pfad, andere Basis» — kein Umschreiben.
//
// Hier steht nur die REINE Regel, unter Linux mit Proben (`KnotenwegeTests`); die Mac-App
// (`Start/Knotenquelle.swift`) liest nur noch Dateien und fuehrt die Anfrage aus.

/// Wohin eine Anfrage der Knotenansicht geht.
public enum Knotenziel: Equatable, Sendable {
    /// Eine Datei des Baus — `pfad` relativ zum Ordner `Knoten` im Buendel, `typ` der
    /// Inhaltstyp (wie `KNOTEN_TYPEN` am Server).
    case datei(pfad: String, typ: String)
    /// Ein Datenweg am Heim-PC — derselbe Pfad wie in der Seite, die Frage unveraendert.
    case heim(pfad: String)
    /// Mit Schraegstrich noch einmal (`/knoten` → `/knoten/`).
    case umleitung(ziel: String)
    /// Gibt es nicht — mit Satz.
    case unbekannt(satz: String)
}

public enum Knotenwege {
    /// Das eigene Adressschema: der Name der Marke, klein (`Marke.name` — der Name steht nur
    /// dort). WebKit nimmt nur ein Schema an, das es nicht selbst bedient (`http`, `https`,
    /// `file`, `about` … sind vergeben). Die Seite kennt es als `EIGENES_SCHEMA` (`mappe.ts`,
    /// bewacht in `tests/test_mac_knotenansicht_buendel.py`).
    public static let schema = Marke.name.lowercased()
    /// Der Rechnername im Schema. Fest: Er traegt nichts, ausser dass die Seite einen
    /// Ursprung hat (`visbox://app`) — ohne ihn behandelte WebKit die Adresse als ursprungslos.
    public static let rechner = "app"
    /// Der Bereich der Knotenansicht — **derselbe Pfad wie am Heim-PC** (`WEG_KNOTEN`).
    public static let bereich = "/knoten"
    /// Der Bereich der Bruecke — derselbe wie am Heim-PC (`WEG_BRUECKE`).
    public static let bruecke = "/bruecke"
    /// Der Ordner des Baus im Buendel (`Contents/Resources/Knoten`, `ipad.yml`).
    public static let ordnerImBuendel = "Knoten"

    /// Die Datenwege unter `/knoten/`, die der Heim-PC bedient — **abgeschrieben und bewacht**
    /// (`tests/test_mac_knotenansicht_buendel.py` gegen `WEG_KNOTEN_*` in `server.py`). Alles
    /// andere unter `/knoten/` ist eine Datei des Baus.
    public static let datenwege: Set<String> = [
        "/knoten/mappe", "/knoten/graph", "/knoten/modell.glb", "/knoten/skizze",
        "/knoten/modell-laden", "/knoten/standpunkte",
        // Schritt 3 (21.10.2026): «An den Mac holen» — die App ruft sie selbst (`Mappenablage`).
        "/knoten/mappen", "/knoten/mappe-paket", "/knoten/mappe-datei",
    ]

    /// Was der Bau enthaelt, mit dem Typ, den WebKit braucht — **dieselbe Liste wie am
    /// Heim-PC** (`KNOTEN_TYPEN`, bewacht). Alles andere wird nicht ausgeliefert. Ein Modul-
    /// Skript ohne `text/javascript` fuehrt WebKit nicht aus.
    public static let typen: [String: String] = [
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".woff2": "font/woff2",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".txt": "text/plain; charset=utf-8",
        ".md": "text/plain; charset=utf-8",
    ]

    /// Die Adresse, mit der das Webfenster die Knotenansicht oeffnet.
    public static var einstieg: URL {
        // Fest gebaut und darum nie `nil`; `URLComponents` statt Zeichenkette, damit kein
        // Ausrufezeichen auf einer Zeichenkette steht.
        var teile = URLComponents()
        teile.scheme = schema
        teile.host = rechner
        teile.path = bereich + "/"
        return teile.url ?? URL(fileURLWithPath: "/")
    }

    /// Ob eine Adresse zum eigenen Schema **und** zum festen Rechner gehoert.
    public static func istEigen(_ adresse: URL) -> Bool {
        adresse.scheme?.lowercased() == schema && adresse.host?.lowercased() == rechner
    }

    /// Wohin eine Anfrage an das eigene Schema geht — der Pfad **aus `URLComponents`**, nicht
    /// aus `URL.path`: Jener streicht den Schraegstrich am Ende, und `visbox://app/knoten/`
    /// hiesse dann `/knoten` — eine Umleitung auf sich selbst, ohne Ende.
    public static func ziel(adresse: URL) -> Knotenziel {
        guard istEigen(adresse),
              let teile = URLComponents(url: adresse, resolvingAgainstBaseURL: true) else {
            return .unbekannt(satz: "Unbekannter Weg: \(adresse.absoluteString)")
        }
        return ziel(pfad: teile.path.isEmpty ? "/" : teile.path)
    }

    /// Die schon kodierte Frage einer Adresse (`?ordner=…`), unveraendert fuer den Heim-PC.
    public static func kodierteFrage(_ adresse: URL) -> String? {
        URLComponents(url: adresse, resolvingAgainstBaseURL: true)?.percentEncodedQuery
    }

    /// Wohin der Pfad einer Anfrage geht. `pfad` ist der **entschluesselte** Pfad der Adresse
    /// (`URL.path`), ohne Frage.
    public static func ziel(pfad: String) -> Knotenziel {
        if pfad == bruecke || pfad.hasPrefix(bruecke + "/") {
            return .heim(pfad: pfad)
        }
        if pfad == bereich {
            // Die Seite laedt ihre Teile relativ (`./assets/…`); ohne den Schraegstrich suchte
            // WebKit sie eine Ebene zu hoch — dieselbe Regel wie am Server.
            return .umleitung(ziel: bereich + "/")
        }
        guard pfad.hasPrefix(bereich + "/") else {
            return .unbekannt(satz: "Unbekannter Weg: \(pfad)")
        }
        if datenwege.contains(pfad) {
            return .heim(pfad: pfad)
        }
        var rest = String(pfad.dropFirst(bereich.count + 1))
        if rest.isEmpty { rest = "index.html" }
        guard let sauber = sichererTeilpfad(rest) else {
            return .unbekannt(satz: "Unbekannter Weg: \(pfad)")
        }
        guard let typ = typ(fuer: sauber) else {
            return .unbekannt(satz: "Unbekannter Weg: \(pfad)")
        }
        return .datei(pfad: sauber, typ: typ)
    }

    /// Der Inhaltstyp nach der Endung, oder `nil`, wenn der Bau so etwas nicht ausliefert.
    public static func typ(fuer pfad: String) -> String? {
        guard let punkt = pfad.lastIndex(of: "."),
              !pfad[punkt...].contains("/") else { return nil }
        return typen[pfad[punkt...].lowercased()]
    }

    /// Ein Teilpfad, der **im Ordner des Baus bleibt** — oder `nil`. Kein `..`, kein `.`, kein
    /// leeres Glied (`a//b`), kein Rueckstrich, kein Nullzeichen: Ein Pfad, der hinausfuehrt,
    /// laese sonst eine beliebige Datei des Programms (oder des Mac) in die Seite.
    public static func sichererTeilpfad(_ rest: String) -> String? {
        if rest.contains("\\") || rest.contains("\0") { return nil }
        let glieder = rest.split(separator: "/", omittingEmptySubsequences: false)
        for glied in glieder where glied.isEmpty || glied == "." || glied == ".." {
            return nil
        }
        return rest
    }

    // ------------------------------------------------------------- an den Heim-PC

    /// Die Adresse am Heim-PC fuer einen Datenweg: **gleicher Pfad, andere Basis**, die Frage
    /// unveraendert (schon kodiert, `URL.query` bzw. `percentEncodedQuery`). Ein Pfad der Basis
    /// (`https://heim.example:8443/visbox`) bleibt davor stehen.
    public static func heimAdresse(pfad: String, kodierteFrage: String?, basis: URL) -> URL? {
        guard var teile = URLComponents(url: basis, resolvingAgainstBaseURL: false),
              let schema = teile.scheme?.lowercased(), schema == "https" || schema == "http"
        else { return nil }
        var vorne = teile.path
        while vorne.hasSuffix("/") { vorne.removeLast() }
        teile.path = vorne + pfad
        teile.percentEncodedQuery = (kodierteFrage?.isEmpty ?? true) ? nil : kodierteFrage
        teile.fragment = nil
        return teile.url
    }

    /// Welche Koepfe der Seite mit hinausgehen — **nur diese**. Alles andere (Kekse, `Origin`,
    /// `Referer`, eine eigene `Authorization`) bleibt in der App: Der Heim-PC bekommt die
    /// Anmeldung der App, nicht was die Seite meint.
    public static let koepfeHinaus: Set<String> = ["content-type", "accept", "x-kosmo-token"]

    /// Welche Koepfe der Antwort an die Seite zurueckgehen. **Nicht** `Content-Length` und
    /// `Content-Encoding`: `URLSession` packt eine gepackte Antwort schon aus, die Laenge
    /// stimmte dann nicht mehr. **Nicht** `Set-Cookie` und `WWW-Authenticate`: Die Seite soll
    /// weder Kekse noch eine Anmeldung sehen.
    public static let koepfeZurueck: Set<String> = [
        "content-type", "content-disposition", "retry-after", "etag", "last-modified",
    ]

    /// Die Koepfe der weitergereichten Anfrage: die erlaubten der Seite, dazu die Anmeldung
    /// der App und `X-Geraet: mac`.
    public static func koepfeFuerHeim(seite: [Kopfzeile], anmeldung: Anmeldung?,
                                      geraet: Geraeteart? = .mac) -> [Kopfzeile] {
        var aus: [Kopfzeile] = seite.filter { koepfeHinaus.contains($0.name.lowercased()) }
        if let anmeldung {
            aus.append(Kopfzeile("Authorization", anmeldung.kopfzeile))
        }
        if let geraet {
            aus.append(Kopfzeile(Geraeteart.kopf, geraet.rawValue))
        }
        return aus
    }

    /// Die Koepfe der Antwort an die Seite: die erlaubten des Heim-PC, dazu **immer**
    /// `Cache-Control: no-store` — eine Mappe aendert sich, ein gemerkter Stand saehe aus wie
    /// der aktuelle.
    public static func koepfeFuerSeite(heim: [Kopfzeile]) -> [Kopfzeile] {
        var aus = heim.filter { koepfeZurueck.contains($0.name.lowercased()) }
        aus.append(Kopfzeile("Cache-Control", "no-store"))
        return aus
    }

    /// Die Koepfe einer Datei aus dem Buendel.
    public static func koepfeFuerDatei(typ: String, laenge: Int) -> [Kopfzeile] {
        [Kopfzeile("Content-Type", typ), Kopfzeile("Content-Length", String(laenge)),
         Kopfzeile("Cache-Control", "no-store")]
    }

    // ------------------------------------------------------------- wie lange gewartet wird

    /// Wie lange ein Datenweg auf das erste Byte des Heim-PC wartet — gleich wie die
    /// Vermittlung (`Heimstrecke.wartezeit`), damit «nicht erreicht» vor der Zeitgrenze der
    /// Bruecke in der Seite (30 s) kommt.
    public static let wartezeitKurz: TimeInterval = 25
    /// Fuer die zwei Wege, die ein Modell **hochladen** und erst danach antworten koennen:
    /// `POST /bruecke/jobs` und `POST /knoten/modell-laden` (20.10.2026). Bis dahin galten
    /// auch hier 25 s, und eine Variante mit grossem Modell endete in «Der Heim-PC ist nicht
    /// erreicht: Er hat nicht rechtzeitig geantwortet.», obwohl er arbeitete. Unter der
    /// ganzen Frist von `hoechstensGanz` (600 s), damit eine haengende Leitung trotzdem endet.
    public static let wartezeitLang: TimeInterval = 300
    /// Hoechstens so lange fuer eine ganze Antwort (`timeoutIntervalForResource`).
    public static let hoechstensGanz: TimeInterval = 600

    /// Welche Wartezeit gilt fuer diese Anfrage? **Lang nur fuer POST auf die zwei Wege mit
    /// Modell**, alles andere kurz — ein Abruf, der haengt, soll weiter schnell «nicht
    /// erreicht» sagen.
    public static func wartezeit(methode: String, pfad: String) -> TimeInterval {
        guard methode.uppercased() == "POST" else { return wartezeitKurz }
        let ohneSchraegstrich = pfad.hasSuffix("/") ? String(pfad.dropLast()) : pfad
        return wegeMitModell.contains(ohneSchraegstrich) ? wartezeitLang : wartezeitKurz
    }

    /// Die Wege, die ein Modell hochladen — **abgeschrieben und bewacht**
    /// (`tests/test_mac_knotenansicht_buendel.py` gegen `WEG_BRUECKE`/`WEG_KNOTEN_MODELL_LADEN`).
    public static let wegeMitModell: Set<String> = ["/bruecke/jobs", "/knoten/modell-laden"]

    // ------------------------------------------------------------- Fehler als Satz

    /// Kein Heim-PC eingerichtet: Die Knotenansicht laedt, ihre Datenwege antworten sofort
    /// mit diesem Satz — **statt zu haengen**.
    public static let satzOhneHeim =
        "Kein Heim-PC eingerichtet — Mappe und Rechnen gehen erst, wenn er gekoppelt ist."

    /// Der Rumpf einer Fehlerantwort, in der Form des Servers (`{"fehler": satz}`), damit die
    /// Seite ihn so zeigt wie jeden Satz des Heim-PC (`fehlerSatz` in `mappe.ts`).
    public static func fehlerRumpf(_ satz: String) -> Data {
        let feld = (try? JSONSerialization.data(withJSONObject: ["fehler": satz],
                                                options: [.sortedKeys])) ?? Data()
        return feld
    }

    /// Status einer Fehlerantwort: 503 ohne Heim-PC, 502 wenn er nicht antwortete, 404 fuer
    /// einen unbekannten Weg.
    public enum Fehlerart: Int, Sendable {
        case unbekannt = 404
        case heimNichtErreicht = 502
        case ohneHeim = 503
    }
}
