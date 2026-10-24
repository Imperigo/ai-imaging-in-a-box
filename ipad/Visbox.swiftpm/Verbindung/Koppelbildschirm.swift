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
/// * **Ohne Abtippen** (Entscheide 99/99b, 20.10.2026, Blatt 27): Zuoberst der **Mac in der
///   Nähe** (`Naehesucher`, beide Seiten bestätigen) und **«Mit QR-Code koppeln»**
///   (`QRLeser`). Beide liefern denselben Koppelschein — Adresse und Zahl —, und gekoppelt
///   wird damit **genau wie beim Abtippen** (`koppeln(an:name:mac:zahl:)`). Das Eintippen
///   bleibt darunter, als letzter Weg.
///
/// **Seit Entscheid 118 (21.10.2026, Blatt «iPad über den Mac») nur noch mit dem Mac,
/// verschlüsselt:** Gefunden werden nur Macs, die `tls=1` sagen (`Suche.waehleMac`); ein Mac mit
/// altem Stand steht mit Satz da, statt still zu fehlen. Die Adresse ist `https`
/// (`Suche.pruefeMac`). Der Schein bringt das Zertifikat des Mac mit, und das iPad nimmt danach
/// nur dieses an; beim Abtippen steht nach dem Koppeln das Zeichen des Mac da — zum Vergleichen.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026; Nähe und QR-Code 20.10.2026; über den Mac
/// 21.10.2026).*
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
    @State private var qrOffen = false
    @StateObject private var naehe = Naehesucher()

    /// Was die Prüfung im Kern zur Eingabe sagt — die Adresse, oder der Satz, warum nicht.
    private var pruefung: Heimadresse.Pruefung { Suche.pruefeMac(eingabe: adresseText) }
    private var ziel: URL? {
        if case .gut(let url, _) = pruefung { return url }
        return nil
    }
    private var bereit: Bool { ziel != nil && Kopplungszahl(zahl) != nil && !laeuft }
    /// Ob Nähe und QR-Code angeboten werden — ungekoppelt, oder gekoppelt und nicht erreichbar
    /// («Neu koppeln», 22.10.2026; Regel im Kern: `Verbindungszustand.bietetKoppeln`).
    private var koppelwege: Bool {
        Verbindungszustand.bietetKoppeln(gekoppelt: stand.gekoppelt, zustand: stand.zustand)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    if koppelwege {
                        if stand.gekoppelt { neuteil }
                        naeheteil
                        qrteil
                    }
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
            .navigationTitle("Mit dem Mac koppeln")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fertig") { schliessen() }
                }
            }
        }
        .onAppear {
            stand.starteSuche()
            // DIE NAEHE NUR UNGEKOPPELT — ODER WENN DER GEKOPPELTE MAC NICHT ANTWORTET (Neu koppeln).
            if koppelwege { naehe.starte() }
            // NUR WAS JETZT GILT (Demolauf 24.10.2026): Die gemerkte Adresse kommt nur ins Feld,
            // wenn der Mac unter ihr antwortet — sonst steht sie als Hinweis darunter (Kern:
            // `Suche.vorbelegung`).
            if adresseText.isEmpty, stand.ueberDenMac,
               let a = Suche.vorbelegung(gemerkt: stand.adresse, erreichbar: !koppelwege) {
                adresseText = a.absoluteString
            }
        }
        // NUR DIE SUCHE DIESES BILDSCHIRMS endet hier. Sucht das Pruefen die gekoppelte
        // HomeStation unter ihrem Namen, sucht es weiter (`Suchwunsch`, Durchsicht 22.09.2026).
        .onDisappear {
            stand.beendeSuche()
            naehe.beende()
        }
        .onChange(of: naehe.schein) { _, neu in
            // DER SCHEIN VOM MAC IST DA (geprueft im Kern): koppeln wie beim Abtippen.
            if let neu { Task { await koppeln(mit: neu) } }
        }
        .onChange(of: koppelwege) { _, an in
            if an { naehe.starte() } else { naehe.beende() }
        }
        .fullScreenCover(isPresented: $qrOffen) {
            QRLeser(gelesen: { schein in
                qrOffen = false
                Task { await koppeln(mit: schein) }
            }, abbrechen: { qrOffen = false })
        }
        .onChange(of: stand.gefunden) { _, neu in
            // GENAU EINE → DIE, aber nur, solange nichts eingetippt ist.
            if case .einer(let d) = Suche.waehleMac(neu), adresseText.isEmpty, let a = d.adresse {
                waehle(d, a)
            }
        }
    }

    // ------------------------------------------------------------------- Teile

    /// Gekoppelt, aber der Mac antwortet nicht: neu koppeln, **ohne** erst zu trennen.
    private var neuteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Neu koppeln")
            Text(Verbindungszustand.satzNeuKoppeln)
                .font(Schrift.text(14))
                .foregroundStyle(Zeichenblatt.schrift)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    /// Der Mac in der Nähe (Entscheid 99): erst fragt das iPad, dann der Mac.
    private var naeheteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Mac in der Nähe")
            switch naehe.lage {
            case .aus, .sucht:
                // EHRLICH, WENN NICHTS KOMMT (20.10.2026): nach 30 s ohne Mac sagt es das.
                Text(naehe.suchstand.satz)
                    .font(Schrift.text(14))
                    .foregroundStyle(naehe.suchstand.qrHervor ? Zeichenblatt.schrift
                                                               : Zeichenblatt.leise)
                    .fixedSize(horizontal: false, vertical: true)
            case .gefunden(let name):
                VStack(alignment: .leading, spacing: 12) {
                    Text("Mit diesem Mac koppeln?")
                        .font(Schrift.text(17, .semibold))
                        .foregroundStyle(Zeichenblatt.schrift)
                    Text(name)
                        .font(Schrift.zahl(17))
                        .foregroundStyle(Zeichenblatt.schrift)
                    Text("Danach fragt der Mac noch einmal. Erst wenn beide zustimmen, schickt er "
                         + "Adresse und Zahl — nie das Kennwort.")
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                        .fixedSize(horizontal: false, vertical: true)
                    HStack(spacing: 12) {
                        Button("Ablehnen") { naehe.lehneAb() }
                            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                        Button("Annehmen") { naehe.nimmAn() }
                            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil))
                    }
                }
                .padding(16)
                .background(RoundedRectangle(cornerRadius: 12).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 12).strokeBorder(Zeichenblatt.linie))
            case .wartetAufMac(let name):
                Text("Angenommen. Jetzt am Mac «\(name)» auf «Koppeln» drücken.")
                    .font(Schrift.text(15, .semibold))
                    .foregroundStyle(Zeichenblatt.schrift)
            case .erhalten(let name):
                Text("Adresse und Zahl von «\(name)» erhalten — das iPad koppelt.")
                    .font(Schrift.text(15))
                    .foregroundStyle(Zeichenblatt.schrift)
            case .fehler(let satz):
                Text(satz)
                    .font(Schrift.text(14))
                    .foregroundStyle(Zeichenblatt.schrift)
                    .fixedSize(horizontal: false, vertical: true)
                Button("Neu suchen") {
                    naehe.beende()
                    naehe.starte()
                }
                .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
            }
        }
    }

    /// Der QR-Code im Koppelfenster des Mac (Entscheid 99b) — mit der Kamera in der App.
    private var qrteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Oder den QR-Code lesen")
            // HERVORGEHOBEN, sobald die Naehe nicht traegt (20.10.2026).
            Button("Mit QR-Code koppeln") { qrOffen = true }
                .buttonStyle(Wahlknopfstil(gewaehlt: naehe.suchstand.qrHervor, breite: nil))
                .disabled(laeuft)
            Text("Der Mac zeigt ihn unter «iPad koppeln», zwei Minuten lang.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    private var fundteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Macs im WLAN")
            switch Suche.waehleMac(stand.gefunden) {
            case .keiner:
                // SEIT ENTSCHEID 118 (21.10.2026) der Mac, zuhause wie unterwegs: Er bietet sich
                // an, sobald dort «iPad koppeln» offen war.
                Text("Noch kein Mac gefunden. Am Mac im Menü «iPad» «iPad koppeln» öffnen — "
                     + "gleiches WLAN oder der Hotspot des Mac.")
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
            // EIN MAC MIT ALTEM STAND (unverschluesselt) fehlt nicht still — er steht mit Satz da.
            ForEach(Suche.alteMacs(stand.gefunden)) { alt in
                Label(Suche.satzAlterMac(alt.name), systemImage: "lock.open")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.schrift)
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
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    // DAS SCHLOSS (Entscheid 118): Nur verschluesselte Macs stehen hier.
                    if d.verschluesselt {
                        Image(systemName: "lock.fill")
                            .accessibilityLabel("verschlüsselt")
                    }
                    Text(d.name)
                    Spacer()
                    Text(Suche.fundtext(d))
                        .font(Schrift.zahl(13))
                }
                // DER GRUND, WENN DAS AUFLOESEN SCHEITERTE (Geraetetest 13.10.2026) — samt dem
                // vorgesehenen Weg über Tailscale.
                if let grund = d.grund, d.adresse == nil {
                    Text(grund)
                        .font(Schrift.text(12))
                        .foregroundStyle(Zeichenblatt.leise)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(.horizontal, 16)
        }
        .buttonStyle(Wahlknopfstil(gewaehlt: an, breite: nil))
        .disabled(d.adresse == nil)
        .accessibilityAddTraits(an ? .isSelected : [])
    }

    private var adressteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Oder die Adresse des Mac eintippen")
            // KEINE ECHT AUSSEHENDE ADRESSE als Platzhalter (Demolauf 24.10.2026): Sie wurde
            // fuer eine gefundene gehalten.
            TextField(Suche.adressplatzhalter, text: $adresseText)
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
            // DIE GEMERKTE ADRESSE EINES MAC, DER NICHT ANTWORTET — als Hinweis, nicht vorbelegt.
            if koppelwege, stand.gekoppelt, stand.ueberDenMac, adresseText.isEmpty,
               let a = stand.adresse {
                Text(Suche.satzZuletzt(a))
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Text("Sie steht am Mac im Fenster «iPad koppeln», unter der Zahl. Immer https — "
                 + "unverschlüsselt koppelt das iPad nicht.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    private var zahlteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            // DER LETZTE WEG (Entscheid 99): eintippen, wenn Naehe und QR-Code nicht gehen.
            Abschnittstitel(text: "Zahl eintippen — vom Mac")
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
            // SEIT ENTSCHEID 118 zeigt sie immer der Mac — er ist es, mit dem gekoppelt wird.
            Text("Der Mac zeigt sie unter «iPad koppeln», zwei Minuten lang. Sie gilt nur für "
                 + "wenige Versuche.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    private var ordnerteil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Projektordner auf der HomeStation — nur ohne Mappe am Mac")
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
            // DAS SCHLOSS UND DAS ZEICHEN DES MAC — oder warum keines (Entscheid 118).
            switch stand.anbindung {
            case .macVerschluesselt(let zeichen):
                Label("Über den Mac, verschlüsselt · Zeichen des Mac: \(zeichen)",
                      systemImage: "lock.fill")
                    .font(Schrift.text(14))
                    .foregroundStyle(Zeichenblatt.schrift)
            default:
                if let satz = stand.anbindung.satz {
                    Label(satz, systemImage: "lock.open")
                        .font(Schrift.text(14))
                        .foregroundStyle(Zeichenblatt.schrift)
                }
            }
            Text("Trennen vergisst den Mac auf diesem iPad. Am Mac bleibt das iPad angemeldet, "
                 + "bis dort «iPad vergessen» gewählt wird. Geparkte Skizzen bleiben auf dem iPad.")
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
        adresseText = a.absoluteString
    }

    private func koppeln() async {
        guard let ziel else { return }
        // DER NAME GILT NUR, WENN DIE ADRESSE NOCH SEINE IST — sonst ist sie eingetippt. Ein Mac
        // ist es immer (Entscheid 118); ohne Schein wird sein Zertifikat beim Koppeln gelernt.
        let name = (gewaehlt?.adresse == ziel) ? gewaehlt?.name : nil
        await koppeln(an: ziel, name: name, mac: true, angeheftet: nil, zahl: zahl)
    }

    /// Mit dem Schein vom Mac (Nähe oder QR-Code): Adresse und Zahl stehen dann sichtbar in
    /// den Feldern, und gekoppelt wird **derselbe Weg** wie beim Abtippen.
    private func koppeln(mit schein: Koppelschein) async {
        guard !laeuft else { return }
        gewaehlt = nil
        adresseText = schein.adresse.absoluteString
        // DER NAME, unter dem der Mac im WLAN steht — damit das iPad ihn wiederfindet, wenn der
        // Router ihm eine neue Adresse gibt.
        let name = stand.gefunden.first { $0.ueberDenMac && $0.adresse == schein.adresse }?.name
        await koppeln(an: schein.adresse, name: name, mac: true, angeheftet: schein.abdruck,
                      zahl: schein.zahl.ziffern)
    }

    private func koppeln(an ziel: URL, name: String?, mac: Bool, angeheftet: String?,
                         zahl eingabe: String) async {
        laeuft = true
        let (ok, text) = await stand.koppele(adresse: ziel, name: name, ueberDenMac: mac,
                                             angeheftet: angeheftet, zahl: eingabe)
        laeuft = false
        geklappt = ok
        satz = text
        // DIE ZAHL IST NACH JEDEM VERSUCH WEG: Drueben ist sie entweder verbraucht oder hat
        // einen Versuch gekostet. Stehen lassen hiesse, zum zweiten Mal dasselbe zu senden.
        zahl = ""
    }
}
