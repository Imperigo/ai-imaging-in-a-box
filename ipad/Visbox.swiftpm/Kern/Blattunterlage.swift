import Foundation

// DIE UNTERLAGE DES BLATTES — das Bild aus der Mappe, auf das skizziert wird.
//
// Blaetter «Main» und «MainHoch»: «Skizze über Lauf 07», das Bild als unterste Zeile der
// Ebenentafel. Bis zum 23.09.2026 zeigte die App keine Unterlage und parkte jede Skizze
// OHNE `ueber`; der Server rechnete sie darum auf neutralem Grau (Protokoll §3, Befund
// aus der Welle 2). Hier stehen die Regeln, die die App dafuer braucht — ohne UIKit, damit
// sie unter Linux geprueft werden (`BlattunterlageTests`).
//
// WAS HIER GEPRUEFT IST (`BlattunterlageTests`, Stand 23.09.2026) — und nur das:
//   1. Die Unterlage ist KEINE Ebene. Sie steht nicht in `Ebenenstapel.ebenen`, zaehlt
//      nicht zur Hoechstzahl, nicht zu «Geht mit», nicht zur Leer-Pruefung, und sie ist nie
//      eine Variante.
//   2. `ueber` geht genau dann mit, wenn eine Unterlage liegt, sichtbar ist UND aus der
//      Mappe stammt, in die abgelegt wird (Entscheid 7, «gerechnet wird, was sichtbar
//      ist» — Begruendung an `Unterlagenangabe`). Tafelsatz und Blatttitel lesen dieselbe
//      Regel wie der Ablageplan (`tafelsatz`, `blatttitel`, seit der Durchsicht der Welle
//      2b: vorher versprachen sie nach einem Mappenwechsel «wird auf X gerechnet»,
//      waehrend der Ablageplan ablehnte).
//   3. Ob gestreckt wird, entscheidet `gestreckt` wie der Server
//      (`arbeitsgang.setze_auf_unterlage`, abgeschrieben; gegen den Server gehalten von
//      `tests/test_app_abschrift_server.py`).
//
// WAS DIE APP-SCHICHT TUT, OHNE PROBE (gebaut, am Geraet unbestaetigt): Die Unterlage ist
// ein Bild unter allen PencilKit-Flaechen, darum radiert der Radierer sie nicht; das PNG
// malt nur die Ebenen (`Zeichenstand.male`), nicht die Unterlage — der Server hat das Bild
// schon und setzt die Skizze selbst darauf; und `Leinwandstapel` zeigt sie gestreckt
// (`scaleToFill`). Ob das Bild dort deckungsgleich unter den Strichen liegt, ist nicht
// gesehen.

/// Das Bild unter den Ebenen — **keine Ebene, sondern das, worauf gezeichnet wird.**
///
/// Gelegt wird sie in der Bildansicht («Darauf skizzieren»). Die App hält daneben die
/// Grafik selbst; hier steht nur, was die Regeln brauchen.
public struct Blattunterlage: Equatable, Sendable {
    /// Der Dateiname, **wie er in der Mappe unter `bilder[].bild` steht** — genau das geht
    /// als `ueber` hinaus (Protokoll §3). Nie leer.
    public let bild: String
    /// Was ein Mensch sieht: der eigene Name des Bildes, sonst sein Name nach der Zeit.
    /// Ohne Angabe der Dateiname — nie eine leere Zeile.
    public let titel: String
    /// Die Mappe, aus der das Bild kam (`ordner` der Anfrage); `nil` heisst die des Starts
    /// der HomeStation. **Nur in dieser Mappe gibt es das Bild** — der Server sucht `ueber`
    /// in der Mappe, in die die Skizze geht (`arbeitsgang._eingangsbild`).
    public let ordner: String?
    /// Die Grösse des Bildes in Bildpunkten — `nil`, wenn sie sich nicht lesen liess
    /// (**nicht gemessen**, nicht 0).
    public let breite: Int?
    public let hoehe: Int?
    /// Ein- oder ausgeblendet. Eine frisch gelegte Unterlage ist sichtbar.
    public internal(set) var sichtbar: Bool

    /// `nil`, wenn der Dateiname leer ist: Eine Unterlage ohne Namen könnte drüben niemand
    /// finden, und ein leeres `ueber` liest der Server als «ohne Unterlage» (`or None`) —
    /// es sähe gesendet aus und rechnete auf Grau.
    ///
    /// Ein leerer Ordner heisst die Mappe des Starts (`nil`), wie überall in der App. Eine
    /// Grösse von 0 oder weniger ist keine Grösse und wird `nil` (nicht gemessen).
    public init?(bild: String, titel: String? = nil, ordner: String? = nil,
                 breite: Int? = nil, hoehe: Int? = nil) {
        guard !bild.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return nil }
        self.bild = bild
        let sauber = titel?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        self.titel = sauber.isEmpty ? bild : sauber
        self.ordner = Blattunterlage.mappe(ordner)
        let gemessen = (breite ?? 0) > 0 && (hoehe ?? 0) > 0
        self.breite = gemessen ? breite : nil
        self.hoehe = gemessen ? hoehe : nil
        self.sichtbar = true
    }

    /// **Ob der Server die Skizze auf dieses Bild strecken wird** — `true`, `false`, oder
    /// `nil`, wenn die Grösse des Bildes nicht gelesen ist (nicht gemessen, nicht «nein»).
    ///
    /// Die Regel des Servers, abgeschrieben aus `arbeitsgang.setze_auf_unterlage` (Stand
    /// 23.09.2026): gestreckt heisst, Skizze und Unterlage weichen im Seitenverhältnis um
    /// mehr als ein Prozent ab — `abs(s_b · t_h − t_b · s_h) > 0.01 · t_b · s_h`, die Skizze
    /// `s` ist das Blatt (`Ebenenstapel.blattBreite × blattHoehe`), `t` die Unterlage.
    /// Gerechnet in derselben Reihenfolge mit Kommazahlen wie dort, damit auch die Grenze
    /// gleich fällt (`BlattunterlageTests.testGestrecktFaelltWieBeimServer`).
    ///
    /// **Wozu:** Die App zeigt die Unterlage blattfüllend, also genauso gestreckt, wie der
    /// Server sie abbildet — gezeichnet wird, wo gerechnet wird. Dass sie verzerrt aussieht,
    /// sagt die Ebenentafel mit diesem Wert, statt es dem Auge zu überlassen.
    public var gestreckt: Bool? {
        guard let tBreite = breite, let tHoehe = hoehe else { return nil }
        let sBreite = Ebenenstapel.blattBreite
        let sHoehe = Ebenenstapel.blattHoehe
        let abweichung = abs(sBreite * tHoehe - tBreite * sHoehe)
        return Double(abweichung) > 0.01 * Double(tBreite) * Double(sHoehe)
    }

    /// Was an der Stelle der Unterlage in der Ebenentafel steht, unter ihrer Zeile — **ein
    /// Satz für jede Lage**, und keiner, der mehr sagt, als bekannt ist.
    ///
    /// `ordner` ist die Mappe, in die jetzt abgelegt würde (leer = die des Starts). **Der
    /// Satz liest dieselbe Regel wie das Ablegen** (`Unterlagenangabe.aus`, die auch
    /// `Ablageplan` nimmt): «wird auf «X» gerechnet» steht genau dann da, wenn `ueber` mit
    /// X hinausginge. Befund Durchsicht der Welle 2b (23.09.2026): Bis dahin kannte der Satz
    /// die Mappe nicht und versprach nach einem Mappenwechsel «wird auf X gerechnet»,
    /// während das Ablegen die Skizze abwies (`BlattunterlageTests`,
    /// `testTafelUndTitelSagenDasselbeWieDerAblageplan`).
    public static func tafelsatz(_ u: Blattunterlage?, ordner: String?) -> String {
        let grau = "Ohne Unterlage wird die Skizze auf neutralem Grau gerechnet. Ein Bild "
            + "der Mappe legt «Darauf skizzieren» darunter."
        guard let u = u else { return grau }
        switch Unterlagenangabe.aus(u, ordner: ordner) {
        case .ohne:
            return grau
        case .ausgeblendet:
            return "Die Unterlage ist ausgeblendet: Die Skizze geht ohne sie hinaus und wird "
                + "auf Grau gerechnet — gerechnet wird, was sichtbar ist."
        case .andereMappe(let von, let jetzt):
            return "«\(u.titel)» stammt aus \(Ablageplan.wo(von)), abgelegt würde in "
                + "\(Ablageplan.wo(jetzt)). Dort gibt es das Bild nicht — so geht die Skizze "
                + "nicht hinaus. Die Mappe zurückstellen oder die Unterlage entfernen."
        case .ueber:
            let gerechnet = "Die Skizze wird auf «\(u.titel)» gerechnet"
            switch u.gestreckt {
            case .some(true):
                return gerechnet + ". Das Bild hat ein anderes Seitenverhältnis als das Blatt "
                    + "und ist gestreckt — so, wie die HomeStation die Skizze daraufsetzt."
            case .some(false):
                return gerechnet + ", Blatt auf Bild."
            case .none:
                return gerechnet + ". Ob das Bild dafür gestreckt wird, ist nicht bekannt: "
                    + "Seine Grösse liess sich nicht lesen."
            }
        }
    }

    /// Der Titel über dem Blatt: «Skizze über Lauf 07 · Variante A» (Blatt «Main»: «Skizze
    /// über Lauf 07») — **«über» nur, wenn die Unterlage auch mitginge** (`.ueber` nach
    /// `Unterlagenangabe.aus`, dieselbe Regel wie `tafelsatz` und `Ablageplan`). Ausgeblendet
    /// oder aus einer anderen Mappe verspräche der Titel sonst, was nicht gerechnet wird.
    public static func blatttitel(ebene: String, unterlage u: Blattunterlage?,
                                  ordner: String?) -> String {
        if let u = u, Unterlagenangabe.aus(u, ordner: ordner).ueber != nil {
            return "Skizze über \(u.titel) · \(ebene)"
        }
        return "Skizze · \(ebene)"
    }

    /// Leer und `nil` sind dieselbe Mappe: die des Starts.
    static func mappe(_ ordner: String?) -> String? {
        guard let o = ordner, !o.isEmpty else { return nil }
        return o
    }
}

/// Was von der Unterlage mit einer Skizze hinausgeht.
///
/// **Entscheid 7, angewandt (23.09.2026): Eine ausgeblendete Unterlage geht nicht mit.**
/// «Gerechnet wird, was sichtbar ist» — wer die Unterlage ausblendet, sieht die Striche auf
/// dem leeren Blatt, und genau das rechnet der Server dann: die Skizze ohne `ueber`, auf
/// Grau. Ginge `ueber` trotzdem mit, rechnete die HomeStation ein Bild, das auf dem Schirm
/// nicht steht — derselbe Fehler wie eine ausgeblendete Ebene, die mitginge. Die
/// Ebenentafel sagt es in einem Satz (`Blattunterlage.tafelsatz`), damit das Grau keine
/// Überraschung ist.
public enum Unterlagenangabe: Equatable, Sendable {
    /// Keine Unterlage gelegt: `ueber` fehlt, der Server rechnet auf Grau.
    case ohne
    /// Eine Unterlage liegt, ist aber ausgeblendet: `ueber` fehlt (Entscheid 7, oben).
    case ausgeblendet(bild: String)
    /// Sichtbar: Der Name geht als `ueber` mit.
    case ueber(String)
    /// **Abgelehnt:** Die Unterlage stammt aus einer anderen Mappe als der, in die die
    /// Skizze jetzt ginge. Dort gibt es das Bild nicht; der Server wiese die Skizze erst
    /// beim Rechnen ab (`arbeitsgang._eingangsbild`: «steht nicht in der Mappe»). Still auf
    /// Grau auszuweichen wäre eine andere Bestellung, die aussieht wie die richtige.
    case andereMappe(unterlage: String?, jetzt: String?)

    /// Der Name, der als `ueber` hinausgeht — **nur** bei `.ueber`.
    public var ueber: String? {
        if case .ueber(let name) = self { return name }
        return nil
    }

    /// Die Regel. `ordner` ist die Mappe, in die gerade abgelegt würde (leer = die des
    /// Starts).
    public static func aus(_ unterlage: Blattunterlage?, ordner: String?) -> Unterlagenangabe {
        guard let u = unterlage else { return .ohne }
        guard u.sichtbar else { return .ausgeblendet(bild: u.bild) }
        let jetzt = Blattunterlage.mappe(ordner)
        guard u.ordner == jetzt else { return .andereMappe(unterlage: u.ordner, jetzt: jetzt) }
        return .ueber(u.bild)
    }
}

/// Was die Zeichenfläche zum Ablegen hergibt: **die gemalten Bilder und die Unterlage,**
/// so, wie beide im Augenblick des Tippens stehen.
public struct Skizzenpaket: Equatable, Sendable {
    public let ausgabe: Ebenenausgabe
    public let unterlage: Blattunterlage?

    public init(ausgabe: Ebenenausgabe, unterlage: Blattunterlage?) {
        self.ausgabe = ausgabe
        self.unterlage = unterlage
    }
}

/// Was «In die Mappe legen» tut: **parken, mit oder ohne `ueber` — oder nicht, mit Satz.**
///
/// Bis zum 23.09.2026 entschied das die App-Schicht (`Verbindungsstand.legeInDieMappe`),
/// ohne Probe. Jetzt steht die Entscheidung hier, und die App führt sie nur aus
/// (`Parkfach.parke(_:ueber:ordner:jetzt:)`).
public enum Ablageplan: Equatable, Sendable {
    /// Ins Parkfach, jedes Bild mit derselben Unterlage (`ueber`, oder `nil`).
    case parke(bilder: [Ebenenausgabe.Bild], ueber: String?)
    /// Nichts geht ins Fach; der Satz sagt warum.
    case nicht(satz: String)

    public static func aus(_ paket: Skizzenpaket, ordner: String?) -> Ablageplan {
        let bilder: [Ebenenausgabe.Bild]
        switch paket.ausgabe {
        case .bilder(let b):
            bilder = b
        case .nichtsGezeichnet(let ausgeblendet):
            // DIE UNTERLAGE ALLEIN IST KEINE SKIZZE: Sie liegt drüben schon, und ein
            // leeres Blatt darüber wäre ein Bild, auf dem bewusst nichts gezeichnet ist.
            if ausgeblendet == 0, let u = paket.unterlage, u.sichtbar {
                return .nicht(satz: "Auf «\(u.titel)» ist noch nichts gezeichnet — die "
                              + "Unterlage allein geht nicht hinaus.")
            }
            return .nicht(satz: ausgeblendet > 0
                ? "Nichts Sichtbares gezeichnet — ausgeblendete Ebenen gehen nicht mit "
                    + "(\(ausgeblendet) mit Strichen)."
                : "Nichts gezeichnet — ein leeres Blatt geht nicht hinaus.")
        case .zuVieleVarianten(let sichtbar, let hoechstens):
            return .nicht(satz: "\(sichtbar) Ebenen sind sichtbar; als Varianten gehen "
                          + "höchstens \(hoechstens). Eine ausblenden.")
        case .nichtErzeugt(let grund):
            return .nicht(satz: grund)
        }
        switch Unterlagenangabe.aus(paket.unterlage, ordner: ordner) {
        case .andereMappe(let unterlage, let jetzt):
            return .nicht(satz: "Die Unterlage stammt aus \(Ablageplan.wo(unterlage)), "
                          + "abgelegt würde in \(Ablageplan.wo(jetzt)). Dort gibt es das "
                          + "Bild nicht. Die Mappe zurückstellen oder die Unterlage entfernen.")
        case let angabe:
            return .parke(bilder: bilder, ueber: angabe.ueber)
        }
    }

    /// «der Mappe «/pfad»», oder «der Mappe des Starts» für `nil`.
    static func wo(_ ordner: String?) -> String {
        guard let o = ordner else { return "der Mappe des Starts" }
        return "der Mappe «\(o)»"
    }
}
