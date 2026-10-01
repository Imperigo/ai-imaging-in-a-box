import Foundation

// DIE KOPPLUNG ZWISCHEN IPAD UND MAC — eine eigene, lokale, mit denselben Regeln wie die
// der HomeStation (`aiimaging.kopplung`, Protokoll §7).
//
// Unterwegs gibt sich der Mac dem iPad gegenueber als Server aus (Protokoll §8b). Die
// Anmeldung trennt darum ZWEI Strecken:
//
//   iPad ↔ Mac       eine Kopplung AM MAC: sechsstellige Zahl, dafuer eigene, zufaellige
//                    Zugangsdaten des Mac (dieser Kern).
//   Mac ↔ Heim-PC    das Kennwort des Heim-PC aus dem Schluesselbund des Mac — das iPad
//                    bekommt es NIE.
//
// *Wer ein Kennwort weitergibt, damit ein anderer es weitergeben kann, hat es verteilt.*
// Das iPad bekommt nur, was der Mac zurueckziehen kann (`Vermittlerstand.ersetzeZugang`),
// ohne dass sich am Heim-PC etwas aendert.
//
// Die Regeln sind eine ABSCHRIFT von `src/aiimaging/kopplung.py` (Frist 600 s, 5 Versuche,
// 6 Stellen, Reihenfolge der Zustaende, ein Satz fuer das Geraet), weil der Mac Python
// nicht laufen laesst. `tests/test_ipad_geruest.py` haelt Frist, Versuche und Stellen gegen
// das Python-Modul.

/// Woran eine Kopplung ist — **vier Zustände**, wie an der HomeStation (Protokoll §7).
public enum Kopplungsstand: String, Equatable, Sendable {
    case offen
    case abgelaufen
    case aufgebraucht
    case verbraucht
}

/// Was ein Versuch ergab — mit **zwei** Sätzen: dem genauen für den Menschen am Mac und
/// dem immer gleichen für das Gerät.
public struct Kopplungsversuch: Equatable, Sendable {
    public let angenommen: Bool
    public let stand: Kopplungsstand
    /// Genau, für den Menschen **am Mac**. Leer, wenn es geklappt hat.
    public let grund: String
    /// Unbestimmt, für das **iPad** — immer derselbe, egal woran es lag. Leer bei Erfolg.
    public let satzFuerDasGeraet: String
    public let versucheUebrig: Int
}

/// Eine offene Kopplung am Mac: die Zahl, ihre Frist und was von ihr übrig ist.
///
/// **Die Uhr wird hineingereicht** (`jetzt`), nicht gelesen: Die Proben stellen sie, der Mac
/// gibt seine Vermittlungsuhr (`Vermittlungsuhr` im Mac-Teil), die nicht zurückspringen kann
/// — wer die Wanduhr zurückstellt, verlängerte sonst die Frist (dieselbe Überlegung wie in
/// `kopplung.py`) — **und die im Ruhezustand weiterläuft**: Eine Uhr, die bei zugeklapptem
/// Deckel stillsteht, liesse eine Zahl über Nacht gelten. Welche Uhr das auf welchem System
/// ist, weiss nur der Mac-Teil; der Kern bleibt ohne sie (Sicherheitsdurchsicht vom
/// 01.10.2026: hier stand `systemUptime`, und die steht im Ruhezustand still). Der Zustand
/// liegt **nur im Arbeitsspeicher**: Eine Zahl, die einen Neustart überlebte, wäre eine, die
/// jemand vor drei Wochen abgelesen hat.
public struct Vermittlerkopplung: Sendable {

    /// Wie lange eine Zahl gilt — Abschrift von `kopplung.FRIST_S`.
    public static let frist: TimeInterval = 600
    /// Wie oft geraten werden darf — Abschrift von `kopplung.VERSUCHE`.
    public static let versuche = 5
    /// Wie viele Stellen — Abschrift von `kopplung.PIN_STELLEN`.
    public static let stellen = 6

    // DIE SAETZE WIE IN `kopplung.py`, nur steht «am Mac», wo dort «an der HomeStation»
    // steht: Der Satz sagt, WO es eine neue Zahl gibt, und unterwegs ist das der Mac.
    public static let grundFalsch = "Die Zahl stimmt nicht."
    public static let grundAbgelaufen = "Die Zahl ist abgelaufen. Am Mac eine neue zeigen lassen."
    public static let grundAufgebraucht =
        "Zu oft daneben. Die Zahl ist tot — am Mac eine neue zeigen lassen."
    public static let grundVerbraucht =
        "Diese Zahl hat schon ein Gerät verbunden. Für ein zweites braucht es eine neue."
    /// Was das Gerät zu hören bekommt — **immer dasselbe, egal woran es lag.** *Wer beim
    /// Raten erfährt, warum er daneben lag, rät beim nächsten Mal besser.*
    public static let satzFuerDasGeraet = "Das hat nicht geklappt. Am Mac eine neue Zahl holen."

    /// Die Zahl mit führenden Nullen. Sie gehört an den Bildschirm des Mac und in **kein
    /// Protokoll**.
    public let zahl: String
    /// Ab wann sie nicht mehr gilt, auf der hineingereichten Uhr.
    public let faellig: TimeInterval
    public private(set) var versucheUebrig: Int
    public private(set) var verbraucht = false

    /// Eine neue Zahl, ab `jetzt` für `frist` Sekunden und `versuche` Versuche.
    ///
    /// `nil` bei einer Frist oder Versuchszahl, die nicht positiv ist — eine Kopplung mit
    /// null Versuchen sähe im Betrieb aus wie eine falsch abgetippte Zahl. `zahl` gibt nur
    /// eine Probe vor; sonst wird gewürfelt.
    public init?(jetzt: TimeInterval, frist: TimeInterval = Vermittlerkopplung.frist,
                 versuche: Int = Vermittlerkopplung.versuche, zahl: String? = nil) {
        guard frist > 0, versuche > 0 else { return nil }
        if let zahl {
            guard zahl.count == Vermittlerkopplung.stellen,
                  zahl.unicodeScalars.allSatisfy({ ("0"..."9").contains($0) }) else { return nil }
            self.zahl = zahl
        } else {
            var zufall = SystemRandomNumberGenerator()
            self.zahl = Vermittlerkopplung.wuerfle(using: &zufall)
        }
        faellig = jetzt + frist
        versucheUebrig = versuche
    }

    /// Eine Zahl, die **niemand sich ausgedacht hat** — gleichverteilt, nichts
    /// ausgeschlossen (kein «000000»-Verbot: das verkleinerte nur den Vorrat).
    /// `SystemRandomNumberGenerator` ist der Zufall des Betriebssystems, nicht ein
    /// fortrechenbarer.
    public static func wuerfle<G: RandomNumberGenerator>(using zufall: inout G) -> String {
        var grenze = 1
        for _ in 0..<stellen { grenze *= 10 }
        let wert = Int.random(in: 0..<grenze, using: &zufall)
        let text = String(wert)
        return String(repeating: "0", count: stellen - text.count) + text
    }

    /// Woran man ist, ohne etwas zu verbrauchen. **Verbraucht vor abgelaufen vor
    /// aufgebraucht** — der Grund, der zuerst eintrat (wie `kopplung.stand`).
    public func stand(jetzt: TimeInterval) -> Kopplungsstand {
        if verbraucht { return .verbraucht }
        if jetzt >= faellig { return .abgelaufen }
        if versucheUebrig <= 0 { return .aufgebraucht }
        return .offen
    }

    /// Einen Versuch prüfen — **und ihn zählen.**
    ///
    /// Leerraum am Rand wird entfernt, mehr nicht. Verglichen wird in gleichbleibender Zeit
    /// (`Vermittlerzugang.gleich`). Ein Versuch an einer Zahl, die nicht mehr offen ist,
    /// zählt nicht und wird mit dem Grund abgelehnt, warum sie es nicht ist.
    public mutating func pruefe(_ eingabe: String?, jetzt: TimeInterval) -> Kopplungsversuch {
        let lage = stand(jetzt: jetzt)
        if lage != .offen {
            let grund: String
            switch lage {
            case .verbraucht: grund = Vermittlerkopplung.grundVerbraucht
            case .abgelaufen: grund = Vermittlerkopplung.grundAbgelaufen
            default: grund = Vermittlerkopplung.grundAufgebraucht
            }
            return Kopplungsversuch(angenommen: false, stand: lage, grund: grund,
                                    satzFuerDasGeraet: Vermittlerkopplung.satzFuerDasGeraet,
                                    versucheUebrig: max(0, versucheUebrig))
        }
        versucheUebrig -= 1
        let gegeben = (eingabe ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard Vermittlerzugang.gleich(Array(gegeben.utf8), Array(zahl.utf8)) else {
            let rest = max(0, versucheUebrig)
            return Kopplungsversuch(
                angenommen: false, stand: stand(jetzt: jetzt),
                grund: rest > 0 ? Vermittlerkopplung.grundFalsch : Vermittlerkopplung.grundAufgebraucht,
                satzFuerDasGeraet: Vermittlerkopplung.satzFuerDasGeraet, versucheUebrig: rest)
        }
        verbraucht = true
        return Kopplungsversuch(angenommen: true, stand: .verbraucht, grund: "",
                                satzFuerDasGeraet: "", versucheUebrig: max(0, versucheUebrig))
    }

    /// Die Zahl von Hand für ungültig erklären.
    public mutating func schliesse() {
        verbraucht = true
    }
}

extension Vermittlerkopplung: CustomStringConvertible {
    /// **Ohne die Zahl** — sie gehört an den Bildschirm, nicht in eine Ausgabe.
    public var description: String {
        "Vermittlerkopplung(faellig: \(faellig), versucheUebrig: \(versucheUebrig), "
            + "verbraucht: \(verbraucht))"
    }
}

/// Die Zugangsdaten, die der Mac dem iPad gibt — **eigene, zufällige, nie die des Heim-PC.**
///
/// Der Benutzername ist der, den auch der Server nennt (der Name der App, klein); die App
/// übernimmt ihn ohnehin aus der Antwort (Protokoll §2). Das Kennwort hat 32 Zeichen wie
/// das des Servers (`KENNWORTLAENGE`) und kommt aus demselben Vorrat wie
/// `secrets.token_urlsafe`: Buchstaben, Ziffern, `-` und `_`.
public struct Vermittlerzugang: Equatable, Sendable, Codable {
    public static let laenge = 32
    static let vorrat = Array("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")

    public let anmeldung: Anmeldung

    public init(anmeldung: Anmeldung) {
        self.anmeldung = anmeldung
    }

    /// Der Benutzername — aus der Marke, damit er beim Umbenennen mitgeht.
    public static var benutzer: String { Marke.name.lowercased() }

    /// Neue Zugangsdaten. `SystemRandomNumberGenerator` ist der Zufall des Betriebssystems.
    public static func erzeuge() -> Vermittlerzugang {
        var zufall = SystemRandomNumberGenerator()
        return erzeuge(using: &zufall)
    }

    public static func erzeuge<G: RandomNumberGenerator>(using zufall: inout G) -> Vermittlerzugang {
        let wort = String((0..<laenge).map { _ in vorrat[Int.random(in: 0..<vorrat.count, using: &zufall)] })
        return Vermittlerzugang(anmeldung: Anmeldung(benutzer: benutzer, kennwort: wort))
    }

    /// Lässt diese `Authorization`-Zeile herein? **Beide Vergleiche laufen immer**, in
    /// gleichbleibender Zeit — ein Vergleich, dessen Dauer vom Inhalt abhängt, verrät den
    /// Inhalt (wie `pruefe_anmeldung` im Server).
    public func laesstHerein(_ kopfzeile: String?) -> Bool {
        guard let kopfzeile, kopfzeile.hasPrefix("Basic "),
              let roh = Data(base64Encoded: String(kopfzeile.dropFirst(6))),
              let text = String(data: roh, encoding: .utf8) else { return false }
        let name: Substring
        let gegeben: Substring
        if let doppelpunkt = text.firstIndex(of: ":") {
            name = text[..<doppelpunkt]
            gegeben = text[text.index(after: doppelpunkt)...]
        } else {
            name = Substring(text)
            gegeben = ""
        }
        let stimmtName = Vermittlerzugang.gleich(Array(name.utf8), Array(anmeldung.benutzer.utf8))
        let stimmtWort = Vermittlerzugang.gleich(Array(gegeben.utf8), Array(anmeldung.kennwort.utf8))
        return stimmtName && stimmtWort
    }

    /// Vergleich in gleichbleibender Zeit: Er läuft über die ganze Länge, auch wenn die
    /// erste Stelle schon falsch ist. Die **Länge** verrät er (wie `hmac.compare_digest`).
    public static func gleich(_ a: [UInt8], _ b: [UInt8]) -> Bool {
        guard a.count == b.count else { return false }
        var unterschied: UInt8 = 0
        for i in 0..<a.count { unterschied |= a[i] ^ b[i] }
        return unterschied == 0
    }
}
