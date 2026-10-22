import Foundation
import XCTest
import VisboxKern

/// Das iPad holt die Mappe vom Mac («Visbox eigenständig», Schritt 4, Entscheide 103a/118): welcher
/// Weg am Mac bleibt, die Sicht in der Form des Heim-PC, Bilder nur aus der Sicht, Skizzen in die
/// Mappe am Mac — **gelesen mit den Lesern der App von heute** (`Projektsicht`, `Skizzenquittung`,
/// `Fortschrittsstand`).
final class MacmappensichtTests: XCTestCase {

    private let auftrag = "vis-1761030000-abc123"
    private let jetzt = Date(timeIntervalSince1970: 1_792_000_000)
    private let png = Data([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 1, 2, 3])

    private func mappe() -> Macmappe {
        var m = Macmappe(name: "Demohaus", herkunft: .heim, angelegt: "2026-10-21T08:00:00Z",
                         heimMappe: "Demohaus",
                         knoten: .objekt(["skizzen": .liste([
                            .objekt(["name": .text("skizzen/alt.png"), "erzeugt": .text("2026-10-01T10:00:00Z"),
                                     "ueber": .text("renders/a.png"), "stand": .text("offen"),
                                     "bemerkung": .text("Dach flacher")]),
                            .objekt(["name": .text("skizzen/fehlt.png")]),
                         ])]))
        m.vermerke(auftrag: auftrag)
        return m
    }

    private func kopf(_ methode: String, _ ziel: String) -> Anfragekopf {
        Anfragekopf(methode: methode, ziel: ziel)
    }

    private var laufzettel: Data {
        Data(#"{"status":"done","finished_at":"2026-10-21T09:00:00Z","result":{"images":["bild.png","fehlt.png"]}}"#.utf8)
    }

    // ------------------------------------------------------------- welcher Weg am Mac bleibt

    func testDieMappenwegeBleibenAmMacDerRestGehtWeiter() {
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("GET", "/api/projekt?ordner=x")), .projekt)
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("GET", "/bild?ordner=x&name=bilder%2Fvis-1-abcdef%2Fa.png")),
                       .bild(name: "bilder/vis-1-abcdef/a.png"))
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("GET", "/bild")), .bild(name: ""))
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("POST", "/api/skizze")), .skizze)
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("POST", "/api/rechne")), .rechnen)
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("POST", "/api/rechne-skizze")), .rechnen)
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("POST", "/api/benennen")), .benennen)
        XCTAssertEqual(Ipadmappenwege.ziel(kopf("GET", "/api/fortschritt")), .fortschritt)
        XCTAssertNil(Ipadmappenwege.ziel(kopf("POST", "/api/abbrechen")), "ein Lauf am Heim-PC")
        XCTAssertNil(Ipadmappenwege.ziel(kopf("GET", "/api/skizze")), "nur in der Art des Servers")
        XCTAssertNil(Ipadmappenwege.ziel(kopf("GET", "/api/projekt;x")), "wörtlich, wie die Positivliste")
        XCTAssertNil(Ipadmappenwege.ziel(kopf("POST", "/api/verbinden")))
    }

    // ------------------------------------------------------------- die Sicht

    private func sicht(_ m: Macmappe? = nil, ipadDa: Set<String> = []) -> (JSONWert, [String: String]) {
        Macmappensicht.sicht(m ?? mappe(),
                             heimDateien: ["skizzen/alt.png", "renders/a.png", "renders/notiz.txt",
                                           "bilder/vis-1-abcdef/x.png", "modell.glb"],
                             auftraege: [Auftragsablage(id: auftrag, laufzettel: laufzettel,
                                                        dateien: ["job.json", "bild.png"]),
                                         Auftragsablage(id: "vis-2-abcdef", laufzettel: laufzettel,
                                                        dateien: ["bild.png"])],
                             glbDa: true, ipadDa: ipadDa)
    }

    func testDieSichtLiestSichWieDieDesHeimPc() throws {
        let (s, erlaubt) = sicht()
        let p = try Projektsicht.lies(status: 200, daten: try s.daten())
        XCTAssertEqual(p.name, "Demohaus")
        XCTAssertEqual(p.modell?.stand, .unveraendert)
        XCTAssertEqual(p.bilder?.map { $0.bild }, ["bilder/\(auftrag)/bild.png", "renders/a.png"],
                       "nur fertige, vorhandene Bilder, nur aus vermerkten Aufträgen, kein Text, keine Skizze")
        XCTAssertEqual(p.bilder?.first?.erzeugt, "2026-10-21T09:00:00Z")
        XCTAssertNil(p.bilder?.first?.urteil, "am Mac steht kein Prüfzeichen — geraten wird nicht")
        XCTAssertEqual(p.bilder?.first?.vorhanden, true)
        XCTAssertEqual(p.skizzen?.map { $0.skizze }, ["skizzen/alt.png"], "nur, was als Datei da ist")
        XCTAssertEqual(p.skizzen?.first?.ueber, "renders/a.png")
        XCTAssertEqual(p.skizzen?.first?.bemerkung, "Dach flacher")
        XCTAssertEqual(erlaubt["renders/a.png"], "heim/renders/a.png")
        XCTAssertEqual(erlaubt["bilder/\(auftrag)/bild.png"], "bilder/\(auftrag)/bild.png")
        XCTAssertEqual(erlaubt["skizzen/alt.png"], "heim/skizzen/alt.png")
        XCTAssertNil(erlaubt["bilder/vis-1-abcdef/x.png"], "ein Heim-Weg, den die Sicht anders läse")
    }

    func testDieSichtErfindetKeinFeld() throws {
        let (s, _) = sicht(ipadDa: [])
        let felder = Set(try XCTUnwrap(s.alsObjekt).keys)
        XCTAssertEqual(felder, Set(Macmappensicht.felderDerSicht + [Macmappensicht.eigenesFeld]))
        let bild = try XCTUnwrap(s["bilder"]?.alsListe?.first?.alsObjekt)
        XCTAssertEqual(Set(bild.keys), Set(Macmappensicht.felderDesBildes))
        let skizze = try XCTUnwrap(s["skizzen"]?.alsListe?.first?.alsObjekt)
        XCTAssertEqual(Set(skizze.keys), Set(Macmappensicht.felderDerSkizze))
    }

    func testOhneModellSagtDieSichtWarum() throws {
        let (s, _) = Macmappensicht.sicht(mappe(), heimDateien: [], auftraege: [], glbDa: false, ipadDa: [])
        let p = try Projektsicht.lies(status: 200, daten: try s.daten())
        XCTAssertEqual(p.modell?.stand, .fehlt)
        XCTAssertEqual(p.modell?.grund, Mappenkern.satzOhneModell("Demohaus"))
        XCTAssertEqual(p.bilder, [])
    }

    func testBilderNurAusDerSicht() {
        let (_, erlaubt) = sicht()
        XCTAssertEqual(Macmappensicht.bildweg("renders/a.png", erlaubt: erlaubt), "heim/renders/a.png")
        for fremd in ["", "../mappe.json", "mappe.json", "renders/notiz.txt", "heim/renders/a.png",
                      "bilder/vis-2-abcdef/bild.png", "/etc/passwd"] {
            XCTAssertNil(Macmappensicht.bildweg(fremd, erlaubt: erlaubt), fremd)
        }
        XCTAssertEqual(Macmappensicht.inhaltstyp("a.PNG"), "image/png")
        XCTAssertEqual(Macmappensicht.inhaltstyp("a.jpeg"), "image/jpeg")
    }

    func testWegeInDerMappe() {
        XCTAssertEqual(Macmappensicht.weg(inDerMappe: "bilder/\(auftrag)/a.png"), "bilder/\(auftrag)/a.png")
        XCTAssertEqual(Macmappensicht.weg(inDerMappe: "ipad/skizze-1.png"), "ipad/skizze-1.png")
        XCTAssertEqual(Macmappensicht.weg(inDerMappe: "renders/a.png"), "heim/renders/a.png")
        XCTAssertNil(Macmappensicht.weg(inDerMappe: "../a.png"))
        XCTAssertEqual(Mappenkern.skizzenweg("ipad/skizze-1.png"), "ipad/skizze-1.png")
        XCTAssertEqual(Mappenkern.skizzenweg("skizzen/a.png"), "heim/skizzen/a.png")
    }

    // ------------------------------------------------------------- Skizzen ablegen

    private func rumpf(_ felder: [String: JSONWert]) throws -> Data {
        try JSONWert.objekt(felder).daten()
    }

    func testEineSkizzeVomIpadLandetInDerMappeAmMac() throws {
        // DIE BAUFORM DER APP VON HEUTE (`Anfragen.skizze`), nicht eine eigene.
        let anfrage = try Anfragen.skizze(png: png, ueber: "renders/a.png", bemerkung: "heller",
                                          name: "Variante", ordner: "egal", schluessel: "a1b2c3d4e5",
                                          anmeldung: nil)
        let ablage = Macskizzen.lege(try XCTUnwrap(anfrage.rumpf), in: mappe(), jetzt: jetzt, zusatz: "Q7z!",
                                     gespeichert: { _ in nil })
        guard case .neu(let eintrag, let daten, let antwort) = ablage else { return XCTFail("\(ablage)") }
        XCTAssertEqual(daten, png)
        XCTAssertEqual(eintrag.name, "ipad/skizze-20261014-174640-q7z.png")
        XCTAssertEqual(eintrag.ueber, "renders/a.png")
        XCTAssertEqual(eintrag.bemerkung, "heller · gewünschter Name: Variante")
        XCTAssertEqual(eintrag.stand, "offen")
        XCTAssertEqual(eintrag.schluessel, "a1b2c3d4e5")
        XCTAssertEqual(eintrag.bytes, png.count)
        let quittung = try Skizzenquittung.lies(status: 200, daten: try antwort.daten())
        XCTAssertEqual(quittung.skizze, eintrag.name)
        XCTAssertEqual(quittung.hinweis, Macskizzen.hinweis)
        XCTAssertEqual(Sendeergebnis.aus(status: 200, daten: try antwort.daten()),
                       .angekommen(skizze: eintrag.name, hinweis: Macskizzen.hinweis))

        // VERMERKT: Die Sicht und die Knotenansicht sehen sie, sobald die Datei liegt.
        var m = mappe()
        Macskizzen.vermerke(eintrag, in: &m)
        let (s, erlaubt) = sicht(m, ipadDa: [eintrag.name])
        let p = try Projektsicht.lies(status: 200, daten: try s.daten())
        XCTAssertEqual(p.skizzen?.map { $0.skizze }, ["skizzen/alt.png", eintrag.name])
        XCTAssertEqual(erlaubt[eintrag.name], eintrag.name)
        let knoten = Mappenkern.knotenAntwort(m, glbDa: true, skizzenDa: ["skizzen/alt.png", eintrag.name])
        let namen = knoten["skizzen"]?.alsListe?.compactMap { $0["name"]?.alsText }
        XCTAssertEqual(namen, [eintrag.name, "skizzen/alt.png"], "die neueste zuerst")
        XCTAssertEqual(knoten["skizzen"]?.alsListe?.first?["bemerkung"]?.alsText, eintrag.bemerkung)
        XCTAssertEqual(knoten["skizzen"]?.alsListe?.first?["standpunkt"]?.alsText, "mappe")
        XCTAssertEqual(Mappenkern.skizzennamen(m), ["skizzen/alt.png", "skizzen/fehlt.png", eintrag.name])
        // Fund A: dieselbe Antwort, wenn nur bekannt ist, welche Wege als Datei liegen — so liest
        // `skizzen_lesen` die Mappe am Mac (die Skizze vom iPad steht darin, die fehlende nicht).
        let liegend: Set<String> = [Mappenkern.skizzenweg("skizzen/alt.png")!, Mappenkern.skizzenweg(eintrag.name)!,
                                    Mappenkern.modelldatei]
        XCTAssertEqual(Mappenkern.knotenAntwort(m, liegt: { liegend.contains($0) }), knoten)

        // UND DIE MAPPE SCHREIBT SICH MIT DEM FELD — eine ohne schreibt es nicht.
        XCTAssertEqual(Macmappe.lies(try m.daten()), m)
        XCTAssertNil(try JSONWert.lies(try mappe().daten())["skizzen"],
                     "eine Mappe ohne Skizzen vom iPad bleibt, wie sie war")
    }

    func testDerSchluesselSchuetztVorDoppelsendung() throws {
        let r = try rumpf(["png_base64": .text(png.base64EncodedString()), "schluessel": .text("a1b2c3d4e5")])
        guard case .neu(let eintrag, _, let erste) = Macskizzen.lege(r, in: mappe(), jetzt: jetzt, zusatz: "x",
                                                                      gespeichert: { _ in nil }) else {
            return XCTFail()
        }
        var m = mappe()
        Macskizzen.vermerke(eintrag, in: &m)
        XCTAssertEqual(Macskizzen.lege(r, in: m, jetzt: jetzt, zusatz: "y", gespeichert: { $0 == eintrag.name ? self.png : nil }),
                       .wiederholung(antwort: erste), "dieselbe Antwort, keine zweite Datei")
        let anders = try rumpf(["png_base64": .text(Data(png + [9]).base64EncodedString()),
                                "schluessel": .text("a1b2c3d4e5")])
        guard case .abgewiesen(_, 409) = Macskizzen.lege(anders, in: m, jetzt: jetzt, zusatz: "y",
                                                         gespeichert: { _ in self.png }) else {
            return XCTFail("eine andere Zeichnung unter demselben Schlüssel ginge still verloren")
        }
    }

    func testOhneSchluesselZweiDateienMitFreiemNamen() throws {
        let r = try rumpf(["png_base64": .text(png.base64EncodedString())])
        guard case .neu(let a, _, _) = Macskizzen.lege(r, in: mappe(), jetzt: jetzt, zusatz: "x",
                                                        gespeichert: { _ in nil }) else { return XCTFail() }
        var m = mappe()
        Macskizzen.vermerke(a, in: &m)
        guard case .neu(let b, _, _) = Macskizzen.lege(r, in: m, jetzt: jetzt, zusatz: "x",
                                                        gespeichert: { _ in nil }) else { return XCTFail() }
        XCTAssertNotEqual(a.name, b.name)
        XCTAssertEqual(b.name, "ipad/skizze-20261014-174640-x-2.png")
    }

    func testAbgewiesenWieAmHeimPc() throws {
        func status(_ felder: [String: JSONWert]) throws -> Int? {
            if case .abgewiesen(_, let s) = Macskizzen.lege(try rumpf(felder), in: mappe(), jetzt: jetzt,
                                                            zusatz: "x", gespeichert: { _ in nil }) { return s }
            return nil
        }
        XCTAssertEqual(try status([:]), 400, "ohne Zeichnung")
        XCTAssertEqual(try status(["png_base64": .text("kein base64!")]), 400)
        XCTAssertEqual(try status(["png_base64": .text(Data("GIF89a".utf8).base64EncodedString())]), 400,
                       "kein PNG")
        XCTAssertEqual(try status(["png_base64": .text(png.base64EncodedString()), "schluessel": .text("kurz")]),
                       400)
        let gross = Data(Macskizzen.pngKennung) + Data(count: Macskizzen.hoechstensBytes)
        XCTAssertEqual(try status(["png_base64": .text(gross.base64EncodedString())]), 413)
        guard case .abgewiesen(_, 400) = Macskizzen.lege(Data("nicht json".utf8), in: mappe(), jetzt: jetzt,
                                                         zusatz: "x", gespeichert: { _ in nil }) else {
            return XCTFail()
        }
        XCTAssertTrue(Macskizzen.istSchluessel("a1b2c3d4"))
        XCTAssertFalse(Macskizzen.istSchluessel("a1b2 c3d4"))
        XCTAssertFalse(Macskizzen.istSchluessel(String(repeating: "a", count: 129)))
    }

    func testDieListeBleibtBegrenzt() {
        var m = mappe()
        for i in 0..<(Macskizzen.hoechstensEintraege + 2) {
            Macskizzen.vermerke(Macskizze(name: "ipad/s-\(i).png", erzeugt: "", ueber: nil, bemerkung: nil,
                                          schluessel: nil, bytes: 1), in: &m)
        }
        XCTAssertEqual(m.skizzen?.count, Macskizzen.hoechstensEintraege)
        XCTAssertEqual(m.skizzen?.first?.name, "ipad/s-2.png")
    }

    // ------------------------------------------------------------- ohne Heim-PC

    func testDerRuhigeLaufstandLiestSichUndSagtWarum() throws {
        let stand = try Fortschrittsstand.lies(status: 200, daten: try Ipadmappenwege.fortschrittOhneHeim.daten())
        XCTAssertEqual(stand.laeuft, false)
        XCTAssertEqual(stand.belegt, false)
        XCTAssertEqual(Ipadmappenwege.fortschrittOhneHeim["satz"]?.alsText, Ipadmappenwege.satzOhneHeim)
    }

    func testRechnenSagtWoGerechnetWird() {
        XCTAssertTrue(Ipadmappenwege.satzRechnenAmMac.contains("Knotenansicht"))
        XCTAssertTrue(Ipadmappenwege.satzBenennenAmMac.contains("Knotenansicht"))
    }

    // ------------------------------------------- ohne eingerichteten Heim-PC (118a)

    func testOhneRechnerBleibtDasIpadVerbundenUndHoertWarum() throws {
        let laufstand = Ipadmappenwege.ohneRechner(.fortschritt)
        XCTAssertEqual(laufstand.status, 200)
        let stand = try Fortschrittsstand.lies(status: 200, daten: laufstand.rumpf)
        XCTAssertEqual(stand.laeuft, false, "ohne Heim-PC rechnet niemand — das ist wahr")
        let o = try JSONWert.lies(laufstand.rumpf)
        XCTAssertEqual(o["heim_pc"]?.alsText, "nicht eingerichtet")
        XCTAssertEqual(o["satz"]?.alsText, Ipadmappenwege.satzKeinRechner)
        XCTAssertTrue(Ipadmappenwege.satzKeinRechner.hasPrefix("Kein Rechner eingerichtet"))
        // DIESELBEN FELDER wie der ruhige Laufstand, nur zwei Werte anders.
        guard case .objekt(let a) = Ipadmappenwege.fortschrittKeinRechner,
              case .objekt(let b) = Ipadmappenwege.fortschrittOhneHeim else { return XCTFail() }
        XCTAssertEqual(Set(a.keys), Set(b.keys))
    }

    func testOhneRechnerUndOhneMappeSagtDerMacWasFehlt() throws {
        func satz(_ a: Leitungsantwort) throws -> String? { try JSONWert.lies(a.rumpf)["fehler"]?.alsText }
        let rechnen = Ipadmappenwege.ohneRechner(.rechnen)
        XCTAssertEqual(rechnen.status, 503)
        XCTAssertEqual(try satz(rechnen), Ipadmappenwege.satzKeinRechner)
        XCTAssertEqual(Ipadmappenwege.ohneRechner(nil).status, 503, "was die Mappe nicht kennt")
        XCTAssertEqual(Ipadmappenwege.ohneRechner(.benennen).status, 503)
        let projekt = Ipadmappenwege.ohneRechner(.projekt)
        XCTAssertEqual(projekt.status, 404)
        XCTAssertEqual(try satz(projekt), Ipadmappenwege.satzKeineMappeKeinRechner)
        XCTAssertEqual(Ipadmappenwege.ohneRechner(.bild(name: "a.png")).status, 404)
        // DIE SKIZZE BLEIBT IM PARKFACH, mit Satz (abgewiesen, nicht verloren).
        let skizze = Ipadmappenwege.ohneRechner(.skizze)
        XCTAssertEqual(Sendeergebnis.aus(status: skizze.status, daten: skizze.rumpf),
                       .abgewiesen(grund: Ipadmappenwege.satzOhneMappeOhneRechner, code: 409))
        for s in [Ipadmappenwege.satzKeinRechner, Ipadmappenwege.satzKeineMappeKeinRechner,
                  Ipadmappenwege.satzOhneMappeOhneRechner] {
            XCTAssertFalse(s.contains("ß"), "Schweizer Schreibung")
        }
    }
}
