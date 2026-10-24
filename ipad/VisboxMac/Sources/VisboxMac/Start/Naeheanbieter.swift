import Foundation
import MultipeerConnectivity
import VisboxKern

/// Der Mac bietet sich dem iPad in der Nähe an — **nur im offenen Koppelfenster, höchstens
/// zwei Minuten** (Entscheide 99/99a, Blatt 27).
///
/// * **Angeboten wird nur, solange das Fenster offen ist.** `biete(_:)` beginnt, `halte()`
///   hört auf; das Koppelfenster ruft `halte()`, sobald seine zwei Minuten um sind, und
///   beim Schliessen. Danach sieht kein iPad den Mac mehr.
/// * **Beide bestätigen** (`Naeheabsprache` im Kern): Eine Einladung ohne den Vermerk des
///   iPad wird abgelehnt, ohne zu fragen. Mit Vermerk nimmt der Mac sie **sofort** an — die
///   Sitzung steht, und es geht nichts hinaus —, dann fragt das Fenster «iPad möchte koppeln»;
///   erst «Koppeln» schickt den Schein. «Ablehnen» schliesst die Sitzung ohne Schein.
///   *Seit dem Demolauf vom 24.10.2026:* Bis dahin wurde die Einladung erst nach dem Klick
///   beantwortet; MultipeerConnectivity wartete darauf nicht, und das iPad gab nach rund drei
///   Sekunden auf.
/// * **Verschlüsselt** (`.required`) — eine Sitzung ohne Verschlüsselung kommt nicht zustande.
/// * **Gesendet wird nur der Koppelschein** — Adresse und Zahl, **nie** das Kennwort des
///   Heim-PC (Entscheid 99). Diese Klasse kennt es nicht einmal: Sie bekommt nur den Schein.
///   Danach schliesst sie die Sitzung und hört auf, sich anzubieten — die Zahl ist einmalig.
///
/// Nicht in `Vermittlung/`: Die Vermittlung (§8b) ist ein anderer Weg und bleibt bei
/// Foundation, Network und Security.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
final class Naeheanbieter: NSObject, ObservableObject {

    enum Lage: Equatable {
        case aus
        /// Das Fenster ist offen; der Mac zeigt sich unter diesem Namen.
        case bietetAn(name: String)
        /// Ein iPad hat angenommen — «iPad möchte koppeln».
        case ipadFragt(name: String)
        /// «Koppeln» gedrückt; die Sitzung baut sich auf.
        case verbindet(name: String)
        /// Der Schein ist beim iPad; es koppelt jetzt selbst.
        case gesendet(name: String)
        case fehler(String)
    }

    @Published private(set) var lage: Lage = .aus
    /// Was die kleine Zeile im Koppelfenster sagt (20.10.2026, Owner-Befund: über die Nähe
    /// geschah nichts, und keine Seite sagte es) — `nil`, solange nicht angeboten wird. Den
    /// Satz bestimmt der Kern (`Naeheanbieterstand.zeile`).
    @Published private(set) var stand: Naeheanbieterstand?

    private var ich: MCPeerID?
    private var anbieter: MCNearbyServiceAdvertiser?
    private var sitzung: MCSession?
    private var schein: Koppelschein?
    private var fenster: Koppelfenster?
    private var absprache = Naeheabsprache()
    /// Das iPad, das gerade fragt — seine Einladung ist schon angenommen, die Sitzung steht oder
    /// baut sich auf.
    private var fragender: MCPeerID?

    // ------------------------------------------------------------ vom Koppelfenster

    /// Beginnt, sich anzubieten — mit diesem Schein, in diesem Fenster.
    @MainActor
    func biete(_ neu: Koppelschein, fenster offen: Koppelfenster) {
        halte()
        schein = neu
        fenster = offen
        absprache = Naeheabsprache()
        let peer = ich ?? MCPeerID(displayName: Naehekopplung.anzeigename(
            Host.current().localizedName ?? "", ersatz: "Mac"))
        ich = peer
        let a = MCNearbyServiceAdvertiser(peer: peer, discoveryInfo: nil,
                                          serviceType: Naehekopplung.dienstart)
        a.delegate = self
        anbieter = a
        a.startAdvertisingPeer()
        lage = .bietetAn(name: peer.displayName)
        stand = .bietetAn(name: peer.displayName)
    }

    /// Hört auf, sich anzubieten, lehnt eine offene Frage ab und schliesst die Sitzung.
    @MainActor
    func halte() {
        anbieter?.stopAdvertisingPeer()
        anbieter?.delegate = nil
        anbieter = nil
        fragender = nil
        sitzung?.disconnect()
        sitzung?.delegate = nil
        sitzung = nil
        schein = nil
        fenster = nil
        stand = nil
        if case .gesendet = lage { return }
        lage = .aus
    }

    /// «Koppeln» am Mac — erst jetzt geht der Schein hinaus, über die stehende Sitzung.
    @MainActor
    func koppeln() {
        guard let peer = fragender, let s = sitzung else { return }
        absprache.macSagtKoppeln()
        guard absprache.macKoppelt else { return }
        sendeSchein(an: peer, in: s)
    }

    /// «Ablehnen» am Mac: Die Sitzung geht zu, **ohne Schein** — das iPad liest das als Absage
    /// (`Naeheeinladung`). Das Fenster bietet sich weiter an.
    @MainActor
    func lehneAb() {
        let alt = sitzung
        sitzung?.delegate = nil
        sitzung = nil
        fragender = nil
        alt?.disconnect()
        absprache = Naeheabsprache()
        if let ich, anbieter != nil {
            lage = .bietetAn(name: ich.displayName)
            stand = .bietetAn(name: ich.displayName)
        }
    }

    // ------------------------------------------------------------ auf dem Hauptfaden

    private func eingeladen(von peer: MCPeerID, vermerk: Data?,
                            antworte: @escaping (Bool, MCSession?) -> Void) {
        // EINE FRAGE ZUR ZEIT, und nur mit Vermerk und offenem Fenster. Alles andere wird
        // abgelehnt, ohne den Menschen am Mac zu stoeren.
        let offen = fenster?.offen(jetzt: Date().timeIntervalSince1970) ?? false
        guard let ich, anbieter != nil, offen else {
            antworte(false, nil)
            return
        }
        // DASSELBE IPAD LAEDT NEU EIN, weil seine erste Sitzung nicht zustande kam (Kern:
        // `Naeheeinladung`): Die alte, die nie stand, geht weg, die neue wird angenommen.
        if let alt = fragender, alt == peer, !absprache.verbunden {
            sitzung?.delegate = nil
            sitzung?.disconnect()
            sitzung = nil
            fragender = nil
        }
        guard fragender == nil, sitzung == nil else {
            antworte(false, nil)
            return
        }
        var neu = Naeheabsprache()
        guard neu.einladung(vermerk: vermerk) else {
            antworte(false, nil)
            return
        }
        let s = MCSession(peer: ich, securityIdentity: nil, encryptionPreference: .required)
        s.delegate = self
        absprache = neu
        fragender = peer
        sitzung = s
        lage = .verbindet(name: peer.displayName)
        // SOFORT ANGENOMMEN (Demolauf 24.10.2026): Die Maschine antwortet der Maschine, bevor
        // MultipeerConnectivity die Einladung verfallen laesst. Der Mensch wird gefragt, sobald
        // die Sitzung steht (`verbunden`) — und erst sein «Koppeln» gibt den Schein frei.
        antworte(true, s)
    }

    private func verbunden(_ peer: MCPeerID, in s: MCSession) {
        guard peer == fragender, s === sitzung, !absprache.verbunden else { return }
        absprache.sitzungSteht()
        // ERST JETZT FRAGT DER MAC DEN MENSCHEN — das iPad ist wirklich da, verschluesselt.
        lage = .ipadFragt(name: peer.displayName)
        stand = .anfrage(name: peer.displayName)
    }

    private func sendeSchein(an peer: MCPeerID, in s: MCSession) {
        guard let schein else { return }
        let offen = fenster?.offen(jetzt: Date().timeIntervalSince1970) ?? false
        // DIE EINE STELLE, AN DER ETWAS HINAUSGEHT — und nur der Schein. Ob es darf, sagt
        // der Kern: beide bestaetigt, verbunden, verschluesselt, im offenen Fenster, einmal.
        guard absprache.darfSenden(verschluesselt: s.encryptionPreference == .required,
                                   fensterOffen: offen) else {
            s.disconnect()
            return
        }
        do {
            try s.send(schein.daten, toPeers: [peer], with: .reliable)
        } catch {
            lage = .fehler("Der Schein ging nicht ans iPad (\(error.localizedDescription)). "
                           + "Am iPad «Neu suchen», oder den QR-Code lesen.")
            s.disconnect()
            return
        }
        absprache.hatGesendet()
        let name = peer.displayName
        lage = .gesendet(name: name)
        // DIE ZAHL IST EINMALIG: Kein zweites iPad soll den Mac jetzt noch sehen. Die Sitzung
        // bleibt einen Augenblick, damit der Schein ankommt; das iPad schliesst sie selbst.
        anbieter?.stopAdvertisingPeer()
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self, weak s] in
            s?.disconnect()
            if self?.sitzung === s { self?.sitzung = nil }
        }
    }

    private func getrennt(_ peer: MCPeerID, in s: MCSession) {
        guard peer == fragender, s === sitzung else { return }
        sitzung = nil
        fragender = nil
        if absprache.gesendet { return }
        let hatteSitzung = absprache.verbunden
        absprache = Naeheabsprache()
        // STAND DIE SITZUNG NIE, laedt das iPad selbst neu ein oder sagt es (Kern:
        // `Naeheeinladung`) — der Mac bietet sich still weiter an, statt rot zu melden.
        guard hatteSitzung else {
            if let ich, anbieter != nil {
                lage = .bietetAn(name: ich.displayName)
                stand = .bietetAn(name: ich.displayName)
            }
            return
        }
        lage = .fehler("Die Verbindung zum iPad kam nicht zustande. Am iPad «Neu suchen».")
        // DAS FENSTER BIETET SICH WEITER AN, solange es offen ist.
        if let ich, anbieter != nil {
            DispatchQueue.main.asyncAfter(deadline: .now() + 4) { [weak self] in
                guard let self, self.anbieter != nil, self.fragender == nil,
                      case .fehler = self.lage else { return }
                self.lage = .bietetAn(name: ich.displayName)
                self.stand = .bietetAn(name: ich.displayName)
            }
        }
    }
}

// ------------------------------------------------------------ Rückrufe (fremde Fäden)

extension Naeheanbieter: MCNearbyServiceAdvertiserDelegate {
    func advertiser(_ advertiser: MCNearbyServiceAdvertiser,
                    didReceiveInvitationFromPeer peerID: MCPeerID, withContext context: Data?,
                    invitationHandler: @escaping (Bool, MCSession?) -> Void) {
        DispatchQueue.main.async { [weak self] in
            guard let self else {
                invitationHandler(false, nil)
                return
            }
            self.eingeladen(von: peerID, vermerk: context, antworte: invitationHandler)
        }
    }

    func advertiser(_ advertiser: MCNearbyServiceAdvertiser,
                    didNotStartAdvertisingPeer error: Error) {
        let satz = "Der Mac zeigt sich dem iPad nicht (\(error.localizedDescription)). "
            + "Den QR-Code lesen oder die Zahl eintippen."
        let grund = error.localizedDescription
        DispatchQueue.main.async { [weak self] in
            self?.lage = .fehler(satz)
            self?.stand = .gehtNicht(grund: grund)
        }
    }
}

extension Naeheanbieter: MCSessionDelegate {
    func session(_ session: MCSession, peer peerID: MCPeerID, didChange state: MCSessionState) {
        DispatchQueue.main.async { [weak self] in
            switch state {
            case .connected: self?.verbunden(peerID, in: session)
            case .notConnected: self?.getrennt(peerID, in: session)
            default: break
            }
        }
    }

    // DER MAC NIMMT NICHTS AN: Das iPad hat ihm nichts zu schicken.
    func session(_ session: MCSession, didReceive data: Data, fromPeer peerID: MCPeerID) {}

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
