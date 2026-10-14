import Foundation
import XCTest
import VisboxKern

/// Aktualisieren (Owner-Entscheid 84, 13.10.2026): Nummern, die Antwort der GitHub-API, Paket
/// und Pruefsumme, die Tagesregel, das Bundle nach dem Entpacken und der Ablauf am iPad.
///
/// Die Antwort unten ist **nachgebaut** nach der Form von `GET /repos/{o}/{r}/releases/latest`
/// (gekuerzt auf die Felder, die der Kern liest, plus einige, die er uebergehen muss). Die
/// Summen sind erfunden.
final class AktualisierungTests: XCTestCase {

    /// Besitzer und Repo aus dem Kern, nicht ausgeschrieben: Ein Name vor dem Repo-Namen in
    /// einem Pfad faellt unter den Waechter von Regel 3 (`tests/test_regel3_kennungen.py`).
    private let hier = "\(Aktualisierung.besitzer)/\(Aktualisierung.repo)"
    private let summeMac = String(repeating: "ab", count: 32)
    private let summeIpad = String(repeating: "cd", count: 32)

    private func antwort(tag: String = "v0.2.1", draft: Bool = false, prerelease: Bool = false,
                         macAdresse: String? = nil, digest: String? = nil) -> Data {
        let mac = macAdresse
            ?? "https://github.com/\(hier)/releases/download/\(tag)/\(Aktualisierung.macPaket)"
        let digestFeld = digest.map { "\"digest\": \"\($0)\"," } ?? ""
        let text = """
        {
          "url": "https://api.github.com/repos/\(hier)/releases/1",
          "html_url": "https://github.com/\(hier)/releases/tag/\(tag)",
          "id": 1,
          "tag_name": "\(tag)",
          "target_commitish": "main",
          "name": "Fassung \(tag)",
          "draft": \(draft),
          "prerelease": \(prerelease),
          "created_at": "2026-10-13T20:00:00Z",
          "published_at": "2026-10-13T20:05:00Z",
          "author": {"login": "github-actions[bot]"},
          "assets": [
            {"name": "\(Aktualisierung.macPaket)", "size": 1234, "state": "uploaded",
             \(digestFeld)
             "content_type": "application/zip",
             "browser_download_url": "\(mac)"},
            {"name": "\(Aktualisierung.ipadPaket)", "size": 999, "state": "uploaded",
             "browser_download_url": "https://github.com/\(hier)/releases/download/\(tag)/\(Aktualisierung.ipadPaket)"},
            {"name": "\(Aktualisierung.pruefsummen)", "size": 300, "state": "uploaded",
             "browser_download_url": "https://github.com/\(hier)/releases/download/\(tag)/\(Aktualisierung.pruefsummen)"},
            {"name": "halb.zip", "size": 5, "state": "starter",
             "browser_download_url": "https://github.com/\(hier)/releases/download/\(tag)/halb.zip"}
          ],
          "body": "# Fassungsblatt\\n\\n## Was neu ist\\n\\n| Fähigkeit | Entscheid | Stand |\\n|---|---|---|\\n| Koppeln mit Zahl | 83 | gebaut |\\n| Aktualisieren | 84 | gebaut |\\n\\n## Grenzen\\n\\n* nicht neu"
        }
        """
        return Data(text.utf8)
    }

    // ------------------------------------------------------------------ Nummern

    func testNummernMitDreiTeilen() {
        XCTAssertEqual(Fassungsnummer("0.2.1")?.description, "0.2.1")
        XCTAssertEqual(Fassungsnummer("v0.2.1")?.description, "0.2.1")
        XCTAssertEqual(Fassungsnummer(" 1.0.0\n")?.tag, "v1.0.0")
        for schlecht in ["0.2", "0.2.1.0", "", "v", "0.2.x", "0..1", "-1.0.0", "0.02.1",
                         "0.2.1-beta", "V0.2.1", "０.2.1", "0.2.1 "+"x"] {
            XCTAssertNil(Fassungsnummer(schlecht), schlecht)
        }
    }

    /// Als Text stuende `0.10.0` vor `0.9.0` — verglichen wird als Zahl.
    func testVergleichTeilFuerTeilAlsZahl() throws {
        let n = { (t: String) throws -> Fassungsnummer in try XCTUnwrap(Fassungsnummer(t)) }
        XCTAssertLessThan(try n("0.9.0"), try n("0.10.0"))
        XCTAssertLessThan(try n("0.2.0"), try n("0.2.1"))
        XCTAssertLessThan(try n("0.2.9"), try n("0.3.0"))
        XCTAssertLessThan(try n("0.99.99"), try n("1.0.0"))
        XCTAssertEqual(try n("0.2.1"), try n("v0.2.1"))
        XCTAssertFalse(try n("0.2.1") < n("0.2.1"))
    }

    // ------------------------------------------------------------------ Antwort deuten

    func testDieAntwortWirdGedeutet() throws {
        let f = try Aktualisierung.deute(antwort())
        XCTAssertEqual(f.nummer.description, "0.2.1")
        XCTAssertEqual(f.seite?.absoluteString,
                       "https://github.com/\(hier)/releases/tag/v0.2.1")
        // NUR FERTIG HOCHGELADENE ANLAGEN: «starter» ist ein abgebrochener Upload.
        XCTAssertEqual(f.anlagen.map(\.name),
                       [Aktualisierung.macPaket, Aktualisierung.ipadPaket, Aktualisierung.pruefsummen])
        XCTAssertEqual(f.anlage(Aktualisierung.macPaket)?.groesse, 1234)
        XCTAssertNil(f.anlage(Aktualisierung.macPaket)?.githubSumme)
        XCTAssertEqual(Aktualisierung.neuerungen(aus: f.begleittext),
                       ["Koppeln mit Zahl", "Aktualisieren"])
    }

    func testDieDateinamenKommenAusDerMarke() {
        XCTAssertEqual(Aktualisierung.macPaket, "\(Marke.name)-mac.zip")
        XCTAssertEqual(Aktualisierung.ipadPaket, "\(Marke.name).swiftpm.zip")
        XCTAssertEqual(Aktualisierung.abfrage.absoluteString,
                       "https://api.github.com/repos/\(hier)/releases/latest")
    }

    /// Ohne Token, mit der Nummer der App im User-Agent (GitHub verlangt einen).
    func testDieKopfzeilenTragenKeinToken() {
        let k = Aktualisierung.kopfzeilen(laufend: Fassungsnummer("0.2.1"))
        XCTAssertEqual(k["User-Agent"], "\(Marke.name)/0.2.1")
        XCTAssertEqual(k["Accept"], "application/vnd.github+json")
        XCTAssertNil(k["Authorization"])
        XCTAssertEqual(Aktualisierung.kopfzeilen(laufend: nil)["User-Agent"], "\(Marke.name)/0.0.0")
    }

    func testEntwurfUndVorabfassungWerdenNichtAngeboten() {
        XCTAssertThrowsError(try Aktualisierung.deute(antwort(draft: true))) {
            XCTAssertEqual($0 as? Aktualisierungsfehler, .entwurf)
        }
        XCTAssertThrowsError(try Aktualisierung.deute(antwort(prerelease: true))) {
            XCTAssertEqual($0 as? Aktualisierungsfehler, .entwurf)
        }
    }

    func testEinTagOhneNummerIstKeineFreigabe() {
        for tag in ["0.2.1", "v0.2", "neueste"] {
            XCTAssertThrowsError(try Aktualisierung.deute(antwort(tag: tag)), tag) {
                XCTAssertEqual($0 as? Aktualisierungsfehler, .keineNummer(tag))
            }
        }
    }

    func testUnlesbareAntwort() {
        for daten in [Data(), Data("{}".utf8), Data("<html>".utf8),
                      Data(#"{"message":"API rate limit exceeded"}"#.utf8)] {
            XCTAssertThrowsError(try Aktualisierung.deute(daten)) {
                XCTAssertEqual($0 as? Aktualisierungsfehler, .unlesbar)
            }
        }
    }

    /// **Laden nur von genau diesem Repo**: Eine Anlage, die woandershin zeigt, faellt weg —
    /// sie wird nicht angeboten und nie geladen.
    func testAnlagenAusFremdenQuellenFallenWeg() throws {
        let fremd = [
            "https://github.com/jemand/ai-imaging-in-a-box/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://github.com/Imperigo/anderes/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://github.com/\(hier)/releases/download/v0.2.0/\(Aktualisierung.macPaket)",
            "http://github.com/\(hier)/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://github.com.example.org/\(hier)/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://github.com:8443/\(hier)/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://x@github.com/\(hier)/releases/download/v0.2.1/\(Aktualisierung.macPaket)",
            "https://github.com/\(hier)/releases/download/v0.2.1/\(Aktualisierung.macPaket)?x=1",
            "https://github.com/\(hier)/releases/download/v0.2.1/anders.zip",
        ]
        for adresse in fremd {
            let f = try Aktualisierung.deute(antwort(macAdresse: adresse))
            XCTAssertNil(f.anlage(Aktualisierung.macPaket), adresse)
        }
    }

    func testWeiterleitungNurZuGithub() throws {
        let gut = ["https://objects.githubusercontent.com/github-production-release-asset/1",
                   "https://release-assets.githubusercontent.com/github-production-release-asset/1",
                   "https://github.com/\(hier)/releases/download/v0.2.1/a"]
        let schlecht = ["http://objects.githubusercontent.com/x",
                        "https://githubusercontent.com.example.org/x",
                        "https://example.org/x",
                        "https://evilgithubusercontent.com/x"]
        for a in gut { XCTAssertTrue(Aktualisierung.istErlaubteWeiterleitung(try XCTUnwrap(URL(string: a))), a) }
        for a in schlecht { XCTAssertFalse(Aktualisierung.istErlaubteWeiterleitung(try XCTUnwrap(URL(string: a))), a) }
    }

    // ------------------------------------------------------------------ Angebot (84b)

    func testAngebotenWirdNurEineNeuereNummer() throws {
        let f = try Aktualisierung.deute(antwort())
        XCTAssertTrue(Aktualisierung.bietetAn(f, laufend: Fassungsnummer("0.2.0")))
        XCTAssertFalse(Aktualisierung.bietetAn(f, laufend: Fassungsnummer("0.2.1")))
        XCTAssertFalse(Aktualisierung.bietetAn(f, laufend: Fassungsnummer("0.3.0")))
        XCTAssertFalse(Aktualisierung.bietetAn(f, laufend: nil))
    }

    func testDieLaufendeNummerKommtAusDerPlist() {
        XCTAssertEqual(Aktualisierung.laufendeNummer(["CFBundleShortVersionString": "0.2.1"]),
                       Fassungsnummer("0.2.1"))
        XCTAssertNil(Aktualisierung.laufendeNummer(["CFBundleShortVersionString": "0.2"]))
        XCTAssertNil(Aktualisierung.laufendeNummer(nil))
    }

    // ------------------------------------------------------------------ Tagesregel (84a)

    func testEinmalTaeglich() {
        let jetzt = Date(timeIntervalSince1970: 2_000_000_000)
        XCTAssertTrue(Aktualisierung.sollFragen(letzte: nil, jetzt: jetzt))
        // Entscheid 87: jede Stunde.
        XCTAssertFalse(Aktualisierung.sollFragen(letzte: jetzt.addingTimeInterval(-60), jetzt: jetzt))
        XCTAssertFalse(Aktualisierung.sollFragen(letzte: jetzt.addingTimeInterval(-3599), jetzt: jetzt))
        XCTAssertTrue(Aktualisierung.sollFragen(letzte: jetzt.addingTimeInterval(-3600), jetzt: jetzt))
        // DIE UHR WURDE ZURUECKGESTELLT: sonst fragte die App womoeglich nie wieder.
        XCTAssertTrue(Aktualisierung.sollFragen(letzte: jetzt.addingTimeInterval(3600), jetzt: jetzt))
        XCTAssertEqual(Aktualisierung.abstand, 3_600)
    }

    // ------------------------------------------------------------------ Pruefsumme

    private var summenDatei: String {
        """
        \(summeMac)  \(Aktualisierung.macPaket)
        \(summeIpad) *\(Aktualisierung.ipadPaket)
        kaputt  zeile
        """
    }

    func testSummeAusDerDateiDerPruefsummen() {
        XCTAssertEqual(Aktualisierung.summe(fuer: Aktualisierung.macPaket, in: summenDatei), summeMac)
        XCTAssertEqual(Aktualisierung.summe(fuer: Aktualisierung.ipadPaket, in: summenDatei), summeIpad)
        XCTAssertNil(Aktualisierung.summe(fuer: "fehlt.zip", in: summenDatei))
        XCTAssertNil(Aktualisierung.summe(fuer: "zeile", in: summenDatei))
        // ZWEIMAL MIT VERSCHIEDENEN SUMMEN: keine gilt.
        let doppelt = summenDatei + "\n\(summeIpad)  \(Aktualisierung.macPaket)"
        XCTAssertNil(Aktualisierung.summe(fuer: Aktualisierung.macPaket, in: doppelt))
        // GROSS GESCHRIEBEN gilt dieselbe Summe.
        XCTAssertEqual(Aktualisierung.summe(fuer: "a", in: summeMac.uppercased() + "  a"), summeMac)
    }

    func testDieGeladeneDateiWirdGeprueft() throws {
        let f = try Aktualisierung.deute(antwort())
        let mac = try XCTUnwrap(f.anlage(Aktualisierung.macPaket))
        XCTAssertNil(Aktualisierung.pruefe(anlage: mac, groesse: 1234, summe: summeMac.uppercased(),
                                           summenDatei: summenDatei))
        XCTAssertEqual(Aktualisierung.pruefe(anlage: mac, groesse: 1234, summe: summeIpad,
                                             summenDatei: summenDatei), .pruefsummeFalsch)
        XCTAssertEqual(Aktualisierung.pruefe(anlage: mac, groesse: 1000, summe: summeMac,
                                             summenDatei: summenDatei),
                       .groesseFalsch(erwartet: 1234, erhalten: 1000))
        XCTAssertEqual(Aktualisierung.pruefe(anlage: mac, groesse: 1234, summe: summeMac,
                                             summenDatei: ""), .pruefsummeFehlt)
    }

    /// GitHub nennt seit 2025 selbst eine Summe je Anlage. Steht sie da, muss auch sie stimmen
    /// — zwei unabhaengige Quellen statt einer.
    func testDieSummeVonGithubMussAuchStimmen() throws {
        let gleich = try Aktualisierung.deute(antwort(digest: "sha256:\(summeMac)"))
        let mac = try XCTUnwrap(gleich.anlage(Aktualisierung.macPaket))
        XCTAssertEqual(mac.githubSumme, summeMac)
        XCTAssertNil(Aktualisierung.pruefe(anlage: mac, groesse: 1234, summe: summeMac,
                                           summenDatei: summenDatei))

        let anders = try Aktualisierung.deute(antwort(digest: "sha256:\(summeIpad)"))
        let falsch = try XCTUnwrap(anders.anlage(Aktualisierung.macPaket))
        XCTAssertEqual(Aktualisierung.pruefe(anlage: falsch, groesse: 1234, summe: summeMac,
                                             summenDatei: summenDatei), .pruefsummeFalsch)

        let fremdeArt = try Aktualisierung.deute(antwort(digest: "md5:abc"))
        XCTAssertNil(fremdeArt.anlage(Aktualisierung.macPaket)?.githubSumme)
    }

    func testSechzehnerschrift() {
        XCTAssertEqual(Aktualisierung.sechzehner([0x00, 0x0f, 0xa0, 0xff]), "000fa0ff")
        XCTAssertTrue(Aktualisierung.istSumme(summeMac))
        XCTAssertFalse(Aktualisierung.istSumme(String(summeMac.dropLast())))
        XCTAssertFalse(Aktualisierung.istSumme(String(repeating: "g", count: 64)))
    }

    // ------------------------------------------------------------------ Ersetzen

    func testGenauEinBundleImPaket() {
        XCTAssertEqual(Aktualisierung.waehleBuendel(["\(Marke.name).app"]), "\(Marke.name).app")
        XCTAssertEqual(Aktualisierung.waehleBuendel(["__MACOSX", "\(Marke.name).app"]),
                       "\(Marke.name).app")
        XCTAssertNil(Aktualisierung.waehleBuendel([]))
        XCTAssertNil(Aktualisierung.waehleBuendel(["a.app", "b.app"]))
        XCTAssertNil(Aktualisierung.waehleBuendel([".versteckt.app"]))
        XCTAssertNil(Aktualisierung.waehleBuendel(["liesmich.txt"]))
    }

    func testDasNeueBundleTraegtDieKennungUndDieNummer() throws {
        let kennung = Marke.kennung + ".mac"
        let nummer = try XCTUnwrap(Fassungsnummer("0.2.1"))
        let gut: [String: Any] = ["CFBundleIdentifier": kennung, "CFBundlePackageType": "APPL",
                                  "CFBundleShortVersionString": "0.2.1"]
        XCTAssertNil(Aktualisierung.pruefeBuendel(gut, kennung: kennung, nummer: nummer))

        var fremd = gut; fremd["CFBundleIdentifier"] = "org.example.anderes"
        XCTAssertEqual(Aktualisierung.pruefeBuendel(fremd, kennung: kennung, nummer: nummer),
                       .fremdeKennung("org.example.anderes"))
        var keineApp = gut; keineApp["CFBundlePackageType"] = "BNDL"
        XCTAssertEqual(Aktualisierung.pruefeBuendel(keineApp, kennung: kennung, nummer: nummer),
                       .fremdeKennung(kennung))
        var alt = gut; alt["CFBundleShortVersionString"] = "0.2.0"
        XCTAssertEqual(Aktualisierung.pruefeBuendel(alt, kennung: kennung, nummer: nummer),
                       .falscheNummer("0.2.0"))
        XCTAssertEqual(Aktualisierung.pruefeBuendel([:], kennung: kennung, nummer: nummer),
                       .fremdeKennung(""))
    }

    func testDerOrtDerLaufendenApp() {
        XCTAssertNil(Aktualisierung.pruefeOrt("/Applications/\(Marke.name).app"))
        XCTAssertNil(Aktualisierung.pruefeOrt("/Users/jemand/Programme/\(Marke.name).app/"))
        XCTAssertNotNil(Aktualisierung.pruefeOrt("/Users/jemand/.build/release"))
        let verschoben = Aktualisierung.pruefeOrt(
            "/private/var/folders/xy/T/AppTranslocation/1234/d/\(Marke.name).app")
        XCTAssertTrue(verschoben?.satz.contains("Programme") ?? false, "\(String(describing: verschoben))")
    }

    // ------------------------------------------------------------------ Neuerungen

    func testNeuerungenAusTabelleUndListe() {
        let blatt = """
        # Fassungsblatt

        **Codestand:** etwas

        ## Warum diese Nummer

        | Nicht | das |
        |---|---|
        | falsch | x |

        ## Was neu ist (mit Entscheid und Stand)

        | Fähigkeit | Entscheid | Stand |
        |:---|---|---:|
        | **Koppeln** mit Zahl | 83 | gebaut |
        |  | 1 | leer |
        | Aktualisieren | 84 | gebaut |

        * Ein Punkt
        - Noch einer
        Ein Satz.

        ## Grenzen

        * nicht neu
        """
        XCTAssertEqual(Aktualisierung.neuerungen(aus: blatt),
                       ["**Koppeln** mit Zahl", "Aktualisieren", "Ein Punkt", "Noch einer",
                        "Ein Satz."])
        XCTAssertEqual(Aktualisierung.neuerungen(aus: "ohne Abschnitt\n\n## Grenzen\n* x"), [])
        XCTAssertEqual(Aktualisierung.neuerungen(aus: ""), [])
    }

    // ------------------------------------------------------------------ Saetze

    func testDieSaetzeVonBlatt18() throws {
        let n = try XCTUnwrap(Fassungsnummer("0.2.1"))
        XCTAssertEqual(Aktualisierung.knopf(n), "● 0.2.1 verfügbar — Aktualisieren")
        XCTAssertEqual(Aktualisierung.ipadHinweis(n),
                       "Neue Fassung 0.2.1 verfügbar — am Mac in Xcode aufspielen")
        XCTAssertEqual(Aktualisierung.titel(n), "\(Marke.name) 0.2.1")
        XCTAssertTrue(Aktualisierung.behelfsHinweis.contains("Trotzdem öffnen"))
        XCTAssertEqual(Aktualisierung.spaeter, "Später")
        XCTAssertEqual(Aktualisierung.ladenUndErsetzen, "Laden und ersetzen")
        XCTAssertEqual(Aktualisierung.neuStarten, "Neu starten")
        XCTAssertEqual(Aktualisierungsphase.laedt(0.425).satz, "Lädt … 43 %")
        XCTAssertEqual(Aktualisierungsphase.laedt(nil).satz, "Lädt …")
        XCTAssertTrue(Aktualisierungsphase.gescheitert(.pruefsummeFalsch).satz.contains("Nichts wurde ersetzt"))
    }

    /// Jeder Fehler hat einen Satz, und keiner ist leer.
    func testJederFehlerHatEinenSatz() {
        let alle: [Aktualisierungsfehler] = [
            .unlesbar, .keineNummer("x"), .entwurf, .ohneMacPaket, .ohnePruefsummen,
            .pruefsummeFehlt, .pruefsummeFalsch, .groesseFalsch(erwartet: 1, erhalten: 2),
            .fremdeAdresse, .keinBuendel, .fremdeKennung("x"), .falscheNummer("x"),
            .unterschriftGebrochen, .ortGesperrt("Grund."), .ersetzenScheiterte("Grund."),
            .neustartScheiterte,
        ]
        for f in alle { XCTAssertFalse(f.satz.isEmpty, "\(f)") }
    }

    // ------------------------------------------------------------------ iPad: Ablauf

    /// Nachgebaut: eine unterschriebene Huelle (hier Fuellbytes) um eine plist in Klartext,
    /// wie Xcode sie als `embedded.mobileprovision` ins Bundle legt.
    private func profil(ablauf: String) -> Data {
        var daten = Data([0x30, 0x82, 0x0b, 0x9a, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x00, 0xff])
        daten.append(Data("""
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>AppIDName</key><string>Beispiel</string>
            <key>CreationDate</key><date>2026-10-13T08:00:00Z</date>
            <key>ExpirationDate</key><date>\(ablauf)</date>
            <key>Name</key><string>iOS Team Provisioning Profile: org.example.beispiel</string>
            <key>TimeToLive</key><integer>7</integer>
        </dict>
        </plist>
        """.utf8))
        daten.append(Data([0xa0, 0x82, 0x00, 0x3c, 0x3c, 0x2f]))
        return daten
    }

    func testDasAblaufdatumAusDemProfil() throws {
        let ablauf = try XCTUnwrap(Bereitstellungsprofil.ablauf(aus: profil(ablauf: "2026-10-20T08:00:00Z")))
        XCTAssertEqual(ablauf.timeIntervalSince1970, 1_792_483_200, accuracy: 0.5)
        XCTAssertNil(Bereitstellungsprofil.ablauf(aus: Data()))
        XCTAssertNil(Bereitstellungsprofil.ablauf(aus: Data("<?xml kaputt".utf8)))
        XCTAssertNil(Bereitstellungsprofil.ablauf(aus: profil(ablauf: "kein Datum")))
    }

    func testDerHinweisKommtErstKurzVorDemAblauf() {
        let ablauf = Date(timeIntervalSince1970: 2_000_000_000)
        let tag: TimeInterval = 86_400
        XCTAssertNil(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf.addingTimeInterval(-5 * tag)))
        XCTAssertNil(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf.addingTimeInterval(-2 * tag - 1)))
        XCTAssertEqual(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf.addingTimeInterval(-2 * tag)),
                       "Die App läuft in 2 Tagen ab — am Mac in Xcode neu aufspielen (▶).")
        XCTAssertEqual(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf.addingTimeInterval(-1.5 * tag)),
                       "Die App läuft in 2 Tagen ab — am Mac in Xcode neu aufspielen (▶).")
        XCTAssertEqual(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf.addingTimeInterval(-3600)),
                       "Die App läuft in weniger als einem Tag ab — am Mac in Xcode neu aufspielen (▶).")
        XCTAssertTrue(Bereitstellungsprofil.hinweis(ablauf: ablauf, jetzt: ablauf)?.contains("abgelaufen") ?? false)
    }

    // Entscheid 89: vom versteckten Ort gestartet → Umzug nach «Programme» anbieten.
    func testDerVersteckteOrtWirdErkannt() {
        XCTAssertTrue(Aktualisierung.istVersteckterOrt(
            "/private/var/folders/x/T/AppTranslocation/ABC/d/\(Marke.name).app"))
        XCTAssertFalse(Aktualisierung.istVersteckterOrt("/Applications/\(Marke.name).app"))
        XCTAssertEqual(Aktualisierung.programmeZiel, "/Applications/\(Marke.name).app")
        XCTAssertNotNil(Aktualisierung.pruefeOrt(
            "/private/var/folders/x/T/AppTranslocation/ABC/d/\(Marke.name).app"))
        XCTAssertNil(Aktualisierung.pruefeOrt("/Applications/\(Marke.name).app"))
    }

    // 14.10.2026: erst beenden, dann oeffnen — und danach bestaetigen.
    func testDerNeustartHelferWartetAufDieAlteApp() {
        let befehl = Aktualisierung.neustartBefehl(pid: 4242, buendel: "/Applications/Vis box.app")
        XCTAssertEqual(befehl.first, "/bin/sh")
        XCTAssertEqual(befehl[1], "-c")
        XCTAssertTrue(befehl[2].contains("kill -0"))
        XCTAssertTrue(befehl[2].contains("exec /usr/bin/open \"$2\""))
        XCTAssertFalse(befehl[2].contains("open -n"))
        // Der Pfad geht als eigenes Argument hinein, nie in den Befehlstext.
        XCTAssertFalse(befehl[2].contains("Vis box"))
        XCTAssertEqual(Array(befehl.suffix(2)), ["4242", "/Applications/Vis box.app"])
    }

    func testNachDemNeustartWirdBestaetigtOderGewarnt() throws {
        let neu = try XCTUnwrap(Fassungsnummer("0.2.8"))
        let alt = try XCTUnwrap(Fassungsnummer("0.2.7"))
        XCTAssertNil(Aktualisierung.nachNeustart(erwartet: nil, laufend: neu))
        XCTAssertNil(Aktualisierung.nachNeustart(erwartet: "kaputt", laufend: neu))
        XCTAssertEqual(Aktualisierung.nachNeustart(erwartet: "0.2.8", laufend: neu), .bestaetigt(neu))
        XCTAssertEqual(Aktualisierung.nachNeustart(erwartet: "0.2.8", laufend: alt),
                       .nichtAngekommen(erwartet: neu, laufend: alt))
        XCTAssertEqual(Neustartbefund.bestaetigt(neu).satz, "\(Marke.name) 0.2.8 ist installiert.")
        XCTAssertEqual(Aktualisierung.kleineNummer(neu), "0.2.8")
        XCTAssertEqual(Aktualisierung.kleineNummer(nil), "")
    }
}
