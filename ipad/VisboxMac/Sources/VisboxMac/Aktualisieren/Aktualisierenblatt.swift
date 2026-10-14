import SwiftUI
import VisboxKern

/// Das Blatt «Aktualisieren» (Blatt 18 der Entwurfsflaeche, Owner-Entscheid 84, 13.10.2026):
/// Nummer, Neuerungen aus dem Fassungsblatt, der Hinweis zur Behelfs-Unterschrift, dann
/// Fortschritt, Abgleich der Pruefsumme, Ersetzen und der Neustart **von selbst** (Entscheid
/// 87: der Klick auf den Knopf hat das Laden schon gestartet). «Laden und ersetzen» bleibt nur
/// für «Erneut versuchen» nach einem Fehler; «Neu starten» nur, falls der Neustart hängt.
///
/// **Zeigt nur an.** Die Saetze und Phasen stehen im Kern (`Aktualisierung`,
/// `Aktualisierungsphase`), das Tun im `Fassungswaechter`.
///
/// *Gebaut, am Geraet unbestaetigt (13.10.2026).*
struct Aktualisierenblatt: View {
    @ObservedObject var waechter: Fassungswaechter
    let schliessen: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            if let freigabe = waechter.angebot {
                inhalt(freigabe)
            } else {
                Text("Diese Fassung ist die neueste.")
                HStack { Spacer(); Button("Schliessen", action: schliessen) }
            }
        }
        .padding(24)
        .frame(width: 540)
        .background(Startfarbe.flaeche)
        .foregroundStyle(Startfarbe.text)
        // OFFEN BLEIBEN, SOLANGE GEARBEITET WIRD: Ein zugeklapptes Blatt hielte das Ersetzen
        // nicht an, aber es verbaerge, wie es ausgeht.
        .interactiveDismissDisabled(arbeitet)
    }

    private var arbeitet: Bool {
        switch waechter.phase {
        case .laedt, .prueft, .ersetzt: return true
        default: return false
        }
    }

    @ViewBuilder
    private func inhalt(_ freigabe: Freigabe) -> some View {
        Text(Aktualisierung.titel(freigabe.nummer))
            .font(.title2.weight(.semibold))
        if let laufend = waechter.laufend {
            Text(Aktualisierung.untertitel(laufend: laufend))
                .foregroundStyle(Startfarbe.leise)
        }

        let neuerungen = Aktualisierung.neuerungen(aus: freigabe.begleittext)
        if neuerungen.isEmpty {
            if let seite = freigabe.seite {
                Link("Neuerungen auf GitHub lesen", destination: seite)
            }
        } else {
            ScrollView {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(Array(neuerungen.enumerated()), id: \.offset) { _, zeile in
                        HStack(alignment: .firstTextBaseline, spacing: 8) {
                            Text("•").foregroundStyle(Startfarbe.gruenText)
                            Text(Self.auszeichnung(zeile))
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxHeight: 240)
        }

        Text(Aktualisierung.behelfsHinweis)
            .font(.callout)
            .foregroundStyle(Startfarbe.leise)
            .fixedSize(horizontal: false, vertical: true)

        stand

        HStack {
            Spacer()
            knoepfe
        }
    }

    @ViewBuilder
    private var stand: some View {
        switch waechter.phase {
        case .angeboten:
            EmptyView()
        case .laedt(let anteil):
            if let anteil {
                ProgressView(value: anteil) { Text(waechter.phase.satz) }
            } else {
                ProgressView { Text(waechter.phase.satz) }
            }
        case .prueft, .ersetzt:
            ProgressView { Text(waechter.phase.satz) }
        case .fertig:
            Text(waechter.phase.satz).foregroundStyle(Startfarbe.gruenText)
        case .gescheitert:
            Text(waechter.phase.satz)
                .foregroundStyle(Startfarbe.rot)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    @ViewBuilder
    private var knoepfe: some View {
        switch waechter.phase {
        case .angeboten:
            Button(Aktualisierung.spaeter, action: schliessen)
                .keyboardShortcut(.cancelAction)
            Button(Aktualisierung.ladenUndErsetzen) { waechter.ladeUndErsetze() }
                .keyboardShortcut(.defaultAction)
        case .laedt, .prueft, .ersetzt:
            Button(Aktualisierung.spaeter) {}
                .disabled(true)
        case .fertig:
            // DER NEUSTART LAEUFT VON SELBST (Entscheid 87); der Knopf ist der Notweg.
            Button(Aktualisierung.neuStarten) { waechter.starteNeu() }
                .keyboardShortcut(.defaultAction)
        case .gescheitert:
            Button("Schliessen") {
                waechter.zuruecksetzen()
                schliessen()
            }
            .keyboardShortcut(.cancelAction)
            if Umzug.istVersteckt {
                // ENTSCHEID 89: statt «Erneut versuchen» (das gleich wieder scheiterte) der Umzug.
                Button(Aktualisierung.umzugKnopf) {
                    Umzug.zieheUndStarteNeu { _ in }
                }
                .keyboardShortcut(.defaultAction)
            } else {
                Button("Erneut versuchen") {
                    waechter.zuruecksetzen()
                    waechter.ladeUndErsetze()
                }
            }
        }
    }

    /// Fett und Code aus dem Fassungsblatt (`**…**`, `` `…` ``) als Auszeichnung statt als
    /// Sternchen. Nur Zeilenauszeichnung — Tabellen und Ueberschriften liest der Kern vorher aus.
    private static func auszeichnung(_ zeile: String) -> AttributedString {
        (try? AttributedString(
            markdown: zeile,
            options: .init(interpretedSyntax: .inlineOnlyPreservingWhitespace)))
            ?? AttributedString(zeile)
    }
}
