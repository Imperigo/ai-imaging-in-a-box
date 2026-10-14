# Die Knoten des Vis-Werkzeugs — was jeder kann und wie sie zusammenhängen

**Codestand:** `7224c0d` (Visbox), Kopie `kosmovis/` auf KosmoOrbit `22988d6ed` (`kosmovis/HERKUNFT.json`)
**Grundlage:** `knotenweg`, `abholer`, `bruecke`, `kosmo_szene` — dazu die Kopie unter `kosmovis/` (Knotenkatalog, Knotenansicht, Auftragsweg)

*Auftrag des Owners, 14.10.2026: «Ergänze auf der Kosmo-Tafel, was jedes einzelne Node kann, wie
es funktioniert, was es auslöst und wie es mit den anderen Nodes zusammenhängt.»* Dieses Blatt ist
die ausführliche Fassung; die Bildkarten auf der Tafel (`tafel/kosmovis/20261014-knoten-*`) sind
daraus gezogen und werden mit `tools/knoten_tafel.py` erzeugt.

Jede Aussage hier ist aus dem Code abgelesen; die Quelle steht je Abschnitt. Wo Visbox etwas
nur als **Stellvertreter** hat (ein Teil, das an der Stelle des Originals steht und ehrlich sagt,
was es nicht kann), steht das ausdrücklich dabei.

---

## Übersicht

### Was ein Knoten ist und wie man verbindet

Ein **Knoten** ist ein Kästchen mit einer Aufgabe. Links hat er seine **Eingänge**, rechts seine
**Ausgänge**. Eine **Linie** führt immer von einem Ausgang zu einem Eingang und sagt: «Dieser
Eingang liest, was jener Ausgang liefert.» Alle Knoten eines Bildes zusammen heissen **Graph**
(Render-Graph).

Drei Regeln gelten beim Verbinden (`vis.verbinden`, `packages/kosmo-kernel/src/commands/vis.ts`):

1. **Nur gleiche Sorte passt.** Ein Zahl-Ausgang lässt sich nicht an einen Bild-Eingang hängen —
   der Befehl lehnt ab und sagt, welche Sorten nicht passen.
2. **Ein Eingang hat genau eine Linie.** Wer eine neue Linie an einen belegten Eingang zieht,
   ersetzt die alte (wie in Blender). Ein Ausgang darf dagegen an viele Eingänge gehen.
3. **Es fliesst nur vorwärts.** Eine Linie, die einen Kreis schliessen würde, wird abgelehnt
   («Render-Graphen fliessen nur vorwärts»).

Ausgewertet wird der Graph in einer Reihenfolge, in der jeder Knoten erst drankommt, wenn alle
seine Zulieferer fertig sind (*topologische Sortierung*, `topoReihenfolge` in
`packages/kosmo-kernel/src/derive/visgraph.ts`). Die **einfachen Knoten** (Prompt, Stimmung,
Material, Kombinierer, Zahl) rechnen dabei sofort und bei jeder Änderung neu — man sieht das
Ergebnis live am Knoten. **Der Render-Knoten rechnet nie von selbst**: Er stellt nur seinen
Auftrag zusammen; abgeschickt wird erst auf «Ausführen».

### Was gespeichert wird und was nicht

Der Graph selbst — welche Knoten, wo sie stehen, ihre Einstellungen, die Linien — liegt im
Projektdokument: Jede Änderung ist ein Befehl und lässt sich **rückgängig machen**. Bilder und der
Zustand eines Renders («wartet», «rendert», «fertig») liegen **nicht** im Dokument, sondern nur im
laufenden Programm (`vis-runtime.ts`) — so wandern keine Bilder durch Rückgängig oder Abgleich.
(Quelle: Kommentar an `VisGraph`, `packages/kosmo-kernel/src/model/entities.ts`.)

### Was durch die Linien fliesst — sechs Sorten mit eigener Farbe

Jeder Anschluss trägt die Farbe seiner Sorte; die Linie nimmt die Farbe mit. Volle Punkte heissen
«verbunden», leere «frei». Werte aus `packages/kosmo-ui/src/aura.css` (`--k-port-*`, heller Grund /
dunkler Grund).

| Sorte | Farbe | Was sie trägt |
|---|---|---|
| **Szene** | Blau `#2455a4` / `#427ad5` | das 3D-Modell, das gerendert wird |
| **Prompt** | Grün `#1e6b47` / `#278c5d` | ein Text, der beschreibt, wie das Bild aussehen soll |
| **Material** | Ocker `#8a6d3b` / `#967740` | Materialsätze aus dem Modell (z. B. «Sichtbeton») |
| **Zahl** | Violett `#7a5c9e` / `#8b70ab` | ein einzelner Wert, z. B. Geometrie-Treue 0,8 |
| **Kameras** | Petrol `#2b8a7a` (beide) | eine Liste von Standpunkten |
| **Bild** | Rostrot `#a84b2b` / `#c95a33` | ein fertiges Bild (Render oder Aufnahme) |

### Vier Gruppen von Knoten

Der Kopf jedes Knotens trägt einen schmalen Farbstreifen nach seiner Gruppe (`VIS_KATEGORIE_HUE`,
`visgraph.ts`). Die Gruppe ist reine Ordnung fürs Auge, sie ändert nichts am Rechnen.

| Gruppe | Streifen | Knoten |
|---|---|---|
| **Quelle** — bringt etwas in den Graphen | Hellblau | Modell, Material-Bausteine, Auto-Kamera, Bild-Referenz, Viewport-Aufnahme |
| **Wandler** — formt Text und Zahlen | Ocker | Prompt, Stimmung, Prompt-Kombinierer, Zahl |
| **Render** — bestellt das Bild | Terracotta | Render |
| **Ausgabe** — zeigt oder legt ab | Grün | Bildvergleich, Aufs Blatt |

### Die typische Kette: vom Modell zum geprüften Bild

```
Modell ──Szene──────────────────────────────────┐
Material-Bausteine ──Material──┐                │
Stimmung ──Prompt──┐           │                ▼
Prompt ──Prompt────┼──▶ Prompt-Kombinierer ──Prompt──▶ RENDER ──Bild──▶ Bildvergleich
                   ┘                    Zahl ──Zahl──▶   ▲              (oder Aufs Blatt)
                                  Auto-Kamera ──Kameras──┘
```

Die Vorlage **«Drei Stimmungen einfügen»** (Insel *Stimmung*) baut genau diese Kette dreimal
nebeneinander auf: ein Modell und ein Material-Knoten für alle, je eine Stimmung (Morgenlicht,
Abendstimmung, Weissmodell) mit eigenem Kombinierer und eigenem Render, und alle drei Bilder in
einen Bildvergleich — als **ein** Rückgängig-Schritt (`dreiStimmungenEinfuegen`,
`apps/kosmo-orbit/src/modules/vis/vis-graph-aktionen.ts`). **«Kamera vorschlagen»** setzt einen
Auto-Kamera-Knoten (falls keiner da ist) und hängt ihn an jeden Render-Knoten, der noch keine
Kameras hat (`kameraVorschlagenAktion`, gleiche Datei).

### Der Weg eines Render-Auftrags

**In Visbox** (Knotenansicht unter `/knoten/` des Visbox-Servers):

1. «Ausführen» am Render-Knoten → der Knoten sammelt Szene, Prompt, Zahlen, Kameras und seine
   Einstellungen und schickt Modell (glb) plus Auftragsbeschrieb an die **Brücke** — in Visbox ist
   das der eigene Server unter `/bruecke` (`brueckeAufDiesenServer`, `apps/visbox-knoten/src/mappe.ts`).
2. Der Server legt den Auftrag als Ordner in die Auftragsablage der Mappe
   (`<Mappe>/knotenweg/vis-…/`, `knotenweg.lege_an`). **Jeder Auftrag beginnt auf «wartet auf
   Freigabe».**
3. Am Knoten erscheint **«Freigeben»**. Erst dieser Klick setzt den Auftrag in die Reihe, mit der
   Marke einer menschlichen Freigabe (`knotenweg.freigeben`).
4. Der **Abholer** am Heim-PC (`tools/abholen.py --store <Ablage>`, Modul `abholer`) holt ihn ab
   und rechnet je Kamera: Blender-Vorlauf (Tiefen- und Hilfsbilder) → Bild (Cycles, und ohne «nur
   Cycles» die KI-Veredelung) → **Geometrie-Prüfung** (passt das Bild zur Form des Modells?).
   Ohne mitgeschickte Kameras rechnet er drei feste Richtungen: frontal Süd, über Eck Südost, über
   Eck Nordwest (`AUTO_RICHTUNGEN`).
5. Er schreibt Bild und Urteil zurück; der Knoten fragt nach, zeigt den Fortschritt im Bildplatz
   und am Ende **Bild + Urteil** (bestanden / durchgefallen / nicht beurteilbar).

**In KosmoOrbit** ist die Brücke ein eigener Dienst auf der HomeStation. Dort geht ein Auftrag
vorgabegemäss sofort in die Reihe; «Freigeben» erscheint nur, wenn die Brücke eine Freigabe
verlangt (Modulkopf `knotenweg.py`, `mappeJobStatus` in `vis-jobs.ts`). Der Abholer am anderen Ende
ist derselbe.

---

## Quellen

### 1 · Modell

**Was er kann.** Bringt das Gebäude als 3D-Szene in den Graphen — der Startpunkt jedes Renders.
Am Knoten steht, wie viele Bauteile die Szene hat («Szene: N Bauteile (GLB)»).

**Wie er funktioniert.** Er rechnet nichts. Seine Linie sagt dem Render-Knoten nur: «Diese Szene
gehört zu dir.» Das Modell selbst wird erst beim Absenden als glb-Datei (ein gängiges 3D-Format)
erzeugt bzw. geholt.

**Was er auslöst.** Nichts von selbst. Ohne Linie vom Modell weigert sich der Render-Knoten
(«braucht eine Szene — verbinde den Modell-Knoten»); bei 0 Bauteilen ist «Ausführen» gesperrt.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Szene** → Render (Eingang *Szene*).

**Visbox vs. KosmoOrbit.** In KosmoOrbit ist es das im Entwurf gebaute Projekt. In Visbox kommt
das Modell **fertig aus der offenen Mappe**: Beim Öffnen holt die Seite das glb vom Server und gibt
es beim Render **unverändert** weiter (Stellvertreter `exportGlb`). Damit die Render-Sperre nicht
greift, legt sie zusätzlich **ein** Bauteil an: die gemessene Hüllbox (der umschreibende Quader)
des Gebäudes. Der Knoten zeigt darum in Visbox «Szene: 1 Bauteile» — gerendert wird trotzdem das
ganze Modell, nicht die Box.

*Quelle:* `VIS_NODE_KATALOG.modell` (`kosmo-kernel/src/derive/visgraph.ts`); `NodeKoerper` Fall
`modell` (`apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx`); `ladeMappe`
(`apps/visbox-knoten/src/mappe.ts`); `HERKUNFT.json` → `stellvertreter` → `derive/gltf.ts`.

### 2 · Material-Bausteine

**Was er kann.** Liest aus dem Modell kurze Materialsätze für den Prompt: die äusserste Schicht
jeder Wand («Sichtbeton», «Holz» …, mit Anstrich), einen geschliffenen Boden, wenn eine Körnung
gesetzt ist, die Sonnenstärke, wenn jemand sie gestellt hat, und das Fassadenraster samt
Fensteranteil aus dem Modul-Editor.

**Wie er funktioniert.** Rein abgeleitet, nie gespeichert: Bei jeder Auswertung liest er das Modell
neu (`renderPromptBausteine`) und gibt die Sätze mit Komma getrennt aus. Am Knoten steht der Text
(aufklappbar).

**Was er auslöst.** Nichts von selbst — er liefert Text an den Kombinierer.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Material** → Prompt-Kombinierer (Eingang *Material*).

**Visbox vs. KosmoOrbit.** In Visbox gibt es keine Wände mit Schichtaufbau, keinen Boden und keine
Fassadenmodule im Dokument — nur die Hüllbox. Der Knoten zeigt darum **«keine Material-Phrasen»**
und liefert einen leeren Text. Der Knoten ist da, sein Rohstoff fehlt.

*Quelle:* `VIS_NODE_KATALOG.material`; `renderPromptBausteine` (`kosmo-kernel/src/derive/renderprompt.ts`);
`NodeKoerper` Fall `material`.

### 3 · Auto-Kamera

**Was er kann.** Schlägt Kamera-Standpunkte vor und gibt sie als Liste an den Render-Knoten.
Ehrlich beschriftet: «Vorschlag aus dem Modell» (keine KI-Wahl) oder «von Hand gesetzt,
übernommen» für Kameras aus einer importierten 3DS-Datei.

**Wie er funktioniert.** Wie der Material-Knoten rein abgeleitet: Bei jeder Auswertung rechnet er
die Standpunkte aus der Ausdehnung des Modells neu (Eingang, Übersicht, und bei Räumen im Modell
auch Innenraum); übernommene Kameras stehen vorne. Ein Standpunkt, dessen Auge ausserhalb des
Modells liegt, wird markiert.

**Was er auslöst.** Hängt er am Render-Knoten, reisen seine Standpunkte im Auftrag mit, und der
Abholer rechnet genau diese. Ohne ihn (oder mit leerer Liste) rechnet der Abholer seine drei festen
Richtungen.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Kameras** → Render (Eingang *Kamera-Standpunkte*).

**Visbox vs. KosmoOrbit.** In Visbox **Stellvertreter**: Er leitet **keine** Standpunkte aus dem
Modell ab (leere Liste) und kennt nur übernommene Kameras — die es in einer Visbox-Mappe heute nicht
gibt. Er zeigt also «Keine Geometrie im Modell — nichts abzuleiten», und der Abholer rechnet die
drei festen Richtungen.

*Quelle:* `VIS_NODE_KATALOG.kamera`; `evaluiereGraph` Fall `render` (Kameras nur bei Linie am
Eingang `kameras`); `NodeKoerper` Fall `kamera`; Stellvertreter `kosmo-kernel/src/derive/kamera.ts`;
`abholer.AUTO_RICHTUNGEN`.

### 4 · Bild-Referenz

**Was er kann.** Hält ein Vorbild: Man gibt eine Bildadresse ein, der Knoten zeigt das Bild.

**Wie er funktioniert.** Speichert nur die Adresse (`url`) und zeigt das Bild im Knoten.

**Was er auslöst.** In der **Kuratierfläche** (Vollbild zum Auswählen und Nacharbeiten) erscheint
jede Bild-Referenz als mögliches Vorbild für einen **Farbangleich**: die Farbstimmung eines Renders
an die des Referenzbilds angleichen, statt sie neu erfinden zu lassen.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Bild** — lässt sich an Bildvergleich oder Aufs Blatt
ziehen. **Aber:** Diese Linie trägt heute kein Bild weiter. Vergleich und Blatt holen Bilder nur
von Render- und Aufnahme-Knoten (`bildQuelle`); eine Linie von der Referenz bleibt dort leer.

**Visbox vs. KosmoOrbit.** Gleich. Die Splat-Ansicht als Quelle, die der Katalog nennt, ist in
Visbox nicht angeschlossen (Splat-Ebene fest leer, Stellvertreter `state/splat-ebene.ts`).

*Quelle:* `VIS_NODE_KATALOG.referenz`; `NodeKoerper` Fall `referenz`; `bildQuelle` (`NodeCanvas.tsx`);
`vorbilder` (`KuratierFlaeche.tsx`).

### 5 · Viewport-Aufnahme

**Was er kann.** Eine echte Bildquelle ohne Rendern: ein Schnappschuss der 3D-Ansicht. Funktioniert
ohne Heim-PC.

**Wie er funktioniert.** Das Bild entsteht nicht hier, sondern im Entwurf (KosmoDesign) über «Für
Vis aufnehmen». Der Knoten zeigt die jüngste Aufnahme (Auswahl jüngste / Nordost / Süd). Der Knopf
«Aufnehmen» am Knoten nimmt nichts auf, er sagt, wo der echte Knopf sitzt.

**Was er auslöst.** Nichts beim Heim-PC. Sein Bild kann an Vergleich und Blatt gehen und erscheint
als Karte in der Kuratierfläche.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Bild** → Bildvergleich, Aufs Blatt.

**Visbox vs. KosmoOrbit.** In Visbox gibt es keine 3D-Entwurfsansicht, also auch keine Aufnahme:
Der Knoten bleibt bei **«Noch keine Aufnahme»**.

*Quelle:* `VIS_NODE_KATALOG.aufnahme`; `NodeKoerper` Fall `aufnahme`; `waehleAufnahme`
(`vis-runtime.ts`); Aufnahmen kommen nur aus `Viewport3D.tsx` (KosmoOrbit, nicht in der Kopie).

## Wandler

### 6 · Prompt

**Was er kann.** Ein Feld für freien Text, z. B. «Sichtbeton, warmes Licht».

**Wie er funktioniert.** Der Text geht wortgleich an seinen Ausgang; gespeichert wird beim
Verlassen des Feldes.

**Was er auslöst.** Nichts von selbst. Der Kombinierer und der Render-Knoten zeigen den neuen Text
sofort an.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Prompt** → Kombinierer (meist Eingang *Stil*) oder
direkt → Render (Eingang *Prompt*).

*Quelle:* `VIS_NODE_KATALOG.prompt`; `evaluiereGraph` Fall `prompt`; `NodeKoerper` Fall `prompt`.

### 7 · Stimmung

**Was er kann.** Wählt eine von drei Lichtstimmungen: Morgenlicht, Abendstimmung, Weissmodell.

**Wie er funktioniert.** Jede Stimmung ist ein fester Satz, z. B. Abendstimmung = «Abendstimmung,
warmes Licht, leuchtende Fenster». Der Satz steht am Knoten und geht als Prompt hinaus.

**Was er auslöst.** Nichts von selbst — er liefert Text. (Er stellt keine Sonne und kein Licht in
Blender; er beschreibt die Stimmung für die KI.)

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Prompt** → Kombinierer (Eingang *Stimmung*).

*Quelle:* `VIS_STIMMUNGEN`, `VIS_NODE_KATALOG.stimmung`; `NodeKoerper` Fall `stimmung`.

### 8 · Prompt-Kombinierer

**Was er kann.** Fügt Stimmung, Stil und Material zum **finalen Prompt** zusammen — live sichtbar
am Knoten.

**Wie er funktioniert.** Reiht die drei Texte mit Komma aneinander, in dieser Reihenfolge, und
lässt Leeres weg (`finalerRenderPrompt`).

**Was er auslöst.** Nichts von selbst. Am Render-Knoten erscheint der neue Prompt sofort; ein schon
fertiges Bild wird als **«veraltet»** markiert, sobald sich der Auftrag geändert hat.

**Ein- und Ausgänge.** Eingänge **Stimmung** (Prompt), **Stil** (Prompt), **Material** (Material).
Ausgang **Finaler Prompt** → Render (Eingang *Prompt*).

*Quelle:* `VIS_NODE_KATALOG.kombinierer`; `evaluiereGraph` Fall `kombinierer`; `finalerRenderPrompt`
(`renderprompt.ts`); `veraltet` über `memoKey` (`NodeCanvas.tsx`, `vis-runtime.ts`).

### 9 · Zahl

**Was er kann.** Ein Regler für einen Wert, Vorgabe 0,8 zwischen 0 und 1 in Schritten von 0,05.

**Wie er funktioniert.** Der Wert geht beim Loslassen des Reglers an den Ausgang.

**Was er auslöst.** Nichts von selbst. Am Render-Knoten wird er zu:
* **Geometrie-Treue** — wie eng die KI der Form des Modells folgen soll (0 bis 1, Vorgabe 0,8 ohne
  Linie). Am Heim-PC wird sie zur Stärke der Formführung (`controlnet_staerke`).
* **Samples** — wie viele Rechenschritte je Bildpunkt (Vorgabe 128). *Achtung:* Ist am Render-Knoten
  «Qualität gegen Zeit» gewählt, gilt diese Wahl und nicht die Zahl von der Linie.

**Ein- und Ausgänge.** Kein Eingang. Ausgang **Wert** (Zahl) → Render (Eingang *Geometrie-Treue*
oder *Samples*).

*Quelle:* `VIS_NODE_KATALOG.zahl`; `evaluiereGraph` Fall `render` (Klemme 0–1, Vorgabe 0,8/128);
`sendeGraphRenderAuftrag` (`vis-jobs.ts`, Bedienung schlägt Zahl); `kosmo_szene.py` (faithful →
controlnet_staerke).

## Render

### 10 · Render

**Was er kann.** Der einzige Knoten, der beim Heim-PC etwas bestellt: Er schickt Szene, Prompt und
Einstellungen ab — **nur auf «Ausführen», nie automatisch** — und zeigt danach Fortschritt, Bild und
Urteil.

**Wie er funktioniert.** Er sammelt alles, was an seinen Eingängen hängt, und dazu seine eigenen
Einstellungen:
* **Preset** — fertige Pakete aus Auflösung, Sonne und Samples (Entwurf schnell 32 · 960×600,
  Präsentation 256 · 1920×1200, Nacht 192 · 1920×1200, Innenraum 2048 · 4000×2667); ohne Preset gilt
  1600×1000 mit 128 Samples.
* **Auflösung**, **Qualität gegen Zeit** (mit geschätzter Rechenzeit), **Himmel** (vier Himmelsarten
  aus Blender) und **Umgebung drehen** (nur mit Himmel).
* **Bildwerkzeug** — welches KI-Bildmodell veredelt (Vorgabe Z-Image Turbo; dazu SDXL,
  FLUX.2 klein, Qwen-Image-Edit, Qwen-Image 2.1 mit offener Lizenz, FLUX.1-Krea nur im
  Forschungsprofil).
* Schalter **«nur Cycles»** (reines Blender-Bild ohne KI) und **«Strichzeichnung»** (Line-Art, ebenfalls
  ohne KI).
* Ein aufklappbares **Auftragsformular** (Fassade, Szene, Jahreszeit, Personen, Freitext) — seine
  Felder werden hinten an den Prompt gehängt.
Der Prompt, der wirklich abgeht, steht immer sichtbar am Knoten; fehlt er, obwohl die KI mitrechnen
soll, warnt der Knoten vorher.

**Was er auslöst.** Den ganzen Auftragsweg (siehe Übersicht): Auftrag an die Brücke → «wartet auf
Freigabe» → **Freigeben** → in der Reihe → der Abholer am Heim-PC rechnet (Vorlauf, Bild,
Geometrie-Prüfung, je Kamera) → **Bild + Urteil** zurück. Die Zustände am Knoten: bereit · gesendet ·
wartet auf Freigabe · wartet (in der Reihe) · rendert · fertig · Fehler · abgebrochen ·
Zeitüberschreitung (nach 30 min ohne Ergebnis) · veraltet. «Abbrechen» steht bereit, solange der
Lauf offen ist. Ab zwei Läufen zeigt der Knoten unter dem Bild eine Reihe der letzten Läufe. Jedes
fertige Bild ist eine Karte in der Kuratierfläche.

**Ein- und Ausgänge.** Eingänge **Szene** (Pflicht), **Prompt**, **Geometrie-Treue** (Zahl),
**Samples** (Zahl), **Kamera-Standpunkte** (Kameras). Ausgang **Bild** → Bildvergleich, Aufs Blatt.

**Visbox vs. KosmoOrbit.** In Visbox geht der Auftrag an den eigenen Server (`/bruecke`), und **jeder**
Auftrag wartet zuerst auf «Freigeben». Gerechnet wird nur, wenn am Heim-PC ein Abholer auf die
Auftragsablage der Mappe schaut; sonst bleibt der Auftrag in der Reihe stehen (die Brücke meldet den
Abholer-Zustand mit). Innenansichten bestellt dieser Weg in Visbox nicht: dafür braucht es Räume
im Dokument und ein IFC-Modell, Visbox schickt glb.

*Quelle:* `VIS_NODE_KATALOG.render`; `evaluiereGraph` Fall `render`; `NodeKoerper` Fall `render`,
`RenderBedienung`, `RenderErklaerungen` (`NodeCanvas.tsx`); `sendeGraphRenderAuftrag`,
`postRenderJob`, `freigebenJob`, `mappeJobStatus`, `BILDWERKZEUG_TEXTE`, `interiorFaehrt`
(`vis-jobs.ts`); `RENDER_PRESETS` (`render-presets.ts`); `RENDER_TIMEOUT_MS_DEFAULT`
(`vis-runtime.ts`); Visbox-Seite `knotenweg.lege_an`/`freigeben`/`gesundheit`, `abholer.verarbeiter`.

## Ausgabe

### 11 · Bildvergleich

**Was er kann.** Stellt bis zu drei Bilder nebeneinander, jedes mit seinem **Prüfurteil**: «QA ok»,
«QA ✗» oder «nicht beurteilbar», darunter der Vorbehalt (warum), Lieferhinweise und die Marke
«Lizenz offen», wo das Bildwerkzeug noch keine geklärte Lizenz hat.

**Wie er funktioniert.** Er holt sich für jeden Eingang das fertige Bild des verbundenen Render-
oder Aufnahme-Knotens. Ohne Linie zeigt er «verbinde Render-Bilder».

**Was er auslöst.** Nichts — er zeigt nur. Bewertet, ausgewählt und nachgearbeitet wird in der
Kuratierfläche.

**Ein- und Ausgänge.** Eingänge **Bild 1**, **Bild 2**, **Bild 3**. Kein Ausgang.

*Quelle:* `VIS_NODE_KATALOG.vergleich`; `NodeKoerper` Fall `vergleich`, `BildKachel`
(`NodeCanvas.tsx`); `qaUrteil`, `quelleAusLauf` (`varianten-diff.ts`).

### 12 · Aufs Blatt

**Was er kann.** Legt das verbundene Bild als Bild auf ein Plakatblatt in KosmoPublish — ein
Rückgängig-Schritt; der Titel ist einstellbar (Vorgabe «Visualisierung»).

**Wie er funktioniert.** Der Knopf «Aufs Blatt» ist nur aktiv, wenn ein Bild anliegt. Er holt das Bild
von der Brücke (bei einer Aufnahme liegt es schon vor) und platziert es auf einem freien Platz des
Blatts. Trägt das Bild eine offene Lizenz, sagt die Meldung es mit; abgelegt wird trotzdem.

**Was er auslöst.** Einen Eintrag im Dokument (KosmoPublish) und eine Meldung «Render liegt auf …».

**Ein- und Ausgänge.** Eingang **Bild**. Kein Ausgang.

**Visbox vs. KosmoOrbit.** Blätter gibt es in Visbox nicht. Der Knoten ist da, der Klick endet mit dem
Satz «Blätter gibt es in Visbox nicht — ‹Aufs Blatt› kommt mit der Rückkehr nach KosmoOrbit wieder»
(Stellvertreter `commands/publish.ts`).

*Quelle:* `VIS_NODE_KATALOG.blatt`; `NodeKoerper` Fall `blatt`; `bildAufsBlatt`, `aufnahmeAufsBlatt`,
`platziereBildAufsBlatt` (`vis-jobs.ts`); Stellvertreter `kosmo-kernel/src/commands/publish.ts`.

---

## Was im Code nicht eindeutig ist

* **Auto-Kamera, Hilfetext gegen Verhalten (KosmoOrbit).** Der Katalogtext sagt «Bestellt wird nur
  Eingang/Übersicht». Der Code bestellt «Innenraum» aber mit, sobald das Modell Räume hat
  (`istUeberDiesenWegBestellbar` mit `interiorFaehrt`, seit B117 Schritt 2) — dann geht auch IFC statt
  glb. Der Hilfetext ist älter als dieser Schritt. Betrifft KosmoOrbit; in Visbox gibt es keine Räume.
* **Bild-Referenz an Vergleich/Blatt.** Die Linie lässt sich ziehen, trägt aber kein Bild weiter
  (`bildQuelle` kennt nur Render und Aufnahme). Ob das so gewollt ist, sagt der Code nicht; der Katalog
  verspricht «Stil-Referenz, Vergleich».
* **Wer in Visbox den Abholer startet.** Der Server sagt nur, dass der Abholer auf die Ablage zeigen
  muss (`--auftragsablage`-Hilfe in `oberflaeche/server.py`). Ob er beim Start der Mac-App oder des
  Heim-PCs von selbst mitläuft, steht nicht in den gelesenen Dateien.
* **Zahl an «Samples».** Die Linie gilt nur, solange «Qualität gegen Zeit» am Render-Knoten leer ist.
  Am Knoten selbst steht das nirgends.
