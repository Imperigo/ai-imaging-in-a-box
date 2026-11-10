import XCTest
import VisboxKern

/// A0267 (Geräteprobe 0.3.75, Befund 1): Die Hüllbox, die der Mac aus der liegenden Datei nachzieht,
/// beschreibt das Haus und nicht das Gelände. Die Regel ist die des Heim-PC (`maske.ist_gelaende`,
/// `glbbox.bauwerksbox`), soweit sie aus den Namen im JSON-Kopf lesbar ist.
///
/// **Eine Probendatei für beide Seiten:** `tests/daten/glbbox_gelaenderegel.json` (synthetisch, von
/// `tools/glbbox_proben.py` aus dem Python-Kern erzeugt). Python prüft sie in
/// `tests/test_glbbox_gelaenderegel_gemeinsam.py`, diese Datei prüft dieselben Fälle in Swift. Läuft
/// eine der beiden Rechnungen weg, wird eine der beiden Proben rot.
final class GlbauskunftGelaendeTests: XCTestCase {
    /// Die Toleranz der Probendatei = `Modellnachzug.boxtoleranz`.
    private let toleranz = 0.01

    private func probendatei() throws -> JSONWert {
        // ipad/VisboxKern/Tests/VisboxKernTests/<diese Datei> → Repo-Wurzel ist fünf Pfadteile höher.
        var wurzel = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { wurzel.deleteLastPathComponent() }
        let datei = wurzel.appendingPathComponent("tests/daten/glbbox_gelaenderegel.json")
        return try JSONWert.lies(try Data(contentsOf: datei))
    }

    private func zahlen(_ box: [[Double]]) -> [Double] { Array(box.joined()) }

    private func box(_ wert: JSONWert?) throws -> [[Double]] {
        let zeilen = try XCTUnwrap(wert?.alsListe)
        return zeilen.map { ($0.alsListe ?? []).compactMap(\.alsZahl) }
    }

    func testJederFallDerProbendateiGibtDieBoxDesHeimPC() throws {
        let faelle = try XCTUnwrap(try probendatei()["faelle"]?.alsListe)
        XCTAssertGreaterThanOrEqual(faelle.count, 6)
        for fall in faelle {
            let name = fall["fall"]?.alsText ?? "?"
            let soll = try XCTUnwrap(fall["erwartet"], name)
            let glb = ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"], name))
            let ist = try XCTUnwrap(Glbauskunft.lies(glb), name)
            XCTAssertEqual(ist.bauteile, soll["bauteile"]?.alsGanz, name)
            let sollBox = zahlen(try box(soll["huellbox"]))
            let istBox = zahlen(ist.huellbox)
            XCTAssertEqual(istBox.count, 6, name)
            for (a, b) in zip(istBox, sollBox) {
                XCTAssertEqual(a, b, accuracy: toleranz, "\(name): \(istBox) statt \(sollBox)")
            }
        }
    }

    /// Satz 3 des Auftrags: das Haus am Hang ist nicht mehr 60 × 50 m, sondern 30,5 × 27,7 m.
    func testHausAmHangIstDieHausboxUndNichtDasGelaende() throws {
        let faelle = try XCTUnwrap(try probendatei()["faelle"]?.alsListe)
        let fall = try XCTUnwrap(faelle.first { $0["fall"]?.alsText == "haus-am-hang" })
        let ist = try XCTUnwrap(Glbauskunft.lies(ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"]))))
        let breite = ist.huellbox[1][0] - ist.huellbox[0][0]
        let tiefe = ist.huellbox[1][1] - ist.huellbox[0][1]
        XCTAssertEqual(breite, 30.5, accuracy: toleranz)
        XCTAssertEqual(tiefe, 27.7, accuracy: toleranz)
        XCTAssertEqual(ist.huellbox[1][2], 9.1, accuracy: toleranz)
    }

    /// Dieselbe Entscheidung wie `maske.ist_gelaende`: ganze Muster und Wörter an den Wortgrenzen.
    func testGelaenderegelFolgtDerMaske() {
        for name in ["Gelaende_Hang", "Gelände", "TERRAIN", "IfcSite_1a2b3c", "ifcsite", "boden_platte",
                     "Umgebung - Toposolid", "gelaendeflaeche gewachsen", "Site (Nord)"] {
            XCTAssertTrue(Glbauskunft.istGelaende(name), name)
        }
        for name in ["Wand_Nord", "Geländer_Balkon", "Bodenplatte des 2. OG", "Sitemap", "Terrassendach",
                     "boden_platte_2", ""] {
            XCTAssertFalse(Glbauskunft.istGelaende(name), name)
        }
    }

    /// Satz 2 des Auftrags: ohne Gelände und bei «alles Gelände» bleibt die Szenenbox, mit dem Vermerk
    /// «Gelände nicht abgetrennt», und es gibt nie eine leere Box.
    func testOhneGelaendeUndBeiAllesGelaendeBleibtDieSzenenboxMitVermerk() throws {
        let faelle = try XCTUnwrap(try probendatei()["faelle"]?.alsListe)
        for name in ["ohne-gelaende", "alles-gelaende"] {
            let fall = try XCTUnwrap(faelle.first { $0["fall"]?.alsText == name }, name)
            let mappe = Macmappe(name: "probe", herkunft: .heim, angelegt: "2026-11-10T05:00:00Z",
                                 knoten: .objekt(["glb": .wahrheit(true), "bauteile": .ganz(1)]))
            let glb = ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"]))
            let gezogen = try XCTUnwrap(
                Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "x", groesse: glb.count, kopf: { glb }), name)
            let vermerk = try XCTUnwrap(gezogen.knoten?["huellbox_vermerk"]?.alsText)
            XCTAssertTrue(vermerk.contains("Gelände nicht abgetrennt"), "\(name): \(vermerk)")
            let ist = zahlen(try box(gezogen.knoten?["huellbox_m"]))
            let szene = zahlen(try box(fall["erwartet"]?["szenenbox"]))
            XCTAssertEqual(ist.count, 6, name)
            for (a, b) in zip(ist, szene) { XCTAssertEqual(a, b, accuracy: toleranz, name) }
            XCTAssertTrue(ist[3] > ist[0] && ist[4] > ist[1], "\(name): leere Box \(ist)")
        }
    }

    /// Abgetrennt: der Vermerk sagt es, und der Satz am Modell-Knoten spricht nicht mehr von «ohne
    /// Geländetrennung».
    func testAbgetrenntesGelaendeStehtImVermerk() throws {
        let faelle = try XCTUnwrap(try probendatei()["faelle"]?.alsListe)
        let fall = try XCTUnwrap(faelle.first { $0["fall"]?.alsText == "haus-am-hang" })
        let mappe = Macmappe(name: "probe", herkunft: .heim, angelegt: "2026-11-10T05:00:00Z",
                             knoten: .objekt(["glb": .wahrheit(true), "bauteile": .ganz(1)]))
        let glb = ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"]))
        let gezogen = try XCTUnwrap(
            Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "x", groesse: glb.count, kopf: { glb }))
        let vermerk = try XCTUnwrap(gezogen.knoten?["huellbox_vermerk"]?.alsText)
        XCTAssertFalse(vermerk.contains("nicht abgetrennt"), vermerk)
        XCTAssertTrue(vermerk.contains("abgetrennt"), vermerk)
        let satz = try XCTUnwrap(gezogen.knoten?["glb_stand"]?["satz"]?.alsText)
        XCTAssertFalse(satz.contains("ohne Geländetrennung"), satz)
    }
}
