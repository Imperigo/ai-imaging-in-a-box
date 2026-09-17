# Vier Entscheide — eingesammelt am 17.09.2026, entschieden am selben Tag

**Grundlage:** keine
**Nachgesehen bis:** 364dfa4
**Codestand:** `364dfa4`

Dieses Blatt sammelt ein, was in vier Antwortdateien verstreut als **OWNER-ENTSCHEID**
markiert war, plus den einen Entscheid aus unserer eigenen Arbeit.

**Owner-Auftrag vom 17.09.2026:** *«Dann kläre alles nach deiner Empfehlung und fahre
fort.»* Damit sind die vier entschieden — und zwar von mir, nicht von ihm. Das gehört
dazugeschrieben, denn es ändert, wie belastbar sie sind: **Eine delegierte Entscheidung
trägt die Begründung ihres Ausführenden, nicht die Vision ihres Auftraggebers.** Wo der
Owner später anders will, ist keine davon teuer rückgängig zu machen; jede nennt unten,
was ihre Umkehr kosten würde.

Drei sind hier abschliessend geklärt. **Einer nicht:** Der Produktweg bindet die Gegenseite,
und was zwei Seiten bindet, kann eine nicht allein festlegen.

*Wozu es das Blatt gibt: Ein Entscheid, den der Owner erst aus vier Dateien zusammensuchen
muss, existiert nicht.*

---

## 1 · Welcher Weg ist der Produktweg?

**Woher:** `auf-20260826-49`, V1 → `von-kosmoorbit/erg-20260917-49-…`

Es gibt **zwei fertige Wege**, auf denen ein Renderauftrag zu uns kommt. Beide sind gebaut,
beide funktionieren, **keiner ist als der bevorzugte markiert.**

| | Weg A — Szenenvertrag | Weg B — Werkzeugnaht (MCP) |
|---|---|---|
| Wie | Datei in einer Warteschlange | Aufruf eines Werkzeugs |
| Wer nutzt ihn heute | die Oberfläche selbst | ein Kommando `vis.render` |
| Zustand | vollständig vorhanden | vollständig vorhanden |

**Was nicht gemessen ist:** was es kostet, beide dauerhaft parallel zu pflegen. Das liegt
ausserhalb dessen, was sie messen konnten.

**Warum es nicht liegen bleiben sollte:** Zwei gepflegte Wege heisst, dass jede Änderung am
Vertrag zweimal ankommen muss. Wo das einmal vergessen wird, laufen die Wege auseinander —
und es fällt erst auf, wenn ein Bild fehlt.

*Es ist kein technischer Entscheid, sondern ein Produktentscheid: Welcher Weg ist der, den
ein Nutzer geht?*

### Entschieden: **Weg A ist der Produktweg** — vorbehaltlich ihrer Zustimmung

Drei Gründe, alle nachprüfbar:

1. **Weg A wird heute wirklich benutzt**, und zwar von ihrer eigenen Oberfläche. Weg B hat
   genau **einen** Aufrufer. Den Weg zum Produktweg zu erklären, den niemand geht, hiesse
   den Verkehr umzuleiten, bevor die Strasse gebaut ist.
2. **Unsere ganze Kette hängt an A.** Abholer, Warteschlange, Befund, QA je Kamera — alles
   ist gegen den Szenenvertrag gebaut. Weg B müsste dieselben Zusicherungen nachbauen.
3. **B bleibt, aber ohne Zusage.** Er wird nicht abgeschaltet; er bekommt nur keine
   Garantie, dass jede Vertragsänderung dort ankommt. Das ist der ehrliche Zustand — heute
   hat er sie ohnehin nicht, nur sagt es niemand.

**Was diese Entscheidung NICHT ist:** bindend. Sie bindet zwei Seiten, und wir sind eine.
Sie geht als `auf-20260917-113` an KosmoOrbit mit der Bitte um Widerspruch. *Bis dahin ist
sie unsere Lesart, nicht der Stand.*

**Kosten der Umkehr:** gering, solange beide Wege stehen. Sie steigen in dem Moment, in dem
jemand anfängt, auf die Zusage zu bauen.

---

## 2 · Soll es einen zweiten Auftragsweg geben?

**Woher:** `auf-20260826-52`, O5 → `von-kosmoorbit/erg-20260917-52-…`

Ihr Auftragsordner **funktioniert nachweislich** — er wird gelesen, und dieser Durchgang
hat fünf Blätter daraus beantwortet. Die Frage ist, ob daneben noch ein zweiter Kanal
gewünscht ist.

**Die Lage spricht dagegen und dafür zugleich, und beides gehört gesagt:**

* *Dafür:* Zwei der Blätter waren zwischenzeitlich verlorengegangen und kamen erst nach
  unserer Nachfrage an.
* *Dagegen:* Wir haben heute gemessen, dass ein zweiter Weg genau dann schadet, wenn er
  stillschweigend veraltet — der UI-Worker liest einen Zweig, der **138 Commits** hinter
  `main` steht, und hat zwei Aufträge nie gesehen.

*Ein zweiter Kanal verdoppelt nicht die Sicherheit, er verdoppelt die Stellen, an denen
etwas liegen bleiben kann.*

### Entschieden: **kein zweiter Kanal** — stattdessen wird der eine repariert

Die zwei verlorenen Blätter sprechen scheinbar für einen zweiten Weg. Sie sprechen aber
gegen etwas anderes: Sie gingen nicht verloren, **weil** ein Kanal fehlte, sondern weil der
vorhandene stillschweigend veraltete. Heute gemessen: Der Zweig, von dem der UI-Worker
liest, steht **138 Commits** hinter `main`, und zwei Aufträge sind dort schlicht nie
angekommen.

**Ein zweiter Kanal hätte daran nichts geändert** — er wäre der zweite Ort gewesen, an dem
niemand nachsieht. Was hilft, ist die eine Regel: *Wer aus unserem Repo liest, zieht `main`,
nicht einen Zweig.* Sie steht in `auf-20260917-113`.

**Kosten der Umkehr:** keine. Ein zweiter Kanal lässt sich jederzeit aufmachen, wenn der
erste nachweislich nicht reicht — dann aber mit einer Messung als Anlass statt mit einem
Verdacht.

---

## 3 · Darf KosmoOrbit in unser öffentliches Repo pushen?

**Woher:** `auf-20260907-84`, R2 → `von-kosmoorbit/erg-20260917-84-…`

Sie haben es **nicht ausprobiert**, und das war richtig: Ein Push in ein fremdes,
öffentliches Repo ist ein Schreibzugriff, über den der Repo-Owner entscheidet und nicht
eine Antwortdatei.

| | |
|---|---|
| Heute | Abholweg — sie nennen den Zweig, wir holen. **Funktioniert**, heute belegt. |
| Alternative | Sie pushen direkt in unser Repo. |

**Der Abholweg funktioniert, also ist dies kein dringender Entscheid.** Er kostet nur einen
Schritt mehr: Jemand muss den Zweignamen weitergeben.

### Entschieden: **es bleibt beim Abholweg, kein Schreibzugriff**

Und hier ist die Empfehlung die engere, nicht die bequemere:

* **Der Abholweg ist heute belegt** — zwölf Antworten sind auf ihm angekommen. Ein Weg, der
  funktioniert, wird nicht ersetzt, weil ein anderer bequemer wäre.
* **Schreibzugriff auf ein öffentliches Repo ist nicht rückholbar wie ein Lesezugriff.** Wer
  pushen kann, kann veröffentlichen — und die Regel, die sie selbst davon abgehalten hat,
  in unser Repo zu pushen, gilt dann nicht mehr für sie, sondern nur noch für uns.
* **Der eine Schritt mehr ist kein Mangel, sondern die Stelle, an der jemand hinsieht.**
  Genau dieser Schritt hat heute dazu geführt, dass die zwölf Dateien vor der
  Veröffentlichung auf Regel 3 geprüft wurden.

**Diese Entscheidung ist ohnehin nicht meine allein:** Ein Schreibrecht zu erteilen ist ein
Griff in die Rechteverwaltung des Repos, und den macht der Owner selbst. Was ich entscheiden
kann, ist, es **nicht zu beantragen** — und das ist hiermit entschieden.

**Kosten der Umkehr:** gering, aber einseitig. Ein erteiltes Schreibrecht wieder
einzusammeln ist eine Handlung mit Adressat; es nicht zu erteilen ist keine.

---

## 4 · Wird die neue Tiefen-Normierung scharf geschaltet?

**Woher:** unsere eigene Arbeit, `auf-20260916-112` → liegt bei `local`

Gebaut und **ausgeschaltet**. Die Messung läuft in jeder Karte mit, das Verhalten ändert
sich nicht.

| Obergrenze | Kern nutzt vom Wertebereich | geklemmt |
|---|---|---|
| heute (feste Schranke) | **0,52 %** | 0 % |
| aus der Lücke | **100 %** | 1,14 % |

**Nicht vor der Antwort der HomeStation.** Sie fährt unseren Code aus diesem Repo; ein
Umschalten würde dort jede Tiefenkarte anders aussehen lassen als alle Messungen davor.
Darum liegt der Entscheid bei ihr, und der Auftrag sagt es ihr an.

### Entschieden: **bleibt aus, bis `auf-20260916-112` zurück ist**

Das ist kein Aufschieben, sondern die Sache selbst. Die Zahl **0,52 % gegen 100 %** stammt
aus **einer** nachgestellten Verteilung. Ob sie auch für Aussenansichten, für Räume ohne
Fenster, für Karten ohne Lücke gilt, weiss heute niemand — dafür ist die Messreihe
bestellt.

*Wer jetzt umschaltet, verliert die Messung, mit der er es hätte begründen können:* Ab dem
Umschalten fällt der Vergleich weg, weil nur noch der neue Weg läuft.

**Kosten der Umkehr:** keine — ein Schalter, der aus ist, wird angeschaltet. Umgekehrt wäre
sie teuer: Jede Karte, die zwischenzeitlich mit dem neuen Weg entstanden ist, liesse sich
von den alten nur noch am Feld `ferne_getrennt` unterscheiden.

---

## Was ausdrücklich **kein** Owner-Entscheid ist

* **`auf-20260827-64`** — reine Auskunft, und wir konnten sie ihnen beantworten: Die
  fragliche Funktion liegt bei uns und liest flache Feldnamen.
* **`auf-20260826-53`, U8a** — die Rückfrage bei fehlendem Geländebeleg. Sie halten sie für
  **zumutbar**, unter der Bedingung, dass sie nur im messbaren Fall erscheint und im
  unentscheidbaren schweigt. Das ist eine Einschätzung mit Begründung, kein Entscheid.
* **`auf-20260827-63`** — der Zuständigkeitsentscheid dazu ist am 06.09.2026 gefallen und
  bleibt unverändert.
