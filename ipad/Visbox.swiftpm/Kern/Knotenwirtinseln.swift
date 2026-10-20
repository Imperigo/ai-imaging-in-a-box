import Foundation

// DIE INSELN DER KNOTENANSICHT AN DER BRUECKE «visboxWirt» (Plan UI-Gleichheit S3/S4, Entscheide
// 115/116, 20.10.2026).
//
// Seit S3 steht in der Knotenansicht die Kugel des Assistenten mit ihrem Gespraechsfeld (wortgleich
// aus KosmoOrbit, Name «Assistent», 116 (2)), seit S4 die Einstellungs-Insel. Beides zeichnet die
// Seite; was es zeigt, sagt die App — und **die Regeln bleiben hier**:
//
// * Das Gespraech fuehrt die App mit `Assistentengespraech` (hoechstens eine Karte, keine zweite
//   Anfrage, solange eine unterwegs ist, in den Verlauf nur, was der Server annahm, die Laengen).
//   `Assistentenlage` macht daraus, was die Seite zeichnet, und sagt auch, **wann statt des Felds ein
//   Satz steht** (ohne Rechner, Modell nicht bereit) — wie die Assistent-Leiste der App.
// * «Wer rechnet?» zeigt dieselben Felder wie `Rechnerwahlansicht` (`Rechnerwahl` entscheidet, was
//   waehlbar ist und warum nicht).
// * «Claude über MCP» traegt die Saetze von `Claudeeinrichtung` woertlich.
//
// Das Heim-PC-Kennwort hat in keiner dieser Lagen ein Feld (Entscheid 116 (6)).

/// Was das Gespraechsfeld will.
public enum Assistentenwunsch: Equatable, Sendable {
    /// Eine Nachricht — die App legt sie ins Feld und schickt sie nach den Regeln des Gespraechs.
    case frage(String)
    case anwenden
    case ablehnen
    case aendern

    /// Aus `{"art":"assistent","tat":…}` — `nil`, wenn unvollstaendig oder unbekannt.
    public init?(aus wert: JSONWert) {
        switch wert["tat"]?.alsText {
        case "frage":
            guard let text = wert["text"]?.alsText else { return nil }
            self = .frage(text)
        case "anwenden": self = .anwenden
        case "ablehnen": self = .ablehnen
        case "aendern": self = .aendern
        default: return nil
        }
    }
}

extension Knotenwirt {
    /// Der Name des Assistenten an Kugel, Fensterkopf und Coop-Teilen (Entscheid 116 (2)) — dieselbe
    /// Zeichenkette meldet die Seite an (`ASSISTENT_NAME`, bewacht in `test_kosmovis_ui_gleichheit.py`).
    public static let assistentName = "Assistent"

    /// Was die Seite ueber das Neuladen hinaus behaelt (die Schluessel von `localStorage`, wie
    /// KosmoOrbit sie nennt): Thema, Akzent, Anzeige, der Rueckgaengig-Schalter. **Nur diese** —
    /// dieselbe Liste wie `MERKBAR` in `wirt-bruecke.ts` (bewacht).
    public static let merkbar: [String] = ["kosmo.thema", "kosmo.akzent", "kosmo.anzeige", "kosmo.touch-undo-geste"]
    /// So lang darf ein gemerkter Wert sein — die Anzeige ist ein kleines JSON-Objekt.
    public static let merkWertHoechstens = 200
    /// Wo die App die gemerkten Werte haelt (App-Einstellungen); das Thema bleibt bei `Thema.einstellung`.
    public static let merkEinstellung = "knoten.gemerkt"

    /// Das Skript am Dokumentanfang, das die gemerkten Werte zurueck in die Seite legt — jeder Wert
    /// als JSON-Zeichenkette (kein Zeichen kann aus ihr ausbrechen), nur Schluessel aus `merkbar`.
    public static func merkSkript(_ werte: [String: String]) -> String {
        var zeilen: [String] = []
        for schluessel in merkbar {
            guard let wert = werte[schluessel], wert.count <= merkWertHoechstens,
                  let k = try? JSONWert.text(schluessel).daten(), let w = try? JSONWert.text(wert).daten(),
                  let kt = String(data: k, encoding: .utf8), let wt = String(data: w, encoding: .utf8)
            else { continue }
            zeilen.append("localStorage.setItem(\(kt), \(wt));")
        }
        return "try { " + zeilen.joined(separator: " ") + " } catch (e) {}"
    }
}

// ============================================================================ das Gespraech

/// Was das Gespraechsfeld zeichnet — **abgeleitet** aus dem Gespraech der App.
public struct Assistentenlage: Equatable, Sendable {
    public var gespraech: Assistentengespraech
    public var zeile: Assistentenzeile?
    /// Ohne Rechner: der Satz der Sperre (`Rechnersperre.satz`); `nil`, wenn der Assistent geht.
    public var gesperrt: String?
    /// Ein Text fuer das Eingabefeld mit laufender Nummer — jede Aenderung der App an ihrem Feld
    /// (nach dem Senden leer, eine zurueckgelegte Nachricht, «Ändern»).
    public var feld: Feld?

    public struct Feld: Equatable, Sendable {
        public let nummer: Int
        public let text: String

        public init(nummer: Int, text: String) {
            self.nummer = nummer
            self.text = text
        }
    }

    public init(gespraech: Assistentengespraech, zeile: Assistentenzeile?, gesperrt: String?, feld: Feld? = nil) {
        self.gespraech = gespraech
        self.zeile = zeile
        self.gesperrt = gesperrt
        self.feld = feld
    }

    /// Solange die Zeile noch nicht nachgesehen ist — derselbe Satz wie die Assistent-Leiste.
    public static let nachgesehen = "Der Assistent wird am Heim-PC nachgesehen …"
    /// Ohne eingerichteten Heim-PC gibt es niemanden, den das Feld fragen koennte.
    public static let ohneHeim = "Der Assistent rechnet am Heim-PC — erst einrichten: Adresse und Kennwort (Einstellungen › Heim-PC)."

    /// **Wo statt des Felds ein Satz steht** — dieselbe Regel wie die Assistent-Leiste der App: ohne
    /// Rechner der Satz der Sperre; sonst nur bei «bereit» ein Feld, sonst der Satz der Zeile.
    public var feldSatz: String? {
        if let gesperrt { return gesperrt }
        if let zeile, zeile.nimmtEingabe { return nil }
        return zeile?.satz ?? Self.nachgesehen
    }

    public var wert: JSONWert {
        var o: [String: JSONWert] = [
            "beitraege": .liste(gespraech.angezeigt.map {
                .objekt(["von": .text($0.von.rawValue), "text": .text($0.text)])
            }),
            "wartet": .wahrheit(gespraech.wartet),
            "hinweis": gespraech.hinweis.map(JSONWert.text) ?? .null,
            "stand": zeile?.stand.map { .text($0.rawValue) } ?? .null,
            "modell": zeile?.modell.map(JSONWert.text) ?? .null,
            "feldSatz": feldSatz.map(JSONWert.text) ?? .null,
            "grenzen": .objekt(["titel": .text(Assistentengrenzen.titel),
                                "satz": .text(Assistentengrenzen.satz)]),
        ]
        if let karte = gespraech.karte {
            o["karte"] = .objekt(["zeilen": .liste(karte.zeilen.map(JSONWert.text)),
                                  "rechenzeit": karte.rechenzeit.map(JSONWert.text) ?? .null])
        } else {
            o["karte"] = .null
        }
        if let feld {
            o["feld"] = .objekt(["nummer": .ganz(feld.nummer), "text": .text(feld.text)])
        } else {
            o["feld"] = .null
        }
        return .objekt(o)
    }
}

// ======================================================================== «Wer rechnet?»

/// «Wer rechnet?» fuer die Einstellungs-Insel — dieselben Felder wie `Rechnerwahlansicht`.
public struct Rechnerwahllage: Equatable, Sendable {
    public let wahl: Rechnerwahl
    public let befund: Rechnerbefund
    public let lage: Leitungslage
    public let eingerichtet: Bool

    public init(wahl: Rechnerwahl, befund: Rechnerbefund, lage: Leitungslage, eingerichtet: Bool) {
        self.wahl = wahl
        self.befund = befund
        self.lage = lage
        self.eingerichtet = eingerichtet
    }

    /// Die Zeile unter einem Feld: am Heim-PC «· verbunden», am Geraet «nicht verfügbar — …».
    public func zeile(_ ort: Rechnerort, fuer arbeit: Rechenarbeit) -> String {
        if let gesperrt = Rechnerwahl.verfuegbarkeit(ort, fuer: arbeit, befund: befund).zeile { return gesperrt }
        return ort == .heimPC
            ? "· " + Rechnerwahl.zusatzHeim(fuer: arbeit, lage: lage, eingerichtet: eingerichtet) : ""
    }

    public var wert: JSONWert {
        .objekt([
            "titel": .text(Rechnerwahl.titel),
            "untertitel": .text(Rechnerwahl.untertitel),
            "arbeiten": .liste(Rechenarbeit.allCases.map { arbeit in
                .objekt([
                    "arbeit": .text(arbeit.rawValue),
                    "titel": .text(arbeit.titel),
                    "felder": .liste(Rechnerort.allCases.map { ort in
                        .objekt([
                            "ort": .text(ort.rawValue),
                            "titel": .text(ort.titel),
                            "zeile": .text(zeile(ort, fuer: arbeit)),
                            "gewaehlt": .wahrheit(wahl.wirksam(fuer: arbeit, befund: befund) == ort),
                            "waehlbar": .wahrheit(Rechnerwahl.verfuegbarkeit(ort, fuer: arbeit,
                                                                            befund: befund).waehlbar),
                        ])
                    }),
                ])
            }),
            "mcpSatz": .text(Rechnerwahl.mcpSatz),
            "heuteSatz": .text(Rechnerwahl.heuteSatz),
        ])
    }
}

// =================================================================== «Claude über MCP»

/// «Claude über MCP» fuer die Einstellungs-Insel — der Schalter und die Saetze von `Claudeeinrichtung`.
public struct Claudemcplage: Equatable, Sendable {
    public let an: Bool
    /// Wie der Hoerer steht («Claude über MCP ist aus.», «… startet …» …) — von der App.
    public let satz: String

    public init(an: Bool, satz: String) {
        self.an = an
        self.satz = satz
    }

    public var wert: JSONWert {
        .objekt([
            "an": .wahrheit(an),
            "satz": .text(satz),
            "titel": .text(Claudeeinrichtung.titel),
            "codeTitel": .text(Claudeeinrichtung.codeTitel),
            "befehl": .text(Claudeeinrichtung.befehl),
            "kopieren": .text(Claudeeinrichtung.kopieren),
            "datenTitel": .text(Claudeeinrichtung.datenTitel),
            "daten": .text(Claudeeinrichtung.daten),
            "werkzeugeTitel": .text(Claudeeinrichtung.werkzeugeTitel),
            "werkzeuge": .text(Claudeeinrichtung.werkzeuge),
            "nurHier": .text(Claudeeinrichtung.nurHier),
        ])
    }
}

// ======================================================================== «Neuigkeiten»

/// «Neuigkeiten»: die laufende Fassung und, wenn eine neuere bereitsteht, ihre Zeilen «Was neu ist».
public struct Neuigkeitenlage: Equatable, Sendable {
    public let fassung: String
    public let angebot: Freigabe?

    public init(fassung: String, angebot: Freigabe?) {
        self.fassung = fassung
        self.angebot = angebot
    }

    public var wert: JSONWert {
        var o: [String: JSONWert] = ["fassung": .text(fassung)]
        if let angebot {
            o["angebot"] = .objekt([
                "nummer": .text(angebot.nummer.description),
                "zeilen": .liste(Aktualisierung.neuerungen(aus: angebot.begleittext).map(JSONWert.text)),
            ])
        } else {
            o["angebot"] = .null
        }
        return .objekt(o)
    }
}
