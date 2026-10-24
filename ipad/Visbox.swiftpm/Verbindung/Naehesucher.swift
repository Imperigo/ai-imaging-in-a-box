import Foundation
import MultipeerConnectivity
import UIKit

/// Sucht den Mac in der Nähe, dessen Koppelfenster offen ist — **über MultipeerConnectivity,
/// ohne Entwicklerkonto und nur lokal** (Entscheid 99, Blatt 27).
///
/// Der Ablauf, und **beide Menschen bestätigen**:
///
/// 1. Gesucht wird nur im Koppelbildschirm und nur, solange das iPad nicht gekoppelt ist.
///    Ein Mac zeigt sich nur, solange sein Koppelfenster offen ist (höchstens zwei Minuten).
/// 2. Gefunden → der Koppelbildschirm fragt «Mit diesem Mac koppeln?» mit dessen Namen.
///    «Ablehnen» vergisst ihn für diesen Bildschirm; erst «Annehmen» lädt ihn ein
///    (`Naehekopplung.einladungsvermerk`).
/// 3. Der Mac nimmt die Einladung sofort an — die Sitzung steht, **verschlüsselt**
///    (`.required`), und trägt noch nichts. Dann fragt er «iPad möchte koppeln»; erst dort
///    «Koppeln» gibt den Schein frei (`Naeheabsprache`, seit dem Demolauf vom 24.10.2026).
/// 4. Der Mac schickt den Koppelschein (Adresse und Zahl, nie das Kennwort). Was er heisst,
///    sagt der Kern (`Koppelschein.lies`); danach schliesst das iPad die Sitzung und koppelt
///    **wie beim Abtippen** (`Verbindungsstand.koppele`).
///
/// **Kein `@MainActor` an der Klasse** (wie `Verbindungsstand`): Die Rückrufe von
/// MultipeerConnectivity kommen auf fremden Fäden und gehen von dort mit
/// `DispatchQueue.main` weiter; was veröffentlicht wird, ändert sich nur auf dem Hauptfaden.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — ob iPadOS die Nähe ohne Sonderberechtigung
/// zulässt und wie schnell sich der Mac zeigt, zeigt erst ein Gerät.
final class Naehesucher: NSObject, ObservableObject {

    /// Was der Koppelbildschirm zeigt.
    enum Lage: Equatable {
        case aus
        case sucht
        /// Ein Mac ist da — «Mit diesem Mac koppeln?».
        case gefunden(name: String)
        /// Angenommen; jetzt muss der Mensch am Mac «Koppeln» drücken.
        case wartetAufMac(name: String)
        /// Der Schein ist da (`schein`); das iPad koppelt.
        case erhalten(name: String)
        case fehler(String)
    }

    @Published private(set) var lage: Lage = .aus
    /// Der Schein vom Mac — einmal gesetzt, wenn er geprüft ankam.
    @Published private(set) var schein: Koppelschein?
    /// **Ehrlich, wenn nichts kommt** (20.10.2026, Owner-Befund): sucht / kein Mac nach 30 s /
    /// startet nicht. Entschieden im Kern (`Naehekopplung.suchstand`); hier nur die Uhr.
    @Published private(set) var suchstand: Naehesuchstand = .sucht
    /// Seit wann gesucht wird — `nil`, wenn nicht.
    private var suchtSeit: Date?
    /// Warum die Suche nicht startet (`didNotStartBrowsingForPeers`).
    private var suchfehler: String?

    /// Wie sich dieses iPad am Mac zeigt — angelegt beim ersten Suchen, auf dem Hauptfaden
    /// (`UIDevice` gehört dorthin). Seit iPadOS 16 nennt das System ohne Sonderberechtigung
    /// nur «iPad», nicht den Namen, den man dem Gerät gab.
    private var ich: MCPeerID?
    private var sucher: MCNearbyServiceBrowser?
    private var sitzung: MCSession?
    /// Die Macs, die sich gerade zeigen, in der Reihenfolge des Findens.
    private var funde: [MCPeerID] = []
    /// Was der Mensch hier schon abgelehnt hat — gilt, bis der Bildschirm wieder aufgeht.
    private var abgelehnt: Set<MCPeerID> = []
    /// Der Mac, den der Mensch angenommen hat.
    private var gewaehlt: MCPeerID?
    /// Der laufende Versuch nach «Annehmen» — was ein «nicht verbunden» heisst, sagt der Kern
    /// (`Naeheeinladung`, Demolauf 24.10.2026).
    private var einladung: Naeheeinladung?

    // ------------------------------------------------------------ vom Bildschirm

    @MainActor
    func starte() {
        guard sucher == nil else { return }
        funde = []
        abgelehnt = []
        gewaehlt = nil
        schein = nil
        let peer = ich ?? MCPeerID(displayName: Naehekopplung.anzeigename(UIDevice.current.name,
                                                                         ersatz: "iPad"))
        ich = peer
        let s = MCNearbyServiceBrowser(peer: peer, serviceType: Naehekopplung.dienstart)
        s.delegate = self
        sucher = s
        lage = .sucht
        suchtSeit = Date()
        suchfehler = nil
        aktualisiereSuchstand()
        s.startBrowsingForPeers()
        // NACH DER FRIST NACHSEHEN, ob etwas kam — eine Uhr genuegt, ein Takt waere zu viel.
        DispatchQueue.main.asyncAfter(deadline: .now() + Naehekopplung.ohneFundNach + 0.5) {
            [weak self] in self?.aktualisiereSuchstand()
        }
    }

    /// Den Stand der Suche neu bestimmen (Kern).
    private func aktualisiereSuchstand() {
        let neu = Naehekopplung.suchstand(seit: suchtSeit, jetzt: Date(),
                                          gefunden: !funde.isEmpty || gewaehlt != nil,
                                          fehler: suchfehler)
        if neu != suchstand { suchstand = neu }
    }

    @MainActor
    func beende() {
        sucher?.stopBrowsingForPeers()
        sucher?.delegate = nil
        sucher = nil
        sitzung?.delegate = nil
        sitzung?.disconnect()
        sitzung = nil
        funde = []
        gewaehlt = nil
        einladung = nil
        suchtSeit = nil
        suchfehler = nil
        suchstand = .sucht
        lage = .aus
    }

    /// «Annehmen»: den gezeigten Mac einladen — **erst jetzt**, und mit dem Vermerk, dass ein
    /// Mensch am iPad angenommen hat.
    @MainActor
    func nimmAn() {
        guard case .gefunden(let name) = lage, let mac = naechster, sucher != nil,
              ich != nil else { return }
        gewaehlt = mac
        einladung = Naeheeinladung(jetzt: Date().timeIntervalSince1970)
        lage = .wartetAufMac(name: name)
        lade(mac)
        // DIE FRISTEN NACHSEHEN (Kern: `Naeheeinladung.uhr`): bis die Sitzung steht, und bis
        // das Fenster am Mac zugeht. Eine Uhr je Frist genuegt.
        for frist in [Naeheeinladung.verbindenHoechstens, Naehekopplung.fenster] {
            DispatchQueue.main.asyncAfter(deadline: .now() + frist + 0.5) { [weak self] in
                self?.pruefeFrist()
            }
        }
    }

    /// Den Mac einladen — **die eine Stelle**, an der das iPad einlädt, immer mit dem Vermerk und
    /// immer mit einer frischen Sitzung. Eine alte, die nicht trug, geht vorher weg.
    private func lade(_ mac: MCPeerID) {
        guard let sucher, let ich else { return }
        sitzung?.delegate = nil
        sitzung?.disconnect()
        let s = MCSession(peer: ich, securityIdentity: nil, encryptionPreference: .required)
        s.delegate = self
        sitzung = s
        // DIE FRIST DER EINLADUNG ist die bis zur stehenden Sitzung: Der Mac antwortet seit dem
        // 24.10.2026 sofort und fragt den Menschen erst danach.
        sucher.invitePeer(mac, to: s, withContext: Naehekopplung.einladungsvermerk,
                          timeout: Naeheeinladung.verbindenHoechstens)
    }

    /// «Ablehnen»: diesen Mac für diesen Bildschirm vergessen.
    @MainActor
    func lehneAb() {
        guard let mac = naechster else { return }
        abgelehnt.insert(mac)
        zeigeNaechsten()
    }

    // ------------------------------------------------------------ auf dem Hauptfaden

    private var naechster: MCPeerID? {
        funde.first { !abgelehnt.contains($0) }
    }

    private func zeigeNaechsten() {
        guard gewaehlt == nil else { return }
        if let mac = naechster {
            lage = .gefunden(name: mac.displayName)
        } else if sucher != nil {
            lage = .sucht
        }
    }

    private func gefunden(_ mac: MCPeerID) {
        guard !funde.contains(mac) else { return }
        funde.append(mac)
        zeigeNaechsten()
        aktualisiereSuchstand()
    }

    private func verloren(_ mac: MCPeerID) {
        funde.removeAll { $0 == mac }
        // DER GEWAEHLTE BLEIBT: Hoert er auf, sich anzubieten, waehrend die Einladung laeuft,
        // sagt das die Sitzung (`notConnected`), nicht die Suche.
        zeigeNaechsten()
    }

    private func angekommen(_ daten: Data, von mac: MCPeerID) {
        guard mac == gewaehlt, schein == nil else { return }
        einladung?.scheinDa()
        let name = mac.displayName
        // DIE SITZUNG IST NACH DEM SCHEIN FERTIG — sie traegt nichts anderes.
        sitzung?.disconnect()
        switch Koppelschein.lies(daten, jetzt: Date().timeIntervalSince1970) {
        case .gut(let s):
            sucher?.stopBrowsingForPeers()
            schein = s
            lage = .erhalten(name: name)
        case .schlecht(let satz):
            gewaehlt = nil
            einladung = nil
            lage = .fehler(satz)
        }
    }

    private func verbunden(_ mac: MCPeerID, in s: MCSession) {
        guard mac == gewaehlt, s === sitzung, schein == nil else { return }
        einladung?.sitzungSteht()
    }

    /// «Nicht verbunden» — **keine Absage, solange die Sitzung nie stand** (Demolauf
    /// 24.10.2026). Was es heisst, sagt der Kern.
    private func getrennt(_ mac: MCPeerID, in s: MCSession) {
        guard mac == gewaehlt, s === sitzung, schein == nil, var e = einladung else { return }
        let folge = e.getrennt(jetzt: Date().timeIntervalSince1970)
        einladung = e
        befolge(folge, mac)
    }

    private func pruefeFrist() {
        guard let mac = gewaehlt, schein == nil, var e = einladung else { return }
        let folge = e.uhr(jetzt: Date().timeIntervalSince1970)
        einladung = e
        befolge(folge, mac)
    }

    private func befolge(_ folge: Naeheeinladung.Folge, _ mac: MCPeerID) {
        switch folge {
        case .warten:
            break
        case .neuEinladen:
            DispatchQueue.main.asyncAfter(deadline: .now() + Naeheeinladung.neuEinladenNach) {
                [weak self] in
                guard let self, self.gewaehlt == mac, self.schein == nil,
                      self.einladung?.erledigt == false else { return }
                self.lade(mac)
            }
        case .aufgeben(let satz):
            sitzung?.delegate = nil
            sitzung?.disconnect()
            sitzung = nil
            gewaehlt = nil
            einladung = nil
            abgelehnt.insert(mac)
            lage = .fehler(satz)
        }
    }
}

// ------------------------------------------------------------ Rückrufe (fremde Fäden)

extension Naehesucher: MCNearbyServiceBrowserDelegate {
    func browser(_ browser: MCNearbyServiceBrowser, foundPeer peerID: MCPeerID,
                 withDiscoveryInfo info: [String: String]?) {
        DispatchQueue.main.async { [weak self] in self?.gefunden(peerID) }
    }

    func browser(_ browser: MCNearbyServiceBrowser, lostPeer peerID: MCPeerID) {
        DispatchQueue.main.async { [weak self] in self?.verloren(peerID) }
    }

    func browser(_ browser: MCNearbyServiceBrowser, didNotStartBrowsingForPeers error: Error) {
        let grund = error.localizedDescription
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            self.suchfehler = grund
            self.aktualisiereSuchstand()
            self.lage = .fehler(self.suchstand.satz)
        }
    }
}

extension Naehesucher: MCSessionDelegate {
    func session(_ session: MCSession, peer peerID: MCPeerID, didChange state: MCSessionState) {
        DispatchQueue.main.async { [weak self] in
            switch state {
            case .connected: self?.verbunden(peerID, in: session)
            case .notConnected: self?.getrennt(peerID, in: session)
            default: break
            }
        }
    }

    func session(_ session: MCSession, didReceive data: Data, fromPeer peerID: MCPeerID) {
        DispatchQueue.main.async { [weak self] in self?.angekommen(data, von: peerID) }
    }

    // NICHTS ANDERES WIRD ANGENOMMEN: kein Strom, keine Datei — der Schein ist eine kurze
    // Nachricht. Was so ankommt, bleibt liegen und wird vom System verworfen.
    func session(_ session: MCSession, didReceive stream: InputStream, withName streamName: String,
                 fromPeer peerID: MCPeerID) {
        stream.close()
    }

    func session(_ session: MCSession, didStartReceivingResourceWithName resourceName: String,
                 fromPeer peerID: MCPeerID, with progress: Progress) {
        progress.cancel()
    }

    func session(_ session: MCSession, didFinishReceivingResourceWithName resourceName: String,
                 fromPeer peerID: MCPeerID, at localURL: URL?, withError error: Error?) {}
}
