# Visbox auf dem iPad — die erste Probe

*Für den Owner. Stand 23.09.2026, nach den Wellen 2, 2b und 2c.*

Die App ist gebaut und übersetzt auf einem Mac ohne eine einzige Warnung. **Auf einem
echten iPad ist nichts davon gelaufen.** Was hier steht, ist darum zweierlei: eine
Anleitung, wie die App auf das iPad kommt, und ein Abnahmeblatt — die Liste der Dinge, die
nur ein Mensch mit Stift und Gerät prüfen kann.

Bis dieses Blatt ausgefüllt zurückkommt, heisst der Stand der App **«gebaut, am Gerät
unbestätigt»**.

---

## 1 · Was es braucht

| | |
|---|---|
| **iPad** | iPad Pro 11 (1. Generation), iPadOS 17 oder neuer, Apple Pencil 2 |
| **Rechner mit Visbox** | die HomeStation (oder jeder Rechner mit diesem Repo und Python 3) |
| **Netz** | iPad und Rechner im **selben** Heimnetz (WLAN), kein Gastnetz |
| **Weg A — Mac** | ein Mac mit Xcode 16 und einem kostenlosen Apple-Konto |
| **Weg B — ohne Mac** | die App «Swift Playgrounds» auf dem iPad (kostenlos im App Store) |

Mit dem kostenlosen Konto läuft die App **sieben Tage**, dann muss sie neu aufgespielt
werden (Entscheid 23). Das ist eine Regel von Apple, kein Fehler.

## 2 · Einmal vorher: die eigene Kennung eintragen

Jede App braucht eine Kennung, die weltweit nur einmal vorkommt. Im Repo steht ein
Platzhalter, `org.example.visbox`, der niemandem gehört — mit ihm lässt Apple die App nicht
auf ein Gerät.

1. Eine eigene Kennung wählen, z. B. `ch.<dein-name>.visbox` (nur Kleinbuchstaben, Punkte,
   keine Leerzeichen).
2. Sie an **zwei** Stellen eintragen, und zwar gleich:
   * `ipad/Visbox.swiftpm/Kern/Marke.swift` — die Zeile `kennung = "…"`
   * `ipad/Visbox.swiftpm/Package.swift` — die Zeile `bundleIdentifier: "…"`
3. Laufen die beiden auseinander, meldet die Prüfung (`tests/test_ipad_geruest.py`) es.

*Warum zwei Stellen:* Die Paketdatei kann die Quellen nicht lesen. Die Prüfung hält beide
zusammen.

## 3 · Die App auf das iPad bringen

### Weg A — mit dem Mac (empfohlen)

1. Das Repo auf den Mac holen (oder den aktuellen Stand ziehen).
2. In Xcode **`ipad/Visbox.swiftpm`** öffnen (Doppelklick genügt).
3. Oben als Ziel **«Visbox»** und als Gerät das **eigene iPad** wählen (per Kabel
   verbunden; beim ersten Mal fragt das iPad, ob es dem Mac vertraut).
4. Unter *Signing & Capabilities* das eigene Apple-Konto als Team wählen.
5. **Run** (▶). Beim ersten Start sagt das iPad, der Entwickler sei nicht vertrauenswürdig:
   *Einstellungen → Allgemein → VPN & Geräteverwaltung →* dem eigenen Konto vertrauen.
   Dazu *Einstellungen → Datenschutz → Entwicklermodus* einschalten, falls das iPad
   danach fragt.

### Weg B — nur mit dem iPad

1. Den Ordner `ipad/Visbox.swiftpm` auf das iPad bringen (iCloud Drive oder Dateien-App).
2. In Swift Playgrounds öffnen und oben rechts **ausführen**.

**Weg B ist nicht erprobt** — dass Swift Playgrounds das Paket öffnet, ist gebaut, aber nie
gesehen worden. Scheitert es, ist das ein Befund und keine Panne: bitte den Wortlaut der
Meldung notieren.

## 4 · Den Rechner bereit machen

Auf dem Rechner, im Repo-Ordner:

```sh
python3 oberflaeche/server.py --ordner <projektordner> --im-heimnetz --kennwort-erzeugen --kopplung
```

Der Rechner zeigt danach drei Dinge an:

* die **Adresse**, unter der er erreichbar ist,
* das **Kennwort** (braucht das iPad nicht einzutippen — die Kopplung besorgt es),
* eine **sechsstellige Zahl**. Sie gilt zehn Minuten, für **ein** Gerät, fünf Versuche.

Dazu eine Warnung, die ernst gemeint ist: Die Verbindung im Heimnetz ist **nicht
verschlüsselt**. Das Kennwort hält Geräte fern, die zufällig im Netz sind — nicht jemanden,
der mithört.

## 5 · Koppeln, zeichnen, senden

1. Die App öffnen. Beim ersten Mal fragt iOS, ob Visbox **Geräte im lokalen Netz** suchen
   darf — **erlauben**, sonst findet sie den Rechner nicht.
2. Die App sucht den Rechner **von selbst**. Erscheint er, antippen und die sechsstellige
   Zahl eingeben.
3. Mit dem Stift zeichnen. Finger schieben und zoomen.
4. **«In die Mappe legen»** (unten im Seitenfeld). Die Skizze fliegt zum Rechner.
5. **«Rechnen lassen»**. Die Laufanzeige zeigt, was der Rechner tut.
6. Das Bild erscheint im Bildband, mit Prüfzeichen (Farbe, Wort und Zahl).
7. Ein Bild antippen → **«Darauf skizzieren»** → es liegt unter dem Blatt; hineinzeichnen,
   ablegen, rechnen.

**Wichtig zu wissen, bevor man sich wundert:** Auf dem Vorgabe-Bildmodell kommt die
Skizze gemessen **nicht** im Bild an (auf-123, auf-137). Das Bild wird trotzdem gerechnet,
und der erste Hinweis daneben sagt «SKIZZE NICHT ANGEKOMMEN» (Entscheid E24). Das ist die
ehrliche Auskunft, kein Fehler der App.

## 6 · Das Abnahmeblatt

Je Zeile: **ja**, **nein** (mit einem Satz, was stattdessen geschah) oder **nicht geprüft**.
«Nicht geprüft» ist eine vollständige Antwort — eine erfundene «ja» ist schlimmer als eine
Lücke.

### A · Aufspielen und Start

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| A1 | Die App lässt sich aufspielen (Weg A oder B — welcher?) | |
| A2 | Sie startet ohne Absturz, quer und hochkant | |
| A3 | Die Frage nach dem lokalen Netz kommt, und nach «erlauben» geht es weiter | |
| A4 | Die eigenen Schriften erscheinen: Titel in einer Serifenschrift, Zahlen gleich breit (Plex Mono). Steht überall die Systemschrift, bitte die Konsolenzeile `Schriftregister` notieren | |
| A5 | *Nur Weg B:* Nach dem Ändern von Symbol oder Farbe in Swift Playgrounds startet die App noch (Playgrounds schreibt dabei das Manifest neu — die Schriftangabe könnte verloren gehen) | |

### B · Verbinden

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| B1 | Der Rechner wird von selbst gefunden (ohne Adresse eintippen) | |
| B2 | Die sechsstellige Zahl koppelt; eine falsche wird abgewiesen | |
| B3 | Nach einem Neustart der App ist sie noch gekoppelt (Kennwort im Schlüsselbund) | |
| B4 | Rechner aus → die Verbindungszeile sagt es ehrlich (nicht «verbunden») | |
| B5 | Skizze ablegen, während der Rechner aus ist → sie wartet im Parkfach und geht von selbst, sobald er wieder da ist | |

### C · Zeichnen

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| C1 | Der Stift zeichnet, der Finger schiebt und zoomt — nie umgekehrt | |
| C2 | Der Druck des Stifts ändert die Strichbreite | |
| C3 | Doppeltipp am Stift schaltet auf den Radierer und zurück | |
| C4 | Radierer für ganze Striche und flächig, umschaltbar | |
| C5 | 20 Schritte zurück — **auch nach dem Drehen des iPads** (die heikle Stelle) | |
| C6 | Ebene ausblenden: auf ihr wird nicht gezeichnet; der Finger schiebt weiter, der Stift schiebt **nicht** | |
| C7 | Nach flächigem Radieren bleibt das Zeichnen flüssig (kein Ruckeln) | |
| C8 | Erscheint je der Satz «liess sich nach dem Radieren nicht prüfen»? (sollte nicht) | |

### D · Senden und Rechnen

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| D1 | Die Übergabe-Marke fliegt sichtbar zum Rechner und rastet erst ein, wenn er die Skizze hat | |
| D2 | Im Vollbild verschwindet die Marke nicht mitten im Flug | |
| D3 | «Rechnen lassen» startet einen Lauf; die Laufanzeige bewegt sich | |
| D4 | «Abbrechen» — die App sagt zuerst «verlangt», dann, dass es gewirkt hat; Fertiges bleibt | |
| D5 | Drei Varianten: einmal «drei Startwerte», einmal «drei Ebenen» | |
| D6 | Mit eingeschalteter Bewegungsreduktion (Einstellungen → Bedienungshilfen) erscheint die Marke erst am Ziel | |

### E · Bilder und Urteil

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| E1 | Jedes Bild trägt sein Prüfzeichen: Farbe, Wort, und die Zahl **nur**, wo es ein Urteil gibt | |
| E2 | Der Hinweis «SKIZZE NICHT ANGEKOMMEN» steht beim Bild und lässt sich aufklappen | |
| E3 | Vorher/Nachher: Wischregler zwischen KI-Bild und Unterlage | |
| E4 | Einem Bild einen Namen geben; er steht danach auch am Rechner | |
| E5 | Teilen: das Bild geht mit seinem Prüfzeichen hinaus | |

### F · Unterlage

| Nr. | Prüfen | Ergebnis |
|---|---|---|
| F1 | «Darauf skizzieren» legt das Bild unter das Blatt | |
| F2 | Beim Schieben und Zoomen bleiben Bild und Striche **deckungsgleich** | |
| F3 | Unterlage ausblenden → die Tafel sagt, dass sie dann nicht mitgeht | |
| F4 | Das gerechnete Bild zeigt die Striche dort, wo sie auf der Unterlage lagen | |

## 7 · Was zurückkommt

Das ausgefüllte Blatt als Text genügt — in den Chat oder als Datei unter
`auftraege/ergebnisse/`. **Keine Bildschirmfotos mit echten Projekten**, keine Namen von
Büros oder Kunden (Regel 3). Wo ein Bild hilft, eine Skizze auf dem Testkörper.

Was «nein» ist, wird ein Posten mit Adressat; was «ja» ist, wird im Einbau-Stand abgehakt
— mit Datum und diesem Blatt als Beleg.
