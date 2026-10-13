import SwiftUI

/// Fragt GitHub nach einer neueren Fassung und liest, wann die App ablaeuft — fuer den
/// **Hinweis** am iPad (Owner-Entscheid 84, 13.10.2026, Blatt 18).
///
/// **Nur ein Hinweis, kein Knopf:** Selbst ersetzen darf eine iPad-App nicht — Apple erlaubt
/// das nur ueber App Store oder TestFlight, beides mit bezahltem Konto. Aufgespielt wird am
/// Mac in Xcode.
///
/// Die Regeln (Nummer, Antwort, Tagesregel, Ablauf) stehen im Kern
/// (`Kern/Aktualisierung.swift`); hier wird nur gefragt und gelesen.
///
/// *Gebaut, am Geraet unbestaetigt (13.10.2026).*
@MainActor
final class Fassungsfrage: ObservableObject {
    static let gemeinsam = Fassungsfrage()

    /// Die neuere Nummer auf GitHub, oder `nil`.
    @Published private(set) var neu: Fassungsnummer?
    /// Der Satz zum Ablauf, nur wenn er naht (`Bereitstellungsprofil.warnung`).
    @Published private(set) var ablaufSatz: String?

    let laufend = Aktualisierung.laufendeNummer(Bundle.main.infoDictionary)

    /// Das Ablaufdatum aus `embedded.mobileprovision` — einmal gelesen; es aendert sich erst,
    /// wenn Xcode die App neu aufspielt, und dann startet sie ohnehin neu. Fehlt das Profil
    /// (Simulator, Swift Playgrounds, App Store), ist es `nil`, und es gibt keinen Hinweis.
    private static let ablauf: Date? = {
        guard let ort = Bundle.main.url(forResource: "embedded", withExtension: "mobileprovision"),
              let daten = try? Data(contentsOf: ort) else { return nil }
        return Bereitstellungsprofil.ablauf(aus: daten)
    }()

    private static let sitzung = URLSession(configuration: .ephemeral)
    private static let letzteSchluessel = "aktualisierung.letzteFrage"
    private var takt: Task<Void, Never>?

    private var letzte: Date? {
        get { UserDefaults.standard.object(forKey: Self.letzteSchluessel) as? Date }
        set { UserDefaults.standard.set(newValue, forKey: Self.letzteSchluessel) }
    }

    /// Beim Start fragen (84a), danach stuendlich nachsehen, ob die Tagesregel eine Frage
    /// faellig nennt. Im Hintergrund haelt iPadOS die Aufgabe an; `wiederAktiv` holt nach.
    func starte() {
        pruefeAblauf()
        guard takt == nil else { return }
        takt = Task { [weak self] in
            await self?.frage()
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 3_600 * 1_000_000_000)
                guard let self else { return }
                self.pruefeAblauf()
                if Aktualisierung.sollFragen(letzte: self.letzte, jetzt: Date()) {
                    await self.frage()
                }
            }
        }
    }

    /// Die App kommt wieder nach vorn — nach einer Nacht im Hintergrund ist die Frage faellig.
    func wiederAktiv() {
        pruefeAblauf()
        guard takt != nil, Aktualisierung.sollFragen(letzte: letzte, jetzt: Date()) else { return }
        Task { await frage() }
    }

    private func pruefeAblauf() {
        ablaufSatz = Self.ablauf.flatMap { Bereitstellungsprofil.hinweis(ablauf: $0, jetzt: Date()) }
    }

    private func frage() async {
        letzte = Date()
        var anfrage = URLRequest(url: Aktualisierung.abfrage,
                                 cachePolicy: .reloadIgnoringLocalCacheData,
                                 timeoutInterval: 20)
        for (name, wert) in Aktualisierung.kopfzeilen(laufend: laufend) {
            anfrage.setValue(wert, forHTTPHeaderField: name)
        }
        // STILL BEI FEHLERN: Ohne Netz gibt es keinen Hinweis, nicht eine Meldung.
        guard let geholt = try? await Self.sitzung.data(for: anfrage),
              (geholt.1 as? HTTPURLResponse)?.statusCode == 200,
              let freigabe = try? Aktualisierung.deute(geholt.0) else { return }
        neu = Aktualisierung.bietetAn(freigabe, laufend: laufend) ? freigabe.nummer : nil
    }
}

/// Die Zeilen unter der Verbindungszeile: «Neue Fassung 0.x.y verfügbar — am Mac in Xcode
/// aufspielen» und, wenn er naht, der Ablauf der 7 Tage. Jede laesst sich ausblenden — die
/// eine fuer **diese** Nummer (eine noch neuere erscheint wieder), die andere bis zum
/// naechsten Start.
struct Fassungshinweis: View {
    @ObservedObject var frage: Fassungsfrage
    @State private var ausgeblendet: Fassungsnummer?
    @State private var ablaufAusgeblendet = false

    var body: some View {
        VStack(spacing: 0) {
            if let neu = frage.neu, ausgeblendet != neu {
                zeile(Aktualisierung.ipadHinweis(neu), symbol: "arrow.down.circle") {
                    ausgeblendet = neu
                }
            }
            if let satz = frage.ablaufSatz, !ablaufAusgeblendet {
                zeile(satz, symbol: "clock.badge.exclamationmark") { ablaufAusgeblendet = true }
            }
        }
    }

    private func zeile(_ satz: String, symbol: String,
                       aus: @escaping () -> Void) -> some View {
        HStack(spacing: 12) {
            Image(systemName: symbol)
                .foregroundStyle(Zeichenblatt.leise)
                .accessibilityHidden(true)
            Text(satz)
                .font(Schrift.text(14))
            Spacer(minLength: 8)
            Button(action: aus) {
                Image(systemName: "xmark")
                    .frame(minWidth: Zeichenblatt.tippzielMindestens,
                           minHeight: Zeichenblatt.tippzielMindestens)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Hinweis ausblenden")
        }
        .padding(.horizontal, 18)
        .background(Zeichenblatt.feld)
    }
}
