import SwiftUI

/// Die Richtung, in der die Leiste läuft.
enum Leistenachse {
    /// Querformat: am Rand, links oder rechts (Entscheid 9).
    case senkrecht
    /// Hochformat: unten, in Daumenreichweite (Blatt «MainHoch»).
    case waagrecht
}

/// Die Werkzeugleiste am Rand — **nicht über dem Bild.** Eine Hand, die zeichnet, liegt
/// auf dem Glas und verdeckt, was darunter liegt (Blatt «Die Zeichen»).
///
/// Sie schreibt nur in `Leistenwahl`; was ein Werkzeug *tut*, entscheidet die
/// Zeichenfläche. Jedes Ziel ist 60 × 60 pt, mit 10 pt Luft.
///
/// **Knöpfe ohne Wirkung gibt es hier nicht.** «Auf die andere Seite» und «Vollbild»
/// erscheinen nur, wenn die Leiste in einem `Arbeitsplatz` sitzt, der sie auch umsetzt
/// (`kannUmlegen`, `kannVollbild`). In der heutigen `Startansicht` steht die Leiste fest
/// links; dort zeigt sie diese beiden Knöpfe darum nicht — *ein Bedienelement ohne Wirkung
/// ist schlimmer als keines.*
struct Leiste: View {
    @ObservedObject var wahl: Leistenwahl
    var achse: Leistenachse
    var kannUmlegen: Bool
    var kannVollbild: Bool

    init(wahl: Leistenwahl = .gemeinsam, achse: Leistenachse = .senkrecht,
         kannUmlegen: Bool = false, kannVollbild: Bool = false) {
        self.wahl = wahl
        self.achse = achse
        self.kannUmlegen = kannUmlegen
        self.kannVollbild = kannVollbild
    }

    var body: some View {
        Group {
            switch achse {
            case .senkrecht:
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: Zeichenblatt.abstand) { inhalt }
                        .padding(.vertical, 16)
                        .frame(maxWidth: .infinity)
                }
            case .waagrecht:
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: Zeichenblatt.abstand) { inhalt }
                        .padding(.horizontal, 22)
                        .frame(maxHeight: .infinity)
                }
            }
        }
        .background(Zeichenblatt.leiste)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Werkzeugleiste")
    }

    @ViewBuilder
    private var inhalt: some View {
        ForEach(Leistenwerkzeug.allCases) { w in
            Button {
                wahl.werkzeug = w
            } label: {
                Image(systemName: w.symbol)
                    .font(.system(size: 24, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: wahl.werkzeug == w))
            .accessibilityLabel(w.name)
            .accessibilityAddTraits(wahl.werkzeug == w ? .isSelected : [])
        }

        trenner

        ForEach(Leistenstrich.allCases) { s in
            Button {
                wahl.strich = s
            } label: {
                Capsule()
                    .frame(width: 26, height: s.bildDicke)
                    .rotationEffect(.degrees(-35))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: wahl.strich == s))
            .accessibilityLabel(s.name)
            .accessibilityAddTraits(wahl.strich == s ? .isSelected : [])
        }

        if kannUmlegen || kannVollbild {
            trenner
        }

        if kannUmlegen && achse == .senkrecht {
            // NUR IM QUERFORMAT. Im Hochformat sitzt die Leiste unten; «links oder rechts»
            // gibt es dort nicht, und ein Knopf dafür täte nichts.
            Button {
                wahl.seite = wahl.seite.andere
            } label: {
                Image(systemName: "arrow.left.arrow.right")
                    .font(.system(size: 22, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .accessibilityLabel("Leiste auf die andere Seite")
            .accessibilityValue(wahl.seite == .links ? "sitzt links" : "sitzt rechts")
        }

        if kannVollbild {
            Button {
                wahl.vollbild = true
            } label: {
                Image(systemName: "arrow.up.left.and.arrow.down.right")
                    .font(.system(size: 22, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .accessibilityLabel("Vollbild")
        }
    }

    private var trenner: some View {
        Rectangle()
            .fill(Zeichenblatt.linie)
            .frame(width: achse == .senkrecht ? 44 : 1, height: achse == .senkrecht ? 1 : 44)
            .padding(achse == .senkrecht ? Edge.Set.vertical : Edge.Set.horizontal, 6)
            .accessibilityHidden(true)
    }
}
