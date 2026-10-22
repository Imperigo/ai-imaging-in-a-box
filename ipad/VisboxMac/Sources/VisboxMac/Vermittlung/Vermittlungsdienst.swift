import Foundation
import Network
import Security
import VisboxKern

/// Der Mac als Vermittler für das iPad (Entscheide 42/47, Protokoll §8b): **er bietet sich
/// im WLAN an wie der Heim-PC zuhause und reicht durch.**
///
/// Unterwegs erreicht das iPad den Heim-PC nicht — der ist nur über Tailscale erreichbar,
/// und das läuft auf dem iPad nicht. Der Mac schon. Er bietet darum denselben Dienst an
/// (`Marke.dienst`, TXT `fassung=1` und `vermittler=mac`), nimmt die Anfragen des iPad an und
/// reicht sie an den Heim-PC weiter, mit **seinem** Kennwort. Die App findet ihn, wie sie
/// heute die HomeStation findet.
///
/// **Was hier entschieden wird, entscheidet nicht diese Klasse**, sondern der Kern
/// (`Vermittlerstand`, `Vermittlungsregel`, `Anfrageleser` — mit Proben unter Linux). Hier
/// steht nur, was das Netz braucht: anbieten (`NWListener`), Verbindungen annehmen
/// (`Vermittlungsleitung`), weiterreichen (`Heimstrecke`), und die Zeile «iPad» nachführen.
///
/// **Was hier nie geschieht:** kein Bild zwischenspeichern (die Antwort liegt nur im
/// Arbeitsspeicher, bis sie hinaus ist), keine Anfrage protokollieren — weder Kopf noch
/// Rumpf, auch nicht den Pfad. *Ein Protokoll, das niemand liest, liest irgendwann jemand
/// anderes.*
///
/// **Nur, wenn ausdrücklich eingeschaltet** (Sicherheitsdurchsicht und Owner-Entscheid vom
/// 01.10.2026): Unterwegs spricht das iPad über Tailscale direkt mit dem Heim-PC; die
/// Vermittlung ist die Ausnahme. Angelegt wird der Dienst, sobald der Heim-PC eingerichtet
/// ist, **anbieten** tut er sich erst nach `starte()` — und das ruft `Vermittlungsanschluss`
/// nur, wenn «iPad über diesen Mac anbieten» an ist. Bis dahin sagt die Zeile «aus».
///
/// **Seit Entscheid 118 (21.10.2026) verschlüsselt, und der Weg des iPad überhaupt:** Der Mac
/// spricht mit dem iPad nur noch TLS, mit seinem eigenen Zertifikat (`Macidentitaet`, im
/// Schlüsselbund); das iPad heftet dessen Fingerabdruck beim Koppeln an. **Ohne Zertifikat
/// bietet er sich nicht an** — kein Rückfall auf unverschlüsselt; die Zeile sagt warum. Ist am
/// Mac eine Mappe offen, beantwortet er Mappe, Bilder und Skizzen des iPad selbst
/// (`Ipadmappenquelle`); alles andere reicht er weiter wie bisher.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026; TLS und Mappe am Mac 21.10.2026)* — hier nicht
/// übersetzt (Linux kennt `Network` nicht).
@MainActor
final class Vermittlungsdienst: ObservableObject {

    /// Was die Startzeile «iPad» sagt (`wort`: steht / lädt / wartet / fehlt, und `satz`).
    @Published private(set) var zeile: Vermittlerlage = .aus
    /// Die Zahl zum Koppeln, solange sie gilt — für den Bildschirm des Mac, nirgends sonst.
    @Published private(set) var koppelzahl: String?
    /// Der genaue Grund des letzten abgelehnten Koppelversuchs — nur für den Menschen am Mac.
    @Published private(set) var koppelgrund: String?
    /// Ein Hinweis zum Zugang des iPad (der Schlüsselbund nahm ihn nicht) — `nil`: alles gut.
    @Published private(set) var hinweis: String?
    /// Der Fingerabdruck des Zertifikats, mit dem der Mac dem iPad antwortet — für den
    /// Koppelschein und das Zeichen am Bildschirm. `nil`: keines, dann bietet er sich nicht an.
    @Published private(set) var abdruck: String?
    /// Wo das iPad den Mac erreicht (`https://<ip>:<anschluss>`) — sobald er sich anbietet.
    @Published private(set) var adresseFuerIpad: URL?

    /// Die Leitung zum Heim-PC — `nil`: **kein Heim-PC eingerichtet** (Entscheid 118a). Dann
    /// gibt es trotzdem die Vermittlung: Das iPad koppelt mit dem Mac und bekommt die Mappe am
    /// Mac; was nur der Heim-PC kann, sagt «kein Rechner eingerichtet» (`Ipadmappenwege.ohneRechner`).
    private let heim: Heimstrecke?
    private var stand: Vermittlerstand
    /// Die Identität für TLS — `nil`: kein Zertifikat, kein Anbieten.
    private let identitaet: SecIdentity?
    private let identitaetsfehler: String?
    private let schlange = DispatchQueue(label: "vermittlung.leitungen")
    private let register = Leitungsregister()
    private var hoerer: NWListener?
    private var uhr: Task<Void, Never>?
    private var bereit = false
    /// Ob er sich anbietet — erst nach `starte()`, bis `schalteAus()`.
    private var angeboten = false
    private var fehler: String?
    /// Ob der feste Anschluss schon versucht wurde — belegt, dann ein freier.
    private var aufFestemAnschluss = true

    /// - Parameters:
    ///   - heim: die Leitung zum Heim-PC im eigenen Tailscale-Netz
    ///     (`https://<rechner>.<netz>.ts.net:8443`) mit der Anmeldung **des Mac** (aus seinem
    ///     Schlüsselbund; sie geht nur zum Heim-PC, nie zum iPad) — oder `nil`, wenn kein
    ///     Heim-PC eingerichtet ist (Entscheid 118a).
    init(heim: Heimstrecke?) {
        self.heim = heim
        let (zugang, satz) = Vermittlerschluessel.liesOderErzeuge()
        // DAS ZERTIFIKAT DES MAC (Entscheid 118) — oder der Satz, warum keines.
        let eigenerAbdruck: String?
        switch Macidentitaet.liesOderErzeuge() {
        case .gut(let geladen):
            identitaet = geladen.identitaet
            identitaetsfehler = nil
            eigenerAbdruck = geladen.abdruck
        case .fehler(let grund):
            identitaet = nil
            identitaetsfehler = "Ohne Zertifikat bietet sich der Mac dem iPad nicht an — "
                + "unverschlüsselt geht nichts mehr. " + grund
            eigenerAbdruck = nil
        }
        stand = Vermittlerstand(zugang: zugang, abdruck: eigenerAbdruck)
        abdruck = eigenerAbdruck
        // KANN DER MAC SICH DEN ZUGANG NICHT MERKEN, geht es trotzdem — nur muss das iPad
        // nach jedem Neustart neu koppeln. Das steht dann im Hinweis, statt still zu fehlen.
        hinweis = satz
    }

    // ------------------------------------------------------------------- Handgriffe

    /// Bietet sich im WLAN an. **Eine Zahl nur, wenn `mitZahl`** — beim Einschalten von Hand,
    /// und auch dann nur, wenn über diesen Mac noch nie ein iPad gekoppelt hat.
    ///
    /// Bis zum 20.10.2026 zeigte er bei **jedem** Start eine Zahl, solange über ihn noch kein
    /// iPad gekoppelt hatte (Owner-Befund an 0.2.11): Das iPad war direkt mit dem Heim-PC
    /// gekoppelt, und der Mac bot trotzdem bei jedem Öffnen eine neue an. Eine neue Zahl gibt
    /// es jetzt nur ausdrücklich — «iPad koppeln» oder «Neue Zahl zum Koppeln über den Mac».
    func starte(mitZahl: Bool = false) {
        guard hoerer == nil else { return }
        angeboten = true
        fehler = nil
        bereit = false
        aufFestemAnschluss = true
        // KEIN RUECKFALL AUF UNVERSCHLUESSELT (Entscheid 118): ohne Zertifikat kein Anbieten.
        guard identitaet != nil else {
            fehler = identitaetsfehler
            aktualisiere()
            return
        }
        if mitZahl, !Vermittlergedaechtnis.gekoppelt {
            stand.oeffneKopplung(jetzt: Vermittlungsuhr.jetzt)
        }
        biete()
        uhr?.cancel()
        // DIE ZEILE GEHT MIT DER ZEIT: «vor 4 s» wird «vor 5 s», eine Zahl laeuft ab.
        uhr = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                self?.aktualisiere()
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
        }
        aktualisiere()
    }

    /// Hört auf, sich anzubieten, und schliesst jede offene Verbindung.
    func halte() {
        hoerer?.cancel()
        hoerer = nil
        register.alleBeenden()
        uhr?.cancel()
        uhr = nil
        bereit = false
        fehler = "Angehalten — das iPad erreicht den Heim-PC gerade nicht über diesen Mac."
        aktualisiere()
    }

    /// **Ausgeschaltet:** bietet sich nicht mehr an, schliesst jede Verbindung, und eine
    /// geltende Zahl ist tot — eine Zahl, die niemand erreicht, soll auch später niemand
    /// mehr eingeben können. Die Zeile sagt «aus».
    func schalteAus() {
        hoerer?.cancel()
        hoerer = nil
        register.alleBeenden()
        uhr?.cancel()
        uhr = nil
        bereit = false
        angeboten = false
        fehler = nil
        stand.schliesseKopplung()
        aktualisiere()
    }

    /// Eine neue Zahl zum Koppeln zeigen (die alte ist damit tot). Ausgeschaltet nicht: Die
    /// Zahl erreichte niemand.
    func neueZahl() {
        guard angeboten else { return }
        stand.oeffneKopplung(jetzt: Vermittlungsuhr.jetzt)
        aktualisiere()
    }

    /// Das Koppelfenster ist zu: die Zahl gilt nicht mehr (sie liefe sonst noch bis zu ihrer
    /// Frist).
    func schliesseZahl() {
        stand.schliesseKopplung()
        aktualisiere()
    }

    /// Für das Koppelfenster (Entscheid 118): eine neue Zahl — und sie zurück, solange sie gilt.
    func zahlFuersKoppelfenster() -> String? {
        neueZahl()
        return stand.koppelzahl(jetzt: Vermittlungsuhr.jetzt)
    }

    /// **Das iPad vergessen:** neue Zugangsdaten. Ein gekoppeltes iPad bekommt danach die
    /// Tür und muss neu koppeln; am Heim-PC ändert sich nichts.
    func vergissIPad() {
        let neu = Vermittlerzugang.erzeuge()
        stand.ersetzeZugang(neu)
        hinweis = Vermittlerschluessel.speichere(neu)
        Vermittlergedaechtnis.gekoppelt = false
        aktualisiere()
    }

    // ------------------------------------------------------- für die Leitungen

    /// Die Tür am Kopf allein — `abweisung` `nil`: weiterlesen. `angemeldet`: Der Kopf trägt
    /// die Zugangsdaten des Mac; die Verbindung wird bei vollem Haus nicht verdrängt.
    func vorab(_ kopf: Anfragekopf) -> (abweisung: Leitungsantwort?, angemeldet: Bool) {
        (stand.vorab(kopf, jetzt: Vermittlungsuhr.jetzt), stand.angemeldet(kopf))
    }

    /// Ob ein Kopf die Zugangsdaten des Mac trägt (für eine Anfrage, die in einem Stück kam
    /// und darum nicht erst an der Tür am Kopf stand).
    func angemeldet(_ kopf: Anfragekopf) -> Bool {
        stand.angemeldet(kopf)
    }

    /// Eine ganz gelesene Anfrage: selbst beantworten oder weiterreichen. `nil` heisst:
    /// **keine Antwort** — ob es drüben ankam, ist nicht bekannt, und die abgebrochene
    /// Verbindung sagt dem iPad genau das.
    func bearbeite(_ anfrage: RoheAnfrage) async -> Leitungsantwort? {
        let vorher = stand.erfolgreicheKopplungen
        let schritt = stand.beantworte(anfrage, jetzt: Vermittlungsuhr.jetzt)
        if stand.erfolgreicheKopplungen > vorher {
            Vermittlergedaechtnis.gekoppelt = true
        }
        aktualisiere()
        switch schritt {
        case .antworte(let antwort):
            return antwort
        case .weiterreichen(let weiterreichung):
            // MIT OFFENER MAPPE AM MAC (Schritt 4): Mappe, Bilder und Skizzen beantwortet der
            // Mac selbst. Hierher kommt nur, was die Tuer durchliess und auf der Positivliste
            // steht. Was der Kern nicht nennt, geht weiter wie bisher.
            let ziel = Ipadmappenwege.ziel(anfrage.kopf)
            if let ordner = Mappenablage.gemeinsam.offenerOrdner, let ziel,
               let antwort = Ipadmappenquelle.antwort(ziel, anfrage, ordner: ordner) {
                return antwort
            }
            // OHNE EINGERICHTETEN HEIM-PC (Entscheid 118a): nichts weiterreichen — der Kern sagt,
            // was das iPad hoert (ruhiger Laufstand, «kein Rechner eingerichtet»).
            guard let heim else { return Ipadmappenwege.ohneRechner(ziel) }
            let ergebnis = await heim.reiche(weiterreichung)
            // DER LAUFSTAND OHNE HEIM-PC: Mit Mappe am Mac geht das iPad weiter — nur gerechnet
            // wird nicht. Es hoert das, statt «Mac weg».
            if case .nichtErreicht = ergebnis, ziel == .fortschritt,
               Mappenablage.gemeinsam.offenerOrdner != nil {
                return .json(Ipadmappenwege.fortschrittOhneHeim)
            }
            return Vermittlungsregel.antwort(auf: ergebnis)
        }
    }

    // ------------------------------------------------------------------- intern

    private func aktualisiere() {
        let jetzt = Vermittlungsuhr.jetzt
        let neu = Vermittlerlage.bestimme(angeboten: angeboten, bereit: bereit, fehler: fehler,
                                          stand: stand, jetzt: jetzt)
        if neu != zeile { zeile = neu }
        let zahl = stand.koppelzahl(jetzt: jetzt)
        if zahl != koppelzahl { koppelzahl = zahl }
        if stand.letzterKoppelgrund != koppelgrund { koppelgrund = stand.letzterKoppelgrund }
    }

    private func biete() {
        let anschluss: NWEndpoint.Port = aufFestemAnschluss
            ? (NWEndpoint.Port(rawValue: UInt16(Suche.vorgabeAnschluss)) ?? .any)
            : .any
        let name = Vermittlerangebot.dienstname(rechner: Host.current().localizedName ?? "diesem Mac")
        guard let identitaet else {
            fehler = identitaetsfehler
            aktualisiere()
            return
        }
        do {
            hoerer = try Vermittlungsdienst.baueHoerer(
                anschluss: anschluss, name: name, identitaet: identitaet,
                txt: Vermittlerangebot.txtMitAbdruck(abdruck), schlange: schlange,
                register: register, dienst: self,
                melde: { [weak self] zustand in
                    Task { @MainActor in self?.hoererZustand(zustand) }
                })
        } catch {
            fehler = "Der Mac kann sich dem iPad nicht anbieten (\(error.localizedDescription))."
            aktualisiere()
        }
    }

    private func hoererZustand(_ zustand: Hoererzustand) {
        switch zustand {
        case .bereit:
            bereit = true
            fehler = nil
            // DIE ADRESSE FUER DEN KOPPELSCHEIN: die im WLAN, mit dem Anschluss, auf dem er hoert.
            if let port = hoerer?.port?.rawValue,
               let ip = Macanbindung.adresseFuerIpad(schnittstellen: Vermittlungsdienst.schnittstellen()) {
                adresseFuerIpad = Macanbindung.adresse(ip: ip, anschluss: Int(port))
            }
        case .wartet(let satz):
            bereit = false
            fehler = satz
        case .belegt where aufFestemAnschluss:
            // DER VORGABE-ANSCHLUSS IST BELEGT (laeuft der Server auf diesem Mac?): ein
            // freier. Das iPad findet den Mac ueber seinen Namen, nicht ueber die Zahl.
            hoerer?.cancel()
            hoerer = nil
            aufFestemAnschluss = false
            biete()
        case .belegt:
            bereit = false
            fehler = "Der Mac findet keinen freien Anschluss, um sich dem iPad anzubieten."
        case .gescheitert(let satz):
            bereit = false
            fehler = satz
            hoerer?.cancel()
            hoerer = nil
        case .aus:
            break
        }
        aktualisiere()
    }

    /// Baut den Anbieter — **ausserhalb des Hauptfadens gedacht:** `nonisolated`, damit die
    /// Rückrufe, die `Network` auf `schlange` ruft, nicht an den Hauptfaden gebunden sind
    /// (in Swift 6 prüft die Laufzeit das und hielte das Programm an).
    nonisolated private static func baueHoerer(
        anschluss: NWEndpoint.Port, name: String, identitaet: SecIdentity, txt: Data,
        schlange: DispatchQueue,
        register: Leitungsregister, dienst: Vermittlungsdienst,
        melde: @escaping @Sendable (Hoererzustand) -> Void
    ) throws -> NWListener {
        // TLS MIT DEM ZERTIFIKAT DES MAC (Entscheid 118), mindestens 1.2 — die Regel des Heim-PC
        // (`heimnetz.tls_kontext`). Kein `NWParameters.tcp` mehr: unverschluesselt hoert der
        // Mac dem iPad nicht mehr zu.
        let tls = NWProtocolTLS.Options()
        guard let eigene = sec_identity_create(identitaet) else {
            throw NWError.tls(errSecParam)
        }
        sec_protocol_options_set_local_identity(tls.securityProtocolOptions, eigene)
        sec_protocol_options_set_min_tls_protocol_version(tls.securityProtocolOptions, .TLSv12)
        let parameter = NWParameters(tls: tls, tcp: NWProtocolTCP.Options())
        // KEIN `allowLocalEndpointReuse`: Der Anschluss soll entweder ganz diesem Mac-Dienst
        // gehoeren oder belegt sein — nicht mit einem anderen Prozess geteilt, der dann einen
        // Teil der Anfragen des iPad bekaeme. Belegt heisst: ein freier (`hoererZustand`).
        parameter.includePeerToPeer = false
        let hoerer = try NWListener(using: parameter, on: anschluss)
        // DER TXT-EINTRAG TRAEGT DEN FINGERABDRUCK DES ZERTIFIKATS (22.10.2026): die feste
        // Kennung, an der das iPad diesen Mac wiedererkennt, auch wenn macOS ihn umbenennt.
        hoerer.service = NWListener.Service(name: name, type: Marke.dienst, domain: nil,
                                            txtRecord: txt)
        hoerer.stateUpdateHandler = { zustand in
            melde(Hoererzustand(zustand))
        }
        hoerer.newConnectionHandler = { [weak dienst] verbindung in
            let leitung = Vermittlungsleitung(verbindung: verbindung, schlange: schlange,
                                              dienst: dienst, register: register)
            // VOLLES HAUS: nicht die neue abweisen, sondern die aelteste, die sich noch nicht
            // angemeldet hat — und je Gegenstelle nur so viele (`Leitungsplaetze`). Sonst
            // sperrten 16 stumme Verbindungen eines Fremden das iPad aus.
            guard register.nimm(leitung, gegenstelle: Vermittlungsdienst.gegenstelle(verbindung))
            else {
                verbindung.cancel()
                return
            }
            leitung.starte()
        }
        hoerer.start(queue: schlange)
        return hoerer
    }
}

extension Vermittlungsdienst {
    /// Die IPv4-Adressen dieses Mac mit dem Namen ihrer Schnittstelle (`getifaddrs`) — welche
    /// davon das iPad bekommt, entscheidet der Kern (`Macanbindung.adresseFuerIpad`).
    nonisolated static func schnittstellen() -> [(name: String, adresse: String)] {
        var aus: [(name: String, adresse: String)] = []
        var kopf: UnsafeMutablePointer<ifaddrs>?
        guard getifaddrs(&kopf) == 0, let erster = kopf else { return aus }
        defer { freeifaddrs(kopf) }
        var zeiger: UnsafeMutablePointer<ifaddrs>? = erster
        while let z = zeiger {
            let eintrag = z.pointee
            zeiger = eintrag.ifa_next
            guard let adresse = eintrag.ifa_addr, adresse.pointee.sa_family == UInt8(AF_INET),
                  (eintrag.ifa_flags & UInt32(IFF_UP)) != 0 else { continue }
            var text = [CChar](repeating: 0, count: Int(NI_MAXHOST))
            guard getnameinfo(adresse, socklen_t(adresse.pointee.sa_len), &text, socklen_t(text.count),
                              nil, 0, NI_NUMERICHOST) == 0 else { continue }
            aus.append((name: String(cString: eintrag.ifa_name), adresse: String(cString: text)))
        }
        return aus
    }

    /// Die Adresse der Gegenstelle, **ohne Anschluss** — jede neue Verbindung hat einen
    /// anderen, und gezählt wird je Gerät. Was keine Adresse hat, zählt unter einem Namen.
    nonisolated static func gegenstelle(_ verbindung: NWConnection) -> String {
        if case .hostPort(let rechner, _) = verbindung.endpoint {
            return String(describing: rechner)
        }
        return "unbekannt"
    }
}

/// Der Zustand des Anbieters, als Satz übersetzt — **auf `schlange`**, bevor er zum
/// Hauptfaden geht, damit dort nur ein einfacher Wert ankommt.
enum Hoererzustand: Sendable {
    case bereit
    case wartet(String)
    case belegt
    case gescheitert(String)
    case aus

    init(_ zustand: NWListener.State) {
        switch zustand {
        case .ready:
            self = .bereit
        case .waiting(let f):
            self = .wartet(Hoererzustand.satz(f))
        case .failed(let f):
            if case .posix(let code) = f, code == .EADDRINUSE {
                self = .belegt
            } else {
                self = .gescheitert(Hoererzustand.satz(f))
            }
        case .setup, .cancelled:
            self = .aus
        @unknown default:
            self = .aus
        }
    }

    /// Ein Satz für einen Menschen. `-65570` ist `kDNSServiceErr_PolicyDenied`: Der Mac darf
    /// sich im lokalen Netz nicht anbieten (die Erlaubnis «Lokales Netzwerk» fehlt, ab
    /// macOS 15).
    static func satz(_ f: NWError) -> String {
        if case .dns(let code) = f, Int(code) == -65570 {
            return "Lokales Netzwerk nicht erlaubt: Systemeinstellungen → Datenschutz & "
                + "Sicherheit → Lokales Netzwerk."
        }
        return "Der Mac kann sich dem iPad nicht anbieten (\(f.localizedDescription))."
    }
}

/// Die offenen Verbindungen — damit `halte()` sie schliessen kann und bei vollem Haus die
/// richtige geht. **Welche** das ist, entscheidet der Kern (`Leitungsplaetze`, mit Proben);
/// hier nur die Sperre, weil `Network` von seiner Schlange ruft und `halte()` vom Hauptfaden.
final class Leitungsregister: @unchecked Sendable {
    private let sperre = NSLock()
    private var plaetze = Leitungsplaetze<ObjectIdentifier>()
    private var leitungen: [ObjectIdentifier: Vermittlungsleitung] = [:]

    /// Nimmt eine neue Verbindung auf — `false`: Sie bleibt draussen. Muss dafür eine ältere,
    /// noch unangemeldete gehen, wird die hier geschlossen.
    func nimm(_ leitung: Vermittlungsleitung, gegenstelle: String) -> Bool {
        let id = ObjectIdentifier(leitung)
        sperre.lock()
        let entscheid = plaetze.nimm(id, gegenstelle: gegenstelle)
        var weg: Vermittlungsleitung?
        switch entscheid {
        case .ablehnen:
            sperre.unlock()
            return false
        case .annehmen(let alt):
            if let alt { weg = leitungen.removeValue(forKey: alt) }
            leitungen[id] = leitung
        }
        sperre.unlock()
        weg?.beende(abrupt: true)
        return true
    }

    /// Diese Verbindung trägt die Zugangsdaten des Mac — sie wird nicht mehr verdrängt.
    func angemeldet(_ leitung: Vermittlungsleitung) {
        sperre.lock()
        plaetze.angemeldet(ObjectIdentifier(leitung))
        sperre.unlock()
    }

    func entferne(_ leitung: Vermittlungsleitung) {
        let id = ObjectIdentifier(leitung)
        sperre.lock()
        leitungen[id] = nil
        plaetze.entferne(id)
        sperre.unlock()
    }

    func alleBeenden() {
        sperre.lock()
        let alle = Array(leitungen.values)
        leitungen = [:]
        plaetze = Leitungsplaetze<ObjectIdentifier>()
        sperre.unlock()
        alle.forEach { $0.beende() }
    }
}
