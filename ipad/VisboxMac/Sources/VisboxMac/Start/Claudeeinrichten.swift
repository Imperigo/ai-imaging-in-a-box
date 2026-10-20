import AppKit
import SwiftUI
import VisboxKern

/// **Einrichten › Claude über MCP** — Blatt 30, Feld 3 (KI-Bedienung Stufe 3; Entscheide 106,
/// 106e, 106f, 108 B).
///
/// * Schalter **an | aus** (`claudeMcp.an`, ab Werk an — 108 B) mit dem Zustand des Hörers.
/// * **Claude Code** — einmal im Terminal: `claude mcp add --transport http visbox
///   http://127.0.0.1:8631/mcp`, mit «Befehl kopieren».
/// * **Claude Desktop** — «Visbox hinzufügen» schreibt den Eintrag in dessen Einstellungsdatei
///   (`Visbox --mcp-stdio`, der Pfad dieser App); alles andere in der Datei bleibt.
/// * **Was Claude bekommt** (106f, wörtlich wie auf dem Blatt), **Werkzeuge**, und «Nur auf
///   diesem Mac. Kein Weg aus dem Internet.» (106e).
///
/// Die Sätze stehen im Kern (`Claudeeinrichtung`, `Claudedesktop`, mit Proben); hier wird nur
/// gezeichnet, kopiert und die Datei geschrieben.
///
/// *Gebaut, am Gerät unbestätigt (20.10.2026)* — hier nicht übersetzt, nur in der Prüfstrecke.
struct Claudeeinrichten: View {
    @ObservedObject var anschluss: Claudeanschluss
    let zurueck: () -> Void

    @State private var kopiert = false
    @State private var desktopSatz: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(Claudeeinrichtung.titel)
                .font(Macschriften.schrift(.titel, 26))
            Claudeschalter(anschluss: anschluss)
            Claudecodeblock(kopiert: $kopiert)
            Claudedesktopblock(satz: $desktopSatz)
            Claudeabsatz(titel: Claudeeinrichtung.datenTitel, text: Claudeeinrichtung.daten)
            Claudeabsatz(titel: Claudeeinrichtung.werkzeugeTitel, text: Claudeeinrichtung.werkzeuge)
            Text(Claudeeinrichtung.nurHier)
                .font(Macschriften.schrift(.text, 13, .semibold))
            HStack {
                Button("← Zurück", action: zurueck)
                    .buttonStyle(.link)
                Spacer()
            }
            .padding(.top, 6)
        }
        .padding(28)
        .frame(width: 560, alignment: .leading)
    }
}

/// «Claude über MCP  an | aus» und darunter, wie der Hörer steht.
private struct Claudeschalter: View {
    @ObservedObject var anschluss: Claudeanschluss

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Picker(Claudeeinrichtung.titel, selection: an) {
                Text("an").tag(true)
                Text("aus").tag(false)
            }
            .pickerStyle(.segmented)
            .frame(width: 200)
            Text(anschluss.lage.satz)
                .font(Macschriften.schrift(.text, 12))
                .foregroundStyle(Startfarbe.leise)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var an: Binding<Bool> {
        Binding(get: { anschluss.lage != .aus }, set: { anschluss.schalte($0) })
    }
}

private struct Claudecodeblock: View {
    @Binding var kopiert: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(Claudeeinrichtung.codeTitel)
                .font(Macschriften.schrift(.text, 13, .semibold))
            Text(Claudeeinrichtung.befehl)
                .font(Macschriften.schrift(.zahl, 12))
                .textSelection(.enabled)
                .padding(8)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(RoundedRectangle(cornerRadius: 6).fill(Startfarbe.flaeche))
            Button(kopiert ? "Kopiert" : Claudeeinrichtung.kopieren) {
                NSPasteboard.general.clearContents()
                NSPasteboard.general.setString(Claudeeinrichtung.befehl, forType: .string)
                kopiert = true
            }
        }
    }
}

/// «Claude Desktop: «Visbox hinzufügen» schreibt den Eintrag.»
private struct Claudedesktopblock: View {
    @Binding var satz: String?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(Claudedesktop.satz(programm: Claudedesktopdatei.programm))
                .font(Macschriften.schrift(.text, 13))
                .fixedSize(horizontal: false, vertical: true)
            Button("\(Marke.name) hinzufügen") { satz = Claudedesktopdatei.trageEin() }
            if let satz {
                Text(satz)
                    .font(Macschriften.schrift(.text, 12))
                    .foregroundStyle(Startfarbe.leise)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

private struct Claudeabsatz: View {
    let titel: String
    let text: String

    var body: some View {
        (Text(titel + " ").bold() + Text(text))
            .font(Macschriften.schrift(.text, 13))
            .fixedSize(horizontal: false, vertical: true)
    }
}

/// Die Einstellungsdatei von Claude Desktop — gelesen und geschrieben nur auf Knopfdruck.
enum Claudedesktopdatei {
    /// Der Pfad dieses Programms (im Bündel), den Claude Desktop mit `--mcp-stdio` startet.
    static var programm: String {
        Bundle.main.executablePath ?? "/Applications/\(Marke.name).app/Contents/MacOS/\(Marke.name)"
    }

    static var ort: URL? {
        FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first?
            .appendingPathComponent(Claudedesktop.datei)
    }

    /// Schreibt den Eintrag — **ohne etwas anderes in der Datei anzufassen** (`Claudedesktop.mische`).
    /// Ist Claude Desktop nicht eingerichtet (kein Ordner), entsteht nichts.
    static func trageEin() -> String {
        guard let ort else { return "Der Ordner für Claude Desktop liess sich nicht finden." }
        let ordner = ort.deletingLastPathComponent()
        guard FileManager.default.fileExists(atPath: ordner.path) else {
            return "Claude Desktop ist auf diesem Mac nicht eingerichtet — erst installieren und einmal öffnen."
        }
        let vorhanden = try? Data(contentsOf: ort)
        if Claudedesktop.traegt(vorhanden, programm: programm) {
            return "Der Eintrag steht schon. Claude Desktop neu starten, falls \(Marke.name) dort fehlt."
        }
        do {
            let neu = try Claudedesktop.mische(vorhanden: vorhanden, programm: programm)
            try neu.write(to: ort, options: .atomic)
            return "Eingetragen. Claude Desktop jetzt neu starten."
        } catch Claudedesktop.Fehler.unlesbar {
            return "Die Einstellungsdatei von Claude Desktop ist nicht lesbar — sie bleibt, wie sie ist."
        } catch {
            return "Der Eintrag liess sich nicht schreiben: \(error.localizedDescription)"
        }
    }
}
