import SwiftUI
import VisboxKern
import WebKit

/// Die Arbeit nach «Schon anfangen» (Entscheid 39) — **für v0.1.7 die Fläche des Heim-PC**,
/// daneben der Platz für den Assistenten.
///
/// Die Fläche ist die Webseite, die der Visbox-Server am Heim-PC unter `/` ausliefert
/// (`oberflaeche/seite.html`), in einer `WKWebView`: Mappe und Bilder gehen damit sofort,
/// ohne dass der Mac etwas davon nachbauen muss. Angemeldet wird über die
/// Basic-Herausforderung des Servers, mit Benutzer und Kennwort aus dem Schlüsselbund — und
/// **nur gegenüber dem eingerichteten Heim-PC** (Name und Anschluss müssen stimmen).
///
/// Der Assistent kommt rechts dazu, sobald er geladen ist; bis seine Seitenleiste verdrahtet
/// ist, steht dort sein Zustand aus den Startzeilen.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Arbeitsansicht: View {
    @ObservedObject var leitung: Heimleitung
    let zurueck: () -> Void

    @State private var flaechenSatz: String?

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 16) {
                Text(Marke.name)
                    .font(Macschriften.schrift(.titel, 25))
                Rectangle().fill(Startfarbe.linie).frame(width: 1, height: 24)
                Text(leitung.bild.kopfzeile)
                    .font(Macschriften.schrift(.text, 14))
                    .foregroundStyle(Startfarbe.leise)
                Spacer()
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
    }

    @ViewBuilder
    private var flaeche: some View {
        if let basis = leitung.adresse, let anmeldung = leitung.anmeldung {
            ZStack(alignment: .bottom) {
                Heimflaeche(basis: basis, anmeldung: anmeldung, meldung: $flaechenSatz)
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
                                                            anmeldung: leitung.anmeldung))
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

/// Die Seite des Heim-PC in einer `WKWebView`.
///
/// **Nichts auf der Platte:** ein flüchtiger Datenspeicher (`nonPersistent`) — keine Kekse,
/// kein Zwischenspeicher, keine gemerkte Anmeldung über das Programmende hinaus.
struct Heimflaeche: NSViewRepresentable {
    let basis: URL
    let anmeldung: Anmeldung
    @Binding var meldung: String?

    func makeCoordinator() -> Flaechenlotse {
        Flaechenlotse(basis: basis, anmeldung: anmeldung)
    }

    func makeNSView(context: Context) -> WKWebView {
        let einstellung = WKWebViewConfiguration()
        einstellung.websiteDataStore = .nonPersistent()
        let ansicht = WKWebView(frame: .zero, configuration: einstellung)
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        ansicht.navigationDelegate = lotse
        lotse.lade(ansicht)
        return ansicht
    }

    func updateNSView(_ ansicht: WKWebView, context: Context) {
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        // NEU EINGERICHTET (andere Adresse, anderes Kennwort): neu laden, sonst bliebe die
        // Seite mit der alten Anmeldung offen.
        if lotse.basis != basis || lotse.anmeldung != anmeldung {
            lotse.basis = basis
            lotse.anmeldung = anmeldung
            lotse.lade(ansicht)
        }
    }
}

/// Führt die Webfläche: lädt die Seite, beantwortet die Anmeldung, meldet Fehler als Satz.
final class Flaechenlotse: NSObject, WKNavigationDelegate {
    var basis: URL
    var anmeldung: Anmeldung
    var melde: (String?) -> Void = { _ in }

    init(basis: URL, anmeldung: Anmeldung) {
        self.basis = basis
        self.anmeldung = anmeldung
    }

    func lade(_ ansicht: WKWebView) {
        guard let ziel = Wege.adresse(Wege.seite, basis: basis) else {
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
        guard raum.authenticationMethod == NSURLAuthenticationMethodHTTPBasic else {
            completionHandler(.performDefaultHandling, nil)
            return
        }
        guard raum.host.lowercased() == basis.host?.lowercased(),
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
