import AppKit
import SwiftUI
import VisboxKern
import WebKit

/// Die Arbeit nach «Schon anfangen» (Entscheid 39) — **zuerst die Knoten** (seit 20.10.2026 aus dem Bündel)
/// (Entscheid 85, 14.10.2026, Blatt 19), umschaltbar auf die Visbox-Seite, daneben der Platz
/// für den Assistenten.
///
/// **Seit Entscheid 85:** Oben steht der Schalter «Knoten | Visbox-Seite» (A); beim Öffnen
/// immer die Knoten (C, `Flaechenwahl.beimOeffnen`). Welche Mappe die Knoten zeigen, sagt der
/// Heim-PC (B): die zuletzt auf der Visbox-Seite geöffnete.
///
/// **Seit «Visbox eigenständig», Schritt 1 (20.10.2026)** kommen die Knoten aus dem App-Bündel
/// (`visbox://app/knoten/`, `Knotenquelle`) — auch ohne Heim-PC. Ihre Datenwege und die Brücke
/// reicht die App an den Heim-PC weiter. Nur die Visbox-Seite (`oberflaeche/seite.html`) kommt
/// vorerst noch vom Heim-PC; sie kommt nicht ins Bündel (Entscheid 103c). Angemeldet wird dort
/// über die Basic-Herausforderung des Servers, mit Benutzer und Kennwort aus dem Schlüsselbund —
/// und **nur gegenüber dem eingerichteten Heim-PC** (Name und Anschluss müssen stimmen).
///
/// Der Assistent kommt rechts dazu, sobald er geladen ist; bis seine Seitenleiste verdrahtet
/// ist, steht dort sein Zustand aus den Startzeilen.
///
/// **Seit Schritt 2 (Entscheid 103b, 20.10.2026)** ist diese Ansicht auch ohne Rechner da: Wo
/// bis 0.3.0 der Vorführmodus das Fenster ersetzte, steht jetzt oben das Band (im
/// `Hauptfenster`), und die Assistent-Leiste ist gesperrt mit dem Satz aus `sperre`.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Arbeitsansicht: View {
    @ObservedObject var leitung: Heimleitung
    let zurueck: () -> Void
    /// Was ohne Rechner gesperrt ist (`Leitungsschalter.sperre`) — hier: der Assistent.
    var sperre: Rechnersperre = .offen

    @State private var flaechenSatz: String?
    @State private var wahl: Flaechenwahl = Flaechenwahl.beimOeffnen

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 16) {
                // DIE NUMMER GANZ KLEIN NEBEN DEM NAMEN (Owner, 14.10.2026): Welche Fassung laeuft,
                // steht so ohne Menue da — auch nach einem Neustart aus dem Aktualisieren.
                HStack(alignment: .firstTextBaseline, spacing: 6) {
                    Text(Marke.name)
                        .font(Macschriften.schrift(.titel, 25))
                    Text(Aktualisierung.kleineNummer(Aktualisierung.laufendeNummer(Bundle.main.infoDictionary)))
                        .font(Macschriften.schrift(.text, 10))
                        .foregroundStyle(Startfarbe.leise)
                }
                Rectangle().fill(Startfarbe.linie).frame(width: 1, height: 24)
                Text(leitung.bild.kopfzeile)
                    .font(Macschriften.schrift(.text, 14))
                    .foregroundStyle(Startfarbe.leise)
                Spacer()
                // ENTSCHEID 94 (14.10.2026): Die Knoten sind DIE Arbeitsflaeche zum Rendern. Kein
                // Schalter mehr in der Leiste — die Seite oeffnet das Menue «Darstellung»
                // (`VisboxMacApp`), und von dort fuehrt dieser eine Knopf zurueck.
                if wahl == .seite {
                    Button("Zurück zu den Knoten") { wahl = .knoten }
                        .buttonStyle(.plain)
                        .font(Macschriften.schrift(.text, 13))
                        .foregroundStyle(Startfarbe.leise)
                }
                Button("Startzeilen", action: zurueck)
                    .buttonStyle(.plain)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.leise)
            }
            .padding(.horizontal, 22)
            .frame(height: 52)
            .background(Startfarbe.flaeche)

            HStack(spacing: 0) {
                flaeche
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                Rectangle().fill(Startfarbe.linie).frame(width: 1)
                assistentenPlatz
                    .frame(width: 360)
                    .frame(maxHeight: .infinity)
            }
        }
        .background(Startfarbe.grund)
        .foregroundStyle(Startfarbe.text)
        // DIE SEITE NUR NOCH UEBER DAS MENUE (Entscheid 94): «Darstellung → Visbox-Seite».
        .onReceive(NotificationCenter.default.publisher(for: .seiteOeffnen)) { _ in
            wahl = .seite
        }
    }

    @ViewBuilder
    private var flaeche: some View {
        // DIE KNOTEN AUCH OHNE HEIM-PC (Schritt 1): Sie kommen aus dem Bündel; ihre Datenwege
        // antworten dann sofort mit einem Satz. Die Seite braucht den Heim-PC weiter.
        if wahl.ausDemBuendel || (leitung.adresse != nil && leitung.anmeldung != nil) {
            ZStack(alignment: .bottom) {
                Heimflaeche(basis: leitung.adresse, anmeldung: leitung.anmeldung, wahl: wahl,
                            meldung: $flaechenSatz)
                if let satz = flaechenSatz {
                    Text(satz)
                        .font(Macschriften.schrift(.text, 13))
                        .foregroundStyle(Startfarbe.rot)
                        .padding(12)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Startfarbe.rotGrund))
                        .padding(16)
                }
            }
        } else {
            Text("Erst einrichten: Adresse und Kennwort des Heim-PC.")
                .font(Macschriften.schrift(.text, 15))
                .foregroundStyle(Startfarbe.leise)
        }
    }

    // ================================================================= der Assistent
    //
    // DIE SEITENLEISTE (Strom D, Blatt 14), verdrahtet am 01.10.2026. Ohne eingerichteten
    // Heim-PC gibt es niemanden, den sie fragen könnte — dann bleibt der Platzhalter mit dem
    // Zustand der Startzeile stehen. Den Ordner wählt die Fläche, nicht die Leiste: `nil`
    // heisst «der Projektordner, mit dem der Server läuft» (Protokoll §3).
    @ViewBuilder
    private var assistentenPlatz: some View {
        if let basis = leitung.adresse {
            Assistentenleiste(anschluss: AssistentAnschluss(basis: basis,
                                                            anmeldung: leitung.anmeldung),
                              gesperrt: sperre.satz)
        } else {
            Assistentenplatzhalter(stand: leitung.bild.assistent)
        }
    }
}

/// Der Platz des Assistenten, solange seine Seitenleiste nicht verdrahtet ist: sein Zustand,
/// wie die Startzeile ihn kennt — **kein Bedienelement**, das so tut, als ginge es schon.
struct Assistentenplatzhalter: View {
    let stand: Zeilenstand

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { zeit in
            VStack(alignment: .leading, spacing: 12) {
                Text("Assistent")
                    .font(Macschriften.schrift(.titel, 24))
                HStack(spacing: 10) {
                    Zeilenzeichen(stand: stand)
                        .frame(width: 18, height: 18)
                    Text(stand.wort)
                        .font(Macschriften.schrift(.zahl, 12))
                        .foregroundStyle(Startfarbe.zeile(stand).satz)
                }
                Text(satz(zeit.date))
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 0)
            }
            .padding(24)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .background(Startfarbe.flaeche)
    }

    private func satz(_ jetzt: Date) -> String {
        if case .laedt(let seit, _) = stand {
            return stand.satz + " · " + Startzeilen.seitText(seit, jetzt: jetzt)
        }
        return stand.satz
    }
}

// ================================================================= die Webfläche

/// Die Knoten (aus dem Bündel) oder die Seite des Heim-PC in einer `WKWebView`.
///
/// **Nichts auf der Platte:** ein flüchtiger Datenspeicher (`nonPersistent`) — keine Kekse,
/// kein Zwischenspeicher, keine gemerkte Anmeldung über das Programmende hinaus. (Der
/// `localStorage` der Knoten — Adresse der Brücke, Kurztasten — lebt darum nur, solange das
/// Fenster offen ist; die Seite setzt ihn bei jedem Laden neu.)
struct Heimflaeche: NSViewRepresentable {
    let basis: URL?
    let anmeldung: Anmeldung?
    let wahl: Flaechenwahl
    @Binding var meldung: String?

    func makeCoordinator() -> Flaechenlotse {
        Flaechenlotse(basis: basis, anmeldung: anmeldung, wahl: wahl)
    }

    func makeNSView(context: Context) -> WKWebView {
        let einstellung = WKWebViewConfiguration()
        einstellung.websiteDataStore = .nonPersistent()
        // DAS EIGENE ADRESSSCHEMA (Schritt 1): Es muss VOR dem Bau der Ansicht stehen —
        // danach nimmt WebKit keinen Gastgeber mehr an. Die Konfiguration hält ihn fest.
        einstellung.setURLSchemeHandler(context.coordinator.quelle, forURLScheme: Knotenwege.schema)
        let ansicht = WKWebView(frame: .zero, configuration: einstellung)
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        ansicht.navigationDelegate = lotse
        // DER DATEIWAEHLER DER SEITE (Entscheid 90): Ohne `uiDelegate` tut ein
        // `<input type="file">` in einer WKWebView nichts — «Datei laden …» am Modell-Knoten
        // waere ein Knopf ohne Wirkung.
        ansicht.uiDelegate = lotse
        lotse.lade(ansicht)
        return ansicht
    }

    func updateNSView(_ ansicht: WKWebView, context: Context) {
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        // NEU EINGERICHTET (andere Adresse, anderes Kennwort): neu laden, sonst bliebe die
        // Seite mit der alten Anmeldung offen.
        // ODER UMGESCHALTET (Knoten ↔ Visbox-Seite): die andere Seite laden.
        if lotse.basis != basis || lotse.anmeldung != anmeldung || lotse.wahl != wahl {
            lotse.basis = basis
            lotse.anmeldung = anmeldung
            lotse.quelle.basis = basis
            lotse.quelle.anmeldung = anmeldung
            lotse.wahl = wahl
            lotse.lade(ansicht)
        }
    }
}

/// Führt die Webfläche: lädt die Seite, beantwortet die Anmeldung, meldet Fehler als Satz —
/// und öffnet den Dateiwähler, wenn die Seite danach fragt (Entscheid 90).
final class Flaechenlotse: NSObject, WKNavigationDelegate, WKUIDelegate {
    var basis: URL?
    var anmeldung: Anmeldung?
    var wahl: Flaechenwahl
    var melde: (String?) -> Void = { _ in }
    /// Der Gastgeber des eigenen Schemas: Bau aus dem Bündel, Datenwege an den Heim-PC.
    let quelle: Knotenquelle

    init(basis: URL?, anmeldung: Anmeldung?, wahl: Flaechenwahl) {
        self.basis = basis
        self.anmeldung = anmeldung
        self.wahl = wahl
        self.quelle = Knotenquelle(basis: basis, anmeldung: anmeldung)
    }

    func lade(_ ansicht: WKWebView) {
        if wahl.ausDemBuendel && !quelle.bauVorhanden {
            melde("Die Knotenansicht fehlt im Programm — bitte die Mac-App neu laden.")
            return
        }
        guard let ziel = wahl.adresse(basis: basis) else {
            melde("Aus der Adresse des Heim-PC liess sich die Seite nicht bauen.")
            return
        }
        melde(nil)
        ansicht.load(URLRequest(url: ziel))
    }

    /// Die Basic-Herausforderung des Servers (Protokoll §2) — beantwortet **nur für den
    /// eingerichteten Heim-PC**, und nur einmal: Weist er das Kennwort ab, wird nicht endlos
    /// dasselbe wieder geschickt.
    func webView(_ webView: WKWebView, didReceive challenge: URLAuthenticationChallenge,
                 completionHandler: @escaping (URLSession.AuthChallengeDisposition,
                                               URLCredential?) -> Void) {
        let raum = challenge.protectionSpace
        // DAS ZERTIFIKAT ZUERST (Entscheid 83b): im Heim-WLAN nur das angeheftete, ueber
        // Tailscale prueft das System — dieselbe Regel wie fuer jede Anfrage der App.
        if raum.authenticationMethod == NSURLAuthenticationMethodServerTrust {
            let (art, ausweis) = Heimvertrauen.entscheide(challenge)
            completionHandler(art, ausweis)
            return
        }
        guard raum.authenticationMethod == NSURLAuthenticationMethodHTTPBasic else {
            completionHandler(.performDefaultHandling, nil)
            return
        }
        guard let basis, let anmeldung,
              raum.host.lowercased() == basis.host?.lowercased(),
              raum.port == (basis.port ?? 443) else {
            // EIN FREMDER FRAGT NACH DEM KENNWORT: er bekommt es nicht.
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        guard challenge.previousFailureCount == 0 else {
            melde("Kennwort stimmt nicht — der Heim-PC weist die Anmeldung ab. Unter "
                  + "«Einrichten» neu eingeben.")
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        completionHandler(.useCredential,
                          URLCredential(user: anmeldung.benutzer, password: anmeldung.kennwort,
                                        persistence: .forSession))
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        melde(nil)
    }

    /// «Datei laden …» am Modell-Knoten (Owner-Entscheid 90, 14.10.2026, Blatt 21): Die Seite
    /// fragt mit einem `<input type="file">` nach einer Datei, und eine `WKWebView` zeigt dafür
    /// von sich aus **nichts** — der Gastgeber muss den Wähler selbst öffnen. Hier ist es der
    /// gewöhnliche Öffnen-Dialog des Mac (`NSOpenPanel`), als Blatt am Fenster.
    ///
    /// **Jede Datei ist wählbar**, auch eine ArchiCAD-Datei: Der Heim-PC sagt dann, wie man
    /// daraus eine IFC macht (Entscheid 90c). Ein Wähler, der sie ausgraut, liesse den Menschen
    /// ohne diesen Satz. Abbrechen gibt `nil` zurück — dann bleibt die Seite, wie sie war.
    func webView(_ webView: WKWebView, runOpenPanelWith parameters: WKOpenPanelParameters,
                 initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping ([URL]?) -> Void) {
        let tafel = NSOpenPanel()
        tafel.canChooseFiles = true
        tafel.canChooseDirectories = parameters.allowsDirectories
        tafel.allowsMultipleSelection = parameters.allowsMultipleSelection
        tafel.resolvesAliases = true
        tafel.message = "Modell wählen — IFC, glb, OBJ, FBX …"
        tafel.prompt = "Laden"
        let fertig: (NSApplication.ModalResponse) -> Void = { antwort in
            completionHandler(antwort == .OK ? tafel.urls : nil)
        }
        if let fenster = webView.window {
            tafel.beginSheetModal(for: fenster, completionHandler: fertig)
        } else {
            tafel.begin(completionHandler: fertig)
        }
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!,
                 withError error: Error) {
        meldeFehler(error)
    }

    func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
        meldeFehler(error)
    }

    /// Ein Fehler als Satz — derselbe wie in den Startzeilen (`Leitungsfehler` im Kern).
    private func meldeFehler(_ error: Error) {
        let ns = error as NSError
        guard ns.domain == NSURLErrorDomain else {
            melde("Die Seite des Heim-PC liess sich nicht laden (\(ns.domain) \(ns.code)).")
            return
        }
        let fehler = Leitungsfehler(urlFehlercode: ns.code)
        // ZURUECKGEZOGEN (etwa beim Neuladen) ist kein Befund.
        if fehler == .abgebrochen { return }
        melde(fehler.satz)
    }
}

extension Notification.Name {
    /// «Darstellung → Visbox-Seite» im Menue der App (Entscheid 94, 14.10.2026).
    static let seiteOeffnen = Notification.Name("flaeche.seiteOeffnen")
}
