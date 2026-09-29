# 3 · Die Randbedingungen sind der Entwurf

> **Stand 29.09.2026 — Entwurf** (geschrieben 19.09.2026, nachgezogen 29.09.2026).
> Zweites geschriebenes Kapitel dieser Arbeit.
> **Die Zahlen dieses Kapitels sind nicht zitiert, sondern erzeugt:** Jede stammt aus
> `tools/beweis/19_regeln_ausfuehrbar.py`, das am 19.09.2026 für dieses Kapitel gefahren
> wurde. Wer sie nachprüfen will, fährt dasselbe Skript.
> **Nachtrag 29.09.2026:** Das Skript ist am 29.09.2026 erneut gefahren (Codestand
> `d93bab2`). Die alten Zahlen bleiben stehen; die neuen stehen jeweils darunter. Drei
> Dinge haben sich seither geändert, und zwei davon sind unbequem: Regel 1 hat eine
> **Forschungs-Ausnahme** bekommen (3.2), die Zahl «0 Treffer» zu Regel 3 hat **mehr
> behauptet, als ihr Wächter prüft** (3.4), und an der Dateigrenze von Regel 2 ist ein
> eigener Lesefehler beim Glas gefunden worden (3.3).

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

> **Nachtrag 29.09.2026 — die Registry am selben Skript, zehn Tage später:**
>
> | | 19.09.2026 | 29.09.2026 |
> |---|---|---|
> | Einträge in der Registry | 8 | **9** |
> | davon bei kommerzieller Nutzung wählbar | 6 | **3** |
> | ausgeschlossen | 2 | **6** |
>
> Die Verschiebung kommt aus drei Entscheiden, und keiner davon hat eine Lizenz geändert:
>
> * **22.09.2026:** SDXL und SD3.5 tragen eingeschränkte Lizenzen, die seit dem 18.08.2026
>   als offene Frage gemeldet wurden. Owner-Entscheid: **nur zum Messen, nie
>   ausgeliefert** — umgesetzt im Urteil (`pruefe_lizenz`) **und** in der Auswahl
>   (`waehle`), weil ein Entscheid, der nur im Urteil steht, über die Auswahl trotzdem ins
>   Produkt käme.
> * **29.09.2026:** `qwen-image-2512` ist **stillgelegt** (neues Feld
>   `Backbone.stillgelegt`, mit Begründung). Die Lizenz ist frei; der Weg fiel, weil das
>   Grundmodell 48 GB braucht und die Herkunft, Lizenz und Form seiner Tiefensteuerungs-Datei
>   auf der Messmaschine ungeklärt war. Folge: **An der Tiefen-Naht bleibt genau ein freies
>   Modell** (`z-image-turbo`).
> * **29.09.2026:** Ein neunter Eintrag, `qwen-image-2.1`, unter einer Forschungslizenz —
>   siehe unten.
>
> **Die Forschungs-Ausnahme — Regel 1 hat zum ersten Mal nachgegeben.**
>
> Am 29.09.2026 hat der Owner entschieden, das Bildmodell Qwen-Image-2.1 für die
> Vertiefungsarbeit **rechnen** zu lassen, obwohl seine Lizenz («Qwen Research License
> Agreement», «for research or evaluation purposes only») nach Regel 1 ausgeschlossen ist.
> Begründung des Owners: *«Wir sind noch lange nicht im Verkauf … sobald es zum Verkauf
> geht, gibt es sowieso neue Versionen.»* Auf die Rückfrage, dass das Regel 1 widerspricht,
> wurde die Form gewählt, die heute in `CLAUDE.md` als **Präzisierung Forschungsmodelle**
> steht — mit vier Auflagen:
>
> 1. nur am Heimrechner und nur mit Schalter (`AIIMAGING_FORSCHUNGSMODELLE=1`, für einen
>    Messlauf, nie dauerhaft);
> 2. nie Vorgabe, nie bestellbar — auch nicht über den Bestellweg von KosmoOrbit;
> 3. markiert — jeder Lauf trägt `nur_forschung`, `pruefe_lizenz` sagt weiter «nicht im
>    Produkt»;
> 4. vor einem Verkauf entfernt oder lizenziert, auch darauf trainierte LoRAs.
>
> **Was daran zur These dieses Kapitels passt:** Auch die Ausnahme ist als Code gebaut und
> nicht als Satz — ein Feld am Registereintrag (`Backbone.nur_forschung`, nur bei nicht
> verkaufbaren Einträgen eintragbar), ein Schalter und eine eigene Ladefreigabe
> (`backbone.ladefreigabe`), die dieselbe Antwort gibt wie `pruefe_lizenz`, ausser für genau
> diesen Eintrag bei gesetztem Schalter. Die Ausnahme gilt je Eintrag, nicht für alles
> Nicht-Kommerzielle: FLUX.1-dev und FLUX.2-dev bleiben ausgeschlossen.
>
> **Was nicht dazu passt, und es gehört hierher:** Die Regel ist hier einem konkreten Modell
> gewichen, nicht umgekehrt. Eine Lizenzanfrage für die kommerzielle Nutzung ist
> geschrieben (`docs/lizenzanfragen/2026-09-29_qwen-image-2-1.md`), aber nicht versandt und
> zurückgestellt. Ob das Modell auf der Messmaschine überhaupt läuft und die Geometrie
> trägt, ist **nicht gemessen** — bestellt als `auf-20260929-178`. Siehe auch 3.7, Viertens.

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

*Nachtrag 29.09.2026:* Dasselbe Skript, erneut gefahren — unverändert: 5 Bauteile,
IFC-Bibliothek nicht geladen; der Blender-Teil wird auf dieser Maschine weiterhin
übersprungen (siehe 3.7).

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

*Nachtrag 29.09.2026 zur Zahl der Proben:* «über 6300» war der Stand vom 19.09.2026; am
29.09.2026 sind es **8379**, weiterhin ohne Grafikkarte (Zahl im `README.md`, dort selbst
unter einem Wächter).

### Nachtrag 29.09.2026: Was über die Grenze geht, ist eine Datei — und wir haben sie halb gelesen

Die Prozessgrenze hat eine Folge, die im Entwurf oben fehlt: **Was zwischen den Prozessen
liegt, ist eine Datei, und ihr Inhalt ist der eigentliche Vertrag.** Am Glas ist das zweimal
sichtbar geworden.

* **24.09.2026:** Die Ausfuhr von KosmoOrbit schreibt Glas mit Deckkraft 0,25 **und**
  Durchlass (`KHR_materials_transmission`) 1. Blender macht aus beidem etwas, und rund
  drei Viertel der Strahlen laufen ungebrochen hindurch. Die Antwort an KosmoOrbit war
  darum kein neues Feld und keine Rendereinstellung, sondern: das Material in ihrer Datei
  deckend (OPAQUE, Deckkraft 1) mit Durchlass ausführen. Eine eigene Glas-Regel im
  Renderaufruf wurde **bewusst nicht** gesetzt, weil sie auch unsere Tiefenkarten und damit
  die Geometrieprüfung verändert hätte — erst messen.
* **29.09.2026, und der Fehler war unserer:** KosmoOrbit hat diesen Vorschlag angenommen,
  **unter der Bedingung**, dass unsere Transparenz-Prüfung Durchlass mitzählt. Nachgesehen:
  Sie tat es nicht. Sie zählte nur Materialien mit `alphaMode: BLEND`. Das Glas, das
  KosmoOrbit künftig liefern will, wäre bei uns als «keine durchsichtigen Materialien»
  gemeldet worden. Behoben am selben Tag (`modellstand._durchlass`, zwei Proben in
  `tests/test_modellstand.py`); im Einbau-Stand als C33 *gebaut, am Gerät unbestätigt*.

*Gefunden, weil die Gegenseite es als Bedingung gestellt hat — nicht, weil wir es gesucht
hätten.* Für die These heisst das: Die Grenze trennt die Programme sauber, aber sie
verschiebt die Frage von «welche Funktion wird aufgerufen?» zu «lesen beide Seiten
dieselbe Datei gleich?». Diese zweite Frage prüft kein Import-Wächter.

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

> **Berichtigt 29.09.2026 — die Zeile «Treffer auf Kunden-, Büro- oder Projektnamen: 0»
> sagt mehr, als ihr Wächter prüft.** Der Wächter (`tests/test_regel3_kennungen.py`) sucht
> **Benutzernamen in Pfaden** — entstanden am 24.08.2026, als der Name des Owners über
> Fehlertexte von Blender ins Repo gereist war. Einen Büro- oder Projektnamen kennt er
> nicht und kann ihn nicht kennen: Eine Liste echter Projektnamen wäre selbst ein Verstoss
> gegen Regel 3.
>
> Die Lücke ist am 24.09.2026 sichtbar geworden. Die Sitzung der Messmaschine meldete nach
> einem Auftrag des Owners, dass das Kürzel und der Ortsname **eines echten Büroprojekts**
> im öffentlichen Repo stehen. Nachgezählt waren es **13 Stellen** (gemeldet waren 12),
> darunter drei Dokumente vom August, deren betroffene Zeilen nachweislich schon vor dem
> 19.09.2026 im Repo standen — also auch, als die Tabelle oben «0 Treffer» meldete. Alle Stellen sind ersetzt (Commit `9cfdf13`, neues Beispielprojekt
> «Testobjekt Lichthof»); die Versionsgeschichte ist, wie verlangt, **nicht** umgeschrieben.
> Gefunden hat es ein Mensch, nicht der Wächter.
>
> Am selben Skript, am 29.09.2026: **1274** geprüfte Dateien, **0** Treffer — mit
> derselben Einschränkung. Die Zeile heisst richtig: *keine Benutzernamen in Pfaden
> gefunden.* Für Projektnamen gibt es keinen Wächter, nur Aufmerksamkeit.

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

> **Nachtrag 29.09.2026 — die Oberflächen sind gekommen, und der Kern hat es nicht
> gemerkt.** Der letzte Absatz ist überholt: Seit dem 21.09.2026 gibt es eine eigene
> Oberfläche am Rechner (`oberflaeche/`, gebaut mit der Standardbibliothek), seit dem
> 22.09.2026 das Gerüst einer iPad-App (`ipad/`), und seit dem 24.09.2026 eine wörtliche
> Kopie der Knotenansicht von KosmoOrbit (`kosmovis/`, Entscheid E26). Alle drei liegen
> **neben** `src/aiimaging/`, nicht darin.
>
> Das ist die Probe auf diese Regel, und sie ist gefahren: Am 29.09.2026 lädt ein einfacher
> Import des Kerns **177** Module, davon **0 von 13** verbotenen Markern — drei Oberflächen
> später dieselbe Null wie am 19.09.2026. *Die Oberflächen hängen am Kern; der Kern hängt
> an keiner.*

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

**Viertens, nachgetragen am 29.09.2026: Eine der vier Regeln gilt nicht mehr ausnahmslos.**
Die These sagt, die Auflagen hätten festgestanden, bevor eine Zeile geschrieben war, und
den Entwurf hervorgebracht. Für Regel 1 ist das seit dem 29.09.2026 nur noch mit einem
Zusatz wahr: Sie hat eine befristete Forschungs-Ausnahme (3.2), und diese Ausnahme ist
**wegen eines bestimmten Modells** entstanden — die Richtung war hier umgekehrt. Dass die
Ausnahme als Code gebaut ist und nicht als Absichtserklärung, spricht für die Arbeitsweise;
es ändert nichts daran, dass ab diesem Tag ein Modell rechnen darf, das im Produkt nie
stehen darf. Ob das trägt, entscheidet sich an der vierten Auflage — *vor einem Verkauf
entfernt oder lizenziert* —, und die liegt ausserhalb dieser Arbeit.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Die vier Regeln im Wortlaut | `CLAUDE.md` |
| Alle Zahlen dieses Kapitels | `tools/beweis/19_regeln_ausfuehrbar.py` (ausführbar) |
| 3.2 Lizenzampel | `src/aiimaging/backbone.py`, `docs/LIZENZPRUEFUNG_2026-08-18.md` |
| 3.2 Nur zum Messen (SDXL, SD3.5) | `docs/sitzungen/2026-09-22_sitzung-62.md` §5 |
| 3.2 Stillgelegt, Forschungs-Ausnahme | `backbone.Backbone.stillgelegt`, `backbone.Backbone.nur_forschung`, `backbone.ladefreigabe`, `tests/test_forschung_ausnahme.py`, `CLAUDE.md` (Präzisierung Forschungsmodelle), `docs/sitzungen/2026-09-29_sitzung-72.md` §4 und §9 |
| 3.3 Prozessgrenze | `src/aiimaging/seams.py`, `tests/test_prozessgrenze.py`, `NOTICE` |
| 3.3 Glas an der Dateigrenze | `docs/sitzungen/2026-09-24_sitzung-71.md` §16, `docs/sitzungen/2026-09-29_sitzung-72.md` §5, `tests/test_modellstand.py` §6, `docs/EINBAU_STAND.md` (C33) |
| 3.4 Der Preis | `auftraege/offen/auf-20260911-106.json` |
| 3.4 Der entfernte Projektname | Commit `9cfdf13`, `docs/sitzungen/2026-09-24_sitzung-71.md` §19 |
| 3.5 Bibliothek ohne Oberfläche | `tests/test_regel4_bibliothek.py` |
| Neu gefahrene Zahlen | `tools/beweis/19_regeln_ausfuehrbar.py`, gefahren am 29.09.2026 auf `d93bab2` |
