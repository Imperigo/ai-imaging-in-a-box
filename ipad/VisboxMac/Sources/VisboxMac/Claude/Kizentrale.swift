import Foundation
import VisboxKern

/// Ein Aufruf in die Knotenansicht: ein JavaScript-Rumpf und seine Argumente, zurueck kommt der
/// JSON-Text, den `window.visboxKi.alsText` schreibt — `nil`, wenn die Seite nicht antwortete.
/// Gesetzt von `Knotenki` (`Start/`), sobald die Seite ihre Schnittstelle anmeldet.
typealias Knotenaufruf = @MainActor (_ rumpf: String, _ argumente: [String: Any]) async -> String?

/// Ein Weg zum Heim-PC fuer die Werkzeuge der Mac-App (`Macwerkzeuge`) — gesetzt vom
/// `Hauptfenster` (`Heimlesen` in `Start/`), sobald ein Heim-PC eingerichtet ist.
typealias Heimholer = @Sendable (_ weg: Macwerkzeuge.Heimweg) async
    -> (status: Int, daten: Data, typ: String?)

/// Die KI-Bedienung der Mac-App (Plan KI-Bedienung, Stufe 3 und 4; Entscheide 105–106f, 108,
/// 114): der Ort, an dem MCP-Kern, Knotenansicht und Assistent-Leiste zusammenkommen.
///
/// * **Fuer den Assistenten** (Stufe 5, 21.10.2026): dieselbe Liste und derselbe Weg, als Urheber
///   «assistent» (`rufeFuerAssistent`) — seine Karten heissen «Vorschlag des Assistenten · A-n».
/// * **Blick und Maus** (Stufe 6): `visbox_blick`, `visbox_maus` gehen an die Seite
///   (`Kibedienen`); die Sperrzonen stehen dort.
/// * **Fuer Claude** (`Knotentraeger`): Werkzeuge nennen — die der Knotenansicht, solange sie
///   offen ist, sonst die Liste aus dem Bau (`Knoten/ki-werkzeugliste.json`), dazu die der Mac-App
///   —, Aufrufe an `window.visboxKi.rufe` reichen, die Mac-Werkzeuge selbst ausfuehren.
///   **Ob eine Karte noetig ist, sagt die Antwort der Knotenansicht** (`Kibruecke`).
/// * **Fuer die Leiste**: der Stand (`Kileistenstand`) aus den Ereignissen der Seite, die
///   Selbstaendigkeit (gemerkt), Anwenden/Ablehnen und «Claudes letzten Schritt zurücknehmen».
/// * **Fuer den Kern**: Jeder Entscheid an einer Karte weckt den wartenden Aufruf
///   (`Mcpkern.entscheide`).
/// * **Die Karten liegen hier** (Strang Karten, 21.10.2026; `Kartenablage` im Kern): Laedt die
///   Knotenansicht neu, wird sie geschlossen oder auf die Visbox-Seite umgeschaltet, bleiben die
///   offenen Karten stehen. Meldet sich die Seite wieder an, bekommt sie die Karten ihrer Mappe
///   zurueck (`visboxKi.stelleWieder`). Verworfen wird nur mit «Ablehnen» oder nach Ablauf — und
///   dann hoert Claude einen Satz mit Grund. Was nicht mehr passt (andere Mappe, Graph geaendert),
///   weist «Anwenden» mit Satz ab.
///
/// Was hier NIE geschieht: die Grafikkarte freigeben. Dafuer gibt es keinen Weg.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
@MainActor
final class Kizentrale: ObservableObject {
    static let gemeinsam = Kizentrale()

    @Published private(set) var stand = Kileistenstand()
    @Published private(set) var modus: Selbstaendigkeit
    /// Ein Satz nach einem Handgriff in der Leiste (Ruecknahme, verschwundene Karte).
    @Published private(set) var meldung: String?
    /// Die Mappe der Knotenansicht, fuer `visbox_status` — gelesen, wenn die Seite bereit ist.
    @Published private(set) var mappenname: String?

    private var knoten: Knotenaufruf?
    /// Die offenen Karten mit Mappe und Zeit — sie ueberleben die Knotenansicht.
    private(set) var ablage = Kartenablage()
    /// Die Mappe der Knotenansicht (gesetzt beim Laden der Flaeche, `Flaechenlotse.lade`).
    private(set) var kartenmappe = Kartenmappe.amHeimPC
    private var ablaufUhr: Timer?
    private var liveWerkzeuge: [Mcpwerkzeug]?
    private var heim: Heimholer?
    private lazy var gebuendelt: [Mcpwerkzeug] = Kizentrale.leseGebuendelteListe()

    init() {
        modus = Selbstaendigkeit(gemerkt: UserDefaults.standard.string(
            forKey: Selbstaendigkeit.einstellung))
        // DER ABLAUF (Strang Karten): einmal je Minute nachsehen, ob eine Karte zu lange liegt.
        ablaufUhr = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.pruefeAblauf() }
        }
    }

    private var kern: Mcpkern { Claudeanschluss.gemeinsam.kern }

    /// Ob die Knotenansicht gerade ihre Schnittstelle angemeldet hat.
    var knotenOffen: Bool { knoten != nil }

    // ================================================================= Einstellung

    /// Der Schalter oben in der Leiste (Entscheid 108 A) — gilt fuer Claude und den Assistenten.
    func setzeModus(_ neu: Selbstaendigkeit) {
        modus = neu
        UserDefaults.standard.set(neu.rawValue, forKey: Selbstaendigkeit.einstellung)
    }

    func setzeHeim(_ holer: Heimholer?) {
        heim = holer
    }

    // ================================================================= von der Knotenansicht

    /// Die Seite hat `window.visboxKi` angemeldet (Nachricht «bereit»): Sie bekommt die offenen
    /// Karten ihrer Mappe zurueck.
    func knotenAngemeldet(_ aufruf: @escaping Knotenaufruf) {
        knoten = aufruf
        Task { await ladeLiveWerkzeuge() }
        Task { await leseMappenname() }
        Task { await gibKartenZurueck() }
    }

    /// In welcher Mappe die Knotenansicht gleich laeuft — vor dem Laden der Flaeche gesetzt.
    func setzeKartenmappe(_ mappe: Kartenmappe) {
        kartenmappe = mappe
    }

    /// Die Seite ist weg (neu geladen, auf die Visbox-Seite umgeschaltet, Fenster zu). **Die
    /// Karten bleiben** (Strang Karten): Sie gelten pro Mappe, nicht pro Ansicht; die wartenden
    /// Aufrufe warten weiter. Bis zum naechsten «bereit» entscheidet die Seite nichts.
    func knotenWeg(_ grund: String) {
        knoten = nil
        stand.nimm(.weg(grund: grund))
        ablage.seiteWeg()
    }

    /// Eine Nachricht der Seite (`webkit.messageHandlers.visboxKi`), schon als JSON-Bytes.
    func empfange(_ daten: Data) {
        guard let wert = try? JSONWert.lies(daten), let ereignis = Kiereignis(wert) else { return }
        if case .weg(let grund) = ereignis {
            knotenWeg(grund)
            return
        }
        stand.nimm(ereignis)
        switch ereignis {
        case .karte(let karte):
            ablage.lege(karte, mappe: kartenmappe)
        case .entschieden(let kennung, _, let ergebnis):
            ablage.entferne(kennung)
            let kern = self.kern
            Task { await kern.entscheide(kennung, ergebnis) }
        default:
            break
        }
    }

    // ================================================================= fuer den Traeger

    func werkzeuge() -> [Mcpwerkzeug] {
        (liveWerkzeuge ?? gebuendelt) + Macwerkzeuge.alle
    }

    func lage() -> Mcplage {
        Mcplage(bereit: knoten != nil, mappe: mappenname, modus: modus,
                zusatz: knoten == nil ? Kibruecke.nichtOffen : "")
    }

    func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort {
        await rufe(aufruf, urheber: .claude)
    }

    /// Ein Aufruf von Claude oder vom Assistenten (Stufe 5: dieselbe Liste, derselbe Weg, nur der
    /// Urheber unterscheidet sie). Blick und Maus (Stufe 6) gehen an `visboxKi.blick`/`maus`.
    func rufe(_ aufruf: Mcpaufruf, urheber: Kiurheber) async -> Traegerantwort {
        if Macwerkzeuge.ist(aufruf.werkzeug) {
            return .ergebnis(await fuehreMacWerkzeugAus(aufruf))
        }
        guard let knoten else {
            return .ergebnis(Mcpergebnis(text: Kibruecke.nichtOffen, fehler: true))
        }
        if let rumpf = Kibedienen.rumpf(aufruf.werkzeug) {
            guard let argumente = (try? JSONWert.objekt(aufruf.argumente).daten())
                .flatMap({ String(data: $0, encoding: .utf8) }),
                  let text = await knoten(rumpf, ["urheber": urheber.rawValue, "argumente": argumente]),
                  let antwort = try? JSONWert.lies(Data(text.utf8)) else {
                return .ergebnis(Mcpergebnis(text: Kibruecke.unlesbar, fehler: true))
            }
            return .ergebnis(Kibedienen.ergebnis(aus: antwort))
        }
        guard let rufText = Kibruecke.ruf(aufruf, urheber: urheber),
              let text = await knoten(
                Kibruecke.rumpf("rufe(JSON.parse(ruf), modus)"),
                ["ruf": rufText, "modus": modus.rawValue]),
              let antwort = try? JSONWert.lies(Data(text.utf8)) else {
            return .ergebnis(Mcpergebnis(text: Kibruecke.unlesbar, fehler: true))
        }
        return Kibruecke.traegerantwort(aus: antwort)
    }

    // ================================================================= fuer den Assistenten (Stufe 5)

    /// Die Werkzeuge fuer den Assistenten — **dieselben wie fuer Claude**, solange die
    /// Knotenansicht offen ist; sonst keine (dann fragt er mit seinen drei Vorschlagswerkzeugen
    /// wie bisher). Die zwei des MCP-Kerns (`visbox_status`, `visbox_vorschlag_status`) nicht: Der
    /// Assistent wartet nie auf eine Karte.
    func werkzeugeFuerAssistent() -> [Mcpwerkzeug] {
        knoten == nil ? [] : werkzeuge()
    }

    /// Ein Schritt des Assistenten in der Knotenansicht. Eine Karte wartet nicht: Das Modell hoert,
    /// dass sie beim Architekten liegt (`Assistentenschrittergebnis`).
    func rufeFuerAssistent(_ aufruf: Assistentenaufruf, kennung: String) async -> String {
        let antwort = await rufe(Mcpaufruf(kennung: kennung, werkzeug: aufruf.werkzeug,
                                           argumente: aufruf.argumente), urheber: .assistent)
        return Assistentenschrittergebnis.text(antwort, kennung: kennung).text
    }

    // ================================================================= aus der Leiste

    /// «Anwenden» (`ja`) oder «Ablehnen» an einer Karte. Das Ergebnis kommt als Ereignis
    /// «entschieden» zurueck und weckt dort den wartenden Aufruf von Claude.
    ///
    /// **Was die Seite nicht entscheiden kann, entscheidet die Ablage** (Strang Karten): Ablehnen
    /// geht auch bei geschlossener Knotenansicht; Anwenden wartet auf sie — ausser die Karte
    /// gehoert zu einer anderen Mappe oder passt nicht mehr zum Graph, dann weist es sie mit Satz ab.
    func entscheide(_ kennung: String, ja: Bool) async {
        meldung = nil
        switch ablage.entscheide(kennung, ja: ja, mappe: kartenmappe, seiteOffen: knoten != nil) {
        case .hier(let antwort, let satz):
            stand.entferne(kennung)
            meldung = satz
            let kern = self.kern
            Task { await kern.entscheide(kennung, antwort) }
            return
        case .wartet(let satz):
            meldung = satz
            return
        case .anDieSeite, .unbekannt:
            break
        }
        guard let knoten else {
            meldung = Kibruecke.nichtOffen
            return
        }
        let text = await knoten(Kibruecke.rumpf("entscheide(kennung, ja)"),
                                ["kennung": kennung, "ja": ja])
        if text == nil || text == "null" {
            // DIE SEITE KENNT DIE KARTE NICHT MEHR: weg damit, und Claude hoert, dass nichts
            // angewendet wurde — mit Satz, nicht still.
            stand.entferne(kennung)
            ablage.entferne(kennung)
            meldung = "Diesen Vorschlag gibt es in der Knotenansicht nicht mehr — nichts wurde geändert."
            let kern = self.kern
            Task { await kern.entscheide(kennung, Kibruecke.verworfen("Die Karte war nicht mehr da")) }
        }
    }

    // ================================================================= Karten zurueckgeben, Ablauf

    /// Gibt einer neu angemeldeten Knotenansicht die Karten ihrer Mappe zurueck. Die Seite
    /// rechnet jede neu durch: Was liegt, meldet sie mit «karte»; was scheitert, bleibt hier als
    /// unpassend stehen, bis «Anwenden» es mit Satz abweist oder «Ablehnen» es wegnimmt.
    private func gibKartenZurueck() async {
        guard let knoten, let karten = ablage.uebergabeText(kartenmappe) else { return }
        let text = await knoten(Kibruecke.rumpf("stelleWieder(JSON.parse(karten))"), ["karten": karten])
        let antwort = text.flatMap { try? JSONWert.lies(Data($0.utf8)) }
        let unpassend = ablage.nimmWiedergabe(antwort)
        if !unpassend.isEmpty {
            meldung = "\(unpassend.joined(separator: ", ")) passt nicht mehr zum Graph — «Anwenden» "
                + "ändert nichts; lehne den Vorschlag ab oder lass Claude einen neuen stellen."
        }
    }

    /// Karten, die zu lange liegen, laufen ab: Claude hoert den Satz mit Grund, die Seite raeumt
    /// sie ab (ihr Ereignis «entschieden» kommt danach und aendert nichts mehr).
    func pruefeAblauf(jetzt: Date = Date()) {
        let weg = ablage.abgelaufene(jetzt: jetzt)
        guard !weg.isEmpty else { return }
        let kern = self.kern
        for e in weg {
            stand.entferne(e.karte.kennung)
            let antwort = Kartenablage.abgelaufen(e)
            Task { await kern.entscheide(e.karte.kennung, antwort) }
            if e.inDerSeite, let knoten {
                Task { _ = await knoten(Kibruecke.rumpf("entscheide(kennung, ja)"),
                                        ["kennung": e.karte.kennung, "ja": false]) }
            }
        }
        meldung = weg.map(Kartenablage.abgelaufenMeldung).joined(separator: " ")
    }

    /// «Claudes letzten Schritt zurücknehmen» (Entscheid 114).
    func nimmClaudesLetztenSchrittZurueck() async {
        guard let knoten else {
            meldung = Kibruecke.nichtOffen
            return
        }
        let text = await knoten(Kibruecke.rumpf("rueckgaengigKi('claude')"), [:])
        let antwort = text.flatMap { try? JSONWert.lies(Data($0.utf8)) }
        meldung = antwort?["satz"]?.alsText ?? Kibruecke.unlesbar
    }

    func vergissMeldung() {
        meldung = nil
    }

    // ================================================================= Handgriffe

    private func ladeLiveWerkzeuge() async {
        guard let knoten,
              let text = await knoten(Kibruecke.rumpf("werkzeuge()"), [:]),
              let wert = try? JSONWert.lies(Data(text.utf8)) else { return }
        let liste = Kibruecke.werkzeuge(aus: wert)
        if !liste.isEmpty { liveWerkzeuge = liste }
    }

    private func leseMappenname() async {
        guard let heim else { return }
        let antwort = await heim(Macwerkzeuge.mappeWeg)
        guard antwort.status == 200, let w = try? JSONWert.lies(antwort.daten) else { return }
        mappenname = w["name"]?.alsText ?? w["mappe"]?.alsText
    }

    /// Die Liste aus dem Bau — damit Claude die Werkzeuge der Knotenansicht kennt, bevor sie
    /// offen ist (`tools/list` fragt Claude einmal je Sitzung).
    private static func leseGebuendelteListe() -> [Mcpwerkzeug] {
        guard let ort = Bundle.main.resourceURL?
            .appendingPathComponent(Knotenwege.ordnerImBuendel, isDirectory: true)
            .appendingPathComponent(Kibruecke.listendatei),
              let daten = try? Data(contentsOf: ort),
              let wert = try? JSONWert.lies(daten) else { return [] }
        return Kibruecke.werkzeuge(aus: wert)
    }

    // ================================================================= die Werkzeuge der Mac-App

    /// `mappe_lesen`, `skizzen_lesen`, `lauf_abbrechen`, `bild_ansehen` — ueber die bestehenden
    /// Wege des Heim-PC. Lesen und Abbrechen brauchen keine Karte; freigeben kann keines.
    private func fuehreMacWerkzeugAus(_ a: Mcpaufruf) async -> Mcpergebnis {
        guard let heim else { return Macwerkzeuge.ohneHeim }
        switch a.werkzeug {
        case Macwerkzeuge.mappeLesenName:
            let r = await heim(Macwerkzeuge.mappeWeg)
            let e = Macwerkzeuge.mappeErgebnis(status: r.status, daten: r.daten)
            if !e.fehler, let w = try? JSONWert.lies(r.daten) {
                mappenname = w["name"]?.alsText ?? w["mappe"]?.alsText
            }
            return e
        case Macwerkzeuge.skizzenLesenName:
            guard let name = a.argumente["name"]?.alsText else {
                let r = await heim(Macwerkzeuge.mappeWeg)
                return Macwerkzeuge.skizzenErgebnis(status: r.status, daten: r.daten)
            }
            guard !name.isEmpty, !name.contains("/"), !name.contains(".."), name.count <= 200 else {
                return Macwerkzeuge.ungueltig("name")
            }
            let r = await heim(Macwerkzeuge.skizzeWeg(name))
            return Macwerkzeuge.bildErgebnis(status: r.status, daten: r.daten, typ: r.typ,
                                             was: "Skizze «\(name)»")
        case Macwerkzeuge.laufAbbrechenName:
            guard let job = a.argumente["jobId"]?.alsText, Macwerkzeuge.gueltigeKennung(job) else {
                return Macwerkzeuge.ungueltig("jobId")
            }
            let r = await heim(Macwerkzeuge.abbrechenWeg(job))
            return Macwerkzeuge.abbrechenErgebnis(status: r.status, daten: r.daten, jobId: job)
        case Macwerkzeuge.bildAnsehenName:
            guard let job = a.argumente["jobId"]?.alsText, Macwerkzeuge.gueltigeKennung(job) else {
                return Macwerkzeuge.ungueltig("jobId")
            }
            let nummer = a.argumente["bild"]?.alsGanz ?? 0
            let zettel = await heim(Macwerkzeuge.laufWeg(job))
            switch Macwerkzeuge.bildname(laufzettel: zettel.daten, status: zettel.status,
                                         jobId: job, nummer: nummer) {
            case .keines(let satz):
                return satz
            case .name(let name):
                guard let weg = Macwerkzeuge.artefaktWeg(job, name) else {
                    return Macwerkzeuge.ungueltig("bild")
                }
                let r = await heim(weg)
                return Macwerkzeuge.bildErgebnis(status: r.status, daten: r.daten, typ: r.typ,
                                                 was: "Bild \(nummer) von Lauf \(job)")
            }
        default:
            return .unbekannt(a.werkzeug)
        }
    }
}

/// Der Werkzeugtraeger des MCP-Kerns in der App (seit Stufe 3, statt des Platzhalters): Er
/// reicht alles an die `Kizentrale` auf dem Hauptfaden.
struct Knotentraeger: Werkzeugtraeger {
    let zentrale: Kizentrale

    func werkzeuge() async -> [Mcpwerkzeug] {
        await zentrale.werkzeuge()
    }

    func lage() async -> Mcplage {
        await zentrale.lage()
    }

    func rufe(_ aufruf: Mcpaufruf, werkzeug: Mcpwerkzeug) async -> Traegerantwort {
        await zentrale.rufe(aufruf, werkzeug: werkzeug)
    }
}
