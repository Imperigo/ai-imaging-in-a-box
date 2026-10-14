import Foundation

// AKTUALISIEREN (Owner-Entscheid 84, 13.10.2026; Blatt 18 der Entwurfsflaeche).
//
// Anlass: Der Owner holte jede neue Fassung der Mac-App bisher von Hand als ZIP aus einem
// Lauf der Pruefstrecke, und am iPad merkte er nicht, dass es eine neue gab. Seither legt die
// Pruefstrecke bei NEUER NUMMER (84b) eine Freigabe auf GitHub ab (`.github/workflows/ipad.yml`,
// Job `freigabe`), und beide Apps fragen BEIM START UND EINMAL TAEGLICH (84a) danach.
//
// WAS HIER STEHT, IST ALLES, WAS ENTSCHIEDEN WIRD — die Apps sind eine duenne Schicht:
// Nummern vergleichen, die Antwort der GitHub-API deuten, Paket und Pruefsumme waehlen, die
// Tagesregel, das Bundle nach dem Entpacken pruefen und die Saetze. Nur Foundation, damit es
// unter Linux pruefbar ist; die Pruefsumme selbst rechnet die Mac-App (CryptoKit), weil der
// Kern unter Linux kein CryptoKit hat.

/// Eine Versionsnummer mit **genau drei Teilen** (`0.2.1`), wie Visbox sie seit Entscheid 66
/// traegt (`tests/test_versionsnummer.py`).
///
/// Verglichen wird **Teil fuer Teil als Zahl**, nicht als Text: Als Text stuende `0.10.0` vor
/// `0.9.0`, und die App boete eine aeltere Fassung als neuere an.
public struct Fassungsnummer: Comparable, Hashable, CustomStringConvertible, Sendable {
    public let haupt: Int
    public let neben: Int
    public let flick: Int

    /// Liest `0.2.1` und die Form des Tags, `v0.2.1`. **Streng:** zwei oder vier Teile,
    /// Buchstaben, Vorzeichen oder fuehrende Nullen (`0.02.1`) sind keine Nummer — eine
    /// Nummer, die zwei Lesarten hat, haette auch zwei Vergleiche.
    public init?(_ text: String) {
        var rest = Substring(text.trimmingCharacters(in: .whitespacesAndNewlines))
        if rest.hasPrefix("v") { rest = rest.dropFirst() }
        let teile = rest.split(separator: ".", omittingEmptySubsequences: false)
        guard teile.count == 3 else { return nil }
        var zahlen: [Int] = []
        for teil in teile {
            guard !teil.isEmpty, teil.count <= 6,
                  teil.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }),
                  !(teil.count > 1 && teil.hasPrefix("0")),
                  let zahl = Int(teil) else { return nil }
            zahlen.append(zahl)
        }
        haupt = zahlen[0]; neben = zahlen[1]; flick = zahlen[2]
    }

    public static func < (a: Fassungsnummer, b: Fassungsnummer) -> Bool {
        (a.haupt, a.neben, a.flick) < (b.haupt, b.neben, b.flick)
    }

    public var description: String { "\(haupt).\(neben).\(flick)" }

    /// Der Name des Tags in der Freigabe — dieselbe Form, die die Pruefstrecke setzt.
    public var tag: String { "v\(description)" }
}

/// Eine Datei in einer Freigabe — **nur solche, die von genau diesem Repo stammen** (die
/// Pruefung steht in `Aktualisierung.istAusDiesemRepo`).
public struct Freigabeanlage: Equatable, Sendable {
    public let name: String
    public let adresse: URL
    public let groesse: Int
    /// Die Pruefsumme, die GitHub selbst beim Hochladen gerechnet hat (`sha256:<hex>`), seit
    /// 2025 in der Antwort. Fehlt sie, gilt allein die Datei der Pruefsummen.
    public let githubSumme: String?

    public init(name: String, adresse: URL, groesse: Int, githubSumme: String? = nil) {
        self.name = name
        self.adresse = adresse
        self.groesse = groesse
        self.githubSumme = githubSumme
    }
}

/// Eine Freigabe auf GitHub, gedeutet.
public struct Freigabe: Equatable, Sendable {
    public let nummer: Fassungsnummer
    /// Der Text der Neuerungen — das Fassungsblatt (`docs/VISBOX_<nummer>_<datum>.md`), so
    /// wie die Pruefstrecke es als Begleittext hochlaedt.
    public let begleittext: String
    /// Die Seite der Freigabe auf GitHub, zum Nachlesen.
    public let seite: URL?
    public let anlagen: [Freigabeanlage]

    public init(nummer: Fassungsnummer, begleittext: String, seite: URL?,
                anlagen: [Freigabeanlage]) {
        self.nummer = nummer
        self.begleittext = begleittext
        self.seite = seite
        self.anlagen = anlagen
    }

    public func anlage(_ name: String) -> Freigabeanlage? { anlagen.first { $0.name == name } }
}

/// Was beim Aktualisieren schiefgehen kann — **jedes mit einem Satz**, den die App zeigt.
public enum Aktualisierungsfehler: Error, Equatable, Sendable {
    case unlesbar
    case keineNummer(String)
    case entwurf
    case ohneMacPaket
    case ohnePruefsummen
    case pruefsummeFehlt
    case pruefsummeFalsch
    case groesseFalsch(erwartet: Int, erhalten: Int)
    case fremdeAdresse
    case keinBuendel
    case fremdeKennung(String)
    case falscheNummer(String)
    case unterschriftGebrochen
    case ortGesperrt(String)
    case ersetzenScheiterte(String)
    case neustartScheiterte

    public var satz: String {
        switch self {
        case .unlesbar:
            return "Die Antwort von GitHub ist nicht lesbar. Es bleibt bei dieser Fassung."
        case .keineNummer(let tag):
            return "Die Freigabe «\(tag)» trägt keine Nummer mit drei Teilen. Es bleibt bei dieser Fassung."
        case .entwurf:
            return "Die neueste Freigabe ist ein Entwurf oder eine Vorabfassung — sie wird nicht angeboten."
        case .ohneMacPaket:
            return "Die Freigabe enthält kein Paket für den Mac."
        case .ohnePruefsummen:
            return "Die Freigabe enthält keine Prüfsummen. Ohne sie wird nichts ersetzt."
        case .pruefsummeFehlt:
            return "Für das Mac-Paket steht keine Prüfsumme in der Freigabe. Ohne sie wird nichts ersetzt."
        case .pruefsummeFalsch:
            return "Die Prüfsumme stimmt nicht — die geladene Datei ist nicht die der Freigabe. Nichts wurde ersetzt."
        case .groesseFalsch(let erwartet, let erhalten):
            return "Die geladene Datei ist \(erhalten) Bytes gross, erwartet waren \(erwartet). Nichts wurde ersetzt."
        case .fremdeAdresse:
            return "Die Datei liegt nicht in diesem Repo. Nichts wurde geladen."
        case .keinBuendel:
            return "Im Paket liegt nicht genau eine App. Nichts wurde ersetzt."
        case .fremdeKennung(let kennung):
            return "Die App im Paket trägt eine fremde Kennung («\(kennung)»). Nichts wurde ersetzt."
        case .falscheNummer(let nummer):
            return "Die App im Paket trägt die Nummer «\(nummer)», nicht die der Freigabe. Nichts wurde ersetzt."
        case .unterschriftGebrochen:
            return "Die Unterschrift der App im Paket ist gebrochen. Nichts wurde ersetzt."
        case .ortGesperrt(let grund):
            return grund
        case .ersetzenScheiterte(let grund):
            return "Ersetzen gescheitert: \(grund) Die bisherige App ist unverändert."
        case .neustartScheiterte:
            return "Ersetzt, aber der Neustart ging nicht. Bitte die App beenden und neu öffnen."
        }
    }
}

/// Wo das Aktualisieren gerade steht — fuer das Blatt am Mac (Blatt 18).
public enum Aktualisierungsphase: Equatable, Sendable {
    /// Angeboten, noch nichts geklickt: «Später» / «Laden und ersetzen».
    case angeboten
    /// Laedt; der Anteil 0…1, oder `nil`, solange die Groesse unbekannt ist.
    case laedt(Double?)
    case prueft
    case ersetzt
    /// Ersetzt und geprueft — wartet auf «Neu starten».
    case fertig
    case gescheitert(Aktualisierungsfehler)

    public var satz: String {
        switch self {
        case .angeboten: return ""
        case .laedt(let anteil):
            if let anteil { return "Lädt … \(Int((anteil * 100).rounded())) %" }
            return "Lädt …"
        case .prueft: return "Prüfsumme wird abgeglichen …"
        case .ersetzt: return "Prüfsumme stimmt. Die App wird ersetzt …"
        case .fertig: return "Ersetzt. Prüfsumme und Kennung stimmen — die App startet neu …"
        case .gescheitert(let fehler): return fehler.satz
        }
    }
}

public enum Aktualisierung {
    // ------------------------------------------------------------------ Woher

    /// **Genau dieses Repo** — oeffentlich, darum ohne Konto und ohne Token zu fragen.
    /// `tests/test_ipad_geruest.py` haelt beide Namen gegen die Pruefstrecke.
    public static let besitzer = "Imperigo"
    public static let repo = "ai-imaging-in-a-box"

    /// Die neueste Freigabe (GitHub zaehlt Entwuerfe und Vorabfassungen hier nicht mit).
    public static var abfrage: URL {
        URL(string: "https://api.github.com/repos/\(besitzer)/\(repo)/releases/latest")!
    }

    /// Die Kopfzeilen der Frage — die Form, die GitHub fuer seine Schnittstelle empfiehlt.
    /// **Kein Token:** Das Repo ist oeffentlich, und ein Token in einer App, die als ZIP
    /// herumgereicht wird, waere keines mehr (Regel 3).
    public static func kopfzeilen(laufend: Fassungsnummer?) -> [String: String] {
        ["Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28",
         "User-Agent": "\(Marke.name)/\(laufend?.description ?? "0.0.0")"]
    }

    /// Die Namen der Dateien in der Freigabe — aus der Marke, wie die Pruefstrecke sie aus
    /// der plist nimmt (`CFBundleName`), nicht ein zweites Mal ausgeschrieben.
    public static var macPaket: String { "\(Marke.name)-mac.zip" }
    public static var ipadPaket: String { "\(Marke.name).swiftpm.zip" }
    public static let pruefsummen = "SHA256SUMS.txt"

    /// Ob eine Adresse eine Datei **dieses** Repos in einer Freigabe nennt:
    /// `https://github.com/<besitzer>/<repo>/releases/download/<tag>/<name>` — nichts davor,
    /// nichts danach, kein anderer Rechner, kein Anschluss, keine Anmeldung in der Adresse.
    public static func istAusDiesemRepo(_ adresse: URL, tag: String? = nil) -> Bool {
        guard adresse.scheme == "https", adresse.host?.lowercased() == "github.com",
              adresse.port == nil, adresse.user == nil, adresse.password == nil,
              adresse.query == nil, adresse.fragment == nil else { return false }
        let teile = adresse.pathComponents
        guard teile.count == 7, teile[0] == "/", teile[1] == besitzer, teile[2] == repo,
              teile[3] == "releases", teile[4] == "download",
              !teile[5].isEmpty, !teile[6].isEmpty,
              teile[5] != "..", teile[6] != ".." else { return false }
        if let tag, teile[5] != tag { return false }
        return true
    }

    /// Wohin GitHub beim Laden **weiterleiten** darf: nur https, nur GitHub selbst und seine
    /// Ablage (`*.githubusercontent.com`). Die Pruefsumme schuetzt den Inhalt ohnehin; diese
    /// Regel haelt fest, dass eine Weiterleitung nicht still zu einem fremden Rechner geht.
    public static func istErlaubteWeiterleitung(_ adresse: URL) -> Bool {
        guard adresse.scheme == "https", let rechner = adresse.host?.lowercased(),
              adresse.user == nil, adresse.password == nil else { return false }
        return rechner == "github.com" || rechner.hasSuffix(".githubusercontent.com")
    }

    // ------------------------------------------------------------------ Antwort deuten

    private struct Antwort: Decodable {
        let tag_name: String
        let body: String?
        let draft: Bool?
        let prerelease: Bool?
        let html_url: String?
        let assets: [Anlage]?

        struct Anlage: Decodable {
            let name: String
            let size: Int?
            let browser_download_url: String
            let state: String?
            let digest: String?
        }
    }

    /// Die Antwort von `GET …/releases/latest`, gedeutet. **Anlagen, die nicht aus diesem
    /// Repo und diesem Tag stammen, fallen weg** — sie werden nie geladen.
    public static func deute(_ daten: Data) throws -> Freigabe {
        guard let antwort = try? JSONDecoder().decode(Antwort.self, from: daten) else {
            throw Aktualisierungsfehler.unlesbar
        }
        if antwort.draft == true || antwort.prerelease == true {
            throw Aktualisierungsfehler.entwurf
        }
        guard let nummer = Fassungsnummer(antwort.tag_name), antwort.tag_name.hasPrefix("v")
        else { throw Aktualisierungsfehler.keineNummer(antwort.tag_name) }
        let anlagen: [Freigabeanlage] = (antwort.assets ?? []).compactMap { a in
            guard a.state == nil || a.state == "uploaded",
                  let adresse = URL(string: a.browser_download_url),
                  istAusDiesemRepo(adresse, tag: nummer.tag),
                  adresse.lastPathComponent == a.name else { return nil }
            let summe = a.digest.flatMap { d -> String? in
                guard d.lowercased().hasPrefix("sha256:") else { return nil }
                return istSumme(String(d.dropFirst(7))) ? String(d.dropFirst(7)).lowercased() : nil
            }
            return Freigabeanlage(name: a.name, adresse: adresse, groesse: a.size ?? -1,
                                  githubSumme: summe)
        }
        return Freigabe(nummer: nummer, begleittext: antwort.body ?? "",
                        seite: antwort.html_url.flatMap(URL.init(string:)), anlagen: anlagen)
    }

    // ------------------------------------------------------------------ Nummer und Angebot

    /// Die Nummer der laufenden App, aus ihrer `Info.plist` (`CFBundleShortVersionString`).
    public static func laufendeNummer(_ info: [String: Any]?) -> Fassungsnummer? {
        (info?["CFBundleShortVersionString"] as? String).flatMap(Fassungsnummer.init)
    }

    /// Ob die Freigabe angeboten wird: **nur, wenn ihre Nummer groesser ist** als die laufende
    /// (84b). Ist die laufende Nummer unbekannt, wird nichts angeboten — eine App, die ihre
    /// eigene Nummer nicht kennt, kann nicht wissen, ob sie aelter ist.
    public static func bietetAn(_ freigabe: Freigabe, laufend: Fassungsnummer?) -> Bool {
        guard let laufend else { return false }
        return freigabe.nummer > laufend
    }

    // ------------------------------------------------------------------ Tagesregel (84a)

    /// Wie lange nach einer Frage die naechste faellig ist. Beim Start wird **immer** gefragt;
    /// laeuft die App laenger, fragt sie, sobald diese Spanne um ist. **Eine Stunde** seit
    /// Entscheid 87 (14.10.2026, Owner per Auswahl; vorher ein Tag, 84a): Eine neue Fassung
    /// soll ankommen wie bei jeder App, ohne zusaetzlichen Dienst.
    public static let abstand: TimeInterval = 60 * 60

    /// Ob jetzt gefragt wird. Nie gefragt → ja. Liegt die letzte Frage **in der Zukunft**
    /// (die Uhr wurde zurueckgestellt), auch ja — sonst fragte die App womoeglich nie wieder.
    public static func sollFragen(letzte: Date?, jetzt: Date) -> Bool {
        guard let letzte else { return true }
        if letzte > jetzt { return true }
        return jetzt.timeIntervalSince(letzte) >= abstand
    }

    // ------------------------------------------------------------------ Pruefsumme

    /// Ob ein Text eine SHA-256-Summe in Sechzehnerschrift ist (64 Stellen).
    public static func istSumme(_ text: String) -> Bool {
        text.count == 64 && text.unicodeScalars.allSatisfy {
            ("0"..."9").contains($0) || ("a"..."f").contains($0) || ("A"..."F").contains($0)
        }
    }

    /// Die erwartete Summe einer Datei aus der Datei der Pruefsummen — der Form, die
    /// `sha256sum` schreibt (`<summe>  <name>`, im Binaermodus `<summe> *<name>`).
    ///
    /// **Steht der Name zweimal mit verschiedenen Summen, gilt keine** — welche die richtige
    /// waere, liesse sich nicht sagen.
    public static func summe(fuer name: String, in text: String) -> String? {
        var gefunden: Set<String> = []
        for zeile in text.split(whereSeparator: \.isNewline) {
            let teile = zeile.split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true)
            guard teile.count == 2, istSumme(String(teile[0])) else { continue }
            var datei = teile[1].trimmingCharacters(in: .whitespaces)
            if datei.hasPrefix("*") { datei.removeFirst() }
            if datei == name { gefunden.insert(teile[0].lowercased()) }
        }
        return gefunden.count == 1 ? gefunden.first : nil
    }

    /// Prueft die geladene Datei: Groesse wie in der Freigabe, Summe wie in der Datei der
    /// Pruefsummen — und, wenn GitHub selbst eine Summe nennt, auch wie diese.
    public static func pruefe(anlage: Freigabeanlage, groesse: Int, summe berechnet: String,
                              summenDatei: String) -> Aktualisierungsfehler? {
        if anlage.groesse >= 0 && anlage.groesse != groesse {
            return .groesseFalsch(erwartet: anlage.groesse, erhalten: groesse)
        }
        guard let erwartet = summe(fuer: anlage.name, in: summenDatei) else {
            return .pruefsummeFehlt
        }
        let ist = berechnet.lowercased()
        guard ist == erwartet else { return .pruefsummeFalsch }
        if let github = anlage.githubSumme, github != ist { return .pruefsummeFalsch }
        return nil
    }

    /// Eine Summe in Sechzehnerschrift, klein — die Form, in der `sha256sum` sie schreibt.
    public static func sechzehner<S: Sequence>(_ bytes: S) -> String where S.Element == UInt8 {
        let stellen = Array("0123456789abcdef")
        var text = ""
        for b in bytes {
            text.append(stellen[Int(b >> 4)])
            text.append(stellen[Int(b & 0x0F)])
        }
        return text
    }

    // ------------------------------------------------------------------ Ersetzen

    /// Welches Bundle im entpackten Ordner die neue App ist: **genau eines** auf oberster
    /// Ebene, das auf `.app` endet. Zwei oder keines heisst, das Paket ist nicht unseres.
    public static func waehleBuendel(_ namen: [String]) -> String? {
        let apps = namen.filter { $0.hasSuffix(".app") && !$0.hasPrefix(".") && !$0.contains("/") }
        return apps.count == 1 ? apps[0] : nil
    }

    /// Prueft die `Info.plist` der neuen App: **dieselbe Kennung wie die laufende**, die
    /// Nummer der Freigabe, und eine App (`APPL`). Ersetzt wird nur, was hier besteht.
    public static func pruefeBuendel(_ info: [String: Any], kennung: String,
                                     nummer: Fassungsnummer) -> Aktualisierungsfehler? {
        let gefunden = info["CFBundleIdentifier"] as? String ?? ""
        guard gefunden == kennung, info["CFBundlePackageType"] as? String == "APPL" else {
            return .fremdeKennung(gefunden)
        }
        let traegt = info["CFBundleShortVersionString"] as? String ?? ""
        guard Fassungsnummer(traegt) == nummer else { return .falscheNummer(traegt) }
        return nil
    }

    /// Ob die laufende App an ihrem Ort ersetzt werden kann. **Zwei Faelle nicht:** Sie laeuft
    /// nicht aus einem Bundle (beim Entwickeln), oder macOS hat sie beim ersten Oeffnen an
    /// einen verborgenen, schreibgeschuetzten Ort verschoben («App Translocation»: eine App,
    /// die aus dem Download-Ordner geoeffnet wurde, ohne sie zu verschieben).
    public static func pruefeOrt(_ pfad: String) -> Aktualisierungsfehler? {
        guard pfad.hasSuffix(".app") || pfad.hasSuffix(".app/") else {
            return .ortGesperrt("Die App läuft nicht aus einem Bundle — es gibt nichts zu ersetzen.")
        }
        if pfad.contains("/AppTranslocation/") {
            return .ortGesperrt("macOS hat die App an einen schreibgeschützten Ort verschoben. "
                                + "Bitte \(Marke.name) in den Ordner «Programme» ziehen, neu öffnen "
                                + "und dann aktualisieren.")
        }
        return nil
    }

    // ------------------------------------------------------------------ Neuerungen

    /// Die Neuerungen aus dem Fassungsblatt, Zeile fuer Zeile — fuer das Blatt am Mac.
    ///
    /// Gelesen wird der Abschnitt, dessen Ueberschrift (`## …`) «neu» enthaelt, bis zur
    /// naechsten Ueberschrift derselben Stufe: aus einer Tabelle die erste Spalte (ohne Kopf-
    /// und Trennzeile), aus einer Liste der Punkt. Fehlt der Abschnitt, ist die Liste leer, und
    /// die App verweist auf die Seite der Freigabe.
    public static func neuerungen(aus text: String) -> [String] {
        var drin = false
        var zeilen: [String] = []
        var tabellenzeile = 0
        for roh in text.split(omittingEmptySubsequences: false, whereSeparator: \.isNewline) {
            let zeile = roh.trimmingCharacters(in: .whitespaces)
            if zeile.hasPrefix("## ") {
                if drin { break }
                drin = zeile.lowercased().contains("neu")
                tabellenzeile = 0
                continue
            }
            guard drin, !zeile.isEmpty else { continue }
            if zeile.hasPrefix("|") {
                tabellenzeile += 1
                let zellen = zeile.split(separator: "|", omittingEmptySubsequences: false)
                    .map { $0.trimmingCharacters(in: .whitespaces) }
                    .dropFirst()
                guard let erste = zellen.first, !erste.isEmpty, tabellenzeile > 1,
                      !erste.allSatisfy({ $0 == "-" || $0 == ":" }) else { continue }
                zeilen.append(erste)
            } else if zeile.hasPrefix("* ") || zeile.hasPrefix("- ") {
                zeilen.append(String(zeile.dropFirst(2)))
            } else {
                zeilen.append(zeile)
            }
        }
        return zeilen
    }

    // ------------------------------------------------------------------ Saetze

    /// Der Knopf in der Werkzeugleiste der Mac-App (Blatt 18).
    public static func knopf(_ nummer: Fassungsnummer) -> String {
        "● \(nummer) verfügbar — Aktualisieren"
    }

    /// Die Ueberschrift des Blatts am Mac.
    public static func titel(_ nummer: Fassungsnummer) -> String { "\(Marke.name) \(nummer)" }

    /// Die Zeile unter der Ueberschrift.
    public static func untertitel(laufend: Fassungsnummer) -> String {
        "Diese App ist \(laufend). Neu ist:"
    }

    /// **Der Hinweis am iPad** — selbst ersetzen darf eine iPad-App nicht (nur ueber App Store
    /// oder TestFlight, mit bezahltem Konto; Entscheid 84).
    public static func ipadHinweis(_ nummer: Fassungsnummer) -> String {
        "Neue Fassung \(nummer) verfügbar — am Mac in Xcode aufspielen"
    }

    /// Der Hinweis im Blatt am Mac, **vor** dem Klick: Die neue App traegt wie jede aus der
    /// Pruefstrecke nur die Behelfs-Unterschrift; ihre Unterschrift ist eine andere als die
    /// der alten, und macOS kann darum einmal nachfragen.
    public static let behelfsHinweis =
        "Die App trägt nur eine Behelfs-Unterschrift. macOS verlangt darum eventuell einmal "
        + "«Trotzdem öffnen» (Systemeinstellungen → Datenschutz & Sicherheit) und fragt "
        + "eventuell, ob sie den Schlüsselbund wieder benutzen darf."

    public static let spaeter = "Später"
    public static let ladenUndErsetzen = "Laden und ersetzen"
    public static let neuStarten = "Neu starten"
}

// ======================================================================= iPad: Ablauf

/// Wann die iPad-App ablaeuft — gelesen aus dem **Provisioning-Profil**, das Xcode beim
/// Aufspielen ins Bundle legt (`embedded.mobileprovision`).
///
/// Anlass (Entscheid 84, 13.10.2026): Mit dem kostenlosen Apple-Konto (Entscheid 23) laeuft die
/// App je **7 Tage**; danach startet sie nicht mehr, bis Xcode sie neu aufspielt. Das Ablauf-
/// datum steht im Profil (`ExpirationDate`). Die Datei ist eine unterschriebene Huelle (CMS) um
/// eine gewoehnliche plist in Klartext — gelesen wird nur die plist, die Unterschrift prueft
/// das System selbst beim Start.
///
/// **Wann es keinen Hinweis gibt, und das ist gewollt:** im Simulator, in Swift Playgrounds
/// und in einer App aus dem App Store liegt kein solches Profil im Bundle. Dann gibt `ablauf`
/// `nil`, und die App sagt nichts — lieber kein Hinweis als ein erfundener.
public enum Bereitstellungsprofil {
    /// Ab wann vor dem Ablauf gewarnt wird: zwei Tage — genug, um an den Mac zu kommen.
    public static let warnung: TimeInterval = 2 * 24 * 60 * 60

    /// Das Ablaufdatum aus dem Inhalt von `embedded.mobileprovision`, oder `nil`.
    public static func ablauf(aus daten: Data) -> Date? {
        guard let anfang = daten.range(of: Data("<?xml".utf8)),
              let ende = daten.range(of: Data("</plist>".utf8),
                                     in: anfang.lowerBound..<daten.endIndex) else { return nil }
        let plist = daten.subdata(in: anfang.lowerBound..<ende.upperBound)
        guard let wurzel = try? PropertyListSerialization.propertyList(from: plist, format: nil),
              let werte = wurzel as? [String: Any] else { return nil }
        return werte["ExpirationDate"] as? Date
    }

    /// Der Satz am iPad, **nur wenn der Ablauf naht** (`warnung`), sonst `nil`.
    public static func hinweis(ablauf: Date, jetzt: Date) -> String? {
        let rest = ablauf.timeIntervalSince(jetzt)
        guard rest <= warnung else { return nil }
        let tun = "am Mac in Xcode neu aufspielen (▶)"
        if rest <= 0 { return "Die Freischaltung dieser App ist abgelaufen — \(tun)." }
        if rest < 24 * 60 * 60 { return "Die App läuft in weniger als einem Tag ab — \(tun)." }
        let tage = Int((rest / (24 * 60 * 60)).rounded(.up))
        return "Die App läuft in \(tage) Tagen ab — \(tun)."
    }
}
