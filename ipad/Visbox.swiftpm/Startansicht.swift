import SwiftUI

/// Der Rahmen, in den die Einheiten ihre Teile legen — **seit dem 22.09.2026 eine
/// bedienbare App** (Blätter «Main» und «MainHoch»).
///
/// **Diese Datei ordnet nur an.** Oben die Verbindungszeile, darunter der `Arbeitsplatz`
/// mit Leiste, Zeichenfläche und **einem** Seitenfeld (`Seitentafel`: Ebenen oder Mappe,
/// umschaltbar). Was jedes Teil tut, steht in seinem eigenen Ordner.
///
/// * **Nach dem Drehen bleibt die Mitte dieselbe Ansicht.** Kein Zweig nach Haltung hier:
///   Der Arbeitsplatz legt dieselben drei Teile nur anders hin (`Arbeitsplatzanordnung`),
///   und die Zeichenfläche wird immer an derselben Stelle gebaut.
/// * **Die Zeichenfläche ohne eigene Tafel** (`eigeneTafel: false`): Die Ebenentafel steht im
///   Seitenfeld. Sonst stünden zwei Seitenfelder nebeneinander.
/// * **Im Vollbild** (Entscheid 29) fällt auch die Verbindungszeile weg — nur das Bild und
///   der Knopf zurück (den bringt der Arbeitsplatz mit).
/// * **Was «In die Mappe legen» ablegt**, folgt der Wahl bei den Varianten: bei «Drei
///   Ebenen» jede sichtbare Ebene als eigene Skizze, sonst eine (`Variantenquelle.ausgabeart`).
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
struct Startansicht: View {
    @ObservedObject private var wahl = Leistenwahl.gemeinsam

    var body: some View {
        VStack(spacing: 0) {
            if !wahl.vollbild {
                Verbindungszeile(skizzenquelle: {
                    Zeichenstand.gemeinsam.pngAusgabe(
                        Bildbandstand.gemeinsam.variantenquelle.ausgabeart)
                })
                Rectangle()
                    .fill(Zeichenblatt.linie)
                    .frame(height: 1)
                    .accessibilityHidden(true)
            }
            Arbeitsplatz(wahl: wahl) {
                Zeichenflaeche(eigeneTafel: false)
            } seitenfeld: {
                Seitentafel(wahl: wahl)
            }
        }
        .background(Zeichenblatt.grund)
        .foregroundStyle(Zeichenblatt.schrift)
        // DER ENTWURF IST DUNKEL, und die Systemteile (Blätter, Hinweise, Tastatur) sollen
        // es auch sein — sonst stünde ein weisses Blatt über der dunklen Fläche.
        .preferredColorScheme(.dark)
    }
}
