import XCTest
@testable import VisboxKern

/// A0289 «Gelände an der Form», Runde 2: Zieht der Mac die Hülle eines Modells nach, umfasst sie das
/// Haus und nicht das Grundstück, auch wenn kein Knoten einen Geländenamen trägt. **Schutz des Hauses
/// geht vor Abtrennen:** Kein Bauwerk und kein Bauwerksteil wird als Gelände entfernt.
///
/// **Der Massstab ist der Heim-PC** (`gelaendeform` über `glbbox.bauwerksbox`). Die gemeinsame
/// Probendatei `tests/daten/glbbox_gelaenderegel.json` trägt unter `formfaelle` je Modell die
/// Python-Entscheidung (`erwartet`) und die Wahrheit (`wahrheit`: welche Körper wirklich Gelände
/// sind). Python prüft sie in `tests/test_glbbox_formregel_gemeinsam.py`, diese Datei prüft dieselben
/// Fälle in Swift.
///
/// **Die Zielfunktion** (`testZielfunktion…`): Gleichstand Mac gegen Heim-PC in JEDEM Fall (100 %);
/// in keinem Gegenfall wird etwas abgetrennt; nie eine leere Hülle.
final class GelaendeformTests: XCTestCase {
    /// Die Toleranz der Probendatei = `Modellnachzug.boxtoleranz`.
    private let toleranz = 0.01

    private struct Formfall {
        let name: String
        let gruppe: String
        let familie: String
        let eben: Bool
        let glb: Data
        let erwartet: JSONWert
        let wahrheit: [Int]
    }

    /// Eine glb aus dem JSON-Kopf; mit `binaerblock` wandert Puffer 0 aus dem Kopf (`data:`) in den
    /// Binärblock der glb, wie `tools/glbbox_proben.schreibe_glb` es am Heim-PC tut.
    private static func glb(_ js: JSONWert, binaerblock: Bool) throws -> Data {
        guard binaerblock else { return ModelltauschAblaufTests.glb(js) }
        var felder = try XCTUnwrap(js.alsObjekt)
        var puffer = try XCTUnwrap(felder["buffers"]?.alsListe)
        var erster = try XCTUnwrap(puffer.first?.alsObjekt)
        let uri = try XCTUnwrap(erster["uri"]?.alsText)
        let trenner = try XCTUnwrap(uri.range(of: ";base64,"))
        var roh = try XCTUnwrap(Data(base64Encoded: String(uri[trenner.upperBound...])))
        while roh.count % 4 != 0 { roh.append(0) }
        erster["uri"] = nil
        puffer[0] = .objekt(erster)
        felder["buffers"] = .liste(puffer)
        var block = try JSONWert.objekt(felder).daten()
        while block.count % 4 != 0 { block.append(0x20) }
        var aus = Data()
        func u32(_ v: Int) { withUnsafeBytes(of: UInt32(v).littleEndian) { aus.append(contentsOf: $0) } }
        u32(0x4654_6C67); u32(2); u32(12 + 8 + block.count + 8 + roh.count)
        u32(block.count); u32(0x4E4F_534A)
        aus.append(block)
        u32(roh.count); u32(0x004E_4942)
        aus.append(roh)
        return aus
    }

    private static var geladen: [Formfall]?

    private func formfaelle() throws -> [Formfall] {
        if let schon = Self.geladen { return schon }
        // ipad/VisboxKern/Tests/VisboxKernTests/<diese Datei> → Repo-Wurzel ist fünf Pfadteile höher.
        var wurzel = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { wurzel.deleteLastPathComponent() }
        let datei = wurzel.appendingPathComponent("tests/daten/glbbox_gelaenderegel.json")
        let alles = try JSONWert.lies(try Data(contentsOf: datei))
        let faelle = try XCTUnwrap(alles["formfaelle"]?.alsListe, "formfaelle fehlen in der Probendatei").map { fall in
            let name = fall["fall"]?.alsText ?? "?"
            return Formfall(name: name, gruppe: try XCTUnwrap(fall["gruppe"]?.alsText, name),
                            familie: fall["familie"]?.alsText ?? "",
                            eben: fall["eben"]?.alsWahrheit ?? false,
                            glb: try Self.glb(try XCTUnwrap(fall["glb"], name),
                                              binaerblock: fall["binaerblock"]?.alsWahrheit ?? false),
                            erwartet: try XCTUnwrap(fall["erwartet"], name),
                            wahrheit: (fall["wahrheit"]?["gelaende_stellen"]?.alsListe ?? []).compactMap(\.alsGanz))
        }
        Self.geladen = faelle
        return faelle
    }

    private func zahlen(_ wert: JSONWert?) -> [Double]? {
        guard let zeilen = wert?.alsListe else { return nil }
        let aus = zeilen.flatMap { ($0.alsListe ?? []).compactMap(\.alsZahl) }
        return aus.count == 6 ? aus : nil
    }

    private func nahe(_ a: [Double], _ b: [Double]?) -> Bool {
        guard let b, a.count == b.count else { return false }
        return zip(a, b).allSatisfy { abs($0 - $1) <= toleranz }
    }

    /// Dieselbe Entscheidung, dieselbe Hülle und dieselben Gründe wie der Heim-PC?
    private func stimmt(_ ist: Glbauskunft, mit soll: JSONWert) -> Bool {
        nahe(Array(ist.huellbox.joined()), zahlen(soll["huellbox"]))
            && nahe(Array(ist.szenenbox.joined()), zahlen(soll["szenenbox"]))
            && ist.bauteile == soll["bauteile"]?.alsGanz
            && ist.abgetrennt == soll["abgetrennt"]?.alsWahrheit
            && ist.gelaendeKnoten == soll["gelaendeKnoten"]?.alsGanz
            && ist.entschiedenDurch == soll["entschieden_durch"]?.alsText
            && ist.formUnklar == soll["form_unklar"]?.alsGanz
            && ist.formGruende == (soll["form_gruende"]?.alsListe ?? []).compactMap(\.alsText)
    }

    // MARK: Die gemeinsame Probendatei

    /// Swift entscheidet JEDEN Formfall wie Python: Hülle, Szenenbox, Entscheidung, Zahl der
    /// Gelände-Teile, Zahl und Gründe der unentschiedenen Körper.
    func testJederFormfallWieAmHeimPC() throws {
        let faelle = try formfaelle()
        XCTAssertGreaterThanOrEqual(faelle.filter { $0.gruppe == "gegenfall" }.count, 80, "mindestens 80 Gegenfälle")
        XCTAssertGreaterThanOrEqual(faelle.filter { $0.gruppe == "gelaende" }.count, 40, "mindestens 40 Geländefälle")
        for fall in faelle {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            XCTAssertEqual(ist.bauteile, fall.erwartet["bauteile"]?.alsGanz, fall.name)
            let box = Array(ist.huellbox.joined())
            let soll = try XCTUnwrap(zahlen(fall.erwartet["huellbox"]), fall.name)
            XCTAssertTrue(nahe(box, soll), "\(fall.name): Hülle \(box) statt \(soll)")
            XCTAssertEqual(ist.abgetrennt, fall.erwartet["abgetrennt"]?.alsWahrheit, "\(fall.name): abgetrennt")
            XCTAssertEqual(ist.gelaendeKnoten, fall.erwartet["gelaendeKnoten"]?.alsGanz, "\(fall.name): Gelände-Teile")
            XCTAssertEqual(ist.entschiedenDurch, fall.erwartet["entschieden_durch"]?.alsText, "\(fall.name): entschieden durch")
            XCTAssertTrue(nahe(Array(ist.szenenbox.joined()), zahlen(fall.erwartet["szenenbox"])), "\(fall.name): Szenenbox")
            XCTAssertEqual(ist.formUnklar, fall.erwartet["form_unklar"]?.alsGanz, "\(fall.name): nicht entscheidbar")
            XCTAssertEqual(ist.formGruende, (fall.erwartet["form_gruende"]?.alsListe ?? []).compactMap(\.alsText),
                           "\(fall.name): Gründe")
        }
    }

    /// Die Zielfunktion der Runde 2: Gleichstand 100 %, Gegenfälle ohne Verlust, Gelände abgetrennt.
    func testZielfunktionGleichstandUndSchutzDesHauses() throws {
        let faelle = try formfaelle()
        var gleich: [String: Int] = [:], alle: [String: Int] = [:], abweichend: [String] = []
        var gegenVerloren: [String] = []
        var gelaendeAb = 0, ebenGemeldet = 0, eben = 0
        for fall in faelle {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            alle[fall.gruppe, default: 0] += 1
            if stimmt(ist, mit: fall.erwartet) { gleich[fall.gruppe, default: 0] += 1 } else { abweichend.append(fall.name) }
            if fall.gruppe == "gegenfall",
               ist.abgetrennt || ist.gelaendeKnoten != 0 || !nahe(Array(ist.huellbox.joined()), Array(ist.szenenbox.joined())) {
                gegenVerloren.append(fall.name)
            }
            if fall.gruppe == "gelaende" {
                if fall.eben {
                    eben += 1
                    if !ist.abgetrennt, ist.formUnklar >= 1, Set(ist.formGruende) == [Gelaendeform.Grund.eben] { ebenGemeldet += 1 }
                } else if ist.entschiedenDurch == "form", ist.gelaendeKnoten == fall.wahrheit.count {
                    gelaendeAb += 1
                }
            }
        }
        let summe = alle.values.reduce(0, +), summeGleich = gleich.values.reduce(0, +)
        let gelaende = alle["gelaende", default: 0]
        print("A0289-2 Zielfunktion: Gleichstand Mac gegen Heim-PC \(summeGleich) von \(summe) Formfällen "
            + "(Gegenfälle \(gleich["gegenfall", default: 0]) von \(alle["gegenfall", default: 0]), Gelände "
            + "\(gleich["gelaende", default: 0]) von \(gelaende), Schwellen "
            + "\(gleich["schwelle", default: 0]) von \(alle["schwelle", default: 0]), Namen "
            + "\(gleich["namen", default: 0]) von \(alle["namen", default: 0])); abweichend: \(abweichend.count) "
            + "\(Array(abweichend.prefix(8))). "
            + "Gegenfälle mit Verlust: \(gegenVerloren.count). Gelände: \(gelaendeAb) von \(gelaende) abgetrennt, "
            + "\(ebenGemeldet) von \(eben) ebenen Flächen als nicht entscheidbar gemeldet.")
        XCTAssertEqual(summeGleich, summe, "Gleichstand 100 %, abweichend: \(abweichend.count) \(Array(abweichend.prefix(8)))")
        XCTAssertGreaterThanOrEqual(alle["gegenfall", default: 0], 80)
        XCTAssertEqual(gegenVerloren, [], "in keinem Gegenfall wird ein Bauwerk als Gelände entfernt")
        XCTAssertGreaterThanOrEqual(gelaende, 40)
        XCTAssertEqual(ebenGemeldet, eben, "jede ebene, waagrechte Fläche ist als nicht entscheidbar gemeldet")
        XCTAssertGreaterThanOrEqual(Double(gelaendeAb + ebenGemeldet) / Double(max(gelaende, 1)), 0.8)
        XCTAssertGreaterThanOrEqual(Double(gelaendeAb) / Double(max(gelaende - eben, 1)), 0.8)
        XCTAssertGreaterThanOrEqual(Double(gelaendeAb) / Double(max(gelaende, 1)), 0.8, "streng gezählt: mindestens 80 % abgetrennt")
    }

    /// Die Pflichtfamilien des Gegenlesens: Tiefgarage, Sockel, Halle, Bodenplatte, namenlos. Der
    /// Grundriss der Hülle ist der der Szene, nichts ist abgetrennt.
    func testGegenfaelleBehaltenDieGanzeSzene() throws {
        var familien: [String: Int] = [:]
        for fall in try formfaelle() where fall.gruppe == "gegenfall" {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            familien[fall.familie, default: 0] += 1
            XCTAssertFalse(ist.abgetrennt, fall.name)
            XCTAssertEqual(ist.gelaendeKnoten, 0, fall.name)
            XCTAssertEqual(ist.entschiedenDurch, "keine", fall.name)
            XCTAssertTrue(nahe(Array(ist.huellbox.joined()), Array(ist.szenenbox.joined())), fall.name)
        }
        XCTAssertEqual(familien["tiefgarage"], 20)
        XCTAssertEqual(familien["sockel"], 18)
        XCTAssertEqual(familien["halle"], 25)
        XCTAssertGreaterThanOrEqual(familien["bodenplatte", default: 0], 18)
        XCTAssertGreaterThanOrEqual(familien["namen", default: 0], 9)
    }

    /// Nie eine leere Hülle: sechs endliche Zahlen, keine Kante negativ, der Grundriss nie null.
    func testNieEineLeereHuelle() throws {
        for fall in try formfaelle() {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            let b = Array(ist.huellbox.joined())
            XCTAssertEqual(b.count, 6, fall.name)
            XCTAssertTrue(b.allSatisfy(\.isFinite), "\(fall.name): \(b)")
            XCTAssertTrue(b[3] > b[0] && b[4] > b[1] && b[5] >= b[2], "\(fall.name): leere Hülle \(b)")
        }
    }

    // MARK: Die Regel selbst

    private func flaeche(oben: Double = 3000, geneigt: Double = 3000, wand: Double = 0, tief: Double? = 0,
                         richtungen: Int = 40, streuung: Double = 10) -> Gelaendeform.Oberseite {
        // Die Oberseite liegt überall auf 4 m (für die Fussprobe).
        .init(oben: oben, geneigt: geneigt, wand: wand, tief: tief, richtungen: richtungen, streuungQuer: streuung,
              rasterLo: [-30, -25], rasterHi: [30, 25], raster: [Double](repeating: 4, count: 256))
    }

    /// Die Fragen des Beweises, je an ihrer Schwelle und in ihrer Reihenfolge.
    func testBeweisAnDenSchwellen() {
        let gelaende = Gelaendeform.Koerper(name: "a", lo: [-30, 0, -25], hi: [30, 4, 25])
        let haus = Gelaendeform.Koerper(name: "b", lo: [-6, 2, -5], hi: [6, 14, 5])
        let alle = [gelaende, haus]
        func b(_ f: Gelaendeform.Oberseite?) -> String? { Gelaendeform.beweis(0, alle, f) }
        XCTAssertNil(b(flaeche()), "gross, geneigt, uneben, eine Lage, kein Sockel, nichts darunter")
        XCTAssertEqual(b(nil), Gelaendeform.Grund.nichtLesbar)
        XCTAssertNil(b(flaeche(oben: 1500, geneigt: 1500)), "Deckung genau die Hälfte")
        XCTAssertEqual(b(flaeche(oben: 1499.9, geneigt: 1499.9)), Gelaendeform.Grund.deckung)
        XCTAssertEqual(b(flaeche(oben: 0, geneigt: 0)), Gelaendeform.Grund.deckung)
        XCTAssertNil(b(flaeche(oben: 3750, geneigt: 3750)), "genau 1,25 Lagen")
        XCTAssertEqual(b(flaeche(oben: 3750.1, geneigt: 3750.1)), Gelaendeform.Grund.lagen)
        XCTAssertNil(b(flaeche(geneigt: 1500)), "genau die Hälfte geneigt")
        XCTAssertEqual(b(flaeche(geneigt: 1499.9)), Gelaendeform.Grund.eben)
        XCTAssertEqual(b(flaeche(geneigt: 0)), Gelaendeform.Grund.eben, "eine ebene, waagrechte Platte")
        XCTAssertNil(b(flaeche(richtungen: 6)))
        XCTAssertEqual(b(flaeche(richtungen: 5)), Gelaendeform.Grund.eineEbene)
        XCTAssertNil(b(flaeche(streuung: 1.0)))
        XCTAssertEqual(b(flaeche(streuung: 0.99)), Gelaendeform.Grund.einfachGekruemmt, "eine Tonne fällt nur nach zwei Seiten")
        XCTAssertNil(b(flaeche(wand: 2.0)))
        XCTAssertEqual(b(flaeche(wand: 2.01)), Gelaendeform.Grund.wand)
        XCTAssertNil(b(flaeche(tief: 1.5)))
        XCTAssertEqual(b(flaeche(tief: 1.51)), Gelaendeform.Grund.sockel)
        XCTAssertEqual(b(flaeche(tief: nil)), Gelaendeform.Grund.sockel)
        // Unterbaut: Ein tiefer reichender Körper unterspannt mehr als ein Viertel.
        let keller = Gelaendeform.Koerper(name: "c", lo: [-30, -3, -25], hi: [-15, 0, 25])
        XCTAssertNil(Gelaendeform.beweis(0, [gelaende, haus, keller], flaeche()), "genau ein Viertel")
        let garage = Gelaendeform.Koerper(name: "c", lo: [-30, -3, -25], hi: [-14, 0, 25])
        XCTAssertEqual(Gelaendeform.beweis(0, [gelaende, haus, garage], flaeche()), Gelaendeform.Grund.unterbaut)
        let flach = Gelaendeform.Koerper(name: "c", lo: [-30, -0.1, -25], hi: [30, 0, 25])
        XCTAssertNil(Gelaendeform.beweis(0, [gelaende, haus, flach], flaeche()), "0,1 m tiefer zählt noch nicht")
    }

    /// Die Oberseite aus Dreiecken: waagrecht, geneigt, steil, gespiegelt, Rand und Wand.
    func testOberseiteAusDreiecken() {
        // Ein Quadrat 10 x 10 m, waagrecht, nach oben (gegen den Uhrzeiger von oben gesehen).
        let eben: [Double] = [0, 0, 0, 0, 0, 10, 10, 0, 10, 0, 0, 0, 10, 0, 10, 10, 0, 0]
        let e = Gelaendeform.oberseite(dreiecke: eben, gespiegelt: false)
        XCTAssertEqual(e.oben, 100, accuracy: 1e-9)
        XCTAssertEqual(e.geneigt, 0)
        XCTAssertEqual(e.richtungen, 0)
        XCTAssertEqual(e.tief, 0)
        // Gespiegelt gelesen zeigt dieselbe Fläche nach unten: keine Oberseite.
        XCTAssertEqual(Gelaendeform.oberseite(dreiecke: eben, gespiegelt: true).oben, 0)
        // Dieselbe Fläche mit 10 % Gefälle längs Z: geneigt, eine Richtung.
        let hang: [Double] = [0, 0, 0, 0, 1, 10, 10, 1, 10, 0, 0, 0, 10, 1, 10, 10, 0, 0]
        let h = Gelaendeform.oberseite(dreiecke: hang, gespiegelt: false)
        XCTAssertEqual(h.oben, 100, accuracy: 1e-9)
        XCTAssertEqual(h.geneigt, 100, accuracy: 1e-9)
        XCTAssertEqual(h.richtungen, 1)
        // 3 % Gefälle ist eine Platte im Gefälle, nicht geneigt.
        let gefaelle: [Double] = [0, 0, 0, 0, 0.3, 10, 10, 0.3, 10, 0, 0, 0, 10, 0.3, 10, 10, 0, 0]
        XCTAssertEqual(Gelaendeform.oberseite(dreiecke: gefaelle, gespiegelt: false).geneigt, 0)
        // Eine Wand am Rand zählt nicht, dieselbe Wand im Inneren zählt mit ihrer Höhe.
        let wandAmRand: [Double] = eben + [0, 0, 0, 0, 3, 0, 0, 3, 10]
        XCTAssertEqual(Gelaendeform.oberseite(dreiecke: wandAmRand, gespiegelt: false).wand, 0)
        let wandInnen: [Double] = eben + [5, 0, 0, 5, 3, 0, 5, 3, 10]
        XCTAssertEqual(Gelaendeform.oberseite(dreiecke: wandInnen, gespiegelt: false).wand, 3)
    }

    /// Die Zweitmeinung spricht nur, wenn die Namensregel schweigt, nie für «alles Gelände», nie ohne
    /// lesbare Dreiecke, und sie trennt nach der Stelle.
    func testZweitmeinungSchweigtWoSieSchweigenMuss() {
        let platte = Gelaendeform.Koerper(name: "Mesh", lo: [-30, 0, -25], hi: [30, 4, 25])
        let haus = Gelaendeform.Koerper(name: "Mesh", lo: [-6, 2, -5], hi: [6, 14, 5])
        let gut = flaeche()
        let z = Gelaendeform.zweitmeinung([platte, haus], hatteNamen: false) { $0 == 0 ? gut : nil }
        XCTAssertTrue(z.entscheidet)
        XCTAssertEqual(z.gelaende, [0], "nach der Stelle: das gleichnamige Haus bleibt")
        XCTAssertEqual(z.unklar, 0)
        let mitNamen = Gelaendeform.zweitmeinung([platte, haus], hatteNamen: true) { _ in gut }
        XCTAssertFalse(mitNamen.entscheidet, "die Namensregel bleibt zuständig")
        XCTAssertEqual(mitNamen.gelaende, [0])
        // Gelände trägt: Steht das Hohe DANEBEN, bleibt alles in der Hülle.
        let daneben = Gelaendeform.Koerper(name: "Turm", lo: [40, 0, -5], hi: [50, 60, 5])
        let schale = Gelaendeform.zweitmeinung([platte, daneben], hatteNamen: false) { _ in gut }
        XCTAssertFalse(schale.entscheidet)
        XCTAssertEqual(schale.gelaende, [])
        XCTAssertEqual(schale.gruende, [Gelaendeform.Grund.traegtNicht])
        XCTAssertTrue(Gelaendeform.traegt([0], [platte, haus]))
        XCTAssertFalse(Gelaendeform.traegt([0], [platte, daneben]))
        let mast = Gelaendeform.Koerper(name: "Mast", lo: [0, 0, 0], hi: [0.25, 20, 0.25])
        XCTAssertFalse(Gelaendeform.traegt([0], [platte, mast]), "ein Mast ist kein Haus")
        let halb = Gelaendeform.Koerper(name: "Haus", lo: [24, 0, -5], hi: [36, 20, 5])
        XCTAssertTrue(Gelaendeform.traegt([0], [platte, halb]), "genau die Hälfte steht darauf")
        // Die Fussprobe: Ein Turm, der am Boden beginnt und durch eine 6 m hohe Schale stösst, steht nicht darauf.
        let kuppel = Gelaendeform.Oberseite(oben: 3000, geneigt: 3000, wand: 0, tief: 0, richtungen: 40,
                                            rasterLo: [-30, -25], rasterHi: [30, 25],
                                            raster: [Double](repeating: 6, count: 256))
        let turmInnen = Gelaendeform.Koerper(name: "Turm", lo: [-5, 0, -5], hi: [5, 60, 5])
        XCTAssertFalse(Gelaendeform.traegt([0], [platte, turmInnen], flaechen: [0: kuppel]), "6 m unter der Fläche")
        let aufgesetzt = Gelaendeform.Koerper(name: "Haus", lo: [-5, 2.5, -5], hi: [5, 60, 5])
        XCTAssertTrue(Gelaendeform.traegt([0], [platte, aufgesetzt], flaechen: [0: kuppel]), "genau 3,5 m darunter")
        XCTAssertEqual(kuppel.oberkante(x0: 0, x1: 1, z0: 0, z1: 1), 6)
        XCTAssertNil(kuppel.oberkante(x0: 40, x1: 50, z0: 0, z1: 1), "daneben liegt keine Oberseite")
        let stumm = Gelaendeform.zweitmeinung([platte, haus], hatteNamen: false) { _ in nil }
        XCTAssertFalse(stumm.entscheidet, "ohne lesbare Dreiecke wird nichts abgetrennt")
        XCTAssertEqual(stumm.gruende, [Gelaendeform.Grund.nichtLesbar])
        // Zwei gleiche Körper, sonst nichts: Beide sind das Höchste der Szene, keiner wird Gelände.
        // «Alles wäre Gelände» kann so nicht mehr eintreten; die Abfrage bleibt als Sicherung.
        let zwei = Gelaendeform.Koerper(name: "x", lo: [-30, 0, -25], hi: [30, 4, 25])
        let beide = Gelaendeform.zweitmeinung([platte, zwei], hatteNamen: false) { _ in gut }
        XCTAssertEqual(beide.gelaende, [])
        XCTAssertEqual(beide.gruende, [Gelaendeform.Grund.zuHoch, Gelaendeform.Grund.zuHoch])
        XCTAssertFalse(beide.entscheidet)
        // Zu hoch: Der Beweis gelänge, aber die Oberkante sitzt über 70 % der Szenenhöhe.
        let niedrig = Gelaendeform.Koerper(name: "b", lo: [-6, 0, -5], hi: [6, 5, 5])
        let hoch = Gelaendeform.zweitmeinung([platte, niedrig], hatteNamen: false) { _ in gut }
        XCTAssertFalse(hoch.entscheidet)
        XCTAssertEqual(hoch.gruende, [Gelaendeform.Grund.zuHoch])
        // Eine Szene ohne Höhe oder ohne Grundfläche: keine Auskunft.
        let scheibe = Gelaendeform.Koerper(name: "c", lo: [0, 0, 0], hi: [10, 0, 10])
        XCTAssertNil(Gelaendeform.merkmale(scheibe, in: [scheibe]))
        XCTAssertEqual(Gelaendeform.zweitmeinung([scheibe], hatteNamen: false) { _ in gut }, .schweigt)
        XCTAssertEqual(Gelaendeform.zweitmeinung([], hatteNamen: false) { _ in gut }, .schweigt)
    }

    func testMerkmaleRechnenGegenDieSzene() throws {
        let platte = Gelaendeform.Koerper(name: "a", lo: [-30, -0.5, -25], hi: [30, 0, 25])
        let haus = Gelaendeform.Koerper(name: "b", lo: [-6, 0, -5], hi: [6, 9, 5])
        let m = try XCTUnwrap(Gelaendeform.merkmale(platte, in: [platte, haus]))
        XCTAssertEqual(m.grundrissanteil, 1.0, accuracy: 1e-12)
        XCTAssertEqual(m.flachheit, 0.01, accuracy: 1e-12)
        XCTAssertEqual(m.tieflage, 0.5 / 9.5, accuracy: 1e-12)
        let h = try XCTUnwrap(Gelaendeform.merkmale(haus, in: [platte, haus]))
        XCTAssertEqual(h.grundrissanteil, 120.0 / 3000.0, accuracy: 1e-12)
        XCTAssertEqual(h.flachheit, 0.9, accuracy: 1e-12)
        XCTAssertEqual(h.tieflage, 1.0, accuracy: 1e-12)
    }

    // MARK: Was nicht lesbar ist, wird nicht geraten

    private func fall(_ name: String) throws -> Formfall {
        try XCTUnwrap(try formfaelle().first { $0.name == name }, name)
    }

    /// Fehlt der Binärblock (nur Kopf und JSON-Block gereicht, wie vor Runde 2), sind die Dreiecke
    /// nicht lesbar: Die Form trennt nichts ab, die Hülle bleibt die Szene.
    func testOhneBinaerblockBleibtDieSzenenhuelle() throws {
        let f = try fall("gelaende-speicher-binaerblock-1")
        let ganz = try XCTUnwrap(Glbauskunft.lies(f.glb))
        XCTAssertEqual(ganz.entschiedenDurch, "form")
        let b = [UInt8](f.glb.prefix(20))
        let laenge = Int(b[12]) | Int(b[13]) << 8 | Int(b[14]) << 16 | Int(b[15]) << 24
        let nurKopf = try XCTUnwrap(Glbauskunft.lies(f.glb.prefix(20 + laenge)))
        XCTAssertEqual(nurKopf.entschiedenDurch, "keine")
        XCTAssertFalse(nurKopf.abgetrennt)
        XCTAssertEqual(nurKopf.formGruende, [Gelaendeform.Grund.nichtLesbar])
        XCTAssertEqual(nurKopf.huellbox, nurKopf.szenenbox)
        // Ein abgeschnittener Binärblock ist ebenso nicht lesbar.
        let gekappt = try XCTUnwrap(Glbauskunft.lies(f.glb.prefix(20 + laenge + 8 + 40)))
        XCTAssertEqual(gekappt.entschiedenDurch, "keine")
        XCTAssertEqual(gekappt.formGruende, [Gelaendeform.Grund.nichtLesbar])
    }

    /// `kopf(von:)` reicht die Datei so, dass die Zweitmeinung die Dreiecke im Binärblock findet.
    func testKopfVonDerPlatteTraegtDenBinaerblock() throws {
        let f = try fall("gelaende-speicher-binaerblock-2")
        let ort = FileManager.default.temporaryDirectory.appendingPathComponent("a0289-\(UUID().uuidString).glb")
        try f.glb.write(to: ort)
        defer { try? FileManager.default.removeItem(at: ort) }
        let daten = try XCTUnwrap(Glbauskunft.kopf(von: ort))
        let ist = try XCTUnwrap(Glbauskunft.lies(daten))
        XCTAssertTrue(stimmt(ist, mit: f.erwartet))
        XCTAssertEqual(ist.entschiedenDurch, "form")
        XCTAssertNil(Glbauskunft.kopf(von: ort.appendingPathExtension("fehlt")))
    }

    // MARK: Was der Mensch liest

    private func gezogen(_ name: String) throws -> (JSONWert, Formfall) {
        let f = try fall(name)
        let mappe = Macmappe(name: "probe", herkunft: .heim, angelegt: "2026-11-10T10:00:00Z",
                             knoten: .objekt(["glb": .wahrheit(true), "bauteile": .ganz(1)]))
        let neu = try XCTUnwrap(
            Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "x", groesse: f.glb.count, kopf: { f.glb }), name)
        return (try XCTUnwrap(neu.knoten, name), f)
    }

    /// An der Form abgetrennt: Vermerk und Satz am Modell-Knoten sagen es, und die Mappe trägt die Hausbox.
    func testAnDerFormAbgetrenntStehtInVermerkUndSatz() throws {
        let (knoten, f) = try gezogen("gelaende-hang-10-prozent-laengs-x-flaeche")
        let vermerk = try XCTUnwrap(knoten["huellbox_vermerk"]?.alsText)
        XCTAssertTrue(vermerk.contains("an der Form abgetrennt"), vermerk)
        XCTAssertFalse(vermerk.contains("nicht abgetrennt"), vermerk)
        let satz = try XCTUnwrap(knoten["glb_stand"]?["satz"]?.alsText)
        XCTAssertTrue(satz.contains("das Gelände ist an der Form abgetrennt"), satz)
        XCTAssertFalse(satz.contains("ohne Geländetrennung"), satz)
        let box = try XCTUnwrap(zahlen(knoten["huellbox_m"]))
        XCTAssertTrue(nahe(box, zahlen(f.erwartet["huellbox"])), "\(box)")
        XCTAssertEqual(box[3] - box[0], 12, accuracy: toleranz)
        XCTAssertEqual(box[4] - box[1], 10, accuracy: toleranz)
    }

    /// Nicht entscheidbar bleibt die Szenenhülle mit Vermerk und Grund: die ebene Platte, die Halle mit
    /// Kamin, die Tiefgarage, der Körper ohne lesbare Dreiecke.
    func testNichtEntscheidbarBleibtDieSzenenhuelleMitVermerk() throws {
        for (name, wort) in [("gelaende-eben-waagrecht-1", "eben und waagrecht"),
                             ("gegen-halle-06-m-kamin", "eben und waagrecht"),
                             ("gegen-tiefgarage-03-geschosse-1-ug", "eben und waagrecht"),
                             ("gegen-namenlos-platte-unter-haus", "eben und waagrecht"),
                             ("gegen-rampe-12-prozent", "eine geneigte Ebene"),
                             ("gegen-schale-auf-dem-boden-6-m-neben-turm", "steht nicht darauf"),
                             ("gegen-koerper-ohne-lesbare-dreiecke", "Dreiecke nicht lesbar"),
                             ("gegen-gelaende-und-haus-in-einem-netz-60-x-50", "eine Wand im Inneren")] {
            let (knoten, f) = try gezogen(name)
            let vermerk = try XCTUnwrap(knoten["huellbox_vermerk"]?.alsText, name)
            XCTAssertTrue(vermerk.contains("Gelände nicht abgetrennt"), "\(name): \(vermerk)")
            XCTAssertTrue(vermerk.contains("nicht entscheidbar"), "\(name): \(vermerk)")
            XCTAssertTrue(vermerk.contains(wort), "\(name): \(vermerk)")
            let satz = try XCTUnwrap(knoten["glb_stand"]?["satz"]?.alsText, name)
            XCTAssertTrue(satz.contains("ohne Geländetrennung"), "\(name): \(satz)")
            XCTAssertTrue(nahe(try XCTUnwrap(zahlen(knoten["huellbox_m"]), name), zahlen(f.erwartet["szenenbox"])), name)
        }
    }

    /// Die Namensfälle der Probendatei (A0267) tragen die Auskunft, welche Regel entschieden hat.
    func testNamensfaelleNennenDieRegel() throws {
        var wurzel = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { wurzel.deleteLastPathComponent() }
        let alles = try JSONWert.lies(try Data(contentsOf: wurzel.appendingPathComponent("tests/daten/glbbox_gelaenderegel.json")))
        for fall in try XCTUnwrap(alles["faelle"]?.alsListe) {
            let name = fall["fall"]?.alsText ?? "?"
            let ist = try XCTUnwrap(Glbauskunft.lies(ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"], name))), name)
            XCTAssertEqual(ist.entschiedenDurch, fall["erwartet"]?["entschieden_durch"]?.alsText, name)
            XCTAssertNotEqual(ist.entschiedenDurch, "form", name)
        }
    }
}
