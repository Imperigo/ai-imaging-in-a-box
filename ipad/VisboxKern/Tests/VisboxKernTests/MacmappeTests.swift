import XCTest
import VisboxKern

/// «Visbox eigenständig», Schritt 3 (21.10.2026): Die Mappe liegt am Mac; die App beantwortet die
/// Datenwege der Knotenansicht aus ihr, holt Mappen vom Heim-PC und legt Auftragsbilder hinein.
final class MacmappeTests: XCTestCase {

    private func mappe(knoten: JSONWert? = nil, heim: String? = nil) -> Macmappe {
        Macmappe(name: "Demohaus Test", herkunft: .angelegt, angelegt: "2026-10-21T08:00:00Z",
                 heimMappe: heim, knoten: knoten)
    }

    // ------------------------------------------------------------- Format

    func testMappeJsonHinUndZurueck() throws {
        var m = mappe(heim: "Hof")
        m.vermerke(auftrag: "vis-1761030000-abc123")
        m.vermerke(auftrag: "vis-1761030000-abc123")
        m.vermerke(auftrag: "keine-kennung")
        let gelesen = try XCTUnwrap(Macmappe.lies(try m.daten()))
        XCTAssertEqual(gelesen, m)
        XCTAssertEqual(gelesen.auftraege, ["vis-1761030000-abc123"])
        XCTAssertNil(Macmappe.lies(Data(#"{"format":"anders/v1"}"#.utf8)))
    }

    func testDieAuftragslisteBleibtBegrenzt() {
        var m = mappe()
        for i in 0..<(Mappenkern.auftraegeHoechstens + 3) {
            m.vermerke(auftrag: "vis-\(i)-abcdef")
        }
        XCTAssertEqual(m.auftraege.count, Mappenkern.auftraegeHoechstens)
        XCTAssertEqual(m.auftraege.first, "vis-3-abcdef")
    }

    // ------------------------------------------------------------- Namen und Wege

    func testOrdnernamen() {
        XCTAssertEqual(Mappenkern.ordnername(fuer: "Übungsmappe 2"), "Uebungsmappe 2")
        XCTAssertEqual(Mappenkern.ordnername(fuer: "  ../etc/  "), "etc")
        XCTAssertNil(Mappenkern.ordnername(fuer: "..."))
        XCTAssertEqual(Mappenkern.ordnername(fuer: String(repeating: "a", count: 80))?.count, 60)
        XCTAssertEqual(Mappenkern.freierName("Hof", belegt: ["hof", "Hof 2"]), "Hof 3")
        XCTAssertEqual(Mappenkern.freierName("Neu", belegt: ["Hof"]), "Neu")
    }

    func testSichereWege() {
        XCTAssertEqual(Mappenkern.sichererWeg("skizzen/a.png"), "skizzen/a.png")
        for schlecht in ["", "../a.png", "a/../b.png", "/a.png", ".a.png", "a//b.png", "a\\b.png",
                         "projekt.json", "a/.versteckt/b.png"] {
            XCTAssertNil(Mappenkern.sichererWeg(schlecht), schlecht)
        }
        XCTAssertEqual(Mappenkern.skizzenweg("skizze-a.png"), "heim/skizze-a.png")
        XCTAssertNil(Mappenkern.skizzenweg("../x.png"))
    }

    func testAuftragskennungWieAmHeimPC() {
        XCTAssertTrue(Mappenkern.istAuftragskennung("vis-1761030000-abc123"))
        for schlecht in ["vis-1-ABC123", "vis--abc123", "vis-1-abc12", "job-1-abc123", "vis-1-abc123/.."] {
            XCTAssertFalse(Mappenkern.istAuftragskennung(schlecht), schlecht)
        }
        XCTAssertEqual(Mappenkern.auftragsweg("vis-1-abcdef", datei: "a.png"), "bilder/vis-1-abcdef/a.png")
        XCTAssertNil(Mappenkern.auftragsweg("vis-1-abcdef", datei: "../a.png"))
    }

    // ------------------------------------------------------------- Wege der Knotenansicht

    func testWelcheWegeDieMappeAmMacBeantwortet() {
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/knoten/mappe"), .mappe)
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/knoten/graph"), .graphLesen)
        XCTAssertEqual(Mappenkern.ziel(methode: "post", pfad: "/knoten/graph"), .graphSichern)
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/knoten/modell.glb"), .modell)
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/knoten/skizze"), .skizze)
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/knoten/standpunkte"), .standpunkte)
        XCTAssertEqual(Mappenkern.ziel(methode: "POST", pfad: "/knoten/mappe-holen"), .modellHolen)
        // BEFUND auf-20261021-304 B1: «Datei laden …» geht mit dem Namen der Mappe am Mac hinueber.
        XCTAssertEqual(Mappenkern.ziel(methode: "POST", pfad: "/knoten/modell-laden"), .modellLaden)
        XCTAssertEqual(Mappenkern.ziel(methode: "POST", pfad: "/bruecke/jobs"), .auftragAnlegen)
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/bruecke/jobs/vis-1-abcdef"),
                       .auftragLesen("vis-1-abcdef"))
        XCTAssertEqual(Mappenkern.ziel(methode: "GET", pfad: "/bruecke/jobs/vis-1-abcdef/artifacts/k%20a.png"),
                       .auftragsbild("vis-1-abcdef", "k a.png"))
        // WIE BISHER AN DEN HEIM-PC: der Stand des Ladens, Freigeben, Abbrechen, die Liste, die Gesundheit.
        for (m, p) in [("GET", "/knoten/modell-laden"),
                       ("POST", "/bruecke/jobs/vis-1-abcdef/approve"), ("GET", "/bruecke/jobs"),
                       ("GET", "/bruecke/health"), ("GET", "/bruecke/jobs/vis-1-abcdef/artifacts/.x"),
                       ("GET", "/knoten/index.html")] {
            XCTAssertNil(Mappenkern.ziel(methode: m, pfad: p), "\(m) \(p)")
        }
    }

    // ------------------------------------------------------------- Antworten aus der Mappe

    func testDieMappeAntwortetWieDerHeimPC() throws {
        let knoten = JSONWert.objekt([
            "glb": .wahrheit(true), "huellbox_m": .liste([.liste([.ganz(0), .ganz(0), .ganz(0)]),
                                                          .liste([.ganz(8), .ganz(5), .ganz(3)])]),
            "bauteile": .ganz(214), "herkunft": .text("IFC"), "name": .text("alt"),
            "skizzen": .liste([.objekt(["name": .text("a.png")]), .objekt(["name": .text("b.png")])]),
        ])
        let antwort = Mappenkern.knotenAntwort(mappe(knoten: knoten), glbDa: true, skizzenDa: ["b.png"])
        XCTAssertEqual(antwort["name"]?.alsText, "Demohaus Test")
        XCTAssertEqual(antwort["mappe"]?.alsText, "Demohaus Test")
        XCTAssertEqual(antwort["glb"]?.alsWahrheit, true)
        XCTAssertEqual(antwort["bauteile"]?.alsGanz, 214)
        XCTAssertEqual(antwort["skizzen"]?.alsListe?.count, 1)
        XCTAssertEqual(antwort["grund"]?.alsText, "")
    }

    /// Befund «Andere Datei» (0.3.67): Die Seite prüft am Zwilling, ob ein Laden in der Mappe am Mac ankam.
    func testDieAntwortNenntDenZwilling() {
        let mit = Mappenkern.knotenAntwort(mappe(knoten: .objekt(["fassung": .ganz(2)]), heim: "haus-am-hang"),
                                           glbDa: true, skizzenDa: [])
        XCTAssertEqual(mit["heim_mappe"]?.alsText, "haus-am-hang")
        XCTAssertEqual(mit["fassung"]?.alsGanz, 2)
        XCTAssertEqual(Mappenkern.knotenAntwort(mappe(), glbDa: true, skizzenDa: [])["heim_mappe"], .null)
    }

    /// A0063, Befund 7 (Demolauf 31.10.2026): 30 Bauteile und 7,1 m in `mappe.json`, daneben aber
    /// eine neue `modell.glb` mit 38 Teilen. Passt der Fingerabdruck nicht, geht die alte Auskunft
    /// nicht als die des Modells hinaus.
    func testVeralteteAuskunftNachNeuemModell() {
        let knoten = JSONWert.objekt([
            "glb": .wahrheit(true), "bauteile": .ganz(30), "glb_bytes": .ganz(1000),
            "huellbox_m": .liste([.liste([.ganz(0), .ganz(0), .ganz(0)]),
                                  .liste([.ganz(8), .ganz(5), .ganz(7)])]),
            "standpunkte": .objekt(["kameras": .liste([])]),
        ])
        let veraltet = Mappenkern.knotenAntwort(mappe(knoten: knoten), glbDa: true, skizzenDa: [],
                                                glbBytes: 1400)
        XCTAssertEqual(veraltet["bauteile"], .null)
        XCTAssertEqual(veraltet["huellbox_m"], .null)
        XCTAssertEqual(veraltet["standpunkte"], .null)
        XCTAssertEqual(veraltet["auskunft_veraltet"]?.alsWahrheit, true)
        XCTAssertEqual(veraltet["grund"]?.alsText, Mappenkern.satzAuskunftVeraltet("Demohaus Test"))
        // Dieselbe Datei: die Auskunft gilt.
        let gleich = Mappenkern.knotenAntwort(mappe(knoten: knoten), glbDa: true, skizzenDa: [],
                                              glbBytes: 1000)
        XCTAssertEqual(gleich["bauteile"]?.alsGanz, 30)
        XCTAssertNil(gleich["auskunft_veraltet"])
        // Eine Mappe von vorher (ohne Fingerabdruck): wie bisher, nichts wird geraten.
        let alt = Mappenkern.knotenAntwort(mappe(knoten: .objekt(["bauteile": .ganz(30)])), glbDa: true,
                                           skizzenDa: [], glbBytes: 1400)
        XCTAssertEqual(alt["bauteile"]?.alsGanz, 30)
    }

    func testOhneModellDerSatzDesModellKnotens() {
        let antwort = Mappenkern.knotenAntwort(mappe(), glbDa: false, skizzenDa: [])
        XCTAssertEqual(antwort["glb"]?.alsWahrheit, false)
        XCTAssertEqual(antwort["huellbox_m"], .null)
        XCTAssertEqual(antwort["grund"]?.alsText, Mappenkern.satzOhneModell("Demohaus Test"))
        XCTAssertEqual(antwort["skizzen"]?.alsListe, [])
    }

    // ------------------------------------------------------------- der Graph

    func testDerGraphWieAmHeimPC() throws {
        let rumpf = Data(#"{"graphen":[{"kind":"visgraph","id":"g1","nodes":[],"edges":[]}]}"#.utf8)
        let (datei, anzahl) = try Mappenkern.graphDatei(aus: rumpf)
        XCTAssertEqual(anzahl, 1)
        let zurueck = Mappenkern.graphAntwort(datei)
        XCTAssertEqual(zurueck["graphen"]?.alsListe?.first?["id"]?.alsText, "g1")
        XCTAssertEqual(zurueck["satz"], .null)
        XCTAssertEqual(Mappenkern.graphAntwort(nil)["graphen"]?.alsListe, [])
        XCTAssertNotNil(Mappenkern.graphAntwort(Data("kaputt".utf8))["satz"]?.alsText)
    }

    func testEinFremderGraphWirdAbgewiesen() {
        XCTAssertThrowsError(try Mappenkern.graphDatei(aus: Data(#"{"graphen":[{"kind":"wand"}]}"#.utf8))) {
            XCTAssertEqual($0 as? Mappenkern.Graphfehler, .keinRendergraph)
        }
        XCTAssertThrowsError(try Mappenkern.graphDatei(aus: Data(#"{"graphen":{}}"#.utf8))) {
            XCTAssertEqual($0 as? Mappenkern.Graphfehler, .keineListe)
        }
        let gross = Data(repeating: 0x20, count: Mappenkern.graphHoechstens + 1)
        XCTAssertThrowsError(try Mappenkern.graphDatei(aus: gross)) {
            XCTAssertEqual(($0 as? Mappenkern.Graphfehler)?.status, 413)
        }
    }

    // ------------------------------------------------------------- Aufträge

    /// Entscheid 117a (W-4): das Grundbild kommt mit in die Mappe; fehlende Ebene, Pfad und Tiefe nicht.
    func testDasGrundbildKommtMitInDieMappe() {
        let fertig = Data(#"""
        {"status":"done","result":{"images":["K1.png","K2.png"],"ebenen":[
          {"kamera":"K1","art":"schoenbild","datei":"K1__schoenbild.png"},
          {"kamera":"K1","art":"tiefe","datei":"K1__tiefe.png"},
          {"kamera":"K2","art":"schoenbild","datei":null,"grund":"fehlt"},
          {"kamera":"K3","art":"schoenbild","datei":"../x.png"}]}}
        """#.utf8)
        XCTAssertEqual(Mappenkern.fertigeBilder(laufzettel: fertig), ["K1.png", "K2.png", "K1__schoenbild.png"])
    }

    func testDieBilderEinesFertigenAuftrags() {
        let fertig = Data(#"{"job_id":"vis-1-abcdef","status":"done","result":{"images":["k1.png","k2.png"]}}"#.utf8)
        XCTAssertEqual(Mappenkern.fertigeBilder(laufzettel: fertig), ["k1.png", "k2.png"])
        let laeuft = Data(#"{"status":"running"}"#.utf8)
        XCTAssertNil(Mappenkern.fertigeBilder(laufzettel: laeuft))
        let boese = Data(#"{"status":"done","result":{"images":["../x.png"]}}"#.utf8)
        XCTAssertNil(Mappenkern.fertigeBilder(laufzettel: boese))
        XCTAssertEqual(Mappenkern.auftragskennung(aus: Data(#"{"job_id":"vis-9-0a0b0c"}"#.utf8)), "vis-9-0a0b0c")
        XCTAssertNil(Mappenkern.auftragskennung(aus: Data(#"{"job_id":"../x"}"#.utf8)))
    }

    /// Befund N8 (Mac-Demolauf «Haus am Hang», 22.10.2026): Was am Heim-PC fertig ist und am Mac
    /// fehlt, holt die App beim Öffnen der Mappe nach — die jüngsten zuerst; abgebrochene und
    /// vollständige nicht.
    func testWasDerMappeFehltWirdNachgeholt() {
        var m = mappe(heim: "haus-am-hang")
        let ids = ["vis-1-aaaaaa", "vis-2-bbbbbb", "vis-3-cccccc", "vis-4-dddddd", "vis-5-eeeeee"]
        for id in ids { m.vermerke(auftrag: id) }
        let zettel: [String: String] = [
            // vollständig: Bild und Grundbild liegen
            "bilder/vis-1-aaaaaa/job.json": #"{"status":"done","result":{"images":["s.png"]}}"#,
            // fertig, aber nNW fehlt am Mac (der Fund)
            "bilder/vis-2-bbbbbb/job.json": #"{"status":"done","result":{"images":["sSE.png","nNW.png"]}}"#,
            // lief noch, als die Seite neu lud
            "bilder/vis-3-cccccc/job.json": #"{"status":"running"}"#,
            // abgebrochen: da kommt nichts mehr
            "bilder/vis-4-dddddd/job.json": #"{"status":"cancelled"}"#,
            // vis-5: nie gesehen (kein Laufzettel)
        ]
        let liegt: Set<String> = ["bilder/vis-1-aaaaaa/s.png", "bilder/vis-2-bbbbbb/sSE.png"]
        let nach = Mappenkern.nachzuholen(m, zettel: { zettel[$0].map { Data($0.utf8) } },
                                          liegt: { liegt.contains($0) })
        XCTAssertEqual(nach, ["vis-5-eeeeee", "vis-3-cccccc", "vis-2-bbbbbb"])
        XCTAssertEqual(Mappenkern.nachzuholen(m, zettel: { zettel[$0].map { Data($0.utf8) } },
                                              liegt: { liegt.contains($0) }, hoechstens: 1),
                       ["vis-5-eeeeee"])
        XCTAssertEqual(Mappenkern.nachzuholen(mappe(), zettel: { _ in nil }, liegt: { _ in false }), [])
    }

    func testDerAuftragNenntSeineMappe() {
        let koepfe = Mappenkern.auftragskoepfe(mappe(heim: "Übungsmappe 2"))
        XCTAssertEqual(koepfe, [Kopfzeile("X-Mappe-Am-Mac", "Demohaus%20Test"),
                                Kopfzeile("X-Mappe-Heim", "%C3%9Cbungsmappe%202")])
        XCTAssertEqual(Mappenkern.auftragskoepfe(mappe()).count, 1)
    }

    func testDateiLadenNenntSeineMappe() {
        // BEFUND auf-20261021-304 B1: ohne diese Koepfe stellte der Heim-PC seine Mappe fuer alle um.
        XCTAssertEqual(Mappenkern.ladekoepfe(mappe(heim: "Hof")),
                       [Kopfzeile("X-Mappe-Am-Mac", "Demohaus%20Test"), Kopfzeile("X-Mappe-Heim", "Hof")])
        XCTAssertEqual(Mappenkern.ladekoepfe(mappe()), [Kopfzeile("X-Mappe-Am-Mac", "Demohaus%20Test")])
        XCTAssertEqual(Mappenkern.wegModellLaden, "/knoten/modell-laden")
    }

    func testStandpunkteNurMitZwilling() {
        XCTAssertNil(Mappenkern.standpunkteFrage(kodierteFrage: "richtungen=s", heimMappe: nil))
        XCTAssertEqual(Mappenkern.standpunkteFrage(kodierteFrage: "ordner=%2Fx&richtungen=s,n", heimMappe: "Hof"),
                       "richtungen=s,n&mappe=Hof")
        XCTAssertEqual(Mappenkern.standpunkteFrage(kodierteFrage: nil, heimMappe: "Hof"), "mappe=Hof")
    }

    func testDerHolwunschNachDateiLaden() {
        XCTAssertEqual(Mappenkern.holwunsch(Data(#"{"mappe":"Hof 2"}"#.utf8)), "Hof 2")
        XCTAssertNil(Mappenkern.holwunsch(Data(#"{"mappe":"../Hof"}"#.utf8)))
        XCTAssertNil(Mappenkern.holwunsch(Data("{}".utf8)))
    }

    // ------------------------------------------------------------- Mappenpaket

    private let paketText = """
    {"format":"visbox.mappenpaket/v1","mappe":"Hof","name":"Probe Hof",
     "knoten":{"glb":true,"bauteile":3,"skizzen":[{"name":"skizze-a.png"}]},
     "graph":{"graphen":[{"kind":"visgraph","id":"g1","nodes":[],"edges":[]}],"satz":null},
     "projekt":{},
     "dateien":[{"weg":"modell.glb","art":"modell","bytes":100},
                {"weg":"skizze-a.png","art":"skizze","bytes":10},
                {"weg":"bilder/b1.png","art":"bild","bytes":20}]}
    """

    func testDasPaketWirdGelesenUndGeplant() throws {
        let paket = try XCTUnwrap(Mappenpaket.lies(Data(paketText.utf8)))
        XCTAssertEqual(paket.mappe, "Hof")
        XCTAssertEqual(paket.schritte.map(\.ziel), ["modell.glb", "heim/skizze-a.png", "heim/bilder/b1.png"])
        XCTAssertEqual(paket.holplan(vorhanden: ["heim/skizze-a.png": 10]).map(\.weg), ["modell.glb", "bilder/b1.png"])
        XCTAssertEqual(paket.holplan(vorhanden: [:], nurModell: true).map(\.weg), ["modell.glb"])
        XCTAssertNotNil(paket.graphDatei)
        XCTAssertEqual(paket.knotenFuerMappe["glb"]?.alsWahrheit, true)
    }

    func testEinBoeserWegVerwirftDasGanzePaket() {
        let boese = paketText.replacingOccurrences(of: "bilder/b1.png", with: "../b1.png")
        XCTAssertNil(Mappenpaket.lies(Data(boese.utf8)))
        let fremd = paketText.replacingOccurrences(of: "mappenpaket/v1", with: "mappenpaket/v9")
        XCTAssertNil(Mappenpaket.lies(Data(fremd.utf8)))
    }

    func testDieAdressenAmHeimPC() throws {
        let basis = try XCTUnwrap(URL(string: "https://heim.example:8443"))
        XCTAssertEqual(Mappenpaket.listeAdresse(basis: basis)?.absoluteString, "https://heim.example:8443/knoten/mappen")
        XCTAssertEqual(Mappenpaket.dateiAdresse(basis: basis, mappe: "Hof 2", weg: "a/b.png")?.absoluteString,
                       "https://heim.example:8443/knoten/mappe-datei?mappe=Hof%202&weg=a%2Fb.png")
    }

    // ------------------------------------------------------------- die Liste

    func testDieListeAmMacUndNochAmHeimPC() throws {
        let heute = try XCTUnwrap(ISO8601DateFormatter().date(from: "2026-10-21T12:00:00Z"))
        let a = mappe()
        var b = Macmappe(name: "Übungsmappe 1", herkunft: .heim, angelegt: "2026-10-19T08:00:00Z", heimMappe: "Uebung1")
        b.vermerke(auftrag: "vis-1-abcdef")
        let c = Macmappe(name: "Beispielmappe", herkunft: .mitgeliefert, angelegt: "2026-01-01T00:00:00Z")
        let zeilen = Mappenliste.amMac([("Demohaus Test", a), ("Uebungsmappe 1", b), ("Beispielmappe", c)],
                                       offen: "Uebungsmappe 1", heute: heute)
        XCTAssertEqual(zeilen.map(\.name), ["Übungsmappe 1", "Beispielmappe", "Demohaus Test"])
        XCTAssertEqual(zeilen[0].untertitel, "offen · vom Heim-PC geholt · 19.10.2026")
        XCTAssertEqual(zeilen[1].untertitel, "mitgeliefert")
        XCTAssertEqual(zeilen[2].untertitel, "angelegt · heute")
        let heim = [Heimmappe(mappe: "Uebung1", name: "Übungsmappe 1", modell: true, skizzen: 0, bilder: 0),
                    Heimmappe(mappe: "Uebung2", name: "Übungsmappe 2", modell: true, skizzen: 3, bilder: 12)]
        let noch = Mappenliste.nochAmHeim(heim, amMac: [a, b, c])
        XCTAssertEqual(noch.map(\.mappe), ["Uebung2"])
        XCTAssertEqual(noch[0].untertitel, "Modell · 3 Skizzen · 12 Bilder")
    }

    func testDieListeDesHeimPCGanzOderGarNicht() {
        let gut = Data(#"{"format":"visbox.mappenpaket/v1","mappen":[{"mappe":"Hof","name":"Hof","modell":true,"skizzen":1,"bilder":0}]}"#.utf8)
        XCTAssertEqual(Heimmappe.liste(gut)?.count, 1)
        let boese = Data(#"{"format":"visbox.mappenpaket/v1","mappen":[{"mappe":"../x"}]}"#.utf8)
        XCTAssertNil(Heimmappe.liste(boese))
    }

    /// Entscheid 96b am Mac (Demobefund 25.10.2026): Skizze auf dem Grundbild sSW → «bild», nicht «mappe».
    func testStandpunktVomBildUnterDerSkizze() {
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: "bilder/vis-1792842106-6e0b77/sSW__schoenbild.png"), "bild")
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: "bilder/vis-1792842106-6e0b77/nNO__schoenbild.png"), "bild")
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: "bilder/vis-1792842106-6e0b77/ansicht-1__schoenbild.png"), "mappe")
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: "bilder/../sSW__schoenbild.png"), "mappe")
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: "heim/bild-1.png"), "mappe")
        XCTAssertEqual(Mappenkern.standpunktDerSkizze(ueber: nil), "mappe")
    }

    func testDerOrdnerTraegtDenNamenDerMarke() {
        XCTAssertEqual(Mappenkern.wurzelname, Marke.name + "-Mappen")
    }
}
