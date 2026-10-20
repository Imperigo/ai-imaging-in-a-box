import Foundation
import SwiftUI
import VisboxKern

/// **Der Takt des Leitungsschalters** — die dünne Schicht über `Leitungsschalter` (Kern).
///
/// Bis 0.3.0 hiess sie `Vorfuehrsteuerung` und lag unter `Vorfuehrung/`; seit Entscheid 103b
/// gibt es den Vorführmodus nicht mehr, der Takt ist geblieben: Er sagt dem Fenster, ob das
/// Band «Heim-PC nicht erreichbar» steht und ob Rechnen und Assistent gesperrt sind.
///
/// Der Schalter selbst hat keine Uhr und sendet nichts; diese Klasse gibt ihm beides: Sie
/// fragt einmal je Sekunde, ob ein Versuch fällig ist, lässt `pruefe` ihn machen und meldet
/// den Ausgang zurück. Was ein Versuch ist, entscheidet, wer sie anlegt — gedacht ist
/// `GET /api/fortschritt` (`Anfragen.fortschritt`) mit der Frist `Leitungsschalter.versuchsfrist`,
/// die Antwort durch `Versuchsausgang.aus(status:daten:)`, ein geworfener Fehler als
/// `.keineAntwort(grund:)`. So bleibt die Leitung an **einer** Stelle der Mac-App (Strom A).
///
/// Die Uhr ist einsetzbar (`uhr`), damit eine Probe am Mac sie vorrücken kann.
///
/// **Unübersetzt** (Linux, 01.10.2026) und ohne Probe — die Übergänge prüft
/// `LeitungsschalterTests` im Kern; hier wird nur getaktet.
@MainActor
public final class Leitungssteuerung: ObservableObject {
    @Published public private(set) var schalter: Leitungsschalter

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
        self.schalter = Leitungsschalter(start: uhr())
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

    /// Adresse oder Kennwort sind neu: der Schalter von vorn (`Leitungsschalter.neuEingerichtet`),
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
    /// (`Leitungsschalter.heimleitungFand`).
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
