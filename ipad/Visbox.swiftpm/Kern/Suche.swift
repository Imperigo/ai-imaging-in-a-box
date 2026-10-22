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
    /// Warum das Auflösen scheiterte — `nil`, solange es läuft oder gelungen ist.
    ///
    /// **Der Anlass** (erster Gerätetest, 13.10.2026, iPadOS 26.7.2): Der Eintrag «über den
    /// Mac» stand endlos auf «wird aufgelöst …», ohne Grund und ohne Abbruch — ein Auflösen,
    /// das scheiterte, liess den Dienst einfach ohne Adresse stehen. Jetzt hat es eine Frist
    /// (`Suche.aufloesFrist`) und danach einen Satz (`Suche.satzNichtAufgeloest`).
    public let grund: String?

    public init(name: String, rechner: String?, anschluss: Int?,
                eintraege: [String: String] = [:], grund: String? = nil) {
        self.name = name
        self.rechner = rechner
        self.anschluss = anschluss
        self.grund = grund
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

    /// Der Fingerabdruck des Zertifikats, den der Dienst nennt (TXT `abdruck`, seit dem
    /// 22.10.2026) — **die feste Kennung des Mac**, an der das iPad ihn wiedererkennt, auch wenn
    /// sein Name wechselt (`Macanbindung.gekoppelterMac`). `nil`: keiner, oder keine 64 Hex-Stellen
    /// (ein Mac mit altem Stand — dann gilt weiter der Name).
    public var abdruck: String? {
        eintraege[Vermittlerangebot.abdruckSchluessel].flatMap(Fingerabdruck.normalisiere)
    }

    /// Ob der Dienst **verschlüsselt** spricht (TXT `tls=1`). Seit Entscheid 118 (21.10.2026)
    /// tut das der Mac für das iPad; der Heim-PC tut es im Heim-WLAN nur für den Mac
    /// (`--heimnetz`, Entscheid 83b) — das iPad nimmt den nicht (`nurFuerDenMac`).
    public var verschluesselt: Bool { eintraege["tls"] == "1" }

    /// Ein verschlüsselter Zuhörer **des Heim-PC** im WLAN (`tls=1`, ohne `vermittler`): Er
    /// ist für die Mac-App da, die sein Zertifikat beim Koppeln anheftet. Das iPad spricht nie
    /// mit ihm — es arbeitet über den Mac (Entscheid 118).
    public var nurFuerDenMac: Bool { verschluesselt && !ueberDenMac }

    /// Ob Rechner und Anschluss bekannt sind.
    public var aufgeloest: Bool { adresse != nil }

    /// Die Adresse für die Anfragen — `nil`, solange nicht aufgelöst. **`https`, wenn der Dienst
    /// verschlüsselt spricht** (`tls=1`), sonst `http`.
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
        return URL(string: (verschluesselt ? "https" : "http") + "://\(r):\(a)")
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

    /// Wie lange das Auflösen eines Fundes dauern darf — **gesetzt, 5 s** (Gerätetest vom
    /// 13.10.2026): Im eigenen WLAN antwortet ein Dienst in Bruchteilen einer Sekunde; wer
    /// fünf Sekunden schweigt, kommt nicht mehr.
    public static let aufloesFrist: TimeInterval = 5

    /// Der Satz, wenn ein Fund nicht aufgelöst wurde — **mit Grund und dem vorgesehenen
    /// Weg**: Seit Entscheid 63 spricht das iPad direkt über Tailscale mit dem Heim-PC; der
    /// Weg über den Mac ist aus, bis man ihn einschaltet, und unverschlüsselt.
    public static func satzNichtAufgeloest(ueberDenMac: Bool) -> String {
        let wer = ueberDenMac ? "Der Mac" : "Dieser Heim-PC"
        // SEIT ENTSCHEID 118 (21.10.2026) ist der Mac der Weg — nicht mehr Tailscale direkt
        // zum Heim-PC. Der Satz schickt darum zum Mac und zum QR-Code.
        return "\(wer) antwortet nicht (nach \(Int(aufloesFrist)) s abgebrochen). Darf "
            + "\(Marke.name) ins lokale Netzwerk? Einstellungen › Datenschutz & Sicherheit › "
            + "Lokales Netzwerk › \(Marke.name). Sonst am Mac «iPad koppeln» öffnen und den "
            + "QR-Code lesen."
    }

    /// Was rechts im Fund steht: die Adresse, «wird aufgelöst …» oder «nicht erreicht».
    public static func fundtext(_ d: GefundenerDienst) -> String {
        if let a = d.adresse { return eingabetext(a) }
        return d.grund == nil ? "wird aufgelöst …" : "nicht erreicht"
    }

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
        // EIN DIREKTER HEIM-PC VOR EINEM «UEBER DEN MAC» (Geraetetest 13.10.2026): Der
        // direkte Weg ist der vorgesehene (Entscheid 63); der Mac vermittelt nur, wenn man ihn
        // eingeschaltet hat. Innerhalb beider Gruppen nach Namen.
        let eindeutig = nachName.values.sorted {
            ($0.ueberDenMac ? 1 : 0, $0.name.lowercased(), $0.name)
                < ($1.ueberDenMac ? 1 : 0, $1.name.lowercased(), $1.name)
        }
        switch eindeutig.count {
        case 0: return .keiner
        case 1: return .einer(eindeutig[0])
        default: return .mehrere(eindeutig)
        }
    }

    /// **Die Wahl zum Koppeln seit Entscheid 118:** nur Macs, die verschlüsselt sprechen
    /// (`ueberDenMac` und `verschluesselt`). Ein Heim-PC wird nicht mehr angeboten — das iPad
    /// arbeitet immer über den Mac —, und ein Mac mit altem Stand (ohne `tls=1`) auch nicht: Mit
    /// ihm ginge die Leitung unverschlüsselt. Er steht in `alteMacs`, damit der Bildschirm sagen
    /// kann, warum er fehlt.
    public static func waehleMac(_ gefunden: [GefundenerDienst]) -> Suchergebnis {
        waehle(gefunden.filter { $0.ueberDenMac && $0.verschluesselt })
    }

    /// Die Macs mit altem Stand: sie vermitteln, aber unverschlüsselt.
    public static func alteMacs(_ gefunden: [GefundenerDienst]) -> [GefundenerDienst] {
        var namen = Set<String>()
        return gefunden.filter { d in
            guard d.ueberDenMac, !d.verschluesselt, !namen.contains(d.name) else { return false }
            namen.insert(d.name)
            return true
        }
    }

    /// Der Satz zu einem Mac mit altem Stand.
    public static func satzAlterMac(_ name: String) -> String {
        "«\(name)» bietet sich noch unverschlüsselt an (alter Stand). Die Mac-App aktualisieren — "
            + "das iPad koppelt nur verschlüsselt."
    }

    /// Prüft die Adresse **eines Mac** — wie sie im Koppelschein steht oder eingetippt wird
    /// (Entscheid 118): **nur `https`** (ohne Schema gilt `https`), ein Rechner, ein Anschluss
    /// (ohne Angabe `vorgabeAnschluss`), nichts sonst. Ein ausdrückliches `http://` wird mit
    /// Satz abgelehnt: Die Leitung zum Mac ist verschlüsselt, und ein Rückfall auf
    /// unverschlüsselt geschieht nie still.
    public static func pruefeMac(eingabe: String) -> Heimadresse.Pruefung {
        let text = eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            return .schlecht("Die Adresse des Mac fehlt. Sie steht im Koppelfenster am Mac.")
        }
        guard text.rangeOfCharacter(from: .whitespacesAndNewlines) == nil else {
            return .schlecht("In der Adresse steht ein Leerzeichen.")
        }
        let mitSchema = text.contains("://") ? text : "https://" + text
        guard let teile = URLComponents(string: mitSchema) else {
            return .schlecht("Das ist keine Adresse. Sie steht im Koppelfenster am Mac.")
        }
        guard teile.scheme?.lowercased() == "https" else {
            return .schlecht("Nur verschlüsselt: Die Adresse des Mac beginnt mit https:// — "
                             + "unverschlüsselt koppelt das iPad nicht mehr.")
        }
        guard teile.user == nil, teile.password == nil else {
            return .schlecht("Benutzer und Kennwort gehören nicht in die Adresse — die App "
                             + "bekommt sie beim Koppeln und legt sie in den Schlüsselbund.")
        }
        guard let rechner = teile.host, !rechner.isEmpty else {
            return .schlecht("Der Name oder die Adresse des Mac fehlt.")
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
        aus.scheme = "https"
        aus.host = rechner
        aus.port = anschluss
        guard let url = aus.url else {
            return .schlecht("Aus «\(rechner)» liess sich keine Adresse bauen.")
        }
        return .gut(url, hinweis: nil)
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

    /// Ob der Koppelbildschirm **Nähe und QR-Code** anbietet: ungekoppelt immer, gekoppelt nur,
    /// wenn der gemerkte Mac **nicht erreichbar** ist (`getrennt`) — dann als «Neu koppeln».
    ///
    /// **Der Anlass** (Demolauf 22.10.2026, iPad 0.3.34): Getrennt, aber noch gekoppelt, zeigte
    /// der Bildschirm nur Adresse, Zahl und «Trennen» — kein Weg zum Neukoppeln ohne erst zu
    /// trennen. Neu koppeln ersetzt die alte Kopplung **erst, wenn die neue gelingt**
    /// (`Verbindungsstand.koppele` merkt erst nach Erfolg und Gegenprobe). Bei «Suche» (noch nicht
    /// gefragt) nicht: Das dauert Sekunden, und die Nähe soll nicht bei jedem Öffnen anspringen.
    public static func bietetKoppeln(gekoppelt: Bool, zustand: Verbindungszustand) -> Bool {
        guard gekoppelt else { return true }
        if case .getrennt = zustand { return true }
        return false
    }

    /// Der Satz über «Neu koppeln», wenn der gekoppelte Mac nicht antwortet.
    public static let satzNeuKoppeln = "Der gekoppelte Mac antwortet nicht. Neu koppeln geht ohne "
        + "Trennen: Die alte Kopplung gilt, bis die neue gelungen ist."

    /// Ob jetzt gesendet werden darf: **nur** gekoppelt. Bei «Suche» ist nicht bekannt,
    /// ob drüben jemand ist — dann bleibt die Skizze im Fach.
    public var darfSenden: Bool { self == .gekoppelt }
}

// ============================================================ ein Aussetzer ist kein Zustand

/// **Ein kurzer Aussetzer trennt nicht** (Owner-Befund vom 20.10.2026): Unterwegs über
/// Mobilfunk und Tailscale zeigten Mac und iPad «antwortet nicht», während der Heim-PC gesund
/// war — eine einzige Anfrage, die ihre Frist verpasste, genügte. Seither gilt am iPad
/// **dieselbe Schwelle wie am Mac** (`Leitungsschalter.schwelleErreicht`): Eine HomeStation,
/// die eben noch antwortete, gilt erst nach drei Fehlschlägen in Folge **und** 30 Sekunden
/// ohne Antwort als nicht erreichbar.
///
/// Geprüft wird weiter in jeder Runde, und eine Antwort holt sofort zurück. Gesendet wird
/// während des Aussetzers nicht aus dem Parkfach (`roh` sagt, ob die letzte Anfrage ankam);
/// nur der angezeigte Zustand bleibt «Gekoppelt».
public struct Aussetzerfilter: Equatable, Sendable {
    public private(set) var fehlschlaege = 0
    /// Seit wann keine Antwort kam — der erste Fehlschlag nach der letzten Antwort.
    public private(set) var seit: Date?
    /// Ob die HomeStation seit dem Start je antwortete. Vorher gibt es nichts zu überbrücken.
    public private(set) var warErreichbar = false
    /// Was die letzte Anfrage ergab — ungefiltert.
    public private(set) var roh: Bool?

    public init() {}

    /// Eine Anfrage kam an (`true`) oder nicht (`false`).
    public mutating func melde(erreicht: Bool, jetzt: Date) {
        roh = erreicht
        if erreicht {
            fehlschlaege = 0
            seit = nil
            warErreichbar = true
        } else {
            fehlschlaege += 1
            if seit == nil { seit = jetzt }
        }
    }

    /// Von vorn — nach neuem Koppeln oder Trennen.
    public mutating func vergiss() {
        self = Aussetzerfilter()
    }

    /// Was als «erreichbar» gilt: die letzte Antwort — **ausser** während eines kurzen
    /// Aussetzers nach einer Antwort; dann noch `true`. `nil`: noch nicht gefragt.
    public func erreichbar(jetzt: Date) -> Bool? {
        guard let roh else { return nil }
        if roh { return true }
        guard warErreichbar, let seit else { return false }
        return !Leitungsschalter.schwelleErreicht(fehlschlaege: fehlschlaege,
                                                  stille: jetzt.timeIntervalSince(seit))
    }

    /// Ob gerade ein Aussetzer überbrückt wird.
    public func kurzWeg(jetzt: Date) -> Bool {
        roh == false && erreichbar(jetzt: jetzt) == true
    }
}
