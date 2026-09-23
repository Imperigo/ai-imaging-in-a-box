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
/// **Unter allen Flächen liegt die Unterlage** (seit dem 23.09.2026, `Leinwandstapel.unterlage`):
/// ein Bild, keine Fläche — nicht radiert, nicht gemalt ins PNG, gestreckt wie beim Server.
///
/// **Was geprüft ist, und was nicht (23.09.2026).** Übersetzt hat die Datei auf dem Mac
/// zuletzt mit dem Stand der Welle 2b (f8f2a40, Lauf 5 der Prüfstrecke für 6e267d7:
/// «success», nachgesehen am 23.09.2026; «ohne Warnung» steht im Protokoll des Laufs, hier
/// nicht nachgelesen). **Nicht übersetzt** sind die Änderungen der Durchsicht der Welle 2b
/// (23.09.2026): der Zug im Stand statt im Koordinator (`Zeichenstand.zugBeginnt`), und
/// dass mit der Hand auch der Stift schiebt (`Ebenenstapel.stiftSchiebtNicht(mit:)`).
/// **Am Gerät unbestätigt ist alles** — auch, ob die Flächen deckungsgleich bleiben.
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

    /// **Der Stift schiebt nicht** — nur der Finger (Entscheid Nr. 4).
    ///
    /// Für die gewählte, ausgeblendete Ebene — **ausser mit der Hand** (Kern,
    /// `Ebenenstapel.stiftSchiebtNicht(mit:)`). Befund Durchsicht (22.09.2026): Dort ist das
    /// Zeichnen aus (`drawingGestureRecognizer`), die Fläche nimmt aber Berührungen an — und
    /// ohne Zeichnen fiele der Stift vermutlich dem Schieben der Fläche zu: Wer auf die
    /// ausgeblendete Ebene zeichnen will, verschöbe das Blatt. Darum wird der Stift aus den
    /// Berührungsarten genommen, die Schieben und Zoomen annehmen; alle anderen bleiben, und
    /// beim Zurückschalten gilt wieder, was vorher galt. Übersetzt mit f8f2a40, **am Gerät
    /// unbestätigt** (23.09.2026).
    var stiftSchiebtNicht = false {
        didSet {
            guard stiftSchiebtNicht != oldValue else { return }
            if stiftSchiebtNicht {
                schiebeArten = panGestureRecognizer.allowedTouchTypes
                panGestureRecognizer.allowedTouchTypes =
                    Leinwand.ohneStift(panGestureRecognizer.allowedTouchTypes)
                if let zoom = pinchGestureRecognizer {
                    zoomArten = zoom.allowedTouchTypes
                    zoom.allowedTouchTypes = Leinwand.ohneStift(zoom.allowedTouchTypes)
                }
            } else {
                if let arten = schiebeArten { panGestureRecognizer.allowedTouchTypes = arten }
                if let arten = zoomArten { pinchGestureRecognizer?.allowedTouchTypes = arten }
                schiebeArten = nil
                zoomArten = nil
            }
        }
    }

    /// Was Schieben und Zoomen annahmen, bevor der Stift herausgenommen wurde.
    private var schiebeArten: [NSNumber]?
    private var zoomArten: [NSNumber]?

    private static func ohneStift(_ arten: [NSNumber]) -> [NSNumber] {
        arten.filter { $0.intValue != UITouch.TouchType.pencil.rawValue }
    }
}

/// Der Behälter der Flächen. Er legt sie deckungsgleich und stellt den Zoom so, dass das
/// ganze Blatt (`Ebenenstapel.blattBreite × blattHoehe`) hineinpasst.
///
/// **Zuunterst liegt die Unterlage** (seit dem 23.09.2026): ein Bild unter allen Flächen,
/// **keine** Fläche — der Radierer erreicht es darum nicht, und es nimmt keine Berührung an.
/// Es füllt das Blatt Rand auf Rand und wird bei anderem Seitenverhältnis **gestreckt**
/// (`scaleToFill`), genau so, wie der Server die Skizze auf das Bild abbildet
/// (`arbeitsgang.setze_auf_unterlage`, Kern: `Blattunterlage.gestreckt`) — gezeichnet wird,
/// wo gerechnet wird. Beim Schieben und Zoomen folgt es der gewählten Fläche
/// (`fuehreUnterlageNach`). Übersetzt mit f8f2a40, am Gerät unbestätigt (23.09.2026) —
/// auch, ob es dabei genau deckungsgleich bleibt.
final class Leinwandstapel: UIView {
    /// Von unten nach oben.
    var leinwaende: [Leinwand] = []
    private var letzteGroesse: CGSize = .zero

    /// Das Bild der Unterlage, unter allen Flächen.
    let unterlage: UIImageView = {
        let bild = UIImageView()
        // GESTRECKT, NICHT EINGEPASST: `scaleAspectFit` liesse Ränder, `scaleAspectFill`
        // schnitte ab — beides zeigte das Bild anders, als der Server es unter die Skizze legt.
        bild.contentMode = .scaleToFill
        bild.isUserInteractionEnabled = false
        bild.isHidden = true
        bild.accessibilityElementsHidden = true
        return bild
    }()

    static let blatt = CGSize(width: Ebenenstapel.blattBreite, height: Ebenenstapel.blattHoehe)

    override init(frame: CGRect) {
        super.init(frame: frame)
        // Der Grund des Blattes aus dem Entwurf — im Kern, dort gegen die Abschrift des
        // Blatts im Test geprüft (`FarbtonTests.testJederStifttonStehtSoAufDemBlatt`).
        backgroundColor = UIColor(Color(Stiftfarben.papier))
        clipsToBounds = true
        layer.cornerRadius = 10
        addSubview(unterlage)
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
        fuehreUnterlageNach(nil)
    }

    /// Zeigt die Unterlage — oder keine. Sie bleibt zuunterst, unter jeder Fläche.
    func zeigeUnterlage(_ bild: UIImage?, sichtbar: Bool) {
        if unterlage.image !== bild { unterlage.image = bild }
        unterlage.isHidden = bild == nil || !sichtbar
        sendSubviewToBack(unterlage)
        fuehreUnterlageNach(nil)
    }

    /// Legt die Unterlage dorthin, wo die Flächen das Blatt gerade zeigen: Ursprung minus
    /// Verschiebung, Grösse des Blattes mal Zoom. `quelle` ist die Fläche, die gerade
    /// geschoben oder gezoomt wird; ohne sie die gewählte (die Berührungen annimmt), sonst
    /// die unterste. Ohne Fläche füllt sie den Behälter.
    func fuehreUnterlageNach(_ quelle: UIScrollView?) {
        let gewaehlt: UIScrollView? = leinwaende.first(where: { $0.isUserInteractionEnabled })
            ?? leinwaende.first
        guard let bezug: UIScrollView = quelle ?? gewaehlt else {
            unterlage.frame = bounds
            return
        }
        let zoom = bezug.zoomScale
        unterlage.frame = CGRect(x: bezug.frame.minX - bezug.contentOffset.x,
                                 y: bezug.frame.minY - bezug.contentOffset.y,
                                 width: Leinwandstapel.blatt.width * zoom,
                                 height: Leinwandstapel.blatt.height * zoom)
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
        let nurFingerSchiebt =
            stapel.stiftSchiebtNicht(mit: Zeichenstand.kernwerkzeug(stand.leistenwahl.werkzeug))
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
            // UND DORT SCHIEBT NUR DER FINGER: Das Zeichnen ist aus, der Stift soll das
            // Blatt trotzdem nicht verschieben (Entscheid Nr. 4). Mit der Hand dagegen
            // schiebt auch der Stift — dafür ist sie da. Die Regel steht im Kern
            // (`Ebenenstapel.stiftSchiebtNicht(mit:)`, mit Probe); bis zur Durchsicht der
            // Welle 2b (23.09.2026) nahm diese Zeile dem Stift das Schieben auch mit der
            // Hand. Ob der Stift mit der Hand am Gerät wirklich schiebt: unbestätigt.
            leinwand.stiftSchiebtNicht = aktiv && nurFingerSchiebt
            leinwand.alpha = CGFloat(ebene.deckkraft)
            // NUR DIE GEWAEHLTE NIMMT BERUEHRUNGEN AN. Die anderen lassen sie durch
            // (eine abgeschaltete Ansicht wird beim Treffertest übergangen).
            leinwand.isUserInteractionEnabled = aktiv
            // Auf eine ausgeblendete Ebene wird nicht gezeichnet (Kern:
            // `aktiveIstZeichenbar`), mit der Hand auch nicht. Nur das Zeichnen ist aus;
            // Schieben und Zoomen mit dem Finger gehören der Fläche selbst und bleiben —
            // am Gerät unbestätigt.
            leinwand.drawingGestureRecognizer.isEnabled =
                aktiv && stapel.aktiveIstZeichenbar && !hand
            if aktiv { leinwand.tool = werkzeug }
        }
        ansicht.leinwaende = reihe
        // DIE UNTERLAGE NACH DEN FLAECHEN: `zeigeUnterlage` schiebt sie wieder ganz nach
        // unten, nachdem die Flächen oben ihre Reihenfolge bekommen haben.
        ansicht.zeigeUnterlage(stand.unterlagenbild,
                               sichtbar: stand.stapel.unterlage?.sichtbar == true)
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

    /// Der Stift setzt zu einem Zug an. Bis zu seinem Ende wird das Bild einer Ebene mit
    /// abgedeckten Strichen nicht gelesen (`Zeichenstand.zeichnungGeaendert`) — die
    /// Durchsicht vom 22.09.2026 fand es bei jeder Änderung gelesen. **Wo der Zug steht,
    /// hält der Stand** (`Zeichenstand.zugBeginnt`, Kern `Zugstand`): Nur dort erreichen ihn
    /// die Wege ohne Stift, die einen abgebrochenen Zug schliessen (Durchsicht der Welle
    /// 2b, 23.09.2026).
    func canvasViewDidBeginUsingTool(_ canvasView: PKCanvasView) {
        guard let id = (canvasView as? Leinwand)?.ebene else { return }
        stand.zugBeginnt(id)
    }

    /// Der Zug ist zu Ende: Was darin ausstand, wird jetzt gelesen. Ob diese Meldung vor
    /// oder nach der letzten Änderung kommt, ist nicht belegt — beides führt zum selben
    /// Stand (`Zeichenstand.zugBeendet`). Kommt sie nie (ein abgebrochener Zug), schliesst
    /// der nächste Weg ohne Stift den Zug (`Zeichenstand.zugOhneStift`). Am Gerät
    /// unbestätigt; in dieser Form (Zug im Stand) nicht übersetzt (23.09.2026).
    func canvasViewDidEndUsingTool(_ canvasView: PKCanvasView) {
        guard let leinwand = canvasView as? Leinwand, let id = leinwand.ebene else { return }
        stand.zugBeendet(id, leinwand.drawing)
    }

    func scrollViewDidZoom(_ scrollView: UIScrollView) {
        Leinwandstapel.passeInhaltAn(scrollView)
        fuehreNach(scrollView)
        unterlageFolgt(scrollView)
    }

    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        fuehreNach(scrollView)
        unterlageFolgt(scrollView)
    }

    /// Die Unterlage folgt der Fläche, die der Finger bewegt — nur der gewählten, wie die
    /// anderen Flächen (`fuehreNach`).
    private func unterlageFolgt(_ quelle: UIScrollView) {
        guard quelle.isUserInteractionEnabled,
              let stapel = quelle.superview as? Leinwandstapel else { return }
        stapel.fuehreUnterlageNach(quelle)
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
