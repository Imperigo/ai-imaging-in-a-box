import Foundation

/// Wie ein Bild gelesen wird — **der Schalter am Bild** (Entscheide 15 und 30).
///
/// *Prüfen:* Erfundenes Volumen ist ein Fehler, das Bild trägt sein Urteil.
/// *Entwerfen:* Erfundenes Volumen ist der Zweck; es wird kein Urteil gesprochen, und das
/// Zeichen ist blau — eine Farbe, die in den drei Antworten nicht vorkommt.
public enum Bildlesart: String, CaseIterable, Sendable {
    case pruefen
    case entwerfen
}

/// Ein Farbton als drei Bytes — **ohne SwiftUI**, damit die Abbildung Urteil → Farbe hier
/// im Kern liegt und unter Linux geprüft werden kann. Die App macht daraus eine `Color`.
public struct Farbton: Equatable, Hashable, Sendable {
    public let rot: UInt8
    public let gruen: UInt8
    public let blau: UInt8

    public init(rot: UInt8, gruen: UInt8, blau: UInt8) {
        self.rot = rot
        self.gruen = gruen
        self.blau = blau
    }

    /// Aus sechs Hex-Ziffern, wie sie im Blatt «Die Zeichen» stehen (`"4ea373"`).
    ///
    /// Die Werte stehen fest im Quelltext; eine falsch geschriebene Ziffer ist ein
    /// Schreibfehler hier und keine Eingabe von aussen. Darum hält die Probe
    /// `testJedeFarbeIstLesbarGeschrieben` jeden Ton fest, statt dass hier geraten wird.
    public init(hex: String) {
        let ziffern = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        let wert = UInt32(ziffern, radix: 16) ?? 0
        self.init(rot: UInt8((wert >> 16) & 0xff),
                  gruen: UInt8((wert >> 8) & 0xff),
                  blau: UInt8(wert & 0xff))
    }

    /// `#rrggbb`, klein geschrieben.
    public var hex: String {
        String(format: "#%02x%02x%02x", rot, gruen, blau)
    }

    /// Dieser Ton, zu `deckung` über `grund` gelegt.
    public func ueber(_ grund: Farbton, deckung: Double) -> Farbton {
        func misch(_ a: UInt8, _ b: UInt8) -> UInt8 {
            UInt8((Double(a) * deckung + Double(b) * (1 - deckung)).rounded())
        }
        return Farbton(rot: misch(rot, grund.rot), gruen: misch(gruen, grund.gruen),
                       blau: misch(blau, grund.blau))
    }

    /// Die relative Helligkeit nach WCAG 2.
    public var helligkeit: Double {
        func kanal(_ k: UInt8) -> Double {
            let c = Double(k) / 255
            return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * kanal(rot) + 0.7152 * kanal(gruen) + 0.0722 * kanal(blau)
    }

    /// Das Kontrastverhältnis zweier Töne nach WCAG 2 (1 bis 21).
    public static func kontrast(_ a: Farbton, _ b: Farbton) -> Double {
        let (h, d) = (max(a.helligkeit, b.helligkeit), min(a.helligkeit, b.helligkeit))
        return (h + 0.05) / (d + 0.05)
    }
}

/// Welche Art Zeichen ein Bild trägt — **fünf, und jede hat ihre eigene Farbe.**
///
/// Die drei Antworten des Projekts, dazu der Entwurf (blau, spricht kein Urteil) und ein
/// Zeichen, das diese App nicht kennt. *Dieselbe Farbe darf nie zwei Dinge heissen*
/// (Blatt «Die Zeichen», 21.09.2026); `testKeineFarbeHeisstZweiDinge` hält das fest.
public enum Zeichenart: String, CaseIterable, Sendable {
    case bestanden
    case durchgefallen
    case nichtGemessen
    case entwurf
    /// Ein Zeichen vom Server, das diese App nicht kennt (ein neuerer Server).
    ///
    /// **Nicht «nicht gemessen».** Dasselbe wie in `Urteil(zeichen:)`: geraten sieht in
    /// der Anzeige genauso aus wie gewusst. Und auch nicht *kein* Zeichen — *kein Zeichen
    /// sieht aus wie kein Problem.*
    case unbekannt

    /// Der Rand um das Bild. Er trägt die Aussage über die Distanz.
    public var rand: Farbton {
        switch self {
        case .bestanden: return Farbton(hex: "4ea373")
        case .durchgefallen: return Farbton(hex: "e2776f")
        case .nichtGemessen: return Farbton(hex: "c8a53f")
        case .entwurf: return Farbton(hex: "6fb3d2")
        case .unbekannt: return Farbton(hex: "9aa2ae")
        }
    }

    /// Die Schrift im Streifen. Bei «bestanden» heller als der Rand: `#4ea373` wäre auf
    /// dem dunklen Streifen zu schwach (Blatt «Die Zeichen»).
    public var schrift: Farbton {
        switch self {
        case .bestanden: return Farbton(hex: "8fd4ac")
        default: return rand
        }
    }

    /// **Gestrichelt heisst: hier ist nichts gemessen.** Damit sich ein ungeprüftes Bild
    /// auch von weitem und ohne Farbensehen nicht wie ein bestandenes liest.
    public var gestrichelt: Bool {
        switch self {
        case .nichtGemessen, .unbekannt: return true
        case .bestanden, .durchgefallen, .entwurf: return false
        }
    }

    /// Das Wort, in Grossbuchstaben wie auf dem Bild.
    public var wort: String {
        switch self {
        case .bestanden: return "BESTANDEN"
        case .durchgefallen: return "DURCHGEFALLEN"
        case .nichtGemessen: return "NICHT GEMESSEN"
        case .entwurf: return "ENTWURF — NICHT GEPRÜFT"
        case .unbekannt: return "ZEICHEN UNBEKANNT"
        }
    }
}

/// Was an der Stelle der Zahl steht.
public enum Zahlanzeige: Equatable, Sendable {
    /// Eine übertragene, lesbare Zahl, fertig geschrieben (`"0.93"`).
    case wert(String)
    /// Das Urteil verlangt eine Zahl, und es kam keine (oder eine unlesbare).
    ///
    /// **Nie `0.00`.** Eine fehlende Zahl als Null zu schreiben hiesse, eine Messung zu
    /// behaupten, die schlechtestmöglich ausfiel — und bei «bestanden» einen Widerspruch
    /// anzuzeigen, der nur aus der Anzeige stammt.
    case fehlt
    /// Hier gehört keine Zahl hin (nicht gemessen, unbekanntes Zeichen, Entwurf ohne
    /// Unterschied).
    case keine

    /// Der Text, der am Bild steht, oder `nil`, wenn keiner hingehört.
    public var text: String? {
        switch self {
        case .wert(let t): return t
        case .fehlt: return "ohne Zahl"
        case .keine: return nil
        }
    }
}

/// Ein Vorbehalt, der **mit dem Zeichen reist** — auch ins geteilte Bild.
public struct Vorbehalt: Equatable, Sendable {
    /// Das kurze Wort für den Streifen.
    public let kurz: String
    /// Der ganze Satz, wie er vom Server kam.
    public let satz: String
}

/// Das Prüfzeichen an einem Bild: **Farbe, Wort und Zahl** (Entscheid 16) — und ein
/// Vorbehalt, wenn einer mitkam.
///
/// Hier wird nichts gemessen und nichts entschieden. Das Urteil, die Zahl und die Hinweise
/// kommen vom Server; diese Datei legt nur fest, **wie** sie am Bild aussehen. Sie liegt im
/// Kern und nicht in der Ansicht, damit genau diese Abbildung unter Linux geprüft wird
/// (`PruefzeichenTests`) — die Ansicht malt danach nur noch ab, was hier steht.
///
///     *Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes — und auch nicht wie
///     gar nichts.*
public struct Pruefzeichen: Equatable, Sendable {
    public let art: Zeichenart
    public let zahl: Zahlanzeige
    public let vorbehalte: [Vorbehalt]

    /// Der feste Anfang des Server-Hinweises, dass die Skizze beim Bildmodell nicht ankam
    /// (Entscheid E24 vom 22.09.2026; `aiimaging.kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN`).
    ///
    /// Der Server setzt ihn als festen Anfang, *damit eine Anzeige ihn erkennen kann, ohne
    /// den Rest zu deuten*. `PruefzeichenTests` liest den Satz in `kette.py` nach und fällt,
    /// sobald er anders anfängt.
    public static let anfangSkizzeNichtAngekommen = "SKIZZE NICHT ANGEKOMMEN"

    /// Der Streifen unter dem Wort: fast schwarz, zu 94 % deckend.
    ///
    /// Befund aus dem Blatt «Die Zeichen» (21.09.2026): Mit 82 % hellte ein weisses Bild
    /// den Streifen so weit auf, dass alle farbigen Aussagen unlesbar wurden.
    /// `testJedesWortIstAufDemStreifenLesbar` rechnet das für jedes Zeichen nach, über
    /// einem weissen und einem schwarzen Bild.
    public static let streifen = Farbton(hex: "080a0d")
    public static let streifenDeckung = 0.94

    /// Die Schrift eines Vorbehalts im Streifen.
    ///
    /// **Bewusst keine der Urteilsfarben:** Ein Vorbehalt ist kein viertes Urteil, und in
    /// Gelb gelesen hiesse er «nicht gemessen» — die Geometrie *ist* aber gemessen.
    public static let vorbehaltSchrift = Farbton(hex: "e6e8ec")

    /// Das Zeichen für ein Bild.
    ///
    /// - Parameters:
    ///   - urteil: Das Urteil des Servers.
    ///   - lesart: Prüfen oder Entwerfen — der Schalter am Bild.
    ///   - pruefzahl: Die Zahl zum Urteil (wie gut das Bild zur Geometrie passt).
    ///     `nil` heisst **nicht übertragen**, nie 0.
    ///   - unterschied: Nur beim Entwerfen: der Abstand zum Modell, «kein Urteil». Eine
    ///     eigene Angabe, weil es eine andere Grösse ist als die Prüfzahl — die App rechnet
    ///     die eine nie aus der anderen (Entscheid 13).
    ///   - hinweise: Die Hinweise des Servers zu diesem Bild, unverändert.
    public init(urteil: Urteil, lesart: Bildlesart, pruefzahl: Double?,
                unterschied: Double? = nil, hinweise: [String] = []) {
        let art: Zeichenart
        let zahl: Zahlanzeige
        switch (lesart, urteil) {
        // OHNE MESSUNG KEINE ZAHL, in beiden Lesarten. Kommt trotzdem eine mit, ist sie
        // nicht die Zahl dieses Urteils — sie zu zeigen hiesse, «nicht gemessen» mit
        // einem Messwert zu versehen.
        case (_, .nichtGemessen):
            art = lesart == .entwerfen ? .entwurf : .nichtGemessen
            zahl = .keine
        case (.entwerfen, _):
            art = .entwurf
            zahl = unterschied.map(Pruefzeichen.schreibe) ?? .keine
        case (.pruefen, .bestanden):
            art = .bestanden
            zahl = Pruefzeichen.schreibe(pruefzahl)
        case (.pruefen, .durchgefallen):
            art = .durchgefallen
            zahl = Pruefzeichen.schreibe(pruefzahl)
        }
        self.init(art: art, zahl: zahl, vorbehalte: Pruefzeichen.vorbehalte(aus: hinweise))
    }

    /// Das Zeichen aus dem Feld `zeichen`, wie `GET /api/projekt` es je Bild liefert.
    ///
    /// Ein unbekanntes Zeichen wird **nicht** geraten: Es bekommt die eigene Art
    /// `.unbekannt` — weder «nicht gemessen» noch gar kein Zeichen.
    public init(zeichen: String, lesart: Bildlesart, pruefzahl: Double?,
                unterschied: Double? = nil, hinweise: [String] = []) {
        if let urteil = Urteil(zeichen: zeichen) {
            self.init(urteil: urteil, lesart: lesart, pruefzahl: pruefzahl,
                      unterschied: unterschied, hinweise: hinweise)
        } else {
            self.init(art: .unbekannt, zahl: .keine,
                      vorbehalte: Pruefzeichen.vorbehalte(aus: hinweise))
        }
    }

    private init(art: Zeichenart, zahl: Zahlanzeige, vorbehalte: [Vorbehalt]) {
        self.art = art
        self.zahl = zahl
        self.vorbehalte = vorbehalte
    }

    /// Die Hauptzeile im Streifen: Wort und Zahl.
    ///
    /// Beim Entwerfen heisst die Zahl «Unterschied», damit sie nicht als Prüfzahl gelesen
    /// wird.
    public var zeile: String {
        guard let t = zahl.text else { return art.wort }
        if art == .entwurf, case .wert = zahl {
            return art.wort + " · Unterschied " + t
        }
        return art.wort + " · " + t
    }

    /// Alle Zeilen, die auf dem Bild stehen — auch im geteilten (Entscheid 20).
    public var zeilen: [String] {
        [zeile] + vorbehalte.map { $0.kurz }
    }

    /// Was ein Bildschirmleser vorliest: dasselbe wie die Zeilen, in ganzen Wörtern.
    public var vorlesetext: String {
        var teile = ["Prüfzeichen: " + zeile.replacingOccurrences(of: " · ", with: ", ")]
        teile += vorbehalte.map { $0.satz }
        return teile.joined(separator: ". ")
    }

    // ------------------------------------------------------------------ intern

    /// Eine Zahl mit zwei Stellen und Punkt, unabhängig von der Spracheinstellung des
    /// Geräts — oder `.fehlt`, wenn keine lesbare da ist.
    static func schreibe(_ wert: Double?) -> Zahlanzeige {
        guard let wert = wert, wert.isFinite else { return .fehlt }
        let text = String(format: "%.2f", locale: Locale(identifier: "en_US_POSIX"), wert)
        // «-0.00» ist dieselbe Zahl wie «0.00» und sähe aus wie ein Vorzeichenbefund.
        return .wert(text == "-0.00" ? "0.00" : text)
    }

    static func vorbehalte(aus hinweise: [String]) -> [Vorbehalt] {
        // ERKANNT AM FESTEN ANFANG, nicht am ersten Platz der Liste. Der Server setzt ihn
        // heute nach vorne; ein zweiter Hinweis davor darf ihn nicht unsichtbar machen.
        let treffer = hinweise.first { h in
            h.drop(while: { $0.isWhitespace }).hasPrefix(anfangSkizzeNichtAngekommen)
        }
        guard let satz = treffer else { return [] }
        return [Vorbehalt(kurz: anfangSkizzeNichtAngekommen + " — aus Tiefenkarte und Text gerechnet",
                          satz: satz.trimmingCharacters(in: .whitespacesAndNewlines))]
    }
}
