import SwiftUI

/// Die Bilder, die der Server zu einem Projekt liefert — je mit ihrem Urteil.
///
/// **Platzhalter, und noch nirgends eingehängt.** Die Einheit «Bilder» füllt diese Datei
/// und entscheidet, wo das Band erscheint. Das Urteil je Bild ist `Urteil` aus
/// `Kern/Urteil.swift` — drei Fälle, und «nicht gemessen» hat ein eigenes Zeichen.
struct Bildband: View {
    var body: some View {
        Platzhalter(titel: "Bilder", satz: "Noch nicht gebaut.")
    }
}
