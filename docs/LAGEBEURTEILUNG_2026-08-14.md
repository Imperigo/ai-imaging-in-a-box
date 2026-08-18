# Lagebeurteilung · offene Bausteine für „AI Imaging in a Box"

**Stand:** 2026-08-14 · **Auftrag:** ehrliche Bestandsaufnahme, ausdrücklich **kein Bau**
**Prüfraster:** die vier Regeln aus `CLAUDE.md`

---

## 0 · Was ich vorgefunden habe (bevor irgendetwas anderes gilt)

Drei Befunde vorweg, weil sie die Ausgangslage des Auftrags korrigieren:

1. **Es gab keine `CLAUDE.md`.** Das Repo `Imperigo/ai-imaging-in-a-box` enthielt zum
   Zeitpunkt dieses Auftrags genau eine Datei: eine zweizeilige `README.md`
   (Commit `d0e2f15`, „Initial commit"). Die vier Regeln existierten nur im Auftragstext.
   Ich habe sie in `CLAUDE.md` schriftlich fixiert — falls anderswo eine ältere Fassung
   liegt, hat diese Vorrang.
2. **Es gab kein `LICENSE`.** Das Repo ist öffentlich und wird als Apache-2.0 geführt,
   trug aber keinen Lizenztext. Ohne `LICENSE` ist ein öffentliches Repo rechtlich
   „all rights reserved" — die Aussage „steht unter Apache-2.0" war unbelegt. Ich habe
   den kanonischen Apache-2.0-Text mit Copyright-Zeile eingesetzt.
3. **Es gibt einen sehr substanziellen Vorläufer.** `Imperigo/KosmoVis` (privat, geklont
   und gelesen) enthält ~38 000 LOC Erstanbieter-Code und einen ETH-Projektbericht vom
   2026-06-30, der viele der hier gestellten Fragen bereits beantwortet. Ich habe diesen
   Bericht **nicht** übernommen, sondern als Hypothese behandelt und die Lizenzfragen neu
   geprüft. An drei Stellen korrigiere ich ihn (Kap. 8).

Diese drei Punkte sind die einzigen Dateiänderungen dieses Auftrags. Es wurde nichts gebaut.

---

## 1 · Knotenbasierte Bildketten

### Was es gibt

| Baustein | Lizenz | Geprüft | Urteil gegen Regel 1 |
|---|---|---|---|
| **ComfyUI** (Comfy-Org) | **GPL-3.0** | ✅ LICENSE-Datei | ⛔ **GPL-Fund** |
| **Fooocus** (lllyasviel) | **GPL-3.0** | ⚠️ nur Sekundärquelle | ⛔ **GPL-Fund** |
| InvokeAI | Apache-2.0 | ⚠️ nur Sekundärquelle | ✅ zulässig |
| SwarmUI | MIT — *über GPL-Backend* | ⚠️ nur Sekundärquelle | ⚠️ siehe unten |
| **Krita AI Diffusion** | **GPL-3.0** | ✅ LICENSE-Datei gelesen **(18.08.2026)** | ⛔ **GPL-Fund** |
| **litegraph.js** (Graph-Engine) | **MIT** | ✅ LICENSE-Datei gelesen | ✅ zulässig |
| **React Flow / xyflow** | **MIT** | ✅ | ✅ zulässig |
| Ryven (Python-Node-Editor) | MIT | ⚠️ nur Sekundärquelle | ✅ zulässig |
| NodeGraphQt | MIT (angenommen) | ❌ **nicht geprüft** | offen |

### Die zentrale Erkenntnis

**ComfyUI ist GPL-3.0 — und damit als Kern ausgeschlossen.** Das ist der wichtigste
einzelne Befund dieser Lagebeurteilung, weil ComfyUI faktisch das De-facto-Backend des
gesamten Ökosystems ist: InvokeAI, SwarmUI, Krita AI Diffusion, sämtliche Blender-Brücken
sind ComfyUI oder umhüllen es.

Der MIT-Schild von SwarmUI **löst das Problem nicht**, er verschiebt es nur:
MIT-lizenziert ist dort die eigene Schale, das ausgelieferte Gesamtpaket enthält weiterhin
GPL-Code. Wer dieses Muster kopiert, liefert ein GPL-Produkt aus und nennt es MIT. Für ein
Repo, das ausdrücklich Apache-2.0 sein soll, ist das kein gangbarer Weg.

> ### ⛔ BERICHTIGUNG 18.08.2026 — Krita AI Diffusion ist nicht MIT, sondern GPL-3.0
>
> Diese Zeile stand hier seit dem 14.08. als „MIT — über GPL-Backend", also als Fall
> derselben Sorte wie SwarmUI: eigene Schale permissiv, Problem nur im Unterbau. **Das
> ist falsch.** Die Lizenzprüfung vom 18.08. hat die `LICENSE`-Datei im Vorgabezweig
> abgerufen — sie ist der **GPLv3-Volltext**, 674 Zeilen:
> `https://raw.githubusercontent.com/Acly/krita-ai-diffusion/main/LICENSE`
>
> **Regel 1 verlangt, GPL-Funde ausdrücklich als solche zu melden. Hiermit geschehen.**
>
> Praktische Folge: keine. Krita AI Diffusion liegt in keinem Pfad dieses Projekts, weder
> als Abhängigkeit noch als Vorbild.
>
> Die eigentliche Folge ist eine über die Arbeitsweise: **Die Sekundärquelle lag in die
> gefährliche Richtung falsch.** Sie meldete permissiv, wo Copyleft steht — nicht
> umgekehrt. Ein Fehler in diese Richtung fällt nie von selbst auf, weil er niemanden
> stört; er wird erst teuer, wenn ausgeliefert wird. Genau dafür steht in `CLAUDE.md`
> „gegen die LICENSE-Datei, nicht gegen eine Suchmaschine", und genau darum ist die
> Wissensschuld „Lizenzen nur aus Sekundärquellen" keine Formalie gewesen.
>
> Voller Prüfbericht: `docs/LIZENZPRUEFUNG_2026-08-18.md`.

Bemerkenswert und nützlich: **litegraph.js — die Graph-Engine, auf der ComfyUIs Oberfläche
aufsetzt — ist MIT.** Die Knotendarstellung ist also frei verfügbar; GPL ist ausschliesslich
ComfyUIs Ausführungs-Backend und Node-Bibliothek.

**Nebenbefund zur Reife:** InvokeAI (die einzige Apache-2.0-Alternative mit Node-Editor)
hat im Oktober 2025 Teile seines Teams an Adobe verloren. Ich werte das als Wartungsrisiko,
nicht als Ausschlusskriterium — aber es entwertet die naheliegende Antwort „dann eben
InvokeAI forken" spürbar.

### Wo der Prototyp eigenständig werden muss

**Hier — und zwar unvermeidbar.** Regel 1 und Regel 4 zwingen gemeinsam zu einem eigenen
Graph-Kern. Das ist keine Doppelung von ComfyUI, sondern die Konsequenz daraus, dass
ComfyUIs Lizenz das Produkt vergiften würde.

Der Umfang ist deutlich kleiner, als es zunächst wirkt, wenn man die Grenze richtig zieht:

- **Selbst bauen:** ein typisierter DAG, Topologie-Sortierung, Artefakt-Cache mit
  Content-Hashing, serialisierbares Graph-Format. Das sind Hunderte, nicht Zehntausende
  Zeilen — und es ist genau der Teil, den Regel 4 als Bibliothek verlangt.
- **Nicht selbst bauen:** die eigentliche Bildarbeit. Jeder Knoten ruft `diffusers`
  (Apache-2.0) auf. ComfyUIs Wert liegt in seinem Knoten-Zoo, nicht in seinem Scheduler —
  und diesen Zoo braucht ein architektur-spezifisches Werkzeug nicht.
- **Für die Oberfläche:** litegraph.js (MIT) oder xyflow (MIT) — beide erlauben die
  vertraute Knotendarstellung ohne jeden GPL-Kontakt.

---

## 2 · IFC lesen

### Was es gibt

| Baustein | Lizenz | Geprüft | Urteil gegen Regel 1 |
|---|---|---|---|
| **IfcOpenShell** (Python) | **LGPL-3.0-or-later** | ✅ | ⚠️ **Grenzfall — Entscheidung nötig** |
| **Bonsai** (ehem. BlenderBIM) | **GPL-3.0-or-later** | ✅ | ⛔ **GPL-Fund** |
| **web-ifc** (ThatOpen) | **MPL-2.0** | ✅ LICENSE.md | ✅ zulässig |
| **IFC++ / IfcPlusPlus** (ifcquery) | **MIT** | ✅ | ✅ zulässig |
| xbim Toolkit (.NET) | CDDL-1.0 | ❌ **nicht geprüft** | offen, .NET-Fremdkörper |

### Die zentrale Erkenntnis

**IfcOpenShell ist LGPL-3.0-or-later** — und damit der eine Baustein, bei dem Regel 1
buchstäblich nicht ausreicht. LGPL ist weder permissiv noch GPL/AGPL; die Regel schweigt
zu diesem Fall. Das ist keine Spitzfindigkeit, denn IfcOpenShell ist praktisch konkurrenzlos:
Es ist die einzige ausgereifte IFC-**Geometrie**-Engine mit Python-Bindings.

Die permissiven Alternativen lösen es nur halb:
- **web-ifc (MPL-2.0)** ist lizenzrechtlich sauber und schnell, aber C++/WASM mit
  JavaScript-Bindings — für einen Python-Kern ein Fremdkörper.
- **IFC++ (MIT)** ist lizenzrechtlich ideal, aber C++ ohne Python-Bindings und mit
  merklich kleinerer Reichweite bei IFC4-Deckung.

### ⛔ Nachtrag 2026-08-14: Das IfcOpenShell-Wheel enthält GPL-Code (verifiziert)

Der zunächst offene CGAL-Verdacht ist geklärt — und er bestätigt sich. Ich habe
`ifcopenshell` 0.8.5 aus PyPI installiert und das mitgelieferte Binary untersucht:

```
_ifcopenshell_wrapper.cpython-311-x86_64-linux-gnu.so   148 MB
  Nef_polyhedron_3           249 Symbolverweise
  Polygon_mesh_processing     47
  convex_decomposition         8
  + Open CASCADE
```

**Beide Geometrie-Kernel sind statisch einkompiliert**, nicht nur Open CASCADE. Und CGAL
ist dual lizenziert: Die Grundschicht steht unter LGPL, **die höheren Pakete unter GPL-3.0**.
`Nef_polyhedron_3` — mit 249 Verweisen der am stärksten genutzte CGAL-Teil, zuständig für
die booleschen Verschneidungen, aus denen IFC-Geometrie überhaupt erst entsteht — ist
eines dieser GPL-Pakete. `Polygon_mesh_processing` ebenfalls.

**Damit ist `import ifcopenshell` im Produkt-venv nicht mehr nur eine LGPL-Frage, sondern
ein echter GPL-Fund.** Wer diese Bibliothek in den eigenen Prozess holt, macht sein
Produkt GPL.

Das ändert nichts an der Empfehlung — es verschärft sie nur von Hygiene zu Notwendigkeit:

- **Die Prozessgrenze ist nicht optional.** IfcOpenShell läuft als eigenes Programm im
  eigenen venv, exakt wie Blender, und wird im `NOTICE` als GPL-Komponente deklariert.
- **Zwei Auswege, falls die Prozessgrenze irgendwann stört:** IfcOpenShell selbst ohne
  CGAL-Kernel bauen (nur Open CASCADE → reines LGPL, erfordert Kompilieren), oder auf
  **web-ifc (MPL-2.0)** bzw. **IFC++ (MIT)** wechseln.
- **Lehre für alles Weitere:** Ein fertiges Wheel verbirgt, was einkompiliert ist. Die
  Lizenzangabe des PyPI-Pakets sagt nichts über die statisch eingebundenen Bibliotheken.
  Für jede weitere Abhängigkeit mit grossem Binäranteil gilt dieselbe Prüfpflicht.

### Empfehlung

**Dieselbe Prozessgrenze wie bei Blender ziehen.** Regel 2 hat für Blender bereits die
richtige Antwort gefunden; sie trägt hier genauso: IfcOpenShell läuft in einem **eigenen
venv als Subprozess**, die Kommunikation ist eine Datei (glb) plus ein JSON-Report. Kein
`import ifcopenshell` im Produkt-venv.

Damit ist die LGPL-Auflage der Ersetzbarkeit trivial erfüllt, das Produkt bleibt Apache-2.0,
und ein späterer Wechsel auf web-ifc oder IFC++ wird zum Austausch eines Subprozesses statt
zu einer Umschreibung. **KosmoVis fährt dieses Muster bereits** (`.venv-ifc/bin/python
ifc_to_glb.py`) — es ist erprobt, nicht theoretisch.

### Wo der Prototyp eigenständig werden muss

Nicht beim Parsen — das wäre reine Doppelung. Wohl aber bei zwei Dingen, die kein
IFC-Werkzeug liefert, weil sie erst durch die Bildkette entstehen:

- **Der Massstabs- und Georeferenz-Torwächter.** IFC-Exporte kommen fehlskaliert
  (mm-als-m ×1000) oder LV95/UTM-verortet an. Letzteres bricht glTF, weil glTF Positionen
  als float32 speichert: bei Ostwert 2.6 · 10⁶ m liegt die Quantisierung bei ~0.3 m.
  Beides muss **vor** dem teuren GPU-Render abgefangen werden, nicht danach.
- **Der Vertrag IFC → Render-Szene.** Was eine Bildkette braucht (gemeshte Geometrie,
  Y-up, Meter, zentriert), ist nicht das, was ein IFC-Reader liefert.

---

## 3 · Blender/Cycles ansteuern

### Was es gibt

| Baustein | Lizenz | Geprüft | Urteil gegen Regel 2 |
|---|---|---|---|
| **Blender** (Quellcode) | **GPL-2.0-or-later** | ✅ | ⛔ nur als externer Prozess |
| **Blender** (Binär-Releases) | **GPL-3.0-or-later** | ✅ | ⛔ nur als externer Prozess |
| **`bpy` PyPI-Wheel** | **GPL-3.0** | ✅ | ⛔ **durch Regel 2 explizit verboten** |
| **Cycles standalone** | **Apache-2.0** | ✅ | ✅ lizenzrechtlich ideal |
| StableGen | GPL-3.0 | ⚠️ Sekundärquelle | ⛔ **GPL-Fund** |
| ComfyUI-BlenderAI-node | GPL-3.0 | ⚠️ Sekundärquelle | ⛔ **GPL-Fund** |
| alexisrolland/ComfyUI-Blender | GPL-3.0 | ⚠️ Sekundärquelle | ⛔ **GPL-Fund** |
| Dream Textures | GPL-3.0 | ⚠️ Sekundärquelle | ⛔ **GPL-Fund** |
| Shaamallow/texture-diffusion | AGPL-3.0 | ⚠️ Sekundärquelle | ⛔ **AGPL-Fund** |
| AI Render (benrugg) | MIT | ⚠️ Sekundärquelle | ✅ (aber Add-on-Muster) |

**Sämtliche existierenden Blender-KI-Brücken sind GPL oder AGPL** — und alle sind Add-ons.
Regel 2 schliesst sie doppelt aus: über die Lizenz und über die Bauform. Das ist kein
Zufall: Wer ein Blender-Add-on schreibt, *muss* GPL sein. Genau deshalb existiert Regel 2.

### Die Cycles-Falle

Cycles standalone ist **Apache-2.0** — die Lizenz wurde 2013 bewusst von GPL gelöst, damit
Cycles in kommerzielle Pipelines eingebunden werden kann. Das klingt nach der perfekten
Antwort auf Regel 2: reiner Renderer, permissiv, kein GPL-Kontakt.

**Es ist trotzdem die falsche Wahl**, und zwar aus rein technischen Gründen. Die
Blender-Entwicklerdokumentation bezeichnet die Standalone-Anwendung selbst als „work in
progress, not ready for production usage"; vorkompilierte Binaries existieren nicht. Vor
allem aber liefert Cycles allein **nichts** von dem, was eine geometrie-treue Bildkette
tatsächlich braucht: keinen glTF-Import, keinen Compositor (und damit keinen echten
Z-Depth-Pass), kein Material-Override pro View-Layer, keine Shader-Graphen, keine
Farbraum-Verwaltung.

Der Weg über Cycles standalone hiesse, die halbe Pipeline auf einer instabilen XML-API neu
zu bauen, um eine Lizenzfrage zu lösen, die Regel 2 **bereits gelöst hat**.

### Empfehlung

**Volles Blender headless als Subprozess** — `blender --background --python stage.py`.
GPL-rechtlich ist das eine Aggregation, keine Ableitung: Blender bleibt GPL, der eigene
Pipeline-Code bleibt Apache-2.0. Das gebündelte Binary wird im `NOTICE` als GPL-Komponente
deklariert. Genau das schreibt Regel 2 vor; sie ist gut begründet.

Die harte Grenze, die dabei nie fallen darf: **kein `import bpy` im Produkt-venv.** Das
`bpy`-Wheel ist mit ~391 MB ohnehin praktisch das ganze Blender — der vermeintliche
Footprint-Vorteil ist bei nahe null, das Linking-Risiko dagegen real.

### Wo der Prototyp eigenständig werden muss

Das Skript **innerhalb** des Blender-Prozesses ist Eigenbau — es gibt nichts zu übernehmen,
weil alles Existierende Add-ons sind. Konkret: glTF-Import, automatische Kameraableitung
aus der Baukörper-Bounding-Box, und der Multipass (Beauty, Material-ID, Depth). Der
Depth-Pass ist die anspruchsvollste Stelle, weil `use_pass_z` über den Compositor als
32-bit-EXR geführt und dann auf 16-bit-Graustufen mit der ControlNet-Konvention
(nah = hell) normalisiert werden muss.

---

## 4 · Lokale Bildmodelle mit LoRA-Training

### Modellgewichte

| Modell | Grösse | Lizenz | Geprüft | Urteil |
|---|---|---|---|---|
| **Qwen-Image-Edit-2511** | 20B | **Apache-2.0** | ✅ Modellkarte | ✅ **empfohlener Default** |
| **Qwen-Image-2512** | 20B | Apache-2.0 | ⚠️ Sekundärquelle | ✅ zulässig |
| **Z-Image-Base / -Turbo** | 6B | Apache-2.0 | ⚠️ Sekundärquelle | ✅ Effizienz-Pfad |
| **FLUX.2 klein-4B** | 4B | Apache-2.0 | ⚠️ Sekundärquelle | ✅ (kein ControlNet-Depth) |
| SD3.5 Large | 8B | Stability Community | ❌ **nicht geprüft** | ⚠️ Umsatzschwelle |
| SDXL / Juggernaut XL | — | OpenRAIL++-M | ❌ **nicht geprüft** | ⚠️ Nutzungsauflagen |
| **FLUX.1-dev / FLUX.2-dev** | 12B / 32B | **Non-Commercial** | ⚠️ Sekundärquelle | ⛔ **ausgeschlossen** |
| HunyuanImage 3.0 | 80B+ | Community, EU ausgeschlossen | ⚠️ Sekundärquelle | ⛔ ausgeschlossen |

**Die Lage ist günstig.** Die 2026er-Landschaft hat sich klar zugunsten Apache-lizenzierter
Open-Weight-Modelle gedreht. Der Verzicht auf FLUX-dev kostet heute kaum noch Qualität —
das ist ein echter Unterschied zur Situation vor einem Jahr.

**Wichtig für abgeleitete Gewichte:** FLUX.1-dev ist nicht nur non-commercial, es untersagt
auch das Trainieren konkurrierender Modelle. Das erstreckt sich auf LoRAs, die darauf
trainiert wurden. Ein verkaufbarer Stil-Moat **muss** auf Qwen-Image oder Z-Image aufsetzen.

### Trainings-Werkzeuge

| Werkzeug | Lizenz | Geprüft | Urteil |
|---|---|---|---|
| **kohya-ss/sd-scripts** | **Apache-2.0** | ⚠️ Sekundärquelle | ✅ zulässig |
| **ostris/ai-toolkit** | **MIT** | ⚠️ Sekundärquelle | ✅ zulässig |
| **DiffSynth-Studio** | **Apache-2.0** | ✅ (LICENSE in KosmoVis-Doku zitiert) | ✅ zulässig |
| **diffusers / transformers / peft** | **Apache-2.0** | ⚠️ Sekundärquelle | ✅ Fundament |
| **OneTrainer** | **AGPL-3.0** | ✅ | ⛔ **AGPL-Fund — meiden** |
| **SimpleTuner** | **AGPL-3.0** | ✅ Repo-Sidebar | ⛔ **AGPL-Fund — meiden** |
| musubi-tuner | Apache-2.0 (angenommen) | ❌ **nicht geprüft** | offen |

Zwei AGPL-Funde unter den populärsten LoRA-Trainern. AGPL ist für eine kommerzielle Pipeline
besonders heikel, weil das Netzwerk-Copyleft auch dann greift, wenn nichts ausgeliefert,
sondern nur als Dienst betrieben wird. **Beide meiden** — die permissiven Alternativen
(kohya, ai-toolkit, DiffSynth) decken denselben Bedarf ab.

### Wo der Prototyp eigenständig werden muss

**Fast nirgends — und das ist die gute Nachricht.** Diffusion-Inferenz und LoRA-Training
sind gelöste, gut lizenzierte Probleme. Sie zu duplizieren wäre reine Verschwendung:
`diffusers` für Inferenz, kohya oder ai-toolkit als Trainings-Subprozess.

Eigenständig werden muss nur die **Schnittstelle**, über die Modelle austauschbar werden.
Der entscheidende Entwurfsgedanke: **nicht das Modell ist der Vertrag, sondern die
Konditionierung.** Wenn jeder Backbone über dieselbe Depth-ControlNet-Naht angesprochen
wird, ist der Modellwechsel ein Registry-Eintrag statt eines Umbaus.

Diese Naht trägt für die Qwen-Familie und SDXL/SD3.5 direkt. **FLUX.2 und HiDream verlassen
das ControlNet-Paradigma** zugunsten integrierten Multi-Reference-Editings und brauchen je
eine eigene Adapterschicht — das ist bei der Entwurfsentscheidung einzuplanen, nicht später
zu entdecken.

---

## 5 · Lokale Sprachmodelle als Steuerung

### Was es gibt

| Baustein | Lizenz | Geprüft | Urteil |
|---|---|---|---|
| **llama.cpp** | **MIT** | ⚠️ Sekundärquelle | ✅ zulässig |
| **Ollama** | **MIT** | ✅ Repo-Footer | ✅ zulässig |
| **vLLM** | **Apache-2.0** | ⚠️ Sekundärquelle | ✅ zulässig |
| **MCP Python SDK** | MIT | ❌ **nicht geprüft** | vermutlich ✅ |
| **text-generation-webui** | **AGPL-3.0** | ⚠️ Sekundärquelle | ⛔ **AGPL-Fund** |
| **Open WebUI** | **custom, Branding-Klausel** | ⚠️ Sekundärquelle | ⛔ nicht OSI-konform |
| LM Studio | proprietär | — | ⛔ |
| Jan | Apache-2.0 | ⚠️ Sekundärquelle | ✅ zulässig |

Zwei Funde, die man leicht übersieht:

- **text-generation-webui ist AGPL-3.0.**
- **Open WebUI ist kein Open Source im OSI-Sinn.** Die Lizenz verlangt die Beibehaltung des
  Open-WebUI-Brandings und behält White-Label-Einsatz zahlenden Kunden vor. Das ist keine
  GPL-Frage, aber es ist eine **Auslieferungssperre** für ein Apache-2.0-Produkt — und weil
  es keine bekannte Lizenz ist, fällt es durch jede automatische Prüfung.

Die Laufzeiten selbst sind unproblematisch: llama.cpp (MIT), Ollama (MIT) und vLLM
(Apache-2.0) sind alle sauber. **Die Oberflächen sind das Problem, nicht die Motoren** —
was gut passt, denn Regel 4 verlangt ohnehin, dass der Kern ohne Oberfläche läuft.

**Zu Ollama:** MIT ist bestätigt, aber es ist ein risikokapitalfinanziertes Produkt mit
Preisliste und optionaler Remote-Ausführung. Für einen local-first-Prototyp würde ich
llama.cpp als Referenz betrachten und Ollama als Bequemlichkeitsschicht — nicht umgekehrt.

### Wo der Prototyp eigenständig werden muss

Nicht beim Modellbetrieb. Wohl aber bei **der Naht, über die ein Sprachmodell die Bildkette
bedienen darf** — und dort ist die entscheidende Frage keine der Fähigkeit, sondern der
Absicherung.

Ein GPU-Render ist teuer und nicht abbrechbar. Ein Sprachmodell, das direkt rendern darf,
ist ein Modell, das Hardware blockieren kann. Die tragfähige Form ist eine **Auftrags-Warteschlange
mit Freigabe**: Das Sprachmodell *stellt Aufträge ein*, es *führt sie nicht aus*. Ein
separater Prozess führt aus, und zwar nur bei ausdrücklicher Freigabe und freier GPU.

KosmoVis hat genau diese Trennung gebaut (MCP-Server → Datei-Job-Store → Idle-Scheduler) und
seine Empirie dazu ist ehrlich: mit einem lokalen `qwen3-coder:30b` ist **Bedienen** machbar,
**Reparieren und Weiterentwickeln** nicht. Diese Erwartung würde ich für den Prototyp
übernehmen — ein lokales Sprachmodell ist eine Bedienoberfläche, kein Entwickler.

---

## 6 · GPL/AGPL-Funde, gesammelt und ausdrücklich

Regel 1 verlangt, GPL-Funde explizit zu melden. Hier sind sie vollständig an einer Stelle:

**AGPL-3.0 (Netzwerk-Copyleft — für eine Pipeline besonders heikel):**
- OneTrainer (LoRA-Training)
- SimpleTuner (LoRA-Training)
- text-generation-webui (LLM-Oberfläche)
- Shaamallow/texture-diffusion (Blender-Texturierung)
- Clarity-Upscaler (Upscaling)

**GPL-3.0:**
- **ComfyUI** ← der folgenreichste Fund; schliesst das De-facto-Standard-Backend aus
- Fooocus
- Bonsai / BlenderBIM (IFC-Authoring in Blender)
- `bpy` PyPI-Wheel
- StableGen, ComfyUI-BlenderAI-node, alexisrolland/ComfyUI-Blender, Dream Textures
  (sämtliche Blender-KI-Brücken)

- **CGAL-Pakete `Nef_polyhedron_3` und `Polygon_mesh_processing`** — statisch im
  `ifcopenshell`-PyPI-Wheel, verifiziert am Binary (Kap. 2). Der einzige Fund, der sich
  nicht aus einer Lizenzangabe ablesen liess, sondern nur aus dem Paket selbst.

**GPL-2.0-or-later:**
- Blender (Quellcode; Binär-Releases GPL-3.0-or-later)

**Grenzfälle, die keine GPL-Funde sind, aber eine Entscheidung brauchen:**
- **IfcOpenShell selbst: LGPL-3.0-or-later** — schwaches Copyleft, über Prozessgrenze
  beherrschbar. Der GPL-Anteil kommt nicht von IfcOpenShell, sondern von CGAL.
- **Open WebUI: custom mit Branding-Klausel** — nicht OSI, fällt durch automatische Prüfung
- **FLUX.1-dev / FLUX.2-dev: Non-Commercial** — erstreckt sich auf abgeleitete LoRAs
- **Krita AI Diffusion: GPL-3.0** — *berichtigt 18.08.2026, siehe Kapitel 2. Die
  ursprüngliche Angabe „MIT über GPL-Backend" stammte aus einer Sekundärquelle und war
  falsch, und zwar in die gefährliche Richtung.*
- **SwarmUI: MIT über GPL-Backend** — der MIT-Schild trügt

---

## 7 · Was aus KosmoVis übernehmbar ist

Der Owner hat das Lesen und Übernehmen von KosmoVis-Code ausdrücklich erlaubt. Der
belastbarste Befund dazu ist eine Zahl, die ich selbst gemessen habe:

**54 von 124 Python-Modulen in KosmoVis sind `bpy`-frei.** Die übrigen 70 sind
Blender-Add-on-Code (`bl_info`, `register()`/`unregister()`, `import bpy`) und damit unter
Regel 2 und Regel 4 **nicht übernehmbar** — nicht als Code, wohl aber als Vorlage.

Direkt übernehmbar, weil `bpy`-frei und in sich geschlossen:

| Modul | LOC | Was es leistet |
|---|---|---|
| `ifc_to_glb.py` | 391 | IFC → glb mit Massstabs-/Georeferenz-Diagnose |
| `connectors/archicad_ifc.py` | 243 | Torwächter vor teurem Render, Prozessgrenze dokumentiert |
| `archviz_geometry_fidelity.py` | 495 | Geometrie-Treue-Score |
| `archviz_style_score.py` | 370 | Stil-Score |
| `render_job_store.py` | 178 | Auftrags-Warteschlange mit Freigabe-Token |
| `backbone_adapter.py` | 206 | Modell-Registry (der Austauschbarkeits-Vertrag) |
| `kosmovis_render.py` | 656 | Render-Einstieg mit Doppel-Gate |
| `render_scheduler.py` | 564 | Ausführung nur bei freier GPU |

Zwei Dinge, die ausdrücklich **nicht** mitwandern dürfen:

- **`archviz_license.py`** — ein proprietäres Lizenzschlüssel-Schema mit Hardware-Bindung
  und Master-Secret. In einem Apache-2.0-Repo ist das ein Widerspruch in sich.
- **Jeder Bezug auf echte Projekte.** KosmoVis' `refs/haus_stil/README.md` nennt den
  Bürona­men des Stil-Referenzsets im Klartext, auch wenn die Bilddateien korrekt
  gitignored sind. Unter Regel 3 gilt das auch für Namen in Kommentaren, Pfaden und
  Fixtures — nicht nur für Dateien.

**Wichtige Einschränkung zur Reife:** Der ETH-Bericht bewertet KosmoVis selbst mit ~60–65 %
und benennt als Schwächen ein fehlendes Regressions-Testnetz und die Tatsache, dass zum
Berichtszeitpunkt **noch kein echtes Projekt durchgerendert** war. Ich habe das nicht
nachgeprüft — der übernommene Code ist erprobt, aber nicht abgenommen.

---

## 8 · Drei Korrekturen am ETH-Bericht vom 2026-06-30

Ich behandle den Vorgängerbericht als Hypothese, nicht als Quelle. Drei Stellen halten der
Nachprüfung nicht stand:

1. **Qwen-Image-2.0 ist nicht der „Nachfolge-Default".** Der Bericht führt es als 7B,
   Apache-2.0, mit Union-Control-LoRA. Tatsächlich wurde Qwen-Image-2.0 am 10.02.2026
   angekündigt, die **Gewichte sind aber bis heute nicht offen veröffentlicht** — es ist
   API-Zugang über Alibaba Cloud BaiLian. Der lauffähige Apache-2.0-Flaggschiff-Stand ist
   **Qwen-Image-2512 / Qwen-Image-Edit-2511, beide 20B**. Das ändert die Planung spürbar:
   Der erhoffte Sprung auf ein leichteres 7B-Modell steht nicht zur Verfügung.
2. **Die LGPL-Frage bei IfcOpenShell fehlt im Bericht.** Er behandelt die GPL-Grenze bei
   Blender sorgfältig, benennt aber nirgends, dass der IFC-Pfad über eine LGPL-Bibliothek
   läuft. Für ein Regelwerk, das „ohne GPL/AGPL" fordert, ist das die zweitwichtigste
   Lizenzfrage überhaupt.
3. **InvokeAI als Apache-Ausweg ist schwächer geworden.** Der Bericht führt InvokeAI ohne
   Vorbehalt als Apache-2.0-Alternative. Seit Oktober 2025 sind Teile des Teams bei Adobe.

---

## 9 · Was ich nicht prüfen konnte

Ausdrücklich offen, damit niemand diese Punkte für geprüft hält:

**Lizenzen, die ich nur aus Sekundärquellen habe** (Suchergebnisse, Blogs, oder die
KosmoVis-Dokumentation — nicht die LICENSE-Datei selbst): Fooocus, InvokeAI, SwarmUI,
Krita AI Diffusion, Ryven, kohya-ss/sd-scripts, ostris/ai-toolkit, diffusers/transformers/peft,
llama.cpp, vLLM, Jan, text-generation-webui, Open WebUI, sämtliche Blender-KI-Brücken,
sowie die Modellkarten von Qwen-Image-2512, Z-Image und FLUX.2 klein.
Vor einer Auslieferung gehört jede davon gegen die tatsächliche LICENSE-Datei geprüft.

**Gar nicht geprüft:** NodeGraphQt, musubi-tuner, xbim Toolkit, MCP Python SDK,
SD3.5 Community License (insbesondere die Umsatzschwelle), OpenRAIL++-M (die Nutzungsauflagen
sind nicht trivial und können mit Apache-2.0 in Konflikt geraten).

**Erledigt:** Der CGAL-Verdacht ist am 2026-08-14 geprüft und **bestätigt** — siehe
Nachtrag in Kap. 2. Damit ist der offene Punkt geschlossen, allerdings mit dem
unangenehmeren der beiden möglichen Ergebnisse.

**Was diese Prüfung nicht abdeckt:** Ich habe genau ein Paket auf statisch eingebundene
Fremdbibliotheken untersucht. Jedes weitere Wheel mit grossem Binäranteil — `torch`,
`opencv`, `trimesh`-Abhängigkeiten — kann dasselbe Problem tragen und ist ungeprüft.

**Nichts ausgeführt.** Ich habe keinen Code laufen lassen, keine Modelle geladen, kein
Blender gestartet, keine Messung reproduziert. Sämtliche Aussagen über KosmoVis' Reife und
Messwerte stammen aus dessen eigener Dokumentation. Insbesondere die Schwellenwerte der
Geometrie-Treue-QA sind laut eigenem Bericht an wenigen Fällen kalibriert.

**Keine Rechtsberatung.** Die Lizenzeinordnungen sind technische Einschätzungen. Die
Prozessgrenzen-Argumentation bei Blender und IfcOpenShell ist gängige Praxis und gut
begründet, aber gerichtlich nicht abschliessend geklärt.

---

## 10 · Wo der Prototyp eigenständig werden muss — Zusammenfassung

Die Frage war, wo eigenständig gebaut und wo Bestehendes genutzt werden soll. Die Antwort
fällt schärfer aus, als ich erwartet hatte:

**Eigenständig, weil die Lizenz dazu zwingt:**
1. **Der Graph-Kern.** ComfyUI ist GPL-3.0 und damit als Kern ausgeschlossen. Ein eigener
   typisierter DAG mit Artefakt-Cache ist unvermeidbar — aber klein, wenn die Knoten nur
   `diffusers` aufrufen statt ComfyUIs Zoo nachzubauen.
2. **Die Blender-Ansteuerung.** Jede existierende Brücke ist GPL und ein Add-on.

**Eigenständig, weil es nirgends existiert:**
3. **Die Geometrie-Treue-QA.** Kein einziges Werkzeug im gesamten geprüften Feld — weder
   die generischen Plattformen noch die Blender-Brücken — prüft, ob der erzeugte Render der
   Eingangsgeometrie folgt. Das ist die einzige echte Forschungslücke, die ich gefunden habe,
   und damit der wissenschaftlich tragfähige Kern der Arbeit.
4. **Die Architektur-Connectors.** IFC als erstklassige Eingabe statt einer Prompt-Box.
   Inklusive Torwächter gegen Massstabs- und Georeferenz-Fehler.

**Nicht eigenständig — hier wäre Eigenbau reine Verschwendung:**
- Diffusion-Inferenz → `diffusers` (Apache-2.0)
- LoRA-Training → kohya (Apache-2.0) oder ai-toolkit (MIT) als Subprozess
- IFC-Parsen → IfcOpenShell (LGPL) hinter einer Prozessgrenze
- Rendern → Blender headless als Subprozess
- Sprachmodell-Betrieb → llama.cpp (MIT)
- Knoten-Darstellung → litegraph.js oder xyflow (beide MIT)

**Das wiederkehrende Muster:** Die Prozessgrenze ist nicht nur ein Lizenztrick für Blender,
sondern das Bauprinzip des ganzen Systems. Blender (GPL), IfcOpenShell (LGPL) und die
Trainings-Werkzeuge liegen alle jenseits einer Subprozess-Grenze; der eigene Kern bleibt
Apache-2.0, `bpy`-frei und ohne Oberfläche aufrufbar. Regel 2 und Regel 4 beschreiben
dieselbe Architektur aus zwei Richtungen.

---

## 11 · Offene Entscheidungen

### Entschieden am 2026-08-14

1. **✅ LGPL ist zugelassen** — unter drei Auflagen: nur hinter einer Prozessgrenze, nur
   unverändert, austauschbar und im `NOTICE` deklariert. Festgehalten in `CLAUDE.md` als
   Präzisierung von Regel 1. Dieselben Auflagen gelten für die GPL-Komponenten, die als
   eigenständiges Programm aufgerufen werden (Blender, IfcOpenShell/CGAL).
2. **✅ CGAL-Frage geklärt** — bestätigt, siehe Kap. 2. IfcOpenShell bleibt eingeplant,
   aber zwingend hinter der Prozessgrenze.

### Weiterhin offen

3. **Wie viel KosmoVis wandert mit?** Die acht `bpy`-freien Module wären ein erheblicher
   Vorsprung — aber sie tragen KosmoVis' Entwurfsentscheidungen mit sich. Alternative:
   nur die Verträge (Schemas, Torwächter-Logik) übernehmen und den Code neu schreiben.
4. **Ist der wissenschaftliche Kern die Geometrie-Treue-QA?** Nach dieser Lagebeurteilung
   ist es der einzige Punkt, an dem der Prototyp etwas kann, was sonst niemand kann. Das
   Packaging ist ein Produktbeitrag, aber kein Forschungsbeitrag.

---

---

## 12 · Nachtrag 2026-08-18: DINOv3 fällt unter Regel 1 durch

Beim Bauen des Stil-Gates wurde die Lizenz des Einbettungsmodells geprüft — eine Frage,
die diese Lagebeurteilung offengelassen hatte und die der Vorläufer KosmoVis stillschweigend
mit **DINOv3** beantwortet. Das Ergebnis korrigiert diese geerbte Annahme.

**DINOv3 steht unter einer eigenen Meta-Lizenz**, nicht unter einer der vier zugelassenen.
Drei Auflagen:

1. **Gated** — Zugang muss beantragt werden, unter Angabe persönlicher Daten.
2. **Namensnennung** — „Built with DINOv3" ist sichtbar zu führen.
3. **Weitergabe nur samt Lizenztext** für abgeleitete Werke.

Kommerzielle Nutzung ist dabei ausdrücklich **erlaubt**. Das ändert nichts an der
Bewertung: Regel 1 verlangt permissive Lizenzen, nicht bloss erlaubte Nutzung. Eine
Sonderlizenz mit Auflagen ist genau das, was sie ausschliesst.

Dazu kommt ein praktischer Grund, der für ein öffentliches Apache-2.0-Repo schwerer wiegt
als der formale: **Eine gated Abhängigkeit kann niemand nachvollziehen**, der keinen
Zugang beantragt hat. Eine wissenschaftliche Arbeit, deren Messkette hinter einem
Antragsverfahren liegt, ist nicht reproduzierbar.

### Die Alternativen sind sauber

| Modell | Lizenz | Bemerkung |
|---|---|---|
| **SigLIP 2** (`google/siglip2-base-patch16-224`) | **Apache-2.0** | **neue Vorgabe** — nicht gated, keine Auflagen |
| **DINOv2** (`facebook/dinov2-base`) | Apache-2.0 | Vorgänger von DINOv3, selbstüberwacht — verhaltensnäher |
| **OpenCLIP ViT-B/32** | MIT | grosses Ökosystem |
| ~~DINOv3~~ | Meta-Sonderlizenz | **ausgeschlossen** |

Festgehalten in `src/aiimaging/einbetter.py` — mitsamt DINOv3 als **ausgeschlossen
markiertem** Eintrag, damit der Grund auffindbar bleibt und niemand später „das nimmt
KosmoVis doch auch" denkt. `waehle()` gibt es nie zurück; ein Test hält das fest, mit
Gegenprobe gegen einen vakuösen Test.

### Was dieser Wechsel kostet

Die überlieferten Wertebereiche des Stil-Scores (Treffer ~0,5–0,6, Verfehlung ~0,06–0,13)
stammen aus **DINOv3**-Läufen. Ob SigLIP-Embeddings den Haus-Stil ähnlich gut trennen,
ist **ungeprüft**. Die Schwelle 0,30 ist beim Einbetterwechsel neu zu kalibrieren — was
ohnehin in die Schwellenstudie (Phase 4) gehört, aber jetzt nicht mehr optional ist.

---

## 13 · Nachtrag 2026-08-18: Depth-Anything-V2 ist nach Grösse verschieden lizenziert

Beim Bau der **Ist-Seite** der Geometrie-QA — der Tiefenschätzung aus dem erzeugten Bild —
wurde die Lizenz des Schätzers geprüft. Kapitel 4 führte ihn als „offen". Er ist es nicht
mehr, und die Antwort trifft ausgerechnet den Forschungskern.

**Der Schätzer ist nach Modellgrösse unterschiedlich lizenziert** (direkt an den
Modellkarten geprüft):

| Variante | Lizenz | Urteil |
|---|---|---|
| **Depth-Anything-V2-Small** (25M) | **`apache-2.0`** | ✅ **die einzige brauchbare Wahl** |
| Depth-Anything-V2-Base (97M) | `cc-by-nc-4.0` | ⛔ Non-Commercial |
| Depth-Anything-V2-Large (335M) | `cc-by-nc-4.0` | ⛔ Non-Commercial |
| Depth-Anything-V2-Giant (1.3B) | `cc-by-nc-4.0` | ⛔ Non-Commercial |

**Der Vorläufer KosmoVis benutzt ViT-L** — also Large, also Non-Commercial. Kapitel 6.1 des
KosmoVis-Berichts führt DepthAnythingV2 pauschal als „offen"; tatsächlich ist die dort
eingesetzte Variante unter Regel 1 ausgeschlossen. Zweite geerbte Annahme nach DINOv3, die
der Prüfung nicht standhält — und beide betreffen die QA-Schicht, also genau den Teil, der
als wissenschaftlicher Beitrag gilt.

### Warum das mehr wiegt als die DINOv3-Frage

Beim Stil-Gate war der Wechsel ein Austausch unter Gleichwertigen: SigLIP 2 statt DINOv3,
beide gross, beide brauchbar. Hier ist es ein Wechsel **von 335M auf 25M Parameter** —
gut eine Grössenordnung.

Die Geometrie-Treue-Metrik steht und fällt damit, wie gut das Ist aus dem erzeugten Bild
zurückgerechnet wird. Ein schwächerer Schätzer verrauscht beide Anteile: die Rangkorrelation
der Tiefe und die Silhouette. Das verschiebt möglicherweise die Schwelle 0,65 — in welche
Richtung und wie weit, ist **ungeprüft**.

### Was daraus folgt

1. **Vorgabe ist Small (Apache-2.0).** Die drei anderen stehen in der Registry, aber als
   ausgeschlossen markiert — mit Begründung, damit der Grund auffindbar bleibt.
2. **Die Schwellenstudie in Phase 4 wird dadurch wichtiger, nicht unwichtiger.** Sie muss
   jetzt zwei Dinge leisten: die Schwelle kalibrieren *und* zeigen, ob Small dafür genügt.
3. **Ein sauberer Nebennutzen für die Arbeit:** Der Vergleich Small gegen Large ist ein
   ordentliches Experiment. Large darf für eine **wissenschaftliche Untersuchung** benutzt
   werden — Non-Commercial verbietet die kommerzielle Verwertung, nicht die Forschung. Das
   ausgelieferte Produkt bleibt bei Small; die Arbeit darf beide vermessen und die Differenz
   berichten. Das ist ehrlicher als so zu tun, als gäbe es keinen Unterschied.

*Vorbehalt zu Punkt 3: Diese Einordnung von CC-BY-NC im Forschungskontext ist meine
technische Einschätzung, keine Rechtsberatung. Wer sie nutzt, sollte sie im Rahmen der
ETH-Arbeit kurz absichern.*

---

## Quellen

Direkt geprüft (LICENSE-Datei, Repo-Sidebar oder Modellkarte):
[ComfyUI](https://github.com/Comfy-Org/ComfyUI/blob/master/LICENSE) ·
[IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell) ·
[web-ifc LICENSE.md](https://github.com/ThatOpen/engine_web-ifc/blob/main/LICENSE.md) ·
[IfcPlusPlus](https://github.com/ifcquery/ifcplusplus) ·
[litegraph.js LICENSE](https://github.com/jagenjo/litegraph.js/blob/master/LICENSE) ·
[SimpleTuner](https://github.com/bghira/SimpleTuner) ·
[Ollama](https://github.com/ollama/ollama) ·
[Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) ·
[Blender License](https://www.blender.org/about/license/) ·
[bpy auf PyPI](https://pypi.org/project/bpy/) ·
[Cycles permissive license](https://code.blender.org/2013/08/cycles-render-engine-released-with-permissive-license/) ·
[Cycles Standalone](https://developer.blender.org/docs/features/cycles/standalone/)

Sekundärquellen (nicht gegen die LICENSE-Datei verifiziert):
[Bonsai / IfcOpenShell-Doku](https://docs.ifcopenshell.org/bonsai.html) ·
[OneTrainer](https://onetrainer.org/) ·
[kohya-ss/sd-scripts](https://github.com/kohya-ss/sd-scripts) ·
[ostris/ai-toolkit](https://sanj.dev/post/onetrainer-vs-kohya-ss-vs-ai-toolkit/) ·
[LLM-Laufzeiten-Vergleich](https://d-central.tech/local-ai-runtime-comparison/) ·
[Open-WebUI-Lizenz](https://www.promptquorum.com/local-llms/text-generation-webui-vs-vllm-vs-llamacpp) ·
[InvokeAI](https://ai.miraheze.org/wiki/InvokeAI) ·
[Qwen-Image-2.0 Status](https://manifold.markets/ShankarSivarajan/when-will-qwenimage20-weights-becom) ·
[Open-Weight-Bildmodelle 2026](https://www.thundercompute.com/blog/best-open-source-image-generation-models) ·
[xyflow](https://github.com/xyflow/xyflow) ·
[React Flow](https://reactflow.dev/)

Projektintern: `Imperigo/KosmoVis` @ `35c9305` — insbesondere
`docs/KOSMOVIS_BERICHT_ETH_2026-06-30.md`, `connectors/archicad_ifc.py`,
`01_workflow/ifc_to_glb.py`, `CROSS_WORKER_INFO_2026-06-16_Overseer-DiffSynth-i2L.md`
