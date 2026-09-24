# Render- und Compositing-Knotensysteme — was ein KI-«Render»-Knoten von ihnen lernen kann

Recherche vom 24.09.2026 (nur öffentliche Webquellen, keine Konten, keine Logins).
Zweck: Entwurfsgrundlage für den Render-Knoten, der Geometrie-Pässe (Tiefe, Normalen,
Material-ID, Linien) plus Prompt/Stil entgegennimmt, ein Diffusionsmodell rechnet und Bilder
samt Qualitätsurteil ausgibt.

## Lesehilfe

* **[V]** = verifiziert, mit Quelle (Herstellerdoku, Handbuch oder Fachpresse, am 24.09.2026
  abgerufen). Wo nur eine Zusammenfassung eines Abrufwerkzeugs vorlag und nicht der
  Wortlaut, steht **[V~]** — inhaltlich belegt, Wortlaut nicht geprüft.
* **[S]** = nur Sekundärquelle (Blog, Drittanbieter-Test, Suchmaschinen-Auszug), nicht beim
  Hersteller bestätigt.
* **[F]** = Folgerung / eigene Übertragung auf unser Projekt, **keine** Quelle.
* Lizenzhinweis vorweg: Alle untersuchten Programme dienen nur als **Vorbild für Konzepte**.
  Es wird kein Code übernommen. Zwei Funde sind nach Projektregel 1 ausdrücklich zu melden:
  **Blender ist GPL** (bekannt, Regel 2) und **ComfyUI ist GPL-3.0** (LICENSE-Datei im
  Repo `Comfy-Org/ComfyUI` am 24.09.2026 geprüft). ComfyUI erscheint unten nur als
  Begriffsreferenz, nie als Abhängigkeit.

---

## Teil A · Die Systeme im Einzelnen

Jedes System wird entlang derselben neun Fragen beschrieben, soweit die Quellen etwas hergeben:
(1) Was ist der Render-/Ausgabeknoten, (2) Parameter und ihre Gruppierung, (3) Pässe/AOVs als
Ports, (4) Vorlagen und Übersteuerungen, (5) Fortschritt/Zustand, (6) Vorschau und Vergleich,
(7) Cache und «schmutzig»-Weitergabe, (8) Varianten/Wedging, (9) Fehler/Warnungen am Knoten.

### A1 · Blender (Compositor, Shader-, Geometry-Nodes)

**Render Layers Node — Pässe werden zu Ausgängen** [V]
* «Renders a View Layer and reads its Passes into the compositing node graph. […] This node
  has no input sockets.» Eigenschaften: *Scene*, *View Layer*; «The button next to the
  dropdown re-renders it immediately.» Ausgänge: *Image*, *Alpha* und «Render pass sockets —
  Additional outputs for any enabled render passes.»
  → https://docs.blender.org/manual/en/latest/compositing/types/input/scene/render_layers.html
* Konsequenz: Die **Liste der Ausgänge ist nicht fix**, sondern folgt dem, was in den
  Ansichtsebenen-Einstellungen eingeschaltet ist. Der Render-Knoten ist eine *Quelle* ohne
  Eingänge; die Rendereinstellungen liegen **nicht am Knoten**, sondern in Szene/Ansichtsebene.
  [V] (gleiche Quelle)

**File Output Node — der Schreibknoten** [V]
* Schreibt jeden verbundenen Eingang als eigene Datei: `{Directory}/{File Name}{Socket
  Name}{frame number}.{extension}`; Eingänge entstehen durch Hineinziehen; Schrägstrich im
  Eingangsnamen erzeugt Unterordner (`passes/diffuse`).
  → https://docs.blender.org/manual/en/latest/compositing/types/output/file_output.html

**Knoten-Anatomie, Sockel-Farben und -Formen** [V]
* Sockel sind farbcodiert nach Datentyp (Farbe gelb, Float hellgrau, Vektor dunkelblau,
  Geometrie seegrün, String hellblau, Boolean rosa, Menü dunkelgrau, Bundle türkis …).
* **Sockelform = Datenstruktur**: Kreis «dynamisch», Rechteck «Single» (ein Einzelwert),
  **Raute «Field»** (Wert pro Element; ein Einzelwert wird implizit auf alle Elemente
  verteilt), «Grid» (vier Quadrate), «List» (drei Striche); Mehrfach-Eingänge als Pille/Ellipse.
* Nicht verbundene Eingänge zeigen ihren **Vorgabewert direkt am Knoten** (editierbar).
* Implizite Typumwandlung (z. B. Farbe↔Float = Graustufe), mit Warnung, dass Information
  verloren gehen kann.
  → https://docs.blender.org/manual/en/latest/interface/controls/nodes/parts.html
* Felder: Verbindungen aus Feld-Sockeln werden **gestrichelt** gezeichnet; eine unzulässige
  Verbindung (Nicht-Feld an Feld) wird als **durchgezogene rote Linie** gezeigt.
  → https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/fields.html

**Vorschau, Stummschalten, Rahmen, Umleitungen, Gruppen** [V]
* *Preview*: kleines Bild über dem Knoten, pro Knoten ein-/ausschaltbar, global über
  Overlay abschaltbar (parts.html).
* *Mute* (M): «removes its contribution to the node tree, and makes all links pass through
  it without change. Links will appear red» — auch einzelne Verbindungen können stumm sein.
  → https://docs.blender.org/manual/en/latest/interface/controls/nodes/editing.html
* *Frame*: gruppiert optisch, mit Beschriftung, optional mit Textblock-Inhalt (Notiz).
  → https://docs.blender.org/manual/en/latest/interface/controls/nodes/types/layout/frame.html
* *Reroute*: ein Eingang, viele Ausgänge, reine Ordnung.
  → https://docs.blender.org/manual/en/latest/interface/controls/nodes/types/layout/reroute.html
* *Node Groups*: «similar to functions in programming: reusable, composable, and
  parametrizable»; grüne Titelleiste; «Input values that do not affect the output will be
  grayed out»; Hinweis, Ausgabeknoten (Material Output) *nicht* in Gruppen zu legen.
  → https://docs.blender.org/manual/en/latest/interface/controls/nodes/groups.html

**Viewer-Knoten und Vergleich** [V]
* Viewer ist «a diagnostic tool that allows users to inspect intermediate results without
  affecting the final output»; nur der aktive Viewer wird angezeigt; **Tastenbelegung
  Strg-1/2/…** weist Knoten einem nummerierten Viewer zu, die Nummer steht am Knoten —
  ausdrücklich «when comparing outputs».
  → https://docs.blender.org/manual/en/latest/compositing/types/output/viewer.html

**Inspektion: Sockelwerte, Warnungen, Zeiten** [V]
* *Socket Inspection* zeigt den Wert der letzten Auswertung; *Node Warnings*: «When the
  inputs to a node are invalid, it displays a warning in the title. Hovering over the warning
  icon shows the error message.» Nur ausgewertete Knoten haben Warnungen.
* *Node Timings Overlay*: Laufzeit je Knoten der letzten Auswertung; **Frames zeigen die
  Summe ihrer Knoten**, der Group-Output die Gesamtzeit.
  → https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/inspection.html
* *Warning Node*: eigene Meldung mit Schweregrad **Info / Warning / Error**, wird «by default
  […] propagated through parent node groups»; Anzeige im Warnungsfeld des Modifiers.
  → https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/output/warning.html

**Bake Node — Zwischenstand einfrieren** [V]
* «allows saving and loading intermediate geometries […] for better performance»; Modus
  *Animation* oder *Still*; Daten auf Platte oder in die Datei gepackt.
  → https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/geometry/operations/bake.html

---

### A2 · SideFX Houdini (ROPs, Solaris/Karma, PDG/TOPs, Flags)

**ROP-Knoten: Rendern ist ein Knopf am Knoten** [V]
* Render-Flags: *Bypass* (überspringt beim Abhängigkeits-Rendern, gelb), *Lock* («prevents
  upstream dependencies from rendering», rot + Badge), und der Render-Knopf: «This opens a
  render dialog to let you start rendering from this node. This is not really a flag.»
  ROPs lassen sich zu **Abhängigkeitsnetzen zwischen Render-Pässen** verbinden.
  → https://www.sidefx.com/docs/houdini/network/flags.html
* Flags allgemein: farbig gefüllt = an; Tastenkürzel Q/W/E/R/T; «Q or B is always bypass»;
  seltene Flags erscheinen als **Badge** statt als Flagfläche. (gleiche Quelle)

**Solaris/Karma: Einstellungen sind Szenedaten, nicht Knotenfelder** [V]
* Der *Karma Render Settings LOP* «creates render vars, a render product and a render
  settings primitive». Parameter: Output Picture (auch `ip` = Vorschaufenster), Camera,
  Resolution Mode (u. a. «Set Width, Compute Height from Aperture»), Engine CPU/XPU …
  → https://www.sidefx.com/docs/houdini/nodes/lop/karmarendersettings.html
* Das zugrunde liegende Modell (USD): *RenderSettings* (global) → Liste von
  *RenderProducts* (Dateien/Puffer) → *RenderVars* (AOVs/Pässe). Knoten arbeiten im
  **Create- oder Edit-Modus**; jeder Parameter hat links ein Menü, **wie** er geschrieben wird
  (setzen / nicht anfassen / …).
  → https://www.sidefx.com/docs/houdini/nodes/lop/rendersettings.html
* Karma XPU: fällt ein Gerät aus (z. B. GPU-Speicher voll), übernehmen die anderen;
  Ergebnis soll unabhängig von der Gerätemischung **identisch** sein.
  → https://www.sidefx.com/docs/houdini/solaris/karma_xpu.html

**Render Gallery: Schnappschüsse, Rückkehr, Differenzbilder** [V~]
* Schnappschüsse speichern das Bild **und die Netzwerk-Einstellungen**; «Revert network to
  this snapshot» (rückgängig machbar); Vergleichsmodi *No Diff, Split Horizontal/Vertical,
  Compare (absolute Differenz), Subtract, Blend, Highlight Differences (Schwelle)*;
  Hintergrund-Render als «live» Schnappschuss; Etiketten, Sterne, Farben, Tags, Filter.
  → https://www.sidefx.com/docs/houdini/ref/panes/rendergallery.html

**PDG/TOPs: Varianten als Arbeitseinheiten mit Zustandspunkten** [V]
* *Work items* sind die Arbeitseinheiten; *statische* sind vor dem Lauf bekannt («static is
  preferable to dynamic», weil der Umfang sichtbar ist), *dynamische* entstehen erst beim Lauf;
  nur Geändertes wird neu gerechnet («update only the tasks that changed»).
  → https://www.sidefx.com/docs/houdini/tops/intro.html
* **Punkteraster im Knoten**, ein Punkt je Work Item, Farbe = Zustand: hellgrün *läuft*,
  mittelgrün *fertig*, blaugrau *wartet*, grau *nicht gerechnet*, **orange *Warnung***,
  rot *fehlgeschlagen*, braun *abgebrochen*. Klick auf Punkt → Info-Fenster mit allen
  Attributwerten. Links am Knoten: Statussymbol mit **Fortschrittsring** und Zähler je Zustand;
  oben eine Taskleiste mit Fehler-/Warnungs-/Fertig-Zählern und «Cook output» / «Cook
  selected» / «Cancel all». Ab 200 Items Seiten; Tabelle für Tausende.
  → https://www.sidefx.com/docs/houdini/tops/ui.html
* TOP-Flags: *Output* (orange Ring = Ausgabe des Netzes), *Lock* friert die Work Items ein
  (Schneeflocken-Badge; Entsperren verwirft sie); Badge «dynamic» violett.
  → https://www.sidefx.com/docs/houdini/network/flags.html
* **Wedge TOP**: je Variante ein Work Item; Arten *Range, Value List, Bracket, Random
  Samples*; schreibt `wedgecount`, `wedgeindex`, `wedgenum`, `wedgetotal`; die Werte werden
  im Render-Knoten per `@attribut` referenziert (Beispiel `@pixelsamples`). Option «Overwrite
  Target Parameter on Work Item Selection»: **Auswahl eines Punktes setzt die Szene auf diese
  Variante** (mit Capture/Restore).
  → https://www.sidefx.com/docs/houdini/nodes/top/wedge.html ·
    https://www.sidefx.com/docs/houdini/tops/wedge.html
* **Cache Mode** (z. B. ROP Fetch): *Automatic* — «If the expected result file exists on
  disk, the work item is marked as cooked without being scheduled»; neue Dateien stromaufwärts
  machen den Cache veraltet; *Automatic (Ignore Upstream)*, *Read Files*, …
  → https://www.sidefx.com/docs/houdini/nodes/top/ropfetch.html
* Kontaktbögen: *ImageMagick TOP* setzt Varianten zu einer Montage zusammen («reviewing and
  evaluating wedged […] variations side-by-side»). [V~]
  → https://www.sidefx.com/docs/houdini/tops/tutorial_pdgimagemanipulation.html ·
    https://www.sidefx.com/docs/houdini/nodes/top/imagemagick.html

---

### A3 · Foundry Nuke

**Read/Write als Ein- und Ausgang; Rendern als Dialog** [V~]
* Write: Kanäle wählen (Checkboxen), Dateityp, **getrennte Pfade für volle Auflösung und
  Proxy**, Render-Knopf → Dialog mit Bildbereich (auch «1-5 8 10 15 22-25»), Ansichten,
  Proxy ja/nein, «Continue on error». Option **«read file»**: der Write-Knoten zeigt das
  **gerenderte Resultat von Platte** statt den Baum neu zu rechnen. «limit to range» deaktiviert
  den Knoten ausserhalb eines Bereichs.
  → https://learn.foundry.com/nuke/content/comp_environment/rendering/output_write_nodes.html
* Read: Fehlverhalten wählbar bei fehlenden Bildern — *error* (Vorgabe, Meldung im Viewer),
  *black*, *checkerboard*, *nearest frame*, *read input*. [S]
  → http://nukexexperts.blogspot.com/2013/05/nuke-book-read-node.html (Sekundär)

**Knoten-Indikatoren** [V]
* Kleine Zeichen am Knoten zeigen: welche Kanäle **verarbeitet** (breite Rechtecke) bzw.
  **durchgereicht** (schmale) werden, Maskierung, deaktiviert (per Taste D oder per Ausdruck),
  geklont, animiert, per Ausdruck gesteuert, Mehransichts-Split.
  → https://learn.foundry.com/nuke/content/getting_started/using_interface/working_nodes.html
* Postage Stamp: Knoten mit Bildminiatur; Miniaturen lassen sich aus Leistungsgründen
  statisch setzen oder abschalten. [V~]
  → https://learn.foundry.com/nuke/content/reference_guide/other_nodes/postagestamp.html ·
    https://support.foundry.com/hc/en-us/articles/207682435

**Viewer mit A/B-Puffern** [V~]
* Zwei Eingangspuffer A und B; Modi *wipe, stack, horizontal, vertical*; Wipe mit Griff
  im Bild, drehbar, überblendbar; Taste W blendet den Griff ein.
  → https://learn.foundry.com/nuke/content/timeline_environment/managetimelines/comparing_media.html

---

### A4 · Autodesk (Maya, 3ds Max, Bifrost, Flame)

**Maya Render Setup: Ebenen → Sammlungen → Übersteuerungen** [V]
* Übersteuerungen hängen an *Collections* in einer *Render Layer*; **absolut** («set the
  exact value») oder **relativ** («Multiply value to 1.5» für 50 % mehr); Sub-Collections für
  feinere Zuordnung.
  → https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=GUID-AA669F09-9CDB-4327-BC37-3E4ECD6A0E69
  → https://help.autodesk.com/view/MAYAUL/2024/ENU/?guid=GUID-646154F9-E4D2-4A3E-A0D9-B2F062960A4E

**3ds Max Slate Material Editor** [V~]
* Knotenansicht + Browser + Parameter-Editor; **ein Vorschaufenster kann jeden Knoten der
  aktiven Ansicht zeigen** (Auswahl per Liste); Vorschau wird mit dem aktiven
  Produktions-Renderer gerechnet, inkompatible Materialien werden ausgeblendet.
  → https://help.autodesk.com/view/3DSMAX/2024/ENU/?guid=GUID-7B51EF9F-E660-4C10-886C-6F6ADE9E8F56
  → https://help.autodesk.com/cloudhelp/2016/ENU/3DSMax/files/GUID-818D9B07-356F-4867-BD9B-1469EE202E9C.htm

**Bifrost: Terminal-Knoten mit Final / Proxy / Diagnostic** [V~]
* Terminal-Knoten tragen drei Flags **F, P, D**: *Final* (das renderbare Ergebnis), *Proxy*
  (schnelle Ansicht), *Diagnostic* (Fehlersuche); einzeln an/aus — sie bestimmen, **was
  überhaupt ausgewertet wird**. *Watchpoints* auf Verbindungen zeigen die durchfliessenden Werte.
  → https://help.autodesk.com/cloudhelp/2026/ENU/Bifrost-Common/files/build-a-graph/Bifrost_Common_build_a_graph_diagnose_and_debug_graphs_html.html
  → https://knowledge.autodesk.com/search-result/caas/CloudHelp/cloudhelp/ENU/Bifrost-MayaPlugin/files/output-objects-to-the-scene/Bifrost-MayaPlugin-output-objects-to-the-scene-output-to-terminal-html-html.html

**Flame Batch: Render- und Write-File-Knoten, Render-Liste** [V~]
* Mehrere Render-/Write-Knoten werden in einer **Render List** verwaltet (Ziel, Ausgabetyp);
  Option, das **Batch-Setup mit dem Resultat mitzuschreiben** («view and modify the original
  Batch setup»).
  → https://help.autodesk.com/cloudhelp/2022/ENU/Flame-Batch/files/GUID-D2E6282A-60B7-46B6-9363-BF546EA91AEB.htm
  → https://help.autodesk.com/cloudhelp/2020/ENU/Flame-Batch/files/GUID-63A5E127-75BC-4EF7-923B-416D31B02184.htm

---

### A5 · Unreal Engine (Movie Render Graph, Material Editor)

**Movie Render Graph (MRG) — der knotenbasierte Nachfolger der Render-Queue** [V]
* Drei Wege zum Rendern: *Movie Render Graph* (Knotengraph), *Movie Render Queue*
  (Vorlagen + Warteschlange), *Quick Render* (ein Klick).
  → https://dev.epicgames.com/documentation/unreal-engine/movie-render-pipeline-in-unreal-engine
* **Globals vs. Per-Layer**: «These settings can only be set once per render job and not per
  layer» (Warm-up, Output Settings, Sampling Method, Camera, Debug, CVar-Presets); z. B.
  *Temporal Samples* nur je Job, *Spatial Samples* je Ebene im Renderer-Knoten.
* **Render Layer Node als Schalter**: «The existence of the Render Layer node in your chain
  will signal for the Movie Render Graph to render this chain. Otherwise, logic will just be
  executed.» Deaktivieren per Kontextmenü.
* **Renderpfad per Knoten**: Deferred- oder Path-Traced-Renderer-Knoten je Ebene — «one layer
  take the Deferred render path and one take the Path Traced render path in the same Render
  Graph.»
* *Collections* (Akteure nach Bedingungen, Platzhalter `Foo*`) + *Modifiers* (versteckt,
  Schatten, Holdout); **gleichnamige spätere Collection übersteuert die frühere**.
* *Branch* (bool) und *Select* (Aufzählung) wählen, welcher Zweig gerechnet wird.
* **Variables and Exposed Properties**: Knoteneigenschaften lassen sich als Pins nach aussen
  heben und dann **je Job/Shot in der Queue setzen** — «Rather than having to have a graph per
  shot, you can expose desired parameters to be set at the job level».
* Ausgabe-Knoten je Dateiformat (EXR, PNG, ProRes …); Dateiname und OCIO **je Ebene** am
  File-Type-Knoten; *Subgraphs* für getrennte Versionsverwaltung.
  → https://dev.epicgames.com/documentation/unreal-engine/movie-render-graph-nodes-in-unreal-engine
  → https://dev.epicgames.com/documentation/unreal-engine/transitioning-to-the-movie-render-graph-from-movie-render-queue-in-unreal-engine?lang=en-US
* Programmierbar: Traversierung ab Globals, `override_output_resolution` u. ä. [V~]
  → https://dev.epicgames.com/documentation/unreal-engine/programming-a-render-in-mrg-in-unreal-engine

**Material Editor** [V~]
* «Start Previewing Node»: beliebigen Knoten im Viewport anzeigen, der Knoten färbt sich blau.
* *Stats*-Panel: Anzahl Shader-Instruktionen (Kosten) und Compilerfehler mit Ursache.
  → https://dev.epicgames.com/documentation/en-us/unreal-engine/previewing-and-applying-your-materials-in-unreal-engine
  → https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-editor-ui

---

### A6 · Unity (Shader Graph, VFX Graph)

* Shader Graph: *Main Preview* (Endergebnis, schwebend), *Blackboard* (Eigenschaften nach
  aussen), *Graph Inspector* mit **Graph Settings** und **Node Settings** (wechselt mit der
  Auswahl), *Preview Node* für Zwischenstände; Knoten einklappbar (versteckt unverbundene
  Ports), Vorschau je Knoten ein-/ausklappbar, Vorschau 2D/3D je Knoten; **Präzision je Knoten
  übersteuerbar** (erbt sonst vom Graphen). [V~]
  → https://docs.unity3d.com/Packages/com.unity.shadergraph@17.3/manual/Internal-Inspector.html
  → https://docs.unity3d.com/Packages/com.unity.shadergraph@13.1/manual/Node.html
  → https://docs.unity3d.com/Packages/com.unity.shadergraph@15.0/manual/Precision-Modes.html
* VFX Graph: **Contexts** (Spawn → Initialize → Update → Output) als senkrechte Stapel,
  in die *Blocks* («Every Block is in charge of one operation») gesteckt werden. Spawn hat
  Zustände *Playing, Stopped, Delayed*. [V~]
  → https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/Contexts.html

---

### A7 · Adobe Substance 3D Designer

* **Vererbung der Basisparameter**: Output Size, Output Format (Bit-Tiefe), Pixel Size,
  Tiling, **Random Seed** jeweils *absolute*, *relative to input* oder *relative to parent*;
  Empfehlung: Graph fast immer «Relative to Parent», Knoten sollen die Grösse nicht
  übersteuern. [V~]
  → https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/substance-graphs/inheritance-in-substance-compositing-graphs
  → https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/best-practices/graph-creation-etiquette
* **Output-Knoten ohne Parameter, aber mit Attributen**: *Identifier*, *Label*, *Group*,
  *Usage* (z. B. baseColor/normal) — gleiche *Usage* verbindet Aus- und Eingänge automatisch
  («Compact Material» fasst gleiche *Group* zu einer Verbindung zusammen). [V~]
  → https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/substance-graphs/nodes-reference-for-substance-graphs/atomic-nodes/output
  → https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/workspace/graph-view/link-creation-modes
* Exponierte Parameter mit sprechenden Labels und passendem Editor (Schieber, Winkel,
  Auswahlliste); Rechenzeit je Knoten in ms unter dem Knoten; Knoten-Miniaturen aus dem
  Bild-Cache; Doppelklick zeigt Knotenausgang in der 2D-Ansicht. [V~]
  → https://experienceleague.adobe.com/en/docs/substance-3d-designer/using/workspace/graph-view/the-graph-view
  → https://community.adobe.com/t5/substance-3d-designer-discussions/ms-time-below-nodes-meaning/m-p/13826094

---

### A8 · TouchDesigner (Derivative)

* **Pull-Prinzip**: «TouchDesigner will cook a node only when it needs to» — gerechnet wird,
  was sichtbar ist (Viewer offen), was ein Panel speist oder Daten nach aussen sendet.
  **Animierte gestrichelte Verbindungen** zeigen, dass stromaufwärts gerechnet wird;
  Mittelklick zeigt letzte Rechenzeit und Anzahl Rechnungen. [V~]
  → https://docs.derivative.ca/Cook
* Flags an allen Knoten: *Viewer* (Bild **im Knoten**), *Viewer Active* (interaktiv),
  *Lock* («data […] frozen in memory (and saved in the .toe)»), *Bypass*, *Cooking*. [V~]
  → https://docs.derivative.ca/Flag
* Familien (TOP, CHOP, SOP, POP, DAT, MAT, COMP) je eigene Farbe; verbunden werden kann nur
  innerhalb derselben Familie. [V~] → https://docs.derivative.ca/Operator
* *Cache TOP*: hält eine Bildfolge im GPU-Speicher, *Output Index* 0 = neuestes,
  negativ = weiter zurück. [V~] → https://docs.derivative.ca/Cache_TOP

---

### A9 · DaVinci Resolve Fusion

* Zwei Viewer, Tasten **1 und 2** laden den gewählten Knoten; am Knoten erscheinen
  **Viewer-Indikator-Punkte**, die zeigen, in welchem Viewer er liegt. [V~]
  → https://www.steakunderwater.com/VFXPedia/__man/Resolve18-6/DaVinciResolve18_Manual_files/part1658.htm
* *Saver* = Ausgabe, auch mitten im Baum für Zwischenstände; «Render All Savers»;
  *Cache to Disk* als Kontextmenü am Knoten. [S]/[V~]
  → https://www.steakunderwater.com/VFXPedia/__man/Fusion18-6/Fusion18_Manual_files/part99.htm
  → https://jmatthewturner.wordpress.com/2024/04/29/davinci-resolve-fusion-caching/ (Sekundär)

---

### A10 · Grasshopper für Rhino (Architektur)

* **Zustandsfarben der Komponente**: hellgrau = in Ordnung; **orange = Warnung** (frisch
  gesetzte Parameter sind orange: «input parameter failed to collect data»); **rot =
  Fehler**; dunkleres Grau = Vorschau aus; stumpfes Grau = deaktiviert («stop sending data to
  downstream components»); hellgrün = ausgewählt. Meldungen in **Sprechblasen** oben rechts.
  [V~]
  → https://modelab.gitbooks.io/grasshopper-primer/content/1-foundations/1-2/1_grasshopper-object-types.html
  → https://interactivetextbooks.tudelft.nl/rhino-grasshopper/Grasshopper_Rhino_course/4_Troubleshooting/Troubleshooting_Grasshopper/Colours&Errors/!index.html
* **Vorschau vs. Bake**: Vorschau-Geometrie im Rhino-Viewport ist nicht auswählbar; erst
  **Bake** macht sie zu echter, dann **nicht mehr mitlaufender** Geometrie. (ETH, Gramazio
  Kohler) [V~]
  → https://gramaziokohler.arch.ethz.ch/teaching-materials/03_grasshopper/2_working_in_gh/
* **«Fancy Wires»**: die Linie zeigt die Datenstruktur — einfach grau = ein Element, doppelt
  = Liste, doppelt gestrichelt = Baum, **orange = leer**. [V~]
  → https://modelab.gitbooks.io/grasshopper-primer/content/1-foundations/1-2/4_wiring-components.html
* **Datenbäume** und Abgleich (*Longest List* = Vorgabe, *Shortest List*, *Cross Reference*):
  mehrere Datenpakete laufen durch dieselbe Definition, ohne sie zu kopieren. [V~]
  → https://modelab.gitbooks.io/grasshopper-primer/content/1-foundations/1-4/3_data-stream-matching.html
  → https://developer.rhino3d.com/guides/grasshopper/gh-algorithms-and-data-structures/advanced-data-structures/
* **Teure Rechnungen bremsen**: *Data Dam* puffert Daten und lässt sie erst auf Auslösen
  durch; «Disable Solver» global. [S] (McNeel-Forum)
  → https://discourse.mcneel.com/t/datadam-vs-disable-vs-disable-solver-functionality-clarification/116785
* **Galapagos**: Evolutionslöser mit Eingängen *Genome* (Schieber) und *Fitness* (eine Zahl,
  maximieren/minimieren, optional Schwelle). [S]
  → http://wiki.bk.tudelft.nl/toi-pedia/Galapagos_Optimization
* **Colibri (Thornton Tomasetti)**: *Iterator* läuft alle Kombinationen von Schiebern durch,
  *Parameters* sammelt Kennzahlen, *Aggregator* schreibt CSV **und ein Vorschaubild je
  Iteration**; Auswertung im *Design Explorer* (Parallelkoordinaten). [V~]
  → https://grasshopperdocs.com/components/tttoolbox/colibriAggregator.html
  → https://github.com/tt-acm/Colibri.Grasshopper

### A11 · Dynamo (Revit)

* Knotenzustände als **Balken unter dem Knoten**: gelb = Warnung, rot = Fehler, blau = Info,
  grau mit Auge = Vorschau aus; roter senkrechter Balken = fehlende Eingänge; **durchscheinend
  blau = eingefroren** (Freeze friert auch alle nachfolgenden Knoten ein). Rangfolge
  «Error > Warning > Info > Preview». [V~]
  → https://primer2.dynamobim.org/4_nodes_and_wires
  → https://github.com/DynamoDS/DynamoPrimerNew/blob/master/4_nodes_and_wires/README.md
* **Ausführungsmodi** *Automatic / Manual (Run-Knopf) / Periodic*, **in der Datei gespeichert**.
  [V~] → https://dynamobim.org/issues/run-modes-manual-automatic-periodic/
* **Generative Design for Revit**: Studie mit *Randomize*, *Cross Product*, *Optimize*;
  Resultate im Dialog *Explore Outcomes*, Rangfolge per **Parallelkoordinaten oder
  Streudiagramm**, dann «Create Revit Elements» (Übernahme). [V~]
  → https://help.autodesk.com/cloudhelp/2023/ENU/Revit-GDiR/files/GUID-780EE9BF-010F-4148-A56C-E480F8D58F70.htm
  → https://help.autodesk.com/cloudhelp/2026/ENU/Revit-GDiR/files/GUID-8ACC2154-54C4-4929-951C-376CF3411A95.htm

---

### A12 · Chaos (V-Ray, Vantage, Enscape, AI Enhancer, Veras)

**V-Ray Render Elements und Frame Buffer** [V~]
* VFB-Verlauf: gerenderte Bilder werden als `.vrimg` gespeichert; **bis zu vier** lassen sich
  aus dem Verlauf zum Vergleich holen; A/B-Vergleich horizontal/vertikal, Anpassung bei
  ungleicher Auflösung (*Compare Fit Mode*).
  → https://documentation.chaos.com/space/VMAYA/111739034/V-Ray+Frame+Buffer
  → https://documentation.chaos.com/space/VRHINO/116129852/V-Ray+Frame+Buffer
* Cryptomatte als Render Element (Masken je Objekt/Material für die Nachbearbeitung).
  → https://documentation.chaos.com/space/VMAYA/111739047
* Vantage: Render Elements über «Setup» wählbar, als Einzeldateien oder in einer Datei;
  Z-Tiefe (Stand Vantage 2.0) ohne Min/Max-Steuerung. [S] (Forum)
  → https://forums.chaos.com/forum/chaos-vantage/chaos-vantage-general/1184995-ventage-2-0-render-elemet-z-depth-set

**Chaos AI Enhancer — die engste Parallele zu unserem Vorhaben** [V~]
* V-Ray 7 (3ds Max, Update 2) bringt ein eigenes Render Element **`VRayEnhancerData`**, das
  «automatically generates material IDs, object IDs and depth data for the render»; der
  Enhancer verarbeitet das in der Cloud. Der Enhancer basiert laut CG Channel auf **Stable
  Diffusion (trainiert auf LAION-5B)**.
  → https://www.cgchannel.com/2025/08/chaos-adds-new-ai-tools-to-v-ray-in-v-ray-7-for-3ds-max-update-2/
* Er erkennt Menschen, Vegetation und «focal areas» und fügt Details hinzu; gesteuert über
  **Objektmasken aus dem Renderer**; erweiterte Regler für Personen (Kleidung u. a.) und
  Vegetation; jede Verbesserung ist eine **eigene Ebene** («Every newly created enhancement is
  unique», Ebenen löschen/neu erzeugen); Dauer: Personen 15–30 s, Gesichter 15–20 s,
  Vegetation 10–30 s; Weg: EXR exportieren → Chaos Cloud → Bearbeiten.
  → https://blog.chaos.com/ai-enhancer-advanced-controls
  → https://blog.chaos.com/introducing-chaos-ai-enhancer
* In Enscape: Knopf in der Werkzeugleiste, Statusfenster «Enhancing…», Meldung «Image enhanced
  successfully», **Vergleich Original vs. verbessert über «compare versions» in der Cloud**.
  → https://documentation.chaos.com/space/ESKETCHUP/127964260/Chaos+AI+Enhancer

**Veras (EvolveLAB, seit 2025 Chaos)** [V~]
* Einstellungen (Doku «Veras for Enscape»): *Veras Presets*, *Aspect Ratio*, *Resolution*
  (1K/2K/4K), *Style Chips* («Append predefined text to the user prompt»), *Source Image*
  (Auto / Preview Image / Rendered Image / Manual Upload / None), *Prompt*, *Negative Prompt*,
  **Geometry Override** («Low values promote geometry detail retention, while high values can
  generate more creative results»), **Material Override** («Low values stay closer to the
  original aesthetic»), **Prompt Strength**, *Width/Height*, **Seed** («used to reproduce
  previous render results — even with different geometry»); bis zu **vier Bilder** je Lauf.
  → https://docs-chaos.atlassian.net/wiki/spaces/ESKETCHUP/pages/127737293
* Seed als Feststellmittel: «With the Seed, we can lock in the solution so that adjustments
  to our settings will have a more predictable change»; Render-Verlauf liefert Seeds zurück.
  → https://www.evolvelab.io/post/creating-consistency-with-ai-render-from-same-seed
* **Veras 4.0 (Feb. 2026)**: neue Engine auf Basis **Google Nano Banana Pro**; *Gallery Mode*
  (Rasteransicht vergangener Renderings zum Vergleich), *Image Reference as Input*,
  **Mehr-Winkel-Perspektiven «that retain correct geometry»**; laut Chaos-Blog ersetzt das
  «kontextbewusste» Verständnis die bisherigen binären Geometry-/Material-Override-Regler
  teilweise; die ältere Stable-Diffusion-Engine bleibt unbegrenzt verfügbar, Nano Banana Pro
  kontingentiert. [V~] (Wortlaut der Override-Aussage nicht geprüft)
  → https://blog.chaos.com/veras-4.0 ·
    https://www.chaos.com/press/chaos-veras-40-now-powered-by-nano-banana
* Veras ist inzwischen in Enscape, V-Ray und Corona integriert (Mai 2026). [V~]
  → https://architosh.com/2026/05/enscape-v-ray-and-corona-get-veras-ai-integration/

---

### A13 · D5 Render, Twinmotion, Autodesk Forma

* **D5** [V~]: *AI Enhancer* mit **«Enhancement Weight»** und **«Texture Strength»**,
  Bereichswahl; eigener **«AI Post Channel»**, der «improves the accuracy of region selection
  during AI Enhancer» (ein Hilfspass für die KI!); *AI Style Transfer* (stilisiert: Aquarell,
  Skizze, Voxel …; realistisch: Tageszeit/Jahreszeit, Referenzbild); *Inpainting* mit
  **Seed** (1…2147483648); Effekt-Nachbearbeitung mit *Transparency* («opacity of the
  AI-enhanced image»); *AI Atmosphere Match* aus Referenzbild; *D5 Hi* (Konzeptbilder aus
  Prompt).
  → https://docs.d5render.com/user-guide/ai/how-to-use-ai-post-processing
  → https://support.d5render.com/support/solutions/articles/72000649240-ai-features
* **Twinmotion** [V~]: In 2026.1 laut CG Channel **keine** KI-/Generativ-Funktionen
  (Neuerungen: Match Perspective, Lighting Channels, Kameraeigenschaften). Eine Behauptung
  über «KI-gestützte Materialvariation» stammt nur von einem Drittanbieter-Blog [S], nicht
  bestätigt.
  → https://www.cgchannel.com/2026/04/epic-games-releases-twinmotion-2026-1/
  → https://archigenai.com/twinmotion-ai-workflow-architects-2026.html (Sekundär)
* **Autodesk Forma** [V~]: KI-Bilder laufen über die **Veras-Erweiterung** («using their
  Forma or Revit model as the basis and prompting the rest»); daneben generative Layout-
  Werkzeuge (Site Automation, Building Layout Explorer), keine eigene Render-Knotenlogik
  gefunden.
  → https://blogs.autodesk.com/forma/2025/07/15/how-to-start-using-ai-for-design-storytelling/
  → https://adsknews.autodesk.com/en/news/building-layout-explorer-in-autodesk-forma/

### A14 · Architektur-KI-Werkzeuge — wie sie Treue, Stil, Ansicht, Varianten, Qualität zeigen

| Werkzeug | Geometrietreue | Stil | Kamera/Ansichten | Varianten/Reproduzierbarkeit | Qualität | Beleg |
|---|---|---|---|---|---|---|
| **Veras** | *Geometry Override* + *Material Override* (hoch = freier) | Presets, Style Chips, Prompt Strength, Negativ-Prompt | Quelle = aktuelle Ansicht; seit 4.0 Mehr-Winkel mit Geometrieerhalt | Seed, Render-Verlauf, bis 4 Bilder, Gallery Mode | kein Urteil angezeigt | [V~] Chaos-Doku, Blog |
| **Chaos AI Enhancer** | implizit: nur maskierte Bereiche (Personen, Vegetation) werden verändert | Regler je Objektklasse | Render aus V-Ray/Enscape/Corona | jede Verbesserung eigene Ebene | «compare versions» Original ↔ verbessert | [V~] Chaos-Blog/Doku |
| **SketchUp Diffusion** | **Respect Model Geometry** (hoch = Modell bleibt) | **Prompt Influence**, Preset-Stile | aktuelle SketchUp-Ansicht | — | — | [V~] Trimble-Blog |
| **Vizcom** | **Drawing Influence** | Stilliste + **Influence**; Palettes (4–30 Bilder) mit *Palette Influence*; Refine-Modus | Skizze/Bild | — | — | [V~] Vizcom-Doku |
| **ArkoAI** | Modi **Render** (Geometrie «100 % intakt») vs. **Ideate**; Geometrie-Regler | Ambiente, Material, Stil, Licht, Hintergrund, Jahreszeit; Presets; Negativ-Prompt | aktive Ansicht in SketchUp/Rhino/Revit | Seed für Konsistenz über Kamerawechsel | — | [S] Drittquellen, Hersteller-Seite ohne Detail |
| **mnml.ai** | Modi *creative* vs. *exact render* + Geometrie-Regler | 20+ Architekturstile, Stil-Inspirationsbild | Foto/Skizze/Screenshot | mehrere Material-/Farbvarianten | — | [S] |
| **Rendair** | *Creativity Strength* / Bildstärke; «Precision» vs. «Exploratory» | Prompt, Referenz | Screenshot 3D | — | — | [S] Rendair-FAQ |
| **PromeAI** | *Creativity/Fidelity*-Regler; 7 Modi, «Precise» am treuesten | Stile | Skizze | — | — | [S] |
| **LookX** | nicht öffentlich dokumentiert | eigene Modelle trainierbar, Style Adapter | SketchUp-/Rhino-Plugins | — | Upscaling, «Detail correction» | [V~] Website (ohne Reglernamen) |
| **D5 AI** | Bereichswahl + AI-Post-Channel; *Enhancement Weight* | Style Transfer, Atmosphere Match | D5-Kamera | Seed (Inpainting) | *Transparency* als Rückblende | [V~] D5-Doku |
| **Forma** | via Veras | via Veras | Forma-Modell | via Veras | — | [V~] |

Quellen für die Tabelle, soweit oben nicht genannt:
* SketchUp Diffusion: https://sketchup.trimble.com/en/blog/article/sketchup-x-genai-realize-your-vision-faster-with-diffusion
* Vizcom: https://docs.vizcom.com/styles-overview · https://vizcom.com/resources/docs/make-your-own-palette
* ArkoAI: https://arko.ai/f/release-20 (Seite ohne Detail abrufbar) · https://aicreativeblog.com/how-to-use-arko-ai-rendering-guide/ [S] · https://sourceforge.net/software/product/ArkoAI/ [S]
* mnml.ai: https://mnml.ai/product · https://windowsreport.com/mnml-ai-review/ [S]
* Rendair: https://rendair.ai/faq/the-best-workflow-for-concept-to-final-render [S]
* PromeAI: https://www.promeai.pro/blog/pencil-drawing-to-architecture-render/ · https://www.aitecture.com.au/post/architectural-sketching-and-rendering-with-promeai [S]
* LookX: https://www.lookx.ai/ · Praxistest: https://www.haynearchitects.com/exploring-ai-rendering-a-hands-on-test-of-arkoai-and-lookx/ [S]

**Befund quer über alle KI-Werkzeuge** [F, gestützt auf die Tabelle]:
1. **Alle** zeigen einen Regler «wie treu zur Geometrie» — aber jedes nennt ihn anders
   (Geometry Override, Respect Model Geometry, Drawing Influence, Creativity, Fidelity) und
   **die Richtung ist nicht einheitlich** (bei Veras/Rendair heisst «hoch» *freier*, bei
   SketchUp Diffusion/Vizcom heisst «hoch» *treuer*).
2. Viele bieten **zwei Modi statt nur eines Reglers** (ArkoAI Render/Ideate, mnml
   creative/exact, Rendair Precision/Exploratory, PromeAI «Precise») — das Wort «Modus»
   trägt die Absicht, der Regler die Feinheit.
3. **Kein einziges** untersuchtes Werkzeug zeigt ein **gemessenes Qualitäts- oder
   Treueurteil** am Resultat. Treue wird eingestellt, aber nie nachgemessen. Nächste
   Verwandte sind der Vorher/Nachher-Vergleich (Chaos «compare versions», D5 Transparency)
   und Seeds. → Hier liegt die Eigenständigkeit unseres Prototyps.
4. Chaos und D5 haben erkannt, dass die KI **eigene Hilfspässe** braucht
   (`VRayEnhancerData` mit Material-ID/Objekt-ID/Tiefe; D5 «AI Post Channel»). Das bestätigt
   unsere Architektur «Geometrie-Pässe → KI» von Herstellerseite.
5. Veras 4.0 zeigt die Gegenbewegung: Bei grossen Allzweck-Bildmodellen (Nano Banana Pro)
   **verlieren die Treue-Regler an Bedeutung**, Anweisungen im Prompt übernehmen. Für einen
   Render-Knoten heisst das: Die Treue-Steuerung muss **je Modell** anders aussehen können
   (Regler bei ControlNet-artigen Modellen, Textanweisung bei Instruktionsmodellen). [F]

### A15 · ComfyUI — nur als Begriffsreferenz (GPL-3.0, gemeldet)

* Knoten *Apply ControlNet (Advanced)*: **strength** (Vorgabe 1.0, 0–10), **start_percent**,
  **end_percent** — die Steuerung wirkt nur in einem Zeitfenster der Entrauschungsschritte.
  [S] (Drittanbieter-Doku)
  → https://comfyui-wiki.com/en/comfyui-nodes/conditioning/controlnet-apply ·
    https://www.runcomfy.com/comfyui-nodes/ComfyUI/ControlNetApplyAdvanced
* Ausführung mit Cache: nur geänderte Knoten werden neu gerechnet; Knoten können sich per
  `IS_CHANGED` als «immer neu» melden. [S]
  → https://github.com/Comfy-Org/ComfyUI/discussions/12546 · https://github.com/Comfy-Org/ComfyUI/blob/master/execution.py
* **Lizenz: GPL-3.0** → kein Import, keine Bündelung; nur Begriffe als Vorbild.

---

## Teil B · Synthese: 25 Muster für einen KI-«Render»-Knoten

Jedes Muster: **was es ist** · **wer es nutzt** (mit Status) · **Übertragung** auf unseren
Knoten [F]. Die Übertragungen sind Vorschläge, keine Entscheide — Entscheide gehören nach
Projektregel erst gezeichnet auf die Entwurfsfläche und dann ins Entscheidblatt.

### Gruppe 1 · Eingänge und Ausgänge

**M1 · Pässe sind Ports, und die Portliste folgt der Konfiguration.**
Wer: Blender Render Layers (Ausgänge je aktiviertem Pass) [V]; Houdini RenderVars [V];
Nuke Kanäle am Write [V~]; Unreal MRG File-Type-Knoten [V].
Übertragung: Tiefe, Normale, Material-ID, Linien als **einzelne, benannte Eingänge**, nicht
«Szene als Ganzes». Ein Pass, der nicht verbunden ist, wird am Knoten als «nicht genutzt»
sichtbar. Ausgänge ebenso aufgefächert: Bild(er), Urteil, Kontrollbilder (siehe M16).

**M2 · Sockelfarbe = Datentyp, Sockelform = Datenstruktur.**
Wer: Blender (Rechteck/Raute/Liste/Grid) [V]; Grasshopper «Fancy Wires» (einfach/doppelt/
gestrichelt/orange leer) [V~]; TouchDesigner Familienfarben [V~].
Übertragung: eigene Sockeltypen «Tiefenbild», «Normalenbild», «ID-Maske», «Linienbild»,
«Prompt», «Kamera»; und eine Form für **«ein Bild» vs. «Satz von Bildern je Kamera»**
(Liste/Baum), damit Mehrkamera-Läufe am Draht erkennbar sind. Leere Verbindung orange wie in
Grasshopper.

**M3 · Semantische Kennung am Ausgang (Usage/Identifier).**
Wer: Substance Output-Knoten mit *Identifier/Label/Group/Usage*, automatische Verbindung
nach gleicher Usage [V~]; Blender File Output (Sockelname → Dateiname/Unterordner) [V].
Übertragung: Pässe tragen eine feste Rolle (`depth`, `normal`, `material_id`, `lineart`),
damit der Render-Knoten sie **automatisch richtig zuordnet**, egal wie der Draht liegt; der
Sockelname bestimmt den Dateinamen im Ergebnisordner.

**M4 · Unverbundene Eingänge zeigen ihren Vorgabewert am Knoten — ein Weg, nicht zwei.**
Wer: Blender (Vorgabewert editierbar, verschwindet bei Verbindung) [V]; Unreal MRG
«Exposed Properties» als Pins [V]; Dynamo Rechtsklick → Default Value [V~].
Übertragung: Löst die heute doppelte Führung (z. B. Samples/Geometrie-Treue als Eingang
**und** als Wähler): Jeder Wert ist entweder Feld am Knoten **oder** verbundener Eingang —
per «als Pin nach aussen heben» umschaltbar.

### Gruppe 2 · Einstellungen, Vorlagen, Übersteuerungen

**M5 · Global vs. je Durchgang trennen.**
Wer: Unreal MRG *Globals* vs. *Per-Layer* (Temporal Samples nur je Job) [V]; Houdini
RenderSettings → RenderProducts → RenderVars [V]; Maya Render Layers [V].
Übertragung: Was für den ganzen Auftrag gilt (Modell/Backbone, Auflösung, Seed-Basis,
Rechenziel HomeStation) gehört in einen **Kopfbereich**; was je Kamera oder je Variante
wechseln darf (Prompt-Zusatz, Treue), in eine **Zeilen- oder Unterknoten-Ebene**.

**M6 · Übersteuerung mit Art: absolut oder relativ, und «spätere gewinnt».**
Wer: Maya absolute/relative Overrides [V]; Unreal «Collections of the same name later in
the graph will override the original» [V]; Houdini Parameter-Menü «wie schreiben» [V];
Substance *absolute / relative to input / relative to parent* [V~].
Übertragung: Eine Vorlage (Preset) setzt Grundwerte; der Knoten zeigt je Feld, ob der Wert
**geerbt** oder **übersteuert** ist (z. B. Punkt oder Kursivschrift), mit «zurück auf
Vorlage». Auflösung «relativ zur Vorlage» statt fester Pixelzahl.

**M7 · Vorlagen sind benannte Absichten, nicht Zahlensätze.**
Wer: Veras Presets + Style Chips (hängen Text an den Prompt) [V~]; SketchUp Diffusion
Preset-Stile [V~]; ArkoAI Render/Ideate [S]; mnml creative/exact [S]; Unreal MRQ-Presets [V].
Übertragung: Zwei bis drei **Modi mit Klartextnamen** («Bestand treu», «Material/Licht
erkunden», «Form erkunden») stellen Treue, Stärke und Denoise gemeinsam; der Feinregler ist
darunter optional. Chips, die Prompt-Text anhängen, zeigen den **wirklich gesendeten Prompt**.

**M8 · Einheitliche Richtung und Klartext für «Treue».**
Wer: Gegenbeispiele Veras (hoch = freier) vs. SketchUp Diffusion/Vizcom (hoch = treuer)
[V~].
Übertragung: Ein Regler, eine Richtung: **«hoch = näher am Modell»**, beschriftet mit beiden
Polen («frei ↔ modelltreu»). Intern darf das auf ControlNet-Stärke, Zeitfenster
(start/end, vgl. ComfyUI [S]) und Denoise abbilden — aussen bleibt eine Bedeutung.

**M9 · Parameter nach aussen heben statt Graph kopieren.**
Wer: Unreal MRG «expose desired parameters to be set at the job level» [V]; Blender Node
Groups (Group Input) [V]; Substance exponierte Parameter mit Label/Editortyp [V~];
Shader-Graph-Blackboard [V~].
Übertragung: Der Render-Knoten ist intern eine Gruppe (Pässe vorbereiten → Diffusion →
Nachbearbeitung → Urteil); aussen sichtbar nur die gehobenen Felder. Fortgeschrittene
Innereien auf Klick («Gruppe öffnen»), nicht als langer Knoten.

**M10 · Bedingte Zweige als eigene Knoten, nicht als Häkchen.**
Wer: Unreal MRG *Branch* (bool) / *Select* (Aufzählung), Renderer-Wahl per verbundenem
Knoten [V]; Houdini Bypass [V].
Übertragung: «nur Cycles (ohne KI)» oder «mit/ohne Linien» wird zu einem Umschalter vor
bzw. hinter dem KI-Schritt, sichtbar im Graphen, statt zu einem versteckten Häkchen.

### Gruppe 3 · Ausführung, Zustand, Fortschritt

**M11 · Rendern ist ein bewusster Knopf; Ausführungsmodus sichtbar und gespeichert.**
Wer: Houdini ROP Render-Knopf «not really a flag» [V]; Dynamo *Automatic/Manual/Periodic*,
in Datei gespeichert [V~]; Grasshopper Data Dam / Disable Solver [S]; TouchDesigner
Pull-Prinzip (rechnet nur, was sichtbar/benötigt ist) [V~].
Übertragung: Teure GPU-Läufe laufen **nur auf Auslösen** (wie heute), aber der Modus
(«manuell») steht als Zustand am Knoten, und Änderungen stromaufwärts machen den Knoten
**«veraltet»** statt ihn neu zu starten (Data-Dam-Prinzip).

**M12 · Zustand pro Arbeitseinheit, nicht nur pro Knoten.**
Wer: Houdini TOPs Punkteraster (grün/blaugrau/grau/orange/rot/braun), Statussymbol mit
Fortschrittsring und Zählern [V]; Houdini Taskleiste mit Fehler-/Warnungszählern [V].
Übertragung: Bei n Kameras × m Varianten zeigt der Knoten **ein Punkteraster**; jeder Punkt
ist ein Bild mit Zustand (wartet auf GPU / rendert / fertig / **Urteil: bestanden / mit
Vorbehalt / durchgefallen**). Klick → Detail mit allen Parametern dieses Bildes (Seed, Treue,
Prompt, Zeit).

**M13 · Laufzeit und Kosten am Knoten.**
Wer: Blender Node Timings (Frames summieren) [V]; Substance ms unter dem Knoten [V~];
Unreal Material Stats (Instruktionen = Kosten) [V~]; TouchDesigner Rechenzeit per Mittelklick
[V~]; Chaos gibt Dauern je Enhancer-Art an [V~].
Übertragung: Letzte Rechenzeit je Bild und **Schätzung vor dem Start** (Bilder × Schritte ×
Auflösung) am Knoten — für einen HomeStation-Worker mit Warteschlange entscheidend.

**M14 · Einfrieren und Cache mit klarer Invalidierung.**
Wer: Houdini TOP *Lock* (Schneeflocke; Entsperren verwirft) [V], *Cache Mode Automatic*
(Datei vorhanden → gilt als gerechnet; neue Dateien stromaufwärts → veraltet) [V];
TouchDesigner *Lock* (in Datei gespeichert) [V~]; Blender *Bake Node* [V]; Dynamo *Freeze*
(inkl. nachgelagerter Knoten) [V~]; Nuke Write «read file» [V~].
Übertragung: Ergebnis-Schlüssel = Hash aus Pässen + Prompt + Modell + Seed + Einstellungen.
Ist er schon gerechnet, wird **von Platte gelesen, nicht neu gerechnet**; ändert sich ein
Pass, springt der Knoten auf «veraltet» und zeigt, **welcher Eingang** es verursacht hat.
Ein «Festhalten»-Schalter friert einen guten Stand ein.

**M15 · Stummschalten/Durchreichen mit sichtbarer Spur.**
Wer: Blender Mute (Verbindungen rot) [V]; Houdini/TouchDesigner/Nuke Bypass (gelb bzw.
Indikator) [V]; Grasshopper Disabled (stumpfgrau) [V~].
Übertragung: KI-Schritt überbrücken → das Cycles-Bild läuft durch; die Verbindung zeigt es
farblich. Nützlich für A/B «mit/ohne KI».

### Gruppe 4 · Vorschau, Vergleich, Varianten

**M16 · Vorschau im Knoten und auf Nummerntasten.**
Wer: Blender Node Preview + Viewer Strg-1/2 mit Nummer am Knoten [V]; Fusion Viewer-
Indikatoren 1/2 am Knoten [V~]; TouchDesigner Viewer-Flag (Bild im Knoten) [V~]; Unreal
«Start Previewing Node» (Knoten färbt sich blau) [V~]; Nuke Postage Stamps [V~].
Übertragung: Miniatur im Knoten; **zusätzlich die Kontrollbilder** (welcher Pass wie stark
wirkte, Differenz Bild↔Geometrie) auf Tastendruck in den grossen Viewer schicken, mit
Nummernmarke am Knoten.

**M17 · A/B-Vergleich als Grundfunktion, mit Differenzbild.**
Wer: Houdini Render Gallery (Split, Compare, Subtract, Blend, **Highlight Differences mit
Schwelle**) [V~]; Nuke Viewer A/B wipe/stack [V~]; V-Ray VFB bis 4 Bilder aus dem Verlauf
[V~]; Chaos «compare versions» [V~]; D5 Transparency [V~].
Übertragung: Neben dem Bild immer der Vergleich **KI-Bild ↔ Geometriepass** (Kanten über
Bild, Tiefenkanten-Differenz) — das ist das sichtbare Gegenstück zum Qualitätsurteil.
«Differenzen über Schwelle hervorheben» ist fast wörtlich unser QA-Blick.

**M18 · Schnappschuss = Bild + Einstellungen, mit Rückkehr.**
Wer: Houdini Render Gallery «Revert network to this snapshot» [V~]; Veras Render-Verlauf mit
Seed-Übernahme [V~]; Flame «Batch Setup» mit dem Resultat speichern [V~]; V-Ray VFB-Verlauf
[V~].
Übertragung: Jedes erzeugte Bild trägt seine vollständigen Einstellungen (Manifest) mit;
«diese Einstellungen übernehmen» setzt den Knoten zurück. Sterne/Etiketten/Tags zum
Aussortieren (Houdini) [V~].

**M19 · Varianten als Wedge: Achsen deklarieren, Kombinationen erzeugen, Werte je Item.**
Wer: Houdini Wedge TOP (Range/Value List/Bracket/Random, `wedgeindex`, Auswahl setzt die
Szene) [V]; Colibri Iterator → Aggregator mit **Bild je Iteration** [V~]; Dynamo Generative
Design *Randomize / Cross Product / Optimize* [V~]; Grasshopper Datenbäume/Cross Reference
[V~]; Veras bis 4 Bilder je Lauf [V~].
Übertragung: Varianten nicht als «Anzahl», sondern als **Achsen** (Seed × Treue × Stil ×
Kamera), mit Vorab-Anzeige der Gesamtzahl («statisch vor dynamisch», Houdini) — wichtig für
GPU-Zeit. Jede Variante ist ein Punkt in M12.

**M20 · Kontaktbogen und Rangfolge statt Einzelbild.**
Wer: Houdini ImageMagick-Montage für Wedges [V~]; Colibri/Design Explorer
(Parallelkoordinaten) [V~]; Dynamo *Explore Outcomes* (Parallelkoordinaten/Streudiagramm)
[V~]; Veras *Gallery Mode* [V~]; Galapagos Fitness [S].
Übertragung: Varianten erscheinen als **Raster, sortierbar nach Urteil** (z. B. Geometrietreue
auf dem Gebäude) — das QA-Urteil wird damit zur *Fitness*, nach der sortiert und
vorausgewählt wird. «Übernehmen» (Dynamo «Create Revit Elements», Grasshopper **Bake**)
macht aus einer Variante das freigegebene Bild.

### Gruppe 5 · Fehler, Warnungen, Urteil

**M21 · Drei Schweregrade am Knoten, mit Weitergabe nach oben.**
Wer: Blender Warning Node *Info/Warning/Error*, «propagated through parent node groups» [V];
Blender Warnsymbol im Titel mit Tooltip [V]; Grasshopper grau/orange/rot + Sprechblase [V~];
Dynamo Balken gelb/rot/blau, Rangfolge «Error > Warning > Info» [V~]; Houdini TOP orange
Warnung / rot Fehler je Item [V].
Übertragung: Das Qualitätsurteil nutzt **dieselbe dreistufige Sprache** wie Fehler — aber
**getrennt** davon: Ein technischer Fehler (GPU weg) ist rot; ein *inhaltlicher* Befund
(Bild weicht von Geometrie ab) ist ein Urteil «durchgefallen» mit eigenem Symbol. Beides
wandert in übergeordnete Gruppen und in die Knotentitelzeile.

**M22 · Das Urteil ist ein Ausgang, kein Anhängsel — mit Vorbehalt und Beleg.**
Wer: **niemand** unter den KI-Werkzeugen [F, siehe A14 Befund 3]. Nächste Verwandte:
Galapagos-Fitness als Zahl [S], Houdini Work-Item-Status [V], Bifrost *Diagnostic*-Ausgang
neben *Final* und *Proxy* [V~], Unreal Stats-Panel [V~].
Übertragung: Der Render-Knoten hat neben «Bild» einen Ausgang **«Urteil»** (bestanden /
mit Vorbehalt / durchgefallen, Zahl, Schwelle, *auf welcher Fläche gemessen*) und einen
**Diagnostic-Ausgang** (Kontrollbilder), analog Bifrost F/P/D. So kann ein nachgelagerter
Knoten nach Urteil filtern, sortieren oder neu anstossen.

### Zusatz · Muster mit Architekturbezug

**M23 · Vorschau ist nicht Übernahme («Bake»).**
Wer: Grasshopper Preview vs. Bake (gebackene Geometrie läuft nicht mehr mit) [V~]; Dynamo
Generative Design «Create Revit Elements» [V~]; Chaos Enhancer als eigene Ebene [V~].
Übertragung: Ein KI-Bild ist zunächst Vorschau; erst «Freigeben/Übernehmen» macht es zum
Projektbild — dann eingefroren und vom Graphen entkoppelt, mit Vermerk, aus welchem Stand es
stammt.

**M24 · Hilfspässe gezielt für die KI erzeugen.**
Wer: V-Ray `VRayEnhancerData` (Material-ID, Objekt-ID, Tiefe) [V~]; D5 «AI Post Channel» [V~];
Chaos Enhancer mit Objektmasken aus dem Renderer [V~]; Blender/V-Ray Cryptomatte [V]/[V~].
Übertragung: Der Knoten stromaufwärts («Pässe») liefert **genau die Pässe, die das gewählte
Modell braucht** — der Render-Knoten meldet fehlende Pässe als Warnung (orange, M21), statt
still ohne sie zu rechnen.

**M25 · Reproduzierbarkeit über Ansichten hinweg: Seed als Feststellhebel.**
Wer: Veras Seed «even with different geometry», Render-Verlauf liefert Seed zurück [V~];
ArkoAI Seed über Kamerawechsel [S]; D5 Inpainting-Seed [V~]; Substance *Random Seed* als
vererbbarer Basisparameter [V~].
Übertragung: Seed sichtbar am Knoten (mit Schloss), **je Kamera gleich** als Vorgabe, damit
eine Kameraserie einheitlich wirkt; Varianten entstehen bewusst über die Seed-Achse (M19).

---

## Teil C · Skizze: Wie der Knoten damit aussehen könnte [F]

*(Nur Vorschlag zum Zeichnen auf der Entwurfsfläche — nicht gebaut, nicht entschieden.)*

```
┌─ KI-Render ─────────────────────────── ⚠ 1 · ◷ ~4 min · ● manuell ─┐
│ Eingänge                              Ausgänge                      │
│ ◆ Tiefe          (depth)              ▭ Bilder      [Liste je Kamera]│
│ ◆ Normalen       (normal)             ▭ Urteil      [bestanden/…]    │
│ ◇ Material-ID    (nicht verbunden)    ▭ Diagnose    [Kontrollbilder] │
│ ◆ Linien         (lineart)                                           │
│ ▭ Prompt / Stil                                                      │
│ ▭ Kameras        [Liste]                                             │
├──────────────────────────────────────────────────────────────────────┤
│ Modus  ( Bestand treu | Material erkunden | Form erkunden )          │
│ Treue  frei ───────●── modelltreu         (geerbt aus Modus)         │
│ Seed   1234 🔒     Varianten: Seed×3 · Kameras×4 = 12 Bilder          │
├──────────────────────────────────────────────────────────────────────┤
│ ● ● ● ◐ ○ ○ ○ ○ ○ ○ ○ ○    3 fertig · 1 rendert · 8 wartet           │
│ [Miniatur]  [A/B mit Linienpass]   Urteil: 2 ✓ · 1 mit Vorbehalt      │
│ [ Ausführen ]  [ Abbrechen ]   … mehr (Gruppe öffnen)                │
└──────────────────────────────────────────────────────────────────────┘
```

Zeichenerklärung: ◆ verbunden, ◇ nicht verbunden (Warnung, falls das Modell den Pass
braucht), ▭ Einzelwert/Liste; Punkte = Bilder mit Zustand (M12).

---

## Teil D · Lücken und Vorbehalte

* **Wortlaut nicht geprüft** bei allen [V~]-Stellen: Das Abrufwerkzeug liefert eine
  Zusammenfassung, nicht den Originaltext. Wörtlich geprüft (per direktem HTML-Abruf) sind
  die Blender-Handbuchseiten, die Houdini-Seiten `flags.html`, `tops/ui.html`,
  `tops/intro.html`, `ropfetch.html`, `rendersettings.html`, `karmarendersettings.html`
  sowie die Unreal-MRG-Knotenseite.
* **ArkoAI, mnml.ai, Rendair, PromeAI, LookX**: keine öffentliche Herstellerdoku mit
  Reglernamen gefunden; Angaben aus Drittquellen [S]. Vor einer Zitierung in der Arbeit
  im Werkzeug selbst prüfen (braucht Konto — hier bewusst nicht gemacht).
* **Twinmotion**: keine KI-Funktion beim Hersteller belegt (Stand 2026.1).
* **Chaos Vantage**: Liste der Render Elements nicht abrufbar (Doku leitet auf Startseite um).
* **Veras 4.0 / Override-Regler**: Ob Geometry/Material Override in der Nano-Banana-Engine
  ganz entfallen oder nur ergänzt werden, ist aus dem abgerufenen Text nicht eindeutig.
* **Fusion**: Knoten-Details (Cache-Anzeige, Render-Bereich) nur teilweise belegt.
* **Lizenzen**: Blender (GPL) und ComfyUI (GPL-3.0) sind nur Vorbilder. Houdini, Nuke,
  Maya, 3ds Max, Flame, Unreal, Unity, Substance, TouchDesigner, Resolve, Rhino/Grasshopper,
  Dynamo-Studio-Teile, Chaos-/D5-Produkte sind proprietär bzw. kommerziell — ebenfalls nur
  Vorbild, keine Abhängigkeit. Dynamo Core ist Apache-2.0 (nicht in dieser Sitzung geprüft).

## Neue Fachbegriffe (für `docs/LEXIKON.md` zu prüfen)

AOV / Render-Pass · Render Element · Cryptomatte · Wedge / Wedging · Work Item · Cooking
(«Kochen» eines Knotens) · Pull-Prinzip · Bypass · Mute · Bake (Grasshopper/Blender) ·
Override (absolut/relativ) · Seed · ControlNet-Stärke / start–end-Fenster · Proxy ·
Postage Stamp · Parallelkoordinaten · Fitness (Galapagos) · Node Group / Subgraph · Reroute.
