import Foundation

// DIE OFFENEN KARTEN LIEGEN IN DER MAC-APP (Strang «Karten», 21.10.2026).
//
// Anlass (erster Claude-Demolauf am Mac, 0.3.16): Claudes Karte K-3 («Stimmung morgen → abend»)
// verschwand, als die Knotenansicht fuer die Visbox-Seite geschlossen wurde. Danach war nichts
// geaendert und kein Vorschlag mehr offen — ohne dass der Architekt es merkte. Die Karten lebten
// nur in der Seite (`ki-werkzeuge.ts`, Modulzustand), und die App verwarf beim Entladen alle.
//
// Seither gilt:
//
//  * **Eine Karte gilt pro Mappe und Graph, nicht pro Ansicht.** Die App haelt sie hier, mit der
//    Mappe, in der sie entstand, und der Zeit. Geht die Knotenansicht (neu geladen, Visbox-Seite,
//    Fenster zu), bleibt die Karte stehen. Meldet sich die Seite wieder an, gibt die App ihr die
//    Karten DIESER Mappe zurueck (`visboxKi.stelleWieder`) — die Seite rechnet sie dabei neu
//    durch (derselbe Probelauf wie beim ersten Mal).
//  * **Eine Karte bleibt, bis sie abgelehnt, angewendet oder beim echten Beenden verworfen wird**
//    (dieselbe Regel wie KosmoOrbit ab v0.1.10; Owner-Grundsatz «Visbox identisch»). Echtes Beenden
//    heisst: die App geht zu, oder der Architekt schaltet «Claude über MCP» aus (`beende`). Dann
//    bekommt Claude je Karte einen Satz mit Grund — ueber die wartende Antwort des Werkzeugaufrufs
//    und `visbox_vorschlag_status` (`Mcpkern.entscheide`), soweit die Leitung noch steht. Ablaufen
//    laesst die App eine Karte nicht mehr (bis zum Folgeauftrag 21.10.2026: nach 4 Stunden).
//  * **Leitungsverlust ist kein Beenden.** Faellt der Hoerer fuer Claude aus, bleiben die Karten mit
//    dem Vermerk «Leitung unterbrochen» stehen (`leitungWeg`). Was der Architekt in der Zeit
//    entscheidet, haelt die Ablage zurueck (`anClaude`). Steht die Leitung wieder (`leitungWieder`),
//    meldet die App zuerst die offenen Karten neu an (`Mcpkern.meldeNeu`), danach erst gehen die
//    zurueckgehaltenen Entscheide an Claude.
//  * **Passt eine Karte nicht mehr** (andere Mappe offen, oder der Graph hat sich so geaendert,
//    dass der Probelauf scheitert), bleibt sie stehen, bis jemand entscheidet: «Anwenden» weist
//    sie dann mit Satz ab, nichts wird geaendert. Nicht still.
//
// Hier steht NUR die Regel, ohne WebKit — darum unter Linux mit Proben (`KartenablageTests`).
// Die `Kizentrale` (Mac-App) fuehrt aus, was die Antworten sagen.

/// Wo eine Karte gilt: die Mappe, in der die Knotenansicht lief.
public struct Kartenmappe: Equatable, Hashable, Sendable {
    /// Eindeutig je Mappe (der Ordner der Mappe am Mac, sonst «am Heim-PC»). Geht nie hinaus.
    public let schluessel: String
    /// So heisst sie in einem Satz.
    public let name: String

    public init(schluessel: String, name: String) {
        self.schluessel = schluessel
        self.name = name
    }

    /// Ohne Mappe am Mac: die Mappe, mit der der Heim-PC laeuft.
    public static let amHeimPC = Kartenmappe(schluessel: "heim-pc", name: "am Heim-PC")

    /// Aus dem Ordner der Mappe am Mac — `nil`: am Heim-PC.
    public static func aus(ordner: URL?) -> Kartenmappe {
        guard let ordner else { return .amHeimPC }
        let pfad = ordner.standardizedFileURL.path
        let name = ordner.deletingPathExtension().lastPathComponent
        return Kartenmappe(schluessel: pfad, name: name.isEmpty ? "ohne Namen" : name)
    }
}

/// Eine offene Karte, wie die App sie haelt.
public struct Kartenablageeintrag: Equatable, Sendable {
    public var karte: Kikarte
    public let mappe: Kartenmappe
    /// Seit wann sie liegt (fuer Saetze und die Reihenfolge). Eine Wiedergabe setzt die Zeit NICHT neu.
    public let seit: Date
    /// Ob die offene Knotenansicht sie gerade kennt (dann entscheidet sie dort).
    public var inDerSeite: Bool
    /// Warum sie nicht mehr passt (die Wiedergabe scheiterte) — `nil`: sie passt.
    public var passtNicht: String?
}

/// Was die App mit einem Entscheid an einer Karte tut.
public enum Kartenentscheid: Equatable, Sendable {
    /// An die Knotenansicht reichen (`visboxKi.entscheide`); ihr Ereignis «entschieden» weckt Claude.
    case anDieSeite
    /// Hier entschieden: Die Karte ist weg, Claude bekommt `antwort`, die Leiste zeigt `meldung`.
    case hier(antwort: Mcpergebnis, meldung: String?)
    /// Die Karte bleibt liegen (die Knotenansicht ist zu); die Leiste sagt warum.
    case wartet(meldung: String)
    /// Diese Kennung liegt nicht hier.
    case unbekannt
}

public struct Kartenablage: Equatable, Sendable {
    /// Die offenen Karten, aelteste zuerst.
    public private(set) var eintraege: [Kartenablageeintrag] = []
    /// Ob die Leitung zu Claude steht (der Hoerer der App ist bereit).
    public private(set) var leitungSteht = true
    /// Entscheide, die waehrend eines Leitungsverlusts fielen — sie gehen nach dem Neuanmelden hinaus.
    public private(set) var zurueckgehalten: [Kartenantwort] = []

    public init() {}

    public var kennungen: [String] { eintraege.map(\.karte.kennung) }

    public func eintrag(_ kennung: String) -> Kartenablageeintrag? {
        eintraege.first { $0.karte.kennung == kennung }
    }

    // ------------------------------------------------------------- aus der Seite

    /// Die Seite hat eine Karte gelegt (Ereignis «karte»). Liegt sie schon (eine Wiedergabe),
    /// bleiben Mappe und Zeit; die Zusammenfassung kommt neu.
    public mutating func lege(_ karte: Kikarte, mappe: Kartenmappe, jetzt: Date = Date()) {
        if let i = eintraege.firstIndex(where: { $0.karte.kennung == karte.kennung }) {
            eintraege[i].karte = karte
            eintraege[i].inDerSeite = true
            eintraege[i].passtNicht = nil
            return
        }
        eintraege.append(Kartenablageeintrag(karte: karte, mappe: mappe, seit: jetzt,
                                             inDerSeite: true, passtNicht: nil))
    }

    /// Die Karte ist entschieden (Ereignis «entschieden» oder hier) — sie faellt weg.
    @discardableResult
    public mutating func entferne(_ kennung: String) -> Kartenablageeintrag? {
        guard let i = eintraege.firstIndex(where: { $0.karte.kennung == kennung }) else { return nil }
        return eintraege.remove(at: i)
    }

    /// Die Knotenansicht ist weg. **Die Karten bleiben** — nur kennt die Seite sie nicht mehr.
    public mutating func seiteWeg() {
        for i in eintraege.indices { eintraege[i].inDerSeite = false }
    }

    // ------------------------------------------------------------- zurueck an die Seite

    /// Was die App einer neu angemeldeten Knotenansicht zurueckgibt: die Karten DIESER Mappe, die
    /// die Seite nicht kennt und die nicht schon als unpassend gelten.
    public func zurUebergabe(_ mappe: Kartenmappe) -> [Kartenablageeintrag] {
        eintraege.filter { $0.mappe == mappe && !$0.inDerSeite && $0.passtNicht == nil }
    }

    /// Die Karten fuer `visboxKi.stelleWieder` als JSON-Text — `nil`: keine.
    public func uebergabeText(_ mappe: Kartenmappe) -> String? {
        let liste = zurUebergabe(mappe).compactMap(\.karte.roh)
        guard !liste.isEmpty else { return nil }
        return (try? JSONWert.liste(liste).daten()).flatMap { String(data: $0, encoding: .utf8) }
    }

    /// Die Antwort der Seite auf `stelleWieder`: je Karte `{kennung, liegt, text}`. Was liegt,
    /// meldet die Seite ohnehin mit «karte» (`lege`); was nicht liegt, passt nicht mehr — mit dem
    /// Satz der Seite als Grund. Gibt die Kennungen zurueck, die nicht passen.
    @discardableResult
    public mutating func nimmWiedergabe(_ antwort: JSONWert?) -> [String] {
        var unpassend: [String] = []
        for w in antwort?.alsListe ?? [] {
            guard let kennung = w["kennung"]?.alsText,
                  let i = eintraege.firstIndex(where: { $0.karte.kennung == kennung }) else { continue }
            if w["liegt"]?.alsWahrheit == true {
                eintraege[i].inDerSeite = true
                eintraege[i].passtNicht = nil
            } else {
                eintraege[i].inDerSeite = false
                eintraege[i].passtNicht = Kartenablage.grundAusSatz(w["text"]?.alsText)
                unpassend.append(kennung)
            }
        }
        return unpassend
    }

    /// Aus dem Satz der Seite («FEHLER: … — nichts wurde vorgeschlagen.») der Grund allein.
    static func grundAusSatz(_ satz: String?) -> String {
        var s = (satz ?? "").trimmingCharacters(in: .whitespaces)
        for kopf in ["FEHLER: ", "OHNE ÄNDERUNG: "] where s.hasPrefix(kopf) {
            s = String(s.dropFirst(kopf.count))
        }
        for schluss in [" — nichts wurde vorgeschlagen.", "."] where s.hasSuffix(schluss) {
            s = String(s.dropLast(schluss.count))
        }
        return s.isEmpty ? "der Probelauf im jetzigen Graph scheiterte" : s
    }

    // ------------------------------------------------------------- Entscheid und Ablauf

    /// «Anwenden» (`ja`) oder «Ablehnen» aus der Leiste. `mappe`: die jetzt offene; `seiteOffen`:
    /// ob die Knotenansicht angemeldet ist. Bei `.hier` ist die Karte schon entfernt.
    public mutating func entscheide(_ kennung: String, ja: Bool, mappe: Kartenmappe,
                                    seiteOffen: Bool) -> Kartenentscheid {
        guard let e = eintrag(kennung) else { return .unbekannt }
        if seiteOffen && e.inDerSeite { return .anDieSeite }
        if !ja {
            entferne(kennung)
            return .hier(antwort: Kartenablage.abgelehnt, meldung: nil)
        }
        if e.mappe != mappe {
            entferne(kennung)
            let grund = "Der Vorschlag gehört zur Mappe «\(e.mappe.name)», offen ist «\(mappe.name)»"
            return .hier(antwort: Kibruecke.verworfen(grund),
                         meldung: "\(kennung) gehört zu einer anderen Mappe — nichts wurde geändert. "
                            + "\(e.karte.urheber.name) hat es gehört.")
        }
        if let grund = e.passtNicht {
            entferne(kennung)
            return .hier(antwort: Kibruecke.verworfen("Der Vorschlag passt nicht mehr zum Graph (\(grund))"),
                         meldung: "\(kennung) passt nicht mehr zum Graph — nichts wurde geändert. "
                            + "\(e.karte.urheber.name) hat es gehört.")
        }
        return .wartet(meldung: seiteOffen ? Kartenablage.wirdZurueckgegebenSatz : Kartenablage.wartetSatz)
    }

    // ------------------------------------------------------------- echtes Beenden

    /// Die App geht zu, oder «Claude über MCP» wird ausgeschaltet: Die Karten fallen weg, je Karte
    /// ein Satz mit Grund. Beim Ausschalten nur Claudes Karten — die des Assistenten gehen nicht
    /// ueber MCP und bleiben. Gibt die Antworten fuer Claude zurueck (die App reicht sie an den Kern
    /// und raeumt die Karten in der Seite ab).
    public mutating func beende(_ wie: Kartenende) -> [Kartenantwort] {
        let weg = eintraege.filter { wie == .appZu || $0.karte.urheber == .claude }
        eintraege.removeAll { e in weg.contains { $0.karte.kennung == e.karte.kennung } }
        let satz = Kibruecke.verworfen(wie.grund)
        let antworten = weg.map { Kartenantwort(kennung: $0.karte.kennung, antwort: satz, inDerSeite: $0.inDerSeite) }
        // Was in einer Unterbrechung zurueckgehalten war, geht jetzt mit hinaus — es gibt kein Spaeter.
        let alt = zurueckgehalten
        zurueckgehalten = []
        return alt + antworten
    }

    /// Der Satz in der Leiste nach dem Ausschalten — `nil`, wenn keine Karte wegfiel.
    public static func beendetMeldung(_ antworten: [Kartenantwort], _ wie: Kartenende) -> String? {
        let kennungen = antworten.filter { $0.antwort == Kibruecke.verworfen(wie.grund) }.map(\.kennung)
        guard !kennungen.isEmpty else { return nil }
        return "\(wie.grund) — \(kennungen.joined(separator: ", ")) verworfen, nichts wurde geändert. "
            + "Claude hat es gehört, soweit es noch verbunden war."
    }

    // ------------------------------------------------------------- Leitung zu Claude

    /// Der Hoerer fuer Claude ist ausgefallen: Die Karten bleiben, mit Vermerk.
    public mutating func leitungWeg() {
        leitungSteht = false
    }

    /// Eine Antwort an Claude: `true` — jetzt senden; `false` — zurueckgehalten bis zur Leitung.
    public mutating func anClaude(_ kennung: String, _ antwort: Mcpergebnis) -> Bool {
        if leitungSteht { return true }
        zurueckgehalten.append(Kartenantwort(kennung: kennung, antwort: antwort, inDerSeite: false))
        return false
    }

    /// Die Leitung steht wieder. Zuerst die offenen Karten (`neuMelden`, fuer `Mcpkern.meldeNeu`),
    /// danach die zurueckgehaltenen Entscheide (`antworten`) — in dieser Reihenfolge an Claude.
    public mutating func leitungWieder() -> (neuMelden: [(kennung: String, zusammenfassung: String)],
                                            antworten: [Kartenantwort]) {
        leitungSteht = true
        let alt = zurueckgehalten
        zurueckgehalten = []
        let offen = eintraege.filter { $0.karte.urheber == .claude }
            .map { (kennung: $0.karte.kennung, zusammenfassung: $0.karte.zusammenfassung) }
        return (offen, alt)
    }

    /// Der Vermerk an einer Karte — «Leitung unterbrochen», solange Claude nicht erreichbar ist.
    public func vermerk(_ kennung: String) -> String? {
        guard !leitungSteht, eintrag(kennung)?.karte.urheber == .claude else { return nil }
        return Kartenablage.leitungUnterbrochen
    }

    public static let leitungUnterbrochen = "Leitung unterbrochen"

    // ------------------------------------------------------------- die Saetze

    /// Dieselben Worte wie «Ablehnen» in der Seite (`ablehnen` in `ki-werkzeuge.ts`).
    public static let abgelehnt = Mcpergebnis(
        text: "ABGELEHNT: Der Architekt hat den Vorschlag abgelehnt; das Projekt ist unverändert.",
        fehler: true)

    /// Der Satz, wenn «Anwenden» bei geschlossener Knotenansicht gedrueckt wird.
    public static let wartetSatz = "Der Vorschlag wartet — er wird in der Knotenansicht angewendet. "
        + "Öffne sie («Zurück zu den Knoten»), dann «Anwenden»."

    /// Der Satz, wenn die Seite offen ist, die Karte aber noch nicht zurueckbekommen hat.
    public static let wirdZurueckgegebenSatz = "Der Vorschlag wird eben an die Knotenansicht "
        + "zurückgegeben — gleich nochmals «Anwenden»."
}

/// Wie die Arbeit mit Claude wirklich endet.
public enum Kartenende: Equatable, Sendable {
    /// Die App geht zu.
    case appZu
    /// Der Architekt schaltet «Claude über MCP» aus.
    case anschlussAus

    public var grund: String {
        switch self {
        case .appZu: return "\(Marke.name) wurde beendet"
        case .anschlussAus: return "Der Architekt hat «Claude über MCP» ausgeschaltet"
        }
    }
}

/// Eine Antwort an Claude zu einer Karte — mit der Angabe, ob die Seite sie noch kennt (dann raeumt
/// die App sie dort ab).
public struct Kartenantwort: Equatable, Sendable {
    public let kennung: String
    public let antwort: Mcpergebnis
    public let inDerSeite: Bool

    public init(kennung: String, antwort: Mcpergebnis, inDerSeite: Bool) {
        self.kennung = kennung
        self.antwort = antwort
        self.inDerSeite = inDerSeite
    }
}
