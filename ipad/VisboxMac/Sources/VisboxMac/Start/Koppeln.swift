import SwiftUI
import VisboxKern

/// Das Blatt «Koppeln» nach **Blatt 17** (Owner-Entscheid 83, 13.10.2026) — statt drei Felder
/// abzutippen, sucht der Mac den Heim-PC selbst und koppelt sich mit einer Zahl.
///
/// 1. **Suchen:** die gefundenen Visbox-Heim-PCs; nur antwortende sind wählbar.
/// 2. **Zahl:** «Weiter» fordert sie an — sie erscheint am Heim-PC (Fenster und Mitteilung).
///    Feld für 6 Ziffern, «Koppeln», «Neue Zahl anfordern»; nach 3 Fehlversuchen die Meldung.
/// 3. **Verbunden:** mit den Startzeilen.
///
/// Klein darunter **«Von Hand eintragen …»** (83c) — der bisherige Dialog `Einrichten` —
/// und seit «Visbox eigenständig», Schritt 6 (20.10.2026) **«Wer rechnet? …»**: die
/// Rechner-Wahl je Arbeit (`Rechnerwahlansicht`, Blatt 28, Feld 2) — und seit der KI-Bedienung
/// Stufe 3 (20.10.2026) **«Claude über MCP …»** (`Claudeeinrichten`, Blatt 30, Feld 3).
///
/// Was ein Schritt heisst, steht im Kern (`Koppelablauf`); hier wird nur gezeigt und
/// gedrückt.
///
/// *Gebaut, am Gerät unbestätigt (13.10.2026).*
struct Koppeln: View {
    @ObservedObject var leitung: Heimleitung
    /// Der Takt der Leitung — für den Zusatz «· verbunden» in «Wer rechnet?».
    @ObservedObject var leitungstakt: Leitungssteuerung
    let fertig: () -> Void
    /// Womit das Blatt aufgeht, wenn die Knotenansicht danach fragt: «rechner» («Wer rechnet?»,
    /// der Heim-PC-Chip), «claude» («Claude über MCP»), sonst die Kopplung (Plan UI-Gleichheit S1).
    var anfang: String?

    @StateObject private var sucher = Heimsucher()
    @State private var ablauf = Koppelablauf()
    @State private var auswahl: String?
    @State private var zahl = ""
    @State private var vonHand = false
    @State private var rechner = false
    /// Einrichten › Claude über MCP (Blatt 30, Feld 3; KI-Bedienung Stufe 3).
    @State private var claude = false
    @State private var arbeitet = false

    var body: some View {
        Group {
            if claude {
                Claudeeinrichten(anschluss: .gemeinsam, zurueck: { claude = false })
            } else if rechner {
                Rechnerwahlansicht(leitung: leitung, leitungstakt: leitungstakt,
                                   zurueck: { rechner = false })
            } else if vonHand {
                VStack(alignment: .leading, spacing: 0) {
                    Einrichten(leitung: leitung, fertig: fertig)
                    Button("← Zurück zur Suche") { vonHand = false }
                        .buttonStyle(.link)
                        .padding([.horizontal, .bottom], 28)
                }
            } else {
                VStack(alignment: .leading, spacing: 16) {
                    switch ablauf.schritt {
                    case .suchen: suchen
                    case .zahl: zahlSchritt
                    case .verbunden: verbunden
                    }
                }
                .padding(28)
                .frame(width: 560)
            }
        }
        .onAppear {
            sucher.starte()
            // AUS DER KNOTENANSICHT GEFRAGT: gleich beim gewünschten Teil.
            if anfang == "rechner" { rechner = true }
            if anfang == "claude" { claude = true }
        }
        .onDisappear { sucher.halte() }
    }

    // ================================================================ 1 · suchen

    private var suchen: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Mit dem Heim-PC koppeln")
                .font(Macschriften.schrift(.titel, 30))
            Text("Der Mac sucht den Heim-PC selbst — im eigenen Tailscale-Netz und im WLAN zu "
                 + "Hause. Danach eine Zahl, die am Heim-PC erscheint, und fertig.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)

            VStack(spacing: 8) {
                ForEach(sucher.suche.kandidaten) { k in
                    kandidatenzeile(k)
                }
                if sucher.suche.kandidaten.isEmpty {
                    Text(sucher.sucht ? "Es wird gesucht …" : "Noch kein Heim-PC gefunden.")
                        .font(Macschriften.schrift(.text, 13))
                        .foregroundStyle(Startfarbe.leise)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(14)
                        .background(RoundedRectangle(cornerRadius: 10).fill(Startfarbe.karte))
                }
            }

            ForEach([sucher.tailscaleSatz, sucher.wlanSatz].compactMap { $0 }, id: \.self) { s in
                Text(s)
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack {
                Button("Von Hand eintragen …") { vonHand = true }
                    .buttonStyle(.link)
                    .font(Macschriften.schrift(.text, 12))
                Button(Rechnerwahl.titel + " …") { rechner = true }
                    .buttonStyle(.link)
                    .font(Macschriften.schrift(.text, 12))
                Button(Claudeeinrichtung.titel + " …") { claude = true }
                    .buttonStyle(.link)
                    .font(Macschriften.schrift(.text, 12))
                Spacer()
                Button("Neu suchen") { sucher.starte() }
                if !leitung.braucheEinrichten {
                    Button("Abbrechen", action: fertig)
                        .keyboardShortcut(.cancelAction)
                }
                Button("Weiter") { Task { await weiter() } }
                    .keyboardShortcut(.defaultAction)
                    .disabled(gewaehlt == nil || arbeitet)
            }
        }
    }

    private var gewaehlt: Heimkandidat? {
        sucher.suche.waehlbare.first { $0.id == auswahl } ?? (sucher.suche.waehlbare.count == 1
            ? sucher.suche.waehlbare.first : nil)
    }

    private func kandidatenzeile(_ k: Heimkandidat) -> some View {
        let an = gewaehlt?.id == k.id
        return Button {
            if k.waehlbar { auswahl = k.id }
        } label: {
            HStack(spacing: 12) {
                Circle()
                    .fill(k.waehlbar ? Startfarbe.gruen : Startfarbe.linie)
                    .frame(width: 10, height: 10)
                VStack(alignment: .leading, spacing: 2) {
                    Text(k.anzeigename)
                        .font(Macschriften.schrift(.text, 15, .semibold))
                    Text(k.satz)
                        .font(Macschriften.schrift(.text, 12))
                        .foregroundStyle(Startfarbe.leise)
                }
                Spacer()
                if an { Image(systemName: "checkmark") }
            }
            .padding(12)
            .contentShape(Rectangle())
            .background(RoundedRectangle(cornerRadius: 10)
                .fill(an ? Startfarbe.gruenKnopf : Startfarbe.karte))
            .overlay(RoundedRectangle(cornerRadius: 10)
                .stroke(an ? Startfarbe.gruen : Startfarbe.linie))
            .opacity(k.waehlbar ? 1 : 0.6)
        }
        .buttonStyle(.plain)
        .disabled(!k.waehlbar)
    }

    @MainActor
    private func weiter() async {
        guard let k = gewaehlt, ablauf.waehle(k) else { return }
        zahl = ""
        await fordereAn()
    }

    // ================================================================ 2 · die Zahl

    private var zahlSchritt: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Die Zahl vom Heim-PC")
                .font(Macschriften.schrift(.titel, 30))
            Text("Am Heim-PC erscheint jetzt eine sechsstellige Zahl — im Fenster des Dienstes "
                 + "und als Mitteilung. Sie gilt 5 Minuten und einmal.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
            if let k = ablauf.gewaehlt {
                Text(k.anzeigename + " · " + k.satz)
                    .font(Macschriften.schrift(.zahl, 12))
                    .foregroundStyle(Startfarbe.leise)
                if case .antwortet(_, let abdruck?) = k.stand {
                    Text("Zeichen des Heim-PC: \(Fingerabdruck.zeichen(abdruck)) — steht auch im "
                         + "Fenster am Heim-PC. Wer ganz sicher sein will, vergleicht.")
                        .font(Macschriften.schrift(.text, 12))
                        .foregroundStyle(Startfarbe.leise)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            TextField("", text: $zahl, prompt: Text(verbatim: "000000"))
                .textFieldStyle(.roundedBorder)
                .font(Macschriften.schrift(.zahl, 28))
                .multilineTextAlignment(.center)
                .frame(maxWidth: 260)
                .onSubmit { Task { await koppeln() } }
                .disabled(ablauf.geschlossen)
            if let satz = ablauf.satz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(ablauf.geschlossen ? Startfarbe.rot : Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
            HStack {
                Button("Zurück") { ablauf.zurueck() }
                Spacer()
                Button("Neue Zahl anfordern") { Task { await fordereAn() } }
                    .disabled(arbeitet)
                Button("Koppeln") { Task { await koppeln() } }
                    .keyboardShortcut(.defaultAction)
                    .disabled(arbeitet || !ablauf.darfKoppeln(zahl))
            }
        }
    }

    @MainActor
    private func fordereAn() async {
        guard let k = ablauf.gewaehlt else { return }
        arbeitet = true
        ablauf.angefordert(await sucher.fordereAn(bei: k))
        arbeitet = false
    }

    @MainActor
    private func koppeln() async {
        guard let k = ablauf.gewaehlt, ablauf.darfKoppeln(zahl),
              let z = Kopplungszahl(zahl) else { return }
        arbeitet = true
        let ergebnis = await sucher.verbinde(k, zahl: z)
        arbeitet = false
        if case .verbunden(let zugang, _) = ergebnis {
            if let fehler = leitung.richteEin(zugang: zugang) {
                ablauf.verbinden(.fehler(satz: fehler))
                return
            }
        }
        ablauf.verbinden(ergebnis)
        zahl = ""
    }

    // ================================================================ 3 · verbunden

    private var verbunden: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Verbunden")
                .font(Macschriften.schrift(.titel, 30))
            Text("Adresse und Benutzer sind gemerkt, das Kennwort liegt im Schlüsselbund dieses "
                 + "Mac. Die Zeilen bauen sich jetzt auf.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
            TimelineView(.periodic(from: .now, by: 1)) { zeit in
                VStack(spacing: 8) {
                    ForEach(Startzeile.allCases, id: \.self) { zeile in
                        Zeilenkarte(zeile: zeile, stand: leitung.bild[zeile], jetzt: zeit.date)
                    }
                }
            }
            HStack {
                Button(Rechnerwahl.titel + " …") { rechner = true }
                    .buttonStyle(.link)
                    .font(Macschriften.schrift(.text, 12))
                Button(Claudeeinrichtung.titel + " …") { claude = true }
                    .buttonStyle(.link)
                    .font(Macschriften.schrift(.text, 12))
                Spacer()
                Button("Fertig", action: fertig)
                    .keyboardShortcut(.defaultAction)
            }
        }
    }
}
