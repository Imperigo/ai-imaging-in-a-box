import SwiftUI

/// Der Reiter «Mappe» im Seitenfeld: **was rechnet, was bestellt werden kann, welche Bilder
/// und Skizzen in der Mappe liegen** (Blätter «Main», «Skizzen», «Lauf», «Varianten»).
///
/// Wie die Ebenentafel ohne eigenen Rahmen und ohne eigenen Rollbereich — den bringt das
/// Seitenfeld des Arbeitsplatzes mit.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
struct Mappentafel: View {
    @ObservedObject var mappe: Bildbandstand
    @ObservedObject var verbindung: Verbindungsstand

    init(mappe: Bildbandstand = .gemeinsam, verbindung: Verbindungsstand = .gemeinsam) {
        self.mappe = mappe
        self.verbindung = verbindung
    }

    private var laeuft: Bool { verbindung.laufstand?.laeuft == true }

    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            kopf
            Laufanzeige(verbindung: verbindung, mappe: mappe)
            varianten
            if let q = mappe.quittung {
                quittung(q)
            }
            VStack(alignment: .leading, spacing: 10) {
                Abschnittstitel(text: "Bilder")
                Bildband(stand: mappe)
            }
            Skizzenliste(mappe: mappe, verbindung: verbindung)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // ------------------------------------------------------------------ Kopf

    private var kopf: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline, spacing: 10) {
                Text(mappe.projektname ?? "Mappe")
                    .font(Schrift.titel(22))
                    .lineLimit(1)
                Spacer(minLength: 4)
                Button {
                    Task { @MainActor in await verbindung.ladeMappe(bildband: mappe) }
                } label: {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 18))
                }
                .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: 44, hoehe: 44))
                .disabled(!verbindung.gekoppelt)
                .accessibilityLabel("Mappe neu laden")
            }
            if let satz = verbindung.mappenSatz {
                Text(satz)
                    .font(Schrift.text(13))
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    // ------------------------------------------------------------- Varianten

    /// Drei Startwerte oder drei Ebenen (Entscheid 32) — **gewählt und bestellt hier.**
    private var varianten: some View {
        VStack(alignment: .leading, spacing: 10) {
            Abschnittstitel(text: "Drei Varianten")
            HStack(spacing: 8) {
                ForEach(Variantenquelle.allCases) { q in
                    Button(q.name) { mappe.variantenquelle = q }
                        .buttonStyle(Wahlknopfstil(gewaehlt: mappe.variantenquelle == q,
                                                   breite: nil, hoehe: 44))
                        .accessibilityAddTraits(mappe.variantenquelle == q ? .isSelected : [])
                }
            }
            Text(mappe.variantenquelle.satz)
                .font(Schrift.text(13))
                .foregroundStyle(Zeichenblatt.leise)
                .fixedSize(horizontal: false, vertical: true)
            if mappe.variantenquelle == .startwerte {
                Button("Drei Startwerte rechnen") {
                    let lesart = mappe.bestellart
                    Task { @MainActor in
                        mappe.sendet = true
                        mappe.quittung = await verbindung.bestelle(.startwerte, lesart: lesart)
                        mappe.sendet = false
                    }
                }
                .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil))
                .disabled(!verbindung.gekoppelt || laeuft || mappe.sendet)
                .accessibilityHint(mappe.bestellart == .entwerfen
                                   ? "Als Entwurf, ohne Geometrieprüfung"
                                   : "Geprüft, mit Geometrieprüfung")
            }
            if laeuft {
                Text("Es läuft schon einer — die HomeStation rechnet einen Lauf zur Zeit.")
                    .font(Schrift.text(13))
                    .foregroundStyle(Zeichenblatt.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    /// Was zur letzten Handlung zu sagen ist. **Ungewiss steht als ungewiss da** — nicht als
    /// Fehler und nicht als Erfolg.
    private func quittung(_ q: Handlungsquittung) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Text(wort(q.ausgang))
                .font(Schrift.zahl(12, .semibold))
                .foregroundStyle(Zeichenblatt.leise)
            Text(q.satz)
                .font(Schrift.text(13))
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
            Button {
                mappe.quittung = nil
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 14))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: 44, hoehe: 44))
            .accessibilityLabel("Meldung schliessen")
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
    }

    private func wort(_ a: Handlungsquittung.Ausgang) -> String {
        switch a {
        case .angenommen: return "ANGENOMMEN"
        case .abgelehnt: return "ABGELEHNT"
        case .ungewiss: return "UNGEWISS"
        case .nichtGesendet: return "NICHT GESENDET"
        }
    }
}
