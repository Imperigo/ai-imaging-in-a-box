import SwiftUI

/// Wie Vorher und Nachher nebeneinanderliegen (Entscheid 17: **beides, umschaltbar**).
enum Bildvergleichsart: String, CaseIterable, Identifiable {
    case nebeneinander
    case wischregler

    var id: String { rawValue }

    var name: String {
        switch self {
        case .nebeneinander: return "Nebeneinander"
        case .wischregler: return "Wischregler"
        }
    }

    /// Der Satz neben dem Schalter (Blatt «Bilder»).
    var hinweis: String {
        switch self {
        case .nebeneinander: return "Beide gleichzeitig im Blick, jedes halb so gross."
        case .wischregler: return "Voll gross, der Unterschied springt an der Kante ins Auge."
        }
    }
}

/// Vorher (die Unterlage) und Nachher (aus der KI) — nebeneinander oder mit Wischregler.
///
/// **Das Vorher ist die Unterlage**, das Bild, über das skizziert wurde (Feld `vorher` der
/// Mappe, seit dem 23.09.2026). Das Blatt «Bilder» beschriftet es «Aus dem Modell»; das
/// stimmt nur, wenn über ein Bild aus dem Modell skizziert wurde — über ein früheres Bild der
/// KI skizziert, wäre es falsch. Darum steht hier «Unterlage»; das Blatt «Bilder» ist so nachgezogen
/// (23.09.2026) und dort als **Owner-Entscheid offen** markiert.
///
/// **Das Vorher trägt hier kein Urteil, und es sagt das.** Ein Rand in einer der
/// Urteilsfarben hiesse, es sei in diesem Vergleich geprüft worden. Das Zeichen
/// des Nachher sitzt am Nachher — beim Wischregler am ganzen Bild, weil beide Hälften zu
/// demselben Nachher gehören.
struct Bildvergleich: View {
    let vorher: UIImage?
    let nachher: UIImage?
    let zeichen: Pruefzeichen
    let art: Bildvergleichsart

    /// Wo der Schnitt sitzt, 0 bis 1 — links davon die KI, rechts die Unterlage.
    @State private var schnitt: Double = 0.5

    var body: some View {
        switch art {
        case .nebeneinander: nebeneinander
        case .wischregler: wischregler
        }
    }

    private var nebeneinander: some View {
        HStack(alignment: .top, spacing: 18) {
            VStack(alignment: .leading, spacing: 8) {
                Abschnittstitel(text: "Unterlage")
                Bildflaeche(grafik: vorher)
                    .overlay(alignment: .bottom) {
                        Text(Bildvergleich.markeVorher)
                            .font(Schrift.text(13, .semibold))
                            .foregroundStyle(Zeichenblatt.leise)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(Pruefzeichen.streifen)
                                .opacity(Pruefzeichen.streifenDeckung))
                    }
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                    .overlay(RoundedRectangle(cornerRadius: 8)
                        .strokeBorder(Zeichenblatt.linie, lineWidth: 3))
            }
            VStack(alignment: .leading, spacing: 8) {
                Abschnittstitel(text: "Aus der KI")
                Bildflaeche(grafik: nachher)
                    .pruefzeichen(zeichen, .mittel)
            }
        }
    }

    private var wischregler: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Links die KI, rechts die Unterlage")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
            GeometryReader { geo in
                ZStack(alignment: .topLeading) {
                    // DAS VORHER SAGT AUCH HIER, DASS ES KEIN URTEIL TRAEGT (Durchsicht B,
                    // 22.09.2026): Nebeneinander stand es schon da, beim Wischregler fehlte
                    // es — und die Hälfte rechts der Kante lag unter dem Zeichen des Nachher,
                    // als gehörte sie dazu. Die Marke sitzt IN der Schicht des Vorher: Wo das
                    // Nachher darüber liegt, deckt es sie mit ab, wie das Bild selbst.
                    Bildflaeche(grafik: vorher)
                        .frame(width: geo.size.width, height: geo.size.height)
                        .overlay(alignment: .topTrailing) {
                            marke(Bildvergleich.markeVorher)
                        }
                    Bildflaeche(grafik: nachher)
                        .frame(width: geo.size.width, height: geo.size.height)
                        .overlay(alignment: .topLeading) { marke("AUS DER KI") }
                        .mask(alignment: .leading) {
                            Rectangle()
                                .frame(width: geo.size.width * CGFloat(schnitt))
                        }
                    Rectangle()
                        .fill(Zeichenblatt.schrift)
                        .frame(width: 2, height: geo.size.height)
                        .offset(x: geo.size.width * CGFloat(schnitt) - 1)
                        .shadow(color: .black.opacity(0.6), radius: 1)
                        .accessibilityHidden(true)
                }
                .contentShape(Rectangle())
                // DER FINGER ZIEHT DEN SCHNITT DIREKT AM BILD. Ohne Übergang: Die Kante
                // folgt dem Finger, eine Bewegung, die ihm nachliefe, wäre eine Lüge über
                // die Stelle.
                .gesture(DragGesture(minimumDistance: 0).onChanged { zug in
                    guard geo.size.width > 0 else { return }
                    schnitt = min(1, max(0, Double(zug.location.x / geo.size.width)))
                })
            }
            .aspectRatio(seitenverhaeltnis, contentMode: .fit)
            .pruefzeichen(zeichen, .gross)

            HStack(spacing: 14) {
                Text("Schnitt")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                Slider(value: $schnitt, in: 0...1)
                    .tint(Zeichenblatt.schrift)
                    .frame(minHeight: Zeichenblatt.tippzielMindestens)
                    .accessibilityLabel("Schnitt zwischen KI und Unterlage")
                Text("\(Int((schnitt * 100).rounded())) %")
                    .font(Schrift.zahl(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .frame(width: 52, alignment: .trailing)
            }
        }
    }

    /// Die Marke am Vorher, in beiden Arten dieselbe.
    static let markeVorher = "UNTERLAGE · hier kein Urteil"

    /// Eine Beschriftung auf dem Bild, im Streifen des Prüfzeichens, aber leise — **keine**
    /// Urteilsfarbe, denn sie sagt nichts über ein Urteil.
    private func marke(_ text: String) -> some View {
        Text(text)
            .font(Schrift.text(12, .semibold))
            .foregroundStyle(Zeichenblatt.leise)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(Color(Pruefzeichen.streifen).opacity(Pruefzeichen.streifenDeckung))
            .padding(8)
    }

    /// Das Seitenverhältnis des Nachher — sonst 3:2 wie im Entwurf.
    private var seitenverhaeltnis: CGFloat {
        guard let n = nachher, n.size.height > 0 else { return 3.0 / 2.0 }
        return n.size.width / n.size.height
    }
}
