import SwiftUI

/// Das erste Verbinden: eine HomeStation wählen (oder ihre Adresse eintippen) und die
/// **sechsstellige Zahl** eingeben, die sie in ihrem Fenster zeigt (Entscheid Nr. 26,
/// Protokoll §7).
///
/// * **Genau eine gefunden → die** (vorausgefüllt). **Mehrere → ein Mensch wählt**, keine
///   wird vorgezogen (`Suche.waehle`).
/// * **Heute findet die Suche nichts** — der Server kündigt sich noch nicht an (Protokoll §8).
///   Darum steht das Eintippen gleichwertig daneben und nicht in einem Untermenü.
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

    private var ziel: URL? { Suche.adresse(ausEingabe: adresseText) }
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
            if adresseText.isEmpty, let a = stand.adresse { adresseText = Koppelbildschirm.text(a) }
        }
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
                Text("Noch keine gefunden. Die HomeStation kündigt sich heute nicht selbst an — "
                     + "ihre Adresse steht in ihrem Fenster (Start mit --im-heimnetz).")
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
                Spacer()
                Text(d.adresse.map(Koppelbildschirm.text) ?? "wird aufgelöst …")
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
            TextField("192.168.1.20:8731", text: $adresseText)
                .font(Schrift.zahl(18))
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 10).strokeBorder(Zeichenblatt.linie))
                .frame(minHeight: Zeichenblatt.tippziel)
            if !adresseText.isEmpty && ziel == nil {
                Text("So lässt sich die HomeStation nicht ansprechen. Gemeint ist die Adresse "
                     + "aus ihrem Fenster, z. B. 192.168.1.20:8731 — nur http, ohne Pfad.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }
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
            Text("Sie steht im Fenster der HomeStation, wenn sie mit --kopplung gestartet "
                 + "wurde. Sie gilt nur kurz und nur für wenige Versuche.")
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
        adresseText = Koppelbildschirm.text(a)
    }

    private func koppeln() async {
        guard let ziel else { return }
        laeuft = true
        // DER NAME GILT NUR, WENN DIE ADRESSE NOCH SEINE IST — sonst ist sie eingetippt.
        let name = (gewaehlt?.adresse == ziel) ? gewaehlt?.name : nil
        let (ok, text) = await stand.koppele(adresse: ziel, name: name, zahl: zahl)
        laeuft = false
        geklappt = ok
        satz = text
        // DIE ZAHL IST NACH JEDEM VERSUCH WEG: Drueben ist sie entweder verbraucht oder hat
        // einen Versuch gekostet. Stehen lassen hiesse, zum zweiten Mal dasselbe zu senden.
        zahl = ""
    }

    /// Eine Adresse, wie ein Mensch sie tippt: ohne `http://`.
    nonisolated static func text(_ adresse: URL) -> String {
        var t = adresse.absoluteString
        if t.hasPrefix("http://") { t.removeFirst("http://".count) }
        return t
    }
}
