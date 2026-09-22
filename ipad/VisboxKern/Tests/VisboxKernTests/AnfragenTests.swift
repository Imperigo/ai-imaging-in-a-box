import Foundation
import XCTest
import VisboxKern

/// Die Anfragen an die HomeStation und das Lesen ihrer Antworten.
///
/// Die Antworten unten sind **dem Server nachgebildet** (`oberflaeche/server.py`, Stand
/// 22.09.2026) — Feld für Feld so, wie `_sende` sie schreibt. Ändert sich dort ein Feld,
/// fällt hier nichts; das Protokollblatt ist dann nachzuziehen (siehe dort, §9).
final class AnfragenTests: XCTestCase {

    private let anmeldung = Anmeldung(benutzer: "probe", kennwort: "geheim-32-zeichen")

    private func json(_ text: String) -> Data { Data(text.utf8) }

    private func rumpf(_ a: Anfrage) throws -> [String: JSONWert] {
        let roh = try XCTUnwrap(a.rumpf, "ein POST ohne Rumpf")
        return try XCTUnwrap(JSONWert.lies(roh).alsObjekt)
    }

    // ------------------------------------------------------------------- die Tür

    func testDieAnmeldungIstHttpBasicAusBenutzerUndKennwort() throws {
        let a = Anfragen.fortschritt(anmeldung: anmeldung)
        let kopf = try XCTUnwrap(a.kopfzeilen["Authorization"])
        XCTAssertTrue(kopf.hasPrefix("Basic "), kopf)
        let roh = try XCTUnwrap(Data(base64Encoded: String(kopf.dropFirst("Basic ".count))))
        XCTAssertEqual(String(decoding: roh, as: UTF8.self), "probe:geheim-32-zeichen")
    }

    func testDerWegHineinBekommtKeineAnmeldungAuchWennEineDaIst() throws {
        // Ein altes, falsches Kennwort gehoert nicht an den Weg, der es erst ausgibt.
        let zahl = try XCTUnwrap(Kopplungszahl("123456"))
        let a = try Anfragen.baue(Wege.verbinden, rumpf: ["pin": .text(zahl.ziffern)],
                                  anmeldung: anmeldung)
        XCTAssertNil(a.kopfzeilen["Authorization"])
        XCTAssertNil(try Anfragen.verbinden(zahl).kopfzeilen["Authorization"])
        XCTAssertEqual(try rumpf(Anfragen.verbinden(zahl)), ["pin": .text("123456")])
    }

    func testJederAndereWegTraegtDieAnmeldung() throws {
        for a in try alleBauformen() where !a.weg.ohneAnmeldung {
            XCTAssertNotNil(a.kopfzeilen["Authorization"], "\(a.methode) \(a.weg.pfad)")
        }
    }

    func testDasKennwortStehtInKeinerAusgabe() {
        let texte = [String(describing: anmeldung), String(reflecting: anmeldung),
                     "\(anmeldung)", { var s = ""; dump(anmeldung, to: &s); return s }()]
        for t in texte {
            XCTAssertFalse(t.contains(anmeldung.kennwort), t)
        }
    }

    // --------------------------------------------------------------- die Bauformen

    /// Jede Bauform einmal. Eine neue Bauform gehört hier dazu.
    private func alleBauformen() throws -> [Anfrage] {
        let png = Data(Ebenenausgabe.pngKennung)
        return [
            Anfragen.projekt(ordner: "/p", anmeldung: anmeldung),
            Anfragen.fortschritt(anmeldung: anmeldung),
            Anfragen.bild(name: "a.png", ordner: nil, anmeldung: anmeldung),
            try Anfragen.verbinden(Kopplungszahl("000000")!),
            try Anfragen.skizze(png: png, anmeldung: anmeldung),
            try Anfragen.rechne(anmeldung: anmeldung),
            try Anfragen.einstellungen(["schritte": .ganz(8)], anmeldung: anmeldung),
            try Anfragen.anlegen(ordner: "/p", modell: "/m.ifc", anmeldung: anmeldung),
            try Anfragen.benennen(bild: "a.png", titel: "Nord", anmeldung: anmeldung),
            try Anfragen.abbrechen(anmeldung: anmeldung),
            try Anfragen.rechneSkizze(["s.png"], anmeldung: anmeldung),
        ]
    }

    func testJederWegDesServersHatEineBauformAusserDerWebseite() throws {
        // Faellt, sobald in `Wege.alle` ein Weg dazukommt, den die App nicht bauen kann.
        let gebaut = Set(try alleBauformen().map(\.weg))
        // `/koppeln` ist eine Webseite fuer den Browser wie `/` — die App koppelt ueber
        // `/api/verbinden` und braucht keine Bauform dafuer.
        let erwartet = Set(Wege.alle).subtracting([Wege.seite, Wege.seiteLang, Wege.koppeln])
        XCTAssertEqual(gebaut, erwartet)
    }

    func testPostTraegtImmerEinJsonObjektUndGetNie() throws {
        for a in try alleBauformen() {
            switch a.methode {
            case .get:
                XCTAssertNil(a.rumpf, a.weg.pfad)
                XCTAssertNil(a.kopfzeilen["Content-Type"], a.weg.pfad)
            case .post:
                XCTAssertEqual(a.kopfzeilen["Content-Type"], "application/json; charset=utf-8")
                XCTAssertNotNil(try rumpf(a), a.weg.pfad)
            }
        }
        XCTAssertEqual(try rumpf(try Anfragen.rechne(anmeldung: anmeldung)), [:])
    }

    // ------------------------------------------ ein unschreibbarer Rumpf geht nicht hinaus

    /// Bis zur Durchsicht vom 22.09.2026 ging hier still `{}` hinaus — und drüben hiess das
    /// «keine Einstellungen»: Die HomeStation rechnete mit ihren Vorgaben.
    func testEinUnschreibbarerRumpfWirftStattStillLeerZuGehen() {
        let unschreibbar: [Double] = [.nan, .infinity, -.infinity]
        for z in unschreibbar {
            XCTAssertThrowsError(try Anfragen.einstellungen(["cfg": .zahl(z)], anmeldung: anmeldung),
                                 "\(z)") { fehler in
                XCTAssertEqual(fehler as? Rumpffehler, Rumpffehler(weg: Wege.einstellungen))
            }
            XCTAssertThrowsError(try Anfragen.rechne(einstellungen: ["cfg": .zahl(z)],
                                                     anmeldung: anmeldung), "\(z)")
            // AUCH TIEF DRIN: in einer Liste in einem Objekt.
            XCTAssertThrowsError(try Anfragen.baue(
                Wege.anlegen, rumpf: ["einstellungen": .objekt(["reihe": .liste([.zahl(1), .zahl(z)])])],
                anmeldung: anmeldung), "\(z)")
        }
        // Der Satz sagt, dass NICHTS hinausging — auch nicht leer.
        let satz = Rumpffehler(weg: Wege.rechne).satz
        XCTAssertTrue(satz.contains("/api/rechne"), satz)
        XCTAssertTrue(satz.contains("ging nicht hinaus"), satz)
        // Und eine gewoehnliche Kommazahl geht, wie sie ist.
        XCTAssertEqual(try rumpf(try Anfragen.einstellungen(["cfg": .zahl(4.5)], anmeldung: anmeldung))[
            "einstellungen"]?["cfg"], .zahl(4.5))
    }

    // ---------------------------------------------- der Schluessel gegen Doppelsendung

    func testDieSkizzeAusDemFachTraegtIhrenSchluessel() throws {
        let ordner = FileManager.default.temporaryDirectory
            .appendingPathComponent("anfragen-probe-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager.default.removeItem(at: ordner) }
        let fach = try Parkfach(ordner: ordner)
        let png = Data(Ebenenausgabe.pngKennung + [4, 2])
        let e = try fach.parke(png: png, ueber: "lauf-07.png", name: "Variante A", ordner: "/mappe")

        let r = try rumpf(try Anfragen.skizze(e, png: png, anmeldung: anmeldung))
        XCTAssertEqual(r["schluessel"], .text(e.schluessel))
        XCTAssertEqual(r["ueber"], .text("lauf-07.png"))
        XCTAssertEqual(r["name"], .text("Variante A"))
        XCTAssertEqual(r["ordner"], .text("/mappe"))
        XCTAssertEqual(r["png_base64"]?.alsText.flatMap { Data(base64Encoded: $0) }, png)

        // DIE FORM, DIE DER SERVER ANNIMMT (Protokoll §3: 8–128 Zeichen aus A–Z a–z 0–9 . _ -).
        // Eine andere Form wiese er mit 400 ab, und die Skizze laege abgewiesen im Fach.
        let erlaubt = Set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
        XCTAssertTrue((8...128).contains(e.schluessel.count), e.schluessel)
        XCTAssertTrue(e.schluessel.allSatisfy { erlaubt.contains($0) }, e.schluessel)

        // Ohne Schluessel fehlt das Feld — es wird nicht leer mitgeschickt.
        XCTAssertNil(try rumpf(try Anfragen.skizze(png: png, anmeldung: anmeldung))["schluessel"])
    }

    func testDieSkizzeGehtAlsBase64UndFreiwilligesFehltStattLeerZuSein() throws {
        let png = Data(Ebenenausgabe.pngKennung + [1, 2, 3, 250])
        let a = try Anfragen.skizze(png: png, ueber: nil, bemerkung: "", name: "Variante A",
                                    ordner: "/mappe", anmeldung: anmeldung)
        let r = try rumpf(a)
        XCTAssertEqual(r["png_base64"]?.alsText.flatMap { Data(base64Encoded: $0) }, png)
        XCTAssertEqual(r["name"], .text("Variante A"))
        XCTAssertEqual(r["ordner"], .text("/mappe"))
        XCTAssertNil(r["ueber"], "ohne Unterlage fehlt das Feld")
        XCTAssertNil(r["bemerkung"], "eine leere Bemerkung ist keine")
        XCTAssertEqual(a.pfad, "/api/skizze")
    }

    func testEinstellungMitNullWirdMitgeschicktDennSieEntferntDrueben() throws {
        let a = try Anfragen.einstellungen(["schritte": .ganz(28), "prompt": .null],
                                           ordner: "/p", anmeldung: anmeldung)
        let e = try XCTUnwrap(try rumpf(a)["einstellungen"]?.alsObjekt)
        XCTAssertEqual(e["prompt"], .null)
        XCTAssertEqual(e["schritte"], .ganz(28))
    }

    func testEineGanzeZahlBleibtGanzAufDerLeitung() throws {
        // Der Server prueft `isinstance(wert, int)`; eine 28.0 haette keinen Nenner.
        let a = try Anfragen.rechne(einstellungen: ["schritte": .ganz(28)], trotzAenderung: true,
                                    anmeldung: anmeldung)
        let text = String(decoding: try XCTUnwrap(a.rumpf), as: UTF8.self)
        XCTAssertTrue(text.contains("\"schritte\":28"), text)
        XCTAssertFalse(text.contains("28.0"), text)
        XCTAssertTrue(text.contains("\"trotz_aenderung\":true"), text)
    }

    func testDieFrageWirdKodiertUndOhneOrdnerFehltSie() throws {
        let a = Anfragen.bild(name: "a+b & c.png", ordner: "/Mappe 1", anmeldung: anmeldung)
        let basis = try XCTUnwrap(URL(string: "http://192.0.2.10:8731"))
        let url = try XCTUnwrap(a.adresse(basis: basis))
        let teile = try XCTUnwrap(URLComponents(url: url, resolvingAgainstBaseURL: false))
        XCTAssertEqual(teile.path, "/bild")
        XCTAssertEqual(teile.queryItems?.first { $0.name == "name" }?.value, "a+b & c.png")
        XCTAssertEqual(teile.queryItems?.first { $0.name == "ordner" }?.value, "/Mappe 1")
        XCTAssertFalse(a.pfad.contains("+"), a.pfad)
        XCTAssertTrue(a.pfad.hasPrefix("/bild?"), a.pfad)

        XCTAssertEqual(Anfragen.projekt(ordner: nil, anmeldung: anmeldung).pfad, "/api/projekt")
        XCTAssertEqual(Anfragen.projekt(ordner: "", anmeldung: anmeldung).pfad, "/api/projekt")
    }

    // ------------------------------------------------------- die sechsstellige Zahl

    func testDieZahlHatGenauSechsAsciiZiffern() {
        XCTAssertEqual(Kopplungszahl(" 042917\n")?.ziffern, "042917")
        XCTAssertNil(Kopplungszahl("12345"))
        XCTAssertNil(Kopplungszahl("1234567"))
        XCTAssertNil(Kopplungszahl("123 456"), "wird nicht zusammengezogen, wie am Server")
        XCTAssertNil(Kopplungszahl("12a456"))
        XCTAssertNil(Kopplungszahl("١٢٣٤٥٦"), "arabisch-indische Ziffern sind nicht die Zahl")
    }

    // --------------------------------------------------------------- JSON als Wert

    func testWahrheitGanzUndKommaBleibenGetrennt() throws {
        let w = try JSONWert.lies(json(#"{"a": true, "b": 1, "c": 1.5, "d": null, "e": "x"}"#))
        XCTAssertEqual(w["a"], .wahrheit(true))
        XCTAssertEqual(w["b"], .ganz(1))
        XCTAssertEqual(w["c"], .zahl(1.5))
        XCTAssertEqual(w["d"], .null)
        XCTAssertNil(w["b"]?.alsWahrheit, "eine 1 ist kein Ja")
        XCTAssertNil(w["a"]?.alsGanz, "ein Ja ist keine 1")
        XCTAssertNil(w["fehlt"])
    }

    // ------------------------------------------------------------- erstes Verbinden

    func testKopplungErfolgGibtDieAnmeldungDesServers() throws {
        let antwort = json(#"""
        {"verbunden": true, "benutzer": "probe", "kennwort": "k", "satz": "Verbunden. Dieses Gerät merkt sich die Anmeldung."}
        """#)
        let e = try Kopplungsergebnis.lies(status: 200, daten: antwort)
        XCTAssertEqual(e, .verbunden(anmeldung: Anmeldung(benutzer: "probe", kennwort: "k"),
                                     satz: "Verbunden. Dieses Gerät merkt sich die Anmeldung."))
    }

    func testKopplungOhneKennwortAmServerIstVerbundenOhneAnmeldung() throws {
        let e = try Kopplungsergebnis.lies(
            status: 200, daten: json(#"{"verbunden": true, "benutzer": "probe", "kennwort": null}"#))
        XCTAssertEqual(e, .verbunden(anmeldung: nil, satz: nil))
    }

    func testKopplungMitFehlendemKennwortIstUnlesbarNichtOhneKennwort() {
        XCTAssertThrowsError(try Kopplungsergebnis.lies(
            status: 200, daten: json(#"{"verbunden": true, "benutzer": "probe"}"#))) {
            XCTAssertEqual(($0 as? Serverfehler)?.art, .unlesbar)
        }
        XCTAssertThrowsError(try Kopplungsergebnis.lies(status: 200, daten: json("{}")))
    }

    func testKopplungAbgelehntTraegtDenSatzDesServers() throws {
        let satz = "Das hat nicht geklappt. An der HomeStation eine neue Zahl holen."
        XCTAssertEqual(try Kopplungsergebnis.lies(
            status: 403, daten: json(#"{"verbunden": false, "satz": "\#(satz)"}"#)),
                       .abgelehnt(satz: satz))
        let zu = "Auf dieser HomeStation ist gerade kein Verbinden offen."
        XCTAssertEqual(try Kopplungsergebnis.lies(
            status: 403, daten: json(#"{"fehler": "\#(zu)"}"#)), .abgelehnt(satz: zu))
        XCTAssertEqual(try Kopplungsergebnis.lies(status: 401, daten: json("{}")),
                       .abgelehnt(satz: Kopplungsergebnis.keinVerbindenOffen))
    }

    // --------------------------------------------------------------------- Fehler

    func testFehlerTragenIhrenSatzUndIhreArt() {
        let faelle: [(Int, Serverfehler.Art)] = [(400, .abgelehnt), (401, .nichtAngemeldet),
                                                 (403, .verweigert), (404, .nichtGefunden),
                                                 (500, .anderer)]
        for (code, art) in faelle {
            do {
                _ = try Projektsicht.lies(status: code,
                                          daten: json(#"{"fehler": "Satz \#(code)"}"#))
                XCTFail("\(code) ist kein Erfolg")
            } catch let f as Serverfehler {
                XCTAssertEqual(f.art, art)
                XCTAssertEqual(f.satz, "Satz \(code)")
                XCTAssertTrue(f.satzVomServer)
            } catch {
                XCTFail("\(error)")
            }
        }
    }

    func testOhneLesbarenSatzSagtDieAppDassErVonIhrKommt() {
        XCTAssertThrowsError(try Fortschrittsstand.lies(status: 502, daten: json("<html>"))) {
            let f = $0 as? Serverfehler
            XCTAssertEqual(f?.satzVomServer, false)
            XCTAssertTrue(f?.satz.contains("502") == true, f?.satz ?? "")
        }
        XCTAssertThrowsError(try Projektsicht.lies(status: 200, daten: json("[1, 2]"))) {
            XCTAssertEqual(($0 as? Serverfehler)?.art, .unlesbar)
        }
    }

    func testEinBildIstBytesOderEinSatz() throws {
        let bytes = Data(Ebenenausgabe.pngKennung)
        XCTAssertEqual(try liesBild(status: 200, daten: bytes), bytes)
        XCTAssertThrowsError(try liesBild(status: 404, daten: json(
            #"{"fehler": "Es fehlt der Projektordner oder der Bildname."}"#))) {
            XCTAssertEqual(($0 as? Serverfehler)?.satz,
                           "Es fehlt der Projektordner oder der Bildname.")
        }
        XCTAssertThrowsError(try liesBild(status: 200, daten: Data()))
    }

    // -------------------------------------------------------------- die Projektsicht

    func testDieProjektsichtLiestDieBilderMitDenDreiAntworten() throws {
        let antwort = json(#"""
        {"name": "Probe", "ordner": "/p",
         "modell": {"pfad": "m.ifc", "stand": "nicht_pruefbar", "grund": "kein Abdruck", "einlass": {}},
         "import": {"status": "ok"}, "einstellungen": {"schritte": 8},
         "knotenbaum": [], "knotenbaum_fehler": null, "bedienfelder": [],
         "bilder": [
           {"bild": "a.png", "schicht": "geometrielayer", "zeichen": "bestanden", "satz": "s",
            "erzeugt": "2026-09-22T08:00:00Z", "herkunft": {}, "vorhanden": true, "basis": null},
           {"bild": "b.png", "zeichen": "nicht-gemessen", "satz": "kein Tiefenbild", "vorhanden": null},
           {"bild": "c.png", "zeichen": "vielleicht", "vorhanden": false},
           {"bild": "d.png"}
         ],
         "skizzen": [{"skizze": "skizze-20260922-080000.png", "ueber": null, "erzeugt": "2026-09-22T08:00:00Z",
                      "stand": "offen", "bemerkung": "", "ergebnis": null}],
         "grundriss": {"bbox": null, "grund": "x", "schrumpfung": null}, "laeufe": [], "formate": []}
        """#)
        let s = try Projektsicht.lies(status: 200, daten: antwort)
        XCTAssertEqual(s.name, "Probe")
        XCTAssertEqual(s.modell?.stand, .nichtPruefbar)
        XCTAssertNil(s.knotenbaumFehler)
        let b = try XCTUnwrap(s.bilder)
        XCTAssertEqual(b.map(\.urteil), [.bestanden, .nichtGemessen, nil, nil],
                       "ein unbekanntes oder fehlendes Zeichen wird nicht geraten")
        XCTAssertEqual(b.map(\.vorhanden), [true, nil, false, nil])
        XCTAssertEqual(b[1].satz, "kein Tiefenbild")
        XCTAssertNil(b[0].basis)
        XCTAssertEqual(s.skizzen?.first?.stand, "offen")
        XCTAssertNil(s.skizzen?.first?.ergebnis)
        XCTAssertEqual(s.einstellungen?["schritte"], .ganz(8))
    }

    func testFehlendeListenSindNichtGeliefertUndNichtLeer() throws {
        let s = try Projektsicht.lies(status: 200, daten: json(#"{"name": "x"}"#))
        XCTAssertNil(s.bilder)
        XCTAssertNil(s.skizzen)
        XCTAssertNil(s.modell)
        let leer = try Projektsicht.lies(status: 200, daten: json(#"{"bilder": []}"#))
        XCTAssertEqual(leer.bilder, [])
    }

    // --------------------------------------------------------------- der Laufstand

    private func laufstand(_ felder: String) -> Data {
        json(#"""
        {"laeuft": true, "ordner": "/p", "seit_s": 12.5, "knoten": "render", "knotenart": "Render",
         "nummer": 3, "von": 5, "knoten_seit_s": 4.0, \#(felder),
         "fertige": [{"knoten": "k1", "knotenart": "Import", "status": "ok", "aus_cache": true, "dauer_s": 0.4}],
         "ergebnis": null, "fehler": null}
        """#)
    }

    func testEinAnteilNurWennDerServerSagtDassGezaehltIst() throws {
        let belegt = try Fortschrittsstand.lies(status: 200, daten: laufstand(
            #""schritt": 14, "schritte_gesamt": 28, "art_des_zeichens": "belegt""#))
        XCTAssertEqual(belegt.schrittanteil, 0.5)
        XCTAssertEqual(belegt.fertige?.first?.ausCache, true)
        XCTAssertEqual(belegt.nummer, 3)

        let unbelegt = try Fortschrittsstand.lies(status: 200, daten: laufstand(
            #""schritt": 14, "schritte_gesamt": 28, "art_des_zeichens": "unbelegt""#))
        XCTAssertNil(unbelegt.schrittanteil, "unbelegt heisst: keine Zahl")

        let ohneNenner = try Fortschrittsstand.lies(status: 200, daten: laufstand(
            #""schritt": 3, "schritte_gesamt": null, "art_des_zeichens": "belegt""#))
        XCTAssertNil(ohneNenner.schritteGesamt, "null ist unbekannt, nicht 0")
        XCTAssertNil(ohneNenner.schrittanteil)

        let fremd = try Fortschrittsstand.lies(status: 200, daten: laufstand(
            #""schritt": 3, "schritte_gesamt": 6, "art_des_zeichens": "geschaetzt""#))
        XCTAssertNil(fremd.belegt)
        XCTAssertNil(fremd.schrittanteil)
    }

    // ---------------------------------------------------------- Antworten auf POST

    func testAbgelegtIstEineQuittungUndNurDann() throws {
        let q = try Skizzenquittung.lies(status: 200, daten: json(
            #"{"abgelegt": true, "skizze": "skizze-20260922-081207.png", "hinweis": "Abgelegt, aber NICHT gerechnet"}"#))
        XCTAssertEqual(q.skizze, "skizze-20260922-081207.png")
        XCTAssertThrowsError(try Skizzenquittung.lies(status: 200, daten: json(#"{"abgelegt": 1}"#)))

        XCTAssertEqual(try Rechenstart.lies(
            status: 200, daten: json(#"{"gestartet": true, "schritte_gesamt": null}"#)).schritteGesamt, nil)
        XCTAssertEqual(try Einstellungsantwort.lies(
            status: 200, daten: json(#"{"gespeichert": true, "einstellungen": {"a": 1}}"#))
            .einstellungen, ["a": .ganz(1)])
        XCTAssertNotNil(try Anlegeantwort.lies(
            status: 200, daten: json(#"{"angelegt": true, "import": {"status": "abgelehnt"}}"#)).einfuhr)
        XCTAssertThrowsError(try Anlegeantwort.lies(status: 200, daten: json("{}")))
    }

    // ---------------------------------------------- das Kennwort liegt nie in UserDefaults

    /// **Eine Abwesenheitsprobe** über die App-Schicht der Verbindung (die hier nicht
    /// übersetzt wird): Keine Datei, deren Code `UserDefaults` benutzt, nennt in ihrem Code
    /// das Kennwort oder die Anmeldung. Die Lehre aus dem früheren Mac-Client, der das
    /// Kennwort dort im Klartext ablegte (22.09.2026). Ganze Kommentarzeilen zählen nicht:
    /// Der Schlüsselbund darf erklären, warum er nicht `UserDefaults` ist.
    func testKeineDateiMitUserDefaultsNenntDasKennwort() throws {
        // DAS APP-PAKET WIRD GESUCHT, NICHT BEIM NAMEN GENANNT: Der Name steht nur in der
        // Marke (`tests/test_ipad_geruest.py`), und nach der Umbenennung hiesse das Paket
        // anders.
        let ipad = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent().deletingLastPathComponent()
            .deletingLastPathComponent().deletingLastPathComponent()
        let paket = try XCTUnwrap(FileManager.default.contentsOfDirectory(
            at: ipad, includingPropertiesForKeys: nil).first { $0.pathExtension == "swiftpm" })
        let ordner = paket.appendingPathComponent("Verbindung", isDirectory: true)
        let dateien = try FileManager.default.contentsOfDirectory(
            at: ordner, includingPropertiesForKeys: nil).filter { $0.pathExtension == "swift" }
        XCTAssertFalse(dateien.isEmpty, ordner.path)
        var mitUserDefaults = 0
        for datei in dateien {
            let text = try String(contentsOf: datei, encoding: .utf8)
                .split(separator: "\n", omittingEmptySubsequences: false)
                .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
                .joined(separator: "\n")
            guard text.contains("UserDefaults") else { continue }
            mitUserDefaults += 1
            for verboten in ["kennwort", "anmeldung", "passwor"] {
                XCTAssertFalse(text.lowercased().contains(verboten),
                               "\(datei.lastPathComponent) benutzt UserDefaults und nennt «\(verboten)»")
            }
        }
        XCTAssertGreaterThan(mitUserDefaults, 0,
                             "die Probe sieht keine Datei mit UserDefaults mehr — hat sich der Ort geändert?")
    }
}
