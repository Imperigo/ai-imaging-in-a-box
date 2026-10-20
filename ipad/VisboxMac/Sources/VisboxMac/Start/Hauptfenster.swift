import SwiftUI
import VisboxKern

/// Das eine Fenster: Startzeilen oder Arbeit, und beim ersten Start das Blatt «Einrichten».
///
/// **Ordnet an, entscheidet nichts.** Was das Fenster zeigt — Start oder Arbeit —, welches
/// Band oben steht und was gesperrt ist, entscheidet `Leitungsschalter` im Kern
/// (`fensterinhalt`, `band`, `sperre`); seine Versuche gehen über dieselbe Leitung
/// (`Heimleitung.versuch`).
///
/// **Seit «Visbox eigenständig», Schritt 2 (Entscheid 103b, 20.10.2026) gibt es keinen
/// Vorführmodus mehr.** Bis 0.3.0 ersetzte er nach der Schwelle das Fenster durch vorher
/// gerechnete Bilder. Jetzt bleibt die Arbeit (Knoten aus dem Bündel); oben steht das Band
/// «Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht. · Erneut
/// verbinden» (Blatt 28, Feld 1), und wer noch im Start steht, kommt von selbst in die Arbeit
/// (`oeffnetDieArbeit`). Weist die Tür ab (401/403), steht dasselbe Band mit eigenem Satz und
/// «Einrichten» — die Arbeit bleibt offen.
///
/// **«Einrichten» ist immer erreichbar** (Durchsicht 01.10.2026, H2): in der Werkzeugleiste
/// und im Band bei einer Absage.
///
/// **Zwei Takte, ein Bild** (M1): Heimleitung und Leitungsschalter fragen je für sich. Nach
/// dem Einrichten beginnt der Schalter von vorn, und jede Frage der Heimleitung meldet ihren
/// Befund an ihn; was daraus folgt, sagt der Kern (`heimleitungFand`).
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Hauptfenster: View {
    @ObservedObject var leitung: Heimleitung
    @ObservedObject var aktualisierung: Fassungswaechter
    @StateObject private var leitungstakt: Leitungssteuerung
    @StateObject private var vermittlung = Vermittlungsanschluss()

    init(leitung: Heimleitung, aktualisierung: Fassungswaechter) {
        self.leitung = leitung
        self.aktualisierung = aktualisierung
        _leitungstakt = StateObject(wrappedValue: Leitungssteuerung(pruefe: { [leitung] in
            await leitung.versuch()
        }))
    }

    @State private var arbeitet = false
    @State private var einrichtenOffen = false
    @State private var aktualisierenOffen = false
    /// Das Koppelfenster «iPad koppeln» (Entscheid 99) — zwei Minuten, dann zu.
    @State private var ipadKoppelnOffen = false
    // ENTSCHEID 89: vom versteckten Ort gestartet → Umzug nach «Programme» anbieten.
    @State private var umzugOffen = false
    @State private var umzugFehler: String?

    var body: some View {
        flaeche
        .background {
            // DIE VERMITTLUNG MELDET NUR, WENN SIE AN IST (Entscheid 63): Sonst gehört die
            // Zeile «iPad» dem direkten Weg über Tailscale und der Zahl aus «iPad koppeln».
            if let dienst = vermittlung.dienst, vermittlung.angeboten {
                Vermittlungsmelder(dienst: dienst, leitung: leitung)
            }
        }
        .background {
            // EIN EIGENER ANKER FUER DAS BLATT «AKTUALISIEREN»: Zwei `.sheet` an derselben
            // Ansicht streiten sich in SwiftUI darum, welches gilt.
            Color.clear.sheet(isPresented: $aktualisierenOffen) {
                Aktualisierenblatt(waechter: aktualisierung,
                                   schliessen: { aktualisierenOffen = false })
            }
        }
        .background {
            // NACH DEM NEUSTART AUS DEM AKTUALISIEREN (14.10.2026): «Visbox 0.x.y ist
            // installiert» — oder dass sie nicht ankam. Ein eigener Anker, wie oben.
            Neustartmeldung(waechter: aktualisierung)
            // DAS KOPPELFENSTER «iPad koppeln» (Entscheid 99): ebenso ein eigener Anker, als
            // eigene Ansicht und ohne weiteren Modifikator — mit einem mehr gab der Uebersetzer
            // am Rumpf auf (Mac-CI 20.10.2026: «unable to type-check … in reasonable time»).
            IpadKoppelanker(offen: $ipadKoppelnOffen, leitung: leitung)
        }
        .toolbar { werkzeuge }
        .frame(minWidth: 1100, minHeight: 700)
        .preferredColorScheme(.dark)
        .sheet(isPresented: $einrichtenOffen) {
            // SEIT ENTSCHEID 83 (13.10.2026) zuerst die Kopplung mit Zahl (Blatt 17); der
            // bisherige Dialog ist darin der kleine Link «Von Hand eintragen …» (83c).
            Koppeln(leitung: leitung, leitungstakt: leitungstakt,
                    fertig: { einrichtenOffen = false })
                // OHNE ADRESSE UND KENNWORT GIBT ES NICHTS ZU ZEIGEN: Das Blatt geht erst zu,
                // wenn beides gesichert ist.
                .interactiveDismissDisabled(leitung.braucheEinrichten)
        }
        .alert(Aktualisierung.umzugTitel, isPresented: $umzugOffen) {
            Button("Später", role: .cancel) {}
            Button(Aktualisierung.umzugKnopf) {
                Umzug.zieheUndStarteNeu { satz in umzugFehler = satz }
            }
        } message: {
            Text(umzugFehler ?? Aktualisierung.umzugSatz)
        }
        .onAppear {
            einrichtenOffen = leitung.braucheEinrichten
            umzugOffen = Umzug.istVersteckt
            aktualisierung.pruefeNeustart()
            leitung.starte()
            // BEIM START UND EINMAL TAEGLICH (84a); ein zweites Fenster startet nichts neu.
            aktualisierung.starte()
            leitungstakt.starte()
            vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
            // DIE LESEWEGE FUER CLAUDE (KI-Bedienung Stufe 4): Mappe, Skizzen, Bild, Abbruch.
            Heimlesen.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
        }
        .onChange(of: leitung.adresse) { _, _ in
            vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
            Heimlesen.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
        }
        .onChange(of: einrichtenOffen) { _, offen in
            // NACH DEM EINRICHTEN kann das Kennwort neu sein, bei gleicher Adresse.
            if !offen {
                vermittlung.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
                Heimlesen.richteAus(adresse: leitung.adresse, anmeldung: leitung.anmeldung)
                // AUCH NACH «ABBRECHEN» gleich nachsehen statt bis zu 60 s zu warten; die Lage
                // bleibt, bis die Antwort da ist.
                leitungstakt.erneutVerbinden()
            }
        }
        .onChange(of: leitung.eingerichtetUm) { _, _ in
            // NEU EINGERICHTET: Die Fehlschlaege von vorher galten einer anderen Adresse
            // oder keiner — der Schalter beginnt von vorn, statt «nicht erreichbar» zu zeigen.
            leitungstakt.neuEingerichtet()
        }
        .onChange(of: leitung.letzteFrage) { _, frage in
            if let frage { leitungstakt.heimleitungFand(frage.befund) }
        }
        .onChange(of: leitungstakt.schalter.lage) { _, lage in
            // OHNE RECHNER IN DIE ARBEIT (Entscheid 103b): an der Stelle, an der bis 0.3.0 der
            // Vorfuehrmodus kam. Und gemerkt — kommt der Heim-PC zurueck, bleibt man dort.
            if leitungstakt.schalter.oeffnetDieArbeit(eingerichtet: !leitung.braucheEinrichten) {
                arbeitet = true
            }
            // DIE TUER WEIST AB: die Startzeile gleich neu gefragt, damit sie dasselbe sagt
            // wie das Band. Die Arbeit bleibt offen (bis 0.3.0 ging es zurueck zum Start).
            if lage == .abgewiesen { leitung.pruefeJetzt() }
        }
        .onDisappear {
            leitungstakt.halte()
            vermittlung.halte()
        }
    }

    // DAS BAND UND DARUNTER START ODER ARBEIT — als eigene Teile, damit der Rumpf von `body`
    // uebersetzbar bleibt (Mac-CI 20.10.2026: «unable to type-check … in reasonable time»).
    private var flaeche: some View {
        let eingerichtet = !leitung.braucheEinrichten
        let band = leitungstakt.schalter.band(eingerichtet: eingerichtet)
        return VStack(spacing: 0) {
            if let band, !band.weich {
                Leitungsband(band: band,
                             erneutVerbinden: { leitungstakt.erneutVerbinden() },
                             einrichten: { einrichtenOffen = true })
            }
            inhalt(eingerichtet: eingerichtet)
        }
        // DAS WEICHE BAND (20.10.2026): Ein Aussetzer ist kein Zustand. Solange die Schwelle
        // nicht erreicht ist, steht oben nur «kurz nicht erreichbar — verbinde neu …».
        .overlay(alignment: .top) {
            KurzWegBand(zeigen: band?.weich == true)
        }
    }

    @ViewBuilder
    private func inhalt(eingerichtet: Bool) -> some View {
        let schalter = leitungstakt.schalter
        switch schalter.fensterinhalt(eingerichtet: eingerichtet, arbeitet: arbeitet) {
        case .arbeit:
            Arbeitsansicht(leitung: leitung, zurueck: { arbeitet = false },
                           sperre: schalter.sperre(eingerichtet: eingerichtet))
        case .start:
            Startansicht(leitung: leitung,
                         anfangen: { arbeitet = true },
                         einrichten: { einrichtenOffen = true },
                         anfangenMoeglich: schalter.anfangenMoeglich(
                            leitungSteht: leitung.bild.schonAnfangen),
                         anfangenSatz: schalter.anfangenSatz(
                            startzeilen: leitung.bild.anfangenSatz,
                            leitungSteht: leitung.bild.schonAnfangen))
        }
    }

    // DIE WERKZEUGLEISTE als eigener Teil (20.10.2026): Im Rumpf von `body` stand sie mit allen
    // Ankern in EINEM Ausdruck, und mit dem Koppelfenster gab der Uebersetzer auf.
    @ViewBuilder
    private var werkzeuge: some View {
        // DER KNOPF «● 0.x.y VERFUEGBAR — AKTUALISIEREN» (Entscheid 84, Blatt 18): nur,
        // wenn GitHub eine NEUERE Nummer hat (84b). EIN KLICK (Entscheid 87): Er oeffnet das
        // Blatt UND startet das Laden; danach ersetzt sich die App und startet neu.
        if let angebot = aktualisierung.angebot {
            Button {
                aktualisierenOffen = true
                aktualisierung.ladeUndErsetze()
            } label: {
                Text(Aktualisierung.knopf(angebot.nummer))
                    .foregroundStyle(Startfarbe.gruenText)
            }
            .help("Eine neue Fassung liegt auf GitHub")
        }
        // IMMER DA, in jeder Ansicht: Falsches Kennwort und vertippte Adresse behebt nur
        // dieses Blatt, und ein Neustart hilft nicht (das Kennwort bleibt im Schluesselbund).
        Button(Leitungssaetze.einrichten) { einrichtenOffen = true }
            .help("Adresse des Heim-PC, Benutzer und Kennwort")
        // DAS IPAD (Entscheid 63): Unterwegs spricht es selbst über Tailscale mit dem
        // Heim-PC. Der Mac holt dort nur die Zahl zum ersten Koppeln (`POST /api/kopplung`,
        // zwei Minuten gültig) und zeigt sie in der Zeile «iPad». Die Vermittlung über den
        // Mac (§8b) steht darunter, ausgeschaltet, bis man sie einschaltet — sie ist im
        // fremden WLAN unverschlüsselt.
        // SEIT ENTSCHEID 99 (20.10.2026) oeffnet «iPad koppeln» das Koppelfenster: Zahl,
        // QR-Code und der Mac in der Naehe, zwei Minuten lang. Es holt die Zahl selbst.
        if leitung.adresse != nil {
            Menu("iPad") {
                Button("iPad koppeln") { ipadKoppelnOffen = true }
                if let dienst = vermittlung.dienst {
                    Divider()
                    Toggle("iPad über diesen Mac anbieten (unverschlüsselt)",
                           isOn: Binding(get: { vermittlung.angeboten },
                                         set: { vermittlung.schalteAnbieten($0) }))
                    Button("Neue Zahl zum Koppeln über den Mac") { dienst.neueZahl() }
                        .disabled(!vermittlung.angeboten)
                    Button("iPad vergessen (über den Mac)") { dienst.vergissIPad() }
                        .disabled(!vermittlung.angeboten)
                }
            }
        }
    }
}

/// Der Anker des Koppelfensters «iPad koppeln» (Entscheid 99) — eine eigene kleine Ansicht,
/// wie `Neustartmeldung`.
private struct IpadKoppelanker: View {
    @Binding var offen: Bool
    @ObservedObject var leitung: Heimleitung

    var body: some View {
        Color.clear.sheet(isPresented: $offen) {
            IpadKoppelfenster(leitung: leitung, schliessen: { offen = false })
        }
    }
}

/// «Visbox 0.x.y ist installiert» nach dem Neustart aus dem Aktualisieren (14.10.2026) — eine
/// eigene kleine Ansicht, damit der Rumpf des Fensters nicht noch einen Ausdruck mehr traegt.
private struct Neustartmeldung: View {
    @ObservedObject var waechter: Fassungswaechter

    private var offen: Binding<Bool> {
        Binding(get: { waechter.neustartBefund != nil },
                set: { neu in if !neu { waechter.bestaetigungGesehen() } })
    }

    var body: some View {
        let satz: String = waechter.neustartBefund?.satz ?? ""
        Color.clear.alert(satz, isPresented: offen) {
            Button("OK", role: .cancel) { waechter.bestaetigungGesehen() }
        }
    }
}
