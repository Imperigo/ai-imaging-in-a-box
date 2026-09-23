import SwiftUI

/// Die Skizzen der Mappe — **offen, gerechnet oder verworfen** (Blatt «Skizzen») — mit den
/// Knöpfen «Rechnen lassen» und «Namen geben».
///
/// * **Nichts rechnet von selbst** (Entscheid 11): Eine abgelegte Skizze ist offen, bis hier
///   jemand «Rechnen lassen» wählt. Gerechnet wird in der Lesart, die oben im Seitenfeld
///   gewählt ist (Prüfen oder Entwerfen).
/// * **Bei «Drei Ebenen»** wählt man hier zwei oder drei offene Skizzen und rechnet sie als
///   **eine Reihe** (Entscheid 32, `Rechenbestellung.ebenenreihe`).
/// * **Ein Stand, den die App nicht kennt, bekommt keinen Knopf** — er steht roh da.
/// * «Zurückholen» für eine verworfene Skizze gibt es nicht: Der Server hat dafür keinen Weg
///   (Protokoll §3), und ein Knopf ohne Wirkung ist schlimmer als keiner.
///
/// *Gebaut, am Gerät unbestätigt (22.09.2026).*
struct Skizzenliste: View {
    @ObservedObject var mappe: Bildbandstand
    @ObservedObject var verbindung: Verbindungsstand

    @State private var rechnen: String?
    @State private var anweisung = ""
    @State private var benennen: String?
    @State private var neuerName = ""
    @State private var offenesBild: Bandbild?

    init(mappe: Bildbandstand = .gemeinsam, verbindung: Verbindungsstand = .gemeinsam) {
        self.mappe = mappe
        self.verbindung = verbindung
    }

    private var laeuft: Bool { verbindung.laufstand?.laeuft == true }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Abschnittstitel(text: "Skizzen")
                Spacer()
                if let s = mappe.skizzen {
                    Text("\(s.count) · \(s.filter { $0.stand == .offen }.count) offen")
                        .font(Schrift.zahl(12))
                        .foregroundStyle(Zeichenblatt.leise)
                }
            }
            if let skizzen = mappe.skizzen {
                if skizzen.isEmpty {
                    leise("Keine Skizze in der Mappe.")
                }
                ForEach(Array(skizzen.enumerated()), id: \.offset) { paar in
                    zeile(paar.element)
                }
                if mappe.variantenquelle == .ebenen {
                    reihenknopf
                }
            } else {
                // NICHT GELIEFERT IST NICHT LEER.
                leise("Die Skizzenliste der Mappe ist nicht geladen.")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .alert("Rechnen lassen", isPresented: rechnenOffen) {
            TextField("Was soll sich ändern?", text: $anweisung)
            Button("Rechnen") {
                if let name = rechnen { bestelle(.skizze(name, anweisung: sauber(anweisung))) }
                rechnen = nil
            }
            Button("Abbrechen", role: .cancel) { rechnen = nil }
        } message: {
            Text(mappe.bestellart == .entwerfen
                 ? "Als Entwurf: schnell, ohne Geometrieprüfung. Leer lassen, dann gilt die Bemerkung der Skizze."
                 : "Geprüft: mit Geometrieprüfung. Leer lassen, dann gilt die Bemerkung der Skizze.")
        }
        .alert("Namen geben", isPresented: benennenOffen) {
            TextField("Name", text: $neuerName)
            Button("Übernehmen") {
                if let name = benennen {
                    let titel = neuerName
                    Task { @MainActor in
                        mappe.sendet = true
                        mappe.quittung = await verbindung.benenne(skizze: name, titel: titel,
                                                                  bildband: mappe)
                        mappe.sendet = false
                    }
                }
                benennen = nil
            }
            Button("Abbrechen", role: .cancel) { benennen = nil }
        } message: {
            Text("Leer lassen, um den Namen zurückzunehmen. Die Datei behält ihren Namen.")
        }
        .fullScreenCover(item: $offenesBild) { b in
            Bildansicht(stand: mappe, bild: b) { offenesBild = nil }
        }
    }

    // ------------------------------------------------------------------ eine Zeile

    private func zeile(_ s: Mappenskizze) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(mappe.name(s))
                    .font(Schrift.text(15, .semibold))
                    .lineLimit(2)
                Spacer(minLength: 4)
                standwort(s)
            }
            Text(unterzeile(s))
                .font(Schrift.zahl(12))
                .foregroundStyle(Zeichenblatt.leise)
                .lineLimit(2)
            knoepfe(s)
        }
        .padding(12)
        .background(RoundedRectangle(cornerRadius: 10).fill(Zeichenblatt.feld))
        .overlay(RoundedRectangle(cornerRadius: 10)
            .strokeBorder(Zeichenblatt.linie, lineWidth: 1))
    }

    private func unterzeile(_ s: Mappenskizze) -> String {
        var teile: [String] = [s.skizze ?? "ohne Dateinamen"]
        if let ueber = s.ueber { teile.append("über " + ueber) } else { teile.append("auf leerem Grund") }
        if let b = s.bemerkung, !b.isEmpty { teile.append(b) }
        return teile.joined(separator: " · ")
    }

    /// Das Wort zum Stand. «Offen» im Gelb von «nicht gemessen» — das ist es auch: Es gibt
    /// noch kein Bild und darum kein Urteil. Gerechnet und verworfen tragen **keine**
    /// Urteilsfarbe; das Urteil trägt das Bild, nicht die Skizze.
    @ViewBuilder
    private func standwort(_ s: Mappenskizze) -> some View {
        switch s.stand {
        case .some(.offen):
            Text("offen")
                .font(Schrift.zahl(12, .medium))
                .foregroundStyle(Color(Zeichenart.nichtGemessen.schrift))
        case .some(.gerechnet):
            Text("gerechnet")
                .font(Schrift.zahl(12, .medium))
                .foregroundStyle(Zeichenblatt.schrift)
        case .some(.verworfen):
            Text("verworfen")
                .font(Schrift.zahl(12, .medium))
                .foregroundStyle(Zeichenblatt.leise)
        case .none:
            Text(s.standRoh.map { "Stand «\($0)» unbekannt" } ?? "Stand nicht geliefert")
                .font(Schrift.zahl(12, .medium))
                .foregroundStyle(Zeichenblatt.leise)
        }
    }

    @ViewBuilder
    private func knoepfe(_ s: Mappenskizze) -> some View {
        if let name = s.skizze {
            // ZWEI KNOEPFE JE REIHE: Im Seitenfeld (340 pt) hätten drei nebeneinander ihre
            // Wörter abgeschnitten.
            HStack(spacing: 8) {
                switch s.stand {
                case .some(.offen):
                    Button("Rechnen lassen") {
                        anweisung = ""
                        rechnen = name
                    }
                    .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil, hoehe: 44))
                    .disabled(!darfBestellen)
                    if mappe.variantenquelle == .ebenen {
                        let drin = mappe.reihe.contains(name)
                        Button(drin ? "In der Reihe" : "Zur Reihe") { mappe.schalteReihe(name) }
                            .buttonStyle(Wahlknopfstil(gewaehlt: drin, breite: nil, hoehe: 44))
                            .accessibilityAddTraits(drin ? .isSelected : [])
                    }
                case .some(.gerechnet):
                    if let ergebnis = s.ergebnis,
                       let b = mappe.bilder.first(where: { $0.bild == ergebnis }) {
                        Button("Bild ansehen") { offenesBild = b }
                            .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil, hoehe: 44))
                    }
                case .some(.verworfen):
                    leise("Bleibt als Spur, rechnet nicht mehr mit.")
                case .none:
                    EmptyView()
                }
            }
            HStack(spacing: 8) {
                Button("Namen geben") {
                    neuerName = s.titel ?? ""
                    benennen = name
                }
                .buttonStyle(Wahlknopfstil(gewaehlt: false, breite: nil, hoehe: 44))
                .disabled(mappe.sendet || !verbindung.gekoppelt)
            }
        } else {
            leise("Ohne Dateinamen lässt sich diese Skizze weder rechnen noch benennen.")
        }
    }

    // ------------------------------------------------------------- die Ebenen-Reihe

    private var reihenknopf: some View {
        VStack(alignment: .leading, spacing: 6) {
            Button("Als Ebenen-Reihe rechnen (\(mappe.reihe.count) von \(Rechenbestellung.reihenlaenge))") {
                bestelle(.ebenenreihe(mappe.reihe, anweisung: nil))
            }
            .buttonStyle(Wahlknopfstil(gewaehlt: true, breite: nil))
            // ZWEI BIS DREI: Eine «Reihe» aus einer Skizze wäre eine gewöhnliche Rechnung,
            // mehr als drei zeigt die Mappe nicht nebeneinander.
            .disabled(!darfBestellen || mappe.reihe.count < 2)
            leise("Je gewählte Skizze eine Variante; ohne Anweisung gilt je die Bemerkung der Skizze.")
        }
    }

    // ------------------------------------------------------------------ Handgriffe

    /// Bestellen geht nur gekoppelt, nicht während schon einer läuft (der Server nimmt nur
    /// einen Lauf zur Zeit) und nicht, während eine andere Handlung unterwegs ist.
    private var darfBestellen: Bool {
        verbindung.gekoppelt && !laeuft && !mappe.sendet
    }

    /// Bestellt und legt die Quittung ab. **Die Auswahl der Ebenen-Reihe wird erst nach der
    /// Quittung geleert, und nur, wenn die HomeStation angenommen hat** — bei «abgelehnt»,
    /// «ungewiss» und «nicht gesendet» bleibt sie stehen (Durchsicht der Verdrahtung,
    /// 22.09.2026: bis dahin wurde sie gleich nach dem Tippen geleert). **Und nur die Auswahl,
    /// die hinausging** (Durchsicht der Welle 2b, 23.09.2026): Bis dahin lief die Regel auf
    /// der Auswahl zur Zeit der Quittung, und wer während der Bestellung neu wählte, verlor
    /// die neue Wahl. Die Regel steht im Kern
    /// (`Rechenbestellung.reihe(_:gesendet:nach:)`) und ist dort geprüft; dass diese Ansicht
    /// sie mit der gesendeten Auswahl ruft, ist nicht übersetzt (23.09.2026) und am Gerät
    /// unbestätigt.
    private func bestelle(_ b: Rechenbestellung) {
        let lesart = mappe.bestellart
        Task { @MainActor in
            mappe.sendet = true
            let q = await verbindung.bestelle(b, lesart: lesart)
            mappe.quittung = q
            if case .ebenenreihe(let gesendet, _) = b {
                mappe.reihe = Rechenbestellung.reihe(mappe.reihe, gesendet: gesendet, nach: q)
            }
            mappe.sendet = false
        }
    }

    private func sauber(_ text: String) -> String? {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        return t.isEmpty ? nil : t
    }

    private var rechnenOffen: Binding<Bool> {
        Binding(get: { rechnen != nil }, set: { if !$0 { rechnen = nil } })
    }

    private var benennenOffen: Binding<Bool> {
        Binding(get: { benennen != nil }, set: { if !$0 { benennen = nil } })
    }

    private func leise(_ satz: String) -> some View {
        Text(satz)
            .font(Schrift.text(13))
            .foregroundStyle(Zeichenblatt.leise)
            .fixedSize(horizontal: false, vertical: true)
    }
}
