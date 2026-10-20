import SwiftUI
import VisboxKern

/// Das Band oben im Fenster, wenn kein Rechner da ist — **Blatt 28, Feld 1** («Visbox
/// eigenständig», Schritt 2, Entscheid 103b, 20.10.2026):
///
///     Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht. · [Erneut verbinden]
///
/// Es **ersetzt nichts**: Darunter bleibt die Arbeit (Knoten aus dem Bündel) bzw. der Start.
/// Bei einer Absage der Tür (401/403) steht derselbe Aufbau mit eigenem Satz und «Einrichten».
/// Was es sagt und wann, entscheidet der Kern (`Leitungsschalter.band`, `Rechnerband`, mit
/// Proben); hier wird nur gezeichnet. Das weiche Band vor der Schwelle zeichnet `KurzWegBand`.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
struct Leitungsband: View {
    let band: Rechnerband
    let erneutVerbinden: () -> Void
    let einrichten: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Text(band.titel)
                .font(Macschriften.schrift(.text, 14, .semibold))
            if let satz = band.satz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 14))
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
            Spacer(minLength: 8)
            if let knopf = band.knopf {
                Button(knopf.wort) { drueck(knopf) }
                    .buttonStyle(Bandknopf())
            }
        }
        .foregroundStyle(Color(band: Rechnerband.schrift))
        .padding(.horizontal, 14)
        .frame(height: 40)
        .frame(maxWidth: .infinity)
        .background(Color(band: Rechnerband.grund))
        .overlay(alignment: .bottom) {
            Rectangle().fill(Color(band: Rechnerband.rand)).frame(height: 1)
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel(band.vorgelesen)
    }

    private func drueck(_ knopf: Rechnerband.Knopf) {
        switch knopf {
        case .erneutVerbinden: erneutVerbinden()
        case .einrichten: einrichten()
        }
    }
}

/// Der Knopf im Band: umrandet, ohne Füllung (`.b2` im Blatt).
private struct Bandknopf: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Macschriften.schrift(.text, 13))
            .foregroundStyle(Startfarbe.hell)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(RoundedRectangle(cornerRadius: 8).stroke(Startfarbe.ring))
            .opacity(configuration.isPressed ? 0.7 : 1)
            .contentShape(Rectangle())
    }
}

/// Das weiche Band vor der Schwelle (20.10.2026): «Heim-PC kurz nicht erreichbar — verbinde
/// neu …» — ein Aussetzer, kein Zustand; darum leise, schwebend und ohne Knopf.
struct KurzWegBand: View {
    let zeigen: Bool

    var body: some View {
        if zeigen {
            Text(Leitungssaetze.kurzWeg)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.gelb)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Capsule().fill(Startfarbe.flaeche))
                .overlay(Capsule().stroke(Startfarbe.linie))
                .padding(.top, 10)
                .accessibilityLabel(Leitungssaetze.kurzWeg)
        }
    }
}

private extension Color {
    /// Ein Farbton des Kerns als Farbe — mit eigenem Etikett, damit es neben anderen
    /// Umwandlungen in der App nicht zusammenstösst.
    init(band ton: Farbton) {
        self.init(.sRGB, red: Double(ton.rot) / 255, green: Double(ton.gruen) / 255,
                  blue: Double(ton.blau) / 255, opacity: 1)
    }
}
