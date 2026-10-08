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
