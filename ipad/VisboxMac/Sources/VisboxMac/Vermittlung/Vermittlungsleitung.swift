import Foundation
import Network
import VisboxKern

/// **Eine** Verbindung vom iPad: lesen, an der Tür fragen, beantworten lassen, schreiben,
/// schliessen. Eine Anfrage je Verbindung — wie beim Server auf dem Heim-PC (Protokoll §1).
///
/// Was die Bytes heissen, sagt der Kern (`Anfrageleser`); was mit der Anfrage geschieht,
/// der `Vermittlungsdienst` (und dahinter wieder der Kern). Hier steht nur die Reihenfolge:
///
/// 1. Lesen, bis der **Kopf** da ist.
/// 2. Die **Tür** fragen, bevor der Rumpf gelesen wird — wer nicht angemeldet ist, bekommt
///    seine 401, ohne vier Megabyte geschickt zu haben. Bis die Antwort da ist, wird nicht
///    weitergelesen.
/// 3. Lesen, bis die Anfrage **ganz** ist; die Grenze des Rumpfs prüft der Leser am Kopf.
/// 4. Beantworten lassen und schreiben — oder, wenn ungewiss ist, ob es drüben ankam, **ohne
///    Antwort abbrechen**: Das sagt dem iPad genau das.
///
/// `@unchecked Sendable`: Jeder veränderliche Wert wird nur auf `schlange` angefasst.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
final class Vermittlungsleitung: @unchecked Sendable {
    /// Wie lange das Lesen einer Anfrage dauern darf. Die App schickt eine Skizze in
    /// Sekunden; wer nach 30 s noch nicht fertig ist, hält nur eine Verbindung besetzt.
    static let lesefrist: TimeInterval = 30
    /// Wie lange die ganze Verbindung höchstens lebt — Lesen, Heim-PC (`Heimstrecke.wartezeit`)
    /// und Schreiben zusammen. Danach wird sie ohne Antwort geschlossen.
    static let lebensfrist: TimeInterval = 120

    private let verbindung: NWConnection
    private let schlange: DispatchQueue
    private weak var dienst: Vermittlungsdienst?
    private let register: Leitungsregister

    private var leser = Anfrageleser()
    private var kopfGefragt = false
    private var gelesen = false
    private var vorbei = false
    private var lesewache: DispatchWorkItem?
    private var lebenswache: DispatchWorkItem?

    init(verbindung: NWConnection, schlange: DispatchQueue, dienst: Vermittlungsdienst?,
         register: Leitungsregister) {
        self.verbindung = verbindung
        self.schlange = schlange
        self.dienst = dienst
        self.register = register
    }

    /// Auf `schlange` gerufen (aus dem Annehmen des Anbieters).
    func starte() {
        verbindung.stateUpdateHandler = { [weak self] zustand in
            switch zustand {
            case .failed, .cancelled:
                self?.beende()
            default:
                break
            }
        }
        verbindung.start(queue: schlange)
        let lesen = DispatchWorkItem { [weak self] in self?.beende(abrupt: true) }
        let leben = DispatchWorkItem { [weak self] in self?.beende(abrupt: true) }
        lesewache = lesen
        lebenswache = leben
        schlange.asyncAfter(deadline: .now() + Vermittlungsleitung.lesefrist, execute: lesen)
        schlange.asyncAfter(deadline: .now() + Vermittlungsleitung.lebensfrist, execute: leben)
        lies()
    }

    /// Schliesst die Verbindung. Darf von jedem Faden gerufen werden.
    func beende(abrupt: Bool = false) {
        schlange.async { [self] in
            guard !vorbei else { return }
            vorbei = true
            lesewache?.cancel()
            lebenswache?.cancel()
            // ABRUPT HEISST: ohne geordnetes Ende. Das iPad sieht dann eine abgerissene
            // Verbindung, nicht eine leere Antwort — und eine leere Antwort laese es als
            // «unlesbar», was etwas anderes ist.
            if abrupt { verbindung.forceCancel() } else { verbindung.cancel() }
            register.entferne(self)
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
                lesewache?.cancel()
                bearbeite(anfrage)
                return
            case .mehr:
                if !kopfGefragt, let kopf = leser.kopf {
                    kopfGefragt = true
                    frageTuer(kopf)
                    return
                }
                if let weiter = leser.zwischenantwort() {
                    verbindung.send(content: weiter, completion: .contentProcessed { _ in })
                }
            }
        }
        // DAS IPAD HAT GESCHLOSSEN, BEVOR DIE ANFRAGE GANZ WAR — oder die Leitung riss:
        // Es gibt niemanden mehr, dem man antworten koennte.
        if fertig || fehler != nil {
            beende(abrupt: true)
            return
        }
        lies()
    }

    /// Die Tür am Kopf: Bis sie antwortet, wird **nicht** weitergelesen.
    private func frageTuer(_ kopf: Anfragekopf) {
        let dienst = self.dienst
        Task { @MainActor [weak self] in
            let abweisung = dienst?.vorab(kopf)
            let fehlt = dienst == nil
            self?.schlange.async {
                guard let self, !self.vorbei else { return }
                if fehlt {
                    self.beende(abrupt: true)
                } else if let abweisung {
                    self.gelesen = true
                    self.sende(abweisung)
                } else {
                    if let weiter = self.leser.zwischenantwort() {
                        self.verbindung.send(content: weiter, completion: .contentProcessed { _ in })
                    }
                    self.lies()
                }
            }
        }
    }

    private func bearbeite(_ anfrage: RoheAnfrage) {
        let dienst = self.dienst
        Task { @MainActor [weak self] in
            let antwort = await dienst?.bearbeite(anfrage)
            self?.schlange.async {
                guard let self, !self.vorbei else { return }
                self.sende(antwort)
            }
        }
    }

    /// Schreibt die Antwort und schliesst. `nil`: **ohne Antwort abbrechen.**
    private func sende(_ antwort: Leitungsantwort?) {
        guard !vorbei else { return }
        guard let antwort else {
            beende(abrupt: true)
            return
        }
        verbindung.send(content: antwort.bytes(), contentContext: .finalMessage, isComplete: true,
                        completion: .contentProcessed { [weak self] _ in self?.beende() })
    }
}
