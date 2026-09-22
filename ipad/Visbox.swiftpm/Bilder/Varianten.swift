import SwiftUI

/// Woraus die drei Varianten entstehen (Entscheid 32: **beides wählbar**).
enum Variantenquelle: String, CaseIterable, Identifiable {
    /// Dieselbe Skizze, dreimal mit anderem Startwert gerechnet.
    case startwerte
    /// Drei Ebenen, jede eine Variante (Entscheid 7).
    case ebenen

    var id: String { rawValue }

    var name: String {
        switch self {
        case .startwerte: return "Drei Startwerte"
        case .ebenen: return "Drei Ebenen"
        }
    }

    var satz: String {
        switch self {
        case .startwerte:
            return "Dieselbe Skizze, dreimal gerechnet — jedes Mal mit einem anderen Startwert."
        case .ebenen:
            return "Jede Ebene ist eine Variante. Gerechnet wird, was sichtbar ist."
        }
    }
}

/// Eine der drei Varianten, wie sie angezeigt wird.
struct Variantenbild: Identifiable {
    let id: String
    let titel: String
    let grafik: UIImage?
    let zeichen: Pruefzeichen
}

/// **Drei Varianten nebeneinander** (Entscheid 18) — eine gross, drei klein darunter.
///
/// Hier wird nur **angezeigt** und die Quelle gewählt; bestellt wird anderswo, und es liest
/// die Wahl aus `Bildbandstand.variantenquelle`. Es sind immer drei Plätze: Fehlt eine
/// Variante, steht ihr Platz leer **und sagt das** — zwei Bilder sähen sonst aus wie eine
/// vollständige Auswahl aus zweien.
///
/// Die Wahl wird mit einem Balken gezeigt, nicht mit einem blauen Rand wie im Entwurf
/// (Blatt «Varianten»): Blau heisst am Bild «Entwurf — nicht geprüft».
struct Variantenansicht: View {
    @ObservedObject var stand: Bildbandstand
    let varianten: [Variantenbild]

    @Environment(\.accessibilityReduceMotion) private var bewegungReduziert
    @State private var gewaehlt = 0

    static let plaetze = 3

    init(stand: Bildbandstand = .gemeinsam, varianten: [Variantenbild]) {
        self.stand = stand
        self.varianten = varianten
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 10) {
                Abschnittstitel(text: "Woraus die drei entstehen")
                HStack(spacing: 8) {
                    ForEach(Variantenquelle.allCases) { q in
                        Button(q.name) { stand.variantenquelle = q }
                            .buttonStyle(Wahlknopfstil(gewaehlt: stand.variantenquelle == q,
                                                       breite: nil))
                            .accessibilityAddTraits(stand.variantenquelle == q ? .isSelected : [])
                    }
                }
                Text(stand.variantenquelle.satz)
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }

            gross

            HStack(alignment: .top, spacing: 14) {
                ForEach(0..<Variantenansicht.plaetze, id: \.self) { i in
                    platz(i)
                }
            }
        }
    }

    @ViewBuilder
    private var gross: some View {
        if gewaehlt < varianten.count {
            let v = varianten[gewaehlt]
            Bildflaeche(grafik: v.grafik)
                .pruefzeichen(v.zeichen, .gross)
        } else {
            leer(Text("Diese Variante ist noch nicht gerechnet."))
                .aspectRatio(3.0 / 2.0, contentMode: .fit)
        }
    }

    private func platz(_ i: Int) -> some View {
        let an = gewaehlt == i
        let buchstabe = ["A", "B", "C"][i]
        return Button {
            if bewegungReduziert {
                gewaehlt = i
            } else {
                withAnimation(.easeInOut(duration: 0.18)) { gewaehlt = i }
            }
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Group {
                    if i < varianten.count {
                        Bildflaeche(grafik: varianten[i].grafik)
                            .pruefzeichen(varianten[i].zeichen, .klein)
                    } else {
                        leer(Text("noch nicht gerechnet"))
                    }
                }
                .frame(height: 130)
                Text(i < varianten.count ? "\(buchstabe) · \(varianten[i].titel)" : buchstabe)
                    .font(Schrift.text(14, .semibold))
                    .foregroundStyle(an ? Zeichenblatt.schrift : Zeichenblatt.leise)
                    .lineLimit(1)
                Rectangle()
                    .fill(an ? Zeichenblatt.schrift : Color.clear)
                    .frame(height: 3)
                    .accessibilityHidden(true)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(an ? .isSelected : [])
    }

    /// Ein leerer Platz — gestrichelt in der leisen Farbe, nicht in einer Urteilsfarbe.
    private func leer(_ satz: Text) -> some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(Zeichenblatt.linie, style: StrokeStyle(lineWidth: 1, dash: [6, 4]))
            satz
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
                .multilineTextAlignment(.center)
                .padding(10)
        }
        .frame(maxWidth: .infinity)
    }
}
