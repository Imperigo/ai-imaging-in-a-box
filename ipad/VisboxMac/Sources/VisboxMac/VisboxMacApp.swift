import SwiftUI
import VisboxKern

/// Der Einstieg der Mac-App — **und sonst nichts.**
///
/// Was die App tut, steht in den Ordnern je Strom (`Start/`, `Vermittlung/`, `Vorfuehrung/`,
/// `Assistent/`); was sie entscheidet, im Kern (`VisboxKern`). Hier wird nur das Fenster
/// aufgemacht und die eine Leitung zum Heim-PC angelegt, die alle Ansichten teilen.
///
/// Der Name des Fensters kommt aus der Marke — wie bei der iPad-App steht er an genau einer
/// Stelle (`Kern/Marke.swift`).
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
@main
struct VisboxMacApp: App {
    @StateObject private var leitung = Heimleitung()

    init() {
        // DIE SCHRIFTEN VOR DEM ERSTEN BILDSCHIRM: Registriert wird einmal (`static let`);
        // scheitert es, gilt die Systemschrift, und der Grund steht im Protokoll.
        _ = Macschriften.stand
    }

    var body: some Scene {
        WindowGroup(Marke.name) {
            Hauptfenster(leitung: leitung)
        }
        // Blatt 13 ist 1440 × 900 gezeichnet — die Fläche eines 14-Zoll-Mac.
        .defaultSize(width: 1440, height: 900)
    }
}
