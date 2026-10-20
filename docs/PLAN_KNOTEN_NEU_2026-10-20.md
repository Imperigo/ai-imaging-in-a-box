# Neue Knoten im Vis-Werkzeug — Bauplan (20.10.2026)

**Codestand:** Plan, noch nichts gebaut; Visbox `ec89f9a`, KosmoOrbit-Zweig `claude/kosmovis-fehler`.
**Grundlage:** Entscheide 107 und 109–111 (Blätter 31–33 der Entwurfsfläche); Himmelsbilder der HomeStation (CC0, Poly Haven, am Heim-PC); Bestandsaufnahme durch Lesen beider Repos. Offene Fragen gehen nach Entscheid 112 über die Zentrale.

Grundlage: Entscheide 107, 109–111. Nichts geändert, ich habe nur gelesen. KO = `KO` (Zweig `claude/kosmovis-fehler`), VB = `VB`.

### 0. Was der Plan voraussetzt (geprüft)
- **Kopie-Regel:** `modules/vis/**`, `packages/kosmo-contracts/**`, `kernel/derive/visgraph.ts`, `commands/vis.ts`, `derive/varianten.ts` und `model/entities.ts` sind in VB wörtliche Kopien. Das halten `VB/kosmovis/HERKUNFT.json` und `VB/tools/kosmovis_uebernahme.py:40-110` fest.
  - Darum wird alles Geteilte **zuerst in KO gebaut** und dann mit `kosmovis_uebernahme.py` übernommen.
  - Von Hand in VB geändert werden dürfen nur die Stellvertreter-Dateien: `apps/kosmo-orbit/package.json`, `kernel/derive/gltf.ts`, `kernel/derive/kamera.ts`. Dazu kommt der eigene Wirt `apps/visbox-knoten/**`.
- **Kernel ist nicht im Dateikreis des Vis-Workers.** Laut `KO/docs/AUFTRAEGE-AN-WORKER.md:173` gehören nur `modules/vis/**` und `contracts` dazu. Bei kv-varianten wurden `commands/vis.ts` und `derive/varianten.ts` trotzdem mitgeändert (Commit `c0a0fea66`). Kernel-Anteile darum im Blatt ausweisen.
- **glb an beiden Orten über dieselbe Funktion:** `exportGlb(doc)`. In KO ist das `KO/packages/kosmo-kernel/src/derive/gltf.ts:1325`. In VB ist es der Stellvertreter `VB/kosmovis/packages/kosmo-kernel/src/derive/gltf.ts:22-45`, der die Bytes aus `setzeModellGlb` liefert (`mappe.ts:270`). Die 3D-Komponente ruft also nur `exportGlb(doc)` auf und läuft unverändert in beiden Programmen.
- **three:** KO hat `three ^0.184` und importiert schon `three/examples/jsm/loaders/GLTFLoader.js`. VB hat three weder in einer `package.json` noch in `node_modules`.
- **VB-Bau:** `dist/assets/index-*.js` hat 718 KB, CSS 157 KB, dazu die Schriften. `dist` ist **eingecheckt**.
- **Dateitypen:** Mac-App und Heim-PC liefern nur `.html .js .css .woff2 .svg .png .txt .md` aus. Das steht in `VB/ipad/Visbox.swiftpm/Kern/Knotenwege.swift:67-76` und `VB/oberflaeche/server.py:480` (`KNOTEN_TYPEN`); `tests/test_mac_knotenansicht_buendel.py:74-79` prüft, dass beide gleich sind. **Kein `.webp`/`.jpg`.**
- **Bauteil-Art ist im Modell auslesbar:**
  - KO-glb: jeder Bauteil-Knoten trägt `extras.kind` (`KO/kernel/derive/gltf.ts:1814-1821`). Werte sind wall, roof, slab, opening, dachfenster, terrain, stair, column …
  - IFC-glb am Heim-PC: der Knotenname lautet `IfcWall_<Name>_<GUID>` (`ifc_to_glb_runner._knotenname:101`, `blender_depth_stage.py:1712 IFC_KNOTEN`).
  - Beliebige glb: keine Angabe vorhanden.
  - In VB ist das Dokument nur `FreeMesh`, die Art muss also aus den glb-Bytes kommen.
  - Der glTF-Import von Blender legt Knoten-`extras` als Custom Properties am Objekt ab (`obj["kind"]`).

---

## (1) Dateien je Feature

### Gemeinsamer Baustein: kleines 3D-Fenster (Voraussetzung für F1, F2 und F4)
- **KO, neue Dateien:**
  - `apps/kosmo-orbit/src/modules/vis/modell-vorschau-3d.tsx`: React-Hülle, `<canvas>`, ResizeObserver.
  - `modell-vorschau-3d-kern.ts`: reine Logik mit THREE.WebGLRenderer, GLTFLoader, OrbitControls aus `three/examples/jsm`. Rahmen auf die Hüllbox, Y oben. Kameras als Kegel (eigene Linien-Pyramide), dazu ein Hilfsrender je Kamera für die kleinen Blickvorschauen. `dispose()` beim Aushängen.
  - `modell-vorschau-3d.css`: eigene Datei, damit `vis-visual.css` nicht angefasst wird.
- **Laden nur bei Bedarf:** `import('./modell-vorschau-3d-kern')` als eigener Chunk, der Haupt-Bundle bleibt gleich gross.
- **Kein WebGL vorhanden:** Rückfall auf einen ruhigen Satz «Kein 3D in diesem Fenster» (jsdom-Probe).
- **Eingaben stoppen:** `onPointerDown`, `onWheel` und Trackpad-Gesten mit `stopPropagation`, sonst zoomt bzw. schiebt `NodeCanvas` (`shell/trackpad-geste.ts`). Pixeldichte = DPR × Knotenzoom, nach oben begrenzt.
- **WebGL-Kontexte begrenzen:** höchstens etwa 4 gleichzeitig, sichtbar ausserhalb des Bildschirms → anhalten. Browser verwerfen ab etwa 16 Kontexten.
- **VB, Stellvertreter:**
  - `kosmovis/apps/kosmo-orbit/package.json`: `three ^0.184.0` (gleich wie KO) und `@types/three` als devDependency.
  - `kosmovis/package-lock.json` nachziehen.
  - `HERKUNFT.json` `stellvertreter` ist schon geführt.
- **VB `NOTICE`:** im Abschnitt «Was mit der Knotenansicht an den Browser ausgeliefert wird» (etwa Zeile 529) die Zeile `three  MIT  https://threejs.org/` ergänzen. KO hat three bereits in `THIRD_PARTY_LICENSES.md:70`.

### F1 Modell-Knoten
- **KO:**
  - `ModellKnoten.tsx`: 3D-Fenster fest etwa 248×140 unter der Szenen-Zeile; Doppelklick öffnet gross in `KDialog` (`kosmo-ui/src/overlay.tsx`).
  - `NodeCanvas.tsx`: Höhe `KOERPER_H.modell` (`:538`, heute 22) und `MODELL_KOERPER_H_MIT_LADEN` (`:722`, heute 140) jeweils um die Fensterhöhe erhöhen. `groessteNodeHoehe` (`:795`) und `startGraphLage` (`start-graph.ts`) rechnen dann automatisch richtig.
  - e2e: `kv-b5-*`-Höhenproben nachziehen und eine neue `kv-modell-3d.spec.ts`.
- **VB-Wirt:** keine Änderung nötig, `mappe.ts:268-270` liefert die glb schon. Optional ein Neuzeichnen beim Modellwechsel über `abonniereModellLaden`.
- **Heim-PC:** nichts.

### F2 Auto-Kamera
- **KO-Kernel `derive/visgraph.ts`:**
  - Katalog `kamera` (`:167-189`): Vorgaben `art:'auto'`, `richtungen:'s,sSE,nNW'`, `augenhoehe:1.7`, `brennweite:35`, `abstandArt:'auto'`, `fuellt:0.7`, `perspektive:'senkrecht'`.
  - Im Fall `render` (`:397-466`) werden die Knoten-Parameter gelesen: Auto → `kamerasAuto` im `VisRenderAuftrag` (`:322`). Manuell → Kameraliste aus dem Parameter `kameras` (JSON-Text, wie `schreibeListe`) mit `perspektive`.
- **KO-App:**
  - neue Datei `KameraKnoten.tsx` (Körper). Bedienung:
    - Chips N, NO, O, SO, S, SW, W, NW. Zuordnung zu den Heim-PC-Kürzeln: N→`n`, NO→`nNE`, O→`e`, SO→`sSE`, S→`s`, SW→`sSW`, W→`w`, NW→`nNW` (Tabelle in `kameras.py:674`; `sSE` = «Südost», `nNW` = «Nordwest» wie in `heim-standpunkte.ts`).
    - Augenhöhe, Brennweite 24/35/50 als KSelect, Abstand auto (Haus füllt X %) oder fest in m, Perspektive.
    - 3D-Fenster mit Kegeln und Blickvorschauen. Im Modus Manuell werden Kamera und Blickpunkt auf einer waagrechten Ebene gezogen, die Höhe wird eingetippt (einfacher und robuster als TransformControls).
    - Knopf «manuell übernehmen» friert die Auto-Standpunkte ein.
  - `heim-standpunkte.ts`: Abfrage mit Parametern.
  - `vis-jobs.ts`: `cameras_auto` in die Szene schreiben (`:1444-1452`), `perspektive` in jede CameraSpec.
  - `grundlage.ts`: `cameras_auto` gehört in `grundlageStand` (`:173`).
  - `NodeCanvas.tsx`: Höhe `KOERPER_H.kamera` (`:560`) bzw. `KAMERA_KOERPER_H_MIT_HEIM` (`:731`) neu setzen; der Fall `case 'kamera'` (`:4377`) delegiert an den neuen Körper.
- **VB-Wirt `mappe.ts:259`:** die Standpunkte für die Kegel kommen vom Heim-PC und müssen die gewählten Parameter mitschicken: neuer Abfrageweg `/knoten/standpunkte?richtungen=…&augenhoehe=…&brennweite=…&fuellt=…|abstand=…`. Den Weg in `server.py` (`WEG_KNOTEN_*`) **und** in `Knotenwege.swift` `datenwege` (`:60`) eintragen; die Probe hält beide gleich.
- **Heim-PC:**
  - `kosmo_szene.py`: `cameras_auto` in `BEKANNTE_FELDER` (`:632`) aufnehmen und prüfen (Kürzel aus `kameras.RICHTUNGEN`, Bereiche). `KAMERA_FELDER` (`:738`) um `perspektive` ergänzen. `lies_szene` (`:1688`) liefert dann `kameras_auto`.
  - `abholer.py`: Bisher gelten Richtungen, Augenhöhe usw. nur als Einstellungen des ganzen Abholers (`verarbeiter(...)`, `:2746`). Neu überschreibt der Auftrag sie je Lauf: Aufgaben werden aus `szene["kameras_auto"]["richtungen"]` statt aus `auto_richtungen` gebaut (`:2985-2987`); `augenhoehe`, `brennweite_mm`, `deckungsgrad` und `kamera_modus` (shift/gekippt) werden je Auftrag an `:3160-3181` weitergereicht. Für Manuell mit `senkrecht` berechnet `kameras.shift_aus_ziel` (`:445`) den Shift, dann `--shift-y` und ein waagrechtes Ziel. Heute gilt `kamera_modus` auf diesem Weg als wirkungslos (`blender_depth_stage.py:155-160`).
  - `kameras.py` `kamerasatz` (`:2067`): neuer Parameter `abstand_fest_m`. Eckentest dann nur melden, nicht nachschieben.
  - `knotenweg.heim_standpunkte` (`:507`): dieselben Parameter annehmen.
  - Die Grundlage-Prüfung braucht keinen neuen Schlüssel: `GRUNDLAGE_MUSS_PASSEN` (`abholer.py:4028`) enthält `kameras` schon. Es muss nur `kameras_auto` mit hineinfliessen.
  - **Hängt ab von** der laufenden Reparatur «Rahmung weist Szene mit Geländeplatte ab».

### F3 Stimmung
- **KO-Kernel:**
  - `VIS_STIMMUNGEN` (`visgraph.ts:81-85`) auf 8 Schlüssel: `morgen, mittag, abend, blaue-stunde, bedeckt, nebel, winter, weiss`, je mit `label`, `prompt` und `hdri` (Namensstamm, z. B. `sunny_vondelpark`).
  - Katalog `stimmung` (`:116-124`): Parameter `presets` (Liste), `drehung`, `wirkung` (licht+prompt). `preset` bleibt als Rückfall lesbar, alte Graphen werden darüber übernommen.
  - `commands/vis.ts:266`: `stimmungPreset`-Aufzählung auf 8 erweitern. `:77`: Beschreibungstext neutral fassen («Preset einer Stimmung»).
  - `derive/varianten.ts`: Die Stimmungs-Achse kommt aus dem vorgeschalteten Stimmung-Knoten (`graphMitStimmung` `:248` setzt dann `presets=[x]`).
- **KO-App:**
  - neue Datei `StimmungKnoten.tsx`: 8 Daumenbilder mit Mehrfachwahl, Regler «Himmel drehen», Zeile «wirkt auf».
  - `vis-jobs.ts`: `'environment'` aus `NICHT_GESENDET.render` streichen (`:1157-1162`), `FREMDNAHT` auf `gelesen` setzen (`:994-1002`). `environment` kommt aus dem Knoten statt nur aus der Insel (`:1214`, `:1461`, `:1648`, `:1825`). Die Insel `island/inhalte/stimmung.tsx` schreibt künftig in den Stimmung-Knoten des aktiven Graphen, damit es nur eine Quelle gibt.
  - `grundlage.ts:157-185`: `environment` gehört in `GrundlageEingaben`/`grundlageStand`. Statt einer Grundlage je Render-Knoten gibt es **eine je Stand**: neuer Parameter `grundlagenJeStand` (JSON stand→{id,seed,kameras,ebenen}) neben `GRUNDLAGE_PARAM` (`:29`). So hat jede Stimmung ihre eigene Grundlage (Nr. 85).
  - `varianten.ts:212-232`: eine Stimmung ohne passende Grundlage zuerst als Grundlage bestellen.
  - `NodeCanvas.tsx`: `KOERPER_H.stimmung` (`:541`) und `KOERPER_H_ZUSATZ_OFFEN` (`:613`) anpassen; `case 'stimmung'` (`:3576-3600`) delegiert an den neuen Körper.
  - Daumenbilder unter `apps/kosmo-orbit/public/vis/stimmungen/<id>.webp` mit Quellenangaben.
- **VB:** `kosmovis_uebernahme.py` `WOERTLICH` um `apps/kosmo-orbit/public/vis/**` ergänzen (heute nur Schriften), denn Vite nutzt `publicDir: '../kosmo-orbit/public'`. Neuen Dateityp `.webp` (und `.jpg`) in `Knotenwege.swift:67` und `server.py:480` aufnehmen. In `NOTICE` einen CC0-Abschnitt nach dem Muster der Schriften: Datei, SHA-256, Quelle (Poly Haven bzw. ambientCG), Asset-Name.
- **Heim-PC:**
  - `kosmo_szene.py`: `render.environment` aus `ABGEWIESENE_FELDER` (`:675-678`) entfernen. Prüfen: `preset` in 8, `hdri` per Muster `^[a-z0-9_]{1,64}$`, `intensitaet`, `rotationGrad`. Datei auflösen: `$AIIMAGING_HIMMEL_ORDNER/<preset>__<hdri>_<2k|4k>.hdr`; 2k bei `guete:'vorschau'`, sonst 4k. Fehlt Ordner oder Datei, **mit einem Satz abweisen**.
  - `abholer.py`: `GRUNDLAGE_MUSS_PASSEN` (`:4028`) um `"umgebung"` ergänzen; den Pfad an den Runner geben.
  - `runners/blender_depth_stage.py`:
    - neue Argumente `--umgebung-hdr`, `--umgebung-staerke`, `--umgebung-drehung` (`:102-216`).
    - `_welt_setzen` (`:1076`) baut bei HDRI: Environment Texture, Mapping mit Drehung um Z, Background. Aufgerufen wird es an `:2271`; der schwarze Grund für den ID-Pass (`:2312`) bleibt.
    - `_sonne_setzen` (`:1099`): keine Sonnenlampe, wenn ein HDRI gesetzt und `render.sun` nicht bestellt ist.
  - `heimstand.py`: Stand «Himmelsbilder 8/8» im Einrichten.

### F4 Oberfläche / Material / Farbpalette
- **KO-Kernel `visgraph.ts`:**
  - Der Typ `material` (`:98-106`) **behält seinen Schlüssel**, nur das Label wird «Oberfläche». Damit ist **keine Migration** nötig: alte Kanten `material`→`kombinierer.material` bleiben gültig.
  - Neue Eingänge (Porttyp `material`, mit `nurVon:['materialTextur']`, Mechanismus wie `:28-34`): `fassade, dach, fenster, boden, uebrige`. Der Ausgang `material` (Prompt-Phrasen plus Satz der Palette) bleibt.
  - Neue Typen `materialTextur` (Label «Material»: Parameter `bibliothek`, `massstab`, `drehung`, `relief`, `vorschau: kugel|wuerfel|flaeche`, Eingang `palette` mit `nurVon:['farbpalette']`) und `farbpalette` (`farben`, `staerke`, `satz`).
  - Render-Eingang `oberflaeche` mit `nurVon:['material']` (`:148-165`). Im Fall `render` → `materialien` im `VisRenderAuftrag`. Im Fall `material` (`:383`) werden zusätzlich die Wahlen gesammelt.
  - **Keine neuen Porttypen**, damit `entities.ts:2888` und die Port-Tokens in aura.css unberührt bleiben.
- **KO-App:**
  - neue Dateien `material-bibliothek.ts` (11 Einträge: id, Label, Vorschaubild, Prompt-Phrase), `bauteil-arten.ts` (rein: KO-Dokument-kinds → Art; glb-JSON-Chunk lesen → `extras.kind` / `Ifc*`-Präfix → Art; gleiche Tabelle wie in Python, über eine Probe gehalten), `OberflaecheKnoten.tsx`, `MaterialKnoten.tsx` (3D-Kugel, -Würfel oder -Fläche über den gemeinsamen Baustein), `FarbpaletteKnoten.tsx`.
  - `start-graph.ts`: Vorlage Material → Oberfläche → Render, zusätzlich Oberfläche → Kombinierer; `startGraphLage` erweitern.
  - `vis-jobs.ts`: `render.materialien`. `grundlage.ts`: `materialien` in den Stand.
  - `NodeCanvas.tsx`: `KOERPER_H` und `case 'material'` (`:3553`) plus zwei neue Fälle.
- **VB:** Vorschaubilder `public/vis/materialien/<id>.webp`, NOTICE wie bei F3.
- **Heim-PC:**
  - `kosmo_szene.py`: `"materialien"` in `BEKANNTE_FELDER["render"]` (`:635`) und ein Unterblock. Bibliotheks-ID gegen das Verzeichnis `$AIIMAGING_MATERIAL_ORDNER/<id>__<ambientCG-Asset>_<1K|2K>-JPG_<Color|Roughness|NormalGL|Displacement>.jpg` prüfen; Unbekanntes oder Fehlendes abweisen.
  - `abholer.py`: Materialwahl als JSON in den Auftragsordner schreiben; `GRUNDLAGE_MUSS_PASSEN` um `"materialien"` ergänzen.
  - Runner, neue Funktion `_oberflaechen_setzen` vor dem Beauty-Bild:
    - Art je Objekt bestimmen: `obj.get("kind")`, dann `IFC_KNOTEN`-Präfix, dann `maske.ist_gelaende` (Gelände ausgenommen), sonst `uebrige`.
    - Principled BSDF bauen: Image Texture mit **Box-Projektion** (Blend 0,2), Texture Coordinate «Object», Mapping (1/massstab, Drehung). Grundfarbe gemischt mit der Tönung (Mix, Faktor = Stärke). Rauheit als Non-Color. **Bump aus Height/Displacement** (Stärke = relief) statt Normal-Map, weil die Box-Projektion keine Tangenten hat. Displacement nur als «Bump Only».
    - Nicht verbundene Arten behalten das glb-Material («aus dem Modell»).
    - `_material_id_zuweisen` (`:1718`) bleibt je Objekt bzw. je Material und vergibt danach neue Namen. Optional `quelle:"oberflaeche"`.
  - `ifc_to_glb_runner.py`: optional `PredefinedType` in `extras` schreiben, damit Dach-Slabs erkennbar werden.

### Varianten-Daumenbilder
- `VariantenKnoten.tsx`: eine Reihe Daumenbilder der fertigen Zellen (`variantenZellen`) mit `BridgeBild`, wie `VariantenRaster.tsx:117`. Klick → gross über denselben Weg wie das Raster.
- `NodeCanvas.tsx`: `KOERPER_H.varianten` (VB `:574`, heute 244) um etwa 60 erhöhen.
- **Achtung:** Die Datei liegt in VB und auf `claude/kosmovis-varianten`, aber **nicht** auf `claude/kosmovis-fehler`. Darum auf dem eingespielten Varianten-Stand bauen.

---

## (2) Vertragsvorschlag an den Integrator (`packages/kosmo-contracts/src/render-scene.ts`)
Alles zusätzlich und optional; das Schema bleibt `/v1`.

```ts
// a) environment (:399-406) — Aufzaehlung erweitert, hdri ohne Pfad
export const StimmungPreset = z.enum(['morgen','mittag','abend','blaue-stunde','bedeckt','nebel','winter','weiss']);
environment: z.object({
  preset: StimmungPreset,
  hdri: z.string().regex(/^[a-z0-9_]{1,64}$/).optional(),   // Namensstamm, nie Pfad (Regel 3)
  intensitaet: z.number().min(0).max(10).default(1),
  rotationGrad: z.number().min(0).max(360).default(0),
}).optional(),

// b) neben `cameras` (oberste Ebene)
export const AutoRichtung = z.enum(['n','e','s','w','nNE','nNW','eEN','eES','sSE','sSW','wWS','wWN']); // = kameras.RICHTUNGEN
cameras_auto: z.object({
  richtungen: z.array(AutoRichtung).min(1).max(8),          // Heim-PC-Vorgabe ohne Feld: s,sSE,nNW
  augenhoehe_m: z.number().min(0.5).max(50).optional(),       // ueber Terrain am Standpunkt; Vorgabe 1.70
  brennweite_mm: z.union([z.literal(24), z.literal(35), z.literal(50)]).optional(), // Vorgabe 35
  abstand: z.discriminatedUnion('art', [
    z.object({ art: z.literal('auto'), fuellt: z.number().min(0.2).max(0.95).optional() }), // Vorgabe 0.70
    z.object({ art: z.literal('fest'), meter: z.number().min(2).max(2000) }),
  ]).optional(),
  perspektive: z.enum(['senkrecht','frei']).optional(),       // senkrecht = Shift (Heim-PC MODUS_SHIFT)
}).optional(),

// c) CameraSpec (:67-79)
perspektive: z.enum(['senkrecht','frei']).optional(),   // fehlt = wie heute (gekippt)

// d) render.materialien — explizites Objekt, KEIN z.record(enum): zod 4 verlangt dort alle Schluessel
export const MaterialWahl = z.object({
  id: z.string().regex(/^[a-z0-9-]{1,48}$/),     // Bibliotheks-Kennung, Heim-PC prueft gegen seine Ablage
  massstab_m: z.number().min(0.05).max(20).default(1),
  drehungGrad: z.number().min(0).max(360).default(0),
  relief: z.number().min(0).max(1).default(0.6),
  toenung: z.object({ farbe: z.string().regex(/^#[0-9a-fA-F]{6}$/), staerke: z.number().min(0).max(1) }).optional(),
});
materialien: z.object({ fassade: MaterialWahl.optional(), dach: …, fenster: …, boden: …, uebrige: … }).optional(),
```
**Abweisungen im `superRefine`, nach dem Muster von `:788-815`:**
- `cameras_auto` ohne `cameras==='auto'` (auch fehlendes `cameras`, denn die Vorgabe ist 'auto').
- `cameras_auto` zusammen mit `skizze` oder `interior`.
- `materialien: {}` ohne einen einzigen Schlüssel.
- `vis.grundlage` plus `environment`/`materialien`/`cameras_auto` ist **erlaubt**. Der Heim-PC weist ab, wenn der Stand nicht passt (`GRUNDLAGE_MUSS_PASSEN`).

**Fixtures:** `test/fixtures/kv-stimmung-hdri.json`, `kv-kamera-auto.json`, `kv-materialien.json`.

**Tokenkosten (KosmoVis-Rahmen 150 Token, davon 49 belegt):**
- Nur die Aufzählung `stimmungPreset` in `vis.render` (`commands/vis.ts:266`) wächst um 5 Werte, etwa +12 bis 18 Token.
- `cameras_auto` und `materialien` **nicht** ins `vis.render`-Schema. Die KI setzt sie über `vis.nodeParametrieren` an den Knoten (kostet 0 Token). `vis.nodeSetzen.typ` ist ein freier String (`:49`), neue Knotentypen kosten also ebenfalls nichts.
- Die Beschreibung an `:77` nicht länger machen.

---

## (3) Reihenfolge, Grösse (Sitzungen), was parallel geht
| Schritt | Inhalt | Grösse | Hängt ab von | Dateien |
|---|---|---|---|---|
| **V** | Vertragsvorschlag und Proben (Zweig `claude/kosmovis-vertrag-werkzeuge`) | 0,5 | – | nur `kosmo-contracts` |
| **K** | **Ein** Katalog-Commit im Kernel: VIS_STIMMUNGEN 8, Labels, neue Typen und Ports, Kamera-Vorgaben, `vis.render`-Aufzählung | 0,5 | V | `visgraph.ts`, `commands/vis.ts` |
| **A** | 3D-Baustein (nur neue Dateien) und three in VB | 1–1,5 | – | `modell-vorschau-3d*`, VB-Stellvertreter-package.json, NOTICE |
| **H1** | Heim-PC Stimmung: annehmen, HDRI-Welt, Grundlage | 1 | V (Feldnamen) | `kosmo_szene.py`, `abholer.py`, Runner, `heimstand.py` |
| **H2** | Heim-PC Kamera: `cameras_auto`, fester Abstand, Manuell senkrecht, Standpunkte-Weg | 1,5 | V, Geländeplatten-Fix | `kosmo_szene.py`, `abholer.py`, `kameras.py`, `knotenweg.py`, `server.py` |
| **H3** | Heim-PC Oberflächen: Bauteil-Art, Principled/Box, Tönung | 2 | V | Runner, `abholer.py`, `kosmo_szene.py` |
| **B** | F1 Modell-Knoten | 0,5–1 | A, **`kosmovis-fehler` eingespielt** | `ModellKnoten.tsx`, NodeCanvas (Höhe), e2e |
| **C** | F3 Stimmung in der Oberfläche, Bilder, Grundlage je Stand | 2 | K, A nicht nötig | `StimmungKnoten.tsx`, `vis-jobs.ts`, `grundlage.ts`, `varianten.ts`, NodeCanvas |
| **D** | F2 Kamera-Knoten in der Oberfläche | 2 | K, A, B | `KameraKnoten.tsx`, `heim-standpunkte.ts`, `vis-jobs.ts`, VB `mappe.ts` |
| **E** | F4 Oberfläche, Material, Palette, Vorlage | 3 | K, A, C (wegen `grundlage.ts`) | neue Knoten-Dateien, `start-graph.ts`, `vis-jobs.ts` |
| **F** | Varianten-Daumenbilder | 0,5 | Varianten-Zweig eingespielt | `VariantenKnoten.tsx`, NodeCanvas (Höhe) |
| **W** | Mac/Server-Dateitypen `.webp`/`.jpg`, Bilder und NOTICE in beiden Repos, `WOERTLICH` + `public/vis/**` | 0,5 | Bilder von der HomeStation | `Knotenwege.swift`, `server.py`, NOTICE, `kosmovis_uebernahme.py` |
| **Ü** | Übernahme nach VB je eingespieltem KO-Stand, `dist` neu bauen | je 0,25 | jeweiliger Merge | HERKUNFT.json, `dist` |

**Gleichzeitig möglich, ohne dass sich Dateien überschneiden:**
- V, A, H1, H3 und W sofort.
- H2 nach dem Geländeplatten-Fix.
- **NodeCanvas.tsx ist der Engpass:** Alle Eingriffe dort sind nur Registrierung (Einfuhr, `KOERPER_H`, ein delegierender `case`) und kommen **nach** dem Einspielen von `claude/kosmovis-fehler` (dort laufen gerade Fokus, Zoom-Bild, Upload, `vis-visual.css`). Die Feature-Zweige B → C → D → E → F darum **nacheinander** auf NodeCanvas.
- Jedes Feature bekommt eigene CSS-Dateien, nie `vis-visual.css`.
- `vis-jobs.ts` und `grundlage.ts` werden von C, D und E geteilt, also auch nacheinander. Alternativ C zuerst und `grundlage.ts` dabei gleich verallgemeinern («je Stand» für Umgebung, Materialien und Kameras).

**Summe:** etwa 11–13 Sitzungen Oberfläche und etwa 4,5 Sitzungen Heim-PC. Kritischer Pfad: V → K → A → B → D/E.

---

## (4) Risiken
- **Bundle:** three r184 bringt nach Tree-Shaking mit GLTFLoader und OrbitControls schätzungsweise **+550–650 KB** minifiziert, also etwa eine Verdopplung von 718 KB. Gegenmittel: dynamischer `import()` als eigener Chunk, geladen erst beim ersten 3D-Fenster.
  - Weil `dist` eingecheckt ist, bringt jeder Bau grosse Binärunterschiede ins Repo. Das im Blatt festhalten.
  - Bilder: 19 Vorschaubilder als WebP mit etwa 160 px etwa 150–250 KB. Als PNG (heute einziger Bildtyp) eher 0,6–1,5 MB.
  - Texturkarten für die Material-Kugel **nicht** in den Bau packen. Erste Stufe: die Kugel trägt das Vorschaubild. Echte Karten erst über einen Datenweg vom Heim-PC.
- **WebGL:**
  - WKWebView (Mac) kann WebGL2 sicher.
  - WebKitGTK (KO-Desktop): WebGL hängt an der Beschleunigung. Unter Xvfb oder in einer VM läuft es über llvmpipe langsam oder fällt ganz aus. Darum Rückfall-Satz, Kontext-Grenze, Pause ausserhalb des Bildschirms, `webglcontextlost` behandeln.
  - Nachweis wie bei C48/C50 als local-Auftrag «Gegenprobe in WebKitGTK».
  - e2e-Chromium nutzt SwiftShader; mit Bild-Schwellen nachsichtig sein.
- **Zeigereingaben:** Knotenzoom und Trackpad-Gesten von NodeCanvas gegen OrbitControls. Mit `stopPropagation` für Zeiger und Rad innerhalb des Fensters lösen. Ziehen am Knotenkopf muss weiter gehen.
- **Lizenz und NOTICE:** three (MIT) ist in VB **eingebaut** und muss in die NOTICE-Liste «an den Browser ausgeliefert». CC0-Bilder mit Quelle, Asset-Name und SHA-256. Bei der Klausel «unverändert» (Entscheid 107) ist offen, ob verkleinerte Vorschaubilder darunter fallen → Frage 1. `tests/test_notice.py` prüft die Form (`AUFLOESUNG` nur bei Copyleft).
- **Regel 3:** keine Heim-PC-Pfade im Repo. Ordner nur über Umgebungsvariablen (`AIIMAGING_HIMMEL_ORDNER`, `AIIMAGING_MATERIAL_ORDNER`, Muster wie `AIIMAGING_BLENDER`). Im Vertrag nur Namensstämme mit Muster, nie Pfade. Proben mit `tmp_path`. Die JSON für den Runner liegt nur zur Laufzeit im Auftragsordner.
- **Regel 2:** alles Blender-seitige nur im Runner (Subprozess). Die Rechnung (Shift, Abstand, Art-Zuordnung) bleibt diesseits in `kameras.py` bzw. in einer neuen reinen Funktion und ist ohne Blender prüfbar.
- **Bildwirkung:**
  - HDRI zusammen mit der bisherigen Sonnenlampe ergibt doppeltes Licht; darum Sonnenlampe aus, ausser `sun` ist bestellt.
  - Box-Projektion zeigt an schrägen Flächen Nähte; Bump statt Normal-Map hält das klein.
  - Jede Stimmung oder Materialänderung braucht eine neue Grundlage: Rechenzeit × Zahl der Stimmungen.
- **Geteilte Dateien:** In KO laufen gleichzeitig zwei Wahrheiten über die Auto-Kamera: `derive/kamera.ts` (Eingang/Übersicht als Liste) und der Heim-PC (`auto`) → Frage 3.
- **Probendrift:** `kv-b5*`-Höhen, `groessteNodeHoehe`/`startGraphLage` und die Varianten-Achse (heute 3 Stimmungen, Vorgabe `abend`, `derive/varianten.ts:47`) müssen mitgezogen werden.

---

## (5) Offene Fragen an den Owner (je Empfehlung zuerst; laut Entscheid 112 über die Zentrale stellen)
1. **Vorschaubilder:** Gelten verkleinerte CC0-Vorschauen (etwa 160 px WebP, Original-Hash und Quelle im NOTICE) als zulässig? *Empfehlung: ja.* CC0 erlaubt es; «unverändert» bleibt für die HDRIs und Texturen selbst. Alternative: die Vorschaubilder der Quelle unverändert übernehmen, grösser und als PNG/JPG.
2. **Fehlt ein Himmelsbild oder eine Textur am Heim-PC:** *Empfehlung: Auftrag mit Satz abweisen* (E75). Alternative: flache Welt bzw. Modellmaterial mit Warnung.
3. **Auto-Kamera in KosmoOrbit:** *Empfehlung: wie Visbox `cameras:'auto'` und `cameras_auto`, der Heim-PC rechnet. Die Kegel kommen über einen neuen Brückenweg vom Heim-PC; ohne Brücke als «ungefähr» aus der eigenen Ableitung.* Alternative: KO behält `derive/kamera.ts` und bekommt die Parameter dort (zweite Rechnung, Drift). Ist zugleich eine Integrator-Frage.
4. **Mehrfachwahl am Stimmung-Knoten ohne Varianten-Knoten:** *Empfehlung: Der Render-Knoten bestellt je gewählte Stimmung einen Auftrag (Knopf «3 Bilder»). Hängt ein Varianten-Knoten dran, liest er seine Stimmungs-Achse aus dem Stimmung-Knoten (eine Quelle).*
5. **Vorgabe «Haus füllt»:** *Empfehlung 70 %* (`kameras.DECKUNGSGRAD`, gemessen). Auf dem Blatt stehen 30 %.
6. **«Weiss (Studio)»:** nur Himmelsbild und Satz, oder zusätzlich alle Oberflächen weiss (Lehm-Ersatz in Blender)? *Empfehlung: zusätzlich weiss.* Der Satz verspricht heute «keine Materialien».
7. **Fenster in der Oberfläche:** Gehören Türen zu «Fenster» oder zu «Übrige»? *Empfehlung: zu Übrige.* Eine eigene Art «Türe» kann später kommen.

### Critical Files for Implementation
- KO/packages/kosmo-contracts/src/render-scene.ts
- KO/packages/kosmo-kernel/src/derive/visgraph.ts
- KO/apps/kosmo-orbit/src/modules/vis/vis-jobs.ts (plus `grundlage.ts`, `NodeCanvas.tsx`)
- src/aiimaging/kosmo_szene.py (plus `abholer.py`, `kameras.py`)
- src/aiimaging/runners/blender_depth_stage.py
