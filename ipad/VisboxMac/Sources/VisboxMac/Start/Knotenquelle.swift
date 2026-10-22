import Foundation
import VisboxKern
import WebKit

/// Die Knotenansicht **aus dem App-Bündel** («Visbox eigenständig», Schritt 1, 20.10.2026).
///
/// Das Webfenster öffnet `visbox://app/knoten/`; jede Anfrage an dieses Schema landet hier.
/// **Wohin** sie geht, entscheidet der Kern (`Knotenwege.ziel`, mit Proben):
///
/// * Teile des Baus kommen aus `Contents/Resources/Knoten/` (`ipad.yml` legt sie dorthin).
/// * Die Datenwege (`/knoten/mappe`, `/knoten/graph`, `/knoten/modell.glb`, `/knoten/skizze`, `/knoten/standpunkte`,
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
    static let hoechstens: TimeInterval = Knotenwege.hoechstensGanz

    var basis: URL?
    var anmeldung: Anmeldung?
    /// Der Ordner der offenen **Mappe am Mac** («Visbox eigenständig», Schritt 3, 21.10.2026) —
    /// `nil`: keine offen, dann geht alles wie bis 0.3.14 an den Heim-PC. Mit Mappe beantwortet
    /// die App `./mappe`, `./graph`, `./modell.glb` und `./skizze` selbst (`Mappenkern.ziel`),
    /// nennt die Mappe bei jedem Auftrag und legt die Bilder fertiger Aufträge hinein.
    var mappe: URL?

    /// Der Ordner des Baus im Bündel.
    private let ordner: URL?
    private let sitzung: URLSession
    /// Dieselbe Leitung mit der langen Wartezeit — für die Wege, die ein Modell hochladen
    /// (`Knotenwege.wartezeit`, 20.10.2026). Eine eigene Sitzung statt `timeoutInterval` an
    /// der Anfrage: welche der beiden Angaben `URLSession` dann nimmt, ist nicht verbürgt.
    private let langeSitzung: URLSession
    /// Laufende Anfragen. WebKit kann eine jederzeit zurückziehen (`stop`); danach darf ihr
    /// **nichts** mehr gemeldet werden, sonst bricht WebKit das Programm ab.
    private var laufend: [ObjectIdentifier: Task<Void, Never>] = [:]

    init(basis: URL?, anmeldung: Anmeldung?) {
        self.basis = basis
        self.anmeldung = anmeldung
        self.ordner = Bundle.main.resourceURL?
            .appendingPathComponent(Knotenwege.ordnerImBuendel, isDirectory: true)
        sitzung = Knotenquelle.baueSitzung(wartezeit: Knotenquelle.wartezeit)
        langeSitzung = Knotenquelle.baueSitzung(wartezeit: Knotenwege.wartezeitLang)
        super.init()
    }

    private static func baueSitzung(wartezeit: TimeInterval) -> URLSession {
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = wartezeit
        art.timeoutIntervalForResource = Knotenquelle.hoechstens
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpCookieStorage = nil
        art.httpShouldSetCookies = false
        art.waitsForConnectivity = false
        // KEIN PROXY DES SYSTEMS — dieselbe Regel wie `Heimstrecke`.
        art.connectionProxyDictionary = [:]
        return URLSession(configuration: art, delegate: Heimvertrauenslotse.gemeinsam,
                          delegateQueue: nil)
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
            if let ordner = mappe,
               let ziel = Mappenkern.ziel(methode: urlSchemeTask.request.httpMethod ?? "GET", pfad: pfad) {
                ausDerMappe(urlSchemeTask, adresse: adresse, pfad: pfad, ziel: ziel, ordner: ordner)
            } else if pfad == Knotenmappenwahl.graphWeg,
                      (urlSchemeTask.request.httpMethod ?? "GET").uppercased() == "GET" {
                // ENTSCHEID 129: Welche Mappe die Knotenansicht gelesen hat, merkt sich die App —
                // beim naechsten Oeffnen verlangt sie genau diese (`Knotenmappenwahl`).
                let verlangt = Knotenmappenwahl.verlangt(in: adresse)
                reicheWeiter(urlSchemeTask, adresse: adresse, pfad: pfad) { status, koepfe, daten in
                    Knotenmappengedaechtnis.nimm(Knotenmappenwahl.folge(status: status, daten: daten,
                                                                        verlangt: verlangt))
                    return (status, koepfe, daten)
                }
            } else {
                reicheWeiter(urlSchemeTask, adresse: adresse, pfad: pfad)
            }
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

    /// Was nach der Antwort des Heim-PC noch geschieht, bevor die Seite sie bekommt (Schritt 3:
    /// Bilder in die Mappe, ohne Heim-PC aus der Mappe) — Status, Köpfe, Rumpf hinein und hinaus.
    typealias Danach = (Int, [Kopfzeile], Data) -> (Int, [Kopfzeile], Data)

    private func reicheWeiter(_ aufgabe: WKURLSchemeTask, adresse: URL, pfad: String,
                              frage: String?? = nil, zusatz: [Kopfzeile] = [],
                              danach: Danach? = nil) {
        guard let basis else {
            let (s, k, r) = (danach ?? { ($0, $1, $2) })(
                Knotenwege.Fehlerart.ohneHeim.rawValue, Knotenwege.koepfeFuerSeite(heim: [
                    Kopfzeile("Content-Type", "application/json; charset=utf-8")]),
                Knotenwege.fehlerRumpf(Knotenwege.satzOhneHeim))
            antworte(aufgabe, status: s, rumpf: r, koepfe: k)
            return
        }
        guard let ziel = Knotenwege.heimAdresse(pfad: pfad,
                                                kodierteFrage: frage ?? Knotenwege.kodierteFrage(adresse),
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
        for k in Knotenwege.koepfeFuerHeim(seite: vonDerSeite, anmeldung: anmeldung) + zusatz {
            auftrag.setValue(k.wert, forHTTPHeaderField: k.name)
        }
        let rumpf = Knotenquelle.rumpf(seite)
        let kennung = ObjectIdentifier(aufgabe)
        // LANG NUR FÜR DIE ZWEI WEGE MIT MODELL (Kern: `Knotenwege.wartezeit`).
        let sitzung = Knotenwege.wartezeit(methode: auftrag.httpMethod ?? "GET", pfad: pfad)
            > Knotenquelle.wartezeit ? self.langeSitzung : self.sitzung
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
            let (s, k, r) = (danach ?? { ($0, $1, $2) })(ergebnis.0, ergebnis.1, ergebnis.2)
            self.antworte(aufgabe, status: s, rumpf: r, koepfe: k)
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

    // ================================================================= aus der Mappe am Mac

    /// Ein Datenweg mit offener Mappe am Mac (Schritt 3) — was `Mappenkern.ziel` sagt.
    private func ausDerMappe(_ aufgabe: WKURLSchemeTask, adresse: URL, pfad: String,
                             ziel: Mappenziel, ordner: URL) {
        guard let mappe = Mappenablage.lies(ordner) else {
            antworte(aufgabe, status: 404, rumpf: Knotenwege.fehlerRumpf(
                "Die Mappe am Mac ist nicht mehr lesbar — unter «Mappen …» eine andere öffnen."))
            return
        }
        switch ziel {
        case .mappe:
            let glbDa = FileManager.default.fileExists(
                atPath: ordner.appendingPathComponent(Mappenkern.modelldatei).path)
            // MIT DEN SKIZZEN VOM IPAD (Schritt 4): auch sie stehen in der Liste, wenn ihre Datei liegt.
            let namen = Mappenkern.skizzennamen(mappe)
            let da = Set(namen.filter { name in
                Mappenkern.skizzenweg(name).map {
                    FileManager.default.fileExists(atPath: ordner.appendingPathComponent($0).path)
                } ?? false
            })
            antworteJSON(aufgabe, Mappenkern.knotenAntwort(mappe, glbDa: glbDa, skizzenDa: da))
        case .graphLesen:
            antworteJSON(aufgabe, Mappenkern.graphAntwort(
                try? Data(contentsOf: ordner.appendingPathComponent(Mappenkern.graphdatei))))
        case .graphSichern:
            do {
                let (datei, anzahl) = try Mappenkern.graphDatei(aus: Knotenquelle.rumpf(aufgabe.request) ?? Data())
                try Mappenablage.lege(datei, weg: Mappenkern.graphdatei, in: ordner)
                antworteJSON(aufgabe, .objekt(["gesichert": .ganz(anzahl)]))
            } catch let fehler as Mappenkern.Graphfehler {
                antworte(aufgabe, status: fehler.status, rumpf: Knotenwege.fehlerRumpf(fehler.satz))
            } catch {
                antworte(aufgabe, status: 500, rumpf: Knotenwege.fehlerRumpf(
                    "Der Graph liess sich am Mac nicht sichern: \(error.localizedDescription)"))
            }
        case .modell:
            liefereAusMappe(aufgabe, ordner: ordner, weg: Mappenkern.modelldatei,
                            fehlt: "Die Mappe hat noch kein glb.")
        case .skizze:
            let name = URLComponents(url: adresse, resolvingAgainstBaseURL: true)?
                .queryItems?.first { $0.name == "name" }?.value ?? ""
            guard let weg = Mappenkern.skizzenweg(name) else {
                antworte(aufgabe, status: 404, rumpf: Knotenwege.fehlerRumpf("Keine Skizze: \(name)"))
                return
            }
            liefereAusMappe(aufgabe, ordner: ordner, weg: weg, fehlt: "Die Skizze liegt nicht in der Mappe.")
        case .standpunkte:
            guard let frage = Mappenkern.standpunkteFrage(kodierteFrage: Knotenwege.kodierteFrage(adresse),
                                                          heimMappe: mappe.heimMappe) else {
                antworte(aufgabe, status: 409, rumpf: Knotenwege.fehlerRumpf(Mappenkern.satzStandpunkteOhneZwilling))
                return
            }
            reicheWeiter(aufgabe, adresse: adresse, pfad: pfad, frage: frage)
        case .modellHolen:
            holeModell(aufgabe, rumpf: Knotenquelle.rumpf(aufgabe.request) ?? Data())
        case .modellLaden:
            // «DATEI LADEN …» MIT DEM NAMEN DER MAPPE AM MAC (Befund auf-20261021-304 B1): sonst
            // stellte der Heim-PC seine zuletzt geoeffnete Mappe fuer alle Geraete um.
            reicheWeiter(aufgabe, adresse: adresse, pfad: pfad, zusatz: Mappenkern.ladekoepfe(mappe))
        case .auftragAnlegen:
            reicheWeiter(aufgabe, adresse: adresse, pfad: pfad, zusatz: Mappenkern.auftragskoepfe(mappe)) {
                status, koepfe, daten in
                if status == 200, let id = Mappenkern.auftragskennung(aus: daten),
                   var neu = Mappenablage.lies(ordner) {
                    neu.vermerke(auftrag: id)
                    try? Mappenablage.schreibe(neu, in: ordner)
                }
                return (status, koepfe, daten)
            }
        case .auftragLesen(let id):
            let zettel = Mappenkern.auftragsweg(id, datei: Mappenkern.laufzettel)
            reicheWeiter(aufgabe, adresse: adresse, pfad: pfad) { [weak self] status, koepfe, daten in
                guard mappe.auftraege.contains(id), let zettel else { return (status, koepfe, daten) }
                if status == 200 {
                    // DER STAND IN DIE MAPPE, und ist er fertig, die Bilder dazu.
                    try? Mappenablage.lege(daten, weg: zettel, in: ordner)
                    if let bilder = Mappenkern.fertigeBilder(laufzettel: daten) {
                        self?.holeBilder(id, bilder, in: ordner)
                    }
                    return (status, koepfe, daten)
                }
                // OHNE HEIM-PC: der Stand, den die Mappe zuletzt sah.
                if status == 502 || status == 503,
                   let gemerkt = try? Data(contentsOf: ordner.appendingPathComponent(zettel)) {
                    return (200, Knotenwege.koepfeFuerSeite(heim: [
                        Kopfzeile("Content-Type", "application/json; charset=utf-8")]), gemerkt)
                }
                return (status, koepfe, daten)
            }
        case .auftragsbild(let id, let name):
            // EIN BILD AENDERT SICH NICHT: liegt es in der Mappe, kommt es von dort.
            if mappe.auftraege.contains(id), let weg = Mappenkern.auftragsweg(id, datei: name),
               FileManager.default.fileExists(atPath: ordner.appendingPathComponent(weg).path) {
                liefereAusMappe(aufgabe, ordner: ordner, weg: weg, fehlt: "")
                return
            }
            reicheWeiter(aufgabe, adresse: adresse, pfad: pfad) { status, koepfe, daten in
                if status == 200, mappe.auftraege.contains(id),
                   let weg = Mappenkern.auftragsweg(id, datei: name) {
                    try? Mappenablage.lege(daten, weg: weg, in: ordner)
                }
                return (status, koepfe, daten)
            }
        }
    }

    /// Die Bilder eines fertigen Auftrags in die Mappe — nur, was noch fehlt, im Hintergrund.
    private func holeBilder(_ id: String, _ namen: [String], in ordner: URL) {
        guard let basis else { return }
        let anmeldung = self.anmeldung
        let fehlend = namen.filter { name in
            Mappenkern.auftragsweg(id, datei: name).map {
                !FileManager.default.fileExists(atPath: ordner.appendingPathComponent($0).path)
            } ?? false
        }
        guard !fehlend.isEmpty else { return }
        Task {
            for name in fehlend {
                guard let weg = Mappenkern.auftragsweg(id, datei: name),
                      let ziel = Knotenwege.heimAdresse(
                        pfad: "/bruecke/jobs/\(id)/artifacts/" + name,
                        kodierteFrage: nil, basis: basis) else { continue }
                try? await Mappenholer.lade(ziel, anmeldung: anmeldung, nach: ordner.appendingPathComponent(weg))
            }
        }
    }

    /// «Datei laden …» ist fertig (Wirt: `POST ./mappe-holen`): das Modell in die offene Mappe.
    private func holeModell(_ aufgabe: WKURLSchemeTask, rumpf: Data) {
        guard let kennung = Mappenkern.holwunsch(rumpf) else {
            antworte(aufgabe, status: 400, rumpf: Knotenwege.fehlerRumpf("Welche Mappe? (mappe fehlt)"))
            return
        }
        let (basis, anmeldung) = (self.basis, self.anmeldung)
        let schluessel = ObjectIdentifier(aufgabe)
        laufend[schluessel] = Task { @MainActor [weak self] in
            var status = 200
            var antwort = JSONWert.objekt(["mappe": .text(kennung)])
            do {
                try await Mappenablage.gemeinsam.holeModell(von: kennung, basis: basis, anmeldung: anmeldung)
            } catch {
                status = Knotenwege.Fehlerart.heimNichtErreicht.rawValue
                antwort = .objekt(["fehler": .text("Das Modell kam nicht an den Mac: " + Mappenholer.satz(error))])
            }
            guard let self, !Task.isCancelled, self.laufend[schluessel] != nil else { return }
            self.laufend[schluessel] = nil
            self.antworteJSON(aufgabe, antwort, status: status)
        }
    }

    private func liefereAusMappe(_ aufgabe: WKURLSchemeTask, ordner: URL, weg: String, fehlt: String) {
        guard let daten = try? Data(contentsOf: ordner.appendingPathComponent(weg)) else {
            antworte(aufgabe, status: 404, rumpf: Knotenwege.fehlerRumpf(fehlt.isEmpty ? "Nicht in der Mappe." : fehlt))
            return
        }
        let endung = (weg as NSString).pathExtension.lowercased()
        let typ = ["glb": "model/gltf-binary", "png": "image/png", "jpg": "image/jpeg",
                   "jpeg": "image/jpeg", "webp": "image/webp"][endung] ?? "application/octet-stream"
        antworte(aufgabe, status: 200, rumpf: daten, koepfe: Knotenwege.koepfeFuerDatei(typ: typ, laenge: daten.count))
    }

    private func antworteJSON(_ aufgabe: WKURLSchemeTask, _ wert: JSONWert, status: Int = 200) {
        antworte(aufgabe, status: status, rumpf: (try? wert.daten()) ?? Data("{}".utf8))
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
