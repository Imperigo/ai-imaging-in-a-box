import SwiftUI
import VisboxKern

/// Die Farben von Blatt 13 — **an einer Stelle**, damit Vorführmodus und Assistent sie
/// mitbenutzen können statt sie abzuschreiben.
///
/// Abgenommen vom Blatt «Visbox startet am Mac» der Entwurfsfläche (01.10.2026): dunkler
/// Grund, Grün für «steht», Gelb für «lädt». Ein Rot für «fehlt» steht auf dem Blatt nicht;
/// es ist gesetzt, gedämpft wie die beiden anderen.
enum Startfarbe {
    static let grund = Color(startHex: 0x14161A)
    static let flaeche = Color(startHex: 0x16191E)
    static let karte = Color(startHex: 0x1C1F26)
    static let linie = Color(startHex: 0x2B3038)
    static let ring = Color(startHex: 0x3A414C)
    static let text = Color(startHex: 0xE6E8EC)
    static let leise = Color(startHex: 0x9AA2AE)
    static let hell = Color(startHex: 0xC9CED6)

    static let gruen = Color(startHex: 0x4EA373)
    static let gruenText = Color(startHex: 0x8FD4AC)
    static let gruenGrund = Color(startHex: 0x17201C)
    static let gruenRand = Color(startHex: 0x2F4438)
    static let gruenKnopf = Color(startHex: 0x1B2420)

    static let gelb = Color(startHex: 0xC8A53F)
    static let gelbGrund = Color(startHex: 0x1E1C17)

    static let rot = Color(startHex: 0xD0685C)
    static let rotGrund = Color(startHex: 0x221818)
    static let rotRand = Color(startHex: 0x5A2E2A)

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
}
