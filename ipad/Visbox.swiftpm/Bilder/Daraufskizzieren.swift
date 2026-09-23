import SwiftUI

/// **«Darauf skizzieren»** — ein Bild der Mappe wird die Unterlage des Blattes (Blätter
/// «Main» und «MainHoch»: «Skizze über Lauf 07»; das Wort selbst steht auf keinem Blatt und
/// ist hier gesetzt, 23.09.2026).
///
/// Ein Tipp holt das Bild (`Zeichenstand.legeUnterlage(aus:titel:verbindung:)`), legt es
/// unter die Ebenen, stellt das Seitenfeld auf «Ebenen» und schliesst die Bildansicht —
/// danach steht das Bild unter dem Stift. Die Striche bleiben, wie sie sind; eine frühere
/// Unterlage wird ersetzt. Geht es nicht, steht der Satz da, warum, und nichts wird gelegt.
///
/// *Gebaut, nicht übersetzt, am Gerät unbestätigt (23.09.2026).*
struct Daraufskizzieren: View {
    @ObservedObject var zeichnen: Zeichenstand
    @ObservedObject var verbindung: Verbindungsstand
    let bild: Bandbild
    let titel: String
    let schliessen: () -> Void

    @State private var legtGerade = false
    @State private var satz: String?

    init(zeichnen: Zeichenstand = .gemeinsam, verbindung: Verbindungsstand = .gemeinsam,
         bild: Bandbild, titel: String, schliessen: @escaping () -> Void) {
        self.zeichnen = zeichnen
        self.verbindung = verbindung
        self.bild = bild
        self.titel = titel
        self.schliessen = schliessen
    }

    /// Liegt genau dieses Bild **aus dieser Mappe** schon unter dem Blatt? Gleicher Name in
    /// einer anderen Mappe ist ein anderes Bild.
    private var liegtSchon: Bool {
        guard let u = zeichnen.stapel.unterlage else { return false }
        let mappe: String? = verbindung.ordner.isEmpty ? nil : verbindung.ordner
        return u.bild == bild.bild && u.ordner == mappe
    }

    /// Die Mappe nennt das Bild, seine Datei fehlt aber (`vorhanden == false`): Dann gibt
    /// es nichts zu holen. `nil` (nicht gefragt) ist **kein** Grund zum Sperren.
    private var fehlt: Bool { bild.vorhanden == false }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Skizzieren")
            Button {
                lege()
            } label: {
                Text(legtGerade ? "Wird geholt …" : "Darauf skizzieren")
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil))
            .disabled(legtGerade || fehlt)
            .accessibilityHint("Legt dieses Bild als Unterlage unter die Ebenen und öffnet "
                               + "das Blatt.")
            Text(erklaerung)
                .font(Schrift.text(13))
                .foregroundStyle(satz == nil ? Zeichenblatt.leise : Zeichenblatt.schrift)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var erklaerung: String {
        if let satz { return "Nicht gelegt: \(satz)" }
        if fehlt { return "Die Datei dieses Bildes fehlt in der Mappe — es kann keine Unterlage sein." }
        if liegtSchon {
            return "Liegt schon unter dem Blatt. Nochmals tippen öffnet das Blatt."
        }
        return "Das Bild kommt unter die Ebenen. Gesendet werden nur die Striche — das Bild "
            + "hat die HomeStation schon; sie setzt die Skizze darauf."
    }

    private func lege() {
        if liegtSchon {
            // DASSELBE BILD NICHT NOCHMALS HOLEN: nur das Blatt zeigen — und einblenden,
            // falls es ausgeblendet war (wer darauf skizzieren will, will es sehen).
            zeichnen.setzeUnterlageSichtbar(true)
            zeigeBlatt()
            return
        }
        legtGerade = true
        satz = nil
        Task { @MainActor in
            let grund = await zeichnen.legeUnterlage(aus: bild, titel: titel,
                                                     verbindung: verbindung)
            legtGerade = false
            if let grund {
                satz = grund
            } else {
                zeigeBlatt()
            }
        }
    }

    private func zeigeBlatt() {
        Leistenwahl.gemeinsam.seitenfeld = .ebenen
        schliessen()
    }
}
