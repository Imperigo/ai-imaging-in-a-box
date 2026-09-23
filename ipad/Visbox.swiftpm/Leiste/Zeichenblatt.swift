import SwiftUI

/// Farben, Schriften und Masse der App — nach dem Blatt «Die Zeichen» der Entwurfsfläche
/// (21./22.09.2026), **an einer Stelle.**
///
/// **Die Farbtöne selbst stehen nicht hier**, sondern im Kern (`Blattfarbe` und
/// `Zeichenart` in `Kern/Pruefzeichen.swift`): Dort werden sie unter Linux gegen die
/// Abschrift des Blatts und gegen die Webseite geprüft
/// (`PruefzeichenTests.testJederFarbtonStehtSoAufDemBlatt`). Bis zur Durchsicht B vom
/// 22.09.2026 standen sie hier als Hex-Ziffern, die keine Probe sah. Diese Datei macht aus
/// ihnen nur SwiftUI-Farben.
///
/// **Was bewacht ist, genau** (Durchsicht der Verdrahtung, 22.09.2026 — bis dahin stand
/// hier, *jeder* Hex-Ton ausserhalb des Kerns lasse eine Probe fallen):
/// `PruefzeichenTests.testDieAppSchreibtKeineFarbtoeneAusserhalbDesKerns` fällt nur, wenn
/// ausserhalb des Kerns ein `Farbton` aus Hex-Ziffern gebaut wird. Andere Schreibweisen
/// (`#rrggbb`-Text, Zahl durch 255, Hex-Bytes) sucht die breitere Probe `FarbtonTests` der
/// Einheit «Zeichnen».
enum Zeichenblatt {
    // ----------------------------------------------------------- Grund und Schrift
    static let grund = Color(Blattfarbe.grund)
    static let feld = Color(Blattfarbe.feld)
    static let leiste = Color(Blattfarbe.leiste)
    static let buehne = Color(Blattfarbe.buehne)
    static let linie = Color(Blattfarbe.linie)
    static let schrift = Color(Blattfarbe.schrift)
    static let leise = Color(Blattfarbe.leise)
    /// Der Grund einer Bildkachel und der eines Bildes, das nicht geladen ist.
    static let kachel = Color(Blattfarbe.kachel)
    static let luecke = Color(Blattfarbe.luecke)

    // ------------------------------------------------------ gewählt (die Anfassfarbe)
    //
    // DAS GRUEN EINES GEWAEHLTEN KNOPFS IST DAS GRUEN VON «BESTANDEN» — so steht es im
    // Entwurf (Blatt «Main»), und es ist eine bekannte Spannung: Ein gewähltes Werkzeug
    // heisst nicht «bestanden». Getragen wird sie davon, dass ein Knopf nie am Bild sitzt
    // und das Prüfzeichen immer Wort UND Farbe trägt. Offen für die Entwurfsfläche.
    static let gewaehltRand = Color(Blattfarbe.gewaehltRand)
    static let gewaehltGrund = Color(Blattfarbe.gewaehltGrund)
    static let gewaehltSchrift = Color(Blattfarbe.gewaehltSchrift)

    // --------------------------------------------------------------------- Masse

    /// Ein Tippziel: 60 × 60 pt, gewählt und ungewählt (Blatt «Die Zeichen»).
    static let tippziel: CGFloat = 60
    /// **Nie darunter** — auch nicht dort, wo der Entwurf enger ist (die Ebenen-Zeile).
    static let tippzielMindestens: CGFloat = 44
    /// Luft zwischen zwei Tippzielen.
    static let abstand: CGFloat = 10
    /// Die Leiste senkrecht (Querformat) — breit genug für ein Tippziel plus Rand.
    static let leisteBreite: CGFloat = 88
    /// Die Leiste waagrecht (Hochformat), unten in Daumenreichweite.
    static let leisteHoehe: CGFloat = 96
    /// Das Seitenfeld im Querformat.
    static let seitenfeldBreite: CGFloat = 340
}

/// Die drei mitgelieferten Schriftfamilien (Entscheide 20 und 25).
enum Schriftfamilie: CaseIterable {
    /// IBM Plex Sans — alles Gelesene.
    case plexSans
    /// IBM Plex Mono — jede Zahl, jeder Dateiname.
    case plexMono
    /// Instrument Serif — Titel und Wortzeichen.
    case instrumentSerif
}

/// Ein mitgelieferter Schnitt: welche Familie, welcher PostScript-Name, welche Datei.
struct Schriftschnitt {
    let familie: Schriftfamilie
    /// Der Name, unter dem das System die Schrift nach der Registrierung kennt.
    let postScript: String
    /// Die Datei unter `Schriften/<Familie>/`, ohne `.ttf`.
    let datei: String
    /// Die Strichstärke des Schnitts auf der OpenType-Skala (400 normal, 500 mittel,
    /// 600 halbfett) — wie sie die Datei selbst angibt (Tabelle `OS/2`, bewacht).
    let staerke: CGFloat
}

/// Die Schriften — **die eine Stelle, an der ihre Namen stehen.**
///
/// Entschieden sind IBM Plex Sans/Mono und Instrument Serif (SIL OFL 1.1, Entscheid 25),
/// **mitgeliefert, nicht geladen** (Entscheid 20: das geteilte Bild trägt das Zeichen, also
/// muss die Schrift auf dem Gerät liegen, und zum Start darf keine Netzverbindung nötig
/// sein). Seit dem 23.09.2026 liegen die Dateien unverändert in `Schriften/` (Herkunft und
/// Prüfsummen im `NOTICE`), registriert werden sie in `Schriftregister.swift`.
///
/// **Die PostScript-Namen und Dateinamen stehen nur in `schnitte`.**
/// `tests/test_ipad_geruest.py` liest jeden Namen aus der Namentabelle der genannten Datei
/// nach und fällt, wenn ein Name dort nicht vorkommt, eine Datei fehlt oder ein Name
/// ausserhalb dieser Datei steht.
///
/// **Scheitert die Registrierung einer Familie, gilt für sie die Systemschrift** (serif,
/// normal, gleich breit — wie bis zum 22.09.2026). Nie unsichtbarer Text, und nie still eine
/// fremde Ersatzschrift: `Schriftregister` prüft nach dem Registrieren, ob das System unter
/// dem Namen wirklich diese Schrift liefert. *Gebaut, am Gerät unbestätigt.*
enum Schrift {
    /// Jeder mitgelieferte Schnitt.
    ///
    /// IBM Plex Sans liegt in der Originalverteilung (google/fonts, 23.09.2026) **nur als
    /// variable Datei** vor — eine Datei, deren Strichstärke über die Achse `wght` (100–700)
    /// einstellbar ist. Ihr Grundschnitt heisst `IBMPlexSans-Regular`; das Gewicht setzt
    /// `Schriftregister.schrift(_:groesse:gewicht:)` über diese Achse. Plex Mono liegt in
    /// festen Schnitten vor; mitgeliefert sind die drei, die die App verlangt (normal,
    /// mittel, halbfett — nachgezählt an den Aufrufen von `zahl(_:_:)` am 23.09.2026).
    static let schnitte: [Schriftschnitt] = [
        Schriftschnitt(familie: .plexSans, postScript: "IBMPlexSans-Regular",
                       datei: "IBMPlexSans[wdth,wght]", staerke: 400),
        Schriftschnitt(familie: .plexMono, postScript: "IBMPlexMono-Regular",
                       datei: "IBMPlexMono-Regular", staerke: 400),
        Schriftschnitt(familie: .plexMono, postScript: "IBMPlexMono-Medium",
                       datei: "IBMPlexMono-Medium", staerke: 500),
        Schriftschnitt(familie: .plexMono, postScript: "IBMPlexMono-SemiBold",
                       datei: "IBMPlexMono-SemiBold", staerke: 600),
        Schriftschnitt(familie: .instrumentSerif, postScript: "InstrumentSerif-Regular",
                       datei: "InstrumentSerif-Regular", staerke: 400),
    ]

    /// Titel und Wortzeichen (Instrument Serif; es gibt nur den normalen Schnitt).
    static func titel(_ groesse: CGFloat) -> Font {
        schnitt(.instrumentSerif, 400).flatMap { Schriftregister.schrift($0, groesse: groesse) }
            ?? .system(size: groesse, weight: .regular, design: .serif)
    }

    /// Alles Gelesene (IBM Plex Sans, Gewicht über die Achse der variablen Datei).
    static func text(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        schnitt(.plexSans, 400).flatMap {
            Schriftregister.schrift($0, groesse: groesse, gewicht: staerke(gewicht))
        } ?? .system(size: groesse, weight: gewicht, design: .default)
    }

    /// Jede Zahl, jeder Dateiname (IBM Plex Mono) — gleich breite Ziffern, damit 0.93 und
    /// 0.36 untereinander gleich breit sind und ein Sprung auffällt.
    ///
    /// Mitgeliefert sind drei Schnitte; ein anderes Gewicht nimmt den nächsten: leichter als
    /// normal → normal, fetter als halbfett → halbfett. (Am 23.09.2026 verlangt kein Aufruf
    /// ein solches Gewicht.)
    static func zahl(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        schnitt(.plexMono, staerke(gewicht)).flatMap {
            Schriftregister.schrift($0, groesse: groesse)
        } ?? .system(size: groesse, weight: gewicht, design: .monospaced)
    }

    /// Die Kopfzeile eines Abschnitts (klein, gesperrt, Grossbuchstaben).
    static let abschnitt = text(12, .semibold)

    // ------------------------------------------------------------------ intern

    /// Der Schnitt einer Familie, der der verlangten Stärke am nächsten liegt.
    private static func schnitt(_ familie: Schriftfamilie,
                                _ staerke: CGFloat) -> Schriftschnitt? {
        schnitte.filter { $0.familie == familie }
            .min { abs($0.staerke - staerke) < abs($1.staerke - staerke) }
    }

    /// Ein SwiftUI-Gewicht als Zahl der Achse `wght` (OpenType: 400 normal, 700 fett).
    private static func staerke(_ gewicht: Font.Weight) -> CGFloat {
        if gewicht == .ultraLight { return 200 }
        if gewicht == .thin { return 100 }
        if gewicht == .light { return 300 }
        if gewicht == .medium { return 500 }
        if gewicht == .semibold { return 600 }
        if gewicht == .bold { return 700 }
        if gewicht == .heavy { return 800 }
        if gewicht == .black { return 900 }
        return 400
    }
}

extension Color {
    /// Ein Farbton aus dem Kern als SwiftUI-Farbe.
    init(_ ton: Farbton) {
        self.init(.sRGB, red: Double(ton.rot) / 255, green: Double(ton.gruen) / 255,
                  blue: Double(ton.blau) / 255, opacity: 1)
    }
}

/// Die Kopfzeile eines Abschnitts, wie im Entwurf («WAS DIE SKIZZE TUT»).
struct Abschnittstitel: View {
    let text: String

    var body: some View {
        Text(text.uppercased())
            .font(Schrift.abschnitt)
            .tracking(0.9)
            .foregroundStyle(Zeichenblatt.leise)
    }
}

/// Ein Knopf im Stil des Entwurfs: gewählt grün umrandet, sonst leise.
///
/// Die Grösse ist das Tippziel (60 pt); kleiner als 44 pt lässt sich keiner machen.
struct Wahlknopfstil: ButtonStyle {
    var gewaehlt: Bool
    var breite: CGFloat? = Zeichenblatt.tippziel
    var hoehe: CGFloat = Zeichenblatt.tippziel

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Schrift.text(15, gewaehlt ? .semibold : .regular))
            .foregroundStyle(gewaehlt ? Zeichenblatt.gewaehltSchrift : Zeichenblatt.leise)
            .padding(.horizontal, breite == nil ? 18 : 0)
            .frame(width: breite.map { max($0, Zeichenblatt.tippzielMindestens) },
                   height: max(hoehe, Zeichenblatt.tippzielMindestens))
            .frame(maxWidth: breite == nil ? .infinity : nil)
            .background(RoundedRectangle(cornerRadius: 12)
                .fill(gewaehlt ? Zeichenblatt.gewaehltGrund : Zeichenblatt.feld))
            .overlay(RoundedRectangle(cornerRadius: 12)
                .strokeBorder(gewaehlt ? Zeichenblatt.gewaehltRand : Zeichenblatt.linie,
                              lineWidth: 1))
            .contentShape(RoundedRectangle(cornerRadius: 12))
            .opacity(configuration.isPressed ? 0.7 : 1)
    }
}
