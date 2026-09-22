import SwiftUI

/// Mit welcher HomeStation die App spricht — oder dass sie mit keiner spricht.
///
/// **Platzhalter.** Die Einheit «Verbindung» ersetzt den Inhalt dieser Datei; der Name
/// `Verbindungszeile` bleibt, weil `Startansicht` ihn benutzt. Die Wege, die sie braucht,
/// stehen in `Kern/Wege.swift`, die Felder in `docs/VISBOX_PROTOKOLL.md`.
struct Verbindungszeile: View {
    var body: some View {
        Platzhalter(titel: "Verbindung",
                    satz: "Nicht verbunden — das Verbinden ist noch nicht gebaut.")
            .frame(height: 72)
    }
}
