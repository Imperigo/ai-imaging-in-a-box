import Foundation
import SwiftUI
import VisboxKern

// DIE KI IN DER ASSISTENT-LEISTE — Blatt 30, Feld 1 («KI bedient Visbox»; Entscheide 106a, 108,
// 114). Oben in der Leiste, fuer Claude und den Assistenten zugleich:
//
//   Claude verbunden · über MCP, nur dieser Mac
//   Assistent: qwen3:14b am Heim-PC · bereit
//   Selbständigkeit  [Karte | Coop | Voll]                       (108 A)
//   ● Claude legt einen Knoten an …       — nur, solange die KI arbeitet (108 C)
//   ┌ VORSCHLAG VON CLAUDE · K-12 ─────────┐
//   │ Zusammenfassung · Schritte           │
//   │ [Anwenden] [Ablehnen]                │
//   │ Rendern braucht danach deine Freigabe am Knoten.
//   └──────────────────────────────────────┘
//   Claudes letzten Schritt zurücknehmen   — nur, wenn es einen gibt (114)
//
// Was die Zeilen sagen und wann etwas steht, entscheidet der Kern (`Claudezeile`,
// `Assistentenkopf`, `Kileistenstand`, `Kikarte`); hier wird nur gezeichnet und gedrueckt. In
// kleine Teilansichten zerlegt, weil der Uebersetzer an einem grossen Rumpf aufgibt (Mac-CI
// 20.10.2026: «unable to type-check this expression in reasonable time»).
//
// **Unuebersetzt** (Linux hat kein SwiftUI): geschrieben gegen macOS 14.

/// Der KI-Teil oben in der Leiste. `assistentSatz` kommt von der Leiste darunter (sie fragt den
/// Heim-PC nach dem Modell) oder vom Platzhalter ohne Heim-PC.
struct Kileiste: View {
    let assistentSatz: String
    // VON AUSSEN GEREICHT (`Kileiste(assistentSatz:zentrale:anschluss:)` im Rumpf der Leiste),
    // nicht als Vorgabewert hier: Ein Vorgabewert laese die Einzelstuecke ausserhalb des
    // Hauptfadens.
    @ObservedObject var zentrale: Kizentrale
    @ObservedObject var anschluss: Claudeanschluss
    @State private var kontakt: Date?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Claudezeilenansicht(lage: anschluss.lage.kernlage, kontakt: kontakt)
            Text(assistentSatz)
                .font(.callout)
                .foregroundStyle(.secondary)
            Selbstaendigkeitsschalter(zentrale: zentrale)
            Taetigkeitsstrom(stand: zentrale.stand)
            Kikartenliste(zentrale: zentrale)
            Ruecknahmeknopf(zentrale: zentrale)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .task { await wacheUeberKontakt() }
    }

    /// Wann Claude zuletzt sprach — der Kern ist ein `actor`, darum nachgesehen, nicht beobachtet.
    private func wacheUeberKontakt() async {
        while !Task.isCancelled {
            kontakt = await anschluss.kern.letzterKontakt
            try? await Task.sleep(nanoseconds: 5_000_000_000)
        }
    }
}

private struct Claudezeilenansicht: View {
    let lage: Claudehoererlage
    let kontakt: Date?

    var body: some View {
        TimelineView(.periodic(from: .now, by: 15)) { zeit in
            let zeile = Claudezeile.zeile(lage: lage, letzterKontakt: kontakt, jetzt: zeit.date)
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Circle()
                    .fill(zeile.titel == "Claude verbunden" ? Color.green : Color.secondary)
                    .frame(width: 8, height: 8)
                Text(zeile.titel).font(.headline)
                Text(zeile.zusatz)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
    }
}

private struct Selbstaendigkeitsschalter: View {
    @ObservedObject var zentrale: Kizentrale

    var body: some View {
        HStack(spacing: 10) {
            Text("Selbständigkeit")
                .font(.callout)
                .foregroundStyle(.secondary)
            Picker("Selbständigkeit", selection: wahl) {
                ForEach(Selbstaendigkeit.allCases, id: \.self) { modus in
                    Text(modus.wort).tag(modus)
                }
            }
            .pickerStyle(.segmented)
            .labelsHidden()
        }
        .help(Mcpfreigabe.satz(zentrale.modus))
    }

    private var wahl: Binding<Selbstaendigkeit> {
        Binding(get: { zentrale.modus }, set: { zentrale.setzeModus($0) })
    }
}

/// «● Claude legt … an» — **nur, solange die KI arbeitet** (108 C), mit kurzem Nachlauf.
private struct Taetigkeitsstrom: View {
    let stand: Kileistenstand

    var body: some View {
        TimelineView(.periodic(from: .now, by: 1)) { zeit in
            let zeilen = stand.strom(jetzt: zeit.date)
            if !zeilen.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(zeilen.enumerated()), id: \.offset) { _, satz in
                        Text("● " + satz)
                            .font(.callout)
                            .foregroundStyle(Assistentenfarbe.violett)
                    }
                }
            }
        }
    }
}

private struct Kikartenliste: View {
    @ObservedObject var zentrale: Kizentrale

    var body: some View {
        ForEach(zentrale.stand.karten) { karte in
            Kikartenansicht(karte: karte, vermerk: zentrale.vermerk(karte.kennung),
                            anwenden: { Task { await zentrale.entscheide(karte.kennung, ja: true) } },
                            ablehnen: { Task { await zentrale.entscheide(karte.kennung, ja: false) } })
        }
    }
}

/// Eine Karte nach Blatt 30: Kopf, Zusammenfassung, Schritte, «Anwenden · Ablehnen» und bei
/// einer Render-Karte der Satz zur Freigabe am Knoten.
private struct Kikartenansicht: View {
    let karte: Kikarte
    /// «Leitung unterbrochen» (Strang Karten) — die Karte bleibt, Claude hoert spaeter.
    let vermerk: String?
    let anwenden: () -> Void
    let ablehnen: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(karte.kopf.uppercased())
                .font(.caption.weight(.semibold))
                .foregroundStyle(Assistentenfarbe.violett)
            Text(karte.zusammenfassung)
                .fixedSize(horizontal: false, vertical: true)
            if let vermerk {
                Text(vermerk)
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
            Kikartenzeilen(zeilen: karte.zeilen)
            HStack(spacing: 8) {
                Button("Anwenden", action: anwenden)
                    .buttonStyle(Kiknopf(betont: true))
                Button("Ablehnen", action: ablehnen)
                    .buttonStyle(Kiknopf(betont: false))
            }
            if let satz = karte.freigabeSatz {
                Text(satz)
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: 10)
            .stroke(Assistentenfarbe.violett, lineWidth: 2))
    }
}

private struct Kikartenzeilen: View {
    let zeilen: [String]

    var body: some View {
        ForEach(Array(zeilen.enumerated()), id: \.offset) { _, zeile in
            Text("· " + zeile)
                .font(.callout)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

/// «Claudes letzten Schritt zurücknehmen» (Entscheid 114) — nur, wenn es einen gibt; darunter
/// der Satz der Ruecknahme.
private struct Ruecknahmeknopf: View {
    @ObservedObject var zentrale: Kizentrale

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let schritt = zentrale.stand.claudeZuruecknehmen {
                Button(Kileistenstand.zuruecknehmenKnopf) {
                    Task { await zentrale.nimmClaudesLetztenSchrittZurueck() }
                }
                .buttonStyle(Kiknopf(betont: false))
                .help(schritt.zusammenfassung)
            }
            if let satz = zentrale.meldung {
                Text(satz)
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
                    .onTapGesture { zentrale.vergissMeldung() }
            }
        }
    }
}

/// Ein Knopf mit **mindestens 44 pt** — wie `Leistenknopf` der Leiste darunter.
private struct Kiknopf: ButtonStyle {
    let betont: Bool
    @Environment(\.isEnabled) private var aktiv

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.body.weight(.medium))
            .padding(.horizontal, 14)
            .frame(minWidth: 44, minHeight: 44)
            .foregroundStyle(betont ? Color.white : Color.primary)
            .background(RoundedRectangle(cornerRadius: 8)
                .fill(betont ? Assistentenfarbe.violett : Color.secondary.opacity(0.15)))
            .opacity(!aktiv ? 0.45 : (configuration.isPressed ? 0.75 : 1))
            .contentShape(Rectangle())
    }
}
