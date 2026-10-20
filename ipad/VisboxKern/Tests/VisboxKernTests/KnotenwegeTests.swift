import XCTest
import VisboxKern

/// «Visbox eigenständig», Schritt 1 (20.10.2026): Die Knotenansicht kommt aus dem App-Bündel
/// über `visbox://app/knoten/`; ihre Datenwege gehen an den Heim-PC.
final class KnotenwegeTests: XCTestCase {

    // ------------------------------------------------------------- Einstieg und Schema

    func testDerEinstiegIstDerBereichImEigenenSchema() {
        XCTAssertEqual(Knotenwege.einstieg.absoluteString, "\(Knotenwege.schema)://app/knoten/")
        // DERSELBE PFAD WIE AM HEIM-PC: `aufDemVisboxServer` in `mappe.ts` erkennt ihn.
        XCTAssertEqual(Knotenwege.einstieg.path, "/knoten")    // `URL.path` ohne Schrägstrich
        XCTAssertTrue(Knotenwege.istEigen(Knotenwege.einstieg))
    }

    func testFremdeAdressenSindNichtEigen() throws {
        XCTAssertFalse(Knotenwege.istEigen(try XCTUnwrap(URL(string: "https://app/knoten/"))))
        XCTAssertFalse(Knotenwege.istEigen(try XCTUnwrap(URL(string: "\(Knotenwege.schema)://anders/knoten/"))))
        XCTAssertTrue(Knotenwege.istEigen(try XCTUnwrap(URL(string: "\(Knotenwege.schema.uppercased())://APP/knoten/mappe"))))
    }

    /// Relativ aufgelöst landen die Wege der Seite auf denselben Pfaden wie am Heim-PC — das
    /// ist die Voraussetzung dafür, dass die Weiterleitung nichts umschreiben muss.
    func testRelativeWegeDerSeiteLandenAufDenPfadenDesServers() throws {
        let seite = Knotenwege.einstieg
        func pfad(_ relativ: String) throws -> String {
            try XCTUnwrap(URL(string: relativ, relativeTo: seite)).absoluteURL.path
        }
        XCTAssertEqual(try pfad("./mappe"), "/knoten/mappe")
        XCTAssertEqual(try pfad("./modell.glb?ordner=x"), "/knoten/modell.glb")
        XCTAssertEqual(try pfad("./assets/index-abc.js"), "/knoten/assets/index-abc.js")
        XCTAssertEqual(try pfad("/bruecke/jobs"), "/bruecke/jobs")
        let bruecke = try XCTUnwrap(URL(string: "/bruecke", relativeTo: seite)).absoluteString
        XCTAssertEqual(bruecke, "\(Knotenwege.schema)://app/bruecke")
    }

    // ------------------------------------------------------------- wie lange gewartet wird

    /// 20.10.2026: Eine Variante lud das Modell hoch und lief nach 25 s in «nicht erreicht».
    /// Lang (300 s) nur fuer POST auf die zwei Wege mit Modell, alles andere bleibt kurz.
    func testLangeWartezeitNurFuerDieZweiWegeMitModell() {
        XCTAssertEqual(Knotenwege.wartezeit(methode: "POST", pfad: "/bruecke/jobs"), 300)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "post", pfad: "/knoten/modell-laden"), 300)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "POST", pfad: "/bruecke/jobs/"), 300)
        // Abrufe und alle anderen Wege bleiben bei 25 s.
        XCTAssertEqual(Knotenwege.wartezeit(methode: "GET", pfad: "/bruecke/jobs"), 25)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "GET", pfad: "/knoten/modell-laden"), 25)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "POST", pfad: "/bruecke/jobs/vis-1-abcdef/approve"), 25)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "POST", pfad: "/knoten/graph"), 25)
        XCTAssertEqual(Knotenwege.wartezeit(methode: "GET", pfad: "/knoten/modell.glb"), 25)
    }

    func testDieLangeWartezeitLiegtUnterDerGanzenFrist() {
        XCTAssertLessThan(Knotenwege.wartezeitLang, Knotenwege.hoechstensGanz)
        XCTAssertGreaterThan(Knotenwege.wartezeitLang, Knotenwege.wartezeitKurz)
        XCTAssertEqual(Knotenwege.hoechstensGanz, 600)
        // Die Wege mit Modell sind Wege des Heim-PC, keine Dateien des Baus.
        for weg in Knotenwege.wegeMitModell {
            XCTAssertEqual(Knotenwege.ziel(pfad: weg), .heim(pfad: weg))
        }
    }

    // ------------------------------------------------------------- welcher Pfad wohin

    func testDieDatenwegeGehenAnDenHeimPC() {
        for weg in ["/knoten/mappe", "/knoten/graph", "/knoten/modell.glb", "/knoten/skizze",
                    "/knoten/modell-laden", "/knoten/standpunkte"] {
            XCTAssertEqual(Knotenwege.ziel(pfad: weg), .heim(pfad: weg), weg)
        }
        XCTAssertEqual(Knotenwege.datenwege.count, 6)
        // Der Knoten «Kamera» (20.10.2026) fragt mit Parametern — die Frage reist mit.
        let mitFrage = URL(string: "\(Knotenwege.schema)://app/knoten/standpunkte?richtungen=s,sSE&fuellt=0.7")
        XCTAssertEqual(mitFrage.map { Knotenwege.ziel(adresse: $0) }, .heim(pfad: "/knoten/standpunkte"))
    }

    func testDieBrueckeGehtGanzAnDenHeimPC() {
        for weg in ["/bruecke", "/bruecke/health", "/bruecke/jobs", "/bruecke/jobs/j1",
                    "/bruecke/jobs/j1/approve", "/bruecke/jobs/j1/cancel",
                    "/bruecke/jobs/j1/artifacts/bild.png"] {
            XCTAssertEqual(Knotenwege.ziel(pfad: weg), .heim(pfad: weg), weg)
        }
        // Ein Pfad, der nur so anfängt, ist nicht die Brücke.
        guard case .unbekannt = Knotenwege.ziel(pfad: "/brueckenbau") else {
            return XCTFail("/brueckenbau ging durch")
        }
    }

    func testDieTeileDesBausKommenAusDemBuendel() {
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/"),
                       .datei(pfad: "index.html", typ: "text/html; charset=utf-8"))
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/index.html"),
                       .datei(pfad: "index.html", typ: "text/html; charset=utf-8"))
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/assets/index-DA-0ioWD.js"),
                       .datei(pfad: "assets/index-DA-0ioWD.js",
                              typ: "text/javascript; charset=utf-8"))
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/assets/index-x.CSS"),
                       .datei(pfad: "assets/index-x.CSS", typ: "text/css; charset=utf-8"))
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/fonts/lato-latin-400-normal.woff2"),
                       .datei(pfad: "fonts/lato-latin-400-normal.woff2", typ: "font/woff2"))
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten/fonts/Lato-OFL.txt"),
                       .datei(pfad: "fonts/Lato-OFL.txt", typ: "text/plain; charset=utf-8"))
    }

    /// An der ganzen Adresse: Der Schrägstrich am Ende bleibt (sonst leitete `/knoten/` auf
    /// sich selbst um), die Frage kommt kodiert mit.
    func testDieGanzeAdresseBehaeltDenSchraegstrich() throws {
        XCTAssertEqual(Knotenwege.ziel(adresse: Knotenwege.einstieg),
                       .datei(pfad: "index.html", typ: "text/html; charset=utf-8"))
        let mitFrage = try XCTUnwrap(URL(string: "\(Knotenwege.schema)://app/knoten/skizze?name=a%2Bb.png"))
        XCTAssertEqual(Knotenwege.ziel(adresse: mitFrage), .heim(pfad: "/knoten/skizze"))
        XCTAssertEqual(Knotenwege.kodierteFrage(mitFrage), "name=a%2Bb.png")
        XCTAssertNil(Knotenwege.kodierteFrage(Knotenwege.einstieg))
        let ohne = try XCTUnwrap(URL(string: "\(Knotenwege.schema)://app/knoten"))
        XCTAssertEqual(Knotenwege.ziel(adresse: ohne), .umleitung(ziel: "/knoten/"))
        // ENTSCHLUESSELT: ein Leerzeichen im Dateinamen trifft die Datei.
        let leer = try XCTUnwrap(URL(string: "\(Knotenwege.schema)://app/knoten/fonts/A%20B.txt"))
        XCTAssertEqual(Knotenwege.ziel(adresse: leer),
                       .datei(pfad: "fonts/A B.txt", typ: "text/plain; charset=utf-8"))
        // Ein verkleideter Ausbruch bleibt einer.
        let raus = try XCTUnwrap(URL(string: "\(Knotenwege.schema)://app/knoten/%2E%2E/Info.plist"))
        guard case .unbekannt = Knotenwege.ziel(adresse: raus) else {
            return XCTFail("%2E%2E ging durch")
        }
        let fremd = try XCTUnwrap(URL(string: "https://app/knoten/"))
        guard case .unbekannt = Knotenwege.ziel(adresse: fremd) else {
            return XCTFail("fremdes Schema ging durch")
        }
    }

    func testOhneSchraegstrichEineUmleitung() {
        XCTAssertEqual(Knotenwege.ziel(pfad: "/knoten"), .umleitung(ziel: "/knoten/"))
    }

    func testNichtsAusserhalbDesBaus() {
        for weg in ["/knoten/../Info.plist", "/knoten/assets/../../x.js", "/knoten/./index.html",
                    "/knoten//index.html", "/knoten/a\\b.js", "/knoten/BAUSTAND.json",
                    "/knoten/programm", "/knoten/assets/", "/", "/api/projekt", "/index.html",
                    "/knoten/geheim.plist", "/knoten/a.js/b"] {
            guard case .unbekannt(let satz) = Knotenwege.ziel(pfad: weg) else {
                XCTFail("\(weg) ging durch: \(Knotenwege.ziel(pfad: weg))")
                continue
            }
            XCTAssertTrue(satz.hasPrefix("Unbekannter Weg"), satz)
        }
    }

    func testTypenWieAmServer() {
        XCTAssertEqual(Set(Knotenwege.typen.keys),
                       [".html", ".js", ".css", ".woff2", ".svg", ".png", ".txt", ".md"])
        XCTAssertNil(Knotenwege.typ(fuer: "ohne-endung"))
        XCTAssertNil(Knotenwege.typ(fuer: "a.json"))
    }

    // ------------------------------------------------------------- die Anfrage nach Hause

    func testHeimAdresseGleicherPfadAndereBasis() throws {
        let basis = try XCTUnwrap(URL(string: "https://heim.example:8443"))
        XCTAssertEqual(Knotenwege.heimAdresse(pfad: "/knoten/mappe", kodierteFrage: nil,
                                              basis: basis)?.absoluteString,
                       "https://heim.example:8443/knoten/mappe")
        // DIE FRAGE UNVERAENDERT — schon kodiert, ein `+` bleibt `%2B`, ein Leerzeichen `%20`.
        XCTAssertEqual(Knotenwege.heimAdresse(pfad: "/knoten/skizze",
                                              kodierteFrage: "name=a%2Bb%20c.png&ordner=x",
                                              basis: basis)?.absoluteString,
                       "https://heim.example:8443/knoten/skizze?name=a%2Bb%20c.png&ordner=x")
        XCTAssertEqual(Knotenwege.heimAdresse(pfad: "/bruecke/jobs/j1", kodierteFrage: "",
                                              basis: basis)?.absoluteString,
                       "https://heim.example:8443/bruecke/jobs/j1")
    }

    func testHeimAdresseBehaeltDenPfadDerBasis() throws {
        let basis = try XCTUnwrap(URL(string: "https://heim.example/heim/"))
        XCTAssertEqual(Knotenwege.heimAdresse(pfad: "/knoten/graph", kodierteFrage: nil,
                                              basis: basis)?.absoluteString,
                       "https://heim.example/heim/knoten/graph")
    }

    func testNurHttpsOderHttpAlsBasis() throws {
        let fremd = try XCTUnwrap(URL(string: "\(Knotenwege.schema)://app"))
        XCTAssertNil(Knotenwege.heimAdresse(pfad: "/knoten/mappe", kodierteFrage: nil,
                                            basis: fremd))
        let datei = URL(fileURLWithPath: "/tmp")
        XCTAssertNil(Knotenwege.heimAdresse(pfad: "/knoten/mappe", kodierteFrage: nil,
                                            basis: datei))
    }

    func testHinausNurErlaubteKoepfeDazuAnmeldungUndGeraet() {
        let seite = [Kopfzeile("Content-Type", "multipart/form-data; boundary=x"),
                     Kopfzeile("Accept", "*/*"), Kopfzeile("X-Kosmo-Token", "t"),
                     Kopfzeile("Cookie", "a=b"), Kopfzeile("Origin", "\(Knotenwege.schema)://app"),
                     Kopfzeile("Authorization", "Basic ZnJlbWQ="),
                     Kopfzeile("Referer", "\(Knotenwege.schema)://app/knoten/")]
        let anmeldung = Anmeldung(benutzer: "nutzer", kennwort: "geheim")
        let aus = Knotenwege.koepfeFuerHeim(seite: seite, anmeldung: anmeldung)
        XCTAssertEqual(aus.wert("Content-Type"), "multipart/form-data; boundary=x")
        XCTAssertEqual(aus.wert("Accept"), "*/*")
        XCTAssertEqual(aus.wert("X-Kosmo-Token"), "t")
        XCTAssertEqual(aus.wert("Authorization"), anmeldung.kopfzeile)  // die der App
        XCTAssertEqual(aus.filter { $0.name.lowercased() == "authorization" }.count, 1)
        XCTAssertEqual(aus.wert("X-Geraet"), "mac")
        XCTAssertNil(aus.wert("Cookie"))
        XCTAssertNil(aus.wert("Origin"))
        XCTAssertNil(aus.wert("Referer"))
    }

    func testOhneAnmeldungKeinAuthorization() {
        let aus = Knotenwege.koepfeFuerHeim(seite: [Kopfzeile("Authorization", "Basic x")],
                                            anmeldung: nil)
        XCTAssertNil(aus.wert("Authorization"))
        XCTAssertEqual(aus.wert("X-Geraet"), "mac")
    }

    func testZurueckNurErlaubteKoepfeUndNieGemerkt() {
        let heim = [Kopfzeile("Content-Type", "model/gltf-binary"),
                    Kopfzeile("Content-Length", "12"), Kopfzeile("Content-Encoding", "gzip"),
                    Kopfzeile("Set-Cookie", "s=1"), Kopfzeile("WWW-Authenticate", "Basic"),
                    Kopfzeile("Cache-Control", "max-age=600"), Kopfzeile("Retry-After", "3")]
        let aus = Knotenwege.koepfeFuerSeite(heim: heim)
        XCTAssertEqual(aus.wert("Content-Type"), "model/gltf-binary")
        XCTAssertEqual(aus.wert("Retry-After"), "3")
        XCTAssertNil(aus.wert("Content-Length"))
        XCTAssertNil(aus.wert("Content-Encoding"))
        XCTAssertNil(aus.wert("Set-Cookie"))
        XCTAssertNil(aus.wert("WWW-Authenticate"))
        XCTAssertEqual(aus.wert("Cache-Control"), "no-store")
        XCTAssertEqual(aus.filter { $0.name.lowercased() == "cache-control" }.count, 1)
    }

    func testDateiKoepfe() {
        let aus = Knotenwege.koepfeFuerDatei(typ: "font/woff2", laenge: 42)
        XCTAssertEqual(aus.wert("Content-Type"), "font/woff2")
        XCTAssertEqual(aus.wert("Content-Length"), "42")
        XCTAssertEqual(aus.wert("Cache-Control"), "no-store")
    }

    // ------------------------------------------------------------- Fehler als Satz

    func testFehlerInDerFormDesServers() throws {
        let rumpf = Knotenwege.fehlerRumpf(Knotenwege.satzOhneHeim)
        let feld = try XCTUnwrap(try JSONSerialization.jsonObject(with: rumpf) as? [String: String])
        XCTAssertEqual(feld, ["fehler": Knotenwege.satzOhneHeim])
        XCTAssertEqual(Knotenwege.Fehlerart.ohneHeim.rawValue, 503)
        XCTAssertEqual(Knotenwege.Fehlerart.heimNichtErreicht.rawValue, 502)
        XCTAssertEqual(Knotenwege.Fehlerart.unbekannt.rawValue, 404)
    }
}
