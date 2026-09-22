import SwiftUI

/// Der Rahmen, in den die Einheiten ihre Teile legen.
///
/// **Diese Datei ordnet nur an.** Jede Einheit hat ihren eigenen Ordner und ihre eigene
/// Datei (`Zeichnen/`, `Leiste/`, `Verbindung/`, `Bilder/`); wer eine Einheit baut,
/// ersetzt dort den Platzhalter und fasst diese Datei nicht an. So stossen zwei Einheiten,
/// die gleichzeitig entstehen, nicht in derselben Zeile zusammen.
struct Startansicht: View {
    var body: some View {
        HStack(spacing: 0) {
            Leiste()
                .frame(width: 88)
            Divider()
            VStack(spacing: 0) {
                Verbindungszeile()
                Divider()
                Zeichenflaeche()
            }
        }
    }
}
