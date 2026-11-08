import AppKit
import SwiftUI
import VisboxKern

/// **Hell und dunkel (A0156, Runde 2, Owner-Entscheid O-20261107-01):** Die Visbox folgt dem
/// Erscheinungsbild des Systems. Jede Farbe traegt ihre dunkle Zahl (Blatt 13) und eine helle;
/// welche gilt, entscheidet das Fenster (`NSAppearance`), nicht ein fest gesetztes Schema.
///
/// Die Farben von Blatt 13 — **an einer Stelle**, damit Vorführmodus und Assistent sie
/// mitbenutzen können statt sie abzuschreiben.
///
/// Abgenommen vom Blatt «Visbox startet am Mac» der Entwurfsfläche (01.10.2026): dunkler
/// Grund, Grün für «steht», Gelb für «lädt». Ein Rot für «fehlt» steht auf dem Blatt nicht;
/// es ist gesetzt, gedämpft wie die beiden anderen.
enum Startfarbe {
    static let grund = Color(startHex: 0x14161A, hell: 0xF4F5F7)
    static let flaeche = Color(startHex: 0x16191E, hell: 0xECEEF2)
    static let karte = Color(startHex: 0x1C1F26, hell: 0xFFFFFF)
    static let linie = Color(startHex: 0x2B3038, hell: 0xD5D9E0)
    static let ring = Color(startHex: 0x3A414C, hell: 0xB3BAC6)
    static let text = Color(startHex: 0xE6E8EC, hell: 0x1B1F26)
    static let leise = Color(startHex: 0x9AA2AE, hell: 0x5C6573)
    static let hell = Color(startHex: 0xC9CED6, hell: 0x3A414C)

    static let gruen = Color(startHex: 0x4EA373, hell: 0x2E8A5A)
    static let gruenText = Color(startHex: 0x8FD4AC, hell: 0x1F6B43)
    static let gruenGrund = Color(startHex: 0x17201C, hell: 0xE4F3EA)
    static let gruenRand = Color(startHex: 0x2F4438, hell: 0xA6D4B8)
    static let gruenKnopf = Color(startHex: 0x1B2420, hell: 0xD6EDDF)

    static let gelb = Color(startHex: 0xC8A53F, hell: 0x8A6D0F)
    static let gelbGrund = Color(startHex: 0x1E1C17, hell: 0xFBF3D9)

    static let rot = Color(startHex: 0xD0685C, hell: 0xB23A2E)
    static let rotGrund = Color(startHex: 0x221818, hell: 0xFCE9E6)
    static let rotRand = Color(startHex: 0x5A2E2A, hell: 0xE3A9A2)

    /// Die Farben einer Zeile nach ihrem Zustand: (Akzent, Satz, Grund, Rand, gestrichelt).
    static func zeile(_ stand: Zeilenstand) -> (akzent: Color, satz: Color, grund: Color,
                                                rand: Color, gestrichelt: Bool) {
        switch stand {
        case .steht: return (gruen, gruenText, gruenGrund, gruenRand, false)
        case .laedt: return (gelb, gelb, gelbGrund, gelb, true)
        case .wartet: return (ring, leise, karte, linie, false)
        case .fehlt: return (rot, rot, rotGrund, rotRand, false)
        }
    }
}

// NUR IN DIESER DATEI, UND MIT EIGENEM NAMEN: Ein `Color(hex:)` legt fast jede SwiftUI-Arbeit
// an — zwei Stroeme, die es je einmal anlegen, stiessen beim Zusammenfuehren zusammen.
private extension Color {
    /// Eine Farbe aus ihrer Sechserzahl (`0xRRGGBB`), wie sie auf dem Blatt steht.
    init(startHex hex: UInt32) {
        self.init(.sRGB,
                  red: Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue: Double(hex & 0xFF) / 255,
                  opacity: 1)
    }

    /// Dieselbe Farbe, im hellen Erscheinungsbild mit der zweiten Zahl. Die Wahl trifft das
    /// System beim Zeichnen, darum wechselt sie mit dem Fenster ohne neuen Aufbau.
    init(startHex dunkel: UInt32, hell: UInt32) {
        self.init(nsColor: NSColor(name: nil) { erscheinung in
            let istDunkel = erscheinung.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
            let hex = istDunkel ? dunkel : hell
            return NSColor(srgbRed: CGFloat((hex >> 16) & 0xFF) / 255,
                           green: CGFloat((hex >> 8) & 0xFF) / 255,
                           blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
        })
    }
}
