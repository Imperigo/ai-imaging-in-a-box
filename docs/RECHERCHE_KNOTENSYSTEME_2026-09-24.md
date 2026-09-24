# Recherche Knotensysteme — was der Render-Knoten von anderen lernen kann

**Grundlage:** keine Messung — öffentliche Quellen, abgerufen am 24.09.2026 (Anhänge), und der
Stand unseres Render-Knotens in `kosmovis/` (Anhang D)
**Codestand:** `b5372fa`

**Stand:** 24.09.2026 (Sitzung 71 §8) · **Auftrag des Owners:** «mit dem Render-Knoten
anfangen, aber zuerst gründliche Recherche zu Referenzprodukten, z. B. Figma Weave … danach
andere Produkte finden und erweitern, was es an Knotensystemen für KI und Rendering gibt.»

**Anhänge (die ausführliche Fassung, jede Aussage mit Quelle und Belegmarke):**

| | Inhalt | Umfang |
|---|---|---|
| [A · Figma Weave](recherche/2026-09-24_knotensysteme/a_figma_weave.md) | jeder dokumentierte Knoten, Modell-Knoten, Kosten, Ergebnisse, App-Modus | 83 Hilfeartikel gelesen |
| [B · KI-Knotenwerkzeuge](recherche/2026-09-24_knotensysteme/b_ki_knotenwerkzeuge.md) | ComfyUI, Krea, FLORA, Magnific, Invoke, Griptape, Runway, Scenario, Adobe Firefly Graph u. a. | 23 Werkzeuge, 27 Muster |
| [C · Render-Knotensysteme](recherche/2026-09-24_knotensysteme/c_render_knotensysteme.md) | Blender, Houdini, Nuke, Unreal, Unity, Substance, TouchDesigner, Fusion, Grasshopper, Dynamo, V-Ray/Chaos, D5 und die KI-Werkzeuge für Architekten | 15 Familien, 25 Muster |
| [D · Unser Render-Knoten heute](recherche/2026-09-24_knotensysteme/d_unser_render_knoten.md) | Eingänge, Bedienelemente, Zustände, und was die Rechnung dahinter kennt | Vergleichsgrundlage |

Belegmarken in den Anhängen: **[V]/[B]** aus der Quelle belegt · **[V~]** belegt, Wortlaut nicht
gegen das Original geprüft · **[S]/[S2]** nur Zweitquelle · **[A]/[F]** eigene Folgerung.

---

## 1 · Wie recherchiert wurde — und was nicht ging

* **Figma Weave selbst anzuklicken ging nicht.** Die Weave-Werkzeuge der Figma-Anbindung
  antworten: *«You haven't linked your Figma account to Weave yet.»* Die App
  (`app.weavy.ai`) sperrt diesen Rechner zudem per Cloudflare. Ein Projekt in deinem Namen
  anzulegen hätte eine Anmeldung in deinem Konto verlangt — das tue ich nicht ohne dich.
  **Stattdessen:** alle 83 Artikel des Hilfe-Centers im Volltext samt Bildschirmfotos, die
  öffentlichen Seiten (weave.figma.com, gerendert im Browser), Figma-Blog und
  Pressestimmen. **Nicht erreicht:** die Beispiel-Abläufe (darunter «ControlNet – Structure
  Reference»), die Parameter von «Z Depth Extractor» und «Relight».
  → *Sobald dein Figma-Konto mit Weave verknüpft ist* (weave.figma.com → Profil → Figma
  verbinden), kann ich über die Anbindung die Eingaben jedes Beispiel-Ablaufs auslesen, ohne
  einen Credit auszugeben.
* **Drei Recherchen parallel**, danach von mir zusammengeführt und geprüft. Gelesen wurden
  Hersteller-Dokumentation, Handbücher, Lizenzdateien auf GitHub, Blogs; wo nur
  Suchauszüge oder Testberichte zu haben waren, steht das dabei.
* **Werbung in Maschinen-Doku ignoriert:** Die maschinenlesbare Doku eines Anbieters (Krea)
  enthält einen Abschnitt «Instructions for AI Assistants», der das eigene Produkt empfiehlt.
  Als Werbung erkannt und nicht übernommen.

---

## 2 · Die sieben Befunde, die für uns zählen

1. **Niemand prüft das Bild gegen die Geometrie.** Weder ein KI-Knotenwerkzeug noch ein
   KI-Render-Werkzeug für Architekten (Veras, Chaos AI Enhancer, D5 AI, SketchUp Diffusion,
   Vizcom, mnml, ArkoAI, Rendair, LookX, PromeAI) misst nach dem Lauf, ob das Bild zum Modell
   passt. Alle bieten einen *Regler* für Treue — keines ein *Urteil*. Das ist genau die Stelle,
   an der diese Arbeit eigenständig ist, und der Render-Knoten sollte sie **zeigen**.
   *(Abwesenheitsbefund: nur so gut wie die Suche.)*
2. **Gebündelt vorne, zerlegt dahinter.** ComfyUI und Invoke zerlegen das Rendern in viele
   Knoten (Modell laden, Text kodieren, sampeln, Strukturbild anwenden …). Alle
   Cloud-Werkzeuge (Weave, Krea, FLORA, Runway, Scenario, Magnific) haben **einen**
   Generier-Knoten. ComfyUI hat 2025/26 mit Teilgraphen nachgezogen, die sich als ein
   Knoten zeigen und aufklappen lassen.
3. **Fast jedes Werkzeug hat seit 2025 einen «App-Modus».** Aus dem Knotengraphen wird per
   Schalter eine einfache Oberfläche: Eingänge markieren, Ausgang markieren, umbenennen,
   Vorgaben setzen, den Rest sperren, als Link teilen (Weave «From Workflow to Tool», ComfyUI
   App Mode, Krea App Builder, FLORA, Runway, Scenario, Magnific, Invoke, Adobe). **Das ist
   unsere Lage mit zwei Ansichten** (Visbox-Seite und Knotenansicht, E26) — nur dass bei
   ihnen die einfache Ansicht *aus* dem Graphen entsteht.
4. **Aufwand vor dem Klick.** Weave zeigt den Preis beim Überfahren, im Panel, und live
   mitgerechnet («Runs × Preis») am Knopf; FLORA auf dem Run-Knopf, ComfyUI als Abzeichen.
   Fehlgeschlagene Läufe kosten bei FLORA nichts. Bei uns ist der Aufwand **Zeit auf der
   HomeStation**, und er ist vorab immer berechenbar (Kameras × Varianten × Auflösung).
5. **Ergebnisse stapeln statt überschreiben — mit Herkunft.** Weave hängt jeden Lauf an
   (Zähler «1 / 7», Galerie, «Show info» mit Prompt, Parametern, Startwert). Runway und FLORA
   halten eine Verlaufsliste im Knoten mit einer «aktiven» Ausgabe, die weiterfliesst.
6. **Geometrie ist bei ihnen «Referenz», bei uns Hauptsache.** Weave hat keinen eigenen
   Struktur-Knoten; Tiefe ist ein gewöhnliches Bild an einem Eingang «Control Image» und wird
   meist *aus Pixeln geschätzt*. Die Render-Programme dagegen (Blender, Houdini, Unreal)
   führen **jeden Pass als eigenen, benannten Anschluss**. V-Ray 7 und D5 erzeugen inzwischen
   eigene Hilfspässe nur für ihre KI — die Hersteller bestätigen damit unseren Aufbau
   «Geometrie-Pässe → KI».
7. **Die Treue-Regler der Architektur-Werkzeuge laufen in entgegengesetzte Richtungen.** Bei
   Veras und Rendair heisst «hoch» *freier*, bei SketchUp Diffusion und Vizcom *treuer*.
   Veras 4.0 (Feb. 2026, auf Googles Bildmodell) verschiebt die Treue sogar vom Regler in
   den Prompt. → Ein Regler braucht **eine** Richtung, mit Klartext an beiden Enden.

---

## 3 · Lizenzfunde (Regel 1 und 2) — ausdrücklich gemeldet

| Komponente | Lizenz, an der LICENSE-Datei geprüft | Folge |
|---|---|---|
| ComfyUI (Kern) | **GPL-3.0** | nur Vorbild; allenfalls als eigenes Programm hinter einer Prozessgrenze, wie Blender |
| ComfyUI-Oberfläche (`ComfyUI_frontend`) | **GPL-3.0** | **kein** Code, keine Stile übernehmen — Ideen sind frei, Quelltext nicht |
| chaiNNer | **GPL-3.0** | nur Vorbild |
| NodeTool | **AGPL-3.0** | nur Vorbild (AGPL greift auch im Netzbetrieb) |
| comfyui-deploy | **AGPL-3.0** | nur Vorbild |
| Blender | GPL (bekannt, NOTICE) | nur Begriffe |
| InvokeAI · Griptape Nodes (Engine) · React Flow · Node Banana | Apache-2.0 · Apache-2.0 · MIT · MIT | als Baustein denkbar — heute nicht nötig |

**Modellgewichte:** Weave und Krea führen FLUX.2-dev bzw. «Flux Dev LoRA» als wählbare
Modelle. Für uns bleiben sie ausgeschlossen (Non-Commercial). Weave zeigt die Lizenz im
Modell-Tooltip («Commercial Use») — **bei uns ist ein nicht-kommerzielles Gewicht gar nicht
wählbar**, nicht bloss markiert.

Alle übrigen Programme (Houdini, Nuke, Unreal, Substance, Grasshopper, Chaos, D5, die
Cloud-Dienste) sind proprietär: Vorbild, keine Abhängigkeit.

---

## 4 · Unser Render-Knoten heute, gegen die Muster gehalten

Aus Anhang D, in einem Satz je Punkt:

* **Stark:** Rendern nur auf Knopf, nie automatisch (wie Houdini, Weave). Freigabe durch einen
  Menschen. Ehrliche Zustände inklusive «veraltet» und «wartet, Grund unbekannt». Der
  wirklich gesendete Prompt steht am Knoten.
* **Schwach:**
  - Der Knoten ist **lang** (elf Bedienbereiche untereinander, Elemente rutschten schon unter
    den Fensterrand).
  - **Zwei Wege für dieselbe Zahl** (Samples als Eingang *und* als Wähler).
  - Die Geometrie-Pässe sind **unsichtbar** (die Szene geht als Ganzes hinein).
  - **Kein Startwert, keine Varianten, kein Aufwand vor dem Lauf, kein Verlauf.**
  - Das **Urteil** gehört nicht zum Knoten, sondern kommt erst über «Bildvergleich».
  - Die Rechnung dahinter kennt viel mehr (Startwert, Schritte, Strukturstärke, Denoise,
    Pässe, Prüfschwelle), als der Knoten erreicht. Und «Samples» heisst am Knoten etwas
    anderes als in der Rechnung: Cycles-Abtastungen, nicht Diffusionsschritte.

---

## 5 · Die Muster für den Render-Knoten, zusammengeführt

Aus 27 (B) + 25 (C) + 14 (A) Beobachtungen, doppelte zusammengelegt. Je Muster: **was**, **wer
es so macht**, **was es für uns hiesse**. Die Nummern verweisen auf die Anhänge.

| # | Muster | Vorbilder | Für unseren Render-Knoten |
|---|---|---|---|
| R1 | **Ein Knoten vorne, aufklappbar** | Weave, Krea, FLORA, Runway; ComfyUI-Teilgraphen; Unreal/Blender Gruppen (B1, B22, C9) | «Render» bleibt ein Knoten; «Gruppe öffnen» zeigt die Kette dahinter (Pässe → Bildmodell → Prüfung) für Fachleute |
| R2 | **Jeder Pass ein eigener, typisierter Eingang** | Blender Render Layers, Houdini, Unreal (C1–C3); Weave-Typfarben (A1) | Tiefe · Linien · Material-ID · Normalen als eigene Anschlüsse mit eigener Farbe; ein unverbundener Pass sichtbar «nicht genutzt»; das Modell fordert, was es braucht (C24) |
| R3 | **Herkunft der Struktur zeigen** | — (Weave: Tiefe meist geschätzt, A2) | Etikett «Tiefe · aus dem Modell» gegenüber «geschätzt». Das trägt später die Prüfung |
| R4 | **Ein Wert ist Feld *oder* Eingang, nie beides** | Blender, Krea, Invoke, Griptape, Unreal (B4, C4) | Löst die Doppelung bei Samples/Treue: Feld am Knoten, per Kabel übersteuerbar, dann verschwindet das Feld |
| R5 | **Kompakt: 4–6 Felder, Rest unter «Erweitert» oder im Seitenfeld** | Krea-Empfehlung, Griptape, Weave (Parameter im Panel, A-3.2) (B5, B6) | Sichtbar: Modus/Treue, Bildwerkzeug, Varianten, Startwert. Unter «Erweitert»: Schritte, Führung, Denoise, Abtastungen, Himmel |
| R6 | **Treue als benannte Absicht, ein Regler mit einer Richtung** | Veras/SketchUp-Presets, mnml «exact/creative»; Gegenbeispiel Treue-Richtungen (C7, C8) | Zwei, drei Modi in Klartext («Bestand treu», «Material erkunden», «Form erkunden») stellen Strukturstärke, Zeitfenster und Denoise gemeinsam; darunter ein Regler «frei ↔ modelltreu» |
| R7 | **Aufwand vor dem Klick, mitgerechnet** | Weave, FLORA, ComfyUI, Magnific; Blender-Zeitmessung (A3, B7, C13) | «≈ 4 min · 12 Bilder» am Knopf, aus Kameras × Varianten × Auflösung; nach dem Lauf die gemessene Zeit |
| R8 | **Varianten als Achsen, sichtbar als Punkteraster** | Houdini Wedge + Punkteraster je Arbeitseinheit, FLORA Cross/Zip (C12, C19, B18) | «Startwert × 3 · Kameras × 4 = 12»; je Bild ein Punkt mit Zustand; Klick zeigt dessen Einstellungen |
| R9 | **Ergebnisse stapeln, eines ist aktiv** | Weave, Runway, FLORA; Houdini Render Gallery (A5, B19, C18) | Filmstreifen der Läufe im Knoten; das aktive Bild fliesst weiter; «diese Einstellungen übernehmen» setzt den Knoten zurück |
| R10 | **Herkunft je Bild** | Weave «Show info» (A6) | Modell + Lizenz, Startwert, Abdruck der Pässe, Kamera, Parameter **und das Urteil** — bei uns im Manifest der Mappe schon da, am Knoten noch nicht |
| R11 | **Das Urteil ist ein Ausgang, nicht ein Anhängsel** | niemand; nächste Verwandte: Bifrost-Diagnoseausgang, Houdini-Zustand je Item, Galapagos-Fitness (C22) | Ausgänge «Bild», «Urteil» (bestanden / mit Vorbehalt / durchgefallen, mit Zahl und Messfläche) und «Kontrollbilder». Ein Folgeknoten kann danach sortieren oder neu anstossen |
| R12 | **Technischer Fehler ≠ inhaltliches Urteil ≠ blockiert** | Blender/Grasshopper/Dynamo drei Stufen; ComfyUI «blockiert durch Vorgänger» (C21, B16) | Rot = Lauf gescheitert; eigenes Zeichen = Bild weicht ab; grau = nicht geprüft, weil kein Bild |
| R13 | **Vergleich Bild ↔ Geometrie im Knoten** | Houdini «Unterschiede über Schwelle hervorheben», Nuke A/B, Weave Compare (C17, A12) | Schieber Bild ↔ Linienpass, Differenz über Schwelle — das sichtbare Gegenstück zur Zahl |
| R14 | **Veraltet statt automatisch neu; Cache nach Eingangs-Abdruck** | Grasshopper «Data Dam», Houdini TOP-Cache, ComfyUI/Griptape (C11, C14, B11–B13) | Ändert sich ein Eingang, springt der Knoten auf «veraltet» und sagt **welcher**; schon Gerechnetes wird von der Platte gelesen. Der Zwischenspeicher im Graph-Kern ist gebaut und gemessen, aber noch nicht am Produktivweg (README) |
| R15 | **Drei Laufumfänge** | Scenario, Griptape, Runway (B10) | «nur rendern» · «Pässe neu + rendern» · «rendern + prüfen» |
| R16 | **Startwert mit Schloss** | Veras, ComfyUI, Weave «Zufall ☐ + Zahl» (C25, B17, A7) | Startwert sichtbar am Knoten, gesperrt = gleich für alle Kameras (einheitliche Serie) |
| R17 | **Lizenz sichtbar im Modellwähler; Unzulässiges nicht wählbar** | Weave «Commercial Use», ComfyUI Modell-Abzeichen (A10, B25, B26) | Abzeichen «Modell · Lizenz» am Knoten; Prüfung beim Laden. Deckt sich mit Regel 1 |
| R18 | **Vorschau ist nicht Übernahme** | Grasshopper «Bake», Dynamo «Create Revit Elements» (C23) | Ein Bild ist Vorschau; erst «Übernehmen» macht es zum Projektbild der Mappe — eingefroren, mit Stand |
| R19 | **App-Modus aus dem Graphen** | Weave Tools, ComfyUI App, Krea, FLORA … (A8, B23) | Langfristig: Die Visbox-Seite (und das iPad) als App-Modus desselben Graphen — offen gelegte Felder werden ihre Bedienelemente |

---

## 6 · Ein erster Vorschlag, wie der Knoten aussehen könnte — **zum Zeichnen, nicht gebaut**

Aus Anhang C (Teil C), mit den Mustern oben abgeglichen:

```
┌─ RENDER ───────────────── z-image-turbo · Apache-2.0 ─── ◷ ≈ 4 min ─┐
│ ● Tiefe · aus dem Modell        Bilder  ●  [je Kamera]               │
│ ● Linien · aus dem Modell       Urteil  ●  [bestanden / Vorbehalt]   │
│ ○ Material-ID (nicht genutzt)   Kontrollbilder ●                     │
│ ● Prompt                                                             │
│ ● Kameras (4)                                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Modus   ( Bestand treu | Material erkunden | Form erkunden )         │
│ Treue   frei ─────────●── modelltreu                                 │
│ Startwert 1234 🔒     Varianten 3 × 4 Kameras = 12 Bilder            │
│ ▸ Erweitert (Schritte, Führung, Auflösung, Himmel …)                 │
├──────────────────────────────────────────────────────────────────────┤
│ ● ● ● ◐ ○ ○ ○ ○ ○ ○ ○ ○   3 fertig · 1 rendert · 8 warten            │
│ [aktives Bild]  ◀ 3/12 ▶   [Schieber Bild ↔ Linien]                  │
│ Urteil: 2 bestanden · 1 mit Vorbehalt                                │
│ [ Rendern · 12 Bilder ]   [ Abbrechen ]                              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7 · Was vor dem Zeichnen zu entscheiden ist (Fragen an den Owner)

Jede Frage mit meiner Empfehlung; entschieden wird erst am gezeichneten Blatt.

1. **Ein Knoten oder viele?** Empfehlung: *einer, aufklappbar* (R1). Die zerlegte Kette
   bleibt für Fachleute erreichbar.
2. **Geometrie-Pässe als eigene Eingänge zeigen?** Empfehlung: *ja* (R2, R3) — das ist das
   Sichtbarste, was uns von allen anderen unterscheidet.
3. **Treue als Modi in Klartext plus ein Regler?** Empfehlung: *ja* (R6). Die Namen der
   Modi wären eine eigene Entscheidung.
4. **Urteil als Ausgang des Render-Knotens — oder ein eigener Prüf-Knoten danach?**
   Empfehlung: *am Render-Knoten* (R11), weil kein Bild ohne Urteil weitergehen soll. Die
   Gegenposition: ein eigener Knoten macht die Prüfung als Schritt sichtbarer.
5. **Varianten und Verlauf im Knoten (Punkteraster, Filmstreifen)?** Empfehlung: *ja* (R8,
   R9). Das macht den Knoten grösser — dafür wandert «Erweitert» hinter einen Klick.
6. **Aufwand in Zeit am Knopf?** Empfehlung: *ja* (R7).
7. **Soll die Visbox-Seite langfristig ein «App-Modus» des Graphen werden?** Das ist eine
   grosse Richtungsfrage (R19) — sie betrifft E26 und die Rückkehr nach KosmoOrbit und muss
   heute nicht entschieden werden. Wichtig ist nur, dass der Render-Knoten ihr nicht im Weg
   steht.

**Was eine Änderung am Render-Knoten für E26 bedeutet:** Der Knoten lebt in wörtlich
kopierten Dateien (`NodeCanvas.tsx`, `visgraph.ts`). Jede Änderung macht sie zu
«geändert» in `kosmovis/HERKUNFT.json`, mit Grund — so war es vorgesehen, und `--pruefen`
erzwingt es. Die Rückkehr im Februar bringt die Änderungen dann als Paket mit.

---

## 8 · Offen

* **Weave vertiefen** braucht die Verknüpfung deines Figma-Kontos mit Weave (siehe §1).
* **Architektur-KI-Werkzeuge ohne öffentliche Doku** (ArkoAI, mnml, Rendair, PromeAI, LookX):
  Reglernamen nur aus Zweitquellen. Vor einem Zitat in der Arbeit im Werkzeug selbst prüfen.
* **Nicht dokumentiert bei Weave:** wie Fortschritt und Fehler im Knoten aussehen, ob
  zwischengespeichert wird.
