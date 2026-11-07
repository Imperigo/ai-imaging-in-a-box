import Foundation

/// Die Masse der Startseite am Mac und des Fensters «Mappen» (A0264, Visbox 0.3.75).
///
/// Ein Befund des Demotesters: Bei rund 1100 px Fensterbreite war die Startseite abgeschnitten
/// («Schon anfangen» nicht erreichbar), und die Liste «Noch am Heim-PC» liess die Knöpfe darunter
/// springen, sobald sie sich fuellte. Beides ist hier Regel statt Gefuehl, damit eine Probe es
/// halten kann; die Ansichten lesen nur diese Zahlen.
public enum Startmass {
    /// Die kleinste Breite und Hoehe des Mac-Fensters (`Hauptfenster`, `.frame(minWidth:minHeight:)`).
    public static let kleinsteFensterbreite: Double = 1100
    public static let kleinsteFensterhoehe: Double = 700

    /// Breite der Zeilenseite (links): am liebsten so, nie schmaler als die kleinste.
    public static let zeilenseiteWunsch: Double = 620
    public static let zeilenseiteKleinste: Double = 440
    /// Die Trennlinie zwischen den Seiten.
    public static let trennlinie: Double = 1
    /// Die rechte Seite («Wer rechnet wo»): was sie gerne haette, und was sie mindestens braucht.
    public static let rechteSeiteWunsch: Double = 882
    public static let rechteSeiteKleinste: Double = 580

    /// Breite der Zeilenseite bei dieser Fensterbreite: rechts bekommt zuerst seinen Wunsch,
    /// links bleibt dazwischen.
    public static func zeilenseite(fuer fensterbreite: Double) -> Double {
        let frei = fensterbreite - trennlinie - rechteSeiteWunsch
        return min(zeilenseiteWunsch, max(zeilenseiteKleinste, frei))
    }

    /// Ob beide Seiten bei dieser Fensterbreite ganz Platz haben.
    public static func passt(fensterbreite: Double) -> Bool {
        zeilenseite(fuer: fensterbreite) + trennlinie + rechteSeiteKleinste <= fensterbreite
    }
}

/// Die Liste im Fenster «Mappen»: ihre Hoehe haengt nicht davon ab, ob die Antwort des Heim-PC
/// schon da ist oder wie viele Mappen kommen.
public enum Mappenfenster {
    /// Solange der Heim-PC noch nicht geantwortet hat (statt der falschen Auskunft «nichts da»).
    public static let heimLaedtSatz = "Der Heim-PC wird gefragt …"
    public static let hoechstens: Double = 380

    /// Die Hoehe des rollenden Bereichs: **immer dieselbe**. Laedt der Heim-PC noch, steht der
    /// Platz schon da (der Ladesatz sitzt darin); kommen drei oder dreissig Mappen, rollt die
    /// Liste darin. So bewegt sich nichts darunter («Neue Mappe», «Schliessen»).
    public static func listenhoehe(heimLaedt: Bool, zeilen: Int) -> Double {
        hoechstens
    }
}
