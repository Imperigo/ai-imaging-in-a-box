import SwiftUI
import VisboxKern

/// Das Blatt «Einrichten» — **einmal**, beim ersten Start: Adresse des Heim-PC und Kennwort.
///
/// * Die **Adresse** prüft der Kern (`Heimadresse.pruefe`: https, Anschluss, kein Pfad, kein
///   Kennwort darin) und sie landet in den Einstellungen des Mac (`Heimgedaechtnis`).
/// * **Benutzer und Kennwort** landen im Schlüsselbund (`Heimschluesselbund`) — nie in einer
///   Datei, nie im Protokoll. Der Benutzer ist ein Vorschlag aus der Marke, kein fester Wert
///   (Protokoll §2): Der Server nennt ihn, und er kann sich mit dem Namen ändern.
/// * Ist schon ein Kennwort gemerkt, darf das Feld leer bleiben — dann gilt das gemerkte.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Einrichten: View {
    @ObservedObject var leitung: Heimleitung
    let fertig: () -> Void

    @State private var adresseText = ""
    @State private var benutzerText = ""
    @State private var kennwortText = ""
    @State private var satz: String?

    private var kennwortGemerkt: Bool { leitung.anmeldung != nil }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Einrichten")
                .font(Macschriften.schrift(.titel, 30))
            Text("Einmal: wo der Heim-PC zu erreichen ist, und mit welchem Kennwort. Beides "
                 + "steht am Heim-PC — die Adresse in der Tailscale-App, Benutzer und Kennwort "
                 + "im Fenster, in dem der Server gestartet wurde.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)

            feld("Adresse des Heim-PC") {
                TextField("", text: $adresseText, prompt: Text(Heimadresse.beispiel))
                    .autocorrectionDisabled()
            }
            feld("Benutzer") {
                TextField("", text: $benutzerText, prompt: Text(Heimadresse.vorgabeBenutzer))
                    .autocorrectionDisabled()
            }
            feld("Kennwort") {
                SecureField("", text: $kennwortText,
                            prompt: Text(verbatim: kennwortGemerkt
                                         ? "leer lassen: das gemerkte bleibt"
                                         : "aus dem Fenster am Heim-PC"))
            }

            Text("Das Kennwort liegt danach im Schlüsselbund dieses Mac, nirgends sonst.")
                .font(Macschriften.schrift(.text, 12))
                .foregroundStyle(Startfarbe.leise)

            if let satz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.rot)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack {
                Spacer()
                if !leitung.braucheEinrichten {
                    Button("Abbrechen", action: fertig)
                        .keyboardShortcut(.cancelAction)
                }
                Button("Sichern", action: sichere)
                    .keyboardShortcut(.defaultAction)
            }
        }
        .padding(28)
        .frame(width: 520)
        .onAppear {
            adresseText = leitung.adresse?.absoluteString ?? ""
            benutzerText = leitung.benutzer ?? Heimadresse.vorgabeBenutzer
        }
    }

    private func feld<Inhalt: View>(_ titel: String,
                                    @ViewBuilder _ inhalt: () -> Inhalt) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(titel)
                .font(Macschriften.schrift(.text, 13, .semibold))
            inhalt()
                .textFieldStyle(.roundedBorder)
                .font(Macschriften.schrift(.zahl, 13))
        }
    }

    private func sichere() {
        let url: URL
        switch Heimadresse.pruefe(adresseText) {
        case .schlecht(let grund):
            satz = grund
            return
        case .gut(let gut, _):
            url = gut
        }
        let benutzer = benutzerText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !benutzer.isEmpty else {
            satz = "Der Benutzer fehlt — er steht im Fenster am Heim-PC."
            return
        }
        // DAS KENNWORT WIRD NICHT BESCHNITTEN: Ein Leerzeichen kann dazugehoeren. Nur ein
        // ganz leeres Feld heisst «das gemerkte behalten».
        let kennwort = kennwortText.isEmpty ? nil : kennwortText
        if let fehler = leitung.richteEin(adresse: url, benutzer: benutzer, kennwort: kennwort) {
            satz = fehler
            return
        }
        kennwortText = ""
        satz = nil
        fertig()
    }
}
