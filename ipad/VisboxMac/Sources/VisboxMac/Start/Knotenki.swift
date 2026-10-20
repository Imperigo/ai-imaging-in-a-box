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

/// Die zweite Brücke der Knotenansicht, **«visboxWirt»** (Plan UI-Gleichheit S1/S2, Entscheide
/// 115/116, 20.10.2026): Die Kopfteile der Seite (Palette am Logo, Einstellungs-Kreis,
/// Heim-PC-Chip, die Selbständigkeit an der Claude-Marke) melden ihre Wünsche, und die App legt
/// ihre Lage in die Seite (`window.visboxWirt.lage({...})`). Was ein Wunsch heisst und was die
/// Lage traegt, steht im Kern (`Knotenwirt`, mit Proben).
///
/// **Dieselbe Wache wie `Knotenki`:** Nur der Hauptrahmen vom eigenen Adressschema spricht; die
/// Visbox-Seite des Heim-PC in derselben Flaeche wuenscht nichts. Die Lage traegt kein Kennwort —
/// sie hat kein Feld dafuer.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
final class Knotenwirtbote: NSObject, WKScriptMessageHandler {
    static let name = Knotenwirt.name

    /// Was die App auf einen Wunsch tut — gesetzt von der `Heimflaeche` (aus der `Arbeitsansicht`).
    var wuensche: (Knotenwirt.Wunsch) -> Void = { _ in }
    /// Die zuletzt gesetzte Lage; nach «bereit» und bei jeder Aenderung in die Seite gelegt.
    private(set) var lage: Knotenwirt.Lage?
    /// Die Ansicht, die «bereit» gemeldet hat — schwach, die Flaeche haelt sie.
    private weak var ansicht: WKWebView?

    static func haengeAn(_ einstellung: WKWebViewConfiguration, bote: Knotenwirtbote) {
        einstellung.userContentController.add(Schwacherbote(bote), name: name)
    }

    func userContentController(_ steuerung: WKUserContentController,
                               didReceive nachricht: WKScriptMessage) {
        guard nachricht.frameInfo.isMainFrame,
              let adresse = nachricht.frameInfo.request.url, Knotenwege.istEigen(adresse),
              JSONSerialization.isValidJSONObject(nachricht.body),
              let daten = try? JSONSerialization.data(withJSONObject: nachricht.body),
              let wert = try? JSONWert.lies(daten),
              let wunsch = Knotenwirt.wunsch(aus: wert) else { return }
        let quelle = nachricht.webView
        MainActor.assumeIsolated {
            if wunsch == .bereit {
                ansicht = quelle
                lege()
            } else {
                wuensche(wunsch)
            }
        }
    }

    /// Eine neue Lage — nur, wenn sie sich geaendert hat.
    @MainActor
    func setze(_ neu: Knotenwirt.Lage) {
        guard neu != lage else { return }
        lage = neu
        lege()
    }

    /// Die Seite geht (neu laden, umschalten): bis zum naechsten «bereit» wird nichts gelegt.
    @MainActor
    func seiteGeht() {
        ansicht = nil
    }

    @MainActor
    private func lege() {
        guard let ansicht, let lage, let rumpf = Knotenwirt.rumpf(lage) else { return }
        ansicht.evaluateJavaScript(rumpf, completionHandler: nil)
    }

    /// Das Thema vor dem ersten Bild: ein Skript am Anfang des Dokuments, das die gemerkte Wahl
    /// dorthin legt, wo die Seite sie liest (`kosmo.thema`, wie KosmoOrbit). Das Webfenster hat
    /// keinen bleibenden Speicher; die App merkt die Wahl (`Knotenwirt.Thema.einstellung`).
    static func themaSkript(_ thema: Knotenwirt.Thema) -> WKUserScript {
        WKUserScript(source: "try { localStorage.setItem('kosmo.thema', '\(thema.rawValue)'); } catch (e) {}",
                     injectionTime: .atDocumentStart, forMainFrameOnly: true)
    }
}

/// Haelt einen Boten nur schwach — sonst hielte die Konfiguration die Flaeche fuer immer.
private final class Schwacherbote: NSObject, WKScriptMessageHandler {
    weak var bote: (NSObject & WKScriptMessageHandler)?

    init(_ bote: NSObject & WKScriptMessageHandler) {
        self.bote = bote
    }

    func userContentController(_ steuerung: WKUserContentController,
                               didReceive nachricht: WKScriptMessage) {
        bote?.userContentController(steuerung, didReceive: nachricht)
    }
}
