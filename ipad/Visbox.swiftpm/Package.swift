// swift-tools-version: 5.9
//
// DAS APP-PAKET — in der Form, die Swift Playgrounds selbst schreibt.
//
// Swift Playgrounds auf dem iPad schreibt diese Datei neu, sobald dort Symbol, Farbe oder
// Faehigkeiten geaendert werden. Sie folgt darum genau seiner Form: EIN Ziel `AppModule`
// mit `path: "."`, keine Abhaengigkeit. Alles, was hier von Hand dazukaeme, ginge beim
// naechsten Aendern auf dem iPad still verloren.
//
// ZWEI ANGABEN STEHEN HIER EIN ZWEITES MAL, weil ein Manifest die Quellen nicht lesen
// kann: die Kennung und der Dienst. Die eine Stelle dafuer ist `Kern/Marke.swift`;
// `tests/test_ipad_geruest.py` faellt, sobald die beiden auseinanderlaufen.
//
// Der Kern (`Kern/`) wird hier NICHT als Paket eingebunden, sondern mituebersetzt — er
// liegt im selben Ziel. Warum, steht in `ipad/LIESMICH.md`.

import PackageDescription
import AppleProductTypes

let package = Package(
    name: "Visbox",
    platforms: [
        .iOS("17.0")
    ],
    products: [
        .iOSApplication(
            name: "Visbox",
            targets: ["AppModule"],
            bundleIdentifier: "org.example.visbox",
            displayVersion: "0.1",
            bundleVersion: "1",
            appIcon: .placeholder(icon: .leaf),
            accentColor: .presetColor(.blue),
            supportedDeviceFamilies: [
                .pad
            ],
            supportedInterfaceOrientations: [
                .portrait,
                .landscapeRight,
                .landscapeLeft,
                .portraitUpsideDown(.when(deviceFamilies: [.pad]))
            ],
            capabilities: [
                // Erzeugt NSLocalNetworkUsageDescription und NSBonjourServices.
                .localNetwork(
                    purposeString: "Findet die HomeStation im Heimnetz und schickt ihr die Skizzen zum Rechnen.",
                    bonjourServiceTypes: ["_visbox._tcp"]
                )
            ],
            // App Transport Security NUR fuer lokale Netze (NSAllowsLocalNetworking).
            // Der Server spricht gewoehnliches HTTP; alles ausserhalb des Heimnetzes
            // bleibt unter dem vollen Schutz.
            additionalInfoPlistContentFilePath: "InfoZusatz.plist"
        )
    ],
    targets: [
        .executableTarget(
            name: "AppModule",
            path: "."
        )
    ]
)
