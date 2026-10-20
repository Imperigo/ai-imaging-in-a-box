import Foundation

// DER LEITUNGSSCHALTER — wo die Leitung zum Heim-PC steht, und was darum gesperrt ist
// («Visbox eigenständig», Schritt 2, Entscheid 103b, 20.10.2026; Blatt 28, Feld 1).
//
// BIS 0.3.0 HIESS ER «VORFUEHRSCHALTER» (Plan v0.1.7, Strom C2; Entscheid 40; Blatt 13b): Nach
// der Schwelle ersetzte der Vorfuehrmodus das ganze Fenster durch vorher gerechnete Bilder.
// Seit Entscheid 103b gibt es ihn nicht mehr. Der Automat ist derselbe — dieselben Lagen,
// dieselbe Schwelle, dieselbe Absage der Tuer —, aber die Lage nach der Schwelle heisst
// `ohneRechner`, und sie ERSETZT NICHTS: Die Arbeitsansicht bleibt (Knoten aus dem Buendel),
// oben steht ein Band («Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles
// andere geht. · Erneut verbinden»), und gesperrt sind genau Rechnen und Assistent
// (`Rechnersperre`). Die Saetze stehen in `Leitungssaetze` und `Rechnerband`, mit Proben.
//
// Ein Zustandsautomat OHNE eigene Uhr: Jedes Ereignis bringt seine Zeit mit (`jetzt:`). Die
// Uhr ist damit von aussen eingesetzt — die App gibt `Date()`, die Proben eine Zeit, die
// sie selbst vorruecken. Gesendet wird hier nichts (wie in `Anfragen.swift`): Der Schalter
// sagt, WANN der naechste Versuch faellig ist, und bekommt gemeldet, wie er ausging.
//
// Fuenf Lagen:
//
//   startet ──Antwort──> verbunden ──Fehlschlag──> getrennt ──Schwelle──> ohneRechner
//      │                    ^                         │                       │
//      └──Schwelle──────────┼─────────────────────────┼──────> ohneRechner    │
//                           └────────── bestaetigte Antwort ──────────────────┘
//
//   aus jeder Lage ──Absage der Tuer (401/403)──> abgewiesen ──Fehlschlag──> getrennt
//
// * EINE ABSAGE DER TUER IST KEINE STILLE (Durchsicht 01.10.2026, H2). Bei falschem Kennwort
//   oder vertippter Adresse antwortet der Heim-PC ja — nur nicht diesem Kennwort. Zaehlte
//   die Absage wie ein Fehlschlag, stuende nach der Schwelle «Heim-PC nicht erreichbar» da
//   (falsch); ein Neustart half nicht, weil das falsche Kennwort im Schluesselbund bleibt.
//   `abgewiesen` hat darum ein eigenes Band mit eigenem Satz und dem Knopf «Einrichten» —
//   gerechnet wird trotzdem nicht (`rechnenMoeglich` nur bei `verbunden`).
// * NIE SOFORT. Ein einzelner Fehlschlag ist ein Ruckler (WLAN-Wechsel, Tailscale nach dem
//   Aufwachen), kein Zustand. Erst die Schwelle schaltet um — auch beim Start ohne Leitung.
// * SEIT DEM 20.10.2026 EINE HOEHERE SCHWELLE (Owner-Befund an 0.2.11): Unterwegs ueber
//   Mobilfunk und Tailscale stand am Mac «Der Heim-PC antwortet nicht», obwohl der Heim-PC
//   gesund war (24 ms, kein Neustart) — ein Netzaussetzer ueber die Frist eines Versuchs
//   genuegte. Seither braucht es DREI Fehlschlaege in Folge UND 30 Sekunden ohne Antwort;
//   davor zeigt die App nur ein weiches Band («kurz nicht erreichbar — verbinde neu …»,
//   `kurzNichtErreichbar`) und verbindet still weiter.
// * ZURUECK NUR MIT BESTAETIGUNG. Eine Antwort, die nicht die des Heim-PC ist (unlesbar,
//   eine Fehlerseite der Weiterleitung), holt `ohneRechner` nicht zurueck: Sonst stuende
//   «Rechnen» wieder offen, und der erste Lauf scheiterte.
// * DER ABSTAND WAECHST, 5 → 10 → 20 → 40 → 60 s, wie KosmoOrbit beim Wiederverbinden
//   (5 bis 60 s, `docs/VORFUEHRFASSUNG_2026-10-01.md`). «Erneut verbinden» setzt ihn zurueck
//   und macht den naechsten Versuch sofort faellig — an der Lage aendert das nichts, bis
//   die Antwort da ist.

/// Wie ein Versuch, den Heim-PC zu erreichen, ausging.
public enum Versuchsausgang: Equatable, Sendable {
    /// **Der Heim-PC hat lesbar geantwortet** — die bestätigte Antwort. Nur sie holt aus
    /// `ohneRechner` zurück.
    case antwort
    /// Keine Antwort: Frist abgelaufen, keine Leitung, Verbindung abgewiesen.
    case keineAntwort(grund: String)
    /// Etwas kam zurück, aber **nicht die bestätigte Antwort des Heim-PC** (unlesbar, eine
    /// Fehlerseite der Weiterleitung, ein anderer Dienst). Zählt wie ein Fehlschlag.
    case unbestaetigt(grund: String)
    /// **Die Tür hat abgewiesen** — 401 (Kennwort oder Benutzer stimmt nicht) oder 403
    /// (über die Weiterleitung ohne Kennwort). Der Heim-PC antwortet also; was fehlt, ist
    /// das Einrichten. Zählt **nicht** als Fehlschlag und führt nie zu `ohneRechner`.
    case abgewiesen(grund: String)
}

extension Versuchsausgang {
    /// Der Ausgang aus der Antwort auf `GET /api/fortschritt` (`Anfragen.fortschritt`) —
    /// **bestätigt nur bei 2xx mit dem Laufstand des Visbox-Servers**: einem JSON-Objekt, in
    /// dem `laeuft` ein Wahrheitswert ist (Protokoll §5). Eine 200 von etwas anderem (eine
    /// Seite der Weiterleitung, ein anderer Dienst am selben Anschluss) ist keine Rückkehr.
    ///
    /// Eine Absage der Tür (401, 403) ist **abgewiesen**, nicht unbestätigt: Der Heim-PC
    /// lebt, und «nicht erreichbar» wäre die falsche Auskunft. Der Grund
    /// ist derselbe Satz wie in der Startzeile «Leitung» (`Startzeilen.satzZumStatus`) —
    /// er sagt, was zu tun ist —, dahinter der Satz des Servers, der sagt, wo das Kennwort
    /// steht.
    ///
    /// Kam gar keine Antwort (Frist, keine Leitung), meldet der Sender `.keineAntwort`.
    public static func aus(status: Int, daten: Data) -> Versuchsausgang {
        if status == 401 || status == 403 {
            return .abgewiesen(grund: absage(status: status, daten: daten))
        }
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

    /// Der Satz zu einer Absage: was am Mac zu tun ist, und — wenn der Server einen
    /// lesbaren Satz mitschickte — was er selbst sagt.
    static func absage(status: Int, daten: Data) -> String {
        let mac = Startzeilen.satzZumStatus(status)
        let server = Serverfehler.aus(status: status, daten: daten)
        guard server.satzVomServer else { return mac }
        return mac + " Der Heim-PC sagt: «\(server.satz)»"
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
    /// **Die Schwelle ist erreicht: kein Rechner.** Bis 0.3.0 der Vorführmodus; seit Entscheid
    /// 103b bleibt die Arbeit offen, nur Rechnen und Assistent sind gesperrt.
    case ohneRechner
    /// Der Heim-PC antwortet, aber **seine Tür weist ab** (401/403). Rechnen und Assistent
    /// gesperrt wie ohne Rechner, aber mit eigenem Satz und «Einrichten» statt «Erneut
    /// verbinden».
    case abgewiesen
}

/// Was das Fenster der Mac-App zeigt.
public enum Fensterinhalt: String, Equatable, Sendable {
    /// Die Startzeilen (Blatt 13) — mit «Einrichten» und dem Grund, warum etwas fehlt.
    case start
    /// Die Arbeit: die Knotenansicht (aus dem Bündel) und die Assistent-Leiste.
    case arbeit
}

/// Der Zustandsautomat der Leitung zum Heim-PC (bis 0.3.0 `Vorfuehrschalter`).
public struct Leitungsschalter: Equatable, Sendable {

    // ------------------------------------------------------------- die Setzungen

    /// **Drei Fehlschläge in Folge** (seit 20.10.2026; vorher zwei) — und dazu
    /// `schwelleSekunden`. Ein Netzaussetzer im Mobilfunk dauert oft länger als ein Versuch;
    /// drei Versuche mit wachsendem Abstand (5, 10 s) überbrücken eine halbe Minute.
    public static let schwelleFehlschlaege = 3
    /// **Und mindestens 30 Sekunden ohne Antwort** (seit 20.10.2026; vorher zehn, und «oder»
    /// statt «und»), gezählt ab dem ersten Fehlschlag (beim Start ab dem Start). Gesetzt, nicht
    /// gemessen; am Gerät nachzusehen.
    public static let schwelleSekunden: TimeInterval = 30
    /// **Oder 90 Sekunden ohne jede Antwort**, auch wenn keine drei Fehlschläge zurückkamen —
    /// für einen Versuch, der trotz seiner Frist hängt. Anderthalb Minuten Stille sind kein
    /// Aussetzer mehr.
    public static let schwelleSekundenAllein: TimeInterval = 90
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
    /// `ohneRechner` der erste Fehlschlag («antwortet nicht seit 14:02»), bei `verbunden`
    /// die erste bestätigte Antwort, bei `abgewiesen` die erste Absage.
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
            abstand = Leitungsschalter.lebenszeichenAbstand
            naechsterVersuch = jetzt.addingTimeInterval(abstand)
        case .abgewiesen(let grund):
            if lage != .abgewiesen {
                seit = jetzt
                stufe = 0
            }
            lage = .abgewiesen
            // KEIN FEHLSCHLAG: Der Zaehler gilt der Stille, und die Tuer hat gesprochen. Der
            // Abstand waechst trotzdem — an der Absage aendert erst das Einrichten etwas, und
            // danach setzt `neuEingerichtet` ohnehin von vorn an.
            fehlschlaege = 0
            letzterGrund = grund
            abstand = Leitungsschalter.abstand(stufe: stufe)
            stufe += 1
            naechsterVersuch = jetzt.addingTimeInterval(abstand)
        case .keineAntwort(let grund), .unbestaetigt(let grund):
            if lage == .verbunden || lage == .abgewiesen {
                // DER ERSTE FEHLSCHLAG NACH EINER ANTWORT (auch einer Absage — auch sie kam
                // vom Heim-PC): «getrennt seit» beginnt hier.
                lage = .getrennt
                seit = jetzt
                stufe = 0
            }
            fehlschlaege += 1
            letzterGrund = grund
            abstand = Leitungsschalter.abstand(stufe: stufe)
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

    /// **Neu eingerichtet** (Adresse oder Kennwort): von vorn, als wäre die App eben
    /// gestartet — der erste Versuch sofort fällig.
    ///
    /// Die bisherigen Fehlschläge galten einer anderen Adresse oder einem anderen Kennwort,
    /// oft gar keiner Adresse (solange das Blatt «Einrichten» offen ist, scheitert jeder
    /// Versuch). Blieben sie stehen, zeigte der Mac nach dem ersten Einrichten bis zum
    /// nächsten Versuch — bis zu 60 s — «nicht erreichbar», obwohl alles stimmt
    /// (Durchsicht 01.10.2026, M1).
    public mutating func neuEingerichtet(jetzt: Date) {
        self = Leitungsschalter(start: jetzt)
    }

    /// Die **Heimleitung** (die Startzeilen, ein eigener Takt) hat gefragt und `befund`
    /// bekommen. Sagt er etwas anderes, als dieser Schalter glaubt, ist der nächste Versuch
    /// **jetzt** fällig — zwei unabhängige Takte sollen nicht bis zu einer Minute lang
    /// Verschiedenes zeigen (Durchsicht 01.10.2026, M1):
    ///
    /// * 200, und der Schalter ist nicht `verbunden` → neu versuchen (die Leitung steht).
    /// * 401/403, und der Schalter ist nicht `abgewiesen` → neu versuchen (die Tür spricht —
    ///   das holt auch aus `ohneRechner`, etwa wenn der Heim-PC mit neuem Kennwort
    ///   wiederkommt).
    ///
    /// **Die Lage ändert sich hier nie.** Entschieden wird weiter nur am eigenen Versuch mit
    /// der eigenen Frist; ein Befund der Heimleitung verkürzt nur das Warten darauf. Und ein
    /// Fehlschlag der Heimleitung beschleunigt nichts: Er soll `ohneRechner` nicht früher
    /// bringen, als die Schwelle es tut.
    public mutating func heimleitungFand(_ befund: Leitungsbefund, jetzt: Date) {
        guard case .antwort(let status, _) = befund else { return }
        let stehtDort = status == 200 && lage != .verbunden
        let sprichtDort = (status == 401 || status == 403) && lage != .abgewiesen
        if stehtDort || sprichtDort {
            erneutVerbinden(jetzt: jetzt)
        }
    }

    // ---------------------------------------------------------------- die Fragen

    /// Ob jetzt ein Versuch fällig ist.
    public func faellig(jetzt: Date) -> Bool {
        jetzt >= naechsterVersuch
    }

    /// Ob die Schwelle erreicht ist: kein Rechner, Band oben, Rechnen und Assistent gesperrt.
    public var ohneRechner: Bool { lage == .ohneRechner }

    /// Ob das **weiche Band** steht: Der Heim-PC antwortete eben noch, jetzt nicht — die
    /// Schwelle ist nicht erreicht, die App verbindet still neu (`Leitungssaetze.kurzWeg`).
    public var kurzNichtErreichbar: Bool { lage == .getrennt }

    /// Ob neu gerechnet werden kann: **nur bei stehender Leitung.**
    public var rechnenMoeglich: Bool { lage == .verbunden }

    /// Was das Fenster zeigt — **entschieden hier, nicht in der Ansicht**, damit die Regel
    /// unter Linux geprüft wird:
    ///
    /// 1. Noch nicht eingerichtet → die Startansicht (das Blatt «Einrichten» liegt darüber).
    /// 2. Sonst die Arbeit, wenn «Schon anfangen» gedrückt ist (oder die App sie selbst
    ///    geöffnet hat, `oeffnetDieArbeit`), und die Startansicht, wenn nicht.
    ///
    /// **Seit Entscheid 103b ersetzt keine Lage mehr das Fenster.** Bis 0.3.0 kam hier nach der
    /// Schwelle der Vorführmodus, und bei einer Absage der Tür ging es mitten aus der Arbeit
    /// zurück zum Start. Jetzt bleibt die Arbeit offen; was fehlt, sagt das Band
    /// (`band(eingerichtet:)`), und was gesperrt ist, `sperre(eingerichtet:)`.
    public func fensterinhalt(eingerichtet: Bool, arbeitet: Bool) -> Fensterinhalt {
        guard eingerichtet else { return .start }
        return arbeitet ? .arbeit : .start
    }

    /// Ob die App **von selbst** in die Arbeit geht: wenn die Schwelle erreicht ist. Bis 0.3.0
    /// kam an dieser Stelle der Vorführmodus; jetzt die gewöhnliche Arbeit mit dem Band —
    /// sonst stünde man ohne Heim-PC vor «Schon anfangen», das erst mit Leitung geht.
    /// **Nicht, solange noch eingerichtet wird:** Ohne Adresse scheitert jeder Versuch, und nach
    /// dem ersten Einrichten soll die App mit den Startzeilen beginnen, nicht mitten in der Arbeit.
    public func oeffnetDieArbeit(eingerichtet: Bool) -> Bool {
        eingerichtet && lage == .ohneRechner
    }

    /// Ob «Schon anfangen» geht: wenn die Leitung steht (`leitungSteht`, aus den Startzeilen)
    /// **oder** die Schwelle erreicht ist — dann ohne Rechner (Entscheid 103b).
    public func anfangenMoeglich(leitungSteht: Bool) -> Bool {
        leitungSteht || lage == .ohneRechner
    }

    /// **Die Schwelle zu `ohneRechner`** (seit 20.10.2026): drei Fehlschläge in Folge **und**
    /// 30 s ohne Antwort — oder 90 s ohne jede Antwort. Eine eigene Funktion, weil das iPad
    /// dieselbe Regel für seinen Verbindungsstand nimmt (`Verbindungsstand`).
    public static func schwelleErreicht(fehlschlaege: Int, stille: TimeInterval) -> Bool {
        (fehlschlaege >= schwelleFehlschlaege && stille >= schwelleSekunden)
            || stille >= schwelleSekundenAllein
    }

    /// Der Abstand nach `stufe` Fehlschlägen: 5, 10, 20, 40, dann 60 s.
    public static func abstand(stufe: Int) -> TimeInterval {
        let roh = ersterAbstand * pow(2, Double(max(0, min(stufe, 16))))
        return min(roh, hoechsterAbstand)
    }

    // ------------------------------------------------------------------ intern

    private mutating func pruefeSchwelle(jetzt: Date) {
        guard lage == .startet || lage == .getrennt else { return }
        if Leitungsschalter.schwelleErreicht(fehlschlaege: fehlschlaege,
                                             stille: jetzt.timeIntervalSince(seit)) {
            // «SEIT» BLEIBT: Der Heim-PC antwortet nicht seit dem ersten Fehlschlag (beim
            // Start: seit dem Start), nicht erst seit dem Umschalten.
            lage = .ohneRechner
        }
    }
}

// ================================================================ was ohne Rechner gesperrt ist

/// Was gerade gesperrt ist, und warum — **für Rechnen und Assistent dieselbe Antwort**
/// (Entscheid 103b: «nur Rechnen und Assistent gesperrt»). `nil` heisst offen.
///
/// Offen auch in `startet` und `getrennt`: Vor der Schwelle ist nichts entschieden, und ein
/// Satz, der beim Start oder bei einem Aussetzer kurz aufblitzt, wäre falscher Alarm. Was in
/// dieser Zeit misslingt, sagt der Weg selbst mit seinem Satz.
public struct Rechnersperre: Equatable, Sendable {
    /// Der Satz am gesperrten Teil, oder `nil`, wenn er geht.
    public let satz: String?

    public var gesperrt: Bool { satz != nil }

    public static let offen = Rechnersperre(satz: nil)
}

extension Leitungsschalter {
    /// Ob gerade gesperrt ist, was einen Rechner braucht (Rechnen, Assistent), und mit
    /// welchem Satz. `eingerichtet: false` — kein Heim-PC gekoppelt — sperrt immer.
    public func sperre(eingerichtet: Bool) -> Rechnersperre {
        guard eingerichtet else { return Rechnersperre(satz: Leitungssaetze.sperreOhneHeim) }
        switch lage {
        case .ohneRechner: return Rechnersperre(satz: Leitungssaetze.sperreNichtErreichbar)
        case .abgewiesen: return Rechnersperre(satz: Leitungssaetze.sperreAbgewiesen)
        case .startet, .verbunden, .getrennt: return .offen
        }
    }

    /// Das Band oben im Fenster (Blatt 28, Feld 1), oder `nil`, wenn keines steht.
    ///
    /// * `getrennt` → das **weiche** Band («kurz nicht erreichbar — verbinde neu …»), ohne
    ///   Knopf: Die App verbindet ohnehin still neu.
    /// * `ohneRechner` → «Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles
    ///   andere geht. · Erneut verbinden».
    /// * `abgewiesen` → derselbe Aufbau mit eigenem Satz und «Einrichten»: Hier hilft kein
    ///   neuer Versuch, nur ein neues Kennwort.
    /// * Noch nicht eingerichtet → keines: Dann liegt das Blatt «Einrichten» über allem.
    public func band(eingerichtet: Bool) -> Rechnerband? {
        guard eingerichtet else { return nil }
        switch lage {
        case .getrennt: return .kurzWeg
        case .ohneRechner: return .nichtErreichbar
        case .abgewiesen: return .abgewiesen
        case .startet, .verbunden: return nil
        }
    }

    /// Der Satz neben «Schon anfangen»: ohne Rechner der eigene, sonst der der Startzeilen.
    public func anfangenSatz(startzeilen: String, leitungSteht: Bool) -> String {
        (!leitungSteht && lage == .ohneRechner) ? Leitungssaetze.anfangenOhneRechner : startzeilen
    }
}

/// Das Band oben im Fenster, nach Blatt 28 (Feld 1).
public struct Rechnerband: Equatable, Sendable {
    /// Welcher Knopf rechts im Band steht.
    public enum Knopf: String, Equatable, Sendable {
        /// «Erneut verbinden» — der nächste Versuch jetzt (`Leitungsschalter.erneutVerbinden`).
        case erneutVerbinden
        /// «Einrichten» — das Blatt mit Kopplung und Kennwort.
        case einrichten

        public var wort: String {
            switch self {
            case .erneutVerbinden: return Leitungssaetze.erneutVerbinden
            case .einrichten: return Leitungssaetze.einrichten
            }
        }
    }

    /// Fett, links: «Heim-PC nicht erreichbar».
    public let titel: String
    /// Daneben: «Rechnen und Assistent gesperrt — alles andere geht.» (`nil` beim weichen Band.)
    public let satz: String?
    public let knopf: Knopf?
    /// Das weiche Band vor der Schwelle: kein Zustand, ein Aussetzer — leiser gezeichnet.
    public let weich: Bool

    public static let kurzWeg = Rechnerband(titel: Leitungssaetze.kurzWeg, satz: nil,
                                            knopf: nil, weich: true)
    public static let nichtErreichbar = Rechnerband(titel: Leitungssaetze.bandNichtErreichbar,
                                                    satz: Leitungssaetze.bandGesperrt,
                                                    knopf: .erneutVerbinden, weich: false)
    public static let abgewiesen = Rechnerband(titel: Leitungssaetze.bandAbgewiesen,
                                               satz: Leitungssaetze.bandAbgewiesenSatz,
                                               knopf: .einrichten, weich: false)

    // DIE FARBEN DES BANDS (Blatt 28, Feld 1): ein gedämpftes Gelb — «Achtung», kein Urteil.
    // Im Kern, damit die Probe sie gegen das Blatt hält und die Lesbarkeit prüft.
    public static let grund = Farbton(hex: "2a2416")
    public static let rand = Farbton(hex: "5a4a22")
    public static let schrift = Farbton(hex: "e8d9b0")

    /// Für die Bedienungshilfe: alles in einem Satz.
    public var vorgelesen: String {
        [titel, satz].compactMap { $0 }.joined(separator: ". ")
    }
}

/// Die Sätze rund um die Leitung, an einer Stelle und geprüft (bis 0.3.0 `Vorfuehrsaetze`).
public enum Leitungssaetze {
    /// Das weiche Band vor der Schwelle (20.10.2026): kein Zustand, ein Aussetzer.
    public static let kurzWeg = "Heim-PC kurz nicht erreichbar — verbinde neu …"
    /// Blatt 28, Feld 1 — wörtlich.
    public static let bandNichtErreichbar = "Heim-PC nicht erreichbar"
    /// Blatt 28, Feld 1 — wörtlich.
    public static let bandGesperrt = "Rechnen und Assistent gesperrt — alles andere geht."
    /// Die Tür weist ab (401/403): eigener Satz, eigener Knopf.
    public static let bandAbgewiesen = "Heim-PC weist die Anmeldung ab"
    public static let bandAbgewiesenSatz = "Rechnen und Assistent gesperrt, bis Kennwort oder "
        + "Kopplung unter «Einrichten» stimmen — alles andere geht."
    public static let erneutVerbinden = "Erneut verbinden"
    /// Der Knopf zum Blatt «Einrichten» — **immer erreichbar**: Stimmen Adresse oder Kennwort
    /// nicht, ist das der einzige Weg hinaus.
    public static let einrichten = "Einrichten"

    /// Am gesperrten Teil (Assistent-Leiste; Blatt 28 am Render-Knoten): wörtlich wie im Blatt.
    public static let sperreNichtErreichbar = "Braucht einen Rechner — Heim-PC nicht erreichbar."
    public static let sperreAbgewiesen = "Braucht einen Rechner — der Heim-PC weist die "
        + "Anmeldung ab. Unter «Einrichten» neu koppeln."
    public static let sperreOhneHeim = "Braucht einen Rechner — noch kein Heim-PC eingerichtet."

    /// Neben «Schon anfangen», wenn es ohne Rechner geht.
    public static let anfangenOhneRechner = "Geht auch ohne Heim-PC — Rechnen und Assistent "
        + "sind dann gesperrt."
}
