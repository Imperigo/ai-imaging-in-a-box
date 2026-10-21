import Foundation

// DAS IPAD HOLT DIE MAPPE VOM MAC («Visbox eigenstaendig», Schritt 4; Entscheide 103a und 118,
// Plan §11, 21.10.2026).
//
// Ist am Mac eine Mappe offen, beantwortet der Mac die Mappenwege des iPad SELBST aus ihr —
// dieselbe Rolle, die `Knotenquelle` fuer die Knotenansicht spielt. Das iPad merkt davon nichts:
// Es fragt weiter `GET /api/projekt`, `GET /bild?name=` und schickt `POST /api/skizze`; die Wege
// (`Wege.alle`) und ihre Antworten bleiben in der Form des Heim-PC (`server.sicht`,
// `_skizze`). Alles andere reicht der Mac weiter wie bisher.
//
//     Weg des iPad              mit Mappe am Mac                       ohne Mappe am Mac
//     GET  /api/projekt         am Mac: `Macmappensicht.sicht`         Heim-PC
//     GET  /bild?name=          am Mac: nur Namen aus der Sicht        Heim-PC
//     POST /api/skizze          am Mac: `ipad/<stempel>.png` + Eintrag Heim-PC
//     POST /api/rechne(-skizze) am Mac: 409 mit Satz (gerechnet wird    Heim-PC
//                               in der Knotenansicht, Entscheid 94)
//     POST /api/benennen        am Mac: 409 mit Satz                   Heim-PC
//     GET  /api/fortschritt     Heim-PC; erreicht der Mac ihn nicht,   Heim-PC
//                               antwortet er selbst (ruhiger Laufstand)
//     POST /api/abbrechen       Heim-PC                                Heim-PC
//
// Hier steht nur die REINE Regel, unter Linux mit Proben (`MacmappensichtTests`); Lesen und
// Schreiben tut der Mac (`VisboxMac/.../Vermittlung/Ipadmappenquelle.swift`).

/// Eine Skizze, die das iPad **an den Mac** geschickt hat — ein Eintrag in `mappe.json`
/// (`skizzen`), die Datei unter `ipad/`.
public struct Macskizze: Codable, Equatable, Sendable {
    /// Der Name in der Mappe — zugleich ihr Weg: `ipad/skizze-<JJJJMMTT-HHMMSS>-<zusatz>.png`.
    public var name: String
    /// Wann sie ankam (ISO 8601, UTC).
    public var erzeugt: String
    /// Worüber sie gezeichnet ist (ein Name aus der Sicht) — `nil` auf leerem Grund.
    public var ueber: String?
    /// Die Bemerkung des Zeichnenden — die Anweisung, wenn sie am Render-Knoten hängt.
    public var bemerkung: String?
    /// `offen` — wie am Heim-PC (`projekt.SKIZZE_OFFEN`).
    public var stand: String
    /// Der Schlüssel gegen Doppelsendung — **in der Mappe**, nicht nur im Arbeitsspeicher
    /// (am Heim-PC steht er nur dort, `Eingangsbuch`, und ein Neustart vergisst ihn).
    public var schluessel: String?
    public var bytes: Int

    public init(name: String, erzeugt: String, ueber: String?, bemerkung: String?,
                stand: String = Macskizzen.standOffen, schluessel: String?, bytes: Int) {
        self.name = name
        self.erzeugt = erzeugt
        self.ueber = ueber
        self.bemerkung = bemerkung
        self.stand = stand
        self.schluessel = schluessel
        self.bytes = bytes
    }
}

/// Wohin eine Anfrage des iPad am Mac geht, **wenn eine Mappe am Mac offen ist**.
public enum Ipadmappenziel: Equatable, Sendable {
    case projekt
    case bild(name: String)
    case skizze
    /// `rechne` und `rechne-skizze`: gerechnet wird in der Knotenansicht.
    case rechnen
    case benennen
    /// An den Heim-PC — erreicht er ihn nicht, antwortet der Mac mit einem ruhigen Laufstand.
    case fortschritt
}

public enum Ipadmappenwege {
    /// Was mit dieser Anfrage geschieht — `nil`: **weiterreichen wie bisher** (auch, was die
    /// Positivliste gar nicht kennt; das entscheidet danach `Vermittlungsregel`). Verglichen
    /// wird **wörtlich** an Art und Pfad, wie die Positivliste.
    public static func ziel(_ kopf: Anfragekopf) -> Ipadmappenziel? {
        func ist(_ weg: Weg) -> Bool { kopf.methode == weg.methode.rawValue && kopf.pfad == weg.pfad }
        if ist(Wege.projekt) { return .projekt }
        if ist(Wege.skizze) { return .skizze }
        if ist(Wege.rechne) || ist(Wege.rechneSkizze) { return .rechnen }
        if ist(Wege.benennen) { return .benennen }
        if ist(Wege.fortschritt) { return .fortschritt }
        if ist(Wege.bild) { return .bild(name: frage(kopf.ziel, "name") ?? "") }
        return nil
    }

    /// Ein Wert der Frage (`?name=…`), dekodiert — `nil`, wenn er fehlt.
    static func frage(_ ziel: String, _ name: String) -> String? {
        guard let frage = ziel.firstIndex(of: "?") else { return nil }
        for paar in ziel[ziel.index(after: frage)...].split(separator: "&") {
            let teile = paar.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
            guard teile.count == 2, teile[0] == Substring(name) else { continue }
            return String(teile[1]).replacingOccurrences(of: "+", with: " ").removingPercentEncoding
        }
        return nil
    }

    /// Der Satz, wenn das iPad mit einer Mappe am Mac rechnen lassen will.
    public static let satzRechnenAmMac = "Die Mappe liegt am Mac — gerechnet wird dort in der "
        + "Knotenansicht: Knoten «Skizze vom iPad» an den Render-Knoten hängen. Die Skizze liegt "
        + "schon in der Mappe."
    /// Der Satz, wenn das iPad benennen will.
    public static let satzBenennenAmMac = "Die Mappe liegt am Mac — benennen geht dort in der "
        + "Knotenansicht."
    /// Was in den Laufstand kommt, wenn der Mac den Heim-PC nicht erreicht.
    public static let satzOhneHeim = "Der Mac erreicht den Heim-PC gerade nicht — Mappe und "
        + "Skizzen gehen trotzdem, nur gerechnet wird nicht."

    /// Der **ruhige Laufstand**, wenn der Mac mit offener Mappe den Heim-PC nicht erreicht: Es
    /// läuft nichts (das ist wahr: ohne Heim-PC rechnet niemand), und `heim_pc` sagt warum.
    /// Ohne ihn hiesse «Heim-PC weg» am iPad «Mac weg» — dabei liegt die Mappe am Mac.
    public static var fortschrittOhneHeim: JSONWert {
        .objekt([
            "laeuft": .wahrheit(false), "ordner": .null, "seit_s": .null, "knoten": .null,
            "knotenart": .null, "nummer": .null, "von": .null, "knoten_seit_s": .null,
            "schritt": .null, "schritte_gesamt": .null, "art_des_zeichens": .text("unbelegt"),
            "fertige": .liste([]), "ergebnis": .null, "fehler": .null,
            "abbruch_verlangt": .null, "variante": .null, "bestellung": .null,
            "heim_pc": .text("nicht erreicht"), "satz": .text(satzOhneHeim),
        ])
    }

    // ------------------------------------------------- ohne eingerichteten Heim-PC (118a)

    /// Der Satz, wenn am Mac **kein Heim-PC eingerichtet** ist (Entscheid 118a, Frage 3).
    public static let satzKeinRechner = "Kein Rechner eingerichtet — der Mac hat keinen Heim-PC. "
        + "Mappe, Bilder und Skizzen gehen über den Mac; gerechnet wird erst, wenn am Mac ein "
        + "Heim-PC eingerichtet ist."
    /// Der Satz für eine Skizze, wenn am Mac weder eine Mappe offen noch ein Heim-PC da ist.
    public static let satzOhneMappeOhneRechner = "Am Mac ist keine Mappe offen und kein Rechner "
        + "eingerichtet — die Skizze wartet im Parkfach. Am Mac eine Mappe öffnen."
    /// Der Satz für Mappe und Bilder, wenn am Mac weder eine Mappe offen noch ein Heim-PC da ist.
    public static let satzKeineMappeKeinRechner = "Am Mac ist keine Mappe offen und kein Rechner "
        + "eingerichtet — am Mac eine Mappe öffnen."

    /// Der **ruhige Laufstand ohne Heim-PC**: wie `fortschrittOhneHeim`, aber `heim_pc` sagt
    /// «nicht eingerichtet». Das iPad bleibt damit verbunden (der Mac ist ja da) und schickt
    /// seine Skizzen in die Mappe am Mac.
    public static var fortschrittKeinRechner: JSONWert {
        guard case .objekt(var felder) = fortschrittOhneHeim else { return fortschrittOhneHeim }
        felder["heim_pc"] = .text("nicht eingerichtet")
        felder["satz"] = .text(satzKeinRechner)
        return .objekt(felder)
    }

    /// Was der Mac antwortet, wenn **kein Heim-PC eingerichtet** ist und die Mappe am Mac die
    /// Anfrage nicht schon beantwortet hat (Entscheid 118a: die Vermittlung entsteht auch ohne
    /// Heim-PC). Nie «weiterreichen» — es gibt kein Ziel:
    ///
    /// * der Laufstand → ruhig, «nicht eingerichtet» (200);
    /// * Mappe und Bilder ohne offene Mappe → 404, mit dem Satz, was am Mac zu tun ist;
    /// * eine Skizze ohne offene Mappe → 409, sie bleibt im Parkfach;
    /// * alles andere (Rechnen, Benennen, Assistent, was die Positivliste sonst kennt) → 503
    ///   mit «Kein Rechner eingerichtet».
    public static func ohneRechner(_ ziel: Ipadmappenziel?) -> Leitungsantwort {
        switch ziel {
        case .fortschritt?:
            return .json(fortschrittKeinRechner)
        case .projekt?, .bild?:
            return .fehler(satzKeineMappeKeinRechner, status: 404)
        case .skizze?:
            return .fehler(satzOhneMappeOhneRechner, status: 409)
        default:
            return .fehler(satzKeinRechner, status: 503)
        }
    }
}

// ============================================================================ die Sicht

/// Ein Auftrag der Mappe, wie der Mac ihn auf der Platte fand.
public struct Auftragsablage: Equatable, Sendable {
    public let id: String
    /// `bilder/<id>/job.json` — `nil`, wenn er (noch) fehlt.
    public let laufzettel: Data?
    /// Welche Dateien in `bilder/<id>/` liegen.
    public let dateien: Set<String>

    public init(id: String, laufzettel: Data?, dateien: Set<String>) {
        self.id = id
        self.laufzettel = laufzettel
        self.dateien = dateien
    }
}

public enum Macmappensicht {
    /// **Die Felder der Sicht** — eine Teilmenge dessen, was `server.sicht` liefert (bewacht in
    /// `tests/test_ipad_ueber_den_mac.py` gegen eine echte Antwort des Servers), dazu nur
    /// `am_mac`. Der Mac erfindet kein Feld, das das iPad vom Heim-PC nicht kennt.
    public static let felderDerSicht = ["name", "ordner", "stand_nr", "modell", "import",
                                        "einstellungen", "knotenbaum", "knotenbaum_fehler",
                                        "bilder", "skizzen"]
    public static let felderDesBildes = ["bild", "schicht", "zeichen", "satz", "erzeugt",
                                         "vorhanden", "herkunft", "basis"]
    public static let felderDerSkizze = ["skizze", "ueber", "erzeugt", "stand", "bemerkung",
                                         "ergebnis"]
    /// Was der Mac dazusetzt — und nur das.
    public static let eigenesFeld = "am_mac"

    /// Die Endungen, die als Bild gelten (wie `server.BILDTYPEN`, ohne glb).
    public static let bildendungen: Set<String> = [".png", ".jpg", ".jpeg", ".webp"]

    /// Die Antwort auf `GET /api/projekt` aus der Mappe am Mac — **in der Form von
    /// `server.sicht`**, soweit das iPad sie liest (`Projektsicht`), und dazu `erlaubt`: welche
    /// Namen `GET /bild` ausliefern darf und wo sie liegen (Weg in der Mappe).
    ///
    /// * **Bilder:** die fertigen Aufträge (`bilder/<id>/<datei>`, aus `result.images` des
    ///   Laufzettels, nur was da ist) und die Bilder, die beim Holen vom Heim-PC kamen
    ///   (`heim/<weg>` unter ihrem Namen von dort, damit ein `ueber` einer alten Skizze sie
    ///   weiter findet). **Ohne Urteil:** Das Prüfzeichen rechnete der Heim-PC an seiner Mappe;
    ///   am Mac steht keins, und geraten wird nicht.
    /// * **Skizzen:** die vom Heim-PC geholten (`knoten.skizzen`, nur wenn die Datei da ist) und
    ///   die, die das iPad an den Mac schickte (`skizzen`).
    ///
    /// - Parameters:
    ///   - heimDateien: die Wege unter `heim/` (ohne `heim/` davor), wie der Mac sie fand.
    ///   - glbDa: ob `modell.glb` liegt.
    public static func sicht(_ mappe: Macmappe, heimDateien: [String], auftraege: [Auftragsablage],
                             glbDa: Bool, ipadDa: Set<String>) -> (sicht: JSONWert, erlaubt: [String: String]) {
        var erlaubt: [String: String] = [:]
        var bilder: [JSONWert] = []
        var skizzen: [JSONWert] = []

        // DIE GEHOLTEN SKIZZEN zuerst bestimmen — sie stehen nicht unter den Bildern.
        let heimSkizzen = (mappe.knoten?["skizzen"]?.alsListe ?? []).compactMap { e -> (String, JSONWert)? in
            guard let name = e["name"]?.alsText, Mappenkern.sichererWeg(name) != nil,
                  heimDateien.contains(name) else { return nil }
            return (name, e)
        }
        let skizzennamen = Set(heimSkizzen.map { $0.0 })

        for (id, ablage) in auftraege.map({ ($0.id, $0) }) where mappe.auftraege.contains(id) {
            guard let zettel = ablage.laufzettel,
                  let namen = Mappenkern.fertigeBilder(laufzettel: zettel) else { continue }
            let erzeugt = (try? JSONWert.lies(zettel))?["finished_at"]?.alsText
            for datei in namen where ablage.dateien.contains(datei) && istBild(datei) {
                guard let weg = Mappenkern.auftragsweg(id, datei: datei) else { continue }
                erlaubt[weg] = weg
                bilder.append(bildeintrag(weg, erzeugt: erzeugt, herkunft: "auftrag"))
            }
        }
        for datei in heimDateien.sorted() where istBild(datei) && !skizzennamen.contains(datei) {
            // EIN WEG, DEN DIE SICHT ANDERS LAESE (`bilder/vis-…`, `ipad/…`), bleibt weg —
            // sonst zeigte derselbe Name auf zwei Dateien.
            let dort = Mappenkern.heimordner + "/" + datei
            guard Macmappensicht.weg(inDerMappe: datei) == dort else { continue }
            erlaubt[datei] = dort
            bilder.append(bildeintrag(datei, erzeugt: nil, herkunft: "heim-pc"))
        }

        for (name, e) in heimSkizzen {
            erlaubt[name] = Mappenkern.heimordner + "/" + name
            skizzen.append(.objekt([
                "skizze": .text(name), "ueber": e["ueber"] ?? .null, "erzeugt": e["erzeugt"] ?? .null,
                "stand": e["stand"] ?? .text(Macskizzen.standOffen),
                "bemerkung": e["bemerkung"] ?? .null, "ergebnis": .null,
            ]))
        }
        for s in mappe.skizzen ?? [] where ipadDa.contains(s.name) {
            erlaubt[s.name] = s.name
            skizzen.append(skizzeneintrag(s))
        }

        let sicht: JSONWert = .objekt([
            "name": .text(mappe.name),
            "ordner": .text(mappe.name),
            "stand_nr": .null,
            "am_mac": .wahrheit(true),
            "modell": .objekt([
                "pfad": glbDa ? .text(Mappenkern.modelldatei) : .null,
                "stand": .text(glbDa ? "unveraendert" : "fehlt"),
                "grund": glbDa ? .null : .text(Mappenkern.satzOhneModell(mappe.name)),
                "einlass": .objekt([:]),
            ]),
            "import": .objekt([:]),
            "einstellungen": .objekt([:]),
            "knotenbaum": .liste([]),
            "knotenbaum_fehler": .null,
            "bilder": .liste(bilder),
            "skizzen": .liste(skizzen),
        ])
        return (sicht, erlaubt)
    }

    static func istBild(_ name: String) -> Bool {
        guard let punkt = name.lastIndex(of: ".") else { return false }
        return bildendungen.contains(name[punkt...].lowercased())
    }

    /// Wo ein Name der Sicht in der Mappe liegt: ein Auftragsbild unter `bilder/`, eine Skizze
    /// des iPad unter `ipad/`, alles andere unter `heim/`.
    public static func weg(inDerMappe name: String) -> String? {
        guard let sicher = Mappenkern.sichererWeg(name) else { return nil }
        let teile = sicher.split(separator: "/", omittingEmptySubsequences: false).map(String.init)
        if teile.count == 3, teile[0] == Mappenkern.bilderordner,
           Mappenkern.istAuftragskennung(teile[1]), Mappenkern.istFlacherName(teile[2]) {
            return sicher
        }
        if teile.count == 2, teile[0] == Macskizzen.ordner, Mappenkern.istFlacherName(teile[1]) {
            return sicher
        }
        return Mappenkern.heimordner + "/" + sicher
    }

    static func bildeintrag(_ name: String, erzeugt: String?, herkunft: String) -> JSONWert {
        .objekt([
            "bild": .text(name), "schicht": .null, "zeichen": .null, "satz": .null,
            "erzeugt": erzeugt.map(JSONWert.text) ?? .null, "vorhanden": .wahrheit(true),
            "herkunft": .objekt(["am_mac": .text(herkunft)]), "basis": .null,
        ])
    }

    static func skizzeneintrag(_ s: Macskizze) -> JSONWert {
        .objekt([
            "skizze": .text(s.name), "ueber": s.ueber.map(JSONWert.text) ?? .null,
            "erzeugt": .text(s.erzeugt), "stand": .text(s.stand),
            "bemerkung": s.bemerkung.map(JSONWert.text) ?? .null, "ergebnis": .null,
        ])
    }

    /// `GET /bild?name=` am Mac: der Weg in der Mappe — **nur für einen Namen aus der Sicht**
    /// (`erlaubt`), sonst `nil` (404). Dieselbe Regel wie `server.bildpfad`: Was die Mappe
    /// nicht nennt, geht nicht hinaus.
    public static func bildweg(_ name: String, erlaubt: [String: String]) -> String? {
        erlaubt[name]
    }

    /// Der Inhaltstyp nach der Endung.
    public static func inhaltstyp(_ name: String) -> String {
        switch name.split(separator: ".").last.map({ $0.lowercased() }) ?? "" {
        case "png": return "image/png"
        case "jpg", "jpeg": return "image/jpeg"
        case "webp": return "image/webp"
        default: return "application/octet-stream"
        }
    }
}

// ============================================================================ Skizzen ablegen

public enum Macskizzen {
    /// Der Ordner der Skizzen vom iPad in der Mappe.
    public static let ordner = "ipad"
    /// `projekt.SKIZZE_OFFEN`.
    public static let standOffen = "offen"
    /// Wie gross eine Skizze höchstens ist — **wie am Heim-PC** (`SKIZZE_GROESSENRIEGEL`,
    /// bewacht in `tests/test_ipad_geruest.py`).
    public static let hoechstensBytes = 2 * 1024 * 1024
    /// Die Kennung einer PNG-Datei (`server.PNG_KENNUNG`).
    public static let pngKennung: [UInt8] = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]
    /// Höchstens so viele Skizzen merkt sich eine Mappe — die ältesten fallen aus der Liste
    /// (ihre Dateien bleiben liegen).
    public static let hoechstensEintraege = 1000
    /// Wie lang eine Bemerkung höchstens ist.
    public static let bemerkungHoechstens = 2000

    /// Was der Mac mit `POST /api/skizze` tut.
    public enum Ablage: Equatable, Sendable {
        /// Neu: diese Datei schreiben (`eintrag.name` ist ihr Weg), den Eintrag vermerken, dann
        /// `antwort` senden.
        case neu(eintrag: Macskizze, png: Data, antwort: JSONWert)
        /// Derselbe Schlüssel mit derselben Zeichnung — dieselbe Antwort, keine zweite Datei.
        case wiederholung(antwort: JSONWert)
        /// Abgewiesen, mit Satz und Code.
        case abgewiesen(satz: String, status: Int)
    }

    /// Der Hinweis, der mit jeder abgelegten Skizze zurückgeht — **abgelegt ist nicht
    /// gerechnet** (wie `HINWEIS_SKIZZE_OHNE_WEG` am Heim-PC, aber mit dem Weg am Mac).
    public static let hinweis = "In der Mappe am Mac abgelegt, nicht gerechnet. Gerechnet wird "
        + "in der Knotenansicht am Mac (Knoten «Skizze vom iPad»)."

    /// Entscheidet über `POST /api/skizze` — dieselben Felder und Sätze wie am Heim-PC
    /// (`png_base64`, `ueber`, `bemerkung`, `name`, `schluessel`; `ordner` zählt am Mac nicht:
    /// es gilt die offene Mappe).
    ///
    /// - Parameters:
    ///   - gespeichert: liest die Datei einer früheren Skizze (für die Wiederholung).
    ///   - zusatz: ein paar zufällige Zeichen für den Namen (vom Mac gewürfelt).
    public static func lege(_ rumpf: Data, in mappe: Macmappe, jetzt: Date, zusatz: String,
                            gespeichert: (String) -> Data?) -> Ablage {
        guard let wert = try? JSONWert.lies(rumpf), let wunsch = wert.alsObjekt else {
            return .abgewiesen(satz: "Die Anfrage war nicht lesbar.", status: 400)
        }
        guard let roh = wunsch["png_base64"]?.alsText, !roh.isEmpty else {
            return .abgewiesen(satz: "Es fehlt die Zeichnung.", status: 400)
        }
        var schluessel: String?
        if let s = wunsch["schluessel"], !s.istNull {
            guard let t = s.alsText, istSchluessel(t) else {
                return .abgewiesen(satz: "Der Schlüssel gegen Doppelsendung hat 8 bis 128 Zeichen aus "
                                   + "Buchstaben, Ziffern, Punkt, Bindestrich und Unterstrich.", status: 400)
            }
            schluessel = t
        }
        guard let png = Data(base64Encoded: roh) else {
            return .abgewiesen(satz: "Die Zeichnung liess sich nicht lesen — sie kam nicht als "
                               + "gültiges Base64 an.", status: 400)
        }
        guard Array(png.prefix(pngKennung.count)) == pngKennung else {
            return .abgewiesen(satz: "Was ankam, ist kein PNG. Der Mac legt nur ab, was er auch "
                               + "erkennt.", status: 400)
        }
        guard png.count <= hoechstensBytes else {
            return .abgewiesen(satz: "Die Zeichnung ist grösser als \(hoechstensBytes / 1024 / 1024) "
                               + "MiB.", status: 413)
        }
        if let schluessel, let frueher = (mappe.skizzen ?? []).last(where: { $0.schluessel == schluessel }) {
            // DERSELBE SCHLUESSEL: dieselbe Zeichnung → dieselbe Antwort; eine andere → nein.
            // Als Wiederholung behandelt, ginge die zweite Zeichnung still verloren.
            guard gespeichert(frueher.name) == png else {
                return .abgewiesen(satz: "Dieser Schlüssel ist schon mit einer ANDEREN Zeichnung "
                                   + "angekommen. Eine neue Zeichnung braucht einen neuen Schlüssel "
                                   + "— abgelegt wurde nichts.", status: 409)
            }
            return .wiederholung(antwort: antwort(frueher.name, schluessel: schluessel))
        }
        let belegt = Set((mappe.skizzen ?? []).map { $0.name })
        guard let name = freierName(jetzt: jetzt, zusatz: zusatz, belegt: belegt) else {
            return .abgewiesen(satz: "Für diese Sekunde gibt es keinen freien Namen.", status: 500)
        }
        let eintrag = Macskizze(name: name, erzeugt: Mappenliste.jetzt(jetzt),
                                ueber: text(wunsch["ueber"], hoechstens: 512),
                                bemerkung: bemerkung(wunsch["bemerkung"], wunsch["name"]),
                                schluessel: schluessel, bytes: png.count)
        return .neu(eintrag: eintrag, png: png, antwort: antwort(name, schluessel: schluessel))
    }

    /// Den Eintrag in der Mappe vermerken (die Datei liegt schon).
    public static func vermerke(_ eintrag: Macskizze, in mappe: inout Macmappe) {
        var liste = mappe.skizzen ?? []
        liste.append(eintrag)
        if liste.count > hoechstensEintraege { liste.removeFirst(liste.count - hoechstensEintraege) }
        mappe.skizzen = liste
    }

    static func antwort(_ name: String, schluessel: String?) -> JSONWert {
        var o: [String: JSONWert] = ["abgelegt": .wahrheit(true), "skizze": .text(name),
                                     "hinweis": .text(hinweis), "am_mac": .wahrheit(true)]
        if let schluessel { o["schluessel"] = .text(schluessel) }
        return .objekt(o)
    }

    /// `[A-Za-z0-9._-]{8,128}` — wie `SCHLUESSEL_FORM` am Heim-PC.
    public static func istSchluessel(_ s: String) -> Bool {
        (8...128).contains(s.count) && s.unicodeScalars.allSatisfy {
            ("A"..."Z").contains($0) || ("a"..."z").contains($0) || ("0"..."9").contains($0)
                || $0 == "." || $0 == "-" || $0 == "_"
        }
    }

    /// `ipad/skizze-<JJJJMMTT-HHMMSS>-<zusatz>.png`, und wenn belegt mit `-2`, `-3` …
    static func freierName(jetzt: Date, zusatz: String, belegt: Set<String>) -> String? {
        var kalender = Calendar(identifier: .gregorian)
        kalender.timeZone = TimeZone(identifier: "UTC") ?? kalender.timeZone
        let t = kalender.dateComponents([.year, .month, .day, .hour, .minute, .second], from: jetzt)
        let stempel = String(format: "%04d%02d%02d-%02d%02d%02d", t.year ?? 0, t.month ?? 0,
                             t.day ?? 0, t.hour ?? 0, t.minute ?? 0, t.second ?? 0)
        let sauber = String(zusatz.filter { $0.isASCII && ($0.isLetter || $0.isNumber) }.prefix(8)).lowercased()
        let grund = ordner + "/skizze-" + stempel + (sauber.isEmpty ? "" : "-" + sauber)
        if !belegt.contains(grund + ".png") { return grund + ".png" }
        for n in 2...1000 where !belegt.contains(grund + "-\(n).png") {
            return grund + "-\(n).png"
        }
        return nil
    }

    static func text(_ wert: JSONWert?, hoechstens: Int) -> String? {
        guard let t = wert?.alsText?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty
        else { return nil }
        return String(t.prefix(hoechstens))
    }

    /// Die Bemerkung — samt dem Namen, den das iPad der Zeichnung geben wollte, **in der Form
    /// des Heim-PC** (`server._bemerkung`: «<bemerkung> · gewünschter Name: <name>»). Der Name
    /// wird nie Dateiname.
    static func bemerkung(_ bemerkung: JSONWert?, _ name: JSONWert?) -> String? {
        var teile: [String] = []
        if let b = text(bemerkung, hoechstens: bemerkungHoechstens) { teile.append(b) }
        if let n = text(name, hoechstens: 200) { teile.append("gewünschter Name: " + n) }
        return teile.isEmpty ? nil : teile.joined(separator: " · ")
    }
}
