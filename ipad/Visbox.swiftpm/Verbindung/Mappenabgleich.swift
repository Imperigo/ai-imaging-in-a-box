import Foundation
import UIKit

/// Die Bilder der Mappe holen und ins Bildband legen (`Bildbandstand.gemeinsam`).
///
/// Die Einheit «Bilder» zeigt, diese hier holt: `GET /api/projekt` für die Liste,
/// `GET /bild` für die Bytes. **Nichts wird hier beurteilt** — das Zeichen geht roh weiter
/// (`Bandbild.zeichen`), und ein unbekanntes wird dort nicht geraten.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
extension Verbindungsstand {

    @MainActor
    func ladeMappe(bildband: Bildbandstand = .gemeinsam) async {
        guard let basis = adresse else { return }
        let zielordner = ordner.isEmpty ? nil : ordner
        let antwort = await sender.fuehreAus(
            Anfragen.projekt(ordner: zielordner, anmeldung: anmeldung), basis: basis)
        let sicht: Projektsicht
        switch antwort {
        case .keineAntwort(let satz, _):
            // NICHT ERREICHT IST KEINE LEERE MAPPE: Was schon im Band liegt, bleibt stehen.
            setzeMappenSatz(satz)
            return
        case .antwort(let status, let daten):
            do {
                sicht = try Projektsicht.lies(status: status, daten: daten)
            } catch let f as Serverfehler {
                setzeMappenSatz(f.satz)
                if f.art == .nichtGefunden { bildband.bilder = [] }
                return
            } catch {
                setzeMappenSatz("Die Mappe liess sich nicht lesen.")
                return
            }
        }
        guard let eintraege = sicht.bilder else {
            setzeMappenSatz("Die HomeStation hat keine Bilderliste mitgeschickt.")
            return
        }
        setzeMappenSatz(nil)

        // WAS SCHON GELADEN IST, BLEIBT — aber nur, wenn es dasselbe Bild ist (gleicher Name
        // UND gleiche Zeit). Ein neuer Lauf schreibt unter denselben Namen.
        let alt = Dictionary(bildband.bilder.map { ($0.bild, $0) },
                             uniquingKeysWith: { erstes, _ in erstes })
        var neu: [Bandbild] = []
        for e in eintraege {
            guard let name = e.bild else { continue }
            var b = Bandbild(bild: name, zeichen: e.zeichen ?? "", satz: e.satz,
                             erzeugt: e.erzeugt, vorhanden: e.vorhanden)
            if let frueher = alt[name], frueher.erzeugt == e.erzeugt {
                b.grafik = frueher.grafik
            }
            neu.append(b)
        }
        bildband.bilder = neu

        for b in neu where b.grafik == nil && b.vorhanden != false {
            let bild = await sender.fuehreAus(
                Anfragen.bild(name: b.bild, ordner: zielordner, anmeldung: anmeldung),
                basis: basis)
            guard case .antwort(let status, let daten) = bild,
                  let bytes = try? liesBild(status: status, daten: daten),
                  let grafik = UIImage(data: bytes),
                  let i = bildband.bilder.firstIndex(where: { $0.bild == b.bild }) else {
                continue
            }
            bildband.bilder[i].grafik = grafik
        }
    }
}
