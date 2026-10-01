import SwiftUI

/// Das erste Verbinden: eine HomeStation wählen (oder ihre Adresse eintippen) und die
/// **sechsstellige Zahl** eingeben, die sie in ihrem Fenster zeigt (Entscheid Nr. 26,
/// Protokoll §7) — oder, unterwegs, die der Mac unter «iPad koppeln» zeigt (Entscheid 63).
///
/// * **Genau eine gefunden → die** (vorausgefüllt). **Mehrere → ein Mensch wählt**, keine
///   wird vorgezogen (`Suche.waehle`).
/// * **Unterwegs findet die Suche nichts** — dort gibt es kein Heimnetz. Die App spricht
///   dann direkt über Tailscale mit dem Heim-PC (`https://<rechner>.<netz>.ts.net:8443`,
///   Entscheid 63, Protokoll §8), und diese Adresse wird eingetippt oder eingefügt. Darum
///   steht das Eintippen gleichwertig daneben und nicht in einem Untermenü. Geprüft wird
///   sie im Kern (`Suche.pruefe(eingabe:)`, für https mit `Heimadresse.pruefe` der Mac-App).
/// * Die Zahl wird **vor** dem Senden geprüft (sechs Ziffern): Ein Tippfehler soll keinen der
///   wenigen Versuche verbrauchen, die die HomeStation zulässt.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
@MainActor
struct Koppelbildschirm: View {
    @ObservedObject var stand: Verbindungsstand
    @Environment(\.dismiss) private var schliessen

    @State private var adresseText = ""
    /// Der Name der gewählten HomeStation — gilt nur, solange die Adresse ihre ist.
    @State private var gewaehlt: GefundenerDienst?
    @State private var zahl = ""
    @State private var satz: String?
    @State private var geklappt = false
    @State private var laeuft = false

    /// Was die Prüfung im Kern zur Eingabe sagt — die Adresse, oder der Satz, warum nicht.
    private var pruefung: Heimadresse.Pruefung { Suche.pruefe(eingabe: adresseText) }
    private var ziel: URL? {
        if case .gut(let url, _) = pruefung { return url }
        return nil
    }
    private var bereit: Bool { ziel != nil && Kopplungszahl(zahl) != nil && !laeuft }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    fundteil
                    adressteil
                    zahlteil
                    ordnerteil
                    knopfteil
                    if stand.gekoppelt { trennteil }
                }
                .padding(28)
                .frame(maxWidth: 640, alignment: .leading)
                .frame(maxWidth: .infinity)
            }
            .background(Zeichenblatt.grund)
            .navigationTitle("Mit der HomeStation koppeln")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fertig") { schliessen() }
                }
            }
        }
        .onAppear {
            stand.starteSuche()
            if adresseText.isEmpty, let a = stand.adresse { adresseText = Suche.eingabetext(a) }
        }
        // NUR DIE SUCHE DIESES BILDSCHIRMS endet hier. Sucht das Pruefen die gekoppelte
        // HomeStation unter ihrem Namen, sucht es weiter (`Suchwunsch`, Durchsicht 22.09.2026).
        .onDisappear { stand.beendeSuche() }
        .onChange(of: stand.gefunden) { _, neu in
            // GENAU EINE → DIE, aber nur, solange nichts eingetippt ist.
            if case .einer(let d) = Suche.waehle(neu), adresseText.isEmpty, let a = d.adresse {
                waehle(d, a)
            }
        }
    }

    // ------------------------------------------------------------------- Teile

    private var fundteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Im Heimnetz gefunden")
            switch Suche.waehle(stand.gefunden) {
            case .keiner:
                // BERICHTIGT 01.10.2026: Seit dem 22.09. kündigt sich die HomeStation selbst an
                // (Protokoll §8). Unterwegs ist seit Entscheid 63 nicht mehr der Mac der Weg,
                // sondern Tailscale direkt zum Heim-PC — dort findet die Suche nichts, und der
                // Satz schickt darum zum Eintippen, nicht zur Mac-App.
                Text("Noch keine gefunden. Zu Hause: läuft die HomeStation im Heimnetz? "
                     + "Unterwegs: Tailscale am iPad einschalten und unten die Adresse des "
                     + "Heim-PC eintippen.")
                    .font(Schrift.text(14))
                    .foregroundStyle(Zeichenblatt.leise)
            case .einer(let d):
                fundknopf(d)
            case .mehrere(let liste):
                Text("Mehrere gefunden — bitte eine wählen. Die App rät nicht.")
                    .font(Schrift.text(14))
                    .foregroundStyle(Zeichenblatt.leise)
                ForEach(liste) { d in fundknopf(d) }
            }
            if let s = stand.suchSatz {
                Text(s)
                    .font(Schrift.text(14))
                    .foregroundStyle(Zeichenblatt.schrift)
            }
        }
    }

    private func fundknopf(_ d: GefundenerDienst) -> some View {
        let an = gewaehlt?.name == d.name && ziel == d.adresse
        return Button {
            if let a = d.adresse { waehle(d, a) }
        } label: {
            HStack {
                Text(d.name)
                // UNTERWEGS VERMITTELT DER MAC (Protokoll §8b): klein und ruhig dazu, damit
                // klar ist, wer antwortet. Gekoppelt wird genau gleich.
                if d.ueberDenMac {
                    Text("über den Mac")
                        .font(Schrift.text(12))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                Spacer()
                Text(d.adresse.map(Suche.eingabetext) ?? "wird aufgelöst …")
                    .font(Schrift.zahl(13))
            }
            .padding(.horizontal, 16)
        }
        .buttonStyle(Wahlknopfstil(gewaehlt: an, breite: nil))
        .disabled(d.adresse == nil)
        .accessibilityAddTraits(an ? .isSelected : [])
    }

    private var adressteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Oder die Adresse eintippen")
            TextField(Heimadresse.beispiel, text: $adresseText)
                .font(Schrift.zahl(18))
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(Zeichenblatt.linie))
                .frame(minHeight: Zeichenblatt.tippziel)
            // DER SATZ KOMMT AUS DER PRUEFUNG IM KERN — er sagt, WAS an der Eingabe nicht
            // geht (Schema, Pfad, Kennwort in der Adresse …), statt einer Regel fuer alle Faelle.
            switch pruefung {
            case .schlecht(let grund) where !adresseText.isEmpty:
                Text(grund)
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.schrift)
            case .gut(_, let hinweis?):
                Text(hinweis)
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
            default:
                EmptyView()
            }
            Text("Zu Hause: die Adresse aus dem Fenster der HomeStation, z. B. "
                 + "192.168.1.20:8731. Unterwegs: die Adresse des Heim-PC aus Tailscale, "
                 + "\(Heimadresse.beispiel) — dafür muss Tailscale am iPad an sein.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    private var zahlteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Die Zahl von der HomeStation")
            TextField("000000", text: $zahl)
                .font(Schrift.zahl(44, .medium))
                .keyboardType(.numberPad)
                .textContentType(.oneTimeCode)
                .multilineTextAlignment(.center)
                .padding(12)
                .background(RoundedRectangle(cornerRadius: 12).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(Zeichenblatt.linie))
                .onChange(of: zahl) { _, neu in
                    // NUR ZIFFERN, HOECHSTENS SECHS — was darueber hinausgeht, wird nicht
                    // still gekuerzt gesendet, sondern gar nicht erst eingetragen.
                    let sauber = String(neu.unicodeScalars
                        .filter { ("0"..."9").contains($0) }
                        .map { Character($0) }
                        .prefix(6))
                    if sauber != neu { zahl = sauber }
                }
            // UNTERWEGS ZEIGT SIE DER MAC (Entscheid 63): Er fragt den Heim-PC danach.
            // Gekoppelt wird trotzdem direkt mit dem Heim-PC — der Mac reicht nur die Zahl.
            Text("Zu Hause steht sie im Fenster der HomeStation. Unterwegs zeigt sie der Mac "
                 + "unter «iPad koppeln». Sie gilt nur zehn Minuten und nur für wenige Versuche.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    private var ordnerteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Projektordner auf der HomeStation — freiwillig")
            TextField("leer: der Ordner, mit dem sie gestartet wurde", text: $stand.ordner)
                .font(Schrift.zahl(15))
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(Zeichenblatt.linie))
        }
    }

    private var knopfteil: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button {
                Task { await koppeln() }
            } label: {
                Text(laeuft ? "Verbindet …" : "Koppeln")
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: bereit, breite: nil))
            .disabled(!bereit)

            if let satz {
                Text(satz)
                    .font(Schrift.text(15, geklappt ? .semibold : .regular))
                    .foregroundStyle(geklappt ? Zeichenblatt.gewaehltSchrift : Zeichenblatt.schrift)
                    .accessibilityAddTraits(.updatesFrequently)
            }
        }
    }

    private var trennteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Gekoppelt")
            Text("Trennen vergisst die HomeStation auf diesem iPad. Drüben bleibt das Gerät "
                 + "angemeldet — einen Weg, es dort zu vergessen, gibt es nicht. Geparkte "
                 + "Skizzen bleiben auf dem iPad.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
            Button("Trennen") {
                stand.trenne()
                satz = nil
                geklappt = false
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
        }
    }

    // ---------------------------------------------------------------- Handeln

    private func waehle(_ d: GefundenerDienst, _ a: URL) {
        gewaehlt = d
        adresseText = Suche.eingabetext(a)
    }

    private func koppeln() async {
        guard let ziel else { return }
        laeuft = true
        // DER NAME GILT NUR, WENN DIE ADRESSE NOCH SEINE IST — sonst ist sie eingetippt.
        let name = (gewaehlt?.adresse == ziel) ? gewaehlt?.name : nil
        let mac = (gewaehlt?.adresse == ziel) && gewaehlt?.ueberDenMac == true
        let (ok, text) = await stand.koppele(adresse: ziel, name: name, ueberDenMac: mac,
                                             zahl: zahl)
        laeuft = false
        geklappt = ok
        satz = text
        // DIE ZAHL IST NACH JEDEM VERSUCH WEG: Drueben ist sie entweder verbraucht oder hat
        // einen Versuch gekostet. Stehen lassen hiesse, zum zweiten Mal dasselbe zu senden.
        zahl = ""
    }
}
