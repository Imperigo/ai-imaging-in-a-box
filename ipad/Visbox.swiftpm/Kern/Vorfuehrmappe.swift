import Foundation

// DIE VORFUEHRMAPPE — vorher gerechnete Bilder fuer den Vorfuehrmodus (Plan v0.1.7, Strom C1;
// Entscheide 40 und 49; Blatt 13b der Entwurfsflaeche).
//
// Antwortet der Heim-PC nicht, zeigt die Mac-App Bilder, die vorher gerechnet wurden. Sie
// liegen als Ordner im App-Buendel: `vorfuehrmappe.json` und die PNG daneben, erzeugt von
// `tools/vorfuehrmappe.py` (Schema `visbox.vorfuehrmappe/v1`, dort beschrieben).
//
// DAS ZEICHEN ENTSTEHT WIE LIVE. Je Bild traegt die Mappe unter `flaeche` die Felder, die
// `GET /api/projekt` je Bild liefert; gelesen werden sie mit `Mappenbild`, und das Zeichen
// macht `Mappenbild.pruefzeichen` — dieselben zwei Stellen wie im Bildband der iPad-App.
// Ein Bild traegt im Vorfuehrmodus darum dasselbe Zeichen wie live, ohne dass hier etwas
// nachgebaut ist. Bewacht in `VorfuehrmappeTests.testDasZeichenIstDasDerFlaeche`.
//
// Drei Zusagen, jede mit Probe in `VorfuehrmappeTests`:
//   1. Ein unbekanntes Schema wird NICHT versuchsweise gelesen (benannter Fehler) — was
//      dabei fehlte, fiele niemandem auf.
//   2. Eine fehlende Bilddatei bringt nichts zu Fall: Das Bild steht mit dem Satz da, dass
//      seine Datei fehlt.
//   3. Ein Dateiname ist ein Name und kein Weg — ein Eintrag mit Pfad wird abgewiesen
//      (Regel 3, und eine Mappe soll nicht aus ihrem Ordner herauszeigen koennen).

/// Ein Kalendertag, wie die Mappe ihn schreibt (`JJJJ-MM-TT`) — **ohne Uhrzeit und ohne
/// Zeitzone**, damit «gerechnet am 28.10.» an jedem Ort derselbe Tag ist.
public struct Kalendertag: Equatable, Hashable, Comparable, Sendable {
    public let jahr: Int
    public let monat: Int
    public let tag: Int

    /// Aus `JJJJ-MM-TT` oder dem Anfang einer Zeit des Servers (`JJJJ-MM-TTTHH:…`).
    /// Alles andere gibt `nil` — **kein geratener Tag.**
    public init?(_ roh: String?) {
        guard let roh = roh, roh.count >= 10 else { return nil }
        let kopf = Array(roh.prefix(10))
        guard kopf[4] == "-", kopf[7] == "-",
              roh.count == 10 || roh.dropFirst(10).first == "T",
              let j = Int(String(kopf[0..<4])), let m = Int(String(kopf[5..<7])),
              let t = Int(String(kopf[8..<10])),
              (1...12).contains(m), (1...31).contains(t) else { return nil }
        jahr = j
        monat = m
        tag = t
    }

    /// «28.10.»
    public var kurz: String { String(format: "%02d.%02d.", tag, monat) }
    /// «28.10.2026»
    public var lang: String { String(format: "%02d.%02d.%04d", tag, monat, jahr) }

    public static func < (a: Kalendertag, b: Kalendertag) -> Bool {
        (a.jahr, a.monat, a.tag) < (b.jahr, b.monat, b.tag)
    }
}

/// Warum eine Vorführmappe nicht gelesen wurde — **mit einem Satz für einen Menschen.**
public enum Vorfuehrmappenfehler: Error, Equatable, Sendable {
    /// `vorfuehrmappe.json` liegt nicht im Ordner.
    case dateiFehlt
    /// Kein JSON, oder kein Objekt.
    case nichtLesbar
    /// Ein anderes Schema — `nil`: gar keines.
    case schemaUnbekannt(String?)
    /// Ein Pflichtfeld fehlt oder hat nicht die erwartete Form.
    case feldFehlt(String)
    /// Ein Eintrag unter `bilder` (gezählt ab 1) hat nicht die Form eines Bildes.
    case bildUnlesbar(stelle: Int, grund: String)

    public var satz: String {
        switch self {
        case .dateiFehlt:
            return "Die Vorführmappe fehlt: Im Ordner liegt keine \(Vorfuehrmappe.dateiname)."
        case .nichtLesbar:
            return "Die Vorführmappe ist nicht lesbar — die Datei ist kein JSON-Objekt."
        case .schemaUnbekannt(let s):
            return "Die Vorführmappe hat ein unbekanntes Format (\(s ?? "ohne Angabe")); "
                + "diese Fassung kennt \(Vorfuehrmappe.schema). Sie wird nicht versuchsweise "
                + "gelesen — was dabei fehlte, fiele niemandem auf."
        case .feldFehlt(let f):
            return "Der Vorführmappe fehlt das Feld «\(f)», oder es hat nicht die erwartete Form."
        case .bildUnlesbar(let stelle, let grund):
            return "Das \(stelle). Bild der Vorführmappe ist nicht lesbar: \(grund)"
        }
    }
}

/// Ein Bild der Vorführmappe.
public struct Vorfuehrbild: Equatable, Sendable, Identifiable {
    /// Der Dateiname im Ordner der Mappe — ein Name, nie ein Weg.
    public let datei: String
    /// Die Unterschrift («Blick Süd-Ost»), oder `nil`.
    public let blick: String?
    /// Der Tag, an dem es gerechnet wurde — `nil` heisst **nicht gerechnet** (Platzhalter)
    /// oder nicht bekannt, nie «heute».
    public let gerechnetAm: Kalendertag?
    /// Was das Bild ist, als Satz.
    public let satz: String?
    /// **Die Felder der Fläche**, gelesen wie live (`Mappenbild`).
    public let angaben: Mappenbild
    /// Ob die Datei im Ordner liegt. Ohne sie steht das Bild mit `fehltSatz` da.
    public let vorhanden: Bool
    /// Die Stelle in der Datei (ab 0) — die Reihenfolge, wenn das Datum nicht entscheidet.
    public let stelle: Int
    /// Ob es aus einer Platzhalter-Mappe stammt (die Mappe sagt es für alle Bilder).
    public let platzhalter: Bool

    public var id: String { datei }

    /// **Das Prüfzeichen — dasselbe wie live**: `Mappenbild.pruefzeichen` in der Lesart, die
    /// das Bild ohne eigenen Schalter hat (ein Entwurf als Entwurf, sonst geprüft).
    public var zeichen: Pruefzeichen {
        angaben.pruefzeichen(angaben.vorgabeLesart)
    }

    /// Das Fussband am Bild (Blatt 13b): «BESTANDEN · 0.84 gegen 0.65», «NICHT GEMESSEN ·
    /// Vorbehalt».
    ///
    /// Wort und Zahl sind `Pruefzeichen.zeile`, die Schwelle steht nur, wo der Kern sie
    /// zeigt (neben einer Prüfzahl). Das Blatt schreibt «UNGEMESSEN»; gebaut ist das Wort
    /// des Kerns, «NICHT GEMESSEN» — ein Zustand, ein Wort, in der App wie im Vorführmodus.
    public var fussband: String {
        let z = zeichen
        var text = z.zeile
        if let grenze = z.schwelle { text += " gegen " + grenze }
        if !z.vorbehalte.isEmpty { text += " · Vorbehalt" }
        return text
    }

    /// Die Zeile unter dem Bild: Unterschrift und **das Datum** (Entscheid 40) — oder, bei
    /// einem Platzhalter, dass es nicht gerechnet ist.
    public var unterzeile: String {
        let name = blick ?? angaben.titel ?? datei
        if !vorhanden { return name + " · Bilddatei fehlt" }
        if platzhalter { return name + " · Platzhalter, nicht gerechnet" }
        if let tag = gerechnetAm { return name + " · vorher gerechnet am " + tag.lang }
        return name + " · vorher gerechnet, Tag nicht bekannt"
    }

    /// Der Satz, wenn die Datei fehlt.
    public var fehltSatz: String {
        "Die Bilddatei «\(datei)» fehlt in der Vorführmappe — gezeigt wird ihr Platz, nicht das Bild."
    }

    /// Was ein Bildschirmleser vorliest.
    public var vorlesetext: String {
        [unterzeile, zeichen.vorlesetext].joined(separator: ". ")
    }
}

/// Die Vorführmappe: Titel, Datum, Bilder.
public struct Vorfuehrmappe: Equatable, Sendable {
    public static let schema = "visbox.vorfuehrmappe/v1"
    public static let dateiname = "vorfuehrmappe.json"

    public let titel: String
    /// «Beispielmappe» — was für eine Mappe das ist, oder `nil`.
    public let art: String?
    /// `true`: graue Platzhalter, die Zeichen von Hand gesetzt. **Fehlt das Feld, gilt es
    /// als Platzhalter** — eine Mappe, die nicht sagt, dass sie gerechnet ist, wird nicht
    /// als gerechnet gezeigt.
    public let platzhalter: Bool
    /// Der Tag des Rechnens (der jüngste der Bilder), `nil` bei Platzhaltern.
    public let gerechnetAm: Kalendertag?
    public let satz: String?
    /// **Sortiert**: das zuletzt gerechnete zuerst, bei gleichem Tag in der Reihenfolge der
    /// Datei; Bilder ohne Tag am Ende.
    public let bilder: [Vorfuehrbild]

    /// Liest eine Mappe aus ihren Bytes. `vorhanden` sagt je Dateiname, ob die Datei liegt.
    public static func lies(_ daten: Data,
                            vorhanden: (String) -> Bool) throws -> Vorfuehrmappe {
        guard let wert = try? JSONWert.lies(daten), let o = wert.alsObjekt else {
            throw Vorfuehrmappenfehler.nichtLesbar
        }
        guard let s = o["schema"]?.alsText, s == schema else {
            throw Vorfuehrmappenfehler.schemaUnbekannt(o["schema"]?.alsText)
        }
        guard let titel = o["titel"]?.alsText,
              !titel.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw Vorfuehrmappenfehler.feldFehlt("titel")
        }
        guard let liste = o["bilder"]?.alsListe else {
            throw Vorfuehrmappenfehler.feldFehlt("bilder")
        }
        let platzhalter = o["platzhalter"]?.alsWahrheit ?? true
        var bilder: [Vorfuehrbild] = []
        var gesehen = Set<String>()
        for (i, eintrag) in liste.enumerated() {
            let bild = try lesBild(eintrag, stelle: i, platzhalter: platzhalter,
                                   vorhanden: vorhanden)
            guard gesehen.insert(bild.datei).inserted else {
                throw Vorfuehrmappenfehler.bildUnlesbar(
                    stelle: i + 1, grund: "«\(bild.datei)» steht zweimal in der Mappe.")
            }
            bilder.append(bild)
        }
        return Vorfuehrmappe(titel: titel, art: o["art"]?.alsText, platzhalter: platzhalter,
                             gerechnetAm: Kalendertag(o["gerechnet_am"]?.alsText),
                             satz: o["satz"]?.alsText, bilder: sortiert(bilder))
    }

    /// Liest die Mappe aus ihrem Ordner. Ob ein Bild liegt, wird dort nachgesehen.
    public static func lies(ordner: URL) throws -> Vorfuehrmappe {
        let datei = ordner.appendingPathComponent(dateiname)
        guard FileManager.default.fileExists(atPath: datei.path) else {
            throw Vorfuehrmappenfehler.dateiFehlt
        }
        guard let daten = try? Data(contentsOf: datei) else {
            throw Vorfuehrmappenfehler.nichtLesbar
        }
        return try lies(daten) { name in
            var ordnerHier: ObjCBool = false
            let pfad = ordner.appendingPathComponent(name).path
            return FileManager.default.fileExists(atPath: pfad, isDirectory: &ordnerHier)
                && !ordnerHier.boolValue
        }
    }

    /// Wo die Datei eines Bildes liegt — `nil`, wenn sie fehlt.
    public static func adresse(_ bild: Vorfuehrbild, in ordner: URL) -> URL? {
        bild.vorhanden ? ordner.appendingPathComponent(bild.datei) : nil
    }

    /// Die Zeile unter dem Titel (Blatt 13b): «Beispielmappe · 12 Bilder · gerechnet am
    /// 28.10.». Bei Platzhaltern sagt sie das statt eines Datums.
    public var kopfzeile: String {
        var teile: [String] = []
        if let a = art, !a.isEmpty { teile.append(a) }
        teile.append(bilder.count == 1 ? "1 Bild" : "\(bilder.count) Bilder")
        if platzhalter {
            teile.append("Platzhalter, nicht gerechnet")
        } else {
            let tage = Set(bilder.compactMap { $0.gerechnetAm })
            if let juengster = tage.max() {
                if let aeltester = tage.min(), aeltester != juengster {
                    teile.append("gerechnet vom \(aeltester.kurz) bis \(juengster.kurz)")
                } else {
                    teile.append("gerechnet am \(juengster.kurz)")
                }
            } else if let tag = gerechnetAm {
                teile.append("gerechnet am \(tag.kurz)")
            } else {
                teile.append("Tag des Rechnens nicht bekannt")
            }
        }
        return teile.joined(separator: " · ")
    }

    // ------------------------------------------------------------------ intern

    private static func lesBild(_ eintrag: JSONWert, stelle i: Int, platzhalter: Bool,
                                vorhanden: (String) -> Bool) throws -> Vorfuehrbild {
        guard let o = eintrag.alsObjekt else {
            throw Vorfuehrmappenfehler.bildUnlesbar(stelle: i + 1, grund: "kein Objekt.")
        }
        guard let datei = o["datei"]?.alsText, istDateiname(datei) else {
            throw Vorfuehrmappenfehler.bildUnlesbar(
                stelle: i + 1,
                grund: "«datei» fehlt oder ist kein schlichter Dateiname (ein Name, kein Weg).")
        }
        guard let flaeche = o["flaeche"]?.alsObjekt else {
            throw Vorfuehrmappenfehler.bildUnlesbar(
                stelle: i + 1, grund: "«flaeche» fehlt — ohne sie gibt es kein Zeichen.")
        }
        let blick = o["blick"]?.alsText.flatMap {
            $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : $0
        }
        return Vorfuehrbild(datei: datei, blick: blick,
                            gerechnetAm: Kalendertag(o["gerechnet_am"]?.alsText),
                            satz: o["satz"]?.alsText, angaben: Mappenbild(flaeche),
                            vorhanden: vorhanden(datei), stelle: i, platzhalter: platzhalter)
    }

    /// Ein Name, kein Weg: kein Trenner, kein Aufstieg, nicht versteckt.
    static func istDateiname(_ s: String) -> Bool {
        !s.isEmpty && !s.contains("/") && !s.contains("\\") && !s.hasPrefix(".")
            && s.trimmingCharacters(in: .whitespacesAndNewlines) == s
    }

    /// Das zuletzt gerechnete zuerst; bei gleichem Tag die Reihenfolge der Datei; ohne Tag
    /// ans Ende. **Die Reihenfolge der Datei ist die Wahl dessen, der die Mappe gemacht
    /// hat** — sie entscheidet, wo das Datum es nicht tut.
    static func sortiert(_ bilder: [Vorfuehrbild]) -> [Vorfuehrbild] {
        bilder.sorted { a, b in
            switch (a.gerechnetAm, b.gerechnetAm) {
            case let (x?, y?) where x != y: return x > y
            case (.some, .none): return true
            case (.none, .some): return false
            default: return a.stelle < b.stelle
            }
        }
    }
}
