import AppKit
import SwiftUI
#if canImport(VisboxKern)
// DER KERN ALS MODUL ODER MITUEBERSETZT: Bindet die Mac-App `VisboxKern` als Paket ein, ist
// er ein Modul; liegen seine Quellen im selben Ziel (wie in der iPad-App), gibt es keines,
// und die Typen sind ohnehin sichtbar. Diese Zeile haelt beide Wege offen, bis Strom A
// entschieden hat. Im Kern selbst ist `canImport` verboten (`tests/test_ipad_geruest.py`),
// hier nicht — das ist die App-Schicht.
import VisboxKern
#endif

/// **Der Vorführmodus am Mac** — Blatt 13b der Entwurfsfläche (Entscheid 40).
///
/// Der Heim-PC antwortet nicht; gezeigt werden Bilder, die vorher gerechnet wurden, jedes mit
/// seinem Prüfzeichen **und dem Tag, an dem es gerechnet wurde**. Neu rechnen ist gesperrt,
/// und rechts steht, was nicht geht und warum.
///
/// Diese Ansicht entscheidet nichts. Das Zeichen, das Fussband, die Zeile unter dem Bild und
/// jeder Satz kommen aus dem Kern (`Vorfuehrmappe`, `Vorfuehrbild`, `Vorfuehrsaetze`,
/// `Vorfuehrfarbe`) und sind dort unter Linux geprüft; hier wird nur abgemalt.
///
/// **Unübersetzt** (Linux, 01.10.2026): Ob sie auf macOS 14 übersetzt und wie das Blatt
/// aussieht, zeigt erst die Mac-Prüfstrecke bzw. der Mac.
public struct Vorfuehransicht: View {
    public let mappe: Vorfuehrmappe
    /// Der Ordner der Mappe — die Bilder liegen darin unter ihrem Dateinamen.
    public let ordner: URL
    /// Seit wann der Heim-PC nicht antwortet (`Vorfuehrschalter.seit`).
    public let seit: Date
    /// Wann zuletzt ein Versuch zurückkam (`Vorfuehrschalter.letzterVersuch`).
    public let letzterVersuch: Date?
    public let ipadVerbunden: Bool
    public let erneutVerbinden: () -> Void

    public init(mappe: Vorfuehrmappe, ordner: URL, seit: Date, letzterVersuch: Date?,
                ipadVerbunden: Bool, erneutVerbinden: @escaping () -> Void) {
        self.mappe = mappe
        self.ordner = ordner
        self.seit = seit
        self.letzterVersuch = letzterVersuch
        self.ipadVerbunden = ipadVerbunden
        self.erneutVerbinden = erneutVerbinden
    }

    public var body: some View {
        // EINMAL JE SEKUNDE NEU GEZEICHNET, damit «Letzter Versuch vor 20 s» weiterzählt.
        // Gezählt wird nur die Anzeige — der Schalter rückt seine Zeit selbst vor.
        TimelineView(.periodic(from: .now, by: 1)) { kontext in
            VStack(alignment: .leading, spacing: 0) {
                kopf
                band
                HStack(alignment: .top, spacing: 28) {
                    ScrollView { mappenteil.padding(.bottom, 24) }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    seitenspalte(jetzt: kontext.date)
                        .frame(width: 300, alignment: .leading)
                }
                .padding(24)
            }
        }
        .frame(minWidth: 900, minHeight: 600, alignment: .topLeading)
        .background(Color(vorfuehr: Blattfarbe.grund))
        .foregroundStyle(Color(vorfuehr: Blattfarbe.schrift))
    }

    private var zone: TimeZone { .current }

    // ------------------------------------------------------------------- Kopf

    private var kopf: some View {
        HStack(spacing: 12) {
            // DER NAME AUS DER MARKE, nie als Zeichenkette (`Marke.swift`, bewacht in
            // `tests/test_ipad_geruest.py`): Nach der Umbenennung in KosmoSketch stuende er
            // sonst hier noch.
            Text("\(Marke.name) · am Mac · unterwegs")
                .font(Vorfuehrschrift.titel(22))
            Text(Vorfuehrsaetze.plakette)
                .font(Vorfuehrschrift.zahl(12, .medium))
                .foregroundStyle(Color(vorfuehr: Vorfuehrfarbe.violett))
                .padding(.horizontal, 10)
                .padding(.vertical, 3)
                .background(Capsule().fill(Color(vorfuehr: Vorfuehrfarbe.grund)))
                .overlay(Capsule().strokeBorder(Color(vorfuehr: Vorfuehrfarbe.rand), lineWidth: 1))
            Spacer()
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 14)
    }

    // ------------------------------------------------------------------- Band

    private var band: some View {
        HStack(alignment: .center, spacing: 14) {
            Text(Vorfuehrsaetze.bandWort)
                .font(Vorfuehrschrift.zahl(13, .semibold))
                .foregroundStyle(Color(vorfuehr: Vorfuehrfarbe.violett))
            Text(Vorfuehrsaetze.band(seit: seit, zone: zone))
                .font(Vorfuehrschrift.text(14))
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 12)
            Button(Vorfuehrsaetze.erneutVerbinden, action: erneutVerbinden)
                .buttonStyle(.bordered)
                .tint(Color(vorfuehr: Vorfuehrfarbe.violett))
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 12)
        .background(Color(vorfuehr: Vorfuehrfarbe.grund))
        .overlay(alignment: .top) { Rectangle().fill(Color(vorfuehr: Vorfuehrfarbe.rand)).frame(height: 1) }
        .overlay(alignment: .bottom) { Rectangle().fill(Color(vorfuehr: Vorfuehrfarbe.rand)).frame(height: 1) }
    }

    // ----------------------------------------------------------------- Mappe

    private var mappenteil: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(mappe.titel)
                .font(Vorfuehrschrift.titel(30))
            Text(mappe.kopfzeile)
                .font(Vorfuehrschrift.text(13))
                .foregroundStyle(Color(vorfuehr: Blattfarbe.leise))
            if mappe.platzhalter {
                // PLATZHALTER SAGEN ES, und zwar oben und an jedem Bild: Ein graues Bild mit
                // «BESTANDEN» darunter laese sich sonst wie ein gemessenes.
                Text(Vorfuehrsaetze.platzhalterKasten)
                    .font(Vorfuehrschrift.text(13))
                    .foregroundStyle(Color(vorfuehr: Vorfuehrfarbe.violett))
                    .fixedSize(horizontal: false, vertical: true)
            }
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 16, alignment: .top),
                                     count: 3),
                      alignment: .leading, spacing: 20) {
                ForEach(mappe.bilder) { bild in
                    Vorfuehrkachel(bild: bild, adresse: Vorfuehrmappe.adresse(bild, in: ordner))
                }
            }
            .padding(.top, 6)
            rechnenzeile
                .padding(.top, 10)
        }
    }

    private var rechnenzeile: some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Text(Vorfuehrsaetze.rechnenTitel)
                .font(Vorfuehrschrift.text(14, .medium))
            // GESPERRT UND SICHTBAR: Ein fehlender Knopf sagte nicht, dass es ihn gibt und
            // warum er gerade nicht geht.
            Button(Vorfuehrsaetze.rechnenKnopf) {}
                .disabled(true)
            Text(Vorfuehrsaetze.rechnenSatz)
                .font(Vorfuehrschrift.text(13))
                .foregroundStyle(Color(vorfuehr: Blattfarbe.leise))
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // ------------------------------------------------------------ Seitenspalte

    private func seitenspalte(jetzt: Date) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Text(Vorfuehrsaetze.spaltenTitel)
                .font(Vorfuehrschrift.titel(20))
            punkt(Vorfuehrfarbe.gehtNicht,
                  Vorfuehrsaetze.leitung(seit: seit, letzterVersuch: letzterVersuch,
                                         jetzt: jetzt, zone: zone))
            punkt(Vorfuehrfarbe.gehtNicht, Vorfuehrsaetze.assistent)
            punkt(ipadVerbunden ? Vorfuehrfarbe.geht : Vorfuehrfarbe.gehtNicht,
                  ipadVerbunden ? Vorfuehrsaetze.ipadVerbunden : Vorfuehrsaetze.ipadNichtVerbunden)
            Text(Vorfuehrsaetze.kasten)
                .font(Vorfuehrschrift.text(13))
                .fixedSize(horizontal: false, vertical: true)
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(vorfuehr: Vorfuehrfarbe.grund))
                .overlay(Rectangle().strokeBorder(Color(vorfuehr: Vorfuehrfarbe.rand), lineWidth: 1))
                .padding(.top, 6)
        }
    }

    private func punkt(_ ton: Farbton, _ satz: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(Color(vorfuehr: ton))
                .frame(width: 8, height: 8)
                .padding(.top, 5)
                .accessibilityHidden(true)
            Text(satz)
                .font(Vorfuehrschrift.text(13))
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

/// Ein Bild der Vorführmappe: Rahmen und Fussband in der Farbe seines Zeichens, darunter
/// Unterschrift und Tag des Rechnens.
struct Vorfuehrkachel: View {
    let bild: Vorfuehrbild
    /// `nil`: Die Datei fehlt — dann steht ihr Platz mit dem Satz da, nicht nichts.
    let adresse: URL?
    @State private var grafik: NSImage?

    var body: some View {
        let zeichen = bild.zeichen
        VStack(alignment: .leading, spacing: 6) {
            Color(vorfuehr: Blattfarbe.kachel)
                .aspectRatio(3.0 / 2.0, contentMode: .fit)
                .overlay {
                    if let grafik {
                        Image(nsImage: grafik)
                            .resizable()
                            .scaledToFill()
                    } else if adresse == nil {
                        Text(bild.fehltSatz)
                            .font(Vorfuehrschrift.text(12))
                            .foregroundStyle(Color(vorfuehr: Blattfarbe.leise))
                            .multilineTextAlignment(.center)
                            .padding(12)
                    }
                }
                .overlay(alignment: .bottom) {
                    Text(bild.fussband)
                        .font(Vorfuehrschrift.zahl(11, .medium))
                        .foregroundStyle(Color(vorfuehr: zeichen.art.schrift))
                        .lineLimit(1)
                        .truncationMode(.tail)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 5)
                        .background(Color(vorfuehr: Pruefzeichen.streifen)
                            .opacity(Pruefzeichen.streifenDeckung))
                }
                .clipped()
                // GESTRICHELT HEISST: HIER IST NICHTS GEMESSEN — auch von weitem und ohne
                // Farbensehen (`Zeichenart.gestrichelt`).
                .overlay(
                    Rectangle().strokeBorder(
                        Color(vorfuehr: zeichen.art.rand),
                        style: StrokeStyle(lineWidth: 2, dash: zeichen.art.gestrichelt ? [6, 4] : []))
                )
            Text(bild.unterzeile)
                .font(Vorfuehrschrift.text(12))
                .foregroundStyle(Color(vorfuehr: Blattfarbe.leise))
                .fixedSize(horizontal: false, vertical: true)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(bild.vorlesetext)
        .help(bild.satz ?? bild.unterzeile)
        .task(id: adresse) { await lade() }
    }

    /// Die Bytes abseits der Hauptschleife lesen, das Bild auf ihr bauen.
    @MainActor
    private func lade() async {
        guard let url = adresse else {
            grafik = nil
            return
        }
        let daten = await Task.detached(priority: .utility) { try? Data(contentsOf: url) }.value
        grafik = daten.flatMap { NSImage(data: $0) }
    }
}

// ============================================================ Farben und Schriften

extension Color {
    /// Ein Farbton des Kerns als Farbe. **Mit eigenem Etikett** (`vorfuehr:`), damit es nicht
    /// mit einer gleichnamigen Umwandlung zusammenstösst, die die Mac-App selbst anlegt.
    init(vorfuehr ton: Farbton) {
        self.init(.sRGB, red: Double(ton.rot) / 255, green: Double(ton.gruen) / 255,
                  blue: Double(ton.blau) / 255, opacity: 1)
    }
}

/// Die Schriften des Vorführmodus — **eine Stelle**, und sie fragt das Register der Mac-App
/// (`Macschriften`, Strom A): IBM Plex Sans, IBM Plex Mono und Instrument Serif, wenn sie im
/// Bündel liegen und registriert sind, sonst die Formen des Systems. Umgestellt beim
/// Zusammenführen am 01.10.2026; bis dahin standen hier nur die Systemformen.
enum Vorfuehrschrift {
    static func titel(_ groesse: CGFloat) -> Font {
        Macschriften.schrift(.titel, groesse)
    }

    static func text(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        Macschriften.schrift(.text, groesse, gewicht)
    }

    static func zahl(_ groesse: CGFloat, _ gewicht: Font.Weight = .regular) -> Font {
        Macschriften.schrift(.zahl, groesse, gewicht)
    }
}
