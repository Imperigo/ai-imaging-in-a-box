import SwiftUI

/// Farben, Schriften und Masse der App — nach dem Blatt «Die Zeichen» der Entwurfsfläche
/// (21./22.09.2026), **an einer Stelle.**
///
/// **Die Farbtöne selbst stehen nicht hier**, sondern im Kern (`Blattfarbe` und
/// `Zeichenart` in `Kern/Pruefzeichen.swift`): Dort werden sie unter Linux gegen die
/// Abschrift des Blatts und gegen die Webseite geprüft
/// (`PruefzeichenTests.testJederFarbtonStehtSoAufDemBlatt`). Bis zur Durchsicht B vom
/// 22.09.2026 standen sie hier als Hex-Ziffern, die keine Probe sah. Diese Datei macht aus
/// ihnen nur SwiftUI-Farben; ein Ton in Hex-Ziffern ausserhalb des Kerns lässt
/// `testDieAppSchreibtKeineFarbtoeneAusserhalbDesKerns` fallen.
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

/// Die Schriften — **die eine Stelle, an der später die eigenen eingesetzt werden.**
///
/// Heute Systemschrift. Entschieden sind IBM Plex Sans/Mono und Instrument Serif (beide
/// OFL, Entscheid 25), und zwar **mitgeliefert, nicht geladen** (Entscheid 20: das geteilte
/// Bild trägt das Zeichen, also muss die Schrift auf dem Gerät liegen). Sobald die Dateien
/// im Paket liegen und registriert sind, wird nur hier getauscht, z. B.
/// `.custom("IBMPlexMono-Regular", size: groesse)`.
enum Schrift {
    /// Titel und Wortzeichen (später Instrument Serif).
    static func titel(_ groesse: CGFloat) -> Font {
        .system(size: groesse, weight: .regular, design: .serif)
    }

    /// Alles Gelesene (später IBM Plex Sans).
    static func text(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        .system(size: groesse, weight: gewicht, design: .default)
    }

    /// Jede Zahl, jeder Dateiname (später IBM Plex Mono) — gleich breite Ziffern, damit
    /// 0.93 und 0.36 untereinander gleich breit sind und ein Sprung auffällt.
    static func zahl(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        .system(size: groesse, weight: gewicht, design: .monospaced)
    }

    /// Die Kopfzeile eines Abschnitts (klein, gesperrt, Grossbuchstaben).
    static let abschnitt = Font.system(size: 12, weight: .semibold)
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
