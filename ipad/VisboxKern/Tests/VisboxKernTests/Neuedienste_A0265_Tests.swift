import Foundation
import XCTest
import VisboxKern

/// A0265: N1 (später angelegte Dienste tragen den frischen Zugang) und N2 (der Testbau bietet sich
/// dem iPad nie an). Verhaltensproben auf den reinen Regeln im Kern; die Mac-Quellen werden dazu
/// auf die Verdrahtung geprüft (die Mac-App lässt sich unter Linux nicht übersetzen).
final class NeueDiensteTests: XCTestCase {

    private struct Lesung: Equatable { var zugang: String; var satz: String? }

    private var wurzel: URL {
        URL(fileURLWithPath: #filePath).deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    }

    private func mac(_ teil: String) throws -> String {
        try String(contentsOf: wurzel.appendingPathComponent("ipad/\(Marke.name)Mac/Sources/\(Marke.name)Mac/\(teil)"),
                   encoding: .utf8)
    }

    private func rumpf(_ text: String, ab kopf: String) throws -> String {
        let k = try XCTUnwrap(text.range(of: kopf), "\(kopf) fehlt")
        let rest = String(text[k.lowerBound...])
        return String(rest.prefix(1500))
    }

    // ------------------------------------------------------------------ N1

    /// «iPad vergessen», dann ein neuer Dienst (Wechsel von Adresse oder Anmeldung): er trägt den neuen Zugang.
    func testNachIpadVergessenTraegtDerNeueDienstDenNeuenZugang() {
        var merker = Lesungsmerker<Lesung>()
        merker.uebernimm(Lesung(zugang: "alt", satz: nil))
        func neuerDienst() -> String? { merker.lesung?.zugang }
        XCTAssertEqual(neuerDienst(), "alt")
        // «iPad vergessen»: der Dienst meldet den neuen Zugang (und den Satz der Ablage).
        merker.fuehreNach { $0 = Lesung(zugang: "neu", satz: "nicht abgelegt") }
        XCTAssertEqual(neuerDienst(), "neu", "ein später angelegter Dienst nahm die alte Startlesung")
        XCTAssertEqual(merker.lesung?.satz, "nicht abgelegt")
        // und nochmals vergessen
        merker.fuehreNach { $0.zugang = "neuer" }
        XCTAssertEqual(neuerDienst(), "neuer")
    }

    func testNachfuehrenOhneLesungErfindetKeine() {
        var merker = Lesungsmerker<Lesung>()
        merker.fuehreNach { $0.zugang = "neu" }
        XCTAssertNil(merker.lesung, "ohne Startlesung gibt es keinen Dienst und nichts nachzuführen")
    }

    func testDieMacQuellenFuehrenDieLesungBeiJederAenderungNach() throws {
        let anschluss = try mac("Start/Vermittlungsanschluss.swift")
        XCTAssertTrue(anschluss.contains("Lesungsmerker<Vermittlerlesung>"))
        XCTAssertTrue(anschluss.contains("fuehreNach"), "der Anschluss führt die Lesung nicht nach")
        XCTAssertTrue(anschluss.contains("zugangGeaendert"), "der neue Dienst meldet dem Anschluss nichts")
        let dienst = try mac("Vermittlung/Vermittlungsdienst.swift")
        let vergiss = try rumpf(dienst, ab: "func vergissIPad(")
        XCTAssertTrue(vergiss.contains("zugangGeaendert"), "«iPad vergessen» meldet den neuen Zugang nicht")
        // Nie auf dem Hauptfaden lesen: der Anschluss liest den Schlüsselbund nicht selbst.
        for verboten in ["liesOderErzeuge", "Vermittlerlesung.lies", "SecItemCopyMatching"] {
            XCTAssertFalse(anschluss.contains(verboten), "der Anschluss liest selbst: \(verboten)")
        }
    }

    // ------------------------------------------------------------------ N2

    func testImTestbauWirktDasAnbietenNieUndSagtEsEinmal() {
        let test = Testbau.anbieten(gewuenscht: true, testbau: true)
        XCTAssertFalse(test.an, "der Testbau bot sich dem iPad an")
        let satz = test.satz ?? ""
        XCTAssertEqual(satz, Testbau.satzKeinAnbieten)
        XCTAssertEqual(satz.filter { ".!?".contains($0) }.count, 1, "mehr oder weniger als ein Satz: \(satz)")
        XCTAssertTrue(satz.contains("Testbau") && satz.contains("iPad") && satz.contains("installierten"), satz)
        // Auch das Ausschalten ist im Testbau still aus.
        XCTAssertFalse(Testbau.anbieten(gewuenscht: false, testbau: true).an)
    }

    func testInDerInstalliertenAppBleibtDasAnbietenWieEingestellt() {
        for wunsch in [true, false] {
            let r = Testbau.anbieten(gewuenscht: wunsch, testbau: false)
            XCTAssertEqual(r.an, wunsch)
            XCTAssertNil(r.satz)
        }
    }

    func testStarteUndSchalteAnbietenFragenZuerstNachDemTestbau() throws {
        let dienst = try mac("Vermittlung/Vermittlungsdienst.swift")
        let starte = try rumpf(dienst, ab: "func starte(mitZahl")
        let wache = try XCTUnwrap(starte.range(of: "Testbau.aktiv"), "starte fragt nicht nach dem Testbau")
        XCTAssertTrue(starte.contains("sageTestbau()"))
        XCTAssertTrue(dienst.contains("Testbau.satzKeinAnbieten"))
        XCTAssertLessThan(wache.lowerBound, try XCTUnwrap(starte.range(of: "biete()")).lowerBound)
        let anschluss = try mac("Start/Vermittlungsanschluss.swift")
        let schalte = try rumpf(anschluss, ab: "func schalteAnbieten(")
        let w2 = try XCTUnwrap(schalte.range(of: "Testbau.anbieten("), "schalteAnbieten fragt nicht nach dem Testbau")
        XCTAssertLessThan(w2.lowerBound, try XCTUnwrap(schalte.range(of: "Vermittlergedaechtnis.angeboten = ")).lowerBound)
        let koppeln = try rumpf(anschluss, ab: "func dienstZumKoppeln(")
        XCTAssertTrue(koppeln.contains("Testbau.aktiv"), "«iPad koppeln» schaltet im Testbau das Anbieten ein")
    }

    func testDerSchalterImTestbauIstOhneWirkungUndSagtEs() throws {
        let fenster = try mac("Start/Hauptfenster.swift")
        let k = try XCTUnwrap(fenster.range(of: "iPad über diesen Mac anbieten"))
        let umfeld = String(fenster[k.lowerBound...].prefix(900))
        XCTAssertTrue(umfeld.contains("anbietenSatz") || umfeld.contains("Testbau.satzKeinAnbieten"),
                      "der Schalter sagt im Testbau nichts")
    }

    func testDieAnleitungSagtDassDerTestbauSichNieAnbietet() throws {
        let text = try String(contentsOf: wurzel.appendingPathComponent("ipad/\(Marke.name)Mac/LIESMICH.md"), encoding: .utf8)
        let k = try XCTUnwrap(text.range(of: "## Testbau"))
        let rest = text[k.lowerBound...].dropFirst(3)
        let abschnitt = String(rest.prefix(upTo: rest.range(of: "\n## ")?.lowerBound ?? rest.endIndex))
        XCTAssertTrue(abschnitt.contains("bietet sich dem iPad nie an"), "Anleitung sagt nicht, dass er sich nie anbietet")
        XCTAssertTrue(abschnitt.contains("iPad über diesen Mac anbieten"), "Anleitung nennt den Schalter nicht")
        XCTAssertTrue(abschnitt.contains("ohne Wirkung"))
        XCTAssertFalse(abschnitt.contains("(das iPad bietet er dann nicht an)"), "alter Halbsatz: nur im Fehlerfall")
    }
}
