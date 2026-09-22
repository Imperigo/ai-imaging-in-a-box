import Combine
import PencilKit
import SwiftUI
import UIKit

/// Der Stand der Zeichenfläche: die Ebenen, ihre Striche, «Zurück» und die Stiftfarbe —
/// **und die Stelle, an der die Skizze als PNG hinausgeht.**
///
/// Die Regeln (was mitgeht, in welcher Folge, wie viele Ebenen, was der Doppeltipp wählt,
/// wie gezählt wird) stehen im Kern (`Kern/Ebenen.swift`) und sind dort geprüft. Diese
/// Datei hält nur, was PencilKit braucht, und reicht jede Entscheidung an den Kern weiter.
///
/// **Warum ein gemeinsamer Stand (`gemeinsam`).** `Startansicht` ruft `Zeichenflaeche()`
/// ohne Übergabe und wird von keiner Einheit angefasst; wer die Skizze senden will
/// (Mappe, Verbindung), findet sie über `Zeichenstand.gemeinsam`. Dieselbe Bauform wie
/// `Leistenwahl.gemeinsam`, aus demselben Grund.
///
/// **Die Schnittstelle für das Senden:** `pngAusgabe(_:)`.
final class Zeichenstand: ObservableObject {
    static let gemeinsam = Zeichenstand()

    /// Die Ebenen, von unten nach oben (Kern).
    @Published private(set) var stapel = Ebenenstapel()
    /// «Zurück» und «Vor», gezählt — oder als nicht gezählt gesagt (Kern).
    @Published private(set) var schritte = Schrittzaehler()
    /// Was der `UndoManager` selbst sagt. Er hat das letzte Wort darüber, ob es geht.
    @Published private(set) var kannZurueck = false
    @Published private(set) var kannVor = false

    /// Die Stiftfarbe. Frei, und sie bedeutet nichts (Entscheid Nr. 8).
    @Published private(set) var farbe: Color = Stiftfarbe.vorgaben[0].farbe
    /// Welche der vorgegebenen Farben gewählt ist — `nil`, wenn eine eigene.
    @Published private(set) var farbvorgabe: String? = Stiftfarbe.vorgaben[0].name

    /// Was die Leiste gewählt hat (Werkzeug, Strichstärke). Die Leiste schreibt, die
    /// Zeichenfläche liest — und schreibt nur beim Doppeltipp zurück.
    let leistenwahl: Leistenwahl

    /// **Ein** `UndoManager` für alle Ebenen, mit der festen Tiefe aus dem Kern.
    ///
    /// Jede Ebene ist eine eigene PencilKit-Fläche; hätte jede ihren eigenen Verlauf,
    /// nähme «Zurück» nur auf der gewählten Ebene zurück — und der Strich, den man eben
    /// auf einer anderen gezogen hat, bliebe stehen. Darum reichen alle Flächen diesen
    /// einen weiter (`Leinwand.undoManager`).
    let rueckgaengig: UndoManager

    /// Die Striche je Ebene. **Nicht `@Published`**: Sie ändern sich bei jedem Strich, und
    /// die Ansicht braucht davon nur die Anzahl (die steht im Stapel).
    private(set) var zeichnungen: [UUID: PKDrawing] = [:]

    private var werkzeugwahl = Werkzeugwahl()
    private var abos: Set<AnyCancellable> = []

    /// Wie viele Leinwandstapel (`Zeichenleinwand`) gerade stehen. Nicht `@Published`: Die
    /// Ansicht braucht die Zahl nicht, nur das Abräumen (`stapelAbgebaut`).
    private var stehendeStapel = 0

    init(leistenwahl: Leistenwahl = .gemeinsam) {
        self.leistenwahl = leistenwahl
        let verlauf = UndoManager()
        verlauf.levelsOfUndo = Schrittzaehler.tiefe
        rueckgaengig = verlauf
        for ebene in stapel.ebenen { zeichnungen[ebene.id] = PKDrawing() }
        werkzeugwahl.waehle(Zeichenstand.kernwerkzeug(leistenwahl.werkzeug))
        beobachte()
    }

    // ------------------------------------------------------------ Zurück und Vor

    func zurueck() {
        if rueckgaengig.canUndo { rueckgaengig.undo() }
        gleicheAb()
    }

    func vor() {
        if rueckgaengig.canRedo { rueckgaengig.redo() }
        gleicheAb()
    }

    /// Zählt mit, was der `UndoManager` tut.
    ///
    /// **Ungeprüft am Gerät (22.09.2026):** Dass PencilKit je Strich genau eine Gruppe
    /// schliesst, ist nach Kenntnis angenommen, nicht beobachtet. Verpasst das Mitzählen
    /// einen Schritt, zeigt der Zähler «?/20» und nicht still eine falsche Zahl — das
    /// hält der Kern fest (`Schrittzaehler.abgleichen`).
    private func beobachte() {
        let zentrale = NotificationCenter.default
        zentrale.publisher(for: .NSUndoManagerDidCloseUndoGroup, object: rueckgaengig)
            .sink { [weak self] _ in
                guard let self = self else { return }
                // NUR DIE AEUSSERSTE GRUPPE, UND NICHT WAEHREND ZURUECK/VOR: Beim
                // Zurücknehmen schreibt der UndoManager den Vor-Schritt selbst in eine
                // Gruppe; die ist kein neuer Strich.
                let verlauf = self.rueckgaengig
                if verlauf.groupingLevel == 0 && !verlauf.isUndoing && !verlauf.isRedoing {
                    self.schritte.neuerSchritt()
                }
                self.gleicheAb()
            }
            .store(in: &abos)
        zentrale.publisher(for: .NSUndoManagerDidUndoChange, object: rueckgaengig)
            .sink { [weak self] _ in
                self?.schritte.zurueckGegangen()
                self?.gleicheAb()
            }
            .store(in: &abos)
        zentrale.publisher(for: .NSUndoManagerDidRedoChange, object: rueckgaengig)
            .sink { [weak self] _ in
                self?.schritte.vorGegangen()
                self?.gleicheAb()
            }
            .store(in: &abos)
        leistenwahl.$werkzeug
            .sink { [weak self] neu in
                self?.werkzeugwahl.waehle(Zeichenstand.kernwerkzeug(neu))
            }
            .store(in: &abos)
    }

    private func gleicheAb() {
        schritte.abgleichen(kannZurueck: rueckgaengig.canUndo, kannVor: rueckgaengig.canRedo)
        kannZurueck = rueckgaengig.canUndo
        kannVor = rueckgaengig.canRedo
    }

    // ------------------------------------------------- Flächen gebaut und abgebaut

    /// Ein Leinwandstapel ist gebaut worden (`Zeichenleinwand.makeUIView`).
    func stapelAufgebaut() {
        stehendeStapel += 1
    }

    /// Ein Leinwandstapel wird abgebaut (`Zeichenleinwand.dismantleUIView`) — **seine
    /// Schritte gehen mit ihm.**
    ///
    /// Befund Durchsicht A (22.09.2026): Nach einem Neuaufbau der Flächen hielt der
    /// gemeinsame `UndoManager` Schritte der abgebauten; «Zurück» wirkte auf eine Fläche,
    /// die niemand mehr sieht, und der Zähler zählte trotzdem herunter. Die Striche selbst
    /// gehen dabei nicht verloren — sie liegen in `zeichnungen`, und die neuen Flächen
    /// laden sie.
    ///
    /// Entfernt werden zuerst die Schritte, die an einer der abgebauten Flächen hängen.
    /// Ob PencilKit seine Schritte an die Fläche hängt oder an etwas in ihr, ist nicht
    /// belegt; **steht danach kein Stapel mehr, wird darum der ganze Verlauf geleert** —
    /// was er dann noch hielte, könnte nur noch unsichtbar wirken. Steht schon ein neuer
    /// (SwiftUI darf den neuen vor dem Abbau des alten bauen), bleibt dessen Verlauf, und
    /// der Zähler sagt «nicht gezählt», wenn noch etwas geht (Kern:
    /// `Schrittzaehler.flaechenNeu`).
    func stapelAbgebaut(_ flaechen: [UIView]) {
        stehendeStapel = max(0, stehendeStapel - 1)
        for flaeche in flaechen {
            rueckgaengig.removeAllActions(withTarget: flaeche)
        }
        if stehendeStapel == 0 {
            rueckgaengig.removeAllActions()
        }
        // SPAETER VEROEFFENTLICHEN: Der Abbau geschieht mitten im Neuzeichnen der Ansicht,
        // und dort darf ein `@Published` nicht geändert werden.
        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }
            self.schritte.flaechenNeu(kannZurueck: self.rueckgaengig.canUndo,
                                      kannVor: self.rueckgaengig.canRedo)
            self.kannZurueck = self.rueckgaengig.canUndo
            self.kannVor = self.rueckgaengig.canRedo
        }
    }

    // ------------------------------------------------------------------ Ebenen

    func legeEbeneAn() {
        guard let neu = stapel.legeAn() else { return }
        zeichnungen[neu.id] = PKDrawing()
    }

    /// Entfernt eine Ebene **samt dem ganzen Verlauf von «Zurück».**
    ///
    /// Der Verlauf hielte sonst Schritte auf einer Fläche, die es nicht mehr gibt:
    /// «Zurück» täte dann nichts Sichtbares und zählte trotzdem herunter. Die Tafel sagt
    /// das vor dem Löschen.
    func entferneEbene(_ id: UUID) {
        guard stapel.entferne(id) else { return }
        zeichnungen[id] = nil
        rueckgaengig.removeAllActions()
        schritte.geleert()
        gleicheAb()
    }

    func waehleEbene(_ id: UUID) { stapel.waehle(id) }
    func setzeSichtbar(_ id: UUID, _ sichtbar: Bool) { stapel.setzeSichtbar(id, sichtbar) }
    func setzeDeckkraft(_ id: UUID, _ wert: Double) { stapel.setzeDeckkraft(id, wert) }
    @discardableResult
    func benenneEbene(_ id: UUID, _ name: String) -> Bool { stapel.benenne(id, name) }
    func verschiebeEbene(_ id: UUID, nachOben: Bool) { stapel.verschiebe(id, nachOben: nachOben) }

    /// Die Zeichnung einer Ebene, wie sie zuletzt gemeldet wurde.
    func zeichnung(_ id: UUID) -> PKDrawing { zeichnungen[id] ?? PKDrawing() }

    /// Die Fläche meldet jede Änderung ihrer Striche (Zeichnen, Radieren, Zurück).
    func zeichnungGeaendert(_ id: UUID, _ zeichnung: PKDrawing) {
        guard stapel.ebene(id) != nil else { return }
        zeichnungen[id] = zeichnung
        meldeStriche(id, zeichnung)
        kannZurueck = rueckgaengig.canUndo
        kannVor = rueckgaengig.canRedo
        // DER ZAEHLER WIRD HIER NICHT SOFORT ABGEGLICHEN. Diese Meldung kann vor dem
        // Schliessen der Gruppe kommen, in der PencilKit den Strich verbucht; ein Abgleich
        // jetzt fände «Zurück geht, gezählt ist 0» und machte aus einem richtig gezählten
        // Strich ein «?». Abgeglichen wird später — und kam die Meldung über das Schliessen
        // nie, zeigt der Zähler dann «?» statt einer falschen 0. Die halbe Sekunde ist
        // gesetzt, nicht gemessen (22.09.2026).
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            self?.gleicheAb()
        }
    }

    /// Meldet dem Kern, ob auf der Ebene etwas zu sehen ist.
    ///
    /// **Die Strichzahl allein reicht nicht** (Befund Durchsicht A, 22.09.2026): Der
    /// flächige Radierer (`PKEraserTool(.bitmap)`) deckt Striche ab, statt sie zu
    /// entfernen; ganz weggewischt kann eine Ebene Striche tragen, von denen nichts zu sehen
    /// ist. Sobald ein Strich eine Abdeckung trägt (`PKStroke.mask`), entscheidet darum das
    /// gemalte Bild (`deckung`, Regel im Kern: `setzeStriche(_:_:alpha:)`). Ohne Abdeckung
    /// ist jeder Strich zu sehen, und die Zahl gilt — so bleibt das Malen beim gewöhnlichen
    /// Zeichnen aus dem Spiel.
    ///
    /// Liess sich das Bild nicht malen (`deckung` gibt `nil`), gilt die Strichzahl. Das ist
    /// ein Rückfall, der im schlimmsten Fall ein leeres Bild hinauslässt; ob `deckung` am
    /// Gerät je `nil` gibt, ist ungeprüft.
    private func meldeStriche(_ id: UUID, _ zeichnung: PKDrawing) {
        let anzahl = zeichnung.strokes.count
        var neu = stapel
        if zeichnung.strokes.contains(where: { $0.mask != nil }),
           let alpha = Zeichenstand.deckung(zeichnung) {
            neu.setzeStriche(id, anzahl, alpha: alpha)
        } else {
            neu.setzeStriche(id, anzahl)
        }
        // Nur schreiben, was sich ändert: Jeder Schreibzugriff auf den Stapel zeichnet
        // die Tafel neu.
        if neu != stapel { stapel = neu }
    }

    /// Die Deckung einer Zeichnung, ein Byte je Bildpunkt, in der Grösse der Ausgabe
    /// (`Ebenenstapel.blattBreite × blattHoehe`, Massstab 1) — oder `nil`, wenn sie sich
    /// nicht malen liess. Ungeprüft am Gerät.
    static func deckung(_ zeichnung: PKDrawing) -> Data? {
        let breite = Ebenenstapel.blattBreite
        let hoehe = Ebenenstapel.blattHoehe
        let rahmen = CGRect(x: 0, y: 0, width: breite, height: hoehe)
        guard let bild = zeichnung.image(from: rahmen, scale: 1).cgImage else { return nil }
        var alpha = Data(count: breite * hoehe)
        let gemalt: Bool = alpha.withUnsafeMutableBytes { roh -> Bool in
            guard let ziel = CGContext(data: roh.baseAddress, width: breite, height: hoehe,
                                       bitsPerComponent: 8, bytesPerRow: breite,
                                       space: CGColorSpaceCreateDeviceGray(),
                                       bitmapInfo: CGImageAlphaInfo.alphaOnly.rawValue) else {
                return false
            }
            ziel.draw(bild, in: rahmen)
            return true
        }
        return gemalt ? alpha : nil
    }

    // ------------------------------------------------------------ Werkzeug und Farbe

    /// Doppeltipp am Pencil 2: Stift ⇄ Radierer (Entscheid Nr. 2). Die Regel steht im
    /// Kern (`Werkzeugwahl.doppeltipp`); hier wird sie nur in die Leiste zurückgeschrieben,
    /// damit die Leiste zeigt, was in der Hand ist.
    func doppeltipp() {
        var wahl = werkzeugwahl
        wahl.doppeltipp()
        leistenwahl.werkzeug = Zeichenstand.leistenwerkzeug(wahl.werkzeug)
    }

    func waehleFarbe(_ vorgabe: Stiftfarbe) {
        farbe = vorgabe.farbe
        farbvorgabe = vorgabe.name
    }

    func waehleEigeneFarbe(_ neu: Color) {
        farbe = neu
        farbvorgabe = nil
    }

    /// Das PencilKit-Werkzeug zu dem, was die Leiste zeigt.
    ///
    /// Der Stift ist `.pen`: Seine Breite folgt dem Druck (Entscheid Nr. 3); die Wahl in
    /// der Leiste setzt die Grundbreite. Die Hand hat kein eigenes Werkzeug — mit ihr ist
    /// das Zeichnen abgeschaltet (`Zeichenleinwand`), und das Werkzeug bleibt der Stift.
    func pencilWerkzeug() -> PKTool {
        switch leistenwahl.werkzeug {
        case .strichradierer:
            return PKEraserTool(.vector)
        case .flaechenradierer:
            return PKEraserTool(.bitmap)
        case .stift, .hand:
            return PKInkingTool(.pen, color: UIColor(farbe),
                                width: Zeichenstand.grundbreite(leistenwahl.strich))
        }
    }

    /// Grundbreiten in Punkten des Blattes. **Gesetzt, nicht gemessen (22.09.2026)** —
    /// ob «dick» am Gerät dick genug aussieht, zeigt erst das Gerät.
    static func grundbreite(_ strich: Leistenstrich) -> CGFloat {
        switch strich {
        case .duenn: return 2
        case .mittel: return 5
        case .dick: return 10
        }
    }

    static func kernwerkzeug(_ w: Leistenwerkzeug) -> Zeichenwerkzeug {
        switch w {
        case .stift: return .stift
        case .strichradierer: return .radiererStriche
        case .flaechenradierer: return .radiererFlaeche
        case .hand: return .hand
        }
    }

    static func leistenwerkzeug(_ w: Zeichenwerkzeug) -> Leistenwerkzeug {
        switch w {
        case .stift: return .stift
        case .radiererStriche: return .strichradierer
        case .radiererFlaeche: return .flaechenradierer
        case .hand: return .hand
        }
    }

    // ------------------------------------------------------------------ Ausgabe

    /// **DIE SCHNITTSTELLE FÜR DAS SENDEN.** Die sichtbaren Ebenen als PNG.
    ///
    /// * `.eineSkizze`: **ein** Bild aus allen sichtbaren, bezeichneten Ebenen,
    ///   übereinander in Stapelfolge, jede mit ihrer Deckkraft.
    /// * `.ebenenAlsVarianten`: ein Bild **je** sichtbarer, bezeichneter Ebene
    ///   (Entscheid Nr. 32), höchstens drei.
    ///
    /// Eine ausgeblendete Ebene geht nie mit. Ist nichts Sichtbares gezeichnet (auch: alles
    /// flächig weggewischt, `meldeStriche`), kommt `.nichtsGezeichnet` und **kein leeres
    /// Bild.**
    ///
    /// **Was das PNG ist, und was nicht (22.09.2026).** Jedes Bild ist
    /// `Ebenenstapel.blattBreite × blattHoehe` = 1536 × 1024 Bildpunkte, mit
    /// **durchsichtigem Grund**; die Deckkraft einer Ebene steckt **nur im Alphakanal.** Es
    /// ist darum *nicht* das Bild, das auf dem Schirm steht: Dort liegt die Skizze auf dem
    /// dunklen Blatt oder auf einem Bild aus einem Lauf. Das Zusammensetzen auf die
    /// Unterlage macht der Server (der weiss über `ueber`, was darunter liegt; es in das PNG
    /// zu malen hiesse, es zweimal zu schicken). Heute liest der Server den Alphakanal nicht
    /// (`bildlesen.lies_png_luminanz` übergeht ihn) — bis er zusammensetzt, sieht er weder
    /// Deckkraft noch durchsichtigen Grund.
    ///
    /// **Nicht geprüft wird hier die Grösse**: Der Server nimmt höchstens 2 MiB je Skizze
    /// (`docs/VISBOX_PROTOKOLL.md`). Das prüft, wer sendet.
    func pngAusgabe(_ art: Ebenenstapel.Ausgabeart) -> Ebenenausgabe {
        Ebenenausgabe.aus(stapel.plan(art)) { teil in self.male(teil) }
    }

    /// Ein Teil als PNG — oder `nil`, wenn eine seiner Ebenen keine Zeichnung hat.
    private func male(_ teil: Ebenenstapel.Teil) -> Data? {
        // EINE EBENE MIT STRICHEN UND OHNE ZEICHNUNG gibt es nicht; gäbe es sie doch, ginge
        // sonst ein Bild hinaus, dem eine sichtbare Ebene fehlt. Die Deckkraft geht als
        // Alpha in das Bild (siehe `pngAusgabe`), nicht als Mischung mit einem Grund.
        var lagen: [(PKDrawing, CGFloat)] = []
        for ebene in teil.ebenen {
            guard let zeichnung = zeichnungen[ebene.id] else { return nil }
            lagen.append((zeichnung, CGFloat(ebene.deckkraft)))
        }
        let groesse = CGSize(width: Ebenenstapel.blattBreite, height: Ebenenstapel.blattHoehe)
        let rahmen = CGRect(origin: .zero, size: groesse)
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = false
        let maler = UIGraphicsImageRenderer(size: groesse, format: format)
        var png: Data?
        // IM HELLEN ERSCHEINUNGSBILD MALEN, wie die Flächen es zeigen
        // (`overrideUserInterfaceStyle = .light` in `Zeichenleinwand`). PencilKit passt
        // Farben sonst dem dunklen Bild an — dann ginge eine andere Farbe hinaus, als der
        // Stift gezeigt hat. Ungeprüft am Gerät.
        UITraitCollection(userInterfaceStyle: .light).performAsCurrent {
            png = maler.pngData { _ in
                for (zeichnung, deckkraft) in lagen {
                    zeichnung.image(from: rahmen, scale: 1)
                        .draw(in: rahmen, blendMode: .normal, alpha: deckkraft)
                }
            }
        }
        return png
    }
}

/// Eine vorgegebene Stiftfarbe. Die Farben sind die des Entwurfs (Blatt «Main», Feld
/// «Stift»); sie **bedeuten nichts** (Entscheid Nr. 8) und sind nur schneller erreicht
/// als die freie Wahl daneben.
struct Stiftfarbe: Identifiable {
    let name: String
    let farbe: Color

    var id: String { name }

    static let vorgaben: [Stiftfarbe] = [
        Stiftfarbe(name: "Orange", farbe: ton(0xe0, 0x8b, 0x52)),
        Stiftfarbe(name: "Hell", farbe: ton(0xe6, 0xe8, 0xec)),
        Stiftfarbe(name: "Blau", farbe: ton(0x6f, 0xb3, 0xd2)),
        Stiftfarbe(name: "Grün", farbe: ton(0x8f, 0xd4, 0xac)),
    ]

    private static func ton(_ r: Double, _ g: Double, _ b: Double) -> Color {
        Color(.sRGB, red: r / 255, green: g / 255, blue: b / 255, opacity: 1)
    }
}
