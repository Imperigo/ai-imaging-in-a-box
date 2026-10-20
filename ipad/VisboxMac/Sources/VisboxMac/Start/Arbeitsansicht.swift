import AppKit
import Combine
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
/// **Seit S3/S4 (Plan UI-Gleichheit, 20.10.2026)** steht in der Knotenansicht keine Leiste mehr
/// rechts: Die Kugel des Assistenten mit ihrem Gespraechsfeld und die Einstellungs-Insel stehen in der
/// Seite (wortgleich aus KosmoOrbit). Das Gespraech fuehrt weiter das `Assistentenmodell` hier (seine
/// Regeln im Kern, `Assistentengespraech`); die Seite bekommt seine Lage, «Wer rechnet?», «Claude über
/// MCP» und «Neuigkeiten» ueber die Bruecke «visboxWirt». Auf der Visbox-Seite bleibt die Leiste.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Arbeitsansicht: View {
    @ObservedObject var leitung: Heimleitung
    let zurueck: () -> Void
    /// Was ohne Rechner gesperrt ist (`Leitungsschalter.sperre`) — hier: der Assistent.
    var sperre: Rechnersperre = .offen
    /// Der Heim-PC-Chip der Knotenansicht (`Knotenwirt.rechnerchip`) und der Satz des Bands —
    /// vom `Hauptfenster`, das den Takt der Leitung haelt.
    var rechner = Knotenwirt.rechnerchip(eingerichtet: false, lage: .startet)
    var leitungSatz: String?
    /// Fuer «Wer rechnet?» in der Einstellungs-Insel (S4): die Lage der Leitung, ob eingerichtet, und
    /// ob eine neuere Fassung bereitsteht («Neuigkeiten»).
    var leitungslage: Leitungslage = .startet
    var eingerichtet = false
    var angebot: Freigabe?

    // VON AUSSEN GEREICHT (`zentrale: .gemeinsam, claude: .gemeinsam` im `Hauptfenster`), nicht
    // als Vorgabewert hier — wie in der `Kileiste`: Ein Vorgabewert laese die Einzelstuecke
    // ausserhalb des Hauptfadens.
    @ObservedObject var zentrale: Kizentrale
    @ObservedObject var claude: Claudeanschluss

    @State private var flaechenSatz: String?
    @State private var wahl: Flaechenwahl = Flaechenwahl.beimOeffnen
    /// Das Thema der Knotenansicht (Entscheid 116 (3)) — gemerkt im `Hauptfenster`, nicht hier:
    /// Diese Ansicht merkt sich nichts (Entscheid 85 C).
    var thema: Knotenwirt.Thema = .vorgabe
    @State private var claudeVerbunden = false
    /// Das Gespraech mit dem Assistenten — hier gehalten, damit es beim Wechsel Knoten ↔ Seite bleibt.
    @StateObject private var assistent = Assistentenhalter()
    /// «Wer rechnet?» — dieselbe Ablage wie das Blatt «Einrichten» (`Rechnerwahl.schluessel`).
    @StateObject private var rechnerwahl = Rechnerwahlspeicher()

    var body: some View {
        VStack(spacing: 0) {
            // DIE KOPFLEISTE NUR NOCH AUF DER VISBOX-SEITE (Entscheid 115, Plan UI-Gleichheit S1,
            // 20.10.2026): Ueber den Knoten stehen die Kopfteile von KosmoOrbit in der Seite selbst
            // (Palette am Logo = Startansicht, Einstellungs- und Speichern-Kreis, Zweitgruppe mit
            // der Fassung). Eine zweite Leiste darueber waere ein zweiter Kopf.
            if wahl == .seite {
                Seitenkopf(kopfzeile: leitung.bild.kopfzeile, zurueckZuDenKnoten: { wahl = .knoten },
                           zurueck: zurueck)
            }

            HStack(spacing: 0) {
                flaeche
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                // DIE LEISTE NUR AUF DER VISBOX-SEITE (S3): In der Knotenansicht steht das
                // Gespraechsfeld an der Kugel in der Seite.
                if wahl != .knoten {
                    Rectangle().fill(Startfarbe.linie).frame(width: 1)
                    assistentenPlatz
                        .frame(width: 360)
                        .frame(maxHeight: .infinity)
                }
            }
        }
        .background(Startfarbe.grund)
        .foregroundStyle(Startfarbe.text)
        // DIE SEITE NUR NOCH UEBER DAS MENUE (Entscheid 94): «Darstellung → Visbox-Seite».
        .onReceive(NotificationCenter.default.publisher(for: .seiteOeffnen)) { _ in
            wahl = .seite
        }
        // OB CLAUDE VERBUNDEN IST, sagt der Kern erst nach einem Kontakt (`Claudezeile`) — der
        // Kern ist ein `actor`, darum nachgesehen wie in der KI-Leiste.
        .task { await wacheUeberClaude() }
        // DER ASSISTENT FUER BEIDE FLAECHEN: angelegt mit der Adresse des Heim-PC, sein Stand
        // nachgesehen, solange die Arbeit offen ist (vorher tat das die Leiste selbst).
        .onAppear { assistent.richteEin(basis: leitung.adresse, anmeldung: leitung.anmeldung) }
        .onChange(of: leitung.adresse) { _, neu in
            assistent.richteEin(basis: neu, anmeldung: leitung.anmeldung)
        }
        .onChange(of: leitung.anmeldung) { _, neu in
            assistent.richteEin(basis: leitung.adresse, anmeldung: neu)
        }
        .onDisappear { assistent.halte() }
    }

    /// Die Lage fuer die Kopfteile der Knotenansicht (`window.visboxWirt.lage`). Kein Kennwort.
    private var wirtlage: Knotenwirt.Lage {
        Knotenwirt.Lage(leitung: leitungSatz, sperre: sperre.satz, rechner: rechner,
                        claudeVerbunden: claudeVerbunden,
                        version: fassung, modus: zentrale.modus, thema: thema,
                        assistent: assistentenlage,
                        rechnerwahl: Rechnerwahllage(wahl: rechnerwahl.wahl, befund: rechnerwahl.befund,
                                                     lage: leitungslage, eingerichtet: eingerichtet),
                        claudeMcp: Claudemcplage(an: claude.lage != .aus, satz: claude.lage.satz),
                        neuigkeiten: Neuigkeitenlage(fassung: fassung, angebot: angebot))
    }

    private var fassung: String {
        Knotenwirt.version(Aktualisierung.kleineNummer(
            Aktualisierung.laufendeNummer(Bundle.main.infoDictionary)))
    }

    /// Das Gespraech fuer das Feld an der Kugel — ohne Heim-PC mit dem Satz, warum nicht.
    private var assistentenlage: Assistentenlage {
        guard let modell = assistent.modell else {
            return Assistentenlage(gespraech: Assistentengespraech(), zeile: nil,
                                   gesperrt: sperre.satz ?? Assistentenlage.ohneHeim)
        }
        return Assistentenlage(gespraech: modell.gespraech, zeile: modell.zeile, gesperrt: sperre.satz,
                               feld: modell.seitenfeld)
    }

    /// Ein Wunsch der Kopfteile (`Knotenwirt.Wunsch`).
    private func erfuelle(_ wunsch: Knotenwirt.Wunsch) {
        switch wunsch {
        case .bereit:
            break
        case .modus(let modus):
            zentrale.setzeModus(modus)
        case .rechner:
            NotificationCenter.default.post(name: .einrichtenOeffnen, object: Einrichtenanfang.rechner)
        case .rechnerWaehlen(let arbeit, let ort):
            rechnerwahl.waehle(ort, fuer: arbeit)
        case .claude(let an):
            claude.schalte(an)
        case .oeffne(.startansicht):
            zurueck()
        case .oeffne(.visboxSeite):
            wahl = .seite
        case .oeffne(.einrichten):
            NotificationCenter.default.post(name: .einrichtenOeffnen, object: nil)
        case .oeffne(.aktualisieren):
            NotificationCenter.default.post(name: .aktualisierenOeffnen, object: nil)
        case .einstellung(let abschnitt):
            NotificationCenter.default.post(name: .einrichtenOeffnen,
                                            object: Einrichtenanfang(abschnitt: abschnitt))
        case .assistent(let w):
            erfuelleAssistent(w)
        case .merke(let schluessel, let wert):
            Knotengedaechtnis.merke(schluessel, wert)
        }
    }

    /// Ein Wunsch des Gespraechsfelds — ohne Heim-PC geschieht nichts (das Feld sagt den Satz).
    private func erfuelleAssistent(_ w: Assistentenwunsch) {
        guard let modell = assistent.modell, sperre.satz == nil else { return }
        switch w {
        case .frage(let text): Task { await modell.frageVonSeite(text) }
        case .anwenden: Task { await modell.anwenden() }
        case .ablehnen: modell.ablehnen()
        case .aendern: modell.aendernVonSeite()
        }
    }

    private func wacheUeberClaude() async {
        while !Task.isCancelled {
            let kontakt = await claude.kern.letzterKontakt
            claudeVerbunden = Knotenwirt.claudeVerbunden(lage: claude.lage.kernlage, letzterKontakt: kontakt)
            try? await Task.sleep(nanoseconds: 5_000_000_000)
        }
    }

    @ViewBuilder
    private var flaeche: some View {
        // DIE KNOTEN AUCH OHNE HEIM-PC (Schritt 1): Sie kommen aus dem Bündel; ihre Datenwege
        // antworten dann sofort mit einem Satz. Die Seite braucht den Heim-PC weiter.
        if wahl.ausDemBuendel || (leitung.adresse != nil && leitung.anmeldung != nil) {
            ZStack(alignment: .bottom) {
                Heimflaeche(basis: leitung.adresse, anmeldung: leitung.anmeldung, wahl: wahl,
                            meldung: $flaechenSatz, wirtlage: wirtlage, wuensche: erfuelle)
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
    //
    // DIE KI-LEISTE NUR AUF DER VISBOX-SEITE (Plan UI-Gleichheit S2, 20.10.2026): In der
    // Knotenansicht stehen Claude-Marke, Karten, Erzaehlzeile und Selbstaendigkeit in der Seite
    // (wortgleich aus KosmoOrbit). Die `Kizentrale` bleibt Zustand und Sperre fuer MCP; ihr
    // Rueckgaengig-Verlauf fuer Claude bleibt getrennt (Entscheid 114).
    @ViewBuilder
    private var assistentenPlatz: some View {
        if let modell = assistent.modell {
            Assistentenleiste(modell: modell, gesperrt: sperre.satz, mitKi: wahl != .knoten)
        } else {
            Assistentenplatzhalter(stand: leitung.bild.assistent, mitKi: wahl != .knoten)
        }
    }
}

/// Die Kopfleiste ueber der Visbox-Seite (bis Entscheid 115 auch ueber den Knoten): Marke mit
/// kleiner Nummer, die Zeile des Heim-PC, «Zurück zu den Knoten» und «Startzeilen».
struct Seitenkopf: View {
    let kopfzeile: String
    let zurueckZuDenKnoten: () -> Void
    let zurueck: () -> Void

    var body: some View {
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
            Text(kopfzeile)
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
            Spacer()
            // ENTSCHEID 94 (14.10.2026): Die Knoten sind DIE Arbeitsflaeche zum Rendern; von der
            // Seite fuehrt dieser eine Knopf zurueck.
            Button("Zurück zu den Knoten", action: zurueckZuDenKnoten)
                .buttonStyle(.plain)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
            Button("Startzeilen", action: zurueck)
                .buttonStyle(.plain)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
        }
        .padding(.horizontal, 22)
        .frame(height: 52)
        .background(Startfarbe.flaeche)
    }
}

/// Womit das Blatt «Einrichten» aufgeht, wenn die Knotenansicht danach fragt (Einstellungs-Kreis,
/// Heim-PC-Chip): «Wer rechnet?», «Claude über MCP» oder der Anfang.
struct Einrichtenanfang: Equatable {
    let abschnitt: String?

    static let rechner = Einrichtenanfang(abschnitt: "rechner")
}

/// Der Platz des Assistenten, solange seine Seitenleiste nicht verdrahtet ist: sein Zustand,
/// wie die Startzeile ihn kennt — **kein Bedienelement**, das so tut, als ginge es schon.
struct Assistentenplatzhalter: View {
    let stand: Zeilenstand
    /// Ob die KI-Leiste oben steht — nicht in der Knotenansicht (dort traegt die Seite sie).
    var mitKi = true

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { zeit in
            VStack(alignment: .leading, spacing: 12) {
                // DER KI-TEIL AUCH OHNE HEIM-PC (Blatt 30, Feld 1): Claude bedient die Knoten aus
                // dem Bündel; nur der Assistent braucht den Heim-PC.
                if mitKi {
                    Kileiste(assistentSatz: "Assistent: " + stand.wort,
                             zentrale: .gemeinsam, anschluss: .gemeinsam)
                    Divider()
                }
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
    /// Die Lage fuer die Kopfteile der Knotenansicht und was die App auf ihre Wuensche tut
    /// (`visboxWirt`, Plan UI-Gleichheit S1/S2).
    var wirtlage: Knotenwirt.Lage?
    var wuensche: (Knotenwirt.Wunsch) -> Void = { _ in }

    func makeCoordinator() -> Flaechenlotse {
        Flaechenlotse(basis: basis, anmeldung: anmeldung, wahl: wahl)
    }

    func makeNSView(context: Context) -> WKWebView {
        let einstellung = WKWebViewConfiguration()
        einstellung.websiteDataStore = .nonPersistent()
        // DAS EIGENE ADRESSSCHEMA (Schritt 1): Es muss VOR dem Bau der Ansicht stehen —
        // danach nimmt WebKit keinen Gastgeber mehr an. Die Konfiguration hält ihn fest.
        einstellung.setURLSchemeHandler(context.coordinator.quelle, forURLScheme: Knotenwege.schema)
        // DER BOTE DER KNOTENANSICHT (KI-Bedienung Stufe 3): «visboxKi» — die Seite meldet
        // Taetigkeit, Karten und Entscheide; die App ruft `window.visboxKi` zurueck. Wie das
        // Schema VOR dem Bau der Ansicht.
        Knotenki.haengeAn(einstellung, bote: context.coordinator.kibote)
        // DIE ZWEITE BRUECKE «visboxWirt» (Plan UI-Gleichheit S1/S2): dieselbe Wache, eigener Bote.
        // Das Thema steht vor dem ersten Bild in der Seite (`themaSkript`).
        Knotenwirtbote.haengeAn(einstellung, bote: context.coordinator.wirtbote)
        if let lage = wirtlage {
            einstellung.userContentController.addUserScript(Knotenwirtbote.themaSkript(lage.thema))
        }
        // WAS DIE SEITE BEHAELT (S4): Akzent, Anzeige, Rueckgaengig-Schalter — vor dem ersten Bild.
        einstellung.userContentController.addUserScript(
            WKUserScript(source: Knotenwirt.merkSkript(Knotengedaechtnis.werte),
                         injectionTime: .atDocumentStart, forMainFrameOnly: true))
        let ansicht = WKWebView(frame: .zero, configuration: einstellung)
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        lotse.wirtbote.wuensche = wuensche
        if let lage = wirtlage { lotse.wirtbote.setze(lage) }
        ansicht.navigationDelegate = lotse
        // DER DATEIWAEHLER DER SEITE (Entscheid 90): Ohne `uiDelegate` tut ein
        // `<input type="file">` in einer WKWebView nichts — «Datei laden …» am Modell-Knoten
        // waere ein Knopf ohne Wirkung.
        ansicht.uiDelegate = lotse
        lotse.lade(ansicht)
        return ansicht
    }

    /// Die Flaeche geht: Die Karten der Knotenansicht fallen weg, Claude hoert «VERWORFEN».
    static func dismantleNSView(_ ansicht: WKWebView, coordinator: Flaechenlotse) {
        Knotenki.seiteGeht("Die Knotenansicht wurde geschlossen")
    }

    func updateNSView(_ ansicht: WKWebView, context: Context) {
        let lotse = context.coordinator
        lotse.melde = { satz in meldung = satz }
        lotse.wirtbote.wuensche = wuensche
        if let lage = wirtlage { lotse.wirtbote.setze(lage) }
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
    /// Der Bote «visboxKi» der Knotenansicht (KI-Bedienung Stufe 3, `Knotenki`).
    let kibote = Knotenki()
    /// Der Bote «visboxWirt» der Kopfteile (Plan UI-Gleichheit S1/S2, `Knotenwirtbote`).
    let wirtbote = Knotenwirtbote()

    init(basis: URL?, anmeldung: Anmeldung?, wahl: Flaechenwahl) {
        self.basis = basis
        self.anmeldung = anmeldung
        self.wahl = wahl
        self.quelle = Knotenquelle(basis: basis, anmeldung: anmeldung)
    }

    func lade(_ ansicht: WKWebView) {
        // WAS VORHER OFFEN WAR, GEHT: Die Karten einer Knotenansicht leben nur in ihr — neu
        // geladen oder auf die Visbox-Seite umgeschaltet, gibt es sie nicht mehr.
        Knotenki.seiteGeht(wahl.ausDemBuendel ? "Die Knotenansicht wird neu geladen"
                           : "Die Knotenansicht wurde für die " + Flaechenwahl.seite.titel + " geschlossen")
        MainActor.assumeIsolated { wirtbote.seiteGeht() }
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
    /// Die Knotenansicht fragt nach dem Blatt «Einrichten» (Einstellungs-Insel › Heim-PC «Am Mac
    /// einrichten»); `object` ist ein `Einrichtenanfang` oder `nil` (der Anfang: die Kopplung).
    static let einrichtenOeffnen = Notification.Name("flaeche.einrichtenOeffnen")
    /// Die Knotenansicht fragt nach «Aktualisieren» (Einstellungs-Insel › Neuigkeiten).
    static let aktualisierenOeffnen = Notification.Name("flaeche.aktualisierenOeffnen")
}

/// Haelt das Gespraech mit dem Assistenten fuer beide Flaechen (S3) — neu angelegt nur, wenn sich
/// Adresse oder Anmeldung aendern. Reicht jede Aenderung des Modells an die Ansicht weiter, damit die
/// Lage der Knotenansicht nachkommt.
@MainActor
final class Assistentenhalter: ObservableObject {
    @Published private(set) var modell: Assistentenmodell?
    private var basis: URL?
    private var anmeldung: Anmeldung?
    private var weiter: AnyCancellable?
    private var wache: Task<Void, Never>?

    func richteEin(basis neu: URL?, anmeldung neueAnmeldung: Anmeldung?) {
        guard modell == nil || neu != basis || neueAnmeldung != anmeldung else { return }
        basis = neu
        anmeldung = neueAnmeldung
        halte()
        guard let neu else {
            modell = nil
            weiter = nil
            return
        }
        let m = Assistentenmodell(anschluss: AssistentAnschluss(basis: neu, anmeldung: neueAnmeldung),
                                  ordner: nil)
        weiter = m.objectWillChange.sink { [weak self] _ in self?.objectWillChange.send() }
        modell = m
        // DER STAND DES ASSISTENTEN (`GET /api/heim`), solange die Arbeit offen ist.
        wache = Task { await m.wacheUeberStand() }
    }

    func halte() {
        wache?.cancel()
        wache = nil
    }
}
