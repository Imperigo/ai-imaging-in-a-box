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
    public static func satzNachgezogen(_ name: String, bauteile: Int, gelaendeGetrennt: Bool = false) -> String {
        let trennung = gelaendeGetrennt ? "das Gelände ist nach den Namen abgetrennt" : "ohne Geländetrennung"
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
                                                                     gelaendeGetrennt: datei.abgetrennt))])
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
/// 60 × 50 m statt 30,5 × 27,7 m). **Was nur die Form entscheiden kann** (`gelaendeform`, die
/// Zweitmeinung, wenn die Namen nichts trennen), liest der Mac nicht: dann bleibt es bei der Szenenbox
/// mit dem Vermerk «Gelände nicht abgetrennt» — nie eine leere Box. Beide Seiten prüft eine gemeinsame
/// Probendatei (`tests/daten/glbbox_gelaenderegel.json`), damit sie nicht auseinanderlaufen.
///
/// **Keine Auskunft statt einer zu kleinen Box:** ein Mesh ohne `min`/`max`, Instanzen
/// (`EXT_mesh_gpu_instancing`) oder kein einziger Mesh-Knoten geben `nil`.
public struct Glbauskunft: Equatable, Sendable {
    public let bauteile: Int
    /// Die Box zum Rahmen: die des Bauwerks, wenn das Gelände nach den Namen abgetrennt ist, sonst die
    /// Szenenbox. `[[xmin, ymin, zmin], [xmax, ymax, zmax]]` in Weltkoordinaten (Meter, Z oben).
    public let huellbox: [[Double]]
    /// Die Box aller Mesh-Knoten (`bbox_szene`).
    public let szenenbox: [[Double]]
    /// Wie viele Mesh-Knoten nach dem Namen als Gelände gelten (`n_gelaende`).
    public let gelaendeKnoten: Int
    /// `true`, wenn `huellbox` das Bauwerk ohne Gelände beschreibt.
    public let abgetrennt: Bool
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
        return aus(js)
    }

    /// Kopf und JSON-Block einer `.glb` von der Platte — die Dreiecke dahinter werden nie gelesen.
    public static func kopf(von datei: URL) -> Data? {
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

    static func aus(_ js: JSONWert) -> Glbauskunft? {
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
            }
            for kind in (n["children"]?.alsListe ?? []).compactMap(\.alsGanz).reversed() {
                stapel.append((kind, welt))
            }
        }
        guard !eintraege.isEmpty else { return nil }
        // glTF (Y oben) → Welt (Z oben): (x, −z, y), wie `glbbox.nach_welt`.
        func huelle(_ teile: [(name: String, lo: [Double], hi: [Double])]) -> [[Double]] {
            var lo = [Double](repeating: .infinity, count: 3), hi = [Double](repeating: -.infinity, count: 3)
            for e in teile { for i in 0 ..< 3 { lo[i] = min(lo[i], e.lo[i]); hi[i] = max(hi[i], e.hi[i]) } }
            return [[lo[0], -hi[2], lo[1]], [hi[0], -lo[2], hi[1]]]
        }
        let szene = huelle(eintraege)
        let bauwerk = eintraege.filter { !istGelaende($0.name) }
        let gelaende = eintraege.count - bauwerk.count
        let ohne = "am Mac aus der Datei nachgezogen (Szenenbox, Gelände nicht abgetrennt)"
        // Wie `glbbox.bauwerksbox`: kein Gelände erkannt → Szenenbox; ALLES Gelände → ebenfalls die
        // Szenenbox (am Heim-PC keine Bauwerksbox, hier nie eine leere).
        if gelaende == 0 || bauwerk.isEmpty {
            let grund = gelaende == 0 ? ohne
                : "am Mac aus der Datei nachgezogen (Szenenbox, Gelände nicht abgetrennt: alle "
                    + "\(eintraege.count) Teile gelten nach dem Namen als Gelände)"
            return Glbauskunft(bauteile: eintraege.count, huellbox: szene, szenenbox: szene,
                               gelaendeKnoten: gelaende, abgetrennt: false, vermerk: grund)
        }
        return Glbauskunft(bauteile: eintraege.count, huellbox: huelle(bauwerk), szenenbox: szene,
                           gelaendeKnoten: gelaende, abgetrennt: true,
                           vermerk: "am Mac aus der Datei nachgezogen (Bauwerksbox, \(gelaende) Gelände-Teile "
                               + "nach dem Namen abgetrennt)")
    }
}
