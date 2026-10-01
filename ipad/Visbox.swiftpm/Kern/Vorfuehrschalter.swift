import Foundation

// DER VORFUEHRSCHALTER — von selbst in den Vorfuehrmodus, und erst nach einer bestaetigten
// Antwort wieder zurueck (Plan v0.1.7, Strom C2; Entscheid 40; Blatt 13b).
//
// Ein Zustandsautomat OHNE eigene Uhr: Jedes Ereignis bringt seine Zeit mit (`jetzt:`). Die
// Uhr ist damit von aussen eingesetzt — die App gibt `Date()`, die Proben eine Zeit, die
// sie selbst vorruecken. Gesendet wird hier nichts (wie in `Anfragen.swift`): Der Schalter
// sagt, WANN der naechste Versuch faellig ist, und bekommt gemeldet, wie er ausging.
//
// Vier Lagen:
//
//   startet ──Antwort──> verbunden ──Fehlschlag──> getrennt ──Schwelle──> vorfuehrung
//      │                    ^                         │                       │
//      └──Schwelle──────────┼─────────────────────────┼──────> vorfuehrung    │
//                           └────────── bestaetigte Antwort ──────────────────┘
//
// * NIE SOFORT. Ein einzelner Fehlschlag ist ein Ruckler (WLAN-Wechsel, Tailscale nach dem
//   Aufwachen), kein Zustand. Erst die Schwelle schaltet um — auch beim Start ohne Leitung.
// * ZURUECK NUR MIT BESTAETIGUNG. Eine Antwort, die nicht die des Heim-PC ist (unlesbar,
//   eine Fehlerseite der Weiterleitung), holt den Vorfuehrmodus nicht zurueck: Sonst
//   stuende «Rechnen» wieder offen, und der erste Lauf scheiterte vor Publikum.
// * DER ABSTAND WAECHST, 5 → 10 → 20 → 40 → 60 s, wie KosmoOrbit beim Wiederverbinden
//   (5 bis 60 s, `docs/VORFUEHRFASSUNG_2026-10-01.md`). «Erneut verbinden» setzt ihn zurueck
//   und macht den naechsten Versuch sofort faellig — am Vorfuehrmodus aendert das nichts,
//   bis die Antwort da ist.

/// Wie ein Versuch, den Heim-PC zu erreichen, ausging.
public enum Versuchsausgang: Equatable, Sendable {
    /// **Der Heim-PC hat lesbar geantwortet** — die bestätigte Antwort. Nur sie holt aus dem
    /// Vorführmodus zurück.
    case antwort
    /// Keine Antwort: Frist abgelaufen, keine Leitung, Verbindung abgewiesen.
    case keineAntwort(grund: String)
    /// Etwas kam zurück, aber **nicht die bestätigte Antwort des Heim-PC** (unlesbar, eine
    /// Fehlerseite der Weiterleitung, ein anderer Dienst). Zählt wie ein Fehlschlag.
    case unbestaetigt(grund: String)
}

extension Versuchsausgang {
    /// Der Ausgang aus der Antwort auf `GET /api/fortschritt` (`Anfragen.fortschritt`) —
    /// **bestätigt nur bei 2xx mit dem Laufstand des Visbox-Servers**: einem JSON-Objekt, in
    /// dem `laeuft` ein Wahrheitswert ist (Protokoll §5). Eine 200 von etwas anderem (eine
    /// Seite der Weiterleitung, ein anderer Dienst am selben Anschluss) ist keine Rückkehr.
    ///
    /// Eine Absage des Servers (401, falsches Kennwort) ist ebenfalls **unbestätigt**: Der
    /// Heim-PC lebt, aber rechnen lässt er so nicht — und darum geht es hier. Welcher Satz
    /// dazu am Mac steht, sagt die Startzeile «Heim-PC», nicht dieser Schalter.
    ///
    /// Kam gar keine Antwort (Frist, keine Leitung), meldet der Sender `.keineAntwort`.
    public static func aus(status: Int, daten: Data) -> Versuchsausgang {
        do {
            let o = try liesAntwort(status: status, daten: daten)
            guard o["laeuft"]?.alsWahrheit != nil else {
                return .unbestaetigt(grund: "Es antwortete etwas, aber nicht der Laufstand "
                    + "des Heim-PC (ohne «laeuft»).")
            }
            return .antwort
        } catch let f as Serverfehler {
            return .unbestaetigt(grund: f.satz)
        } catch {
            return .unbestaetigt(grund: "Die Antwort des Heim-PC war nicht lesbar.")
        }
    }
}

/// Wo die Leitung zum Heim-PC steht.
public enum Leitungslage: String, Equatable, Sendable {
    /// Seit dem Start noch keine Antwort, und die Schwelle ist nicht erreicht.
    case startet
    /// Der Heim-PC hat zuletzt bestätigt geantwortet.
    case verbunden
    /// Zuletzt kam keine Antwort; die Schwelle ist nicht erreicht.
    case getrennt
    /// **Der Vorführmodus** — vorher gerechnete Bilder, Rechnen gesperrt.
    case vorfuehrung
}

/// Der Zustandsautomat des Vorführmodus.
public struct Vorfuehrschalter: Equatable, Sendable {

    // ------------------------------------------------------------- die Setzungen

    /// **Zwei Fehlschläge in Folge** schalten um. Einer ist ein Ruckler; zwei, zwischen
    /// denen mindestens `ersterAbstand` liegt, sind ein Zustand.
    public static let schwelleFehlschlaege = 2
    /// **Oder zehn Sekunden ohne Antwort**, gezählt ab dem ersten Fehlschlag (beim Start ab
    /// dem Start). Für den Fall, dass ein Versuch hängt und kein zweiter Fehlschlag kommt —
    /// zehn Sekunden Stille vor Publikum sind lang genug, um es zu sagen. Gesetzt, nicht
    /// gemessen; am Gerät nachzusehen.
    public static let schwelleSekunden: TimeInterval = 10
    /// Der erste Abstand zwischen zwei Versuchen — wie KosmoOrbit.
    public static let ersterAbstand: TimeInterval = 5
    /// Der grösste Abstand — wie KosmoOrbit.
    public static let hoechsterAbstand: TimeInterval = 60
    /// Wie oft bei stehender Leitung nachgefragt wird, ob sie noch steht.
    public static let lebenszeichenAbstand: TimeInterval = 10
    /// **Die Frist eines einzelnen Versuchs.** Kürzer als `schwelleSekunden`, damit ein
    /// hängender Versuch als Fehlschlag zurückkommt, bevor die Zeitschwelle allein greift.
    /// Der Sender der App setzt sie (`URLRequest.timeoutInterval`).
    public static let versuchsfrist: TimeInterval = 8

    // ------------------------------------------------------------------ der Stand

    public private(set) var lage: Leitungslage
    /// **Seit wann** die Lage gilt: bei `startet` der Start, bei `getrennt` und
    /// `vorfuehrung` der erste Fehlschlag («antwortet nicht seit 14:02»), bei `verbunden`
    /// die erste bestätigte Antwort.
    public private(set) var seit: Date
    /// Fehlschläge in Folge seit der letzten bestätigten Antwort (oder dem Start).
    public private(set) var fehlschlaege: Int
    /// Wann der nächste Versuch fällig ist.
    public private(set) var naechsterVersuch: Date
    /// Der Abstand, mit dem `naechsterVersuch` zuletzt gesetzt wurde.
    public private(set) var abstand: TimeInterval
    /// Wann zuletzt ein Versuch zurückkam (gleich wie) — «Letzter Versuch vor 20 s».
    public private(set) var letzterVersuch: Date?
    /// Wann zuletzt bestätigt geantwortet wurde.
    public private(set) var letzteAntwort: Date?
    /// Warum der letzte Versuch scheiterte, oder `nil`.
    public private(set) var letzterGrund: String?
    /// Wie viele Fehlschläge seit dem letzten Zurücksetzen den Abstand wachsen liessen.
    private var stufe: Int

    /// Der Schalter beim Start: noch keine Antwort, **der erste Versuch sofort fällig**.
    public init(start: Date) {
        lage = .startet
        seit = start
        fehlschlaege = 0
        naechsterVersuch = start
        abstand = 0
        letzterVersuch = nil
        letzteAntwort = nil
        letzterGrund = nil
        stufe = 0
    }

    // -------------------------------------------------------------- die Ereignisse

    /// Ein Versuch kam zurück.
    public mutating func melde(_ ausgang: Versuchsausgang, jetzt: Date) {
        letzterVersuch = jetzt
        switch ausgang {
        case .antwort:
            if lage != .verbunden { seit = jetzt }
            lage = .verbunden
            fehlschlaege = 0
            stufe = 0
            letzteAntwort = jetzt
            letzterGrund = nil
            abstand = Vorfuehrschalter.lebenszeichenAbstand
            naechsterVersuch = jetzt.addingTimeInterval(abstand)
        case .keineAntwort(let grund), .unbestaetigt(let grund):
            if lage == .verbunden {
                // DER ERSTE FEHLSCHLAG NACH EINER ANTWORT: «getrennt seit» beginnt hier.
                lage = .getrennt
                seit = jetzt
                stufe = 0
            }
            fehlschlaege += 1
            letzterGrund = grund
            abstand = Vorfuehrschalter.abstand(stufe: stufe)
            stufe += 1
            naechsterVersuch = jetzt.addingTimeInterval(abstand)
            pruefeSchwelle(jetzt: jetzt)
        }
    }

    /// Die Zeit ist vorgerückt — für die Zeitschwelle, auch wenn kein Versuch zurückkam.
    public mutating func ticke(jetzt: Date) {
        pruefeSchwelle(jetzt: jetzt)
    }

    /// «Erneut verbinden»: der Abstand zurück auf den ersten, der nächste Versuch **jetzt**.
    /// Die Lage bleibt — zurück geht es erst mit der bestätigten Antwort.
    public mutating func erneutVerbinden(jetzt: Date) {
        stufe = 0
        abstand = 0
        naechsterVersuch = jetzt
    }

    // ---------------------------------------------------------------- die Fragen

    /// Ob jetzt ein Versuch fällig ist.
    public func faellig(jetzt: Date) -> Bool {
        jetzt >= naechsterVersuch
    }

    /// Ob der Vorführmodus gezeigt wird.
    public var imVorfuehrmodus: Bool { lage == .vorfuehrung }

    /// Ob neu gerechnet werden kann: **nur bei stehender Leitung.**
    public var rechnenMoeglich: Bool { lage == .verbunden }

    /// Der Abstand nach `stufe` Fehlschlägen: 5, 10, 20, 40, dann 60 s.
    public static func abstand(stufe: Int) -> TimeInterval {
        let roh = ersterAbstand * pow(2, Double(max(0, min(stufe, 16))))
        return min(roh, hoechsterAbstand)
    }

    // ------------------------------------------------------------------ intern

    private mutating func pruefeSchwelle(jetzt: Date) {
        guard lage == .startet || lage == .getrennt else { return }
        if fehlschlaege >= Vorfuehrschalter.schwelleFehlschlaege
            || jetzt.timeIntervalSince(seit) >= Vorfuehrschalter.schwelleSekunden {
            // «SEIT» BLEIBT: Der Heim-PC antwortet nicht seit dem ersten Fehlschlag (beim
            // Start: seit dem Start), nicht erst seit dem Umschalten.
            lage = .vorfuehrung
        }
    }
}

// ================================================================== Farben und Sätze

/// Die Farben des Vorführmodus (Blatt 13b) — **ein eigener Ton, Violett**, damit der Modus
/// sich von jedem Urteil unterscheidet: *nichts auf diesem Schirm ist gerade gerechnet.*
/// Im Kern, damit `VorfuehrschalterTests` sie gegen das Blatt und gegen die Urteilsfarben
/// hält.
public enum Vorfuehrfarbe {
    /// Schrift und Plakette.
    public static let violett = Farbton(hex: "a996e0")
    /// Rand des Bands und des Kastens.
    public static let rand = Farbton(hex: "5b4f7a")
    /// Grund des Bands und des Kastens.
    public static let grund = Farbton(hex: "1d1a26")
    /// Der Punkt «geht» — das Grün von «bestanden».
    public static let geht = Zeichenart.bestanden.rand
    /// Der Punkt «geht nicht» — das Rot von «durchgefallen».
    public static let gehtNicht = Zeichenart.durchgefallen.rand
}

/// Die Sätze des Vorführmodus (Blatt 13b), an einer Stelle und geprüft.
public enum Vorfuehrsaetze {
    public static let plakette = "Vorführmodus"
    public static let bandWort = "VORFÜHRMODUS"
    public static let erneutVerbinden = "Erneut verbinden"
    public static let rechnenTitel = "Neu rechnen"
    public static let rechnenKnopf = "Rechnen, gesperrt"
    public static let rechnenSatz = "geht erst wieder, wenn der Heim-PC antwortet. Zeichnen "
        + "geht — die Skizze wartet im Parkfach und fährt mit, sobald die Leitung steht."
    public static let spaltenTitel = "Was nicht geht, und warum"
    public static let assistent = "Assistent: läuft am Heim-PC, darum ebenfalls nicht da."
    public static let ipadVerbunden = "iPad: verbunden mit diesem Mac — zeichnen und zeigen geht."
    public static let ipadNichtVerbunden = "iPad: nicht mit diesem Mac verbunden — gezeigt "
        + "wird nur hier am Mac."
    public static let kasten = "Violett heisst hier: nichts auf diesem Schirm ist gerade "
        + "gerechnet. Die Prüfzeichen an den Bildern gelten für den Tag, an dem sie gerechnet "
        + "wurden — das Datum steht daneben."
    /// Bei einer Platzhalter-Mappe: Die Zeichen sind nicht einmal an einem Tag gemessen.
    public static let platzhalterKasten = "Diese Mappe hält Platzhalter: graue Flächen, die "
        + "Zeichen von Hand gesetzt, nicht gemessen. Die echte Beispielmappe rechnet der Heim-PC."

    /// «14:02» in der Zeitzone `zone`.
    public static func uhrzeit(_ zeit: Date, zone: TimeZone) -> String {
        var kalender = Calendar(identifier: .gregorian)
        kalender.timeZone = zone
        let t = kalender.dateComponents([.hour, .minute], from: zeit)
        return String(format: "%02d:%02d", t.hour ?? 0, t.minute ?? 0)
    }

    /// Das Band: «Der Heim-PC antwortet nicht (seit 14:02). Gezeigt werden Bilder, die
    /// vorher gerechnet wurden — neue Läufe sind nicht möglich.»
    public static func band(seit: Date, zone: TimeZone) -> String {
        "Der Heim-PC antwortet nicht (seit \(uhrzeit(seit, zone: zone))). Gezeigt werden "
            + "Bilder, die vorher gerechnet wurden — neue Läufe sind nicht möglich."
    }

    /// «vor 20 s», «vor 3 min», «um 13:40» — wie lange ein Zeitpunkt zurückliegt.
    public static func vorWieLange(_ zeit: Date, jetzt: Date, zone: TimeZone) -> String {
        let sekunden = max(0, Int(jetzt.timeIntervalSince(zeit)))
        if sekunden < 60 { return "vor \(sekunden) s" }
        if sekunden < 3600 { return "vor \(sekunden / 60) min" }
        return "um \(uhrzeit(zeit, zone: zone))"
    }

    /// Die Zeile zur Leitung: «Leitung zum Heim-PC: keine Antwort seit 14:02. Letzter
    /// Versuch vor 20 s.»
    public static func leitung(seit: Date, letzterVersuch: Date?, jetzt: Date,
                               zone: TimeZone) -> String {
        let anfang = "Leitung zum Heim-PC: keine Antwort seit \(uhrzeit(seit, zone: zone))."
        guard let v = letzterVersuch else { return anfang + " Noch kein Versuch zurück." }
        return anfang + " Letzter Versuch \(vorWieLange(v, jetzt: jetzt, zone: zone))."
    }
}
