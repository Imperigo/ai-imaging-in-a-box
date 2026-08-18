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

### Aufträge an die HomeStation kommen mit einem kopierbaren Prompt

Ein Auftrag im Repo ist die Hälfte. Die andere Hälfte ist der Text, den der Owner ohne
Nachdenken weiterreichen kann — **fertig formuliert, in einem Block, zum Kopieren**
(Owner-Wunsch 2026-08-18).

Wer etwas von der HomeStation will, liefert beides:

1. Die Auftragsdatei unter `auftraege/offen/`, **committet und gepusht**, bevor der
   Prompt herausgeht. Ein Prompt, der auf einen Auftrag zeigt, den es auf dem Remote
   noch nicht gibt, ist eine Fehlanweisung.
2. Einen Prompt-Block im Chat: was zu tun ist, in welcher Reihenfolge, was
   zurückkommen soll — und was **nicht** getan werden soll. Kein „siehe Auftrag XY",
   sondern der Inhalt.

Faustregel wie bei der Oberfläche: Was der Owner erst zusammensuchen muss, existiert
nicht.

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
