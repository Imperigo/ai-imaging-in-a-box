import Foundation

/// «Exportieren» aus der Knotenansicht (Video-Befund L3-A4, Demolauf 16.10.2026): Die grosse
/// Ansicht eines Laufs gibt das Bild im Original heraus. Im Browser ist das ein gewöhnliches
/// Herunterladen; in der Mac-App fängt die Webfläche es ab und zeigt den Sichern-Dialog des Mac
/// (`Flaechenlotse`, `WKDownloadDelegate`). Diese Datei sagt nur, **welcher Name dort
/// vorgeschlagen wird** — ohne Plattform, darum auch unter Linux geprüft.
///
/// Die Seite schlägt einen Namen vor (`Projekt-Lauf-3-K1.png`). Er kommt aus einer Webseite und
/// wird darum bereinigt, bevor er in einen Dialog geht: nur der letzte Teil eines Pfads, keine
/// Steuerzeichen, kein Doppelpunkt (der Finder zeigt ihn als Schrägstrich), kein Punkt am
/// Anfang (sonst wäre die Datei unsichtbar), höchstens 120 Zeichen, und eine Endung muss da sein.
public enum Sichername {
    /// Der Name, wenn die Seite keinen brauchbaren mitgibt — aus dem Namen der App (`Marke`, an einer Stelle).
    public static var vorgabe: String { Marke.name + "-Bild.png" }

    /// Längste Länge des Vorschlags (mit Endung).
    public static let hoechstens = 120

    public static func vorschlag(_ angebot: String?) -> String {
        guard let angebot else { return vorgabe }
        let letzter = angebot.split(whereSeparator: { $0 == "/" || $0 == "\\" }).last.map(String.init) ?? ""
        var name = String(letzter.unicodeScalars.filter { !CharacterSet.controlCharacters.contains($0) })
            .replacingOccurrences(of: ":", with: "-")
            .trimmingCharacters(in: .whitespaces)
        while name.hasPrefix(".") { name.removeFirst() }
        name = name.trimmingCharacters(in: .whitespaces)
        guard !name.isEmpty else { return vorgabe }
        var endung = ""
        if let punkt = name.lastIndex(of: "."), punkt != name.startIndex,
           name.distance(from: punkt, to: name.endIndex) <= 6 {
            endung = String(name[punkt...])
            name = String(name[..<punkt])
        } else {
            endung = ".png"
        }
        let platz = max(1, hoechstens - endung.count)
        if name.count > platz { name = String(name.prefix(platz)) }
        return name + endung
    }
}
