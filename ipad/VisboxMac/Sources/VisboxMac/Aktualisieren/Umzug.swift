import AppKit
import Foundation
import VisboxKern

/// «In Programme verschieben» (Owner-Entscheid 89, 14.10.2026, Blatt 18 Feld 4).
///
/// Anlass: Am Mac des Owners scheiterte das Aktualisieren mit «macOS hat die App an einen
/// schreibgeschützten Ort verschoben». macOS startet eine heruntergeladene App, die nicht mit
/// dem Finder verschoben wurde, aus einer versteckten, schreibgeschützten Kopie («App
/// Translocation»). Wie viele Mac-Apps bietet Visbox dann an, sich selbst nach «Programme» zu
/// legen und dort neu zu starten — ein Klick.
///
/// Der Weg: das laufende Bündel (lesbar, auch am versteckten Ort) nach `/Applications`
/// kopieren — eine ältere Visbox dort geht in den Papierkorb, nicht ins Nichts —, das
/// Quarantäne-Merkmal der Kopie entfernen (sonst legte macOS auch sie wieder an den versteckten
/// Ort), die Kopie öffnen, diese Instanz beenden. Die heruntergeladene Datei bleibt liegen.
///
/// *Gebaut, am Gerät unbestätigt (14.10.2026).*
enum Umzug {
    /// Läuft diese App vom versteckten Ort?
    static var istVersteckt: Bool { Aktualisierung.istVersteckterOrt(Bundle.main.bundlePath) }

    enum Fehler: LocalizedError {
        case kopieren(String)
        var errorDescription: String? {
            switch self {
            case .kopieren(let grund):
                return "Verschieben nach «Programme» ging nicht: \(grund) — bitte die App mit dem "
                    + "Finder nach «Programme» ziehen."
            }
        }
    }

    /// Kopiert, entfernt die Quarantäne, öffnet die Kopie und beendet diese Instanz.
    @MainActor
    static func zieheUndStarteNeu(gescheitert: @escaping (String) -> Void) {
        let fm = FileManager.default
        let quelle = Bundle.main.bundleURL
        let ziel = URL(fileURLWithPath: Aktualisierung.programmeZiel)
        do {
            if fm.fileExists(atPath: ziel.path) {
                try fm.trashItem(at: ziel, resultingItemURL: nil)
            }
            try fm.copyItem(at: quelle, to: ziel)
        } catch {
            gescheitert(Fehler.kopieren(error.localizedDescription).errorDescription ?? "")
            return
        }
        entferneQuarantaene(ziel)
        // ERST BEENDEN, DANN OEFFNEN (14.10.2026), wie beim Neustart nach dem Aktualisieren:
        // Der Helfer wartet, bis diese Instanz weg ist, und oeffnet dann die Kopie.
        let befehl = Aktualisierung.neustartBefehl(pid: ProcessInfo.processInfo.processIdentifier,
                                                   buendel: ziel.path)
        let helfer = Process()
        helfer.executableURL = URL(fileURLWithPath: befehl[0])
        helfer.arguments = Array(befehl.dropFirst())
        do {
            try helfer.run()
        } catch {
            gescheitert(Fehler.kopieren(error.localizedDescription).errorDescription ?? "")
            return
        }
        NSApp.terminate(nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + Aktualisierung.beendenFrist) {
            exit(0)
        }
    }

    /// `com.apple.quarantine` von der Kopie und allem darin.
    private static func entferneQuarantaene(_ wurzel: URL) {
        let name = "com.apple.quarantine"
        removexattr(wurzel.path, name, XATTR_NOFOLLOW)
        guard let alle = FileManager.default.enumerator(atPath: wurzel.path) else { return }
        for case let teil as String in alle {
            removexattr(wurzel.appendingPathComponent(teil).path, name, XATTR_NOFOLLOW)
        }
    }
}
