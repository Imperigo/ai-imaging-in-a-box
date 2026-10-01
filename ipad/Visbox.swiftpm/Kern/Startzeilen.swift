import Foundation

// DIE STARTZEILEN DER MAC-APP (Blatt 13, Entscheid 38) — der Zustand, ohne Oberflaeche.
//
// Vier Zeilen: Leitung zum Heim-PC, Rechner am Heim-PC, Assistent, iPad. Jede sagt, was
// sie gerade tut, und wenn sie nicht ankommt, warum. Die Ableitung aus den Antworten des
// Servers steht HIER, nicht in der Mac-App: Der Kern ist unter Linux pruefbar, die
// Mac-App sieht erst in der Pruefstrecke einen Uebersetzer (Regel 4 — die Logik in die
// Bibliothek, die Oberflaeche duenn). Die Mac-App misst nur (Antwortcode, Zeit, Fehlercode)
// und zeigt, was hier herauskommt.
//
//     *Eine Zeile, die «steht» sagt, weil niemand nachgesehen hat, ist schlimmer als keine.*

// ===================================================================== der Zustand

/// Wie es um eine Zeile steht — **vier Antworten, jede mit ihrem Satz.**
///
/// «Wartet» und «fehlt» sind verschieden: Was wartet, kommt, sobald etwas anderes da ist
/// (die Leitung, das iPad, ein neuerer Server). Was fehlt, kommt von selbst nicht — der
/// Grund sagt, was zu tun ist.
public enum Zeilenstand: Equatable, Sendable {
    case steht(satz: String)
    /// `seit` bleibt über mehrere Abfragen dieselbe (`fortgeschrieben(vorher:)`): «seit 12 s»
    /// zählt ab dem ersten Mal, nicht ab der letzten Abfrage.
    case laedt(seit: Date, satz: String)
    case wartet(satz: String)
    case fehlt(grund: String)

    /// Das eine Wort am rechten Rand der Zeile (Blatt 13).
    public var wort: String {
        switch self {
        case .steht: return "steht"
        case .laedt: return "lädt"
        case .wartet: return "wartet"
        case .fehlt: return "fehlt"
        }
    }

    /// Der Satz unter dem Titel — **nie leer.** Kommt einer leer an (etwa ein leerer `satz`
    /// des Servers, oder ein Aufrufer, der keinen hatte), steht der Ersatz da: Eine Zeile
    /// ohne Satz sieht aus wie eine, die nichts zu sagen hat.
    public var satz: String {
        switch self {
        case .steht(let s): return Zeilensatz.oder(s, "Steht.")
        case .laedt(_, let s): return Zeilensatz.oder(s, "Wird geladen.")
        case .wartet(let s): return Zeilensatz.oder(s, "Wartet.")
        case .fehlt(let g): return Zeilensatz.oder(g, "Fehlt — ohne Angabe des Grundes.")
        }
    }

    public var steht: Bool {
        if case .steht = self { return true }
        return false
    }

    public var laedt: Bool {
        if case .laedt = self { return true }
        return false
    }

    public var fehlt: Bool {
        if case .fehlt = self { return true }
        return false
    }

    /// Lädt die Zeile jetzt **und** lud sie schon vorher, gilt der frühere Beginn. Sonst
    /// bleibt sie, wie sie ist.
    public func fortgeschrieben(vorher: Zeilenstand?) -> Zeilenstand {
        guard case .laedt(_, let satz) = self,
              case .laedt(let frueher, _)? = vorher else { return self }
        return .laedt(seit: frueher, satz: satz)
    }
}

/// Die vier Zeilen, in der Reihenfolge von Blatt 13.
public enum Startzeile: String, CaseIterable, Sendable {
    case leitung, rechner, assistent, ipad

    public var titel: String {
        switch self {
        case .leitung: return "Leitung zum Heim-PC"
        case .rechner: return "Rechner am Heim-PC"
        case .assistent: return "Assistent"
        case .ipad: return "iPad"
        }
    }
}

/// Sätze, die nie leer sind.
enum Zeilensatz {
    /// `text`, wenn er etwas sagt — sonst `ersatz`.
    static func oder(_ text: String?, _ ersatz: String) -> String {
        guard let t = text?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty else {
            return ersatz
        }
        return t
    }
}

// ================================================================ was gemessen wurde

/// Warum keine Antwort kam — **die Fälle, die einen anderen Satz brauchen.**
///
/// Die Mac-App gibt den Fehlercode von `URLSession` herein (`init(urlFehlercode:)`); die
/// Zuordnung steht hier, damit sie unter Linux geprüft wird. Die Codes sind die
/// festen Werte von `NSURLErrorDomain`, als Zahl, weil `URLError` unter Linux in einem
/// anderen Modul liegt als unter macOS.
public enum Leitungsfehler: Equatable, Sendable {
    /// Gefragt, und in der Frist kam nichts.
    case zeitUeberschritten
    /// Der Rechner unter dem Namen nimmt keine Verbindung an.
    case keineVerbindung
    /// Mitten in der Antwort abgerissen.
    case abgerissen
    /// Dieser Mac hat gar kein Netz.
    case keinNetz
    /// Der Name lässt sich nicht auflösen — im eigenen Tailscale-Netz heisst das fast immer:
    /// Tailscale am Mac ist aus.
    case nameUnbekannt
    /// Die verschlüsselte Leitung kam nicht zustande (Zertifikat). Tailscale Serve hat ein
    /// gültiges; ein fremdes oder keines heisst fast immer: nicht über Tailscale gefragt.
    case zertifikat
    /// Die App hat die Frage selbst zurückgezogen (Neustart der Abfrage) — kein Befund.
    case abgebrochen
    case sonstig(code: Int)

    public init(urlFehlercode code: Int) {
        switch code {
        case -1001: self = .zeitUeberschritten                       // timedOut
        case -1004: self = .keineVerbindung                          // cannotConnectToHost
        case -1005: self = .abgerissen                               // networkConnectionLost
        case -1009, -1018, -1020: self = .keinNetz                   // notConnectedToInternet,
                                                                     // internationalRoaming-,
                                                                     // dataNotAllowed
        case -1003, -1006: self = .nameUnbekannt                     // cannotFindHost,
                                                                     // dnsLookupFailed
        case -1206 ... -1200: self = .zertifikat                     // secureConnectionFailed
                                                                     // bis clientCertificate-
                                                                     // Required
        case -999: self = .abgebrochen                               // cancelled
        default: self = .sonstig(code: code)
        }
    }

    /// Der Satz für einen Menschen.
    public var satz: String {
        switch self {
        case .zeitUeberschritten:
            return "Heim-PC antwortet nicht — in der Frist kam nichts zurück. Läuft er?"
        case .keineVerbindung:
            return "Heim-PC antwortet nicht — er nimmt keine Verbindung an. Läuft dort der "
                + "Server, und ist der Anschluss richtig?"
        case .abgerissen:
            return "Heim-PC antwortet nicht — die Leitung ist unterwegs abgerissen."
        case .keinNetz:
            return "Dieser Mac ist mit keinem Netz verbunden."
        case .nameUnbekannt:
            return "Tailscale am Mac an? Der Name des Heim-PC ist im Netz nicht zu finden."
        case .zertifikat:
            return "Tailscale am Mac an? Die verschlüsselte Leitung kam nicht zustande "
                + "(das Zertifikat des Heim-PC liess sich nicht prüfen)."
        case .abgebrochen:
            return "Die Leitung wird neu aufgebaut."
        case .sonstig(let code):
            return "Heim-PC antwortet nicht — die Leitung kam nicht zustande (Fehler \(code))."
        }
    }
}

/// Was `GET /api/fortschritt` ergab: eine Antwort (mit der gemessenen Zeit) oder keine.
public enum Leitungsbefund: Equatable, Sendable {
    case antwort(status: Int, millisekunden: Int)
    case keineAntwort(Leitungsfehler)
}

/// Was `GET /api/heim` ergab: eine Antwort (mit ihrem Rumpf) oder keine.
public enum Heimbefund: Equatable, Sendable {
    case antwort(status: Int, daten: Data)
    case keineAntwort(Leitungsfehler)
}

// ========================================================== die Antwort von /api/heim

/// Die Antwort von `GET /api/heim` — **der feste Vertrag** mit dem Visbox-Server (v0.1.7):
///
/// ```json
/// {"blender":     {"da": true, "satz": "…"},
///  "grafikkarte": {"frei_gb": 30.2, "satz": "…"},
///  "assistent":   {"stand": "bereit" | "laedt" | "fehlt" | "aus", "modell": "…", "satz": "…"},
///  "satz": "…"}
/// ```
///
/// **Jeder Teil wird für sich gelesen:** Ist einer nicht in der Form, bleibt er `nil`, und
/// nur seine Zeile sagt «nicht lesbar» — ein kaputter Assistentenblock soll nicht auch
/// den Rechner verschweigen. `da` muss ein echter Wahrheitswert sein (eine `1` ist kein Ja,
/// wie überall im Kern); `frei_gb` darf `null` sein.
public struct Heimbericht: Equatable, Sendable {
    public struct Blender: Equatable, Sendable {
        public let da: Bool
        public let satz: String?
    }

    public struct Grafikkarte: Equatable, Sendable {
        /// Freier Speicher in GB — `nil`: nicht gemeldet (nie «0»).
        public let freiGB: Double?
        public let satz: String?
    }

    public enum Assistentenstand: Equatable, Sendable {
        case bereit, laedt, fehlt, aus
        /// Ein Wort, das dieser Stand der App nicht kennt — er wird gezeigt, nicht geraten.
        case unbekannt(String)

        init(_ wort: String) {
            switch wort {
            case "bereit": self = .bereit
            case "laedt": self = .laedt
            case "fehlt": self = .fehlt
            case "aus": self = .aus
            default: self = .unbekannt(wort)
            }
        }
    }

    public struct Assistent: Equatable, Sendable {
        public let stand: Assistentenstand
        public let modell: String?
        public let satz: String?
    }

    public let blender: Blender?
    public let grafikkarte: Grafikkarte?
    public let assistent: Assistent?
    public let satz: String?

    /// Liest den Bericht — `nil`, wenn die Antwort gar kein JSON-Objekt ist.
    public static func lies(_ daten: Data) -> Heimbericht? {
        guard let wert = try? JSONWert.lies(daten), let feld = wert.alsObjekt else { return nil }

        var blender: Blender?
        if let b = feld["blender"], let da = b["da"]?.alsWahrheit {
            blender = Blender(da: da, satz: b["satz"]?.alsText)
        }
        var grafikkarte: Grafikkarte?
        if let g = feld["grafikkarte"], g.alsObjekt != nil {
            let frei = g["frei_gb"]
            // DA, ABER KEINE ZAHL (etwa ein Text «30 GB»): nicht lesbar. Fehlt es oder ist es
            // `null`, heisst es «nicht gemeldet» — das ist eine Antwort.
            if frei == nil || frei == .null || frei?.alsZahl != nil {
                grafikkarte = Grafikkarte(freiGB: frei?.alsZahl, satz: g["satz"]?.alsText)
            }
        }
        var assistent: Assistent?
        if let a = feld["assistent"], let wort = a["stand"]?.alsText {
            assistent = Assistent(stand: Assistentenstand(wort), modell: a["modell"]?.alsText,
                                  satz: a["satz"]?.alsText)
        }
        return Heimbericht(blender: blender, grafikkarte: grafikkarte, assistent: assistent,
                           satz: feld["satz"]?.alsText)
    }
}

// ===================================================================== die Ableitung

/// Aus dem, was gemessen wurde, die Zeilen — **reine Funktionen**, ohne Uhr und ohne Netz.
public enum Startzeilen {

    /// Die Zeile «Leitung zum Heim-PC» aus `GET /api/fortschritt`.
    ///
    /// * keine Adresse → **wartet** (erst einrichten),
    /// * noch nicht gefragt → **lädt**,
    /// * 200 → **steht**, mit der gemessenen Antwortzeit,
    /// * jede andere Antwort und keine Antwort → **fehlt**, mit dem Grund.
    public static func leitung(_ befund: Leitungsbefund?, adresseDa: Bool,
                               jetzt: Date) -> Zeilenstand {
        guard adresseDa else {
            return .wartet(satz: "Noch keine Adresse des Heim-PC — unter «Einrichten» eintragen.")
        }
        guard let befund = befund else {
            return .laedt(seit: jetzt, satz: "Leitung zum Heim-PC wird aufgebaut")
        }
        switch befund {
        case .antwort(200, let ms):
            return .steht(satz: "verschlüsselt · Antwort in \(max(ms, 0)) ms")
        case .antwort(let status, _):
            return .fehlt(grund: satzZumStatus(status))
        case .keineAntwort(.abgebrochen):
            return .laedt(seit: jetzt, satz: Leitungsfehler.abgebrochen.satz)
        case .keineAntwort(let fehler):
            return .fehlt(grund: fehler.satz)
        }
    }

    /// Die Zeilen «Rechner am Heim-PC» und «Assistent» aus `GET /api/heim`.
    ///
    /// **Fehlt der Weg (404, ein älterer Server), heisst es «wartet», nie «steht»:** Ein
    /// Server, der die Frage nicht kennt, hat nichts über Blender und Assistent gesagt — und
    /// was nicht gesagt ist, steht nicht.
    public static func heim(leitung: Zeilenstand, _ befund: Heimbefund?,
                            jetzt: Date) -> (rechner: Zeilenstand, assistent: Zeilenstand) {
        guard leitung.steht else {
            let s = Zeilenstand.wartet(satz: "Erst wenn die Leitung zum Heim-PC steht.")
            return (s, s)
        }
        guard let befund = befund else {
            let s = Zeilenstand.laedt(seit: jetzt, satz: "Der Heim-PC wird gefragt")
            return (s, s)
        }
        switch befund {
        case .keineAntwort(.abgebrochen):
            let s = Zeilenstand.laedt(seit: jetzt, satz: "Der Heim-PC wird gefragt")
            return (s, s)
        case .keineAntwort(let fehler):
            let s = Zeilenstand.fehlt(grund: fehler.satz)
            return (s, s)
        case .antwort(404, _):
            let s = Zeilenstand.wartet(satz: "Der Heim-PC kennt diese Frage noch nicht "
                                       + "(ein älterer Server).")
            return (s, s)
        case .antwort(200, let daten):
            guard let bericht = Heimbericht.lies(daten) else {
                let s = Zeilenstand.fehlt(grund: "Die Antwort des Heim-PC war nicht lesbar.")
                return (s, s)
            }
            return (rechner(bericht), assistent(bericht, jetzt: jetzt))
        case .antwort(let status, _):
            let s = Zeilenstand.fehlt(grund: satzZumStatus(status))
            return (s, s)
        }
    }

    static func rechner(_ bericht: Heimbericht) -> Zeilenstand {
        guard let blender = bericht.blender else {
            return .fehlt(grund: "Der Heim-PC sagt nicht lesbar, ob Blender da ist.")
        }
        guard blender.da else {
            return .fehlt(grund: Zeilensatz.oder(blender.satz, "Blender fehlt am Heim-PC."))
        }
        let teilBlender = Zeilensatz.oder(blender.satz, "Blender da")
        let teilKarte: String
        if let karte = bericht.grafikkarte {
            let ersatz = karte.freiGB.map { "Grafikkarte frei (\(gb($0)) GB)" }
                ?? "Grafikkarte: freier Speicher nicht gemeldet"
            teilKarte = Zeilensatz.oder(karte.satz, ersatz)
        } else {
            teilKarte = "Grafikkarte: Angabe nicht lesbar"
        }
        return .steht(satz: teilBlender + " · " + teilKarte)
    }

    static func assistent(_ bericht: Heimbericht, jetzt: Date) -> Zeilenstand {
        guard let a = bericht.assistent else {
            return .fehlt(grund: "Der Heim-PC sagt nicht lesbar, wie es um den Assistenten steht.")
        }
        switch a.stand {
        case .bereit:
            let ersatz = a.modell.map { "Sprachmodell geladen · \($0)" } ?? "Sprachmodell geladen"
            return .steht(satz: Zeilensatz.oder(a.satz, ersatz))
        case .laedt:
            return .laedt(seit: jetzt,
                          satz: Zeilensatz.oder(a.satz, "Sprachmodell am Heim-PC wird geladen"))
        case .fehlt:
            return .fehlt(grund: Zeilensatz.oder(a.satz, "Das Sprachmodell fehlt am Heim-PC."))
        case .aus:
            // «AUS» IST KEIN FEHLER: Vor einem Bild wird das Sprachmodell entladen (die
            // Grafikkarte reicht nicht fuer beide), danach kommt es wieder. Was wieder kommt,
            // wartet — der Satz des Servers sagt, worauf.
            return .wartet(satz: Zeilensatz.oder(a.satz, "Der Assistent ist am Heim-PC gerade aus."))
        case .unbekannt(let wort):
            return .fehlt(grund: "Der Heim-PC meldet für den Assistenten «\(wort)» — diesen "
                          + "Zustand kennt diese App nicht.")
        }
    }

    /// Ein Antwortcode, der nicht «200» ist, als Satz.
    static func satzZumStatus(_ status: Int) -> String {
        switch status {
        case 401:
            return "Kennwort stimmt nicht — der Heim-PC weist die Anmeldung ab. Unter "
                + "«Einrichten» neu eingeben."
        case 403:
            return "Der Heim-PC lässt über die Weiterleitung ohne Kennwort niemanden herein — "
                + "dort den Server mit Kennwort starten."
        case 404:
            return "Unter dieser Adresse antwortet ein Server, aber nicht der von \(Marke.name) "
                + "(Code 404). Ist der Anschluss richtig?"
        case 502, 503, 504:
            return "Tailscale erreicht den Heim-PC, aber dort antwortet kein Server "
                + "(Code \(status)) — läuft er?"
        default:
            return "Der Heim-PC antwortet unerwartet (Code \(status))."
        }
    }

    /// Eine Kommazahl mit einer Stelle, mit Punkt — wie auf Blatt 13 («30.2 GB»), und gleich
    /// auf jedem Mac, unabhängig von seiner Spracheinstellung.
    static func gb(_ wert: Double) -> String {
        let zehntel = (wert * 10).rounded()
        let ganz = Int(zehntel) / 10
        let rest = abs(Int(zehntel)) % 10
        return "\(ganz).\(rest)"
    }

    /// «seit 12 s» / «seit 3 min» — die Dauer einer ladenden Zeile.
    public static func seitText(_ seit: Date, jetzt: Date) -> String {
        let sekunden = max(0, Int(jetzt.timeIntervalSince(seit)))
        if sekunden < 60 { return "seit \(sekunden) s" }
        return "seit \(sekunden / 60) min"
    }
}

// ===================================================================== das Ganze

/// Die vier Zeilen zusammen — und was aus ihnen folgt: die Kopfzeile, «Schon anfangen».
public struct Startbild: Equatable, Sendable {
    public var leitung: Zeilenstand
    public var rechner: Zeilenstand
    public var assistent: Zeilenstand
    public var ipad: Zeilenstand

    /// Die iPad-Zeile, solange niemand etwas anderes meldet. Den echten Zustand liefert
    /// die Vermittlung (Strom B); bis dahin wartet die Zeile — **nie «steht»**, weil kein
    /// iPad gesehen wurde.
    public static var ipadVorgabe: Zeilenstand {
        // ENTSCHEID 63 (01.10.2026): Das iPad spricht unterwegs selbst über Tailscale mit
        // dem Heim-PC. Der Mac hat nur eine Aufgabe dabei — die Zahl zum ersten Koppeln.
        .wartet(satz: "\(Marke.name) auf dem iPad öffnen — es verbindet sich selbst über "
                + "Tailscale. Beim ersten Mal: Menü «iPad» → «iPad koppeln», die Zahl am iPad eingeben.")
    }

    public init(leitung: Zeilenstand, rechner: Zeilenstand, assistent: Zeilenstand,
                ipad: Zeilenstand? = nil) {
        self.leitung = leitung
        self.rechner = rechner
        self.assistent = assistent
        self.ipad = ipad ?? Startbild.ipadVorgabe
    }

    /// Alles neu abgeleitet — aus den Befunden und dem vorigen Bild (damit «lädt seit»
    /// weiterzählt, statt bei jeder Abfrage neu zu beginnen).
    public static func aus(leitung befund: Leitungsbefund?, heim: Heimbefund?, adresseDa: Bool,
                           ipad: Zeilenstand?, vorher: Startbild?, jetzt: Date) -> Startbild {
        let l = Startzeilen.leitung(befund, adresseDa: adresseDa, jetzt: jetzt)
            .fortgeschrieben(vorher: vorher?.leitung)
        let h = Startzeilen.heim(leitung: l, heim, jetzt: jetzt)
        return Startbild(leitung: l,
                         rechner: h.rechner.fortgeschrieben(vorher: vorher?.rechner),
                         assistent: h.assistent.fortgeschrieben(vorher: vorher?.assistent),
                         ipad: ipad)
    }

    public subscript(zeile: Startzeile) -> Zeilenstand {
        switch zeile {
        case .leitung: return leitung
        case .rechner: return rechner
        case .assistent: return assistent
        case .ipad: return ipad
        }
    }

    /// Die Zeilen in der Reihenfolge des Blatts.
    public var zeilen: [(zeile: Startzeile, stand: Zeilenstand)] {
        Startzeile.allCases.map { ($0, self[$0]) }
    }

    /// Wie viele Zeilen stehen — **gezählt, nicht geschätzt.**
    public var stehend: Int { zeilen.filter { $0.stand.steht }.count }

    /// Die Kopfzeile, z. B. «baut auf · 2 von 4».
    ///
    /// Das Wort sagt, was die Zeilen **gerade tun**, nicht was man hofft: «bereit», wenn alle
    /// stehen; «unvollständig», wenn eine fehlt (dann baut sie nicht mehr auf); «baut auf»,
    /// solange eine lädt; sonst «wartet» (etwa nur noch auf das iPad, oder auf eine Adresse).
    public var kopfzeile: String {
        let gesamt = zeilen.count
        let wort: String
        if stehend == gesamt {
            wort = "bereit"
        } else if zeilen.contains(where: { $0.stand.fehlt }) {
            wort = "unvollständig"
        } else if zeilen.contains(where: { $0.stand.laedt }) {
            wort = "baut auf"
        } else {
            wort = "wartet"
        }
        return "\(wort) · \(stehend) von \(gesamt)"
    }

    /// «Schon anfangen» (Entscheid 39): geht, **sobald die Leitung steht** — Mappe und Bilder
    /// brauchen nur sie. Der Assistent darf noch laden, das iPad noch fehlen.
    public var schonAnfangen: Bool { leitung.steht }

    /// Der Satz neben dem Knopf.
    public var anfangenSatz: String {
        if !leitung.steht {
            return "Geht, sobald die Leitung zum Heim-PC steht."
        }
        if assistent.steht {
            return "Mappe, Bilder und Assistent sind da."
        }
        return "Mappe und Bilder gehen sofort; der Assistent kommt dazu, sobald er geladen ist."
    }
}

// ==================================================================== der Takt

/// Wie lange bis zur nächsten Abfrage — **5 bis 60 Sekunden, mit wachsendem Abstand**, wie
/// KosmoOrbit es macht («nicht verbunden», still neu versucht, 5 bis 60 s).
///
/// Nach jeder Abfrage, die nichts geändert hat, verdoppelt sich der Abstand bis 60 s; hat
/// sich etwas geändert oder lädt eine Zeile, geht er auf 5 s zurück — wer gerade zusieht,
/// wie der Assistent lädt, soll nicht eine Minute auf das «steht» warten.
public enum Leitungstakt {
    public static let kuerzest: TimeInterval = 5
    public static let laengst: TimeInterval = 60

    public static func naechster(nach vorher: TimeInterval?, geaendert: Bool,
                                 laedt: Bool) -> TimeInterval {
        guard let vorher = vorher, !geaendert, !laedt else { return kuerzest }
        return min(max(vorher, kuerzest) * 2, laengst)
    }
}

// ================================================================ das Signal nach aussen

/// Ob der Heim-PC erreichbar ist, und **seit wann** — das Signal, an dem später der
/// Vorführmodus (Strom C) hängt. Hier wird nur gemeldet, nicht entschieden.
///
/// Erreichbar heisst: Die Leitung **steht** (der Server antwortet mit dem Kennwort). Eine
/// fehlende oder wartende Leitung (auch: keine Adresse, falsches Kennwort) heisst nicht
/// erreichbar — gearbeitet werden kann dann nicht. Lädt die Leitung (erste Abfrage, oder
/// neu aufgebaut), bleibt der bisherige Stand: Ein Nachsehen ist kein Wechsel.
public enum Heimerreichbarkeit: Equatable, Sendable {
    case unbekannt
    case erreichbar(seit: Date)
    case nichtErreichbar(seit: Date)

    public func nach(_ leitung: Zeilenstand, jetzt: Date) -> Heimerreichbarkeit {
        switch leitung {
        case .laedt:
            return self
        case .steht:
            if case .erreichbar = self { return self }
            return .erreichbar(seit: jetzt)
        case .wartet, .fehlt:
            if case .nichtErreichbar = self { return self }
            return .nichtErreichbar(seit: jetzt)
        }
    }

    public var erreichbar: Bool {
        if case .erreichbar = self { return true }
        return false
    }
}

// ============================================================ die Zahl fürs iPad

/// Die Antwort auf `POST /api/kopplung` (Entscheid 63): der Heim-PC öffnet eine Zahl, die das
/// iPad über Tailscale gegen die Anmeldung tauscht. Die Mac-App zeigt sie in der Zeile «iPad».
public enum Koppelzahl {
    /// Die Zeile «iPad» aus der Antwort — oder ein Satz, warum es keine Zahl gibt. **Nie die
    /// Zahl ohne die Adresse:** Am iPad braucht man beides, und die Adresse steht nur am Mac.
    public static func zeile(status: Int, daten: Data, adresse: URL) -> Zeilenstand {
        do {
            let o = try liesAntwort(status: status, daten: daten)
            guard let zahl = o["zahl"]?.alsText, zahl.count == 6,
                  zahl.allSatisfy({ $0.isASCII && $0.isNumber }) else {
                return .fehlt(grund: "Der Heim-PC hat keine Zahl geschickt.")
            }
            let minuten = max(1, Int(((o["gilt_noch_s"]?.alsZahl ?? 600) / 60).rounded()))
            return .wartet(satz: "Zahl fürs iPad: \(gruppiert(zahl)) — gilt \(minuten) min. Am iPad "
                + "im Koppelbildschirm die Adresse \(adresse.absoluteString) und diese Zahl eingeben.")
        } catch let f as Serverfehler {
            return .fehlt(grund: "Keine Zahl fürs iPad: \(f.satz)")
        } catch {
            return .fehlt(grund: "Keine Zahl fürs iPad: die Antwort war nicht lesbar.")
        }
    }

    /// «123 456» — drei und drei, wie man sie abliest.
    static func gruppiert(_ zahl: String) -> String {
        String(zahl.prefix(3)) + " " + String(zahl.suffix(3))
    }
}

