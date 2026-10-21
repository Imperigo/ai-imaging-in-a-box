import Foundation

// DAS ZERTIFIKAT DES MAC FUER DIE LEITUNG ZUM IPAD (Owner-Entscheid 118, 21.10.2026).
//
// Bis 0.3.x ging die Leitung iPad–Mac unverschluesselt (Entscheid 01.10.2026: darum war die
// Vermittlung von Haus aus aus). Seit Entscheid 118 arbeitet das iPad IMMER ueber den Mac — also
// muss die Leitung verschluesselt sein, bevor ein Byte der Mappe darueber geht. Der Mac haelt dazu
// ein eigenes Zertifikat im Schluesselbund; das iPad heftet seinen Fingerabdruck beim Koppeln an
// (`Koppelschein.abdruck`) und nimmt danach kein anderes an.
//
// Apple hat keine Schnittstelle, die ein Zertifikat AUSSTELLT — nur eine, die eines liest
// (`SecCertificateCreateWithData`). Eine fremde Bibliothek dafuer verbietet Regel 1 nicht, aber
// der Auftrag («nur Apple-Frameworks») und die Mac-Manifest-Probe. Darum steht der Bau hier,
// klein und unter Linux geprueft: ein X.509-Zertifikat der Fassung 3, selbst unterschrieben,
// Schluessel P-256, Unterschrift ECDSA mit SHA-256. Die UNTERSCHRIFT selbst macht der Mac
// (`SecKeyCreateSignature`, Security) — der Kern baut nur die Bytes davor und danach.
//
// Geprueft am 21.10.2026 mit `openssl x509 -text` und `openssl verify` gegen ein Zertifikat
// aus genau diesen Bytes (Protokoll 74, Strang iPad); die Probe `MaczertifikatTests` friert das
// Ergebnis ein.

/// Die Bausteine von DER (ITU-T X.690) — **nur, was ein Zertifikat braucht.**
public enum Der {
    /// Die Länge in DER-Form: bis 127 in einem Byte, sonst `0x80 | n` und n Bytes.
    public static func laenge(_ n: Int) -> [UInt8] {
        precondition(n >= 0)
        if n < 0x80 { return [UInt8(n)] }
        var bytes: [UInt8] = []
        var rest = n
        while rest > 0 {
            bytes.insert(UInt8(rest & 0xff), at: 0)
            rest >>= 8
        }
        return [0x80 | UInt8(bytes.count)] + bytes
    }

    /// Ein Teil: Kennung, Länge, Inhalt.
    public static func teil(_ kennung: UInt8, _ inhalt: [UInt8]) -> [UInt8] {
        [kennung] + laenge(inhalt.count) + inhalt
    }

    /// `SEQUENCE`.
    public static func folge(_ teile: [[UInt8]]) -> [UInt8] { teil(0x30, teile.flatMap { $0 }) }
    /// `SET`.
    public static func menge(_ teile: [[UInt8]]) -> [UInt8] { teil(0x31, teile.flatMap { $0 }) }

    /// `INTEGER` aus Bytes (gross zuerst) — **positiv**: führende Nullen weg, eine Null davor,
    /// wenn das oberste Bit gesetzt ist.
    public static func ganz(_ bytes: [UInt8]) -> [UInt8] {
        var b = Array(bytes.drop(while: { $0 == 0 }))
        if b.isEmpty { b = [0] }
        if b[0] & 0x80 != 0 { b.insert(0, at: 0) }
        return teil(0x02, b)
    }

    public static func ganz(_ wert: Int) -> [UInt8] {
        precondition(wert >= 0)
        var bytes: [UInt8] = []
        var rest = wert
        repeat {
            bytes.insert(UInt8(rest & 0xff), at: 0)
            rest >>= 8
        } while rest > 0
        return ganz(bytes)
    }

    /// `OBJECT IDENTIFIER` aus seinen Gliedern.
    public static func kennzeichen(_ glieder: [UInt64]) -> [UInt8] {
        precondition(glieder.count >= 2)
        var aus: [UInt8] = [UInt8(glieder[0] * 40 + glieder[1])]
        for g in glieder.dropFirst(2) {
            var stuecke: [UInt8] = [UInt8(g & 0x7f)]
            var rest = g >> 7
            while rest > 0 {
                stuecke.insert(UInt8(rest & 0x7f) | 0x80, at: 0)
                rest >>= 7
            }
            aus += stuecke
        }
        return teil(0x06, aus)
    }

    /// `UTF8String`.
    public static func text(_ s: String) -> [UInt8] { teil(0x0c, Array(s.utf8)) }
    /// `BIT STRING` ohne ungenutzte Bits.
    public static func bits(_ bytes: [UInt8]) -> [UInt8] { teil(0x03, [0] + bytes) }
    /// `OCTET STRING`.
    public static func oktette(_ bytes: [UInt8]) -> [UInt8] { teil(0x04, bytes) }
    /// `BOOLEAN`.
    public static func wahr(_ w: Bool) -> [UInt8] { teil(0x01, [w ? 0xff : 0x00]) }
    /// Ein ausdrücklich markierter Teil `[n]` (konstruiert).
    public static func markiert(_ n: UInt8, _ inhalt: [UInt8]) -> [UInt8] { teil(0xa0 | n, inhalt) }

    /// Eine Zeit: `UTCTime` bis 2049, danach `GeneralizedTime` (RFC 5280 §4.1.2.5), immer UTC
    /// und auf die Sekunde.
    public static func zeit(_ datum: Date) -> [UInt8] {
        var kalender = Calendar(identifier: .gregorian)
        kalender.timeZone = TimeZone(identifier: "UTC") ?? kalender.timeZone
        let t = kalender.dateComponents([.year, .month, .day, .hour, .minute, .second], from: datum)
        let jahr = t.year ?? 1970
        func zwei(_ v: Int?) -> String { String(format: "%02d", v ?? 0) }
        let rest = zwei(t.month) + zwei(t.day) + zwei(t.hour) + zwei(t.minute) + zwei(t.second) + "Z"
        if jahr < 2050 {
            return teil(0x17, Array((zwei(jahr % 100) + rest).utf8))
        }
        return teil(0x18, Array((String(format: "%04d", jahr) + rest).utf8))
    }
}

/// Ein selbst unterschriebenes Zertifikat für den Mac — **gebaut, nicht unterschrieben.**
///
/// Ablauf am Mac (`Start/Macidentitaet.swift`): Schlüssel erzeugen (P-256, im Schlüsselbund) →
/// `tbs(…)` → die Bytes mit dem Schlüssel unterschreiben (ECDSA/SHA-256, DER) →
/// `zertifikat(tbs:unterschrift:)` → in den Schlüsselbund. Der Fingerabdruck (SHA-256 über die
/// Bytes von `zertifikat`) ist, was das iPad anheftet.
public enum Maczertifikat {
    /// Wie lange es gilt — **825 Tage**, die Grenze, die Apple für Server-Zertifikate setzt
    /// (gilt für vom System geprüfte; das iPad prüft hier selbst, aber ein Zertifikat, das
    /// die Regel einhält, fällt nirgends auf). Danach stellt der Mac ein neues aus, und das iPad
    /// koppelt einmal neu.
    public static let gueltigTage = 825
    /// Wie viele Tage vor dem Ablauf ein neues ausgestellt wird.
    public static let erneuernTage = 30
    /// So lange zurück gilt es schon — eine Uhr des iPad, die etwas nachgeht, soll nicht
    /// «noch nicht gültig» lesen (es prüft die Zeit zwar nicht, aber andere Leser tun es).
    public static let rueckdatiert: TimeInterval = 3600

    // Die Kennzeichen (RFC 5480, RFC 5758, RFC 5280).
    static let ecdsaMitSha256: [UInt64] = [1, 2, 840, 10045, 4, 3, 2]
    static let ecSchluessel: [UInt64] = [1, 2, 840, 10045, 2, 1]
    static let p256: [UInt64] = [1, 2, 840, 10045, 3, 1, 7]
    static let gemeinsamerName: [UInt64] = [2, 5, 4, 3]
    static let grundbedingungen: [UInt64] = [2, 5, 29, 19]
    static let schluesselzweck: [UInt64] = [2, 5, 29, 15]
    static let erweiterterZweck: [UInt64] = [2, 5, 29, 37]
    static let serverZweck: [UInt64] = [1, 3, 6, 1, 5, 5, 7, 3, 1]

    public enum Fehler: Error, Equatable {
        /// Der öffentliche Schlüssel ist nicht in der Form `04 ‖ X ‖ Y` (65 Bytes).
        case schluesselform
        /// Die Seriennummer ist leer oder länger als 20 Bytes (RFC 5280 §4.1.2.2).
        case seriennummer
        /// Der Name ist leer.
        case name
    }

    /// Der Name im Zertifikat: «<Marke> Mac» und ein zufälliger Zusatz — **kein Gerätename**
    /// (Regel 3: er verriete, wessen Mac es ist).
    public static func name(zusatz: String) -> String {
        Marke.name + " Mac " + zusatz
    }

    /// Der zu unterschreibende Teil (`TBSCertificate`).
    ///
    /// - Parameters:
    ///   - schluessel: der öffentliche Schlüssel, unkomprimiert (`04 ‖ X ‖ Y`, 65 Bytes) — so,
    ///     wie `SecKeyCopyExternalRepresentation` ihn gibt.
    ///   - seriennummer: 1 bis 20 zufällige Bytes.
    public static func tbs(schluessel: [UInt8], name: String, seriennummer: [UInt8],
                           von: Date, bis: Date) throws -> [UInt8] {
        guard schluessel.count == 65, schluessel[0] == 0x04 else { throw Fehler.schluesselform }
        guard !seriennummer.isEmpty, seriennummer.count <= 20 else { throw Fehler.seriennummer }
        guard !name.isEmpty else { throw Fehler.name }
        let wer = Der.folge([Der.menge([Der.folge([Der.kennzeichen(gemeinsamerName), Der.text(name)])])])
        // DIE SERIENNUMMER POSITIV: das oberste Bit geloescht, damit `Der.ganz` keine Null
        // davorsetzen muss und die Laenge bei 20 Bytes bleibt.
        var serie = seriennummer
        serie[0] &= 0x7f
        if serie.allSatisfy({ $0 == 0 }) { serie[serie.count - 1] = 1 }
        let erweiterungen = Der.folge([
            // KEINE STELLE, DIE ANDERE ZERTIFIKATE AUSSTELLT — und das als «kritisch».
            Der.folge([Der.kennzeichen(grundbedingungen), Der.wahr(true), Der.oktette(Der.folge([]))]),
            // NUR UNTERSCHREIBEN (digitalSignature), kritisch.
            Der.folge([Der.kennzeichen(schluesselzweck), Der.wahr(true),
                       Der.oktette(Der.teil(0x03, [0x07, 0x80]))]),
            // NUR ALS SERVER.
            Der.folge([Der.kennzeichen(erweiterterZweck),
                       Der.oktette(Der.folge([Der.kennzeichen(serverZweck)]))]),
        ])
        return Der.folge([
            Der.markiert(0, Der.ganz(2)),
            Der.ganz(serie),
            Der.folge([Der.kennzeichen(ecdsaMitSha256)]),
            wer,
            Der.folge([Der.zeit(von), Der.zeit(bis)]),
            wer,
            Der.folge([Der.folge([Der.kennzeichen(ecSchluessel), Der.kennzeichen(p256)]),
                       Der.bits(schluessel)]),
            Der.markiert(3, erweiterungen),
        ])
    }

    /// Das ganze Zertifikat aus dem unterschriebenen Teil und der Unterschrift (ECDSA, DER —
    /// so, wie `SecKeyCreateSignature` mit `.ecdsaSignatureMessageX962SHA256` sie gibt).
    public static func zertifikat(tbs: [UInt8], unterschrift: [UInt8]) -> [UInt8] {
        Der.folge([tbs, Der.folge([Der.kennzeichen(ecdsaMitSha256)]), Der.bits(unterschrift)])
    }

    /// Von wann bis wann ein neues gilt, ab `jetzt`.
    public static func frist(jetzt: Date) -> (von: Date, bis: Date) {
        (jetzt.addingTimeInterval(-rueckdatiert),
         jetzt.addingTimeInterval(TimeInterval(gueltigTage) * 86_400))
    }

    /// Ob ein Zertifikat, das bis `bis` gilt, **jetzt** ersetzt werden soll.
    public static func erneuern(bis: Date?, jetzt: Date) -> Bool {
        guard let bis else { return true }
        return bis.timeIntervalSince(jetzt) < TimeInterval(erneuernTage) * 86_400
    }
}
