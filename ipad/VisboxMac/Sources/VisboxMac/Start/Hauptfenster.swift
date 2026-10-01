import SwiftUI
import VisboxKern

/// Das eine Fenster: Startzeilen oder Arbeit, und beim ersten Start das Blatt «Einrichten».
///
/// **Ordnet an, entscheidet nichts.** Ob der Mac bei stummem Heim-PC in den Vorführmodus
/// geht (Blatt 13b, Strom C, Entscheid 40), entscheidet `Vorfuehrschalter` im Kern; seine
/// Versuche gehen über dieselbe Leitung (`Heimleitung.versuch`). Solange der Mac noch
/// eingerichtet wird, zeigt er keinen Vorführmodus — ohne Adresse ist «der Heim-PC antwortet
/// nicht» keine Aussage über den Heim-PC.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Hauptfenster: View {
    @ObservedObject var leitung: Heimleitung
    @StateObject private var vorfuehrung: Vorfuehrsteuerung
    @StateObject private var vermittlung = Vermittlungsanschluss()

    init(leitung: Heimleitung) {
        self.leitung = leitung
        _vorfuehrung = StateObject(wrappedValue: Vorfuehrsteuerung(pruefe: { [leitung] in
            await leitung.versuch()
        }))
    }

    @State private var arbeitet = false
    @State private var einrichtenOffen = false

    var body: some View {
        Group {
            if vorfuehrung.schalter.imVorfuehrmodus && !leitung.braucheEinrichten {
                Vorfuehrbereich(steuerung: vorfuehrung,
                                ipadVerbunden: leitung.bild.ipad.steht)
            } else if arbeitet {
                Arbeitsansicht(leitung: leitung, zurueck: { arbeitet = false })
            } else {
                Startansicht(leitung: leitung,
                             anfangen: { arbeitet = true },
                             einrichten: { einrichtenOffen = true })
            }
        }
        .background {
            if let dienst = vermittlung.dienst {
                Vermittlungsmelder(dienst: dienst, leitung: leitung)
            }
        }
        .toolbar {
            // DIE ZAHL FUERS IPAD GILT ZEHN MINUTEN (Protokoll §8b). Danach, oder fuer ein
            // zweites iPad, gibt es hier eine neue — und hier vergisst der Mac ein iPad.
            if let dienst = vermittlung.dienst {
                Menu("iPad") {
                    Button("Neue Zahl zum Koppeln") { dienst.neueZahl() }
                    Button("iPad vergessen") { dienst.vergissIPad() }
                }
            }
        }
        .frame(minWidth: 1100, minHeight: 700)
        .preferredColorScheme(.dark)
        .sheet(isPresented: $einrichtenOffen) {
            Einrichten(leitung: leitung, fertig: { einrichtenOffen = false })
                // OHNE ADRESSE UND KENNWORT GIBT ES NICHTS ZU ZEIGEN: Das Blatt geht erst zu,
                // wenn beides gesichert ist.
                .interactiveDismissDisabled(leitung.braucheEinrichten)
        }
        .onAppear {
            einrichtenOffen = leitung.braucheEinrichten
            leitung.starte()
            vorfuehrung.starte()
            vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
        }
        .onChange(of: leitung.adresse) { _, _ in
            vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
        }
        .onChange(of: einrichtenOffen) { _, offen in
            // NACH DEM EINRICHTEN kann das Kennwort neu sein, bei gleicher Adresse.
            if !offen {
                vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
            }
        }
        .onDisappear {
            vorfuehrung.halte()
            vermittlung.halte()
        }
    }
}
