import CryptoKit
import Foundation
import Security
import VisboxKern

/// Das Zertifikat des Mac für die Leitung zum iPad (Owner-Entscheid 118, 21.10.2026) — **im
/// Schlüsselbund des Mac, und nur dort.**
///
/// Seit 118 arbeitet das iPad immer über den Mac; die Leitung dazwischen ist darum
/// verschlüsselt (`Vermittlungsdienst`, TLS mit dieser Identität). Das iPad heftet beim Koppeln
/// den Fingerabdruck an (`abdruck`) und nimmt danach kein anderes Zertifikat an.
///
/// * **Der Schlüssel** (P-256) entsteht im Schlüsselbund (`SecKeyCreateRandomKey`, dauerhaft)
///   und verlässt ihn nie — auch nicht beim Unterschreiben.
/// * **Das Zertifikat** baut der Kern (`Maczertifikat`, mit Proben unter Linux und einmal mit
///   `openssl` geprüft); unterschrieben wird hier (`SecKeyCreateSignature`, ECDSA/SHA-256).
///   Apple hat keine Schnittstelle, die ein Zertifikat ausstellt.
/// * **Die Identität** (Zertifikat und Schlüssel zusammen) findet das System über den
///   öffentlichen Schlüssel (`SecIdentityCreateWithCertificate`).
/// * **Erneuert** wird 30 Tage vor dem Ablauf (825 Tage, `Maczertifikat.erneuern`) — danach
///   koppelt das iPad einmal neu. Bis wann es gilt, steht in den Einstellungen der App (kein
///   Geheimnis).
///
/// Der Schlüsselbund des Anmeldens, wie bei `Heimschluesselbund`: Nach jedem neuen Herunterladen
/// fragt macOS einmal, ob die App an den Schlüssel darf («Immer erlauben»).
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026)* — hier nicht übersetzt (Linux kennt `Security`
/// nicht in dieser Form).
enum Macidentitaet {

    struct Geladen {
        let identitaet: SecIdentity
        /// SHA-256 über die Bytes des Zertifikats, 64 Hex-Stellen.
        let abdruck: String
    }

    enum Ergebnis {
        case gut(Geladen)
        case fehler(String)
    }

    /// Unter welchem Namen Zertifikat und Schlüssel im Schlüsselbund stehen — aus der Marke.
    private static var etikett: String { Marke.name + " · iPad-Leitung" }
    private static var kennzeichen: Data { Data((Marke.kennung + ".ipad-leitung").utf8) }
    /// Bis wann das Zertifikat gilt (Sekunden seit 1970) — **kein Geheimnis**.
    private static let bisEintrag = "vermittlung.zertifikatBis"

    private static var bis: Date? {
        get {
            let wert = UserDefaults.standard.double(forKey: bisEintrag)
            return wert > 0 ? Date(timeIntervalSince1970: wert) : nil
        }
        set {
            if let newValue {
                UserDefaults.standard.set(newValue.timeIntervalSince1970, forKey: bisEintrag)
            } else {
                UserDefaults.standard.removeObject(forKey: bisEintrag)
            }
        }
    }

    /// Das Zertifikat aus dem Schlüsselbund — oder ein neues, wenn keines da ist oder es bald
    /// abläuft.
    static func liesOderErzeuge(jetzt: Date = Date()) -> Ergebnis {
        if let geladen = lies(), !Maczertifikat.erneuern(bis: bis, jetzt: jetzt) {
            return .gut(geladen)
        }
        loesche()
        return erzeuge(jetzt: jetzt)
    }

    /// Der Fingerabdruck eines Zertifikats — dieselbe Rechnung wie am iPad und am Heim-PC.
    static func abdruck(_ zertifikat: SecCertificate) -> String {
        let der = SecCertificateCopyData(zertifikat) as Data
        return Fingerabdruck.hex(Array(SHA256.hash(data: der)))
    }

    // ------------------------------------------------------------------- intern

    private static func lies() -> Geladen? {
        let frage: [String: Any] = [
            kSecClass as String: kSecClassCertificate,
            kSecAttrLabel as String: etikett,
            kSecReturnRef as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var ergebnis: CFTypeRef?
        guard SecItemCopyMatching(frage as CFDictionary, &ergebnis) == errSecSuccess,
              let roh = ergebnis, CFGetTypeID(roh) == SecCertificateGetTypeID() else { return nil }
        let zertifikat = roh as! SecCertificate
        var identitaet: SecIdentity?
        guard SecIdentityCreateWithCertificate(nil, zertifikat, &identitaet) == errSecSuccess,
              let identitaet else { return nil }
        return Geladen(identitaet: identitaet, abdruck: abdruck(zertifikat))
    }

    private static func loesche() {
        SecItemDelete([kSecClass as String: kSecClassCertificate,
                       kSecAttrLabel as String: etikett] as CFDictionary)
        SecItemDelete([kSecClass as String: kSecClassKey,
                       kSecAttrApplicationTag as String: kennzeichen] as CFDictionary)
        bis = nil
    }

    private static func erzeuge(jetzt: Date) -> Ergebnis {
        let schluesselart: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeECSECPrimeRandom,
            kSecAttrKeySizeInBits as String: 256,
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: kennzeichen,
                kSecAttrLabel as String: etikett,
            ] as [String: Any],
        ]
        var fehler: Unmanaged<CFError>?
        guard let privat = SecKeyCreateRandomKey(schluesselart as CFDictionary, &fehler),
              let oeffentlich = SecKeyCopyPublicKey(privat),
              let roh = SecKeyCopyExternalRepresentation(oeffentlich, &fehler) as Data? else {
            return .fehler(satz("Der Schlüssel liess sich nicht anlegen", fehler))
        }
        var zufall = [UInt8](repeating: 0, count: 16)
        guard SecRandomCopyBytes(kSecRandomDefault, zufall.count, &zufall) == errSecSuccess else {
            return .fehler("Der Zufall des Systems antwortete nicht — kein Zertifikat.")
        }
        let (von, frist) = Maczertifikat.frist(jetzt: jetzt)
        let teil: [UInt8]
        do {
            teil = try Maczertifikat.tbs(schluessel: [UInt8](roh),
                                         name: Maczertifikat.name(zusatz: Fingerabdruck.hex(Array(zufall.prefix(3)))),
                                         seriennummer: zufall, von: von, bis: frist)
        } catch {
            return .fehler("Das Zertifikat liess sich nicht bauen (\(error)).")
        }
        guard let unterschrift = SecKeyCreateSignature(privat, .ecdsaSignatureMessageX962SHA256,
                                                       Data(teil) as CFData, &fehler) as Data? else {
            return .fehler(satz("Das Zertifikat liess sich nicht unterschreiben", fehler))
        }
        let der = Maczertifikat.zertifikat(tbs: teil, unterschrift: [UInt8](unterschrift))
        guard let zertifikat = SecCertificateCreateWithData(nil, Data(der) as CFData) else {
            return .fehler("Das System nahm das Zertifikat nicht an.")
        }
        let stand = SecItemAdd([kSecClass as String: kSecClassCertificate,
                                kSecValueRef as String: zertifikat,
                                kSecAttrLabel as String: etikett] as CFDictionary, nil)
        guard stand == errSecSuccess else {
            return .fehler("Das Zertifikat liess sich nicht im Schlüsselbund ablegen (Code \(stand)).")
        }
        var identitaet: SecIdentity?
        guard SecIdentityCreateWithCertificate(nil, zertifikat, &identitaet) == errSecSuccess,
              let identitaet else {
            return .fehler("Zertifikat und Schlüssel finden sich im Schlüsselbund nicht zusammen.")
        }
        bis = frist
        return .gut(Geladen(identitaet: identitaet, abdruck: abdruck(zertifikat)))
    }

    private static func satz(_ anfang: String, _ fehler: Unmanaged<CFError>?) -> String {
        guard let f = fehler?.takeRetainedValue() else { return anfang + "." }
        let text: String = CFErrorCopyDescription(f).map { $0 as String } ?? "ohne Angabe"
        return anfang + " (" + text + ")."
    }
}
