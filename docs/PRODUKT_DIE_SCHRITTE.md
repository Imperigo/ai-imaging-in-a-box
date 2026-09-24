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

## 1 · Der wichtigste Punkt zuerst: wie man eine Software von Grund auf baut

**Owner-Auftrag 22.09.2026, als erster wichtiger Punkt markiert.** Bevor dieses Blatt
sagt, was gebaut ist, steht hier, *wie* gebaut wird — in einem eigenen Dokument, für
einen Architekten geschrieben, nicht für Programmierer:

→ **[`SOFTWARE_VON_GRUND_AUF.md`](SOFTWARE_VON_GRUND_AUF.md)** — zehn Grundkonzepte, jedes
an Visbox erklärt: erst die Frage, dann der Bau · Bibliothek und Oberfläche · Bausteine
und Schnittstellen · fremde Bausteine und Lizenzen · Versionsverwaltung · Prüfen · die
dritte Antwort · gebaut ist nicht eingebaut · Arbeitsteilung · erst zeichnen, dann bauen.
Anhang B der Vertiefungsarbeit.

---

## Wozu die Software da ist — zwei Betriebsarten, nicht eine

**Owner-Entscheid 21.09.2026, und er ist der wichtigste Entscheid auf diesem Blatt:**

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
| 5 | **hineinzeichnen** | **gebaut, rechnet mit Hinweis** | Seit 22.09. lässt sich eine Skizze rechnen, seit 23.09. auch aus der iPad-App, auf ein Bild als Unterlage. Auf dem Vorgabemodell kommt sie gemessen nicht an — das Bild sagt es dazu. Die App ist am Gerät unbestätigt. |
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

### 24.09.2026 (spät) · Was andere Knotensysteme vormachen — Vorlauf für den Render-Knoten

* **Recherchiert:** Figma Weave (alle Hilfe-Artikel), 23 KI-Knotenwerkzeuge, 15
  Render- und Architekturprogramme. Weave selbst liess sich nicht anklicken: Das Figma-Konto
  ist dort nicht verknüpft, und die App sperrt diesen Rechner.
* **Der wichtigste Befund:** Kein Werkzeug prüft, ob das Bild zum Gebäude passt. Alle haben
  einen Regler für Treue, keines ein Urteil. Genau das kann unser Render-Knoten zeigen.
* **Was sich bewährt hat:** ein Knoten vorne, aufklappbar dahinter; Aufwand vor dem Klick;
  Ergebnisse stapeln statt überschreiben; Varianten als Achsen; eine einfache Ansicht, die
  aus dem Graphen entsteht.
* **Offen:** sieben Fragen an den Owner, dann wird der Render-Knoten gezeichnet.

### 24.09.2026 (abends) · Die Knotenansicht bestellt jetzt bei Visbox

* **Das Gebäude der Mappe erscheint in der Knotenansicht**, und der Knopf «Ausführen» ist frei.
* **Eine Bestellung landet bei unserem eigenen Server** und wartet, bis jemand «Freigeben»
  drückt. Erst dann steht sie in der Reihe — eine Maschine gibt sich hier nichts selbst frei.
* **Gerechnet wird mit dem bestehenden Abholer**, ohne zweite Rechenstrecke. Das erste
  echte Bild auf diesem Weg misst die HomeStation (Auftrag 164).
* **Auf der Visbox-Seite steht oben der Knopf «Knotenansicht».**

### 24.09.2026 (später) · Die Knotenansicht von KosmoOrbit ist herübergekommen — und läuft

* **Neue Richtung des Owners (E26):** Statt eine eigene Knotenansicht zu zeichnen, kommt die
  echte aus KosmoOrbit herüber — als Kopie, wird hier bis Februar weiterbearbeitet und geht
  dann zurück.
* **Kopiert, nicht nachgebaut:** 198 Dateien Byte für Byte, jede mit Fingerabdruck. Wo das
  Werkzeug etwas von KosmoOrbit braucht, das nicht mitkommt (der Assistent, die
  Plan-Blätter, der Entwurfskern), steht ein kleiner **Stellvertreter** — 19 Stück, jeder
  sagt im Kopf, dass er einer ist. So bleibt die Rückkehr ein Austausch.
* **Es läuft im Browser:** Knoten aus der Palette legen, der Render-Knoten mit allen
  Einstellungen, der Bildvergleich. 722 Prüfungen des Originals laufen hier grün.
* **Noch nicht angeschlossen:** Der Modell-Knoten sagt «0 Bauteile» — das Gebäude aus der
  Mappe und das Rendern über unseren Server kommen als Nächstes.

### 24.09.2026 · Die Knoten sichtbar machen

* **Die Oberfläche mit den verbundenen Knoten gehört zu KosmoOrbit.** Dort ist Visbox ein
  Knoten unter vielen. Wir haben um Bildschirmfotos gebeten und gefragt, wie weit die acht
  neuen Knoten sind, die am 18.09. beschlossen wurden.
* **Visbox bekommt eine eigene Knotenansicht** ihres festen Ablaufs: Modell, Tiefenbilder,
  KI-Bild, Prüfung, mit Vorschau an jedem Kästchen und Einstellungen in verständlichen
  Namen. Gezeichnet, noch nicht gebaut.

### 23.09.2026 (spät nachts) · Berichtigt: Der Handgriff trägt nicht

* **Die Meldung darunter war zu früh.** Über drei Startwerte und ein zweites Gebäude
  wiederholt, trägt der Gewinn nicht: Er hängt an einem einzigen Startwert eines einzigen
  Körpers. Der Schalter bleibt ein Messinstrument und wird nicht eingebaut.
* **Neu gefunden, und wichtiger:** Beim gegliederten Hochhaus zeichnet das Modell die Tiefe
  **verkehrt herum** — was vorn ist, erscheint hinten. Beim einfachen Quader nicht. Das wird
  jetzt gezielt gemessen.
* **Ein stiller Fehler beim zweiten Bildmodell:** Es lief ohne Führung durch den Prompt, weil
  ein leerer Gegentext die Führung ganz abschaltet. **Behoben** — mit den Werten seiner
  Modellkarte. Das betrifft auch jede Bestellung aus KosmoOrbit ohne Modellangabe; sie
  rechnet jetzt etwa doppelt so lang (angesagt, wird gemessen).
* **Das neuere Steuermodell zeichnet sichtbar viel besser** — ein sauberes Gebäude genau auf
  der Form. Ausgerechnet diese Bilder erklärt unsere Prüfung aber für «nicht messbar». Die
  Prüfung muss das erst lernen; die HomeStation misst, woran es liegt.

### 23.09.2026 (nachts) · Die Tiefe steuert — mit einem Handgriff besser

* **Die HomeStation hat gemessen:** Hebt man das Gebäude in der Tiefenkarte leicht vom
  Hintergrund ab, folgt das KI-Bild der Form deutlich besser — die Deckung steigt von rund
  einem Drittel auf über neun Zehntel. Belegt ist, dass der Gewinn im Bild liegt und nicht
  in der Messung. Die Prüfung besteht trotzdem noch keiner der Läufe.
* **Zwei weitere Hebel werden gemessen:** ob der Gewinn über mehrere Startwerte und ein
  zweites Gebäude trägt, und ob ein neueres Steuermodell desselben Herstellers (frei
  lizenziert) besser führt und das Hineinskizzieren möglich macht.
* **Aufgeräumt:** Elf alte Posten waren längst erledigt und nie abgehakt. Zwei Messblätter
  widersprachen ihren eigenen Antworten — berichtigt.
* **Sicherer:** Ein Renderauftrag konnte die Freigabeprüfung umgehen, wenn er gleich mit
  Token eingestellt wurde. Die Tür ist zu.
* **Die iPad-App bringt ihre Schriften mit** — am Gerät noch unbestätigt.

### 23.09.2026 (spät) · Warum die Form manchmal nicht ankommt — jetzt messbar

* **Zwei Messschalter**, ausgeschaltet, solange niemand sie setzt: Der eine hebt das
  Gebaute in der Tiefenkarte vom Hintergrund ab, der andere dreht die Tiefe für einen
  Versuch um. Ohne sie rechnet alles genau wie vorher — belegt, nicht angenommen.
* **Die HomeStation fährt sechs gezielte Läufe** (`auf-154`, Nachtrag): mit und ohne
  Boden, mit Abstand, umgedreht, kleiner, schwächer. Danach ist bekannt, ob es an unserer
  Aufbereitung liegt oder am Bildmodell.
* **Nebenbei behoben:** Eine Rückrechnung von Grau in Meter lieferte in einem selten
  benutzten Fall Punkte zu nah; ein Schalter ging beim Skizzieren still verloren.

### 23.09.2026 (abends) · Eine ehrliche Lieferauskunft, und eine schlechte Nachricht zum Bild

* **KosmoOrbit erfährt jetzt je Kamera, ob ihr Bild kam.** Bisher stand dort still
  «geliefert», auch wenn Bilder fehlten — ein Feld, das niemand füllte.
* **Ein Fehler, den die HomeStation fand, ist behoben:** Eine Projektmappe auf einem
  anderen Laufwerk fand ihr Gebäudemodell nicht mehr.
* **Ein Lauf, in dem an der Stelle des Gebäudes kein Gebäude kam** — *berichtigt am selben
  Abend:* Das war ein kleiner Quader ohne Boden, bei kleiner Auflösung und schwacher Führung.
  Alle früheren Läufe mit Boden, grösserer Auflösung und voller Führung folgten der Form.
  Der wahrscheinliche Grund: Die Rückkante eines freistehenden Körpers verschwindet in
  unserer Tiefenkarte im Hintergrund. Die HomeStation misst das jetzt gezielt.

### 23.09.2026 · Was angenommen wird und nicht wirkt, wird jetzt gesagt

* **Einstellungen ohne Wirkung werden nicht mehr still geschluckt.** Augenhöhe, Winkel und
  Kameramodus wirken nur, wenn der Standpunkt aus einer Himmelsrichtung kommt. Neben einem
  Standpunkt von Hand werden sie jetzt abgewiesen oder als «wirkungslos» gemeldet.
* **Eine unsinnige Zahl in einer Bestellung** (z. B. «viele» statt einer Zahl) legte bisher
  das ganze Abholen lahm — auch alle anderen Bestellungen. Jetzt bleibt nur diese eine
  liegen, mit einem Satz, warum.
* **Keine Richtung mehr aus Zufall.** Die Prüfung sagt «erwartete Richtung» erst, wenn die
  Zahl deutlich genug ist; vorher schon bei Rauschen.
* **Die App lässt nichts mehr still weg**, was sie nicht lesen kann — sie sagt es.

Nichts davon ändert ein Bild oder ein Urteil; es ändert, was **gesagt** wird.

### 23.09.2026 · Die App ist zusammengesteckt — und wartet auf Ihren Stift

* **Alles hängt zusammen:** Zeichnen, Koppeln, Parken, Senden, Rechnen lassen, Abbrechen,
  Namen geben, Varianten, das Prüfzeichen am Bild. Die ganze App übersetzt auf einem Mac
  **ohne eine einzige Warnung**.
* **Neu: «Darauf skizzieren».** Ein fertiges Bild wird zur Unterlage unter dem Blatt, man
  zeichnet hinein und lässt neu rechnen. Bis dahin landete jede Skizze aus der App auf Grau,
  weil die App das Bild darunter weder zeigte noch mitschickte.
* **Innenraum-Bestellungen aus KosmoOrbit kommen durch.** Bis heute blieb jede liegen — aus
  zwei Gründen, die man nur am Stück sieht: Das Feld war unbekannt, und die Datei hiess
  anders, als wir sie suchten. Beides behoben; ob drüben ein drittes Hindernis wartet,
  fragt ein Auftrag an KosmoOrbit.
* **Die Entwurfsfläche ist nachgezogen:** Was der Bau brauchte und kein Blatt zeigte, ist
  jetzt gezeichnet. Zwei Stellen tragen das Schild «Owner-Entscheid offen» — dort haben Sie
  das Wort.
* **Geprüft:** 158 absichtliche Fehler über drei Wellen, jeder wurde gefunden.

**Ausprobieren am iPad** können nur Sie — die Anleitung samt Abnahmeblatt liegt in
`docs/VISBOX_IPAD_ERSTE_PROBE.md`. Bis es ausgefüllt zurückkommt, heisst der Stand der App
«gebaut, am Gerät unbestätigt».

### 22.09.2026 · Die iPad-App entsteht — und sie übersetzt auf einem Mac

* **Eine eigene App statt einer Webseite** (Ihr Entscheid). Sie heisst Visbox, wird später
  KosmoSketch, und öffnet sich in Xcode und in Swift Playgrounds.
* **Das Gerüst übersetzt** — geprüft auf einem Mac bei GitHub, weil es hier keinen gibt.
* **Gebaut, aber noch nicht zusammengesteckt:** Zeichnen mit Ebenen, 20 Schritten zurück und
  Doppeltipp-Radierer; Leiste, Prüfzeichen, Vergleich, Varianten, Teilen; Suche im Heimnetz,
  Koppeln mit Zahl, Parken und Nachsenden. Zwei dieser Teile hat die Durchsicht
  zurückgewiesen, sie werden nachgebessert.
* **Der Rechner kann jetzt mehr:** eine Skizze rechnen lassen (mit dem Hinweis, wenn sie
  nicht ankommt), einen Lauf abbrechen, Bilder umbenennen, schnell entwerfen, Varianten.
* **Ein Grundlagenblatt** «Wie man eine Software von Grund auf baut» liegt als erster
  wichtiger Punkt bereit.

**Ausprobieren am iPad** können nur Sie — eine Anleitung folgt, sobald die App fertig
zusammengesteckt ist.

### 22.09.2026 · Was angenommen wird, muss auch wirken

* **Der Bildausschnitt steht nur noch dort im Bericht, wo er gewirkt hat.** Vorher stand er
  überall, auch wo er nichts tat — der Bericht behauptete eine Rahmung, die es nie gab.
* **Himmelsrichtung und angeklickter Standpunkt zugleich werden abgelehnt,** statt dass
  still einer gewinnt. Die Oberfläche muss beim Anklicken die Richtung löschen — beauftragt.
* **«Vorne und hinten vertauscht» kommt nur noch bei einem deutlichen Wert.** Sonst heisst
  es ehrlich «kein messbarer Zusammenhang».
* **Das Programm weiss jetzt, welches Bildmodell ein Ausgangsbild annimmt** — und jedes
  Urteil darüber muss den Messauftrag nennen, sonst startet es gar nicht.

**Eine Frage an Sie:** Auf dem Vorgabemodell kommt eine hineingezeichnete Skizze gemessen
nicht an. Soll das Hineinskizzieren dort gesperrt werden, oder weiter rechnen und den
Vorbehalt anzeigen?

### 22.09.2026 · Warum die Sonne nichts am Bild ändert — und was jetzt drüben ankommt

* **Ihr Entscheid ist eingebaut:** Ein von Hand gesetzter Geländestand heisst jetzt überall
  «nicht geprüft».
* **Die Innenansicht funktioniert über die Mappe** — sofern das Modell als IFC hereinkam.
  Das Programm liest die Räume einmal beim Anlegen. Ob sie am echten Modell an der richtigen
  Stelle liegen, prüft die Werkstatt.
* **Die Sonne kann das Bild heute gar nicht ändern.** Sie wirkt nur auf das
  Blender-Vorschaubild, und unser Bildmodell nimmt kein Vorschaubild an — es sieht nur die
  Tiefenkarte, und Tiefe hat kein Licht. Das ist Bauart, kein Fehler. Der Regler wird das
  künftig dazusagen.
* **Der Bildausschnitt wirkt nur, wenn Sie eine Himmelsrichtung wählen** und keinen
  Standpunkt anklicken. Die Werkstatt hat — auf unsere Bitte hin — mit angeklicktem
  Standpunkt gemessen; darum änderte sich nichts. Unser Fehler im Auftrag.
* **«Vorne und hinten vertauscht» stimmte nicht.** Der Wert lag so nah bei null, dass er
  «kein Zusammenhang» heisst. Das Bild folgt der Tiefenkarte nicht — aber nicht, weil etwas
  umgedreht wäre.
* **Nach KosmoOrbit ging bis heute nur die schlechteste Kamera.** Jetzt spricht jede, bei
  der etwas nicht stimmt. Und ein Punkt, der seit fünf Tagen als erledigt galt, war es nicht:
  Pro Kamera kamen nur Namen an. Zurückgestuft und repariert.

### 22.09.2026 · Vier Stellen, an denen eine Zahl mehr sagte, als gemessen war

* **Ein zweites Bildmodell ist einen Schritt näher.** Das Programm wählte für jedes
  Modell denselben Bauplan. Jetzt nach Modellfamilie. Laden lässt sich das Modell
  trotzdem noch nicht: Wie sein Zusatzordner auf der Werkstattmaschine heisst, ist nicht
  gemessen — gefragt ist es.
* **Am Bild steht jetzt, warum die Prüfung so geurteilt hat — und unter welcher Lizenz es
  entstand.** Bis dahin stand beim Grund immer «leer», weil unter dem falschen Namen
  nachgesehen wurde. Und wo die Prüfung gar nicht urteilen konnte, klang ihr Satz trotzdem
  nach «bestanden»; jetzt steht der Vorbehalt davor.
* **Der Rat des Programms schaltete die Prüfung ab.** Wer den Geländestand setzte, wie
  empfohlen, bekam gar keine Kompositionsprüfung mehr. Behoben.
* **Die Adresse fürs iPad ist jetzt eine, die man eintippen kann.** Vorher stand dort
  «0.0.0.0» — das ist keine Adresse, sondern eine Anweisung an den Rechner.

**Eine Frage an Sie:** Wenn Sie den Geländestand von Hand eingeben — soll das Programm ihm
trauen wie einer Messung, oder soll es dazuschreiben «nicht geprüft»? Heute sagen zwei
Stellen Verschiedenes.

### 22.09.2026 · Sechs Fehler, die niemand sah, weil nichts kaputtging

Sechs der dreizehn Befunde von vorhin sind behoben. Sie hatten alle dieselbe Form: Etwas
wurde gemessen und kam nicht an — oder es kam an und behauptete mehr, als gemessen war.

* **Die Mappe vergass, wie ein Bild entstanden ist.** Bestellt war «aus dem Ausgangsbild
  weiterzeichnen», gerechnet wurde «nur aus dem Text» — und in der gespeicherten Mappe sah
  das Bild danach aus wie jedes andere. Jetzt steht die Abweichung am Bild.
* **Die Prüfung bescheinigte gerade Kanten, die sie nie gemessen hatte.** Fehlte die
  Angabe der Kameraneigung, rechnete sie mit null Grad. Genau auf dem Weg, den Sie nehmen,
  wenn Sie den Standpunkt im Grundriss anklicken. Jetzt heisst es «nicht gemessen».
* **Die Innenansicht ist jetzt bestellbar — aber noch nicht lieferbar.** Räume kennt das
  Programm nur aus einer IFC-Datei, und die Mappe rechnet mit der umgewandelten Datei.
  Wer innen bestellt, bekommt deshalb eine klare Fehlermeldung statt eines falschen
  Aussenbilds. *Lieferbar wird sie, wenn die Mappe die Räume mitführt.*
* **Drei Prüfstände an der Anmeldung prüften nichts.** Man konnte die Tür aufsperren, und
  sie blieben grün. Jetzt klopfen sie wirklich an.

Zwei der sechs Arbeiten hat der zweite Agent zuerst **abgelehnt** — nicht, weil sie falsch
waren, sondern weil sie mehr versprachen, als sie prüften. Beide sind nachgebessert.

**Und einer war meiner:** Der Lizenzentscheid von heute Morgen hat einen Test rot
hinterlassen, weil ich danach nicht alles laufen liess. Behoben, bevor er nach `main` kam.

### 22.09.2026 · Ein einziges leeres Feld legte die ganze Warteschlange lahm

Eine Durchsuchung des ganzen Programms nach sechs bekannten Fehlerarten hat **dreizehn
bestätigte Befunde** gebracht. Der schwerste:

Kommt aus der KosmoOrbit-Warteschlange ein Auftrag, in dem ein Feld ausdrücklich **leer**
steht — was jeder schreibt, der die Vorgabe gelten lassen will —, dann bricht nicht dieser
eine Auftrag ab, sondern **der ganze Durchlauf**. Und weil der kaputte Auftrag danach
weiter als «wartend» dasteht, stolpert jeder folgende Lauf wieder über ihn. Auch unsere
eigene Ablage steht dann still.

> *Ein Auftrag, den wir nicht lesen können, ist ein Mangel an diesem Auftrag — und nicht
> das Ende des Durchgangs.*

**Derselbe Griff zum vierten Mal in zwei Tagen.** Er steht jetzt an einer Stelle je Datei
und nicht mehr an jeder einzelnen.

**Der gefährlichste Fall stürzt gar nicht ab:** Steht das Feld «nur bei freier Karte
rechnen» leer, galt das Sicherheitstor als *im Auftrag abgeschaltet*. Keine Meldung, kein
Fehler — die Grafikkarte hätte gerechnet, obwohl ein fremdes Modell darauf liegt. *Eine
Sperre, die ein leeres Feld aufhebt, ist keine Sperre — und sie fällt nicht auf, weil
nichts kaputtgeht.*

**Und zwei Prüfstände prüften nichts:** Einer erreichte die Stelle gar nicht, die er
bewachen sollte. Der andere suchte eine Textstelle und hat deshalb eine **richtige**
Verbesserung als Fehler gemeldet. Beide ersetzt.

### 22.09.2026 · Die Warnung von vorhin kam bei niemandem an

Eine Stunde nachdem die Warnung gebaut war, hat eine Prüfung gemeldet: **Vier Werkzeuge
sehen sie nicht** — darunter ausgerechnet das, über das die HomeStation ihre Testgebäude
baut. Sie fangen die Ausgabe des Hilfsprogramms ab und werfen sie weg.

Das ist derselbe Fehler wie der, den die Warnung beheben sollte, nur eine Etage tiefer —
und diesmal war er meiner.

> *Eine Auskunft, die nur beim Tippen von Hand erscheint, gibt es für jedes Programm, das
> das Hilfsprogramm aufruft, nicht.*

Jetzt warnt die Funktion selbst, und die beiden Werkzeuge reichen weiter, was ihr
Hilfsprogramm sagt — **alles davon**, nicht nach einem Stichwort gesucht, damit die
nächste Warnung nicht wieder hängenbleibt.

**Und zwei meiner eigenen Prüfungen waren keine:** Die eine zählte eine Textstelle, die es
gar nicht gab, und war deshalb grün. Die andere prüfte nur genau diese eine Warnung,
obwohl der Kommentar «reicht alles durch» versprach. Beide ersetzt durch Prüfungen, die
das Ergebnis ansehen statt den Text.

### 22.09.2026 · Der Widerspruch 0,93 gegen 0,36 ist aufgeklärt — und es war unsere Szene

Zwei Messungen desselben Verfahrens ergaben einmal 0,93 und einmal 0,36. Das sah aus wie
ein Befund über das Verfahren. Es war keiner.

Die HomeStation hat es ohne einen einzigen neuen Bildlauf aufgelöst: **Es sind zwei
verschiedene Gebäude**, und das kleinere nimmt im Bild fast viermal so viel Fläche ein wie
das grössere. Der Messweg war in beiden Fällen buchstabengleich derselbe.

**Warum das so ist:** Das Testgelände unter dem Gebäude wächst mit der **grössten**
Abmessung — und beim hohen Gebäude ist das die Höhe. 15 m hoch ergibt 38 m Wiese bei einem
Grundriss von 12 × 9,5 m. Ein kleiner Turm auf einem grossen Feld, und im Bild ist er
entsprechend klein.

**Das Unangenehme:** Wir wussten es. Es stand seit dem 09.09. im Quelltext, mit einer
Tabelle von sieben gemessenen Zeilen. Gelesen hat es niemand — es ist ein Hinweis an einer
Stelle, an die man nur schaut, wenn man die Antwort schon hat.

> *Ein Vorbehalt im Kommentar ist keine Warnung. Er wird gelesen, wenn man ihn schon kennt.*

**Jetzt sagt das Werkzeug es beim Erzeugen**, mit der Zahl und mit dem Ausweg — und es
sagt es auch dann noch, wenn man angeglichen hat, weil der Umstand bleibt.

**Was offen bleibt, und es wird nicht schöngeredet:** Die unterschiedliche Grösse erklärt
den Abstand **nicht ganz**. Ein Rest bleibt unerklärt und steht als offene Frage da.

### 22.09.2026 · Das iPad verbindet sich mit einer sechsstelligen Zahl

Seit dem 21.09. darf die Oberfläche ins Heimnetz — geschützt mit einem Kennwort aus 32
zufälligen Zeichen. Für ein Kennwort ist das richtig. Zum **ersten Verbinden** auf einem
Tablet ist es unbrauchbar: Niemand tippt 32 Zeichen ab, und wer es doch tut, vertippt sich.

Das ist derselbe Satz, mit dem diese Woche schon der Standpunkt aus dem Eingabefeld in den
Grundriss gewandert ist — *was nur über das Eintippen erreichbar ist, wird nicht benutzt.*
Er galt hier genauso und war übersehen worden.

**Jetzt zeigt die HomeStation beim Start eine sechsstellige Zahl.** Das iPad tippt sie
einmal ein und bekommt dafür das richtige Kennwort, das es von da an selbst aufbewahrt.

Sechs Stellen sind nicht viel, und darum hängt die Zahl an drei Auflagen:

* **zehn Minuten** — gerechnet auf einer Uhr, die sich nicht stellen lässt;
* **fünf Versuche** — danach ist sie tot, nicht «kurz gesperrt»;
* **ein Gerät** — nach dem ersten Verbinden verbraucht.

Für ein zweites Gerät wird neu gestartet, und das verlangt jemanden am Rechner. Das ist
die eigentliche Sicherung.

**Wer daneben tippt, hört auf dem iPad immer denselben Satz.** Der genaue Grund — falsch,
abgelaufen, aufgebraucht — steht im Fenster am Rechner, also vor dem Menschen, der etwas
daran ändern kann. *Wer beim Raten erfährt, warum er daneben lag, rät beim nächsten Mal
besser.*

**Was das nicht löst:** wie das iPad die **Adresse** des Rechners findet. Die muss heute
noch einmal eingegeben werden. Die Zahl löst das Kennwort, nicht das Finden.

### 22.09.2026 · Zwei Geräte an derselben Mappe löschen sich nicht mehr gegenseitig

Aus dem iPad-Entwurf blieb eine Frage offen: Was passiert, wenn das iPad und der Rechner
gleichzeitig an derselben Mappe arbeiten? Die Antwort war unbequem — **es war gar nicht
bedacht.** Wer zuletzt speicherte, gewann; die Arbeit des anderen war weg, ohne Meldung
und ohne Spur.

Das ist dieselbe Sache wie die zwei gleichzeitigen Rechnungen vom Vortag, nur eine Etage
höher. Zum zweiten Mal in zwei Tagen.

**Jetzt zählt jede Mappe mit, wie oft sie geschrieben wurde.** Wer von einem älteren Stand
kommt, bekommt eine Absage statt eines stillen Überschreibens — und kann die Mappe neu
öffnen, seine Änderung darauf wiederholen und speichern. Niemand verliert etwas.

Bewusst **keine Uhrzeit**, sondern eine Zählung: Zwei Geräte haben zwei Uhren, und eine
davon geht falsch.

**Eine Regel ist dabei entstanden, und sie gilt weiter:**

> **Wiederholen darf, was hinzufügt. Was ersetzt, muss fragen.**

Eine abgelegte Skizze *kommt dazu* — die wiederholt das Programm von selbst, und danach
steht beides da. Eine geänderte Einstellung *ersetzt* — die wird gemeldet, denn sie
stillschweigend zu wiederholen hiesse, die Einstellung des anderen wegzuwerfen.

Und was die Sperre **nicht** kann, steht ausdrücklich dabei: Zwei Geräte, die in derselben
Millisekunde schreiben, fängt sie nicht. Sie fängt den Fall, der wirklich vorkommt — zwei
Geräte, Minuten auseinander.

### 22.09.2026 · Das Warnzeichen ist jetzt lesbar — und der Rechner passt darauf auf

Das Rot für «durchgefallen» war auf dem dunklen Grund zu dunkel: 4.06, nötig sind 4.5.
Ausgerechnet die eine Aussage, die niemand übersehen darf, war von allen dreien die am
schlechtesten lesbare. Jetzt steht dort derselbe hellere Wert wie im iPad-Entwurf — eine
Bedeutung, eine Farbe.

**Meine eigene Zahl von gestern war falsch.** Ich hatte «3.3» geschrieben, ohne es
nachzurechnen, und sie ist in vier Dokumente gewandert. Der Befund stimmt, die Zahl
stimmte nicht. *Eine Zahl, die niemand nachgerechnet hat, ist eine Behauptung mit
Nachkommastelle.* Überall berichtigt.

**Neu passt ein Rechner darauf auf.** Er liest die Farben aus der Oberfläche selbst und
rechnet bei jedem Testlauf nach, ob sich jede Schriftfarbe von ihrem Untergrund abhebt.
Wer morgen eine vierte farbige Aussage einführt, bekommt die Prüfung geschenkt.

### 22.09.2026 · Und dabei fiel etwas auf, wonach niemand gesucht hat

Der dunkle Streifen, auf dem das Prüfzeichen steht, war **halbdurchsichtig**. Über einem
dunklen Bild ist das schön. Über einem **hellen** Bild — Himmel, weisser Render, Schnee —
hellt er so weit auf, dass **alle vier** farbigen Aussagen unlesbar werden.

Das ist schlimmer als die erste Sache, denn es trifft alle drei Antworten auf einmal, und
zwar genau dort, wo das Zeichen sitzt: auf dem Bild.

> *Ein Abzeichen, dessen Lesbarkeit vom Bild abhängt, auf dem es sitzt, ist auf dem hellen
> Bild keines.*

Der Streifen deckt jetzt zu 94 %. Man sieht noch, dass ein Bild darunter liegt, und im
schlechtesten Fall bleibt genug Abstand. Die iPad-Blätter sind mitgezogen.

Gefunden hat das **nicht das Nachdenken, sondern die Bauform der Prüfung**: Sie rechnet
über alle Untergründe, nicht über die, an die jemand gedacht hat.

### 21.09.2026 · Der ganze Weg war gesperrt — von einer Zahl, die niemand mitgab

Die HomeStation hat sechs Aufträge beantwortet, und einer davon hat den wichtigsten
Befund seit Tagen gebracht: **Kein Lauf kam bis zum Bild.** Auf zwei ganz verschiedenen
Wegen brach er an derselben Stelle ab, mit demselben Satz.

**Was los war, in einfachen Worten:** Bevor gerechnet wird, prüft das Programm, ob das
Modell eine plausible Grösse hat — ein Haus, das versehentlich in Millimetern statt Metern
steht, soll auffallen, *bevor* die Grafikkarte eine Stunde rechnet. Diese Prüfung braucht
die Ausdehnung des Modells. Und die verlangte sie vom Aufrufer, statt sie aus der Datei zu
lesen, in der sie steht. Wer eine Datei vorlegt und ihre Masse nicht auswendig kennt, kam
nicht durch.

*Eine Angabe, die das Programm selbst ausrechnen kann, darf es nicht verlangen.*

Repariert; das Programm liest die Ausdehnung jetzt aus der Datei. Eine Datei, die es
nicht lesen kann, wird weiterhin abgelehnt — **es rät nicht.** Fünf Wächter halten das
fest, und drei Gegenproben belegen, dass sie fallen, wenn man den Fehler zurücklegt.

**Zwei kleinere aus demselben Stapel:**

* Zwei Auskunftsfelder, die sagen, *was bestellt war* und *was wirklich gerechnet wurde*,
  wurden gebaut, begründet — und eine Funktion vor dem Leser weggeworfen. Sie kommen
  jetzt an. Und eine Abweichung steht **vorne** statt als Hinweis Nummer sechzehn.
* Eine Beschreibung behauptete zwei Rückgabewerte, wo drei kamen. Die HomeStation ist
  daran gescheitert, als sie genau die Stelle prüfen wollte, für die sie gebaut ist.

### 21.09.2026 · Und eine unbequeme Nachricht zum Entwurfsmodus

Das Modell, auf das die Hoffnung fürs Hineinskizzieren lag (`qwen-image-edit-2511`),
**nimmt kein Eingangsbild an**, solange eine Tiefenkarte mitgeschickt wird: Drei Läufe mit
drei verschiedenen Bildern ergaben **dasselbe** Bild, bitgenau. Die Tiefenkarte belegt den
einzigen Bildeingang.

Das ist dieselbe Falle wie am 18.08.2026, nur bei einem anderen Modell — und die
Tiefenkarte ist im Auftrag heute Pflicht.

**Berichtigung am 22.09.2026, und sie ändert die Lage:** Wir hatten daraus geschrieben,
die Bildstrecke habe «kein Modell, das eine Skizze annimmt». Das ist zu stark. Sie hat
**kein gemessenes**. Nachgesehen in der eigenen Modellliste: **Drei Einträge sind nie
geprüft worden**, und alle drei haben einen eigenen, getrennten Steuereingang für die
Tiefe — also genau die Bauform, bei der der Bildeingang für die Skizze frei bleibt.

*Ein «geht nicht», das aus zwei Messungen auf acht Einträge schliesst, ist keine Messung
mehr, sondern eine Vermutung mit Beleg-Anstrich.*

Die Prüfung ist billig: Für den ersten Teil muss kein einziger Rechenschritt laufen — man
sieht der geladenen Software an, welche Eingänge sie kennt. Als Auftrag abgelegt
(`auf-20260922-138`).

Offen bleibt es trotzdem, und es entscheidet mehr als jede Bedienfrage.

### 21.09.2026 · Zwanzig Bedienfragen beantwortet — und die zwei Geräte werden eines

Der Entwurf stellte zwanzig Fragen, und sie sind alle beantwortet. Sie stehen mit
Begründung in `docs/ENTSCHEIDE_IPAD_2026-09-21.md`. Was sich dadurch am Entwurf geändert
hat:

* **Hochformat gleichberechtigt.** Es gibt jetzt ein zweites Blatt der Zeichenfläche, bei
  dem die Werkzeuge unten in Daumenreichweite liegen. Gleicher Inhalt, andere Anordnung.
* **Zwei Radierer** statt einem: einer nimmt ganze Striche weg, einer wischt flächig.
* **Mehrere Ebenen**, jede eine Variante — und daraus folgt eine Regel, die vorher keine
  war: **gerechnet wird, was sichtbar ist.** Eine ausgeblendete Ebene geht nicht mit.
* **Wischregler** neben dem Nebeneinander: zwei Bilder deckungsgleich übereinander, ein
  Strich zum Schieben. Der Unterschied zeigt sich an der Kante statt im Hin-und-Her-Blick.
* **Nie auf dem iPad rechnen.** Ist die HomeStation aus, wird die Skizze geparkt und von
  selbst nachgeschickt. Ein Ort, ein Ergebnis — sonst wären zwei Bilder nicht vergleichbar.

### 21.09.2026 · Ein Faden zwischen iPad und Rechner

Dazu kam der Wunsch, dass die beiden Geräte **als ein Werkzeug wirken** und das Senden
einer Skizze als Bewegung beginnt und drüben weitergeht.

Der Entwurf dafür steht auf zwei neuen Blättern: dem Faden selbst (fünf Augenblicke vom
Ablegen bis zum Rückweg) und der HomeStation am Rechner, auf der die Skizze ankommt.

Die Grundidee ist ein Satz: **Ein Gegenstand, ein Weg.** Die Skizze verschwindet nicht
hier und erscheint dort, sondern reist — als dieselbe Marke, gleiche Farbe, gleiche Form.
Kommt das Bild zurück, legt es sich genau an die Stelle, von der die Skizze kam.

**Und die Bewegung darf nicht mehr behaupten, als sie weiss** — das ist dieselbe Lehre wie
beim Fortschrittsbalken, eine Etage weiter:

* Bewegt sich etwas, ist etwas unterwegs.
* Gleichmässig läuft nur, was gezählt wird. Reines Warten *atmet* an Ort und Stelle.
* Die Animation endet nie vor der Ankunft. *Sie endet früher, behauptet sie eine Ankunft.*
* Reisst die Verbindung, fällt die Marke zurück aufs iPad. Sie verschwindet nie in der
  Mitte.

Wer Bewegung am Gerät abgestellt hat, bekommt denselben Weg ohne Bewegung.

### 21.09.2026 · Die iPad-Oberfläche liegt als Entwurf vor — acht Blätter

Bisher gab es die Oberfläche **nur als Browserseite**. Jetzt liegt daneben ein
gezeichneter Entwurf für das iPad: acht Blätter, die den ganzen Weg zeigen — Mappe
öffnen, Standpunkt im Grundriss setzen, rechnen lassen, auf dem Bild zeichnen, Skizzen
verwalten, Urteil ansehen, Varianten vergleichen. Dazu ein neuntes Blatt mit den Zeichen
selbst: Farben, Abzeichen, Schriften, Knopfgrössen.

Wichtig an diesem Schritt ist, was er **nicht** ist: Es ist **kein Code**. Es ist die
Vorlage, gegen die Code später gebaut wird — und der Ort, an dem Entscheidungen über die
Bedienung fallen, bevor sie teuer werden.

Drei Dinge hält der Entwurf fest, die vorher nur im Text standen:

* **Der Stift ist das Hauptwerkzeug, nicht die Maus.** Die Werkzeugleiste sitzt am
  Bildschirmrand und lässt sich auf die andere Seite legen — eine Hand, die zeichnet,
  liegt auf dem Glas und verdeckt, was darunter ist.
* **Prüfen und Entwerfen sind ein Schalter am selben Bild.** Dieselbe Messung, zwei
  Lesarten: beim Prüfen ein Urteil, beim Entwerfen ein Abstand. Erfundenes Volumen ist
  dort der Zweck und nicht der Fehler.
* **Das Abzeichen sitzt auf dem Bild**, wie in der Browserseite — auch auf dem
  ungeprüften. Kein Zeichen sähe aus wie kein Problem.

**Ein Befund gegen die eigene Oberfläche fiel dabei ab:** Das Rot für «durchgefallen»
(`#c2554f`) erreicht auf dem dunklen Grund nur ein Kontrastverhältnis von 4.06 zu 1 — unter
dem Mindestmass von 4.5 zu 1 für normale Schriftgrösse. Auf kleinen Bildschirmen und bei
Tageslicht ist das schlecht lesbar. Im iPad-Entwurf steht es eine Stufe heller
(`#e2776f`); **in der Browserseite ist es noch nicht geändert** — das ist ein offener
Posten, kein erledigter.

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

### 21.09.2026 · Zwei Rechnungen gleichzeitig verloren eine davon — lautlos

**Der unangenehmste Fund des Tages**, und er betrifft genau das, was Sie vorhaben: iPad
und Rechner am selben Projekt.

Starten zwei Rechnungen gleichzeitig auf derselben Mappe, **melden beide Erfolg** — und
danach steht nur **eine** in der Mappe. Die andere ist weg. Ohne Fehlermeldung, ohne
Spur.

> *Ein Fehlschlag, der wie ein Erfolg aussieht, wird nicht gefunden — er wird geglaubt.*

**Repariert:** Die Mappe wird für die Dauer einer Rechnung gesperrt. Ein zweiter Versuch
bekommt jetzt einen Satz statt eines Verlusts — mit der Angabe, seit wann der erste läuft.

Und die Sperre blockiert nicht ewig: Stürzt eine Rechnung ab, gibt sie nach vier Stunden
von selbst frei. *Eine Sperre, die man nur von Hand lösen kann, wird von Hand gelöscht —
auch dann, wenn sie gerade zu Recht steht.*

### 21.09.2026 · Jeder Klick rechnete alles neu — jetzt nicht mehr

Nachdem der Pfadfehler gefunden war, habe ich gezielt nach weiteren Stellen dieser Art
gesucht. Zwei Sondierungen gaben Entwarnung (Leerzeichen, Umlaute und lange Namen in
Pfaden halten überall). **Die dritte nicht.**

**Wer zweimal auf «Rechnen» klickte, wartete zweimal auf Blender** — auch wenn sich nichts
geändert hatte. Die Software hat einen Zwischenspeicher, der genau das verhindert; er ist
gebaut, durch drei Beweise belegt — und auf dem Weg, den das Produkt geht, war er **nicht
eingeschaltet**.

Jetzt ist er es. Gemessen danach:

| Was Sie tun | Was gerechnet wird |
|---|---|
| Zweimal «Rechnen» ohne Änderung | **nichts** von Blender oder dem Bild — nur das Urteil |
| Nur den Text ändern | das **Bild**, nicht die Geometrie |
| Das Modell austauschen | alles, und das ist richtig so |

Der Speicher liegt **in der Mappe**. Wer sie auf einen Stick kopiert, nimmt ihn mit.

**Ausserdem:** Dieselbe Sondierung zeigte, dass dreimal «Rechnen» dreimal denselben
Bildnamen in die Mappe schrieb. *Eine Liste von Bildern, in der dieselbe Datei dreimal
steht, ist keine Liste von Bildern — sie ist eine Liste von Klicks.* Jetzt steht jedes
Bild einmal da; die Läufe werden weiterhin alle gezählt.

### 21.09.2026 · Der ganze Weg einmal am Stück — und er war kaputt

**Die schlechteste Nachricht dieses Tages, und sie ist rechtzeitig gekommen.**

Ich habe einen Beweis gebaut, der den Weg fährt, den **Sie** gehen würden: Modelldatei
hineingeben → Mappe anlegen → rechnen → Mappe morgen wieder öffnen. Bisher war jede
einzelne Stufe geprüft, der ganze Weg am Stück aber nie.

**Er fiel beim ersten Lauf um.** Jede Mappe verlor beim Speichern den Pfad zu ihrem
Modell. Beim nächsten Öffnen hätte dort gestanden: «Modell fehlt» — und weiterrechnen wäre
unmöglich gewesen.

**Der Grund ist eine unserer eigenen Regeln.** Dieses Repository ist öffentlich, darum
wird beim Speichern Ihr Benutzername aus allen Pfaden entfernt. Genau das machte die Pfade
unbrauchbar. Und dasselbe traf **die Bilder**: Die Oberfläche hätte nie ein einziges
echtes Bild angezeigt.

**Warum es niemandem aufgefallen ist:** Alle automatischen Prüfungen laufen in einem
Ordner ohne Benutzernamen. Dort funktionierte alles.

**Repariert, und zwar besser als vorher:** Die Mappe merkt sich ihre Dateien jetzt
*relativ* — «eine Ebene höher, dann haus.ifc» statt des ganzen Wegs. Kein Benutzername,
und als Nebeneffekt lässt sich eine Mappe jetzt **verschieben**: Kopieren Sie sie samt
Modell auf einen Stick, funktioniert sie dort weiter.

> *Zum dritten Mal in diesem Projekt sass der Fehler genau dort, wo die Prüfung aufhört
> und die Wirklichkeit anfängt.*

**Was noch fehlt:** Der Beweis läuft hier ohne Grafikkarte, also mit Platzhaltern. Er
belegt die fünf Stufen, **nicht das Bild**. Auf der Werkstattmaschine läuft derselbe
Befehl mit echtem Blender und echter Grafikkarte — das ist bestellt und ist die Marke vom
15. November.

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
| **1** | **Die App auf dem iPad ausprobieren** | Das kann nur **Sie** — hier gibt es kein iPad und keinen Stift. Anleitung und Abnahmeblatt: `docs/VISBOX_IPAD_ERSTE_PROBE.md`. |
| **2** | **Die drei Messungen der Werkstatt** | Sie entscheiden am **15.10.**, ob der Entwurfsmodus gebaut oder gestrichen wird. Bestellt, liegen dort. |
| **3** | **Kapitel 6 nachziehen** | Die Messungen bleiben, ihr Geltungsbereich hat sich geändert: Sie bedienen eine von zwei Betriebsarten statt der einzigen. |

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

## Der Terminplan — rückwärts gerechnet von Ende Januar 2027

**Owner-Angabe 21.09.2026: «bis Ende Januar ca. soll fertig sein.»** Damit ist der Plan
keine Absichtserklärung mehr, sondern eine Rechnung.

**Von heute bis zum 31.01.2027 sind es 19 Wochen.** Davon gehören die letzten sechs
**Ihnen** — Sie schreiben die Arbeit, und ein Text entsteht nicht neben einer Baustelle.

> *Eine Software, die im Januar noch wächst, ist im Januar nicht gemessen — und was nicht
> gemessen ist, steht nicht in der Arbeit.*

| Bis wann | Was fertig sein muss | Wenn nicht |
|---|---|---|
| **15.10.2026**<br>in 3½ Wochen | Die drei Messungen, an denen alles hängt: läuft der Ausweichweg (`auf-131`), läuft ein Modell mit Eingangsbild (`auf-134`), und wie weit reicht das tragende Ergebnis (`auf-128`). | Der Entwurfsmodus wird **gestrichen** — nicht später, sondern dann. |
| **15.11.2026**<br>in 8 Wochen | Der durchgehende Weg ist **belegt**: ein Lauf vom Modell bis zum geprüften Bild, auf der Werkstattmaschine, dokumentiert. Entwurfsmodus gebaut oder gestrichen. | Die Arbeit zeigt einen Prototyp ohne durchgehenden Beleg. Das wäre der teuerste Verlust. |
| **15.12.2026**<br>in 12 Wochen | **Software eingefroren.** Alle Zahlen, die in der Arbeit stehen sollen, sind gefahren und abgelegt. Lexikon und Protokolle vollständig. | Sie schreiben über etwas, das sich noch ändert. |
| **15.12. – 31.01.**<br>6½ Wochen | **Sie schreiben.** Ich liefere nur noch Belege, rechne Zahlen nach und berichtige. **Kein neuer Code.** | — |

**Der 15. Oktober ist der wichtigste Tag dieser Tabelle**, und zwar nicht wegen dessen,
was dann gebaut ist, sondern wegen der Entscheidung: Bis dahin muss feststehen, ob der
Entwurfsmodus überhaupt möglich ist. *Ein Vorhaben, über das man nicht rechtzeitig
entscheidet, entscheidet sich selbst — meistens zu spät und immer teurer.*

---

## Was wegfällt, und warum

Die **Reihenfolge** steht hier, damit sie nicht im Januar unter Zeitdruck entsteht.

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

**Und wo die Linie bei Ende Januar liegt:**

**Punkt 1 (Rückweg ins Modell) ist gestrichen.** Er hängt an einem fremden Team und einem
Vertrag, den es nicht gibt. In 19 Wochen, von denen 6 dem Schreiben gehören, ist das nicht
zu verhandeln und zu bauen. Er bleibt als **Ausblick** in der Arbeit stehen — das ist sein
richtiger Platz.

**Punkt 2 (eigene iPad-App) ist gestrichen.** Die Seite im Browser ist die Antwort.

**Punkt 3 (Entwurfsmodus) steht auf der Kippe**, und die Entscheidung fällt am
**15.10.2026**. Er hängt an zwei Messungen, die wir nicht selbst fahren können.

**Punkt 4 (Bequemlichkeit) ist gestrichen**, ausser dort, wo etwas ohne sie unbedienbar
wäre.

**Alles in der zweiten Tabelle bleibt.** Es ist zusammen weniger Arbeit als Punkt 3 allein,
und es ist das, worüber die Arbeit handelt.

---

## Was heute nicht gemessen ist, und darum nicht behauptet wird

* **Auf einem fremden Rechner ist die Oberfläche nie geöffnet worden.** Ob der Browser
  einer anderen Person dieselbe Seite gleich darstellt: unbekannt.
* **Das Abgabedatum ist «Ende Januar 2027, ca.»** — mit dem «ca.». Der Plan oben rechnet
  mit dem **31.01.2027**; verschiebt sich der Tag um eine Woche, verschieben sich alle
  Marken mit. Die Reihenfolge ändert sich dadurch nicht.
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
