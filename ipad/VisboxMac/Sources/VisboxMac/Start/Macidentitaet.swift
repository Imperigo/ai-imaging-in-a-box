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
/// **Nie still ein neues (Befund Demolauf 0.3.54, 24.10.2026).** Bis dahin legte `lies()` → `nil`
/// still ein neues Zertifikat an — nach jedem Update, weil die neu (ad hoc) unterschriebene App
/// das alte nicht mehr las. Jedes iPad war danach getrennt («anderes Zertifikat»), und im
/// Schlüsselbund sammelten sich die Einträge «Visbox Mac …» (das Löschen über das Etikett traf
/// sie nicht). Seither:
///
/// * **gefunden über den Fingerabdruck**, den der Mac sich merkt (kein Geheimnis — er steht auf
///   jedem Koppelschein), nicht über das Etikett; gesucht wird unter allen Zertifikaten, deren
///   Name mit «<Marke> Mac » beginnt;
/// * **lesbar heisst: der Schlüssel unterschreibt** (eine Probe-Unterschrift beim Start). Fragt
///   macOS dabei nach dem Kennwort und man erlaubt, bleibt das Zertifikat — und die iPads
///   gekoppelt;
/// * **was dann geschieht, sagt der Kern** (`Macidentitaetsregel`): nach einem Verlust **einmal**
///   ein neues, mit dem Satz «iPads neu koppeln» in der Zeile «iPad»; in derselben Fassung kein
///   zweites;
/// * **gelöscht wird nur, was die App lesen kann** (beim Erneuern der Frist) — gezielt dieses
///   Zertifikat und sein Schlüssel. Fremd gewordene alte Einträge löscht man von Hand in der
///   Schlüsselbundverwaltung (`docs/MAC_UNTERSCHRIFT_EINRICHTEN.md`); ein Löschversuch der App
///   fragte je Eintrag nach dem Kennwort.
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026; Fingerabdruck und Regel 24.10.2026)* — hier nicht
/// übersetzt (Linux kennt `Security` nicht in dieser Form).
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
    /// Der Fingerabdruck des Zertifikats, mit dem der Mac zuletzt antwortete — **kein Geheimnis**
    /// (er steht auf jedem Koppelschein). Daran findet er es wieder, nicht am Etikett.
    private static let abdruckEintrag = "vermittlung.zertifikatAbdruck"
    /// In welcher Fassung der App zuletzt nach einem Verlust ersetzt wurde — für «nur einmal».
    private static let ersetztEintrag = "vermittlung.zertifikatErsetztIn"
    /// Ob die iPads nach einem Verlust neu koppeln müssen — bis eines es getan hat.
    private static let neuKoppelnEintrag = "vermittlung.ipadsNeuKoppeln"

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

    /// Die laufende Fassung (Versionsnummer und Baunummer) — jedes Update ist eine neue.
    private static var fassung: String {
        let info = Bundle.main.infoDictionary ?? [:]
        let nummer = info["CFBundleShortVersionString"] as? String ?? "?"
        let bau = info["CFBundleVersion"] as? String ?? "?"
        return nummer + " (" + bau + ")"
    }

    /// Ob nach einem Verlust noch kein iPad neu gekoppelt hat — dann sagt es die Zeile «iPad».
    static var ipadsMuessenNeuKoppeln: Bool {
        UserDefaults.standard.bool(forKey: neuKoppelnEintrag)
    }

    /// Ein iPad hat gekoppelt: Der Hinweis «neu koppeln» ist erledigt.
    static func ipadNeuGekoppelt() {
        UserDefaults.standard.removeObject(forKey: neuKoppelnEintrag)
    }

    /// Das Zertifikat aus dem Schlüsselbund — oder ein neues, **nach der Regel des Kerns**
    /// (`Macidentitaetsregel`): nie still, wenn es schon eines gab, und nach einem Verlust nur
    /// einmal je Fassung.
    static func liesOderErzeuge(jetzt: Date = Date()) -> Ergebnis {
        let gemerkt = UserDefaults.standard.string(forKey: abdruckEintrag)
        let (fund, geladen) = suche(gemerkt: gemerkt)
        let schritt = Macidentitaetsregel.schritt(
            fund: fund, fristLaeuftAb: Maczertifikat.erneuern(bis: bis, jetzt: jetzt),
            gemerkt: gemerkt != nil,
            ersetztIn: UserDefaults.standard.string(forKey: ersetztEintrag), fassung: fassung)
        switch schritt {
        case .behalten:
            guard let geladen else { return .fehler(Macidentitaetsregel.satzAngehalten) }
            // UEBERNAHME aus der Zeit vor dem Fingerabdruck: ab jetzt daran wiederfinden.
            UserDefaults.standard.set(geladen.abdruck, forKey: abdruckEintrag)
            return .gut(geladen)
        case .erneuern:
            if let geladen { loesche(geladen) }
            return erzeuge(jetzt: jetzt)
        case .erstesMal:
            return erzeuge(jetzt: jetzt)
        case .ersetzenNachVerlust:
            // NICHT STILL: einmal ein neues, und die Zeile «iPad» sagt, dass jedes iPad neu
            // koppeln muss. Das alte bleibt liegen — die App darf es nicht mehr anfassen.
            let ergebnis = erzeuge(jetzt: jetzt)
            if case .gut = ergebnis {
                UserDefaults.standard.set(fassung, forKey: ersetztEintrag)
                // DER SATZ NUR, WENN ES WAS ZU KOPPELN GAB: War nie ein iPad ueber den Mac
                // gekoppelt, verliert auch keines etwas.
                if Vermittlergedaechtnis.gekoppelt {
                    UserDefaults.standard.set(true, forKey: neuKoppelnEintrag)
                }
                Vermittlergedaechtnis.gekoppelt = false
            }
            return ergebnis
        case .anhalten:
            return .fehler(Macidentitaetsregel.satzAngehalten)
        }
    }

    /// Der Fingerabdruck eines Zertifikats — dieselbe Rechnung wie am iPad und am Heim-PC.
    static func abdruck(_ zertifikat: SecCertificate) -> String {
        let der = SecCertificateCopyData(zertifikat) as Data
        return Fingerabdruck.hex(Array(SHA256.hash(data: der)))
    }

    // ------------------------------------------------------------------- intern

    /// Was im Schlüsselbund steht: das gemerkte Zertifikat, lesbar — oder warum nicht.
    private static func suche(gemerkt: String?) -> (Macidentitaetsregel.Fund, Geladen?) {
        let (stand, eigene) = eigeneZertifikate()
        // VERWEIGERT ODER UNBEKANNT (nicht «nichts gefunden»): als nicht lesbar zaehlen — lieber
        // einmal neu koppeln als still ein neues anlegen.
        guard stand == errSecSuccess || stand == errSecItemNotFound else { return (.nichtLesbar, nil) }
        guard !eigene.isEmpty else { return (.keines, nil) }
        let kandidat: SecCertificate?
        if let gemerkt {
            kandidat = eigene.first { abdruck($0) == gemerkt }
        } else {
            // DER ERSTE START MIT DIESER REGEL: noch kein Fingerabdruck gemerkt — der alte Weg
            // ueber das Etikett. Nicht alle Kandidaten durchprobieren: Jeder fremd gewordene
            // Schluessel fragte nach dem Kennwort.
            kandidat = nachEtikett()
        }
        guard let kandidat, let geladen = pruefe(kandidat) else { return (.nichtLesbar, nil) }
        return (.lesbar, geladen)
    }

    /// Alle Zertifikate, deren Name mit «<Marke> Mac » beginnt (`Maczertifikat.name`).
    private static func eigeneZertifikate() -> (OSStatus, [SecCertificate]) {
        let frage: [String: Any] = [
            kSecClass as String: kSecClassCertificate,
            kSecReturnRef as String: true,
            kSecMatchLimit as String: kSecMatchLimitAll,
        ]
        var ergebnis: CFTypeRef?
        let stand = SecItemCopyMatching(frage as CFDictionary, &ergebnis)
        guard stand == errSecSuccess, let roh = ergebnis as? [AnyObject] else { return (stand, []) }
        let anfang = Maczertifikat.name(zusatz: "")
        let liste: [SecCertificate] = roh.compactMap { (eintrag: AnyObject) -> SecCertificate? in
            guard CFGetTypeID(eintrag) == SecCertificateGetTypeID() else { return nil }
            let zertifikat = eintrag as! SecCertificate
            let name = SecCertificateCopySubjectSummary(zertifikat) as String? ?? ""
            return name.hasPrefix(anfang) ? zertifikat : nil
        }
        return (stand, liste)
    }

    /// Der Weg vor dem 24.10.2026: über das Etikett.
    private static func nachEtikett() -> SecCertificate? {
        let frage: [String: Any] = [
            kSecClass as String: kSecClassCertificate,
            kSecAttrLabel as String: etikett,
            kSecReturnRef as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var ergebnis: CFTypeRef?
        guard SecItemCopyMatching(frage as CFDictionary, &ergebnis) == errSecSuccess,
              let roh = ergebnis, CFGetTypeID(roh) == SecCertificateGetTypeID() else { return nil }
        return (roh as! SecCertificate)
    }

    /// **Lesbar heisst: der Schlüssel unterschreibt.** Dass Zertifikat und Schlüssel sich finden,
    /// reicht nicht — den Schlüssel benutzen darf nach einem Update nur, wem der Schlüsselbund es
    /// erlaubt. Fragt macOS hier nach dem Kennwort und man erlaubt, bleibt alles, wie es war.
    private static func pruefe(_ zertifikat: SecCertificate) -> Geladen? {
        var identitaet: SecIdentity?
        guard SecIdentityCreateWithCertificate(nil, zertifikat, &identitaet) == errSecSuccess,
              let identitaet else { return nil }
        var schluessel: SecKey?
        guard SecIdentityCopyPrivateKey(identitaet, &schluessel) == errSecSuccess,
              let schluessel else { return nil }
        var fehler: Unmanaged<CFError>?
        let probe = Data((Marke.kennung + ".probe").utf8) as CFData
        guard SecKeyCreateSignature(schluessel, .ecdsaSignatureMessageX962SHA256, probe,
                                    &fehler) != nil else {
            _ = fehler?.takeRetainedValue()
            return nil
        }
        return Geladen(identitaet: identitaet, abdruck: abdruck(zertifikat))
    }

    /// Löscht **genau dieses** Zertifikat und seinen Schlüssel — nur, was die App lesen konnte.
    private static func loesche(_ geladen: Geladen) {
        var zertifikat: SecCertificate?
        var schluessel: SecKey?
        _ = SecIdentityCopyCertificate(geladen.identitaet, &zertifikat)
        _ = SecIdentityCopyPrivateKey(geladen.identitaet, &schluessel)
        if let zertifikat {
            SecItemDelete([kSecClass as String: kSecClassCertificate,
                           kSecValueRef as String: zertifikat] as CFDictionary)
        }
        if let schluessel {
            SecItemDelete([kSecClass as String: kSecClassKey,
                           kSecValueRef as String: schluessel] as CFDictionary)
        }
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
        let neu = abdruck(zertifikat)
        UserDefaults.standard.set(neu, forKey: abdruckEintrag)
        return .gut(Geladen(identitaet: identitaet, abdruck: neu))
    }

    private static func satz(_ anfang: String, _ fehler: Unmanaged<CFError>?) -> String {
        guard let f = fehler?.takeRetainedValue() else { return anfang + "." }
        let text: String = CFErrorCopyDescription(f).map { $0 as String } ?? "ohne Angabe"
        return anfang + " (" + text + ")."
    }
}
