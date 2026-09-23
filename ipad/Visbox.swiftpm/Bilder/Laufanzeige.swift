import SwiftUI

/// **Was auf der HomeStation gerade rechnet** — und der Knopf «Lauf abbrechen» (Blatt
/// «Lauf», Entscheide 14 und 31).
///
/// Gezeigt wird nur, was der Laufstand sagt (`GET /api/fortschritt`,
/// `Verbindungsstand.laufstand`):
///
/// * **Ein Balken nur bei gezählten Schritten** (`Fortschrittsstand.schrittanteil`, nur bei
///   `belegt`). Sonst steht da, wie lange der Schritt schon läuft — *nur ein Lebenszeichen*.
///   Einen Anteil über den ganzen Lauf gibt es nicht (Protokoll §5), und hier wird keiner
///   ausgerechnet.
/// * **«Abbruch verlangt» ist nicht «abgebrochen».** Nach dem Tippen sagt der Knopf, dass
///   der Abbruch verlangt ist; ob er wirkte, steht erst nach dem Lauf im Ergebnis.
/// * **Der Knopf sagt, was der Server weiss** (seit der Durchsicht der Welle 2b, 23.09.2026):
///   `Fortschrittsstand.abbruchAngezeigt(hier:)` — der Abbruch gilt als verlangt, wenn die
///   HomeStation ihn vermerkt hat, auch von einem anderen Gerät; nur wenn sie dazu nichts
///   sagt, gilt, was dieses iPad verlangt hat (`mappe.abbruchVerlangt`). Darunter steht,
///   woher das «verlangt» kommt (`abbruchSatz(hier:)`). Bis dahin kannte der Knopf nur
///   dieses iPad.
/// * **Die Kopfzeile** über dem Schritt: «Variante 2 von 3 · Prüfen» (`Fortschrittsstand.
///   kopfzeile`). Mit jeder Variante beginnt die Knotennummer wieder bei eins; ohne diese
///   Zeile sähe die zweite Variante aus wie ein Lauf, der rückwärts geht. **Fehlt ein Feld,
///   fehlt sein Teil** — kein «Prüfen» aus einem fehlenden `entwurf`.
///
/// Beide Regeln stehen im Kern und sind dort geprüft (`AnfragenTests`); dass diese Ansicht
/// sie zeigt, ist nicht übersetzt (Stand 23.09.2026), ohne Probe und am Gerät unbestätigt.
///
/// Das Nachfragen während eines Laufs macht `Laufwaechter` — er sitzt am ganzen Seitenfeld,
/// damit es auch weiterläuft, wenn dort gerade die Ebenen stehen. *Gebaut, am Gerät
/// unbestätigt (22.09.2026).*
struct Laufanzeige: View {
    @ObservedObject var verbindung: Verbindungsstand
    @ObservedObject var mappe: Bildbandstand

    init(verbindung: Verbindungsstand = .gemeinsam, mappe: Bildbandstand = .gemeinsam) {
        self.verbindung = verbindung
        self.mappe = mappe
    }

    private var stand: Fortschrittsstand? { verbindung.laufstand }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Lauf")
            inhalt
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private var inhalt: some View {
        if let s = stand {
            switch s.laeuft {
            case .some(true):
                laufend(s)
            case .some(false):
                ruhend(s)
            case .none:
                leise("Ob gerade gerechnet wird, sagt die HomeStation nicht.")
            }
        } else {
            leise(verbindung.gekoppelt
                  ? "Die HomeStation hat noch keinen Laufstand geschickt."
                  : "Nicht gekoppelt — kein Laufstand.")
        }
    }

    // ------------------------------------------------------------------ es rechnet

    private func laufend(_ s: Fortschrittsstand) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            // NUR, WAS DER SERVER SAGT: ohne Variante und Lesart keine Zeile, kein «Prüfen».
            if let kopf = s.kopfzeile {
                Text(kopf)
                    .font(Schrift.zahl(13, .medium))
                    .foregroundStyle(Zeichenblatt.schrift)
            }
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(s.knoten ?? "Schritt ohne Namen")
                    .font(Schrift.zahl(14, .medium))
                if let art = s.knotenart {
                    Text(art)
                        .font(Schrift.text(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
                Spacer(minLength: 4)
                if let n = s.nummer, let von = s.von {
                    Text("\(n) von \(von)")
                        .font(Schrift.zahl(13))
                        .foregroundStyle(Zeichenblatt.leise)
                }
            }
            if let anteil = s.schrittanteil, let schritt = s.schritt, let gesamt = s.schritteGesamt {
                ProgressView(value: anteil)
                    .tint(Zeichenblatt.schrift)
                    .accessibilityLabel("Schritte im laufenden Knoten")
                    .accessibilityValue("\(schritt) von \(gesamt)")
                Text("\(schritt) / \(gesamt) Schritte — gezählt, der Balken ist belegt.")
                    .font(Schrift.zahl(12))
                    .foregroundStyle(Zeichenblatt.leise)
            } else {
                Text(s.knotenSeitS.flatMap(Laufanzeige.zeit).map { "läuft seit " + $0 }
                     ?? "Wie lange schon, sagt die HomeStation nicht.")
                    .font(Schrift.zahl(13))
                leise("Nur ein Lebenszeichen. Wie weit es ist, sagt dieser Schritt nicht — "
                      + "und darum behauptet es hier auch nichts.")
            }
            fertige(s)
            abbrechen(s)
        }
    }

    private func abbrechen(_ s: Fortschrittsstand) -> some View {
        let verlangt = s.abbruchAngezeigt(hier: mappe.abbruchVerlangt)
        return VStack(alignment: .leading, spacing: 6) {
            Button {
                Task { @MainActor in
                    mappe.sendet = true
                    let q = await verbindung.brichLaufAb()
                    mappe.sendet = false
                    mappe.quittung = q
                    if q.ausgang == .angenommen { mappe.abbruchVerlangt = true }
                }
            } label: {
                Text(verlangt ? "Abbruch verlangt" : "Lauf abbrechen")
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil))
            .disabled(verlangt || mappe.sendet)
            .accessibilityHint("Hält zwischen zwei Schritten an. Was fertig ist, bleibt in der Mappe.")
            if let woher = s.abbruchSatz(hier: mappe.abbruchVerlangt) {
                leise(woher)
            }
            leise("Abgebrochen wird zwischen zwei Schritten. Was schon fertig ist, bleibt in der "
                  + "Mappe und wird beim nächsten Mal nicht neu gerechnet.")
        }
    }

    @ViewBuilder
    private func fertige(_ s: Fortschrittsstand) -> some View {
        if let liste = s.fertige, !liste.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                ForEach(Array(liste.enumerated()), id: \.offset) { paar in
                    let k = paar.element
                    HStack(spacing: 8) {
                        Text(k.knoten ?? "?")
                            .font(Schrift.zahl(12))
                        Spacer(minLength: 4)
                        Text(fertigSatz(k))
                            .font(Schrift.text(12))
                            .foregroundStyle(Zeichenblatt.leise)
                    }
                }
            }
        }
    }

    private func fertigSatz(_ k: FertigerKnoten) -> String {
        var teile = [k.status ?? "Stand nicht gemeldet"]
        if k.ausCache == true { teile.append("aus dem Speicher") }
        if let d = k.dauerS.flatMap(Laufanzeige.zeit) { teile.append(d) }
        return teile.joined(separator: " · ")
    }

    // ------------------------------------------------------------ es rechnet nicht

    @ViewBuilder
    private func ruhend(_ s: Fortschrittsstand) -> some View {
        if let fehler = s.fehler, !fehler.isEmpty {
            VStack(alignment: .leading, spacing: 4) {
                Text("Der letzte Lauf scheiterte:")
                    .font(Schrift.text(13, .semibold))
                Text(fehler)
                    .font(Schrift.text(13))
                    .fixedSize(horizontal: false, vertical: true)
            }
        } else if let e = s.ergebnis {
            // «VERLANGT» UND «GEWIRKT» GETRENNT: Nur `ergebnis.abgebrochen == true` heisst,
            // dass der Abbruch einen Schritt verhindert hat.
            let status = e["status"]?.alsText ?? "ohne gemeldeten Stand"
            let abgebrochen = e["abgebrochen"]?.alsWahrheit
            VStack(alignment: .leading, spacing: 4) {
                Text("Letzter Lauf: \(status)")
                    .font(Schrift.text(13, .semibold))
                if abgebrochen == true {
                    leise("Abgebrochen. Was fertig war, liegt in der Mappe.")
                }
            }
        } else {
            leise("Es rechnet gerade nichts. Nichts rechnet von selbst.")
        }
    }

    // ------------------------------------------------------------------ Handgriffe

    /// Sekunden als «m:ss» — oder `nil`, wenn keine lesbare Zahl kam.
    static func zeit(_ sekunden: Double) -> String? {
        guard sekunden.isFinite, sekunden >= 0 else { return nil }
        let ganz = Int(sekunden.rounded(.down))
        return String(format: "%d:%02d", ganz / 60, ganz % 60)
    }

    private func leise(_ satz: String) -> some View {
        Text(satz)
            .font(Schrift.text(13))
            .foregroundStyle(Zeichenblatt.leise)
            .fixedSize(horizontal: false, vertical: true)
    }
}

/// Fragt den Laufstand nach, **solange ein Lauf läuft** — alle zwei Sekunden statt alle zehn
/// (`Verbindungsstand.pruefabstand`), damit ein gezählter Schritt sichtbar weiterrückt. Endet
/// der Lauf, wird die Mappe neu geladen, damit das Ergebnis dasteht, ohne dass jemand danach
/// suchen muss.
///
/// **Warum zwei Zustände und nicht eine Schleife bis zum Ende:** `.task(id:)` bricht die
/// laufende Aufgabe ab, sobald sich die Kennung ändert — also genau in dem Augenblick, in dem
/// der Lauf endet. Eine Schleife, die danach die Mappe laden wollte, käme nie dort an. Die
/// Aufgabe zu `false` merkt darum an `warLaufend`, dass eben einer zu Ende ging.
struct Laufwaechter: ViewModifier {
    @ObservedObject var verbindung: Verbindungsstand
    @ObservedObject var mappe: Bildbandstand
    @State private var warLaufend = false

    /// Gesetzt, nicht gemessen.
    static let abstandImLauf: UInt64 = 2

    private var laeuft: Bool { verbindung.laufstand?.laeuft == true }

    func body(content: Content) -> some View {
        content.task(id: laeuft) {
            guard laeuft else {
                if warLaufend {
                    warLaufend = false
                    mappe.abbruchVerlangt = false
                    await verbindung.ladeMappe(bildband: mappe)
                }
                return
            }
            warLaufend = true
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: Laufwaechter.abstandImLauf * 1_000_000_000)
                if Task.isCancelled { return }
                await verbindung.pruefe()
            }
        }
    }
}
