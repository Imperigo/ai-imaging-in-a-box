import Foundation

// DAS IPAD ARBEITET UEBER DEN MAC, VERSCHLUESSELT (Owner-Entscheid 118, 21.10.2026).
//
// Bis 0.3.15 sprach das iPad direkt mit dem Heim-PC (zuhause im Heimnetz, unterwegs ueber
// Tailscale, Entscheid 63); der Mac vermittelte nur, wer es einschaltete, und dann
// unverschluesselt. Seit Schritt 3 liegt die Mappe aber AM MAC — sprach das iPad weiter mit dem
// Heim-PC, saehe es dort die Zwillingsmappe und unterwegs die Mappe am Mac: zwei Staende
// derselben Arbeit. Darum (Entscheid 118, Antwort A): immer ueber den Mac, auch zuhause, und
// zuerst verschluesselt.
//
// Die Leitung: `https` zum Mac, mit dem Zertifikat des Mac (`Maczertifikat`), dessen
// Fingerabdruck das iPad beim Koppeln ANHEFTET — aus dem Koppelschein (QR-Code, Naehe), beim
// Abtippen aus dem Handschlag mit Gegenprobe. Danach nimmt das iPad kein anderes Zertifikat an,
// und auf unverschluesselt faellt es nie still zurueck.
//
// Hier stehen die Regeln des iPad, ohne Netz und mit Proben (`MacanbindungTests`); die App
// fragt nur (`Verbindung/Verbindungsstand.swift`, `Verbindung/Sender.swift`).

/// Wie das iPad angebunden ist — **abgelesen an dem, was es sich gemerkt hat**, nie geraten.
public enum Anbindungsart: Equatable, Sendable {
    /// Über den Mac, verschlüsselt, mit angeheftetem Zertifikat — der Weg seit Entscheid 118.
    case macVerschluesselt(zeichen: String)
    /// Über den Mac, aber **ohne** Verschlüsselung oder ohne angeheftetes Zertifikat (eine
    /// Kopplung aus der Zeit vor 118). Gesendet wird darüber nichts.
    case macUngeschuetzt
    /// Direkt am Heim-PC (Heimnetz oder Tailscale) — **eine Kopplung von vorher**: In 0.3.16
    /// ging sie noch (Übergang); seit Entscheid 118a weist der Heim-PC sie mit 410 ab
    /// (`Macanbindung.satzDirektBeendet`). Gefragt wird trotzdem, damit der Satz des Heim-PC
    /// ankommt — und ein Heim-PC mit altem Stand weiter antwortet, bis er nachgezogen ist.
    case direkt(Strecke)
    /// Nicht gekoppelt.
    case keine

    public static func bestimme(adresse: URL?, ueberDenMac: Bool, abdruck: String?) -> Anbindungsart {
        guard let adresse else { return .keine }
        guard ueberDenMac else { return .direkt(Strecke(basis: adresse)) }
        guard adresse.scheme?.lowercased() == "https",
              let a = abdruck.flatMap(Fingerabdruck.normalisiere) else { return .macUngeschuetzt }
        return .macVerschluesselt(zeichen: Fingerabdruck.zeichen(a))
    }

    /// Ob das Schloss gezeigt wird.
    public var schloss: Bool {
        if case .macVerschluesselt = self { return true }
        return false
    }

    /// Ob über diese Anbindung gesendet und gefragt wird. **Nie unverschlüsselt über den Mac**
    /// — die Zeile sagt dann, warum (`satz`).
    public var darfSprechen: Bool { self != .macUngeschuetzt && self != .keine }

    /// Was hinter dem Namen in der Verbindungszeile steht.
    public var zusatz: String {
        switch self {
        case .macVerschluesselt: return " · über den Mac, verschlüsselt"
        case .macUngeschuetzt: return " · über den Mac, unverschlüsselt"
        case .direkt(let s): return s.zusatz + " · direkt"
        case .keine: return ""
        }
    }

    /// Der Satz darunter — `nil`, wenn alles ist, wie es sein soll.
    public var satz: String? {
        switch self {
        case .macVerschluesselt, .keine: return nil
        case .macUngeschuetzt: return Macanbindung.satzUngeschuetzt
        case .direkt: return Macanbindung.satzDirekt
        }
    }
}

public enum Macanbindung {
    /// Wie der Mac seinen Zugang in der Antwort auf `POST /api/verbinden` nennt
    /// (`zugang.weg`) — neben `heimnetz` des Heim-PC.
    public static let zugangsweg = "mac"

    // ------------------------------------------------------------------- Sätze

    /// Das Zertifikat passt nicht zum angehefteten — **es wird nicht verbunden.**
    public static let satzFremdesZertifikat = "Der Mac zeigt ein anderes Zertifikat als beim "
        + "Koppeln — nicht verbunden. Am Mac «iPad koppeln» öffnen und neu koppeln."
    /// Eine Kopplung über den Mac aus der Zeit vor 118 (unverschlüsselt).
    public static let satzUngeschuetzt = "Über den Mac gekoppelt, aber unverschlüsselt (alter "
        + "Stand) — darüber geht nichts mehr. Am Mac «iPad koppeln» öffnen und neu koppeln; die "
        + "Skizzen warten im Parkfach."
    /// Direkt am Heim-PC — der Weg endet (Entscheid 118a).
    public static let satzDirekt = "Direkt am Heim-PC — dieser Weg endet, der Heim-PC nimmt "
        + "das iPad so nicht mehr an. Am Mac «iPad koppeln» öffnen und mit dem Mac koppeln."
    /// **Wortgleich mit dem Satz des Heim-PC** (`aiimaging.geraetebuch.SATZ_DIREKT_BEENDET`,
    /// bewacht in `tests/test_ipad_ueber_den_mac.py`) — für eine 410 ohne lesbaren Satz.
    public static let satzDirektBeendet = "Das iPad verbindet sich jetzt über den Mac — am Mac "
        + "«iPad koppeln» öffnen und das iPad mit dem Mac koppeln. Direkt nimmt der Heim-PC das "
        + "iPad nicht mehr an."
    /// Der Mac nannte bei der Kopplung kein Zertifikat.
    public static let satzOhneAbdruck = "Der Mac nannte beim Koppeln kein Zertifikat (alter "
        + "Stand) — nichts gemerkt. Die Mac-App aktualisieren und neu koppeln."
    /// Das gesehene Zertifikat ist nicht das genannte oder nicht das aus dem Schein.
    public static let satzGegenprobe = "Das Zertifikat, das das iPad sah, ist nicht das des Mac "
        + "aus dem Koppelfenster — nichts gemerkt. Am Mac «iPad koppeln» neu öffnen."
    /// Der Mac antwortet nicht — das iPad zeichnet weiter.
    public static let satzOhneMac = "Der Mac antwortet nicht. Zeichnen geht weiter; Skizzen "
        + "warten im Parkfach, bis der Mac wieder da ist."

    // ------------------------------------------------------------------- koppeln

    /// Was nach einer **angenommenen** Kopplung am Mac gemerkt wird — oder der Satz, warum
    /// nichts.
    public enum Pruefung: Equatable, Sendable {
        case gut(abdruck: String)
        case abgelehnt(String)
    }

    /// Die Gegenprobe nach `POST /api/verbinden` am Mac (dieselbe wie zwischen Mac und
    /// Heim-PC, `Verbindungsergebnis.lies`):
    ///
    /// 1. Der Mac nennt seinen Zugang (`zugang.weg == "mac"`, `zertifikat_sha256`) — sonst ist
    ///    es ein Mac mit altem Stand, und nichts wird gemerkt.
    /// 2. Das iPad hat **im Handschlag dieser Anfrage** genau dieses Zertifikat gesehen.
    /// 3. Kam ein Abdruck aus dem Koppelschein (`angeheftet`), ist es auch **dieser**. Das ist
    ///    der starke Teil: Den Schein brachte die Kamera oder die verschlüsselte Nähe — wer im
    ///    WLAN dazwischen sitzt, kann ihn nicht umschreiben.
    ///
    /// Beim Abtippen gibt es keinen Schein: Dann schützt die Zahl, die nur am Bildschirm des Mac
    /// steht, und wer will, vergleicht das Zeichen auf beiden Bildschirmen.
    public static func pruefeKopplung(antwort daten: Data, gesehen: String?,
                                      angeheftet: String?) -> Pruefung {
        guard let wert = try? JSONWert.lies(daten), let zugang = wert["zugang"]?.alsObjekt,
              zugang["weg"]?.alsText == zugangsweg,
              let genannt = zugang["zertifikat_sha256"]?.alsText.flatMap(Fingerabdruck.normalisiere)
        else { return .abgelehnt(satzOhneAbdruck) }
        guard let g = gesehen.flatMap(Fingerabdruck.normalisiere), g == genannt else {
            return .abgelehnt(satzGegenprobe)
        }
        if let a = angeheftet {
            guard Fingerabdruck.normalisiere(a) == genannt else { return .abgelehnt(satzGegenprobe) }
        }
        return .gut(abdruck: genannt)
    }

    // ------------------------------------------------------------------- wiederfinden

    /// Was mit einem Fund geschieht, der **der gekoppelte Mac** ist (`gekoppelterMac`: an seinem
    /// Fingerabdruck, sonst am Namen) — der Router hat ihm eine neue Adresse gegeben.
    public enum Wiederfund: Equatable, Sendable {
        /// Dieselbe Adresse — nichts zu tun.
        case gleich
        /// Eine neue Adresse, verschlüsselt — übernehmen (das Zertifikat bleibt angeheftet).
        case neu(URL)
        /// Der Fund spricht **unverschlüsselt** — **nicht** übernehmen, und es sagen.
        case unverschluesselt(String)
        /// Noch nicht aufgelöst.
        case offen
    }

    /// Welcher Fund **der gekoppelte Mac** ist — an seiner festen Kennung, nicht am Namen.
    ///
    /// **Der Anlass** (Demolauf 22.10.2026): macOS hatte den Mac wegen eines Namenskonflikts in
    /// «MacBook Pro von … (2)» umbenannt; er bot sich unter dem neuen Namen an, und das iPad,
    /// das nur `name == gemerkt` verglich, fand ihn nicht mehr («getrennt»).
    ///
    /// Die Regel, in dieser Reihenfolge — betrachtet werden nur aufgelöste Funde «über den Mac»:
    /// 1. **Nennt ein Fund den angehefteten Fingerabdruck** (TXT `abdruck`), ist er es — unter
    ///    welchem Namen auch immer.
    /// 2. **Rückfall für einen Mac mit altem Stand:** Ein Fund **ohne** Abdruck wird weiter am
    ///    gemerkten Namen erkannt.
    /// 3. Ein Fund, der einen **anderen** Abdruck nennt, ist es **nie** — auch nicht unter dem
    ///    gemerkten Namen. Das ist ein anderer Mac (oder ein erneuertes Zertifikat, das das iPad
    ///    ohnehin nicht annähme); seine Adresse zu übernehmen hiesse, ins Leere zu sprechen.
    ///
    /// Kein Geheimnis wird verglichen und keines geschützt: Was danach spricht, prüft weiter
    /// das angeheftete Zertifikat (`Maclotse`). Die Kennung sagt nur, **wo** gesucht wird.
    public static func gekoppelterMac(in liste: [GefundenerDienst], name: String?,
                                      abdruck: String?) -> GefundenerDienst? {
        let angeheftet = abdruck.flatMap(Fingerabdruck.normalisiere)
        let macs = liste.filter { $0.ueberDenMac && $0.aufgeloest }
        if let angeheftet, let fund = macs.first(where: { $0.abdruck == angeheftet }) {
            return fund
        }
        guard let name else { return nil }
        return macs.first { fund in
            guard fund.name == name else { return false }
            guard let genannt = fund.abdruck, let angeheftet else { return true }
            return genannt == angeheftet
        }
    }

    /// Der Name, den sich das iPad **neu** merkt, wenn es den gekoppelten Mac unter einem anderen
    /// Namen wiederfand — `nil`: nichts zu ändern. Nur ein verschlüsselter Fund darf den Namen
    /// ändern (wie die Adresse, `wiedergefunden`). Der Name ist **Anzeige**, keine Kennung.
    public static func neuerName(gemerkt: String?, fund: GefundenerDienst) -> String? {
        guard fund.verschluesselt, !fund.name.isEmpty, fund.name != gemerkt else { return nil }
        return fund.name
    }

    /// **Kein Rückfall auf unverschlüsselt:** Bietet sich derselbe Name nur noch ohne `tls=1`
    /// an (ein Mac, der auf einen alten Stand zurückgesetzt wurde — oder ein anderes Gerät
    /// unter seinem Namen), bleibt die gemerkte Adresse, und die Zeile sagt warum.
    public static func wiedergefunden(gemerkt: URL, fund: GefundenerDienst) -> Wiederfund {
        guard let neu = fund.adresse else { return .offen }
        guard fund.verschluesselt else { return .unverschluesselt(Suche.satzAlterMac(fund.name)) }
        return neu == gemerkt ? .gleich : .neu(neu)
    }

    /// Ob ein Rechner und Anschluss der gemerkte Mac ist — für das Anheften im Lotsen: **nur
    /// dort** gilt der angeheftete Abdruck; jede andere Adresse prüft das System.
    public static func istMac(host: String, port: Int, gemerkt: URL?) -> Bool {
        guard let gemerkt, let h = gemerkt.host else { return false }
        let ohneKlammern = h.trimmingCharacters(in: CharacterSet(charactersIn: "[]")).lowercased()
        let gefragt = host.trimmingCharacters(in: CharacterSet(charactersIn: "[]")).lowercased()
        return ohneKlammern == gefragt && (gemerkt.port ?? 443) == port
    }

    // ------------------------------------------------------------------- die Adresse des Mac

    /// Welche Adresse der Mac dem iPad in den Koppelschein schreibt — aus den Schnittstellen,
    /// die er hat (Name, IPv4). **Im WLAN, nicht über Tailscale:** Das iPad hat kein Tailscale
    /// mehr nötig (Entscheid 118). Ausgelassen: die eigene Schleife (127.*), Adressen ohne
    /// Router (169.254.*) und Tailscale (100.64.0.0/10). Vorzug: `en0` (meist das WLAN), dann
    /// die übrigen `en*`, dann `bridge*` (der persönliche Hotspot des Mac), dann der Rest. Das
    /// iPad findet den Mac danach über seinen Namen wieder, wenn die Adresse wechselt.
    public static func adresseFuerIpad(schnittstellen: [(name: String, adresse: String)]) -> String? {
        func brauchbar(_ a: String) -> Bool {
            let teile = a.split(separator: ".").compactMap { Int($0) }
            guard teile.count == 4, teile.allSatisfy({ (0...255).contains($0) }) else { return false }
            if teile[0] == 127 || teile[0] == 0 { return false }
            if teile[0] == 169 && teile[1] == 254 { return false }
            if teile[0] == 100 && (64...127).contains(teile[1]) { return false }
            return true
        }
        func rang(_ name: String) -> Int {
            if name == "en0" { return 0 }
            if name.hasPrefix("en") { return 1 }
            if name.hasPrefix("bridge") { return 2 }
            return 3
        }
        return schnittstellen.filter { brauchbar($0.adresse) && !$0.name.hasPrefix("utun") }
            .enumerated()
            .min { (rang($0.element.name), $0.offset) < (rang($1.element.name), $1.offset) }?
            .element.adresse
    }

    /// Die Adresse des Mac als `https://<ip>:<anschluss>` — `nil`, wenn sie keine wäre.
    public static func adresse(ip: String, anschluss: Int) -> URL? {
        guard case .gut(let url, _) = Suche.pruefeMac(eingabe: "https://\(ip):\(anschluss)") else {
            return nil
        }
        return url
    }
}
