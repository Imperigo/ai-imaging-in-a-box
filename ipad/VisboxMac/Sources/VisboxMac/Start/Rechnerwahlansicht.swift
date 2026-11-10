import Foundation
import AppKit
import SwiftUI
import VisboxKern

/// **«Wer rechnet?»** — Einrichten › Rechner, nach Blatt 28, Feld 2 («Visbox eigenständig»,
/// Schritt 6, 20.10.2026).
///
/// Je Arbeit (Blender-Render, Bildmodell, Bedien-KI) zwei Felder: «Heim-PC» und «Dieses
/// Gerät». Der Heim-PC ist gewählt; «Dieses Gerät» steht da, aber gesperrt mit seinem Grund,
/// bis ein lokaler Rechner gebaut ist. **Die Wahl ändert heute nichts am Weg** — alles geht an
/// den Heim-PC —, sie ist sichtbar und gespeichert. Was wählbar ist und warum nicht, sagt der
/// Kern (`Rechnerwahl`, mit Proben); hier wird gezeichnet, gespeichert und am Mac nachgesehen,
/// ob es Blender gibt.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
struct Rechnerwahlansicht: View {
    @ObservedObject var leitung: Heimleitung
    @ObservedObject var leitungstakt: Leitungssteuerung
    let zurueck: () -> Void

    @StateObject private var speicher = Rechnerwahlspeicher()

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(Rechnerwahl.titel)
                .font(Macschriften.schrift(.titel, 26))
            Text(Rechnerwahl.untertitel)
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
            ForEach(Rechenarbeit.allCases, id: \.self) { arbeit in
                Rechnerzeile(arbeit: arbeit, speicher: speicher,
                             zusatz: Rechnerwahl.zusatzHeim(fuer: arbeit,
                                                            lage: leitungstakt.schalter.lage,
                                                            eingerichtet: !leitung.braucheEinrichten))
            }
            Text(Rechnerwahl.mcpSatz)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, 4)
            Text(Rechnerwahl.heuteSatz)
                .font(Macschriften.schrift(.text, 12))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
            HStack {
                Button("← Zurück", action: zurueck)
                    .buttonStyle(.link)
                Spacer()
            }
            .padding(.top, 6)
        }
        .padding(28)
        .frame(width: 560, alignment: .leading)
    }
}

/// Eine Arbeit: der Titel, darunter die zwei Felder.
private struct Rechnerzeile: View {
    let arbeit: Rechenarbeit
    @ObservedObject var speicher: Rechnerwahlspeicher
    let zusatz: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(arbeit.titel)
                .font(Macschriften.schrift(.text, 14, .semibold))
                .padding(.top, 8)
            HStack(spacing: 10) {
                ForEach(Rechnerort.allCases, id: \.self) { ort in
                    Rechnerfeld(titel: ort.titel, zeile: zeile(ort),
                                gewaehlt: speicher.wahl.wirksam(fuer: arbeit,
                                                                befund: speicher.befund) == ort,
                                waehlbar: verfuegbarkeit(ort).waehlbar,
                                waehle: { speicher.waehle(ort, fuer: arbeit) })
                }
            }
        }
    }

    private func verfuegbarkeit(_ ort: Rechnerort) -> Verfuegbarkeit {
        Rechnerwahl.verfuegbarkeit(ort, fuer: arbeit, befund: speicher.befund)
    }

    /// «· verbunden» am Heim-PC, «nicht verfügbar — …» am Gerät.
    private func zeile(_ ort: Rechnerort) -> String {
        if let gesperrt = verfuegbarkeit(ort).zeile { return gesperrt }
        return ort == .heimPC ? "· " + zusatz : ""
    }
}

/// Ein Feld («.wahl» im Blatt): blau umrandet, wenn gewählt; gesperrt in der leisen Schriftfarbe auf der
/// Fläche, mit gestricheltem Rand.
///
/// A0270 (Geräteprobe 0.3.75, Befund A0156): Ein Feld halb durchsichtig zu zeichnen (`.opacity(0.45)`)
/// machte «Dieses Gerät» im hellen Modus sehr blass (Schrift und Rand zusammen unter 3:1). Gesperrt
/// heisst jetzt: eigene, deckende Farben, jede mindestens 3:1 gegen ihren Grund (WCAG 1.4.11);
/// gerechnet in `tests/test_rechnerwahl_kontrast_a0270.py`.
///
/// **Gesperrt ist es für Hilfsmittel trotzdem (A0270 Runde 2, Mangel M1).** `.disabled(_:)` bleibt weg:
/// Apple beschreibt es als Bedingung, ob jemand mit der Ansicht umgehen kann, nennt aber keinen
/// Dimmfaktor (developer.apple.com/documentation/swiftui/view/disabled(_:)); ein Wert, den die Probe
/// nicht kennt, lässt sich nicht gegen 3:1 rechnen. Darum ist ein gesperrtes Feld hier **gar kein
/// Knopf**: eine Beschriftung (`isStaticText`, «ein statischer Text, den man nicht ändern kann»), ohne
/// `isButton`, mit `accessibilityRespondsToUserInteraction(false)` («Switch Control, Sprachsteuerung
/// oder volle Tastaturbedienung» sprechen es nicht an). VoiceOver liest Titel und Zeile in einem
/// («… nicht verfügbar — Grund»). Am echten Mac gehört das Hören noch zur Geräteprobe.
private struct Rechnerfeld: View {
    let titel: String
    let zeile: String
    let gewaehlt: Bool
    let waehlbar: Bool
    let waehle: () -> Void

    private static let blau = Color(.sRGB, red: 0x2f / 255, green: 0x6f / 255, blue: 0xd6 / 255)
    // HELL UND DUNKEL (A0156): auf dunklem Grund das tiefe Blau, auf hellem ein blasses.
    private static let blauGrund = Color(nsColor: NSColor(name: nil) { erscheinung in
        erscheinung.bestMatch(from: [.darkAqua, .aqua]) == .darkAqua
            ? NSColor(srgbRed: 0x17 / 255, green: 0x23 / 255, blue: 0x3a / 255, alpha: 1)
            : NSColor(srgbRed: 0xE3 / 255, green: 0xEC / 255, blue: 0xFB / 255, alpha: 1)
    })

    /// Der Rand: blau, wenn gewählt; sonst der Ring; gesperrt in der leisen Schriftfarbe, gestrichelt.
    private var rand: Color { gewaehlt ? Rechnerfeld.blau : (waehlbar ? Startfarbe.ring : Startfarbe.leise) }

    /// Wählbar: ein Knopf. Gesperrt: kein Knopf, sondern eine Beschriftung (siehe oben).
    @ViewBuilder
    var body: some View {
        if waehlbar {
            Button(action: waehle) { inhalt }
                .buttonStyle(.plain)
        } else {
            inhalt
                .accessibilityElement(children: .combine)
                .accessibilityRemoveTraits(.isButton)
                .accessibilityAddTraits(.isStaticText)
                .accessibilityRespondsToUserInteraction(false)
        }
    }

    private var inhalt: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(titel)
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(waehlbar ? Color.primary : Startfarbe.leise)
            if !zeile.isEmpty {
                Text(zeile)
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 8)
            .fill(gewaehlt ? Rechnerfeld.blauGrund : (waehlbar ? Color.clear : Startfarbe.flaeche)))
        .overlay(RoundedRectangle(cornerRadius: 8)
            .stroke(rand, style: StrokeStyle(lineWidth: 1, dash: waehlbar ? [] : [4, 3])))
        .contentShape(Rectangle())
    }
}

/// Die Wahl in den App-Einstellungen (`Rechnerwahl.schluessel`) und der Befund dieses Mac.
///
/// **Nur die Wahl liegt dort** — welcher Ort je Arbeit, als kleines JSON-Objekt; nichts zur
/// Kopplung (die liegt im Schlüsselbund und in `Heimgedaechtnis`).
@MainActor
final class Rechnerwahlspeicher: ObservableObject {
    @Published private(set) var wahl: Rechnerwahl
    /// Was die App über diesen Mac weiss: Blender am üblichen Ort, Arbeitsspeicher.
    let befund: Rechnerbefund

    private let ablage: UserDefaults

    init(ablage: UserDefaults = .standard) {
        self.ablage = ablage
        wahl = Rechnerwahl.aus(daten: ablage.data(forKey: Rechnerwahl.schluessel))
        befund = Rechnerbefund(
            blenderGefunden: FileManager.default.fileExists(atPath: Rechnerwahl.blenderOrt),
            arbeitsspeicher: ProcessInfo.processInfo.physicalMemory)
    }

    func waehle(_ ort: Rechnerort, fuer arbeit: Rechenarbeit) {
        guard wahl.waehle(ort, fuer: arbeit, befund: befund) else { return }
        ablage.set(wahl.alsDaten(), forKey: Rechnerwahl.schluessel)
    }
}
