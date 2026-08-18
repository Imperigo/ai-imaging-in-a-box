# Das Ökosystem, gelesen · und wo unser Code nicht hineinpasst

**Stand:** 2026-08-18 · **Auftrag:** die letzte grosse Wissensschuld aus `docs/PLAN.md`
abtragen — `KosmoPrepare`, `ArchitekturKosmos-Codex`, `KosmoPublish`, `KosmoDesign`,
`architekturkosmos-control-hub`, `Architektur-Cosmos`.

**Leitfrage war nicht** „was steht in diesen Repos", sondern: *Was muss unser Code können,
damit er in KosmoOrbit sauber hineinpasst — und wo tut er es heute nicht?*
Kapitel 7 ist die Antwort; alles davor ist der Beleg.

---

## 0 · Was ich gemacht habe — und was nicht

**Gemacht:**

- Sechs Repos read-only geklont, ausschliesslich ins Scratchpad ausserhalb des
  Projektverzeichnisses. Nichts kopiert, kein Code übernommen.
- Zusätzlich **`KosmoVis`** geöffnet — nicht auf der Leseliste, aber unvermeidlich:
  Das Ökosystem verweist an drei Stellen auf dessen `docs/RENDER_SCENE_CONTRACT.md`
  als den Vertrag, an den unsere Lane andocken soll (Kap. 6). Der teuerste Fund dieses
  Auftrags steht dort.
- Gelesen wurden vorrangig: MCP-Server (die tatsächlichen `inputSchema`/`outputSchema`),
  Handoff-Verträge, Cross-Lane-Memos, Job-Store-Formate. Also das, was Feldnamen trägt.

**Nicht gemacht:**

- **`KosmoDraw-Privat` nicht angefasst** — „Privat" im Namen, Regel 3.
- Nichts ausgeführt: keine Testsuite eines fremden Repos gestartet, keinen Render
  ausgelöst, nichts registriert. Alle Reifegrad-Angaben unten sind aus Code, Commits und
  Zählungen abgeleitet, nicht aus Läufen. Wo ich das nicht kann, steht es dabei.
- Die Ökosystem-Repos sind **nicht vollständig** gelesen. `KosmoPrepare` allein hat
  61 000 Zeilen Python; gelesen habe ich davon die MCP-Naht, die Handoff-Verträge und die
  Brücke zu unserer Lane. Kapitel 9 nennt, was liegen blieb.

**Regel 3, ausdrücklich angewandt:** Diese Repos enthalten reale Wettbewerbs-, Auslober-
und Ortsnamen, Adressen und Koordinaten aus echten Aufträgen — in Beispielen, Testfixtures
und Gold-Standard-Dateien. **Keiner davon steht in diesem Dokument.** Wo ein Beispiel eine
Struktur zeigen soll, nenne ich die Struktur und lasse den Inhalt weg; wo eine Aussage
ohne den konkreten Fall nicht trägt, schreibe ich „ein realer Wettbewerb" und nenne ihn
nicht. Das betrifft rund ein Dutzend Stellen. Auch die Farb-, Ebenen- und
Dateinamens-Verträge zwischen den Lanes habe ich nur so weit wiedergegeben, wie sie
Konvention und nicht Projektinhalt sind.

Geändert wurde in unserem Repo **nur diese Datei**. Nichts committet.

---

## 1 · Das Ökosystem, wie es sich heute darstellt

Das Bild aus `EINBINDUNG_KOSMOORBIT_2026-08-14.md` (KosmoOrbit ist Cockpit, die Lanes
liefern MCP-Werkzeuge) stimmt weiterhin — es ist nur **erheblich weiter gediehen**, als
jenes Dokument annehmen konnte.

Belegt aus dem Codex-Repo (`_overseer/E2E-PIPELINE-WETTBEWERB-2026-06-16.md`,
`_overseer/PIPELINE-FELD-ALIASE-2026-06-16.md`):

- **99 bis 113 MCP-Werkzeuge** waren im Juni 2026 in Odysseus registriert, über fünf
  Lanes (Prepare · Draw · Design · Vis · Publish) plus Systemwerkzeuge.
- Die **volle Kette Prepare → Draw → Design → Vis → Publish** ist einmal end-to-end an
  echten Geodaten gelaufen. Die Vis-Stufe meldete dabei korrekt „ComfyUI offline → Render
  gegatet" — genau das Verhalten, das der Freeze-Schutz verlangt.
- Die Feldnamen-Aliase, die unser `mcp_schemas.FELD_SYNONYME` nachbildet, sind aus
  genau dieser Validierung entstanden: Sie waren die Reparatur eines real gebrochenen
  Datenflusses, nicht eine Vorsichtsmassnahme.

Eine unabhängige Reifeschätzung aller acht Lanes vom 2026-06-29 liegt in
`KosmoDesign/docs/GROSSPLAN_KOSMOS_2026-06-29.md` (eigener Scan der Design-Lane, nicht
Selbstauskunft der jeweiligen Lane):

| Lane | Reife laut jenem Scan | Cadence |
|---|---|---|
| KosmoDraw | ~88 % | Engine eingefroren |
| KosmoOrbit | ~82 % | periodischer Scan |
| KosmoPrepare | ~82 % | eingefroren-grün |
| KosmoDesign | ~80 % | aktiv |
| KosmoPublish | ~72 % | Background-Worker |
| **KosmoVis** | **~65 %, „v1-Cut, Bau offen", blockiert** | Background-Worker |
| Control-Hub | ~25 %, eingefroren | blockiert auf Owner-Entscheid |
| Architektur-Cosmos | ~70 % | fremde Lane (Codex) |

**Das ist die gesuchte Gegenprobe zur PLAN-Schuld** „KosmoVis' Reife nicht nachgeprüft":
Eine *andere* Lane schätzt KosmoVis auf ~65 % und nennt es blockiert — dieselbe
Grössenordnung wie KosmoVis' Selbstauskunft. Es bleibt eine Schätzung aus demselben Haus,
aber es ist nicht mehr nur die Selbstauskunft.

---

## 2 · `KosmoPrepare` — Phase 0, der Zulieferer vor uns

**Was es ist.** Ein Blender-Add-on, das aus Wettbewerbsunterlagen ein aufbereitetes
3D-Arbeitsmodell macht: Standort und Terrain, Baurechts-Hüllen, Raumprogramm aus PDF,
Massing-Varianten mit Rangfolge, Export nach Phase 1. Schweiz-spezifisch (LV95, SIA 416,
swisstopo).

**Reifegrad — nüchtern.** Das ist **lauffähige Software, keine Absichtserklärung**:
125 Module in `core/`, **1112 Testfunktionen** in 103 Testdateien, ein
`setup.sh`-Bootstrap, ein Headless-Smoke über die ganze Kette. Die Tests laufen
ausdrücklich ohne Blender (reiner Python-Kern) — dieselbe Trennung, die unsere Regel 4
verlangt. Ich habe sie **nicht ausgeführt**; die Zahl 1112 ist gezählt, nicht gemessen.

Zwei ehrliche Abstriche:

- **Letzter Commit: 2026-06-22.** Die Annahme im Auftrag, das Repo sei am 18.08.
  bearbeitet worden, trifft nicht zu — das ist vermutlich das Datum der Repo-Spiegelung.
  Das Repo ruht seit zwei Monaten, passend zur Einstufung „eingefroren-grün".
- **Versionsangaben driften:** `README.md` sagt v0.84.0, `blender_manifest.toml` sagt
  v0.139.0, der `CHANGELOG` beginnt bei v0.132.0. Das ist kein Fehler in der Software,
  aber ein Hinweis, wie belastbar Selbstauskünfte in diesem Ökosystem sind.

**Lizenz: GPL-3.0-or-later** (`blender_manifest.toml`). Für uns heisst das: **Aus diesem
Repo darf kein Code übernommen werden.** Verträge und Feldnamen ja — die sind keine
Werke im urheberrechtlichen Sinn; Code nein.

**Feldnamen (MCP, acht Werkzeuge, alle mit `outputSchema`):**

| Ebene | Namen |
|---|---|
| Standort/Fläche | `parzelle_flaeche_m2` · `bauhuelle_flaeche_m2` · `landflaeche_m2` · `agf_max_m2` · `lv95` · `polygon_lv95` · `grenzabstand_m` · `max_height_m` |
| Programm | `total_hnf_m2` · `programm_hnf_m2` · `category_budgets` · `category_counts` · `annahmen` |
| Ergebnis | `empfohlen` · `ranking[]` · `review_ready` · `schritte[]` · `fragen[]` · `quelle` |

**Keine Überschneidung mit unseren Feldern.** Weder `ifc_path` noch `glb_path`, `up_axis`,
`bbox`, `depth_*` kommen im MCP-Vertrag von KosmoPrepare vor. Eine direkte Kante
KosmoPrepare → wir entsteht nicht und soll auch nicht entstehen: Dazwischen liegen Draw
(Geometrie) und der Phase-0-Export.

**Was KosmoPrepare aber als Datei liefert — und wo es uns betrifft:**

`docs/PHASE0_EXPORT_v0.1.md` definiert ein JSON-Manifest mit einem eigenen Kapitel
„**KosmoViz konsumiert daraus**", also für unsere Lane:

| Sektion | wofür gedacht |
|---|---|
| `terrain.mesh_file` + `terrain.orthofoto_file` | Backplate für den Render |
| `lod2_context.buildings_file` | Bestandsbauten als Mesh-Ebene |
| `lod2_facade_textures` | photoreale Bestandsfassaden statt Grau |
| `sun_settings.studied_dates` / `studied_hours` | Sonnenstand-Keyframes |
| `cosmos_references[]`, `praezedenz[]` | Stilrichtungs-Hinweise für die KI-Varianten |

Drei Befunde daraus, und alle drei sind für uns unangenehm:

1. **Die Geometrie heisst dort nicht `glb_path`, sondern `mesh_file` bzw.
   `buildings_file` — und sie sind verschachtelt** (`terrain.mesh_file`). `mergeInputs`
   zieht Kanten über *flache* Feldnamen. Eine Kante Phase-0-Export → wir entsteht also
   auch dann nicht, wenn jemand den Export als Knoten in die Pipeline hängt.
2. **Kein `up_axis`, nirgends.** Die Dateien sind glb, exportiert über
   `bpy.ops.export_scene.gltf` ohne gesetztes `export_yup` — also Blender-Default und
   damit glTF-konform Y-up. Das ist eine *Ableitung aus dem Default*, keine Zusage; der
   Vertrag schweigt. Unser `contracts.normalize_up_axis` lehnt fehlendes `up_axis` ab,
   und das ist hier genau richtig: Es gibt nichts zu raten, es gibt etwas zu vereinbaren.
3. **Koordinaten sind gegen den LV95-Ursprung verschoben,** nicht absolut — steht so im
   Kapitel „Konventionen". Unser `torwaechter` fängt absolute LV95-Koordinaten in float32
   ab; diese Dateien sind bereits entschärft. Gut für uns, aber wir sollten es wissen,
   statt es zu vermuten.

**Kameras — der einzige Ort im ganzen Ökosystem, an dem ein Kameravertrag existiert.**
`nodes/kosmodraw_bridge.py` schreibt in ein Übergabepaket eine `camera_presets.json`:

```
{name, location: [x,y,z], look_at: [x,y,z], lens_mm, type: "frontal"|"diagonal"}
```

Acht Kameras: vier frontal (N/O/S/W), vier diagonal, Augenhöhe 1,70 m, Radius = 1,5 ×
grösste Gebäudeausdehnung, 35 mm. Koordinaten sind **Blender-Weltkoordinaten in Metern,
Z-up**. Dazu ein `manifest.json` mit `lv95_origin`, `parcel_centroid_local`, `baubereiche[]`
(je `hoehe_m`, `area_m2`), `sun`.

Der Kommentar dort nennt die Quelle: die Owner-Vorgabe „standardisierte Kamerasetzung mit
geregeltem Gebäudeabstand und 1.7 m Augenhöhe, 8 Kameraperspektiven rundum Gebäude". Das
ist keine Erfindung der Lane, sondern der Plan (siehe Kap. 6.2).

**Nebenbefund zu `glb_path`:** KosmoPrepare *führt* das Feld `glb_path` — aber in
`core/trellis_client.py` und `core/fal_client.py`, den Rückgaben zweier
Bild-zu-3D-Cloud-Dienste. Eine glb aus einem generativen Dienst hat weder bekannten
Massstab noch bekannte Up-Achse. Diese Werkzeuge sind heute **nicht** als MCP exponiert;
würden sie es, hätte `glb_path` im Ökosystem einen dritten Erzeuger mit einer dritten
Bedeutung. Für unseren Torwächter ist das der interessanteste denkbare Eingang.

---

## 3 · `ArchitekturKosmos-Codex` — hier stehen die Konventionen

Das ist das Repo, das der Auftrag richtig eingeschätzt hat: **Wenn irgendwo
übergreifende Festlegungen stehen, dann hier.** Es ist kein Produkt, sondern das
Arbeitsgedächtnis der System-Lane („Overseer") — Tagespläne, Cross-Lane-Memos,
Handoff-Briefe, Kopien der Backend-Endpunkte, dazu ein einvendorter Starter des
Control-Hub.

Letzter Commit 2026-08-10. Kaum Code, viel Festlegung. **Vier Dokumente daraus sind für
uns bindend.**

### 3.1 `_overseer/MCP-V1-TOOL-VERTRAEGE-2026-06-16.md` — der Bauplan unserer Lane

Dort steht, welche drei Werkzeuge die Render-Lane bekommen soll, mit vollständiger
Feldliste. Es sind exakt unsere drei — mit anderen Namen:

| Ökosystem-Plan | Unser Werkzeug |
|---|---|
| `kosmovis_enqueue_render` | `aiimaging_enqueue_render` |
| `kosmovis_enqueue_depth_pass` | (bei uns Teil von `enqueue_render`, `art: "depth"`) |
| `kosmovis_render_job_status` | `aiimaging_query_render` |
| — | `aiimaging_check_geometry` (haben nur wir) |

Ebenfalls dort, und für uns wichtig: die **Gating-Klassen** des Ökosystems —
🟢 read-only (CPU) · 🟠 write-gated (schreibt Dateien) · 🔴 gpu-gated (Owner-Freigabe +
Leerlauffenster). Beide Enqueue-Werkzeuge sind 🔴, das Status-Werkzeug 🟢.

### 3.2 `_overseer/VIS-JOB-INFRA-KONTRAKT-2026-06-17.md` — das Auftragsformat, festgeschrieben

Ein **verbindlicher Vertrag zwischen zwei Lanes** über die Auftragsablage. Wörtlich
festgelegt:

- Ablageort **`/mnt/data/ArchitekturKosmos/render-jobs/`** (Umgebungsvariable
  `KOSMOVIS_RENDER_JOBS_DIR`), eine JSON-Datei je Auftrag, das Verzeichnis *ist* die
  Warteschlange.
- Kennung **`vis-<unix_ts>-<6hex>`**.
- Token-Muster **`CONFIRMED_RENDER_*`**.
- Statusvokabular `awaiting_approval | queued | running | done | error | cancelled`.
- Phasenvokabular `IDLE | RENDER | SUBMIT | POLLING | DOWNLOAD | DONE | ERROR`.
- Satzfelder: `job_id`, `kind`, `status`, `created_at`, `approval_token`,
  `idle_window_only`, `params`, `progress`, `phase`, `outputs{variant_paths, pass_paths}`,
  `error`, `updated_at`.
- Arbeitsteilung: Die Lane schreibt und liest Aufträge; **den Scheduler baut die
  System-Lane**, nicht wir.

Unsere `jobs.py` trifft davon Status, Token-Präfix und `vis-`-Präfix **exakt** — das ist
kein Zufall, sondern kommt daher, dass Phase 0 KosmoVis' Vorgänger gelesen hat. Die
Abweichungen sind in Kap. 7.3 aufgelistet, und sie sind real.

### 3.3 `_overseer/backend-pipeline-endpoints/pipeline_routes.py` — das Read-only-Tor

Der wichtigste Fund dieses Repos, weil er unsere Selbstauskunft entwertet:

```python
_BUILTIN_SERVERS = {"image_gen", "memory", "rag", "email"}

def is_read_only_tool(qualified_name):
    ...
    if tool_name in READ_ONLY_MCP_TOOLS:      # harte Allowlist
        return True
    if server_id not in _BUILTIN_SERVERS:     # Dritt-Server → keine Heuristik
        return False
    ...                                       # Verb-Heuristik nur für Builtins
```

Das heisst: **Die Verb-Heuristik („query_", „list_", „get_") gilt für uns nicht.** Wir
sind ein Dritt-Server. Jedes unserer Werkzeuge, das ohne Admin-Rechte aus dem Cockpit
aufrufbar sein soll, muss namentlich in `READ_ONLY_MCP_TOOLS` eingetragen werden — in
einer Datei, die uns nicht gehört. Unser Vertragsfeld `"readonly": True` in
`mcp_schemas.WERKZEUGE` hat **keinen Leser**. Es ist eine Behauptung, kein Schalter.

Ebenfalls hier belegt: Der qualifizierte Name lautet `mcp__{server_id}__{tool_name}`, und
`server_id` ist die **bei der Registrierung vergebene Datenbank-Kennung** — in den
Handoffs stehen Werte wie `mcp__589e9f05__kosmodraw_bauteil_layers`. Unser
`mcp_schemas.voller_name()` bildet `mcp__aiimaging__…`; das ist ein Sonderfall, kein
Regelfall. Kleine Korrektur an `EINBINDUNG_KOSMOORBIT_2026-08-14.md` §8.3, siehe Kap. 8.

### 3.4 `_overseer/PIPELINE-FELD-ALIASE-2026-06-16.md`

Bestätigt unsere `FELD_SYNONYME` wörtlich (drei Gruppen, dieselben Mitglieder) und nennt
zusätzlich einen Warnfall, den wir nicht kennen: **`alias-conflict`** — liefern zwei
Vorgänger dieselbe Alias-Grösse mit verschiedenen Werten, entscheidet still die
Kantenreihenfolge. KosmoOrbit macht das seit Juni sichtbar. Unsere
`pruefe_verdrahtbarkeit` kennt nur `missing-required` und `dead-edge`; der dritte Befund
fehlt.

---

## 4 · `KosmoPublish` — der Abnehmer nach uns

**Was es ist.** Aus dem 3D-Modell werden bemasste 2D-Pläne (Grundriss, Schnitt, Fassade)
und A0-Wettbewerbsplakate. Blender-Add-on plus headless-CLI.

**Reifegrad.** **~2015 Testfunktionen**, 18 dokumentierte Ausbaustufen, Headless-CLI,
Cache-Optimierungen mit gemessenen Zahlen. Letzter Commit 2026-07-30 — von allen
gelesenen Repos das zuletzt aktive nach Architektur-Cosmos. Auch hier: gezählt, nicht
ausgeführt. Der Grossplan der Design-Lane setzt es auf ~72 % und nennt einen
blockierenden Fehler in der wichtigsten Funktion (`render_ifc_plans` lieferte auf einem
realen IFC null Pfade); die Overseer-Notiz vom 16.06. meldet dieselbe Funktion dagegen
als empirisch verifiziert. **Beide Aussagen stehen nebeneinander im Ökosystem, ich kann
sie nicht auflösen.**

**Lizenz: GPL-3.0-or-later** im Haupt-Manifest — bei einem einzelnen Unterordner
(`blender_addon/blender_manifest.toml`) steht dagegen `SPDX:MIT`. Ein Widerspruch
innerhalb desselben Repos. Für uns gilt die strengere Angabe: **kein Code von dort.**

**Feldnamen:**

| Werkzeug | Ein | Aus |
|---|---|---|
| `kosmopublish_render_ifc_plans` | **`ifc_path`** · **`out_dir`** · `scale` · `floorplans`/`section`/`elevation`/`space_labels` | `status` · `outputs[]` · `n_outputs` · `timings_s` · **`error_msg`** · `notes[]` |
| `kosmopublish_assess_ifc_plan_readiness` | `ifc_path` | `status` · `storey_count` · `unit_scale` · `storeys[]` · `issues[]` · `recommendations[]` |
| `kosmopublish_program_totals` | `areas` | `GF` · `NGF` · `NF` · `HNF` · `unknown_codes[]` |

**Das ist die einzige echte Feldnamen-Überschneidung mit uns:** `ifc_path` und `out_dir`.
Beide Werkzeuge — ihres und unseres — sind *Verbraucher* von `ifc_path`. Das ist kein
Konflikt, sondern die erwartete Parallelschaltung hinter demselben Erzeuger.

**Aber `out_dir` ist eine Falle.** Wir führen `out_dir` als **Eingabe *und* Ausgabe**
(`mcp_schemas._ausgang_enqueue`). KosmoPublish führt `out_dir` nur als Eingabe. Hängt
jemand uns *vor* `render_ifc_plans`, schreiben beide Werkzeuge in dasselbe Verzeichnis —
denn `mergeInputs` reicht unser Ausgabe-`out_dir` an dessen Eingabe weiter, ohne dass es
jemand verdrahtet hätte. Das ist genau die Klasse von stiller Kante, für die Phase 0
angesetzt war, nur in der anderen Richtung.

**Wer nimmt unsere Bilder ab? Heute niemand.** Die Plakat-Slots von KosmoPublish
(`nodes/layout_templates.py`) matchen **SVG-Dateinamen per Regex**:

```
FP_EG · FP_01 · FP_1.OG   (Grundrisse)
SE_A · SE_B               (Schnitte)
FA_N/S/E/W                (Fassaden)
AX_…                      (Axonometrie)
LAGEPLAN · SITE
```

Es gibt einen Slot `hero_view` — die naheliegende Stelle für ein Rendering — aber auch
er sucht SVG (`SE_A|AX_|FA_S`). Ein PNG hat im Plakat-Composer keinen Platz und keine
Namenskonvention. Unser `images[]`-Ausgabefeld hat im Ökosystem **keinen Verbraucher**.

---

## 5 · `KosmoDesign` und zwei kleinere Repos

### 5.1 `KosmoDesign`

**Was es ist.** Die Entwurfs-Werkbank: Skizze/Sprache → Modell, mit einem „Design-Gewissen"
(normbasierte Prüfung) und einem Review-Gate. Sie besitzt seit Juni auch die
KosmoDraw-Engine und koordiniert laut eigenem Grossplan das ganze Ökosystem.

**Reifegrad.** 282 Python-Dateien, Tests nach der Konvention `*_test.py` mit rund 580
Testfunktionen in `core/tests` und `layout/tests`. Letzter Commit 2026-08-01. Aktiv.
Das MCP-Seam ist nachweislich live: Ein Cross-Lane-Memo belegt 23 registrierte Werkzeuge,
davon 15 mit `output_schema`, und einen autonomen 16-Runden-Lauf, in dem ein lokales
Sprachmodell drei davon selbst verkettet hat.

**Lizenz: keine.** Kein `LICENSE`, keine SPDX-Angabe. Privates Repo ⇒ faktisch „all
rights reserved". **Kein Code übernehmbar.**

**Für uns relevant ist nicht der Code, sondern `contracts/`** — sieben JSON-Schemas mit
einer ausgeschriebenen Versionierungs-Konvention:

> Jeder Vertrag deklariert sein `schema_version`-Feld als
> `{"type":"string","enum":[…]}` — die unterstützten Versionen explizit, nicht als
> freien String. (Owner-Entscheid 22.06., gesetzt 24.06.)

Daneben lebt eine zweite, ältere Form: `publish_handoff.schema.json` führt
`"schema": {"const": "kosmodesign.publish-handoff/0.1"}`. **Unser `contracts.SCHEMA_ID =
"aiimaging.render-scene/v1"` folgt genau dieser zweiten Form** — sie ist also
präzedenzgestützt, aber nicht die Form, auf die sich das Ökosystem zuletzt geeinigt hat.

Weitere Konventionen aus denselben Schemas, die wir teilen sollten: Einheiten hängen am
Feldnamen (`elevation_m`, `height_m`, `area_m2`, `site_area_m2`) — nie am Kommentar. Wir
machen das bei `bbox` nicht (Meter stehen nur in der Beschreibung).

### 5.2 `architekturkosmos-control-hub`

**Reifegrad: eingefroren.** Letzter Commit 2026-06-05, seither nichts. Der Grossplan
setzt es auf ~25 % und stellt es zur Disposition („archivieren / Komponenten plündern /
reaktivieren" — offener Owner-Entscheid). Der Inhalt ist zudem als Kopie im Codex-Repo
einvendort. **Es ist im Wesentlichen ein Konzept-Repo mit einem FastAPI-Skelett.**

Zwei Dinge daraus sind trotzdem wertvoll:

1. **`docs/pipeline/PIPELINE_PHASE_0_1.md` ist die Urfassung der Vision** — der Text,
   aus dem alle Lanes abgeleitet sind, in der Sprache des Owners. „Toolkit 2 — Arch
   Visualizer" ist unsere Lane, in 15 Schritten. Siehe Kap. 6.2; das ist das eigentliche
   Pflichtenheft.
2. **Ein drittes Statusvokabular:** `draft · queued · running · waiting_for_approval ·
   paused · completed · failed · cancelled`. Es kollidiert mit dem Job-Store-Vertrag
   (`awaiting_approval`, `done`, `error`). Da das Repo eingefroren ist, gewichte ich das
   niedrig — aber es zeigt, dass „Statuswerte des Ökosystems" nicht eindeutig ist.

### 5.3 `Architektur-Cosmos`

**Was es ist.** Die öffentliche Website und das kuratierte Referenzarchiv (Next.js,
Cloudflare). Aktivstes der gelesenen Repos (Commit 2026-08-13), ~587 Tests in TS/JS,
fremde Lane (Codex-betreut).

**Für uns ist das die Quelle der Stil-Referenzen** — also der Eingang unserer
`stil_qa.py`. Und dort steht eine Regel, die wir heute nicht abbilden:

`docs/media-and-model-policy.md` führt eine **Rechte-Statusvokabel je Asset**:

```
placeholder · needs_permission · licensed · public_domain · own_work
```

plus `private_research` (nur lokale Analyse). **Öffentlich verwendet werden darf nur
`own_work`, `licensed`, `public_domain`.** Der API-Vertrag zum Referenzabruf
(`KosmoPrepare/docs/COSMOS_API_CONTRACT.md`, §B.2) verschärft es für Bilder ausdrücklich
auf **„nur cc-by/cc-by-sa"**.

Modelle liegen als glb-Ebenen (`full`, `mass`, `low`, `site`, `structure`, `tectonic`)
unter einer festen Schlüsselkonvention; das Match-Signal für Referenzen ist ein
`themes[]`-Vokabular von ~23 Begriffen.

---

## 6 · `KosmoVis` — der Vertrag, an den wir andocken sollen

Nicht auf der Leseliste, aber unumgänglich: Drei Cross-Lane-Memos sagen, andere Lanen
sollen an KosmoVis' `docs/RENDER_SCENE_CONTRACT.md` **andocken**. Der Vertrag existiert
seit 2026-06-16 und heisst `kosmovis.render-scene/v1`.

### 6.1 `render-scene.json` — zwei Verträge, ein Dateiname

| | KosmoVis `kosmovis.render-scene/v1` | Wir `aiimaging.render-scene/v1` |
|---|---|---|
| Geometrie | `geometry: {path, format}` | `geometry: {ifc_path \| glb_path, up_axis, needs_rotation}` |
| Ausgabe | `out` | `out_dir` |
| Kameras | `cameras: "auto" \| "saved" \| [namen]` | — |
| Render | `render: {resolution, samples, faithful, sun{lat,lon,datetime,presets}}` | `aufloesung`, `samples` (flach, im MCP-Argument) |
| Stil | `style: {mode: none\|redux\|ipadapter\|lora, refs[], lora, prompt}` | — |
| Modellwahl | `vis: {skip, backbone, upscale}` | `backbone.py` als Registry, kein Vertragsfeld |
| Projekt | `project` | — |

Und der Satz, an dem sich alles entscheidet, aus §1a jenes Vertrags:

> „Einheiten: Meter; **Z = oben**; Projekt-Nullpunkt = Parzellen-Nullpunkt."

**Das ist die dritte, widersprüchliche Up-Achsen-Angabe im Ökosystem** — und die erste,
die *unserer* Kette direkt widerspricht:

| Quelle | Aussage |
|---|---|
| KosmoDraw `glb_export_runner.py` | `up_axis: "Z"` (rohe IFC-Koordinaten) |
| KosmoVis `ifc_to_glb.py` (Phase-0-Befund) | `up_axis: "Y (glTF-2.0-Standard)"` |
| **KosmoVis `RENDER_SCENE_CONTRACT.md` §1a** | **„Z = oben"** für dieselbe Eingangs-glb |
| KosmoPrepare Phase-0-Export | schweigt (Blender-Default ⇒ Y-up) |
| Wir | `up_axis` Pflicht, Y-up normalisiert, Z→Y wird gedreht |

KosmoVis widerspricht sich also **zwischen der eigenen Dokumentation und dem eigenen
Code**. Ich habe nichts ausgeführt und kann nicht sagen, welche Seite gilt. Was ich sagen
kann: **Die Entscheidung von Phase 2, `up_axis` zum Pflichtfeld zu machen und nichts zu
raten, war richtig — und sie ist durch diesen dritten Beleg besser begründet als vorher.**
Bei drei Erzeugern mit drei Angaben ist jeder Default eine stille Verdrehung.

### 6.2 Das Pflichtenheft unserer Lane: „Toolkit 2 — Arch Visualizer"

Aus `architekturkosmos-control-hub/docs/pipeline/PIPELINE_PHASE_0_1.md`, 15 Schritte.
Verdichtet, mit unserem Stand daneben:

| Erwartet | Bei uns |
|---|---|
| Gebäudeerkennung: Hüllbox über das entworfene Volumen, Abruf von Material/Tragstruktur | ansatzweise (`bbox`, `torwaechter`), Bauteildaten nein |
| **Standardisierte Kamerasetzung**: geregelter Abstand, 1,70 m Augenhöhe, 8 Perspektiven | **fehlt vollständig** |
| Manuelle Kameras überschreiben, speichern, als Knopf ablegen | fehlt |
| **Materialkatalog**: erfassen, durch HQ-Texturen ersetzen, Vorschau | fehlt |
| KI-Materialgenerierung, wenn keine Textur vorliegt | fehlt |
| Referenzprojekte aus der Datenbank als Stilgrundlage | teilweise (`stil_qa` nimmt Referenzbilder, ohne Anbindung) |
| **Cycles-Multipass** auslösen | **vorhanden** (`seams.glb_zu_multipass`) |
| 3D-Assets automatisch setzen/streuen (Menschen, Möbel, Vegetation) | fehlt |
| **Kompositor**: Einzelbilder zu Ebenen zusammenlegen | fehlt |
| **KI-Bildvarianten** auf Basis des Kompositors | vorhanden (`render.py`), nie ausgeführt |
| Stilanpassungen in den KI-Bildern, Änderungen zurückschicken | fehlt |
| **Erneut generieren, ohne Cycles neu zu rendern** („nutzt letzten Stand") | **teilweise vorhanden** — genau das leistet `kette.py` |
| Export-Paket: Cycles-Renders + KI-Varianten | fehlt |

Der Zwischenstand ist ehrlich gemischt: Der schwierigste Teil (Multipass über die
Prozessgrenze, Zwischenspeicher, Doppel-Gate) steht, der bedienbare Teil (Kameras,
Material, Assets, Paket) fehlt vollständig. Was das Pflichtenheft **nicht** verlangt und
wir trotzdem haben, ist die messbare Geometrie-Treue — das bleibt unser eigener Beitrag.

### 6.3 KosmoVis hat unsere drei Werkzeuge bereits gebaut

`integrations/odysseus/kosmovis_mcp_server.py` enthält heute:

- `kosmovis_enqueue_render` · `kosmovis_enqueue_depth_pass` · `kosmovis_render_job_status`
  — die Trias aus Kap. 3.1, mit exakt den geplanten Feldnamen.
- `kosmovis_query_qa_verdict` — **ein Doppel-Gate-Leseverfahren.** Es liest
  `render-result.json` und leitet das Urteil neu ab (fail-closed, dem gespeicherten Wert
  wird nicht vertraut).
- `render_job_store.py` — eine Zeile-für-Zeile-Umsetzung des Job-Store-Vertrags aus 3.2.

Damit ist die Frage „was baut unsere Lane, was gibt es schon" beantwortet: **Es gibt
schon einiges, und es trägt andere Namen als unseres.** Der Job-Store dort und die
`jobs.py` hier sind zwei Umsetzungen desselben Vertrags, die einander nicht lesen können.

Der Reifevorbehalt bleibt: Der Pilot-Runner `01_workflow/_pilot/run_kosmovis_stage.py`
schreibt eine Datei **`kosmovis_stage.json`**; der Vertrag §2 verspricht
**`render-scene-result.json`**; das QA-Werkzeug liest **`render-result.json`**. Drei
Ergebnisdateinamen in einer Lane. Das ist der konkrete Beleg für „~65 %, Bau offen" — die
Naht ist beschrieben, aber nicht geschlossen.

---

## 7 · Wo unser Code heute nicht hineinpasst

Zwölf Befunde, nach Kosten sortiert. „Tote Kante" heisst durchgängig: Es entsteht keine
Verbindung, und **es wird kein Fehler gemeldet**.

### 7.1 ⛔ Unsere QA schreibt nicht, was das Ökosystem liest

Das Ökosystem hat die Landestelle für unser Doppel-Gate bereits gebaut.
`kosmovis_query_qa_verdict` liest aus `render-result.json` diese Struktur:

```
{ "schema": …, "generated_at": …,
  "qa": { "style":    { "style_score": …, "threshold": … },
          "geometry": { "geometry_fidelity": …, "threshold": … } } }
```

und gibt nach aussen `released` (harter Freigabe-Boolean, nie null), `passed`
(dreiwertig), `style_passed`/`geometry_passed`, `style_status`/`geometry_status`
(`ok|fehlt|degeneriert`) und `fail_reasons[]`.

Unser `gate.doppel_gate` gibt zurück: `bestanden`, `geometrie`, `stil`, `maengel`,
`begruendung`. Die Teil-Urteile tragen `score`, `schwelle`, `bestanden`.

| Ökosystem | Wir |
|---|---|
| `released` (fail-closed, nie null) | `bestanden` (bool) |
| `passed` (dreiwertig: ja/nein/unbekannt) | — |
| `style_score` | `stil.score` |
| `geometry_fidelity` | `geometrie.score` |
| `threshold` | `schwelle` |
| `fail_reasons[]` | `maengel[]` |
| `style_status`/`geometry_status`: `ok\|fehlt\|degeneriert` | — |

**Kosten:** Das ist der Fund mit dem grössten Hebel, weil er in beide Richtungen wirkt.
Unser wissenschaftlicher Kern — die messbare Geometrie-Treue — hat im Ökosystem eine
fertige, bereits verdrahtete Abfragestelle, und wir bedienen sie nicht. Umgekehrt fehlt
uns deren dreiwertige Ehrlichkeit: Wir unterscheiden nicht zwischen „durchgefallen" und
„nicht beurteilbar, weil die Evidenz fehlt oder degeneriert ist". Für die
Schwellenstudie ist genau das die interessante dritte Kategorie.

### 7.2 ⛔ `aufloesung`, `torwaechter`, `art` — deutsche Feldnamen an der Naht

Unsere Bibliothek ist auf Deutsch, und das ist richtig und soll bleiben. **Die Feldnamen
an der MCP-Naht sind aber kein Deutsch und kein Englisch, sondern ein Protokoll.**

| Unser Feld | Ökosystem | Wirkung |
|---|---|---|
| `aufloesung` (Eingabe `enqueue_render`) | `resolution` | tote Kante |
| `torwaechter` (Ausgabe) | — (kein Gegenstück) | niemand liest es |
| `art` (Auftragsfeld) | `kind` | Scheduler findet die Auftragsart nicht |
| `erstellt` / `geaendert` | `created_at` / `updated_at` | dito |
| `ergebnis` / `fehler` | `outputs` / `error` | dito |
| `approval_token` (Eingabe) | `owner_approval_token` | Freigabe kommt nicht an |
| `out_dir` (Ausgabe) | `output_dir` (Ausgabe der Trias) | Nachfolger findet das Verzeichnis nicht |

`aufloesung` ist der teuerste davon: Setzt jemand im Cockpit einen Knoten mit `resolution`
davor — der Vorgabewert des Ökosystems ist `"1920x1440"` —, kommt bei uns nichts an, und
wir rendern still in 512 px. Nebenbei: Deren `resolution` ist ein **String `"BxH"`**,
unsere `aufloesung` eine **ganze Zahl** (Kantenlänge). Selbst nach dem Umbenennen wäre der
Typ noch verschieden.

**`approval_token` gegen `owner_approval_token` ist der gefährlichste,** weil er
*fail-safe* danebengeht: Ein durchgereichtes `owner_approval_token` erreicht unser Feld
nicht, der Auftrag bleibt auf `awaiting_approval` — die Freigabe wirkt einfach nicht. Kein
Schaden, aber ein Fehler, den niemand als Fehler sieht.

### 7.3 ⛔ Unsere Auftragsdatei ist für den Scheduler des Ökosystems unlesbar

Der Scheduler ist **nicht unsere Lane** (Kap. 3.2, ausdrücklich). Er liest
`<job_id>.json` und entscheidet nach `status`, `approval_token`, `idle_window_only`.

| Vertrag | Unser Satz | Folge |
|---|---|---|
| `kind` | `art` | Auftragsart unbekannt |
| `created_at` / `updated_at` | `erstellt` / `geaendert` | Alter nicht ermittelbar |
| `outputs: {variant_paths[], pass_paths{}}` | `ergebnis` (frei) | Ergebnispfade nicht auffindbar |
| `error` | `fehler` | Fehler unsichtbar |
| `progress`, `phase` | fehlen beide | keine Fortschrittsanzeige |
| `approval_token` (Wert steht in der Datei) | `freigegeben: true` (Token **nie** auf Platte) | **Scheduler kann die Freigabe nicht prüfen** |
| `job_id` `vis-<unix_ts>-<6hex>` | `vis-<JJJJMMTTHHMMSS>-<6hex>` | asymmetrisch, siehe unten |
| Ablage `/mnt/data/ArchitekturKosmos/render-jobs/`, Env `KOSMOVIS_RENDER_JOBS_DIR` | `/tmp/aiimaging-jobs`, Env `AIIMAGING_JOB_DIR` | zwei Warteschlangen, die einander nicht sehen |

**Die Kennung ist asymmetrisch inkompatibel,** und das ist eine genaue Aussage: Deren
Muster ist `^vis-\d+-[0-9a-f]{6}$` — unsere 14-stellige Kennung besteht dort. Unser
Muster ist `^vis-\d{14}-[0-9a-f]{6}$` — deren zehnstellige Unix-Zeit besteht bei uns
**nicht**. Wir lehnen fremde Aufträge ab, sie nehmen unsere an.

**Zum Token muss man Stellung beziehen, nicht nur berichten.** Unsere `jobs.py` legt das
Token bewusst nie ab, mit einer im Code ausgeschriebenen Begründung: „Das Token ist eine
Befugnis; eine Auftragsdatei ist für jeden lesbar, der das Verzeichnis sieht." Das ist
sachlich richtig, und der Ökosystem-Vertrag ist an dieser Stelle schwächer — er legt eine
Befugnis in eine Datei, die als geteiltes Verzeichnis explizit für zwei Lanes lesbar ist.
**Aber:** Unser `freigegeben: true` ist für einen fremden Scheduler wertlos, weil es
genau das ist, was ein Angreifer schreiben würde. Wer die Datei manipulieren kann, setzt
das Flag. Der Vertrag prüft wenigstens ein Muster. Das ist eine Frage für den Owner und
die System-Lane, keine, die wir einseitig entscheiden können — aber wir sollten sie
stellen, statt still ein unlesbares Format zu schreiben.

### 7.4 ⛔ Wir haben keine Kameras, und die Kette hat welche

Es gibt keinen Kamerabegriff in unserem Code. Das Ökosystem hat:

- den Vertrag (`camera_presets.json`: `name`, `location`, `look_at`, `lens_mm`, `type`),
- das Eingabefeld (`cameras: "auto" | "saved" | [namen]`),
- die Ausgabestruktur (`render-scene-result.json`: `cameras[].passes.{beauty, depth,
  depth_method, material, material_id}`, `ai_variant`, `qa`),
- die Verzeichniskonvention (`<out>/<kameraname>/render_<kamera>_<pass>.png`, KI-Variante
  unter `<kamera>/final/`),
- und ein eigenes Werkzeug `kosmovis_list_cameras`.

Unser Multipass rendert **eine** Ansicht in flache Dateien mit deutschen Namen
(`tiefe_norm.png`, `tiefe_*.exr`, `material_id.png`, `beauty_*.png`).

Das ist mehr als ein fehlendes Feature: Solange wir keine Kamera-Identität führen, kann
unsere Geometrie-QA ihr Urteil nicht an eine Ansicht binden. Das Ergebnisformat des
Ökosystems hat den `qa`-Block **pro Kamera**. Unser Gate urteilt über ein Bild ohne Namen.

### 7.5 ⛔ Unser `readonly: True` liest niemand

Kap. 3.3. Die Verb-Heuristik gilt nur für vier eingebaute Server; wir sind ein
Dritt-Server, für uns entscheidet allein die fest verdrahtete Allowlist
`READ_ONLY_MCP_TOOLS` im Backend. **Alle drei unserer Werkzeuge landen heute hinter
`require_admin`** — auch `aiimaging_query_render`, das nichts tut als lesen, und auch
`aiimaging_check_geometry`, das nur rechnet.

Das ist keine Umbenennung, sondern eine Eintragung in einer fremden Datei. Der Weg dahin
ist der Cross-Lane-Brief an die System-Lane; das Muster dafür liegt in
`_overseer/handoffs/` mehrfach vor.

Nebenbei: **`check` ist auch kein Read-Verb des Ökosystems.** Die Liste lautet `read, get,
list, search, fetch, query, describe, overview, inspect, view, show, lookup, status,
count, find, preview`. Selbst wenn die Heuristik für uns griffe, fiele
`check_geometry` durch — `inspect_geometry` oder `preview_geometry` fiele nicht durch.

### 7.6 ⚠️ Zwei `render-scene.json`, ein Dateiname

Kap. 6.1. `kosmovis.render-scene/v1` und `aiimaging.render-scene/v1` haben denselben
Dateinamen und unvereinbare Strukturen (`geometry.path` gegen `geometry.ifc_path`, `out`
gegen `out_dir`). Beide sind Verträge der Render-Lane.

Das ist noch keine tote Kante — die Dateien treffen sich nirgends. Es wird eine, sobald
jemand „die render-scene.json" sagt und zwei verschiedene Dinge meint. Der saubere Ausweg
ist entweder ein anderer Dateiname für unseren Vertrag oder eine echte Übernahme des
KosmoVis-Vertrags mit unseren Ergänzungen (`up_axis` als Pflichtfeld ist die wichtigste;
KosmoVis hat es nicht, und es ist genau das Feld, dessen Fehlen die Kette still verdreht).

### 7.7 ⚠️ Der Treue-Regler heisst dreimal anders

| Ort | Name | Wertebereich |
|---|---|---|
| `render-scene.json` | `faithful` | 0..1, „1.0 = Cycles-treu ↔ 0.0 = KI-frei" |
| `kosmovis_enqueue_render` | `faithful_slider` | 0..1, „structural faithfulness (denoise)" |
| Wir (`render.py`, Schwellenstudie) | `controlnet_staerke` | 0..1 |

Die **Bedeutung ist dieselbe**, die Richtung möglicherweise nicht: „ControlNet-Strength"
und „denoise" laufen gegenläufig. Das ist genau die Fehlerklasse aus `FIELD_ALIAS_GROUPS`
— zwei Felder, die gleich heissen sollen und es nicht dürfen, solange die Richtung
ungeklärt ist. Für die zweite Hälfte der Schwellenstudie ist das keine Nebensache: Eine
Punktwolke über `controlnet_staerke` ist nur dann vergleichbar mit den Werten des
Ökosystems, wenn dieselbe Achse gemeint ist.

### 7.8 ⚠️ `depth_method` und `depth_png` — wir liefern mehr und sagen es anders

Das Ökosystem führt je Kamera `passes.depth` (**PNG**) und daneben `depth_method` mit
drei belegten Werten: `compositor_z | foreach_z | emission_fallback`. Es hält also fest,
**wie** die Tiefe zustande kam — weil die drei Wege unterschiedlich genau sind.

Wir liefern `depth_exr` (echte Meterwerte) **und** `depth_png` (normalisiert, mit
Rückrechnungsformel und aktiver Warnung über den Silhouetten-Verlust) und führen
zusätzlich `depth_normalisierung` und `depth_png_fehler`. Sachlich ist das der reichere
Befund. Aber:

- `depth_exr` steht in unserem `outputSchema` von `query_render`, `depth_png` nicht —
  wer die PNG will, findet sie nicht.
- `depth_method` fehlt bei uns ganz. Unser Weg entspricht am ehesten `compositor_z`; das
  zu deklarieren kostet ein Feld und macht einen Vergleich über Lanes hinweg erst möglich.

### 7.9 ⚠️ Der `hero_view`-Slot nimmt kein PNG

Kap. 4. KosmoPublish matcht Plakat-Slots über SVG-Dateinamen (`AX_`, `FP_`, `SE_`,
`FA_`, `LAGEPLAN`). Unser Bildergebnis hat weder Format noch Namensschema, das dort
ankommt. **Der letzte Meter der Kette — vom fertigen Render aufs Abgabeplakat — existiert
im Ökosystem nicht.** Das ist keine Bringschuld von uns allein, aber es ist die Antwort
auf die Frage „wer nimmt unsere Bilder ab": heute niemand.

### 7.10 ⚠️ Unsere Stil-Referenzen haben keinen Rechte-Status

`stil_qa` nimmt eine Liste Referenzbilder und misst dagegen. Das Referenzarchiv, aus dem
diese Bilder kommen sollen, führt je Asset einen Rechte-Status (`own_work`, `licensed`,
`public_domain`, `needs_permission`, `placeholder`, `private_research`) und der
API-Vertrag beschränkt Bilder ausdrücklich auf **cc-by/cc-by-sa**.

Wir prüfen Modell-Lizenzen vorbildlich (`lizenzquelle.py`, drei Registries, Regel 1
ausführbar) und **Asset-Rechte gar nicht**. Für die Stil-QA ist das nur ein Schönheitsfehler
— gemessen wird lokal. Für ein **Stil-LoRA** (PLAN, Phase 4) ist es keiner: Ein auf
`needs_permission`-Bildern trainiertes LoRA ist genau das, was Regel 3 und Regel 1
gemeinsam ausschliessen, und der Rechte-Status steht bereits im Datenmodell — er müsste
nur gelesen werden.

### 7.11 ⚠️ `out_dir` als Ausgabefeld ist eine unbeabsichtigte Kante

Kap. 4. Wir geben `out_dir` aus, KosmoPublish nimmt `out_dir` entgegen. `mergeInputs`
verkettet das von selbst. Gewollt ist das nicht: Unser Ausgabeverzeichnis ist der Ort für
Renders, deren Eingabefeld der Ort für Plan-SVGs. Zwei Werkzeuge schreiben nach demselben
Pfad, ohne dass es jemand verdrahtet hat.

Ein Ausgabefeld `output_dir` (nach dem Vorbild der Trias) hätte diese Nebenwirkung nicht
und wäre zugleich der Name, den die Nachbarlane erwartet — 7.2 und 7.11 haben dieselbe
Lösung.

### 7.12 ℹ️ `pruefe_verdrahtbarkeit` kennt den dritten Befund nicht

KosmoOrbit meldet seit Juni drei Arten: `missing-required`, `dead-edge` und
**`alias-conflict`** (zwei Vorgänger liefern dieselbe Alias-Grösse mit verschiedenen
Werten; die Kantenreihenfolge entscheidet still). Unsere Portierung kennt die ersten
beiden. Das ist die kleinste Lücke der Liste, aber unsere Nachbildung behauptet, KosmoOrbits
Prüfung nachzubilden — und tut es zu zwei Dritteln.

### Was **passt** — der Vollständigkeit halber

Das Bild wäre falsch ohne die Gegenliste. Folgendes deckt sich exakt:

- Statusvokabular der Aufträge (sechs Werte, gleiche Namen, gleiche Bedeutung).
- Token-Präfix `CONFIRMED_RENDER_` und die Regel „ohne gültiges Token nie `queued`".
- Der `vis-`-Präfix und der 6-Hex-Suffix der Kennung.
- Kein `additionalProperties: false`; `inputSchema` **und** `outputSchema` je Werkzeug.
- Die drei Feldnamen-Synonymgruppen, wörtlich.
- Die Dreiteilung Einreihen / Abfragen / Ausführen-ausserhalb — und die Regel, dass ein
  Enqueue-Werkzeug **nie** `done` zurückgibt.
- `ifc_path`, `glb_path`, `up_axis`, `bbox` als Eingangsnamen (Phase-0-Befund bestätigt
  sich; KosmoPublish nutzt `ifc_path` genauso).
- Die Prozessgrenze selbst: Alle vier gelesenen Blender-Lanes fahren eigene venvs und
  Subprozess-Runner. Wir sind dort nicht der Sonderfall, sondern die Regel.
- Die Pfad-Sandbox (`$HOME`/temp/Workspace-Root, Dot-Verzeichnisse gesperrt) — vier
  Lanes setzen sie mit fast identischem Code um; unser `job_verzeichnis()` respektiert sie.

---

## 8 · Korrekturen an unseren eigenen Dokumenten

1. **`EINBINDUNG_KOSMOORBIT_2026-08-14.md` §8.3** sagt, der qualifizierte Name sei
   `mcp__<servername>__<toolname>` und die Doppelung des Lane-Namens sei gewollt. Der
   erste Teil ist eine bei der Registrierung vergebene **Server-Kennung**; in den
   Cross-Lane-Briefen stehen Hex-Werte. Die Doppelung im *Werkzeugnamen* stimmt, die
   Deutung des ersten Segments nicht.
2. **`PLAN.md`**, Schuldposten „KosmoVis' Reife nicht nachgeprüft": Es gibt jetzt eine
   Fremdeinschätzung (~65 %, „Bau offen", blockiert) aus der Design-Lane und einen
   harten Beleg — drei verschiedene Ergebnisdateinamen in einer Lane (Kap. 6.3). Die
   Schuld ist damit nicht getilgt (ich habe nichts ausgeführt), aber sie ist keine reine
   Selbstauskunft mehr.
3. **`EINBINDUNG_KOSMOORBIT_2026-08-14.md` §8.1** nennt zwei widersprüchliche
   Up-Achsen-Angaben. Es sind **drei** (Kap. 6.1), und die dritte steht in der
   Dokumentation derselben Lane, deren Code die zweite trägt.

---

## 9 · Was ungeprüft blieb

Ohne diese Liste wäre der Bericht unehrlich.

**Nicht gelesen:**

- **`KosmoDraw-Privat`** — verboten, Regel 3. Da dort die BIM-Engine liegt, kenne ich die
  Erzeugerseite unserer Geometrie nur über das öffentliche `KosmoDraw` (Phase 0) und über
  Handoff-Verträge.
- **`kosmo-backend` / Odysseus selbst** — ich habe nur die im Codex-Repo abgelegten
  Kopien der Pipeline-Endpunkte gelesen (`pipeline_routes.py`, `mcp_routes.py`). Ob das
  der heutige Stand ist, weiss ich nicht; die Dateien tragen Datumsangaben aus Juni.
- **Der grösste Teil von KosmoPrepare, KosmoPublish, KosmoDesign** — zusammen weit über
  100 000 Zeilen. Gelesen habe ich die MCP-Nähte, die Handoff-Verträge, die
  Vertragsschemas und alles, was Feldnamen trägt. Die Fachlogik (Raumprogramm-Extraktion,
  Plan-Vektorisierung, Design-Gewissen) habe ich **nicht** beurteilt.
- **`Architektur-Cosmos`** nur in den Teilen zu Rechten, Medien-Slots und Modellpaketen.
  Die Website selbst, das D1-Schema und der Atlas: nicht gelesen.
- **Die `.ui-qa/`- und Screenshot-Bestände** des Codex-Repos: nicht angesehen.

**Gelesen, aber nicht verstanden oder nicht auflösbar:**

- **Welche Up-Achse KosmoVis tatsächlich erwartet** (Kap. 6.1). Doku und Code
  widersprechen sich; das entscheidet ein Lauf, nicht eine Lektüre.
- **Ob `kosmopublish_render_ifc_plans` funktioniert.** Zwei Dokumente aus demselben
  Ökosystem sagen das Gegenteil voneinander (Kap. 4).
- **Ob der Idle-Scheduler der System-Lane existiert.** Der Vertrag beschreibt ihn, eine
  `render_scheduler.py` und eine systemd-Unit liegen in KosmoVis, das MCP-Vertragsdokument
  vom 16.06. sagt „heute existiert KEIN headless Daemon/Timer". Ich habe nicht geprüft,
  welche Aussage die jüngere ist.
- **Der tatsächliche Registrierungsstand.** Alle Zahlen (99 Werkzeuge, 113 Werkzeuge,
  „live und gesund") stammen aus Juni-Protokollen. Ob heute irgendetwas davon läuft, ist
  aus einem Container nicht feststellbar.
- **Keine einzige Testsuite ausgeführt.** Alle Testzahlen sind Zählungen von
  Funktionsdefinitionen, keine Läufe. Sie sind Obergrenzen, keine Messwerte.

**Bewusst weggelassen (Regel 3):** rund ein Dutzend reale Wettbewerbs-, Auslober-,
Orts- und Adressangaben aus Beispielen und Testfixtures; die konkreten Farbwerte und
Ebenennamen des Plakat-Vertrags, soweit sie Projektinhalt statt Konvention sind.
