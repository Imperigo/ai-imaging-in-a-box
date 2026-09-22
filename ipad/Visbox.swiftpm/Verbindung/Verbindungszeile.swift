import SwiftUI

/// Mit welcher HomeStation die App spricht — **oder dass sie mit keiner spricht**, und was
/// im Parkfach wartet.
///
/// Die Anzeige hat vier Zustände und behauptet in keinem mehr, als bekannt ist
/// (`Verbindungszustand` im Kern): **Aus** (nicht gekoppelt), **Suche** (es wird gesucht,
/// oder die gekoppelte HomeStation hat noch nicht geantwortet), **Gekoppelt** (sie hat
/// zuletzt geantwortet), **Getrennt** (sie hat nicht geantwortet — mit Grund).
///
/// **«In die Mappe legen» sitzt vorerst hier.** Im Entwurf (Blatt «Main») steht der Knopf
/// im Seitenfeld; das Seitenfeld hängt noch nirgends (`Startansicht` ordnet fest an). Der
/// Knopf ist darum als eigene Ansicht gebaut (`Mappenknopf`) und zieht mit, sobald das
/// Seitenfeld eingehängt wird — **dann hier entfernen**, sonst gibt es ihn zweimal.
///
/// Der Name `Verbindungszeile` bleibt, weil `Startansicht` ihn benutzt.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
@MainActor
struct Verbindungszeile: View {
    @ObservedObject var stand: Verbindungsstand
    let skizzenquelle: Skizzenquelle

    @State private var koppelnOffen = false
    @State private var fachOffen = false

    /// `skizzenquelle` `nil` heisst: **die Vorgabe** — die sichtbaren Ebenen der
    /// Zeichenfläche als **ein** Bild (Einheit «Zeichnen», `Zeichenstand.pngAusgabe`).
    ///
    /// Warum die Vorgabe im Rumpf steht und nicht als Standardwert (Mac-Übersetzung vom
    /// 22.09.2026, Warnung «main actor-isolated static property 'zeichenflaeche' can not be
    /// referenced from a nonisolated context»): Ein Standardwert wird **ausserhalb** des
    /// Hauptfadens ausgewertet, die Eigenschaft gehörte aber zu dieser `@MainActor`-Ansicht.
    /// Im Rumpf von `init` ist der Hauptfaden gesichert, und keine Marke muss wandern.
    init(stand: Verbindungsstand = .gemeinsam, skizzenquelle: Skizzenquelle? = nil) {
        self.stand = stand
        self.skizzenquelle = skizzenquelle ?? { Zeichenstand.gemeinsam.pngAusgabe(.eineSkizze) }
    }

    var body: some View {
        HStack(spacing: 16) {
            Button { koppelnOffen = true } label: { statusteil }
                .buttonStyle(.plain)
                .accessibilityHint("Öffnet das Koppeln")

            Spacer(minLength: 8)

            if let phase = stand.uebergabe {
                Uebergabestrecke(phase: phase, ziel: zielname)
                    .frame(width: 260)
                    .transition(.opacity)
            }

            if !stand.fach.isEmpty {
                // FESTE BREITE AUS DEM INHALT: Ohne `fixedSize` nimmt der Knopf (breite: nil
                // heisst im Wahlknopfstil «so breit wie moeglich») der Zeile den Platz weg.
                Button { fachOffen = true } label: { fachteil }
                    .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
                    .fixedSize()
            }

            Mappenknopf(stand: stand, skizzenquelle: skizzenquelle)
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 6)
        .frame(minHeight: 72)
        .background(Zeichenblatt.leiste)
        .animation(.easeOut(duration: Flugbahn.ablegen), value: stand.uebergabe == nil)
        .sheet(isPresented: $koppelnOffen) { Koppelbildschirm(stand: stand) }
        .sheet(isPresented: $fachOffen) { Parkfachliste(stand: stand) }
    }

    // ------------------------------------------------------------------- Teile

    private var statusteil: some View {
        HStack(spacing: 12) {
            Statuspunkt(zustand: stand.zustand)
            VStack(alignment: .leading, spacing: 3) {
                Text(stand.zustand.wort)
                    .font(Schrift.text(15, .semibold))
                    .foregroundStyle(Zeichenblatt.schrift)
                Text(detail)
                    .font(Schrift.text(12))
                    .foregroundStyle(Zeichenblatt.leise)
                    .lineLimit(2)
            }
        }
        // 60 PT, WIE DAS BLATT «ZEICHEN» ES FUER JEDES ZIEL DES STIFTS VERLANGT — nicht die
        // 44 pt, die Apple fuer den Finger als Untergrenze nennt (Durchsicht 22.09.2026).
        .frame(minHeight: Zeichenblatt.tippziel)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
    }

    private var zielname: String {
        stand.stationsname ?? stand.adresse.map(Koppelbildschirm.text) ?? "HomeStation"
    }

    /// Der Satz unter dem Zustand.
    private var detail: String {
        switch stand.zustand {
        case .aus:
            return "Nicht gekoppelt. Skizzen warten auf dem iPad."
        case .suche:
            return stand.gekoppelt ? "\(zielname) hat noch nicht geantwortet …"
                                   : "Sucht im Heimnetz …"
        case .gekoppelt:
            return "\(zielname) · antwortet"
        case .getrennt(let grund):
            return grund
        }
    }

    /// Was der Knopf zum Parkfach sagt — **nur Zahlen, die nicht null sind.**
    ///
    /// Bis zur Durchsicht vom 22.09.2026 stand hier dauerhaft «0 geparkt», sobald nur noch
    /// angekommene Skizzen im Fach lagen (und die blieben für immer). Jetzt räumt das Fach
    /// sie nach 7 Tagen weg (`Parkfach.raeumeAuf`), und solange sie dastehen, sagt der Knopf
    /// nur «Parkfach»: Die Quittungen sind erreichbar, ohne eine Null zu behaupten.
    private var fachteil: some View {
        let wartend = stand.wartend
        let unterwegs = stand.fach.filter { $0.zustand == .unterwegs }.count
        let offen = stand.brauchenEntscheid
        let teile = [(wartend, "geparkt"), (unterwegs, "unterwegs"), (offen, "offen")]
            .filter { $0.0 > 0 }
        return HStack(spacing: 8) {
            if teile.isEmpty {
                Text("Parkfach")
            }
            ForEach(Array(teile.enumerated()), id: \.offset) { paar in
                if paar.offset > 0 { Text("·") }
                Text("\(paar.element.0)").font(Schrift.zahl(15, .medium))
                Text(paar.element.1)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(Text(teile.isEmpty
            ? "Parkfach: nichts wartet"
            : "Parkfach: " + teile.map { "\($0.0) \($0.1)" }.joined(separator: ", ")))
    }
}

/// Der Punkt vor dem Zustand. **Er ist nie die ganze Aussage** — das Wort daneben ist es.
///
/// Grün nur bei «Gekoppelt» (wie auf dem Blatt der HomeStation: «iPad verbunden»); ein
/// atmender Punkt nur bei «Suche», weil dann wirklich etwas geschieht. Aus und getrennt
/// sind hohl — ein Ring, der sagt: hier ist gerade niemand.
@MainActor
struct Statuspunkt: View {
    let zustand: Verbindungszustand
    @Environment(\.accessibilityReduceMotion) private var ruhig

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: !atmet)) { zeit in
            let t = zeit.date.timeIntervalSinceReferenceDate
            let welle = 0.5 - 0.5 * cos(2 * Double.pi * t / Flugbahn.atem)
            punkt.opacity(atmet ? 0.35 + 0.65 * welle : 1)
        }
        .frame(width: 12, height: 12)
        .accessibilityHidden(true)
    }

    private var atmet: Bool { zustand == .suche && !ruhig }

    @ViewBuilder
    private var punkt: some View {
        switch zustand {
        case .gekoppelt:
            Circle().fill(Zeichenblatt.gewaehltRand)
        case .suche:
            Circle().fill(Zeichenblatt.leise)
        case .aus, .getrennt:
            Circle().strokeBorder(Zeichenblatt.leise, lineWidth: 2)
        }
    }
}

/// «In die Mappe legen» — **die Skizze geht ins Parkfach und von dort hinaus.**
///
/// Nach dem Tippen steht ein Satz da, wenn es einen zu sagen gibt (nichts gezeichnet,
/// geparkt, weil niemand antwortet, …). Geht sie gleich hinaus, sagt es die Marke.
@MainActor
struct Mappenknopf: View {
    @ObservedObject var stand: Verbindungsstand
    let skizzenquelle: Skizzenquelle
    @State private var satz: String?

    var body: some View {
        HStack(spacing: 12) {
            if let satz {
                Text(satz)
                    .font(Schrift.text(12))
                    .foregroundStyle(Zeichenblatt.leise)
                    .lineLimit(3)
                    .frame(maxWidth: 260, alignment: .trailing)
                    .multilineTextAlignment(.trailing)
                    .onTapGesture { self.satz = nil }
            }
            Button {
                satz = stand.legeInDieMappe(skizzenquelle())
            } label: {
                Text("In die Mappe legen")
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil))
            .fixedSize()
            .accessibilityHint("Legt die sichtbaren Ebenen als Skizze in die Mappe der HomeStation. "
                               + "Nichts rechnet von selbst.")
        }
    }
}
