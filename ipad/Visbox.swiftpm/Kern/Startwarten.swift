import Foundation

/// Der Start der Mac-App wartet nicht auf den Schlüsselbund (A0255, Mac-Abend 06.11.2026).
///
/// **Anlass:** Fragt macOS nach dem Zugang zum Schlüsselbund, liegt dessen Fenster oft HINTER
/// dem der App, und die App stand bis zur Antwort ohne Fenster da, still. Der Lesevorgang
/// (`Heimschluesselbund.lies()`) bleibt inhaltlich, wie er ist; nur das Warten darauf wandert
/// in den Hintergrund. Das Fenster steht zuerst, und solange gelesen wird, steht im Fenster der
/// Hinweis.
///
/// Reine Regel und ein kleiner Läufer, ohne Apple-Teile — darum mit Proben unter Linux.
public enum Startwarten {

    /// Der Satz im Fenster, solange der Schlüsselbund noch liest.
    public static let schluesselbundHinweis =
        "Der Schlüsselbund fragt nach dem Zugang. Das Fenster dazu liegt eventuell hinter diesem."

    /// Der Hinweis — `nil`, sobald nicht mehr gelesen wird.
    public static func hinweis(liest: Bool) -> String? {
        liest ? schluesselbundHinweis : nil
    }

    /// Ob «Einrichten» aufgehen soll: nie, solange der Schlüsselbund noch liest (die Anmeldung
    /// fehlt dann nur scheinbar), sonst wenn Adresse oder Anmeldung fehlen.
    public static func brauchtEinrichten(liest: Bool, adresseDa: Bool, anmeldungDa: Bool) -> Bool {
        guard !liest else { return false }
        return !adresseDa || !anmeldungDa
    }

    /// Liest im Hintergrund und kehrt SOFORT zurück. `fertig` kommt später, auf `antwort`
    /// (vorgegeben: der Hauptfaden).
    public static func starte<Wert>(
        _ lies: @escaping () -> Wert,
        fertig: @escaping (Wert) -> Void,
        arbeit: DispatchQueue = .global(qos: .userInitiated),
        antwort: DispatchQueue = .main
    ) {
        let lies = UncheckedBox(lies)
        let fertig = UncheckedBox(fertig)
        arbeit.async {
            let wert = UncheckedBox(lies.wert())
            antwort.async { fertig.wert(wert.wert) }
        }
    }

    /// Der Satz, wenn eine zweite Instanz derselben Kennung startet und die laufende nach vorn
    /// kommt — statt dass der Start still mit Fehler -10810 endet.
    public static func zweiteInstanz(name: String) -> String {
        "\(name) läuft schon. Das laufende Fenster kommt nach vorn; dieser zweite Start endet."
    }

    /// Hüllt einen Wert, den die Sprache nicht als sendbar kennt, aber nur einmal weitergereicht wird.
    private struct UncheckedBox<T>: @unchecked Sendable {
        let wert: T
        init(_ wert: T) { self.wert = wert }
    }
}
