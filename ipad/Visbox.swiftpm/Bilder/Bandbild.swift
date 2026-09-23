import SwiftUI
import UIKit

/// Ein Bild der Mappe, wie das Bildband es zeigt — **nur, was der Server sagt.**
///
/// Die Angaben kommen unverändert aus `bilder[]` von `GET /api/projekt`
/// (`docs/VISBOX_PROTOKOLL.md`, §4), gelesen im Kern (`Mappenbild`). Die Einheit
/// «Verbindung» legt sie in `Bildbandstand.gemeinsam` (`Verbindung/Mappenabgleich.swift`);
/// die Bildbytes kommen über `GET /bild`.
///
/// **Seit dem 22.09.2026 mit Zahl:** Der Server schickt je Bild `score` und `schwelle`,
/// den eigenen Namen, ob es ein Entwurf ist, die Reihe und die Hinweise. Das Prüfzeichen
/// entsteht daraus im Kern (`Mappenbild.pruefzeichen`) — dort ist bewacht, dass ein Bild
/// ohne Urteil **keine** Zahl zeigt, auch wenn eine mitkommt.
struct Bandbild: Identifiable, Equatable {
    /// Was der Server über das Bild sagt, wie es kam.
    let angaben: Mappenbild
    /// Der Dateiname relativ zum Projektordner (Feld `bild`). Er ist zugleich die Kennung;
    /// ein Eintrag ohne ihn wird kein `Bandbild` (siehe `Mappenabgleich`).
    let bild: String
    /// **Die Mappe, aus der dieses Bild geladen wurde** — der Projektordner auf der
    /// HomeStation, mit dem `ladeMappe` die Liste holte. `nil` heisst hier nicht «unbekannt»,
    /// sondern, wie beim Ordner jeder Anfrage (`Anfragen.bild(ordner:)`) und bei
    /// `Blattunterlage.ordner`: **die Mappe des Starts**. Die Mappe ist immer bekannt — sie
    /// ist die, die gefragt wurde.
    ///
    /// Durchsicht der Welle 2b (23.09.2026): Bis dahin trug das Bandbild seine Mappe nicht,
    /// und wer es danach holte (die Unterlage des Vergleichs, «Darauf skizzieren»), nahm den
    /// Ordner, der **jetzt** im Ordnerfeld steht. Das Feld lässt sich ändern, ohne dass die
    /// Mappe neu geladen wird — dann kam das Bild gleichen Namens aus einer anderen Mappe.
    /// Gesetzt nur von `Verbindung/Mappenabgleich.swift`; dass es dort richtig ankommt, ist
    /// nicht übersetzt (23.09.2026), ohne Probe und am Gerät unbestätigt.
    let mappe: String?
    /// Die geladenen Bildbytes; `nil`, solange nichts geladen ist.
    var grafik: UIImage? = nil
    /// **Der Name der Unterlage** — des Bildes, über das skizziert wurde (Feld `vorher`,
    /// Entscheid 17), gelesen im Kern (`Mappenbild.vorher`, dort mit Probe). `nil` heisst:
    /// keine, oder der Server nennt sie nicht — nicht «es gibt keine».
    ///
    /// Bis zum 23.09.2026 (Welle 2b) war hier ein Bild-Feld, das nirgends gesetzt wurde: Der
    /// Vergleich Vorher/Nachher war im Produkt nie zu sehen (Durchsicht der Verdrahtung). Die Bytes
    /// liegen jetzt am `Bildbandstand` (`vorherbild`), nicht hier — `ladeMappe` baut die
    /// Bandbilder bei jedem Laden neu und übernimmt nur `grafik`; ein Bild hier ginge dabei
    /// jedes Mal verloren.
    var vorher: String? { angaben.vorher }

    var id: String { bild }

    var satz: String? { angaben.satz }
    var erzeugt: String? { angaben.erzeugt }
    /// `true`, `false` (die Mappe nennt es, die Datei fehlt) oder `nil` (nicht gefragt).
    var vorhanden: Bool? { angaben.vorhanden }

    /// Das Prüfzeichen dieses Bildes in einer Lesart. Entschieden wird im Kern.
    func pruefzeichen(_ lesart: Bildlesart) -> Pruefzeichen {
        angaben.pruefzeichen(lesart)
    }

    /// Der Name nach der Zeit (Entscheid 19), in Ortszeit: «21.09.2026 · 14:03».
    ///
    /// Ohne lesbare Zeit der Dateiname — **nicht** eine erfundene Zeit.
    var zeitname: String {
        Bandbild.zeitname(erzeugt) ?? bild
    }

    /// Eine Zeit des Servers (`JJJJ-MM-TTTHH:MM:SSZ`) in Ortszeit, oder `nil`.
    static func zeitname(_ roh: String?) -> String? {
        guard let roh = roh, let datum = lies.date(from: roh) else { return nil }
        return schreib.string(from: datum)
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

/// Die Mappe, wie die App sie gerade kennt — und was im Seitenfeld dazu gewählt ist.
///
/// **Eigene Namen liegen seit dem 22.09.2026 in der Mappe**, nicht mehr auf dem Gerät:
/// Der Server hat `POST /api/benennen` (Protokoll §3). Bis dahin merkte sich dieses iPad
/// Namen in seinen Einstellungen — ein zweites Gerät sah sie nicht, und die Mappe wusste
/// nichts davon. Solche alten Namen werden nicht mehr gelesen; wer einen braucht, gibt ihn
/// neu (er landet dann in der Mappe).
final class Bildbandstand: ObservableObject {
    static let gemeinsam = Bildbandstand()

    @Published var bilder: [Bandbild] = []
    /// Die Skizzen der Mappe. `nil` heisst: **nicht gelesen** — nicht «keine Skizzen». Warum
    /// nicht, sagt `skizzenLage` (seit Runde 7b kann `nil` auch «nicht lesbar» heissen).
    @Published var skizzen: [Mappenskizze]?
    /// **Wie die Skizzenliste beim letzten Laden stand** — nicht geliefert, nicht lesbar oder
    /// gelesen; `nil`: noch nie geladen. Gesetzt in `ladeMappe`, an derselben Stelle wie die
    /// Liste; der Satz dazu kommt aus dem Kern (`Mappenlage.skizzenlistensatz`).
    ///
    /// **Ein Stand, nicht zwei** (Durchsicht der Runden 7b und 7c, 23.09.2026): Die Lage lag
    /// erst in einem eigenen globalen Stand neben dem Bildband, dann als angehängter Wert der
    /// Objective-C-Laufzeit an ihm. Jetzt ist sie ein gewöhnliches Feld — wer den Bildband
    /// beobachtet, zeichnet bei einer Änderung neu. *Unübersetzt hier, am Gerät unbestätigt.*
    @Published var skizzenLage: Listenlage?
    /// Die Standnummer der Mappe, für `von_stand` beim Benennen. `nil`: nicht geführt.
    @Published var standNr: Int?
    @Published var projektname: String?
    @Published var gewaehlt: String?
    /// Prüfen oder Entwerfen, **je Bild** — der Schalter sitzt am Bild (Entscheid 15).
    @Published var lesarten: [String: Bildlesart] = [:]
    /// Was die nächste Bestellung tut: **Prüfen oder Entwerfen** (Blatt «Main», «Was die
    /// Skizze tut»; Entscheid 30). Vorgabe Prüfen — schnell und ungeprüft muss man wählen.
    @Published var bestellart: Bildlesart = .pruefen
    /// Drei Startwerte oder drei Ebenen (Entscheid 32). Liest die Bestellung — und das
    /// Ablegen: Bei «Drei Ebenen» geht jede sichtbare Ebene als eigene Skizze hinaus
    /// (`Variantenquelle.ausgabeart`).
    @Published var variantenquelle: Variantenquelle = .startwerte
    /// Die offenen Skizzen, die als Ebenen-Reihe gerechnet werden sollen.
    @Published var reihe: [String] = []
    /// Was zur letzten Handlung (Rechnen, Abbrechen, Benennen) zu sagen ist.
    @Published var quittung: Handlungsquittung?
    /// Ob für den laufenden Lauf ein Abbruch **verlangt** ist — nicht, ob er gewirkt hat
    /// (das steht nach dem Lauf in dessen Ergebnis). Zurückgesetzt, wenn der Lauf endet.
    @Published var abbruchVerlangt = false
    /// Ob gerade eine Handlung unterwegs ist — dann ist derselbe Knopf nicht noch einmal
    /// zu haben.
    @Published var sendet = false
    /// Die zuletzt geladene Unterlage (Name → Bild) — **nur eine**, damit das Gedächtnis
    /// nicht mit jedem geöffneten Bild wächst (gesetzt, nicht gemessen). Geladen von
    /// `Verbindungsstand.ladeUnterlage` (`Bilder/Unterlage.swift`).
    ///
    /// Geführt unter Mappe **und** Name (`unterlagenSchluessel`): Gleicher Name in einer
    /// anderen Mappe ist ein anderes Bild (23.09.2026; bis dahin nur unter dem Namen).
    @Published var unterlagen: [String: UIImage] = [:]
    /// Warum eine Unterlage nicht da ist, je Mappe und Name — der Satz des Servers oder der
    /// Leitung. Fehlt ein Eintrag und ein Bild, ist sie **noch nicht geladen**, nicht «keine».
    /// Beim Nachladen wird der alte Satz zuerst weggenommen (`ladeUnterlage`).
    @Published var unterlagenSatz: [String: String] = [:]

    /// Unter welchem Schlüssel eine Unterlage steht: Mappe und Name, getrennt durch ein
    /// Zeichen, das in keinem Pfad und keinem Dateinamen vorkommt.
    static func unterlagenSchluessel(_ name: String, mappe: String?) -> String {
        (mappe ?? "") + "\u{0}" + name
    }

    /// Der Satz, warum die Unterlage eines Bildes nicht da ist — `nil`, wenn es keinen gibt.
    func satzZurUnterlage(_ b: Bandbild) -> String? {
        guard let name = b.vorher else { return nil }
        return unterlagenSatz[Bildbandstand.unterlagenSchluessel(name, mappe: b.mappe)]
    }

    /// Der Name, den ein Mensch sieht: der eigene aus der Mappe, sonst der nach der Zeit.
    func name(_ b: Bandbild) -> String {
        b.angaben.titel ?? b.zeitname
    }

    /// Der Name einer Skizze: der eigene, sonst die Zeit, sonst der Dateiname — und wenn
    /// nicht einmal der kam, **das**, statt einer leeren Zeile.
    func name(_ s: Mappenskizze) -> String {
        s.titel ?? Bandbild.zeitname(s.erzeugt) ?? s.skizze ?? "Skizze ohne Dateinamen"
    }

    /// Die Lesart eines Bildes: die am Bild gewählte, sonst die **aus der Mappe** — ein
    /// Entwurf als Entwurf (blau), alles andere geprüft (`Mappenbild.vorgabeLesart`).
    func lesart(_ b: Bandbild) -> Bildlesart {
        lesarten[b.bild] ?? b.angaben.vorgabeLesart
    }

    func setzeLesart(_ l: Bildlesart, fuer b: Bandbild) {
        lesarten[b.bild] = l
    }

    /// Das Vorher eines Bildes: die geladene Unterlage **aus seiner Mappe** — oder, wenn die
    /// Unterlage selbst ein Bild derselben Mappe ist, dessen schon geladene Grafik. `nil`,
    /// solange nichts geladen ist.
    func vorherbild(_ b: Bandbild) -> UIImage? {
        guard let name = b.vorher else { return nil }
        return unterlagen[Bildbandstand.unterlagenSchluessel(name, mappe: b.mappe)]
            ?? bilder.first(where: { $0.bild == name && $0.mappe == b.mappe })?.grafik
    }

    /// Die Bilder einer Reihe, nach ihrer Nummer.
    func reihenbilder(_ gruppe: String) -> [Bandbild] {
        bilder.filter { $0.angaben.variantengruppe?.id == gruppe }
            .sorted { ($0.angaben.variantengruppe?.nummer ?? Int.max)
                    < ($1.angaben.variantengruppe?.nummer ?? Int.max) }
    }

    /// Eine offene Skizze in die Reihe nehmen oder herausnehmen — **höchstens drei**
    /// (`Rechenbestellung.reihenlaenge`).
    func schalteReihe(_ name: String) {
        if let i = reihe.firstIndex(of: name) {
            reihe.remove(at: i)
        } else if reihe.count < Rechenbestellung.reihenlaenge {
            reihe.append(name)
        }
    }
}
