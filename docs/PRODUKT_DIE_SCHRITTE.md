# Visbox — die Schritte, und wie weit jeder gebaut ist

> **Bis zum 21.09.2026 hiess dieses Blatt «die sechs Schritte».** Es sind sieben geworden:
> Der Owner hat an diesem Abend entschieden, dass die Software Volumen **erfinden** darf
> und das Ergebnis danach **zurück ins Modell** soll. Der siebte Schritt ist der Rückweg.

**Dieses Blatt ist für den Owner geschrieben, nicht für die Arbeit.** Es beantwortet eine
einzige Frage: *Was kann die Software heute, und was noch nicht?* Kein Herleitungsweg,
keine Fachsprache ohne Erklärung, keine Zahl ohne ihre Folge.

Der Text der Vertiefungsarbeit steht in `docs/arbeit/` und wird vom Owner geschrieben
(Entscheid 21.09.2026). Dieses Blatt ist die Zuarbeit dazu: **was gebaut wurde, in
welcher Reihenfolge, und was dabei offen blieb.**

> **Fortgeschrieben wird es in derselben Sitzung, in der gebaut wird.** Ein Standblatt,
> das nachgezogen wird, wenn Zeit ist, steht irgendwann auf einem alten Stand — und ein
> alter Stand sieht genauso aus wie ein aktueller.

---

## Wozu die Software da ist — zwei Betriebsarten, nicht eine

**Owner-Entscheid 21.09.2026, und er ist der wichtigste Satz auf diesem Blatt:**

> *Das AI-Imaging soll auch **Volumen erfinden** dürfen — nach einer Skizze, ins fertige
> Bild gezeichnet, für schnelle Variantenstudien. Und wenn ein Bild überzeugt, soll Kosmo
> versuchen, es im Modell nachzubauen.*

Damit hat die Software **zwei** Aufgaben, und sie sind fast entgegengesetzt:

| | **Darstellung** | **Entwurf** |
|---|---|---|
| Die Frage | Zeigt das Bild, was im Modell steht? | Wie sähe es aus, wenn dort etwas anderes stünde? |
| Erfundenes Volumen | **Fehler** | **das Ergebnis** |
| Die Prüfung sagt | bestanden oder durchgefallen | **wo** es abweicht |
| Wofür | Präsentation, Abgabe | Variantenstudie am Bild |

**Und die Prüfung ist in beiden dieselbe.** Das ist der Punkt, an dem das zusammenpasst:
Die Software vergleicht Bild und Modell. Heute liest man daraus ein Urteil ab. Im
Entwurfsmodus liest man **dieselbe Zahl** als Differenz — *und genau diese Differenz ist
die Übergabe an Kosmo.* Ohne sie hätte Kosmo nur ein Bild und müsste raten, was neu ist.

> *Der Riegel und der Messstab sind dasselbe Gerät. Nur liest man im einen Modus ein
> Urteil ab und im anderen eine Differenz.*

**Was dem heute im Weg steht, und es ist gemessen:** Unser Vorgabe-Bildmodell nimmt
**überhaupt kein Eingangsbild an**. Ohne Eingangsbild gibt es keine Skizze, die
hineingereicht werden könnte. Mehr dazu weiter unten.

---

## Der Ablauf, um den es geht

Aus Entscheid **E4** (18.09.2026) — die kleinste Fassung, die ein Erfolg wäre:

```
1 Modell rein → 2 Kamera → 3 Blender-Render → 4 KI-Bild → 5 hineinzeichnen → 6 neues Bild
```

**Woran der Erfolg gemessen wird:** Eine fremde Person öffnet die Software zum ersten Mal
und kommt **ohne Hilfe** zu einem veränderten Bild.

---

## Der Stand, Schritt für Schritt

| # | Schritt | Stand | Woran es noch hängt |
|---|---|---|---|
| 1 | **Modell rein** | **gebaut** | Blender hat der Importeur nur einmal wirklich gesehen (`auf-126`). |
| 2 | **Kamera** | **gebaut**, aber nicht bedienbar | Die Software wählt den Standpunkt selbst. Von Hand wählen geht nur über die Bibliothek. |
| 3 | **Blender-Render** | **gebaut** | Läuft nur, wo Blender liegt — also bis heute nur auf der Werkstattmaschine. |
| 4 | **KI-Bild** | **gebaut** | Braucht eine Grafikkarte. Der Vorgabeweg lief dort drei Wochen lang gar nicht (repariert 21.09.). |
| 5 | **hineinzeichnen** | **nicht gebaut** | Braucht ein Modell, das ein Bild annimmt. Unseres tut es nicht. |
| 6 | **neues Bild** | **nicht gebaut** | Folgt aus 5. |
| 7 | **zurück ins Modell** (Kosmo baut nach) | **nicht gebaut** | Neu seit 21.09. Braucht die Differenz aus Schritt 6. |

**Dazu, quer über alle Schritte:**

| Teil | Stand | Bemerkung |
|---|---|---|
| **Die Mappe** (ein Projekt öffnen, morgen dort weitermachen) | gebaut | Merkt sich auch, ob das Modell seither verändert wurde. |
| **Die Oberfläche** | gebaut, wächst | Läuft auf dem eigenen Rechner, ohne Netz, ohne fremde Bausteine. |
| **Der Knotenbaum** | bedienbar | Zeigt, was gerechnet würde, und lässt die Werte ändern. Knoten hinzufügen geht nicht. |
| **Die Bildanzeige** | **neu am 21.09.2026** | Zeigt die Bilder selbst, mit dem Prüfvermerk **auf** dem Bild. |

---

## Was zuletzt dazugekommen ist

### 21.09.2026 · Die Fläche zeigt Bilder

Bis dahin nannte sie **Dateinamen und Urteile** — ein Werkzeug für Bilder, das keine
Bilder zeigt. Jetzt stehen die Bilder da, und zwar so:

* **Der Prüfvermerk sitzt auf dem Bild**, nicht daneben. Grund: Beim Weiterreichen — ein
  Bildschirmfoto, ein Ausschnitt in einer Mail — bleibt nur das Bild übrig.
  *Ein Vorbehalt, der beim ersten Weiterreichen abfällt, ist kein Vorbehalt.*
* **Drei Zustände, drei verschiedene Rahmen.** Geprüft, durchgefallen, **nicht geprüft** —
  der letzte gestrichelt, damit er sich auch ohne Farbe unterscheidet.
* **Nebeneinander.** Ein nachbearbeitetes Bild steht neben der Vorlage, auf der es
  aufsetzt. Ohne Vorher gibt es kein Nachher.
* **Und wo die Datei fehlt, steht die Lücke da** — in der Grösse, die das Bild hätte.
  *Ein Name ohne Datei sieht in einer Liste genauso aus wie einer mit.*

**Was dabei zusätzlich nötig war:** Von dem Augenblick an, in dem die Fläche Dateien
ausliefert, entscheidet sie, was von dieser Platte in einen Browser geht. Sie liefert
darum ausschliesslich Bilder aus dem Projektordner — geprüft am **aufgelösten** Pfad, nicht
am Namen, damit ein Verweis nicht hinausführt.

### 21.09.2026 · Der Vorgabeweg rechnete gar nicht mehr

Auf der Werkstattmaschine lief das KI-Bild **überhaupt nicht** — die Software verlangte
39 GB Grafikspeicher für einen Lauf, der 25 braucht, und wich deshalb auf einen langsamen
Weg aus, der stirbt. Repariert; die Hälfte des Fehlers (der Ausweichweg selbst) ist
gemessen bestellt und noch offen.

### 21.09.2026 · Die Registry sagt jetzt, ob eine Zahl gemessen oder geschätzt ist

Beim Nachsehen, welches Modell eine Skizze annehmen könnte, fiel ein Fehler in der
Reparatur von heute früh auf: Der neue, kleinere Sicherheitszuschlag war damit begründet,
dass die Speicherzahl **gemessen** sei — bei fünf von sieben Modellen ist sie aber
**geschätzt**. *Ein Zuschlag, der mit einer Messung begründet ist, darf nicht auf eine
Schätzung angewandt werden.* Berichtigt; auf der Werkstattmaschine ändert es heute keine
einzige Entscheidung, aber die Begründung stimmt wieder.

### 21.09.2026 · Ein Lauf sagt jetzt, was er gerechnet hat

Vorher stand im Protokoll «mit Ankerbild gerechnet», während ohne gerechnet wurde.

---

## Was als Nächstes dran ist

| | Schritt | Warum jetzt |
|---|---|---|
| **1** | **Den Standpunkt von Hand wählen** (Schritt 2) | Die Software entscheidet ihn heute allein. Für ein Architekturbild ist der Blickpunkt keine Nebensache. |
| **2** | **Den Lauf in der Fläche starten und zusehen** | Heute rechnet die Fläche, und dann steht sie still. Ein Fortschritt, den niemand sieht, sieht aus wie ein Absturz. |
| **3** | **Schritt 5 «hineinzeichnen»** | Entschieden, aber **hardwareseitig blockiert** — siehe unten. |

---

## Was Schritt 5 heute wirklich blockiert — und es ist keine Frage mehr

Die Frage «darf die Tiefenkarte wahlweise werden?» ist am 21.09.2026 **beantwortet: ja**,
unter drei Auflagen (Entscheid E23). Damit ist der Weg entschieden.

**Im Weg steht jetzt etwas anderes, und es ist gemessen:**

**1 · Unser Bildmodell nimmt kein Eingangsbild an.** Sieben Läufe auf der
Werkstattmaschine, verschiedene Eingangsbilder, verschiedene Stärken — **eine einzige
Prüfsumme**. Das Bild kam nie an. Ohne Eingangsbild gibt es keine Skizze, die
hineingereicht werden könnte.

**2 · Es gibt genau ein erlaubtes Modell, das es könnte** — `qwen-image-edit-2511`,
Apache-2.0. Ob es auf der Werkstattkarte überhaupt läuft, ist offen: Die einzige Messung
dazu sagt, die Gewichte passen mit 29,57 von 31,4 GB gerade so hinein — und dann scheitert
das Rechnen an 18 MB. *Es passte nicht. Knapp, aber nicht.*

**3 · Der Ausweichweg für zu grosse Modelle ist kaputt.** Derselbe, der heute früh den
Vorgabe-Backbone lahmgelegt hat. Ohne ihn hat ein zu grosses Modell keinen zweiten Weg.

**Die Reihenfolge ist zwingend:** Ausweichweg reparieren → messen, ob das Bildmodell läuft
→ Schritt 5 bauen. Beides ist bei der Werkstatt bestellt (`auf-131`, `auf-134`).

### Und eine Frage bleibt doch — eine kleine

**Wie kommt die Skizze herein?** Im Browser auf das Bild gezeichnet, oder als fertige
Datei danebengelegt? Das Zeichnen im Bild ist deutlich mehr Arbeit und deutlich näher an
dem, was Sie beschrieben haben. Solange Punkt 1 bis 3 offen sind, drängt es nicht — aber
es entscheidet, wie Schritt 5 aussieht.

---

## Was heute nicht gemessen ist, und darum nicht behauptet wird

* **Auf einem fremden Rechner ist die Oberfläche nie geöffnet worden.** Ob der Browser
  einer anderen Person dieselbe Seite gleich darstellt: unbekannt.
* **Der Erfolgsmassstab von E4 ist nie geprüft worden.** Keine fremde Person hat diese
  Software je geöffnet.
* **Ohne Grafikkarte gibt es kein KI-Bild.** Der Ein-Klick-Download ist das Ziel; ein
  Rechner ohne Grafikkarte ist damit heute nicht bedient.

---

| Belegstelle | Wo |
|---|---|
| Die sechs Schritte (E4) und der Skizzenmodus (E23) | `docs/ENTSCHEIDE_VISBOX_2026-09-18.md` |
| Der Bau, Sitzung für Sitzung | `docs/sitzungen/`, `docs/PLAN.md` |
| Die Oberfläche und ihre Auflagen | `oberflaeche/LIESMICH.md` |
| Der Bildweg und seine Sperren | `oberflaeche/server.py`, `tests/test_oberflaeche.py` |
