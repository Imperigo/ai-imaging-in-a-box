import Foundation

// ============================================================================ Macmappe
//
// DIE MAPPE AM MAC («Visbox eigenständig», Schritt 3, 21.10.2026; Entscheide 103–103c, Blatt 28
// Feld 3 und Blatt 36 «Mappen am Mac»).
//
// Bis 0.3.14 lag jede Mappe am Heim-PC; die Knotenansicht las und sicherte sie über `/knoten/*`
// dort. Seither liegt sie AM MAC, als gewöhnlicher Ordner:
//
//     ~/<Marke>-Mappen/<Name>/
//         mappe.json          — dieses Format (`visbox.macmappe/v1`): Name, Herkunft, die Auskunft
//                               der Knotenansicht (Hüllbox, Standpunkte, Skizzen), die Aufträge
//         modell.glb          — das Modell (fehlt, solange keines geladen ist)
//         knotengraph.json    — der Graph der Knotenansicht (`visbox.knotengraph/v1`, wie am Heim-PC)
//         heim/<weg>          — Skizzen und Bilder, die beim Holen vom Heim-PC kamen
//         bilder/<auftrag>/   — was ein Auftrag zurückgab: `job.json` und die Bilder
//
// Die Knotenansicht merkt davon nichts: Sie fragt weiter `./mappe`, `./graph`, `./modell.glb`,
// `./skizze` — die App beantwortet diese Wege jetzt selbst aus der offenen Mappe (`ziel`). Der
// Heim-PC bekommt je Auftrag nur Modell und Szene (`POST /bruecke/jobs`, wie bisher mit Modell)
// und gibt die Bilder zurück; die App legt sie in die Mappe (`bilder/<auftrag>/`).
//
// RUECKWAERTS: Ist keine Mappe am Mac offen, gilt `ziel` nicht — alles geht wie bis 0.3.14 an
// den Heim-PC (`Knotenwege`).
//
// Hier steht nur die REINE Regel, unter Linux mit Proben (`MacmappeTests`); Lesen, Schreiben und
// Holen tut die Mac-App (`Start/Mappenablage.swift`, `Start/Knotenquelle.swift`).

/// Woher eine Mappe am Mac kommt.
public enum Mappenherkunft: String, Codable, Equatable, Sendable {
    /// Am Mac angelegt («Neue Mappe»).
    case angelegt
    /// Vom Heim-PC geholt («An den Mac holen»).
    case heim = "heim-pc"
    /// Mit der App geliefert (die Beispielmappe, Entscheid 103b).
    case mitgeliefert
}

/// Die Datei `mappe.json` einer Mappe am Mac.
public struct Macmappe: Codable, Equatable, Sendable {
    public static let formatkennung = "visbox.macmappe/v1"

    public var format: String
    /// Der Name, wie er in der Liste steht (der Ordner trägt ihn als `ordnername`).
    public var name: String
    public var herkunft: Mappenherkunft
    /// Wann angelegt bzw. geholt (ISO 8601, UTC).
    public var angelegt: String
    /// Die Zwillingsmappe am Heim-PC (ihre Kennung, `mappenpaket.finde`) — gesetzt nach dem Holen
    /// und nach «Datei laden …». Nur sie braucht der Heim-PC, und nur für Standpunkte und Skizzen.
    public var heimMappe: String?
    /// Die Auskunft der Knotenansicht über das Modell (`MappeAntwort` in `mappe.ts`), so wie der
    /// Heim-PC sie beim Holen gerechnet hat — Hüllbox, Standpunkte, Bauteile, Skizzen. Ohne Modell
    /// `nil`.
    public var knoten: JSONWert?
    /// Die Aufträge, die aus dieser Mappe bestellt wurden — nur ihre Bilder kommen zurück.
    public var auftraege: [String]
    /// Die Skizzen, die das iPad **an den Mac** schickte (Schritt 4, Entscheid 118) — die Dateien
    /// unter `ipad/`. Fehlt in einer Mappe von vorher (dann `nil`, und so wird es auch
    /// geschrieben: ohne das Feld).
    public var skizzen: [Macskizze]?

    public init(name: String, herkunft: Mappenherkunft, angelegt: String, heimMappe: String? = nil,
                knoten: JSONWert? = nil, auftraege: [String] = []) {
        self.format = Macmappe.formatkennung
        self.name = name
        self.herkunft = herkunft
        self.angelegt = angelegt
        self.heimMappe = heimMappe
        self.knoten = knoten
        self.auftraege = auftraege
    }

    /// Liest `mappe.json` — `nil`, wenn die Datei kein lesbares Format dieser Art ist.
    public static func lies(_ daten: Data) -> Macmappe? {
        guard let mappe = try? JSONDecoder().decode(Macmappe.self, from: daten),
              mappe.format == formatkennung else { return nil }
        return mappe
    }

    /// Schreibt `mappe.json` — eingerückt und sortiert, damit ein Mensch hineinsehen kann.
    public func daten() throws -> Data {
        let schreiber = JSONEncoder()
        schreiber.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        return try schreiber.encode(self)
    }

    /// Einen Auftrag vermerken (einmal, höchstens `auftraegeHoechstens`, die ältesten fallen weg).
    public mutating func vermerke(auftrag: String) {
        guard Mappenkern.istAuftragskennung(auftrag), !auftraege.contains(auftrag) else { return }
        auftraege.append(auftrag)
        if auftraege.count > Mappenkern.auftraegeHoechstens {
            auftraege.removeFirst(auftraege.count - Mappenkern.auftraegeHoechstens)
        }
    }
}

/// Was die App mit einer Anfrage der Knotenansicht tut, wenn eine Mappe am Mac offen ist.
public enum Mappenziel: Equatable, Sendable {
    /// `GET /knoten/mappe` — die Auskunft aus `mappe.json`.
    case mappe
    /// `GET /knoten/graph` — `knotengraph.json`.
    case graphLesen
    /// `POST /knoten/graph` — `knotengraph.json` ersetzen.
    case graphSichern
    /// `GET /knoten/modell.glb`.
    case modell
    /// `GET /knoten/skizze?name=…`.
    case skizze
    /// `GET /knoten/standpunkte?…` — an den Heim-PC, mit der Zwillingsmappe (`?mappe=…`).
    case standpunkte
    /// `POST /knoten/mappe-holen` — nach «Datei laden …»: das Modell der neuen Mappe am Heim-PC
    /// in die offene Mappe am Mac holen. Nur die App kennt diesen Weg.
    case modellHolen
    /// `POST /bruecke/jobs` — an den Heim-PC, mit dem Namen der Mappe; die Kennung wird vermerkt.
    case auftragAnlegen
    /// `GET /bruecke/jobs/<id>` — an den Heim-PC; ist er fertig, kommen die Bilder in die Mappe.
    case auftragLesen(String)
    /// `GET /bruecke/jobs/<id>/artifacts/<name>` — an den Heim-PC, eine Kopie in die Mappe; ohne
    /// Heim-PC aus der Mappe.
    case auftragsbild(String, String)
}

public enum Mappenkern {
    /// Der Ordner der Mappen am Mac (unter dem Heimordner des Benutzers) — der Name aus der Marke.
    public static let wurzelname = Marke.name + "-Mappen"
    public static let mappendatei = "mappe.json"
    public static let modelldatei = "modell.glb"
    public static let graphdatei = "knotengraph.json"
    /// Wo die Dateien vom Heim-PC liegen (Skizzen, Bilder — mit ihrem Weg von dort).
    public static let heimordner = "heim"
    /// Wo die Bilder der Aufträge liegen.
    public static let bilderordner = "bilder"
    /// Der Laufzettel eines Auftrags in der Mappe.
    public static let laufzettel = "job.json"
    /// Wie lang ein Name höchstens ist — wie am Heim-PC (`modellladen.NAME_HOECHSTENS`).
    public static let nameHoechstens = 60
    /// Wie viele Aufträge eine Mappe sich merkt.
    public static let auftraegeHoechstens = 500
    /// Das Format des Graphen — **dasselbe wie am Heim-PC** (`knotenweg.GRAPH_FORMAT`).
    public static let graphFormat = "visbox.knotengraph/v1"
    /// Höchstens so gross darf der Graph sein (`knotenweg.GRAPH_HOECHSTENS`).
    public static let graphHoechstens = 2 * 1024 * 1024
    /// Der lokale Weg der App nach «Datei laden …» — **kein** Weg des Heim-PC.
    public static let wegModellHolen = "/knoten/mappe-holen"
    /// Die drei Wege des Heim-PC für «An den Mac holen» (`WEG_KNOTEN_MAPPEN` …, bewacht).
    public static let wegMappen = "/knoten/mappen"
    public static let wegPaket = "/knoten/mappe-paket"
    public static let wegDatei = "/knoten/mappe-datei"
    /// Die Köpfe, mit denen ein Auftrag seine Mappe nennt (`KOPF_MAPPE_AM_MAC`, `KOPF_MAPPE_HEIM`).
    public static let kopfMappeAmMac = "X-Mappe-Am-Mac"
    public static let kopfMappeHeim = "X-Mappe-Heim"
    /// Die Endungen der Dateien, die vom Heim-PC kommen (`mappenpaket.BILDENDUNGEN` und glb).
    public static let endungen: Set<String> = [".png", ".jpg", ".jpeg", ".webp", ".glb"]

    // ------------------------------------------------------------- Namen

    /// Der Ordnername für einen Mappennamen — oder `nil`, wenn nichts Brauchbares übrig bleibt.
    /// Umlaute ausgeschrieben, nur Buchstaben, Ziffern, Leerschlag, `-` und `_`, höchstens
    /// `nameHoechstens` Zeichen, kein Punkt am Anfang.
    public static func ordnername(fuer name: String) -> String? {
        let ersatz: [Character: String] = ["ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe",
                                           "Ü": "Ue", "ß": "ss"]
        var aus = ""
        for zeichen in name {
            if let e = ersatz[zeichen] {
                aus += e
            } else if zeichen.isASCII, zeichen.isLetter || zeichen.isNumber || zeichen == "-" || zeichen == "_" {
                aus.append(zeichen)
            } else if zeichen == " " || zeichen == "." || zeichen == "/" {
                aus.append(" ")
            }
        }
        let teile = aus.split(separator: " ", omittingEmptySubsequences: true)
        var sauber = teile.joined(separator: " ")
        if sauber.count > nameHoechstens { sauber = String(sauber.prefix(nameHoechstens)) }
        sauber = sauber.trimmingCharacters(in: .whitespaces)
        return sauber.isEmpty ? nil : sauber
    }

    /// Ein freier Ordnername: `name`, sonst `name 2`, `name 3` …
    public static func freierName(_ name: String, belegt: Set<String>) -> String {
        let klein = Set(belegt.map { $0.lowercased() })
        if !klein.contains(name.lowercased()) { return name }
        var n = 2
        while true {
            let anhang = " \(n)"
            let kandidat = String(name.prefix(nameHoechstens - anhang.count)) + anhang
            if !klein.contains(kandidat.lowercased()) { return kandidat }
            n += 1
        }
    }

    /// Ein Weg in der Mappe, der **in ihr bleibt** — oder `nil`: kein leeres Glied, kein `.`/`..`,
    /// kein Glied mit Punkt am Anfang, kein Rückstrich, nur die bekannten Endungen.
    public static func sichererWeg(_ weg: String) -> String? {
        if weg.isEmpty || weg.contains("\\") || weg.contains("\0") || weg.hasPrefix("/") { return nil }
        let glieder = weg.split(separator: "/", omittingEmptySubsequences: false)
        for glied in glieder where glied.isEmpty || glied.hasPrefix(".") {
            return nil
        }
        guard let punkt = weg.lastIndex(of: "."), endungen.contains(weg[punkt...].lowercased()) else {
            return nil
        }
        return weg
    }

    /// Die Form der Auftragskennung des Heim-PC (`kosmo_szene.FREMDE_JOB_ID`: `vis-<Ziffern>-<6 hex>`).
    public static func istAuftragskennung(_ wert: String) -> Bool {
        let teile = wert.split(separator: "-", omittingEmptySubsequences: false)
        guard teile.count == 3, teile[0] == "vis", !teile[1].isEmpty,
              teile[1].allSatisfy({ $0.isASCII && $0.isNumber }),
              teile[2].count == 6, teile[2].allSatisfy({ "0123456789abcdef".contains($0) }) else {
            return false
        }
        return true
    }

    /// Ein flacher Dateiname eines Auftragsbilds (`bruecke._ist_flacher_name`).
    public static func istFlacherName(_ name: String) -> Bool {
        !name.isEmpty && !name.contains("/") && !name.contains("\\") && !name.hasPrefix(".")
            && !name.contains("\0")
    }

    // ------------------------------------------------------------- Wege der Knotenansicht

    /// Was die App mit dieser Anfrage tut, **wenn eine Mappe am Mac offen ist** — `nil`: wie bisher
    /// an den Heim-PC weiterreichen (oder aus dem Bau). `pfad` ist der entschlüsselte Pfad.
    public static func ziel(methode: String, pfad: String) -> Mappenziel? {
        let m = methode.uppercased()
        switch (m, pfad) {
        case ("GET", "/knoten/mappe"): return .mappe
        case ("GET", "/knoten/graph"): return .graphLesen
        case ("POST", "/knoten/graph"): return .graphSichern
        case ("GET", "/knoten/modell.glb"): return .modell
        case ("GET", "/knoten/skizze"): return .skizze
        case ("GET", "/knoten/standpunkte"): return .standpunkte
        case ("POST", wegModellHolen): return .modellHolen
        case ("POST", "/bruecke/jobs"), ("POST", "/bruecke/jobs/"): return .auftragAnlegen
        default: break
        }
        guard m == "GET", pfad.hasPrefix("/bruecke/jobs/") else { return nil }
        let teile = pfad.dropFirst("/bruecke/jobs/".count).split(separator: "/",
                                                                  omittingEmptySubsequences: false)
        if teile.count == 1, istAuftragskennung(String(teile[0])) {
            return .auftragLesen(String(teile[0]))
        }
        if teile.count == 3, teile[1] == "artifacts", istAuftragskennung(String(teile[0])) {
            let name = String(teile[2]).removingPercentEncoding ?? String(teile[2])
            if istFlacherName(name) { return .auftragsbild(String(teile[0]), name) }
        }
        return nil
    }

    // ------------------------------------------------------------- Antworten aus der Mappe

    /// Der Satz, wenn die Mappe noch kein Modell hat — wie am Heim-PC (`mappe_fuer_knoten`).
    public static func satzOhneModell(_ name: String) -> String {
        "Die Mappe «\(name)» hat noch kein Modell — «Datei laden …» holt eines herein."
    }

    /// Die Antwort auf `GET /knoten/mappe` aus der Mappe am Mac — in der Form von `MappeAntwort`
    /// (`mappe.ts`). `skizzenDa` sagt, welche Skizzen (ihr Name) als Datei in der Mappe liegen;
    /// nur sie stehen in der Liste.
    public static func knotenAntwort(_ mappe: Macmappe, glbDa: Bool, skizzenDa: Set<String>) -> JSONWert {
        var felder = mappe.knoten?.alsObjekt ?? [:]
        let geholt = (felder["skizzen"]?.alsListe ?? []).filter {
            guard let name = $0["name"]?.alsText else { return false }
            return skizzenDa.contains(name)
        }
        // DIE SKIZZEN VOM IPAD (Schritt 4) in der Form von `knotenweg.skizzen_der_mappe` — der
        // Knoten «Skizze vom iPad» sieht sie sofort. Standpunkt: der der Mappe (den eines
        // Bildes rechnet der Heim-PC an seiner Kopie; am Mac gibt es keine).
        let vomIpad = (mappe.skizzen ?? []).filter { skizzenDa.contains($0.name) && $0.stand != "verworfen" }
            .map { s -> JSONWert in
                .objekt(["name": .text(s.name), "titel": .null, "erzeugt": .text(s.erzeugt),
                         "ueber": s.ueber.map(JSONWert.text) ?? .null, "stand": .text(s.stand),
                         "bemerkung": s.bemerkung.map(JSONWert.text) ?? .null,
                         "standpunkt": .text("mappe")])
            }
        // DIE NEUESTE ZUERST, wie am Heim-PC — STABIL: Gleich alte behalten ihre Reihenfolge.
        let skizzen = vomIpad.isEmpty ? geholt : (geholt + vomIpad).enumerated().sorted { a, b in
            let (ea, eb) = (a.element["erzeugt"]?.alsText ?? "", b.element["erzeugt"]?.alsText ?? "")
            return ea != eb ? ea > eb : a.offset < b.offset
        }.map { $0.element }
        felder["skizzen"] = .liste(skizzen)
        felder["name"] = .text(mappe.name)
        felder["mappe"] = .text(mappe.name)
        felder["glb"] = .wahrheit(glbDa)
        felder["am_mac"] = .wahrheit(true)
        if felder["huellbox_vermerk"] == nil { felder["huellbox_vermerk"] = .text("") }
        if felder["hochachse"] == nil { felder["hochachse"] = .null }
        if glbDa {
            if felder["huellbox_m"] == nil { felder["huellbox_m"] = .null }
            if felder["grund"] == nil { felder["grund"] = .text("") }
        } else {
            felder["huellbox_m"] = .null
            felder["standpunkte"] = .null
            felder["bauteile"] = .null
            felder["grund"] = .text(satzOhneModell(mappe.name))
        }
        return .objekt(felder)
    }

    /// Der Weg einer Skizze in der Mappe — `heim/<name>` für eine vom Heim-PC geholte,
    /// `ipad/<datei>` (unverändert) für eine, die das iPad an den Mac schickte (Schritt 4);
    /// `nil` für einen unsicheren Namen.
    public static func skizzenweg(_ name: String) -> String? {
        guard let sicher = sichererWeg(name) else { return nil }
        let teile = sicher.split(separator: "/", omittingEmptySubsequences: false)
        if teile.count == 2, teile[0] == Substring(Macskizzen.ordner), istFlacherName(String(teile[1])) {
            return sicher
        }
        return heimordner + "/" + sicher
    }

    /// Die Namen aller Skizzen der Mappe — geholte und die vom iPad. Welche davon als Datei da
    /// sind, prüft der Mac (`skizzenDa` in `knotenAntwort`).
    public static func skizzennamen(_ mappe: Macmappe) -> [String] {
        (mappe.knoten?["skizzen"]?.alsListe ?? []).compactMap { $0["name"]?.alsText }
            + (mappe.skizzen ?? []).map { $0.name }
    }

    // ------------------------------------------------------------- der Graph

    /// Der gesicherte Graph als Antwort `{graphen, satz}` — wie `knotenweg.lies_graph`.
    public static func graphAntwort(_ datei: Data?) -> JSONWert {
        guard let datei else { return .objekt(["graphen": .liste([]), "satz": .null]) }
        guard let wert = try? JSONWert.lies(datei), wert["format"]?.alsText == graphFormat,
              let graphen = wert["graphen"], (try? pruefeGraphen(graphen)) != nil else {
            return .objekt(["graphen": .liste([]),
                            "satz": .text("Der gesicherte Graph liess sich nicht lesen.")])
        }
        return .objekt(["graphen": graphen, "satz": .null])
    }

    public enum Graphfehler: Error, Equatable {
        case zuGross
        case keinJSON
        case keineListe
        case keinRendergraph

        public var satz: String {
            switch self {
            case .zuGross: return "Der Graph ist zu gross, um ihn zu sichern."
            case .keinJSON: return "Der Graph ist kein JSON."
            case .keineListe: return "Der Graph der Mappe muss eine Liste sein."
            case .keinRendergraph: return "Im Graph der Mappe steht etwas, das kein Render-Graph ist."
            }
        }

        public var status: Int { self == .zuGross ? 413 : 400 }
    }

    /// Nur Render-Graphen (`kind == "visgraph"`, `id` Text, `nodes`/`edges` Listen) —
    /// dieselbe Regel wie `knotenweg.pruefe_graphen`.
    @discardableResult
    public static func pruefeGraphen(_ graphen: JSONWert) throws -> [JSONWert] {
        guard let liste = graphen.alsListe else { throw Graphfehler.keineListe }
        for g in liste {
            guard g["kind"]?.alsText == "visgraph", g["id"]?.alsText != nil,
                  g["nodes"]?.alsListe != nil, g["edges"]?.alsListe != nil else {
                throw Graphfehler.keinRendergraph
            }
        }
        return liste
    }

    /// Aus dem Rumpf von `POST ./graph` (`{graphen: [...]}`) die Datei `knotengraph.json` und die
    /// Zahl der gesicherten Graphen.
    public static func graphDatei(aus rumpf: Data) throws -> (datei: Data, anzahl: Int) {
        if rumpf.count > graphHoechstens { throw Graphfehler.zuGross }
        guard let wert = try? JSONWert.lies(rumpf.isEmpty ? Data("{}".utf8) : rumpf) else {
            throw Graphfehler.keinJSON
        }
        let liste = try pruefeGraphen(wert["graphen"] ?? .null)
        let datei = try JSONWert.objekt(["format": .text(graphFormat), "graphen": .liste(liste)]).daten()
        if datei.count > graphHoechstens { throw Graphfehler.zuGross }
        return (datei, liste.count)
    }

    // ------------------------------------------------------------- Aufträge

    /// Die Kennung aus der Antwort auf `POST /bruecke/jobs` (`job_id`).
    public static func auftragskennung(aus antwort: Data) -> String? {
        guard let wert = try? JSONWert.lies(antwort), let id = wert["job_id"]?.alsText,
              istAuftragskennung(id) else { return nil }
        return id
    }

    /// Die Bilder eines **fertigen** Auftrags (`status == "done"`, `result.images`) — `nil`,
    /// solange er läuft oder wenn das Ergebnis nicht lesbar ist. Nur flache Namen.
    public static func fertigeBilder(laufzettel: Data) -> [String]? {
        guard let wert = try? JSONWert.lies(laufzettel), wert["status"]?.alsText == "done",
              let bilder = wert["result"]?["images"]?.alsListe else { return nil }
        let namen = bilder.compactMap { $0.alsText }.filter(istFlacherName)
        return namen.count == bilder.count ? namen : nil
    }

    /// Wo ein Auftrag in der Mappe liegt: `bilder/<id>`, und eine Datei darin.
    public static func auftragsweg(_ id: String, datei: String? = nil) -> String? {
        guard istAuftragskennung(id) else { return nil }
        guard let datei else { return bilderordner + "/" + id }
        guard istFlacherName(datei) else { return nil }
        return bilderordner + "/" + id + "/" + datei
    }

    /// Die Köpfe eines Auftrags aus einer Mappe am Mac: ihr Name, und die Zwillingsmappe am
    /// Heim-PC, wenn es eine gibt. Der Name ist kodiert (ein Kopf trägt kein «ü»).
    public static func auftragskoepfe(_ mappe: Macmappe) -> [Kopfzeile] {
        var aus = [Kopfzeile(kopfMappeAmMac, kodiert(mappe.name))]
        if let heim = mappe.heimMappe { aus.append(Kopfzeile(kopfMappeHeim, kodiert(heim))) }
        return aus
    }

    /// Prozentkodiert für Frage und Kopf (nur Buchstaben, Ziffern und `-_.~` bleiben).
    public static func kodiert(_ text: String) -> String {
        var erlaubt = CharacterSet.alphanumerics
        erlaubt.insert(charactersIn: "-_.~")
        return text.addingPercentEncoding(withAllowedCharacters: erlaubt) ?? ""
    }

    // ------------------------------------------------------------- Standpunkte

    /// Der Satz, wenn eine Mappe am Mac keinen Zwilling am Heim-PC hat.
    public static let satzStandpunkteOhneZwilling =
        "Standpunkte mit eigenen Werten rechnet der Heim-PC an seiner Kopie der Mappe — diese Mappe "
        + "hat dort keine. Der Auftrag rechnet sie trotzdem."

    /// Die Frage an den Heim-PC für die Standpunkte: die der Seite ohne `ordner`/`mappe`, dazu
    /// `mappe=<Zwilling>`. `nil` ohne Zwilling.
    public static func standpunkteFrage(kodierteFrage: String?, heimMappe: String?) -> String? {
        guard let heimMappe else { return nil }
        let teile = (kodierteFrage ?? "").split(separator: "&").filter {
            !$0.hasPrefix("ordner=") && !$0.hasPrefix("mappe=") && !$0.isEmpty
        }
        return (teile.map(String.init) + ["mappe=" + kodiert(heimMappe)]).joined(separator: "&")
    }

    // ------------------------------------------------------------- «Datei laden …»

    /// Der Name der Mappe am Heim-PC aus dem Rumpf von `POST /knoten/mappe-holen` (`{mappe}`).
    public static func holwunsch(_ rumpf: Data) -> String? {
        guard let wert = try? JSONWert.lies(rumpf), let name = wert["mappe"]?.alsText,
              istHeimkennung(name) else { return nil }
        return name
    }

    /// Eine Kennung einer Mappe am Heim-PC (`mappenpaket.pruefe_kennung`).
    public static func istHeimkennung(_ k: String) -> Bool {
        !k.isEmpty && k.count <= nameHoechstens && !k.contains("/") && !k.contains("\\")
            && !k.hasPrefix(".") && !k.contains("\0")
    }
}

// ============================================================================ Mappenpaket

/// Eine Mappe am Heim-PC, wie `GET /knoten/mappen` sie nennt.
public struct Heimmappe: Equatable, Sendable, Identifiable {
    public let mappe: String
    public let name: String
    public let modell: Bool
    public let skizzen: Int
    public let bilder: Int

    public var id: String { mappe }

    public init(mappe: String, name: String, modell: Bool, skizzen: Int, bilder: Int) {
        self.mappe = mappe
        self.name = name
        self.modell = modell
        self.skizzen = skizzen
        self.bilder = bilder
    }

    /// Die Liste aus der Antwort — ganz oder gar nicht.
    public static func liste(_ daten: Data) -> [Heimmappe]? {
        guard let wert = try? JSONWert.lies(daten), wert["format"]?.alsText == Mappenpaket.formatkennung
        else { return nil }
        return JSONWert.ganzOderNicht(wert["mappen"]) { e -> Heimmappe? in
            guard let k = e["mappe"]?.alsText, Mappenkern.istHeimkennung(k) else { return nil }
            return Heimmappe(mappe: k, name: e["name"]?.alsText ?? k,
                             modell: e["modell"]?.alsWahrheit ?? false,
                             skizzen: e["skizzen"]?.alsGanz ?? 0, bilder: e["bilder"]?.alsGanz ?? 0)
        }.liste
    }

    /// Die zweite Zeile in der Liste («Modell · 3 Skizzen · 12 Bilder»).
    public var untertitel: String {
        var teile = [modell ? "Modell" : "ohne Modell"]
        if skizzen > 0 { teile.append(skizzen == 1 ? "1 Skizze" : "\(skizzen) Skizzen") }
        teile.append(bilder == 0 ? "keine Bilder" : (bilder == 1 ? "1 Bild" : "\(bilder) Bilder"))
        return teile.joined(separator: " · ")
    }
}

/// Eine Datei des Pakets und wohin sie in der Mappe am Mac kommt.
public struct Holschritt: Equatable, Sendable {
    /// Der Weg am Heim-PC (`?weg=…`).
    public let weg: String
    /// Der Weg in der Mappe am Mac.
    public let ziel: String
    public let bytes: Int
    public let art: String
}

/// Die Auskunft `GET /knoten/mappe-paket` (`aiimaging.mappenpaket.paket`).
public struct Mappenpaket: Equatable, Sendable {
    public static let formatkennung = "visbox.mappenpaket/v1"

    public let mappe: String
    public let name: String
    public let knoten: JSONWert
    public let graph: JSONWert
    public let schritte: [Holschritt]

    /// Liest das Paket — `nil`, wenn Format, Kennung oder **ein** Dateiweg nicht passt.
    public static func lies(_ daten: Data) -> Mappenpaket? {
        guard let wert = try? JSONWert.lies(daten), wert["format"]?.alsText == formatkennung,
              let mappe = wert["mappe"]?.alsText, Mappenkern.istHeimkennung(mappe),
              let knoten = wert["knoten"], knoten.alsObjekt != nil else { return nil }
        let (schritte, lage) = JSONWert.ganzOderNicht(wert["dateien"]) { e -> Holschritt? in
            guard let weg = e["weg"]?.alsText, let art = e["art"]?.alsText,
                  let bytes = e["bytes"]?.alsGanz, bytes >= 0,
                  let sicher = Mappenkern.sichererWeg(weg) else { return nil }
            let ziel = art == "modell" ? Mappenkern.modelldatei : Mappenkern.heimordner + "/" + sicher
            if art == "modell" && sicher != Mappenkern.modelldatei { return nil }
            return Holschritt(weg: sicher, ziel: ziel, bytes: bytes, art: art)
        }
        guard lage != .nichtLesbar else { return nil }
        return Mappenpaket(mappe: mappe, name: wert["name"]?.alsText ?? mappe, knoten: knoten,
                           graph: wert["graph"] ?? .objekt(["graphen": .liste([])]),
                           schritte: schritte ?? [])
    }

    /// Was noch zu holen ist: jede Datei, die am Mac fehlt oder eine andere Grösse hat. Nur das
    /// Modell, wenn `nurModell` (nach «Datei laden …»).
    public func holplan(vorhanden: [String: Int], nurModell: Bool = false) -> [Holschritt] {
        schritte.filter { s in
            (!nurModell || s.art == "modell") && vorhanden[s.ziel] != s.bytes
        }
    }

    /// Die Auskunft der Knotenansicht für `mappe.json` — `glb` als Wahrheitswert, nie ein Pfad.
    public var knotenFuerMappe: JSONWert {
        var felder = knoten.alsObjekt ?? [:]
        felder["glb"] = .wahrheit(felder["glb"]?.alsWahrheit ?? false)
        return .objekt(felder)
    }

    /// Der Graph als Datei `knotengraph.json` — `nil`, wenn keiner gesichert ist.
    public var graphDatei: Data? {
        guard let liste = graph["graphen"]?.alsListe, !liste.isEmpty,
              (try? Mappenkern.pruefeGraphen(.liste(liste))) != nil else { return nil }
        return try? JSONWert.objekt(["format": .text(Mappenkern.graphFormat), "graphen": .liste(liste)]).daten()
    }

    /// Die Adressen am Heim-PC — gleicher Bau wie jeder Datenweg (`Knotenwege.heimAdresse`).
    public static func listeAdresse(basis: URL) -> URL? {
        Knotenwege.heimAdresse(pfad: Mappenkern.wegMappen, kodierteFrage: nil, basis: basis)
    }

    public static func paketAdresse(basis: URL, mappe: String) -> URL? {
        Knotenwege.heimAdresse(pfad: Mappenkern.wegPaket,
                               kodierteFrage: "mappe=" + Mappenkern.kodiert(mappe), basis: basis)
    }

    public static func dateiAdresse(basis: URL, mappe: String, weg: String) -> URL? {
        Knotenwege.heimAdresse(pfad: Mappenkern.wegDatei,
                               kodierteFrage: "mappe=" + Mappenkern.kodiert(mappe) + "&weg="
                                   + Mappenkern.kodiert(weg), basis: basis)
    }
}

// ============================================================================ die Liste

/// Eine Zeile «Am Mac» im Fenster «Mappen» (Blatt 36, Feld 1).
public struct Mappenzeile: Equatable, Sendable, Identifiable {
    public let ordner: String
    public let name: String
    public let untertitel: String
    public let offen: Bool

    public var id: String { ordner }
}

public enum Mappenliste {
    /// Die Zeilen «Am Mac», die offene zuerst, dann nach Name.
    public static func amMac(_ mappen: [(ordner: String, mappe: Macmappe)], offen: String?,
                             heute: Date, kalender: Calendar = Calendar(identifier: .gregorian)) -> [Mappenzeile] {
        let zeilen = mappen.map { eintrag -> Mappenzeile in
            let istOffen = eintrag.ordner == offen
            var teile: [String] = []
            if istOffen { teile.append("offen") }
            teile.append(herkunftsWort(eintrag.mappe, heute: heute, kalender: kalender))
            return Mappenzeile(ordner: eintrag.ordner, name: eintrag.mappe.name,
                               untertitel: teile.joined(separator: " · "), offen: istOffen)
        }
        return zeilen.sorted { a, b in
            if a.offen != b.offen { return a.offen }
            return a.name.localizedCaseInsensitiveCompare(b.name) == .orderedAscending
        }
    }

    /// «Noch am Heim-PC»: was dort liegt und noch keinen Zwilling am Mac hat.
    public static func nochAmHeim(_ heim: [Heimmappe], amMac: [Macmappe]) -> [Heimmappe] {
        let geholt = Set(amMac.compactMap { $0.heimMappe })
        return heim.filter { !geholt.contains($0.mappe) }
    }

    static func herkunftsWort(_ mappe: Macmappe, heute: Date, kalender: Calendar) -> String {
        if mappe.herkunft == .mitgeliefert { return "mitgeliefert" }
        let tag = datum(mappe.angelegt).map { tagWort($0, heute: heute, kalender: kalender) } ?? ""
        let vorne = mappe.herkunft == .heim ? "vom Heim-PC geholt" : "angelegt"
        return tag.isEmpty ? vorne : vorne + " · " + tag
    }

    static func datum(_ iso: String) -> Date? {
        let leser = ISO8601DateFormatter()
        return leser.date(from: iso)
    }

    static func tagWort(_ tag: Date, heute: Date, kalender: Calendar) -> String {
        var k = kalender
        k.timeZone = TimeZone(identifier: "UTC") ?? k.timeZone
        if k.isDate(tag, inSameDayAs: heute) { return "heute" }
        if let gestern = k.date(byAdding: .day, value: -1, to: heute), k.isDate(tag, inSameDayAs: gestern) {
            return "gestern"
        }
        let t = k.dateComponents([.day, .month, .year], from: tag)
        return String(format: "%02d.%02d.%04d", t.day ?? 0, t.month ?? 0, t.year ?? 0)
    }

    /// Jetzt als ISO 8601 (UTC, Sekunden) — für `angelegt`.
    public static func jetzt(_ datum: Date = Date()) -> String {
        ISO8601DateFormatter().string(from: datum)
    }
}

// ============================================================================ die Sätze

/// Die Sätze des Fensters «Mappen» — wörtlich nach Blatt 28 Feld 3 und Blatt 36.
public enum Mappensaetze {
    public static let titel = "Mappen"
    public static let amMac = "Am Mac"
    public static let nochAmHeim = "Noch am Heim-PC"
    public static let holen = "An den Mac holen"
    public static let oeffnen = "Öffnen"
    public static let offen = "Offen"
    public static let neu = "Neue Mappe"
    public static let anlegen = "Anlegen"
    public static let namensfeld = "Name der Mappe"
    public static let menue = "Mappen …"
    public static let fuss = "Einmal holen, danach liegt die Mappe am Mac. Der Heim-PC bekommt je Auftrag nur "
        + "Modell und Szene und gibt die Bilder zurück."
    public static let neuSatz = "Eine neue Mappe ist leer; «Datei laden …» am Modell-Knoten holt das Modell hinein."
    public static let ohneHeim = "Der Heim-PC ist nicht erreichbar — seine Mappen stehen hier, sobald er da ist."
    public static let nichtsAmHeim = "Am Heim-PC liegt keine Mappe, die nicht schon am Mac ist."
    /// Rückwärts: die Knotenansicht wieder mit der Mappe am Heim-PC, wie bis 0.3.14.
    public static let wieBisher = "Ohne Mappe am Mac (wie bisher: Mappe am Heim-PC)"
    public static let wieBisherSatz = "Ohne offene Mappe am Mac liest die Knotenansicht die Mappe am Heim-PC."
}
