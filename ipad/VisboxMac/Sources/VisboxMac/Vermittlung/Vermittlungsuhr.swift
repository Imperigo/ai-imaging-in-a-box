import Foundation

/// Die Uhr der Vermittlung — **stetig und mit dem Ruhezustand**: Sie springt nicht zurück,
/// wenn jemand die Wanduhr stellt, und sie läuft weiter, während der Deckel zu ist.
///
/// *Warum nicht `systemUptime` (Sicherheitsdurchsicht vom 01.10.2026):* Die steht im
/// Ruhezustand still. Eine Zahl zum Koppeln, um 18 Uhr gezeigt und mit dem Deckel
/// zugeklappt, galt am nächsten Morgen in einem fremden WLAN noch für die Minuten, die bis
/// zum Zuklappen fehlten. `ContinuousClock` zählt nach Apples Unterlagen auch den Schlaf
/// (auf macOS `CLOCK_MONOTONIC_RAW`, auf Linux `CLOCK_BOOTTIME`).
///
/// Die Uhr gehört **dem Mac-Teil, nicht dem Kern**: Der Kern rechnet mit dem `jetzt`, das
/// man ihm gibt (`Vermittlerkopplung`, `Vermittlerstand`), und bleibt so ohne Annahme über
/// das System — die Proben stellen ihn auf jede Zeit.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026)* — dass sie über einen Ruhezustand wirklich
/// weiterzählt, prüft erst ein zugeklappter Mac.
enum Vermittlungsuhr {
    /// Der Nullpunkt — der erste Blick auf die Uhr in diesem Programm.
    private static let anfang = ContinuousClock.now

    /// Sekunden seit `anfang`, **mit** Ruhezustand.
    static var jetzt: TimeInterval {
        let (sekunden, attosekunden) = anfang.duration(to: ContinuousClock.now).components
        return TimeInterval(sekunden) + TimeInterval(attosekunden) / 1e18
    }
}
