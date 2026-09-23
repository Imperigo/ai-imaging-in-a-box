import CoreText
import Foundation
import SwiftUI

/// Registriert die mitgelieferten Schriften beim System — **die eine Registrierstelle.**
///
/// Die Dateien liegen in `Schriften/` und kommen über `resources: [.process("Schriften")]`
/// in die Ablage der App (`Bundle.module`). Registriert wird nur für diesen Prozess
/// (`.process`): Die App installiert keine Schrift ins System.
///
/// **Wann:** einmal, beim ersten Gebrauch einer `Schrift` — also beim Zeichnen des ersten
/// Bildschirms. `stand` ist ein `static let`; Swift rechnet ihn genau einmal aus, auch wenn
/// mehrere Ansichten gleichzeitig danach fragen.
///
/// **Was als registriert gilt** (23.09.2026): nicht, dass `CTFontManagerRegisterFontsForURL`
/// «ja» sagt, sondern dass das System danach **unter dem PostScript-Namen wirklich diese
/// Schrift liefert.** Der Grund: `CTFontCreateWithName` gibt für einen unbekannten Namen
/// ohne Fehler eine Ersatzschrift zurück — eine Prüfung ohne Nachfrage sähe nie einen
/// Fehlschlag. Fehlt auch nur ein Schnitt einer Familie, gilt für die ganze Familie die
/// Systemschrift (in `Schrift`), damit nie zwei Schriften derselben Rolle nebeneinander
/// stehen.
///
/// *Gebaut, am Gerät unbestätigt* — ob Swift Playgrounds `Bundle.module` wie Xcode anlegt,
/// und ob die variable Datei ihr Gewicht über die Achse annimmt, zeigt erst das iPad.
enum Schriftregister {
    /// Was die Registrierung ergeben hat.
    struct Stand {
        /// Die Familien, deren jeder Schnitt registriert ist und unter seinem Namen kommt.
        var bereit: Set<Schriftfamilie> = []
        /// Warum ein Schnitt fehlt — ein Satz je Befund, für die Fehlersuche am Gerät.
        var befunde: [String] = []
    }

    /// Einmal ausgerechnet, beim ersten Zugriff.
    static let stand: Stand = registriereAlle()

    /// Die Kennung der Achse `wght` (Strichstärke) einer variablen Schrift: die vier
    /// Buchstaben «wght» als Zahl, wie OpenType und CoreText sie führen.
    private static let achseGewicht: UInt32 = 0x7767_6874

    /// Die Schrift eines Schnitts in fester Grösse — oder `nil`, wenn seine Familie nicht
    /// bereit ist (dann nimmt `Schrift` die Systemschrift).
    ///
    /// `gewicht` nur für die variable Datei (IBM Plex Sans): Es wird auf die Achse `wght`
    /// gesetzt, im Bereich 100–700, den die Datei anbietet.
    static func schrift(_ schnitt: Schriftschnitt, groesse: CGFloat,
                        gewicht: CGFloat? = nil) -> Font? {
        guard stand.bereit.contains(schnitt.familie) else { return nil }
        guard let gewicht = gewicht else {
            // `fixedSize` wie bisher `.system(size:)`: Die Masse des Entwurfs sind fest.
            return .custom(schnitt.postScript, fixedSize: groesse)
        }
        let achse: [NSNumber: NSNumber] = [
            NSNumber(value: achseGewicht): NSNumber(value: Double(min(max(gewicht, 100), 700)))
        ]
        let merkmale: [String: Any] = [
            kCTFontNameAttribute as String: schnitt.postScript,
            kCTFontVariationAttribute as String: achse,
        ]
        let beschreibung = CTFontDescriptorCreateWithAttributes(merkmale as CFDictionary)
        return Font(CTFontCreateWithFontDescriptor(beschreibung, groesse, nil))
    }

    // ------------------------------------------------------------------ intern

    private static func registriereAlle() -> Stand {
        var stand = Stand()
        var gescheitert = Set<Schriftfamilie>()
        for schnitt in Schrift.schnitte {
            if let befund = registriere(schnitt) {
                gescheitert.insert(schnitt.familie)
                stand.befunde.append(befund)
                print("Schrift: \(befund)")
            }
        }
        stand.bereit = Set(Schriftfamilie.allCases).subtracting(gescheitert)
        return stand
    }

    /// `nil`: registriert und nachgefragt. Sonst ein Satz, warum nicht.
    private static func registriere(_ schnitt: Schriftschnitt) -> String? {
        guard let ort = fundort(schnitt) else {
            return "\(schnitt.datei).ttf liegt nicht in der Ablage der App."
        }
        var fehler: Unmanaged<CFError>?
        if !CTFontManagerRegisterFontsForURL(ort as CFURL, .process, &fehler) {
            let code = fehler.map { CFErrorGetCode($0.takeRetainedValue()) }
            // Schon registriert (etwa ein zweiter Aufruf im selben Prozess) ist kein Fehler.
            if code != CTFontManagerError.alreadyRegistered.rawValue {
                let angabe = code.map { String($0) } ?? "ohne Angabe"
                return "\(schnitt.datei).ttf liess sich nicht registrieren (Fehler \(angabe))."
            }
        }
        let probe = CTFontCreateWithName(schnitt.postScript as CFString, 12, nil)
        let geliefert = CTFontCopyPostScriptName(probe) as String
        guard geliefert == schnitt.postScript else {
            return "Unter \(schnitt.postScript) liefert das System \(geliefert)."
        }
        return nil
    }

    /// Wo die Datei in der Ablage liegt. `.process` legt sie flach hinein (so SwiftPM,
    /// nachgefahren am 23.09.2026 unter Linux); sollte eine Umgebung die Unterordner
    /// behalten, wird dort gesucht.
    private static func fundort(_ schnitt: Schriftschnitt) -> URL? {
        let ablage = Bundle.module
        if let flach = ablage.url(forResource: schnitt.datei, withExtension: "ttf") {
            return flach
        }
        let gesucht = schnitt.datei + ".ttf"
        guard let wurzel = ablage.resourceURL,
              let alle = FileManager.default.enumerator(at: wurzel,
                                                        includingPropertiesForKeys: nil)
        else { return nil }
        for case let ort as URL in alle where ort.lastPathComponent == gesucht {
            return ort
        }
        return nil
    }
}
