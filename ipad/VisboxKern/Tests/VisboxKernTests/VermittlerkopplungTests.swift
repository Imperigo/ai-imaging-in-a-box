import Foundation
import XCTest
import VisboxKern

/// Die lokale Kopplung iPad ↔ Mac — dieselben Regeln wie an der HomeStation (Protokoll §7):
/// 600 s, 5 Versuche, nach Erfolg verbraucht, ein Satz für das Gerät.
final class VermittlerkopplungTests: XCTestCase {

    private let start: TimeInterval = 1000

    private func neu(_ zahl: String = "042917") -> Vermittlerkopplung {
        Vermittlerkopplung(jetzt: start, zahl: zahl)!
    }

    // ------------------------------------------------------------------ die Regeln

    func testDieRegelnSindDieDerHomeStation() {
        XCTAssertEqual(Vermittlerkopplung.frist, 600)
        XCTAssertEqual(Vermittlerkopplung.versuche, 5)
        XCTAssertEqual(Vermittlerkopplung.stellen, 6)
    }

    func testDieFristLaeuftAufDerGereichtenUhr() {
        let k = neu()
        XCTAssertEqual(k.stand(jetzt: start), .offen)
        XCTAssertEqual(k.stand(jetzt: start + 599.9), .offen)
        XCTAssertEqual(k.stand(jetzt: start + 600), .abgelaufen)
    }

    func testDieRichtigeZahlVerbindetEinmal() {
        var k = neu()
        let erst = k.pruefe("042917", jetzt: start + 1)
        XCTAssertTrue(erst.angenommen)
        XCTAssertEqual(erst.stand, .verbraucht)
        XCTAssertEqual(erst.satzFuerDasGeraet, "")
        let zweit = k.pruefe("042917", jetzt: start + 2)
        XCTAssertFalse(zweit.angenommen, "ein zweites Gerät braucht eine neue Zahl")
        XCTAssertEqual(zweit.grund, Vermittlerkopplung.grundVerbraucht)
    }

    func testFuenfFehlversucheUndDieZahlIstTot() {
        var k = neu()
        for i in 1...4 {
            let v = k.pruefe("000000", jetzt: start + Double(i))
            XCTAssertFalse(v.angenommen)
            XCTAssertEqual(v.grund, Vermittlerkopplung.grundFalsch)
            XCTAssertEqual(v.versucheUebrig, 5 - i)
        }
        let fuenfter = k.pruefe("000000", jetzt: start + 5)
        XCTAssertEqual(fuenfter.grund, Vermittlerkopplung.grundAufgebraucht)
        XCTAssertEqual(fuenfter.stand, .aufgebraucht)
        let richtig = k.pruefe("042917", jetzt: start + 6)
        XCTAssertFalse(richtig.angenommen, "auch die richtige hilft nicht mehr")
        XCTAssertEqual(k.stand(jetzt: start + 6), .aufgebraucht)
    }

    func testAnEinerAbgelaufenenZahlZaehltKeinVersuch() {
        var k = neu()
        let v = k.pruefe("042917", jetzt: start + 600)
        XCTAssertFalse(v.angenommen, "die richtige Zahl, aber zu spät")
        XCTAssertEqual(v.grund, Vermittlerkopplung.grundAbgelaufen)
        XCTAssertEqual(k.versucheUebrig, 5)
    }

    func testVerbrauchtGehtVorAbgelaufen() {
        var k = neu()
        _ = k.pruefe("042917", jetzt: start + 1)
        XCTAssertEqual(k.stand(jetzt: start + 10_000), .verbraucht)
    }

    func testDasGeraetHoertImmerDenselbenSatz() {
        var k = neu()
        var saetze = Set<String>()
        saetze.insert(k.pruefe("111111", jetzt: start + 1).satzFuerDasGeraet)
        for _ in 0..<4 { saetze.insert(k.pruefe("111111", jetzt: start + 2).satzFuerDasGeraet) }
        var spaet = neu()
        saetze.insert(spaet.pruefe("042917", jetzt: start + 700).satzFuerDasGeraet)
        var weg = neu()
        _ = weg.pruefe("042917", jetzt: start + 1)
        saetze.insert(weg.pruefe("042917", jetzt: start + 2).satzFuerDasGeraet)
        XCTAssertEqual(saetze, [Vermittlerkopplung.satzFuerDasGeraet],
                       "falsch, aufgebraucht, abgelaufen, verbraucht — ein Satz")
    }

    func testNurLeerraumAmRandWirdEntfernt() {
        var k = neu()
        XCTAssertFalse(k.pruefe("042 917", jetzt: start + 1).angenommen)
        XCTAssertFalse(k.pruefe(nil, jetzt: start + 1).angenommen)
        XCTAssertTrue(k.pruefe(" 042917\n", jetzt: start + 1).angenommen)
    }

    func testVonHandGeschlossenIstVerbraucht() {
        var k = neu()
        k.schliesse()
        XCTAssertEqual(k.stand(jetzt: start), .verbraucht)
    }

    func testEineKopplungOhneFristOderVersucheGibtEsNicht() {
        XCTAssertNil(Vermittlerkopplung(jetzt: 0, frist: 0))
        XCTAssertNil(Vermittlerkopplung(jetzt: 0, versuche: 0))
        XCTAssertNil(Vermittlerkopplung(jetzt: 0, zahl: "12345"))
        XCTAssertNil(Vermittlerkopplung(jetzt: 0, zahl: "12345a"))
    }

    // --------------------------------------------------------------- die Zahl

    private struct Fest: RandomNumberGenerator {
        var wert: UInt64
        mutating func next() -> UInt64 { wert }
    }

    func testDieZahlHatSechsStellenAuchMitFuehrendenNullen() {
        // EINS, NICHT NULL: `Int.random(in:using:)` verwirft Werte (Lemire); ein Erzeuger,
        // der immer 0 liefert, kaeme nie heraus. Aus 1 wird die kleinste Zahl, 0.
        var null = Fest(wert: 1)
        XCTAssertEqual(Vermittlerkopplung.wuerfle(using: &null), "000000")
        for _ in 0..<50 {
            let k = Vermittlerkopplung(jetzt: 0)!
            XCTAssertEqual(k.zahl.count, 6)
            XCTAssertTrue(k.zahl.allSatisfy { $0.isASCII && $0.isNumber })
        }
    }

    func testDieZahlStehtInKeinerAusgabe() {
        let k = neu("424242")
        XCTAssertFalse("\(k)".contains("424242"))
    }

    // ---------------------------------------------------------------- der Zugang

    func testDerZugangIstZufaelligUndLang() {
        let a = Vermittlerzugang.erzeuge()
        let b = Vermittlerzugang.erzeuge()
        XCTAssertEqual(a.anmeldung.kennwort.count, Vermittlerzugang.laenge)
        XCTAssertEqual(Vermittlerzugang.laenge, 32)
        XCTAssertNotEqual(a.anmeldung.kennwort, b.anmeldung.kennwort)
        XCTAssertEqual(a.anmeldung.benutzer, Marke.name.lowercased(),
                       "derselbe Benutzername wie beim Server — aus der Marke")
        let erlaubt = Set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        XCTAssertTrue(a.anmeldung.kennwort.allSatisfy { erlaubt.contains($0) })
        XCTAssertFalse("\(a)".contains(a.anmeldung.kennwort), "das Kennwort steht in keiner Ausgabe")
    }

    func testDerZugangLaesstNurSichSelbstHerein() {
        let z = Vermittlerzugang.erzeuge()
        let a = z.anmeldung
        XCTAssertTrue(z.laesstHerein(a.kopfzeile))
        XCTAssertFalse(z.laesstHerein(nil))
        XCTAssertFalse(z.laesstHerein(""))
        XCTAssertFalse(z.laesstHerein("Bearer " + a.kennwort))
        XCTAssertFalse(z.laesstHerein("Basic !!!kein-base64"))
        XCTAssertFalse(z.laesstHerein(Anmeldung(benutzer: a.benutzer, kennwort: a.kennwort + "x").kopfzeile))
        XCTAssertFalse(z.laesstHerein(Anmeldung(benutzer: "anderer", kennwort: a.kennwort).kopfzeile))
        XCTAssertFalse(z.laesstHerein("Basic " + Data(a.kennwort.utf8).base64EncodedString()),
                       "ohne Doppelpunkt kein Benutzer")
        XCTAssertFalse(z.laesstHerein(Vermittlerzugang.erzeuge().anmeldung.kopfzeile))
    }

    func testDerVergleichSiehtJedeStelle() {
        XCTAssertTrue(Vermittlerzugang.gleich([1, 2, 3], [1, 2, 3]))
        XCTAssertFalse(Vermittlerzugang.gleich([1, 2, 3], [1, 2, 4]))
        XCTAssertFalse(Vermittlerzugang.gleich([0, 2, 3], [1, 2, 3]))
        XCTAssertFalse(Vermittlerzugang.gleich([1, 2], [1, 2, 3]))
        XCTAssertTrue(Vermittlerzugang.gleich([], []))
    }
}
