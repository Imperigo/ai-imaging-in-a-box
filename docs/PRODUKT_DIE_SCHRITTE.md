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
> Bild gezeichnet, für schnelle Variantenstudien. Und wenn ein Bild überzeugt, soll
> versucht werden, es im Modell nachzubauen.*

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
die Übergabe ans Modell.* Ohne sie gäbe es nur ein Bild, und wer nachbaut, müsste raten, was neu ist.

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
| 7 | **zurück ins Modell** (das Modell wird nachgebaut) | **nicht gebaut** | Neu seit 21.09. Braucht die Differenz aus Schritt 6. |

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

### 01.10.2026 (Abend) · Zwei Durchsichten, ein Umentscheid, und es trägt am Heim-PC

* **Durchgesehen, bevor es hinausging:** Zwei Prüfungen fanden echte Fehler — der Server war
  blockiert, solange der Assistent nachdachte; aus dem Vorführmodus kam man nicht zum
  Einrichten; über den Mac gab es einen Umweg zum Kennwort des Heim-PC; und zwischen iPad und
  Mac wäre die Leitung im fremden WLAN unverschlüsselt gewesen. Alles behoben.
* **Umentschieden (Entscheid 63):** Das iPad geht unterwegs selbst über Tailscale zum Heim-PC,
  verschlüsselt. Der Mac holt nur die Zahl zum ersten Koppeln.
* **Am Heim-PC nachgemessen:** Nach dem Rechnen gibt der Server die Grafikkarte frei; während
  der Assistent nachdenkt, antwortet er weiter sofort. Der Assistent versteht 9 von 10 Sätzen.
* **Die Vorführmappe** hat jetzt 9 echte, verschiedene Bilder — eines davon durchgefallen, und
  das bleibt so (Entscheid 64): Die Mappe zeigt, dass die Prüfung ein falsches Bild erkennt.
* **Ehrlich dazu:** Gestartet hat die Apps noch niemand.

### 01.10.2026 (Nachmittag) · Die Mac-App steht — gebaut, übersetzt, noch nie gestartet

* **Gebaut, in vier Teilen gleichzeitig:** die Mac-App mit den vier Startzeilen; der Mac als
  Vermittler fürs iPad (das iPad koppelt sich mit einer eigenen Zahl am Mac, das Kennwort des
  Heim-PC bleibt auf dem Mac); der Vorführmodus mit einer Beispielmappe; der Assistent, der nur
  vorschlägt und erst nach «Anwenden» rechnen lässt.
* **Geprüft:** Alle Proben grün. Die Mac-App lässt sich auf GitHub übersetzen und liegt dort als
  ZIP zum Herunterladen.
* **Ehrlich dazu:** Gestartet hat sie noch niemand. Ob sie am Mac öffnet, sich verbindet und das
  iPad findet, zeigt erst die Probe nach der Abgabe. Die Bilder im Vorführmodus sind noch graue
  Platzhalter; die echten rechnet der Heim-PC (Auftrag 218).

### 01.10.2026 (Mittag) · Der Plan für v0.1.7: zwei Tage Vollbau, dann Abgabe

* **Ziel:** Bis Freitagabend eine Visbox-App für den Mac zum Herunterladen — sie baut beim
  Öffnen die Leitung nach Hause selbst auf, reicht das iPad durch, zeigt vorher gerechnete
  Bilder, wenn der Heim-PC fehlt, und hat einen ersten Assistenten.
* **Wie entschieden:** Zwanzig Fragen an den Owner, zwanzig Antworten (Entscheide 43–62). Drei
  davon betreffen den Auftrags- und Ergebnisvertrag: «nicht festgestellt» beim Lieferstatus soll
  erlaubt sein; die Lizenz von Qwen-2.1 gilt bis v1.0 als offen; Union-2.1 und die Formprüfung bleiben
  bei uns.
* **Bleibt bewusst draussen:** Entwurfsmodus (Entscheid bis 15.10.), Probe am Gerät (erst nach
  der Abgabe, bis Freitag gibt es kein iPad).
* **Plan:** `docs/PLAN_V017_2026-10-01.md`.

### 01.10.2026 (Vormittag) · Die Vorführfassung: was es schon gibt, wird mitbenutzt

* **Befund:** Die Leitung nach Hause (Tailscale) und das Sprachmodell (Qwen3 über Ollama) laufen
  am Heim-PC schon. Visbox benutzt sie mit, statt eigene zu bauen.
* **Gemessen am Heim-PC:** Sprachmodell und Bildmodell passen nicht gleichzeitig auf die
  Grafikkarte; der Wechsel kostet rund 4 Sekunden. Deutsche Werkzeugaufrufe 3 von 3 richtig.
* **Behoben:** Über die Weiterleitung kam jede Anfrage ohne Kennwort durch. Jetzt wird sie ohne
  Kennwort abgewiesen, und das Kennwort übersteht einen Neustart.
* **Lizenz:** Ein GPL-Fund (wireguard-tools) ausdrücklich gemeldet; der gewählte Weg braucht ihn
  nicht.

### 30.09.2026 (Abschluss) · Die neue Steuerung wird nicht Vorgabe — sie tauscht ein Problem gegen ein anderes

* **Ergebnis (96 Bilder, blind):** Beim Hochhaus stehen mit der neuen Fassung 18 von 24 statt
  15 von 24 — besser, aber nicht um die vorher verlangten 20 Punkte. Also bleibt die alte
  Vorgabe.
* **Was sich zeigt:** Die «Gasse» verschwindet ganz, und die unklaren Bilder werden viel
  seltener (15 → 5). Dafür entstehen echte Fehler: Häuser zu hoch oder zu schlank, der flache
  Testbau von vorne oft zu hoch.
* **Bleibt:** Die neue Fassung ist bestellbar, etwa für Hochhäuser. Wie es weitergeht,
  entscheidet der Owner.

### 30.09.2026 (Nachtrag) · Die neue Steuerung läuft — erster Blick ermutigend

* **Eingerichtet:** Der Heim-PC hat die neue Fassung geprüft und ihren Speicher gemessen.
* **Mein Fehler, behoben:** Das Programm fand die gemeinsamen Grundgewichte nicht, weil es sie
  unter dem neuen Namen suchte.
* **Speicher:** Die neue Fassung füllt die Grafikkarte fast ganz. Damit daneben noch etwas
  Platz hat, lagert das Programm Teile aus — ein Bild dauert dann etwa 17 statt 2 Sekunden.
* **Erster Blick (zählt noch nicht):** Mit der alten Fassung wieder die «Gasse», mit der
  neuen ein freistehender Turm genau auf dem Umriss.
* **Weiter:** Der eigentliche Vergleich — 96 Bilder, blind beurteilt, Regel vorher fest.

### 30.09.2026 (spät) · Statt besser prüfen: besser erzeugen

* **Entscheid des Owners:** die Ursache angehen — das Hochhaus soll öfter richtig stehen, statt
  dass eine Prüfung die unklaren Bilder finden muss.
* **Der Hebel:** eine neuere Fassung des Steuermodells, das die Gebäudeform ins Bild bringt.
  Der Heim-PC hatte im September gesehen, dass sie sauberere, freistehende Gebäude zeichnet;
  entschieden wurde damals nicht, weil es keinen Massstab gab. Jetzt gibt es ihn: das blinde
  Auge.
* **Gebaut:** Die neue Fassung ist bestellbar, aber nicht Vorgabe. Der Heim-PC richtet sie ein
  und misst den Speicher; danach folgt der Vergleich mit einer Regel, die schon feststeht.

### 30.09.2026 (Nachtrag) · Die Grenze trägt nicht — und der gute Befund hielt nicht

* **Ergebnis:** An 96 neuen Bildern trägt die vorher festgelegte Grenze nicht. Beim niedrigen
  Testbau knapp ja, beim Hochbau nein.
* **Schwerer:** Das sehr gute Ergebnis der Runde davor hat sich nicht wiederholt. Bei voller
  Steuerung — dem Normalfall — unterscheidet keine Zahl ein stehendes Hochhaus von einem, bei
  dem auch das Auge unsicher ist.
* **Was bleibt:** Deutliche Fehlbilder erkennt die Umrisstreue. Sie bleibt darum Auskunft und
  sortiert weiter unter mehreren Versuchen aus. Ein Urteil «Form steht» gibt es nicht.
* **Offen:** Welcher Weg jetzt — Entscheid des Owners.

### 30.09.2026 (zuletzt) · Eine Zahl folgt dem Auge: die Umrisstreue

* **Ergebnis:** Die Gegenprobe war tauglich — das perfekte Bild besteht sie überall. Mit ihr
  und 72 frischen Bildern folgen zwei Zahlen dem Augenurteil: die Umrisstreue und ihr
  Ausschnitt an der Silhouette. Auch beim hohen Gebäude von vorne, wo die alte Zahl versagte.
* **Eingebaut:** Die Umrisstreue steht jetzt als «Formprüfung» im Bericht jedes gewählten
  Bildes — als Auskunft, ohne Urteil.
* **Vorbehalt:** Die schlechten Bilder der Messung kamen fast alle aus halber Steuerstärke. Im
  Betrieb läuft volle Stärke, und dort ist die Frage «steht oder unklar» schwerer.
* **Weiter:** Eine Grenze (2,0) ist jetzt vorab festgelegt und wird an 96 neuen Bildern
  geprüft. Erst wenn sie trägt, stellt sich die Frage, ob die Prüfung urteilen darf.

### 30.09.2026 (tief in der Nacht) · Erste Messung gegen das Auge: noch keine Zahl besteht

* **Ergebnis:** Nach der Regel, die vorher feststand, folgt keine Zahl dem Auge.
* **Knapp daneben:** Zwei der neuen Messungen (Richtung der Kanten, Ruhe in den Flächen)
  bestehen alles ausser einer Gegenprobe. Diese Gegenprobe war selbst ungeprüft — womöglich
  hätte sie auch ein perfektes Bild nicht bestanden.
* **Eigener Fehler:** Der Auftrag liess 18 Bilder aus der Vorserie wiederholen; sie zählten
  doppelt. Am Urteil ändert das nichts. Nebenbei zeigte sich: Das Auge urteilte bei allen 18
  Wiederholungen gleich.
* **Weiter:** Zuerst wird die Gegenprobe am perfekten Bild geprüft, dann eine frische Reihe
  mit einer neuen, wieder vorher festgelegten Regel gerechnet. Die alten Bilder werden nicht
  nachträglich umbewertet.

### 30.09.2026 (spätnachts) · Das Auge des Heim-PC wird zum Massstab für die Form

* **Warum:** Ob die Gebäudeform im Bild steht, erkennt bisher nur ein Mensch. Keine Zahl konnte
  es verlässlich. Jetzt wird umgekehrt gefragt: Welche Zahl folgt dem Auge?
* **Gebaut:** Drei neue Messungen, die ohne Hilfsmodell nur Bild und Blender-Ebenen lesen: der
  Umriss allein, die Richtung der Kanten und die Ruhe innerhalb jeder Fläche des Gebäudes. Dazu
  ein Werkzeug, das jede Zahl gegen das Augenurteil stellt.
* **Befund dabei, und er ist unangenehm:** An den 88 schon beurteilten Bildern kamen fast alle
  schlechten aus der alten, falschen Rahmung. Jede Zahl sah darum gut aus, weil sie die Rahmung
  erkannte, nicht die Form. Der Heim-PC erzeugt jetzt gezielt schlechte Bilder unter der neuen
  Rahmung (54 Bilder, Regel vorher festgelegt).
* **Noch nicht:** Keine Zahl urteilt. Erst die Messung, dann eine zweite Reihe für eine Schwelle.

### 30.09.2026 (nachts) · Unter mehreren Versuchen wird jetzt nach dem Umriss ausgewählt

* **Bestätigt:** Mit der neuen Rahmung standen am Heim-PC 19 von 36 Bildern richtig (vorher 2).
  Unter den Versuchen eines Bildes wählt die neue Umriss-Messung öfter das richtige als die
  alte Zahl — nach der Regel, die vorher feststand.
* **Umgestellt:** Das behaltene Bild wird jetzt nach dem Umriss gewählt.
* **Vorbehalt:** Der Vorsprung ist knapp und hängt daran, wie man unklare Bilder zählt. Ein Ja
  oder Nein für ein einzelnes Bild liefert auch diese Messung nicht.

### 30.09.2026 (spätabends) · Die Kamera schaut aufs Gebäude, nicht aufs Grundstück

* **Gefunden:** Am Heim-PC füllte das Gebäude oft nur 2 % des Bildes, weil die Kamera das
  ganze Grundstück einrahmte. Das Bildmodell hat so ein Gebäude einfach übermalt.
* **Umgestellt:** Am Heim-PC rahmt die Kamera jetzt das Gebäude (21 % des Bildes). Für
  Bestellungen über die Knotenansicht ist es vorbereitet und wird eingeschaltet, sobald ein Beweislauf
  zeigt, dass die Form dann wirklich hält.
* **Nachtrag, Beweislauf bestanden:** Mit Gebäude-Rahmung stand die Form in 6 von 8 Bildern,
  mit Grundstücks-Rahmung in keinem. Jetzt gilt es auch für Bestellungen über die Knotenansicht.
  **Schlechte Nachricht dazu:** Keine unserer Zahlen erkennt zuverlässig, ob die Form steht —
  das hat das Auge entschieden.
* **Qwen-Image-2.1** taugt auch als Bildbearbeiter nicht; das freie Qwen-Bearbeitungsmodell
  schon eher (hält die Form, erfindet aber die Umgebung).

### 30.09.2026 (abends) · Ein neuer Versuch, die Gebäudeform zu prüfen — ohne Hilfsmodell

* **Neue Messung gebaut:** Sie schaut, ob das erzeugte Bild dort Kanten hat, wo das Gebäude
  seinen Umriss hat. Sie braucht kein Hilfsmodell, das Tiefe schätzt — genau das hatte die
  alten Messungen getäuscht.
* **Die Pflichtproben bestanden:** Eine graue Fläche bekommt 0 (die alte Messung gab ihr
  die Bestnote), Rauschen den Zufallswert. An echten Blender-Bildern passt das richtige Bild
  fast doppelt so gut wie ein falsches.
* **Offen:** Ob das auch an KI-Bildern trennt. Der Heim-PC misst es.
* **Nebenbei repariert:** Die Bearbeitungsmodelle bekommen jetzt das Blender-Bild als
  Vorlage statt der Tiefenkarte — so steht das Haus wenigstens an der richtigen Stelle.

### 30.09.2026 (nachmittags) · Eine Prüfung, die würfelt, entscheidet nicht mehr

* **Schlechte Nachricht vom Heim-PC:** Die Zahl, die seit gestern allein das «Paarurteil»
  trug (ob das Bild das Gebäude an der richtigen Stelle zeigt), trennt gute von schlechten
  Bildern nicht — weder von vorne noch schräg.
* **Entschieden und gebaut:** Sie wird nur noch angezeigt, mit dem Vermerk «nicht geeicht».
  Kein Bild heisst mehr «durchgefallen» oder «bestanden» wegen ihr.
* **Als Nächstes:** eine andere Messung suchen, die wirklich trennt.
* **Qwen-Image-2.1 gemessen:** Es läuft auf der Grafikkarte, aber nur mit Auslagerung, und
  die Gebäudeform kommt nicht an. Als Bildbearbeiter (Stil, Masken) vielleicht brauchbar —
  offen.

### 30.09.2026 (mittags) · Qwen-Image-2.1 kommt ins Produkt — mit offener Lizenz

* **Entschieden (E128):** Das neue Qwen-Bildmodell wird regulär eingebaut, nicht nur zum
  Forschen. Die Lizenz wird vor einer Veröffentlichung gekauft oder das Modell ersetzt.
* **Eingebaut:** Man kann es über die Knotenansicht bestellen; es ist nie Standard, und jedes Ergebnis
  sagt «Lizenz offen», damit niemand es aus Versehen veröffentlicht.
* **Offen:** Der Name und der Vermerk müssen noch in den Auftragsvertrag (Frage ist
  gestellt). Und die eigentliche Frage bleibt: Übernimmt das Modell die Gebäudeform? Der
  Heim-PC misst es gerade.

### 30.09.2026 · Keine Dauerwarnung mehr an Innenbildern, und leere Angaben werden benannt

* **Innenbilder tragen kein Warnzeichen mehr.** Der Satz «Innenansicht bestellt» ist
  eine Auskunft, kein Vorbehalt (Entscheid des Owners). Er steht jetzt in einem Feld für
  Hinweise.
* **Unser Eingang nimmt leere Angaben an und sagt, welche.** Schickt ein Vorgänger zum Beispiel
  «Geometrie: unbekannt», kommt keine unverständliche Fehlermeldung mehr, sondern der Satz, was
  gefehlt hat. Ohne Geometrie entsteht trotzdem kein Auftrag.

### 29.09.2026 (abends) · Ein neues Bildmodell, nur für die Forschung

* **Qwen-Image-2.1 darf jetzt rechnen — aber nur zum Forschen.** Seine Lizenz verbietet den
  Verkauf. Weil ein Verkauf noch fern ist, hat der Owner eine Ausnahme erlaubt.
* **Die Grenzen sind eingebaut, nicht nur aufgeschrieben:** Das Modell lädt nur am Heim-PC
  mit einem eigenen Schalter, ist nie Standard und kann über die Knotenansicht nicht bestellt werden.
  Jedes Bild daraus trägt den Vermerk «nur Forschung».
* **Offen:** Ob es auf der Grafikkarte läuft und ob es die Form des Gebäudes übernimmt. Es
  hat keine eigene Formsteuerung — das ist die eigentliche Frage. Der Heim-PC misst es.

### 29.09.2026 (später) · Die Fragen zum Vertrag sind beantwortet — und es gibt echte Beispiele

* **Alle sechs offenen Fragen zum Auftrags- und Ergebnisvertrag sind beantwortet.** Sie nehmen die vier
  Vorschläge aus der Bildstrecke an, zwei davon mit Bedingungen.
* **Glas:** Die Modellausfuhr soll Glas künftig «deckend mit Durchlass» ausgeben. Unsere Prüfung
  hätte das bis heute als Fehler gemeldet, weil sie nur den alten Weg kannte. Jetzt zählt
  sie beides. **Das war ein echter Fehler bei uns**, gefunden, weil nachgefragt wurde.
* **Zusatzbilder je Ansicht (Tiefe, Material, Schönbild):** Man kann sie jetzt bestellen,
  und sie kommen mit einer Erklärung in Zahlen. Fehlt eines, steht die Ansicht als «nicht
  geliefert» da.
* **Ohne Modellangabe rechnet jetzt das schnelle Modell** — so steht es im Auftragsvertrag.
  Das Ergebnis sagt neu, mit welchem Modell gerechnet wurde.
* **Die Prüf-Auskunft spricht jetzt die Wörter des Vertrags** («gemessen», «nicht gemessen»), damit
  die Anzeige ein ungeprüftes Bild nicht mehr als «durchgefallen» liest.
* **Offen:** Die Beispiele sind mit echtem Blender erzeugt, das KI-Bild und die Prüfung
  darin sind Platzhalter. Den ganz echten Lauf macht der Heim-PC.

### 29.09.2026 · Drei Aufräum-Entscheide, und die Post ist endlich angekommen

* **Unsere Antworten sind zugestellt.** Sie lagen fünf Tage nur bei uns, weil der
  Botengang fehlte.
* **Ein Bildmodell weniger:** Das grosse Qwen-Modell mit eigener Formsteuerung wird nicht
  mehr angeboten. Es hätte 48 GB gebraucht und war nicht sauber geklärt. Damit bleibt ein
  einziges freies Modell mit Formsteuerung, das schnelle Vorgabemodell.
* **Eine Warnung weniger, die grundlos kam:** Die Prüfung am Gebäudeumriss entscheidet nicht
  mehr mit. An echten Bildern hat sie gewürfelt. Sie wird weiter angezeigt.
* **Offen:** Jetzt hängt die Geometrieprüfung an einer einzigen Zahl, und deren Grenze ist
  nicht geeicht. Der Heim-PC misst das.

### 24.09.2026 (abends) · Berichtigt: Die neue Prüfung trennt nicht — sie ist wieder draussen

* **Am Heim-PC gemessen:** An echten Bildern stellt sie das schlechte Bild über alle guten,
  und eine graue Fläche bekommt die Bestnote.
* **Darum wieder herausgenommen**, bevor jemand ihr glaubt. Sie hatte noch nichts
  entschieden; es ist nichts kaputt gegangen.
* **Offen bleibt die Frage** «Wie misst man ein sauberes Bild?». Als Nächstes käme ein Weg
  über die sichtbaren Kanten im Bild statt über die geschätzte Tiefe.

### 24.09.2026 (Nacht auf den 25.) · Eine Prüfung, die saubere Bilder messen kann — im Versuch

* **Das Problem:** Unsere Bildprüfung nannte die besten Bilder «nicht messbar». Sie hielt
  den Boden, den das Bildmodell vor das Haus malt, für einen Fehler, weil unser Modell dort
  nichts hat.
* **Neu gebaut:** eine zweite Messung. Sie schaut nur an den Kanten des Gebäudes, ob «vorne»
  und «hinten» richtig herum stehen. Den Boden lässt sie in Ruhe.
* **Ehrlich dazu:** Die erste Fassung gab einem leeren Grundstück die Bestnote. Die eigenen
  Proben haben das gefunden, bevor es jemand sah. Jetzt stimmt sie auf den Testbildern.
* **Sie entscheidet noch nichts.** Der Heim-PC prüft zuerst an echten Bildern, ob sie gute
  von schlechten trennt.

### 24.09.2026 (Nacht auf den 25.) · Was für das erste echte Bild fehlt

* **Beantwortet, Punkt für Punkt**, mit einem Ergebnisblatt.
* **Ein Demohaus wird angenommen**, wenn keine Render-Voreinstellung gewählt ist. Mit
  Voreinstellung kommt ein Feld mit, das wir nicht lesen, und der Auftrag wird abgewiesen.
* **Ein alter Fehler gefunden:** Die bestellte Sonne stand um 180 Grad verdreht, weil die
  beiden Seiten die Himmelsrichtung von verschiedenen Enden zählten. Behoben. Helligkeit
  und Farbe der Sonne kommen jetzt auch an, allerdings nur im Blender-Bild, nicht im
  KI-Bild.
* **Neu:** Ist auf der Grafikkarte zu wenig Speicher frei, wartet der Auftrag mit Grund,
  statt abzustürzen. Und der Abholer gibt ein Lebenszeichen, damit man sieht, ob er läuft.
* **Offen:** Der Heim-PC misst am echten Gerät nach.

### 24.09.2026 (tief nachts) · Alle drei automatischen Kameras rendern wieder

* **Die Ursache war eine gesetzte Zahl:** Die Kamera durfte der Fassade nie näher als 10 m
  kommen. Bei einem kleinen Bau (8 m) stand sie darum zu weit weg, das Gebäude war zu klein
  im Bild, und unsere eigene Prüfung sperrte zwei der drei Ansichten.
* **Jetzt 3 m.** Alle drei Ansichten füllen das Bild wie verlangt; bei Gebäuden ab 12 m
  ändert sich nichts. Die Prüfung selbst ist nicht gelockert.
* **Nebenbei gefunden und behoben:** Sehr kleine Körper (unter etwa 1,5 m) brachten die
  Rechnung zum Absturz. Jetzt wird die Kamera zurückgenommen und das gesagt.
* **Offen:** Der Heim-PC bestätigt es am echten Bild (Auftrag 169).

### 24.09.2026 (nachts) · Das erste Bild über die Knotenansicht

* **Die HomeStation hat es gemacht:** Knoten verbunden, «Ausführen», «Freigeben» — das Bild
  erscheint am Render-Knoten. Der ganze Weg vom Klick bis zum Bild läuft.
* **Das zweite Bildmodell rechnet jetzt durch**, mit Führung durch den Prompt — aber
  langsam (knapp 6 Minuten je Bild gegen knapp eine mit dem Vorgabemodell).
* **Ein neuer Befund:** Von drei automatischen Kameras wurden zwei nicht gerendert — unsere
  eigene Prüfung fand das Gebäude zu klein im Bild. Das ist jetzt ein offener Posten.
* **Behoben:** Die Probe sagt jetzt vorher, ob der Rechner rechnen kann.

### 24.09.2026 (spät) · Was andere Knotensysteme vormachen — Vorlauf für den Render-Knoten

* **Recherchiert:** Figma Weave (alle Hilfe-Artikel), 23 KI-Knotenwerkzeuge, 15
  Render- und Architekturprogramme. Weave selbst liess sich nicht anklicken: Das Figma-Konto
  ist dort nicht verknüpft, und die App sperrt diesen Rechner.
* **Der wichtigste Befund:** Kein Werkzeug prüft, ob das Bild zum Gebäude passt. Alle haben
  einen Regler für Treue, keines ein Urteil. Genau das kann unser Render-Knoten zeigen.
* **Was sich bewährt hat:** ein Knoten vorne, aufklappbar dahinter; Aufwand vor dem Klick;
  Ergebnisse stapeln statt überschreiben; Varianten als Achsen; eine einfache Ansicht, die
  aus dem Graphen entsteht.
* **Gezeichnet (Blatt 12 und 12b):** der Render-Knoten mit allen Empfehlungen, und daneben die
  sieben Entscheide als Bildpaare — oben die Empfehlung, unten die Alternative. Neu ist ein
  eigener Knoten «Geometrie-Pässe» und das Urteil als eigener Ausgang.
* **Entschieden (E27):** Die Knoten-Oberfläche wird gerade umgebaut — Visbox übernimmt sie,
  wenn sie fertig ist. Fest ist ein Punkt: **das Urteil gehört an den Render-Knoten.** Die
  Blätter gehen als Vorschlag mit.
* **Am Abend:** Drei Knoten-Entwürfe lagen vor, der Owner hat «n1
  Insel-Karte» gewählt — runde Karten mit Fächern, das Bild im Ergebnis. Visbox wartet auf
  den Bau und holt ihn danach. Das Urteil fehlt im Entwurf
  noch und ist nachgefordert.

### 24.09.2026 (abends) · Die Knotenansicht bestellt jetzt bei Visbox

* **Das Gebäude der Mappe erscheint in der Knotenansicht**, und der Knopf «Ausführen» ist frei.
* **Eine Bestellung landet bei unserem eigenen Server** und wartet, bis jemand «Freigeben»
  drückt. Erst dann steht sie in der Reihe — eine Maschine gibt sich hier nichts selbst frei.
* **Gerechnet wird mit dem bestehenden Abholer**, ohne zweite Rechenstrecke. Das erste
  echte Bild auf diesem Weg misst die HomeStation (Auftrag 164).
* **Auf der Visbox-Seite steht oben der Knopf «Knotenansicht».**

### 24.09.2026 (später) · Die Knotenansicht ist da — und läuft

* **Neue Richtung des Owners (E26):** Statt nur eine Ansicht des festen Ablaufs zu zeichnen,
  bekommt Visbox eine vollständige Knotenansicht.
* **198 Dateien, jede mit Fingerabdruck.** Wo das Werkzeug etwas braucht, das in Visbox
  fehlt (der Assistent, die Plan-Blätter, der Entwurfskern), steht ein kleiner
  **Stellvertreter** — 19 Stück, jeder sagt im Kopf, dass er einer ist.
* **Es läuft im Browser:** Knoten aus der Palette legen, der Render-Knoten mit allen
  Einstellungen, der Bildvergleich. 722 Prüfungen der Knotenansicht laufen hier grün.
* **Noch nicht angeschlossen:** Der Modell-Knoten sagt «0 Bauteile» — das Gebäude aus der
  Mappe und das Rendern über unseren Server kommen als Nächstes.

### 24.09.2026 · Die Knoten sichtbar machen

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
  Modellkarte. Das betrifft auch jede Bestellung über die Warteschlange ohne Modellangabe; sie
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

* **Das Ergebnis sagt jetzt je Kamera, ob ihr Bild kam.** Bisher stand dort still
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
* **Innenraum-Bestellungen über die Warteschlange kommen durch.** Bis heute blieb jede liegen — aus
  zwei Gründen, die man nur am Stück sieht: Das Feld war unbekannt, und die Datei hiess
  anders, als wir sie suchten. Beides behoben; ob im gelieferten Modell ein drittes
  Hindernis wartet, ist gefragt.
* **Die Entwurfsfläche ist nachgezogen:** Was der Bau brauchte und kein Blatt zeigte, ist
  jetzt gezeichnet. Zwei Stellen tragen das Schild «Owner-Entscheid offen» — dort haben Sie
  das Wort.
* **Geprüft:** 158 absichtliche Fehler über drei Wellen, jeder wurde gefunden.

**Ausprobieren am iPad** können nur Sie — die Anleitung samt Abnahmeblatt liegt in
`docs/VISBOX_IPAD_ERSTE_PROBE.md`. Bis es ausgefüllt zurückkommt, heisst der Stand der App
«gebaut, am Gerät unbestätigt».

### 22.09.2026 · Die iPad-App entsteht — und sie übersetzt auf einem Mac

* **Eine eigene App statt einer Webseite** (Ihr Entscheid). Sie heisst Visbox und
  öffnet sich in Xcode und in Swift Playgrounds.
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

### 22.09.2026 · Warum die Sonne nichts am Bild ändert — und was jetzt im Ergebnis ankommt

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
* **Ins Ergebnis ging bis heute nur die schlechteste Kamera.** Jetzt spricht jede, bei
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

Kommt aus der Warteschlange ein Auftrag, in dem ein Feld ausdrücklich **leer**
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
einer Skizze als Bewegung am iPad beginnt und am Rechner weitergeht.

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

### 20.10.2026 · Claude bedient Visbox am Mac

Claude (im Terminal als Claude Code oder als Programm Claude Desktop) kann jetzt die Knotenansicht von Visbox am Mac
bedienen: den Knotengraph lesen, Knoten anlegen, einstellen und verbinden, ein Bild oder Varianten bestellen, die Mappe
und die Skizzen vom iPad lesen, fertige Bilder ansehen und einen laufenden Render-Auftrag abbrechen. Der Anschluss liegt
in der App und ist nur von diesem Mac aus erreichbar.

**Die Spielregel ist für den Architekten gemacht, nicht für die KI.** Oben in der Assistent-Leiste stellt er ein, wie
selbständig die KI arbeitet: «Karte» (jede Änderung wird erst ein Vorschlag mit «Anwenden» und «Ablehnen»), «Coop» oder
«Voll» (Änderungen ohne Vorschlag). Löschen ist in jedem Fall ein Vorschlag, und die Grafikkarte gibt immer der
Architekt frei — dafür gibt es kein Werkzeug. Was die KI gerade tut, steht nur, solange sie arbeitet.

**Wer nimmt was zurück:** Strg+Z nimmt nur die eigenen Schritte des Architekten zurück. Was Claude ohne Vorschlag
geändert hat, nimmt der Knopf «Claudes letzten Schritt zurücknehmen» zurück — und nur, wenn seither niemand am selben
Graphen weitergearbeitet hat; sonst sagt ein Satz, woran es hängt. Fremde Arbeit wird nie still überschrieben.

**Begründung des Wegs:** Die Werkzeuge kommen aus der Knotenansicht selbst, nicht aus einer zweiten Beschreibung in der
App — so kann die Liste nicht auseinanderlaufen. Ob ein Aufruf ein Vorschlag wird, entscheidet die Knotenansicht nach
einem Probelauf auf einer Kopie; ein ungültiger Schritt wird gar nicht erst vorgeschlagen. Im Einrichten steht, was an
Anthropic geht: Mappennamen, Prompts, der Knotengraph und Bilder, die Claude ansehen will.

**Offen:** die Probe am Gerät mit beiden Claude-Programmen; die Werkzeuge, die die Mappe am Mac brauchen (Modell laden,
Kameras vorschlagen, Verlauf, Mappe anlegen); der Assistent mit derselben Werkzeugliste.

---

### 21.10.2026 · Die Mappe liegt am Mac

Bis hierhin lag jede Mappe — Modell, Knotengraph, Skizzen, Bilder — am Heim-PC, und der Mac zeigte sie nur an. Jetzt
liegt sie am Mac, als gewöhnlicher Ordner `~/Visbox-Mappen/<Name>/`, den man im Finder sieht und mit dem Mac sichert.
Der Heim-PC ist damit auf dem Weg zum reinen Rechner: Er bekommt je Auftrag das Modell und die Szene und gibt die Bilder
zurück; die App legt sie in die Mappe.

**Was der Architekt sieht:** ein Fenster «Mappen» (über das Logo oben links oder ⌘O) mit drei Teilen — die Mappen am
Mac zum Öffnen, die Mappen, die noch am Heim-PC liegen, mit dem Knopf «An den Mac holen», und «Neue Mappe». Die
Knotenansicht selbst sieht aus wie vorher; sie liest und sichert nur an einem anderen Ort. Ohne Heim-PC bleiben die
Mappe und die schon gerechneten Bilder da.

**Begründung des Wegs:** Die Knotenansicht wurde nicht umgebaut. Sie fragt weiter nach «der Mappe», «dem Graphen»,
«dem Modell»; die App beantwortet diese Fragen jetzt selbst aus dem Ordner am Mac. So bleibt die Arbeitsfläche, die
geprüft ist, dieselbe, und der Umzug steckt an einer Stelle. «An den Mac holen» kopiert und löscht nichts: Die Mappe am
Heim-PC bleibt liegen, weil das iPad seine Skizzen bis zum nächsten Schritt noch dorthin schickt. Das Umwandeln einer
IFC-Datei bleibt am Heim-PC, weil das Programm dafür nur dort laufen darf (Lizenz, Prozessgrenze); das fertige Modell
kommt danach in die offene Mappe am Mac. Ist keine Mappe am Mac offen, läuft alles wie vorher.

**Nachgebessert nach der Messung am Heim-PC:** Das Laden einer Datei aus einer Mappe am Mac machte die neue Mappe am
Heim-PC zur «zuletzt geöffneten» — für alle Geräte. Die Visbox-Seite und das iPad zeigten danach plötzlich die neue
Mappe statt ihrer eigenen. Jetzt sagt der Mac beim Laden, dass die Datei in seine Mappe gehört. Der Heim-PC legt dann
nur eine Kopie zum Umwandeln an (den Zwilling) und lässt alles andere, wie es war. Er schreibt dabei auch nie in die
Mappe, mit der am Heim-PC gerade gearbeitet wird. Ohne Mappe am Mac ist alles wie vorher.

**Offen:** die Probe am Mac (Mappe holen, ein Bild rechnen lassen, ohne Heim-PC wieder öffnen); die Messung am Heim-PC,
dass Holen, Auftrag und die alte Mappe dort zusammen funktionieren; das iPad, das die Mappe vom Mac holt (nächster
Schritt, der Weg ist im Plan beschrieben).

### Das iPad arbeitet über den Mac, verschlüsselt

**Was gebaut ist:** Das iPad spricht nicht mehr mit dem Heim-PC, sondern immer mit dem Mac — zuhause wie unterwegs. Die
Mappe liegt am Mac; das iPad holt dort die Bilder und legt seine Skizzen hinein, und die Knotenansicht sieht eine neue
Skizze sofort. Die Leitung zwischen iPad und Mac ist verschlüsselt: Der Mac hat dafür ein eigenes Zertifikat (einen
digitalen Ausweis) im Schlüsselbund, und das iPad merkt sich beim Koppeln dessen Fingerabdruck. Danach spricht es mit
keinem anderen Gerät, das sich als dieser Mac ausgibt.

**Was der Architekt sieht:** Am Mac «iPad koppeln» — QR-Code, Zahl, ein Schloss und das «Zeichen des Mac». Am iPad
«Mit dem Mac koppeln»; nach dem Koppeln steht in der Zeile oben ein Schloss und «über den Mac, verschlüsselt». Ist der
Mac weg, sagt das iPad das in einem Satz; Skizzen warten auf dem iPad, bis er wieder da ist.

**Begründung des Wegs:** Sprach das iPad weiter mit dem Heim-PC, sähe es dort eine andere Mappe als der Mac — zwei
Stände derselben Arbeit. Verschlüsselt wird zuerst, weil über diese Leitung jetzt die ganze Mappe geht. Das Zertifikat
kommt über den QR-Code oder die Nähe ans iPad, also über einen Weg, den ein Fremder im selben WLAN nicht umschreiben
kann. Ein iPad, das noch direkt mit dem Heim-PC gekoppelt ist, arbeitet in dieser Fassung weiter, sagt aber, dass es die
Mappe am Mac so nicht sieht; ab der nächsten Fassung soll der direkte Weg ganz wegfallen. Gerechnet wird mit einer Mappe
am Mac in der Knotenansicht, nicht vom iPad aus.

**Offen:** die Probe an Mac und iPad (koppeln, Skizze, Bild, ohne Mac); das Abschalten des direkten Wegs in der nächsten
Fassung.

**Nachtrag: der direkte Weg endet, und der Mac geht auch ohne Heim-PC (21.10.2026).** Der Heim-PC nimmt ein iPad, das
direkt mit ihm spricht, nicht mehr an. Er antwortet mit einem Satz: «Das iPad verbindet sich jetzt über den Mac — am Mac
‹iPad koppeln› öffnen und das iPad mit dem Mac koppeln.» Das iPad zeigt diesen Satz in seiner Verbindungszeile, statt
still zu scheitern, und seine Skizzen bleiben auf dem iPad liegen, bis es mit dem Mac gekoppelt ist. Woran der Heim-PC
den Unterschied erkennt: Was über den Mac kommt, trägt einen Vermerk «über den Mac»; alles andere, das sich als iPad
ausgibt, kam direkt. Der Mac selbst, die Webseite und die Werkzeuge am Heim-PC tragen keinen solchen Vermerk und merken
nichts davon. Dazu geht die Verbindung iPad–Mac jetzt **auch ohne eingerichteten Heim-PC**: Das iPad koppelt mit dem Mac
und sieht die Mappe am Mac mit Bildern und Skizzen; wer rechnen will, liest «Kein Rechner eingerichtet». *Begründung:*
Ein iPad, das still weiter direkt spricht, legt Skizzen an einen Ort, an dem der Architekt sie nicht sucht — darum ein
klarer Satz statt eines stillen Fehlers. Und die Mappe liegt am Mac; dass sie ohne Heim-PC nicht ans iPad käme, hätte das
iPad vom Rechner abhängig gemacht, obwohl es zum Zeichnen keinen braucht.

### 21.10.2026 · Vorschläge überstehen den Wechsel der Ansicht

**Anlass:** Beim ersten Durchlauf mit Claude am Mac schlug Claude vor, die Stimmung von «morgen» auf «abend» zu stellen.
Der Architekt wechselte kurz zur Visbox-Seite und zurück — der Vorschlag war weg, nichts geändert, und niemand hatte es
gesagt. Der Vorschlag hatte nur in der Knotenansicht gelebt, und die wird beim Wechsel jedes Mal neu geladen.

**Was gebaut ist:** Die Mac-App hebt die offenen Vorschläge selbst auf, zusammen mit der Mappe, zu der sie gehören.
Kommt die Knotenansicht zurück, bekommt sie die Vorschläge ihrer Mappe wieder und rechnet jeden noch einmal zur Probe
durch. Weg ist ein Vorschlag nur, wenn der Architekt ihn ablehnt oder anwendet — oder wenn die Arbeit mit Claude wirklich
endet: Die App wird geschlossen, oder der Architekt schaltet «Claude über MCP» aus. Dann hört Claude einen Satz mit dem
Grund, und die Leiste sagt, welche Vorschläge wegfielen. Ist Claude bloss kurz nicht erreichbar, bleibt der Vorschlag mit
dem Vermerk «Leitung unterbrochen» stehen; sobald die Verbindung zurück ist, erfährt Claude zuerst, welche Vorschläge noch
offen sind, und danach, was der Architekt in der Zwischenzeit entschieden hat. Eine Frist gibt es nicht: Ein Vorschlag
hält am Rechner nichts fest, er muss also nicht ablaufen. Passt ein Vorschlag nicht mehr — eine andere Mappe ist offen, oder der
Knoten, den er ändern wollte, ist inzwischen gelöscht —, bleibt er sichtbar, und «Anwenden» sagt, warum nichts geschieht.

**Was der Architekt sieht:** nichts Neues — der Vorschlag steht nach dem Zurückkehren einfach noch da. Neu sind nur die
Sätze in der Leiste, wenn ein Vorschlag nicht mehr passt oder wegfällt, und der Vermerk «Leitung unterbrochen».

**Begründung des Wegs:** Ein Vorschlag gilt für eine Mappe und ihren Knotengraph, nicht für ein Fenster. Darum liegt er
dort, wo die Arbeit über den Wechsel hinweg bleibt: in der App. Beim Zurückgeben wird er neu geprüft statt blind
eingesetzt, weil sich der Graph in der Zwischenzeit geändert haben kann; und er wird dabei nie von selbst angewendet,
auch wenn Claude frei arbeiten darf. Still verschwinden darf nichts: Wer einen Vorschlag gestellt hat, soll erfahren, was
aus ihm wurde.

**Offen:** die Probe am Mac (vorschlagen, Seite wechseln, zurück, anwenden).

### 22.10.2026 · Das iPad erkennt den Mac, auch wenn er umbenannt wird

**Anlass:** Bei einem Probelauf stand das iPad plötzlich auf «getrennt», obwohl der Mac lief. macOS hatte den Mac
wegen eines Namenskonflikts im Netz still umbenannt — aus «MacBook Pro» wurde «MacBook Pro (2)». Das iPad suchte den
gekoppelten Mac aber an seinem Namen und fand unter dem neuen keinen.

**Was gebaut ist:** Der Mac nennt bei der Suche im WLAN neben seinem Namen jetzt auch eine feste Kennung: den
Fingerabdruck seines Zertifikats, also seines digitalen Ausweises für die verschlüsselte Leitung. Das iPad kennt diesen
Fingerabdruck schon, denn es merkt ihn sich beim Koppeln. Es sucht den gekoppelten Mac jetzt an diesem Merkmal; wie der
Mac gerade heisst, ist nur noch Anzeige, und den neuen Namen übernimmt das iPad. Ein Mac mit älterem Stand nennt keinen
Fingerabdruck — dann sucht das iPad wie bisher am Namen. Ein Gerät, das unter dem gemerkten Namen auftritt, aber einen
anderen Fingerabdruck nennt, ist nie der gekoppelte Mac.

**Was der Architekt sieht:** nichts — das iPad bleibt verbunden, und in der Verbindungszeile steht der neue Name. Neu
koppeln muss er nicht.

**Begründung des Wegs:** Ein Name ist eine Anzeige, die das System ändern kann, ohne zu fragen; zum Wiedererkennen taugt
er nicht. Der Fingerabdruck ist das Merkmal, an dem das iPad den Mac ohnehin prüft, bevor es ein Byte schickt — er ist
kein Geheimnis, und wer ihn fälscht, gewinnt nichts, weil das iPad danach trotzdem nur mit dem gemerkten Zertifikat
spricht. Das Koppeln selbst bleibt unverändert; geändert ist allein das Wiederfinden.

**Nachtrag: grün heisst «da» (22.10.2026).** Im selben Probelauf zeigte der Mac in seiner Startansicht das iPad grün als
«gekoppelt · zuletzt vor 21 h», obwohl es gar nicht verbunden war. Gekoppelt war es — erreichbar nicht. Jetzt ist die Zeile
nur grün, wenn sich das iPad in den letzten fünf Minuten gemeldet hat; sonst ist sie gelb und sagt «gekoppelt, aber nicht
erreichbar seit …». *Begründung:* Das iPad meldet sich alle zehn Sekunden, solange die App offen ist; fünf Minuten Stille
sind kein Aussetzer mehr, und eine grüne Zeile, die nicht stimmt, verleitet dazu, den Fehler am falschen Ort zu suchen.

**Nachtrag: ein Weg heraus (22.10.2026).** War das iPad gekoppelt, der Mac aber nicht erreichbar, bot der Koppelbildschirm
nur «Trennen» an — der Weg über die Nähe oder den QR-Code erschien erst danach. Jetzt steht dort in diesem Fall zuoberst
«Neu koppeln» mit beiden Wegen. Die alte Kopplung gilt weiter, bis die neue gelungen ist; scheitert der Versuch, ist nichts
verloren. *Begründung:* Wer nicht verbunden ist, soll nicht erst etwas wegwerfen müssen, um es neu zu versuchen.

**Offen:** die Probe an Mac und iPad.

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

**01.10.2026, abends — Befunde aus der Nachprobe 230 an unserem Code behoben.** Die
Warteschlange zählt nur noch Läufe; eine Kamera über dem Dach wird gerechnet und als Aufsicht
markiert; ein Bildmodell, das die installierte Bibliothek nicht kennt, wird vorher abgewiesen;
die Innenkamera bekommt einen eigenen Bildauftrag, und ein Mass, das dort nichts misst, heisst
«nicht anwendbar». Ein Befund blieb offen: Die IFC-Materialien gehen schon bei uns verloren
(Arbeit für v0.1.8). Die HomeStation prüft das mit `auf-20261001-235`. Zwischenstand von 234:
Visbox für den Mac baut am echten Mac in Xcode, alle 401 Proben grün.

**02.10.2026, morgens — Nachmessung 235.** Die Korrektur für die Innenkamera wirkte im echten Lauf
nicht: Eine Zahl kam unterwegs nicht an, und unsere Proben hatten sie von Hand eingesetzt. Behoben,
mit einer Probe, die den echten Weg geht. Dazu drei Textfehler in den Hinweisen. Bestätigt am Gerät:
Das Ergebnis sagt jetzt, ob die Bildführung wirkte. Qwen-2.1 wird am Heim-PC mit dem
Entwicklungsstand der Bildbibliothek nachgerüstet (Auftrag 238).

**06.10.2026 — Qwen-2.1 rechnet am Heim-PC.** Die Bildbibliothek wurde auf ihren Entwicklungsstand
gehoben (nur zwei Pakete, das Standardmodell liefert bitgleiche Bilder). Ein echter Qwen-2.1-Lauf über
den Bestellweg kam geliefert zurück, mit der Marke «Lizenz offen». Die Innenkamera-
Korrektur ist am echten Lauf bestätigt.

**07.10.2026 — das Bildmodell wird je Auftrag nur noch einmal geladen (v0.1.8).** Die Messung 221
hatte gezeigt, dass bei drei Varianten das Bildmodell dreimal geladen wurde, je 1–2 Sekunden. Jetzt
bleibt es für den ganzen Auftrag liegen — alle Varianten einer Reihe, alle Kameras einer Bestellung —
und wird am Ende freigegeben, auch wenn eine Variante scheitert. Zwischen zwei Aufträgen bleibt alles
wie bisher, damit das Sprachmodell des Assistenten danach wieder Platz hat. Wechselt mitten im Auftrag
das Modell, wird das alte zuerst abgebaut, nie zwei zugleich. Geprüft mit Attrappen (drei Varianten:
vorher drei Ladevorgänge, jetzt einer); am Heim-PC gemessen wird es mit Auftrag 260 — dort auch, ob
die Geometrieprüfung neben dem liegenden Modell weiter Platz hat und ob die Bilder bitgleich bleiben.

**07.10.2026 — Materialien aus dem Modell: geprüft und bewusst nicht gebaut.** Bevor Farben und Materialien aus
der IFC in unsere 3D-Datei übernommen werden, wurde gezählt, ob das Demohaus überhaupt welche trägt. Es trägt
keine: Die Materialnamen haben keine Farbe, und was ein Lesewerkzeug dafür einsetzt, sind seine eigenen Grautöne.
Diese zu übernehmen hiesse, Erfundenes als Modellinformation auszugeben. Dabei fiel auf, dass die Modellausfuhr des
Demohauses Dächer, Treppe und Geländer weglässt — für die Prüfung gegen die Geometrie wichtiger als jede Farbe.

**07.10.2026 — einmal laden: am Heim-PC bestätigt, und ein Fund nebenbei.** Das Bildmodell wird je Auftrag nur
noch einmal geladen; die Bilder bleiben bitgleich, das Standardmodell wird rund ein Sechstel schneller. Bei der
Messung fiel auf, dass die Prüfung an der Vorführmappe jetzt durchfällt, die am 01.10. noch bestand — schon vor
dem Umbau. Woran das liegt, wird gerade getrennt gemessen.

**07.10.2026 — warum die Vorführmappe durchfiel, und die Behebung.** Die Nachmessung fand den Grund: Die Mappe
hatte keinen Standpunkt, und ohne Standpunkt nahm die Software einen alten Notblick schräg von oben, in dem das
Haus nur ein Sechstel des Bildes füllte. Mit Blick von Süden bestand dieselbe Mappe wie am 01.10. Jetzt rechnet
«Anwenden» ohne Angabe frontal von Süden — genau wie der Bestellweg — und sagt dazu, dass
es diese Vorgabe genommen hat. Das langsamere erste Qwen-Bild war Zufall der Reihenfolge, nicht der Umbau.

**07.10.2026 — der Verlauf am Render-Knoten ist gebaut.** Wie auf Blatt 15 gezeichnet und vom Owner abgenommen:
Unter dem Bild stehen die letzten vier Läufe, das neueste links, jeder mit seinem Urteilspunkt; ein Klick zeigt ein
Bild gross, ohne das Hauptbild zu ersetzen; gelöscht wird nichts. Beim Bau zeigte sich, dass die Software frühere
Läufe bisher wirklich vergass — jetzt hält sie die letzten vier fest. Ein Satz der Zeichnung war falsch und wurde
berichtigt. Geprüft ist es im Browser; die Probe in der Engine der Desktop-App macht der Heim-PC.

**08.10.2026 — Farben aus dem Modell kommen jetzt mit.** Die IFC des Demohauses trägt inzwischen Farben je
Material, dazu Dach, Treppe, Geländer, Fenster und Türen. Unsere Umwandlung übernimmt diese Farben — aber nur die,
die wirklich im Modell stehen, nicht die Ersatzgrautöne des Lesewerkzeugs. Die Form bleibt dabei unangetastet:
Die Tiefenkarte, an der jedes Bild gemessen wird, ist mit und ohne Farben dieselbe, auf das Pixel. Ob unsere Messung
jetzt auch das Dach sieht, prüft der Heim-PC am echten Demohaus.

**08.10.2026 — ein Fehler von uns, gefunden am echten Haus und behoben.** Die Messung am vollständigen Demohaus
bestätigte: Farben kommen an, die Form bleibt gleich, und die Prüfung sieht jetzt das Dach. Sie zeigte aber auch,
dass die Übernahme der Farben eine wichtige Prüfung still ausgeschaltet hatte — die, die erkennt, ob im Bild
überhaupt ein Gebäude steht. Am Testhaus fiel das nicht auf, weil es ein Gelände hatte; am Demohaus ohne Gelände
schon. Die Ursache war eindeutig, die Behebung klein, und ein neuer Test fängt den Fall künftig ab. Die Nachmessung
am Demohaus läuft.

**08.10.2026 — ehrlich «nicht beurteilbar», wenn das Haus zu klein im Bild ist.** Modelle ohne Boden, wie das
Demohaus, füllen das Bild nur zu knapp einem Fünftel. Dort kann der ältere Prüfwert gar nicht
bestehen, und jedes Bild galt als durchgefallen. Der Owner hat entschieden: In diesem Fall steht «nicht
beurteilbar», mit Grund und der Gebäude-Zahl als Auskunft. Auf dem Weg dahin habe ich eine Frage mit einer falschen
Zahl gestellt; sie wurde berichtigt und neu beantwortet. Nebenbei behoben: Solche Ergebnisse wurden bisher bei
jedem Lauf neu gerechnet, statt aus dem Zwischenspeicher zu kommen.

**08.10.2026 — zwei Sätze stehen jetzt am Bild, so wie auf Blatt 16 gezeichnet.** Rechnet Visbox ein Bild, ohne
dass jemand einen Standpunkt gewählt hat, steht direkt darunter: «Kein Standpunkt bestellt — von Süden gerechnet.»
Im Browser führt «Standpunkt setzen» gleich zum Grundriss, auf dem man ihn wählt; auf dem iPad steht vorerst nur
der Satz, weil die App noch keinen Ort hat, an dem man den Standpunkt wählt. Der Satz ist eine Auskunft und keine
Warnung, darum ohne Warnfarbe. Und füllt das Haus weniger als ein Fünftel des Bildes, trägt das Bild jetzt ein
eigenes Zeichen «NICHT BEURTEILBAR» — gelb und gestrichelt wie «nicht gemessen», aber mit dem richtigen Wort, denn
gemessen wurde. Beides steht jetzt im Projekt beim Bild selbst und bleibt darum auch nach dem Neuladen erhalten.
Auf dem Gerät ist es noch nicht geprüft.

**08.10.2026 — die Umgebung kommt ins Bild (Entscheid 76).** Eine Aufnahme des Ortes — ein «Splat», eine Wolke aus
Hunderttausenden farbiger Punkte — kann jetzt mit ins Bild. Visbox setzt sie um das Gebäude herum, sie erscheint im
Schönbild und in der Tiefenkarte, und das Bildmodell sieht damit, wo das Haus steht. Gemessen wird aber weiterhin
nur das Gebäude: Die Kamera richtet sich nach ihm, und die Prüfung, ob das Bild zur Form passt, sieht die Umgebung
nicht. Steht ein Baum der Aufnahme vor dem Haus, verdeckt er es — so wie ihn auch die Kamera sähe —, und der
Bericht sagt, wieviel. Eine Bestellung kann die Umgebung jetzt mitschicken; wo sie liegt, sagt eine Lageangabe. Geprüft
ist das an einem künstlichen Splat; wie gut es mit einem echten aussieht, misst der Heim-PC. Eine Frage ist dabei
aufgetaucht: Mit weiter Umgebung bekommt das Haus in der Tiefenkarte weniger Kontrast — ob das stört, zeigt erst
die Messung.

**Bestand ohne Schrift (08.10.2026).** Sind bestehende Gebäude aus der Punktaufnahme übernommen, sind sie
in der Modelldatei markiert. Visbox erkennt die Markierung und sagt dem Bildmodell dazu, dass diese Gebäude schlicht und
ohne Schrift erscheinen sollen — im Demolauf hatte es einen erfundenen Schriftzug an die Halle gemalt. Ob der Satz
wirkt, ist noch nicht gemessen; das macht der Heim-PC mit und ohne Zusatz.

**Erste Messung mit der echten Umgebung — und was sie umgeworfen hat (08.10.2026).** Der Heim-PC hat die Umgebung
mit der echten Punktaufnahme gerechnet. Lage und Farbe stimmten. Drei Dinge trugen nicht: Die Prüfung zählte die
Bäume als Gebäude mit; die Tiefenkarte wurde durch die Umgebung so gestreckt, dass das Haus kaum noch Kontrast hatte;
und die nähere Kamera für lange Bauten schaltete gerade bei der Halle nie ein. Alle drei sind behoben: Die Umgebung
wird bei der Prüfung ausgeblendet, die Tiefe richtet sich nach dem Haus, und der nähere Blick greift auch ohne
Gelände. Dabei kam ein älterer Fehler ans Licht: Die Regel «nach dem Gebäude rahmen» vom 30.09. kam bei Aufträgen
über die Brücke nie an. Offen bleibt, dass das Bildmodell aus den Punkten der Umgebung «Konfetti» malt.

**Konfetti — Entscheid 77 (08.10.2026).** Mit der echten Umgebung malte das Bildmodell bunte Punkte statt Bäume, weil
die Aufnahme Lücken hat. Der Owner hat «glätten» gewählt: Die Lücken werden im Tiefenbild gefüllt und die
Entfernungen dort gemittelt, damit Flächen entstehen. Beim Ansehen fiel auf, dass die erste Fassung den Boden vor
dem Haus zu einer weissen Fläche machte; jetzt bekommt das Haus den mittleren Bereich der Grautöne und die Umgebung
weiche Ränder. Ob das Konfetti weg ist, misst der Heim-PC.

**Messboden — Entscheid 78 (08.10.2026).** Die nähere Kamera für lange Bauten funktionierte, aber ohne Umgebung
sagte die Prüfung «nicht messbar», obwohl die Bilder gut waren: Das Modell hat keinen Boden, das Bild schon, und die
Prüfung hielt den Boden für das Gebäude. Der Owner hat einen «Messboden» gewählt — eine gedachte Bodenfläche, die
nur die Prüfung kennt. Sie wird aus der Kamera berechnet und stimmt mit einer echt gerenderten Bodenplatte auf
Millimeter überein. Zugleich wurde das Glätten der Umgebung verstärkt, weil das Konfetti blieb.

**Wo der Fehler beim Splat lag, und der richtige Weg (13.10.2026).** Auf die Frage des Owners, warum der Splat nicht
richtig verarbeitet wird, die ehrliche Antwort: Wir hatten ihn nur behelfsmässig als harte Kugeln gezeichnet — daher
das Konfetti, und kein Glätten konnte das beheben. Geprüft wurden die offiziellen Wege bei NVIDIA und Epic samt
Lizenzen. Entscheid 79: Im Produkt macht ein offener Weg (gsplat und Open3D) aus dem Splat ein echtes 3D-Netz; wo der
Owner Epic RealityScan selbst installiert hat, macht eine Brücke aus den Fotos ein noch besseres Netz. RealityScan
darf nicht mitgeliefert und nicht als Dienst für Kunden betrieben werden — dafür gibt es jetzt eine eigene Regel.
Ausserdem zählt der Messboden nur noch zum Trennen von Haus und Hintergrund, nicht in die Punktzahl.

**Die Brücke vom Splat zum Netz (13.10.2026).** Gebaut ist der offene Weg aus Entscheid 79: Ein eigenes kleines Programm
in eigener Umgebung (wie Blender) rendert den Splat mit gsplat richtig aus 48 Blickwinkeln und verschmilzt die Bilder
mit Open3D zu einem farbigen 3D-Netz. Blender lädt dieses Netz wie ein gewöhnliches Objekt — keine Kugeln mehr. Ohne
die Umgebung bleibt die alte Notlösung, und das Ergebnis sagt es dazu. Weil hier keine Grafikkarte ist, misst der
Heim-PC, ob das Konfetti damit verschwindet. RealityScan folgt später.

**Die Umgebung aus den echten Kamerastandorten (13.10.2026).** Der erste Lauf mit dem Netz hatte das Konfetti beseitigt,
aber grosse Löcher gelassen, weil die Brücke aus einem gesetzten Kreis schaute. Jetzt schaut sie von dort, wo die
Aufnahme wirklich stand — der Heim-PC hat nachgewiesen, dass Kameras und Splat genau übereinander liegen. Am künstlichen
Strassenraum stieg die Abdeckung von 71 auf 96 %. Dabei ein Lizenzfund: Ein Lesewerkzeug (pycolmap) trägt in seinem
fertigen Paket GPL-Code; es wird darum nicht verwendet, ein eigener Leser ersetzt es.

**Prüfung bestanden, Löcher bleiben — Tiefenfilter (13.10.2026).** Mit der echten Umgebung bestanden die Bilder zum
ersten Mal in allen drei Kameras. Die Umgebung selbst hatte aber weiter Löcher: Die gefilmte Person stand als Wolke vor
der Kamera, und die Tiefe war gesprenkelt. Jetzt sortiert die Brücke unsichere Tiefen aus, bevor sie das Netz baut —
am wirksamsten die Punkte, an denen der Splat entlang eines Sehstrahls «unentschieden» ist. Ob das am echten Splat die
Löcher schliesst, misst der Heim-PC.

**RealityScan jetzt (13.10.2026).** Der offene Weg über den Splat bleibt bei etwa einem Zehntel Umgebung stehen; der
Splat liefert seine Tiefe zu unscharf für ein sauberes Netz, und Filter halfen nicht. Der Owner hat entschieden, die
Umgebung aus den Fotos zu rechnen, mit Epic RealityScan, das er selbst installiert. Die Brücke ist gebaut: Sie gibt
RealityScan die Fotos samt den Kamerastandorten, holt das Netz zurück, prüft, dass es am richtigen Ort liegt, und fällt
sonst auf den offenen Weg zurück. Mitgeliefert wird RealityScan nie.

**RealityScan gemessen und repariert (14.10.2026).** Der Heim-PC hat RealityScan an der echten Aufnahme laufen lassen:
In gut fünf Minuten deckt das Netz 93 % der Umgebung, statt einem Zehntel beim offenen Weg, und es liegt am richtigen
Ort. Der Vergleichsweg mit COLMAP brauchte über eine Stunde und hatte Löcher oder aufgeblasene Flächen. Der Owner hat
RealityScan darum zum Weg fürs Umgebungsnetz gemacht; der offene Weg bleibt der Rückfall. Die Brücke selbst lief beim
ersten Versuch aber nicht — sieben Dinge waren anders, als die Dokumentation vermuten liess (das falsche Startprogramm,
ein Dialog, der den Lauf anhielt, das falsche Modell beim Export, schwarze Farben, ein «Deckel» über der Szene, ein
Programm, das nach dem Abbruch weiterlief, und ein Pfad im Fehlertext). Alle sieben sind behoben; ob das fertige Bild
besteht, misst der Heim-PC als Nächstes.

**Die Mac-App zeigt zuerst die Knoten (14.10.2026).** Der Owner fragte, warum die Mac-App eine Webseite zeigt, wo sie doch
die Knotenansicht zeigen soll. Die Antwort: Die Mac-App ist ein Fenster auf den Heim-PC, und der Knotenbaum lag dort
hinter einem Knopf. Jetzt öffnet die App direkt die Knoten; oben schaltet ein Schalter auf die Visbox-Seite und zurück, und
die Knoten zeigen die Mappe, die zuletzt offen war. Nachgebaut wird am Mac nichts.

**RealityScan am echten Auftrag (14.10.2026).** Der Heim-PC hat mit der reparierten Brücke einen echten Auftrag gerechnet:
Sie lief in knapp fünf Minuten ohne Hänger durch, das Bild besteht die Prüfung, und die Farben stimmen. Schlechte
Nachricht: Ein Teil des «Deckels» blieb stehen und erschien in fünf von neun Bildern als Fremdkörper. Die Grenze, ab der
ein Dreieck als Deckel gilt, ist darum halbiert; ob dabei echte Teile verloren gehen, misst der Heim-PC als Nächstes.

**Massstab aus der Kamerabewegung (14.10.2026).** Der Heim-PC hat einen Weg gezeigt, wie ein Scan von selbst echte Meter
bekommt: aus dem Bewegungssensor der Kamera, mit einer zweiten Schätzung als Gegenprobe. Gebaut wird das dort,
wo die Scan-Kette liegt. Visbox liest das Ergebnis und sagt im Urteil, wie verlässlich der Massstab ist — grün still, gelb
mit der Bitte um ein Mass von Hand, rot mit dem Hinweis, dass der Behelf bleibt.

**Ein Klick fürs Aktualisieren (14.10.2026).** Am Mac des Owners lief noch die Fassung, die sich selbst nicht ersetzen
kann; darum erschien kein Knopf. Der Owner will es wie bei jeder App. Jetzt genügt ein Klick: Die App lädt die neue
Fassung, prüft sie, ersetzt sich und startet von selbst neu; gefragt wird stündlich. Einmal muss die alte Fassung noch von
Hand ersetzt werden.

**Ein eigenes Icon (14.10.2026).** Bis dahin trug Visbox ein Platzhalter-Blatt. Drei Vorschläge lagen auf der
Entwurfsfläche; der Owner wählte die Box, deren eine Seite schon Bild ist — Modell hinein, Bild heraus. Es kommt mit
der Fassung 0.2.4 auf Mac und iPad.

**Die Knotenansicht wieder auf dem neuesten Stand (14.10.2026).** Am Mac zeigte Visbox noch die Knoten vom September:
alte Boxen, kein Schieben mit zwei Fingern. Die Knotenansicht war drei Wochen nicht nachgezogen worden, und ihr fertiger Bau
kam nie mit `git pull` auf den Heim-PC. Beides ist behoben; dazu zoomt die Knotenfläche jetzt
spürbar schneller.

**Die erste echte Probe des Ein-Klick-Wegs (14.10.2026).** Die App bot die neue Fassung an, scheiterte aber beim Ersetzen:
macOS liess sie von einem versteckten, schreibgeschützten Ort laufen, weil sie nicht in «Programme» lag. Ab 0.2.6 erkennt
Visbox das selbst und legt sich mit einem Klick nach «Programme».

**Die Umgebung mit echter Textur (14.10.2026).** Bisher trug das Netz aus den Fotos nur eine Farbe je Eckpunkt — an
Fensterwänden ein unlesbarer Brei. Jetzt legt RealityScan eine echte Bildtextur auf das Netz, wie ein Foto, das auf die
Flächen gelegt wird; im Vergleich des Heim-PC war das gleich scharf wie der Splat oder schärfer. Ob es im fertigen Bild
sichtbar besser ist, misst der Heim-PC als Nächstes. Wer die neue Einstellung nicht setzt, bekommt weiter den alten Weg.

**Was die Knoten tun (14.10.2026).** Auf der Bildertafel des Owners hängt jetzt je Knoten eine Karte: was er kann, wie er
funktioniert, was er auslöst und mit wem er verbunden ist, dazu eine Übersicht vom Modell bis zum geprüften Bild. Alles
aus dem Code belegt; wo Visbox noch einen Platzhalter hat, steht es auf der Karte. Beim Aufschreiben fielen vier
Ungereimtheiten auf, die jetzt als eigene Posten im Plan stehen.

**Ein Modell direkt im Knoten laden (14.10.2026).** Der Owner fragte, ob er im Modell-Knoten eine IFC oder sogar eine
ArchiCAD-Datei laden kann. Jetzt geht es: «Datei laden …» im Knoten, der Heim-PC legt daraus eine Mappe an und wandelt
IFC und andere Formate selbst um; eine neue Fassung derselben Datei bleibt in derselben Mappe, mit allen Bildern.
ArchiCAD-Dateien sind ein geschlossenes Format — der Knoten sagt, dass sie als IFC aus ArchiCAD gespeichert werden.

**Die Textur am echten Auftrag gemessen (14.10.2026).** An vier Blickpunkten ist die Umgebung mit Textur deutlich schärfer
als mit Eckfarben und als der Splat. Sie kostet je neuer Aufnahme rund vier Minuten mehr. Das fertige Bild mit Prüfung
steht noch aus.

**Visbox 0.2.0 (13.10.2026).** Seit der ersten vorführbaren Fassung 0.1.0 vom 3. Oktober sind neue Fähigkeiten dazu
gekommen; der Owner hat die neue Nummer 0.2.0 gewählt. Sie steht überall gleich — in der Bibliothek, der iPad-App und
der Mac-App —, und ein Fassungsblatt sagt, was drin ist, was am Gerät bestätigt ist und was nicht.


**Visbox 0.2.8: sauberer Neustart und ein iPad, das sich selbst verbindet (14.10.2026).** Nach dem Aktualisieren blieb am
Mac die alte App offen, und ein neues Fenster ging davor auf. Jetzt beendet sich die alte App zuerst, und ein kleiner
Helfer öffnet danach die neue; beim nächsten Start meldet sie, welche Fassung installiert ist. Die Nummer steht klein
neben dem Namen. Das iPad fragt beim Öffnen sofort nach der gemerkten HomeStation und sucht gleichzeitig nach ihrem
Namen — vorher wartete es bis zu einer halben Minute, bevor es überhaupt suchte. Am Gerät ist beides noch zu sehen.

**Die Skizze vom iPad als Knoten (14.10.2026).** Die Skizzen, die man am iPad zeichnet und in die Mappe legt, standen
bisher nur auf der alten Visbox-Seite. Jetzt holt ein eigener Knoten sie in die Knotenansicht: von selbst die neueste, eine
ältere ist am Knoten wählbar, mit kleinem Vorschaubild. Ehrlich gesagt kann die Skizze das Bild noch nicht führen — der
Render-Knoten nimmt heute gar kein Bild an, und die Bestellung hat kein Feld dafür. Sie lässt sich darum vorerst neben die
Renders in den Bildvergleich legen. Ob eine Skizze künftig den Render lenken soll, ist eine eigene Entscheidung.

**Die Skizze führt das Bild (15.10.2026).** Was die alte Visbox-Seite schon konnte, geht jetzt auch in der Knotenansicht:
Man hängt den Knoten «Skizze vom iPad» an den neuen Eingang «Skizze» des Render-Knotens, und der Heim-PC rechnet das Bild
aus der Zeichnung — die Skizze auf dem Bild, über das sie gezeichnet wurde, dazu der Prompt als Anweisung, was sich ändern
soll (ohne Prompt gilt die Bemerkung an der Skizze). Danach steht die Skizze in der Mappe als «gerechnet». Dafür hat die
Bestellung ein neues Feld bekommen, das im Auftragsvertrag noch bestätigt werden muss. Ehrlich gesagt: Auf dem Vorgabemodell kommt die
Skizze gemessen nicht an — der Knoten und das Ergebnis sagen das. Ob sie beim Modell Qwen-Image 2.1 ankommt, ist noch
ungemessen; der Heim-PC prüft es.

**Varianten mit einem Klick (15.10.2026).** Statt jedes Bild einzeln zu bestellen, hängt jetzt ein Knoten «Varianten»
hinter dem Render-Knoten. Man hakt an, aus welchen Standpunkten, in welchen Stimmungen und für welche Entwürfe gerechnet
werden soll; ein Zähler sagt vorher, wie viele Bilder es werden (Vorgabe: drei Standpunkte, Abendstimmung, ein Entwurf =
drei Bilder). Ab zwölf Bildern warnt er mit der ungefähren Dauer, sperrt aber nichts. Ein Klick bestellt alles, ein
zweiter gibt alles frei. Die Bilder erscheinen im Bildvergleich als Tabelle: Zeilen Standpunkte, Spalten Stimmungen,
je Entwurf ein Reiter, mit einem farbigen Punkt fürs Prüfurteil. Claude kann dasselbe mit einem Befehl
bestellen und den Stand lesen — so soll die Wettbewerbs-Demo ihre Variantenbilder ohne eigenes Skript bekommen. Ehrlich
gesagt: Die Dauer ist
eine Schätzung, am Heim-PC noch nicht gemessen; und dass Volumenvarianten von selbst als eigene Entwürfe erscheinen, fehlt
noch (heute muss man sie auf Ebenen legen).

**Eine Grundlage, mehrere Varianten (20.10.2026).** Im Demolauf vom 16.10. zeigten Morgen- und Abendbild desselben
Projekts verschiedene Standpunkte und verschiedene Häuser — für einen Wettbewerb unbrauchbar. Der Owner hat daraus einen
Grundsatz gemacht: Ein Rendering ist **eine** Blender-Grundlage (Kamera, Geometrie, Bilddurchgänge), und alle Varianten
entstehen aus ihr; nur Stimmung, Prompt und Zufallswert ändern sich. Der Heim-PC legt dafür jetzt jede gerechnete
Grundlage unter einer Kennung ab und holt sie für jede Variante wieder, ohne Blender neu zu rechnen; passt sie nicht
zum Auftrag, lehnt er laut ab. Ein fester Zufallswert sorgt dafür, dass nicht jede Variante einen anderen «besten»
Wurf behält. Dabei fiel ein alter Fehler auf: Das Häkchen «nur Cycles» bekam seit August gar nichts, weil zwei Seiten
dasselbe Feld verschieden lasen — jetzt liefert es das rohe Blender-Bild, den ersten der zwei Schritte, die der Owner
verlangt. Ehrlich gesagt: Die zwei Knöpfe am Render-Knoten («Grundlage rendern», «Variante erzeugen») fehlen noch; sie
werden zuerst gezeichnet. Und ob die Varianten am Gerät wirklich deckungsgleich sind, misst erst die HomeStation.

**Ein Fenster nach dem Aktualisieren (20.10.2026, Visbox 0.2.10).** Beim Aktualisieren am Mac stand am Ende eine zweite
und dritte Visbox neben der alten. Zwei Dinge kamen zusammen: Die App startete nach dem Herunterladen von selbst neu,
und der kleine Helfer, der die neue App öffnet, öffnete nach einer halben Minute auch dann, wenn die alte noch lief.
Jetzt klickt man selbst «Neu starten»; der Helfer bittet die alte App zu enden, zwingt sie notfalls und öffnet nie
daneben; und wer Visbox ein zweites Mal startet, bekommt die laufende nach vorn statt eines neuen Fensters.


**iPad koppeln ohne Abtippen (20.10.2026).** Bisher tippte man am iPad zwei Dinge ab, die am Mac standen: eine lange
Adresse und eine sechsstellige Zahl. Jetzt öffnet «iPad koppeln» am Mac ein kleines Fenster für zwei Minuten. Liegt das
iPad daneben, fragt es von selbst «Mit diesem Mac koppeln?»; nimmt man an, fragt der Mac seinerseits «iPad möchte
koppeln» — erst wenn beide Ja sagen, schickt der Mac über eine verschlüsselte Verbindung Adresse und Zahl hinüber, nie
das Kennwort. Geht das nicht, liest das iPad mit seiner Kamera einen QR-Code im selben Fenster, und als letzter Weg
bleibt das Abtippen. Nach den zwei Minuten verschwindet alles von selbst. Ehrlich gesagt: Gebaut und vom Übersetzer
geprüft, aber noch nie an zwei echten Geräten ausprobiert; und der Heim-PC lässt die Zahl selbst noch zehn Minuten
gelten — dass sie dort auch nach zwei Minuten verfällt, ist eine eigene Entscheidung.

**Man sieht jetzt, wie weit ein Bild ist (20.10.2026).** Ein Rendering mit drei Kameras dauert Minuten, und bisher
stand dabei nur «läuft». Jetzt meldet der Heim-PC laufend, bei welcher Kamera er ist und in welchem Schritt (Blender,
Bildmodell, Prüfung), wie weit er insgesamt ist und wie lange es noch etwa dauert. Sobald Blender eine Ansicht fertig
hat, liegt ihr rohes Bild als Vorschau bereit — man sieht also früh, ob Standpunkt und Ausschnitt stimmen. Bricht man
ab, hört der Heim-PC nach dem laufenden Schritt auf und behält das letzte fertige Bild als «Teilbild», ohne Gütewerte,
weil die Prüfung nicht mehr lief. Dabei fiel ein alter Fehler auf: Ein Lauf, der trotz Abbruch fertig wurde, meldete
danach «fertig» statt «abgebrochen». Ehrlich gesagt: Die Restzeit ist eine Schätzung aus den schon fertigen Kameras und
fehlt bei der ersten; wie sich die drei Schritte einer Kamera teilen, ist eine feste Annahme, keine Messung. Und ein
Schritt, der schon läuft, wird nicht mitten drin unterbrochen.

**Einmal koppeln, und der Mac weiss es (20.10.2026, Visbox 0.2.11 und 0.2.12).** Das iPad lässt sich jetzt ohne Abtippen
koppeln: Es scannt einen QR-Code am Mac, oder es findet den Mac in der Nähe. Am Gerät ging der QR-Code auf Anhieb; die
Suche in der Nähe zeigte nichts, und warum, ist noch offen — beide Geräte sagen jetzt ehrlich, wenn sie nichts finden.
Danach merkt sich das iPad die Kopplung so, dass sie auch ein Neuaufspielen übersteht, und der Mac zeigt, dass ein iPad
gekoppelt ist, statt immer neue Zahlen anzubieten. Ein kurzer Aussetzer im Mobilfunk wirft die Apps nicht mehr gleich in
den Vorführmodus.

**Die Mac-App bringt ihre Knoten selbst mit (20.10.2026, erster Schritt zu Visbox 0.3).** Bis jetzt holte die Mac-App
die Knotenansicht jedes Mal vom Heim-PC — war er aus, gab es keine Arbeitsfläche, und jede Änderung an den Knoten kam
über den Heim-PC statt mit der App. Jetzt liegt die Knotenansicht im Programm selbst. Das Webfenster der App fragt dafür
nicht mehr das Netz, sondern das Programm, über einen eigenen Adressanfang (`visbox://`): Die Teile der Ansicht liefert
die App aus sich heraus; nur was den Heim-PC wirklich braucht — Mappe, Modell, Skizzen und die Render-Aufträge — reicht
sie mit ihrer Anmeldung dorthin weiter. Ist kein Heim-PC da, erscheinen die Knoten trotzdem, und wo er fehlt, steht ein
Satz statt einer Wartezeit. Das ist der erste von sechs Schritten, an deren Ende Visbox ganz auf dem Gerät läuft und der
Heim-PC nur noch rechnet. Ehrlich gesagt: Die Mappe liegt in diesem Schritt noch am Heim-PC, der Vorführmodus ist noch
da, und am Mac selbst ist die neue Fassung noch nicht ausprobiert — ob das Webfenster mit dem eigenen Adressanfang in
jeder Einzelheit so arbeitet wie erwartet, zeigt erst das Gerät.


**Ohne Heim-PC bleibt alles bedienbar — und man sieht, wer rechnet (20.10.2026, Schritte 2 und 6 zu Visbox 0.3).**
Bisher ersetzte die Mac-App ihr ganzes Fenster durch einen «Vorführmodus» mit vorher gerechneten Bildern, sobald der
Heim-PC eine halbe Minute nicht antwortete. Das fällt weg. Jetzt bleibt die gewöhnliche Arbeitsfläche mit den Knoten
stehen, und oben erscheint ein schmales Band: «Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere
geht.» mit dem Knopf «Erneut verbinden». Wer gerade noch auf dem Startbildschirm steht, kommt von selbst in die Arbeit.
Die Assistent-Leiste sagt in einem Satz, dass sie einen Rechner braucht, statt einen Fehler zu melden; und wer trotzdem
ein Bild bestellt, liest am Render-Knoten denselben klaren Satz statt einer Fehlernummer. Ein kurzer Aussetzer zeigt wie
bisher nur ein leises «kurz nicht erreichbar — verbinde neu …». Stimmt das Kennwort nicht, steht ein eigenes Band mit
dem Knopf «Einrichten». Neu ist ausserdem unter «Einrichten» der Abschnitt «Wer rechnet?»: Für das Rendern mit Blender,
das Bildmodell und die Bedien-KI steht je «Heim-PC» (gewählt) und «Dieses Gerät» — Letzteres sichtbar, aber gesperrt mit
seinem Grund, etwa «kein Blender gefunden» oder «zu wenig Grafikspeicher». Die Wahl wird gespeichert. Ehrlich gesagt:
Sie ändert heute noch nichts — alles rechnet weiter am Heim-PC, bis ein Rechner auf dem Gerät selbst gebaut ist. Die
Render-Knöpfe am Knoten sehen ohne Heim-PC noch aus wie immer; erst der Klick sagt, dass es nicht geht. Und am Mac
selbst ist die neue Fassung noch nicht ausprobiert.
**Die schnelle KI-Vorschau (20.10.2026).** Am Render-Knoten gibt es jetzt den Schalter «Güte: Vorschau | Voll», und
die Vorschau ist die Vorgabe. Der Anlass war eine Zeit: Eine Variante brauchte im Probelauf rund neun Minuten. Die
Ursache war nicht das gewöhnliche Bildmodell, sondern ein grösseres Forschungsmodell, das mit 40 Schritten rechnete. Die
Vorschau rechnet darum immer mit dem schnellen Modell, mit den 8 Schritten, auf die es trainiert ist, mit einem einzigen
Zufallswert statt der Auswahl aus dreien und mit einem kleineren KI-Bild, das danach auf die Grösse der Blender-Grundlage
gebracht wird. Sie wird geprüft wie jedes Bild und trägt den Vermerk «Vorschau». Die Grundlage bleibt dabei unverändert;
dieselbe Ansicht lässt sich danach in voller Güte rechnen. Ehrlich gesagt: Wie schnell die Vorschau am Heim-PC wirklich
ist, ist noch nicht gemessen — erwartet sind Sekunden je Bild, gemessen wird es mit dem nächsten Auftrag. Im selben Gang
wurden fünf Fehler beim Abbrechen behoben, die eine Probe am Heim-PC gefunden hatte: Das Zwischenbild trug den Namen der
falschen Kamera, der Satz nannte den falschen Schritt, der Fortschritt blieb stehen, die Freigabe behauptete einen Klick,
und zwei Schreiber konnten sich den Abbruch gegenseitig überschreiben.

**Varianten ohne Zeitüberschreitung, und die Messung am Heim-PC (20.10.2026).** Die erste Messung der Vorschau am Heim-PC
ergab: Bei ruhigem Rechner brauchen drei Ansichten gut 100 Sekunden, das Bildmodell davon nur 2 Sekunden je Bild; den
grössten Teil frisst die Prüfung. Zugleich meldete die Mac-App bei jeder Variante «Der Heim-PC ist nicht erreicht». Die
Ursache lag nicht am Netz: Jede Variante schickte das ganze Modell noch einmal, und der Heim-PC las es in einem Zug,
während alle anderen Anfragen warten mussten. Seither liest er die Sendung in Stücken, legt das Modell direkt ab und hält
die anderen Anfragen nur für den kurzen Schritt des Anlegens an; eine Variante darf ganz ohne Modell kommen und bekommt
das Modell ihrer Grundlage. Die Mac-App wartet auf die zwei Wege mit Modell bis fünf Minuten statt 25 Sekunden. Dieselbe
Messung fand vier Fehler: Eine widersprüchliche Bestellung blieb ewig in der Warteschlange statt mit Satz zu enden; der
Satz zum Abbrechen erreichte die Anzeige nicht; zwei gleiche Ansichten eines Quaders wurden doppelt gerechnet, weil drei
von 1,6 Millionen Randpunkten verschieden waren; und jede Szene mit Geländeplatte wurde abgelehnt, weil die Prüfung den
Anteil des Hauses an der Platte zweimal abzog — einmal beim Ausrichten der Kamera, einmal beim Nachrechnen. Bei der
Prüfung wird jetzt gespart, was sich ohne Verlust sparen lässt: Die Vergleichsmessung an Bildern ohne Geometrie hängt
nur an der Grundlage und wird für jede weitere Variante wiederverwendet. Der Assistent hat ein eigenes Sprachmodell und
nimmt kein fremdes mehr von der Grafikkarte. Ehrlich gesagt: Alles ist mit Attrappen geprüft, am Heim-PC wird es erst
nachgemessen; und dass die Vorschau in der Prüfung «Geometrie nicht gemessen» zeigt, ist kein Rechenfehler — das
Bildmodell malte bei diesem kleinen Testhaus einen Innenraum statt eines Hauses.
**Claude kann sich mit der Mac-App verbinden — erst der Anschluss (20.10.2026, KI-Bedienung Stufe 2).** Claude (als
Programm auf demselben Rechner) soll Visbox einmal so bedienen können wie ein Mensch: Knoten setzen, Bilder bestellen,
Ergebnisse ansehen. Dafür hat die Mac-App jetzt einen eigenen Anschluss nach dem offenen Standard MCP. Er ist nur auf
diesem Rechner erreichbar, nicht im WLAN, und ab Werk eingeschaltet; ein Kennwort braucht er darum nicht. Jede Anfrage
muss sich als lokal ausweisen, damit keine fremde Webseite im Browser mithören kann. Die Regeln stehen fest, bevor es ein
einziges Werkzeug gibt: Was etwas ändert, wird eine Karte in der Assistent-Leiste, die der Architekt anwendet oder
ablehnt; Löschen geht nur über eine Karte; und die Grafikkarte gibt immer ein Mensch frei, auch wenn die KI sonst
selbständig arbeiten darf. Wartet eine Karte länger als 45 Sekunden, bekommt Claude «wartet noch» und fragt später nach,
statt den Auftrag zu wiederholen. Für Claude Desktop startet sich die App auf Wunsch ohne Fenster und reicht nur weiter.
Ehrlich gesagt: Heute kann Claude erst fragen, ob Visbox bereit ist; alles andere antwortet «kommt mit Stufe 3», wenn die
Knotenansicht ihre Werkzeuge an den Anschluss gibt. Am Mac selbst ist der Anschluss noch nicht ausprobiert.

**Stimmung, Kamera und Material rechnen jetzt am Heim-PC (20.10.2026, Entscheide 107 und 109–113).** Drei neue Knoten
der Knotenansicht von Visbox haben ihre Rechnung bekommen, bevor ihre Bedienung gezeichnet ist — damit die Bedienung
etwas hat, das wirklich wirkt. *Stimmung:* Statt einer festen Sonne liegt ein Rundumfoto des Himmels um das Modell
(acht Stimmungen, von Morgen bis Winter, frei von Rechten und nur am Rechenrechner abgelegt). Es beleuchtet das Modell,
wie der Himmel dort es getan hätte; die zusätzliche Sonnenlampe fällt dann weg, damit das Licht nicht doppelt kommt.
«Weiss» macht alle Flächen zum Gipsmodell. *Kamera:* Wohin die Kameras schauen, auf welcher Augenhöhe, mit welcher
Brennweite, wie weit weg und ob die senkrechten Kanten senkrecht bleiben, wird jetzt mit jedem Bild bestellt — bisher
galten dafür drei feste Richtungen für alle Bilder. Die Vorschau der Standpunkte im Knoten rechnet dieselbe Rechnung
wie das Bild. *Material:* Fassade, Dach, Fenster, Boden und übrige Bauteile können je ein Material aus einer kleinen
Bibliothek bekommen (Sichtbeton, Backstein, Stampflehm, Holzlattung …), mit Massstab, Drehung, Relief und Tönung.
Welches Bauteil was ist, liest der Rechner aus dem Modell; das Gelände bleibt immer, wie es ist. Fehlt am Rechner ein
Himmelsbild oder eine Textur, wird der Auftrag mit einem Satz abgelehnt, der die fehlende Datei nennt — ein Bild ohne
das Bestellte sähe sonst aus wie eines mit. Und jedes Ergebnis sagt, mit welchen Werten wirklich gerechnet wurde,
auch mit denen, die der Rechner selbst eingesetzt hat. Ehrlich gesagt: Geprüft ist alles mit nachgebauten Rechnern;
am echten Rechenrechner wird es erst gemessen, und die Bedienung in der Knotenansicht folgt noch.

**Das Haus steht nicht mehr vor einem fremden Foto, und es brennt nicht mehr aus (20.10.2026).** Die erste Messung der
Stimmungen am Rechenrechner zeigte drei Fehler, die man sofort sieht: Bei «Abend» stand hinter dem Haus das Rundumfoto
des Himmels selbst — ein Bodenfoto mit Wald und Felsen, das Haus schwebte davor. Bei «Mittag» war das Haus eine reine
weisse Fläche ohne Kanten. Und die Geländeplatte bekam das Bodenmaterial. Behoben: Das Himmelsfoto gibt jetzt nur noch
Licht, Schatten und Spiegelungen; was die Kamera direkt sieht, ist ein ruhiger Verlauf in den Farben dieses Himmels. Mit
Himmelsbild führt eine weiche Tonwertkurve die hellen Werte sanft gegen Weiss, statt sie abzuschneiden, und jede Stimmung
hat ihre eigene Belichtung und, wo nötig, eine warme oder kühle Tönung. Wieviel des Hauses trotzdem voll weiss ist, wird
jetzt bei jedem Bild gemessen und steht im Ergebnis (Ziel: unter einem Prozent). Das Gelände bekommt nie ein Material.
Dazu kleinere Dinge: Das Bild hat genau die bestellte Grösse (vorher wurde es still um einige Zeilen gekürzt, und die
Kamera stand darum etwas anders als in der Vorschau des Kamera-Knotens); die schnelle Vorschau folgt der Form enger;
eine Prüfzahl, die nicht gemessen werden konnte, heisst jetzt «nicht gemessen» statt null; eine Variante, die nicht zu
ihrer Grundlage passt, wird schon beim Bestellen abgewiesen. Die Himmelsbilder selbst wurden am Rechenrechner getauscht —
Abend ist jetzt ein echter Sonnenuntergang, Weiss ein neutrales Studio. Ehrlich gesagt: Die Helligkeit je Stimmung ist
ein erster Stand; ob das Haus in allen acht Stimmungen lesbar ist, misst der Rechenrechner als Nächstes.

**Licht mit Schatten, und das Haus hebt sich ab (20.10.2026).** Die zweite Messung der Stimmungen zeigte das nächste
Problem, und es war nicht kleiner: Alle Bilder wirkten milchig und flach. Das Haus war bei «Winter» praktisch
unsichtbar, weil der ruhige Hintergrund genau so hell war wie das Haus; nirgends gab es einen Schatten, weder am Haus
noch auf der Platte; der Abend hatte kein tiefes Licht, die blaue Stunde war pastell. Heller oder dunkler stellen half
nicht — es macht Haus und Hintergrund gleich viel heller. Fünf Änderungen: Der Rechner sucht im Himmelsbild die Sonne
(den kleinen, sehr hellen Fleck) und stellt eine Sonnenlampe genau dorthin; am Morgen und am Abend steht sie tief und
gibt Streiflicht mit langen Schatten. Das Himmelsbild hellt nur noch die Schattenseiten auf. Bei Stimmungen ohne Sonne
(bedeckt, Nebel, blaue Stunde, Weissmodell) kommt das Licht von einer grossen, weichen Lampe aus dem hellsten Teil des
Himmels — weiche Schatten statt keiner. Vor dem eigentlichen Bild rechnet der Rechner ein kleines Probebild, misst daran,
wie hell das Haus wird, und stellt den Hintergrund danach um einen festen Abstand dunkler oder heller. Die Platte ist
jetzt ein ruhiges Grau, auf dem man Schatten sieht, und die Tonwertkurve hat etwas mehr Kontrast. Wie stark sich das
Haus abhebt, steht jetzt bei jedem Bild als Zahl im Ergebnis; unter einem Grenzwert sagt ein Satz «Haus kaum sichtbar».
Dazu zwei Fehler: Bei einem Bild ohne KI-Schritt fehlten diese Messungen ganz, und auf einem kleinen Grundlagenbild fand
die schnelle Vorschau das Haus nicht (sie malte einen Strand) — die Vorlagen für das Bildmodell werden jetzt vorher
vergrössert. Und eine Prüfzahl der Vorschau blieb leer, weil das Bildmodell vor der kleinen Platte Boden malt, wo das
Modell nur Himmel hat; die gedachte Bodenfläche der Prüfung hilft jetzt auch dort beim Trennen. Ehrlich gesagt: Die
Stärken von Sonne und Aufhellung sind gesetzt, nicht gemessen; ob die Bilder jetzt Tiefe haben, misst der Rechenrechner
als Nächstes. Schrift-Artefakte im Vordergrund der KI-Bilder bleiben ein offener Befund.

**Die Sonne kommt von der Seite, und die Prüfung sieht, wenn die KI zu viel baut (20.10.2026).** Die dritte Messung
der Stimmungen zeigte: Das Haus hebt sich jetzt in allen acht Stimmungen vom Hintergrund ab, aber das Licht kam in
allen acht von vorn. Die Sonne stand in jedem Himmelsbild zufällig fast hinter der Kamera (beim Abend nur 5° neben der
Blickrichtung), die Fassaden waren gleichmässig hell und die Schatten fielen hinter das Haus, wo man sie nicht sieht.
Die Ursache lag nicht in der Rechnung, sondern in den Bildern: Wo die Sonne in einem Rundumfoto des Himmels steht, ist
Zufall. Gelöst ist es von der Kamera aus: Für jede Kamera wird das Himmelsbild so gedreht, dass die Sonne um einen
festen Winkel seitlich steht (je Stimmung zwischen 65° und 80°, auf einer wählbaren Seite) — eine Fassade im Licht, eine
im Schatten, und der Schatten fällt seitlich ins Bild. Weil jede Kamera ihr eigenes Bild aus Blender bekommt, gilt das
für jeden Standpunkt; wer die Drehung selbst bestellt, bekommt seine. Dazu vier kleinere Dinge: Eine «weiche» Ersatzlampe
(wenn ein Himmelsbild keine Sonnenscheibe hat) warf harte Schatten — sie ist jetzt wirklich gross. Die blaue Stunde
ist dunkler, mit doppeltem Abstand zum Hintergrund. Der Abend ist eine halbe Stufe dunkler belichtet (das Haus war fast
weiss), und sein Satz für das Bildmodell bestellt keine leuchtenden Innenräume mehr — das Bildmodell hatte daraus eine
Nacht gemacht. Ein Auftrag halb deutsch, halb englisch («Sichtbeton, Architekturfotografie, no people») wurde für
englisch gehalten und nicht übersetzt; das Bildmodell malte Holz statt Beton. Jetzt zählen die deutschen Fachwörter,
und nur der deutsche Teil wird übersetzt. Neu ist eine Zahl für ein Problem, das bisher keine Zahl sah: Das Bildmodell
baute aus der Geländeplatte ein Gebäude über die ganze Bildbreite. Die Prüfung zählt jetzt, wieviel Gebäude neben dem
Haus steht, wo das Modell nur Himmel hat, und sagt es ab einem Viertel der Hausfläche in einem Satz. Ehrlich gesagt: Die
Winkel und die Grenze sind gesetzt, nicht gemessen; ob die Schatten jetzt im Bild liegen und die Zahl zu dem passt, was
man sieht, misst der Rechenrechner als Nächstes, aus zwei Richtungen.

**Der Abend hebt sich ab, und die Prüfung sagt, wenn das Haus fehlt (21.10.2026).** Die vierte Messung der Stimmungen
bestätigte: Die Sonne steht jetzt in allen acht Stimmungen aus beiden Richtungen genau dort, wo sie stehen soll, und die
Schatten fallen seitlich ins Bild. Vier Dinge waren noch nicht recht. *Der Abend:* Das Haus hob sich kaum vom Himmel ab.
Die Kamera sah fast nur die Schattenseite, das Probebild vor dem Rechnen hatte aber das Haus im Durchschnitt gemessen —
und dieser Durchschnitt gehörte der hellen Sonnenseite, die zwanzigmal heller ist. Der Himmel galt darum als dunkel
genug, obwohl er heller war als die Schattenseite. Jetzt mittelt das Probebild die Helligkeit so, wie das fertige Bild
sie zeigt (in Blendenstufen); damit misst die Steuerung dieselbe Grösse wie die Prüfung danach. Den Abstand zum Himmel zu
verdoppeln wäre der einfachere Weg gewesen; er hätte den Abendhimmel fast nachtdunkel gemacht, und eine Nacht war der
Fehler der Messung davor. *Das fehlende Haus:* Ein KI-Bild zeigte den Blick unter ein Vordach — vom Haus war nichts
mehr zu erkennen, und eine Nachrechnung aus Farbe und Kanten fand den Umriss trotzdem «gut». Deckt sich das Bild kaum
mit dem Modell (weniger als ein Zehntel), sagt das Ergebnis jetzt in einem Satz, dass das Haus nicht wiederzuerkennen ist
und dass Masse aus Farbe und Kanten dort nicht gelten. *Die Drehung:* Das Ergebnis nannte als Drehung des Himmels 0°, auch
wenn je Kamera ganz anders gedreht worden war; jetzt steht dort je Kamera die gerechnete Drehung. *Die Zahl für zu viel
Gebäude:* Sie ist an der Hausfläche gemessen und kann darum über 1 liegen; nachgezählt an den Bildern zählt sie eher zu
wenig als zu viel. Alle sieben KI-Bilder bauten sichtbar über die ganze Bildbreite — ob die Grenze bei einem Viertel
richtig liegt, liess sich darum nicht prüfen. Ehrlich gesagt: Gemessen ist noch nichts davon am Rechenrechner; die
nächste Messung bestellt dafür zwei Prüfbilder, eines, das sicher im Umriss bleibt (ein Gipsmodell mit voller
Steuerung), und eines, das sicher ausbricht. Offen und ohne Fix notiert: Der Sichtbeton erscheint im KI-Bild nur
teilweise, und Schlagschatten sind auf Augenhöhe kaum zu sehen.

**Auch ein Bild voller Häuser zeigt das Haus nicht (21.10.2026).** Die fünfte Messung der Stimmungen bestätigte: Der
Abend hebt sich jetzt aus beiden Richtungen deutlich ab, der Himmel bleibt Abend und wird nicht Nacht, und der Satz «Haus
nicht wiederzuerkennen» steht genau beim Bild unter dem Vordach. Die Grenze für «zu viel Gebäude» trennt die beiden
Prüfbilder sauber: Das Gipsmodell blieb im Umriss, das Strassenbild brach aus. Drei Dinge waren noch nicht recht. *Das
Strassenbild:* Man erkennt das Haus darin nicht, der Satz fehlte trotzdem. Das Bild war fast ganz Gebäude, und so deckte
ein Teil davon zufällig die Fläche des Modells. Jetzt gilt das Haus auch dann als nicht wiederzuerkennen, wenn das Bild
mehr als doppelt so viel «Haus» zeigt, wie modelliert ist, oder wenn es weit über den Umriss hinaus baut und sich dabei
wenig mit dem Modell deckt. Der Satz nennt, woran es lag. *Der Vermerk an der Auswahl* stand bisher nur, wenn das Haus
fehlte; jetzt steht er immer, als Ja oder Nein. *Das Haus im Umriss halten:* Auch mit voller Steuerung durch die Tiefe
malte die KI bei Mittag Gebäude über die ganze Bildbreite. Nur das Gipsmodell blieb im Umriss, und dessen Beschreibung
sagte ausdrücklich «leerer Hintergrund, keine anderen Gebäude». Dieser Satz ist jetzt als Schalter vorbereitet, vorerst
aus. Die nächste Messung vergleicht mit und ohne, bevor er eingebaut wird. Ehrlich gesagt, und das ist die wichtigere
Nachricht: Die Arbeit am Licht der letzten Messungen wirkt nur im gerenderten Bild. Die KI liest vom Modell nur die Tiefe,
die Stimmung kommt bei ihr nur als Satz in der Beschreibung an. Die KI-Bilder vom Abend sind darum bildpunktgleich
geblieben, obwohl der Himmel im gerenderten Bild jetzt viel dunkler ist. Wie das Licht als Grundlage ins KI-Bild kommen
könnte, stellt ein eigenes Planblatt zur Wahl (`docs/PLAN_LICHT_INS_KI_BILD_2026-10-21.md`). Die Empfehlung ist, erst zu
messen, ob ein freies Modell das gerenderte Bild und die Tiefe zugleich annimmt. Offen und ohne Fix notiert: Bei
«Abend» liegt die Schattenseite des Hauses noch fast so dunkel wie der Himmel daneben.

**Licht ins KI-Bild: erst messen, dann am Bild wählen (21.10.2026, Entscheid 117).** Der Owner hat entschieden, zuerst
zu messen, wie das Licht der Stimmung ins KI-Bild kommen kann, und danach an Vergleichsbildern zu wählen. Dafür gibt es
zwei neue Schalter, beide vorerst aus. *Der Farbabgleich* bringt nach dem KI-Schritt die mittleren Farben und ihre
Schwankung auf die des gerenderten Bilds; jeder Bildpunkt behält seinen Ort, nur seine Farbe ändert sich. Eine Probe zeigt,
dass die Kanten am selben Ort bleiben. Geprüft wird weiter das KI-Bild ohne Abgleich, das Original bleibt daneben liegen.
*Der Bildeingang mit Stärke* gibt der KI das gerenderte Bild als Ausgangspunkt mit, zusätzlich zur Tiefe; die Stärke sagt,
wie viel sie neu malen darf. Unser Standardmodell nimmt ein solches Bild von sich aus nicht an. Darum beginnt die
Rechnung mit dem gerenderten Bild statt mit reinem Rauschen und rechnet nur die letzten Schritte, die Tiefe führt weiter
die Form. Ob das wirkt, ist noch nicht gemessen. Ein grösseres freies Modell (Qwen-Image) hätte den Weg nicht verkürzt: Die
Bibliothek, die wir verwenden, kann bei ihm Bild, Stärke und Tiefe nicht zugleich übergeben, und es wären 58 GB zu laden.
Die Messung rechnet drei Stärken in drei Stimmungen (Morgen, Abend, bedeckt), jedes Bild mit und ohne Farbabgleich, und
legt die Vergleichsbilder für die Wahl ab. Nur frei lizenzierte Gewichte (Apache-2.0), die schon auf dem Rechenrechner
liegen; nichts wird heruntergeladen. Danach wird eingebaut, was gewählt ist.

**Die Zahl für «zu viel Gebäude» zählt jetzt richtig (21.10.2026).** Die sechste Messung der Stimmungen bestätigte:
Das Strassenbild bekommt jetzt den Satz «Haus nicht wiederzuerkennen», und der Vermerk an der Auswahl steht bei jedem
KI-Bild. Der Satz «leerer Hintergrund, keine anderen Gebäude» hielt das Haus dagegen bei keinem Bild im Umriss; er
bleibt aus. *Die Zahl:* Sie mass breite Häuserzeilen viel zu klein — bei einem Bild mit einer Zeile über die ganze Breite
meldete sie 0,30 der Hausfläche, nachgezählt waren es 2,2. Sie zählte nur, was der Tiefenschätzer genau so nah sah wie
das Haus, und eine Zeile, die nur wenig dahinter steht, fiel durch. Jetzt zählt alles, was neben dem Haus nicht Himmel
ist; den Himmel erkennt der Tiefenschätzer zuverlässig, er legt ihn auf «unendlich fern». Fünf Rechenwege wurden an den
Bildern der letzten drei Messungen gegen die Nachzählung gelegt (Tabelle im Protokoll); dieser traf sie am besten. Eine
Ausnahme braucht es beim Gipsmodell: Dort malt die KI statt Himmel eine Fels- oder Studiowand, und «nicht Himmel» wäre
alles. Hat ein Bild keinen Himmel, zählt darum weiter nur, was so nah wie das Haus ist — so bleiben die Gipsmodelle bei
0 bis 0,2, und die Grenze bei einem Viertel trennt weiter richtig. Ehrlich gesagt: Zwei Bilder, in denen eine breite Zeile
statt des Hauses steht, bekommen den Satz «nicht wiederzuerkennen» weiterhin nicht. Die geeichte Zahl unterscheidet sie
nicht von Bildern, in denen man das Haus teilweise noch erkennt — beide bauen gleich viel daneben. Eine Regel, die an den
bisherigen Bildern passen würde, liegt zu knapp zwischen zwei Werten und ist darum nicht gebaut; die nächste Messung
beurteilt erst alle Bilder von Auge. Offen und ohne Fix notiert: Trotz «no people» malte die KI zwei kleine Personen;
ein Gegentext («was nicht zu sehen sein soll») wirkt bei unserem schnellen Modell nicht, weil es ohne die Rechnung
arbeitet, von der ein Gegentext abgezogen würde. Und beim Gipsmodell erfindet die KI den Hintergrund selbst.

**Licht ins KI-Bild: die erste Messung und was danach gebaut ist (21.10.2026).** Die Messung zu Entscheid 117 zeigt:
Das gerenderte Bild kommt über den eigenen Start bei der KI an. Eine rote Marke, die zur Probe hineingemalt war, stand
danach im KI-Bild. Schon ab einer Stärke von 0,4 hält das Haus seine Form, und Sonnenseite, Schatten und Helligkeit der
Stimmung kommen voll an. Ehrlich gesagt, und das ist die eigentliche Nachricht: Das KI-Bild ist dann fast genau das
gerenderte Gipsmodell. «Sichtbeton» aus der Beschreibung kommt nicht an, und bei bedecktem Himmel fehlt ab 0,55 der
Dachaufbau. Der Farbabgleich allein bringt den Farbton der Stimmung, aber kein Licht, und das Bild wird blass. Das liegt
nicht an einer Grenze im Abgleich, sondern daran, dass das weisse Gipsmodell selbst wenig Kontrast hat. Bis zur
nächsten Messung ist die Empfehlung darum, beide Bilder nebeneinander zu liefern. Das geht heute schon: Das gerenderte
Bild lässt sich als eigene Ebene mitbestellen, es fehlt nur die Anzeige am Render-Knoten. Gebaut wurden vier Dinge aus
der Messung. *Speicher:* Mit Bildeingang braucht die KI auf der Grafikkarte 3,8 GB mehr als ohne, und die Karte ist dann
fast voll. Die Prüfung vor dem Laden rechnet jetzt mit dieser gemessenen Zahl. Liegt ein anderes Modell auf der Karte
oder reicht der Platz nicht, wird der Auftrag mit einem klaren Satz abgewiesen, statt zu laden und mitten im Rechnen
abzubrechen. *Sichtbar:* Am Ergebnis steht jetzt, dass mit Bildeingang oder Farbabgleich gerechnet wurde und wie, je
Kamera ein Satz. Bisher war das nur durch Nachrechnen zu sehen. *Kleinigkeiten:* Der Satz zur Schrittzahl rechnete beim
Bildeingang mit dem falschen Wert. Und der Vermerk, ob der Farbabgleich die Formmessung verändert, sagte immer «nein,
nicht gleich», weil er aufs letzte Komma verglich; jetzt gilt eine Abweichung bis 0,03 als gleich, und die Zahl steht
daneben. Die nächste Messung rechnet höhere Stärken (0,8, 0,9 und 0,95). Dort darf die KI mehr selbst malen, und es
zeigt sich, ob sie dann Material malt und die Form trotzdem hält.

**Licht ins KI-Bild: die zweite Messung, und warum es beide Bilder werden sollen (21.10.2026).** Gerechnet wurden die
höheren Stärken 0,8, 0,9 und 0,95 in drei Stimmungen. Ehrlich gesagt: Sichtbeton kommt bei keiner. Bei 0,8 und 0,9 ist
das KI-Bild das gerenderte Gipsmodell mit Licht, also das, was das gerenderte Bild ohnehin schon zeigt. Bei 0,9 beginnt
die Form zu wandern, und bei 0,95 malt die KI ein anderes, weiss verputztes Haus. Bei bedecktem Himmel fehlt der
Dachaufbau bei allen drei Stärken. Der Farbabgleich hilft bei 0,9 nicht, die Farbe ist schon da. Die Empfehlung ist
darum, in der Knotenansicht das gerenderte Bild neben das KI-Bild zu stellen; der Architekt wählt am Bild. Die
Entscheidung darüber steht noch aus. Gebaut wurden vier Dinge aus dieser und der vorigen Messung. *Ein Fehler, der jeden
Lauf verhinderte:* Bestellt über die Knotenansicht, wurde jeder Lauf mit Bildeingang abgewiesen, auch bei leerer
Grafikkarte. Die Prüfung vor dem Lauf sah genug Platz; die zweite Prüfung im rechnenden Programm zählte den eigenen
Arbeitsbereich auf der Karte (rund 500 MB) als fremd und wies ab. Jetzt rechnen beide Prüfungen gleich, an einer
Stelle. *Ein Ergebnis auch bei Abweisung:* Diese zweite Abweisung schrieb kein Ergebnis, der Grund stand nur im Laufzettel;
jetzt trägt das Ergebnis den Satz. *Ein klarer Satz:* Die Abweisung nannte das eigene Sprachmodell des Assistenten
doppelt und «fremd»; jetzt einmal und als «eigenes Assistenzmodell». *Ein vierter Grund für «Haus nicht
wiederzuerkennen»:* Zwei Bilder, in denen eine breite Zeile statt des Hauses steht, bekamen den Satz bisher nicht. Neu
gilt: zeigt das Bild mehr als 1,2-mal so viel Haus, wie modelliert ist, und baut es zugleich weit über den Umriss, steht
der Satz, aber nur an Bildern ab 960 Bildpunkten Breite, weil das Verhältnis an kleinen Bildern höher ausfällt. An allen
14 Bildern der letzten drei Messungen trifft das genau das Urteil von Auge. Der Abstand zwischen «teilweise» und «nein»
ist schmal (1,16 gegen 1,27). Offen und ohne Fix notiert: Die Zahl «über den Umriss gebaut» kippt, wo die KI einen Himmel
malt, und ein ganz anderes Haus mit gleicher Silhouette fällt keinem der vier Gründe auf. Eine kurze Nachprobe am Heim-PC
bestätigt das Gebaute.

**Die Nachprobe, und was sie an Meldungen fand (21.10.2026).** Die Nachprobe am Heim-PC bestätigt das Gebaute: Bestellt
über die Knotenansicht, rechnet der Bildeingang wieder, und die Bilder sind Bildpunkt für Bildpunkt dieselben wie aus dem
direkten Aufruf. Die Abweisung nennt das eigene Sprachmodell einmal und als eigenes, und wo der Auftrag «nur bei freier
Karte» trägt, wird es entladen und gerechnet. Der vierte Grund für «Haus nicht wiederzuerkennen» trifft alle 14 Bilder wie
von Auge. Gefunden wurden kleine Lücken in den Meldungen, und sie sind behoben. Der Satz einer Abweisung stand im Feld,
das die Anzeige liest, nur bei der zweiten Prüfung, nicht bei der ersten; jetzt bei beiden. Die zweite Speicherprüfung
schrieb ihre Zahlen nirgends hin; jetzt steht im Logbuch des Heimrechners, wie viel frei war, wie viel dem eigenen Programm
gehört und wie viel verlangt ist. Und nach dem Entladen des Sprachmodells fehlte im Logbuch die Zeile mit dem Speicher:
Sie war geschrieben, aber an eine lange Zeile angehängt und beim Kürzen abgeschnitten; jetzt steht sie für sich. Dazu
fand ein Messprogramm, von Hand gestartet, die Gewichte des Tiefenschätzers nicht, weil nur der Dienst wusste, wo sie
liegen. Jetzt liest jedes Programm den Ort aus derselben Einstellung wie der Dienst, und der Tiefenschätzer lädt nur noch
aus dem eigenen Ordner, nie aus dem Netz. Ehrlich gesagt: Geprüft an Proben; ob die Einstellung am Heim-PC so gelesen wird
und die neuen Zeilen dort stehen, zeigt ein kleiner Prüfauftrag.
**Material und Umriss: zwei neue Schalter zum Messen (21.10.2026).** Zwei Dinge trifft die KI nicht, die der Architekt
bestellt. Sie malt Sichtbeton nur teilweise, mit Streifen aus Holz und Stein dazwischen. Und sie baut fast immer neben das
Haus weitere Gebäude; nur beim Gipsmodell bleibt sie im Umriss. Ein Satz wie «leerer Hintergrund» half kaum, eine
stärkere Bindung an die Tiefe auch nicht, und ein Gegen-Prompt wirkt bei diesem Modell gar nicht. Ein Planblatt prüft
fünf Wege mit Lizenz, Speicherbedarf, Aufwand und Risiko (`docs/PLAN_MATERIAL_UND_UMRISS_2026-10-21.md`). Gebaut sind die
zwei aussichtsreichsten, beide vorerst aus. *Umriss halten:* Ausserhalb des modellierten Hauses gilt das gerenderte Bild
mit Himmel und Boden, innen malt die KI. Das geht auf zwei Arten: nachträglich gemischt, oder schon während des Malens,
indem der Hintergrund nach jedem Rechenschritt auf das gerenderte Bild zurückgesetzt wird; dann malt die KI die Kante zum
Hintergrund selbst. *Material vorne:* Der Stoff, etwa Sichtbeton, steht am Anfang der Bildbeschreibung und dreimal,
statt an zweiter Stelle; eine Gewichtung in Klammern kennt dieses Modell nicht. Ohne Messung wird nichts davon Vorgabe.
Die Messung am Heim-PC rechnet jeden Weg gegen dasselbe Kontrollbild, dazu den Material-Knoten mit Sichtbeton-Textur, der
das gerenderte Bild als Ausgangspunkt mitgibt. Zurück kommen die Zahlen und ein Urteil von Auge: «Sichtbeton?». Nur
frei lizenzierte Gewichte, die schon auf dem Rechner liegen.
**Material und Umriss: was die Messung zeigte, und was danach nachgezogen ist (21.10.2026).** Die Messung am Heim-PC
fand ein klares bestes Bild: beide Schalter zusammen, der Stoff vorne und der Hintergrund während des Malens
festgehalten. Das Haus war ganz aus Sichtbeton, stand im Umriss, ohne sichtbare Naht, und man erkannte das Modell wieder.
Jeder Schalter allein reichte nicht: Der festgehaltene Hintergrund allein machte aus dem Hauptbau einen Rundturm, der
Stoff vorne allein baute noch mehr neben das Haus, und das nachträgliche Mischen sah aus wie ausgeschnitten und
aufgeklebt. Grafikspeicher kostete das Festhalten keinen. Danach sind vier kleine Dinge nachgezogen. Beim nachträglichen
Mischen bemängelten zwei Sätze noch das Bild von vor dem Mischen («baut über den Umriss», «nicht wiederzuerkennen»);
jetzt sprechen sie über das Bild, das geliefert wird, und die Zahlen von vorher stehen daneben. Der Satz, der sagt, dass
der Hintergrund festgehalten wurde, stand nur in einer Nebendatei; jetzt steht er im Ergebnis. Mit dem Material-Knoten
stand der Stoff fünfmal in der Bildbeschreibung; jetzt höchstens dreimal, ohne doppelten Satz. Und beim Bildeingang
merkte sich das Programm beim Vorbereiten des gerenderten Bilds einen Rechenweg, den es nie braucht; das kostete
vermutlich die knapp vier Gigabyte Mehrbedarf und ist abgestellt. Dazu zwei Kleinigkeiten aus der Messung davor: Ein
leerer Ordner für die Gewichte des Tiefenschätzers heisst jetzt «leer oder unvollständig» statt «unbekanntes Modell», und
im Logbuch steht die Speicherprüfung unter ihrem Auftrag. Und aus der Messung der neuen Knoten: Der deutsche Satz des Stimmungs-Knotens kam halb übersetzt an («leuchtende window»), der englische Satz des Heim-PC fehlte darum, und die Abendstimmung zeigte einen Innenraum statt des Hauses. Jetzt hängt der Heim-PC bei einer bestellten Stimmung immer seinen eigenen Satz an, genau einmal, und nimmt den des Knotens heraus; die Sätze aller acht Stimmungen werden ganz übersetzt. Und das Ergebnis nennt die Grösse des Himmelsbilds, mit dem das Grundbild wirklich gerechnet wurde. Ehrlich gesagt: gemessen war ein Startwert, eine Kamera und eine
Stimmung mit Material. Der Hintergrund ist dann flach wie bei einem Modellfoto, weil die Kamera in Blender nicht den
Himmel sieht, sondern einen ruhigen Farbverlauf, der bewusst vom Haus abgesetzt ist. Ob das Himmelsbild dort besser
wäre, und ob das beste Bild mit vier Startwerten, zwei Kameras und drei Stimmungen hält, misst der nächste Auftrag. Erst
danach wird über die Vorgabe entschieden.

**Licht ins KI-Bild: das Grundbild steht neben dem KI-Bild (21.10.2026, Entscheid 117a).** Nach den zwei Messungen hat
der Owner gewählt: Das KI-Bild bleibt, was es ist, ein Entwurf, und daneben steht das gerenderte Grundbild, in dem Sonne
und Schatten echt gerechnet sind. Der Render-Knoten bestellt dieses Grundbild jetzt bei jedem KI-Bild von sich aus mit;
der Heim-PC liefert es ohnehin schon, es wurde nur nicht abgeholt. Ein Klick auf das Bild am Knoten zeigt beide gross und
gleich gross nebeneinander, beschriftet «KI-Bild» und «Grundbild mit Licht»; die Marke «Vorschau» steht nur am KI-Bild.
Ein Umschalter darüber wählt «nebeneinander», «nur KI» oder «nur Grundbild», und die Wahl gilt auch für das Bild am
Knoten. Ehrlich gesagt: Am Knoten selbst stehen die zwei Bilder nicht nebeneinander. Der Knoten ist 184 Bildpunkte breit,
und jedes Bild wäre dort schmaler als 96 Bildpunkte, die Grenze, ab der ein Bild noch lesbar ist. Darum zeigt der Knoten
das KI-Bild mit der Beschriftung «KI-Bild · + Grundbild», und nebeneinander steht es in der grossen Ansicht. Ein Lauf von
früher, der kein Grundbild hat, sieht aus wie bisher. Die Varianten zeigen weiter nur das KI-Bild, weil das Grundbild für
alle Varianten derselben Grundlage gleich ist. Mit offener Mappe am Mac kommt das Grundbild mit in die Mappe, damit es
auch ohne Heim-PC da ist. Bildeingang und Farbabgleich bleiben Schalter zum Messen, ab Werk aus. Geprüft ist es mit Proben
und in einem Browserlauf gegen eine Attrappe des Heim-PC; am Gerät ist es noch nicht gesehen.


**Der Render-Knoten wird breiter: beide Bilder schon am Knoten (21.10.2026, Entscheid 119).** Bis hierhin stand am Knoten
nur das KI-Bild, weil zwei Bilder im 184 Bildpunkte breiten Knoten zu schmal geworden wären. Jetzt ist der Render-Knoten
zwölf Bildpunkte breiter, innen 196, und jedes Bild hat 96 — genug, dass KI-Bild und Grundbild schon am Knoten
nebeneinander stehen, beide beschriftet. Nur dieser eine Knoten wird breiter, und nur in der Breite: Er wird nicht höher,
weil jede Zeile ihre gemessene Höhe behält. Alles, was mit seiner Breite rechnet, rechnet mit der neuen: wo die
Verbindungen ansetzen, wie ein neuer Knoten Platz findet, wie der fertige Anfang die Knoten in Spalten legt, und wie ein
gesicherter Graph beim Öffnen entzerrt wird. Die Marke «Vorschau» steht unten links im KI-Bild; seine Beschriftung rückt
darüber, damit nichts verdeckt ist. Die grosse Ansicht mit dem Umschalter bleibt. Geprüft ist es mit Proben und in einem
Browserlauf gegen eine Attrappe des Heim-PC; am Gerät ist es noch nicht gesehen.

**Eine verlorene Klammer, und eine Probe dagegen (21.10.2026).** Am Mac lag die Bedienung der Knotenansicht links unten
ungestaltet übereinander: die Werkzeugknöpfe als Spalte, ein Wort doppelt, die Kugel des Assistenten als grosses Feld;
Claudes Vorschläge waren unter den Fensterrand gerutscht. Die Ursache war eine einzige fehlende schliessende Klammer in
einer Stildatei, entstanden, als zwei Arbeitsstände zusammengeführt wurden. Weil beim Bau alle Stildateien zu einer
werden, galt danach fast die Hälfte der Gestaltung nirgends mehr — und weder der Bau noch die übrigen Proben merkten es,
denn für sie ist das gültig. Seither gibt es eine Stilprobe: Sie prüft, dass jede Stildatei geschlossen ist, und öffnet
den fertigen Bau in einem Browser ohne Fenster, um nachzumessen, ob die Inseln am Rand sitzen, die Kugel klein ist und
Claudes Karte und das Gesprächsfeld im Fenster stehen. Sie läuft bei jedem Hochladen mit. Geprüft ist es mit dem Bau vor
und nach der Klammer (vorher 14 Befunde, danach keiner); am Gerät ist es noch nicht gesehen.

**Das Modell in 3D im Modell-Knoten (20.10.2026, Entscheid 109 A).** Bisher stand im Knoten «Modell» nur eine Zeile:
wie viele Bauteile die Szene hat. Jetzt zeigt ein kleines 3D-Fenster darunter das Gebäude selbst — genau das Modell,
das ein Bild-Auftrag mitbekommt. Ziehen dreht es, das Mausrad holt es näher, ein Doppelklick öffnet es gross über der
Knotenansicht. Solange der Zeiger im Fenster ist, bleibt die Knotenansicht still; daneben verschiebt und vergrössert
sie sich wie immer. Das Fenster ist fest klein, damit die Knoten ihren Platz behalten; die Grösse kommt mit dem
Doppelklick. Was es zum Zeichnen braucht (die freie Bibliothek three.js, MIT), lädt die Seite erst, wenn ein Modell
geladen ist — die Knotenansicht öffnet darum nicht langsamer. Fehlt dem Rechner die Grafikfähigkeit dafür, steht dort
ein ruhiger Satz statt eines leeren Bildes. Dasselbe Fenster ist der Grundstein für die nächsten Knoten: die
Auto-Kamera zeigt darin ihre Kameras als Kegel. Ehrlich gesagt: Geprüft ist es im Browser des Prüfrechners; ob es in
der Mac-App genauso zeichnet, sieht erst der Owner am Gerät.
**Die Bedienteile über der Knotenansicht (20.10.2026, Entscheide 115/116).** Die Knotenansicht hatte bisher nur ihre
Fläche; was rundherum zu bedienen war, stand in einer eigenen Leiste der Mac-App darüber und daneben. Jetzt schweben die
Bedienteile selbst am Rand der Ansicht, so wie in der übrigen Oberfläche der Arbeit: oben links ein runder Knopf mit dem
Logo, der zur Startansicht führt und beim Darüberfahren «Knoten» und «Visbox-Seite» auffächert; oben rechts ein Zahnrad
für die Einstellungen, ein Speichern-Knopf, der still zeigt, ob der Render-Graph gesichert ist (und laut wird, wenn
nicht), und eine kleine Reihe mit einem Schild zum Heim-PC («Heim-PC · bereit»; ein Klick öffnet «Wer rechnet?»),
Rückgängig, Wiederholen und der Nummer der Fassung. Unten links steht, sobald Claude angeschlossen ist, das Schild
«Claude verbunden» mit Claudes Vorschlägen zum Anwenden oder Ablehnen; dort stellt man auch ein, wie frei Claude
arbeiten darf (jede Änderung als Vorschlag, frei ändern oder Vollautomatik), und nimmt Claudes letzten Schritt zurück.
Oben in der Mitte sagt eine Zeile, was Claude gerade tut. Die ganze Ansicht ist jetzt dunkel; hell gibt es sie weiter
über das Menü «Darstellung». Die Leiste der Mac-App fällt über den Knoten weg — sie stand doppelt. Was nicht
übernommen ist, weil es die Sache in Visbox nicht gibt (gemeinsames Arbeiten mehrerer Personen im selben Modell, eine
Plan- und 3D-Ansicht, Geschosse, ein Rundgang durch Stationen), steht mit Grund in einer Liste, und eine Probe sorgt
dafür, dass kein neuer Bedienteil unbemerkt fehlt. Die Mac-App und die Seite sprechen dafür über einen zweiten, schmalen
Weg; das Kennwort des Heim-PC läuft nie darüber. Ehrlich gesagt: Geprüft ist es im Browser des Prüfrechners und an den
Proben; ob es in der Mac-App genauso aussieht, sieht erst der Owner am Gerät. Der Gesprächspartner «Assistent» als
schwebende Kugel und eine eigene Einstellungs-Fläche folgen als nächste Stufen.

**Das 3D-Fenster hell und ohne Abschneiden (20.10.2026, Befund am Mac).** Am Mac war ein IFC-Modell im Fenster fast
schwarz, beim Drehen ganz, und beim Heranzoomen fiel das Haus vorne weg. Zwei Ursachen: Bauteile, denen die IFC-Datei
keine Farbe gibt, kamen ohne Material an, und das Dateiformat macht sie dann ganz metallisch — Metall zeigt ohne
Umgebung nichts. Und die vordere Schnittebene stand fest so weit vor der Kamera, dass sie beim Heranzoomen ins Haus
schnitt. Jetzt steht das Modell in einem hellen Umgebungslicht, jedes Material ist auf eine helle, matte Wirkung
begrenzt (wie ein Weissmodell), dünne Kanten zeichnen die Körper nach, und die Schnittebenen folgen bei jedem Bild dem
Abstand. Dazu lag in einer älteren Mappe der Knoten «Auto-Kamera» über dem gewachsenen Modell-Knoten; beim Öffnen
rückt Visbox überlappende Knoten jetzt einmal nach unten, ohne sonst etwas zu verschieben. Ehrlich gesagt: Geprüft im
Browser des Prüfrechners, mit dem Beispielhaus; das IFC-Modell am Mac sieht erst der Owner.

**Der Assistent als Kugel und die Einstellungen als eigene Fläche (20.10.2026, Entscheide 115/116).** Unten rechts in
der Knotenansicht steht jetzt eine runde, leicht bewegte Kugel: der Assistent, der am Heim-PC mit einem freien
Sprachmodell (qwen3:14b) rechnet. Ein Klick öffnet daneben ein Gesprächsfeld — auf einem breiten Bildschirm als Spalte
am rechten Rand, die die Arbeitsfläche zur Seite rückt. Man schreibt, was das Bild zeigen soll; der Assistent antwortet
und legt, wenn er etwas einzustellen vorschlägt, eine Karte mit «Anwenden», «Ablehnen» und «Ändern» darunter. Gerechnet
wird erst nach «Anwenden», und das löst immer ein Mensch aus. Kommt eine Antwort, während das Feld zu ist, steht ihr
Anfang als kleine Blase an der Kugel. Fehlt der Heim-PC, steht im Feld statt der Eingabe ein Satz, warum — kein
Eingabefeld, das nur einen Fehler zurückbrächte. Die Regeln des Gesprächs (eine Karte zugleich, keine zweite Frage,
solange eine unterwegs ist, wie lang eine Nachricht sein darf) stehen an einer Stelle, in der Mac-App, die auch das
Kennwort des Heim-PC hält; die Seite zeigt nur, was die App ihr sagt. Die frühere Leiste des Assistenten am rechten
Fensterrand fällt in der Knotenansicht weg. Das Zahnrad oben links öffnet jetzt eine eigene Einstellungs-Fläche in der
Ansicht: Darstellung (hell oder dunkel, Farbakzent), Anzeige (Schriftgrösse, Bewegung), Bewegung und Klang, dazu der
Heim-PC mit seiner Lage und dem Knopf «Am Mac einrichten» (Adresse und Kennwort bleiben in der Mac-App), «Wer rechnet?»
mit der Wahl je Arbeit, «Claude über MCP» mit Ein und Aus und dem Befehl zum Verbinden, die Lizenzen und was eine neue
Fassung bringt. Das Schild «Heim-PC» oben rechts öffnet dieselbe Fläche gleich bei «Wer rechnet?». Was man dort wählt,
behält die App über das Neuladen hinaus. Abschnitte, die es in Visbox fachlich nicht gibt (Planungsphasen, Projektname,
Sonnenstand an dieser Stelle, Nutzungsstatistik), sind bewusst weggelassen und mit Grund aufgeschrieben. Ehrlich gesagt:
Geprüft an den Proben und im Browser des Prüfrechners; das Gespräch mit dem echten Heim-PC und das Bild in der Mac-App
sieht erst der Owner am Gerät.

**Der Bau der Knotenansicht prüft sich, bevor er beginnt (21.10.2026).** Die Knotenansicht von Visbox besteht zu
grossen Teilen aus Dateien, die wörtlich aus ihrer Vorlage stammen; für jede ist ein Fingerabdruck festgehalten. Bisher
prüfte eine Probe nur, ob eine Kopie seit dem Kopieren still verändert wurde — dass die Vorlage inzwischen weitergegangen
war, sah sie nie. Jetzt gibt es einen Abgleich: Er liest den aktuellen Stand der Vorlage direkt aus deren
Versionsgeschichte und sagt je Datei, ob sie gleich ist, abweicht, dort weggefallen oder hier noch nicht übernommen ist.
Eine Datei, die wir selbst geändert und zur Übernahme angemeldet haben, zählt nicht als Fehler, sondern als
angemeldeter Weg. Das Bauwerkzeug ruft zuerst die bisherige Prüfung und dann den Abgleich; findet einer etwas, wird
nicht gebaut. Wer bewusst gegen den festgehaltenen Stand bauen will, muss das ausdrücklich sagen, und dann steht es im
Stempel des Baus. Der erste Abgleich fand keine Abweichung; was neu war, war schon übernommen. Die Befehlspalette (ein
Suchfeld für Befehle, das mit Befehlstaste + K aufgeht) kommt nicht mit: Sie trägt in der Vorlage nur Befehle, die es in
Visbox nicht gibt (Wechsel zwischen Programmteilen, Projektdateien), und die Knotenansicht meldet dort keinen eigenen an.
Das steht mit Grund in der Liste der Ausnahmen, und eine Probe wird rot, sobald sich das ändert. Ehrlich gesagt: Geprüft an
Proben mit einem kleinen künstlichen Repository und einmal am echten Stand; ein Bau mit dem neuen Vermerk ist noch nicht
am Mac angekommen.

**Der Assistent bedient die Knotenansicht wie Claude, und beide sehen und klicken selbst (21.10.2026).** Bisher kannte
der Assistent am Heim-PC nur drei Vorschläge (Standpunkt, Bildauftrag, Varianten), während Claude die ganze
Knotenansicht über Werkzeuge bediente. Jetzt bekommt der Assistent dieselbe Liste: Er kann den Graph lesen, Knoten
anlegen, einstellen und verbinden, ein Bild bestellen. Sein Sprachmodell sagt, welches Werkzeug es aufrufen will; die
Mac-App führt den Aufruf aus und gibt das Ergebnis zurück, bis das Modell antwortet — höchstens zwölf Schritte je
Frage. Es gelten dieselben Regeln wie für Claude: Im Modus «Karte» wird jede Änderung ein Vorschlag, den der Architekt
anwendet; in «Coop» und «Voll» ändert die KI selbst, und jeder Schritt lässt sich zurücknehmen; Löschen und Rendern sind
immer ein Vorschlag, und die Grafikkarte gibt nie eine KI frei. Die Vorschläge des Assistenten stehen in seinem
Gesprächsfeld. Dazu kommen **Blick und Maus**: Eine KI kann sich die Knotenansicht ansehen — als Text, der sagt, was
sichtbar ist, und für Claude auf Wunsch als Bild; der Assistent bekommt nur den Text, weil sein Modell keine Bilder
liest. Und sie kann mit einer eigenen Maus klicken, tippen und ziehen — eine zweite Maus, die als kleine Figur mit
Schild zu sehen ist, die eigene bleibt frei. Bestimmte Stellen trifft diese Maus nie: «Freigeben» und «Alle freigeben»
(beide starten die Grafikkarte), die Knöpfe, die ein Bild direkt bestellen, Löschen, die Vorschläge selbst, die
Schalter, Rückgängig, Kennwort-Felder und die Anmeldung am Heim-PC. Solange eine KI bedient, sind diese Stellen
gestrichelt umrandet; die Taste Esc oder «Stopp» beendet das Bedienen sofort. Ändert ein Klick den Graph, gilt dieselbe
Regel wie bei einem Werkzeug — es entsteht also keine zweite Art von Vorschlag. An der Marke «Claude» stehen je KI die
Schalter «Mitschauen» und «Bedienen»; was der Architekt dort ausschaltet, bleibt aus. Ehrlich gesagt: Geprüft an
Proben im Browser des Prüfrechners und mit einem nachgespielten Sprachmodell; ob das echte Modell am Heim-PC die
Werkzeuge brauchbar ruft und wie die Maus am Mac aussieht, zeigen erst die Messung am Heim-PC und das Gerät.

**Was die Messung am Heim-PC zeigte, und was daraus wurde (21.10.2026).** Das Sprachmodell des Assistenten ruft die
Werkzeuge mit gültigen Namen, nie eines, das freigibt, und die Maus der KI klickt in keine gesperrte Stelle. Aber zwei
Dinge stimmten nicht. *Erstens* waren Leiste, Figur und die gestrichelten Rahmen im Browser unsichtbar. Der Grund war ein
einziges fehlendes Zeichen: In einer Datei mit Stilregeln fehlte eine schliessende Klammer. Weil beim Bau alle diese
Dateien hintereinander gehängt werden, galt danach fast die Hälfte aller Regeln nur noch innerhalb eines kleinen
Textfelds — darum lagen auch die Leisten am Rand der Knotenansicht ungestaltet in einer Ecke. Die Klammer ist gesetzt,
und eine Probe prüft jetzt das fertig gebaute Programm, nicht nur die einzelne Datei. *Zweitens* war der Assistent
inhaltlich schwach: Er riet die Kennung eines eben angelegten Knotens, erfand eine Stimmung, die niemand verlangt hatte,
meldete «gelöscht», wo nur ein Vorschlag lag, und sagte bei «Gib die Grafikkarte frei» nicht, dass das nur der
Architekt kann. Die Anweisung an das Modell ist geschärft — und weil eine Bitte an ein Modell keine Gewähr ist, prüft
Visbox dieselben Punkte jetzt selbst: Ein Aufruf mit einer Kennung, die das Modell nirgends gelesen haben kann, oder mit
einer Angabe, die niemand nannte, wird zurückgewiesen, und das Modell muss korrigieren; eine Antwort, die einen
Vorschlag als erledigt meldet, wird richtiggestellt; und wer nach der Freigabe fragt, hört immer «Freigeben kann nur der
Architekt». Die Taste Esc stoppt weiterhin beide KI zugleich — eine Notbremse, die nur eine anhält, wäre keine. Ehrlich
gesagt: geprüft an Proben und einmal im Browser des Prüfrechners; ob das echte Modell damit besser antwortet, zeigt die
nächste Messung am Heim-PC.

**Stimmung, Kamera und Oberfläche als Knoten (21.10.2026).** Was der Heim-PC seit dem 20.10. rechnen kann — Himmelsbilder
als Licht, Kameras nach Einstellungen, Materialien je Bauteil —, lässt sich jetzt in der Knotenansicht wählen. Der Knoten
**Stimmung** zeigt oben den Himmel der gewählten Stimmung und darunter die acht Stimmungen zum Anhaken: Morgen, Mittag,
Abend, Blaue Stunde, Bedeckt, Nebel, Winter und Weiss. Man kann den Himmel fest drehen oder es dem Heim-PC überlassen,
der die Sonne dann seitlich zur Kamera stellt, und wählen, ob die Stimmung auf das Licht, auf den Satz an das Bildmodell
oder auf beides wirkt. Weil das Licht die Grundlage verändert, rechnet jede Stimmung ihre eigene; wer zur vorigen
zurückwechselt, findet deren Grundlage wieder, ohne neu zu rechnen. Der Knoten **Kamera** hat zwei Arten. «Auto» heisst:
Der Heim-PC stellt die Kameras aus den gewählten Himmelsrichtungen, der Augenhöhe, der Brennweite, dem Abstand und der
Perspektive — die übliche mit senkrechten Kanten oder frei gekippt. Ein kleines 3D-Fenster zeigt das Modell mit einer
Pyramide je Kamera, darunter das Bild aus einer Kamera; beides kommt aus derselben Rechnung, die beim Rendern läuft, und
ändert sich bei jeder Einstellung mit. «Manuell» friert diese Kameras ein; danach tippt man Standpunkt und Blickpunkt in
Metern. Für die Oberfläche gibt es drei Knoten: **Material** wählt einen von elf Stoffen (Sichtbeton, Fichte, Backstein …)
mit Massstab, Drehung und Relief und zeigt ihn als Kugel, Würfel oder Fläche; **Farbpalette** hält bis zu vier Farben,
von denen eine das Material tönt, und alle gehen als Satz an das Bildmodell; **Oberfläche** ordnet die Materialien den
Bauteil-Arten zu — Fassade, Dach, Fenster, Boden, Übrige —, und was nichts bekommt, behält das Material aus dem Modell.
Ein neuer Graph beginnt schon mit Sichtbeton an der Fassade. Ehrlich gesagt: Die Bilder der Himmel und Stoffe am Knoten
sind noch gezeichnete Farbverläufe, bis der Heim-PC die verkleinerten Bilder liefert; bei mehreren Stimmungen bestellt
der Render-Knoten vorerst die erste, ein Bild je Stimmung gibt es über den Varianten-Knoten; Kameras im 3D-Fenster ziehen
geht noch nicht. Geprüft an Proben im Browser des Prüfrechners; was der Heim-PC aus diesen Bestellungen rechnet, zeigt
die Messung dort.

**Der Varianten-Knoten zeigt seine Bilder (21.10.2026, Blatt 36).** Bisher sah man die Bilder einer Varianten-Bestellung
erst im Bildvergleich. Jetzt trägt der Varianten-Knoten selbst eine Bildzeile: ein Daumenbild, daneben Stimmung und
Standpunkt, «2 von 6» und zwei Pfeile zum Blättern. Zwei Bilder nebeneinander hätten in der schmalen Karte die
Mindestgrösse von 96 Bildpunkten unterschritten, und ein Streifen zum Wischen hätte mit dem Rad gestritten, das die
Knotenansicht zoomt. Die Zeile ist in jedem Zustand gleich hoch — noch nichts bestellt, wartet, rechnet, fehlgeschlagen
(der Grund steht in der Kurzhilfe) oder fertig —, damit der Knoten nicht springt. Gezeigt wird nur das KI-Bild; das
Grundbild mit Licht gilt für alle Varianten gleich und steht am Render-Knoten. Ein «Vorschau»-Bild trägt seine Marke
wie am Render-Knoten. Ein Klick zeigt das Bild gross; dort blättert man und kann eine Variante **wählen** — ein Schritt,
den «Rückgängig» zurücknimmt, und den Claude und der Assistent im Stand des Knotens lesen. Dabei fielen drei Fehler auf,
die mitbehoben sind: Im Stilblatt fehlte seit dem Vortag eine Klammer, wodurch ein ganzer Teil des Aussehens still
ausfiel (unter anderem die Marke «Vorschau» und die Zeile «Grundlage»); die grosse Ansicht des Rasters im Bildvergleich
lag beim Zoomen ausserhalb des Fensters; und die Höhe des Varianten-Knotens war 26 Bildpunkte zu knapp, die Knöpfe
lagen halb unter dem Rand. Die Achse «Stimmungen» rollt jetzt, statt bei acht Stimmungen die letzten abzuschneiden.
Ehrlich gesagt: Geprüft an Proben und im Browser des Prüfrechners mit einer nachgestellten Brücke; am Mac und mit echten
Bildern des Heim-PC noch nicht gesehen. Offen ist, wohin eine gewählte Variante weitergeht (aufs Blatt, in den
Bildvergleich) — das ist ein eigener Entscheid.

**Eine Probe verfälscht nicht mehr den Stand des iPad (21.10.2026).** Der Heim-PC führt ein kleines Gerätebuch, damit der
Mac anzeigen kann, ob und wie das iPad zuletzt kam. Als der Heim-PC nachgeprüft wurde, ob das iPad über den Mac
hereinkommt, schrieb die Probe in die Zeile des echten iPad — der Mac zeigte danach «über den Mac, gerade gesehen», obwohl
kein iPad da war. Eine eigene Kennung je Gerät hätte das gelöst, aber das iPad schickt keine, und eine dauerhafte Kennung
würde das Tablet wiedererkennbar machen. Darum gibt es jetzt einen eigenen Namen für Proben («ipad-probe»): Er wird wie
ein iPad behandelt, steht aber in einer eigenen Zeile. Ehrlich gesagt: geprüft an Proben, am Heim-PC noch nicht
nachgemessen.

**Jedes Ergebnis sagt jetzt, wie das Bild entstand (21.10.2026).** Das Bildmodell kann ein Bild anders rechnen als
bestellt — etwa «aus dem Grundbild weiterzeichnen» bestellt und «nur aus dem Text» gerechnet, weil das Grundbild unterwegs
fehlte. Ein solches Bild sah bisher aus wie jedes andere; nur ein Satz im Urteil verriet es. Jetzt steht im Ergebnis jedes
Bildauftrags ein eigenes Feld: was bestellt war, was gerechnet wurde, und ob das abweicht — für den ganzen Auftrag und je
Kamera. Hat das Bildmodell nichts gemeldet, steht dort «nicht gemeldet» und nicht «gleich». Damit kann die Knotenansicht ein
Zeichen am Bild setzen. Ehrlich gesagt: geprüft an Proben mit nachgestelltem Bildmodell, am Heim-PC noch nicht an einem
echten Lauf gesehen; angezeigt wird es noch nicht.
**Drei Knoten passen wieder in ihre Karte (21.10.2026).** Die Karten der Knotenansicht sind schmal — der Inhalt hat 184
Bildpunkte Breite. Drei Knoten hielten das nicht ein. Am **Kamera-Knoten** brachen die Wahlknöpfe («Auto | Manuell»,
«24 | 35 | 50») in zwei und drei Zeilen um, die Zeile darunter stand weit über den Rand, und die Felder trugen die dunkle
Farbe auf der hellen Karte. An der **Stimmung** standen die acht Namen in zu engen Spalten und überlappten sich, und
«Himmel drehen» brach in zwei Zeilen. Am **Varianten-Knoten** stand «Alle freigeben» über den Rand hinaus. Behoben ist
das mit Regeln, die nur innerhalb der Knoten gelten — die gleichen Bausteine anderswo bleiben, wie sie sind: einzeilige,
schmalere Wahlknöpfe, die Namen der Stimmungen in kleinerer Schrift und in Spalten nach ihrer Länge, die zwei Knöpfe am
Varianten-Knoten dürfen zweizeilig werden. Der Schalter heisst jetzt kurz «Drehen»; was er tut, steht in der Kurzhilfe,
und wer sich vorlesen lässt, hört weiter «Himmel drehen». Beim Nachmessen fielen zwei Reste auf, die mitbehoben sind:
der Reiter «Satz» an der Stimmung und der rechte Blätterpfeil am Varianten-Knoten standen noch wenige Bildpunkte über.
Die Stilprobe misst die drei Knoten jetzt im fertigen Bau mit: nichts steht über, jede Wahlleiste ist einzeilig, keine
zwei Namen überlappen. Ehrlich gesagt: gemessen im Browser des Prüfrechners in beiden Farbthemen und beim Zoom, mit dem
die Knotenansicht startet; am Mac noch nicht gesehen.

**Die Prüfung spricht über das Bild, das man sieht (21.10.2026).** Im Video zum Verlauf stand «Das Haus füllt 2,9 %»
direkt neben einem KI-Bild, in dem das Haus sichtbar ein Sechstel füllt. Beides stimmte: Gezählt war am Bild aus dem
3D-Modell (der Grundlage), und die KI hatte den Ausschnitt selbst näher gewählt. Jetzt stehen zwei Zahlen nebeneinander —
«Grundlage 2,9 % · KI-Bild ≈ 17 %» —, mit dem Satz, dass die zweite aus der Tiefe des KI-Bilds geschätzt ist, und der Marke
«Ausschnitt anders», wenn eine Zahl mindestens doppelt so gross ist wie die andere. Daneben stand «Geometrie 0.0 gegen
0.65». Nachgerechnet an vier Läufen des Heim-PC war jede 0.0 dort kein Fehler, sondern eine festgehaltene Untergrenze: Das
KI-Bild ordnet vorne und hinten anders als das Modell, die Rechnung ergäbe weniger als null. Der Satz sagt das jetzt in
Worten («KI-Bild weicht von der Geometrie ab … kein Messfehler») und dass die Zahl bei so kleinem Haus nur Auskunft ist.
Ehrlich gesagt: Die Schätzung am KI-Bild ist an gezeichneten Testbildern geprüft, an echten Bildern des Heim-PC noch nicht;
die Grenze «doppelt so gross» ist gesetzt, nicht gemessen.
**Ein gewählter Blick wird zur Kamera (21.10.2026).** In einem Vorführvideo kam ein bewusst gesicherter Blick — ein
Fussgänger an der Hausecke — nicht im Knoten «Kamera» an: Der einzige Weg dorthin verlangte eine offene 3D-Ansicht. Jetzt
hat der Knoten einen Reiter «Blick», der die gesicherten Blicke als Auswahl anbietet. Ein gewählter Blick wird beim Wählen
festgehalten und als genau dieser eine Standpunkt bestellt; Varianten ändern danach nur die Stimmung. In Visbox sind die
gesicherten Blicke die Standpunkte, die für ein Bild der Mappe am Grundriss gesetzt wurden. Claude kann einen Blick beim
Namen wählen. Ehrlich gesagt: geprüft an Proben, am Mac noch nicht gesehen.

### Grossansicht und Vergleich der Läufe (21.10.2026)

Im Demolauf war das fertige Bild nur klein zu sehen, und mehrere Bilder auf derselben Grundlage liessen sich nicht
vergleichen. Jetzt zeigt ein Klick das Bild fensterbreit; die Prüfwerte sind eingeklappt, das Urteil bleibt sichtbar. Der
Verlauf am Render-Knoten ordnet die Bilder nach Grundlage, und die Bilder einer Grundlage stehen auf Wunsch gleich gross
nebeneinander. «Kuratieren» kennt jetzt jedes gerechnete Bild, nicht nur das letzte. Ob sich die Ansicht bei «fertig» von
selbst öffnet, ist ein Schalter, ab Werk aus — ein Fenster, das sich ungefragt öffnet, unterbricht die Arbeit.

Dazu der Kontext: Blendet ein Entwurf den ganzen Bestand aus, sagt Visbox das beim Bestellen, denn ein Entwurf ohne
Nachbarn steht im Bild «im Leeren». Am Heim-PC entsteht neben der Bauwerksmaske eine eigene **Kontextmaske** — wo die
Nachbarbauten und die Umgebung im Bild stehen. Sie ändert noch nichts am Bild; zuerst wird gemessen, ob der Bestand bisher
fälschlich als Bauwerk mitgeprüft wurde (Protokoll 74 §197).

**Fünf Befunde aus dem Heim-PC behoben, und ein Satz zur Lizenz (21.10.2026).** Der Heim-PC hatte bei einer Messreihe
fünf Dinge gefunden. Bestellte man nur eine Stimmung («Abendstimmung, warmes Licht»), blieb vom Prompt nur der
Stimmungssatz übrig, und das Bildmodell malte eine Höhle — jetzt steht dann «architectural building» davor. Der Lauf mit
dem Grundbild als Eingang braucht weniger Grafikspeicher als bisher eingetragen (gemessen 27'116 statt 31'316 MiB);
eingetragen ist die Messung mit einem Rand für mehrere Kameras. Bei «Umriss halten im Lauf» zählte die Prüfung den
festgehaltenen, flachen Hintergrund als zusätzliche Baumasse und meldete bei sauberen Bildern «baut über den Umriss» —
jetzt zählt dort nur, was so nah ist wie das Haus. Der Assistent nahm die Nummer einer Karte als Nummer eines Knotens;
das weist der Heim-PC jetzt mit Satz ab. Und auf «Rechne jetzt das Bild» schlug er gar nichts mehr vor; er bekommt jetzt
einmal den Hinweis, dass ein Render-Auftrag als Karte erlaubt ist. Dazu ein neuer Messschalter, der hinter dem Haus das
Himmelsbild zeigt statt eines Verlaufs — gebaut, noch nicht gemessen. Am Bild von Qwen-Image-2.1 steht jetzt der Satz
«Qwen-Image-2.1: Lizenz offen — nicht für Wettbewerb oder Veröffentlichung» (Owner-Entscheid 120); Wettbewerbsbilder
rechnet Z-Image Turbo. Ehrlich gesagt: Alles ist an Testdaten geprüft; ob es am Heim-PC trägt, misst der nächste Auftrag.

Und eine Schärfung: «deckungsgleich» hiess bis jetzt nur «auf derselben Grundlage gerechnet». Neu misst der Heim-PC je Bild,
ob die KI auch dieselben Kanten gemalt hat. Liegt der Wert unter der Schwelle, sagt der Vergleich «gleiche Grundlage, Form
weicht ab» — ein Vergleich, der keiner ist, wird so sichtbar. Die Schwelle ist vorerst gesetzt und wird gemessen.

**Ein Bild kommt im Original aufs Blatt und aus der Ansicht hinaus (21.10.2026).** Im Demolauf vom 16.10. kam am Ende kein
Rendering auf das A0-Blatt: «Aufs Blatt» nahm nur den letzten Lauf, und der war abgebrochen; die Bilder lagen nur am
Heim-PC; ein Bildschirmausschnitt von 369 × 228 Bildpunkten wurde hochgezogen und war unbrauchbar. Jetzt nimmt der Knoten
«Aufs Blatt» das neueste **fertige** Bild und sagt, wenn es nicht das letzte ist — gibt es keines, sagt er warum. Die grosse
Ansicht jedes Laufs hat «Exportieren»: die Datei so gross, wie sie gerechnet wurde, am Mac mit dem gewohnten
Sichern-Fenster. Wo es ein Blatt gibt, wird jedes fertige Bild in Originalauflösung in die Projektdatei gesichert und von
dort aufs Blatt gesetzt; beim Platzieren prüft eine Rechnung, ob das Bild an seinem Platz für den Druck fein genug ist
(150 dpi), und warnt sonst mit der grössten Breite, die noch reicht. Visbox selbst hat kein Blatt; dort zählt das
Exportieren. Ehrlich gesagt: geprüft an Proben, am Mac und mit echten Bildern des Heim-PC noch nicht gesehen.

**Auch das allererste Bild öffnet gross (21.10.2026).** Das erste Bild eines Render-Knotens — noch ohne Grundbild daneben
und ohne Verlauf — öffnet per Klick dieselbe grosse Ansicht wie jedes andere, mit «Exportieren» (und «Aufs Blatt», wo es
ein Blatt gibt) in der Fusszeile. Sonst käme man ausgerechnet an das erste Bild nicht zum Weitergeben. Im Kopf fehlt dann
die Angabe «1 von 1 im Verlauf», weil der Knoten noch keinen Verlauf zeigt. Beim Prüfen im Browser fiel dabei ein Fehler
auf: Wo fertige Bilder in die Projektdatei gesichert werden, zählte genau dieses Sichern als Änderung am Modell — die eben
gerechnete Grundlage galt sofort als veraltet, «Variante erzeugen» blieb gesperrt, und das erste Bild verschwand vom
Knoten. Gesicherte Bilder und Blätter zählen jetzt nicht mehr zum Modell. Ehrlich gesagt: im Browser mit einer
nachgestellten Gegenseite geprüft, am Mac noch nicht gesehen.

**Eine Variante rechnet auch ohne neu geschicktes Modell (21.10.2026).** In einer Testfassung kam auf «Grundlage rendern» das Grundbild, aber «Variante erzeugen» danach nie: Die Variante kommt bewusst ohne Modell — sie braucht kein Blender, nur die Tiefe und die Ebenen der Grundlage —, und der Heim-PC wies einen leeren Geometriepfad auf diesem Weg immer ab und liess den Auftrag liegen. Jetzt nimmt er eine Variante mit gültiger Grundlage an, nimmt das Modell des Laufs, der die Grundlage gerechnet hat, und rechnet notfalls aus der abgelegten Grundlage allein. Fehlt die Grundlage, sagt er «bitte zuerst Grundlage rendern». Ehrlich gesagt: an einer nachgestellten Bestellung geprüft, am Heim-PC noch nicht nachgefahren.

**Viele gleiche Teile in einer Modelldatei (21.10.2026).** Ein Haus aus einzelnen Steinen hat rund zwanzigtausend davon; eine Modelldatei kann einen Stein einmal beschreiben und dazu eine Liste, wo er überall liegt. Blender und die 3D-Vorschau von Visbox lesen das schon. Nur die schnelle Rechnung, die vor dem Rendern die Grösse des Bauwerks aus der Datei liest, sah bis heute nur den einen Stein — die Kamera hätte das Haus zu nah gerahmt. Jetzt zählt sie alle Lagen mit. Ehrlich gesagt: an Testdateien geprüft; wie lange Blender für zwanzigtausend Steine braucht, ist nicht gemessen.

**Die Statusantwort an Claude nennt die Fassung (21.10.2026).** Fragt Claude den Stand von Visbox ab, steht jetzt in einer eigenen Zeile, welche Fassung der Mac-App antwortet.

**Grosse Bilder reissen den Abgleich nicht mehr (21.10.2026).** Die Projektdatei wird mit anderen Geräten in Stücken
abgeglichen, und ein Stück darf höchstens 8 MiB gross sein; ein grösseres Bild brach die Verbindung ohne Meldung ab. Jetzt
wird ein fertiges Bild über 5 MB vor dem Ablegen als JPEG gespeichert und, wenn das nicht reicht, verkleinert — für ein
A0-Plakat bleibt das weit genug. Geht auch das nicht, wird es abgelehnt, und ein Satz sagt warum. Das Original in voller
Grösse gibt weiterhin «Exportieren». Ehrlich gesagt: geprüft an Proben mit nachgestelltem Umkodieren; am Gerät mit einem
echten grossen Bild noch nicht gesehen.

**Ein Bild sagt, wenn es das Grundlagenbild nicht gesehen hat (21.10.2026).** Eine Variante schickt dem Bildmodell zwei
Dinge: die Tiefe der Grundlage und ihr gerendertes Bild. Das Vorgabemodell kann das Bild aber gar nicht entgegennehmen —
es malt nur nach der Tiefe, Material, Licht und Ausschnitt frei. Gemessen in sechs Läufen: Das Haus wurde mehrmals über
die ganze Bildbreite gemalt. Bis jetzt stand im Ergebnis trotzdem einfach «geliefert». Jetzt steht beim Bild der Satz
«KI-BILD OHNE GRUNDLAGENBILD» mit dem Grund. Ob eine Variante das Bild künftig wirklich sieht, ist eine Entscheidung des
Owners. Zwei Wege sind vorbereitet: das Grundlagenbild als Start mitgeben, oder die Umgebung im Lauf festhalten.

**Die Knotenansicht merkt sich, wie ein Bild entstand (21.10.2026).** Zu jedem fertigen Bild hält die Knotenansicht von
Visbox jetzt fest, ob es so gerechnet wurde wie bestellt: was bestellt war, was gerechnet wurde, ob es abwich, und je
Kamera dasselbe. Meldet ein älteres Ergebnis nur den Satz «KI-BILD OHNE GRUNDLAGENBILD», gilt das Bild als abweichend,
ohne die Werte zu erfinden. Sagt das Ergebnis gar nichts, steht nichts da — «nicht gemeldet» wird nie als «wie bestellt»
gezeigt. Darauf setzt das Schild «Ohne Grundlagenbild» bzw. «Anders gerechnet» am Bild auf. Ehrlich gesagt: geprüft an
Ergebnissen aus dem Kern, mit nachgestellten Läufen; das Schild selbst und ein echter Lauf am Gerät stehen noch aus.

**Wie gross das Haus im Bild ist, zählt jetzt ehrlicher (21.10.2026).** An der Grundlage zählt nur noch das Haus, nicht
die Geländeplatte darunter und nicht der Bestand daneben. Am KI-Bild wird die Fläche vom Haus aus «gewachsen», solange die
geschätzte Entfernung stetig bleibt; Himmel, Boden und Hecken davor bleiben draussen. Die alte Zählung meldete bei einem
breit gemalten Haus 15 % statt 43 %, darum kam der Hinweis «Ausschnitt anders» nie. Der Bestand zählt auch in der Prüfung
der Form nicht mehr als Haus, sondern nur noch als Umgebung. Die Maske der Umgebung entsteht schon beim Rendern der
Grundlage. Ehrlich gesagt: an nachgestellten Szenen geprüft; am Heim-PC noch nicht nachgemessen.

**Varianten rechnen ab jetzt mit der besten gemessenen Einstellung (21.10.2026).** Ohne besondere Angabe stellt der
Heim-PC das gewählte Material an den Anfang der Bildbeschreibung, hält die Umgebung ausserhalb des Hauses in jedem
Rechenschritt fest, wie sie in der Grundlage aussieht, und zeigt hinter dem Haus den Himmel der Stimmung statt eines
ruhigen Verlaufs. Wer eine dieser Einstellungen ausdrücklich ausschaltet, bekommt sie aus. Wo eine Einstellung nicht
passt (Vorschau, nur Grundlage, Skizze, Gipsmodell), entfällt sie mit Grund. Eine Variante auf einer älteren Grundlage
ohne Himmel bleibt gültig und sagt am Bild, dass der Himmel dafür neu gerendert werden muss. Am Heim-PC noch nicht
nachgemessen.

**Ein Haus aus zwanzigtausend Steinen, richtig gelesen (21.10.2026).** Eine Probe mit einer Mauer aus einzelnen
Backsteinen zeigte zwei Fehler. Erstens bekam jeder Stein eine eigene Kennung im Material-Bild, und die Namen hängten sich
immer länger aneinander — am Ende hiess kaum noch ein Stein «backstein». Der Grund: Alle Steine teilen sich eine Form, und
beim Umbenennen las der nächste Stein schon den neuen Namen. Jetzt wird zuerst geplant und dann getauscht: eine Kennung je
Material, also drei für die ganze Mauer, jede mit eigener Farbe. Zweitens zählte der Boden als Bauwerk, weil er «boden»
heisst — ein Wort, das Visbox absichtlich nicht als Gelände liest, denn auch ein Geschossboden heisst so. Jetzt erkennt
Visbox ihn an seiner Form (gross, flach, unten), auch wenn kein Name hilft, und eine Modelldatei kann ihn ausdrücklich als
Boden kennzeichnen. Ehrlich gesagt: ohne Blender geprüft; ob es am Heim-PC so rechnet und wie viel schneller es wird, ist
noch nicht gemessen.
**Der Assistent sagt, was er wirklich getan hat (21.10.2026).** Schlägt er das Löschen eines Knotens vor, liegt eine
Karte bereit, und erst «Anwenden» löscht. Er sagte trotzdem «Der Knoten wurde gelöscht — es liegt eine Karte». Jetzt
prüft Visbox jeden Schlusssatz: Was nur vorgeschlagen ist, heisst «vorgeschlagen», mit dem Namen der Karte. Und wer
eine neue Stimmung «mit dem Render-Knoten verbinden» lässt, bekommt keinen zweiten, leeren Graph mehr, sondern die
Verbindung im bestehenden. Daneben: Kamerakürzel dürfen deutsch geschrieben sein («nNO»), ein unbekanntes beendet den
Auftrag sofort mit einem Satz; der Satz «KI baut über den Umriss hinaus» steht an jeder Kamera, für die er gilt. Am
Heim-PC noch nicht nachgemessen.

**Drei Messungen, sechs Nachbesserungen (21.10.2026).** Der Heim-PC hat die Arbeit des Tages nachgemessen. Vier Bilder mit Augenurteil zeigten: Die Grenze, ab der Visbox zwei Bilder «deckungsgleich» nennt, lag zu hoch. Ein Bild, das die Form hielt und nur Fenster und Fugen dazumalte, galt als «Form weicht ab»; neue Fenster sind eben auch Kanten, die das graue Grundbild nicht hat. Die Grenze steht jetzt bei 10 % statt 30 % gemeinsamer Kanten — gesetzt aus diesen vier Bildern, und so auch angeschrieben. Der Assistent der Knotenansicht hatte einen Beispielsatz aus seiner Anweisung wörtlich übernommen («Das Löschen ist als Karte A-1 vorgeschlagen») und an Antworten gehängt, in denen nichts gelöscht wurde. Die Anweisung steht jetzt ohne Beispielsatz, und Visbox streicht selbst jeden Satz, der eine Karte nennt, die im Gespräch nicht entstand, oder ein Löschen, das niemand vorschlug. Wer eine neue Stimmung «mit dem Render-Knoten verbinden» lässt, bekommt beides in einem Schritt vorgeschlagen, statt eines Knotens ohne Verbindung. Kleinere Dinge: Ein ausgeschalteter Schalter heisst im Ergebnis «aus» statt «leer»; die Herkunft des Bodens ist gleich gebaut, ob ein Name, die Form oder eine Kennzeichnung in der Datei ihn fand; und eine schwer verständliche Zeile im Protokoll des Heim-PCs sagt jetzt in Worten, wie viel der Übereinstimmung jedes leere Bild auch bekäme. Offen und ehrlich: Im nahen Bild schätzt Visbox den Anteil des Hauses zu klein (31 % gegen 46 % von Hand); die Ursache ist ohne die Tiefenkarte nicht zu sehen. Visbox schreibt jetzt mit, woran die Schätzung aufhört, und der nächste Lauf zeigt es. Eine Mauer aus zwanzigtausend Einzelsteinen wird weiter nicht zusammengefügt: Das Bild rechnet in jeder Form gleich schnell, der Umbau kostete ein Vielfaches.

**Neuer Knoten und seine Verbindung in einem Zug (21.10.2026).** Bat man den Assistenten, einen Knoten zu setzen und
gleich zu verbinden, riet er die Kennung des neuen Knotens — die gibt es aber erst, wenn der Knoten angelegt ist. Die
Verbindung wurde abgewiesen, der Knoten stand allein. Der richtige Weg (beides als ein Paket, der spätere Schritt zeigt
auf «den neuen Knoten aus Schritt 0») stand nur in der Beschreibung des Paket-Werkzeugs. Jetzt nennen ihn auch die
Beschreibungen von «Knoten setzen» und «Verbinden» in einem Satz — für den Assistenten und für Claude dieselbe Liste. Ob
der Assistent ihn damit wählt, ist am Heim-PC noch nicht nachgemessen.

**«Rechne das Bild» ergibt wieder ein Bild (21.10.2026).** Bei der Nachmessung bat man den Assistenten «Rechne jetzt das Bild», und es kam kein Auftrag zustande. Das Sprachmodell hatte Werte erfunden, nach denen niemand gefragt hatte — ein bestimmtes Bildmodell, volle Güte, eine Bildgrösse —, weil die Beschreibung des Werkzeugs sie ihm alle aufzählt. Visbox wies sie eins nach dem anderen zurück, bis die Versuche aufgebraucht waren. Jetzt lässt Visbox erfundene oder unerlaubte Werte einfach weg, stellt den Auftrag mit dem Rest und sagt, was es wegliess; dann gilt, was am Knoten eingestellt ist. Wer nach der Grafikkarte fragt, hört in jedem Fall, dass nur der Architekt freigibt. Beim Schätzen, wie viel Haus im KI-Bild steht, schnitt eine Hilfslinie aus dem Blender-Bild das näher gerahmte KI-Bild mitten in der Fassade ab; sie fällt jetzt weg, wenn das KI-Bild anders rahmt und das Haus unter ihr weiterginge. Ehrlich gesagt schätzt Visbox dann eher zu viel, weil Hecken vor dem Haus mitzählen (56 % gegen 46 % von Hand) — näher dran als vorher (31 %), aber nicht genau. Am Heim-PC noch nicht nachgemessen.

**Was der Architekt sagt, kommt auf die Karte — und die Antwort sagt, wer freigibt (21.10.2026).** Die Nachmessung bestätigte die Arbeit vom selben Tag: «Rechne das Bild» ergibt eine Karte, und Visbox lässt Erfundenes weg. Drei Dinge waren noch schief. Bat man um «eine Vorschau mit Stimmung abend in 1920 x 1080», trug die Karte Stimmung und Grösse, aber nicht «Vorschau» — das Sprachmodell hatte das Wort fallen lassen, und Visbox ergänzte bis dahin nichts. Jetzt übernimmt Visbox, was in der Frage eindeutig steht und erlaubt ist (eine Stimmung mit dem Wort «Stimmung» davor, «Vorschau», eine Bildgrösse wie «1920 x 1080»), und sagt es dazu; wo zwei Werte genannt sind, ergänzt es nichts. Im selben Vorschlag hatte das Sprachmodell zusätzlich einen Stimmungs-Knoten in den Graph gelegt, doppelt zur Stimmung auf dem Auftrag; den lässt Visbox jetzt weg, ausser man bittet ausdrücklich um einen Knoten. Die Schlussantwort sagte «der Render wird dann ausgeführt» — falsch, denn gerechnet wird erst, wenn der Architekt am Render-Knoten freigibt; jede Antwort mit einem Render-Vorschlag sagt das jetzt. Und ohne Vorschlag darf keine Antwort mehr behaupten, ein Auftrag sei gestellt. Beim Schätzen der Hausfläche zählte die unterste Bildzeile über die ganze Breite als Haus, weil die Bodenprüfung dort nicht hinsah; das ist behoben, und Gründe ohne Fläche stehen nicht mehr in der Liste. Ehrlich gesagt: Hecken und Weg vor dem Haus zählen im nahen Bild weiter mit (56 % gegen 46 % von Hand). In der Tiefe allein sind sie nicht sicher von Sockel und Vordach zu trennen, und eine Regel, die sie abschneidet, schnitte auch diese ab — das wurde darum bewusst nicht gebaut. Am Heim-PC noch nicht nachgemessen.

**Der Assistent spricht zum Architekten, nicht zur Maschine (22.10.2026).** Die Nachmessung bestätigte die Arbeit vom Vortag: Was der Architekt nennt, kommt auf die Karte, jede Antwort mit Render-Vorschlag sagt, dass nur er freigibt, und die unterste Bildzeile zählt nicht mehr über die ganze Breite als Haus. Eine Regel liess sich nur mit einem nachgestellten Sprachmodell belegen, weil das echte diesmal einen anderen Weg nahm. Dabei fielen vier Sätze auf, die nicht für den Architekten geschrieben waren. Visbox weist einen falschen Handgriff des Sprachmodells zurück und sagt ihm, wie es richtig geht — diese Anleitung stand zweimal wörtlich in der Antwort an den Architekten. Jetzt liest er einmal in seinen Worten, was nicht vorgeschlagen wurde, und beim doppelten Stimmungs-Knoten den Satz, der es erklärt. Die Antwort nannte einen internen Werkzeugnamen («vis_render»); sie sagt jetzt «Rendern». Ein richtiger Satz wie «Der Render-Auftrag ist noch nicht gestellt» wurde gestrichen, weil die Prüfung auf das Wort «gestellt» ansprang; verneinte Sätze bleiben jetzt stehen. Ein Hinweis «weggelassen …» erschien zu einem Vorschlag, der gar nicht zustande kam; er steht jetzt nur noch beim Vorschlag, der wirklich hinausgeht. Wenn das Sprachmodell beim Lesen des Graphen eine Kennung rät, lässt Visbox sie weg und liest alle Graphen, statt einen der drei Versuche zu verbrauchen. Und die Antwort sagt durchgehend «der Architekt». Ehrlich gesagt: Hecken vor dem Haus zählen im nahen Bild weiter mit. Geprüft wurde ein Vorschlag, unterhalb des Blender-Bilds nur in dessen Breite weiterzuzählen; am gemessenen Bild hätte er auch ein Viertel des Vordachs und die ganze untere Fassade neben dem Eingang abgeschnitten, weil das KI-Bild das Haus fünfmal grösser zeigt als das Blender-Bild. Er ist darum nicht gebaut; eine Trennung nach Art (Pflanze oder Bauteil) folgt nach der Demo. Am Heim-PC noch nicht nachgemessen.

**Jeder Vorschlag wird genannt (22.10.2026).** Die Nachmessung bestätigte: Der Architekt liest keine Anleitungen an das Sprachmodell und keine internen Namen mehr, und ein verneinter Satz bleibt stehen. Drei kleine Dinge waren noch schief. Bat man um eine Vorschau in einer bestimmten Grösse, legte das Sprachmodell neben dem Render-Vorschlag einen zweiten Vorschlag an, der die Grösse am Knoten einstellt — keine Zeile der Antwort nannte ihn. Liegen jetzt zwei oder mehr Vorschläge vor, nennt Visbox jeden, den die Antwort noch nicht nennt. Beim Vereinheitlichen auf «der Architekt» wurde aus «der Bestätigung der Architektin» fälschlich «der Bestätigung dem Architekten»; Visbox unterscheidet jetzt Dativ und Genitiv. Und nach einem Gedankenstrich geht der Satz klein weiter. Am Heim-PC noch nicht nachgemessen.

**Auch «die Nutzerin» ist der Architekt (22.10.2026).** Die Nachmessung bestätigte die Arbeit davor. Das Sprachmodell schrieb diesmal «Warte auf die Bestätigung der Nutzerin» — gemeint ist der Architekt, und so steht es jetzt auch da. Liegen mehrere Vorschläge vor, nennt Visbox sie in einer einheitlichen Form und in der Mehrzahl. Am Heim-PC noch nicht nachgemessen.

**Zwei Vorschläge, sauber genannt (22.10.2026).** Die Nachmessung zeigte erstmals mit dem echten Sprachmodell eine Frage, die zwei Vorschläge ergibt — Auflösung einstellen und rechnen —, und die Antwort nennt beide. Ein Vorschlag stand dabei doppelt, weil das Sprachmodell ihn schon ohne Kennung erwähnt hatte, und der Schlusssatz sprach von «der Karte». Beides ist geglättet. Am Heim-PC noch nicht nachgemessen.

**Die schnelle Vorschau hält das Haus in seinem Umriss (22.10.2026).** Eine Woche vor der Vorführung lief die ganze Kette
einmal in einem Zug am Heim-PC — vom Laden des Modells bis zu den Fragen an den Assistenten. Ein Schritt war rot: Die
schnelle Vorschau malte neben das Haus anderthalbmal so viel Gebäude, wie das Haus selbst gross ist, und das Bild wirkte
verschmiert. Die Ursache lag in Visbox: Seit dem Vortag gilt für Varianten eine Einstellung aus zwei Teilen — der Baustoff
steht vorne in der Bildbeschreibung, und ausserhalb des Hauses bleibt das gerenderte Bild stehen. Die Vorschau bekam nur
den ersten Teil, und gerade dieser Teil allein lässt die KI noch mehr dazubauen. Jetzt bekommt auch die Vorschau beide.
Daneben: Der Satz, der sagt, dass das Bildmodell das gerenderte Bild nicht sieht, sagt jetzt genauer «im Haus» — ausserhalb
sieht es das Bild sehr wohl. Und das Ergebnis nennt, ob hinter dem Haus ein Himmelsbild oder ein Farbverlauf stand und welche
Sätze die Knoten an die Bildbeschreibung gehängt haben. Ehrlich gesagt: ohne Grafikkarte geprüft; wie die Vorschau damit am
Heim-PC aussieht, ist noch nicht gemessen. Nicht behoben ist ein Wolkenschleier, den die KI an einer Ansicht auf die
Fassade legte, und zwei Varianten mit fast gleicher Beschreibung sahen erwartungsgemäss fast gleich aus — für die
Vorführung sollte die zweite Variante etwas am Haus ändern, etwa den Baustoff.

**Die Knotenansicht zeigt nach dem Laden den richtigen Stand (22.10.2026).** In derselben Generalprobe fielen in der
Knotenansicht zwei Dinge auf, die den Architekten in die Irre geführt hätten. Erstens: Lädt man ein neues Modell, legt
Visbox dafür eine neue Mappe an — die Knotenansicht zeigte aber weiter die Knoten der vorigen Mappe, bis man die Seite neu
lud. Jetzt erscheinen sofort die Knoten der neuen Mappe, und hat sie noch keine, der fertige Anfang. Zweitens: Stellte man
die Kamera auf zwei Richtungen um, kündigte der Varianten-Knoten weiter drei Bilder an, und im Bildvergleich wäre eine
leere, «fehlgeschlagene» Zeile stehen geblieben. Bestellt wurde schon vorher richtig; jetzt sagt auch der Knoten, was
kommt. Geklärt, ohne etwas zu ändern: Am Render-Knoten steht «Himmel: keiner», obwohl der Himmel im Bild zu sehen ist. Das
ist eine alte Auswahl für einen gerechneten Himmel, die nicht mehr mitgeschickt wird; der Himmel im Bild kommt aus der
Stimmung, und die Bestellung aus der Knotenansicht ist dieselbe wie im Versuch. Die Zeile wird nach der Vorführung neu
gezeichnet. Bilder, die ein anderes Programm direkt beim Heim-PC bestellt, erscheinen nicht im Bildvergleich — er zeigt,
was in der Knotenansicht bestellt wurde. Ehrlich gesagt: ohne Grafikkarte geprüft; am Gerät noch nicht bestätigt.

**Die Grafikkarte gehört dem Bild (22.10.2026).** In der Generalprobe lag vor dem ersten Bild ein grosses Sprachmodell
eines anderen Programms auf der Grafikkarte des Heim-PCs — 22 GB. Das Bildmodell braucht rund 28 GB, die Karte hat 32.
Beides zusammen passt nicht. Es musste acht Minuten gewartet werden, bis das andere Programm sein Modell von selbst
herunternahm; und direkt nach einem Bild fand der Assistent der Visbox kaum Platz und antwortete erst nach fast drei
Minuten, weil er grösstenteils auf dem Hauptprozessor rechnete. Der Owner hat entschieden: In der Vorführung hat Visbox
Vorrang. Vor jedem Bild fragt Visbox jetzt das Programm, das die Sprachmodelle bereithält (Ollama), welche gerade auf der
Karte liegen, und nimmt alle herunter — auch das des anderen Programms auf demselben Rechner. Mehr tut sie nicht: Sie lädt
nichts, löscht nichts und stellt nichts um; das andere Programm lädt sein Modell bei der nächsten Frage von selbst wieder,
ebenso der Assistent. Läuft Ollama nicht oder antwortet es nicht, rechnet das Bild trotzdem. Im Ergebnis steht, welche
Modelle mit welcher Grösse freigegeben wurden und wie lange das dauerte. Ehrlich gesagt: ohne Grafikkarte geprüft, mit
einem nachgestellten Ollama; ob der Assistent danach wirklich auf der Karte rechnet, misst der nächste Versuch am Heim-PC.
Offen bleibt der zweite Teil des Befunds: Fragt man den Assistenten, während das Bildmodell nach dem Bild noch auf der Karte
liegt, kann er wieder zu wenig Platz finden — das betrifft diese Entscheidung nicht und wird zuerst gemessen.

**Varianten rechnen auf der Grundlage, die schon da ist, und lassen sich exportieren (22.10.2026).** Die Nachmessung am
Heim-PC bestätigte beides vom Vortag: Die Vorschau hält das Haus jetzt in seinem Umriss (nichts mehr daneben gebaut), und
die Knotenansicht zeigt nach dem Laden sofort die richtige Mappe. Auch die Grafikkarte wird vor dem Bild frei: Das grosse
Sprachmodell des anderen Programms war in 0,4 Sekunden herunter, das Bild rechnete allein, und der Assistent antwortete
danach in 12 statt 163 Sekunden. Die Kette lief ganz in der Knotenansicht durch, in rund 14 Minuten. Vier Dinge fielen auf
und sind behoben. Erstens: Der Varianten-Knoten liess für jede Bestellung das Bild aus Blender neu rechnen und wählte aus
drei Zufallswerten — gut dreieinhalb Minuten je Bestellung —, obwohl das Blender-Bild für genau diese Lage am Render-Knoten
schon lag. Jetzt nimmt er es mit und rechnet mit dessen einem Zufallswert, wie der Knopf «Variante erzeugen» am Render-Knoten.
Ändert die Variante etwas, das im Blender-Bild steckt — etwa den Baustoff —, rechnet sie wie bisher ihr eigenes. Zweitens: Der
Bildvergleich schrieb «Prüfung durchgefallen», wo die Prüfung in Wahrheit sagte «nicht beurteilbar» (das Haus füllt zu wenig
vom Bild, um es zu beurteilen). Der Fehler lag in Visbox: Je Ansicht stand nur «nein» da, ohne das Wort, das sagt, dass
«nein» hier «nicht entscheidbar» heisst. Drittens: Die Bilder der Varianten liessen sich nicht exportieren; jetzt trägt ihre
grosse Ansicht «Exportieren» wie jedes andere Bild, und der Dateiname nennt Mappe, Variante und Ansicht statt «Unbenannt».
Viertens: Nach «Freigeben» vergingen bis zu 30 Sekunden, bevor der Heim-PC zu rechnen begann — nicht weil er eine Runde
verlor, sondern weil er nur alle 30 Sekunden nachsah. Jetzt sieht er alle 10 Sekunden nach. Bewusst nicht gebaut, weil es
neue Bedienung wäre und erst gezeichnet werden muss: zwei Bestellungen nebeneinander im Bildvergleich (heute zeigt er die
letzte), die Varianten auch beim Kuratieren, und ein Werkzeug beim Kuratieren, das bei einem Aussenbild Innenraum-Bereiche
wie «Deckenholz» vorschlägt. Ehrlich gesagt: ohne Grafikkarte geprüft; am Gerät noch nicht bestätigt, und der neue Takt gilt
erst, wenn er am Heim-PC neu eingerichtet ist.

**Der Graph hatte sich nicht von selbst geändert — ein zweites Gerät arbeitete in derselben Mappe (22.10.2026, Befund am
Mac).** Ein Vorschlag von Claude («Stimmung morgen → abend») lag offen, niemand hatte ihn angenommen. Nach dem Wechsel zur
Startansicht und zurück stand im Graph «abend» — es sah aus, als hätte das Neuladen den Vorschlag still angewendet. Die
Prüfung ergab etwas anderes: Der Vorschlag hätte nur ein einziges Feld geschrieben; im Graph standen aber Werte in der Form,
die nur ein Klick am Knoten selbst schreibt, und dazu eine Kamera-Einstellung, die niemand vorgeschlagen hatte. Zur selben
Zeit bediente am Heim-PC ein Probelauf dieselbe Mappe und sicherte genau diese Werte; das Neuladen am Mac holte sie. Die
Spielregel — ein Vorschlag ändert nichts, bis jemand «Anwenden» drückt — hielt. Aufgefallen sind drei Lücken, die jetzt
geschlossen sind. Erstens: Eine offene Ansicht sieht nicht, was ein anderes Gerät sichert, und hätte es beim nächsten eigenen
Sichern still überschrieben; jetzt weist der Heim-PC ein Sichern auf veraltetem Stand ab, und die Ansicht sagt «ein anderes
Gerät hat geändert — neu laden». Zweitens: Die Ansicht sicherte in die Mappe, die *im Augenblick des Sicherns* am Heim-PC
zuletzt offen war; jetzt sichert sie in die Mappe, die sie gelesen hat, und ein offener Vorschlag gilt nur in seiner Mappe.
Drittens: Am Mac öffnete die Knotenansicht die Mappe, die irgendein Gerät zuletzt geöffnet hatte; nach der Entscheidung des
Owners merkt sich der Mac jetzt seine eigene und öffnet immer diese — Browser am Heim-PC und iPad bleiben, wie sie waren.
Nicht behoben, weil hier nicht messbar: Am Mac laufen einige Knoteninhalte schon bei normaler Schriftgrösse über ihren Rand;
das wird erst am Gerät gemessen.

**Die Zeitangabe am Varianten-Knoten stimmt jetzt mit der Rechnung überein (22.10.2026).** Die zweite Nachmessung am
Heim-PC bestätigte die Änderungen vom Vormittag: Eine Variante, die auf dem schon gerechneten Blender-Bild aufbaut, war in
92 statt 221 Sekunden fertig; der Bildvergleich sagt «nicht beurteilbar», wo die Prüfung nichts sagen kann; das Bild einer
Variante lässt sich mit sprechendem Namen exportieren und ist Bit für Bit das gerechnete; und nach «Freigeben» beginnt der
Heim-PC nach höchstens zehn Sekunden. Ein Fehler blieb: Der Varianten-Knoten kündigte für die zwei Bilder «ungefähr 3 min
2 s» an, weil seine Schätzung das Blender-Bild immer mitzählte. Jetzt fragt sie dieselbe Regel wie die Bestellung selbst:
Liegt das passende Blender-Bild schon da, zählt nur der KI-Schritt («ungefähr 1 min 34 s»), sonst kommen das Blender-Bild
und die Wahl aus drei Zufallswerten dazu («ungefähr 3 min 20 s», gemessen 194 und 205 Sekunden). Bewusst nicht geändert:
Eine Variante mit anderem Baustoff wählt weiter aus drei Zufallswerten. Das kostet gut eine Minute, aber eine frühere
Messreihe zeigt, dass ein einzelner Wurf das Haus manchmal deutlich verfehlt und die Wahl aus drei das im Mittel spürbar
verbessert. Drei weitere Beobachtungen sind kein Fehler: «Bild 1, Bild 2, Bild 3» am Bildvergleich sind seine drei
Anschlüsse, keine Spalten; der Hinweis «Grundlage veraltet» nach einem Baustoffwechsel gilt dem Knopf am Render-Knoten, der
dann wirklich gesperrt ist; und dass der Assistent im Browser am Heim-PC «nicht verbunden» sagt, ist gewollt — das Gespräch
führt die Visbox-App am Mac, damit das Kennwort nie durch die Webseite läuft. Ehrlich gesagt: Die neue Zeitangabe ist ohne
Grafikkarte geprüft und am Gerät noch nicht abgelesen.

**Beim Herauszoomen schrumpft die Schrift in den Knoten jetzt mit (22.10.2026).** Am Mac fiel dem Owner auf, dass die
Schrift in der Knotenansicht beim Zoomen anders wuchs als die Knoten selbst: Zog man die Ansicht klein, blieben die
Buchstaben gross, liefen über den Rand und wurden abgeschnitten — schon in der ersten Ansicht, weil diese meist etwas
herausgezoomt öffnet. Der Wunsch des Owners: Ein Knoten verhält sich wie eine Zeichnung, alles wird gemeinsam grösser
oder kleiner, und wer Einzelheiten lesen will, zoomt hinein. Die Ursache lag nicht in den Knoten, sondern in der Art,
wie die Ansicht zoomt: Sie setzte jeden Knoten in der neuen Grösse frisch, und dabei hält das Anzeigefenster am Mac eine
Mindestschrift von etwa 9 Pixeln ein. Der Rahmen schrumpfte, die Schrift nicht. Jetzt wird jeder Knoten beim
Herauszoomen einmal in Normalgrösse gesetzt und dann als Ganzes verkleinert, mit demselben Faktor für Rahmen, Schrift und
Bild; beim Hineinzoomen bleibt es beim frischen Setzen, damit die Knoten scharf bleiben. Ziehen und Verbinden treffen
dabei wie vorher, geprüft bei halber Grösse. Bewusst nicht geändert: Bei der Schriftgrösse «Gross» laufen einige Knoten
auch ohne Zoomen über, weil ihre Zeilen feste Höhen haben; das gehört zum Umbau der Knoten nach dem Entwurfsblatt
«Knoten im Massstab» und kommt nach der Demo. Ehrlich gesagt: Die Mindestschrift lässt sich hier im Testbrowser nicht
nachstellen; dass die Schrift am Mac jetzt mitschrumpft, zeigt erst der Blick am Gerät.

**Die Schrift klebt jetzt bei jeder Zoomstufe am Knoten (22.10.2026, Nachtrag).** Am Mac reichte der erste Schritt nicht:
Die Schrift zitterte beim Zoomen weiter und wechselte teils die Grösse. Diesmal wurde gemessen statt vermutet — jeder
Textblock in sechs Knoten, seine Zeilenzahl, Lage und Grösse im Verhältnis zum Knoten, bei halber, voller und doppelter
Grösse und Bild für Bild während einer Zwei-Finger-Geste um die volle Grösse herum. Vorher wichen 2600 Messwerte ab, und
drei Ursachen kamen heraus. Erstens setzte die Ansicht beim Hineinzoomen jeden Knoten bei jedem Zoomschritt neu, und dabei
rundet das Programm Breiten und Buchstaben jedes Mal etwas anders — eine Abkürzung verliert ein Zeichen, ein Knopf wird
breiter. Zweitens wechselte bei voller Grösse die Art des Zoomens, mitten in der Geste. Drittens sind die Kopfzeile und die
Namen der Anschlüsse als Vektorgrafik gezeichnet, und deren Text setzt das Programm in der Grösse, die er gerade am
Bildschirm hat — bei halber Grösse war «Prompt» im Verhältnis zum Knoten 8 % höher als bei voller. Jetzt gilt ein einziger
Weg: Die Knoten werden einmal gesetzt und beim Zoomen nur als Ganzes grösser oder kleiner gezogen, wie eine Zeichnung
unter dem Kopierer. Scharf wird es, wenn die Geste ruht: Dann zeichnet die Ansicht die Knoten einmal in doppelter (oder
drei-, vierfacher) Feinheit neu. Damit dabei nichts verrutscht, setzt sie die Buchstaben mit ihren genauen Breiten aus der
Schriftdatei, ungerundet — dann ist ein Wort in doppelter Feinheit genau doppelt so breit. Nach dem Umbau weicht kein
Messwert mehr ab, weder in der Ruhe noch mitten in der Geste; Ziehen und Verbinden treffen wie vorher. Ehrlich gesagt: Das
Anzeigefenster des Mac lässt sich hier nicht starten; geprüft ist im Testbrowser, und ob es am Mac genauso ruhig steht,
zeigt erst der Blick am Gerät.
**Wählt Claude eine Stimmung, gilt sie auch im Bild (22.10.2026).** Seit am Stimmungs-Knoten mehrere Stimmungen angehakt
werden können, speichert er die Wahl zweimal: als Liste und als einzelnen ersten Wert. Knoten, Prompt und Bestellung lesen
die Liste. Wählte Claude oder der Assistent eine Stimmung, wurde aber nur der einzelne Wert neu geschrieben — die Liste blieb.
War am Knoten vorher «Abendstimmung» angeklickt, meldete Claude danach «Morgenlicht», der Knoten zeigte weiter «Abend», und
gerendert worden wäre Abend. Jetzt gilt eine Regel an einer Stelle: Eine einzelne Stimmung ersetzt die ganze Wahl, wie ein
Klick; eine Liste gewinnt vor einem einzelnen Wert; beide werden immer zusammen geschrieben, und eine unbekannte Stimmung wird
abgewiesen statt still durch «Morgenlicht» ersetzt. Für Graphen, die schon widersprüchlich gespeichert sind, ist die
Lese-Regel festgelegt: Die Liste gewinnt — auch in dem, was Claude über den Graphen erfährt. Die Beschreibung des Werkzeugs,
die Claude liest, sagt jetzt genau das und kommt aus einer einzigen Quelle; eine Probe prüft, dass ihr Beispiel tut, was sie
verspricht. Ehrlich gesagt: Was der Mac-Test damals zeigte, hatte eine andere Ursache (die Ansicht zeigte den Graphen einer
anderen Mappe, siehe oben); die Lücke selbst war trotzdem echt und ist mit einer Probe belegt, die gegen den alten Stand rot
ist. Am Gerät ist die neue Regel noch nicht ausprobiert.

**Ein Vorschlag von Claude sagt jetzt, was er ändert (22.10.2026).** Beim Test am Mac stand derselbe Vorschlag zweimal
auf dem Bildschirm: oben als schmales Band mit «Ablehnen» und «Anwenden», dessen Text abgeschnitten war, und unten links
als Karte. Und die Karte sprach Programmiersprache: «Node-Parameter (preset, presets)» — man sah, *dass* Claude etwas ändern
wollte, aber nicht *was*. Der Owner entschied: Entschieden wird nur noch an der Karte unten links, und die Karte nennt Werte.
Jetzt steht dort «Stimmung: Morgenlicht → Abendstimmung» oder «Render-Knoten · Güte: Voll → Vorschau · Auflösung:
1600 × 1000 → 1920 × 1200», bei einem Paket aus mehreren Schritten eine Zeile je Schritt, beim Rechnen «Vorschau rechnen am
Render-Knoten (Freigabe durch den Architekten)». Oben bleibt nur der Satz «Claude wartet auf dich», ohne Knöpfe. Eine
Hürde lag im Detail: Das Programm schreibt den Satz erst, *nachdem* es die Änderung zur Probe ausgeführt hat — der alte Wert
war dann schon weg, und jede Karte hätte «Abendstimmung → Abendstimmung» gezeigt. Darum merkt sich das Programm den Stand,
den es vor der Änderung gelesen hat. Steht an einem Knoten noch gar nichts, nennt die Karte als alten Wert die Vorgabe, die
bis dahin galt. Was nicht in der Liste der bekannten Einstellungen steht, heisst «eine weitere Einstellung» statt eines
internen Namens. Ehrlich gesagt: geprüft in den Proben und auf einem Bildschirmfoto der Knotenansicht, am Mac noch nicht
angesehen. Bewusst später: dass die Pille «2 offen» pulsiert, wenn die Karten zugeklappt sind, und ein sichtbarer Schalter,
wie selbständig Claude arbeiten darf — beides wird zuerst gezeichnet.

**Am Render-Knoten gibt es keine stumme Sackgasse mehr beim Freigeben (22.10.2026).** Im Demolauf am Mac lag ein Bild-
Auftrag, den Claude vorgeschlagen hatte, am Render-Knoten und wartete auf die Freigabe. Die Mappe hatte noch keine
Grundlage; der Knoten riet «zuerst Grundlage rendern», doch genau dieser Knopf war gesperrt, solange der Auftrag wartete.
Ein Klick auf «Freigeben» tat nichts und sagte nichts. Erst nach dem Abbrechen ging es weiter. Zwei Dinge wurden geändert.
Erstens sagt der Knoten jetzt in jedem Fall, warum «Freigeben» nichts bewirkt hat und was zu tun ist — statt still
stehenzubleiben. Zweitens sperrt ein Auftrag, der nur auf die Freigabe wartet und nichts rechnet, «Grundlage rendern»
nicht mehr; ein Klick darauf bricht den wartenden Auftrag ab und bestellt die Grundlage. Bewusst nicht geändert: Der
vorgeschlagene Auftrag selbst war nicht falsch. Ein Bild in einem Schritt, ohne Grundlage, ist für Vorschläge von Claude
ausdrücklich vorgesehen; er hätte nach der Freigabe gerechnet. Ehrlich gesagt: Welcher der stillen Wege am Mac zuschlug,
liess sich ohne das Gerät nicht feststellen; die Änderung deckt alle, und am Mac ist sie noch nicht ausprobiert.

**Drei Funde aus einem Demolauf am Mac (22.10.2026).** Ein Probelauf mit einem Demohaus zeigte drei Dinge. Erstens stand
am Render-Knoten direkt nach «Freigeben» «nicht abgeholt (Grund unbekannt)» — und Sekunden später begann der Heim-PC zu
rechnen. Der Heim-PC schaut nur alle zehn Sekunden nach neuen Aufträgen; die Meldung war also eine Vermutung, keine
Beobachtung. Jetzt steht drei solche Takte lang «wartet auf den Heim-PC …», und erst danach die alte Meldung. Zweitens
schwebte das Haus im Bild: Das Demohaus hat kein Gelände, und Visbox legt bewusst keinen eigenen Boden darunter. Einen
Ersatzboden einzubauen, berührt Tiefe, Maske und Bildausschnitt; das ist keine Änderung für die Woche vor der Demo.
Empfohlen ist, das Gelände im Modell zu zeichnen — so, wie es der Grundsatz «möglichst viel modelliert» ohnehin verlangt.
Drittens wirkten die Fenster leer. Dabei fiel eine echte Lücke auf: Wer für die Fenster eine Holztextur wählte, bekam sie
auch auf die Scheibe; jetzt bekommt sie nur der Rahmen, das Glas bleibt Glas. Warum die Fenster hier leer wirkten, ist
damit noch nicht beantwortet — klares Glas vor einem dunklen Innenraum sieht aus wie ein Loch. Ehrlich gesagt: Ob das
Himmelsbild bei diesem Lauf ankam und ob die Modelldatei Glas trägt, lässt sich nur am Heim-PC an den echten Dateien
prüfen; dafür liegt ein Messauftrag bereit. Bei einem früheren Lauf derselben Art kam der Himmel nachweislich an.
**Ein Vorschlag zum Rechnen bleibt beim Architekten, und die Skizze hat ihren Knopf (22.10.2026).** Beim Durchlauf «Skizze
vom iPad bis zum Bild» am Mac kam ein Rechenauftrag, den Claude vorgeschlagen hatte, als «vom Architekten angewendet»
zurück, obwohl niemand etwas angewendet hatte. Der Vorschlag selbst war richtig als Karte gelegt; aber die Zeile oben in
der Mitte trug denselben «Anwenden»-Knopf, und die eigene Maus der KI durfte dort klicken. Jetzt ist diese Zeile für die
Maus gesperrt wie die Karte; der Auftrag wartet danach ohnehin am Knoten auf «Freigeben». Drei weitere Stellen sagten nicht,
was los ist: Claude las beim Nachschauen die Mappe des Heim-PC statt der, die am Mac offen war, und fand die Skizze nicht;
mit Skizze war der Knopf für das KI-Bild gesperrt, weil er eine Grundlage verlangte, die eine Skizze gar nicht braucht —
er heisst jetzt «Bild aus Skizze erzeugen» und schickt die Skizze; und Fehler standen als Zahl («400») statt als Satz da.
Ehrlich gesagt: Die Ursache der Zahl ist damit nur sichtbar, nicht behoben. Eine Skizze, die das iPad in eine Mappe *am Mac*
legt, liegt nicht am Heim-PC, der rechnet — er weist sie ab. Mit einer Mappe des Heim-PC geht der Weg; für eine Mappe am Mac
muss die Skizze erst mitgenommen werden, und das kommt nach der Demo. Am Gerät ist keiner dieser Punkte ausprobiert.


**Woher Dach, Fenster und Farbe fehlten (22.10.2026).** Die Nachmessung am Heim-PC zeigte: Die Modelldatei des Demolaufs
hatte gar kein Dach, keine Fenster (nur die Löcher in den Wänden) und keine Farben — sie stammte aus einem älteren Export.
Visbox hatte umgewandelt, was da war; nichts ging unterwegs verloren. Beim Nachprüfen mit einer eigenen Testdatei, die Dach,
Fenster, Tür und Glas enthält, fielen trotzdem drei Lücken der Umwandlung auf, und sie sind geschlossen: Eine Dachplatte, die
in der Datei als Teil eines Dachs eingetragen ist, wurde bisher wie ein Boden behandelt und bekam das Bodenmaterial — jetzt ist
sie Dach. Eine Glasscheibe kam als hellgraue Platte an — jetzt kommt sie als Glas, durch das man hindurchsieht, und für die
Prüfung der Form bleibt sie trotzdem eine Fläche. Ein Gelände, das die Datei am Grundstück selbst trägt, wird jetzt als Boden
erkannt. Und weil der Fehler diesmal erst im Bild sichtbar wurde, sagt die Umwandlung jetzt beim Laden in einem Satz, wenn
einer Datei Dach, Fenster oder Farben fehlen. Ehrlich gesagt: Hier lief die Umwandlung mit einer neueren Fassung der
Hilfsbibliothek als am Heim-PC und ohne das Rendering; die Bestätigung dort steht noch aus. Der dunkle Abendhimmel ist
eingeordnet, aber nicht geändert: Er wird bewusst dunkler als das Haus gestellt, und ein Haus mit offenen Löchern und ohne Dach
misst dunkel — zuerst wird mit einem vollständigen Modell nachgemessen.

**Eigene Zeichen für Visbox (22.10.2026).** Oben links in der Knotenansicht stand bisher ein fremdes Zeichen, eine Spirale, und
unten rechts war der Knopf zum Assistenten eine rote Kugel. Beide stammen aus der Vorlage, aus der die Knotenansicht übernommen
ist. Jetzt trägt Visbox seine eigenen: oben links das Logo von Visbox — dieselbe Box wie im App-Symbol —, und unten rechts ein
Senklot an der Schnur in einer leicht blauen Glaskachel. Das Lot ist das Werkzeug, mit dem man am Bau prüft, was wirklich
senkrecht ist; es passt zur Regel des Assistenten, nichts zu behaupten, was nicht ist. Rechnet der Assistent, pendelt das Lot
sanft; wer in den Einstellungen weniger Bewegung wünscht, sieht es still hängen. Getauscht ist nur das Zeichen: Wo der Knopf
steht, was ein Klick tut und wie der Assistent heisst und spricht, bleibt bis zur nächsten grösseren Fassung gleich. Am Mac ist
der Tausch noch nicht angesehen.

**Eine Mappe am Mac bekommt ihr Modell (22.10.2026).** Im Probelauf mit dem «Haus am Hang» wurde eine Mappe am Mac neu
angelegt und ein Modell hineingeladen. Gewandelt wird das Modell am Heim-PC, weil dort die Hilfsprogramme liegen; danach
soll es in die Mappe am Mac zurückkommen. Es kam nicht: Die Mappe zeigte null Bauteile, «Grundlage rendern» blieb gesperrt,
und am Heim-PC lag eine zweite Mappe gleichen Namens, die man ein zweites Mal an den Mac holen konnte. Die Ursache war ein
einzelner fehlender Eintrag in der Wegliste des Mac-Programms: Der Schritt «hol das Modell in die offene Mappe» galt dort als
unbekannte Datei, und die Antwort «gibt es nicht» las die Knotenansicht als «hier ist keine Mappe am Mac» — sie tat darum
nichts und sagte nichts. Jetzt kommt das Modell mit seiner Auswertung in genau die Mappe, aus der geladen wurde, und die
Mappe merkt sich ihren Zwilling am Heim-PC; er erscheint nicht mehr als zweite Mappe. Im selben Lauf fehlte ein Bild einer
Variante am Mac, obwohl es am Heim-PC fertig war. Bilder kamen bisher nur, wenn die Knotenansicht im richtigen Augenblick
nachfragte; lud sie zwischendurch neu, fragte niemand mehr. Jetzt fragt das Mac-Programm beim Öffnen einer Mappe selbst nach
fertigen Bildern, die ihr noch fehlen, und versucht jedes mehrmals. Ehrlich gesagt: Ob genau dieser Grund das eine Bild
verlor, lässt sich ohne Aufzeichnung des Laufs nicht beweisen; geschlossen ist die Lücke, durch die es verloren gehen kann.
Am Mac ist beides noch nicht nachgeprüft.

**Eine Variante behält ihre Stimmung, ein Baum sein Material (22.10.2026).** Im Probelauf mit einem Haus am Hang kam die
Variante «Mittag» als blaue Nacht zurück. Sie hatte auf dem schon gerechneten Abend-Grundbild gemalt — und weil Visbox
ausserhalb des Hauses das Grundbild festhält, damit die KI keine Nachbarhäuser dazuerfindet, blieben Himmel und Boden vom
Abend stehen. Wo die Bestellung ein Licht trug, wurde der Satz «Mittag» sogar still durch den des Abends ersetzt. Jetzt gilt:
Nennt eine Variante eine andere Stimmung als ihr Grundbild, rechnet Visbox für sie ein eigenes Grundbild mit dem passenden
Himmel; das dauert länger als eine Variante, und das Bild sagt es in einem Satz. Im selben Lauf lag die gewählte Holzlattung
auch auf Beton, Bäumen und Terrasse, weil die Datei ihren Teilen keine Rolle mitgab und alles als «übrige» galt. Jetzt liest
Visbox zuletzt den Namen eines Teils («Aussenwand», «Satteldach»), und ein Teil, über das die Datei gar nichts sagt, behält
sein Material, sofern es einen sprechenden Namen trägt. Glas kommt glatt ins Bild statt als mattes Milchglas, und der Bericht
trennt jetzt «diese Art gibt es im Modell nicht» von «es gibt sie, aber alles blieb wie in der Datei» — beides gewollt, keines
ein Fehler. Ehrlich gesagt: Am Rechner mit Grafikkarte ist keiner dieser Punkte gesehen; die Messung steht aus. Der helle Saum,
der beim KI-Bild ohne Variante rund ums Haus lag, ist nur eingeordnet — vermutlich malt die KI im schmalen freien Band um das
Haus ihren eigenen, helleren Himmel; er wird zuerst gemessen.

**Die Karte sagt, was angewendet wird, und ein volles Bild zählt als Grundbild (22.10.2026).** Drei Befunde aus der
Prüfliste am Mac. Erstens schlug der Assistent am Stimmungs-Knoten «Morgenlicht» vor; die Karte, das Band oben und die
Rückmeldung nach dem Anwenden sagten aber «Abendstimmung». Angewendet wurde richtig Morgenlicht. Der Knoten kann mehrere
Stimmungen tragen; ein Vorschlag mit nur einer ersetzt die ganze Wahl — so rechnet das Programm, nur der Satz auf der Karte
mischte die neue Stimmung in die alte Liste und las dann die alte. Jetzt leitet die Karte den neuen Wert nach derselben Regel
ab wie das Anwenden. Zweitens blieb nach einem Auftrag, der für vier Standpunkte Grundbild und KI-Bild in einem rechnete, am
Knoten der Satz «Grundlage veraltet — erst neu rendern» stehen. Ein solcher Auftrag rechnet dabei auch ein neues Grundbild,
und der Heim-PC meldet es; der Knoten merkte sich aber nur Grundbilder aus dem eigenen Knopf «Grundlage rendern». Jetzt gilt
auch das Grundbild eines vollen Auftrags, und «Variante erzeugen» ist danach sofort frei. Drittens war die Datei, in der der
Heim-PC alle Messwerte eines Auftrags ablegt, 93 MB gross. Darin stand für jeden Standpunkt eine Liste mit einem Ja/Nein je
Bildpunkt (wo das Haus ist, wo die Umgebung), jeder Wert auf einer eigenen Zeile, und eine davon doppelt. Gelesen hat diese
Listen aus der Datei niemand. Jetzt stehen in der Datei nur noch die Zahlen und ein Verweis, die Listen liegen gepackt — ein
Bit je Bildpunkt — in einer Datei daneben und lassen sich verlustfrei zurückholen. Ehrlich gesagt: Zum Mac reist diese Datei
auf keinem Weg; das eine fehlende Grundbild im selben Auftrag erklärt sie nicht. Das holt seit dem vorigen Schritt das
Nachholen beim Öffnen der Mappe. Am Mac ist keiner der drei Punkte nachgeprüft.

**Der Himmel passt zur Stimmung (22.10.2026).** Die Messung am Rechner mit Grafikkarte bestätigte die Schritte davor: Eine
Variante «Mittag» bekommt ihr eigenes Grundbild, Bauteile ohne Angabe behalten ihr Material, Glas ist glatt, das Haus steht
auf dem Gelände. Aber der Mittagshimmel war dunkles Nachtblau — und zwar schon im Bild aus Blender, nicht erst im KI-Bild.
Die Ursache lag in einer älteren Regel: Sie stellt den Hintergrund eine Blendenstufe dunkler als das Haus, damit es sich
abhebt. Gebaut war sie für einen ruhigen, erfundenen Farbverlauf hinter dem Haus. Seit die Kamera das echte Himmelsfoto der
Stimmung sieht, dunkelte dieselbe Regel den Himmel ungebremst ab, beim Abend bis fast schwarz; dazu startete der Himmel schon
gedämpft, weil er an die Stärke des Aufhelllichts gekoppelt war. Jetzt ist die Regel für den sichtbaren Himmel begrenzt: Bei
Morgen, Abend und Blauer Stunde darf der Himmel höchstens eine Blendenstufe dunkler werden — so weit, wie die Regel ihn vom
Haus wegrücken will, nicht weiter. Bei Mittag, Bedeckt, Nebel und Winter steht er mindestens so hell, wie die Stimmung ihn
liefert. Ohne sichtbaren Himmel rechnet alles wie vorher. Dazu vier kleine Korrekturen: Schon glattes Glas wird nicht mehr
als «geglättet» gezählt, das Gelände des Zeichenprogramms wird am Namen erkannt, Öffnungen ohne Angabe werden als Fenster
erkannt (Türöffnungen nicht), und «Haus am Hang» wird ganz übersetzt. Ehrlich gesagt: Ein hellerer Himmel kann das Haus
weniger abheben; ob es sich bei Mittag weiter klar abhebt, misst der nächste Auftrag am Rechner mit Grafikkarte.
