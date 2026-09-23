import SwiftUI

/// Der Inhalt des **einen** Seitenfelds im Arbeitsplatz (Blätter «Main» und «MainHoch»).
///
/// Oben, immer sichtbar: **was die Skizze tut — Prüfen oder Entwerfen** (Entscheide 15 und
/// 30). Die Wahl gilt für jede Bestellung aus dem Seitenfeld («Rechnen lassen», «Drei
/// Startwerte rechnen», «Als Ebenen-Reihe rechnen»). Darunter ein Umschalter: die **Ebenen**
/// (`Ebenentafel` der Einheit «Zeichnen», hier nur hingelegt) **oder die Mappe**
/// (`Mappentafel`). Nie beides nebeneinander — zwei Seitenfelder nähmen dem Blatt die Mitte.
///
/// Der Umschalter steht in `Leistenwahl.seitenfeld` und nicht im Zustand dieser Ansicht:
/// Er übersteht so das Drehen und das Vollbild.
///
/// **Unten, unter beiden Reitern: «In die Mappe legen»** (`Mappenknopf`, Blätter «Main» und
/// «MainHoch»). Seit dem 23.09.2026 hier und nur hier — vorher sass er in der
/// Verbindungszeile, weil das Seitenfeld noch nirgends hing.
///
/// Am ganzen Seitenfeld sitzt der `Laufwaechter`: Solange die HomeStation rechnet, fragt er
/// öfter nach und holt am Ende die Mappe — auch wenn gerade die Ebenen dastehen.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
struct Seitentafel: View {
    @ObservedObject var wahl: Leistenwahl
    @ObservedObject var mappe: Bildbandstand
    @ObservedObject var verbindung: Verbindungsstand

    init(wahl: Leistenwahl = .gemeinsam, mappe: Bildbandstand = .gemeinsam,
         verbindung: Verbindungsstand = .gemeinsam) {
        self.wahl = wahl
        self.mappe = mappe
        self.verbindung = verbindung
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            wasDieSkizzeTut
            umschalter
            // ES RECHNET, UND DIE MAPPE IST ZU: Der Knopf «Lauf abbrechen» sitzt in der Mappe.
            // Damit er nicht unerreichbar hinter dem anderen Reiter liegt, steht hier der Weg.
            if wahl.seitenfeld == .ebenen, verbindung.laufstand?.laeuft == true {
                Button("Es rechnet auf der HomeStation — zum Lauf") { wahl.seitenfeld = .mappe }
                    .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil, hoehe: 44))
            }
            switch wahl.seitenfeld {
            case .ebenen:
                Ebenentafel(stand: Zeichenstand.gemeinsam)
            case .mappe:
                Mappentafel(mappe: mappe, verbindung: verbindung)
            }
            Mappenknopf(stand: verbindung)
                .padding(.top, 6)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .foregroundStyle(Zeichenblatt.schrift)
        .modifier(Laufwaechter(verbindung: verbindung, mappe: mappe))
    }

    private var wasDieSkizzeTut: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Was die Skizze tut")
            HStack(spacing: 8) {
                knopf(.pruefen, "Prüfen")
                knopf(.entwerfen, "Entwerfen")
            }
            Text(mappe.bestellart == .entwerfen
                 ? "Beim Entwerfen ist erfundenes Volumen der Zweck: schnell gerechnet, ohne Geometrieprüfung, das Zeichen ist blau."
                 : "Beim Prüfen ist erfundenes Volumen ein Fehler: Die Geometrie wird geprüft, das Bild trägt sein Urteil.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private func knopf(_ l: Bildlesart, _ titel: String) -> some View {
        let an = mappe.bestellart == l
        return Button(titel) { mappe.bestellart = l }
            .buttonStyle(Wahlknopfstil(gewaehlt: an, breite: nil, hoehe: 44))
            .accessibilityAddTraits(an ? .isSelected : [])
    }

    private var umschalter: some View {
        HStack(spacing: 8) {
            ForEach(Seitenfeldwahl.allCases) { w in
                Button(w.name) { wahl.seitenfeld = w }
                    .buttonStyle(Wahlknopfstil(gewaehlt: wahl.seitenfeld == w, breite: nil,
                                               hoehe: 44))
                    .accessibilityAddTraits(wahl.seitenfeld == w ? .isSelected : [])
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Seitenfeld")
    }
}
