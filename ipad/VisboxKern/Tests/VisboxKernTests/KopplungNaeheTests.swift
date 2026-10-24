import Foundation
import XCTest
import VisboxKern

/// iPad koppeln ohne Abtippen (Entscheide 99/99a/99b): der Koppelschein für QR-Code und
/// Nähe-Verbindung, das Fenster von zwei Minuten, die Absprache beider Seiten.
final class KopplungNaeheTests: XCTestCase {

    /// Seit Entscheid 118 (21.10.2026) die Adresse **des Mac**, verschlüsselt, und sein Abdruck.
    private let heim = URL(string: "https://rechner.netz.ts.net:8443")!
    private let abdruck = String(repeating: "0f", count: 32)
    private let jetzt: TimeInterval = 1_800_000_000

    private func schein(bis: Int? = nil, zahl: String = "482913") throws -> Koppelschein {
        try XCTUnwrap(Koppelschein(adresse: heim, zahl: zahl, bis: bis ?? Int(jetzt) + 120,
                                   abdruck: abdruck))
    }

    private func gelesen(_ text: String, jetzt t: TimeInterval? = nil) -> Koppelschein? {
        if case .gut(let s) = Koppelschein.lies(text, jetzt: t ?? jetzt) { return s }
        return nil
    }

    private func satz(_ text: String, jetzt t: TimeInterval? = nil) -> String? {
        if case .schlecht(let s) = Koppelschein.lies(text, jetzt: t ?? jetzt) { return s }
        return nil
    }

    // ------------------------------------------------------------ die Form

    func testDerScheinHatDieVerabredeteForm() throws {
        let s = try schein()
        XCTAssertEqual(s.text, "\(Marke.koppelschema):2?adresse=https%3A%2F%2Frechner.netz.ts.net"
                       + "%3A8443&zahl=482913&bis=\(Int(jetzt) + 120)&abdruck=\(abdruck)")
    }

    func testHinUndZurueck() throws {
        let s = try schein()
        XCTAssertEqual(gelesen(s.text), s)
        XCTAssertEqual(Koppelschein.lies(s.daten, jetzt: jetzt), .gut(s))
    }

    func testDieAdresseImWlanGehtHinUndZurueckAberNurVerschluesselt() throws {
        let lan = URL(string: "https://192.0.2.10:8731")!
        let s = try XCTUnwrap(Koppelschein(adresse: lan, zahl: "000123", bis: Int(jetzt) + 60,
                                           abdruck: abdruck))
        XCTAssertEqual(gelesen(s.text)?.adresse, lan)
        XCTAssertEqual(gelesen(s.text)?.zahl.ziffern, "000123", "führende Nullen bleiben")
        XCTAssertNil(Koppelschein(adresse: URL(string: "http://192.0.2.10:8731")!, zahl: "000123",
                                  bis: Int(jetzt) + 60, abdruck: abdruck), "Entscheid 118")
    }

    func testImScheinStehenNurAdresseZahlFristUndAbdruck() throws {
        // ENTSCHEID 99: nie das Kennwort, nie der Benutzer — weder im QR-Code noch über die
        // Nähe-Verbindung (beide tragen denselben Schein). Seit 118 dazu der Abdruck des Mac.
        XCTAssertEqual(Koppelschein.felder, ["adresse", "zahl", "bis", "abdruck"])
        let text = try schein().text.lowercased()
        for verboten in ["kennwort", "passwort", "password", "benutzer", "user", "authorization"] {
            XCTAssertFalse(text.contains(verboten), verboten)
        }
        let frage = try XCTUnwrap(text.split(separator: "?").last)
        let namen = frage.split(separator: "&").map { String($0.split(separator: "=")[0]) }
        XCTAssertEqual(namen, Koppelschein.felder)
    }

    func testDieBeschreibungNenntDieZahlNicht() throws {
        XCTAssertFalse(String(describing: try schein()).contains("482913"))
    }

    // ------------------------------------------------------------ abgelehnt

    func testAbgelaufenWirdAbgelehnt() throws {
        let s = try schein(bis: Int(jetzt) + 10)
        XCTAssertNotNil(gelesen(s.text, jetzt: jetzt + 9))
        XCTAssertEqual(satz(s.text, jetzt: jetzt + 10), Koppelschein.satzAbgelaufen)
        XCTAssertEqual(satz(s.text, jetzt: jetzt + 3600), Koppelschein.satzAbgelaufen)
    }

    func testLaengerAlsZweiMinutenStelltDerMacKeinenAus() throws {
        let grenze = Int(jetzt + Naehekopplung.fenster + Naehekopplung.uhrenspiel)
        XCTAssertNotNil(gelesen(try schein(bis: grenze).text))
        XCTAssertEqual(satz(try schein(bis: grenze + 1).text), Koppelschein.satzZuLange)
        XCTAssertEqual(satz(try schein(bis: Int(jetzt) + 86_400 * 365).text),
                       Koppelschein.satzZuLange)
    }

    func testFalschesSchemaUndFalscheFassung() throws {
        let gut = try schein().text
        let ohneSchema = String(gut.drop(while: { $0 != ":" }).dropFirst())
        XCTAssertEqual(satz("https://beispiel.org/?" + ohneSchema), Koppelschein.satzFremd)
        XCTAssertEqual(satz("anderes:" + ohneSchema), Koppelschein.satzFremd)
        XCTAssertEqual(satz(gut.replacingOccurrences(of: ":2?", with: ":3?")),
                       Koppelschein.satzFassung)
        XCTAssertEqual(satz(gut.replacingOccurrences(of: ":2?", with: ":1?")),
                       Koppelschein.satzAlterMac, "ein Mac vor Entscheid 118")
        XCTAssertEqual(satz("\(Marke.koppelschema):2"), Koppelschein.satzFremd)
        XCTAssertEqual(satz(""), Koppelschein.satzFremd)
    }

    func testFalscheZahl() throws {
        let gut = try schein().text
        for falsch in ["48291", "4829130", "48a913", "٤٨٢٩١٣", "+48291", "", "48 913"] {
            let kodiert = falsch.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? ""
            XCTAssertEqual(satz(gut.replacingOccurrences(of: "zahl=482913", with: "zahl=\(kodiert)")),
                           Koppelschein.satzZahl, falsch)
        }
        XCTAssertNil(Koppelschein(adresse: heim, zahl: "12345", bis: Int(jetzt) + 60, abdruck: abdruck))
        XCTAssertNil(Koppelschein(adresse: heim, zahl: " 123456", bis: Int(jetzt) + 60, abdruck: abdruck))
    }

    func testFremdeDoppelteUndFehlendeFelder() throws {
        let gut = try schein().text
        XCTAssertEqual(satz(gut + "&kennwort=geheim"), Koppelschein.satzFremd,
                       "ein Schein mit Kennwort stammt nicht vom Mac")
        XCTAssertEqual(satz(gut + "&zahl=111111"), Koppelschein.satzFremd)
        XCTAssertEqual(satz(gut.replacingOccurrences(of: "&zahl=482913", with: "")),
                       Koppelschein.satzFremd)
        XCTAssertEqual(satz(gut + "&"), Koppelschein.satzFremd)
        XCTAssertEqual(satz(gut.replacingOccurrences(of: "bis=", with: "bis=-")),
                       Koppelschein.satzFremd)
    }

    func testEineSchlechteAdresseSagtWarum() throws {
        let gut = try schein().text
        let mitKennwort = "https%3A%2F%2Fich%3Ageheim%40rechner.netz.ts.net%3A8443"
        let text = gut.replacingOccurrences(
            of: "https%3A%2F%2Frechner.netz.ts.net%3A8443", with: mitKennwort)
        let grund = try XCTUnwrap(satz(text))
        XCTAssertTrue(grund.hasPrefix("Die Adresse im Code geht nicht:"), grund)
        XCTAssertNil(Koppelschein(adresse: URL(string: "ftp://192.0.2.10")!, zahl: "123456",
                                  bis: Int(jetzt) + 60, abdruck: abdruck))
    }

    func testZuLangWirdNichtErstGelesen() throws {
        let lang = try schein().text + String(repeating: "x", count: Koppelschein.hoechstensBytes)
        XCTAssertEqual(satz(lang), Koppelschein.satzZuLang)
        XCTAssertEqual(Koppelschein.lies(Data(lang.utf8), jetzt: jetzt),
                       .schlecht(Koppelschein.satzZuLang))
        XCTAssertEqual(Koppelschein.lies(Data([0xff, 0xfe]), jetzt: jetzt),
                       .schlecht(Koppelschein.satzFremd))
    }

    // ------------------------------------------------------------ das Fenster

    func testDasFensterIstZweiMinutenOffen() {
        XCTAssertEqual(Naehekopplung.fenster, 120, "Entscheid 99a")
        let f = Koppelfenster(jetzt: jetzt, zahlGiltNoch: 600)
        XCTAssertTrue(f.offen(jetzt: jetzt))
        XCTAssertTrue(f.offen(jetzt: jetzt + 119.9))
        XCTAssertFalse(f.offen(jetzt: jetzt + 120))
        XCTAssertEqual(f.rest(jetzt: jetzt), 120)
        XCTAssertEqual(f.rest(jetzt: jetzt + 0.5), 120, "aufgerundet")
        XCTAssertEqual(f.rest(jetzt: jetzt + 500), 0)
    }

    func testDasFensterGiltNieLaengerAlsDieZahl() {
        let f = Koppelfenster(jetzt: jetzt, zahlGiltNoch: 45)
        XCTAssertFalse(f.offen(jetzt: jetzt + 45))
        XCTAssertEqual(Koppelfenster(jetzt: jetzt, zahlGiltNoch: nil).schluss, jetzt + 120)
        XCTAssertFalse(Koppelfenster(jetzt: jetzt, zahlGiltNoch: -5).offen(jetzt: jetzt))
    }

    func testDerScheinDesFenstersGiltBisZuSeinemSchluss() throws {
        let f = Koppelfenster(jetzt: jetzt + 0.7, zahlGiltNoch: 600)
        let s = try XCTUnwrap(f.schein(adresse: heim, zahl: try XCTUnwrap(Kopplungszahl("482913")),
                                                  abdruck: abdruck))
        XCTAssertEqual(s.bis, Int(jetzt) + 120)
        XCTAssertNotNil(gelesen(s.text, jetzt: jetzt + 1))
        XCTAssertEqual(satz(s.text, jetzt: jetzt + 121), Koppelschein.satzAbgelaufen)
    }

    func testDieUhrZeigtMinutenUndSekunden() {
        XCTAssertEqual(Koppelfenster.uhrtext(120), "2:00")
        XCTAssertEqual(Koppelfenster.uhrtext(119), "1:59")
        XCTAssertEqual(Koppelfenster.uhrtext(5), "0:05")
        XCTAssertEqual(Koppelfenster.uhrtext(-3), "0:00")
    }

    func testDieZeileNenntHoechstensDasFenster() throws {
        let daten = Data(#"{"zahl": "123456", "gilt_noch_s": 600}"#.utf8)
        let a = try XCTUnwrap(try Koppelzahl.angebot(status: 200, daten: daten))
        XCTAssertEqual(a.zahl.ziffern, "123456")
        XCTAssertEqual(a.giltNoch, 600)
        XCTAssertNil(try Koppelzahl.angebot(status: 200, daten: Data(#"{"zahl": "12a456"}"#.utf8)))
        XCTAssertTrue(Koppelzahl.zeile(status: 200, daten: daten, adresse: heim).satz
            .contains("gilt 2 min"))
    }

    // ------------------------------------------------------------ der Dienst

    func testDerDienstDerNaeheIstGueltig() {
        XCTAssertTrue(Naehekopplung.istGueltigeDienstart(Naehekopplung.dienstart))
        XCTAssertEqual(Naehekopplung.dienstart, Marke.naehedienst)
        XCTAssertEqual(Naehekopplung.bonjourDienste,
                       ["_\(Marke.naehedienst)._tcp", "_\(Marke.naehedienst)._udp"])
        XCTAssertNotEqual(Naehekopplung.bonjourDienste[0], Marke.dienst,
                          "ein eigener Dienst, nicht der der HomeStation")
    }

    func testDieRegelnDerDienstart() {
        for gut in ["a", "abc-def", "x1-y2", "abcdefghijklmno"] {
            XCTAssertTrue(Naehekopplung.istGueltigeDienstart(gut), gut)
        }
        for schlecht in ["", "abcdefghijklmnop", "Gross", "mit_strich", "-vorn", "hinten-",
                         "dop--pelt", "123", "ä-umlaut", "leer zeichen"] {
            XCTAssertFalse(Naehekopplung.istGueltigeDienstart(schlecht), schlecht)
        }
    }

    func testDerAnzeigenameHatHoechstens63Bytes() {
        XCTAssertEqual(Naehekopplung.anzeigename("  Arbeitsrechner ", ersatz: "Mac"), "Arbeitsrechner")
        XCTAssertEqual(Naehekopplung.anzeigename("", ersatz: "Mac"), "Mac")
        let lang = String(repeating: "ä", count: 40) // 80 Bytes
        let kurz = Naehekopplung.anzeigename(lang, ersatz: "Mac")
        XCTAssertLessThanOrEqual(kurz.utf8.count, 63)
        XCTAssertEqual(kurz, String(repeating: "ä", count: 31), "kein Zeichen zerschnitten")
    }

    // ------------------------------------------------------------ beide bestätigen

    func testOhneBeideBestaetigungenGehtNichtsHinaus() {
        var a = Naeheabsprache()
        XCTAssertFalse(a.darfSenden(verschluesselt: true, fensterOffen: true))
        // Ohne angenommene Einladung: keine Sitzung, kein «Koppeln».
        a.sitzungSteht()
        a.macSagtKoppeln()
        XCTAssertFalse(a.verbunden)
        XCTAssertFalse(a.macKoppelt)
        XCTAssertFalse(a.darfSenden(verschluesselt: true, fensterOffen: true))

        XCTAssertTrue(a.einladung(vermerk: Naehekopplung.einladungsvermerk))
        XCTAssertFalse(a.fragt, "der Mac fragt erst, wenn die Sitzung steht")
        a.macSagtKoppeln()
        XCTAssertFalse(a.macKoppelt, "«Koppeln» ohne stehende Sitzung zählt nicht")
        a.sitzungSteht()
        XCTAssertTrue(a.verbunden, "die Einladung mit Vermerk wird sofort angenommen")
        XCTAssertTrue(a.fragt)
        XCTAssertFalse(a.darfSenden(verschluesselt: true, fensterOffen: true),
                       "die Sitzung steht, aber der Mensch am Mac hat noch nicht zugestimmt")
        a.macSagtKoppeln()
        XCTAssertFalse(a.fragt)
        XCTAssertTrue(a.darfSenden(verschluesselt: true, fensterOffen: true))
        XCTAssertFalse(a.darfSenden(verschluesselt: false, fensterOffen: true),
                       "nie unverschlüsselt")
        XCTAssertFalse(a.darfSenden(verschluesselt: true, fensterOffen: false),
                       "nie nach den zwei Minuten")
        a.hatGesendet()
        XCTAssertFalse(a.darfSenden(verschluesselt: true, fensterOffen: true), "nur einmal")
    }

    func testEineEinladungOhneVermerkWirdNichtGefragt() {
        var a = Naeheabsprache()
        XCTAssertFalse(a.einladung(vermerk: nil))
        XCTAssertFalse(a.einladung(vermerk: Data("annehmen/2".utf8)))
        a.sitzungSteht()
        XCTAssertFalse(a.verbunden, "ohne Vermerk keine Sitzung")
        a.macSagtKoppeln()
        XCTAssertFalse(a.macKoppelt)
    }

    // ------------------------------------------------------------ das iPad wartet (24.10.2026)

    /// Der Demolauf: «nicht verbunden» nach drei Sekunden, während der Mac noch fragt — das
    /// war keine Absage. Vor der stehenden Sitzung lädt das iPad neu ein.
    func testNichtVerbundenVorDerSitzungIstKeineAbsage() {
        var e = Naeheeinladung(jetzt: 1000)
        let erste = e.getrennt(jetzt: 1003)
        XCTAssertEqual(erste, .neuEinladen)
        XCTAssertEqual(e.versuche, 2)
        XCTAssertFalse(e.erledigt)
        let zweite = e.getrennt(jetzt: 1005)
        XCTAssertEqual(zweite, .neuEinladen)
        XCTAssertEqual(e.versuche, Naeheeinladung.hoechstensVersuche)
        let dritte = e.getrennt(jetzt: 1007)
        XCTAssertEqual(dritte, .aufgeben(Naehekopplung.satzKeineVerbindung),
                       "nach drei Versuchen sagt es, dass keine Verbindung kam")
        XCTAssertTrue(e.erledigt)
        let danach = e.getrennt(jetzt: 1008)
        XCTAssertEqual(danach, .warten, "erledigt ist erledigt")
    }

    func testNachDerFristWirdNichtMehrNeuEingeladen() {
        var e = Naeheeinladung(jetzt: 0)
        let folge = e.getrennt(jetzt: Naeheeinladung.verbindenHoechstens)
        XCTAssertEqual(folge, .aufgeben(Naehekopplung.satzKeineVerbindung))
    }

    /// Nach der stehenden Sitzung heisst «nicht verbunden» ohne Schein: Der Mac hat abgelehnt
    /// (er schliesst die Sitzung), oder sein Fenster ging zu.
    func testNachDerSitzungIstNichtVerbundenDieAbsage() {
        var e = Naeheeinladung(jetzt: 0)
        e.sitzungSteht()
        let uhr = e.uhr(jetzt: 60)
        XCTAssertEqual(uhr, .warten, "der Mensch am Mac darf sich Zeit nehmen")
        let folge = e.getrennt(jetzt: 61)
        XCTAssertEqual(folge, .aufgeben(Naehekopplung.satzMacAbgelehnt))
        XCTAssertTrue(e.erledigt)
    }

    func testDieUhr() {
        var ohne = Naeheeinladung(jetzt: 0)
        let knapp = ohne.uhr(jetzt: Naeheeinladung.verbindenHoechstens - 0.1)
        XCTAssertEqual(knapp, .warten)
        let um = ohne.uhr(jetzt: Naeheeinladung.verbindenHoechstens)
        XCTAssertEqual(um, .aufgeben(Naehekopplung.satzKeineVerbindung))

        var mit = Naeheeinladung(jetzt: 0)
        mit.sitzungSteht()
        let spaeter = mit.uhr(jetzt: Naeheeinladung.verbindenHoechstens + 5)
        XCTAssertEqual(spaeter, .warten, "steht die Sitzung, gilt das Fenster des Mac")
        let zu = mit.uhr(jetzt: Naehekopplung.fenster)
        XCTAssertEqual(zu, .aufgeben(Naehekopplung.satzFristUm))
    }

    func testMitDemScheinIstAllesErledigt() {
        var e = Naeheeinladung(jetzt: 0)
        e.sitzungSteht()
        e.scheinDa()
        let getrennt = e.getrennt(jetzt: 5)
        XCTAssertEqual(getrennt, .warten, "der Mac schliesst nach dem Schein")
        let uhr = e.uhr(jetzt: 500)
        XCTAssertEqual(uhr, .warten)
    }

    func testDieFristenPassenZumFenster() {
        XCTAssertLessThan(Naeheeinladung.verbindenHoechstens, Naehekopplung.fenster)
        XCTAssertGreaterThanOrEqual(Naeheeinladung.hoechstensVersuche, 2)
        XCTAssertLessThan(Naeheeinladung.neuEinladenNach, Naeheeinladung.verbindenHoechstens)
    }
}
