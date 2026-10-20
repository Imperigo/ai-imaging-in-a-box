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
/// * **Beim Start und jede Stunde** (Entscheid 87, vorher taeglich): `starte()` fragt sofort
///   und sieht danach alle zehn Minuten nach, ob die Regel des Kerns eine Frage faellig nennt
///   — ein Mac schlaeft, und ein Takt, der eine Stunde schliefe, verschoebe sich um jede Nacht.
/// * **Ein Klick** (Entscheid 87): Der Knopf «● 0.x.y verfügbar» laedt sofort; nach dem
///   Ersetzen steht **«Neu starten»** da (seit 0.2.10, Owner-Befund 20.10.2026 — bis dahin
///   startete die App von selbst neu). Ohne den Klick wird nie etwas installiert.
/// * **Immer die neueste** (Owner-Befund 20.10.2026): Jede gelungene Antwort ersetzt das
///   Angebot, und der Klick fragt **vor dem Laden noch einmal** — so laedt er nie eine
///   Zwischenfassung, auch wenn mehrere dazwischen liegen. Welches Angebot gilt, sagt der Kern
///   (`Angebotsstand`); scheitert eine Frage, sieht der Waechter nach fuenf Minuten wieder
///   nach statt nach einer Stunde, und nach dem Aufwachen des Mac sofort.
/// * **Still bei Fehlern der Frage:** Kein Netz oder eine gedrosselte Schnittstelle heisst
///   «kein Angebot», nicht eine Meldung am Bildschirm — die App laeuft ohne GitHub weiter.
///
/// *Gebaut, am Geraet unbestaetigt (13.10.2026).*
@MainActor
final class Fassungswaechter: ObservableObject {
    @Published private(set) var phase: Aktualisierungsphase = .angeboten

    /// Die Nummer dieser App, aus ihrer `Info.plist`. Laeuft sie nicht als Bundle (beim
    /// Entwickeln), ist sie `nil`, und es wird nie etwas angeboten.
    let laufend: Fassungsnummer?

    /// Welches Angebot gilt und ob gerade geladen wird — die Regeln stehen im Kern.
    @Published private var stand: Angebotsstand

    /// Was der Knopf «● 0.x.y verfügbar» zeigt.
    var angebot: Freigabe? { stand.angebot }

    init() {
        let nummer = Aktualisierung.laufendeNummer(Bundle.main.infoDictionary)
        laufend = nummer
        stand = Angebotsstand(laufend: nummer)
    }

    private var takt: Task<Void, Never>?
    private var wachHoerer: NSObjectProtocol?
    /// Ob die letzte Frage eine Antwort bekam — sonst fragt der Takt nach
    /// `Aktualisierung.abstandNachFehler` wieder, nicht erst nach einer Stunde.
    private var letzteGelungen = true
    private var arbeitet = false
    private var neustartLaeuft = false

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
            // Auch nach «Neu starten» ist das ein Start: Die neue Fassung fragt sofort.
            await self?.frage()
            while !Task.isCancelled {
                let blick = UInt64(Aktualisierung.blickAbstand * 1_000_000_000)
                try? await Task.sleep(nanoseconds: blick)
                guard let self else { return }
                if Aktualisierung.sollFragen(letzte: self.letzte, jetzt: Date(),
                                             gelungen: self.letzteGelungen) {
                    await self.frage()
                }
            }
        }
        // NACH DEM AUFWACHEN SOFORT: Ein Mac, der die Nacht durch schlief, soll nicht erst
        // eine Stunde lang ein altes Angebot zeigen.
        wachHoerer = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didWakeNotification, object: nil, queue: .main) { [weak self] _ in
            Task { @MainActor in await self?.frage() }
        }
    }

    func halte() {
        takt?.cancel()
        takt = nil
        if let wachHoerer { NSWorkspace.shared.notificationCenter.removeObserver(wachHoerer) }
        wachHoerer = nil
    }

    /// Eine Frage an `…/releases/latest`: die Freigabe, oder `nil`, wenn keine Antwort kam.
    private func hole(frist: TimeInterval = 20) async -> Freigabe? {
        letzte = Date()
        var anfrage = URLRequest(url: Aktualisierung.abfrage,
                                 cachePolicy: .reloadIgnoringLocalCacheData,
                                 timeoutInterval: frist)
        for (name, wert) in Aktualisierung.kopfzeilen(laufend: laufend) {
            anfrage.setValue(wert, forHTTPHeaderField: name)
        }
        guard let geholt = try? await Self.sitzung.data(for: anfrage),
              (geholt.1 as? HTTPURLResponse)?.statusCode == 200,
              let freigabe = try? Aktualisierung.deute(geholt.0) else {
            letzteGelungen = false
            return nil
        }
        letzteGelungen = true
        return freigabe
    }

    private func frage() async {
        let antwort = await hole()
        // JEDE ANTWORT ERSETZT DAS ANGEBOT durch die neueste Nummer — ausser waehrend geladen
        // oder ersetzt wird (`Angebotsstand.nimm`): Eine neue Nummer mitten im Ersetzen gaebe
        // dem Blatt eine andere Nummer als der geladenen Datei.
        if stand.nimm(antwort), !stand.gesperrt, !arbeitet { phase = .angeboten }
    }

    /// Laden und ersetzen — ausgeloest vom einen Klick auf den Knopf (Entscheid 87), ohne den
    /// nichts ersetzt wird.
    ///
    /// **VOR DEM LADEN NOCH EINMAL FRAGEN** (Owner-Befund 20.10.2026): Das angezeigte Angebot
    /// kann bis zu einer Stunde alt sein. Geladen wird die neueste aus Angebot und frischer
    /// Antwort (`Angebotsstand.beginne`); scheitert die Frage, das angezeigte Angebot.
    func ladeUndErsetze() {
        guard angebot != nil, !arbeitet, !stand.gesperrt else { return }
        guard let kennung = Bundle.main.bundleIdentifier else {
            phase = .gescheitert(.ortGesperrt("Die App läuft nicht aus einem Bundle — es gibt nichts zu ersetzen."))
            return
        }
        let buendel = Bundle.main.bundleURL
        arbeitet = true
        phase = .laedt(nil)
        Task { [weak self] in
            guard let self else { return }
            let frisch = await self.hole(frist: 10)
            guard let ziel = self.stand.beginne(frisch: frisch) else {
                // Die frische Antwort sagt: diese Fassung ist schon die neueste.
                self.arbeitet = false
                self.phase = .angeboten
                return
            }
            do {
                try await Ersetzer.ersetze(ziel, buendel: buendel, kennung: kennung) { [weak self] neu in
                    Task { @MainActor in self?.melde(neu) }
                }
                // NEU STARTEN AUF KLICK (Owner-Befund 20.10.2026, ersetzt den Teil «von selbst»
                // aus Entscheid 87): Bis 0.2.9 startete die App nach dem Ersetzen sofort neu —
                // am Mac des Owners stand danach ein zweites Fenster neben dem alten. Jetzt
                // steht «Neu starten» da, und erst der Klick beendet die alte App.
                self.schliesse(mit: .fertig)
            } catch let fehler as Aktualisierungsfehler {
                self.schliesse(mit: .gescheitert(fehler))
            } catch {
                self.schliesse(mit: .gescheitert(.ersetzenScheiterte(error.localizedDescription)))
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
        stand.beende(ersetzt: ende == .fertig)
        phase = ende
    }

    /// Nach einem Fehler: zurueck zum Angebot, damit «Erneut versuchen» von vorn beginnt.
    func zuruecksetzen() {
        guard !arbeitet, phase != .fertig else { return }
        phase = .angeboten
    }

    /// «Neu starten»: **erst beenden, dann oeffnen** (14.10.2026). Ein kleiner Helfer
    /// (`/bin/sh`, Befehl aus dem Kern: `Aktualisierung.neustartBefehl`) wartet, bis diese
    /// App weg ist, und oeffnet dann das Buendel am selben Ort — das ist jetzt die neue App.
    /// Bis dahin oeffnete die App die neue selbst und beendete sich danach; am Mac des Owners
    /// ging dabei nur ein zweites Fenster der alten App auf, und die alte blieb stehen.
    ///
    /// Vorher merkt sich die App, welche Nummer danach laufen soll; der naechste Start
    /// bestaetigt sie (`pruefeNeustart`). Bleibt das Beenden an etwas haengen, endet die App
    /// nach `Aktualisierung.beendenFrist` von selbst — gespeichert ist zu dem Zeitpunkt alles.
    func starteNeu() {
        // EIN NEUSTART, NICHT ZWEI: Ein zweiter Klick haette einen zweiten Helfer gestartet.
        guard phase == .fertig, !neustartLaeuft else { return }
        neustartLaeuft = true
        let befehl = Aktualisierung.neustartBefehl(pid: ProcessInfo.processInfo.processIdentifier,
                                                   buendel: Bundle.main.bundlePath)
        let helfer = Process()
        helfer.executableURL = URL(fileURLWithPath: befehl[0])
        helfer.arguments = Array(befehl.dropFirst())
        do {
            try helfer.run()
        } catch {
            phase = .gescheitert(.neustartScheiterte)
            return
        }
        // DIE NUMMER DER ERSETZTEN APP, nicht die des Knopfs (die steht seit dem Klick fest).
        if let nummer = stand.inArbeit?.nummer ?? angebot?.nummer {
            UserDefaults.standard.set("\(nummer)", forKey: Aktualisierung.erwarteteSchluessel)
        }
        UserDefaults.standard.synchronize()
        NSApp.terminate(nil)
        DispatchQueue.main.asyncAfter(deadline: .now() + Aktualisierung.beendenFrist) {
            exit(0)
        }
    }

    /// Was nach dem Neustart zu sagen ist: «Visbox 0.x.y ist installiert» — oder dass die
    /// Aktualisierung nicht ankam. Einmal: Der Merker wird beim Lesen geloescht.
    @Published private(set) var neustartBefund: Neustartbefund?

    func pruefeNeustart() {
        let merker = UserDefaults.standard.string(forKey: Aktualisierung.erwarteteSchluessel)
        UserDefaults.standard.removeObject(forKey: Aktualisierung.erwarteteSchluessel)
        neustartBefund = Aktualisierung.nachNeustart(erwartet: merker, laufend: laufend)
    }

    func bestaetigungGesehen() {
        neustartBefund = nil
    }
}
