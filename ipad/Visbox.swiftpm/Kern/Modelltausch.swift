import Foundation

// «MODELL LADEN» IN EINE BESTEHENDE MAPPE AM MAC (A0063b).
//
// Runde 1 (04.11.2026): Das neue Modell liegt erst an seinem Platz, dann wird geprüft; scheitert die
// Prüfung oder das Schreiben von `mappe.json`, kommt das alte Modell zurück.
// Runde 2 (07.11.2026, G-A0063b Mangel 2): Der ganze Ablauf steht hier im Kern, mit eingespeistem
// Holen, damit `holeModell` selbst unter Linux im XCTest läuft (`ModelltauschAblaufTests`). Die
// Mac-App (`Start/Mappenablage.swift`) reicht nur die Leitung und ihre Platte herein.

/// Ein Fehler mit einem Satz für den Menschen — `Mappenholer.satz` gibt ihn wörtlich weiter.
public struct Mappenfehler: LocalizedError, Equatable {
    public let satz: String
    public init(satz: String) { self.satz = satz }
    public var errorDescription: String? { satz }
}

/// Wie der Ablauf `mappe.json` liest und schreibt — in der App `Mappenablage` (atomar über eine
/// Zwischendatei), in den Proben eine Platte im Zwischenordner.
public protocol Mappenzugriff {
    static func lies(_ ordner: URL) -> Macmappe?
    static func schreibe(_ mappe: Macmappe, in ordner: URL) throws
}

public enum Modelltausch {
    /// Die Kopie des Modells vor dem letzten Laden.
    public static let vorherdatei = "modell.vorher.glb"

    /// Der Satz, wenn in dieselbe Mappe schon ein Modell geholt wird (G-A0063b Mangel 5).
    public static let satzLaeuftSchon =
        "In diese Mappe wird gerade schon ein Modell geholt — bitte warten, bis es da ist, dann noch einmal."

    /// Angehängt, wenn nach einem Scheitern das alte Modell nicht zurückkam (Mangel 4).
    public static let satzNichtZurueck =
        " Das alte Modell kam dabei nicht zurück (die Kopie heisst «modell.vorher.glb» in der Mappe) — "
        + "bitte «Andere Datei …» noch einmal."

    /// Die Mappen (ihr Ordner), in die gerade ein Modell geholt wird — je Mappe höchstens eines.
    @MainActor private static var laufend: Set<String> = []

    /// Ein Satz, wenn die Auskunft des Pakets nicht zur liegenden Datei gehört, sonst `nil`. Ohne
    /// Abdruck im Paket gibt es nichts zu vergleichen (die Mappe zeigt dann «Modell neu holen»).
    public static func abweichung(summe: String?, knoten: JSONWert) -> String? {
        guard let erwartet = knoten["glb_abdruck"]?["summe"]?.alsText, !erwartet.isEmpty,
              summe != erwartet else { return nil }
        return "Das neue Modell kam anders an den Mac, als der Heim-PC es beschreibt."
    }

    /// Nach «Datei laden …» (Wirt: `POST ./mappe-holen`): das Modell der Mappe `kennung` am Heim-PC
    /// in **die Mappe am Mac, aus der geladen wurde** (`ordner`); sie nennt danach diese als Zwilling.
    ///
    /// `fortschrittEnde` räumt den Fortschrittssatz der App ab, wenn dieser Lauf endet (Erfolg oder
    /// Fehler) — ein vom Riegel abgewiesener Aufruf ruft es nicht.
    ///
    /// `Mappenablage` ist der Zugriff auf `mappe.json` (in der App die gleichnamige Klasse),
    /// `holePaket` die Auskunft des Heim-PC, `holeDateien` legt die Dateien des Plans in den Ordner
    /// (`Modelltausch.lege`), `summe` rechnet den Abdruck der liegenden `modell.glb`.
    ///
    /// Befund N1 (22.10.2026): `mappe.json` wird erst nach dem Holen frisch gelesen — was in der
    /// Zwischenzeit dazukam (ein Auftrag, eine Skizze vom iPad), bleibt stehen.
    @MainActor
    public static func holeModell<Mappenablage: Mappenzugriff>(
        von kennung: String, in ordner: URL, ablage _: Mappenablage.Type,
        holePaket: @MainActor () async throws -> Mappenpaket,
        holeDateien: @MainActor (_ plan: [Holschritt], _ titel: String) async throws -> Void,
        summe: @MainActor () -> String?,
        fortschrittEnde: @MainActor () -> Void = {}
    ) async throws {
        // MANGEL 5: ZWEI «MODELL LADEN» IN DIESELBE MAPPE verschränkten sich an den await-Stellen —
        // das zweite überschrieb die Kopie, ein Scheitern des ersten holte dann das falsche zurück.
        let schluessel = ordner.standardizedFileURL.path
        guard laufend.insert(schluessel).inserted else { throw Mappenfehler(satz: satzLaeuftSchon) }
        // A0261 (G-A0063b Runde 2, Befund 5): `fortschrittEnde` räumt den Fortschrittssatz ab, aber nur
        // für den EIGENEN Lauf — also erst hier, nach dem Riegel. Ein abgewiesenes zweites Laden
        // (oben) löscht den Satz des ersten, noch laufenden nicht.
        defer { laufend.remove(schluessel); fortschrittEnde() }
        guard let vorher = Mappenablage.lies(ordner) else {
            throw Mappenfehler(satz: "Die Mappe am Mac ist nicht mehr lesbar — unter «Mappen …» eine andere öffnen.")
        }
        let paket = try await holePaket()
        // BEFUND «ANDERE DATEI» (0.3.67): Ohne Modell im Paket gibt es nichts zu ersetzen — ein Satz,
        // kein stilles «fertig».
        let plan = paket.holplan(vorhanden: [:], nurModell: true)
        guard let schritt = plan.first else {
            throw Mappenfehler(satz: "Die Mappe «\(kennung)» am Heim-PC hat kein Modell zum Holen.")
        }
        let glb = ordner.appendingPathComponent(Mappenkern.modelldatei)
        let fm = FileManager.default
        let vorherGlb = ordner.appendingPathComponent(vorherdatei)
        let warDa = fm.fileExists(atPath: glb.path)
        if warDa {
            try? fm.removeItem(at: vorherGlb)
            try fm.copyItem(at: glb, to: vorherGlb)
        }
        // MANGEL 3: AUCH EIN ABBRUCH BEIM HOLEN SELBST (Netz, Status, Verschieben) holt das alte zurück.
        do {
            try await holeDateien(plan, vorher.name)
        } catch {
            throw scheitert(error, glb: glb, vorher: vorherGlb, warDa: warDa)
        }
        // ERST WENN DAS NEUE MODELL GANZ DA LIEGT, nennt `mappe.json` den neuen Stand.
        let groesse = (try? fm.attributesOfItem(atPath: glb.path))?[.size] as? Int
        guard groesse == schritt.bytes else {
            throw scheitert(Mappenfehler(satz: "Das neue Modell kam nicht ganz an den Mac (\(groesse ?? 0) von \(schritt.bytes) Bytes)."),
                            glb: glb, vorher: vorherGlb, warDa: warDa)
        }
        if let abweichung = abweichung(summe: summe(), knoten: paket.knoten) {
            throw scheitert(Mappenfehler(satz: abweichung), glb: glb, vorher: vorherGlb, warDa: warDa)
        }
        var mappe = Mappenablage.lies(ordner) ?? vorher
        mappe.knoten = paket.knotenFuerMappe
        mappe.heimMappe = kennung
        do {
            try Mappenablage.schreibe(mappe, in: ordner)
        } catch {
            throw scheitert(error, glb: glb, vorher: vorherGlb, warDa: warDa)
        }
    }

    /// Eine geholte Datei (`zwischen`) an ihren Platz in der Mappe — **nie erst löschen, dann
    /// verschieben** (G-A0063b Mangel 3): Sie kommt zuerst neben das Ziel (derselbe Ordner, also
    /// dasselbe Laufwerk) und ersetzt es dann in einem Zug. Scheitert ein Schritt, liegt das alte
    /// Ziel unverändert da.
    public static func lege(_ zwischen: URL, nach ziel: URL) throws {
        let fm = FileManager.default
        try fm.createDirectory(at: ziel.deletingLastPathComponent(), withIntermediateDirectories: true)
        guard fm.fileExists(atPath: ziel.path) else {
            try fm.moveItem(at: zwischen, to: ziel)
            return
        }
        let neben = nebendatei(ziel)
        try fm.moveItem(at: zwischen, to: neben)
        do {
            try ersetze(ziel, durch: neben)
        } catch {
            try? fm.removeItem(at: neben)
            throw error
        }
    }

    /// Stellt den Stand vor dem Laden her: die Kopie zurück (sie selbst bleibt liegen), oder ohne
    /// altes Modell keines. `false`, wenn das nicht ging (Mangel 4: nie still) — dann liegt das
    /// neue Modell weiter da.
    @discardableResult
    public static func zurueck(glb: URL, vorher: URL, warDa: Bool) -> Bool {
        let fm = FileManager.default
        guard warDa else {
            guard fm.fileExists(atPath: glb.path) else { return true }
            return (try? fm.removeItem(at: glb)) != nil
        }
        let neben = nebendatei(glb)
        guard (try? fm.copyItem(at: vorher, to: neben)) != nil else { return false }
        do {
            if fm.fileExists(atPath: glb.path) {
                try ersetze(glb, durch: neben)
            } else {
                try fm.moveItem(at: neben, to: glb)
            }
            return true
        } catch {
            try? fm.removeItem(at: neben)
            return false
        }
    }

    /// Nach einem Scheitern: zurückholen und den Fehler weitergeben — kam das alte Modell nicht
    /// zurück, mit dem Satz dazu.
    static func scheitert(_ fehler: Error, glb: URL, vorher: URL, warDa: Bool) -> Error {
        if zurueck(glb: glb, vorher: vorher, warDa: warDa) { return fehler }
        let satz = (fehler as? Mappenfehler)?.satz ?? fehler.localizedDescription
        return Mappenfehler(satz: satz + satzNichtZurueck)
    }

    /// Ersetzt `ziel` durch `neben` in einem Zug (`rename(2)`, im selben Ordner): Es gibt keinen
    /// Augenblick ohne Datei. (`FileManager.replaceItemAt` verliert unter Linux das Ziel.)
    static func ersetze(_ ziel: URL, durch neben: URL) throws {
        let ergebnis = neben.withUnsafeFileSystemRepresentation { von in
            ziel.withUnsafeFileSystemRepresentation { nach in
                guard let von, let nach else { return Int32(-1) }
                return rename(von, nach)
            }
        }
        guard ergebnis == 0 else {
            throw Mappenfehler(satz: "Die Datei «\(ziel.lastPathComponent)» liess sich nicht ersetzen (Fehler \(errno)).")
        }
    }

    /// Eine verborgene Datei neben `ziel`, für den Zug in einem Schritt.
    static func nebendatei(_ ziel: URL) -> URL {
        ziel.deletingLastPathComponent().appendingPathComponent(".\(ziel.lastPathComponent).\(UUID().uuidString).neu")
    }
}

/// Was in `mappe.json` steht, wenn die liegende `modell.glb` nicht dazu passt (A0063b Runde 2,
/// Diagnose vom Mac-Abend 06.11.2026).
///
/// **Befund 1:** In der Mappe «haus-am-hang» war `modell.glb` von Hand ersetzt worden (38 Teile,
/// First 9,1 m); `mappe.json` nannte weiter 30 Teile und 7,1 m, ohne Abdruck. Seit A0063 Runde 2
/// zeigte der Mac dann gar keine Zahlen — richtig, aber ohne Weg zurück ausser «Modell neu holen».
/// **Befund 2:** Eine Mappe von vor dem Abdruck (0.3.73) zeigte «Szene: 0 Bauteile (aus IFC)»,
/// obwohl Datei und Auskunft 35 Teile hatten: `bauteile` ging leer hinaus, die Seite machte 0 daraus.
///
/// Beim Öffnen zieht der Mac darum nach, was sich aus der Datei selbst lesen lässt — Bauteile und
/// Hüllbox aus dem JSON-Kopf, wie `glbbox.knotenboxen` am Heim-PC — und schreibt es mit dem
/// Abdruck in `mappe.json`. **Die Standpunkte nicht:** sie rechnet nur der Heim-PC; die alten
/// gehören zum alten Modell und fallen weg, der Modell-Knoten sagt es.
public enum Modellnachzug {
    /// Wie nah zwei Hüllboxen sein müssen, damit eine Auskunft ohne Abdruck als «dieselbe» gilt (m).
    static let boxtoleranz = 0.01

    /// Der Satz am Modell-Knoten nach dem Nachziehen.
    public static func satzNachgezogen(_ name: String, bauteile: Int, gelaendeGetrennt: Bool = false,
                                       anDerForm: Bool = false) -> String {
        let trennung = !gelaendeGetrennt ? "ohne Geländetrennung"
            : anDerForm ? "das Gelände ist an der Form abgetrennt" : "das Gelände ist nach den Namen abgetrennt"
        return "Die Angaben der Mappe «\(name)» passten nicht zum Modell, das in ihr liegt — Bauteile (\(bauteile)) "
            + "und Hüllbox sind aus der Datei nachgezogen, \(trennung). Standpunkte rechnet der "
            + "Heim-PC erst wieder nach «Andere Datei …»."
    }

    /// Der Satz, wenn der Kamera-Knoten Standpunkte einer nachgezogenen Mappe will: Der Zwilling am
    /// Heim-PC trägt nicht das Modell, das hier liegt — er rechnete sie falsch.
    public static let satzStandpunkteNachgezogen =
        "Das Modell dieser Mappe liegt nur am Mac (von Hand ersetzt); Standpunkte rechnet der Heim-PC "
        + "erst, wenn es über «Andere Datei …» geladen ist."

    /// Die Mappe mit einer Auskunft aus der liegenden Datei — `nil`, wenn nichts zu tun ist (die
    /// Auskunft gehört belegt zur Datei, keine Datei, kein Abdruck) oder die Datei sich nicht lesen
    /// lässt (dann bleibt es bei «Modell neu holen», `fuerDieSeite`).
    ///
    /// `abdruck`: die Summe der liegenden `modell.glb` (`Glbabdruck`), `groesse` ihre Bytes, `kopf`
    /// liefert Kopf und JSON-Block (`Glbauskunft.kopf(von:)`) — nur gelesen, wenn nötig.
    public static func gezogen(_ mappe: Macmappe, glbDa: Bool, abdruck: String?, groesse: Int?,
                               kopf: () -> Data?) -> Macmappe? {
        guard glbDa, let abdruck, !abdruck.isEmpty, let groesse else { return nil }
        var felder = mappe.knoten?.alsObjekt ?? [:]
        guard let warum = Mappenkern.auskunftVeraltet(felder, glbAbdruck: abdruck),
              let datei = kopf().flatMap(Glbauskunft.lies) else { return nil }
        let belegt: JSONWert = .objekt(["art": .text(Mappenkern.abdruckBereiche(groesse: groesse).art),
                                        "groesse_byte": .ganz(groesse), "summe": .text(abdruck)])
        var neu = mappe
        // EINE MAPPE VON VOR DEM ABDRUCK, DEREN DATEI PASST (Befund 2): gleiche Teilzahl und gleiche
        // Box (oder gleiche Grösse) — dann gilt die Auskunft des Heim-PC weiter, mit allen Feldern.
        if warum == "ohne_abdruck", felder["bauteile"]?.alsGanz == datei.bauteile,
           gleich(felder["huellbox_m"], datei.huellbox) || felder["glb_bytes"]?.alsGanz == groesse {
            felder["glb_abdruck"] = belegt
            felder["glb_bytes"] = .ganz(groesse)
            neu.knoten = .objekt(felder)
            return neu
        }
        felder["glb"] = .wahrheit(true)
        felder["bauteile"] = .ganz(datei.bauteile)
        felder["huellbox_m"] = .liste(datei.huellbox.map { .liste($0.map(JSONWert.zahl)) })
        felder["hochachse"] = .text("Y")
        felder["standpunkte"] = .null
        felder["herkunft"] = .text("glb")
        felder["glb_bytes"] = .ganz(groesse)
        felder["glb_abdruck"] = belegt
        felder["grund"] = .text("")
        felder["huellbox_vermerk"] = .text(datei.vermerk)
        felder["glb_stand"] = .objekt(["stand": .text("nachgezogen"),
                                       "satz": .text(satzNachgezogen(mappe.name, bauteile: datei.bauteile,
                                                                     gelaendeGetrennt: datei.abgetrennt,
                                                                     anDerForm: datei.entschiedenDurch == "form"))])
        felder["auskunft_nachgezogen"] = .wahrheit(true)
        neu.knoten = .objekt(felder)
        return neu
    }

    /// Die Antwort an die Knotenansicht (`GET ./mappe`): Gehen die Zahlen leer hinaus
    /// (`auskunft_veraltet`), steht der Grund auch in `glb_stand.satz` — den zeigt der Modell-Knoten
    /// unter «Szene: …». Sonst unverändert.
    public static func fuerDieSeite(_ antwort: JSONWert) -> JSONWert {
        guard antwort["auskunft_veraltet"]?.alsWahrheit == true, var felder = antwort.alsObjekt else { return antwort }
        felder["glb_stand"] = .objekt(["stand": .text("veraltet"), "satz": felder["grund"] ?? .text("")])
        return .objekt(felder)
    }

    /// Der Satz, wenn Standpunkte vom Zwilling für diese Mappe falsch wären — sonst `nil`.
    /// Eine Bestellung hat keine solche Sperre (A0261 Runde 2): sie schickt das Modell vom Mac als Feld
    /// «model» mit, der Heim-PC rechnet also mit diesem.
    public static func standpunkteGesperrt(_ mappe: Macmappe) -> String? {
        mappe.knoten?["auskunft_nachgezogen"]?.alsWahrheit == true ? satzStandpunkteNachgezogen : nil
    }

    static func gleich(_ box: JSONWert?, _ soll: [[Double]]) -> Bool {
        guard let ist = box?.alsListe?.map({ $0.alsListe?.compactMap(\.alsZahl) ?? [] }),
              ist.count == 2, ist.allSatisfy({ $0.count == 3 }) else { return false }
        return zip(ist.joined(), soll.joined()).allSatisfy { abs($0 - $1) <= boxtoleranz }
    }
}

/// Bauteile und Hüllbox aus dem JSON-Kopf einer `.glb` — dieselbe Rechnung wie am Heim-PC
/// (`glbbox.knotenboxen` und `nach_welt`): Mesh-Knoten der aktiven Szene, Elternmatrizen mitgeführt,
/// die acht Ecken einzeln, Welt = (x, −z, y).
///
/// **Die Geländeregel ist dieselbe wie am Heim-PC, soweit sie aus den Namen im JSON-Kopf lesbar ist**
/// (A0267): `maske.ist_gelaende` — die Muster `GELAENDE_MUSTER` ganz, die Wörter `GELAENDE_WOERTER`
/// an den Wortgrenzen. Die Hüllbox beschreibt dann das Haus und nicht das Gelände (Geräteprobe 0.3.75:
/// 60 × 50 m statt 30,5 × 27,7 m). **Trennen die Namen nichts, entscheidet die Form** (A0289,
/// `Gelaendeform`, das Abbild der Zweitmeinung `gelaendeform` am Heim-PC): Die Box macht einen Körper
/// zum Kandidaten (gross im Grundriss, nicht aufragend), Gelände wird er nur mit dem Beweis an seinen
/// Dreiecken (Oberseite geneigt und uneben, nichts darunter gebaut). **Schutz des Hauses geht vor
/// Abtrennen:** Eine ebene, waagrechte Fläche kann Gelände oder Bauteil sein und bleibt in der Hülle.
/// Was die Form nicht entscheiden kann, bleibt die Szenenbox mit dem Vermerk «Gelände nicht
/// abgetrennt» — nie eine leere Box. Beide Seiten prüft eine gemeinsame Probendatei
/// (`tests/daten/glbbox_gelaenderegel.json`), damit sie nicht auseinanderlaufen.
///
/// **Keine Auskunft statt einer zu kleinen Box:** ein Mesh ohne `min`/`max`, Instanzen
/// (`EXT_mesh_gpu_instancing`) oder kein einziger Mesh-Knoten geben `nil`.
public struct Glbauskunft: Equatable, Sendable {
    public let bauteile: Int
    /// Die Box zum Rahmen: die des Bauwerks, wenn das Gelände abgetrennt ist (nach den Namen oder an der
    /// Form), sonst die Szenenbox. `[[xmin, ymin, zmin], [xmax, ymax, zmax]]` in Weltkoordinaten (Meter, Z oben).
    public let huellbox: [[Double]]
    /// Die Box aller Mesh-Knoten (`bbox_szene`).
    public let szenenbox: [[Double]]
    /// Wie viele Mesh-Knoten als Gelände gelten (`n_gelaende`): nach dem Namen oder, wenn die Form
    /// entschieden hat, an der Form.
    public let gelaendeKnoten: Int
    /// `true`, wenn `huellbox` das Bauwerk ohne Gelände beschreibt.
    public let abgetrennt: Bool
    /// Welche Regel entschieden hat, wie `entschieden_durch` am Heim-PC: `"name"`, `"form"` oder `"keine"`.
    public let entschiedenDurch: String
    /// Wie viele Körper an der Form «nicht entscheidbar» blieben (Kandidaten ohne Beweis). Sie zählen
    /// zum Bauwerk und bleiben in der Hülle. Nur gezählt, wenn die Form gefragt wurde.
    public let formUnklar: Int
    /// Je unklarem Körper das Kurzwort des Grundes (`Gelaendeform.Grund`), wie `form_befund.gruende`
    /// am Heim-PC.
    public let formGruende: [String]
    /// Der Vermerk für `mappe.json` (`huellbox_vermerk`).
    public let vermerk: String

    // MARK: Geländeregel (Abbild von `maske.ist_gelaende`)

    /// `maske.GELAENDE_MUSTER`: der ganze Name, kleingeschrieben, gegen jedes Muster (`*`/`?` Platzhalter).
    static let gelaendeMuster = ["ifcsite*", "boden_platte", "gelaende", "gelände", "terrain"]
    /// `maske.GELAENDE_WOERTER`: einzelne Wörter eines Namens.
    static let gelaendeWoerter: Set<String> = ["gelaende", "gelände", "terrain", "site", "toposolid", "gelaendeflaeche"]
    /// `maske._WORTTRENNER`: Leerraum und `_ - . , ; : / \\ ( ) [ ]`.
    static let wortTrenner = Set("_-.,;:/\\()[]")

    /// Gilt `name` als Gelände? Dieselbe Entscheidung wie `maske.ist_gelaende` mit den Vorgabemustern.
    public static func istGelaende(_ name: String) -> Bool {
        let n = name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if gelaendeMuster.contains(where: { passt($0, n) }) { return true }
        let woerter = n.split(whereSeparator: { $0.isWhitespace || wortTrenner.contains($0) }).map(String.init)
        return woerter.contains(where: gelaendeWoerter.contains)
    }

    /// `fnmatchcase` für `*` und `?` (mehr stehen in den Mustern nicht).
    static func passt(_ muster: String, _ text: String) -> Bool {
        let m = Array(muster), t = Array(text)
        func los(_ i: Int, _ j: Int) -> Bool {
            if i == m.count { return j == t.count }
            if m[i] == "*" { return los(i + 1, j) || (j < t.count && los(i, j + 1)) }
            guard j < t.count else { return false }
            return (m[i] == "?" || m[i] == t[j]) && los(i + 1, j + 1)
        }
        return los(0, 0)
    }

    /// Höchstens so gross darf der JSON-Block sein, den der Mac liest.
    static let jsonHoechstens = 256 * 1024 * 1024

    public static func lies(_ daten: Data) -> Glbauskunft? {
        let b = [UInt8](daten.prefix(20))
        guard b.count == 20 else { return nil }
        func u32(_ i: Int) -> Int { Int(b[i]) | Int(b[i + 1]) << 8 | Int(b[i + 2]) << 16 | Int(b[i + 3]) << 24 }
        guard u32(0) == 0x4654_6C67, u32(4) == 2, u32(16) == 0x4E4F_534A else { return nil }
        let laenge = u32(12)
        guard laenge <= jsonHoechstens, daten.count >= 20 + laenge,
              let js = try? JSONWert.lies(daten.subdata(in: daten.startIndex + 20 ..< daten.startIndex + 20 + laenge))
        else { return nil }
        // Der Binärblock hinter dem JSON-Block, wenn `daten` ihn trägt (`kopf(von:)` reicht die ganze
        // Datei als eingeblendeten Speicher): daraus liest die Zweitmeinung die Dreiecke der Kandidaten.
        var binaer: Data?
        if daten.count >= 20 + laenge + 8 {
            let k = [UInt8](daten.subdata(in: daten.startIndex + 20 + laenge ..< daten.startIndex + 20 + laenge + 8))
            let n = Int(k[0]) | Int(k[1]) << 8 | Int(k[2]) << 16 | Int(k[3]) << 24
            let art = Int(k[4]) | Int(k[5]) << 8 | Int(k[6]) << 16 | Int(k[7]) << 24
            let anfang = 20 + laenge + 8
            if art == 0x004E_4942 {
                // Wie am Heim-PC zählt die angekündigte Länge; was über das Dateiende reicht, ist nicht lesbar.
                binaer = daten.subdata(in: daten.startIndex + anfang ..< daten.startIndex + min(anfang + n, daten.count))
            }
        }
        return aus(js, binaer: binaer)
    }

    /// Bis zu dieser Grösse wird die ganze Datei als eingeblendeter Speicher gereicht.
    static let dateiHoechstens = 4 * 1024 * 1024 * 1024

    /// Die `.glb` von der Platte. Gelesen werden der Kopf und der JSON-Block; die Dreiecke dahinter
    /// werden **eingeblendet, nicht geladen**, und nur die Zweitmeinung fasst sie an, nur für ihre
    /// Kandidaten (A0289, Runde 2). Lässt sich die Datei nicht einblenden oder ist sie zu gross,
    /// bleibt es bei Kopf und JSON-Block: Dann sind die Dreiecke «nicht lesbar», und die Form trennt
    /// nichts ab.
    public static func kopf(von datei: URL) -> Data? {
        let groesse = ((try? FileManager.default.attributesOfItem(atPath: datei.path))?[.size] as? NSNumber)?.intValue
        if let groesse, groesse >= 20, groesse <= dateiHoechstens,
           let ganz = try? Data(contentsOf: datei, options: .mappedIfSafe), ganz.count == groesse {
            let b = [UInt8](ganz.prefix(20))
            let laenge = Int(b[12]) | Int(b[13]) << 8 | Int(b[14]) << 16 | Int(b[15]) << 24
            if laenge <= jsonHoechstens, ganz.count >= 20 + laenge { return ganz }
            return nil
        }
        guard let griff = try? FileHandle(forReadingFrom: datei) else { return nil }
        defer { try? griff.close() }
        guard let anfang = try? griff.read(upToCount: 20), anfang.count == 20 else { return nil }
        let b = [UInt8](anfang)
        let laenge = Int(b[12]) | Int(b[13]) << 8 | Int(b[14]) << 16 | Int(b[15]) << 24
        guard laenge <= jsonHoechstens, let block = try? griff.read(upToCount: laenge), block.count == laenge
        else { return nil }
        return anfang + block
    }

    typealias Matrix = [[Double]]
    static let einheit: Matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]

    static func mal(_ a: Matrix, _ b: Matrix) -> Matrix {
        (0 ..< 4).map { r in (0 ..< 4).map { c in (0 ..< 4).reduce(0) { $0 + a[r][$1] * b[$1][c] } } }
    }

    /// Die lokale Matrix aus `matrix` (spaltenweise gespeichert) oder aus T·R·S.
    static func matrix(_ n: JSONWert) -> Matrix {
        if let m = n["matrix"]?.alsListe?.compactMap(\.alsZahl), m.count == 16 {
            return (0 ..< 4).map { r in (0 ..< 4).map { c in m[c * 4 + r] } }
        }
        func vek(_ feld: String, _ vorgabe: [Double]) -> [Double] {
            let v = n[feld]?.alsListe?.compactMap(\.alsZahl) ?? []
            return v.count == vorgabe.count ? v : vorgabe
        }
        let t = vek("translation", [0, 0, 0]), q = vek("rotation", [0, 0, 0, 1]), s = vek("scale", [1, 1, 1])
        let (x, y, z, w) = (q[0], q[1], q[2], q[3])
        let dreh: Matrix = [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
        return (0 ..< 3).map { i in (0 ..< 3).map { j in dreh[i][j] * s[j] } + [t[i]] } + [[0, 0, 0, 1]]
    }

    /// `(lo, hi)` eines Meshes aus seinen POSITION-Accessors, oder `nil`.
    static func grenzen(_ js: JSONWert, mesh: Int) -> ([Double], [Double])? {
        guard let netze = js["meshes"]?.alsListe, netze.indices.contains(mesh) else { return nil }
        var lo = [Double](repeating: .infinity, count: 3), hi = [Double](repeating: -.infinity, count: 3)
        for prim in netze[mesh]["primitives"]?.alsListe ?? [] {
            guard let stelle = prim["attributes"]?["POSITION"]?.alsGanz else { continue }
            guard let zugriffe = js["accessors"]?.alsListe, zugriffe.indices.contains(stelle),
                  let mn = zugriffe[stelle]["min"]?.alsListe?.compactMap(\.alsZahl),
                  let mx = zugriffe[stelle]["max"]?.alsListe?.compactMap(\.alsZahl),
                  mn.count >= 3, mx.count >= 3 else { return nil }
            for i in 0 ..< 3 { lo[i] = min(lo[i], mn[i]); hi[i] = max(hi[i], mx[i]) }
        }
        return lo[0] < .infinity ? (lo, hi) : nil
    }

    static func aus(_ js: JSONWert, binaer: Data? = nil) -> Glbauskunft? {
        let knoten = js["nodes"]?.alsListe ?? []
        let szenen = js["scenes"]?.alsListe ?? []
        let nummer = js["scene"]?.alsGanz ?? 0
        let wurzeln: [Int]
        if szenen.indices.contains(nummer) {
            wurzeln = (szenen[nummer]["nodes"]?.alsListe ?? []).compactMap(\.alsGanz)
        } else {
            let kinder = Set(knoten.flatMap { ($0["children"]?.alsListe ?? []).compactMap(\.alsGanz) })
            wurzeln = knoten.indices.filter { !kinder.contains($0) }
        }
        var eintraege: [(name: String, lo: [Double], hi: [Double])] = []
        // Gleich lang wie `eintraege`: Mesh und Weltmatrix je Körper, für die Dreiecke der Kandidaten.
        var herkunft: [(mesh: Int, welt: Matrix)] = []
        var stapel: [(Int, Matrix)] = wurzeln.reversed().map { ($0, einheit) }
        var gesehen = Set<Int>()
        while let (index, eltern) = stapel.popLast() {
            guard knoten.indices.contains(index), gesehen.insert(index).inserted else { continue }
            let n = knoten[index]
            let welt = mal(eltern, matrix(n))
            if let mesh = n["mesh"]?.alsGanz {
                if n["extensions"]?["EXT_mesh_gpu_instancing"] != nil { return nil }
                guard let (blo, bhi) = grenzen(js, mesh: mesh) else { return nil }
                var elo = [Double](repeating: .infinity, count: 3), ehi = [Double](repeating: -.infinity, count: 3)
                for bx in [blo[0], bhi[0]] { for by in [blo[1], bhi[1]] { for bz in [blo[2], bhi[2]] {
                    for i in 0 ..< 3 {
                        let v = welt[i][0] * bx + welt[i][1] * by + welt[i][2] * bz + welt[i][3]
                        elo[i] = min(elo[i], v); ehi[i] = max(ehi[i], v)
                    }
                } } }
                eintraege.append((n["name"]?.alsText ?? "", elo, ehi))
                herkunft.append((mesh, welt))
            }
            for kind in (n["children"]?.alsListe ?? []).compactMap(\.alsGanz).reversed() {
                stapel.append((kind, welt))
            }
        }
        guard !eintraege.isEmpty else { return nil }
        // Wie am Heim-PC (`GlbError`): eine Box, die keine endliche Zahl ist, gibt keine Auskunft.
        guard eintraege.allSatisfy({ ($0.lo + $0.hi).allSatisfy(\.isFinite) }) else { return nil }
        // glTF (Y oben) → Welt (Z oben): (x, −z, y), wie `glbbox.nach_welt`.
        func huelle(_ teile: [(name: String, lo: [Double], hi: [Double])]) -> [[Double]] {
            var lo = [Double](repeating: .infinity, count: 3), hi = [Double](repeating: -.infinity, count: 3)
            for e in teile { for i in 0 ..< 3 { lo[i] = min(lo[i], e.lo[i]); hi[i] = max(hi[i], e.hi[i]) } }
            return [[lo[0], -hi[2], lo[1]], [hi[0], -lo[2], hi[1]]]
        }
        let szene = huelle(eintraege)
        let bauwerk = eintraege.filter { !istGelaende($0.name) }
        let gelaende = eintraege.count - bauwerk.count
        let nachgezogen = "am Mac aus der Datei nachgezogen"
        // Wie `glbbox.bauwerksbox`: ALLES Gelände nach dem Namen → die Szenenbox (am Heim-PC keine
        // Bauwerksbox, hier nie eine leere). Die Form wird dann nicht gefragt.
        if bauwerk.isEmpty {
            return Glbauskunft(bauteile: eintraege.count, huellbox: szene, szenenbox: szene,
                               gelaendeKnoten: gelaende, abgetrennt: false, entschiedenDurch: "name", formUnklar: 0,
                               formGruende: [],
                               vermerk: "\(nachgezogen) (Szenenbox, Gelände nicht abgetrennt: alle "
                                   + "\(eintraege.count) Teile gelten nach dem Namen als Gelände)")
        }
        let nachNamen = huelle(bauwerk)
        // DIE ZWEITMEINUNG (A0289), an derselben Schwelle wie am Heim-PC: Sie spricht nur, wenn die
        // Namensregel den Grundriss um weniger als 5 % enger gemacht hat (gemessen an der Diagonale).
        func breite(_ box: [[Double]]) -> Double { hypot(box[1][0] - box[0][0], box[1][1] - box[0][1]) }
        let breiteSzene = breite(szene)
        let schrumpfung = breiteSzene > 0 ? 1 - breite(nachNamen) / breiteSzene : 0
        var form = Gelaendeform.Zweitmeinung.schweigt
        if schrumpfung < Gelaendeform.geringeSchrumpfung {
            let quelle = Glbdreiecke(js: js, binaer: binaer)
            form = Gelaendeform.zweitmeinung(
                eintraege.map { Gelaendeform.Koerper(name: $0.name, lo: $0.lo, hi: $0.hi) }, hatteNamen: gelaende > 0,
                oberseite: { quelle.oberseite(mesh: herkunft[$0].mesh, welt: herkunft[$0].welt) })
        }
        let unklar = form.unklar == 0 ? ""
            : " \(form.unklar) grosse flache Teile sind an der Form nicht entscheidbar und bleiben in der "
                + "Hülle (\(Glbauskunft.inWorten(form.gruende)))."
        if form.entscheidet {
            // NACH DER STELLE, NICHT NACH DEM NAMEN: Ein gleichnamiges Geschoss bleibt im Bauwerk.
            let weg = Set(form.gelaende)
            let rest = eintraege.indices.filter { !weg.contains($0) }.map { eintraege[$0] }
            // `entscheidet` heisst: nicht alles ist Gelände. Trotzdem nie eine leere Box.
            if !rest.isEmpty {
                return Glbauskunft(bauteile: eintraege.count, huellbox: huelle(rest), szenenbox: szene,
                                   gelaendeKnoten: weg.count, abgetrennt: true, entschiedenDurch: "form",
                                   formUnklar: form.unklar, formGruende: form.gruende,
                                   vermerk: "\(nachgezogen) (Bauwerksbox, \(weg.count) Gelände-Teile an der Form "
                                       + "abgetrennt: gross im Grundriss, die Oberseite geneigt und uneben)." + unklar)
            }
        }
        if gelaende == 0 {
            return Glbauskunft(bauteile: eintraege.count, huellbox: szene, szenenbox: szene,
                               gelaendeKnoten: 0, abgetrennt: false, entschiedenDurch: "keine",
                               formUnklar: form.unklar, formGruende: form.gruende,
                               vermerk: "\(nachgezogen) (Szenenbox, Gelände nicht abgetrennt)"
                                   + (unklar.isEmpty ? "" : "." + unklar))
        }
        return Glbauskunft(bauteile: eintraege.count, huellbox: nachNamen, szenenbox: szene,
                           gelaendeKnoten: gelaende, abgetrennt: true, entschiedenDurch: "name",
                           formUnklar: form.unklar, formGruende: form.gruende,
                           vermerk: "\(nachgezogen) (Bauwerksbox, \(gelaende) Gelände-Teile "
                               + "nach dem Namen abgetrennt)")
    }

    /// Die Gründe, aus denen Körper «nicht entscheidbar» blieben, in Worten für den Vermerk.
    static func inWorten(_ gruende: [String]) -> String {
        let worte: [String: String] = [
            Gelaendeform.Grund.eben: "eben und waagrecht: Gelände oder Bauteil",
            Gelaendeform.Grund.eineEbene: "eine geneigte Ebene: Hang, Rampe oder Dach",
            Gelaendeform.Grund.nichtLesbar: "Dreiecke nicht lesbar",
            Gelaendeform.Grund.deckung: "keine zusammenhängende Oberseite",
            Gelaendeform.Grund.lagen: "mehrere Lagen übereinander",
            Gelaendeform.Grund.wand: "eine Wand im Inneren",
            Gelaendeform.Grund.sockel: "die Oberseite beginnt über einem Sockel",
            Gelaendeform.Grund.unterbaut: "darunter ist gebaut",
            Gelaendeform.Grund.traegtNicht: "was die Szene überragt, steht nicht darauf",
            Gelaendeform.Grund.zuHoch: "hoch in der Szene: steiler Hang oder frei geformtes Bauwerk",
        ]
        var gesehen = Set<String>(), aus: [String] = []
        for g in gruende where gesehen.insert(g).inserted { aus.append(worte[g] ?? g) }
        return aus.joined(separator: "; ")
    }
}

/// Die Dreiecke eines Meshes aus den Binärdaten einer glb, nur auf Verlangen (A0289, Runde 2): das
/// Abbild von `glbbox.Dreiecksquelle` am Heim-PC.
///
/// Der JSON-Kopf trägt die Hüllboxen, und für die Rahmung genügen sie. Ob die Oberseite eines grossen
/// flachen Körpers eine Geschossdecke oder ein Hang ist, steht nur in seinen Ecken. Gelesen wird darum
/// nur für Kandidaten: aus dem Binärblock der glb oder aus einem `data:`-Puffer im Kopf.
///
/// **Was nicht lesbar ist, wird nicht geraten:** andere Zeichenarten als Dreieckslisten, Ecken, die
/// nicht als 32-Bit-Kommazahlen stehen (gepackte oder quantisierte Netze), dünn besetzte Accessors,
/// fremde Dateien als Puffer. Dann gibt es `nil`, und der Körper bleibt «nicht entscheidbar».
final class Glbdreiecke {
    let js: JSONWert
    let binaer: Data?
    private var puffer: [Int: Data?] = [:]

    init(js: JSONWert, binaer: Data?) {
        self.js = js
        self.binaer = binaer
    }

    private func lies(_ nummer: Int, _ anfang: Int, _ laenge: Int) -> Data? {
        guard let liste = js["buffers"]?.alsListe, liste.indices.contains(nummer), anfang >= 0, laenge >= 0
        else { return nil }
        guard let uri = liste[nummer]["uri"] else {
            guard nummer == 0, let binaer, anfang + laenge <= binaer.count else { return nil }
            return binaer.subdata(in: binaer.startIndex + anfang ..< binaer.startIndex + anfang + laenge)
        }
        if puffer[nummer] == nil {
            var daten: Data?
            if let text = uri.alsText, text.hasPrefix("data:"), let trenner = text.range(of: ";base64,") {
                daten = Data(base64Encoded: String(text[trenner.upperBound...]))
            }
            puffer[nummer] = .some(daten)
        }
        guard let daten = puffer[nummer] ?? nil, anfang + laenge <= daten.count else { return nil }
        return daten.subdata(in: daten.startIndex + anfang ..< daten.startIndex + anfang + laenge)
    }

    /// Rohbytes eines Accessors mit `breite` Byte je Eintrag: `(roh, schritt, anzahl)`.
    private func accessor(_ stelle: Int, _ breite: Int) -> (roh: [UInt8], schritt: Int, anzahl: Int)? {
        guard let zugriffe = js["accessors"]?.alsListe, zugriffe.indices.contains(stelle) else { return nil }
        let acc = zugriffe[stelle]
        guard acc["sparse"] == nil, let nr = acc["bufferView"]?.alsGanz,
              let sichten = js["bufferViews"]?.alsListe, sichten.indices.contains(nr),
              let anzahl = acc["count"]?.alsGanz else { return nil }
        let sicht = sichten[nr]
        guard sicht["extensions"] == nil, anzahl >= 1 else { return nil }
        let schritt = (sicht["byteStride"]?.alsGanz).flatMap { $0 == 0 ? nil : $0 } ?? breite
        let versatz = acc["byteOffset"]?.alsGanz ?? 0
        let (produkt, zuGross) = schritt.multipliedReportingOverflow(by: anzahl - 1)
        guard !zuGross, let lang = sicht["byteLength"]?.alsGanz, let pufferNr = sicht["buffer"]?.alsGanz else { return nil }
        let laenge = produkt + breite
        guard schritt >= breite, versatz >= 0, versatz + laenge <= lang,
              let roh = lies(pufferNr, (sicht["byteOffset"]?.alsGanz ?? 0) + versatz, laenge) else { return nil }
        return ([UInt8](roh), schritt, anzahl)
    }

    /// Die Ecken eines POSITION-Accessors in Weltkoordinaten, je Ecke drei Zahlen hintereinander.
    private func ecken(_ stelle: Int, _ welt: Glbauskunft.Matrix) -> [Double]? {
        guard let zugriffe = js["accessors"]?.alsListe, zugriffe.indices.contains(stelle),
              zugriffe[stelle]["componentType"]?.alsGanz == 5126, zugriffe[stelle]["type"]?.alsText == "VEC3",
              let (roh, schritt, anzahl) = accessor(stelle, 12) else { return nil }
        var aus = [Double](repeating: 0, count: anzahl * 3)
        func zahl(_ o: Int) -> Double {
            Double(Float(bitPattern: UInt32(roh[o]) | UInt32(roh[o + 1]) << 8 | UInt32(roh[o + 2]) << 16 | UInt32(roh[o + 3]) << 24))
        }
        for i in 0 ..< anzahl {
            let o = i * schritt
            let x = zahl(o), y = zahl(o + 4), z = zahl(o + 8)
            aus[i * 3] = welt[0][0] * x + welt[0][1] * y + welt[0][2] * z + welt[0][3]
            aus[i * 3 + 1] = welt[1][0] * x + welt[1][1] * y + welt[1][2] * z + welt[1][3]
            aus[i * 3 + 2] = welt[2][0] * x + welt[2][1] * y + welt[2][2] * z + welt[2][3]
        }
        return aus
    }

    /// Die Indexliste eines Primitivs; `nil`, wenn sie nicht lesbar ist oder über die Ecken hinausweist.
    private func folge(_ stelle: Int, _ nEcken: Int) -> [Int]? {
        guard let zugriffe = js["accessors"]?.alsListe, zugriffe.indices.contains(stelle),
              zugriffe[stelle]["type"]?.alsText == "SCALAR",
              let art = zugriffe[stelle]["componentType"]?.alsGanz,
              let breite = [5121: 1, 5123: 2, 5125: 4][art],
              let (roh, schritt, anzahl) = accessor(stelle, breite) else { return nil }
        var aus = [Int](repeating: 0, count: anzahl)
        for i in 0 ..< anzahl {
            let o = i * schritt
            var v = 0
            for k in 0 ..< breite { v |= Int(roh[o + k]) << (8 * k) }
            if v >= nEcken { return nil }
            aus[i] = v
        }
        return aus
    }

    /// Alle Dreiecke eines Meshes in Weltkoordinaten, neun Zahlen je Dreieck, oder `nil`.
    func dreiecke(mesh: Int, welt: Glbauskunft.Matrix) -> [Double]? {
        guard let netze = js["meshes"]?.alsListe, netze.indices.contains(mesh) else { return nil }
        var aus: [Double] = []
        for prim in netze[mesh]["primitives"]?.alsListe ?? [] {
            guard prim.alsObjekt != nil else { return nil }
            guard let stelle = prim["attributes"]?["POSITION"]?.alsGanz else { continue }
            if let art = prim["mode"], art.alsGanz != 4 { return nil }
            if prim["extensions"] != nil { return nil }
            guard let e = ecken(stelle, welt) else { return nil }
            let n = e.count / 3
            var f: [Int]
            if let index = prim["indices"], index != .null {
                guard let nr = index.alsGanz, let gelesen = folge(nr, n) else { return nil }
                f = gelesen
            } else {
                f = Array(0 ..< n)
            }
            if aus.count / 9 + f.count / 3 > Gelaendeform.dreieckeHoechstens { return nil }
            var i = 0
            while i + 2 < f.count {
                for k in 0 ..< 3 {
                    let o = f[i + k] * 3
                    aus.append(e[o]); aus.append(e[o + 1]); aus.append(e[o + 2])
                }
                i += 3
            }
        }
        return aus.isEmpty ? nil : aus
    }

    /// `Gelaendeform.oberseite` für einen Mesh-Knoten, oder `nil`, wenn seine Dreiecke nicht lesbar sind.
    func oberseite(mesh: Int, welt: Glbauskunft.Matrix) -> Gelaendeform.Oberseite? {
        guard let d = dreiecke(mesh: mesh, welt: welt) else { return nil }
        // Ecken jenseits jeder Baugrösse (oder nicht endlich) laufen in der Rechnung über: nicht lesbar.
        guard d.allSatisfy({ abs($0) <= Gelaendeform.eckeHoechstens }) else { return nil }
        let det = welt[0][0] * (welt[1][1] * welt[2][2] - welt[1][2] * welt[2][1])
            - welt[0][1] * (welt[1][0] * welt[2][2] - welt[1][2] * welt[2][0])
            + welt[0][2] * (welt[1][0] * welt[2][1] - welt[1][1] * welt[2][0])
        return Gelaendeform.oberseite(dreiecke: d, gespiegelt: det < 0)
    }
}
