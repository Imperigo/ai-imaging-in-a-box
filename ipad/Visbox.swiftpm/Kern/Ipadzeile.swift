import Foundation

// DIE ZEILE «iPad» AM MAC ZEIGT DEN ECHTEN STAND (Owner-Befund vom 20.10.2026, Visbox 0.2.11).
//
// Das iPad war gekoppelt — direkt mit dem Heim-PC, ueber Tailscale, gruen. Der Mac zeigte die
// Zeile trotzdem als «wartet» mit einer Zahl, die alle zwei Minuten neu kam, und im Bild «Wer
// rechnet wo» den Satz «Der Mac reicht das iPad durch». Beides war falsch, und beides aus
// demselben Grund: Der Mac kannte nur, was ueber IHN lief (die Vermittlung, §8b). Was das iPad
// direkt mit dem Heim-PC tat, sah er nie.
//
// Seither fuehrt der Heim-PC ein Geraetebuch (`aiimaging.geraetebuch`, `GET /api/geraete`):
// ob ein iPad gekoppelt ist, wann es sich zuletzt meldete und ueber welchen Weg. Der Mac fragt
// es ab; WAS DIE ZEILE DARAUS MACHT, steht hier — unter Linux geprueft
// (`IpadzeileTests`). Die Mac-App fragt nur und zeigt.
//
//     *Eine Zeile, die «wartet» sagt, obwohl das Gerät längst da ist, lädt zu einer zweiten
//     Kopplung ein — und die zweite Zahl macht die erste nicht rückgängig.*

// ================================================================ die Antwort des Heim-PC

/// Was `GET /api/geraete` ergab: eine Antwort (mit Rumpf) oder keine.
public enum Geraetebefund: Equatable, Sendable {
    case antwort(status: Int, daten: Data)
    case keineAntwort(Leitungsfehler)
}

/// Die Antwort von `GET /api/geraete` — **der feste Vertrag** mit dem Heim-PC (ab 0.2.12):
///
/// ```json
/// {"ipad": {"gekoppelt": true, "gekoppelt_vor_s": 120, "zuletzt_gesehen_s": 8,
///           "weg": "direkt" | "mac" | null}}
/// ```
///
/// Die Zeiten sind **Sekunden vor der Antwort**, vom Heim-PC gerechnet — so spielt es keine
/// Rolle, ob die Uhren von Mac und Heim-PC gleich gehen. `null` heisst: nicht bekannt.
public struct Geraetebericht: Equatable, Sendable {
    public enum Weg: String, Equatable, Sendable {
        case direkt
        case mac
    }

    public let gekoppelt: Bool
    public let gekoppeltVor: TimeInterval?
    public let zuletztGesehenVor: TimeInterval?
    public let weg: Weg?

    public init(gekoppelt: Bool, gekoppeltVor: TimeInterval? = nil,
                zuletztGesehenVor: TimeInterval? = nil, weg: Weg? = nil) {
        self.gekoppelt = gekoppelt
        self.gekoppeltVor = gekoppeltVor
        self.zuletztGesehenVor = zuletztGesehenVor
        self.weg = weg
    }

    /// Liest den Teil `ipad` — `nil`, wenn die Antwort nicht in der Form ist. **`gekoppelt`
    /// muss ein echter Wahrheitswert sein** (wie überall im Kern); eine Zeit, die keine Zahl
    /// ist, oder eine negative, zählt als unbekannt, nicht als «eben».
    public static func lies(_ daten: Data) -> Geraetebericht? {
        guard let wert = try? JSONWert.lies(daten), let feld = wert.alsObjekt,
              let ipad = feld["ipad"], ipad.alsObjekt != nil,
              let gekoppelt = ipad["gekoppelt"]?.alsWahrheit else { return nil }
        func zeit(_ name: String) -> TimeInterval? {
            guard let z = ipad[name]?.alsZahl, z >= 0, z.isFinite else { return nil }
            return z
        }
        return Geraetebericht(gekoppelt: gekoppelt, gekoppeltVor: zeit("gekoppelt_vor_s"),
                              zuletztGesehenVor: zeit("zuletzt_gesehen_s"),
                              weg: ipad["weg"]?.alsText.flatMap(Weg.init(rawValue:)))
    }
}

// ================================================================ die Entscheidung

/// Eine Zahl fürs iPad, die gerade am Mac angeboten wird (aus «iPad koppeln») — mit dem
/// Zeitpunkt, zu dem das Koppelfenster aufging.
public struct Koppelangebot: Equatable, Sendable {
    public let stand: Zeilenstand
    public let seit: Date

    public init(stand: Zeilenstand, seit: Date) {
        self.stand = stand
        self.seit = seit
    }
}

/// Über welchen Weg das iPad den Heim-PC erreicht — für die Zeile und für «Wer rechnet wo».
public enum Ipadweg: Equatable, Sendable {
    /// Das iPad spricht selbst mit dem Heim-PC (über Tailscale oder im Heimnetz).
    case direkt
    /// Der Mac reicht das iPad durch (Vermittlung, §8b).
    case ueberMac

    /// Das Wort nach «iPad gekoppelt ·».
    public var wort: String {
        switch self {
        case .direkt: return "direkt"
        case .ueberMac: return "über diesen Mac"
        }
    }

    /// Der Satz unter «Wer rechnet wo».
    public var satz: String {
        switch self {
        case .direkt:
            // SEIT ENTSCHEID 118a (21.10.2026) ENDET DER DIREKTE WEG: Der Heim-PC weist ein iPad,
            // das direkt spricht, mit Satz ab (410). In 0.3.16 war er noch Uebergang.
            return "Gerechnet wird nie auf dem Mac und nie auf dem iPad. Das iPad war direkt mit "
                + "dem Heim-PC gekoppelt — diesen Weg nimmt der Heim-PC nicht mehr an. Im Menü "
                + "«iPad» «iPad koppeln» koppelt es mit diesem Mac."
        case .ueberMac:
            return "Gerechnet wird nie auf dem Mac und nie auf dem iPad. Das iPad arbeitet über "
                + "diesen Mac, verschlüsselt: Mappe, Bilder und Skizzen kommen von hier, der Mac "
                + "trägt die Leitung nach Hause — das iPad muss nur ins selbe WLAN wie der Mac."
        }
    }

    /// Was der Kasten «Mac» darunter sagt.
    public var macSatz: String {
        switch self {
        case .direkt: return "Oberfläche, Zahl zum Koppeln"
        case .ueberMac: return "Oberfläche, Vermittler fürs iPad"
        }
    }
}

/// Die Zeile «iPad» am Mac — **eine reine Funktion**, ohne Uhr und ohne Netz.
public enum Ipadzeile {
    /// Wie lange eine Meldung des iPad als «da» gilt: **24 Stunden** — gesetzt, nicht gemessen.
    /// Das iPad fragt alle zehn Sekunden, solange die App offen ist; eine Zeile, die nach zehn
    /// Sekunden ohne Frage auf «wartet» fiele, flackerte bei jedem Wegstellen des Tablets. Wer
    /// einen Tag nichts von sich hören liess, ist aber nicht mehr «gekoppelt und da», sondern
    /// «gekoppelt, länger nicht gesehen» — und das sagt die Zeile dann.
    public static let gesehenHoechstens: TimeInterval = 24 * 3600

    /// Wie viel früher als das Koppelfenster eine Kopplung drüben stehen darf und trotzdem als
    /// «die aus diesem Fenster» gilt — die Uhren von Mac und Heim-PC laufen nie ganz gleich, und
    /// die Antwort braucht ihre Zeit.
    public static let fensterspiel: TimeInterval = 5

    /// Der Weg, über den das iPad den Heim-PC erreicht.
    ///
    /// **Über den Mac nur, wenn der Mac wirklich vermittelt:** Die Vermittlung ist an und meldet
    /// ein iPad (`verbunden`), oder der Heim-PC hat das iPad zuletzt über den Mac gesehen und
    /// die Vermittlung ist an. Sonst — auch wenn nichts bekannt ist — direkt: Das ist der Weg
    /// seit Entscheid 63, und die Vermittlung ist von Haus aus aus.
    public static func weg(bericht: Geraetebericht?, vermittlung: Vermittlerlage?) -> Ipadweg {
        let vermittlungAn: Bool
        switch vermittlung {
        case nil, .aus?: vermittlungAn = false
        default: vermittlungAn = true
        }
        guard vermittlungAn else { return .direkt }
        if case .verbunden? = vermittlung { return .ueberMac }
        if bericht?.weg == .mac { return .ueberMac }
        return .direkt
    }

    /// Die Zeile. In dieser Reihenfolge:
    ///
    /// 1. **Ein offenes Koppelfenster** zeigt seine Zahl — wer «iPad koppeln» drückt, will sie
    ///    sehen. *Ausser* der Heim-PC meldet eine Kopplung, die **nach** dem Öffnen kam: Dann
    ///    hat genau diese Zahl gekoppelt, und die Zeile sagt es.
    /// 2. **Die Vermittlung meldet ein iPad** (`verbunden`) → steht, «über diesen Mac».
    /// 3. **Eine Zahl der Vermittlung** (ausdrücklich angefordert) → ihr Satz.
    /// 4. **Der Heim-PC meldet ein gekoppeltes iPad** → steht, «direkt» (oder «über diesen
    ///    Mac»), mit «zuletzt vor …» — oder wartet, wenn es sich länger als
    ///    `gesehenHoechstens` nicht meldete.
    /// 5. Sonst die Vermittlung, wenn sie an ist, und zuletzt die Vorgabe.
    ///
    /// Antwortet der Heim-PC nicht oder kennt er den Weg nicht (404, vor 0.2.12), gilt der
    /// Bericht als nicht da — die Zeile fällt auf 2, 3 und 5 zurück und sagt nie «gekoppelt»,
    /// ohne dass es jemand gemeldet hat.
    public static func stand(geraete befund: Geraetebefund?, vermittlung: Vermittlerlage?,
                             koppeln: Koppelangebot?, jetzt: Date) -> Zeilenstand {
        let bericht = lies(befund)
        let weg = weg(bericht: bericht, vermittlung: vermittlung)

        if let k = koppeln {
            if let b = bericht, b.gekoppelt, let vor = b.gekoppeltVor,
               jetzt.addingTimeInterval(-vor) >= k.seit.addingTimeInterval(-fensterspiel) {
                return gekoppelt(b, weg: weg)
            }
            return k.stand
        }
        if case .verbunden(let vor)? = vermittlung {
            return .steht(satz: "iPad gekoppelt · \(Ipadweg.ueberMac.wort) · zuletzt "
                          + Vermittlerlage.dauer(vor))
        }
        if case .koppeln? = vermittlung, let v = vermittlung {
            return v.alsZeilenstand()
        }
        if let b = bericht, b.gekoppelt {
            return gekoppelt(b, weg: weg)
        }
        if let v = vermittlung, v != .aus {
            return v.alsZeilenstand()
        }
        return Startbild.ipadVorgabe
    }

    /// Der Bericht aus dem Befund — nur bei 200 und lesbarer Form, sonst `nil` (404 heisst: ein
    /// Heim-PC vor 0.2.12, der kein Gerätebuch führt).
    public static func bericht(_ befund: Geraetebefund) -> Geraetebericht? {
        guard case .antwort(200, let daten) = befund else { return nil }
        return Geraetebericht.lies(daten)
    }

    static func lies(_ befund: Geraetebefund?) -> Geraetebericht? {
        befund.flatMap(bericht)
    }

    static func gekoppelt(_ b: Geraetebericht, weg: Ipadweg) -> Zeilenstand {
        let kopf = "iPad gekoppelt · \(weg.wort)"
        guard let vor = b.zuletztGesehenVor else {
            // GEKOPPELT, ABER SEITHER NICHT GESEHEN (oder ein iPad vor 0.2.12, das seine Art
            // nicht sagt): gekoppelt ist es trotzdem — der Heim-PC hat die Zahl angenommen.
            return .steht(satz: kopf + " · zuletzt gesehen: unbekannt")
        }
        guard vor <= gesehenHoechstens else {
            return .wartet(satz: "iPad gekoppelt, aber seit \(dauer(vor)) nicht gemeldet. "
                           + "\(Marke.name) am iPad öffnen.")
        }
        return .steht(satz: kopf + " · zuletzt " + Vermittlerlage.dauer(vor))
    }

    /// «3 Tagen», «30 Stunden» — für «seit …».
    static func dauer(_ s: TimeInterval) -> String {
        let stunden = Int(s / 3600)
        if stunden < 48 { return "\(stunden) Stunden" }
        return "\(stunden / 24) Tagen"
    }
}
