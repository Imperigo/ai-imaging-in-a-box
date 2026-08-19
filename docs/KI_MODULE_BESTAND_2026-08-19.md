# Die beiden ungeöffneten KI-Module des Altbestands · Auswertung

**Datum:** 2026-08-19
**Gegenstand:** `archviz_comfyui_workflow.py` (1706 Zeilen) und `archviz_ai_pipeline_v2.py`
(1450 Zeilen) aus dem KosmoVis-Altbestand — die beiden Module, die
`docs/BLENDER_ADDON_BESTAND_2026-08-18.md` in Kapitel C.4 als **nicht geöffnet** führt.
**Auftrag:** Was davon ist brauchbar?

**Zustand des fremden Arbeitsbaums:** vollständig. `git ls-files` meldet 314 Dateien,
auf der Platte liegen 314 Dateien, `git status` ist leer. **Kein `git reset --hard`
war nötig, und es wurde keiner ausgeführt.** Am fremden Repo wurde nichts geändert.

---

## TEIL 0 · Der Lizenzbefund zuerst (Regel 1)

### 0.1 · Die beiden beauftragten Module: kein ComfyUI-Code — Fall (a) und (c)

**`archviz_comfyui_workflow.py` ist lizenzrechtlich unbedenklich.** Der Befund im
Einzelnen, mit dem Prüfweg:

| Prüfung | Ergebnis |
|---|---|
| Alle `import`/`from`-Zeilen des Moduls | genau drei: `os`, `json`, `urllib.request` |
| `import comfy`, `import nodes`, `import folder_paths`, `import execution` | **kein Treffer** |
| `NODE_CLASS_MAPPINGS`, `INPUT_TYPES`, `RETURN_TYPES`, `CATEGORY =` | **kein Treffer** — also auch keine Custom-Node-Verpackung |
| `custom_nodes`, `comfy_extras` | **kein Treffer** |

Was das Modul tatsächlich tut: Es baut Python-Wörterbücher der Form
`{"class_type": "KSampler", "inputs": {...}}` und gibt sie zurück. Die Zeichenketten
`"KSampler"`, `"CheckpointLoaderSimple"`, `"ControlNetApplyAdvanced"` sind **Namen von
Knoten in einer fremden Schnittstelle**, kein Programmtext — dasselbe Verhältnis wie
zwischen einer HTTP-Anfrage und dem Server, den sie anspricht.

Damit liegt **Fall (c)** vor: ein ComfyUI-Workflow wird als JSON gebaut und weggeschickt.
Das ist eine Datenstruktur, kein Code.

An drei Stellen kommt zusätzlich **Fall (a)** hinzu: das Modul fragt den laufenden
ComfyUI-Server über `urllib.request.urlopen("http://127.0.0.1:8188/object_info")`, welche
Knoten und Modelle er kennt, bevor es sie in den Workflow schreibt. Ein HTTP-Aufruf gegen
einen eigenständig laufenden Server ist eine Prozessgrenze im Sinn der LGPL-Präzisierung
der `CLAUDE.md` — Aggregation, kein abgeleitetes Werk.

**`archviz_ai_pipeline_v2.py` enthält ebenfalls keinen ComfyUI-Code.** Es ruft die beiden
Nachbarmodule auf und sonst nichts, was ComfyUI berührt.

Die eigentliche Transportschicht liegt in einem dritten, nicht beauftragten Modul,
`archviz_comfyui_bridge.py`: reines `urllib.request` gegen `/prompt`, `/queue`,
`/history`, `/view`, `/upload/image`, plus ein `subprocess.Popen` auf ein Startskript.
Auch das ist durchgehend Prozessgrenze. (Der Kopfkommentar spricht von Websocket; im Code
steht keiner — es wird abgefragt, nicht gelauscht.)

> **Zwischenbefund:** Aus den beiden beauftragten Modulen folgt **kein Regel-1-Verstoss**.
> Wer ihre Bauart übernähme, bliebe auf der zulässigen Seite.

### 0.2 · ABER: ein Regel-1-Befund ersten Ranges nebenan — `kosmovis_render.py`

Die repo-weite Gegenprobe (`grep` nach echten ComfyUI-Importen über alle 314 Dateien) hat
**einen** Treffer geliefert, und der wiegt schwer.

`01_workflow/kosmovis_render.py` (656 Zeilen) — laut eigenem Kopfkommentar der
„**produktionsreife KosmoVis Render-Einstieg**", also nicht ein Experiment, sondern der
gedachte Hauptweg — tut Folgendes:

* `import nodes` — **ComfyUIs eigenes Knotenmodul**
* `import execution` — **ComfyUIs eigener Ausführungskern**
* `execution.PromptExecutor(...)` wird instanziiert und im selben Prozess betrieben
* `execution.validate_prompt(...)` wird aufgerufen; ein Kommentar nennt die Funktion
  ausdrücklich „**Mirror von `execution.validate_prompt`**"
* ein selbstgebauter `_Stub` ersetzt ComfyUIs Server-Objekt, damit der Ausführungskern
  ohne Webserver läuft
* der Lauf ist ausdrücklich für ComfyUIs eigenes venv vorgesehen

**Das ist Fall (b): ComfyUI-Code wird importiert und in-process ausgeführt.** ComfyUI
steht unter **GPL-3.0**. Ein Programm, das ComfyUIs Module importiert und dessen
Ausführungskern instanziiert, ist bei Weitergabe ein abgeleitetes Werk und fällt selbst
unter GPL-3.0.

**Folgen für uns, konkret:**

1. **`kosmovis_render.py` darf nicht in unser Produkt.** Nicht als Kopie, nicht als
   Vorlage, aus der abgeschrieben wird, nicht in Teilen. Es ist der einzige Modulname des
   Altbestands, der bisher wie ein natürlicher Kandidat für „das haben die schon gebaut"
   aussah — und er ist der einzige, der es sicher nicht ist.
2. Die Grenze verläuft **nicht** zwischen „ComfyUI benutzen" und „ComfyUI nicht benutzen",
   sondern zwischen `urllib` gegen `:8188` (zulässig) und `import execution` (nicht
   zulässig). Der Altbestand hat beide Seiten gebaut, ohne den Unterschied irgendwo zu
   benennen.
3. **Das ist ein neuer Befund gegenüber `docs/BLENDER_ADDON_BESTAND_2026-08-18.md`.** Jene
   Bestandsaufnahme führt `kosmovis_render.py` nicht als Lizenzrisiko. Sie sollte
   entsprechend ergänzt werden.

### 0.3 · Regel 1 bei den Modellgewichten — mehrfach verletzt

Unabhängig vom Programmcode führen die beiden beauftragten Module Präferenzlisten von
Modellen. Mehrere davon sind nach Regel 1 ausgeschlossen:

| Liste im Modul | Inhalt | Lizenzlage |
|---|---|---|
| `PREFERRED_FLUX_UNET` | `flux1-dev-*` in acht Quantisierungen | FLUX.1-dev = **nicht-kommerziell**, in `CLAUDE.md` namentlich ausgeschlossen |
| `PREFERRED_KREA_DIFFUSION` / `PREFERRED_KREA_GGUF` | `flux1-krea-dev-*` | Ableitung von FLUX.1-dev, trägt dieselbe nicht-kommerzielle Lizenz |
| `PREFERRED_FLUX_CONTROLNET` | `FLUX.1-dev-ControlNet-Union-Pro*` | ControlNets zu FLUX.1-dev, an dessen Lizenz gebunden |
| `PREFERRED_CHECKPOINTS` | JuggernautXL, RealVisXL, SDXL-Basis | CreativeML OpenRAIL-M mit Nutzungsbeschränkungen — **nicht OSI-permissiv**, deckt sich mit unserem Befund zu SDXL in `docs/BACKBONE_CONTROLNET_2026-08-18.md` Kap. 4.3 |
| `PREFERRED_UPSCALE_MODELS` | `4x-UltraSharp.pth`, `4x_NMKD-Siax`, `RealESRGAN_x4plus` | RealESRGAN ist BSD-3-Clause; für die beiden Gemeinschaftsmodelle habe ich **keine Lizenzangabe gefunden und keine geprüft** |

Der ganze Stapel des Altbestands — SDXL-Juggernaut als Basis, FLUX-Krea als „neue Stufe
1", FLUX-ControlNet-Union als Steuerung — ist für ein kommerziell nutzbares Produkt
**geschlossen unbrauchbar**. Das ist nicht überraschend, aber es sollte einmal
ausgeschrieben dastehen, damit niemand die Präferenzlisten für einen Fundus hält.

### 0.4 · Regel-3-Funde (Grund, nichts wörtlich zu übernehmen)

* `archviz_ai_pipeline_v2.py` trägt in den Zeilen 30–35 einen **fest verdrahteten
  persönlichen Cloud-Pfad** mit Klarnamen, Ausbildungsgang und privater Ordnerstruktur.
* Im Kommentar zur Negativ-Prompt-Liste steht ein **Kürzel, das nach einem realen Kunden
  aussieht**, als Name eines Fehlerbilds („… -Logo-Problem").
* Die Auto-Auswahl sucht das Referenzbild in fest verdrahteten deutschen
  Projektordnernamen.
* Der positive Vorspann des Prompts nennt **eine lebende Person und ein reales
  Visualisierungsbüro namentlich** als Stilvorgabe. Das ist unabhängig von Regel 3
  heikel — Stilimitation benannter lebender Urheber gehört nicht in ein
  Vertiefungsarbeits-Prototyp, der öffentlich liegt.

Alles vier sind Gründe, aus diesen Dateien **Gedanken** zu übernehmen und **keine Zeile
Text**.

---

## TEIL 1 · Was tun die beiden Module?

### `archviz_comfyui_workflow.py` — der Bauplanzeichner

Dieses Modul rendert nichts. Es **schreibt Baupläne**. Man gibt ihm ein Wörterbuch mit
Wünschen — welches Bild aus Blender vorliegt, welche Tiefenkarte, wie treu es dem
Ausgangsbild bleiben soll, wie viele Fassungen es geben soll — und es liefert einen
vollständigen, ausführbaren Ablaufplan für ComfyUI zurück, als reine Datenstruktur.

Bevor es das tut, fragt es beim Bildprogramm nach, was dort überhaupt installiert ist,
und **baut nur das ein, was wirklich da ist**. Fehlt die Tiefensteuerung, wird sie
weggelassen statt zu einem Absturz zu führen; fehlt die Stilübertragung, ebenso. Es gibt
vier verschiedene Baupläne: den Hauptweg, einen zweistufigen „erst Grobbild, dann
Detailverfeinerung, dann Vergrösserung", einen fürs Nachbessern einer einzelnen
Bildstelle, und einen für ein alternatives Hauptmodell.

### `archviz_ai_pipeline_v2.py` — die Schalttafel

Dieses Modul ist die **Bedienoberfläche in Blender**. Es ist ein Knoten mit einem grossen
Knopf, ein paar Reglern und einer Bildergalerie darunter. Ein Druck auf den Knopf löst
die ganze Kette aus: prüfen ob das Bildprogramm läuft und es notfalls starten, in Blender
rendern, aus dem Ergebnis mit dem Nachbarmodul einen Bauplan bauen, ihn hinschicken,
warten, die fertigen Bilder abholen, sie bewerten, das beste vorschlagen und ablegen.

Die Regler sind bewusst zweistufig: drei grosse, in normaler Sprache benannte Regler
(Material-Treue, Stil, Dramatik) rechnen im Hintergrund auf sechs technische Zahlen um.
Wer will, klappt die technischen Zahlen auf und stellt sie einzeln.

---

## TEIL 2 · Was braucht `bpy` und was nicht

### `archviz_comfyui_workflow.py` — **vollständig `bpy`-frei**

Kein `import bpy`, keine Blender-Datentypen, keine laufende Oberfläche vorausgesetzt.
Das Modul ist als reine Bibliothek aufrufbar und hat sogar einen eigenen Selbsttest unter
`if __name__ == "__main__"`. Es erfüllt Regel 4 vorbildlich.

| Funktion | Zeilen | `bpy`? | Einstufung nach unserer Grenze |
|---|---|---|---|
| `_fetch_remote_object_info`, `_remote_model_list`, `_detect_via_remote` | 158–240 | nein | Rechnung + HTTP über Prozessgrenze — produktfähig |
| `detect_available_models` | 241–358 | nein | Rechnung + Verzeichnisdurchsicht — produktfähig |
| `build_archviz_workflow` | 399–924 | nein | Rechnung; **aber** zwei HTTP-Aufrufe stecken mitten im Bau (Z. 544, 622) |
| `_detect_multistage_via_remote`, `detect_multistage_models` | 925–1047 | nein | Rechnung |
| `build_multistage_workflow` | 1056–1280 | nein | Rechnung |
| `build_inpaint_workflow` | 1281–1385 | nein | Rechnung |
| `detect_krea_models`, `build_flux_krea_workflow`, `get_flux_krea_status` | 1402–1694 | nein | Rechnung |
| `register()` / `unregister()` | 1696–1704 | nein (leere Rümpfe) | **Regel-2-Rest** — s. u. |

**Ein Konstruktionsfehler, auch ohne `bpy`:** `build_archviz_workflow` ist als reine
Funktion beschrieben, öffnet aber zweimal mitten im Bau eine Netzverbindung, um zu
prüfen, ob ein Knoten existiert. Damit hängt das Ergebnis der Funktion vom Zustand eines
fremden Servers ab, ohne dass das an der Schnittstelle sichtbar wäre. Sie ist ohne
laufenden Server nicht wiederholbar prüfbar. Wer die Bauart übernimmt, zieht diese
Abfragen nach vorn in die Erkennungsstufe — dort gehören sie hin und dort stehen sie
teilweise auch schon.

**Regel-2-Rest:** die leeren `register()`/`unregister()` am Dateiende existieren nur,
damit Blenders Autoloader das Modul mitlädt. Ein `bl_info` fehlt. Nach Regel 2 ist jede
Add-on-Verpackung ausgeschlossen — beim Übernehmen fallen diese beiden Funktionen
ersatzlos weg. Sie sind der einzige Regel-2-Kontakt dieser Datei.

### `archviz_ai_pipeline_v2.py` — **vollständig `bpy`-gebunden**

`bl_info` in Zeile 14, `import bpy` in Zeile 22, `bpy.types.Node`, `bpy.types.Operator`,
`bpy.props.*` durchgehend. Nach Regel 2 ist das Modul **als Ganzes vom Produkt
ausgeschlossen** und gehört, wenn überhaupt, jenseits der Prozessgrenze.

| Einheit | Zeilen | `bpy`? | Einstufung |
|---|---|---|---|
| `_auto_load_bolognese_refs` | 37–46 | nein | trivial; enthält den Privatpfad |
| `ARCHVIZ_NODE_AIPipelineV2` (Knotenklasse, ~835 Z.) | 50–885 | ja | Oberfläche — Runner-Seite |
| ↳ `_apply_macro_sliders` | 380–406 | formal ja | **Die Rechnung darin ist `bpy`-frei**: sechs lineare Abbildungen. Diese ~10 Zeilen sind der einzige Teil dieses Moduls, dessen *Inhalt* ins Produkt könnte |
| ↳ `_apply_quality_preset` | 407–430 | formal ja | Eine Tabelle mit sieben Spalten. Ebenfalls inhaltlich `bpy`-frei |
| `ARCHVIZ_OT_aip_run_pipeline` | 895–1180 | ja | Ablaufsteuerung — als **Vorbild** wertvoll, als Code nicht übernehmbar |
| `ARCHVIZ_OT_aip_cancel_pipeline`, `…_start_comfyui`, `…_select_variant`, `…_upscale` | 1181–1273 | ja | Oberfläche |
| `ARCHVIZ_OT_aip_auto_pick_best` | 1274–1393 | ja | nur Hülle; die Bewertung selbst liegt in `archviz_variant_scorer` und ist `bpy`-frei |
| `ARCHVIZ_OT_aip_save_final` | 1394–1435 | ja | Oberfläche |
| `register()` / `unregister()` | 1436–1450 | ja | Add-on-Verpackung — Regel 2 |

`tests/test_prozessgrenze.py` würde bei diesem Modul sofort anschlagen, und das zu Recht.

---

## TEIL 3 · Was ich übernehmen würde und was nicht

### 3.1 · Übernehmen (als Gedanke, nie als Zeile)

**A. Die Fortschrittsgrenze — die wichtigste Einzelübernahme.**
Der Altbestand führt **zwei** Zeitgrenzen: eine harte Gesamtdauer (`bridge_timeout`) und
eine zweite, `bridge_no_progress` — „maximale Zeit ohne Statuswechsel". Die zweite ist
die wertvollere. Sie fängt genau den Fall, den eine Gesamtdauer nicht fängt: ein
Backbone, das nicht abstürzt, sondern **stehen bleibt**. Die Wertepaare sind nach
Qualitätsstufe gestaffelt (180/60 s beim Schnelltest bis 3000/600 s beim Endprodukt), und
die kleinere Zahl skaliert mit — das ist durchdacht.
**Wir haben das nicht.** Weder `render.py` noch `jobs.py` kennt eine Fortschrittsgrenze.

**B. Der Makroreglersatz.**
Drei benannte Regler auf sechs technische Zahlen:

* Material-Treue → Rauschanteil (fallend), Tiefensteuerung 0.45–0.95, Liniensteuerung
  0.30–0.90
* Stil → Stärke der Bildeinbettung 0.40–1.10 und wie lange sie wirkt, 0.40–0.95
* Dramatik → Führungsstärke 5.0–7.5

Das ist der `faithful`-Regler aus `RENDER_SCENE_CONTRACT.md`, ausgebaut auf drei Achsen
statt einer, und **nach Läufen nachjustiert**. Bei uns liegen `controlnet_staerke`,
`denoise`, `fuehrung` und `schritte` in `RenderAuftrag` einzeln nebeneinander. Eine
Makroschicht darüber wäre ein Gewinn — die *Form* übernehmen, die *Zahlen* nicht: sie
gelten für SDXL mit Bildeinbettung, nicht für Z-Image-Turbo.

**C. Das Beipack-Prinzip des QA-Tors.**
Neben jedes erzeugte Bild wird eine `.json` gelegt: Startwert des Zufalls, beide Prompts,
Sampler, Führungsstärke, Stilangaben, die verwendeten Blender-Passes, welches Backend auf
welchem Rechner, Anfangs- und Endzeit, Dauer, SHA-256 der Datei und der ganze Bauplan.
Damit ist jede Ausgabedatei **allein** nachvollziehbar, auch wenn sie aus ihrem
Verzeichnis herausgetragen wird. Unser `herkunft.py` beantwortet die Herkunftsfrage am
*Eingang* (Einheit, Achsenlage). Am *Ausgang* haben wir nichts Vergleichbares. Der
Gedanke passt genau zur Arbeitsregel „Was nicht in einer Datei steht, ist weg".

**D. Der feste Startwert für Messreihen (`locked_seed`).**
Normalfall: `seed = seed_base + Variantennummer`. Sonderfall `locked_seed`: **alle**
Fassungen bekommen denselben Startwert, damit ausschliesslich der Prompt variiert. Das
ist die saubere Trennung, die eine Vergleichsreihe braucht — und sie ist ausdrücklich als
Bedienelement vorhanden, nicht als Zufallsfund. Unsere `schwellenstudie.py` hält den
Startwert bereits fest („Eine Studie, die sich nicht wiederholen lässt, ist keine"); in
`render.py` fehlt der Gegenpart, weil es dort noch keine Reihe gibt.

**E. Die deterministische Vorgabe statt Zufall.**
Wo kein Startwert gesetzt ist, nimmt der Altbestand `8472` — eine feste Zahl, kein
Zufall. Ein Lauf ohne Angabe ist damit wiederholbar. Das ist eine kleine, richtige
Entscheidung, die wir in `render.py` mit `seed: int = 0` bereits genauso treffen.

### 3.2 · Nicht übernehmen

**Alle vier Bauplanzeichner** (`build_archviz_workflow`, `build_multistage_workflow`,
`build_inpaint_workflow`, `build_flux_krea_workflow`). Zulässig wären sie — aber sie
setzen ComfyUI als Laufzeit voraus und sind damit ein **zweiter, völlig anderer Weg**
neben unserem `render.py` über `diffusers`. `src/aiimaging/graph.py` begründet genau
diese Entscheidung bereits. Zwei Wege zu pflegen ist der Fehler, nicht das Fehlen des
zweiten.

**Sämtliche Modell-Präferenzlisten** — Lizenzlage, s. Kap. 0.3.

**Die Prompt-Vorspänne.** Regel 3 und die Namensnennung lebender Urheber, s. Kap. 0.4.
Unser `prompts.py` ist hier ohnehin weiter.

**Die Erkennung über Dateisystemdurchsicht.** `detect_available_models` durchsucht
`~/ComfyUI/models/`. Unsere `backbone.vorhandene_dateien` und
`render.finde_einzeldatei_gewichte` machen dasselbe sauberer und gegen eine deklarierte
Registry statt gegen eine Namensliste.

**Die gesamte Knoten-Oberfläche** — Regel 2 und Regel 4.

**`kosmovis_render.py` in jeder Form** — Kap. 0.2.

### 3.3 · Was wir ausdrücklich SCHLECHTER haben

Sieben Punkte, in absteigender Wichtigkeit:

1. **Variantenreihen.** `render.rendere()` erzeugt **ein** Bild pro Aufruf mit **einem**
   Startwert. Der Altbestand erzeugt standardmässig fünf Fassungen in *einem* Bauplan,
   fünf Sampler-Knoten mit fortlaufenden Startwerten und ansonsten identischen
   Parametern. Für einen Prototypen, dessen Zweck Bildvorschläge sind, ist das ein echter
   Rückstand.
2. **Vergleich mehrerer Ausgaben gegeneinander.** Der Altbestand bewertet Schärfe,
   Farbreichtum, Histogrammnähe zum Cycles-Bild und Ausreisserabstand zu einem Wert
   0–100 und wählt automatisch. Unsere `stil_qa.py` vergleicht **ein** Bild gegen
   Referenzen; `geometrie_qa.py` **ein** Bild gegen seine Tiefenkarte. Keines vergleicht
   mehrere Erzeugnisse untereinander. Der Ausreisserabstand ist dabei die interessanteste
   der vier Grössen: „welche Fassung fällt aus der Reihe" ist ohne eine Reihe nicht
   definiert und hat deshalb bei uns noch gar keinen Ort.
3. **Belichtungsprüfung der Ausgabe.** Luminanz, Ausbrennen, Dynamikumfang, ein Urteil
   und ein Schweregrad, pro Fassung. Bei uns steckt Vergleichbares nur in
   `schwellenstudie.py` als Messwerkzeug, nicht in der Renderstufe als Prüfung.
4. **Fortschrittsgrenze** (s. 3.1 A).
5. **Zweite Steuerspur.** Der Altbestand fährt Tiefe *und* Linienzeichnung als zwei
   ControlNets gleichzeitig — und zwar mit unterschiedlicher Reichweite: Tiefe über die
   ganze Entrauschung (`end_percent 1.0`), Linien nur über die ersten 70 %. Die
   Begründung steht im Kommentar: „Material-Edges + Text-Lesbarkeit". Die Linienspur war
   die Antwort auf verlaufende Schrift und weiche Materialkanten. Wir haben nur Tiefe.
6. **Bereichsweise Konditionierung.** Pro Material eine eigene Schwarzweissmaske plus
   Teilprompt, bis zu acht Bereiche, wahlweise mit weichen Kanten. Haben wir nicht — ob
   wir es brauchen, ist offen.
7. **Nachbessern einer einzelnen Bildstelle.** Maske, weiche Kante, hoher Rauschanteil
   nur dort. Haben wir nicht.

---

## TEIL 4 · Beantworten sie offene Fragen von uns?

### 4.1 · Wie wurden Varianten erzeugt? — **Ja, klar beantwortet**

Fünf getrennte Sampler-Knoten in *einem* Bauplan, `seed = seed_base + Nummer`, alle
übrigen Parameter identisch, jeder mit eigenem Speicherknoten und eigenem Dateipräfix.
Kein Stapelverfahren im Latentraum, sondern fünf vollständige Läufe — das kostet Zeit,
macht aber jede Fassung einzeln wiederholbar. Dazu `locked_seed` für kontrollierte
Vergleiche (s. 3.1 D).

### 4.2 · Wie wurde die ControlNet-Stärke gewählt? — **Nach Augenmass, nicht gemessen**

Das ist ein klares Ergebnis, auch wenn es ein negatives ist. Es gibt **kein Messskript,
keine Tabelle, keine Metrik** hinter diesen Zahlen. Was es gibt, ist eine Kommentarspur
mit Datum und Begründung — und die ist trotzdem lehrreich:

| Grösse | vorher | nachher | begründet mit |
|---|---|---|---|
| Tiefensteuerung | 0.80 | **0.95** | „Geometry-Treue" |
| Liniensteuerung | 0.50 | **0.85** | „Material-Edges + Text-Lesbarkeit" |
| Führungsstärke | 6.5 | **5.0** | „gegen Über-Saturierung + Flach" |
| Schritte | 28 | **32** | „mehr Detail-Feinheit" |
| Stileinbettung | 0.75 | **0.85** | „Stil stärker" |
| Wirkdauer der Stileinbettung | 0.65 | **0.85** | „Stil länger wirken lassen" |
| Treue-Vorgabe | 0.5 | **0.35** | „mehr Cycles-Treue" |

**Der wertvollste Einzelbefund steht bei der Rauschabbildung.** Ursprünglich bildete der
Treue-Regler auf 0.18–0.55 ab. Der Kommentar zur Änderung — datiert, „nach Lauf 1" —
sagt wörtlich: *die KI-Fassungen waren fast identisch zum Cycles-Bild.* Das untere Ende
war so nah am Ausgangsbild, dass die KI-Stufe sichtbar nichts tat. Neu: **0.30–0.70**.

Daraus folgt eine übertragbare Erfahrung: **Unterhalb von etwa 0.30 Rauschanteil
verändert eine SDXL-Bild-zu-Bild-Stufe das Ausgangsbild nicht sichtbar.** Ein Regler, der
in seinem unteren Drittel nichts tut, sieht aus wie ein Befund — genau die Falle, die
unsere `backbone.py` beim Qwen-Eintrag schon einmal aufgeschrieben hat. Ob die Grenze bei
Z-Image-Turbo dort liegt, ist **nicht geprüft** und dürfte anders liegen: das Modell ist
destilliert und läuft auf acht Schritten.

Und noch eine stille Aussage: die Makroregler gehen bei der Tiefensteuerung **nie unter
0.45**, bei der Liniensteuerung nie unter 0.30. Die Bandbreite, die man dem Anwender
zutraut, ist enger als die technisch mögliche.

### 4.3 · Gibt es einen Beleg zur Tiefenkonvention? — **Nein, aber der Fund ist trotzdem wertvoll**

Das war die wichtigste Frage an diesen Bestand. Die Antwort in Stufen:

**(i) Der Altbestand schreibt exakt wie wir: nah = hell.**
In `archviz_multipass_render.py` steht die Rechnung offen da:
`g = 1.0 - ((v - near) / span)  # nah = 1.0`, Himmel und Unendlich auf 0 — also schwarz.
Identisch zu unserer `tiefe_norm.png`.

**(ii) Die Begründung daneben ist eine Behauptung, keine Messung.**
Der Kommentar lautet sinngemäss „nah = hell (typische ControlNet-Depth-Konvention)". Im
ETH-Bericht des Altbestands steht dieselbe Formulierung noch einmal: „**near=hell**
(ControlNet-Konvention)". Es gibt **im gesamten Altbestand keine Invertierung, kein
Vergleichsskript, keinen Messwert und keine Quellenangabe** dazu. Ich habe repo-weit nach
`invert`, `1.0 - depth`, `ImageInvert` und verwandten Formen gesucht; alle Treffer
betreffen anderes (Materialrauheit, Kamera-Vorzeichen, Rangumkehr im Bewerter).

**(iii) Die Tiefenkarte geht ohne jede Umrechnung in die Steuerung.**
Im ausgelieferten Qwen-Bauplan des Altbestands lädt Knoten 11 die Tiefen-PNG und reicht
sie unverändert an `ControlNetApplyAdvanced` (Stärke 0.8, über die gesamte Entrauschung).
Kein Zwischenschritt.

**(iv) Der Rückfallpfad ist der eigentliche Aufschluss.**
Fehlt die Blender-Tiefenkarte, schiebt der Altbestand das Beauty-Bild durch
`MiDaS-DepthMapPreprocessor` oder `DepthAnythingPreprocessor`. Beide liefern
**Disparität** — nah = hell. Und die dort geführten Steuermodelle
(`control_v11p_sdxl_depth`) sind auf genau solchen Vorverarbeiter-Ausgaben trainiert.
**Für jenen Stapel ist nah = hell mit hoher Wahrscheinlichkeit richtig.**

**(v) Und dazu passt eine Zahl.**
Der Altbestand misst Geometrietreue mit derselben Formel wie wir —
`sqrt(|spearman| · geom_iou)` — und berichtet für treue Renders **0.81–0.93** bei
nah = hell und ohne Invertierung. Unsere `geometrie_qa.py` hat die Schwelle 0.65 und die
Bandwerte 0.81–0.93 / 0.11 aus genau dieser Quelle. Auf **unserer** Kette liegt der
höchstmögliche Score dagegen bei **0.509** (`geometrie_qa.py`, Stand nach der
Schwellenstudie).

**Was daraus folgt — und das ist die eigentliche Antwort:**

Der Altbestand **widerspricht unserer Messung nicht.** Er betrifft andere ControlNets.
Zusammengenommen ergibt sich ein konsistentes Bild:

> Die Tiefenpolarität ist **keine Eigenschaft der Bildkette und keine Konvention des
> Feldes, sondern eine Eigenschaft des einzelnen ControlNets.** Die SD1.5/SDXL-Familie
> und die Qwen-Union sind auf Disparitätsausgaben trainiert und erwarten nah = hell —
> deshalb funktioniert der Altbestand ohne Invertierung und erreicht 0.81–0.93. Unsere
> Messung an `Z-Image-Turbo-Fun-Controlnet-Union` (|spearman| 0.38–0.52 gegen 0.79–0.85
> umgedreht, bei jeder Stärke rund das Doppelte) zeigt, dass die Fun-ControlNet-Familie
> es anders hält.

Damit ist auch der **Konstruktionsfehler des Altbestands** benannt: Er kennt kein Feld
für die Polarität. Er hat *eine* Annahme und wendet sie auf jedes Modell an. Unser
`backbone.tiefen_polaritaet` — ein Feld pro Eintrag, Vorgabe `POL_UNBEKANNT` — ist die
richtige Bauart, und der Altbestand belegt durch sein Fehlen, warum.

Was der Altbestand **nicht** liefert: einen Beleg. Wer gehofft hat, dort stünde eine
Messung, wird enttäuscht. Er liefert eine zweite, unabhängige Wiederholung derselben
ungeprüften Annahme — und erklärt damit immerhin, warum die Annahme so naheliegend war.

### 4.4 · Hat Qwen-Image-Edit eine echte ControlNet-Naht? — **Ja, und das war eine offene Frage von uns**

`backbone.py` hält beim Eintrag `qwen-image-edit-2511` ausdrücklich fest: *„Ob
Qwen-Image-Edit über einen anderen Weg eine Depth-ControlNet-Naht hat, ist NICHT
geprüft."* Der Altbestand beantwortet das.

Seine Modell-Registry führt für den Qwen-Weg vier Pflichtmodelle, darunter ein
**eigenständiges ControlNet**: `qwen_image_controlnet_union.safetensors`. Der Bauplan
verdrahtet es über einen regulären `ControlNetLoader` und `ControlNetApplyAdvanced`
(Knoten 30, Stärke 0.8) neben der Qwen-Edit-Konditionierung.

**Die Naht existiert also — aber nicht dort, wo wir gesucht haben.** Sie liegt in einem
*separaten ControlNet-Modell* (InstantX-Union für Qwen-Image), nicht in
`QwenImageEditPlusPipeline`. Unser Befund vom 18.08. — jene diffusers-Pipeline kennt
weder `control_image` noch `controlnet_conditioning_scale` — bleibt **richtig**; er war
nur nicht die ganze Geschichte.

Bemerkenswert an ihrem Bauplan: Rauschanteil **1.0**, also volle Neuerzeugung. Das
Beauty-Bild wirkt nicht als Bild-zu-Bild-Anker, sondern über die Edit-Konditionierung.
Das deckt sich mit unserer Beobachtung, dass die Tiefenkarte in jener Pipeline den
Beauty-Pass *ersetzt* statt ihn zu steuern.

**Was das für uns wert ist:** Ein weiterer Kandidat für
`docs/BACKBONE_CONTROLNET_2026-08-18.md`, und zwar einer, der beidseitig permissiv sein
könnte — Qwen-Image ist Apache-2.0, das Union-ControlNet müsste geprüft werden.
**Ich habe die Lizenz dieses ControlNets nicht geprüft** und die Naht nicht ausgeführt.
Kapitel 4.2 jener Doku hat Qwen-Image + InstantX-Union bereits als „lizenzrechtlich
sauber, an der Karte gescheitert" geführt — der Altbestand belegt, dass die Naht
technisch trägt, wenn die Karte reicht.

---

## TEIL 5 · Was dort nachweislich schiefgegangen ist

Die Spuren sind wertvoller als der Code. Neun Funde, mit Prüfweg.

**1. Der ganze Cycles-Render kam schwarz heraus.**
Die geladene Blender-Datei trug in ihrem Kompositor Normalisierungs- und
Umkehrungsknoten, die alle Werte auf 0 abbildeten. Der Fix: **vor** dem Multipass-Render
den Kompositor der Szene ausdrücklich auf `None` setzen.
*Für uns:* Wer in einem Blender-Runner eine fremde Datei öffnet, erbt deren
Nachbearbeitung. Ein Runner, der ein Bild herausschreibt, muss den Kompositor
ausdrücklich abschalten, sonst rechnet eine fremde Datei in unser Ergebnis hinein — und
das Ergebnis sieht nicht nach Fehler aus, sondern nach Bild.

**2. Der Treue-Regler tat in seinem unteren Drittel nichts.** — s. 4.2.
*Für uns:* die bereits in `backbone.py` beschriebene Falle, ein zweites Mal belegt.

**3. Der Dramatik-Regler war verkehrt herum.**
Kommentar: „CFG REVERSED 2026-05-16". Man hatte angenommen, mehr Dramatik brauche
*weniger* Führung. Beobachtet wurde das Gegenteil: Dramatik-Wörter im Prompt greifen nur
bei *hoher* Führungsstärke. Eine korrigierte Fehlannahme mit Datum — genau die Sorte, die
laut unserer Arbeitsregel ins Protokoll gehört.

**4. Modellgewichte mit 0 Byte führten zum Absturz.**
Die Erkennung filtert seither Dateien unter 1 MB heraus.
*Für uns:* `render.finde_einzeldatei_gewichte` prüft Existenz. Ob es
Grössenplausibilität prüft, **habe ich nicht nachgesehen** — das wäre eine billige
Härtung. Ein abgebrochener Download ist häufiger als eine fehlende Datei.

**5. Die Stilübertragung fiel still aus.**
Fehlende Zusatzpakete führten dazu, dass die Bildeinbettung wirkungslos blieb — das Bild
kam heraus, nur ohne Stil, ohne Fehlermeldung. Die Antwort im Code: ein Laufzeit-Check
gegen `/object_info`, **bevor** der Knoten in den Bauplan geschrieben wird.
*Für uns:* Ein optionaler Schritt, der bei Abwesenheit stillschweigend nichts tut, ist
schlimmer als einer, der abbricht. Unser `gate.py` folgt dem Grundsatz „Ablehnung ist ein
Ergebnis" bereits.

**6. Blenders Kompositor-Ausgabeknoten laufen beim Render nicht zuverlässig.**
Bereits in `BLENDER_ADDON_BESTAND_2026-08-18.md` Kap. C.1 vermerkt; die Auswertung dieser
Module bestätigt es aus zweiter Quelle.

**7. Ein Ausführungsfehler mit Namen: „Outputs:[]".**
In `kosmovis_render.py` steht dokumentiert, dass die Ausführung ohne explizit übergebene
Ausgabeknoten **leer durchlief und nichts rendert** — kein Fehler, kein Bild. Es dauerte
offenbar, bis das gefunden war.
*Für uns:* die allgemeine Form dieses Fehlers ist „Erfolg gemeldet, nichts getan". Genau
dagegen prüft unser `torwaechter.py`.

**8. Der grösste Bauartfehler: stiller Ausfall als Muster.**
Im Hauptoperator stehen **fünf** Stellen mit `except ImportError: pass`, teils mit dem
Kommentar „silent": Stil-Erweiterung, QA-Tor, Kostenprotokoll, Zusatztexturen,
Wasserzeichen. Der Lauf meldet am Ende „fertig, N Fassungen", auch wenn **Beipackdatei
und Kostenprotokoll nie geschrieben wurden**. Damit ist die Nachvollziehbarkeit, die
diese Module ausdrücklich anstreben, im Fehlerfall genau das, was zuerst wegfällt — ohne
dass jemand es merkt. Das ist die direkte Gegenthese zu unserer Arbeitsregel „Was nicht
in einer Datei steht, ist weg".

**9. Ein schlummernder Zählfehler.**
`num_variants` erlaubt Werte bis **8**. Das Einsammeln der Ergebnisse läuft über
`for i in range(1, 6)`, und es gibt nur Felder `variant_1_path` bis `variant_5_path`.
Wer sechs bis acht Fassungen anfordert, bekommt sie berechnet, bezahlt die Rechenzeit —
und **die Fassungen 6 bis 8 werden stillschweigend verworfen**. Ich habe keinen Hinweis
gefunden, dass das je aufgefallen ist.
*Für uns:* Wenn wir Variantenreihen bauen (3.3 Punkt 1), gehören Erzeugungsanzahl und
Einsammelanzahl an **eine** Stelle, nicht an zwei.

*Nebenbefund, uns nicht betreffend:* Die Lizenzprüfung des Altbestands fällt bei einem
`ImportError` in einen „Dev-Modus" mit dem Wasserzeichen `"DEV"` zurück. Die Prüfung lässt
sich also durch Löschen einer Datei umgehen.

---

## TEIL 6 · Was ich NICHT prüfen konnte

Ehrlichkeitshalber, weil dieser Bericht sonst mehr behauptet, als er belegt:

1. **Nichts davon wurde ausgeführt.** Kein ComfyUI, kein Blender, keine Modellgewichte.
   Alle Aussagen über Verhalten stammen aus Quelltext, Kommentaren und den
   Sitzungsnotizen des Altbestands — nicht aus Läufen.
2. **Die Lizenz von `qwen_image_controlnet_union.safetensors` habe ich nicht geprüft.**
   Für den Vorschlag in 4.4 ist das die entscheidende offene Frage.
3. **Die Lizenzen von `4x-UltraSharp.pth` und `4x_NMKD-Siax_200k.pth` habe ich nicht
   geprüft** — ich habe keine gefunden.
4. **Ob unser `finde_einzeldatei_gewichte` Dateigrössen prüft, habe ich nicht
   nachgesehen** (Befund 5.4).
5. **Die Denoise-Untergrenze ~0.30 gilt für SDXL-Bild-zu-Bild.** Ob bei Z-Image-Turbo
   eine vergleichbare Grenze existiert und wo sie liegt, ist ungeprüft.
6. **Die drei anderen Bauplanzeichner** (Mehrstufe, Nachbesserung, Krea) habe ich in
   ihrer Struktur gelesen, aber nicht Knoten für Knoten geprüft. Für die Empfehlung „nicht
   übernehmen" reicht das; für ein Nachbauen reichte es nicht.
7. **`archviz_variant_scorer.py` und `archviz_exposure_check.py`** — die beiden Module,
   in denen die in 3.3 gelobte Rechnung tatsächlich steckt — **habe ich nicht geöffnet.**
   Sie stehen ebenfalls in der Nicht-ausgewertet-Liste von Kap. C.4 und sind nach dieser
   Auswertung die nächstwichtigsten. Meine Aussagen über sie stammen aus ihren
   Aufrufstellen.
8. **Der Vergleich 0.81–0.93 (alt) gegen max. 0.509 (wir)** ist ein Vergleich zweier
   Berichte, nicht zweier Läufe auf derselben Szene. Er stützt die Deutung in 4.3, er
   beweist sie nicht.

---

## TEIL 7 · Was ich empfehle

**Sofort, ohne Bau:**

1. **`docs/BLENDER_ADDON_BESTAND_2026-08-18.md` um den Befund aus 0.2 ergänzen:**
   `kosmovis_render.py` importiert GPL-3.0-Code von ComfyUI und ist damit für uns
   gesperrt. Kapitel C.4 kann für die beiden hier ausgewerteten Module auf dieses
   Dokument verweisen.
2. **`backbone.py` beim Qwen-Eintrag um 4.4 ergänzen:** die ControlNet-Naht existiert als
   separates Union-Modell; die Notiz „nicht geprüft" wird zu „geprüft: existiert
   ausserhalb der Edit-Pipeline, Lizenz offen".
3. **Kapitel 6 von `docs/BACKBONE_CONTROLNET_2026-08-18.md`** („Was offen blieb", Punkt
   Tiefenkonvention) um die Deutung aus 4.3 ergänzen: der Altbestand liefert keinen
   Beleg, aber eine konsistente Gegenprobe für die SDXL/Qwen-Familie.

**Als nächste Auswertung:** `archviz_variant_scorer.py` und `archviz_exposure_check.py`.
Sie sind klein, `bpy`-frei und enthalten genau die drei Fähigkeiten, die uns nach 3.3 am
meisten fehlen.

**Als nächster Bau, in dieser Reihenfolge:**
Fortschrittsgrenze (3.1 A) → Variantenreihe mit festem Startwert (3.3 Punkt 1 + 3.1 D) →
Vergleich der Reihe gegen sich selbst (3.3 Punkt 2) → Beipackdatei (3.1 C).

---

## Was ins Lexikon gehört

Begriffe, die in diesem Bericht vorkommen und in `docs/LEXIKON.md` **fehlen** (geprüft
durch Suche in der Datei). Nicht selbst eingetragen — zur Aufnahme in derselben Sitzung:

| Begriff | worum es geht |
|---|---|
| **Bildeinbettung / IP-Adapter** | Verfahren, das den *Stil* eines Referenzbilds übernimmt, statt ihn in Worten zu beschreiben. Im Altbestand die zweite Steuerspur neben der Tiefe. |
| **Linienzeichnung als Steuerspur (Lineart)** | Ein zweites ControlNet, das Kanten statt Tiefe vorgibt. Im Altbestand die Antwort auf verlaufende Schrift und weiche Materialkanten. |
| **Bereichsweise Konditionierung (Regional Conditioning)** | Verschiedene Bildbereiche bekommen über Masken verschiedene Teilprompts. |
| **Nachbessern einer Bildstelle (Inpainting)** | Nur ein maskierter Ausschnitt wird neu erzeugt, der Rest bleibt unverändert. Kommt in `LEXIKON.md` einmal vor, aber ohne eigenen Eintrag. |
| **Sampler und Zeitplan (Scheduler)** | Das Verfahren, mit dem aus Rauschen schrittweise ein Bild wird, und die Verteilung der Schritte darauf. `Scheduler` ist belegt, `Sampler` fehlt. |
| **Fortschrittsgrenze (no-progress timeout)** | Zeitgrenze nicht auf die Gesamtdauer, sondern auf den Stillstand — fängt ein hängendes, nicht abgestürztes Backend. |
| **Disparität** | Der Kehrwert der Entfernung. Der Grund, warum Tiefenschätzer üblicherweise nah = hell ausgeben — und damit der Schlüssel zur ganzen Polaritätsfrage. |
| **Destilliertes Modell (Turbo)** | Ein auf wenige Schritte eingedampftes Modell. Erklärt, warum bei Z-Image-Turbo die Führungsstärke 0.0 richtig ist und ein Negativprompt nichts ausrichtet. |
| **Beipackdatei (Sidecar)** | Eine Datei, die neben einer Ausgabedatei liegt und beschreibt, wie diese entstanden ist. |
| **Kachelweise Vergrösserung (Tile-Upscale)** | Ein Bild wird stückweise vergrössert und nachgeschärft. `Tile` und `Kachel` kommen vor, der Begriff fehlt. |
| **GGUF** | Ein Dateiformat für platzsparend abgelegte Modellgewichte. Einmal erwähnt, nicht erklärt. |
