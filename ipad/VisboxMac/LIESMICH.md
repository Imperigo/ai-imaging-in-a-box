# Die Mac-App «Visbox»

Eine eigene App für den Mac (SwiftUI, macOS 14 oder neuer, Apple-Chip), gebaut für die
**Vorführung auswärts** (Entscheide 35–44, Plan v0.1.7 Strom A). Sie baut beim Öffnen die
Leitung zum Heim-PC selbst auf, zeigt in vier Zeilen, wie weit sie ist (Blatt 13), und öffnet
mit «Schon anfangen» die **Knotenansicht** des Heim-PC — das KosmoVis-Werkzeug (Entscheid 85,
14.10.2026, Blatt 19). Oben schaltet «Knoten | Visbox-Seite» auf die Visbox-Seite (Mappe
wählen, Bilder, Skizzen) und zurück; die Knoten zeigen die zuletzt dort geöffnete Mappe.
**Sie rechnet nie selbst** — gerechnet wird am Heim-PC, wie bei der iPad-App.

Sie teilt den **Kern** mit der iPad-App (`ipad/VisboxKern`): dieselben Wege, dieselbe
Anmeldung, dieselbe Marke. Die Regeln der Startzeilen und die Prüfung der Adresse stehen dort
(`Kern/Startzeilen.swift`, `Kern/Heimadresse.swift`) und sind unter Linux mit Proben geprüft;
die Mac-App selbst misst nur und zeigt.

## Herunterladen

**Seit 0.2.1 (Entscheid 84, 13.10.2026) aus der Freigabe:** Auf GitHub im Repo rechts unter
**Releases** die neueste Freigabe öffnen und `Visbox-mac.zip` laden — ohne Anmeldung, nur einmal
auspacken. Daneben liegen das iPad-Paket, das Fassungsblatt und `SHA256SUMS.txt`
(nachprüfen mit `shasum -a 256 -c SHA256SUMS.txt` im Download-Ordner). Eine Freigabe entsteht
nur, wenn auf `main` eine neue Nummer steht.

**Danach aktualisiert sich die App selbst:** Liegt eine neuere Fassung auf GitHub, steht in der
Werkzeugleiste **«● 0.x.y verfügbar — Aktualisieren»**. **Ein Klick genügt** (Entscheid 87): Die
App zeigt Nummer und Neuerungen, lädt, gleicht die Prüfsumme ab, prüft Kennung und Unterschrift,
legt die alte App in den Papierkorb und die neue an ihren Platz und **startet von selbst neu**.
Gefragt wird beim Start und danach jede Stunde. **Wer noch 0.2.0 hat**, holt einmal von Hand: Erst
ab 0.2.1 sucht die App selbst nach neuen Fassungen. Danach verlangt macOS eventuell noch einmal «Trotzdem öffnen»
(unten) und den Schlüsselbund. Läuft die App noch aus «Downloads», ersetzt sie sich nicht —
erst in «Programme» ziehen.

Für einen Zweig, der noch nicht auf `main` ist, gilt weiter der Weg aus der Prüfstrecke, ohne
Xcode und ohne Apple-Konto (Entscheid 58):

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

## Koppeln (seit 13.10.2026, Entscheid 83)

Beim ersten Start geht das Blatt **«Koppeln»** auf (Blatt 17 der Entwurfsfläche). Nichts
abtippen:

1. **Suchen.** Der Mac sucht den Heim-PC selbst — im eigenen Tailscale-Netz (über die
   Befehlszeile der Tailscale-App, `tailscale status --json`) und im WLAN zu Hause (Bonjour).
   Jeder Fund wird gefragt (`GET /api/hallo`); **wählbar ist nur, wer als Visbox-Heim-PC
   antwortet.**
2. **Weiter → Zahl.** Am Heim-PC erscheint eine sechsstellige Zahl — im Fenster des Dienstes und
   als Mitteilung. Sie gilt **5 Minuten, einmal, 3 Versuche**. Eintippen, «Koppeln». «Neue Zahl
   anfordern» holt eine neue (höchstens eine je 30 s). Nach drei Fehlversuchen sagt der Mac,
   dass die Zahl geschlossen ist.
3. **Verbunden.** Adresse und Benutzer sind gemerkt, das Kennwort liegt im Schlüsselbund; das
   Blatt zeigt die vier Startzeilen, wie sie sich aufbauen.

**Im WLAN ohne Tailscale** geht das nur, wenn der Heim-PC mit `--heimnetz` läuft
(`betrieb/README.md`): verschlüsselt, mit selbst unterschriebenem Zertifikat. Der Mac **heftet
es an** — er nimmt danach nur noch dieses an. Beim Koppeln steht unter dem Namen das **Zeichen
des Heim-PC** (16 Stellen); dasselbe steht im Fenster am Heim-PC. Wer ganz sicher sein will,
vergleicht die beiden — nur das schützt gegen jemanden, der sich genau beim Koppeln im WLAN
dazwischenstellt.

**Wo Tailscale am Mac gesucht wird:** `/Applications/Tailscale.app/Contents/MacOS/Tailscale`
(App-Store-Fassung, so in der Tailscale-Doku; die Standalone-Fassung liegt am selben Ort), dann
`/usr/local/bin/tailscale` (Starter der Standalone-Fassung, wenn in deren Einstellungen
installiert), dann `/opt/homebrew/bin/tailscale` (Homebrew, nicht belegt). Findet sich keiner,
sucht der Mac nur im WLAN, und das Blatt sagt es.

Klein darunter: **«Von Hand eintragen …»** öffnet den bisherigen Dialog (Entscheid 83c).

## Von Hand eintragen

Der bisherige Weg, heute der kleine Link im Blatt «Koppeln». Später ist es **immer** erreichbar: über
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

## Stand (13.10.2026, Entscheid 83)

**Gebaut, am Gerät unbestätigt:** das Blatt «Koppeln» (Suche über Tailscale und Bonjour, Zahl,
Verbunden), das Anheften des Zertifikats im WLAN für alle Leitungen zum Heim-PC (Startzeilen,
Fläche, Assistent, Vermittlung; `Start/Heimvertrauen.swift`). Die Logik dahinter steht im Kern
(`Kern/Heimkopplung.swift`, Proben `HeimkopplungTests`).

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
    ├── Assistent/           Strom D: die Seitenleiste des Assistenten
    └── Aktualisieren/       Entscheid 84: fragen, laden, prüfen, ersetzen (Regeln im Kern)
```

Übersetzt wird nur in der Prüfstrecke (`.github/workflows/ipad.yml`, Job `mac`): `swift build`
für Apple-Chip, daraus `Visbox.app` mit `Contents/MacOS/<Programm>`, `Contents/Info.plist` und
`Contents/Resources/Schriften/` (die Schriften der iPad-App unverändert, samt ihren
OFL-Lizenztexten), Behelfs-Unterschrift, ZIP. Unter Linux lässt sich nur der Kern prüfen
(`swift test` in `ipad/VisboxKern`).
