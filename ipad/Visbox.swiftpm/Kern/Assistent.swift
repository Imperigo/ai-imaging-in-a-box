import Foundation

// DER ASSISTENT IM KERN (Plan v0.1.7, Strom D3) — nur Foundation, darum unter Linux pruefbar.
//
// Was hier steht: die Anfragen an `POST /api/assistent`, `POST /api/assistent/anwenden` und
// `GET /api/heim`, die Typen ihrer Antworten, die Karte (Blatt 14) und der Zustand des
// Gespraechs. Was hier NICHT steht: das Senden (macht die App, wie bei allen Wegen) und das
// Zeichnen (`VisboxMac/Assistent/Assistentenleiste.swift`).
//
// Der Assistent rechnet nie (Entscheid 41): Ein Vorschlag wird erst mit «Anwenden» zu einem
// Lauf, und «Anwenden» ist eine eigene Anfrage, die nur ein Mensch ausloest. Die Felder
// stehen so, wie `oberflaeche/server.py` sie am 01.10.2026 liefert
// (`docs/VISBOX_PROTOKOLL.md`, §3).

// ======================================================================= das Gespraech

/// Wer etwas gesagt hat — die zwei Rollen, die der Server annimmt. Eine dritte («system»)
/// weist er ab: Sie wäre ein Weg, dem Modell eine Anweisung unterzuschieben.
public enum Sprecher: String, Codable, Equatable, Sendable {
    case mensch
    case assistent
}

/// Ein Beitrag im Verlauf, wie er an `POST /api/assistent` geht (`{"von", "text"}`).
public struct Gespraechsbeitrag: Codable, Equatable, Sendable {
    public let von: Sprecher
    public let text: String

    public init(von: Sprecher, text: String) {
        self.von = von
        self.text = text
    }

    var alsJSON: JSONWert { .objekt(["von": .text(von.rawValue), "text": .text(text)]) }
}

/// Die geschätzte Rechenzeit — **ohne Zahl, solange sie nicht gemessen ist.**
public struct Rechenzeit: Codable, Equatable, Sendable {
    public let sekunden: Int?
    public let satz: String

    public init(sekunden: Int?, satz: String) {
        self.sekunden = sekunden
        self.satz = satz
    }
}

/// Ein Vorschlag des Assistenten. `einstellungen` sind Felder der Bildkette; `null` heisst
/// dort «für diesen Lauf auf die Vorgabe zurück» und wird darum mitgeführt, nicht
/// weggelassen. `saetze` sind die Zeilen der Karte, gebaut vom Server aus den geprüften
/// Einstellungen — nicht aus dem freien Text des Modells.
public struct Assistentenvorschlag: Codable, Equatable, Sendable {
    public let einstellungen: [String: JSONWert]
    public let varianten: Int?
    public let saetze: [String]
    public let rechenzeit: Rechenzeit?

    public init(einstellungen: [String: JSONWert], varianten: Int?, saetze: [String],
                rechenzeit: Rechenzeit?) {
        self.einstellungen = einstellungen
        self.varianten = varianten
        self.saetze = saetze
        self.rechenzeit = rechenzeit
    }

    /// So geht er an `POST /api/assistent/anwenden` zurück. Drüben wird er **neu geprüft**;
    /// angewendet wird nur, was ein Werkzeug auch hätte vorschlagen können.
    public var alsJSON: JSONWert {
        var o: [String: JSONWert] = ["einstellungen": .objekt(einstellungen),
                                     "saetze": .liste(saetze.map { .text($0) })]
        o["varianten"] = varianten.map { .ganz($0) } ?? .null
        return .objekt(o)
    }
}

/// Was `POST /api/assistent` zurückgibt: die Antwort (nie der Gedankentext des Modells) und
/// vielleicht einen Vorschlag.
public struct Assistentenantwort: Codable, Equatable, Sendable {
    public let antwort: String
    public let vorschlag: Assistentenvorschlag?
    /// Stufe 5 (KI-Bedienung, 21.10.2026): Werkzeugaufrufe, die die App in der Knotenansicht
    /// ausfuehrt, bevor sie weiterfragt (`schritte_offen`). Leer: Die Antwort ist fertig.
    public let schritte: [Assistentenaufruf]

    public init(antwort: String, vorschlag: Assistentenvorschlag?, schritte: [Assistentenaufruf] = []) {
        self.antwort = antwort
        self.vorschlag = vorschlag
        self.schritte = schritte
    }

    enum CodingKeys: String, CodingKey {
        case antwort, vorschlag
        case schritte = "schritte_offen"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        antwort = try c.decode(String.self, forKey: .antwort)
        vorschlag = try c.decodeIfPresent(Assistentenvorschlag.self, forKey: .vorschlag)
        schritte = try c.decodeIfPresent([Assistentenaufruf].self, forKey: .schritte) ?? []
    }

    /// Liest die Antwort — oder wirft den `Serverfehler` mit dem Satz des Servers.
    public static func lies(status: Int, daten: Data) throws -> Assistentenantwort {
        _ = try liesAntwort(status: status, daten: daten)
        do {
            return try JSONDecoder().decode(Assistentenantwort.self, from: daten)
        } catch {
            throw Serverfehler.unlesbar(status, "keine Antwort des Assistenten")
        }
    }
}

// ======================================================= Werkzeugschritte (Stufe 5, 21.10.2026)

/// Ein Werkzeugaufruf des Assistenten, wie der Heim-PC ihn zurueckgibt — die App fuehrt ihn in der
/// Knotenansicht aus (als Urheber «assistent»: Karte, Coop oder Voll wie bei Claude).
public struct Assistentenaufruf: Codable, Equatable, Sendable {
    public let werkzeug: String
    public let argumente: [String: JSONWert]

    public init(werkzeug: String, argumente: [String: JSONWert]) {
        self.werkzeug = werkzeug
        self.argumente = argumente
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        werkzeug = try c.decode(String.self, forKey: .werkzeug)
        argumente = (try? c.decodeIfPresent([String: JSONWert].self, forKey: .argumente)) ?? [:]
    }
}

/// Ein ausgefuehrter Schritt — geht mit der naechsten Anfrage zurueck an den Heim-PC.
public struct Assistentenschritt: Equatable, Sendable {
    public let aufruf: Assistentenaufruf
    public let ergebnis: String

    public init(aufruf: Assistentenaufruf, ergebnis: String) {
        self.aufruf = aufruf
        self.ergebnis = ergebnis
    }

    var alsJSON: JSONWert {
        .objekt(["werkzeug": .text(aufruf.werkzeug), "argumente": .objekt(aufruf.argumente),
                 "ergebnis": .text(ergebnis)])
    }
}

// =================================================================== der Stand (Heim-PC)

/// Die vier Antworten der Zeile «Assistent» (`GET /api/heim`, Feld `assistent.stand`).
public enum Assistentenstand: String, Codable, Equatable, Sendable, CaseIterable {
    /// Antwortet — sofort oder nach einigen Sekunden Laden; der Satz sagt, welches.
    case bereit
    /// Liegt da, aber gerade rechnet ein Bild; danach kommt er wieder.
    case laedt
    /// Ollama antwortet, das Modell liegt nicht da (oder ist nicht zugelassen).
    case fehlt
    /// Ollama antwortet nicht.
    case aus
}

/// Die Zeile «Assistent» aus `GET /api/heim`.
public struct Assistentenzeile: Codable, Equatable, Sendable {
    /// `nil`, wenn der Server einen Stand schickt, den diese App nicht kennt — dann wird
    /// **nicht** geraten, sondern nicht eingegeben (`nimmtEingabe` ist falsch).
    public let stand: Assistentenstand?
    public let modell: String?
    public let satz: String

    public init(stand: Assistentenstand?, modell: String?, satz: String) {
        self.stand = stand
        self.modell = modell
        self.satz = satz
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        stand = Assistentenstand(rawValue: (try? c.decode(String.self, forKey: .stand)) ?? "")
        modell = try c.decodeIfPresent(String.self, forKey: .modell)
        satz = try c.decode(String.self, forKey: .satz)
    }

    /// Nur bei `bereit` gibt es ein Eingabefeld (Blatt 14); sonst steht der Satz da.
    public var nimmtEingabe: Bool { stand == .bereit }

    /// Liest die Zeile aus der ganzen Antwort von `GET /api/heim`.
    public static func ausHeim(status: Int, daten: Data) throws -> Assistentenzeile {
        let o = try liesAntwort(status: status, daten: daten)
        guard let zeile = o["assistent"], let roh = try? zeile.daten(),
              let gelesen = try? JSONDecoder().decode(Assistentenzeile.self, from: roh) else {
            throw Serverfehler.unlesbar(status, "keine Zeile «assistent»")
        }
        return gelesen
    }
}

// ============================================================================ die Karte

/// Der vorgeschlagene Standpunkt, wie ihn der Plan violett neben den heutigen zeichnet.
public enum VorgeschlagenerStandpunkt: Equatable, Sendable {
    /// Ein Richtungskürzel (`n`, `sSE`, …) — der Standpunkt wird drüben aus der Hülle
    /// gerechnet; der Plan zeigt die Richtung, keinen Punkt.
    case richtung(String)
    /// Von Hand, in Metern im Weltsystem.
    case vonHand(auge: [Double], blickAuf: [Double])

    /// Aus den Einstellungen eines Vorschlags — `nil`, wenn er keinen Standpunkt trägt.
    public init?(_ einstellungen: [String: JSONWert]) {
        if let kuerzel = einstellungen["kamera"]?.alsText, !kuerzel.isEmpty {
            self = .richtung(kuerzel)
            return
        }
        guard let auge = Self.punkt(einstellungen["auge"]),
              let ziel = Self.punkt(einstellungen["blick_auf"]) else { return nil }
        self = .vonHand(auge: auge, blickAuf: ziel)
    }

    private static func punkt(_ wert: JSONWert?) -> [Double]? {
        guard let liste = wert?.alsListe, liste.count == 3 else { return nil }
        let zahlen = liste.compactMap(\.alsZahl)
        return zahlen.count == 3 ? zahlen : nil
    }
}

/// Die violett gerahmte Karte von Blatt 14 — **abgeleitet**, nicht gespeichert.
public struct Assistentenkarte: Equatable, Sendable {
    /// Die Zeilen unter «Vorschlag:».
    public let zeilen: [String]
    /// Die Zeile zur Rechenzeit — ohne Zahl, solange nicht gemessen.
    public let rechenzeit: String?
    public let standpunkt: VorgeschlagenerStandpunkt?

    public init(_ vorschlag: Assistentenvorschlag) {
        let saetze = vorschlag.saetze.filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        // KEINE ZEILEN, ABER EIN VORSCHLAG: Dann wird gesagt, was er enthaelt, statt eine
        // leere Karte mit «Anwenden» zu zeigen — angewendet wuerde etwas, das niemand sah.
        if saetze.isEmpty {
            var felder = vorschlag.einstellungen.filter { !$0.value.istNull }.keys.sorted()
            if let v = vorschlag.varianten { felder.append("\(v) Varianten") }
            zeilen = ["Vorschlag ohne Beschreibung: " + felder.joined(separator: ", ")]
        } else {
            zeilen = saetze
        }
        rechenzeit = vorschlag.rechenzeit?.satz
        standpunkt = VorgeschlagenerStandpunkt(vorschlag.einstellungen)
    }

    /// «Ändern» legt den Vorschlag als Text ins Eingabefeld — zum Umschreiben, nicht als
    /// Befehl. Die Nutzerin schickt ihn danach selbst ab.
    public var aenderungstext: String {
        "Bitte ändern: " + zeilen.joined(separator: " · ")
    }
}

/// Was «Was der Assistent nicht tut» unter der Karte sagt (Blatt 14), an **einer** Stelle.
public enum Assistentengrenzen {
    public static let titel = "Was der Assistent nicht tut"
    public static let satz = "das Urteil am Bild ändern, eine Prüfung überspringen, etwas "
        + "ohne «Anwenden» rechnen."
}

// ================================================================== der Zustand der Leiste

/// Eine Bitte, wie sie hinausgeht: die neue Nachricht und der Verlauf **davor** — seit Stufe 5
/// dazu die Werkzeugliste der Knotenansicht und die schon ausgefuehrten Schritte dieser Frage.
public struct Assistentenbitte: Equatable, Sendable {
    public let nachricht: String
    public let verlauf: [Gespraechsbeitrag]
    /// Leer: die drei Vorschlagswerkzeuge von frueher (Knotenansicht nicht offen).
    public let werkzeuge: [Mcpwerkzeug]
    public let schritte: [Assistentenschritt]

    public init(nachricht: String, verlauf: [Gespraechsbeitrag], werkzeuge: [Mcpwerkzeug] = [],
                schritte: [Assistentenschritt] = []) {
        self.nachricht = nachricht
        self.verlauf = verlauf
        self.werkzeuge = werkzeuge
        self.schritte = schritte
    }
}

/// Der Zustand der Seitenleiste — ohne Netz und ohne Ansicht, damit er geprüft werden kann.
///
/// Eine Regel trägt ihn: **Es liegt höchstens eine Karte da, und solange eine Anfrage
/// unterwegs ist, geht keine zweite hinaus.** Zwei «Anwenden» hintereinander hiessen zwei
/// Läufe; der zweite bekäme drüben «Es läuft schon einer» — besser, er entsteht gar nicht.
///
/// Und eine zweite (Durchsicht 01.10.2026, M2): **In den Verlauf kommt nur, was der Server
/// angenommen hat.** Hing eine Nachricht schon vor der Antwort darin, blieb eine abgewiesene
/// (zu lang, Heim-PC weg) für immer stehen — und weil der Server jeden Verlaufsbeitrag über
/// seiner Grenze abweist, scheiterte danach jede weitere Frage, bis die Leiste neu entstand.
public struct Assistentengespraech: Equatable, Sendable {
    /// So viele Beiträge gehen höchstens als Verlauf mit — **Abschrift** von
    /// `VERLAUF_HOECHSTENS` in `src/aiimaging/assistent.py`, bewacht in
    /// `tests/test_ipad_geruest.py`.
    public static let verlaufHoechstens = 40
    /// So lang darf eine Nachricht sein, in Zeichen — **Abschrift** von
    /// `NACHRICHT_HOECHSTENS`. Gezählt wie Python zählt: Unicode-Zeichen
    /// (`unicodeScalars`), nicht Swifts zusammengesetzte Zeichen — ein Emoji mit Hautton ist
    /// für Python zwei.
    public static let nachrichtHoechstens = 2000
    /// So lang darf ein Beitrag im Verlauf sein — **Abschrift** von
    /// `VERLAUF_TEXT_HOECHSTENS`. Die eigenen Nachrichten bleiben darunter (sie sind höchstens
    /// `nachrichtHoechstens` lang); eine lange Antwort des Modells nicht.
    public static let verlaufTextHoechstens = 4000

    public private(set) var beitraege: [Gespraechsbeitrag] = []
    /// Stufe 5: die Frage, an der der Assistent gerade mit Werkzeugen arbeitet — `nil`: keine.
    /// Solange sie laeuft, ist `wartet` wahr; ihre Schritte fuehrt die App aus.
    public private(set) var lauf: Assistentenlauf?
    /// Zaehlt die Kennungen der Schritte («A-1», «A-2», …) ueber das ganze Gespraech.
    public private(set) var schrittzahl = 0
    /// Die Nachricht, die gerade unterwegs ist — **noch nicht im Verlauf.** Gezeigt wird sie
    /// trotzdem (`angezeigt`), damit niemand meint, sie sei verloren.
    public private(set) var unterwegs: String?
    public private(set) var vorschlag: Assistentenvorschlag?
    public private(set) var wartet = false
    /// Der letzte Satz, der kein Beitrag ist (ein Fehler, «gestartet»).
    public private(set) var hinweis: String?

    public init() {}

    public var karte: Assistentenkarte? { vorschlag.map(Assistentenkarte.init) }

    /// Was die Leiste zeigt: der Verlauf und, solange sie unterwegs ist, die neue Nachricht.
    public var angezeigt: [Gespraechsbeitrag] {
        beitraege + (unterwegs.map { [Gespraechsbeitrag(von: .mensch, text: $0)] } ?? [])
    }

    /// Wie Python die Länge zählt (`len(str)`): in Unicode-Zeichen.
    public static func laenge(_ text: String) -> Int { text.unicodeScalars.count }

    /// Der Satz, wenn eine Nachricht zu lang ist — **statt** sie zu senden.
    public static func satzZuLang(_ laenge: Int) -> String {
        "Die Nachricht ist länger als \(nachrichtHoechstens) Zeichen (jetzt \(laenge)) — "
            + "bitte kürzen. Gesendet wurde nichts."
    }

    /// Die Nutzerin schickt `text` ab. `nil`, wenn nichts hinausgeht: leer, es wartet schon
    /// eine Anfrage, oder die Nachricht ist zu lang — dann steht der Satz in `hinweis`, und
    /// der Text bleibt im Eingabefeld (die Leiste leert es nur, wenn etwas hinausgeht).
    public mutating func sende(_ text: String, werkzeuge: [Mcpwerkzeug] = []) -> Assistentenbitte? {
        let nachricht = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !nachricht.isEmpty, !wartet else { return nil }
        // VOR DEM SENDEN GEPRUEFT, nicht erst drueben: Der Server weist sie ohnehin ab, und
        // hier kann der Satz sagen, um wie viel zu lang — der Text steht ja noch da.
        let laenge = Self.laenge(nachricht)
        guard laenge <= Self.nachrichtHoechstens else {
            hinweis = Self.satzZuLang(laenge)
            return nil
        }
        let verlauf = Self.alsVerlauf(beitraege)
        unterwegs = nachricht
        // EINE NEUE BITTE ERSETZT DIE ALTE KARTE: Sie stand fuer eine andere Frage.
        vorschlag = nil
        hinweis = nil
        wartet = true
        lauf = werkzeuge.isEmpty ? nil
            : Assistentenlauf(nachricht: nachricht, verlauf: verlauf, werkzeuge: werkzeuge)
        return Assistentenbitte(nachricht: nachricht, verlauf: verlauf, werkzeuge: werkzeuge)
    }

    /// Der Verlauf, wie er hinausgeht: **die letzten `verlaufHoechstens`**, und jeder Beitrag
    /// über `verlaufTextHoechstens` **gekürzt**, mit «…» am Ende.
    ///
    /// Gekürzt, nicht weggelassen: Ohne die lange Antwort stünden zwei Fragen der Nutzerin
    /// hintereinander, und das Modell läse ein Gespräch, das so nicht stattfand. Ihr Anfang
    /// trägt meist das Wesentliche (die Antwort, dann die Begründung). Im Verlauf der Leiste
    /// selbst bleibt sie ganz — gekürzt wird nur, was hinausgeht.
    public static func alsVerlauf(_ beitraege: [Gespraechsbeitrag]) -> [Gespraechsbeitrag] {
        beitraege.suffix(verlaufHoechstens).map { b in
            guard laenge(b.text) > verlaufTextHoechstens else { return b }
            let kopf = b.text.unicodeScalars.prefix(verlaufTextHoechstens - 1)
            return Gespraechsbeitrag(von: b.von,
                                     text: String(String.UnicodeScalarView(kopf)) + "…")
        }
    }

    /// Der Server hat geantwortet: **jetzt erst** kommen Frage und Antwort in den Verlauf — ausser
    /// er nennt noch Werkzeugschritte (Stufe 5): dann bleibt die Frage unterwegs, der Zwischensatz
    /// steht im Hinweis, und die App holt die Schritte mit `naechsterSchritt`.
    public mutating func empfange(_ antwort: Assistentenantwort) {
        if var l = lauf, !antwort.schritte.isEmpty {
            l.offen = antwort.schritte
            lauf = l
            let satz = antwort.antwort.trimmingCharacters(in: .whitespacesAndNewlines)
            hinweis = satz.isEmpty ? nil : satz
            return
        }
        lauf = nil
        if let frage = unterwegs {
            beitraege.append(Gespraechsbeitrag(von: .mensch, text: frage))
        }
        unterwegs = nil
        beitraege.append(Gespraechsbeitrag(von: .assistent, text: antwort.antwort))
        vorschlag = antwort.vorschlag
        wartet = false
    }

    /// Eine Anfrage scheiterte; der Satz wird gezeigt. Eine liegende Karte bleibt liegen.
    ///
    /// Gibt die Nachricht zurück, die unterwegs war (`nil` beim Anwenden): Sie kommt **nicht**
    /// in den Verlauf, und die Leiste legt sie zurück ins Eingabefeld, damit sie nicht
    /// verloren ist.
    @discardableResult
    public mutating func scheitert(_ satz: String) -> String? {
        lauf = nil
        let zurueck = unterwegs
        unterwegs = nil
        hinweis = satz
        wartet = false
        return zurueck
    }

    /// Der naechste Schritt, den die App ausfuehrt, mit seiner Kennung — `nil`, wenn keiner offen
    /// ist (dann geht mit `schrittErledigt` die naechste Bitte hinaus oder die Frage ist fertig).
    public mutating func naechsterSchritt() -> (kennung: String, aufruf: Assistentenaufruf)? {
        guard let l = lauf, let aufruf = l.offen.first else { return nil }
        schrittzahl += 1
        return (Assistentenschrittergebnis.kennungVorsatz + String(schrittzahl), aufruf)
    }

    /// Ein Schritt ist ausgefuehrt. Sind alle offenen erledigt, kommt die naechste Bitte zurueck —
    /// dieselbe Nachricht, derselbe Verlauf, dazu alle Schritte dieser Frage. Wie viele Schritte
    /// eine Frage machen darf, sagt der Heim-PC (`SCHRITTE_HOECHSTENS`), nicht die App.
    public mutating func schrittErledigt(_ ergebnis: String) -> Assistentenbitte? {
        guard var l = lauf, !l.offen.isEmpty else { return nil }
        l.getan.append(Assistentenschritt(aufruf: l.offen.removeFirst(), ergebnis: ergebnis))
        lauf = l
        guard l.offen.isEmpty else { return nil }
        return Assistentenbitte(nachricht: l.nachricht, verlauf: l.verlauf, werkzeuge: l.werkzeuge,
                                schritte: l.getan)
    }

    /// «Ablehnen»: die Karte verwerfen. Gerechnet wird nichts.
    public mutating func lehneAb() {
        guard !wartet else { return }
        vorschlag = nil
    }

    /// «Ändern»: der Text für das Eingabefeld; die Karte verschwindet.
    public mutating func aendere() -> String? {
        guard !wartet, let karte else { return nil }
        vorschlag = nil
        return karte.aenderungstext
    }

    /// «Anwenden» gedrückt: der Vorschlag, der hinausgeht — oder `nil`, wenn keiner liegt
    /// oder schon eine Anfrage unterwegs ist.
    public mutating func beginneAnwenden() -> Assistentenvorschlag? {
        guard !wartet, let vorschlag else { return nil }
        wartet = true
        return vorschlag
    }

    /// Drüben gestartet: Die Karte ist erledigt.
    public mutating func angewendet(_ start: Rechenstart) {
        vorschlag = nil
        wartet = false
        hinweis = "Angewendet — der Heim-PC rechnet."
    }
}

/// Eine Frage, an der der Assistent mit Werkzeugen arbeitet (Stufe 5).
public struct Assistentenlauf: Equatable, Sendable {
    public let nachricht: String
    public let verlauf: [Gespraechsbeitrag]
    public let werkzeuge: [Mcpwerkzeug]
    /// Was die App noch ausfuehren muss, in Reihenfolge.
    public var offen: [Assistentenaufruf] = []
    /// Was schon ausgefuehrt ist, mit Ergebnis.
    public var getan: [Assistentenschritt] = []
}

// ============================================================================ die Anfragen

extension Anfragen {
    /// `GET /api/heim` — die Startzeilen der Mac-App.
    public static func heim(anmeldung: Anmeldung?) -> Anfrage {
        baueLesen(Wege.heim, anmeldung: anmeldung)
    }

    /// `POST /api/assistent` — eine Bitte samt Verlauf. Rechnet nie.
    public static func assistent(_ bitte: Assistentenbitte,
                                 anmeldung: Anmeldung?) throws -> Anfrage {
        var rumpf: [String: JSONWert] = ["nachricht": .text(bitte.nachricht)]
        if !bitte.verlauf.isEmpty {
            rumpf["verlauf"] = .liste(bitte.verlauf.map(\.alsJSON))
        }
        // STUFE 5: die Liste wie Claude sie sieht (Name, Beschreibung, Schema) — die Art bleibt in
        // der App, sie entscheidet ueber Karten, nicht das Modell.
        if !bitte.werkzeuge.isEmpty {
            rumpf["werkzeuge"] = .liste(bitte.werkzeuge.map {
                .objekt(["name": .text($0.name), "description": .text($0.beschreibung),
                         "inputSchema": $0.eingabe])
            })
        }
        if !bitte.schritte.isEmpty {
            rumpf["schritte"] = .liste(bitte.schritte.map(\.alsJSON))
        }
        return try baue(Wege.assistent, rumpf: rumpf, anmeldung: anmeldung)
    }

    /// `POST /api/assistent/anwenden` — antwortet wie `rechne` (`Rechenstart.lies`).
    public static func assistentAnwenden(_ vorschlag: Assistentenvorschlag,
                                         ordner: String? = nil,
                                         anmeldung: Anmeldung?) throws -> Anfrage {
        var rumpf: [String: JSONWert] = ["vorschlag": vorschlag.alsJSON]
        if let o = ordner, !o.isEmpty { rumpf["ordner"] = .text(o) }
        return try baue(Wege.assistentAnwenden, rumpf: rumpf, anmeldung: anmeldung)
    }
}
