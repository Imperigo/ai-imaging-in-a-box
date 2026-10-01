import Foundation
import VisboxKern

/// Die Leitung vom Mac zum Heim-PC — `URLSession`, HTTPS über Tailscale, mit der Anmeldung
/// **des Mac**.
///
/// Was hinausgeht, hat der Kern bestimmt (`Weiterreichung`: Pfad, erlaubte Köpfe, Rumpf;
/// `koepfe(mit:)` setzt die Anmeldung des Mac **an die Stelle** der des iPad). Was
/// zurückkommt, wird hier nur gelesen und als `Heimergebnis` gemeldet; was das iPad davon
/// sieht, entscheidet wieder der Kern (`Vermittlungsregel.antwort`).
///
/// **Flüchtig:** keine Ablage, keine Kekse, kein Zwischenspeicher — ein Bild liegt nur so
/// lange im Arbeitsspeicher, bis es beim iPad ist.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026)* — hier nicht übersetzt.
final class Heimleitung: Sendable {
    /// Wie lange auf den Heim-PC gewartet wird (ohne ein Byte). **Kürzer als die 30 s der
    /// App** (`Sender`): So sagt der Mac «nicht erreicht», bevor das iPad selbst aufgibt
    /// und nur «keine Antwort» weiss.
    static let wartezeit: TimeInterval = 25

    let basis: URL
    private let anmeldung: Anmeldung
    private let sitzung: URLSession

    init(basis: URL, anmeldung: Anmeldung) {
        self.basis = basis
        self.anmeldung = anmeldung
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = Heimleitung.wartezeit
        art.timeoutIntervalForResource = 90
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpCookieStorage = nil
        art.httpShouldSetCookies = false
        art.waitsForConnectivity = false
        sitzung = URLSession(configuration: art)
    }

    /// Reicht eine Anfrage weiter und meldet, was kam.
    func reiche(_ w: Weiterreichung) async -> Heimergebnis {
        guard let adresse = w.adresse(heimBasis: basis) else {
            return .nichtErreicht(grund: "Aus der Adresse des Heim-PC liess sich kein Weg bauen.")
        }
        var auftrag = URLRequest(url: adresse)
        auftrag.httpMethod = w.methode
        for k in w.koepfe(mit: anmeldung) {
            auftrag.setValue(k.wert, forHTTPHeaderField: k.name)
        }
        let zaehler = Heimzaehler()
        do {
            let daten: Data
            let antwort: URLResponse
            if let rumpf = w.rumpf {
                (daten, antwort) = try await sitzung.upload(for: auftrag, from: rumpf, delegate: zaehler)
            } else {
                (daten, antwort) = try await sitzung.data(for: auftrag, delegate: zaehler)
            }
            guard let http = antwort as? HTTPURLResponse else {
                return Heimergebnis.ohneAntwort(
                    grund: "Was vom Heim-PC zurückkam, war keine Antwort.",
                    methode: w.methode, bytesHinaus: zaehler.gesendet)
            }
            var koepfe: [Kopfzeile] = []
            for (name, wert) in http.allHeaderFields {
                if let n = name as? String { koepfe.append(Kopfzeile(n, "\(wert)")) }
            }
            return .antwort(status: http.statusCode, koepfe: koepfe, rumpf: daten)
        } catch {
            // SICHER NICHT GESENDET, wenn die Leitung gar nicht zustande kam — dann zaehlt
            // auch ein Zaehlerstand nicht (bei TLS-Fehlern meldet das System manchmal Bytes).
            let nie = (error as? URLError).map { Heimleitung.vorDemSenden.contains($0.code) } ?? false
            return Heimergebnis.ohneAntwort(grund: Heimleitung.satz(error), methode: w.methode,
                                            bytesHinaus: nie ? 0 : zaehler.gesendet)
        }
    }

    /// Fehler, bei denen die Leitung zum Heim-PC nie stand — **kein Byte** ging hinüber.
    static let vorDemSenden: Set<URLError.Code> = [
        .badURL, .unsupportedURL, .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed,
        .notConnectedToInternet, .secureConnectionFailed, .serverCertificateUntrusted,
        .serverCertificateHasBadDate, .serverCertificateNotYetValid,
        .serverCertificateHasUnknownRoot,
    ]

    /// Ein Satz für einen Menschen — am iPad steht er hinter «erreicht aber den Heim-PC
    /// nicht:».
    static func satz(_ fehler: Error) -> String {
        guard let f = fehler as? URLError else {
            return "Die Verbindung kam nicht zustande (\(fehler.localizedDescription))."
        }
        switch f.code {
        case .cannotFindHost, .dnsLookupFailed:
            return "Seine Adresse ist nicht zu finden — läuft Tailscale auf dem Mac?"
        case .cannotConnectToHost:
            return "Er nimmt keine Verbindung an — läuft der Server dort?"
        case .notConnectedToInternet:
            return "Der Mac ist mit keinem Netz verbunden."
        case .timedOut:
            return "Er hat nicht rechtzeitig geantwortet."
        case .networkConnectionLost:
            return "Die Leitung ist unterwegs abgerissen."
        case .secureConnectionFailed, .serverCertificateUntrusted, .serverCertificateHasBadDate,
             .serverCertificateNotYetValid, .serverCertificateHasUnknownRoot:
            return "Die gesicherte Verbindung kam nicht zustande (Zertifikat)."
        default:
            return "Die Verbindung kam nicht zustande (\(f.localizedDescription))."
        }
    }
}

/// Zählt, was die Sitzung wirklich hinausgibt, und **folgt keiner Umleitung**: Eine
/// Umleitung geht als Antwort zum iPad (der Kern lässt nur einen Pfad am selben Rechner
/// durch), statt dass der Mac selbst irgendwohin geht — mit seinem Kennwort im Gepäck.
final class Heimzaehler: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    private let sperre = NSLock()
    private var bisher: Int64 = 0

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
    }

    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse,
                    newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) {
        completionHandler(nil)
    }
}
