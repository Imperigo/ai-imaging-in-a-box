import SwiftUI

/// Ein Feld, das eine spätere Einheit füllt — **und es sagt das auch.**
///
/// Ein leerer Bereich sähe aus wie ein Fehler der Anzeige; ein Bereich mit einem
/// erfundenen Inhalt sähe aus wie ein fertiger. Der Platzhalter nennt, was hier kommen
/// wird, und behauptet nichts darüber hinaus.
struct Platzhalter: View {
    let titel: String
    let satz: String

    var body: some View {
        VStack(spacing: 8) {
            Text(titel)
                .font(.headline)
            Text(satz)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.secondary.opacity(0.06))
        .accessibilityElement(children: .combine)
    }
}
