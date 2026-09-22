# Die iPad-App «Visbox» — das Gerüst

Native App für das iPad (SwiftUI, später PencilKit), Zielgerät iPad Pro 11 (1. Gen.) mit
Apple Pencil 2. Sie spricht per HTTP mit dem Server `oberflaeche/server.py` auf der
HomeStation im Heimnetz. **Sie rechnet nie selbst** — jedes Bild, jedes Urteil, jede Zahl
kommt vom Server. Was über die Leitung geht, steht in `docs/VISBOX_PROTOKOLL.md`.

Nach der Abgabe (Januar 2027) wird die App in KosmoOrbit eingebaut und heisst dann
«KosmoSketch». Name, Bundle-Kennung und Dienstname stehen darum an **einer** Stelle:
`Visbox.swiftpm/Kern/Marke.swift`. Das App-Manifest muss Kennung, Dienst und Namen
wiederholen (es kann die Quellen nicht lesen); `tests/test_ipad_geruest.py` fällt, sobald
die beiden auseinanderlaufen oder eine andere Swift-Datei sie nennt.

**Stand (22.09.2026, nachgeführt):** Welle 1 gebaut — Zeichnen, Leiste, Bilder, Verbindung und
ihr Kern. **Übersetzt auf dem Mac:** Die Prüfstrecke `.github/workflows/ipad.yml` lief für den
Stand `f32266f` durch (Lauf 3, «success»; der Lauf davor für `54f28b9` fand einen Fehler, der
mit `f32266f` behoben ist; beides nachgesehen in der Laufliste auf GitHub). Nach Angabe der
Welle-2-Leitung meldet der Lauf eine Warnung (`Verbindung/Verbindungszeile.swift`, «main
actor-isolated static property 'zeichenflaeche'») — die Warnung selbst ist hier nicht
nachgelesen. **Am Gerät unbestätigt** ist alles,
was über das Übersetzen hinausgeht. Der Baum unten zeigt das Gerüst der Welle 0; die Einheiten
haben seither weitere Dateien in ihren Ordnern.

## Was wo liegt

```
ipad/
├── Visbox.swiftpm/              das App-Paket — öffnet sich in Xcode und in Swift Playgrounds
│   ├── Package.swift            Manifest in der Form, die Swift Playgrounds selbst schreibt
│   ├── InfoZusatz.plist         nur: App Transport Security für lokale Netze
│   ├── VisboxApp.swift          der Einstieg (@main)
│   ├── Startansicht.swift       ordnet die Einheiten an, sonst nichts
│   ├── Platzhalter.swift        ein Feld, das sagt, dass es noch nicht gebaut ist
│   ├── Kern/                    der plattformneutrale Kern — NUR Foundation
│   │   ├── Marke.swift          Name, Kennung, Dienst: die eine Stelle
│   │   ├── Urteil.swift         bestanden / durchgefallen / nicht gemessen
│   │   └── Wege.swift           die Wege des Servers, bewacht gegen server.py
│   ├── Zeichnen/Zeichenflaeche.swift     Platzhalter der Einheit «Zeichnen»
│   ├── Leiste/Leiste.swift               Platzhalter der Einheit «Leiste»
│   ├── Verbindung/Verbindungszeile.swift Platzhalter der Einheit «Verbindung»
│   └── Bilder/Bildband.swift             Platzhalter der Einheit «Bilder» (noch nicht eingehängt)
└── VisboxKern/                  der Kern als eigenes Swift-Paket, zum Prüfen
    ├── Package.swift
    ├── Sources/VisboxKern  →  ../../Visbox.swiftpm/Kern   (ein Verweis, keine Kopie)
    └── Tests/VisboxKernTests/   XCTest-Proben des Kerns
```

**Für spätere Einheiten:** Jede Einheit bekommt ihren eigenen Ordner und ersetzt dort den
Platzhalter. Der Typname (`Zeichenflaeche`, `Leiste`, `Verbindungszeile`, `Bildband`) bleibt,
weil `Startansicht` ihn benutzt; `Startansicht.swift` selbst fasst keine Einheit an. Neue
Dateien kommen in den Ordner ihrer Einheit — so stossen zwei Einheiten, die gleichzeitig
entstehen, nicht in derselben Zeile zusammen. Kern-Code (ohne UIKit/SwiftUI/PencilKit) gehört
nach `Kern/`, seine Proben nach `VisboxKern/Tests/VisboxKernTests/`.

## Warum der Kern im App-Paket liegt und nicht daneben

Gewünscht war: ein eigenes Paket `ipad/VisboxKern/`, das das App-Paket als **lokale
Abhängigkeit per Pfad** einbindet (`.package(path: "../VisboxKern")`). In Xcode ginge das.
In **Swift Playgrounds auf dem iPad** ist es nicht zuverlässig, aus drei Gründen:

1. **Swift Playgrounds sieht nur, was im `.swiftpm` liegt.** Ein Paket wird dort als
   Dokument geöffnet, und das Dokument ist der Ordner `Visbox.swiftpm` — ein Pfad
   `../VisboxKern` zeigt aus ihm heraus, auf etwas, das die App nicht öffnen darf. Nach allem,
   was über Swift Playgrounds bekannt ist, bindet es Abhängigkeiten **über eine Adresse
   (git)** ein, nicht über einen Pfad.
2. **Swift Playgrounds schreibt `Package.swift` neu**, sobald dort Symbol, Farbe oder
   Fähigkeiten geändert werden. Eine von Hand ergänzte Pfad-Abhängigkeit ginge dabei still
   verloren.
3. **Ein Verweis (Symlink) im App-Paket** nach draussen läge auf dem iPad ebenso ins Leere —
   iCloud Drive und die Dateien-App führen Verweise nicht verlässlich mit.

**Gewählt ist darum die umgekehrte Richtung:** Die Quellen des Kerns liegen **im** App-Paket
(`Visbox.swiftpm/Kern/`) und werden dort mitübersetzt — das einzige Ziel `AppModule` mit
`path: "."` nimmt jede Swift-Datei im Paket, auch in Unterordnern. Das ist genau die Form,
die Swift Playgrounds selbst erzeugt; es gibt nichts, was es beim Neuschreiben verlieren
könnte. Das Paket `ipad/VisboxKern/` bekommt seine Quellen über einen **Verweis nach
innen** (`Sources/VisboxKern → ../../Visbox.swiftpm/Kern`). Swift Playgrounds sieht diesen
Verweis nie; SwiftPM unter Linux und macOS folgt ihm (geprüft am 22.09.2026 mit Swift 6.4
unter Linux).

**Was das kostet, und es steht hier, damit es niemand für umsonst hält:**

* In der App ist der Kern **kein eigenes Modul**. Die App schreibt darum nie
  `import VisboxKern` (es gäbe dort kein solches Modul); die Typen aus `Kern/` sind direkt
  sichtbar. Die Proben dagegen importieren `VisboxKern` als Modul — dort ist es eines.
* Dass der Kern nur Foundation benutzt, erzwingt in der App kein Übersetzer (alles ist ein
  Modul). Erzwungen wird es an zwei anderen Stellen: `swift build` unter Linux kennt UIKit,
  SwiftUI und PencilKit nicht und bricht ab, und `tests/test_ipad_geruest.py` prüft die
  Importe jeder Kern-Datei.
* Unter Windows ohne Verweis-Unterstützung fehlt `VisboxKern/Sources/VisboxKern`. Das betrifft
  nur das Prüfpaket, nicht die App.

*Ein Pfad, der in einer von zwei Umgebungen ins Leere zeigt, ist in dieser Umgebung kein
Pfad — und genau die Umgebung, in der der Owner die App öffnet, ist die heikle.*

## Öffnen

* **Xcode (Mac):** `ipad/Visbox.swiftpm` öffnen, Ziel «Visbox», ein iPad-Simulator oder das
  eigene Gerät. Mit kostenlosem Konto (Entscheid Nr. 23) läuft die App je 7 Tage.
  **Vor dem ersten Aufspielen** die Kennung `org.example.visbox` (ein Platzhalter, der
  niemandem gehört) gegen eine eigene tauschen — in `Kern/Marke.swift` **und** in
  `Package.swift` (`bundleIdentifier`), sonst schlägt die Prüfung an.
* **Swift Playgrounds (iPad):** den Ordner `Visbox.swiftpm` auf das iPad bringen (Dateien-App,
  iCloud Drive oder ein git-Programm) und dort öffnen. **Am Gerät unbestätigt.**

## Die Swift-Kette hier (Linux) laden

Nur für den Kern: `swift build` und `swift test` in `ipad/VisboxKern`. Die App selbst lässt
sich unter Linux nicht übersetzen (SwiftUI gibt es nur bei Apple) — das tut die Prüfstrecke
`.github/workflows/ipad.yml` auf einem Mac.

```sh
# Die aktuelle Fassung nachsehen: https://www.swift.org/install/linux/
# Gebraucht wird «Ubuntu 24.04», x86_64, als tar.gz. Am 22.09.2026 war das 6.4.0.
FASSUNG=6.4.0
curl -fL -o swift.tar.gz \
  "https://download.swift.org/swift-${FASSUNG}-release/ubuntu2404/swift-${FASSUNG}-RELEASE/swift-${FASSUNG}-RELEASE-ubuntu24.04.tar.gz"
sudo mkdir -p /opt/swift
sudo tar -xzf swift.tar.gz -C /opt/swift --strip-components=1
rm swift.tar.gz
export PATH=/opt/swift/usr/bin:$PATH
swift --version

cd ipad/VisboxKern && swift test
```

Das Archiv ist rund 1,1 GB gross. Hinter einem Proxy mit eigenem Zertifikat muss `curl`
diesem Zertifikat trauen (`--cacert`); die Verbindung ungeprüft zu lassen ist keine Lösung.

`tests/test_ipad_geruest.py` fährt `swift test` selbst mit, wenn `swift` im `PATH` oder unter
`/opt/swift/usr/bin/` liegt, und meldet sich sonst mit Grund als übersprungen.

## Was ungeprüft ist

* **Ob die App läuft.** Dass sie **übersetzt**, zeigt die Prüfstrecke auf dem Mac (siehe
  «Stand» oben). Ob die Angaben im Manifest, die aus `AppleProductTypes` stammen
  (`.placeholder(icon: .leaf)`, `.localNetwork(...)`, `additionalInfoPlistContentFilePath`),
  auf einem Gerät wirken, wie sie sollen, zeigt erst das Aufspielen.
* **Ob Swift Playgrounds das Paket öffnet** und den Unterordner `Kern/` mitübersetzt.
* **Ob iOS die Verbindung zur HomeStation zulässt** — lokale Netzwerkfreigabe
  (`NSLocalNetworkUsageDescription`, `NSBonjourServices`) und die ATS-Ausnahme
  `NSAllowsLocalNetworking` sind eingetragen, am Gerät nicht erprobt.
* **Finden im Heimnetz.** Der Server kündigt sich seit dem 22.09.2026 an, wenn er mit
  `--im-heimnetz` läuft (`oberflaeche/rundruf.py`, geprüft über einen lokalen UDP-Socket);
  ob ein echtes iPad ihn über die Bonjour-Suche findet, ist **am Gerät unbestätigt**. Siehe
  `docs/VISBOX_PROTOKOLL.md`, §8, samt dem Vorbehalt zu eigenen Rundrufen und dem Befund,
  dass der Rundruf einem vorhandenen avahi direkte Pakete wegnehmen kann.
