import SwiftUI

/// Der Einstieg der App. Er tut nichts, als die Startansicht zu zeigen.
///
/// **Die App rechnet nie selbst.** Alles, was ein Urteil, ein Bild oder eine Zahl ist,
/// kommt vom Server auf der HomeStation (`oberflaeche/server.py`). Stünde hier eine
/// Schwelle oder eine Umrechnung, gäbe es dieselbe Fähigkeit an zwei Stellen — und eine
/// davon ohne Python erreichbar, gegen Regel 4.
@main
struct VisboxApp: App {
    var body: some Scene {
        WindowGroup {
            Startansicht()
        }
    }
}
