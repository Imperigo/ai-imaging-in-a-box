import Foundation

// IPAD KOPPELN OHNE ABTIPPEN (Owner-Entscheide 99/99a/99b, 20.10.2026, Blatt 27 der
// Entwurfsflaeche «iPad koppeln ohne Abtippen»).
//
// Bis dahin tippte man am iPad zwei Dinge ab, die am Mac standen: die Adresse des Heim-PC
// und die sechsstellige Zahl aus «iPad koppeln». Jetzt gibt es zwei Wege ohne Abtippen und
// das Abtippen als letzten:
//
//   A · NAEHE   Der Mac bietet sich im offenen Koppelfenster ueber MultipeerConnectivity an
//               (lokal, ohne Entwicklerkonto). Das iPad fragt «Mit diesem Mac koppeln?»,
//               der Mac fragt «iPad möchte koppeln» — BEIDE bestaetigen. Dann schickt der Mac
//               ueber die verschluesselte Sitzung den Koppelschein: Adresse und Zahl, NIE das
//               Kennwort (Entscheid 99). Das iPad koppelt damit genau wie heute.
//   B · QR-CODE Das Koppelfenster zeigt denselben Koppelschein als QR-Code; das iPad liest
//               ihn mit der eigenen Kamera in der App (99b).
//   C · ZAHL    Adresse und Zahl eintippen, wie bisher.
//
// Alle drei gelten zwei Minuten (99a): So lange ist das Koppelfenster am Mac offen, dann
// hoert es von selbst auf, sich anzubieten, und der Schein laeuft ab.
//
// Hier stehen die ENTSCHEIDUNGEN, ohne Kamera und ohne Funk: wie der Schein aussieht und
// gelesen wird, wann der Mac senden darf, wie lange das Fenster offen ist. Die Apps rufen
// MultipeerConnectivity, CoreImage und die Kamera (`Verbindung/Naehesucher.swift`,
// `Verbindung/QRLeser.swift`, am Mac `Start/Naeheanbieter.swift`, `Start/IpadKoppelfenster.swift`).

/// Die Regeln der Nähe-Verbindung und des Koppelfensters.
public enum Naehekopplung {
    /// Wie lange das Koppelfenster am Mac offen ist — **zwei Minuten** (Entscheid 99a). Für
    /// Nähe, QR-Code und die angezeigte Zahl dieselbe Frist.
    public static let fenster: TimeInterval = 120

    /// Wie weit die Uhren von Mac und iPad auseinander sein dürfen, bevor ein Schein, der
    /// «länger als zwei Minuten» gilt, als gefälscht gilt — **gesetzt**: Beide stellen ihre
    /// Uhr übers Netz, Abweichungen von Sekunden sind üblich, von einer halben Minute nicht.
    public static let uhrenspiel: TimeInterval = 30

    /// Der `serviceType` für MultipeerConnectivity — aus der Marke.
    public static var dienstart: String { Marke.naehedienst }

    /// Was iOS im Manifest als `NSBonjourServices` dazu verlangt: beide Formen, tcp und udp.
    public static var bonjourDienste: [String] {
        ["_\(dienstart)._tcp", "_\(dienstart)._udp"]
    }

    /// Ob ein `serviceType` die Regeln von MultipeerConnectivity erfüllt: 1 bis 15 Zeichen,
    /// nur Kleinbuchstaben (ASCII), Ziffern und Bindestrich, mindestens ein Buchstabe, kein
    /// Bindestrich am Rand und keine zwei nebeneinander. Ein ungültiger wirft erst am Gerät.
    public static func istGueltigeDienstart(_ art: String) -> Bool {
        let zeichen = Array(art.unicodeScalars)
        guard (1...15).contains(zeichen.count) else { return false }
        let buchstabe: (Unicode.Scalar) -> Bool = { ("a"..."z").contains($0) }
        let ziffer: (Unicode.Scalar) -> Bool = { ("0"..."9").contains($0) }
        guard zeichen.allSatisfy({ buchstabe($0) || ziffer($0) || $0 == "-" }),
              zeichen.contains(where: buchstabe),
              zeichen.first != "-", zeichen.last != "-" else { return false }
        for i in 1..<max(1, zeichen.count) where zeichen[i] == "-" && zeichen[i - 1] == "-" {
            return false
        }
        return true
    }

    /// Was das iPad seiner Einladung mitgibt: **«der Mensch am iPad hat angenommen».** Der Mac
    /// nimmt keine Einladung ohne diesen Vermerk an — eine fremde App unter demselben Dienst
    /// bekäme so nicht einmal die Frage am Mac.
    public static let einladungsvermerk = Data("annehmen/1".utf8)

    /// Wie viele Bytes ein Gerätename für MultipeerConnectivity höchstens hat (`MCPeerID`
    /// wirft bei mehr als 63 Bytes UTF-8).
    public static let hoechstensNamensbytes = 63

    /// Der Name, unter dem sich ein Gerät zeigt — gekürzt auf 63 Bytes, **ohne ein Zeichen
    /// zu zerschneiden**, und `ersatz`, wenn das System keinen nennt.
    public static func anzeigename(_ roh: String, ersatz: String) -> String {
        let sauber = roh.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !sauber.isEmpty else { return ersatz }
        var name = ""
        for zeichen in sauber {
            let probe = name + String(zeichen)
            guard probe.utf8.count <= hoechstensNamensbytes else { break }
            name = probe
        }
        return name.isEmpty ? ersatz : name
    }

    /// Die Zeile «iPad» am Mac, wenn das Koppelfenster zu ist.
    public static let satzFensterZu = "Das Koppelfenster ist zu. Für ein iPad im Menü «iPad» "
        + "«iPad koppeln» neu öffnen."

    /// Was das iPad sagt, wenn der Mac die Sitzung beendet, bevor ein Schein kam.
    public static let satzMacAbgelehnt = "Der Mac hat nicht gekoppelt — abgelehnt, das Fenster "
        + "ist zu, oder die Verbindung brach ab. Am Mac «iPad koppeln» öffnen und neu versuchen."
}

// ============================================================ der Koppelschein

/// Was der Mac dem iPad zum Koppeln gibt — als QR-Code oder über die Nähe-Verbindung, **in
/// derselben Form**: die Adresse **des Mac** (verschlüsselt, `https`), die sechsstellige Zahl
/// **des Mac**, bis wann der Schein gilt — und seit Entscheid 118 (21.10.2026) der
/// **Fingerabdruck des Zertifikats des Mac**, den das iPad anheftet.
///
///     <schema>:2?adresse=<prozentkodiert>&zahl=482913&bis=<Unix-Sekunden>&abdruck=<64 hex>
///
/// **Kein Kennwort, kein Benutzer** (Entscheid 99): Die Zahl ist einmalig und läuft ab; das
/// Kennwort holt sich das iPad danach selbst, mit `POST /api/verbinden`, wie beim Abtippen.
/// Wer den QR-Code abfotografiert, hat zwei Minuten und wenige Versuche — kein Kennwort.
///
/// **Fassung 2 (Entscheid 118):** Bis 0.3.15 trug der Schein die Adresse **des Heim-PC** und
/// dessen Zahl, und das iPad koppelte direkt dort. Seither koppelt es **mit dem Mac** — und der
/// Abdruck im Schein ist das, was die Leitung sicher macht: Er kommt über einen Weg, den ein
/// Fremder im WLAN nicht umschreiben kann (Kamera, verschlüsselte Nähe-Sitzung), und das iPad
/// nimmt danach **nur dieses** Zertifikat an. Ein Schein der Fassung 1 kommt von einem Mac mit
/// altem Stand — er wird mit einem Satz abgelehnt, nicht still gelesen.
public struct Koppelschein: Equatable, Sendable {
    /// Die Fassung der Form. Eine andere wird abgelehnt, nicht geraten.
    public static let fassung = 2
    /// Höchstens so viele Bytes — ein Schein ist kurz; ein langer ist keiner von uns.
    public static let hoechstensBytes = 512
    /// Die Felder, **genau diese** — jedes andere lehnt `lies` ab.
    public static let felder = ["adresse", "zahl", "bis", "abdruck"]

    public static var schema: String { Marke.koppelschema }

    public let adresse: URL
    public let zahl: Kopplungszahl
    /// Bis wann der Schein gilt, in Unix-Sekunden (Mac und iPad haben verschiedene Uhren,
    /// aber dieselbe Weltzeit).
    public let bis: Int
    /// Der Fingerabdruck des Zertifikats des Mac (SHA-256, 64 Hex-Stellen, klein).
    public let abdruck: String

    /// Ein Schein — `nil`, wenn die Adresse keine des Mac ist (`Suche.pruefeMac(eingabe:)`:
    /// nur `https`), die Zahl nicht sechs Ziffern hat oder der Abdruck keiner ist. Was der Mac
    /// nicht eintippen liesse, stellt er auch nicht aus.
    public init?(adresse: URL, zahl: String, bis: Int, abdruck: String) {
        guard case .gut(let geprueft, _) = Suche.pruefeMac(eingabe: adresse.absoluteString),
              zahl.count == 6, let z = Kopplungszahl(zahl),
              let a = Fingerabdruck.normalisiere(abdruck) else { return nil }
        self.adresse = geprueft
        self.zahl = z
        self.bis = bis
        self.abdruck = a
    }

    /// Nur Buchstaben, Ziffern und `-._~` bleiben stehen (RFC 3986, «unreserved»); alles
    /// andere wird prozentkodiert — auch `:` und `/`, damit die Adresse ein Wert bleibt.
    static let unkodiert: CharacterSet = {
        var menge = CharacterSet()
        menge.insert(charactersIn: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
                     + "0123456789-._~")
        return menge
    }()

    /// Der Schein als Text — so steht er im QR-Code und geht über die Nähe-Verbindung.
    public var text: String {
        let roh = adresse.absoluteString
        let kodiert = roh.addingPercentEncoding(withAllowedCharacters: Koppelschein.unkodiert) ?? ""
        return "\(Koppelschein.schema):\(Koppelschein.fassung)?adresse=\(kodiert)"
            + "&zahl=\(zahl.ziffern)&bis=\(bis)&abdruck=\(abdruck)"
    }

    public var daten: Data { Data(text.utf8) }

    /// Wie viele ganze Sekunden er noch gilt — 0, wenn er abgelaufen ist.
    public func restSekunden(jetzt: TimeInterval) -> Int {
        max(0, Int((TimeInterval(bis) - jetzt).rounded(.down)))
    }

    /// Was beim Lesen herauskam: der Schein, oder der Satz, warum nicht.
    public enum Lesung: Equatable, Sendable {
        case gut(Koppelschein)
        case schlecht(String)
    }

    public static func lies(_ daten: Data, jetzt: TimeInterval) -> Lesung {
        guard daten.count <= hoechstensBytes else { return .schlecht(satzZuLang) }
        guard let text = String(data: daten, encoding: .utf8) else { return .schlecht(satzFremd) }
        return lies(text, jetzt: jetzt)
    }

    /// Liest einen Schein und prüft ihn — **in dieser Reihenfolge**: Länge, Schema, Fassung,
    /// Felder (genau die vier, keins doppelt), Zahl, Abdruck, Adresse, Frist. `jetzt` in
    /// Unix-Sekunden.
    public static func lies(_ text: String, jetzt: TimeInterval) -> Lesung {
        guard text.utf8.count <= hoechstensBytes else { return .schlecht(satzZuLang) }
        let kopf = "\(schema):"
        guard text.hasPrefix(kopf) else { return .schlecht(satzFremd) }
        let rest = text.dropFirst(kopf.count)
        guard let frage = rest.firstIndex(of: "?") else { return .schlecht(satzFremd) }
        let gelesen = String(rest[..<frage])
        // FASSUNG 1 KOMMT VON EINEM MAC MIT ALTEM STAND (Entscheid 118): Er schickt die Adresse
        // des Heim-PC — das iPad koppelte damit direkt dort, und die Mappe am Mac bliebe ihm
        // unsichtbar. Das wird gesagt, nicht still ausgefuehrt.
        if gelesen == "1" { return .schlecht(satzAlterMac) }
        guard gelesen == String(fassung) else { return .schlecht(satzFassung) }

        var werte: [String: String] = [:]
        for paar in rest[rest.index(after: frage)...].split(separator: "&",
                                                            omittingEmptySubsequences: false) {
            let teile = paar.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
            guard teile.count == 2, let name = teile[0].removingPercentEncoding,
                  let wert = teile[1].removingPercentEncoding else { return .schlecht(satzFremd) }
            // EIN FELD, DAS WIR NICHT KENNEN, ist kein Versehen: Ein Schein mit «kennwort=»
            // stammt nicht vom Mac — er stellt keinen aus.
            guard felder.contains(name) else { return .schlecht(satzFremd) }
            guard werte[name] == nil else { return .schlecht(satzFremd) }
            werte[name] = wert
        }
        guard let adresstext = werte["adresse"], let zahltext = werte["zahl"],
              let bistext = werte["bis"], let abdrucktext = werte["abdruck"] else {
            return .schlecht(satzFremd)
        }

        guard zahltext.count == 6, zahltext.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) })
        else { return .schlecht(satzZahl) }
        guard !bistext.isEmpty, bistext.count <= 12,
              bistext.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }),
              let bis = Int(bistext) else { return .schlecht(satzFremd) }
        // DER ABDRUCK GENAU SO, WIE DER MAC IHN SCHREIBT: 64 kleine Hex-Stellen. Eine andere
        // Schreibweise stammt nicht vom Mac.
        guard abdrucktext.count == 64, Fingerabdruck.normalisiere(abdrucktext) == abdrucktext
        else { return .schlecht(satzAbdruck) }

        let adresse: URL
        switch Suche.pruefeMac(eingabe: adresstext) {
        case .gut(let url, _): adresse = url
        case .schlecht(let grund): return .schlecht("Die Adresse im Code geht nicht: " + grund)
        }

        guard TimeInterval(bis) > jetzt else { return .schlecht(satzAbgelaufen) }
        // LAENGER ALS ZWEI MINUTEN stellt der Mac keinen aus. Ein solcher Schein ist von Hand
        // gemacht — oder die Uhr des iPad geht weit falsch; beides gehoert gesagt.
        guard TimeInterval(bis) - jetzt <= Naehekopplung.fenster + Naehekopplung.uhrenspiel
        else { return .schlecht(satzZuLange) }

        guard let schein = Koppelschein(adresse: adresse, zahl: zahltext, bis: bis,
                                        abdruck: abdrucktext) else {
            return .schlecht(satzFremd)
        }
        return .gut(schein)
    }

    public static let satzZuLang = "Der Code ist zu lang für einen Koppel-Code."
    public static let satzFremd = "Das ist kein Koppel-Code von \(Marke.name). Am Mac im Menü "
        + "«iPad» «iPad koppeln» öffnen und den Code dort lesen."
    public static let satzFassung = "Der Koppel-Code stammt aus einer anderen Fassung. "
        + "Beide Apps auf denselben Stand bringen oder die Zahl eintippen."
    /// Fassung 1: ein Mac mit altem Stand (vor Entscheid 118).
    public static let satzAlterMac = "Der Koppel-Code kommt von einem Mac mit altem Stand — er "
        + "schickt das iPad direkt zum Heim-PC. Seit dieser Fassung arbeitet das iPad über den "
        + "Mac: die Mac-App aktualisieren und den Code neu zeigen lassen."
    public static let satzZahl = "Im Koppel-Code steht keine sechsstellige Zahl."
    public static let satzAbdruck = "Im Koppel-Code fehlt das Zeichen des Mac (der Fingerabdruck "
        + "seines Zertifikats) — ohne es koppelt das iPad nicht verschlüsselt."
    public static let satzAbgelaufen = "Der Koppel-Code ist abgelaufen. Am Mac «iPad koppeln» "
        + "neu öffnen."
    public static let satzZuLange = "Der Koppel-Code gilt länger als zwei Minuten — so einen "
        + "stellt der Mac nicht aus. Geht die Uhr des iPad falsch?"
}

extension Koppelschein: CustomStringConvertible {
    /// **Ohne die Zahl** — sie gehört an den Bildschirm, nicht in eine Ausgabe.
    public var description: String {
        "Koppelschein(adresse: \(adresse.absoluteString), bis: \(bis), abdruck: "
            + "\(Fingerabdruck.zeichen(abdruck)))"
    }
}

// ============================================================ das Koppelfenster am Mac

/// Das offene Koppelfenster am Mac: ab wann, bis wann. **Höchstens zwei Minuten**, und nie
/// länger, als die Zahl drüben noch gilt.
///
/// Die Uhr ist die **Weltzeit** (Unix-Sekunden), nicht die Vermittlungsuhr: Der Schein geht
/// an ein anderes Gerät, und dort zählt nur eine Uhr, die beide kennen. Springt die Uhr des
/// Mac, irrt nur die Anzeige — gelten lässt die Zahl allein der Heim-PC.
public struct Koppelfenster: Equatable, Sendable {
    public let geoeffnet: TimeInterval
    public let schluss: TimeInterval

    /// `zahlGiltNoch`: was der Heim-PC zur Zahl sagte (`gilt_noch_s`); `nil`, wenn nichts.
    public init(jetzt: TimeInterval, zahlGiltNoch: TimeInterval?) {
        geoeffnet = jetzt
        let frist = min(Naehekopplung.fenster, max(0, zahlGiltNoch ?? Naehekopplung.fenster))
        schluss = jetzt + frist
    }

    public func offen(jetzt: TimeInterval) -> Bool {
        jetzt < schluss
    }

    /// Ganze Sekunden bis zum Schluss — aufgerundet, damit «0:00» erst steht, wenn es zu ist.
    public func rest(jetzt: TimeInterval) -> Int {
        max(0, Int((schluss - jetzt).rounded(.up)))
    }

    /// «1:59» — Minuten und Sekunden, wie eine Uhr sie zeigt.
    public static func uhrtext(_ sekunden: Int) -> String {
        let s = max(0, sekunden)
        let sek = s % 60
        return "\(s / 60):" + (sek < 10 ? "0" : "") + "\(sek)"
    }

    /// Der Schein für dieses Fenster: gültig bis zu seinem Schluss — mit der Adresse und dem
    /// Zertifikat **des Mac** (Entscheid 118).
    public func schein(adresse: URL, zahl: Kopplungszahl, abdruck: String) -> Koppelschein? {
        Koppelschein(adresse: adresse, zahl: zahl.ziffern, bis: Int(schluss.rounded(.down)),
                     abdruck: abdruck)
    }
}

// ============================================================ beide Seiten bestätigen

/// Die Absprache einer Nähe-Verbindung am Mac — **erst wenn beide Menschen bestätigt haben,
/// geht der Schein hinaus** (Entscheid 99).
///
/// 1. Das iPad lädt ein — nur nach «Annehmen», und dann mit `Naehekopplung.einladungsvermerk`.
/// 2. Der Mac fragt «iPad möchte koppeln»; erst «Koppeln» nimmt die Einladung an.
/// 3. Die Sitzung steht (verschlüsselt, `.required`).
/// 4. Der Mac schickt den Schein — einmal — und schliesst die Sitzung.
///
/// Ein Schritt ausser der Reihe zählt nicht: Ohne Vermerk kein «Koppeln», ohne «Koppeln»
/// kein «verbunden».
public struct Naeheabsprache: Equatable, Sendable {
    public private(set) var ipadNimmtAn = false
    public private(set) var macKoppelt = false
    public private(set) var verbunden = false
    public private(set) var gesendet = false

    public init() {}

    /// Eine Einladung kam. Gibt zurück, ob sie den Vermerk trägt — sonst lehnt der Mac sie
    /// ab, ohne zu fragen.
    public mutating func einladung(vermerk: Data?) -> Bool {
        ipadNimmtAn = vermerk == Naehekopplung.einladungsvermerk
        return ipadNimmtAn
    }

    /// Der Mensch am Mac drückt «Koppeln».
    public mutating func macSagtKoppeln() {
        guard ipadNimmtAn else { return }
        macKoppelt = true
    }

    /// Die Sitzung mit dem iPad steht.
    public mutating func sitzungSteht() {
        guard macKoppelt else { return }
        verbunden = true
    }

    /// Darf der Schein jetzt hinaus? Nur nach beiden Bestätigungen, über eine verschlüsselte
    /// Sitzung, im offenen Fenster — und nur einmal.
    public func darfSenden(verschluesselt: Bool, fensterOffen: Bool) -> Bool {
        ipadNimmtAn && macKoppelt && verbunden && verschluesselt && fensterOffen && !gesendet
    }

    public mutating func hatGesendet() {
        gesendet = true
    }
}

// ============================================================ ehrlich sagen, was geht

// DIE NAEHE SAGT, WENN SIE NICHTS FINDET (Owner-Befund vom 20.10.2026): Am Gerät koppelte der
// QR-Code; über die Nähe passierte nichts — am iPad kam kein «Mit diesem Mac koppeln?», und
// keine der beiden Seiten sagte, dass sie nichts fand. Seither melden beide ihren Zustand,
// und die Sätze und der Zeitpunkt stehen hier.

/// Was der Mac im Koppelfenster über die Nähe sagt — **eine kleine Zeile**.
public enum Naeheanbieterstand: Equatable, Sendable {
    /// Er bietet sich an; noch hat kein iPad gefragt.
    case bietetAn(name: String)
    /// Ein iPad hat gefragt («iPad möchte koppeln»).
    case anfrage(name: String)
    /// Das Anbieten startet nicht (`didNotStartAdvertisingPeer`) — mit dem Grund des Systems.
    case gehtNicht(grund: String)

    public var zeile: String {
        switch self {
        case .bietetAn(let name):
            return "In der Nähe: sucht … (sichtbar als «\(name)»)"
        case .anfrage(let name):
            return "In der Nähe: «\(name)» fragt an."
        case .gehtNicht(let grund):
            return "In der Nähe: geht hier nicht — \(Naehekopplung.ohnePunkt(grund)). Bitte den "
                + "QR-Code nehmen."
        }
    }

    /// Ob die Zeile ein Fehler ist (rot statt leise).
    public var istFehler: Bool {
        if case .gehtNicht = self { return true }
        return false
    }
}

/// Was das iPad über die Suche in der Nähe weiss — und **wann es aufgibt, still zu bleiben**.
public enum Naehesuchstand: Equatable, Sendable {
    /// Sucht, seit weniger als `Naehekopplung.ohneFundNach`.
    case sucht
    /// Sucht seit `ohneFundNach` und hat nichts gefunden — der QR-Code wird hervorgehoben.
    case keinFund
    /// Die Suche startet nicht (`didNotStartBrowsingForPeers`).
    case gehtNicht(grund: String)

    public var satz: String {
        switch self {
        case .sucht:
            return Naehekopplung.satzSucht
        case .keinFund:
            return Naehekopplung.satzKeinMac
        case .gehtNicht(let grund):
            return "Die Suche nach dem Mac in der Nähe startet nicht ("
                + Naehekopplung.ohnePunkt(grund) + "). Lokales Netzwerk erlaubt? Sonst den "
                + "QR-Code nehmen."
        }
    }

    /// Ob der Knopf «Mit QR-Code koppeln» hervorgehoben wird: sobald die Nähe nicht trägt.
    public var qrHervor: Bool { self != .sucht }
}

extension Naehekopplung {
    /// Nach wie vielen Sekunden Suche ohne Fund das iPad es **sagt** — **30 s**, gesetzt: Ein
    /// Mac mit offenem Koppelfenster zeigt sich in der Regel nach wenigen Sekunden; das
    /// Fenster ist zwei Minuten offen. Nach einer halben Minute bleibt genug Zeit für den
    /// QR-Code, bevor es zugeht.
    public static let ohneFundNach: TimeInterval = 30

    public static let satzSucht = "Am Mac im Menü «iPad» «iPad koppeln» öffnen — er erscheint "
        + "dann hier, zwei Minuten lang. Nichts abtippen."

    public static let satzKeinMac = "Kein Mac in der Nähe gefunden. Gleiches WLAN? Lokales "
        + "Netzwerk erlaubt? Sonst den QR-Code nehmen."

    /// Der Stand der Suche am iPad. `seit`: wann sie begann (`nil`: sie läuft nicht);
    /// `gefunden`: ob gerade ein Mac zu sehen ist; `fehler`: der Grund, wenn sie nicht startet.
    public static func suchstand(seit: Date?, jetzt: Date, gefunden: Bool,
                                 fehler: String?) -> Naehesuchstand {
        if let fehler { return .gehtNicht(grund: fehler) }
        guard let seit, !gefunden else { return .sucht }
        return jetzt.timeIntervalSince(seit) >= ohneFundNach ? .keinFund : .sucht
    }

    /// Ein Grund ohne Punkt am Ende — er steht mitten im Satz.
    static func ohnePunkt(_ grund: String) -> String {
        var g = grund.trimmingCharacters(in: .whitespacesAndNewlines)
        while g.hasSuffix(".") { g.removeLast() }
        return g.isEmpty ? "ohne Angabe des Grundes" : g
    }
}
