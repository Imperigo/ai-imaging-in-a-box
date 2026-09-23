import Foundation
import UIKit

/// **Ein Bild der Mappe als Unterlage unter die Ebenen legen** — der Weg hinter «Darauf
/// skizzieren» (`Bilder/Daraufskizzieren.swift`).
///
/// Die Bytes kommen, wie jedes Bild, über `GET /bild` (`Anfragen.bild`, gelesen mit
/// `liesBild`) — oder, wenn das Bildband dasselbe Bild schon geladen hat, von dort: Es ist
/// dieselbe Datei (`Mappenabgleich` übernimmt eine Grafik nur bei gleichem Namen **und**
/// gleicher Zeit). Die Grösse wird am Bild selbst gelesen, in Bildpunkten (`cgImage`),
/// nicht in Punkten (`size` hinge an `scale`); lässt sie sich nicht lesen, bleibt sie
/// **nicht gemessen** (`nil`), und die Tafel sagt, dass unbekannt ist, ob gestreckt wird.
///
/// Mit der Unterlage wird die **Mappe** vermerkt, aus der das Bild kam (`ordner`): Nur dort
/// gibt es das Bild, und der Kern lehnt das Ablegen in eine andere ab
/// (`Unterlagenangabe.andereMappe`).
///
/// *Gebaut, nicht übersetzt, am Gerät unbestätigt (23.09.2026).*
extension Zeichenstand {

    /// Gibt `nil` zurück, wenn die Unterlage liegt — sonst den Satz, warum nicht. **Eine
    /// Unterlage, die nicht geladen ist, wird nicht gelegt**: Ein Name ohne Bild ginge als
    /// `ueber` hinaus, während auf dem Schirm das leere Blatt stünde — gegen «gerechnet wird,
    /// was sichtbar ist» (Entscheid 7).
    @MainActor
    func legeUnterlage(aus b: Bandbild, titel: String,
                       verbindung: Verbindungsstand) async -> String? {
        let grafik: UIImage
        if let schon = b.grafik {
            grafik = schon
        } else {
            switch await Zeichenstand.holeBild(b.bild, verbindung: verbindung) {
            case .success(let geholt):
                grafik = geholt
            case .failure(let grund):
                return grund.satz
            }
        }
        guard let unterlage = Blattunterlage(bild: b.bild, titel: titel,
                                             ordner: verbindung.ordner,
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
    private static func holeBild(_ name: String,
                                 verbindung: Verbindungsstand) async -> Result<UIImage, Bildfehler> {
        guard let basis = verbindung.adresse else {
            return .failure(Bildfehler(satz: "Nicht gekoppelt — das Bild ist nicht geladen, "
                                       + "es liegt keine Unterlage."))
        }
        let anfrage = Anfragen.bild(name: name,
                                    ordner: verbindung.ordner.isEmpty ? nil : verbindung.ordner,
                                    anmeldung: verbindung.anmeldung)
        switch await verbindung.sender.fuehreAus(anfrage, basis: basis) {
        case .keineAntwort(let grund, _):
            return .failure(Bildfehler(satz: grund))
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
