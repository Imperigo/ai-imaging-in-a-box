import Foundation

/// Die Fassungswache des stdio-Wegs (Mac-Probe 0.3.67, 25.10.2026).
///
/// Claude Desktop startet die App mit `--mcp-stdio` als eigenen Prozess, wenn die Claude-Sitzung beginnt.
/// Nach einer Aktualisierung der Mac-App laeuft dieser Prozess mit dem **alten** Code im Speicher
/// weiter, waehrend die App auf 127.0.0.1 schon neu ist — der Demotester sah darum einen alten
/// Werkzeugkatalog. Kein Fehler im Code, nur die Reihenfolge; aber niemand sah es.
///
/// Jetzt nennt die App ihre Fassung in jeder Antwort auf `/mcp` (Kopf `X-App-Fassung`), und der
/// stdio-Weg vergleicht sie mit seiner eigenen (gelesen beim Start). Weichen sie ab, steht vor dem
/// Text jedes Werkzeugergebnisses **eine Warnzeile** — kein Fehler, der Aufruf gilt.
/// Ohne Kopf (eine App vor diesem Bau) liest die Wache die Zeile «Fassung: …» aus `visbox_status`.
public enum Mcpfassungswache {
    /// Der Kopf, mit dem die App ihre Fassung nennt.
    public static let kopf = "X-App-Fassung"

    /// Die Antwort der App mit ihrer Fassung im Kopf.
    public static func mitFassung(_ antwort: Leitungsantwort, _ fassung: String) -> Leitungsantwort {
        Leitungsantwort(status: antwort.status, koepfe: antwort.koepfe + [Kopfzeile(kopf, fassung)],
                        rumpf: antwort.rumpf)
    }

    /// Die Warnzeile, wenn der stdio-Weg und die App verschiedene Fassungen haben — sonst `nil`
    /// (gleich, oder die Fassung der App ist unbekannt).
    public static func warnung(bruecke: String, app: String?) -> String? {
        let b = bruecke.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let a = app?.trimmingCharacters(in: .whitespacesAndNewlines), !a.isEmpty, !b.isEmpty,
              a != b else { return nil }
        return "Claude-Verbindung läuft mit \(b), App ist \(a) — Claude neu starten."
    }

    /// Die Fassung der App aus ihrer HTTP-Antwort: der Kopf, sonst die Zeile «Fassung: <Marke> X.»
    /// im Text (`Mcpkern.fassungsSatz`).
    public static func appFassung(ausAntwort daten: Data) -> String? {
        if let grenze = Anfrageleser.kopfende(daten),
           let kopfText = String(data: daten.prefix(grenze.kopfLaenge), encoding: .isoLatin1) {
            for zeile in kopfText.components(separatedBy: "\r\n").dropFirst() {
                guard let d = zeile.firstIndex(of: ":"),
                      zeile[..<d].lowercased() == kopf.lowercased() else { continue }
                let wert = zeile[zeile.index(after: d)...].trimmingCharacters(in: .whitespaces)
                if !wert.isEmpty { return wert }
            }
        }
        let text = String(decoding: daten, as: UTF8.self)
        let vorne = "Fassung: \(Marke.name) "
        guard let anfang = text.range(of: vorne) else { return nil }
        let rest = text[anfang.upperBound...]
        let nummer = rest.prefix { $0.isNumber || $0 == "." }
        let sauber = nummer.hasSuffix(".") ? String(nummer.dropLast()) : String(nummer)
        return sauber.isEmpty ? nil : sauber
    }

    /// Die Antwortzeile an Claude mit der Warnung vorn im ersten Text eines Werkzeugergebnisses
    /// (`result.content[0].text`). Andere Antworten (initialize, tools/list, Fehler) bleiben, wie sie sind.
    public static func zeile(_ zeile: String, warnung: String?) -> String {
        guard let warnung, let wert = try? JSONWert.lies(Data(zeile.utf8)),
              var aussen = wert.alsObjekt, var ergebnis = aussen["result"]?.alsObjekt,
              var inhalt = ergebnis["content"]?.alsListe, var erstes = inhalt.first?.alsObjekt,
              erstes["type"]?.alsText == "text", let text = erstes["text"]?.alsText else { return zeile }
        erstes["text"] = .text("⚠ " + warnung + "\n" + text)
        inhalt[0] = .objekt(erstes)
        ergebnis["content"] = .liste(inhalt)
        aussen["result"] = .objekt(ergebnis)
        return Mcpweiterleitung.zeile(.objekt(aussen)) ?? zeile
    }
}
