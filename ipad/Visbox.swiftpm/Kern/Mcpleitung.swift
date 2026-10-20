import Foundation

// DIE LEITUNG DES MCP-KERNS — wer an den Anschluss darf, wie eine HTTP-Anfrage zur
// JSON-RPC-Nachricht wird, und wie der Weg ueber stdio sie weiterreicht.
//
// Die Bytes liest der bestehende `Anfrageleser` (`Leitung.swift`) — derselbe, der fuer das
// iPad liest, mit denselben Grenzen (Kopf 32 KiB, Rumpf 4 MiB, kein Stueckeln). Hier steht nur,
// was MCP dazu braucht. Der Mac-Teil (`VisboxMac/Claude/`) nimmt die Verbindungen an und
// schreibt zurueck, sonst nichts.
//
// MCP «STREAMABLE HTTP», SO KLEIN WIE ES GEHT (wie KosmoOrbit `kosmo-mcp-kern/src/http.rs`):
//
//  * `POST /mcp` — eine Nachricht oder ein Buendel; Antwort als `application/json`, bei reinen
//    Meldungen `202` ohne Rumpf. Kein Ereignisstrom in der Antwort: Die Norm erlaubt JSON.
//  * `GET /mcp` — `405`. KosmoOrbit haelt dort einen Ereignisstrom offen, weil seine Liste
//    wechselt, sobald die Oberflaeche kommt oder geht («Liste geaendert»). Die Liste der Mac-App
//    steht fest, der Kern meldet `listChanged: false` — und die Norm sagt fuer diesen Fall
//    ausdruecklich: 405.
//  * `DELETE /mcp` — `405`: Es gibt keine Sitzungen; jede Anfrage steht fuer sich.
//  * `OPTIONS` — die Vorabfrage eines Browsers, nur fuer einen erlaubten Ursprung.
//
// NUR DIESER RECHNER (Entscheide 106 und 106e): Der Hoerer bindet `127.0.0.1`. Dazu prueft
// jede Anfrage `Host` und `Origin` — gegen das Umbiegen eines Namens (DNS-Rebinding): Eine
// fremde Webseite koennte sonst ihren Namen auf 127.0.0.1 zeigen lassen und im Browser des
// Architekten mitlesen. Und was Spuren eines Vermittlers traegt (`Forwarded`, `Cf-…`), kam
// nicht von diesem Rechner und bleibt draussen.

// ===================================================================== Zugang

public enum Mcpzugang {
    /// `Host` muss `127.0.0.1:<anschluss>` oder `localhost:<anschluss>` sein — ohne `Host`
    /// keine Antwort.
    public static func hostErlaubt(_ host: String?, anschluss: Int = Mcp.anschluss) -> Bool {
        guard let host else { return false }
        let h = host.lowercased()
        return h == "127.0.0.1:\(anschluss)" || h == "localhost:\(anschluss)"
    }

    /// Ein mitgeschicktes `Origin` muss lokal sein (`http://localhost[:n]`,
    /// `http://127.0.0.1[:n]`). **Fehlt es, ist das kein Browser** (Claude Code, curl) — erlaubt.
    /// `null` (eine Datei, ein Sandbox-Rahmen) ist ein Browser ohne Herkunft — abgewiesen.
    public static func ursprungErlaubt(_ origin: String?) -> Bool {
        guard let origin, !origin.isEmpty else { return true }
        for vorn in ["http://localhost", "http://127.0.0.1"] where origin.hasPrefix(vorn) {
            let rest = origin.dropFirst(vorn.count)
            if rest.isEmpty { return true }
            guard rest.first == ":" else { return false }
            let zahl = rest.dropFirst()
            return !zahl.isEmpty && zahl.count <= 5
                && zahl.unicodeScalars.allSatisfy { ("0"..."9").contains($0) }
        }
        return false
    }

    /// Ob die Anfrage durch einen Vermittler kam (Tunnel, Umleitung). Vorerst nur lokal (106e).
    public static func kamUeberVermittler(_ koepfe: [Kopfzeile]) -> Bool {
        koepfe.contains {
            let n = $0.name.lowercased()
            return n == "forwarded" || n == "x-forwarded-for" || n == "x-forwarded-host"
                || n == "x-real-ip" || n.hasPrefix("cf-")
        }
    }

    /// Ob die Gegenstelle einer Verbindung dieser Rechner ist — die zweite Wand hinter dem
    /// Binden an 127.0.0.1 (der Mac prueft jede Verbindung, bevor er liest).
    public static func gegenstelleIstLokal(_ adresse: String) -> Bool {
        var a = adresse.lowercased()
        if let prozent = a.firstIndex(of: "%") { a = String(a[..<prozent]) }
        if a.hasPrefix("::ffff:") { a = String(a.dropFirst(7)) }
        if a == "::1" || a == "localhost" { return true }
        let teile = a.split(separator: ".", omittingEmptySubsequences: false)
        return teile.count == 4 && teile[0] == "127"
            && teile.allSatisfy { t in Int(t).map { (0...255).contains($0) } ?? false }
    }
}

// ===================================================================== HTTP

public enum Mcpleitung {

    /// Die Antwort auf eine ganz gelesene Anfrage. Ein `tools/call` kann bis zur Wartefrist
    /// dauern (45 s); der Mac haelt die Verbindung so lange offen.
    public static func antworte(auf anfrage: RoheAnfrage, kern: Mcpkern,
                                anschluss: Int = Mcp.anschluss) async -> Leitungsantwort {
        let kopf = anfrage.kopf
        let origin = kopf.koepfe.wert("Origin")
        guard kopf.koepfe.werte("Host").count == 1,
              Mcpzugang.hostErlaubt(kopf.koepfe.wert("Host"), anschluss: anschluss),
              kopf.koepfe.werte("Origin").count <= 1,
              Mcpzugang.ursprungErlaubt(origin),
              !Mcpzugang.kamUeberVermittler(kopf.koepfe) else {
            return verweigert
        }
        var koepfe: [Kopfzeile] = []
        if let origin, !origin.isEmpty {
            koepfe.append(Kopfzeile("Access-Control-Allow-Origin", origin))
            koepfe.append(Kopfzeile("Vary", "Origin"))
            koepfe.append(Kopfzeile("Access-Control-Allow-Headers",
                                    "content-type, accept, mcp-protocol-version, mcp-session-id"))
        }
        koepfe.append(Kopfzeile("Cache-Control", "no-store"))
        if kopf.methode == "OPTIONS" {
            koepfe.append(Kopfzeile("Access-Control-Allow-Methods", "POST, OPTIONS"))
            return Leitungsantwort(status: 204, koepfe: koepfe)
        }
        guard kopf.pfad == Mcp.pfad else { return Leitungsantwort(status: 404, koepfe: koepfe) }
        if let stand = kopf.koepfe.wert("MCP-Protocol-Version"), !Mcp.protokolle.contains(stand) {
            return .json(Mcpkern.fehler(id: .null, -32600, "MCP-Fassung «\(stand)» wird nicht "
                                        + "gesprochen (\(Mcp.protokolle.joined(separator: ", ")))."),
                         status: 400, koepfe: koepfe)
        }
        guard kopf.methode == "POST" else {
            return Leitungsantwort(status: 405, koepfe: koepfe + [Kopfzeile("Allow", "POST, OPTIONS")])
        }
        guard let nachricht = try? JSONWert.lies(anfrage.rumpf) else {
            return .json(Mcpkern.fehler(id: .null, -32700, "Kein gültiges JSON."), status: 400,
                         koepfe: koepfe)
        }
        guard let antwort = await kern.verarbeite(nachricht) else {
            return Leitungsantwort(status: 202, koepfe: koepfe)
        }
        return .json(antwort, koepfe: koepfe)
    }

    /// Die Abweisung — **ohne Grund nach aussen.** Wer nicht hinein darf, erfaehrt nicht, woran
    /// es lag.
    public static let verweigert = Leitungsantwort(
        status: 403, koepfe: [Kopfzeile("Content-Type", "text/plain; charset=utf-8")],
        rumpf: Data("verweigert".utf8))
}

// ===================================================================== der Weg ueber stdio

/// Zerlegt, was ueber stdin kommt, in Zeilen — eine JSON-RPC-Nachricht je Zeile (MCP stdio).
///
/// Die Stuecke kommen, wie das Betriebssystem sie liefert; eine Zeile kann ueber mehrere gehen.
/// Leere Zeilen fallen weg, ein `\r` am Ende auch. **Eine Zeile ueber der Grenze** wird ganz
/// verworfen (bis zum naechsten Zeilenende), statt den Speicher zu fuellen.
public struct Mcpzeilen: Sendable {
    public static let grenze = Anfrageleser.rumpfGrenze

    private var puffer = Data()
    private var verwerfen = false
    /// Wie viele Zeilen wegen der Grenze verworfen wurden.
    public private(set) var verworfen = 0

    public init() {}

    public mutating func nimm(_ stueck: Data) -> [String] {
        var zeilen: [String] = []
        for byte in stueck {
            if byte == 10 {
                if verwerfen {
                    verwerfen = false
                } else {
                    if puffer.last == 13 { puffer.removeLast() }
                    if !puffer.isEmpty, let z = String(data: puffer, encoding: .utf8) {
                        zeilen.append(z)
                    }
                }
                puffer.removeAll(keepingCapacity: true)
                continue
            }
            if verwerfen { continue }
            puffer.append(byte)
            if puffer.count > Mcpzeilen.grenze {
                puffer.removeAll()
                verwerfen = true
                verworfen += 1
            }
        }
        return zeilen
    }
}

/// `Visbox --mcp-stdio` (Claude Desktop): jede Zeile per `POST /mcp` an die laufende App,
/// die Antwort als eine Zeile zurueck — wie `kosmo-orbit --mcp-stdio` (`stdio.rs`).
public enum Mcpweiterleitung {
    /// So lange wartet der Weg auf eine Antwort der App: die Wartefrist und Luft.
    public static let frist: TimeInterval = Mcp.wartefrist + 75

    /// Die Bytes der Anfrage an die App. `Connection: close`: eine Anfrage je Verbindung.
    public static func anfrage(_ zeile: String, anschluss: Int = Mcp.anschluss) -> Data {
        let rumpf = Data(zeile.utf8)
        var kopf = "POST \(Mcp.pfad) HTTP/1.1\r\n"
        kopf += "Host: 127.0.0.1:\(anschluss)\r\n"
        kopf += "Content-Type: application/json\r\n"
        kopf += "Accept: application/json, text/event-stream\r\n"
        kopf += "Content-Length: \(rumpf.count)\r\n"
        kopf += "Connection: close\r\n\r\n"
        return Data(kopf.utf8) + rumpf
    }

    /// Was die App zurueckgab, als Zeilen fuer stdout. `nachricht` ist die Zeile, die
    /// hinausging — fuer die Fehlerantwort, wenn die App etwas anderes als JSON-RPC sagt.
    public static func zeilen(ausAntwort antwort: Data, nachricht: String) -> [String] {
        guard let (status, rumpf) = lies(antwort) else {
            return fehlerzeilen(nachricht, "Die Antwort von \(Marke.name) war nicht lesbar.")
        }
        if status == 202 { return [] }
        if let wert = try? JSONWert.lies(rumpf), wert.alsObjekt != nil || wert.alsListe != nil,
           let z = zeile(wert) {
            return [z]
        }
        if status == 200 && rumpf.isEmpty { return [] }
        return fehlerzeilen(nachricht, "\(Marke.name) hat die Anfrage abgewiesen (HTTP \(status)).")
    }

    /// Die Antwort an Claude, wenn eine Nachricht nicht ankam oder die Verbindung abriss — nur
    /// fuer Anfragen mit `id`; eine Meldung bekommt nie eine Antwort.
    public static func fehlerzeilen(_ nachricht: String, _ satz: String) -> [String] {
        guard let wert = try? JSONWert.lies(Data(nachricht.utf8)) else {
            return [zeile(Mcpkern.fehler(id: .null, -32700, "Kein gültiges JSON.")) ?? ""]
        }
        let ids = (wert.alsListe ?? [wert]).compactMap { n -> JSONWert? in
            guard let id = n["id"], !id.istNull else { return nil }
            return id
        }
        let antworten = ids.map { Mcpkern.fehler(id: $0, -32603, satz) }
        guard !antworten.isEmpty else { return [] }
        let gesamt: JSONWert = wert.alsListe != nil ? .liste(antworten) : antworten[0]
        return zeile(gesamt).map { [$0] } ?? []
    }

    /// Eine Nachricht als **eine** Zeile (JSON ohne Zeilenumbruch, `\n` steht nur escaped).
    public static func zeile(_ wert: JSONWert) -> String? {
        guard let d = try? wert.daten(), let z = String(data: d, encoding: .utf8) else { return nil }
        return z
    }

    /// Liest eine HTTP-Antwort: Status und Rumpf (nach `Content-Length`, sonst bis zum Ende).
    public static func lies(_ daten: Data) -> (status: Int, rumpf: Data)? {
        guard let grenze = Anfrageleser.kopfende(daten),
              let kopf = String(data: daten.prefix(grenze.kopfLaenge), encoding: .isoLatin1) else {
            return nil
        }
        let zeilen = kopf.components(separatedBy: "\r\n")
        let erste = zeilen[0].split(separator: " ", maxSplits: 2)
        guard erste.count >= 2, erste[0].hasPrefix("HTTP/1."), let status = Int(erste[1]) else {
            return nil
        }
        var rumpf = Data(daten.dropFirst(grenze.rumpfAnfang))
        let laenge = zeilen.dropFirst().compactMap { z -> Int? in
            guard let d = z.firstIndex(of: ":"),
                  z[..<d].lowercased() == "content-length" else { return nil }
            return Int(z[z.index(after: d)...].trimmingCharacters(in: .whitespaces))
        }.first
        if let laenge {
            guard rumpf.count >= laenge else { return nil }
            rumpf = Data(rumpf.prefix(laenge))
        }
        return (status, rumpf)
    }
}
