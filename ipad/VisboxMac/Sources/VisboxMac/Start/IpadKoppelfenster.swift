import Combine
import CoreImage
import SwiftUI
import VisboxKern

/// Das Koppelfenster «iPad koppeln» (Entscheide 99/99a/99b, Blatt 27) — **drei Wege, eine
/// Zahl, zwei Minuten**:
///
/// * **Mac in der Nähe:** Solange das Fenster offen ist, bietet sich der Mac über
///   MultipeerConnectivity an (`Naeheanbieter`). Fragt ein iPad, steht hier «iPad möchte
///   koppeln» mit seinem Namen — erst «Koppeln» schickt Adresse und Zahl, nie das Kennwort.
/// * **QR-Code:** derselbe Koppelschein (`Koppelschein` im Kern) als Bild, mit CoreImage
///   erzeugt (`CIQRCodeGenerator`). Das iPad liest ihn mit der Kamera in der App.
/// * **Zahl und Adresse** zum Abtippen, als letzter Weg.
///
/// **Nach zwei Minuten hört es von selbst auf** (99a): Der QR-Code und die Zahl verschwinden,
/// der Mac bietet sich nicht mehr an, und die Zeile «iPad» sagt, dass das Fenster zu ist.
/// Wann das ist, sagt der Kern (`Koppelfenster`); hier läuft nur die Uhr.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026).*
struct IpadKoppelfenster: View {
    @ObservedObject var leitung: Heimleitung
    let schliessen: () -> Void

    @StateObject private var naehe = Naeheanbieter()
    @State private var fenster: Koppelfenster?
    @State private var schein: Koppelschein?
    @State private var qr: CGImage?
    @State private var satz: String?
    @State private var holt = false
    @State private var jetzt = Date()

    private let takt = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    private var offen: Bool {
        fenster?.offen(jetzt: jetzt.timeIntervalSince1970) ?? false
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("iPad koppeln")
                .font(Macschriften.schrift(.titel, 30))
            Text("Am iPad im Koppelbildschirm: den Mac in der Nähe annehmen, den QR-Code lesen "
                 + "oder Adresse und Zahl eintippen. Das Fenster gilt zwei Minuten.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)

            if let schein, let fenster, offen {
                HStack(alignment: .top, spacing: 24) {
                    qrteil
                    VStack(alignment: .leading, spacing: 14) {
                        zahlteil(schein, fenster)
                        naeheteil
                    }
                }
            } else if holt {
                ProgressView("Die Zahl kommt vom Heim-PC …")
            } else {
                Text(satz ?? Naehekopplung.satzFensterZu)
                    .font(Macschriften.schrift(.text, 14))
                    .foregroundStyle(satz == nil ? Startfarbe.leise : Startfarbe.rot)
                    .fixedSize(horizontal: false, vertical: true)
            }

            HStack {
                Spacer()
                if !offen && !holt {
                    Button("Neue Zahl holen") { Task { await oeffne() } }
                }
                Button("Schliessen", action: schliessen)
                    .keyboardShortcut(.cancelAction)
            }
        }
        .padding(28)
        .frame(width: 640)
        .task { await oeffne() }
        .onReceive(takt) { neu in
            jetzt = neu
            // DIE ZWEI MINUTEN SIND UM: aufhoeren, sich anzubieten — von selbst (99a).
            if fenster != nil, !offen { schliesseFenster() }
        }
        .onDisappear {
            naehe.halte()
            if fenster != nil { schliesseFenster() }
        }
    }

    // ------------------------------------------------------------------- Teile

    private var qrteil: some View {
        VStack(spacing: 8) {
            if let qr {
                // WEISSER GRUND MIT RUHEZONE: Auf dunklem Grund lesen viele Kameras den Code
                // nicht, und ohne Rand fehlt ihnen der Anfang.
                Image(decorative: qr, scale: 1)
                    .interpolation(.none)
                    .resizable()
                    .frame(width: 220, height: 220)
                    .padding(16)
                    .background(RoundedRectangle(cornerRadius: 10).fill(Color.white))
            } else {
                Text("Kein QR-Code — die Zahl eintippen.")
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
                    .frame(width: 252, height: 252)
            }
            Text("Mit QR-Code koppeln")
                .font(Macschriften.schrift(.text, 12))
                .foregroundStyle(Startfarbe.leise)
        }
    }

    private func zahlteil(_ schein: Koppelschein, _ fenster: Koppelfenster) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(Koppelfenster.uhrtext(fenster.rest(jetzt: jetzt.timeIntervalSince1970)))
                .font(Macschriften.schrift(.zahl, 13))
                .foregroundStyle(Startfarbe.gelb)
            Text(String(schein.zahl.ziffern.prefix(3)) + " " + String(schein.zahl.ziffern.suffix(3)))
                .font(Macschriften.schrift(.zahl, 40))
                .textSelection(.enabled)
            Text(Suche.eingabetext(schein.adresse))
                .font(Macschriften.schrift(.zahl, 13))
                .foregroundStyle(Startfarbe.hell)
                .textSelection(.enabled)
            Text("Zahl eintippen — Adresse und Zahl, einmal gültig.")
                .font(Macschriften.schrift(.text, 12))
                .foregroundStyle(Startfarbe.leise)
        }
    }

    @ViewBuilder
    private var naeheteil: some View {
        switch naehe.lage {
        case .aus:
            EmptyView()
        case .bietetAn(let name):
            Text("In der Nähe sichtbar als «\(name)». Am iPad annehmen.")
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
        case .ipadFragt(let name):
            VStack(alignment: .leading, spacing: 10) {
                Text("iPad möchte koppeln")
                    .font(Macschriften.schrift(.text, 16, .semibold))
                Text(name)
                    .font(Macschriften.schrift(.zahl, 14))
                Text("Koppeln schickt diesem iPad Adresse und Zahl — nie das Kennwort.")
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
                HStack {
                    Button("Ablehnen") { naehe.lehneAb() }
                    Button("Koppeln") { naehe.koppeln() }
                        .keyboardShortcut(.defaultAction)
                }
            }
            .padding(14)
            .background(RoundedRectangle(cornerRadius: 10).fill(Startfarbe.gruenGrund))
            .overlay(RoundedRectangle(cornerRadius: 10).stroke(Startfarbe.gruenRand))
        case .verbindet(let name):
            Text("Verbindet mit «\(name)» …")
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.gelb)
        case .gesendet(let name):
            Text("Adresse und Zahl sind bei «\(name)». Das iPad koppelt jetzt selbst mit dem "
                 + "Heim-PC.")
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.gruenText)
                .fixedSize(horizontal: false, vertical: true)
        case .fehler(let grund):
            Text(grund)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.rot)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // ---------------------------------------------------------------- Handeln

    /// Holt eine neue Zahl beim Heim-PC und öffnet das Fenster für zwei Minuten.
    @MainActor
    private func oeffne() async {
        guard !holt else { return }
        holt = true
        satz = nil
        let angebot = await leitung.koppleIPad()
        holt = false
        guard let angebot, let adresse = leitung.adresse else {
            satz = "Keine Zahl vom Heim-PC — der Grund steht in der Zeile «iPad»."
            return
        }
        let nun = Date()
        jetzt = nun
        let neu = Koppelfenster(jetzt: nun.timeIntervalSince1970, zahlGiltNoch: angebot.giltNoch)
        guard let s = neu.schein(adresse: adresse, zahl: angebot.zahl) else {
            satz = "Die Adresse des Heim-PC lässt sich dem iPad nicht weitergeben."
            return
        }
        fenster = neu
        schein = s
        qr = IpadKoppelfenster.qrBild(s.text)
        naehe.biete(s, fenster: neu)
    }

    /// Das Fenster ist zu: nichts mehr anbieten, nichts mehr zeigen.
    @MainActor
    private func schliesseFenster() {
        naehe.halte()
        fenster = nil
        schein = nil
        qr = nil
        leitung.setzeIpad(.wartet(satz: Naehekopplung.satzFensterZu))
    }

    /// Der QR-Code des Scheins — Fehlerkorrektur «M» (15 %), reicht für einen Bildschirm.
    static func qrBild(_ text: String) -> CGImage? {
        guard let filter = CIFilter(name: "CIQRCodeGenerator") else { return nil }
        filter.setValue(Data(text.utf8), forKey: "inputMessage")
        filter.setValue("M", forKey: "inputCorrectionLevel")
        guard let roh = filter.outputImage else { return nil }
        let gross = roh.transformed(by: CGAffineTransform(scaleX: 8, y: 8))
        return CIContext().createCGImage(gross, from: gross.extent)
    }
}
