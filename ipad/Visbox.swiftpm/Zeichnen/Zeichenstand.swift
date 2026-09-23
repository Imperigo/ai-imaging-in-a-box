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
/// **Warum ein gemeinsamer Stand (`gemeinsam`).** Drei Stellen müssen dieselben Ebenen
/// sehen, und keine baut die andere: `Startansicht` setzt `Zeichenflaeche(eigeneTafel:
/// false)` ohne Stand ein, `Seitentafel` legt `Ebenentafel(stand: Zeichenstand.gemeinsam)`
/// ins Seitenfeld, und der `Mappenknopf` im Seitenfeld nimmt
/// `Zeichenstand.gemeinsam.skizzenpaket(_:)` als Quelle der Skizze. Dieselbe Bauform wie
/// `Leistenwahl.gemeinsam`, aus demselben Grund (Stand 23.09.2026).
///
/// **Die Schnittstelle für das Senden:** `skizzenpaket(_:)` — die PNG aus `pngAusgabe(_:)`
/// und die Unterlage des Blattes (seit dem 23.09.2026).
final class Zeichenstand: ObservableObject {
    static let gemeinsam = Zeichenstand()

    /// Die Ebenen, von unten nach oben (Kern).
    @Published private(set) var stapel = Ebenenstapel()
    /// «Zurück» und «Vor», gezählt — oder als nicht gezählt gesagt (Kern).
    @Published private(set) var schritte = Schrittzaehler()
    /// Was der `UndoManager` selbst sagt. Er hat das letzte Wort darüber, ob es geht.
    @Published private(set) var kannZurueck = false
    @Published private(set) var kannVor = false

    /// **Das Bild der Unterlage**, wie es unter den Ebenen liegt — `nil`, wenn keine liegt.
    /// Was die Regeln brauchen (Name, Mappe, Grösse, ein- oder ausgeblendet), steht im Kern
    /// an `stapel.unterlage`; hier nur die Grafik, die UIKit zeigt (`Leinwandstapel`).
    /// Gesetzt und weggenommen **nur zusammen mit** `stapel.unterlage`
    /// (`legeUnterlage(_:bild:)`, `entferneUnterlage()`).
    @Published private(set) var unterlagenbild: UIImage?

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

    /// Ebenen mit abgedeckten Strichen, deren Bild noch nicht gelesen ist — weil die
    /// Änderung mitten in einem Zug kam (`zeichnungGeaendert(_:_:imZug:)`). Gelesen wird am
    /// Ende des Zugs (`zugBeendet`), spätestens vor dem Senden (`pngAusgabe`).
    private var deckungAusstehend: Set<UUID> = []

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
    /// Entfernt werden zuerst die Schritte, die an einer der abgebauten Flächen hängen
    /// (`removeAllActions(withTarget:)`). Ob PencilKit seine Schritte an die Fläche hängt
    /// oder an etwas in ihr, ist nicht belegt; **steht danach kein Stapel mehr, wird darum
    /// der ganze Verlauf geleert** — was er dann noch hielte, könnte nur noch unsichtbar
    /// wirken.
    ///
    /// **Die offene Lücke (offengelegt 22.09.2026, nicht behoben):** SwiftUI darf den neuen
    /// Stapel bauen, *bevor* es den alten abbaut. Dann steht beim Abbau noch einer, und der
    /// Verlauf wird nicht geleert — er gehört ja auch dem neuen. Hängt PencilKit seine
    /// Schritte nicht an die `PKCanvasView` selbst, bleiben die Schritte der abgebauten
    /// Flächen darin stehen, und «Zurück» wirkt auf eine Fläche, die niemand mehr sieht:
    /// Sichtbar geschieht nichts. **Der Zähler zeigt dann «?/20» und keine Zahl** —
    /// `Schrittzaehler.flaechenNeu` setzt «nicht gezählt», solange der `UndoManager` noch
    /// etwas zurücknehmen kann (Kern, `testNachFlaechenNeuGiltKeineAlteZahl`), und ein neuer
    /// Strich macht daraus keine Zahl. Ob der Fall am Gerät vorkommt, ist unbestätigt.
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
            // Ein Zug, der mit den Flächen abgebaut wurde, meldet sein Ende nie mehr.
            self.holeDeckungNach()
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
        deckungAusstehend.remove(id)
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

    // ------------------------------------------------------------------ Unterlage

    /// Legt ein Bild der Mappe unter die Ebenen (Bildansicht, «Darauf skizzieren»).
    ///
    /// **Keine Ebene** (Kern, `Blattunterlage`): Die Ebenen, ihre Striche, die gewählte Ebene
    /// und «Zurück» bleiben, wie sie sind — der Wechsel des Bildes ist kein Strich, und
    /// «Zurück» nimmt ihn nicht zurück. Der Radierer erreicht sie nicht: Sie ist keine
    /// PencilKit-Fläche, sondern ein Bild unter allen Flächen (`Leinwandstapel`).
    func legeUnterlage(_ unterlage: Blattunterlage, bild: UIImage) {
        stapel.legeUnterlage(unterlage)
        unterlagenbild = bild
    }

    func setzeUnterlageSichtbar(_ sichtbar: Bool) { stapel.setzeUnterlageSichtbar(sichtbar) }

    /// Nimmt die Unterlage weg — samt dem Bild, damit es nicht im Speicher bleibt.
    func entferneUnterlage() {
        stapel.entferneUnterlage()
        unterlagenbild = nil
    }

    /// Die Zeichnung einer Ebene, wie sie zuletzt gemeldet wurde.
    func zeichnung(_ id: UUID) -> PKDrawing { zeichnungen[id] ?? PKDrawing() }

    /// Die Fläche meldet jede Änderung ihrer Striche (Zeichnen, Radieren, Zurück).
    ///
    /// `imZug`: Die Änderung kam, während der Stift noch auf dem Blatt ist
    /// (`canvasViewDidBeginUsingTool` … `canvasViewDidEndUsingTool`). Dann wird das Bild
    /// einer Ebene mit abgedeckten Strichen erst am Ende des Zugs gelesen (`zugBeendet`) —
    /// ob PencilKit mitten im Zug überhaupt meldet, ist am Gerät unbestätigt; meldet es erst
    /// danach, wird gleich gelesen.
    func zeichnungGeaendert(_ id: UUID, _ zeichnung: PKDrawing, imZug: Bool = false) {
        guard stapel.ebene(id) != nil else { return }
        zeichnungen[id] = zeichnung
        meldeStriche(id, zeichnung, bildLesen: !imZug)
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

    /// Der Stift ist vom Blatt (`canvasViewDidEndUsingTool`): Steht das Bild dieser Ebene
    /// noch aus, wird es jetzt gelesen — **einmal je Zug**, nicht bei jeder Meldung darin.
    func zugBeendet(_ id: UUID, _ zeichnung: PKDrawing) {
        guard stapel.ebene(id) != nil, deckungAusstehend.contains(id) else { return }
        zeichnungen[id] = zeichnung
        meldeStriche(id, zeichnung, bildLesen: true)
    }

    /// Liest jedes Bild, das noch aussteht. Vor dem Senden, damit nie ein Stand
    /// hinausgeht, der mitten in einem Zug stehen blieb.
    private func holeDeckungNach() {
        for id in Array(deckungAusstehend) {
            guard let zeichnung = zeichnungen[id], stapel.ebene(id) != nil else {
                deckungAusstehend.remove(id)
                continue
            }
            meldeStriche(id, zeichnung, bildLesen: true)
        }
    }

    /// Meldet dem Kern, ob auf der Ebene etwas zu sehen ist.
    ///
    /// **Die Strichzahl allein reicht nicht** (Befund Durchsicht A, 22.09.2026): Der
    /// flächige Radierer (`PKEraserTool(.bitmap)`) deckt Striche nach Kenntnis ab, statt sie
    /// zu entfernen, und die Abdeckung steht am Strich (`PKStroke.mask`) — so beschrieben,
    /// am Gerät unbestätigt. Ganz weggewischt kann eine Ebene dann Striche tragen, von denen
    /// nichts zu sehen ist. Sobald ein Strich eine Abdeckung trägt, entscheidet darum das
    /// gemalte Bild (`deckung`, Regel im Kern: `setzeStriche(_:_:deckung:)`). Ohne
    /// Abdeckung ist jeder Strich zu sehen, und die Zahl gilt — so bleibt das Malen beim
    /// gewöhnlichen Zeichnen aus dem Spiel.
    ///
    /// **Liess sich das Bild nicht lesen** (`deckung` gibt `nil`), gilt die Strichzahl,
    /// aber nicht still: Die Ebene trägt dann den Vorbehalt `deckungUngewiss`, und die
    /// Ebenentafel sagt es (Befund Durchsicht, 22.09.2026). Ob `deckung` am Gerät je `nil`
    /// gibt, ist ungeprüft.
    private func meldeStriche(_ id: UUID, _ zeichnung: PKDrawing, bildLesen: Bool) {
        let anzahl = zeichnung.strokes.count
        var neu = stapel
        if zeichnung.strokes.contains(where: { $0.mask != nil }) {
            guard bildLesen else {
                // MITTEN IM ZUG: Der Stand der Tafel bleibt, bis das Bild gelesen ist.
                deckungAusstehend.insert(id)
                return
            }
            neu.setzeStriche(id, anzahl, deckung: Zeichenstand.deckung(zeichnung))
        } else {
            neu.setzeStriche(id, anzahl)
        }
        deckungAusstehend.remove(id)
        // Nur schreiben, was sich ändert: Jeder Schreibzugriff auf den Stapel zeichnet
        // die Tafel neu.
        if neu != stapel { stapel = neu }
    }

    /// Die Deckung einer Zeichnung in der Grösse der Ausgabe
    /// (`Ebenenstapel.blattBreite × blattHoehe`, Massstab 1) — oder `nil`, wenn sie sich
    /// nicht lesen liess.
    ///
    /// **Einmal gemalt, nicht zweimal** (Durchsicht, 22.09.2026). Bisher wurde die
    /// Zeichnung zu einem Bild gemalt und dieses ein zweites Mal in einen Puffer nur für die
    /// Deckung. Jetzt werden die Bytes des einen Bildes gelesen, wenn ihre Form bekannt ist
    /// (8 Bit je Kanal, 4 Bytes je Bildpunkt, Deckung vorne oder hinten); **nur sonst** wird
    /// wie bisher ein zweites Mal gemalt. Wo die Deckung im Bildpunkt steht, folgt aus
    /// `alphaInfo` und `byteOrderInfo` des Bildes; das ist nach der Beschreibung von Core
    /// Graphics abgeleitet, **am Gerät unbestätigt.** Welcher der beiden Wege dort genommen
    /// wird und wie lange er dauert: **nicht gemessen.**
    static func deckung(_ zeichnung: PKDrawing) -> Deckungsbild? {
        let rahmen = CGRect(x: 0, y: 0, width: Ebenenstapel.blattBreite,
                            height: Ebenenstapel.blattHoehe)
        guard let bild = zeichnung.image(from: rahmen, scale: 1).cgImage else { return nil }
        return gelesen(bild) ?? nachgemalt(bild)
    }

    /// Die Bytes des Bildes selbst — oder `nil`, wenn ihre Form keine der bekannten ist.
    private static func gelesen(_ bild: CGImage) -> Deckungsbild? {
        guard bild.bitsPerComponent == 8, bild.bitsPerPixel == 32,
              !bild.bitmapInfo.contains(.floatComponents),
              let stelle = alphaStelle(bild),
              let roh = bild.dataProvider?.data else { return nil }
        return Deckungsbild(daten: roh as Data, breite: bild.width, hoehe: bild.height,
                            zeilenlaenge: bild.bytesPerRow, punktlaenge: 4,
                            alphaStelle: stelle)
    }

    /// Das wievielte Byte eines 4-Byte-Bildpunkts die Deckung trägt. «Vorne» (`first`)
    /// und «hinten» (`last`) gelten in der Reihenfolge der 32-Bit-Zahl; bei
    /// `order32Little` liegt diese Zahl umgekehrt im Speicher. Eine andere Ordnung, oder
    /// ein Bild ohne Deckung: `nil`, und dann wird nachgemalt.
    private static func alphaStelle(_ bild: CGImage) -> Int? {
        let vorne: Bool
        switch bild.alphaInfo {
        case .premultipliedFirst, .first: vorne = true
        case .premultipliedLast, .last: vorne = false
        default: return nil
        }
        switch bild.byteOrderInfo {
        case .orderDefault, .order32Big: return vorne ? 0 : 3
        case .order32Little: return vorne ? 3 : 0
        default: return nil
        }
    }

    /// Der alte Weg: das Bild ein zweites Mal in einen Puffer nur für die Deckung malen.
    private static func nachgemalt(_ bild: CGImage) -> Deckungsbild? {
        let breite = bild.width
        let hoehe = bild.height
        guard breite > 0, hoehe > 0 else { return nil }
        var alpha = Data(count: breite * hoehe)
        let gemalt: Bool = alpha.withUnsafeMutableBytes { roh -> Bool in
            guard let ziel = CGContext(data: roh.baseAddress, width: breite, height: hoehe,
                                       bitsPerComponent: 8, bytesPerRow: breite,
                                       space: CGColorSpaceCreateDeviceGray(),
                                       bitmapInfo: CGImageAlphaInfo.alphaOnly.rawValue) else {
                return false
            }
            ziel.draw(bild, in: CGRect(x: 0, y: 0, width: breite, height: hoehe))
            return true
        }
        guard gemalt else { return nil }
        return Deckungsbild(daten: alpha, breite: breite, hoehe: hoehe, zeilenlaenge: breite,
                            punktlaenge: 1, alphaStelle: 0)
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

    /// **DIE SCHNITTSTELLE FÜR DAS SENDEN** (seit dem 23.09.2026): die PNG aus
    /// `pngAusgabe(_:)` und die Unterlage, wie sie gerade liegt. Ob ihr Name als `ueber`
    /// mitgeht, entscheidet der Kern (`Ablageplan`, `Unterlagenangabe`) — nicht diese Stelle.
    /// **Das Bild der Unterlage geht nie mit**: Der Server hat es schon und setzt die
    /// Skizze selbst darauf.
    func skizzenpaket(_ art: Ebenenstapel.Ausgabeart) -> Skizzenpaket {
        let ausgabe = pngAusgabe(art)
        return Skizzenpaket(ausgabe: ausgabe, unterlage: stapel.unterlage)
    }

    /// Die sichtbaren Ebenen als PNG — **ohne die Unterlage.**
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
    /// dunklen Blatt oder auf der Unterlage (`unterlagenbild`, seit dem 23.09.2026). Das
    /// Zusammensetzen auf die Unterlage macht der Server (der weiss über `ueber`, was
    /// darunter liegt; es in das PNG zu malen hiesse, es zweimal zu schicken): Seit dem 22.09.2026 setzt er die Skizze
    /// **mit ihrem Alphakanal** auf das Bild, auf dem gezeichnet wurde, oder ohne Unterlage
    /// auf ein neutrales Grau (`arbeitsgang._eingangsbild`, `setze_auf_unterlage`) — nicht
    /// auf den dunklen Grund des Blattes (`Stiftfarben.papier`).
    ///
    /// **Nicht geprüft wird hier die Grösse**: Der Server nimmt höchstens 2 MiB je Skizze
    /// (`docs/VISBOX_PROTOKOLL.md`). Das prüft, wer sendet.
    func pngAusgabe(_ art: Ebenenstapel.Ausgabeart) -> Ebenenausgabe {
        // ERST DIE AUSSTEHENDEN BILDER LESEN: Sonst ginge nach einem Zug, dessen Ende nie
        // gemeldet wurde, der Stand von davor hinaus — etwa eine weggewischte Ebene.
        holeDeckungNach()
        return Ebenenausgabe.aus(stapel.plan(art)) { teil in self.male(teil) }
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

/// Eine vorgegebene Stiftfarbe, als SwiftUI-Farbe. **Die Töne stehen im Kern**
/// (`Stiftfarben.vorgaben`, `Kern/Stiftfarben.swift`) und werden dort gegen das Blatt
/// «Main» geprüft (`FarbtonTests.testJederStifttonStehtSoAufDemBlatt`); bis zur Durchsicht
/// vom 22.09.2026 standen sie hier als Zahlen, die keine Probe sah. Sie **bedeuten
/// nichts** (Entscheid Nr. 8) und sind nur schneller erreicht als die freie Wahl daneben.
struct Stiftfarbe: Identifiable {
    let name: String
    let farbe: Color

    var id: String { name }

    static let vorgaben: [Stiftfarbe] = Stiftfarben.vorgaben.map {
        Stiftfarbe(name: $0.name, farbe: Color($0.ton))
    }
}
