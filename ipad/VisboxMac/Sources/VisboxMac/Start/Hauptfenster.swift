import SwiftUI
import VisboxKern

/// Das eine Fenster: Startzeilen oder Arbeit, und beim ersten Start das Blatt «Einrichten».
///
/// **Ordnet an, entscheidet nichts.** Was das Fenster zeigt — Start, Arbeit oder
/// Vorführmodus (Blatt 13b, Strom C, Entscheid 40) —, entscheidet `Vorfuehrschalter` im Kern
/// (`fensterinhalt`); seine Versuche gehen über dieselbe Leitung (`Heimleitung.versuch`).
/// Solange der Mac noch eingerichtet wird, zeigt er keinen Vorführmodus, und weist die Tür
/// des Heim-PC ab (401/403), die Startansicht mit dem Grund — nie den Vorführmodus.
///
/// **«Einrichten» ist immer erreichbar** (Durchsicht 01.10.2026, H2): in der Werkzeugleiste
/// und im Band des Vorführmodus. Vorher stand der Knopf nur in der Startansicht, und die war
/// im Vorführmodus verdeckt — bei vertippter Adresse gab es keinen Weg hinaus.
///
/// **Zwei Takte, ein Bild** (M1): Heimleitung und Vorführschalter fragen je für sich. Nach
/// dem Einrichten beginnt der Schalter von vorn, und jede Frage der Heimleitung meldet ihren
/// Befund an ihn; was daraus folgt, sagt der Kern (`heimleitungFand`).
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
            switch vorfuehrung.schalter.fensterinhalt(eingerichtet: !leitung.braucheEinrichten,
                                                      arbeitet: arbeitet) {
            case .vorfuehrung:
                Vorfuehrbereich(steuerung: vorfuehrung,
                                ipadVerbunden: leitung.bild.ipad.steht,
                                einrichten: { einrichtenOffen = true })
            case .arbeit:
                Arbeitsansicht(leitung: leitung, zurueck: { arbeitet = false })
            case .start:
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
            // IMMER DA, in jeder Ansicht: Falsches Kennwort und vertippte Adresse behebt nur
            // dieses Blatt, und ein Neustart hilft nicht (das Kennwort bleibt im Schluesselbund).
            Button(Vorfuehrsaetze.einrichten) { einrichtenOffen = true }
                .help("Adresse des Heim-PC, Benutzer und Kennwort")
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
                // AUCH NACH «ABBRECHEN» gleich nachsehen statt bis zu 60 s zu warten; die Lage
                // bleibt, bis die Antwort da ist.
                vorfuehrung.erneutVerbinden()
            }
        }
        .onChange(of: leitung.eingerichtetUm) { _, _ in
            // NEU EINGERICHTET: Die Fehlschlaege von vorher galten einer anderen Adresse
            // oder keiner — der Schalter beginnt von vorn, statt den Vorfuehrmodus zu zeigen.
            vorfuehrung.neuEingerichtet()
        }
        .onChange(of: leitung.letzteFrage) { _, frage in
            if let frage { vorfuehrung.heimleitungFand(frage.befund) }
        }
        .onChange(of: vorfuehrung.schalter.lage) { _, lage in
            guard lage == .abgewiesen else { return }
            // DIE TUER WEIST AB: zurueck zum Start, wo der Grund steht — und die Startzeile
            // gleich neu gefragt, damit sie dasselbe sagt wie der Schalter.
            arbeitet = false
            leitung.pruefeJetzt()
        }
        .onDisappear {
            vorfuehrung.halte()
            vermittlung.halte()
        }
    }
}
