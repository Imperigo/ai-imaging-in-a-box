import AppKit
import SwiftUI
import VisboxKern

/// Das Glas hinter dem Fensterkopf (A0156, E132 A, Runde 2): ein Streifen in der Hoehe des
/// Titelbalkens, ueber die ganze Breite, **ueber** dem Inhalt und **unter** den Werkzeugen und der Ampel (die zeichnet das System in der Titelleiste darueber).
///
/// **Warum nicht `.toolbarBackground(.ultraThinMaterial)`:** Dieses Material mischt nur, was
/// innerhalb des Fensters hinter ihm liegt — und das ist die undurchsichtige Fensterflaeche.
/// Eine `NSVisualEffectView` mit `.behindWindow` mischt, was HINTER dem Fenster liegt (Hintergrund,
/// andere Fenster); der Farbwert des Kopfs aendert sich darum mit dem Hintergrund.
///
/// **Die Ampel bleibt unberuehrt:** Es gibt keinen Zugriff auf ihre Knoepfe und keinen versteckten
/// Titel; das System zeichnet sie weiter. Der Titelbalken wird nur durchsichtig gestellt, damit
/// das Glas zu sehen ist (`Fensterstellung`).
///
/// **Transparenz reduzieren** (`Kopfgrund.deckend`): eine deckende Flaeche statt Glas.
struct Fensterglas: View {
    let grund: Kopfgrund

    /// Wie viel Luft die Fassungsnummer zum naechsten Werkzeug im Kopf hat.
    static let abstandZumNachbarn: CGFloat = 14
    /// Die Hoehe, falls das System keine Oberkante meldet (Titelbalken mit Werkzeugleiste).
    private static let vorgabeHoehe: CGFloat = 52

    var body: some View {
        GeometryReader { feld in
            let oben = feld.safeAreaInsets.top
            streifen
                .frame(height: oben > 0 ? oben : Self.vorgabeHoehe)
        }
        .ignoresSafeArea(edges: .top)
        .background(Fensterstellung())
    }

    @ViewBuilder
    private var streifen: some View {
        switch grund {
        case .glas:
            ZStack {
                Mischung()
                // EIN SANFTER VERLAUF: oben etwas Grund, unten klar — die Unschaerfe bleibt
                // sichtbar, der Rand zur Flaeche darunter wird weich.
                LinearGradient(colors: [Startfarbe.flaeche.opacity(0.30), Startfarbe.flaeche.opacity(0)],
                               startPoint: .top, endPoint: .bottom)
            }
        case .deckend:
            Startfarbe.flaeche
        }
    }
}

/// Die Mischung hinter dem Fenster, vom System (`NSVisualEffectView`).
private struct Mischung: NSViewRepresentable {
    func makeNSView(context: Context) -> NSVisualEffectView {
        let ansicht = NSVisualEffectView()
        ansicht.material = .headerView
        ansicht.blendingMode = .behindWindow
        // IMMER AKTIV: Sonst graut das Glas aus, sobald ein anderes Fenster vorn liegt.
        ansicht.state = .active
        return ansicht
    }

    func updateNSView(_ ansicht: NSVisualEffectView, context: Context) {}
}

/// Stellt den Titelbalken durchsichtig und laesst den Inhalt darunter laufen. **Nur das:**
/// Die Ampel-Knoepfe, der Titel und die Kopplung des Fensters bleiben, wie sie sind.
private struct Fensterstellung: NSViewRepresentable {
    func makeNSView(context: Context) -> Beobachter { Beobachter() }
    func updateNSView(_ ansicht: Beobachter, context: Context) {}

    final class Beobachter: NSView {
        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            guard let fenster = window else { return }
            fenster.styleMask.insert(.fullSizeContentView)
            fenster.titlebarAppearsTransparent = true
            // NICHT DURCHSICHTIG ALS GANZES: Der Fensterhintergrund bleibt deckend; nur die
            // Mischung im Kopf sieht, was hinter dem Fenster liegt.
            fenster.isOpaque = false
            fenster.backgroundColor = .windowBackgroundColor
        }
    }
}
