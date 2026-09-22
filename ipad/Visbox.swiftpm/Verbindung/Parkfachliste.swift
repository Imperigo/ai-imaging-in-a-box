import SwiftUI
import UIKit

/// Was im Parkfach liegt — **jede Skizze mit ihrem Zustand, und was nicht ankam, mit
/// seinem Grund.**
///
/// Eine abgewiesene Skizze verschwindet nicht still: Das entscheidet hier ein Mensch —
/// «Noch einmal senden» oder «Verwerfen» (`Kern/Parkfach.swift`).
///
/// **Eine ungewisse geht seit dem 22.09.2026 von selbst noch einmal**, wenn ihr Schlüssel
/// gegen Doppelsendung mitging (`Parkeintrag.gehtVonSelbst`): Die HomeStation erkennt ihn
/// und legt keine zweite Datei an — ausser sie wurde dazwischen neu gestartet. Erst wenn
/// das nicht bekannt ist oder zu oft nichts Klares zurückkam, entscheidet ein Mensch.
/// Der Satz unter der Skizze sagt, welcher Fall es ist.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
@MainActor
struct Parkfachliste: View {
    @ObservedObject var stand: Verbindungsstand
    @Environment(\.dismiss) private var schliessen
    @State private var zuVerwerfen: Parkeintrag?

    var body: some View {
        NavigationStack {
            List {
                if let s = stand.fachSatz {
                    Text(s).font(Schrift.text(14))
                }
                if stand.fach.isEmpty {
                    Text("Das Parkfach ist leer.")
                        .font(Schrift.text(14))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                // DIE NEUESTE OBEN — sie ist die, nach der man sucht.
                ForEach(Array(stand.fach.reversed())) { e in zeile(e) }
            }
            .navigationTitle("Parkfach")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Fertig") { schliessen() }
                }
            }
            .confirmationDialog("Diese Skizze verwerfen?",
                                isPresented: Binding(get: { zuVerwerfen != nil },
                                                     set: { if !$0 { zuVerwerfen = nil } }),
                                titleVisibility: .visible) {
                Button("Verwerfen", role: .destructive) {
                    if let e = zuVerwerfen { stand.verwirf(e) }
                    zuVerwerfen = nil
                }
                Button("Behalten", role: .cancel) { zuVerwerfen = nil }
            } message: {
                Text("Sie ist danach weder auf dem iPad noch — falls sie nie ankam — drüben.")
            }
        }
    }

    private func zeile(_ e: Parkeintrag) -> some View {
        HStack(alignment: .top, spacing: 14) {
            vorschau(e)
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 8) {
                    Text(e.zustand.wort.uppercased())
                        .font(Schrift.abschnitt)
                        .tracking(0.9)
                        .foregroundStyle(e.zustand == .geparkt || e.zustand == .unterwegs
                                         ? Zeichenblatt.schrift : Zeichenblatt.leise)
                    Text(Parkfachliste.zeit.string(from: e.erstellt))
                        .font(Schrift.zahl(12))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                if let name = e.name {
                    Text(name).font(Schrift.text(14))
                }
                if let erklaerung = Parkfachliste.erklaerung(e) {
                    Text(erklaerung)
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                handgriffe(e)
            }
        }
        .padding(.vertical, 6)
    }

    @ViewBuilder
    private func vorschau(_ e: Parkeintrag) -> some View {
        if let daten = stand.zeichnung(e), let bild = UIImage(data: daten) {
            Image(uiImage: bild)
                .resizable()
                .scaledToFit()
                .frame(width: 96, height: 64)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 6))
                .accessibilityHidden(true)
        } else {
            // ANGEKOMMEN: Die Zeichnung liegt drueben, nicht mehr hier — und das steht da,
            // statt eines leeren Rahmens, der aussaehe wie ein Fehler.
            Text(Parkfachliste.istAngekommen(e) ? "drüben" : "fehlt")
                .font(Schrift.zahl(11))
                .foregroundStyle(Zeichenblatt.leise)
                .frame(width: 96, height: 64)
                .background(RoundedRectangle(cornerRadius: 6).strokeBorder(Zeichenblatt.linie))
        }
    }

    @ViewBuilder
    private func handgriffe(_ e: Parkeintrag) -> some View {
        // 60 PT JE ZIEL (Blatt «Zeichen»), nicht 44 — die Vorgabe des Wahlknopfstils. Und
        // `fixedSize`, weil `breite: nil` dort «so breit wie moeglich» heisst.
        if e.brauchtEntscheid {
            HStack(spacing: Zeichenblatt.abstand) {
                Button("Noch einmal senden") { stand.nochEinmal(e) }
                    .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                    .fixedSize()
                Button("Verwerfen") { zuVerwerfen = e }
                    .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                    .fixedSize()
            }
        } else if e.zustand != .unterwegs {
            Button("Verwerfen") { zuVerwerfen = e }
                .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                .fixedSize()
        }
    }

    /// Der Satz unter einer Skizze — **der Grund, wo es einen gibt.**
    static func erklaerung(_ e: Parkeintrag) -> String? {
        switch e.zustand {
        case .geparkt:
            return e.letzterGrund.map { "Wartet. Zuletzt: \($0)" } ?? "Wartet auf die HomeStation."
        case .unterwegs:
            return "Wird gerade gesendet."
        case .angekommen(let skizze, let hinweis):
            let name = skizze.map { "Drüben als \($0)." } ?? "Drüben abgelegt."
            return [name, hinweis].compactMap { $0 }.joined(separator: " ")
        case .abgewiesen(let grund, let code):
            return code.map { "Abgewiesen (\($0)): \(grund)" } ?? "Abgewiesen: \(grund)"
        case .ungewiss(let grund):
            if e.gehtVonSelbst {
                return grund + " Sie geht mit demselben Schlüssel von selbst noch einmal; "
                    + "drüben entsteht dabei keine zweite Datei — ausser die HomeStation wurde "
                    + "inzwischen neu gestartet."
            }
            if e.schluesselGesendet == nil {
                return grund + " Ob sie mit dem Schlüssel gegen Doppelsendung hinausging, ist "
                    + "nicht bekannt — noch einmal senden kann sie drüben verdoppeln."
            }
            return grund + " Schon \(e.versuche)-mal ohne klare Antwort. Noch einmal senden geht "
                + "mit demselben Schlüssel; nach einem Neustart der HomeStation kann drüben "
                + "eine zweite Datei entstehen."
        }
    }

    static func istAngekommen(_ e: Parkeintrag) -> Bool {
        if case .angekommen = e.zustand { return true }
        return false
    }

    private static let zeit: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale(identifier: "de_CH")
        f.dateFormat = "dd.MM.yyyy · HH:mm"
        return f
    }()
}
