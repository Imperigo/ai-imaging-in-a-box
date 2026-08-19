# Der Renderauftrag — Entwurf zur Entscheidung

**19.08.2026 · unser Stand gegen `KosmoVis/docs/RENDER_SCENE_CONTRACT.md` (v1, 2026-06-16)**

Dies ist ein **Entwurf, kein Bau.** Es wurde kein Modul geändert und keine Zeile Code
geschrieben. Was hier steht, ist ein Vorschlag mit Begründungen — er will
widersprochen werden, bevor er umgesetzt wird.

Gelesen wurden: der fremde Vertrag, seine Bedienung in `KosmoVis/01_workflow/render_scene.py`
(die Bestandsaufnahme hatte sie nicht geöffnet), `integrations/odysseus/kosmovis_mcp_server.py`,
und auf unserer Seite `render.py`, `mcp_schemas.py`, `prompts.py`, `kameras.py`,
`backbone.py`, `contracts.py`, `seams.py`, `kosmo_naht.py`, `gate.py`, `geometrie_qa.py`,
`stil_qa.py`, `runners/blender_depth_stage.py` sowie die Messreihe `auf-20260818-13`.

Am fremden Repo wurde **nichts** geändert; ein `git reset --hard` war nicht nötig, der
Arbeitsbaum war vollständig (314 verfolgte Dateien in KosmoVis).

---

## 0 · Kurzfassung

1. **Der fremde Vertrag kann sieben Dinge, die wir nicht können** — und das wichtigste ist
   nicht `faithful`, sondern dass er die **Mehrzahl** kennt: mehrere Kameras, mehrere
   Sonnenstände, ein Verzeichnis statt einer Datei. Unser `RenderAuftrag` beschreibt
   **genau ein Bild ohne Namen**. Für den „start imaging"-Knoten der Demo-Vision ist das
   die eigentliche Lücke.
2. **Wir können neun Dinge, die er nicht kann** — und das wichtigste ist nicht die
   Tiefenpolarität, sondern der **Seed**. Der fremde Vertrag führt keinen. Damit ist dort
   kein einziger Lauf wiederholbar. Für ein Produkt verzeihlich, für eine
   Vertiefungsarbeit tödlich.
3. **`faithful` als eine Zahl: nein.** Nicht weil die Idee schlecht wäre, sondern weil
   unsere eigene Messung sie widerlegt: Die ControlNet-Stärke wirkt **nicht monoton**
   (0.80 schlägt 1.00), und sie ist nur einer von drei Reglern, von denen einer
   (`denoise`) je nach Betriebsart gar nicht wirkt. Ein Schieber, dessen Beschriftung
   „mehr = treuer" verspricht, verspricht damit etwas Ungemessenes. Vorschlag:
   **benannte Punkte statt einer Zahl**, und das Wort „treu" bleibt der **gemessenen
   Ausgabe** vorbehalten.
4. **Der Auftrag trägt Verweise, das Ergebnis trägt aufgelöste Werte.** Das ist die eine
   Regel, aus der die Naht zur Oberfläche folgt.
5. **Drei Dinge, die im fremden Ergebnis fehlen und ohne die ein Lauf nicht
   nachvollziehbar ist:** die Bild-Prüfsumme, die Fassung der Gewichte, und die Liste der
   Argumente, die die Pipeline **wirklich genommen** hat.

---

# TEIL 1 · Was der fremde Vertrag kann, was unserer nicht kann

## 1.1 · Die drei Punkte aus der Bestandsaufnahme, nachgeprüft

### `faithful` als eine Zahl — stimmt, und die Bestandsaufnahme hat es zu freundlich beurteilt

Die Bestandsaufnahme nennt es „ein guter Entwurf". Nachgeprüft in
`KosmoVis/01_workflow/render_scene.py:222-225`:

```python
faithful = (scene.get("render") or {}).get("faithful")
if isinstance(faithful, (int, float)):
    cmd += ["--strength", str(float(faithful))]
```

`faithful` ist also **nicht** ein abstrakter Regler, der auf mehrere Parameter aufgelöst
wird. Er wird **eins zu eins** als ControlNet-Stärke durchgereicht, unter einem anderen
Namen. Das ist weniger, als der Kommentar im Vertrag („1.0=Cycles-treu ↔ 0.0=KI-frei")
verspricht, und es ist der Kern des Einwands in Teil 3.

**Zusatzbefund, der in der Bestandsaufnahme fehlt:** Derselbe Vertrag führt eine **zweite**
Angabe für dieselbe Achse — `vis.skip=true` heisst „nur Cycles-Multipass, kein KI-Schritt".
Das ist genau der Punkt, den `faithful=1.0` beschreiben soll. Zwei Felder für einen
Endpunkt, ohne Regel, welches gewinnt. Bei uns hat dieselbe Aussage einen sauberen Ort:
Sie ist die **Abwesenheit des Render-Knotens** in der Kette (`kette.py`), nicht ein Feld.

### `depth_method` in der Ausgabe — stimmt, und es ist der beste Gedanke des Vertrags

`compositor_z | foreach_z | emission_fallback`. Die Ausgabe sagt, wie sie entstanden ist.

Das deckt sich mit E.2/8 der Bestandsaufnahme („die Ausgabe schreibt mit, welcher Weg
gegriffen hat") und mit unserer eigenen Linie: `blender-report.json` führt bereits
`depth_exr_kanaele`, `depth_exr_format`, `depth_normalisierung`, `kamera` (Herkunft:
vorgegeben / abgeleitet / Rückfall). Wir haben die Bauart, aber **nicht das Feld** — und
vor allem reicht sie nicht bis ins Renderergebnis. Der Bericht bleibt im Multipass-Ordner
liegen; `render.rendere` weiss nichts von ihm.

### `cameras: "auto"` als Verweis auf die zwölf Richtungen — stimmt, und die Kürzel decken sich wörtlich

Das Beispiel im Vertrag nennt `["n","sSE",...]`. Beide Kürzel stehen in unserer
`kameras.RICHTUNGSFOLGE` (`"n","e","s","w","nNE","eEN","eES","sSE","sSW","wWS","wWN","nNW"`).
Der Kreis schliesst sich tatsächlich.

**Einschränkung:** `"saved"` — die dritte zulässige Angabe — verweist auf in einer
`.blend` gespeicherte Kameras. Das können wir nicht und sollten es nicht wollen: Es setzt
eine Blender-Datei als Zustandsträger voraus (Regel 4) und macht den Auftrag von etwas
abhängig, das nicht im Auftrag steht.

## 1.2 · Was ich sonst noch finde — Feld für Feld

Legende der Spalte „bei uns": ✅ vorhanden · ⚠️ vorhanden, aber woanders/schwächer · ❌ fehlt.

### Eingang

| Feld drüben | Was es leistet | Bei uns | Befund |
|---|---|---|---|
| `schema` | Fassungskennung, defensives Lesen | ✅ `contracts.SCHEMA_ID = "aiimaging.render-scene/v1"` | Wir haben es, und der Name ist bis auf das Präfix identisch. Das ist kein Zufall — es ist dieselbe Idee. |
| `project` | Ein Name für den Lauf | ❌ | Fehlt. Unter Regel 3 heikel, aber als **Feld** zulässig: Verboten sind echte Namen im Repo, nicht das Feld, in das der Owner zur Laufzeit einen schreibt. Ohne es tragen zwölf Ausgabeverzeichnisse keinen gemeinsamen Bezug. |
| `geometry.path` + `format` | glb **oder fbx oder .blend** | ⚠️ `geometry.{ifc_path,glb_path,up_axis,bbox}` | Unseres ist **präziser** (Up-Achse wird nicht geraten, Hüllbox für den Torwächter), ihres ist **breiter** (fbx, fertige Szene). fbx und `.blend` würde ich nicht übernehmen: `.blend` ist wieder ein Zustandsträger ausserhalb des Auftrags. |
| `cameras` | „auto" / „saved" / Liste | ❌ **im Auftrag** | `kameras.kamerasatz` rechnet die zwölf, `seams` nimmt `--kamera <kürzel>` für **eine**. Aber der `RenderAuftrag` kennt keine Kamera, nicht einmal ihren Namen. **Das ist die grösste Lücke.** |
| `render.resolution: [b,h]` | Ein **Paar** — trägt das Seitenverhältnis | ⚠️ `aufloesung: int` | Unsere Auflösung ist **eine Zahl** und damit zwingend quadratisch (`blender_depth_stage.py:658`: `resolution_x = resolution_y = a.aufloesung`). Siehe 1.3 — das ist eine echte Verarmung mit Folgen bis in die Kamerarechnung. |
| `render.samples` | Cycles-Samples | ⚠️ im MCP-Schema und in `seams`, nicht im `RenderAuftrag` | Richtig getrennt bei uns — aber es gibt keinen Ort, an dem beides zusammen steht. |
| `render.faithful` | Ein Treue-Regler | ⚠️ `controlnet_staerke` | Siehe Teil 3. |
| `render.sun{lat,lon,datetime,presets}` | **Sonnenstand aus Ort und Zeit** | ❌ | Bei uns ist die Sonne im Runner **fest verdrahtet** (`_sonne_setzen`: 50° Höhe, 35° Azimut, mit dem Kommentar „bewusst schlicht"). Für einen Messschnitt richtig, für ein Wettbewerbsbild unbrauchbar. Und `presets: ["morgen","mittag","abend"]` ist eine **Liste** — siehe 1.4. |
| `style.mode: none\|redux\|ipadapter\|lora` | **Wie** der Stil übertragen wird | ❌ | Wir kennen nur den Prompt-Weg. `lora.py` **trainiert** LoRAs, wendet aber keine an; `RenderAuftrag` hat kein LoRA-Feld. IP-Adapter und Redux gar nicht. |
| `style.refs` | Referenzbilder für die Übertragung | ⚠️ mit umgekehrtem Vorzeichen | Bei uns sind Referenzbilder die **Messlatte** (`stil_qa.stil_gate_aus_bildern`), drüben das **Ausgangsmaterial**. Siehe 1.5 — daraus folgt eine Warnung. |
| `style.prompt` | Freitext | ✅ und deutlich weiter | `prompts.komponiere` mit sieben Kategorien, Bauteilwächter, Negativ-Prompt, Warnungen. |
| `vis.skip` | Nur Cycles, kein KI-Schritt | ⚠️ als Kettenform | Bei uns die Abwesenheit eines Knotens. Sauberer, aber nicht als Feld ansprechbar — ein Preset-Knoten müsste den Graphen umbauen, nicht ein Häkchen setzen. |
| `vis.backbone` | Modellwahl | ✅ und strenger | Unsere Registry prüft Lizenz, Konditionierung, Dateien, ControlNet-Lizenz. |
| `vis.upscale: none\|seedvr2\|supir` | Nachvergrösserung | ❌ | Haben wir nicht. **Und ich würde es nicht übernehmen, ohne die Lizenzen zu prüfen** — SeedVR2 und SUPIR sind bei uns nirgends geprüft (Regel 1). Als Feld mit `"none"` als einziger heute gültiger Angabe wäre es ehrlich. |
| `out` | Ausgabe**verzeichnis** | ⚠️ `out_dir` (MCP) / `ausgabe_png` (Auftrag) | Unser `RenderAuftrag` schreibt **eine Datei**. Bei zwölf Kameras mal drei Varianten braucht es ein Verzeichnis **plus Namensschema**, sonst überschreiben sich Läufe. |

### Ausgang

| Feld drüben | Bei uns | Befund |
|---|---|---|
| `cameras[]` — Ergebnis **je Kamera** | ❌ | Unser Ergebnis ist ein flaches Wörterbuch für ein Bild. Der Demoplan sagt es schon: „Unser Gate urteilt über ein Bild ohne Namen." |
| `passes{beauty,depth,material,material_id}` | ⚠️ in `blender-report.json` | Vorhanden, aber im Multipass-Bericht, nicht im Renderergebnis. Zwei Dateien, die niemand zusammenführt. |
| `depth_method` | ❌ als Feld | Siehe oben. |
| `ai_variant` | ⚠️ `bild_png` | Ihres ist ausdrücklich **nullbar bei `vis.skip`** — die Aussage „kein KI-Schritt" ist unterscheidbar von „KI-Schritt fehlgeschlagen". Bei uns fällt beides auf `bild_png=None`. |
| `qa{ok,notes}` | ✅ und weit reicher | Siehe 1.6 — hier ist unser Stand dem Vertrag **überlegen**, und zwar messbar. |
| `engine{blender,comfyui,backbone}` | ❌ | Wir haben `blender` im Multipass-Bericht und `python/torch/diffusers` im HomeStation-Ergebnissatz (`auf-20260818-13.json:umgebung`), aber nichts davon im Renderergebnis. |
| `cost{gpu_peak_w,wall_s,cloud_chf}` | ⚠️ `dauer_s` | `gpu_peak_w` fehlt ganz — obwohl wir eine **400-W-Leistungsgrenze** führen. `vram_spitze_mib` haben wir nur im HomeStation-Satz. |
| `status: ok\|partial\|failed` | ⚠️ `ok\|abgelehnt\|fehler` | **Beide Seiten haben je einen Zustand, der dem anderen fehlt.** Siehe 1.7. |

## 1.3 · Der Befund, den ich für den unangenehmsten halte: das Seitenverhältnis

Drüben ist die Auflösung ein Paar `[1920, 1440]` und trägt damit das Seitenverhältnis
(4:3). Bei uns ist sie **eine Zahl**, und die Kette rendert zwingend quadratisch.

Das ist keine Kosmetik, und `prompts.Stil` sagt selbst, warum:

> Der vertikale Bildwinkel folgt aus dem Seitenverhältnis (`kameras.bildwinkel`), und
> damit auch der Abstand, aus dem ein Bauwerk gerahmt wird.

Heute stehen drei Stellen mit drei verschiedenen Antworten nebeneinander:

| Stelle | Wert | Herkunft |
|---|---|---|
| `kameras.kamerasatz(seitenverhaeltnis=…)` | **16/9** als öffentliche Vorgabe | Setzung |
| `runners/blender_depth_stage.py:265` | **1.0**, fest verdrahtet, mit Kommentar „der Runner rendert quadratisch" | Setzung |
| `prompts.Stil.seitenverhaeltnis` | `1.0` bei `kosmo_standard`, sonst `None` | aus der Stilanalyse abgeleitet |

Der Runner reicht 1.0 korrekt an die Kamerarechnung durch — die Kette ist also **nicht
falsch**, sie ist **festgenagelt**. Die Folge: `Stil.seitenverhaeltnis` ist heute ein
Feld, **das niemand liest**. Ein Stil mit hochformatiger Vorgabe liesse sich nicht
rendern, und die einzige Stelle, an der das auffiele, ist eine Bildkomposition, die
niemand mit dieser Ursache in Verbindung bringt.

**Daraus folgt für den Entwurf:** Das Seitenverhältnis ist **ein** Feld des Auftrags, aus
dem drei Stellen bedient werden (Kamerarechnung, Blender-Auflösung, Bildmodell-Auflösung).
Nicht drei Felder, die man abgleichen muss.

## 1.4 · Der übersehene Punkt: der fremde Vertrag kennt die Mehrzahl, unserer nicht

Drei Felder drüben nehmen eine **Liste** entgegen:

* `cameras` — mehrere Ansichten,
* `sun.presets: ["morgen","mittag","abend"]` — mehrere Lichtstimmungen,
* `style.refs` — mehrere Referenzen.

Damit ist die **Variantenerzeugung im Vertrag angelegt**, ohne dass der Auftrag mehrfach
geschrieben werden müsste. Genau das verlangt die Demo-Vision vom Ausgabeknoten
(„start imaging" erzeugt n Bilder, Varianten).

Unser `RenderAuftrag` ist demgegenüber der **Atom-Auftrag**: ein Bild, ein Modellaufruf,
eine Datei. Das ist eine gute Eigenschaft und soll bleiben — er ist die
Wiederholvorschrift, und eine Wiederholvorschrift für drei Bilder wäre keine. Aber
darüber fehlt eine Schicht.

**Und daran hängt mehr als Bequemlichkeit:** Unser Freigabe-Token (`jobs.py`,
`CONFIRMED_RENDER_*`) gibt heute **einen Auftrag** frei. Sobald ein Auftrag n Bilder
aufspannt, gibt dasselbe Token n GPU-Läufe frei — und wie viele das sind, weiss der
Freigebende nur, wenn der Auftrag es **vor** dem Lauf ausrechnen kann. Der Entwurf braucht
deshalb eine Funktion, die aus einem Auftrag die Bildzahl bestimmt, ohne ihn auszuführen.

## 1.5 · Referenzbilder: dasselbe Material, entgegengesetzte Rolle — und eine Warnung

Drüben sind `style.refs` das **Ausgangsmaterial** der Stilübertragung (Redux, IP-Adapter,
LoRA). Bei uns sind Referenzbilder die **Messlatte** der Stil-QA.

Wenn beides derselbe Bilderstapel ist, misst das Gate seine eigene Vorgabe. Der Stil-Score
stiege, ohne dass irgendetwas besser würde — und das Doppel-Gate verlöre genau die Hälfte,
die es einmal gerettet hat. Dieselbe Klasse von Fehler, die `gate.py` in seinem
Eröffnungsabschnitt beschreibt: eine Zahl, die den Fehler belohnt, den sie finden soll.

**Für den Entwurf heisst das:** Wenn ein Feld für Stilreferenzen entsteht, muss es
**zwei** Felder sein — `stil_referenzen` (Erzeugung) und `qa_referenzen` (Messung) —, und
das Ergebnis muss melden, wenn sie sich überschneiden. Ich bin unsicher, ob eine
Überschneidung ganz verboten werden sollte: Sie ist manchmal genau das, was jemand will
(„mach es wie diese fünf Bilder, und miss, ob es geklappt hat"). Gemeldet gehört sie auf
jeden Fall.

## 1.6 · Wo der fremde Vertrag hinter seinem eigenen Repo zurückbleibt

Dies ist ein Befund über den Vertrag, nicht über KosmoVis. In demselben Repo stehen
**zwei** Ergebnisformate:

* `render-scene-result.json` (der Vertrag) mit `qa: {ok, notes}`,
* `render-result.json` (Fassung v2), das `kosmovis_query_qa_verdict` liest — mit
  `released`, `passed`, `style_passed`, `geometry_passed`, `style_status`,
  `geometry_status`, `style_score`, `geometry_fidelity`, `style_threshold`,
  `geometry_threshold`, `fail_reasons`.

Und `render_scene.py:251-268` baut das erste aus dem zweiten. Der entscheidende Ausschnitt:

```python
notes = f"style={style} geom={geom}"
if reasons:
    notes += f" fail={','.join(reasons)}"
```

**Zwei Messwerte und eine Begründungsliste werden in eine formatierte Zeichenkette
gegossen.** Wer das Ergebnis später auswertet, muss den Satz wieder zerlegen — und
verliert dabei die Unterscheidung zwischen „nicht gemessen" und „gemessen und
durchgefallen", die `gate.als_kosmovis_verdikt` ausdrücklich führt.

**Der Vertrag ist an dieser Stelle älter als das MCP-Werkzeug desselben Repos.** Wir haben
mit `als_kosmovis_verdikt` bereits die reichere Form — die Landestelle, die wir bedienen,
ist die richtige. Für unser eigenes Ergebnis folgt daraus die schärfste Regel des Teils 5:
**Zahlen kommen nie in Prosa.**

## 1.7 · Die Statuswörter: jede Seite hat eines, das der anderen fehlt

| Zustand | Drüben | Bei uns | Bedeutung |
|---|---|---|---|
| `ok` / `ok` | ✅ | ✅ | gerechnet, gelungen |
| `failed` / `fehler` | ✅ | ✅ | versucht, schiefgegangen |
| `partial` | ✅ | ❌ | **Ein Teil gelang.** Bei zwölf Kameras, von denen drei durchfallen, ist das der wahre Zustand. |
| `abgelehnt` | ❌ | ✅ | **Es wurde gar nicht gerechnet**, weil der Auftrag den Vertrag verletzt (Regel 1, fehlende Eingabe, unsinniger Parameter). Drüben fiele das unter `failed` — und ein Lizenzverstoss sähe dann aus wie ein Absturz. |

Beide gehören in den Entwurf. `partial` ist die unmittelbare Folge davon, dass ein Auftrag
mehrere Bilder aufspannt; `abgelehnt` ist der Zustand, ohne den Regel 1 im Protokoll nicht
von einem Defekt unterscheidbar wäre.

---

# TEIL 2 · Was unserer kann, was der fremde nicht kann

Der Fairness halber zuerst der Punkt, der uns am meisten voraus ist — er stand nicht in
der Aufgabenstellung.

## 2.1 · Der Seed. Der fremde Vertrag hat keinen.

Weder im Eingang noch in der Ausgabe steht ein Startwert des Zufalls. Damit ist **kein
einziger Lauf drüben wiederholbar**: Zwei Aufrufe mit identischem `render-scene.json`
ergeben zwei verschiedene Bilder, und kein Feld sagt, worin sie sich unterschieden.

Für ein Produkt ist das verzeihlich — man nimmt das Bild, das gefällt. Für eine
Vertiefungsarbeit ist es das Ende: Die ganze Schwellenstudie beruht darauf, dass genau ein
Parameter sich ändert und alles andere gleich bleibt. `render.py` sagt es in seiner
Dokumentation selbst: „Ohne ihn ist ein Render nicht wiederholbar, und ohne
Wiederholbarkeit gibt es keine Schwellenstudie."

**Das ist der eine Punkt, an dem wir nichts übernehmen dürfen, sondern der fremde Vertrag
von uns lernen müsste.**

## 2.2 · Die Tiefenpolarität (`tiefen_polaritaet`)

Der fremde Vertrag führt `depth` als Pass und `depth_method` als Herkunft — aber nirgends,
**welche Konvention** die Karte trägt und welche das ControlNet erwartet. Bei uns steht
beides:

* `backbone.Backbone.tiefen_polaritaet` — was das Modell erwartet (`nah_hell`,
  `nah_dunkel`, `unbekannt`),
* `backbone.UNSERE_POLARITAET` — was der Multipass schreibt,
* `render._baue_parameter` schreibt `tiefen_polaritaet_modell` **und** `tiefe_invertiert`
  in den Parametersatz,
* `render._hinweise` sagt bei `unbekannt` ausdrücklich, dass **nicht** gedreht wird und
  ein schlechter Score daran liegen könnte.

Und es ist gemessen, nicht behauptet (`auf-20260818-13`): |spearman| springt von 0.38–0.52
auf 0.79–0.85, wenn die Karte gedreht wird. Rund das Doppelte, bei **jeder**
ControlNet-Stärke.

Der Punkt, der über das Feld hinausgeht: **Keine Modellkarte sagt diese Konvention.** Ein
Vertrag, der sie nicht führt, macht einen unsichtbaren Faktor zu einer stillen Annahme —
und eine verkehrte Polarität sieht aus wie ein Problem des Bildmodells, während sie eines
der Übergabe ist.

## 2.3 · Die Führung (`fuehrung` / `guidance_scale`)

Drüben nicht vorhanden. Bei uns ein Feld mit drei Eigenschaften, die zusammengehören:

* **Auftrag schlägt Registry schlägt fremde Vorgabe** — und `None` bleibt `None`, statt
  durch einen Ersatzwert ersetzt zu werden, der eine Messung vortäuschte.
* **Bei einem destillierten Turbo-Modell ist die diffusers-Vorgabe nachweislich falsch**
  (`z-image-turbo` läuft mit 0.0; 5.0 überzeichnet).
* **Unterhalb von 1.0 ist der negative Prompt wirkungslos.** Er steht im Protokoll und
  nicht im Bild — und `render._hinweise` sagt genau das, statt es geschehen zu lassen.

Der letzte Punkt ist die eigentliche Leistung: Es ist eine **stille** Unwirksamkeit, und
ohne das Feld gäbe es keinen Ort, an dem sie auffallen könnte.

## 2.4 · Messtaugliche und nicht messtaugliche Stile (`treue_geeignet`)

Der fremde Vertrag kennt `style.mode` und `style.prompt` — beides Fragen der Erzeugung.
Die Frage, **ob ein Stil überhaupt gemessen werden darf**, kommt dort nicht vor.

Bei uns ist sie ein Feld je Stil, mit Begründung je Fall:

| Stil | `treue_geeignet` | Warum |
|---|---|---|
| `messschnitt` | ✅ | erfindet so wenig wie möglich; **jede Schwellenmessung gehört hierauf** |
| `wettbewerb`, `modellfoto` | ✅ | präzise Oberflächen, klare Silhouette |
| `abendstimmung` | ❌ | Schlagschatten liest der Tiefenschätzer als Fläche |
| `morgennebel` | ❌ | Nebel verdeckt den Fuss; `geom_iou` misst danach den Nebel |
| `einskizziert` | ❌ | offene Kanten sind der **Zweck**; eine niedrige Zahl ist die Beschreibung des Stils |
| `kosmo_standard` | ❌ | Vordergrundbewuchs verdeckt die Silhouette systematisch |

Das ist mehr als eine Kennzeichnung: Es ist die Trennung von **Messstil** und
**Hausstil** (`MESS_STIL = "messschnitt"`, `HAUS_STIL = "kosmo_standard"`), und der
Kommentar dazu ist die Begründung:

> Gemessen wird auf dem Stil, der am wenigsten erfindet; ausgeliefert wird der, der
> aussieht wie das Büro. Wer beides in einen Stil zwingt, bekommt entweder unbrauchbare
> Bilder oder unbrauchbare Zahlen.

Ein Vertrag ohne dieses Feld lässt zu, dass jemand `abendstimmung` misst, 0.19 bekommt und
das Bildmodell verdächtigt.

## 2.5 · Die zweiseitige ControlNet-Lizenz

Der fremde Vertrag nennt `vis.backbone` als **einen** Namen. Unsere Registry hält fest,
dass ein Depth-ControlNet **nie ein Modell, sondern immer zwei** ist:

```
controlnet_id, controlnet_lizenz, controlnet_lizenz_quelle
```

mit dem Kommentar, der das Loch benennt: „Ein Apache-2.0-Basismodell mit einem
nicht-kommerziellen ControlNet ergibt eine nicht-kommerzielle Kette, und `pruefe_lizenz`
hätte ‚zulässig' gemeldet." Bei FLUX ist genau das der Fall — alle drei verbreiteten
Depth-ControlNets sind selbst nicht kommerziell lizenziert.

`None` heisst dort ausdrücklich **nicht** „keines nötig", sondern „noch nicht benannt", und
ist bei `depth_controlnet` ein gemeldeter Mangel. Ein Vertrag, der eine Modellwahl als
einen Namen führt, kann Regel 1 nur halb prüfen.

## 2.6 · Fünf weitere Punkte, kürzer

**Der Bauteilwächter** (`prompts.bauteilwaechter`). Er prüft freien Prompt-Text auf
Bauteilwörter und meldet Funde — weil ein Prompt, der Bauteile nennt, die die Geometrie
nicht hat, eine Aufforderung zur Halluzination ist. Am Gerät gelernt (`auf-20260818-09`:
„clean flat roof" für einen oben offenen Quader ergab ein Dach). Drüben ist `style.prompt`
ein Textfeld ohne Prüfung.

**Die Konditionierungsart als Feld** (`konditionierung`). Ob ein Backbone überhaupt eine
Depth-ControlNet-Naht hat, ist bei uns eine Registry-Angabe und wird **vor** dem Laden
geprüft. Drüben ist `backbone` ein Name — und `auf-20260818-09` hat gezeigt, was passiert,
wenn man das nicht prüft: `QwenImageEditPlusPipeline` kennt `controlnet_conditioning_scale`
gar nicht, drei verschiedene Stärken ergaben auf zwölf Stellen denselben Score.

**Die Ablehnung als Ergebnis, nicht als Ausnahme.** `render.rendere` liefert bei einem
Lizenzverstoss `status='abgelehnt'` **mit vollständigem Parametersatz**. Eine Ausnahme
kann jemand fangen und weiterlaufen; ein protokolliertes `abgelehnt` nicht.

**Der Torwächter vor der GPU** (`torwaechter.py`, `approval_token`). Massstab und
Georeferenz werden geprüft, **bevor** GPU-Zeit verbraucht wird. Der fremde Vertrag hat den
Leerlauf-Gatter (400-W-Cap), aber keine Prüfung der Geometrie.

**Die Herkunft der Geometrie** (`herkunft.py`). Erzeugendes Programm, Einheit,
SI-Vorsatz, Up-Achse — an 40 echten Dateien gemessen. Drüben ist `geometry.format` ein
Wort aus drei Möglichkeiten.

---

# TEIL 3 · Ist `faithful` als eine Zahl eine gute Idee?

**Nein.** Nicht als Feld des Auftrags. Als Bedienelement der Oberfläche ja — aber dann
muss die Übersetzung in den Auftrag benannt, versioniert und im Ergebnis nachlesbar sein.

Fünf Gründe, vom stärksten zum schwächsten.

## 3.1 · Die Wirkung ist nicht monoton — gemessen, nicht vermutet

`auf-20260818-13`, HomeStation, z-image-turbo mit Fun-ControlNet-Union, 512×512, 8 Schritte,
Seed 12345, Führung 0.0, derselbe Prompt, dieselbe Geometrie. Sechs Läufe, alle sechs
Prüfsummen verschieden — der Regler wirkt also wirklich.

| Polarität | ControlNet-Stärke | `score` | `spearman` | `geom_iou` | gemeinsame Punkte |
|---|---:|---:|---:|---:|---:|
| invertiert (die richtige) | 0.65 | 0.2355 | −0.8481 | 0.0654 | 2916 |
| invertiert | **0.80** | **0.2649** | **−0.8529** | **0.0823** | 3670 |
| invertiert | 1.00 | 0.2421 | −0.7939 | 0.0738 | 3294 |
| wie wir (die falsche) | 0.65 | 0.1153 | −0.5186 | 0.0256 | 1143 |
| wie wir | 0.80 | 0.1149 | −0.5176 | 0.0255 | 1137 |
| wie wir | 1.00 | 0.0752 | −0.3802 | 0.0149 | 664 |

**Die entscheidende Zeile ist die mittlere Gruppe:** Bei der richtigen Polarität ist 0.80
besser als 0.65 **und** besser als 1.00. Die Kurve hat ein Maximum in der Mitte.

Ein Feld namens `faithful` mit „1.0 = renderer-treu" verspricht, dass die gemessene Treue
steigt, wenn man den Regler hochdreht. Genau das tut sie nicht. Wer bei 0.80 steht und
„treuer" will, dreht auf 1.00 und bekommt **weniger** Treue — und zwar in allen drei
Kennzahlen zugleich (spearman fällt, geom_iou fällt, die gemeinsame Silhouette schrumpft
um 10 %).

**Was ich an dieser Messung nicht behaupten kann, und das gehört dazu:** Es ist **ein**
Punkt je Stärke, **eine** Geometrie, **ein** Seed, **ein** Prompt. Ich kenne die Streuung
nicht. 0.2649 gegen 0.2421 könnte Rauschen sein.

Aber der Einwand hängt nicht an der Grösse des Unterschieds, sondern an seiner Richtung —
und die ist in **allen drei** Kennzahlen gleich, was für reines Rauschen wenig spricht.
Und selbst wenn es Rauschen wäre, bliebe der Schluss stehen, nur anders begründet: Dann
ist die Monotonie **ungemessen**, und ein Feld, dessen Beschriftung eine ungemessene
Monotonie behauptet, ist eine Setzung, die sich als Messung ausgibt.

Die zweite Gruppe zeigt zudem: Bei der **falschen** Polarität fällt die Kurve monoton. Die
Form der Kurve hängt also von einer Grösse ab, die in `faithful` gar nicht vorkommt.

## 3.2 · Es sind mindestens drei Regler, und sie liegen nicht auf einer Achse

| Regler | Was er tut | Warum er nicht auf dieselbe Achse passt |
|---|---|---|
| `controlnet_staerke` | bindet die Tiefenkarte | nicht monoton (3.1) |
| `denoise` | wie stark ein Ausgangsbild überschrieben wird | **wirkt nur im Modus `image_edit`.** Ohne `beauty_png` gibt es nichts zu überschreiben; `render._hinweise` meldet das ausdrücklich als wirkungslos. |
| `schritte` | Anzahl Entrauschungsschritte | Wenige Schritte heisst, dass **auch** die ControlNet-Führung nicht ausgerechnet wird; viele Schritte geben **auch** den eigenen Vorstellungen des Modells mehr Raum. Der Zusammenhang zur Treue ist nicht einmal im Vorzeichen klar. |
| (`fuehrung`) | wie stark der Prompt zwingt | unterhalb 1.0 stirbt der Negativ-Prompt. Ein `faithful`, das daran drehte, würde ihn **still** abschalten. |

Ein einziger Schieber müsste sich entscheiden:

* Dreht er nur an `controlnet_staerke`, ist er das, was drüben tatsächlich gebaut ist
  (`--strength`) — dann ist der Name `faithful` schlicht falsch, denn er beschreibt nur
  einen der drei.
* Dreht er an mehreren, versteckt er, dass `denoise` in `txt2img` **gar nichts** tut. Ein
  Nutzer, der von 0.85 auf 0.60 geht und keinen Unterschied sieht, sucht den Fehler beim
  Modell.
* Schaltet er nebenbei den Modus um (setzt also `beauty_png`, damit `denoise` wirkt), dann
  ändert ein einziger Schieber die **Betriebsart** — und das ist keine Feineinstellung
  mehr, sondern ein anderer Lauf.

## 3.3 · Der Stil bringt schon eine Empfehlung mit — und die beiden kollidieren heute bereits

`prompts.Stil.empfohlene_controlnet_staerke`:

| Stil | Empfehlung | Was die Zahl bedeutet |
|---|---:|---|
| `messschnitt` | 1.00 | „So streng wie möglich, damit die Zahl das Modell misst." |
| `modellfoto` | 0.95 | |
| `wettbewerb` | 0.90 | |
| `abendstimmung`, `kosmo_standard` | 0.85 | |
| `morgennebel` | 0.80 | |
| `einskizziert` | 0.60 | „Bei 1.0 entsteht ein Foto mit Bleistiftfilter." |

Zwei Beobachtungen:

**Erstens gibt es die Kollision schon.** `komponiere()` liefert `controlnet_staerke` aus
dem Stil; `RenderAuftrag.controlnet_staerke` hat eine eigene Vorgabe von 0.8. Wer beides
benutzt, hat zwei Wahrheiten und keine Regel, welche gewinnt. Ein zusätzliches `faithful`
wäre die **dritte**. Das gehört im Entwurf entschieden, unabhängig von der
`faithful`-Frage (Vorschlag in 4.4).

**Zweitens bedeuten dieselben Zahlen an verschiedenen Stilen Verschiedenes.** Für
`messschnitt` ist 0.60 ein **Mangel** — die Messung wäre entwertet. Für `einskizziert` ist
0.60 der **Zweck** — bei 1.0 entsteht der Stil gar nicht. Eine Skala „0 = KI-frei,
1 = renderer-treu" behauptet, dass 0.60 überall dasselbe heisst. Es heisst nicht überall
dasselbe.

## 3.4 · „Treu" ist bei uns schon vergeben — an die Ausgabe

Wir messen Treue: `geometrie_qa.geometrie_score` → `sqrt(|spearman| · geom_iou)`, und die
Landestelle des Ökosystems nennt das Feld `geometry_fidelity`.

Ein Eingabefeld `faithful` stünde im selben Ergebnis neben `geometry_fidelity` — im
gemessenen Beispiel als `faithful: 0.85` neben `geometry_fidelity: 0.26`. Zwei Zahlen,
beide „Treue" genannt, die eine gewünscht, die andere gemessen, und um den Faktor drei
auseinander.

**Das ist der Grund, aus dem ich den Namen selbst ablehne, unabhängig von der Struktur
dahinter.** Das Wort „treu" gehört der Messung. Was hineingeht, heisst nach dem, was es
tut: `controlnet_staerke`.

## 3.5 · Der Endpunkt der Skala existiert zweimal

`faithful = 1.0` heisst laut Kommentar „Cycles-treu". Aber `controlnet_staerke = 1.0`
liefert **nicht** das Cycles-Bild, sondern ein Diffusionsbild, das sich an einer
Tiefenkarte festhält — und laut 3.1 sogar ein schlechteres als bei 0.80. Das wirklich
renderertreue Ende der Achse ist `vis.skip = true`: kein KI-Schritt.

Der Vertrag hat für einen Endpunkt zwei Felder und keine Regel, welches gewinnt.

## 3.6 · Was ich stattdessen vorschlage: benannte Punkte statt einer Zahl

Ein Schieber verspricht **Zwischenwerte**: dass zwischen zwei Einstellungen etwas
dazwischen herauskommt. Genau diese Zusage widerlegen unsere Zahlen.

Eine **Liste benannter Punkte** verspricht das nicht. Sie sagt nur: Diese Punkte gibt es,
und für diese ist bekannt, was sie tun.

```
treue_preset:  "render_pur" | "gebunden" | "ausgewogen" | "frei" | "skizze" | "eigen"
```

| Preset | ControlNet-Stärke | denoise | Schritte | Bedeutung |
|---|---:|---:|---:|---|
| `render_pur` | — | — | — | **kein KI-Schritt.** Der Render ist das Ergebnis. Der ehrliche Endpunkt. |
| `gebunden` | 1.00 | 0.35 | mehr | „so nah an der Geometrie wie möglich" — der Messschnitt |
| `ausgewogen` | 0.80 | 0.60 | Vorgabe | **der gemessene Bestpunkt** aus `auf-13` |
| `frei` | 0.65 | 0.75 | Vorgabe | Stimmung vor Silhouette |
| `skizze` | 0.60 | 0.85 | Vorgabe | für `einskizziert`; bei 1.0 entsteht der Stil nicht |
| `eigen` | aus den drei Einzelfeldern | | | wer selbst rechnet, setzt selbst |

Vier Eigenschaften, auf die es mir dabei ankommt:

1. **Ein Name lässt sich nicht interpolieren.** Niemand kann „zwischen `gebunden` und
   `ausgewogen`" schreiben und damit eine Zusage einfordern, die wir nicht gemessen haben.
2. **`ausgewogen` ist der gemessene Punkt, nicht die Mitte der Skala.** Auf einer Skala
   0…1 läge die Mitte bei 0.5; gemessen am besten war 0.80. Ein Preset kann das abbilden,
   ein Schieber suggeriert das Gegenteil.
3. **Die Auflösung ist eine Tabelle im Code, und sie landet im Ergebnis.** Der Auftrag
   trägt `treue_preset: "ausgewogen"`, das Ergebnis trägt zusätzlich
   `controlnet_staerke: 0.80, denoise: 0.60, schritte: 20` und
   `treue_preset_fassung: "v1-2026-08-19"`. Ändert sich die Tabelle, sagen alte Ergebnisse
   weiterhin, was damals gerechnet wurde.
4. **Die Oberfläche darf trotzdem einen Schieber zeigen.** Fünf Rasten, nicht stufenlos.
   Was der Auftrag trägt, ist der Name der Raste.

**Die Gegenrede, die ich selbst am ernstesten nehme:** Presets sind grobkörnig, und die
Schwellenstudie braucht gerade die Zwischenwerte. Antwort: Dafür gibt es `eigen`, und die
Studie fährt ohnehin über die Einzelfelder — sie ist der Ort, an dem die Zwischenwerte
**gemessen** werden, statt sie zu unterstellen. Sobald mehr Punkte gemessen sind, kommen
Rasten dazu. Das ist der Weg herum: erst messen, dann beschriften.

---

# TEIL 4 · Der Renderauftrag — vollständiger Vorschlag

## 4.1 · Die tragende Entscheidung: drei Ebenen statt einer

Der fremde Vertrag hat **zwei** Ebenen (Szene → Kameras). Unser `RenderAuftrag` hat
**eine** (ein Bild). Beides ist zu wenig. Vorschlag:

```
Visualisierungsauftrag        ← was der Owner bestellt; trägt VERWEISE und LISTEN
        │
        │  auflösen (rein rechnend, ohne GPU, ohne Blender)
        ▼
  n × RenderAuftrag           ← die Wiederholvorschrift je Bild; trägt ZAHLEN
        │
        ▼
  n × Renderergebnis  →  Kameraergebnis  →  Visualisierungsergebnis
```

Drei Gründe:

* **Der `RenderAuftrag` bleibt, was er ist.** Er ist heute die Wiederholvorschrift für
  genau einen Modellaufruf, `frozen`, mit vollständigem Parametersatz. Eine
  Wiederholvorschrift für zwölf Bilder wäre keine.
* **Die Auflösung ist prüfbar ohne Hardware.** Aus einem Visualisierungsauftrag n
  `RenderAuftrag` zu rechnen ist reine stdlib — dieselbe Bauart wie `kameras.kamerasatz`
  und `prompts.komponiere`. Damit ist die ganze Preset- und Variantenlogik hier im
  Container prüfbar, bevor eine GPU sie ausführt.
* **Der Freigebende sieht die Bildzahl vor der Freigabe** (1.4). `zaehle_bilder(auftrag)`
  fällt als Nebenprodukt ab.

## 4.2 · Die Regel für die Naht zur Oberfläche

> **Der Auftrag trägt Verweise. Das Ergebnis trägt aufgelöste Werte.**

Konkret: Der Auftrag sagt `stil: "kosmo_standard"`, nicht die sieben Bausteine.
Das Ergebnis sagt beides — den Verweis **und** die aufgelösten Bausteine, den fertigen
Prompt, die Stärke.

Vier Folgerungen:

1. **Ein Preset-Knoten kann Presets anbieten**, weil jede aufzählbare Wahl eine Funktion
   hat, die reine Daten liefert. `prompts.uebersicht()` gibt es bereits und ist das
   Vorbild („Regel 4 in einer Funktion"). Es fehlen `kameras.uebersicht()`,
   `backbone.uebersicht()`, `treue.uebersicht()`.
2. **Ein geänderter Stil wirkt auf neue Läufe, nicht rückwirkend** — weil alte Ergebnisse
   die aufgelösten Werte tragen. Trüge der Auftrag die Kopie, wüsste niemand mehr, ob ein
   Lauf ein Preset benutzt oder von Hand nachgebessert wurde.
3. **Die Feldnamen an der Aussenkante bleiben die des Ökosystems.** KosmoOrbit verdrahtet
   über Namensgleichheit, ohne Fehlermeldung bei Abweichung: `ifc_path`, `glb_path`,
   `up_axis`, `bbox`, `out_dir` heissen weiter so. Innen bleibt alles deutsch — genau die
   Linie aus `mcp_schemas.py` und `gate.als_kosmovis_verdikt`.
4. **Der Ausgabeknoten braucht nur die Variantenachsen.** „start imaging" heisst: Listen
   füllen, `zaehle_bilder` zeigen, Freigabe holen, ausführen.

## 4.3 · Der Visualisierungsauftrag, Feld für Feld

Legende: **(a)** existiert schon · **(b)** neu · **(c)** aus dem fremden Vertrag.

### Kopf

| Feld | Typ | Vorgabe | Warum es existiert | |
|---|---|---|---|---|
| `schema` | `str` | `"aiimaging.visualisierung/v1"` | Ein Leser muss eine fremde Generation erkennen statt sie zu raten. | (a) analog `contracts.SCHEMA_ID` |
| `projekt` | `str \| None` | `None` | Ein gemeinsamer Bezug über zwölf Ausgabeverzeichnisse. Regel 3 gilt für das, was im Repo landet, nicht für das Feld. | (c) `project` |
| `notiz` | `str` | `""` | Wofür dieser Lauf war. Nach zwei Wochen weiss das sonst niemand mehr. | (b) |

### Geometrie — unverändert übernommen

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `geometrie.ifc_path` | `str \| None` | `None` | Eigener IFC-Pfad (Regel 4: der Kern liest selbst). | (a) |
| `geometrie.glb_path` | `str \| None` | `None` | Einfügen hinter `kosmodraw_export_glb`. Genau **eine** der beiden Quellen. | (a) |
| `geometrie.up_axis` | `"Y" \| "Z" \| None` | `None` | Pflicht bei `glb_path`. Wird **nicht geraten** — eine Z-up-glb landet in Blender liegend, und Tiefenkarte und QA wären still verdreht. | (a) |
| `geometrie.bbox` | `[[3],[3]] \| None` | `None` | Massstabs- und Georeferenzprüfung vor der GPU. | (a) |

`geometry.format` und `.blend` aus dem fremden Vertrag übernehme ich **nicht**: Eine
fertige Blender-Szene ist ein Zustandsträger ausserhalb des Auftrags, und dann steht im
Auftrag nicht mehr, was gerechnet wurde.

### Ansicht — die grösste Lücke, geschlossen

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `ansicht.kameras` | `"auto" \| list[str]` | `"auto"` | `"auto"` = alle zwölf aus `RICHTUNGSFOLGE`. **Das ist der Verweis, den der fremde Vertrag schon hat und wir noch nicht.** `"saved"` übernehme ich nicht (siehe 1.1). | (c) |
| `ansicht.bias_grad` | `float` | `35.0` | Fassadenverhältnis der Diagonalen: 30° ≈ 2/3 zu 1/3, 45° = Eckblick. Architektonisches Bildwissen, kein Programmierdetail. | (a) `kameras.BIAS_GRAD` |
| `ansicht.brennweite_mm` | `float` | `28.0` | 28 mm ist der Weitwinkel, mit dem Gebäude fotografiert werden, ohne dass die Fluchten kippen. | (a) |
| `ansicht.seitenverhaeltnis` | `float \| None` | `None` | **Das eine Feld, aus dem drei Stellen bedient werden** (Kamerarechnung, Blender-Auflösung, Bildmodell). `None` heisst „aus dem Stil nehmen"; hat auch der keins, gilt 1.0. Siehe 1.3. | (b) |
| `ansicht.augenhoehe_m` | `float` | `1.70` | Über dem **Geländestand**. Die Bestandsaufnahme fand drei verschiedene Augenhöhen; 1.70 ist der Entscheid, und 1.65 gegen 1.70 ist keine Rundung, sondern eine andere Annahme über den Menschen im Bild. | (a) |
| `ansicht.gelaende_z` | `float \| None` | `None` | Angeben, wenn das Bauwerk ein Untergeschoss hat — sonst steht die Kamera im Keller. | (a) |
| `ansicht.deckungsgrad` | `float` | `0.55` | Anteil des Bildes, den das Bauwerk füllen soll: die „2/3-Komposition" als Zahl. | (a) |

### Multipass — die Cycles-Stufe, getrennt von der KI-Stufe

**Bewusst ein eigener Block.** Drüben stehen `samples` (Cycles) und `faithful` (KI) in
demselben `render`-Block. Das sind zwei Maschinen; wer sie in einen Block legt, kann
später nicht sagen, welcher Teil des Laufs teuer war.

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `multipass.aufloesung_px` | `[int, int]` | `[512, 512]` | **Ein Paar, keine Zahl.** Siehe 1.3. Der Kanten-Integer bleibt als Eingang zulässig und wird auf ein Paar aufgelöst — sonst bräche `mcp_schemas` und die Naht zum Ökosystem. | (c) `resolution` |
| `multipass.samples` | `int` | `16` | Rechenschritte je Bildpunkt. Wenige reichen für Tiefe und Material-ID; das Beauty-Bild wird davon rauschig. | (a) |
| `multipass.passes` | `list[str]` | `["tiefe","beauty","material_id"]` | Welche Kanäle gebraucht werden. Wer nur die Tiefe braucht, soll das Beauty-Bild nicht bezahlen. | (c) `passes` |
| `multipass.sonne` | `dict \| None` | `None` | `{lat, lon, zeitpunkt}` oder `{hoehe_grad, azimut_grad}`. `None` heisst die heutige feste Sonne (50°/35°). **Ein Feld, das heute nichts tut** — aber es sagt aus, dass die Sonne fest ist, statt es zu verschweigen. | (c) `sun` |

Zur Sonne, ehrlich: Sie aus Ort und Zeit zu rechnen ist ein eigenes Vorhaben (Sonnenstand
nach Datum und Breitengrad). Ich würde das Feld **jetzt** aufnehmen und **später** füllen —
mit einem Hinweis im Ergebnis, dass eine Angabe ignoriert wurde. Ein ignoriertes Feld,
das das sagt, ist besser als ein fehlendes.

### Bild — die KI-Stufe

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `bild.stil` | `str` | `HAUS_STIL` (`"kosmo_standard"`) | Verweis auf `prompts.STILE`, nicht die Kopie. Trägt Bausteine, Handschrift, Negativ-Prompt, Messtauglichkeit und empfohlene Stärke. | (a) |
| `bild.freitext` | `str` | `""` | Was im Prompt-Feld des Knotens steht. Steht im fertigen Prompt **vorne** und wiegt am schwersten — darum läuft er durch den Bauteilwächter. | (a) |
| `bild.ersetzungen` | `dict[str,str]` | `{}` | Einzelne Kategorien tauschen, ohne den Stil zu verlassen: „wie der Wettbewerbsstil, aber ohne Menschen". | (a) |
| `bild.backbone` | `str` | `VORGABE_BACKBONE` | Name aus der Registry, **kein freier Text** — der Eintrag entscheidet über Lizenz, Konditionierung und Tiefenpolarität. | (a) |
| `bild.treue_preset` | `str` | `"aus_stil"` | Siehe 3.6. `"aus_stil"` nimmt die `empfohlene_controlnet_staerke` des Stils — damit ist die Kollision aus 3.3 entschieden. | (b) |
| `bild.controlnet_staerke` | `float \| None` | `None` | `None` heisst „aus dem Preset". Ein gesetzter Wert schlägt das Preset und **schaltet es auf `"eigen"`** — es soll nie eine Zahl neben einem Namen stehen, der etwas anderes sagt. | (a) |
| `bild.denoise` | `float \| None` | `None` | Wie oben. Wirkt nur mit Ausgangsbild; sonst Hinweis. | (a) |
| `bild.schritte` | `int \| None` | `None` | Wie oben. Obergrenze `MAX_SCHRITTE = 200` bleibt. | (a) |
| `bild.fuehrung` | `float \| None` | `None` | Auftrag schlägt Registry schlägt diffusers. `None` bleibt `None` — ein eingesetzter Ersatzwert wäre eine Erfindung. Unter 1.0 stirbt der Negativ-Prompt. | (a) |
| `bild.ausgangsbild` | `"keines" \| "beauty"` | `"keines"` | Ob der Beauty-Pass als Anker dient (`image_edit`) oder aus dem Nichts begonnen wird (`txt2img`). **Als Wort, nicht als Pfad:** Welche Datei das ist, weiss erst der Multipass. | (b) |
| `bild.stil_referenzen` | `list[str]` | `[]` | Referenzbilder für die **Erzeugung** (LoRA, IP-Adapter). Heute leer, weil wir nur den Prompt-Weg haben. | (c) `style.refs` |
| `bild.lora` | `str \| None` | `None` | Pfad zu einem LoRA. **Lizenzpflichtig:** ein LoRA erbt die Lizenz seines Basismodells (`lora.lizenz_des_ergebnisses`), und aus FLUX.1-dev abgeleitete LoRAs sind unter Regel 1 ausgeschlossen. | (c) `style.lora` |
| `bild.upscale` | `"none"` | `"none"` | Aufgenommen, damit ein fremder Auftrag lesbar bleibt — aber heute ist `"none"` der einzige gültige Wert, weil SeedVR2 und SUPIR **lizenzrechtlich ungeprüft** sind. Alles andere wird abgelehnt, nicht ignoriert. | (c) `vis.upscale` |

### Varianten — die Achsen, die der Ausgabeknoten aufspannt

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `varianten.seeds` | `list[int]` | `[0]` | **Die einzige Achse, die der fremde Vertrag gar nicht hat** (2.1). Drei Seeds bei sonst gleichem Auftrag sind die ehrlichste Variantenerzeugung: Sie zeigt, wieviel vom Bild das Modell erfindet. | (b) |
| `varianten.treue_presets` | `list[str]` | `[]` | Leer heisst: nur der eine aus `bild`. Gefüllt: die Vergleichsreihe der Schwellenstudie, ohne den Auftrag n-mal zu schreiben. | (b) |
| `varianten.sonnenstaende` | `list[str]` | `[]` | `["morgen","mittag","abend"]`. | (c) `sun.presets` |
| `varianten.hoechstzahl` | `int` | `24` | **Eine Bremse, kein Wunsch.** Zwölf Kameras × drei Seeds × drei Sonnenstände sind 108 GPU-Läufe. Wer das will, hebt die Grenze bewusst — dieselbe Überlegung wie `MAX_SCHRITTE`. | (b) |

Die Bildzahl ist das Produkt der belegten Achsen; `zaehle_bilder(auftrag)` rechnet es
**ohne** Blender und **ohne** GPU. Überschreitet es `hoechstzahl`, wird der Auftrag
abgelehnt — vor der Freigabe, nicht danach.

### QA — was am Ende beurteilt wird

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `qa.aktiv` | `bool` | `True` | Der Demoplan-Entscheid ist Weg A: die QA ist sichtbar. Abschaltbar bleibt sie trotzdem — aber dann sagt das Ergebnis es. | (b) |
| `qa.referenzen` | `list[str]` | `[]` | Referenzbilder für die **Messung**. Getrennt von `bild.stil_referenzen`; Überschneidung wird gemeldet (1.5). | (b) |
| `qa.schwelle_geometrie` | `float` | `SCHWELLE_GEOMETRIE` (0.65) | Empirisch an wenigen Fällen gesetzt. Landet ins Ergebnis, weil sie sich ändern wird. | (a) |
| `qa.schwelle_stil` | `float \| None` | `None` | `None` heisst **aus dem Boden ableiten** statt setzen. Die alte 0.30 lag 3,24 Streuungen **unter** dem gemessenen SigLIP-2-Boden und liess 4950 von 4950 Paaren durch. Ein Gate, das nie zugeht, sieht aus wie Schutz. | (a) |
| `qa.mess_durchlauf` | `bool` | `False` | Zusätzlich zum gewählten Stil einen Lauf auf `messschnitt` fahren. **Der Knopf, der die Stiltrennung bedienbar macht:** ausgeliefert wird der Hausstil, gemessen der Messschnitt — sonst misst die Zahl den Stil. | (b) |

### Ausgabe

| Feld | Typ | Vorgabe | Warum | |
|---|---|---|---|---|
| `ausgabe.out_dir` | `str` | (Pfad-Sandbox) | Ökosystem-Name, damit die Kante trägt. | (a) |
| `ausgabe.namensschema` | `str` | `"<kamera>/<kamera>_<stil>_s<seed>_c<staerke>.png"` | **Ohne das überschreiben sich Varianten.** Der Bestand hat schon eine Konvention (`<out>/<kamera>/render_<kamera>_<pass>.png`); sie trägt nur die Varianten nicht. | (b) |
| `ausgabe.ueberschreiben` | `bool` | `False` | `render.rendere` räumt heute ein liegengebliebenes `ausgabe_png` ab. Bei n Bildern muss das eine Entscheidung sein — ein halb überschriebener Satz ist schlimmer als ein Abbruch. | (b) |
| `ausgabe.approval_token` | `str \| None` | `None` | Ohne Token bleibt der Auftrag auf `awaiting_approval` und rührt die GPU nicht an. Der Regelfall. **Neu daran:** Das Token gilt jetzt für eine **bekannte Bildzahl**. | (a), Bedeutung erweitert |

## 4.4 · Was der `RenderAuftrag` daraus wird

Er ändert sich **kaum** — und das ist ein gutes Zeichen. Ergänzt werden vier Felder, die
heute fehlen, weil er nichts von seiner Umgebung weiss:

| Feld | Typ | Warum neu | |
|---|---|---|---|
| `kamera` | `str \| None` | Die Identität, die das ganze Projekt braucht: Ohne sie kann die Geometrie-QA ihr Urteil nicht an eine Ansicht binden. Der `qa`-Block des Ökosystems ist **pro Kamera**. | (b/c) |
| `stil` | `str \| None` | Der Verweis, aus dem der Prompt entstand. Heute steht im Ergebnis der fertige Prompt, aber nicht, welcher Stil ihn gebaut hat — die Rückrechnung ist unmöglich. | (b) |
| `seitenverhaeltnis` | `float` | Damit die Bildgrösse des Modells zur Kamera passt (1.3). | (b) |
| `treue_preset` | `str` | Der Name neben den drei Zahlen, damit im Protokoll steht, aus welcher Absicht sie kamen. | (b) |

Und **eine Regel für die Kollision aus 3.3**, die heute fehlt:

> Auftrag schlägt Preset schlägt Stil schlägt Vorgabe. Wer eine Zahl setzt, schaltet das
> Preset auf `"eigen"`. Was gewonnen hat, steht als `quelle_der_staerke` im Ergebnis.

Dieselbe Kaskade, die `_baue_parameter` für `fuehrung` bereits fährt („Auftrag schlägt
Registry schlägt fremde Vorgabe") — nur ausgeschrieben und um die fehlende Stufe ergänzt.

---

# TEIL 5 · Das Ergebnis

Der Massstab ist unsere eigene Haltung, verschärft:

> **Was nicht im Parametersatz steht, kann das Modell nicht benutzt haben.**
> Und was im Parametersatz steht, ist noch kein Beleg, dass es **angekommen** ist.

Der zweite Satz ist der Punkt, den `auf-20260818-09` gelehrt hat: `controlnet_staerke`
stand im Parametersatz, und `QwenImageEditPlusPipeline` kannte das Argument gar nicht.
Drei Stärken, auf zwölf Stellen derselbe Score. Der Parametersatz war vollständig und
trotzdem irreführend.

## 5.1 · Drei Ebenen, spiegelbildlich zum Auftrag

```
Visualisierungsergebnis     status, engine, cost, regel_1, kameras[]
  └─ Kameraergebnis         kamera, passes, depth_herkunft, bilder[]
       └─ Bildergebnis      parameter, bild_png, pruefsumme, qa, hinweise
```

## 5.2 · Das Bildergebnis

| Feld | Herkunft | Warum es tragen muss | |
|---|---|---|---|
| `status` | `ok\|teilweise\|abgelehnt\|fehler` | Beide fehlenden Zustände beider Seiten (1.7). | (a)+(c) |
| `bild_png` | `str \| None` | | (a) |
| `pruefsumme_sha256` | **neu** | **Das Einzige, was beweist, dass zwei Läufe verschieden sind.** `auf-13` hat den Regler damit belegt (`alle_verschieden: True`) — bei Qwen waren die Scores identisch, weil die Bilder identisch waren. Ohne dieses Feld ist „der Regler wirkt" unbelegbar. Der fremde Vertrag hat es nicht. | (b) |
| `parameter` | vollständig | Die Wiederholvorschrift. Bleibt wie heute, ergänzt um Kamera, Stil, Seitenverhältnis, Preset. | (a) |
| `argumente_genommen` | **aus `hinweise` herausgelöst** | Welche Argumente die geladene Pipeline **wirklich** angenommen hat. `_vertraegliche_argumente` weiss das schon, heute landet es als Prosa in `hinweise`. **Als Liste ist es prüfbar, als Satz nicht.** Die schärfste Fassung unserer harten Haltung. | (b) |
| `argumente_verworfen` | **neu** | Die Gegenprobe: gesetzt, aber nicht angekommen. Genau der `auf-09`-Fall, als Feld statt als tagelanger Verdacht. | (b) |
| `qa` | `gate.gesamturteil` **vollständig** | Beide Scores, beide Schwellen, beide Zustände (`ok\|fehlt\|degeneriert`), `fail_reasons`, `begruendung`. **Nie als formatierte Zeichenkette** — siehe 1.6. | (a) |
| `hinweise` | `tuple[str]` | Was still wirkungslos geblieben wäre: `denoise` ohne Ausgangsbild, Negativ-Prompt unter Führung 1.0, ungemessene Tiefenpolarität, ignorierte Sonnenangabe. | (a) |
| `dauer_s`, `vram_spitze_mib` | | | (a) / (a) im HomeStation-Satz |
| `error`, `maengel`, `lizenz` | | | (a) |

## 5.3 · Das Kameraergebnis

| Feld | Warum | |
|---|---|---|
| `kamera` | Das Urteil bindet an eine Ansicht. | (c) |
| `azimut_grad`, `auge`, `blick_auf`, `abstand_m`, `fuellgrad` | `kamerasatz` liefert sie schon. **`fuellgrad` besonders:** Ein Bild, auf dem das Bauwerk ein Fleck ist, sieht wie ein Fehler des Bildmodells aus — die Ursache liegt in der Kamera, und niemand würde dort suchen. | (a) |
| `vollstaendig`, `durchlaeufe`, `warnungen` | Ob der Eckentest aufging. Eine „als unvollkommen gekennzeichnete Antwort" ist besser als keine — aber nur, wenn die Kennzeichnung mitreist. | (a) |
| `passes{tiefe_exr,tiefe_png,beauty,material_id}` | | (c) |
| `depth_herkunft` | **Der beste Gedanke des fremden Vertrags.** Bei uns reicher: der Weg (`compositor_z\|foreach_z\|emission_fallback`), die EXR-Kanalnamen, das Format, die Normalisierungsspanne. `blender-report.json` hat all das — es muss nur bis hierher reisen. | (c), erweitert |
| `depth_polaritaet` | Welche Konvention die Datei trägt und ob sie beim Übergeben gedreht wurde. Der teuerste ungeprüfte Punkt der ganzen Kette (2.2). | (b) |
| `kamera_herkunft` | `vorgegeben \| abgeleitet \| rueckfall`. Der Runner führt es bereits. Ohne es ist einem Bild nicht anzusehen, ob es die angeforderte Ansicht zeigt oder die Notlösung. | (a) |
| `bilder[]` | Die Varianten dieser Kamera. | (b) |

## 5.4 · Das Visualisierungsergebnis

| Feld | Warum | |
|---|---|---|
| `status` | `ok\|teilweise\|abgelehnt\|fehler`. **`teilweise` ist hier der Normalfall** bei zwölf Kameras. | (c) |
| `auftrag` | Der Auftrag, wie er hereinkam — **unverändert**, damit Verweis und Auflösung nebeneinander lesbar sind. | (b) |
| `aufgeloest` | Was die Verweise ergaben: der fertige Prompt, die Bausteine, die drei Treue-Zahlen, `treue_preset_fassung`, `quelle_der_staerke`. **Die Kernstelle der Regel aus 4.2.** | (b) |
| `engine.blender` | Steht im Multipass-Bericht, muss hierher. | (c) |
| `engine.python`, `.torch`, `.diffusers` | Im HomeStation-Satz vorhanden, im Renderergebnis nicht. Ein Lauf unter diffusers 0.39 ist ein anderer als unter 0.31. | (b) |
| `engine.backbone_repo`, `.controlnet_repo`, **`.revision`** | **Der wichtigste Zusatz.** Ein Hugging-Face-Repo kann unter demselben Namen andere Gewichte **und eine andere Lizenz** tragen. Ohne die Fassung ist weder der Lauf wiederholbar noch Regel 1 nachprüfbar. Der fremde Vertrag hat nur `backbone: "flux2-klein-4b"`. | (b) |
| `regel_1{basis,controlnet}` | Repo, Lizenz, `gated`, `private`, Quelle der Prüfung, Zeitpunkt. `auf-13` hat genau das **vor dem Laden** geprüft (`HfApi.model_info`) — das Ergebnis dieser Prüfung gehört ins Ergebnis. Eine Lizenzregel, die nur beim Laden gilt, ist im Protokoll nicht belegbar. | (b) |
| `cost.wall_s` | Summe. | (c) |
| `cost.gpu_spitze_w` | Wir führen eine 400-W-Grenze und messen die Spitze nicht. | (c) |
| `cost.vram_spitze_mib` | Im HomeStation-Satz vorhanden. | (a) |
| `cost.cloud_chf` | **Immer 0.0 — und genau darum als Feld.** Local-first ist eine Zusage; ein Feld, das sie jedes Mal mit einer Null bestätigt, ist ein Beleg. Ein fehlendes Feld ist keiner. | (c) |
| `bilanz{angefordert,gerechnet,bestanden,abgelehnt,fehlgeschlagen}` | Bei 24 Bildern will niemand 24 Einträge zählen. **Und `angefordert` gegen `gerechnet` ist die Probe darauf, dass nichts stillschweigend ausgefallen ist.** | (b) |
| `verdikt` | `gate.als_kosmovis_verdikt` je Kamera **und** aggregiert. Die Landestelle des Ökosystems ist gebaut und erwartet genau diese Namen. | (a) |

## 5.5 · Die vier Regeln, die aus alldem folgen

1. **Zahlen kommen nie in Prosa.** Der Gegenbeleg steht drüben:
   `notes = f"style={style} geom={geom}"` (1.6). Wer eine Zahl in einen Satz schreibt,
   nimmt dem nächsten Leser die Auswertung ab — und die Unterscheidung zwischen „nicht
   gemessen" und „durchgefallen" gleich mit.
2. **Der Parametersatz sagt, was gewollt war; `argumente_genommen` sagt, was ankam.**
   Beides, weil `auf-09` gezeigt hat, dass sie auseinanderfallen können, ohne dass
   irgendetwas abstürzt.
3. **Jede Zahl trägt ihre Herkunft.** `quelle_der_staerke`, `depth_herkunft`,
   `kamera_herkunft`, `treue_preset_fassung`, `lizenz_quelle`. Eine Zahl ohne Herkunft ist
   in zwei Wochen eine Setzung, die aussieht wie eine Messung.
4. **Ein ignoriertes Feld meldet sich.** Eine gesetzte Sonne, die der Runner nicht
   umsetzt; ein `denoise` ohne Ausgangsbild; ein `upscale`, das abgelehnt wird. Stilles
   Verwerfen ist die Fehlerklasse, gegen die `render._hinweise` schon heute antritt.

---

# TEIL 6 · Wo ich unsicher bin

Ausdrücklich, weil ein Entwurf ohne diese Liste vorgibt, mehr zu wissen, als er weiss.

1. **Die Nichtmonotonie ruht auf einem Punkt je Stärke.** Ein Seed, eine Geometrie, ein
   Prompt (3.1). Der Unterschied 0.2649 gegen 0.2421 könnte Rauschen sein. Der Schluss
   ändert sich dadurch nicht, wohl aber seine Begründung — von „widerlegt" zu
   „ungemessen". **Was ihn entscheiden würde:** dieselbe Reihe über drei bis fünf Seeds.
   Bei 1.4 s je Bild kostet das Minuten.
2. **Drei Ebenen könnten eine zu viel sein.** Bei genau einer Kamera und einem Seed ist
   der mittlere Block reine Zeremonie. Ich halte ihn trotzdem für richtig, weil der
   `qa`-Block des Ökosystems pro Kamera geführt wird — aber das ist ein Argument von der
   Schnittstelle her, nicht von der Sache.
3. **Ob `treue_preset` und die drei Einzelfelder nebeneinander bestehen sollten.** Meine
   Kaskade (4.4) ist eine Setzung. Sauberer wäre vielleicht: Preset **oder** Zahlen, nie
   beides. Das wäre strenger und für die Schwellenstudie unbequemer.
4. **Ob die Überschneidung von `stil_referenzen` und `qa_referenzen` verboten oder nur
   gemeldet gehört** (1.5). Ich neige zu „gemeldet", weil sie manchmal gewollt ist. Der
   Zirkelschluss bliebe dann aber möglich.
5. **Der Sonnenstand ist ein Feld ohne Umsetzung.** Ich schlage vor, es jetzt aufzunehmen.
   Wer das für Vorratshaltung hält, hat einen Punkt.
6. **Die Presetnamen sind erfunden**, nicht gemessen. `ausgewogen` sitzt auf einer echten
   Messung, die anderen vier auf Plausibilität. Das gehört so gekennzeichnet, bis sie
   gemessen sind.
7. **Nicht geöffnet** habe ich die beiden grössten Module des fremden Bestands zur
   KI-Stufe (`archviz_comfy_bridge.py`, `archviz_ai_render.py`, in der Bestandsaufnahme
   unter C.4 als „nicht ausgewertet" geführt). Es ist möglich, dass `faithful` dort auf
   mehr als `--strength` aufgelöst wird und mein Befund aus 1.1 nur für `render_scene.py`
   gilt. Was ich belegen kann, ist der Pfad, den `render_scene.py` nimmt.
8. **Ich habe nicht geprüft**, ob KosmoOrbits `mergeInputs` mit verschachtelten Feldern
   umgeht. Unsere heutigen MCP-Schemas sind flach; ein `ansicht.kameras` wäre es nicht.
   Möglicherweise muss die MCP-Aussenkante flach bleiben und nur die Bibliothek
   verschachteln. **Das gehört geprüft, bevor gebaut wird** — eine tote Kante meldet
   niemand.

---

# TEIL 7 · Was ins Lexikon gehört

Nicht selbst eingetragen, wie beauftragt. Geprüft gegen `docs/LEXIKON.md` (Stand
19.08.2026) — die folgenden Begriffe kommen in diesem Entwurf vor und fehlen dort:

| Begriff | Warum er erklärt werden muss |
|---|---|
| **Monotonie / monotone Wirkung (eines Reglers)** | Der Kern von Teil 3. Das Lexikon führt „Streng monoton (rangerhaltend)" für **Umrechnungen**; hier geht es um die Wirkung einer Einstellung auf ein Messergebnis. Verwandt, aber nicht dasselbe. |
| **Preset (Voreinstellung)** | Kommt in Demoplan, Bestandsaufnahme und diesem Entwurf durchgehend vor und ist nirgends erklärt. |
| **Interpolation / Zwischenwert** | Das Argument aus 3.6: Ein Schieber sagt Zwischenwerte zu, eine Liste benannter Punkte nicht. |
| **Kaskade / Vorrangregel (bei Vorgabewerten)** | „Auftrag schlägt Preset schlägt Stil schlägt Vorgabe" — die Bauart, die `_baue_parameter` schon für `fuehrung` fährt. |
| **Verweis gegen eingebettete Kopie (Referenz vs. Inline)** | Die Regel aus 4.2, aus der die ganze Naht zur Oberfläche folgt. |
| **Variantenachse** | Ein Feld, dessen Liste die Zahl der Läufe multipliziert. Der Begriff, der „start imaging" beschreibt. |
| **Revision (eines Modell-Repos)** | Aus 5.4. Dass derselbe Name andere Gewichte **und eine andere Lizenz** tragen kann, ist für Regel 1 wesentlich und im Lexikon nicht erfasst — „Modellkarte" und „Gated Model" stehen dort, die Fassungsbindung nicht. |
| **Sonnenstand / Azimut und Höhe der Sonne** | „Azimut" steht als Himmelsrichtung für Kameras im Lexikon, der Sonnenstand als Paar aus Azimut und Höhe nicht. |
| **Atom-Auftrag / Auflösung eines Auftrags** | Aus 4.1. Der Unterschied zwischen dem, was bestellt wird, und dem, was gerechnet wird. |
| **Zirkelschluss (in einer Messung)** | Aus 1.5: dieselben Bilder erzeugen und messen. Das Lexikon hat „Nullprobe" und „Kontrolle", aber nicht diesen Fehler. |

---

## Anhang · Was geprüft wurde und wie

| Behauptung | Prüfweg |
|---|---|
| `faithful` wird 1:1 als ControlNet-Stärke durchgereicht | `KosmoVis/01_workflow/render_scene.py:222-225` gelesen |
| Der fremde `qa`-Block ist eine Verarmung des eigenen v2-Formats | `render_scene.py:251-268` gegen `integrations/odysseus/kosmovis_mcp_server.py:160-165` |
| Die zwölf Richtungskürzel decken sich | Beispiel im Vertrag (`"n"`, `"sSE"`) gegen `kameras.RICHTUNGSFOLGE` |
| Der fremde Vertrag führt keinen Seed | Volltextsuche im Vertrag; beide JSON-Blöcke Feld für Feld gelesen |
| Unsere Kette rendert zwingend quadratisch | `runners/blender_depth_stage.py:658` (`resolution_x = resolution_y`) |
| `Stil.seitenverhaeltnis` wird nirgends gelesen | Volltextsuche über `src/aiimaging/` — nur `prompts.py` |
| ControlNet-Stärke wirkt nicht monoton | `auftraege/ergebnisse/auf-20260818-13.json:messwerte.tabelle`, alle sechs Zeilen |
| Der Regler wirkt überhaupt | ebenda, `pruefsummen.alle_verschieden: True` |
| Der Arbeitsbaum des fremden Repos war vollständig | `git -C KosmoVis ls-files \| wc -l` → 314; kein `reset` nötig |
| Die Testsuite bleibt grün | `python -m pytest -q` → **2102 passed**, 31 warnings, 41.65 s |
