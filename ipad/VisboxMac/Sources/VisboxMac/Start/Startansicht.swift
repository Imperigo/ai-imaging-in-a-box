import SwiftUI
import VisboxKern

/// Der Start am Mac nach **Blatt 13** (Entscheid 38): links die vier Zeilen, rechts «Wer
/// rechnet wo», unten «Schon anfangen».
///
/// Die Ansicht zeigt nur. Welche Zeile was sagt, steht in `Startbild` (Kern); wann gefragt
/// wird, in `Heimleitung`. Nichts davon muss man anklicken — der einzige Knopf ist
/// «Schon anfangen», und der geht, sobald die Leitung steht (Entscheid 39).
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
struct Startansicht: View {
    @ObservedObject var leitung: Heimleitung
    let anfangen: () -> Void
    let einrichten: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Startkopf(bild: leitung.bild, einrichten: einrichten)
            HStack(spacing: 0) {
                zeilenseite
                    .frame(width: 620)
                    .background(Startfarbe.flaeche)
                Rectangle().fill(Startfarbe.linie).frame(width: 1)
                WerrechnetWo()
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            }
        }
        .background(Startfarbe.grund)
        .foregroundStyle(Startfarbe.text)
    }

    private var zeilenseite: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("\(Marke.name) baut die Verbindungen auf.")
                .font(Macschriften.schrift(.titel, 38))
            Text("Nichts davon muss man anklicken. Jede Zeile sagt, was sie gerade tut — und "
                 + "wenn eine nicht ankommt, warum.")
                .font(Macschriften.schrift(.text, 15))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)

            // JEDE SEKUNDE NEU GEZEICHNET, damit «seit 12 s» zaehlt — gefragt wird dadurch
            // nicht oefter; das bestimmt allein der Takt der Heimleitung.
            TimelineView(.periodic(from: .now, by: 1)) { zeit in
                VStack(spacing: 12) {
                    ForEach(Startzeile.allCases, id: \.self) { zeile in
                        Zeilenkarte(zeile: zeile, stand: leitung.bild[zeile], jetzt: zeit.date)
                    }
                }
            }
            .padding(.top, 10)

            if let satz = leitung.schluesselbundSatz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.rot)
            }

            Spacer(minLength: 0)

            HStack(alignment: .center, spacing: 12) {
                Button(action: anfangen) {
                    Text("Schon anfangen")
                        .font(Macschriften.schrift(.text, 15, .semibold))
                        .padding(.horizontal, 20)
                        .frame(minHeight: 44)
                        .background(RoundedRectangle(cornerRadius: 10)
                            .fill(leitung.bild.schonAnfangen ? Startfarbe.gruenKnopf
                                  : Startfarbe.karte))
                        .overlay(RoundedRectangle(cornerRadius: 10)
                            .stroke(leitung.bild.schonAnfangen ? Startfarbe.gruen
                                    : Startfarbe.linie, lineWidth: 1))
                }
                .buttonStyle(.plain)
                .disabled(!leitung.bild.schonAnfangen)
                .keyboardShortcut(.defaultAction)

                Text(leitung.bild.anfangenSatz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(.horizontal, 36)
        .padding(.vertical, 40)
        .frame(maxHeight: .infinity, alignment: .topLeading)
    }
}

// ===================================================================== der Kopf

/// Name, «am Mac · unterwegs», und rechts die gezählte Kopfzeile («baut auf · 2 von 4»).
struct Startkopf: View {
    let bild: Startbild
    let einrichten: () -> Void

    /// Die Farbe der Kopfzeile folgt ihrem Wort (`Startbild.kopfzeile`): grün «bereit», rot
    /// «unvollständig», gelb und atmend «baut auf», grau «wartet».
    private var gesamt: Zeilenstand {
        if bild.stehend == bild.zeilen.count { return .steht(satz: bild.kopfzeile) }
        if bild.zeilen.contains(where: { $0.stand.fehlt }) { return .fehlt(grund: bild.kopfzeile) }
        if bild.zeilen.contains(where: { $0.stand.laedt }) {
            return .laedt(seit: .distantPast, satz: bild.kopfzeile)
        }
        return .wartet(satz: bild.kopfzeile)
    }

    var body: some View {
        let farbe = Startfarbe.zeile(gesamt)
        HStack(spacing: 16) {
            Text(Marke.name)
                .font(Macschriften.schrift(.titel, 25))
            Rectangle().fill(Startfarbe.linie).frame(width: 1, height: 24)
            Text("am Mac · unterwegs")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
            Spacer()
            Button("Einrichten", action: einrichten)
                .buttonStyle(.plain)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
            HStack(spacing: 10) {
                Atmen(farbe: farbe.akzent, aktiv: gesamt.laedt)
                    .frame(width: 8, height: 8)
                Text(bild.kopfzeile)
                    .font(Macschriften.schrift(.text, 14))
            }
            .foregroundStyle(farbe.satz)
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Capsule().fill(farbe.grund))
            .overlay(Capsule().stroke(farbe.rand,
                                      style: StrokeStyle(lineWidth: 1,
                                                         dash: farbe.gestrichelt ? [4, 3] : [])))
        }
        .padding(.horizontal, 22)
        .frame(height: 60)
        .background(Startfarbe.flaeche)
        .overlay(Rectangle().fill(Startfarbe.linie).frame(height: 1), alignment: .bottom)
    }
}

// ===================================================================== eine Zeile

/// Eine der vier Zeilen: Zeichen, Titel, Satz, und rechts das eine Wort.
struct Zeilenkarte: View {
    let zeile: Startzeile
    let stand: Zeilenstand
    let jetzt: Date

    var body: some View {
        let farbe = Startfarbe.zeile(stand)
        HStack(spacing: 14) {
            Zeilenzeichen(stand: stand)
                .frame(width: 28, height: 28)
            VStack(alignment: .leading, spacing: 3) {
                Text(zeile.titel)
                    .font(Macschriften.schrift(.text, 16, .semibold))
                Text(satz)
                    .font(Macschriften.schrift(.text, 13))
                    .foregroundStyle(farbe.satz)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 8)
            Text(stand.wort)
                .font(Macschriften.schrift(.zahl, 12))
                .foregroundStyle(farbe.satz)
        }
        .padding(16)
        .background(RoundedRectangle(cornerRadius: 12).fill(farbe.grund))
        .overlay(RoundedRectangle(cornerRadius: 12)
            .stroke(farbe.rand, style: StrokeStyle(lineWidth: 1,
                                                   dash: farbe.gestrichelt ? [5, 4] : [])))
        // EINE ZEILE, EIN SATZ fuer VoiceOver — nicht vier Bruchstuecke.
        .accessibilityElement(children: .combine)
    }

    /// Der Satz, bei «lädt» mit der Dauer («· seit 12 s»).
    private var satz: String {
        if case .laedt(let seit, _) = stand {
            return stand.satz + " · " + Startzeilen.seitText(seit, jetzt: jetzt)
        }
        return stand.satz
    }
}

/// Das Zeichen links: gefüllter Kreis mit Haken (steht), atmender Ring (lädt), leerer Ring
/// (wartet), Kreis mit Ausrufezeichen (fehlt).
struct Zeilenzeichen: View {
    let stand: Zeilenstand

    var body: some View {
        let farbe = Startfarbe.zeile(stand).akzent
        switch stand {
        case .steht:
            Circle().fill(farbe)
                .overlay(Image(systemName: "checkmark")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Startfarbe.grund))
        case .laedt:
            Atmen(farbe: farbe, aktiv: true, ring: true)
        case .wartet:
            Circle().strokeBorder(farbe, lineWidth: 2)
        case .fehlt:
            Circle().fill(farbe)
                .overlay(Image(systemName: "exclamationmark")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(Startfarbe.grund))
        }
    }
}

/// Ein Punkt oder Ring, der atmet (1,8 s, wie auf dem Blatt) — still, wenn das System
/// «Bewegung reduzieren» verlangt.
struct Atmen: View {
    let farbe: Color
    let aktiv: Bool
    var ring = false
    @State private var hell = false
    @Environment(\.accessibilityReduceMotion) private var ruhig

    var body: some View {
        Group {
            if ring {
                Circle().strokeBorder(farbe, lineWidth: 2)
            } else {
                Circle().fill(farbe)
            }
        }
        .opacity(aktiv && !ruhig ? (hell ? 1 : 0.35) : 1)
        .onAppear {
            guard aktiv, !ruhig else { return }
            withAnimation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true)) {
                hell = true
            }
        }
    }
}

// ================================================================ wer rechnet wo

/// Die rechte Seite von Blatt 13: wer was tut, und der Satz zum ersten Öffnen.
struct WerrechnetWo: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 22) {
            Text("WER RECHNET WO")
                .font(Macschriften.schrift(.text, 12, .semibold))
                .kerning(1)
                .foregroundStyle(Startfarbe.leise)

            HStack(spacing: 18) {
                kasten("iPad", "zeichnet und zeigt", hervor: false, breite: 170)
                strich(gestrichelt: true)
                kasten("Mac", "Oberfläche, Vermittler fürs iPad", hervor: true, breite: 190)
                strich(gestrichelt: false)
                kasten("Heim-PC", "Blender, Bildmodell, Prüfung, Sprachmodell", hervor: true,
                       breite: 190)
            }

            Text("Gerechnet wird nie auf dem Mac und nie auf dem iPad. Der Mac trägt die Leitung "
                 + "nach Hause und reicht das iPad durch — dafür muss das iPad nur ins selbe "
                 + "WLAN wie der Mac, nicht ins Heimnetz.")
                .font(Macschriften.schrift(.text, 14))
                .foregroundStyle(Startfarbe.leise)
                .lineSpacing(4)
                .padding(.horizontal, 20)
                .padding(.vertical, 18)
                .frame(maxWidth: 700, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 12).fill(Startfarbe.flaeche))
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(Startfarbe.linie))

            Spacer(minLength: 0)

            VStack(alignment: .leading, spacing: 8) {
                Text("BEIM ERSTEN ÖFFNEN, EINMAL")
                    .font(Macschriften.schrift(.text, 12, .semibold))
                    .kerning(1)
                    .foregroundStyle(Startfarbe.leise)
                // MACOS 15: «Rechtsklick → Öffnen» genuegt nicht mehr (Korrektur zu Entscheid
                // 36, 01.10.2026). Der Satz steht auch im LIESMICH.
                Text("\(Marke.name) einmal öffnen — ohne Apple-Konto hält der Mac es an. Dann "
                     + "Systemeinstellungen → Datenschutz & Sicherheit → «Trotzdem öffnen». "
                     + "Danach öffnet es wie jedes Programm.")
                    .font(Macschriften.schrift(.text, 14))
                    .foregroundStyle(Startfarbe.hell)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 16)
            .frame(maxWidth: 700, alignment: .leading)
            .background(RoundedRectangle(cornerRadius: 12).fill(Startfarbe.flaeche))
            .overlay(RoundedRectangle(cornerRadius: 12)
                .stroke(Startfarbe.ring, style: StrokeStyle(lineWidth: 1, dash: [5, 4])))
        }
        .padding(40)
    }

    private func kasten(_ titel: String, _ satz: String, hervor: Bool,
                        breite: CGFloat) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(titel).font(Macschriften.schrift(.text, 16, .semibold))
            Text(satz)
                .font(Macschriften.schrift(.text, 13))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(18)
        .frame(width: breite, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 14)
            .fill(hervor ? Startfarbe.gruenKnopf : Startfarbe.karte))
        .overlay(RoundedRectangle(cornerRadius: 14)
            .stroke(hervor ? Startfarbe.gruen : Startfarbe.linie))
    }

    private func strich(gestrichelt: Bool) -> some View {
        Path { p in
            p.move(to: CGPoint(x: 0, y: 1))
            p.addLine(to: CGPoint(x: 90, y: 1))
        }
        .stroke(gestrichelt ? Startfarbe.ring : Startfarbe.gruen,
                style: StrokeStyle(lineWidth: 2, dash: gestrichelt ? [5, 5] : []))
        .frame(width: 90, height: 2)
    }
}
