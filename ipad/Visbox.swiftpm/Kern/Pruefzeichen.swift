import Foundation

/// Wie ein Bild gelesen wird — **der Schalter am Bild** (Entscheide 15 und 30).
///
/// *Prüfen:* Erfundenes Volumen ist ein Fehler, das Bild trägt sein Urteil.
/// *Entwerfen:* Erfundenes Volumen ist der Zweck; es wird kein Urteil gesprochen, und das
/// Zeichen ist blau — eine Farbe, die in den drei Antworten nicht vorkommt.
public enum Bildlesart: String, CaseIterable, Sendable {
    case pruefen
    case entwerfen
}

/// Ein Farbton als drei Bytes — **ohne SwiftUI**, damit die Abbildung Urteil → Farbe hier
/// im Kern liegt und unter Linux geprüft werden kann. Die App macht daraus eine `Color`.
public struct Farbton: Equatable, Hashable, Sendable {
    public let rot: UInt8
    public let gruen: UInt8
    public let blau: UInt8

    public init(rot: UInt8, gruen: UInt8, blau: UInt8) {
        self.rot = rot
        self.gruen = gruen
        self.blau = blau
    }

    /// Aus sechs Hex-Ziffern, wie sie im Blatt «Die Zeichen» stehen (`"4ea373"`).
    ///
    /// Die Werte stehen fest im Quelltext; eine falsch geschriebene Ziffer ist ein
    /// Schreibfehler hier und keine Eingabe von aussen. Darum hält die Probe
    /// `testJedeFarbeIstLesbarGeschrieben` jeden Ton fest, statt dass hier geraten wird.
    public init(hex: String) {
        let ziffern = hex.hasPrefix("#") ? String(hex.dropFirst()) : hex
        let wert = UInt32(ziffern, radix: 16) ?? 0
        self.init(rot: UInt8((wert >> 16) & 0xff),
                  gruen: UInt8((wert >> 8) & 0xff),
                  blau: UInt8(wert & 0xff))
    }

    /// `#rrggbb`, klein geschrieben.
    public var hex: String {
        String(format: "#%02x%02x%02x", rot, gruen, blau)
    }

    /// Dieser Ton, zu `deckung` über `grund` gelegt.
    public func ueber(_ grund: Farbton, deckung: Double) -> Farbton {
        func misch(_ a: UInt8, _ b: UInt8) -> UInt8 {
            UInt8((Double(a) * deckung + Double(b) * (1 - deckung)).rounded())
        }
        return Farbton(rot: misch(rot, grund.rot), gruen: misch(gruen, grund.gruen),
                       blau: misch(blau, grund.blau))
    }

    /// Die relative Helligkeit nach WCAG 2.
    public var helligkeit: Double {
        func kanal(_ k: UInt8) -> Double {
            let c = Double(k) / 255
            return c <= 0.03928 ? c / 12.92 : pow((c + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * kanal(rot) + 0.7152 * kanal(gruen) + 0.0722 * kanal(blau)
    }

    /// Das Kontrastverhältnis zweier Töne nach WCAG 2 (1 bis 21).
    public static func kontrast(_ a: Farbton, _ b: Farbton) -> Double {
        let (h, d) = (max(a.helligkeit, b.helligkeit), min(a.helligkeit, b.helligkeit))
        return (h + 0.05) / (d + 0.05)
    }
}

/// Welche Art Zeichen ein Bild trägt — **fünf Arten, vier Farben.**
///
/// Die drei Antworten des Projekts, dazu der Entwurf (blau, spricht kein Urteil) und ein
/// Zeichen, das diese App nicht kennt. *Dieselbe Farbe darf nie zwei Dinge heissen*
/// (Blatt «Die Zeichen», 21.09.2026): Die vier Aussagen tragen vier Farben. Das unbekannte
/// Zeichen trägt die Farbe von «nicht gemessen», weil es **dasselbe heisst** — kein Urteil —,
/// und unterscheidet sich durch sein Wort (22.09.2026, siehe `rand`).
/// `testKeineFarbeHeisstZweiDinge` hält beides fest.
public enum Zeichenart: String, CaseIterable, Sendable {
    case bestanden
    case durchgefallen
    case nichtGemessen
    case entwurf
    /// Ein Zeichen vom Server, das diese App nicht kennt (ein neuerer Server).
    ///
    /// **Nicht «nicht gemessen».** Dasselbe wie in `Urteil(zeichen:)`: geraten sieht in
    /// der Anzeige genauso aus wie gewusst. Und auch nicht *kein* Zeichen — *kein Zeichen
    /// sieht aus wie kein Problem.*
    case unbekannt

    /// Der Rand um das Bild. Er trägt die Aussage über die Distanz.
    public var rand: Farbton {
        switch self {
        case .bestanden: return Farbton(hex: "4ea373")
        case .durchgefallen: return Farbton(hex: "e2776f")
        case .nichtGemessen: return Farbton(hex: "c8a53f")
        case .entwurf: return Farbton(hex: "6fb3d2")
        // DAS GELB VON «NICHT GEMESSEN», UNTERSCHIEDEN DURCH DAS WORT (Durchsicht der
        // Verdrahtung, 22.09.2026). Zuerst trug «Zeichen unbekannt» #9aa2ae, das Leise jeder
        // Beschriftung (Durchsicht B) — ein unbekanntes Zeichen sah aus wie ein Satz ohne
        // Belang. Ein danach gesetzter eigener Ton stand auf keinem Blatt; *Oberfläche wird
        // gezeichnet, bevor sie gebaut wird.* Das Blatt «Die Zeichen» kennt für «nicht gemessen
        // / kein Urteil vorhanden» genau einen Ton, gestrichelt — und ein Zeichen, das die App
        // nicht lesen kann, ist für sie keines. (Auch das Blau des Entwurfs spricht kein
        // Urteil, aber aus Absicht: gerechnet, nur nicht geprüft. Ein unlesbares Zeichen sagt
        // das nicht.) Ein eigener Ton kommt erst mit einem Eintrag auf dem Blatt und dem
        // Entscheid des Owners. Bewacht: `testJederFarbtonStehtSoAufDemBlatt` (jede Art,
        // gegen die Abschrift des Blatts), `testKeineFarbeHeisstZweiDinge` (das Wort trennt),
        // `testKeineUrteilsfarbeIstEineGrundfarbe` (nie das Leise).
        case .unbekannt: return Zeichenart.nichtGemessen.rand
        }
    }

    /// Die Schrift im Streifen. Bei «bestanden» heller als der Rand: `#4ea373` wäre auf
    /// dem dunklen Streifen zu schwach (Blatt «Die Zeichen»).
    public var schrift: Farbton {
        switch self {
        case .bestanden: return Farbton(hex: "8fd4ac")
        default: return rand
        }
    }

    /// **Gestrichelt heisst: hier ist nichts gemessen** — auch beim unbekannten Zeichen,
    /// denn ein Urteil, das die App nicht lesen kann, ist für sie keines. Damit sich ein
    /// ungeprüftes Bild auch von weitem und ohne Farbensehen nicht wie ein bestandenes
    /// liest. `testNichtGemessenUndUnbekanntSindGestrichelt` bewacht beide.
    public var gestrichelt: Bool {
        switch self {
        case .nichtGemessen, .unbekannt: return true
        case .bestanden, .durchgefallen, .entwurf: return false
        }
    }

    /// Das Wort, in Grossbuchstaben wie auf dem Bild.
    public var wort: String {
        switch self {
        case .bestanden: return "BESTANDEN"
        case .durchgefallen: return "DURCHGEFALLEN"
        case .nichtGemessen: return "NICHT GEMESSEN"
        case .entwurf: return "ENTWURF — NICHT GEPRÜFT"
        case .unbekannt: return "ZEICHEN UNBEKANNT"
        }
    }
}

/// Was an der Stelle der Zahl steht.
public enum Zahlanzeige: Equatable, Sendable {
    /// Eine übertragene, lesbare Zahl, fertig geschrieben (`"0.93"`).
    case wert(String)
    /// Das Urteil verlangt eine Zahl, und es kam keine (oder eine unlesbare).
    ///
    /// **Nie `0.00`.** Eine fehlende Zahl als Null zu schreiben hiesse, eine Messung zu
    /// behaupten, die schlechtestmöglich ausfiel — und bei «bestanden» einen Widerspruch
    /// anzuzeigen, der nur aus der Anzeige stammt.
    case fehlt
    /// Hier gehört keine Zahl hin (nicht gemessen, unbekanntes Zeichen, Entwurf ohne
    /// Unterschied).
    case keine

    /// Der Text, der am Bild steht, oder `nil`, wenn keiner hingehört.
    public var text: String? {
        switch self {
        case .wert(let t): return t
        case .fehlt: return "ohne Zahl"
        case .keine: return nil
        }
    }
}

/// Ein Vorbehalt, der **mit dem Zeichen reist** — auch ins geteilte Bild.
public struct Vorbehalt: Equatable, Sendable {
    /// Der feste Anfang, der **immer** ganz lesbar bleibt — auch in der 160-pt-Kachel,
    /// wo der Streifen zugeklappt ist (`kurz` steht dort erst nach dem Aufklappen).
    public let kopf: String
    /// Das kurze Wort für den Streifen.
    public let kurz: String
    /// Der ganze Satz, wie er vom Server kam.
    public let satz: String
}

/// Das Prüfzeichen an einem Bild: **Farbe, Wort und Zahl** (Entscheid 16) — und ein
/// Vorbehalt, wenn einer mitkam.
///
/// Hier wird nichts gemessen und nichts entschieden. Das Urteil, die Zahl und die Hinweise
/// kommen vom Server; diese Datei legt nur fest, **wie** sie am Bild aussehen. Sie liegt im
/// Kern und nicht in der Ansicht, damit genau diese Abbildung unter Linux geprüft wird
/// (`PruefzeichenTests`) — die Ansicht malt danach nur noch ab, was hier steht.
///
///     *Ein ungeprüftes Bild darf nie aussehen wie ein bestandenes — und auch nicht wie
///     gar nichts.*
public struct Pruefzeichen: Equatable, Sendable {
    public let art: Zeichenart
    /// Das Wort im Streifen. Meist `art.wort`; nur beim **fehlenden** Zeichen ein eigenes
    /// («ZEICHEN NICHT GELIEFERT»), denn *nicht geliefert* ist etwas anderes als *geliefert,
    /// aber unbekannt* — beide sind kein Urteil und tragen darum dieselbe Art und Farbe.
    public let wort: String
    public let zahl: Zahlanzeige
    /// Die Schwelle, gegen die geprüft wurde (`"0.80"`) — **nur**, wo auch die Zahl steht.
    /// Ohne Messung keine Schwelle: Eine Schwelle neben «nicht gemessen» läse sich wie ein
    /// halbes Ergebnis.
    public let schwelle: String?
    public let vorbehalte: [Vorbehalt]

    /// Das Wort, wenn der Server **kein** Zeichen mitschickte (Feld fehlt oder `null`).
    public static let wortNichtGeliefert = "ZEICHEN NICHT GELIEFERT"

    /// Der feste Anfang des Server-Hinweises, dass die Skizze beim Bildmodell nicht ankam
    /// (Entscheid E24 vom 22.09.2026; `aiimaging.kette.HINWEIS_SKIZZE_NICHT_ANGEKOMMEN`).
    ///
    /// Der Server setzt ihn als festen Anfang, *damit eine Anzeige ihn erkennen kann, ohne
    /// den Rest zu deuten*. `PruefzeichenTests` liest den Satz in `kette.py` nach und fällt,
    /// sobald er anders anfängt.
    public static let anfangSkizzeNichtAngekommen = "SKIZZE NICHT ANGEKOMMEN"

    /// Der Streifen unter dem Wort: fast schwarz, zu 94 % deckend.
    ///
    /// Befund aus dem Blatt «Die Zeichen» (21.09.2026): Mit 82 % hellte ein weisses Bild
    /// den Streifen so weit auf, dass alle farbigen Aussagen unlesbar wurden.
    /// `testJedesWortIstAufDemStreifenLesbar` rechnet das für jedes Zeichen nach, über
    /// einem weissen und einem schwarzen Bild.
    public static let streifen = Farbton(hex: "080a0d")
    public static let streifenDeckung = 0.94

    /// Die Schrift eines Vorbehalts im Streifen.
    ///
    /// **Bewusst keine der Urteilsfarben:** Ein Vorbehalt ist kein viertes Urteil, und in
    /// Gelb gelesen hiesse er «nicht gemessen» — die Geometrie *ist* aber gemessen.
    public static let vorbehaltSchrift = Blattfarbe.schrift

    /// Das Zeichen für ein Bild.
    ///
    /// - Parameters:
    ///   - urteil: Das Urteil des Servers.
    ///   - lesart: Prüfen oder Entwerfen — der Schalter am Bild.
    ///   - pruefzahl: Die Zahl zum Urteil (wie gut das Bild zur Geometrie passt).
    ///     `nil` heisst **nicht übertragen**, nie 0.
    ///   - unterschied: Nur beim Entwerfen: der Abstand zum Modell, «kein Urteil». Eine
    ///     eigene Angabe, weil es eine andere Grösse ist als die Prüfzahl — die App rechnet
    ///     die eine nie aus der anderen (Entscheid 13).
    ///   - hinweise: Die Hinweise des Servers zu diesem Bild, unverändert.
    ///   - schwelle: Die Schwelle der Prüfung, die das Urteil fällte. Gezeigt nur neben
    ///     einer gezeigten Prüfzahl.
    public init(urteil: Urteil, lesart: Bildlesart, pruefzahl: Double?,
                unterschied: Double? = nil, hinweise: [String] = [],
                schwelle: Double? = nil) {
        let art: Zeichenart
        let zahl: Zahlanzeige
        switch (lesart, urteil) {
        // OHNE MESSUNG KEINE ZAHL, in beiden Lesarten. Kommt trotzdem eine mit, ist sie
        // nicht die Zahl dieses Urteils — sie zu zeigen hiesse, «nicht gemessen» mit
        // einem Messwert zu versehen.
        case (_, .nichtGemessen):
            art = lesart == .entwerfen ? .entwurf : .nichtGemessen
            zahl = .keine
        case (.entwerfen, _):
            art = .entwurf
            zahl = unterschied.map(Pruefzeichen.schreibe) ?? .keine
        case (.pruefen, .bestanden):
            art = .bestanden
            zahl = Pruefzeichen.schreibe(pruefzahl)
        case (.pruefen, .durchgefallen):
            art = .durchgefallen
            zahl = Pruefzeichen.schreibe(pruefzahl)
        }
        // DIE SCHWELLE NUR NEBEN EINER PRUEFZAHL: nicht beim Entwurf (dort ist die Zahl
        // ein Unterschied), nicht ohne Messung, nicht neben «ohne Zahl». Bewacht in
        // `testDieSchwelleNurNebenEinerPruefzahl` — der Teil «nicht beim Entwurf» erst seit
        // der Durchsicht vom 22.09.2026 (die Mutation `if true, case .wert = zahl` blieb bis
        // dahin grün).
        var grenze: String?
        if art == .bestanden || art == .durchgefallen, case .wert = zahl,
           case .wert(let s) = Pruefzeichen.schreibe(schwelle) {
            grenze = s
        }
        self.init(art: art, wort: art.wort, zahl: zahl, schwelle: grenze,
                  vorbehalte: Pruefzeichen.vorbehalte(aus: hinweise))
    }

    /// Das Zeichen aus dem Feld `zeichen`, wie `GET /api/projekt` es je Bild liefert.
    ///
    /// Ein unbekanntes Zeichen wird **nicht** geraten: Es bekommt die eigene Art
    /// `.unbekannt` — weder «nicht gemessen» noch gar kein Zeichen. **`nil` heisst: nicht
    /// geliefert** — dieselbe Art, aber das Wort sagt es («ZEICHEN NICHT GELIEFERT»). Bis
    /// zum 22.09.2026 wurde ein fehlendes Zeichen in der App zu `""` und damit zu einem
    /// unbekannten; *eine Lücke, die als Wert weitergereicht wird, sieht aus wie ein Wert.*
    public init(zeichen: String?, lesart: Bildlesart, pruefzahl: Double?,
                unterschied: Double? = nil, hinweise: [String] = [],
                schwelle: Double? = nil) {
        if let roh = zeichen, let urteil = Urteil(zeichen: roh) {
            self.init(urteil: urteil, lesart: lesart, pruefzahl: pruefzahl,
                      unterschied: unterschied, hinweise: hinweise, schwelle: schwelle)
        } else {
            self.init(art: .unbekannt,
                      wort: zeichen == nil ? Pruefzeichen.wortNichtGeliefert : Zeichenart.unbekannt.wort,
                      zahl: .keine, schwelle: nil,
                      vorbehalte: Pruefzeichen.vorbehalte(aus: hinweise))
        }
    }

    private init(art: Zeichenart, wort: String, zahl: Zahlanzeige, schwelle: String?,
                 vorbehalte: [Vorbehalt]) {
        self.art = art
        self.wort = wort
        self.zahl = zahl
        self.schwelle = schwelle
        self.vorbehalte = vorbehalte
    }

    /// Die Hauptzeile im Streifen: Wort und Zahl.
    ///
    /// Beim Entwerfen heisst die Zahl «Unterschied», damit sie nicht als Prüfzahl gelesen
    /// wird.
    public var zeile: String {
        guard let t = zahl.text else { return wort }
        if art == .entwurf, case .wert = zahl {
            return wort + " · Unterschied " + t
        }
        return wort + " · " + t
    }

    /// Alle Zeilen, die auf dem Bild stehen — auch im geteilten (Entscheid 20).
    public var zeilen: [String] {
        [zeile] + vorbehalte.map { $0.kurz }
    }

    /// Was ein Bildschirmleser vorliest: dasselbe wie die Zeilen, in ganzen Wörtern.
    public var vorlesetext: String {
        var teile = ["Prüfzeichen: " + zeile.replacingOccurrences(of: " · ", with: ", ")]
        teile += vorbehalte.map { $0.satz }
        return teile.joined(separator: ". ")
    }

    // ------------------------------------------------------------------ intern

    /// Eine Zahl mit zwei Stellen und Punkt, unabhängig von der Spracheinstellung des
    /// Geräts — oder `.fehlt`, wenn keine lesbare da ist.
    static func schreibe(_ wert: Double?) -> Zahlanzeige {
        guard let wert = wert, wert.isFinite else { return .fehlt }
        let text = String(format: "%.2f", locale: Locale(identifier: "en_US_POSIX"), wert)
        // «-0.00» ist dieselbe Zahl wie «0.00» und sähe aus wie ein Vorzeichenbefund.
        return .wert(text == "-0.00" ? "0.00" : text)
    }

    static func vorbehalte(aus hinweise: [String]) -> [Vorbehalt] {
        // ERKANNT AM FESTEN ANFANG, nicht am ersten Platz der Liste. Der Server setzt ihn
        // heute nach vorne; ein zweiter Hinweis davor darf ihn nicht unsichtbar machen.
        let treffer = hinweise.first { h in
            h.drop(while: { $0.isWhitespace }).hasPrefix(anfangSkizzeNichtAngekommen)
        }
        guard let satz = treffer else { return [] }
        return [Vorbehalt(kopf: anfangSkizzeNichtAngekommen,
                          kurz: anfangSkizzeNichtAngekommen + " — aus Tiefenkarte und Text gerechnet",
                          satz: satz.trimmingCharacters(in: .whitespacesAndNewlines))]
    }
}

// ======================================================================= die Blattfarben

/// Die übrigen Farbtöne der Entwurfsfläche — **abgeschrieben an einer Stelle, im Kern,
/// damit sie hier geprüft werden** (Durchsicht B, 22.09.2026).
///
/// Bis dahin standen sie als Hex-Ziffern in `Leiste/Zeichenblatt.swift` und in zwei Ansichten
/// der Mappe — dort, wo sie niemand prüfen kann (SwiftUI übersetzt unter Linux nicht). Jetzt
/// macht die App aus diesen Werten nur noch Farben, und
/// `PruefzeichenTests.testJederFarbtonStehtSoAufDemBlatt` hält jeden gegen die Abschrift
/// des Blatts; die Töne, die auch die Webseite führt, vergleicht
/// `testDieGemeinsamenToeneSindDieDerWebseite` mit `oberflaeche/seite.html`.
///
/// Die Farben der **Urteile** stehen nicht hier, sondern an `Zeichenart` — dort wird
/// geprüft, dass «nicht gemessen» nie wie «bestanden» aussieht.
public enum Blattfarbe {
    /// Grund der ganzen App (Blatt «Die Zeichen»: Grund).
    public static let grund = Farbton(hex: "14161a")
    /// Ein Feld, eine Karte, ein ungewählter Knopf («Die Zeichen»: Feld).
    public static let feld = Farbton(hex: "1c1f26")
    /// Leiste, Kopfzeile, Seitenfeld (Blatt «Main»).
    public static let leiste = Farbton(hex: "16191e")
    /// Die Bühne hinter dem Zeichenblatt (Blatt «Main»).
    public static let buehne = Farbton(hex: "101317")
    /// Trennlinien und Ränder (Blatt «Main», in der Webseite `--rand`).
    public static let linie = Farbton(hex: "2b3038")
    /// Alles Gelesene («Die Zeichen»: Schrift).
    public static let schrift = Farbton(hex: "e6e8ec")
    /// Beschriftungen, die zurücktreten («Die Zeichen»: Leise).
    public static let leise = Farbton(hex: "9aa2ae")
    /// Gewählt: Rand, Grund, Schrift («Die Zeichen»: Anfassbar). Der Rand ist das Grün von
    /// «bestanden» — eine bekannte, offene Spannung des Entwurfs, siehe `Zeichenblatt`.
    public static let gewaehltRand = Farbton(hex: "4ea373")
    public static let gewaehltGrund = Farbton(hex: "223028")
    public static let gewaehltSchrift = Farbton(hex: "a7dec0")
    /// Der Grund einer Bildkachel (Blatt «Main»: die Kacheln der Läufe).
    public static let kachel = Farbton(hex: "14181b")
    /// Der Grund eines Bildes, das nicht geladen ist (Blätter «Main», «Bilder»).
    public static let luecke = Farbton(hex: "0e1013")

    /// Die Grundfarben, die **keine** Aussage über ein Bild tragen. Keine Urteilsfarbe darf
    /// eine von ihnen sein (`testKeineUrteilsfarbeIstEineGrundfarbe`).
    public static let grundfarben: [Farbton] = [grund, feld, leiste, buehne, linie, schrift,
                                                leise, kachel, luecke]
}

// ================================================================ die Mappe, je Bild

/// Woraus ein Bild einer Reihe stammt (`variantengruppe`, Entscheid 32) — roh, wie es kam.
public struct Variantengruppe: Equatable, Sendable {
    public let id: String?
    /// `startwerte` oder `ebenen` — roh; ein anderer Wert wird nicht geraten.
    public let art: String?
    public let nummer: Int?
    public let von: Int?
    /// Bei `startwerte`: der Startwert dieser Variante.
    public let seed: Int?
    /// Bei `ebenen`: die Skizze dieser Variante.
    public let skizze: String?

    public init(_ o: [String: JSONWert]) {
        id = o["id"]?.alsText ?? o["id"]?.alsGanz.map { String($0) }
        art = o["art"]?.alsText
        nummer = o["nummer"]?.alsGanz
        von = o["von"]?.alsGanz
        seed = o["seed"]?.alsGanz
        skizze = o["skizze"]?.alsText
    }
}

/// Ein Bild der Mappe, **wie der Server es seit dem 22.09.2026 liefert** (`bilder[]` aus
/// `GET /api/projekt`, `docs/VISBOX_PROTOKOLL.md` §4; gebaut in `oberflaeche/server.py`,
/// `_bild_fuer_die_flaeche`).
///
/// Jedes Feld, das fehlt oder `null` ist, bleibt `nil` — **nicht geliefert**, nie `""`,
/// nie `0`, nie `false`. Das Zeichen daraus macht `pruefzeichen(_:)`.
///
/// **Warum hier und nicht an `Bildeintrag` (`Anfragen.swift`):** Die Felder `score`,
/// `schwelle`, `titel`, `entwurf`, `variantengruppe`, `hinweise` und die beiden zur Skizze
/// braucht nur das Prüfzeichen; `Anfragen.swift` gehörte in dieser Welle einer anderen
/// Einheit. Gelesen wird dieselbe Antwort (`Mappenlage.lies`), keine zweite Anfrage.
public struct Mappenbild: Equatable, Sendable {
    public let bild: String?
    /// Das Zeichen, roh. `nil` heisst **nicht geliefert**. Kam etwas anderes als ein Text,
    /// steht hier seine JSON-Form — dann ist es ein unbekanntes Zeichen, kein fehlendes.
    public let zeichen: String?
    public let satz: String?
    public let erzeugt: String?
    public let schicht: String?
    /// `true`, `false` (die Mappe nennt es, die Datei fehlt) oder `nil` (nicht gefragt).
    public let vorhanden: Bool?
    /// Die Zahl zum Zeichen — `nil` heisst nicht gemessen, nie 0.
    public let score: Double?
    public let schwelle: Double?
    /// Der eigene Name (Entscheid 19) — `nil`: dann gilt der Name nach der Zeit.
    public let titel: String?
    /// `true` aus einem Entwurfslauf, `false` sonst, `nil` bei älteren Einträgen.
    public let entwurf: Bool?
    public let variantengruppe: Variantengruppe?
    /// Die Hinweise der Bildstufe. `[]` heisst gemessen und ohne Hinweis, **`nil` heisst
    /// nicht gemessen.**
    public let hinweise: [String]?
    /// Drei Antworten: `true` (die Skizze kam beim Modell nicht an), `false` (kam an),
    /// `nil` (kein Skizzenbild oder nicht gemessen).
    public let skizzeNichtAngekommen: Bool?
    /// Der Satz der Bibliothek dazu, oder `nil`.
    public let skizzeHinweis: String?
    /// **Die Unterlage** — der Name des Bildes, über das skizziert wurde (Feld `vorher`,
    /// Entscheid 17: Vorher und Nachher). `nil` heisst: Es gab keine, oder der Server nennt
    /// sie nicht (ein Server vor dem 23.09.2026 führt das Feld nicht — es kam mit der Welle 2b,
    /// `f8f2a40`) — **nicht** «es gibt keine». Ein leerer Name gilt wie keiner: Unter ihm
    /// lässt sich nichts laden.
    ///
    /// Bis zum 23.09.2026 gab es das Feld nicht, und der Vergleich Vorher/Nachher war im
    /// Produkt nie zu sehen (Durchsicht der Verdrahtung vom 22.09.2026). Die Bytes holt die
    /// App-Schicht über `GET /bild` unter genau diesem Namen.
    public let vorher: String?

    public init(_ o: [String: JSONWert]) {
        bild = o["bild"]?.alsText
        zeichen = o["zeichen"].flatMap(Mappenbild.textOderForm)
        satz = o["satz"]?.alsText
        erzeugt = o["erzeugt"]?.alsText
        schicht = o["schicht"]?.alsText
        vorhanden = o["vorhanden"]?.alsWahrheit
        score = o["score"]?.alsZahl.flatMap { $0.isFinite ? $0 : nil }
        schwelle = o["schwelle"]?.alsZahl.flatMap { $0.isFinite ? $0 : nil }
        // EIN LEERER NAME IST KEIN NAME: Er gilt wie keiner, sonst stünde an der Kachel nichts.
        titel = o["titel"]?.alsText.flatMap {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : $0
        }
        entwurf = o["entwurf"]?.alsWahrheit
        variantengruppe = o["variantengruppe"]?.alsObjekt.map(Variantengruppe.init)
        hinweise = o["hinweise"]?.alsListe?.compactMap { $0.alsText }
        skizzeNichtAngekommen = o["skizze_nicht_angekommen"]?.alsWahrheit
        skizzeHinweis = o["skizze_hinweis"]?.alsText
        vorher = o["vorher"]?.alsText.flatMap {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : $0
        }
    }

    /// Wie das Bild ohne eigenen Schalter gelesen wird: **Ein Entwurf als Entwurf** (das
    /// blaue Zeichen entsteht am Feld `entwurf`, Protokoll §4), alles andere geprüft. Ein
    /// älterer Eintrag ohne das Feld wird geprüft gelesen — und zeigt dann ehrlich, was
    /// sein Zeichen sagt.
    public var vorgabeLesart: Bildlesart {
        entwurf == true ? .entwerfen : .pruefen
    }

    /// Das Prüfzeichen dieses Bildes in einer Lesart — **Farbe, Wort, Zahl, Vorbehalt.**
    ///
    /// Die Zahl ist `score`; ohne Urteil (`nicht-gemessen`) steht **keine**, auch wenn der
    /// Server eine mitschickt (`Pruefzeichen.init(urteil:…)`, die dritte Antwort). Der
    /// Vorbehalt «SKIZZE NICHT ANGEKOMMEN» erscheint, wenn der Server ihn meldet
    /// (`skizze_nicht_angekommen: true`) **oder** ein Hinweis mit dem festen Anfang
    /// beginnt — ein Vorbehalt geht nie verloren, weil nur einer der beiden Wege ihn trug.
    public func pruefzeichen(_ lesart: Bildlesart) -> Pruefzeichen {
        var alle = hinweise ?? []
        if skizzeNichtAngekommen == true {
            let satz = skizzeHinweis ?? (Pruefzeichen.anfangSkizzeNichtAngekommen
                + ": Der Server meldet es, schickte aber keinen Satz dazu.")
            if !alle.contains(satz) { alle.insert(satz, at: 0) }
        }
        return Pruefzeichen(zeichen: zeichen, lesart: lesart, pruefzahl: score,
                            hinweise: alle, schwelle: schwelle)
    }

    /// Ein Text wie er ist; `null` als nicht geliefert; alles andere in seiner JSON-Form.
    static func textOderForm(_ w: JSONWert) -> String? {
        if w.istNull { return nil }
        if let t = w.alsText { return t }
        guard let daten = try? JSONWert.liste([w]).daten(),
              let form = String(data: daten, encoding: .utf8) else { return "?" }
        return String(form.dropFirst().dropLast())
    }
}

/// Wo eine Skizze der Mappe steht (`skizzen[].stand`).
public enum Skizzenstand: String, Equatable, Sendable {
    /// Liegt da, niemand rechnet (Entscheid 11: nichts rechnet von selbst).
    case offen
    /// Hat ein Bild (`ergebnis`) und darüber ein Urteil.
    case gerechnet
    /// Bleibt als Spur, rechnet nicht mehr mit.
    case verworfen
}

/// Eine Skizze der Mappe (`skizzen[]`), roh wie sie kam — samt eigenem Namen.
public struct Mappenskizze: Equatable, Sendable {
    public let skizze: String?
    public let ueber: String?
    public let erzeugt: String?
    /// Wie der Server den Stand schrieb.
    public let standRoh: String?
    public let bemerkung: String?
    /// Der Bildname, wenn etwas daraus wurde; sonst `nil`.
    public let ergebnis: String?
    public let titel: String?

    public init(_ o: [String: JSONWert]) {
        skizze = o["skizze"]?.alsText
        ueber = o["ueber"]?.alsText
        erzeugt = o["erzeugt"]?.alsText
        standRoh = o["stand"]?.alsText
        bemerkung = o["bemerkung"]?.alsText
        ergebnis = o["ergebnis"]?.alsText
        titel = o["titel"]?.alsText.flatMap {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : $0
        }
    }

    /// Ein unbekannter Stand gibt `nil` — **nicht** «offen». Eine Skizze, deren Stand die
    /// App nicht kennt, bekommt keinen Knopf «Rechnen lassen» geschenkt.
    public var stand: Skizzenstand? { standRoh.flatMap(Skizzenstand.init(rawValue:)) }
}

/// Was die App aus `GET /api/projekt` für die Mappe braucht.
public struct Mappenlage: Equatable, Sendable {
    public let name: String?
    /// Die Standnummer (§6) — `nil` bei einer Mappe, die sie nicht führt. Geht als
    /// `von_stand` an `POST /api/benennen`.
    public let standNr: Int?
    /// `nil` heisst **nicht geliefert** — nicht «keine Bilder».
    public let bilder: [Mappenbild]?
    public let skizzen: [Mappenskizze]?

    public init(_ o: [String: JSONWert]) {
        name = o["name"]?.alsText
        standNr = o["stand_nr"]?.alsGanz
        bilder = o["bilder"]?.alsListe?.compactMap { $0.alsObjekt.map(Mappenbild.init) }
        skizzen = o["skizzen"]?.alsListe?.compactMap { $0.alsObjekt.map(Mappenskizze.init) }
    }

    public static func lies(status: Int, daten: Data) throws -> Mappenlage {
        Mappenlage(try liesAntwort(status: status, daten: daten))
    }
}

// ============================================================ Rechnen lassen, Namen geben

/// Was bestellt wird, wenn jemand «Rechnen lassen» wählt — **und in welcher Lesart.**
///
/// Prüfen oder Entwerfen (Entscheide 15 und 30) steht hier, weil es dieselbe Wahl ist wie
/// am Bild: Beim Entwerfen rechnet die HomeStation schnell und **ohne Geometrieprüfung**
/// (`entwurf: true`), und das Bild trägt danach das blaue Zeichen.
public enum Rechenbestellung: Equatable, Sendable {
    /// Eine Skizze aus der Mappe (`POST /api/rechne-skizze`). Ohne `anweisung` gilt drüben
    /// die Bemerkung der Skizze.
    case skizze(String, anweisung: String?)
    /// Mehrere Skizzen als **Ebenen-Reihe** (Entscheid 32) — je Skizze eine Variante.
    case ebenenreihe([String], anweisung: String?)
    /// Das Bild aus dem Modell, mit **drei Startwerten** (Entscheid 32, `POST /api/rechne`
    /// mit `varianten`).
    case startwerte

    /// Wie viele Varianten eine Reihe hat: **drei** — so viele zeigt die Mappe
    /// nebeneinander (Entscheid 18). Dieselbe Zahl wie beim Senden der Ebenen, nicht eine
    /// zweite.
    public static let reihenlaenge = Ebenenstapel.hoechstensVarianten

    /// Was nach einer Ebenen-Reihe von der Auswahl bleibt — **geleert wird nur, was die
    /// HomeStation angenommen hat**, und nur, wenn es noch die Auswahl ist, die hinausging.
    ///
    /// `jetzt` ist die Auswahl, wenn die Quittung kommt; `gesendet` die, die bestellt wurde.
    ///
    /// Befund der Durchsicht vom 22.09.2026: Die Skizzenliste leerte die Auswahl gleich nach
    /// dem Tippen, auch wenn die Bestellung abgelehnt wurde oder gar nicht hinausging — wer
    /// es noch einmal versuchen wollte, musste zwei bis drei Skizzen neu wählen. Bei
    /// `ungewiss` bleibt sie ebenfalls stehen: Ob drüben etwas rechnet, zeigt der Laufstand,
    /// und eine stehengebliebene Auswahl kostet höchstens einen Tipp, eine verlorene drei.
    ///
    /// Befund der Durchsicht vom 23.09.2026: Die Regel lief auf der Auswahl **zur Zeit der
    /// Quittung**. Wählte jemand, während die Bestellung unterwegs war, neu, leerte das
    /// Annehmen der alten die neue Wahl mit. Hat sich die Auswahl seither geändert, bleibt sie
    /// darum, wie sie ist — geleert wird nie etwas, das nicht hinausging.
    /// Bewacht: `testDieReiheBleibtStehenAusserSieWurdeAngenommen`,
    /// `testEineInzwischenGeaenderteReiheBleibtStehen`.
    public static func reihe(_ jetzt: [String], gesendet: [String],
                             nach quittung: Handlungsquittung) -> [String] {
        quittung.ausgang == .angenommen && jetzt == gesendet ? [] : jetzt
    }

    /// Die Anfrage dazu. Wirft `Rumpffehler`, wenn sie sich nicht schreiben lässt.
    public func anfrage(lesart: Bildlesart, ordner: String?,
                        anmeldung: Anmeldung?) throws -> Anfrage {
        let entwurf = lesart == .entwerfen
        switch self {
        case .skizze(let name, let anweisung):
            return try Anfragen.rechneSkizze([name], anweisung: anweisung, entwurf: entwurf,
                                             ordner: ordner, anmeldung: anmeldung)
        case .ebenenreihe(let namen, let anweisung):
            return try Anfragen.rechneSkizze(namen, anweisung: anweisung, entwurf: entwurf,
                                             ordner: ordner, anmeldung: anmeldung)
        case .startwerte:
            // `Anfragen.rechne` kennt `varianten` und `entwurf` (noch) nicht; gebaut wird
            // darum über die allgemeine Bauform, mit denselben Feldnamen wie im Protokoll §3.
            var rumpf: [String: JSONWert] = ["entwurf": .wahrheit(entwurf),
                                             "varianten": .ganz(Rechenbestellung.reihenlaenge)]
            if let o = ordner, !o.isEmpty { rumpf["ordner"] = .text(o) }
            return try Anfragen.baue(Wege.rechne, rumpf: rumpf, anmeldung: anmeldung)
        }
    }
}

/// Was nach «Rechnen lassen», «Abbrechen» oder «Namen geben» angezeigt wird — **mit
/// vier Ausgängen, und einer davon ist «nicht bekannt».**
///
/// Eine Antwort, die nicht gelesen werden kann, oder gar keine Antwort, heisst nicht
/// «hat nicht geklappt»: Die Anfrage kann drüben angekommen sein. Das steht dann so da
/// (`ungewiss`), und der Laufstand oder die Mappe zeigt, was wirklich geschah.
public struct Handlungsquittung: Equatable, Sendable {
    public enum Ausgang: Equatable, Sendable {
        /// Die HomeStation hat es angenommen.
        case angenommen
        /// Die HomeStation hat es abgelehnt — mit ihrem Satz.
        case abgelehnt
        /// Ob es drüben ankam, ist **nicht bekannt**.
        case ungewiss
        /// Es ging nicht hinaus (nicht gekoppelt, nicht baubar) — sicher nicht angekommen.
        case nichtGesendet
    }

    public let ausgang: Ausgang
    public let satz: String

    public init(ausgang: Ausgang, satz: String) {
        self.ausgang = ausgang
        self.satz = satz
    }

    /// Keine Antwort: **ungewiss**, nicht abgelehnt.
    public static func ohneAntwort(grund: String) -> Handlungsquittung {
        Handlungsquittung(ausgang: .ungewiss,
                          satz: grund + " Ob es drüben ankam, ist nicht bekannt.")
    }

    /// `POST /api/rechne` oder `/api/rechne-skizze`.
    public static func rechnen(status: Int, daten: Data) -> Handlungsquittung {
        lies(status: status, daten: daten, bestaetigung: "gestartet") { o in
            o["entwurf"]?.alsWahrheit == true
                ? "Bestellt, als Entwurf: schnell und ohne Geometrieprüfung. Fertig ist es "
                    + "erst, wenn das Bild in der Mappe liegt."
                : "Bestellt. Fertig ist es erst, wenn das Bild in der Mappe liegt."
        }
    }

    /// `POST /api/abbrechen`. **Verlangt ist nicht gewirkt** (Protokoll §3): Der Schritt,
    /// der gerade rechnet, rechnet zu Ende.
    public static func abbrechen(status: Int, daten: Data) -> Handlungsquittung {
        lies(status: status, daten: daten, bestaetigung: "abbruch_verlangt") { o in
            o["satz"]?.alsText ?? "Abbruch verlangt. Der Schritt, der gerade rechnet, rechnet "
                + "zu Ende; danach beginnt keiner mehr."
        }
    }

    /// `POST /api/benennen`. Die Datei behält ihren Namen (Entscheid 19).
    public static func benennen(status: Int, daten: Data) -> Handlungsquittung {
        lies(status: status, daten: daten, bestaetigung: "benannt") { _ in
            "Benannt. Die Datei behält ihren Namen."
        }
    }

    private static func lies(status: Int, daten: Data, bestaetigung: String,
                             satz: ([String: JSONWert]) -> String) -> Handlungsquittung {
        do {
            let o = try liesAntwort(status: status, daten: daten)
            // ERFOLG NUR, WENN ER DASTEHT. Eine 200 ohne die Bestätigung ist nicht «nein»,
            // sondern «nicht bekannt».
            guard o[bestaetigung]?.alsWahrheit == true else {
                return Handlungsquittung(
                    ausgang: .ungewiss,
                    satz: "Die HomeStation antwortete, aber ohne «\(bestaetigung): true». "
                        + "Ob es drüben ankam, ist nicht bekannt.")
            }
            return Handlungsquittung(ausgang: .angenommen, satz: satz(o))
        } catch let f as Serverfehler {
            return Handlungsquittung(ausgang: f.art == .unlesbar ? .ungewiss : .abgelehnt,
                                     satz: f.satz)
        } catch {
            return Handlungsquittung(ausgang: .ungewiss,
                                     satz: "Die Antwort der HomeStation war nicht lesbar.")
        }
    }
}
