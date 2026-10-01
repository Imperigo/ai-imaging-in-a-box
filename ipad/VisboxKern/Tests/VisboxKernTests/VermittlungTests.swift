import Foundation
import XCTest
import VisboxKern

/// Der Mac als Vermittler (Protokoll §8b): welche Anfrage er selbst beantwortet, welche er
/// abweist und welche er weiterreicht — und dass die App von heute damit zurechtkommt.
final class VermittlungTests: XCTestCase {

    private let zugang = Vermittlerzugang.erzeuge()
    /// Die Anmeldung, die das iPad **am Heim-PC** hätte — sie darf nie durch den Mac gehen.
    private let fremd = Anmeldung(benutzer: "ipad", kennwort: "NICHT-WEITERGEBEN-0123456789abcd")
    /// Die Anmeldung des Mac am Heim-PC (aus seinem Schlüsselbund).
    private let mac = Anmeldung(benutzer: "heim", kennwort: "kennwort-des-mac-am-heim-pc-0123")
    private let heim = URL(string: "https://rechner.netz.invalid:8443")!

    // ------------------------------------------------------------------ Handgriffe

    /// Eine Anfrage des Kerns als Bytes, wie `URLSession` sie schickt — und zurückgelesen.
    private func roh(_ a: Anfrage, zusatz: [Kopfzeile] = []) -> RoheAnfrage {
        var text = "\(a.methode.rawValue) \(a.pfad) HTTP/1.1\r\nHost: mac.invalid:8731\r\n"
        for (n, w) in a.kopfzeilen.sorted(by: { $0.key < $1.key }) { text += "\(n): \(w)\r\n" }
        for k in zusatz { text += "\(k.name): \(k.wert)\r\n" }
        if let r = a.rumpf { text += "Content-Length: \(r.count)\r\n" }
        text += "\r\n"
        var d = Data(text.utf8)
        if let r = a.rumpf { d.append(r) }
        var leser = Anfrageleser()
        guard case .fertig(let gelesen) = leser.nimm(d) else {
            XCTFail("nicht gelesen: \(text)")
            return RoheAnfrage(kopf: Anfragekopf(methode: "GET", ziel: "/"))
        }
        return gelesen
    }

    private func anfrage(_ methode: String, _ ziel: String, auth: String? = nil,
                         koepfe: [Kopfzeile] = [], rumpf: Data = Data()) -> RoheAnfrage {
        var k = koepfe
        if let auth { k.append(Kopfzeile("Authorization", auth)) }
        return RoheAnfrage(kopf: Anfragekopf(methode: methode, ziel: ziel, koepfe: k), rumpf: rumpf)
    }

    private func istTuer(_ v: Vermittlung, file: StaticString = #filePath, line: UInt = #line) {
        guard case .abweisen(let a) = v else { return XCTFail("\(v)", file: file, line: line) }
        XCTAssertEqual(a.status, 401, file: file, line: line)
    }

    // ------------------------------------------------------------------ die Tür

    func testOhneLokaleAnmeldungGehtNichtsWeiter() {
        for weg in Wege.alle {
            for kopplung: Kopplungsstand? in [nil, .abgelaufen, .verbraucht, .aufgebraucht] {
                let a = anfrage(weg.methode.rawValue, weg.pfad)
                if weg == Wege.verbinden && kopplung != nil { continue }
                istTuer(Vermittlungsregel.entscheide(a, zugang: zugang, kopplung: kopplung))
            }
        }
        // AUCH NICHT MIT DER ANMELDUNG FUER DEN HEIM-PC: Die zaehlt am Mac nicht.
        istTuer(Vermittlungsregel.entscheide(anfrage("GET", "/api/fortschritt", auth: fremd.kopfzeile),
                                             zugang: zugang, kopplung: nil))
    }

    /// **Genau die zwei Ausnahmen** — und es sind dieselben, die die App als `ohneAnmeldung`
    /// führt (Protokoll §2).
    func testNurDieZweiAusnahmenKommenOhneAnmeldungDurch() {
        var durch: [Weg] = []
        for weg in Wege.alle {
            let v = Vermittlungsregel.entscheide(anfrage(weg.methode.rawValue, weg.pfad),
                                                 zugang: zugang, kopplung: .offen)
            if case .selbstKoppeln = v { durch.append(weg) }
            if case .weiterreichen = v { XCTFail("unangemeldet weitergereicht: \(weg.pfad)") }
        }
        XCTAssertEqual(Set(durch), Set(Wege.alle.filter(\.ohneAnmeldung)))
        XCTAssertEqual(Set(durch), [Wege.verbinden, Wege.koppeln])
    }

    func testDieKoppelwegeNurInIhrerArtUndNurWennEsPasst() {
        istTuer(Vermittlungsregel.entscheide(anfrage("GET", "/api/verbinden"), zugang: zugang,
                                             kopplung: .offen))
        istTuer(Vermittlungsregel.entscheide(anfrage("POST", "/koppeln"), zugang: zugang,
                                             kopplung: .offen))
        istTuer(Vermittlungsregel.entscheide(anfrage("GET", "/koppeln/"), zugang: zugang,
                                             kopplung: .offen))
        // ABGELAUFEN: das Verbinden kommt an der Tuer vorbei und hoert den Ablehnungssatz —
        // seit dem 01.10.2026 schon am Kopf, ohne Lesen —, die Koppelseite nicht mehr, wie
        // beim Server.
        XCTAssertEqual(Vermittlungsregel.entscheide(anfrage("POST", "/api/verbinden"),
                                                    zugang: zugang, kopplung: .abgelaufen),
                       .abweisen(Vermittlungsregel.koppelAblehnung))
        istTuer(Vermittlungsregel.entscheide(anfrage("GET", "/koppeln"), zugang: zugang,
                                             kopplung: .abgelaufen))
        istTuer(Vermittlungsregel.entscheide(anfrage("POST", "/api/verbinden"), zugang: zugang,
                                             kopplung: nil))
    }

    func testDieTuerSprichtWieDieDesServers() throws {
        let a = Vermittlungsregel.tuer
        XCTAssertEqual(a.status, 401)
        XCTAssertEqual(a.koepfe.wert("WWW-Authenticate"),
                       "Basic realm=\"\(Marke.name)\", charset=\"UTF-8\"")
        XCTAssertEqual(try JSONWert.lies(a.rumpf)["fehler"]?.alsText,
                       "Nicht angemeldet. Benutzername und Kennwort stehen im Fenster, in dem "
                       + "\(Marke.name) gestartet wurde.")
    }

    /// Die Tür entscheidet **am Kopf** — wer nicht angemeldet ist, muss seinen Rumpf nicht
    /// erst schicken.
    func testDieTuerEntscheidetAmKopfAllein() {
        let kopf = Anfragekopf(methode: "POST", ziel: "/api/skizze",
                               koepfe: [Kopfzeile("Content-Length", "3000000")])
        if case .abweisen(let a)? = Vermittlungsregel.vorab(kopf, zugang: zugang, kopplung: .offen) {
            XCTAssertEqual(a.status, 401)
        } else {
            XCTFail("unangemeldet durchgelassen")
        }
        let angemeldet = Anfragekopf(methode: "POST", ziel: "/api/skizze",
                                     koepfe: [Kopfzeile("Authorization", zugang.anmeldung.kopfzeile)])
        XCTAssertNil(Vermittlungsregel.vorab(angemeldet, zugang: zugang, kopplung: nil))
    }

    // ---------------------------------------------------- was weitergeht, und was nie

    /// **Der Kopf des iPad wird nie weitergereicht** — ersetzt, nicht ergänzt.
    func testDieAnmeldungDesIpadGehtNieWeiter() throws {
        let a = anfrage("GET", "/api/projekt?ordner=x", auth: zugang.anmeldung.kopfzeile,
                        koepfe: [Kopfzeile("Proxy-Authorization", fremd.kopfzeile)])
        guard case .weiterreichen(let w) = Vermittlungsregel.entscheide(a, zugang: zugang,
                                                                         kopplung: nil) else {
            return XCTFail()
        }
        XCTAssertNil(w.koepfe.wert("Authorization"))
        XCTAssertNil(w.koepfe.wert("Proxy-Authorization"))
        let hinaus = w.koepfe(mit: mac)
        XCTAssertEqual(hinaus.werte("Authorization"), [mac.kopfzeile], "genau eine: die des Mac")
        for k in hinaus {
            XCTAssertFalse(k.wert.contains(zugang.anmeldung.kopfzeile.dropFirst(6)))
            XCTAssertFalse(k.wert.contains(fremd.kopfzeile.dropFirst(6)))
        }
        XCTAssertEqual(w.ziel, "/api/projekt?ordner=x")
        XCTAssertNil(w.rumpf, "ein GET hat keinen Rumpf")
    }

    func testZweiAnmeldungenSindKeine() {
        let a = anfrage("GET", "/api/fortschritt", auth: zugang.anmeldung.kopfzeile,
                        koepfe: [Kopfzeile("authorization", fremd.kopfzeile)])
        istTuer(Vermittlungsregel.entscheide(a, zugang: zugang, kopplung: nil))
        let b = anfrage("GET", "/api/fortschritt", auth: zugang.anmeldung.kopfzeile,
                        koepfe: [Kopfzeile("Authorization", zugang.anmeldung.kopfzeile)])
        istTuer(Vermittlungsregel.entscheide(b, zugang: zugang, kopplung: nil))
    }

    func testNurErlaubteKoepfeGehenWeiter() throws {
        let alle = [
            Kopfzeile("Accept", "application/json"),
            Kopfzeile("Content-Type", "application/json; charset=utf-8"),
            Kopfzeile("Accept-Language", "de-CH"),
            Kopfzeile("Host", "mac.invalid:8731"),
            Kopfzeile("Connection", "keep-alive, X-Geheim"),
            Kopfzeile("X-Geheim", "1"),
            Kopfzeile("Keep-Alive", "timeout=5"),
            Kopfzeile("Upgrade", "websocket"),
            Kopfzeile("Expect", "100-continue"),
            Kopfzeile("Cookie", "a=b"),
            Kopfzeile("X-Forwarded-For", "192.0.2.1"),
            Kopfzeile("Forwarded", "for=192.0.2.1"),
            Kopfzeile("Tailscale-User-Login", "jemand"),
            Kopfzeile("User-Agent", "Gerät"),
        ]
        let a = anfrage("POST", "/api/skizze", auth: zugang.anmeldung.kopfzeile, koepfe: alle,
                        rumpf: Data("{}".utf8))
        guard case .weiterreichen(let w) = Vermittlungsregel.entscheide(a, zugang: zugang,
                                                                         kopplung: nil) else {
            return XCTFail()
        }
        XCTAssertEqual(Set(w.koepfe.map { $0.name.lowercased() }),
                       ["accept", "content-type", "accept-language"])
        XCTAssertEqual(w.rumpf, Data("{}".utf8))
        XCTAssertEqual(w.methode, "POST")
    }

    func testEinLeererPostBehaeltSeinenLeerenRumpf() {
        let a = anfrage("POST", "/api/abbrechen", auth: zugang.anmeldung.kopfzeile)
        guard case .weiterreichen(let w) = Vermittlungsregel.entscheide(a, zugang: zugang,
                                                                         kopplung: nil) else {
            return XCTFail()
        }
        XCTAssertEqual(w.rumpf, Data())
    }

    /// **`POST /api/verbinden` geht nie zum Heim-PC** — auch angemeldet, auch kodiert.
    /// Sonst bekäme das iPad bei offener Kopplung drüben das Kennwort des Heim-PC.
    func testDieKoppelwegeBeantwortetImmerDerMac() {
        let auth = zugang.anmeldung.kopfzeile
        for kopplung: Kopplungsstand? in [nil, .offen, .verbraucht] {
            // EINE VERBRAUCHTE ZAHL lehnt der Mac schon am Kopf ab — auch das ist «selbst».
            let erwartet: Vermittlung = kopplung == .verbraucht
                ? .abweisen(Vermittlungsregel.koppelAblehnung)
                : .selbstKoppeln(.verbinden)
            XCTAssertEqual(Vermittlungsregel.entscheide(anfrage("POST", "/api/verbinden", auth: auth),
                                                        zugang: zugang, kopplung: kopplung),
                           erwartet)
            XCTAssertEqual(Vermittlungsregel.entscheide(anfrage("POST", "/api/verbinde%6E", auth: auth),
                                                        zugang: zugang, kopplung: kopplung),
                           erwartet)
            XCTAssertEqual(Vermittlungsregel.entscheide(anfrage("GET", "/koppeln?x=1", auth: auth),
                                                        zugang: zugang, kopplung: kopplung),
                           .selbstKoppeln(.koppelseite))
        }
    }

    func testNurGetUndPostGehenWeiter() {
        let auth = zugang.anmeldung.kopfzeile
        for art in ["PUT", "DELETE", "HEAD", "OPTIONS", "CONNECT"] {
            guard case .abweisen(let a) = Vermittlungsregel.entscheide(
                anfrage(art, "/api/projekt", auth: auth), zugang: zugang, kopplung: nil) else {
                return XCTFail(art)
            }
            XCTAssertEqual(a.status, 501, art)
            istTuer(Vermittlungsregel.entscheide(anfrage(art, "/api/projekt"), zugang: zugang,
                                                 kopplung: nil))
        }
    }

    // ------------------------------------------- nur die Wege, die die App ruft

    /// **`;` im Pfad** (Sicherheitsdurchsicht vom 01.10.2026, belegt): `POST
    /// /api/verbinden;x` hielt der Mac nicht für das Verbinden und reichte es mit dem
    /// Kennwort des Heim-PC weiter. Python liest den Pfad mit `urlparse` **ohne** `;x`, prüft
    /// die Zahl gegen seine eigene Kopplung — und gibt bei richtiger Zahl das Kennwort des
    /// Heim-PC zurück. Jetzt geht nur weiter, was **wörtlich** auf der Positivliste steht.
    func testEinStrichpunktImPfadGehtNichtZumHeimPc() {
        let auth = zugang.anmeldung.kopfzeile
        for ziel in ["/api/verbinden;x", "/api/verbinden;", "/api/verbinden/;x", "/koppeln;x",
                     "/api/projekt;x", "/api/skizze;a=b", "/bild;x?name=a.png",
                     "/api/verbinde%6E;x", "/api/proj%65kt", "/api/projekt%3Bx", "/API/projekt",
                     "/api/projekt/", "/api//projekt", "/api/./projekt", "/api/x/../projekt"] {
            for art in ["GET", "POST"] {
                for kopplung: Kopplungsstand? in [nil, .offen] {
                    let v = Vermittlungsregel.entscheide(
                        anfrage(art, ziel, auth: auth, rumpf: Data(#"{"pin":"042917"}"#.utf8)),
                        zugang: zugang, kopplung: kopplung)
                    if case .weiterreichen = v { XCTFail("weitergereicht: \(art) \(ziel)") }
                }
            }
        }
        guard case .abweisen(let a) = Vermittlungsregel.entscheide(
            anfrage("POST", "/api/verbinden;x", auth: auth), zugang: zugang, kopplung: .offen) else {
            return XCTFail()
        }
        XCTAssertEqual(a.status, 404, "der Mac antwortet selbst, und zwar mit «gibt es nicht»")
    }

    /// Weiter geht **genau** die Positivliste, mit Frage und ohne; alles andere aus
    /// `Wege.alle` beantwortet der Mac mit 404 (oder selbst, die zwei Koppelwege).
    func testNurDiePositivlisteGehtWeiter() {
        let auth = zugang.anmeldung.kopfzeile
        var weiter: Set<Weg> = []
        for weg in Wege.alle {
            for ziel in [weg.pfad, weg.pfad + "?ordner=x"] {
                switch Vermittlungsregel.entscheide(anfrage(weg.methode.rawValue, ziel, auth: auth),
                                                    zugang: zugang, kopplung: nil) {
                case .weiterreichen(let w):
                    XCTAssertEqual(w.ziel, ziel)
                    weiter.insert(weg)
                case .abweisen(let a):
                    XCTAssertEqual(a.status, weg.ohneAnmeldung ? 403 : 404, ziel)
                case .selbstKoppeln:
                    XCTAssertTrue(weg.ohneAnmeldung, ziel)
                }
            }
        }
        XCTAssertEqual(weiter, Set(Vermittlungsregel.weiterreichbar))
        XCTAssertEqual(weiter, [Wege.projekt, Wege.fortschritt, Wege.bild, Wege.skizze,
                                Wege.rechne, Wege.rechneSkizze, Wege.benennen, Wege.abbrechen])
        // DIE ART GEHOERT DAZU: `GET /api/skizze` ist nicht `POST /api/skizze`.
        guard case .abweisen(let a) = Vermittlungsregel.entscheide(
            anfrage("GET", "/api/skizze", auth: auth), zugang: zugang, kopplung: nil) else {
            return XCTFail()
        }
        XCTAssertEqual(a.status, 404)
        // UND WEGE, DIE DIE APP GAR NICHT KENNT: die Knotenansicht, die Brücke.
        for ziel in ["/knoten", "/knoten/mappe", "/bruecke/jobs", "/favicon.ico"] {
            for art in ["GET", "POST"] {
                if case .weiterreichen = Vermittlungsregel.entscheide(
                    anfrage(art, ziel, auth: auth), zugang: zugang, kopplung: nil) {
                    XCTFail("\(art) \(ziel)")
                }
            }
        }
    }

    /// **Jeder Weg ist entschieden:** weitergereicht oder bewusst nicht. Kommt in `Wege.alle`
    /// ein neuer dazu, fällt diese Probe, bis jemand ihn einer der zwei Listen zuordnet.
    func testJederWegIstWeitergereichtOderBewusstNicht() {
        let weiter = Set(Vermittlungsregel.weiterreichbar)
        let nicht = Set(Vermittlungsregel.nichtWeitergereicht)
        XCTAssertTrue(weiter.isDisjoint(with: nicht))
        XCTAssertEqual(weiter.union(nicht), Set(Wege.alle))
        XCTAssertFalse(weiter.contains(Wege.verbinden))
        XCTAssertFalse(weiter.contains(Wege.koppeln))
        XCTAssertTrue(weiter.allSatisfy { !$0.ohneAnmeldung })
    }

    // ------------------------------------------------- die Koppelwege, klein und kurz

    /// **Ein Fremder schickt keine vier Megabyte an das Verbinden** (Sicherheitsdurchsicht
    /// vom 01.10.2026, belegt): Unangemeldet kam `POST /api/verbinden` bis 4 MiB durch, auch
    /// bei toter Zahl, und das JSON wurde auf dem Hauptfaden gelesen. Jetzt sagt schon der
    /// Kopf: mehr als 1 KiB ist kein Koppeln.
    func testDieKoppelwegeNehmenAmKopfHoechstensEinKiB() throws {
        let gross = String(Vermittlungsregel.koppelRumpfGrenze + 1)
        let auth = zugang.anmeldung.kopfzeile
        for (art, pfad) in [("POST", "/api/verbinden"), ("GET", "/koppeln")] {
            for a in [nil, auth] {
                var k = [Kopfzeile("Content-Length", gross)]
                if let a { k.append(Kopfzeile("Authorization", a)) }
                let v = Vermittlungsregel.vorab(Anfragekopf(methode: art, ziel: pfad, koepfe: k),
                                                zugang: zugang, kopplung: .offen)
                guard case .abweisen(let antwort)? = v else { return XCTFail("\(art) \(pfad)") }
                XCTAssertEqual(antwort.status, 413, "\(art) \(pfad)")
            }
        }
        let genug = Anfragekopf(methode: "POST", ziel: "/api/verbinden", koepfe: [
            Kopfzeile("Content-Length", String(Vermittlungsregel.koppelRumpfGrenze))])
        XCTAssertNil(Vermittlungsregel.vorab(genug, zugang: zugang, kopplung: .offen))
        // DIE BAUFORM DER APP PASST LOCKER HINEIN.
        let app = try Anfragen.verbinden(XCTUnwrap(Kopplungszahl("042917")))
        XCTAssertLessThan(app.rumpf?.count ?? 0, Vermittlungsregel.koppelRumpfGrenze / 8)
        // ANDERE WEGE BEHALTEN IHRE GRENZE: Eine Skizze geht angemeldet weiter.
        let skizze = Anfragekopf(methode: "POST", ziel: "/api/skizze", koepfe: [
            Kopfzeile("Content-Length", "3000000"), Kopfzeile("Authorization", auth)])
        XCTAssertNil(Vermittlungsregel.vorab(skizze, zugang: zugang, kopplung: nil))
    }

    /// **Eine tote Zahl wird am Kopf abgelehnt**, ohne dass ein Byte des Rumpfs gelesen ist —
    /// mit dem gleichbleibenden Satz, den das Gerät auch sonst hört (Protokoll §7).
    func testEineToteZahlWirdAmKopfAbgelehntOhneLesen() throws {
        for tot: Kopplungsstand in [.abgelaufen, .aufgebraucht, .verbraucht] {
            for a in [nil, zugang.anmeldung.kopfzeile] {
                var k = [Kopfzeile("Content-Length", "16")]
                if let a { k.append(Kopfzeile("Authorization", a)) }
                let v = Vermittlungsregel.vorab(Anfragekopf(methode: "POST", ziel: "/api/verbinden",
                                                            koepfe: k),
                                                zugang: zugang, kopplung: tot)
                guard case .abweisen(let antwort)? = v else { return XCTFail("\(tot)") }
                XCTAssertEqual(antwort.status, 403)
                XCTAssertEqual(try Kopplungsergebnis.lies(status: antwort.status, daten: antwort.rumpf),
                               .abgelehnt(satz: Vermittlerkopplung.satzFuerDasGeraet))
            }
        }
        // AM STAND: Der Mensch am Mac erfährt trotzdem, woran es lag.
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        XCTAssertEqual(stand.vorab(Anfragekopf(methode: "POST", ziel: "/api/verbinden",
                                               koepfe: [Kopfzeile("Content-Length", "16")]),
                                   jetzt: 700)?.status, 403)
        XCTAssertEqual(stand.letzterKoppelgrund,
                       Vermittlerkopplung.grundAbgelaufen + " (noch 5 Versuche)")
    }

    // --------------------------------------------------------- die Adresse drüben

    func testDieAdresseZeigtAufDenHeimPcUndNurDorthin() throws {
        let w = Weiterreichung(methode: "GET", ziel: "/bild?name=a%2Bb.png&ordner=x", koepfe: [],
                               rumpf: nil)
        XCTAssertEqual(w.adresse(heimBasis: heim)?.absoluteString,
                       "https://rechner.netz.invalid:8443/bild?name=a%2Bb.png&ordner=x")
        XCTAssertEqual(w.adresse(heimBasis: URL(string: "https://rechner.netz.invalid:8443/")!)?
                        .absoluteString,
                       "https://rechner.netz.invalid:8443/bild?name=a%2Bb.png&ordner=x")
        for ziel in ["//anders.invalid/x", "http://anders.invalid/", "@anders.invalid/x",
                     "/x#y", "x", ""] {
            XCTAssertNil(Weiterreichung(methode: "GET", ziel: ziel, koepfe: [], rumpf: nil)
                            .adresse(heimBasis: heim), ziel)
        }
    }

    // --------------------------------------------------- die Antwort des Heim-PC

    func testDieAntwortGehtZurueckMitDenErlaubtenKoepfen() throws {
        let a = try XCTUnwrap(Vermittlungsregel.antwort(auf: .antwort(
            status: 200,
            koepfe: [Kopfzeile("Content-Type", "image/png"),
                     Kopfzeile("Cache-Control", "no-store"),
                     Kopfzeile("Set-Cookie", "a=b"),
                     Kopfzeile("Content-Encoding", "gzip"),
                     Kopfzeile("WWW-Authenticate", "Basic"),
                     Kopfzeile("Server", "drüben"),
                     Kopfzeile("Location", "https://rechner.netz.invalid:8443/knoten/")],
            rumpf: Data([1, 2, 3]))))
        XCTAssertEqual(a.status, 200)
        XCTAssertEqual(a.rumpf, Data([1, 2, 3]))
        XCTAssertEqual(a.koepfe, [Kopfzeile("Content-Type", "image/png"),
                                  Kopfzeile("Cache-Control", "no-store")])
        let weiter = try XCTUnwrap(Vermittlungsregel.antwort(auf: .antwort(
            status: 301, koepfe: [Kopfzeile("Location", "/knoten/")], rumpf: Data())))
        XCTAssertEqual(weiter.koepfe.wert("Location"), "/knoten/", "ein Pfad am selben Rechner")
    }

    /// Eine 401 **des Heim-PC** heisst: Das Kennwort des Mac passt drüben nicht. Am iPad
    /// darf daraus nicht «neu koppeln» werden.
    func testEine401DesHeimPcWirdKeine401AmIpad() throws {
        let a = try XCTUnwrap(Vermittlungsregel.antwort(auf: .antwort(
            status: 401, koepfe: [Kopfzeile("WWW-Authenticate", "Basic")], rumpf: Data())))
        XCTAssertEqual(a.status, 403)
        XCTAssertNil(a.koepfe.wert("WWW-Authenticate"))
        let f = Serverfehler.aus(a)
        XCTAssertNotEqual(f.art, .nichtAngemeldet, "das iPad sagte sonst «neu koppeln»")
        XCTAssertTrue(f.satz.contains("Kennwort des Mac"))
    }

    /// **Nicht erreicht heisst am iPad: zurück ins Parkfach**, nicht «abgewiesen» — die App
    /// von heute kennt das nur bei 401/403.
    func testNichtErreichtLegtDieSkizzeZurueckInsFach() throws {
        let a = try XCTUnwrap(Vermittlungsregel.antwort(auf: .nichtErreicht(
            grund: "Die Leitung nach Hause steht nicht.")))
        XCTAssertEqual(a.status, 403)
        guard case .nichtAngemeldet(let grund) = Sendeergebnis.aus(status: a.status, daten: a.rumpf) else {
            return XCTFail("die Skizze gälte als abgewiesen")
        }
        XCTAssertTrue(grund.contains("erreicht aber den Heim-PC nicht"))
        XCTAssertTrue(grund.contains("Die Leitung nach Hause steht nicht."))
        // Und das Pruefen der App zeigt den Satz, statt «neu koppeln» zu verlangen.
        XCTAssertThrowsError(try Fortschrittsstand.lies(status: a.status, daten: a.rumpf)) { e in
            XCTAssertEqual((e as? Serverfehler)?.art, .verweigert)
        }
    }

    func testUngewissBekommtKeineAntwort() {
        XCTAssertNil(Vermittlungsregel.antwort(auf: .ungewiss(grund: "abgerissen")))
    }

    func testOhneAntwortEntscheidenArtUndBytes() {
        XCTAssertEqual(Heimergebnis.ohneAntwort(grund: "g", methode: "GET", bytesHinaus: 99,
                                                leitungStand: true),
                       .nichtErreicht(grund: "g"), "ein GET ändert drüben nichts")
        XCTAssertEqual(Heimergebnis.ohneAntwort(grund: "g", methode: "POST", bytesHinaus: 0,
                                                leitungStand: false),
                       .nichtErreicht(grund: "g"))
        XCTAssertEqual(Heimergebnis.ohneAntwort(grund: "g", methode: "POST", bytesHinaus: 1,
                                                leitungStand: false),
                       .ungewiss(grund: "g"))
    }

    /// **Ein POST ohne Rumpf kann angekommen sein** (Sicherheitsdurchsicht vom 01.10.2026):
    /// `POST /api/abbrechen` hat keinen Rumpf, und gezählt wurden nur Rumpf-Bytes — er galt
    /// darum immer als «nicht erreicht», auch wenn der Kopf drüben angekommen war und der
    /// Lauf schon anhielt. Stand die Leitung, ist es ungewiss.
    func testEinLeererPostIstUngewissSobaldDieLeitungStand() {
        XCTAssertEqual(Heimergebnis.ohneAntwort(grund: "g", methode: "POST", bytesHinaus: 0,
                                                leitungStand: true),
                       .ungewiss(grund: "g"))
        XCTAssertEqual(Heimergebnis.ohneAntwort(grund: "g", methode: "GET", bytesHinaus: 0,
                                                leitungStand: true),
                       .nichtErreicht(grund: "g"))
    }

    // ------------------------------------------- die App von heute, gegen den Mac

    /// **Die App findet und benutzt den Mac ohne Änderung:** Sie koppelt mit ihrer eigenen
    /// Bauform (`Anfragen.verbinden`), liest die Antwort mit ihrem eigenen Leser
    /// (`Kopplungsergebnis.lies`) — und bekommt die Zugangsdaten des Mac, nicht die des
    /// Heim-PC. Danach geht ihre gewöhnliche Anfrage weiter, mit dem Kopf des Mac.
    func testDieAppKoppeltMitDemMacWieMitDerHomeStation() throws {
        var stand = Vermittlerstand(zugang: zugang)
        XCTAssertTrue(stand.oeffneKopplung(jetzt: 10, zahl: "042917"))
        XCTAssertEqual(stand.koppelzahl(jetzt: 10), "042917")

        let koppeln = try Anfragen.verbinden(XCTUnwrap(Kopplungszahl("042917")))
        guard case .antworte(let a) = stand.beantworte(roh(koppeln), jetzt: 20) else {
            return XCTFail()
        }
        XCTAssertEqual(a.status, 200)
        guard case .verbunden(let anmeldung?, let satz) = try Kopplungsergebnis.lies(
            status: a.status, daten: a.rumpf) else { return XCTFail() }
        XCTAssertEqual(anmeldung, zugang.anmeldung)
        XCTAssertNotEqual(anmeldung.kennwort, mac.kennwort, "nie das Kennwort des Heim-PC")
        XCTAssertEqual(satz, Vermittlerstand.satzVerbunden)
        XCTAssertNil(stand.koppelzahl(jetzt: 21), "nach Erfolg verbraucht")
        XCTAssertEqual(stand.erfolgreicheKopplungen, 1)

        let fragen = Anfragen.fortschritt(anmeldung: anmeldung)
        guard case .weiterreichen(let w) = stand.beantworte(roh(fragen), jetzt: 30) else {
            return XCTFail()
        }
        XCTAssertEqual(w.methode, "GET")
        XCTAssertEqual(w.ziel, Wege.fortschritt.pfad)
        XCTAssertEqual(w.koepfe(mit: mac).werte("Authorization"), [mac.kopfzeile])
        XCTAssertEqual(stand.letzteAnfrage, 30)

        // UND EINE SKIZZE AUS DEM PARKFACH, MIT IHREM SCHLUESSEL, GEHT UNVERAENDERT WEITER.
        let skizze = try Anfragen.skizze(png: Data([0x89, 0x50, 0x4E, 0x47]), schluessel: "a1b2c3d4e5",
                                         anmeldung: anmeldung)
        guard case .weiterreichen(let s) = stand.beantworte(roh(skizze), jetzt: 31) else {
            return XCTFail()
        }
        XCTAssertEqual(s.rumpf, skizze.rumpf)
        XCTAssertEqual(s.koepfe.wert("Content-Type"), "application/json; charset=utf-8")
    }

    func testEineFalscheZahlHoertDenSatzUndDerMacDenGrund() throws {
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        let falsch = try Anfragen.verbinden(XCTUnwrap(Kopplungszahl("111111")))
        guard case .antworte(let a) = stand.beantworte(roh(falsch), jetzt: 1) else { return XCTFail() }
        XCTAssertEqual(a.status, 403)
        XCTAssertEqual(try Kopplungsergebnis.lies(status: a.status, daten: a.rumpf),
                       .abgelehnt(satz: Vermittlerkopplung.satzFuerDasGeraet))
        XCTAssertEqual(stand.letzterKoppelgrund, "Die Zahl stimmt nicht. (noch 4 Versuche)")
        XCTAssertNil(stand.letzteAnfrage, "eine abgelehnte Zahl ist keine Verbindung")
        XCTAssertEqual(stand.erfolgreicheKopplungen, 0)
        XCTAssertFalse(String(decoding: a.rumpf, as: UTF8.self).contains(zugang.anmeldung.kennwort))
    }

    func testNachFuenfFehlversuchenHilftDieRichtigeNicht() throws {
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        let falsch = roh(try Anfragen.verbinden(XCTUnwrap(Kopplungszahl("111111"))))
        for _ in 0..<5 { _ = stand.beantworte(falsch, jetzt: 1) }
        let richtig = roh(try Anfragen.verbinden(XCTUnwrap(Kopplungszahl("042917"))))
        guard case .antworte(let a) = stand.beantworte(richtig, jetzt: 2) else { return XCTFail() }
        XCTAssertEqual(a.status, 403)
        XCTAssertNil(stand.koppelzahl(jetzt: 2))
        // UND DIE KOPPELSEITE IST WIEDER HINTER DER TUER.
        guard case .antworte(let seite) = stand.beantworte(anfrage("GET", "/koppeln"), jetzt: 3) else {
            return XCTFail()
        }
        XCTAssertEqual(seite.status, 401)
    }

    func testEinUnlesbarerRumpfKostetKeinenVersuch() {
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        guard case .antworte(let a) = stand.beantworte(
            anfrage("POST", "/api/verbinden", rumpf: Data("{kaputt".utf8)), jetzt: 1) else {
            return XCTFail()
        }
        XCTAssertEqual(a.status, 400)
        XCTAssertEqual(stand.kopplung?.versucheUebrig, 5)
    }

    func testAngemeldetOhneKopplungIstKeinVerbindenOffen() throws {
        var stand = Vermittlerstand(zugang: zugang)
        guard case .antworte(let a) = stand.beantworte(
            anfrage("POST", "/api/verbinden", auth: zugang.anmeldung.kopfzeile,
                    rumpf: Data(#"{"pin":"042917"}"#.utf8)), jetzt: 1) else { return XCTFail() }
        XCTAssertEqual(a.status, 403)
        guard case .antworte(let seite) = stand.beantworte(
            anfrage("GET", "/koppeln", auth: zugang.anmeldung.kopfzeile), jetzt: 1) else {
            return XCTFail()
        }
        XCTAssertEqual(seite.status, 404)
    }

    func testDieKoppelseiteGibtEsNurSolangeDieZahlGilt() throws {
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "042917")
        guard case .antworte(let a) = stand.beantworte(anfrage("GET", "/koppeln"), jetzt: 1) else {
            return XCTFail()
        }
        XCTAssertEqual(a.status, 200)
        XCTAssertEqual(a.koepfe.wert("Cache-Control"), "no-store")
        let html = String(decoding: a.rumpf, as: UTF8.self)
        XCTAssertTrue(html.contains("/api/verbinden"))
        XCTAssertFalse(html.contains("042917"), "die Zahl steht nur am Mac")
        guard case .antworte(let spaet) = stand.beantworte(anfrage("GET", "/koppeln"), jetzt: 600) else {
            return XCTFail()
        }
        XCTAssertEqual(spaet.status, 401)
    }

    func testDasIpadVergessenSperrtDieAlteAnmeldung() {
        var stand = Vermittlerstand(zugang: zugang)
        let alt = zugang.anmeldung.kopfzeile
        stand.ersetzeZugang(Vermittlerzugang.erzeuge())
        guard case .antworte(let a) = stand.beantworte(anfrage("GET", "/api/fortschritt", auth: alt),
                                                       jetzt: 1) else { return XCTFail() }
        XCTAssertEqual(a.status, 401)
    }

    func testDieTuerDesStandsAmKopf() {
        var stand = Vermittlerstand(zugang: zugang)
        XCTAssertEqual(stand.vorab(Anfragekopf(methode: "POST", ziel: "/api/skizze"), jetzt: 0)?.status,
                       401)
        XCTAssertEqual(stand.vorab(Anfragekopf(methode: "POST", ziel: "/api/verbinden"), jetzt: 0)?
                        .status, 401, "keine Kopplung, also Tür")
        stand.oeffneKopplung(jetzt: 0)
        XCTAssertNil(stand.vorab(Anfragekopf(methode: "POST", ziel: "/api/verbinden"), jetzt: 1))
    }

    // --------------------------------------------------------- die Zeile «iPad»

    func testDieZeileSagtWasIst() {
        var stand = Vermittlerstand(zugang: zugang)
        XCTAssertEqual(Vermittlerlage.bestimme(bereit: false, fehler: nil, stand: stand, jetzt: 0),
                       .startet)
        XCTAssertEqual(Vermittlerlage.bestimme(bereit: true, fehler: nil, stand: stand, jetzt: 0),
                       .wartet(letzteAnfrageVor: nil))
        let fehlt = Vermittlerlage.bestimme(bereit: true, fehler: "Lokales Netzwerk nicht erlaubt.",
                                            stand: stand, jetzt: 0)
        XCTAssertEqual(fehlt.wort, "fehlt")
        XCTAssertEqual(fehlt.satz, "Lokales Netzwerk nicht erlaubt.")

        stand.oeffneKopplung(jetzt: 100, zahl: "042917")
        let koppeln = Vermittlerlage.bestimme(bereit: true, fehler: nil, stand: stand, jetzt: 130)
        XCTAssertEqual(koppeln, .koppeln(zahl: "042917", nochSekunden: 570))
        XCTAssertEqual(koppeln.wort, "wartet")
        XCTAssertTrue(koppeln.satz.contains("042 917"))
        XCTAssertTrue(koppeln.satz.contains("10 min"))

        _ = stand.beantworte(roh(try! Anfragen.verbinden(Kopplungszahl("042917")!)), jetzt: 140)
        let verbunden = Vermittlerlage.bestimme(bereit: true, fehler: nil, stand: stand, jetzt: 144)
        XCTAssertEqual(verbunden, .verbunden(letzteAnfrageVor: 4))
        XCTAssertEqual(verbunden.wort, "steht")
        XCTAssertEqual(verbunden.satz, "Verbunden, letzte Anfrage vor 4 s.")

        let still = Vermittlerlage.bestimme(bereit: true, fehler: nil, stand: stand, jetzt: 140 + 180)
        XCTAssertEqual(still, .wartet(letzteAnfrageVor: 180))
        XCTAssertEqual(still.satz, "Wartet auf das iPad. Letzte Anfrage vor 3 min.")
    }

    /// **Ausdrücklich eingeschaltet** (Sicherheitsdurchsicht vom 01.10.2026): Ist «iPad über
    /// diesen Mac anbieten» aus, sagt die Zeile das — vor jedem anderen Zustand, auch vor
    /// einer geltenden Zahl, weil dann niemand sie erreicht.
    func testAusgeschaltetSagtDieZeileWieManEinschaltet() {
        var stand = Vermittlerstand(zugang: zugang)
        stand.oeffneKopplung(jetzt: 0, zahl: "123456")
        let aus = Vermittlerlage.bestimme(angeboten: false, bereit: true, fehler: "x",
                                          stand: stand, jetzt: 1)
        XCTAssertEqual(aus, .aus)
        XCTAssertEqual(aus.satz, "Aus — im Menü «iPad» einschalten, wenn ein iPad mitkommt.")
        XCTAssertEqual(aus.alsZeilenstand(), .wartet(satz: aus.satz))
        XCTAssertFalse(aus.satz.contains("123"), "eine Zahl, die niemand erreicht, steht nicht da")
        XCTAssertEqual(Vermittlerlage.bestimme(angeboten: true, bereit: true, fehler: nil,
                                               stand: stand, jetzt: 1),
                       .koppeln(zahl: "123456", nochSekunden: 599))
    }

    func testEineGeltendeZahlGehtVorVerbunden() {
        var stand = Vermittlerstand(zugang: zugang)
        _ = stand.beantworte(anfrage("GET", "/api/fortschritt", auth: zugang.anmeldung.kopfzeile),
                             jetzt: 10)
        stand.oeffneKopplung(jetzt: 11, zahl: "123456")
        guard case .koppeln = Vermittlerlage.bestimme(bereit: true, fehler: nil, stand: stand,
                                                      jetzt: 12) else { return XCTFail() }
    }

    // ------------------------------------------------------------- das Anbieten

    func testDasIpadErkenntDenMacAmEintrag() {
        let eintraege = GefundenerDienst.txtEintraege(Vermittlerangebot.txt)
        XCTAssertEqual(eintraege, ["fassung": "1", "vermittler": "mac"])
        let ueberMac = GefundenerDienst(name: "m", rechner: "192.0.2.5", anschluss: 8731,
                                        eintraege: eintraege)
        XCTAssertTrue(ueberMac.ueberDenMac)
        XCTAssertEqual(ueberMac.fassung, "1")
        XCTAssertFalse(GefundenerDienst(name: "h", rechner: nil, anschluss: nil,
                                        eintraege: ["fassung": "1"]).ueberDenMac)
        XCTAssertTrue(GefundenerDienst(name: "h", rechner: nil, anschluss: nil,
                                       eintraege: ["Vermittler": "MAC"]).ueberDenMac)
        XCTAssertFalse(GefundenerDienst(name: "h", rechner: nil, anschluss: nil,
                                        eintraege: ["vermittler": "anderer"]).ueberDenMac)
    }

    func testDerNamePasstInEinenDnsTeil() {
        let lang = Vermittlerangebot.dienstname(rechner: String(repeating: "Ä", count: 80))
        XCTAssertLessThanOrEqual(lang.utf8.count, 63)
        XCTAssertTrue(lang.hasPrefix(Marke.name + " über "))
        XCTAssertEqual(Vermittlerangebot.dienstname(rechner: "Mac"), Marke.name + " über Mac")
    }

    // ------------------------------------------------------ in die Startzeile

    func testDieLageWirdZurZeileIpadMitDemselbenSatz() {
        let faelle: [(Vermittlerlage, String)] = [
            (.startet, "wartet"), (.wartet(letzteAnfrageVor: nil), "wartet"),
            (.koppeln(zahl: "123456", nochSekunden: 90), "wartet"),
            (.verbunden(letzteAnfrageVor: 4), "steht"), (.fehlt(grund: "Kein WLAN."), "fehlt"),
        ]
        for (lage, wort) in faelle {
            let zeile = lage.alsZeilenstand()
            XCTAssertEqual(zeile.wort, wort, "\(lage)")
            XCTAssertEqual(zeile.satz, lage.satz, "der Satz geht unverändert mit: \(lage)")
        }
        XCTAssertTrue(Vermittlerlage.koppeln(zahl: "123456", nochSekunden: 90)
                        .alsZeilenstand().satz.contains("123 456"),
                      "die Zahl muss am Mac zu lesen sein")
    }
}

private extension Serverfehler {
    static func aus(_ a: Leitungsantwort) -> Serverfehler {
        do {
            _ = try liesAntwort(status: a.status, daten: a.rumpf)
        } catch let f as Serverfehler {
            return f
        } catch {}
        return Serverfehler(code: a.status, satz: "", satzVomServer: false)
    }
}
