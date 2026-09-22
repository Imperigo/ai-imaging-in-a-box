import SwiftUI

/// Woraus die drei Varianten entstehen (Entscheid 32: **beides wählbar**).
enum Variantenquelle: String, CaseIterable, Identifiable {
    /// Das Bild aus dem Modell, dreimal mit anderem Startwert gerechnet.
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
            return "Das Bild aus dem Modell, dreimal gerechnet — jedes Mal mit einem anderen "
                + "Startwert."
        case .ebenen:
            return "Jede Ebene ist eine Variante. «In die Mappe legen» legt dann jede sichtbare "
                + "Ebene als eigene Skizze ab; unten zwei oder drei davon wählen."
        }
    }

    /// Wie die Zeichnung abgelegt wird. **Bei «Drei Ebenen» als eine Skizze je Ebene** —
    /// sonst gäbe es in der Mappe nichts, woraus eine Ebenen-Reihe bestehen könnte.
    var ausgabeart: Ebenenstapel.Ausgabeart {
        switch self {
        case .startwerte: return .eineSkizze
        case .ebenen: return .ebenenAlsVarianten
        }
    }

    /// Die Art einer Reihe aus der Mappe (`variantengruppe.art`), oder `nil`, wenn der
    /// Server eine schrieb, die die App nicht kennt.
    init?(art: String?) {
        switch art {
        case "startwerte": self = .startwerte
        case "ebenen": self = .ebenen
        default: return nil
        }
    }
}

/// **Drei Varianten nebeneinander** (Entscheid 18) — eine gross, drei klein darunter.
///
/// Gezeigt wird **eine Reihe aus der Mappe** (`variantengruppe`), jede Variante mit ihrem
/// eigenen Prüfzeichen. Es sind immer drei Plätze: Fehlt eine Variante, steht ihr Platz
/// leer **und sagt das** — zwei Bilder sähen sonst aus wie eine vollständige Auswahl aus
/// zweien. Hat die Reihe mehr als drei, steht das darüber.
///
/// Die Wahl wird mit einem Balken gezeigt, nicht mit einem blauen Rand wie im Entwurf
/// (Blatt «Varianten»): Blau heisst am Bild «Entwurf — nicht geprüft».
struct Variantenansicht: View {
    @ObservedObject var stand: Bildbandstand
    let gruppe: String

    @Environment(\.accessibilityReduceMotion) private var bewegungReduziert
    @State private var gewaehlt = 0

    static let plaetze = Rechenbestellung.reihenlaenge

    init(stand: Bildbandstand = .gemeinsam, gruppe: String) {
        self.stand = stand
        self.gruppe = gruppe
    }

    private var varianten: [Bandbild] { stand.reihenbilder(gruppe) }

    private var kopfsatz: String {
        let g = varianten.first?.angaben.variantengruppe
        let quelle = Variantenquelle(art: g?.art)?.name ?? "Reihe unbekannter Art"
        guard let von = g?.von else { return quelle + " · wie viele es sind, sagt die Mappe nicht" }
        if von > Variantenansicht.plaetze {
            return quelle + " · \(von) Varianten, hier die ersten \(Variantenansicht.plaetze)"
        }
        return quelle + " · \(varianten.count) von \(von) in der Mappe"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 6) {
                Abschnittstitel(text: "Varianten nebeneinander")
                Text(kopfsatz)
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
            Bildflaeche(grafik: v.grafik, vorhanden: v.vorhanden)
                .pruefzeichen(v.pruefzeichen(stand.lesart(v)), .gross)
        } else {
            leer(Text("Diese Variante ist nicht in der Mappe."))
                .aspectRatio(3.0 / 2.0, contentMode: .fit)
        }
    }

    private func titel(_ v: Bandbild) -> String {
        if let eigener = v.angaben.titel { return eigener }
        let g = v.angaben.variantengruppe
        if let seed = g?.seed { return "Startwert \(seed)" }
        if let skizze = g?.skizze { return skizze }
        return stand.name(v)
    }

    private func platz(_ i: Int) -> some View {
        let an = gewaehlt == i
        let buchstabe = ["A", "B", "C", "D", "E", "F", "G", "H"][min(i, 7)]
        // KEIN `Button` UM DEN PLATZ: Im Prüfzeichen der kleinen Kachel sitzt ein eigener
        // Knopf (der Vorbehalt klappt auf, `Zeichenrahmen`), und ein Knopf in einem Knopf
        // bekommt in SwiftUI nicht verlässlich seinen eigenen Tipp.
        return VStack(alignment: .leading, spacing: 6) {
            Group {
                if i < varianten.count {
                    Bildflaeche(grafik: varianten[i].grafik, vorhanden: varianten[i].vorhanden)
                        .pruefzeichen(varianten[i].pruefzeichen(stand.lesart(varianten[i])),
                                      .klein)
                } else {
                    leer(Text("nicht in der Mappe"))
                }
            }
            .frame(height: 130)
            Text(i < varianten.count ? "\(buchstabe) · \(titel(varianten[i]))" : buchstabe)
                .font(Schrift.text(14, .semibold))
                .foregroundStyle(an ? Zeichenblatt.schrift : Zeichenblatt.leise)
                .lineLimit(1)
            Rectangle()
                .fill(an ? Zeichenblatt.schrift : Color.clear)
                .frame(height: 3)
                .accessibilityHidden(true)
        }
        .frame(maxWidth: .infinity)
        .contentShape(Rectangle())
        .onTapGesture { waehle(i) }
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(an ? [.isButton, .isSelected] : [.isButton])
        .accessibilityAction { waehle(i) }
    }

    private func waehle(_ i: Int) {
        if bewegungReduziert {
            gewaehlt = i
        } else {
            withAnimation(.easeInOut(duration: 0.18)) { gewaehlt = i }
        }
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
