import Foundation

/// Was auf eine Anfrage zurückkam — **eine Antwort, oder keine.**
///
/// «Keine» trägt mit, wie viele Bytes des Rumpfs schon hinaus waren. Das entscheidet im
/// Parkfach, ob eine Skizze sicher nicht angekommen ist (kein Byte) oder ob es **nicht
/// bekannt** ist (`Sendeergebnis.ohneVerbindung`).
enum Leitungsergebnis {
    case antwort(status: Int, daten: Data)
    case keineAntwort(grund: String, gesendeteBytes: Int64)
}

/// Führt die Anfragen des Kerns (`Kern/Anfragen.swift`) mit `URLSession` aus — **und
/// entscheidet nichts.** Was eine Antwort heisst, liest der Kern.
///
/// **Der Fortschritt ist gezählt, nicht geschätzt:** Er kommt aus
/// `urlSession(_:task:didSendBodyData:…)`, also aus den Bytes, die das System wirklich
/// hinausgegeben hat. Kennt das System das Gesamt nicht, kommt `nil` — dann zeigt die
/// Übergabe keinen Balken, sondern eine atmende Marke (Regel 2 des Entwurfs).
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).* Hier nicht übersetzt; `URLSession` gibt
/// es unter Linux nicht in dieser Form.
final class Sender {
    private let sitzung: URLSession

    init() {
        // FLUECHTIG: nichts zwischenspeichern, keine Kekse. Ein Bild aus einem neuen Lauf
        // kommt unter demselben Namen; ein zwischengespeichertes altes zeigte ein Ergebnis,
        // das es nicht mehr gibt (der Server sagt dasselbe mit `Cache-Control: no-store`).
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = 30
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        sitzung = URLSession(configuration: art)
    }

    /// Führt eine Anfrage aus. `fortschritt` bekommt (gesendet, gesamt oder `nil`) — von
    /// einem beliebigen Faden aus.
    func fuehreAus(_ anfrage: Anfrage, basis: URL,
                   fortschritt: ((Int64, Int64?) -> Void)? = nil) async -> Leitungsergebnis {
        guard let adresse = anfrage.adresse(basis: basis) else {
            return .keineAntwort(grund: "Aus der Adresse der HomeStation liess sich kein Weg bauen.",
                                 gesendeteBytes: 0)
        }
        var auftrag = URLRequest(url: adresse)
        auftrag.httpMethod = anfrage.methode.rawValue
        for (name, wert) in anfrage.kopfzeilen {
            auftrag.setValue(wert, forHTTPHeaderField: name)
        }
        let zaehler = Bytezaehler(melde: fortschritt)
        do {
            let daten: Data
            let antwort: URLResponse
            if let rumpf = anfrage.rumpf {
                (daten, antwort) = try await sitzung.upload(for: auftrag, from: rumpf,
                                                            delegate: zaehler)
            } else {
                (daten, antwort) = try await sitzung.data(for: auftrag, delegate: zaehler)
            }
            guard let http = antwort as? HTTPURLResponse else {
                return .keineAntwort(grund: "Was zurückkam, war keine Antwort der HomeStation.",
                                     gesendeteBytes: zaehler.gesendet)
            }
            return .antwort(status: http.statusCode, daten: daten)
        } catch {
            return .keineAntwort(grund: Sender.satz(error), gesendeteBytes: zaehler.gesendet)
        }
    }

    /// Ein Satz für einen Menschen — nicht die Programmmeldung des Systems.
    static func satz(_ fehler: Error) -> String {
        guard let f = fehler as? URLError else {
            return "Die Verbindung kam nicht zustande (\(fehler.localizedDescription))."
        }
        switch f.code {
        case .cannotConnectToHost:
            return "Die HomeStation nimmt keine Verbindung an — läuft der Server dort?"
        case .cannotFindHost, .dnsLookupFailed:
            return "Die Adresse der HomeStation ist im Netz nicht zu finden."
        case .timedOut:
            return "Die HomeStation hat nicht rechtzeitig geantwortet."
        case .notConnectedToInternet:
            return "Das iPad ist mit keinem Netz verbunden."
        case .networkConnectionLost:
            return "Die Verbindung ist unterwegs abgerissen."
        case .cancelled:
            return "Das Senden wurde abgebrochen."
        default:
            return "Die Verbindung kam nicht zustande (\(f.localizedDescription))."
        }
    }
}

/// Zählt, was die Sitzung wirklich hinausgibt — **für genau eine Anfrage.**
///
/// `@unchecked Sendable`, weil die Sitzung ihn von ihrem eigenen Faden aus ruft: Der eine
/// veränderliche Wert (`bisher`) liegt hinter einer Sperre.
final class Bytezaehler: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    private let sperre = NSLock()
    private var bisher: Int64 = 0
    private let melde: ((Int64, Int64?) -> Void)?

    init(melde: ((Int64, Int64?) -> Void)?) {
        self.melde = melde
    }

    var gesendet: Int64 {
        sperre.lock()
        defer { sperre.unlock() }
        return bisher
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didSendBodyData bytesSent: Int64,
                    totalBytesSent: Int64, totalBytesExpectedToSend: Int64) {
        sperre.lock()
        bisher = totalBytesSent
        sperre.unlock()
        // `NSURLSessionTransferSizeUnknown` (-1) oder 0 heisst: DAS GESAMT IST NICHT BEKANNT.
        melde?(totalBytesSent, totalBytesExpectedToSend > 0 ? totalBytesExpectedToSend : nil)
    }
}
