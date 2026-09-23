import SwiftUI

/// Die Ebenen, von oben nach unten — **jede eine Variante** (Entscheid Nr. 7).
///
/// Anlegen, ein- und ausblenden, Deckkraft, umbenennen, umstapeln, löschen. Was davon
/// mitgeht, sagt die Tafel in einem Satz, und der Satz kommt aus derselben Regel wie die
/// Ausgabe (`Ebenenstapel.plan`) — *eine Tafel, die etwas anderes zeigt, als hinausgeht,
/// wäre derselbe Fehler wie die Ausgabe selbst.*
///
/// **Die Unterlage steht als unterste Zeile** (seit dem 23.09.2026, Blatt «Main»: «Bild aus
/// Lauf 07» unter den Ebenen): ein- und ausblendbar und entfernbar, aber **nicht wählbar** —
/// sie ist keine Ebene (Kern, `Blattunterlage`), auf sie wird nicht gezeichnet und nicht
/// radiert, und sie zählt nicht zu «Geht mit». Darunter ein Satz, was mit ihr gerechnet
/// wird (`Blattunterlage.tafelsatz`, aus dem Kern mit Probe).
///
/// **Eine eigenständige Ansicht, ohne Rahmen:** kein Rollbereich, kein Rand, kein Grund.
/// Die bringt mit, wer sie hinlegt — das Seitenfeld des Arbeitsplatzes
/// (`ScrollView { seitenfeld.padding(20) }` mit dem Grund der Leiste) oder die
/// Zeichenfläche selbst, wenn sie ihre eigene Tafel zeigt. Mit eigenem Rollbereich stünde
/// im Seitenfeld ein Rollbereich im Rollbereich (Befund Durchsicht A, 22.09.2026).
struct Ebenentafel: View {
    @ObservedObject var stand: Zeichenstand

    @State private var umbenennen: UUID?
    @State private var neuerName = ""
    @State private var loeschen: UUID?

    init(stand: Zeichenstand? = nil) {
        self.stand = stand ?? Zeichenstand.gemeinsam
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            kopf
            ForEach(stand.stapel.vonObenGesehen) { ebene in
                zeile(ebene)
            }
            if let u = stand.stapel.unterlage {
                unterlagenzeile(u)
            }
            if !stand.stapel.kannAnlegen {
                leise("Höchstens \(Ebenenstapel.hoechstensEbenen) Ebenen.")
            }
            aktiveEbene
            Text(mitgehSatz)
                .font(Schrift.text(13, .semibold))
                .foregroundStyle(Zeichenblatt.schrift)
                .padding(.top, 4)
            if let satz = variantenSatz {
                leise(satz)
            }
            if let satz = ungewissSatz {
                leise(satz)
            }
            leise(Blattunterlage.tafelsatz(stand.stapel.unterlage))
            leise("Jede Ebene ist eine Variante. Gerechnet wird, was sichtbar ist — "
                  + "unsichtbare Ebenen gehen nicht mit.")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .alert("Ebene umbenennen", isPresented: umbenennenOffen) {
            TextField("Name", text: $neuerName)
            Button("Übernehmen") {
                if let id = umbenennen { stand.benenneEbene(id, neuerName) }
                umbenennen = nil
            }
            Button("Abbrechen", role: .cancel) { umbenennen = nil }
        } message: {
            Text("Ein leerer Name wird nicht übernommen.")
        }
        .confirmationDialog("Ebene löschen?", isPresented: loeschenOffen,
                            titleVisibility: .visible) {
            Button("Löschen", role: .destructive) {
                if let id = loeschen { stand.entferneEbene(id) }
                loeschen = nil
            }
            Button("Abbrechen", role: .cancel) { loeschen = nil }
        } message: {
            Text("Die Striche darauf sind weg. «Zurück» beginnt danach von vorn und kann "
                 + "das Löschen nicht zurücknehmen.")
        }
    }

    // ------------------------------------------------------------------ Teile

    private var kopf: some View {
        HStack(spacing: 10) {
            Abschnittstitel(text: "Ebenen")
            Spacer()
            Button {
                stand.legeEbeneAn()
            } label: {
                Image(systemName: "plus")
                    .font(.system(size: 18, weight: .semibold))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: 44, hoehe: 44))
            .disabled(!stand.stapel.kannAnlegen)
            .accessibilityLabel("Ebene hinzufügen")
        }
    }

    private func zeile(_ ebene: Ebene) -> some View {
        let aktiv = ebene.id == stand.stapel.aktiv
        return HStack(spacing: 10) {
            Button {
                stand.setzeSichtbar(ebene.id, !ebene.sichtbar)
            } label: {
                Image(systemName: ebene.sichtbar ? "checkmark.square.fill" : "square")
                    .font(.system(size: 22))
                    .foregroundStyle(ebene.sichtbar ? Zeichenblatt.gewaehltRand
                                                    : Zeichenblatt.leise)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(ebene.sichtbar ? "\(ebene.name) ausblenden"
                                               : "\(ebene.name) einblenden")

            Button {
                stand.waehleEbene(ebene.id)
            } label: {
                HStack(spacing: 10) {
                    Text(ebene.name)
                        .font(Schrift.text(15, aktiv ? .semibold : .regular))
                        .foregroundStyle(ebene.sichtbar ? Zeichenblatt.schrift
                                                        : Zeichenblatt.leise)
                        .lineLimit(1)
                    Spacer(minLength: 4)
                    Text(zustand(ebene))
                        .font(Schrift.zahl(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                .frame(minHeight: 44)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel("\(ebene.name), \(zustand(ebene))")
            .accessibilityAddTraits(aktiv ? .isSelected : [])
        }
        .padding(.horizontal, 6)
        .frame(minHeight: 46)
        .background(RoundedRectangle(cornerRadius: 10)
            .fill(aktiv ? Zeichenblatt.gewaehltGrund : Color.clear))
        .overlay(RoundedRectangle(cornerRadius: 10)
            .strokeBorder(aktiv ? Zeichenblatt.gewaehltRand : Zeichenblatt.linie,
                          lineWidth: 1))
    }

    /// Die Zeile der Unterlage, zuunterst. **Kein Knopf zum Wählen** — ein Tipp auf den Namen
    /// täte nichts, und ein Knopf, der nichts tut, sieht aus wie ein kaputter. Die Deckkraft
    /// ist fest: Der Server legt die Skizze auf das ganze Bild, nicht auf ein blasses.
    private func unterlagenzeile(_ u: Blattunterlage) -> some View {
        HStack(spacing: 10) {
            Button {
                stand.setzeUnterlageSichtbar(!u.sichtbar)
            } label: {
                Image(systemName: u.sichtbar ? "checkmark.square.fill" : "square")
                    .font(.system(size: 22))
                    .foregroundStyle(u.sichtbar ? Zeichenblatt.gewaehltRand : Zeichenblatt.leise)
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(u.sichtbar ? "Unterlage \(u.titel) ausblenden"
                                           : "Unterlage \(u.titel) einblenden")

            Image(systemName: "photo")
                .font(.system(size: 15))
                .foregroundStyle(Zeichenblatt.leise)
                .accessibilityHidden(true)
            Text(u.titel)
                .font(Schrift.text(15))
                .foregroundStyle(u.sichtbar ? Zeichenblatt.schrift : Zeichenblatt.leise)
                .lineLimit(1)
            Spacer(minLength: 4)
            Text(unterlagenzustand(u))
                .font(Schrift.zahl(13))
                .foregroundStyle(Zeichenblatt.leise)

            Button {
                stand.entferneUnterlage()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 15))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: 44, hoehe: 44))
            .accessibilityLabel("Unterlage \(u.titel) entfernen")
        }
        .padding(.horizontal, 6)
        .frame(minHeight: 46)
        .overlay(RoundedRectangle(cornerRadius: 10)
            .strokeBorder(Zeichenblatt.linie, style: StrokeStyle(lineWidth: 1, dash: [4, 3])))
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Unterlage \(u.titel), \(unterlagenzustand(u))")
    }

    /// Neben dem Namen der Unterlage: ausgeblendet, gestreckt, oder nur «Unterlage». Ob sie
    /// gestreckt ist, sagt der Kern (`Blattunterlage.gestreckt`); nicht bekannt steht als «?».
    private func unterlagenzustand(_ u: Blattunterlage) -> String {
        if !u.sichtbar { return "ausgeblendet" }
        switch u.gestreckt {
        case .some(true): return "gestreckt"
        case .some(false): return "Unterlage"
        case .none: return "Unterlage ?"
        }
    }

    /// Was neben dem Namen steht. «leer» ist **kein** «0 %»: Eine leere Ebene ist nicht
    /// durchsichtig, sondern unbezeichnet — und geht darum nicht mit.
    private func zustand(_ ebene: Ebene) -> String {
        if !ebene.sichtbar { return "ausgeblendet" }
        if ebene.istLeer { return "leer" }
        return "\(Int((ebene.deckkraft * 100).rounded())) %"
    }

    /// Deckkraft und Handgriffe der gewählten Ebene.
    private var aktiveEbene: some View {
        let ebene = stand.stapel.aktiveEbene
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Deckkraft")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                Spacer()
                Text("\(Int((ebene.deckkraft * 100).rounded())) %")
                    .font(Schrift.zahl(13))
                    .foregroundStyle(Zeichenblatt.leise)
            }
            Slider(value: Binding(get: { ebene.deckkraft },
                                  set: { stand.setzeDeckkraft(ebene.id, $0) }),
                   in: Ebenenstapel.mindestDeckkraft...1)
                .tint(Zeichenblatt.gewaehltRand)
                .accessibilityLabel("Deckkraft von \(ebene.name)")
            HStack(spacing: 10) {
                handgriff("chevron.up", "\(ebene.name) nach oben") {
                    stand.verschiebeEbene(ebene.id, nachOben: true)
                }
                .disabled(stand.stapel.ebenen.last?.id == ebene.id)
                handgriff("chevron.down", "\(ebene.name) nach unten") {
                    stand.verschiebeEbene(ebene.id, nachOben: false)
                }
                .disabled(stand.stapel.ebenen.first?.id == ebene.id)
                handgriff("character.cursor.ibeam", "\(ebene.name) umbenennen") {
                    neuerName = ebene.name
                    umbenennen = ebene.id
                }
                handgriff("trash", "\(ebene.name) löschen") {
                    loeschen = ebene.id
                }
                .disabled(!stand.stapel.kannEntfernen)
            }
        }
        .padding(.top, 6)
    }

    private func handgriff(_ symbol: String, _ name: String,
                           _ tu: @escaping () -> Void) -> some View {
        Button(action: tu) {
            Image(systemName: symbol)
                .font(.system(size: 18))
        }
        .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: 44, hoehe: 44))
        .accessibilityLabel(name)
    }

    private func leise(_ satz: String) -> some View {
        Text(satz)
            .font(Schrift.text(13))
            .foregroundStyle(Zeichenblatt.leise)
            .fixedSize(horizontal: false, vertical: true)
    }

    // ------------------------------------------------------------ was mitgeht

    /// Der Satz darüber, was als eine Skizze hinausginge — aus derselben Regel wie die
    /// Ausgabe.
    private var mitgehSatz: String {
        let alle = stand.stapel.ebenen.count
        switch stand.stapel.plan(.eineSkizze) {
        case .teile(let teile):
            let mit = teile.reduce(0) { $0 + $1.ebenen.count }
            return "Geht mit: \(mit) von \(alle) \(alle == 1 ? "Ebene" : "Ebenen")."
        case .nichtsGezeichnet(let versteckt):
            if versteckt == 0 { return "Noch nichts gezeichnet — es geht nichts mit." }
            return "Nichts Sichtbares gezeichnet. \(versteckt) ausgeblendete "
                + "\(versteckt == 1 ? "Ebene trägt" : "Ebenen tragen") Striche; "
                + "sie gehen nicht mit."
        case .zuVieleVarianten(let sichtbar, let hoechstens):
            return "\(sichtbar) sichtbare Ebenen, höchstens \(hoechstens) gehen."
        }
    }

    /// Nur, wenn sich das Bild einer Ebene nach dem Radieren nicht lesen liess
    /// (`Ebene.deckungUngewiss`, Befund Durchsicht 22.09.2026). Dann zählen ihre Striche,
    /// und sie geht mit — auch wenn sie leer aussieht. Das steht hier, statt dass die Tafel
    /// still «bezeichnet» zeigt. Ob der Fall am Gerät vorkommt, ist ungeprüft.
    private var ungewissSatz: String? {
        let namen = stand.stapel.vonObenGesehen
            .filter { $0.deckungUngewiss && $0.gehtMit }
            .map { "«\($0.name)»" }
        guard !namen.isEmpty else { return nil }
        let wer = namen.joined(separator: ", ")
        let satz = "Bei \(wer) liess sich nach dem Radieren nicht prüfen, ob noch etwas zu "
            + "sehen ist."
        if namen.count == 1 { return satz + " Sie geht mit, weil sie Striche trägt." }
        return satz + " Sie gehen mit, weil sie Striche tragen."
    }

    /// Nur, wenn es als Varianten nicht ginge.
    private var variantenSatz: String? {
        if case .zuVieleVarianten(let sichtbar, let hoechstens) =
            stand.stapel.plan(.ebenenAlsVarianten) {
            return "Als Varianten gehen höchstens \(hoechstens) — sichtbar und bezeichnet "
                + "sind \(sichtbar). Eine ausblenden, oder als eine Skizze senden."
        }
        return nil
    }

    // ------------------------------------------------------------ Dialoge

    private var umbenennenOffen: Binding<Bool> {
        Binding(get: { umbenennen != nil }, set: { if !$0 { umbenennen = nil } })
    }

    private var loeschenOffen: Binding<Bool> {
        Binding(get: { loeschen != nil }, set: { if !$0 { loeschen = nil } })
    }
}
