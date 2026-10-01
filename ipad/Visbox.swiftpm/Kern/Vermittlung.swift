import Foundation

// DER MAC ALS VERMITTLER — welche Anfrage des iPad er selbst beantwortet, welche er
// abweist und welche er an den Heim-PC weiterreicht (Entscheide 42/47, Protokoll §8b).
//
// Unterwegs (an der ETH, im Zug am Hotspot) erreicht das iPad den Heim-PC nicht: Der ist nur
// ueber Tailscale erreichbar, und das laeuft auf dem iPad nicht. Der Mac schon. Er bietet
// sich darum im WLAN unter demselben Dienst an wie der Heim-PC zuhause und reicht durch —
// so findet die App ihn, wie sie heute die HomeStation findet, und braucht kaum etwas Neues.
//
// Hier stehen die REGELN, ohne Netz: Der Mac-Teil (`ipad/VisboxMac/.../Vermittlung/`) liest
// Bytes, fragt diesen Kern und schreibt Bytes. *Was nur im Mac-Code steht, laesst sich unter
// Linux nicht pruefen — und was sich nicht pruefen laesst, stimmt irgendwann nicht mehr.*

/// Welchen Weg der Mac **selbst** beantwortet.
public enum Selbstweg: Equatable, Sendable {
    /// `POST /api/verbinden` — die Zahl vom Mac gegen die Zugangsdaten des Mac.
    case verbinden
    /// `GET /koppeln` — die Koppelseite für einen Browser.
    case koppelseite
}

/// Was mit einer Anfrage des iPad geschieht.
public enum Vermittlung: Equatable, Sendable {
    /// Der Mac antwortet selbst (Koppeln) — **nie** der Heim-PC. Ginge `POST /api/verbinden`
    /// weiter, bekäme das iPad bei offener Kopplung drüben das Kennwort des Heim-PC.
    case selbstKoppeln(Selbstweg)
    /// Abgewiesen, mit dieser Antwort; nichts geht weiter.
    case abweisen(Leitungsantwort)
    /// Weiter an den Heim-PC — so, wie es hier steht.
    case weiterreichen(Weiterreichung)
}

/// Eine Anfrage, wie sie an den Heim-PC geht — **ohne** die Anmeldung des iPad.
public struct Weiterreichung: Equatable, Sendable {
    /// `GET` oder `POST`.
    public let methode: String
    /// Pfad samt Frage, wie das iPad ihn schickte.
    public let ziel: String
    /// Nur die erlaubten Köpfe (`Vermittlungsregel.erlaubteKoepfe`) — nie `Authorization`,
    /// nie ein Kopf der Verbindung, nie einer, der eine Weiterleitung vortäuscht.
    public let koepfe: [Kopfzeile]
    /// Bei `POST` der Rumpf (auch leer), bei `GET` `nil` — ein GET mit Rumpf lehnt
    /// `URLSession` ab.
    public let rumpf: Data?

    public init(methode: String, ziel: String, koepfe: [Kopfzeile], rumpf: Data?) {
        self.methode = methode
        self.ziel = ziel
        self.koepfe = koepfe
        self.rumpf = rumpf
    }

    /// Die Köpfe, wie sie zum Heim-PC gehen: die erlaubten **und die Anmeldung des Mac.**
    /// Der `Authorization`-Kopf des iPad ist hier schon nicht mehr dabei; er wird ersetzt,
    /// nicht ergänzt.
    public func koepfe(mit anmeldung: Anmeldung) -> [Kopfzeile] {
        koepfe.filter { $0.name.lowercased() != "authorization" }
            + [Kopfzeile("Authorization", anmeldung.kopfzeile)]
    }

    /// Die Adresse am Heim-PC — `nil`, wenn sich keine bauen lässt, die **auf genau diesen
    /// Rechner** zeigt.
    ///
    /// Gebaut wird aus Text (`<basis><ziel>`), nicht über `URLComponents.percentEncodedPath`:
    /// Dessen Setzer bricht das Programm bei einer ungültigen Kodierung ab. Danach wird
    /// nachgesehen, dass Schema, Rechner und Anschluss die der Basis sind — *eine Adresse,
    /// die man zusammensetzt, prüft man, nachdem sie zusammengesetzt ist.*
    public func adresse(heimBasis: URL) -> URL? {
        guard Anfrageleser.zielIstSauber(ziel) else { return nil }
        var basis = heimBasis.absoluteString
        while basis.hasSuffix("/") { basis.removeLast() }
        guard let url = URL(string: basis + ziel),
              url.scheme?.lowercased() == heimBasis.scheme?.lowercased(),
              url.host?.lowercased() == heimBasis.host?.lowercased(),
              url.port == heimBasis.port,
              url.user == nil, url.password == nil else { return nil }
        return url
    }
}

/// Was vom Heim-PC kam.
public enum Heimergebnis: Equatable, Sendable {
    /// Eine Antwort, wie sie kam.
    case antwort(status: Int, koepfe: [Kopfzeile], rumpf: Data)
    /// **Kein Byte** ging zum Heim-PC (nicht erreichbar, Name unbekannt, Leitung zu) — es
    /// kann drüben nichts angekommen sein.
    case nichtErreicht(grund: String)
    /// Bytes waren unterwegs, eine Antwort kam nicht. **Ob es drüben ankam, ist nicht
    /// bekannt** — auch dem Mac nicht.
    case ungewiss(grund: String)

    /// Wenn keine Antwort kam. Ein `GET` ändert drüben nichts: Dann ist es gleich, ob er
    /// ankam, und es heisst «nicht erreicht». Bei einem `POST` entscheidet, ob schon Bytes
    /// hinaus waren (`bytesHinaus`) — dieselbe Regel wie im Parkfach des iPad.
    public static func ohneAntwort(grund: String, methode: String,
                                   bytesHinaus: Int64) -> Heimergebnis {
        if methode == "GET" || bytesHinaus <= 0 { return .nichtErreicht(grund: grund) }
        return .ungewiss(grund: grund)
    }
}

/// Die Regeln der Vermittlung — **die Tür des Mac**, dieselbe Form wie die des Servers
/// (Protokoll §2), mit den Zugangsdaten des Mac statt des Kennworts des Heim-PC.
public enum Vermittlungsregel {

    /// Die Köpfe des iPad, die weitergehen — **nur diese.** Was nicht ausdrücklich erlaubt
    /// ist, bleibt am Mac: `Authorization` (das iPad meldet sich am Mac an, nicht am
    /// Heim-PC), die Köpfe der Verbindung (`Connection`, `Keep-Alive`, `Transfer-Encoding`,
    /// `Upgrade`, `Expect`, `Host`, `Content-Length` — die setzt der Mac für seine eigene
    /// Leitung), und die Köpfe, an denen der Heim-PC eine Weiterleitung erkennt
    /// (`X-Forwarded-*`, `Forwarded`, `Tailscale-User-*`): Die soll ihm keiner vortäuschen
    /// und keiner verbergen können. Eine Liste der verbotenen veraltete mit jedem neuen
    /// Kopf; eine Liste der erlaubten nicht.
    public static let erlaubteKoepfe: Set<String> = ["accept", "accept-language", "content-type"]

    /// Die Köpfe des Heim-PC, die zum iPad zurückgehen. `Location` nur als Pfad am selben
    /// Rechner (`/…`); eine ganze Adresse zeigte auf den Heim-PC, den das iPad nicht
    /// erreicht. `WWW-Authenticate` nie: Die Tür des Heim-PC ist nicht die des iPad.
    public static let erlaubteAntwortkoepfe: Set<String> =
        ["content-type", "cache-control", "content-disposition", "last-modified", "etag", "location"]

    /// Die Abweisung an der Tür: 401, derselbe Satz und derselbe Kopf wie beim Server
    /// (Protokoll §2), der Name aus der Marke. «Im Fenster, in dem … gestartet wurde» ist
    /// am Mac die App selbst.
    public static var tuer: Leitungsantwort {
        let bereich = Marke.name.replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "\"", with: "\\\"")
        return .fehler("Nicht angemeldet. Benutzername und Kennwort stehen im Fenster, in dem "
                       + "\(Marke.name) gestartet wurde.",
                       status: 401,
                       koepfe: [Kopfzeile("WWW-Authenticate",
                                          "Basic realm=\"\(bereich)\", charset=\"UTF-8\"")])
    }

    /// Der Pfad, wie er verglichen wird: **dekodiert.** Der Server dekodiert nicht — aber
    /// ein `/api/verbinde%6E` soll nicht am Mac vorbei zum Heim-PC gehen, nur weil zwei
    /// Leser es verschieden lesen.
    static func vergleichspfad(_ kopf: Anfragekopf) -> String {
        kopf.pfad.removingPercentEncoding ?? kopf.pfad
    }

    /// Ob die Anfrage **mit den Zugangsdaten des Mac** kommt — genau ein `Authorization`-Kopf,
    /// und der stimmt. Zwei solche Köpfe sind keine Anmeldung, sondern eine Frage, welcher
    /// gilt; die beantwortet die Tür nicht.
    public static func angemeldet(_ kopf: Anfragekopf, zugang: Vermittlerzugang) -> Bool {
        let werte = kopf.koepfe.werte("Authorization")
        return werte.count == 1 && zugang.laesstHerein(werte[0])
    }

    static func istVerbinden(_ kopf: Anfragekopf) -> Bool {
        kopf.methode == Wege.verbinden.methode.rawValue && vergleichspfad(kopf) == Wege.verbinden.pfad
    }

    static func istKoppelseite(_ kopf: Anfragekopf) -> Bool {
        kopf.methode == Wege.koppeln.methode.rawValue && vergleichspfad(kopf) == Wege.koppeln.pfad
    }

    /// **Die Tür, am Kopf allein** — bevor der Rumpf gelesen ist. `nil` heisst: herein;
    /// sonst die Abweisung.
    ///
    /// Herein kommt, wer die Zugangsdaten **des Mac** schickt, und ohne sie genau zwei
    /// Wege, wie beim Server (Protokoll §2):
    ///
    /// * `POST /api/verbinden`, solange am Mac eine Kopplung **besteht** (auch eine
    ///   verbrauchte oder abgelaufene: dann folgt der gleichbleibende Ablehnungssatz);
    /// * `GET /koppeln`, nur solange die Zahl **gilt**.
    public static func vorab(_ kopf: Anfragekopf, zugang: Vermittlerzugang,
                             kopplung: Kopplungsstand?) -> Vermittlung? {
        if angemeldet(kopf, zugang: zugang) { return nil }
        if istVerbinden(kopf), kopplung != nil { return nil }
        if istKoppelseite(kopf), kopplung == .offen { return nil }
        return .abweisen(tuer)
    }

    /// Entscheidet über eine ganz gelesene Anfrage.
    ///
    /// Die zwei Koppelwege beantwortet **immer der Mac**, auch angemeldet. Alles andere
    /// geht nur nach der Tür weiter, nur als `GET` oder `POST` (mehr bedient der Server
    /// nicht), und ohne die Köpfe, die am Mac bleiben.
    public static func entscheide(_ anfrage: RoheAnfrage, zugang: Vermittlerzugang,
                                  kopplung: Kopplungsstand?) -> Vermittlung {
        if let abweisung = vorab(anfrage.kopf, zugang: zugang, kopplung: kopplung) {
            return abweisung
        }
        let kopf = anfrage.kopf
        if istVerbinden(kopf) { return .selbstKoppeln(.verbinden) }
        if istKoppelseite(kopf) { return .selbstKoppeln(.koppelseite) }
        guard kopf.methode == "GET" || kopf.methode == "POST" else {
            return .abweisen(.fehler("Diese Art Anfrage reicht der Mac nicht weiter: "
                                     + "\(kopf.methode).", status: 501))
        }
        let koepfe = kopf.koepfe.filter { erlaubteKoepfe.contains($0.name.lowercased()) }
        return .weiterreichen(Weiterreichung(
            methode: kopf.methode, ziel: kopf.ziel, koepfe: koepfe,
            rumpf: kopf.methode == "POST" ? anfrage.rumpf : nil))
    }

    /// Was vom Heim-PC kam, als Antwort an das iPad — `nil` heisst: **keine Antwort, die
    /// Verbindung wird geschlossen.**
    ///
    /// * **Eine Antwort** geht zurück, wie sie kam, mit den erlaubten Köpfen.
    /// * **Eine 401 des Heim-PC wird 403.** Sie hiesse am iPad «die gemerkte Anmeldung gilt
    ///   nicht mehr, neu koppeln» — dabei ist es das Kennwort **des Mac**, das drüben nicht
    ///   passt, und neu koppeln hülfe nichts.
    /// * **Nicht erreicht** wird 403 mit Satz, **nicht** 502: Die App von heute legt eine
    ///   Skizze bei 401/403 zurück ins Parkfach und schickt sie wieder, bei jedem anderen
    ///   Code gilt sie als abgewiesen und wartet auf einen Menschen (`Sendeergebnis.aus`).
    ///   Drüben kam nichts an — also gehört sie zurück ins Fach.
    /// * **Ungewiss** bekommt keine Antwort. Der Mac weiss nicht, ob es drüben ankam; eine
    ///   abgebrochene Verbindung sagt dem iPad genau das (`ohneAntwort`, die Skizze wird
    ///   mit ihrem Schlüssel noch einmal geschickt, drüben entsteht keine zweite Datei).
    public static func antwort(auf ergebnis: Heimergebnis) -> Leitungsantwort? {
        switch ergebnis {
        case .antwort(let status, _, _) where status == 401:
            return .fehler("Der Heim-PC nimmt das Kennwort des Mac nicht an. Am Mac das "
                           + "Kennwort des Heim-PC neu eingeben.", status: 403)
        case .antwort(let status, let koepfe, let rumpf):
            let durch = koepfe.filter { k in
                let name = k.name.lowercased()
                guard erlaubteAntwortkoepfe.contains(name) else { return false }
                return name != "location" || Anfrageleser.zielIstSauber(k.wert)
            }
            return Leitungsantwort(status: status, koepfe: durch, rumpf: rumpf)
        case .nichtErreicht(let grund):
            return .fehler("Der Mac antwortet, erreicht aber den Heim-PC nicht: \(grund)",
                           status: 403)
        case .ungewiss:
            return nil
        }
    }
}

// ======================================================= der Stand am Mac, ohne Netz

/// Was der Mac mit einer Anfrage tut.
public enum Vermittlungsschritt: Equatable, Sendable {
    /// Selbst antworten.
    case antworte(Leitungsantwort)
    /// An den Heim-PC weiterreichen; seine Antwort geht über `Vermittlungsregel.antwort`.
    case weiterreichen(Weiterreichung)
}

/// Der Stand der Vermittlung am Mac — Zugang, Kopplung, letzte Anfrage. **Der Mac-Teil hält
/// genau einen davon** und fragt ihn bei jeder Anfrage; alles, was hier entschieden wird,
/// ist geprüft.
public struct Vermittlerstand: Sendable {
    public private(set) var zugang: Vermittlerzugang
    public private(set) var kopplung: Vermittlerkopplung?
    /// Wann zuletzt eine **angemeldete** Anfrage kam (stetige Uhr) — `nil`: noch keine.
    public private(set) var letzteAnfrage: TimeInterval?
    /// Der genaue Grund des letzten abgelehnten Koppelversuchs — **nur für den Menschen am
    /// Mac**; das iPad hört den gleichbleibenden Satz.
    public private(set) var letzterKoppelgrund: String?
    /// Wie oft hier schon ein Gerät gekoppelt hat — damit der Mac sich merken kann, dass es
    /// geschah (ohne die Zahl oder das Kennwort zu kennen).
    public private(set) var erfolgreicheKopplungen = 0

    /// Der Satz bei Erfolg — wortgleich mit `SATZ_VERBUNDEN` des Servers.
    public static let satzVerbunden =
        "Verbunden. Benutzer und Kennwort kommen nur dieses eine Mal über die Leitung."

    public init(zugang: Vermittlerzugang) {
        self.zugang = zugang
    }

    /// Eine neue Zahl zeigen. Die alte ist damit tot.
    @discardableResult
    public mutating func oeffneKopplung(jetzt: TimeInterval, zahl: String? = nil) -> Bool {
        guard let neu = Vermittlerkopplung(jetzt: jetzt, zahl: zahl) else { return false }
        kopplung = neu
        letzterKoppelgrund = nil
        return true
    }

    public mutating func schliesseKopplung() {
        kopplung?.schliesse()
    }

    /// **Das iPad vergessen:** neue Zugangsdaten. Ein gekoppeltes iPad bekommt danach die
    /// Tür (401) und muss neu koppeln. Am Heim-PC ändert sich nichts.
    public mutating func ersetzeZugang(_ neu: Vermittlerzugang) {
        zugang = neu
        letzteAnfrage = nil
    }

    /// Die Zahl, die gerade gilt — `nil`, wenn keine gilt.
    public func koppelzahl(jetzt: TimeInterval) -> String? {
        guard let kopplung, kopplung.stand(jetzt: jetzt) == .offen else { return nil }
        return kopplung.zahl
    }

    /// Die Tür am Kopf allein (siehe `Vermittlungsregel.vorab`) — `nil`: weiterlesen.
    public func vorab(_ kopf: Anfragekopf, jetzt: TimeInterval) -> Leitungsantwort? {
        if case .abweisen(let a)? = Vermittlungsregel.vorab(
            kopf, zugang: zugang, kopplung: kopplung?.stand(jetzt: jetzt)) {
            return a
        }
        return nil
    }

    /// Beantwortet eine ganz gelesene Anfrage — oder sagt, was weitergeht.
    public mutating func beantworte(_ anfrage: RoheAnfrage,
                                    jetzt: TimeInterval) -> Vermittlungsschritt {
        let entscheid = Vermittlungsregel.entscheide(anfrage, zugang: zugang,
                                                     kopplung: kopplung?.stand(jetzt: jetzt))
        if Vermittlungsregel.angemeldet(anfrage.kopf, zugang: zugang) {
            letzteAnfrage = jetzt
        }
        switch entscheid {
        case .abweisen(let a):
            return .antworte(a)
        case .weiterreichen(let w):
            return .weiterreichen(w)
        case .selbstKoppeln(.koppelseite):
            guard koppelzahl(jetzt: jetzt) != nil else {
                return .antworte(.fehler("Auf diesem Mac ist gerade kein Verbinden offen. Am "
                                         + "Mac eine neue Zahl zeigen lassen.", status: 404))
            }
            return .antworte(Leitungsantwort(
                status: 200,
                koepfe: [Kopfzeile("Content-Type", "text/html; charset=utf-8"),
                         Kopfzeile("Cache-Control", "no-store")],
                rumpf: Data(Koppelseite.html.utf8)))
        case .selbstKoppeln(.verbinden):
            return .antworte(verbinde(anfrage.rumpf, jetzt: jetzt))
        }
    }

    /// `POST /api/verbinden` am Mac — dieselben Antworten wie beim Server (Protokoll §3, §7).
    private mutating func verbinde(_ rumpf: Data, jetzt: TimeInterval) -> Leitungsantwort {
        let wunsch: [String: JSONWert]
        if rumpf.isEmpty {
            wunsch = [:]
        } else {
            guard let wert = try? JSONWert.lies(rumpf), let objekt = wert.alsObjekt else {
                return .fehler("Die Anfrage war nicht lesbar.", status: 400)
            }
            wunsch = objekt
        }
        guard var offen = kopplung else {
            return .fehler("Auf diesem Mac ist gerade kein Verbinden offen.", status: 403)
        }
        // EIN PIN, DER KEIN TEXT IST, ZAEHLT ALS FALSCHER VERSUCH — wie im Server, wo er
        // zur leeren Zeichenkette wird.
        let versuch = offen.pruefe(wunsch["pin"]?.alsText ?? "", jetzt: jetzt)
        kopplung = offen
        guard versuch.angenommen else {
            letzterKoppelgrund = versuch.grund + " (noch \(versuch.versucheUebrig) Versuche)"
            return .json(.objekt(["verbunden": .wahrheit(false),
                                  "satz": .text(versuch.satzFuerDasGeraet)]), status: 403)
        }
        letzterKoppelgrund = nil
        letzteAnfrage = jetzt
        erfolgreicheKopplungen += 1
        return .json(.objekt(["verbunden": .wahrheit(true),
                              "benutzer": .text(zugang.anmeldung.benutzer),
                              "kennwort": .text(zugang.anmeldung.kennwort),
                              "satz": .text(Vermittlerstand.satzVerbunden)]))
    }
}

// ============================================================ die Zeile «iPad» am Mac

/// Was die Startzeile «iPad» am Mac sagt (Blatt 13) — **mit echtem Signal**: «verbunden»
/// steht erst, wenn eine angemeldete Anfrage kam, und nur so lange, wie das iPad sich
/// meldet (es fragt alle zehn Sekunden, `Verbindungsstand.pruefabstand`).
public enum Vermittlerlage: Equatable, Sendable {
    /// Der Mac richtet sich ein (das Anbieten im WLAN steht noch nicht).
    case startet
    /// Er bietet sich an; kein iPad meldet sich. Mit der Zeit seit der letzten Anfrage,
    /// wenn es je eine gab.
    case wartet(letzteAnfrageVor: TimeInterval?)
    /// Eine Zahl gilt — sie gehört an den Bildschirm.
    case koppeln(zahl: String, nochSekunden: Int)
    /// Ein iPad hat sich eben gemeldet.
    case verbunden(letzteAnfrageVor: TimeInterval)
    /// Es geht nicht — mit dem Grund und was zu tun ist.
    case fehlt(grund: String)

    /// Wie lange nach der letzten Anfrage «verbunden» noch gilt: drei Fragerunden des iPad.
    public static let verbundenHoechstens: TimeInterval = 30

    /// Leitet die Lage ab. **Eine geltende Zahl geht vor «verbunden»**: Wer sie zeigen
    /// lässt, will ein (weiteres) iPad koppeln und muss sie sehen.
    public static func bestimme(bereit: Bool, fehler: String?, stand: Vermittlerstand,
                                jetzt: TimeInterval) -> Vermittlerlage {
        if let fehler { return .fehlt(grund: fehler) }
        guard bereit else { return .startet }
        if let zahl = stand.koppelzahl(jetzt: jetzt), let k = stand.kopplung {
            return .koppeln(zahl: zahl, nochSekunden: max(0, Int((k.faellig - jetzt).rounded(.up))))
        }
        if let letzte = stand.letzteAnfrage {
            let vor = max(0, jetzt - letzte)
            return vor <= verbundenHoechstens ? .verbunden(letzteAnfrageVor: vor)
                                              : .wartet(letzteAnfrageVor: vor)
        }
        return .wartet(letzteAnfrageVor: nil)
    }

    /// Das Wort der Startzeile: **steht / lädt / wartet / fehlt.**
    public var wort: String {
        switch self {
        case .startet: return "lädt"
        case .wartet, .koppeln: return "wartet"
        case .verbunden: return "steht"
        case .fehlt: return "fehlt"
        }
    }

    /// Der Satz daneben.
    public var satz: String {
        switch self {
        case .startet:
            return "Der Mac bietet sich dem iPad im WLAN an …"
        case .wartet(nil):
            return "Wartet auf das iPad — gleiches WLAN oder Hotspot dieses Mac."
        case .wartet(let vor?):
            return "Wartet auf das iPad. Letzte Anfrage \(Vermittlerlage.dauer(vor))."
        case .koppeln(let zahl, let noch):
            return "Am iPad koppeln und diese Zahl eingeben: \(Vermittlerlage.gruppiert(zahl)) "
                + "(gilt noch \(Vermittlerlage.frist(noch)))."
        case .verbunden(let vor):
            return "Verbunden, letzte Anfrage \(Vermittlerlage.dauer(vor))."
        case .fehlt(let grund):
            return grund
        }
    }

    /// «vor 4 s», «vor 3 min», «vor 2 h».
    static func dauer(_ s: TimeInterval) -> String {
        let ganz = Int(s.rounded(.down))
        if ganz < 60 { return "vor \(ganz) s" }
        if ganz < 3600 { return "vor \(ganz / 60) min" }
        return "vor \(ganz / 3600) h"
    }

    static func frist(_ s: Int) -> String {
        s >= 60 ? "\((s + 59) / 60) min" : "\(s) s"
    }

    /// «123 456» — drei und drei, wie man sie abliest. Das iPad nimmt beim Tippen nur die
    /// Ziffern.
    static func gruppiert(_ zahl: String) -> String {
        guard zahl.count == 6 else { return zahl }
        return String(zahl.prefix(3)) + " " + String(zahl.suffix(3))
    }
}

// ============================================================ in die Startzeile

extension Vermittlerlage {
    /// Die Lage als Zeile «iPad» der Mac-App (Blatt 13, `Startzeilen.swift`) — **dieselben
    /// Wörter und Sätze**, nur in den Typ der Startzeilen gebracht. Zwei Typen gibt es, weil
    /// die Vermittlung und die Startzeilen parallel entstanden (Vollbau v0.1.7); hier, an
    /// einer Stelle, wird übersetzt.
    ///
    /// `startet` wird «wartet», nicht «lädt»: «lädt» trägt bei den Startzeilen eine Uhr
    /// («seit 12 s»), und das Anbieten im WLAN hat keine, die etwas sagte.
    public func alsZeilenstand() -> Zeilenstand {
        switch self {
        case .startet, .wartet, .koppeln: return .wartet(satz: satz)
        case .verbunden: return .steht(satz: satz)
        case .fehlt(let grund): return .fehlt(grund: grund)
        }
    }
}

// =================================================================== das Anbieten

/// Wie sich der Mac im WLAN anbietet: **derselbe Dienst** wie der Heim-PC (`Marke.dienst`),
/// dieselbe Fassung, und ein Eintrag mehr, an dem das iPad ihn erkennt.
public enum Vermittlerangebot {
    /// Die Fassung des Protokolls — eine Abschrift von `rundruf.FASSUNG`, bewacht in
    /// `tests/test_ipad_geruest.py`.
    public static let fassung = "1"
    /// Woran das iPad den Mac erkennt (`GefundenerDienst.ueberDenMac`).
    public static let vermittler = "mac"

    /// Die TXT-Einträge, in fester Reihenfolge.
    public static var eintraege: [(String, String)] {
        [("fassung", fassung), ("vermittler", vermittler)]
    }

    /// Die TXT-Einträge in Leitungsform (RFC 6763 §6): je Eintrag ein Längenbyte und
    /// `schluessel=wert` — die Form, die `NWListener.Service(txtRecord:)` nimmt und
    /// `GefundenerDienst.txtEintraege` liest.
    public static var txt: Data {
        var aus = Data()
        for (s, w) in eintraege {
            let teil = Array("\(s)=\(w)".utf8.prefix(255))
            aus.append(UInt8(teil.count))
            aus.append(contentsOf: teil)
        }
        return aus
    }

    /// Der Name, unter dem der Mac im WLAN steht: «<Name der App> über <Name des Mac>».
    /// Höchstens 63 Bytes (die Grenze eines DNS-Namensteils), ohne ein Zeichen zu zerteilen.
    public static func dienstname(rechner: String) -> String {
        var name = "\(Marke.name) über \(rechner)"
        while name.utf8.count > 63 { name.removeLast() }
        return name
    }
}

/// Die Koppelseite des Mac für einen Browser (`GET /koppeln`) — ein Zahlenfeld, das
/// `POST /api/verbinden` ruft, sonst nichts. Die App braucht sie nicht.
public enum Koppelseite {
    public static var html: String {
        let name = Marke.name.replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
            .replacingOccurrences(of: ">", with: "&gt;")
        return """
        <!doctype html>
        <html lang="de"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>\(name) – mit dem Mac koppeln</title></head>
        <body style="font-family:system-ui,sans-serif;max-width:28em;margin:2em auto;padding:0 1em">
        <h1>Mit dem Mac koppeln</h1>
        <p>Die sechsstellige Zahl steht am Mac. Sie gilt zehn Minuten und für fünf Versuche.</p>
        <p><input id="zahl" inputmode="numeric" maxlength="6" autocomplete="one-time-code">
        <button id="los">Koppeln</button></p>
        <p id="satz"></p>
        <script>
        document.getElementById('los').onclick = async () => {
          const pin = document.getElementById('zahl').value.trim();
          let j = {};
          try {
            const r = await fetch('/api/verbinden', {method: 'POST',
              headers: {'Content-Type': 'application/json'}, body: JSON.stringify({pin})});
            j = await r.json();
          } catch (e) { j = {fehler: 'Der Mac antwortet nicht.'}; }
          document.getElementById('satz').textContent = j.verbunden
            ? j.satz + ' Benutzer: ' + j.benutzer + ' · Kennwort: ' + j.kennwort
            : (j.satz || j.fehler || 'Das hat nicht geklappt.');
        };
        </script>
        </body></html>
        """
    }
}
