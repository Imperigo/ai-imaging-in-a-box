import Foundation

/// Die Adresse des Heim-PC, wie die Mac-App sie beim Einrichten nimmt — **geprüft, bevor
/// sie gemerkt wird.**
///
/// Der Weg nach Hause ist Tailscale Serve auf einem **eigenen Anschluss** (8443), nicht ein
/// Unterpfad: Die Seite des Servers ruft feste Pfade (`/api/…`), die unter einem Unterpfad
/// bei KosmoOrbit landeten (Befund `auf-20261001-213`, `docs/VORFUEHRFASSUNG_2026-10-01.md`).
/// Darum die drei Regeln: **https**, **ein Anschluss** (ohne Angabe 8443), **kein Pfad**.
///
/// Und eine vierte, die nichts mit der Form zu tun hat: **kein Benutzer und kein Kennwort in
/// der Adresse.** Die Adresse landet in den Einstellungen des Mac (eine Datei), das
/// Kennwort gehört in den Schlüsselbund. Eine Adresse wie `https://name:geheim@…` legte es
/// still in die Datei.
public enum Heimadresse {
    /// Der Anschluss, auf dem Tailscale Serve am Heim-PC zu Visbox weiterleitet.
    public static let vorgabeAnschluss = 8443

    /// Wie eine Adresse aussieht — mit Platzhaltern, nie mit einem echten Namen (Regel 3).
    public static let beispiel = "https://<rechner>.<netz>.ts.net:8443"

    /// Der Benutzer, der im Feld vorgeschlagen wird. **Ein Vorschlag, kein fester Wert**
    /// (Protokoll §2): Der Server nennt ihn heute `BENUTZER` und leitet ihn aus dem Namen
    /// ab; `tests/test_ipad_geruest.py` hält beide Seiten gegeneinander.
    public static var vorgabeBenutzer: String { Marke.name.lowercased() }

    public enum Pruefung: Equatable, Sendable {
        /// Die Adresse in der Form, die gemerkt wird (`https://name:anschluss`), und ein Satz,
        /// wenn etwas ergänzt wurde.
        case gut(URL, hinweis: String?)
        case schlecht(String)
    }

    public static func pruefe(_ eingabe: String) -> Pruefung {
        let text = eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else {
            return .schlecht("Die Adresse fehlt — sie sieht so aus: \(beispiel)")
        }
        guard text.rangeOfCharacter(from: .whitespacesAndNewlines) == nil else {
            return .schlecht("In der Adresse steht ein Leerzeichen.")
        }
        guard !text.contains("<"), !text.contains(">") else {
            return .schlecht("Die Platzhalter <rechner> und <netz> durch die eigenen Namen "
                             + "ersetzen — sie stehen in der Tailscale-App am Heim-PC.")
        }
        // OHNE «://» IST HTTPS GEMEINT. Sonst laese `URLComponents` «name:8443» als Schema
        // «name» mit dem Pfad «8443».
        let mitSchema = text.contains("://") ? text : "https://" + text
        guard let teile = URLComponents(string: mitSchema) else {
            return .schlecht("Das ist keine Adresse — sie sieht so aus: \(beispiel)")
        }
        guard let schema = teile.scheme?.lowercased(), schema == "https" else {
            return .schlecht("Nur https: Die Leitung geht verschlüsselt über Tailscale Serve, "
                             + "und das spricht https. Die Adresse beginnt mit https://")
        }
        guard teile.user == nil, teile.password == nil else {
            return .schlecht("Benutzer und Kennwort gehören nicht in die Adresse, sondern in "
                             + "die Felder darunter — sonst lägen sie in den Einstellungen des "
                             + "Mac, statt im Schlüsselbund.")
        }
        guard let name = teile.host?.lowercased(), !name.isEmpty else {
            return .schlecht("Der Name des Heim-PC fehlt — sie sieht so aus: \(beispiel)")
        }
        guard teile.path.isEmpty || teile.path == "/" else {
            return .schlecht("Ohne Pfad: Die Adresse endet nach dem Anschluss (\(teile.path) "
                             + "weglassen). \(Marke.name) liegt am Heim-PC auf einem eigenen "
                             + "Anschluss, nicht unter einem Unterpfad.")
        }
        guard teile.query == nil, teile.fragment == nil else {
            return .schlecht("Ohne «?» und «#»: Die Adresse endet nach dem Anschluss.")
        }
        var hinweis: String?
        let anschluss: Int
        if let p = teile.port {
            guard (1...65535).contains(p) else {
                return .schlecht("Den Anschluss \(p) gibt es nicht (1 bis 65535).")
            }
            anschluss = p
        } else {
            anschluss = vorgabeAnschluss
            hinweis = "Ohne Anschluss angegeben — \(vorgabeAnschluss) genommen, der Anschluss "
                + "von \(Marke.name) am Heim-PC."
        }
        var sauber = URLComponents()
        sauber.scheme = "https"
        sauber.host = name
        sauber.port = anschluss
        guard let url = sauber.url else {
            return .schlecht("Aus dem Namen «\(name)» liess sich keine Adresse bauen.")
        }
        return .gut(url, hinweis: hinweis)
    }
}
