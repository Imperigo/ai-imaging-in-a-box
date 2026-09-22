import Foundation

// DIE ANFRAGEN AN DIE HOMESTATION — gebaut und gelesen, aber NICHT gesendet.
//
// Warum der Kern nicht selbst sendet (22.09.2026): Unter Linux gibt es `URLSession` und
// `URLRequest` in Foundation nicht, und der Kern soll hier pruefbar bleiben. Er baut darum
// jede Anfrage als EIGENE Datenstruktur (Weg, Frage, Kopfzeilen, Rumpf) und liest jede
// Antwort aus `Data`. Das Senden macht die App (`Verbindung/Sender.swift`).
//
// Die Felder stehen so, wie `oberflaeche/server.py` sie am 22.09.2026 WIRKLICH liefert
// (`docs/VISBOX_PROTOKOLL.md`). Ein Feld, das fehlt, bleibt `nil` — und `nil` heisst hier
// «nicht geliefert», nie «falsch» und nie «0».

// ======================================================================= JSON als Wert

/// Ein JSON-Wert, **wie er kam** — ohne dass eine Zahl zum Wahrheitswert oder ein `null`
/// zu einem leeren Text wird.
///
/// **Warum ganze Zahlen ein eigener Fall sind.** Der Server prüft die Schrittzahl mit
/// `isinstance(wert, int)`: Eine `28.0` wäre dort **keine** Schrittzahl, und der Lauf
/// hätte keinen Nenner. Ein einziger Zahlenfall (`Double`) machte aus jeder ganzen Zahl,
/// die das iPad weiterreicht, still eine Kommazahl.
public enum JSONWert: Equatable, Hashable, Sendable {
    case null
    case wahrheit(Bool)
    case ganz(Int)
    case zahl(Double)
    case text(String)
    case liste([JSONWert])
    case objekt([String: JSONWert])

    /// Ein Feld eines Objekts — `nil`, wenn es fehlt oder dies kein Objekt ist.
    public subscript(feld: String) -> JSONWert? {
        if case .objekt(let felder) = self { return felder[feld] }
        return nil
    }

    public var istNull: Bool { self == .null }

    public var alsText: String? {
        if case .text(let t) = self { return t }
        return nil
    }

    /// **Nur** `true` oder `false`. Eine `1` ist kein Ja.
    public var alsWahrheit: Bool? {
        if case .wahrheit(let w) = self { return w }
        return nil
    }

    /// Nur eine ganze Zahl. Eine `1.5` ist keine.
    public var alsGanz: Int? {
        if case .ganz(let g) = self { return g }
        return nil
    }

    /// Jede Zahl (ganz oder mit Komma) — aber kein Wahrheitswert.
    public var alsZahl: Double? {
        switch self {
        case .ganz(let g): return Double(g)
        case .zahl(let z): return z
        default: return nil
        }
    }

    public var alsListe: [JSONWert]? {
        if case .liste(let l) = self { return l }
        return nil
    }

    public var alsObjekt: [String: JSONWert]? {
        if case .objekt(let o) = self { return o }
        return nil
    }

    /// Liest JSON aus Bytes.
    public static func lies(_ daten: Data) throws -> JSONWert {
        try JSONDecoder().decode(JSONWert.self, from: daten)
    }

    /// Schreibt JSON — mit sortierten Schlüsseln, damit dieselbe Anfrage dieselben Bytes
    /// ergibt (und eine Probe sie vergleichen kann).
    public func daten() throws -> Data {
        let schreiber = JSONEncoder()
        schreiber.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        return try schreiber.encode(self)
    }
}

extension JSONWert: Codable {
    public init(from decoder: Decoder) throws {
        let behaelter = try decoder.singleValueContainer()
        // DIE REIHENFOLGE TRAEGT: erst null, dann Wahrheitswert, dann ganze Zahl, dann
        // Kommazahl. Andersherum gelesen, wuerde aus `true` eine 1 oder aus `28` eine 28.0.
        if behaelter.decodeNil() {
            self = .null
        } else if let w = try? behaelter.decode(Bool.self) {
            self = .wahrheit(w)
        } else if let g = try? behaelter.decode(Int.self) {
            self = .ganz(g)
        } else if let z = try? behaelter.decode(Double.self) {
            self = .zahl(z)
        } else if let t = try? behaelter.decode(String.self) {
            self = .text(t)
        } else if let l = try? behaelter.decode([JSONWert].self) {
            self = .liste(l)
        } else {
            self = .objekt(try behaelter.decode([String: JSONWert].self))
        }
    }

    public func encode(to encoder: Encoder) throws {
        var behaelter = encoder.singleValueContainer()
        switch self {
        case .null: try behaelter.encodeNil()
        case .wahrheit(let w): try behaelter.encode(w)
        case .ganz(let g): try behaelter.encode(g)
        case .zahl(let z): try behaelter.encode(z)
        case .text(let t): try behaelter.encode(t)
        case .liste(let l): try behaelter.encode(l)
        case .objekt(let o): try behaelter.encode(o)
        }
    }
}

// ========================================================================= Anmeldung

/// Benutzer und Kennwort für die Tür des Servers (HTTP-Basic).
///
/// **Der Benutzername wird nicht eingebaut**, sondern aus der Antwort von
/// `POST /api/verbinden` übernommen (Protokoll §2) — sonst trüge die App nach der
/// Umbenennung den alten Namen weiter.
///
/// **Wo sie liegt:** Die App legt sie in den Schlüsselbund (`Verbindung/Schluesselbund.swift`),
/// nie in `UserDefaults` — die Lehre aus dem früheren Mac-Client, der das Kennwort dort
/// im Klartext liegen hatte. Diese Struktur zeigt das Kennwort auch in keiner Ausgabe
/// (`description`, `dump`).
public struct Anmeldung: Equatable, Sendable, Codable {
    public let benutzer: String
    public let kennwort: String

    public init(benutzer: String, kennwort: String) {
        self.benutzer = benutzer
        self.kennwort = kennwort
    }

    /// Der Wert der Kopfzeile `Authorization`.
    public var kopfzeile: String {
        "Basic " + Data("\(benutzer):\(kennwort)".utf8).base64EncodedString()
    }
}

extension Anmeldung: CustomStringConvertible, CustomDebugStringConvertible, CustomReflectable {
    public var description: String { "Anmeldung(benutzer: \(benutzer), kennwort: verdeckt)" }
    public var debugDescription: String { description }
    public var customMirror: Mirror {
        Mirror(self, children: ["benutzer": benutzer, "kennwort": "verdeckt"])
    }
}

// ============================================================================ Anfrage

/// Ein Teil der Frage (`?name=wert`). Eigene Struktur statt Tupel, damit eine Anfrage
/// vergleichbar bleibt.
public struct Frageteil: Equatable, Hashable, Sendable {
    public let name: String
    public let wert: String

    public init(_ name: String, _ wert: String) {
        self.name = name
        self.wert = wert
    }
}

/// Eine fertige Anfrage an einen Weg — **ohne Netz.** Die App macht daraus einen
/// `URLRequest`; eine Probe kann sie Feld für Feld ansehen.
public struct Anfrage: Equatable, Sendable {
    public let weg: Weg
    public let frage: [Frageteil]
    public let kopfzeilen: [String: String]
    /// Der Rumpf (JSON) — bei GET `nil`.
    public let rumpf: Data?

    public var methode: Methode { weg.methode }

    /// Die ganze Adresse auf einer HomeStation. Kodiert wird an **einer** Stelle
    /// (`Wege.adresse`), nicht hier ein zweites Mal.
    public func adresse(basis: URL) -> URL? {
        Wege.adresse(weg, basis: basis, frage: frage.map { ($0.name, $0.wert) })
    }

    /// Pfad samt kodierter Frage, z. B. `/bild?name=a%2Bb.png`.
    public var pfad: String {
        guard let basis = URL(string: "http://homestation.invalid"),
              let url = adresse(basis: basis),
              let teile = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            return weg.pfad
        }
        if let frage = teile.percentEncodedQuery, !frage.isEmpty {
            return teile.percentEncodedPath + "?" + frage
        }
        return teile.percentEncodedPath
    }
}

/// Die Anfragen an die Wege aus `Wege.swift` — **eine Bauform je Weg.**
///
/// Die Webseite (`Wege.seite`, `Wege.seiteLang`) bekommt keine eigene; die App braucht
/// sie nicht. Wer einen neuen Weg einträgt, fällt in `AnfragenTests` auf, solange er hier
/// keine Bauform hat.
public enum Anfragen {

    /// Die allgemeine Bauform. Die benannten darunter rufen nur sie.
    ///
    /// * Ein **POST** trägt immer einen Rumpf — mindestens `{}`, auch wenn der Server einen
    ///   leeren Rumpf ebenso liest. Ausdrücklich ist besser als gleichwertig.
    /// * Die **Anmeldung** geht nur an Wege, die sie verlangen. `POST /api/verbinden` ist
    ///   der Weg hinein; ein altes, falsches Kennwort dort mitzuschicken, hülfe nichts und
    ///   gäbe ein Geheimnis aus der Hand, das an diesem Weg niemand braucht.
    public static func baue(_ weg: Weg, frage: [Frageteil] = [],
                            rumpf: [String: JSONWert]? = nil,
                            anmeldung: Anmeldung?) -> Anfrage {
        var kopf = ["Accept": "application/json"]
        if !weg.ohneAnmeldung, let a = anmeldung {
            kopf["Authorization"] = a.kopfzeile
        }
        var roh: Data?
        if weg.methode == .post {
            kopf["Content-Type"] = "application/json; charset=utf-8"
            // `try?` IST HIER KEIN WEGSCHAUEN: Ein `JSONWert` besteht nur aus Faellen, die
            // JSON kennt; das Schreiben scheitert nur an einer Kommazahl wie `nan`, und
            // dann geht `{}` hinaus, nicht eine halbe Anfrage.
            roh = (try? JSONWert.objekt(rumpf ?? [:]).daten()) ?? Data("{}".utf8)
        }
        return Anfrage(weg: weg, frage: frage, kopfzeilen: kopf, rumpf: roh)
    }

    // -------------------------------------------------------------------- lesen (GET)

    /// `GET /api/projekt` — ohne `ordner` gilt der beim Start der HomeStation gesetzte.
    public static func projekt(ordner: String?, anmeldung: Anmeldung?) -> Anfrage {
        baue(Wege.projekt, frage: frageteile(["ordner": ordner]), anmeldung: anmeldung)
    }

    /// `GET /api/fortschritt` — der eine Laufstand des Servers.
    public static func fortschritt(anmeldung: Anmeldung?) -> Anfrage {
        baue(Wege.fortschritt, anmeldung: anmeldung)
    }

    /// `GET /bild` — ein Bild aus dem Projektordner.
    public static func bild(name: String, ordner: String?, anmeldung: Anmeldung?) -> Anfrage {
        baue(Wege.bild, frage: frageteile(["ordner": ordner, "name": name]),
             anmeldung: anmeldung)
    }

    // ----------------------------------------------------------------- handeln (POST)

    /// `POST /api/verbinden` — die sechsstellige Zahl gegen Benutzer und Kennwort.
    /// Nimmt nur eine geprüfte Zahl an: Ein Tippfehler soll keinen der wenigen Versuche
    /// verbrauchen, die die HomeStation zulässt.
    public static func verbinden(_ zahl: Kopplungszahl) -> Anfrage {
        baue(Wege.verbinden, rumpf: ["pin": .text(zahl.ziffern)], anmeldung: nil)
    }

    /// `POST /api/skizze` — eine Zeichnung als PNG.
    ///
    /// `ueber` fehlt, wenn auf leerem Grund gezeichnet wurde; `name` wird drüben **nicht**
    /// Dateiname, sondern geht in die Bemerkung (Protokoll §3).
    ///
    /// **Die Grösse prüft hier niemand** (der Server nimmt höchstens 2 MiB). Eine Abschrift
    /// seiner Grenze wäre eine zweite Regel, die unbewacht veraltet; eine zu grosse Skizze
    /// kommt als Abweisung mit Satz zurück und bleibt im Parkfach liegen.
    public static func skizze(png: Data, ueber: String? = nil, bemerkung: String? = nil,
                              name: String? = nil, ordner: String? = nil,
                              anmeldung: Anmeldung?) -> Anfrage {
        var rumpf = felder(["ordner": ordner, "ueber": ueber, "bemerkung": bemerkung,
                            "name": name])
        rumpf["png_base64"] = .text(png.base64EncodedString())
        return baue(Wege.skizze, rumpf: rumpf, anmeldung: anmeldung)
    }

    /// `POST /api/rechne` — antwortet sofort; der Lauf kommt über `fortschritt`.
    public static func rechne(ordner: String? = nil, einstellungen: [String: JSONWert]? = nil,
                              trotzAenderung: Bool? = nil,
                              anmeldung: Anmeldung?) -> Anfrage {
        var rumpf = felder(["ordner": ordner])
        if let e = einstellungen { rumpf["einstellungen"] = .objekt(e) }
        if let t = trotzAenderung { rumpf["trotz_aenderung"] = .wahrheit(t) }
        return baue(Wege.rechne, rumpf: rumpf, anmeldung: anmeldung)
    }

    /// `POST /api/einstellungen`. Ein Feld mit `.null` **entfernt** die Einstellung drüben
    /// (dann gilt wieder die Vorgabe) — es wird darum mitgeschickt und nicht weggelassen.
    public static func einstellungen(_ werte: [String: JSONWert], ordner: String? = nil,
                                     anmeldung: Anmeldung?) -> Anfrage {
        var rumpf = felder(["ordner": ordner])
        rumpf["einstellungen"] = .objekt(werte)
        return baue(Wege.einstellungen, rumpf: rumpf, anmeldung: anmeldung)
    }

    /// `POST /api/anlegen` — `ordner` und `modell` sind Pfade **auf der HomeStation.**
    public static func anlegen(ordner: String, modell: String, name: String? = nil,
                               einstellungen: [String: JSONWert]? = nil,
                               anmeldung: Anmeldung?) -> Anfrage {
        var rumpf = felder(["ordner": ordner, "modell": modell, "name": name])
        if let e = einstellungen { rumpf["einstellungen"] = .objekt(e) }
        return baue(Wege.anlegen, rumpf: rumpf, anmeldung: anmeldung)
    }

    // ------------------------------------------------------------------- Handgriffe

    /// Freiwillige Textfelder: **fehlt** der Wert oder ist er leer, fehlt das Feld. Ein
    /// leerer Ordner hiesse drüben dasselbe wie keiner, sähe hier aber aus wie eine Angabe.
    private static func felder(_ werte: [String: String?]) -> [String: JSONWert] {
        var aus: [String: JSONWert] = [:]
        for (name, wert) in werte {
            if let w = wert, !w.isEmpty { aus[name] = .text(w) }
        }
        return aus
    }

    private static func frageteile(_ werte: [String: String?]) -> [Frageteil] {
        werte.compactMap { name, wert in
            guard let w = wert, !w.isEmpty else { return nil }
            return Frageteil(name, w)
        }.sorted { $0.name < $1.name }
    }
}

// ================================================================ die sechsstellige Zahl

/// Die Zahl für das erste Verbinden — **genau sechs Ziffern**, sonst keine.
///
/// Wie der Server (`aiimaging.kopplung.pruefe`) wird nur Leerraum **am Rand** entfernt.
/// «123 456» wird nicht zusammengezogen: Das täte der Server auch nicht, und die Zahl
/// ginge als falsch durch und kostete einen Versuch.
public struct Kopplungszahl: Equatable, Sendable {
    public let ziffern: String

    public init?(_ eingabe: String) {
        let sauber = eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
        // NUR ASCII-ZIFFERN. `Character.isNumber` liesse auch «٣» oder «½» durch — die
        // der Server nie als seine Zahl erkennt.
        guard sauber.count == 6,
              sauber.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }) else {
            return nil
        }
        ziffern = sauber
    }
}

// ============================================================================ Antworten

/// Eine Antwort, die kein Erfolg ist — **mit dem Satz, der dem Menschen gezeigt wird.**
public struct Serverfehler: Error, Equatable, Sendable {
    public enum Art: Equatable, Sendable {
        /// 400 — die Anfrage wurde gelesen und abgelehnt.
        case abgelehnt
        /// 401 — die Tür: nicht (mehr) angemeldet.
        case nichtAngemeldet
        /// 403 — verweigert (beim Verbinden: keine offene Zahl).
        case verweigert
        /// 404 — kein Projekt, kein Bild, kein Weg.
        case nichtGefunden
        /// Erfolg gemeldet, aber die Antwort liess sich nicht lesen. Dann ist **nicht
        /// bekannt**, was drüben geschah — und das wird nicht als Erfolg ausgegeben.
        case unlesbar
        case anderer
    }

    public let code: Int
    public let satz: String
    /// Ob der Satz vom Server kommt (`true`) oder von dieser App, weil der Server keinen
    /// lesbaren mitschickte (`false`). Die Anzeige soll das nicht vermischen.
    public let satzVomServer: Bool

    public init(code: Int, satz: String, satzVomServer: Bool) {
        self.code = code
        self.satz = satz
        self.satzVomServer = satzVomServer
    }

    public var art: Art {
        switch code {
        case 200..<300: return .unlesbar
        case 400: return .abgelehnt
        case 401: return .nichtAngemeldet
        case 403: return .verweigert
        case 404: return .nichtGefunden
        default: return .anderer
        }
    }

    /// Aus einer Antwort, die nicht 2xx ist: der Satz aus `fehler` (sonst `satz`).
    static func aus(status: Int, daten: Data) -> Serverfehler {
        let wert = try? JSONWert.lies(daten)
        if let satz = wert?["fehler"]?.alsText ?? wert?["satz"]?.alsText, !satz.isEmpty {
            return Serverfehler(code: status, satz: satz, satzVomServer: true)
        }
        return Serverfehler(
            code: status,
            satz: "Die HomeStation antwortete mit \(status), ohne einen lesbaren Satz.",
            satzVomServer: false)
    }

    static func unlesbar(_ status: Int, _ was: String) -> Serverfehler {
        Serverfehler(code: status,
                     satz: "Die Antwort der HomeStation war nicht lesbar (\(was)).",
                     satzVomServer: false)
    }
}

/// Liest eine JSON-Antwort, die ein **Objekt** sein muss — oder wirft den `Serverfehler`.
public func liesAntwort(status: Int, daten: Data) throws -> [String: JSONWert] {
    guard (200..<300).contains(status) else {
        throw Serverfehler.aus(status: status, daten: daten)
    }
    guard let wert = try? JSONWert.lies(daten), let objekt = wert.alsObjekt else {
        throw Serverfehler.unlesbar(status, "kein JSON-Objekt")
    }
    return objekt
}

/// Die Bildbytes aus `GET /bild` — oder der Satz, warum keine.
public func liesBild(status: Int, daten: Data) throws -> Data {
    guard (200..<300).contains(status) else {
        throw Serverfehler.aus(status: status, daten: daten)
    }
    guard !daten.isEmpty else { throw Serverfehler.unlesbar(status, "leeres Bild") }
    return daten
}

// ------------------------------------------------------------------- erstes Verbinden

/// Was `POST /api/verbinden` sagt.
public enum Kopplungsergebnis: Equatable, Sendable {
    /// Verbunden. `anmeldung` ist `nil`, wenn die HomeStation **ohne** Kennwort läuft
    /// (dann gibt es nichts aufzubewahren) — nicht, weil etwas fehlte.
    case verbunden(anmeldung: Anmeldung?, satz: String?)
    /// Abgelehnt, mit dem Satz für den Menschen. Den genauen Grund sagt die HomeStation
    /// absichtlich nur in ihrem eigenen Fenster (Protokoll §7).
    case abgelehnt(satz: String)

    /// Ein Satz, wenn die HomeStation ein Verbinden gar nicht offen hat und darum mit der
    /// Tür antwortet (401). Ihr eigener Satz spräche dann von Benutzer und Kennwort —
    /// richtig für die Tür, irreführend für jemanden, der eine Zahl eintippt.
    public static let keinVerbindenOffen =
        "Die HomeStation lässt gerade kein Verbinden zu. Dort eine neue Zahl holen."

    public static func lies(status: Int, daten: Data) throws -> Kopplungsergebnis {
        if status == 401 { return .abgelehnt(satz: keinVerbindenOffen) }
        if status == 403 {
            // Beide Formen des Servers: `{"verbunden": false, "satz"}` bei falscher Zahl,
            // `{"fehler"}` ohne offene Kopplung. Beides heisst: eine neue Zahl holen.
            return .abgelehnt(satz: Serverfehler.aus(status: status, daten: daten).satz)
        }
        let o = try liesAntwort(status: status, daten: daten)
        // ERFOLG NUR, WENN ER DASTEHT. Eine 200 ohne `verbunden: true` ist keine Kopplung.
        guard o["verbunden"]?.alsWahrheit == true else {
            throw Serverfehler.unlesbar(status, "kein «verbunden: true»")
        }
        var anmeldung: Anmeldung?
        if let benutzer = o["benutzer"]?.alsText, let kennwort = o["kennwort"]?.alsText {
            anmeldung = Anmeldung(benutzer: benutzer, kennwort: kennwort)
        } else if o["kennwort"]?.istNull != true {
            // Ein Kennwort, das fehlt oder kein Text ist, ist nicht «ohne Kennwort».
            throw Serverfehler.unlesbar(status, "Benutzer oder Kennwort fehlt")
        }
        return .verbunden(anmeldung: anmeldung, satz: o["satz"]?.alsText)
    }
}

// ------------------------------------------------------------------ Sicht auf ein Projekt

/// Wie es um die Modelldatei steht (`modell.stand`) — **vier Fälle, und einer ist weder ja
/// noch nein** (`nichtPruefbar`).
public enum Modellstand: String, Equatable, Sendable {
    case unveraendert
    case veraendert
    case fehlt
    case nichtPruefbar = "nicht_pruefbar"
}

/// `modell` aus der Sicht.
public struct Modellangabe: Equatable, Sendable {
    public let pfad: String?
    /// Wie der Server es schrieb.
    public let standRoh: String?
    public let grund: String?

    /// Ein unbekannter Stand gibt `nil` — und nicht «unverändert».
    public var stand: Modellstand? { standRoh.flatMap(Modellstand.init(rawValue:)) }
}

/// Ein Bild der Mappe (`bilder[]`).
public struct Bildeintrag: Equatable, Sendable {
    public let bild: String?
    public let schicht: String?
    /// Das Zeichen, roh.
    public let zeichen: String?
    public let satz: String?
    public let erzeugt: String?
    /// `true`, `false` (die Mappe nennt es, die Datei fehlt) oder `nil` (nicht gefragt).
    public let vorhanden: Bool?
    public let herkunft: JSONWert?
    /// Das **geerbte** Urteil eines Bildes der zweiten Stufe — ein eigenes Feld.
    public let basis: JSONWert?

    /// Das Urteil. Ein fehlendes oder unbekanntes Zeichen gibt `nil` — **nicht** «nicht
    /// gemessen». Geraten sähe in der Anzeige aus wie gewusst.
    public var urteil: Urteil? { zeichen.flatMap(Urteil.init(zeichen:)) }

    init(_ o: [String: JSONWert]) {
        bild = o["bild"]?.alsText
        schicht = o["schicht"]?.alsText
        zeichen = o["zeichen"]?.alsText
        satz = o["satz"]?.alsText
        erzeugt = o["erzeugt"]?.alsText
        vorhanden = o["vorhanden"]?.alsWahrheit
        herkunft = o["herkunft"]
        basis = o["basis"].flatMap { $0.istNull ? nil : $0 }
    }
}

/// Eine Skizze der Mappe (`skizzen[]`), unverändert.
public struct Skizzeneintrag: Equatable, Sendable {
    public let skizze: String?
    public let ueber: String?
    public let erzeugt: String?
    /// `offen`, `gerechnet` oder `verworfen` — roh.
    public let stand: String?
    public let bemerkung: String?
    /// `nil`, solange nichts daraus wurde.
    public let ergebnis: JSONWert?

    init(_ o: [String: JSONWert]) {
        skizze = o["skizze"]?.alsText
        ueber = o["ueber"]?.alsText
        erzeugt = o["erzeugt"]?.alsText
        stand = o["stand"]?.alsText
        bemerkung = o["bemerkung"]?.alsText
        ergebnis = o["ergebnis"].flatMap { $0.istNull ? nil : $0 }
    }
}

/// `GET /api/projekt` — die Sicht auf ein Projekt, **soweit die App sie braucht.** Alles
/// Übrige steht unverändert in `roh`.
public struct Projektsicht: Equatable, Sendable {
    public let name: String?
    public let ordner: String?
    public let modell: Modellangabe?
    /// `nil` heisst: **nicht geliefert** — nicht «keine Bilder».
    public let bilder: [Bildeintrag]?
    public let skizzen: [Skizzeneintrag]?
    public let knotenbaumFehler: String?
    public let einstellungen: JSONWert?
    /// Der Import-Block (`import`).
    public let einfuhr: JSONWert?
    public let roh: [String: JSONWert]

    public static func lies(status: Int, daten: Data) throws -> Projektsicht {
        let o = try liesAntwort(status: status, daten: daten)
        return Projektsicht(o)
    }

    init(_ o: [String: JSONWert]) {
        roh = o
        name = o["name"]?.alsText
        ordner = o["ordner"]?.alsText
        modell = o["modell"]?.alsObjekt.map {
            Modellangabe(pfad: $0["pfad"]?.alsText, standRoh: $0["stand"]?.alsText,
                         grund: $0["grund"]?.alsText)
        }
        bilder = o["bilder"]?.alsListe?.compactMap { $0.alsObjekt.map(Bildeintrag.init) }
        skizzen = o["skizzen"]?.alsListe?.compactMap { $0.alsObjekt.map(Skizzeneintrag.init) }
        knotenbaumFehler = o["knotenbaum_fehler"]?.alsText
        einstellungen = o["einstellungen"]
        einfuhr = o["import"]
    }
}

// --------------------------------------------------------------------------- Laufstand

/// Ein fertiger Knoten des laufenden Laufs (`fertige[]`).
public struct FertigerKnoten: Equatable, Sendable {
    public let knoten: String?
    public let knotenart: String?
    /// `ok`, `abgelehnt`, `fehler` oder `uebersprungen` — roh.
    public let status: String?
    public let ausCache: Bool?
    public let dauerS: Double?
}

/// `GET /api/fortschritt` — der **eine** Laufstand des Servers.
public struct Fortschrittsstand: Equatable, Sendable {
    public let laeuft: Bool?
    public let ordner: String?
    public let seitS: Double?
    public let knoten: String?
    public let knotenart: String?
    public let nummer: Int?
    public let von: Int?
    public let knotenSeitS: Double?
    public let schritt: Int?
    /// `nil` heisst **unbekannt**, nicht 0.
    public let schritteGesamt: Int?
    /// `belegt` oder `unbelegt` — roh.
    public let artDesZeichens: String?
    public let fertige: [FertigerKnoten]?
    public let ergebnis: JSONWert?
    public let fehler: String?

    /// Ob der Stand **gezählt** ist: `true` bei `belegt`, `false` bei `unbelegt`, `nil`
    /// bei allem anderen.
    public var belegt: Bool? {
        switch artDesZeichens {
        case "belegt": return true
        case "unbelegt": return false
        default: return nil
        }
    }

    /// Der Anteil der Schritte **im laufenden Knoten** — nur, wenn der Server sagt, dass
    /// er gezählt ist. Einen Anteil über den ganzen Lauf gibt es nicht (Protokoll §5),
    /// und bei `unbelegt` ist jede Zahl hier eine erfundene.
    public var schrittanteil: Double? {
        guard belegt == true, let s = schritt, let g = schritteGesamt, g > 0 else {
            return nil
        }
        return min(max(Double(s) / Double(g), 0), 1)
    }

    public static func lies(status: Int, daten: Data) throws -> Fortschrittsstand {
        let o = try liesAntwort(status: status, daten: daten)
        return Fortschrittsstand(
            laeuft: o["laeuft"]?.alsWahrheit,
            ordner: o["ordner"]?.alsText,
            seitS: o["seit_s"]?.alsZahl,
            knoten: o["knoten"]?.alsText,
            knotenart: o["knotenart"]?.alsText,
            nummer: o["nummer"]?.alsGanz,
            von: o["von"]?.alsGanz,
            knotenSeitS: o["knoten_seit_s"]?.alsZahl,
            schritt: o["schritt"]?.alsGanz,
            schritteGesamt: o["schritte_gesamt"]?.alsGanz,
            artDesZeichens: o["art_des_zeichens"]?.alsText,
            fertige: o["fertige"]?.alsListe?.compactMap { w in
                w.alsObjekt.map {
                    FertigerKnoten(knoten: $0["knoten"]?.alsText,
                                   knotenart: $0["knotenart"]?.alsText,
                                   status: $0["status"]?.alsText,
                                   ausCache: $0["aus_cache"]?.alsWahrheit,
                                   dauerS: $0["dauer_s"]?.alsZahl)
                }
            },
            ergebnis: o["ergebnis"].flatMap { $0.istNull ? nil : $0 },
            fehler: o["fehler"]?.alsText)
    }
}

// ---------------------------------------------------------------- Antworten auf POST

/// `POST /api/skizze` — **abgelegt** heisst in der Mappe, nicht gerechnet.
public struct Skizzenquittung: Equatable, Sendable {
    /// Der Dateiname, den die HomeStation vergab (aus der Uhrzeit, nie aus dem Wunsch).
    public let skizze: String?
    public let hinweis: String?

    public static func lies(status: Int, daten: Data) throws -> Skizzenquittung {
        let o = try liesAntwort(status: status, daten: daten)
        guard o["abgelegt"]?.alsWahrheit == true else {
            throw Serverfehler.unlesbar(status, "kein «abgelegt: true»")
        }
        return Skizzenquittung(skizze: o["skizze"]?.alsText, hinweis: o["hinweis"]?.alsText)
    }
}

/// `POST /api/rechne` — gestartet, nicht gerechnet.
public struct Rechenstart: Equatable, Sendable {
    /// `nil` heisst unbekannt.
    public let schritteGesamt: Int?

    public static func lies(status: Int, daten: Data) throws -> Rechenstart {
        let o = try liesAntwort(status: status, daten: daten)
        guard o["gestartet"]?.alsWahrheit == true else {
            throw Serverfehler.unlesbar(status, "kein «gestartet: true»")
        }
        return Rechenstart(schritteGesamt: o["schritte_gesamt"]?.alsGanz)
    }
}

/// `POST /api/einstellungen` — der ganze neue Satz.
public struct Einstellungsantwort: Equatable, Sendable {
    public let einstellungen: [String: JSONWert]?

    public static func lies(status: Int, daten: Data) throws -> Einstellungsantwort {
        let o = try liesAntwort(status: status, daten: daten)
        guard o["gespeichert"]?.alsWahrheit == true else {
            throw Serverfehler.unlesbar(status, "kein «gespeichert: true»")
        }
        return Einstellungsantwort(einstellungen: o["einstellungen"]?.alsObjekt)
    }
}

/// `POST /api/anlegen` — angelegt, samt Import-Block. Ein unbrauchbares Modell ist hier
/// kein Fehler; der Befund steht im Import-Block.
public struct Anlegeantwort: Equatable, Sendable {
    public let einfuhr: JSONWert?

    public static func lies(status: Int, daten: Data) throws -> Anlegeantwort {
        let o = try liesAntwort(status: status, daten: daten)
        guard o["angelegt"]?.alsWahrheit == true else {
            throw Serverfehler.unlesbar(status, "kein «angelegt: true»")
        }
        return Anlegeantwort(einfuhr: o["import"])
    }
}

// ============================================ die Wege vom 22.09.2026 (Einheit D-SERVER)

extension Anfragen {
    /// `POST /api/benennen` — ein eigener Name (Entscheid 19). `titel` `nil` nimmt ihn
    /// zurück und geht darum als `null` hinaus, nicht als fehlendes Feld.
    public static func benennen(bild: String? = nil, skizze: String? = nil, titel: String?,
                                vonStand: Int? = nil, ordner: String? = nil,
                                anmeldung: Anmeldung?) -> Anfrage {
        var rumpf: [String: JSONWert] = [:]
        if let o = ordner, !o.isEmpty { rumpf["ordner"] = .text(o) }
        if let b = bild { rumpf["bild"] = .text(b) }
        if let s = skizze { rumpf["skizze"] = .text(s) }
        rumpf["titel"] = titel.map { .text($0) } ?? .null
        if let v = vonStand { rumpf["von_stand"] = .ganz(v) }
        return baue(Wege.benennen, rumpf: rumpf, anmeldung: anmeldung)
    }

    /// `POST /api/abbrechen` — zwischen zwei Knoten (Entscheid 31).
    public static func abbrechen(anmeldung: Anmeldung?) -> Anfrage {
        baue(Wege.abbrechen, rumpf: [:], anmeldung: anmeldung)
    }

    /// `POST /api/rechne-skizze` — eine Skizze, oder 2 bis 8 als Ebenen-Reihe.
    public static func rechneSkizze(_ skizzen: [String], anweisung: String? = nil,
                                    entwurf: Bool = false, ordner: String? = nil,
                                    anmeldung: Anmeldung?) -> Anfrage {
        var rumpf: [String: JSONWert] = [:]
        if let o = ordner, !o.isEmpty { rumpf["ordner"] = .text(o) }
        rumpf["skizze"] = skizzen.count == 1 ? .text(skizzen[0]) : .liste(skizzen.map { .text($0) })
        if let a = anweisung, !a.isEmpty { rumpf["anweisung"] = .text(a) }
        rumpf["entwurf"] = .wahrheit(entwurf)
        return baue(Wege.rechneSkizze, rumpf: rumpf, anmeldung: anmeldung)
    }
}
