import Foundation

/// Die gemerkte Lesung des Schlüsselbunds, die spätere Dienste übernehmen (A0265, N1).
///
/// Die Lesung entsteht einmal im Hintergrund beim Start. Ändert sich der Zugang danach (z. B. «iPad
/// vergessen» erzeugt einen neuen), führt der Besitzer des Merkers sie nach (`fuehreNach`), damit ein
/// später angelegter Dienst (Wechsel von Adresse oder Anmeldung des Heim-PC, Einrichten, Koppeln) nicht
/// mit dem alten Zugang aus der Startlesung entsteht. Gelesen wird dafür nichts: weder auf dem
/// Hauptfaden noch sonst, der Dienst meldet den neuen Wert selbst.
///
/// Reine Regel, ohne Apple-Teile — darum mit Proben unter Linux.
public struct Lesungsmerker<Lesung> {
    public private(set) var lesung: Lesung?

    public init() {}

    /// Die Startlesung (oder `nil`: noch keine).
    public mutating func uebernimm(_ neu: Lesung?) {
        lesung = neu
    }

    /// Ändert die gemerkte Lesung. Ohne Startlesung gibt es keinen Dienst und nichts nachzuführen.
    public mutating func fuehreNach(_ aendere: (inout Lesung) -> Void) {
        guard var l = lesung else { return }
        aendere(&l)
        lesung = l
    }
}
