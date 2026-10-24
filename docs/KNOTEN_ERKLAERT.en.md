# The nodes of Visbox — what each one does and how they fit together

**Code state:** `3a76a247` (Visbox, version 0.3.51); the content matches the German sheet `docs/KNOTEN_ERKLAERT.md`
(written against 0.3.50 — the nodes have not changed since). Node view at version `366532904` (`HERKUNFT.json` in the
node view folder).
**Basis:** the node registry of the node view (`derive/visgraph.ts` in the core), the bodies of the nodes
(`modules/vis/*Knoten.tsx`, `NodeCanvas.tsx`), the host of the Mac app (`apps/visbox-knoten/src/`), the release
notes 0.3.0 to 0.3.50, `docs/PRODUKT_DIE_SCHRITTE.md`.

*Owner's request, 23.10.2026: “add individual explanations of the Visbox nodes to the board, one card per node to
explain its functions”. Owner's rule of 15.10.2026, confirmed on 23.10.2026 (decision 142): Visbox things in English.*
This sheet is the full English version; the explanation cards on the board (files `20261024-knoten-*`, group
“Visbox · What the nodes do”) are generated from it with `tools/knoten_tafel.py` (default `--sprache en`). The German
sheet `docs/KNOTEN_ERKLAERT.md` says the same, sentence for sentence.

**About names.** The Visbox interface shows German labels. Wherever a reader has to find a node, an input or a
button on screen, this sheet gives the English word first and the label as it appears on screen in brackets — for
example *Model (Modell)* or *Release (Freigeben)*. Names that are the same in both languages (Render, Prompt,
Material, Samples, Preset) stand alone.

Every statement here is read from the code; the source is named per section (paths inside the node view folder).
Where Visbox has a node only as a **placeholder** — the node is in the list but says honestly that it has no effect
here — this is stated explicitly instead of being left out.

---

## Overview

### What a node is and how to connect nodes

A **node** is a small box with one task. On the left it has its **inputs**, on the right its **outputs**. A **line**
always runs from an output to an input and says: “This input reads what that output delivers.” All the nodes of an
image together are called the **graph** (render graph). The node view of Visbox is the workspace in which an image is
ordered, compared and filed.

Three rules apply when connecting (`vis.verbinden`, `commands/vis.ts` in the core):

1. **Only the same kind fits.** A number output cannot be attached to an image input. Some inputs are stricter still:
   the five inputs of the Surface node (Oberfläche) accept only the Material node, the “Palette” input of the
   Material node accepts only the Colour palette (Farbpalette), and the “Skizze” (sketch) input of the Render node
   accepts only the Sketch from iPad (Skizze vom iPad).
2. **An input has exactly one line.** A new line on an occupied input replaces the old one. An output, on the other
   hand, may feed many inputs.
3. **Things only flow forwards.** A line that would close a circle is refused.

The **simple nodes** (Prompt, Mood, Surface, Material, Colour palette, Prompt combiner, Number) compute at once and
again on every change — the result is visible live at the node. **Render and Variants never compute by
themselves**: they put an order together, and computing starts only at the press of a button and after release.

### What is saved and what is not

The graph — which nodes, where they stand, their settings, the lines — is kept in the **project folder** (Mappe, the
project's folder on the Mac). Every change is a step that can be **undone**. Images and the state of a run
(“waiting”, “rendering”, “done”) are not in the graph but are files in the project folder; the Render node does,
however, remember its **latest image** and shows it again after the project folder is opened (since 0.3.44).

### What flows through the lines — six kinds, each with its own colour

| Kind | Colour | What it carries |
|---|---|---|
| **Scene** | blue | the 3D model that is rendered |
| **Prompt** | green | a text that describes how the image should look |
| **Material** | ochre | surfaces, colours and material phrases |
| **Number** | violet | a single value, e.g. geometry fidelity 0.8 |
| **Cameras** | petrol | a list of viewpoints |
| **Image** | rust red | a finished image (render, sketch, reference) |

### Four groups of nodes

The head of each node carries a narrow coloured stripe for its group. The group is for the eye only; it changes
nothing in the computing.

| Group | Nodes |
|---|---|
| **Source** — brings something into the graph | Model, Camera, Sketch from iPad, Material, Colour palette, Image reference, Viewport capture *(placeholder)*, Camera from 3D view *(placeholder)* |
| **Converter** — shapes text, surfaces and numbers | Mood, Prompt, Surface, Prompt combiner, Number |
| **Render** — orders images | Render, Variants |
| **Output** — shows or files | Image comparison, Onto the sheet *(placeholder)* |

Seventeen kinds of node are in the registry, and the list of the node view offers all seventeen. **Three of them are
placeholders in Visbox:** Viewport capture and Camera from 3D view need a 3D design view, which Visbox does not have;
Onto the sheet needs poster sheets, which do not exist in Visbox. All three say so at the node.

### The typical chain: from the model to the checked image

This is how Visbox lays out the **ready-made start** when a project folder has no graph yet (`start-graph.ts`), as
one undo step (labels as on screen):

```
Stimmung ──Prompt──┐
Prompt ────Prompt──┼──▶ Prompt-Kombinierer ──Prompt──┐
Material ─▶ Oberfläche ──Material──┘                 │
Modell ───────────────────────────Szene──────────────┼──▶ RENDER ──Bild──▶ Varianten ──Bilder──▶ Bildvergleich
Kamera ───────────────────────────Kameras────────────┘       ▲
                                     Skizze vom iPad ──Skizze┘   (optional)
```

In English: Mood and Prompt feed the Prompt combiner; Material feeds the Surface node, which also feeds the
combiner; the combiner, the Model and the Camera feed the Render node; the Render node feeds Variants, and Variants
feed Image comparison. Optionally a Sketch from iPad feeds the Render node.

Added as needed: a **Colour palette** in front of the Material node, a **Number** on “Geometrie-Treue” (geometry
fidelity) or “Samples”, an **Image reference** into Image comparison. Computing starts only on “Grundlage rendern”
(render base) or “Variante erzeugen” (make variant), and after “Freigeben” (release).

### The path of an image — two steps

1. **Render base (Grundlage rendern)** at the Render node: the home PC computes with Blender only — camera, geometry,
   the light of the mood, surfaces — and delivers per camera the **base image** and the helper images (depth, masks).
   No AI.
2. **Make variant (Variante erzeugen)**: the AI paints on this basis. Since decision 138 it **starts from the base
   image** (image input at strength 0.5): shape, windows and surface stay, the AI adds mood and life. A variant with
   different light or a different facade surface first computes a base image of its own.
3. **Release (Freigeben)**: in Visbox **every** order waits at “wartet auf Freigabe” (waiting for release). Only the
   architect's click sends it to the home PC. Neither the assistant nor Claude can release.
4. **The home PC computes**: the Mac app passes the order with the model on to the home PC; the collector there
   computes per camera the image and the **geometry check** (does the AI image fit the shape of the model?).
5. **Image and verdict come back**: the image goes into the project folder and to the node, with a verdict (“QA ok”,
   “QA ✗” or “nicht beurteilbar”, cannot be judged) and, for runs on the same base, with the **match check**
   (“deckungsgleich”, identical shape, or “Form weicht ab”, shape differs).

### Who else operates nodes

Bottom right is the **Lot** (plumb line), the sign of the assistant (on the home PC). The assistant and Claude (via
MCP, only on this Mac) can read, set, connect and adjust nodes — but only as a **suggestion on a card**: applying and
releasing stay with the architect.

---

## Sources

### 1 · Model (Modell)

*Source: registry `modell`; `ModellKnoten.tsx`; host `apps/visbox-knoten/src/mappe.ts` (loading).*

**What for.** Brings the building into the graph as a 3D scene — the starting point of every image.

**What you set.**
* **Load file … (Datei laden …)** — picks a model file (glb, gltf or IFC; the list is shown at the node) and puts it
  into the open project folder.
* **Other file … (Andere Datei …)** — replaces the loaded model with another; the project folder stays the same.
* **3D window** — shows the model that the render will receive; dragging turns it, a double-click enlarges it.
* **Status line** — “Szene: N Bauteile (aus IFC)” (scene: N building parts, from IFC) and the name of the project
  folder with its version.

**In and out.** No input. Output **Szene** (scene): the model as it goes to the home PC.

**What it triggers.** Loading shows a bar with the real progress; an IFC file is converted into a 3D model on the
home PC (roof, glass, windows, terrain are recognised; if something is missing, Visbox says so, e.g. “Kein Dach in
der Datei”, no roof in the file). Nothing is computed until the Render node orders.

**Typically connected.** Scene → Render, input “Szene” (required: without it the Render node orders nothing).

**Honest limit.** The file is read and converted on the home PC — without it nothing loads. What an IFC file lacks
(roof, colours, terrain), Visbox reports but does not add. An unreadable file ends with the home PC's sentence; the
previous model stays in place.

### 2 · Camera (Kamera)

*Source: registry `kamera`, `kameraAutoAusParams`, `KAMERA_AUTO_VORGABEN`; `KameraKnoten.tsx`; `heim-standpunkte.ts`;
`blick-quelle.ts`.*

**What for.** Decides where the house is seen from — a list of viewpoints.

**What you set.** Three tabs at the top:
* **Auto** (default for new nodes) — the home PC computes the viewpoints from the settings below:
  * **Directions (Richtungen)** — eight buttons N to NW; three are preset (south, south-east, north-west).
  * **Eye (Auge)** — eye height above the ground at the viewpoint, in metres (default 1.7).
  * **Focal length (Brennweite)** — 24, 35 or 50 mm (default 35); a smaller number means a wider view.
  * **Distance (Abstand)** — “füllt” (fills): the house fills this much of the image width (default 70 %); “fest”
    (fixed): distance in metres.
  * **Perspective (Perspektive)** — “Senkrecht” (upright): vertical edges stay vertical (the usual architectural
    perspective); “Frei” (free): the camera tilts towards the target.
  * **Manual (Manuell)** — freezes the computed viewpoints so they can be moved by hand.
* **View (Blick)** — picks a saved view or a viewpoint of the project folder as one fixed viewpoint; it is captured
  when picked and recognised by its ID, even if it is renamed.
* **Manual (Manuell)** — per viewpoint the **eye** and the **target** (where it looks) as east, north and height in
  metres; **Auto** leads back, and the values set by hand stay saved.
* **3D window and view** — at the top the model with one cone per camera, below it the view from one camera; a click
  on the view shows the next viewpoint. Both come from the same calculation as the render.

**In and out.** No input (the camera reads the model itself; a line from the model would only be decoration). Output
**Kamera-Standpunkte** (camera viewpoints).

**What it triggers.** With “Auto” the node asks the home PC for the viewpoints, live on every change; the order says
“automatic” with these settings. With “Manual” and “View” the fixed list goes into the order.

**Typically connected.** Camera viewpoints → Render, input “Kamera-Standpunkte”; Variants read the viewpoints through
the Render node.

**Honest limit.** Without the home PC, Auto shows no cones. The three fixed direction cameras are currently measured
from the underside of the floor slab (on the demo house about 1.3 m above the ground instead of 1.7 m); whether the
terrain becomes the reference is for the owner to decide after the demo. The “Eingang” (entrance) camera, which is
derived from a modelled house and computes its distance from the width and height of the house (since 0.3.46), does
not exist in Visbox: Visbox derives no viewpoints from building parts. This path does not order interior views.

### 3 · Sketch from iPad (Skizze vom iPad)

*Source: registry `skizzeIpad`; `SkizzeKnoten.tsx`; `skizze-quelle.ts`; `skizze-fuehrt.ts`; host `mappe.ts`.*

**What for.** Brings a sketch that was placed in the project folder on the iPad into the node view.

**What you set.**
* **Which sketch** — “neueste” (newest; by default automatically the one placed last) or an older one from the list
  of the project folder.
* **Thumbnail** — shows the sketch that applies.

**In and out.** No input. Output **Bild** (image): the sketch together with its note and the viewpoint of the image
it was drawn on.

**What it triggers.** At the “Skizze” (sketch) input of the Render node **the sketch leads the image**: the second
button then reads “Bild aus Skizze erzeugen” (make image from sketch), the sketch's note is the instruction, and the
image is made from the viewpoint of the image that was drawn on. On Variants, one image is made per mood, from this
viewpoint.

**Typically connected.** Image → Render, input “Skizze”; also → Image comparison.

**Honest limit.** The list is read when the node appears, when the selection is opened and when returning to the
window — not continuously. The “Vorschau” (preview) quality does not yet work for sketches. The iPad connects only
through the Mac.

### 4 · Material

*Source: registry `materialTextur`, `VIS_MATERIAL_BIBLIOTHEK`, `materialAusParams`; `OberflaecheKnoten.tsx`.*

**What for.** One surface from the library of eleven (fair-faced concrete sandblasted or smooth-formed, spruce,
brick, clinker, sandstone, rammed earth, plaster smooth or rough, timber battens, three-layer panel).

**What you set.**
* **Surface (Stoff)** — the choice from the library (default fair-faced concrete, sandblasted).
* **Preview (Vorschau)** — as a sphere, cube or flat panel.
* **Scale (Massstab)** — how large one tile of the texture is on the building part, in metres (default 1 m).
* **Rotation (Drehung)** — rotation of the texture on the building part, in degrees.
* **Relief** — how three-dimensional the surface looks, 0 to 1 (default 0.6).

**In and out.** Input **Palette** (only from the Colour palette): tints the surface. Output **Material**: surface,
scale, rotation, relief and tint.

**What it triggers.** Nothing by itself. At an input of the Surface node it becomes part of the order; on the home
PC that kind of building part gets the texture in Blender (colour, roughness, height), and the home PC names the
surface in the prompt.

**Typically connected.** Colour palette → Palette; Material → Surface (Oberfläche), input “Fassade” (facade), “Dach”
(roof), “Fenster” (window), “Boden” (floor) or “Übrige” (others).

**Honest limit.** The textures (free, CC0, from ambientCG) are stored only on the home PC; if one is missing, it
rejects the order with a sentence. The node alone has no effect — only at the Surface node.

### 5 · Colour palette (Farbpalette)

*Source: registry `farbpalette`, `paletteAusParams`, `farbWort`, `paletteSatz`; `OberflaecheKnoten.tsx`.*

**What for.** Holds up to four colours for the design.

**What you set.**
* **Colours** — up to four colour swatches; a plus adds one.
* **Tints with (Tönt mit)** — which of the colours tints the attached material (the lead colour).
* **Strength (Stärke)** — how strongly the tint works, 0 to 1 (default 0.4).

**In and out.** No input. Output **Palette** (kind Material).

**What it triggers.** On the home PC, Blender mixes the lead colour into the texture. All colours become a phrase of
colour words (“Farbpalette: Helles Beige, Schiefergrau …”, colour palette: light beige, slate grey …) that travels
through Surface and Prompt combiner into the prompt.

**Typically connected.** Palette → Material, input “Palette”.

**Honest limit.** The colour words are chosen roughly by hue and lightness; the AI reads words, not exact colour
values. Without a Material node in between, the palette goes nowhere.

### 6 · Image reference (Bild-Referenz)

*Source: registry `referenz`; `NodeCanvas.tsx` (`bildQuelle`, case `blatt`); `KuratierFlaeche.tsx`.*

**What for.** Holds a reference — an outside image for comparison or as a colour model.

**What you set.**
* **Image address** — a web address or an embedded image (data: address); the node shows the image.

**In and out.** No input. Output **Bild** (image).

**What it triggers.** Nothing on the home PC. In Image comparison the reference stands next to the renders; in the
curation view (full screen for choosing) it serves as the model for a colour match.

**Typically connected.** Image → Image comparison, Bild 1–3.

**Honest limit.** A reference does not go onto a sheet (“nur Vorbild”, reference only) — it is not an image of this
project. It does not steer the style of the AI image.

### 7 · Viewport capture (Viewport-Aufnahme) — a placeholder in Visbox

*Source: registry `aufnahme`; `NodeCanvas.tsx` (case `aufnahme`, `waehleAufnahme`).*

**What for.** Meant as a snapshot of the 3D design view — an image without rendering and without the home PC.

**What you set.**
* **Which capture** — “jüngste Aufnahme” (latest capture) or a named viewpoint.
* **Capture (Aufnehmen)** — only says where the real button is; the node itself captures nothing.

**In and out.** No input. Output **Bild** (image).

**What it triggers.** Nothing on the home PC.

**Typically connected.** Image → Image comparison.

**Honest limit.** Visbox has no 3D design view, so there is no capture: the node stays at “Noch keine Aufnahme” (no
capture yet). It is in the list so that graphs stay the same.

### 8 · Camera from 3D view (Kamera aus 3D-Ansicht) — a placeholder in Visbox

*Source: registry `kameraAus3d`; `derive/kamera-aus-3d.ts`; `KameraAus3dKnoten.tsx`.*

**What for.** Meant to take over the view of an open 3D view as a camera.

**What you set.**
* **Take over camera (Kamera übernehmen)** — reads eye, field of view and target of the 3D view and stores them in
  the node (not continuously).

**In and out.** No input. Output **Kamera-Standpunkte** (camera viewpoints).

**What it triggers.** At the Render node only its camera would go into the order; if it carries none, nothing is
ordered.

**Typically connected.** Camera viewpoints → Render.

**Honest limit.** Visbox has no 3D view. The node says “Keine 3D-Ansicht offen” (no 3D view open) instead of faking a
camera. For a fixed view, Visbox uses the **Camera** node with the “Blick” (view) tab.

---

## Converters

### 9 · Mood (Stimmung)

*Source: registry `stimmung`, `VIS_STIMMUNGEN`, `stimmungAusParams`; `StimmungKnoten.tsx`; on the home PC `stimmung.py`.*

**What for.** Chooses the light and mood of the image.

**What you set.**
* **Moods (Stimmungen)** — eight to tick: Morgenlicht (morning light), Mittag (midday), Abendstimmung (evening mood),
  Blaue Stunde (blue hour), Bedeckt (overcast), Nebel (fog), Winter, Weissmodell (white model); several at once means
  one image per mood (the first leads the Render node).
* **Preview (Vorschau)** — the sky image of the chosen mood.
* **Rotate (Drehen)** — off: the home PC places the sun to the side for each camera (raking light); on: the sky stays
  fixed at the set angle.
* **Acts on (Wirkt auf)** — “Licht + Satz” (light and phrase, default), only “Licht” (light: sky image in Blender) or
  only “Satz” (phrase: text for the AI).

**In and out.** No input. Output **Prompt**: the mood phrase, e.g. “Abendstimmung, warmes Licht, leuchtende
Fenster” (evening mood, warm light, glowing windows).

**What it triggers.** On the home PC the sky image (free, CC0) gives light, sun, shadows and reflections in Blender;
sky and ground up to the horizon match the mood (midday bright, evening dusky, never black). Each mood needs its own
base image; going back to the previous one brings back its base render.

**Typically connected.** Prompt → Prompt combiner, input “Stimmung” (mood).

**Honest limit.** “Satz” (phrase) alone does not change the light in Blender. A variant with another mood takes
longer, because Blender computes a new base image.

### 10 · Prompt

*Source: registry `prompt`; `NodeCanvas.tsx` (case `prompt`).*

**What for.** Free text that describes how the image should look — e.g. “Sichtbeton, Herbstlaub” (fair-faced
concrete, autumn leaves).

**What you set.**
* **Style text (Stil-Text)** — a text field; it is saved when you leave the field.

**In and out.** No input. Output **Prompt**: the text, word for word.

**What it triggers.** Nothing by itself; Prompt combiner and Render show the new text at once. If the text names a
different facade surface (e.g. “Sichtbeton”, fair-faced concrete), a variant computes its base image again with that
surface (since 0.3.43).

**Typically connected.** Prompt → Prompt combiner, input “Stil” (style), or directly Render, input “Prompt”.

**Honest limit.** German text is translated on the home PC; unusual words can get lost. An empty prompt with an AI
step is rejected — the button says so beforehand.

### 11 · Surface (Oberfläche)

*Source: registry `material` (called “Oberfläche” since decision 111), `oberflaecheMaterialien`, `VIS_BAUTEIL_ARTEN`;
`OberflaecheKnoten.tsx`; on the home PC `materialwahl.py`.*

**What for.** Gives each kind of building part a surface.

**What you set.**
* **Five inputs** — Fassade (facade), Dach (roof), Fenster (window), Boden (floor), Übrige (others); one Material
  node each. Doors count as “Übrige”.
* **Assignment** — one line says which kind has which surface; whatever gets nothing keeps the surface from the
  model.
* **… mehr (more)** — opens the material phrases that go to the Prompt combiner.

**In and out.** Five **Material** inputs (only from the Material node). Output **Material**: the assignment and the
phrases (e.g. the phrase of a colour palette).

**What it triggers.** The Render node orders the surfaces per kind of building part; on the home PC Blender applies
the textures, and the base image already shows them.

**Typically connected.** Material → Fassade (etc.); output → Prompt combiner, input “Material”.

**Honest limit.** Which parts are “Fassade” or “Dach”, the home PC reads from the file; parts without a kind keep
their surface. Wall layers as phrases do not exist in a Visbox project folder.

### 12 · Prompt combiner (Prompt-Kombinierer)

*Source: registry `kombinierer`; `renderprompt.ts` (`finalerRenderPrompt`).*

**What for.** Joins mood, style and material into the text that really goes to the AI.

**What you set.**
* **Nothing** — it shows the finished prompt live; **… mehr** (more) opens it in full.

**In and out.** Inputs **Stimmung** (mood, Prompt), **Stil** (style, Prompt), **Material** (Material). Output
**Finaler Prompt** (final prompt).

**What it triggers.** Nothing by itself. If the text changes, a finished image at the Render node is marked
“veraltet” (out of date).

**Typically connected.** Mood → Stimmung, Prompt → Stil, Surface → Material; output → Render, input “Prompt”.

**Honest limit.** It only strings the parts together (with commas; empty parts drop out); it does not resolve
contradictions between mood and style.

### 13 · Number (Zahl)

*Source: registry `zahl`; `NodeCanvas.tsx` (case `zahl`); `vis-jobs.ts`.*

**What for.** A slider for one single value.

**What you set.**
* **Slider** — default 0.8, from 0 to 1 in steps of 0.05; the value applies on release.

**In and out.** No input. Output **Wert** (value).

**What it triggers.** At the Render node it becomes the **geometry fidelity** (Geometrie-Treue: how closely the AI
follows the shape of the model) or the **samples** (computing steps per pixel in Blender).

**Typically connected.** Value → Render, input “Geometrie-Treue” or “Samples”.

**Honest limit.** If “Qualität gegen Zeit” (quality versus time) is chosen on the Render node, it applies instead of
the number on “Samples”. For samples the range 0 to 1 is too small — there the minimum and maximum would have to be
changed.

---

## Render

### 14 · Render

*Source: registry `render`; `NodeCanvas.tsx` (case `render`, `RenderBedienung`, `GueteSchalter`,
`RenderAuftragsFormular`); `grundlage.ts`; `guete.ts`; `nebeneinander.ts`; `vis-jobs.ts`; `RenderVerlauf.tsx`.*

**What for.** The node that orders images from the home PC — only at the press of a button, never automatically.

**What you set.**
* **Preset** — a ready package (quick draft, presentation, night, interior) or none (128 samples).
* **Resolution (Auflösung)** — 1600 × 1000 (default) up to 4000 × 2667 pixels.
* **Quality versus time (Qualität gegen Zeit)** — quick, medium, high or full; takes priority over the number on
  “Samples”.
* **Sky (Himmel)** — one of Blender's sky types, or none.
* **Rotate environment (Umgebung drehen)** — turns the sky in degrees (only with a sky).
* **Image tool (Bildwerkzeug)** — which AI model paints (default Z-Image Turbo); models with an open licence are
  marked.
* **Render base (Grundlage rendern)** — step 1: Blender only (camera, geometry, light, surfaces), no AI.
* **Make variant (Variante erzeugen)** — step 2: the AI paints on the base, starting from the base image; locked
  until a current base render exists. With a sketch the button reads **Bild aus Skizze erzeugen** (make image from
  sketch).
* **Release (Freigeben)** — appears at “wartet auf Freigabe” (waiting for release); only this click sends the order
  to the home PC.
* **Cancel (Abbrechen)** — stops a running order.
* **Base line (Grundlage)** — ID and number of cameras of the base render, or “veraltet” (out of date) or “noch
  keine” (none yet).
* **Seed (Startwert) · reroll (neu würfeln)** — the random number the AI starts from; “neu würfeln” gives another.
* **Quality (Güte): Vorschau | Voll** — the quality of “Variante erzeugen” (make variant). **Voll (full) is the
  default** (decision 143): large with the chosen image tool, starting from the base image (image input 0.5), about
  33–45 s per image. Vorschau (preview) is quicker (about 26–36 s) and small (always Z-Image Turbo, without the base
  image) — windows and shape are not secured there; the image carries the mark “Vorschau”.
* **Line drawing (Strichzeichnung)** — orders the image as a line drawing, without AI.
* **… mehr (more)** — opens the order form next to the node (facade, scene, season, people, free text) and the
  explanations.
* **Image at the node** — AI image and base image side by side, only AI or only base image; a click opens the large
  view with **Exportieren** (export) at full resolution.

**In and out.** Inputs **Szene** (scene, required), **Prompt**, **Geometrie-Treue** (geometry fidelity) and
**Samples** (numbers), **Kamera-Standpunkte** (camera viewpoints), **Skizze** (sketch, only from the Sketch from
iPad). Output **Bild** (image).

**What it triggers.** Every order waits for “Freigeben” (release); then the home PC computes per camera — Blender for
the base image, the AI starting from the base image (image input 0.5, decision 138), then the geometry check. Image
and verdict come back to the node and into the project folder; the node remembers its latest image. Runs on the same
base can be compared side by side in the large view, with “deckungsgleich” (identical shape) or “Form weicht ab”
(shape differs).

**Typically connected.** Model → Szene, Prompt combiner → Prompt, Camera → Kamera-Standpunkte, Sketch from iPad →
Skizze; output → Variants or Image comparison.

**Honest limit.** Without the home PC nothing is computed (the node says so in one sentence). The preview does not
yet start from the base image and can therefore look different from the full variant (on the test house it painted
over a band of windows) — it is only ever chosen, never applied by itself. Models with an open licence
paint freely (without a base image) and carry “Lizenz offen — nicht für Wettbewerb oder Veröffentlichung” (licence
open — not for competitions or publication). This path does not order interior views.

### 15 · Variants (Varianten)

*Source: registry `varianten`; `derive/varianten.ts`; `VariantenKnoten.tsx`; `VariantenDaumen.tsx`; `varianten.ts`.*

**What for.** Orders the Render node's settings in every combination of viewpoints, moods and designs — with one
click.

**What you set.**
* **Counter** — says beforehand how many images there will be (viewpoints × moods × designs).
* **Viewpoints (Standpunkte)** — in Visbox the directions of the camera are combined; with a sketch, the viewpoint of
  the sketch.
* **Moods (Stimmungen)** — the eight to tick (default evening).
* **Designs (Entwürfe)** — which model; in Visbox the current one.
* **Warning** — from twelve images on, with an estimated duration, without a limit.
* **Thumbnails** — one preview per variant with mood and viewpoint; browse, enlarge, pick one.
* **Order N images (N Bilder bestellen)** and **Release all (Alle freigeben)** — two clicks for the whole series.

**In and out.** Input **Render** (Image): the Render node whose settings apply. Output **Bilder** (images).

**What it triggers.** One order per mood and design, with all viewpoints, on the home PC — only after “Alle
freigeben” (release all). It computes in full quality, starting from the base image (decision 143); a preview happens
here only if it is set explicitly on the node (through the assistant — the node has no switch for it). If the Render node's base image fits, the variant uses it (also when only some of its
cameras are chosen); another mood gets its own base image.

**Typically connected.** Render → Render; Bilder → Image comparison, Bild 1 (shown there as a grid).

**Honest limit.** The time estimate is an assumption, not a measurement. Variants with an open licence do not start
from the base image. Two surface variants with the same surface compute the base image twice.

---

## Output

### 16 · Image comparison (Bildvergleich)

*Source: registry `vergleich`; `NodeCanvas.tsx` (case `vergleich`, `BildKachel`); `VariantenRaster.tsx`;
`varianten-diff.ts`.*

**What for.** Puts images side by side, each with its check verdict.

**What you set.**
* **Nothing** — a click on an image enlarges it; the large view stays inside the window when zooming.

**In and out.** Inputs **Bild 1**, **Bild 2**, **Bild 3** (image 1–3). No output.

**What it triggers.** Nothing — it only shows. Each image carries “QA ok”, “QA ✗”, “nicht beurteilbar” (cannot be
judged) or “without QA” (a pure base image; on the tile “QA nicht gemessen”, not measured), with the reason and,
where needed, “Vorschau” (preview) and “Lizenz offen” (licence open). If Variants are attached, it shows their images
as a **grid**: rows are viewpoints, columns are moods.

**Typically connected.** Variants → Bild 1; Render, Sketch from iPad or Image reference → Bild 1–3.

**Honest limit.** At most three single images; more only as a grid through Variants. Choosing and exporting happen in
the large view or in the curation view.

### 17 · Onto the sheet (Aufs Blatt) — a placeholder in Visbox

*Source: registry `blatt`; `NodeCanvas.tsx` (case `blatt`); placeholder `commands/publish.ts` in the core.*

**What for.** Meant to place an image on a poster sheet.

**What you set.**
* **Title (Titel)** — the name on the sheet (default “Visualisierung”, visualisation).
* **Onto the sheet (Aufs Blatt)** — active only when a finished image is attached; takes the newest finished image
  and says so if it is not the latest.

**In and out.** Input **Bild** (image). No output.

**What it triggers.** In Visbox the click ends with a sentence saying there are no sheets here.

**Typically connected.** Render → Bild.

**Honest limit.** Poster sheets do not exist in Visbox. To keep an image, use **Exportieren** (export) in the large
view (full resolution, file name with the name of the project folder). An image reference does not go onto a sheet.

---

## What is not clear-cut in the code

* **Number on “Samples”.** The slider runs from 0 to 1 and so fits the geometry fidelity, not samples (computing
  steps, e.g. 128). Anyone attaching it to “Samples” has to change minimum and maximum at the node — the interface has
  no field for that. The reliable way is “Qualität gegen Zeit” (quality versus time).
* **Camera kind “Modell”.** The registry knows a fourth kind (viewpoints from the modelled house, e.g. “Eingang”,
  entrance). The tab appears only when the model supplies such viewpoints — in Visbox never, because Visbox derives
  no viewpoints from building parts. An old graph without a kind still stands on this kind and then shows an empty
  list until one switches to “Auto”.
