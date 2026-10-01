// swift-tools-version: 5.9
//
// DIE MAC-APP (v0.1.7, Strom A) — eine eigene App, die den Kern der iPad-App mitbenutzt
// (Owner-Entscheid 44).
//
// ANDERS ALS DAS APP-PAKET DES IPAD bindet sie den Kern als PAKET ein, ueber den Pfad
// `../VisboxKern`. Das iPad-Paket kann das nicht, weil Swift Playgrounds nur sieht, was im
// `.swiftpm` liegt (`ipad/LIESMICH.md`). Die Mac-App wird nie in Swift Playgrounds geoeffnet,
// sondern in der Pruefstrecke mit `swift build` uebersetzt — dort folgt SwiftPM dem Pfad und
// dem Verweis in `VisboxKern/Sources`. Der Kern bleibt damit EINER: derselbe, den
// `swift test` prueft und den die iPad-App mituebersetzt. Hier heisst es darum
// `import VisboxKern`, in der iPad-App nie.
//
// KEINE WEITERE ABHAENGIGKEIT (Regel 1): nur Apples Plattform (SwiftUI, WebKit, Network,
// Security, CoreText) und unser Kern. `tests/test_ipad_geruest.py` prueft die Importe.
//
// Ordner unter `Sources/VisboxMac/`, je Strom einer, damit parallele Arbeit nicht in
// derselben Datei zusammenstoesst: `Start/` (A), `Vermittlung/` (B), `Vorfuehrung/` (C),
// `Assistent/` (D).
//
// Kein App-Manifest wie beim iPad (`AppleProductTypes` kennt nur iOS-Apps). Das Buendel
// `.app` setzt die Pruefstrecke zusammen; die Angaben dafuer stehen in `App/Info.plist`.

import PackageDescription

let package = Package(
    name: "VisboxMac",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(path: "../VisboxKern"),
    ],
    targets: [
        .executableTarget(
            name: "VisboxMac",
            dependencies: [.product(name: "VisboxKern", package: "VisboxKern")],
            path: "Sources/VisboxMac"
        ),
    ]
)
