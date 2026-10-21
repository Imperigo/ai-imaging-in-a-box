import Foundation

// DER MAC KOPPELT SICH SELBST (Owner-Entscheid 83, 13.10.2026, Blatt 17 der Entwurfsflaeche).
//
// Bis dahin verlangte «Einrichten» drei Felder: die Adresse des Heim-PC, den Benutzer und das
// Kennwort aus dem Fenster am Heim-PC. Der Owner wollte das nicht eintippen. Jetzt:
//
//   1. Der Mac SUCHT den Heim-PC selbst — im eigenen Tailscale-Netz (die Liste der Geraete
//      aus `tailscale status --json`) und im Heim-WLAN (Bonjour, `Marke.dienst` mit `tls=1`).
//      Wer auf `GET /api/hallo` als Visbox-Heim-PC antwortet, ist waehlbar.
//   2. «Weiter» fordert eine ZAHL an (`POST /api/kopplung/anfordern`). Sie erscheint am
//      Heim-PC — im Fenster und als Mitteilung —, nie in der Antwort.
//   3. Die Zahl geht an `POST /api/verbinden`; zurueck kommen Benutzer, Kennwort und der
//      kuenftige Zugang (Adresse, im WLAN dazu der Fingerabdruck des Zertifikats).
//
// Was davon Entscheidung ist und nicht Senden, steht HIER, mit Proben unter Linux: welche
// Geraete Kandidaten sind, was eine Antwort heisst, wann die Zahl geschlossen ist, ob ein
// Zertifikat das angeheftete ist. Die Mac-App sendet nur und zeigt (`Start/Koppeln.swift`).

/// Die Regeln der Zahl, die sich der Mac anfordert — **Abschrift** von
/// `aiimaging.kopplung` (`FRIST_ANGEFORDERT_S`, `VERSUCHE_ANGEFORDERT`,
/// `DROSSEL_ANGEFORDERT_S`) und `server.VORGABE_HEIMNETZ_ANSCHLUSS`, bewacht in
/// `tests/test_ipad_geruest.py`.
public enum Heimkopplung {
    /// Wie lange die Zahl gilt — fünf Minuten (Entscheid 83).
    public static let frist: TimeInterval = 300
    /// Wie oft geraten werden darf — drei Versuche (Entscheid 83).
    public static let versuche = 3
    /// Wie oft eine neue Zahl kommt — höchstens eine je 30 s.
    public static let drossel: TimeInterval = 30
    /// Der Anschluss des verschlüsselten Zuhörers im Heim-WLAN (`--heimnetz`). Gefunden wird
    /// er über Bonjour, wo der Anschluss mitkommt; die Zahl hier ist nur die Vorgabe.
    public static let heimnetzAnschluss = 8732
    /// Wie lange ein Kandidat für `hallo` hat — **gesetzt**: Ein Heim-PC im eigenen Netz
    /// antwortet in Bruchteilen einer Sekunde; wer länger schweigt, ist keiner oder schläft.
    public static let halloFrist: TimeInterval = 3
    /// Höchstens so viele Tailscale-Geräte werden gefragt — ein grosses Netz soll die Suche
    /// nicht in hundert Anfragen verwandeln.
    public static let hoechstensGeraete = 32

    /// Wo die Befehlszeile von Tailscale am Mac liegt, **in dieser Reihenfolge versucht.**
    ///
    /// Geprüft in der Tailscale-Doku (`tailscale.com/kb/1080/cli`, 13.10.2026):
    /// * **App-Store-Fassung:** «the CLI is bundled inside the Tailscale app» —
    ///   `/Applications/Tailscale.app/Contents/MacOS/Tailscale`.
    /// * **Standalone-Fassung:** dasselbe Bündel unter `/Applications`; die Doku nennt
    ///   ausdrücklich nur den Starter `/usr/local/bin/tailscale`, den man in den
    ///   Einstellungen der App installiert. Darum beide.
    /// * **Homebrew (`tailscaled`, quelloffen):** in der Doku ohne macOS-Pfad;
    ///   `/opt/homebrew/bin/tailscale` ist der übliche Ort, **nicht belegt.**
    public static let tailscaleProgramme = [
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
        "/usr/local/bin/tailscale",
        "/opt/homebrew/bin/tailscale",
    ]

    /// Die Satz bei geschlossener Zahl — vom Mac selbst gezählt, nicht vom Server gehört:
    /// Der Server sagt absichtlich nicht, wie viele Versuche übrig sind (Protokoll §7).
    public static let satzGeschlossen = "Nach drei Fehlversuchen ist die Zahl geschlossen. "
        + "«Neue Zahl anfordern» — sie erscheint wieder am Heim-PC."
}

// ============================================================ Tailscale-Geräte

/// Ein Gerät aus `tailscale status --json` (Feld `Peer`).
public struct Tailscalegeraet: Equatable, Sendable {
    /// `HostName` — nur zur Anzeige.
    public let name: String
    /// `DNSName` **ohne** den Punkt am Ende (`heim-pc.beispiel.ts.net`).
    public let dnsName: String
    public let online: Bool
    /// `OS` — `linux`, `windows`, `macOS`, `iOS`, `android`.
    public let system: String

    public init(name: String, dnsName: String, online: Bool, system: String) {
        self.name = name
        self.dnsName = dnsName
        self.online = online
        self.system = system
    }
}

public enum Tailscalestatus {
    /// Die Geräte aus der Ausgabe von `tailscale status --json` — `nil`, wenn sie nicht
    /// lesbar ist (dann sagt die Suche das, statt «keine gefunden»).
    ///
    /// Gelesen wird nur `Peer` (die **anderen** Geräte; `Self` ist dieser Mac). Fehlende
    /// Felder machen ein Gerät nicht unlesbar, nur ohne Namen.
    public static func geraete(aus daten: Data) -> [Tailscalegeraet]? {
        guard let wurzel = try? JSONWert.lies(daten), let o = wurzel.alsObjekt else {
            return nil
        }
        guard let peers = o["Peer"] else { return [] }
        if peers.istNull { return [] }
        guard let liste = peers.alsObjekt else { return nil }
        return liste.keys.sorted().compactMap { schluessel in
            guard let p = liste[schluessel]?.alsObjekt else { return nil }
            var dns = p["DNSName"]?.alsText ?? ""
            while dns.hasSuffix(".") { dns.removeLast() }
            return Tailscalegeraet(name: p["HostName"]?.alsText ?? dns,
                                   dnsName: dns.lowercased(),
                                   online: p["Online"]?.alsWahrheit ?? false,
                                   system: p["OS"]?.alsText ?? "")
        }
    }

    /// Die Kandidaten unter den Geräten: **online**, mit Namen, und kein Telefon oder
    /// Tablet (iOS, Android — ein Heim-PC ist keines). Je einer `https://<DNSName>:8443`.
    public static func kandidaten(_ geraete: [Tailscalegeraet],
                                  anschluss: Int = Heimadresse.vorgabeAnschluss)
        -> [Heimkandidat] {
        let ohneMobil = Set(["ios", "android"])
        var gesehen = Set<String>()
        var aus: [Heimkandidat] = []
        for g in geraete where g.online && !g.dnsName.isEmpty
            && !ohneMobil.contains(g.system.lowercased()) {
            guard !gesehen.contains(g.dnsName),
                  case .gut(let url, _) = Heimadresse.pruefe("https://\(g.dnsName):\(anschluss)")
            else { continue }
            gesehen.insert(g.dnsName)
            aus.append(Heimkandidat(anzeigename: g.name, adresse: url, weg: .tailscale))
            if aus.count >= Heimkopplung.hoechstensGeraete { break }
        }
        return aus
    }
}

// ============================================================ Kandidaten

/// Wie der Mac den Heim-PC erreicht.
public enum Heimweg: String, Equatable, Sendable {
    /// Über Tailscale Serve — das Zertifikat prüft das System (Tailscale stellt es aus).
    case tailscale
    /// Im Heim-WLAN, über den verschlüsselten Zuhörer — selbst unterschrieben, **angeheftet.**
    case heimnetz
}

/// Was `GET /api/hallo` sagt.
public struct Hallo: Equatable, Sendable {
    public let fassung: String
    public let name: String

    /// Nur eine 200 mit `visbox: true` ist ein Visbox-Heim-PC. Alles andere — ein anderer
    /// Dienst auf 8443, ein älterer Visbox-Server ohne `hallo` (404) — ist keiner.
    public static func lies(status: Int, daten: Data) -> Hallo? {
        guard status == 200, let o = (try? JSONWert.lies(daten))?.alsObjekt,
              o[Marke.name.lowercased()]?.alsWahrheit == true else { return nil }
        return Hallo(fassung: o["fassung"]?.alsText ?? "?",
                     name: o["name"]?.alsText ?? "\(Marke.name) Heim-PC")
    }
}

/// Wie es um einen Kandidaten steht.
public enum Kandidatenstand: Equatable, Sendable {
    case gefragt
    /// Antwortet als Visbox-Heim-PC. `fingerabdruck`: im WLAN das Zertifikat, das der Mac im
    /// Handschlag sah — noch **nicht** angeheftet, das geschieht erst nach der Kopplung.
    case antwortet(Hallo, fingerabdruck: String?)
    /// Antwortet nicht, oder nicht als Visbox — mit Satz.
    case stumm(String)
}

/// Ein möglicher Heim-PC in der Liste von Blatt 17.
public struct Heimkandidat: Equatable, Sendable, Identifiable {
    public let anzeigename: String
    public let adresse: URL
    public let weg: Heimweg
    public var stand: Kandidatenstand

    public var id: String { weg.rawValue + " " + adresse.absoluteString }

    public init(anzeigename: String, adresse: URL, weg: Heimweg,
                stand: Kandidatenstand = .gefragt) {
        self.anzeigename = anzeigename
        self.adresse = adresse
        self.weg = weg
        self.stand = stand
    }

    /// **Nur antwortende sind wählbar** (Blatt 17).
    public var waehlbar: Bool {
        if case .antwortet = stand { return true }
        return false
    }

    /// Der Satz unter dem Namen.
    public var satz: String {
        switch stand {
        case .gefragt:
            return "wird gefragt …"
        case .antwortet(let hallo, let abdruck):
            let wo = weg == .tailscale ? "über Tailscale" : "im WLAN, verschlüsselt"
            if let abdruck { return "\(wo) · Fassung \(hallo.fassung) · Zeichen "
                + Fingerabdruck.zeichen(abdruck) }
            return "\(wo) · Fassung \(hallo.fassung)"
        case .stumm(let grund):
            return grund
        }
    }

    /// Ein Fund der Bonjour-Suche — **nur mit `tls=1`**. Ein Server mit `--im-heimnetz`
    /// kündigt denselben Dienst unverschlüsselt an (für das iPad); mit ihm koppelt der Mac
    /// nicht, sonst ginge das Kennwort im Klartext durch das WLAN (Entscheid 83b).
    public static func ausBonjour(name: String, host: String, anschluss: Int,
                                  txt: [String: String]) -> Heimkandidat? {
        guard txt["tls"] == "1", (1...65535).contains(anschluss) else { return nil }
        // EIN MAC, DER SICH DEM IPAD ANBIETET (Entscheid 118), spricht seit 21.10.2026 auch
        // verschluesselt — er ist aber kein Heim-PC und gehoert nicht in diese Liste.
        guard txt["vermittler"] == nil else { return nil }
        var h = host
        // EINE IPv6-ADRESSE MIT ZONE («fe80::1%en0») kann keine Adresse tragen; die Zone
        // gilt nur auf diesem Mac. Bonjour liefert sie, `URL` nicht — also ohne.
        if let prozent = h.firstIndex(of: "%") { h = String(h[..<prozent]) }
        if h.contains(":") && !h.hasPrefix("[") { h = "[\(h)]" }
        guard !h.isEmpty, let url = URL(string: "https://\(h):\(anschluss)") else { return nil }
        return Heimkandidat(anzeigename: name, adresse: url, weg: .heimnetz)
    }

    /// Den Kandidaten mit seiner `hallo`-Antwort — oder ohne (`status == nil`: keine Antwort).
    public func nach(halloStatus status: Int?, daten: Data, fingerabdruck: String?,
                     grund: String? = nil) -> Heimkandidat {
        var neu = self
        if let status, let hallo = Hallo.lies(status: status, daten: daten) {
            if weg == .heimnetz {
                // IM WLAN OHNE GESEHENES ZERTIFIKAT kein Vertrauen beim ersten Mal — es gäbe
                // nichts anzuheften.
                guard let abdruck = fingerabdruck.flatMap(Fingerabdruck.normalisiere) else {
                    neu.stand = .stumm("antwortet, aber das Zertifikat war nicht lesbar")
                    return neu
                }
                neu.stand = .antwortet(hallo, fingerabdruck: abdruck)
            } else {
                neu.stand = .antwortet(hallo, fingerabdruck: nil)
            }
        } else if let status {
            neu.stand = .stumm(status == 404
                ? "antwortet, aber nicht als \(Marke.name)-Heim-PC (oder ein älterer Server)"
                : "antwortet, aber nicht als \(Marke.name)-Heim-PC (\(status))")
        } else {
            neu.stand = .stumm(grund ?? "antwortet nicht")
        }
        return neu
    }
}

/// Die Liste der Kandidaten — Tailscale und WLAN zusammen, **ohne Doppel.**
public struct Heimsuche: Equatable, Sendable {
    public private(set) var kandidaten: [Heimkandidat] = []

    public init() {}

    /// Kandidaten aufnehmen; ein schon bekannter (gleiche `id`) behält seinen Stand.
    public mutating func nimm(_ neue: [Heimkandidat]) {
        for k in neue where !kandidaten.contains(where: { $0.id == k.id }) {
            kandidaten.append(k)
        }
    }

    /// Den Stand eines Kandidaten ersetzen.
    public mutating func setze(_ k: Heimkandidat) {
        if let i = kandidaten.firstIndex(where: { $0.id == k.id }) { kandidaten[i] = k }
    }

    public var waehlbare: [Heimkandidat] { kandidaten.filter(\.waehlbar) }
}

// ============================================================ Zahl anfordern

/// Was `POST /api/kopplung/anfordern` sagt.
public enum Anforderungsergebnis: Equatable, Sendable {
    /// Die Zahl steht am Heim-PC. `neu`: eben erzeugt (dann zählt der Mac von vorn).
    case angezeigt(satz: String, neu: Bool)
    /// Gedrosselt, und keine Zahl gilt — in `sekunden` gibt es eine neue.
    case warten(satz: String, sekunden: Int)
    case abgelehnt(satz: String)

    public static func lies(status: Int, daten: Data) -> Anforderungsergebnis {
        let o = (try? JSONWert.lies(daten))?.alsObjekt ?? [:]
        let satz = o["satz"]?.alsText ?? o["fehler"]?.alsText
        if status == 200, o["angezeigt"]?.alsWahrheit == true {
            return .angezeigt(satz: satz ?? "Die Zahl steht am Heim-PC.",
                              neu: o["neu"]?.alsWahrheit ?? true)
        }
        if status == 429 {
            let s = o["warten_s"]?.alsGanz ?? Int(Heimkopplung.drossel)
            return .warten(satz: satz ?? "Eine neue Zahl gibt es in \(s) s.", sekunden: s)
        }
        if status == 404 {
            return .abgelehnt(satz: "Dieser Heim-PC kennt das Koppeln mit Zahl noch nicht "
                + "(älterer Server). Am Heim-PC aktualisieren — oder von Hand eintragen.")
        }
        return .abgelehnt(satz: satz ?? "Der Heim-PC gab keine Zahl heraus (\(status)).")
    }
}

// ============================================================ verbinden

/// Was der Mac nach der Kopplung **behält**: wohin, mit welcher Anmeldung, und im WLAN
/// welchen Fingerabdruck er annimmt.
public struct Heimzugang: Equatable, Sendable {
    public let adresse: URL
    public let anmeldung: Anmeldung
    /// `nil` über Tailscale (das System prüft das Zertifikat); im WLAN der angeheftete.
    public let fingerabdruck: String?

    public init(adresse: URL, anmeldung: Anmeldung, fingerabdruck: String?) {
        self.adresse = adresse
        self.anmeldung = anmeldung
        self.fingerabdruck = fingerabdruck
    }
}

public enum Verbindungsergebnis: Equatable, Sendable {
    case verbunden(Heimzugang, satz: String?)
    /// Die Zahl wurde nicht angenommen — zählt als Fehlversuch.
    case abgelehnt(satz: String)
    /// Etwas anderes ging schief — zählt **nicht** als Fehlversuch.
    case fehler(satz: String)

    /// Die Antwort von `POST /api/verbinden` deuten.
    ///
    /// - Parameters:
    ///   - gefragtBei: Wo gefragt wurde — über Tailscale ist das auch die künftige Adresse
    ///     (der Server kennt seinen Tailscale-Namen nicht, `zugang.adresse` ist `null`).
    ///   - gesehen: Der Fingerabdruck, den der Mac **im Handschlag dieser Anfrage** sah —
    ///     `nil` über Tailscale.
    ///
    /// **Was die Gegenprobe des Fingerabdrucks leistet, und was nicht:** Der Server nennt
    /// den Fingerabdruck seines Zertifikats; stimmt er nicht mit dem gesehenen überein,
    /// sprach der Mac nicht mit dem Zuhörer, den der Server meint — dann wird **nichts**
    /// gemerkt. Wer sich im WLAN dazwischenstellt und die Antwort umschreibt, fällt damit
    /// nicht auf; gegen ihn hilft nur der Vergleich des Zeichens auf beiden Bildschirmen
    /// (`Fingerabdruck.zeichen`, Begründung in `aiimaging/heimnetz.py`).
    public static func lies(status: Int, daten: Data, gefragtBei: URL,
                            gesehen: String?) -> Verbindungsergebnis {
        let ergebnis: Kopplungsergebnis
        do {
            ergebnis = try Kopplungsergebnis.lies(status: status, daten: daten)
        } catch let f as Serverfehler {
            return .fehler(satz: f.satz)
        } catch {
            return .fehler(satz: "Die Antwort des Heim-PC war nicht lesbar.")
        }
        switch ergebnis {
        case .abgelehnt(let satz):
            return .abgelehnt(satz: satz)
        case .verbunden(let anmeldung, let satz):
            guard let anmeldung else {
                return .fehler(satz: "Der Heim-PC läuft ohne Kennwort — es gibt nichts zu "
                    + "merken. Dort mit --kennwort-datei starten (betrieb/README.md).")
            }
            let gesehenSauber = gesehen.flatMap(Fingerabdruck.normalisiere)
            let zugang = ((try? JSONWert.lies(daten))?.alsObjekt?["zugang"])?.alsObjekt ?? [:]
            if zugang["weg"]?.alsText == "heimnetz" {
                guard let text = zugang["adresse"]?.alsText,
                      case .gut(let url, _) = Heimadresse.pruefe(text),
                      let genannt = zugang["zertifikat_sha256"]?.alsText
                        .flatMap(Fingerabdruck.normalisiere) else {
                    return .fehler(satz: "Der Heim-PC nannte keinen lesbaren Zugang im WLAN.")
                }
                guard let gesehenSauber, gesehenSauber == genannt else {
                    return .fehler(satz: "Das Zertifikat, das der Mac sah, ist nicht das, das "
                        + "der Heim-PC nennt — nichts gemerkt. Noch einmal suchen.")
                }
                return .verbunden(Heimzugang(adresse: url, anmeldung: anmeldung,
                                             fingerabdruck: genannt), satz: satz)
            }
            guard case .gut(let url, _) = Heimadresse.pruefe(gefragtBei.absoluteString) else {
                return .fehler(satz: "Die Adresse, unter der gefragt wurde, ist keine https-Adresse.")
            }
            return .verbunden(Heimzugang(adresse: url, anmeldung: anmeldung,
                                         fingerabdruck: gesehenSauber), satz: satz)
        }
    }
}

// ============================================================ der Ablauf (Blatt 17)

/// Die drei Schritte von Blatt 17: **suchen → Zahl → verbunden.**
public struct Koppelablauf: Equatable, Sendable {
    public enum Schritt: Equatable, Sendable {
        case suchen
        case zahl
        case verbunden
    }

    public private(set) var schritt: Schritt = .suchen
    public private(set) var gewaehlt: Heimkandidat?
    /// Vom Mac gezählt, seit die letzte **neue** Zahl erschien.
    public private(set) var fehlversuche = 0
    /// Der Satz unter dem Zahlenfeld.
    public private(set) var satz: String?
    public private(set) var zugang: Heimzugang?

    public init() {}

    /// Nach 3 Fehlversuchen ist die Zahl drüben geschlossen.
    public var geschlossen: Bool { fehlversuche >= Heimkopplung.versuche }

    /// Ob «Koppeln» geht: im Schritt «Zahl», nicht geschlossen, und genau sechs Ziffern.
    public func darfKoppeln(_ eingabe: String) -> Bool {
        schritt == .zahl && !geschlossen && Kopplungszahl(eingabe) != nil
    }

    /// «Weiter» mit einem Kandidaten — **nur einem wählbaren.**
    @discardableResult
    public mutating func waehle(_ k: Heimkandidat) -> Bool {
        guard k.waehlbar else { return false }
        gewaehlt = k
        schritt = .zahl
        fehlversuche = 0
        satz = nil
        return true
    }

    public mutating func angefordert(_ e: Anforderungsergebnis) {
        switch e {
        case .angezeigt(let s, let neu):
            if neu { fehlversuche = 0 }
            satz = s
        case .warten(let s, _), .abgelehnt(let s):
            satz = s
        }
    }

    public mutating func verbinden(_ e: Verbindungsergebnis) {
        switch e {
        case .verbunden(let z, _):
            zugang = z
            schritt = .verbunden
            satz = nil
        case .abgelehnt(let s):
            fehlversuche += 1
            satz = geschlossen ? Heimkopplung.satzGeschlossen : s
        case .fehler(let s):
            satz = s
        }
    }

    /// «Zurück» zur Liste.
    public mutating func zurueck() {
        schritt = .suchen
        gewaehlt = nil
        fehlversuche = 0
        satz = nil
    }
}

// ============================================================ Fingerabdruck

/// Der Fingerabdruck eines Zertifikats — SHA-256 über seine Bytes, 64 Hex-Stellen.
public enum Fingerabdruck {
    /// Klein, ohne Doppelpunkte und Leerraum — oder `nil`, wenn es keine 64 Hex-Stellen sind.
    public static func normalisiere(_ text: String) -> String? {
        let sauber = text.lowercased().filter { $0 != ":" && $0 != " " }
        guard sauber.count == 64, sauber.allSatisfy({ $0.isHexDigit && $0.isASCII }) else {
            return nil
        }
        return sauber
    }

    /// Bytes als Hex (für die Prüfsumme, die der Mac berechnet).
    public static func hex(_ bytes: [UInt8]) -> String {
        let ziffern = Array("0123456789abcdef")
        var aus = ""
        aus.reserveCapacity(bytes.count * 2)
        for b in bytes {
            aus.append(ziffern[Int(b >> 4)])
            aus.append(ziffern[Int(b & 0x0f)])
        }
        return aus
    }

    /// Das «Zeichen des Heim-PC»: die ersten 16 Stellen in Vierergruppen — dasselbe, das der
    /// Heim-PC in seinem Fenster zeigt (`heimnetz.zeichen`, bewacht).
    public static func zeichen(_ abdruck: String) -> String {
        let kurz = Array((normalisiere(abdruck) ?? abdruck.lowercased()).prefix(16))
        return stride(from: 0, to: kurz.count, by: 4)
            .map { String(kurz[$0..<min($0 + 4, kurz.count)]) }
            .joined(separator: " ")
    }

    public enum Pruefung: Equatable, Sendable {
        /// Nichts angeheftet — das System prüft (Tailscale).
        case systemprueft
        case passt
        /// Angeheftet, und das gesehene ist ein anderes — **ablehnen.**
        case passtNicht
    }

    /// Nimmt der Mac dieses Zertifikat an?
    public static func pruefe(gesehen: String?, angeheftet: String?) -> Pruefung {
        guard let a = angeheftet.flatMap(normalisiere) else { return .systemprueft }
        guard let g = gesehen.flatMap(normalisiere), g == a else { return .passtNicht }
        return .passt
    }
}
