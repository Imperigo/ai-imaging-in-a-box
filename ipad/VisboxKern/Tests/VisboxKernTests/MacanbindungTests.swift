import Foundation
import XCTest
import VisboxKern

/// Das iPad arbeitet über den Mac, verschlüsselt (Entscheid 118, 21.10.2026): Koppelschein mit
/// Zertifikat, Gegenprobe nach dem Koppeln, kein Rückfall auf unverschlüsselt, die Sätze.
final class MacanbindungTests: XCTestCase {

    private let abdruck = String(repeating: "ab", count: 32)
    private let fremd = String(repeating: "cd", count: 32)
    private let mac = URL(string: "https://192.0.2.7:8731")!
    private let jetzt: TimeInterval = 1_800_000_000
    private let zugang = Vermittlerzugang.erzeuge()

    // ------------------------------------------------------------- die Adresse des Mac

    func testDieAdresseDesMacIstImmerHttps() {
        XCTAssertEqual(Suche.pruefeMac(eingabe: "192.0.2.7"), .gut(URL(string: "https://192.0.2.7:8731")!, hinweis: nil))
        XCTAssertEqual(Suche.pruefeMac(eingabe: "https://mein-mac.local:8740"),
                       .gut(URL(string: "https://mein-mac.local:8740")!, hinweis: nil))
        guard case .schlecht(let satz) = Suche.pruefeMac(eingabe: "http://192.0.2.7:8731") else {
            return XCTFail("ein ausdrückliches http darf nicht still verschlüsselt werden — und nicht durch")
        }
        XCTAssertTrue(satz.contains("https://"), satz)
        for schlecht in ["", "https://ich:geheim@192.0.2.7", "https://192.0.2.7/pfad", "https://192.0.2.7?x=1",
                         "192.0.2.7:70000", "a b"] {
            guard case .schlecht = Suche.pruefeMac(eingabe: schlecht) else { return XCTFail(schlecht) }
        }
    }

    // ------------------------------------------------------------- der Schein (Fassung 2)

    func testDerScheinTraegtDenAbdruckDesMac() throws {
        let s = try XCTUnwrap(Koppelschein(adresse: mac, zahl: "482913", bis: Int(jetzt) + 120,
                                           abdruck: abdruck.uppercased()))
        XCTAssertEqual(s.abdruck, abdruck, "klein geschrieben")
        XCTAssertEqual(s.text, "\(Marke.koppelschema):2?adresse=https%3A%2F%2F192.0.2.7%3A8731"
                       + "&zahl=482913&bis=\(Int(jetzt) + 120)&abdruck=\(abdruck)")
        XCTAssertEqual(Koppelschein.lies(s.text, jetzt: jetzt), .gut(s))
        XCTAssertFalse(String(describing: s).contains("482913"), "die Zahl nie in einer Ausgabe")
    }

    func testOhneAbdruckOderMitHttpGibtEsKeinenSchein() {
        XCTAssertNil(Koppelschein(adresse: mac, zahl: "482913", bis: Int(jetzt) + 60, abdruck: "ab12"))
        XCTAssertNil(Koppelschein(adresse: URL(string: "http://192.0.2.7:8731")!, zahl: "482913",
                                  bis: Int(jetzt) + 60, abdruck: abdruck),
                     "unverschlüsselt stellt der Mac keinen Schein aus")
    }

    func testEinScheinVomAltenMacSagtEsStattZuKoppeln() {
        let alt = "\(Marke.koppelschema):1?adresse=https%3A%2F%2Frechner.netz.ts.net%3A8443"
            + "&zahl=482913&bis=\(Int(jetzt) + 60)"
        XCTAssertEqual(Koppelschein.lies(alt, jetzt: jetzt), .schlecht(Koppelschein.satzAlterMac))
    }

    func testEinFalscherAbdruckImScheinWirdAbgelehnt() throws {
        let gut = try XCTUnwrap(Koppelschein(adresse: mac, zahl: "482913", bis: Int(jetzt) + 60,
                                             abdruck: abdruck)).text
        for falsch in [String(abdruck.dropLast()), abdruck.uppercased(), "ab:" + abdruck.dropFirst(2), ""] {
            let text = gut.replacingOccurrences(of: "abdruck=\(abdruck)", with: "abdruck=\(falsch)")
            XCTAssertEqual(Koppelschein.lies(text, jetzt: jetzt), .schlecht(Koppelschein.satzAbdruck), falsch)
        }
        let ohne = gut.replacingOccurrences(of: "&abdruck=\(abdruck)", with: "")
        XCTAssertEqual(Koppelschein.lies(ohne, jetzt: jetzt), .schlecht(Koppelschein.satzFremd))
        let http = gut.replacingOccurrences(of: "https%3A", with: "http%3A")
        guard case .schlecht(let grund) = Koppelschein.lies(http, jetzt: jetzt) else { return XCTFail() }
        XCTAssertTrue(grund.hasPrefix("Die Adresse im Code geht nicht:"), grund)
    }

    func testDasFensterStelltDenScheinMitAbdruckAus() throws {
        let f = Koppelfenster(jetzt: jetzt, zahlGiltNoch: nil)
        let s = try XCTUnwrap(f.schein(adresse: mac, zahl: try XCTUnwrap(Kopplungszahl("000123")),
                                       abdruck: abdruck))
        XCTAssertEqual(s.bis, Int(jetzt) + 120)
        XCTAssertEqual(s.abdruck, abdruck)
    }

    // ------------------------------------------------------------- gefunden

    func testDerMacBietetSichVerschluesseltAn() {
        let txt = GefundenerDienst.txtEintraege(Vermittlerangebot.txt)
        XCTAssertEqual(txt["tls"], "1")
        XCTAssertEqual(txt["vermittler"], "mac")
        let d = GefundenerDienst(name: "Haus über Mac", rechner: "192.0.2.7", anschluss: 8731, eintraege: txt)
        XCTAssertTrue(d.ueberDenMac && d.verschluesselt && !d.nurFuerDenMac)
        XCTAssertEqual(d.adresse, mac)
    }

    func testZumKoppelnStehenNurVerschluesselteMacs() {
        let neu = GefundenerDienst(name: "Haus über Mac", rechner: "192.0.2.7", anschluss: 8731,
                                   eintraege: ["vermittler": "mac", "tls": "1"])
        let alt = GefundenerDienst(name: "Haus über Alt", rechner: "192.0.2.8", anschluss: 8731,
                                   eintraege: ["vermittler": "mac"])
        let heim = GefundenerDienst(name: "HomeStation", rechner: "192.0.2.9", anschluss: 8731)
        let heimTls = GefundenerDienst(name: "HomeStation", rechner: "192.0.2.9", anschluss: 8732,
                                       eintraege: ["tls": "1"])
        XCTAssertEqual(Suche.waehleMac([alt, heim, heimTls, neu]), .einer(neu))
        XCTAssertEqual(Suche.alteMacs([alt, heim, neu, alt]), [alt])
        XCTAssertTrue(heimTls.nurFuerDenMac, "der Zuhörer des Heim-PC für den Mac")
        XCTAssertEqual(heim.adresse, URL(string: "http://192.0.2.9:8731"), "ohne tls bleibt http")
        XCTAssertTrue(Suche.satzAlterMac("Alt").contains("unverschlüsselt"))
    }

    func testDerMacIstKeinHeimPcFuerDenMac() {
        XCTAssertNil(Heimkandidat.ausBonjour(name: "Haus über Mac", host: "192.0.2.7", anschluss: 8731,
                                             txt: ["tls": "1", "vermittler": "mac"]))
        XCTAssertNotNil(Heimkandidat.ausBonjour(name: "Heim", host: "192.0.2.9", anschluss: 8732,
                                                txt: ["tls": "1"]))
    }

    // ------------------------------------------------------------- die Anbindung

    func testDieAnbindungWirdAbgelesenNichtGeraten() {
        XCTAssertEqual(Anbindungsart.bestimme(adresse: nil, ueberDenMac: true, abdruck: abdruck), .keine)
        let gut = Anbindungsart.bestimme(adresse: mac, ueberDenMac: true, abdruck: abdruck)
        XCTAssertEqual(gut, .macVerschluesselt(zeichen: "abab abab abab abab"))
        XCTAssertTrue(gut.schloss && gut.darfSprechen)
        XCTAssertNil(gut.satz)
        let alt = Anbindungsart.bestimme(adresse: URL(string: "http://192.0.2.7:8731")!, ueberDenMac: true,
                                         abdruck: nil)
        XCTAssertEqual(alt, .macUngeschuetzt)
        XCTAssertFalse(alt.darfSprechen, "nie unverschlüsselt über den Mac")
        XCTAssertEqual(alt.satz, Macanbindung.satzUngeschuetzt)
        XCTAssertEqual(Anbindungsart.bestimme(adresse: mac, ueberDenMac: true, abdruck: nil), .macUngeschuetzt,
                       "https ohne angeheftetes Zertifikat ist nicht geschützt")
        let direkt = Anbindungsart.bestimme(adresse: URL(string: "https://rechner.netz.ts.net:8443")!,
                                            ueberDenMac: false, abdruck: nil)
        XCTAssertEqual(direkt, .direkt(.tailscale))
        XCTAssertTrue(direkt.darfSprechen, "Übergangsfassung: der direkte Weg geht noch")
        XCTAssertEqual(direkt.satz, Macanbindung.satzDirekt)
        XCTAssertFalse(direkt.schloss)
    }

    func testDieStreckeZumMacHatEigeneSaetze() {
        XCTAssertEqual(Strecke(basis: mac, ueberDenMac: true), .mac)
        XCTAssertEqual(Strecke(basis: mac, ueberDenMac: false), .tailscale)
        XCTAssertEqual(Strecke(basis: URL(string: "http://192.0.2.7:8731")!, ueberDenMac: true), .heimnetz)
        XCTAssertEqual(Strecke.mac.zusatz, " · über den Mac")
        XCTAssertEqual(Leitungsfehler.zertifikat.satzAmIPad(.mac), Macanbindung.satzFremdesZertifikat)
        for f in [Leitungsfehler.nameUnbekannt, .keineVerbindung, .zeitUeberschritten, .abgerissen] {
            let satz = f.satzAmIPad(.mac)
            XCTAssertTrue(satz.contains("Mac"), satz)
            XCTAssertFalse(satz.contains("Tailscale"), satz)
        }
    }

    // ------------------------------------------------------------- Gegenprobe beim Koppeln

    private func verbunden(_ mitAbdruck: String?) throws -> Data {
        var stand = Vermittlerstand(zugang: zugang, abdruck: mitAbdruck)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        let rumpf = Data(#"{"pin":"042917"}"#.utf8)
        let kopf = Anfragekopf(methode: "POST", ziel: Wege.verbinden.pfad,
                               koepfe: [Kopfzeile("Content-Length", "\(rumpf.count)")])
        guard case .antworte(let a) = stand.beantworte(RoheAnfrage(kopf: kopf, rumpf: rumpf), jetzt: 1)
        else { XCTFail(); return Data() }
        XCTAssertEqual(a.status, 200)
        return a.rumpf
    }

    func testDerMacNenntSeinZertifikatBeimKoppeln() throws {
        let antwort = try verbunden(abdruck.uppercased())
        let wert = try JSONWert.lies(antwort)
        XCTAssertEqual(wert["zugang"]?["weg"]?.alsText, "mac")
        XCTAssertEqual(wert["zugang"]?["zertifikat_sha256"]?.alsText, abdruck)
        // DIE APP VON HEUTE LIEST DIE ANTWORT WEITER (das Feld kommt nur dazu).
        guard case .verbunden(let a?, _) = try Kopplungsergebnis.lies(status: 200, daten: antwort) else {
            return XCTFail()
        }
        XCTAssertEqual(a, zugang.anmeldung)
    }

    func testGegenprobe() throws {
        let antwort = try verbunden(abdruck)
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: antwort, gesehen: abdruck, angeheftet: abdruck),
                       .gut(abdruck: abdruck))
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: antwort, gesehen: abdruck, angeheftet: nil),
                       .gut(abdruck: abdruck), "beim Abtippen: der gesehene, wenn der Mac ihn nennt")
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: antwort, gesehen: fremd, angeheftet: nil),
                       .abgelehnt(Macanbindung.satzGegenprobe), "jemand dazwischen")
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: antwort, gesehen: abdruck, angeheftet: fremd),
                       .abgelehnt(Macanbindung.satzGegenprobe), "nicht der Mac aus dem Schein")
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: antwort, gesehen: nil, angeheftet: abdruck),
                       .abgelehnt(Macanbindung.satzGegenprobe))
        let ohne = try verbunden(nil)
        XCTAssertEqual(Macanbindung.pruefeKopplung(antwort: ohne, gesehen: abdruck, angeheftet: abdruck),
                       .abgelehnt(Macanbindung.satzOhneAbdruck), "ein Mac mit altem Stand")
    }

    // ------------------------------------------------------------- wiederfinden

    func testKeinRueckfallAufUnverschluesselt() {
        let neu = GefundenerDienst(name: "Haus über Mac", rechner: "192.0.2.20", anschluss: 8731,
                                   eintraege: ["vermittler": "mac", "tls": "1"])
        XCTAssertEqual(Macanbindung.wiedergefunden(gemerkt: mac, fund: neu),
                       .neu(URL(string: "https://192.0.2.20:8731")!))
        let gleich = GefundenerDienst(name: "Haus über Mac", rechner: "192.0.2.7", anschluss: 8731,
                                      eintraege: ["vermittler": "mac", "tls": "1"])
        XCTAssertEqual(Macanbindung.wiedergefunden(gemerkt: mac, fund: gleich), .gleich)
        let alt = GefundenerDienst(name: "Haus über Mac", rechner: "192.0.2.20", anschluss: 8731,
                                   eintraege: ["vermittler": "mac"])
        guard case .unverschluesselt(let satz) = Macanbindung.wiedergefunden(gemerkt: mac, fund: alt) else {
            return XCTFail("ein Fund ohne tls darf die Adresse nicht ersetzen")
        }
        XCTAssertTrue(satz.contains("unverschlüsselt"))
        let offen = GefundenerDienst(name: "Haus über Mac", rechner: nil, anschluss: nil)
        XCTAssertEqual(Macanbindung.wiedergefunden(gemerkt: mac, fund: offen), .offen)
    }

    func testAngeheftetWirdNurBeimGemerktenMac() {
        XCTAssertTrue(Macanbindung.istMac(host: "192.0.2.7", port: 8731, gemerkt: mac))
        XCTAssertFalse(Macanbindung.istMac(host: "192.0.2.7", port: 8732, gemerkt: mac))
        XCTAssertFalse(Macanbindung.istMac(host: "rechner.netz.ts.net", port: 8731, gemerkt: mac))
        XCTAssertFalse(Macanbindung.istMac(host: "192.0.2.7", port: 8731, gemerkt: nil))
        let v6 = URL(string: "https://[fe80::1]:8731")!
        XCTAssertTrue(Macanbindung.istMac(host: "fe80::1", port: 8731, gemerkt: v6))
    }

    // ------------------------------------------------------------- die Adresse im Schein

    func testDieAdresseDesMacIstDieImWlan() {
        let liste: [(name: String, adresse: String)] = [
            ("lo0", "127.0.0.1"), ("utun3", "100.101.102.103"), ("en5", "169.254.10.2"),
            ("bridge100", "192.168.2.1"), ("en1", "10.0.0.5"), ("en0", "192.168.1.24")]
        XCTAssertEqual(Macanbindung.adresseFuerIpad(schnittstellen: liste), "192.168.1.24")
        XCTAssertEqual(Macanbindung.adresseFuerIpad(schnittstellen: Array(liste.dropLast())), "10.0.0.5")
        XCTAssertEqual(Macanbindung.adresseFuerIpad(schnittstellen: [("bridge100", "192.168.2.1"),
                                                                    ("awdl0", "192.168.9.9")]),
                       "192.168.2.1", "der Hotspot des Mac vor dem Rest")
        XCTAssertNil(Macanbindung.adresseFuerIpad(schnittstellen: [("lo0", "127.0.0.1"),
                                                                  ("utun0", "100.64.0.1")]),
                     "nur Tailscale: das iPad erreicht den Mac so nicht")
        XCTAssertEqual(Macanbindung.adresse(ip: "192.168.1.24", anschluss: 8731),
                       URL(string: "https://192.168.1.24:8731"))
    }
}

