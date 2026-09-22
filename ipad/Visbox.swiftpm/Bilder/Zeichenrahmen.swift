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
///
/// **Der Vorbehalt wird nicht abgeschnitten** (Durchsicht B, 22.09.2026). In der
/// 160-pt-Kachel des Bildbands schnitt `lineLimit(2)` das kurze Wort «SKIZZE NICHT
/// ANGEKOMMEN — aus Tiefenkarte und Text gerechnet» mitten im Satz ab. Jetzt steht dort
/// zugeklappt der **feste Anfang ganz** (`Vorbehalt.kopf`) mit einem Pfeil, und ein Tipp auf
/// den Streifen klappt das kurze Wort auf — ohne Zeilengrenze, notfalls kleiner gesetzt.
/// In allen grösseren Stufen und im geteilten Bild steht es immer ganz da. *Am Gerät
/// unbestätigt*, ebenso, dass der Tipp auf den Streifen nicht die Kachel öffnet.
struct Zeichenrahmen: ViewModifier {
    let zeichen: Pruefzeichen
    var groesse: Streifengroesse = .mittel

    @State private var aufgeklappt = false

    /// Nur die kleine Kachel klappt; überall sonst ist Platz für den ganzen Vorbehalt.
    private var klappbar: Bool {
        groesse == .klein && !zeichen.vorbehalte.isEmpty
    }

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
                .lineLimit(2)
                .minimumScaleFactor(0.8)
            // DER VORBEHALT STEHT IM STREIFEN, nicht daneben — damit er beim Teilen
            // mitgeht (Entscheid 20). *Ein Vorbehalt, der beim ersten Weiterreichen
            // abfällt, ist keiner.*
            ForEach(zeichen.vorbehalte, id: \.satz) { v in
                if klappbar {
                    Button {
                        aufgeklappt.toggle()
                    } label: {
                        HStack(alignment: .firstTextBaseline, spacing: 4) {
                            Text(aufgeklappt ? v.kurz : v.kopf)
                                .lineLimit(aufgeklappt ? nil : 2)
                                .minimumScaleFactor(aufgeklappt ? 0.7 : 0.8)
                                .multilineTextAlignment(.leading)
                            Image(systemName: aufgeklappt ? "chevron.up" : "chevron.down")
                                .font(.system(size: groesse.schrift * 0.8, weight: .semibold))
                        }
                        .foregroundStyle(Color(Pruefzeichen.vorbehaltSchrift))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                } else {
                    Text(v.kurz)
                        .foregroundStyle(Color(Pruefzeichen.vorbehaltSchrift))
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
        .font(Schrift.text(groesse.schrift, .semibold))
        .tracking(groesse.schrift * 0.04)
        .padding(.horizontal, groesse.schrift * 0.85)
        .padding(.vertical, groesse.schrift * 0.55)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(Pruefzeichen.streifen).opacity(Pruefzeichen.streifenDeckung))
        // DER BILDSCHIRMLESER HOERT IMMER DEN GANZEN SATZ, zugeklappt oder nicht
        // (`vorlesetext` trägt jeden Vorbehalt in voller Länge).
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
                Zeichenblatt.luecke
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
