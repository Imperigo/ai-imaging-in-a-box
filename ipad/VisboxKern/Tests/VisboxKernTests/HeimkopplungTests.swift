import Foundation
import XCTest
import VisboxKern

/// Der Mac koppelt sich selbst (Owner-Entscheid 83, Blatt 17): Tailscale-Geräte lesen,
/// Kandidaten filtern, Antworten deuten, Fehlversuche zählen, Anheften prüfen.
///
/// **Die Namen sind erfunden** (Regel 3): `beispiel.ts.net` gehört niemandem in diesem
/// Projekt, die Adressen stammen aus den Dokumentationsbereichen (RFC 5737, RFC 3849).
final class HeimkopplungTests: XCTestCase {

    // ------------------------------------------------------------ tailscale status

    /// Die Form von `tailscale status --json`, gekürzt auf die Felder, die gelesen werden.
    private let status = Data("""
    {
      "Version": "1.76.0",
      "Self": {"HostName": "mein-mac", "DNSName": "mein-mac.beispiel.ts.net.",
               "OS": "macOS", "Online": true},
      "Peer": {
        "nodekey:aa": {"HostName": "heim-pc", "DNSName": "heim-pc.beispiel.ts.net.",
                       "OS": "linux", "Online": true},
        "nodekey:bb": {"HostName": "altes-notebook", "DNSName": "altes-notebook.beispiel.ts.net.",
                       "OS": "windows", "Online": false},
        "nodekey:cc": {"HostName": "telefon", "DNSName": "telefon.beispiel.ts.net.",
                       "OS": "iOS", "Online": true},
        "nodekey:dd": {"HostName": "ohne-namen", "DNSName": "", "OS": "linux", "Online": true}
      }
    }
    """.utf8)

    func testDieGeraeteKommenAusPeerNichtAusSelf() throws {
        let geraete = try XCTUnwrap(Tailscalestatus.geraete(aus: status))
        XCTAssertEqual(geraete.count, 4)
        XCTAssertFalse(geraete.contains { $0.name == "mein-mac" })
        let heim = try XCTUnwrap(geraete.first { $0.name == "heim-pc" })
        XCTAssertEqual(heim.dnsName, "heim-pc.beispiel.ts.net", "ohne den Punkt am Ende")
        XCTAssertTrue(heim.online)
    }

    func testKandidatenSindOnlineMitNamenUndKeinTelefon() throws {
        let geraete = try XCTUnwrap(Tailscalestatus.geraete(aus: status))
        let kandidaten = Tailscalestatus.kandidaten(geraete)
        XCTAssertEqual(kandidaten.map(\.adresse.absoluteString),
                       ["https://heim-pc.beispiel.ts.net:8443"])
        XCTAssertEqual(kandidaten.first?.weg, .tailscale)
        XCTAssertEqual(kandidaten.first?.waehlbar, false, "erst nach hallo wählbar")
    }

    func testUnlesbareAusgabeIstNichtKeinGeraet() {
        XCTAssertNil(Tailscalestatus.geraete(aus: Data("Tailscale is stopped.".utf8)))
        XCTAssertEqual(Tailscalestatus.geraete(aus: Data(#"{"Peer": null}"#.utf8)), [])
    }

    func testDieProgrammeStehenInDerReihenfolgeDerDoku() {
        XCTAssertEqual(Heimkopplung.tailscaleProgramme.first,
                       "/Applications/Tailscale.app/Contents/MacOS/Tailscale")
        XCTAssertTrue(Heimkopplung.tailscaleProgramme.contains("/usr/local/bin/tailscale"))
    }

    // ------------------------------------------------------------ hallo

    private let hallo = Data(#"{"\#(Marke.name.lowercased())": true, "fassung": "0.2.0", "name": "Heim-PC"}"#.utf8)

    func testNurEinVisboxHalloMachtWaehlbar() throws {
        let k = try XCTUnwrap(Tailscalestatus.kandidaten(
            [Tailscalegeraet(name: "heim-pc", dnsName: "heim-pc.beispiel.ts.net",
                             online: true, system: "linux")]).first)
        XCTAssertTrue(k.nach(halloStatus: 200, daten: hallo, fingerabdruck: nil).waehlbar)
        XCTAssertFalse(k.nach(halloStatus: 404, daten: Data(), fingerabdruck: nil).waehlbar)
        XCTAssertFalse(k.nach(halloStatus: 200, daten: Data(#"{"ok": true}"#.utf8),
                              fingerabdruck: nil).waehlbar)
        let stumm = k.nach(halloStatus: nil, daten: Data(), fingerabdruck: nil,
                           grund: "Tailscale am Mac an?")
        XCTAssertFalse(stumm.waehlbar)
        XCTAssertEqual(stumm.satz, "Tailscale am Mac an?")
    }

    // ------------------------------------------------------------ Bonjour

    private let abdruck = String(repeating: "ab12", count: 16)

    func testBonjourNurMitTls() throws {
        XCTAssertNil(Heimkandidat.ausBonjour(name: "Heim-PC", host: "192.0.2.20",
                                             anschluss: 8731, txt: ["fassung": "1"]),
                     "ein unverschlüsselter Server (--im-heimnetz) ist kein Kandidat")
        let k = try XCTUnwrap(Heimkandidat.ausBonjour(name: "Heim-PC", host: "192.0.2.20",
                                                      anschluss: 8732,
                                                      txt: ["fassung": "1", "tls": "1"]))
        XCTAssertEqual(k.adresse.absoluteString, "https://192.0.2.20:8732")
        XCTAssertEqual(k.weg, .heimnetz)
    }

    func testBonjourMitIpv6OhneZone() throws {
        let k = try XCTUnwrap(Heimkandidat.ausBonjour(name: "x", host: "2001:db8::1%en0",
                                                      anschluss: 8732, txt: ["tls": "1"]))
        XCTAssertEqual(k.adresse.absoluteString, "https://[2001:db8::1]:8732")
    }

    func testImWlanOhneGesehenesZertifikatNichtWaehlbar() throws {
        let k = try XCTUnwrap(Heimkandidat.ausBonjour(name: "x", host: "192.0.2.20",
                                                      anschluss: 8732, txt: ["tls": "1"]))
        XCTAssertFalse(k.nach(halloStatus: 200, daten: hallo, fingerabdruck: nil).waehlbar)
        let mit = k.nach(halloStatus: 200, daten: hallo, fingerabdruck: abdruck.uppercased())
        XCTAssertTrue(mit.waehlbar)
        XCTAssertTrue(mit.satz.contains("ab12 ab12 ab12 ab12"), mit.satz)
    }

    func testDieSucheNimmtKeinDoppel() throws {
        var suche = Heimsuche()
        let k = try XCTUnwrap(Heimkandidat.ausBonjour(name: "x", host: "192.0.2.20",
                                                      anschluss: 8732, txt: ["tls": "1"]))
        suche.nimm([k])
        suche.setze(k.nach(halloStatus: 200, daten: hallo, fingerabdruck: abdruck))
        suche.nimm([k])
        XCTAssertEqual(suche.kandidaten.count, 1)
        XCTAssertEqual(suche.waehlbare.count, 1, "der Stand bleibt beim zweiten Fund")
    }

    // ------------------------------------------------------------ anfordern

    func testAnfordernDeuten() {
        XCTAssertEqual(Anforderungsergebnis.lies(status: 200, daten: Data(
            #"{"angezeigt": true, "neu": true, "satz": "Zahl am Heim-PC angezeigt, gültig bis 14:05."}"#.utf8)),
            .angezeigt(satz: "Zahl am Heim-PC angezeigt, gültig bis 14:05.", neu: true))
        XCTAssertEqual(Anforderungsergebnis.lies(status: 429, daten: Data(
            #"{"angezeigt": false, "warten_s": 12, "satz": "Eine neue Zahl gibt es in 12 s."}"#.utf8)),
            .warten(satz: "Eine neue Zahl gibt es in 12 s.", sekunden: 12))
        if case .abgelehnt(let satz) = Anforderungsergebnis.lies(status: 404, daten: Data()) {
            XCTAssertTrue(satz.contains("älterer Server"), satz)
        } else {
            XCTFail("404 ist abgelehnt")
        }
    }

    func testDieAnfrageZumAnfordernTraegtKeineAnmeldung() throws {
        XCTAssertNil(try Anfragen.kopplungAnfordern().kopfzeilen["Authorization"])
        XCTAssertNil(Anfragen.hallo().kopfzeilen["Authorization"])
    }

    // ------------------------------------------------------------ verbinden

    private let tailscaleBasis = URL(string: "https://heim-pc.beispiel.ts.net:8443")!

    private func antwort(_ zugang: String) -> Data {
        Data("""
        {"verbunden": true, "benutzer": "probe", "kennwort": "k-32", "satz": "Verbunden.",
         "zugang": \(zugang)}
        """.utf8)
    }

    func testUeberTailscaleGiltDieAdresseUnterDerGefragtWurde() {
        let e = Verbindungsergebnis.lies(
            status: 200,
            daten: antwort(#"{"weg": "wie_gefragt", "adresse": null, "zertifikat_sha256": null}"#),
            gefragtBei: tailscaleBasis, gesehen: nil)
        XCTAssertEqual(e, .verbunden(Heimzugang(adresse: tailscaleBasis,
                                                anmeldung: Anmeldung(benutzer: "probe",
                                                                     kennwort: "k-32"),
                                                fingerabdruck: nil), satz: "Verbunden."))
    }

    func testImWlanWirdDerGeseheneFingerabdruckAngeheftet() throws {
        let basis = try XCTUnwrap(URL(string: "https://192.0.2.20:8732"))
        let zugang = #"{"weg": "heimnetz", "adresse": "https://192.0.2.20:8732", "#
            + #""zertifikat_sha256": "\#(abdruck)"}"#
        guard case .verbunden(let z, _) = Verbindungsergebnis.lies(
            status: 200, daten: antwort(zugang), gefragtBei: basis, gesehen: abdruck) else {
            return XCTFail("verbunden erwartet")
        }
        XCTAssertEqual(z.fingerabdruck, abdruck)
        XCTAssertEqual(z.adresse, basis)
    }

    func testEinAnderesZertifikatAlsGenanntWirdNichtGemerkt() throws {
        let basis = try XCTUnwrap(URL(string: "https://192.0.2.20:8732"))
        let zugang = #"{"weg": "heimnetz", "adresse": "https://192.0.2.20:8732", "#
            + #""zertifikat_sha256": "\#(abdruck)"}"#
        let anderes = String(repeating: "cd34", count: 16)
        guard case .fehler(let satz) = Verbindungsergebnis.lies(
            status: 200, daten: antwort(zugang), gefragtBei: basis, gesehen: anderes) else {
            return XCTFail("fehler erwartet")
        }
        XCTAssertTrue(satz.contains("nichts gemerkt"), satz)
    }

    func testEineAbgelehnteZahlIstEinFehlversuchEinFehlerNicht() {
        let ab = Verbindungsergebnis.lies(
            status: 403, daten: Data(#"{"verbunden": false, "satz": "Das hat nicht geklappt."}"#.utf8),
            gefragtBei: tailscaleBasis, gesehen: nil)
        XCTAssertEqual(ab, .abgelehnt(satz: "Das hat nicht geklappt."))
        let ohneKennwort = Verbindungsergebnis.lies(
            status: 200, daten: Data(#"{"verbunden": true, "benutzer": "probe", "kennwort": null}"#.utf8),
            gefragtBei: tailscaleBasis, gesehen: nil)
        guard case .fehler = ohneKennwort else { return XCTFail("ohne Kennwort ist ein Fehler") }
    }

    // ------------------------------------------------------------ der Ablauf

    func testDerAblaufSchliesstNachDreiFehlversuchen() throws {
        var ablauf = Koppelablauf()
        let k = Heimkandidat(anzeigename: "heim-pc", adresse: tailscaleBasis, weg: .tailscale)
        XCTAssertFalse(ablauf.waehle(k), "ein nicht antwortender ist nicht wählbar")
        XCTAssertTrue(ablauf.waehle(k.nach(halloStatus: 200, daten: hallo, fingerabdruck: nil)))
        XCTAssertEqual(ablauf.schritt, .zahl)
        ablauf.angefordert(.angezeigt(satz: "steht da", neu: true))
        XCTAssertTrue(ablauf.darfKoppeln("123456"))
        XCTAssertFalse(ablauf.darfKoppeln("12345"))
        for _ in 0..<2 { ablauf.verbinden(.abgelehnt(satz: "Das hat nicht geklappt.")) }
        XCTAssertFalse(ablauf.geschlossen)
        ablauf.verbinden(.fehler(satz: "Leitung weg"))
        XCTAssertFalse(ablauf.geschlossen, "ein Leitungsfehler ist kein Fehlversuch")
        ablauf.verbinden(.abgelehnt(satz: "Das hat nicht geklappt."))
        XCTAssertTrue(ablauf.geschlossen)
        XCTAssertEqual(ablauf.satz, Heimkopplung.satzGeschlossen)
        XCTAssertFalse(ablauf.darfKoppeln("123456"))
        // Die alte Zahl, noch einmal angezeigt, öffnet nichts — nur eine neue.
        ablauf.angefordert(.angezeigt(satz: "steht schon da", neu: false))
        XCTAssertTrue(ablauf.geschlossen)
        ablauf.angefordert(.angezeigt(satz: "neu", neu: true))
        XCTAssertFalse(ablauf.geschlossen)
        let z = Heimzugang(adresse: tailscaleBasis,
                           anmeldung: Anmeldung(benutzer: "probe", kennwort: "k"),
                           fingerabdruck: nil)
        ablauf.verbinden(.verbunden(z, satz: nil))
        XCTAssertEqual(ablauf.schritt, .verbunden)
        XCTAssertEqual(ablauf.zugang, z)
    }

    // ------------------------------------------------------------ Anheften

    func testAnheften() {
        XCTAssertEqual(Fingerabdruck.pruefe(gesehen: abdruck, angeheftet: nil), .systemprueft)
        XCTAssertEqual(Fingerabdruck.pruefe(gesehen: abdruck.uppercased(), angeheftet: abdruck),
                       .passt)
        XCTAssertEqual(Fingerabdruck.pruefe(gesehen: nil, angeheftet: abdruck), .passtNicht)
        XCTAssertEqual(Fingerabdruck.pruefe(gesehen: String(repeating: "0", count: 64),
                                            angeheftet: abdruck), .passtNicht)
    }

    func testFingerabdruckForm() {
        XCTAssertNil(Fingerabdruck.normalisiere("ab12"))
        XCTAssertEqual(Fingerabdruck.normalisiere("AB:" + String(abdruck.dropFirst(2))), abdruck)
        XCTAssertEqual(Fingerabdruck.hex([0x00, 0x0f, 0xab, 0xff]), "000fabff")
        XCTAssertEqual(Fingerabdruck.zeichen("ab12cd34ef567890" + String(repeating: "0", count: 48)),
                       "ab12 cd34 ef56 7890")
    }
}
