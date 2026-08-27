# AI Imaging in a Box

Prototyp zur Vertiefungsarbeit an der ETH Zürich (HS26, ITA, Betreuung Gonzalo Casas).
Öffentliches Repo, Apache-2.0.

> **Hinweis zur Entstehung dieser Datei:** Beim ersten Arbeitsauftrag (2026-08-14) war das
> Repo leer — nur eine zweizeilige `README.md`, keine `CLAUDE.md`, kein `LICENSE`. Die vier
> Regeln unten sind aus dem Auftrag des Owners übernommen und hier erstmals schriftlich
> fixiert. Wenn eine ältere, andere `CLAUDE.md` existiert, hat diese Vorrang — bitte melden.

---

## Die vier nicht verhandelbaren Regeln

### 1 · Permissive Lizenzen, ohne GPL/AGPL

Alles, was in das ausgelieferte Produkt eingeht, ist MIT, Apache-2.0, BSD oder MPL-2.0.
**Kein GPL, kein AGPL** — weder als Abhängigkeit noch als gebündelte Komponente.

- GPL/AGPL-Funde werden **ausdrücklich als solche gemeldet**, nie stillschweigend übergangen.
- Modellgewichte zählen mit: Non-Commercial-Lizenzen (FLUX.1-dev, FLUX.2-dev) sind
  ausgeschlossen, auch für daraus abgeleitete LoRAs.

**Präzisierung LGPL (Owner-Entscheid 2026-08-14):** LGPL-Bibliotheken sind zugelassen,
aber ausschliesslich unter drei Auflagen:

1. **Nur hinter einer Prozessgrenze** — eigenes venv, Aufruf als Subprozess, Austausch
   über Dateien. Kein `import` im Produkt-venv.
2. **Unverändert** — wird die Bibliothek selbst angefasst, greift das Copyleft. Wer eine
   Änderung braucht, eskaliert statt zu patchen.
3. **Austauschbar und deklariert** — die Bibliothek muss ersetzbar bleiben, und sie
   gehört mit ihrer Lizenz ins `NOTICE`.

Dieselben drei Auflagen gelten für GPL-Komponenten, die als eigenständiges Programm
aufgerufen werden (Blender, IfcOpenShell) — siehe Regel 2.

### 2 · Blender nur als externer Prozess, nie als Add-on

Blender ist GPL. Die saubere Grenze ist der **Prozessaufruf**, nicht der Import.

- Erlaubt: `blender --background --python script.py` als Subprozess.
- Verboten: `import bpy` im Produkt-venv, das `bpy`-PyPI-Wheel, jede Add-on-Verpackung
  (`bl_info`, `register()`/`unregister()`), jede Abhängigkeit von einer laufenden Blender-UI.
- Das Blender-Binary wird als GPL-Komponente im `NOTICE` deklariert, nicht einverleibt.

### 3 · Keine echten Projektdaten, keine darauf trainierten Gewichte im Repo

- Keine Bürodaten, keine Kundenprojekte, keine IFC/Pläne/Renders aus echten Aufträgen.
- Keine LoRAs oder Checkpoints, die auf solchen Daten trainiert wurden.
- Auch keine Büro-, Kunden- oder Projektnamen in Pfaden, Kommentaren oder Testfixtures.
- Testdaten sind synthetisch und im Repo erzeugbar.

### 4 · Der Kern ist eine Bibliothek, ohne Oberfläche aufrufbar

Jede Fähigkeit muss aus Python heraus nutzbar sein, ohne dass eine GUI läuft.

- Die Oberfläche ist eine dünne Schicht über der Bibliothek, nie deren Voraussetzung.
- Kein `import bpy` und kein UI-Framework-Import im Kern.
- Faustregel: Was nur über einen Klick erreichbar ist, existiert nicht.

---

---

## Arbeitsregeln

### Das Lexikon wird mitgeführt

`docs/LEXIKON.md` erklärt jeden nicht-architektonischen Fachbegriff des Projekts für
Leser:innen ohne Informatikhintergrund. Es ist Anhang der Vertiefungsarbeit, kein
Nebenprodukt.

**Pflicht bei jeder Sitzung:** Taucht ein Fachbegriff in Code, Commit, Erklärung oder
Gespräch auf, der dort noch nicht steht, wird er nachgetragen — in derselben Sitzung,
nicht später. Definitionen sind für Laien geschrieben: was es ist, wozu es dient, und
wo es im Projekt vorkommt. Keine Definition, die einen anderen unerklärten Fachbegriff
voraussetzt.

### Jede Sitzung wird protokolliert

Nach `docs/sitzungen/JJJJ-MM-TT_sitzung-NN.md`. Die Gespräche tragen Entscheidungen und
Begründungen, die sonst nur im Kontext des Modells existieren — und der geht mit der
Sitzung verloren. Was nicht in einer Datei steht, ist weg.

Ins Protokoll gehören: getroffene Entscheidungen **mit Begründung**, korrigierte
Fehlannahmen (die kehren wieder), geprüfte Befunde samt Prüfweg, die Fragen des Owners,
und was am Ende offen blieb. Kein wörtliches Gesprächsprotokoll — die Substanz.

`docs/PLAN.md` wird in derselben Sitzung fortgeschrieben: Erledigtes abhaken, nicht
löschen.

### Aufträge gehören in das Repo, nicht in den Chat

**Es gibt drei Worker, und sie können nicht dasselbe** (Owner-Hinweis 2026-08-22,
erweitert 2026-08-26):

* **`local` — die HomeStation.** GPU, Blender, `.venv-ifc`, unser Repo. Misst, rendert,
  prüft. Liest `auftraege/offen/` und legt Ergebnisse daneben.
* **`cloud` — der Worker an KosmoOrbit.** Hat unser Repo **nicht**; er hält **ihren
  Vertrag** und ihre Warteschlange. Was er tun soll, betrifft nie unseren Code.
* **`ui` — der Kosmo-UI-Worker.** Seit dem 26.08.2026 zuständig für die **ganze
  Oberfläche** von KosmoOrbit. Er hat unser Repo **als Quelle** — ein Auftrag in
  `auftraege/offen/` erreicht ihn also über git.

Ein Messauftrag an den Cloud-Worker wäre unerfüllbar, ein Vertragsauftrag an die
HomeStation liefe ins Leere, und ein Oberflächenauftrag an einen von beiden landete bei
jemandem, der die Oberfläche nicht mehr baut. `auftrag.py` verlangt das Feld `worker`
darum als Pflicht.

**Warum `ui` und `cloud` getrennt bleiben, obwohl beide „drüben" sind:** Vertrag und
Oberfläche sind zwei Gegenstände. *Welchen Feldnamen ein QA-Block je Kamera bekommt*, ist
eine Vertragsfrage; *ob neben der Zahl ihr Vorbehalt steht*, eine Oberflächenfrage. Beide
an dieselbe Stelle zu schicken hiesse, dass eine liegen bleibt, weil sie nicht zum Auftrag
des Lesers gehört.

**Was beim UI-Worker landet:** jeder Punkt zur Oberfläche, der bei der eigenen Arbeit
auffällt — ein Bedienelement ohne Wirkung, eine Zahl ohne ihren Vorbehalt, ein Zustand,
den die Anzeige auf zwei rundet. Sie werden **gesammelt und als Auftrag weitergegeben**,
nicht im Vorbeigehen erwähnt.

**Der Auftrag trägt seine Anweisung vollständig in sich** (Owner-Wunsch 2026-08-22). Bis
dahin galt: Auftragsdatei ins Repo, Prompt in den Chat. Das hiess für den Owner, jeden
Auftrag von Hand hin- und herzukopieren — Arbeit, die niemand tun sollte, und eine
Fehlerquelle obendrein.

Neu gilt: **Was der Worker wissen muss, steht in der Auftragsdatei.** Was zu tun ist, in
welcher Reihenfolge, was zurückkommen soll, und was **nicht** getan werden soll. Kein
„siehe Dokument XY", sondern der Inhalt — ein Auftrag, der auf etwas verweist, das der
Worker erst suchen muss, ist ein halber Auftrag.

Im Chat steht danach höchstens **ein Satz**: dass der Auftrag liegt und was er fragt.

Faustregel wie bei der Oberfläche: Was der Owner erst zusammensuchen muss, existiert nicht.

### Der Einbau ist das Ziel, nicht der Bau

**Owner-Auftrag 26.08.2026**, und er verschiebt den Massstab dieser Arbeit:

> *«Sorge dafür, dass andere Worker immer alles einbauen in die Software — das ist
> Endziel. Du verteilst, wo was hin muss, und du bist verantwortlich, dass sie es einbauen
> und mir dann bestätigst.»*

Damit ist gebauter Code **kein Ergebnis mehr, sondern eine Zwischenstufe.** Das Ergebnis
ist Code, der in KosmoOrbit läuft. Dazwischen liegen drei fremde Wartende, und keiner von
ihnen liest Gedanken.

Vier Pflichten folgen daraus:

1. **Verteilen.** Jeder offene Posten hat einen **Adressaten** — `local`, `cloud` oder
   `ui`. «Niemand» war bis zum 26.08.2026 eine zulässige Angabe im Einbau-Stand; sie ist
   es nicht mehr. Ein Posten ohne Adressaten wird nie eingebaut, und es fällt keinem auf.
2. **Nachhalten.** Der Rückstand wird **gezählt, nicht geschätzt**: `aiimaging.einbau`
   und `tools/einbau.py` sagen, welcher Auftrag wie lange bei wem liegt. Was von Hand
   gezählt wird, wird irgendwann nicht mehr gezählt.
3. **Einbauen lassen heisst einbauen beauftragen.** Ein Messauftrag ist kein
   Einbauauftrag. Wer eine Zahl liefert, hat nichts eingebaut — der Auftrag muss sagen,
   *was in die Software kommt*, und die Rückgabe muss den Einbau belegen, nicht die
   Messung.
4. **Bestätigen.** Was eingebaut ist, wird dem Owner gemeldet — mit Beleg und Datum, im
   Einbau-Stand abgehakt. **Nicht** gemeldet wird, was gebaut ist: Das ist der Unterschied,
   um den es in diesem Auftrag geht.

**Der Zustand dazwischen hat einen eigenen Namen.** Was bei uns fertig ist und drüben
ungeprüft, heisst im Einbau-Stand `gebaut, am Gerät unbestätigt` — weder erledigt noch
offen. Die dritte Antwort dieses Projekts, angewandt auf den Einbau.

**Und der stillste Weg ist der dritte.** Die HomeStation führt `tools/homeworker.py` und
`tools/abholen.py` **aus diesem Repo** aus: Ein `git pull` dort ändert, was gerechnet
wird, ohne dass irgendwo ein Posten umspringt. Eine Verhaltensänderung auf diesem Weg
**wird angesagt, bevor sie ankommt** — sonst sieht sie drüben aus wie ein Fehler.

**Ein Messauftrag an die HomeStation braucht keine Rückfrage** (Owner-Freigabe
2026-08-26): *«Schicke Aufträge an den Local Worker immer, wenn du HomePC-Tests
benötigst.»* Was GPU, echte Gewichte oder einen Blick auf das fremde Backend braucht,
wird als Auftrag abgelegt — nicht als Frage an den Owner und nicht als Vorbehalt in einem
Dokument. **Eine Messung, die hier nicht geht, ist keine offene Frage, sondern ein
unverschickter Auftrag.**
### Git

Innerhalb dieses Repos entscheidet Claude eigenständig über Zweige und Zusammenführungen
(Owner-Freigabe 2026-08-14). Gearbeitet wird auf Themenzweigen; ist ein Stand in sich
schlüssig und geprüft, wird nach `main` zusammengeführt. Ein Pull Request wird nur
angelegt, wenn wirklich etwas zu besprechen ist. Ausserhalb dieses Repos wird nichts
ohne Rückfrage geändert.

Commit-Messages tragen das *Warum*, nicht das *Was*.

---

## Arbeitsstand

Der erste Auftrag war ausdrücklich **kein Bau**, sondern eine Lagebeurteilung:
→ `docs/LAGEBEURTEILUNG_2026-08-14.md`

Diese Datei nennt für jeden offenen Baustein die Lizenz, meldet GPL/AGPL-Funde explizit
und benennt, wo der Prototyp eigenständig werden muss statt Bestehendes zu verdoppeln.

Es ist noch kein Code geschrieben.
