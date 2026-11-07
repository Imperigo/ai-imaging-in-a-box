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
    public static let zeilenseiteKleinste: Double = 620
    /// Die Trennlinie zwischen den Seiten.
    public static let trennlinie: Double = 1
    /// Die rechte Seite («Wer rechnet wo»): was sie gerne haette, und was sie mindestens braucht.
    public static let rechteSeiteWunsch: Double = 882
    public static let rechteSeiteKleinste: Double = 882

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
    public static let zeilenhoehe: Double = 46
    public static let kopfhoehe: Double = 60
    public static let hoechstens: Double = 380

    /// Die Hoehe des rollenden Bereichs.
    public static func listenhoehe(heimLaedt: Bool, zeilen: Int) -> Double {
        min(hoechstens, kopfhoehe + Double(zeilen) * zeilenhoehe)
    }
}
