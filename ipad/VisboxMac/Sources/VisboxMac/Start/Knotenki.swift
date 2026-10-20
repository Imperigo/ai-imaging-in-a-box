import Foundation
import VisboxKern
import WebKit

/// Der Bote der Knotenansicht an die App (Plan KI-Bedienung, Stufe 3): ein
/// `WKScriptMessageHandler` namens **«visboxKi»** an der Heimflaeche.
///
/// Die Seite (`apps/visbox-knoten/src/ki-wirt.ts`) schickt jedes Ereignis des KI-Werkzeugsatzes
/// mit `webkit.messageHandlers.visboxKi.postMessage(…)`: Taetigkeit, Karte, entschieden,
/// kiverlauf — und zuerst «bereit». Auf «bereit» meldet dieser Bote der `Kizentrale` den Weg
/// zurueck in die Seite: `callAsyncJavaScript` an `window.visboxKi` (die Antwort als JSON-Text).
///
/// **Nur die eigene Seite spricht hier:** Eine Nachricht zaehlt nur aus dem Hauptrahmen und vom
/// eigenen Adressschema (`visbox://app/knoten/`, `Knotenwege.istEigen`). Die Visbox-Seite des
/// Heim-PC laeuft in derselben Flaeche — sie kann keine Karte legen und nichts anwenden.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
final class Knotenki: NSObject, WKScriptMessageHandler {
    static let name = Kibruecke.name

    /// Meldet den Boten an der Konfiguration an — ueber einen schwachen Vermittler, denn
    /// `WKUserContentController` haelt seinen Boten fest, und der Bote haelt die Ansicht.
    static func haengeAn(_ einstellung: WKWebViewConfiguration, bote: Knotenki) {
        einstellung.userContentController.add(Schwacherbote(bote), name: name)
    }

    func userContentController(_ steuerung: WKUserContentController,
                               didReceive nachricht: WKScriptMessage) {
        guard nachricht.frameInfo.isMainFrame,
              let adresse = nachricht.frameInfo.request.url, Knotenwege.istEigen(adresse),
              JSONSerialization.isValidJSONObject(nachricht.body),
              let daten = try? JSONSerialization.data(withJSONObject: nachricht.body) else { return }
        let ansicht = nachricht.webView
        let istBereit = (nachricht.body as? [String: Any])?["art"] as? String == "bereit"
        MainActor.assumeIsolated {
            let zentrale = Kizentrale.gemeinsam
            if istBereit, let ansicht {
                zentrale.knotenAngemeldet { [weak ansicht] rumpf, argumente in
                    guard let ansicht else { return nil }
                    return await Knotenki.rufe(ansicht, rumpf, argumente)
                }
            }
            zentrale.empfange(daten)
        }
    }

    /// Ein Aufruf in die Seite. Die Antwort ist der Text von `visboxKi.alsText(…)`; ein Fehler in
    /// der Seite (oder keine Schnittstelle) gibt `nil`.
    @MainActor
    static func rufe(_ ansicht: WKWebView, _ rumpf: String, _ argumente: [String: Any]) async -> String? {
        do {
            let wert = try await ansicht.callAsyncJavaScript(rumpf, arguments: argumente,
                                                             in: nil, contentWorld: .page)
            return wert as? String
        } catch {
            return nil
        }
    }

    /// Die Seite geht (neu laden, umschalten, Fenster zu).
    static func seiteGeht(_ grund: String) {
        MainActor.assumeIsolated { Kizentrale.gemeinsam.knotenWeg(grund) }
    }
}

/// Haelt den Boten nur schwach — sonst hielte die Konfiguration die Flaeche fuer immer.
private final class Schwacherbote: NSObject, WKScriptMessageHandler {
    weak var bote: Knotenki?

    init(_ bote: Knotenki) {
        self.bote = bote
    }

    func userContentController(_ steuerung: WKUserContentController,
                               didReceive nachricht: WKScriptMessage) {
        bote?.userContentController(steuerung, didReceive: nachricht)
    }
}
