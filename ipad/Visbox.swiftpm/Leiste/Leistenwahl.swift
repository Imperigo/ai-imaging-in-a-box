import SwiftUI

/// Das Werkzeug in der Hand.
///
/// Der Radierer ist zweifach (Entscheid 5: ganze Striche und flächig, umschaltbar); die
/// Hand schiebt und zoomt (Entscheid 4: der Finger zeichnet nie).
enum Leistenwerkzeug: String, CaseIterable, Identifiable {
    case stift
    case strichradierer
    case flaechenradierer
    case hand

    var id: String { rawValue }

    var name: String {
        switch self {
        case .stift: return "Stift"
        case .strichradierer: return "Radierer: ganze Striche"
        case .flaechenradierer: return "Radierer: flächig wegwischen"
        case .hand: return "Schieben und zoomen"
        }
    }

    /// Der Name eines SF-Symbols. **Ob es ihn in iOS 17 gibt, ist am Gerät unbestätigt**
    /// (Durchsicht B, 22.09.2026): Der Übersetzer prüft Symbolnamen nicht, ein falscher
    /// zeigt zur Laufzeit ein leeres Feld. Die Bezeichnung für den Bildschirmleser
    /// (`name`) trägt der Knopf unabhängig davon.
    var symbol: String {
        switch self {
        case .stift: return "pencil.tip"
        case .strichradierer: return "eraser.line.dashed"
        case .flaechenradierer: return "eraser"
        case .hand: return "hand.raised"
        }
    }
}

/// Drei Strichstärken. Der Druck des Stifts steuert die Breite darüber hinaus
/// (Entscheid 3); was hier gewählt ist, ist die Grundbreite.
enum Leistenstrich: String, CaseIterable, Identifiable {
    case duenn
    case mittel
    case dick

    var id: String { rawValue }

    var name: String {
        switch self {
        case .duenn: return "Dünner Strich"
        case .mittel: return "Mittlerer Strich"
        case .dick: return "Dicker Strich"
        }
    }

    /// Die Dicke des Strichs im Knopf — nur die Abbildung, keine Zeichenbreite.
    var bildDicke: CGFloat {
        switch self {
        case .duenn: return 2
        case .mittel: return 4.5
        case .dick: return 8
        }
    }
}

/// Was das eine Seitenfeld zeigt (Blätter «Main», «Skizzen»): **die Ebenen oder die
/// Mappe** — umschaltbar, nie beides nebeneinander. Zwei Seitenfelder nähmen dem Blatt im
/// Querformat 680 pt; eines, das umschaltet, lässt ihm die Mitte.
enum Seitenfeldwahl: String, CaseIterable, Identifiable {
    case ebenen
    case mappe

    var id: String { rawValue }

    var name: String {
        switch self {
        case .ebenen: return "Ebenen"
        case .mappe: return "Mappe"
        }
    }
}

/// Auf welcher Seite die Leiste im Querformat sitzt (Entscheid 9).
enum Leistenseite: String {
    case links
    case rechts

    var andere: Leistenseite { self == .links ? .rechts : .links }
}

/// Was in der Leiste gewählt ist — **eine** Stelle, die die Leiste schreibt und die
/// Zeichenfläche liest.
///
/// **Warum ein gemeinsamer Stand (`gemeinsam`) und keine Übergabe von oben.** Die Leiste
/// und die Zeichenfläche entstanden in zwei Einheiten gleichzeitig; über
/// `Leistenwahl.gemeinsam` finden sie sich, ohne dass eine die Datei der anderen ändern
/// muss. `Startansicht` übergibt seit dem 22.09.2026 genau diesen Stand an den
/// `Arbeitsplatz`, und `Zeichenstand.gemeinsam` liest ebenfalls ihn — es gibt einen.
///
/// Die Seite der Leiste wird auf dem Gerät gemerkt — eine Linkshänderin soll sie nicht bei
/// jedem Start umlegen müssen. Werkzeug und Strich beginnen jedes Mal mit dem Stift.
final class Leistenwahl: ObservableObject {
    static let gemeinsam = Leistenwahl()

    private static let seitenSchluessel = "leiste.seite"

    @Published var werkzeug: Leistenwerkzeug = .stift
    @Published var strich: Leistenstrich = .mittel
    @Published var seite: Leistenseite {
        didSet { Leistenwahl.merke(seite) }
    }
    /// Vollbild (Entscheid 29): nur das Bild, keine Leiste, kein Seitenfeld.
    @Published var vollbild = false
    /// Was im Seitenfeld steht. Hier und nicht im Zustand einer Ansicht, damit es das
    /// Drehen und das Vollbild übersteht.
    @Published var seitenfeld: Seitenfeldwahl = .ebenen

    init(seite: Leistenseite? = nil) {
        self.seite = seite ?? Leistenwahl.gemerkteSeite()
    }

    private static func gemerkteSeite() -> Leistenseite {
        let roh = UserDefaults.standard.string(forKey: seitenSchluessel) ?? ""
        return Leistenseite(rawValue: roh) ?? .links
    }

    private static func merke(_ seite: Leistenseite) {
        UserDefaults.standard.set(seite.rawValue, forKey: seitenSchluessel)
    }
}
