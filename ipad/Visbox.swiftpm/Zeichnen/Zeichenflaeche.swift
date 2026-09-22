import SwiftUI

/// Die Zeichenfläche: das Blatt, «Zurück»/«Vor» mit Zähler, die Stiftfarbe und die
/// Ebenen (Entscheide Nr. 2–8, Blätter «Main» und «MainHoch»).
///
/// Werkzeug und Strichstärke wählt die Leiste (`Leistenwahl`); hier wird nur gelesen,
/// was sie gewählt hat. Die Regeln stehen im Kern (`Kern/Ebenen.swift`), die Striche und
/// die PNG-Ausgabe in `Zeichenstand` — **die Schnittstelle für das Senden ist
/// `Zeichenstand.gemeinsam.pngAusgabe(_:)`.**
///
/// Im Querformat liegt die Ebenentafel rechts neben dem Blatt, im Hochformat darunter —
/// derselbe Inhalt, eine andere Anordnung (Entscheid Nr. 1).
struct Zeichenflaeche: View {
    @ObservedObject var stand: Zeichenstand
    @ObservedObject var wahl: Leistenwahl

    init(stand: Zeichenstand? = nil) {
        let s = stand ?? Zeichenstand.gemeinsam
        self.stand = s
        self.wahl = s.leistenwahl
    }

    var body: some View {
        GeometryReader { flaeche in
            if flaeche.size.width >= flaeche.size.height {
                HStack(spacing: 0) {
                    buehne
                    trennlinie.frame(width: 1)
                    Ebenentafel(stand: stand)
                        .frame(width: 300)
                }
            } else {
                VStack(spacing: 0) {
                    buehne
                    trennlinie.frame(height: 1)
                    Ebenentafel(stand: stand)
                        .frame(height: 300)
                }
            }
        }
        .background(Zeichenblatt.buehne)
    }

    private var trennlinie: some View {
        Rectangle().fill(Zeichenblatt.linie)
    }

    // ------------------------------------------------------------------ das Blatt

    private var buehne: some View {
        VStack(spacing: 14) {
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                Abschnittstitel(text: "Skizze · \(stand.stapel.aktiveEbene.name)")
                Spacer()
                Text("\(Ebenenstapel.blattBreite) × \(Ebenenstapel.blattHoehe) px")
                    .font(Schrift.zahl(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }
            ZStack {
                Zeichenleinwand(stand: stand, wahl: wahl)
                if !stand.stapel.aktiveIstZeichenbar {
                    ausgeblendetHinweis
                }
            }
            .aspectRatio(CGFloat(Ebenenstapel.blattBreite) / CGFloat(Ebenenstapel.blattHoehe),
                         contentMode: .fit)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            werkzeugzeile
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    /// Die gewählte Ebene ist ausgeblendet — dann wird nicht gezeichnet, und das steht da.
    /// *Ein Stift, der nichts tut, ohne dass es gesagt wird, sieht aus wie ein kaputter.*
    private var ausgeblendetHinweis: some View {
        VStack(spacing: 12) {
            Text("«\(stand.stapel.aktiveEbene.name)» ist ausgeblendet.")
                .font(Schrift.text(15, .semibold))
            Text("Auf eine ausgeblendete Ebene wird nicht gezeichnet.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
            Button("Einblenden") {
                stand.setzeSichtbar(stand.stapel.aktiv, true)
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: 160, hoehe: 44))
        }
        .foregroundStyle(Zeichenblatt.schrift)
        .padding(20)
        .background(RoundedRectangle(cornerRadius: 12).fill(Zeichenblatt.feld))
    }

    // ------------------------------------------------------ Zurück, Vor, Farbe

    private var werkzeugzeile: some View {
        HStack(spacing: Zeichenblatt.abstand) {
            Button {
                stand.zurueck()
            } label: {
                ZStack(alignment: .bottomTrailing) {
                    Image(systemName: "arrow.uturn.backward")
                        .font(.system(size: 22))
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    Text(stand.schritte.anzeige)
                        .font(Schrift.zahl(10))
                        .padding(.trailing, 5)
                        .padding(.bottom, 3)
                }
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .disabled(!stand.kannZurueck)
            .accessibilityLabel(zurueckName)

            Button {
                stand.vor()
            } label: {
                Image(systemName: "arrow.uturn.forward")
                    .font(.system(size: 22))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false))
            .disabled(!stand.kannVor)
            .accessibilityLabel("Vor")

            Spacer(minLength: 10)

            ForEach(Stiftfarbe.vorgaben) { vorgabe in
                Button {
                    stand.waehleFarbe(vorgabe)
                } label: {
                    Circle()
                        .fill(vorgabe.farbe)
                        .frame(width: 34, height: 34)
                        .overlay(Circle().strokeBorder(
                            stand.farbvorgabe == vorgabe.name ? Zeichenblatt.schrift
                                                              : Zeichenblatt.linie,
                            lineWidth: 2))
                        .frame(width: 44, height: 44)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Stiftfarbe \(vorgabe.name)")
                .accessibilityAddTraits(stand.farbvorgabe == vorgabe.name ? .isSelected : [])
            }
            ColorPicker("Weitere Farbe",
                        selection: Binding(get: { stand.farbe },
                                           set: { stand.waehleEigeneFarbe($0) }),
                        supportsOpacity: false)
                .labelsHidden()
                .frame(width: 44, height: 44)
        }
    }

    private var zurueckName: String {
        if let n = stand.schritte.zurueck {
            return "Zurück, noch \(n) von \(Schrittzaehler.tiefe) Schritten"
        }
        return "Zurück, Zahl der Schritte nicht gezählt"
    }
}
