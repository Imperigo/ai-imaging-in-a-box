import Foundation
import UIKit

/// Die Unterlage eines Bildes holen — **das Vorher des Vergleichs** (Entscheid 17).
///
/// Der Server nennt seit dem 23.09.2026 (Welle 2b) je Bild in `vorher` den Namen des Bildes,
/// über das skizziert wurde (`Mappenbild.vorher`). Die Bytes kommen wie jedes Bild über
/// `GET /bild` unter genau diesem Namen, **aus der Mappe des Bildes** (`Bandbild.mappe`, seit
/// der Durchsicht vom 23.09.2026 — bis dahin aus dem Ordner, der gerade eingestellt war).
/// Gehalten wird nur die zuletzt geladene Unterlage (`Bildbandstand.unterlagen`); was schief
/// ging, steht als Satz daneben (`Bildbandstand.unterlagenSatz`) — **nicht geladen ist nicht
/// «keine Unterlage».**
///
/// **Beim Nachladen geht der alte Satz zuerst weg** (Durchsicht vom 23.09.2026): Bis dahin
/// blieb nach einem Fehlschlag der Satz stehen, und wer das Bild wieder öffnete, las während
/// des Nachladens den alten Fehler, als wäre er der neue. Jetzt steht dann «wird geladen».
/// Am Gerät unbestätigt; eine Probe gibt es nicht (hier nicht übersetzt).
///
/// Warum hier in `Bilder/` und nicht in `Verbindung/Mappenabgleich.swift`: Jene Datei gehörte
/// am 22.09.2026 einer anderen Einheit. Geschickt wird über dieselbe Schnittstelle
/// (`sender.fuehreAus`), gelesen mit dem Kern (`liesBild`); `Verbindungsstand` selbst ist
/// nicht angefasst. Darf später dorthin ziehen.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
extension Verbindungsstand {

    /// Holt die Unterlage `name` aus der Mappe `mappe` (`nil`: die des Starts) — gerufen mit
    /// `Bandbild.vorher` und `Bandbild.mappe` desselben Bildes.
    @MainActor
    func ladeUnterlage(_ name: String, mappe: String?,
                       bildband: Bildbandstand = .gemeinsam) async {
        let schluessel = Bildbandstand.unterlagenSchluessel(name, mappe: mappe)
        // DER ALTE SATZ GEHT ZUERST: Waehrend des Nachladens steht «wird geladen», nicht der
        // Fehler vom letzten Mal.
        bildband.unterlagenSatz[schluessel] = nil
        // IST DIE UNTERLAGE EIN BILD DERSELBEN MAPPE UND SCHON GELADEN, wird sie nicht zweimal
        // geholt (`Bildbandstand.vorherbild` nimmt dann dessen Grafik).
        if bildband.bilder.contains(where: {
            $0.bild == name && $0.mappe == mappe && $0.grafik != nil
        }) { return }
        guard let basis = adresse else {
            bildband.unterlagenSatz[schluessel] = "Nicht gekoppelt — die Unterlage ist nicht geladen."
            return
        }
        let anfrage = Anfragen.bild(name: name, ordner: mappe, anmeldung: anmeldung)
        switch await sender.fuehreAus(anfrage, basis: basis) {
        case .keineAntwort(let grund, _):
            bildband.unterlagenSatz[schluessel] = grund
        case .antwort(let status, let daten):
            do {
                let bytes = try liesBild(status: status, daten: daten)
                guard let grafik = UIImage(data: bytes) else {
                    bildband.unterlagenSatz[schluessel] = "Die Unterlage kam an, liess sich aber nicht als Bild lesen."
                    return
                }
                // NUR EINE: die neue ersetzt die alte (siehe `Bildbandstand.unterlagen`).
                bildband.unterlagen = [schluessel: grafik]
                bildband.unterlagenSatz[schluessel] = nil
            } catch let f as Serverfehler {
                bildband.unterlagenSatz[schluessel] = f.satz
            } catch {
                bildband.unterlagenSatz[schluessel] = "Die Antwort zur Unterlage liess sich nicht lesen."
            }
        }
    }
}
