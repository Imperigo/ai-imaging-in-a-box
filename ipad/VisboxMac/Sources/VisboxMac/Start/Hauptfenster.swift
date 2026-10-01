import SwiftUI
import VisboxKern

/// Das eine Fenster: Startzeilen oder Arbeit, und beim ersten Start das Blatt «Einrichten».
///
/// **Ordnet an, entscheidet nichts.** Ob der Mac bei stummem Heim-PC in den Vorführmodus
/// geht (Blatt 13b, Strom C), wird beim Zusammenführen hier eingesetzt — das Signal dafür
/// liefert `Heimleitung.erreichbarkeit` («erreichbar seit / nicht erreichbar seit»).
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Hauptfenster: View {
    @ObservedObject var leitung: Heimleitung

    @State private var arbeitet = false
    @State private var einrichtenOffen = false

    var body: some View {
        Group {
            if arbeitet {
                Arbeitsansicht(leitung: leitung, zurueck: { arbeitet = false })
            } else {
                Startansicht(leitung: leitung,
                             anfangen: { arbeitet = true },
                             einrichten: { einrichtenOffen = true })
            }
        }
        .frame(minWidth: 1100, minHeight: 700)
        .preferredColorScheme(.dark)
        .sheet(isPresented: $einrichtenOffen) {
            Einrichten(leitung: leitung, fertig: { einrichtenOffen = false })
                // OHNE ADRESSE UND KENNWORT GIBT ES NICHTS ZU ZEIGEN: Das Blatt geht erst zu,
                // wenn beides gesichert ist.
                .interactiveDismissDisabled(leitung.braucheEinrichten)
        }
        .onAppear {
            einrichtenOffen = leitung.braucheEinrichten
            leitung.starte()
        }
    }
}
