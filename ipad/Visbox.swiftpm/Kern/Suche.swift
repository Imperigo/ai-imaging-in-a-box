import Foundation

// DAS FINDEN DER HOMESTATION — was gefunden wurde, und welche genommen wird.
//
// Die App sucht ueber die Bonjour-Suche des Systems (`Verbindung/Sucher.swift`) und sendet
// selbst keinen Rundruf (Protokoll §8, Entscheid Nr. 27). Was die Suche meldet, wird hier
// zu einem Modell; die Wahl trifft dieser Kern: genau eine gefunden → die; mehrere →
// ein Mensch waehlt. Geraten wird nicht (22.09.2026): *Eine geratene HomeStation bekaeme
// die Skizzen — und das Kennwort — einer anderen.*
//
// Seit dem 22.09.2026 kuendigt sich der Server im Heimnetz an (Protokoll §8). Unterwegs
// findet die Suche nichts — dann wird die Adresse des Heim-PC ueber Tailscale eingetippt
// (`Suche.pruefe(eingabe:)`, Entscheid 63, 01.10.2026).

/// Eine HomeStation, die die Suche gemeldet hat.
public struct GefundenerDienst: Equatable, Hashable, Sendable, Identifiable {
    /// Der Name, unter dem sie sich meldet (Bonjour-Instanzname). Im Heimnetz eindeutig.
    public let name: String
    /// Rechnername oder Adresse — `nil`, solange nicht aufgelöst.
    public let rechner: String?
    /// Anschluss — `nil`, solange nicht aufgelöst.
    public let anschluss: Int?
    /// Die TXT-Einträge, Schlüssel klein geschrieben.
    public let eintraege: [String: String]

    public init(name: String, rechner: String?, anschluss: Int?,
                eintraege: [String: String] = [:]) {
        self.name = name
        self.rechner = rechner
        self.anschluss = anschluss
        var klein: [String: String] = [:]
        for (s, w) in eintraege where klein[s.lowercased()] == nil {
            klein[s.lowercased()] = w
        }
        self.eintraege = klein
    }

    public var id: String { name }

    /// Die Fassung, die der Dienst von sich angibt (TXT `fassung`) — `nil`, wenn er keine
    /// nennt. **Nicht** «die richtige».
    public var fassung: String? { eintraege["fassung"] }

    /// Wer vermittelt (TXT `vermittler`) — `nil`: niemand, der Dienst ist der Server selbst.
    public var vermittler: String? { eintraege["vermittler"] }

    /// Ob unterwegs **der Mac** vermittelt (Protokoll §8b, seit dem 01.10.2026). Nur für die
    /// Anzeige: Gekoppelt und angemeldet wird genau wie bei der HomeStation — der Mac
    /// beantwortet dieselben Wege und reicht sie an den Heim-PC weiter.
    public var ueberDenMac: Bool { vermittler?.lowercased() == Vermittlerangebot.vermittler }

    /// Ob Rechner und Anschluss bekannt sind.
    public var aufgeloest: Bool { adresse != nil }

    /// Die Adresse für die Anfragen — `nil`, solange nicht aufgelöst.
    public var adresse: URL? {
        guard var r = rechner?.trimmingCharacters(in: .whitespaces), !r.isEmpty,
              let a = anschluss, (1...65535).contains(a) else { return nil }
        if r.contains(":") {
            // EINE IPv6-ADRESSE GEHOERT IN KLAMMERN, und ihr Bereich («%en0») muss als
            // «%25» stehen — sonst liest die Adresse das «%» als Kodierung.
            if !r.hasPrefix("[") {
                r = "[" + r.replacingOccurrences(of: "%", with: "%25") + "]"
            }
        }
        return URL(string: "http://\(r):\(a)")
    }

    /// Liest TXT-Einträge in ihrer Leitungsform (RFC 6763, §6): je Eintrag ein Längenbyte
    /// und `schluessel=wert`. Ein Schlüssel ohne `=` steht mit leerem Wert da; kommt ein
    /// Schlüssel zweimal, gilt der erste (so will es die RFC).
    public static func txtEintraege(_ daten: Data) -> [String: String] {
        let bytes = [UInt8](daten)
        var aus: [String: String] = [:]
        var i = 0
        while i < bytes.count {
            let laenge = Int(bytes[i])
            i += 1
            guard laenge > 0 else { continue }
            guard i + laenge <= bytes.count else { break }
            let teil = bytes[i..<(i + laenge)]
            i += laenge
            let schluesselBytes: ArraySlice<UInt8>
            let wert: String
            if let gleich = teil.firstIndex(of: UInt8(ascii: "=")) {
                schluesselBytes = teil[teil.startIndex..<gleich]
                wert = String(decoding: teil[(gleich + 1)...], as: UTF8.self)
            } else {
                schluesselBytes = teil
                wert = ""
            }
            let schluessel = String(decoding: schluesselBytes, as: UTF8.self).lowercased()
            guard !schluessel.isEmpty, aus[schluessel] == nil else { continue }
            aus[schluessel] = wert
        }
        return aus
    }
}

/// Was die Wahl ergibt.
public enum Suchergebnis: Equatable, Sendable {
    /// Keine gefunden.
    case keiner
    /// Genau eine — die wird genommen.
    case einer(GefundenerDienst)
    /// Mehrere — **ein Mensch wählt**, nach Namen geordnet.
    case mehrere([GefundenerDienst])
}

public enum Suche {

    /// Der Anschluss, auf dem der Server ohne Angabe hört.
    ///
    /// **Eine Abschrift** von `VORGABE_ANSCHLUSS` in `oberflaeche/server.py`. Bewacht seit
    /// der Durchsicht vom 22.09.2026: `tests/test_ipad_geruest.py`
    /// (`test_der_vorgabe_anschluss_der_app_ist_der_des_servers`) liest beide und fällt,
    /// sobald sie auseinanderlaufen. Sie gilt nur, wenn beim Eintippen kein Anschluss
    /// angegeben wird; wer einen angibt, ist von ihr unabhängig.
    public static let vorgabeAnschluss = 8731

    /// Wählt aus dem, was die Suche meldet.
    ///
    /// Dieselbe HomeStation kann mehrfach gemeldet werden (über WLAN und Kabel). Gleiche
    /// Namen zählen darum als **eine**; genommen wird die erste aufgelöste Meldung. Erst
    /// was danach mehr als eine ist, sind mehrere — und dann wird **nicht geraten.**
    public static func waehle(_ gefunden: [GefundenerDienst]) -> Suchergebnis {
        var nachName: [String: GefundenerDienst] = [:]
        for d in gefunden {
            if let schon = nachName[d.name], schon.aufgeloest || !d.aufgeloest { continue }
            nachName[d.name] = d
        }
        let eindeutig = nachName.values.sorted {
            ($0.name.lowercased(), $0.name) < ($1.name.lowercased(), $1.name)
        }
        switch eindeutig.count {
        case 0: return .keiner
        case 1: return .einer(eindeutig[0])
        default: return .mehrere(eindeutig)
        }
    }

    /// Eine eingetippte Adresse als Adresse für die Anfragen — oder `nil`. Kurzform von
    /// `pruefe(eingabe:)` für alle, die den Satz nicht brauchen.
    public static func adresse(ausEingabe eingabe: String) -> URL? {
        if case .gut(let url, _) = pruefe(eingabe: eingabe) { return url }
        return nil
    }

    /// Prüft eine eingetippte (oder eingefügte) Adresse — **zwei Formen, und nur diese:**
    ///
    /// * **Im Heimnetz `http`** — `192.168.1.20`, `192.168.1.20:8731`,
    ///   `http://homestation.local:8731`. Ohne Anschluss gilt `vorgabeAnschluss` (8731), der
    ///   des Servers.
    /// * **Unterwegs `https` über Tailscale** (Entscheid 63, 01.10.2026) —
    ///   `https://<rechner>.<netz>.ts.net:8443`. Geprüft von **`Heimadresse.pruefe`**, der
    ///   Prüfung, mit der die Mac-App dieselbe Adresse nimmt: ohne Anschluss 8443, kein Pfad.
    ///   Zwei Prüfungen für dieselbe Adresse hiessen, dass iPad und Mac sie eines Tages
    ///   verschieden lesen.
    ///
    /// **Ohne Schema** gilt `http` — ausser der Name endet auf `.ts.net`: Dann ist es ein Name
    /// aus Tailscale, und dort spricht Tailscale Serve nur `https`. Ein ausdrückliches
    /// `http://` vor einem `.ts.net`-Namen wird abgelehnt, mit Satz: Es scheiterte sonst erst
    /// beim Koppeln, mit einer Meldung, die nichts erklärt.
    ///
    /// **Benutzer und Kennwort in der Adresse** werden in beiden Formen abgelehnt, nicht still
    /// weggeworfen: Die App bekommt sie beim Koppeln und legt sie in den Schlüsselbund; die
    /// Adresse dagegen merkt sie sich offen (`Verbindungsgedaechtnis`). Ebenso abgelehnt: ein
    /// Pfad, eine Frage, ein Anker.
    public static func pruefe(eingabe: String) -> Heimadresse.Pruefung {
        let text = eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            return .schlecht("Die Adresse fehlt. Zuhause sieht sie so aus: 192.168.1.20:8731, "
                             + "unterwegs so: \(Heimadresse.beispiel)")
        }
        guard text.rangeOfCharacter(from: .whitespacesAndNewlines) == nil else {
            return .schlecht("In der Adresse steht ein Leerzeichen.")
        }
        // DIE PLATZHALTER DES BEISPIELS: Den Satz dazu hat die Pruefung des Heim-PC.
        if text.contains("<") || text.contains(">") { return Heimadresse.pruefe(text) }

        let mitSchema: String
        if text.contains("://") {
            mitSchema = text
        } else {
            // OHNE «://» liest `URLComponents` «name:8731» als Schema «name» — darum erst mit
            // `http://` lesen, nur um den Namen zu finden.
            let rechner = URLComponents(string: "http://" + text)?.host ?? ""
            mitSchema = (Strecke.istTailscaleName(rechner) ? "https://" : "http://") + text
        }
        guard let teile = URLComponents(string: mitSchema) else {
            return .schlecht("Das ist keine Adresse. Zuhause sieht sie so aus: "
                             + "192.168.1.20:8731, unterwegs so: \(Heimadresse.beispiel)")
        }
        guard teile.user == nil, teile.password == nil else {
            return .schlecht("Benutzer und Kennwort gehören nicht in die Adresse — die App "
                             + "bekommt sie beim Koppeln und legt sie in den Schlüsselbund.")
        }
        switch teile.scheme?.lowercased() {
        case "https":
            return Heimadresse.pruefe(mitSchema)
        case "http":
            return heimnetzadresse(teile)
        default:
            return .schlecht("Nur http (zuhause im Heimnetz) oder https (unterwegs über "
                             + "Tailscale).")
        }
    }

    /// Die Form im Heimnetz: `http`, ein Rechner, ein Anschluss (ohne Angabe 8731), nichts sonst.
    private static func heimnetzadresse(_ teile: URLComponents) -> Heimadresse.Pruefung {
        guard let rechner = teile.host, !rechner.isEmpty else {
            return .schlecht("Der Name oder die Adresse der HomeStation fehlt.")
        }
        guard !Strecke.istTailscaleName(rechner) else {
            return .schlecht("Ein Name aus Tailscale (…ts.net) geht nur mit https: "
                             + "\(Heimadresse.beispiel)")
        }
        guard teile.path.isEmpty || teile.path == "/" else {
            return .schlecht("Ohne Pfad: Die Adresse endet nach dem Anschluss (\(teile.path) "
                             + "weglassen).")
        }
        guard teile.query == nil, teile.fragment == nil else {
            return .schlecht("Ohne «?» und «#»: Die Adresse endet nach dem Anschluss.")
        }
        let anschluss = teile.port ?? vorgabeAnschluss
        guard (1...65535).contains(anschluss) else {
            return .schlecht("Den Anschluss \(anschluss) gibt es nicht (1 bis 65535).")
        }
        var aus = URLComponents()
        aus.scheme = "http"
        aus.host = rechner
        aus.port = anschluss
        guard let url = aus.url else {
            return .schlecht("Aus «\(rechner)» liess sich keine Adresse bauen.")
        }
        return .gut(url, hinweis: nil)
    }

    /// Eine Adresse, wie ein Mensch sie ins Feld tippt: im Heimnetz **ohne** `http://`, über
    /// Tailscale **mit** `https://` — weil das Schema dort zählt und sichtbar bleiben soll.
    /// `pruefe(eingabe:)` liest beide Formen wieder zur selben Adresse.
    public static func eingabetext(_ adresse: URL) -> String {
        var t = adresse.absoluteString
        if t.lowercased().hasPrefix("http://") { t.removeFirst("http://".count) }
        return t
    }

    /// Ein kurzer Name für die Verbindungszeile: im Heimnetz die Adresse (wie eingetippt),
    /// über Tailscale nur der Rechner — `<rechner>` statt der ganzen `https://…ts.net:8443`;
    /// «über Tailscale» setzt die Zeile dazu (`Strecke.zusatz`).
    public static func anzeigename(_ adresse: URL) -> String {
        guard Strecke(basis: adresse) == .tailscale,
              let rechner = URLComponents(url: adresse, resolvingAgainstBaseURL: false)?.host,
              let erster = rechner.split(separator: ".").first, !erster.isEmpty else {
            return eingabetext(adresse)
        }
        return String(erster)
    }

    /// Liest eine **gemerkte** Adresse (`Verbindungsgedaechtnis`) zurück — samt Schema,
    /// Rechner und Anschluss, **unverändert**: `http://…:8731` bleibt http, `https://…:8443`
    /// bleibt https. Abgelehnt (`nil`) wird nur, was keine Adresse der App sein kann: ein
    /// anderes Schema, kein Rechner, kein Anschluss, Benutzer oder Kennwort, ein Pfad.
    ///
    /// **Nicht neu gebaut**, nur geprüft: Eine über Bonjour gefundene IPv6-Adresse
    /// (`http://[fe80::1%25en0]:8731`) soll genau so wiederkommen, wie sie gemerkt wurde.
    public static func gemerkt(_ text: String?) -> URL? {
        guard let text, let url = URL(string: text),
              let teile = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let schema = teile.scheme?.lowercased(), schema == "http" || schema == "https",
              let rechner = teile.host, !rechner.isEmpty,
              let anschluss = teile.port, (1...65535).contains(anschluss),
              teile.user == nil, teile.password == nil,
              teile.query == nil, teile.fragment == nil,
              teile.path.isEmpty || teile.path == "/" else { return nil }
        return url
    }
}

// ================================================================= wer die Suche will

/// **Wer** gerade will, dass gesucht wird — die Suche läuft, solange es einer will.
///
/// Zwei wollen es aus verschiedenen Gründen: der Koppelbildschirm, solange er offen ist,
/// und das Prüfen, solange die gekoppelte HomeStation nicht antwortet (sie hat vielleicht
/// eine neue Adresse). Bis zur Durchsicht vom 22.09.2026 gab es nur ein «an» und ein
/// «aus»: Schloss ein Mensch den Koppelbildschirm, endete damit auch die Suche, die das
/// Prüfen gestartet hatte — und eine HomeStation mit neuer Adresse wurde nicht mehr
/// wiedergefunden. `SucheTests.testSchliesstDerKoppelbildschirmSuchtDasPruefenWeiter`
/// bewacht es.
public struct Suchwunsch: Equatable, Sendable {
    public enum Anlass: Hashable, Sendable {
        /// Der Koppelbildschirm ist offen.
        case koppeln
        /// Die gekoppelte HomeStation antwortet nicht; sie wird am Namen wiedergesucht.
        case wiederfinden
    }

    public private(set) var anlaesse: Set<Anlass> = []

    public init() {}

    /// Ob gesucht werden soll.
    public var sucht: Bool { !anlaesse.isEmpty }

    /// Ein Anlass will die Suche. Gibt zurück, ob sie **dadurch** beginnt.
    @discardableResult
    public mutating func verlange(_ anlass: Anlass) -> Bool {
        let vorher = sucht
        anlaesse.insert(anlass)
        return !vorher && sucht
    }

    /// Ein Anlass will sie nicht mehr. Gibt zurück, ob sie **dadurch** endet — nur, wenn
    /// kein anderer sie noch will.
    @discardableResult
    public mutating func gibFrei(_ anlass: Anlass) -> Bool {
        let vorher = sucht
        anlaesse.remove(anlass)
        return vorher && !sucht
    }
}

// ================================================================= der Verbindungsstand

/// Was die Statusanzeige sagt — **vier Fälle, und keiner behauptet mehr, als bekannt ist.**
///
/// Die Lehre, angewandt auf die Verbindung (22.09.2026): «Gekoppelt» steht erst da, wenn
/// die HomeStation **geantwortet** hat. Eine gespeicherte Anmeldung allein heisst nur, dass
/// es einmal ging; bis zur ersten Antwort sucht die App.
public enum Verbindungszustand: Equatable, Sendable {
    /// Nicht gekoppelt, und es wird nicht gesucht.
    case aus
    /// Es wird gesucht — oder eine gekoppelte HomeStation hat noch nicht geantwortet.
    case suche
    /// Gekoppelt, und die letzte Anfrage kam an.
    case gekoppelt
    /// Gekoppelt, aber die letzte Anfrage kam nicht an — mit dem Grund.
    case getrennt(grund: String)

    /// Leitet den Zustand ab.
    ///
    /// - Parameters:
    ///   - gekoppelt: ob eine HomeStation gemerkt ist (Adresse, und wo nötig Anmeldung).
    ///   - sucht: ob gerade gesucht wird.
    ///   - erreichbar: `true` die letzte Anfrage kam an, `false` nicht, `nil` **noch nicht
    ///     gefragt** — nie still `false`.
    ///   - grund: warum nicht erreichbar.
    public static func bestimme(gekoppelt: Bool, sucht: Bool, erreichbar: Bool?,
                                grund: String?) -> Verbindungszustand {
        guard gekoppelt else { return sucht ? .suche : .aus }
        switch erreichbar {
        case .some(true): return .gekoppelt
        case .some(false): return .getrennt(grund: grund ?? "Die HomeStation antwortet nicht.")
        case .none: return .suche
        }
    }

    /// Das Wort, das ein Mensch sieht.
    public var wort: String {
        switch self {
        case .aus: return "Aus"
        case .suche: return "Suche"
        case .gekoppelt: return "Gekoppelt"
        case .getrennt: return "Getrennt"
        }
    }

    /// Ob jetzt gesendet werden darf: **nur** gekoppelt. Bei «Suche» ist nicht bekannt,
    /// ob drüben jemand ist — dann bleibt die Skizze im Fach.
    public var darfSenden: Bool { self == .gekoppelt }
}
