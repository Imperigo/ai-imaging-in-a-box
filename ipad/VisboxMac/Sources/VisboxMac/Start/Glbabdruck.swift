import CryptoKit
import Foundation
import VisboxKern

/// Der Inhalts-Abdruck der `modell.glb` einer Mappe am Mac (A0063 Runde 2, Satz 7, 31.10.2026).
///
/// **Anlass:** Nach «Modell laden» zeigte die Mappe am Mac die Bauteile und die Hüllbox eines
/// früheren Modells. Runde 1 erkannte das an der Dateigrösse (`glb_bytes`) — zwei Modelle gleicher
/// Grösse wären dabei dasselbe gewesen. Jetzt rechnet der Mac dieselbe Summe wie der Heim-PC
/// (`projekt.fingerabdruck`: SHA-256 über die Bytes aus `Mappenkern.abdruckBereiche`, dahinter die
/// Grösse als Text) und vergleicht sie mit `glb_abdruck.summe` der Auskunft
/// (`Mappenkern.auskunftVeraltet`).
///
/// CryptoKit ist Plattform wie in `Heimvertrauen` (NOTICE), keine neue Abhängigkeit. Die Regel,
/// WELCHE Bytes eingehen, steht im Kern (unter Linux prüfbar); hier wird nur gelesen und gerechnet.
///
/// *Gebaut, am Gerät unbestätigt (31.10.2026) — XCTest und Übersetzer laufen in der Cloud nicht.*
enum Glbabdruck {

    /// Die Summe der `modell.glb` im Mappenordner, klein geschrieben, oder `nil`, wenn sie nicht
    /// liegt oder sich nicht lesen lässt (dann zeigt die Mappe keine Zahlen, `nicht_lesbar`).
    static func summe(in ordner: URL) -> String? {
        let datei = ordner.appendingPathComponent(Mappenkern.modelldatei)
        guard let groesse = (try? FileManager.default.attributesOfItem(atPath: datei.path))?[.size] as? Int,
              let griff = try? FileHandle(forReadingFrom: datei) else { return nil }
        defer { try? griff.close() }
        var hasch = SHA256()
        let block = 1024 * 1024
        for bereich in Mappenkern.abdruckBereiche(groesse: groesse).bereiche {
            do {
                try griff.seek(toOffset: UInt64(bereich.lowerBound))
                var rest = bereich.count
                while rest > 0 {
                    guard let stueck = try griff.read(upToCount: min(block, rest)), !stueck.isEmpty else {
                        return nil
                    }
                    hasch.update(data: stueck)
                    rest -= stueck.count
                }
            } catch {
                return nil
            }
        }
        hasch.update(data: Mappenkern.abdruckSchluss(groesse: groesse))
        return Fingerabdruck.hex(Array(hasch.finalize()))
    }
}
