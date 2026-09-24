# Figma Weave (vormals Weavy): Inventar des Knotensystems

Stand der Recherche: 24.09.2026. Reine Web-Recherche: kein Konto angelegt, kein Login, keine
kostenpflichtige Aktion.

## Legende und Quellenlage

| Marke | Bedeutung |
|---|---|
| **[V]** | Direkt aus der genannten Quelle belegt (Wortlaut oder Screenshot gesehen) |
| **[S]** | Sekundärquelle (Presse, Blog Dritter, Suchmaschinen-Zusammenfassung). Plausibel, aber nicht aus erster Hand |
| **[A]** | Von mir abgeleitet oder vermutet. Nicht belegt |

**Wichtigste Quelle** ist das offizielle Hilfe-Center «Figma Weave's Knowledge Center» unter
`https://help.weavy.ai/en/` (Intercom). Die Domain blockt automatisierte Abrufe per Cloudflare.
Die Artikel sind aber inhaltsgleich über den Intercom-Spiegel `https://intercom.help/figmaweave/en/…`
abrufbar (gleiche Artikel-IDs). Alle 83 Artikel der Sammlungen «Nodes and Models Documentations»,
«Weave's Editor», «My Dashboard», «Account management» und «FAQ» wurden so im Volltext
gelesen. Zitiert wird unten immer die kanonische URL `help.weavy.ai/en/articles/<id>`.
Zusätzlich wurden die Screenshots aus den Artikeln angesehen. Mehrere UI-Aussagen unten stützen
sich auf diese Screenshots («Screenshot in …»).

**Nicht zugänglich:** `app.weavy.ai`, also die öffentlichen Flows und Rezepte, ist für diese
Maschine per Cloudflare gesperrt. YouTube (Kanal @figmaweave, Tutorials) liefert nur eine
Captcha- bzw. 401-Seite. `figma.com/community/ai-workflows` antwortet mit 403. Inhalte der
Beispiel-Workflows (auch «ControlNet - Structure Reference») sind darum **nicht** aus erster
Hand erfasst.

Weave ist ein proprietärer SaaS-Dienst. Wir übernehmen **nur UX-Muster**, weder Code noch Assets.

---

## 1. Überblick

- Weavy wurde 2024 in Tel Aviv gegründet und im Herbst 2025 von Figma übernommen. Seither heisst
  es «Figma Weave». Die Marketing-Seite liegt jetzt auf `weave.figma.com` (weavy.ai leitet mit
  301 dorthin um), die App weiterhin auf `app.weavy.ai`. [V] https://www.figma.com/blog/welcome-weavy-to-figma/,
  [V] https://help.weavy.ai/en/articles/12692387-figma-weave-faq, [S] https://techcrunch.com/?p=3063533
- Selbstbeschreibung: «Access all AI models and professional editing tools in one node-based
  platform». Genannte Modell-Anbieter: Google, Kling, OpenAI, Bytedance, Black Forest Labs,
  Runway, Luma, LTX, Wan, Grok, Recraft, Bria. [V] https://weave.figma.com/
- Werkzeuge auf der Startseite: Invert, Outpaint, Crop, Inpaint, Mask extractor, Upscale,
  **Z depth extractor**, Image describer, Channels, Painter, Relight. Dazu «Layers, type, and
  blends» (Compositing) und «From Workflow to Tool … automatically generating a simplified UI».
  [V] https://weave.figma.com/
- Ausführung der Modelle: fal.ai ist das Inferenz-Backend. [S] https://blog.fal.ai/powering-creative-workflows-with-weavy-x-fal/
- Die Arbeitsrichtung ist links nach rechts: «inputs connect on the left, outputs come out on the
  right». [V] https://help.figma.com/hc/en-us/articles/42847574436119
- Für den Browser werden Hardwarebeschleunigung und WebGL verlangt, Chrome wird empfohlen.
  [V] https://help.weavy.ai/en/articles/12449982-how-do-i-configure-my-browser-for-figma-weave

---

## 2. Vollständige Knotenliste (Stand Hilfe-Center)

### 2.1 Grundbegriffe «Knoten» und Porttypen

- Ein Knoten ist eine Funktion mit Eingängen links und Ausgängen rechts. Verbunden wird durch
  Ziehen vom Ausgangs-Handle zum Eingangs-Handle. Verbunden werden darf nur Kompatibles
  («text to text, image to image»). [V] https://help.weavy.ai/en/articles/12292386-understanding-nodes
- **Zwei Klassen:**
  - **Generative AI Nodes:** haben einen «Run»-Button, kosten Credits je Generierung und
    erzeugen neue Inhalte.
  - **Non-Generative Nodes:** Painter, Blur, Multi-Layer-Komposition, Prompt Concatenator usw.
    Sie laufen ohne Credits.

  [V] ebd.
- **Farbcode der Typen** (offiziell): Green = Image, Purple = Text, Red = Video, Purple = LoRA,
  Blue = Array / List / 3D, White = «Multiple inputs option», **Lime = Mask**. [V] ebd.
  Im Screenshot im selben Artikel ist die Prompt-Leitung pink-violett. Ein Datei-Ausgang eines
  Import-Knotens ist grün und mit «File» beschriftet (Screenshot in
  https://help.weavy.ai/en/articles/14653652-working-with-media).
- **Pflicht-Eingänge** sind mit einem Stern markiert. Fehlt ein Pflicht-Eingang, läuft das
  Modell nicht oder nicht korrekt. [V] https://help.weavy.ai/en/articles/12343730-how-can-i-know-which-inputs-are-mandatory-for-a-model-to-run
  Im Screenshot tragen die Ports Beschriftungen wie «Prompt*» und «Image 1*» (Credit-Artikel, siehe 3.3).
- **Automatisches Verbinden:** Eine Leitung, die auf einen Knoten fällt, verbindet sich selbst
  mit dem passenden Eingang, der Reihe nach: die erste Leitung mit dem ersten freien passenden
  Eingang. Ohne passenden Eingang entsteht keine Verbindung. Bei Mehrfach-Eingängen
  (z.B. mehrere Bilder) **erscheinen neue Eingangs-Slots automatisch**. Lässt man eine Leitung
  ins Leere fallen, öffnet sich ein Menü zum Erzeugen eines neuen, gleich verbundenen Knotens.
  [V] https://help.weavy.ai/en/articles/14688276-connecting-edges-wires
- Wer beim Ziehen Alt/Option hält, bekommt Knotenvorschläge und eine automatische Verbindung.
  [V] https://help.weavy.ai/en/articles/14688389-keyboard-shortcuts

### 2.2 Eingabe- und Datentyp-Knoten («Datatypes», «Text Tools»)

Quellen: [V] https://help.weavy.ai/en/articles/12268346-datatypes und
[V] https://help.weavy.ai/en/articles/12268282-text-tools

| Knoten | Zweck und Verhalten |
|---|---|
| **Prompt** | Freitext-Prompt. Kann **Variablen** tragen: «Add Variables» erzeugt einen neuen Eingangs-Handle, ein daran angeschlossener Text-Knoten wirkt als Variable. Im Text wird sie mit `@` referenziert und darf mehrfach vorkommen. Anzeige umschaltbar: «Variable Source / Value / Source + Value» ([V] https://help.weavy.ai/en/articles/14047674-prompt-variables). Tastenkürzel Cmd/Ctrl+P. Ein Doppelklick auf einen Text-Handle erzeugt einen verbundenen Prompt-Knoten ([V] https://help.weavy.ai/en/articles/15263628-new-figma-weave-delights-4) |
| **Text** | wie Prompt; zeigt ein Text-Attribut eines Modells als Knoten |
| **Number** | numerisches Attribut mit Min, Max und Nachkommastellen; Typ «float» einstellbar |
| **Toggle** | Wahr/Falsch-Attribut |
| **List Selector** | Liste als Dropdown: von Hand, aus einem Array-Knoten oder aus einem Listen-Attribut eines Modells |
| **Seed** | macht das Seed-Attribut sichtbar. «each generated output receives a seed, either a random one or one that is manually selected» |
| **Array** | mehrere Texte, per Trennzeichen zerlegt (im Figma-Beispiel ein Asterisk); speist List- oder Iterator-Knoten ([V] https://help.figma.com/hc/en-us/articles/42847574436119) |
| **Color Palette** | Farbsatz; Ausgänge: gerendertes Farbfeld (Bild) **und** Liste von Hex-Codes ([V] https://help.weavy.ai/en/articles/12268186-editing-tools) |
| **Prompt Concatenator** | beliebig viele Text-Eingänge (Knopf «+» unten links) plus Zusatztext, zusammengefügt |
| **Prompt Enhancer** (generativ) | verbessert einen Prompt; LLM per Dropdown wählbar, Anweisungen editierbar |
| **Run Any LLM** (generativ) | Text- und Bild-Eingänge an ein beliebiges LLM, Antwort als Text |
| **Image Describer** / **Video Describer** (generativ) | macht aus Bild oder Video einen Prompt; LLM wählbar, «Image/Model Instructions» editierbar |

**Wichtiges Muster: «Set as Output».** Im Parameter-Panel steht neben jedem Parameter ein
Knopf. Er holt den Parameter als eigenen Knoten (Number, Toggle usw.) auf die Leinwand.
[V] Datatypes-Artikel. Der Screenshot dort zeigt das Panel mit Aspect Ratio, Cfg, Prompt
Strength (mit dem Knopf), Steps, Seed («Random»-Checkbox und Wert 195539), Output Format und
Output Quality.

### 2.3 Helfer-Knoten («Helpers»)

Quelle: [V] https://help.weavy.ai/en/articles/12268300-helpers-overview

| Knoten | Zweck und Verhalten |
|---|---|
| **Import** | Datei hochladen, per Drag&Drop oder per Link. Bild: JPEG/PNG/HEIC/WEBP; Video: MP4/QuickTime; Audio: MP3/WAV/OGG; **3D nur GLB**. Mehrere Dateien landen in *einem* Knoten ([V] https://help.weavy.ai/en/articles/14653652-working-with-media). Grenzen: Bild 1 GB, Video 20 GB ([V] https://help.weavy.ai/en/articles/12414427-what-is-the-size-limit-for-imported-files) |
| **Export** | Download; behält das Format der Quelle (PNG bleibt PNG) |
| **Preview** | zeigt ein Ergebnis in einem neuen, «sauberen» Knoten |
| **Import Model** | Modell per URL von **Fal, Replicate, CivitAI** einbinden. Die Parameter erscheinen automatisch im rechten Panel; «Save model» macht es workspace-weit verfügbar ([V] https://help.weavy.ai/en/articles/12265334-importing-models). Nur für bezahlte Pläne |
| **Import LoRA** / **Import Multiple LoRAs** | eigene LoRA hochladen. Anschluss an «LoRA1», Stärke über einen Number-Knoten an «LoRA1 scale» ([V] https://help.weavy.ai/en/articles/11046940-importing-loras-in-figma-weave) |
| **Router** | ein Eingang auf viele Ausgänge; ein Tausch der Quelle genügt dann an einer Stelle. Entsteht durch **Doppelklick auf einen Ausgang** |
| **Output** | markiert das Ergebnis für ein **Tool** (App-Modus); erst damit erscheint der Reiter «Tool» |
| **Compare** | zwei Bilder im **Slider**- oder **Toggle**-Modus vergleichen (Toggle per Augen-Symbol). Man wählt, welches Bild weitergeht, und zieht von dort den Ausgang ([V] https://help.weavy.ai/en/articles/14046860-compare-node) |
| **Sticky Notes** | Notizen auf der Leinwand, Farbe und Schriftgrösse wählbar ([V] https://help.weavy.ai/en/articles/14046539-sticky-notes) |
| **Figma** | ein Figma-Frame als Knoten. «Add Input» (Text oder Bild) bindet eine Ebene im Frame an einen Weave-Eingang. «Connect» schreibt Änderungen in die Figma-Datei zurück, «Update» holt Änderungen aus Figma ([V] https://help.weavy.ai/en/articles/16440592-figma-node) |

### 2.4 Iteratoren (Stapelverarbeitung)

Quelle: [V] https://help.weavy.ai/en/articles/12343281-iterators

- **Text Iterator:** mehrere Texte, jeder bleibt ein eigener Lauf, alle gehen ins selbe Modell.
  Eingabe von Hand, per Array oder per Prompt. **CSV-Import:** Wird eine CSV auf die Leinwand
  gezogen, entsteht je Spalte ein Iterator ([V] https://help.weavy.ai/en/articles/15068263-new-figma-weave-delights-3).
- **Image Iterator** und **Video Iterator:** mehrere Bilder oder Videos, «generate all … at once
  as separated runs».
- **Iterator aus Ergebnissen:** Im Drei-Punkte-Menü eines Knotens mit mehreren Ergebnissen macht
  «Create Iterator» daraus einen neuen Iterator ([V] https://help.weavy.ai/en/articles/14688156-creating-iterators-from-existing-node).
- **Anzeige:** Ein Knoten mit Iterator-Ergebnissen zeigt wahlweise ein Ergebnis, alle oder
  «a specific batch» ([V] https://help.weavy.ai/en/articles/14688070-unpack-a-node).
- **Kosten:** Bei «dynamic iterators» kann der Preis vor dem Lauf nicht angegeben werden.
  [V] https://help.weavy.ai/en/articles/16202764-running-weave-tools-from-external-agents-mcp

### 2.5 Bearbeitungs-Knoten («Editing Tools»)

Quelle: [V] https://help.weavy.ai/en/articles/12268186-editing-tools

| Knoten | Zweck und Parameter |
|---|---|
| Rotate and Flip | Bild oder Video drehen und spiegeln |
| Color Palette | siehe 2.2 |
| Color Correction | Hue, Saturation, Brightness, Contrast u.a., für Bild und Video |
| **Levels** | Histogramm; Schwarz-, Grau- und Weisspunkt |
| **Compositor** | Ebenen-Komposition, siehe 2.7 |
| Trim | Video kürzen |
| **Painter** | Malen auf Bild oder konfigurierbarer Fläche. Vier Reiter: Background (Farbe, Grösse), Brush (Farbe, Grösse, Härte), Shapes, Eraser. **Zwei Ausgänge: Bild und Maske** |
| **Crop** | Zuschnitt per Seitenverhältnis-Vorgabe oder mit freien Massen |
| **Resize** | streckt oder staucht auf freie Masse, «useful for meeting model input requirements» |
| Blur | Fast Box oder Gaussian, mit Stärke |
| **Invert** | invertieren, «especially useful … to invert a mask» |
| **Channels** | Zugriff auf R, G, B und Alpha |
| Extract Video Frame | ein Bild aus einem Video, gewählt per Zeitleiste, Frame-Nummer oder Timecode |
| Video to GIF | Video wird GIF |

**Hinweis:** Auf der Startseite werden auch **Upscale, Inpaint, Outpaint, Relight und Z Depth
Extractor** als Werkzeuge beworben ([V] https://weave.figma.com/). Im Hilfe-Center haben sie
**keinen eigenen Knoten-Artikel**. Upscale, Inpaint, Outpaint und Relight erscheinen dort als
**Modelle** in den Modell-Vergleichstabellen (siehe 2.9), also als generative Knoten mit
Credits. Zum **Z Depth Extractor** fand sich **keine** Beschreibung: weder Eingänge noch
Parameter noch Modell noch Preis. [A] Vermutlich ein monokularer Tiefenschätzer (Bild → Graustufen-Tiefenbild).

### 2.6 Masken-Knoten («Matte Tools»)

Quelle: [V] https://help.weavy.ai/en/articles/12414117-matte-tools

| Knoten | Eingänge und Verhalten |
|---|---|
| **Mask Extractor** | Eingang Bild. Zerlegt das Bild automatisch in Teile; Shift fügt hinzu, Alt+Shift zieht ab. Ansicht Original oder Maske umschaltbar (oben rechts im Knoten) |
| **Mask By Text** | Bild und Text; die Maske wird per Beschreibung erzeugt |
| **Matte Grow / Shrink** | Bild, Video oder Maske; **Slider unten im Knoten** |
| **Merge Alpha** | Bild und Maske ergeben ein Bild mit Alpha |
| Video Matte | Video, Matte-Typ per Dropdown |
| Video Mask by Text | Video und Text, «run the model» (generativ) |

### 2.7 Compositor und Timeline

Quellen: [V] https://help.weavy.ai/en/articles/15887786-compositor-node,
[V] https://help.weavy.ai/en/articles/14689260-timeline-editor

- Jeder Eingang wird eine Ebene. Ebenen lassen sich sortieren, transformieren, mit Mischmodus
  versehen und gruppieren. Eine Gruppe wirkt als Einheit.
- Werkzeugleiste: Move, Pan, Text, Shapes (Rechteck, Ellipse, Dreieck, Stern), Vector (Pfad).
  Hintergrund per «Fill».
- Medien lassen sich direkt hineinziehen, ohne vorgelagerten Knoten. Ein Assets-Panel zählt, wie
  viele Ebenen ein Asset nutzen.
- Ebenen, die von einem verbundenen Knoten gespeist werden, lassen sich **nicht** duplizieren.
  Beim Löschen einer Gruppe rücken sie eine Ebene hoch statt zu verschwinden.
- Timeline hinter «Edit»: Dauer, Framerate, Trimmen, Sichtbarkeit, **Lock** und Mute je Ebene.
  Im Panel: Opacity, Blend, Position, Scale, Alignment.
- Der Mockup auf der Startseite zeigt links eine Ebenenliste und rechts Dimensions, Position,
  Rotation, Opacity, Blend Mode, Font, Style, Size und Fill ([V] Bild «Weavy UI» auf https://weave.figma.com/).

### 2.8 Weitere Spezial-Knoten

- **Gen Effect:** Ein Effekt wird in Worten beschrieben (optional mit Referenzbild), dann
  «Generate effect». Das Ergebnis bringt **automatisch passende Regler** mit; um bestimmte
  Regler kann man im Prompt bitten. «Edit» überarbeitet den Effekt. Kosten: Credits, nur auf
  bezahlten Plänen. [V] https://help.weavy.ai/en/articles/16118602-gen-effect-node,
  [V] https://help.weavy.ai/en/articles/16137383-gen-effect-node-launch-promotion
- **Gaussian Splat / World Labs:** 1 bis 5 Bilder, Prompt oder Video ergeben eine begehbare
  3D-Welt. Modell-Optionen «Plus» und «Mini». Kamera im Orbit- oder Fly-Modus (WASD, Q/E),
  **Field of View** und **Dimensions**. **Reset** setzt zurück, ein **Schloss-Symbol sperrt
  Kamera-Modus, FoV und Masse**. **Zwei Ausgänge:** die 3D-Welt und ein gerendertes Bild der
  aktuellen Kamera. Empfohlener Weg: «feed the rendered image into an image model along with a
  prompt … lock in the camera angle and composition first». Import und Export als `.ply`.
  [V] https://help.weavy.ai/en/articles/16554960-gaussian-splat
- **3D-Knoten, Kling Element:** In einem offiziellen Beispiel steuern ein 3D-Knoten und ein
  «Kling Element»-Knoten die Blickwinkel eines Objekts für ein Videomodell.
  [V] https://www.figma.com/blog/five-figma-weave-workflows/

### 2.9 Modell-Knoten nach Kategorie (mit Preisen)

Quellen: die Vergleichsartikel. Alle Preise gelten «per run» in Credits. Die Tabellen sind als
flache Listen ausgelesen und die Zuordnung wurde durch Abzählen geprüft. Zwei Werte stimmen mit
Screenshots überein: Imagen 3 = 6 und Gemini 2.0 Flash = 0.1. Hinweis der Quelle: «prices …
may change».

- **Image (Text→Bild)** ([V] https://help.weavy.ai/en/articles/12284752-image-models-comparison):
  ChatGPT Images 2.0 (1–37), Reve 4, Higgsfield Image 21, GPT Image 1 8, Imagen 4 6, Imagen 3 6,
  Imagen 3 Fast 3, Flux 2 Pro 5, Flux 2 Flex 14, Flux 2 Dev LoRA 4, Flux 1.1 Ultra 7,
  Flux Pro 1.1 5, Flux Fast 0.4, Flux Dev LoRA 4, Recraft V3 5, Mystic 12, Ideogram V3 4,
  Ideogram V3 Character 15, SD 3.5 8, Minimax Image 01 1, Bria 6, Dalle 3 5, Luma Photon 2,
  Nvidia Sana 0.2, Nvidia Consistory 5.
  - Pflicht-Eingang ist fast immer «Prompt». Optional sind je nach Modell Reference Image,
    Negative Prompt, LoRA/LoRA Weight, Style Image, **Control Image**, Mask usw.
  - Seitenverhältnisse sind je Modell verschieden: feste Pixelmasse, Verhältnisse,
    «Custom», 1K/2K/4K.
- **Edit Image** ([V] https://help.weavy.ai/en/articles/12343904-edit-image-models-comparison),
  35 Modelle, u.a.:
  - Gemini 3.1 Flash «Nano Banana 2» (4–18), Gemini 3 Pro (15–30), Seedream V5/V4.5/V4 Edit (je 4),
    Qwen Image Edit 2511 (10), Flux Kontext (3), Flux Kontext Multi Image (10), GPT Image 1/1.5 Edit (8/7),
    Gemini 2.0 Flash (0.1), Flux 2 Max (10)
  - Inpaint-Modelle: Flux Fill Pro 6, Ideogram V3 Inpaint 11, SD3 Inpaint 4, Bria Inpaint 5
  - Outpaint: Flux Pro Outpaint 6, SD3 Outpaint 5
  - Remove Background: SD3 2, Bria 0.6
  - Replace Background, Content-Aware Fill, Kolors Virtual Try-On
  - **Relight 2.0 (10)**
  - Zusatzoptionen je Modell z.B. «Enable Web Search», «Enhance Prompt Mode», «Add multiple LoRAs», «Denoise, Downscale»
- **Generate from Image** (Struktur- und Referenz-geführt)
  ([V] https://help.weavy.ai/en/articles/12344174-generate-from-image-models-comparison):
  Flux Dev Redux 3, **Flux ControlNet & LoRA 10**, **Flux Canny Pro 6**, **Flux Depth Pro 6**,
  **Qwen Edit Multiangle 4**, Image to Image 10, **Stable Diffusion controlnets 1**, **Sketch To Image 0.1**.
  - Pflicht-Eingänge sind überwiegend «**Control Image**» plus «Prompt». Die Zuordnung je
    Modell ist in der flachen Tabelle nicht ganz eindeutig.
  - Anmerkungen der Tabelle: «You need to add the LoRA as a link» und «**Has Camera Control
    Options on the toolbar**». [A] Die zweite gehört wohl zu Qwen Edit Multiangle.
- **Enhance Image (Upscale)** ([V] https://help.weavy.ai/en/articles/12344205-enhance-images-models-comparison):
  Topaz Upscale 19, Topaz Sharpen 19, Recraft Crisp Upscale 5, Magnific Upscale 12,
  Magnific Precision Upscale (V2) 18, Magnific Skin Enhancer 18, Enhancor 36.
  Faktoren 2×, 4×, 8×; Formate bis TIFF.
- **Video** ([V] https://help.weavy.ai/en/articles/12344226-video-models-comparison):
  Seedance 2.0, Kling 3, Wan 2.5/2.2, Grok Imagine, Sora 2, LTX 2, Moonvalley, Veo 3.1/3/2,
  Runway Gen-4.5/4/3, Luma Ray 2, Minimax, Hunyuan u.a. Die Eingänge heissen First Frame und
  Last Frame. Die Preise hängen von **Dauer und Auflösung** ab.
- **Generate from Video** ([V] https://help.weavy.ai/en/articles/12344285-generate-from-video-models-comparison):
  u.a. Runway Aleph, Luma Modify/Reframe, Kling Motion Control, **Wan Vace Depth**,
  Wan Vace Pose, Wan Vace Reframe/Outpainting. Preise gestaffelt, z.B. «480p – 48 / 720p – 100»
  oder «5s – 92 / 10s – 184».
- **Enhance Video**, **Lip Sync**, **Vector** (Vectorizer mit SVG/EPS/PDF/DXF, Recraft V3 SVG)
  und **3D** (Rodin/Rodin V2, Trellis, Meshy V6, Hunyuan 3D, Sam 3D Objects; bis 96 Credits;
  Optionen Topologie, Polygonzahl, Texturgrösse).
  [V] https://help.weavy.ai/en/articles/12344357-3d-models-comparison und Nachbarartikel
- **Verified / Unverified:** Das Badge «Verified by Figma» steht für Vertrag, kein Training auf
  Kundendaten und Freistellung (Indemnity). Bei ungeprüften Modellen verlinkt der Knoten unten
  AGB und Datenschutz. Vor dem ersten Lauf muss der Hinweis «unverified» bestätigt werden.
  Tools mit ungeprüften Modellen dürfen nicht in die Community.
  [V] https://help.weavy.ai/en/articles/14034721-verified-and-unverified-models

---

## 3. Wie ein Modell-Knoten aussieht und sich verhält

### 3.1 Aufbau auf der Leinwand

Alles belegt [V] durch den Screenshot in https://help.weavy.ai/en/articles/12292386-understanding-nodes:

- **Kopfzeile:** Anbieter-Logo, Modellname (z.B. «Minimax Image 01») und rechts ein «…»-Menü.
- **Körper:** grosse Vorschau des aktuellen Ergebnisses **im Knoten selbst**.
- **Fuss:** Knopf «**→ Run Model**» unten rechts. Bei Bild-Eingängen gibt es zusätzlich einen
  Link «**Add another image input**» (Screenshot im Credit-Artikel).
- **Ports** sitzen als runde Handles links und rechts, beschriftet (z.B. «Prompt*», «Image 1*»,
  «Result»). Die Parameter stehen **nicht** im Knoten, sondern im rechten Panel.

### 3.2 Parameter-Panel statt Regler im Knoten

- Klick auf einen Knoten zeigt rechts alle Parameter: Seitenverhältnis, «prompt adherence» und
  modellspezifische Werte. [V] Understanding Nodes.
- Screenshot eines Flux-Knotens: Aspect Ratio (Dropdown), Cfg (Slider 3.5), Prompt Strength
  (0.6), Steps (28), **Seed (Checkbox «Random» + Zahl)**, Output Format (png), Output Quality (90).
  Jeder Parameter hat ein (i)-Symbol und den Knopf «Set as Output». [V] Datatypes-Artikel.
- **Ausnahmen mit Reglern im Knoten:** Matte Grow/Shrink (Slider unten), Compare (Method unten
  links), Mask Extractor (Ansicht oben rechts), Gen Effect (automatisch erzeugte Regler) und die
  Kamera-Bedienung des Gaussian-Splat-Knotens. [V] jeweilige Artikel.
- **Modellwahl:** Jedes Modell ist ein eigener Knotentyp. Es gibt keinen «Model»-Dropdown im
  generischen Knoten. Die Auswahl erfolgt im Toolbox-Panel links, gegliedert nach Kategorie
  (z.B. «Image Models → Generate from text»), oder per Tab oder Rechtsklick-Suche.
  - Der Tooltip beim Überfahren zeigt eine Kurzbeschreibung, **«From [Text] to [Image]»**
    (Typ-Chips in Typfarbe), das Lizenz-Tag **«Commercial Use»** und den Preis «6 credits».
  - [V] Screenshot in https://help.weavy.ai/en/articles/12267166-figma-weave-s-credit-system
  - Ausnahme: LLM-Knoten (Prompt Enhancer, Any LLM, Describer) wählen das Modell per Dropdown.
    [V] Text-Tools-Artikel.
- **Vorlagen:** Ein Modell mit eigenen Einstellungen lässt sich als benannte Vorlage speichern
  («Saved Models»), ebenso Knoten und Knotengruppen. Die Ablage «Saved» ist workspace-weit.
  [V] https://help.weavy.ai/en/articles/15495911-using-the-saved-section

### 3.3 Kosten und Credits in der Oberfläche

Alles [V] aus https://help.weavy.ai/en/articles/12267166-figma-weave-s-credit-system samt Screenshots:

- Der Preis erscheint an zwei Stellen:
  1. beim Überfahren des Modells in der Toolbox;
  2. nach Klick auf den Knoten oben rechts im Panel neben einem «✱»-Symbol, z.B. «Gemini 2.0 Flash ✱ 0.1».
- **Der Preis ändert sich live mit den Parametern** (Sekunden, Auflösung): «you will see the
  credit price change when you adjust these parameters».
- Unten im rechten Panel sitzt ein Block «**Run selected nodes**»: «Runs [– 1 +]», «**Total cost ✱ 8 credits**»
  und der Knopf «**→ Run selected**». Mehrere markierte Knoten lassen sich also mit Wiederholungszahl
  gemeinsam starten, bei angezeigter Gesamtsumme. [V] Screenshots im Credit- und Datatypes-Artikel.
- Oben rechts stehen ständig das Credit-Guthaben (z.B. «10.9K credits») und ein Dropdown
  «**No active runs**», die Warteschlange der laufenden Läufe. [V] Screenshots.
  [A] Die Laufanzeige dürfte dort den Fortschritt zeigen. Wie Fortschritt und Fehler im
  Knoten selbst aussehen, ist **nicht dokumentiert** (siehe Lücken).
- Über MCP laufende Tools zeigen die Kosten und verlangen eine Bestätigung. Läufe ohne Kosten
  überspringen das, und bei dynamischen Iteratoren wird gesagt, dass kein Preis angebbar ist.
  [V] https://help.weavy.ai/en/articles/16202764-running-weave-tools-from-external-agents-mcp
- Das Verbrauchsprotokoll lässt sich als Download je Zeitraum abrufen.
  [V] https://help.weavy.ai/en/articles/13751776-credit-usage-log

### 3.4 Ergebnisse, Verlauf, Varianten

- **Ergebnisse stapeln sich im Knoten:** «When you generate multiple results using the same node,
  they are all hosted within it». Die Ansicht wechselt zwischen einem, allen oder einem
  Iterator-Batch. [V] https://help.weavy.ai/en/articles/14688070-unpack-a-node
- **Bedienelemente im Medien-Knoten:** Knopf «Single/Gallery», Pfeile mit Zähler «1 / 7»,
  Sortierung (Name/Datum), Download, Pixelmass-Anzeige («1088x976»), «+ Add more images».
  [V] Screenshot in https://help.weavy.ai/en/articles/14653652-working-with-media
- **Aufräumen:** «Remove Current Generation» und «Remove All Other Generations» im «…»-Menü.
  [V] https://help.weavy.ai/en/articles/12968045-removing-a-file-from-a-node
- **Unpack:** verteilt alle Ergebnisse als einzelne Knoten in eine Gruppe. **Create Iterator:**
  macht aus ihnen einen Iterator. [V] siehe 2.4
- **Herkunft pro Bild:** Die Galerie-Ansicht öffnet sich per Symbol unten rechts im Knoten oder
  per **Leertaste** beim Überfahren. «Show info» zeigt **Prompt, Parameter, Seed** und weitere
  Details. Oben: Zoom, Info, Download, Link teilen; rechts Miniaturen.
  [V] https://help.weavy.ai/en/articles/12292408-media-gallery
- **Seeds und Varianten:** Seed zufällig oder fest (Panel oder Seed-Knoten). Varianten entstehen
  über «Runs» > 1, über Iteratoren oder über mehrere parallel verbundene Modell-Knoten
  (Router-Muster). [V]/[A] Kombination aus Datatypes-, Credit- und Helper-Artikel.
- **Vergleich:** Compare-Knoten (Slider/Toggle) für zwei Bilder. Für Modellvergleiche hängt man
  mehrere Modelle an denselben Prompt; Beispiel-Workflow «Multiple Models» auf der Startseite.
  [V] https://weave.figma.com/
- **Caching und Neuläufe:** **Nicht dokumentiert.**
  [A] Das Verhalten spricht dafür, dass nichts implizit neu gerechnet wird:
  - Generative Knoten laufen nur auf Klick («Run Model» oder «Run selected»).
  - Jeder Lauf **hängt ein neues Ergebnis an** und überschreibt nichts.
  - Nachgelagerte Knoten verwenden das jeweils gewählte Ergebnis.
  - Nicht-generative Knoten (Levels, Crop …) rechnen ohne Run-Knopf, also vermutlich sofort.
  - Einen dokumentierten «Run all»-Knopf gibt es im Editor nicht, wohl aber «Run» im Tool-Modus.

### 3.5 Knoten-Menü «…» (gesammelt)

Belegt [V] aus den jeweiligen Artikeln:

- Lock/Unlock (bestimmt die Sichtbarkeit im Tool, mit Schloss-Symbol neben «…»)
- Remove from Group
- Create Iterator
- Unpack
- Download current / Download all
- Remove Current / All Other Generations
- Save Node

---

## 4. Ebene des Graphen

- **Knoten einfügen:**
  - aus der Toolbox links (Suche),
  - mit **Tab** oder **Rechtsklick** und Tippen,
  - durch Loslassen einer Leitung im Leeren (typgerechtes Menü).

  [V] Understanding Nodes, Connecting Edges.
- **Leitungen:**
  - Stil Elbow, Line oder Bezier, global einstellbar
    ([V] https://help.weavy.ai/en/articles/14047607-changing-wire-styles)
  - Löschen per Auswahl und Delete, auch im Rechteck
    ([V] https://help.weavy.ai/en/articles/14655207-deleting-edges-wires)
  - «Multi-Connect»: mehrere markierte Knoten auf einmal verbinden
  - «Smart Edge Dragging»: mit Shift über Ziele fahren
    ([V] https://help.weavy.ai/en/articles/15263628-new-figma-weave-delights-4)
- **Knoten-Operationen:**
  - Shift+Delete löscht einen Knoten **und hält den Fluss verbunden**
    ([V] https://help.weavy.ai/en/articles/14878372-new-figma-weave-delights-2)
  - Cmd+Shift+D oder Alt-Ziehen dupliziert **mit Verbindungen**
    ([V] https://help.weavy.ai/en/articles/15068263-new-figma-weave-delights-3)
- **Navigation:** Hand-Werkzeug H, Auswahl V, Zoom mit Cmd/Ctrl+Scrollen oder Pinch, Zoomanzeige
  unten. Undo/Redo stehen in der unteren Werkzeugleiste.
  [V] https://help.weavy.ai/en/articles/12292356-navigating-the-canvas, Tastenkürzel-Artikel.
- **Gruppen:** Cmd/Ctrl+G. Titel und Titelgrösse, Farbe, «Resize to Fit», Ungroup. «Download All»
  für eine Gruppe. Gruppen lassen sich als wiederverwendbare Bausteine mit Vorschaubild speichern.
  [V] https://help.weavy.ai/en/articles/13560959-group-and-ungroup-nodes, Saved-Artikel.
- **Kommentare:** Es gibt nur **Sticky Notes**. Ein Kommentar-System im Figma-Sinn ist nicht dokumentiert. [V]/[A]
- **Versionen:**
  - Workflows werden automatisch versioniert: «Version History» mit **Restore** oder
    **Duplicate** ([V] https://help.weavy.ai/en/articles/16110597-version-history).
  - Gelöschte Workflows bleiben 30 Tage im Archiv
    ([V] https://help.weavy.ai/en/articles/14688405-workflow-trash).
- **Teilen:**
  - Rechte: nur Eingeladene, Workspace oder alle mit Link. Geteilte Workflows sind
    **read-only**; zum Bearbeiten «Duplicate». Eigentum lässt sich übertragen.
  - Team-Plan: «Workspace Files» read-only.
  - [V] https://help.weavy.ai/en/articles/12944804-sharing-files, https://help.weavy.ai/en/articles/12292543-file-collaboration
- **Vorlagen und Community:**
  - Workflows lassen sich in die Figma Community publizieren (Name, Beschreibung, Unterkategorie,
    Tags, Bild) ([V] https://help.weavy.ai/en/articles/15624624-publish-weave-workflows-to-the-figma-community).
  - Im Dashboard gibt es eine «Workflow library» mit Beispielen (Screenshot im Credit-Artikel).
  - Die Startseite verlinkt «Explore Our Workflows»: Multiple Models, Wan LoRA Inflate,
    **ControlNet – Structure Reference**, **Camera Angle Control**, Relight 2.0 human,
    Relight – Product, Wan LoRA – Rotate. [V] https://weave.figma.com/, Inhalt nicht abrufbar.

### 4.1 App-Modus («Tools», früher «Design Apps»)

Quelle: [V] https://help.weavy.ai/en/articles/12267755-tools samt Screenshots

- **Aktivieren:** Ein **Output**-Knoten ans Endergebnis schalten. Dann erscheint oben der
  Umschalter **«Canvas | Tool»**.
- **Welche Eingaben sichtbar werden:** «The attributes visible in your tool are generated from
  nodes that do not have an input (such as Prompt or Import Image nodes)». Alle offenen
  Wurzel-Knoten werden also automatisch zu Formularfeldern. **Ausblenden per Lock** im «…»-Menü.
  Parameter werden über «Set as Output» zu eigenen Knoten und damit zu Tool-Feldern ([A] Kombination mit 2.2).
- **Aufbau des Tool-Bildschirms** (Screenshot):
  - links eine Spalte mit Eingabefeldern, je mit farbigem Typ-Chip und optionaler Beschreibung
    («Add a description»);
  - unten «Runs [– 1 +]», «Total cost ✱ … credits» und ein grosser Knopf **Run**;
  - rechts die Ergebnisfläche.
- **Veröffentlichen:** «Create tool» mit Name*, Beschreibung und Thumbnail. Änderungen am
  Workflow wirken sich **nicht** auf das laufende Tool aus, bis man auf «**Update tool**» klickt.
  Jede Veröffentlichung wird **mit Zeitstempel versioniert** («Last Published At: August 12,
  9:56 AM ▾»). Alte Versionen lassen sich ansehen und teilen, aber nicht bearbeiten.
- **Teilen:** getrennt vom Workflow-Teilen. Empfänger sehen nur die Tool-Ansicht, der Ersteller
  immer die editierbare.
- **Weitere Kanäle:**
  - Tools laufen in **Figma Design** (nur Bild- und Vektor-Ausgaben). Dort ist ein Modal für
    die Eingaben vorgesehen, dann wählt man die Zahl der Läufe und klickt «Generate».
    [V] https://help.figma.com/hc/en-us/articles/40779260614935-Use-Weave-tools-in-Figma
  - Tools laufen über den **Figma-MCP-Server**, wo ein Agent sie auflisten, Eingaben prüfen,
    Dateien hochladen, starten, verfolgen und abbrechen kann. Workflows lassen sich per MCP
    **nicht** erstellen. [V] MCP-Artikel.
- **API:** geschlossene Beta nur für Enterprise.
  [V] https://help.weavy.ai/en/articles/12301695-api-integration

---

## 5. Architektur, Innenraum, Struktur-Führung

- **Offizieller Bezug zur Architektur:**
  - Figma nennt als Nutzer «Architects generating staging images»
    ([V] https://www.figma.com/blog/welcome-weavy-to-figma/).
  - Ein grosses internationales Architekturbüro wird im Figma-Blog als Nutzer zitiert (Name
    hier bewusst weggelassen, Regel 3 sinngemäss): «new users of Weave brought up to speed on Wednesday can produce content with it
    by Friday» ([V] https://www.figma.com/blog/connecting-figma-and-weave/).
  - Laut Suchmaschinen-Auszug aus Figma-Investorenunterlagen übersetzt dieses Büro damit «3D models
    into precise, photorealistic renderings» und stellt Tageslicht und städtischen Kontext ein
    [S]; die PDF liess sich nicht auslesen.
- **Community-Tools mit Architekturbezug** ([V] https://www.figma.com/blog/try-these-5-weave-tools-and-share-your-own/):
  - «Interior Design Moodboard to Render»: Moodboard ergibt ein fotorealistisches Raum-Rendering;
    **eingebaute Raumtypen und Kamerawinkel als Dropdowns**.
  - «Physical Architectural Model Maker»: Referenzfoto ergibt ein Modellfoto; Materialien für
    Gebäude, Landschaft und Details wählbar.
  - «Sketch Generator»: Prompt in drei Teilen (Raumtyp, Materialien, Blickpunkt) ergibt eine
    Konzeptskizze.
  - Tipp aus dem Artikel: Vokabular **per Dropdown** begrenzen, um mit unsauberen Eingaben
    umzugehen, und mit Laien testen.
- **Struktur- und Tiefenführung (ControlNet-artig):** Es gibt **keinen eigenen
  «ControlNet»-Knoten**. Struktur läuft über Modell-Knoten mit einem Eingang «**Control Image**»:
  - Flux Depth Pro, Flux Canny Pro, Flux ControlNet & LoRA, Stable Diffusion controlnets,
    Sketch To Image ([V] Generate-from-Image-Vergleich), dazu optional «Control Image» bei
    einzelnen Text→Bild-Modellen ([V] Image-Vergleich);
  - für Video Wan Vace Depth und Wan Vace Pose ([V] Generate-from-Video-Vergleich).
  - Die Tiefenkarte kommt entweder aus dem **Z Depth Extractor**, einer Schätzung aus einem
    Bild ([V] als Werkzeug auf https://weave.figma.com/, Details nicht dokumentiert), oder als
    importiertes Bild.
  - Die Vorlage «ControlNet – Structure Reference» existiert ([V] Startseite), ihr Inhalt war
    nicht abrufbar. Ein YouTube-Tutorial «Weavy Tutorial: Using ControlNet for precise design
    control» existiert (https://www.youtube.com/watch?v=mWRnijpv2pw), Inhalt nicht abrufbar.
- **Kamera:**
  - Qwen Edit Multiangle hat «Camera Control Options on the toolbar» ([V] Tabelle, Zuordnung [A]).
  - Gaussian Splat mit gesperrter Kamera, danach Bildmodell (siehe 2.8).
  - Die Seite «Camera Angle Control» bleibt allgemein
    ([V] https://www.figma.com/solutions/camera-angle-generator/).
- **Licht:** Relight 2.0 ist ein Edit-Modell für 10 Credits; Vorlagen «Relight 2.0 human» und
  «Relight – Product». Die Parameter von Relight sind **nicht dokumentiert**.
- **3D-Eingang:** Weave importiert nur **GLB**.
  [V] https://help.weavy.ai/en/articles/12343740-what-kinds-of-3d-models-does-figma-weave-support
  Es gibt keinen Hinweis auf IFC, Tiefen- oder Normalen-Pässe aus Geometrie. [A] Weave arbeitet
  bildbasiert: Struktur wird aus Pixeln *geschätzt*, nicht aus einem Modell *gerendert*.

---

## 6. Lizenz- und Preismodell, soweit es die Oberfläche prägt

- **Pläne** ([V] https://weave.figma.com/pricing, https://help.weavy.ai/en/articles/12267070-figma-weave-s-subscription-plans):

  | Plan | Preis | Credits pro Monat | Weiteres |
  |---|---|---|---|
  | Free | 0 | 150 | 5 Workflows; ohne Video- und Import-Modelle |
  | Starter | 24 $ | 1'500 | |
  | Professional | 45 $ | 4'000 | Rollover 3 Monate |
  | Team | 60 $/Person | 4'500 je Person | geteilter Pool, Limits je Person möglich |
  | Enterprise | auf Anfrage | eigene Zuteilung | eigene API-Schlüssel, erweiterte Indemnity |

- **Nachkauf:** 10 $ für 1'000 Credits (Starter) bzw. 1'200 (Pro/Team), 12 Monate gültig.
  [A] Damit ist 1 Credit ≈ 0.8–1 US-Cent: ein Flux-2-Pro-Bild kostet rund 5 Cent, ein
  Topaz-Upscale rund 19 Cent.
- **Gebühren nur für Generatives:** Nicht-generative Knoten sind gratis
  ([V] Understanding Nodes). Das prägt die Oberfläche: nur generative Knoten tragen Run-Knopf
  und Preis.
- **«Commercial license»** gilt laut Preisseite für alle Pläne ([V] Pricing). Dazu kommt das
  Lizenz-Tag «Commercial Use» im Modell-Tooltip und das Verified/Unverified-Badge (siehe 2.9, 3.2).
- Figma-AI-Credits und Weave-Credits sind getrennt. Weave-Tools in Figma sind in der offenen
  Beta gratis, später gegen Figma-AI-Credits.
  [V] https://help.figma.com/hc/en-us/articles/35965787376919-Figma-Weave-FAQ
- Eine Aktion kann den Preis ändern: Gen-Effect-Knoten waren zwei Wochen gratis und sind
  danach nur auf bezahlten Plänen verfügbar ([V] Promo-Artikel).

---

## 7. Lücken (nicht belegt, bewusst offen)

- Fehler- und Fortschrittsanzeige **im** Knoten: Spinner, Prozent, Fehlermeldung, Credit-Erstattung
  bei Fehlschlag. Nicht dokumentiert.
- Caching und Neuberechnung nachgelagerter Knoten bei geänderten Eingängen. Nicht dokumentiert
  (siehe [A] in 3.4).
- Parameter von Z Depth Extractor, Relight 2.0, Upscale-Knoten und Inpaint/Outpaint-Werkzeugen.
- Aufbau der Vorlagen «ControlNet – Structure Reference» und «Camera Angle Control» (app.weavy.ai gesperrt).
- YouTube-Inhalte (gesperrt).
- **Unzuverlässige Sekundärquellen**, hier bewusst **nicht** übernommen:
  - chasejarvis.com nennt ComfyUI-artige Knoten («Load Model», «Denoise Latent», «Apply
    ControlNet»), die im offiziellen Hilfe-Center nicht vorkommen.
  - Eine Suchzusammenfassung sprach von «grünen Kreisen/blauen Quadraten» als Ports. Das stammt
    aus einem Fremdprojekt auf GitHub und nicht aus Weave.

---

## 8. Was davon für einen Render-Knoten lehrreich ist

Kontext: Unser Pfad lautet Gebäudemodell → Tiefen- und Geometrie-Pässe → KI-Bild → Qualitätsprüfung.
Unten steht jeweils die Beobachtung bei Weave und die Folgerung für uns [A].

1. **Typisierte, farbige Ports mit Pflicht-Stern.** Weave färbt nach Datentyp und hat einen
   eigenen Typ «Mask» (Lime). Pflicht-Eingänge tragen einen Stern.
   → Unser Render-Knoten braucht eigene Typen statt «Bild für alles»: *Tiefe*, *Normalen*,
   *Kanten/Linien*, *Maske*, *Bild*. Der Tiefen-Eingang ist Pflicht (Stern). Dann kann eine
   Tiefenkarte nicht versehentlich als Farbreferenz angeschlossen werden. Weave kann das nicht
   unterscheiden: dort ist ein «Control Image» ein gewöhnliches grünes Bild.

2. **Herkunft der Struktur ausweisen.** Bei Weave ist Tiefe fast immer *geschätzt* (Z Depth
   Extractor aus Pixeln).
   → Unser Vorteil ist Tiefe *aus Geometrie*. Der Port oder das Etikett sollte das sichtbar
   machen, etwa «Tiefe · aus Modell» gegenüber «Tiefe · geschätzt». Das trägt später die
   Qualitätsprüfung: Ein Vergleich gegen geschätzte Tiefe prüft weniger als einer gegen
   gerechnete.

3. **Kosten vor dem Klick, live mit den Parametern.** Weave zeigt den Preis beim Überfahren, im
   Panel neben dem Modellnamen und als «Total cost = Runs × Preis» neben dem Run-Knopf. Der Preis
   ändert sich sofort mit Auflösung oder Dauer.
   → Unser Render-Knoten sollte vor dem Lauf den Aufwand nennen. Auf der HomeStation ist das
   Zeit statt Geld («≈ 40 s je Bild bei 1536 px»), bei einem Cloud-Pfad Geld. Mit der Zahl der
   Kameras und Varianten multipliziert sich das, wie bei «Runs».

4. **Nur Generatives hat einen Run-Knopf.** Deterministische Knoten (Crop, Levels, Masken)
   rechnen ohne Knopf und ohne Kosten.
   → Genau diese Trennung passt: Pass-Erzeugung aus dem Modell ist deterministisch und darf
   automatisch nachziehen. Der Render-Knoten ist explizit («Rendern») und teuer. Einen
   impliziten «alles neu rechnen»-Pfad sollte es für den Render-Knoten nicht geben.
   [A] Weave dokumentiert kein Caching. Gerade deshalb lohnt sich bei uns eine sichtbare Markierung
   «Eingänge seit letztem Lauf geändert».

5. **Ergebnisse stapeln statt überschreiben.** Jeder Lauf hängt ein Ergebnis an (Zähler «1 / 7»,
   Einzel- oder Galerieansicht). Es gibt «Remove current/others», «Unpack» in Einzelknoten und
   «Create Iterator» aus den Ergebnissen.
   → Der Render-Knoten hält seine Läufe als Stapel. Das gewählte Ergebnis geht weiter, der Rest
   bleibt vergleichbar. «Unpack» entspricht bei uns dem Ausspielen der Varianten an die QA.

6. **Herkunft pro Bild.** «Show info» in der Galerie zeigt Prompt, Parameter und Seed.
   → Bei uns gehört jedes Ergebnis mit seiner vollständigen Herkunft abgelegt: Modell und
   Gewichte (mit Lizenz), Seed, Hash der Tiefen- und Geometrie-Pässe, Kamera, Parameter und das
   QA-Ergebnis. Weave zeigt nur die Eingaben. Wir zeigen zusätzlich, *wie gut es passt*, mit
   Vorbehalt.

7. **Seed als «Zufall ☐ + Zahl», Parameter lassen sich auf die Leinwand heben.** «Set as Output»
   macht aus jedem Parameter einen eigenen Knoten. Der wird damit automatisch ein Eingabefeld
   im Tool-Modus.
   → Das ist ein eleganter Weg, zu bestimmen, was der Endnutzer sieht: kein separater
   Formular-Editor, sondern «was offen auf der Leinwand liegt, ist ein Feld». Das passt zu
   unserer Regel «Kern als Bibliothek»: Ein Tool ist ein Bibliotheksaufruf mit genau diesen
   offenen Argumenten.

8. **App-Modus mit Versionen.** Der Output-Knoten markiert das Ergebnis. Offene Wurzeln werden
   Felder, «Lock» blendet aus. «Update tool» veröffentlicht mit Zeitstempel. Der Nutzer sieht
   nie den halbfertigen Graphen.
   → Für die iPad-Oberfläche (Visbox) ist das das Vorbild: ein gebauter Render-Graph wird zu
   einem Werkzeug mit wenigen Feldern (Kamera, Stimmung, Tageszeit). Veröffentlichungen sind
   datiert, damit «was drüben läuft» und «was hier gebaut ist» getrennt bleiben. Das ist die
   gleiche Unterscheidung wie unser «gebaut, am Gerät unbestätigt».

9. **Begrenztes Vokabular per Dropdown.** Das Interior-Tool bietet Raumtypen und Kamerawinkel als
   Dropdown und keinen freien Prompt. Figma rät ausdrücklich dazu.
   → Der Render-Knoten sollte Stimmung, Tageszeit, Material-Stil und ähnliches als Listen führen
   (List-Selector-Muster). Freier Prompt bleibt die Ausnahme für Fortgeschrittene.

10. **Lizenz und Datenstatus im Modell-Picker.** Weave zeigt «Commercial Use» im Tooltip und
    «Verified by Figma» als Badge. Ungeprüfte Modelle verlangen vor dem Lauf eine Bestätigung,
    und mit ihnen darf nicht publiziert werden.
    → Für uns ist das Pflicht, nicht Kür (Regel 1): Jede Modell- oder Gewichtswahl im
    Render-Knoten trägt ihre Lizenz sichtbar. Nicht-kommerzielle Gewichte (FLUX.1-dev,
    FLUX.2-dev) sind **gar nicht wählbar**, nicht bloss markiert.
    Achtung beim Übernehmen von Weave-Modelllisten: Weave führt «Flux Dev LoRA» und «Flux 2 Dev
    LoRA» als Modelle. Für uns kommen sie nicht in Frage.

11. **Kamera sperren, dann generieren.** Beim Gaussian-Splat-Knoten sperrt ein Schloss Kamera-Modus,
    Sichtfeld und Bildmasse. Der Knoten gibt Welt *und* gerendertes Bild aus, und das Bild speist
    das KI-Modell.
    → Das ist fast unser Pfad, nur mit geschätzter statt gebauter Geometrie. Übernehmen lässt
    sich: eine Kamera, die im Knoten *sichtbar gesperrt* ist, und ein Knoten mit zwei Ausgängen
    (Pässe und Vorschau). Die Kamera kommt aber aus dem Gebäudemodell.

12. **Compare-Knoten für die Prüfung.** Slider und Toggle für zwei Bilder, und man wählt, welches
    weitergeht.
    → Für die Qualitätsprüfung ist das der naheliegende Blick: Render gegen Tiefenpass als Overlay
    oder Slider, Render gegen den vorherigen Lauf. Weave hat keine *gemessene* Prüfung; hier kann
    unser Knoten eigenständig werden, statt Weave zu verdoppeln.

13. **Iteratoren für Kameras × Varianten.** Weave rechnet Listen als getrennte Läufe mit Anzeige je
    Batch. Bei dynamischen Iteratoren gibt es keinen Preis im Voraus.
    → Mehrere Kameras eines Gebäudes sind bei uns der natürliche Iterator. Anders als bei Weave
    ist deren Zahl vorab bekannt, der Aufwand also **immer** angebbar. Das sollte man ausnutzen.

14. **Schwächen von Weave, die man nicht kopieren sollte:**
    - Fehler- und Fortschrittszustände im Knoten sind nicht dokumentiert.
    - Es gibt kein belegtes Caching.
    - Die Parameter stehen nur im Seitenpanel, der Knoten zeigt keinen Parameterzustand.
      Ob ein Seed fest ist, sieht man erst nach Anklicken.
    - Tiefe ist nur als Bild typisiert.

    → Unser Render-Knoten sollte im Knoten selbst mindestens drei Dinge zeigen: den Zustand
    (bereit / läuft / fehlgeschlagen / veraltet), ob der Seed fest ist, und die Herkunft der
    Struktur.

---

## Quellenverzeichnis (Auswahl, alle abgerufen am 24.09.2026)

- Figma Weave Knowledge Center (Intercom-Spiegel `intercom.help/figmaweave` inhaltsgleich):
  - Sammlung Knoten: https://help.weavy.ai/en/collections/15247921-nodes-and-models-documentations
  - Knoten-Grundlagen: …/articles/12292386, 12268346, 12268300, 12343281, 12268186, 12414117,
    12268282, 15887786, 16118602, 16554960, 14046860, 14047674, 16440592
  - Editor: 14688276, 14047607, 14655207, 12292356, 13560959, 14688389, 16110597, 12944804,
    12292543, 15495911, 14653652, 12292408, 12968045, 14654565, 14688070, 14688156,
    14878372, 15068263, 15263628
  - Tools/App-Modus und MCP: 12267755, 16202764, 15624624, 15623550
  - Modelle: 12284752, 12343904, 12344174, 12344205, 12344226, 12344285, 12344342, 12441548,
    12343888, 12344357, 14034721, 12265334, 11046940, 12343730
  - Credits und Pläne: 12267166, 12267070, 13751776, 12669991, 12670218, 16137383
- https://weave.figma.com/ und https://weave.figma.com/pricing
- https://www.figma.com/blog/welcome-weavy-to-figma/
- https://www.figma.com/blog/connecting-figma-and-weave/
- https://www.figma.com/blog/try-these-5-weave-tools-and-share-your-own/
- https://www.figma.com/blog/five-figma-weave-workflows/
- https://help.figma.com/hc/en-us/articles/35965787376919-Figma-Weave-FAQ
- https://help.figma.com/hc/en-us/articles/40779260614935-Use-Weave-tools-in-Figma
- https://help.figma.com/hc/en-us/articles/42847574436119 (Workflow lab)
- https://www.figma.com/solutions/3d-rendering-tool/, https://www.figma.com/solutions/camera-angle-generator/
- [S] https://blog.fal.ai/powering-creative-workflows-with-weavy-x-fal/
- [S] https://techcrunch.com/?p=3063533, https://note.com/momotaro_ai/n/nadf8304c32a1, https://note.com/onemorevision/n/nd6c1ad9a7381
