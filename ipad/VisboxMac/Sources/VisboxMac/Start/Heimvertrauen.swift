import CryptoKit
import Foundation
import Security
import VisboxKern

/// Welches Zertifikat der Mac vom Heim-PC annimmt (Entscheid 83b, 13.10.2026).
///
/// * **Über Tailscale** ist nichts angeheftet: Das Zertifikat von Tailscale Serve prüft das
///   System wie jedes andere (`performDefaultHandling`).
/// * **Im Heim-WLAN** ist das Zertifikat selbst unterschrieben; der Mac nimmt dort **nur
///   das angeheftete** an — das, dessen Fingerabdruck er bei der Kopplung sah
///   (`Heimgedaechtnis.fingerabdruck`). Ein anderes wird abgelehnt, auch wenn es sonst gültig
///   aussähe.
///
/// Ob ein Zertifikat passt, entscheidet der Kern (`Fingerabdruck.pruefe`, mit Proben); hier
/// steht nur, wie der Fingerabdruck aus dem Handschlag gelesen wird: SHA-256 über die Bytes
/// des Blatt-Zertifikats — dieselbe Rechnung wie am Heim-PC (`heimnetz.fingerabdruck`).
///
/// *Gebaut, am Gerät unbestätigt (13.10.2026).*
enum Heimvertrauen {

    /// Der Fingerabdruck des Zertifikats, das der Server im Handschlag zeigt.
    static func fingerabdruck(_ vertrauen: SecTrust) -> String? {
        guard let kette = SecTrustCopyCertificateChain(vertrauen) as? [SecCertificate],
              let blatt = kette.first else { return nil }
        let der = SecCertificateCopyData(blatt) as Data
        return Fingerabdruck.hex(Array(SHA256.hash(data: der)))
    }

    /// Der angeheftete Fingerabdruck **für diesen Rechner und Anschluss** — nur, wenn es der
    /// eingerichtete Heim-PC ist.
    static func angeheftet(host: String, port: Int) -> String? {
        guard let basis = Heimgedaechtnis.adresse,
              basis.host?.lowercased() == host.lowercased(),
              (basis.port ?? 443) == port else { return nil }
        return Heimgedaechtnis.fingerabdruck
    }

    /// Die Antwort auf eine Herausforderung des Servers.
    static func entscheide(_ herausforderung: URLAuthenticationChallenge)
        -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        let raum = herausforderung.protectionSpace
        guard raum.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let vertrauen = raum.serverTrust else {
            return (.performDefaultHandling, nil)
        }
        let gemerkt = angeheftet(host: raum.host, port: raum.port)
        switch Fingerabdruck.pruefe(gesehen: fingerabdruck(vertrauen), angeheftet: gemerkt) {
        case .systemprueft:
            return (.performDefaultHandling, nil)
        case .passt:
            return (.useCredential, URLCredential(trust: vertrauen))
        case .passtNicht:
            return (.cancelAuthenticationChallenge, nil)
        }
    }
}

/// Der Lotse für jede `URLSession` zum eingerichteten Heim-PC — Heimleitung, Assistent,
/// Vermittlung. **Einer für alle**, damit die Regel an einer Stelle steht.
final class Heimvertrauenslotse: NSObject, URLSessionDelegate, @unchecked Sendable {
    static let gemeinsam = Heimvertrauenslotse()

    // DIE ASYNCHRONE FORM, nicht die mit Rueckruf: Deren Rueckruf traegt im SDK von Xcode 16
    // eine Akteur-Angabe, die eine Abschrift ohne sie bemaengelt (Warnung im Lauf vom
    // 13.10.2026; in Swift 6 ein Fehler).
    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge)
        async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        Heimvertrauen.entscheide(challenge)
    }
}

/// Der Lotse **der Suche** — er lernt, statt zu prüfen, und nur für Kandidaten im WLAN.
///
/// Vertrauen beim ersten Mal (Entscheid 83b): Für `hallo`, `anfordern` und `verbinden` an
/// einen Heim-PC im WLAN nimmt die Suche sein selbst unterschriebenes Zertifikat an und
/// **merkt sich, welches es war.** Angeheftet wird es erst nach einer gelungenen Kopplung,
/// und nur, wenn der Heim-PC denselben Fingerabdruck nennt (`Verbindungsergebnis.lies`).
/// Abgesichert ist dieser erste Schritt durch die Zahl, die nur am Bildschirm des Heim-PC
/// steht — und, wer will, durch das Zeichen auf beiden Bildschirmen.
///
/// Für jeden anderen Rechner (Tailscale) prüft das System wie gewohnt.
final class Lernlotse: NSObject, URLSessionDelegate, @unchecked Sendable {
    private let sperre = NSLock()
    private var imWlan = Set<String>()
    private var gesehen: [String: String] = [:]

    private static func schluessel(_ host: String, _ port: Int) -> String {
        host.lowercased() + ":" + String(port)
    }

    /// Diesen Kandidaten im WLAN zulassen.
    func lasseZu(_ url: URL) {
        guard let host = url.host else { return }
        sperre.lock()
        imWlan.insert(Self.schluessel(host, url.port ?? 443))
        sperre.unlock()
    }

    /// Was zuletzt bei diesem Kandidaten gesehen wurde.
    func gesehen(_ url: URL) -> String? {
        guard let host = url.host else { return nil }
        sperre.lock()
        defer { sperre.unlock() }
        return gesehen[Self.schluessel(host, url.port ?? 443)]
    }

    func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge)
        async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
        let raum = challenge.protectionSpace
        guard raum.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let vertrauen = raum.serverTrust else {
            return (.performDefaultHandling, nil)
        }
        let s = Self.schluessel(raum.host, raum.port)
        guard merke(s, vertrauen) else { return (.performDefaultHandling, nil) }
        return (.useCredential, URLCredential(trust: vertrauen))
    }

    /// Merkt den Fingerabdruck, wenn der Kandidat im WLAN zugelassen ist — `false` sonst.
    /// Eigene Methode, weil eine Sperre in einer `async`-Methode nicht genommen werden soll.
    private func merke(_ s: String, _ vertrauen: SecTrust) -> Bool {
        sperre.lock()
        defer { sperre.unlock() }
        guard imWlan.contains(s), let abdruck = Heimvertrauen.fingerabdruck(vertrauen) else {
            return false
        }
        gesehen[s] = abdruck
        return true
    }
}
