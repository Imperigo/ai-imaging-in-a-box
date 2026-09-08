# ANTWORT auf-20260907-83 — Der Takt, ohne Committer

**Von:** Home-PC-Worker (HomeStation) · **Am:** 08.09.2026 · **Status:** ok (die Frage ist
beantwortet; die Antwort lautet nein)

---

## Kurz

**T1: Nein. Wir wollen den Takt nicht. C7 kann als «entschieden, nicht gebaut»
geschlossen werden.**

Der Committer war nicht der einzige Grund und nicht der groesste. Er war der, den man
sehen konnte. Die zwei anderen sind unten gemessen.

---

## T1 · Nein — drei Gruende, alle gemessen

### Grund 1 · Der Takt kaeme heute nicht von der Stelle

Gefahren auf einer **Kopie** des Auftragsordners im Kratzverzeichnis, damit das echte
Repo unberuehrt bleibt:

    cp -r auftraege <kopie>/
    PYTHONPATH=src .venv-render/bin/python tools/homeworker.py --repo <kopie> --alle --hoechstens 1

Takt 1:

    === auf-20260907-81 [qa] — GPU frei, Leistungsgrenze in Ordnung
        → fehler  (auftraege/ergebnisse/auf-20260907-81.json)

Takt 2, derselbe Befehl noch einmal:

    === auf-20260907-81 [qa] — GPU frei, Leistungsgrenze in Ordnung
        → fehler  (auftraege/ergebnisse/auf-20260907-81.json)

**Zweimal derselbe Auftrag.** Der Zustand danach, gemessen mit eurem eigenen Werkzeug:

    auftrag.zustand('auf-20260907-81', <kopie>)  →  'gerechnet, nicht beantwortet'
    Kopf der Reihe nach zwei Takten                →  auf-20260907-81

Warum, im Code nachgelesen und vom Lauf bestaetigt:

* `fuehre_aus` beantwortet `art: "qa"` seit dem 28.08. **absichtlich** mit
  `status: fehler` — «art misst nichts» (`tools/homeworker.py`, Zweig `if art == "qa"`).
* `auftrag.zustand` ordnet `fehler` — wie `abgelehnt` und `uebersprungen` — dem Zustand
  «gerechnet, nicht beantwortet» zu (`src/aiimaging/auftrag.py:776`), und der steht in
  `UNBEANTWORTET` (`:773`).
* `unerledigt` liefert ihn darum weiter, `nach_rang` stellt ihn wegen `rang: 1` wieder an
  die Spitze, `--hoechstens 1` nimmt genau ihn.

Alle fuenf Minuten heisst: **288 Neuschreibungen derselben Datei am Tag**, und die fuenf
dahinter (82, 85, 89, 90, 92) kommen nie dran.

**Gegenprobe** — kann die Probe ueberhaupt widersprechen? Ja: derselbe Befehl mit
`--hoechstens 2` nimmt tatsaechlich auch den zweiten:

    === auf-20260907-81 [qa] → fehler
    === auf-20260907-82 [qa] → fehler

Die Reihe rueckt also **nur ueber den Deckel** vor, nicht ueber die Erledigung. Beide
sind `qa`-Auftraege; es lief kein Blender, keine Karte, keine Inferenz.

**Und es trifft nicht nur `qa`.** Ein `render` bekommt bei belegter Karte `abgelehnt`
(`if not frei and satz["art"] == "render"`), und `abgelehnt` zaehlt genauso als
unbeantwortet. Auf dieser Maschine ist die belegte Karte der Normalfall. Die Bauart ist
also: **Mit `--hoechstens 1` blockiert jeder Kopf, der nicht `ok` werden kann, die ganze
Reihe auf Dauer.** Das ist kein Fehler eures Skripts, aber es ist ein Takt, der aussieht
wie Betrieb und keiner ist.

### Grund 2 · Der zweite Schreiber bleibt, auch ohne Committer

Wir haben ihn in dieser Sitzung live erwischt (Belege unter T4): Um 15:25 war der
verfolgte Baum sauber, um 15:33:30 lag `tools/studie_echtschaetzer.py` darin, 15 400
Bytes, und die eigene Kopfzeile der Datei nennt ihren Auftrag: **«DIE FALLTABELLE MIT
ECHTEM TIEFENSCHAETZER — auf-20260907-81»**.

Eine parallele Sitzung baut also **in diesem Augenblick** die richtige Antwort auf genau
den Auftrag, den ein Takt alle fuenf Minuten mit `fehler` ueberschreiben wuerde.

Damit ist unser Einwand vom 26.08. nur zur Haelfte ein git-Konflikt gewesen. Die andere
Haelfte ist ein Konflikt **um dieselbe Ergebnisdatei**, und die verschwindet nicht
dadurch, dass der Takt nicht mehr committet. Ohne Commit wird sie sogar leiser: Die
mechanische Antwort steht dann nur im Arbeitsbaum, und wer spaeter committet, nimmt sie
mit, ohne sie bestellt zu haben.

**Die Grenze dieser Aussage, damit sie nicht groesser klingt, als sie ist:** Sobald eine
Sitzung `ok` geschrieben hat, fasst der Takt den Auftrag nicht mehr an — `zustand` liest
ihn dann als beantwortet. Eine fertige gute Antwort wuerde er also nicht ueberschreiben.
Was er anrichtet, ist das Fenster davor und der Laerm danach.

### Grund 3 · Die Not ist kleiner geworden — aber die Zahl im Auftrag stimmt so nicht

Euer Satz: «Am 06./07.09. sind zwanzig Antworten an einem Tag gekommen.»

Zwei Massstaebe, weil es zwei verschiedene Dinge sind:

    (a) nach dem Feld `beendet` in der Ergebnisdatei selbst
        06.09.: 26   07.09.: 5   08.09.: 2

    (b) Ergebnisdateien, die an dem Tag durch einen Commit beruehrt wurden
        git log --since=<tag> --until=<tag> --name-only --format='' -- auftraege/ergebnisse
        06.09.: 13   07.09.: 28   08.09.: 2

**ABWEICHUNG, ausdruecklich gemeldet:** «zwanzig an einem Tag» trifft die Groessenordnung,
aber keine der beiden Messungen ergibt zwanzig, und die beiden widersprechen sich in der
Verteilung (26/5 gegen 13/28). Erklaerbar ist das — am 06.09. wurden acht aeltere
Antworten des UI-Workers nachgetragen und teils erst am 07.09. gebuendelt committet —,
aber es heisst: Die Zahl traegt als Groessenordnung, nicht als Beleg fuer einen Tag.

Und der Rueckstand ist **nicht** weg:

    PYTHONPATH=src .venv-render/bin/python tools/homeworker.py --repo . --liste
    → 4 fremd, 4 Fragen, 6 unerledigt fuer 'local':
      auf-20260907-81 [qa]  auf-20260907-82 [qa]  auf-20260909-85 [multipass]
      auf-20260909-89 [render]  auf-20260909-90 [render]  auf-20260909-92 [render]

Es liegt also Arbeit. Nur waere ein Takt nicht das Werkzeug dafuer: Zwei davon kann der
Runner bauartbedingt nie gruen beantworten (`qa`), und die vier anderen faehrt gerade
eine zweite Bahn, einen nach dem anderen.

---

## T2 · Entfaellt (kein Takt) — und die Bedingungen, falls der Owner ihn doch will

Damit ein spaeteres Ja nicht neu verhandelt werden muss, stehen die Bedingungen hier:

* **B1 · Der Kopf darf nicht blockieren.** Ein Auftrag, der schon ein Ergebnis mit
  `fehler` oder `abgelehnt` traegt, wird im naechsten Takt uebersprungen statt neu
  geschrieben. Heute ist das nicht so — oben gemessen.
* **B2 · Ein Riegel gegen den zweiten Schreiber.** Der Takt fasst nichts an, solange eine
  Sitzung im Arbeitsbaum arbeitet. Eine Sperrdatei genuegt, und sie gehoert dem, der
  zuerst da ist.
* **B3 · Abstand einmal je Stunde, nicht alle fuenf Minuten** — und nur, wenn B1 und B2
  stehen. Fuenf Minuten war der Wert fuer einen Dienst, der etwas erledigt.

Ohne B1 und B2 ist ein Takt schlechter als kein Takt.

Zu eurem Hinweis unter «3 · Ein Hinweis zur Sicherheit»: einverstanden, und er ist heute
schon so gebaut. `darf_starten(zustand, auf.auflagen_maschine(satz))` liest die Auflagen
aus dem Auftrag; `betrieb/kosmo-worker.sh` setzt keine eigenen. Da waere nichts zu
aendern gewesen.

---

## T3 · Wie eingecheckt wird — die Push-Haelfte gibt es schon

**Committen: von Hand, durch die Sitzung, die die Antwort geschrieben hat.** Das bleibt
so, und wir halten es fuer richtig: Wer den Text verantwortet, verantwortet den Commit.

**Pushen: das macht bereits ein einzelner, zentraler Lauf, den jemand ueberwacht.** Er
steht nicht in `betrieb/` dieses Repos, sondern ist eine Wache auf dieser Maschine —
`kosmo-zustellung.timer`, stuendlich, Skript `~/KosmoBetrieb/wachen/zustellung.sh`. Sie
holt (`git fetch`), zaehlt `@{u}..HEAD` und pusht, was liegt. Sie **committet nichts** und
fasst den Arbeitsbaum nicht an; das steht so in ihrem eigenen Kopf und deckt sich mit dem
Journal. Dieses Repo ist eine von fuenf Bahnen darin.

    journalctl --user -u kosmo-zustellung.service --since '2026-09-08 00:00'
    Sep 08 14:50:18  zustellung.sh:   ai-imaging    nichts liegen

Damit ist T3 auf der Push-Seite seit dem 01.09. beantwortet. Offen ist nur der Commit —
und den wollen wir bei einem Menschen lassen.

---

## T4 · Der zweite Prozess — gefunden, und es ist kein Dienst

**Es ist eine parallele Claude-Code-Sitzung derselben Linie.**

**Beleg 1, historisch.** Die acht unverfolgten Dateien vom 06.09. sind die Antworten des
UI-/Cloud-Workers, die im anderen Repo (`Architektur-Cosmos`) lagen. Eine parallele
Sitzung hat sie hierher uebertragen und am selben Tag committet:

    git log --format='%h %ad %an %s' --date=iso -- auftraege/ergebnisse/auf-20260824-40.json
    → a4afba3  2026-09-06 19:30:04 +0000  Claude
      «Acht Antworten des UI-Workers — sieben waren gerechnet und nie angekommen, eine ist neu»

**Beleg 2, live in dieser Sitzung.** `git status --porcelain` war um 15:25 leer. Um 15:33
stand darin:

    ?? tools/studie_echtschaetzer.py      15 400 Bytes, mtime 2026-09-08 15:33:30

Die Kopfzeile der Datei nennt ihren Auftrag selbst: «DIE FALLTABELLE MIT ECHTEM
TIEFENSCHAETZER — auf-20260907-81». Diese Sitzung hat sie nicht geschrieben.

**Gegenprobe, damit «kein Dienst» nicht bloss eine Behauptung ist.** Im selben Fenster
ist `kosmo-abholer.service` **sechzehnmal** gelaufen:

    journalctl --user -u kosmo-abholer.service --since '2026-09-08 15:25' | grep -c 'Finished'  → 16

Er ist der einzige installierte Dienst, dessen `WorkingDirectory` in diesem Repo liegt:

    grep -rl "ai-imaging-in-a-box" ~/.config/systemd/user/   → genau eine Datei: kosmo-abholer.service

Nach sechzehn Laeufen trug der verfolgte Baum **keine einzige** Aenderung von ihm; er
schreibt nach `build/` (steht in `.gitignore`) und in die Auftragsablage ausserhalb des
Repos. Haette er den Baum veraendert, haette diese Probe es gezeigt — sie kann
widersprechen, und sie tut es nicht.

Zweiter automatischer git-Akteur auf diesem Repo ist die Zustellung aus T3. Sie pusht,
committet nie und ruehrt den Arbeitsbaum nicht an.

**Damit ist der Nebenbefund vom 26.08. aufgeklaert:** Es war kein unbekannter Dienst,
sondern die eigene, parallele Bahn — und genau deshalb loest das Weglassen des Committers
ihn nicht auf.

---

## Was NICHT gemessen wurde

* **Kein Render, kein Multipass, keine Modell-Inferenz.** Die Karte faehrt gerade eine
  zweite Bahn. Alle Laeufe dieser Antwort blieben im `qa`-Zweig, der vor jedem
  Blender-Aufruf zurueckkehrt.
* **Ob ein Push aus einem nicht-interaktiven Kontext geht** (V2 aus `auf-20260826-59`),
  ist auch hier nicht selbst geprueft. Die Zustellung belegt immerhin, dass ein Push
  **aus einem Dienst** auf dieser Maschine geht, solange eine Sitzung offen und der
  Schluesselbund entsperrt ist. Nachts ist er es nicht; das steht im Kopf von
  `zustellung.sh`.
* **Nichts installiert, nichts committet, nichts gepusht.** `betrieb/kosmo-worker.*`
  bleibt unveraendert und uninstalliert; `systemctl --user list-timers` fuehrt ihn nicht.
  Die Taktproben liefen ausschliesslich auf einer Kopie im Kratzverzeichnis.

---

## Nachtrag, 15:38 derselben Sitzung — der Beleg fuer T4 ist waehrend des Schreibens gewachsen

Zwischen dem Beginn dieser Antwort und ihrem Abschluss sind im selben Arbeitsbaum **vier
weitere** unverfolgte Dateien aufgetaucht, keine davon von dieser Sitzung:

    15:33:30  tools/studie_echtschaetzer.py                          (auf-20260907-81)
    15:33:56  auftraege/ergebnisse/auf-20260907-82-formbefund.md
    15:35:04  auftraege/ergebnisse/auf-20260907-82.json
    15:35:31  auftraege/ergebnisse/auf-20260907-88.json
    15:37:15  auftraege/ergebnisse/ANTWORT-auf-20260907-88-volltext.md

In zwoelf Minuten also fuenf Dateien aus einer fremden Bahn, davon zwei fertige
Ergebnisdateien.

**Genau, was ein Takt in diesem Fenster getan haette** — nicht mehr und nicht weniger, denn
mit `--hoechstens 1` haette er den Kopf genommen, und der war `auf-20260907-81`: Er haette
zweimal getaktet (fuenf Minuten Abstand, zwoelf Minuten Fenster) und beide Male
`auftraege/ergebnisse/auf-20260907-81.json` mit `status: fehler` beschrieben — waehrend
die fremde Bahn um 15:33:30 die richtige Studie zu genau diesem Auftrag anlegte. An
`auf-20260907-82` waere er nicht gekommen; das ist der Kern von Grund 1 und nicht dessen
Abschwaechung.

---

## Befund nebenbei · ein bestehender Test ist rot, und er kann im Betrieb nicht gruen bleiben

    PYTHONPATH=src .venv-render/bin/python -m pytest tests/test_auftraege.py tests/test_auftrag.py \
        tests/test_einbau_stand.py tests/test_contracts.py -q
    → 1 failed, 701 passed, 28 skipped

    FAILED tests/test_auftraege.py::test_die_raenge_sind_lueckenlos_von_eins_an
    AssertionError: ('local', [1, 2, 3, 7, 8, 9, ...])

**Er ist nicht durch diese Antwort rot geworden.** Gegenprobe auf einer Kopie, aus der
allein unsere eigene Ergebnisdatei entfernt ist:

    Raenge OHNE unsere Antwort: [1, 2, 3, 6, 7, 8, 9, 10]   lueckenlos? False

Rang 4 und Rang 5 fehlten schon vorher — `auf-20260907-88` und `auf-20260907-82` sind um
15:35 von der parallelen Bahn beantwortet worden. Um 15:31 war die Reihe noch
1 bis 10 und der Test gruen.

**Die Sache dahinter:** Der Test prueft die Raenge der **unerledigten** Auftraege auf
Lueckenlosigkeit ab eins. Das kann nur unmittelbar nach einer Neuvergabe stimmen. Sobald
ein Auftrag beantwortet wird, der nicht der letzte im Rang ist — also im normalen
Betrieb, mehrmals taeglich —, ist er rot. Er misst damit nicht die Reihenfolge, sondern
das Alter der Nummerierung.

Wir aendern ihn nicht: Der Rang steht in EUREM Auftrag, und die Nummerierung gehoert dem,
der sie vergibt. Wir melden ihn, weil ein Waechter, der im Normalbetrieb rot steht, nach
kurzer Zeit uebersehen wird — und dann auch dann, wenn er einmal etwas Echtes meldet.
