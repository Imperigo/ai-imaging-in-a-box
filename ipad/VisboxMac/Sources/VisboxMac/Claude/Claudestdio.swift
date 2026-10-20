import Foundation
import Network
import VisboxKern

/// `Visbox --mcp-stdio` — der Weg fuer **Claude Desktop**, ohne Fenster (wie
/// `kosmo-orbit --mcp-stdio`, KosmoOrbit `claude_mcp.rs`/`stdio.rs`).
///
/// Claude Desktop startet MCP-Server als Prozess und spricht ueber stdin/stdout: eine
/// JSON-RPC-Nachricht je Zeile. In diesem Modus oeffnet Visbox **kein Fenster**; jede Zeile
/// geht per `POST /mcp` an die laufende App auf `127.0.0.1:8631` (`Claudeanschluss`), die
/// Antwort als eine Zeile zurueck nach stdout.
///
/// **Laeuft die App nicht**, antwortet ein eigener Kern mit dem Platzhalter «ohne App»:
/// `visbox_status` sagt, dass der Architekt Visbox oeffnen muss; nichts wird ausgefuehrt. Jede
/// Zeile fragt neu — kommt die App spaeter, geht die naechste Zeile schon zu ihr.
///
/// stdout gehoert allein dem Protokoll; Hinweise gehen nach stderr. Die Zeilen werden
/// **nebeneinander** bearbeitet: Ein `tools/call`, der bis zu 45 s auf die Karte wartet, haelt
/// ein `ping` nicht auf (die Antworten tragen ihre `id`, die Reihenfolge zaehlt nicht).
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
enum Claudestdio {
    static let schalter = "--mcp-stdio"

    /// Im Einstieg der App, **vor allem anderen**: Steht der Schalter da, laeuft der Weg und
    /// die App endet danach — bevor ein Fenster entsteht und bevor `Einzelstart` eine laufende
    /// Visbox nach vorn holt.
    static func pruefe(_ argumente: [String] = CommandLine.arguments) {
        guard argumente.dropFirst().contains(schalter) else { return }
        exit(fuehreAus())
    }

    private static let ausgabe = NSLock()

    static func fuehreAus() -> Int32 {
        let fassung = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString")
            as? String ?? "0.0.0"
        let ersatz = Mcpkern(traeger: Mcpplatzhalter(ort: .ohneApp), fassung: fassung)
        let arbeit = DispatchQueue(label: "claude.mcp.stdio", attributes: .concurrent)
        let gruppe = DispatchGroup()
        var zeilen = Mcpzeilen()
        hinweis("\(Marke.name) spricht MCP über stdio; die Zeilen gehen an 127.0.0.1:\(Mcp.anschluss).")
        while true {
            // `availableData` WARTET, bis etwas da ist; leer heisst: stdin ist zu.
            let stueck = FileHandle.standardInput.availableData
            if stueck.isEmpty { break }
            for zeile in zeilen.nimm(stueck) {
                arbeit.async(group: gruppe) {
                    for aus in bearbeite(zeile, ersatz: ersatz) { schreibe(aus) }
                }
            }
        }
        if zeilen.verworfen > 0 {
            hinweis("\(zeilen.verworfen) zu lange Zeile(n) verworfen.")
        }
        gruppe.wait()
        return 0
    }

    /// Eine Zeile: weiterreichen — oder, ohne laufende App, der eigene Kern.
    static func bearbeite(_ zeile: String, ersatz: Mcpkern) -> [String] {
        switch sende(Mcpweiterleitung.anfrage(zeile)) {
        case .antwort(let daten):
            return Mcpweiterleitung.zeilen(ausAntwort: daten, nachricht: zeile)
        case .abgerissen:
            return Mcpweiterleitung.fehlerzeilen(
                zeile, "Die Verbindung zu \(Marke.name) ist abgebrochen; ob etwas angewendet wurde, "
                    + "zeigt \(Mcpkern.statusName).")
        case .keineApp:
            guard let nachricht = try? JSONWert.lies(Data(zeile.utf8)) else {
                return Mcpweiterleitung.fehlerzeilen(zeile, "")
            }
            let antwort = warte { await ersatz.verarbeite(nachricht) }
            return antwort.flatMap(Mcpweiterleitung.zeile).map { [$0] } ?? []
        }
    }

    // ---------------------------------------------------------- Handgriffe

    enum Gesendet: Sendable {
        case antwort(Data)
        case keineApp
        case abgerissen
    }

    /// Schickt die Bytes an die App und liest bis zum Ende (die App schliesst nach der Antwort).
    /// Warten, bis es fertig ist — dieser Weg hat keinen Hauptfaden, der etwas anderes taete.
    static func sende(_ anfrage: Data) -> Gesendet {
        guard let anschluss = NWEndpoint.Port(rawValue: UInt16(Mcp.anschluss)) else { return .keineApp }
        let verbindung = NWConnection(host: .ipv4(.loopback), port: anschluss, using: .tcp)
        let schlange = DispatchQueue(label: "claude.mcp.stdio.leitung")
        let fertig = DispatchSemaphore(value: 0)
        let stand = Sendestand()

        @Sendable func lies() {
            verbindung.receive(minimumIncompleteLength: 1, maximumLength: 64 * 1024) {
                daten, _, ende, fehler in
                if let daten { stand.gelesen.append(daten) }
                if ende || fehler != nil {
                    // DIE APP SCHLIESST NACH DER ANTWORT: Was bis dahin kam, ist die Antwort.
                    stand.schliesse(fehler == nil || !stand.gelesen.isEmpty
                                    ? .antwort(stand.gelesen) : .abgerissen, fertig)
                } else {
                    lies()
                }
            }
        }

        verbindung.stateUpdateHandler = { zustand in
            switch zustand {
            case .ready where !stand.bereit:
                stand.bereit = true
                verbindung.send(content: anfrage, completion: .contentProcessed { fehler in
                    if fehler != nil { stand.schliesse(.abgerissen, fertig) }
                })
                lies()
            case .waiting, .failed:
                // ABGEWIESEN, BEVOR DIE VERBINDUNG STAND: Es laeuft keine Visbox (oder ihr
                // Anschluss ist aus). `NWConnection` wartet sonst still auf einen neuen Versuch.
                stand.schliesse(stand.bereit ? .abgerissen : .keineApp, fertig)
            default:
                break
            }
        }
        verbindung.start(queue: schlange)
        let zeit = fertig.wait(timeout: .now() + Mcpweiterleitung.frist)
        verbindung.cancel()
        return schlange.sync {
            if zeit == .timedOut, stand.ergebnis == nil { return stand.bereit ? .abgerissen : .keineApp }
            return stand.ergebnis ?? .abgerissen
        }
    }

    /// Fuehrt Asynchrones aus und wartet darauf — fuer den Ersatz-Kern, der ein `actor` ist.
    static func warte<T: Sendable>(_ arbeit: @escaping @Sendable () async -> T) -> T {
        let fertig = DispatchSemaphore(value: 0)
        let kiste = Kiste<T>()
        Task.detached {
            kiste.wert = await arbeit()
            fertig.signal()
        }
        fertig.wait()
        return kiste.wert!
    }

    static func schreibe(_ zeile: String) {
        ausgabe.lock()
        FileHandle.standardOutput.write(Data((zeile + "\n").utf8))
        ausgabe.unlock()
    }

    static func hinweis(_ satz: String) {
        FileHandle.standardError.write(Data("[\(Mcp.servername)-mcp] \(satz)\n".utf8))
    }
}

/// Der Stand einer Sendung — nur auf der Schlange der Verbindung angefasst.
private final class Sendestand: @unchecked Sendable {
    var bereit = false
    var gelesen = Data()
    var ergebnis: Claudestdio.Gesendet?

    /// Setzt das Ergebnis **einmal** und weckt den Wartenden; spaetere Rufe aendern nichts.
    func schliesse(_ e: Claudestdio.Gesendet, _ fertig: DispatchSemaphore) {
        guard ergebnis == nil else { return }
        ergebnis = e
        fertig.signal()
    }
}

private final class Kiste<T>: @unchecked Sendable {
    var wert: T?
}
