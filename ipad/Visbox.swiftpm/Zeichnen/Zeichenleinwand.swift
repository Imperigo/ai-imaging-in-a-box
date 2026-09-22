import PencilKit
import SwiftUI
import UIKit

/// Die Flächen, auf die gezeichnet wird — **eine PencilKit-Fläche je Ebene, übereinander.**
///
/// Nur der Stift zeichnet, der Finger schiebt und zoomt (Entscheid Nr. 4:
/// `drawingPolicy = .pencilOnly`). Der Druck steuert die Breite (Nr. 3; das tut der
/// Stifttyp `.pen` selbst). Der Doppeltipp am Pencil 2 schaltet Werkzeug ⇄ Radierer
/// (Nr. 2, `UIPencilInteraction`).
///
/// **Warum mehrere Flächen und nicht eine.** Eine PencilKit-Fläche kennt keine Ebenen.
/// Jede Ebene bekommt darum ihre eigene; nur die gewählte nimmt Berührungen an, die
/// anderen liegen darüber oder darunter und folgen ihr beim Schieben und Zoomen. Was das
/// kostet: Speicher je Ebene — darum die Höchstzahl im Kern.
///
/// **Beim Abbau gehen die Schritte mit** (`dismantleUIView`, `Zeichenstand.stapelAbgebaut`):
/// Baut SwiftUI die Flächen neu, hielte der gemeinsame `UndoManager` sonst Schritte auf
/// Flächen, die niemand mehr sieht (Befund Durchsicht A, 22.09.2026).
///
/// **Ungeprüft (22.09.2026):** Die ganze Datei ist nie einem Übersetzer vorgelegt worden,
/// und ob die Flächen am Gerät deckungsgleich bleiben, zeigt erst das Gerät.
struct Zeichenleinwand: UIViewRepresentable {
    @ObservedObject var stand: Zeichenstand
    @ObservedObject var wahl: Leistenwahl

    func makeCoordinator() -> Leinwandkoordinator {
        Leinwandkoordinator(stand: stand)
    }

    func makeUIView(context: Context) -> Leinwandstapel {
        let ansicht = Leinwandstapel()
        let stift = UIPencilInteraction()
        stift.delegate = context.coordinator
        ansicht.addInteraction(stift)
        stand.stapelAufgebaut()
        context.coordinator.gleicheAb(ansicht)
        return ansicht
    }

    func updateUIView(_ ansicht: Leinwandstapel, context: Context) {
        context.coordinator.stand = stand
        context.coordinator.gleicheAb(ansicht)
    }

    static func dismantleUIView(_ ansicht: Leinwandstapel, coordinator: Leinwandkoordinator) {
        coordinator.raeumeAb()
    }
}

/// Eine PencilKit-Fläche, die den **gemeinsamen** `UndoManager` weiterreicht.
///
/// Ohne diese Überschreibung nähme PencilKit den des Fensters — dessen Tiefe diese App
/// nicht setzt, und den sich alle Ebenen ohnehin teilten, ohne dass es irgendwo stünde.
final class Leinwand: PKCanvasView {
    var ebene: UUID?
    var gemeinsamerVerlauf: UndoManager?

    override var undoManager: UndoManager? { gemeinsamerVerlauf }

    /// Der Inhalt ist verdeckt, die Fläche nimmt aber weiter Berührungen an.
    ///
    /// Für die **gewählte, ausgeblendete** Ebene. Befund Durchsicht A (22.09.2026): War sie
    /// mit `isHidden` versteckt, nahm keine Fläche mehr Berührungen an — der Finger schob
    /// und zoomte gar nicht, gegen Entscheid Nr. 4. Eine versteckte Ansicht und eine mit
    /// Deckkraft unter 0.01 übergeht UIKit beim Treffertest; eine **leere Maske** verdeckt
    /// alles, ohne dass der Treffertest sie beachtet. Am Gerät unbestätigt.
    var inhaltVerdeckt = false {
        didSet {
            guard inhaltVerdeckt != oldValue else { return }
            mask = inhaltVerdeckt ? UIView(frame: .zero) : nil
        }
    }
}

/// Der Behälter der Flächen. Er legt sie deckungsgleich und stellt den Zoom so, dass das
/// ganze Blatt (`Ebenenstapel.blattBreite × blattHoehe`) hineinpasst.
final class Leinwandstapel: UIView {
    /// Von unten nach oben.
    var leinwaende: [Leinwand] = []
    private var letzteGroesse: CGSize = .zero

    static let blatt = CGSize(width: Ebenenstapel.blattBreite, height: Ebenenstapel.blattHoehe)

    override init(frame: CGRect) {
        super.init(frame: frame)
        // Der Grund des Blattes aus dem Entwurf (Blatt «Main»: #191d23).
        backgroundColor = UIColor(red: 0x19 / 255.0, green: 0x1d / 255.0,
                                  blue: 0x23 / 255.0, alpha: 1)
        clipsToBounds = true
        layer.cornerRadius = 10
    }

    required init?(coder: NSCoder) {
        fatalError("Leinwandstapel wird nur im Code angelegt")
    }

    /// Der Zoom, bei dem das Blatt genau die Ansicht füllt.
    var passenderZoom: CGFloat {
        guard bounds.width > 0, bounds.height > 0 else { return 1 }
        return min(bounds.width / Leinwandstapel.blatt.width,
                   bounds.height / Leinwandstapel.blatt.height)
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        guard bounds.width > 0, bounds.height > 0 else { return }
        let passend = passenderZoom
        // BEIM DREHEN WIRD DER ZOOM ZURUECKGESETZT, auf das ganze Blatt. Einen Ausschnitt
        // über eine Drehung zu retten hiesse zu raten, welcher gemeint war.
        let neueGroesse = bounds.size != letzteGroesse
        letzteGroesse = bounds.size
        let vorbild = leinwaende.first { $0.frame == bounds && !neueGroesse }
        for leinwand in leinwaende {
            let war = leinwand.frame
            leinwand.frame = bounds
            leinwand.minimumZoomScale = passend
            leinwand.maximumZoomScale = passend * 6
            if neueGroesse {
                leinwand.zoomScale = passend
                leinwand.contentOffset = .zero
            } else if war != bounds {
                // Eine neue Ebene übernimmt Zoom und Ausschnitt der anderen.
                leinwand.zoomScale = vorbild?.zoomScale ?? passend
                leinwand.contentOffset = vorbild?.contentOffset ?? .zero
            }
            Leinwandstapel.passeInhaltAn(leinwand)
        }
    }

    /// Das Blatt in der Grösse des Zooms — so rechnet PencilKit mit festen
    /// Blattkoordinaten, gleich wie weit hineingezoomt ist.
    static func passeInhaltAn(_ leinwand: UIScrollView) {
        leinwand.contentSize = CGSize(width: blatt.width * leinwand.zoomScale,
                                      height: blatt.height * leinwand.zoomScale)
    }
}

/// Hält die Flächen mit dem Stand in Deckung und nimmt ihre Meldungen entgegen.
final class Leinwandkoordinator: NSObject, PKCanvasViewDelegate, UIPencilInteractionDelegate {
    var stand: Zeichenstand
    private var leinwaende: [UUID: Leinwand] = [:]
    /// Verhindert, dass das Nachführen der anderen Flächen wieder ein Nachführen auslöst.
    private var fuehrtNach = false

    init(stand: Zeichenstand) {
        self.stand = stand
    }

    /// Bringt die Flächen auf den Stand: neue anlegen, entfernte wegnehmen, Reihenfolge,
    /// Sichtbarkeit, Deckkraft, Werkzeug.
    func gleicheAb(_ ansicht: Leinwandstapel) {
        let stapel = stand.stapel
        let vorhanden = Set(stapel.ebenen.map { $0.id })

        for (id, leinwand) in leinwaende where !vorhanden.contains(id) {
            leinwand.delegate = nil
            leinwand.removeFromSuperview()
            leinwaende[id] = nil
        }

        for ebene in stapel.ebenen where leinwaende[ebene.id] == nil {
            let leinwand = Leinwand()
            leinwand.ebene = ebene.id
            leinwand.gemeinsamerVerlauf = stand.rueckgaengig
            leinwand.drawingPolicy = .pencilOnly
            leinwand.backgroundColor = .clear
            leinwand.isOpaque = false
            // HELL, AUCH IM DUNKLEN BILD: PencilKit passt Farben sonst dem Erscheinungsbild
            // an, und der Strich sähe anders aus als die Farbe, die gewählt ist — und als
            // das PNG, das hinausgeht (`Zeichenstand.male`).
            leinwand.overrideUserInterfaceStyle = .light
            leinwand.showsHorizontalScrollIndicator = false
            leinwand.showsVerticalScrollIndicator = false
            leinwand.drawing = stand.zeichnung(ebene.id)
            leinwand.delegate = self
            leinwaende[ebene.id] = leinwand
            ansicht.addSubview(leinwand)
        }

        let werkzeug = stand.pencilWerkzeug()
        let hand = stand.leistenwahl.werkzeug == .hand
        var reihe: [Leinwand] = []
        for ebene in stapel.ebenen {
            guard let leinwand = leinwaende[ebene.id] else { continue }
            ansicht.bringSubviewToFront(leinwand)
            reihe.append(leinwand)
            let aktiv = ebene.id == stapel.aktiv
            // DIE GEWAEHLTE BLEIBT DA, AUCH AUSGEBLENDET: Sie ist die Fläche, die der Finger
            // schiebt und zoomt (Entscheid Nr. 4). Ausgeblendet wird sie verdeckt, nicht
            // versteckt (`Leinwand.inhaltVerdeckt`); die anderen folgen ihr (`fuehreNach`).
            leinwand.isHidden = !ebene.sichtbar && !aktiv
            leinwand.inhaltVerdeckt = !ebene.sichtbar && aktiv
            leinwand.alpha = CGFloat(ebene.deckkraft)
            // NUR DIE GEWAEHLTE NIMMT BERUEHRUNGEN AN. Die anderen lassen sie durch
            // (eine abgeschaltete Ansicht wird beim Treffertest übergangen).
            leinwand.isUserInteractionEnabled = aktiv
            // Auf eine ausgeblendete Ebene wird nicht gezeichnet (Kern:
            // `aktiveIstZeichenbar`), mit der Hand auch nicht. Nur das Zeichnen ist aus;
            // Schieben und Zoomen gehören der Fläche selbst und bleiben.
            leinwand.drawingGestureRecognizer.isEnabled =
                aktiv && stapel.aktiveIstZeichenbar && !hand
            if aktiv { leinwand.tool = werkzeug }
        }
        ansicht.leinwaende = reihe
        ansicht.setNeedsLayout()
    }

    /// Der Stapel wird abgebaut: Die Flächen melden nichts mehr, und ihre Schritte gehen
    /// mit ihnen (`Zeichenstand.stapelAbgebaut`).
    func raeumeAb() {
        let weg = Array(leinwaende.values)
        for leinwand in weg {
            leinwand.delegate = nil
        }
        leinwaende = [:]
        stand.stapelAbgebaut(weg)
    }

    // ------------------------------------------------------------ PencilKit meldet

    func canvasViewDrawingDidChange(_ canvasView: PKCanvasView) {
        guard let leinwand = canvasView as? Leinwand, let id = leinwand.ebene else { return }
        stand.zeichnungGeaendert(id, leinwand.drawing)
    }

    func scrollViewDidZoom(_ scrollView: UIScrollView) {
        Leinwandstapel.passeInhaltAn(scrollView)
        fuehreNach(scrollView)
    }

    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        fuehreNach(scrollView)
    }

    /// Die anderen Flächen folgen der gewählten — sonst stünde eine Ebene beim Zoomen
    /// verschoben über der anderen, und was übereinander gezeichnet wurde, sähe nicht
    /// mehr übereinander aus.
    private func fuehreNach(_ quelle: UIScrollView) {
        guard !fuehrtNach, quelle.isUserInteractionEnabled else { return }
        fuehrtNach = true
        for leinwand in leinwaende.values where leinwand !== quelle {
            leinwand.zoomScale = quelle.zoomScale
            Leinwandstapel.passeInhaltAn(leinwand)
            leinwand.contentOffset = quelle.contentOffset
        }
        fuehrtNach = false
    }

    // ------------------------------------------------------------ der Doppeltipp

    /// Wann zuletzt ein Doppeltipp umgeschaltet hat (Sekunden seit Gerätestart).
    private var letzterDoppeltipp: TimeInterval = -1

    /// Doppeltipp am Pencil 2 (Entscheid Nr. 2) — **iOS 17.0 bis 17.4.**
    ///
    /// **Wer den Doppeltipp in den Einstellungen des iPads abgeschaltet hat, bekommt ihn
    /// auch hier nicht** (`preferredTapAction == .ignore`). Jede andere Einstellung
    /// führt zum Radierer, wie entschieden.
    func pencilInteractionDidTap(_ interaction: UIPencilInteraction) {
        doppeltipp()
    }

    /// Doppeltipp am Pencil 2 — **ab iOS 17.5**, wo die Meldung so heisst. Dieselbe Wirkung
    /// wie oben.
    @available(iOS 17.5, *)
    func pencilInteraction(_ interaction: UIPencilInteraction,
                           didReceiveTap tap: UIPencilInteraction.Tap) {
        doppeltipp()
    }

    /// **Ein Doppeltipp schaltet einmal**, auch wenn beide Meldungen ankämen. Ob iOS ab
    /// 17.5 die alte Meldung weiter schickt, wenn die neue umgesetzt ist, ist nicht belegt
    /// (22.09.2026); kämen beide, schaltete der Stift zum Radierer und sofort zurück —
    /// sichtbar nichts. Was innert 0.3 s nach einem Umschalten ankommt, gilt darum als
    /// dieselbe Berührung. Die Frist ist gesetzt, nicht gemessen: Zwei echte Doppeltipps
    /// liegen nach Kenntnis weiter auseinander. Am Gerät ungeprüft.
    private func doppeltipp() {
        guard UIPencilInteraction.preferredTapAction != .ignore else { return }
        let jetzt = ProcessInfo.processInfo.systemUptime
        guard letzterDoppeltipp < 0 || jetzt - letzterDoppeltipp > 0.3 else { return }
        letzterDoppeltipp = jetzt
        stand.doppeltipp()
    }
}
