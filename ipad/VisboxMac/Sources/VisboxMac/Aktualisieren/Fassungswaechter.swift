import AppKit
import Foundation
import VisboxKern

/// Fragt GitHub, ob es eine neuere Fassung gibt, und fuehrt das Ersetzen — **entscheidet
/// nichts**: Ob angeboten wird, ob die Datei stimmt und ob das Bundle passt, sagt der Kern
/// (`Kern/Aktualisierung.swift`).
///
/// Anlass: Owner-Entscheid 84 (13.10.2026, Blatt 18). Bis dahin holte der Owner jede Fassung
/// von Hand als ZIP aus einem Lauf der Pruefstrecke.
///
/// * **Beim Start und einmal taeglich** (84a): `starte()` fragt sofort und danach stuendlich,
///   ob die Tagesregel des Kerns eine Frage faellig nennt. Stuendlich und nicht alle 24 h,
///   weil ein Mac schlaeft: Ein Takt, der 24 h wartet, verschoebe sich um jede Nacht.
/// * **Keine Installation ohne Klick:** Hier wird nur angeboten. Geladen wird erst mit
///   «Laden und ersetzen».
/// * **Still bei Fehlern der Frage:** Kein Netz oder eine gedrosselte Schnittstelle heisst
///   «kein Angebot», nicht eine Meldung am Bildschirm — die App laeuft ohne GitHub weiter.
///
/// *Gebaut, am Geraet unbestaetigt (13.10.2026).*
@MainActor
final class Fassungswaechter: ObservableObject {
    @Published private(set) var angebot: Freigabe?
    @Published private(set) var phase: Aktualisierungsphase = .angeboten

    /// Die Nummer dieser App, aus ihrer `Info.plist`. Laeuft sie nicht als Bundle (beim
    /// Entwickeln), ist sie `nil`, und es wird nie etwas angeboten.
    let laufend = Aktualisierung.laufendeNummer(Bundle.main.infoDictionary)

    private var takt: Task<Void, Never>?
    private var arbeitet = false

    // EINE FLUECHTIGE SITZUNG: keine Kekse, kein Zwischenspeicher auf der Platte — die Frage
    // an GitHub soll nichts hinterlassen und immer die aktuelle Antwort bekommen.
    private static let sitzung = URLSession(configuration: .ephemeral)
    private static let letzteSchluessel = "aktualisierung.letzteFrage"

    private var letzte: Date? {
        get { UserDefaults.standard.object(forKey: Self.letzteSchluessel) as? Date }
        set { UserDefaults.standard.set(newValue, forKey: Self.letzteSchluessel) }
    }

    func starte() {
        guard takt == nil else { return }
        takt = Task { [weak self] in
            // BEIM START IMMER (84a), unabhaengig davon, wann zuletzt gefragt wurde.
            await self?.frage()
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 3_600 * 1_000_000_000)
                guard let self else { return }
                if Aktualisierung.sollFragen(letzte: self.letzte, jetzt: Date()) {
                    await self.frage()
                }
            }
        }
    }

    func halte() {
        takt?.cancel()
        takt = nil
    }

    private func frage() async {
        letzte = Date()
        var anfrage = URLRequest(url: Aktualisierung.abfrage,
                                 cachePolicy: .reloadIgnoringLocalCacheData,
                                 timeoutInterval: 20)
        for (name, wert) in Aktualisierung.kopfzeilen(laufend: laufend) {
            anfrage.setValue(wert, forHTTPHeaderField: name)
        }
        guard let geholt = try? await Self.sitzung.data(for: anfrage),
              (geholt.1 as? HTTPURLResponse)?.statusCode == 200,
              let freigabe = try? Aktualisierung.deute(geholt.0) else { return }
        // WAEHREND GELADEN ODER ERSETZT WIRD, bleibt das Angebot stehen — eine neue Antwort
        // mitten im Ersetzen gaebe sonst dem Blatt eine andere Nummer als der geladenen Datei.
        guard !arbeitet, phase != .fertig else { return }
        if Aktualisierung.bietetAn(freigabe, laufend: laufend) {
            if angebot?.nummer != freigabe.nummer { phase = .angeboten }
            angebot = freigabe
        } else {
            angebot = nil
        }
    }

    /// «Laden und ersetzen» — der eine Klick, ohne den nichts ersetzt wird.
    func ladeUndErsetze() {
        guard let angebot, !arbeitet else { return }
        guard let kennung = Bundle.main.bundleIdentifier else {
            phase = .gescheitert(.ortGesperrt("Die App läuft nicht aus einem Bundle — es gibt nichts zu ersetzen."))
            return
        }
        let buendel = Bundle.main.bundleURL
        arbeitet = true
        phase = .laedt(nil)
        Task { [weak self] in
            do {
                try await Ersetzer.ersetze(angebot, buendel: buendel, kennung: kennung) { neu in
                    Task { @MainActor in self?.melde(neu) }
                }
                self?.schliesse(mit: .fertig)
            } catch let fehler as Aktualisierungsfehler {
                self?.schliesse(mit: .gescheitert(fehler))
            } catch {
                self?.schliesse(mit: .gescheitert(.ersetzenScheiterte(error.localizedDescription)))
            }
        }
    }

    /// Ein Zwischenstand vom Ersetzer. Kommt er nach dem Ende an (er reist ueber eine eigene
    /// Aufgabe), wird er verworfen — sonst stuende nach «Ersetzt» wieder «Lädt …».
    private func melde(_ neu: Aktualisierungsphase) {
        guard arbeitet else { return }
        phase = neu
    }

    private func schliesse(mit ende: Aktualisierungsphase) {
        arbeitet = false
        phase = ende
    }

    /// Nach einem Fehler: zurueck zum Angebot, damit «Erneut versuchen» von vorn beginnt.
    func zuruecksetzen() {
        guard !arbeitet, phase != .fertig else { return }
        phase = .angeboten
    }

    /// «Neu starten»: die neue App am selben Ort oeffnen, dann diese beenden. Eine neue
    /// Instanz ausdruecklich (`createsNewApplicationInstance`) — sonst holte macOS nur diese,
    /// noch laufende, nach vorn.
    func starteNeu() {
        guard phase == .fertig else { return }
        let art = NSWorkspace.OpenConfiguration()
        art.createsNewApplicationInstance = true
        NSWorkspace.shared.openApplication(at: Bundle.main.bundleURL, configuration: art) { _, fehler in
            Task { @MainActor [weak self] in
                if fehler == nil {
                    NSApp.terminate(nil)
                } else {
                    self?.phase = .gescheitert(.neustartScheiterte)
                }
            }
        }
    }
}
