import SwiftUI
import VisboxKern

/// **Die Vermittlung (Strom B) an der Mac-App**: legt den `Vermittlungsdienst` an, sobald
/// Adresse und Anmeldung des Heim-PC da sind, und meldet seine Lage als Zeile «iPad».
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
    private var fuer: (URL, Anmeldung)?

    /// Den Dienst zum eingerichteten Heim-PC anlegen oder, wenn er schon passt, lassen.
    /// Er bietet sich nur an, wenn `angeboten`.
    func richteAus(adresse: URL?, anmeldung: Anmeldung?) {
        guard let adresse, let anmeldung else {
            dienst?.halte()
            dienst = nil
            fuer = nil
            return
        }
        if let f = fuer, f.0 == adresse, f.1 == anmeldung { return }
        dienst?.halte()
        let neu = Vermittlungsdienst(heimBasis: adresse, benutzer: anmeldung.benutzer,
                                     kennwort: anmeldung.kennwort)
        if angeboten { neu.starte() }
        dienst = neu
        fuer = (adresse, anmeldung)
    }

    /// **«iPad über diesen Mac anbieten» ein- oder ausschalten** — gemerkt über den Neustart
    /// hinaus. Gehört als Schalter ins Menü «iPad» der Mac-App.
    func schalteAnbieten(_ an: Bool) {
        angeboten = an
        Vermittlergedaechtnis.angeboten = an
        guard let dienst else { return }
        if an { dienst.starte() } else { dienst.schalteAus() }
    }

    func halte() {
        dienst?.halte()
    }
}

/// Unsichtbar: reicht jede neue Lage des Dienstes als Zeile «iPad» an die Heimleitung.
struct Vermittlungsmelder: View {
    @ObservedObject var dienst: Vermittlungsdienst
    let leitung: Heimleitung

    var body: some View {
        Color.clear
            .frame(width: 0, height: 0)
            .onAppear { leitung.setzeIpad(dienst.zeile.alsZeilenstand()) }
            .onChange(of: dienst.zeile) { _, neu in
                leitung.setzeIpad(neu.alsZeilenstand())
            }
    }
}
