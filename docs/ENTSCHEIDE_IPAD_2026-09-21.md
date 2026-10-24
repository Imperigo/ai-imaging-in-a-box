# Entscheide zur iPad-Oberfläche — 21.09.2026

**Grundlage:** keine — hier steht kein Messwert, sondern was der Owner entschieden hat
**Codestand:** `3ffbffd`

Zwanzig Fragen zum Entwurf, vom Owner am 21.09.2026 beantwortet. Diese Liste ist die
Grundlage für den Bau; was hier steht, wird nicht neu verhandelt.

Der Entwurf selbst liegt als Entwurfsfläche ausserhalb des Repos (elf Blätter). Diese
Datei ist die Fassung, die bleibt — *was nicht in einer Datei steht, ist weg.*

---

## Der Stift

| # | Frage | Entschieden |
|---|---|---|
| 1 | Querformat oder Hochformat | **Beide gleichwertig.** Eigene Anordnung je Haltung, gleicher Inhalt |
| 2 | Doppeltipp am Stift | **Radierer** |
| 3 | Was der Druck steuert | **Strichbreite** |
| 4 | Wer zeichnen darf | **Nur der Stift.** Der Finger schiebt und zoomt |
| 5 | Radierer | **Beides, umschaltbar** — ganze Striche und flächig |
| 6 | Tiefe von «Zurück» | **Die letzten 20 Schritte.** Fester Deckel |
| 7 | Ebenen | **Mehrere, frei anlegbar.** Jede Ebene ist eine Variante |
| 8 | Bedeutung der Stiftfarbe | **Keine.** Frei wählbar |

**Was Nummer 7 nach sich zieht, und es ist keine Kleinigkeit:** Wenn eine Ebene eine
Variante ist, muss entschieden sein, *was gerechnet wird.* Festgelegt: **gerechnet wird,
was sichtbar ist.** Eine ausgeblendete Ebene geht nicht mit. Sonst rechnet das Gerät etwas
anderes, als auf dem Schirm steht — und das ist derselbe Fehler wie ein erfundener
Fortschrittsbalken, nur eine Etage tiefer.

## Leiste und Bildschirm

| # | Frage | Entschieden |
|---|---|---|
| 9 | Wo die Werkzeugleiste sitzt | **Umlegbar per Knopf**, links oder rechts |
| 10 | Vollbild | **Ja, mit einem Wisch von unten** |

## Das Rechnen

| # | Frage | Entschieden |
|---|---|---|
| 11 | Nach «In die Mappe legen» | **Bleibt offen liegen.** Nichts rechnet von selbst |
| 12 | HomeStation nicht erreichbar | **Lokal parken**, später von selbst nachschicken |
| 13 | Rechnet das iPad selbst | **Nie.** Ein Ort, ein Ergebnis, vergleichbar |
| 14 | Abbruch eines Laufs | **Fertiges bleibt in der Mappe** und wird nicht neu gerechnet |

## Das Urteil

| # | Frage | Entschieden |
|---|---|---|
| 15 | Prüfen oder Entwerfen | **Schalter am Bild**, jederzeit umlegbar |
| 16 | Was das Abzeichen trägt | **Farbe, Wort und Zahl** — immer, auch beim Teilen |
| 17 | Vorher und Nachher | **Beides umschaltbar**: nebeneinander und Wischregler |

## Die Mappe

| # | Frage | Entschieden |
|---|---|---|
| 18 | Varianten nebeneinander | **Drei** |
| 19 | Benennung | **Nach der Zeit**, ein eigener Name nachträglich möglich |
| 20 | Was beim Teilen mitgeht | **Bild mit Prüfzeichen** |

**Was Nummer 20 entscheidet, ohne gefragt worden zu sein:** Wenn das Prüfzeichen in das
geteilte Bild hineingerechnet wird, muss die Schrift dafür **auf dem Gerät** liegen. Eine
Schrift von einem fremden Server ist eine Netzverbindung, und die Auflage dieses Projekts
lautet, dass zum Start keine nötig sein darf. Also: **Schriften werden mitgeliefert, nicht
geladen.** Damit bleibt auch die zweite Schriftfrage beantwortet — eigene Schriften sind
zulässig, solange sie im Paket stecken und permissiv lizenziert sind.

---

## Die Verbindung zwischen iPad und Rechner

**Owner-Wunsch vom 21.09.2026:** Die beiden Geräte sollen als *ein* zusammenhängendes
Werkzeug wirken — das Senden einer fertigen Skizze soll als Bewegung beginnen und auf dem
Rechner weitergehen.

**Der Gedanke, auf den es hinausläuft:** Ein Gegenstand, ein Weg. Die Skizze verschwindet
auf dem iPad nicht und taucht drüben auf, sondern **reist**: Sie schrumpft auf eine Marke
zusammen, wandert an den Rand, auf dem der Rechner liegt, fliegt auf einem Faden hinüber
und legt sich dort als **dieselbe Marke** oben in die Warteschlange — gleiche Farbe,
gleiche Form, gleiche Grösse. Kommt das Bild zurück, nimmt es denselben Faden und legt
sich genau an die Stelle, von der die Skizze kam.

**Vier Regeln, und alle vier sind Anwendungen der bestehenden Lehre auf die Bewegung:**

1. **Bewegt sich etwas, ist etwas unterwegs.** Eine Animation, die weiterläuft, während
   nichts passiert, ist eine Lüge mit Zeitverlauf — dasselbe wie ein erfundener Balken.
2. **Gleichmässig heisst gezählt.** Der Flug läuft nur dort gleichmässig, wo Bytes
   gezählt werden. Wo nur gewartet wird, atmet die Marke an Ort und Stelle.
3. **Die Animation endet nicht vor der Ankunft.** Sie hält kurz vor dem Ziel und rastet
   erst ein, wenn die Gegenseite bestätigt hat. *Eine Animation, die vor der Ankunft
   endet, behauptet eine Ankunft.*
4. **Ein Gegenstand, ein Weg.** Was abhebt und was landet, ist dieselbe Marke — nie zwei
   Dinge, die sich ähnlich sehen.

**Und der Abbruchfall gehört dazu:** Bricht die Verbindung, hört die Bewegung auf der
Stelle auf und die Marke **fällt zurück aufs iPad**. Sie verschwindet nie in der Mitte.

**Zeiten:** Ablegen 220 ms, Abheben 180 ms, Flug so lange wie die Übertragung wirklich
dauert, Einrasten 140 ms nach der Bestätigung, Warten als Atmen mit 1.8 s.

**Bewegungsreduktion:** Wer am Gerät Bewegung abgestellt hat, bekommt denselben Weg ohne
Bewegung — die Marke erscheint am Ziel, der Balken bleibt. *Eine Aussage, die nur in der
Bewegung steckt, ist für diese Leute keine Aussage.*

---

## Nachtrag 22.09.2026 — die App, und wie sie gebaut wird

Zwanzig weitere Fragen, vom Owner am 22.09.2026 beantwortet. Anlass: Die Bestandsaufnahme
zeigte, dass die Webseite die meisten der zwanzig Entscheide oben nicht trägt — und dass
es nirgends eine native iPad-App gibt. Geprüft wurden auch die eigenen früheren Arbeiten:
KosmoOrbit hat eine Zeichen-Webseite mit QR-Kopplung (nie am echten iPad gelaufen), das
Codex-Repo eine Zahlenkopplung mit einem SwiftUI-Client **für den Mac**. Übernommen werden
Abläufe und Lehren, kein Code.

| # | Frage | Entschieden |
|---|---|---|
| 21 | Webseite oder eigene App | **Eigene native App «Visbox»** (SwiftUI + PencilKit), jetzt |
| 22 | Wo sie gebaut wird | **Xcode und Swift Playgrounds**, beide vorbereitet; die Prüfstrecke auf GitHub übersetzt sie |
| 23 | Apple-Konto | **Kostenlos**: die App läuft je 7 Tage, dann neu aufspielen |
| 24 | Radierer | **Doppeltipp am Pencil 2** (in der App nativ; die Webseite hätte ihn nicht gesehen) |
| 25 | Schriften | **IBM Plex / Instrument Serif unter OFL zugelassen** (CLAUDE.md, Regel 1) |
| 26 | Koppeln | **Sechsstellige Zahl**; für die Web-Fläche eine kleine Koppelseite ohne Kennwort |
| 27 | Finden | **Automatisch** — ein eigener kleiner Rundruf im Heimnetz, nur mit Python-Bordmitteln |
| 28 | Parken | Skizzen bleiben auf dem Gerät und gehen hinaus, sobald der Rechner erreichbar ist |
| 29 | Vollbild | **Knopf**; als App ohnehin ohne Browserleiste |
| 30 | Entwerfen | **Schnell, ohne Geometrieprüfung**, blaues Zeichen «Entwurf — nicht geprüft» |
| 31 | Abbrechen | **Jetzt mitbauen**, auch im Kern; Fertiges bleibt |
| 32 | Drei Varianten | **Beides wählbar**: drei Startwerte **oder** drei Ebenen |
| 33 | Name | **Visbox** |
| 34 | Zukunft | **Nach der Abgabe werden Visbox (Rechner und iPad) wieder in die KosmoOrbit-Software integriert; die iPad-App wird zur KosmoSketch-App.** Darum steht der Name an einer Stelle, und das Protokoll ist offen beschrieben (`docs/VISBOX_PROTOKOLL.md`) |

**Was 21 kostet, und es steht hier, damit es später nicht überrascht:** Die App wird hier
geschrieben, aber nicht auf einem Mac übersetzt. Übersetzt wird sie in der Prüfstrecke auf
GitHub; aufs iPad bringt sie nur der Owner. Bis dahin heisst jeder Teil «gebaut, am Gerät
unbestätigt».

## Was daraus noch nicht entschieden ist

* ~~**Wie die Geräte sich finden.**~~ *Entschieden am 22.09.2026 (Nr. 27): automatisch,
  eigener Rundruf.*
* ~~**Was bei zwei iPads passiert.**~~ *Gebaut am 22.09.2026: Jede Mappe trägt eine
  Standnummer; wer auf einem veralteten Stand speichert, wird abgewiesen
  (`projekt.ProjektKollision`), statt still zu überschreiben. Nachgeführt am 23.09.2026.*
* **Wie gross eine Skizze werden darf**, bevor das Senden spürbar wird. Ohne Messung am
  Gerät ist das eine Vermutung — also ein unverschickter Auftrag und keine offene Frage.

---

## Nachtrag 23.09.2026 — was der Bau gezeichnet brauchte

Die Regel heisst «erst zeichnen, dann bauen». Die Welle 2b (Commit `f8f2a40`) brauchte
Dinge, die kein Blatt zeigte: die Unterlage unter den Ebenen, «Darauf skizzieren», die
getrennte Zählung am Knopf zum Parkfach und ein paar Wörter. Sie sind hier **nachträglich**
auf die Blätter der Entwurfsfläche gezeichnet — so, wie sie gebaut sind, und als Teil des
Bildschirms, nicht als Fussnote. Wo ein Blatt schon voll war, steht das Neue als **zweiter
Zustand im selben Blatt** (ein Schalter auf dem Blatt, oder eine zweite Lage darunter).
Kein Blatt wurde angelegt, umbenannt oder verschoben.

**Die Nummern N1 … N11 sind keine Entscheide.** «nach Blatt» heisst: Blatt und Bau sagen
jetzt dasselbe, zu entscheiden ist nichts. «gebaut, Owner-Entscheid offen» heisst: so gebaut
und so gezeichnet, aber das Wort oder die Farbe hat der Owner nicht gewählt — auf dem Blatt
trägt die Stelle das Schild «Owner-Entscheid offen». Entscheidet der Owner, bekommt der
Entscheid eine eigene Nummer ab 35.

| Nr. | Was | Blatt | Stand |
|---|---|---|---|
| N1 | Die Beschriftung des Vergleichs: «Unterlage» statt «Aus dem Modell», «UNTERLAGE · hier kein Urteil» statt «VERGLEICHSBILD · kein Urteil nötig»; beim Wischregler darüber «Links die KI, rechts die Unterlage» und am Bild die Marken «AUS DER KI» und «UNTERLAGE · hier kein Urteil»; unter dem Vergleich «Unterlage: ‹Dateiname›». Grund: Das Vorher ist die Unterlage, das Bild, über das skizziert wurde — und das kann ein früheres Bild der KI sein. «Aus dem Modell» wäre dann falsch | Bilder | gebaut, Owner-Entscheid offen |
| N2 | «Darauf skizzieren» als Knopf (60 px) zuoberst im Seitenfeld der Bildansicht, Abschnitt «Skizzieren», mit dem Satz, dass nur die Striche gesendet werden. Der Verweis «Darauf zeichnen» in der Kopfzeile des Blatts ist dafür weg — ein Weg, nicht zwei | Bilder | nach Blatt |
| N3 | Die Unterlage als unterste Lage unter den Ebenen. Der Titel über dem Blatt heisst «Skizze über Lauf 07 · Variante B» — «über» nur, wenn die Unterlage mitginge; sonst «Skizze · Variante B» | Main, MainHoch | nach Blatt |
| N4 | In der Ebenentafel die Unterlage als unterste, **gestrichelte** Zeile: Einblenden/Ausblenden, Entfernen (44 px), nicht wählbar, ohne Deckkraft. Sie ersetzt die frühere Zeile «Bild aus Lauf 07 · 100 %», die wie eine Ebene aussah | Main, MainHoch | nach Blatt |
| N5 | Der Satz unter der Zeile, aus derselben Regel wie das Ablegen: «Die Unterlage ist ausgeblendet: Die Skizze geht ohne sie hinaus und wird auf Grau gerechnet — gerechnet wird, was sichtbar ist» (Entscheid 7). «MainHoch» zeigt diesen Zustand von sich aus, «Main» den sichtbaren; beide lassen sich umschalten, und das Bild unter den Strichen verschwindet dabei mit | Main, MainHoch | nach Blatt |
| N6 | «In die Mappe legen» fest am Fuss des Seitenfelds — geprüft: Er stand schon dort. Neu gezeichnet ist, dass der Inhalt darüber rollt und der Knopf nicht mitrollt. Der Satz darunter wie gebaut: gerechnet wird erst auf «Rechnen lassen» in der Mappe, nicht mehr «wenn die HomeStation den Auftrag nimmt» — das klang, als nähme sie ihn von selbst (Entscheid 11) | Main, MainHoch | nach Blatt |
| N7 | «Zeichen unbekannt» als dritte Lage unter «Wie die Zeichen am Bild sitzen»: dasselbe Gelb wie «nicht gemessen», gestrichelt, unterschieden durch das Wort. Ein eigener Ton kommt nur mit einem Entscheid des Owners | Zeichen | nach Blatt; eigener Ton: Owner-Entscheid offen |
| N8 | Der Knopf zum Parkfach zählt getrennt: «2 geparkt · 1 ungewiss · 1 unterwegs · 1 offen» — nur Teile, die nicht null sind, in fester Folge —, dazu die Bedeutung jedes Worts. Auf dem Blatt als zweiter Zustand (Schalter «Knopf zum Parkfach» unten rechts) | Verbindung | nach Blatt |
| N9 | Das Wort «offen» ist doppelt belegt: im Knopf zum Parkfach heisst es «braucht einen Menschen» (abgewiesen, ungewiss ohne Schlüssel, oder ungewiss nach fünf Versuchen), in der Mappe «abgelegt, wartet, bis jemand ‹Rechnen lassen› wählt» (Projekt, Main, MainHoch, Skizzen). Gezeichnet ist der Stand, beide nebeneinander | Verbindung | gebaut, Owner-Entscheid offen |
| N10 | «Abbruch verlangt» nach dem Tippen: gesperrt, mit dem Satz, woher das «verlangt» kommt (von der HomeStation vermerkt, oder nur von diesem iPad) — verlangt ist nicht gewirkt. Als zweiter Zustand unter dem Knopf | Lauf | nach Blatt |
| N11 | Die Kopfzeile über den Schritten: «Variante 2 von 3 · Prüfen» (oder «Entwerfen», wie bestellt). Fehlt ein Feld, fehlt sein Teil | Lauf | nach Blatt |

**Was beim Nachziehen auffiel und nicht gezeichnet ist.** Es liegt hier, bei der
Entwurfsfläche und dem iPad-Bau, nicht bei einem der drei Worker:

* Das Seitenfeld der App hat einen Umschalter «Ebenen | Mappe» und den Satz «Geht mit:
  n von m Ebenen». Beides fehlt auf «Main» und «MainHoch».
* Der Abschnitt «Stift» (Druck, Finger, Farben) steht auf «Main» im Seitenfeld, in der App
  nicht. Auf dem Blatt rollt er jetzt unter den Fuss.
* «Kanten aus dem Modell» ist auf «Main» eine Ebene; die App kennt keine solche Ebene.
* «Lauf abbrechen» ist auf «Lauf» rot umrandet, und Rot heisst sonst «durchgefallen». Die
  App zeichnet den Knopf neutral.
* Der Satz «Beim Teilen geht das Zeichen mit» steht auf «Bilder» gelb; die App setzt ihn
  leise, weil Gelb «nicht gemessen» heisst.
* Drei Stellen im Bau sprachen noch vom alten Blatt: der Kommentar in
  `ipad/Visbox.swiftpm/Leiste/Mappenknopf.swift` («Der Satz weicht vom Blatt «Main» ab»),
  die Abschrift in `PruefzeichenTests.testJederFarbtonStehtSoAufDemBlatt` («Kein eigener
  Eintrag auf dem Blatt» bei «Zeichen unbekannt») und der Kommentar in
  `Bilder/Bildvergleich.swift` («bis das Blatt nachgezogen ist»). **Nachgezogen am
  23.09.2026**, in derselben Sitzung.
* **Der Abgleich Blatt ↔ Bau ist von Hand gemacht** (23.09.2026) und von keiner Probe
  gehalten. Ändert sich ein Satz in der App, veraltet «nach Blatt» still. Wer einen der
  Sätze N1–N11 in der App ändert, zieht das Blatt mit.

**Stand der Fläche:** Die Blätter sind am 23.09.2026 in der Arbeitskopie der
Entwurfsfläche nachgezogen und geprüft: wohlgeformtes HTML, jede Variable der Blattlogik
belegt, jeder neue Zustand einmal durchgeschaltet. Gesehen ist davon nichts — hier gibt es
keinen Browser. **Veröffentlicht am 23.09.2026** (Fassung 6 der Entwurfsfläche), mit zwei
Berichtigungen auf «Verbindung»: «offen» im Knopf auch nach fünf Versuchen, und «Main» in
der Liste der Blätter, auf denen «offen» in der Mappe steht.

## Nachtrag 30.09./01.10.2026 — die Vorführfassung am Mac

Owner-Wunsch: ein herunterladbarer Stand für Mac und iPad zum Präsentieren; beim Öffnen am Mac
baut sich alles selbst auf. Gezeichnet auf der Entwurfsfläche, Blätter 13, 13b und 14
(Sitzung 73 §25, §28; Sitzung 74).

| Nr. | Frage | Entscheid |
|---|---|---|
| 35 | Wo wird präsentiert? | **Auswärts** (z. B. ETH) — der Mac erreicht den Heim-PC über das Internet, verschlüsselt |
| 36 | Apple-Entwicklerkonto? | **Nein** — iPad über Swift Playgrounds oder per Kabel vom Mac; Mac-App beim ersten Öffnen mit Rechtsklick → Öffnen |
| 37 | Sprachmodell? | **Ein Assistent wie Kosmo in KosmoOrbit** — stellt Kamera, Bildauftrag und Varianten ein; das Modell läuft am Heim-PC und muss Regel 1 bestehen |
| 38 | Start am Mac | **Die vier Zeilen sichtbar** (Leitung, Heim-PC, Assistent, iPad), jede mit Satz (Blatt 13) |
| 39 | Anfangen, bevor alles steht | **Ja** — «Schon anfangen», bevor der Assistent geladen ist |
| 40 | Vorführmodus | **Von selbst**, wenn der Heim-PC nicht antwortet — mit eigener Farbe und Datum an jedem vorher gerechneten Bild (Blatt 13b) |
| 41 | Was der Assistent darf | **Vorschlagen und auf «Anwenden» warten**, wie Kosmo — gerechnet wird nie ohne (Blatt 14) |
| 42 | iPad unterwegs | **Über den Mac** — gleiches WLAN oder Hotspot des Mac, nicht ins Heimnetz |

## Nachtrag 01.10.2026 — zwanzig Antworten für v0.1.7

Vor dem Vollbau 01.–03.10.2026 gefragt, nach dem Owner-Wunsch «stelle mir 20 Fragen». Der Plan
dazu: `docs/PLAN_V017_2026-10-01.md` (Sitzung 74 §4).

| Nr. | Frage | Entscheid |
|---|---|---|
| 43 | Was liefert Visbox mit v0.1.7? | **Beides** — Mac-Vorführfassung und die offenen Vertragsposten beim Integrator |
| 44 | Form der Mac-App | **Eigene Visbox-App**, teilt den Kern mit der iPad-App; nicht Teil der Mac-Fassung von KosmoOrbit |
| 45 | Abgabe an den Integrator | **Freitag, 03.10.2026, abends** |
| 46 | Wie parallel | **Claude + Hilfsagenten** in getrennten Arbeitskopien, zentral geprüft |
| 47 | iPad unterwegs | **Über den Mac** (bestätigt Entscheid 42) |
| 48 | Assistent in v0.1.7 | **Erste Fassung** — Chat, drei Werkzeuge, Vorschlag + «Anwenden» |
| 49 | Bilder im Vorführmodus | **Synthetische Beispiele**, am Heim-PC vorher gerechnet |
| 50 | Auftrag 214 | **Go** am 01.10.2026 |
| 51 | `lieferstatus: null` («nicht festgestellt») | **KosmoOrbit lässt es zu**, als Vorbehalt; die Bilder bleiben |
| 52 | Lizenzmarke Qwen-2.1 | **«Lizenz wie offen behandeln bis v1.0»** — gelesen als: Marke mitführen, nicht verwerfen; Anzeige und Sperre bis v1.0 entscheiden; E128 gilt vor jeder Veröffentlichung |
| 53 | Union-2.1 drüben bestellbar | **Nein**, bleibt Messschalter bei uns |
| 54 | Formprüfung drüben sichtbar | **Nein**, nur intern |
| 55 | Sammel-Nachprobe am Gerät | **Ja**, alle «gebaut, am Gerät unbestätigt» |
| 56 | Entwurfsmodus in v0.1.7 | **Nein** — Entscheid bis 15.10., Bau in v0.1.8 |
| 57 | Freigabe-Taste | **«Anwenden» bleibt** (Entscheid 41); angeglichen beim Einbau in KosmoOrbit |
| 58 | Mac-App auf den Mac | **Fertige App zum Herunterladen** aus der Prüfstrecke |
| 59 | Geräte bis Freitag | **Ein Mac mit Apple-Chip**, kein iPad |
| 60 | Probe am Gerät | **Erst nach der Abgabe** |
| 61 | Meldungen im Vollbau | **Morgens und abends kurz** |
| 62 | Abgabeform | **Ein Lieferblatt v0.1.7** im Eingang des Integrators |

**Korrektur zu Entscheid 36:** «Rechtsklick → Öffnen» öffnet auf macOS 15 eine App ohne
Apple-Unterschrift nicht mehr. Der Weg ist: einmal öffnen, dann *Systemeinstellungen →
Datenschutz & Sicherheit → «Trotzdem öffnen»*. Am Entscheid ändert das nichts, nur am Satz
auf Blatt 13.

## Nachtrag 01.10.2026, abends — das iPad unterwegs

| Nr. | Frage | Entscheid |
|---|---|---|
| 63 | Wie kommt das iPad unterwegs zum Heim-PC, nachdem die Durchsicht gezeigt hat, dass iPad ↔ Mac im fremden WLAN unverschlüsselt wäre? | **Direkt über Tailscale** — Tailscale-App auch aufs iPad, die App spricht https mit dem Heim-PC. Der Mac gibt dem iPad beim ersten Mal nur die Zahl zum Koppeln (er fragt sie am Heim-PC ab). **Ersetzt Entscheide 42/47** für die Vorführung; die Vermittlung über den Mac bleibt im Code, aber ausgeschaltet, bis man sie einschaltet. Verworfen: «eigener Hotspot, später verschlüsseln» (empfohlen gewesen) und «jetzt verschlüsseln» (ein Tag, gefährdet die Abgabe). |
| 64 | Soll die Vorführmappe ein durchgefallenes Bild zeigen (Westblick, «Bild im Bild», `auf-20261001-220`)? | **Ja, es bleibt drin** — die Mappe zeigt, dass Visbox ein falsches Bild erkennt und benennt. Verworfen: nur bestandene Bilder; beide Fassungen umschaltbar. |
| 65 | Wer baut, was Visbox drüben in KosmoOrbit braucht? (Owner, 01.10.2026: «der Integrator integriert in die Software und baut auch seine eigenen Dinge … damit heben wir den Flaschenhals auf») | **Wir bauen selbst** — alles für Visbox und das KosmoVis-Werkzeug im KosmoOrbit-Repo, **auf eigenem Zweig**, mit ihren Proben und Toren grün, und melden ihn KosmoOrbit Int 1 mit einem Blatt. **Nur Int 1 führt zusammen** (wie die Hilfs-Sitzungen Int 2–5). Sofort angewandt: P1 (Lieferstatus «nicht festgestellt») und P2 (Hinweise am Bild) des Lieferblatts v0.1.7 baut KosmoVis selbst; P3 (Raumliste Prepare) bleibt beim Integrator. |
| 66 | Welche Versionsnummer trägt Visbox? (bis dahin drei verschiedene: Bibliothek 0.0.1/0.0.2, iPad-App 0.1, Mac-App 0.1.7) | **0.1.0, eigene Zählung** — Bibliothek, iPad-App und Mac-App überall gleich (bewacht in `tests/test_versionsnummer.py`); die erste vorführbare Fassung ist die Abgabe vom 03.10.2026. Welche KosmoOrbit-Fassung dazu passt (heute 0.1.7), steht im Lieferblatt. Das KosmoVis-Werkzeug in KosmoOrbit trägt keine eigene Nummer, es ist Teil der KosmoOrbit-Fassung. |
| 67 | Eine Kamera über dem Dach (KosmoOrbits Auto-Kamera «Übersicht», 16 m bei 6 m Gebäude) — abweisen wie bisher (HABS/NPS) oder rechnen? | **Rechnen, mit Vorbehalt** — als Auskunft «Aufsicht, nicht nach den Regeln für Architekturaufnahmen beurteilt» in `qa.verdict.hinweise`; Augenhöhe-Kameras bleiben streng. Anlass: Sammel-Nachprobe `auf-20261001-230` — jeder Auto-Auftrag galt bis dahin als «fehlgeschlagen». |
| 68 | Der Render-Knoten der Vis-Station hält nur den letzten Lauf; ein neues «Ausführen» ersetzt das Bild am Knoten (Befund der HomeStation in 246/250). Soll er mehr zeigen? (Frage über die Zentrale, 07.10.2026) | **B — kleiner Verlauf am Knoten, in v0.1.8**: die letzten 3–5 Läufe als Daumenbilder unter dem Hauptbild, ein Klick zeigt das Bild gross, nichts wird gelöscht. Vorgehen: erst ein Blatt auf der Entwurfsfläche, dann bauen. Nicht mehr in v0.1.7. Verworfen: A (so lassen), C (Verlauf mit Vergleich am Knoten). Antwort des Owners über die Zentrale (ausgewählt). Bei KosmoOrbit als **E170** geführt. **Ausgestaltung (Owner, 07.10.2026):** die letzten **4** Läufe in einer Reihe, das neueste links, jedes mit Urteilspunkt; ein Klick zeigt das Bild **nur gross** — das Hauptbild bleibt der letzte Lauf. Gezeichnet als Blatt 15 auf der Entwurfsfläche, **vom Owner so abgenommen** (07.10.2026, über die Zentrale; bei KosmoOrbit **E174**). |
| 69 | Die Visbox-App für den Mac trägt die Platzhalter-Kennung `org.example.visbox.mac`; ein späterer Wechsel verliert das im Schlüsselbund gespeicherte Kennwort. Wann und wie wird sie gesetzt? (07.10.2026) | **Später, mit dem Apple-Konto** — der Platzhalter bleibt, bis der Owner die App mit seinem Konto signiert; dann wird die Kennung passend zum Konto gewählt. Verworfen vorerst: eine neutrale Kennung nach dem öffentlichen Repo, eine eigene Domain. |
| 70 | Füllt das Haus weniger als 20 % des Bildes (Modelle ohne Boden, z. B. das Demohaus aus KosmoOrbit: 17–20 %), ist der Gesamtwert der Prüfung rechnerisch unerreichbar, und jedes Bild fiel durch. Was soll dastehen? (Befund `auf-20261008-265`) | **«Nicht beurteilbar» statt «durchgefallen»** — mit dem Grund «Haus füllt weniger als 20 % des Bildes, der Gesamtwert ist hier nicht anwendbar» und der Gebäude-Zahl als Auskunft (nicht geeicht, urteilt nicht). Ab 20 % bleibt alles wie bisher. Verworfen: so lassen; die Gebäude-Zahl ab 0,80 entscheiden lassen (trennt nach Entscheid vom 30.09.2026 nicht); eine Bodenplatte unterlegen. Owner per Auswahl, 08.10.2026, im Chat und über die Zentrale gleichlautend. *Die erste Fassung der Frage enthielt eine falsche Angabe (0,80 «geeicht»); ihre Antwort «Gebäude-Prüfung entscheidet» ist damit ersetzt* (Protokoll 74 §68). Gebaut: `tiefenschaetzer.qa_gegen_soll` (`gesamtwert_anwendbar`). |
| 71 | Verlauf am Render-Knoten: Die Uhrzeitzeile unter den Daumenbildern macht den Knoten so hoch, dass er an der Palettenstelle 8 px über den Fensterrand ragt; mittig verdeckt der ⇄-Knopf zwei Uhrzeiten halb (`auf-20261007-263` V6). | **Uhrzeiten unter den Daumenbildern weglassen** — der Knoten wird 14 px niedriger; die Zeit bleibt im Laufschild, in der grossen Ansicht und im Vorleser-Label. Weicht von Blatt 15 ab, bewusst. Verworfen: so lassen. Owner per Auswahl, 08.10.2026. |
| 72 | Bild-Kachel: Der Prüf-Satz (`verdict.reason`) wird nach einer halben Zeile abgeschnitten (`auf-20261008-267` B2). | **Eine Zeile mit «…», der volle Satz in der Kurzhilfe** (beim Darüberfahren); vorher als Blatt gezeichnet. Verworfen: so lassen. Owner per Auswahl, 08.10.2026. |
| 73 | Der Satz `standpunkt_vorgabe` («Kein Standpunkt bestellt — von Süden gerechnet») steht nur im Ergebnis, nicht am Bildschirm. | **Sichtbar auf Fläche und iPad**, als kleiner Satz unter dem Bild; vorher als Blatt gezeichnet. Verworfen: so lassen. Owner per Auswahl, 08.10.2026. |
| 74 | «Nicht beurteilbar» reist zu KosmoOrbit als `passed: false` plus Satz; die Anzeige liest den Satz. Eigener dritter Zustand im Vertrag? | **Später, in Ruhe** — nach v0.1.8, als Vertragsänderung beim Integrator. Heute funktioniert es richtig. Verworfen: jetzt angehen (bindet ihn im Schnitt von v0.1.7); nie. Owner per Auswahl, 08.10.2026. |
| 75 | Sehr lange, flache Bauten (Splat-Demo der HomeStation: Halle 66 × 10 × 3,45 m) füllen bei der Rahmung «ganzes Bauwerk auf 70 % der Bildbreite» (Entscheid 28.08.2026) nur 3,8–4,5 % des Bildes und sind «nicht beurteilbar». Wie sollen die automatischen Ansichten sie zeigen? | **Näher, als Ausschnitt:** Ist das Bauwerk viel breiter als hoch, rückt die Kamera so nah, dass es mindestens rund ein Viertel des Bildes füllt; die Enden dürfen aus dem Bild laufen. Verworfen: eine zusätzliche Ansicht längs; so lassen. Owner per Auswahl, 08.10.2026. |
| 76 | Der Splat (Aufnahme der Umgebung) kommt nicht ins Bild — `RenderScene` kennt nur glb und IFC. Wann angehen? | **Jetzt, vor allem anderen.** Verworfen: erst nach v0.1.8 prüfen; vorerst nicht. Owner per Auswahl, 08.10.2026. |
| 77 | Am echten Splat (`auf-20261008-271`) malt Z-Image aus den Punkten der Umgebung «Konfetti» (Kreisscheiben, 18 von 18 Bildern): die Aufnahme ist lückig, das Tiefenbild zeigt einzelne Scheiben. Wie geht die Umgebung ins Bild? | **Glätten** (Owner, 08.10.2026, per Auswahl): Lücken der Umgebung im Tiefenbild schliessen (nur auf Hintergrund, nie auf dem Bauwerk), ihre Tiefe über ein Fenster mitteln; dazu bekommt das Modell das mittlere Grauband, die Umgebung davor und dahinter gestaucht. Verworfen: «nur ruhige Kulisse» (grobe Silhouette, Bäume bleiben unscharf), «nicht ins KI-Bild» (verfehlt Entscheid 76). Wirkung misst `auf-20261008-273`. |
| 78 | Ohne Umgebung sagt die Prüfung an der Halle «nicht messbar» (`auf-20261008-272`: Haus 23–28 % des Bildes, ρ 0,99 auf dem Haus, 0 gemeinsame Punkte) — das Modell hat keinen Boden, das Bild schon; die Hintergrundmarkierung nimmt das Haus als Hintergrund. Was soll gelten? | **Messboden** (Owner, 08.10.2026, per Auswahl): Hat das Modell gemessen kein Gelände, rechnet die Prüfung mit einer gedachten Ebene auf Geländehöhe — nur in der Soll-Karte, das Bild sieht sie nicht. Verworfen: «immer nicht beurteilbar» (solche Modelle bestünden nie), «so lassen» (gute Bilder sähen durchgefallen aus). Gegen echtes Blender geprüft (Mittel 1,3 mm); Wirkung misst `auf-20261008-274`. |
| 78a | Nachtrag zu 78 (`auf-20261008-274`): Der Messboden «schenkt» einen Teil der Punktzahl (Halle 0,98 statt geschätzt ~0,91; bei «Übersicht» füllt der Boden das ganze Bild). Soll er in die Punktzahl zählen? | **Nur zum Trennen** (Owner, 13.10.2026, per Auswahl): Der Boden hilft nur, Haus und Hintergrund im Bild zu trennen; Score, geom_iou und Anteil zählen allein das Haus. Verworfen: «mitzählen wie jetzt». Dazu behoben: Messboden nur bei **gemessener** Maske (274 C3). |
| 79 | Das Konfetti bleibt auch mit Radius 50 (274: Tafeln und Klötze). Owner-Frage: «wo liegt der Fehler?» — bei uns: Der Splat wird als harte Kugeln gezeichnet, 70 % verworfen, ohne Form und weiche Mischung. Offizielle Wege geprüft (Lizenzen siehe `docs/SPLAT_WEGE_2026-10-13.md`). | **Offener Weg im Produkt + Brücke zu RealityScan, wo selbst installiert** (Owner, 13.10.2026): gsplat (Apache-2.0) + Open3D (MIT) machen aus dem Splat ein echtes Netz, mitgeliefert wie Blender; RealityScan (Epic, proprietär) macht aus den Fotos ein besseres Netz, nur als vom Nutzer installiertes Fremdprogramm (neue Präzisierung in `CLAUDE.md`). Verworfen: nur RealityScan, nur offen. Die Frage nach einer **lichtaktiven Splat-Oberfläche** an Bauteilen (relightable Gaussian Splatting) als Forschungsfrage festgehalten, nicht gebaut. |
| 80 | Die Brücke zu RealityScan braucht eine Installation durch den Owner selbst (Regel Fremdprogramme). Wann? | **Später** (Owner, 13.10.2026, per Auswahl): Zuerst wird der offene Weg (gsplat + Open3D) gebaut und gemessen; RealityScan danach. Die Fotos liegen am Heim-PC (960 Bilder, 4 Richtungen, mit Masken). Verworfen: «jetzt installieren», «lieber nicht». |
| 81 | Die Umgebung trägt nach 276/277 nur ~10 % bei; Tiefenfilter und Masken helfen am echten Splat nicht, ein Filter nahm sogar das Netz. Offene Fotogrammetrie ist kaum erlaubt (OpenMVS AGPL, COLMAP-Netzbildung an GPL-Code). Wie weiter? | **RealityScan jetzt** (Owner, 13.10.2026, per Auswahl; ersetzt «später» aus 80): Der Owner installiert es selbst; die Brücke macht aus den 960 Fotos mit den Kamerastandorten (`-importColmap`) ein Netz. Der offene Weg bleibt Rückfall. Verworfen: «so lassen», «offen weiterforschen». |
| 82 | Visbox stand seit 03.10. auf 0.1.0; seither 164 Änderungen (Umgebung, Messboden, Ausschnitt, RealityScan-Brücke). Welche Nummer, wann? | **0.2.0 jetzt** (Owner, 13.10.2026, per Auswahl): überall gleich, Fassungsblatt `docs/VISBOX_0.2.0_2026-10-13.md`. Verworfen: 0.1.1, «warten auf KosmoOrbit 0.1.8 und RealityScan». |
| 83 | Erster echter Start der Mac-App 0.2.0 (13.10.2026): «Einrichten» verlangt Adresse, Benutzer und Kennwort von Hand. Geht das ohne Eintippen? | **Koppeln mit Zahl** (Owner, per Auswahl; Blatt 17): Der Mac sucht den Heim-PC selbst, der Heim-PC zeigt eine 6-stellige Zahl (5 min, einmal, 3 Fehlversuche), die Geräte tauschen den Rest aus. Verworfen: Einrichtungs-Link, «vorerst von Hand». |
| 83a | Wo erscheint die Zahl am Heim-PC? | **Im Fenster des Dienstes und als Mitteilung am Bildschirm** (Owner, per Auswahl). Verworfen: nur im Fenster. |
| 83b | Wer darf koppeln? | **Tailscale-Netz und auch Heim-WLAN** (Owner, per Auswahl; Empfehlung war nur Tailscale). Bau: im WLAN nur mit TLS und angeheftetem Zertifikat, nie Klartext. |
| 83c | «Von Hand eintragen» behalten? | **Ja, als kleiner Link** (Owner, per Auswahl). |
| 84 | Ein Aktualisieren-Knopf, wenn eine neue Fassung auf GitHub liegt? | **Mac: Knopf, lädt die neue Fassung und ersetzt sich; iPad: nur Hinweis** (Owner, 13.10.2026, per Auswahl; Blatt 18). Selbst-Ersetzen am iPad erlaubt Apple nur über App Store/TestFlight (bezahltes Konto) — verworfen; ebenso «nur Hinweis» und «nicht jetzt» am Mac. |
| 84a | Wann fragt die App? | **Beim Start und einmal täglich** (Owner, per Auswahl). Verworfen: nur auf Knopfdruck. |
| 84b | Wann erscheint eine Fassung zum Herunterladen? | **Nur bei neuer Nummer** (Owner, per Auswahl). Verworfen: bei jedem Stand auf main. |
| 83d | Bau zu 83/83b (Hilfsagent, 13.10.2026): Wie wird die Kopplung im Heim-WLAN gegen jemanden dazwischen geschützt? | **Vertrauen beim ersten Mal** (Zertifikat angeheftet) plus ein freiwillig vergleichbares **«Zeichen des Heim-PC»** (16 Hex-Stellen) im Fenster und am Mac; die 6-stellige Zahl wird **nicht** mit dem Fingerabdruck verrechnet (wäre in unter einer Sekunde durchprobierbar; ein richtiges Verfahren mit kurzem Geheimnis hiesse Kryptografie erfinden). Drossel: eine neue Zahl je 30 s, 3 Versuche, 5 min gültig; jede neue Zahl erscheint als Mitteilung am Heim-PC. |
| 83e | Nach `auf-279`: Kopplung im Heim-WLAN (`--heimnetz`) dauerhaft einschalten? | **Nein, nur Tailscale** (Owner, 14.10.2026, per Auswahl). Der WLAN-Weg bleibt gebaut und geprüft, aber ausgeschaltet; einschaltbar mit `--heimnetz`. Präzisiert 83b. |
| 85 | Owner-Frage 14.10.2026: «Die Macversion ist vollständig KosmoVis-Werkzeug, nichts auf Website — warum auf Website?» (Die Mac-App zeigte nach «Schon anfangen» die Visbox-Seite des Heim-PC; der Knotenbaum lag hinter deren Knopf.) | **Knoten als Startfläche** (Owner, per Auswahl; Blatt 19): Die Mac-App öffnet direkt die Knotenansicht, die Visbox-Seite bleibt einen Klick entfernt. Beides kommt weiter vom Heim-PC; nichts am Mac nachgebaut. Verworfen: so lassen und nur prüfen; den Knotenbaum am Mac eigenständig nachbauen (Wochen, eine zweite Fassung neben KosmoOrbit, die veraltet). |
| 85a | Wie schaltet man um? | **Schalter «Knoten \| Visbox-Seite» oben in der Kopfleiste** (Owner, per Auswahl). Verworfen: nur ein Knopf «Visbox-Seite». |
| 85b | Welche Mappe zeigen die Knoten? | **Die zuletzt auf der Visbox-Seite geöffnete, sonst die vom Start** (Owner, per Auswahl). Der Heim-PC merkt sie sich (`Flaeche.zuletzt_geoeffnet`); gilt auch für den Browser. Verworfen: immer die vom Start. |
| 85c | Was beim nächsten Öffnen? | **Immer zuerst die Knoten** (Owner, per Auswahl). Verworfen: die zuletzt offene Ansicht. |
| 86 | Der Heim-PC rechnet den Massstab eines Scans bald selbst (Bewegungssensor der Kamera, Gegenprobe aus Einzelbildtiefe) und setzt eine Ampel. Welche Grenzen, und was bei Gelb? (14.10.2026) | **Grenzen wie vorgeschlagen:** grün bei Unsicherheit ≤ 5 % und Gegenprobe ≤ 15 %, gelb bis 10 % bzw. 30 %, sonst rot; ein Handmass gewinnt immer (Owner, per Auswahl). **Bei Gelb übernehmen und um ein Kontrollmass bitten** (Owner, per Auswahl). Verworfen: strenger (3 %/10 %), lockerer (8 %/20 %); bei Gelb nur Hinweis; bei Gelb nicht übernehmen. Gebaut wird die Stufe bei KosmoPrepare, die Bitte um das Mass beim UI-Worker; Visbox sagt die Ampel im Urteil. Zentrale `…-massstab-ampel`. |
| 87 | Owner 14.10.2026, nach dem Gerätebefund (Mac-App 0.2.0 ohne Knopf): «Es sollte ein Signal direkt an die Software geben zum One-Click-Aktualisieren — wie bei jeder App, mit automatischem Neustart; dito für KosmoOrbit.» Wie schnell soll die App von einer neuen Fassung erfahren? | **Ein Klick, Neustart von selbst** (Owner-Vorgabe): Der Knopf «● 0.x.y verfügbar» lädt sofort, prüft, ersetzt und startet neu; «Laden und ersetzen» und «Neu starten» bleiben nur als Notweg. **Gefragt wird beim Start und jede Stunde** (Owner, per Auswahl; ersetzt 84a «täglich»). Verworfen: Heim-PC gibt Bescheid (nur bei Verbindung, mehr Bau); wie heute täglich. 0.2.0 muss einmal von Hand ersetzt werden. KosmoOrbit: über die Zentrale an den Integrator. Blatt 18 nachgeführt. |
| 88 | Owner 14.10.2026: «Erstelle für diese Version ein Visbox-Icon.» Welches der drei auf Blatt 20? | **A · Box mit Bild** (Owner, per Auswahl): ein Gebäude als Box, eine Seite ist schon Bild (blau) — Modell hinein, Bild heraus. Verworfen: B «Stift zu Bild», C «V im Rahmen». Ohne Schrift gezeichnet; Vorlage `ipad/Marke/`, erzeugt von `tools/make_icon.py`. Kommt mit 0.2.4 (0.2.3 war schon freigegeben). |
| 89 | Gerätebefund 14.10.2026: Aktualisieren 0.2.4 → 0.2.5 angeboten, aber «macOS hat die App an einen schreibgeschützten Ort verschoben» (App Translocation). Soll Visbox das selbst lösen? | **Ja, ein Klick** (Owner, per Auswahl; Blatt 18 Feld 4): Beim Start vom versteckten Ort bietet die App «In Programme verschieben» an, kopiert sich nach «Programme» (ältere dort in den Papierkorb), entfernt das Quarantäne-Merkmal und startet dort neu; dasselbe im Aktualisieren-Blatt. Verworfen: nur der Hinweis. |
| 90 | Owner 14.10.2026: «Kann ich im Node-Tree im Modell-Knoten einen Ordner öffnen und ein IFC oder sogar ein ArchiCAD laden?» Heute legt die Visbox-Seite aus einer Datei eine Mappe an; der Knoten zeigt sie. | **«Datei laden …» im Modell-Knoten** (Owner, per Auswahl; Blatt 21): Datei wählen → Heim-PC legt die Mappe an (IFC und andere Formate werden umgewandelt) → der Knoten zeigt das Modell. Gleicher Knoten-Code in Visbox und KosmoVis; in KosmoOrbit ohne Ladeknopf oder mit dem dortigen Import (Integrator). Verworfen: so lassen. |
| 90a | Wohin kommt die neue Mappe? | **Neben die Start-Mappe, Name aus der Datei** (Owner, per Auswahl). Verworfen: fester Ordner «Visbox-Mappen». |
| 90b | Dieselbe Datei noch einmal laden? | **Neue Fassung in derselben Mappe, Bilder und Skizzen bleiben** (Owner, per Auswahl). Verworfen: jedes Mal eine neue Mappe. |
| 90c | ArchiCAD-Dateien (.pln)? | **Als IFC aus ArchiCAD** (Owner, per Auswahl): Ablage → Sichern unter → IFC; der Knoten sagt das bei einer .pln. Geschlossenes Format, kein freier Leser. Verworfen (vorerst): eine Brücke zum installierten ArchiCAD. |
| 91 | Ohne Render-Graph gibt es keinen Modell-Knoten und damit kein «Datei laden …» — man muss erst «Graph erstellen». Soll eine leere Mappe einen fertigen Anfang zeigen? (14.10.2026) | **Ja, Modell + Prompt + Render (+ Bildvergleich) verbunden vorlegen** (Owner, per Auswahl; Blatt 22). Nichts rechnet vor «Ausführen» und «Freigeben»; ein bestehender Graph bleibt. Verworfen: nur Modell-Knoten; so lassen. |
| 91a | Auto-Kamera im Anfang? | **Ja, mit Auto-Kamera** (Owner, per Auswahl) — gegen die Empfehlung; in Visbox ist sie noch Stellvertreter (leer → Heim-PC rechnet die drei festen Richtungen). |
| 91b | Auch in KosmoOrbit? | **Ja, in beiden** (Owner, per Auswahl). |
| 92 | Owner 14.10.2026: «Grundlage so ausbauen, dass automatisch alle Nodes gesetzt, verbunden und direkt mit Kamera aufs Objekt ausgerichtet sind — direkt bereit zum One-Click-Render von Varianten.» Was sind Varianten? | **Stimmungen, Standpunkte und Entwürfe** (Owner, per Auswahl, alle drei; Blatt 23). Die Auto-Kamera richtet ihre Blicke aus der Hülle des Gebäudes aus. **Alle Kombinationen mit Zähler, einmal freigeben** (Owner, per Auswahl). Verworfen: je Achse getrennt. Ergebnis im Bildvergleich als Raster (Zeilen Standpunkte, Spalten Stimmungen, Reiter Entwurf). |
| 92a | Vorgabe beim Öffnen? | **3 Standpunkte, 1 Stimmung (Abend), 1 Entwurf = 3 Bilder** (Owner, per Auswahl). Verworfen: alles an. |
| 92b | Grenze je Klick? | **Warnung ab 12 Bildern mit ungefährer Dauer, kein hartes Limit** (Owner, per Auswahl). Verworfen: höchstens 12. |
| 90d | Am Heim-PC lief der Dienst ohne Start-Mappe, «Datei laden» antwortete «ohne Start-Mappe» (auf-282). | **Fester Ordner als Rückfall** (Owner, per Auswahl): ohne Start-Mappe kommen neue Mappen nach `~/Visbox-Mappen` (`AIIMAGING_MAPPEN_ORDNER` überschreibt); mit Start-Mappe weiter daneben (90a). Verworfen: Dienst bekommt eine feste Start-Mappe. |
| 93 | Am Heim-PC kann man aus der Knotenansicht nichts bestellen — der Dienst hat keine Auftragsablage (auf-284 D3, 503 «Keine Auftragsablage»). | **Ja, umstellen** (Owner, 14.10.2026, per Auswahl): Der Dienst bekommt `--auftragsablage` auf die Ablage, die der Abholer liest; Auftrag `auf-20261014-285` mit Probe von Anfang bis Ende. Verworfen: so lassen. |
| 94 | Owner 14.10.2026: «Bei beiden Softwares ist die Node-Tree-Oberfläche die offizielle Rendering-Arbeitsfläche für den Architekten.» Was geschieht mit dem Schalter «Knoten / Seite» der Mac-App? | **Seite nur noch als Nebenweg** (Owner, per Auswahl): kein Schalter in der Leiste; die Seite öffnet das Menü «Darstellung», zurück führt «Zurück zu den Knoten». Verworfen: Seite ganz entfernen (Skizzen-Liste und Läufe fehlten dann); so lassen. Ersetzt 85 A. |
| 94b | Fertiger Anfang in KosmoOrbit von selbst wie in Visbox? | **Knopf in KosmoOrbit lassen** (Owner, per Auswahl): ein Klick, keine doppelten Graphen im gemeinsamen Projekt. |
| 95 | Blatt 25: Was die Seite noch allein kann (Skizze, Standpunkt, Bilder der Mappe) kommt als Knoten. Womit anfangen? | **Skizze vom iPad zuerst** (Owner, 14.10.2026, per Auswahl). Verworfen: Bilder der Mappe zuerst; Standpunkt zuerst. |
| 95a | Welche Skizze nimmt der Knoten? | **Von selbst die neueste**, eine ältere am Knoten wählbar (Owner, per Auswahl). Verworfen: immer selbst wählen. |
| 96 | Der Knoten «Skizze vom iPad» geht heute nur in den Bildvergleich; der Render-Knoten nimmt kein Bild an, die Seite konnte «aus Skizze rechnen». Soll die Skizze in der Knotenansicht das Bild führen? | **Ja, die Skizze führt das Bild** (Owner, 15.10.2026, per Auswahl): Render-Knoten mit Eingang «Skizze», ein Feld dafür in der Bestellung, gerechnet wie auf der Seite mit dem Bearbeitungs-Modell (Lizenz offen, E128 — vor einer Veröffentlichung lösen). Verworfen: nur zum Vergleichen. |
| 97 | Auf die Frage, ob die Umgebungs-Textur bleibt, obwohl das KI-Bild sie kaum übernimmt (auf-287 B). | **Owner-Klarstellung (15.10.2026):** «AI Imaging brauchen wir nur für Entwürfe und Varianten und evtl. als Add-on fürs Rendering — nicht für Grundlagen-Darstellungen wie Gaussian Splats oder Punktwolken.» Grundlagen werden direkt dargestellt, nicht durch das Bildmodell geschickt. Als Grundsatz in `CLAUDE.md`; an alle Worker gemeldet. |
| 97a | Was heisst 97 fürs fertige Bild mit Umgebung (heute malt die KI auch den Bestand)? | **«User entscheidet»** (Owner, 15.10.2026): grundsätzlich möglichst viel modelliert, und der KI die Grundlagen so weit wie möglich liefern; die KI kann Skizzen, Varianten, Stimmung, ergänzen und schnelle Änderungen. Folge: am Render-Knoten eine Wahl «Bestand direkt / von der KI mitgemalt» (noch nicht gebaut, erst zeichnen). |
| 96a | Hängt eine Skizze am Render-Knoten: Was ist die Anweisung — die Stimmung aus dem Prompt oder die Bemerkung der Skizze? | **Die Bemerkung der Skizze gilt** (Owner, 15.10.2026, per Auswahl); die Stimmung tritt zurück. Verworfen: beides zusammen; Stimmung gilt. |
| 96b | Von welchem Standpunkt entsteht das Bild aus der Skizze? | **Vom Bild, auf das gezeichnet wurde** (Owner, per Auswahl). Verworfen: Standpunkt der Mappe (so machte es die Seite). |
| 96c | Am iPad gibt es kein Feld für die Bemerkung zur Skizze — nach 96a bliebe jede Skizze vom iPad hängen. | **Jetzt Rückfall, später Feld** (Owner, 15.10.2026, per Auswahl): Ohne Bemerkung gilt der Prompt des Render-Knotens als Anweisung; ohne beides wird nichts gesendet. Nach dem Reset ein Feld für die Bemerkung (iPad beim Ablegen oder am Knoten), erst gezeichnet. Verworfen: nur Feld am Knoten; nur Feld am iPad. |
| 98 | Blatt 26 (Nr. 85 mit 81/84, Demolauf 16.10.): Entsteht das Bild am Render-Knoten in einem oder in zwei Schritten? | **Immer zwei Schritte** (Owner, 20.10.2026, per Auswahl): erst «Grundlage rendern» (nur Blender, zur Kontrolle), «Variante erzeugen» (KI) erst aktiv, wenn die Grundlage da ist. Verworfen: zusätzlich «Alles auf einmal». |
| 98a | Zufallswert der Varianten derselben Grundlage? | **Einer für alle** (Owner, per Auswahl): einmal je Grundlage gezogen, am Knoten sichtbar, für alle Varianten gleich, «neu würfeln» auf Klick. Verworfen: je Variante eigener. |
| 98b | Ändert sich Modell, Kamera, Sonne, Auflösung oder Samples — was geschieht mit der Grundlage? | **Hinweis, Varianten gesperrt** (Owner, per Auswahl): «Grundlage veraltet», erst nach neuem «Grundlage rendern» wieder Varianten. Verworfen: still von selbst neu rendern. |
| 98c | Insel «Render senden» und Kosmo-Befehl auch zweistufig? | **Bleibt ein Klick** (Owner, 20.10.2026, per Auswahl): Die Knotenansicht ist die Arbeitsfläche (94); die Insel bleibt der schnelle Weg ohne Grundlage, Claude kann über `vis_render` eine Grundlage mitgeben. Verworfen: auch zwei Schritte. |
| 99 | Owner-Auftrag 20.10.2026 «A + B jetzt» (Blatt 27): iPad koppeln per Nähe, QR-Code als Rückfall, die Zahl als Notweg. Was gibt der Mac über die Nähe weiter? | **Adresse und die einmalige Zahl** (Owner, per Auswahl): Das iPad koppelt damit wie heute, nur ohne Abtippen; kein Kennwort auf dem neuen Weg. Bestätigung an beiden Geräten, Gerätename sichtbar, nur im lokalen Netz. Verworfen: das Kennwort selbst. iCloud-Schlüsselbund (C) nur vorgemerkt (kein Entwicklerkonto). |
| 99a | Zeitfenster der Kopplung am Mac? | **2 Minuten** (Owner, per Auswahl), dann schliesst sie sich von selbst. Verworfen: 5 Minuten. |
| 99b | Wo wird der QR-Code gescannt? | **In der Visbox-App mit ihrer Kamera** (Owner, per Auswahl). Verworfen: Kamera-App des iPad über einen Link. |
| 100 | Owner 20.10.2026: Für die Vertiefungsarbeit ist Visbox ein eigenes Projekt — KosmoOrbit und KosmoVis sind ein anderes. Welche Unterlagen erwähnen sie nicht mehr? | **Nur was Leser sehen** (Owner, per Auswahl): Architektur-Blatt, die Visbox-Karten der Tafel, `docs/PRODUKT_DIE_SCHRITTE.md` und das Material der Arbeit (`docs/arbeit/`). Arbeitsunterlagen (Protokolle, Plan, Einbau-Stand, Aufträge, Entscheide) bleiben, wie sie sind. Verworfen: alle Dokumente umschreiben. |
| 100a | Wie heisst die Knotenansicht dort? | **Einfach Teil von Visbox** (Owner, per Auswahl): «die Knotenansicht von Visbox», ohne Herkunft. Verworfen: Herkunftsfussnote. |
| 100b | Ordner `kosmovis/` umbenennen? | **Erst später** (Owner, per Auswahl): jetzt nur die Dokumente; das Umbenennen ist ein eigener, angesagter Schritt. |
| 100c | Wo liegen die Visbox-Darstellungen? | **Auf der Kosmo-Tafel, in einem eigenen, separaten Abteil** für die saubere Doku von Visbox Mac und iPad (Owner, Antwort im Freitext). |
| 101 | Lizenz: libquadmath (LGPL) steckt im numpy-Paket und läuft im Render-Prozess mit — ohne Prozessgrenze. Gilt die Hausregel (Regel 1, Auflage 1) auch dafür? | **Ausnahme für Mitgeliefertes** (Owner, 20.10.2026, per Auswahl): unverändert in einem permissiven Paket mitgeliefert und von niemandem direkt eingebunden ist erlaubt, deklariert im `NOTICE`. Verworfen: numpy aus dem Render-Prozess nehmen. Offen seit Sitzung 13. |
| 101a | Der Render-Knoten wird mit den zwei Knöpfen 80 px höher und ragt mit Verlauf wohl über den Fensterrand. | **Verlauf einklappbar** (Owner, per Auswahl): Der kleine Verlauf am Knoten lässt sich zuklappen; zuerst am Gerät messen. Verworfen: so lassen. |
| 101b | Wie kommt die iPad-App aufs iPad? | **Xcode am Mac** (Owner, Auskunft) — das fehlende Icon ist damit sehr wahrscheinlich das zwischengespeicherte Bild einer früheren Installation; das gebaute Bündel trägt es (Prüfstrecke 20.10.). |
| 102 | «Varianten mit einem Klick» (L24) für Kosmo/Claude in KosmoOrbit: Der eigene Befehl kostet 146 Token, vom Werkzeug-Budget des Vis-Werkzeugs (150) sind rund 120 übrig. | **Als Angabe an `vis_render`** (Owner, 20.10.2026, per Auswahl): kein eigener Befehl; eine kurze Angabe «Stimmungen» an `vis_render` (eine Grundlage, mehrere Stimmungen, Nr. 85). Verworfen: eigener Befehl mit Reserve des Integrators. |
| 102a | In den bereinigten Kapiteln stehen noch «drüben»/«die Gegenseite». | **Umformulieren, Befund behalten** (Owner, per Auswahl): die Stellen beschreiben nur Visbox, z. B. «der Auftragsvertrag verlangt …». |
| 102b | Die Kopplungszahl galt am Heim-PC 10 Minuten, der Mac zeigt sie 2 Minuten (99a). | **Auch am Heim-PC 2 Minuten** (Owner, per Auswahl): `kopplung.FRIST_S` = 120 s, Abschrift `Vermittlerkopplung.frist`; vor dem Einspielen der HomeStation angesagt. Verworfen: Heim-PC bei 10 Minuten. |
| 103 | Owner 20.10.2026: «visbox ist eine standalone lokale software … home pc ist eigentlich nur server wo sich visbox verknüpft um die heavy arbeiten übernehmen zu können» und «baue nächste version richtig!» (Plan `docs/PLAN_VISBOX_EIGENSTAENDIG_2026-10-20.md`, Blatt 28). Wo liegt die Mappe? | **Am Mac** (Owner, per Auswahl): Der Heim-PC bekommt je Auftrag nur Modell und Szene und gibt die Bilder zurück, wie KosmoOrbit. Verworfen: am Mac mit Sicherung am Heim-PC; bleibt am Heim-PC mit Kopie am Mac. |
| 103a | Woher hat das iPad die Mappe? | **Vom Mac** (Owner, per Auswahl): Das iPad ist das Zeichenbrett zum Mac; ohne Mac zeichnet es weiter, Skizzen warten im Parkfach. Verworfen: weiter vom Heim-PC. |
| 103b | Vorführmodus? | **Entfällt** (Owner, per Auswahl): Ohne Heim-PC bleibt die normale Oberfläche, nur Rechnen und Assistent gesperrt mit einer Zeile; die Beispielmappe ist eine normale Mappe. Ersetzt die Vorführfassung (Entscheide 35–42, Blatt 13b). Verworfen: zusätzlich Knopf «Vorführen». |
| 103c | Kommt die Visbox-Seite (`seite.html`) mit in die App? | **Nein, sie wird Knoten** (Owner, per Auswahl): Was sie noch kann, kommt als Knoten (Blatt 25, Entscheid 95); danach fällt sie weg. Ersetzt 94 (Seite als Nebenweg). Verworfen: mit ins Bündel. |
| 104 | Blatt 29 (Demolauf 16.10. Nr. 62/63/71/72, Video-Analyse L4-17): Wie wählt man am Render-Knoten die schnelle KI-Vorschau (Ziel ≤ 2 Min statt ≈ 9 Min je Variante)? | **Schalter «Güte: Vorschau \| Voll» am Knoten, Vorgabe Vorschau** (Owner, 20.10.2026, per Auswahl). Verworfen: eigener Knopf «Schnelle Vorschau». Befund dazu: Die ≈ 9 Min des Demolaufs rechnete **qwen-image-2.1** (Lizenz offen, 40 Schritte, ohne Tiefensteuerung), nicht die Vorgabe z-image-turbo; die Vorschau rechnet immer mit z-image-turbo (Apache-2.0), einem Zufallswert, 8 Schritten und kleinerem KI-Bild. **Für Varianten geändert durch Entscheid 143 (24.10.2026):** «Variante erzeugen» und der Varianten-Knoten rechnen ohne Wahl voll; die Vorgabe Vorschau bleibt nur als eigener Wert des Render-Knotens. |
| 104a | Wird die Vorschau geprüft? | **Ja, mit Vermerk «Vorschau»** (Owner, per Auswahl) am Bild und im Verlauf. Verworfen: ohne Prüfung. |
| 104b | Ab wann zeigt der Knoten die Restzeit? | **Erst nach der ersten fertigen Kamera** (Owner, per Auswahl), davor «Restzeit wird geschätzt …»; nie eine erfundene Zahl. Verworfen: sofort aus früheren Läufen geschätzt. |
| 105 | Owner-Fragen 20.10.2026: «hat Visbox ein MCP zu Claude? welches KI-Assistenten-Modell ist verbunden? ist das Kosmo?» — Befund: Visbox hat einen MCP-Server (`aiimaging.mcp_server`, stdio, vier Werkzeuge: Geometrie prüfen, Auftrag stellen, Auftrag abfragen, Fähigkeiten), angemeldet nur bei Kosmos Hintergrunddienst am Heim-PC, **nicht bei Claude**. Der Assistent der Visbox ist **nicht Kosmo**, sondern ein eigener: `qwen3:30b` über Ollama am Heim-PC (`aiimaging.assistent`). Der Satz «Claude über MCP steuert Visbox immer» in 0.3.1 (Einrichten › Wer rechnet?) stimmt darum heute nicht. Soll der Zugang für Claude eingerichtet werden? | **«Ja und alle Werkzeuge, voller Umfang freigeben von Funktionen für Claude und für die KI-Assistenz. Übernimm sämtliche Funktionen von KosmoOrbit, was die KI-Bedienung angeht.»** (Owner, 20.10.2026, Freitext zur Auswahl). Folge: Bestandsaufnahme der KI-Bedienung in KosmoOrbit, Plan und Blatt, dann Bau; der falsche Satz wird bis dahin berichtigt. Auflage HomeStation (Owner-Regel): Kosmo-Modelle (`kosmo-*`, `gpt-oss`) werden nie entladen. |
| 106 | KI-Bedienung (Plan `docs/PLAN_KI_BEDIENUNG_2026-10-20.md`): Wo verbindet sich Claude mit Visbox? | **In der Mac-App, nur lokal** (Owner, 20.10.2026, per Auswahl): MCP-Server in der App auf diesem Rechner, ohne Geheimnis in der Claude-Einstellung, wie KosmoOrbit. Verworfen: am Heim-PC über Tailscale mit Token. |
| 106a | Wo stehen die Vorschläge der KI zum Anwenden? | **In der Assistent-Leiste der Mac-App** (Owner, per Auswahl): eine Karte für Claude wie für den Assistenten, mit Anwenden und Ablehnen. Verworfen: unten links in der Knotenansicht. |
| 106b | Wie selbständig darf die KI arbeiten? | **Karte als Vorgabe, Coop und Vollautomatik als Schalter; die Grafikkarte gibt immer ein Mensch frei**, auch in der Vollautomatik (Owner, per Auswahl). Verworfen: Vollautomatik gibt auch Render-Aufträge frei. |
| 106c | Darf die KI Knoten und Graphen löschen? | **Ja, nur über die Karte** (Owner, per Auswahl). Verworfen: ausgeschlossen. |
| 106d | Der Visbox-Assistent nutzt `qwen3:30b` — Kosmos «Leiter»-Modell — und entlädt es beim Anwenden (gegen die Regel «Kosmo-Modelle nie entladen»). | **Eigenes Modell `qwen3:14b`** (Owner, 20.10.2026, per Auswahl; Apache-2.0, schon in `ERLAUBTE_MODELLE`): Visbox entlädt nur dieses; eine Liste schützt `kosmo-*`, `gpt-oss` und Kosmos Rollenkarte. Verworfen: `qwen3:30b` behalten und nie entladen. |
| 106e | Soll Claude Visbox auch über das Internet bedienen (claude.ai)? | **Vorerst nur lokal** (Owner, per Auswahl). Verworfen: Tunnel wie KosmoOrbit E156. |
| 106f | Daten an Anthropic (Mappennamen, Prompts, Graph, Bilder)? | **Hinweis im Einrichten, Bilder an Claude erlaubt** (Owner, per Auswahl), wie KosmoOrbit seit 07.10. Verworfen: Bilder nur einzeln. |
| 107 | Für Material-Knoten und Stimmungsbilder Texturen und Himmelsbilder (HDRI) aus freien Bibliotheken (ambientCG, Poly Haven) — CC0, steht nicht in der Lizenzliste. | **CC0 zugelassen, nur für Bilddaten** (Owner, 20.10.2026, per Auswahl): Texturen und Himmelsbilder, unverändert, mit Quelle im `NOTICE`, wie bei den Schriften; nicht für Code. Als Präzisierung in `CLAUDE.md`. Verworfen: nur selbst erzeugte Materialien. |
| 108 | Blatt 30 (KI bedient Visbox): Wo stellt man die Selbständigkeit ein, ist MCP ab Werk an, wann zeigt sich der Tätigkeitsstrom? | **A oben in der Assistent-Leiste**, gilt für Claude und Assistent; **B Claude über MCP ab Werk an, nur lokal**; **C Tätigkeitsstrom nur, solange die KI arbeitet** (Owner, 20.10.2026, per Auswahl). Verworfen: nur im Einrichten; ab Werk aus; immer als Verlauf. |
| 109 | Blatt 31 (Modell im 3D-Fenster, Kamera einstellen): Grösse, Handeinstellung, Perspektive? | **A 3D-Fenster klein fest im Modell-Knoten, Doppelklick gross**; **B Kamera im 3D ziehen, Werte zusätzlich eintippbar**; **C Vorgabe «Senkrechte gerade»** (Zwei-Punkt-Perspektive) (Owner, per Auswahl). Verworfen: ziehbare Grösse; nur Werte; frei. |
| 110 | Blatt 32 (Stimmungen mit Himmelsbild): Wirkung, Auswahl, eigene Himmel? | **A Licht in Blender (Himmelsbild als Welt) und Prompt** — jede Stimmung braucht eine eigene Grundlage; **B acht Stimmungen: Morgen, Mittag, Abend, Blaue Stunde, Bedeckt, Nebel, Winter, Weiss (Studio)**; **C Himmelsbilder JETZT** (Owner über LW, Ausnahme zur Empfehlung): schöne Gratis-HDRIs aus dem Netz, CC0 von Poly Haven (Entscheid 107), je Stimmung ein bis zwei, 2k und 4k, ausgesucht und am Heim-PC abgelegt von der HomeStation; als feste Himmel je Stimmung. Eigene Uploads später. |
| 111 | Blatt 33 (Oberfläche, Material, Farbpalette): Zuordnung, Vorschau, Palette? | **A Material nach Bauteil-Art aus dem Modell** (Fassade, Dach, Boden …); **B Vorschau als Kugel, umschaltbar auf Würfel und Fläche**; **C Farbpalette tönt das Material und geht als Satz ans Bildmodell** (Owner, per Auswahl und über LW). Umbenennung in beiden Programmen: «Material-Bausteine» → **Oberfläche**, neuer Textur-Knoten → **Material**; Vorlage mit Material → Oberfläche → Render. Texturen CC0 (ambientCG), Entscheid 107. |
| 112 | Owner über LW: «teils fragst du doppelt … einmal hier und einmal beim Vis-Worker». Wie wird künftig gefragt? | **Nur über die Zentrale** (Owner, 20.10.2026, per Auswahl im Chat): Fragen gehen als Zentrale-Nachricht an `owner`/`homestation`, die HomeStation stellt sie gebündelt als Klickfrage; im Chat nicht zusätzlich. Ersetzt die Vorgabe vom 08.10.2026 in `CLAUDE.md`. Verworfen: nur im Chat; doppelt wie bisher. |
| 113 | Sieben Fragen zum Bauplan der neuen Knoten (`docs/PLAN_KNOTEN_NEU_2026-10-20.md` §5). | **«Alles nach deiner Empfehlung los»** (Owner über LW, 20.10.2026): (1) Vorschaubilder als verkleinerte CC0-Kopien (~160 px), Quelle und Prüfsumme im `NOTICE`; (2) fehlt am Heim-PC ein Himmelsbild oder eine Textur, wird der Auftrag mit klarem Satz abgewiesen; (3) die Auto-Kamera rechnet der Heim-PC, KosmoOrbit zeigt das Ergebnis — eine Rechnung für beide; (4) Mehrfachwahl am Stimmung-Knoten = ein Bild je Stimmung (Knopf «n Bilder»), mit Varianten-Knoten gilt dessen Wahl; (5) Vorgabe «Haus füllt» 70 %; (6) «Weiss (Studio)» = Himmelsbild plus alle Oberflächen weiss wie ein Gipsmodell; (7) Türen gehören zu «Übrige», eigene Art «Türe» später. Der Vertragsvorschlag (environment, cameras_auto, materialien) liegt beim Integrator; HDRI-Name = Stamm der Dateien in der Himmelsbild-Ablage des Heim-PC. |
| 114 | KI-Bedienung: Claudes Schritte im Modus Coop/Voll landen im selben Rückgängig-Verlauf wie die des Owners. Wer nimmt sie zurück? | **Getrennt wie in KosmoOrbit** (Owner über LW, 20.10.2026, «alles nach Empfehlung»): Strg+Z nimmt nur die eigenen Schritte zurück; Claudes Schritte über die Leiste mit «Claudes letzten Schritt zurücknehmen». Verworfen: gemeinsamer Verlauf. Im Modus Karte ist jede Karte ein eigener Schritt. |
| 115 | Owner über LW, 20.10.2026 (stehend), wörtlich: «ansichten ui und ux sollte zu kosmovis identisch sein immer». Was heisst das für die Visbox-Knotenansicht, die heute ohne Kopfteile (InselKopf, NaviInsel, Ansichts-Pille, Erzählzeile) läuft und Assistent/Einrichten nativ in der Mac-App zeigt? | **Die Visbox-Ansichten übernehmen die KosmoOrbit-Vis-Oberfläche 1:1** — Gestaltung, Abstände, Pillen, Legende, Verhalten und die Kopfteile; was in KosmoOrbit über Inseln läuft (Assistent, Einrichten …), läuft auch in Visbox als Insel. Ausnahmen nur, wo eine Funktion in Visbox fachlich nicht existiert, und die werden benannt. Synchron gehalten über wortgleiche Dateien und eine Probe, die beim Bau rot wird, sobald die Kopie abweicht. Als Grundsatz in `CLAUDE.md`. |
| 116 | Acht Fragen zum Abgleich Visbox = KosmoVis (`docs/PLAN_UI_GLEICHHEIT_2026-10-20.md` §6). | **Alle nach Empfehlung** (Owner über LW, 20.10.2026, Vollmacht «alles nach Empfehlung»): (1) Stationen-Palette zeigen, Logo = Startansicht, aufgefächert «Knoten» und «Visbox-Seite»; (2) Kugel in gleicher Optik, Name «Assistent»; (3) dunkles Thema wie KosmoOrbit, umschaltbar; (4) Pillen «3D · PLAN» und «Geschoss» entfallen; (5) Heim-PC-Chip in Sync-Optik, Klick öffnet «Wer rechnet?»; (6) Heim-PC-Kennwort bleibt in der Mac-App; (7) Rundgang übernehmen, falls er Vis-Schritte hat; (8) die Visbox-Seite bleibt, wie sie ist. |
| 116a | Darf das gemeinsame, in KosmoOrbit private Paket `@kosmo/insel` in das öffentliche Visbox-Repo? | **Ja** (Owner per Klickfrage über LW, 20.10.2026): Das Visbox-Repo bleibt bewusst öffentlich (Apache-2.0) mit den KosmoOrbit-Vis-Teilen darin; die Kopie von `@kosmo/insel` darf hinein. Die Namens-Pille rechts der Kugel (UI-Worker) kommt mit dem Paket. |
| 117 | Soll das Licht der Stimmung (Sonnenrichtung, Schatten, Helligkeit aus dem Cycles-Bild) auch ins KI-Bild kommen? Heute liest die KI nur die Tiefe (`docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`). | **Variante A — erst messen, dann am Bild entscheiden** (Owner über LW, 21.10.2026, Vollmacht «alles nach Empfehlung»). Bedingungen: (a) nur Gewichte unter Apache-2.0 oder MIT, Lizenz je Datei mit Quelle (Modellkarte) im Auftrag; FLUX-Redux und SDXL-Adapter ausgeschlossen; (b) Download-Grösse und Grafikspeicher je Gewicht genannt, ein Lauf zur Zeit, 400-W-Grenze; (c) drei Stärken × drei Stimmungen (morgen, abend, bedeckt), Farbabgleich als eigener Schalter; (d) am Ende Vergleichsbilder für die Tafel, der Owner wählt am Bild. Der Grundsatz «KI-Bild nur Entwurf» (E97) bleibt; der Farbabgleich verschiebt nichts an der Form. Umgesetzt: Messschalter `vis.farbabgleich` und `vis.bildeingang` (beide Vorgabe aus, kein Vertragsfeld), Messauftrag auf-20261021-298. Verworfen: nur Farbabgleich; so lassen; beide Bilder liefern (stehen nach der Messung wieder zur Wahl). |
| 117a | Licht ins KI-Bild nach den Messungen 298 und 300: Der Bildeingang bringt das Licht, aber bis Stärke 0,9 nur als Gipsmodell, bei 0,95 verliert das Haus die Form; der Farbabgleich allein macht blass. Welcher Weg? | **W-4, nebeneinander** (Owner per Klickfrage über LW, 21.10.2026): In der Knotenansicht steht das gerenderte Grundbild (`render.passes ['schoenbild']`, `<kamera>__schoenbild.png`) mit Licht und Schatten neben dem KI-Bild — in Visbox und KosmoVis gleich (E115). `vis.bildeingang` und `vis.farbabgleich` bleiben Messschalter, Vorgabe aus, kein Szene-Feld. **Für Varianten ersetzt durch Entscheid 138 (22.10.2026): `vis.bildeingang` 0,5 ist dort Vorgabe; W-4 (Grundbild daneben) und `vis.farbabgleich` als Messschalter gelten weiter.** |
| 118 | Visbox eigenständig, Schritt 4: Soll das iPad zuhause den Mac nehmen statt des Heim-PC? | **A — immer über den Mac, auch zuhause** (Owner per Klickfrage über LW, 21.10.2026). Reihenfolge: zuerst die Verbindung iPad–Mac mit dem Zertifikat des Mac verschlüsseln, dann Mappe, Bilder und Skizzen über den Mac. Die drei Detailfragen zu Schritt 3 (Mappen über Logo-Palette und ⌘O; «An den Mac holen» kopiert und lässt den Zwilling am Heim-PC; «Datei laden» in die offene Mappe) bleiben wie nach Empfehlung gebaut. |
| 119 | Grundbild neben dem KI-Bild: Der Render-Knoten ist innen nur 184 px breit, zwei Bilder wären je unter 96 px. Breiter machen? | **B — breiter** (Owner per Klickfrage über LW, 21.10.2026): Innenbreite mindestens 196 px, beide Bilder stehen schon am Knoten nebeneinander, in Visbox und KosmoVis gleich; die grosse Ansicht mit Umschalter bleibt zusätzlich. Integrator und UI werden wegen Goldens und Layout informiert. |
| 118a | Drei Folgefragen zu «iPad über den Mac» (Blatt 40). | **Alle nach Empfehlung** (Owner per Klickfrage über LW, 21.10.2026): (1) der direkte Weg iPad → Heim-PC ist in 0.3.16 nur Übergang mit Hinweis; ab der nächsten Fassung weist der Heim-PC ein direkt sprechendes iPad mit klarem Satz ab; (2) liegt die Mappe am Mac, wird in der Knotenansicht am Mac gerechnet, das iPad sagt das (wie 94); (3) die Verbindung iPad–Mac geht auch ohne eingerichteten Heim-PC. |
| 120 | L4-18 (Video-Befund): Qwen-Image-2.1 hat eine offene Lizenz («Qwen Research License Agreement»). Bleibt es bestellbar, und was steht am Bild? | **A — bestellbar, nie Vorgabe; am Bild der Satz** (Owner über die Zentrale, 21.10.2026): Statt «Lizenz offen» steht «Qwen-Image-2.1: Lizenz offen — nicht für Wettbewerb oder Veröffentlichung»; Wettbewerbsbilder mit Z-Image Turbo. `engine_license_open: true` bleibt das Signal, nichts wird gesperrt (E154 (4)). Umgesetzt nach Blatt «Lizenz-Satz am Bild», Empfehlung A: der Satz am Render-Knoten, in der grossen Ansicht, an Kachel, Inspektor und Ablage; als Abzeichen auf einem Bild und neben «Aufs Blatt» die kurze Form «Qwen-Image-2.1: Lizenz offen», der Satz vorne in der Kurzhilfe (sonst dreizeilig, auf-250). In Visbox und KosmoVis gleich (E115). Verworfen: aus der Auswahl nehmen; nur «Lizenz offen». |
| 121 | Ein gesicherter Blick ist am Render-Knoten festgehalten; danach wird er in der Ansicht verschoben. Gilt er weiter? | **Festhalten, mit Satz** (Owner über den Hauptstrang, 21.10.2026): Bestellt wird der festgehaltene Blick; am Knoten steht «Blick wurde verschoben», damit niemand meint, der neue Standpunkt sei bestellt. Verworfen: still nachführen. |
| 122 | Öffnet sich die Grossansicht von selbst, wenn ein Bild «fertig» ist? | **Nur auf Wunsch — Schalter, ab Werk aus; im Präsentationsmodus immer** (Owner über den Hauptstrang, 21.10.2026). Grund: Ein Fenster, das sich ungefragt öffnet, unterbricht die Arbeit; in der Präsentation ist das grosse Bild der Zweck. |
| 123 | Das erste Bild eines Laufs gross öffnen (auch ohne Verlauf und ohne Grundbild)? | **A — ja** (Owner über den Hauptstrang, 21.10.2026). Gebaut von einem anderen Strang. |
| 124 | Wer führt den Hilfszweig `claude/kosmovis-visbox-stand` nach, wenn mehrere Stränge zugleich arbeiten? | **Die Hilfsstränge selbst, per normalem Merge, nie überschreiben** (Owner, 21.10.2026). Kein Vorspulen auf fremde Stände, kein force; ein Zusammenstoss wird neu geholt und gemergt. |
| 125 | Auf welchem Stand läuft die Demo am 29.10.2026? | **KosmoOrbit v0.1.10; was bis Montag 26.10. eingespielt und stabil ist, kommt hinein** (Owner, 21.10.2026). Priorisiert: «Bild aufs Blatt» und die Grossansicht. Was danach kommt, wartet auf die nächste Fassung. |
| 126 | Womit rechnet eine Variante, wenn die Bestellung keine Messschalter trägt? (Messungen 309, 312, 314: M2 hält die Form, das Himmelsbild nimmt den flachen «Modellfoto»-Hintergrund) | **M2 mit Himmel als Vorgabe für Varianten** (Owner per Klickfrage A, 21.10.2026): Stoff vorne (`vis.material_vorne`), Umriss im Lauf gehalten (`vis.umriss_halten: im_lauf`) und Himmel sichtbar (`vis.himmel_sichtbar`). Fehlt ein Schalter (oder steht `null`), gilt am Heim-PC die Vorgabe; ein ausdrücklich gesetzter gewinnt, auch «aus» (`false`). Der Satz «KI-BILD OHNE GRUNDLAGENBILD» bleibt am Bild. Die Vorgabe entfällt still mit Grund, wo sie fachlich nicht passt: «Nur Grundlage» (kein KI-Schalter, der Himmel aber schon — er gehört zur Grundlage), Vorschau und ungemessenes Bildmodell (kein Umriss im Lauf), Skizze, keine Stimmung oder Gipsmodell (kein Himmel), kein Stoff erkennbar (nichts vorne). Eine Variante auf einer Grundlage ohne Himmel behält deren Himmel, mit Satz; war der Himmel ausdrücklich anders bestellt, wird sie laut abgewiesen. `angewandt.messschalter` nennt je Schalter Wert und Herkunft. Die App schickt die Schalter nicht mit (nicht im Vertrag) — die Vorgabe gilt darum für jede Bestellung, ohne Änderung drüben. |
| 127 | Generalprobe 327 (Hauptbefund 1): Bildmodell 27,9 GB und Kosmos Sprachmodell `kosmo-qwen3.6:35b-a3b` (22 GB) passen nicht zugleich auf die 32-GB-Karte des Heim-PCs; danach kam der Visbox-Assistent `qwen3:14b` nur zu 2,5 von 16,4 GB auf die Karte (F2: 163 s). Wer hat in der Demo Vorrang? | **A — Visbox hat Vorrang** (Owner über die Zentrale, 22.10.2026): Vor jedem Bildauftrag gibt Visbox **alle** von Ollama geladenen Modelle frei — auch fremde (Kosmo, `gpt-oss`) — per `keep_alive: 0`; das fremde Programm lädt sein Modell danach bei Bedarf selbst neu. Kein anderer Eingriff (nichts laden, löschen, umstellen). Fehlt Ollama oder hängt es, rechnet das Bild trotzdem, mit Vermerk. Ersetzt für den Bildweg die Auflage aus 105/106d («Kosmo-Modelle nie entladen»); für den Assistenten (Entladen beim «Anwenden», `entlade_wenn_nur_eigenes`) gilt 106d weiter. Gebaut: `assistent.gib_karte_frei`, Abholer und Dienst, Befund `angewandt.freigegeben` (C139, Protokoll 74 §228). |
| 128 | Mac-App: bei jedem Update fragte macOS zweimal das Passwort (Behelfs-Unterschrift wechselt je Bau; Schlüsselbund-Einträge Heimschlüsselbund und Vermittlerschlüssel). Wie unterschreiben? | **A: ein festes, selbst erstelltes Zertifikat («Visbox Eigenzertifikat», 10 Jahre), als GitHub-Secret `MAC_ZERT_P12`/`MAC_ZERT_PASSWORT` hinterlegt; die Mac-Prüfstrecke unterschreibt damit, ohne Secret weiter mit dem Behelf** (Owner, 22.10.2026, über die Zentrale). Danach einmal Passwort und «Immer erlauben», dann still über Updates. Keine Apple Developer ID vor der Demo; Gatekeeper warnt beim ersten Öffnen weiter. Der private Schlüssel liegt nie im Repo. |
| 129 | Mac-Befund 0.3.33 (Protokoll 74 §231): Ohne Mappe am Mac öffnete die Knotenansicht nach «Schon anfangen» die Mappe, die am Heim-PC irgendein Gerät zuletzt geöffnet hatte (Entscheid 85 B) — ein Probelauf am Heim-PC verstellte, was der Owner sah. Soll die Knotenansicht am Mac ihrer eigenen Mappe treu bleiben? | **A: Der Mac merkt sich seine zuletzt offene Mappe selbst** und öffnet nach «Schon anfangen» immer diese; andere Geräte verstellen sie nicht mehr (Owner über die Zentrale, 22.10.2026). Heim-PC-Browser und iPad behalten 85 B. Gebaut: Die App merkt sich den Ordnernamen aus der Antwort von `GET /knoten/graph` und lädt die Knoten mit `?mappe=` (`Knotenmappenwahl`); von der Visbox-Seite zurück gilt die dort geöffnete; mit Mappe am Mac unverändert; eine verschwundene Mappe (404) wird vergessen. Dazu, weil zwei Geräte in derselben Mappe arbeiteten: Sichern auf veraltetem Stand weist der Heim-PC ab («anderes Gerät … neu laden»), statt still zu überschreiben. |
| 130 | Owner-UI-Auftrag Knotenansicht 22.10.2026 «Der Knoten ist eine Zeichnung im Massstab» (Regeln R1–R9, Blatt 50 bis 50e, Protokoll 74 §234). Welcher Wortschatz, welche Kategoriefarben, welche Schrift, und welche Varianten der acht Wahlpunkte A–H? | **Alles nach Empfehlung** (Owner über die Zentrale, 22.10.2026): **Wortschatz ja** — Grundbild statt Grundlage, Knopf «Bild erzeugen» statt «Variante erzeugen», «Bildmodell» statt Bildwerkzeug/Backbone, «Qualität» mit «20 Schritte» im Hinweis statt Samples, Anrede «du»; gleich in Knoten, Karte, MCP-Beschreibungen und Lexikon. **Kategoriefarben ja** — Quelle grün, Stimmung & Stil ocker, Material violett, Rechnen blau, Ergebnis grau. **Wahlpunkte A1–H1:** Wort-Kacheln bei Stimmung; Grundbild und KI-Bild gleich gross nebeneinander; Zustandszeile über der Hauptaktion; Bildknoten zeigen in Stufe 2 ihr Bild; Umriss bleibt in Stufe 3 gleich gross; Kamera-Richtungen als Kacheln 4 × 2; Varianten-Knoten immer 480 breit; Kurzname bis 14 Zeichen im Kopf («Kamera aus 3D», «Aufs Blatt»). **Detailstufen:** beim Herauszoomen wenige, grössere Wörter in Welt-Einheiten (Stufe 2 Kopfwort 20 und Kernzeile 16, Stufe 3 Kopfwort 32), Umriss gleich. **Schrift IBM Plex Sans** (Jua hat keine Umlaute) — zuerst in den Knoten, nach der Demo in der ganzen App; Rollen 11/10/8,5, Plex Mono nur für Zahlen. Vor der Demo nur R1.2 (transform:scale bei Zoom < 1) und R6.4 bei UI; der Rest nach der Demo in beiden Softwares — Bausteine (R4, R5, R6.4, R7, R9) baut UI in `@kosmo/ui`, die Knoten (R1–R3, R6 mit Probe R6.6, R8, Soll je Knoten) bauen wir. |
| 131 | Mac-Test Visbox 0.3.33, Karte K-10 (Blatt 49): Vorschläge von Claude stehen in der Knotenansicht doppelt — oben das Band «Claude wartet auf dich … Ablehnen / Anwenden» (Text abgeschnitten), unten links die Karte «Vorschlag von Claude» mit Schrittliste; und die Karte nennt Feldnamen («Node-Parameter (preset, presets)») statt Werten. | **Entschieden wird nur noch unten links an der Claude-Marke; das Band oben verliert seine Knöpfe. Die Karte zeigt Werte statt Feldnamen** («Stimmung: Morgenlicht → Abendstimmung») (Owner über die Zentrale, 22.10.2026). Vor der Demo nur diese zwei Punkte (kleines Risiko); Puls an der Pille «N offen» und der Schalter Selbständigkeit an der Marke kommen nach der Demo und werden gezeichnet. Umsetzung: Die Kartenzeile kommt aus dem Vis-Werkzeug (beide Programme gleich); das Band ist allgemeine Oberfläche des Partnerprogramms — dort nimmt der UI-Worker die Knöpfe heraus und lässt einen Klick die Karten aufklappen; Visbox blendet die Knöpfe bis dahin im eigenen Wirt aus (Protokoll 74 §238). |
| 132 | Blatt 47 «Mac-Fenster: Glas-Kopf», Fragen A–C. | **A** (Owner über die Zentrale, 22.10.2026): Glas-Kopf mit Verlauf und Unschärfe statt des grauen Balkens, die Ampel-Knöpfe bleiben; «Einrichten» und «iPad» in die Einstellungs-Insel und zusätzlich in die Menüleiste von macOS; «Aktualisieren» als grüner Punkt an der Fassung im Kopf. Bau mit Visbox 0.4.0 nach der Demo (29.10.2026). **Nachtrag 22.10.2026 (Owner über die Zentrale):** nur das Logo oben links (Visbox-Box statt Kosmo-Spirale) als Kleinauftrag vor der Demo vorgezogen (Visbox 0.3.36, Protokoll 74 §244); der Glas-Kopf bleibt 0.4.0. |
| 133 | Blatt 48 «Der Assistent von Visbox»: Name, Symbol, Ton? | **A «Lot»** (Owner über die Zentrale, 22.10.2026): Senklot in einer Glaskachel, knapp und sachlich, eigener Name statt «Assistent»; bewusste Ausnahme des Owners von Entscheid 115 (Marke und Assistent). Bau 0.4.0 nach der Demo; das Symbol braucht eine Nahtstelle im Partnerprogramm (eigener Zweig). Verworfen: Mina, Zirkel. **Nachtrag 22.10.2026 (Owner über die Zentrale):** nur das Symbol als Kleinauftrag vor der Demo vorgezogen (Visbox 0.3.36, Protokoll 74 §244) — ohne Nahtstelle, allein im Visbox-Wirt (`visbox.css`); Name und Ton bleiben «Assistent» bis 0.4.0, die Nahtstelle kommt dann. |
| 134 | Blatt 49: Was darf die Selbständigkeit «Voll» ohne Klick? | **A** (Owner über die Zentrale, 22.10.2026): Vorschau-Läufe ohne Klick, höchstens 5 je Stunde; nie Modelle mit offener Lizenz, nie Voll- oder Endgüte; Löschen bleibt eine Karte. Ergänzt 106b/106c. Bau 0.4.0 nach der Demo, mit Puls an «N offen» und dem Schalter «Karte · Coop · Voll» an der Marke; den Schalter im Partnerprogramm baut der UI-Worker (v0.1.11). Verworfen: B alles ohne Klick; C wie heute. |
| 135 | Owner-Verbesserungsliste 22.10.2026 (Blätter 51–56): acht Wahlen | **Alle a** (Owner, 22.10.2026, über die Zentrale): (1) iPad ganz in schwebenden Inseln, Werkzeugrad oben links (wie «Concepts»), 3D-Skizzieren zuerst als Bild, später im Raum; (2) Zeichnungsart: die KI schlägt vor, der Architekt bestätigt (braucht ein Bild-Sprachmodell mit freier Lizenz — vor dem Bau prüfen und messen); (3) je Skizze wählbar «ins 3D» oder «nur ins Bild», vorbelegt aus der Art («Skizze wird 3D» ist Forschung, Ziel 0.5.0); (4) Änderungsfarben nach Planfarben: Bestand grau, neu rot, Abbruch gelb, dazu «geändert» als vierte Farbe mit Kante (Form unterscheidet sie vom Abbruch; Feinabstimmung mit UI); (5) Tafel je Projekt als eigene Ansicht, oben «Knoten | Tafel», Spalten nach Art; (6) Materialpass beim Laden als eine Karte — Farben der Datei bleiben, fehlende schlägt Visbox vor, dazu acht neue Materialien; (7) Knotenansicht in drei Zonen (Modell links, Maschine Mitte getönt mit Akzentkanten, KI-Bild rechts oben/unten), Kombinierer mit beliebig vielen Eingängen; (8) erster Start leer bis auf «Datei laden», danach eine Karte mit vier Blicken über Eck und Start-Vorschlag der KI — **ersetzt Entscheid 91** und ändert 92a (vier statt drei Richtungen, am Heim-PC zu messen). Bau nach der Demo (Visbox 0.4.x; KosmoOrbit ab v0.1.11), Bausteine bei UI, Inhalte bei uns (Protokoll 74 §243). |
| 136 | Wie sieht der Zustand «geändert» aus (Änderungsfarben, Entscheid 135 Punkt 4)? | **Violett mit doppelter Kante, in 2D und 3D gleich** (Owner, 22.10.2026, über die Zentrale). Bestand grau, neu rot, Abbruch gelb (im 3D mit weiter Schraffur im Stiftton und gestrichelter Kante). Farbwerte aus `stilblatt.ts` (UI). Ersetzt die Vorschläge «graue Fläche mit roter Kante» (KosmoVis) und «hellblau mit kräftiger Kante» (UI). |
| 137 | Knotenansicht in drei Zonen (Blatt 55a): Wo liegen die fertigen Bilder (Varianten, Vergleich, Aufs Blatt)? | **Rechts unten, neben den KI-Knoten; das Bild kommt von links aus der Maschine** (Owner, 22.10.2026, über die Zentrale). Anschluss-Seite richtet sich nach der Zone des Knotens (Owner-Nachtrag zu A3). Bau nach der Demo. |
| 138 | Messung 337: Ohne Bildeingang malt die KI-Variante im Haus aus Rauschen und verliert die Fenster (Kanten im Haus 0,207); mit Bildeingang 0,5 hält der Giebel (0,334, ein erfundenes Fenster an der Traufe, geom_iou 0,991, KI 13,5 s), mit 0,65 weniger (0,273, vier erfunden). Wovon geht die KI-Variante aus? | **A — vom Grundbild, mit Stärke 0,5 als Vorgabe** (Owner über die Zentrale, 22.10.2026 abends). Auflagen: (1) Bildeingang 0,5 ist Vorgabe für Varianten — fehlt `vis.bildeingang` (oder steht `null`), gilt 0,5; eine eigene Stärke gewinnt, `false` schaltet ab; (2) **nie** an einem Modell mit offener Lizenz oder Forschungslizenz (`Backbone.lizenz_offen` / `nur_forschung`) — dort rechnet die Variante ohne, mit Satz im Ergebnis; ebenso entfällt die Vorgabe an Modellen ohne vorbereiteten Weg, in der Vorschau (Entscheid 104, ungemessen), bei «Nur Grundlage» und Skizze, und wenn die Grafikkarte nicht reicht (dann ohne statt abgewiesen); (3) das Grundbild bleibt neben dem KI-Bild stehen (W-4 aus 117a gilt weiter). **Ersetzt für Varianten Entscheid 117a** («Bildeingang nur Messschalter»). Bestätigt von Messung 339 (Sichtbeton mit 0,5: Kanten im Haus 0,438, Fenster gehalten; ohne: anderes Haus). Verworfen: B so lassen; C Kanten-Führung und D anderes Modell — nach der Demo. Gebaut: `kosmo_szene.VARIANTEN_VORGABE["bildeingang"]`, `bildeingang_vorgabe_entfaellt` (Protokoll 74 §256, Einbau C176). |
| 139 | Zonen-Knotenansicht (Blatt 55a, UI-Baustein KZonenFlaeche): Wohin kommen Knotenarten, die keiner Zone zugeordnet sind? | **In die Maschine** (Owner über die Zentrale, 23.10.2026, wie vom UI-Worker empfohlen). Einbau nach der Demo durch uns (UI-Zweig `claude/kosmo-ui-zonen-tafel` c9e49ffb8). |
| 140 | Planfarben (I6, UI-Baustein KPlanMarke): Wie sieht die Bestand-Marke aus? | **Blasser Tintenrand** (Owner über die Zentrale, 23.10.2026, wie vom UI-Worker empfohlen). Einbau nach der Demo durch uns. |
| 141 | iPad: Soll man auch mit dem Finger zeichnen können (heute nur Pencil)? | **A** (Owner über die Zentrale, 23.10.2026): Schalter «Mit dem Finger zeichnen» in den Einstellungen, Vorgabe **aus**; mit Pencil bleibt der Finger zum Verschieben und Zoomen. Bau nach der Demo, Blatt vorher auf der Entwurfsfläche. Im Simulator zeichnet jede Berührung schon jetzt (0.3.51, für Proben). Verworfen: B Finger zeichnet immer; C nur Pencil. |
| 142 | In welcher Sprache stehen Dinge, die Visbox betreffen, und Dinge, die KosmoOrbit betreffen (Anlass: die Erklärkarten der Knoten vom 23.10. waren deutsch)? | **«KosmoOrbit-Dinge deutsch, Visbox-Dinge englisch»** (Owner über die Zentrale, 23.10.2026, wörtlich). Bestätigt die Owner-Regel vom 15.10.2026 (Protokoll 74 §137: Titel, Gruppe und Notiz der Visbox-Blätter auf der Kosmo-Tafel englisch, weil die Vertiefungsarbeit englisch ist; Gruppen beginnen mit «Visbox · …»), die bis dahin nur im Protokoll stand. Umgesetzt: die Erklärkarten der Knoten englisch (`20261024-knoten-*`, Gruppe «Visbox · What the nodes do»), Quelle `docs/KNOTEN_ERKLAERT.en.md`, `tools/knoten_tafel.py --sprache en` als Vorgabe; die Oberfläche von Visbox zeigt deutsche Beschriftungen, darum auf den Karten das englische Wort mit der Bildschirm-Beschriftung in Klammern. Die deutschen Karten `20261023-knoten-*` werden nicht aufgehängt (Protokoll 74 §271). |
| 143 | Messung 346: «Variante erzeugen» bestellte ohne einen Klick die Vorschau (Vorgabe 104) — 8 Schritte, ohne das Grundbild als Bildeingang; sie übermalte am Testhaus ein Fensterband, die Bäume wurden braun-rosa, das Bild unscharf. Voll mit Bildeingang 0,5 hielt alles (Fenster 0,98). Womit rechnen Varianten, wenn niemand wählt? | **A — Varianten rechnen standardmässig «Voll»** (vom Grundbild, Bildeingang 0,5 nach Entscheid 138) (Owner über die Zentrale, 24.10.2026). Die Vorschau bleibt wählbar und trägt den Hinweis «Fenster und Form nicht gesichert»; der Render-Knoten behält seine eigene Vorgabe (Entscheid 104). **Ändert 104 für Varianten.** Rechenzeit voll rund 33–45 s je Bild statt rund 26–36 s (346). Gebaut: Vorgabe je Bestellart (`guete.ts` `GUETE_VORGABE_JE_ART`, `gueteAmKnoten(params, art)`); «Variante erzeugen» und der Varianten-Knoten bestellen ohne Wahl `vis.guete: 'voll'`, eine gewählte Vorschau bleibt Vorschau; der Schalter am Render-Knoten wählt die Güte von «Variante erzeugen» und steht darum ohne Wahl auf Voll. Am Heim-PC keine Änderung (voll mit Grundlage → Bildeingang 0,5). Protokoll 74 §275, Einbau C193. |
| 144 | Mac: Wie bewahrt der Mac seinen Ausweis für die iPad-Verbindung auf (nach jedem Update war er unlesbar)? | **A** (Owner über die Zentrale, 24.10.2026): im Schlüsselbund lassen; nach der Demo die feste Unterschrift einrichten (Entscheid 128, nach dem Malware-Scan) und prüfen, ob iPads ein Update überstehen. Bis dahin: klare Meldung, höchstens ein neuer Ausweis je Update, «Erlauben» bei der Passwortfrage hält die Kopplung (C196); alte Einträge löscht der Owner nach docs/MAC_UNTERSCHRIFT_EINRICHTEN.md. Demo-Regie: nach dem Koppeln den Mac nicht mehr aktualisieren. Verworfen: B Ausweis als Datei (für jedes Programm des Nutzers lesbar); C dasselbe vor der Demo. |
| 145 | iPad-Wünsche I8 (Skizze auf Visbox-Grundlage) und I9 (Vorlagen je Skizzenart): wie und wann? | **Alle wie empfohlen** (Owner über die Zentrale, 24.10.2026, gebündelt mit UI): (1) nach der Demo, erst Blätter, dann Bau, I8 vor I9; (2) I8 bei Perspektive/Axonometrie: helle Linienzeichnung des Modells aus der Kamera, umschaltbar auf das gerechnete Grundbild; (3) I9 Grundriss/Schnitt/Ansicht: masshaltige Plan-Grundlage aus dem Modell im gewählten Massstab, bei «Freihand» nur Raster; (4) Art beim Anlegen über die Vorlagenwahl, später im Werkzeugrad änderbar, Kosmo darf vorschlagen, der Architekt bestätigt; (5) Grundlage als gesperrte untere Ebene, ab Werk 60 % Deckkraft, ausblendbar, nie hineinzeichnen; (6) die Skizze bleibt an ihrer Kamera, der Standpunkt reist mit, Hinweis bei abweichender Kamera; (7) Auflösung 2× Bildschirmgrösse des iPad, Rechenzeit sichtbar, abbrechbar. Aufteilung: Bildweg und Vertrag bei uns (Felder skizze.art, modus, grundlage, striche, hilfe — v1 an UI bestätigt), Bedienung und Sprache bei UI. |
