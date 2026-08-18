# Einbindung in KosmoOrbit — Vertrag und Folgen für den Entwurf

**Stand:** 2026-08-14 · **Grundlage:** `Imperigo/KosmoOrbit` @ `a69af5d`, read-only gelesen
**Anlass:** Der Prototyp soll am Ende in KosmoOrbit laufen. Das ist keine Randbedingung,
sondern bestimmt die Bauform.

---

## 1 · Was KosmoOrbit ist

Eine lokale Desktop-Anwendung (Tauri + React 19 + TypeScript) auf dem **Kosmo**-Backend
(`http://127.0.0.1:7860`, REST + SSE). Nicht Python — das ist die erste Konsequenz für
die Naht.

Das Leitprinzip steht wörtlich im README:

> **KosmoOrbit ist Cockpit, keine Engine.** Jedes Panel **konsumiert** Tool-Verträge
> read-only (über Kosmo/MCP) — es baut die Logik nicht nach.

Für „AI Imaging in a Box" heisst das: **Wir liefern die Engine, nicht die Oberfläche.**
Genau die Rollenteilung, die Regel 4 ohnehin verlangt.

---

## 2 · Der Knotengraph existiert bereits

Das ist der Befund, der eine Empfehlung der Lagebeurteilung korrigiert.

`src/components/NodePipeline.tsx` ist ein **ausführbarer Knoten-Graph** auf
`@xyflow/react` — React Flow, MIT-lizenziert. Die Ausführungslogik liegt in
`src/lib/pipeline.ts`, bewusst rein und ohne React-Abhängigkeit, damit sie headless
prüfbar ist:

| Funktion | Leistung |
|---|---|
| `topoOrder` | topologische Sortierung (Kahn), erkennt Zyklen |
| `mergeInputs` | Datenfluss: Ausgaben aller Vorgänger fliessen als Eingaben zusammen |
| `expandAliases` | Feldnamen-Synonyme über Lane-Grenzen hinweg |
| `descendants` | Skip-on-Error: fällt ein Knoten aus, werden Nachfolger übersprungen |
| `validateOutput` | Laufzeitprüfung der Tool-Ausgabe gegen ihr `outputSchema` (AJV) |
| `pipelineReadiness` | Entwurfszeit-Prüfung: meldet tote Kanten und fehlende Pflichtfelder |

**Folge:** In der Lagebeurteilung (Kap. 1) steht, für die Oberfläche sei litegraph.js oder
xyflow zu nehmen. Das ist überholt — im Ökosystem ist die Entscheidung längst gefallen
(xyflow), und der Graph ist gebaut. **Wir bauen keinen zweiten.**

### Zwei Graphen auf zwei Ebenen — der Unterschied bleibt

Das entwertet den eigenen Graph-Kern **nicht**, es verortet ihn nur richtig:

- **Der äussere Graph** (KosmoOrbit): Skizze → 3D → Varianten → Render → Plakat. Kette
  über Fachbereiche hinweg. **Existiert.**
- **Der innere Graph** (unsere Bibliothek): Geometrie → Multipass → Depth → ControlNet →
  Diffusion → Doppel-QA. Die Bildkette selbst. **Existiert nicht**, und ComfyUI scheidet
  wegen GPL aus.

Von aussen betrachtet ist unsere ganze Bildkette **ein Knoten** in KosmoOrbits Pipeline.
Innen ist sie selbst ein Graph.

---

## 3 · Der Vertrag, den wir erfüllen müssen

Aus `src/lib/kosmo.ts` und `src/lib/pipeline.ts` gelesen — das ist keine Auslegung,
sondern der Code, der uns aufrufen wird.

### 3.1 Form

Ein **MCP-Werkzeug** namens `mcp__<lane>__<funktion>`, registriert bei Kosmo. Pro
Werkzeug verpflichtend:

- **`inputSchema`** (JSON-Schema) — welche Angaben es erwartet
- **`outputSchema`** (JSON-Schema) — was es zurückgibt
- Ergebnis im Feld **`structuredContent`**, nicht als Freitext

Ohne beide Schemas greift `pipelineReadiness` und meldet unsere Kanten als tot. Das
Werkzeug erschiene im Cockpit, wäre aber nicht verdrahtbar.

### 3.2 Kanten entstehen über Feldnamen

Das ist der überraschendste und folgenreichste Teil. `mergeInputs` legt schlicht die
Ausgaben **aller** Vorgänger übereinander und reicht sie weiter. Eine Kante entsteht
dadurch, dass ein Ausgabefeld des einen Werkzeugs **gleich heisst** wie ein Eingabefeld
des nächsten.

Heisst unsere Eingabe `ifc_path`, verbindet sie sich von selbst mit
`kosmodraw_export_ifc`. Heisst sie `pfad_zur_ifc`, verbindet sich nichts — ohne
Fehlermeldung, es entsteht einfach keine Kante.

**Für Namen ohne gemeinsame Schreibweise gibt es `FIELD_ALIAS_GROUPS`.** Der Kommentar
dort ist streng und gut begründet: nur Felder **gleicher Bedeutung** gruppieren, nie
berechnete Ergebnisse mit Sollwerten. Wer eine neue Gruppe eintragen will, braucht einen
Schema-Beleg.

Zusätzlich, ausdrücklich als Konvention notiert: **Eingabe-Schemas dürfen nicht
`additionalProperties: false` setzen** — `mergeInputs` reicht ohnehin alles durch, was
die Vorgänger geliefert haben.

### 3.3 Read-only, fail-closed — und was das für einen GPU-Render bedeutet

Der Ausführungspfad ist **read-only gegatet, fail-closed**. Generieren und Bewerten
gelten als Lesen; Schreiben nicht.

Ein GPU-Render ist beides: Er schreibt Dateien und belegt für Minuten die Grafikkarte.
Er kann darum **kein gewöhnliches read-only-Werkzeug** sein. Die Naht muss aufgeteilt
werden:

| Werkzeug | Wirkung | Im Cockpit |
|---|---|---|
| `…_enqueue_render` | legt einen Auftrag mit Status `awaiting_approval` ab — rührt die GPU nicht an | zulässig |
| `…_query_render` | liest Status und Ergebnis | zulässig |
| *die eigentliche Ausführung* | Scheduler, ausserhalb der Pipeline, nur bei Freigabe und freier GPU | nicht im Cockpit |

KosmoVis hat genau diese Dreiteilung bereits gebaut (`render_job_store.py` +
`render_scheduler.py` + MCP-Server mit acht Werkzeugen, alle mit `outputSchema`). Sie
ist damit nicht Entwurf, sondern erprobt — und sie passt exakt zum Cockpit-Prinzip.

---

## 4 · Was das für unsere Bauform heisst

```
┌── KosmoOrbit (Tauri/React) ─────────────────────────────┐
│  Knotengraph · xyflow · read-only, fail-closed          │
│  vorhanden — wir bauen hier nichts                      │
└────────────────────┬────────────────────────────────────┘
                     │ Kosmo · MCP · inputSchema+outputSchema
┌────────────────────┴────────────────────────────────────┐
│  Dünne MCP-Schicht — Übersetzung, keine Logik           │
├─────────────────────────────────────────────────────────┤
│  ⬛ UNSER BEITRAG · Apache-2.0 · Python-Bibliothek       │
│     innerer Graph der Bildkette                         │
│     Geometrie-Treue-QA                                  │
│     Auftragsverwaltung mit Freigabe                     │
│     aus Python aufrufbar, ohne alles darüber (Regel 4)  │
├─────────────────────────────────────────────────────────┤
│  Subprozesse: Blender (GPL) · IfcOpenShell+CGAL (GPL)   │
│               LoRA-Training (Apache/MIT)                │
└─────────────────────────────────────────────────────────┘
```

Vier Konsequenzen:

1. **Die Bibliothek bleibt Python und eigenständig lauffähig.** Dass KosmoOrbit in
   TypeScript geschrieben ist, berührt uns nicht — die Naht ist MCP, nicht ein
   gemeinsamer Prozess. Regel 4 und die Einbindung verlangen dasselbe.
2. **Die MCP-Schicht ist dünn und austauschbar.** Sie übersetzt Schemas, mehr nicht.
   Läge Logik darin, wäre die Bibliothek ohne Cockpit unvollständig — Regel 4 verletzt.
3. **Feldnamen sind ein Entwurfsgegenstand, kein Detail.** Sie entscheiden, ob sich
   unsere Werkzeuge in die Ökosystem-Kette einfügen. Vor dem ersten Schema gehören die
   Ausgabefelder der Nachbar-Lanes gelesen — mindestens `kosmodraw_export_ifc`.
4. **Der Render bleibt asynchron und gegatet.** Nicht als nachträgliche Absicherung,
   sondern weil der read-only-Pfad des Cockpits nichts anderes zulässt.

---

## 5 · Die beiden offenen Punkte — jetzt beantwortbar

### 5.1 Wieviel KosmoVis wandert mit?

Der KosmoOrbit-Vertrag entscheidet das, denn ein Teil des KosmoVis-Codes **spricht diese
Sprache bereits**.

**Übernehmen — Verträge und Muster, weil erprobt und passend:**

| Modul | LOC | Warum |
|---|---|---|
| `render_job_store.py` | 178 | Auftrag/Freigabe/Status — genau die Dreiteilung aus §3.3 |
| `kosmovis_mcp_server.py` | 813 | 8 Werkzeuge, alle mit `outputSchema` — erfüllt den Vertrag schon |
| `archviz_geometry_fidelity.py` | 495 | die QA-Methode selbst — der Forschungskern |
| `archviz_style_score.py` | 370 | zweites Gate |
| `backbone_adapter.py` | 206 | der Modell-Austauschbarkeits-Vertrag |

**Neu schreiben, Verträge übernehmen:** `ifc_to_glb.py` und `connectors/archicad_ifc.py`.
Fachlich richtig (Massstabs- und Georeferenz-Torwächter), aber sie tragen KosmoVis-Pfade
und -Annahmen. Die Prüflogik ist das Wertvolle, nicht der Code drumherum.

**Nicht übernehmen:** `archviz_license.py` (proprietäres Schlüsselschema, unvereinbar mit
Apache-2.0) und die 70 `bpy`-behafteten Add-on-Module (Regel 2).

Ergibt rund 2 000 Zeilen belastbaren Vorsprung — bei ehrlicher Buchführung: erprobt,
aber laut KosmoVis' eigenem Bericht ohne Regressions-Testnetz und ohne abgenommenen v1.

### 5.2 Ist die Geometrie-Treue-QA der wissenschaftliche Kern?

**Ja — und der Blick auf KosmoOrbit macht das Argument stärker, nicht schwächer.**

Die Lagebeurteilung nannte drei Kandidaten: Packaging/Zugänglichkeit,
Architektur-Connectors, Geometrie-Treue-QA. Zwei davon sind nun schwächer:

- **Packaging/Zugänglichkeit** ist im Ökosystem weitgehend gelöst. KosmoOrbit *ist* die
  zugängliche Oberfläche über einem Knotengraph. Wir würden es nachbauen, nicht erfinden.
- **Connectors** sind wertvoll, aber Ingenieurarbeit: eine Datei-Export-Naht mit einem gut
  gemachten Torwächter. Ein Produktbeitrag, keine Forschungsfrage.

Übrig bleibt die **messbare, erzwungene Geometrie-Treue**. Sie ist das Einzige, das
weder KosmoOrbit noch ein geprüftes externes Werkzeug leistet, und die Frage dahinter —
*folgt der Render der echten Geometrie?* — ist offen, formulierbar und prüfbar.

Der belegte Anlass macht sie zitierfähig: Im ersten Lauf an echter Geometrie gab das
reine Stil-Gate „bestanden" auf eine **halluzinierte** Kubatur. Ein Fehlurteil, das das
zweite Gate abfängt. Das ist die Art von Befund, aus der eine Forschungsfrage wird.

Die offensichtliche Schwäche gehört mitgenannt: Die Schwellen (0.65 / 0.30) sind an
wenigen Fällen kalibriert. Eine systematische Schwellenstudie wäre der naheliegende
wissenschaftliche Ausbau — und zugleich das, was die Arbeit über einen Werkstattbericht
hinaushebt.

**Empfehlung:** So mit Gonzalo besprechen — Forschungsfrage die QA, Framework und
Connectors als Produktbeitrag, systematische Schwellenkalibrierung als Ausbau.

---

## 6 · Was ich nicht gelesen habe

Der Auftrag lautete, alle ArchitekturKosmos-Repos anzusehen. Ich habe nach KosmoOrbit
bewusst abgebrochen, weil es die Frage nach der Einbindung beantwortet und weiteres Lesen
den verbleibenden Rahmen aufgebraucht hätte, ohne die Antwort zu ändern.

**Ungelesen und für den Bau noch relevant:**

- **`kosmo-backend`** — der MCP-Registrierungsweg. *Wie* ein Werkzeug bei Kosmo angemeldet
  wird, habe ich nur aus KosmoOrbits Sicht (der aufrufenden Seite) gesehen.
- **`KosmoDraw`** — liefert `kosmodraw_export_ifc`. **Die konkreten Ausgabefeldnamen
  müssen vor unserem ersten `inputSchema` gelesen werden** (§3.2).
- **`KosmoPublish`** — Abnehmer der Renders (A0-Plakat-Slots).
- **`KosmoDesign`, `KosmoPrepare`, `ArchitekturKosmos-Codex`,
  `architekturkosmos-control-hub`, `Architektur-Cosmos`** — Ökosystem-Kontext.

Der einzige davon, der **vor** dem ersten Code gelesen werden muss, ist **KosmoDraw** —
wegen der Feldnamen. Alles andere kann begleitend geschehen.

---

## 7 · Was sich an der Lagebeurteilung ändert

| Kapitel | Vorher | Jetzt |
|---|---|---|
| 1 · Knotenketten | „litegraph.js oder xyflow für die Oberfläche" | Oberfläche existiert (xyflow). Eigener Graph nur **innen**, in der Bibliothek |
| 5 · Sprachmodelle | MCP als optionale Bedienschicht | MCP ist **der** Einbindungsvertrag — mit Pflicht zu `inputSchema` + `outputSchema` |
| 10 · Eigenständigkeit | „Packaging ist Produktbeitrag" | schwächer als gedacht — das Cockpit gibt es schon |
| 11 · offene Punkte | zwei offen | beide beantwortet (§5) |

Unverändert gültig: sämtliche Lizenzbefunde, die Prozessgrenzen-Architektur und die
Einordnung der Geometrie-Treue-QA als eigentlicher Beitrag.

---

## 8 · Nachtrag Phase 0 (2026-08-14): belegte Feldnamen

Gelesen: `Imperigo/KosmoDraw` @ `8481ea8`,
`code/integrations/odysseus/kosmodraw_mcp_server.py` (1540 Zeilen) und
`code/tools/glb_export_runner.py`. Damit sind die Namen **belegt statt vermutet**.

### 8.1 ⚠️ Der Befund, der die Kette hätte kippen können: `up_axis`

KosmoDraw hat bereits ein Werkzeug **`kosmodraw_export_glb`** (IFC → glb). Sein
Ausgabefeld heisst `glb_path` — genau der Name, den auch wir als Eingang bräuchten.
Über `mergeInputs` entstünde die Kante **automatisch**.

Und genau dort sitzt der Konflikt:

| Erzeuger | `up_axis` | Verhalten |
|---|---|---|
| **KosmoDraw** `glb_export_runner.py:122` | `"Z"` | rohe IFC-Koordinaten, **keine Rotation** — Kommentar: „Z-up (IFC-Konvention) — der Viewer orientiert" |
| **KosmoVis** `ifc_to_glb.py:340` | `"Y (glTF-2.0-Standard)"` | dreht Z-up → Y-up, damit Blender aufrecht importiert |

Beide schreiben ein Feld `glb_path` und ein Feld `up_axis` — mit **unverträglichem
Inhalt**. glTF 2.0 ist definitionsgemäss Y-up und kennt kein Up-Achsen-Feld; Blender
importiert strikt Y-up → Z-up. Eine rohe Z-up-glb landet in Blender **liegend auf der
Seite**.

Für KosmoDraw ist das richtig: Sein Abnehmer ist KosmoOrbits Viewer, dem man die
Orientierung mitgeben kann. Für uns ist es falsch — und es fällt **still** durch:
Tiefenkarte, Kameraableitung und Geometrie-QA wären allesamt verdreht, ohne
Fehlermeldung.

**Konsequenz für unser `inputSchema`:** `up_axis` wird **Pflichtfeld**, nicht optional.
Wir prüfen es zur Laufzeit und rotieren bei `"Z"`, statt eine Konvention anzunehmen.
Fehlt das Feld, wird abgelehnt — nicht geraten.

Das ist exakt die Fehlerklasse, für die Phase 0 angesetzt war: Die Kante verbindet sich
von selbst, weil die Namen stimmen; die Bedeutung tut es nicht.

### 8.2 Belegte Ausgabefelder der Nachbar-Lane

Aus dem `_OUT`-Block (`kosmodraw_mcp_server.py:274-300`):

| Werkzeug | Ausgabefelder |
|---|---|
| `kosmodraw_export_ifc` | `ifc_path` · `n_entities` · `status` · `error` |
| `kosmodraw_export_glb` | `glb_path` · `n_vertices` · `n_triangles` · `bbox` · `up_axis` · `layers` · `status` |
| `kosmodraw_bim_layers` | `layers` · `n_layers` · `bbox` · `element_counts` · `geometry_ref` · `source_ifc` · `bbox_note` |

**Für uns zu übernehmende Eingangsnamen:** `ifc_path`, `glb_path`, `up_axis`, `bbox`.
Kein `model_path`, kein `geometry`, kein `pfad` — sonst entsteht keine Kante.

`geometry_ref` ist der Ökosystem-Begriff für „hier liegt die 3D-Geometrie" und taucht
auch in KosmoOrbits Varianten-Knoten auf. Als **Ausgabe**feld für uns vorzumerken.

### 8.3 Werkzeugbenennung — doppeltes Präfix

KosmoOrbit ruft `mcp__kosmodraw__kosmodraw_seed_variants`. Das Muster ist:

```
mcp__<servername>__<toolname>
   └ aus der MCP-Registrierung  └ trägt den Lane-Namen nochmals
```

Also: Servername `KosmoVis` + Werkzeug `kosmovis_enqueue_render` ergibt
`mcp__kosmovis__kosmovis_enqueue_render`. Die Doppelung ist gewollt und einzuhalten.

### 8.4 Registrierung bei Kosmo — geklärt ohne `kosmo-backend`

`register_in_odysseus.sh` dokumentiert den Weg vollständig; das Backend musste dafür
nicht gelesen werden.

1. Login: `POST /api/auth/login` (JSON `{username,password}`) → Session-Cookie
2. Anmelden: `POST /api/mcp/servers` mit `name`, `transport=stdio`, `command`, `args`, `env`
3. Persistenz in der Odysseus-DB (`mcp_servers`); Entfernen via `DELETE /api/mcp/servers/<id>`

Der Server läuft über **stdio**, von Odysseus gespawnt. Voraussetzung: Das aufgerufene
Python kann `import mcp`. Es gibt eine **Pfad-Sandbox** — Schreibziele müssen unter
`$HOME` oder `/tmp` liegen.

### 8.5 Unabhängige Bestätigung unserer Architektur

Bemerkenswert: KosmoDraw fährt bereits **genau das Muster**, das wir aus der Lizenzlage
abgeleitet haben. Kommentar im Server (Zeile 666f.):

> „Der IFC-Bau (ifcopenshell) läuft über eine Subprozess-Seam im `.venv-night`
> (kein ifcopenshell/bpy im MCP-Python → Freeze-Schutz)."

Dieselbe Prozessgrenze, dasselbe eigene venv, dieselbe Runner-Bauform
(`export_ifc_runner.py`, `glb_export_runner.py`, `bim_layers_runner.py`) — dort aus
Stabilitätsgründen begründet, bei uns zusätzlich aus Lizenzgründen. Zwei unabhängige
Wege zur selben Naht. Das stärkt die Entscheidung.

**Nebenbefund:** `export_ifc` und `export_glb` sind **write-gated**, nicht read-only —
die Unterscheidung aus §3.3 ist im Ökosystem also bereits etabliert und keine Erfindung
unsererseits.

### 8.6 Offene Frage aus diesem Nachtrag

Wenn KosmoDraw IFC→glb bereits liefert: **Brauchen wir einen eigenen IFC-Pfad?**

Beides ist vertretbar, und die Entscheidung gehört bewusst getroffen:

- **Dagegen** — wir konsumieren `glb_path` und sind die IFC-Kette samt LGPL/CGAL-Frage
  vollständig los; sie liegt dann in KosmoDraws Prozess, nicht in unserem.
- **Dafür** — Regel 4 verlangt, dass der Kern eigenständig läuft. Ein Prototyp, der ohne
  KosmoDraw keine Geometrie einlesen kann, ist kein eigenständiges Framework, sondern
  ein Anhängsel. Ausserdem entfielen der Massstabs- und Georeferenz-Torwächter.

**Empfehlung:** eigener IFC-Pfad, aber `glb_path` zusätzlich als Eingang akzeptieren.
Dann ist der Prototyp allein lauffähig **und** fügt sich in die Kette ein.
