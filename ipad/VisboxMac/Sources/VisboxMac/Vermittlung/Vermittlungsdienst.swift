import Foundation
import Network
import VisboxKern

/// Der Mac als Vermittler für das iPad (Entscheide 42/47, Protokoll §8b): **er bietet sich
/// im WLAN an wie der Heim-PC zuhause und reicht durch.**
///
/// Unterwegs erreicht das iPad den Heim-PC nicht — der ist nur über Tailscale erreichbar,
/// und das läuft auf dem iPad nicht. Der Mac schon. Er bietet darum denselben Dienst an
/// (`Marke.dienst`, TXT `fassung=1` und `vermittler=mac`), nimmt die Anfragen des iPad an und
/// reicht sie an den Heim-PC weiter, mit **seinem** Kennwort. Die App findet ihn, wie sie
/// heute die HomeStation findet.
///
/// **Was hier entschieden wird, entscheidet nicht diese Klasse**, sondern der Kern
/// (`Vermittlerstand`, `Vermittlungsregel`, `Anfrageleser` — mit Proben unter Linux). Hier
/// steht nur, was das Netz braucht: anbieten (`NWListener`), Verbindungen annehmen
/// (`Vermittlungsleitung`), weiterreichen (`Heimleitung`), und die Zeile «iPad» nachführen.
///
/// **Was hier nie geschieht:** kein Bild zwischenspeichern (die Antwort liegt nur im
/// Arbeitsspeicher, bis sie hinaus ist), keine Anfrage protokollieren — weder Kopf noch
/// Rumpf, auch nicht den Pfad. *Ein Protokoll, das niemand liest, liest irgendwann jemand
/// anderes.*
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026)* — hier nicht übersetzt (Linux kennt
/// `Network` nicht).
@MainActor
final class Vermittlungsdienst: ObservableObject {

    /// Was die Startzeile «iPad» sagt (`wort`: steht / lädt / wartet / fehlt, und `satz`).
    @Published private(set) var zeile: Vermittlerlage = .startet
    /// Die Zahl zum Koppeln, solange sie gilt — für den Bildschirm des Mac, nirgends sonst.
    @Published private(set) var koppelzahl: String?
    /// Der genaue Grund des letzten abgelehnten Koppelversuchs — nur für den Menschen am Mac.
    @Published private(set) var koppelgrund: String?
    /// Ein Hinweis zum Zugang des iPad (der Schlüsselbund nahm ihn nicht) — `nil`: alles gut.
    @Published private(set) var hinweis: String?

    /// Wie viele Verbindungen zugleich offen sein dürfen. Die App öffnet wenige (Prüfen,
    /// Mappe, ein paar Bilder); mehr ist kein iPad, sondern ein Fremder im WLAN.
    nonisolated static let hoechstensLeitungen = 16

    /// Unter diesem Schlüssel merkt sich der Mac, **dass** schon ein iPad gekoppelt hat —
    /// kein Geheimnis, nur der Anlass, beim Start keine Zahl mehr zu zeigen.
    private static let gekoppeltSchluessel = "vermittlung.ipadGekoppelt"

    private let heim: Heimleitung
    private var stand: Vermittlerstand
    private let schlange = DispatchQueue(label: "vermittlung.leitungen")
    private let register = Leitungsregister()
    private var hoerer: NWListener?
    private var uhr: Task<Void, Never>?
    private var bereit = false
    private var fehler: String?
    /// Ob der feste Anschluss schon versucht wurde — belegt, dann ein freier.
    private var aufFestemAnschluss = true

    /// - Parameters:
    ///   - heimBasis: der Heim-PC im eigenen Tailscale-Netz, `https://<rechner>.<netz>.ts.net:8443`.
    ///   - benutzer, kennwort: die Anmeldung **des Mac** am Heim-PC (aus seinem Schlüsselbund).
    ///     Sie geht nur zum Heim-PC, nie zum iPad.
    init(heimBasis: URL, benutzer: String, kennwort: String) {
        heim = Heimleitung(basis: heimBasis,
                           anmeldung: Anmeldung(benutzer: benutzer, kennwort: kennwort))
        let (zugang, satz) = Vermittlerschluessel.liesOderErzeuge()
        stand = Vermittlerstand(zugang: zugang)
        // KANN DER MAC SICH DEN ZUGANG NICHT MERKEN, geht es trotzdem — nur muss das iPad
        // nach jedem Neustart neu koppeln. Das steht dann im Hinweis, statt still zu fehlen.
        hinweis = satz
    }

    // ------------------------------------------------------------------- Handgriffe

    /// Bietet sich im WLAN an. Hat noch nie ein iPad gekoppelt, zeigt er gleich eine Zahl.
    func starte() {
        guard hoerer == nil else { return }
        fehler = nil
        bereit = false
        aufFestemAnschluss = true
        if !UserDefaults.standard.bool(forKey: Self.gekoppeltSchluessel) {
            stand.oeffneKopplung(jetzt: Vermittlerkopplung.stetigeUhr)
        }
        biete()
        uhr?.cancel()
        // DIE ZEILE GEHT MIT DER ZEIT: «vor 4 s» wird «vor 5 s», eine Zahl laeuft ab.
        uhr = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                self?.aktualisiere()
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
        aktualisiere()
    }

    /// Hört auf, sich anzubieten, und schliesst jede offene Verbindung.
    func halte() {
        hoerer?.cancel()
        hoerer = nil
        register.alleBeenden()
        uhr?.cancel()
        uhr = nil
        bereit = false
        fehler = "Angehalten — das iPad erreicht den Heim-PC gerade nicht über diesen Mac."
        aktualisiere()
    }

    /// Eine neue Zahl zum Koppeln zeigen (die alte ist damit tot).
    func neueZahl() {
        stand.oeffneKopplung(jetzt: Vermittlerkopplung.stetigeUhr)
        aktualisiere()
    }

    /// **Das iPad vergessen:** neue Zugangsdaten. Ein gekoppeltes iPad bekommt danach die
    /// Tür und muss neu koppeln; am Heim-PC ändert sich nichts.
    func vergissIPad() {
        let neu = Vermittlerzugang.erzeuge()
        stand.ersetzeZugang(neu)
        hinweis = Vermittlerschluessel.speichere(neu)
        UserDefaults.standard.removeObject(forKey: Self.gekoppeltSchluessel)
        aktualisiere()
    }

    // ------------------------------------------------------- für die Leitungen

    /// Die Tür am Kopf allein — `nil`: weiterlesen.
    func vorab(_ kopf: Anfragekopf) -> Leitungsantwort? {
        stand.vorab(kopf, jetzt: Vermittlerkopplung.stetigeUhr)
    }

    /// Eine ganz gelesene Anfrage: selbst beantworten oder weiterreichen. `nil` heisst:
    /// **keine Antwort** — ob es drüben ankam, ist nicht bekannt, und die abgebrochene
    /// Verbindung sagt dem iPad genau das.
    func bearbeite(_ anfrage: RoheAnfrage) async -> Leitungsantwort? {
        let vorher = stand.erfolgreicheKopplungen
        let schritt = stand.beantworte(anfrage, jetzt: Vermittlerkopplung.stetigeUhr)
        if stand.erfolgreicheKopplungen > vorher {
            UserDefaults.standard.set(true, forKey: Self.gekoppeltSchluessel)
        }
        aktualisiere()
        switch schritt {
        case .antworte(let antwort):
            return antwort
        case .weiterreichen(let weiterreichung):
            let ergebnis = await heim.reiche(weiterreichung)
            return Vermittlungsregel.antwort(auf: ergebnis)
        }
    }

    // ------------------------------------------------------------------- intern

    private func aktualisiere() {
        let jetzt = Vermittlerkopplung.stetigeUhr
        let neu = Vermittlerlage.bestimme(bereit: bereit, fehler: fehler, stand: stand, jetzt: jetzt)
        if neu != zeile { zeile = neu }
        let zahl = stand.koppelzahl(jetzt: jetzt)
        if zahl != koppelzahl { koppelzahl = zahl }
        if stand.letzterKoppelgrund != koppelgrund { koppelgrund = stand.letzterKoppelgrund }
    }

    private func biete() {
        let anschluss: NWEndpoint.Port = aufFestemAnschluss
            ? (NWEndpoint.Port(rawValue: UInt16(Suche.vorgabeAnschluss)) ?? .any)
            : .any
        let name = Vermittlerangebot.dienstname(rechner: Host.current().localizedName ?? "diesem Mac")
        do {
            hoerer = try Vermittlungsdienst.baueHoerer(
                anschluss: anschluss, name: name, schlange: schlange, register: register,
                dienst: self,
                melde: { [weak self] zustand in
                    Task { @MainActor in self?.hoererZustand(zustand) }
                })
        } catch {
            fehler = "Der Mac kann sich dem iPad nicht anbieten (\(error.localizedDescription))."
            aktualisiere()
        }
    }

    private func hoererZustand(_ zustand: Hoererzustand) {
        switch zustand {
        case .bereit:
            bereit = true
            fehler = nil
        case .wartet(let satz):
            bereit = false
            fehler = satz
        case .belegt where aufFestemAnschluss:
            // DER VORGABE-ANSCHLUSS IST BELEGT (laeuft der Server auf diesem Mac?): ein
            // freier. Das iPad findet den Mac ueber seinen Namen, nicht ueber die Zahl.
            hoerer?.cancel()
            hoerer = nil
            aufFestemAnschluss = false
            biete()
        case .belegt:
            bereit = false
            fehler = "Der Mac findet keinen freien Anschluss, um sich dem iPad anzubieten."
        case .gescheitert(let satz):
            bereit = false
            fehler = satz
            hoerer?.cancel()
            hoerer = nil
        case .aus:
            break
        }
        aktualisiere()
    }

    /// Baut den Anbieter — **ausserhalb des Hauptfadens gedacht:** `nonisolated`, damit die
    /// Rückrufe, die `Network` auf `schlange` ruft, nicht an den Hauptfaden gebunden sind
    /// (in Swift 6 prüft die Laufzeit das und hielte das Programm an).
    nonisolated private static func baueHoerer(
        anschluss: NWEndpoint.Port, name: String, schlange: DispatchQueue,
        register: Leitungsregister, dienst: Vermittlungsdienst,
        melde: @escaping @Sendable (Hoererzustand) -> Void
    ) throws -> NWListener {
        let parameter = NWParameters.tcp
        // KEIN `allowLocalEndpointReuse`: Der Anschluss soll entweder ganz diesem Mac-Dienst
        // gehoeren oder belegt sein — nicht mit einem anderen Prozess geteilt, der dann einen
        // Teil der Anfragen des iPad bekaeme. Belegt heisst: ein freier (`hoererZustand`).
        parameter.includePeerToPeer = false
        let hoerer = try NWListener(using: parameter, on: anschluss)
        hoerer.service = NWListener.Service(name: name, type: Marke.dienst, domain: nil,
                                            txtRecord: Vermittlerangebot.txt)
        hoerer.stateUpdateHandler = { zustand in
            melde(Hoererzustand(zustand))
        }
        hoerer.newConnectionHandler = { [weak dienst] verbindung in
            // ZU VIELE ZUGLEICH: gleich wieder zu, ohne ein Byte zu lesen.
            guard register.anzahl < Vermittlungsdienst.hoechstensLeitungen else {
                verbindung.cancel()
                return
            }
            let leitung = Vermittlungsleitung(verbindung: verbindung, schlange: schlange,
                                              dienst: dienst, register: register)
            register.nimm(leitung)
            leitung.starte()
        }
        hoerer.start(queue: schlange)
        return hoerer
    }
}

/// Der Zustand des Anbieters, als Satz übersetzt — **auf `schlange`**, bevor er zum
/// Hauptfaden geht, damit dort nur ein einfacher Wert ankommt.
enum Hoererzustand: Sendable {
    case bereit
    case wartet(String)
    case belegt
    case gescheitert(String)
    case aus

    init(_ zustand: NWListener.State) {
        switch zustand {
        case .ready:
            self = .bereit
        case .waiting(let f):
            self = .wartet(Hoererzustand.satz(f))
        case .failed(let f):
            if case .posix(let code) = f, code == .EADDRINUSE {
                self = .belegt
            } else {
                self = .gescheitert(Hoererzustand.satz(f))
            }
        case .setup, .cancelled:
            self = .aus
        @unknown default:
            self = .aus
        }
    }

    /// Ein Satz für einen Menschen. `-65570` ist `kDNSServiceErr_PolicyDenied`: Der Mac darf
    /// sich im lokalen Netz nicht anbieten (die Erlaubnis «Lokales Netzwerk» fehlt, ab
    /// macOS 15).
    static func satz(_ f: NWError) -> String {
        if case .dns(let code) = f, Int(code) == -65570 {
            return "Lokales Netzwerk nicht erlaubt: Systemeinstellungen → Datenschutz & "
                + "Sicherheit → Lokales Netzwerk."
        }
        return "Der Mac kann sich dem iPad nicht anbieten (\(f.localizedDescription))."
    }
}

/// Die offenen Verbindungen — damit `halte()` sie schliessen kann und keine zu viel offen
/// ist. Eine Sperre, weil `Network` von seiner Schlange ruft und `halte()` vom Hauptfaden.
final class Leitungsregister: @unchecked Sendable {
    private let sperre = NSLock()
    private var leitungen: [ObjectIdentifier: Vermittlungsleitung] = [:]

    var anzahl: Int {
        sperre.lock()
        defer { sperre.unlock() }
        return leitungen.count
    }

    func nimm(_ leitung: Vermittlungsleitung) {
        sperre.lock()
        leitungen[ObjectIdentifier(leitung)] = leitung
        sperre.unlock()
    }

    func entferne(_ leitung: Vermittlungsleitung) {
        sperre.lock()
        leitungen[ObjectIdentifier(leitung)] = nil
        sperre.unlock()
    }

    func alleBeenden() {
        sperre.lock()
        let alle = Array(leitungen.values)
        leitungen = [:]
        sperre.unlock()
        alle.forEach { $0.beende() }
    }
}
