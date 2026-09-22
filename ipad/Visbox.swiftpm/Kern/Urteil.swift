import Foundation

/// Das Urteil über ein Bild — **drei Fälle, und der dritte ist kein Nein.**
///
/// Im Projekt (`projekt.json`) steht es als `geometrie_bestanden`: `true`, `false` oder
/// `null`. `null` heisst **nicht gemessen** und nie «in Ordnung», aber auch nie «nicht
/// bestanden». Die Fläche des Servers liefert dasselbe als Zeichen: `bestanden`,
/// `durchgefallen`, `nicht-gemessen`.
///
/// **Warum das kein `Bool?` ist.** Ein optionales `Bool` lädt zu `urteil ?? false` ein —
/// eine Zeile, die aus «nicht gemessen» still «durchgefallen» macht, oder mit `?? true`
/// ein grünes Abzeichen an ein ungeprüftes Bild hängt. Ein eigener Fall lässt sich nicht
/// mit einem Standardwert wegkürzen; wer ihn behandeln will, muss ihn nennen.
///
///     *Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes — und auch nicht wie
///     gar nichts.*
public enum Urteil: Equatable, Hashable, Sendable {
    case bestanden
    case durchgefallen
    case nichtGemessen

    /// Aus dem Wert, wie er im Projekt steht. `nil` wird **nicht gemessen**.
    public init(bestanden: Bool?) {
        switch bestanden {
        case .some(true): self = .bestanden
        case .some(false): self = .durchgefallen
        case .none: self = .nichtGemessen
        }
    }

    /// Aus dem Zeichen, wie es `GET /api/projekt` je Bild liefert (Feld `zeichen`).
    ///
    /// Ein **unbekanntes** Zeichen gibt `nil` — und nicht «nicht gemessen». Ein Zeichen,
    /// das diese App nicht kennt, kommt von einem neueren Server; es als «nicht gemessen»
    /// zu lesen wäre geraten, und geraten sieht in der Anzeige genauso aus wie gewusst.
    public init?(zeichen: String) {
        switch zeichen {
        case "bestanden": self = .bestanden
        case "durchgefallen": self = .durchgefallen
        case "nicht-gemessen": self = .nichtGemessen
        default: return nil
        }
    }

    /// Zurück in die Form des Projekts: `true`, `false` oder `nil`.
    public var bestanden: Bool? {
        switch self {
        case .bestanden: return true
        case .durchgefallen: return false
        case .nichtGemessen: return nil
        }
    }

    /// Das Zeichen, wie der Server es schreibt.
    public var zeichen: String {
        switch self {
        case .bestanden: return "bestanden"
        case .durchgefallen: return "durchgefallen"
        case .nichtGemessen: return "nicht-gemessen"
        }
    }
}

extension Urteil: Codable {
    /// Liest `true`, `false` oder `null` — **und sonst nichts.**
    ///
    /// Eine Zahl (`0`, `1`) oder ein Text an dieser Stelle wird abgelehnt und nicht
    /// gedeutet. Dieselbe Entscheidung wie in `aiimaging.projekt.vermerke_bild`: *Eine
    /// Zahl, die sich als Urteil ausgibt, beantwortet die Frage, ohne sie gestellt zu
    /// haben.*
    ///
    /// Ein **fehlendes** Feld erreicht diese Stelle nicht; wer ein Urteil als Feld liest,
    /// nimmt `decodeIfPresent(...) ?? .nichtGemessen` — fehlt es, ist es nicht gemessen.
    public init(from decoder: Decoder) throws {
        let behaelter = try decoder.singleValueContainer()
        if behaelter.decodeNil() {
            self = .nichtGemessen
            return
        }
        self.init(bestanden: try behaelter.decode(Bool.self))
    }

    public func encode(to encoder: Encoder) throws {
        var behaelter = encoder.singleValueContainer()
        if let wert = bestanden {
            try behaelter.encode(wert)
        } else {
            try behaelter.encodeNil()
        }
    }
}
