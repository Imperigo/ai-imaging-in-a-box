import CryptoKit
import Foundation
import Security
import VisboxKern

/// Laedt die neue Fassung, prueft sie und legt sie an den Ort der alten — **ueber das System,
/// ohne Shell** (Owner-Auftrag zu Entscheid 84, 13.10.2026).
///
/// Die Reihenfolge ist die Sicherung; jeder Schritt bricht ab, bevor etwas angefasst ist:
///
/// 1. **Der Ort:** Laeuft die App an einem Ort, den macOS schreibgeschuetzt verschoben hat,
///    wird gar nicht erst geladen (`Aktualisierung.pruefeOrt`).
/// 2. **Laden nur aus diesem Repo:** Die Adresse muss eine Datei der Freigabe dieses Repos
///    nennen; Weiterleitungen nur zu GitHub selbst (`Herunterlader`).
/// 3. **Groesse und Pruefsumme** gegen die Datei `SHA256SUMS.txt` derselben Freigabe — und,
///    wenn GitHub selbst eine Summe nennt, auch gegen diese.
/// 4. **Entpacken in einen eigenen, leeren Ordner** auf demselben Laufwerk, mit `ditto`, dem
///    Werkzeug des Systems, das auch die Pruefstrecke zum Packen nimmt. Als Prozess mit fester
///    Pfadangabe und Liste der Argumente — keine Shell, kein Zeichen wird gedeutet.
/// 5. **Das Bundle:** genau eines, mit derselben Kennung wie die laufende App, der Nummer der
///    Freigabe, und einer Unterschrift, deren Siegel haelt.
/// 6. **Tauschen:** die alte App in den Papierkorb, die neue an dieselbe Stelle. Scheitert
///    das Hinlegen, kommt die alte aus dem Papierkorb zurueck.
///
/// **Was die Pruefsumme nicht kann, und das steht hier, damit es niemand ueberliest:** Sie
/// beweist, dass die Datei die der Freigabe ist — nicht, wer die Freigabe gemacht hat. Wer
/// in dieses Repo schreiben darf, kann beides ersetzen. Eine Beglaubigung durch Apple gibt es
/// ohne Apple-Konto nicht (`docs/VISBOX_0.2.1_2026-10-13.md`, Grenzen).
///
/// *Gebaut, am Geraet unbestaetigt (13.10.2026).*
enum Ersetzer {
    typealias Melder = @Sendable (Aktualisierungsphase) -> Void

    static func ersetze(_ freigabe: Freigabe, buendel alt: URL, kennung: String,
                        melde: @escaping Melder) async throws {
        if let fehler = Aktualisierung.pruefeOrt(alt.path) { throw fehler }
        guard let paket = freigabe.anlage(Aktualisierung.macPaket) else {
            throw Aktualisierungsfehler.ohneMacPaket
        }
        guard let summen = freigabe.anlage(Aktualisierung.pruefsummen) else {
            throw Aktualisierungsfehler.ohnePruefsummen
        }

        let dateien = FileManager.default
        // DASSELBE LAUFWERK WIE DIE APP (`itemReplacementDirectory`): So ist das Hinlegen am
        // Ende ein Umbenennen und kein Kopieren, das halb fertig liegen bleiben kann.
        let arbeitsort = try dateien.url(for: .itemReplacementDirectory, in: .userDomainMask,
                                         appropriateFor: alt, create: true)
        defer { try? dateien.removeItem(at: arbeitsort) }

        let summenDatei = try await Herunterlader.lade(
            summen.adresse, nach: arbeitsort.appendingPathComponent(summen.name), fortschritt: nil)
        let summenText = String(decoding: try Data(contentsOf: summenDatei), as: UTF8.self)

        melde(.laedt(nil))
        let zip = try await Herunterlader.lade(
            paket.adresse, nach: arbeitsort.appendingPathComponent(paket.name),
            fortschritt: { anteil in melde(.laedt(anteil)) })

        melde(.prueft)
        let (groesse, summe) = try groesseUndSumme(zip)
        if let fehler = Aktualisierung.pruefe(anlage: paket, groesse: groesse, summe: summe,
                                              summenDatei: summenText) { throw fehler }

        let entpackt = arbeitsort.appendingPathComponent("entpackt", isDirectory: true)
        try dateien.createDirectory(at: entpackt, withIntermediateDirectories: false)
        try await entpacke(zip, nach: entpackt)
        guard let name = Aktualisierung.waehleBuendel(
            try dateien.contentsOfDirectory(atPath: entpackt.path)) else {
            throw Aktualisierungsfehler.keinBuendel
        }
        let neu = entpackt.appendingPathComponent(name, isDirectory: true)

        let infoDaten = try Data(contentsOf: neu.appendingPathComponent("Contents/Info.plist"))
        let info = (try? PropertyListSerialization.propertyList(from: infoDaten, format: nil))
            as? [String: Any] ?? [:]
        if let fehler = Aktualisierung.pruefeBuendel(info, kennung: kennung,
                                                     nummer: freigabe.nummer) { throw fehler }
        guard siegelHaelt(neu) else { throw Aktualisierungsfehler.unterschriftGebrochen }

        melde(.ersetzt)
        try tausche(alt: alt, neu: neu)
    }

    /// Groesse und SHA-256 der Datei, in Stuecken gelesen — ein ZIP muss nicht ganz in den
    /// Speicher.
    static func groesseUndSumme(_ datei: URL) throws -> (Int, String) {
        let griff = try FileHandle(forReadingFrom: datei)
        defer { try? griff.close() }
        var rechner = SHA256()
        var groesse = 0
        while let stueck = try griff.read(upToCount: 1 << 20), !stueck.isEmpty {
            rechner.update(data: stueck)
            groesse += stueck.count
        }
        return (groesse, Aktualisierung.sechzehner(rechner.finalize()))
    }

    /// `ditto -x -k <zip> <ordner>` als Prozess — dasselbe Werkzeug, das das ZIP in der
    /// Pruefstrecke gepackt hat (`ditto -c -k --keepParent`), und es behaelt, was ein Bundle
    /// braucht (Rechte, die Unterschrift in den erweiterten Merkmalen).
    static func entpacke(_ zip: URL, nach ordner: URL) async throws {
        let prozess = Process()
        prozess.executableURL = URL(fileURLWithPath: "/usr/bin/ditto")
        prozess.arguments = ["-x", "-k", zip.path, ordner.path]
        try await withCheckedThrowingContinuation { (fortsetzung: CheckedContinuation<Void, Error>) in
            prozess.terminationHandler = { beendet in
                if beendet.terminationStatus == 0 {
                    fortsetzung.resume()
                } else {
                    fortsetzung.resume(throwing: Aktualisierungsfehler.keinBuendel)
                }
            }
            do {
                try prozess.run()
            } catch {
                // OHNE START KEIN ENDE: Der `terminationHandler` laeuft dann nie, die
                // Fortsetzung wird genau hier einmal aufgeloest.
                fortsetzung.resume(throwing: error)
            }
        }
    }

    /// Ob das Siegel der Unterschrift haelt. Die Behelfs-Unterschrift beglaubigt niemanden,
    /// aber sie versiegelt das Bundle: Eine danach geaenderte Datei bricht es.
    static func siegelHaelt(_ buendel: URL) -> Bool {
        var code: SecStaticCode?
        guard SecStaticCodeCreateWithPath(buendel as CFURL, SecCSFlags(), &code) == errSecSuccess,
              let code else { return false }
        return SecStaticCodeCheckValidity(code, SecCSFlags(), nil) == errSecSuccess
    }

    /// Die alte App in den Papierkorb, die neue an ihre Stelle. **Nicht loeschen:** Was im
    /// Papierkorb liegt, holt der Owner mit einem Griff zurueck, wenn die neue Fassung nicht
    /// taugt.
    static func tausche(alt: URL, neu: URL) throws {
        let dateien = FileManager.default
        var imPapierkorb: NSURL?
        do {
            try dateien.trashItem(at: alt, resultingItemURL: &imPapierkorb)
        } catch {
            throw Aktualisierungsfehler.ersetzenScheiterte(
                "Die bisherige App liess sich nicht in den Papierkorb legen (\(error.localizedDescription)).")
        }
        do {
            try dateien.moveItem(at: neu, to: alt)
        } catch {
            if let zurueck = imPapierkorb as URL? { try? dateien.moveItem(at: zurueck, to: alt) }
            throw Aktualisierungsfehler.ersetzenScheiterte(
                "Die neue App liess sich nicht hinlegen (\(error.localizedDescription)).")
        }
    }
}

/// Ein Download mit Fortschritt und **bewachten Weiterleitungen**.
///
/// Eine eigene, fluechtige Sitzung je Datei: Der Beauftragte (`delegate`) sieht jede
/// Weiterleitung, bevor ihr gefolgt wird, und laesst nur die zu GitHub selbst zu
/// (`Aktualisierung.istErlaubteWeiterleitung`). GitHub leitet Dateien einer Freigabe auf seine
/// Ablage um (`*.githubusercontent.com`).
final class Herunterlader: NSObject, URLSessionDownloadDelegate, @unchecked Sendable {
    private let ziel: URL
    private let fortschritt: (@Sendable (Double?) -> Void)?
    private let schloss = NSLock()
    private var fortsetzung: CheckedContinuation<URL, Error>?
    private var ergebnis: Result<URL, Error>?

    private init(ziel: URL, fortschritt: (@Sendable (Double?) -> Void)?) {
        self.ziel = ziel
        self.fortschritt = fortschritt
    }

    static func lade(_ adresse: URL, nach ziel: URL,
                     fortschritt: (@Sendable (Double?) -> Void)?) async throws -> URL {
        guard Aktualisierung.istAusDiesemRepo(adresse) else {
            throw Aktualisierungsfehler.fremdeAdresse
        }
        let lader = Herunterlader(ziel: ziel, fortschritt: fortschritt)
        let sitzung = URLSession(configuration: .ephemeral, delegate: lader, delegateQueue: nil)
        defer { sitzung.finishTasksAndInvalidate() }
        return try await withCheckedThrowingContinuation { fortsetzung in
            lader.schloss.lock()
            lader.fortsetzung = fortsetzung
            lader.schloss.unlock()
            sitzung.downloadTask(with: adresse).resume()
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        if let neu = request.url, Aktualisierung.istErlaubteWeiterleitung(neu) {
            completionHandler(request)
        } else {
            schloss.lock()
            ergebnis = .failure(Aktualisierungsfehler.fremdeAdresse)
            schloss.unlock()
            completionHandler(nil)
        }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didWriteData _: Int64, totalBytesWritten geschrieben: Int64,
                    totalBytesExpectedToWrite erwartet: Int64) {
        fortschritt?(erwartet > 0 ? Double(geschrieben) / Double(erwartet) : nil)
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didFinishDownloadingTo ort: URL) {
        // DIE DATEI GILT NUR BIS ZUM ENDE DIESER METHODE — darum hier verschieben.
        schloss.lock()
        defer { schloss.unlock() }
        guard ergebnis == nil else { return }
        guard (downloadTask.response as? HTTPURLResponse)?.statusCode == 200 else {
            ergebnis = .failure(Aktualisierungsfehler.ersetzenScheiterte(
                "GitHub hat die Datei nicht geliefert."))
            return
        }
        do {
            try? FileManager.default.removeItem(at: ziel)
            try FileManager.default.moveItem(at: ort, to: ziel)
            ergebnis = .success(ziel)
        } catch {
            ergebnis = .failure(error)
        }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask,
                    didCompleteWithError fehler: Error?) {
        schloss.lock()
        let ende = ergebnis ?? .failure(fehler ?? Aktualisierungsfehler.ersetzenScheiterte(
            "Der Download brach ab."))
        let wartend = fortsetzung
        fortsetzung = nil
        schloss.unlock()
        wartend?.resume(with: ende)
    }
}
