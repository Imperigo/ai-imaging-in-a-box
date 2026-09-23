import SwiftUI

/// Die Übergabe als Bewegung: **eine** Marke auf einem Faden vom iPad zur HomeStation
/// (Blatt «Ein Faden, zwei Geräte», Entscheide vom 21.09.2026).
///
/// **Wo die Marke steht, rechnet der Kern** (`Flugbahn`, geprüft in `ParkfachTests`); diese
/// Ansicht zeichnet nur. Die vier Regeln, wie sie hier ankommen:
///
/// 1. *Bewegt sich etwas, ist etwas unterwegs.* Die Ansicht gibt es nur, solange eine Skizze
///    **reist** (`Verbindungsstand.uebergabe`): vom Vorspiel an bis zum Einrasten oder
///    Zurückfallen. Im Flug folgt der Ort den gezählten Bytes. **Das Vorspiel kommt vor dem
///    Tor** (`Flugbahn.vorspiel`: ablegen 220 ms, abheben 180 ms — beim Abheben wandert die
///    Marke an den Rand des iPads, zum Ziel hin, `Flugbahn.rand`): Bricht das Senden dort ab,
///    geht **nichts** hinaus, und die Marke fällt zurück. Für diese 0,4 s gilt die Regel
///    darum nicht ganz — die Marke bewegt sich, bevor feststeht, dass gesendet wird
///    (Durchsicht der Welle 2b, 23.09.2026; bis dahin stand hier «nur, solange gesendet
///    wird»).
/// 2. *Gleichmässig heisst gezählt.* Ohne Gesamt kein Balken; die Marke atmet an Ort und
///    Stelle (1.8 s) — vom Beginn des Sendens an (`Flugbahn.flugbeginn`), auch wenn nie
///    ein Zählerstand kommt.
/// 3. *Die Animation endet nicht vor der Ankunft.* Vor der Antwort 200 steht die Marke vor
///    dem Ziel; sie rastet erst danach ein (140 ms).
/// 4. *Ein Gegenstand, ein Weg.* Es gibt **eine** Marke mit fester Identität, die ihren
///    Ort ändert — keine zweite, die am Ziel auftaucht.
///
/// **Bewegungsreduktion** (Blatt: *«Die Marke erscheint am Ziel, der Balken bleibt.»*):
/// Während der Übertragung steht die Marke **nirgends** — nicht am iPad, nicht auf dem
/// Faden. Sie erscheint erst mit der Bestätigung, und dann am Ziel; fällt sie zurück,
/// liegt sie auf dem iPad. Balken und Satz bleiben die ganze Zeit. Wo sie steht, rechnet
/// der Kern (`Flugbahn.ortOhneBewegung`, geprüft in
/// `ParkfachTests.testOhneBewegungErscheintDieMarkeErstAmZiel`). Bis zur Durchsicht vom
/// 22.09.2026 stand sie in dieser Lage während der Übertragung am iPad — gegen das Blatt.
/// *Eine Aussage, die nur in der Bewegung steckt, ist für diese Leute keine Aussage.*
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
@MainActor
struct Uebergabestrecke: View {
    let phase: Flugbahn.Phase
    /// Wie das Ziel heisst (Name der HomeStation oder ihre Adresse).
    let ziel: String

    @Environment(\.accessibilityReduceMotion) private var ruhig

    static let marke: CGFloat = 34
    // DIE FARBEN DES FADENS SIND DIE DES ZEICHENBLATTS (#4ea373 / #223028, Blatt «Ein Faden,
    // zwei Geraete») — hier nur benannt, nicht ein zweites Mal als Zahl geschrieben.
    static let gruen = Zeichenblatt.gewaehltRand
    static let markengrund = Zeichenblatt.gewaehltGrund

    private var ort: Double { Flugbahn.ort(phase) }
    private var atmet: Bool { Flugbahn.atmet(phase) && !ruhig }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            GeometryReader { geo in
                let weg = max(geo.size.width - Uebergabestrecke.marke, 0)
                ZStack(alignment: .leading) {
                    // DER FADEN: grau die ganze Strecke, grün so weit, wie die Marke kam.
                    Rectangle()
                        .fill(Zeichenblatt.linie)
                        .frame(height: 1)
                    Rectangle()
                        .fill(Uebergabestrecke.gruen)
                        .frame(width: weg * CGFloat(ort) + Uebergabestrecke.marke / 2, height: 2)
                    markeAnsicht
                        .opacity(markenort == nil ? 0 : 1)
                        .offset(x: weg * CGFloat(markenort ?? 0))
                }
                .frame(height: Uebergabestrecke.marke)
            }
            .frame(height: Uebergabestrecke.marke)
            .animation(ruhig ? nil : Uebergabestrecke.bewegung(phase), value: ort)
            balken
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text("Übergabe an \(ziel)"))
        .accessibilityValue(Text(beschriftung))
    }

    /// Wo die Marke steht — `nil`: nicht gezeigt (nur bei Bewegungsreduktion, unterwegs).
    /// Unsichtbar gemacht, nicht weggenommen: Es bleibt **eine** Marke (Regel 4).
    private var markenort: Double? {
        ruhig ? Flugbahn.ortOhneBewegung(phase) : ort
    }

    /// **Eine** Marke, auch beim Atmen: kein `if`/`else` um zwei Ansichten (SwiftUI baute
    /// sonst beim Wechsel eine neue — zwei Dinge, die sich ähnlich sehen, Regel 4), sondern
    /// dieselbe, deren Uhr nur läuft, solange sie atmet.
    private var markeAnsicht: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: !atmet)) { zeit in
            // ATMEN AN ORT UND STELLE, aus der Uhr gerechnet — kein Vorankommen.
            let t = zeit.date.timeIntervalSinceReferenceDate
            let welle = 0.5 - 0.5 * cos(2 * Double.pi * t / Flugbahn.atem)
            marke.opacity(atmet ? 0.35 + 0.65 * welle : 1)
        }
    }

    private var marke: some View {
        RoundedRectangle(cornerRadius: 9)
            .fill(Uebergabestrecke.markengrund)
            .overlay(RoundedRectangle(cornerRadius: 9)
                .strokeBorder(Uebergabestrecke.gruen, lineWidth: 2))
            .frame(width: Uebergabestrecke.marke, height: Uebergabestrecke.marke)
            .scaleEffect(phase == .ablegen && !ruhig ? 1.25 : 1)
            .animation(ruhig ? nil : .easeOut(duration: Flugbahn.ablegen), value: phase == .ablegen)
    }

    @ViewBuilder
    private var balken: some View {
        HStack(spacing: 10) {
            if let anteil = Flugbahn.anteil(phase) {
                GeometryReader { geo in
                    ZStack(alignment: .leading) {
                        Capsule().fill(Zeichenblatt.linie)
                        Capsule().fill(Uebergabestrecke.gruen)
                            .frame(width: geo.size.width * anteil)
                    }
                }
                .frame(width: 90, height: 5)
            }
            Text(beschriftung)
                .font(Schrift.zahl(11))
                .foregroundStyle(Zeichenblatt.leise)
                .lineLimit(1)
        }
    }

    /// Was unter dem Faden steht — **gezählt, wo gezählt wird; sonst ohne Zahl.**
    private var beschriftung: String {
        switch phase {
        case .ablegen, .abheben:
            return "legt ab …"
        case .flug(let gesendet, let gesamt):
            guard let g = gesamt, g > 0 else { return "unterwegs · nicht gezählt" }
            return "\(Uebergabestrecke.mb(gesendet)) von \(Uebergabestrecke.mb(g)) MB · gezählt"
        case .warten:
            return "alles drüben · wartet auf die Bestätigung"
        case .eingerastet:
            return "in der Mappe · noch nicht gerechnet"
        case .zurueck:
            return "nicht angekommen · liegt auf dem iPad, siehe Parkfach"
        }
    }

    static func mb(_ bytes: Int64) -> String {
        String(format: "%.1f", Double(bytes) / 1_000_000)
    }

    /// Die Zeiten des Entwurfs. Der Flug gleitet nur zwischen zwei Zählerständen.
    static func bewegung(_ phase: Flugbahn.Phase) -> Animation {
        switch phase {
        case .ablegen: return .easeOut(duration: Flugbahn.ablegen)
        case .abheben: return .easeOut(duration: Flugbahn.abheben)
        case .flug, .warten: return .linear(duration: 0.2)
        case .eingerastet: return .easeOut(duration: Flugbahn.einrasten)
        // ZURUECK OHNE SCHWUNG: Die Bewegung hoert auf der Stelle auf, die Marke faellt.
        case .zurueck: return .easeIn(duration: Flugbahn.abheben)
        }
    }
}
