import Foundation
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

/// Ein Feld («.wahl» im Blatt): blau umrandet, wenn gewählt; halb durchsichtig, wenn gesperrt.
private struct Rechnerfeld: View {
    let titel: String
    let zeile: String
    let gewaehlt: Bool
    let waehlbar: Bool
    let waehle: () -> Void

    private static let blau = Color(.sRGB, red: 0x2f / 255, green: 0x6f / 255, blue: 0xd6 / 255)
    private static let blauGrund = Color(.sRGB, red: 0x17 / 255, green: 0x23 / 255, blue: 0x3a / 255)

    var body: some View {
        Button(action: waehle) {
            VStack(alignment: .leading, spacing: 2) {
                Text(titel)
                    .font(Macschriften.schrift(.text, 14))
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
                .fill(gewaehlt ? Rechnerfeld.blauGrund : Color.clear))
            .overlay(RoundedRectangle(cornerRadius: 8)
                .stroke(gewaehlt ? Rechnerfeld.blau : Startfarbe.ring))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(!waehlbar)
        .opacity(waehlbar ? 1 : 0.45)
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
