import Foundation
import UIKit

/// Die Mappe holen und ins Bildband legen (`Bildbandstand.gemeinsam`) — **und die drei
/// Handlungen, die an der Mappe etwas ändern:** rechnen lassen, abbrechen, Namen geben.
///
/// Die Einheit «Bilder» zeigt, diese hier holt und schickt: `GET /api/projekt` für die
/// Liste, `GET /bild` für die Bytes, `POST /api/rechne(-skizze)`, `/api/abbrechen`,
/// `/api/benennen`. **Nichts wird hier beurteilt** — was eine Antwort heisst, liest der Kern
/// (`Mappenlage`, `Mappenbild`, `Handlungsquittung`), und dort ist es geprüft.
///
/// Gesendet wird über die bestehende Schnittstelle (`sender.fuehreAus`); `Verbindungsstand`
/// und `Sender` selbst sind hier nicht angefasst.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
extension Verbindungsstand {

    @MainActor
    func ladeMappe(bildband: Bildbandstand = .gemeinsam) async {
        guard let basis = adresse else { return }
        let zielordner = ordner.isEmpty ? nil : ordner
        let antwort = await sender.fuehreAus(
            Anfragen.projekt(ordner: zielordner, anmeldung: anmeldung), basis: basis)
        let lage: Mappenlage
        switch antwort {
        case .keineAntwort(let satz, _):
            // NICHT ERREICHT IST KEINE LEERE MAPPE: Was schon im Band liegt, bleibt stehen.
            setzeMappenSatz(satz)
            return
        case .antwort(let status, let daten):
            do {
                lage = try Mappenlage.lies(status: status, daten: daten)
            } catch let f as Serverfehler {
                setzeMappenSatz(f.satz)
                if f.art == .nichtGefunden {
                    bildband.bilder = []
                    bildband.skizzen = nil
                    bildband.standNr = nil
                }
                return
            } catch {
                setzeMappenSatz("Die Mappe liess sich nicht lesen.")
                return
            }
        }
        bildband.projektname = lage.name
        bildband.standNr = lage.standNr
        // NICHT GELIEFERT BLEIBT NICHT GELIEFERT: Kommt keine Skizzenliste, steht keine
        // leere da, sondern die Anzeige sagt, dass keine kam (`skizzen == nil`).
        bildband.skizzen = lage.skizzen
        bildband.reihe = bildband.reihe.filter { name in
            lage.skizzen?.contains { $0.skizze == name && $0.stand == .offen } ?? false
        }
        guard let eintraege = lage.bilder else {
            setzeMappenSatz("Die HomeStation hat keine Bilderliste mitgeschickt.")
            return
        }

        // WAS SCHON GELADEN IST, BLEIBT — aber nur, wenn es dasselbe Bild ist (gleicher Name,
        // gleiche Zeit UND gleiche Mappe). Ein neuer Lauf schreibt unter denselben Namen, und
        // eine andere Mappe kann denselben Namen tragen (23.09.2026).
        let alt = Dictionary(bildband.bilder.map { ($0.bild, $0) },
                             uniquingKeysWith: { erstes, _ in erstes })
        var neu: [Bandbild] = []
        var ohneNamen = 0
        for e in eintraege {
            // EIN EINTRAG OHNE DATEINAMEN lässt sich weder laden noch benennen. Er wird nicht
            // gezeigt — aber gezählt und gesagt, statt still zu fehlen.
            guard let name = e.bild, !name.isEmpty else {
                ohneNamen += 1
                continue
            }
            // DAS BILD TRAEGT SEINE MAPPE: die, aus der diese Liste kam (`Bandbild.mappe`).
            var b = Bandbild(angaben: e, bild: name, mappe: zielordner)
            if let frueher = alt[name], frueher.erzeugt == e.erzeugt,
               frueher.mappe == zielordner {
                b.grafik = frueher.grafik
            }
            neu.append(b)
        }
        bildband.bilder = neu
        setzeMappenSatz(ohneNamen == 0 ? nil
            : "\(ohneNamen) Bildeinträge der Mappe tragen keinen Dateinamen und sind hier nicht gezeigt.")

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

    // --------------------------------------------------------- rechnen, abbrechen, benennen

    /// «Rechnen lassen» — in der Lesart, die im Seitenfeld gewählt ist (Prüfen/Entwerfen).
    ///
    /// Die Antwort heisst nur **gestartet**; was daraus wird, zeigt der Laufstand. Er wird
    /// darum gleich danach neu gefragt (`pruefe`), statt auf die nächste Runde zu warten.
    @MainActor
    func bestelle(_ bestellung: Rechenbestellung, lesart: Bildlesart) async -> Handlungsquittung {
        let quittung = await schicke { ordner, anmeldung in
            try bestellung.anfrage(lesart: lesart, ordner: ordner, anmeldung: anmeldung)
        } lies: { status, daten in
            Handlungsquittung.rechnen(status: status, daten: daten)
        }
        await pruefe()
        return quittung
    }

    /// «Abbrechen» (Entscheid 31). **Verlangt ist nicht gewirkt**: Der Schritt, der gerade
    /// rechnet, rechnet zu Ende; was fertig ist, bleibt in der Mappe (Entscheid 14).
    @MainActor
    func brichLaufAb() async -> Handlungsquittung {
        let quittung = await schicke { _, anmeldung in
            try Anfragen.abbrechen(anmeldung: anmeldung)
        } lies: { status, daten in
            Handlungsquittung.abbrechen(status: status, daten: daten)
        }
        await pruefe()
        return quittung
    }

    /// «Namen geben» (Entscheid 19) — **in die Mappe**, mit der Standnummer der zuletzt
    /// geladenen Mappe (`von_stand`): Hat drüben inzwischen jemand anderes gespeichert, wird
    /// abgewiesen statt überschrieben (Protokoll §6). Danach wird die Mappe neu geladen —
    /// auch nach einer Abweisung, damit der neue Stand dasteht, über den neu entschieden
    /// wird. Die Datei behält ihren Namen.
    @MainActor
    func benenne(bild: String? = nil, skizze: String? = nil, titel: String,
                 bildband: Bildbandstand = .gemeinsam) async -> Handlungsquittung {
        let sauber = titel.trimmingCharacters(in: .whitespacesAndNewlines)
        let stand = bildband.standNr
        let quittung = await schicke { ordner, anmeldung in
            // LEER NIMMT DEN NAMEN ZURUECK: Das Protokoll will dafür `null`, kein "".
            try Anfragen.benennen(bild: bild, skizze: skizze, titel: sauber.isEmpty ? nil : sauber,
                                  vonStand: stand, ordner: ordner, anmeldung: anmeldung)
        } lies: { status, daten in
            Handlungsquittung.benennen(status: status, daten: daten)
        }
        if quittung.ausgang != .nichtGesendet {
            await ladeMappe(bildband: bildband)
        }
        return quittung
    }

    /// Baut, schickt und liest **eine** Handlung — mit denselben vier Ausgängen für alle.
    @MainActor
    private func schicke(_ baue: (String?, Anmeldung?) throws -> Anfrage,
                         lies: (Int, Data) -> Handlungsquittung) async -> Handlungsquittung {
        guard let basis = adresse else {
            return Handlungsquittung(ausgang: .nichtGesendet,
                                     satz: "Nicht gekoppelt — es ging nichts hinaus.")
        }
        let anfrage: Anfrage
        do {
            anfrage = try baue(ordner.isEmpty ? nil : ordner, anmeldung)
        } catch let f as Rumpffehler {
            return Handlungsquittung(ausgang: .nichtGesendet, satz: f.satz)
        } catch {
            return Handlungsquittung(
                ausgang: .nichtGesendet,
                satz: "Die Anfrage liess sich nicht bauen (\(error.localizedDescription)).")
        }
        switch await sender.fuehreAus(anfrage, basis: basis) {
        case .antwort(let status, let daten):
            return lies(status, daten)
        case .keineAntwort(let grund, _):
            return Handlungsquittung.ohneAntwort(grund: grund)
        }
    }
}
