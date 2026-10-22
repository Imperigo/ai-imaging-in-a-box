import Foundation
import XCTest
@testable import VisboxKern

/// Die Zeile «iPad» am Mac, der Weg in «Wer rechnet wo», die ehrliche Nähe und der
/// Aussetzerfilter — alles vom Owner-Befund des 20.10.2026 (Visbox 0.2.11).
final class IpadzeileTests: XCTestCase {

    private let t0 = Date(timeIntervalSinceReferenceDate: 812_000_000)
    private func t(_ s: TimeInterval) -> Date { t0.addingTimeInterval(s) }

    private func buch(_ json: String, status: Int = 200) -> Geraetebefund {
        .antwort(status: status, daten: Data(json.utf8))
    }

    private let direktGesehen = #"{"ipad": {"gekoppelt": true, "gekoppelt_vor_s": 600, "zuletzt_gesehen_s": 8, "weg": "direkt"}}"#
    private let nieGekoppelt = #"{"ipad": {"gekoppelt": false, "gekoppelt_vor_s": null, "zuletzt_gesehen_s": null, "weg": null}}"#

    // ------------------------------------------------------------- der Owner-Befund

    /// Das iPad ist direkt (Tailscale) mit dem Heim-PC gekoppelt, die Vermittlung am Mac ist an
    /// und wartet: **steht**, «direkt», und die Kopfzeile sagt 4 von 4.
    func testDirektGekoppeltStehtAuchWennDieVermittlungWartet() {
        let z = Ipadzeile.stand(geraete: buch(direktGesehen),
                                vermittlung: .wartet(letzteAnfrageVor: nil), koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, .steht(satz: "iPad gekoppelt · direkt · zuletzt vor 8 s"))
        let bild = Startbild(leitung: .steht(satz: "x"), rechner: .steht(satz: "x"),
                             assistent: .steht(satz: "x"), ipad: z)
        XCTAssertEqual(bild.kopfzeile, "bereit · 4 von 4")
        XCTAssertEqual(Ipadzeile.weg(bericht: Ipadzeile.bericht(buch(direktGesehen)),
                                     vermittlung: .wartet(letzteAnfrageVor: nil)), .direkt)
    }

    func testOhneVermittlungUndDirektGekoppelt() {
        XCTAssertTrue(Ipadzeile.stand(geraete: buch(direktGesehen), vermittlung: nil, koppeln: nil,
                                      jetzt: t0).steht)
        XCTAssertTrue(Ipadzeile.stand(geraete: buch(direktGesehen), vermittlung: .aus, koppeln: nil,
                                      jetzt: t0).steht)
    }

    /// Gekoppelt, aber seither nicht gesehen (oder ein iPad vor 0.2.12): trotzdem gekoppelt.
    func testGekoppeltOhneMeldungIstGekoppeltMitUnbekanntemZuletzt() {
        let z = Ipadzeile.stand(
            geraete: buch(#"{"ipad": {"gekoppelt": true, "gekoppelt_vor_s": 30, "zuletzt_gesehen_s": null, "weg": "direkt"}}"#),
            vermittlung: nil, koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, .wartet(satz: "iPad gekoppelt · direkt · zuletzt gesehen: unbekannt"),
                       "ohne bekannten Kontakt nicht grün (22.10.2026)")
    }

    /// Länger als 24 h nicht gemeldet: gekoppelt, aber nicht «da» — die Zeile wartet und sagt es.
    func testLaengerAlsEinenTagNichtGesehenWartet() {
        let z = Ipadzeile.stand(
            geraete: buch(#"{"ipad": {"gekoppelt": true, "gekoppelt_vor_s": 900000, "zuletzt_gesehen_s": 259200, "weg": "direkt"}}"#),
            vermittlung: nil, koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, .wartet(satz: "iPad gekoppelt, aber seit 3 Tagen nicht gemeldet. "
                                  + "\(Marke.name) am iPad öffnen."))
        let grenze = Ipadzeile.stand(
            geraete: buch(#"{"ipad": {"gekoppelt": true, "zuletzt_gesehen_s": 86400, "weg": "direkt"}}"#),
            vermittlung: nil, koppeln: nil, jetzt: t0)
        XCTAssertFalse(grenze.steht, "24 h ohne Kontakt sind nicht grün (22.10.2026)")
        XCTAssertEqual(Ipadzeile.gesehenHoechstens, 86400)
    }

    /// DER DEMOLAUF (22.10.2026): «gekoppelt · über diesen Mac · zuletzt vor 21 h» stand grün,
    /// während das iPad «getrennt» zeigte. Grün nur bei Kontakt in den letzten fünf Minuten.
    func testGruenNurMitKontaktInDenLetztenMinuten() {
        XCTAssertEqual(Ipadzeile.erreichbarHoechstens, 300)
        func zeile(_ vor: Int) -> Zeilenstand {
            Ipadzeile.stand(
                geraete: buch(#"{"ipad": {"gekoppelt": true, "zuletzt_gesehen_s": \#(vor), "weg": "mac"}}"#),
                vermittlung: .wartet(letzteAnfrageVor: nil), koppeln: nil, jetzt: t0)
        }
        XCTAssertEqual(zeile(75600), .wartet(satz: "iPad gekoppelt · über diesen Mac, aber nicht "
                                             + "erreichbar seit 21 h. \(Marke.name) am iPad öffnen."))
        XCTAssertEqual(zeile(600), .wartet(satz: "iPad gekoppelt · über diesen Mac, aber nicht "
                                           + "erreichbar seit 10 min. \(Marke.name) am iPad öffnen."))
        XCTAssertEqual(zeile(301).wort, "wartet")
        XCTAssertEqual(zeile(300), .steht(satz: "iPad gekoppelt · über diesen Mac · zuletzt vor 5 min"),
                       "genau fünf Minuten gelten noch")
    }

    func testNieGekoppeltZeigtDieVorgabe() {
        XCTAssertEqual(Ipadzeile.stand(geraete: buch(nieGekoppelt), vermittlung: nil, koppeln: nil,
                                       jetzt: t0), Startbild.ipadVorgabe)
    }

    /// Ein Heim-PC vor 0.2.12 (404), keine Antwort oder eine unlesbare: **nie «gekoppelt»**,
    /// ohne dass es jemand meldet.
    func testOhneGeraetebuchNieGekoppelt() {
        for befund: Geraetebefund? in [nil, buch(#"{"fehler": "Unbekannter Weg"}"#, status: 404),
                                       .keineAntwort(.zeitUeberschritten), buch("<html>"),
                                       buch(#"{"ipad": {"gekoppelt": 1}}"#), buch(#"{"ipad": true}"#)] {
            XCTAssertEqual(Ipadzeile.stand(geraete: befund, vermittlung: nil, koppeln: nil, jetzt: t0),
                           Startbild.ipadVorgabe, "\(String(describing: befund))")
        }
    }

    // ------------------------------------------------------------- die Vermittlung

    func testDieVermittlungMeldetEinIpadUeberDiesenMac() {
        let z = Ipadzeile.stand(geraete: buch(nieGekoppelt), vermittlung: .verbunden(letzteAnfrageVor: 4),
                                koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, .steht(satz: "iPad gekoppelt · über diesen Mac · zuletzt vor 4 s"))
        XCTAssertEqual(Ipadzeile.weg(bericht: nil, vermittlung: .verbunden(letzteAnfrageVor: 4)),
                       .ueberMac)
    }

    /// Der Heim-PC hat das iPad zuletzt über den Mac gesehen, und die Vermittlung ist an.
    func testUeberDenMacGesehen() {
        let mac = buch(#"{"ipad": {"gekoppelt": true, "zuletzt_gesehen_s": 12, "weg": "mac"}}"#)
        let z = Ipadzeile.stand(geraete: mac, vermittlung: .wartet(letzteAnfrageVor: 40),
                                koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, .steht(satz: "iPad gekoppelt · über diesen Mac · zuletzt vor 12 s"))
        // IST DIE VERMITTLUNG AUS, kann der Mac nicht vermitteln — dann direkt.
        XCTAssertEqual(Ipadzeile.weg(bericht: Ipadzeile.bericht(mac), vermittlung: .aus), .direkt)
        XCTAssertEqual(Ipadzeile.weg(bericht: Ipadzeile.bericht(mac), vermittlung: nil), .direkt)
    }

    /// Eine Zahl der Vermittlung kommt nur noch ausdrücklich — und dann zeigt die Zeile sie.
    func testEineAusdruecklicheZahlDerVermittlungWirdGezeigt() {
        let lage = Vermittlerlage.koppeln(zahl: "845501", nochSekunden: 16)
        let z = Ipadzeile.stand(geraete: buch(nieGekoppelt), vermittlung: lage, koppeln: nil, jetzt: t0)
        XCTAssertEqual(z, lage.alsZeilenstand())
    }

    func testNichtGekoppeltUndVermittlungWartetZeigtIhrenSatz() {
        let lage = Vermittlerlage.wartet(letzteAnfrageVor: nil)
        XCTAssertEqual(Ipadzeile.stand(geraete: buch(nieGekoppelt), vermittlung: lage, koppeln: nil,
                                       jetzt: t0), lage.alsZeilenstand())
    }

    // ------------------------------------------------------------- das Koppelfenster

    func testDasOffeneKoppelfensterZeigtSeineZahl() {
        let angebot = Koppelangebot(stand: .wartet(satz: "Zahl fürs iPad: 123 456"), seit: t(0))
        // DAS IPAD WAR SCHON VORHER GEKOPPELT (vor 600 s): Wer «iPad koppeln» drückt, will die
        // Zahl sehen — etwa für ein zweites iPad.
        XCTAssertEqual(Ipadzeile.stand(geraete: buch(direktGesehen), vermittlung: nil,
                                       koppeln: angebot, jetzt: t(5)), angebot.stand)
    }

    /// Koppelt das iPad aus diesem Fenster (QR-Code), sagt die Zeile es gleich — nicht erst,
    /// wenn das Fenster zugeht.
    func testEineKopplungNachDemOeffnenGehtVorDieZahl() {
        let angebot = Koppelangebot(stand: .wartet(satz: "Zahl fürs iPad: 123 456"), seit: t(0))
        let frisch = buch(#"{"ipad": {"gekoppelt": true, "gekoppelt_vor_s": 3, "zuletzt_gesehen_s": 3, "weg": "direkt"}}"#)
        XCTAssertEqual(Ipadzeile.stand(geraete: frisch, vermittlung: nil, koppeln: angebot, jetzt: t(20)),
                       .steht(satz: "iPad gekoppelt · direkt · zuletzt vor 3 s"))
    }

    // ------------------------------------------------------------- «Wer rechnet wo»

    func testDieSaetzeZumWeg() {
        // SEIT ENTSCHEID 118a endet der direkte Weg, und ueber den Mac kommt die Mappe.
        XCTAssertTrue(Ipadweg.direkt.satz.contains("diesen Weg nimmt der Heim-PC nicht mehr an"))
        XCTAssertFalse(Ipadweg.direkt.satz.contains("Übergang"))
        XCTAssertFalse(Ipadweg.direkt.satz.contains("arbeitet über"))
        XCTAssertTrue(Ipadweg.ueberMac.satz.contains("Das iPad arbeitet über diesen Mac, verschlüsselt"))
        XCTAssertEqual(Ipadweg.direkt.wort, "direkt")
        XCTAssertEqual(Ipadweg.ueberMac.wort, "über diesen Mac")
        XCTAssertEqual(Ipadzeile.weg(bericht: nil, vermittlung: nil), .direkt,
                       "nichts bekannt und keine Vermittlung: der Weg seit Entscheid 63")
        for satz in [Ipadweg.direkt.satz, Ipadweg.ueberMac.satz] {
            XCTAssertFalse(satz.contains("ß"), "Schweizer Schreibung")
        }
    }

    func testDerBerichtLiestNurSeineForm() {
        XCTAssertEqual(Geraetebericht.lies(Data(direktGesehen.utf8)),
                       Geraetebericht(gekoppelt: true, gekoppeltVor: 600, zuletztGesehenVor: 8,
                                      weg: .direkt))
        XCTAssertEqual(Geraetebericht.lies(Data(#"{"ipad": {"gekoppelt": true, "zuletzt_gesehen_s": -5, "weg": "funk"}}"#.utf8)),
                       Geraetebericht(gekoppelt: true), "negative Zeit und fremder Weg: unbekannt")
        XCTAssertNil(Geraetebericht.lies(Data("[]".utf8)))
    }

    // ------------------------------------------------------------- die Köpfe

    func testJedeAnfrageSagtIhreGeraeteartOhneNamen() {
        let a = Anmeldung(benutzer: "b", kennwort: "k")
        let ipad = Anfragen.kopfzeilen(Wege.fortschritt, anmeldung: a, geraet: .ipad)
        XCTAssertEqual(ipad["X-Geraet"], "ipad")
        XCTAssertEqual(Anfragen.kopfzeilen(Wege.verbinden, anmeldung: nil, geraet: .ipad)["X-Geraet"],
                       "ipad", "auch beim Koppeln — der Heim-PC vermerkt die Kopplung")
        XCTAssertEqual(Anfragen.kopfzeilen(Wege.fortschritt, anmeldung: a, geraet: .mac)["X-Geraet"], "mac")
        XCTAssertNil(Anfragen.kopfzeilen(Wege.fortschritt, anmeldung: a, geraet: nil)["X-Geraet"])
        XCTAssertEqual(Set(ipad.keys), ["Accept", "Authorization", "X-Geraet"])
        XCTAssertEqual(Anfragen.geraete(anmeldung: a).weg, Wege.geraete)
        XCTAssertEqual(Wege.geraete.pfad, "/api/geraete")
        XCTAssertFalse(Wege.geraete.ohneAnmeldung)
    }

    /// Was über die Vermittlung geht, trägt «ipad» und «über den Mac» — gesetzt vom Mac, nicht
    /// vom iPad weitergereicht.
    func testDieVermittlungSagtIpadUeberDenMac() {
        let w = Weiterreichung(methode: "GET", ziel: "/api/fortschritt",
                               koepfe: [Kopfzeile("Accept", "application/json"),
                                        Kopfzeile("X-Geraet-Weg", "direkt"),
                                        Kopfzeile("x-geraet", "mac")], rumpf: nil)
        let hinaus = w.koepfe(mit: Anmeldung(benutzer: "b", kennwort: "m"))
        XCTAssertEqual(hinaus.werte("X-Geraet"), ["ipad"])
        XCTAssertEqual(hinaus.werte("X-Geraet-Weg"), ["mac"])
        XCTAssertEqual(hinaus.werte("Accept"), ["application/json"])
    }

    // ------------------------------------------------------------- die Nähe

    func testDieSucheSagtNachDreissigSekundenDassNichtsKam() {
        XCTAssertEqual(Naehekopplung.ohneFundNach, 30)
        XCTAssertEqual(Naehekopplung.suchstand(seit: t0, jetzt: t(29.9), gefunden: false, fehler: nil), .sucht)
        let kein = Naehekopplung.suchstand(seit: t0, jetzt: t(30), gefunden: false, fehler: nil)
        XCTAssertEqual(kein, .keinFund)
        XCTAssertEqual(kein.satz, "Kein Mac in der Nähe gefunden. Gleiches WLAN? Lokales Netzwerk "
                       + "erlaubt? Sonst den QR-Code nehmen.")
        XCTAssertTrue(kein.qrHervor)
        XCTAssertEqual(Naehekopplung.suchstand(seit: t0, jetzt: t(300), gefunden: true, fehler: nil), .sucht,
                       "ein gefundener Mac ist kein «nichts gefunden»")
        XCTAssertEqual(Naehekopplung.suchstand(seit: nil, jetzt: t(300), gefunden: false, fehler: nil), .sucht)
        XCTAssertFalse(Naehesuchstand.sucht.qrHervor)
    }

    func testDieSucheStartetNichtSagtDenGrund() {
        let s = Naehekopplung.suchstand(seit: t0, jetzt: t(1), gefunden: false,
                                        fehler: "Der Vorgang konnte nicht abgeschlossen werden.")
        XCTAssertEqual(s.satz, "Die Suche nach dem Mac in der Nähe startet nicht (Der Vorgang "
                       + "konnte nicht abgeschlossen werden). Lokales Netzwerk erlaubt? Sonst den "
                       + "QR-Code nehmen.")
        XCTAssertTrue(s.qrHervor)
    }

    func testDieZeileDesMacZurNaehe() {
        XCTAssertEqual(Naeheanbieterstand.bietetAn(name: "Mac").zeile,
                       "In der Nähe: sucht … (sichtbar als «Mac»)")
        XCTAssertEqual(Naeheanbieterstand.anfrage(name: "iPad").zeile, "In der Nähe: «iPad» fragt an.")
        let geht = Naeheanbieterstand.gehtNicht(grund: "Fehler -72008.")
        XCTAssertEqual(geht.zeile, "In der Nähe: geht hier nicht — Fehler -72008. Bitte den QR-Code nehmen.")
        XCTAssertTrue(geht.istFehler)
        XCTAssertFalse(Naeheanbieterstand.bietetAn(name: "Mac").istFehler)
        XCTAssertEqual(Naeheanbieterstand.gehtNicht(grund: "  ").zeile,
                       "In der Nähe: geht hier nicht — ohne Angabe des Grundes. Bitte den QR-Code nehmen.")
    }

    // ------------------------------------------------------------- der Aussetzer am iPad

    func testEinAussetzerTrenntDasIpadNicht() {
        var f = Aussetzerfilter()
        XCTAssertNil(f.erreichbar(jetzt: t0), "noch nicht gefragt")
        f.melde(erreicht: true, jetzt: t0)
        XCTAssertEqual(f.erreichbar(jetzt: t0), true)
        // PRUEFABSTAND 10 s: drei Fehlschlaege bei 10, 20, 30.
        f.melde(erreicht: false, jetzt: t(10))
        XCTAssertEqual(f.erreichbar(jetzt: t(10)), true, "ein Aussetzer")
        XCTAssertTrue(f.kurzWeg(jetzt: t(10)))
        f.melde(erreicht: false, jetzt: t(20))
        f.melde(erreicht: false, jetzt: t(30))
        XCTAssertEqual(f.erreichbar(jetzt: t(30)), true, "drei, aber erst 20 s still")
        f.melde(erreicht: false, jetzt: t(40))
        XCTAssertEqual(f.erreichbar(jetzt: t(40)), false, "vier und 30 s: getrennt")
        XCTAssertFalse(f.kurzWeg(jetzt: t(40)))
        f.melde(erreicht: true, jetzt: t(50))
        XCTAssertEqual(f.erreichbar(jetzt: t(50)), true, "von selbst zurück")
        XCTAssertEqual(f.fehlschlaege, 0)
    }

    func testOhneFruehereAntwortGibtEsNichtsZuUeberbruecken() {
        var f = Aussetzerfilter()
        f.melde(erreicht: false, jetzt: t0)
        XCTAssertEqual(f.erreichbar(jetzt: t0), false)
        f.melde(erreicht: true, jetzt: t(1))
        f.vergiss()
        f.melde(erreicht: false, jetzt: t(2))
        XCTAssertEqual(f.erreichbar(jetzt: t(2)), false, "nach dem Vergessen von vorn")
    }

    /// Und die Abfolge aus dem Befund, als Folge: Antwort, zwei Aussetzer, Antwort — die
    /// Anzeige bleibt durchgehend «Gekoppelt».
    func testDieFolgeAusDemBefundBleibtGekoppelt() {
        var f = Aussetzerfilter()
        let folge: [(TimeInterval, Bool)] = [(0, true), (10, false), (20, false), (30, true), (40, true)]
        for (zeit, ok) in folge {
            f.melde(erreicht: ok, jetzt: t(zeit))
            let z = Verbindungszustand.bestimme(gekoppelt: true, sucht: false,
                                                erreichbar: f.erreichbar(jetzt: t(zeit)), grund: "x")
            XCTAssertEqual(z, .gekoppelt, "bei \(zeit) s")
        }
    }
}
