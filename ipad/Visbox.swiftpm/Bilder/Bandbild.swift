import SwiftUI
import UIKit

/// Ein Bild der Mappe, wie das Bildband es zeigt — **nur, was der Server sagt.**
///
/// Die Felder folgen `bilder[]` aus `GET /api/projekt` (`docs/VISBOX_PROTOKOLL.md`, §4).
/// Wer die Antwort liest (Einheit «Verbindung»), baut daraus `Bandbild`-Werte und legt sie
/// in `Bildbandstand.gemeinsam`; die Bildbytes kommen über `GET /bild`.
///
/// **Was heute fehlt, und es steht hier, damit es nicht als Null angezeigt wird:** Das
/// Protokoll liefert je Bild **keine Zahl** (Stand 22.09.2026, §4: `bild, schicht, zeichen,
/// satz, erzeugt, herkunft, vorhanden, basis`). `pruefzahl` ist darum heute immer `nil`,
/// und das Prüfzeichen schreibt «ohne Zahl» — nie «0.00». Entscheid 16 («Farbe, Wort und
/// Zahl — immer») ist damit am Bild erst erfüllt, wenn der Server die Zahl mitschickt.
struct Bandbild: Identifiable, Equatable {
    /// Der Dateiname relativ zum Projektordner (Feld `bild`). Er ist zugleich die Kennung.
    let bild: String
    /// Das Zeichen, roh, wie es kam (`bestanden`, `durchgefallen`, `nicht-gemessen` — oder
    /// ein unbekanntes, das nicht geraten wird).
    let zeichen: String
    /// Der Satz zum Zeichen (Feld `satz`).
    let satz: String?
    /// Wann es entstand (Feld `erzeugt`, Weltzeit, `JJJJ-MM-TTTHH:MM:SSZ`).
    let erzeugt: String?
    /// Die Zahl zum Urteil — `nil` heisst **nicht übertragen**, nie 0.
    var pruefzahl: Double? = nil
    /// Beim Entwerfen: der Abstand zum Modell — `nil` heisst nicht übertragen.
    var unterschied: Double? = nil
    /// Die Hinweise des Servers zu diesem Bild, unverändert.
    var hinweise: [String] = []
    /// Ob die Datei da ist: `true`, `false` (die Mappe nennt sie, sie fehlt) oder `nil`
    /// (nicht gefragt) — die drei Antworten, auch hier.
    var vorhanden: Bool? = nil
    /// Die geladenen Bildbytes; `nil`, solange nichts geladen ist.
    var grafik: UIImage? = nil
    /// Das Vergleichsbild «aus dem Modell» (die Basis eines Bildes der zweiten Stufe),
    /// wenn eines geladen ist.
    var vorher: UIImage? = nil

    var id: String { bild }

    /// Das Prüfzeichen dieses Bildes in einer Lesart. Entschieden wird im Kern.
    func pruefzeichen(_ lesart: Bildlesart) -> Pruefzeichen {
        Pruefzeichen(zeichen: zeichen, lesart: lesart, pruefzahl: pruefzahl,
                     unterschied: unterschied, hinweise: hinweise)
    }

    /// Der Name nach der Zeit (Entscheid 19), in Ortszeit: «21.09.2026 · 14:03».
    ///
    /// Ohne lesbare Zeit der Dateiname — **nicht** eine erfundene Zeit.
    var zeitname: String {
        guard let roh = erzeugt, let datum = Bandbild.lies.date(from: roh) else { return bild }
        return Bandbild.schreib.string(from: datum)
    }

    private static let lies: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    private static let schreib: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale(identifier: "de_CH")
        f.dateFormat = "dd.MM.yyyy · HH:mm"
        return f
    }()
}

/// Was im Bildband gewählt und benannt ist — die Stelle, an der die anderen Einheiten
/// Bilder hineinlegen und die Wahl der Varianten ablesen.
///
/// **Eigene Namen bleiben auf dem Gerät.** Der Server kennt keinen Weg, ein Bild
/// umzubenennen (Protokoll §3), und der Dateiname entsteht dort aus der Uhrzeit. Ein Name,
/// den man hier vergibt (Entscheid 19), ist darum eine Beschriftung dieses iPads und nicht
/// der Mappe; ein zweites Gerät sieht ihn nicht. *Am Gerät unbestätigt.*
final class Bildbandstand: ObservableObject {
    static let gemeinsam = Bildbandstand()

    private static let namenSchluessel = "bilder.eigene-namen"

    @Published var bilder: [Bandbild] = []
    @Published var gewaehlt: String?
    /// Prüfen oder Entwerfen, **je Bild** — der Schalter sitzt am Bild (Entscheid 15).
    @Published var lesarten: [String: Bildlesart] = [:]
    /// Drei Startwerte oder drei Ebenen (Entscheid 32). Hier nur gewählt und angezeigt;
    /// die Bestellung liest es von hier.
    @Published var variantenquelle: Variantenquelle = .startwerte
    @Published private(set) var eigeneNamen: [String: String]

    init() {
        eigeneNamen = UserDefaults.standard.dictionary(forKey: Bildbandstand.namenSchluessel)
            as? [String: String] ?? [:]
    }

    /// Der Name, den ein Mensch sieht: der eigene, sonst der nach der Zeit.
    func name(_ b: Bandbild) -> String {
        eigeneNamen[b.bild] ?? b.zeitname
    }

    /// Einen eigenen Namen vergeben; ein leerer nimmt ihn zurück (dann gilt wieder die Zeit).
    func benenne(_ b: Bandbild, als name: String) {
        let sauber = name.trimmingCharacters(in: .whitespacesAndNewlines)
        eigeneNamen[b.bild] = sauber.isEmpty ? nil : sauber
        UserDefaults.standard.set(eigeneNamen, forKey: Bildbandstand.namenSchluessel)
    }

    /// Die Lesart eines Bildes. **Vorgabe ist Prüfen**: Ein Bild, das ohne Prüfung
    /// entstand, zeigt dann «nicht gemessen» — und nicht still ein blaues Zeichen, das der
    /// Server nie gesetzt hat.
    func lesart(_ b: Bandbild) -> Bildlesart {
        lesarten[b.bild] ?? .pruefen
    }

    func setzeLesart(_ l: Bildlesart, fuer b: Bandbild) {
        lesarten[b.bild] = l
    }
}
