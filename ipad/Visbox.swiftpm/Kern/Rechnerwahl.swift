import Foundation

// DIE RECHNER-WAHL — wer welche Arbeit rechnet («Visbox eigenständig», Schritt 6; Plan §5;
// Blatt 28, Feld 2 «Einrichten › Rechner», 20.10.2026).
//
// Drei Arbeiten brauchen einen Rechner: der Blender-Render, das Bildmodell und die Bedien-KI
// (das Sprachmodell der Assistent-Leiste). Je Arbeit gibt es zwei Orte: den Heim-PC und
// dieses Gerät. Vorgabe ist der Heim-PC.
//
// VORBEREITET, NICHT VERDRAHTET: Heute rechnet alles am Heim-PC. «Dieses Gerät» steht
// sichtbar da, aber gesperrt mit seinem Grund (`Rechnerort.verfuegbarkeit`), bis ein lokaler
// Rechner gebaut ist — dann ist er derselbe Abholer am Mac mit eigenem Auftragsordner, kein
// zweiter Weg (Plan §5). Die Wahl wird gespeichert (App-Einstellungen, `alsDaten`/`aus`),
// aendert aber am Weg nichts: `wirksam` gibt fuer jede Arbeit den Heim-PC, solange «dieses
// Geraet» nicht verfuegbar ist — auch wenn eine spaetere Fassung «dieses Geraet» gespeichert
// haette und diese hier sie liest.
//
// CLAUDE UEBER MCP IST NICHT DIESE WAHL (Owner, Plan §5): Claude steuert die App von aussen,
// immer und unabhaengig davon; die Wahl «Bedien-KI» gilt nur fuer die Assistent-Leiste.
//
// Die Pruefung, ob es Blender am Mac gibt, macht die App (`/Applications/Blender.app`,
// `Rechnerwahl.blenderOrt`); der Kern bekommt nur das Ergebnis. Blender ist GPL und bliebe
// auch am Mac ein eigener Prozess (Regel 2) — hier wird es nicht einmal gestartet.

/// Eine Arbeit, die einen Rechner braucht.
public enum Rechenarbeit: String, CaseIterable, Codable, Equatable, Sendable {
    case blenderRender
    case bildmodell
    case bedienKI

    /// Wie die Zeile heisst (Blatt 28, Feld 2).
    public var titel: String {
        switch self {
        case .blenderRender: return "Blender-Render"
        case .bildmodell: return "Bildmodell"
        case .bedienKI: return "Bedien-KI"
        }
    }
}

/// Wo eine Arbeit gerechnet wird.
public enum Rechnerort: String, CaseIterable, Codable, Equatable, Sendable {
    case heimPC
    case diesesGeraet

    public var titel: String {
        switch self {
        case .heimPC: return "Heim-PC"
        case .diesesGeraet: return "Dieses Gerät"
        }
    }
}

/// Ob ein Ort für eine Arbeit wählbar ist, und wenn nicht, warum.
public enum Verfuegbarkeit: Equatable, Sendable {
    case verfuegbar
    case nichtVerfuegbar(grund: String)

    public var waehlbar: Bool { self == .verfuegbar }

    /// «nicht verfügbar — kein Blender gefunden» (Blatt 28), oder `nil`, wenn wählbar.
    public var zeile: String? {
        guard case .nichtVerfuegbar(let grund) = self else { return nil }
        return grund.isEmpty ? Rechnerwahl.nichtVerfuegbar
            : Rechnerwahl.nichtVerfuegbar + " — " + grund
    }
}

/// Was die App über **dieses Gerät** weiss — erhoben am Mac, entschieden hier.
public struct Rechnerbefund: Equatable, Sendable {
    /// Liegt Blender am üblichen Ort (`Rechnerwahl.blenderOrt`)?
    public let blenderGefunden: Bool
    /// Der Arbeitsspeicher in Byte (`ProcessInfo.physicalMemory`). Auf einem Mac mit
    /// Apple-Chip teilen sich Rechenwerk und Grafik denselben Speicher; er ist darum die
    /// ehrlichste Zahl für «Grafikspeicher», die ohne weiteres Framework zu haben ist.
    public let arbeitsspeicher: UInt64

    public init(blenderGefunden: Bool, arbeitsspeicher: UInt64) {
        self.blenderGefunden = blenderGefunden
        self.arbeitsspeicher = arbeitsspeicher
    }
}

/// Die Wahl je Arbeit — gespeichert in den App-Einstellungen.
public struct Rechnerwahl: Equatable, Sendable {

    // ------------------------------------------------------------- die Setzungen

    /// Der Schlüssel in den App-Einstellungen. Mit Fassung, damit eine spätere Form neben
    /// dieser lesbar bleibt.
    public static let schluessel = "rechnerwahl.v1"
    /// Wo die App nach Blender sieht — nur dort (Owner-Auftrag Schritt 6).
    public static let blenderOrt = "/Applications/Blender.app"
    /// **Gesetzt, nicht gemessen:** Ab so viel Speicher hiesse der Grund beim Bildmodell nicht
    /// mehr «zu wenig Grafikspeicher», sondern «kommt später». 32 GiB — die Bildmodelle des
    /// Heim-PC brauchen dort eine Grafikkarte mit 24 GB und mehr, und ein Mac teilt seinen
    /// Speicher mit allem anderen. Wird mit dem lokalen Rechner gemessen.
    public static let bildmodellSpeicher: UInt64 = 32 * 1024 * 1024 * 1024

    public static let titel = "Wer rechnet?"
    public static let untertitel = "Je Arbeit wählbar. Vorgabe: Heim-PC."
    public static let nichtVerfuegbar = "nicht verfügbar"
    public static let keinBlender = "kein Blender gefunden"
    public static let blenderSpaeter = "lokales Rechnen kommt in einer späteren Fassung"
    public static let zuWenigGrafikspeicher = "zu wenig Grafikspeicher"
    public static let bildmodellSpaeter = "kommt in einer späteren Fassung"
    /// Blatt 28, Feld 2 — der Name kommt aus der Marke (er steht in keiner Zeichenkette).
    public static let mcpSatz = "Claude über MCP steuert " + Marke.name + " immer — unabhängig "
        + "von dieser Wahl. Die Wahl gilt für die Assistent-Leiste in der App."
    /// Unter den Zeilen: was die Wahl heute bewirkt — nichts am Weg.
    public static let heuteSatz = "Heute rechnet alles am Heim-PC; die Wahl wird gespeichert "
        + "und gilt, sobald dieses Gerät rechnen kann."

    // ------------------------------------------------------------------ der Stand

    private var orte: [Rechenarbeit: Rechnerort]

    /// Die Vorgabe: alles am Heim-PC.
    public static let vorgabe = Rechnerwahl(orte: [:])

    private init(orte: [Rechenarbeit: Rechnerort]) {
        self.orte = orte
    }

    /// Was gewählt ist (gespeichert), auch wenn es gerade nicht verfügbar ist.
    public func ort(fuer arbeit: Rechenarbeit) -> Rechnerort {
        orte[arbeit] ?? .heimPC
    }

    /// Wo **wirklich** gerechnet wird: der gewählte Ort, wenn er verfügbar ist, sonst der
    /// Heim-PC. Heute ist das immer der Heim-PC.
    public func wirksam(fuer arbeit: Rechenarbeit, befund: Rechnerbefund) -> Rechnerort {
        let gewaehlt = ort(fuer: arbeit)
        return Rechnerwahl.verfuegbarkeit(gewaehlt, fuer: arbeit, befund: befund).waehlbar
            ? gewaehlt : .heimPC
    }

    /// Wählen — **nur, was verfügbar ist.** Gibt zurück, ob die Wahl gilt; ein gesperrter
    /// Ort ändert nichts.
    @discardableResult
    public mutating func waehle(_ neu: Rechnerort, fuer arbeit: Rechenarbeit,
                                befund: Rechnerbefund) -> Bool {
        guard Rechnerwahl.verfuegbarkeit(neu, fuer: arbeit, befund: befund).waehlbar else {
            return false
        }
        orte[arbeit] = neu == .heimPC ? nil : neu
        return true
    }

    // ------------------------------------------------------------- die Verfügbarkeit

    /// Ob `ort` für `arbeit` wählbar ist. Der Heim-PC immer (ob er gerade antwortet, sagt die
    /// Leitung, nicht die Wahl); dieses Gerät heute nie — mit dem Grund, der für dieses Gerät
    /// gilt.
    public static func verfuegbarkeit(_ ort: Rechnerort, fuer arbeit: Rechenarbeit,
                                      befund: Rechnerbefund) -> Verfuegbarkeit {
        guard ort == .diesesGeraet else { return .verfuegbar }
        switch arbeit {
        case .blenderRender:
            // AUCH MIT BLENDER NICHT: Der lokale Abholer ist nicht gebaut. Gefunden heisst nur,
            // dass der Grund ein anderer ist.
            return .nichtVerfuegbar(grund: befund.blenderGefunden ? blenderSpaeter : keinBlender)
        case .bildmodell:
            return .nichtVerfuegbar(grund: befund.arbeitsspeicher < bildmodellSpeicher
                                    ? zuWenigGrafikspeicher : bildmodellSpaeter)
        case .bedienKI:
            return .nichtVerfuegbar(grund: "")
        }
    }

    /// Der kleine Zusatz am Heim-PC (Blatt 28: «· verbunden», bei der Bedien-KI
    /// «· Sprachmodell») — aus der Lage der Leitung.
    public static func zusatzHeim(fuer arbeit: Rechenarbeit, lage: Leitungslage,
                                  eingerichtet: Bool) -> String {
        guard eingerichtet else { return "nicht eingerichtet" }
        let leitung: String
        switch lage {
        case .verbunden: leitung = "verbunden"
        case .startet: leitung = "wird gefragt"
        case .getrennt, .ohneRechner: leitung = "nicht erreichbar"
        case .abgewiesen: leitung = "weist ab"
        }
        if arbeit == .bedienKI {
            return lage == .verbunden ? "Sprachmodell" : "Sprachmodell · " + leitung
        }
        return leitung
    }

    // ------------------------------------------------------------- das Speichern

    /// Für die App-Einstellungen: nur, was vom Heim-PC abweicht, als JSON-Objekt.
    public func alsDaten() -> Data {
        var roh: [String: String] = [:]
        for (arbeit, ort) in orte { roh[arbeit.rawValue] = ort.rawValue }
        return (try? JSONSerialization.data(withJSONObject: roh, options: [.sortedKeys]))
            ?? Data("{}".utf8)
    }

    /// Aus den App-Einstellungen. **Nichts oder Unlesbares gibt die Vorgabe**, unbekannte
    /// Arbeiten und Orte werden übergangen — eine Einstellung soll den Start nie aufhalten.
    public static func aus(daten: Data?) -> Rechnerwahl {
        guard let daten,
              let roh = (try? JSONSerialization.jsonObject(with: daten)) as? [String: Any] else {
            return .vorgabe
        }
        var orte: [Rechenarbeit: Rechnerort] = [:]
        for (schluessel, wert) in roh {
            guard let arbeit = Rechenarbeit(rawValue: schluessel),
                  let text = wert as? String, let ort = Rechnerort(rawValue: text),
                  ort != .heimPC else { continue }
            orte[arbeit] = ort
        }
        return Rechnerwahl(orte: orte)
    }
}
