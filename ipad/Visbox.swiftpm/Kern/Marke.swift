import Foundation

/// Wie die App heisst, unter welcher Kennung sie läuft und welchen Dienst sie im Heimnetz
/// sucht — **an genau dieser einen Stelle.**
///
/// Der Anlass ist ein Owner-Entscheid vom 22.09.2026: Nach der Abgabe der Arbeit wird die
/// App in KosmoOrbit eingebaut und heisst dann anders. Ein Name, der an zwanzig Stellen
/// steht, wird an neunzehn umbenannt — und die zwanzigste zeigt danach den alten Namen
/// an einer Stelle, an der niemand mehr hinsieht.
///
///     *Was an zwei Stellen steht, ist an einer davon bereits veraltet.*
///
/// **Was die Plattform trotzdem zweimal verlangt, und es steht hier, damit es niemand
/// übersieht:** Das App-Manifest (`Visbox.swiftpm/Package.swift`) kann diese Datei nicht
/// lesen — ein Manifest wird übersetzt, bevor es die Quellen gibt. Kennung und Dienst
/// stehen dort darum ein zweites Mal. `tests/test_ipad_geruest.py` prüft, dass beide
/// Stellen übereinstimmen, und dass sonst keine Swift-Datei sie nennt.
public enum Marke {
    /// Der Name, den ein Mensch sieht. Auf der HomeStation tragen ihn der Rundruf
    /// (`rundruf.NAME`) und die Koppelseite (`server.NAME`, aus `rundruf.NAME`) —
    /// beide gegen diese Zeile bewacht.
    public static let name = "Visbox"

    /// Die Bundle-Kennung (umgekehrte Domain-Schreibweise).
    ///
    /// **Ein Platzhalter nach RFC 2606** (`example` gehört niemandem): Er nennt keinen
    /// Menschen und kein Büro (Regel 3). Vor dem ersten Aufspielen auf ein Gerät gegen
    /// eine eigene Kennung tauschen — hier und im Manifest, sonst schlägt die Prüfung an.
    public static let kennung = "org.example.visbox"

    /// Der Dienst, unter dem die HomeStation im Heimnetz gesucht wird (Bonjour-Form
    /// `_name._tcp`).
    ///
    /// **Der Server kündigt ihn seit dem 22.09.2026 an** — mit `--im-heimnetz`
    /// (`oberflaeche/rundruf.py`, dieselbe Zeichenkette, bewacht in
    /// `tests/test_rundruf.py`); siehe `docs/VISBOX_PROTOKOLL.md`, §8. Dass ein echtes iPad
    /// ihn findet, ist am Gerät unbestätigt. Er steht hier, weil iOS verlangt, dass eine
    /// App jeden Dienst, den sie sucht, vorher im Manifest nennt.
    public static let dienst = "_visbox._tcp"
}
