import Foundation

// DIE LEITUNG IN BYTES — eine HTTP-Anfrage lesen, eine HTTP-Antwort schreiben.
//
// Gebraucht vom Mac, der sich dem iPad gegenueber als Server ausgibt und dessen Anfragen an
// den Heim-PC weiterreicht (Entscheide 42/47, Protokoll §8b). Der Mac bekommt die Bytes aus
// `NWConnection`; was sie heissen, steht hier — im Kern, nur Foundation, darum unter Linux
// pruefbar (Regel 4). Der Mac-Teil liest und schreibt nur noch.
//
// BEWUSST SCHLICHT. Gelesen wird genau die Form, die die App (`URLSession`) und ein Browser
// schicken: eine Anfragezeile, Koepfe, ein Rumpf nach `Content-Length`. Kein Stueckeln
// (`Transfer-Encoding: chunked`), keine zweite Anfrage auf derselben Verbindung: Nach jeder
// Antwort schliesst der Mac, wie der Server auf dem Heim-PC (Protokoll §1). *Ein Leser, der
// alles kann, was HTTP erlaubt, ist ein Leser, in dem sich etwas verstecken laesst.*

/// Eine Kopfzeile, wie sie kam — Name in seiner Schreibweise, Wert ohne Leerraum am Rand.
///
/// Eine Liste statt eines Wörterbuchs: Derselbe Kopf darf zweimal kommen, und ein
/// Wörterbuch verschluckte den zweiten still.
public struct Kopfzeile: Equatable, Hashable, Sendable {
    public let name: String
    public let wert: String

    public init(_ name: String, _ wert: String) {
        self.name = name
        self.wert = wert
    }
}

extension Array where Element == Kopfzeile {
    /// Der erste Wert unter diesem Namen, **ohne Rücksicht auf Gross- und Kleinschreibung**
    /// (HTTP-Köpfe kennen sie nicht).
    public func wert(_ name: String) -> String? {
        first { $0.name.lowercased() == name.lowercased() }?.wert
    }

    /// Alle Werte unter diesem Namen.
    public func werte(_ name: String) -> [String] {
        filter { $0.name.lowercased() == name.lowercased() }.map(\.wert)
    }
}

/// Anfragezeile und Köpfe — was feststeht, **bevor** der Rumpf gelesen ist.
///
/// Eigens, damit die Tür entscheiden kann, ohne den Rumpf abzuwarten: Wer nicht angemeldet
/// ist, bekommt seine 401, bevor er vier Megabyte geschickt hat (`Vermittlungsregel.vorab`).
public struct Anfragekopf: Equatable, Sendable {
    /// `GET`, `POST`, … — wie geschickt, gross geschrieben.
    public let methode: String
    /// Pfad samt Frage, wie geschickt (`/bild?name=a%2Bb.png`). Immer mit `/` vorn.
    public let ziel: String
    /// `HTTP/1.0` oder `HTTP/1.1`.
    public let fassung: String
    public let koepfe: [Kopfzeile]

    public init(methode: String, ziel: String, fassung: String = "HTTP/1.1",
                koepfe: [Kopfzeile] = []) {
        self.methode = methode
        self.ziel = ziel
        self.fassung = fassung
        self.koepfe = koepfe
    }

    /// Der Pfad ohne Frage, **wörtlich** — ohne Dekodieren und ohne `;…` abzutrennen.
    /// `urlparse(...).path` des Servers trennt `;…` ab; darum geht nur weiter, was wörtlich
    /// auf der Positivliste steht (`Vermittlungsregel.weiterreichbar`), und dort steht
    /// kein `;`.
    public var pfad: String {
        if let frage = ziel.firstIndex(of: "?") { return String(ziel[..<frage]) }
        return ziel
    }

    /// Wie lang der Rumpf wird, nach `Content-Length` — 0, wenn keine Länge steht. Der
    /// Leser hat sie schon geprüft (eine Zahl, höchstens `Anfrageleser.rumpfGrenze`).
    public var laenge: Int {
        Int(koepfe.wert("Content-Length") ?? "") ?? 0
    }
}

/// Eine ganz gelesene Anfrage.
public struct RoheAnfrage: Equatable, Sendable {
    public let kopf: Anfragekopf
    public let rumpf: Data

    public init(kopf: Anfragekopf, rumpf: Data = Data()) {
        self.kopf = kopf
        self.rumpf = rumpf
    }
}

/// Eine Antwort, wie sie über die Leitung geht.
public struct Leitungsantwort: Equatable, Sendable {
    public let status: Int
    /// Ohne `Content-Length` und `Connection` — die setzt `bytes()` selbst.
    public let koepfe: [Kopfzeile]
    public let rumpf: Data

    public init(status: Int, koepfe: [Kopfzeile] = [], rumpf: Data = Data()) {
        self.status = status
        self.koepfe = koepfe
        self.rumpf = rumpf
    }

    /// Ein Fehlschlag in der Form des Servers: `{"fehler": "<Satz>"}` (Protokoll §1).
    public static func fehler(_ satz: String, status: Int,
                              koepfe: [Kopfzeile] = []) -> Leitungsantwort {
        json(.objekt(["fehler": .text(satz)]), status: status, koepfe: koepfe)
    }

    /// Ein JSON-Rumpf in UTF-8, mit dem Inhaltstyp des Servers.
    public static func json(_ wert: JSONWert, status: Int = 200,
                            koepfe: [Kopfzeile] = []) -> Leitungsantwort {
        // `daten()` WIRFT NUR BEI `nan`/`inf` — die kommen in keiner Antwort dieses Kerns
        // vor. Fiele es doch, ginge ein leerer Rumpf mit dem Code hinaus, nicht ein falscher.
        let roh = (try? wert.daten()) ?? Data()
        return Leitungsantwort(
            status: status,
            koepfe: [Kopfzeile("Content-Type", "application/json; charset=utf-8")] + koepfe,
            rumpf: roh)
    }

    /// Die Antwort als Bytes. **Der Mac schliesst danach** (`Connection: close`), wie der
    /// Server auf dem Heim-PC nach jeder Antwort (Protokoll §1); die Länge steht immer da.
    public func bytes() -> Data {
        var kopf = "HTTP/1.1 \(status) \(Leitungsantwort.grund(status))\r\n"
        for k in koepfe where !Leitungsantwort.selbstGesetzt(k.name) {
            kopf += "\(k.name): \(k.wert)\r\n"
        }
        kopf += "Content-Length: \(rumpf.count)\r\n"
        kopf += "Connection: close\r\n\r\n"
        var aus = Data(kopf.utf8)
        aus.append(rumpf)
        return aus
    }

    private static func selbstGesetzt(_ name: String) -> Bool {
        ["content-length", "connection", "transfer-encoding"].contains(name.lowercased())
    }

    /// Der Text zur Zahl in der Statuszeile. Er trägt nichts — gelesen wird die Zahl —,
    /// aber eine Statuszeile ohne ihn ist für manche Leser keine.
    static func grund(_ status: Int) -> String {
        switch status {
        case 100: return "Continue"
        case 200: return "OK"
        case 204: return "No Content"
        case 301: return "Moved Permanently"
        case 302: return "Found"
        case 304: return "Not Modified"
        case 400: return "Bad Request"
        case 401: return "Unauthorized"
        case 403: return "Forbidden"
        case 404: return "Not Found"
        case 405: return "Method Not Allowed"
        case 411: return "Length Required"
        case 413: return "Payload Too Large"
        case 431: return "Request Header Fields Too Large"
        case 500: return "Internal Server Error"
        case 501: return "Not Implemented"
        case 502: return "Bad Gateway"
        case 505: return "HTTP Version Not Supported"
        default: return "Status"
        }
    }
}

/// Wie weit das Lesen einer Anfrage ist.
public enum Lesestand: Equatable, Sendable {
    /// Noch nicht ganz da — weiterlesen.
    case mehr
    /// Ganz gelesen.
    case fertig(RoheAnfrage)
    /// So nicht lesbar — **diese Antwort geht hinaus, und die Verbindung wird geschlossen.**
    /// Was danach noch kommt, wird nicht mehr gelesen.
    case kaputt(Leitungsantwort)
}

/// Liest **eine** Anfrage aus Bytes, die in beliebigen Stücken kommen.
///
/// Die Stücke kommen, wie das Netz sie schneidet: Ein Kopf kann über drei Stücke gehen, ein
/// Rumpf über hundert. Der Leser sammelt, bis die Anfrage ganz ist (`fertig`), und sagt
/// sonst `mehr` — oder `kaputt`, sobald feststeht, dass es nichts wird.
public struct Anfrageleser: Sendable {

    /// **Wie gross ein Rumpf höchstens sein darf: 4 MiB.**
    ///
    /// Die grösste Anfrage der App ist eine Skizze (`POST /api/skizze`). Der Server nimmt
    /// höchstens **2 MiB** PNG (`SKIZZE_GROESSENRIEGEL` in `server.py`); als Base64 im JSON
    /// werden daraus 4/3 davon, also **2,67 MiB**, dazu die übrigen Felder (Bemerkung,
    /// Name, Ordner, Schlüssel — wenige Kilobyte). 4 MiB lässt dafür einen Drittel Luft und
    /// ist klein genug, dass ein Fremder im WLAN den Mac nicht mit einem Film füllt.
    ///
    /// **Was nicht durchgeht, und es ist gewollt:** der Auftrag der Knotenansicht mit einem
    /// ganzen Modell (`/bruecke/jobs`, bis 768 MB) — der gehört dem Browser am Heim-PC, nicht
    /// dem iPad unterwegs. Eine Skizze, die der Server ablehnte (über 2 MiB PNG), lehnt
    /// hier niemand ab: Sie geht weiter, und der Server sagt seinen eigenen Satz.
    public static let rumpfGrenze = 4 * 1024 * 1024

    /// Wie gross Anfragezeile und Köpfe zusammen höchstens sein dürfen. Die App schickt
    /// wenige hundert Bytes; 32 KiB fasst jeden Browser und keinen Unfug.
    public static let kopfGrenze = 32 * 1024

    private var puffer = Data()
    /// Bis wohin der Puffer schon nach dem Kopfende abgesucht ist — die Suche setzt hier fort
    /// (drei Bytes davor), statt bei jedem Stück von vorn zu beginnen.
    private var gesucht = 0
    /// Der gelesene Kopf und wie lang der Rumpf wird — sobald der Kopf ganz ist.
    public private(set) var kopf: Anfragekopf?
    private var rumpfLaenge = 0
    private var rumpfAnfang = 0
    private var fortsetzungGesagt = false
    private var ende: Lesestand?

    public init() {}

    /// Nimmt das nächste Stück. Nach `fertig` oder `kaputt` ändert kein Stück mehr etwas.
    public mutating func nimm(_ stueck: Data) -> Lesestand {
        if let ende { return ende }
        puffer.append(stueck)
        if kopf == nil {
            // DREI BYTES ZURUECK: Ein `\r\n\r\n` kann ueber die Grenze zweier Stuecke reichen.
            let ab = max(0, gesucht - 3)
            gesucht = puffer.count
            guard let grenze = Anfrageleser.kopfende(puffer, ab: ab) else {
                // NOCH KEIN KOPFENDE — aber schon mehr, als ein Kopf sein darf. Nicht weiter
                // sammeln: Wer 32 KiB ohne Leerzeile schickt, schickt keinen Kopf.
                if puffer.count > Anfrageleser.kopfGrenze {
                    return beende(.kaputt(.fehler(
                        "Die Köpfe der Anfrage sind zu gross (mehr als "
                            + "\(Anfrageleser.kopfGrenze / 1024) KiB).", status: 431)))
                }
                return .mehr
            }
            guard grenze.kopfLaenge <= Anfrageleser.kopfGrenze else {
                return beende(.kaputt(.fehler(
                    "Die Köpfe der Anfrage sind zu gross (mehr als "
                        + "\(Anfrageleser.kopfGrenze / 1024) KiB).", status: 431)))
            }
            switch Anfrageleser.liesKopf(puffer.prefix(grenze.kopfLaenge)) {
            case .failure(let abweisung):
                return beende(.kaputt(abweisung.antwort))
            case .success(let (k, laenge)):
                kopf = k
                rumpfLaenge = laenge
                rumpfAnfang = grenze.rumpfAnfang
            }
        }
        let da = puffer.count - rumpfAnfang
        guard da >= rumpfLaenge, let kopf else { return .mehr }
        let start = puffer.startIndex + rumpfAnfang
        let rumpf = Data(puffer[start..<(start + rumpfLaenge)])
        // WAS NACH DEM RUMPF KOMMT, WIRD NICHT GELESEN: eine zweite Anfrage auf derselben
        // Verbindung gibt es hier nicht (der Mac schliesst nach der Antwort).
        return beende(.fertig(RoheAnfrage(kopf: kopf, rumpf: rumpf)))
    }

    /// Die Zwischenantwort `100 Continue` — **einmal**, und nur, wenn der Absender sie
    /// verlangt (`Expect: 100-continue`), der Kopf angenommen ist und noch Rumpf fehlt.
    ///
    /// Ohne sie wartete ein Absender, der fragt, bevor er schickt, bis zu einer Sekunde auf
    /// eine Antwort, die nie kommt. Ein abgewiesener Kopf bekommt sie nie: Dann geht
    /// gleich die Abweisung hinaus, und der Rumpf bleibt, wo er ist.
    public mutating func zwischenantwort() -> Data? {
        guard ende == nil, !fortsetzungGesagt, let kopf,
              kopf.fassung == "HTTP/1.1",
              kopf.koepfe.wert("Expect")?.lowercased() == "100-continue",
              puffer.count - rumpfAnfang < rumpfLaenge else { return nil }
        fortsetzungGesagt = true
        return Data("HTTP/1.1 100 Continue\r\n\r\n".utf8)
    }

    private mutating func beende(_ stand: Lesestand) -> Lesestand {
        ende = stand
        puffer = Data()
        return stand
    }

    // ---------------------------------------------------------------- Handgriffe

    /// Wo der Kopf endet: die erste Leerzeile (`\r\n\r\n`) ab der Stelle `ab`.
    ///
    /// **Ohne Kopie und nur ab `ab`** (Sicherheitsdurchsicht vom 01.10.2026): Bis dahin wurde
    /// der Puffer bei jedem Stück in eine Liste kopiert und von vorn durchsucht. Wer seinen
    /// Kopf Byte für Byte schickt, liess den Mac so für 32 KiB rund eine halbe Milliarde
    /// Bytes ansehen — *eine Suche, die bei jedem Byte von vorn beginnt, bezahlt der Leser,
    /// nicht der Schreiber.*
    static func kopfende(_ daten: Data, ab: Int = 0) -> (kopfLaenge: Int, rumpfAnfang: Int)? {
        daten.withUnsafeBytes { (b: UnsafeRawBufferPointer) -> (Int, Int)? in
            guard b.count >= 4 else { return nil }
            var i = max(0, ab)
            while i + 3 < b.count {
                if b[i] == 13, b[i + 1] == 10, b[i + 2] == 13, b[i + 3] == 10 {
                    return (i, i + 4)
                }
                i += 1
            }
            return nil
        }
    }

    /// Liest Anfragezeile und Köpfe — und wie lang der Rumpf wird.
    static func liesKopf(_ daten: Data) -> Result<(Anfragekopf, Int), Lesefehler> {
        // ISO-8859-1 UND NICHT UTF-8: Jedes Byte ist dann genau ein Zeichen, und nichts geht
        // beim Lesen verloren. Was kein sichtbares ASCII ist, faellt unten ohnehin.
        guard let text = String(data: daten, encoding: .isoLatin1) else {
            return .failure(Lesefehler(.fehler("Die Anfrage war nicht lesbar.", status: 400)))
        }
        var zeilen = text.components(separatedBy: "\r\n")
        let erste = zeilen.removeFirst()
        let teile = erste.split(separator: " ", omittingEmptySubsequences: false).map(String.init)
        guard teile.count == 3 else {
            return .failure(Lesefehler(.fehler("Die Anfragezeile war nicht lesbar.", status: 400)))
        }
        let (methode, ziel, fassung) = (teile[0], teile[1], teile[2])
        guard !methode.isEmpty, methode.unicodeScalars.allSatisfy({ ("A"..."Z").contains($0) }) else {
            return .failure(Lesefehler(.fehler("Die Art der Anfrage war nicht lesbar.", status: 400)))
        }
        guard fassung == "HTTP/1.1" || fassung == "HTTP/1.0" else {
            return .failure(Lesefehler(.fehler(
                "Diese HTTP-Fassung wird nicht gesprochen (nur 1.0 und 1.1).", status: 505)))
        }
        // NUR DIE FORM «/pfad?frage». Eine ganze Adresse an dieser Stelle («http://…»)
        // ist die Form, mit der man einen Vermittler bittet, ANDERSWOHIN zu gehen — der Mac
        // geht nur zum Heim-PC.
        guard Anfrageleser.zielIstSauber(ziel) else {
            return .failure(Lesefehler(.fehler(
                "Das Ziel der Anfrage hat nicht die Form «/pfad».", status: 400)))
        }

        var koepfe: [Kopfzeile] = []
        for zeile in zeilen {
            // EINE FORTGESETZTE ZEILE (beginnt mit Leerraum) ist eine alte Form, die zwei
            // Leser verschieden lesen koennen. Abgewiesen statt geraten.
            if zeile.hasPrefix(" ") || zeile.hasPrefix("\t") {
                return .failure(Lesefehler(.fehler("Eine Kopfzeile war nicht lesbar.", status: 400)))
            }
            guard let doppelpunkt = zeile.firstIndex(of: ":") else {
                return .failure(Lesefehler(.fehler("Eine Kopfzeile war nicht lesbar.", status: 400)))
            }
            let name = String(zeile[..<doppelpunkt])
            let wert = String(zeile[zeile.index(after: doppelpunkt)...])
                .trimmingCharacters(in: CharacterSet(charactersIn: " \t"))
            guard Anfrageleser.istToken(name),
                  wert.unicodeScalars.allSatisfy({ $0 == "\t" || (0x20...0x7E).contains($0.value)
                                                   || (0xA0...0xFF).contains($0.value) }) else {
                return .failure(Lesefehler(.fehler("Eine Kopfzeile war nicht lesbar.", status: 400)))
            }
            koepfe.append(Kopfzeile(name, wert))
        }

        // KEIN STUECKELN. Der Server auf dem Heim-PC liest ihn auch nicht (er liest nur
        // `Content-Length`), und beides zugleich ist die Form, mit der man zwei Leser
        // verschiedene Anfragen sehen laesst.
        if !koepfe.werte("Transfer-Encoding").isEmpty {
            if !koepfe.werte("Content-Length").isEmpty {
                return .failure(Lesefehler(.fehler(
                    "Die Anfrage nennt Länge und Stückelung zugleich.", status: 400)))
            }
            return .failure(Lesefehler(.fehler(
                "Die Anfrage braucht eine Länge (Content-Length); gestückelt wird nicht gelesen.",
                status: 411)))
        }
        let laengen = Set(koepfe.werte("Content-Length"))
        var laenge = 0
        if !laengen.isEmpty {
            guard laengen.count == 1, let l = laengen.first, !l.isEmpty, l.count <= 12,
                  l.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }),
                  let zahl = Int(l) else {
                return .failure(Lesefehler(.fehler("Die Länge der Anfrage war nicht lesbar.",
                                                   status: 400)))
            }
            laenge = zahl
        }
        // DIE GRENZE GREIFT AM KOPF, nicht am Rumpf: Was zu gross angekuendigt ist, wird
        // abgewiesen, bevor ein Byte davon gelesen ist. *Ein Riegel, der erst nach dem
        // Lesen greift, hat schon gelesen.*
        guard laenge <= Anfrageleser.rumpfGrenze else {
            return .failure(Lesefehler(.fehler(
                "Die Anfrage ist zu gross: \(laenge / 1024) KiB, über den Mac gehen höchstens "
                    + "\(Anfrageleser.rumpfGrenze / 1024) KiB.", status: 413)))
        }
        return .success((Anfragekopf(methode: methode, ziel: ziel, fassung: fassung,
                                     koepfe: koepfe), laenge))
    }

    /// Ein Ziel der Form `/pfad` oder `/pfad?frage`: nur sichtbares ASCII, kein `#`, kein
    /// Rückstrich, und **nicht** `//…` — das läse ein Adressbauer als anderen Rechner.
    public static func zielIstSauber(_ ziel: String) -> Bool {
        guard ziel.hasPrefix("/"), !ziel.hasPrefix("//"), ziel.count <= 8 * 1024 else {
            return false
        }
        return ziel.unicodeScalars.allSatisfy {
            (0x21...0x7E).contains($0.value) && $0 != "#" && $0 != "\\"
        }
    }

    /// Ein Name nach RFC 9110 («token»): Buchstaben, Ziffern und ``!#$%&'*+-.^_`|~``.
    static func istToken(_ text: String) -> Bool {
        guard !text.isEmpty else { return false }
        let zeichen = Set("!#$%&'*+-.^_`|~".unicodeScalars)
        return text.unicodeScalars.allSatisfy {
            ("a"..."z").contains($0) || ("A"..."Z").contains($0) || ("0"..."9").contains($0)
                || zeichen.contains($0)
        }
    }
}

/// Eine Abweisung beim Lesen — eigens, damit `Result` einen Fehlertyp hat.
public struct Lesefehler: Error, Equatable, Sendable {
    public let antwort: Leitungsantwort

    init(_ antwort: Leitungsantwort) {
        self.antwort = antwort
    }
}
