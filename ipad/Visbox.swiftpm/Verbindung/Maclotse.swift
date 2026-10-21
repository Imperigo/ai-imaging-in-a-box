import CryptoKit
import Foundation
import Security

/// Welches Zertifikat das iPad vom Mac annimmt (Owner-Entscheid 118, 21.10.2026) — **nur das
/// angeheftete.**
///
/// Seit 118 arbeitet das iPad immer über den Mac, verschlüsselt (`https`). Das Zertifikat des
/// Mac ist selbst unterschrieben; das System kann es nicht prüfen, also prüft das iPad: Beim
/// Koppeln heftet es den Fingerabdruck an (aus dem Koppelschein, beim Abtippen aus dem
/// Handschlag mit Gegenprobe, `Macanbindung.pruefeKopplung`), danach nimmt es für die Adresse
/// des Mac **kein anderes** an. Jede andere Adresse (Tailscale, GitHub) prüft das System wie
/// gewohnt.
///
/// Ob ein Zertifikat passt, entscheidet der Kern (`Fingerabdruck.pruefe`); hier steht nur, wie
/// der Fingerabdruck aus dem Handschlag gelesen wird — SHA-256 über die Bytes des
/// Blatt-Zertifikats, dieselbe Rechnung wie am Mac (`Macidentitaet.abdruck`).
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026)* — hier nicht übersetzt.
final class Maclotse: NSObject, URLSessionDelegate, @unchecked Sendable {
    static let gemeinsam = Maclotse()

    private let sperre = NSLock()
    /// Der gekoppelte Mac und sein angehefteter Abdruck.
    private var mac: URL?
    private var angeheftet: String?
    /// Beim Koppeln: diese Adresse lernen — mit dem Abdruck aus dem Schein, wenn es einen gibt.
    private var lernend: [String: String?] = [:]
    private var gesehen: [String: String] = [:]
    /// Wo zuletzt ein Zertifikat abgelehnt wurde — damit der Satz «anderes Zertifikat» heisst
    /// und nicht «abgebrochen».
    private var abgelehnt = Set<String>()

    private static func schluessel(_ host: String, _ port: Int) -> String {
        host.trimmingCharacters(in: CharacterSet(charactersIn: "[]")).lowercased() + ":" + String(port)
    }

    private static func schluessel(_ url: URL) -> String? {
        guard let host = url.host else { return nil }
        return schluessel(host, url.port ?? 443)
    }

    /// Den gekoppelten Mac setzen (oder keinen).
    func setze(mac: URL?, abdruck: String?) {
        sperre.lock()
        self.mac = mac
        self.angeheftet = abdruck
        sperre.unlock()
    }

    /// Ob eine Adresse **der Mac** ist — der gekoppelte oder der, mit dem gerade gekoppelt wird.
    func kennt(_ url: URL) -> Bool {
        guard let s = Maclotse.schluessel(url) else { return false }
        sperre.lock()
        defer { sperre.unlock() }
        if let m = mac, Maclotse.schluessel(m) == s { return true }
        return lernend[s] != nil
    }

    /// Zum Koppeln: diese Adresse lernen, und wenn ein Schein den Abdruck mitbrachte, **nur ihn**
    /// annehmen.
    func lerne(_ url: URL, erwartet: String?) {
        guard let s = Maclotse.schluessel(url) else { return }
        sperre.lock()
        lernend[s] = .some(erwartet)
        gesehen[s] = nil
        abgelehnt.remove(s)
        sperre.unlock()
    }

    /// Was beim Koppeln gesehen wurde — und das Lernen endet.
    func beendeLernen(_ url: URL) -> String? {
        guard let s = Maclotse.schluessel(url) else { return nil }
        sperre.lock()
        defer { sperre.unlock() }
        lernend[s] = nil
        return gesehen.removeValue(forKey: s)
    }

    /// Ob hier eben ein Zertifikat abgelehnt wurde (und vergisst es).
    func nimmAblehnung(_ url: URL) -> Bool {
        guard let s = Maclotse.schluessel(url) else { return false }
        sperre.lock()
        defer { sperre.unlock() }
        return abgelehnt.remove(s) != nil
    }

    // ------------------------------------------------------------------- der Handschlag

    /// Die asynchrone Form, wie am Mac (`Heimvertrauenslotse`).
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge)
        async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        let raum = challenge.protectionSpace
        guard raum.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let vertrauen = raum.serverTrust else {
            return (.performDefaultHandling, nil)
        }
        switch entscheide(Maclotse.schluessel(raum.host, raum.port), abdruck(vertrauen)) {
        case .system: return (.performDefaultHandling, nil)
        case .annehmen: return (.useCredential, URLCredential(trust: vertrauen))
        case .ablehnen: return (.cancelAuthenticationChallenge, nil)
        }
    }

    private enum Entscheid { case system, annehmen, ablehnen }

    /// Eigene Methode, weil eine Sperre in einer `async`-Methode nicht genommen werden soll.
    private func entscheide(_ s: String, _ gesehenJetzt: String?) -> Entscheid {
        sperre.lock()
        defer { sperre.unlock() }
        if let erwartet = lernend[s] {
            // BEIM KOPPELN: Mit Schein nur sein Abdruck; ohne Schein wird gelernt, und die
            // Gegenprobe nach der Antwort entscheidet, ob gemerkt wird.
            if let e = erwartet, Fingerabdruck.pruefe(gesehen: gesehenJetzt, angeheftet: e) != .passt {
                abgelehnt.insert(s)
                return .ablehnen
            }
            if let g = gesehenJetzt { gesehen[s] = g }
            return gesehenJetzt == nil ? .ablehnen : .annehmen
        }
        guard let m = mac, Maclotse.schluessel(m) == s else { return .system }
        switch Fingerabdruck.pruefe(gesehen: gesehenJetzt, angeheftet: angeheftet) {
        case .passt:
            return .annehmen
        case .passtNicht, .systemprueft:
            // OHNE ANGEHEFTETES ZERTIFIKAT SPRICHT DAS IPAD NICHT MIT DEM MAC — `systemprueft`
            // hiesse hier, ein selbst unterschriebenes dem System zu ueberlassen.
            abgelehnt.insert(s)
            return .ablehnen
        }
    }

    private func abdruck(_ vertrauen: SecTrust) -> String? {
        guard let kette = SecTrustCopyCertificateChain(vertrauen) as? [SecCertificate],
              let blatt = kette.first else { return nil }
        let der = SecCertificateCopyData(blatt) as Data
        return Fingerabdruck.hex(Array(SHA256.hash(data: der)))
    }
}
