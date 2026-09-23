import SwiftUI

/// «In die Mappe legen» — **die Skizze geht ins Parkfach und von dort hinaus**, mit ihrer
/// Unterlage (`ueber`), wenn eine liegt und sichtbar ist.
///
/// **Der Ort ist das Seitenfeld, unten** (Blätter «Main» und «MainHoch»), eingesetzt von
/// `Seitentafel` — unter Ebenen **und** Mappe, damit er nicht hinter dem anderen Reiter
/// liegt. Bis zum 23.09.2026 stand er in der Verbindungszeile, weil das Seitenfeld noch
/// nirgends hing; dort ist er entfernt (es gibt ihn einmal, nicht zweimal).
///
/// Nach dem Tippen steht ein Satz da, wenn es einen zu sagen gibt (nichts gezeichnet,
/// geparkt, weil niemand antwortet, eine Unterlage aus einer anderen Mappe, …). Geht sie
/// gleich hinaus, sagt es die Marke in der Verbindungszeile. Was hinausgeht, entscheidet
/// der Kern (`Ablageplan`), nicht dieser Knopf.
///
/// *Gebaut, nicht übersetzt, am Gerät unbestätigt (23.09.2026).*
@MainActor
struct Mappenknopf: View {
    @ObservedObject var stand: Verbindungsstand
    let skizzenquelle: Skizzenquelle
    @State private var satz: String?

    /// `skizzenquelle` `nil` heisst: **die Vorgabe** — die sichtbaren Ebenen und die
    /// Unterlage der Zeichenfläche, abgelegt so, wie die Wahl bei den Varianten es will
    /// (bei «Drei Ebenen» jede sichtbare Ebene als eigene Skizze, sonst eine;
    /// `Variantenquelle.ausgabeart`).
    ///
    /// Warum die Vorgabe im Rumpf steht und nicht als Standardwert (Mac-Übersetzung vom
    /// 22.09.2026, damals an der Verbindungszeile): Ein Standardwert wird **ausserhalb** des
    /// Hauptfadens ausgewertet; im Rumpf von `init` einer `@MainActor`-Ansicht ist er
    /// gesichert.
    init(stand: Verbindungsstand = .gemeinsam, skizzenquelle: Skizzenquelle? = nil) {
        self.stand = stand
        self.skizzenquelle = skizzenquelle ?? {
            Zeichenstand.gemeinsam.skizzenpaket(
                Bildbandstand.gemeinsam.variantenquelle.ausgabeart)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Button {
                satz = stand.legeInDieMappe(skizzenquelle())
            } label: {
                Text("In die Mappe legen")
                    .font(Schrift.text(17, .semibold))
            }
            // 56 PT WIE AUF DEM BLATT: der eine Knopf, der etwas hinausschickt.
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil, hoehe: 56))
            .accessibilityHint("Legt die sichtbaren Ebenen als Skizze in die Mappe der "
                               + "HomeStation, mit der Unterlage, wenn eine sichtbar ist. "
                               + "Nichts rechnet von selbst.")
            if let satz {
                Text(satz)
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.schrift)
                    .fixedSize(horizontal: false, vertical: true)
                    .onTapGesture { self.satz = nil }
            }
            Text("Sie wird als offen abgelegt und wartet. Ist die HomeStation nicht da, "
                 + "bleibt sie hier liegen, bis sie wieder da ist.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}
