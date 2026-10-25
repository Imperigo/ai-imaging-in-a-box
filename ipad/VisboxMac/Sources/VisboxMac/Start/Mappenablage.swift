import Foundation
import VisboxKern

/// Die Mappen **am Mac** («Visbox eigenständig», Schritt 3, 21.10.2026; Entscheide 103–103c,
/// Blatt 36 «Mappen am Mac»).
///
/// Liegt unter `~/<Marke>-Mappen/<Name>/` (Aufbau in `Kern/Macmappe.swift`). Hier geschieht nur,
/// was die Platte und die Leitung braucht: auflisten, anlegen, öffnen, die Beispielmappe einrichten
/// und eine Mappe vom Heim-PC holen. Was erlaubt ist und wie ein Weg heisst, sagt der Kern
/// (`Mappenkern`, `Mappenpaket`, `Mappenliste` — mit Proben).
///
/// **Rückwärts:** Ohne offene Mappe (`offen == nil`) bleibt alles wie bis 0.3.14 — die
/// Knotenansicht liest die Mappe am Heim-PC (`Knotenquelle`).
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
@MainActor
final class Mappenablage: ObservableObject {
    static let gemeinsam = Mappenablage()

    @Published private(set) var offen: String?
    @Published private(set) var amMac: [Mappenzeile] = []
    @Published private(set) var amHeim: [Heimmappe] = []
    /// Was gerade geholt wird, als Satz («Holt «Hof» … 3 von 7 Dateien»), und wie weit (0…1).
    @Published private(set) var holtSatz: String?
    @Published private(set) var holtAnteil: Double = 0
    /// Ein Satz, wenn etwas nicht ging (Heim-PC nicht erreicht, Platte voll …).
    @Published var satz: String?

    private init() {
        offen = Mappengedaechtnis.offen
        if let o = offen, Mappenablage.lies(Mappenablage.ordner(o)) == nil { offen = nil }
    }

    // ================================================================= Ordner

    nonisolated static var wurzel: URL {
        FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent(Mappenkern.wurzelname, isDirectory: true)
    }

    nonisolated static func ordner(_ name: String) -> URL {
        wurzel.appendingPathComponent(name, isDirectory: true)
    }

    /// Der Ordner der offenen Mappe — `nil` ohne.
    var offenerOrdner: URL? { offen.map(Mappenablage.ordner) }

    nonisolated static func lies(_ ordner: URL) -> Macmappe? {
        guard let daten = try? Data(contentsOf: ordner.appendingPathComponent(Mappenkern.mappendatei))
        else { return nil }
        return Macmappe.lies(daten)
    }

    /// Schreibt `mappe.json` über eine Zwischendatei — eine halb geschriebene Mappe gibt es nicht.
    nonisolated static func schreibe(_ mappe: Macmappe, in ordner: URL) throws {
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
        try mappe.daten().write(to: ordner.appendingPathComponent(Mappenkern.mappendatei), options: .atomic)
    }

    /// Eine Datei in die Mappe legen (atomar), mit Unterordnern.
    nonisolated static func lege(_ daten: Data, weg: String, in ordner: URL) throws {
        let ziel = ordner.appendingPathComponent(weg)
        try FileManager.default.createDirectory(at: ziel.deletingLastPathComponent(),
                                                withIntermediateDirectories: true)
        try daten.write(to: ziel, options: .atomic)
    }

    // ================================================================= Liste

    func ladeListe() {
        richteBeispielEin()
        let fm = FileManager.default
        let namen = (try? fm.contentsOfDirectory(atPath: Mappenablage.wurzel.path)) ?? []
        let mappen = namen.filter { !$0.hasPrefix(".") }.compactMap { name -> (String, Macmappe)? in
            Mappenablage.lies(Mappenablage.ordner(name)).map { (name, $0) }
        }
        amMac = Mappenliste.amMac(mappen.map { (ordner: $0.0, mappe: $0.1) }, offen: offen, heute: Date())
        amHeim = Mappenliste.nochAmHeim(amHeimRoh, amMac: mappen.map(\.1))
    }

    private var amHeimRoh: [Heimmappe] = []

    // ================================================================= öffnen, anlegen

    func oeffne(_ ordnername: String?) {
        offen = ordnername
        Mappengedaechtnis.offen = ordnername
        ladeListe()
    }

    /// «Neue Mappe»: ein leerer Ordner mit `mappe.json`, danach offen.
    func legeAn(_ wunsch: String) {
        guard let roh = Mappenkern.ordnername(fuer: wunsch) else {
            satz = "Bitte einen Namen mit Buchstaben oder Ziffern."
            return
        }
        let belegt = Set((try? FileManager.default.contentsOfDirectory(atPath: Mappenablage.wurzel.path)) ?? [])
        let name = Mappenkern.freierName(roh, belegt: belegt)
        do {
            try Mappenablage.schreibe(Macmappe(name: wunsch.trimmingCharacters(in: .whitespaces),
                                               herkunft: .angelegt, angelegt: Mappenliste.jetzt()),
                                      in: Mappenablage.ordner(name))
            satz = nil
            oeffne(name)
        } catch {
            satz = "Die Mappe liess sich nicht anlegen: \(error.localizedDescription)"
        }
    }

    /// Die Beispielmappe (Entscheid 103b: eine gewöhnliche Mappe) — einmal aus dem Bündel.
    private func richteBeispielEin() {
        let name = "Beispielmappe"
        let ziel = Mappenablage.ordner(name)
        guard Mappenablage.lies(ziel) == nil,
              let quelle = Bundle.main.resourceURL?.appendingPathComponent(name, isDirectory: true),
              let dateien = try? FileManager.default.contentsOfDirectory(atPath: quelle.path) else { return }
        do {
            for datei in dateien where Mappenkern.sichererWeg(datei) != nil {
                let daten = try Data(contentsOf: quelle.appendingPathComponent(datei))
                try Mappenablage.lege(daten, weg: Mappenkern.heimordner + "/" + datei, in: ziel)
            }
            try Mappenablage.schreibe(Macmappe(name: name, herkunft: .mitgeliefert,
                                               angelegt: Mappenliste.jetzt()), in: ziel)
        } catch {
            satz = "Die Beispielmappe liess sich nicht einrichten: \(error.localizedDescription)"
        }
    }

    // ================================================================= vom Heim-PC

    /// «Noch am Heim-PC»: die Liste von dort (`GET /knoten/mappen`). Ohne Heim-PC leer, mit Satz.
    func frageHeim(basis: URL?, anmeldung: Anmeldung?) async {
        guard let basis, let adresse = Mappenpaket.listeAdresse(basis: basis) else {
            amHeimRoh = []
            ladeListe()
            return
        }
        do {
            let daten = try await Mappenholer.hole(adresse, anmeldung: anmeldung)
            guard let liste = Heimmappe.liste(daten) else {
                satz = "Die Liste der Mappen am Heim-PC war nicht lesbar."
                return
            }
            amHeimRoh = liste
            satz = nil
        } catch {
            amHeimRoh = []
            satz = "Die Mappen am Heim-PC sind gerade nicht erreichbar: " + Mappenholer.satz(error)
        }
        ladeListe()
    }

    /// «An den Mac holen»: die ganze Mappe in einen neuen Ordner am Mac, danach offen. Holt eine
    /// abgebrochene Mappe weiter (nur, was fehlt).
    @discardableResult
    func hole(_ heim: Heimmappe, basis: URL?, anmeldung: Anmeldung?) async -> Bool {
        guard let basis else {
            satz = Knotenwege.satzOhneHeim
            return false
        }
        // SCHON EINMAL ANGEFANGEN? Dann in denselben Ordner (derselbe Zwilling).
        let namen = (try? FileManager.default.contentsOfDirectory(atPath: Mappenablage.wurzel.path)) ?? []
        let bestehend = namen.first { Mappenablage.lies(Mappenablage.ordner($0))?.heimMappe == heim.mappe }
        let ordnername = bestehend ?? Mappenkern.freierName(
            Mappenkern.ordnername(fuer: heim.name) ?? heim.mappe, belegt: Set(namen))
        let ordner = Mappenablage.ordner(ordnername)
        do {
            let paket = try await holePaket(heim.mappe, basis: basis, anmeldung: anmeldung)
            var mappe = Mappenablage.lies(ordner)
                ?? Macmappe(name: heim.name, herkunft: .heim, angelegt: Mappenliste.jetzt(), heimMappe: heim.mappe)
            mappe.knoten = paket.knotenFuerMappe
            mappe.heimMappe = heim.mappe
            try Mappenablage.schreibe(mappe, in: ordner)
            // DER GRAPH NUR, WENN AM MAC NOCH KEINER LIEGT: Was am Mac gesichert ist, gilt.
            let graphweg = ordner.appendingPathComponent(Mappenkern.graphdatei)
            if !FileManager.default.fileExists(atPath: graphweg.path), let graph = paket.graphDatei {
                try Mappenablage.lege(graph, weg: Mappenkern.graphdatei, in: ordner)
            }
            try await holeDateien(paket.holplan(vorhanden: Mappenablage.groessen(in: ordner)),
                                  von: heim.mappe, titel: heim.name, in: ordner, basis: basis,
                                  anmeldung: anmeldung)
            holtSatz = nil
            satz = nil
            oeffne(ordnername)
            return true
        } catch {
            holtSatz = nil
            satz = "«\(heim.name)» kam nicht ganz an den Mac: " + Mappenholer.satz(error)
                + " Was da ist, bleibt; noch einmal holen holt nur, was fehlt."
            ladeListe()
            return false
        }
    }

    /// Das Modell vor dem letzten «Andere Datei …» — eine Kopie, falls das neue nicht taugt.
    nonisolated static let modellVorher = "modell.vorher.glb"

    /// Nach «Datei laden …» (Wirt: `POST ./mappe-holen`): das Modell der neuen Mappe am Heim-PC
    /// in **die Mappe am Mac, aus der geladen wurde** (`ordner`, von der `Knotenquelle`); sie nennt
    /// danach diese als Zwilling — dann steht sie nicht mehr unter «Noch am Heim-PC».
    ///
    /// Befund N1 (Mac-Demolauf «Haus am Hang», 22.10.2026): Bis dahin nahm sie die Mappe, die hier
    /// gerade offen hiess, und kehrte **still** zurück, wenn keine lesbar war. `mappe.json` wird
    /// jetzt erst nach dem Holen frisch gelesen: Was in der Zwischenzeit dazukam (ein Auftrag, eine
    /// Skizze vom iPad), bleibt stehen.
    func holeModell(von kennung: String, in ordner: URL, basis: URL?, anmeldung: Anmeldung?) async throws {
        guard let vorher = Mappenablage.lies(ordner) else {
            throw Mappenfehler(satz: "Die Mappe am Mac ist nicht mehr lesbar — unter «Mappen …» eine andere öffnen.")
        }
        guard let basis else { throw URLError(.cannotConnectToHost) }
        let paket = try await holePaket(kennung, basis: basis, anmeldung: anmeldung)
        // BEFUND «ANDERE DATEI» (0.3.67): Ohne Modell im Paket gibt es nichts zu ersetzen — ein Satz,
        // kein stilles «fertig». Das alte Modell bleibt als `modell.vorher.glb` liegen.
        let plan = paket.holplan(vorhanden: [:], nurModell: true)
        guard let schritt = plan.first else {
            throw Mappenfehler(satz: "Die Mappe «\(kennung)» am Heim-PC hat kein Modell zum Holen.")
        }
        let glb = ordner.appendingPathComponent(Mappenkern.modelldatei)
        let fm = FileManager.default
        if fm.fileExists(atPath: glb.path) {
            let vorherGlb = ordner.appendingPathComponent(Mappenablage.modellVorher)
            try? fm.removeItem(at: vorherGlb)
            try fm.copyItem(at: glb, to: vorherGlb)
        }
        try await holeDateien(plan, von: kennung, titel: vorher.name, in: ordner, basis: basis,
                              anmeldung: anmeldung)
        // ERST WENN DAS NEUE MODELL GANZ DA LIEGT, nennt `mappe.json` den neuen Stand.
        let groesse = (try? fm.attributesOfItem(atPath: glb.path))?[.size] as? Int
        guard groesse == schritt.bytes else {
            throw Mappenfehler(satz: "Das neue Modell kam nicht ganz an den Mac (\(groesse ?? 0) von \(schritt.bytes) Bytes).")
        }
        var mappe = Mappenablage.lies(ordner) ?? vorher
        mappe.knoten = paket.knotenFuerMappe
        mappe.heimMappe = kennung
        try Mappenablage.schreibe(mappe, in: ordner)
        holtSatz = nil
        ladeListe()
    }

    private func holePaket(_ kennung: String, basis: URL, anmeldung: Anmeldung?) async throws -> Mappenpaket {
        guard let adresse = Mappenpaket.paketAdresse(basis: basis, mappe: kennung) else {
            throw URLError(.badURL)
        }
        guard let paket = Mappenpaket.lies(try await Mappenholer.hole(adresse, anmeldung: anmeldung)) else {
            throw URLError(.cannotParseResponse)
        }
        return paket
    }

    private func holeDateien(_ plan: [Holschritt], von kennung: String, titel: String, in ordner: URL,
                             basis: URL, anmeldung: Anmeldung?) async throws {
        let gesamt = max(1, plan.count)
        for (i, schritt) in plan.enumerated() {
            holtSatz = "Holt «\(titel)» an den Mac … \(i + 1) von \(plan.count) Dateien"
            holtAnteil = Double(i) / Double(gesamt)
            guard let adresse = Mappenpaket.dateiAdresse(basis: basis, mappe: kennung, weg: schritt.weg) else {
                throw URLError(.badURL)
            }
            try await Mappenholer.lade(adresse, anmeldung: anmeldung,
                                       nach: ordner.appendingPathComponent(schritt.ziel))
        }
        holtAnteil = 1
    }

    /// Die Grössen der Dateien in der Mappe, nach ihrem Weg — für «nur, was fehlt».
    nonisolated static func groessen(in ordner: URL) -> [String: Int] {
        var aus: [String: Int] = [:]
        let basis = ordner.standardizedFileURL.path + "/"
        guard let gang = FileManager.default.enumerator(at: ordner, includingPropertiesForKeys: [.fileSizeKey])
        else { return aus }
        for case let datei as URL in gang {
            let pfad = datei.standardizedFileURL.path
            guard pfad.hasPrefix(basis),
                  let groesse = try? datei.resourceValues(forKeys: [.fileSizeKey]).fileSize else { continue }
            aus[String(pfad.dropFirst(basis.count))] = groesse
        }
        return aus
    }
}

/// Die Leitung zum Heim-PC für das Holen — dieselben Regeln wie jede Anfrage der App: flüchtig,
/// kein Proxy, angeheftetes Zertifikat, Anmeldung und `X-Geraet: mac` aus dem Kern.
enum Mappenholer {
    static let sitzung: URLSession = {
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = Knotenwege.wartezeitLang
        art.timeoutIntervalForResource = 60 * 60
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpCookieStorage = nil
        art.httpShouldSetCookies = false
        art.waitsForConnectivity = false
        art.connectionProxyDictionary = [:]
        return URLSession(configuration: art, delegate: Heimvertrauenslotse.gemeinsam, delegateQueue: nil)
    }()

    /// Ein Satz: der des Heim-PC, wenn er einen sagte, sonst der der Leitung.
    static func satz(_ fehler: Error) -> String {
        (fehler as? Mappenfehler)?.satz ?? Heimstrecke.satz(fehler)
    }

    static func anfrage(_ adresse: URL, anmeldung: Anmeldung?, methode: String = "GET") -> URLRequest {
        var auftrag = URLRequest(url: adresse)
        auftrag.httpMethod = methode
        for k in Knotenwege.koepfeFuerHeim(seite: [], anmeldung: anmeldung) {
            auftrag.setValue(k.wert, forHTTPHeaderField: k.name)
        }
        return auftrag
    }

    /// Eine kleine Antwort ganz (Liste, Paket, Laufzettel). Ein Status ausser 200 ist ein Fehler
    /// mit dem Satz des Heim-PC.
    static func hole(_ adresse: URL, anmeldung: Anmeldung?) async throws -> Data {
        let (daten, antwort) = try await sitzung.data(for: anfrage(adresse, anmeldung: anmeldung))
        try pruefe(antwort, daten)
        return daten
    }

    /// Eine Datei in die Mappe — über eine Zwischendatei, erst danach an ihren Platz.
    static func lade(_ adresse: URL, anmeldung: Anmeldung?, nach ziel: URL) async throws {
        let (zwischen, antwort) = try await sitzung.download(for: anfrage(adresse, anmeldung: anmeldung))
        defer { try? FileManager.default.removeItem(at: zwischen) }
        try pruefe(antwort, nil)
        let fm = FileManager.default
        try fm.createDirectory(at: ziel.deletingLastPathComponent(), withIntermediateDirectories: true)
        if fm.fileExists(atPath: ziel.path) { try fm.removeItem(at: ziel) }
        try fm.moveItem(at: zwischen, to: ziel)
    }

    private static func pruefe(_ antwort: URLResponse, _ daten: Data?) throws {
        guard let http = antwort as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard http.statusCode == 200 else {
            let satz = daten.flatMap { try? JSONWert.lies($0) }?["fehler"]?.alsText
            throw Mappenfehler(satz: satz ?? "Der Heim-PC antwortet mit \(http.statusCode).")
        }
    }
}

/// Ein Fehler mit dem Satz des Heim-PC — `Heimstrecke.satz` gibt ihn wörtlich weiter.
struct Mappenfehler: LocalizedError {
    let satz: String
    var errorDescription: String? { satz }
}
