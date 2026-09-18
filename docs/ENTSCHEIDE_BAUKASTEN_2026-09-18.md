# Baukasten — die zwanzig Entscheide, die den Anfang tragen

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

## E1 · Der Name — **Baukasten** *(Owner)*

Englischer Untertitel: *an AI imaging workbench for architects*. Repo-Name bleibt
`ai-imaging-in-a-box`; das Paket heisst `baukasten`.

**Kippt an:** einem Markenkonflikt. Ich prüfe PyPI, npm und die Markenregister, bevor
der Name irgendwo festgeschrieben wird.

## E2 · Module, die mitkommen — **`vis`, `asset`, `spez`; `design` nur teilweise**

`vis` (Bilder), `asset` (Modelle), `spez` (KI-Werkzeugschicht). Bei `design` habe ich
meine Empfehlung **korrigiert**: Der Skizzenmodus dort ist ein *Strich-zu-Wand-Wandler*,
kein Zeichnen auf einem Bild — für unseren Schritt 5 also fast wertlos. Wir nehmen aus
`design` nur die Eingabeschicht (Zeiger, Druck, Glättung) und bauen das Zeichnen neu.

**Kippt an:** dem Wunsch, auch Pläne ausgeben zu können — dann käme `publish` dazu.

## E3 · BIM-Kern — **nein**

Baukasten importiert Modelle, es baut keine. Das ist der grösste einzelne Brocken drüben
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

Baukasten läuft vollständig ohne Konto und ohne Schlüssel. Ein eigener Anthropic-Schlüssel
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

**Verbindlich: Blender 4.2 LTS.**

## E15 · Die Messlatte — **Apple Silicon, 16 GB Minimum, 32 GB empfohlen**

Mit `flux2-klein-4b` (9,6 GB) sind 16 GB knapp, aber machbar. 32 GB ist die Grösse, auf
der es angenehm ist. Darunter lehnt Baukasten ab, statt eine Stunde zu rechnen und dann zu
sterben.

**Diese Zahlen sind gerechnet, nicht gemessen** — siehe die offenen Punkte am Ende.

## E16 · Der Speicherdeckel — **60 % des vereinten Speichers**

Also 9,6 GB bei 16 GB, 19,2 GB bei 32 GB. Darüber bricht Baukasten ab **mit einer
Erklärung und einem Vorschlag** (kleineres Modell, kleinere Auflösung, weniger Schritte)
statt das System einfrieren zu lassen.

**Warum ein Deckel überhaupt:** macOS lagert aus, statt abzustürzen — und dann dauert ein
Lauf statt zwei Minuten zwei Stunden, ohne dass jemand versteht, warum. *Ein Abbruch mit
Grund ist besser als ein Erfolg, auf den man nicht warten kann.*

## E17 · Der eine Download — **App plus Python, ohne Gewichte, ohne Blender**

Grössenordnung 150–200 MB. Beim ersten Start holt Baukasten, was fehlt, und sagt vorher,
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

## E19 · Die Forschungsfrage — **und der Befund oben hat sie geschärft**

> **Lässt sich ein Entwurfswerkzeug bauen, das aus einem Architekturmodell Bilder erzeugt,
> deren Geometrie nachweislich erhalten bleibt — unter ausschliesslich permissiven Lizenzen
> und auf der Hardware, die Studierende besitzen?**

Und die drei Teilfragen, die die Arbeit beantworten kann, weil sie messbar sind:

1. **Was kostet die Lizenztreue an Bildqualität?** Wir wissen jetzt: Der zugelassene
   Tiefenschätzer ist dreizehnmal kleiner als der übliche, und das stärkste permissive
   Modell passt nicht auf den Laptop. *Das ist eine messbare Grösse, keine Meinung.*
2. **Was kostet die Laptoptauglichkeit an Bildqualität?** Derselbe Ablauf auf einem
   kleinen und einem grossen Modell, mit unserer Geometriekennzahl gemessen.
3. **Trägt die Kennzahl überhaupt?** Wir haben `geometrie_qa` gebaut und an Störungen
   geeicht — hier kommt sie zum ersten Mal an echten Entwürfen zum Einsatz.

**Warum das eine gute Forschungsfrage ist:** Sie hat ein Ergebnis, auch wenn die Antwort
*nein* lautet. Eine Arbeit, die zeigt, dass es unter diesen Bedingungen **nicht** geht,
und genau beziffert woran, ist mehr wert als eine Software, die auf einer Grafikkarte für
2000 Franken schöne Bilder macht.

---

# Was ich nicht entscheiden kann

Diese zwei sind **Tatsachen, keine Wahl**. Ich trage sie nicht als entschieden ein.

## O1 · Der Abgabetermin und die Form (F59) — **offen**

Ich weiss nicht, wann abzugeben ist, in welchem Umfang und in welcher Form. **Der ganze
Plan hängt daran**, denn er wird rückwärts vom Termin gerechnet.

*Bis zur Antwort rechne ich mit: Abgabe Ende Februar 2027, schriftliche Arbeit plus
Software als Anhang.* Sagen Sie mir das Datum, und ich richte den Plan danach aus.

## O2 · Eine Maschine zum Messen (F49, berührt E12/E15/E16) — **offen**

Ich habe hier weder GPU noch Apple Silicon. **Jede Hardwarezahl in diesem Blatt ist
gerechnet und nicht gemessen** — auch die Speicherangaben, auf denen E15 und E16 stehen.
Und die Frage, an der ein erster Mac-Lauf zuerst scheitern würde, ist offen: ob PyTorch
`bfloat16` auf MPS in der benötigten Breite trägt.

*Eine Messung auf einem echten M1 Max, früh, ist der billigste Weg, den ganzen Plan gegen
eine böse Überraschung im Januar abzusichern.*
