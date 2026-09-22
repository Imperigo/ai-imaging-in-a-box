// swift-tools-version:5.9
//
// DER KERN DER IPAD-APP — nur Foundation, darum auch unter Linux pruefbar.
//
// Die Quellen liegen NICHT hier, sondern im App-Paket (`../Visbox.swiftpm/Kern`);
// `Sources/VisboxKern` ist ein Verweis dorthin. Warum diese Richtung und nicht die
// umgekehrte, steht in `ipad/LIESMICH.md`: Swift Playgrounds auf dem iPad sieht nur, was
// im App-Paket selbst liegt, und ein Verweis NACH DRAUSSEN laege dort ins Leere.
import PackageDescription

let package = Package(
    name: "VisboxKern",
    // Die Mindeststaende der App. Unter Linux gelten sie nicht — dort baut SwiftPM ohne
    // Plattformangabe, und genau das soll es: Der Kern ist plattformneutral.
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "VisboxKern", targets: ["VisboxKern"]),
    ],
    targets: [
        .target(name: "VisboxKern"),
        .testTarget(name: "VisboxKernTests", dependencies: ["VisboxKern"]),
    ]
)
