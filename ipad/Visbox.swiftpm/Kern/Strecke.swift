import Foundation

// DIE STRECKE ZUR HOMESTATION — im Heimnetz (http) oder unterwegs ueber Tailscale (https).
//
// Owner-Entscheid 63 (01.10.2026): Unterwegs spricht die iPad-App DIREKT mit dem Heim-PC,
// ueber Tailscale und verschluesselt (`https://<rechner>.<netz>.ts.net:8443`, Tailscale
// Serve mit gueltigem Zertifikat) — nicht mehr ueber den Mac. Der Grund stammt aus einer
// Sicherheitsdurchsicht: Zwischen iPad und Mac ginge die Leitung im fremden WLAN
// unverschluesselt (Protokoll §8b, «Grenzen»), mit Zugangsdaten und Bildern lesbar fuer
// jeden im selben Netz.
//
// Fuer die Anfragen aendert das nichts: Gleiche Wege, Felder, Saetze (Protokoll §1–§7). Was
// sich aendert, ist, WAS EIN MENSCH HOERT, wenn keine Antwort kommt. Im Heimnetz heisst ein
// unbekannter Name «die HomeStation ist nicht da»; ueber Tailscale heisst er fast immer
// «Tailscale am iPad ist aus» — und genau das soll die Verbindungszeile dann sagen.

/// Über welche Strecke die App die HomeStation erreicht — abgelesen an der gemerkten Adresse.
public enum Strecke: Equatable, Sendable {
    /// `http` im Heimnetz — gefunden über Bonjour oder eingetippt; auch der Mac als
    /// Vermittler (§8b) steht auf dieser Strecke.
    case heimnetz
    /// `https` über Tailscale Serve zum Heim-PC (Entscheid 63).
    case tailscale

    /// Die Strecke einer Adresse.
    ///
    /// **https heisst Tailscale.** Der Server selbst spricht nur HTTP (Protokoll §1); eine
    /// verschlüsselte Leitung zu ihm gibt es nur über Tailscale Serve. Ein Name auf `.ts.net`
    /// zählt ebenso, auch mit `http` geschrieben — die Prüfung der Eingabe lässt so eine
    /// Adresse zwar nicht zu (`Suche.pruefe(eingabe:)`), aber eine gemerkte aus einer älteren
    /// Fassung soll beim Scheitern trotzdem den Tailscale-Satz bekommen.
    public init(basis: URL) {
        let schema = basis.scheme?.lowercased()
        let rechner = (URLComponents(url: basis, resolvingAgainstBaseURL: false)?.host ?? "")
            .lowercased()
        self = (schema == "https" || Strecke.istTailscaleName(rechner)) ? .tailscale : .heimnetz
    }

    /// Ob ein Rechnername einer aus Tailscale ist (MagicDNS: `<rechner>.<netz>.ts.net`).
    public static func istTailscaleName(_ rechner: String) -> Bool {
        let r = rechner.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "."))
        return r.hasSuffix(".ts.net")
    }

    /// Was die Verbindungszeile hinter den Namen setzt — klein, wie «· über den Mac».
    public var zusatz: String {
        switch self {
        case .heimnetz: return ""
        case .tailscale: return " · über Tailscale"
        }
    }
}

// ================================================================ der Satz am iPad

extension Leitungsfehler {

    /// Der Satz **am iPad**, je nach Strecke.
    ///
    /// **Die Einteilung der Fehlercodes ist die der Mac-App** (`Leitungsfehler(urlFehlercode:)`
    /// in `Startzeilen.swift`) — wiederverwendet, nicht nachgebaut: Welcher Code «Name
    /// unbekannt» oder «Zertifikat» heisst, steht an einer Stelle. **Die Sätze dort** sagen
    /// aber «Tailscale am Mac an?» und «Dieser Mac» — am iPad wären beide falsch. Darum
    /// stehen die Sätze des iPad hier, neben denen des Mac und nicht in ihnen.
    ///
    /// Über Tailscale beginnen die vier Fälle, die fast immer «Tailscale am iPad ist aus»
    /// bedeuten (Name unbekannt, keine Verbindung, keine Antwort in der Frist, Zertifikat),
    /// mit derselben Frage. Ein Mensch soll den ersten Handgriff lesen, nicht den Code.
    ///
    /// - Parameter beschreibung: die Meldung des Systems, für den Fall, den keiner der Sätze
    ///   trifft — sonst stünde dort nur eine Zahl.
    public func satzAmIPad(_ strecke: Strecke, beschreibung: String? = nil) -> String {
        switch strecke {
        case .heimnetz: return heimnetzsatz(beschreibung)
        case .tailscale: return tailscalesatz(beschreibung)
        }
    }

    /// Die Frage, mit der ein Satz über Tailscale beginnt, wenn es fast sicher daran liegt.
    public static let tailscaleFrage = "Tailscale am iPad an?"

    // DIE SAETZE DES HEIMNETZES sind die, die `Verbindung/Sender.swift` bis zum 01.10.2026
    // selbst schrieb — wortgleich, damit sich zuhause nichts aendert. Neu ist nur, dass sie
    // hier stehen und unter Linux geprueft werden.
    private func heimnetzsatz(_ beschreibung: String?) -> String {
        switch self {
        case .keineVerbindung:
            return "Die HomeStation nimmt keine Verbindung an — läuft der Server dort?"
        case .nameUnbekannt:
            return "Die Adresse der HomeStation ist im Netz nicht zu finden."
        case .zeitUeberschritten:
            return "Die HomeStation hat nicht rechtzeitig geantwortet."
        case .keinNetz:
            return "Das iPad ist mit keinem Netz verbunden."
        case .abgerissen:
            return "Die Verbindung ist unterwegs abgerissen."
        case .abgebrochen:
            return "Das Senden wurde abgebrochen."
        case .zertifikat:
            return "Die verschlüsselte Leitung kam nicht zustande (das Zertifikat liess sich "
                + "nicht prüfen)."
        case .sonstig(let code):
            return "Die Verbindung kam nicht zustande (\(Leitungsfehler.grund(beschreibung, code)))."
        }
    }

    private func tailscalesatz(_ beschreibung: String?) -> String {
        let frage = Leitungsfehler.tailscaleFrage
        switch self {
        case .nameUnbekannt:
            // OHNE TAILSCALE KENNT DAS IPAD DEN NAMEN NICHT: `<rechner>.<netz>.ts.net` loest
            // nur die Tailscale-App auf (MagicDNS). Der haeufigste Grund, mit Abstand.
            return "\(frage) Der Name des Heim-PC ist im Netz nicht zu finden."
        case .keineVerbindung:
            return "\(frage) Der Heim-PC nimmt keine Verbindung an — ist er an, und läuft "
                + "dort der Dienst samt Tailscale Serve?"
        case .zeitUeberschritten:
            return "\(frage) Der Heim-PC hat nicht rechtzeitig geantwortet — vielleicht ist "
                + "er aus oder schläft."
        case .zertifikat:
            // EIN ZERTIFIKATSFEHLER UEBER TAILSCALE heisst fast immer: Die Adresse ist nicht
            // der Name aus Tailscale (etwa die Zahlenadresse 100.…), oder die Anfrage ging an
            // einen anderen Rechner. Tailscale Serve selbst hat ein gueltiges.
            return "\(frage) Die verschlüsselte Leitung kam nicht zustande (das Zertifikat des "
                + "Heim-PC liess sich nicht prüfen). Die Adresse muss sein Name aus Tailscale "
                + "sein, der auf .ts.net endet."
        case .keinNetz:
            return "Das iPad ist mit keinem Netz verbunden."
        case .abgerissen:
            return "Die Leitung zum Heim-PC ist unterwegs abgerissen."
        case .abgebrochen:
            return "Das Senden wurde abgebrochen."
        case .sonstig(let code):
            return "Die Leitung zum Heim-PC kam nicht zustande "
                + "(\(Leitungsfehler.grund(beschreibung, code)))."
        }
    }

    private static func grund(_ beschreibung: String?, _ code: Int) -> String {
        guard let b = beschreibung?.trimmingCharacters(in: .whitespacesAndNewlines),
              !b.isEmpty else { return "Fehler \(code)" }
        return b
    }
}
