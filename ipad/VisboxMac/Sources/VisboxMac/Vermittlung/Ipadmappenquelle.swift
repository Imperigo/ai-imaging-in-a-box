import Foundation
import VisboxKern

/// Die Mappe am Mac **für das iPad** («Visbox eigenständig», Schritt 4; Entscheide 103a/118).
///
/// Ist am Mac eine Mappe offen, beantwortet der Mac die Mappenwege des iPad selbst — dieselbe
/// Rolle wie `Knotenquelle` für die Knotenansicht. **Was** am Mac bleibt und was die Antwort
/// ist, entscheidet der Kern (`Ipadmappenwege`, `Macmappensicht`, `Macskizzen`, mit Proben
/// unter Linux); hier wird nur gelesen und geschrieben.
///
/// Gerufen nur für Anfragen, die die Tür des Mac schon durchgelassen hat und die auf der
/// Positivliste stehen (`Vermittlungsdienst.bearbeite`): Wer hier ankommt, ist das gekoppelte
/// iPad, über die verschlüsselte Leitung.
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026)* — hier nicht übersetzt.
enum Ipadmappenquelle {

    /// Die Antwort aus der Mappe — `nil` heisst: **an den Heim-PC** (der Laufstand).
    static func antwort(_ ziel: Ipadmappenziel, _ anfrage: RoheAnfrage, ordner: URL) -> Leitungsantwort? {
        guard let mappe = Mappenablage.lies(ordner) else {
            return .fehler("Die Mappe am Mac ist nicht mehr lesbar — am Mac unter «Mappen …» eine "
                           + "andere öffnen.", status: 404)
        }
        switch ziel {
        case .projekt:
            let (sicht, _) = sicht(mappe, ordner: ordner)
            return .json(sicht, koepfe: [Kopfzeile("Cache-Control", "no-store")])
        case .bild(let name):
            let (_, erlaubt) = sicht(mappe, ordner: ordner)
            guard let weg = Macmappensicht.bildweg(name, erlaubt: erlaubt),
                  let daten = lies(weg, in: ordner) else {
                return .fehler("Dieses Bild gibt es in der Mappe am Mac nicht: \(name)", status: 404)
            }
            return Leitungsantwort(status: 200,
                                   koepfe: [Kopfzeile("Content-Type", Macmappensicht.inhaltstyp(weg)),
                                            Kopfzeile("Cache-Control", "no-store")],
                                   rumpf: daten)
        case .skizze:
            return legeSkizze(anfrage.rumpf, mappe: mappe, ordner: ordner)
        case .rechnen:
            return .fehler(Ipadmappenwege.satzRechnenAmMac, status: 409)
        case .benennen:
            return .fehler(Ipadmappenwege.satzBenennenAmMac, status: 409)
        case .fortschritt:
            return nil
        }
    }

    /// Die Sicht samt den Namen, die `GET /bild` ausliefern darf.
    static func sicht(_ mappe: Macmappe, ordner: URL) -> (JSONWert, [String: String]) {
        let heim = ordner.appendingPathComponent(Mappenkern.heimordner, isDirectory: true)
        let auftraege = mappe.auftraege.map { id -> Auftragsablage in
            let ort = ordner.appendingPathComponent(Mappenkern.auftragsweg(id) ?? "-", isDirectory: true)
            let dateien = (try? FileManager.default.contentsOfDirectory(atPath: ort.path)) ?? []
            return Auftragsablage(id: id,
                                  laufzettel: try? Data(contentsOf: ort.appendingPathComponent(Mappenkern.laufzettel)),
                                  dateien: Set(dateien))
        }
        let ipadDa = Set((mappe.skizzen ?? []).map { $0.name }.filter { name in
            FileManager.default.fileExists(atPath: ordner.appendingPathComponent(name).path)
        })
        let glbDa = FileManager.default.fileExists(
            atPath: ordner.appendingPathComponent(Mappenkern.modelldatei).path)
        return Macmappensicht.sicht(mappe, heimDateien: dateien(unter: heim), auftraege: auftraege,
                                    glbDa: glbDa, ipadDa: ipadDa)
    }

    /// Alle Dateien unter einem Ordner, als Wege relativ zu ihm — **ohne Verweisen zu folgen.**
    static func dateien(unter wurzel: URL) -> [String] {
        let basis = wurzel.standardizedFileURL.path + "/"
        guard let gang = FileManager.default.enumerator(
            at: wurzel, includingPropertiesForKeys: [.isRegularFileKey, .isSymbolicLinkKey],
            options: [.skipsHiddenFiles]) else { return [] }
        var aus: [String] = []
        for case let url as URL in gang {
            let werte = try? url.resourceValues(forKeys: [.isRegularFileKey, .isSymbolicLinkKey])
            guard werte?.isRegularFile == true, werte?.isSymbolicLink != true else { continue }
            let pfad = url.standardizedFileURL.path
            if pfad.hasPrefix(basis) { aus.append(String(pfad.dropFirst(basis.count))) }
        }
        return aus
    }

    /// Eine Datei der Mappe — **nur, wenn sie wirklich in ihr liegt** (zweite Sicherung zur Regel
    /// im Kern: auch ein Verweis führt nicht hinaus).
    static func lies(_ weg: String, in ordner: URL) -> Data? {
        let innen = ordner.standardizedFileURL.resolvingSymlinksInPath().path + "/"
        let ziel = ordner.appendingPathComponent(weg).standardizedFileURL
        guard ziel.resolvingSymlinksInPath().path.hasPrefix(innen) else { return nil }
        return try? Data(contentsOf: ziel)
    }

    /// `POST /api/skizze` in die Mappe am Mac: Datei unter `ipad/`, Eintrag in `mappe.json`. Die
    /// Knotenansicht sieht sie danach über `./mappe` (Knoten «Skizze vom iPad»).
    static func legeSkizze(_ rumpf: Data, mappe: Macmappe, ordner: URL) -> Leitungsantwort {
        var zufall = SystemRandomNumberGenerator()
        let zusatz = String(UInt16.random(in: 0...UInt16.max, using: &zufall), radix: 16)
        switch Macskizzen.lege(rumpf, in: mappe, jetzt: Date(), zusatz: zusatz,
                               gespeichert: { lies($0, in: ordner) }) {
        case .abgewiesen(let satz, let status):
            return .fehler(satz, status: status)
        case .wiederholung(let antwort):
            return .json(antwort)
        case .neu(let eintrag, let png, let antwort):
            do {
                let ziel = ordner.appendingPathComponent(eintrag.name)
                try FileManager.default.createDirectory(at: ziel.deletingLastPathComponent(),
                                                        withIntermediateDirectories: true)
                // NIE UEBER EINE VORHANDENE: der Name ist frei nach der Mappe; liegt doch eine
                // Datei da, scheitert es laut.
                try png.write(to: ziel, options: [.withoutOverwriting])
                // FRISCH GELESEN: Die Knotenansicht kann inzwischen geschrieben haben.
                var frisch = Mappenablage.lies(ordner) ?? mappe
                Macskizzen.vermerke(eintrag, in: &frisch)
                try Mappenablage.schreibe(frisch, in: ordner)
            } catch {
                return .fehler("Die Zeichnung liess sich am Mac nicht ablegen: "
                               + error.localizedDescription, status: 500)
            }
            return .json(antwort)
        }
    }
}
