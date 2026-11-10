import Foundation

// GELÄNDE AN DER FORM ERKENNEN, WENN DER NAME ES NICHT TRÄGT (A0289, «Gelände an der Form»).
//
// Das Abbild von `src/aiimaging/gelaendeform.py` und ihres Einsatzes in `glbbox.bauwerksbox` am
// Heim-PC. Die Regel ist dort erfunden und begründet; hier wird sie nur nachgerechnet, mit denselben
// Rechenschritten in derselben Reihenfolge, damit beide Seiten an den Schwellen dasselbe sagen.
//
// **Keine zweite Regel, sondern eine Zweitmeinung:** Sie spricht nur, wenn die Namensregel
// (`Glbauskunft.istGelaende`) nichts getrennt hat, und sie kennt die dritte Antwort «nicht
// entscheidbar». Gerechnet wird auf den Hüllboxen der Mesh-Knoten aus dem JSON-Kopf der glb (glTF,
// Y oben), ohne Dreiecke und ohne Abhängigkeit.
//
// **Wo der Mac vom Heim-PC abweichen darf:** nur zu «nicht entscheidbar», nie umgekehrt. Heute ist
// das genau ein Fall, die Namensgleichheit (`Zweitmeinung.namensgleich`).
//
// Beide Seiten prüft die gemeinsame Probendatei `tests/daten/glbbox_gelaenderegel.json`
// (`formfaelle`); die Schwellen hier stehen in `tests/test_glbbox_formregel_gemeinsam.py` gegen die
// des Heim-PC fest.
public enum Gelaendeform {
    /// `gelaendeform.GRUNDRISSANTEIL_MIN`: Grundfläche des Körpers geteilt durch die der Szene; darunter
    /// ist er zu klein für Gelände.
    public static let grundrissanteilMin = 0.25
    /// `gelaendeform.FLACHHEIT_MAX`: Höhe geteilt durch die kleinere Grundrisskante; darüber ragt der
    /// Körper auf.
    public static let flachheitMax = 0.15
    /// `gelaendeform.TIEFLAGE_MAX`: Oberkante im Höhenbereich der Szene (0 unten, 1 oben); bis hier
    /// liegt der Körper unten.
    public static let tieflageMax = 0.35
    /// `gelaendeform.TIEFLAGE_UNKLAR_MAX`: bis hier ist ein grosser flacher Körper «nicht entscheidbar»
    /// (Geländesockel oder Tiefgaragendecke), darüber ein Dach oder eine Decke.
    public static let tieflageUnklarMax = 0.60
    /// `glbbox.GERINGE_SCHRUMPFUNG`: Die Form wird nur gefragt, wenn die Namensregel den Grundriss um
    /// weniger als diesen Anteil enger gemacht hat.
    public static let geringeSchrumpfung = 0.05

    /// Die drei Urteile. Keine Wahrheitswerte: «nicht entscheidbar» ist der häufige Fall.
    public enum Urteil: String, Equatable, Sendable {
        case gelaende
        case bauwerk
        case nichtEntscheidbar = "nicht entscheidbar"
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

    /// Was die Form zu einer ganzen Szene sagt.
    public struct Zweitmeinung: Equatable, Sendable {
        /// Die Stellen (in der übergebenen Liste) der Körper, die an der Form Gelände sind.
        public let gelaende: [Int]
        /// Wie viele Körper «nicht entscheidbar» blieben; sie zählen zum Bauwerk.
        public let unklar: Int
        /// `true`: Die Form trennt das Gelände ab (`glbbox`: `entschieden_durch == "form"`).
        public let entscheidet: Bool
        /// `true`: Die Form hätte entschieden, aber ein Bauteil trägt den Namen eines Gelände-Körpers.
        /// Der Heim-PC trennt nach diesen Namen und nähme das Bauteil mit heraus (ohne Namen an allen
        /// Knoten bliebe dort gar keine Box). Der Mac sagt hier «nicht entscheidbar».
        public let namensgleich: Bool

        static let schweigt = Zweitmeinung(gelaende: [], unklar: 0, entscheidet: false, namensgleich: false)
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

    /// Gelände, Bauwerk oder nicht entscheidbar? Dieselbe Reihenfolge der Fragen wie
    /// `gelaendeform.urteil`: erst die Grösse, dann die Flachheit, dann die Lage.
    public static func urteil(_ m: Merkmale) -> Urteil {
        if m.grundrissanteil < grundrissanteilMin { return .bauwerk }
        if m.flachheit > flachheitMax { return .bauwerk }
        if m.tieflage <= tieflageMax { return .gelaende }
        if m.tieflage <= tieflageUnklarMax { return .nichtEntscheidbar }
        return .bauwerk
    }

    /// Das Urteil je Körper (`gelaendeform.gelaende_knoten`, ohne Familienprüfung: sie ist am Heim-PC
    /// Vorgabe aus), oder `nil` für eine Szene ohne Ausdehnung.
    public static func urteile(_ alle: [Koerper]) -> [Urteil]? {
        guard let bezug = szenenbezug(alle) else { return nil }
        return alle.map { urteil(merkmale($0, bezug: bezug)) }
    }

    /// Die Form fragen, wenn die Namensregel nichts getrennt hat (`glbbox._zweitmeinung`).
    ///
    /// `hatteNamen`: Die Namensregel hat etwas gefunden, nur zu wenig. Dann bleibt sie zuständig; die
    /// Form ergänzt nicht und ersetzt nicht.
    public static func zweitmeinung(_ alle: [Koerper], hatteNamen: Bool) -> Zweitmeinung {
        guard let alleUrteile = urteile(alle) else { return .schweigt }
        let gelaende = alleUrteile.indices.filter { alleUrteile[$0] == .gelaende }
        let unklar = alleUrteile.filter { $0 == .nichtEntscheidbar }.count
        // Kein Treffer; ALLES wäre Gelände (dann trennt die Form nichts, und eine leere Hülle wäre
        // schlimmer als eine zu grosse); oder die Namensregel bleibt zuständig.
        guard !gelaende.isEmpty, gelaende.count < alle.count, !hatteNamen else {
            return Zweitmeinung(gelaende: gelaende, unklar: unklar, entscheidet: false, namensgleich: false)
        }
        let namen = Set(gelaende.map { alle[$0].name })
        let weg = Set(gelaende)
        let gleich = alle.indices.contains { !weg.contains($0) && namen.contains(alle[$0].name) }
        return Zweitmeinung(gelaende: gelaende, unklar: unklar, entscheidet: !gleich, namensgleich: gleich)
    }
}
