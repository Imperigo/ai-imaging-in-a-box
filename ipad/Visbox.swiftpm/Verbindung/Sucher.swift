import Foundation
import Network

/// Sucht die HomeStation im Heimnetz — **mit der Bonjour-Suche des Systems, und nur so.**
///
/// Das iPad **sendet selbst keinen Rundruf.** Nach Apples Unterlagen bräuchte eine App, die
/// eigene Rundrufe (Broadcast/Multicast) sendet oder empfängt, eine Sonderberechtigung, die
/// ein kostenloses Konto (Entscheid Nr. 23) nicht bekommt; die Suche über das System
/// braucht sie nicht (Protokoll §8, Aufteilung vom 22.09.2026). Gesucht wird der Dienst aus
/// `Marke.dienst` — derselbe, den das Manifest iOS vorher ankündigt.
///
/// **Was gemeldet wird, entscheidet der Kern** (`Suche.waehle`): eine → die, mehrere → ein
/// Mensch wählt.
///
/// **Der Server kündigt sich an, seit dem 22.09.2026 — aber nur, wenn er mit
/// `--im-heimnetz` läuft** (`oberflaeche/rundruf.py`, Protokoll §8). Bis zum 23.09.2026
/// stand hier, er tue es noch nicht; das war mit dem Bau des Rundrufs überholt. Läuft er
/// ohne die Angabe, findet diese Suche nichts, und die Adresse wird im Koppelbildschirm
/// eingetippt. Ob ein iPad die Ankündigung über die Bonjour-Suche wirklich sieht, ist
/// **am Gerät unbestätigt.**
///
/// *Gebaut, am Gerät unbestätigt* — auch, ob iOS die Suche ohne Sonderberechtigung zulässt.
final class Sucher {
    /// Was gefunden wurde (auch Unaufgelöstes). Kommt auf dem Hauptfaden.
    var meldeGefunden: (([GefundenerDienst]) -> Void)?
    /// `nil`: die Suche läuft ohne Befund; sonst ein Satz, warum sie nicht läuft.
    var meldeZustand: ((String?) -> Void)?

    private let schlange = DispatchQueue(label: "verbindung.sucher")
    private var browser: NWBrowser?
    /// Je Name, was bekannt ist — nur auf `schlange` angefasst.
    private var bekannt: [String: GefundenerDienst] = [:]
    private var aufloesungen: [String: NWConnection] = [:]

    var sucht: Bool { browser != nil }

    func starte() {
        guard browser == nil else { return }
        let parameter = NWParameters()
        parameter.includePeerToPeer = false
        let b = NWBrowser(for: .bonjourWithTXTRecord(type: Marke.dienst, domain: nil),
                          using: parameter)
        b.stateUpdateHandler = { [weak self] zustand in
            self?.zustandGeaendert(zustand)
        }
        b.browseResultsChangedHandler = { [weak self] ergebnisse, _ in
            self?.verarbeite(ergebnisse)
        }
        browser = b
        b.start(queue: schlange)
    }

    func beende() {
        browser?.cancel()
        browser = nil
        schlange.async { [weak self] in
            self?.aufloesungen.values.forEach { $0.cancel() }
            self?.aufloesungen = [:]
            // KEINE AUFLOESUNG AUS EINER FRUEHEREN SUCHE (Demolauf 24.10.2026): Was bekannt war,
            // galt sonst beim naechsten Suchen ungeprueft weiter — samt einer Adresse, die der
            // Mac laengst nicht mehr hat. Jede Suche loest neu auf.
            self?.bekannt = [:]
        }
    }

    // ------------------------------------------------------------ auf `schlange`

    private func zustandGeaendert(_ zustand: NWBrowser.State) {
        let satz: String?
        switch zustand {
        case .ready, .setup:
            satz = nil
        case .waiting(let fehler), .failed(let fehler):
            satz = Sucher.satz(fehler)
        case .cancelled:
            satz = nil
        @unknown default:
            satz = nil
        }
        DispatchQueue.main.async { [weak self] in self?.meldeZustand?(satz) }
    }

    private func verarbeite(_ ergebnisse: Set<NWBrowser.Result>) {
        var jetzt: [String: GefundenerDienst] = [:]
        for ergebnis in ergebnisse {
            guard case .service(let name, _, _, _) = ergebnis.endpoint else { continue }
            var eintraege: [String: String] = [:]
            if case .bonjour(let txt) = ergebnis.metadata {
                eintraege = txt.dictionary
            }
            if let schon = bekannt[name], schon.aufgeloest {
                jetzt[name] = GefundenerDienst(name: name, rechner: schon.rechner,
                                               anschluss: schon.anschluss, eintraege: eintraege)
            } else {
                // DER GRUND VOM LETZTEN VERSUCH BLEIBT STEHEN, waehrend neu aufgeloest wird —
                // sonst sprang die Zeile zwischen «nicht erreicht» und «wird aufgelöst».
                jetzt[name] = GefundenerDienst(name: name, rechner: nil, anschluss: nil,
                                               eintraege: eintraege, grund: bekannt[name]?.grund)
                loeseAuf(ergebnis.endpoint, name: name, eintraege: eintraege)
            }
        }
        bekannt = jetzt
        melde()
    }

    /// Rechner und Anschluss holen: Eine Verbindung zum Dienst aufbauen, ablesen, wohin sie
    /// ging, und sie wieder schliessen. **Nur IPv4** — eine IPv6-Adresse mit Bereich
    /// («fe80::…%en0») ist in einer Adresse für `URLSession` die fehleranfälligere Form.
    private func loeseAuf(_ endpunkt: NWEndpoint, name: String, eintraege: [String: String]) {
        guard aufloesungen[name] == nil else { return }
        let parameter = NWParameters.tcp
        if let ip = parameter.defaultProtocolStack.internetProtocol as? NWProtocolIP.Options {
            ip.version = .v4
        }
        let verbindung = NWConnection(to: endpunkt, using: parameter)
        aufloesungen[name] = verbindung
        verbindung.stateUpdateHandler = { [weak self, weak verbindung] zustand in
            guard let self, let verbindung else { return }
            switch zustand {
            case .ready:
                if case .hostPort(let rechner, let anschluss)? = verbindung.currentPath?.remoteEndpoint {
                    self.bekannt[name] = GefundenerDienst(
                        name: name, rechner: Sucher.text(rechner),
                        anschluss: Int(anschluss.rawValue), eintraege: eintraege)
                    self.melde()
                }
                verbindung.cancel()
                self.aufloesungen[name] = nil
            case .failed, .waiting:
                // NICHT AUFGELOEST BLEIBT NICHT AUFGELOEST — gemeldet wird der Dienst trotzdem,
                // ohne Adresse, und seit dem Geraetetest vom 13.10.2026 MIT GRUND. Bis dahin
                // stand er dann endlos auf «wird aufgelöst …».
                verbindung.cancel()
                self.aufloesungen[name] = nil
                self.gescheitert(name, eintraege: eintraege)
            default:
                break
            }
        }
        verbindung.start(queue: schlange)
        // DIE FRIST (`Suche.aufloesFrist`): Kommt die Verbindung bis dahin nicht zustande,
        // wird sie abgebrochen und der Fund mit Grund gemeldet.
        schlange.asyncAfter(deadline: .now() + Suche.aufloesFrist) { [weak self, weak verbindung] in
            guard let self, let verbindung, self.aufloesungen[name] === verbindung else { return }
            verbindung.cancel()
            self.aufloesungen[name] = nil
            self.gescheitert(name, eintraege: eintraege)
        }
    }

    /// Den Fund ohne Adresse, aber mit Grund melden — nur auf `schlange`.
    private func gescheitert(_ name: String, eintraege: [String: String]) {
        guard bekannt[name]?.aufgeloest != true else { return }
        let ohne = GefundenerDienst(name: name, rechner: nil, anschluss: nil, eintraege: eintraege)
        bekannt[name] = GefundenerDienst(
            name: name, rechner: nil, anschluss: nil, eintraege: eintraege,
            grund: Suche.satzNichtAufgeloest(ueberDenMac: ohne.ueberDenMac))
        melde()
    }

    private func melde() {
        let liste = Array(bekannt.values)
        DispatchQueue.main.async { [weak self] in self?.meldeGefunden?(liste) }
    }

    static func text(_ rechner: NWEndpoint.Host) -> String {
        switch rechner {
        case .name(let name, _): return name
        case .ipv4(let adresse): return "\(adresse)"
        case .ipv6(let adresse): return "\(adresse)"
        @unknown default: return "\(rechner)"
        }
    }

    /// Ein Satz für einen Menschen. `-65570` ist `kDNSServiceErr_PolicyDenied`: Das iPad
    /// darf das Heimnetz nicht durchsuchen (die Freigabe «Lokales Netzwerk» fehlt).
    static func satz(_ fehler: NWError) -> String {
        if case .dns(let code) = fehler, Int(code) == -65570 {
            return "Das iPad darf das Heimnetz nicht durchsuchen. In den Einstellungen unter "
                + "Datenschutz › Lokales Netzwerk erlauben."
        }
        return "Die Suche im Heimnetz läuft nicht (\(fehler.localizedDescription))."
    }
}
