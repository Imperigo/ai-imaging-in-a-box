import CoreText
import Foundation
import SwiftUI

/// Die Schriften der Mac-App — **dieselben Dateien wie beim iPad**, zur Laufzeit registriert.
///
/// Die Prüfstrecke legt den Ordner `ipad/Visbox.swiftpm/Schriften/` unverändert, samt den
/// Lizenztexten (OFL 1.1), nach `Contents/Resources/Schriften/` ins Bündel. Registriert wird
/// hier jede `.ttf` darin, nur für diesen Prozess (`.process`): Die App installiert keine
/// Schrift ins System.
///
/// **Warum hier Familiennamen stehen und nicht die Schnitte des iPad** (`Schrift.schnitte` in
/// `Leiste/Zeichenblatt.swift`): Die iPad-App ist kein Modul, ihre Leiste lässt sich von hier
/// nicht einbinden. Die Mac-App fragt darum nach der **Familie** und lässt CoreText den
/// Schnitt wählen; `tests/test_ipad_geruest.py` prüft, dass jede Familie hier in einer der
/// Dateien steht.
///
/// **Was als bereit gilt:** nicht, dass das Registrieren «ja» sagt, sondern dass CoreText
/// danach unter dem Familiennamen wirklich diese Familie liefert — für einen unbekannten
/// Namen gibt es ohne Fehler eine Ersatzschrift. Scheitert eine Familie, gilt für sie die
/// Systemschrift, und der Grund steht im Protokoll. **Kein Absturz.**
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
enum Macschriften {

    enum Rolle: Hashable {
        /// Fliesstext und Bedienung.
        case text
        /// Zahlen, Zustandswörter, Dateinamen.
        case zahl
        /// Überschriften.
        case titel
    }

    /// Die Familie je Rolle (Entscheide 20 und 25).
    static let familien: [Rolle: String] = [
        .text: "IBM Plex Sans",
        .zahl: "IBM Plex Mono",
        .titel: "Instrument Serif",
    ]

    struct Stand {
        var bereit: Set<Rolle> = []
        var befunde: [String] = []
    }

    /// Einmal ausgerechnet, beim ersten Zugriff (`VisboxMacApp.init`).
    static let stand: Stand = registriereAlle()

    /// Die Schrift einer Rolle — die eigene, wenn sie bereit ist, sonst die des Systems.
    static func schrift(_ rolle: Rolle, _ groesse: CGFloat,
                        _ gewicht: Font.Weight = .regular) -> Font {
        guard stand.bereit.contains(rolle), let familie = familien[rolle] else {
            switch rolle {
            case .text: return .system(size: groesse, weight: gewicht)
            case .zahl: return .system(size: groesse, weight: gewicht, design: .monospaced)
            case .titel: return .system(size: groesse, weight: gewicht, design: .serif)
            }
        }
        return Font(ctSchrift(familie, groesse, staerke(gewicht)))
    }

    // ------------------------------------------------------------------ intern

    private static func registriereAlle() -> Stand {
        var stand = Stand()
        let dateien = schriftdateien()
        if dateien.isEmpty {
            stand.befunde.append("Im Bündel liegt kein Ordner Schriften mit .ttf-Dateien — "
                                 + "es gilt die Systemschrift.")
        }
        for ort in dateien {
            var fehler: Unmanaged<CFError>?
            if !CTFontManagerRegisterFontsForURL(ort as CFURL, .process, &fehler) {
                let code = fehler.map { CFErrorGetCode($0.takeRetainedValue()) }
                // Schon registriert (ein zweiter Aufruf im selben Prozess) ist kein Fehler.
                if code != CTFontManagerError.alreadyRegistered.rawValue {
                    let angabe = code.map { String($0) } ?? "ohne Angabe"
                    stand.befunde.append("\(ort.lastPathComponent) liess sich nicht "
                                         + "registrieren (Fehler \(angabe)).")
                }
            }
        }
        for (rolle, familie) in familien {
            let geliefert = CTFontCopyFamilyName(ctSchrift(familie, 12, 0)) as String
            if geliefert == familie {
                stand.bereit.insert(rolle)
            } else {
                stand.befunde.append("Unter «\(familie)» liefert das System «\(geliefert)» — "
                                     + "für diese Rolle gilt die Systemschrift.")
            }
        }
        for befund in stand.befunde {
            print("Schrift: \(befund)")
        }
        return stand
    }

    /// Jede Schriftdatei unter `Contents/Resources/Schriften/`, auch in Unterordnern.
    private static func schriftdateien() -> [URL] {
        guard let wurzel = Bundle.main.resourceURL?
                .appendingPathComponent("Schriften", isDirectory: true),
              let alle = FileManager.default.enumerator(at: wurzel,
                                                        includingPropertiesForKeys: nil)
        else { return [] }
        var dateien: [URL] = []
        for case let ort as URL in alle where ["ttf", "otf"].contains(ort.pathExtension.lowercased()) {
            dateien.append(ort)
        }
        return dateien
    }

    /// Eine CoreText-Schrift einer Familie in einer Stärke (−1 … 1, wie `NSFont.Weight`).
    private static func ctSchrift(_ familie: String, _ groesse: CGFloat,
                                  _ staerke: CGFloat) -> CTFont {
        let merkmale: [String: Any] = [
            kCTFontFamilyNameAttribute as String: familie,
            kCTFontTraitsAttribute as String: [kCTFontWeightTrait as String: staerke],
        ]
        let beschreibung = CTFontDescriptorCreateWithAttributes(merkmale as CFDictionary)
        return CTFontCreateWithFontDescriptor(beschreibung, groesse, nil)
    }

    /// Die Stärke als Zahl, wie CoreText sie im Merkmal `kCTFontWeightTrait` führt (die Werte
    /// von `NSFont.Weight`).
    private static func staerke(_ gewicht: Font.Weight) -> CGFloat {
        switch gewicht {
        case .ultraLight: return -0.8
        case .thin: return -0.6
        case .light: return -0.4
        case .medium: return 0.23
        case .semibold: return 0.3
        case .bold: return 0.4
        case .heavy: return 0.56
        case .black: return 0.62
        default: return 0
        }
    }
}
