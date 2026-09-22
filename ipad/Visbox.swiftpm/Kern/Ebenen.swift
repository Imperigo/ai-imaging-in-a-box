import Foundation

// DIE REGELN DER ZEICHENFLAECHE — ohne PencilKit, darum hier pruefbar.
//
// Die Zeichenflaeche (`Zeichnen/`) haelt die Striche; was davon zum Rechnen hinausgeht,
// in welcher Reihenfolge, wie viele Ebenen es geben darf und was «Zurueck» noch kann,
// steht HIER. Der Grund ist derselbe wie beim Urteil: Eine Regel, die nur in einer Ansicht
// steht, laesst sich nur am Geraet pruefen — und dort prueft sie niemand (22.09.2026).
//
// Owner-Entscheide (docs/ENTSCHEIDE_IPAD_2026-09-21.md): Nr. 2 Doppeltipp = Radierer,
// Nr. 5 Radierer umschaltbar, Nr. 6 Zurueck mit fester Tiefe 20, Nr. 7 Ebenen = Varianten,
// «gerechnet wird, was sichtbar ist», Nr. 18/32 drei Varianten nebeneinander.

/// Eine Ebene der Zeichenfläche — **jede Ebene ist eine Variante** (Entscheid Nr. 7).
///
/// Die Striche selbst liegen in der App (PencilKit); hier steht nur, wie viele es sind.
/// Mehr braucht die Regel nicht, und mehr könnte sie unter Linux auch nicht prüfen.
public struct Ebene: Identifiable, Equatable, Sendable {
    public let id: UUID
    /// Der Name, den ein Mensch sieht. Nie leer (siehe `Ebenenstapel.benenne`).
    public internal(set) var name: String
    public internal(set) var sichtbar: Bool
    /// Zwischen `Ebenenstapel.mindestDeckkraft` und 1.
    public internal(set) var deckkraft: Double
    /// Wie viele Striche auf der Ebene liegen. `0` heisst: **nichts, was man sieht** —
    /// nichts gezeichnet, oder alles weggewischt (`Ebenenstapel.setzeStriche(_:_:alpha:)`).
    public internal(set) var striche: Int

    /// Nichts gezeichnet. Das ist kein leeres Bild, sondern keines.
    public var istLeer: Bool { striche == 0 }

    /// Ob die Ebene zum Rechnen mitgeht: sichtbar **und** bezeichnet.
    public var gehtMit: Bool { sichtbar && !istLeer }
}

/// Die Ebenen übereinander, **von unten nach oben** — und die Regel, was davon hinausgeht.
///
/// **Gerechnet wird, was sichtbar ist** (Entscheid Nr. 7). Eine ausgeblendete Ebene geht
/// nie mit, in keiner Ausgabeart. Sonst rechnet die HomeStation etwas anderes, als auf dem
/// Schirm steht — derselbe Fehler wie ein erfundener Fortschrittsbalken, eine Etage tiefer.
public struct Ebenenstapel: Equatable, Sendable {

    /// Wie viele Ebenen es höchstens gibt.
    ///
    /// **Gesetzt, nicht gemessen (22.09.2026).** Jede Ebene ist in der App eine eigene
    /// Zeichenfläche mit eigenem Speicher; das Zielgerät (iPad Pro 11, 1. Gen.) hat davon
    /// wenig. Ob acht dort flüssig bleiben, zeigt erst das Gerät.
    public static let hoechstensEbenen = 8

    /// Wie viele Varianten höchstens auf einmal hinausgehen — **drei**, weil die Mappe
    /// drei nebeneinander zeigt (Entscheide Nr. 18 und Nr. 32).
    public static let hoechstensVarianten = 3

    /// Die kleinste Deckkraft einer sichtbaren Ebene.
    ///
    /// **Warum nicht null.** Eine Ebene mit Deckkraft 0 wäre «sichtbar» und doch
    /// unsichtbar — und ginge mit, obwohl auf dem Schirm nichts von ihr steht. Wer eine
    /// Ebene nicht sehen will, blendet sie aus; dann geht sie auch nicht mit.
    public static let mindestDeckkraft = 0.1

    /// Wie lang ein Name höchstens ist (in Zeichen). Gesetzt: ein Name muss in eine Zeile
    /// der Ebenentafel passen.
    public static let hoechstensNamenslaenge = 40

    /// Die Grösse des Blattes, **in Bildpunkten der Ausgabe.**
    ///
    /// Übernommen aus dem Entwurf (Blatt «Main»: «1536 × 1024 px», 3 : 2). Gesetzt, nicht
    /// gemessen: Ob das Bildmodell der HomeStation genau dieses Format will, ist offen.
    public static let blattBreite = 1536
    public static let blattHoehe = 1024

    /// Von unten nach oben — **die Stapelfolge ist die Ausgabefolge.**
    public private(set) var ebenen: [Ebene]
    /// Die Ebene, auf die der Stift zeichnet.
    public private(set) var aktiv: UUID

    /// Ein Stapel mit einer einzigen, leeren, sichtbaren Ebene «Variante A».
    public init() {
        let erste = Ebene(id: UUID(), name: Ebenenstapel.vorgabename(nummer: 0),
                          sichtbar: true, deckkraft: 1, striche: 0)
        ebenen = [erste]
        aktiv = erste.id
    }

    // ------------------------------------------------------------------ nachsehen

    /// Von oben nach unten — so, wie die Ebenentafel sie zeigt.
    public var vonObenGesehen: [Ebene] { Array(ebenen.reversed()) }

    public var aktiveEbene: Ebene {
        // `aktiv` zeigt immer auf eine vorhandene Ebene: `entferne` waehlt neu, bevor
        // es die aktive entfernt, und die letzte Ebene laesst sich nicht entfernen.
        ebenen.first { $0.id == aktiv } ?? ebenen[ebenen.count - 1]
    }

    public func ebene(_ id: UUID) -> Ebene? { ebenen.first { $0.id == id } }

    /// Ob auf die aktive Ebene gezeichnet werden darf. **Nicht, wenn sie ausgeblendet
    /// ist** — ein Strich, den man beim Zeichnen nicht sieht, ist ein Strich, den man
    /// nicht gezeichnet haben will.
    public var aktiveIstZeichenbar: Bool { aktiveEbene.sichtbar }

    public var kannAnlegen: Bool { ebenen.count < Ebenenstapel.hoechstensEbenen }
    public var kannEntfernen: Bool { ebenen.count > 1 }

    // ------------------------------------------------------------------ aendern

    /// Legt eine leere, sichtbare Ebene **zuoberst** an und macht sie aktiv — oder gibt
    /// `nil`, wenn schon `hoechstensEbenen` da sind. Nichts wird still verdrängt.
    @discardableResult
    public mutating func legeAn() -> Ebene? {
        guard kannAnlegen else { return nil }
        let neu = Ebene(id: UUID(), name: freierVorgabename(), sichtbar: true,
                        deckkraft: 1, striche: 0)
        ebenen.append(neu)
        aktiv = neu.id
        return neu
    }

    /// Entfernt eine Ebene. Die letzte bleibt stehen (`false`) — eine Zeichenfläche ohne
    /// Ebene hätte keinen Ort für den nächsten Strich.
    @discardableResult
    public mutating func entferne(_ id: UUID) -> Bool {
        guard kannEntfernen, let stelle = ebenen.firstIndex(where: { $0.id == id }) else {
            return false
        }
        if aktiv == id {
            // Die darunter, sonst die darueber: die, auf die der Blick als naechstes faellt.
            aktiv = stelle > 0 ? ebenen[stelle - 1].id : ebenen[stelle + 1].id
        }
        ebenen.remove(at: stelle)
        return true
    }

    public mutating func waehle(_ id: UUID) {
        if ebene(id) != nil { aktiv = id }
    }

    public mutating func setzeSichtbar(_ id: UUID, _ sichtbar: Bool) {
        aendere(id) { $0.sichtbar = sichtbar }
    }

    /// Setzt die Deckkraft, **begrenzt** auf `mindestDeckkraft ... 1`. Ein Wert ausserhalb
    /// (oder keine Zahl) wird an die Grenze gelegt, nicht übernommen.
    public mutating func setzeDeckkraft(_ id: UUID, _ wert: Double) {
        let begrenzt = wert.isNaN ? 1 : min(1, max(Ebenenstapel.mindestDeckkraft, wert))
        aendere(id) { $0.deckkraft = begrenzt }
    }

    /// Benennt eine Ebene um. Ein leerer Name (auch nur Leerzeichen) wird **abgelehnt**
    /// (`false`, der alte bleibt), ein zu langer gekürzt.
    @discardableResult
    public mutating func benenne(_ id: UUID, _ name: String) -> Bool {
        let sauber = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !sauber.isEmpty, ebene(id) != nil else { return false }
        let gekuerzt = String(sauber.prefix(Ebenenstapel.hoechstensNamenslaenge))
        aendere(id) { $0.name = gekuerzt }
        return true
    }

    /// Meldet, wie viele Striche eine Ebene trägt. Die App ruft das nach jeder Änderung
    /// der Zeichnung; eine negative Zahl gibt es nicht und wird zu 0.
    public mutating func setzeStriche(_ id: UUID, _ anzahl: Int) {
        aendere(id) { $0.striche = max(0, anzahl) }
    }

    /// Meldet die Striche einer Ebene **zusammen mit ihrem gemalten Bild**: `alpha` trägt
    /// ein Byte je Bildpunkt, die Deckung. Deckt kein einziger Bildpunkt (überall 0), zählt
    /// die Ebene als leer — gleich, wie viele Striche PencilKit noch führt.
    ///
    /// **Warum am Bild und nicht an der Strichzahl (Befund Durchsicht A, 22.09.2026).** Der
    /// flächige Radierer nimmt Striche nicht weg, er deckt sie ab: Nach vollständigem
    /// Radieren kann eine Ebene Striche tragen, von denen nichts mehr zu sehen ist. Nach der
    /// Strichzahl ginge sie als leeres PNG hinaus — ein Bild, das drüben aussähe wie eine
    /// bewusst leere Skizze, gegen die dritte Antwort. Die Grenze der Zeichnung
    /// (`PKDrawing.bounds`) wäre billiger, aber ob PencilKit darin die Abdeckung abzieht,
    /// ist nirgends belegt; das Bild ist das, was hinausginge.
    ///
    /// **Die Schwelle ist «grösser als 0», nicht «kaum sichtbar».** Der Server liest den
    /// Alphakanal heute nicht (`bildlesen.lies_png_luminanz` übergeht ihn): Was dort von
    /// einem schwach deckenden Bildpunkt ankommt, bestimmt nicht dessen Deckung. Ein
    /// leerer Puffer ist kein gemaltes Bild und zeigt darum nichts.
    public mutating func setzeStriche(_ id: UUID, _ anzahl: Int, alpha: Data) {
        let zeigtEtwas = alpha.contains { $0 > 0 }
        setzeStriche(id, zeigtEtwas ? anzahl : 0)
    }

    /// Schiebt eine Ebene im Stapel eine Stelle nach oben oder unten. Am Rand geschieht
    /// nichts (`false`).
    @discardableResult
    public mutating func verschiebe(_ id: UUID, nachOben: Bool) -> Bool {
        guard let stelle = ebenen.firstIndex(where: { $0.id == id }) else { return false }
        let ziel = nachOben ? stelle + 1 : stelle - 1
        guard ebenen.indices.contains(ziel) else { return false }
        ebenen.swapAt(stelle, ziel)
        return true
    }

    // ------------------------------------------------------------------ ausgeben

    /// Wie die Zeichnung hinausgeht (Entscheid Nr. 32: beides wählbar).
    public enum Ausgabeart: String, Sendable, CaseIterable {
        /// Ein Bild aus allen sichtbaren, bezeichneten Ebenen, übereinander in Stapelfolge.
        /// (Wie es auf dem Schirm aussieht, hängt zusätzlich an der Unterlage — die legt
        /// der Server darunter, nicht die App.)
        case eineSkizze
        /// Ein Bild je sichtbarer Ebene — jede eine Variante.
        case ebenenAlsVarianten
    }

    /// Ein Bild, das hinausgeht: sein Name und die Ebenen darin, **von unten nach oben.**
    public struct Teil: Equatable, Sendable {
        public let name: String
        public let ebenen: [Ebene]
    }

    /// Was hinausgehen **würde** — bevor ein einziges Bild gemalt ist.
    public enum Plan: Equatable, Sendable {
        /// Die Bilder, in Stapelfolge. Nie leer.
        case teile([Teil])
        /// **Die dritte Antwort:** Es ist nichts Sichtbares gezeichnet. Das ist kein leeres
        /// Bild, sondern keines — ein leeres PNG sähe drüben aus wie eine Skizze, auf der
        /// jemand bewusst nichts gezeichnet hat. `ausgeblendetGezeichnet` sagt, wie viele
        /// ausgeblendete Ebenen Striche tragen (die gehen nicht mit, aber sie sind da).
        case nichtsGezeichnet(ausgeblendetGezeichnet: Int)
        /// Mehr sichtbare, bezeichnete Ebenen als Varianten gehen. **Abgelehnt, nicht
        /// gekürzt:** Still drei von vier zu nehmen hiesse, eine sichtbare Ebene nicht zu
        /// rechnen — gegen «gerechnet wird, was sichtbar ist».
        case zuVieleVarianten(sichtbar: Int, hoechstens: Int)
    }

    /// Die Regel. **Eine ausgeblendete Ebene erscheint in keinem Teil**, eine leere auch
    /// nicht; die Reihenfolge ist die Stapelfolge, von unten nach oben.
    public func plan(_ art: Ausgabeart) -> Plan {
        let mit = ebenen.filter { $0.gehtMit }
        guard !mit.isEmpty else {
            let versteckt = ebenen.filter { !$0.sichtbar && !$0.istLeer }.count
            return .nichtsGezeichnet(ausgeblendetGezeichnet: versteckt)
        }
        switch art {
        case .eineSkizze:
            let name = mit.map { $0.name }.joined(separator: " + ")
            return .teile([Teil(name: name, ebenen: mit)])
        case .ebenenAlsVarianten:
            guard mit.count <= Ebenenstapel.hoechstensVarianten else {
                return .zuVieleVarianten(sichtbar: mit.count,
                                         hoechstens: Ebenenstapel.hoechstensVarianten)
            }
            return .teile(mit.map { Teil(name: $0.name, ebenen: [$0]) })
        }
    }

    // ------------------------------------------------------------------ intern

    private mutating func aendere(_ id: UUID, _ tu: (inout Ebene) -> Void) {
        guard let stelle = ebenen.firstIndex(where: { $0.id == id }) else { return }
        tu(&ebenen[stelle])
    }

    /// «Variante A», «Variante B», … — nach «Z» mit Zahl weiter.
    static func vorgabename(nummer: Int) -> String {
        let buchstaben = Array("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        if nummer < buchstaben.count { return "Variante \(buchstaben[nummer])" }
        return "Variante \(nummer + 1)"
    }

    /// Der erste Vorgabename, den noch keine Ebene trägt — damit zwei Varianten, die
    /// nebeneinander liegen, nie gleich heissen, nur weil eine dazwischen gelöscht wurde.
    private func freierVorgabename() -> String {
        let vergeben = Set(ebenen.map { $0.name })
        var nummer = 0
        while vergeben.contains(Ebenenstapel.vorgabename(nummer: nummer)) { nummer += 1 }
        return Ebenenstapel.vorgabename(nummer: nummer)
    }
}

/// Was die Zeichenfläche hinausgibt: **die PNG-Bilder, oder der Grund, warum keine.**
///
/// Die App malt die Bilder (PencilKit), der Kern entscheidet, ob das Ergebnis eines ist.
/// Die einzige Stelle, an der beides zusammenkommt, ist `aus(_:maler:)`.
public enum Ebenenausgabe: Equatable, Sendable {

    /// Ein fertiges Bild: sein Name, die Namen der Ebenen darin (von unten nach oben) und
    /// die PNG-Bytes.
    public struct Bild: Equatable, Sendable {
        public let name: String
        public let ebenen: [String]
        public let png: Data
    }

    /// Die Bilder, in Stapelfolge. Nie leer.
    case bilder([Bild])
    /// Siehe `Ebenenstapel.Plan.nichtsGezeichnet` — kein Bild, kein leeres Bild.
    case nichtsGezeichnet(ausgeblendetGezeichnet: Int)
    /// Siehe `Ebenenstapel.Plan.zuVieleVarianten`.
    case zuVieleVarianten(sichtbar: Int, hoechstens: Int)
    /// Ein Bild liess sich nicht malen. Dann geht **keines** — ein halbes Paket Varianten
    /// sähe drüben aus wie ein ganzes.
    case nichtErzeugt(grund: String)

    /// Die ersten acht Bytes jeder PNG-Datei. Der Server prüft genau diese
    /// (`docs/VISBOX_PROTOKOLL.md`, `/api/skizze`); was sie nicht trägt, weist er ab.
    public static let pngKennung: [UInt8] = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]

    /// Führt einen Plan aus: `maler` malt je Teil ein PNG (oder `nil`).
    ///
    /// Alles oder nichts: Liefert der Maler für einen Teil nichts oder etwas, das kein PNG
    /// ist, wird die ganze Ausgabe `nichtErzeugt` — mit dem Namen des Teils im Grund.
    public static func aus(_ plan: Ebenenstapel.Plan,
                           maler: (Ebenenstapel.Teil) -> Data?) -> Ebenenausgabe {
        switch plan {
        case .nichtsGezeichnet(let versteckt):
            return .nichtsGezeichnet(ausgeblendetGezeichnet: versteckt)
        case .zuVieleVarianten(let sichtbar, let hoechstens):
            return .zuVieleVarianten(sichtbar: sichtbar, hoechstens: hoechstens)
        case .teile(let teile):
            var bilder: [Bild] = []
            for teil in teile {
                guard let png = maler(teil), istPNG(png) else {
                    return .nichtErzeugt(
                        grund: "«\(teil.name)» liess sich nicht als PNG-Bild schreiben.")
                }
                bilder.append(Bild(name: teil.name, ebenen: teil.ebenen.map { $0.name },
                                   png: png))
            }
            return .bilder(bilder)
        }
    }

    static func istPNG(_ daten: Data) -> Bool {
        daten.count >= pngKennung.count && Array(daten.prefix(pngKennung.count)) == pngKennung
    }
}

/// Wie viele Schritte «Zurück» und «Vor» noch gehen — **gezählt, und wo nicht gezählt,
/// als solches gesagt.**
///
/// Die Tiefe ist fest: 20 (Entscheid Nr. 6). Die App stellt ihren `UndoManager` auf
/// genau diese Zahl (`levelsOfUndo`) — eine Stelle, nicht zwei.
///
/// **Warum `Int?`.** Der `UndoManager` sagt nur, *ob* ein Schritt zurück geht, nicht wie
/// viele. Die App zählt darum mit. Weiss der `UndoManager`, dass es zurückgeht, der Zähler
/// aber steht auf 0, hat das Mitzählen einen Schritt verpasst — dann ist die Zahl
/// **nicht gezählt** (`nil`, angezeigt als «?») und nicht still 0. *Ein Zähler, der 0
/// zeigt, während «Zurück» noch geht, lügt an der Stelle, auf die man vor dem Tippen sieht.*
public struct Schrittzaehler: Equatable, Sendable {
    public static let tiefe = 20

    /// Wie viele Schritte zurück gehen; `nil` heisst nicht gezählt.
    public private(set) var zurueck: Int? = 0
    /// Wie viele Schritte vor gehen; `nil` heisst nicht gezählt.
    public private(set) var vor: Int? = 0

    public init() {}

    /// Ein neuer Strich (oder Radierzug). Die Vor-Schritte sind danach weg — so hält es
    /// jeder `UndoManager`.
    public mutating func neuerSchritt() {
        zurueck = zurueck.map { min($0 + 1, Schrittzaehler.tiefe) }
        vor = 0
    }

    public mutating func zurueckGegangen() {
        zurueck = zurueck.map { max($0 - 1, 0) }
        vor = vor.map { min($0 + 1, Schrittzaehler.tiefe) }
    }

    public mutating func vorGegangen() {
        vor = vor.map { max($0 - 1, 0) }
        zurueck = zurueck.map { min($0 + 1, Schrittzaehler.tiefe) }
    }

    /// Alles vergessen — nach dem Löschen einer Ebene zum Beispiel.
    public mutating func geleert() {
        zurueck = 0
        vor = 0
    }

    /// **Die Flächen wurden neu gebaut**, und ihre Schritte sind aus dem `UndoManager`
    /// entfernt. Was er danach noch kann, gehört nicht zu dem, was gezählt wurde — wie viel
    /// es ist, weiss niemand.
    ///
    /// **Warum nicht `abgleichen`.** Nach sieben gezählten Strichen und dem Neuaufbau hielte
    /// `abgleichen(kannZurueck: true, …)` die 7 fest — eine Zahl über Schritte, die es nicht
    /// mehr gibt. Befund Durchsicht A (22.09.2026): Nach dem Drehen baute SwiftUI die Flächen
    /// neu, «Zurück» wirkte auf die alten, unsichtbar, und der Zähler zählte trotzdem.
    /// Hier heisst darum «es geht noch etwas» immer **nicht gezählt** («?»), und «es geht
    /// nichts» sicher 0.
    public mutating func flaechenNeu(kannZurueck: Bool, kannVor: Bool) {
        zurueck = kannZurueck ? nil : 0
        vor = kannVor ? nil : 0
    }

    /// Mit dem abgleichen, was der `UndoManager` selbst weiss. Er hat das letzte Wort
    /// darüber, **ob** es geht; der Zähler nur darüber, wie oft.
    public mutating func abgleichen(kannZurueck: Bool, kannVor: Bool) {
        if !kannZurueck { zurueck = 0 } else if zurueck == 0 { zurueck = nil }
        if !kannVor { vor = 0 } else if vor == 0 { vor = nil }
    }

    /// «7/20» — oder «?/20», wenn nicht gezählt.
    public var anzeige: String {
        "\(zurueck.map { String($0) } ?? "?")/\(Schrittzaehler.tiefe)"
    }
}

/// Die Werkzeuge des Stifts, wie die Leiste sie anbietet.
public enum Zeichenwerkzeug: String, Sendable, CaseIterable {
    case stift
    /// Nimmt ganze Striche weg (Entscheid Nr. 5).
    case radiererStriche
    /// Wischt flächig, wie ein Gummi (Entscheid Nr. 5).
    case radiererFlaeche
    /// Schiebt und zoomt; es wird nicht gezeichnet.
    case hand

    public var istRadierer: Bool { self == .radiererStriche || self == .radiererFlaeche }
}

/// Welches Werkzeug gewählt ist — und **was der Doppeltipp am Stift daraus macht.**
///
/// Doppeltipp heisst Radierer (Entscheid Nr. 2), und zwar **der zuletzt benutzte**: Wer
/// flächig radiert hat, will beim nächsten Doppeltipp nicht plötzlich ganze Striche
/// verlieren. Der zweite Doppeltipp führt zurück zu dem Werkzeug, das vorher in der Hand
/// war — so hält es auch das iPad selbst («zwischen aktuellem Werkzeug und Radierer
/// wechseln»).
public struct Werkzeugwahl: Equatable, Sendable {
    public private(set) var werkzeug: Zeichenwerkzeug = .stift
    public private(set) var letzterRadierer: Zeichenwerkzeug = .radiererStriche
    /// Wohin der Doppeltipp vom Radierer aus zurückführt.
    public private(set) var vorDemRadierer: Zeichenwerkzeug = .stift

    public init() {}

    public mutating func waehle(_ neu: Zeichenwerkzeug) {
        werkzeug = neu
        if neu.istRadierer {
            letzterRadierer = neu
        } else {
            vorDemRadierer = neu
        }
    }

    /// Werkzeug ⇄ Radierer.
    public mutating func doppeltipp() {
        waehle(werkzeug.istRadierer ? vorDemRadierer : letzterRadierer)
    }
}
