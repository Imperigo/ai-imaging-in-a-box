# Die iPad-App «Visbox»

Native App für das iPad (SwiftUI und PencilKit, iOS 17), Zielgerät iPad Pro 11 (1. Gen.) mit
Apple Pencil 2. Sie spricht per HTTP mit dem Server `oberflaeche/server.py` auf der
HomeStation im Heimnetz. **Sie rechnet nie selbst** — jedes Bild, jedes Urteil, jede Zahl
kommt vom Server. Was über die Leitung geht, steht in `docs/VISBOX_PROTOKOLL.md`.

Nach der Abgabe (Januar 2027) wird die App in KosmoOrbit eingebaut und heisst dann
«KosmoSketch». Name, Bundle-Kennung und Dienstname stehen darum an **einer** Stelle:
`Visbox.swiftpm/Kern/Marke.swift`. Das App-Manifest muss Kennung, Dienst und Namen
wiederholen (es kann die Quellen nicht lesen); `tests/test_ipad_geruest.py` fällt, sobald
die beiden auseinanderlaufen oder eine andere Swift-Datei sie nennt. Der Server nimmt den
Namen seit dem 23.09.2026 in allen Sätzen aus derselben Quelle (`server.NAME`).

## Stand (23.09.2026, nach Welle 2b)

**Gebaut** sind die fünf Einheiten Zeichnen, Leiste, Bilder, Verbindung und ihr Kern — zwei
Wellen und eine Nachbesserung lang, jede mit einer Durchsicht. Der Stand der Welle 2 ist
`edbdcad`, die Nachbesserung (Welle 2b) `f8f2a40`.

**Übersetzt auf dem Mac:** Die Prüfstrecke `.github/workflows/ipad.yml` lief für `6e267d7`
(der Stand nach `f8f2a40`, nur das README dazu) durch — Lauf 5, «success», nachgesehen am
23.09.2026 im Protokoll des Laufs: **172 Proben des Kerns grün** (nach der Welle 2 waren es
139), die App für den iOS-Simulator «BUILD SUCCEEDED», **keine Warnung des Übersetzers**. Im
Protokoll steht wieder nur die Zeile eines Apple-Werkzeugs («Metadata extraction skipped. No
AppIntents.framework dependency found.») — ein Hinweis, dass die App keine App-Intents hat,
kein Befund am Code.

**Was die App heute kann — gebaut, am Gerät unbestätigt:**

* **Zeichnen:** eine PencilKit-Fläche je Ebene, übereinander; Ebenen als Varianten
  (Entscheid 7), «Zurück»/«Vor» mit Zähler, Stiftfarben; das Blatt bleibt beim Drehen
  dasselbe.
* **Die Unterlage** (Welle 2b): In der grossen Bildansicht legt «Darauf skizzieren» das Bild
  unter die Ebenen — blattfüllend, und bei anderem Seitenverhältnis gestreckt, **nach
  derselben Regel wie der Server** (`Kern/Blattunterlage.swift`, abgeschrieben aus
  `arbeitsgang.setze_auf_unterlage`; dass beide Seiten gleich entscheiden, hält
  `tests/test_app_abschrift_server.py`). Die App schickt ihren Namen als `ueber` mit; eine
  **ausgeblendete** Unterlage geht **nicht** mit (Entscheid 7, «gerechnet wird, was sichtbar
  ist» — die Skizze wird dann auf Grau gerechnet, und die Ebenentafel sagt es). Ob das Bild
  am Gerät deckungsgleich unter den Strichen liegt, ist **unbestätigt**.
* **Leiste und Arbeitsplatz:** die Werkzeugleiste, ein Seitenfeld (Ebenen oder Mappe),
  hoch und quer (Blätter «Main» und «MainHoch»), Vollbild (Entscheid 29); «In die Mappe
  legen» unten im Seitenfeld.
* **Bilder:** das Bildband mit Prüfzeichen je Bild (Farbe, Wort, Zahl, Vorbehalt —
  Entscheide 15, 16, 30), die grosse Ansicht mit Schalter Prüfen/Entwerfen, Skizzenliste,
  Varianten, Laufanzeige mit «Lauf abbrechen», Teilen mit dem Zeichen auf dem Bild
  (Entscheid 20). **Vorher und Nachher** (Entscheid 17) erscheint nur, wenn der Server zum
  Bild das Feld `vorher` liefert — das Bild, über das skizziert wurde. Das Feld gibt es seit
  der Welle 2b (23.09.2026); **vorher war der Vergleich in der App nie zu sehen**, und bei
  einem Bild ohne Unterlage (auf Grau gerechnet, oder aus dem Modell) bleibt er es.
* **Verbindung:** Suchen im Heimnetz über die Bonjour-Suche des Systems, erstes Verbinden
  mit der sechsstelligen Zahl, Anmeldung im Schlüsselbund, das Parkfach für Skizzen, die
  (noch) nicht drüben sind, mit Schlüssel gegen Doppelsendung und samt `ueber`, und die
  Übergabe als Bewegung.
* **Kern** (nur Foundation, hier unter Linux mit `swift test` geprüft): Anfragen bauen und
  Antworten lesen, Prüfzeichen, Ebenenregeln, Unterlage, Parkfach, Suche, Wege, Marke.

**Was bekannt fehlt:**

* **Kein Teil der App ist auf einem iPad gelaufen.** Alles oben ist übersetzt und im Kern
  geprüft, nicht bedient — Stift, Drehen, Vollbild, Übergabe, und neu die Unterlage unter
  dem Blatt.
* **Die Anleitung zum Aufspielen** samt Abnahmeblatt steht in
  [`docs/VISBOX_IPAD_ERSTE_PROBE.md`](../docs/VISBOX_IPAD_ERSTE_PROBE.md).
* **Die Beschriftung des Vergleichs** («Unterlage» statt «Aus dem Modell», weil über ein
  früheres Bild der KI skizziert das Vorher nicht aus dem Modell stammt) ist auf dem Blatt
  «Bilder» der Entwurfsfläche nachgezeichnet (23.09.2026) und dort als **Owner-Entscheid
  offen** markiert.

**Am Gerät unbestätigt** ist alles, was über das Übersetzen und die Kernproben hinausgeht.

## Was wo liegt

```
ipad/
├── Visbox.swiftpm/              das App-Paket — öffnet sich in Xcode und in Swift Playgrounds
│   ├── Package.swift            Manifest in der Form, die Swift Playgrounds selbst schreibt
│   ├── InfoZusatz.plist         nur: App Transport Security für lokale Netze
│   ├── VisboxApp.swift          der Einstieg (@main)
│   ├── Startansicht.swift       ordnet die Einheiten an, sonst nichts
│   ├── Platzhalter.swift        aus Welle 0; keine Einheit benutzt ihn mehr
│   ├── Kern/                    der plattformneutrale Kern — NUR Foundation
│   │   ├── Marke.swift          Name, Kennung, Dienst: die eine Stelle
│   │   ├── Urteil.swift         bestanden / durchgefallen / nicht gemessen
│   │   ├── Wege.swift           die Wege des Servers, bewacht gegen server.py
│   │   ├── Anfragen.swift       Anfragen gebaut und Antworten gelesen — nicht gesendet
│   │   ├── Pruefzeichen.swift   das Zeichen am Bild, und wie ein Bild gelesen wird
│   │   ├── Ebenen.swift         die Regeln der Zeichenfläche, ohne PencilKit
│   │   ├── Blattunterlage.swift die Unterlage unter dem Blatt: gestreckt, was mitgeht
│   │   ├── Stiftfarben.swift    Grund des Blattes und Stiftfarben, gegen das Blatt geprüft
│   │   ├── Parkfach.swift       Skizzen, die (noch) nicht drüben sind
│   │   └── Suche.swift          was gefunden wurde, und welche HomeStation genommen wird
│   ├── Zeichnen/                Zeichenfläche, Leinwand je Ebene, Ebenentafel, Zeichenstand,
│   │                            Unterlagenbild
│   ├── Leiste/                  Leiste, Werkzeugwahl, Arbeitsplatz, Seitenfeld, Zeichenblatt,
│   │                            Mappenknopf (Farben, Schriften, Masse nach «Die Zeichen»)
│   ├── Bilder/                  Bildband, Bildansicht, Vergleich, Skizzen, Varianten,
│   │                            Laufanzeige, Teilen, Zeichenrahmen, Mappentafel,
│   │                            Unterlage, «Darauf skizzieren»
│   └── Verbindung/              Verbindungszeile, Koppelbildschirm, Sucher, Sender,
│                                Schlüsselbund, Parkfachliste, Mappenabgleich, Übergabe
└── VisboxKern/                  der Kern als eigenes Swift-Paket, zum Prüfen
    ├── Package.swift
    ├── Sources/VisboxKern  →  ../../Visbox.swiftpm/Kern   (ein Verweis, keine Kopie)
    └── Tests/VisboxKernTests/   XCTest-Proben des Kerns, eine Datei je Kerndatei
```

**Für weitere Arbeit:** Neue Dateien kommen in den Ordner ihrer Einheit — so stossen zwei
Einheiten, die gleichzeitig entstehen, nicht in derselben Zeile zusammen.
`Startansicht.swift` fasst keine Einheit an, sie ordnet nur an. Kern-Code (ohne
UIKit/SwiftUI/PencilKit) gehört nach `Kern/`, seine Proben nach
`VisboxKern/Tests/VisboxKernTests/`.

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
  «Stand» oben). Wie sie sich bedienen lässt — Stift, Drehen, Vollbild, Übergabe, die
  Unterlage unter dem Blatt —, zeigt erst ein iPad. Ob die Angaben im Manifest, die aus `AppleProductTypes` stammen
  (`.placeholder(icon: .leaf)`, `.localNetwork(...)`, `additionalInfoPlistContentFilePath`),
  auf einem Gerät wirken, wie sie sollen, zeigt erst das Aufspielen — die Liste dessen, was
  dort zu prüfen ist, steht im Abnahmeblatt (`docs/VISBOX_IPAD_ERSTE_PROBE.md`).
* **Ob Swift Playgrounds das Paket öffnet** und den Unterordner `Kern/` mitübersetzt.
* **Ob iOS die Verbindung zur HomeStation zulässt** — lokale Netzwerkfreigabe
  (`NSLocalNetworkUsageDescription`, `NSBonjourServices`) und die ATS-Ausnahme
  `NSAllowsLocalNetworking` sind eingetragen, am Gerät nicht erprobt.
* **Finden im Heimnetz.** Der Server kündigt sich seit dem 22.09.2026 an, wenn er mit
  `--im-heimnetz` läuft (`oberflaeche/rundruf.py`, geprüft über einen lokalen UDP-Socket);
  ob ein echtes iPad ihn über die Bonjour-Suche findet, ist **am Gerät unbestätigt**. Siehe
  `docs/VISBOX_PROTOKOLL.md`, §8, samt dem Vorbehalt zu eigenen Rundrufen und dem Befund,
  dass der Rundruf einem vorhandenen avahi direkte Pakete wegnehmen kann.
