import SwiftUI

/// Die Zeichenfläche: das Blatt, «Zurück»/«Vor» mit Zähler, die Stiftfarbe und die
/// Ebenen (Entscheide Nr. 2–8, Blätter «Main» und «MainHoch»).
///
/// Werkzeug und Strichstärke wählt die Leiste (`Leistenwahl`); hier wird nur gelesen,
/// was sie gewählt hat. Die Regeln stehen im Kern (`Kern/Ebenen.swift`), die Striche und
/// die PNG-Ausgabe in `Zeichenstand` — **die Schnittstelle für das Senden ist
/// `Zeichenstand.gemeinsam.skizzenpaket(_:)`** (die PNG und die Unterlage, seit dem
/// 23.09.2026). Unter den Ebenen liegt, wenn gelegt, die Unterlage (`Leinwandstapel`).
///
/// **Wo die Ebenentafel steht, entscheidet, wer die Zeichenfläche einsetzt.**
///
/// * `eigeneTafel: false` — **so setzt `Startansicht` sie heute ein** (Stand 23.09.2026):
///   nur Blatt und Werkzeugzeile. Die Ebenentafel legt `Seitentafel` in das Seitenfeld
///   des Arbeitsplatzes (`Ebenentafel(stand: Zeichenstand.gemeinsam)`, umschaltbar mit der
///   Mappe): `Arbeitsplatz { Zeichenflaeche(eigeneTafel: false) } seitenfeld: {
///   Seitentafel(wahl: wahl) }`. Sonst stünden zwei Seitenfelder nebeneinander (Befund
///   Durchsicht A, 22.09.2026).
/// * `eigeneTafel: true` (die Vorgabe des Aufrufs, heute von keiner Stelle genutzt): Die
///   Fläche bringt die Tafel selbst mit — im Querformat rechts, im Hochformat darunter
///   (Entscheid Nr. 1), so breit wie das Seitenfeld des Arbeitsplatzes
///   (`Zeichenblatt.seitenfeldBreite`). Im Vollbild (`Leistenwahl.vollbild`) fällt sie
///   weg, wie das Seitenfeld dort.
struct Zeichenflaeche: View {
    @ObservedObject var stand: Zeichenstand
    @ObservedObject var wahl: Leistenwahl
    private let eigeneTafel: Bool

    init(stand: Zeichenstand? = nil, eigeneTafel: Bool = true) {
        let s = stand ?? Zeichenstand.gemeinsam
        self.stand = s
        self.wahl = s.leistenwahl
        self.eigeneTafel = eigeneTafel
    }

    var body: some View {
        GeometryReader { flaeche in
            let quer = flaeche.size.width >= flaeche.size.height
            // EINE ANORDNUNG, DIE SICH NUR UMLEGT — kein `if quer { HStack } else { VStack }`.
            // Befund Durchsicht A (22.09.2026): Mit zwei Zweigen war das Blatt nach dem Drehen
            // eine andere Ansicht; SwiftUI baute Leinwand, Koordinator und alle PencilKit-
            // Flächen neu, und der gemeinsame `UndoManager` hielt die Schritte der alten —
            // «Zurück» wirkte unsichtbar, der Zähler zählte trotzdem. `AnyLayout` wechselt
            // nur die Anordnung; die Kinder bleiben dieselben. Was trotzdem neu gebaut wird,
            // räumt `Zeichenleinwand.dismantleUIView` ab. Beides am Gerät unbestätigt.
            let anordnung = quer ? AnyLayout(HStackLayout(spacing: 0))
                                 : AnyLayout(VStackLayout(spacing: 0))
            anordnung {
                buehne
                if eigeneTafel && !wahl.vollbild {
                    trennlinie
                        .frame(width: quer ? 1 : nil, height: quer ? nil : 1)
                    ScrollView(.vertical, showsIndicators: false) {
                        Ebenentafel(stand: stand).padding(20)
                    }
                    .background(Zeichenblatt.leiste)
                    // Querformat: die Breite des Seitenfelds. Hochformat: 300 pt, dieselbe
                    // Höhe, die `Arbeitsplatzanordnung` dem Seitenfeld dort gibt.
                    .frame(width: quer ? Zeichenblatt.seitenfeldBreite : nil,
                           height: quer ? nil : 300)
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
                Abschnittstitel(text: blatttitel)
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

    /// «Skizze über Lauf 07 · Variante A» (Blatt «Main»: «Skizze über Lauf 07») — **über**
    /// nur, solange die Unterlage sichtbar ist: Ausgeblendet geht sie nicht mit (Kern,
    /// `Unterlagenangabe`), und der Titel soll nicht versprechen, was nicht gerechnet wird.
    private var blatttitel: String {
        let ebene = stand.stapel.aktiveEbene.name
        if let u = stand.stapel.unterlage, u.sichtbar {
            return "Skizze über \(u.titel) · \(ebene)"
        }
        return "Skizze · \(ebene)"
    }

    /// Die gewählte Ebene ist ausgeblendet — dann wird nicht gezeichnet, und das steht da.
    /// *Ein Stift, der nichts tut, ohne dass es gesagt wird, sieht aus wie ein kaputter.*
    ///
    /// **Der Satz sagt nur, was sicher ist** (Durchsicht, 22.09.2026): Die Ebene ist
    /// ausgeblendet, und auf ihr wird nicht gezeichnet — beides folgt aus der Regel des
    /// Kerns (`aktiveIstZeichenbar`). Dass der Finger dort weiter schiebt und zoomt
    /// (`Leinwand.inhaltVerdeckt`), ist am Gerät unbestätigt und steht darum nicht da.
    ///
    /// **Das Feld fängt keine Finger ab, ausser am Knopf:** Text und Grund lassen
    /// Berührungen durch (`allowsHitTesting(false)`), damit das Blatt auch dort zu schieben
    /// bleibt, wo der Hinweis liegt. Gebaut, nicht übersetzt, am Gerät unbestätigt.
    private var ausgeblendetHinweis: some View {
        VStack(spacing: 12) {
            Text("«\(stand.stapel.aktiveEbene.name)» ist ausgeblendet.")
                .font(Schrift.text(15, .semibold))
                .allowsHitTesting(false)
            Text("Auf eine ausgeblendete Ebene wird nicht gezeichnet.")
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
                .multilineTextAlignment(.center)
                .allowsHitTesting(false)
            Button("Einblenden") {
                stand.setzeSichtbar(stand.stapel.aktiv, true)
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: 160, hoehe: 44))
        }
        .foregroundStyle(Zeichenblatt.schrift)
        .padding(20)
        .background(RoundedRectangle(cornerRadius: 12).fill(Zeichenblatt.feld)
            .allowsHitTesting(false))
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
