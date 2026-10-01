import Foundation
import SwiftUI
#if canImport(VisboxKern)
// Warum bedingt: siehe `Vorfuehransicht.swift`.
import VisboxKern
#endif

/// **Der Takt des Vorführschalters** — die dünne Schicht über `Vorfuehrschalter` (Kern).
///
/// Der Schalter selbst hat keine Uhr und sendet nichts; diese Klasse gibt ihm beides: Sie
/// fragt einmal je Sekunde, ob ein Versuch fällig ist, lässt `pruefe` ihn machen und meldet
/// den Ausgang zurück. Was ein Versuch ist, entscheidet, wer sie anlegt — gedacht ist
/// `GET /api/fortschritt` (`Anfragen.fortschritt`) mit der Frist `Vorfuehrschalter.versuchsfrist`,
/// die Antwort durch `Versuchsausgang.aus(status:daten:)`, ein geworfener Fehler als
/// `.keineAntwort(grund:)`. So bleibt die Leitung an **einer** Stelle der Mac-App (Strom A).
///
/// Die Uhr ist einsetzbar (`uhr`), damit eine Probe am Mac sie vorrücken kann.
///
/// **Unübersetzt** (Linux, 01.10.2026) und ohne Probe — die Übergänge prüft
/// `VorfuehrschalterTests` im Kern; hier wird nur getaktet.
@MainActor
public final class Vorfuehrsteuerung: ObservableObject {
    @Published public private(set) var schalter: Vorfuehrschalter

    private let uhr: @Sendable () -> Date
    private let pruefe: @Sendable () async -> Versuchsausgang
    private var takt: Task<Void, Never>?
    /// Ob ein Versuch unterwegs ist — **nie zwei zugleich**: Ein hängender Versuch und ein
    /// zweiter, der ihn überholt, meldeten ihre Ausgänge in falscher Reihenfolge.
    private var versuchUnterwegs = false
    /// Zählt jedes Neu-Einrichten. Ein Versuch, der davor losging, galt der alten Adresse
    /// oder dem alten Kennwort; sein Ausgang wird verworfen statt gemeldet.
    private var runde = 0

    public init(uhr: @escaping @Sendable () -> Date = { Date() },
                pruefe: @escaping @Sendable () async -> Versuchsausgang) {
        self.uhr = uhr
        self.pruefe = pruefe
        self.schalter = Vorfuehrschalter(start: uhr())
    }

    /// Den Takt anwerfen. Ein zweiter Aufruf tut nichts.
    public func starte() {
        guard takt == nil else { return }
        takt = Task { [weak self] in
            // SCHWACH GEHALTEN, AUCH IM WARTEN: Ist die Steuerung weg, endet der Takt — ohne
            // `deinit`, das hier nicht an den Takt kaeme (es laeuft ausserhalb des MainActor).
            while !Task.isCancelled, self != nil {
                self?.schritt()
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
    }

    /// Den Takt anhalten (beim Schliessen des Fensters).
    public func halte() {
        takt?.cancel()
        takt = nil
    }

    /// «Erneut verbinden» — der Abstand zurück, der nächste Versuch jetzt.
    public func erneutVerbinden() {
        schalter.erneutVerbinden(jetzt: uhr())
        schritt()
    }

    /// Adresse oder Kennwort sind neu: der Schalter von vorn (`Vorfuehrschalter.neuEingerichtet`),
    /// der erste Versuch gleich.
    public func neuEingerichtet() {
        runde += 1
        // EIN VERSUCH DER ALTEN RUNDE darf den neuen nicht aufhalten: Er laeuft zu Ende, sein
        // Ausgang wird verworfen (`schritt`), und der neue geht sofort los.
        versuchUnterwegs = false
        schalter.neuEingerichtet(jetzt: uhr())
        schritt()
    }

    /// Die Heimleitung hat gefragt (`Heimleitung.letzteFrage`) — steht die Leitung dort oder
    /// spricht die Tür, ist der nächste Versuch hier gleich fällig. Die Regel steht im Kern
    /// (`Vorfuehrschalter.heimleitungFand`).
    public func heimleitungFand(_ befund: Leitungsbefund) {
        schalter.heimleitungFand(befund, jetzt: uhr())
        schritt()
    }

    /// Ein Takt: die Zeitschwelle prüfen, und wenn ein Versuch fällig ist, ihn losschicken.
    private func schritt() {
        let jetzt = uhr()
        schalter.ticke(jetzt: jetzt)
        guard !versuchUnterwegs, schalter.faellig(jetzt: jetzt) else { return }
        versuchUnterwegs = true
        let pruefe = self.pruefe
        let runde = self.runde
        // DER VERSUCH LAEUFT NEBENHER, der Takt weiter: Haengt er bis zu seiner Frist, greift
        // die Zeitschwelle trotzdem.
        Task { [weak self] in
            let ausgang = await pruefe()
            guard let self else { return }
            // AUS EINER ALTEN RUNDE: Die Antwort gehoert zur Adresse von vorher.
            guard runde == self.runde else { return }
            self.versuchUnterwegs = false
            self.schalter.melde(ausgang, jetzt: self.uhr())
        }
    }
}

// ================================================================== die Beispielmappe

extension Vorfuehrmappe {
    /// Der Ordner der Mappe im App-Bündel: `Contents/Resources/Beispielmappe/` (die
    /// Prüfstrecke legt ihn dorthin; im Repo `ipad/VisboxMac/Beispielmappe/`).
    public static let buendelordner = "Beispielmappe"

    /// Die Mappe aus dem App-Bündel — gesucht über `Bundle.main`, nicht über `Bundle.module`:
    /// Die Prüfstrecke kopiert den Ordner in die fertige App, nicht SwiftPM (dieselbe Lehre
    /// wie bei den Schriften der iPad-App, Mac-CI vom 23.09.2026).
    ///
    /// - Throws: `Vorfuehrmappenfehler` mit seinem Satz — `dateiFehlt`, wenn der Ordner nicht
    ///   im Bündel liegt.
    public static func ausDemBuendel(_ buendel: Bundle = .main) throws
        -> (mappe: Vorfuehrmappe, ordner: URL) {
        guard let ressourcen = buendel.resourceURL else {
            throw Vorfuehrmappenfehler.dateiFehlt
        }
        let ordner = ressourcen.appendingPathComponent(buendelordner, isDirectory: true)
        return (try Vorfuehrmappe.lies(ordner: ordner), ordner)
    }
}

/// **Der Vorführmodus, verdrahtet**: die Beispielmappe aus dem Bündel und der Stand aus der
/// Steuerung. Lässt sich die Mappe nicht lesen, steht ihr Satz da — nicht ein leerer Schirm.
public struct Vorfuehrbereich: View {
    @ObservedObject public var steuerung: Vorfuehrsteuerung
    public let ipadVerbunden: Bool
    /// Öffnet das Blatt «Einrichten» (siehe `Vorfuehransicht.einrichten`).
    public let einrichten: (() -> Void)?
    @State private var geladen: Result<GeladeneMappe, Vorfuehrmappenfehler>?

    public init(steuerung: Vorfuehrsteuerung, ipadVerbunden: Bool,
                einrichten: (() -> Void)? = nil) {
        self.steuerung = steuerung
        self.ipadVerbunden = ipadVerbunden
        self.einrichten = einrichten
    }

    public var body: some View {
        Group {
            switch geladen {
            case .success(let g):
                Vorfuehransicht(mappe: g.mappe, ordner: g.ordner, seit: steuerung.schalter.seit,
                                letzterVersuch: steuerung.schalter.letzterVersuch,
                                letzterGrund: steuerung.schalter.letzterGrund,
                                ipadVerbunden: ipadVerbunden,
                                erneutVerbinden: { steuerung.erneutVerbinden() },
                                einrichten: einrichten)
            case .failure(let fehler):
                // AUCH OHNE MAPPE der Grund: Er sagt, was zu tun ist; die Mappe nicht.
                Text(([Vorfuehrsaetze.band(seit: steuerung.schalter.seit, zone: .current),
                        Vorfuehrsaetze.grund(steuerung.schalter.letzterGrund), fehler.satz]
                       as [String?]).compactMap { $0 }.joined(separator: "\n\n"))
                    .font(Vorfuehrschrift.text(14))
                    .padding(24)
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                    .background(Color(vorfuehr: Blattfarbe.grund))
                    .foregroundStyle(Color(vorfuehr: Blattfarbe.schrift))
            case .none:
                Color(vorfuehr: Blattfarbe.grund)
            }
        }
        .onAppear {
            guard geladen == nil else { return }
            do {
                let (mappe, ordner) = try Vorfuehrmappe.ausDemBuendel()
                geladen = .success(GeladeneMappe(mappe: mappe, ordner: ordner))
            } catch let f as Vorfuehrmappenfehler {
                geladen = .failure(f)
            } catch {
                geladen = .failure(.nichtLesbar)
            }
        }
    }

    struct GeladeneMappe: Equatable {
        let mappe: Vorfuehrmappe
        let ordner: URL
    }
}
