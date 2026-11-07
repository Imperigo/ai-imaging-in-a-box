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

    /// Der Satz, wenn in dieselbe Mappe schon ein Modell geholt wird.
    public static let satzLaeuftSchon = ""

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
        summe: @MainActor () -> String?
    ) async throws {
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
        try await holeDateien(plan, vorher.name)
        // ERST WENN DAS NEUE MODELL GANZ DA LIEGT, nennt `mappe.json` den neuen Stand.
        let groesse = (try? fm.attributesOfItem(atPath: glb.path))?[.size] as? Int
        guard groesse == schritt.bytes else {
            zurueck(glb: glb, vorher: vorherGlb, warDa: warDa)
            throw Mappenfehler(satz: "Das neue Modell kam nicht ganz an den Mac (\(groesse ?? 0) von \(schritt.bytes) Bytes).")
        }
        if let abweichung = abweichung(summe: summe(), knoten: paket.knoten) {
            zurueck(glb: glb, vorher: vorherGlb, warDa: warDa)
            throw Mappenfehler(satz: abweichung)
        }
        var mappe = Mappenablage.lies(ordner) ?? vorher
        mappe.knoten = paket.knotenFuerMappe
        mappe.heimMappe = kennung
        do {
            try Mappenablage.schreibe(mappe, in: ordner)
        } catch {
            zurueck(glb: glb, vorher: vorherGlb, warDa: warDa)
            throw error
        }
    }

    /// Eine geholte Datei (`zwischen`) an ihren Platz in der Mappe.
    public static func lege(_ zwischen: URL, nach ziel: URL) throws {
        let fm = FileManager.default
        try fm.createDirectory(at: ziel.deletingLastPathComponent(), withIntermediateDirectories: true)
        if fm.fileExists(atPath: ziel.path) { try fm.removeItem(at: ziel) }
        try fm.moveItem(at: zwischen, to: ziel)
    }

    /// Stellt den Stand vor dem Laden her: die Kopie zurück, oder ohne altes Modell keines.
    @discardableResult
    public static func zurueck(glb: URL, vorher: URL, warDa: Bool) -> Bool {
        let fm = FileManager.default
        try? fm.removeItem(at: glb)
        if warDa { try? fm.copyItem(at: vorher, to: glb) }
        return true
    }
}

/// Was in `mappe.json` steht, wenn die liegende `modell.glb` nicht dazu passt (A0063b Runde 2).
public enum Modellnachzug {
    /// Die Mappe mit einer Auskunft aus der liegenden Datei — `nil`, wenn nichts zu tun ist.
    public static func gezogen(_ mappe: Macmappe, glbDa: Bool, abdruck: String?, groesse: Int?,
                               kopf: () -> Data?) -> Macmappe? {
        nil
    }

    /// Die Antwort an die Knotenansicht, mit dem Satz für den Modell-Knoten.
    public static func fuerDieSeite(_ antwort: JSONWert) -> JSONWert { antwort }
}

/// Bauteile und Hüllbox aus dem JSON-Kopf einer `.glb`.
public struct Glbauskunft: Equatable, Sendable {
    public let bauteile: Int
    public let huellbox: [[Double]]

    public static func lies(_ daten: Data) -> Glbauskunft? { nil }

    /// Kopf und JSON-Block einer `.glb` von der Platte.
    public static func kopf(von datei: URL) -> Data? { nil }
}
