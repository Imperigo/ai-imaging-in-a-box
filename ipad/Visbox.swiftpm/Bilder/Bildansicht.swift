import SwiftUI

/// Ein Bild gross — mit dem **Schalter Prüfen/Entwerfen am Bild** (Entscheide 15, 30), dem
/// Vergleich Vorher/Nachher (17), einem eigenen Namen (19) und dem Teilen samt Zeichen (20).
///
/// Anordnung nach dem Blatt «Bilder»: links das Bild, rechts ein Feld von 360 pt mit dem,
/// was der Server über das Bild sagt. Im Hochformat liegt das Feld darunter — derselbe
/// Inhalt, eigene Anordnung (Entscheid 1).
struct Bildansicht: View {
    @ObservedObject var stand: Bildbandstand
    /// Das Bild, mit dem die Ansicht geöffnet wurde. Gezeigt wird der **aktuelle** Stand
    /// desselben Bildes aus `stand` — kommen die Bytes nach dem Öffnen an, erscheinen sie.
    let bild: Bandbild
    let schliessen: () -> Void

    @Environment(\.accessibilityReduceMotion) private var bewegungReduziert
    @State private var vergleich: Bildvergleichsart = .nebeneinander
    @State private var benennen = false
    @State private var neuerName = ""

    private var aktuell: Bandbild {
        stand.bilder.first { $0.bild == bild.bild } ?? bild
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
            Button("Übernehmen") { stand.benenne(aktuell, als: neuerName) }
            Button("Abbrechen", role: .cancel) {}
        } message: {
            Text("Leer lassen, um wieder den Namen nach der Zeit zu zeigen. Der Name bleibt auf diesem iPad.")
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
                neuerName = stand.eigeneNamen[aktuell.bild] ?? ""
                benennen = true
            } label: {
                Image(systemName: "pencil")
                    .font(.system(size: 20, weight: .regular))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .accessibilityLabel("Eigenen Namen geben")

            Spacer(minLength: 0)

            Teilenknopf(grafik: aktuell.grafik, zeichen: zeichen, titel: stand.name(aktuell))
        }
        .padding(.horizontal, 20)
        .frame(minHeight: 76)
        .background(Zeichenblatt.leiste)
    }

    // ---------------------------------------------------------------- das Bild

    @ViewBuilder
    private var mitte: some View {
        VStack(alignment: .leading, spacing: 18) {
            if aktuell.vorher != nil {
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
                Bildvergleich(vorher: aktuell.vorher, nachher: aktuell.grafik,
                              zeichen: zeichen, art: vergleich)
            } else {
                Bildflaeche(grafik: aktuell.grafik, vorhanden: aktuell.vorhanden)
                    .pruefzeichen(zeichen, .gross)
                Text("Kein Vergleichsbild aus dem Modell geladen — darum hier ohne Vorher.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }
        }
    }

    // -------------------------------------------------------------- das Seitenfeld

    private var feld: some View {
        VStack(alignment: .leading, spacing: 22) {
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

            VStack(alignment: .leading, spacing: 8) {
                Abschnittstitel(text: "Was der Server sagt")
                Text(zeichen.zeile)
                    .font(Schrift.zahl(22, .medium))
                    .foregroundStyle(Color(zeichen.art.schrift))
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
