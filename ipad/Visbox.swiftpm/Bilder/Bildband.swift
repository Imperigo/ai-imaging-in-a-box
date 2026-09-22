import SwiftUI

/// Die Bilder, die der Server zu einem Projekt liefert — **je mit ihrem Prüfzeichen.**
///
/// Jedes Bild trägt ein Zeichen, auch das ungeprüfte: *Kein Zeichen sähe aus wie kein
/// Problem.* Die Wahl wird **nicht** mit einem grünen Rand gezeigt, wie im Entwurf (Blatt
/// «Main»), sondern mit einem Balken darunter — grün heisst am Bild «bestanden», und ein
/// gewähltes Bild ist nicht bestanden, nur weil es gewählt ist.
///
/// Ein Tipp öffnet das Bild gross (`Bildansicht`), mit dem Schalter Prüfen/Entwerfen, dem
/// Vergleich, dem eigenen Namen und dem Teilen. Eingehängt ist das Band seit dem 22.09.2026
/// im Seitenfeld, Reiter «Mappe» (`Mappentafel`).
struct Bildband: View {
    @ObservedObject var stand: Bildbandstand
    @State private var offen: Bandbild?

    init(stand: Bildbandstand = .gemeinsam) {
        self.stand = stand
    }

    var body: some View {
        Group {
            if stand.bilder.isEmpty {
                Text("Noch keine Bilder in der Mappe.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .frame(maxWidth: .infinity, minHeight: 80, alignment: .leading)
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(alignment: .top, spacing: Zeichenblatt.abstand + 2) {
                        ForEach(stand.bilder) { b in kachel(b) }
                    }
                    .padding(.vertical, 4)
                }
            }
        }
        .fullScreenCover(item: $offen) { b in
            Bildansicht(stand: stand, bild: b) { offen = nil }
        }
    }

    private func kachel(_ b: Bandbild) -> some View {
        let gewaehlt = stand.gewaehlt == b.bild
        // KEIN `Button` UM DIE KACHEL, sondern ein Tipp: Im Streifen der Kachel sitzt der
        // Knopf, der den Vorbehalt aufklappt (`Zeichenrahmen`), und ein Knopf in einem
        // Knopf bekommt in SwiftUI nicht verlässlich seinen eigenen Tipp.
        return VStack(alignment: .leading, spacing: 6) {
            Bildflaeche(grafik: b.grafik, vorhanden: b.vorhanden)
                .frame(width: 160, height: 106)
                .background(Zeichenblatt.kachel)
                .pruefzeichen(b.pruefzeichen(stand.lesart(b)), .klein)
            Text(stand.name(b))
                .font(Schrift.zahl(12))
                .foregroundStyle(gewaehlt ? Zeichenblatt.schrift : Zeichenblatt.leise)
                .lineLimit(1)
                .frame(width: 160, alignment: .leading)
            Rectangle()
                .fill(gewaehlt ? Zeichenblatt.schrift : Color.clear)
                .frame(width: 160, height: 3)
                .accessibilityHidden(true)
        }
        .contentShape(Rectangle())
        .onTapGesture { oeffne(b) }
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(gewaehlt ? [.isButton, .isSelected] : [.isButton])
        .accessibilityHint("Öffnet das Bild gross")
        .accessibilityAction { oeffne(b) }
    }

    private func oeffne(_ b: Bandbild) {
        stand.gewaehlt = b.bild
        offen = b
    }
}
