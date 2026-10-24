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
/// **Seit Entscheid 118 (21.10.2026) über den Mac, verschlüsselt:** Gekoppelt wird nur noch mit
/// dem Mac (`https`, Zertifikat angeheftet, `Maclotse`); eine Kopplung von vorher bleibt als
/// Übergang (direkt am Heim-PC) oder wird abgewiesen (unverschlüsselt über den Mac) — beides
/// mit Satz, nie still (`Anbindungsart` im Kern).
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026; über den Mac 21.10.2026).*
final class Verbindungsstand: ObservableObject {
    static let gemeinsam = Verbindungsstand()

    /// Wie oft nachgesehen wird, ob die HomeStation antwortet (Sekunden). Gesetzt, nicht
    /// gemessen: oft genug, dass eine geparkte Skizze bald hinausgeht; selten genug, dass
    /// das Heimnetz davon nichts merkt.
    static let pruefabstand: UInt64 = 10
    /// So lange wartet das Nachsehen auf eine Antwort (14.10.2026). Bis dahin galten die 30 s
    /// jeder Anfrage: Antwortete die gemerkte Adresse nicht (der Router hatte eine neue
    /// vergeben), stand die App nach dem Öffnen eine halbe Minute auf «Suche», bevor sie
    /// überhaupt nach dem Namen zu suchen begann — es sah aus, als verbinde sie nie.
    static let pruefFrist: TimeInterval = 5

    @Published private(set) var zustand: Verbindungszustand = .aus
    /// Der Name der gekoppelten HomeStation im Heimnetz — `nil`, wenn eingetippt.
    @Published private(set) var stationsname: String?
    /// Ob unterwegs **der Mac** vermittelt (Protokoll §8b) — nur für die Anzeige; gekoppelt,
    /// angemeldet und gesendet wird genau wie bei der HomeStation.
    @Published private(set) var ueberDenMac: Bool
    /// Der angeheftete Fingerabdruck des Zertifikats des Mac (Entscheid 118) — `nil` ohne.
    @Published private(set) var abdruck: String?
    @Published private(set) var adresse: URL?
    @Published private(set) var gefunden: [GefundenerDienst] = []
    /// Warum die Suche nicht läuft — `nil`, wenn sie läuft oder nicht gefragt ist.
    @Published private(set) var suchSatz: String?
    @Published private(set) var fach: [Parkeintrag] = []
    /// Ein Satz zum Parkfach selbst (nicht zu einer Skizze). **Welcher, entscheidet das Fach**
    /// (`Parkfach.satz`: der ernste zuerst, und jeder geht mit seinem Grund); hier steht er
    /// nur gespiegelt — ausser das Fach liess sich gar nicht öffnen (`oeffnenSatz`).
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
    /// Warum das Fach nicht offen ist — `nil`, wenn es offen ist. Er bleibt, solange die App
    /// läuft: Ein Fach, das nicht aufging, geht erst beim nächsten Start wieder auf.
    private let oeffnenSatz: String?
    private(set) var anmeldung: Anmeldung?
    private var erreichbar: Bool?
    /// Ein kurzer Aussetzer trennt nicht (20.10.2026): dieselbe Schwelle wie am Mac.
    private var aussetzer = Aussetzerfilter()
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
        ueberDenMac = Verbindungsgedaechtnis.ueberDenMac
        abdruck = Verbindungsgedaechtnis.abdruck

        do {
            parkfach = try Parkfach(ordner: Verbindungsstand.fachordner())
            oeffnenSatz = nil
        } catch {
            parkfach = nil
            oeffnenSatz = "Das Parkfach liess sich nicht öffnen (\(error.localizedDescription)). "
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

        heftAn()
        sucher.meldeGefunden = { [weak self] liste in self?.gefundenGemeldet(liste) }
        sucher.meldeZustand = { [weak self] satz in self?.suchSatz = satz }
        netz.pathUpdateHandler = { [weak self] pfad in
            guard pfad.status == .satisfied else { return }
            // DAS NETZ IST WIEDER DA: gleich nachsehen, statt auf die naechste Runde zu warten.
            Task { @MainActor [weak self] in await self?.pruefe() }
        }
        netz.start(queue: DispatchQueue(label: "verbindung.netz"))

        spiegleFach()
        // BEIM OEFFNEN GLEICH AUCH NACH DEM NAMEN SUCHEN (14.10.2026), nicht erst nach einer
        // gescheiterten Frage: Hat die HomeStation eine neue Adresse, findet die Suche sie
        // in ein bis zwei Sekunden. Antwortet die alte Adresse, gibt `pruefe` die Suche frei.
        if adresse != nil, stationsname != nil { verlange(.wiederfinden) }
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

    /// Wie das iPad angebunden ist — über den Mac verschlüsselt, ungeschützt, direkt (Übergang)
    /// oder gar nicht. Entschieden im Kern (`Anbindungsart.bestimme`).
    var anbindung: Anbindungsart {
        Anbindungsart.bestimme(adresse: adresse, ueberDenMac: ueberDenMac, abdruck: abdruck)
    }

    /// Den Lotsen auf den gekoppelten Mac stellen — nur über den Mac gibt es etwas anzuheften.
    private func heftAn() {
        Maclotse.gemeinsam.setze(mac: ueberDenMac ? adresse : nil, abdruck: ueberDenMac ? abdruck : nil)
    }

    /// Über welche Strecke die gekoppelte HomeStation erreicht wird — Heimnetz (http) oder
    /// Tailscale (https, Entscheid 63); abgelesen an der gemerkten Adresse, nie geraten.
    var strecke: Strecke? { adresse.map { Strecke(basis: $0, ueberDenMac: ueberDenMac) } }

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
        // DER AUSSETZER (20.10.2026): Kam die letzte Anfrage nicht an, die HomeStation hat aber
        // eben noch geantwortet und die Schwelle ist nicht erreicht, bleibt «Gekoppelt».
        let gefiltert: Bool? = (erreichbar == false && aussetzer.kurzWeg(jetzt: Date())) ? true : erreichbar
        zustand = Verbindungszustand.bestimme(gekoppelt: gekoppelt, sucht: sucher.sucht,
                                              erreichbar: gefiltert, grund: grund)
    }

    /// Spiegelt Fach und Satz. **Der Satz kommt aus dem Fach** (`Parkfach.satz`, Vorrang und
    /// Zurücknehmen dort mit Probe): Bis zur Durchsicht vom 23.09.2026 schrieben die Handgriffe
    /// unten «liess sich nicht beschreiben» selbst hierher, und dieses Spiegeln ersetzte es
    /// gleich danach durch die harmlose Aufräummeldung — zurückgenommen wurde er nie. Dass
    /// jeder Handgriff danach wirklich spiegelt, prüft keine Probe (hier nicht übersetzt).
    private func spiegleFach() {
        fach = parkfach?.eintraege ?? []
        fachSatz = oeffnenSatz ?? parkfach?.satz
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
            // DIE FUNDE ENDEN MIT DER SUCHE (Demolauf 24.10.2026): Ein Fund von vorhin ist
            // beim naechsten Oeffnen keiner mehr — sonst stuende seine alte Adresse wieder da.
            gefunden = []
        }
        bestimmeZustand()
    }

    private func gefundenGemeldet(_ liste: [GefundenerDienst]) {
        gefunden = liste
        // DER GEKOPPELTE MAC HAT EINE NEUE ADRESSE (Entscheid 118): uebernommen nur, wenn er
        // weiter verschluesselt spricht — KEIN RUECKFALL AUF UNVERSCHLUESSELT (Kern:
        // `Macanbindung.wiedergefunden`). Das Zertifikat bleibt angeheftet.
        // ERKANNT AN SEINER FESTEN KENNUNG (Demolauf 22.10.2026): dem Fingerabdruck im TXT-Eintrag,
        // nicht am Namen — den aendert macOS bei einem Namenskonflikt («… (2)»). Ein Mac mit altem
        // Stand nennt keinen; dann weiter am Namen (Kern: `Macanbindung.gekoppelterMac`).
        if ueberDenMac, let gemerkt = adresse,
           let fund = Macanbindung.gekoppelterMac(in: liste, name: stationsname, abdruck: abdruck) {
            // DER NAME IST ANZEIGE: Hat der Mac einen neuen, merkt sich das iPad den neuen.
            if let neuerName = Macanbindung.neuerName(gemerkt: stationsname, fund: fund) {
                stationsname = neuerName
                Verbindungsgedaechtnis.name = neuerName
            }
            switch Macanbindung.wiedergefunden(gemerkt: gemerkt, fund: fund) {
            case .neu(let neu):
                adresse = neu
                Verbindungsgedaechtnis.adresse = neu
                heftAn()
                Task { @MainActor [weak self] in await self?.pruefe() }
            case .unverschluesselt(let satz):
                erreichbar = false
                grund = satz
                bestimmeZustand()
            case .gleich, .offen:
                break
            }
            return
        }
        // DIE GEKOPPELTE HOMESTATION HAT EINE NEUE ADRESSE BEKOMMEN (der Router vergibt sie
        // neu): Sie wird am NAMEN wiedererkannt, den sie im Heimnetz traegt — nicht geraten.
        // (Der Uebergang: eine Kopplung direkt am Heim-PC. Sein verschluesselter Zuhoerer fuer
        // den Mac traegt denselben Namen und zaehlt hier nicht.)
        guard let name = stationsname,
              let wieder = liste.first(where: { $0.name == name && $0.aufgeloest && !$0.nurFuerDenMac })
        else { return }
        if wieder.ueberDenMac != ueberDenMac {
            ueberDenMac = wieder.ueberDenMac
            Verbindungsgedaechtnis.ueberDenMac = wieder.ueberDenMac
        }
        guard let neu = wieder.adresse, neu != adresse else { return }
        adresse = neu
        Verbindungsgedaechtnis.adresse = neu
        Task { @MainActor [weak self] in await self?.pruefe() }
    }

    // ------------------------------------------------------------------- Koppeln

    /// Koppelt mit der sechsstelligen Zahl. Gibt zurück, ob es geklappt hat, und den Satz,
    /// der gezeigt wird.
    ///
    /// **Seit Entscheid 118 nur mit dem Mac, verschlüsselt:** `ziel` ist `https`, `mac` wahr.
    /// `angeheftet` ist der Abdruck aus dem Koppelschein (QR-Code, Nähe) — dann nimmt das iPad
    /// schon im Handschlag nur dieses Zertifikat an. Beim Abtippen lernt es das Zertifikat und
    /// merkt es nur nach der Gegenprobe (`Macanbindung.pruefeKopplung`).
    @MainActor
    func koppele(adresse ziel: URL, name: String?, ueberDenMac mac: Bool = false,
                 angeheftet: String? = nil, zahl eingabe: String) async -> (Bool, String) {
        guard let zahl = Kopplungszahl(eingabe) else {
            return (false, "Die Zahl hat genau sechs Ziffern.")
        }
        guard mac, ziel.scheme?.lowercased() == "https" else {
            return (false, "Seit dieser Fassung koppelt das iPad nur mit dem Mac, verschlüsselt — "
                    + "am Mac «iPad koppeln» öffnen.")
        }
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.verbinden(zahl)
        } catch let f as Rumpffehler {
            return (false, f.satz)
        } catch {
            return (false, "Die Anfrage liess sich nicht bauen (\(error.localizedDescription)).")
        }
        Maclotse.gemeinsam.lerne(ziel, erwartet: angeheftet)
        let antwort = await sender.fuehreAus(anfrage, basis: ziel)
        let gesehen = Maclotse.gemeinsam.beendeLernen(ziel)
        let ergebnis: Kopplungsergebnis
        let neuerAbdruck: String
        switch antwort {
        case .keineAntwort(let satz, _):
            return (false, satz)
        case .antwort(let status, let daten):
            do {
                ergebnis = try Kopplungsergebnis.lies(status: status, daten: daten)
            } catch let f as Serverfehler {
                return (false, f.satz)
            } catch {
                return (false, "Die Antwort des Mac war nicht lesbar.")
            }
            // DIE GEGENPROBE (Entscheid 118): Der Mac nennt sein Zertifikat, und es ist das,
            // das das iPad sah — und, mit Schein, das aus dem Schein. Sonst wird nichts gemerkt.
            if case .verbunden = ergebnis {
                switch Macanbindung.pruefeKopplung(antwort: daten, gesehen: gesehen,
                                                   angeheftet: angeheftet) {
                case .gut(let a): neuerAbdruck = a
                case .abgelehnt(let satz): return (false, satz)
                }
            } else {
                neuerAbdruck = ""
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
                    // WO ES DIE NEUE GIBT, haengt an der Strecke: Unterwegs zeigt sie der
                    // Mac («iPad koppeln», Entscheid 63), zuhause die HomeStation.
                    return (false, fehler + " Die Zahl ist damit verbraucht — am Mac unter «iPad "
                            + "koppeln» eine neue holen.")
                }
            } else {
                Schluesselbund.loesche()
            }
            anmeldung = neu
            adresse = ziel
            stationsname = name
            ueberDenMac = mac
            abdruck = neuerAbdruck
            Verbindungsgedaechtnis.adresse = ziel
            Verbindungsgedaechtnis.name = name
            Verbindungsgedaechtnis.ueberDenMac = mac
            Verbindungsgedaechtnis.abdruck = neuerAbdruck
            heftAn()
            erreichbar = true
            grund = nil
            aussetzer.vergiss()
            aussetzer.melde(erreicht: true, jetzt: Date())
            bestimmeZustand()
            starteSchleife()
            Task { @MainActor [weak self] in
                await self?.nachsenden()
                await self?.ladeMappe()
            }
            return (true, (satz ?? "Verbunden.") + " Zeichen des Mac: "
                    + Fingerabdruck.zeichen(neuerAbdruck) + " — gleich wie am Mac?")
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
        ueberDenMac = false
        abdruck = nil
        heftAn()
        erreichbar = nil
        grund = nil
        aussetzer.vergiss()
        laufstand = nil
        bestimmeZustand()
    }

    // ------------------------------------------------------------------- Prüfen

    /// Die App ist wieder vorn (aus dem Hintergrund oder beim Öffnen): **sofort** nachsehen,
    /// statt auf die nächste Runde zu warten (14.10.2026). Im Hintergrund hält iPadOS die
    /// Schleife an; eine Anfrage, die dabei hing, liesse sonst bis zu 30 s «Getrennt» stehen.
    @MainActor
    func wiederAktiv() {
        guard gekoppelt else { return }
        if stationsname != nil { verlange(.wiederfinden) }
        starteSchleife()
    }

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
        // NIE UNVERSCHLUESSELT UEBER DEN MAC (Entscheid 118): Eine Kopplung von vorher bleibt
        // stehen, aber es geht nichts darueber — die Zeile sagt warum, die Skizzen warten.
        guard anbindung.darfSprechen else {
            erreichbar = false
            grund = anbindung.satz
            aussetzer.vergiss()
            bestimmeZustand()
            return
        }
        let vorher = zustand
        let antwort = await sender.fuehreAus(Anfragen.fortschritt(anmeldung: anmeldung),
                                             basis: basis, frist: Verbindungsstand.pruefFrist)
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
        // EIN AUSSETZER IST KEIN ZUSTAND (20.10.2026): Was angezeigt wird, geht durch den
        // Filter des Kerns — gekoppelt bleibt, wer eben noch antwortete, bis zur Schwelle.
        // Gesendet wird aber nur nach einer Antwort (`roh`).
        // NUR DIE STILLE WIRD UEBERBRUECKT: Eine Antwort mit Absage (401, unlesbar) ist kein
        // Aussetzer — dann gilt sie sofort.
        let angekommen = erreichbar == true
        switch antwort {
        case .keineAntwort: aussetzer.melde(erreicht: false, jetzt: Date())
        case .antwort where angekommen: aussetzer.melde(erreicht: true, jetzt: Date())
        case .antwort: aussetzer.vergiss()
        }
        bestimmeZustand()

        if angekommen, zustand.darfSenden {
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
            return oeffnenSatz ?? "Das Parkfach ist nicht offen — die Skizze kann nicht warten."
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
        let wer = ueberDenMac ? "Der Mac ist" : "Die HomeStation ist"
        return "Geparkt. \(wer) gerade nicht erreichbar; die Skizze geht von selbst hinaus, "
            + "sobald es wieder geht."
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
                // DER SATZ STEHT IM FACH (`Parkfach.schreibFehler`) und kommt mit dem Spiegeln.
                spiegleFach()
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
            // GESCHEITERT STEHT ES IM FACH (`Parkfach.schreibFehler`), mit Vorrang vor der
            // Aufraeummeldung; das Spiegeln danach zeigt es.
            _ = try? fach.melde(schluessel, ergebnis)
            spiegleFach()

            // DIE MARKE RASTET ERST JETZT EIN — nach der Antwort, nicht nach dem letzten Byte.
            switch ergebnis {
            case .angekommen:
                uebergabe = .eingerastet
                angekommen = true
            case .abgewiesen:
                uebergabe = .zurueck
            case .nichtAngemeldet(let satz):
                uebergabe = .zurueck
                erreichbar = false
                grund = satz
                aussetzer.vergiss()
                bestimmeZustand()
            case .nichtErreicht(let satz), .ohneAntwort(let satz):
                uebergabe = .zurueck
                erreichbar = false
                grund = satz
                // EIN AUSSETZER BEIM SENDEN zaehlt wie einer beim Pruefen (20.10.2026).
                aussetzer.melde(erreicht: false, jetzt: Date())
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
        // SCHEITERT ES, sagt es das Fach (`Parkfach.schreibFehler`); das Spiegeln zeigt es.
        _ = try? parkfach?.verwirf(eintrag.schluessel)
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
