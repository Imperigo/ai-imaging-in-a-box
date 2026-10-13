import Combine
import Foundation
import Network
import VisboxKern

/// Sucht den Heim-PC **selbst** (Entscheid 83, Blatt 17) — im Tailscale-Netz und im WLAN —
/// und spricht mit dem gewählten die drei Wege der Kopplung.
///
/// * **Tailscale:** die Befehlszeile der Tailscale-App **als Prozess** (`status --json`, die
///   Pfade in `Heimkopplung.tailscaleProgramme`), dann je Gerät `GET /api/hallo` mit kurzer
///   Frist. Fehlt Tailscale, gibt es nur die WLAN-Suche, und der Satz sagt es.
/// * **WLAN:** `NWBrowser` nach `Marke.dienst` (Network, Plattform), nur Funde mit `tls=1`;
///   aufgelöst über eine kurze Verbindung, dann `hallo` über TLS mit noch nicht
///   angeheftetem Zertifikat (`Lernlotse`).
///
/// Was eine Antwort heisst, entscheidet der Kern (`Tailscalestatus`, `Heimkandidat`,
/// `Anforderungsergebnis`, `Verbindungsergebnis`). Hier stehen nur Prozess, Netz und Uhr.
///
/// **Kein Kennwort im Protokoll, keins in einer Datei:** Die Antwort von `verbinden` geht
/// als `Heimzugang` an `Heimleitung.richteEin(zugang:)`, die es in den Schlüsselbund legt.
///
/// *Gebaut, am Gerät unbestätigt (13.10.2026).*
final class Heimsucher: ObservableObject {
    @Published private(set) var suche = Heimsuche()
    @Published private(set) var tailscaleSatz: String?
    @Published private(set) var wlanSatz: String?
    @Published private(set) var sucht = false

    private let lotse = Lernlotse()
    private let sitzung: URLSession
    private var browser: NWBrowser?

    init() {
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = 10
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpShouldSetCookies = false
        art.httpCookieAcceptPolicy = .never
        // KEIN PROXY DES SYSTEMS — wie die Leitung nach Hause (`Heimstrecke`).
        art.connectionProxyDictionary = [:]
        sitzung = URLSession(configuration: art, delegate: lotse, delegateQueue: nil)
    }

    deinit {
        browser?.cancel()
    }

    // ------------------------------------------------------------------ suchen

    @MainActor
    func starte() {
        halte()
        suche = Heimsuche()
        tailscaleSatz = nil
        wlanSatz = nil
        sucht = true
        Task { @MainActor in
            await sucheTailscale()
            sucht = false
        }
        sucheImWlan()
    }

    @MainActor
    func halte() {
        browser?.cancel()
        browser = nil
    }

    @MainActor
    private func sucheTailscale() async {
        let ausgabe = await Task.detached { Heimsucher.tailscaleStatus() }.value
        guard let daten = ausgabe else {
            tailscaleSatz = "Tailscale nicht gefunden oder nicht an — gesucht wird nur im WLAN."
            return
        }
        guard let geraete = Tailscalestatus.geraete(aus: daten) else {
            tailscaleSatz = "Tailscale antwortet, aber die Liste ist nicht lesbar (angemeldet?)."
            return
        }
        let kandidaten = Tailscalestatus.kandidaten(geraete)
        tailscaleSatz = kandidaten.isEmpty
            ? "Im Tailscale-Netz ist kein anderes Gerät online."
            : nil
        suche.nimm(kandidaten)
        await withTaskGroup(of: Void.self) { gruppe in
            for k in kandidaten {
                gruppe.addTask { await self.frageHallo(k) }
            }
        }
    }

    /// `tailscale status --json` — die Ausgabe, oder `nil`, wenn kein Programm antwortet.
    /// Höchstens 5 s je Programm: Eine hängende Befehlszeile soll die Suche nicht aufhalten.
    private static func tailscaleStatus() -> Data? {
        for pfad in Heimkopplung.tailscaleProgramme
            where FileManager.default.isExecutableFile(atPath: pfad) {
            let prozess = Process()
            prozess.executableURL = URL(fileURLWithPath: pfad)
            prozess.arguments = ["status", "--json"]
            let rohr = Pipe()
            prozess.standardOutput = rohr
            prozess.standardError = FileHandle.nullDevice
            do {
                try prozess.run()
            } catch {
                continue
            }
            let wache = DispatchWorkItem { if prozess.isRunning { prozess.terminate() } }
            DispatchQueue.global().asyncAfter(deadline: .now() + 5, execute: wache)
            // ERST LESEN, DANN WARTEN: Eine volle Leitung haelt sonst den Prozess fest.
            let daten = rohr.fileHandleForReading.readDataToEndOfFile()
            prozess.waitUntilExit()
            wache.cancel()
            if prozess.terminationStatus == 0, !daten.isEmpty { return daten }
        }
        return nil
    }

    @MainActor
    private func sucheImWlan() {
        let parameter = NWParameters.tcp
        parameter.includePeerToPeer = false
        let b = NWBrowser(for: .bonjourWithTXTRecord(type: Marke.dienst, domain: nil),
                          using: parameter)
        b.stateUpdateHandler = { [weak self] stand in
            if case .failed = stand {
                Task { @MainActor in
                    self?.wlanSatz = "Die Suche im WLAN ging nicht (lokales Netzwerk erlaubt? "
                        + "Systemeinstellungen → Datenschutz & Sicherheit → Lokales Netzwerk)."
                }
            }
        }
        b.browseResultsChangedHandler = { [weak self] ergebnisse, _ in
            for e in ergebnisse {
                guard case .service(let name, _, _, _) = e.endpoint else { continue }
                var txt: [String: String] = [:]
                if case .bonjour(let eintrag) = e.metadata { txt = eintrag.dictionary }
                self?.loese(e.endpoint, name: name, txt: txt)
            }
        }
        b.start(queue: .main)
        browser = b
    }

    /// Einen Bonjour-Fund in Adresse und Anschluss auflösen — über eine kurze Verbindung,
    /// **nur IPv4** (eine IPv6-Adresse mit Zone trüge keine `URL`).
    private func loese(_ ziel: NWEndpoint, name: String, txt: [String: String]) {
        guard txt["tls"] == "1" else {
            Task { @MainActor in
                self.wlanSatz = "Im WLAN läuft ein \(Marke.name)-Heim-PC nur unverschlüsselt "
                    + "(--im-heimnetz). Zum Koppeln braucht es --heimnetz (betrieb/README.md)."
            }
            return
        }
        let parameter = NWParameters.tcp
        if let ip = parameter.defaultProtocolStack.internetProtocol as? NWProtocolIP.Options {
            ip.version = .v4
        }
        let leitung = NWConnection(to: ziel, using: parameter)
        leitung.stateUpdateHandler = { [weak self] stand in
            switch stand {
            case .ready:
                if case .hostPort(let host, let port)? = leitung.currentPath?.remoteEndpoint {
                    let text: String
                    switch host {
                    case .ipv4(let a): text = "\(a)"
                    case .ipv6(let a): text = "\(a)"
                    case .name(let n, _): text = n
                    @unknown default: text = ""
                    }
                    if let k = Heimkandidat.ausBonjour(name: name, host: text,
                                                       anschluss: Int(port.rawValue), txt: txt) {
                        Task { @MainActor in
                            self?.lotse.lasseZu(k.adresse)
                            self?.suche.nimm([k])
                            await self?.frageHallo(k)
                        }
                    }
                }
                leitung.cancel()
            case .failed, .waiting:
                leitung.cancel()
            default:
                break
            }
        }
        leitung.start(queue: .main)
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { leitung.cancel() }
    }

    @MainActor
    private func frageHallo(_ k: Heimkandidat) async {
        switch await hole(Anfragen.hallo(), basis: k.adresse, frist: Heimkopplung.halloFrist) {
        case .antwort(let status, let daten):
            suche.setze(k.nach(halloStatus: status, daten: daten,
                               fingerabdruck: lotse.gesehen(k.adresse)))
        case .keine(let fehler):
            suche.setze(k.nach(halloStatus: nil, daten: Data(), fingerabdruck: nil,
                               grund: fehler.satz))
        }
    }

    // ------------------------------------------------------------------ koppeln

    /// «Weiter» und «Neue Zahl anfordern».
    @MainActor
    func fordereAn(bei k: Heimkandidat) async -> Anforderungsergebnis {
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.kopplungAnfordern()
        } catch {
            return .abgelehnt(satz: "Die Anfrage liess sich nicht bauen.")
        }
        switch await hole(anfrage, basis: k.adresse, frist: 10) {
        case .antwort(let status, let daten):
            return Anforderungsergebnis.lies(status: status, daten: daten)
        case .keine(let fehler):
            return .abgelehnt(satz: fehler.satz)
        }
    }

    /// «Koppeln»: die Zahl gegen den Zugang.
    @MainActor
    func verbinde(_ k: Heimkandidat, zahl: Kopplungszahl) async -> Verbindungsergebnis {
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.verbinden(zahl)
        } catch {
            return .fehler(satz: "Die Anfrage liess sich nicht bauen.")
        }
        switch await hole(anfrage, basis: k.adresse, frist: 10) {
        case .antwort(let status, let daten):
            let gesehen = k.weg == .heimnetz ? lotse.gesehen(k.adresse) : nil
            return Verbindungsergebnis.lies(status: status, daten: daten,
                                            gefragtBei: k.adresse, gesehen: gesehen)
        case .keine(let fehler):
            return .fehler(satz: fehler.satz)
        }
    }

    // ------------------------------------------------------------------ senden

    private enum Ergebnis {
        case antwort(status: Int, daten: Data)
        case keine(Leitungsfehler)
    }

    private func hole(_ anfrage: Anfrage, basis: URL, frist: TimeInterval) async -> Ergebnis {
        guard let ziel = anfrage.adresse(basis: basis) else { return .keine(.sonstig(code: 0)) }
        var auftrag = URLRequest(url: ziel)
        auftrag.httpMethod = anfrage.methode.rawValue
        auftrag.httpBody = anfrage.rumpf
        auftrag.timeoutInterval = frist
        for (name, wert) in anfrage.kopfzeilen {
            auftrag.setValue(wert, forHTTPHeaderField: name)
        }
        do {
            let (daten, antwort) = try await sitzung.data(for: auftrag)
            guard let http = antwort as? HTTPURLResponse else { return .keine(.sonstig(code: 0)) }
            return .antwort(status: http.statusCode, daten: daten)
        } catch let fehler as URLError {
            return .keine(Leitungsfehler(urlFehlercode: fehler.code.rawValue))
        } catch {
            let ns = error as NSError
            return .keine(Leitungsfehler(urlFehlercode: ns.domain == NSURLErrorDomain ? ns.code : 0))
        }
    }
}
