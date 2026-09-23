import Foundation
import UIKit

/// **Ein Bild der Mappe als Unterlage unter die Ebenen legen** — der Weg hinter «Darauf
/// skizzieren» (`Bilder/Daraufskizzieren.swift`).
///
/// **Die Bytes kommen immer frisch über `GET /bild`** (`Anfragen.bild`, gelesen mit
/// `liesBild`), aus der Mappe, in die jetzt abgelegt würde — und **genau diese Mappe** wird
/// mit der Unterlage vermerkt (`ordner`). Der Ordner wird dafür **einmal** gelesen und für
/// Anfrage und Vermerk genommen; ein Tastendruck im Ordnerfeld dazwischen trennt die beiden
/// nicht. Nur in dieser Mappe gibt es das Bild, und der Kern lehnt das Ablegen in eine
/// andere ab (`Unterlagenangabe.andereMappe`).
///
/// **Warum nicht mehr das Bild aus dem Bildband** (Befund Durchsicht der Welle 2b,
/// 23.09.2026): Bis dahin nahm dieser Weg die Grafik des Bildbands, wenn sie schon geladen
/// war, und vermerkte den Ordner **zum Zeitpunkt des Legens**. Ein `Bandbild` trug damals
/// nicht, aus welcher Mappe es geladen wurde (seit dem 23.09.2026 trägt es sie:
/// `Bandbild.mappe`, und hier wird sie geprüft), und das Ordnerfeld lässt sich ändern, ohne
/// dass die Mappe neu geladen wird — dann lag das Bild der einen Mappe unter dem Blatt, und
/// `ueber` zeigte in die andere (dort womöglich auf ein anderes Bild gleichen Namens). Auch
/// in derselben Mappe kann ein neuer Lauf unter demselben Namen schreiben
/// (`Mappenabgleich`). Frisch geholt liegt unter dem Blatt, was die HomeStation unter
/// diesem Namen **jetzt** hat. Was das kostet: ein Bild mehr über die Leitung je «Darauf
/// skizzieren», und **ohne Verbindung wird keine Unterlage gelegt** — auch wenn das
/// Bildband das Bild zeigt (der Satz sagt es).
///
/// Die Grösse wird am Bild selbst gelesen, in Bildpunkten (`cgImage`), nicht in Punkten
/// (`size` hinge an `scale`); lässt sie sich nicht lesen, bleibt sie **nicht gemessen**
/// (`nil`), und die Tafel sagt, dass unbekannt ist, ob gestreckt wird.
///
/// *Gebaut, nicht übersetzt, am Gerät unbestätigt, ohne Probe (23.09.2026).*
extension Zeichenstand {

    /// Gibt `nil` zurück, wenn die Unterlage liegt — sonst den Satz, warum nicht. **Eine
    /// Unterlage, die nicht geladen ist, wird nicht gelegt**: Ein Name ohne Bild ginge als
    /// `ueber` hinaus, während auf dem Schirm das leere Blatt stünde — gegen «gerechnet wird,
    /// was sichtbar ist» (Entscheid 7).
    @MainActor
    func legeUnterlage(aus b: Bandbild, titel: String,
                       verbindung: Verbindungsstand) async -> String? {
        // EINMAL GELESEN, FUER ANFRAGE UND VERMERK: leer heisst die Mappe des Starts.
        let mappe: String? = verbindung.ordner.isEmpty ? nil : verbindung.ordner
        // DIE MAPPE DES BILDES, HIER GEPRUEFT UND NICHT NUR IN DER ANSICHT (23.09.2026):
        // `Daraufskizzieren` sperrt den Knopf schon, aber zwischen jener Pruefung und dem
        // Lesen oben lag ein Zeitfenster. Stammt das Bild aus einer anderen Mappe als der
        // eingestellten, wird nichts gelegt — dieselbe Regel, dieselben Worte.
        guard b.mappe == mappe else {
            return "Dieses Bild stammt aus \(Daraufskizzieren.wo(b.mappe)); eingestellt ist "
                + "\(Daraufskizzieren.wo(mappe)). Es liegt keine Unterlage."
        }
        let grafik: UIImage
        switch await Zeichenstand.holeBild(b.bild, mappe: mappe, verbindung: verbindung) {
        case .success(let geholt):
            grafik = geholt
        case .failure(let grund):
            return grund.satz
        }
        guard let unterlage = Blattunterlage(bild: b.bild, titel: titel,
                                             ordner: mappe,
                                             breite: grafik.cgImage?.width,
                                             hoehe: grafik.cgImage?.height) else {
            return "Das Bild hat keinen Dateinamen und kann keine Unterlage sein."
        }
        legeUnterlage(unterlage, bild: grafik)
        return nil
    }

    /// Ein Satz, warum ein Bild nicht kam — als Fehler, damit `Result` ihn tragen kann.
    struct Bildfehler: Error {
        let satz: String
    }

    @MainActor
    private static func holeBild(_ name: String, mappe: String?,
                                 verbindung: Verbindungsstand) async -> Result<UIImage, Bildfehler> {
        guard let basis = verbindung.adresse else {
            return .failure(Bildfehler(satz: "Nicht gekoppelt — das Bild ist nicht geladen, "
                                       + "es liegt keine Unterlage."))
        }
        let anfrage = Anfragen.bild(name: name, ordner: mappe,
                                    anmeldung: verbindung.anmeldung)
        switch await verbindung.sender.fuehreAus(anfrage, basis: basis) {
        case .keineAntwort(let grund, _):
            // AUCH WENN DAS BILDBAND DAS BILD ZEIGT: Es ist nicht aus dieser Mappe geholt.
            return .failure(Bildfehler(satz: grund + " Das Bild ist nicht aus der Mappe "
                                       + "geholt — es liegt keine Unterlage."))
        case .antwort(let status, let daten):
            do {
                let bytes = try liesBild(status: status, daten: daten)
                guard let grafik = UIImage(data: bytes) else {
                    return .failure(Bildfehler(
                        satz: "Das Bild kam an, liess sich aber nicht als Bild lesen."))
                }
                return .success(grafik)
            } catch let f as Serverfehler {
                return .failure(Bildfehler(satz: f.satz))
            } catch {
                return .failure(Bildfehler(satz: "Die Antwort zum Bild liess sich nicht lesen."))
            }
        }
    }
}
