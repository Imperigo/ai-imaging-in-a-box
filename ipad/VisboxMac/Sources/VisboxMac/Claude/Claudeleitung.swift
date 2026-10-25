import Foundation
import Network
import VisboxKern

/// **Eine** Verbindung von Claude: lesen, beantworten lassen, schreiben, schliessen — eine
/// Anfrage je Verbindung, wie die Vermittlung (`Vermittlungsleitung`).
///
/// Was die Bytes heissen, sagt der Kern (`Anfrageleser`, `Mcpleitung.antworte`); hier steht nur
/// die Reihenfolge und die Fristen:
///
/// * der **Kopf** in 5 s, die **ganze Anfrage** in 30 s — wer schweigt, haelt nur einen Platz;
/// * die **ganze Verbindung** hoechstens 120 s: Ein `tools/call` wartet bis zu 45 s auf den
///   Entscheid an der Karte (`Mcp.wartefrist`), dazu Luft.
///
/// Nichts wird protokolliert — weder Kopf noch Rumpf. Was Claude schickt, sind Daten der Mappe.
///
/// `@unchecked Sendable`: Jeder veraenderliche Wert wird nur auf `schlange` angefasst.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
final class Claudeleitung: @unchecked Sendable {
    /// Die Fassung dieser App (Info.plist) — fuer den Kopf `X-App-Fassung` (`Mcpfassungswache`).
    static let fassung = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString")
        as? String ?? "0.0.0"
    static let kopffrist: TimeInterval = 5
    static let lesefrist: TimeInterval = 30
    static let lebensfrist: TimeInterval = Mcp.wartefrist + 75

    private let verbindung: NWConnection
    private let schlange: DispatchQueue
    private let kern: Mcpkern
    private let zaehler: Claudezaehler

    private var leser = Anfrageleser()
    private var gelesen = false
    private var vorbei = false
    private var wachen: [DispatchWorkItem] = []
    /// Die Leitung haelt sich selbst, bis sie vorbei ist — sonst ginge sie mit dem Ende von
    /// `newConnectionHandler` verloren.
    private var selbst: Claudeleitung?

    init(verbindung: NWConnection, schlange: DispatchQueue, kern: Mcpkern,
         zaehler: Claudezaehler) {
        self.verbindung = verbindung
        self.schlange = schlange
        self.kern = kern
        self.zaehler = zaehler
    }

    /// Auf `schlange` gerufen (aus dem Annehmen des Hoerers).
    func starte() {
        selbst = self
        verbindung.stateUpdateHandler = { [weak self] zustand in
            switch zustand {
            case .failed, .cancelled: self?.beende()
            default: break
            }
        }
        verbindung.start(queue: schlange)
        for frist in [Claudeleitung.kopffrist, Claudeleitung.lesefrist, Claudeleitung.lebensfrist] {
            let wache = DispatchWorkItem { [weak self] in
                guard let self else { return }
                // DIE KOPFFRIST GILT NUR, SOLANGE KEIN KOPF DA IST; die Lesefrist nur bis zur
                // ganzen Anfrage. Die Lebensfrist immer.
                if frist == Claudeleitung.kopffrist, self.leser.kopf != nil { return }
                if frist == Claudeleitung.lesefrist, self.gelesen { return }
                self.beende(abrupt: true)
            }
            wachen.append(wache)
            schlange.asyncAfter(deadline: .now() + frist, execute: wache)
        }
        lies()
    }

    /// Schliesst die Verbindung. Darf von jedem Faden gerufen werden.
    func beende(abrupt: Bool = false) {
        schlange.async { [self] in
            guard !vorbei else { return }
            vorbei = true
            wachen.forEach { $0.cancel() }
            wachen = []
            if abrupt { verbindung.forceCancel() } else { verbindung.cancel() }
            zaehler.gib()
            selbst = nil
        }
    }

    // ---------------------------------------------------------- auf `schlange`

    private func lies() {
        guard !vorbei else { return }
        verbindung.receive(minimumIncompleteLength: 1, maximumLength: 64 * 1024) {
            [weak self] daten, _, fertig, fehler in
            self?.empfangen(daten, fertig: fertig, fehler: fehler)
        }
    }

    private func empfangen(_ daten: Data?, fertig: Bool, fehler: NWError?) {
        guard !vorbei, !gelesen else { return }
        if let daten, !daten.isEmpty {
            switch leser.nimm(daten) {
            case .kaputt(let antwort):
                gelesen = true
                sende(antwort)
                return
            case .fertig(let anfrage):
                gelesen = true
                bearbeite(anfrage)
                return
            case .mehr:
                if let weiter = leser.zwischenantwort() {
                    verbindung.send(content: weiter, completion: .contentProcessed { _ in })
                }
            }
        }
        if fertig || fehler != nil {
            beende(abrupt: true)
            return
        }
        lies()
    }

    private func bearbeite(_ anfrage: RoheAnfrage) {
        let kern = self.kern
        Task { [weak self] in
            // FASSUNGSWACHE (0.3.67): die Fassung der App im Kopf — der stdio-Weg vergleicht sie mit seiner.
            let roh = await Mcpleitung.antworte(auf: anfrage, kern: kern)
            let antwort = Mcpfassungswache.mitFassung(roh, Claudeleitung.fassung)
            guard let self else { return }
            self.schlange.async { self.sende(antwort) }
        }
    }

    private func sende(_ antwort: Leitungsantwort) {
        guard !vorbei else { return }
        verbindung.send(content: antwort.bytes(), contentContext: .finalMessage, isComplete: true,
                        completion: .contentProcessed { [weak self] _ in self?.beende() })
    }
}
