import SwiftUI

/// Ein Bild gross — mit dem **Schalter Prüfen/Entwerfen am Bild** (Entscheide 15, 30), dem
/// Vergleich Vorher/Nachher (17: die Unterlage gegen das Ergebnis), einem eigenen Namen (19),
/// dem Teilen samt Zeichen (20) und, seit dem 23.09.2026, **«Darauf skizzieren»**: das Bild
/// als Unterlage unter die Ebenen (`Daraufskizzieren`).
///
/// Anordnung nach dem Blatt «Bilder»: links das Bild, rechts ein Feld von 360 pt mit dem,
/// was der Server über das Bild sagt. Im Hochformat liegt das Feld darunter — derselbe
/// Inhalt, eigene Anordnung (Entscheid 1).
///
/// **Der eigene Name geht in die Mappe** (`POST /api/benennen`, seit 22.09.2026), nicht mehr
/// in die Einstellungen dieses iPads; ein zweites Gerät sieht ihn damit auch.
struct Bildansicht: View {
    @ObservedObject var stand: Bildbandstand
    @ObservedObject var verbindung: Verbindungsstand
    /// Das Bild, mit dem die Ansicht geöffnet wurde. Gezeigt wird der **aktuelle** Stand
    /// desselben Bildes aus `stand` — kommen die Bytes nach dem Öffnen an, erscheinen sie.
    let bild: Bandbild
    let schliessen: () -> Void

    @Environment(\.accessibilityReduceMotion) private var bewegungReduziert
    @State private var vergleich: Bildvergleichsart = .nebeneinander
    @State private var benennen = false
    @State private var neuerName = ""
    @State private var namensQuittung: Handlungsquittung?
    @State private var variantenOffen = false

    init(stand: Bildbandstand, verbindung: Verbindungsstand = .gemeinsam, bild: Bandbild,
         schliessen: @escaping () -> Void) {
        self.stand = stand
        self.verbindung = verbindung
        self.bild = bild
        self.schliessen = schliessen
    }

    /// Derselbe Name **aus derselben Mappe** (`Bandbild.mappe`, 23.09.2026): Nach einem
    /// Wechsel der Mappe ist ein Bild gleichen Namens ein anderes Bild.
    private var aktuell: Bandbild {
        stand.bilder.first { $0.bild == bild.bild && $0.mappe == bild.mappe } ?? bild
    }

    private var zeichen: Pruefzeichen {
        aktuell.pruefzeichen(stand.lesart(aktuell))
    }

    var body: some View {
        VStack(spacing: 0) {
            kopf
            Divider().overlay(Zeichenblatt.linie)
            GeometryReader { geo in
                if Haltung(groesse: geo.size) == .quer {
                    HStack(spacing: 0) {
                        ScrollView { mitte.padding(28) }
                        Divider().overlay(Zeichenblatt.linie)
                        ScrollView { feld.padding(22) }
                            .frame(width: 360)
                            .background(Zeichenblatt.leiste)
                    }
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 28) {
                            mitte
                            feld
                        }
                        .padding(24)
                    }
                }
            }
        }
        .background(Zeichenblatt.grund)
        .foregroundStyle(Zeichenblatt.schrift)
        .alert("Eigener Name", isPresented: $benennen) {
            TextField("Name", text: $neuerName)
            Button("Übernehmen") {
                let name = aktuell.bild
                let titel = neuerName
                Task { @MainActor in
                    stand.sendet = true
                    namensQuittung = await verbindung.benenne(bild: name, titel: titel,
                                                              bildband: stand)
                    stand.sendet = false
                }
            }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Leer lassen, um wieder den Namen nach der Zeit zu zeigen. Der Name steht in "
                 + "der Mappe der HomeStation; die Datei behält ihren.")
        }
        .sheet(isPresented: $variantenOffen) {
            if let gruppe = aktuell.angaben.variantengruppe?.id {
                ScrollView {
                    Variantenansicht(stand: stand, gruppe: gruppe).padding(24)
                }
                .background(Zeichenblatt.grund)
                .foregroundStyle(Zeichenblatt.schrift)
            }
        }
    }

    // ------------------------------------------------------------------ Kopfzeile

    private var kopf: some View {
        HStack(spacing: 14) {
            Button(action: schliessen) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 20, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .accessibilityLabel("Zurück zum Bildband")

            Text(stand.name(aktuell))
                .font(Schrift.titel(26))
                .lineLimit(1)
            Button {
                neuerName = aktuell.angaben.titel ?? ""
                namensQuittung = nil
                benennen = true
            } label: {
                Image(systemName: "pencil")
                    .font(.system(size: 20, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .disabled(stand.sendet || !verbindung.gekoppelt)
            .accessibilityLabel("Namen geben")

            Spacer(minLength: 0)

            Teilenknopf(grafik: aktuell.grafik, zeichen: zeichen, titel: stand.name(aktuell))
        }
        .padding(.horizontal, 20)
        .frame(minHeight: 76)
        .background(Zeichenblatt.leiste)
    }

    // ---------------------------------------------------------------- das Bild

    /// Vorher und Nachher, sobald die Unterlage da ist (Entscheid 17) — sonst das Bild allein,
    /// **und der Satz, warum**: keine Unterlage genannt, noch nicht geladen, oder nicht
    /// ladbar. Drei verschiedene Lagen, drei verschiedene Sätze.
    @ViewBuilder
    private var mitte: some View {
        VStack(alignment: .leading, spacing: 18) {
            if let vorher = stand.vorherbild(aktuell) {
                HStack(spacing: Zeichenblatt.abstand) {
                    ForEach(Bildvergleichsart.allCases) { art in
                        Button(art.name) {
                            mitBewegung { vergleich = art }
                        }
                        .buttonStyle(Wahlknopfstil(gewaehlt: vergleich == art, breite: nil))
                        .fixedSize(horizontal: true, vertical: false)
                        .accessibilityAddTraits(vergleich == art ? .isSelected : [])
                    }
                    Text(vergleich.hinweis)
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                Bildvergleich(vorher: vorher, nachher: aktuell.grafik,
                              zeichen: zeichen, art: vergleich)
                if let name = aktuell.vorher {
                    Text("Unterlage: " + name)
                        .font(Schrift.zahl(12))
                        .foregroundStyle(Zeichenblatt.leise)
                        .textSelection(.enabled)
                }
            } else {
                Bildflaeche(grafik: aktuell.grafik, vorhanden: aktuell.vorhanden)
                    .pruefzeichen(zeichen, .gross)
                Text(ohneVorherSatz)
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        // DIE UNTERLAGE WIRD BEIM OEFFNEN GEHOLT, und neu, wenn die Mappe dem Bild eine andere
        // nennt — aus der Mappe des Bildes, nicht aus der eingestellten (23.09.2026). Am Gerät
        // unbestätigt.
        .task(id: aktuell.vorher) {
            if let name = aktuell.vorher {
                await verbindung.ladeUnterlage(name, mappe: aktuell.mappe, bildband: stand)
            }
        }
    }

    /// Warum hier kein Vorher steht — **nie «es gibt keines»**, wenn es nur nicht geladen ist.
    private var ohneVorherSatz: String {
        guard let name = aktuell.vorher else {
            return "Die Mappe nennt zu diesem Bild keine Unterlage — darum hier ohne Vorher."
        }
        if let satz = stand.satzZurUnterlage(aktuell) {
            return "Die Unterlage «\(name)» ist nicht geladen: \(satz)"
        }
        return "Die Unterlage «\(name)» wird geladen."
    }

    // -------------------------------------------------------------- das Seitenfeld

    private var feld: some View {
        VStack(alignment: .leading, spacing: 22) {
            // «DARAUF SKIZZIEREN» ZUOBERST (23.09.2026): Das Bild wird die Unterlage des
            // Blattes, und die Ansicht schliesst sich zum Blatt hin.
            Daraufskizzieren(verbindung: verbindung, bild: aktuell, titel: stand.name(aktuell),
                             schliessen: schliessen)

            VStack(alignment: .leading, spacing: 10) {
                Abschnittstitel(text: "Wie das Bild gelesen wird")
                HStack(spacing: 8) {
                    lesartKnopf(.pruefen, "Prüfen")
                    lesartKnopf(.entwerfen, "Entwerfen")
                }
                Text("Beim Prüfen ist erfundenes Volumen ein Fehler. Beim Entwerfen ist es der Zweck — dann wird kein Urteil gesprochen, und das Zeichen ist blau.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }

            if let q = namensQuittung {
                Text(q.satz)
                    .font(Schrift.text(13))
                    .foregroundStyle(q.ausgang == .angenommen ? Zeichenblatt.leise
                                                               : Zeichenblatt.schrift)
                    .fixedSize(horizontal: false, vertical: true)
            }

            VStack(alignment: .leading, spacing: 8) {
                Abschnittstitel(text: "Was der Server sagt")
                Text(zeichen.zeile)
                    .font(Schrift.zahl(22, .medium))
                    .foregroundStyle(Color(zeichen.art.schrift))
                // DIE SCHWELLE NUR NEBEN EINER GEZEIGTEN PRUEFZAHL — das entscheidet der Kern
                // (`Pruefzeichen.schwelle`), nicht diese Ansicht.
                if let grenze = zeichen.schwelle {
                    Text("Schwelle \(grenze)")
                        .font(Schrift.zahl(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                if let satz = aktuell.satz, !satz.isEmpty {
                    Text(satz)
                        .font(Schrift.text(14))
                        .fixedSize(horizontal: false, vertical: true)
                }
                if case .fehlt = zeichen.zahl {
                    Text("Die Zahl zu diesem Urteil kam nicht mit. Sie wird nicht als 0 gezeigt.")
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            ForEach(zeichen.vorbehalte, id: \.satz) { v in
                VStack(alignment: .leading, spacing: 6) {
                    Abschnittstitel(text: "Vorbehalt")
                    Text(v.satz)
                        .font(Schrift.text(14))
                        .foregroundStyle(Color(Pruefzeichen.vorbehaltSchrift))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(14)
                .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
                .overlay(RoundedRectangle(cornerRadius: 10)
                    .strokeBorder(Color(Pruefzeichen.vorbehaltSchrift), lineWidth: 1))
            }

            VStack(alignment: .leading, spacing: 6) {
                Abschnittstitel(text: "Hinweise der Bildstufe")
                // DREI ANTWORTEN: nicht gemessen (`nil`), gemessen ohne Hinweis (`[]`), und
                // die Hinweise selbst, unverändert.
                if let hinweise = aktuell.angaben.hinweise {
                    if hinweise.isEmpty {
                        Text("Gemessen, ohne Hinweis.")
                            .font(Schrift.text(13))
                            .foregroundStyle(Zeichenblatt.leise)
                    }
                    ForEach(Array(hinweise.enumerated()), id: \.offset) { paar in
                        Text(paar.element)
                            .font(Schrift.text(13))
                            .fixedSize(horizontal: false, vertical: true)
                    }
                } else {
                    Text("Nicht gemessen — die Bildstufe hat zu diesem Bild nichts gemeldet.")
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            if aktuell.angaben.variantengruppe?.id != nil {
                Button("Varianten nebeneinander") { variantenOffen = true }
                    .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
            }

            VStack(alignment: .leading, spacing: 8) {
                Abschnittstitel(text: "Datei")
                Text(aktuell.bild)
                    .font(Schrift.zahl(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .textSelection(.enabled)
            }

            Text("Beim Teilen geht das Zeichen mit: Der Vorbehalt steht auf dem Bild, nicht daneben.")
                .font(Schrift.text(13))
                // LEISE UND NICHT GELB wie im Entwurf (Blatt «Bilder»): Gelb heisst
                // «nicht gemessen», und dieser Satz ist keine Messaussage.
                .foregroundStyle(Zeichenblatt.leise)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func lesartKnopf(_ l: Bildlesart, _ titel: String) -> some View {
        let an = stand.lesart(aktuell) == l
        return Button(titel) {
            mitBewegung { stand.setzeLesart(l, fuer: aktuell) }
        }
        .buttonStyle(Wahlknopfstil(gewaehlt: an, breite: nil))
        .accessibilityAddTraits(an ? .isSelected : [])
    }

    private func mitBewegung(_ tu: () -> Void) {
        if bewegungReduziert {
            tu()
        } else {
            withAnimation(.easeInOut(duration: 0.18), tu)
        }
    }
}
