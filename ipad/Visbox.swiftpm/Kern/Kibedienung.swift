import Foundation

// DIE KI BEDIENT DIE KNOTENANSICHT — die reine Logik von Stufe 3 und 4 des Plans
// «KI-Bedienung» (`docs/PLAN_KI_BEDIENUNG_2026-10-20.md`; Entscheide 105–106f, 108, 114).
//
// Die Knotenansicht traegt den KI-Werkzeugsatz (`ki-werkzeuge.ts`, woertlich aus KosmoOrbit) und
// haengt ihn als `window.visboxKi` an (`apps/visbox-knoten/src/ki-wirt.ts`). Die Mac-App ruft ihn
// und hoert seine Ereignisse. Hier steht, was die Antworten HEISSEN — ohne WebKit und ohne Netz,
// darum unter Linux mit Proben (`KibedienungTests`):
//
//  * `Kibruecke` — die Antworten von `window.visboxKi` als `Traegerantwort` und `Mcpwerkzeug`.
//    **Ob eine Karte noetig ist, sagt die Antwort der Knotenansicht**, nicht die Art des Werkzeugs
//    allein: Ein `vis_paket` ist «aendern», wird mit einem Loeschen darin aber eine Karte.
//  * `Kiereignis`, `Kikarte`, `Kileistenstand` — was die Assistent-Leiste zeigt (Blatt 30, Feld 1).
//  * `Claudezeile`, `Assistentenkopf` — die zwei Zeilen oben in der Leiste.
//  * `Macwerkzeuge` — die Werkzeuge der Mac-App selbst (Mappe, Skizzen, Lauf abbrechen, Bild
//    ansehen), mit ihren Wegen zum Heim-PC und den Saetzen ihrer Antworten.
//  * `Claudedesktop` — der Eintrag fuer Claude Desktop («Visbox hinzufügen», Blatt 30, Feld 3).
//
// Was hier NIE steht: ein Weg, der die Grafikkarte freigibt. Den Knopf «Freigeben» am
// Render-Knoten drueckt ein Mensch (Entscheid 106b).

// ===================================================================== wer ruft

/// Wer ein Werkzeug ruft — dieselben zwei Worte wie `KiUrheber` in `ki-werkzeuge.ts`.
public enum Kiurheber: String, Equatable, Sendable, CaseIterable {
    case claude
    case assistent

    /// Fuer den Kopf der Karte: «Vorschlag von Claude», «Vorschlag des Assistenten».
    public var vonWem: String {
        switch self {
        case .claude: return "von Claude"
        case .assistent: return "des Assistenten"
        }
    }

    /// Fuer den Taetigkeitsstrom: «Claude …», «Der Assistent …».
    public var name: String {
        switch self {
        case .claude: return "Claude"
        case .assistent: return "Der Assistent"
        }
    }
}

// ===================================================================== die Bruecke

public enum Kibruecke {
    /// Der Name der Schnittstelle in der Seite (`window.visboxKi`) und des Boten
    /// (`webkit.messageHandlers.visboxKi`) — aus der Marke gebildet, wie `ki-wirt.ts` ihn schreibt.
    public static let name = Mcp.servername + "Ki"

    /// Ein Aufruf an die Schnittstelle als JavaScript-Rumpf fuer `callAsyncJavaScript`; die
    /// Antwort kommt als JSON-Text (`alsText`). `aufruf` ist z. B. `rufe(JSON.parse(ruf), modus)`.
    public static func rumpf(_ aufruf: String) -> String {
        "return \(name).alsText(\(name).\(aufruf));"
    }

    /// Wie `rumpf`, aber fuer einen Weg, der ein Versprechen gibt (Blick und Maus, Stufe 6):
    /// `callAsyncJavaScript` wartet auf `await`.
    public static func rumpfWartend(_ aufruf: String) -> String {
        "return \(name).alsText(await \(name).\(aufruf));"
    }

    /// Der Ruf an die Knotenansicht als JSON-Text (`ruf` in `rufe(JSON.parse(ruf), modus)`) —
    /// derselbe fuer Claude und den Assistenten, nur der Urheber unterscheidet sie (Stufe 5).
    public static func ruf(_ aufruf: Mcpaufruf, urheber: Kiurheber) -> String? {
        let wert: JSONWert = .objekt([
            "kennung": .text(aufruf.kennung), "werkzeug": .text(aufruf.werkzeug),
            "argumente": .objekt(aufruf.argumente), "urheber": .text(urheber.rawValue),
        ])
        return (try? wert.daten()).flatMap { String(data: $0, encoding: .utf8) }
    }

    /// Der Satz, wenn die Knotenansicht nicht offen ist — jedes ihrer Werkzeuge antwortet so.
    public static let nichtOffen = "Die Knotenansicht ist in \(Marke.name) nicht offen — nichts wurde "
        + "ausgeführt. Der Architekt öffnet sie mit «Schon anfangen» (oder «Zurück zu den Knoten»); "
        + "danach geht der Aufruf."
    /// Der Satz, wenn die Knotenansicht geantwortet hat, aber nichts Lesbares.
    public static let unlesbar = "Die Knotenansicht hat nicht lesbar geantwortet — nichts wurde "
        + "vorgeschlagen."
    /// Die Datei im Bau der Knotenansicht (`dist/ki-werkzeugliste.json`, `knoten_bau.py`).
    public static let listendatei = "ki-werkzeugliste.json"
    /// Das Format dieser Datei — eine andere Fassung wird nicht geraten, sondern nicht gelesen.
    public static let listenformat = "\(Mcp.servername).ki-werkzeugliste/v1"

    /// Die Werkzeuge aus der Antwort von `visboxKi.werkzeuge()` (eine Liste) oder aus der Datei
    /// im Bau (`{format, werkzeuge}`). Ein Eintrag ohne gueltigen Namen, ohne Objekt-Schema oder
    /// mit unbekannter Art faellt weg — der Kern boete ihn sonst Claude an.
    public static func werkzeuge(aus wert: JSONWert) -> [Mcpwerkzeug] {
        let liste: [JSONWert]
        if let l = wert.alsListe {
            liste = l
        } else if wert["format"]?.alsText == listenformat, let l = wert["werkzeuge"]?.alsListe {
            liste = l
        } else {
            return []
        }
        return liste.compactMap { w in
            guard let name = w["name"]?.alsText, Mcpwerkzeug.nameIstGueltig(name),
                  let schema = w["inputSchema"], schema["type"]?.alsText == "object",
                  let art = w["art"]?.alsText.flatMap(Werkzeugart.init(rawValue:)) else {
                return nil
            }
            return Mcpwerkzeug(name: name, beschreibung: w["description"]?.alsText ?? "",
                               eingabe: schema, art: art)
        }
    }

    /// Die Antwort von `visboxKi.rufe(...)`: `{sofort: {ok, text}}` → fertig (ein Fehlschlag,
    /// wenn `ok` falsch ist); `{karte: {zusammenfassung}}` → eine Karte liegt.
    public static func traegerantwort(aus wert: JSONWert) -> Traegerantwort {
        if let sofort = wert["sofort"], let text = sofort["text"]?.alsText {
            return .ergebnis(Mcpergebnis(text: text, fehler: sofort["ok"]?.alsWahrheit != true))
        }
        if let karte = wert["karte"], let satz = karte["zusammenfassung"]?.alsText {
            return .karte(satz)
        }
        return .ergebnis(Mcpergebnis(text: unlesbar, fehler: true))
    }

    /// Das Ergebnis eines Entscheids (`{kennung, ok, text}`) als Antwort an Claude.
    public static func ergebnis(aus wert: JSONWert?) -> Mcpergebnis? {
        guard let text = wert?["text"]?.alsText else { return nil }
        return Mcpergebnis(text: text, fehler: wert?["ok"]?.alsWahrheit != true)
    }

    /// Der Satz an Claude fuer eine Karte, die nicht angewendet wurde und wegfaellt — mit Grund
    /// (abgelaufen, andere Mappe, passt nicht mehr zum Graph, nicht mehr in der Seite).
    public static func verworfen(_ grund: String) -> Mcpergebnis {
        Mcpergebnis(text: "VERWORFEN: \(grund) — der Vorschlag wurde nicht angewendet; nichts "
                    + "wurde geändert.", fehler: true)
    }
}

// ===================================================================== Karten und Ereignisse

/// Ein Vorschlag in der Assistent-Leiste (Entscheid 106a) — aus dem Ereignis «karte».
public struct Kikarte: Equatable, Sendable, Identifiable {
    public let kennung: String
    public let werkzeug: String
    public let art: Werkzeugart
    public let urheber: Kiurheber
    public let zusammenfassung: String
    /// Je Schritt die Zusammenfassung (bei einem Paket mehrere).
    public let schritte: [String]
    /// Der Vorschlag, wie die Seite ihn schickte — damit die App ihn einer neu geladenen
    /// Knotenansicht zurueckgeben kann (`Kartenablage`, `visboxKi.stelleWieder`).
    public let roh: JSONWert?

    public var id: String { kennung }

    public init(kennung: String, werkzeug: String, art: Werkzeugart, urheber: Kiurheber,
                zusammenfassung: String, schritte: [String] = [], roh: JSONWert? = nil) {
        self.kennung = kennung
        self.werkzeug = werkzeug
        self.art = art
        self.urheber = urheber
        self.zusammenfassung = zusammenfassung
        self.schritte = schritte
        self.roh = roh
    }

    /// Aus `vorschlag` des Ereignisses — `nil`, wenn etwas fehlt.
    public init?(_ v: JSONWert) {
        guard let kennung = v["kennung"]?.alsText, let werkzeug = v["werkzeug"]?.alsText,
              let art = v["art"]?.alsText.flatMap(Werkzeugart.init(rawValue:)),
              let zusammenfassung = v["zusammenfassung"]?.alsText else { return nil }
        let urheber = v["urheber"]?.alsText.flatMap(Kiurheber.init(rawValue:)) ?? .claude
        let schritte = (v["schritte"]?.alsListe ?? []).compactMap { $0["zusammenfassung"]?.alsText }
        self.init(kennung: kennung, werkzeug: werkzeug, art: art, urheber: urheber,
                  zusammenfassung: zusammenfassung, schritte: schritte, roh: v)
    }

    /// «VORSCHLAG VON CLAUDE · K-12» (Blatt 30, Feld 1).
    public var kopf: String {
        "Vorschlag \(urheber.vonWem) · \(kennung)"
    }

    /// Bei einer Render-Karte der Satz unter den Knoepfen (Entscheid 106b) — sonst `nil`.
    public var freigabeSatz: String? {
        art == .rendern ? Kikarte.rendernSatz : nil
    }

    public static let rendernSatz = "Rendern braucht danach deine Freigabe am Knoten."

    /// Die Zeilen unter der Zusammenfassung: die Schritte eines Pakets, sonst keine.
    public var zeilen: [String] {
        schritte.count > 1 ? schritte : []
    }
}

/// Ein KI-Schritt ohne Karte (Coop/Voll), der sich zuruecknehmen laesst (Entscheid 114).
public struct Kischritt: Equatable, Sendable {
    public let kennung: String
    public let urheber: Kiurheber
    public let zusammenfassung: String

    public init(kennung: String, urheber: Kiurheber, zusammenfassung: String) {
        self.kennung = kennung
        self.urheber = urheber
        self.zusammenfassung = zusammenfassung
    }

    init?(_ w: JSONWert?) {
        guard let w, let kennung = w["kennung"]?.alsText,
              let zusammenfassung = w["zusammenfassung"]?.alsText else { return nil }
        self.init(kennung: kennung,
                  urheber: w["urheber"]?.alsText.flatMap(Kiurheber.init(rawValue:)) ?? .claude,
                  zusammenfassung: zusammenfassung)
    }
}

/// Was die Knotenansicht meldet (`webkit.messageHandlers.visboxKi`).
public enum Kiereignis: Equatable, Sendable {
    case beginn(kennung: String, werkzeug: String, urheber: Kiurheber)
    case ende(kennung: String, werkzeug: String, urheber: Kiurheber, ok: Bool, text: String)
    case karte(Kikarte)
    case entschieden(kennung: String, angewendet: Bool, ergebnis: Mcpergebnis)
    /// Je Urheber der letzte stehende KI-Schritt ohne Karte.
    case kiverlauf(claude: Kischritt?, assistent: Kischritt?)
    /// Die Schnittstelle steht (nach dem Laden der Mappe).
    case bereit(werkzeuge: Int)
    /// Die Seite geht (neu laden, andere Seite).
    case weg(grund: String)

    /// Aus der Nachricht der Seite — `nil`, wenn sie keine bekannte Form hat.
    public init?(_ n: JSONWert) {
        switch n["art"]?.alsText {
        case "taetigkeit":
            guard let kennung = n["kennung"]?.alsText, let werkzeug = n["werkzeug"]?.alsText
            else { return nil }
            let urheber = n["urheber"]?.alsText.flatMap(Kiurheber.init(rawValue:)) ?? .claude
            switch n["phase"]?.alsText {
            case "beginn":
                self = .beginn(kennung: kennung, werkzeug: werkzeug, urheber: urheber)
            case "ende":
                self = .ende(kennung: kennung, werkzeug: werkzeug, urheber: urheber,
                             ok: n["ok"]?.alsWahrheit == true, text: n["text"]?.alsText ?? "")
            default:
                return nil
            }
        case "karte":
            guard let v = n["vorschlag"], let karte = Kikarte(v) else { return nil }
            self = .karte(karte)
        case "entschieden":
            guard let kennung = n["kennung"]?.alsText,
                  let ergebnis = Kibruecke.ergebnis(aus: n["ergebnis"]) else { return nil }
            self = .entschieden(kennung: kennung, angewendet: n["angewendet"]?.alsWahrheit == true,
                                ergebnis: ergebnis)
        case "kiverlauf":
            self = .kiverlauf(claude: Kischritt(n["letzter"]?["claude"]),
                              assistent: Kischritt(n["letzter"]?["assistent"]))
        case "bereit":
            self = .bereit(werkzeuge: n["werkzeuge"]?.alsGanz ?? 0)
        case "weg":
            self = .weg(grund: n["grund"]?.alsText ?? "Die Knotenansicht wurde geschlossen")
        default:
            return nil
        }
    }
}

/// Eine laufende Taetigkeit der KI — fuer den Strom «● Claude legt … an».
public struct Kitaetigkeit: Equatable, Sendable {
    public let kennung: String
    public let werkzeug: String
    public let urheber: Kiurheber
    /// Wann sie endete — `nil`: laeuft noch.
    public var ende: Date?

    /// Der Satz im Strom, ohne den Punkt davor.
    public var satz: String {
        "\(urheber.name) \(Kiworte.tut(werkzeug)) …"
    }
}

/// Wie ein Werkzeug im Taetigkeitsstrom heisst — einfache Worte statt Werkzeugnamen.
public enum Kiworte {
    public static func tut(_ werkzeug: String) -> String {
        switch werkzeug {
        case "graph_lesen": return "liest den Knotengraph"
        case "vis_graphErstellen": return "legt einen Render-Graph an"
        case "vis_nodeSetzen": return "legt einen Knoten an"
        case "vis_nodeParametrieren": return "stellt einen Knoten ein"
        case "vis_nodeSchieben": return "schiebt einen Knoten"
        case "vis_verbinden": return "verbindet zwei Knoten"
        case "vis_trennen": return "trennt eine Verbindung"
        case "vis_nodeKollabieren": return "klappt einen Knoten ein oder auf"
        case "vis_nodeLoeschen": return "schlägt vor, einen Knoten zu löschen"
        case "vis_graphLoeschen": return "schlägt vor, einen Render-Graph zu löschen"
        case "vis_render": return "bestellt ein Bild"
        case "vis_varianten": return "bestellt Varianten"
        case "vis_paket": return "arbeitet an mehreren Knoten"
        case Macwerkzeuge.mappeLesenName: return "liest die Mappe"
        case Macwerkzeuge.skizzenLesenName: return "sieht die Skizzen an"
        case Macwerkzeuge.laufAbbrechenName: return "bricht einen Lauf ab"
        case Macwerkzeuge.bildAnsehenName: return "sieht ein Bild an"
        case Kibedienen.blickName: return "schaut in die Knotenansicht"
        case Kibedienen.mausName: return "bedient die Knotenansicht"
        default: return "arbeitet"
        }
    }
}

/// Was die KI-Teile der Assistent-Leiste zeigen (Blatt 30, Feld 1) — ein Wert, den die Ereignisse
/// der Knotenansicht fortschreiben.
public struct Kileistenstand: Equatable, Sendable {
    /// Die offenen Karten, aelteste zuerst.
    public private(set) var karten: [Kikarte] = []
    /// Was gerade laeuft oder eben endete (fuer den kurzen Nachlauf).
    public private(set) var taetigkeiten: [Kitaetigkeit] = []
    /// Je Urheber der letzte KI-Schritt ohne Karte, den man zuruecknehmen kann.
    public private(set) var letzterSchritt: [Kiurheber: Kischritt] = [:]
    /// Ob die Knotenansicht ihre Schnittstelle angemeldet hat.
    public private(set) var knotenBereit = false

    /// So lange bleibt eine beendete Taetigkeit im Strom stehen — sonst saehe man ein Lesen nie.
    public static let nachlauf: TimeInterval = 3
    /// Hoechstens so viele Eintraege merkt sich der Strom.
    public static let hoechstens = 8

    public init() {}

    /// Ein Ereignis einarbeiten. `jetzt` fuer die Proben.
    public mutating func nimm(_ e: Kiereignis, jetzt: Date = Date()) {
        switch e {
        case .beginn(let kennung, let werkzeug, let urheber):
            taetigkeiten.removeAll { $0.kennung == kennung }
            taetigkeiten.append(Kitaetigkeit(kennung: kennung, werkzeug: werkzeug, urheber: urheber))
            if taetigkeiten.count > Kileistenstand.hoechstens {
                taetigkeiten.removeFirst(taetigkeiten.count - Kileistenstand.hoechstens)
            }
        case .ende(let kennung, _, _, _, _):
            if let i = taetigkeiten.firstIndex(where: { $0.kennung == kennung }) {
                taetigkeiten[i].ende = jetzt
            }
        case .karte(let karte):
            // EINE KARTE IST KEINE ARBEIT MEHR (108 C): Sie wartet auf den Architekten und steht
            // als Karte da, nicht im Strom.
            taetigkeiten.removeAll { $0.kennung == karte.kennung }
            // ZURUECKGEGEBEN (die Seite lud neu): an ihrem Platz, nicht hinten angehaengt.
            if let i = karten.firstIndex(where: { $0.kennung == karte.kennung }) {
                karten[i] = karte
            } else {
                karten.append(karte)
            }
        case .entschieden(let kennung, _, _):
            karten.removeAll { $0.kennung == kennung }
        case .kiverlauf(let claude, let assistent):
            letzterSchritt[.claude] = claude
            letzterSchritt[.assistent] = assistent
        case .bereit:
            knotenBereit = true
        case .weg:
            // DIE KARTEN BLEIBEN (Strang Karten, 21.10.2026): Sie gelten pro Mappe, nicht pro
            // Ansicht — die App gibt sie der neu geladenen Seite zurueck (`Kartenablage`). Was
            // wegfaellt, ist die laufende Arbeit und der KI-Verlauf der Seite (Entscheid 114).
            knotenBereit = false
            taetigkeiten = []
            letzterSchritt = [:]
        }
    }

    /// Eine Karte, deren Entscheid nicht ankam (die Knotenansicht kannte sie nicht mehr), faellt weg.
    public mutating func entferne(_ kennung: String) {
        karten.removeAll { $0.kennung == kennung }
    }

    /// Der Taetigkeitsstrom — **nur, solange die KI arbeitet** (Entscheid 108 C), dazu ein kurzer
    /// Nachlauf. Leer: Der Strom ist nicht zu sehen.
    public func strom(jetzt: Date = Date()) -> [String] {
        taetigkeiten.filter { t in
            guard let ende = t.ende else { return true }
            return jetzt.timeIntervalSince(ende) < Kileistenstand.nachlauf
        }.map(\.satz)
    }

    /// Der Knopf «Claudes letzten Schritt zurücknehmen» (Entscheid 114) — nur, wenn es einen gibt.
    public var claudeZuruecknehmen: Kischritt? { letzterSchritt[.claude] }

    public static let zuruecknehmenKnopf = "Claudes letzten Schritt zurücknehmen"
}

// ===================================================================== die zwei Zeilen oben

/// Wie der Hoerer fuer Claude steht — die Mac-App uebersetzt ihren Zustand hierher.
public enum Claudehoererlage: Equatable, Sendable {
    case aus
    case startet
    case bereit
    case gestoert(String)
}

/// Die Zeile «Claude verbunden · über MCP, nur dieser Mac» (Blatt 30, Feld 1).
public enum Claudezeile {
    /// So lange gilt Claude als verbunden, nachdem es zuletzt etwas geschickt hat. Claude Code
    /// fragt nicht von sich aus nach; ein Werkzeugaufruf oder `ping` erneuert die Zeit.
    public static let frische: TimeInterval = 10 * 60

    public static let ueberMcp = "· über MCP, nur dieser Mac"

    /// Titel und Zusatz. **«verbunden» nur, wenn eine Gegenstelle kürzlich gesprochen hat** —
    /// ein lauschender Anschluss ist noch keine Verbindung.
    public static func zeile(lage: Claudehoererlage, letzterKontakt: Date?,
                             jetzt: Date = Date()) -> (titel: String, zusatz: String) {
        switch lage {
        case .aus:
            return ("Claude: aus", "· im Einrichten einschalten")
        case .startet:
            return ("Claude: startet", "")
        case .gestoert(let satz):
            return ("Claude: nicht bereit", "· \(satz)")
        case .bereit:
            if let k = letzterKontakt, jetzt.timeIntervalSince(k) < frische {
                return ("Claude verbunden", ueberMcp)
            }
            return ("Claude: bereit", "· wartet auf Claude Code oder Claude Desktop")
        }
    }
}

/// Die Zeile «Assistent: qwen3:14b am Heim-PC · bereit».
public enum Assistentenkopf {
    public static func satz(_ zeile: Assistentenzeile?, heimEingerichtet: Bool) -> String {
        guard heimEingerichtet else { return "Assistent: braucht den Heim-PC" }
        guard let zeile else { return "Assistent: wird am Heim-PC nachgesehen …" }
        let modell = zeile.modell.map { "\($0) am Heim-PC" } ?? "am Heim-PC"
        return "Assistent: \(modell) · \(zeile.stand.map(wort) ?? "unbekannt")"
    }

    private static func wort(_ s: Assistentenstand) -> String {
        switch s {
        case .bereit: return "bereit"
        case .laedt: return "wartet, ein Bild rechnet"
        case .fehlt: return "Modell fehlt"
        case .aus: return "aus"
        }
    }
}

// ===================================================================== Selbstaendigkeit merken

extension Selbstaendigkeit {
    /// Der Schluessel in den Einstellungen des Mac (Entscheid 108 A: oben in der Leiste).
    public static let einstellung = "ki.selbstaendigkeit"

    /// Aus dem gemerkten Wort — fehlt es oder ist es unbekannt, gilt die Vorgabe «Karte».
    public init(gemerkt: String?) {
        self = gemerkt.flatMap(Selbstaendigkeit.init(rawValue:)) ?? .vorgabe
    }
}

// ===================================================================== die Werkzeuge der Mac-App

/// Die Werkzeuge, die die Mac-App selbst ausfuehrt (Stufe 4, soweit ohne Mappe am Mac): Sie lesen
/// ueber die bestehenden Heim-Wege oder halten einen Lauf an. **Keines gibt die Grafikkarte frei.**
public enum Macwerkzeuge {
    public static let mappeLesenName = "mappe_lesen"
    public static let skizzenLesenName = "skizzen_lesen"
    public static let laufAbbrechenName = "lauf_abbrechen"
    public static let bildAnsehenName = "bild_ansehen"

    /// Hoechstens so gross darf ein Bild an Claude sein (vor Base64). Die Claude-API nimmt bis
    /// 5 MB je Bild nach Base64; 3,75 MB roh sind 5 MB kodiert.
    public static let bildHoechstens = 3_750_000

    static func schema(_ felder: [String: JSONWert], pflicht: [String] = []) -> JSONWert {
        var s: [String: JSONWert] = [
            "type": .text("object"), "properties": .objekt(felder),
            "additionalProperties": .wahrheit(false),
        ]
        if !pflicht.isEmpty { s["required"] = .liste(pflicht.map { .text($0) }) }
        return .objekt(s)
    }

    static func feld(_ typ: String, _ beschreibung: String) -> JSONWert {
        .objekt(["type": .text(typ), "description": .text(beschreibung)])
    }

    public static let mappeLesen = Mcpwerkzeug(
        name: mappeLesenName,
        beschreibung: "Liest die Mappe, die die Knotenansicht zeigt: Name, Modell (ob geladen, "
            + "Herkunft, Fassung, Bauteile), die Skizzen vom iPad und die vorgeschlagenen "
            + "Standpunkte. Ändert nichts.",
        art: .lesen)

    public static let skizzenLesen = Mcpwerkzeug(
        name: skizzenLesenName,
        beschreibung: "Ohne name: die Skizzen der Mappe, die neueste zuerst (Name, Titel, Stand, "
            + "Bemerkung). Mit name: das Bild dieser Skizze zum Ansehen. Ändert nichts.",
        eingabe: schema(["name": feld("string", "Der Name aus der Liste, z. B. «skizze-3.png».")]),
        art: .lesen)

    public static let laufAbbrechen = Mcpwerkzeug(
        name: laufAbbrechenName,
        beschreibung: "Bricht einen Render-Lauf ab (jobId aus graph_lesen, Feld lauf.jobId) und "
            + "gibt die Grafikkarte frei. Sofort, ohne Karte: Abbrechen ändert kein Dokument, und "
            + "neu bestellen geht jederzeit. Ein fertiger Lauf bleibt, was er ist. Kann nichts "
            + "freigeben oder starten.",
        eingabe: schema(["jobId": feld("string", "Die Kennung des Laufs.")], pflicht: ["jobId"]),
        art: .anhalten)

    public static let bildAnsehen = Mcpwerkzeug(
        name: bildAnsehenName,
        beschreibung: "Zeigt Claude das Bild eines fertigen Laufs (jobId aus graph_lesen). "
            + "bild: welches, ab 0 (bei Varianten je Kamera eines); ohne: das erste. Ändert "
            + "nichts.",
        eingabe: schema(["jobId": feld("string", "Die Kennung des Laufs."),
                         "bild": feld("integer", "Welches Bild, ab 0.")],
                        pflicht: ["jobId"]),
        art: .lesen)

    public static let alle = [mappeLesen, skizzenLesen, laufAbbrechen, bildAnsehen]

    public static func ist(_ name: String) -> Bool {
        alle.contains { $0.name == name }
    }

    /// Eine Kennung, die in einen Pfad darf: 1–128 Zeichen aus Buchstaben, Ziffern, `_`, `-`, `.`
    /// — ohne `..`. Alles andere fuehrte aus dem Weg der Bruecke hinaus.
    public static func gueltigeKennung(_ k: String) -> Bool {
        guard (1...128).contains(k.count), !k.contains(".."), !k.hasPrefix(".") else { return false }
        return k.unicodeScalars.allSatisfy {
            ("a"..."z").contains($0) || ("A"..."Z").contains($0) || ("0"..."9").contains($0)
                || $0 == "_" || $0 == "-" || $0 == "."
        }
    }

    // ------------------------------------------------------------- die Wege zum Heim-PC

    /// Ein Weg zum Heim-PC: Methode, Pfad (wie in der Seite) und die schon kodierte Frage.
    public struct Heimweg: Equatable, Sendable {
        public let methode: String
        public let pfad: String
        public let frage: String?

        public init(methode: String, pfad: String, frage: String?) {
            self.methode = methode
            self.pfad = pfad
            self.frage = frage
        }
    }

    public static let mappeWeg = Heimweg(methode: "GET", pfad: "/knoten/mappe", frage: nil)

    /// Fund A (Mac-Demolauf 0.3.34, 22.10.2026; Entscheid 129): die Mappe des Heim-PC, die DIESER
    /// Mac in der Knotenansicht offen hat (`?mappe=`) — nicht die, die irgendein Geraet zuletzt
    /// geoeffnet hat. Ohne gueltigen Namen wie bisher.
    public static func mappeWeg(mappe: String?) -> Heimweg {
        guard let frage = mappenfrage(mappe, dazu: []) else { return mappeWeg }
        return Heimweg(methode: "GET", pfad: "/knoten/mappe", frage: frage)
    }

    public static func skizzeWeg(_ name: String) -> Heimweg {
        skizzeWeg(name, mappe: nil)
    }

    public static func skizzeWeg(_ name: String, mappe: String?) -> Heimweg {
        let nameTeil = URLQueryItem(name: "name", value: name)
        if let frage = mappenfrage(mappe, dazu: [nameTeil]) {
            return Heimweg(methode: "GET", pfad: "/knoten/skizze", frage: frage)
        }
        var teile = URLComponents()
        teile.queryItems = [nameTeil]
        return Heimweg(methode: "GET", pfad: "/knoten/skizze", frage: teile.percentEncodedQuery)
    }

    private static func mappenfrage(_ mappe: String?, dazu: [URLQueryItem]) -> String? {
        guard let mappe, Knotenmappenwahl.gueltig(mappe) else { return nil }
        var teile = URLComponents()
        teile.queryItems = dazu + [URLQueryItem(name: "mappe", value: mappe)]
        return teile.percentEncodedQuery
    }

    /// Wo `mappe_lesen` und `skizzen_lesen` lesen (Fund A): **in derselben Mappe wie die
    /// Knotenansicht** — die Mappe am Mac, wenn eine offen ist, sonst die Mappe des Heim-PC, die
    /// dieser Mac zuletzt gelesen hat.
    public enum Lesequelle: Equatable, Sendable {
        case macMappe
        case heimPC(mappe: String?)
    }

    public static func lesequelle(macMappeOffen: Bool, gemerkteHeimMappe: String?) -> Lesequelle {
        macMappeOffen ? .macMappe : .heimPC(mappe: gemerkteHeimMappe)
    }

    /// Ein Name, den `skizzen_lesen` in einer Mappe am Mac annimmt: der Weg aus der Liste
    /// (`ipad/skizze-….png` oder ein geholter Name), sicher in der Mappe — `nil` sonst.
    public static func skizzenwegAmMac(_ name: String) -> String? {
        guard !name.isEmpty, name.count <= 200, !name.contains("..") else { return nil }
        return Mappenkern.skizzenweg(name)
    }

    public static func laufWeg(_ jobId: String) -> Heimweg {
        Heimweg(methode: "GET", pfad: "/bruecke/jobs/\(jobId)", frage: nil)
    }

    public static func abbrechenWeg(_ jobId: String) -> Heimweg {
        Heimweg(methode: "POST", pfad: "/bruecke/jobs/\(jobId)/cancel", frage: nil)
    }

    public static func artefaktWeg(_ jobId: String, _ name: String) -> Heimweg? {
        guard gueltigeKennung(name),
              let kodiert = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed)
        else { return nil }
        return Heimweg(methode: "GET", pfad: "/bruecke/jobs/\(jobId)/artifacts/\(kodiert)", frage: nil)
    }

    // ------------------------------------------------------------- die Antworten

    /// Der Satz einer Fehlerantwort des Heim-PC (`{"fehler": satz}`), sonst der Status.
    public static func fehlersatz(status: Int, daten: Data) -> String {
        if let w = try? JSONWert.lies(daten), let satz = w["fehler"]?.alsText { return satz }
        return "Der Heim-PC antwortete mit \(status)."
    }

    /// `mappe_lesen`: ein Satz vorne, dann die Antwort als JSON (ohne Plattenpfade — die nimmt
    /// schon der Server heraus).
    public static func mappeErgebnis(status: Int, daten: Data) -> Mcpergebnis {
        guard status == 200, let w = try? JSONWert.lies(daten) else {
            return Mcpergebnis(text: fehlersatz(status: status, daten: daten), fehler: true)
        }
        let name = w["name"]?.alsText ?? w["mappe"]?.alsText ?? "ohne Namen"
        let skizzen = w["skizzen"]?.alsListe?.count ?? 0
        let modell = w["glb"]?.alsWahrheit == true
            ? "Modell geladen" + (w["bauteile"]?.alsGanz.map { " (\($0) Bauteile)" } ?? "")
            : "noch kein Modell"
        let grund = w["grund"]?.alsText.flatMap { $0.isEmpty ? nil : " \($0)" } ?? ""
        let json = (try? w.daten()).flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
        return Mcpergebnis(text: "Mappe «\(name)»: \(modell), \(skizzen) Skizze(n).\(grund)\n\(json)")
    }

    /// `skizzen_lesen` ohne Namen: die Liste aus der Mappe.
    public static func skizzenErgebnis(status: Int, daten: Data) -> Mcpergebnis {
        guard status == 200, let w = try? JSONWert.lies(daten) else {
            return Mcpergebnis(text: fehlersatz(status: status, daten: daten), fehler: true)
        }
        let liste = w["skizzen"]?.alsListe ?? []
        if liste.isEmpty {
            return Mcpergebnis(text: "Die Mappe hat keine Skizzen vom iPad.")
        }
        let json = (try? JSONWert.liste(liste).daten()).flatMap { String(data: $0, encoding: .utf8) } ?? "[]"
        return Mcpergebnis(text: "\(liste.count) Skizze(n), die neueste zuerst. Ansehen mit "
                           + "\(skizzenLesenName) und name.\n\(json)")
    }

    /// Ein Bild als Antwort (Entscheid 106f: Bilder an Claude erlaubt) — zu gross oder ohne
    /// bekannte Art wird es nicht geschickt, mit Satz.
    public static func bildErgebnis(status: Int, daten: Data, typ: String?, was: String) -> Mcpergebnis {
        guard status == 200 else {
            return Mcpergebnis(text: fehlersatz(status: status, daten: daten), fehler: true)
        }
        guard let art = bildart(typ: typ, daten: daten) else {
            return Mcpergebnis(text: "\(was) ist kein Bild, das Claude lesen kann.", fehler: true)
        }
        guard daten.count <= bildHoechstens else {
            return Mcpergebnis(text: "\(was) ist zu gross für Claude (\(daten.count / 1_000_000) MB; "
                               + "höchstens \(bildHoechstens / 1_000_000) MB).", fehler: true)
        }
        return Mcpergebnis(text: "\(was):", bild: (daten: daten.base64EncodedString(), art: art))
    }

    /// Die Art eines Bilds — aus dem Kopf der Antwort, sonst aus den ersten Bytes.
    public static func bildart(typ: String?, daten: Data) -> String? {
        let kopf = (typ ?? "").lowercased().split(separator: ";").first.map(String.init)?
            .trimmingCharacters(in: .whitespaces) ?? ""
        if ["image/png", "image/jpeg", "image/webp", "image/gif"].contains(kopf) { return kopf }
        let b = [UInt8](daten.prefix(12))
        if b.starts(with: [0x89, 0x50, 0x4E, 0x47]) { return "image/png" }
        if b.starts(with: [0xFF, 0xD8, 0xFF]) { return "image/jpeg" }
        if b.count >= 12, Array(b[0...3]) == [0x52, 0x49, 0x46, 0x46],
           Array(b[8...11]) == [0x57, 0x45, 0x42, 0x50] {
            return "image/webp"
        }
        return nil
    }

    /// Was der Laufzettel ueber ein Bild sagt: sein Name — oder warum es keines gibt.
    public enum Bildwahl: Equatable, Sendable {
        case name(String)
        case keines(Mcpergebnis)
    }

    /// Aus dem Laufzettel (`GET /bruecke/jobs/{id}`) der Name des Bilds `nummer`.
    public static func bildname(laufzettel daten: Data, status: Int, jobId: String,
                                nummer: Int) -> Bildwahl {
        guard status == 200, let w = try? JSONWert.lies(daten) else {
            return .keines(Mcpergebnis(text: fehlersatz(status: status, daten: daten), fehler: true))
        }
        let bilder = (w["result"]?["images"]?.alsListe ?? []).compactMap(\.alsText)
        guard !bilder.isEmpty else {
            let stand = w["status"]?.alsText ?? "unbekannt"
            return .keines(Mcpergebnis(text: "Der Lauf \(jobId) hat (noch) kein Bild — Stand: "
                                       + "\(stand).", fehler: true))
        }
        guard (0..<bilder.count).contains(nummer) else {
            return .keines(Mcpergebnis(text: "Der Lauf \(jobId) hat \(bilder.count) Bild(er); "
                                       + "bild ist 0 bis \(bilder.count - 1).", fehler: true))
        }
        return .name(bilder[nummer])
    }

    /// `lauf_abbrechen`: der Laufzettel danach als Satz.
    public static func abbrechenErgebnis(status: Int, daten: Data, jobId: String) -> Mcpergebnis {
        guard status == 200, let w = try? JSONWert.lies(daten) else {
            return Mcpergebnis(text: fehlersatz(status: status, daten: daten), fehler: true)
        }
        switch w["status"]?.alsText {
        case "cancelled":
            return Mcpergebnis(text: "Lauf \(jobId) abgebrochen — die Grafikkarte ist frei.")
        case let s?:
            return Mcpergebnis(text: "Lauf \(jobId) war schon beendet (\(s)); nichts geändert.")
        case nil:
            return Mcpergebnis(text: "Lauf \(jobId): Der Heim-PC nannte keinen Stand.", fehler: true)
        }
    }

    /// Ohne Heim-PC: jedes Mac-Werkzeug antwortet so.
    public static let ohneHeim = Mcpergebnis(text: Knotenwege.satzOhneHeim + " Nichts wurde ausgeführt.",
                                             fehler: true)

    public static func ungueltig(_ feld: String) -> Mcpergebnis {
        Mcpergebnis(text: "«\(feld)» fehlt oder ist keine gültige Kennung — nichts wurde ausgeführt.",
                    fehler: true)
    }
}

// ===================================================================== Blick und Maus (Stufe 6)

/// `visbox_blick` und `visbox_maus` (Plan KI-Bedienung Stufe 6, 21.10.2026; Vorlage `kosmo_blick`,
/// `kosmo_maus` von KosmoOrbit, woertlich in der Seite: `state/kosmo-maus.ts`). Die Liste mit
/// ihren Schemas kommt aus der Seite (`visboxKi.blickMausWerkzeuge`, im Bau `ki-werkzeugliste.json`);
/// hier steht, wie die App sie ruft und ihre Antwort liest.
///
/// **Die Maus ist nie selbst eine Karte** (`Werkzeugart.bedienen`): Was ein Klick am Graph aendert,
/// haelt die Wache der Seite an und legt es durch den Werkzeugsatz — Karte, Coop oder Voll; Loeschen
/// und Rendern immer Karte. Die Sperrzonen (Freigeben, Bestell-Knoepfe, Loeschen, Karten, Schalter,
/// Kennwoerter, Rueckgaengig) stehen in der Seite. **Kein Weg hier gibt die Grafikkarte frei.**
public enum Kibedienen {
    public static let blickName = Mcp.servername + "_blick"
    public static let mausName = Mcp.servername + "_maus"

    public static func ist(_ name: String) -> Bool {
        name == blickName || name == mausName
    }

    /// Der Rumpf fuer die Seite: `blick(urheber, JSON.parse(argumente))` bzw. `maus(…)`.
    public static func rumpf(_ name: String) -> String? {
        switch name {
        case blickName: return Kibruecke.rumpfWartend("blick(urheber, JSON.parse(argumente))")
        case mausName: return Kibruecke.rumpfWartend("maus(urheber, JSON.parse(argumente))")
        default: return nil
        }
    }

    /// Die Antwort der Seite (`{ok, text, bild?: {data, mimeType}}`) als Ergebnis. Ein Bild nur in
    /// einer Art, die Claude liest, und nur bis `Macwerkzeuge.bildHoechstens` (roh) — sonst der Text
    /// allein mit einem Satz.
    public static func ergebnis(aus wert: JSONWert) -> Mcpergebnis {
        guard let text = wert["text"]?.alsText else {
            return Mcpergebnis(text: Kibruecke.unlesbar, fehler: true)
        }
        let fehler = wert["ok"]?.alsWahrheit != true
        guard let daten = wert["bild"]?["data"]?.alsText, let art = wert["bild"]?["mimeType"]?.alsText else {
            return Mcpergebnis(text: text, fehler: fehler)
        }
        guard ["image/png", "image/jpeg", "image/webp"].contains(art) else {
            return Mcpergebnis(text: text + "\nBILD: nicht mitgeschickt (keine Art, die Claude liest).", fehler: fehler)
        }
        guard daten.utf8.count / 4 * 3 <= Macwerkzeuge.bildHoechstens else {
            return Mcpergebnis(text: text + "\nBILD: nicht mitgeschickt (zu gross).", fehler: fehler)
        }
        return Mcpergebnis(text: text, bild: (daten: daten, art: art), fehler: fehler)
    }
}

// ===================================================================== der Assistent mit Werkzeugen (Stufe 5)

/// Was ein Werkzeugschritt des Assistenten als Ergebnis an sein Modell zurueckgibt (Plan
/// KI-Bedienung Stufe 5, 21.10.2026). Der Assistent wartet nie auf einen Entscheid: Eine Karte
/// liegt dann beim Architekten («Vorschlag des Assistenten · A-n»), und das Modell hoert genau das.
/// Ein Bild kann sein Modell nicht lesen — es bekommt den Text und einen Satz.
public enum Assistentenschrittergebnis {
    /// Die Kennungen der Aufrufe des Assistenten: «A-1», «A-2», … (Claudes heissen «K-n»).
    public static let kennungVorsatz = "A-"

    public static func text(_ antwort: Traegerantwort, kennung: String) -> (text: String, ok: Bool) {
        switch antwort {
        case .karte(let satz):
            return ("VORSCHLAG \(kennung) liegt als Karte beim Architekten: \(satz). Er entscheidet; "
                    + "schlage dasselbe nicht noch einmal vor.", true)
        case .ergebnis(let e):
            let bild = e.bild == nil ? "" : "\n(Ein Bild dazu sieht nur Claude.)"
            return (e.text + bild, !e.fehler)
        }
    }
}

// ===================================================================== Claude Desktop

/// «Visbox hinzufügen» fuer Claude Desktop (Blatt 30, Feld 3): ein Eintrag in dessen
/// Einstellungsdatei (`claude_desktop_config.json`), der die App mit `--mcp-stdio` startet.
public enum Claudedesktop {
    /// Der Ort der Datei, relativ zum Ordner «Application Support» des Benutzers.
    public static let datei = "Claude/claude_desktop_config.json"

    /// Der Eintrag fuer `mcpServers.visbox`.
    public static func eintrag(programm: String) -> JSONWert {
        .objekt(["command": .text(programm), "args": .liste([.text("--mcp-stdio")])])
    }

    public enum Fehler: Error, Equatable {
        /// Die vorhandene Datei ist kein JSON-Objekt — sie wird NICHT ueberschrieben.
        case unlesbar
    }

    /// Die neue Datei: die vorhandene, mit dem Eintrag `visbox` unter `mcpServers` — **alles
    /// andere bleibt**, wie es war. Ohne Datei entsteht eine mit nur diesem Eintrag.
    public static func mische(vorhanden: Data?, programm: String) throws -> Data {
        var wurzel: [String: JSONWert] = [:]
        if let vorhanden, !vorhanden.isEmpty {
            guard let w = try? JSONWert.lies(vorhanden), let o = w.alsObjekt else {
                throw Fehler.unlesbar
            }
            wurzel = o
        }
        var server = wurzel["mcpServers"]?.alsObjekt ?? [:]
        server[Mcp.servername] = eintrag(programm: programm)
        wurzel["mcpServers"] = .objekt(server)
        return try JSONWert.objekt(wurzel).daten()
    }

    /// Ob die Datei den Eintrag schon so traegt.
    public static func traegt(_ daten: Data?, programm: String) -> Bool {
        guard let daten, let w = try? JSONWert.lies(daten) else { return false }
        return w["mcpServers"]?[Mcp.servername] == eintrag(programm: programm)
    }

    /// Der Satz im Einrichten.
    public static func satz(programm: String) -> String {
        "Claude Desktop: «\(Marke.name) hinzufügen» schreibt den Eintrag (startet \(programm) "
            + "--mcp-stdio). Danach Claude Desktop neu starten."
    }
}

// ===================================================================== Einrichten › Claude über MCP

/// Die Saetze des Abschnitts «Claude über MCP» (Blatt 30, Feld 3) — woertlich wie gezeichnet.
public enum Claudeeinrichtung {
    public static let titel = "Claude über MCP"
    public static let codeTitel = "Claude Code — einmal im Terminal:"
    public static let befehl = "claude mcp add --transport http \(Mcp.servername) \(Mcp.adresse)"
    public static let kopieren = "Befehl kopieren"
    public static let datenTitel = "Was Claude bekommt:"
    public static let daten = "Mappennamen, Prompts, den Knotengraph und Bilder, die Claude ansehen "
        + "will. Das geht an Anthropic."
    public static let werkzeugeTitel = "Werkzeuge:"
    public static let werkzeuge = "Knoten setzen, verbinden, einstellen, löschen (über Karte), "
        + "Grundlage und Varianten bestellen, Mappe und Skizzen lesen, Bild ansehen, Lauf abbrechen, "
        + "die Knotenansicht ansehen und mit eigener Maus bedienen (nie «Freigeben», Bestellen "
        + "oder Löschen)."
    public static let nurHier = "Nur auf diesem Mac. Kein Weg aus dem Internet."
}
