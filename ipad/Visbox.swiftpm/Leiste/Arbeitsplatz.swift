import SwiftUI

/// Wie das iPad gehalten wird — abgelesen an der Fläche, die die App wirklich hat.
///
/// **Nicht an der Grössenklasse.** Auf dem iPad ist sie im Hoch- und im Querformat
/// dieselbe («regular»), sie unterscheidet die beiden Haltungen also nicht. Breiter als
/// hoch heisst quer — auch in der geteilten Ansicht, wo die App nur einen Teil des
/// Schirms hat und die Haltung des Geräts nichts über ihre eigene Fläche sagt.
enum Haltung {
    case quer
    case hoch

    init(groesse: CGSize) {
        self = groesse.width > groesse.height ? .quer : .hoch
    }
}

/// Der Arbeitsplatz: Leiste, Mitte und Seitenfeld — **eigene Anordnung je Haltung,
/// derselbe Inhalt** (Entscheid 1).
///
/// * **Querformat** (Blatt «Main»): Leiste senkrecht am Rand, Mitte, Seitenfeld 340 pt.
///   «Auf die andere Seite» spiegelt die ganze Reihe (Entscheid 9) — die Leiste wandert
///   zur anderen Hand, das Seitenfeld auf die freie Seite.
/// * **Hochformat** (Blatt «MainHoch»): Mitte oben, Leiste waagrecht darunter in
///   Daumenreichweite, Seitenfeld unten. *Eine Fähigkeit, die nur im Querformat erreichbar
///   wäre, gäbe es hier nicht* — darum wandert das Seitenfeld mit und fällt nicht weg.
/// * **Vollbild** (Entscheid 29): nur die Mitte, dazu ein Knopf zurück. Der Knopf bleibt
///   sichtbar — ein Vollbild ohne erkennbaren Ausgang ist eine Falle.
///
/// **Warum eine eigene Anordnung (`Arbeitsplatzanordnung`) und nicht drei Stapel.** Mit
/// einem `if quer { HStack … } else { VStack … }` wäre die Mitte nach dem Drehen eine
/// *andere* Ansicht: SwiftUI baut sie neu, und alles, was sie in sich hält, wäre weg — beim
/// Drehen des iPads mitten im Zeichnen. Hier bleiben die drei Teile dieselben drei und
/// werden nur anders hingelegt. *Am Gerät unbestätigt*, und für die Zeichenfläche gilt
/// trotzdem: Was nicht verloren gehen darf, gehört nicht in den Zustand einer Ansicht.
///
/// `Startansicht` setzt ihn seit dem 22.09.2026 ein:
/// `Arbeitsplatz { Zeichenflaeche(eigeneTafel: false) } seitenfeld: { Seitentafel() }` —
/// die Zeichenfläche **ohne** eigene Ebenentafel, weil die Tafel im einen Seitenfeld steht.
struct Arbeitsplatz<Mitte: View, Seitenfeld: View>: View {
    @ObservedObject var wahl: Leistenwahl
    @Environment(\.accessibilityReduceMotion) private var bewegungReduziert
    private let mitte: Mitte
    private let seitenfeld: Seitenfeld

    init(wahl: Leistenwahl = .gemeinsam,
         @ViewBuilder mitte: () -> Mitte,
         @ViewBuilder seitenfeld: () -> Seitenfeld) {
        self.wahl = wahl
        self.mitte = mitte()
        self.seitenfeld = seitenfeld()
    }

    var body: some View {
        GeometryReader { geo in
            let haltung = Haltung(groesse: geo.size)
            Arbeitsplatzanordnung(haltung: haltung, seite: wahl.seite, vollbild: wahl.vollbild) {
                Leiste(wahl: wahl, achse: haltung == .quer ? .senkrecht : .waagrecht,
                       kannUmlegen: true, kannVollbild: true)
                    .overlay(alignment: kante(haltung, fuerLeiste: true)) { randlinie(haltung) }
                    .versteckt(wahl.vollbild)

                mitte
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Zeichenblatt.buehne)
                    .overlay(alignment: wahl.seite == .links ? .topLeading : .topTrailing) {
                        if wahl.vollbild { ausgang }
                    }

                ScrollView(.vertical) { seitenfeld.padding(20) }
                    .background(Zeichenblatt.leiste)
                    .overlay(alignment: kante(haltung, fuerLeiste: false)) { randlinie(haltung) }
                    .versteckt(wahl.vollbild)
            }
        }
        .background(Zeichenblatt.grund)
        // BEWEGUNG NUR, WO SIE ERLAUBT IST. Wer am Gerät Bewegung abgestellt hat, bekommt
        // denselben Wechsel ohne Übergang — die Aussage steckt nicht in der Bewegung.
        .animation(bewegungReduziert ? nil : .easeInOut(duration: 0.18), value: wahl.seite)
        .animation(bewegungReduziert ? nil : .easeInOut(duration: 0.18), value: wahl.vollbild)
        .statusBarHidden(wahl.vollbild)
        .persistentSystemOverlays(wahl.vollbild ? .hidden : .automatic)
    }

    private var ausgang: some View {
        Button {
            wahl.vollbild = false
        } label: {
            Image(systemName: "arrow.down.right.and.arrow.up.left")
                .font(.system(size: 22, weight: .regular))
        }
        .buttonStyle(Wahlknopfstil(gewaehlt: false))
        .padding(16)
        .accessibilityLabel("Vollbild verlassen")
    }

    /// Die Kante, an der ein Teil an die Mitte grenzt — dort sitzt die Trennlinie.
    private func kante(_ haltung: Haltung, fuerLeiste: Bool) -> Alignment {
        switch haltung {
        case .hoch:
            return .top
        case .quer:
            let leisteLinks = wahl.seite == .links
            // Die Leiste grenzt mit ihrer inneren Kante an die Mitte, das Seitenfeld mit
            // der gegenüberliegenden.
            return (fuerLeiste == leisteLinks) ? .trailing : .leading
        }
    }

    private func randlinie(_ haltung: Haltung) -> some View {
        Rectangle()
            .fill(Zeichenblatt.linie)
            .frame(width: haltung == .quer ? 1 : nil, height: haltung == .quer ? nil : 1)
            .accessibilityHidden(true)
    }
}

/// Legt die drei Teile des Arbeitsplatzes hin: **Leiste, Mitte, Seitenfeld** — immer in
/// dieser Reihenfolge übergeben, damit jedes Teil beim Drehen dasselbe bleibt.
struct Arbeitsplatzanordnung: Layout {
    var haltung: Haltung
    var seite: Leistenseite
    var vollbild: Bool

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews,
                      cache: inout ()) -> CGSize {
        proposal.replacingUnspecifiedDimensions()
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews,
                       cache: inout ()) {
        guard subviews.count == 3 else { return }
        let leiste = subviews[0], mitte = subviews[1], feld = subviews[2]

        if vollbild {
            mitte.place(at: bounds.origin, anchor: .topLeading,
                        proposal: ProposedViewSize(bounds.size))
            // WEGGELEGT, NICHT ENTFERNT: Sie behalten ihren Zustand für die Rückkehr.
            for teil in [leiste, feld] {
                teil.place(at: bounds.origin, anchor: .topLeading, proposal: .zero)
            }
            return
        }

        switch haltung {
        case .quer:
            let lb = min(Zeichenblatt.leisteBreite, bounds.width)
            let fb = min(Zeichenblatt.seitenfeldBreite, max(0, bounds.width - lb))
            let mb = max(0, bounds.width - lb - fb)
            let reihe: [(LayoutSubview, CGFloat)] = seite == .links
                ? [(leiste, lb), (mitte, mb), (feld, fb)]
                : [(feld, fb), (mitte, mb), (leiste, lb)]
            var x = bounds.minX
            for (teil, breite) in reihe {
                teil.place(at: CGPoint(x: x, y: bounds.minY), anchor: .topLeading,
                           proposal: ProposedViewSize(width: breite, height: bounds.height))
                x += breite
            }
        case .hoch:
            let lh = min(Zeichenblatt.leisteHoehe, bounds.height)
            let fh = min(300, max(0, bounds.height - lh))
            let mh = max(0, bounds.height - lh - fh)
            var y = bounds.minY
            for (teil, hoehe) in [(mitte, mh), (leiste, lh), (feld, fh)] {
                teil.place(at: CGPoint(x: bounds.minX, y: y), anchor: .topLeading,
                           proposal: ProposedViewSize(width: bounds.width, height: hoehe))
                y += hoehe
            }
        }
    }
}

extension View {
    /// Unsichtbar, nicht antippbar und für den Bildschirmleser still — aber noch da.
    ///
    /// Nicht mehr `private` seit dem 22.09.2026: Auch `Startansicht` blendet die
    /// Verbindungszeile im Vollbild so aus, statt sie aus dem Baum zu nehmen.
    func versteckt(_ ja: Bool) -> some View {
        self
            .opacity(ja ? 0 : 1)
            .allowsHitTesting(!ja)
            .accessibilityHidden(ja)
    }
}
