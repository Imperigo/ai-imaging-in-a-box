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
    public static let flachheitBewiesenMax = 0.40
    /// `gelaendeform.LAGE_BEWIESEN_MAX`: Oberkante im Höhenbereich der Szene (0 unten, 1 oben). Liegt
    /// sie höher und gelänge der Beweis sonst, heisst das Urteil «nicht entscheidbar» (`zu_hoch`).
    public static let lageBewiesenMax = 0.70
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
    /// `gelaendeform.STREUUNG_QUER_MIN`: so breit streuen die Gefällerichtungen quer zu ihrer Hauptrichtung
    /// mindestens. Eine Tonne oder ein Sheddach fällt nur nach zwei Seiten, gewachsener Boden nach allen.
    public static let streuungQuerMin = 1.0
    /// `gelaendeform.RICHTUNG_RASTER`: die Feldweite, in der Richtungen gezählt werden.
    public static let richtungRaster = 0.01
    /// `gelaendeform.WANDHOEHE_MAX`: so hoch darf eine steile Fläche im Inneren des Körpers aufragen.
    public static let wandhoeheMax = 2.0
    /// `gelaendeform.SOCKEL_MAX`: so hoch darf die tiefste Stelle der Oberseite über der Unterkante liegen.
    public static let sockelMax = 1.5
    /// `gelaendeform.TRAEGT_ANTEIL_MIN`: Was die Szene überragt, steht zu mindestens diesem Anteil seines
    /// Grundrisses auf dem bewiesenen Gelände. Eine Schale neben einem Turm trägt ihn nicht.
    public static let traegtAnteilMin = 0.5
    /// `gelaendeform.TRAEGT_FLAECHE_MIN`: und mit mindestens so vielen Quadratmetern (ein Raum, kein Mast).
    public static let traegtFlaecheMin = 4.0
    /// `gelaendeform.FUSS_MAX`: die Fussprobe. Die Unterkante dessen, was auf Gelände steht, liegt
    /// höchstens so viel unter der Oberseite an seinem Standort. Ein Turm, der durch eine Kuppel stösst,
    /// beginnt mehrere Meter darunter: Er steht nicht darauf, er steht darin.
    public static let fussMax = 3.5
    /// `gelaendeform.RASTER_FELDER`: Felder je Richtung, in denen die Oberseite für die Fussprobe liegt.
    public static let rasterFelder = 16
    /// `glbbox.ECKE_HOECHSTENS`: grösser darf keine Koordinate einer Ecke sein, sonst «nicht lesbar».
    public static let eckeHoechstens = 1_000_000_000.0
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
        public static let einfachGekruemmt = "einfach_gekruemmt"
        public static let wand = "wand"
        public static let sockel = "sockel"
        public static let unterbaut = "unterbaut"
        public static let traegtNicht = "traegt_nicht"
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

    /// Die Oberseite eines Körpers aus seinen Dreiecken (`gelaendeform.oberseite`).
    public struct Oberseite: Equatable, Sendable {
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
        /// Die Varianz der Richtungsfelder entlang ihrer kleineren Hauptachse (`_streuung_quer`).
        public let streuungQuer: Double
        /// Der Rand des Körpers im Grundriss (x, z) und je Feld die höchste Ecke der Oberseite
        /// (`-.infinity`: dort liegt keine); leer, wenn kein Raster gerechnet ist.
        public let rasterLo: [Double]
        public let rasterHi: [Double]
        public let raster: [Double]
        public init(oben: Double, geneigt: Double, wand: Double, tief: Double?, richtungen: Int,
                    streuungQuer: Double = 100,
                    rasterLo: [Double] = [], rasterHi: [Double] = [], raster: [Double] = []) {
            self.oben = oben
            self.geneigt = geneigt
            self.wand = wand
            self.tief = tief
            self.richtungen = richtungen
            self.streuungQuer = streuungQuer
            self.rasterLo = rasterLo
            self.rasterHi = rasterHi
            self.raster = raster
        }

        /// Die höchste Stelle der Oberseite über einem Rechteck im Grundriss (`gelaendeform.oberkante_bei`),
        /// `nil`, wenn dort keine Oberseite liegt.
        public func oberkante(x0: Double, x1: Double, z0: Double, z1: Double) -> Double? {
            guard raster.count == rasterFelder * rasterFelder, rasterLo.count == 2, rasterHi.count == 2 else { return nil }
            if x1 < rasterLo[0] || x0 > rasterHi[0] || z1 < rasterLo[1] || z0 > rasterHi[1] { return nil }
            var hoechste = -Double.infinity
            let b1 = rasterHi[0] - rasterLo[0], b2 = rasterHi[1] - rasterLo[1]
            for j in Gelaendeform.feld(z0, rasterLo[1], b2) ... Gelaendeform.feld(z1, rasterLo[1], b2) {
                for i in Gelaendeform.feld(x0, rasterLo[0], b1) ... Gelaendeform.feld(x1, rasterLo[0], b1) {
                    let h = raster[j * rasterFelder + i]
                    if h > hoechste { hoechste = h }
                }
            }
            return hoechste == -Double.infinity ? nil : hoechste
        }
    }

    /// Das Feld des Rasters, in dem `wert` liegt (0 bis `rasterFelder - 1`).
    static func feld(_ wert: Double, _ lo: Double, _ breite: Double) -> Int {
        if !(breite > 0.0) { return 0 }
        let f = ((wert - lo) / breite * Double(rasterFelder)).rounded(.down)
        if !(f > 0) { return 0 }
        return f >= Double(rasterFelder - 1) ? rasterFelder - 1 : Int(f)
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

    // MARK: Der Beweis an der Oberseite

    private struct Richtung: Hashable {
        let a: Double
        let b: Double
    }

    /// Die Oberseite aus Dreiecken in Weltkoordinaten (glTF, Y oben): `ecken` trägt je Dreieck neun
    /// Zahlen (a, b, c je x, y, z), Umlaufsinn gegen den Uhrzeiger von aussen. `gespiegelt`: Die
    /// Knotenmatrix spiegelt, der Umlaufsinn dreht sich.
    ///
    /// Dieselben Rechenschritte in derselben Reihenfolge wie `gelaendeform.oberseite` (mit `hoch = 1`).
    public static func oberseite(dreiecke ecken: [Double], gespiegelt: Bool) -> Oberseite {
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
        var raster = [Double](repeating: -.infinity, count: rasterFelder * rasterFelder)
        let breite1 = hi1 - lo1, breite2 = hi2 - lo2
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
                let hoechste = max(ay, by, cy)
                let i0 = feld(min(ax, bx, cx), lo1, breite1), i1 = feld(max(ax, bx, cx), lo1, breite1)
                let j0 = feld(min(az, bz, cz), lo2, breite2), j1 = feld(max(az, bz, cz), lo2, breite2)
                for j in j0 ... j1 { for i in i0 ... i1 where hoechste > raster[j * rasterFelder + i] {
                    raster[j * rasterFelder + i] = hoechste
                } }
            }
        }
        // Die Streuung quer, in ganzen Zahlen gerechnet (die Felder sind ganzzahlig): So ändert die
        // Reihenfolge der Menge nichts, und Heim-PC und Mac kommen auf dasselbe.
        var streuung = 0.0
        let n = richtungen.count
        if n >= 2 {
            var sa = 0, sb = 0, saa = 0, sbb = 0, sab = 0
            for r in richtungen {
                let a = Int(r.a), b = Int(r.b)
                sa += a; sb += b; saa += a * a; sbb += b * b; sab += a * b
            }
            let xx = n * saa - sa * sa, yy = n * sbb - sb * sb, xy = n * sab - sa * sb
            let wurzel = Double((xx - yy) * (xx - yy) + 4 * xy * xy).squareRoot()
            streuung = (Double(xx + yy) - wurzel) / 2.0 / Double(n * n)
        }
        return Oberseite(oben: oben, geneigt: geneigt, wand: wand, tief: tief, richtungen: richtungen.count,
                         streuungQuer: streuung, rasterLo: [lo1, lo2], rasterHi: [hi1, hi2], raster: raster)
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

    /// Steht das, was die Szene überragt, auf dem bewiesenen Gelände (`gelaendeform.traegt`)? Gemessen
    /// gegen die gemeinsame Hüllbox aller Gelände-Körper im Grundriss.
    ///
    /// `nurFlaeche`: nur die Mindestfläche prüfen. So wird jeder Gelände-Körper einzeln gefragt, ob
    /// überhaupt etwas Hohes auf IHM steht; der Anteil gilt für alle zusammen.
    ///
    /// `flaechen`: die Oberseiten der Gelände-Körper. Sind sie gegeben, zählt ein überragender Körper
    /// nur, wenn er die Fussprobe besteht (`fussMax`).
    public static func traegt(_ gelaende: [Int], _ alle: [Koerper], nurFlaeche: Bool = false,
                              flaechen: [Int: Oberseite]? = nil) -> Bool {
        if gelaende.isEmpty { return false }
        var lo1 = Double.infinity, lo2 = Double.infinity, hi1 = -Double.infinity, hi2 = -Double.infinity
        var oben = -Double.infinity
        for i in gelaende {
            lo1 = min(lo1, alle[i].lo[0]); lo2 = min(lo2, alle[i].lo[2])
            hi1 = max(hi1, alle[i].hi[0]); hi2 = max(hi2, alle[i].hi[2])
            oben = max(oben, alle[i].hi[1])
        }
        let weg = Set(gelaende)
        var gesamt = 0.0, innen = 0.0
        for (j, k) in alle.enumerated() {
            if weg.contains(j) || !(k.hi[1] > oben) { continue }
            gesamt += (k.hi[0] - k.lo[0]) * (k.hi[2] - k.lo[2])
            let x0 = max(k.lo[0], lo1), x1 = min(k.hi[0], hi1)
            let z0 = max(k.lo[2], lo2), z1 = min(k.hi[2], hi2)
            if !(x1 > x0 && z1 > z0) { continue }
            if let flaechen {
                var aufgesetzt = false
                for i in gelaende {
                    if let kante = flaechen[i]?.oberkante(x0: k.lo[0], x1: k.hi[0], z0: k.lo[2], z1: k.hi[2]),
                       !(kante - k.lo[1] > fussMax) {
                        aufgesetzt = true
                        break
                    }
                }
                if !aufgesetzt { continue }
            }
            innen += (x1 - x0) * (z1 - z0)
        }
        if nurFlaeche { return innen >= traegtFlaecheMin }
        return innen >= traegtFlaecheMin && innen >= traegtAnteilMin * gesamt
    }

    /// Ist der Kandidat an seiner Oberseite nachweislich Gelände (`gelaendeform.beweis`)? `nil` heisst
    /// Gelände, sonst das Kurzwort des Grundes, aus dem er «nicht entscheidbar» bleibt. Die Reihenfolge
    /// der Fragen ist dieselbe wie am Heim-PC: lesbar, Deckung, Lagen, geneigt, uneben, Wand, Sockel,
    /// unterbaut.
    public static func beweis(_ stelle: Int, _ alle: [Koerper], _ flaeche: Oberseite?) -> String? {
        guard let flaeche else { return Grund.nichtLesbar }
        let k = alle[stelle]
        let grund = (k.hi[0] - k.lo[0]) * (k.hi[2] - k.lo[2])
        let oben = flaeche.oben
        if !(oben >= deckungMin * grund) || !(oben > 0.0) { return Grund.deckung }
        if oben > lagenMax * grund { return Grund.lagen }
        if !(flaeche.geneigt >= geneigtAnteilMin * oben) { return Grund.eben }
        if flaeche.richtungen < richtungenMin { return Grund.eineEbene }
        if flaeche.streuungQuer < streuungQuerMin { return Grund.einfachGekruemmt }
        if flaeche.wand > wandhoeheMax { return Grund.wand }
        guard let tief = flaeche.tief, !(tief - k.lo[1] > sockelMax) else { return Grund.sockel }
        if unterbauung(stelle, alle) > unterbautMax { return Grund.unterbaut }
        return nil
    }

    /// Die Form fragen, wenn die Namensregel nichts getrennt hat (`glbbox._zweitmeinung` über
    /// `gelaendeform.gelaende_knoten` mit `oberseiten`).
    ///
    /// `hatteNamen`: Die Namensregel hat etwas gefunden, nur zu wenig. Dann bleibt sie zuständig; die
    /// Form ergänzt nicht und ersetzt nicht. `oberseite` liefert je Kandidat die Auskunft über seine
    /// Dreiecke oder `nil`, wenn sie nicht lesbar sind; gefragt wird sie nur für Kandidaten.
    public static func zweitmeinung(_ alle: [Koerper], hatteNamen: Bool,
                                    oberseite: (Int) -> Oberseite?) -> Zweitmeinung {
        guard let bezug = szenenbezug(alle) else { return .schweigt }
        var gelaende: [Int] = [], gruende: [String] = []
        // Die Körper, die Gelände oder «nicht entscheidbar» wurden, in ihrer Reihenfolge.
        var reihenfolge: [Int] = []
        var flaechen: [Int: Oberseite] = [:]
        for stelle in alle.indices {
            let m = merkmale(alle[stelle], bezug: bezug)
            // KANDIDAT: gross genug und nicht aufragend. Alles andere ist Bauwerk.
            if m.grundrissanteil < grundrissanteilMin || m.flachheit > flachheitBewiesenMax { continue }
            let flaeche = oberseite(stelle)
            if let flaeche { flaechen[stelle] = flaeche }
            let grund = beweis(stelle, alle, flaeche)
            if m.tieflage > lageBewiesenMax {
                // ZU HOCH: nur wenn der Beweis sonst gelänge, steht der Körper als «nicht entscheidbar»
                // im Befund; ein gewöhnliches Dach bleibt still Bauwerk.
                if grund == nil { gruende.append(Grund.zuHoch); reihenfolge.append(stelle) }
                continue
            }
            if let grund { gruende.append(grund) } else { gelaende.append(stelle) }
            reihenfolge.append(stelle)
        }
        // GELÄNDE TRÄGT: Steht das, was die Szene überragt, nicht auf dem bewiesenen Gelände, ist es
        // eine Schale, ein Zelt, eine Halle NEBEN dem Hohen. Dann bleibt alles in der Hülle. Die Gründe
        // stehen in der Reihenfolge der Körper, wie am Heim-PC.
        // Zuerst JEDER für sich (ein Zelt neben dem Haus am Hang wird nicht mitgenommen, nur weil der
        // Hang das Haus trägt), dann alle zusammen gegen ihre gemeinsame Hülle.
        var allein = gelaende.filter { !traegt([$0], alle, nurFlaeche: true, flaechen: flaechen) }
        let zusammen = gelaende.filter { !allein.contains($0) }
        if !zusammen.isEmpty, !traegt(zusammen, alle, flaechen: flaechen) { allein = gelaende }
        if !allein.isEmpty {
            let fallen = Set(allein)
            let bewiesen = Set(gelaende)
            var neu: [String] = [], alt = gruende.makeIterator()
            for stelle in reihenfolge {
                if fallen.contains(stelle) { neu.append(Grund.traegtNicht) }
                else if !bewiesen.contains(stelle), let g = alt.next() { neu.append(g) }
            }
            gelaende = gelaende.filter { !fallen.contains($0) }
            gruende = neu
        }
        // Kein Treffer; ALLES wäre Gelände (dann trennt die Form nichts, und eine leere Hülle wäre
        // schlimmer als eine zu grosse); oder die Namensregel bleibt zuständig.
        let entscheidet = !gelaende.isEmpty && gelaende.count < alle.count && !hatteNamen
        return Zweitmeinung(gelaende: gelaende, unklar: gruende.count, gruende: gruende, entscheidet: entscheidet)
    }
}
