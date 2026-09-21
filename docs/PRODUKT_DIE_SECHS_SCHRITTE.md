# Visbox — die sechs Schritte, und wie weit jeder gebaut ist

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
| 5 | **hineinzeichnen** | **nicht gebaut** | Hat keinen Weg. Es hängt an einer offenen Frage an den Owner. |
| 6 | **neues Bild** | **nicht gebaut** | Folgt aus 5. |

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

### 21.09.2026 · Ein Lauf sagt jetzt, was er gerechnet hat

Vorher stand im Protokoll «mit Ankerbild gerechnet», während ohne gerechnet wurde.

---

## Was als Nächstes dran ist

| | Schritt | Warum jetzt |
|---|---|---|
| **1** | **Den Standpunkt von Hand wählen** (Schritt 2) | Die Software entscheidet ihn heute allein. Für ein Architekturbild ist der Blickpunkt keine Nebensache. |
| **2** | **Den Lauf in der Fläche starten und zusehen** | Heute rechnet die Fläche, und dann steht sie still. Ein Fortschritt, den niemand sieht, sieht aus wie ein Absturz. |
| **3** | **Schritt 5 «hineinzeichnen»** | Braucht **zuerst eine Antwort des Owners** — siehe unten. |

---

## Die eine Frage, an der Schritt 5 hängt

**Darf die Tiefenkarte wahlweise werden?**

Heute gilt: ohne Tiefenkarte kein Bild. Das ist der Riegel, der verhindert, dass die
Software ein Gebäude erfindet, das im Modell nicht steht — und es ist der Kern dieser
Arbeit.

Schritt 5 («in ein fertiges Bild hineinzeichnen») braucht diesen Weg aber **ohne** neue
Tiefenkarte: Wer einen Menschen in eine fertige Ansicht setzt, hat für den Menschen keine
Geometrie.

Beides gleichzeitig geht nicht. Es ist eine Entscheidung über die Arbeit, nicht über den
Code, und sie liegt beim Owner.

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
| Die sechs Schritte (E4) | `docs/ENTSCHEIDE_VISBOX_2026-09-18.md` |
| Der Bau, Sitzung für Sitzung | `docs/sitzungen/`, `docs/PLAN.md` |
| Die Oberfläche und ihre Auflagen | `oberflaeche/LIESMICH.md` |
| Der Bildweg und seine Sperren | `oberflaeche/server.py`, `tests/test_oberflaeche.py` |
