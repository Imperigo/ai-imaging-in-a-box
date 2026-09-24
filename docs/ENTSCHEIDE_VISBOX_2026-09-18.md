# Visbox — die zwanzig Entscheide, die den Anfang tragen

**Grundlage:** keine
**Nachgesehen bis:** 2796ea5
**Codestand:** `2796ea5`

> **Owner 18.09.2026:** *«Baukasten passt, beantworte die roten Fragen nach deiner
> Empfehlung.»*

**Der Name ist seiner, die neunzehn anderen Entscheide sind meine.** Das steht hier, weil
es zählt: Eine delegierte Entscheidung trägt die Begründung ihres Ausführenden. Jede nennt
darum, **woran sie kippen würde** — das ist die Stelle, an der der Owner widersprechen
kann, ohne alles lesen zu müssen.

**Zwei kann ich nicht entscheiden, weil sie Tatsachen sind und keine Wahl** — sie stehen
am Ende als das, was sie sind: offen.

---

## Der Befund, der alles andere umgestellt hat

Die Kartierung von vierzehn Agenten hat **meine wichtigste Empfehlung widerlegt**, und das
gehört an den Anfang statt in eine Fussnote.

Ich hatte in F35 die SDXL-Familie empfohlen. Nachgemessen gibt es sie so nicht:

| Modell | Lizenz | Grösse | Tiefen-Naht | passt auf 32 GB |
|---|---|---|---|---|
| `z-image-turbo` | Apache-2.0 ✓ | **25,1 GB** (gemessen) | ✓ | **nein** — 78 % des ganzen Speichers |
| `qwen-image-2512` | permissiv ✓ | **48 GB** (geschätzt) | ✓ | nein |
| `flux2-klein-4b` | Apache-2.0 ✓ | **9,6 GB** | **✗** | **ja** |
| `sdxl-juggernaut` | **OpenRAIL-M ✗** | 8,4 GB | ✓ | ja |
| `sd35-large` | **Umsatzschwelle ✗** | 19,2 GB | ✓ | knapp |

**Es gibt heute kein Modell, das alle drei Bedingungen erfüllt:** permissiv lizenziert,
laptoptauglich, **und** mit der Tiefen-Naht, die unsere Geometrietreue trägt. Genau das ist
der Kern des Vorhabens, und ich habe es vor der Kartierung nicht gewusst.

**Dazu drei weitere harte Befunde:**

1. **Es gibt keinen MPS-Zweig.** `render.py` kennt genau zwei Geräte: `cuda` und `cpu`.
   Auf einem M1 Max läuft heute **jeder Lauf auf der CPU** — die langsamste denkbare
   Variante. Das ist nicht ein Detail, sondern die Frage, an der das Vorhaben hängt.
2. **Der Tiefenschätzer verliert ebenfalls.** Depth-Anything-V2 ist nur in der **Small**-
   Grösse Apache-2.0 (24,8 Mio. Parameter); Large und Giant sind CC-BY-NC. KosmoVis nutzt
   heute Large — **dreizehnmal grösser** als das, was wir verwenden dürfen.
3. **ComfyUI ist GPL-3.0** und damit ausgeschlossen. Der Bildweg läuft deshalb direkt über
   `diffusers` (Apache-2.0) — richtig so, aber es heisst, dass jede Bequemlichkeit, die
   ComfyUI mitbrächte, hier von Hand zu bauen ist.

*Es wäre bequemer gewesen, das nicht zu messen.* Aber eine Arbeit, die diese drei Punkte
erst im Januar entdeckt, ist im Februar nicht zu retten.

---

# Die Entscheide

## E1 · Der Name — **Visbox** *(Owner, 18.09.2026, dritte und letzte Fassung)*

Der Name ist an einem Tag zweimal gewechselt, und beide Male aus einem Grund, der
dokumentiert gehört:

| | | |
|---|---|---|
| **Baukasten** | Owner-Wahl am Vormittag | **gefallen** — PyPI und npm belegt, und zwar von einem **GPL-3.0**-Paket. Dazu heisst «Baukasten» im deutschen Software-Alltag der *Website-Baukasten*. |
| **Baugespann** | meine Empfehlung | vom Owner angenommen, dann verworfen — zu schweizerisch, kein Bezug zur Sache für jemanden ausserhalb. |
| **Visbox** | Owner-Wahl, endgültig | PyPI **404**, npm **404** — selbst geprüft am 18.09.2026. |

**Visbox** trifft die Sache direkt: Visualisierung, und «Box» trägt die Verheissung des
Ein-Klick-Downloads — *alles drin, eine Datei*. In beiden Sprachen lesbar und sprechbar,
was an einer Hochschule zählt, an der englisch gelesen wird.

| | |
|---|---|
| Die Software | **Visbox** |
| Das Paket | `pip install visbox` |
| Der Importpfad | bleibt `aiimaging` — siehe unten |
| Das Repo | bleibt `ai-imaging-in-a-box` |
| Die Vertiefungsarbeit | trägt ihren eigenen Titel |

**Warum der Importpfad `aiimaging` bleibt.** Ihn mitzuziehen hiesse, rund 40 000 Zeilen und
131 Testdateien anzufassen, ohne dass danach etwas ginge, was vorher nicht ging. Im
Python-Raum ist die Trennung üblich und unauffällig (`pip install pillow` → `import PIL`).
Umbenannt wird er, wenn die Produktfläche steht und der Schnitt ohnehin fällt — *nicht
heute, mitten im Bau.*

**Nicht geprüft:** GitHub-Namen und Markenregister. Die GitHub-Schnittstelle verlangte
eine Anmeldung; das Markenregister habe ich nicht angesehen. **Für einen Paketnamen
entscheiden PyPI und npm, und die sind frei** — aber «ungeprüft» heisst hier ungeprüft und
nicht «frei».

## E2 · Module, die mitkommen — **`vis`, `asset`, `spez`; `design` nur teilweise**

`vis` (Bilder), `asset` (Modelle), `spez` (KI-Werkzeugschicht). Bei `design` habe ich
meine Empfehlung **korrigiert**: Der Skizzenmodus dort ist ein *Strich-zu-Wand-Wandler*,
kein Zeichnen auf einem Bild — für unseren Schritt 5 also fast wertlos. Wir nehmen aus
`design` nur die Eingabeschicht (Zeiger, Druck, Glättung) und bauen das Zeichnen neu.

**Kippt an:** dem Wunsch, auch Pläne ausgeben zu können — dann käme `publish` dazu.

## E3 · BIM-Kern — **nein**

Visbox importiert Modelle, es baut keine. Das ist der grösste einzelne Brocken drüben
und gehört nicht zu dem Ablauf, den der Owner beschrieben hat.

**Kippt an:** dem Satz «man muss das Importierte auch ändern können». Dann bräuchte es
nicht den BIM-Kern, sondern ein sehr kleines Teilstück davon — und das wäre eigens zu
entscheiden.

## E4 · Die kleinste Fassung, die ein Erfolg wäre — **sechs Schritte, die zusammenhängen**

```
Modell rein  →  Kamera  →  Blender-Render  →  KI-Bild  →  hineinzeichnen  →  neues Bild
```

Alles andere ist Zugabe. **Woran ich das messe:** Eine fremde Person, die die Software
zum ersten Mal öffnet, kommt ohne Hilfe zu einem veränderten Bild.

**Kippt an:** der Antwort auf F59 (Abgabetermin). Bei weniger Zeit fällt der letzte
Schritt zuerst.

## E5 · Die Naht zwischen TypeScript und Python — **lokaler Python-Dienst**

Die Oberfläche (Tauri, React) spricht über HTTP mit einem Python-Dienst auf demselben
Rechner. Rückfallebene bleibt der Unterprozess-Aufruf.

**Warum:** Die Bildmodelle sind Python und bleiben es. Die Oberfläche ist gebaut. Und ein
Lauf dauert Minuten — nur ein Dienst trägt eine ehrliche Fortschrittsanzeige über eine
solche Zeit. Die Prozessgrenze hilft zusätzlich bei den Lizenzen: `ifcopenshell` (LGPL mit
GPL-CGAL) darf ohnehin nie im selben Prozess laufen.

**Kippt an:** einem Dienst, der sich als unzuverlässig erweist (Ports, Abstürze, Zombie-
Prozesse). Darum wird der Unterprozess-Weg nicht weggeworfen, sondern gepflegt.

## E6 · Importformate — **IFC, glTF/GLB, OBJ**

Rhino `.3dm` und SketchUp `.skp` **nicht bis Februar**. Begründung: Beide brauchen fremde
Bibliotheken mit eigener Lizenzprüfung, und der Importweg ist schon heute der reifste Teil
— ihn zu verbreitern kostet Zeit, die an anderer Stelle fehlt.

**Was ich dazu baue, weil es billiger ist als ein Importer:** eine ehrliche Meldung *«dieses
Format kann ich nicht — exportiere aus Rhino als OBJ oder glTF»* statt eines Absturzes.

**Kippt an:** einer Nutzerbefragung, die zeigt, dass Studierende ihre Modelle nicht
exportieren können oder wollen.

## E7 · Was an Figma Weave das Vorbild ist — **das Verhalten, nicht das Aussehen**

Ich konnte Weave nicht ansehen (Zugang nicht verknüpft), also entscheide ich es:
**Vorschau an jedem Knoten, Ausführung auf Knopfdruck, Ergebnis bleibt am Knoten stehen.**
Das ist das, was eine Knotenoberfläche für Entwerfende brauchbar macht — man sieht an jeder
Stelle, was herauskommt, statt nur am Ende.

**Nicht übernommen:** Aussehen und Bedienlogik im Einzelnen. Wir haben mit `NodeCanvas.tsx`
bereits einen handgeschriebenen SVG-Knoteneditor mit typgeprüften Ports, Zyklus-Riegel und
Undo — der ist besser als ein Nachbau.

**Kippt an:** zwei Bildschirmfotos von Weave. *Diese Frage bleibt offen und ist billig zu
beantworten.*

## E8 · Welche Knoten es gibt — **die acht vorhandenen plus acht neue**

Vorhanden: `modell szene material prompt stimmung kombinierer zahl render`.
Neu: **`import` · `kamera` · `tiefe` · `skizze` · `maske` · `variante` · `vergleich` ·
`export`**.

**Begründung je Knoten:** `import` und `export` sind die Ränder des Ablaufs. `kamera` und
`tiefe` tragen die Geometrietreue — das ist der Kern der Arbeit. `skizze` und `maske` sind
Schritt 5 und 6. `variante` und `vergleich` machen aus einem Bildwerkzeug ein
Entwurfswerkzeug: *Entwerfen heisst vergleichen.*

**Kippt an:** dem Zeitbudget. Fällt etwas, dann `vergleich` zuerst.

## E9 · Was die KI tun darf — **antworten und vorschlagen, nicht selbst bauen**

Kosmo erklärt Knoten, schlägt Wege vor und beantwortet Fragen zum eigenen Zustand
(*«warum ist dieses Bild durchgefallen?»*). Sie legt **keine** Knoten selbst an.

**Warum diese Grenze:** Eine KI, die den Graphen umbaut, muss rückgängig machen können,
und das ist ein eigenes Vorhaben. Die Werkzeugschicht drüben (`commandTools()` macht 158
Befehle automatisch zu Werkzeugen) macht die dritte Stufe später zu einer kleinen
Erweiterung — sie ist aufgeschoben, nicht verbaut.

## E10 · KI ohne Konto — **ja, Ollama ist die Vorgabe**

Visbox läuft vollständig ohne Konto und ohne Schlüssel. Ein eigener Anthropic-Schlüssel
ist optional und macht die KI besser; die Software sagt ehrlich, was der Unterschied ist.

**Ein Fund, der hier hilft:** Kosmo kennt bereits acht Anbieter, darunter Ollama, LM Studio
und einen **ETH-SPH-Proxy**. Letzterer könnte für Studierende der ETH der bequemste Weg
sein — das prüfe ich.

## E11 · Das iPad — **nach Februar**

Bis Februar: Zeichnen im Desktop-Fenster. Die iPad-Fassung wird **nicht gebaut, aber nicht
verbaut** — die Zeichenschicht wird so getrennt, dass sie später auf einer PWA sitzen kann.

**Warum so hart:** Der Skizzenmodus, den ich für übernehmbar hielt, ist es nicht (siehe E2).
Zeichnen auf einem Bild muss neu gebaut werden — im Desktop wie auf dem iPad. Beides bis
Februar wären zwei Vorhaben, und dann wird keines fertig.

**Kippt an:** dem Owner, der sagt, das iPad sei der Kern der Arbeit. Dann fällt dafür der
Photoshop-Ersatz.

## E12 · Das Standardmodell — **`flux2-klein-4b`, und die fehlende Naht wird gebaut**

Das ist der schwerste Entscheid, und er folgt aus dem Befund oben: Von den drei Bedingungen
— permissiv, laptoptauglich, Tiefen-Naht — sind nur je zwei gleichzeitig zu haben.

**Ich wähle die Laptoptauglichkeit und die Lizenz und baue die Naht.**

| | |
|---|---|
| Vorgabe | `flux2-klein-4b`, Apache-2.0, 9,6 GB — läuft auf 16 GB |
| für grosse Maschinen | `z-image-turbo`, Apache-2.0, 25,1 GB — mit fertiger Naht |
| **was gebaut werden muss** | die Tiefen-Konditionierung für `flux2-klein-4b` |

**Warum nicht andersherum:** Ein Standardmodell, das auf dem Zielgerät nicht läuft, ist
kein Standardmodell. Und die Naht zu bauen ist Arbeit, die **der Arbeit gehört** — sie ist
genau der Beitrag, den eine Vertiefungsarbeit leisten kann.

**Zwei Dinge sind sofort zu berichtigen** (beide von der Kartierung gefunden): Die
Repo-Kennung von `flux2-klein` im Code ist falsch, und die Lizenz kippt bei der 9B-Grösse
auf Non-Commercial — der Riegel muss die Grösse prüfen, nicht den Namen.

**Kippt an:** einer Messung, die zeigt, dass die Naht für dieses Modell nicht zu bauen ist.
**Darum wird sie im Oktober gemessen und nicht im Januar.**

## E13 · Gewichte — **nachladen, nicht mitliefern**

Beim ersten Start, mit einer ehrlichen Anzeige vorher: *«Ich lade 9,6 GB. Das dauert bei
dir etwa X Minuten.»*

**Warum:** Ein Paket mit Gewichten wäre 10–25 GB und würde bei jeder Weitergabe die
Modelllizenz mitschleppen. Nachladen hält das Paket klein und die Lizenzlage einfach.

## E14 · Blender — **vorausgesetzt, beim ersten Start geprüft**

Nicht mitgeliefert. Blender ist GPL; als eigener Prozess aufgerufen ist es eine
Aggregation, mitgeliefert wird die Frage schwieriger, als sie sein muss.

**Ein Befund, der das stützt:** Die Prozessgrenze ist heute die reifste Stelle des Repos —
genau zwei `import bpy`, beide in Runner-Skripten, bewacht von einer Probe, die **den
Syntaxbaum prüft statt den Text**. Das wird nicht angetastet.

**BERICHTIGT am 18.09.2026.** Ich schrieb hier «verbindlich: Blender 4.2 LTS». Im Code
stehen **zwei** Fassungen nebeneinander: 4.2 für die CPU-Messungen, **5.2.0 LTS** für
alles, was auf der HomeStation mit GPU lief (`seams.py:76, 264, 717`). Eine Fassung
festzuschreiben bleibt richtig — sie muss aber die sein, auf der die Messungen beruhen,
und das ist zu klären, bevor sie im `INSTALL` steht.

**Und die Grösse war falsch:** Ich schrieb «~300 MB», gemessen sind **1,3 GB entpackt**.
Der Entscheid ändert sich dadurch nicht, die Zahl schon.

## E15 · Die Messlatte — **Apple Silicon, 16 GB Minimum, 32 GB empfohlen**

Mit `flux2-klein-4b` (9,6 GB) sind 16 GB knapp, aber machbar. 32 GB ist die Grösse, auf
der es angenehm ist. Darunter lehnt Visbox ab, statt eine Stunde zu rechnen und dann zu
sterben.

**Diese Zahlen sind gerechnet, nicht gemessen** — siehe die offenen Punkte am Ende.

## E16 · Der Speicherdeckel — **60 % des vereinten Speichers**

Also 9,6 GB bei 16 GB, 19,2 GB bei 32 GB. Darüber bricht Visbox ab **mit einer
Erklärung und einem Vorschlag** (kleineres Modell, kleinere Auflösung, weniger Schritte)
statt das System einfrieren zu lassen.

**Warum ein Deckel überhaupt:** macOS lagert aus, statt abzustürzen — und dann dauert ein
Lauf statt zwei Minuten zwei Stunden, ohne dass jemand versteht, warum. *Ein Abbruch mit
Grund ist besser als ein Erfolg, auf den man nicht warten kann.*

## E17 · Der eine Download — **App plus Python, ohne Gewichte, ohne Blender**

Grössenordnung 150–200 MB. Beim ersten Start holt Visbox, was fehlt, und sagt vorher,
wie viel und wie lange.

**Ein Befund, der Arbeit bedeutet:** Der Tauri-Bauweg liefert heute **nur Linux**
(`bundle.targets: ["deb","rpm"]`). macOS ist einzurichten — das ist ein eigener Posten im
Plan, kein Nebenbei.

**Und eine gute Nachricht:** `torch` zieht auf Linux über 1,5 GB proprietäre
NVIDIA-Dateien nach — auf macOS **nicht**. Die Mac-Auslieferung ist also nicht nur das
Ziel, sondern auch die lizenzrechtlich sauberere.

## E18 · Die Quelle der Wahrheit bei zwei Spuren — **der Vertrag liegt drüben**

`kosmo-contracts` bleibt die eine Quelle für die Feldnamen, weil der Cloud-Worker daran
hängt. Alles andere darf kopiert sein — **mit einer Probe, die anschlägt, wenn eine Kopie
altert.**

**Ein Befund, der das dringend macht:** Heute werden **drei Verträge auf beiden Seiten von
Hand doppelt gepflegt**, und es gibt kein Programm, das das bemerkt. Das ist der erste
Posten der Zweispurigkeit und wird im Oktober gebaut.

## E19 · Die Forschungsfrage — **BERICHTIGT, und die Messung dazu ist schon gelaufen**

Ich habe beim Schreiben dieses Blatts eine Messung übersehen, die im eigenen Repo liegt und
die Frage umstellt: **`auf-20260909-92`, HomeStation, 08.09.2026.**

Vier Fälle, je drei Startwerte, zwölf Bilder:

| | Ergebnis |
|---|---|
| gegen die **richtige** Soll-Karte | **12 von 12 bestehen**, 0,8965 – 0,9884 |
| gegen die **falsche** Soll-Karte (anderes Gebäude) | **12 von 12 bestehen ebenfalls**, 0,8279 – 0,8763 |
| bei ControlNet-Stärke 0,30, wo ρ über der Bauwerksmaske ≈ 0 ist | **11 von 12 bestehen immer noch** |

> **Das gesuchte Bild existiert — aber die Schwelle, die es besteht, belegt nicht, was sie
> belegen sollte.** Sie misst zum grossen Teil den Boden-Himmel-Aufbau, den jedes
> Architekturbild auf Augenhöhe hat.

**BERICHTIGT am 18.09.2026 — dieser Satz war falsch.** Ich hatte hier geschrieben:
*«Die Rettung steht im selben Befund: `rho_maske` trennt sauber, wo der zusammengesetzte
Score es nicht tut.»* Das war aus der Prosa des Befunds übernommen, **ohne die Tabelle
danebenzulegen, die im selben Verzeichnis lag.**

Nachgerechnet (`docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md`): Für die Frage *«richtiges oder
falsches Gebäude?»* trennt `rho_maske` **am schlechtesten von allen dreien** — paarweise nur
10 von 12, mit fast vollständig überlappenden Wertebereichen.

**Die Rettung ist eine andere und bessere:** Es sind **zwei** Fragen, und sie brauchen
**zwei** Zahlen.

| | folgt das Bild dem Modell überhaupt? | folgt es DIESEM Modell? |
|---|---|---|
| **`rho_maske`** | **ja** — fällt auf −0,009, also exakt null | nein (10/12) |
| **`geom_iou`** | nein — bleibt bei 0,72, wenn nichts mehr stimmt | **ja** — Lücke +0,149, paarweise 12/12 |

*Eine Kennzahl, die zwei Fragen zu einer verrechnet, beantwortet keine von beiden* — und
genau das tut der zusammengesetzte `score`.

*Das ist kein Scheitern, sondern das beste Ergebnis, das dieses Projekt bisher hat.* Ein
Prüfverfahren, das schwächer ist als das Erzeugungsverfahren, ist genau die Sorte Befund,
die man nur durch eine Gegenprobe findet — und wir haben sie gefahren, obwohl niemand sie
verlangt hatte.

### Die Forschungsfrage, neu gefasst

> **Woran lässt sich messen, dass ein erzeugtes Architekturbild die Geometrie seines
> Modells wirklich trägt — und was kostet es, dieses Mass auf Studierenden-Hardware unter
> ausschliesslich permissiven Lizenzen einzuhalten?**

Die drei Teilfragen, alle messbar und alle schon angefangen:

1. **Welches Mass trennt?** Der zusammengesetzte Score tut es nicht, `rho_maske`
   offenbar schon. Das ist zu belegen — mit derselben Gegenprobe gegen fremde Geometrie,
   die den ersten Befund erzeugt hat. **Ohne eine Gegenprobe gegen die falsche Karte ist
   keine Geometriekennzahl etwas wert**, und das ist ein Ergebnis, das über dieses Projekt
   hinaus gilt.
2. **Was kostet die Lizenztreue?** Der zugelassene Tiefenschätzer ist dreizehnmal kleiner
   als der übliche; das stärkste permissive Bildmodell passt nicht auf den Laptop.
   Beides ist in derselben Kennzahl zu beziffern.
3. **Was kostet die Laptoptauglichkeit?** Derselbe Ablauf, kleines und grosses Modell.

**Warum diese Fassung besser ist als meine erste:** Sie fragt nicht *ob es geht*, sondern
*woran man es erkennt*. Die erste Fassung hätte eine Messung gebraucht, die es schon gibt
— und die sie widerlegt hätte.

### Zwei Berichtigungen, die daraus folgen

* **Im Repo standen zwei verschiedene Forschungsfragen** — eine vom 09.09.2026 und die,
  die ich heute geschrieben habe. Es gibt jetzt eine, und sie steht hier.
* **README und `STRUKTUR_VERTIEFUNGSARBEIT.md` waren stehengeblieben.** Die README
  behauptete weiterhin, es gebe kein bestehendes Bild; das Strukturpapier führt
  `auf-20260909-92` als noch ausstehend. Die README ist nachgezogen, das Strukturpapier
  folgt beim Schreiben des Plans.

## E21 · Die Zielhardware ist wieder der **HomePC**, nicht der Laptop

**Owner-Entscheid 21.09.2026**, im Wortlaut:

> *«Ist okay, wir lassen das sonst mal mit dem Laptop. Wir nehmen mal meinen HomePC als
> Standard wie anhin und lassen das Laptop-Thema mal.»*

**Damit ist eine Prämisse vom 18.09.2026 zurückgenommen**, und zwar die, die seither die
meisten Entscheidungen getragen hat.

### Was am 18.09. galt, und warum es fiel

Am 18.09. war die Zielhardware auf den *Laptop einer Studierenden* (MacBook M1 Max)
umgestellt worden. Daraus folgte eine Klemme, die als Messauftrag hinausging: Ein Modell
müsste **drei** Bedingungen zugleich erfüllen — permissiv lizenziert, laptoptauglich, und
mit der Tiefen-Naht, auf der die Geometrieprüfung steht. Es gibt keines; immer nur zwei
von dreien.

**Die Messung dazu ist am 21.09. zurückgekommen, und sie ist eindeutig negativ:**

| | |
|---|---|
| Die Apache-2.0-LoRA für das kleine Modell | folgt dem **Referenzbild**, nicht der Tiefenkarte |
| Der integrierte Weg, bei Führung 1,0 | trägt ein wenig (0,299 gegen 0,031), bei Führung 4,0 ist die Bindung weg |
| Von 78 Bildern bestehen beide Tore | **null** |

*Der Weg über das kleine Modell ist nicht eng — er ist an dieser Messung nicht vorhanden.*

### Was das für die Software heisst

**Am Code ändert sich nichts.** Der Vorgabe-Backbone war nie umgestellt worden; er steht
seit August auf `z-image-turbo`, und er bleibt es. *Dass hier nichts zurückzubauen ist,
liegt daran, dass die Umstellung als Messauftrag hinausging statt als Umbau.*

| | |
|---|---|
| **Referenzmaschine** | die HomeStation — Ryzen 9 9950X, 96 GB, RTX 5090 |
| **Vorgabe-Backbone** | `z-image-turbo`, unverändert |
| **Speichergrenze** | die gemessenen 25,1 GB bleiben stehen |
| **Zeitgrenzen** | bleiben grosszügig; sie schaden auf einer schnellen Maschine nicht |

**Was stehen bleibt, obwohl das Thema ruht:** der Umrechnungsfaktor für langsame Maschinen
(`AIIMAGING_ZEITFAKTOR`) und die Ersatzpfade, die kein `/ai`-Verzeichnis voraussetzen.
Beides ist am 18.09. wegen des Laptops gebaut worden und ist **auch ohne ihn richtig** —
es macht die Software von einer bestimmten Maschine unabhängig, und genau das verlangt
Regel 4.

> *Eine Vorkehrung, die aus einer zurückgenommenen Annahme stammt, ist nicht dadurch
> falsch. Sie ist nur nicht mehr begründet durch sie.*

### Und was dieser Entscheid für die Arbeit bedeutet

Die Vertiefungsarbeit misst damit wieder auf **einer** Maschine, und das ist für die
Forschungsfrage ein Gewinn: Sie fragt, ob ein Bild dem Gebäudemodell folgt — nicht, auf
welcher Hardware. *Eine zweite Zielmaschine hätte jede Zahl mit einer zweiten Bedingung
belastet, ohne die Frage zu schärfen.*

Die Messung `auf-20260918-114` bleibt trotzdem in der Arbeit stehen, und zwar als
**Ergebnis**, nicht als Vorarbeit: Sie hat gezeigt, dass ein Regler existiert, der alle
alten Kennzahlen hebt und die Geometrie dabei herausdreht. Das ist die erste Bestätigung
des tragenden Ergebnisses an fremden Daten — *bestellt für eine Frage, die der Owner heute
zurückgezogen hat, und wertvoll für eine andere.*

---

## E22 · Zwei Oberflächen für zwei Produkte — und sie bleiben getrennt

**Owner-Entscheid 21.09.2026**, auf die Frage, ob die neue Visbox-Fläche und die von
KosmoOrbit zusammenwachsen sollen: *«Ja, getrennt bleiben.»*

### Was damit entschieden ist

| | |
|---|---|
| **Die Oberfläche von KosmoOrbit** | baut der UI-Worker, seit dem 26.08.2026 ganz. Dort ist Visbox **ein Knoten** unter vielen. |
| **Die Oberfläche von Visbox** | liegt hier, in `oberflaeche/`. Dort ist Visbox **das Programm**. |

**Das ist kein Doppelbau, sondern zwei Gegenstände.** Eine Fläche, in der Visbox ein
Knoten neben siebzehn anderen ist, kann nicht zugleich die Fläche sein, in der es das
Ganze ist: Was dort ein Bedienelement unter vielen wäre, ist hier der Hauptgegenstand —
und umgekehrt sind die siebzehn anderen Knoten hier gar nicht vorhanden.

### Was das kostet, und es steht hier, weil es sonst später überrascht

**Zwei Flächen zeigen dieselbe Zahl, und sie können auseinanderlaufen.** Genau das ist
der Grund, warum der Entscheid aufgeschrieben wird statt stillschweigend zu gelten:

> *Zwei Anzeigen derselben Messung sind zwei Gelegenheiten, sie falsch anzuzeigen.*

Die Gegenmassnahme ist keine gemeinsame Oberfläche, sondern eine gemeinsame **Quelle**:
Beide holen Urteil und Vorbehalt aus derselben Bibliothek und formulieren keinen eigenen
Satz dazu. Wo eine Fläche einen Satz selbst schreibt, ist sie die Stelle, an der die
beiden auseinandergehen — hier hält `tests/test_oberflaeche.py` das fest.

### Was daraus für die Arbeit folgt

Die Vertiefungsarbeit beschreibt **Visbox**. Die KosmoOrbit-Fläche kommt darin als
*Einbauort* vor (Kapitel 8), nicht als Produktfläche. Umgekehrt ist die Fläche hier keine
Vorarbeit für drüben — *sie ist die Fläche des Programms, das abgegeben wird.*

### Nachtrag 24.09.2026 — Visbox bekommt eine eigene Knotenansicht

**Owner-Entscheid 24.09.2026**, auf die Frage, wo «die Oberfläche mit den verbundenen
Knoten» sei, und drei Wege zur Wahl (KosmoOrbit zeigen · Visbox eine eigene geben ·
beides): *«3.»* — beides.

* **Die Trennung bleibt.** Der Knoteneditor von KosmoOrbit bleibt dort, und Visbox bleibt
  dort ein Knoten. Beauftragt: `auftraege/offen/auf-20260924-162.json` (ui) —
  Bildschirmfotos und der Stand der acht Knoten aus E8.
* **Neu:** Auch die Fläche von Visbox zeigt ihre eigene Kette als verbundene Knoten — nicht
  die achtzehn von KosmoOrbit, sondern die vier (bzw. mit Skizze sieben), die `kette`
  wirklich baut. Gezeichnet als Blatt 11 «Der Knotenweg am Rechner» auf der Entwurfsfläche,
  **noch nicht gebaut** (erst zeichnen, dann bauen).
* **Offen beim Owner** (Schilder auf dem Blatt): Ersetzt die Knotenansicht die Liste «Was
  gerechnet würde» oder sind beide umschaltbar? Und: nur zeigen, oder Verbindungen auch
  ziehen? *Vorschlag:* umschaltbar, nur zeigen — die Kette von Visbox ist fest, freies
  Verdrahten ist die Aufgabe von KosmoOrbit.

---

## E23 · Nach der Abgabe: zurück in KosmoOrbit — die iPad-App wird KosmoSketch

**Owner-Entscheid 22.09.2026**, im Wortlaut:

> *«Nach Abgabe Vertiefungsarbeit wird Visbox App Desktop und iPad-Version komplett wieder
> in KosmoOrbit-Softwares integriert, die Visbox-iPad-App wird wieder zur KosmoSketch-App.»*

**Das ergänzt E22, es hebt ihn nicht auf.** Bis zur Abgabe bleiben die Flächen getrennt;
die Arbeit beschreibt Visbox. Danach ist Visbox ein Teil von KosmoOrbit.

**Was daraus schon heute folgt:** Name, Kennung und Dienstname der App stehen an **einer**
Stelle; die Wege zwischen App und Rechner sind in `docs/VISBOX_PROTOKOLL.md` beschrieben,
nicht nur im Code; und kein Teil geht davon aus, nur Visbox zu sein. *Eine Integration,
die erst nach der Abgabe bedacht wird, beginnt mit einem Umbau.*

## E24 · Hineinskizzieren auf dem Vorgabemodell: weiter rechnen, mit Hinweis

**Owner-Entscheid 22.09.2026.** Gemessen ist, dass das Vorgabemodell `z-image-turbo` kein
Ausgangsbild annimmt (`auf-20260919-123`, bestätigt `auf-20260922-137`). Ein Nachrender
dort rechnet aus Tiefenkarte und Text; die Skizze steckt nicht im Bild.

Entschieden: **nicht sperren, sondern rechnen und es sagen.** Der Nachrender setzt den
Satz «SKIZZE NICHT ANGEKOMMEN …» mit Beleg als ersten Hinweis; er reist bis an das Bild in
der Mappe. Bewacht in `tests/test_bildeingang_register.py`, samt Gegenprobe für einen
ungemessenen Bildeingang (dort kein solcher Satz).

**Kippt an:** einem Modell, das Tiefe **und** Skizze annimmt. Meldet die Werkstatt, dass
`qwen-image-2512` das kann, rechnet es **nur** das Hineinskizzieren; `z-image-turbo`
bleibt Vorgabe (Owner, 22.09.2026).

---

# Was ich nicht entscheiden kann

## E20 · Zwei Schichten — **Geometrielayer, und ein AI-Imaging-Layer darauf**

**Owner-Entscheid 19.09.2026**, auf die Frage, ob ein Bild auch ohne Gebäudeform
weiterbearbeitet werden kann. Die Antwort war grösser als die Frage:

> *«Es wird sozusagen Stufe zwei, Layer aktiv — also ein AI-Imaging-Layer, wo
> pixelbasierte Anpassungen gemacht werden können, also Lightroom- und Photoshop-Ersatz
> über AI Imaging. Das wird auf den Geometrielayer draufgesetzt, für Variantenstudien
> etc.»*

**Damit ist nicht eine Ausnahme erlaubt, sondern eine Architektur festgelegt.**

| | |
|---|---|
| **Layer 1 · Geometrielayer** | Aus dem Modell gerechnet, gegen die Tiefenkarte gemessen. Trägt ein **echtes** Geometrie-Urteil: bestanden, durchgefallen oder nicht gemessen. |
| **Layer 2 · AI-Imaging-Layer** | Pixelbasiert, auf Layer 1 aufgesetzt. Hineingezeichnetes, Lichtstimmung, Materialvarianten. Trägt **kein eigenes** Geometrie-Urteil — wohl aber **das seiner Basis**. |

**Was das berichtigt, und zwar an etwas, das am selben Tag gebaut wurde.** Vormittags war
entschieden worden: Nach einem Handeingriff lautet das Urteil «nicht anwendbar»
(`bestanden = None`). Das ist richtig und **es wirft zu viel weg** — das Urteil über die
Geometrie *darunter* verschwand mit.

Bei einer Variantenstudie — acht Bildvarianten auf **derselben** geprüften Geometrie —
will genau das jemand wissen: *Die Geometrie darunter ist geprüft und bestanden; was Sie
hier sehen, ist Stufe zwei darauf.*

> **Ein Vorbehalt soll die Auskunft einschränken, nicht sie löschen.**

**Die bindende Auflage**, und sie ist die einzige: *Die beiden Urteile dürfen nie
verwechselbar sein.* Ein geerbtes Urteil ist kein eigenes. Ein Feld, in dem einmal das
eigene und einmal das fremde steht, ist genau der Fehler, gegen den dieses Projekt seit
Wochen anschreibt.

**Was daraus für die Forschungsfrage folgt** — und das ist der Grund, warum dieser
Entscheid hier steht und nicht in einem Bauzettel: Die Arbeit misst **Layer 1**. Layer 2
ist Produktfläche und kein Gegenstand der Messung. *Ein Bild, das auf Stufe zwei entsteht,
belegt nichts über Geometrietreue — es zeigt, was man mit einer geprüften Geometrie
anfangen kann.*

---

## E23 · Der Skizzenmodus — **Volumen darf erfunden werden, aber nie unbemerkt**

**Owner-Entscheid 21.09.2026**, und er verschiebt den Zweck des ganzen Werkzeugs:

> *«Das AI-Imaging soll für Variantentests auch Volumen hineinerfinden gemäss meiner
> Skizze. Ich kann Dinge in Skizzenform abgeben, AI-imagen, und es gut als Entwurfstool
> für schnelle Variantenstudien nutzen — im Bild selbst. Wenn ich dann sage, das Bild ist
> gut, kann Kosmo das Bild untersuchen und versuchen, es im Modell nachzubauen.»*

### Was daran neu ist

Bis heute stand im ganzen Projekt **ein** Satz über erfundene Geometrie: Sie ist der
Fehler, gegen den gemessen wird. Die Tiefenkarte war der Riegel dagegen, und Kapitel 6
steht darauf.

**Das bleibt richtig — für den einen Modus.** Dazu kommt ein zweiter, in dem das Erfinden
**der Zweck** ist:

| | Modus 1 · Darstellung | Modus 2 · Entwurf |
|---|---|---|
| Frage | Zeigt das Bild, was im Modell steht? | Wie sähe es aus, wenn dort etwas anderes stünde? |
| Tiefenkarte | Pflicht | nur als Anhalt, nicht als Riegel |
| Erfundenes Volumen | **Fehler** | **Ergebnis** |
| Was die Messung sagt | bestanden / durchgefallen | **wo es abweicht**, nicht ob |

### Die drei Auflagen, unter denen Modus 2 gebaut wird

**1 · Ein Bild aus Modus 2 sieht nie aus wie eines aus Modus 1.** Es bekommt ein eigenes
Zeichen und einen eigenen Satz — nicht das «nicht geprüft» von heute, denn *nicht geprüft*
und *absichtlich erfunden* sind nicht dasselbe. Wer die beiden im selben Feld führt,
macht genau den Fehler, gegen den E20 gebaut ist.

**2 · Die Abweichung wird gemessen, nicht bloss festgestellt.** Die Kennzahlen dieser
Arbeit — Silhouettenüberdeckung und Tiefenrangfolge — beantworten heute *ob* das Bild dem
Modell folgt. In Modus 2 beantworten **dieselben** Kennzahlen *wo es abweicht*. Das ist
kein neues Werkzeug, sondern dasselbe mit umgekehrtem Vorzeichen.

> *Der Riegel und der Messstab sind dasselbe Gerät. Nur im ersten Modus liest man ein
> Urteil ab und im zweiten eine Differenz.*

**3 · Die Abweichung ist die Übergabe an Kosmo.** Das ist der Grund, warum Punkt 2 nicht
Zierde ist: Wenn das nachgebaut werden soll, muss etwas sagen, **was** hinzugekommen ist.
Ein Bild allein sagt es nicht.

### Was das für Kapitel 6 heisst

**Nichts an den Messungen, alles an ihrer Einordnung.** Das tragende Ergebnis bleibt: Auf
den Szenen des Datensatzes vom 09.09.2026 trennt das Verfahren richtig von fremd. Neu ist,
dass diese Trennung **eine von zwei Betriebsarten** bedient statt der einzigen.

*Ein Riegel, der auch dort hält, wo er gar nicht gebraucht wird, ist kein besserer Riegel
— er ist ein Werkzeug, das seinen zweiten Gebrauch nicht kennt.*

### Was dem heute im Weg steht, und es ist gemessen

**Unser Vorgabe-Bildmodell nimmt überhaupt kein Eingangsbild an** (`auf-20260919-123`,
sieben Läufe, ein einziger sha256). Ohne Eingangsbild gibt es keine Skizze, die
hineingereicht werden könnte. **Modus 2 ist auf dem Vorgabeweg heute nicht baubar.**

In der Registry steht genau **ein** Modell, das es könnte und unter Regel 1 zulässig ist:
`qwen-image-edit-2511`, Apache-2.0, integriertes Edit. Drei Dinge sind daran offen:

1. Sein Speicherbedarf ist **geschätzt** (48 GB aus der Parameterzahl), nicht gemessen.
   Die einzige echte Messung dazu (`auf-20260818-09`) sagt: Gewichte 29,57 GiB geladen,
   und dann scheitert der Lauf an 18 MiB. *Er passte nicht — knapp.*
2. Damit landet er auf dem **Auslagerungsweg**, und der ist seit dem 25.08.2026 kaputt
   (`auf-20260921-131`, offen).
3. Wie eine Skizze überhaupt hereinkommt — im Browser gezeichnet oder als Datei —, ist
   eine Frage an den Owner und noch nicht entschieden.

**Diese Reihenfolge ist zwingend:** ohne 2 kein 1, ohne 1 kein Modus 2.

---

## E24 · Die Lieferform ist ein **iPad mit Stift** — und die Fläche geht mit

**Owner-Entscheid 21.09.2026**, unmittelbar auf E23:

> *«Es soll eine Ergänzungssoftware für das iPad entwickelt werden, die genau dafür gebaut
> ist. Eine simple Oberfläche wie bei iPad-Zeichnungs-Apps, damit ein schlauer
> Stift-zu-Skizze-zu-AI-Imaging-Ablauf entsteht — ähnlich wie Samsung das auf ihrem Handy
> macht.»*

**Das ist kein neues Produkt, sondern die Lieferform für E23.** Der Entwurfsmodus braucht
jemanden, der zeichnet; ein Stift auf einem Tablet ist das naheliegendste Gerät dafür, und
es ist das, was der Owner in der Hand hat.

### Die Aufteilung, und sie folgt aus Regel 4

Ein iPad kann das Bildmodell **nicht** rechnen: kein CUDA, und die Gewichte brauchen rund
dreissig Gigabyte. Damit ist die Rollenteilung vorgegeben und nicht gewählt:

```
iPad  ─ zeichnen, ansehen, entscheiden ─┐
                                        ├─ Netz ─  HomePC: Bibliothek, Blender, GPU
Browser am Rechner  ────────────────────┘
```

*Das ist genau die Bauform, die Regel 4 seit dem ersten Tag verlangt: Der Kern ist eine
Bibliothek, die Fläche ist dünn. Eine zweite dünne Fläche kostet darum nichts an der
Bibliothek.* Hätte das Projekt die Fähigkeiten in die Oberfläche gebaut, wäre an dieser
Stelle ein zweites Programm fällig.

### Empfehlung: **Seite im Browser, keine App im App Store**

Das iPad öffnet **dieselbe Seite**, die heute schon läuft. Begründet, nicht bequem:

| | Seite im Safari | Eigene App |
|---|---|---|
| Zweiter Quelltext | **nein** | ja, in Swift |
| Apple-Entwicklerkonto (jährliche Gebühr) | **nein** | ja |
| Verteilung an Dritte | Link | App Store, mit Prüfung |
| Stiftdruck und Stiftart | **ja**, über Zeiger­ereignisse | ja |
| Latenz wie eine Zeichen-App | **nicht gemessen** | vermutlich besser |
| Regel 1 | unberührt | unberührt (Apples Werkzeuge sind proprietär, nicht ansteckend) |

**Die eine Zeile, die zählt, ist die vorletzte:** Ob sich eine Browserseite auf einem iPad
wie eine Zeichen-App *anfühlt*, ist **nicht gemessen** und von hier aus nicht messbar.
Das entscheidet niemand am Schreibtisch, sondern ein Mensch mit einem Stift.

*Darum wird die Zeichenfläche zuerst gebaut und ausprobiert, bevor über eine App geredet
wird.* Fällt die Probe durch, ist eine App die Antwort — dann aber mit gemessener
Begründung statt mit einer Vermutung.

### Die offene Frage, und sie ist keine technische

**Das iPad muss den HomePC erreichen können.** Die Fläche hört heute ausdrücklich nur auf
der eigenen Maschine, und der Grund steht in ihrem LIESMICH: *Hier liegen die
Gebäudemodelle von jemandem.*

Sie im Heimnetz zu öffnen ist ein kleiner Handgriff und eine **Entscheidung des Owners**,
keine des Ausführenden. Was daran hängt: Jedes Gerät im selben Netz könnte die Projekte
lesen. Ein Passwort davor ist machbar, ist aber selbst wieder etwas, das gebaut, geprüft
und nicht vergessen werden will.

*Solange das nicht entschieden ist, wird die Fläche nicht geöffnet.*

---

## E25 · Die Fläche darf ins Heimnetz — **mit Kennwort, und mit gesagtem Vorbehalt**

**Owner-Entscheid 21.09.2026.** Damit ein iPad die Fläche erreicht, muss sie im Netz
hören statt nur auf dem Rechner selbst. Gewählt wurde **«ja, mit Kennwort»**.

### Was gebaut ist

**Fail-closed**, und das ist die eigentliche Eigenschaft: Wer eine andere Adresse als
`127.0.0.1` wählt und **kein** Kennwort setzt, bekommt keinen Server, sondern einen Satz.

> *Eine Sperre, die man vergessen kann, ist im entscheidenden Augenblick vergessen.*

Auf `127.0.0.1` bleibt es ohne Kennwort. Dort kommt ohnehin nur diese Maschine heran, und
wer eine Hürde ohne Gegenüber jeden Tag nimmt, schaltet sie irgendwann ab.

Verglichen wird in gleichbleibender Zeit (`hmac.compare_digest`), Name **und** Kennwort,
beide immer. Das Kennwort kommt aus `secrets`, nicht aus `random`: *Ein Zufall, der sich
fortrechnen lässt, ist keiner.*

### Was diese Anmeldung **nicht** leistet

Sie läuft über gewöhnliches HTTP. **Kennwort und Bilder gehen unverschlüsselt durch das
Netz.** Wer im selben WLAN mitliest, liest mit.

Sie hält Geräte fern, die zufällig im selben Netz sind — nicht jemanden, der dort mithört.
Das steht im Quelltext, im LIESMICH und beim Start auf dem Bildschirm, und eine Probe hält
fest, dass es stehenbleibt.

**Warum kein TLS:** Ein selbst ausgestelltes Zertifikat erzeugt auf dem iPad eine Warnung,
die man wegklicken muss — und eine Sicherheitswarnung, die man täglich wegklickt, erzieht
zum Wegklicken. Ein echtes Zertifikat braucht einen Namen im Netz und eine Stelle, die ihn
bestätigt. *Für ein Heimnetz mit einem Benutzer ist das die teurere Hälfte einer Lösung,
deren billigere Hälfte hier genügt* — solange danebensteht, was sie nicht kann.

### Was daran noch offen ist

Wer das Kennwort einmal hat, hat es dauerhaft: Es gibt kein Abmelden und keinen Ablauf.
Für ein Heimnetz mit einem Menschen ist das vertretbar; **sobald jemand Drittes die Fläche
sehen soll, ist es das nicht mehr.**

---

Diese zwei sind **Tatsachen, keine Wahl**. Ich trage sie nicht als entschieden ein.

## O1 · Der Abgabetermin und die Form (F59) — **BEANTWORTET, 21.09.2026**

> *«Also einfach bis Ende Januar ca. soll fertig sein.»*

**Damit ist O1 keine offene Frage mehr.** Gerechnet wird mit dem **31.01.2027**; das «ca.»
bleibt stehen und heisst: Verschiebt sich der Tag um eine Woche, verschieben sich alle
Marken mit — die Reihenfolge nicht.

**Die Rechnung, und sie ist der ganze Punkt dieser Antwort:** 19 Wochen. Davon gehören die
letzten **sechs dem Schreiben**, und das ist keine Grosszügigkeit, sondern eine Bedingung:

> *Eine Software, die im Januar noch wächst, ist im Januar nicht gemessen — und was nicht
> gemessen ist, steht nicht in der Arbeit.*

Bleiben **zwölf Wochen Bauzeit.** Der Terminplan mit vier Marken steht in
`docs/PRODUKT_DIE_SCHRITTE.md`. Die wichtigste ist **nicht** die letzte:

**Am 15.10.2026 fällt die Entscheidung über den Entwurfsmodus** (E23). Er hängt an drei
Messungen, die wir nicht selbst fahren können. Liegen sie bis dahin nicht vor, wird er
gestrichen — *ein Vorhaben, über das man nicht rechtzeitig entscheidet, entscheidet sich
selbst, meistens zu spät und immer teurer.*

**Was damit fällt, ist entschieden und nicht vertagt:** der Rückweg ins Modell (E23,
Schritt 7) und eine eigene iPad-App (E24). Beide bleiben als **Ausblick** in der Arbeit —
das ist ihr richtiger Platz, nicht der Papierkorb.

### Die alte Fassung dieser Frage, zum Nachlesen



Ich weiss nicht, wann abzugeben ist, in welchem Umfang und in welcher Form. **Der ganze
Plan hängt daran**, denn er wird rückwärts vom Termin gerechnet.

**Neu am 21.09.2026:** Der Owner hat geantwortet — **früher als Ende Februar 2027**. Ein
Datum steht noch nicht fest.

Das ist keine Kleinigkeit und auch keine Formalie: Es ist die erste Angabe, die den Plan
**kürzt** statt ihn zu füllen. Was zuerst wegfällt, steht in
`docs/PRODUKT_DIE_SCHRITTE.md` — und zwar **begründet, nicht nach Gefühl**.

*Bis zum Datum rechne ich weiter mit Ende Februar 2027 als oberer Schranke und behandle
alles darunter als möglich.* **Das ist eine Arbeitsannahme und keine Auskunft** — sie
steht überall dort, wo sie etwas trägt, ausdrücklich als solche da.

## O2 · Eine Maschine zum Messen (F49, berührt E12/E15/E16) — **offen**

Ich habe hier weder GPU noch Apple Silicon. **Jede Hardwarezahl in diesem Blatt ist
gerechnet und nicht gemessen** — auch die Speicherangaben, auf denen E15 und E16 stehen.
Und die Frage, an der ein erster Mac-Lauf zuerst scheitern würde, ist offen: ob PyTorch
`bfloat16` auf MPS in der benötigten Breite trägt.

*Eine Messung auf einem echten M1 Max, früh, ist der billigste Weg, den ganzen Plan gegen
eine böse Überraschung im Januar abzusichern.*

---

## E26 · Die Vis-Oberfläche von KosmoOrbit kommt herüber — **als Kopie, bis Februar, dann zurück**

**Owner-Entscheid 24.09.2026**, im Wortlaut:

> *«Das Ziel ist, Code von KosmoVis-UI-Oberfläche etc. zu übernehmen, den Code zu kopieren,
> weiterzubearbeiten bis Februar und dann wieder seamless in die KosmoOrbit-Software
> einzubauen. Die Node-Oberfläche hat starke Prio und soll dringend sauber gelöst werden.
> Danach schauen wir jeden einzelnen Knoten an.»*

Und auf die vier Rückfragen desselben Tages:

| Frage | Antwort des Owners |
|---|---|
| Wird der Code öffentlich (Apache-2.0)? | *«Bitte nur Code von KosmoVis und nicht der ganzen Software … ja, das ist mir klar, dass bis zur Februarversion der Code von Vis öffentlich wird — das ist das Ziel. Einfach wirklich nur Code vom Vis-Tool nehmen, und auch UI und UX davon.»* |
| Umfang zuerst | **Die ganze KosmoVis-Ansicht** (Knoteneditor, Kuratieren, Bericht, …). |
| Laufort | **Im Browser**, ausgeliefert von unserem Server auf der HomeStation. |
| Die heutige Visbox-Fläche | *«Die aktuelle ist die richtige neue — wir bauen nur die Node-Oberfläche ergänzend rein, denn die soll genauso wichtig sein wie der Rest.»* |

### Was damit entschieden ist

* **Quelle:** das Vis-Werkzeug von KosmoOrbit, `kosmo-orbit/apps/kosmo-orbit/src/modules/vis/`
  im Repo Architektur-Cosmos, samt dem, was nur ihm dient. **Nicht** der Rest von KosmoOrbit
  (Architekturkern, Zeichnen, Publizieren, Synchronisieren). **Nicht** das ältere Repo
  «KosmoVis» mit seinem Blender-Add-on — ein Add-on bleibt nach Regel 2 verboten.
* **Was ausserhalb des Vis-Werkzeugs liegt und gebraucht wird, bekommt einen Stellvertreter**
  mit denselben Namen (Bausteine der Oberfläche, Projektspeicher, Anbindung an den
  Rechenweg). So bleibt der kopierte Code **unverändert**, und die Rückkehr im Februar ist
  ein Austausch der Stellvertreter gegen die Originale — nicht ein Zusammenführen zweier
  auseinandergelaufener Fassungen.
* **Jede Änderung am kopierten Code wird einzeln geführt** (Herkunft mit Commit, Liste der
  Abweichungen). *Seamless heisst: Man kann bis Februar jederzeit sagen, was anders ist.*
* **E22 ist damit abgelöst, soweit es um das Vis-Werkzeug geht:** Die beiden Flächen bleiben
  nicht getrennt, sondern das Vis-Werkzeug lebt bis Februar hier und geht dann zurück.
* **Die heutige Visbox-Fläche bleibt die Hauptfläche**; die Knotenoberfläche kommt als
  gleichwertiger Teil dazu. Blatt 11 der Entwurfsfläche (eigene Knotenansicht) ist damit
  überholt: Die Knotenansicht ist die von KosmoVis, mit ihrem Aussehen und ihrer Bedienung.
* **Die Auflage «keine fremden Bausteine, kein Web-Rahmenwerk»** der Visbox-Fläche
  (`oberflaeche/LIESMICH.md`) gilt für die Knotenoberfläche nicht: Sie ist React und
  TypeScript und wird beim Bauen zu festen Dateien gebündelt, die unser Server ausliefert.
  **Unverändert gilt:** zum Start keine Netzverbindung, nur permissive Lizenzen (Regel 1),
  jede Abhängigkeit geprüft und im `NOTICE`.
* **Regel 3 gilt für den kopierten Code wie für jeden anderen:** vor dem ersten Commit auf
  Namen, Pfade mit Benutzernamen, Adressen und Schlüssel durchsucht.

