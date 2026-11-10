import XCTest
import VisboxKern

/// A0289 «Gelände an der Form»: Zieht der Mac die Hülle eines Modells nach, umfasst sie das Haus und
/// nicht das Grundstück, auch wenn kein Knoten einen Geländenamen trägt.
///
/// **Der Massstab ist der Heim-PC** (`gelaendeform` über `glbbox.bauwerksbox`). Die gemeinsame
/// Probendatei `tests/daten/glbbox_gelaenderegel.json` trägt unter `formfaelle` je Modell die
/// Python-Entscheidung (`erwartet`) und, was der Mac liefern muss (`mac`). Python prüft sie in
/// `tests/test_glbbox_formregel_gemeinsam.py`, diese Datei prüft dieselben Fälle in Swift.
///
/// **Die Zielfunktion** (`testZielfunktion…`): Anteil der Formfälle, in denen der Mac dieselbe
/// Entscheidung und dieselbe Hülle liefert wie der Heim-PC, mindestens 90 %; bei den Gegenfällen
/// 100 %; nie eine leere Hülle. Abweichen darf der Mac nur zu «nicht entscheidbar», nie umgekehrt.
final class GelaendeformTests: XCTestCase {
    /// Die Toleranz der Probendatei = `Modellnachzug.boxtoleranz`.
    private let toleranz = 0.01

    private struct Formfall {
        let name: String
        let gruppe: String
        let glb: Data
        let erwartet: JSONWert
        let mac: JSONWert
    }

    private func formfaelle() throws -> [Formfall] {
        // ipad/VisboxKern/Tests/VisboxKernTests/<diese Datei> → Repo-Wurzel ist fünf Pfadteile höher.
        var wurzel = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { wurzel.deleteLastPathComponent() }
        let datei = wurzel.appendingPathComponent("tests/daten/glbbox_gelaenderegel.json")
        let alles = try JSONWert.lies(try Data(contentsOf: datei))
        return try XCTUnwrap(alles["formfaelle"]?.alsListe, "formfaelle fehlen in der Probendatei").map { fall in
            let name = fall["fall"]?.alsText ?? "?"
            return Formfall(name: name, gruppe: try XCTUnwrap(fall["gruppe"]?.alsText, name),
                            glb: ModelltauschAblaufTests.glb(try XCTUnwrap(fall["glb"], name)),
                            erwartet: try XCTUnwrap(fall["erwartet"], name), mac: try XCTUnwrap(fall["mac"], name))
        }
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

    /// Dieselbe Entscheidung und dieselbe Hülle wie in `soll` (`erwartet` oder `mac` eines Falls)?
    private func stimmt(_ ist: Glbauskunft, mit soll: JSONWert) -> Bool {
        nahe(Array(ist.huellbox.joined()), zahlen(soll["huellbox"]))
            && ist.abgetrennt == soll["abgetrennt"]?.alsWahrheit
            && ist.gelaendeKnoten == soll["gelaendeKnoten"]?.alsGanz
            && ist.entschiedenDurch == soll["entschieden_durch"]?.alsText
    }

    // MARK: Die gemeinsame Probendatei

    /// Fertig-Satz 2: Swift entscheidet die Formfälle wie Python. Je Fall steht eine Zeile im Protokoll.
    func testJederFormfallLiefertWasDerMacLiefernMuss() throws {
        let faelle = try formfaelle()
        XCTAssertGreaterThanOrEqual(faelle.filter { $0.gruppe == "form" }.count, 20, "mindestens 20 Formfälle")
        for fall in faelle {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            XCTAssertEqual(ist.bauteile, fall.erwartet["bauteile"]?.alsGanz, fall.name)
            let box = Array(ist.huellbox.joined())
            let soll = try XCTUnwrap(zahlen(fall.mac["huellbox"]), fall.name)
            XCTAssertTrue(nahe(box, soll), "\(fall.name): Hülle \(box) statt \(soll)")
            XCTAssertEqual(ist.abgetrennt, fall.mac["abgetrennt"]?.alsWahrheit, "\(fall.name): abgetrennt")
            XCTAssertEqual(ist.gelaendeKnoten, fall.mac["gelaendeKnoten"]?.alsGanz, "\(fall.name): Gelände-Teile")
            XCTAssertEqual(ist.entschiedenDurch, fall.mac["entschieden_durch"]?.alsText, "\(fall.name): entschieden durch")
            XCTAssertTrue(nahe(Array(ist.szenenbox.joined()), zahlen(fall.erwartet["szenenbox"])), "\(fall.name): Szenenbox")
            // Wie viele Körper «nicht entscheidbar» blieben, zählt der Mac wie der Heim-PC.
            XCTAssertEqual(ist.formUnklar, fall.erwartet["form_unklar"]?.alsGanz, "\(fall.name): nicht entscheidbar")
            print("A0289 Formfall \(fall.name) [\(fall.gruppe)]: \(ist.entschiedenDurch), "
                + "\(ist.abgetrennt ? "abgetrennt" : "Szenenhülle"), \(stimmt(ist, mit: fall.mac) ? "wie verlangt" : "ANDERS")")
        }
    }

    /// Fertig-Satz 3, die Zielfunktion: Gleichstand mit dem Heim-PC, gemessen gegen `erwartet`.
    func testZielfunktionGleichstandMitDemHeimPC() throws {
        let faelle = try formfaelle()
        var gleich: [String: Int] = [:], alle: [String: Int] = [:], abweichend: [String] = []
        for fall in faelle {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            alle[fall.gruppe, default: 0] += 1
            if stimmt(ist, mit: fall.erwartet) {
                gleich[fall.gruppe, default: 0] += 1
            } else {
                abweichend.append(fall.name)
                // NUR «NICHT ENTSCHEIDBAR» STATT EINER ENTSCHEIDUNG, NIE UMGEKEHRT: Wo der Mac abweicht,
                // hat der Heim-PC an der Form entschieden, der Mac behält die Szenenhülle, und der Fall
                // ist in der Probendatei einzeln benannt und begründet.
                XCTAssertEqual(fall.erwartet["entschieden_durch"]?.alsText, "form", fall.name)
                XCTAssertFalse(ist.abgetrennt, "\(fall.name): der Mac trennt, wo der Heim-PC anders entscheidet")
                XCTAssertEqual(ist.entschiedenDurch, "keine", fall.name)
                XCTAssertTrue(nahe(Array(ist.huellbox.joined()), zahlen(fall.erwartet["szenenbox"])), fall.name)
                XCTAssertEqual(fall.mac["gleich"]?.alsWahrheit, false, "\(fall.name): Abweichung nicht benannt")
                XCTAssertEqual(fall.mac["urteil"]?.alsText, "nicht entscheidbar", fall.name)
                XCTAssertFalse((fall.mac["grund"]?.alsText ?? "").isEmpty, "\(fall.name): Abweichung nicht begründet")
            }
            // Der Mac entscheidet nie an der Form, wo der Heim-PC es nicht tut.
            if ist.entschiedenDurch == "form" {
                XCTAssertEqual(fall.erwartet["entschieden_durch"]?.alsText, "form", fall.name)
            }
        }
        let form = Double(gleich["form", default: 0]) / Double(max(alle["form", default: 0], 1))
        print("A0289 Zielfunktion: Gleichstand Mac gegen Heim-PC \(gleich["form", default: 0]) von "
            + "\(alle["form", default: 0]) Formfällen (\(Int((form * 100).rounded())) %), Gegenfälle "
            + "\(gleich["gegenfall", default: 0]) von \(alle["gegenfall", default: 0]), Befunde "
            + "\(gleich["befund", default: 0]) von \(alle["befund", default: 0]); abweichend: \(abweichend)")
        XCTAssertGreaterThanOrEqual(alle["form", default: 0], 20)
        XCTAssertGreaterThanOrEqual(form, 0.9, "Ziel: mindestens 90 % Gleichstand, abweichend: \(abweichend)")
        XCTAssertGreaterThanOrEqual(alle["gegenfall", default: 0], 5)
        XCTAssertEqual(gleich["gegenfall", default: 0], alle["gegenfall", default: 0], "Gegenfälle: 100 %")
    }

    /// Gegenfälle (kein Gelände, Tiefgaragendecke, Flachdach): Der Grundriss der Hülle ist der der Szene,
    /// kein Haus wird als Gelände entfernt.
    func testGegenfaelleVerlierenNichtsVomGrundriss() throws {
        for fall in try formfaelle() where fall.gruppe == "gegenfall" {
            let ist = try XCTUnwrap(Glbauskunft.lies(fall.glb), fall.name)
            XCTAssertFalse(ist.abgetrennt, fall.name)
            XCTAssertEqual(ist.gelaendeKnoten, 0, fall.name)
            XCTAssertTrue(nahe(Array(ist.huellbox.joined()), Array(ist.szenenbox.joined())), fall.name)
        }
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

    /// Die Schwellen, in der Reihenfolge der Fragen: Grösse, Flachheit, Lage.
    func testUrteilAnDenSchwellen() {
        func u(_ g: Double, _ f: Double, _ t: Double) -> Gelaendeform.Urteil {
            Gelaendeform.urteil(.init(grundrissanteil: g, flachheit: f, tieflage: t))
        }
        XCTAssertEqual(u(0.25, 0.15, 0.35), .gelaende, "alle drei genau an der Schwelle")
        XCTAssertEqual(u(0.2499, 0.01, 0.0), .bauwerk, "zu klein")
        XCTAssertEqual(u(0.9, 0.1501, 0.0), .bauwerk, "ragt auf")
        XCTAssertEqual(u(0.9, 0.05, 0.3501), .nichtEntscheidbar, "gross und flach, aber zu hoch")
        XCTAssertEqual(u(0.9, 0.05, 0.60), .nichtEntscheidbar, "genau an der oberen Schwelle")
        XCTAssertEqual(u(0.9, 0.05, 0.6001), .bauwerk, "ein Dach oder eine Decke")
        XCTAssertEqual(Gelaendeform.Urteil.nichtEntscheidbar.rawValue, "nicht entscheidbar")
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
        XCTAssertEqual(Gelaendeform.urteile([platte, haus]), [.gelaende, .bauwerk])
        // Eine Szene ohne Höhe oder ohne Grundfläche: keine Auskunft, kein Vorgabewert.
        let flach = Gelaendeform.Koerper(name: "c", lo: [0, 0, 0], hi: [10, 0, 10])
        XCTAssertNil(Gelaendeform.merkmale(flach, in: [flach]))
        XCTAssertNil(Gelaendeform.urteile([flach]))
        XCTAssertNil(Gelaendeform.urteile([]))
        XCTAssertFalse(Gelaendeform.zweitmeinung([flach], hatteNamen: false).entscheidet)
    }

    /// Die Zweitmeinung spricht nur, wenn die Namensregel schweigt, nie für «alles Gelände», und bei
    /// Namensgleichheit sagt sie «nicht entscheidbar».
    func testZweitmeinungSchweigtWoSieSchweigenMuss() {
        let platte = Gelaendeform.Koerper(name: "Platte", lo: [-30, -0.5, -25], hi: [30, 0, 25])
        let haus = Gelaendeform.Koerper(name: "Haus", lo: [-6, 0, -5], hi: [6, 9, 5])
        let z = Gelaendeform.zweitmeinung([platte, haus], hatteNamen: false)
        XCTAssertTrue(z.entscheidet)
        XCTAssertEqual(z.gelaende, [0])
        XCTAssertFalse(z.namensgleich)
        let mitNamen = Gelaendeform.zweitmeinung([platte, haus], hatteNamen: true)
        XCTAssertFalse(mitNamen.entscheidet, "die Namensregel bleibt zuständig")
        XCTAssertEqual(mitNamen.gelaende, [0])
        let gleich = Gelaendeform.Koerper(name: "Platte", lo: [-6, 0, -5], hi: [6, 9, 5])
        let n = Gelaendeform.zweitmeinung([platte, gleich], hatteNamen: false)
        XCTAssertFalse(n.entscheidet)
        XCTAssertTrue(n.namensgleich)
        // Zwei Gelände-Platten mit demselben Namen sind keine Namensgleichheit mit einem Bauteil.
        let p2 = Gelaendeform.Koerper(name: "Platte", lo: [30, -0.5, -25], hi: [90, 0, 25])
        let zwei = Gelaendeform.zweitmeinung([platte, p2, haus], hatteNamen: false)
        XCTAssertTrue(zwei.entscheidet)
        XCTAssertEqual(zwei.gelaende, [0, 1])
    }

    // MARK: Was der Mensch liest

    private func gezogen(_ name: String) throws -> (JSONWert, Formfall) {
        let fall = try XCTUnwrap(try formfaelle().first { $0.name == name }, name)
        let mappe = Macmappe(name: "probe", herkunft: .heim, angelegt: "2026-11-10T10:00:00Z",
                             knoten: .objekt(["glb": .wahrheit(true), "bauteile": .ganz(1)]))
        let neu = try XCTUnwrap(
            Modellnachzug.gezogen(mappe, glbDa: true, abdruck: "x", groesse: fall.glb.count, kopf: { fall.glb }), name)
        return (try XCTUnwrap(neu.knoten, name), fall)
    }

    /// An der Form abgetrennt: Vermerk und Satz am Modell-Knoten sagen es, und die Mappe trägt die Hausbox.
    func testAnDerFormAbgetrenntStehtInVermerkUndSatz() throws {
        let (knoten, fall) = try gezogen("form-ebene-unter-dem-haus")
        let vermerk = try XCTUnwrap(knoten["huellbox_vermerk"]?.alsText)
        XCTAssertTrue(vermerk.contains("an der Form abgetrennt"), vermerk)
        XCTAssertFalse(vermerk.contains("nicht abgetrennt"), vermerk)
        let satz = try XCTUnwrap(knoten["glb_stand"]?["satz"]?.alsText)
        XCTAssertTrue(satz.contains("das Gelände ist an der Form abgetrennt"), satz)
        XCTAssertFalse(satz.contains("ohne Geländetrennung"), satz)
        let box = try XCTUnwrap(zahlen(knoten["huellbox_m"]))
        XCTAssertTrue(nahe(box, zahlen(fall.erwartet["huellbox"])), "\(box)")
        XCTAssertEqual(box[3] - box[0], 12, accuracy: toleranz)
        XCTAssertEqual(box[4] - box[1], 10, accuracy: toleranz)
    }

    /// Nicht entscheidbar bleibt die Szenenhülle mit Vermerk: bei Namensgleichheit und bei einem
    /// grossen flachen Körper auf halber Höhe.
    func testNichtEntscheidbarBleibtDieSzenenhuelleMitVermerk() throws {
        for name in ["form-kein-knoten-hat-einen-namen", "form-gelaende-und-bauteil-gleicher-name",
                     "form-hang-oberkante-zu-hoch", "gegen-tiefgaragendecke"] {
            let (knoten, fall) = try gezogen(name)
            let vermerk = try XCTUnwrap(knoten["huellbox_vermerk"]?.alsText, name)
            XCTAssertTrue(vermerk.contains("Gelände nicht abgetrennt"), "\(name): \(vermerk)")
            XCTAssertTrue(vermerk.contains("nicht entscheidbar"), "\(name): \(vermerk)")
            let satz = try XCTUnwrap(knoten["glb_stand"]?["satz"]?.alsText, name)
            XCTAssertTrue(satz.contains("ohne Geländetrennung"), "\(name): \(satz)")
            XCTAssertTrue(nahe(try XCTUnwrap(zahlen(knoten["huellbox_m"]), name), zahlen(fall.erwartet["szenenbox"])), name)
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
