import Foundation
import UIKit

/// Die Unterlage eines Bildes holen — **das Vorher des Vergleichs** (Entscheid 17).
///
/// Der Server nennt seit dem 22.09.2026 je Bild in `vorher` den Namen des Bildes, über das
/// skizziert wurde (`Mappenbild.vorher`). Die Bytes kommen wie jedes Bild über `GET /bild`
/// unter genau diesem Namen. Gehalten wird nur die zuletzt geladene Unterlage
/// (`Bildbandstand.unterlagen`); was schief ging, steht als Satz daneben
/// (`Bildbandstand.unterlagenSatz`) — **nicht geladen ist nicht «keine Unterlage».**
///
/// Warum hier in `Bilder/` und nicht in `Verbindung/Mappenabgleich.swift`: Jene Datei gehörte
/// am 22.09.2026 einer anderen Einheit. Geschickt wird über dieselbe Schnittstelle
/// (`sender.fuehreAus`), gelesen mit dem Kern (`liesBild`); `Verbindungsstand` selbst ist
/// nicht angefasst. Darf später dorthin ziehen.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
extension Verbindungsstand {

    @MainActor
    func ladeUnterlage(_ name: String, bildband: Bildbandstand = .gemeinsam) async {
        // IST DIE UNTERLAGE EIN BILD DER MAPPE UND SCHON GELADEN, wird sie nicht zweimal
        // geholt (`Bildbandstand.vorherbild` nimmt dann dessen Grafik).
        if bildband.bilder.contains(where: { $0.bild == name && $0.grafik != nil }) { return }
        guard let basis = adresse else {
            bildband.unterlagenSatz[name] = "Nicht gekoppelt — die Unterlage ist nicht geladen."
            return
        }
        let anfrage = Anfragen.bild(name: name, ordner: ordner.isEmpty ? nil : ordner,
                                    anmeldung: anmeldung)
        switch await sender.fuehreAus(anfrage, basis: basis) {
        case .keineAntwort(let grund, _):
            bildband.unterlagenSatz[name] = grund
        case .antwort(let status, let daten):
            do {
                let bytes = try liesBild(status: status, daten: daten)
                guard let grafik = UIImage(data: bytes) else {
                    bildband.unterlagenSatz[name] = "Die Unterlage kam an, liess sich aber nicht als Bild lesen."
                    return
                }
                // NUR EINE: die neue ersetzt die alte (siehe `Bildbandstand.unterlagen`).
                bildband.unterlagen = [name: grafik]
                bildband.unterlagenSatz[name] = nil
            } catch let f as Serverfehler {
                bildband.unterlagenSatz[name] = f.satz
            } catch {
                bildband.unterlagenSatz[name] = "Die Antwort zur Unterlage liess sich nicht lesen."
            }
        }
    }
}
