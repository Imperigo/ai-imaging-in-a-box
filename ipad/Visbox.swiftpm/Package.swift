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
//
// DIE SCHRIFTEN (`Schriften/`, 23.09.2026) stehen als `resources: [.process(...)]` am
// Ziel — die Form, die Swift Playgrounds selbst schreibt, wenn man dort Dateien hinzufuegt.
// Ohne die Angabe waeren die Dateien im Ziel «unbehandelt», und SwiftPM warnt (nachgefahren
// am 23.09.2026 mit Swift 6.4 unter Linux, an einer Kopie dieses Aufbaus). `.process` legt
// alle Dateien FLACH in die Ablage der App: Zwei Dateien gleichen Namens, auch in
// verschiedenen Unterordnern, sind ein Fehler («multiple resources named 'OFL.txt'»,
// ebenso nachgefahren) — darum heissen die Lizenztexte `<Familie>-OFL.txt`.

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
            displayVersion: "0.3.40",
            bundleVersion: "55",
            // DAS ICON (Owner-Entscheid 88, 14.10.2026, Blatt 20 «Box mit Bild»): ein Bild 1024
            // in `Assets.xcassets/AppIcon.appiconset`, erzeugt von `tools/make_icon.py`. Die
            // Form `.asset("AppIcon")` ist die, die Swift Playgrounds selbst schreibt.
            appIcon: .asset("AppIcon"),
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
                // Erzeugt NSLocalNetworkUsageDescription und NSBonjourServices. Der Satz nennt
                // seit dem 01.10.2026 auch den Mac: Unterwegs ist ER es, den die App im WLAN
                // findet und der die Skizzen an die HomeStation weiterreicht (Protokoll §8b).
                // SEIT DEM 20.10.2026 (Entscheid 99) dazu die Naehe-Verbindung zum Koppeln:
                // MultipeerConnectivity verlangt ihren Dienst `Marke.naehedienst` zweimal, als
                // tcp und udp. Der erste Eintrag bleibt der Dienst der HomeStation.
                .localNetwork(
                    purposeString: "Findet die HomeStation im Heimnetz oder unterwegs den Mac, der für sie vermittelt, koppelt sich mit einem Mac in der Nähe und schickt der HomeStation die Skizzen zum Rechnen.",
                    bonjourServiceTypes: ["_visbox._tcp", "_visbox-kopp._tcp", "_visbox-kopp._udp"]
                ),
                // Erzeugt NSCameraUsageDescription (Entscheid 99b): «Mit QR-Code koppeln» liest
                // den Code im Koppelfenster des Mac mit der Kamera in der App.
                .camera(
                    purposeString: "Liest den QR-Code im Koppelfenster des Mac, damit sich das iPad ohne Abtippen koppelt."
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
            path: ".",
            resources: [
                .process("Schriften")
            ]
        )
    ]
)
