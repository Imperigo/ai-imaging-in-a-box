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
| 2 | **Kamera** | **gebaut und bedienbar** | Seit 21.09. klicken Sie Standpunkt und Blickrichtung im Grundriss an. |
| 3 | **Blender-Render** | **gebaut** | Läuft nur, wo Blender liegt — also bis heute nur auf der Werkstattmaschine. |
| 4 | **KI-Bild** | **gebaut** | Braucht eine Grafikkarte. Der Vorgabeweg lief dort drei Wochen lang gar nicht (repariert 21.09.). |
| 5 | **hineinzeichnen** | **halb gebaut** | Zeichnen geht seit 21.09. Rechnen nicht — unser Modell nimmt kein Bild an. |
| 6 | **neues Bild** | **nicht gebaut** | Folgt aus 5. |
| 7 | **zurück ins Modell** (Kosmo baut nach) | **nicht gebaut** | Neu seit 21.09. Braucht die Differenz aus Schritt 6. |

**Dazu, quer über alle Schritte:**

| Teil | Stand | Bemerkung |
|---|---|---|
| **Die Mappe** (ein Projekt öffnen, morgen dort weitermachen) | gebaut | Merkt sich auch, ob das Modell seither verändert wurde. |
| **Die Oberfläche** | gebaut, wächst | Läuft auf dem eigenen Rechner, ohne Netz, ohne fremde Bausteine. |
| **Der Knotenbaum** | bedienbar | Zeigt, was gerechnet würde, und lässt die Werte ändern. Knoten hinzufügen geht nicht. |
| **Die Bildanzeige** | **neu am 21.09.2026** | Zeigt die Bilder selbst, mit dem Prüfvermerk **auf** dem Bild. |
| **Die Zeichenfläche** | **neu am 21.09.2026** | Mit dem Stift ins Bild zeichnen, ablegen. Für iPad gebaut. |
| **Zusehen beim Rechnen** | **neu am 21.09.2026** | Die Seite bleibt bedienbar und zeigt, wo der Lauf steht. |
| **Der Grundriss** | **neu am 21.09.2026** | Standpunkt und Blickziel anklicken statt Zahlen tippen. |
| **Die Anmeldung** | **neu am 21.09.2026** | Die Fläche darf ins Heimnetz — nur mit Kennwort. |

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

### 21.09.2026 · Der Standpunkt wird angeklickt, nicht getippt

Bisher entschied die Software allein, von wo das Gebäude gezeigt wird. Der Blickpunkt war
zwar einstellbar — aber nur, indem man **drei Zahlen eintippt**. Das ist dasselbe, wie es
gar nicht zu können.

Jetzt zeigt die Oberfläche einen **Grundriss**: das Gebäude von oben, massstäblich, Norden
oben. Erster Klick — hier stehe ich. Zweiter Klick — dorthin sehe ich. Dazu ein Feld für
die Augenhöhe. «Übernehmen» schreibt es in die Einstellungen, und beim nächsten Lauf gilt
es.

**Zwei Kleinigkeiten, die den Unterschied machen:**

* **Gezeichnet wird das Gebäude, nicht das Gelände.** Die Software trennt beides. Ein
  Grundriss, in dem das Haus ein Fleck in einer Wiese ist, lädt zu einem Standpunkt ein,
  der daran vorbeisieht.
* **Das Blickziel liegt auf halber Gebäudehöhe**, nicht am Boden. Wer auf den Boden zielt,
  bekommt ein Bild, in dem das Haus nach hinten kippt.

Wo die Software das Gebäude nicht sicher von der Wiese trennen kann, **zeichnet sie keinen
Grundriss** und sagt warum — statt eine Fläche zu zeigen, die falsch ist.

### 21.09.2026 · Die Oberfläche darf ins Heimnetz — mit Kennwort

Damit Ihr iPad den Rechner erreicht, muss die Oberfläche im Netz hören. Das geht jetzt,
und zwar **nur mit Kennwort**: Wer sie ohne startet, bekommt keinen Server, sondern einen
Satz, der erklärt warum.

So starten Sie sie:

```
python3 oberflaeche/server.py --ordner <projektordner> --im-heimnetz --kennwort-erzeugen
```

Benutzername und Kennwort stehen danach im Fenster. Auf dem iPad rufen Sie die Adresse
auf, die dort steht, und geben beides ein.

**Und der Satz, den ich nicht weglasse:** Das läuft über eine unverschlüsselte Verbindung.
Das Kennwort hält Geräte fern, die zufällig in Ihrem WLAN sind — **nicht jemanden, der
dort mithört.** Für ein Heimnetz ist das vertretbar; in einem fremden WLAN wäre es das
nicht.

### 21.09.2026 · Man kann dem Lauf zusehen — und die Anzeige behauptet nichts

Bisher klickten Sie auf «Rechnen», und dann stand die Seite still. Minutenlang. **Das sieht
aus wie ein Absturz**, auch wenn alles in Ordnung ist.

Jetzt läuft die Rechnung im Hintergrund, und die Seite zeigt, wo sie steht: welcher Schritt
von wie vielen, wie lange er schon läuft, und was schon erledigt ist — samt dem Hinweis,
wenn etwas aus dem Zwischenspeicher kam statt neu gerechnet zu werden.

**Das Wichtigste daran ist aber, was die Anzeige *nicht* tut.** Es gibt zwei ganz
verschiedene Auskünfte, und sie sehen hier verschieden aus:

* **Gezählt.** Beim Bild werden die Rechenschritte wirklich mitgezählt, und es steht
  vorher fest, wie viele es werden. Nur hier gibt es einen Fortschrittsbalken.
* **Lebt.** Beim Blender-Lauf ist nur erkennbar, dass er noch arbeitet. Wie weit er ist,
  weiss niemand. Dort steht ein blinkender Punkt, eine Dauer — und **kein Balken**.

> *Ein erfundener Balken ist dasselbe wie ein grünes Prüfzeichen an einem ungeprüften
> Bild: Er sieht aus wie eine Auskunft und ist geraten.*

Und es gibt **keinen** Prozentsatz über den ganzen Lauf. Dafür müsste man wissen, wie lange
die einzelnen Schritte im Verhältnis dauern — das weiss niemand.

### 21.09.2026 · Zeichnen geht — und zwar für den Stift, nicht für die Maus

**Sie sollen es auf dem iPad ausprobieren können, und dafür musste es zuerst existieren.**

In der Oberfläche steht jetzt eine Zeichenfläche: Bild auswählen, mit dem Stift
hineinzeichnen, Radierer, Strichstärke, «in die Mappe legen». Die Zeichnung landet als
eigener Eintrag im Projekt — mit dem Bild, auf das gezeichnet wurde, und dem Vermerk, dass
noch nichts daraus gerechnet ist.

**Drei Dinge daran sind bewusst so und nicht anders:**

* **Der Druck des Stifts kommt an**, und die Fläche sagt Ihnen, ob er ankommt. Steht dort
  «kein Druck gemeldet», hat Ihr Gerät keinen geliefert — dann liegt es nicht an der
  Software. *Eine Zeichenfläche, die das nicht sagt, lässt Sie raten, warum der Strich
  überall gleich dick ist.*
* **Keine erfundene Druckkurve.** Wie sich ein echter Stift auf einem echten Gerät
  verhält, hat hier niemand gemessen. Eine ausgedachte Kurve sähe nach Handwerk aus und
  wäre geraten.
* **Jede abgelegte Zeichnung trägt den Satz, dass sie NICHT gerechnet wurde.** Sie geht
  nicht verloren — sie wartet. *Eine Bestellung, die angenommen und nicht ausgeliefert
  wird, ist schlimmer als eine abgelehnte: Die Ablehnung sieht man.*

**Was Sie dafür tun müssten:** Das iPad muss den Rechner erreichen. Heute hört die Fläche
nur auf dem Rechner selbst — mit Absicht, denn dort liegen Ihre Gebäudemodelle. Das zu
öffnen ist ein kleiner Handgriff und Ihre Entscheidung, nicht meine.

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
| **1** | **Die Zeichenfläche auf dem iPad ausprobieren** | Das kann nur **Sie** — hier gibt es kein iPad und keinen Stift. Es ist die einzige offene Frage, die kein Worker beantworten kann. Alles dafür ist jetzt gebaut. |
| **2** | **Das Abgabedatum nennen** | Sie haben «früher als Februar» gesagt. Ohne das Datum kann ich nicht sagen, was wegfällt — nur, in welcher Reihenfolge. |
| **3** | **Schritt 5 fertig machen** | Zeichnen geht. Rechnen ist **hardwareseitig blockiert** — siehe unten. |

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

## Wenn die Zeit knapper wird — was zuerst wegfällt, und warum

**Sie haben am 21.09.2026 gesagt: früher als Ende Februar 2027.** Das Datum kenne ich
nicht, und ohne Datum kann ich nicht sagen, *wie viel* wegfällt. Die **Reihenfolge** kann
ich sagen, und sie steht hier, damit sie nicht im Januar unter Zeitdruck entsteht.

> *Eine Streichliste, die man erst macht, wenn es eng wird, streicht das, woran man
> gerade zuletzt gearbeitet hat.*

**Fällt zuerst — und tut am wenigsten weh:**

| | Was | Warum es verzichtbar ist |
|---|---|---|
| **1** | **Schritt 7, der Rückweg ins Modell** | Er hängt an einem fremden Team und einem Vertrag, den es noch nicht gibt. Das ist Aufwand, den wir nicht allein steuern — und die Arbeit steht auch ohne ihn. |
| **2** | **Eine eigene iPad-App** | Die Seite im Browser ist die Antwort, bis gemessen ist, dass sie nicht genügt. Eine App wäre ein zweiter Quelltext für dieselbe Fähigkeit. |
| **3** | **Schritt 5 und 6, der Entwurfsmodus** | Er ist heute hardwareseitig blockiert. Bleibt er es, fällt er von selbst — und die Arbeit verliert eine Anwendung, nicht ihr Ergebnis. |
| **4** | **Weitere Bequemlichkeit in der Oberfläche** | Warteschlange für zwei Läufe, feinere Anzeigen, mehr Bedienelemente. Angenehm, trägt nichts. |

**Fällt nicht — und zwar auch dann nicht, wenn es eng wird:**

| | Was | Warum es bleiben muss |
|---|---|---|
| **A** | **Die Messung und ihr Geltungsbereich** | Das ist die Arbeit. Ein Prototyp ohne sie wäre ein Softwareprojekt, kein Forschungsbeitrag. |
| **B** | **Der Widerspruch 0,93 gegen 0,36** (`auf-128`) | Er sagt, **wie weit** das tragende Ergebnis reicht. Ungeklärt müsste die Arbeit ihr eigenes Hauptergebnis auf «die Szenen eines Tages» einschränken. |
| **C** | **Der durchgehende Weg: Modell rein → Bild raus** | Ohne ihn gibt es nichts zu messen und nichts zu zeigen. |
| **D** | **Die Protokolle und das Lexikon** | Sie sind Anhang der Arbeit und entstehen nur laufend. Nachträglich sind sie nicht herstellbar. |

**Was das praktisch heisst, wenn Sie mir das Datum nennen:** Ich rechne rückwärts und sage
Ihnen, wo die Linie zwischen der oberen und der unteren Tabelle zu liegen kommt. Nicht
mehr, und nicht weniger.

---

## Was heute nicht gemessen ist, und darum nicht behauptet wird

* **Auf einem fremden Rechner ist die Oberfläche nie geöffnet worden.** Ob der Browser
  einer anderen Person dieselbe Seite gleich darstellt: unbekannt.
* **Das Abgabedatum ist nicht bekannt.** «Früher als Ende Februar 2027» ist die einzige
  Angabe. Jede Planung darunter ist eine **Arbeitsannahme** und steht überall als solche da.
* **Und auf einem iPad erst recht nicht.** Ob sich eine Browserseite dort wie eine
  Zeichen-App *anfühlt*, ist nicht gemessen und von hier aus nicht messbar. Das entscheidet
  kein Schreibtisch, sondern ein Mensch mit einem Stift. **Fällt die Probe durch, ist eine
  eigene App die Antwort** — dann aber mit gemessener Begründung statt mit einer Vermutung.
* **Der Erfolgsmassstab von E4 ist nie geprüft worden.** Keine fremde Person hat diese
  Software je geöffnet.
* **Ohne Grafikkarte gibt es kein KI-Bild.** Der Ein-Klick-Download ist das Ziel; ein
  Rechner ohne Grafikkarte ist damit heute nicht bedient.

---

| Belegstelle | Wo |
|---|---|
| Die Schritte (E4), der Skizzenmodus (E23), das iPad (E24) | `docs/ENTSCHEIDE_VISBOX_2026-09-18.md` |
| Der Bau, Sitzung für Sitzung | `docs/sitzungen/`, `docs/PLAN.md` |
| Die Oberfläche und ihre Auflagen | `oberflaeche/LIESMICH.md` |
| Der Bildweg und seine Sperren | `oberflaeche/server.py`, `tests/test_oberflaeche.py` |
