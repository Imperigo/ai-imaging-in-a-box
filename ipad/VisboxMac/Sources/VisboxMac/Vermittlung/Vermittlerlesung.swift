import Foundation
import VisboxKern

/// Was der `Vermittlungsdienst` aus dem Schlüsselbund braucht: der Zugang fürs iPad und das
/// Zertifikat des Mac (A0255, Runde 2).
///
/// **Gelesen wird im Hintergrund**, in derselben Arbeit wie die Anmeldung zum Heim-PC
/// (`Heimleitung.leseSchluesselbund`), nie auf dem Hauptfaden: Fragt macOS nach dem Zugang und liegt
/// dessen Fenster hinter unserem, stand die App sonst bis zur Antwort ohne Fenster da. Der Dienst
/// bekommt das Ergebnis fertig (`Vermittlungsdienst.init(heim:lesung:)`) und liest selbst nicht mehr.
struct Vermittlerlesung {
    var zugang: Vermittlerzugang
    /// Warum das iPad nach einem Neustart neu koppeln muss — `nil`: alles gut.
    var satz: String?
    let identitaet: Macidentitaet.Ergebnis

    /// Beide Lesungen hintereinander, in der einen Hintergrundarbeit des Starts.
    static func lies() -> Vermittlerlesung {
        let (zugang, satz) = Vermittlerschluessel.liesOderErzeuge()
        return Vermittlerlesung(zugang: zugang, satz: satz, identitaet: Macidentitaet.liesOderErzeuge())
    }
}
