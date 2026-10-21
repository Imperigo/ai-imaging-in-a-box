import SwiftUI
import VisboxKern

/// **Die Vermittlung (Strom B) an der Mac-App**: legt den `Vermittlungsdienst` an — mit dem
/// Heim-PC, sobald Adresse und Anmeldung da sind, **und seit Entscheid 118a auch ohne** (dann
/// bekommt das iPad die Mappe am Mac, und Rechnen sagt «kein Rechner eingerichtet») — und
/// meldet seine Lage als Zeile «iPad».
///
/// **Angeboten wird nur, wenn eingeschaltet** (Sicherheitsdurchsicht und Owner-Entscheid vom
/// 01.10.2026; `Vermittlergedaechtnis.angeboten`, Vorgabe aus): Der Dienst entsteht trotzdem,
/// damit das Menü «iPad» und die Zeile «aus — im Menü iPad einschalten …» da sind; im WLAN
/// zeigt er sich erst nach `schalteAnbieten(true)`.
///
/// Ein eigener kleiner Halter, weil der Dienst erst entstehen kann, wenn der Mac eingerichtet
/// ist — und neu entstehen muss, wenn Adresse oder Kennwort wechseln: Er trägt die Anmeldung
/// zum Heim-PC fest in sich.
///
/// *Gebaut, am Gerät unbestätigt (01.10.2026).*
@MainActor
final class Vermittlungsanschluss: ObservableObject {
    @Published private(set) var dienst: Vermittlungsdienst?
    /// Ob «iPad über diesen Mac anbieten» an ist — für den Schalter im Menü «iPad».
    @Published private(set) var angeboten = Vermittlergedaechtnis.angeboten
    /// Für welchen Heim-PC der Dienst steht — `nil` (bei vorhandenem Dienst): für keinen.
    private var fuer: (URL, Anmeldung)?

    /// Den Dienst anlegen oder, wenn er schon passt, lassen — **zum eingerichteten Heim-PC oder,
    /// ohne ihn, ohne Heim-PC** (Entscheid 118a: die Verbindung iPad–Mac geht auch ohne). Wechselt
    /// der Heim-PC (eingerichtet, neue Adresse, neues Kennwort), entsteht ein neuer Dienst, denn
    /// er trägt die Anmeldung fest in sich. Er bietet sich nur an, wenn `angeboten`.
    func richteAus(adresse: URL?, anmeldung: Anmeldung?) {
        var ziel: (URL, Anmeldung)?
        if let adresse, let anmeldung { ziel = (adresse, anmeldung) }
        if dienst != nil, ziel?.0 == fuer?.0, ziel?.1 == fuer?.1 { return }
        dienst?.halte()
        let neu = Vermittlungsdienst(heim: ziel.map { Heimstrecke(basis: $0.0, anmeldung: $0.1) })
        if angeboten { neu.starte() }
        dienst = neu
        fuer = ziel
    }

    /// **«iPad über diesen Mac anbieten» ein- oder ausschalten** — gemerkt über den Neustart
    /// hinaus. Gehört als Schalter ins Menü «iPad» der Mac-App.
    func schalteAnbieten(_ an: Bool) {
        angeboten = an
        Vermittlergedaechtnis.angeboten = an
        guard let dienst else { return }
        // EINE ZAHL NUR BEIM EINSCHALTEN VON HAND (20.10.2026) — nicht bei jedem Start der App.
        if an { dienst.starte(mitZahl: true) } else { dienst.schalteAus() }
    }

    func halte() {
        dienst?.halte()
    }

    /// **Für «iPad koppeln» (Entscheid 118):** Das iPad arbeitet immer über den Mac — darum
    /// schaltet das Koppelfenster das Anbieten ein (verschlüsselt) und lässt es an. Eine Zahl
    /// holt sich das Fenster danach selbst (`zahlFuersKoppelfenster`). `nil` nur, solange die
    /// App den Dienst noch nicht angelegt hat (vor dem ersten `richteAus`) — seit Entscheid 118a
    /// gibt es ihn auch ohne Heim-PC.
    func dienstZumKoppeln() -> Vermittlungsdienst? {
        guard let dienst else { return nil }
        if !angeboten {
            angeboten = true
            Vermittlergedaechtnis.angeboten = true
        }
        // HINTER DEM MERKER, wie jeder Start (die Probe `test_der_mac_bietet_sich_nur_an_wenn_
        // eingeschaltet`): eingeschaltet hat ihn eben das Koppelfenster.
        if angeboten { dienst.starte() }
        return dienst
    }
}

/// Unsichtbar: reicht jede neue Lage des Dienstes als Zeile «iPad» an die Heimleitung.
struct Vermittlungsmelder: View {
    @ObservedObject var dienst: Vermittlungsdienst
    let leitung: Heimleitung

    var body: some View {
        Color.clear
            .frame(width: 0, height: 0)
            .onAppear { leitung.setzeVermittlung(dienst.zeile) }
            .onChange(of: dienst.zeile) { _, neu in
                leitung.setzeVermittlung(neu)
            }
            // AUSGESCHALTET ODER WEG: Die Zeile gehört wieder Gerätebuch und Koppelfenster.
            .onDisappear { leitung.setzeVermittlung(nil) }
    }
}
