import Foundation

// DAS PARKFACH — Skizzen, die (noch) nicht drueben sind.
//
// Owner-Entscheide Nr. 12 und Nr. 28: Ist die HomeStation nicht erreichbar, bleibt die
// Skizze auf dem Geraet und geht von selbst hinaus, sobald sie es wieder ist. Gebaut am
// 22.09.2026 so, dass JEDE Skizze zuerst hier landet und von hier aus gesendet wird: Das
// Parken ist der Weg, nicht die Ausnahme. Eine Skizze, die nur im Speicher auf das Senden
// wartet, ist beim Schliessen der App weg — und niemand merkt es.
//
// Vier Zusagen, jede mit einer Probe in `ParkfachTests`:
//   1. Nach einem Neustart ist das Fach noch da (es liegt in Dateien, nicht im Speicher).
//   2. Eine angekommene Skizze geht NIE ein zweites Mal hinaus.
//   3. Eine abgewiesene bleibt mit ihrem Grund liegen, statt still verworfen zu werden.
//   4. Das Fach waechst nicht ohne Ende: Angekommene gehen nach 7 Tagen, und es bleiben
//      hoechstens 50 davon (Durchsicht vom 22.09.2026 — vorher blieb jede Quittung fuer
//      immer, und der Knopf in der Leiste zeigte dauerhaft «0 geparkt»). Was wartet oder
//      eine Entscheidung braucht, raeumt nichts weg.
//
// Und eine Grenze fuer das Aufraeumen (Durchsicht vom 22.09.2026): Es bringt NIE das Oeffnen
// oder eine Ankunftsmeldung zu Fall. Bis dahin stand es mit `try` — liess sich eine einzige
// alte Quittung nicht loeschen, warf das Oeffnen, das Fach war in der App nicht offen, und
// keine geparkte Skizze konnte mehr warten oder hinaus. In `melde` warf es, nachdem die
// Ankunft schon auf der Platte stand, und die App meldete «liess sich nicht beschreiben».
// Seither steht ein solcher Fehler in `Parkfach.aufraeumFehler`, und die Quittung bleibt
// stehen (`ParkfachTests.testEinNichtLoeschbarerAlterEintragHaeltDasOeffnenNichtAuf`).

/// Wo eine geparkte Skizze steht.
public enum Parkzustand: Equatable, Sendable, Codable {
    /// Wartet auf das Senden.
    case geparkt
    /// Ist gerade unterwegs. Steht **vor** dem Senden auf der Platte — siehe `ungewiss`.
    case unterwegs
    /// Drüben in der Mappe abgelegt (Antwort 200). `skizze` ist der Dateiname drüben.
    case angekommen(skizze: String?, hinweis: String?)
    /// Drüben abgewiesen, mit dem Satz des Servers. Bleibt liegen, bis ein Mensch sie
    /// noch einmal schickt oder verwirft.
    case abgewiesen(grund: String, code: Int?)
    /// **Ob sie angekommen ist, ist nicht bekannt** — die dritte Antwort.
    ///
    /// Die Leitung riss ab, nachdem schon Bytes hinaus waren, oder die App wurde mitten im
    /// Senden beendet. Sie als angekommen zu führen könnte eine Skizze verlieren.
    ///
    /// **Ob sie von selbst noch einmal geht, entscheidet der Schlüssel** (geändert am
    /// 22.09.2026, `Parkeintrag.gehtVonSelbst`). Bis dahin entschied hier immer ein Mensch,
    /// weil ein zweites Senden eine zweite Datei in die Mappe legen konnte. Seit dem
    /// 22.09.2026 kennt der Server einen Schlüssel gegen Doppelsendung (Protokoll §3):
    /// Derselbe Schlüssel mit derselben Zeichnung gibt dieselbe Antwort und **keine**
    /// zweite Datei. Ging der Schlüssel mit, ist das zweite Senden darum die Frage «liegt
    /// sie drüben?» — und die Antwort darauf macht aus «ungewiss» ein Wissen.
    ///
    /// **Die Grenze, und sie steht hier, damit niemand sie für geschlossen hält:** Der
    /// Server merkt sich die Schlüssel nur im Arbeitsspeicher (die letzten 512). Wurde er
    /// zwischen den beiden Sendungen neu gestartet, erkennt er den Schlüssel nicht, und es
    /// entsteht doch eine zweite Datei. Eine doppelte Skizze ist sichtbar und lässt sich
    /// drüben verwerfen; eine verlorene sieht niemand — darum wird nachgeschickt.
    case ungewiss(grund: String)

    /// Das Wort, das ein Mensch sieht.
    public var wort: String {
        switch self {
        case .geparkt: return "geparkt"
        case .unterwegs: return "unterwegs"
        case .angekommen: return "angekommen"
        case .abgewiesen: return "abgewiesen"
        case .ungewiss: return "ungewiss"
        }
    }
}

/// Eine Skizze im Fach.
public struct Parkeintrag: Equatable, Sendable, Codable, Identifiable {
    /// Eindeutig, auf dem Gerät vergeben. **Gegen Doppelsendung:** Jeder Sendeversuch
    /// läuft über `Parkfach.beginneSenden(_:abgebrochen:jetzt:)`, und das gibt denselben Schlüssel nur einmal
    /// frei, solange er unterwegs oder angekommen ist.
    public let schluessel: String
    public let erstellt: Date
    public internal(set) var geaendert: Date
    public internal(set) var zustand: Parkzustand
    /// Wie oft sie schon hinausging.
    public internal(set) var versuche: Int
    /// Warum der letzte Versuch nicht ankam, wenn er zurück ins Fach fiel.
    public internal(set) var letzterGrund: String?
    /// Wie gross die Zeichnung ist (Bytes des PNG).
    public let bytes: Int
    /// Ob der letzte Versuch den Schlüssel gegen Doppelsendung trug: `true`, oder `nil`
    /// — **nicht bekannt**, weil der Eintrag aus einer Fassung vor dem 22.09.2026 stammt,
    /// die ihn noch nicht mitschickte. Nie still `false`.
    ///
    /// Gesetzt am Tor (`Parkfach.beginneSenden`), und das ruft die App erst **nach** dem
    /// Vorspiel der Marke, unmittelbar vor dem Senden. Dass die App dann wirklich über
    /// `Anfragen.skizze(_:png:anmeldung:)` sendet, die ihn mitnimmt, prüft hier keine
    /// Probe — das tut die App-Schicht (`Verbindung/Verbindungsstand.swift`).
    public internal(set) var schluesselGesendet: Bool?
    // Was mit ihr hinausgeht (siehe `Anfragen.skizze`).
    public let ueber: String?
    public let bemerkung: String?
    public let name: String?
    public let ordner: String?

    public var id: String { schluessel }

    /// Ob die Skizze **von selbst** hinausgeht, sobald die HomeStation antwortet:
    ///
    /// * geparkt — ja;
    /// * ungewiss — ja, **wenn der Schlüssel mitging** und sie noch keine
    ///   `Parkfach.selbstHoechstens` Versuche hinter sich hat (siehe `Parkzustand.ungewiss`);
    /// * alles andere — nein.
    ///
    /// Die Grenze der Versuche ist gesetzt, nicht gemessen: Antwortet die HomeStation
    /// jedes Mal unlesbar, soll die Skizze nicht alle zehn Sekunden für immer hinausgehen,
    /// sondern irgendwann einem Menschen vorgelegt werden.
    public var gehtVonSelbst: Bool {
        switch zustand {
        case .geparkt:
            return true
        case .ungewiss:
            return schluesselGesendet == true && versuche < Parkfach.selbstHoechstens
        default:
            return false
        }
    }

    /// Ob ein Mensch entscheiden muss: abgewiesen, oder ungewiss und **nicht** von selbst.
    public var brauchtEntscheid: Bool {
        switch zustand {
        case .abgewiesen: return true
        case .ungewiss: return !gehtVonSelbst
        default: return false
        }
    }
}

/// Was der Knopf zum Parkfach zählt — **jede Skizze in genau einem Fach der Zählung**
/// (angekommene in keinem: sie sind Quittungen).
///
/// Warum getrennt gezählt wird (Durchsicht vom 22.09.2026): Bis dahin stand im Knopf
/// «geparkt» für alles, was von selbst hinausgeht — auch für ungewisse Skizzen, die mit
/// ihrem Schlüssel nochmals gehen. Die sind aber nicht geparkt (so heisst auf dem Blatt
/// «Skizzen» nur, was auf dem iPad wartet, weil die HomeStation nicht erreichbar ist),
/// sondern **ungewiss**: vielleicht schon drüben. Das Wort im Knopf ist jetzt das Wort,
/// das die Liste des Fachs über dieselbe Skizze schreibt (`Parkzustand.wort`), und «offen»
/// für alles, was einen Menschen braucht. `ParkfachTests.testDerKnopfZaehltUngewisseNichtAlsGeparkt`
/// bewacht es.
public struct Fachzaehlung: Equatable, Sendable {
    /// Ein Teil der Anzeige: die Zahl und ihr Wort.
    public struct Teil: Equatable, Sendable {
        public let zahl: Int
        public let wort: String
    }

    /// Wartet auf das Senden und war noch nie ungewiss hinaus (`Parkzustand.geparkt`).
    public let geparkt: Int
    /// Ungewiss, geht aber mit dem Schlüssel von selbst noch einmal.
    public let ungewiss: Int
    public let unterwegs: Int
    /// Braucht eine Entscheidung eines Menschen (`Parkeintrag.brauchtEntscheid`).
    public let offen: Int

    public init(_ eintraege: [Parkeintrag]) {
        var g = 0, u = 0, w = 0, o = 0
        for e in eintraege {
            switch e.zustand {
            case .geparkt: g += 1
            case .unterwegs: w += 1
            case .ungewiss: if e.gehtVonSelbst { u += 1 } else { o += 1 }
            case .abgewiesen: o += 1
            case .angekommen: break
            }
        }
        geparkt = g
        ungewiss = u
        unterwegs = w
        offen = o
    }

    /// Die Teile, die der Knopf zeigt — **nur die, die nicht null sind**, in fester Folge.
    /// Leer heisst: Es liegen nur Quittungen im Fach (oder nichts).
    public var teile: [Teil] {
        [Teil(zahl: geparkt, wort: Parkzustand.geparkt.wort),
         Teil(zahl: ungewiss, wort: Parkzustand.ungewiss(grund: "").wort),
         Teil(zahl: unterwegs, wort: Parkzustand.unterwegs.wort),
         Teil(zahl: offen, wort: "offen")].filter { $0.zahl > 0 }
    }
}

/// Was ein Sendeversuch ergab — aus der Sicht des Fachs.
public enum Sendeergebnis: Equatable, Sendable {
    /// 200 mit `abgelegt: true`.
    case angekommen(skizze: String?, hinweis: String?)
    /// Drüben abgewiesen (400, 404, …). Die Skizze bleibt mit dem Satz liegen.
    case abgewiesen(grund: String, code: Int?)
    /// Die Tür (401/403): nicht die Skizze ist falsch, sondern die Anmeldung. Zurück ins
    /// Fach; sie geht wieder, sobald neu gekoppelt ist.
    case nichtAngemeldet(grund: String)
    /// Kein Byte ist hinaus — sie **kann** nicht angekommen sein. Zurück ins Fach.
    case nichtErreicht(grund: String)
    /// Bytes waren hinaus, eine Antwort kam nicht (oder keine lesbare). Ob sie angekommen
    /// ist, ist nicht bekannt.
    case ohneAntwort(grund: String)

    /// Aus einer Antwort der HomeStation auf `POST /api/skizze`.
    public static func aus(status: Int, daten: Data) -> Sendeergebnis {
        if (200..<300).contains(status) {
            do {
                let q = try Skizzenquittung.lies(status: status, daten: daten)
                return .angekommen(skizze: q.skizze, hinweis: q.hinweis)
            } catch {
                // EIN ERFOLG, DER SICH NICHT LESEN LAESST, IST KEINER — aber auch kein
                // Misserfolg. Die Skizze kann drueben liegen.
                return .ohneAntwort(grund: "Die HomeStation hat geantwortet, aber nicht "
                                    + "lesbar — ob die Skizze abgelegt ist, ist nicht bekannt.")
            }
        }
        let fehler = Serverfehler.aus(status: status, daten: daten)
        if status == 401 || status == 403 {
            return .nichtAngemeldet(grund: fehler.satz)
        }
        return .abgewiesen(grund: fehler.satz, code: status)
    }

    /// Wenn gar keine Antwort kam: **Ob Bytes hinaus waren, entscheidet.** Ohne ein Byte
    /// kann drüben nichts angekommen sein; mit Bytes ist es nicht bekannt.
    public static func ohneVerbindung(grund: String, gesendeteBytes: Int64) -> Sendeergebnis {
        gesendeteBytes > 0 ? .ohneAntwort(grund: grund) : .nichtErreicht(grund: grund)
    }
}

/// Die Warteschlange der Skizzen, **als Dateien in einem Ordner**, den die App übergibt.
///
/// Je Skizze zwei Dateien: `<schluessel>.png` (die Zeichnung) und `<schluessel>.json` (der
/// Eintrag). **Der Eintrag wird zuletzt geschrieben** — er ist die Bestätigung. Bricht die
/// App dazwischen ab, liegt ein PNG ohne Eintrag da; es wird beim nächsten Öffnen als
/// geparkt aufgenommen, nicht übergangen (*eine Zeichnung, die niemand mehr findet, ist
/// verloren, auch wenn ihre Datei noch da ist*).
///
/// Nicht für mehrere Fäden gebaut: Die App benutzt es von einem Ort aus (dem Hauptfaden).
public final class Parkfach {
    /// Wie oft eine **ungewisse** Skizze insgesamt hinausgegangen sein darf, damit sie
    /// noch von selbst geht (`Parkeintrag.gehtVonSelbst`). Gesetzt, nicht gemessen.
    public static let selbstHoechstens = 5
    /// Wie lange eine angekommene Skizze als Quittung im Fach steht (Sekunden: 7 Tage).
    /// Gesetzt, nicht gemessen — lang genug, um nachzusehen, was diese Woche hinausging.
    public static let angekommenHoechstensAlter: TimeInterval = 7 * 24 * 3600
    /// Wie viele angekommene höchstens stehen bleiben; die ältesten gehen zuerst.
    public static let angekommenHoechstens = 50

    public let ordner: URL
    /// Alle Einträge, die ältesten zuerst.
    public private(set) var eintraege: [Parkeintrag] = []
    /// Dateien, die wie Einträge aussehen und sich nicht lesen liessen. **Gemeldet, nicht
    /// übergangen** — und nicht gelöscht.
    public private(set) var unlesbar: [String] = []
    /// Warum sich beim letzten Aufräumen eine alte Quittung nicht löschen liess — `nil`,
    /// wenn das letzte Aufräumen alles weggenommen hat, was gehen sollte.
    ///
    /// **Getrennt geführt, nicht geworfen** (Durchsicht vom 22.09.2026): Eine Quittung, die
    /// stehen bleibt, schadet niemandem; ein Fach, das deswegen nicht aufgeht, hält jede
    /// wartende Skizze fest.
    public private(set) var aufraeumFehler: String?

    /// Wie eine Datei gelöscht wird. Nur für Proben anders als die Vorgabe: Eine Datei, die
    /// sich nicht löschen lässt, gibt es unter Linux als Verwalter nicht (Schreibschutz
    /// wirkt dort nicht), und ein nicht leerer Ordner an ihrer Stelle wird mitgelöscht.
    private let loesche: (URL) throws -> Void

    /// Öffnet (oder legt an) das Fach in `ordner` und liest, was darin liegt.
    ///
    /// Was beim letzten Schliessen **unterwegs** war, wird `ungewiss`: Die App wurde mitten
    /// im Senden beendet, und ob die Skizze drüben liegt, weiss hier niemand.
    ///
    /// `loesche` bleibt in der App bei der Vorgabe; eine Probe setzt es, um ein Löschen
    /// scheitern zu lassen (siehe `aufraeumFehler`).
    public init(ordner: URL, jetzt: Date = Date(),
                loesche: @escaping (URL) throws -> Void = {
                    try FileManager.default.removeItem(at: $0)
                }) throws {
        self.ordner = ordner
        self.loesche = loesche
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
        try lade(jetzt: jetzt)
    }

    // ---------------------------------------------------------------------- lesen

    /// Die nächste Skizze, die hinaus soll: die älteste, die **von selbst** geht
    /// (`Parkeintrag.gehtVonSelbst` — geparkt, oder ungewiss mit Schlüssel).
    public var naechster: Parkeintrag? {
        eintraege.first { $0.gehtVonSelbst }
    }

    /// Wie viele von selbst hinausgehen: geparkte **und** ungewisse mit Schlüssel. Für den
    /// Knopf nicht als eine Zahl gedacht — dort zählt `Fachzaehlung` beide getrennt.
    public var wartend: Int { eintraege.filter { $0.gehtVonSelbst }.count }

    /// Wie viele eine Entscheidung eines Menschen brauchen.
    public var brauchenEntscheid: Int { eintraege.filter { $0.brauchtEntscheid }.count }

    public func eintrag(_ schluessel: String) -> Parkeintrag? {
        eintraege.first { $0.schluessel == schluessel }
    }

    /// Die Zeichnung. `nil` nach der Ankunft — dann liegt sie drüben in der Mappe, und
    /// hier gibt es nichts mehr, das ein zweites Mal hinausgehen könnte.
    public func png(_ schluessel: String) -> Data? {
        try? Data(contentsOf: pngDatei(schluessel))
    }

    // ------------------------------------------------------------------- schreiben

    /// Legt eine Skizze ins Fach.
    @discardableResult
    public func parke(png: Data, ueber: String? = nil, bemerkung: String? = nil,
                      name: String? = nil, ordner zielordner: String? = nil,
                      jetzt: Date = Date()) throws -> Parkeintrag {
        let schluessel = UUID().uuidString
        let e = Parkeintrag(schluessel: schluessel, erstellt: jetzt, geaendert: jetzt,
                            zustand: .geparkt, versuche: 0, letzterGrund: nil,
                            bytes: png.count, schluesselGesendet: nil, ueber: ueber,
                            bemerkung: bemerkung, name: name, ordner: zielordner)
        try png.write(to: pngDatei(schluessel), options: .atomic)
        try schreibe(e)
        eintraege.append(e)
        sortiere()
        return e
    }

    /// Legt die Bilder eines Ablageplans ins Fach (`Ablageplan.parke`) — **jedes mit
    /// derselben Unterlage** und unter dem Namen seines Teils. Der Weg, den «In die Mappe
    /// legen» nimmt (`Verbindungsstand.legeInDieMappe`), seit dem 23.09.2026: Bis dahin
    /// parkte die App jede Skizze ohne `ueber`, und der Server rechnete sie auf Grau.
    ///
    /// Die Unterlage steht im Eintrag auf der Platte und **überlebt den Neustart der App**
    /// (`BlattunterlageTests.testDieUnterlageGehtDurchFachUndNeustartBisInDieAnfrage`).
    /// Scheitert ein Bild, ist, was davor lag, schon geparkt — und geht auch hinaus.
    @discardableResult
    public func parke(_ bilder: [Ebenenausgabe.Bild], ueber: String?,
                      ordner zielordner: String?, jetzt: Date = Date()) throws -> [Parkeintrag] {
        var gelegt: [Parkeintrag] = []
        for bild in bilder {
            gelegt.append(try parke(png: bild.png, ueber: ueber, name: bild.name,
                                    ordner: zielordner, jetzt: jetzt))
        }
        return gelegt
    }

    /// **Das Tor gegen Doppelsendung.** Gibt eine Skizze zum Senden frei — nur, wenn sie
    /// von selbst geht (`Parkeintrag.gehtVonSelbst`) — und hält `unterwegs` auf der Platte
    /// fest, **bevor** gesendet wird.
    ///
    /// `nil` heisst: nicht senden. Eine Skizze, die unterwegs, angekommen oder abgewiesen
    /// ist, kommt hier nicht noch einmal durch; eine ungewisse nur mit Schlüssel.
    ///
    /// **Das Tor ist der letzte Schritt vor dem ersten Byte** (Durchsicht vom 22.09.2026).
    /// Bis dahin rief die App es vor dem Vorspiel der Marke (0,4 s): `unterwegs`, ein
    /// Versuch mehr und «Schlüssel ging mit» standen dann schon auf der Platte, und ein
    /// Abbruch im Vorspiel wurde verschluckt — gesendet wurde trotzdem. Jetzt spielt die
    /// App das Vorspiel zuerst und fragt dann hier, mit `abgebrochen`: Ist das Senden
    /// inzwischen abgebrochen, gibt das Tor nichts frei und **schreibt nichts** — die
    /// Skizze steht, wie sie vorher stand (`ParkfachTests.testEinAbbruchVorDemTorLaesstDenEintragUnberuehrt`).
    /// Dass die App es wirklich nach dem Vorspiel ruft, prüft hier keine Probe.
    public func beginneSenden(_ schluessel: String, abgebrochen: Bool,
                              jetzt: Date = Date()) throws -> Parkeintrag? {
        guard !abgebrochen else { return nil }
        guard var e = eintrag(schluessel), e.gehtVonSelbst else { return nil }
        guard FileManager.default.fileExists(atPath: pngDatei(schluessel).path) else {
            e.zustand = .abgewiesen(grund: "Die Zeichnung fehlt im Fach — es gibt nichts "
                                    + "zu senden.", code: nil)
            e.geaendert = jetzt
            try ersetze(e)
            return nil
        }
        e.zustand = .unterwegs
        e.versuche += 1
        e.schluesselGesendet = true
        e.geaendert = jetzt
        try ersetze(e)
        return e
    }

    /// Was aus dem Versuch wurde. Nur eine Skizze, die **unterwegs** ist, nimmt eine
    /// Meldung an — eine zweite Meldung für dieselbe Sendung ändert nichts (`false`).
    @discardableResult
    public func melde(_ schluessel: String, _ ergebnis: Sendeergebnis,
                      jetzt: Date = Date()) throws -> Bool {
        guard var e = eintrag(schluessel), e.zustand == .unterwegs else { return false }
        e.geaendert = jetzt
        switch ergebnis {
        case .angekommen(let skizze, let hinweis):
            e.zustand = .angekommen(skizze: skizze, hinweis: hinweis)
            e.letzterGrund = nil
        case .abgewiesen(let grund, let code):
            e.zustand = .abgewiesen(grund: grund, code: code)
        case .nichtAngemeldet(let grund), .nichtErreicht(let grund):
            e.zustand = .geparkt
            e.letzterGrund = grund
        case .ohneAntwort(let grund):
            e.zustand = .ungewiss(grund: grund)
        }
        try ersetze(e)
        if case .angekommen = e.zustand {
            // ERST DER EINTRAG, DANN DIE ZEICHNUNG WEG. Andersherum laege nach einem
            // Absturz dazwischen ein Eintrag «unterwegs» ohne Zeichnung da.
            try? FileManager.default.removeItem(at: pngDatei(schluessel))
            // DAS AUFRAEUMEN WIRFT NICHT: Die Ankunft steht schon auf der Platte, und ein
            // Fehler hier ist keiner der Meldung (siehe `aufraeumFehler`).
            raeumeAuf(jetzt: jetzt)
        }
        return true
    }

    /// Nimmt **angekommene** Skizzen aus dem Fach: die älter als
    /// `angekommenHoechstensAlter`, und von den übrigen alle über `angekommenHoechstens`
    /// (die ältesten zuerst). Gibt zurück, wie viele gingen.
    ///
    /// Nur angekommene: Ihre Zeichnung liegt drüben in der Mappe, hier steht nur noch die
    /// Quittung. Geparkte, ungewisse und abgewiesene bleiben, wie alt sie auch sind — sie
    /// warten auf das Senden oder auf einen Menschen.
    ///
    /// Gerufen beim Öffnen und nach jeder Ankunft; von aussen nur für Proben nötig.
    ///
    /// **Wirft nicht.** Lässt sich eine Quittung nicht löschen, bleibt sie im Fach stehen
    /// (auf der Platte und hier), der Grund steht in `aufraeumFehler`, und die übrigen
    /// gehen trotzdem. Das nächste Aufräumen versucht es wieder.
    @discardableResult
    public func raeumeAuf(jetzt: Date = Date()) -> Int {
        let angekommen = eintraege.filter {
            if case .angekommen = $0.zustand { return true }
            return false
        }.sorted { ($0.geaendert, $0.schluessel) > ($1.geaendert, $1.schluessel) }
        var weg: [Parkeintrag] = []
        for (i, e) in angekommen.enumerated()
        where i >= Parkfach.angekommenHoechstens
            || jetzt.timeIntervalSince(e.geaendert) > Parkfach.angekommenHoechstensAlter {
            weg.append(e)
        }
        var gegangen = 0
        var fehler: [String] = []
        for e in weg {
            try? FileManager.default.removeItem(at: pngDatei(e.schluessel))
            do {
                try loesche(eintragsDatei(e.schluessel))
            } catch {
                // SCHON WEG IST WEG: Hat jemand die Datei inzwischen entfernt, ist erreicht,
                // was das Aufraeumen wollte. Nur was noch DA ist, ist ein Fehler.
                if FileManager.default.fileExists(atPath: eintragsDatei(e.schluessel).path) {
                    fehler.append("\(e.schluessel).json (\(error.localizedDescription))")
                    continue
                }
            }
            eintraege.removeAll { $0.schluessel == e.schluessel }
            gegangen += 1
        }
        aufraeumFehler = fehler.isEmpty ? nil
            : "\(fehler.count) alte Quittung(en) liessen sich nicht löschen und bleiben "
                + "stehen: " + fehler.joined(separator: ", ")
        return gegangen
    }

    /// Eine abgewiesene oder ungewisse Skizze **auf Wunsch eines Menschen** wieder ins
    /// Fach legen. Angekommene, geparkte und unterwegs befindliche nicht.
    @discardableResult
    public func nochEinmal(_ schluessel: String, jetzt: Date = Date()) throws -> Bool {
        guard var e = eintrag(schluessel) else { return false }
        switch e.zustand {
        case .abgewiesen(let grund, _), .ungewiss(let grund):
            e.zustand = .geparkt
            e.letzterGrund = grund
            e.geaendert = jetzt
            try ersetze(e)
            return true
        default:
            return false
        }
    }

    /// Nimmt eine Skizze aus dem Fach — **nur auf Wunsch eines Menschen**, und nie, solange
    /// sie unterwegs ist.
    @discardableResult
    public func verwirf(_ schluessel: String) throws -> Bool {
        guard let e = eintrag(schluessel), e.zustand != .unterwegs else { return false }
        // ERST DIE ZEICHNUNG, DANN DER EINTRAG. Andersherum naehme ein Absturz dazwischen
        // die Zeichnung beim naechsten Oeffnen als verwaist wieder auf.
        try? FileManager.default.removeItem(at: pngDatei(schluessel))
        try FileManager.default.removeItem(at: eintragsDatei(schluessel))
        eintraege.removeAll { $0.schluessel == schluessel }
        return true
    }

    // ------------------------------------------------------------------- Handgriffe

    private func pngDatei(_ s: String) -> URL { ordner.appendingPathComponent(s + ".png") }
    private func eintragsDatei(_ s: String) -> URL { ordner.appendingPathComponent(s + ".json") }

    private func schreibe(_ e: Parkeintrag) throws {
        let schreiber = JSONEncoder()
        schreiber.outputFormatting = [.sortedKeys]
        try schreiber.encode(e).write(to: eintragsDatei(e.schluessel), options: .atomic)
    }

    private func ersetze(_ e: Parkeintrag) throws {
        try schreibe(e)
        if let i = eintraege.firstIndex(where: { $0.schluessel == e.schluessel }) {
            eintraege[i] = e
        }
    }

    private func sortiere() {
        eintraege.sort { ($0.erstellt, $0.schluessel) < ($1.erstellt, $1.schluessel) }
    }

    private func lade(jetzt: Date) throws {
        let dateien = try FileManager.default.contentsOfDirectory(
            at: ordner, includingPropertiesForKeys: nil)
        var gelesen: [Parkeintrag] = []
        var mitEintrag = Set<String>()
        var fehlerhaft: [String] = []
        let leser = JSONDecoder()

        for datei in dateien where datei.pathExtension == "json" {
            let stamm = datei.deletingPathExtension().lastPathComponent
            guard UUID(uuidString: stamm) != nil else { continue }
            guard let daten = try? Data(contentsOf: datei),
                  var e = try? leser.decode(Parkeintrag.self, from: daten),
                  e.schluessel == stamm else {
                fehlerhaft.append(datei.lastPathComponent)
                // DIE ZEICHNUNG DAZU WIRD NICHT ALS VERWAIST AUFGENOMMEN — sie hat einen
                // Eintrag, nur einen unlesbaren. Beides bleibt liegen, wie es ist.
                mitEintrag.insert(stamm)
                continue
            }
            mitEintrag.insert(stamm)
            if e.zustand == .unterwegs {
                e.zustand = .ungewiss(grund: "Das Senden wurde unterbrochen (die App wurde "
                                      + "beendet). Ob die Skizze angekommen ist, ist nicht bekannt.")
                e.geaendert = jetzt
                try schreibe(e)
            }
            if case .angekommen = e.zustand {
                try? FileManager.default.removeItem(at: pngDatei(stamm))
            }
            gelesen.append(e)
        }

        // VERWAISTE ZEICHNUNGEN: ein PNG ohne Eintrag. Die App wurde zwischen dem Schreiben
        // der Zeichnung und dem des Eintrags beendet. Aufgenommen, nicht uebergangen.
        for datei in dateien where datei.pathExtension == "png" {
            let stamm = datei.deletingPathExtension().lastPathComponent
            guard UUID(uuidString: stamm) != nil, !mitEintrag.contains(stamm),
                  let daten = try? Data(contentsOf: datei) else { continue }
            let zeit = (try? FileManager.default.attributesOfItem(atPath: datei.path))?[
                .modificationDate] as? Date ?? jetzt
            let e = Parkeintrag(schluessel: stamm, erstellt: zeit, geaendert: jetzt,
                                zustand: .geparkt, versuche: 0,
                                letzterGrund: "Nach einem Abbruch wieder aufgenommen.",
                                bytes: daten.count, schluesselGesendet: nil, ueber: nil,
                                bemerkung: nil, name: nil, ordner: nil)
            try schreibe(e)
            gelesen.append(e)
        }

        eintraege = gelesen
        unlesbar = fehlerhaft.sorted()
        sortiere()
        // DAS AUFRAEUMEN WIRFT NICHT: Eine alte Quittung, die stehen bleibt, darf das Fach
        // nicht verschliessen (siehe `aufraeumFehler`).
        raeumeAuf(jetzt: jetzt)
    }
}

// ============================================================ die Übergabe als Bewegung

/// Wo die Marke der Übergabe steht — **die vier Bewegungsregeln als Rechnung** (Entwurf
/// «Ein Faden, zwei Geräte», Entscheide vom 21.09.2026):
///
/// 1. *Bewegt sich etwas, ist etwas unterwegs.* Der Ort ändert sich nur mit gezählten Bytes.
/// 2. *Gleichmässig heisst gezählt.* Ohne Zählung fliegt die Marke nicht, sie **atmet**.
/// 3. *Die Animation endet nicht vor der Ankunft.* Vor der Antwort 200 bleibt die Marke
///    vor dem Ziel stehen (`haltepunkt`); am Ziel ist sie erst `eingerastet`.
/// 4. *Ein Gegenstand, ein Weg.* Das ist Sache der Ansicht: **eine** Marke, die ihren Ort
///    ändert — nie eine zweite, die am Ziel erscheint.
///
/// Die Ansicht (`Verbindung/Uebergabe.swift`) zeichnet nur, was hier steht.
public enum Flugbahn {
    public enum Phase: Equatable, Sendable {
        /// Die Skizze schrumpft auf die Marke (am iPad).
        case ablegen
        /// Die Marke wandert an den Rand, an dem der Rechner sitzt (Blatt «Verbindung»,
        /// Augenblick 2) — noch am iPad, aber schon in der Richtung des Ziels: `Flugbahn.rand`.
        case abheben
        /// Bytes gehen hinaus. `gesamt` `nil` oder 0: **nicht gezählt.**
        case flug(gesendet: Int64, gesamt: Int64?)
        /// Alles ist hinaus, die Antwort steht aus.
        case warten
        /// Drüben bestätigt (200).
        case eingerastet
        /// Abgebrochen: die Marke fällt zurück aufs iPad.
        case zurueck
    }

    /// Wie weit die Marke vor der Bestätigung höchstens kommt (Anteil des Wegs).
    public static let haltepunkt = 0.92

    /// Wo der Rand des iPads auf dem Faden liegt (Anteil des Wegs): dorthin hebt die Marke
    /// ab, und dort beginnt der Flug.
    ///
    /// Das Blatt «Verbindung» sagt zum Abheben: *«Die Marke wandert an den Rand, an dem der
    /// Rechner sitzt. Die Richtung ist die Richtung.»* Bis zur Durchsicht vom 22.09.2026
    /// gab `ort(.abheben)` 0 wie das Ablegen — die Marke stand still, wo das Blatt eine
    /// Bewegung zum Ziel hin zeigt. Der Wert selbst ist gesetzt, nicht gemessen: eine
    /// sichtbare Strecke, klein genug, dass niemand sie für Übertragung hält.
    /// `ParkfachTests.testBeimAbhebenWandertDieMarkeAnDenRandZumZiel` bewacht die Richtung.
    public static let rand = 0.08

    // Die Zeiten des Entwurfs, in Sekunden.
    public static let ablegen = 0.22
    public static let abheben = 0.18
    public static let einrasten = 0.14
    public static let atem = 1.8

    /// **Was vor dem ersten Byte geschieht**, je Phase mit ihrer Dauer: erst ablegen, dann
    /// abheben. Die App spielt es ab und beginnt **danach** mit dem Senden
    /// (`flugbeginn`).
    ///
    /// Warum es als Liste im Kern steht (Durchsicht vom 22.09.2026): Bis dahin setzte die
    /// App `.abheben` nie, und auf `.ablegen` folgte der Flug erst mit dem ersten
    /// Zählerstand. Kam keiner — ein kleines PNG geht oft in einem Stück, ohne Meldung —,
    /// blieb die Marke vergrössert in `.ablegen` stehen, bis die Antwort kam, und atmete
    /// nicht (Regel 2). `ParkfachTests.testVorDemErstenByteLegtDieMarkeAbUndHebtAb` bewacht
    /// die Reihenfolge, `testDerFlugBeginntUngezaehltUndAtmet` den Beginn.
    public static let vorspiel: [(phase: Phase, dauer: Double)] = [
        (.ablegen, ablegen),
        (.abheben, abheben),
    ]

    /// Die Phase, mit der das Senden beginnt: **unterwegs, nicht gezählt** — die Marke
    /// atmet am Rand, bis ein Zählerstand mit Gesamt kommt.
    public static let flugbeginn = Phase.flug(gesendet: 0, gesamt: nil)

    /// Ein Zählerstand vom Senden, angewandt auf die Phase — `nil` heisst: **er ändert
    /// nichts** (die Marke ist nicht im Flug: sie legt noch ab, wartet schon, ist
    /// eingerastet oder zurückgefallen).
    ///
    /// Sind alle Bytes hinaus, wird gewartet — **nicht** eingerastet: Das tut erst die
    /// Antwort (Regel 3).
    public static func gezaehlt(_ phase: Phase, gesendet: Int64, gesamt: Int64?) -> Phase? {
        guard case .flug = phase else { return nil }
        if let g = gesamt, g > 0, gesendet >= g { return .warten }
        return .flug(gesendet: gesendet, gesamt: gesamt)
    }

    /// Wo die Marke **bei Bewegungsreduktion** steht — `nil` heisst: **nicht gezeigt.**
    ///
    /// Das Blatt «Ein Faden, zwei Geräte»: *«Wer am Gerät Bewegung abgestellt hat, bekommt
    /// denselben Weg ohne Bewegung: Die Marke erscheint am Ziel, der Balken bleibt.»* Die
    /// Marke erscheint darum erst mit der Bestätigung, und dann dort (1). Fällt sie
    /// zurück, liegt sie auf dem iPad (0) — das sagt auch der Satz darunter. Dazwischen
    /// steht sie nirgends: Am iPad sähe sie aus wie «nicht losgegangen», auf dem Faden wie
    /// eine Bewegung in Sprüngen. Was unterwegs geschieht, sagen Balken und Satz.
    ///
    /// Bis zur Durchsicht vom 22.09.2026 stand sie in dieser Lage während der ganzen
    /// Übertragung am iPad — gegen das Blatt.
    public static func ortOhneBewegung(_ phase: Phase) -> Double? {
        switch phase {
        case .eingerastet: return 1
        case .zurueck: return 0
        default: return nil
        }
    }

    /// Der Anteil der gezählten Bytes — `nil`, wenn nicht gezählt.
    public static func anteil(_ phase: Phase) -> Double? {
        guard case .flug(let gesendet, let gesamt) = phase, let g = gesamt, g > 0 else {
            return nil
        }
        return min(max(Double(gesendet) / Double(g), 0), 1)
    }

    /// Der Ort der Marke: 0 am iPad, `rand` am Rand des iPads, 1 am Ziel.
    public static func ort(_ phase: Phase) -> Double {
        switch phase {
        case .ablegen, .zurueck:
            return 0
        case .abheben:
            return rand
        case .flug:
            // NICHT GEZAEHLT HEISST: DIE MARKE BLEIBT, WO SIE IST — am Rand des iPads. Gezaehlt
            // geht sie vom Rand bis zum Haltepunkt, nie zurueck hinter den Rand.
            return rand + (anteil(phase) ?? 0) * (haltepunkt - rand)
        case .warten:
            return haltepunkt
        case .eingerastet:
            return 1
        }
    }

    /// Ob die Marke an Ort und Stelle atmet statt zu fliegen: wenn gewartet wird, und
    /// wenn Bytes gehen, die niemand zählt.
    public static func atmet(_ phase: Phase) -> Bool {
        switch phase {
        case .warten: return true
        case .flug: return anteil(phase) == nil
        default: return false
        }
    }
}
