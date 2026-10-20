import Foundation
import VisboxKern
import WebKit

/// Die Knotenansicht **aus dem App-Bündel** («Visbox eigenständig», Schritt 1, 20.10.2026).
///
/// Das Webfenster öffnet `visbox://app/knoten/`; jede Anfrage an dieses Schema landet hier.
/// **Wohin** sie geht, entscheidet der Kern (`Knotenwege.ziel`, mit Proben):
///
/// * Teile des Baus kommen aus `Contents/Resources/Knoten/` (`ipad.yml` legt sie dorthin).
/// * Die Datenwege (`/knoten/mappe`, `/knoten/graph`, `/knoten/modell.glb`, `/knoten/skizze`,
///   `/knoten/modell-laden`) und die Brücke (`/bruecke/*`) reicht die App an den Heim-PC weiter
///   — mit **ihrer** Anmeldung (Basic, aus dem Schlüsselbund), `X-Geraet: mac` und dem
///   angehefteten Zertifikat (`Heimvertrauenslotse`), wie jede andere Anfrage der App.
///   Methode, Typ, Rumpf und Status gehen unverändert durch; gemerkt wird nichts.
/// * Ohne eingerichteten Heim-PC antworten die Datenwege **sofort** mit einem Satz (503),
///   statt zu hängen — die Knotenansicht lädt trotzdem.
///
/// WebKit ruft beide Methoden auf dem Hauptfaden; die Antwort geht ebenfalls dort hinaus
/// (`Task { @MainActor … }`) — dieselbe Form wie `Flaechenlotse`, ohne Akteur an der Klasse.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
final class Knotenquelle: NSObject, WKURLSchemeHandler {
    /// Wie lange ein Datenweg auf den ersten Byte des Heim-PC wartet — gleich wie die
    /// Vermittlung (`Heimstrecke.wartezeit`), damit «nicht erreicht» vor der Zeitgrenze der
    /// Brücke in der Seite (30 s) kommt.
    static let wartezeit: TimeInterval = Heimstrecke.wartezeit
    /// Höchstens so lange für eine ganze Antwort — ein grosses Modell (glb, IFC) hin oder her.
    static let hoechstens: TimeInterval = 600

    var basis: URL?
    var anmeldung: Anmeldung?

    /// Der Ordner des Baus im Bündel.
    private let ordner: URL?
    private let sitzung: URLSession
    /// Laufende Anfragen. WebKit kann eine jederzeit zurückziehen (`stop`); danach darf ihr
    /// **nichts** mehr gemeldet werden, sonst bricht WebKit das Programm ab.
    private var laufend: [ObjectIdentifier: Task<Void, Never>] = [:]

    init(basis: URL?, anmeldung: Anmeldung?) {
        self.basis = basis
        self.anmeldung = anmeldung
        self.ordner = Bundle.main.resourceURL?
            .appendingPathComponent(Knotenwege.ordnerImBuendel, isDirectory: true)
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = Knotenquelle.wartezeit
        art.timeoutIntervalForResource = Knotenquelle.hoechstens
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpCookieStorage = nil
        art.httpShouldSetCookies = false
        art.waitsForConnectivity = false
        // KEIN PROXY DES SYSTEMS — dieselbe Regel wie `Heimstrecke`.
        art.connectionProxyDictionary = [:]
        sitzung = URLSession(configuration: art, delegate: Heimvertrauenslotse.gemeinsam,
                             delegateQueue: nil)
        super.init()
    }

    /// Ob es den Bau im Bündel gibt — sonst sagt die Fläche, dass er fehlt.
    var bauVorhanden: Bool {
        guard let ordner else { return false }
        return FileManager.default.fileExists(atPath: ordner.appendingPathComponent("index.html").path)
    }

    // ================================================================= WKURLSchemeHandler

    func webView(_ webView: WKWebView, start urlSchemeTask: WKURLSchemeTask) {
        guard let adresse = urlSchemeTask.request.url else {
            antworte(urlSchemeTask, status: 400, rumpf: Knotenwege.fehlerRumpf("Ohne Adresse."))
            return
        }
        switch Knotenwege.ziel(adresse: adresse) {
        case .datei(let pfad, let typ):
            liefereDatei(urlSchemeTask, adresse: adresse, pfad: pfad, typ: typ)
        case .umleitung(let ziel):
            // WebKit folgt keiner 301 aus einem Schema-Gastgeber; die Seite selbst wird ohnehin
            // mit Schrägstrich geöffnet. Für alles andere: der Satz, wohin.
            antworte(urlSchemeTask, status: 404,
                     rumpf: Knotenwege.fehlerRumpf("Bitte mit Schrägstrich: \(ziel)"))
        case .unbekannt(let satz):
            antworte(urlSchemeTask, status: Knotenwege.Fehlerart.unbekannt.rawValue,
                     rumpf: Knotenwege.fehlerRumpf(satz))
        case .heim(let pfad):
            reicheWeiter(urlSchemeTask, adresse: adresse, pfad: pfad)
        }
    }

    func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask) {
        let kennung = ObjectIdentifier(urlSchemeTask)
        laufend[kennung]?.cancel()
        laufend[kennung] = nil
    }

    // ================================================================= aus dem Bündel

    private func liefereDatei(_ aufgabe: WKURLSchemeTask, adresse: URL, pfad: String, typ: String) {
        guard let ordner else {
            antworte(aufgabe, status: 404,
                     rumpf: Knotenwege.fehlerRumpf("Die Knotenansicht liegt nicht im Programm."))
            return
        }
        let ziel = ordner.appendingPathComponent(pfad).standardizedFileURL
        // ZWEITE SICHERUNG zur Regel im Kern: Auch ein Verweis im Bündel führt nicht hinaus.
        let innen = ordner.standardizedFileURL.resolvingSymlinksInPath().path + "/"
        guard ziel.resolvingSymlinksInPath().path.hasPrefix(innen),
              let daten = try? Data(contentsOf: ziel) else {
            antworte(aufgabe, status: 404,
                     rumpf: Knotenwege.fehlerRumpf("Unbekannter Weg: \(adresse.path)"))
            return
        }
        antworte(aufgabe, status: 200, rumpf: daten,
                 koepfe: Knotenwege.koepfeFuerDatei(typ: typ, laenge: daten.count))
    }

    // ================================================================= an den Heim-PC

    private func reicheWeiter(_ aufgabe: WKURLSchemeTask, adresse: URL, pfad: String) {
        guard let basis else {
            antworte(aufgabe, status: Knotenwege.Fehlerart.ohneHeim.rawValue,
                     rumpf: Knotenwege.fehlerRumpf(Knotenwege.satzOhneHeim))
            return
        }
        guard let ziel = Knotenwege.heimAdresse(pfad: pfad,
                                                kodierteFrage: Knotenwege.kodierteFrage(adresse),
                                                basis: basis) else {
            antworte(aufgabe, status: Knotenwege.Fehlerart.heimNichtErreicht.rawValue,
                     rumpf: Knotenwege.fehlerRumpf(
                        "Aus der Adresse des Heim-PC liess sich kein Weg bauen."))
            return
        }
        let seite = aufgabe.request
        var auftrag = URLRequest(url: ziel)
        auftrag.httpMethod = seite.httpMethod ?? "GET"
        var vonDerSeite: [Kopfzeile] = []
        for (name, wert) in seite.allHTTPHeaderFields ?? [:] {
            vonDerSeite.append(Kopfzeile(name, wert))
        }
        for k in Knotenwege.koepfeFuerHeim(seite: vonDerSeite, anmeldung: anmeldung) {
            auftrag.setValue(k.wert, forHTTPHeaderField: k.name)
        }
        let rumpf = Knotenquelle.rumpf(seite)
        let kennung = ObjectIdentifier(aufgabe)
        let sitzung = self.sitzung
        laufend[kennung] = Task { @MainActor [weak self] in
            let ergebnis: (Int, [Kopfzeile], Data)
            do {
                let (daten, antwort): (Data, URLResponse)
                if let rumpf {
                    (daten, antwort) = try await sitzung.upload(for: auftrag, from: rumpf)
                } else {
                    (daten, antwort) = try await sitzung.data(for: auftrag)
                }
                guard let http = antwort as? HTTPURLResponse else {
                    throw URLError(.badServerResponse)
                }
                var koepfe: [Kopfzeile] = []
                for (name, wert) in http.allHeaderFields {
                    if let n = name as? String { koepfe.append(Kopfzeile(n, "\(wert)")) }
                }
                ergebnis = (http.statusCode, Knotenwege.koepfeFuerSeite(heim: koepfe), daten)
            } catch {
                if Task.isCancelled { return }
                ergebnis = (Knotenwege.Fehlerart.heimNichtErreicht.rawValue,
                            Knotenwege.koepfeFuerSeite(heim: [
                                Kopfzeile("Content-Type", "application/json; charset=utf-8")]),
                            Knotenwege.fehlerRumpf("Der Heim-PC ist nicht erreicht: "
                                                   + Heimstrecke.satz(error)))
            }
            guard let self, !Task.isCancelled, self.laufend[kennung] != nil else { return }
            self.laufend[kennung] = nil
            self.antworte(aufgabe, status: ergebnis.0, rumpf: ergebnis.2, koepfe: ergebnis.1)
        }
    }

    /// Der Rumpf der Anfrage der Seite — als `httpBody` oder als Strom (WebKit liefert je nach
    /// Art des Rumpfs das eine oder das andere). Die Seite schickt Formulare als fertige Bytes
    /// (`koerperAlsBytes` in `mappe.ts`), weil WebKit einem Schema-Gastgeber den Rumpf mit
    /// Datei-Teilen sonst nicht sicher weitergibt.
    private static func rumpf(_ anfrage: URLRequest) -> Data? {
        if let roh = anfrage.httpBody { return roh }
        guard let strom = anfrage.httpBodyStream else { return nil }
        strom.open()
        defer { strom.close() }
        var gesammelt = Data()
        let stueck = 64 * 1024
        var puffer = [UInt8](repeating: 0, count: stueck)
        while strom.hasBytesAvailable {
            let gelesen = strom.read(&puffer, maxLength: stueck)
            if gelesen <= 0 { break }
            gesammelt.append(puffer, count: gelesen)
        }
        return gesammelt
    }

    // ================================================================= Antwort an die Seite

    private func antworte(_ aufgabe: WKURLSchemeTask, status: Int, rumpf: Data,
                          koepfe: [Kopfzeile]? = nil) {
        let adresse = aufgabe.request.url ?? Knotenwege.einstieg
        var felder: [String: String] = [:]
        let alle = koepfe ?? Knotenwege.koepfeFuerSeite(heim: [
            Kopfzeile("Content-Type", "application/json; charset=utf-8")])
        for k in alle { felder[k.name] = k.wert }
        guard let antwort = HTTPURLResponse(url: adresse, statusCode: status,
                                            httpVersion: "HTTP/1.1", headerFields: felder) else {
            aufgabe.didFailWithError(URLError(.badServerResponse))
            return
        }
        aufgabe.didReceive(antwort)
        aufgabe.didReceive(rumpf)
        aufgabe.didFinish()
    }
}
