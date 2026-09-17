# Was jetzt beim Owner liegt — vier Entscheide, eingesammelt am 17.09.2026

**Grundlage:** keine
**Nachgesehen bis:** 364dfa4
**Codestand:** `364dfa4`

Dieses Blatt sammelt ein, was in vier Antwortdateien verstreut als **OWNER-ENTSCHEID**
markiert ist, plus den einen Entscheid, der aus unserer eigenen Arbeit kommt. Es entscheidet
nichts — es legt die Wege nebeneinander und nennt, was jeder kostet.

*Wozu es das gibt: Ein Entscheid, den der Owner erst aus vier Dateien zusammensuchen muss,
existiert nicht.*

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

---

## Was ausdrücklich **kein** Owner-Entscheid ist

* **`auf-20260827-64`** — reine Auskunft, und wir konnten sie ihnen beantworten: Die
  fragliche Funktion liegt bei uns und liest flache Feldnamen.
* **`auf-20260826-53`, U8a** — die Rückfrage bei fehlendem Geländebeleg. Sie halten sie für
  **zumutbar**, unter der Bedingung, dass sie nur im messbaren Fall erscheint und im
  unentscheidbaren schweigt. Das ist eine Einschätzung mit Begründung, kein Entscheid.
* **`auf-20260827-63`** — der Zuständigkeitsentscheid dazu ist am 06.09.2026 gefallen und
  bleibt unverändert.
