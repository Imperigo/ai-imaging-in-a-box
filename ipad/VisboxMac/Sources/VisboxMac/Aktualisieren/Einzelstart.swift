import AppKit
import Foundation
import VisboxKern

/// Ein Visbox-Fenster, nie zwei Instanzen — die Ausfuehrung zu `Aktualisierung.startentscheid`.
///
/// Anlass: Owner-Befund 20.10.2026 beim Aktualisieren von 0.2.8 auf 0.2.9 — nach dem
/// Herunterladen stand eine zweite Visbox neben der alten, nach «Neu starten» eine dritte.
/// Die Regel steht im Kern; hier wird nur gefragt, wer laeuft, und getan, was die Regel sagt.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
enum Einzelstart {
    /// Wie lange die neue Fassung nach «Neu starten» auf das Ende der alten wartet, bevor sie
    /// sie zwingt. Der Helfer hat sie dann meist schon beendet.
    static let warteAufAlte: TimeInterval = 3

    static func pruefe() {
        guard let kennung = Bundle.main.bundleIdentifier else { return }
        let eigene = ProcessInfo.processInfo.processIdentifier
        let laufend = NSRunningApplication.runningApplications(withBundleIdentifier: kennung)
            .filter { $0.processIdentifier != eigene && !$0.isTerminated }
        let andere = laufend.map {
            (pid: $0.processIdentifier, start: $0.launchDate?.timeIntervalSince1970 ?? 0)
        }
        let erwartet = UserDefaults.standard.string(forKey: Aktualisierung.erwarteteSchluessel) != nil
        switch Aktualisierung.startentscheid(andere: andere, neustartErwartet: erwartet) {
        case .allein:
            return
        case .vorneHolen(let pid):
            laufend.first { $0.processIdentifier == pid }?.activate(options: [])
            exit(0)
        case .alteBeenden(let pids):
            let alte = laufend.filter { pids.contains($0.processIdentifier) }
            alte.forEach { $0.terminate() }
            let frist = Date().addingTimeInterval(warteAufAlte)
            while alte.contains(where: { !$0.isTerminated }) && Date() < frist {
                RunLoop.current.run(until: Date().addingTimeInterval(0.1))
            }
            alte.filter { !$0.isTerminated }.forEach { $0.forceTerminate() }
        }
    }
}
