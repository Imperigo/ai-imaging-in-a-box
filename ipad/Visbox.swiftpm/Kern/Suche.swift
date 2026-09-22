import Foundation

// DAS FINDEN DER HOMESTATION — was gefunden wurde, und welche genommen wird.
//
// Die App sucht ueber die Bonjour-Suche des Systems (`Verbindung/Sucher.swift`) und sendet
// selbst keinen Rundruf (Protokoll §8, Entscheid Nr. 27). Was die Suche meldet, wird hier
// zu einem Modell; die Wahl trifft dieser Kern: genau eine gefunden → die; mehrere →
// ein Mensch waehlt. Geraten wird nicht (22.09.2026): *Eine geratene HomeStation bekaeme
// die Skizzen — und das Kennwort — einer anderen.*
//
// Stand 22.09.2026: Der Server kuendigt sich noch NICHT an. Bis er es tut, findet die
// Suche nichts, und die Adresse wird eingetippt (`Suche.adresse(ausEingabe:)`).

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
    /// **Eine Abschrift** von `VORGABE_ANSCHLUSS` in `oberflaeche/server.py`, und sie ist
    /// (22.09.2026) nicht bewacht. Sie gilt nur, wenn beim Eintippen kein Anschluss
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

    /// Eine eingetippte Adresse — `192.168.1.20`, `192.168.1.20:8731`,
    /// `http://homestation.local:8731` — als Adresse für die Anfragen, oder `nil`.
    ///
    /// **Nur `http`.** Der Server spricht kein HTTPS (Protokoll §1); eine `https`-Adresse
    /// scheiterte erst am Gerät und mit einer Meldung, die nichts erklärt. Ein Pfad, eine
    /// Frage oder Anmeldedaten in der Adresse werden abgelehnt, nicht still weggeworfen.
    public static func adresse(ausEingabe eingabe: String) -> URL? {
        var text = eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !text.contains(" ") else { return nil }
        if !text.contains("://") { text = "http://" + text }
        guard let teile = URLComponents(string: text),
              teile.scheme?.lowercased() == "http",
              let rechner = teile.host, !rechner.isEmpty,
              teile.user == nil, teile.password == nil,
              teile.query == nil, teile.fragment == nil,
              teile.path.isEmpty || teile.path == "/" else { return nil }
        let anschluss = teile.port ?? vorgabeAnschluss
        guard (1...65535).contains(anschluss) else { return nil }
        var aus = URLComponents()
        aus.scheme = "http"
        aus.host = rechner
        aus.port = anschluss
        return aus.url
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
