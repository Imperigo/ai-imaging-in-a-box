import Foundation
import SwiftUI
// DER KERN KOMMT JE NACH AUFBAU DES PAKETS ALS MODUL ODER MITUEBERSETZT (Plan v0.1.7,
// Strom A). Diese Datei soll in beiden Faellen bauen; im Kern selbst ist `canImport`
// verboten (`tests/test_ipad_geruest.py`), hier nicht.
#if canImport(VisboxKern)
import VisboxKern
#endif

// DIE SEITENLEISTE DES ASSISTENTEN — Blatt 14, gezeichnet nach der Entwurfsflaeche.
//
// Rechts am Fenster: «Assistent · läuft am Heim-PC», das Gespraech, darunter die violett
// gerahmte Karte «Vorschlag:» mit «Anwenden · Ablehnen · Ändern», gestrichelt die Grenzen,
// unten das Eingabefeld. Was sie zeigt und wann, entscheidet der Kern
// (`Assistentengespraech`, `Assistentenkarte`, `Assistentenzeile`); hier wird nur
// gezeichnet und gesendet.
//
// **Unuebersetzt** (Linux hat kein SwiftUI): geschrieben gegen macOS 14. Die Stellen, an
// denen das am Mac zuerst zu pruefen ist, stehen im Bericht an Claude.

// ==================================================================== der Anschluss

/// Wohin die Leiste fragt: die Adresse des Visbox-Servers und die Anmeldung. Der Mac
/// spricht **nur** mit dem Visbox-Server, nie direkt mit Ollama (Plan v0.1.7, D2).
///
/// Gesendet wird über eine `URLSession`, die von aussen kommt — so kann die App dieselbe
/// Sitzung einsetzen wie für die anderen Wege (etwa mit eigener Prüfung des Zertifikats).
struct AssistentAnschluss: @unchecked Sendable {
    let basis: URL
    let anmeldung: Anmeldung?
    var sitzung: URLSession = .shared

    /// Eine Frage an den Assistenten darf dauern: Der Kern wartet bis zu 300 s auf Ollama.
    static let frist: TimeInterval = 330

    func schicke(_ anfrage: Anfrage) async throws -> (status: Int, daten: Data) {
        guard let url = anfrage.adresse(basis: basis) else { throw URLError(.badURL) }
        var r = URLRequest(url: url)
        r.httpMethod = anfrage.methode.rawValue
        for (name, wert) in anfrage.kopfzeilen { r.setValue(wert, forHTTPHeaderField: name) }
        r.httpBody = anfrage.rumpf
        r.timeoutInterval = Self.frist
        let (daten, antwort) = try await sitzung.data(for: r)
        return ((antwort as? HTTPURLResponse)?.statusCode ?? 0, daten)
    }
}

// =========================================================================== das Modell

@MainActor
final class Assistentenmodell: ObservableObject {
    @Published private(set) var gespraech = Assistentengespraech()
    @Published private(set) var zeile: Assistentenzeile?
    @Published var eingabe = ""

    let anschluss: AssistentAnschluss
    let ordner: String?

    /// Wie oft der Stand nachgesehen wird — **gesetzt**: oft genug, dass die Eingabe nach
    /// einem Bild bald wieder steht, selten genug, dass die Startzeile nicht drängelt.
    static let standAlle: UInt64 = 10_000_000_000

    init(anschluss: AssistentAnschluss, ordner: String?) {
        self.anschluss = anschluss
        self.ordner = ordner
    }

    func wacheUeberStand() async {
        while !Task.isCancelled {
            await pruefeStand()
            try? await Task.sleep(nanoseconds: Self.standAlle)
        }
    }

    func pruefeStand() async {
        do {
            let (status, daten) = try await anschluss.schicke(
                Anfragen.heim(anmeldung: anschluss.anmeldung))
            zeile = try Assistentenzeile.ausHeim(status: status, daten: daten)
        } catch let fehler as Serverfehler {
            zeile = Assistentenzeile(stand: nil, modell: nil, satz: fehler.satz)
        } catch {
            zeile = Assistentenzeile(stand: nil, modell: nil,
                                     satz: "Der Heim-PC antwortet nicht — der Assistent wartet.")
        }
    }

    func sende() async {
        guard let bitte = gespraech.sende(eingabe) else { return }
        eingabe = ""
        do {
            let anfrage = try Anfragen.assistent(bitte, anmeldung: anschluss.anmeldung)
            let (status, daten) = try await anschluss.schicke(anfrage)
            gespraech.empfange(try Assistentenantwort.lies(status: status, daten: daten))
        } catch {
            gespraech.scheitert(Self.satz(zu: error))
        }
    }

    func anwenden() async {
        guard let vorschlag = gespraech.beginneAnwenden() else { return }
        do {
            let anfrage = try Anfragen.assistentAnwenden(vorschlag, ordner: ordner,
                                                         anmeldung: anschluss.anmeldung)
            let (status, daten) = try await anschluss.schicke(anfrage)
            gespraech.angewendet(try Rechenstart.lies(status: status, daten: daten))
        } catch {
            gespraech.scheitert(Self.satz(zu: error))
        }
        // NACH DEM ANWENDEN IST DAS SPRACHMODELL ENTLADEN — die Zeile soll das gleich
        // sagen und nicht erst beim naechsten Takt.
        await pruefeStand()
    }

    func ablehnen() { gespraech.lehneAb() }

    func aendern() {
        if let text = gespraech.aendere() { eingabe = text }
    }

    private static func satz(zu fehler: Error) -> String {
        if let f = fehler as? Serverfehler { return f.satz }
        if let f = fehler as? Rumpffehler { return f.satz }
        return "Der Heim-PC antwortete nicht (\(fehler.localizedDescription))."
    }
}

// =========================================================================== die Leiste

/// Die Seitenleiste nach Blatt 14. `beiStandpunkt` meldet den vorgeschlagenen Standpunkt,
/// damit der Plan ihn violett neben den heutigen grünen zeichnen kann (`nil`: keiner).
struct Assistentenleiste: View {
    @StateObject private var modell: Assistentenmodell
    private let beiStandpunkt: (VorgeschlagenerStandpunkt?) -> Void

    init(anschluss: AssistentAnschluss, ordner: String? = nil,
         beiStandpunkt: @escaping (VorgeschlagenerStandpunkt?) -> Void = { _ in }) {
        _modell = StateObject(wrappedValue: Assistentenmodell(anschluss: anschluss,
                                                              ordner: ordner))
        self.beiStandpunkt = beiStandpunkt
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Assistent · läuft am Heim-PC")
                .font(.headline)
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(Array(modell.gespraech.beitraege.enumerated()), id: \.offset) {
                        _, beitrag in
                        Beitragsblase(beitrag: beitrag)
                    }
                    if modell.gespraech.wartet {
                        HStack(spacing: 8) {
                            ProgressView().controlSize(.small)
                            Text("Der Assistent antwortet …").foregroundStyle(.secondary)
                        }
                    }
                    if let karte = modell.gespraech.karte {
                        Vorschlagskarte(karte: karte, gesperrt: modell.gespraech.wartet,
                                        anwenden: { Task { await modell.anwenden() } },
                                        ablehnen: { modell.ablehnen() },
                                        aendern: { modell.aendern() })
                    }
                    if let hinweis = modell.gespraech.hinweis {
                        Text(hinweis).font(.callout).foregroundStyle(.secondary)
                    }
                    Grenzen()
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            Eingabe(modell: modell)
        }
        .padding(16)
        .frame(minWidth: 300, idealWidth: 340, maxWidth: 420, maxHeight: .infinity,
               alignment: .top)
        .task { await modell.wacheUeberStand() }
        .onChange(of: modell.gespraech.karte?.standpunkt) { _, neu in beiStandpunkt(neu) }
    }
}

// ======================================================================== die Teile

/// Violett: die Farbe des Vorschlags auf Blatt 14 — auf der Karte und im Plan.
enum Assistentenfarbe {
    static let violett = Color(red: 0.49, green: 0.36, blue: 0.86)
}

private struct Beitragsblase: View {
    let beitrag: Gespraechsbeitrag

    var body: some View {
        let mensch = beitrag.von == .mensch
        Text(beitrag.text)
            .textSelection(.enabled)
            .padding(10)
            .background(RoundedRectangle(cornerRadius: 10)
                .fill(mensch ? Color.secondary.opacity(0.12) : Color.clear))
            .frame(maxWidth: .infinity, alignment: mensch ? .trailing : .leading)
    }
}

private struct Vorschlagskarte: View {
    let karte: Assistentenkarte
    let gesperrt: Bool
    let anwenden: () -> Void
    let ablehnen: () -> Void
    let aendern: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Vorschlag:").font(.headline)
            ForEach(Array(karte.zeilen.enumerated()), id: \.offset) { _, zeile in
                Text("· " + zeile).fixedSize(horizontal: false, vertical: true)
            }
            if let zeit = karte.rechenzeit {
                Text(zeit).font(.callout).foregroundStyle(.secondary)
            }
            HStack(spacing: 8) {
                Button("Anwenden", action: anwenden)
                    .buttonStyle(Leistenknopf(betont: true))
                Button("Ablehnen", action: ablehnen)
                    .buttonStyle(Leistenknopf(betont: false))
                Button("Ändern", action: aendern)
                    .buttonStyle(Leistenknopf(betont: false))
            }
            .disabled(gesperrt)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: 10)
            .stroke(Assistentenfarbe.violett, lineWidth: 2))
    }
}

/// Ein Knopf mit **mindestens 44 pt** in beide Richtungen — selbst gezeichnet, weil die
/// Knopfformen von macOS ihre Höhe aus der Steuergrösse nehmen und 44 pt nicht erreichen.
private struct Leistenknopf: ButtonStyle {
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

private struct Grenzen: View {
    var body: some View {
        (Text(Assistentengrenzen.titel + ": ").bold() + Text(Assistentengrenzen.satz))
            .font(.callout)
            .foregroundStyle(.secondary)
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .overlay(RoundedRectangle(cornerRadius: 8)
                .stroke(style: StrokeStyle(lineWidth: 1, dash: [5, 4]))
                .foregroundStyle(.secondary))
    }
}

private struct Eingabe: View {
    @ObservedObject var modell: Assistentenmodell

    var body: some View {
        // NUR BEI «BEREIT» EIN FELD. Sonst ein ruhiger Satz: warum nicht, und dass Bilder
        // trotzdem gehen. Ein Feld, das nichts abschickt, waere ein Bedienelement ohne
        // Wirkung.
        if let zeile = modell.zeile, zeile.nimmtEingabe {
            HStack(alignment: .bottom, spacing: 8) {
                TextField("Schreiben, was das Bild zeigen soll …", text: $modell.eingabe,
                          axis: .vertical)
                    .lineLimit(1...4)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit { Task { await modell.sende() } }
                Button("Senden") { Task { await modell.sende() } }
                    .buttonStyle(Leistenknopf(betont: true))
                    .disabled(modell.gespraech.wartet
                              || modell.eingabe.trimmingCharacters(in: .whitespacesAndNewlines)
                                  .isEmpty)
            }
        } else {
            Text(modell.zeile?.satz ?? "Der Assistent wird am Heim-PC nachgesehen …")
                .font(.callout)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
        }
    }
}
