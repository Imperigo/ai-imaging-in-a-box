import SwiftUI

/// Die Bilder, die der Server zu einem Projekt liefert — **je mit ihrem Prüfzeichen.**
///
/// Jedes Bild trägt ein Zeichen, auch das ungeprüfte: *Kein Zeichen sähe aus wie kein
/// Problem.* Die Wahl wird **nicht** mit einem grünen Rand gezeigt, wie im Entwurf (Blatt
/// «Main»), sondern mit einem Balken darunter — grün heisst am Bild «bestanden», und ein
/// gewähltes Bild ist nicht bestanden, nur weil es gewählt ist.
///
/// Ein Tipp öffnet das Bild gross (`Bildansicht`), mit dem Schalter Prüfen/Entwerfen, dem
/// Vergleich und dem Teilen.
///
/// **Noch nirgends eingehängt**: `Startansicht` ordnet fest an. Die Bilder legt die Einheit
/// «Verbindung» in `Bildbandstand.gemeinsam`; bis dahin sagt das Band, dass es leer ist.
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
        return Button {
            stand.gewaehlt = b.bild
            offen = b
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Bildflaeche(grafik: b.grafik, vorhanden: b.vorhanden)
                    .frame(width: 160, height: 106)
                    .background(Color(Farbton(hex: "14181b")))
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
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(gewaehlt ? .isSelected : [])
        .accessibilityHint("Öffnet das Bild gross")
    }
}
