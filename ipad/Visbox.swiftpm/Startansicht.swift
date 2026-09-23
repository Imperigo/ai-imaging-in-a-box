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
/// * **Im Vollbild** (Entscheid 29) ist auch die Verbindungszeile weg — nur das Bild und
///   der Knopf zurück (den bringt der Arbeitsplatz mit). **Ausgeblendet, nicht entfernt**
///   (Durchsicht der Verdrahtung, 22.09.2026): Bis dahin nahm ein `if` sie aus dem Baum. Damit
///   ging ihr Zustand verloren (welches Blatt offen ist), und eine laufende Übergabe-Marke
///   verschwand mitten im Flug. Jetzt bleibt sie im Baum, auf Höhe 0, unsichtbar, nicht
///   antippbar und für den Bildschirmleser still (`versteckt`, wie Leiste und Seitenfeld).
/// * **«In die Mappe legen» steht im Seitenfeld** (`Seitentafel`, `Leiste/Mappenknopf.swift`,
///   seit dem 23.09.2026), nicht mehr in der Verbindungszeile. Was er ablegt, folgt der Wahl
///   bei den Varianten (bei «Drei Ebenen» jede sichtbare Ebene als eigene Skizze, sonst
///   eine; `Variantenquelle.ausgabeart`), und die Unterlage geht als `ueber` mit, wenn sie
///   sichtbar ist (`Ablageplan` im Kern).
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
struct Startansicht: View {
    @ObservedObject private var wahl = Leistenwahl.gemeinsam

    var body: some View {
        VStack(spacing: 0) {
            // IM BAUM GEHALTEN, NUR AUSGEBLENDET: Zustand und Flug der Übergabe laufen im
            // Vollbild weiter. Dass die Marke dabei wirklich nie in der Mitte verschwindet,
            // ist am Gerät unbestätigt (22.09.2026) — hier übersetzt SwiftUI nicht.
            VStack(spacing: 0) {
                Verbindungszeile()
                Rectangle()
                    .fill(Zeichenblatt.linie)
                    .frame(height: 1)
                    .accessibilityHidden(true)
            }
            .frame(height: wahl.vollbild ? 0 : nil, alignment: .top)
            .clipped()
            .versteckt(wahl.vollbild)
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
