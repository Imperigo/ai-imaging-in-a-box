# 3 · Die Randbedingungen sind der Entwurf

> **Stand 19.09.2026 — Entwurf.** Zweites geschriebenes Kapitel dieser Arbeit.
> **Die Zahlen dieses Kapitels sind nicht zitiert, sondern erzeugt:** Jede stammt aus
> `tools/beweis/19_regeln_ausfuehrbar.py`, das am 19.09.2026 für dieses Kapitel gefahren
> wurde. Wer sie nachprüfen will, fährt dasselbe Skript.

---

## 3.1 Die These: Auflagen sind kein Rahmen, sondern ein Treiber

Softwarearbeiten behandeln Lizenz- und Betriebsauflagen üblicherweise als **Rahmen**:
etwas, das den Entwurf einschränkt, ohne ihn hervorzubringen. Man baut, was man bauen
will, und prüft hinterher, ob es erlaubt ist.

Diese Arbeit behauptet das Gegenteil. **Vier Auflagen standen fest, bevor eine Zeile
geschrieben war**, und die Architektur dieser Software ist aus ihnen hervorgegangen. Der
Nachweis ist nicht, dass die Software sie einhält — das wäre trivial —, sondern dass ihre
**Gestalt ohne sie eine andere wäre**, und zwar an benennbaren Stellen.

Die vier Auflagen im Wortlaut, wie sie am 14.08.2026 festgeschrieben wurden:

1. **Alles im ausgelieferten Produkt ist permissiv lizenziert.** MIT, Apache-2.0, BSD oder
   MPL-2.0. Kein GPL, kein AGPL — weder als Abhängigkeit noch als gebündelte Komponente.
   **Modellgewichte zählen mit.**
2. **Blender nur als externer Prozess, nie als Erweiterung.** Blender steht unter GPL; die
   saubere Grenze ist der Prozessaufruf, nicht der Import.
3. **Keine echten Projektdaten im Repo.** Keine Bürodaten, keine Kundenprojekte, keine
   Pläne oder Renders aus echten Aufträgen — auch keine Namen davon in Pfaden,
   Kommentaren oder Testdaten.
4. **Der Kern ist eine Bibliothek, ohne Oberfläche aufrufbar.** Was nur über einen Klick
   erreichbar ist, existiert nicht.

---

## 3.2 Regel 1 · Die Lizenz gehört in die Registry, nicht in eine Liste

**Was die Regel erzwungen hat.** Die naheliegende Umsetzung wäre eine Liste erlaubter
Modelle in der Dokumentation und ein Hinweis, sie einzuhalten. Genau das ist die Form,
die nichts prüft: *Ein Riegel prüft, ob jedes Element der Wirklichkeit in seiner Liste
steht — nicht umgekehrt.*

Gebaut wurde stattdessen eine **Registry mit Lizenzfeld**, und die Auswahlfunktion nimmt
die Lizenz als Argument. Ein gesperrtes Modell kann nicht ausgewählt werden, weil es die
Auswahl nicht verlässt. Gemessen am 19.09.2026:

| | |
|---|---|
| Einträge in der Registry | **8** |
| davon bei kommerzieller Nutzung wählbar | **6** |
| ausgeschlossen | **2**, darunter zwei Modelle mit Nicht-kommerziell-Lizenz |
| Ergebnis der Auswahlfunktion für ein gesperrtes Modell | es ist **nicht enthalten** |

**Die Stelle, an der die Regel schärfer wurde als geplant.** Bei einer Modellfamilie hängt
die Lizenz **an der Grösse**: Die kleine Fassung ist frei verwendbar, die grosse nicht.
Ein Eintrag, der durch Abschreiben des Nachbarn entsteht, erbt dabei das falsche
Lizenzfeld — und der Datensatz behauptet dann etwas Falsches, das jede Prüfung bestätigt,
die nur den Datensatz liest.

Der gebaute Riegel steht darum **über** dem Datensatz: Eine Tabelle im Quelltext nennt je
Familie die freigegebenen Grössen, und sie gewinnt gegen das Lizenzfeld des Eintrags.
Zusätzlich wird die Grössenangabe gegen die Bezeichner geprüft; widersprechen sie
einander, wird der Eintrag **abgewiesen** statt auf die freundlichere Lesart zugeschlagen.

**Und die Grenze steht daneben**, weil sie zur Sache gehört: Die Familienerkennung hängt
an den Bezeichnern des Eintrags. Wer **beide** umschreibt, kommt durch. Beide Spuren zu
lesen *halbiert* die Lücke; es schliesst sie nicht. Geschlossen würde sie nur durch eine
Angabe ausserhalb des Eintrags — die Grösse der Gewichte auf der Platte —, und diese
Messung ist bestellt und steht aus.

---

## 3.3 Regel 2 · Die Prozessgrenze, die dem System auch technisch guttut

**Was die Regel erzwungen hat.** Blender als Erweiterung zu betreiben wäre der bequeme
Weg: Man hätte die Modelldaten im selben Speicher, kein Serialisieren, keine
Zwischendateien. Die GPL macht das unmöglich, ohne das ganze Produkt anzustecken.

Gebaut wurde darum eine **Prozessgrenze**: Blender wird als Programm aufgerufen, die
Übergabe läuft über Dateien, und das Ergebnis kommt als Bericht zurück. Dasselbe gilt für
die Bibliothek, die Gebäudemodelle liest — sie lebt in einer eigenen Umgebung und wird nie
importiert.

Gemessen am 19.09.2026 in einem frischen Interpreter, nach einem vollständigen Kettenlauf:

| | |
|---|---|
| Modellgeometrie eingelesen | **5 Bauteile**, Hüllbox 8 × 5 × 3,25 m |
| IFC-Bibliothek im Produktprozess geladen | **nein** |
| Blender-Modul im Produktprozess geladen | **nein** |

**Und hier zeigt sich die These am deutlichsten.** Die Prozessgrenze war eine
Lizenzauflage; sie hat sich als technisch überlegen erwiesen:

* **Der Kern läuft ohne jede schwere Abhängigkeit.** Die gesamte Testsammlung — über 6300
  Proben — fährt ohne Grafikkarte, ohne Blender und ohne Modellgewichte durch. Das ist
  nicht Sparsamkeit, sondern eine Folge der Grenze: Was jenseits von ihr liegt, muss
  diesseits attrappierbar sein.
* **Ein Absturz jenseits der Grenze bringt den Kern nicht um.** Blender kann am Compositor
  scheitern, ohne dass die Software abstürzt — sie liest einen Bericht und urteilt.
* **Die Komponente ist austauschbar.** Ein anderes Renderprogramm wäre ein anderer
  Prozessaufruf, kein Umbau.

*Die Auflage hat eine Entwurfsentscheidung erzwungen, die man auch ohne sie hätte treffen
sollen — und die ohne sie vermutlich nicht getroffen worden wäre.*

---

## 3.4 Regel 3 · Die Stelle, an der eine Regel etwas kostet

**Was die Regel erzwungen hat.** Alle Testdaten dieser Arbeit sind **synthetisch und im
Repo erzeugbar**. Es gibt ein Werkzeug, das Gebäudemodelle erzeugt — einen Quader und
einen fünfgeschossigen Bau, wahlweise mit Gelände —, und jede Messung dieser Arbeit läuft
an ihnen.

Gemessen am 19.09.2026, über alle versionierten Textdateien:

| | |
|---|---|
| geprüfte Dateien | **685** |
| Treffer auf Kunden-, Büro- oder Projektnamen | **0** |

Das ist ein Wächter, kein Versprechen: Er läuft bei jedem Testlauf mit.

**Der Preis.** Am 11.09.2026 bot die Messmaschine die Bildebenen eines laufenden
Renderprojekts an — 121 Megabyte, darunter **genau der Tiefenanker mit belegtem
Wertebereich, der dieser Arbeit fehlt**. Er hätte eine offene Frage in Stunden
geschlossen.

Abgelehnt, weil dieses Repo öffentlich ist.

> *Die Stelle, an der eine Regel etwas kostet, ist die, an der sie gilt.*

Dieser eine Fall ist der beste verfügbare Beleg dafür, dass die Randbedingungen dieser
Arbeit nicht nachträglich zurechtgelegt wurden. Eine Regel, die nie etwas verhindert hat,
ist von einer Absichtserklärung nicht zu unterscheiden.

**Was die Regel zusätzlich erzwungen hat, und es war nicht vorhergesehen:** Weil kein
echtes Gebäudemodell im Repo liegen darf, musste ein Erzeuger dafür gebaut werden. Dieser
Erzeuger ist heute die Grundlage jeder reproduzierbaren Messung dieser Arbeit — *eine Zahl,
die in einem Dokument steht und nicht nachgebaut werden kann, ist eine Behauptung.* Ohne
Regel 3 gäbe es ihn vermutlich nicht.

---

## 3.5 Regel 4 · Was nur über einen Klick erreichbar ist, existiert nicht

**Was die Regel erzwungen hat.** Die Oberfläche ist eine dünne Schicht über der
Bibliothek, nie deren Voraussetzung. Jede Fähigkeit muss aus Python heraus nutzbar sein,
ohne dass eine Oberfläche läuft.

Gemessen am 19.09.2026, frischer Interpreter, einfacher Import des Kerns:

| | |
|---|---|
| geladene Module | **167** |
| davon verbotene Marker (Oberflächen-Rahmenwerke, Blender, schwere Rechenbibliotheken) | **0 von 13** |

**Die Folge, die man erst im Betrieb sieht.** Diese Regel ist der Grund, warum diese
Arbeit überhaupt messbar ist. Ein Verfahren, das nur über eine Oberfläche läuft, kann man
vorführen; man kann es nicht in einem Testlauf sechstausendmal durchrechnen.

Sie hat auch etwas gekostet: Die Bedienung dieser Software ist heute unbequem. Es gibt
keinen Befehl, den man in ein Terminal tippt; man ruft eine Funktion auf. Das ist für
einen Prototyp vertretbar und für ein Produkt nicht — es steht im Ausblick und nicht in
den Ergebnissen.

---

## 3.6 Was die vier Regeln zusammen bewirkt haben

Die vier Auflagen sind unabhängig voneinander entstanden. Ihre Wirkung ist es nicht.

**Alle vier drängen in dieselbe Richtung: Trennung.** Die Lizenzregel trennt, was
ausgeliefert wird, von dem, was aufgerufen wird. Die Blender-Regel trennt Prozesse. Die
Datenregel trennt Testdaten von echten. Die Bibliotheksregel trennt Fähigkeit von
Bedienung.

Was daraus entstanden ist, ist eine Software, deren Teile **einzeln prüfbar** sind — und
das ist die Voraussetzung dafür, dass diese Arbeit überhaupt Messwerte vorlegen kann. Eine
Software, in der Modelllizenz, Rendering, Testdaten und Bedienung ineinandergreifen, hätte
dieselbe Frage nicht beantworten können, weil man ihre Teile nicht hätte einzeln befragen
können.

> **Die Randbedingungen haben den Entwurf nicht eingeschränkt. Sie haben ihn erzeugt.**

---

## 3.7 Grenzen dieses Kapitels

**Erstens: Die Belege sind ausführbar, aber sie laufen hier.** Alle Zahlen dieses Kapitels
stammen von einer Linux-Maschine ohne Grafikkarte. Ein Teil der Prüfung zu Regel 2 — der
Nachweis, dass das Blender-Modul auch bei einem echten Renderlauf nicht in den
Produktprozess gerät — wird auf dieser Maschine **übersprungen** und ist auf der
Messmaschine belegt. Die Zahl steht mit diesem Vorbehalt da.

**Zweitens: «Keine GPL im Produkt» ist geprüft, nicht bewiesen.** Geprüft sind die direkten
Abhängigkeiten und die Modellgewichte. Die Prüfung der indirekten Abhängigkeiten einer
optionalen Komponente steht ausdrücklich aus — sie zieht 19 weitere nach sich, und sie
sind **nicht einzeln geprüft**. Die Komponente ist darum optional: Der Kern läuft ohne sie.

**Drittens: Die These ist nicht widerlegbar formuliert.** Dass die Architektur ohne diese
Regeln anders aussähe, lässt sich nicht beweisen — es gibt keine zweite Fassung dieser
Software, die ohne sie entstanden wäre. Was gezeigt werden kann, ist das Schwächere: dass
jede der vier Regeln eine benennbare Entscheidung erzwungen hat, und dass mindestens eine
davon etwas gekostet hat.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Die vier Regeln im Wortlaut | `CLAUDE.md` |
| Alle Zahlen dieses Kapitels | `tools/beweis/19_regeln_ausfuehrbar.py` (ausführbar) |
| 3.2 Lizenzampel | `src/aiimaging/backbone.py`, `docs/LIZENZPRUEFUNG_2026-08-18.md` |
| 3.3 Prozessgrenze | `src/aiimaging/seams.py`, `tests/test_prozessgrenze.py`, `NOTICE` |
| 3.4 Der Preis | `auftraege/offen/auf-20260911-106.json` |
| 3.5 Bibliothek ohne Oberfläche | `tests/test_regel4_bibliothek.py` |
