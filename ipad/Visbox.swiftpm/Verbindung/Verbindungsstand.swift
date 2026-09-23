import Foundation
import Network

/// Woher die Skizze kommt, die in die Mappe gelegt wird — **die eine Schnittstelle zur
/// Zeichenfläche.**
///
/// Die Einheit «Verbindung» baut nichts in `Zeichnen/`; sie nimmt nur diese Funktion an.
/// Vorgegeben ist `Zeichenstand.gemeinsam.skizzenpaket(_:)` (siehe `Mappenknopf`): die
/// sichtbaren Ebenen als PNG **und die Unterlage des Blattes** (seit dem 23.09.2026; vorher
/// nur die Bilder, und jede Skizze ging ohne `ueber` hinaus). Was davon ins Fach geht,
/// entscheidet der Kern (`Ablageplan`, Entscheid Nr. 7: «gerechnet wird, was sichtbar ist»).
///
/// `@MainActor`, weil das Malen der Ebenen (UIKit) auf den Hauptfaden gehört — und damit es
/// gleich bleibt, ob die Zeichenfläche ihren Stand selbst so auszeichnet oder nicht.
typealias Skizzenquelle = @MainActor () -> Skizzenpaket

/// Die Verbindung zur HomeStation: koppeln, prüfen, parken, nachsenden — **und ehrlich
/// sagen, wie es steht.**
///
/// * **Jede Skizze geht zuerst ins Parkfach** (`Kern/Parkfach.swift`) und von dort hinaus.
///   Ist die HomeStation nicht erreichbar, bleibt sie dort und geht von selbst, sobald sie
///   es wieder ist (Entscheide Nr. 12 und Nr. 28).
/// * **«Gekoppelt» heisst: sie hat zuletzt geantwortet** (`Verbindungszustand`). Eine
///   gemerkte Anmeldung allein ist noch keine Verbindung.
/// * Geprüft wird mit `GET /api/fortschritt` — der einfachste angemeldete Weg. Er zeigt
///   zugleich, ob die gemerkte Anmeldung drüben noch gilt (sonst 401).
///
/// **Kein `@MainActor` an der Klasse**, sondern an den Methoden, die eine Ansicht ruft: So
/// lässt sich `gemeinsam` aus jeder Ansicht erreichen, ohne dass es auf die Fassung der
/// SwiftUI-Schnittstellen ankommt (22.09.2026, hier nicht übersetzt).
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
final class Verbindungsstand: ObservableObject {
    static let gemeinsam = Verbindungsstand()

    /// Wie oft nachgesehen wird, ob die HomeStation antwortet (Sekunden). Gesetzt, nicht
    /// gemessen: oft genug, dass eine geparkte Skizze bald hinausgeht; selten genug, dass
    /// das Heimnetz davon nichts merkt.
    static let pruefabstand: UInt64 = 10

    @Published private(set) var zustand: Verbindungszustand = .aus
    /// Der Name der gekoppelten HomeStation im Heimnetz — `nil`, wenn eingetippt.
    @Published private(set) var stationsname: String?
    @Published private(set) var adresse: URL?
    @Published private(set) var gefunden: [GefundenerDienst] = []
    /// Warum die Suche nicht läuft — `nil`, wenn sie läuft oder nicht gefragt ist.
    @Published private(set) var suchSatz: String?
    @Published private(set) var fach: [Parkeintrag] = []
    /// Ein Satz zum Parkfach selbst (nicht zu einer Skizze).
    @Published private(set) var fachSatz: String?
    /// Die Skizze, die gerade reist, und wo ihre Marke steht.
    @Published private(set) var uebergabe: Flugbahn.Phase?
    /// Der letzte Laufstand der HomeStation, wie er kam.
    @Published private(set) var laufstand: Fortschrittsstand?
    /// Warum die Mappe nicht geladen ist — `nil`, wenn sie es ist oder nicht gefragt wurde.
    @Published private(set) var mappenSatz: String?
    /// Der Projektordner **auf der HomeStation**; leer heisst: der ihres Starts.
    @Published var ordner: String {
        didSet { Verbindungsgedaechtnis.ordner = ordner }
    }

    let sender = Sender()
    private let sucher = Sucher()
    private let netz = NWPathMonitor()
    private let parkfach: Parkfach?
    private(set) var anmeldung: Anmeldung?
    private var erreichbar: Bool?
    private var grund: String?
    private var sendetGerade = false
    /// Wer die Suche gerade will (`Kern/Suche.swift`). Der Sucher läuft, solange einer es
    /// tut — der Koppelbildschirm beendet nicht die Suche, die das Prüfen braucht.
    private var suchwunsch = Suchwunsch()
    private var uebergabeSchluessel: String?
    private var schleife: Task<Void, Never>?

    init() {
        ordner = Verbindungsgedaechtnis.ordner
        adresse = Verbindungsgedaechtnis.adresse
        stationsname = Verbindungsgedaechtnis.name

        do {
            parkfach = try Parkfach(ordner: Verbindungsstand.fachordner())
        } catch {
            parkfach = nil
            fachSatz = "Das Parkfach liess sich nicht öffnen (\(error.localizedDescription)). "
                + "Skizzen können gerade nicht auf dem iPad warten."
        }

        switch Schluesselbund.lies() {
        case .gefunden(let a):
            anmeldung = a
        case .keiner:
            break
        case .fehler(let satz):
            erreichbar = false
            grund = satz
        }

        sucher.meldeGefunden = { [weak self] liste in self?.gefundenGemeldet(liste) }
        sucher.meldeZustand = { [weak self] satz in self?.suchSatz = satz }
        netz.pathUpdateHandler = { [weak self] pfad in
            guard pfad.status == .satisfied else { return }
            // DAS NETZ IST WIEDER DA: gleich nachsehen, statt auf die naechste Runde zu warten.
            Task { @MainActor [weak self] in await self?.pruefe() }
        }
        netz.start(queue: DispatchQueue(label: "verbindung.netz"))

        spiegleFach()
        bestimmeZustand()
        if adresse != nil {
            Task { @MainActor [weak self] in self?.starteSchleife() }
        }
    }

    /// Der Ordner des Parkfachs: im Ordner der App, **nicht** im Zwischenspeicher — den darf
    /// das System leeren, und eine geparkte Skizze ist keine Kopie von etwas.
    static func fachordner() throws -> URL {
        let basis = try FileManager.default.url(for: .applicationSupportDirectory,
                                                in: .userDomainMask, appropriateFor: nil,
                                                create: true)
        return basis.appendingPathComponent("Parkfach", isDirectory: true)
    }

    var gekoppelt: Bool { adresse != nil }

    /// Was der Knopf zum Parkfach zählt — geparkt, ungewiss, unterwegs und offen **getrennt**
    /// (Kern: `Fachzaehlung`). Bis zur Durchsicht vom 22.09.2026 stand hier `wartend`, und
    /// der Knopf nannte auch ungewisse Skizzen «geparkt».
    var zaehlung: Fachzaehlung { Fachzaehlung(fach) }

    // ------------------------------------------------------------------- Zustand
    //
    // DIE HANDGRIFFE OHNE `@MainActor` (`bestimmeZustand`, `spiegleFach`, `verlange`,
    // `gibFrei`, `gefundenGemeldet`, `flug`) werden nur auf dem Hauptfaden gerufen: aus
    // `init`, aus Methoden mit `@MainActor` oder ueber `DispatchQueue.main`. Sie tragen die Marke nicht,
    // weil `init` und die Rueckrufe von `Sucher` und `Sender` sie sonst nicht rufen duerften.

    private func bestimmeZustand() {
        zustand = Verbindungszustand.bestimme(gekoppelt: gekoppelt, sucht: sucher.sucht,
                                              erreichbar: erreichbar, grund: grund)
    }

    private func spiegleFach() {
        fach = parkfach?.eintraege ?? []
        if let unlesbar = parkfach?.unlesbar, !unlesbar.isEmpty {
            fachSatz = "\(unlesbar.count) Einträge im Parkfach liessen sich nicht lesen. "
                + "Sie bleiben liegen, wie sie sind."
        } else if let fehler = parkfach?.aufraeumFehler {
            // EINE ALTE QUITTUNG BLIEB STEHEN — gesagt, aber das Fach ist offen und sendet.
            fachSatz = fehler
        }
    }

    // ------------------------------------------------------------------- Suchen

    /// Der Koppelbildschirm will suchen (beim Erscheinen).
    @MainActor
    func starteSuche() {
        verlange(.koppeln)
    }

    /// Der Koppelbildschirm will nicht mehr suchen (beim Verschwinden). **Die Suche endet
    /// nur, wenn sonst keiner sie will** — sucht das Prüfen die gekoppelte HomeStation
    /// unter ihrem Namen, sucht es weiter (Durchsicht vom 22.09.2026, `Suchwunsch`).
    @MainActor
    func beendeSuche() {
        gibFrei(.koppeln)
    }

    private func verlange(_ anlass: Suchwunsch.Anlass) {
        if suchwunsch.verlange(anlass) { sucher.starte() }
        bestimmeZustand()
    }

    private func gibFrei(_ anlass: Suchwunsch.Anlass) {
        if suchwunsch.gibFrei(anlass) {
            sucher.beende()
            suchSatz = nil
        }
        bestimmeZustand()
    }

    private func gefundenGemeldet(_ liste: [GefundenerDienst]) {
        gefunden = liste
        // DIE GEKOPPELTE HOMESTATION HAT EINE NEUE ADRESSE BEKOMMEN (der Router vergibt sie
        // neu): Sie wird am NAMEN wiedererkannt, den sie im Heimnetz traegt — nicht geraten.
        guard let name = stationsname,
              let wieder = liste.first(where: { $0.name == name && $0.aufgeloest }),
              let neu = wieder.adresse, neu != adresse else { return }
        adresse = neu
        Verbindungsgedaechtnis.adresse = neu
        Task { @MainActor [weak self] in await self?.pruefe() }
    }

    // ------------------------------------------------------------------- Koppeln

    /// Koppelt mit der sechsstelligen Zahl. Gibt zurück, ob es geklappt hat, und den Satz,
    /// der gezeigt wird.
    @MainActor
    func koppele(adresse ziel: URL, name: String?, zahl eingabe: String) async -> (Bool, String) {
        guard let zahl = Kopplungszahl(eingabe) else {
            return (false, "Die Zahl hat genau sechs Ziffern.")
        }
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.verbinden(zahl)
        } catch let f as Rumpffehler {
            return (false, f.satz)
        } catch {
            return (false, "Die Anfrage liess sich nicht bauen (\(error.localizedDescription)).")
        }
        let antwort = await sender.fuehreAus(anfrage, basis: ziel)
        let ergebnis: Kopplungsergebnis
        switch antwort {
        case .keineAntwort(let satz, _):
            return (false, satz)
        case .antwort(let status, let daten):
            do {
                ergebnis = try Kopplungsergebnis.lies(status: status, daten: daten)
            } catch let f as Serverfehler {
                return (false, f.satz)
            } catch {
                return (false, "Die Antwort der HomeStation war nicht lesbar.")
            }
        }
        switch ergebnis {
        case .abgelehnt(let satz):
            return (false, satz)
        case .verbunden(let neu, let satz):
            if let neu {
                if let fehler = Schluesselbund.speichere(neu) {
                    // DIE ZAHL IST DRUEBEN SCHON VERBRAUCHT. Das zu verschweigen hiesse, den
                    // naechsten Versuch mit derselben Zahl scheitern zu lassen, ohne Grund.
                    return (false, fehler + " Die Zahl ist damit verbraucht — an der "
                            + "HomeStation eine neue holen.")
                }
            } else {
                Schluesselbund.loesche()
            }
            anmeldung = neu
            adresse = ziel
            stationsname = name
            Verbindungsgedaechtnis.adresse = ziel
            Verbindungsgedaechtnis.name = name
            erreichbar = true
            grund = nil
            bestimmeZustand()
            starteSchleife()
            Task { @MainActor [weak self] in
                await self?.nachsenden()
                await self?.ladeMappe()
            }
            return (true, satz ?? "Verbunden.")
        }
    }

    /// Vergisst die HomeStation auf diesem iPad. **Drüben** bleibt die Anmeldung gültig —
    /// einen Weg, ein Gerät zu vergessen, hat der Server nicht (Protokoll §7). Das Parkfach
    /// bleibt: Die Skizzen warten auf die nächste Kopplung.
    @MainActor
    func trenne() {
        schleife?.cancel()
        schleife = nil
        gibFrei(.wiederfinden)
        Schluesselbund.loesche()
        Verbindungsgedaechtnis.vergiss()
        anmeldung = nil
        adresse = nil
        stationsname = nil
        erreichbar = nil
        grund = nil
        laufstand = nil
        bestimmeZustand()
    }

    // ------------------------------------------------------------------- Prüfen

    @MainActor
    private func starteSchleife() {
        schleife?.cancel()
        schleife = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                await self?.pruefe()
                try? await Task.sleep(nanoseconds: Verbindungsstand.pruefabstand * 1_000_000_000)
            }
        }
    }

    /// Fragt die HomeStation, ob sie antwortet — und schickt, wenn ja, was im Fach wartet.
    @MainActor
    func pruefe() async {
        guard let basis = adresse else {
            bestimmeZustand()
            return
        }
        let vorher = zustand
        let antwort = await sender.fuehreAus(Anfragen.fortschritt(anmeldung: anmeldung),
                                             basis: basis)
        switch antwort {
        case .antwort(let status, let daten):
            do {
                laufstand = try Fortschrittsstand.lies(status: status, daten: daten)
                erreichbar = true
                grund = nil
            } catch let f as Serverfehler {
                erreichbar = false
                grund = f.art == .nichtAngemeldet
                    ? "Die HomeStation nimmt die gemerkte Anmeldung nicht mehr an "
                        + "(neu gestartet?). Neu koppeln."
                    : f.satz
            } catch {
                erreichbar = false
                grund = "Die Antwort der HomeStation war nicht lesbar."
            }
        case .keineAntwort(let satz, _):
            erreichbar = false
            grund = satz
        }
        // NICHT ERREICHBAR, ABER MIT NAMEN GEKOPPELT: im Heimnetz nach ihr suchen — sie hat
        // vielleicht eine neue Adresse. Wieder erreichbar: DIESEN Wunsch zuruecknehmen. Die
        // Suche des offenen Koppelbildschirms laeuft weiter (bis zum 22.09.2026 beendete
        // das Pruefen sie hier mit, und umgekehrt).
        if erreichbar == false, stationsname != nil { verlange(.wiederfinden) }
        if erreichbar == true { gibFrei(.wiederfinden) }
        bestimmeZustand()

        if zustand.darfSenden {
            await nachsenden()
            if !vorher.darfSenden { await ladeMappe() }
        }
    }

    // --------------------------------------------------------- Parken und Senden

    /// «In die Mappe legen»: Die Skizze geht **ins Parkfach** und von dort hinaus. Gibt den
    /// Satz zurück, der gezeigt wird — `nil`, wenn es nichts zu sagen gibt, weil die Marke
    /// es zeigt.
    ///
    /// **Was hinausgeht, entscheidet der Kern** (`Ablageplan.aus`, seit dem 23.09.2026, mit
    /// Proben in `BlattunterlageTests`): nichts Gezeichnetes, zu viele Varianten, eine
    /// Unterlage aus einer anderen Mappe — dann ein Satz und nichts im Fach. Sonst parkt das
    /// Fach jedes Bild **mit `ueber`**, wenn eine Unterlage liegt und sichtbar ist
    /// (`Parkfach.parke(_:ueber:ordner:jetzt:)`), und die Angabe überlebt den Neustart.
    @MainActor
    func legeInDieMappe(_ paket: Skizzenpaket) -> String? {
        let zielordner = ordner.isEmpty ? nil : ordner
        let bilder: [Ebenenausgabe.Bild]
        let ueber: String?
        switch Ablageplan.aus(paket, ordner: zielordner) {
        case .nicht(let satz):
            return satz
        case .parke(let b, let u):
            bilder = b
            ueber = u
        }
        guard let fach = parkfach else {
            return fachSatz ?? "Das Parkfach ist nicht offen — die Skizze kann nicht warten."
        }
        do {
            try fach.parke(bilder, ueber: ueber, ordner: zielordner)
        } catch {
            spiegleFach()
            return "Die Skizze liess sich nicht ins Parkfach legen (\(error.localizedDescription))."
        }
        spiegleFach()
        if zustand.darfSenden {
            Task { @MainActor [weak self] in await self?.nachsenden() }
            return nil
        }
        return "Geparkt. Die HomeStation ist gerade nicht erreichbar; die Skizze geht von "
            + "selbst hinaus, sobald sie es wieder ist."
    }

    /// Schickt, was im Fach wartet — eine Skizze nach der anderen, **jede durch das Tor**
    /// (`Parkfach.beginneSenden`), damit keine zweimal hinausgeht, und **jede mit ihrem
    /// Schlüssel** (`Anfragen.skizze(_:png:anmeldung:)`), damit eine ungewisse beim zweiten
    /// Mal drüben keine zweite Datei anlegt (Protokoll §3).
    ///
    /// Die Folge je Skizze: Vorspiel der Marke → Tor (mit der Frage, ob inzwischen
    /// abgebrochen ist) → erstes Byte. *Gebaut, am Gerät unbestätigt (22.09.2026)* — dass
    /// ein Abbruch im Vorspiel wirklich nicht sendet, prüft keine Probe; bewacht ist nur die
    /// Regel des Tors im Kern.
    @MainActor
    func nachsenden() async {
        guard !sendetGerade, let fach = parkfach, let basis = adresse else { return }
        sendetGerade = true
        defer { sendetGerade = false }
        var angekommen = false

        while zustand.darfSenden, let naechste = fach.naechster {
            let schluessel = naechste.schluessel
            uebergabeSchluessel = schluessel

            // DAS VORSPIEL DES BLATTS ZUERST: ablegen (220 ms), abheben (180 ms) — erst dann
            // das Tor, und gleich danach das erste Byte. Bis zur Durchsicht vom 22.09.2026 kam
            // das Tor VOR dem Vorspiel: `unterwegs`, ein Versuch mehr und «Schluessel ging
            // mit» standen schon auf der Platte, und ein Abbruch im Vorspiel (`trenne` beendet
            // die Pruefschleife) wurde von `try?` verschluckt — gesendet wurde trotzdem.
            for (phase, dauer) in Flugbahn.vorspiel {
                uebergabe = phase
                try? await Task.sleep(nanoseconds: UInt64(dauer * 1_000_000_000))
            }

            // NACH DEM VORSPIEL: Ist das Senden abgebrochen (die Aufgabe beendet, getrennt,
            // eine andere Adresse, nicht mehr gekoppelt), gibt das Tor nichts frei und
            // schreibt nichts (Kern: `Parkfach.beginneSenden(_:abgebrochen:)`, bewacht). Die
            // Skizze bleibt, wie sie war, und geht beim naechsten Pruefen.
            let abgebrochen = Task.isCancelled || adresse != basis || !zustand.darfSenden
            let eintrag: Parkeintrag
            do {
                guard let frei = try fach.beginneSenden(schluessel, abgebrochen: abgebrochen) else {
                    spiegleFach()
                    await lasseZurueckfallen(schluessel)
                    if abgebrochen { break }
                    continue
                }
                eintrag = frei
            } catch {
                fachSatz = "Das Parkfach liess sich nicht beschreiben (\(error.localizedDescription))."
                uebergabe = nil
                uebergabeSchluessel = nil
                break
            }
            guard let png = fach.png(schluessel) else {
                _ = try? fach.melde(schluessel,
                                    .abgewiesen(grund: "Die Zeichnung fehlt im Fach.", code: nil))
                spiegleFach()
                await lasseZurueckfallen(schluessel)
                continue
            }
            let anfrage: Anfrage
            do {
                anfrage = try Anfragen.skizze(eintrag, png: png, anmeldung: anmeldung)
            } catch {
                // NICHT GEBAUT HEISST NICHT GESENDET: Die Skizze bleibt mit dem Satz liegen,
                // statt in einer anderen Form hinauszugehen.
                let satz = (error as? Rumpffehler)?.satz
                    ?? "Die Anfrage liess sich nicht bauen (\(error.localizedDescription))."
                _ = try? fach.melde(schluessel, .abgewiesen(grund: satz, code: nil))
                spiegleFach()
                await lasseZurueckfallen(schluessel)
                continue
            }
            spiegleFach()

            // UNTERWEGS, NICHT GEZAEHLT: Die Marke atmet am Rand, bis ein Zaehlerstand mit
            // Gesamt kommt — auch dann, wenn keiner mehr kommt.
            uebergabe = Flugbahn.flugbeginn

            let antwort = await sender.fuehreAus(anfrage, basis: basis) { [weak self] gesendet, gesamt in
                DispatchQueue.main.async {
                    self?.flug(schluessel, gesendet: gesendet, gesamt: gesamt)
                }
            }
            let ergebnis: Sendeergebnis
            switch antwort {
            case .antwort(let status, let daten):
                ergebnis = .aus(status: status, daten: daten)
            case .keineAntwort(let satz, let bytes):
                ergebnis = .ohneVerbindung(grund: satz, gesendeteBytes: bytes)
            }
            do {
                try fach.melde(schluessel, ergebnis)
            } catch {
                fachSatz = "Das Parkfach liess sich nicht beschreiben (\(error.localizedDescription))."
            }
            spiegleFach()

            // DIE MARKE RASTET ERST JETZT EIN — nach der Antwort, nicht nach dem letzten Byte.
            switch ergebnis {
            case .angekommen:
                uebergabe = .eingerastet
                angekommen = true
            case .abgewiesen:
                uebergabe = .zurueck
            case .nichtAngemeldet(let satz), .nichtErreicht(let satz), .ohneAntwort(let satz):
                uebergabe = .zurueck
                erreichbar = false
                grund = satz
                bestimmeZustand()
            }
            // Einen Augenblick stehen lassen, damit man sieht, wo sie liegt.
            try? await Task.sleep(nanoseconds: 900_000_000)
            if uebergabeSchluessel == schluessel {
                uebergabe = nil
                uebergabeSchluessel = nil
            }
        }
        if angekommen { await ladeMappe() }
    }

    /// Die Marke fällt zurück aufs iPad (Blatt: *«sie verschwindet nie in der Mitte»*), steht
    /// einen Augenblick und geht dann weg — aber nur, wenn inzwischen keine andere reist.
    @MainActor
    private func lasseZurueckfallen(_ schluessel: String) async {
        uebergabe = .zurueck
        try? await Task.sleep(nanoseconds: 900_000_000)
        if uebergabeSchluessel == schluessel {
            uebergabe = nil
            uebergabeSchluessel = nil
        }
    }

    /// Ein Zählerstand vom Senden. Gilt nur für die Skizze, die gerade reist, und nur,
    /// solange sie noch nicht angekommen oder zurückgefallen ist.
    /// Was ein Zählerstand bewirkt, rechnet der Kern (`Flugbahn.gezaehlt`).
    private func flug(_ schluessel: String, gesendet: Int64, gesamt: Int64?) {
        guard uebergabeSchluessel == schluessel, let phase = uebergabe,
              let neu = Flugbahn.gezaehlt(phase, gesendet: gesendet, gesamt: gesamt) else { return }
        uebergabe = neu
    }

    /// Eine abgewiesene oder ungewisse Skizze auf Wunsch noch einmal schicken — mit
    /// demselben Schlüssel wie zuvor.
    @MainActor
    func nochEinmal(_ eintrag: Parkeintrag) {
        _ = try? parkfach?.nochEinmal(eintrag.schluessel)
        spiegleFach()
        if zustand.darfSenden {
            Task { @MainActor [weak self] in await self?.nachsenden() }
        }
    }

    /// Eine Skizze auf Wunsch verwerfen.
    @MainActor
    func verwirf(_ eintrag: Parkeintrag) {
        do {
            _ = try parkfach?.verwirf(eintrag.schluessel)
        } catch {
            fachSatz = "Die Skizze liess sich nicht verwerfen (\(error.localizedDescription))."
        }
        spiegleFach()
    }

    /// Die Zeichnung eines Eintrags (für die Vorschau im Fach) — `nil` nach der Ankunft.
    func zeichnung(_ eintrag: Parkeintrag) -> Data? {
        parkfach?.png(eintrag.schluessel)
    }

    @MainActor
    func setzeMappenSatz(_ satz: String?) {
        mappenSatz = satz
    }
}
