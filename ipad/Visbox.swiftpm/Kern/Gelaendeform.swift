import Foundation

// GELÄNDE AN DER FORM ERKENNEN, WENN DER NAME ES NICHT TRÄGT (A0289, «Gelände an der Form»).
//
// Das Abbild von `src/aiimaging/gelaendeform.py` und ihres Einsatzes in `glbbox.bauwerksbox` am
// Heim-PC. Die Regel ist dort erfunden und begründet; hier wird sie nur nachgerechnet, mit denselben
// Rechenschritten in derselben Reihenfolge, damit beide Seiten an den Schwellen dasselbe sagen.
//
// **Keine zweite Regel, sondern eine Zweitmeinung:** Sie spricht nur, wenn die Namensregel
// (`Glbauskunft.istGelaende`) nichts getrennt hat, und sie kennt die dritte Antwort «nicht
// entscheidbar».
//
// **Runde 2: Schutz des Hauses geht vor Abtrennen.** Eine Hüllbox sagt nicht, ob ihre Oberseite eine
// Geschossdecke oder ein Hang ist: Ein Sockelgeschoss und ein Hangkörper haben dieselbe Box. Darum
// macht die Box einen Körper nur zum Kandidaten (gross im Grundriss, nicht aufragend). Gelände wird er
// erst mit dem **Beweis an seinen Dreiecken**: Die Oberseite ist überwiegend geneigt UND uneben, sie
// liegt in einer Lage, ohne Hauswand im Inneren, nicht auf einem Sockel, und unter ihr ist nichts
// gebaut. Fehlt ein Beleg, heisst das Urteil «nicht entscheidbar», und der Körper bleibt in der Hülle.
// Eine ebene, waagrechte Fläche kann Gelände ODER Bauteil sein; die Form entscheidet sie nicht.
//
// **Getrennt wird nach der Stelle des Körpers, nicht nach seinem Namen.** Der Mac liefert in jedem
// Fall dasselbe wie der Heim-PC; die Ausnahme der Runde 1 (Namensgleichheit) ist weggefallen.
//
// Beide Seiten prüft die gemeinsame Probendatei `tests/daten/glbbox_gelaenderegel.json`
// (`formfaelle`); die Schwellen hier stehen in `tests/test_glbbox_formregel_gemeinsam.py` gegen die
// des Heim-PC fest.
public enum Gelaendeform {
    /// `gelaendeform.GRUNDRISSANTEIL_MIN`: Grundfläche des Körpers geteilt durch die der Szene; darunter
    /// ist er zu klein für Gelände.
    public static let grundrissanteilMin = 0.25
    /// `gelaendeform.FLACHHEIT_BEWIESEN_MAX`: Höhe geteilt durch die kleinere Grundrisskante; darüber
    /// ragt der Körper auf und ist kein Kandidat.
    public static let flachheitBewiesenMax = 0.30
    /// `gelaendeform.TIEFLAGE_UNKLAR_MAX`: Oberkante im Höhenbereich der Szene (0 unten, 1 oben). Liegt
    /// sie höher und gelänge der Beweis sonst, heisst das Urteil «nicht entscheidbar» (`zu_hoch`).
    public static let tieflageUnklarMax = 0.60
    /// `gelaendeform.NEIGUNG_MIN`: ab dieser Neigung (Höhe je Länge) zählt ein Dreieck als geneigt.
    public static let neigungMin = 0.04
    /// `gelaendeform.NEIGUNG_MAX`: bis zu dieser Neigung gehört ein Dreieck zur Oberseite.
    public static let neigungMax = 1.0
    /// `gelaendeform.DECKUNG_MIN`: die Oberseite deckt mindestens diesen Anteil des Grundrisses der Box.
    public static let deckungMin = 0.5
    /// `gelaendeform.LAGEN_MAX`: die Oberseite deckt den Grundriss höchstens so viel mal (ein Höhenfeld).
    public static let lagenMax = 1.25
    /// `gelaendeform.GENEIGT_ANTEIL_MIN`: mindestens dieser Anteil der Oberseite ist geneigt.
    public static let geneigtAnteilMin = 0.5
    /// `gelaendeform.RICHTUNGEN_MIN`: so viele verschiedene Gefällerichtungen zeigt gewachsener Boden
    /// mindestens; eine Rampe oder ein Dach zeigt eine bis vier.
    public static let richtungenMin = 6
    /// `gelaendeform.RICHTUNG_RASTER`: die Feldweite, in der Richtungen gezählt werden.
    public static let richtungRaster = 0.01
    /// `gelaendeform.WANDHOEHE_MAX`: so hoch darf eine steile Fläche im Inneren des Körpers aufragen.
    public static let wandhoeheMax = 2.0
    /// `gelaendeform.SOCKEL_MAX`: so hoch darf die tiefste Stelle der Oberseite über der Unterkante liegen.
    public static let sockelMax = 1.5
    /// `gelaendeform.UNTERBAUT_MAX`: tiefer reichende Körper dürfen höchstens diesen Anteil unterspannen.
    public static let unterbautMax = 0.25
    /// `gelaendeform.UNTERBAUT_TOLERANZ`: um so viel muss ein Körper tiefer reichen, damit er zählt.
    public static let unterbautToleranz = 0.1
    /// `glbbox.GERINGE_SCHRUMPFUNG`: Die Form wird nur gefragt, wenn die Namensregel den Grundriss um
    /// weniger als diesen Anteil enger gemacht hat.
    public static let geringeSchrumpfung = 0.05
    /// `glbbox.DREIECKE_HOECHSTENS`: mehr Dreiecke liest die Zweitmeinung je Körper nicht.
    public static let dreieckeHoechstens = 2_000_000

    /// Warum ein Kandidat «nicht entscheidbar» blieb: dieselben Kurzwörter wie am Heim-PC (`GRUND_…`).
    public enum Grund {
        public static let nichtLesbar = "nicht_lesbar"
        public static let deckung = "deckung"
        public static let lagen = "lagen"
        public static let eben = "eben"
        public static let eineEbene = "eine_ebene"
        public static let wand = "wand"
        public static let sockel = "sockel"
        public static let unterbaut = "unterbaut"
        public static let zuHoch = "zu_hoch"
    }

    /// Ein Mesh-Knoten mit seiner Hüllbox in glTF-Koordinaten (Y oben), wie `glbbox.knotenboxen`.
    public struct Koerper: Equatable, Sendable {
        public let name: String
        public let lo: [Double]
        public let hi: [Double]
        public init(name: String, lo: [Double], hi: [Double]) {
            self.name = name
            self.lo = lo
            self.hi = hi
        }
    }

    /// Die drei namensfreien Merkmale eines Körpers, bezogen auf die Szene.
    public struct Merkmale: Equatable, Sendable {
        public let grundrissanteil: Double
        public let flachheit: Double
        public let tieflage: Double
        public init(grundrissanteil: Double, flachheit: Double, tieflage: Double) {
            self.grundrissanteil = grundrissanteil
            self.flachheit = flachheit
            self.tieflage = tieflage
        }
    }

    /// Die Oberseite eines Körpers aus seinen Dreiecken (`gelaendeform.oberflaeche`).
    public struct Oberflaeche: Equatable, Sendable {
        /// Grundrissfläche der Dreiecke, die nach oben zeigen und höchstens `neigungMax` geneigt sind.
        public let oben: Double
        /// Der Teil davon mit mindestens `neigungMin`.
        public let geneigt: Double
        /// Die grösste Höhe eines steilen Dreiecks, das nicht am Rand der Hüllbox des Körpers liegt.
        public let wand: Double
        /// Die tiefste Ecke der Oberseite, `nil` ohne Oberseite.
        public let tief: Double?
        /// Wie viele verschiedene Gefällerichtungen der geneigte Teil zeigt.
        public let richtungen: Int
        public init(oben: Double, geneigt: Double, wand: Double, tief: Double?, richtungen: Int) {
            self.oben = oben
            self.geneigt = geneigt
            self.wand = wand
            self.tief = tief
            self.richtungen = richtungen
        }
    }

    /// Was die Form zu einer ganzen Szene sagt.
    public struct Zweitmeinung: Equatable, Sendable {
        /// Die Stellen (in der übergebenen Liste) der Körper, die an der Form Gelände sind.
        public let gelaende: [Int]
        /// Wie viele Körper «nicht entscheidbar» blieben; sie zählen zum Bauwerk.
        public let unklar: Int
        /// Je unklarem Körper das Kurzwort des Grundes, in der Reihenfolge der Körper.
        public let gruende: [String]
        /// `true`: Die Form trennt das Gelände ab (`glbbox`: `entschieden_durch == "form"`).
        public let entscheidet: Bool

        static let schweigt = Zweitmeinung(gelaende: [], unklar: 0, gruende: [], entscheidet: false)
    }

    /// Die Merkmale eines Körpers in seiner Szene, oder `nil`, wenn die Szene keine Ausdehnung hat
    /// (`GelaendeformError`): Jeder Anteil daran wäre unendlich oder beliebig.
    ///
    /// Höhenachse ist Y (Index 1): Die Boxen stehen in glTF-Koordinaten, die Umrechnung nach Welt
    /// kommt erst danach.
    public static func merkmale(_ koerper: Koerper, in alle: [Koerper]) -> Merkmale? {
        guard let bezug = szenenbezug(alle) else { return nil }
        return merkmale(koerper, bezug: bezug)
    }

    /// Unter- und Oberkante der Szene je Achse, oder `nil` ohne Grundfläche oder ohne Höhe.
    static func szenenbezug(_ alle: [Koerper]) -> (lo: [Double], hi: [Double])? {
        guard !alle.isEmpty, alle.allSatisfy({ $0.lo.count == 3 && $0.hi.count == 3 }) else { return nil }
        var lo = [Double](repeating: .infinity, count: 3), hi = [Double](repeating: -.infinity, count: 3)
        for k in alle { for i in 0 ..< 3 { lo[i] = min(lo[i], k.lo[i]); hi[i] = max(hi[i], k.hi[i]) } }
        let grund = (hi[0] - lo[0]) * (hi[2] - lo[2])
        let hoehe = hi[1] - lo[1]
        // Auch eine nicht messbare Zahl (NaN, unendlich) gibt keine Auskunft.
        guard grund > 0, hoehe > 0, grund.isFinite, hoehe.isFinite else { return nil }
        return (lo, hi)
    }

    static func merkmale(_ k: Koerper, bezug: (lo: [Double], hi: [Double])) -> Merkmale {
        let grundSzene = (bezug.hi[0] - bezug.lo[0]) * (bezug.hi[2] - bezug.lo[2])
        let hoeheSzene = bezug.hi[1] - bezug.lo[1]
        let breite = k.hi[0] - k.lo[0], hoehe = k.hi[1] - k.lo[1], tiefe = k.hi[2] - k.lo[2]
        let kleinere = min(breite, tiefe)
        return Merkmale(
            grundrissanteil: (breite * tiefe) / grundSzene,
            // Durch die KLEINERE Kante: Ein langer schmaler Steg wäre sonst «flach», obwohl er aufragt.
            flachheit: kleinere > 0 ? hoehe / kleinere : .infinity,
            tieflage: (k.hi[1] - bezug.lo[1]) / hoeheSzene)
    }

    // MARK: Der Beweis an der Oberfläche

    private struct Richtung: Hashable {
        let a: Double
        let b: Double
    }

    /// Die Oberseite aus Dreiecken in Weltkoordinaten (glTF, Y oben): `ecken` trägt je Dreieck neun
    /// Zahlen (a, b, c je x, y, z), Umlaufsinn gegen den Uhrzeiger von aussen. `gespiegelt`: Die
    /// Knotenmatrix spiegelt, der Umlaufsinn dreht sich.
    ///
    /// Dieselben Rechenschritte in derselben Reihenfolge wie `gelaendeform.oberflaeche` (mit `hoch = 1`).
    public static func oberflaeche(dreiecke ecken: [Double], gespiegelt: Bool) -> Oberflaeche {
        let anzahl = ecken.count / 9
        let zyklisch: Double = gespiegelt ? 1.0 : -1.0
        let min2 = neigungMin * neigungMin
        let max2 = neigungMax * neigungMax
        // Erster Durchgang: der Rand des Körpers im Grundriss, aus seinen eigenen Ecken.
        var lo1 = Double.infinity, lo2 = Double.infinity, hi1 = -Double.infinity, hi2 = -Double.infinity
        var i = 0
        while i < anzahl * 9 {
            let x = ecken[i], z = ecken[i + 2]
            if x < lo1 { lo1 = x }
            if x > hi1 { hi1 = x }
            if z < lo2 { lo2 = z }
            if z > hi2 { hi2 = z }
            i += 3
        }
        var oben = 0.0, geneigt = 0.0, wand = 0.0
        var tief: Double?
        var richtungen = Set<Richtung>()
        for d in 0 ..< anzahl {
            let o = d * 9
            let ax = ecken[o], ay = ecken[o + 1], az = ecken[o + 2]
            let bx = ecken[o + 3], by = ecken[o + 4], bz = ecken[o + 5]
            let cx = ecken[o + 6], cy = ecken[o + 7], cz = ecken[o + 8]
            let u1 = bx - ax, uh = by - ay, u2 = bz - az
            let v1 = cx - ax, vh = cy - ay, v2 = cz - az
            let n1 = uh * v2 - u2 * vh
            let n2 = u1 * vh - uh * v1
            let nh = (u1 * v2 - u2 * v1) * zyklisch
            let waag2 = n1 * n1 + n2 * n2
            let hoch2 = nh * nh
            if waag2 > max2 * hoch2 {
                let amRand = (ax == lo1 && bx == lo1 && cx == lo1) || (ax == hi1 && bx == hi1 && cx == hi1)
                    || (az == lo2 && bz == lo2 && cz == lo2) || (az == hi2 && bz == hi2 && cz == hi2)
                if !amRand {
                    let spanne = max(ay, by, cy) - min(ay, by, cy)
                    if spanne > wand { wand = spanne }
                }
            } else if nh > 0.0 {
                let grund = 0.5 * nh
                oben += grund
                if waag2 >= min2 * hoch2 {
                    geneigt += grund
                    richtungen.insert(Richtung(a: (n1 / nh / richtungRaster + 0.5).rounded(.down),
                                               b: (n2 / nh / richtungRaster + 0.5).rounded(.down)))
                }
                let t = min(ay, by, cy)
                if tief == nil || t < tief! { tief = t }
            }
        }
        return Oberflaeche(oben: oben, geneigt: geneigt, wand: wand, tief: tief, richtungen: richtungen.count)
    }

    /// Wie viel vom Grundriss des Körpers `alle[stelle]` ist von Tieferem unterspannt
    /// (`gelaendeform.unterbauung`)? Gemessen wird die Hülle der Schnittflächen, nicht deren Summe.
    public static func unterbauung(_ stelle: Int, _ alle: [Koerper]) -> Double {
        let k = alle[stelle]
        let grund = (k.hi[0] - k.lo[0]) * (k.hi[2] - k.lo[2])
        if !(grund > 0) { return 0.0 }
        let grenze = k.lo[1] - unterbautToleranz
        var sLo = [Double.infinity, Double.infinity], sHi = [-Double.infinity, -Double.infinity]
        for (j, a) in alle.enumerated() {
            if j == stelle || !(a.lo[1] < grenze) { continue }
            let x0 = max(a.lo[0], k.lo[0]), x1 = min(a.hi[0], k.hi[0])
            let z0 = max(a.lo[2], k.lo[2]), z1 = min(a.hi[2], k.hi[2])
            if !(x1 > x0 && z1 > z0) { continue }
            sLo = [min(sLo[0], x0), min(sLo[1], z0)]
            sHi = [max(sHi[0], x1), max(sHi[1], z1)]
        }
        if sLo[0] == .infinity { return 0.0 }
        return ((sHi[0] - sLo[0]) * (sHi[1] - sLo[1])) / grund
    }

    /// Ist der Kandidat an seiner Oberfläche nachweislich Gelände (`gelaendeform.beweis`)? `nil` heisst
    /// Gelände, sonst das Kurzwort des Grundes, aus dem er «nicht entscheidbar» bleibt. Die Reihenfolge
    /// der Fragen ist dieselbe wie am Heim-PC: lesbar, Deckung, Lagen, geneigt, uneben, Wand, Sockel,
    /// unterbaut.
    public static func beweis(_ stelle: Int, _ alle: [Koerper], _ flaeche: Oberflaeche?) -> String? {
        // ZWISCHENSTAND (rot vor grün): Der Mac ist noch stumm, kein Beweis gelingt. Die Probendatei
        // der Runde 2 liegt schon; an ihren Geländefällen muss dieser Stand rot sein.
        if stelle >= 0 { return Grund.nichtLesbar }
        guard let flaeche else { return Grund.nichtLesbar }
        let k = alle[stelle]
        let grund = (k.hi[0] - k.lo[0]) * (k.hi[2] - k.lo[2])
        let oben = flaeche.oben
        if !(oben >= deckungMin * grund) || !(oben > 0.0) { return Grund.deckung }
        if oben > lagenMax * grund { return Grund.lagen }
        if !(flaeche.geneigt >= geneigtAnteilMin * oben) { return Grund.eben }
        if flaeche.richtungen < richtungenMin { return Grund.eineEbene }
        if flaeche.wand > wandhoeheMax { return Grund.wand }
        guard let tief = flaeche.tief, !(tief - k.lo[1] > sockelMax) else { return Grund.sockel }
        if unterbauung(stelle, alle) > unterbautMax { return Grund.unterbaut }
        return nil
    }

    /// Die Form fragen, wenn die Namensregel nichts getrennt hat (`glbbox._zweitmeinung` über
    /// `gelaendeform.gelaende_knoten` mit `oberflaechen`).
    ///
    /// `hatteNamen`: Die Namensregel hat etwas gefunden, nur zu wenig. Dann bleibt sie zuständig; die
    /// Form ergänzt nicht und ersetzt nicht. `oberflaeche` liefert je Kandidat die Auskunft über seine
    /// Dreiecke oder `nil`, wenn sie nicht lesbar sind; gefragt wird sie nur für Kandidaten.
    public static func zweitmeinung(_ alle: [Koerper], hatteNamen: Bool,
                                    oberflaeche: (Int) -> Oberflaeche?) -> Zweitmeinung {
        guard let bezug = szenenbezug(alle) else { return .schweigt }
        var gelaende: [Int] = [], gruende: [String] = []
        for stelle in alle.indices {
            let m = merkmale(alle[stelle], bezug: bezug)
            // KANDIDAT: gross genug und nicht aufragend. Alles andere ist Bauwerk.
            if m.grundrissanteil < grundrissanteilMin || m.flachheit > flachheitBewiesenMax { continue }
            let grund = beweis(stelle, alle, oberflaeche(stelle))
            if m.tieflage > tieflageUnklarMax {
                // ZU HOCH: nur wenn der Beweis sonst gelänge, steht der Körper als «nicht entscheidbar»
                // im Befund; ein gewöhnliches Dach bleibt still Bauwerk.
                if grund == nil { gruende.append(Grund.zuHoch) }
                continue
            }
            if let grund { gruende.append(grund) } else { gelaende.append(stelle) }
        }
        // Kein Treffer; ALLES wäre Gelände (dann trennt die Form nichts, und eine leere Hülle wäre
        // schlimmer als eine zu grosse); oder die Namensregel bleibt zuständig.
        let entscheidet = !gelaende.isEmpty && gelaende.count < alle.count && !hatteNamen
        return Zweitmeinung(gelaende: gelaende, unklar: gruende.count, gruende: gruende, entscheidet: entscheidet)
    }
}
