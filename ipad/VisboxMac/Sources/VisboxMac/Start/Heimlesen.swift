import Foundation
import VisboxKern

/// Die Lesewege der Mac-Werkzeuge fuer Claude (Plan KI-Bedienung, Stufe 4): `mappe_lesen`,
/// `skizzen_lesen`, `bild_ansehen` und `lauf_abbrechen` gehen ueber die **bestehenden** Wege des
/// Heim-PC (`/knoten/mappe`, `/knoten/skizze`, `/bruecke/jobs/…`) — mit der Anmeldung der App und
/// dem angehefteten Zertifikat, wie jede andere Anfrage (`Knotenwege.koepfeFuerHeim`,
/// `Heimvertrauenslotse`). Welcher Weg und was die Antwort heisst, sagt der Kern
/// (`Macwerkzeuge`); hier wird nur geschickt.
///
/// Keiner dieser Wege gibt die Grafikkarte frei: `/approve` steht nirgends.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
final class Heimlesen: @unchecked Sendable {
    let basis: URL
    private let anmeldung: Anmeldung?
    private let sitzung: URLSession

    init(basis: URL, anmeldung: Anmeldung?) {
        self.basis = basis
        self.anmeldung = anmeldung
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = Knotenwege.wartezeitKurz
        art.timeoutIntervalForResource = 120
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpCookieStorage = nil
        art.httpShouldSetCookies = false
        art.connectionProxyDictionary = [:]
        sitzung = URLSession(configuration: art, delegate: Heimvertrauenslotse.gemeinsam,
                             delegateQueue: nil)
    }

    /// Fuer die `Kizentrale` — `nil` ohne eingerichteten Heim-PC.
    @MainActor
    static func richteAus(adresse: URL?, anmeldung: Anmeldung?) {
        guard let adresse else {
            Kizentrale.gemeinsam.setzeHeim(nil)
            return
        }
        let leser = Heimlesen(basis: adresse, anmeldung: anmeldung)
        Kizentrale.gemeinsam.setzeHeim { weg in await leser.hole(weg) }
    }

    func hole(_ weg: Macwerkzeuge.Heimweg) async -> (status: Int, daten: Data, typ: String?) {
        guard let ziel = Knotenwege.heimAdresse(pfad: weg.pfad, kodierteFrage: weg.frage,
                                                basis: basis) else {
            return (Knotenwege.Fehlerart.heimNichtErreicht.rawValue,
                    Knotenwege.fehlerRumpf("Aus der Adresse des Heim-PC liess sich kein Weg bauen."), nil)
        }
        var auftrag = URLRequest(url: ziel)
        auftrag.httpMethod = weg.methode
        for k in Knotenwege.koepfeFuerHeim(seite: [], anmeldung: anmeldung) {
            auftrag.setValue(k.wert, forHTTPHeaderField: k.name)
        }
        if weg.methode == "POST" {
            auftrag.setValue("application/json", forHTTPHeaderField: "Content-Type")
            auftrag.httpBody = Data("{}".utf8)
        }
        do {
            let (daten, antwort) = try await sitzung.data(for: auftrag)
            let http = antwort as? HTTPURLResponse
            return (http?.statusCode ?? 0, daten, http?.value(forHTTPHeaderField: "Content-Type"))
        } catch {
            return (Knotenwege.Fehlerart.heimNichtErreicht.rawValue,
                    Knotenwege.fehlerRumpf("Der Heim-PC ist nicht erreicht: " + Heimstrecke.satz(error)),
                    nil)
        }
    }
}
