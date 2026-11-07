import XCTest
import VisboxKern

/// A0063b Runde 2 (07.11.2026): «Modell laden» in eine bestehende Mappe am Mac, der ganze Ablauf
/// `Modelltausch.holeModell` mit eingespeistem Holen (G-A0063b Mangel 2 bis 5), dazu der Nachzug
/// aus der liegenden `modell.glb` (Diagnose vom Mac-Abend, Befunde 1 und 2).
///
/// Alles synthetisch: Häuser aus Scheiben wie `tests/test_modell_ersetzen_mac.py` (30 vorher,
/// 38 nachher), Kennungen und Namen erfunden.
/// (Nicht `@MainActor` als Klasse: die Testsuche unter Linux kann solche Methoden nicht aufrufen;
/// `Modelltausch.holeModell` läuft trotzdem auf dem MainActor, die Proben warten darauf.)
final class ModelltauschAblaufTests: XCTestCase {
    private var ordner: URL!

    override func setUp() async throws {
        ordner = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString, isDirectory: true)
        try FileManager.default.createDirectory(at: ordner, withIntermediateDirectories: true)
        Platte.schreibenScheitert = false
    }

    override func tearDown() async throws { try? FileManager.default.removeItem(at: ordner) }

    // ------------------------------------------------------------------ Bausteine

    /// `mappe.json` im Zwischenordner, wie `Mappenablage` sie liest und schreibt.
    enum Platte: Mappenzugriff {
        nonisolated(unsafe) static var schreibenScheitert = false
        static func lies(_ ordner: URL) -> Macmappe? {
            (try? Data(contentsOf: ordner.appendingPathComponent(Mappenkern.mappendatei))).flatMap(Macmappe.lies)
        }
        static func schreibe(_ mappe: Macmappe, in ordner: URL) throws {
            if schreibenScheitert { throw Mappenfehler(satz: "Platte voll") }
            try mappe.daten().write(to: ordner.appendingPathComponent(Mappenkern.mappendatei), options: .atomic)
        }
    }

    /// Ein Haus aus `teile` Scheiben, Hochachse Y (glTF), First bei `hoehe` — als `.glb` mit JSON-Block.
    static func haus(_ teile: Int, hoehe: Double) -> Data {
        var knoten: [JSONWert] = []
        var netze: [JSONWert] = []
        var zugriffe: [JSONWert] = []
        for i in 0 ..< teile {
            let x = Double(i) * 0.5
            knoten.append(.objekt(["name": .text("Teil_\(i)"), "mesh": .ganz(i)]))
            netze.append(.objekt(["primitives": .liste([.objekt(["attributes": .objekt(["POSITION": .ganz(i)])])])]))
            zugriffe.append(.objekt(["componentType": .ganz(5126), "count": .ganz(8), "type": .text("VEC3"),
                                     "min": .liste([.zahl(x), .zahl(0), .zahl(0)]),
                                     "max": .liste([.zahl(x + 0.4), .zahl(hoehe), .zahl(6)])]))
        }
        let js = JSONWert.objekt(["asset": .objekt(["version": .text("2.0")]), "scene": .ganz(0),
                                  "scenes": .liste([.objekt(["nodes": .liste((0 ..< teile).map { .ganz($0) })])]),
                                  "nodes": .liste(knoten), "meshes": .liste(netze), "accessors": .liste(zugriffe)])
        return glb(js)
    }

    static func glb(_ js: JSONWert) -> Data {
        var block = (try? js.daten()) ?? Data()
        while block.count % 4 != 0 { block.append(0x20) }
        var aus = Data()
        func u32(_ v: UInt32) { withUnsafeBytes(of: v.littleEndian) { aus.append(contentsOf: $0) } }
        u32(0x4654_6C67); u32(2); u32(UInt32(12 + 8 + block.count))
        u32(UInt32(block.count)); u32(0x4E4F_534A)
        aus.append(block)
        return aus
    }

    /// Die Auskunft, wie der Heim-PC sie rechnet (`mappe_fuer_knoten`), mit erfundenem Abdruck.
    static func auskunft(bauteile: Int, first: Double, summe: String?) -> JSONWert {
        var felder: [String: JSONWert] = [
            "glb": .wahrheit(true), "bauteile": .ganz(bauteile), "herkunft": .text("IFC"),
            "huellbox_m": .liste([.liste([.zahl(-9.65), .zahl(-17), .zahl(0)]),
                                  .liste([.zahl(8.3), .zahl(5.3), .zahl(first)])]),
            "standpunkte": .objekt(["n": .objekt(["abstand_m": .zahl(30)])]),
        ]
        if let summe { felder["glb_abdruck"] = .objekt(["art": .text("voll"), "summe": .text(summe)]) }
        return .objekt(felder)
    }

    static func paket(_ kennung: String, knoten: JSONWert, bytes: Int) -> Mappenpaket {
        let wert = JSONWert.objekt([
            "format": .text(Mappenpaket.formatkennung), "mappe": .text(kennung), "name": .text(kennung),
            "knoten": knoten,
            "dateien": .liste([.objekt(["weg": .text("modell.glb"), "art": .text("modell"), "bytes": .ganz(bytes)])]),
        ])
        return Mappenpaket.lies(try! wert.daten())!
    }

    private func nahe(_ box: JSONWert?, _ soll: [[Double]], file: StaticString = #filePath, line: UInt = #line) {
        let ist = box?.alsListe?.map { $0.alsListe?.compactMap(\.alsZahl) ?? [] } ?? []
        XCTAssertEqual(ist.count, 2, "Hüllbox \(String(describing: box))", file: file, line: line)
        for (a, b) in zip(ist.joined(), soll.joined()) {
            XCTAssertEqual(a, b, accuracy: 1e-9, file: file, line: line)
        }
    }

    private var glb: URL { ordner.appendingPathComponent(Mappenkern.modelldatei) }
    private var vorher: URL { ordner.appendingPathComponent(Modelltausch.vorherdatei) }
    private let alt = haus(30, hoehe: 7.1)
    private let neu = haus(38, hoehe: 9.1)

    /// Eine Mappe am Mac mit dem alten Modell (30 Teile, 7,1 m), Zwilling «demohaus-test».
    private func legeAlteMappe() throws {
        try alt.write(to: glb)
        try Platte.schreibe(Macmappe(name: "Demohaus Test", herkunft: .heim, angelegt: "2026-11-01T08:00:00Z",
                                     heimMappe: "demohaus-test",
                                     knoten: Self.auskunft(bauteile: 30, first: 7.1, summe: "alt")), in: ordner)
    }

    /// Der Abdruck der Proben: welches der beiden Häuser liegt.
    private func summe() -> String? {
        guard let d = try? Data(contentsOf: glb) else { return nil }
        return d == neu ? "neu" : d == alt ? "alt" : "anders"
    }

    /// Holt `daten` an den Platz, wie `Mappenholer.lade` (über eine Zwischendatei).
    private func lege(_ daten: Data) throws {
        let zwischen = ordner.appendingPathComponent("zwischen-\(UUID().uuidString)")
        try daten.write(to: zwischen)
        try Modelltausch.lege(zwischen, nach: glb)
    }

    private func lade(_ kennung: String = "haus-am-hang-variante-a", bytes: Int? = nil,
                      holeDateien: @MainActor ([Holschritt], String) async throws -> Void) async throws {
        let knoten = Self.auskunft(bauteile: 38, first: 9.1, summe: "neu")
        try await Modelltausch.holeModell(
            von: kennung, in: ordner, ablage: Platte.self,
            holePaket: { Self.paket(kennung, knoten: knoten, bytes: bytes ?? self.neu.count) },
            holeDateien: holeDateien, summe: { self.summe() })
    }

    // ------------------------------------------------------------------ der Ablauf

    /// Auftrag, Probe: nach «Modell laden» stimmen Bauteilzahl und Hüllbox mit dem neuen Modell —
    /// gelesen über `knotenAntwort`, wie die Knotenansicht sie bekommt.
    func testNachDemLadenStimmenBauteileUndHuellbox() async throws {
        try legeAlteMappe()
        try await lade { _, _ in try self.lege(self.neu) }
        let mappe = try XCTUnwrap(Platte.lies(ordner))
        let antwort = Mappenkern.knotenAntwort(mappe, glbDa: true, skizzenDa: [], glbAbdruck: summe())
        XCTAssertEqual(antwort["bauteile"]?.alsGanz, 38)
        XCTAssertEqual(antwort["huellbox_m"]?.alsListe?[1].alsListe?[2].alsZahl, 9.1)
        XCTAssertNil(antwort["auskunft_veraltet"])
        XCTAssertEqual(try Data(contentsOf: glb), neu)
        XCTAssertEqual(try Data(contentsOf: vorher), alt)
        // BEFUND 3 (gewollt): Der Zwilling ist danach die Mappe am Heim-PC, die das neue Modell trägt;
        // die alte bleibt dort unberührt und steht wieder unter «Noch am Heim-PC».
        XCTAssertEqual(mappe.heimMappe, "haus-am-hang-variante-a")
        let amHeim = [Heimmappe(mappe: "demohaus-test", name: "Demohaus Test", modell: true, skizzen: 0, bilder: 0),
                      Heimmappe(mappe: "haus-am-hang-variante-a", name: "Variante A", modell: true, skizzen: 0, bilder: 0)]
        XCTAssertEqual(Mappenliste.nochAmHeim(amHeim, amMac: [mappe]).map(\.mappe), ["demohaus-test"])
    }

    /// Mangel 3: Bricht das Holen selbst ab (Netz, Status, Verschieben), kommt das alte Modell zurück
    /// und `mappe.json` bleibt beim alten Stand.
    func testBrichtDasHolenAbKommtDasAlteModellZurueck() async throws {
        try legeAlteMappe()
        do {
            try await lade { _, _ in
                try self.neu.prefix(100).write(to: self.glb)
                throw URLError(.networkConnectionLost)
            }
            XCTFail("Ein abgebrochenes Holen meldet einen Fehler.")
        } catch {}
        XCTAssertEqual(try Data(contentsOf: glb), alt)
        XCTAssertEqual(Platte.lies(ordner)?.knoten?["bauteile"]?.alsGanz, 30)
    }

    /// Mangel 3, Glied «Verschieben»: `lege` löscht das liegende Modell nie, bevor das neue an seinem
    /// Platz ist — scheitert es, liegt das alte weiter da.
    func testLegeLaesstDasAlteModellLiegenWennEsScheitert() throws {
        try alt.write(to: glb)
        let fehlt = ordner.appendingPathComponent("gibt-es-nicht")
        XCTAssertThrowsError(try Modelltausch.lege(fehlt, nach: glb))
        XCTAssertEqual(try Data(contentsOf: glb), alt)
    }

    /// Mangel 4: Scheitert das Zurückholen, sagt der Satz es (und wo die Kopie liegt) — nicht nur
    /// «kam nicht ganz an».
    func testScheitertDasZurueckholenSagtDerSatzEs() async throws {
        try legeAlteMappe()
        do {
            try await lade(bytes: neu.count + 1) { _, _ in
                try self.lege(self.neu)
                try FileManager.default.removeItem(at: self.vorher)   // die Kopie ist weg
            }
            XCTFail("Ein Modell falscher Grösse meldet einen Fehler.")
        } catch let fehler as Mappenfehler {
            XCTAssertTrue(fehler.satz.contains("nicht zurück"), fehler.satz)
        }
        XCTAssertEqual(Platte.lies(ordner)?.knoten?["bauteile"]?.alsGanz, 30)
    }

    /// Ohne Kopie (das Zurückholen ging) gibt `zurueck` wahr, ohne Kopie und mit altem Modell falsch.
    func testZurueckMeldetObEsGing() throws {
        try alt.write(to: vorher)
        try neu.write(to: glb)
        XCTAssertTrue(Modelltausch.zurueck(glb: glb, vorher: vorher, warDa: true))
        XCTAssertEqual(try Data(contentsOf: glb), alt)
        try FileManager.default.removeItem(at: vorher)
        try neu.write(to: glb)
        XCTAssertFalse(Modelltausch.zurueck(glb: glb, vorher: vorher, warDa: true))
    }

    /// Mangel 2/Schreiben: Lässt sich `mappe.json` nicht schreiben, kommt das alte Modell zurück.
    func testScheitertMappeJsonKommtDasAlteModellZurueck() async throws {
        try legeAlteMappe()
        Platte.schreibenScheitert = true
        do {
            try await lade { _, _ in try self.lege(self.neu) }
            XCTFail("Eine nicht schreibbare Mappe meldet einen Fehler.")
        } catch {}
        XCTAssertEqual(try Data(contentsOf: glb), alt)
    }

    /// Mangel 5: Ein zweites «Modell laden» in dieselbe Mappe, während das erste noch holt, wird
    /// abgewiesen — sonst überschrieb es die Kopie, und ein Scheitern des ersten holte das falsche
    /// Modell zurück.
    func testZweimalLadenInDieselbeMappeWirdAbgewiesen() async throws {
        try legeAlteMappe()
        var weiter: CheckedContinuation<Void, Never>?
        var wartet = false
        let erstes = Task { @MainActor in
            try await self.lade { _, _ in
                await withCheckedContinuation { c in weiter = c; wartet = true }
                try self.lege(self.neu)
            }
        }
        while !wartet { await Task.yield() }
        do {
            try await lade("andere-variante") { _, _ in try self.lege(Self.haus(5, hoehe: 3)) }
            XCTFail("Das zweite Laden in dieselbe Mappe muss warten oder abgewiesen werden.")
        } catch let fehler as Mappenfehler {
            XCTAssertEqual(fehler.satz, Modelltausch.satzLaeuftSchon)
        }
        weiter?.resume()
        try await erstes.value
        XCTAssertEqual(Platte.lies(ordner)?.heimMappe, "haus-am-hang-variante-a")
        XCTAssertEqual(try Data(contentsOf: glb), neu)
        // Danach ist die Mappe wieder frei.
        try await lade { _, _ in try self.lege(self.neu) }
    }

    // ------------------------------------------------------------------ der Nachzug (Befunde 1, 2)

    /// Befund 1 (Mappe «haus-am-hang»): `modell.glb` von Hand ersetzt (38 Teile, First 9,1 m),
    /// `mappe.json` ohne Abdruck mit 30 Teilen und 7,1 m. Beim Öffnen zieht der Mac nach.
    func testVonHandErsetztesModellWirdNachgezogen() throws {
        let mappe = Macmappe(name: "haus-am-hang", herkunft: .heim, angelegt: "2026-10-22T08:00:00Z",
                             heimMappe: "haus-am-hang", knoten: Self.auskunft(bauteile: 30, first: 7.1, summe: nil))
        let gezogen = try XCTUnwrap(Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "neu",
                                                          groesse: neu.count, kopf: { self.neu }))
        let antwort = Mappenkern.knotenAntwort(gezogen, glbDa: true, skizzenDa: [], glbAbdruck: "neu")
        XCTAssertEqual(antwort["bauteile"]?.alsGanz, 38)
        nahe(antwort["huellbox_m"], [[0, -6, 0], [18.9, 0, 9.1]])
        XCTAssertNil(antwort["auskunft_veraltet"])
        // Die Standpunkte des alten Modells gelten nicht mehr — keine statt falscher.
        XCTAssertEqual(antwort["standpunkte"], .null)
        let satz = try XCTUnwrap(antwort["glb_stand"]?["satz"]?.alsText)
        XCTAssertTrue(satz.contains("nachgezogen") && satz.contains("38"), satz)
        // Der Zwilling am Heim-PC trägt nicht dieses Modell: keine Standpunkte von dort.
        XCTAssertEqual(Modellnachzug.standpunkteGesperrt(gezogen), Modellnachzug.satzStandpunkteNachgezogen)
        XCTAssertNil(Modellnachzug.standpunkteGesperrt(mappe))
        // Ein zweites Öffnen hat nichts mehr nachzuziehen.
        XCTAssertNil(Modellnachzug.gezogen(gezogen, glbDa: true, abdruck: "neu", groesse: neu.count, kopf: { self.neu }))
    }

    /// Ein anderer Abdruck (die Datei wurde nach dem Holen ersetzt) wird ebenso nachgezogen.
    func testAndererAbdruckWirdNachgezogen() throws {
        let mappe = Macmappe(name: "Hof", herkunft: .heim, angelegt: "2026-10-22T08:00:00Z",
                             knoten: Self.auskunft(bauteile: 30, first: 7.1, summe: "alt"))
        let gezogen = try XCTUnwrap(Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "neu",
                                                          groesse: neu.count, kopf: { self.neu }))
        XCTAssertEqual(gezogen.knoten?["bauteile"]?.alsGanz, 38)
        XCTAssertEqual(gezogen.knoten?["glb_abdruck"]?["summe"]?.alsText, "neu")
    }

    /// Befund 2: Vor dem Laden stand «Szene: 0 Bauteile (aus IFC)», obwohl `mappe.json` und Datei
    /// 35 Teile hatten. Ursache: eine Auskunft ohne Abdruck (Mappe von vor 0.3.73) gilt als veraltet,
    /// `bauteile` geht leer hinaus, die Seite macht daraus 0 (`zustandAusMappe`: `?? 0`), die
    /// Herkunft «IFC» bleibt. Passt die Datei (gleiche Teilzahl, gleiche Box), bekommt die Auskunft
    /// nur den Abdruck dazu und behält ihre Standpunkte.
    func testPassendeMappeOhneAbdruckZeigtIhreZahlen() throws {
        let datei = Self.haus(35, hoehe: 5.6)
        var felder = Self.auskunft(bauteile: 35, first: 5.6, summe: nil).alsObjekt!
        felder["huellbox_m"] = .liste([.liste([.zahl(0), .zahl(-6), .zahl(0)]), .liste([.zahl(17.4), .zahl(0), .zahl(5.6)])])
        let mappe = Macmappe(name: "Demohaus Test", herkunft: .heim, angelegt: "2026-10-20T08:00:00Z",
                             knoten: .objekt(felder))
        let vorher = Mappenkern.knotenAntwort(mappe, glbDa: true, skizzenDa: [], glbAbdruck: "d35")
        XCTAssertEqual(vorher["bauteile"], .null)            // das «0» des Knotens
        XCTAssertEqual(vorher["herkunft"]?.alsText, "IFC")   // das «(aus IFC)»
        let gezogen = try XCTUnwrap(Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "d35",
                                                          groesse: datei.count, kopf: { datei }))
        let antwort = Mappenkern.knotenAntwort(gezogen, glbDa: true, skizzenDa: [], glbAbdruck: "d35")
        XCTAssertEqual(antwort["bauteile"]?.alsGanz, 35)
        XCTAssertEqual(antwort["standpunkte"], felder["standpunkte"])
        XCTAssertEqual(antwort["herkunft"]?.alsText, "IFC")
    }

    /// Geht der Nachzug nicht (Datei kein lesbares glb), sagt der Modell-Knoten, warum keine Zahl
    /// steht — der Satz kommt in `glb_stand.satz`, den die Seite zeigt.
    func testOhneLesbareDateiSagtDerKnotenWarum() throws {
        let mappe = Macmappe(name: "Hof", herkunft: .heim, angelegt: "2026-10-22T08:00:00Z",
                             knoten: Self.auskunft(bauteile: 30, first: 7.1, summe: nil))
        XCTAssertNil(Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "x", groesse: 3, kopf: { Data("abc".utf8) }))
        let antwort = Modellnachzug.fuerDieSeite(
            Mappenkern.knotenAntwort(mappe, glbDa: true, skizzenDa: [], glbAbdruck: "x"))
        XCTAssertEqual(antwort["glb_stand"]?["satz"]?.alsText, Mappenkern.satzAuskunftVeraltet("Hof"))
        XCTAssertEqual(antwort["bauteile"], .null)
    }

    /// Ohne Modell oder ohne lesbaren Abdruck gibt es nichts nachzuziehen.
    func testOhneModellNichtsNachzuziehen() {
        let mappe = Macmappe(name: "Hof", herkunft: .angelegt, angelegt: "2026-10-22T08:00:00Z")
        XCTAssertNil(Modellnachzug.gezogen(mappe, glbDa: false, abdruck: nil, groesse: nil, kopf: { nil }))
        XCTAssertNil(Modellnachzug.gezogen(mappe, glbDa: true, abdruck: nil, groesse: 5, kopf: { self.neu }))
    }

    // ------------------------------------------------------------------ der glb-Kopf

    /// Wie `glbbox.knotenboxen` und `nach_welt`: Elternmatrizen werden mitgeführt, Welt = (x, −z, y).
    func testGlbauskunftRechnetWieDerHeimPC() throws {
        let js = JSONWert.objekt([
            "scene": .ganz(0), "scenes": .liste([.objekt(["nodes": .liste([.ganz(0)])])]),
            "nodes": .liste([
                .objekt(["name": .text("Gruppe"), "translation": .liste([.zahl(10), .zahl(1), .zahl(0)]),
                         "children": .liste([.ganz(1)])]),
                .objekt(["name": .text("Wand"), "mesh": .ganz(0), "scale": .liste([.zahl(2), .zahl(1), .zahl(1)])]),
            ]),
            "meshes": .liste([.objekt(["primitives": .liste([.objekt(["attributes": .objekt(["POSITION": .ganz(0)])])])])]),
            "accessors": .liste([.objekt(["min": .liste([.zahl(0), .zahl(0), .zahl(0)]),
                                          "max": .liste([.zahl(1), .zahl(3), .zahl(0.5)])])]),
        ])
        let a = try XCTUnwrap(Glbauskunft.lies(Self.glb(js)))
        XCTAssertEqual(a.bauteile, 1)
        nahe(.liste(a.huellbox.map { .liste($0.map(JSONWert.zahl)) }), [[10, -0.5, 1], [12, 0, 4]])
        // Ein Mesh ohne min/max: keine Auskunft statt einer zu kleinen Box.
        var ohne = js.alsObjekt!
        ohne["accessors"] = .liste([.objekt(["count": .ganz(3)])])
        XCTAssertNil(Glbauskunft.lies(Self.glb(.objekt(ohne))))
        XCTAssertNil(Glbauskunft.lies(Data("kein glb".utf8)))
        // Von der Platte: nur Kopf und JSON-Block.
        try neu.write(to: glb)
        XCTAssertEqual(Glbauskunft.kopf(von: glb).flatMap(Glbauskunft.lies)?.bauteile, 38)
    }
}
