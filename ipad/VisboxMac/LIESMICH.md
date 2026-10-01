# Die Mac-App «Visbox»

Eine eigene App für den Mac (SwiftUI, macOS 14 oder neuer, Apple-Chip), gebaut für die
**Vorführung auswärts** (Entscheide 35–44, Plan v0.1.7 Strom A). Sie baut beim Öffnen die
Leitung zum Heim-PC selbst auf, zeigt in vier Zeilen, wie weit sie ist (Blatt 13), und öffnet
mit «Schon anfangen» die Visbox-Fläche des Heim-PC. **Sie rechnet nie selbst** — gerechnet
wird am Heim-PC, wie bei der iPad-App.

Sie teilt den **Kern** mit der iPad-App (`ipad/VisboxKern`): dieselben Wege, dieselbe
Anmeldung, dieselbe Marke. Die Regeln der Startzeilen und die Prüfung der Adresse stehen dort
(`Kern/Startzeilen.swift`, `Kern/Heimadresse.swift`) und sind unter Linux mit Proben geprüft;
die Mac-App selbst misst nur und zeigt.

## Herunterladen

Die App kommt fertig aus der Prüfstrecke, ohne Xcode und ohne Apple-Konto (Entscheid 58):

1. Auf GitHub im Repo unter **Actions** den Ablauf **«iPad»** öffnen und den letzten grünen
   Lauf des gewünschten Zweigs wählen.
2. Unten unter **Artifacts** «Visbox-mac» herunterladen (nur angemeldet bei GitHub). Es bleibt
   **14 Tage** liegen; danach den Ablauf neu starten («Run workflow»).
3. GitHub packt das Ergebnis noch einmal ein: Die heruntergeladene Datei auspacken, darin
   liegt `Visbox-mac.zip`, auch diese auspacken — heraus kommt `Visbox.app`.
4. `Visbox.app` in den Ordner **Programme** ziehen. Aus «Downloads» heraus gestartet, legt
   macOS die App jedes Mal an einen anderen, versteckten Ort.

## Das erste Öffnen auf macOS 15

Die App trägt nur eine **Behelfs-Unterschrift**, keine von Apple beglaubigte. macOS hält sie
darum beim ersten Mal an. **«Rechtsklick → Öffnen» genügt seit macOS 15 nicht mehr.** Der Weg:

1. `Visbox.app` einmal öffnen (Doppelklick). macOS meldet, die App könne nicht geöffnet werden,
   weil Apple sie nicht prüfen konnte → **«Fertig»**.
2. **Systemeinstellungen → Datenschutz & Sicherheit**, ganz nach unten zum Abschnitt
   «Sicherheit»: Dort steht, dass «Visbox» blockiert wurde → **«Trotzdem öffnen»**, mit dem
   Kennwort oder Touch ID des Mac bestätigen.
3. Die App noch einmal öffnen und in der Rückfrage **«Trotzdem öffnen»** wählen.

Danach öffnet sie wie jedes Programm. **Nach jedem neuen Herunterladen** ist es eine neue
Unterschrift: Der Weg oben gilt dann noch einmal, und beim ersten Lesen des Kennworts fragt
macOS, ob «Visbox» an den Schlüsselbund darf → **«Immer erlauben»**.

## Einrichten

Beim ersten Start geht das Blatt **«Einrichten»** auf. Später ist es **immer** erreichbar: über
«Einrichten» in der Werkzeugleiste des Fensters, in der Startansicht oben rechts und im Band des
Vorführmodus.

**Stimmt das Kennwort nicht** (oder ist der Server ohne Kennwort hinter der Weiterleitung), weist
die Tür des Heim-PC ab (401/403). Das ist **kein Vorführmodus** — der Heim-PC antwortet ja: Die
App bleibt in der Startansicht (oder kehrt aus der Arbeit dorthin zurück), und die Zeile
«Leitung» sagt, was zu tun ist. Ein Neustart hilft dabei nicht, weil das Kennwort im
Schlüsselbund bleibt — nur «Einrichten».

* **Adresse des Heim-PC** — `https://<rechner>.<netz>.ts.net:8443`. `<rechner>` und `<netz>`
  stehen in der Tailscale-App am Heim-PC (der volle Name des Rechners im eigenen
  Tailscale-Netz). Der Anschluss **8443** ist der, auf dem Tailscale Serve am Heim-PC zum
  Visbox-Server weiterleitet; ohne Angabe nimmt die App ihn selbst. Geprüft wird: **https**,
  ein Anschluss, **kein Pfad** dahinter, und **kein Benutzer oder Kennwort in der Adresse**.
* **Benutzer und Kennwort** — aus dem Fenster am Heim-PC, in dem der Visbox-Server gestartet
  wurde. Der Benutzer ist vorgeschlagen (heute `visbox`), aber nicht fest: Er kommt vom Server.

Das Kennwort liegt danach **im Schlüsselbund dieses Mac** und nirgends sonst — nicht in einer
Datei, nicht in den Einstellungen, nicht im Protokoll. Die Adresse liegt in den Einstellungen
der App (sie ist kein Geheimnis).

**Am Mac muss Tailscale laufen** (das installierte Programm, angemeldet im eigenen Netz). Die
App bringt Tailscale nicht selbst mit.

## Die vier Zeilen

| Zeile | Woher | Was sie sagen kann |
|---|---|---|
| Leitung zum Heim-PC | `GET /api/fortschritt` | **steht** (mit Antwortzeit) · **fehlt**: Kennwort stimmt nicht (401), über die Weiterleitung ohne Kennwort (403), Heim-PC antwortet nicht, «Tailscale am Mac an?» (Name oder Zertifikat) · **wartet**: noch keine Adresse |
| Rechner am Heim-PC | `GET /api/heim` | **steht**: Blender da, Grafikkarte frei · **fehlt**: Blender fehlt · **wartet**: Leitung steht nicht, oder der Heim-PC kennt die Frage noch nicht (älterer Server) |
| Assistent | `GET /api/heim` | **steht** (Modell geladen) · **lädt** (seit …) · **wartet** (entladen, solange ein Bild rechnet) · **fehlt** |
| iPad | Vermittlung (Strom B) | **Vorgabe aus** (Owner-Entscheid 01.10.2026: unterwegs spricht das iPad über Tailscale direkt mit dem Heim-PC): **wartet** — «Aus — im Menü «iPad» einschalten, wenn ein iPad mitkommt.» Eingeschaltet: **wartet** auf das iPad oder mit der Zahl zum Koppeln · **steht** (letzte Anfrage vor höchstens 30 s) · **fehlt** mit Grund. Warum aus: Die Strecke iPad ↔ Mac ist unverschlüsselt (Protokoll §8b, «Übertragung») |

Die Kopfzeile ist gezählt («baut auf · 2 von 4»). Gefragt wird beim Start und dann alle 5 bis
60 Sekunden, mit wachsendem Abstand; ändert sich etwas oder lädt eine Zeile, wieder nach 5.

**«Schon anfangen»** (Entscheid 39) geht, sobald die Leitung steht — auch wenn der Assistent
noch lädt. Es öffnet die Visbox-Fläche des Heim-PC in der App; rechts ist der Platz für den
Assistenten.

## Stand (01.10.2026)

**Gebaut:** das Paket, die Startzeilen samt Kopfzeile und Takt, «Einrichten» mit Schlüsselbund,
die Fläche des Heim-PC nach «Schon anfangen», die Schriften (registriert zur Laufzeit, sonst
Systemschrift), die Prüfstrecke mit ZIP. Die Logik dahinter ist im Kern mit Proben geprüft
(`StartzeilenTests`, `HeimadresseTests`); das Gerüst und das Bündel bewacht
`tests/test_ipad_geruest.py` (Abschnitt 7).

**Am Gerät unbestätigt — alles, was über Übersetzen und Kernproben hinausgeht.** Bis zur Abgabe
ist die App nie gestartet worden (Entscheid 60). Insbesondere ungeprüft:

* ob macOS 15 sie mit der Behelfs-Unterschrift über «Trotzdem öffnen» startet,
* ob der Schlüsselbund mit der Behelfs-Unterschrift ablegt und wieder liest,
* ob die Fläche über die Basic-Anmeldung lädt, auch die Anfragen der Seite selbst (`/api/…`),
* ob die Schriften erscheinen,
* ob die Leitung über Tailscale steht (Anschluss 8443, Zertifikat von Tailscale Serve).

**Was seit dem Gerüst dazukam (01.10.2026, alles am Gerät unbestätigt):** `GET /api/heim`
(Zeilen «Rechner» und «Assistent»), der Vorführmodus (Blatt 13b), die Seitenleiste des
Assistenten (Blatt 14), «Einrichten» immer in der Werkzeugleiste, und das Menü «iPad» mit
**«iPad koppeln»**: Der Mac holt beim Heim-PC eine Zahl, und das iPad koppelt sich damit über
Tailscale selbst (Entscheid 63). Die Vermittlung über den Mac steht im selben Menü, **aus**,
bis man sie einschaltet — sie ist im fremden WLAN unverschlüsselt.

## Was wo liegt

```
ipad/VisboxMac/
├── Package.swift            bindet den Kern per Pfad ein (../VisboxKern), sonst nichts
├── App/Info.plist           Name, Kennung (.mac), Dienst, lokales Netz — gegen die Marke bewacht
├── LIESMICH.md              dieses Blatt
└── Sources/VisboxMac/
    ├── VisboxMacApp.swift   der Einstieg (@main), sonst nichts
    ├── Start/               Strom A: Startzeilen, Einrichten, Leitung, Fläche, Schriften, Farben
    ├── Vermittlung/         Strom B: das iPad über den Mac
    ├── Vorfuehrung/         Strom C: der Vorführmodus
    └── Assistent/           Strom D: die Seitenleiste des Assistenten
```

Übersetzt wird nur in der Prüfstrecke (`.github/workflows/ipad.yml`, Job `mac`): `swift build`
für Apple-Chip, daraus `Visbox.app` mit `Contents/MacOS/<Programm>`, `Contents/Info.plist` und
`Contents/Resources/Schriften/` (die Schriften der iPad-App unverändert, samt ihren
OFL-Lizenztexten), Behelfs-Unterschrift, ZIP. Unter Linux lässt sich nur der Kern prüfen
(`swift test` in `ipad/VisboxKern`).
