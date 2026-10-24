import Foundation

// DER MCP-KERN — Claude bedient Visbox (Plan `docs/PLAN_KI_BEDIENUNG_2026-10-20.md`, Stufe 2;
// Entscheide 105–106f und 108).
//
// MCP («Model Context Protocol») ist der offene Standard, ueber den Claude die Werkzeuge eines
// anderen Programms benutzt. Gesprochen wird JSON-RPC 2.0: Claude schickt eine Nachricht mit
// `method` (und `id`, wenn es eine Antwort erwartet), der Kern antwortet mit `result` oder
// `error`. Hier steht NUR die Logik, ohne Netz — darum unter Linux pruefbar (Regel 4). Das Netz
// (`Mcpleitung.swift` fuer die Bytes, `VisboxMac/Claude/` fuer den Hoerer) reicht nur durch.
//
// VORLAGE: der Kern von KosmoOrbit (`tools/kosmo-mcp/src/kern.mjs`,
// `src-tauri/kosmo-mcp-kern/src/kern.rs`) — dieselben Methoden, dieselbe Wartegrenze von 45 s,
// dieselbe Spielregel. Anders als dort:
//
//  * KEIN ZWEITER PROZESS FUER DIE APP. In KosmoOrbit meldet sich die Oberflaeche ueber einen
//    Ereignisstrom beim Kern an. Hier liegt der Kern IN der App; was die Werkzeuge tun, sagt
//    ein `Werkzeugtraeger` (ein Protokoll, async). Seit Stufe 3 in der App die Knotenansicht und
//    die Mac-App selbst (`Knotentraeger`); ohne laufende App (stdio) der Platzhalter.
//  * KEINE MELDUNG «LISTE GEAENDERT». Die Werkzeugliste der Mac-App steht fest, solange sie
//    laeuft; darum `listChanged: false` und kein Ereignisstrom (siehe `Mcpleitung`).
//  * DIE KENNUNG HEISST «K-n» (Karte), nicht «c-n» — sie steht so auf der Karte in der
//    Assistent-Leiste (Entscheid 106a), und Claude nennt sie so.
//
// Was hier NIE geschieht: Der Kern fuehrt nichts selbst aus. Er reicht weiter und wartet.

// ===================================================================== Festwerte

/// Die festen Angaben des Anschlusses.
public enum Mcp {
    /// Die MCP-Fassungen, die der Kern spricht — die erste ist sein Vorschlag, wenn Claude eine
    /// unbekannte wuenscht. Dieselbe Liste wie KosmoOrbit (`MCP_PROTOKOLLE`).
    public static let protokolle = ["2025-06-18", "2025-03-26", "2024-11-05"]
    /// Der Anschluss auf diesem Rechner. KosmoOrbit hat 8630; beide duerfen zugleich laufen.
    public static let anschluss = 8631
    /// Der eine Pfad (MCP «Streamable HTTP»).
    public static let pfad = "/mcp"
    /// So heisst der Server bei Claude (`claude mcp add … visbox …`).
    public static let servername = Marke.name.lowercased()
    /// **So lange wartet ein Aufruf auf das Ergebnis oder den Entscheid an der Karte**, bevor er
    /// «wartet noch» zurueckgibt. Unter der ueblichen 60-s-Grenze der MCP-Programme — wie
    /// KosmoOrbit (`STANDARD_WARTEN_MS`).
    public static let wartefrist: TimeInterval = 45
    /// Wie viele erledigte Aufrufe der Kern sich merkt (fuer `visbox_vorschlag_status`).
    public static let gedaechtnis = 200

    /// **Die Spielregel**, die Claude beim Handschlag bekommt (`instructions`). Sie sagt, was
    /// die Entscheide 106b und 106c festlegen — und was Claude tun soll, wenn es wartet.
    public static let anleitung =
        "\(Marke.name) ist ein Bildwerkzeug für Architektur: In der Knotenansicht werden Bilder aus "
        + "Modell, Skizze und Stimmung bestellt, verglichen und in der Mappe abgelegt. "
        + "Rufe zuerst \(Mcpkern.statusName) auf: Es nennt die offene Mappe, die Werkzeuge und den Modus "
        + "(Karte, Coop oder Voll). "
        + "Spielregel: Alles, was etwas ändert, wird eine Karte in der Assistent-Leiste — erst "
        + "«Anwenden» des Architekten ändert etwas, ausser im Coop oder in Voll. "
        + "Löschen geht nur über eine Karte, in jedem Modus. "
        + "Bilder (vis_render, vis_varianten, vis_grundlage): in Karte und Coop eine Karte, danach "
        + "gibt der Architekt am Render-Knoten frei. In Voll rechnen sie sofort, ohne Karte und "
        + "ohne Freigabe-Klick — höchstens 5 Läufe je Stunde (am Heim-PC gezählt) und nie mit "
        + "einem Bildmodell mit offener Lizenz; sonst wieder eine Karte. Freigeben selbst ist "
        + "kein Werkzeug. "
        + "Meldet ein Aufruf «wartet noch», arbeite weiter und frage später mit "
        + "\(Mcpkern.nachfrageName) nach; wiederhole den Aufruf nicht. "
        + "Prüfe Ergebnisse selbst, statt den Architekten zu fragen; halte nur bei "
        + "Entwurfsentscheiden an."
}

// ===================================================================== Werkzeuge als Daten

/// Was ein Werkzeug tut — daraus folgt, ob es eine Karte braucht (`Mcpfreigabe`).
public enum Werkzeugart: String, Equatable, Sendable, CaseIterable {
    /// Liest nur (Status, Graph, Mappe). Laeuft sofort, in jedem Modus.
    case lesen
    /// Aendert etwas (Knoten setzen, verbinden, Parameter).
    case aendern
    /// Loescht etwas (Knoten, Graph). **Immer Karte** (Entscheid 106c).
    case loeschen
    /// Bestellt ein Bild (Rendern, Varianten, Grundlage). Karte in «Karte» und «Coop» (106b); in «Voll»
    /// ohne Karte, solange der Heim-PC «frei» meldet und das Bildmodell zulaessig ist (Entscheid 146) —
    /// das entscheidet die Seite, nicht `brauchtKarte`.
    case rendern
    /// Haelt etwas an, das laeuft (`lauf_abbrechen`): aendert kein Dokument und gibt die
    /// Grafikkarte FREI statt sie zu starten — darum nie eine Karte (Stufe 4, 20.10.2026). Nur
    /// auf der Seite der Mac-App; die Knotenansicht kennt kein solches Werkzeug, und ihre vier
    /// Worte (`KiWerkzeugArt` in `ki-werkzeuge.ts`) bleiben gleich.
    case anhalten
    /// Bedient die Knotenansicht mit einer eigenen Maus der KI (`visbox_maus`, Stufe 6,
    /// 21.10.2026). Der Klick selbst ist nie eine Karte: Was er am Graph aendert, haelt die Wache
    /// der Seite an und legt es durch den Werkzeugsatz — dort gilt `brauchtKarte` mit der Art des
    /// ausgeloesten Befehls (Loeschen und Rendern ueber die Maus immer Karte). Die Sperrzonen (Freigeben,
    /// Bestellen, Loeschen, Karten, Schalter, Kennwoerter) stehen in der Seite (`kosmo-maus.ts`).
    case bedienen
}

/// Ein Werkzeug, wie Claude es in `tools/list` sieht.
public struct Mcpwerkzeug: Equatable, Sendable {
    public let name: String
    public let beschreibung: String
    /// Das JSON-Schema der Argumente (`inputSchema`), immer ein Objekt.
    public let eingabe: JSONWert
    public let art: Werkzeugart

    public init(name: String, beschreibung: String,
                eingabe: JSONWert = Mcpwerkzeug.ohneArgumente, art: Werkzeugart) {
        self.name = name
        self.beschreibung = beschreibung
        self.eingabe = eingabe
        self.art = art
    }

    /// Ein Schema ohne Argumente.
    public static let ohneArgumente: JSONWert = .objekt([
        "type": .text("object"), "properties": .objekt([:]),
        "additionalProperties": .wahrheit(false),
    ])

    /// Ob der Name die Form hat, die MCP-Programme annehmen: 1–64 Zeichen aus Buchstaben,
    /// Ziffern, `_` und `-`. Ein Werkzeug mit anderem Namen bietet der Kern nicht an — Claude
    /// Code wiese sonst die ganze Liste ab.
    public static func nameIstGueltig(_ name: String) -> Bool {
        guard (1...64).contains(name.count) else { return false }
        return name.unicodeScalars.allSatisfy {
            ("a"..."z").contains($0) || ("A"..."Z").contains($0) || ("0"..."9").contains($0)
                || $0 == "_" || $0 == "-"
        }
    }

    /// Die Form in `tools/list`. Die Hinweise (`annotations`, ab MCP 2025-03-26) sagen Claude,
    /// was nur liest und was loescht; aeltere Programme ueberlesen sie.
    public var alsJSON: JSONWert {
        .objekt([
            "name": .text(name),
            "description": .text(beschreibung),
            "inputSchema": eingabe,
            "annotations": .objekt([
                "readOnlyHint": .wahrheit(art == .lesen),
                "destructiveHint": .wahrheit(art == .loeschen),
            ]),
        ])
    }
}

/// Das Ergebnis eines Werkzeugs: Text, hoechstens ein Bild, und ob es ein Fehlschlag ist.
public struct Mcpergebnis: Equatable, Sendable {
    public let text: String
    /// Ein Bild an Claude (Entscheid 106f: Bilder an Claude erlaubt) — Base64 und Art.
    public let bild: (daten: String, art: String)?
    public let fehler: Bool

    public init(text: String, bild: (daten: String, art: String)? = nil, fehler: Bool = false) {
        self.text = text
        self.bild = bild
        self.fehler = fehler
    }

    public static func == (a: Mcpergebnis, b: Mcpergebnis) -> Bool {
        a.text == b.text && a.fehler == b.fehler && a.bild?.daten == b.bild?.daten
            && a.bild?.art == b.bild?.art
    }

    /// Die Form in `tools/call`: `content` und, bei einem Fehlschlag, `isError`.
    public var alsJSON: JSONWert {
        var inhalt: [JSONWert] = [.objekt(["type": .text("text"), "text": .text(text)])]
        if let bild {
            inhalt.append(.objekt(["type": .text("image"), "data": .text(bild.daten),
                                   "mimeType": .text(bild.art)]))
        }
        var felder: [String: JSONWert] = ["content": .liste(inhalt)]
        if fehler { felder["isError"] = .wahrheit(true) }
        return .objekt(felder)
    }

    /// Die Antwort auf ein Werkzeug, das es nicht gibt.
    public static func unbekannt(_ name: String) -> Mcpergebnis {
        Mcpergebnis(text: "Unbekanntes Werkzeug «\(name)». Die Liste gibt tools/list.",
                    fehler: true)
    }
}

/// Ein Aufruf, wie der Kern ihn an den Traeger reicht.
public struct Mcpaufruf: Equatable, Sendable {
    /// «K-1», «K-2», … — so steht er auf der Karte.
    public let kennung: String
    public let werkzeug: String
    /// Immer ein Objekt (fehlende Argumente werden `{}`).
    public let argumente: [String: JSONWert]

    public init(kennung: String, werkzeug: String, argumente: [String: JSONWert]) {
        self.kennung = kennung
        self.werkzeug = werkzeug
        self.argumente = argumente
    }
}

/// Was der Traeger auf einen Aufruf sagt.
public enum Traegerantwort: Equatable, Sendable {
    /// Fertig — das Ergebnis geht an Claude.
    case ergebnis(Mcpergebnis)
    /// Eine Karte liegt in der Assistent-Leiste; das Ergebnis kommt mit «Anwenden» oder
    /// «Ablehnen» ueber `Mcpkern.entscheide`. Der Text ist die Zusammenfassung der Karte.
    case karte(String)
}

// ===================================================================== Modus und Freigabe

/// Wie selbstaendig die KI arbeiten darf (Entscheid 106b; eingestellt oben in der
/// Assistent-Leiste, Entscheid 108 A — fuer Claude und den Assistenten zugleich).
public enum Selbstaendigkeit: String, Equatable, Sendable, CaseIterable {
    /// Jede Aenderung ist eine Karte. **Die Vorgabe.**
    case karte
    /// Aendern geht ohne Karte; Loeschen und Rendern nicht.
    case coop
    /// Vollautomatik: wie Coop, und Bilder rechnen ohne Karte und ohne Freigabe-Klick (Entscheid 146:
    /// hoechstens 5 Laeufe je Stunde, nie ein Bildmodell mit offener Lizenz). Loeschen bleibt Karte.
    case voll

    public static let vorgabe: Selbstaendigkeit = .karte

    public var wort: String {
        switch self {
        case .karte: return "Karte"
        case .coop: return "Coop"
        case .voll: return "Voll"
        }
    }
}

/// Wann eine Karte noetig ist — die Regel an EINER Stelle, damit Claude und der Assistent sie
/// gleich bekommen (Stufe 5).
public enum Mcpfreigabe {
    /// `true`: **Ein Mensch entscheidet an einer Karte.** `false`: Der Traeger darf sofort.
    ///
    /// DIE GRUNDREGEL: Lesen nie; Loeschen und Rendern immer (106b, 106c); Aendern nur im Modus
    /// Karte. Die eine Ausnahme — Rendern in «Voll» ohne Karte (Entscheid 146) — entscheidet die
    /// Knotenansicht je Aufruf mit dem Stand des Heim-PC (`voll-render.ts`), nicht diese Regel.
    public static func brauchtKarte(_ art: Werkzeugart, modus: Selbstaendigkeit) -> Bool {
        switch art {
        case .lesen, .anhalten, .bedienen: return false
        case .loeschen, .rendern: return true
        case .aendern: return modus == .karte
        }
    }

    /// Der Satz zur Regel, fuer `visbox_status` — je Modus (Entscheid 146).
    public static func satz(_ modus: Selbstaendigkeit) -> String {
        switch modus {
        case .karte:
            return "Modus: Karte — jede Änderung wartet auf «Anwenden»; ein Bild wartet danach auf "
                + "«Freigeben» am Render-Knoten."
        case .coop:
            return "Modus: Coop — Änderungen laufen ohne Karte; Löschen und Bilder bleiben eine "
                + "Karte, und die Grafikkarte gibt ein Mensch frei."
        case .voll:
            return "Modus: Voll — Änderungen und Bilder (vis_render, vis_varianten, vis_grundlage) "
                + "laufen ohne Karte und ohne Freigabe-Klick, höchstens \(Mcpfreigabe.vollGrenze) "
                + "Läufe je Stunde (am Heim-PC gezählt, über alle Geräte); danach und bei einem "
                + "Bildmodell mit offener Lizenz wieder eine Karte. Löschen bleibt eine Karte; "
                + "«Alle anhalten» hält alles an."
        }
    }

    /// Die Grenze je Stunde — dieselbe Zahl wie am Heim-PC (`knotenweg.VOLL_GRENZE`).
    public static let vollGrenze = 5

    /// Die Zeile zum Stand der Vollautomatik in `visbox_status` — der Satz des Heim-PC, sonst der
    /// Hinweis, dass er nicht antwortete (dann wird jedes Bild eine Karte).
    public static func vollSatz(_ vomHeimPC: String?) -> String {
        if let s = vomHeimPC?.trimmingCharacters(in: .whitespacesAndNewlines), !s.isEmpty { return s }
        return "Vollautomatik: Der Heim-PC hat seinen Stand nicht gemeldet — bis er antwortet, wird "
            + "jedes Bild eine Karte."
    }
}

/// Die Lage, wie der Traeger sie fuer `visbox_status` meldet.
public struct Mcplage: Equatable, Sendable {
    /// Ob die Knotenansicht bereit ist, Aufrufe anzunehmen.
    public let bereit: Bool
    /// Die offene Mappe — `nil`: keine.
    public let mappe: String?
    public let modus: Selbstaendigkeit
    /// Ein Satz dazu (z. B. «Die Werkzeuge kommen mit Stufe 3»). Leer: keiner.
    public let zusatz: String
    /// In «Voll»: der Stand der Vollautomatik vom Heim-PC (Entscheid 146). Leer: keiner.
    public let vollSatz: String

    public init(bereit: Bool, mappe: String? = nil, modus: Selbstaendigkeit = .vorgabe,
                zusatz: String = "", vollSatz: String = "") {
        self.bereit = bereit
        self.mappe = mappe
        self.modus = modus
        self.zusatz = zusatz
        self.vollSatz = vollSatz
    }
}

// ===================================================================== der Traeger

/// Wer die Werkzeuge ausfuehrt — seit Stufe 3 die Knotenansicht ueber die Mac-App (`Knotentraeger`).
///
/// **Der Kern prueft vorher:** Ein Name, der nicht in `werkzeuge()` steht, erreicht `rufe`
/// nie, sondern `unbekanntesWerkzeug`. Die Argumente sind dann ein Objekt.
public protocol Werkzeugtraeger: Sendable {
    /// Die Werkzeuge ohne die zwei des Kerns (`visbox_status`, `visbox_vorschlag_status`).
    func werkzeuge() async -> [Mcpwerkzeug]
    func lage() async -> Mcplage
    /// Fuehrt aus oder legt eine Karte. Dauert es laenger als `Mcp.wartefrist`, bekommt Claude
    /// «wartet noch», und das spaetere Ergebnis holt es mit `visbox_vorschlag_status`.
    func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort
    /// Was ein unbekannter Name zur Antwort bekommt. Vorgabe: «Unbekanntes Werkzeug».
    func unbekanntesWerkzeug(_ name: String) async -> Mcpergebnis
}

extension Werkzeugtraeger {
    public func unbekanntesWerkzeug(_ name: String) async -> Mcpergebnis {
        .unbekannt(name)
    }
}

// ===================================================================== der Kern

/// Der MCP-Kern: liest eine JSON-RPC-Nachricht von Claude und gibt die Antwort.
///
/// Ein `actor`: Mehrere Anfragen koennen zugleich laufen (jede HTTP-Verbindung eine), und ein
/// wartender `tools/call` haelt die anderen nicht auf.
public actor Mcpkern {
    public static let statusName = Mcp.servername + "_status"
    public static let nachfrageName = Mcp.servername + "_vorschlag_status"

    /// `visbox_status` — zuerst aufrufen.
    public static let statusWerkzeug = Mcpwerkzeug(
        name: statusName,
        beschreibung: "Zeigt, ob \(Marke.name) bereit ist, welche Mappe offen ist, wie viele "
            + "Vorschläge in der Assistent-Leiste warten und welcher Modus gilt (Karte, Coop, "
            + "Voll) und welche Fassung läuft. Zuerst aufrufen.",
        art: .lesen)

    /// `visbox_vorschlag_status` — nur nach «wartet noch».
    public static let nachfrageWerkzeug = Mcpwerkzeug(
        name: nachfrageName,
        beschreibung: "Fragt nach, ob ein Vorschlag in \(Marke.name) angewendet oder abgelehnt wurde. "
            + "Nur nötig, wenn ein früherer Aufruf «wartet noch» meldete; wartet bis 45 s auf "
            + "den Entscheid.",
        eingabe: .objekt([
            "type": .text("object"),
            "properties": .objekt([
                "kennung": .objekt([
                    "type": .text("string"),
                    "description": .text("Die Kennung aus der Meldung «wartet noch», z. B. «K-3»."),
                ]),
            ]),
            "required": .liste([.text("kennung")]),
            "additionalProperties": .wahrheit(false),
        ]),
        art: .lesen)

    private let traeger: Werkzeugtraeger
    private let fassung: String
    private let wartefrist: TimeInterval

    private var naechste = 1
    /// Die Zahl des naechsten Leseaufrufs («L-n», F15) — getrennt von den Karten.
    private var naechsteLesung = 1
    /// Wann zuletzt eine Gegenstelle etwas schickte — fuer «Claude verbunden» in der Leiste.
    public private(set) var letzterKontakt: Date?
    private var offen: [String: Offen] = [:]
    private var erledigt: [String: Mcpergebnis] = [:]
    private var erledigtFolge: [String] = []

    private struct Offen {
        var karte: String?
        var warter: [Warteplatz] = []
    }

    /// - Parameters:
    ///   - fassung: die Fassung der App, fuer `serverInfo`.
    ///   - wartefrist: in Proben kuerzer; sonst `Mcp.wartefrist`.
    public init(traeger: Werkzeugtraeger, fassung: String,
                wartefrist: TimeInterval = Mcp.wartefrist) {
        self.traeger = traeger
        self.fassung = fassung
        self.wartefrist = wartefrist
    }

    // ------------------------------------------------------------- von der App

    /// Der Entscheid an der Karte (oder das spaete Ergebnis): weckt alle, die darauf warten.
    /// Eine unbekannte oder schon erledigte Kennung aendert nichts.
    public func entscheide(_ kennung: String, _ ergebnis: Mcpergebnis) {
        guard let o = offen.removeValue(forKey: kennung) else { return }
        merke(kennung, ergebnis)
        o.warter.forEach { $0.wecke(ergebnis) }
    }

    /// Alle offenen Aufrufe auf einmal beantworten — etwa, wenn die Knotenansicht neu laedt und
    /// ihre Karten wegfallen. Gibt die Kennungen zurueck.
    @discardableResult
    public func beantworteOffene(_ ergebnis: Mcpergebnis) -> [String] {
        let kennungen = offeneVorschlaege().map(\.kennung)
        for k in kennungen { entscheide(k, ergebnis) }
        return kennungen
    }

    /// Die Leitung zu Claude steht wieder (Strang Karten, wie KosmoOrbit ab v0.1.10): Die App meldet
    /// ihre offenen Karten neu an, bevor ein zurueckgehaltener Entscheid hinausgeht. Eine Kennung,
    /// die schon erledigt ist, bleibt erledigt; eine offene bekommt die Zusammenfassung ihrer Karte.
    public func meldeNeu(_ karten: [(kennung: String, zusammenfassung: String)]) {
        for k in karten where erledigt[k.kennung] == nil {
            if offen[k.kennung] == nil { offen[k.kennung] = Offen() }
            offen[k.kennung]?.karte = k.zusammenfassung
        }
    }

    /// Die offenen Vorschlaege, nach Kennung — mit der Zusammenfassung ihrer Karte, falls eine
    /// liegt.
    public func offeneVorschlaege() -> [(kennung: String, karte: String?)] {
        offen.map { (kennung: $0.key, karte: $0.value.karte) }
            .sorted { Mcpkern.nummer($0.kennung) < Mcpkern.nummer($1.kennung) }
    }

    // ------------------------------------------------------------- von Claude

    /// Liest eine Nachricht (oder ein Buendel) und gibt die Antwort — `nil` bei Meldungen und
    /// Antworten, die keine Antwort bekommen.
    public func verarbeite(_ nachricht: JSONWert) async -> JSONWert? {
        letzterKontakt = Date()
        if case .liste(let buendel) = nachricht {
            // EIN BUENDEL (MCP 2025-03-26 kennt es, 2025-06-18 nicht mehr): jede Nachricht fuer
            // sich; ein leeres ist ungueltig.
            guard !buendel.isEmpty else {
                return Mcpkern.fehler(id: .null, -32600, "Leeres Bündel.")
            }
            var antworten: [JSONWert] = []
            for n in buendel {
                if let a = await verarbeiteEine(n) { antworten.append(a) }
            }
            return antworten.isEmpty ? nil : .liste(antworten)
        }
        return await verarbeiteEine(nachricht)
    }

    private func verarbeiteEine(_ nachricht: JSONWert) async -> JSONWert? {
        guard let felder = nachricht.alsObjekt else {
            return Mcpkern.fehler(id: .null, -32600, "Ungültige Anfrage.")
        }
        let id = felder["id"] ?? .null
        let istAnfrage = !id.istNull
        let methode = felder["method"]?.alsText
        let params = felder["params"]
        func antworte(_ ergebnis: JSONWert) -> JSONWert? {
            istAnfrage ? .objekt(["jsonrpc": .text("2.0"), "id": id, "result": ergebnis]) : nil
        }
        // EINE ID MUSS TEXT ODER GANZE ZAHL SEIN (JSON-RPC 2.0); sonst ist die Anfrage ungueltig.
        if istAnfrage, id.alsText == nil, id.alsGanz == nil {
            return Mcpkern.fehler(id: .null, -32600, "Die Kennung (id) muss Text oder Zahl sein.")
        }
        switch methode {
        case "initialize":
            let gewuenscht = params?["protocolVersion"]?.alsText
            return antworte(.objekt([
                "protocolVersion": .text(Mcpkern.fassungFuer(gewuenscht)),
                "capabilities": .objekt(["tools": .objekt(["listChanged": .wahrheit(false)])]),
                "serverInfo": .objekt(["name": .text(Mcp.servername), "version": .text(fassung)]),
                "instructions": .text(Mcp.anleitung),
            ]))
        case "ping":
            return antworte(.objekt([:]))
        case "tools/list":
            return antworte(.objekt(["tools": .liste(await liste().map(\.alsJSON))]))
        case "tools/call":
            guard let name = params?["name"]?.alsText else {
                return istAnfrage ? Mcpkern.fehler(id: id, -32602, "tools/call braucht «name».")
                    : nil
            }
            let roh = params?["arguments"] ?? .null
            guard roh.istNull || roh.alsObjekt != nil else {
                return istAnfrage
                    ? Mcpkern.fehler(id: id, -32602, "Die Argumente müssen ein Objekt sein.") : nil
            }
            let ergebnis = await rufe(name, argumente: roh.alsObjekt ?? [:])
            return antworte(ergebnis.alsJSON)
        default:
            // MELDUNGEN (`notifications/initialized`, `…/cancelled`) und Antworten des Programms
            // bekommen keine Antwort; dieser Server stellt selbst keine Anfragen.
            if let m = methode, m.hasPrefix("notifications/") { return nil }
            if !istAnfrage { return nil }
            if methode == nil {
                if felder["result"] != nil || felder["error"] != nil { return nil }
                return Mcpkern.fehler(id: id, -32600, "Ungültige Anfrage (ohne «method»).")
            }
            return Mcpkern.fehler(id: id, -32601, "Methode nicht unterstützt: \(methode ?? "")")
        }
    }

    /// Die Fassung, die der Kern beim Handschlag nennt: die gewuenschte, wenn er sie spricht,
    /// sonst seine neueste.
    public static func fassungFuer(_ gewuenscht: String?) -> String {
        if let g = gewuenscht, Mcp.protokolle.contains(g) { return g }
        return Mcp.protokolle[0]
    }

    // ------------------------------------------------------------- Werkzeuge

    /// Die zwei des Kerns und die des Traegers — ohne Doppel und ohne ungueltige Namen.
    private func liste() async -> [Mcpwerkzeug] {
        var namen: Set<String> = [Mcpkern.statusName, Mcpkern.nachfrageName]
        var l = [Mcpkern.statusWerkzeug, Mcpkern.nachfrageWerkzeug]
        for w in await traeger.werkzeuge()
        where Mcpwerkzeug.nameIstGueltig(w.name) && !namen.contains(w.name) {
            namen.insert(w.name)
            l.append(w)
        }
        return l
    }

    private func rufe(_ name: String, argumente: [String: JSONWert]) async -> Mcpergebnis {
        if name == Mcpkern.statusName { return await status() }
        if name == Mcpkern.nachfrageName {
            let kennung = argumente["kennung"]?.alsText ?? ""
            return await warteAuf(kennung)
        }
        guard let werkzeug = await liste().first(where: { $0.name == name }) else {
            return await traeger.unbekanntesWerkzeug(name)
        }
        // F15 (Mac-Demolauf 0.3.34, 22.10.2026): «K-n» NUR FUER VORSCHLAEGE, die eine Karte werden
        // koennen (aendern, loeschen, rendern) — sie stehen so auf der Karte. Lesen, Anhalten und
        // Bedienen zaehlen eigen als «L-n»; bis dahin sprangen die Kartennummern (K-1 gelesen, K-2
        // Karte …), und eine Nachfrage auf eine Lese-Kennung lieferte das alte Leseergebnis.
        let vorschlag = Mcpkern.istVorschlag(werkzeug.art)
        let kennung: String
        if vorschlag {
            kennung = "K-\(naechste)"
            naechste += 1
        } else {
            kennung = "\(Mcpkern.lesevorsatz)\(naechsteLesung)"
            naechsteLesung += 1
        }
        offen[kennung] = Offen()
        let aufruf = Mcpaufruf(kennung: kennung, werkzeug: name, argumente: argumente)
        // DER TRAEGER LAEUFT FUER SICH: Dauert er laenger als die Frist, antwortet der Kern
        // trotzdem («wartet noch»), und das Ergebnis wird gemerkt, wenn es kommt.
        let traeger = self.traeger
        Task { [weak self] in
            let antwort = await traeger.rufe(aufruf, werkzeug: werkzeug)
            await self?.traegerSagt(kennung, antwort)
        }
        let ergebnis = await warteAuf(kennung)
        // EIN LESEAUFRUF, DER SOFORT ANTWORTETE, IST KEIN VORSCHLAG: nichts zum Nachfragen. Nur wer
        // «wartet noch» hoerte, darf nachfragen (das spaete Ergebnis wird dann gemerkt).
        if !vorschlag, offen[kennung] == nil { vergiss(kennung) }
        return ergebnis
    }

    /// Ob ein Werkzeug dieser Art ein Vorschlag ist (eine Karte werden kann) und darum «K-n» heisst.
    public static func istVorschlag(_ art: Werkzeugart) -> Bool {
        switch art {
        case .aendern, .loeschen, .rendern: return true
        case .lesen, .anhalten, .bedienen: return false
        }
    }

    /// Der Vorsatz der Kennung eines Leseaufrufs — «L-1», «L-2», …
    public static let lesevorsatz = "L-"

    /// Die Antwort auf eine Nachfrage zu einem Leseaufruf: kein Vorschlag.
    public static func keinVorschlag(_ kennung: String) -> String {
        "Kein Vorschlag: «\(kennung)» war ein Leseaufruf, sein Ergebnis kam schon mit dem Aufruf. "
            + "Nachfragen gibt es nur für Vorschläge (K-…)."
    }

    private func traegerSagt(_ kennung: String, _ antwort: Traegerantwort) {
        switch antwort {
        case .ergebnis(let e):
            entscheide(kennung, e)
        case .karte(let zusammenfassung):
            offen[kennung]?.karte = zusammenfassung
        }
    }

    /// Wartet bis zur Frist auf das Ergebnis; danach «wartet noch».
    private func warteAuf(_ kennung: String) async -> Mcpergebnis {
        if let e = erledigt[kennung] { return e }
        if offen[kennung] == nil, kennung.hasPrefix(Mcpkern.lesevorsatz) {
            return Mcpergebnis(text: Mcpkern.keinVorschlag(kennung))
        }
        guard offen[kennung] != nil else {
            return Mcpergebnis(text: "Keine Vorschlag-Kennung «\(kennung)» bekannt.", fehler: true)
        }
        let platz = Warteplatz()
        offen[kennung]?.warter.append(platz)
        let frist = UInt64(max(0, wartefrist) * 1_000_000_000)
        let wecker = Task {
            try? await Task.sleep(nanoseconds: frist)
            platz.wecke(nil)
        }
        let ergebnis = await platz.warte()
        wecker.cancel()
        if let ergebnis { return ergebnis }
        offen[kennung]?.warter.removeAll { $0 === platz }
        return Mcpergebnis(text: Mcpkern.wartetNoch(kennung, karte: offen[kennung]?.karte))
    }

    /// Der Satz nach der Frist — **mit Karte** heisst: sie liegt in der Assistent-Leiste.
    public static func wartetNoch(_ kennung: String, karte: String?) -> String {
        let schluss = " Frage später mit \(Mcpkern.nachfrageName) nach; wiederhole den Aufruf nicht."
        if let karte {
            return "Wartet noch — Vorschlag \(kennung) liegt in der Assistent-Leiste: \(karte). "
                + "Erst «Anwenden» des Architekten ändert etwas; arbeite weiter." + schluss
        }
        return "Wartet noch — \(Marke.name) hat den Aufruf \(kennung) noch nicht beantwortet." + schluss
    }

    /// Die Zeile mit der Fassung in `visbox_status`, z. B. «Fassung: Visbox 0.3.21.».
    public static func fassungsSatz(_ fassung: String) -> String {
        let nummer = fassung.trimmingCharacters(in: .whitespacesAndNewlines)
        return "Fassung: \(Marke.name) \(nummer.isEmpty ? "unbekannt" : nummer)."
    }

    private func status() async -> Mcpergebnis {
        let lage = await traeger.lage()
        let zahl = await liste().count
        let vorschlaege = offeneVorschlaege()
        var zeilen: [String] = []
        if lage.bereit {
            zeilen.append("\(Marke.name) ist bereit. Mappe: «\(lage.mappe ?? "keine offen")». "
                          + "Werkzeuge: \(zahl). Offene Vorschläge: \(vorschlaege.count).")
        } else {
            zeilen.append("\(Marke.name) läuft, die Knotenansicht ist noch nicht bereit. "
                          + "Werkzeuge: \(zahl). Offene Vorschläge: \(vorschlaege.count).")
        }
        // DIE FASSUNG (Demolauf-Sitzung 21.10.2026): Claude sah bis dahin nur in `serverInfo`, welche
        // App antwortet, und das liest im Gespraech niemand. Dieselbe Nummer wie dort — die Mac-App
        // reicht sie aus der Info.plist (`CFBundleShortVersionString`, `Claudestdio`/`Claudeanschluss`).
        zeilen.append(Mcpkern.fassungsSatz(fassung))
        zeilen.append(Mcpfreigabe.satz(lage.modus))
        if !lage.vollSatz.isEmpty { zeilen.append(lage.vollSatz) }
        let karten = vorschlaege.compactMap { v in v.karte.map { "\(v.kennung) «\($0)»" } }
        if !karten.isEmpty {
            zeilen.append("In der Assistent-Leiste: \(karten.joined(separator: ", ")).")
        }
        if !lage.zusatz.isEmpty { zeilen.append(lage.zusatz) }
        return Mcpergebnis(text: zeilen.joined(separator: "\n"))
    }

    // ------------------------------------------------------------- Handgriffe

    private func merke(_ kennung: String, _ ergebnis: Mcpergebnis) {
        erledigt[kennung] = ergebnis
        erledigtFolge.append(kennung)
        while erledigtFolge.count > Mcp.gedaechtnis {
            erledigt[erledigtFolge.removeFirst()] = nil
        }
    }

    private func vergiss(_ kennung: String) {
        erledigt[kennung] = nil
        erledigtFolge.removeAll { $0 == kennung }
    }

    private static func nummer(_ kennung: String) -> Int {
        Int(kennung.dropFirst(2)) ?? Int.max
    }

    /// Eine Fehlerantwort nach JSON-RPC 2.0.
    public static func fehler(id: JSONWert, _ code: Int, _ satz: String) -> JSONWert {
        .objekt(["jsonrpc": .text("2.0"), "id": id,
                 "error": .objekt(["code": .ganz(code), "message": .text(satz)])])
    }
}

/// Ein Platz zum Warten, der **genau einmal** geweckt wird — vom Ergebnis oder von der Frist,
/// was zuerst kommt. Eine Sperre statt des Actors: Der Wecker der Frist laeuft ausserhalb.
final class Warteplatz: @unchecked Sendable {
    private let sperre = NSLock()
    private var fortsetzung: CheckedContinuation<Mcpergebnis?, Never>?
    private var geweckt = false
    private var wert: Mcpergebnis?

    func warte() async -> Mcpergebnis? {
        await withCheckedContinuation { (c: CheckedContinuation<Mcpergebnis?, Never>) in
            sperre.lock()
            if geweckt {
                let w = wert
                sperre.unlock()
                c.resume(returning: w)
            } else {
                fortsetzung = c
                sperre.unlock()
            }
        }
    }

    func wecke(_ ergebnis: Mcpergebnis?) {
        sperre.lock()
        guard !geweckt else { sperre.unlock(); return }
        geweckt = true
        wert = ergebnis
        let c = fortsetzung
        fortsetzung = nil
        sperre.unlock()
        c?.resume(returning: ergebnis)
    }
}

// ===================================================================== der Platzhalter

/// Der Traeger ohne Werkzeuge: `visbox_status` antwortet (der Kern), alles andere sagt, warum
/// nichts geht.
///
/// Zwei Lagen: **ohne App** (der Weg ueber stdio findet keine laufende Visbox — die eine, die
/// seit Stufe 3 noch gebraucht wird) und **in der App** (bis Stufe 3; heute nur noch in Proben).
public struct Mcpplatzhalter: Werkzeugtraeger {
    public enum Ort: Sendable { case inDerApp, ohneApp }

    public static let stufe3 = "Die Werkzeuge zum Bedienen der Knotenansicht kommen mit Stufe 3 "
        + "(Plan KI-Bedienung); heute gibt es nur \(Mcpkern.statusName) und \(Mcpkern.nachfrageName)."
    public static let ohneAppSatz = "\(Marke.name) läuft nicht auf diesem Rechner. Der Architekt muss "
        + "die \(Marke.name)-App öffnen; danach verbindet sich dieser Weg von selbst."

    public let ort: Ort
    public let modus: Selbstaendigkeit

    public init(ort: Ort = .inDerApp, modus: Selbstaendigkeit = .vorgabe) {
        self.ort = ort
        self.modus = modus
    }

    public func werkzeuge() async -> [Mcpwerkzeug] { [] }

    public func lage() async -> Mcplage {
        switch ort {
        case .inDerApp: return Mcplage(bereit: false, modus: modus, zusatz: Mcpplatzhalter.stufe3)
        case .ohneApp: return Mcplage(bereit: false, modus: modus, zusatz: Mcpplatzhalter.ohneAppSatz)
        }
    }

    public func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort {
        .ergebnis(await unbekanntesWerkzeug(aufruf.werkzeug))
    }

    public func unbekanntesWerkzeug(_ name: String) async -> Mcpergebnis {
        switch ort {
        case .inDerApp:
            return Mcpergebnis(text: "«\(name)» kommt mit Stufe 3 — nichts wurde ausgeführt. "
                               + Mcpplatzhalter.stufe3, fehler: true)
        case .ohneApp:
            return Mcpergebnis(text: "Nichts wurde ausgeführt. " + Mcpplatzhalter.ohneAppSatz,
                               fehler: true)
        }
    }
}
