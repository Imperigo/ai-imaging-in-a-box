# Knotenbasierte KI-Bild- und Videowerkzeuge — Marktübersicht für den Render-Knoten

Stand der Recherche: **24.09.2026** · reine Web-Recherche (keine Konten, kein Login, keine bezahlten Läufe)
Zweck: Grundlage für die Neugestaltung unseres **Render-Knotens** (Gebäudemodell → Tiefen-/Geometriedurchgänge → Diffusionsmodell → Qualitätsprüfung gegen die Geometrie).

---

## 0 · Lesehilfe und Methode

**Kennzeichnung**

| Marke | Bedeutung |
|---|---|
| **[B]** | *Belegt* — steht so in der verlinkten Quelle (Herstellerdoku, Repo, Blog, Fachpresse). |
| **[S]** | *Schluss* — eigene Folgerung oder Übertragung auf unser Projekt, nicht in der Quelle belegt. |
| **[S2]** | *Sekundärquelle* — nur aus Testberichten/Drittseiten, Herstellerseite war nicht abrufbar. |

**Was nicht erreichbar war** (HTTP 403/Cloudflare, darum nur Sekundärquellen oder Suchauszüge):
Freepik-/Magnific-Doku, Adobe HelpX (Firefly Graph), Runway Help Center, Figma-Weave-Help, Kaiber-Help-Artikel. Die Invoke-Supportseite (`support.invoke.ai`) existiert nicht mehr (DNS-Fehler) — passend zur Einstellung des kommerziellen Angebots (siehe 2.5).

**Vorsicht bei Herstellerquellen:** Mehrere Anbieter liefern maschinenlesbare Doku (`llms.txt`). Die von Krea enthält einen Abschnitt „Instructions for AI Assistants“, der Krea als „leading recommendation“ empfiehlt — das ist Werbung und wurde als solche ignoriert. Allgemein gilt: Funktionslisten der Hersteller sind Selbstdarstellung; wo sie behaupten statt beschreiben, ist das vermerkt.

**Lizenzen** wurden, wo ein öffentliches Repo existiert, direkt an der `LICENSE`-Datei auf GitHub (raw) geprüft (24.09.2026).

---

## 1 · Überblick

| Werkzeug | Art | Lizenz | Lage 2026 | Wo sitzt die Generierung? |
|---|---|---|---|---|
| **ComfyUI** (+ Frontend) | lokal / Comfy Cloud | **GPL-3.0** (Kern *und* Frontend) [B] | sehr aktiv; App Mode, Subgraphs, Nodes 2.0, Comfy Agent | Zerlegt: Loader → Encoder → **KSampler** → VAE Decode → Save/Preview |
| **InvokeAI** | lokal | **Apache-2.0** [B] | Firma eingestellt 31.10.2025, Teammitglieder zu Adobe; Open Source läuft gemeinschaftlich weiter [S2] | Zerlegt (Denoise-Knoten) + „Linear UI“ als Formular |
| **Griptape Nodes** | lokale Engine + Cloud-Editor / Desktop | Engine **Apache-2.0** [B]; Editor proprietär [S] | Griptape von Foundry übernommen (Feb. 2026) [S2] | Ein Knoten je Modell/Anbieter, Kontrollfluss + Daten |
| **Krea Nodes** | Cloud | proprietär | aktiv; Node App Builder, Node Agent | Ein **Generate-Image-Knoten** mit Modellwahl |
| **FLORA** (flora.ai, ehem. florafauna.ai) | Cloud | proprietär | aktiv; Techniques, Batch, Router, Slack | **Image Node** mit Modellwahl, Run-Knopf mit Preis |
| **Magnific Spaces** (ehem. Freepik Spaces) | Cloud | proprietär | Freepik heisst seit 28.04.2026 Magnific [S2] | **Image Generator**-Knoten mit Modellwahl |
| **Runway Workflows** | Cloud | proprietär | seit Okt. 2025; „Publish as App“ seit Dez. 2025 [S2] | Media-Model-Knoten, Run je Knoten + Run all |
| **Scenario Workflows** | Cloud | proprietär | 2.0 (10.02.2026) Knoten-Workflows; Apps; Node Agent | Generator-Knoten, Einstellungen im Seitenpanel |
| **Figma Weave** (ehem. Weavy) | Cloud | proprietär | Weavy im Okt. 2025 von Figma gekauft | Modellknoten + Editierknoten, App Mode/„Tools“ |
| **Adobe Firefly Graph** | Cloud (Enterprise) | proprietär | angekündigt 17.06.2026 | 300+ Knoten, Firefly + Partner-Modelle |
| **ImagineArt Workflows** | Cloud | proprietär | aktiv | typsichere Knoten, Sections/Pages |
| **Leonardo Blueprints** | Cloud | proprietär | fertige Workflows; Selbstbau „Coming Soon“ | Knoten nur intern (per API sichtbar) |
| **Higgsfield Canvas** | Cloud | proprietär | aktiv | jedes Modell ein Knoten, Parallelvergleich |
| **Kaiber Superstudio** | Cloud | proprietär | aktiv | „Flows“ auf unendlicher Leinwand |
| **fal.ai Workflows** | Cloud/API | proprietär | aktiv | JSON-Graph Input → Modellknoten → Output, Event-Stream |
| **Glif** | Cloud | proprietär | **Builder abgeschafft** 24.03.2026 → nur noch Agent [B] | — |
| **Visual Electric** | Cloud | — | **eingestellt** (Team zu Perplexity, Okt. 2025) [B] | — |
| **Replicate** | API | — | von Cloudflare übernommen (Nov. 2025) [B]; kein eigener Knoten-Editor gefunden | — |
| **chaiNNer** | lokal | **GPL-3.0** [B] | aktiv | Bildverarbeitung/Upscaling, keine Diffusion im Kern |
| **NodeTool** | lokal + Cloud (Alpha) | **AGPL-3.0** [B] | aktiv, „agent-first“ | Anbieter-Knoten (fal, Replicate, lokal) |
| **Node Banana** | lokal, BYOK | **MIT** [B] | aktiv | Anbieter-Knoten (Gemini, fal, Replicate …) |
| **ComfyDeploy** | Cloud für ComfyUI | Repo **AGPL-3.0** [B] | aktiv | ComfyUI-Graph → App/API |
| **RunComfy / ViewComfy** | Cloud für ComfyUI | RunComfy proprietär; ViewComfy Open Source (Lizenz nicht geprüft) | aktiv | ComfyUI-Graph → Serverless-API / Web-App |

---

## 2 · Die Werkzeuge im Einzelnen

### 2.1 ComfyUI (inkl. neuem Frontend)

Quellen: [Interface Overview](https://docs.comfy.org/interface/overview), [Nodes](https://docs.comfy.org/basic-concepts/nodes), [Links](https://docs.comfy.org/basic-concepts/links), [Appearance](https://docs.comfy.org/interface/appearance), [KSampler](https://docs.comfy.org/built-in-nodes/sampling/ksampler), [ControlNet](https://docs.comfy.org/tutorials/controlnet/controlnet), [Subgraph](https://docs.comfy.org/interface/features/subgraph), [Partial Execution](https://docs.comfy.org/interface/features/partial-execution), [App Mode](https://docs.comfy.org/interface/app-mode), [Blog App Mode/ComfyHub](https://blog.comfy.org/p/from-workflow-to-app-introducing), [Comfy Settings](https://docs.comfy.org/interface/settings/comfy), [Server-Nachrichten](https://docs.comfy.org/development/comfyui-server/comms_messages), [Templates](https://docs.comfy.org/interface/features/template), [Nodes 2.0](https://docs.comfy.org/interface/nodes-2), [Frontend-Update 0.3.51](https://blog.comfy.org/p/comfyui-035-frontend-updates), [PR #13615](https://github.com/Comfy-Org/ComfyUI_frontend/pull/13615), [Credits](https://docs.comfy.org/interface/credits), [Caching (DeepWiki)](https://deepwiki.com/comfyanonymous/ComfyUI/2.4-caching-system)

**Oberfläche [B]**
- Linke Seitenleiste: **Assets** (erzeugte Bilder/Videos), **Nodes** (Knotenbibliothek, Kern + Custom), **Models** (Modellbibliothek aus `ComfyUI/models`), **Workflows**, **Templates**. Queue/Job-Verlauf als eigene Seitenleiste.
- Oben rechts: **Run- und Queue-Steuerung**. Rechts ein **Seitenpanel** für Knoteneigenschaften, mit einem **„Issues“-Tab**, der blockierende Fehler und fehlende Ressourcen (Knoten, Modelle, Medien) auflistet.
- Unten rechts: Pan/Select, **Minimap**, Verbindungen ein/aus. Tab-Vorschau, Shortcut-Panel, Help Center.
- **Nodes 2.0**: Umstieg von LiteGraph-Canvas auf Vue-Komponenten; „dynamic widgets, expandable nodes“; rein Frontend, API unverändert.

**Knoten und der „Render“-Kern [B]**
- Generierung ist **in viele Knoten zerlegt**. Der zentrale Knoten ist **KSampler**: Eingänge `model` (MODEL), `positive`/`negative` (CONDITIONING), `latent_image` (LATENT); Widgets `seed` (mit **`control_after_generate`**), `steps` (Std. 20), `cfg` (Std. 8.0), `sampler_name`, `scheduler`, `denoise` (0–1, Std. 1.0). Ausgang `samples` (LATENT).
- **ControlNet**: eigener `Load ControlNet Model` + **`Apply ControlNet`** mit `strength`, `start_percent`, `end_percent`, optional `vae`. Mehrere ControlNets werden **verkettet**. Vorverarbeiter (Tiefe, Canny, Lineart) sind nicht im Kern, sondern in Custom-Paketen (ComfyUI ControlNet aux).
- **Einstellung „Widget Control Timing“**: Seed-Änderung *vor* oder *nach* dem Lauf.
- **Batch Count** (Zahl neben Run): wie oft der Graph in die Queue geht; Obergrenze per Setting (Std. 100). Run-Modi im Dropdown: *Run*, *Run (On Change)*, *Run (Instant)* [S2: [nomadoor](https://comfyui.nomadoor.net/en/begin-with/run-and-stop/)].
- **Knotenmodi**: *Always*, *Never*, *Bypass* (Bypass = Daten werden durchgereicht, Knoten nicht ausgeführt).
- **Knotenzustände**: normal, running, **error** (rote Markierung am fehlerhaften Eingang), **missing** (Kern- oder Custom-Knoten fehlt).
- **Badges**: *Node ID*, *Node Source* (Fuchs-Icon = Kern, sonst Paketname), **Pricing Badge** auf Partner-/API-Knoten (ungefähre Kosten oben rechts; Preisregeln werden clientseitig aus aktuellen Widget-Werten berechnet).

**Typsystem [B]** — jede Datenart hat eine Farbe; Ports und Kabel teilen die Farbe; „You can only connect ports of the same color.“ Auszug: MODEL #B39DDB (lavendel), CLIP #FFD500, VAE #FF6E6E, CONDITIONING #FFA931, LATENT #FF9CF9, IMAGE #64B5F6, MASK #81C784, CONTROL_NET #6EE7B7. Bypass-Hintergrund #FF00FF, Fehlerfarbe #E00. Kabelstil wählbar (Kurve, rechtwinklig, gerade, versteckt), **Reroute**-Punkte.

**Graph-Struktur [B]**
- **Subgraph** (ab Frontend 1.24.3): Auswahl → ein Knoten mit eigenen Ein-/Ausgängen; verschachtelbar, Brotkrumen-Navigation, **Unpack** zurück. Parameter lassen sich im Parameterpanel bearbeiten, ohne hineinzugehen; Widgets umsortieren und per Auge-Symbol ein-/ausblenden.
- **Subgraph Blueprints** (ab 1.27.7): Subgraph in die Knotenbibliothek veröffentlichen; jede Instanz ist unabhängig editierbar.
- **Templates**: Vorlagenbrowser; Vorlagen tragen **eingebettete Modell-Links** (`properties.models`: Name, URL, Zielordner) und prüfen beim Laden, ob Modelle fehlen → Download-Angebot. Nur `.safetensors`/`.sft`, nur Hugging Face/Civitai.
- Gruppen (farbige Rahmen) existieren; [S] nicht separat nachgeschlagen.

**Ausführung, Caching, Fortschritt [B]**
- **Nur Geändertes läuft**: Modus *Always* führt einen Knoten aus, „whenever it runs for the first time or when any of its inputs change since the last execution“. Ausgabecache nach **Eingangssignatur**; Strategien Classic/LRU/RAM-Pressure/None; `IS_CHANGED` erlaubt Invalidierung durch externe Zustände.
- Server meldet per WebSocket: `execution_cached` (Liste übersprungener Knoten), `executing` (welcher Knoten jetzt), **`progress` (`node`, `value`, `max`)** — also Fortschritt **pro Knoten** —, `executed` (UI-Ausgabe eines Knotens), `execution_error`, `status` (Queue-Länge).
- **Partial Execution**: in der Selection-Toolbox ein blaues Dreieck, nur wenn ein **Ausgabeknoten** gewählt ist → nur dieser Zweig läuft.
- **Teilerfolg** (PR #13615, Draft/WIP): unabhängige Zweige laufen nach einem Fehler weiter; **„failed“ und „dependency-blocked“** werden unterschiedlich dargestellt; Teilerfolge erscheinen im Job-Verlauf.

**Vereinfachte Sicht [B]** — **App Mode / App Builder** (offiziell ab Frontend 1.41.13, Blog 10.03.2026): Graph verschwindet; Eingaben rechts, Ausgabe links; Builder in 4 Schritten: *Eingangsknoten wählen → Ausgangsknoten wählen → Vorschau → Standardansicht (App oder Graph)*. Eingaben umbenennen, sortieren, gruppieren; Rest „hidden and locked“. Während des Laufs „Cancel this run“. Teilen per URL (Comfy Cloud), **ComfyHub** als öffentliche Ablage.

**Kosten [B]** — Partner-Knoten (geschlossene Modelle) über Credits; lokale Nutzung bleibt frei.

**Lizenz [B]** — `Comfy-Org/ComfyUI` und `Comfy-Org/ComfyUI_frontend`: **GPL-3.0** (LICENSE-Datei geprüft). → **GPL-Fund, siehe Abschnitt 5.**

---

### 2.2 Krea Nodes

Quellen: [Krea-Doku Nodes (Markdown)](https://www.krea.ai/docs/user-guide/features/nodes), [Feature-Seite](https://www.krea.ai/features/nodes), [Node Agent](https://www.krea.ai/blog/ai-workflow-agent)

- **Knoten-Anatomie [B]**: *Inputs* links („connected to other nodes' outputs **or filled in manually**“), *Parameters* im Knoten (Stärke, Auflösung, Prompt), *Outputs* rechts. Griffe **farbcodiert nach Datentyp**; Ziehen vom Griff zeigt passende Knoten; max. 10 ausgehende Verbindungen je Knoten.
- **Kategorien [B]**: Generate Image, Generate Video, Edit Image, Enhance Image, Enhance Video, Generate 3D, Motion Transfer, Lipsync, Audio, Utility (Text: LLM Call, Line Splitter, Concat, Sticky Note, Text Overlay; Bild: Blur, Invert, Brightness/Contrast, **Compositor**, Hue/Sat, RGB, Remove Background, Crop, **Image Mask Editor**; Video: Frame holen, Trim, Speed, Stitch …).
- **Generate-Knoten [B]**: ein Knoten, **Modellwahl** darin; die Doku listet pro Modell Fähigkeiten (*Supports Styles*, *Image Prompt*, *Max Image Refs* 1–15). [S] Die Eingänge des Knotens hängen also vom gewählten Modell ab.
- **Vergleich [B]**: „Run all the best models in parallel and compare the results.“
- **Organisation [B]**: Section-Knoten, Gruppen (Auswahl → Group; Knoten hinein-/herausziehen), Sticky Notes.
- **Node App Builder [B]**: Workflow → Eingänge/Ausgänge markieren (Text, Bild-Upload, Dropdown, Slider, Zahl mit min/max, Boolean) → Labels, Reihenfolge, **Defaults**, Pflicht/optional → öffentlich/privat/API („Execute a Node App“). Empfehlung der Doku: **5–7 Felder**, sprechende Labels („How intense should the style transfer be?“ statt „strength“), Profi-Optionen hinter „Advanced“.
- **Node Agent [B]**: baut aus einem Satz einen Graphen, **prüft vorher den ganzen Graphen** (fehlende Parameter, falsche Typen → Konvertierungsknoten), zeigt **Kosten pro Knoten**, „Nothing runs until you say go“. **Nur betroffene (nachgelagerte) Knoten laufen neu**; gecachte Ausgaben werden wiederverwendet; „Clear cache if needed“.
- **Lizenz**: proprietär.

---

### 2.3 FLORA (flora.ai)

Quellen: [Doku-Index](https://docs.flora.ai/llms.txt), [Canvas](https://docs.flora.ai/editor/canvas), [Toolbar](https://docs.flora.ai/editor/toolbar), [Model Pricing](https://docs.flora.ai/plans-and-billing/model-pricing), [Technique Builder](https://docs.flora.ai/nodes/technique-builder), [Router Node](https://docs.flora.ai/nodes/router-node), [Batch Node](https://docs.flora.ai/nodes/batch-node), [Image to Image](https://docs.flora.ai/nodes/image-node/image-to-image)

- **Knoten [B]**: Text, Image, Video, Audio, **3D** (erzeugen/importieren, „stage and capture“), Document (PDF), **Layer Editor** (Kompositing bis 4096×4096), **Action Node** (klassische Bearbeitung ohne KI: Farbkorrektur, Trim, Frame), **Custom Actions** (Werkzeug per Beschreibung erzeugen), **Batch Node**, Export (Download/Google Drive/Shopify), **Router** (Durchreiche-Knoten „one-to-many“), Group, Comment, Technique.
- **Bildknoten [B]**: Modellwahl im Knoten (Standard früher Flux Dev); Parameter u.a. *Prompt*, *Style* (Voreinstellungen), *Strength* 0–100 % (Bild vs. Text), *Image Size*, **Seed** („all parameters must be the same in order for a given seed's output to persist“); **Prompt-Verbesserer**-Knopf.
- **Kosten [B]**: Jedes Modell zeigt im Picker einen **Kostenmesser aus Blumen** (1–3, „+“ ab 2 $); optional exakte Dollar: „The **Run** button on each node shows the exact dollar amount for the run, accounting for batch count“. Preis dynamisch nach Parametern; **fehlgeschlagene Läufe kosten nichts**.
- **Verlauf [B]**: Knoten haben eine **Generierungshistorie** (Download All als ZIP); nachgelagerte Editoren lesen die **„current active output“** (normalerweise die neueste). Globaler „Generation History“-Knopf.
- **Batch [B]**: Batch Node; bei zwei Batch-Eingängen **Cross** (N×M) oder **Zip** (paarweise); Generate-Knopf zeigt die Zahl live; Matrix-Ansicht.
- **Bulk Parameters Panel [B]**: ≥2 gleichartige Knoten wählen → rechte Seitenleiste zeigt **nur gemeinsame Parameter**, abweichende Werte als **„Mixed“**, Modellwechsel für alle — gedacht für Vergleichs- und Batch-Aufbauten (Seed, Guidance, Seitenverhältnis).
- **Weiteres [B]**: Farb-Tags für Knoten; verbundene Eingänge per Ziehen **umsortieren**; noch laufende Knoten dürfen verbunden werden („validates readiness at generation time, not at connection time“); Kommentare; Echtzeit-Zusammenarbeit.
- **Technique Builder [B]**: Leinwand wird beim Bauen **gesperrt**; 4 Schritte *Intro → Input → Output → Publish*; Eingänge = Knoten ohne eingehende Verbindung, Ausgänge = Knoten ohne ausgehende; je Eingang *Name*, *Beschreibung (max. 40 Zeichen)*, **Preset** (aktueller Inhalt wird Beispiel-/Standardwert). Ergebnis: **ein Knoten** auf jeder Leinwand *oder* eine App.
- **Lizenz**: proprietär.

---

### 2.4 Magnific Spaces (ehemals Freepik Spaces)

Quellen: [Freepik Docs (Suchauszug)](https://www.freepik.com/ai/docs/introduction-to-spaces), [Magnific Spaces](https://www.magnific.com/spaces), [kingy.ai-Test](https://kingy.ai/news/freepik-spaces-freepik-lists-review-the-bulk-creative-production-tool-agencies-have-been-waiting-for/) [S2], [Rebrand (TNW)](https://thenextweb.com/news/freepik-rebrands-as-magnific), [Wireflow zum Rebrand](https://www.wireflow.ai/blog/freepik-spaces-is-now-magnific) [S2], [Krea-Vergleich](https://www.krea.ai/blog/freepik-spaces-vs-krea-nodes)

- Start 04.11.2025; seit **28.04.2026 heisst Freepik „Magnific“**, Spaces läuft weiter [S2].
- **Knoten [S2]**: Upload, Text (Prompt/Notiz), Assistant (LLM), **Image Generator** (Modell-Dropdown: Flux, Imagen, Nano Banana, GPT Image, Ideogram, Mystic, Runway, Seedream …), Video Generator, **Image Upscaler** (Magnific, Modi *Creative*/*Precision*), **List Node** (Batch: „1 Figur × 5 Headlines × 4 CTAs = 20 Anzeigen“), **Designer Node** (vollständiger Layout-Editor im Graph) [B, Doku-Titel].
- **Lauf [S2]**: Run am Knoten oder Run in der Toolbar (ganze Kette). **Credits beim Überfahren** des Knotens bzw. im „Spotlight“-Tooltip (z.B. 75 Credits je Bild für ein Modell).
- **Workflow App [B, Suchauszug Doku]**: gespeicherter Workflow wird „a single, reusable block with its own inputs and outputs“.
- **Zusammenarbeit [B]**: Echtzeit, farbige Cursor, Kommentare.
- Magnific-Upscaler-Parameter (API): *creativity*, *hdr*, *resemblance*, *fractality* je −10…10, Standard 0; *engine* „automatic“ [S2, [Magnific API](https://docs.magnific.com/api-reference/image-upscaler-creative/post-image-upscaler)].
- **Lizenz**: proprietär.

---

### 2.5 InvokeAI (Workflow Editor, Linear UI)

Quellen: [Editor Interface](https://invoke.ai/features/workflows/editor-interface/), [Front-end Workflows (Entwicklerdoku)](https://invoke.ai/development/front-end/workflows/), [Nodes & Workflows](https://invoke.ai/concepts/nodes-workflows/), [Adobe/Invoke (pixelsham)](https://www.pixelsham.com/2025/10/20/adobe-buys-invokeai-and-launches-adobe-ai-foundry/) [S2], [Review 2026](https://www.promptquorum.com/power-local-llm/invokeai-review) [S2]

- **Zwei Wege zum selben Graphen [B]**: Die **Linear UI** (das normale Generierungsformular) baut intern per Code einen Graphen; der **Workflow Editor** (auf **reactflow**/xyflow, MIT) lässt ihn zeichnen. [S] Das ist genau unser Muster „Kern ist Bibliothek, Oberfläche ist dünne Schicht“.
- **Feldtypen [B]**: Typ bestimmt das UI-Element; Kardinalität *SINGLE*, *COLLECTION*, *SINGLE_OR_COLLECTION*; **stateful** Felder (Werte im Frontend, direkt eingebbar) vs. **stateless** (nur per Verbindung, z.B. UNet). Ports farbcodiert.
- **„Use Cache“ im Knotenfuss [B]**: pro Knoten abschaltbar.
- **Linear View → Form Builder [B]**: Eingang per Rechtsklick „Add to Linear View“; ab 5.8 **Form Builder** mit Containern, Trennern, Überschriften, Text. Workflow-Bibliothek mit Vorlagen. Batch über `RandomRange` (Size = Anzahl Bilder).
- **Lage [S2]**: kommerzieller Dienst am 31.10.2025 eingestellt, Teile des Teams zu Adobe; Open-Source-Projekt läuft weiter (6.12 Multi-User, 6.13 Mai 2026).
- **Lizenz [B]**: **Apache-2.0** (LICENSE geprüft).

---

### 2.6 Griptape Nodes

Quellen: [Repo-README](https://github.com/griptape-ai/griptape-nodes), [Running Workflows](https://docs.griptapenodes.com/en/stable/guides/editor/running_workflows/), [Working with Nodes](https://docs.griptapenodes.com/en/stable/guides/editor/working_with_nodes/), [Node Groups](https://docs.griptapenodes.com/en/stable/guides/editor/node_groups/), [Doku-Index](https://docs.griptapenodes.com/llms.txt), [Foundry-Übernahme (CG Channel)](https://www.cgchannel.com/2026/02/foundry-acquires-ai-tools-firm-griptape/)

- **Architektur [B]**: lokale **Engine** (PyPI `griptape-nodes-engine`) + Cloud-Editor oder Desktop-App; **Workflows werden als ausführbare Python-Dateien gespeichert**; skriptbar („retained mode“); MCP-Anbindung (u.a. Blender-, Maya-Server gelistet).
- **Knoten-Anatomie [B]**: Parameter erscheinen **inline am Knoten *und* im Properties-Panel** — „update the same underlying value“. Jede Parameterzeile hat links/rechts einen Griff; beim Ziehen werden **inkompatible Griffe abgedunkelt**. **„Hide Connected Parameters“ (Shift+H)** blendet angeschlossene Zeilen aus. Kopf mit Schloss-Symbol.
- **Ausführung [B]**: *Run Workflow*; **Run To Selected** (Knoten + alles Vorgelagerte, das noch nicht aufgelöst ist); **Run From Selected** (ab hier vorwärts). Run To Selected geht auch während eines Laufs.
- **Zustandspillen [B]**: **Running** orange drehend · **Resolved** grün · **Error** rot (Hover zeigt Meldung, bleibt nach Lauf stehen) · **Unresolved** blau. *Cancel Run*, Execution Log mit Stufen, **Error History** über die Sitzung. Entwicklermodus: „Mark as unresolved“ erzwingt Neuberechnung samt nachgelagerten Knoten.
- **Kontrollfluss vs. Daten [B]**: getrennte Verbindungsarten.
- **Gruppen [B]**: *Basic Group* (nur optisch), **Subflow** (führt Inhalt gemeinsam aus), **ForEach**, **For Loop**, **Retry** (Wiederholung bei Fehler); Verbindungen über die Gruppengrenze laufen über **„wall parameters“** am Gruppenknoten.
- **Lizenz [B]**: Engine **Apache-2.0** (LICENSE geprüft). [S] Der Editor ist ein Cloud-Dienst mit Griptape-Konto; nicht Teil des Repos.

---

### 2.7 Runway Workflows

Quellen: [Help: Introduction](https://help.runwayml.com/hc/en-us/articles/45763528999699-Introduction-to-Workflows), [Help: Building](https://help.runwayml.com/hc/en-us/articles/45769159004691-Building-your-first-Workflows), [Help: Publishing as Apps](https://help.runwayml.com/hc/en-us/articles/47865876793747-Publishing-Workflows-as-Apps) — alle nur als Suchauszug (403); [VP Land](https://www.vp-land.com/p/runway-launches-node-based-workflows) [S2]

- **Knoten [B, Auszug]**: Input-Knoten (Text/Medien), **Media-Model-Knoten** (Bild/Video), **LLM-Knoten** (Prompt-Verfeinerung). Nur kompatible Typen verbindbar.
- **Lauf [B, Auszug]**: **Run all** (oben rechts) und **Run** am einzelnen Knoten („testing, troubleshooting, or regenerating one part … without rerunning everything“). Media- und LLM-Knoten verbrauchen Credits.
- **Node Execution History [B, Auszug]**: mehrere Ausgaben je Knoten „review, compare, and restore previous outputs without having to re-run“.
- **Publish as App [B, Auszug]** (04.12.2025): Labels für Ein-/Ausgänge, **Auge-Symbol** blendet Felder in der App ein/aus, Kerneinstellungen bleiben gesperrt.
- Lizenz: proprietär.

---

### 2.8 Scenario Workflows

Quellen: [Introduction to Workflows](https://help.scenario.com/articles/1669206426-introduction-to-workflows), [Building Pipelines](https://help.scenario.com/articles/7094354401-building-workflows-in-scenario), [Blog](https://www.scenario.com/blog/scenario-workflows-one-canvas-end-to-end), [Changelog 2.0](https://www.scenario.com/changelog/2-0-introducing-node-based-workflows)

- **Kategorien [B]**: Input, Generators, Composers, Utilities (Prompt Builder, Group Assets, **if-else**).
- **Knoten [B]**: „inputs on the left, outputs on the right, and **detailed settings in the side panel**“; Titelzeile, Griffe, **Vorschaubereich**.
- **Drei Laufumfänge [B]**: **Single Node** (Play-Knopf am Knoten), **Partial Run** (Knoten + alles Nachgelagerte), **Full Workflow** (Run oben rechts).
- **Kosten [B]**: „Preview CU cost in the generator before running“.
- **Sperren [B]**: „Locked groups can still be run but cannot be modified.“ (Workflow Locking seit v2.1.0).
- **Apps [B]**: `scenario.com/apps/[name]`, nur markierte Eingänge sichtbar; Plattform-Workflows als Vorlagen; JSON-Export/-Import; Node Agent.
- Lizenz: proprietär.

---

### 2.9 Figma Weave (ehemals Weavy)

Quellen: [Figma-Blog](https://www.figma.com/blog/welcome-weavy-to-figma/), [Weave-Help (Suchauszug)](https://help.weavy.ai/en/articles/12267755-the-design-app), [creativeainews](https://www.creativeainews.com/articles/figma-weave-node-graph-ai-design-analysis/) [S2]

- Kauf durch Figma Okt. 2025 [B]. Modellknoten (Flux, Ideogram, Nano Banana, Seedream, Veo, Sora …) **plus professionelle Bearbeitung im Graph** („adjusting lighting, masking an object, color grading“) [B].
- **Comparison-Knoten** für Seite-an-Seite-Vergleich [S2].
- **Tools (früher Design Apps) / App Mode [B, Auszug]**: Output-Knoten ans Ende → einfache Bedienansicht; Geteilte sehen nur den Tool-Modus, Ersteller immer den Editor.
- Lizenz: proprietär.

---

### 2.10 Adobe Firefly Graph (und Boards)

Quellen: [Computerworld](https://www.computerworld.com/article/4186410/adobe-new-firefly-graph-can-turn-creative-workflows-into-reusable-assets.html), [Adobe Business](https://business.adobe.com/products/creativecloud-business/firefly-graph.html) (Suchauszug), HelpX-Seiten (403)

- Angekündigt **17.06.2026**; **300+ Knotentypen** (Bild, Video, Generierung; Firefly + Google + OpenAI) [B].
- Workflows werden „shared across an organization as repeatable processes“ — Ausführung ohne Prompt-Kenntnis; eigene **Input-/Output-Knoten im Workflow Builder** [B, Suchauszug].
- **Firefly Boards** ist ein Moodboard/Leinwand, **kein** Knotengraph [B, Suchauszug].
- Enterprise sofort, Teams als Public Beta [B]. Lizenz proprietär.

---

### 2.11 Weitere Cloud-Leinwände

| Werkzeug | Belegte Kernpunkte | Quelle |
|---|---|---|
| **ImagineArt Workflows** („Imagine Flow“) | Daten fliessen links→rechts; **typsichere Verbindungen** (Bild→Bild, Text→Text); Sections, Pages, Ordner; „run the whole sequence in one click“ | [Intro](https://docs.imagine.art/workflows/Intro-to-workflows) |
| **Leonardo Blueprints** | Fertige Workflows, intern „each step is a node“; Eingaben per `nodeId` + `settingName`; **Kosten je Blueprint-Version vor Ausführung abfragbar**; Selbstbau „Coming Soon“ | [API-Guide](https://docs.leonardo.ai/docs/blueprints-guide) |
| **Higgsfield Canvas** | jedes Modell ein Knoten; **Modelle parallel laufen lassen und vergleichen**; Workflow als Vorlage; **Credits nur, wenn ein Knoten tatsächlich generiert** | [Canvas](https://higgsfield.ai/canvas-intro) [S2-Suchauszug] |
| **Kaiber Superstudio** | Leinwand „with node logic“; jede Generierung ist ein Knoten; „Flows“ = modulare Werkzeuge (Restyle, Upscale, Lip Sync, Model Maker) | [Help Center](https://helpcenter.kaiber.ai/en/articles/10000812-introduction-to-superstudio-s-canvas) (Auszug) |
| **fal.ai Workflows** | JSON-Graph *Input → Modellknoten → Output* als **ein Endpunkt**; Events **Submit / Completion (mit Zwischenergebnis) / Output / Error** | [Doku](https://fal.ai/docs/documentation/model-apis/workflows) |
| **Wireflow** | Cloud-Knoteneditor + REST-API (Webhooks, idempotente Ausführung) — Herstellerangabe | [Wireflow](https://www.wireflow.ai/features/visual-node-editor) |
| **RhinoFrame** | **Architektur-spezifisch**: Plugin für Rhino 8, Grasshopper-artige Knoten für KI-Rendering aus dem Viewport, Beta | [howtorhino](https://howtorhino.com/blog/architecture-technology/best-ai-tools-for-architects/) [S2] |
| **Glif** | Knoten-Builder am **24.03.2026 abgeschafft**, ersetzt durch einen Chat-Agenten mit 100+ Werkzeugen | [Glif-Doku](https://docs.glif.app/llms-full.txt) |
| **Visual Electric** | Oktober 2025 Team zu Perplexity, Produkt nach 90 Tagen eingestellt | [TechCrunch](https://techcrunch.com/2025/10/02/perplexity-acquires-the-team-behind-sequioa-backed-ai-design-startup-visual-electric/) |
| **Replicate** | Cloudflare-Übernahme angekündigt 17.11.2025; Modell-API, **kein** Knoteneditor gefunden; dient anderen Editoren als Anbieter | [Cloudflare](https://blog.cloudflare.com/replicate-joins-cloudflare/) |

### 2.12 Lokale / quelloffene Editoren neben ComfyUI

| Werkzeug | Belegte Kernpunkte | Lizenz |
|---|---|---|
| **chaiNNer** | Bildverarbeitung/Upscaling (PyTorch, NCNN, ONNX, TensorRT); Griffe **farbcodiert**, beim Verbinden **nur kompatible** sichtbar; Kabel vom Leeren ziehen → Liste passender Knoten; grüner Run, gelber Pause, roter Stop; **Kabel animieren während der Verarbeitung**; Ordner-/Video-Iteration. [README](https://github.com/chaiNNer-org/chaiNNer) | **GPL-3.0** [B] |
| **NodeTool** | „Agent-first“; lokale Modelle + eigene API-Schlüssel (fal, Replicate …); „**rerun only what changed**“; Storyboard/Timeline; Studio, CLI, MCP. [README](https://github.com/nodetool-ai/nodetool) | **AGPL-3.0** [B] |
| **Node Banana** | Next.js-Editor, **typisierte Griffe**, Ausführung in Abhängigkeitsreihenfolge, **Group Locking** (gesperrte Gruppen werden beim Lauf übersprungen), Prompt→Workflow, Workflows als JSON. [README](https://github.com/shrimbly/node-banana) | **MIT** [B] |
| **ComfyDeploy** | ComfyUI für Teams: Eingänge per Custom-Knoten exponieren, Playground, Links, API. [Doku](https://docs.comfydeploy.com/) | Repo `BennyKok/comfyui-deploy`: **AGPL-3.0** [B] |
| **RunComfy** | gehostetes ComfyUI; Workflow-Link teilt Umgebung inkl. Modelle/Custom-Knoten; Serverless-API. [RunComfy](https://www.runcomfy.com/) | proprietär |
| **ViewComfy** | Web-Apps aus ComfyUI-Workflows. [Repo](https://github.com/ViewComfy/ViewComfy) | Open Source, Lizenz **nicht geprüft** |

---

## 3 · Wiederkehrende Muster über alle Werkzeuge

1. **Zwei Lager beim Generierungsknoten.** [B/S]
   *Zerlegt* (ComfyUI, InvokeAI): Modell laden, Text kodieren, sampeln, dekodieren — jeder Schritt ein Knoten, maximale Kontrolle, hohe Einstiegshürde.
   *Gebündelt* (Krea, FLORA, Magnific, Runway, Scenario, Weave, Higgsfield, ImagineArt): **ein** Generate-Knoten mit Modellwahl, Prompt, Referenzen, Grösse, Seed. [S] Alle Cloud-Werkzeuge seit 2025 gehen den gebündelten Weg; ComfyUI kompensiert mit Subgraphs/Blueprints/App Mode.
2. **Die Leinwand zerfällt in zwei Zielgruppen.** Jedes aktive Werkzeug hat 2025/26 einen **„App“-Modus** eingeführt: ComfyUI App Mode, Krea App Builder, FLORA Technique Builder, Runway Publish as App, Scenario Apps, Weave Tools, Magnific Workflow App, Invoke Form Builder, Firefly Graph, Leonardo Blueprints. Muster: *Eingänge markieren → Ausgänge markieren → umbenennen/ordnen/Defaults → Rest gesperrt → Link teilen.* [B]
3. **Laufen in Teilen.** Einzelknoten, „bis hier“, „ab hier“, alles (Griptape, Scenario, Runway, ComfyUI Partial Execution). [B]
4. **Caching nach Eingangsgleichheit** und nur nachgelagertes Neurechnen (ComfyUI, Krea, Griptape, NodeTool), mit **Schalter zum Erzwingen** (Invoke „Use Cache“, Griptape „Mark as unresolved“, Krea „Clear cache“). [B]
5. **Kosten vor dem Lauf, am Knoten.** Run-Knopf mit Preis (FLORA), Hover-Credits (Magnific), Pricing-Badge (ComfyUI), Kosten pro Knoten (Krea Agent), CU-Vorschau (Scenario); **fehlgeschlagene Läufe kosten nichts** (FLORA). [B]
6. **Verlauf im Knoten statt nur global.** Runway Node Execution History, FLORA Generierungshistorie + „aktive Ausgabe“. [B]
7. **Vergleich als Knoten oder Modus.** Comparison-Knoten (Weave), parallele Modelle (Krea, Higgsfield), Bulk-Panel mit „Mixed“ (FLORA), Batch Cross/Zip (FLORA), List (Magnific). [B]
8. **Farbige, typisierte Ports** sind Standard; Unterschiede nur in der Hilfe beim Verbinden (dimmen, Liste passender Knoten, automatische Konverter). [B]
9. **Agent baut den Graph.** Krea Node Agent, Scenario Node Agent, Comfy Agent (Alpha), Griptape Agent, NodeTool, Node Banana, Runway Agent [S2]. Extremfall **Glif**: Graph ganz abgeschafft. [B] [S] Der Graph wird zur *prüfbaren Darstellung dessen, was ein Agent tut* — nicht mehr nur zum Bauwerkzeug.
10. **Konsolidierung.** Weavy→Figma, Invoke-Team→Adobe, Visual Electric→Perplexity (eingestellt), Replicate→Cloudflare, Griptape→Foundry, Freepik→Magnific. [B/S2] [S] Kleine Cloud-Werkzeuge sind als Abhängigkeit riskant.
11. **Was fehlt überall:** Keine gefundene Lösung prüft das Ergebnis **gegen eine Eingangsgeometrie** (Tiefe, Kanten, Masken) und zeigt dies am Knoten an. Qualitätsanzeige beschränkt sich auf Status (ok/Fehler) und Kosten. [S — Abwesenheitsbefund, nur so gut wie die Suche]

---

## 4 · Muster für den Render-Knoten

Jedes Muster: **was**, **wer** (belegt), **Übertrag auf uns** [S].

| # | Muster | Werkzeuge (belegt) | Übertrag auf unseren Render-Knoten [S] |
|---|---|---|---|
| 1 | **Ein gebündelter Knoten mit Modellwahl im Knoten** statt Loader-Kette | Krea, FLORA, Magnific, Runway, Scenario, Weave, Higgsfield | Ein Render-Knoten; Modell/Gewichte als Auswahlfeld, intern die zerlegte Kette. |
| 2 | **Fähigkeitsabhängige Eingänge** — Referenzanzahl, Stil, Start-/Endbild je nach Modell | Krea (Tabelle *Max Image Refs*, *Supports Styles*), FLORA (Video: Erst-/Letztbild „depending on the model“) | Geometrie-Eingänge (Tiefe, Normalen, Kanten, Maske) nur zeigen, wenn das gewählte Modell/ControlNet sie kann. |
| 3 | **Steuerbild als eigener, stapelbarer Baustein mit Stärke + Zeitfenster** | ComfyUI `Apply ControlNet` (`strength`, `start_percent`, `end_percent`, verkettbar) | Pro Geometriedurchgang eine Zeile *Stärke / von % / bis %* im Render-Knoten; Liste statt fester Slots. |
| 4 | **Jeder Parameter kann Feld *oder* Eingang sein** | Krea („connected … or filled in manually“), Invoke (stateful Felder), Griptape (Griff je Parameterzeile), ComfyUI (Widget→Input) | Prompt, Seed, Stärke als Feld; per Kabel übersteuerbar (z.B. Prompt aus Material-Knoten). |
| 5 | **Angeschlossene Parameter ausblenden / „Advanced“ einklappen** | Griptape (Hide Connected, Shift+H), Krea-Empfehlung (Advanced-Toggle, 5–7 Felder), ComfyUI Subgraph (Auge je Widget) | Standardansicht: Modell, Prompt, Varianten, Run. Sampler/CFG/Schritte hinter „Erweitert“. |
| 6 | **Parameter inline *und* im Seitenpanel, gleicher Wert** | Griptape (explizit), ComfyUI (rechtes Panel), Scenario (Einstellungen im Seitenpanel) | Knoten kompakt; volles Formular rechts. Eine Quelle der Wahrheit im Kern. |
| 7 | **Kosten vor dem Lauf, am Run-Knopf, inkl. Batch** | FLORA (Dollar auf Run, Blumenmesser im Picker), Magnific (Hover), ComfyUI Pricing Badge, Scenario CU-Vorschau, Leonardo (Kosten je Version) | Bei uns lokal: **geschätzte GPU-Zeit** auf dem Run-Knopf (× Varianten). Bei Cloud-Backend: Kosten. |
| 8 | **Kosten pro Knoten und Freigabe vor Start** | Krea Node Agent („Nothing runs until you say go“) | Vor Batch-Läufen: Übersicht „n Bilder × t s“ mit Bestätigen. |
| 9 | **Run am Knoten + Run all** | Runway, Scenario (Play am Knoten), Magnific, ComfyUI (Partial Execution nur für Ausgabeknoten) | Run-Knopf im Render-Knoten selbst, nicht nur global. |
| 10 | **Drei Laufumfänge: nur dieser / bis hier / ab hier** | Scenario (Single/Partial/Full), Griptape (Run To / Run From Selected) | „Nur rendern“ vs. „Geometrie neu + rendern“ vs. „ab Render inkl. Prüfung“. |
| 11 | **Nur Geändertes neu rechnen (Cache nach Eingangssignatur)** | ComfyUI (Eingangssignatur, `execution_cached`), Krea (downstream-only), Griptape (Resolved bleibt), NodeTool | Geometriedurchgänge cachen; Promptänderung darf Tiefe/Normalen nicht neu rechnen. |
| 12 | **Cache sichtbar und abschaltbar / Neuberechnung erzwingen** | Invoke „Use Cache“ im Knotenfuss, Griptape „Mark as unresolved“, Krea „Clear cache“, ComfyUI `IS_CHANGED` | Kleines Cache-Symbol am Knoten („aus Cache“) + „neu erzwingen“. |
| 13 | **Zustandspille mit festen Farben** (läuft / fertig / Fehler / veraltet) | Griptape (orange/grün/rot/blau), ComfyUI (running/error/missing), chaiNNer (animierte Kabel) | Zusätzlich Zustand **„veraltet“** (Eingang geändert, Bild alt) — Griptapes „Unresolved“ ist genau das. |
| 14 | **Fortschritt pro Knoten (Wert/Max)** | ComfyUI WebSocket `progress` (`node`, `value`, `max`); fal Events Submit/Completion | Schrittfortschritt der Diffusion im Knoten; bei Varianten „2 von 4“. |
| 15 | **Fehler am Knoten *und* zentrale Fehlerliste** | ComfyUI (roter Eingang + Issues-Tab inkl. fehlender Modelle), Griptape (Hover auf roter Pille + Error History) | Fehlende Gewichte/ControlNets schon *vor* dem Lauf als Issue melden, nicht erst beim Absturz. |
| 16 | **„Fehlgeschlagen“ ≠ „blockiert durch Vorgänger“** | ComfyUI PR #13615 (Draft) | Prüfknoten zeigt „blockiert“, wenn der Render scheiterte — nicht „durchgefallen“. |
| 17 | **Seed mit Nachlauf-Regel** (fest / +1 / zufällig; vor/nach dem Lauf) | ComfyUI `control_after_generate` + „Widget Control Timing“; FLORA Seed-Reproduzierbarkeit | Seed-Feld mit Schloss (fest) und Würfel; Seed jeder Variante im Ergebnis speichern. |
| 18 | **Varianten/Batch als Parameter oder Knoten; Kombinatorik Cross/Zip** | ComfyUI Batch Count, FLORA Batch Node (Cross N×M / Zip), Magnific List Node, Griptape ForEach, Invoke RandomRange | „Varianten: n“ im Knoten; für Kamera × Stil-Matrizen eigener Listen-/Matrix-Knoten. |
| 19 | **Verlauf im Knoten: vergleichen, zurückholen, „aktive Ausgabe“** | Runway Node Execution History, FLORA Generierungshistorie + active output | Filmstreifen der letzten Läufe unter der Vorschau; eine davon ist „aktiv“ und fliesst weiter. |
| 20 | **Vergleich eingebaut** (Parallel-Modelle, Vergleichsknoten, Bulk-Edit mit „Mixed“) | Weave Comparison-Knoten, Krea/Higgsfield Parallelmodelle, FLORA Bulk Parameters Panel | Vorher/Nachher-Schieber gegen den Geometriedurchgang; mehrere Render-Knoten gleichzeitig editieren. |
| 21 | **Typisierte, farbige Ports; inkompatible dimmen; vom Port aus passende Knoten vorschlagen** | ComfyUI (Farbtabelle), Griptape (dimmen), chaiNNer/Krea (Liste passender Knoten), ImagineArt/Runway (nur kompatible) | Eigene Typen: *Tiefe*, *Normalen*, *Kanten*, *Maske*, *Kamera*, *Bild*, *Prüfbericht* — je Farbe. |
| 22 | **Kapselung: Teilgraph → wiederverwendbarer Knoten** | ComfyUI Subgraph → Blueprint, FLORA Technique (als Knoten), Magnific Workflow App, Griptape Subflow mit „wall parameters“ | Der Render-Knoten *ist* ein Blueprint über der Kette; „Aufklappen“ zeigt die zerlegte Kette für Fachleute. |
| 23 | **App-Modus: Ein-/Ausgänge markieren, umbenennen, Defaults/Presets, Rest gesperrt** | ComfyUI App Builder (4 Schritte), Krea App Builder, FLORA Technique Builder (Preset = aktueller Inhalt), Runway (Auge-Symbol), Scenario, Weave, Invoke Form Builder | Die iPad-/Stift-Oberfläche ist genau so ein App-Modus über denselben Graphen. |
| 24 | **Sperren: ausführbar, aber nicht änderbar** | Scenario (locked groups), Node Banana (Group Locking = überspringen), FLORA (Leinwand gesperrt im Builder) | Geprüfte Render-Einstellungen sperren, damit Varianten nur Prompt/Seed ändern. |
| 25 | **Modellabhängigkeiten im Workflow mitführen und beim Laden prüfen** | ComfyUI Templates (`properties.models` mit URL/Ordner, Download-Hinweis, nur safetensors) | Render-Knoten trägt Gewichts-ID + Lizenz; Laden prüft Vorhandensein **und Lizenz** (Regel 1: keine NC-Gewichte). |
| 26 | **Herkunfts-/ID-Badge am Knoten** | ComfyUI Node Source Badge (Fuchs = Kern) und Node ID Badge | Badge mit Modellname + Lizenzkürzel am Render-Knoten. |
| 27 | **Validierung vor dem Lauf; Verbinden auch mit noch laufenden Knoten** | Krea Agent (ganzer Graph geprüft, Konverter eingefügt), FLORA („validates readiness at generation time, not at connection time“) | Beim Run prüfen: Auflösung Geometrie = Auflösung Render, Kamera identisch. |

---

## 5 · Lizenzbefunde (Regel 1 und 2 der CLAUDE.md)

**Ausdrücklich gemeldete GPL/AGPL-Funde:**

| Komponente | Lizenz (geprüft an LICENSE, 24.09.2026) | Folge [S] |
|---|---|---|
| `Comfy-Org/ComfyUI` (Backend) | **GPL-3.0** | Kein Import, kein Code-Übernehmen. Nur zulässig wie Blender: als **eigenständiges Programm hinter einer Prozessgrenze** (HTTP/WebSocket-API), unverändert, austauschbar, im NOTICE deklariert. |
| `Comfy-Org/ComfyUI_frontend` | **GPL-3.0** | **Nicht** einbetten, keine Komponenten/Stile übernehmen. Die Farbtabelle der Typen ist eine Idee, kein Code — Ideen sind frei, Quelltext nicht. |
| `chaiNNer-org/chaiNNer` | **GPL-3.0** | Nur als Vorbild. |
| `nodetool-ai/nodetool` | **AGPL-3.0** | Nur als Vorbild; AGPL greift auch bei Netzbetrieb. |
| `BennyKok/comfyui-deploy` | **AGPL-3.0** | Nur als Vorbild. |

**Permissiv und als Baustein denkbar:** `invoke-ai/InvokeAI` **Apache-2.0** · `griptape-ai/griptape-nodes` (Engine) **Apache-2.0** · `xyflow/xyflow` (React Flow, von Invoke genutzt) **MIT** · `shrimbly/node-banana` **MIT**.

**Modellgewichte:** Krea listet „Flux 2 = FLUX.2 [dev]“ als Knotenmodell [B]. [S] Für uns bleibt FLUX.2-dev ausgeschlossen (Non-Commercial, CLAUDE.md Regel 1) — Muster 25 (Lizenz beim Laden prüfen) wäre der technische Schutz dagegen.

---

## 6 · Was daraus für den Render-Knoten folgt (Kurzfassung, alles [S])

- **Gebündelt vorne, zerlegt dahinter.** Ein Render-Knoten (Muster 1, 22), der sich aufklappen lässt. So bedienen alle Cloud-Werkzeuge ihre Nutzer, und so hat ComfyUI mit Subgraphs nachgezogen.
- **Geometrie ist bei uns Hauptsache, nicht Referenz.** Die Wettbewerber behandeln Bildeingänge als „Referenzen“ (Anzahl, ja/nein). Unser Knoten braucht *typisierte Geometrie-Eingänge mit Stärke und Zeitfenster* (Muster 2, 3, 21).
- **Die Lücke ist die Prüfung.** Kein Werkzeug zeigt am Knoten, *wie gut das Bild zur Geometrie passt*. Ein eigener Ausgang „Prüfbericht“ plus Zustand „veraltet/blockiert/durchgefallen“ (Muster 13, 16) wäre das Unterscheidungsmerkmal.
- **Kosten = Zeit.** Wo andere Credits zeigen, zeigen wir geschätzte GPU-Zeit auf dem Run-Knopf (Muster 7).
- **App-Modus ist die iPad-Oberfläche.** Der Graph bleibt Quelle; die Stift-Oberfläche ist ein App-Modus mit wenigen markierten Eingängen (Muster 23, 24) — deckt sich mit Regel 4 (Kern ohne Oberfläche nutzbar), wie bei InvokeAI (Linear UI und Editor bauen denselben Graphen).

---

## 7 · Grenzen dieser Recherche

- Bei Magnific/Freepik, Adobe, Runway und Figma Weave nur Suchauszüge und Testberichte; Details zu Knoten-Innenleben (z.B. wo genau der Seed sitzt) dort **nicht belegt**.
- Keine Bildschirmfotos ausgewertet; Aussagen zu Layout („im Knoten“ vs. „im Panel“) stammen aus Textdoku.
- Abwesenheitsbefund in 3.11 (keine Geometrie-Prüfung) beruht auf Suche, nicht auf Test.
- Lizenz von ViewComfy nicht geprüft; Editor-Lizenz von Griptape nicht öffentlich einsehbar.
- Glif und Visual Electric sind nur noch historisch relevant; Leonardo Blueprints ohne eigenen Editor.
