import SwiftUI
import VisboxKern

/// Der Einstieg der Mac-App — **und sonst nichts.**
///
/// Was die App tut, steht in den Ordnern je Strom (`Start/`, `Vermittlung/`, `Assistent/`,
/// `Aktualisieren/`, `Claude/`; `Vorfuehrung/` ist seit Entscheid 103b weg); was sie entscheidet, im Kern (`VisboxKern`). Hier wird nur das Fenster
/// aufgemacht und die eine Leitung zum Heim-PC angelegt, die alle Ansichten teilen.
///
/// Der Name des Fensters kommt aus der Marke — wie bei der iPad-App steht er an genau einer
/// Stelle (`Kern/Marke.swift`).
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
@main
struct VisboxMacApp: App {
    @StateObject private var leitung = Heimleitung()
    // EINER FUER DIE GANZE APP, nicht je Fenster (Entscheid 84, 13.10.2026): Zwei Fenster
    // fragten sonst zweimal und koennten zweimal ersetzen.
    @StateObject private var aktualisierung = Fassungswaechter()

    init() {
        // CLAUDE DESKTOP STARTET DIE APP MIT `--mcp-stdio` (Plan KI-Bedienung, Stufe 2): Dann
        // laeuft nur der Weg ueber stdio, ohne Fenster, und die App endet danach — VOR dem
        // Einzelstart, der sonst die laufende Visbox nach vorn holte und diesen Start beendete.
        Claudestdio.pruefe()
        // EIN VISBOX-FENSTER (Owner-Befund 20.10.2026): Laeuft schon eine, kommt sie nach vorn,
        // und dieser Start endet — bevor ein Fenster entsteht. Nach «Neu starten» umgekehrt.
        Einzelstart.pruefe()
        // DIE SCHRIFTEN VOR DEM ERSTEN BILDSCHIRM: Registriert wird einmal (`static let`);
        // scheitert es, gilt die Systemschrift, und der Grund steht im Protokoll.
        _ = Macschriften.stand
        // CLAUDE UEBER MCP, AB WERK AN (Entscheid 108 B): nur auf 127.0.0.1:8631, abschaltbar
        // mit der Einstellung `claudeMcp.an`.
        Claudeanschluss.gemeinsam.starteWennAn()
    }

    var body: some Scene {
        // EIN FENSTER, NICHT EINE GRUPPE (14.10.2026): Mit `WindowGroup` machte jedes erneute
        // Oeffnen der laufenden App ein zweites Fenster auf — so stand nach «Neu starten» ein
        // neues Fenster vor dem alten. `Window` holt das eine nach vorn.
        Window(Marke.name, id: "haupt") {
            Hauptfenster(leitung: leitung, aktualisierung: aktualisierung)
        }
        // Blatt 13 ist 1440 × 900 gezeichnet — die Fläche eines 14-Zoll-Mac.
        .defaultSize(width: 1440, height: 900)
        .commands {
            // ENTSCHEID 94 (14.10.2026): Die Knoten sind DIE Arbeitsflaeche zum Rendern; die
            // Visbox-Seite (Mappe, Skizzen vom iPad, Laeufe) ist ein Nebenweg im Menue.
            CommandGroup(after: .toolbar) {
                Button(Flaechenwahl.seite.titel + " öffnen") {
                    NotificationCenter.default.post(name: .seiteOeffnen, object: nil)
                }
            }
        }
    }
}
