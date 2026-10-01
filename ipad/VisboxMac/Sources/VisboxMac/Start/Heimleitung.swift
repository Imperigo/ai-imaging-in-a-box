import Combine
import Foundation
import VisboxKern

/// Die Leitung zum Heim-PC — **fragt, misst und meldet; entscheiden tut der Kern.**
///
/// Beim Start und danach alle 5 bis 60 Sekunden, mit wachsendem Abstand (`Leitungstakt`),
/// wird gefragt:
///
/// 1. `GET /api/fortschritt` — der einfachste angemeldete Weg. Antwortet er mit 200, steht
///    die Leitung, und die gemessene Zeit steht im Satz. Er zeigt zugleich, ob das Kennwort
///    drüben gilt (401) und ob der Server hinter der Weiterleitung eines verlangt (403).
/// 2. Nur wenn die Leitung steht: `GET /api/heim` — Blender, Grafikkarte, Assistent.
///
/// Was die Antworten heissen, sagt `Startbild.aus` im Kern (mit Proben unter Linux). Hier
/// stehen nur das Senden und die Uhr.
///
/// **Das Signal nach aussen** ist `erreichbarkeit` («erreichbar seit / nicht erreichbar
/// seit»). Ob die App dann in den Vorführmodus geht, entscheidet nicht diese Klasse. Für den
/// Vorführschalter, der einen eigenen Takt hat, meldet sie dazu jede Frage (`letzteFrage`)
/// und jedes Einrichten (`eingerichtetUm`) — sonst zeigten die beiden Takte bis zu einer
/// Minute lang Verschiedenes.
///
/// **Kein `@MainActor` an der Klasse**, sondern an den Methoden, die den Zustand ändern —
/// wie `Verbindungsstand` in der iPad-App: So lässt sie sich als `@StateObject` anlegen,
/// ohne dass es auf die Fassung der SwiftUI-Schnittstellen ankommt.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
final class Heimleitung: ObservableObject {

    @Published private(set) var bild: Startbild
    @Published private(set) var erreichbarkeit: Heimerreichbarkeit = .unbekannt
    @Published private(set) var adresse: URL?
    /// Der Benutzer, der im Schlüsselbund liegt — für das Feld beim Einrichten. Er ist kein
    /// Geheimnis; das Kennwort wird nie veröffentlicht.
    @Published private(set) var benutzer: String?
    /// Warum der Schlüsselbund nichts hergab — `nil`, wenn er es tat oder leer ist.
    @Published private(set) var schluesselbundSatz: String?
    /// Was die letzte Frage nach `/api/fortschritt` ergab, und wann — für den
    /// Vorführschalter (`Vorfuehrschalter.heimleitungFand`), der einen eigenen Takt hat.
    /// `nil`, solange ohne Adresse nicht gefragt wurde.
    @Published private(set) var letzteFrage: Leitungsfrage?
    /// Wann zuletzt erfolgreich eingerichtet wurde — der Vorführschalter beginnt dann von
    /// vorn (`Vorfuehrschalter.neuEingerichtet`). `nil`: in diesem Lauf noch nie.
    @Published private(set) var eingerichtetUm: Date?

    /// Für die Fläche (`Arbeitsansicht`) — nicht veröffentlicht, nicht gedruckt.
    private(set) var anmeldung: Anmeldung?
    /// Was die Vermittlung (Strom B) über das iPad meldet; `nil`: nichts gemeldet.
    private var ipadStand: Zeilenstand?
    private var abstand: TimeInterval?
    private var schleife: Task<Void, Never>?
    private let sitzung: URLSession

    /// Der Heim-PC antwortet seit … — `nil`, wenn er es gerade nicht tut.
    var erreichbarSeit: Date? {
        if case .erreichbar(let seit) = erreichbarkeit { return seit }
        return nil
    }

    /// Der Heim-PC antwortet nicht seit … — `nil`, wenn er es tut oder noch nicht gefragt ist.
    var nichtErreichbarSeit: Date? {
        if case .nichtErreichbar(let seit) = erreichbarkeit { return seit }
        return nil
    }

    /// Noch nichts eingerichtet — dann geht beim Start das Blatt «Einrichten» auf.
    var braucheEinrichten: Bool { adresse == nil || anmeldung == nil }

    init() {
        // FLUECHTIG: nichts zwischenspeichern, keine Kekse, nichts auf der Platte. Und eine
        // kurze Frist — eine Startzeile, die eine Minute auf «antwortet nicht» wartet, sagt
        // eine Minute lang nichts.
        let art = URLSessionConfiguration.ephemeral
        art.timeoutIntervalForRequest = 10
        art.urlCache = nil
        art.requestCachePolicy = .reloadIgnoringLocalCacheData
        art.httpShouldSetCookies = false
        sitzung = URLSession(configuration: art)

        // DIE GEMERKTE ADRESSE WIRD NOCH EINMAL GEPRUEFT: Was in den Einstellungen liegt, kann
        // jemand von Hand geändert haben.
        var geprueft: URL?
        if let gemerkt = Heimgedaechtnis.adresse,
           case .gut(let url, _) = Heimadresse.pruefe(gemerkt.absoluteString) {
            geprueft = url
        }
        var gefunden: Anmeldung?
        var satz: String?
        switch Heimschluesselbund.lies() {
        case .gefunden(let a):
            gefunden = a
        case .keiner:
            break
        case .fehler(let s):
            satz = s
        }
        // UEBER DIE HUELLEN GESETZT, nicht ueber die Eigenschaften: Deren Setzer brauchen ein
        // fertiges `self`, und `bild` ist an dieser Stelle noch nicht gesetzt.
        anmeldung = gefunden
        _adresse = Published(initialValue: geprueft)
        _benutzer = Published(initialValue: gefunden?.benutzer)
        _schluesselbundSatz = Published(initialValue: satz)
        _bild = Published(initialValue: Startbild.aus(leitung: nil, heim: nil,
                                                      adresseDa: geprueft != nil, ipad: nil,
                                                      vorher: nil, jetzt: Date()))
    }

    deinit {
        schleife?.cancel()
    }

    // ------------------------------------------------------------------ Takt

    /// Beginnt zu fragen — sofort, und dann im Takt. Ein zweiter Aufruf beginnt von vorn
    /// (etwa nach dem Einrichten), mit dem kürzesten Abstand.
    @MainActor
    func starte() {
        schleife?.cancel()
        abstand = nil
        schleife = Task { @MainActor [weak self] in
            while !Task.isCancelled {
                guard let warte = await self?.pruefe() else { return }
                try? await Task.sleep(nanoseconds: UInt64(warte * 1_000_000_000))
            }
        }
    }

    /// «Erneut verbinden»: gleich fragen, und den Abstand auf das Kürzeste zurück.
    @MainActor
    func pruefeJetzt() {
        starte()
    }

    /// Fragt einmal und gibt zurück, wie lange bis zur nächsten Frage gewartet wird.
    @MainActor
    func pruefe() async -> TimeInterval {
        let vorher = bild
        var leitungsbefund: Leitungsbefund?
        var heimbefund: Heimbefund?
        if let basis = adresse {
            leitungsbefund = await frageLeitung(basis)
            if case .antwort(200, _)? = leitungsbefund {
                heimbefund = await frageHeim(basis)
            }
        }
        // ZWISCHENDURCH NEU EINGERICHTET: Diese Antworten gehören zur alten Adresse.
        guard !Task.isCancelled else { return Leitungstakt.kuerzest }

        let jetzt = Date()
        let neu = Startbild.aus(leitung: leitungsbefund, heim: heimbefund,
                                adresseDa: adresse != nil, ipad: ipadStand, vorher: vorher,
                                jetzt: jetzt)
        bild = neu
        erreichbarkeit = erreichbarkeit.nach(neu.leitung, jetzt: jetzt)
        if let befund = leitungsbefund {
            letzteFrage = Leitungsfrage(befund: befund, um: jetzt)
        }

        let geaendert = neu.zeilen.map(\.stand.wort) != vorher.zeilen.map(\.stand.wort)
        let laedt = neu.zeilen.contains { $0.stand.laedt }
        let naechster = Leitungstakt.naechster(nach: abstand, geaendert: geaendert, laedt: laedt)
        abstand = naechster
        return naechster
    }

    // ------------------------------------------------------------- die Zahl fürs iPad

    /// «iPad koppeln» (Entscheid 63): fragt den Heim-PC nach einer neuen Zahl und zeigt sie
    /// samt Adresse in der Zeile «iPad». Die Zahl tauscht das iPad über Tailscale selbst gegen
    /// die Anmeldung; der Mac reicht dabei nichts weiter. Was der Kern daraus macht
    /// (`Koppelzahl.zeile`), steht dort mit Proben.
    @MainActor
    func koppleIPad() async {
        guard let basis = adresse else { return }
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.kopplung(anmeldung: anmeldung)
        } catch {
            setzeIpad(.fehlt(grund: "Keine Zahl fürs iPad: die Anfrage liess sich nicht bauen."))
            return
        }
        switch await hole(anfrage, basis: basis) {
        case .antwort(let status, let daten, _):
            setzeIpad(Koppelzahl.zeile(status: status, daten: daten, adresse: basis))
        case .keine(let fehler):
            setzeIpad(.fehlt(grund: "Keine Zahl fürs iPad: \(fehler.satz)"))
        }
    }

    // ------------------------------------------------------- für den Vorführmodus

    /// Ein Versuch für den Vorführschalter (Strom C): `GET /api/fortschritt` mit dessen Frist.
    /// Über **diese** Leitung, damit Adresse, Kennwort und Zertifikatsregeln an einer Stelle
    /// bleiben; ob die Antwort die bestätigte ist, entscheidet der Kern
    /// (`Versuchsausgang.aus`), nicht diese Klasse.
    @MainActor
    func versuch() async -> Versuchsausgang {
        guard let basis = adresse else {
            return .keineAntwort(grund: "Auf diesem Mac ist noch kein Heim-PC eingerichtet.")
        }
        switch await hole(Anfragen.fortschritt(anmeldung: anmeldung), basis: basis,
                          frist: Vorfuehrschalter.versuchsfrist) {
        case .antwort(let status, let daten, _):
            return Versuchsausgang.aus(status: status, daten: daten)
        case .keine(let fehler):
            return .keineAntwort(grund: fehler.satz)
        }
    }

    // ------------------------------------------------------------- von aussen

    /// Die iPad-Zeile, wie die Vermittlung (Strom B) sie meldet. `nil` nimmt die Meldung
    /// zurück — dann wartet die Zeile wieder.
    @MainActor
    func setzeIpad(_ stand: Zeilenstand?) {
        ipadStand = stand
        bild.ipad = stand ?? Startbild.ipadVorgabe
    }

    /// Richtet den Heim-PC ein. `kennwort == nil` behält das gemerkte (nur der Benutzer oder die
    /// Adresse ändern sich). Gibt `nil` zurück, wenn es geklappt hat, sonst den Satz.
    @MainActor
    func richteEin(adresse eingabe: URL, benutzer name: String, kennwort: String?) -> String? {
        // AUCH HIER GEPRUEFT, nicht nur im Blatt: Die Startzeile sagt «verschlüsselt», und das
        // stimmt nur fuer eine Adresse, die der Kern als https angenommen hat.
        let url: URL
        switch Heimadresse.pruefe(eingabe.absoluteString) {
        case .gut(let gut, _): url = gut
        case .schlecht(let grund): return grund
        }
        let neuesKennwort: String
        if let k = kennwort, !k.isEmpty {
            neuesKennwort = k
        } else if let alt = anmeldung {
            neuesKennwort = alt.kennwort
        } else {
            return "Das Kennwort fehlt — es steht im Fenster, in dem der Server am Heim-PC "
                + "gestartet wurde."
        }
        let neu = Anmeldung(benutzer: name, kennwort: neuesKennwort)
        if let fehler = Heimschluesselbund.speichere(neu) {
            return fehler
        }
        Heimgedaechtnis.adresse = url
        adresse = url
        anmeldung = neu
        benutzer = name
        schluesselbundSatz = nil
        erreichbarkeit = .unbekannt
        letzteFrage = nil
        let jetzt = Date()
        bild = Startbild.aus(leitung: nil, heim: nil, adresseDa: true, ipad: ipadStand,
                             vorher: nil, jetzt: jetzt)
        eingerichtetUm = jetzt
        starte()
        return nil
    }

    // ------------------------------------------------------------------ Senden

    private enum Ergebnis {
        case antwort(status: Int, daten: Data, millisekunden: Int)
        case keine(Leitungsfehler)
    }

    private func frageLeitung(_ basis: URL) async -> Leitungsbefund {
        let anfrage = Anfragen.fortschritt(anmeldung: anmeldung)
        switch await hole(anfrage, basis: basis) {
        case .antwort(let status, _, let ms): return .antwort(status: status, millisekunden: ms)
        case .keine(let fehler): return .keineAntwort(fehler)
        }
    }

    private func frageHeim(_ basis: URL) async -> Heimbefund {
        // EIN GET WIRFT NIE (nur ein Rumpf kann scheitern) — die Bauform ist aber die
        // allgemeine, und die ist mit `throws` ausgezeichnet.
        let anfrage: Anfrage
        do {
            anfrage = try Anfragen.baue(Wege.heim, anmeldung: anmeldung)
        } catch {
            return .keineAntwort(.sonstig(code: 0))
        }
        switch await hole(anfrage, basis: basis) {
        case .antwort(let status, let daten, _): return .antwort(status: status, daten: daten)
        case .keine(let fehler): return .keineAntwort(fehler)
        }
    }

    /// Führt eine Anfrage des Kerns aus und misst die Zeit bis zur Antwort.
    private func hole(_ anfrage: Anfrage, basis: URL,
                      frist: TimeInterval? = nil) async -> Ergebnis {
        guard let ziel = anfrage.adresse(basis: basis) else {
            return .keine(.sonstig(code: 0))
        }
        var auftrag = URLRequest(url: ziel)
        auftrag.httpMethod = anfrage.methode.rawValue
        // SEIT «iPad koppeln» GEHT HIER AUCH EIN POST HINAUS: Der Rumpf muss mit.
        auftrag.httpBody = anfrage.rumpf
        if let frist { auftrag.timeoutInterval = frist }
        for (name, wert) in anfrage.kopfzeilen {
            auftrag.setValue(wert, forHTTPHeaderField: name)
        }
        let beginn = Date()
        do {
            let (daten, antwort) = try await sitzung.data(for: auftrag)
            let ms = Int((Date().timeIntervalSince(beginn) * 1000).rounded())
            guard let http = antwort as? HTTPURLResponse else {
                return .keine(.sonstig(code: 0))
            }
            return .antwort(status: http.statusCode, daten: daten, millisekunden: ms)
        } catch let fehler as URLError {
            return .keine(Leitungsfehler(urlFehlercode: fehler.code.rawValue))
        } catch {
            let ns = error as NSError
            return .keine(Leitungsfehler(urlFehlercode: ns.domain == NSURLErrorDomain ? ns.code : 0))
        }
    }
}

/// Eine Frage der Heimleitung nach `/api/fortschritt`: was herauskam, und wann. **Mit der
/// Zeit**, damit zwei gleiche Befunde hintereinander zwei Meldungen sind — `onChange` meldet
/// nur, was sich ändert.
struct Leitungsfrage: Equatable {
    let befund: Leitungsbefund
    let um: Date
}
