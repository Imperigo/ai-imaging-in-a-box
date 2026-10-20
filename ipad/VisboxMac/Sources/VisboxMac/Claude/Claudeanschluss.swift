import Foundation
import Network
import VisboxKern

/// Der Anschluss fuer Claude (Plan KI-Bedienung, Stufe 2; Entscheide 106, 106e, 108 B): ein
/// MCP-Server **in der Mac-App, nur auf diesem Rechner** — `http://127.0.0.1:8631/mcp`.
///
/// Claude Code traegt ihn so ein: `claude mcp add --transport http visbox
/// http://127.0.0.1:8631/mcp`; Claude Desktop startet die App mit `--mcp-stdio`
/// (`Claudestdio`). Ein Geheimnis braucht es nicht (Regel 3): Wer an den Anschluss kommt, sitzt
/// an diesem Rechner — und was etwas aendert, wird ab Stufe 3 eine Karte in der
/// Assistent-Leiste.
///
/// **Was hier entschieden wird, entscheidet nicht diese Klasse**, sondern der Kern (`Mcpkern`,
/// `Mcpleitung`, `Mcpzugang` — mit Proben unter Linux). Hier steht nur das Netz:
///
/// 1. **Binden nur an 127.0.0.1** (`requiredLocalEndpoint` und `requiredInterfaceType =
///    .loopback`) — im WLAN ist der Anschluss nicht zu sehen und nicht zu erreichen. Kein
///    Bonjour-Angebot, anders als die Vermittlung fuer das iPad.
/// 2. **Jede Verbindung pruefen**, bevor ein Byte gelesen ist: Die Gegenstelle muss dieser
///    Rechner sein (`Mcpzugang.gegenstelleIstLokal`) — die zweite Wand hinter dem Binden.
/// 3. **Ab Werk an** (Entscheid 108 B), abschaltbar mit der Einstellung `claudeMcp.an`.
///
/// Der Werkzeugtraeger ist bis Stufe 3 ein Platzhalter (`Mcpplatzhalter`): `visbox_status`
/// antwortet, alles andere sagt «kommt mit Stufe 3».
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt (Linux kennt `Network`
/// nicht); übersetzt in der Prüfstrecke am Mac.
@MainActor
final class Claudeanschluss: ObservableObject {

    /// Einer fuer die ganze App — wie der Fassungswaechter: Zwei Hoerer auf einem Anschluss
    /// gibt es nicht.
    static let gemeinsam = Claudeanschluss()

    /// Die Einstellung «Claude über MCP» — **ab Werk an** (108 B). Kein Geheimnis darin.
    static let einstellung = "claudeMcp.an"

    /// Ob «Claude über MCP» eingeschaltet ist. Fehlt der Eintrag, gilt die Vorgabe: an.
    static var istAn: Bool {
        UserDefaults.standard.object(forKey: einstellung) as? Bool ?? true
    }

    enum Lage: Equatable {
        case aus
        case startet
        case bereit
        case belegt
        case gescheitert(String)

        var satz: String {
            switch self {
            case .aus: return "Claude über MCP ist aus."
            case .startet: return "Claude über MCP startet …"
            case .bereit: return "Claude kann sich verbinden: http://127.0.0.1:\(Mcp.anschluss)\(Mcp.pfad)"
            case .belegt: return "Der Anschluss \(Mcp.anschluss) ist belegt — läuft schon eine \(Marke.name)?"
            case .gescheitert(let grund): return "Claude über MCP läuft nicht: \(grund)"
            }
        }
    }

    @Published private(set) var lage: Lage = .aus

    /// Der Kern — ein `actor`, darum an jede Verbindung weiterreichbar.
    let kern: Mcpkern
    private let schlange = DispatchQueue(label: "claude.mcp.leitungen")
    private let zaehler = Claudezaehler()
    private var hoerer: NWListener?

    init() {
        let fassung = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString")
            as? String ?? "0.0.0"
        kern = Mcpkern(traeger: Mcpplatzhalter(ort: .inDerApp), fassung: fassung)
    }

    /// Beim App-Start: nur, wenn eingeschaltet.
    func starteWennAn() {
        if Claudeanschluss.istAn { starte() }
    }

    /// Schaltet ein oder aus und merkt es sich.
    func schalte(_ an: Bool) {
        UserDefaults.standard.set(an, forKey: Claudeanschluss.einstellung)
        if an { starte() } else { halte() }
    }

    func starte() {
        guard hoerer == nil else { return }
        guard let anschluss = NWEndpoint.Port(rawValue: UInt16(Mcp.anschluss)) else { return }
        lage = .startet
        do {
            hoerer = try Claudeanschluss.baueHoerer(
                anschluss: anschluss, schlange: schlange, kern: kern, zaehler: zaehler,
                melde: { [weak self] zustand in
                    Task { @MainActor in self?.hoererZustand(zustand) }
                })
        } catch {
            lage = .gescheitert(error.localizedDescription)
        }
    }

    func halte() {
        hoerer?.cancel()
        hoerer = nil
        lage = .aus
    }

    private func hoererZustand(_ zustand: Claudehoerer) {
        switch zustand {
        case .bereit:
            lage = .bereit
        case .belegt:
            // KEIN FREIER ANSCHLUSS ALS ERSATZ (anders als die Vermittlung): Claude sucht
            // Visbox unter 8631 und nirgends sonst.
            hoerer?.cancel()
            hoerer = nil
            lage = .belegt
        case .gescheitert(let satz):
            hoerer?.cancel()
            hoerer = nil
            lage = .gescheitert(satz)
        case .wartet(let satz):
            lage = .gescheitert(satz)
        case .aus:
            break
        }
    }

    /// Baut den Hoerer — `nonisolated`, damit die Rueckrufe, die `Network` auf `schlange`
    /// ruft, nicht an den Hauptfaden gebunden sind (wie `Vermittlungsdienst.baueHoerer`).
    nonisolated private static func baueHoerer(
        anschluss: NWEndpoint.Port, schlange: DispatchQueue, kern: Mcpkern,
        zaehler: Claudezaehler, melde: @escaping @Sendable (Claudehoerer) -> Void
    ) throws -> NWListener {
        let parameter = NWParameters.tcp
        // NUR 127.0.0.1: die Adresse UND die Schnittstelle. Nie 0.0.0.0, nie das WLAN.
        parameter.requiredLocalEndpoint = NWEndpoint.hostPort(host: .ipv4(.loopback), port: anschluss)
        parameter.requiredInterfaceType = .loopback
        parameter.includePeerToPeer = false
        // KEIN `allowLocalEndpointReuse`: Der Anschluss gehoert ganz dieser App oder ist belegt.
        let hoerer = try NWListener(using: parameter)
        hoerer.stateUpdateHandler = { zustand in
            melde(Claudehoerer(zustand))
        }
        hoerer.newConnectionHandler = { verbindung in
            // DIE ZWEITE WAND: Kommt die Verbindung nicht von diesem Rechner, wird sie
            // geschlossen, bevor ein Byte gelesen ist.
            guard Claudeanschluss.istLokal(verbindung), zaehler.nimm() else {
                verbindung.cancel()
                return
            }
            Claudeleitung(verbindung: verbindung, schlange: schlange, kern: kern,
                          zaehler: zaehler).starte()
        }
        hoerer.start(queue: schlange)
        return hoerer
    }

    nonisolated static func istLokal(_ verbindung: NWConnection) -> Bool {
        guard case .hostPort(let rechner, _) = verbindung.endpoint else { return false }
        return Mcpzugang.gegenstelleIstLokal(String(describing: rechner))
    }
}

/// Wie viele Verbindungen zugleich offen sind — hoechstens `hoechstens`. Claude haelt selten
/// mehr als zwei; ein Programm, das den Anschluss zuschuettet, bekommt keine weitere.
final class Claudezaehler: @unchecked Sendable {
    static let hoechstens = 32
    private let sperre = NSLock()
    private var offen = 0

    func nimm() -> Bool {
        sperre.lock()
        defer { sperre.unlock() }
        guard offen < Claudezaehler.hoechstens else { return false }
        offen += 1
        return true
    }

    func gib() {
        sperre.lock()
        offen = max(0, offen - 1)
        sperre.unlock()
    }
}

/// Der Zustand des Hoerers als einfacher Wert — uebersetzt auf `schlange`, bevor er zum
/// Hauptfaden geht. Eigens und nicht `Hoererzustand` der Vermittlung: Deren Saetze sprechen vom
/// iPad.
enum Claudehoerer: Sendable {
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
            self = .wartet(f.localizedDescription)
        case .failed(let f):
            if case .posix(let code) = f, code == .EADDRINUSE {
                self = .belegt
            } else {
                self = .gescheitert(f.localizedDescription)
            }
        case .setup, .cancelled:
            self = .aus
        @unknown default:
            self = .aus
        }
    }
}
