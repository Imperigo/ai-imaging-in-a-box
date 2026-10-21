import SwiftUI
import VisboxKern

/// Das Fenster **«Mappen»** («Visbox eigenständig», Schritt 3, 21.10.2026) — nach Blatt 36 Feld 1
/// und 2 (und Blatt 28 Feld 3): «Am Mac» (öffnen), «Noch am Heim-PC» («An den Mac holen»), «Neue
/// Mappe». Geöffnet über die Palette am Logo der Knotenansicht («Mappen …») und das Menü (⌘O).
///
/// Ein natives Blatt, keine Insel in der Seite: Die Mappe ist Sache der App (Ordner am Mac), nicht
/// des Knotencodes, der in KosmoOrbit und Visbox derselbe bleibt (Entscheid 115).
///
/// *Gebaut, am Gerät unbestätigt (21.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
struct Mappenwahl: View {
    @ObservedObject var ablage: Mappenablage
    let basis: URL?
    let anmeldung: Anmeldung?
    let schliessen: () -> Void

    @State private var neuerName = ""
    @State private var holt = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(Mappensaetze.titel)
                .font(Macschriften.schrift(.titel, 26))
            ScrollView {
                VStack(alignment: .leading, spacing: 6) {
                    abschnitt(Mappensaetze.amMac)
                    ForEach(ablage.amMac) { zeile in
                        Mappenreihe(name: zeile.name, untertitel: zeile.untertitel, hervor: zeile.offen,
                                    knopf: zeile.offen ? Mappensaetze.offen : Mappensaetze.oeffnen,
                                    gesperrt: zeile.offen || holt) {
                            ablage.oeffne(zeile.ordner)
                            schliessen()
                        }
                    }
                    abschnitt(Mappensaetze.nochAmHeim).padding(.top, 8)
                    if basis == nil {
                        leise(Knotenwege.satzOhneHeim)
                    } else if ablage.amHeim.isEmpty {
                        leise(ablage.satz == nil ? Mappensaetze.nichtsAmHeim : Mappensaetze.ohneHeim)
                    }
                    ForEach(ablage.amHeim) { heim in
                        Mappenreihe(name: heim.name, untertitel: heim.untertitel, hervor: false,
                                    knopf: Mappensaetze.holen, gesperrt: holt) {
                            holt = true
                            Task {
                                let gut = await ablage.hole(heim, basis: basis, anmeldung: anmeldung)
                                holt = false
                                if gut { schliessen() }
                            }
                        }
                    }
                }
            }
            .frame(maxHeight: 380)
            if let satz = ablage.holtSatz {
                ProgressView(value: ablage.holtAnteil)
                leise(satz)
            }
            leise(Mappensaetze.fuss)
            abschnitt(Mappensaetze.neu).padding(.top, 6)
            HStack {
                TextField(Mappensaetze.namensfeld, text: $neuerName)
                    .textFieldStyle(.roundedBorder)
                Button(Mappensaetze.anlegen) {
                    ablage.legeAn(neuerName)
                    if ablage.satz == nil { schliessen() }
                }
                .disabled(neuerName.trimmingCharacters(in: .whitespaces).isEmpty || holt)
            }
            leise(Mappensaetze.neuSatz)
            if let satz = ablage.satz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.rot)
                    .fixedSize(horizontal: false, vertical: true)
            }
            HStack {
                // RUECKWAERTS (Schritt 3): ohne Mappe am Mac, wie bis 0.3.14.
                Button(Mappensaetze.wieBisher) {
                    ablage.oeffne(nil)
                    schliessen()
                }
                .buttonStyle(.link)
                .disabled(ablage.offen == nil || holt)
                .help(Mappensaetze.wieBisherSatz)
                Spacer()
                Button("Schliessen", action: schliessen)
                    .keyboardShortcut(.cancelAction)
                    .disabled(holt)
            }
            .padding(.top, 6)
        }
        .padding(28)
        .frame(width: 560, alignment: .leading)
        .task {
            ablage.ladeListe()
            await ablage.frageHeim(basis: basis, anmeldung: anmeldung)
        }
    }

    private func abschnitt(_ text: String) -> some View {
        Text(text.uppercased())
            .font(Macschriften.schrift(.zahl, 11))
            .foregroundStyle(Startfarbe.leise)
    }

    private func leise(_ text: String) -> some View {
        Text(text)
            .font(Macschriften.schrift(.text, 12))
            .foregroundStyle(Startfarbe.leise)
            .fixedSize(horizontal: false, vertical: true)
    }
}

/// Eine Zeile: Name, darunter die Herkunft, rechts der Knopf.
private struct Mappenreihe: View {
    let name: String
    let untertitel: String
    let hervor: Bool
    let knopf: String
    let gesperrt: Bool
    let tun: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            RoundedRectangle(cornerRadius: 4)
                .fill(Startfarbe.ring)
                .frame(width: 28, height: 22)
            VStack(alignment: .leading, spacing: 2) {
                Text(name).font(Macschriften.schrift(.text, 14))
                Text(untertitel)
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
            }
            Spacer()
            Button(knopf, action: tun)
                .disabled(gesperrt)
        }
        .padding(.vertical, 7)
        .padding(.horizontal, 10)
        .background(RoundedRectangle(cornerRadius: 8).fill(hervor ? Startfarbe.karte : Color.clear))
    }
}

/// Der Anker des Fensters «Mappen» — eigene kleine Ansicht wie `IpadKoppelanker`, damit der Rumpf
/// des Hauptfensters übersetzbar bleibt. Geht auf, wenn jemand `.mappenOeffnen` sendet.
struct Mappenanker: View {
    @ObservedObject var leitung: Heimleitung
    @State private var offen = false

    var body: some View {
        Color.clear
            .sheet(isPresented: $offen) {
                Mappenwahl(ablage: .gemeinsam, basis: leitung.adresse, anmeldung: leitung.anmeldung,
                           schliessen: { offen = false })
            }
            .onReceive(NotificationCenter.default.publisher(for: .mappenOeffnen)) { _ in offen = true }
    }
}

extension Notification.Name {
    /// «Mappen …» — aus der Palette am Logo (`Knotenwirt.Ziel.mappen`) oder dem Menü (⌘O).
    static let mappenOeffnen = Notification.Name("flaeche.mappenOeffnen")
}
