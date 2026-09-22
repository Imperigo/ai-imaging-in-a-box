import SwiftUI

/// Wie gross das Zeichen am Bild sitzt.
enum Streifengroesse: Equatable {
    /// Im Bildband.
    case klein
    /// Im Vergleich und bei den Varianten.
    case mittel
    /// Das grosse Bild.
    case gross
    /// Im geteilten Bild, mitgewachsen mit seiner Breite (in Punkten).
    case geteilt(breite: CGFloat)

    var schrift: CGFloat {
        switch self {
        case .klein: return 12
        case .mittel: return 13
        case .gross: return 14
        case .geteilt(let breite): return max(14, breite * 0.016)
        }
    }

    var rand: CGFloat {
        switch self {
        case .klein, .mittel, .gross: return 3
        case .geteilt(let breite): return max(3, breite * 0.004)
        }
    }

    var ecke: CGFloat {
        switch self {
        case .klein, .mittel: return 8
        case .gross: return 10
        case .geteilt: return 0
        }
    }
}

/// Das Prüfzeichen **am** Bild: Rand und Streifen gehören zusammen (Blatt «Die Zeichen»).
/// Der Rand trägt die Aussage über die Distanz, der Streifen über den Ausschnitt.
///
/// Hier wird nichts entschieden. Farbe, Wort, Zahl, Strichelung und Vorbehalt stehen fertig
/// in `Pruefzeichen` (Kern) und sind dort bewacht; diese Ansicht malt sie nur ab.
struct Zeichenrahmen: ViewModifier {
    let zeichen: Pruefzeichen
    var groesse: Streifengroesse = .mittel

    func body(content: Content) -> some View {
        content
            .overlay(alignment: .bottom) { streifen }
            .clipShape(RoundedRectangle(cornerRadius: groesse.ecke))
            .overlay(
                RoundedRectangle(cornerRadius: groesse.ecke)
                    .strokeBorder(Color(zeichen.art.rand),
                                  style: StrokeStyle(lineWidth: groesse.rand,
                                                     dash: zeichen.art.gestrichelt
                                                        ? [groesse.rand * 3, groesse.rand * 2]
                                                        : []))
                    .accessibilityHidden(true)
            )
    }

    private var streifen: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(zeichen.zeile)
                .foregroundStyle(Color(zeichen.art.schrift))
            // DER VORBEHALT STEHT IM STREIFEN, nicht daneben — damit er beim Teilen
            // mitgeht (Entscheid 20). *Ein Vorbehalt, der beim ersten Weiterreichen
            // abfällt, ist keiner.*
            ForEach(zeichen.vorbehalte, id: \.satz) { v in
                Text(v.kurz)
                    .foregroundStyle(Color(Pruefzeichen.vorbehaltSchrift))
            }
        }
        .font(Schrift.text(groesse.schrift, .semibold))
        .tracking(groesse.schrift * 0.04)
        .lineLimit(2)
        .minimumScaleFactor(0.8)
        .padding(.horizontal, groesse.schrift * 0.85)
        .padding(.vertical, groesse.schrift * 0.55)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(Pruefzeichen.streifen).opacity(Pruefzeichen.streifenDeckung))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(zeichen.vorlesetext)
    }
}

extension View {
    /// Setzt das Prüfzeichen an dieses Bild.
    func pruefzeichen(_ zeichen: Pruefzeichen, _ groesse: Streifengroesse = .mittel) -> some View {
        modifier(Zeichenrahmen(zeichen: zeichen, groesse: groesse))
    }
}

/// Die Fläche eines Bildes — das Bild selbst, oder **ausdrücklich** seine Lücke.
///
/// Drei Fälle, die nie gleich aussehen: geladen, die Datei fehlt (`vorhanden == false`),
/// und noch nicht geladen. *Ein Name ohne Datei sieht in einer Liste genauso aus wie einer
/// mit* — darum sagt die Lücke, welche sie ist.
struct Bildflaeche: View {
    let grafik: UIImage?
    var vorhanden: Bool? = nil

    var body: some View {
        if let grafik = grafik {
            Image(uiImage: grafik)
                .resizable()
                .scaledToFit()
                .accessibilityHidden(true)
        } else {
            ZStack {
                Color(Farbton(hex: "0e1013"))
                Text(vorhanden == false
                     ? "Die Mappe nennt dieses Bild, die Datei fehlt."
                     : "Bild nicht geladen.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .multilineTextAlignment(.center)
                    .padding(12)
                    .padding(.bottom, 28)
            }
            .aspectRatio(3.0 / 2.0, contentMode: .fit)
        }
    }
}
