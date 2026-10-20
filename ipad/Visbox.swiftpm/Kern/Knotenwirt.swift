import Foundation

/// Die zweite Brücke der Knotenansicht, **«visboxWirt»** (Plan UI-Gleichheit S1/S2, Entscheide
/// 115/116, 20.10.2026) — neben `Kibruecke` («visboxKi», der KI-Werkzeugsatz).
///
/// Die Knotenansicht zeigt seit S1/S2 die Kopfteile von KosmoOrbit (Palette am Logo, Einstellungs-
/// und Speichern-Kreis, Zweitgruppe, Claude-Marke mit Karten und Selbständigkeit). Was diese Teile
/// von der App brauchen, geht hier hin und her (`apps/visbox-knoten/src/wirt-bruecke.ts`):
///
/// * **Seite → App** (`Wunsch`): bereit, Modus (Karte | Coop | Voll), «Wer rechnet?» öffnen, Claude
///   an/aus, Startansicht oder Visbox-Seite öffnen, Einstellungen öffnen.
/// * **App → Seite** (`Lage`, als `window.visboxWirt.lage({...})`): Leitung, Sperre, Heim-PC-Chip,
///   ob Claude verbunden ist, Fassung, Modus, Thema.
///
/// **Seit S3/S4** (Kugel, Gespraechsfeld, Einstellungs-Insel, 20.10.2026) dazu: das Gespraech mit dem
/// Assistenten (Seite → App `assistent`, App → Seite `assistent` — die Regeln bleiben im Kern,
/// `Assistentengespraech`), «Wer rechnet?» (`rechnerwahl`, die Wahl ueber `rechner`), «Claude über MCP»
/// (`claudeMcp`), «Neuigkeiten» und was die Seite ueber das Neuladen hinaus behaelt (`merke`). Die
/// Bausteine dazu stehen in `Knotenwirtinseln.swift`.
///
/// **Das Heim-PC-Kennwort läuft nie durch die Seite** (Entscheid 116 (6)): `Lage` hat kein Feld
/// dafür, und die Seite liest nur die genannten Felder.
///
/// Was hier steht, ist rein und geprüft (`KnotenwirtTests`); gedrückt und gezeichnet wird in der
/// Mac-App (`Start/Knotenki.swift`, `Start/Arbeitsansicht.swift`).
public enum Knotenwirt {
    /// Der Name der Schnittstelle (`window.visboxWirt`) und des Boten
    /// (`webkit.messageHandlers.visboxWirt`) — aus der Marke gebildet wie `Kibruecke.name`.
    public static let name = Mcp.servername + "Wirt"

    /// Wohin die Palette am Logo führt. Das Wort der Seite («<marke>-seite») kommt aus der Marke.
    public enum Ziel: Equatable, Sendable {
        case startansicht
        case visboxSeite
        /// «Am Mac einrichten» (Einstellungs-Insel › Heim-PC): das Blatt mit Adresse und Kennwort.
        case einrichten
        /// «Aktualisieren …» (Einstellungs-Insel › Neuigkeiten).
        case aktualisieren

        public var wort: String {
            switch self {
            case .startansicht: return "startansicht"
            case .visboxSeite: return Mcp.servername + "-seite"
            case .einrichten: return "einrichten"
            case .aktualisieren: return "aktualisieren"
            }
        }

        public init?(wort: String) {
            switch wort {
            case Ziel.startansicht.wort: self = .startansicht
            case Ziel.visboxSeite.wort: self = .visboxSeite
            case Ziel.einrichten.wort: self = .einrichten
            case Ziel.aktualisieren.wort: self = .aktualisieren
            default: return nil
            }
        }
    }

    /// Was die Seite von der App will.
    public enum Wunsch: Equatable, Sendable {
        case bereit
        case modus(Selbstaendigkeit)
        /// Der Heim-PC-Chip: «Wer rechnet?» öffnen.
        case rechner
        case claude(an: Bool)
        case oeffne(Ziel)
        /// Das Blatt «Einrichten» an einem Abschnitt (z. B. «claude», «rechner»).
        case einstellung(abschnitt: String?)
        /// «Wer rechnet?» in der Einstellungs-Insel: diese Arbeit an diesem Ort (S4).
        case rechnerWaehlen(Rechenarbeit, Rechnerort)
        /// Das Gespraechsfeld der Kugel (S3).
        case assistent(Assistentenwunsch)
        /// Eine Einstellung der Seite, die die App ueber das Neuladen hinaus behaelt (S4) — nur
        /// Schluessel aus `merkbar`, Werte hoechstens `merkWertHoechstens` Zeichen.
        case merke(schluessel: String, wert: String)
    }

    /// Ein Wunsch aus der Nachricht der Seite — `nil`, wenn sie unvollständig oder unbekannt ist.
    public static func wunsch(aus wert: JSONWert) -> Wunsch? {
        switch wert["art"]?.alsText {
        case "bereit":
            return .bereit
        case "modus":
            return wert["modus"]?.alsText.flatMap(Selbstaendigkeit.init(rawValue:)).map(Wunsch.modus)
        case "rechner":
            // MIT ARBEIT UND ORT eine Wahl; beide oder keines — halb heisst unbekannt.
            switch (wert["arbeit"]?.alsText, wert["ort"]?.alsText) {
            case (nil, nil):
                return .rechner
            case (let a?, let o?):
                guard let arbeit = Rechenarbeit(rawValue: a), let ort = Rechnerort(rawValue: o) else { return nil }
                return .rechnerWaehlen(arbeit, ort)
            default:
                return nil
            }
        case "assistent":
            return Assistentenwunsch(aus: wert).map(Wunsch.assistent)
        case "merke":
            guard let schluessel = wert["schluessel"]?.alsText, merkbar.contains(schluessel),
                  let text = wert["wert"]?.alsText, text.count <= merkWertHoechstens else { return nil }
            return .merke(schluessel: schluessel, wert: text)
        case "claude":
            return wert["an"]?.alsWahrheit.map { Wunsch.claude(an: $0) }
        case "oeffne":
            return wert["ziel"]?.alsText.flatMap { Ziel(wort: $0) }.map(Wunsch.oeffne)
        case "einstellung":
            return .einstellung(abschnitt: wert["abschnitt"]?.alsText)
        default:
            return nil
        }
    }

    /// Das Thema der Knotenansicht wie in KosmoOrbit: «orbit» (Kosmos, dunkel) ist die Vorgabe.
    public enum Thema: String, Equatable, Sendable, CaseIterable {
        case paper
        case orbit

        public static let vorgabe: Thema = .orbit
        /// Die Einstellung der App — das Webfenster hat keinen bleibenden Speicher.
        public static let einstellung = "knoten.thema"

        public init(gemerkt: String?) {
            self = gemerkt.flatMap(Thema.init(rawValue:)) ?? .vorgabe
        }

        public var anderes: Thema { self == .orbit ? .paper : .orbit }

        /// Der Menüpunkt, wortgleich zur Befehlspalette von KosmoOrbit.
        public static let menuepunkt = "Thema wechseln (Papier/Kosmos)"
    }

    /// Der Chip an der Stelle des Sync-Chips: Text und Farbe wie dort («gut», «aus», «warnung»).
    public struct Rechnerchip: Equatable, Sendable {
        public let text: String
        public let ton: String

        public init(text: String, ton: String) {
            self.text = text
            self.ton = ton
        }
    }

    /// Der Heim-PC-Chip aus der Leitung — kurz wie der Sync-Chip (`syncChipText` in KosmoOrbit).
    public static func rechnerchip(eingerichtet: Bool, lage: Leitungslage) -> Rechnerchip {
        guard eingerichtet else { return Rechnerchip(text: "Heim-PC · nicht gekoppelt", ton: "aus") }
        switch lage {
        case .verbunden: return Rechnerchip(text: "Heim-PC · bereit", ton: "gut")
        case .startet: return Rechnerchip(text: "Heim-PC · verbindet …", ton: "warnung")
        case .getrennt: return Rechnerchip(text: "Heim-PC · verbindet neu", ton: "warnung")
        case .ohneRechner: return Rechnerchip(text: "Heim-PC · nicht erreichbar", ton: "warnung")
        case .abgewiesen: return Rechnerchip(text: "Heim-PC · Anmeldung abgewiesen", ton: "warnung")
        }
    }

    /// Was die App der Seite sagt.
    public struct Lage: Equatable, Sendable {
        public var leitung: String?
        public var sperre: String?
        public var rechner: Rechnerchip
        public var claudeVerbunden: Bool
        public var version: String
        public var modus: Selbstaendigkeit
        public var thema: Thema
        /// S3: das Gespraech mit dem Assistenten — `nil`, solange die App keines fuehrt.
        public var assistent: Assistentenlage?
        /// S4: «Wer rechnet?», «Claude über MCP», «Neuigkeiten» fuer die Einstellungs-Insel.
        public var rechnerwahl: Rechnerwahllage?
        public var claudeMcp: Claudemcplage?
        public var neuigkeiten: Neuigkeitenlage?

        public init(leitung: String?, sperre: String?, rechner: Rechnerchip, claudeVerbunden: Bool,
                    version: String, modus: Selbstaendigkeit, thema: Thema,
                    assistent: Assistentenlage? = nil, rechnerwahl: Rechnerwahllage? = nil,
                    claudeMcp: Claudemcplage? = nil, neuigkeiten: Neuigkeitenlage? = nil) {
            self.leitung = leitung
            self.sperre = sperre
            self.rechner = rechner
            self.claudeVerbunden = claudeVerbunden
            self.version = version
            self.modus = modus
            self.thema = thema
            self.assistent = assistent
            self.rechnerwahl = rechnerwahl
            self.claudeMcp = claudeMcp
            self.neuigkeiten = neuigkeiten
        }

        /// Als JSON-Wert — genau die Felder, die `liesLage` in der Seite liest.
        public var wert: JSONWert {
            var o: [String: JSONWert] = [
                "leitung": leitung.map(JSONWert.text) ?? .null,
                "sperre": sperre.map(JSONWert.text) ?? .null,
                "rechner": .objekt(["text": .text(rechner.text), "ton": .text(rechner.ton)]),
                "claude": .objekt(["verbunden": .wahrheit(claudeVerbunden)]),
                "version": .text(version),
                "modus": .text(modus.rawValue),
                "thema": .text(thema.rawValue),
            ]
            if let assistent { o["assistent"] = assistent.wert }
            if let rechnerwahl { o["rechnerwahl"] = rechnerwahl.wert }
            if let claudeMcp { o["claudeMcp"] = claudeMcp.wert }
            if let neuigkeiten { o["neuigkeiten"] = neuigkeiten.wert }
            return .objekt(o)
        }
    }

    /// Ob Claude als verbunden gilt — dieselbe Regel wie die Zeile der Leiste (`Claudezeile`).
    public static func claudeVerbunden(lage: Claudehoererlage, letzterKontakt: Date?,
                                       jetzt: Date = Date()) -> Bool {
        Claudezeile.zeile(lage: lage, letzterKontakt: letzterKontakt, jetzt: jetzt).titel
            == "Claude verbunden"
    }

    /// Die Fassung für die Zweitgruppe («v0.4.0»), aus der laufenden Nummer der App.
    public static func version(_ nummer: String?) -> String {
        guard let nummer, !nummer.isEmpty else { return "" }
        return nummer.hasPrefix("v") ? nummer : "v" + nummer
    }

    /// Der JavaScript-Rumpf, der die Lage in die Seite legt (für `evaluateJavaScript`). Ohne
    /// Schnittstelle (die Seite lädt noch) geschieht nichts — die Seite meldet «bereit», dann
    /// kommt die Lage noch einmal.
    public static func rumpf(_ lage: Lage) -> String? {
        guard let daten = try? lage.wert.daten(), let text = String(data: daten, encoding: .utf8) else {
            return nil
        }
        return "window.\(name) && window.\(name).lage(\(text));"
    }
}
