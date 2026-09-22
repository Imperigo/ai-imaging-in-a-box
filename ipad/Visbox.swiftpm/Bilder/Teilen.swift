import SwiftUI
import UIKit

/// Das Bild, wie es geteilt wird: **mit dem Prüfzeichen darauf** (Entscheid 20).
///
/// Nicht daneben, nicht in einer Bildunterschrift: Was geteilt wird, ist eine Bilddatei, und
/// alles, was nicht in ihren Pixeln steht, fällt beim ersten Weiterreichen ab. *Ein
/// Vorbehalt, der beim ersten Weiterreichen abfällt, ist keiner.*
struct Teilbild: View {
    let grafik: UIImage
    let zeichen: Pruefzeichen
    /// Die Breite in Punkten; das Zeichen wächst mit, damit es auch klein lesbar bleibt.
    let breite: CGFloat

    var body: some View {
        Image(uiImage: grafik)
            .resizable()
            .aspectRatio(contentMode: .fit)
            .frame(width: breite)
            .pruefzeichen(zeichen, .geteilt(breite: breite))
    }
}

/// Malt das Teilbild in eine Bilddatei.
@MainActor
enum Teilbildmaler {
    /// Nie breiter als dies — ein geteiltes Bild soll in eine Nachricht passen.
    static let hoechstbreite: CGFloat = 2048

    static func male(_ grafik: UIImage, _ zeichen: Pruefzeichen) -> UIImage? {
        let pixelbreite = grafik.size.width * grafik.scale
        let breite = min(hoechstbreite, max(1, pixelbreite))
        let maler = ImageRenderer(content: Teilbild(grafik: grafik, zeichen: zeichen,
                                                    breite: breite))
        // EIN PUNKT, EIN PIXEL: Die Breite oben ist in Pixeln des Bildes gerechnet.
        maler.scale = 1
        return maler.uiImage
    }
}

/// Der Knopf «Teilen». Er teilt **nur das Bild mit Zeichen** — nie das nackte Bild.
///
/// Solange das Teilbild nicht gemalt ist, gibt es keinen Knopf, der etwas anderes teilen
/// könnte: Es steht da, warum nicht geteilt werden kann.
struct Teilenknopf: View {
    let grafik: UIImage?
    let zeichen: Pruefzeichen
    let titel: String

    @State private var teilbild: UIImage?

    /// Neu gemalt wird, sobald sich Bild oder Zeichen ändern — ein umgelegter Schalter
    /// Prüfen/Entwerfen ändert, was auf dem geteilten Bild steht.
    private var schluessel: String {
        let bildteil = grafik.map { String(describing: ObjectIdentifier($0)) } ?? "-"
        return bildteil + "|" + zeichen.zeilen.joined(separator: "|")
    }

    var body: some View {
        Group {
            if let fertig = teilbild {
                ShareLink(item: Image(uiImage: fertig),
                          preview: SharePreview(titel, image: Image(uiImage: fertig))) {
                    Label("Teilen", systemImage: "square.and.arrow.up")
                }
                .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                .fixedSize(horizontal: true, vertical: false)
                .accessibilityHint("Teilt das Bild mit seinem Prüfzeichen")
            } else {
                Text(grafik == nil ? "Teilen: das Bild ist nicht geladen" : "Teilen wird vorbereitet …")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }
        }
        .task(id: schluessel) {
            teilbild = nil
            guard let g = grafik else { return }
            teilbild = await Teilbildmaler.male(g, zeichen)
        }
    }
}
